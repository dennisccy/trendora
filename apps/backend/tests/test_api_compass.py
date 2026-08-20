"""GET /api/compass (goal-market-compass iter-2) — API-layer contract: create-once-on-GET / serve-from-
storage (TC-1), every new field present at the response layer directly, and honest as-of error mapping.

`compass_engine` is a small hand-built DB (mirrors `test_api_runs.py`'s `multi_run_engine` style) —
deliberately NOT the session-scoped `loaded_engine`. The route function is called DIRECTLY with a
session (the SAME lightweight pattern `test_api_runs.py::test_api_runs_n_stocks_single_grouped_query_not_per_run`
uses) rather than through a full TestClient/lifespan, since these are query-shape/contract proofs, not
browser-facing checks (those are QA's job).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import compass as compass_module
from app.models import DailyPrice, NextSessionManifest, ScannerResult, ScannerRun


@pytest.fixture()
def cfg():
    return load_config()


@pytest.fixture()
def compass_engine(tmp_path):
    """Two `ScannerRun` rows (so a "prior session" exists) each carrying one `ScannerResult`, plus the
    `DailyPrice` bars `resolve_as_of_date`/`latest_data_date` need to resolve `as_of` at all."""
    engine = make_engine(f"sqlite:///{tmp_path / 'compass_api.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for bar_date in (date(2024, 6, 1), date(2024, 6, 8)):
            session.add(DailyPrice(
                symbol="SPY", date=bar_date, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
            ))
        session.commit()
        for i, (asof, regime_score) in enumerate(((date(2024, 6, 1), 50.0), (date(2024, 6, 8), 58.0))):
            run = ScannerRun(
                asof_date=asof, created_at=datetime(2024, 6, 1 + i * 7, tzinfo=timezone.utc),
                provider="seed", benchmark="SPY", regime_score=regime_score, regime_label="Expansion",
                regime_components_json="[]", breadth_above_50dma=55.0, breadth_above_200dma=60.0,
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


def test_compass_route_serves_every_new_field_directly(compass_engine, cfg):
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        result = compass_route(None, session)

    # NOTES: assert every new field at the response layer itself -- never behind a fixture-data gate.
    assert result["as_of"] == "2024-06-08"
    assert isinstance(result["session_delta"], dict)
    for key in ("prior_as_of", "gap_days", "changes", "suppressed", "suppressed_count"):
        assert key in result["session_delta"]
    assert isinstance(result["narrative"], dict) and "sentences" in result["narrative"]
    assert isinstance(result["selection"], dict)
    for key in ("candidates", "why_not", "disposition_tally", "candidates_empty_reason"):
        assert key in result["selection"]
    assert isinstance(result["content_hash"], str) and len(result["content_hash"]) == 64  # sha256 hex


def test_compass_route_computes_once_serves_from_storage_after(compass_engine, cfg, monkeypatch):
    """TC-1: the second call for the same as-of returns byte-identical content with ZERO additional
    producer calls (get_or_create_manifest short-circuits on the stored row)."""
    from app.api.compass import compass as compass_route

    calls = {"n": 0}
    original = compass_module.build_manifest_payload

    def counting_build(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(compass_module, "build_manifest_payload", counting_build)

    with Session(compass_engine) as session:
        first = compass_route(None, session)
    assert calls["n"] == 1

    with Session(compass_engine) as session:
        second = compass_route(None, session)
    assert calls["n"] == 1  # no additional producer call on the second, separate-request hit

    assert first == second

    with Session(compass_engine) as session:
        rows = session.exec(
            __import__("sqlmodel").select(NextSessionManifest).where(NextSessionManifest.as_of == date(2024, 6, 8))
        ).all()
    assert len(rows) == 1


def test_compass_route_unknown_asof_returns_honest_error_never_fabricated(compass_engine, cfg):
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        with pytest.raises(HTTPException) as exc_info:
            compass_route("2099-01-01", session)  # far future -- no stored run for this as-of
    assert exc_info.value.status_code in (400, 404, 422, 503)  # snapshot_serving's honest as-of mapping
    assert exc_info.value.detail  # a real message, never a silent/empty fabricated body


def test_compass_route_historical_asof_serves_that_dates_own_manifest(compass_engine, cfg):
    from app.api.compass import compass as compass_route

    with Session(compass_engine) as session:
        result = compass_route("2024-06-01", session)
    assert result["as_of"] == "2024-06-01"
    assert result["session_delta"]["prior_as_of"] is None  # earliest stored run -- explicit no-prior-run state
