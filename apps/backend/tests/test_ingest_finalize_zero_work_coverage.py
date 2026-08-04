"""ops-hardening iter-46 FIX PASS (QA blocker 1 + 4 — J-01 / J-03) — the ingest finalize tail must not pay
the heavy `_compute_coverage_uncached` derivation for a ZERO-WORK backfill.

WHAT THE QA RUN MEASURED: a backfill whose payload resolved to zero trading days (`dates_total: 0`, QA run
287 — two weekend dates) never left `status: "running"` for 15+ minutes on an otherwise idle,
freshly-restarted backend. The per-date work resolved instantly; the job record stayed `running` because
the finalize tail ran an unconditional full coverage/membership-timeline recompute afterward.

ROOT CAUSE, READ DIRECTLY FROM THE CODE: `_refresh_ingest_aggregates` called `refresh_coverage_snapshot`
UNCONDITIONALLY on every backfill/both/rebuild. Every OTHER heavy step in that tail is already served by a
`dataset_version`-keyed cache (forward-aggregates, research hot keys, index series, drawdown expectations),
so on a zero-work job they are all cheap HITS — `refresh_coverage_snapshot` was the ONE uncached heavy call
left, and it re-derives the whole payload (its own `prefilled_bar_cache` whole-bar load) even when the
persisted row already reflects this exact `(asof_key, dataset_version)` stamp.

THE FIX REUSES AN ALREADY-AUDITED GATE, NOT A NEW MECHANISM: `_coverage_snapshot_is_current` was added in
iter-3 (audit B1) for EXACTLY this purpose and is already applied to the fetch/expand finalize branch
(`data_manager.py`, "gated by `_coverage_snapshot_is_current` so a zero-work fetch (the common offline
case) pays no extra compute/write"). This pass applies the SAME gate to the backfill branch.

The contract proven here is a CALL-COUNT contract (mirroring iter-3's own TC-2), never a wall-clock
assertion: a zero-work finalize must reach `_compute_coverage_uncached` ZERO times, and a genuinely stale
one must still reach it (no regression to the refresh that keeps `/api/data` honest).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager, forward_testing, research
from app.engine.data_manager import JobProgress
from app.models import ScannerRun

ASOF = date(2020, 1, 2)
LATER_ASOF = date(2020, 1, 3)


def _make_run(cfg, asof: date) -> ScannerRun:
    return ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label=cfg.regime.labels[0], regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )


@pytest.fixture()
def finalize_session(tmp_path):
    """The smallest DB the finalize tail needs: one `ScannerRun` (so the coverage as-of resolves and the
    per-horizon forward-aggregate loop is reached). No price rows — this module proves a CALL-COUNT
    contract, so the real cost of any individual warm is irrelevant to what is being asserted."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_zero_work.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(_make_run(cfg, ASOF))
        session.commit()
    with Session(engine) as session:
        yield session, cfg


@pytest.fixture()
def quiet_finalize(monkeypatch):
    """Silence the finalize tail's OTHER aggregate warms so this module measures exactly one thing: how
    many times the COVERAGE path reaches `_compute_coverage_uncached`. Each stub stands in for a step that
    is already `dataset_version`-cached in production (a cheap HIT on a zero-work job) — they are not this
    module's subject."""
    monkeypatch.setattr(data_manager, "read_entries", lambda _path: [])          # no ledger claims to warm
    monkeypatch.setattr(data_manager, "subject_catalog", lambda _cfg: [])        # no research hot key
    monkeypatch.setattr(
        forward_testing, "forward_aggregates_ingest_cached", lambda *_a, **_k: None
    )


def _spy_uncached_coverage(monkeypatch) -> list[object]:
    """Record every `_compute_coverage_uncached` call — the heavy derivation whose avoidance IS the fix."""
    calls: list[object] = []
    real = data_manager._compute_coverage_uncached

    def _spy(session, cfg, *, as_of=None):
        calls.append(as_of)
        return real(session, cfg, as_of=as_of)

    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _spy)
    return calls


# ==================================================================================================
# TC-A1 — a ZERO-WORK backfill's finalize tail must not recompute coverage at all
# ==================================================================================================
def test_zero_work_backfill_finalize_skips_heavy_coverage_recompute(
    finalize_session, quiet_finalize, monkeypatch
):
    """TC-A1 (QA blocker 1, J-01): when the persisted `CoverageSnapshot` already reflects the CURRENT
    `(asof_key, dataset_version)` stamp and the job created NO new snapshot dates, the finalize tail must
    reach `_compute_coverage_uncached` ZERO times — the same zero-work call-count contract iter-3's B1 fix
    already established for the fetch/expand branch.

    This is the defect that kept QA run 287 (`dates_total: 0`) `running` for 15+ minutes: nothing to
    backfill, yet a full coverage/membership-timeline derivation ran anyway."""
    session, cfg = finalize_session
    # a prior ingest already persisted the row for this exact stamp (the real precondition, via the real path)
    data_manager.refresh_coverage_snapshot(session, cfg)
    assert data_manager._coverage_snapshot_is_current(session, cfg), (
        "fixture precondition: the persisted snapshot must be current for this stamp before the drill"
    )

    calls = _spy_uncached_coverage(monkeypatch)  # spy installed AFTER the seed, so it counts only the tail
    prog = JobProgress(job_id="zero-work-backfill", kind="backfill", start=ASOF, end=ASOF)
    prog.new_snapshot_dates = []  # the zero-work case: no trading day in range produced a snapshot

    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise

    assert calls == [], (
        "a zero-work backfill must pay NO coverage recompute — `_compute_coverage_uncached` was reached "
        f"{len(calls)} time(s) with as_of={calls}. This is the unconditional heavy call that kept QA run "
        "287 (dates_total:0) in `running` for 15+ minutes."
    )
    # honesty gate: nothing was refreshed, so neither category may be claimed (never a fabricated refresh).
    assert "coverage" not in refreshed and "membership_timeline" not in refreshed, (
        "a skipped (already-current) refresh must be honestly ABSENT from the reported categories; "
        f"refreshed={refreshed}"
    )


# ==================================================================================================
# TC-A2 — a genuinely STALE stamp must still refresh (no regression to the freshness the gate protects)
# ==================================================================================================
def test_stale_stamp_backfill_finalize_still_refreshes_coverage(
    finalize_session, quiet_finalize, monkeypatch
):
    """TC-A2: the gate must skip ONLY redundant work. When the job actually landed a new snapshot date the
    `dataset_version` moves, no row exists for the new stamp, and the finalize tail must still run the
    canonical refresh exactly once and report BOTH categories — otherwise `/api/data` would serve a stale
    coverage payload (and J-05's `aggregates_refreshed` would lose `membership_timeline`)."""
    session, cfg = finalize_session
    data_manager.refresh_coverage_snapshot(session, cfg)  # current for the ONE-run stamp

    # this job landed a genuinely new snapshot date -> the narrow membership dataset version moves
    session.add(_make_run(cfg, LATER_ASOF))
    session.commit()
    assert not data_manager._coverage_snapshot_is_current(session, cfg), (
        "fixture precondition: a new snapshot date must stale the persisted stamp"
    )

    calls = _spy_uncached_coverage(monkeypatch)
    prog = JobProgress(job_id="real-work-backfill", kind="backfill", start=ASOF, end=LATER_ASOF)
    prog.new_snapshot_dates = [LATER_ASOF]

    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    # exactly one CURRENT-stamp refresh, plus the per-date warm for the one new date (unchanged behavior)
    assert LATER_ASOF in calls, (
        f"the new snapshot date's own coverage row must still be computed; calls={calls}"
    )
    assert "coverage" in refreshed and "membership_timeline" in refreshed, (
        f"a genuinely stale stamp must still refresh + report both categories; refreshed={refreshed}"
    )
    assert data_manager._coverage_snapshot_is_current(session, cfg), (
        "after the finalize tail the persisted snapshot must be current again for the NEW stamp"
    )


# ==================================================================================================
# TC-A3 (iter-46 AUDIT, B1) — a CLEAR-AND-RECREATE rebuild restores an IDENTICAL stamp, so the gate must
# not be allowed to skip on it
# ==================================================================================================
def test_rebuild_that_restores_an_identical_stamp_still_refreshes_coverage(
    finalize_session, quiet_finalize, monkeypatch
):
    """TC-A3: the fix-pass rationale ("any job that actually landed a bar or a snapshot moves
    `_membership_dataset_version`") does NOT hold for the J-85 clear-and-recreate rebuild.
    `scanner_runs.id` is a plain `INTEGER PRIMARY KEY` (no `AUTOINCREMENT`, no `sqlite_sequence` row), so
    clearing every run and recomputing the SAME date set restores the SAME `max(id)` and `count(*)`; with
    the bars untouched the stamp is byte-identical before and after. A rebuild whose whole documented
    purpose is to pick up a universe expansion — a change the NARROW membership stamp does not encode —
    would then skip its coverage refresh, leave `/api/data` serving the pre-rebuild payload while
    `coverage_status` still reports it fresh, and drop `coverage`/`membership_timeline` from the field
    J-05 asserts on.

    The gate therefore also requires `new_snapshot_dates == []` — the zero-work case it exists for."""
    session, cfg = finalize_session
    data_manager.refresh_coverage_snapshot(session, cfg)
    stamp_before = research._membership_dataset_version(session, cfg)

    # the rebuild's clear-then-create-once cycle, reproduced exactly: drop every snapshot, then recompute
    # the SAME date set. SQLite hands the recreated row the SAME id, so the stamp lands back where it was.
    for run in session.exec(select(ScannerRun)).all():
        session.delete(run)
    session.commit()
    session.add(_make_run(cfg, ASOF))
    session.commit()

    assert research._membership_dataset_version(session, cfg) == stamp_before, (
        "fixture precondition: the clear-and-recreate cycle must restore the IDENTICAL stamp — this is "
        "the exact blind spot the `_coverage_snapshot_is_current` gate has on its own"
    )
    assert data_manager._coverage_snapshot_is_current(session, cfg), (
        "fixture precondition: with the stamp restored, the pre-rebuild row still reads as 'current'"
    )

    calls = _spy_uncached_coverage(monkeypatch)
    prog = JobProgress(job_id="rebuild-same-stamp", kind="rebuild", start=ASOF, end=ASOF)
    prog.new_snapshot_dates = [ASOF]  # a rebuild recreates every snapshot -> every date is 'new'

    refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert calls, (
        "a rebuild that recreated snapshots must still recompute coverage even when the narrow stamp "
        f"happens to be unchanged; `_compute_coverage_uncached` was reached {len(calls)} time(s)"
    )
    assert "coverage" in refreshed and "membership_timeline" in refreshed, (
        f"a snapshot-creating job must report both categories honestly; refreshed={refreshed}"
    )
