"""The availability heatmap must be refreshed IMMEDIATELY by every ingest job — deterministic proof for
the fix that hoisted the `AvailabilityCache` warm to the head of `_refresh_ingest_aggregates`.

THE BUG THESE PIN (observed live 2026-08-14, on the 8.4 GB dev DB):
a fetch of 2026-08-05..08-13 committed its bars, then the backend restarted mid-job (`logs/backend.log`:
`boot: swept 1 orphaned 'running' job record(s) -> 'interrupted'`). The finalize tail never ran, so the
availability warm — which sat SECOND-TO-LAST, behind `forward_aggregates_warm` alone at 95.57s while the
warm itself costs 1.09s — was lost. `AvailabilityCache`'s only writer was that hook, so nothing repaired
it: `GET /api/data/availability` kept serving 5,391 trading days (`stale: False`, because no job was
running) while `GET /api/data`'s coverage block served 5,398 — the two panels of the SAME page
disagreeing by exactly the 7 fetched dates, with `compute_availability`'s own docstring asserting those
two counts are equal.

The fix is positional, not algorithmic: the SAME single warm call now runs FIRST in the finalize tail,
before `cache_ctx` and every heavy phase. `compute_availability` is untouched and remains the sole
producer. These tests therefore assert POSITION and its two consequences (liveness under an interrupted
tail; computing outside the job-start `_BarCache`), never a new derivation.

Every test builds its own tiny DB and calls `_refresh_ingest_aggregates` directly — the same technique
`test_ingest_finalize_fault_injection.py` uses. The boot-safety-net tests for `warmup._warm_availability`
live here too, rather than in `test_warmup.py`, so this whole module stays self-contained and fast (that
module's session-scoped fixture pays a full warm-up).
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import data_manager, prices, warmup as warmup_mod
from app.engine.data_manager import JobProgress
from app.models import AvailabilityCache, DailyPrice, ScannerRun

# SPY defines the trading calendar (`_trading_days` reads `cfg.etfs.index[0]`), so these five dates ARE
# the expected availability cells — the same construction `test_data_manager.py::coverage_engine` uses.
SPY_DAYS = [
    date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8),
]
PHASE_LOG = "J-05 finalize-tail phase timing"


@pytest.fixture()
def ingest_engine(tmp_path):
    """SPY bars on five dates + one snapshot — enough for `compute_availability` to produce an exact,
    fully-known calendar, and for the finalize hook to reach its later phases."""
    engine = make_engine(f"sqlite:///{tmp_path / 'availability_finalize.db'}")
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


def _stored_cell_dates(session: Session) -> list[str]:
    """The trading days in the persisted `AvailabilityCache` row, or [] when no row exists."""
    row = session.exec(select(AvailabilityCache)).first()
    if row is None:
        return []
    return [c["date"] for c in json.loads(row.payload_json)["cells"]]


def _logged_phases(caplog) -> list[str]:
    """The finalize-tail phase names in the order they were logged."""
    phases: list[str] = []
    for record in caplog.records:
        message = record.getMessage()
        if PHASE_LOG in message and "phase=" in message:
            phases.append(message.split("phase=")[1].split(" ")[0])
    return phases


# ==================================================================================================
# TC-1 — the regression: an interrupted heavy tail can no longer strand the cache
# ==================================================================================================
def test_availability_is_persisted_even_when_the_heavy_tail_is_interrupted(ingest_engine, monkeypatch):
    """The exact live failure. `_enter_ingest_heavy_warm` is the seam between the hoisted warm and the
    heavy tail; raising `KeyboardInterrupt` there reproduces "the process was interrupted after the bars
    committed but before the tail finished" — a `BaseException`, so none of the per-phase
    `except Exception` handlers can absorb it and the whole finalize is genuinely lost from that point on.

    The availability row must ALREADY be durable by then, carrying every trading day. Against the
    pre-fix ordering (the warm ran second-to-last, inside the tail) no row exists at all here — which is
    precisely how the live 5,391-vs-5,398 split arose."""
    cfg = load_config()

    def _interrupt(_job_id):
        raise KeyboardInterrupt("simulated mid-tail process interruption")

    monkeypatch.setattr(data_manager, "_enter_ingest_heavy_warm", _interrupt)

    with Session(ingest_engine) as session:
        prog = JobProgress(job_id="avail-interrupt", kind="fetch", start=SPY_DAYS[0], end=SPY_DAYS[-1])
        with pytest.raises(KeyboardInterrupt):
            data_manager._refresh_ingest_aggregates(session, cfg, prog)

    with Session(ingest_engine) as session:
        assert _stored_cell_dates(session) == [d.isoformat() for d in SPY_DAYS], (
            "the availability warm must be durable BEFORE the heavy tail runs — an interruption after "
            "the job's bars committed must never leave the heatmap behind the data"
        )


# ==================================================================================================
# TC-2 — position: availability is the FIRST phase of the finalize tail
# ==================================================================================================
def test_availability_warm_is_the_first_finalize_phase(ingest_engine, caplog):
    """Position stated directly, read from the hook's own phase-timing log. This is what makes the
    refresh immediate (~1s) instead of arriving after minutes of heavy warms."""
    cfg = load_config()
    with Session(ingest_engine) as session:
        prog = JobProgress(job_id="avail-order", kind="fetch", start=SPY_DAYS[0], end=SPY_DAYS[-1])
        with caplog.at_level(logging.INFO, logger="trendora.data_manager"):
            data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must never raise

    phases = _logged_phases(caplog)
    assert len(phases) >= 2, (
        f"the finalize tail must have logged several phases for this assertion to mean anything; got {phases}"
    )
    assert phases[0] == "availability_heatmap_warm", (
        "the availability warm is the cheapest phase and the one a lost tail strands — it must run first, "
        f"ahead of every heavy phase; observed order was {phases}"
    )


# ==================================================================================================
# TC-3 — the backfill split-brain: the warm never reads the job-start bar cache
# ==================================================================================================
def test_availability_warm_computes_outside_the_job_start_bar_cache(ingest_engine, monkeypatch):
    """`compute_availability` -> `_trading_days` -> `prices.bars_asof` PREFERS a `_BarCache` bound to the
    session, and the finalize tail attaches `_do_backfill`'s cache — prefilled at JOB START. Computing
    the calendar through it could persist a job-start calendar under the POST-job dataset stamp: a stale
    payload wearing a fresh stamp, which by construction never re-invalidates.

    Asserted structurally — at the moment the warm is invoked, no cache is attached to the session — so
    this holds regardless of what any particular cache happens to contain."""
    cfg = load_config()
    attached_during_warm: list[object] = []
    real_warm = data_manager.availability_cached_with_status

    def _spy(session, config=None):
        attached_during_warm.append(prices.active_bar_cache(session))
        return real_warm(session, config)

    monkeypatch.setattr(data_manager, "availability_cached_with_status", _spy)

    with Session(ingest_engine) as session:
        prog = JobProgress(job_id="avail-cache", kind="backfill", start=SPY_DAYS[0], end=SPY_DAYS[-1])
        # a backfill that stashed its job-start cache — the live shape this guards
        prog._shared_bar_cache = prices._BarCache()
        data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert attached_during_warm == [None], (
        "the availability warm must run BEFORE the job-start `_BarCache` is attached, so its calendar "
        f"comes from the committed DB; saw attached cache(s) {attached_during_warm}"
    )


# ==================================================================================================
# TC-4 — both job kinds refresh it (fetch adds bars, backfill adds snapshots)
# ==================================================================================================
@pytest.mark.parametrize("kind", ["fetch", "backfill"])
def test_both_fetch_and_backfill_refresh_availability(ingest_engine, kind):
    """The warm is unconditional (never gated on `prog.new_snapshot_dates`), because the dataset stamp is
    global: a bars-only fetch and a snapshots-only backfill must both leave the heatmap current."""
    cfg = load_config()
    with Session(ingest_engine) as session:
        prog = JobProgress(job_id=f"avail-{kind}", kind=kind, start=SPY_DAYS[0], end=SPY_DAYS[-1])
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)

    assert "availability_heatmap" in refreshed, (
        f"a {kind} job's finalize must honestly report the availability refresh; refreshed={refreshed}"
    )
    with Session(ingest_engine) as session:
        assert _stored_cell_dates(session) == [d.isoformat() for d in SPY_DAYS]


# ==================================================================================================
# TC-5 — the boot safety net (`warmup._warm_availability`)
# ==================================================================================================
def test_boot_warm_persists_availability_when_no_row_exists(ingest_engine, caplog):
    """The sibling `_warm_coverage_snapshot` always had. A DB whose ingest never reached its finalize has
    no `AvailabilityCache` row; the background warm-up must leave one — this is what repairs a cache
    stranded by an interrupted job, and the reason coverage self-healed at boot while the heatmap did
    not."""
    cfg = load_config()
    with Session(ingest_engine) as session:
        assert _stored_cell_dates(session) == []  # precondition: genuinely cold

    with caplog.at_level(logging.INFO, logger="trendora.warmup"):
        warmup_mod._warm_availability(ingest_engine, cfg)

    with Session(ingest_engine) as session:
        assert _stored_cell_dates(session) == [d.isoformat() for d in SPY_DAYS]
    assert "availability cache warmed" in caplog.text


def test_boot_warm_is_idempotent_on_an_already_current_row(ingest_engine):
    """A bootstrap/repair net, not a per-boot recompute: a second call is a cache HIT that persists
    nothing new (the owner's "no regular recompute" constraint)."""
    cfg = load_config()
    warmup_mod._warm_availability(ingest_engine, cfg)

    def _boom(*_a, **_k):
        raise AssertionError("an already-current row must never trigger a second compute")

    with Session(ingest_engine) as session:
        before = _stored_cell_dates(session)
    original = data_manager.compute_availability
    data_manager.compute_availability = _boom
    try:
        warmup_mod._warm_availability(ingest_engine, cfg)
    finally:
        data_manager.compute_availability = original

    with Session(ingest_engine) as session:
        assert _stored_cell_dates(session) == before


def test_boot_warm_failure_is_non_fatal(ingest_engine, monkeypatch, caplog):
    """Mirrors `_warm_coverage_snapshot`'s contract: a failure is caught + logged here and never
    propagates out to fail the whole warm-up."""
    cfg = load_config()

    def _boom(*_a, **_k):
        raise RuntimeError("simulated availability warm failure")

    monkeypatch.setattr(data_manager, "availability_cached_with_status", _boom)

    with caplog.at_level(logging.ERROR, logger="trendora.warmup"):
        warmup_mod._warm_availability(ingest_engine, cfg)  # must never raise

    assert "availability cache warm failed (non-fatal)" in caplog.text
