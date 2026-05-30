"""GET /api/runs (+ /{run_id}) — the immutable as-of history endpoints (iter-5).

The app lifespan bootstraps the snapshot runs on startup, so the shared `loaded_engine` fixture
(also the process engine) has the configured Risk-off dates + the latest run persisted by the time
a `TestClient` context opens. These tests prove: the list is dated/descending with >=2 runs; the
detail serves the STORED snapshot (canonical StockRow shape) for a historical date; J-07's Risk-Off
run carries zero Actionable; unknown run -> 404; no price data -> 503.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date

_RUN_SUMMARY_FIELDS = {"run_id", "asof_date", "created_at", "regime", "candidate_counts", "n_stocks"}


def test_api_runs_lists_runs_descending_by_date(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/runs")
    assert resp.status_code == 200
    runs = resp.json()["runs"]

    assert len(runs) >= 2  # J-08 precondition: >=2 dated runs
    dates = [r["asof_date"] for r in runs]
    assert dates == sorted(dates, reverse=True)  # descending by as-of date

    top = runs[0]
    assert _RUN_SUMMARY_FIELDS <= set(top)
    assert top["regime"]["label"]
    assert isinstance(top["regime"]["score"], (int, float))
    assert top["n_stocks"] == len(load_config().universe.symbols)
    # candidate counts carry the canonical statuses (a number always renders)
    assert isinstance(top["candidate_counts"].get("Actionable"), int)


def test_api_run_detail_returns_stored_snapshot(loaded_engine):
    with TestClient(main.app) as client:
        runs = client.get("/api/runs").json()["runs"]
        oldest = min(runs, key=lambda r: r["asof_date"])  # a historical as-of view
        resp = client.get(f"/api/runs/{oldest['run_id']}")
    assert resp.status_code == 200
    detail = resp.json()

    assert detail["asof_date"] == oldest["asof_date"]
    assert detail["regime"]["label"] == oldest["regime"]["label"]
    assert detail["regime"]["components"]  # the regime panel carries its component breakdown
    assert detail["breadth"]["label"] == "universe-relative"
    assert len(detail["rows"]) == len(load_config().universe.symbols)

    # the stored rows are the canonical StockRow shape (so the detail page reuses the leaderboard row)
    row = detail["rows"][0]
    assert {"ticker", "leadership", "entry_quality", "risk", "setup", "rank"} <= set(row)
    assert row["rank"] == 1
    for block in ("leadership", "entry_quality", "risk"):
        assert {"score", "bucket", "components"} <= set(row[block])


def test_api_run_detail_rankings_differ_from_latest_j08(loaded_engine):
    """J-08 at the API level: an older run's stored rankings/scores differ from the latest run's."""
    with TestClient(main.app) as client:
        runs = client.get("/api/runs").json()["runs"]
        latest = max(runs, key=lambda r: r["asof_date"])
        oldest = min(runs, key=lambda r: r["asof_date"])
        latest_rows = client.get(f"/api/runs/{latest['run_id']}").json()["rows"]
        oldest_rows = client.get(f"/api/runs/{oldest['run_id']}").json()["rows"]

    assert latest["asof_date"] != oldest["asof_date"]
    latest_lead = {r["ticker"]: r["leadership"]["score"] for r in latest_rows}
    oldest_lead = {r["ticker"]: r["leadership"]["score"] for r in oldest_rows}
    common = set(latest_lead) & set(oldest_lead)
    assert common
    assert any(latest_lead[t] != oldest_lead[t] for t in common)  # frozen as-of, not recomputed today


def test_api_risk_off_run_has_zero_actionable_j07(loaded_engine):
    """J-07 at the API level: the Risk-Off run's regime reads 'Risk-off' and NO stored result
    carries the setup status 'Actionable'."""
    with TestClient(main.app) as client:
        runs = client.get("/api/runs").json()["runs"]
        risk_off = [r for r in runs if r["regime"]["label"] == "Risk-off"]
        assert risk_off, "expected a seeded Risk-off run in the history"
        detail = client.get(f"/api/runs/{risk_off[0]['run_id']}").json()

    assert detail["regime"]["label"] == "Risk-off"
    assert detail["rows"]
    assert all(row["setup"]["status"] != "Actionable" for row in detail["rows"])


def test_api_run_detail_unknown_run_404(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/runs/99999999")
    assert resp.status_code == 404


def test_runs_endpoints_raise_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 on both new endpoints (never fabricated rows). The handlers are
    called directly against an empty DB session, leaving the process engine untouched."""
    from app.api.runs import run_detail, runs as runs_route

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)  # tables exist, but no price rows were ever loaded
    with Session(engine) as session:
        assert latest_data_date(session) is None
        for call in (lambda: runs_route(session), lambda: run_detail(1, session)):
            with pytest.raises(HTTPException) as exc:
                call()
            assert exc.value.status_code == 503
