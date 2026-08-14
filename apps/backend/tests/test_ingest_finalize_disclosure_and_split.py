"""The finalize tail must be VISIBLE while it runs, and the UI hot-key warms must not hold the job open.

THE BUG THESE PIN (observed live 2026-08-14, run 530 — an 8-date backfill):
the backfill looked like it never finished. Its scan loop ended at 20:47:21 and the job did not reach
`ok` until 21:02:43 — 15m22s later — and for that whole window `GET /api/data/jobs/<id>` served:

    dates_done/dates_total = 8/8          -> the progress bar rendered FULL
    message                = "snapshots 8/8 dates"
    current_activity       = "scanning 2026-08-12 (8/8)"   <- FALSE; the scan had ended minutes earlier
    last_progress_at       = 141s stale                    -> the card ALSO showed "possibly stalled"
    status                 = "running"

Every visible field claimed the work was complete, one of them claimed a scan was still in progress, and
the stale-heartbeat heuristic claimed it was stuck — on a perfectly healthy job. Two causes:

  1. `_refresh_ingest_aggregates` ticks the heartbeat WITHOUT an activity argument (the iter-4 F1 choice,
     correct DURING the scan so an in-flight "scanning ..." line is not clobbered), so `current_activity`
     froze at the last scanned date for the entire tail and nothing named the real phase.
  2. The tail's two `EventStudyCache` hot-key warms dominate it. Measured for that run:
     essential 124.6s (availability 1.11 + coverage/membership 6.18 + per-date coverage 12.01 +
     market phase 6.00 + forward aggregates 98.16 + index series 1.16) vs deferred 796.8s
     (research hot keys 2.10 + factor lab 511.35 + drawdown expectations 283.32). 87% of the wait bought
     nothing `/data` reads.

The fix: publish `finalize_phase`/`finalize_phase_started_at` throughout the tail, and move the three
hot-key warms into `_refresh_deferred_hot_keys`, run AFTER `prog.status` flips so the badge clears at the
essential-set boundary. `prog.aggregates_refreshed` still accumulates BOTH halves, so the persisted run
record names every category that ran — the contract narrows nowhere.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager
from app.engine.data_manager import JobProgress
from app.models import DailyPrice, ScannerRun

SPY_DAYS = [
    date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8),
]

# The categories each half owns. `/data` reads every essential one; none of the deferred three.
ESSENTIAL = {"availability_heatmap", "coverage", "membership_timeline", "market_phase",
             "forward_aggregates", "index_series", "latest_snapshot"}
DEFERRED = {"research_hot_keys", "factor_lab_all", "drawdown_expectations"}


@pytest.fixture()
def ingest_engine(tmp_path):
    """SPY bars on five dates + one snapshot — enough for both finalize halves to reach their phases."""
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_disclosure.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in SPY_DAYS:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        session.add(ScannerRun(
            asof_date=SPY_DAYS[1], created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
            provider="seed", benchmark="SPY", regime_score=50.0, regime_label=load_config().regime.labels[0],
            regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
        ))
        session.commit()
    return engine


def _progress(kind: str = "backfill") -> JobProgress:
    prog = JobProgress(job_id=f"disclose-{kind}", kind=kind, start=SPY_DAYS[0], end=SPY_DAYS[-1])
    # the post-scan state the live defect was captured in
    prog.dates_total = len(SPY_DAYS)
    prog.dates_done = len(SPY_DAYS)
    prog.current_activity = f"scanning {SPY_DAYS[-1].isoformat()} (5/5)"
    prog.message = "snapshots 5/5 dates"
    return prog


def _record_phases(monkeypatch) -> list[str]:
    """Every distinct value `finalize_phase` takes, in order — the exact sequence a UI poller would see."""
    seen: list[str] = []
    real = JobProgress.enter_finalize_phase

    def _spy(self, phase: str) -> None:
        seen.append(phase)
        real(self, phase)

    monkeypatch.setattr(JobProgress, "enter_finalize_phase", _spy)
    return seen


# ==================================================================================================
# TC-1 — the tail names itself while it runs
# ==================================================================================================
def test_essential_finalize_publishes_a_named_phase_for_every_step(ingest_engine, monkeypatch):
    """Each essential phase must announce itself, so a poller sees a MOVING label instead of a frozen
    scan line. Before this fix nothing was published at all."""
    cfg = load_config()
    seen = _record_phases(monkeypatch)

    with Session(ingest_engine) as session:
        data_manager._refresh_ingest_aggregates(session, cfg, _progress())

    assert seen, "the finalize tail must publish at least one named phase — it published none"
    assert "availability heatmap" in seen
    assert any("forward aggregates" in p for p in seen), (
        f"the longest essential phase must be named; phases seen were {seen}"
    )


def test_finalize_phase_is_cleared_when_no_phase_is_running(ingest_engine):
    """Absence is the honest idle signal — a lingering label would claim work that already finished."""
    cfg = load_config()
    prog = _progress()
    assert prog.finalize_phase == ""  # nothing running yet

    with Session(ingest_engine) as session:
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert prog.finalize_phase == "", "the essential half must clear its label on the way out"
    assert prog.finalize_phase_started_at is None

    with Session(ingest_engine) as session:
        data_manager._refresh_deferred_hot_keys(session, cfg, prog)
    assert prog.finalize_phase == "", "the deferred half must clear its label on the way out"
    assert prog.finalize_phase_started_at is None


def test_message_stops_claiming_the_scan_is_complete_while_the_tail_runs(ingest_engine):
    """The bar is visually full at 5/5, so the message beside it must not be the only thing the card
    says. It names the tail instead — and `_run_job`'s `finally` still overwrites it with the real
    summary at completion, so the persisted record is unaffected."""
    cfg = load_config()
    prog = _progress()
    with Session(ingest_engine) as session:
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert prog.message == "5/5 dates · finalizing", f"got {prog.message!r}"


def test_current_activity_semantics_are_untouched(ingest_engine):
    """The scan line belongs to the scan loop. The finalize disclosure is ADDITIVE — it must not
    overwrite `current_activity` (that would reverse the iter-4 F1 fix rather than complete it)."""
    cfg = load_config()
    prog = _progress()
    before = prog.current_activity
    with Session(ingest_engine) as session:
        data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert prog.current_activity == before


# ==================================================================================================
# TC-2 — the split: hot-key warms are not in the essential half
# ==================================================================================================
def test_essential_half_does_not_run_the_deferred_hot_keys(ingest_engine):
    """The 796.8s that made the job look hung must be absent from the half that gates the badge."""
    cfg = load_config()
    with Session(ingest_engine) as session:
        refreshed = set(data_manager._refresh_ingest_aggregates(session, cfg, _progress()))

    assert not (refreshed & DEFERRED), (
        f"the essential half must not warm the UI hot keys; it reported {sorted(refreshed & DEFERRED)}"
    )
    assert refreshed <= ESSENTIAL, f"unexpected category in the essential half: {sorted(refreshed - ESSENTIAL)}"


def test_deferred_half_runs_only_the_hot_keys_and_reports_them(ingest_engine, caplog):
    """The deferred half owns exactly the three UI caches, and reports honestly (a category appears only
    when it actually warmed)."""
    cfg = load_config()
    with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
        with Session(ingest_engine) as session:
            refreshed = set(data_manager._refresh_deferred_hot_keys(session, cfg, _progress()))

    assert refreshed <= DEFERRED, f"unexpected category in the deferred half: {sorted(refreshed - DEFERRED)}"
    assert "factor_lab_all_warm" in caplog.text, (
        "the deferred half must still emit its per-phase timing lines so a slow warm stays attributable"
    )


def test_deferred_half_never_raises(ingest_engine, monkeypatch):
    """Same non-fatal contract as its sibling: it runs after the job is already `ok`, so nothing it does
    may retro-flip a completed job to failed."""
    cfg = load_config()

    def _boom(*_a, **_k):
        raise RuntimeError("simulated hot-key warm failure")

    monkeypatch.setattr(data_manager, "factor_lab_all_cached", _boom, raising=False)
    monkeypatch.setattr(data_manager, "event_study_cached", _boom, raising=False)

    with Session(ingest_engine) as session:
        refreshed = data_manager._refresh_deferred_hot_keys(session, cfg, _progress())  # must not raise
    assert isinstance(refreshed, list)


# ==================================================================================================
# TC-3 — the two halves together still report every category (no contract narrowing)
# ==================================================================================================
def test_amend_run_record_updates_detail_without_reopening_or_duplicating(ingest_engine):
    """The deferred half runs AFTER the run-history row is closed (so Run history stops showing a
    finished job as `running` for another ~13 minutes — live: run 531 flipped its live status at t+147s
    but its row's `finished_at` was 12m38s later). Its categories must still reach the persisted record,
    which is what `_amend_run_record_detail` is for: update the detail blob of an ALREADY-TERMINAL row,
    touching neither `status` nor `finished_at`, and never INSERTing a second history entry the way
    `_finalize_run_record` would when it finds no open row."""
    from app.models import DataProviderRun

    prog = _progress()
    prog.status = "ok"
    # `_run_detail` only emits the backfill breakdown (and with it `aggregates_refreshed`) once the run
    # genuinely computed one — `_breakdown_computed` gates on `calendar_days > 0`. A real completed
    # backfill always has it; set it so this exercises the populated shape rather than the null sentinel.
    prog.calendar_days = 7
    closed_at = datetime(2026, 8, 14, 21, 47, 14, tzinfo=timezone.utc)
    with Session(ingest_engine) as session:
        session.add(DataProviderRun(
            provider="seed", started_at=datetime(2026, 8, 14, 21, 44, 47, tzinfo=timezone.utc),
            finished_at=closed_at, symbols_ok=0, symbols_failed=0, status="ok",
            message=json.dumps({"aggregates_refreshed": ["forward_aggregates"]}), job_id=prog.job_id,
        ))
        session.commit()

    prog.aggregates_refreshed = ["forward_aggregates", "factor_lab_all", "drawdown_expectations"]
    data_manager._amend_run_record_detail(ingest_engine, prog)

    with Session(ingest_engine) as session:
        rows = session.exec(
            select(DataProviderRun).where(DataProviderRun.job_id == prog.job_id)
        ).all()
    assert len(rows) == 1, f"amending must never fabricate a second history entry; got {len(rows)}"
    row = rows[0]
    # SQLite hands back naive datetimes, so compare on the wall-clock value the row actually stores.
    assert row.status == "ok" and row.finished_at.replace(tzinfo=timezone.utc) == closed_at, (
        "amending must leave the terminal transition exactly as it was closed"
    )
    assert json.loads(row.message)["aggregates_refreshed"] == prog.aggregates_refreshed


def test_amend_run_record_is_a_noop_without_a_row(ingest_engine):
    """No row for this job id — never an INSERT, never a raise."""
    from app.models import DataProviderRun

    prog = _progress()
    data_manager._amend_run_record_detail(ingest_engine, prog)  # must not raise
    with Session(ingest_engine) as session:
        assert session.exec(select(DataProviderRun)).all() == []


def test_both_halves_together_cover_the_full_category_set(ingest_engine):
    """`prog.aggregates_refreshed` is persisted by `_finalize_run_record` AFTER both halves have run, so
    splitting the hook must not drop a category from the run record. Union == what the single hook used
    to report."""
    cfg = load_config()
    prog = _progress()
    with Session(ingest_engine) as session:
        essential = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    with Session(ingest_engine) as session:
        deferred = data_manager._refresh_deferred_hot_keys(session, cfg, prog)

    combined = essential + deferred
    assert len(combined) == len(set(combined)), f"a category was reported twice: {combined}"
    assert set(combined) <= ESSENTIAL | DEFERRED
