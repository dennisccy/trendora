"""goal-market-compass iter-2 — the "compass content" finalize-tail phase in `_refresh_ingest_aggregates`
(data_manager.py, inserted between the market-phase warm and the forward-aggregates phase).

TC-31: a normal backfill still completes and every pre-existing "Refreshed:" phase still reports its
prior counts unchanged. Also proves the new phase's own try/except isolation: a producer exception here
is caught by ITS OWN handler and never blocks or crashes the rest of `_refresh_ingest_aggregates` (the
same isolate-and-continue contract the market-phase loop already has).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import compass, data_manager
from app.engine.data_manager import JobProgress
from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun

ASOF = date(2024, 7, 8)
PRIOR_ASOF = date(2024, 7, 1)


@pytest.fixture()
def finalize_engine(tmp_path):
    """Two `ScannerRun`s (so `session_delta` has a real prior session) each with one `ScannerResult`,
    plus SPY bars so the market-phase / forward-aggregate phases can also run in the same pass."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'finalize_compass.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d in (PRIOR_ASOF, ASOF):
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for d, score in ((PRIOR_ASOF, 50.0), (ASOF, 55.0)):
            run = ScannerRun(
                asof_date=d, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
                regime_score=score, regime_label=cfg.regime.labels[0], regime_components_json="[]",
                breadth_above_50dma=50.0, breadth_above_200dma=50.0,
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            session.add(ScannerResult(
                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=92.0, leadership_bucket="A",
                entry_quality_score=85.0, entry_quality_bucket="B", risk_score=40.0, risk_bucket="C",
                setup_status="Breakout-watch", rank=1,
                record_json=json.dumps({"ticker": "AAA", "invalidation": {"note": "AAA note"}}),
            ))
            session.commit()
    return engine


def _progress() -> JobProgress:
    prog = JobProgress(job_id="finalize-compass-test", kind="backfill", start=PRIOR_ASOF, end=ASOF)
    prog.dates_total = 1
    prog.dates_done = 1
    prog.new_snapshot_dates = [ASOF]  # only the LATEST date was "newly produced" this run
    return prog


def test_compass_content_phase_persists_manifest_and_reports_refreshed(finalize_engine):
    cfg = load_config()
    with Session(finalize_engine) as session:
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, _progress())
    assert "next-session_manifest" in refreshed
    assert "market_phase" in refreshed  # the pre-existing phase this one is inserted after still ran

    with Session(finalize_engine) as session:
        rows = session.exec(select(NextSessionManifest).where(NextSessionManifest.as_of == ASOF)).all()
    assert len(rows) == 1
    assert rows[0].content_hash


def test_compass_content_failure_is_isolated_forward_aggregates_still_runs(finalize_engine, monkeypatch, caplog):
    """The new phase's own try/except must catch a producer exception and continue the finalize tail —
    it must NEVER block or crash the pre-existing forward-aggregates phase that runs right after it."""
    def _boom(*args, **kwargs):
        raise RuntimeError("synthetic compass-content failure")

    monkeypatch.setattr(compass, "get_or_create_manifest", _boom)
    cfg = load_config()
    with caplog.at_level("ERROR"):
        with Session(finalize_engine) as session:
            refreshed = data_manager._refresh_ingest_aggregates(session, cfg, _progress())

    assert "next-session_manifest" not in refreshed  # honestly NOT reported as refreshed -- it failed
    assert "forward_aggregates" in refreshed  # the NEXT phase still ran -- isolation held
    assert any("compass-content warm failed" in record.message for record in caplog.records)

    with Session(finalize_engine) as session:
        rows = session.exec(select(NextSessionManifest)).all()
    assert rows == []  # no partial/corrupt row was written


def test_compass_content_is_a_noop_when_no_new_snapshot_dates(finalize_engine):
    """Mirrors the market-phase loop's own contract: an empty `new_snapshot_dates` (e.g. a re-run that
    added no new date) means this phase does no work and is honestly omitted from `refreshed`."""
    cfg = load_config()
    prog = _progress()
    prog.new_snapshot_dates = []
    with Session(finalize_engine) as session:
        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
    assert "next-session_manifest" not in refreshed
