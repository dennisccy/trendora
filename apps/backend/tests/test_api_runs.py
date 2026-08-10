"""GET /api/runs (+ /{run_id}) — the immutable as-of history endpoints (iter-5).

The app lifespan bootstraps the snapshot runs on startup, so the shared `loaded_engine` fixture
(also the process engine) has the configured Risk-off dates + the latest run persisted by the time
a `TestClient` context opens. These tests prove: the list is dated/descending with >=2 runs; the
detail serves the STORED snapshot (canonical StockRow shape) for a historical date; J-07's Risk-Off
run carries zero Actionable; unknown run -> 404; no price data -> 503.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event, func
from sqlmodel import Session, select

import main
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.prices import latest_data_date
from app.engine.universe_screen import read_pool
from app.models import DailyPrice, ScannerResult, ScannerRun

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
    # iter-33 (J-93) / iter-18: n_stocks is the POINT-IN-TIME-RESOLVED member count at the run's date (a
    # non-empty subset of the BROADENED 548-name pool at a full-universe bootstrap date), not the static
    # config.universe.symbols size.
    assert 0 < top["n_stocks"] <= len(read_pool())
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
    # iter-33 (J-93) / iter-18: one row per resolved member at the run's date (a non-empty subset of the
    # broadened 548-name pool — not the legacy static config.universe.symbols).
    assert 0 < len(detail["rows"]) <= len(read_pool())

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


# ==================================================================================================
# ops-hardening iter-56 (J-06 closure) -- GET /api/runs's n_stocks N+1 fix. Live profiling against the
# grown 8.37 GB dev DB (2,937 stored ScannerRun rows) confirmed one ScannerResult COUNT query issued
# PER stored run inside a Python loop (see the dev handoff for the exact profiled query count) -- fixed
# with a single grouped aggregate query. Same endpoint, same response shape, byte-identical n_stocks.
#
# `multi_run_engine` is a small hand-built DB (mirrors `test_data_manager.py`'s `coverage_engine`/
# `finalize_hook_engine` style) — deliberately NOT the session-scoped `loaded_engine` (a full 30-year
# committed-seed backfill+warm, far more setup cost than these query-shape/byte-identity proofs need).
# ==================================================================================================
@pytest.fixture()
def multi_run_engine(tmp_path):
    """THREE `ScannerRun` rows carrying 3/0/2 `ScannerResult` children respectively — deliberately
    includes a ZERO-result run so the grouped query's "absent from GROUP BY" default path is exercised
    by the SAME fixture every test in this section shares."""
    engine = make_engine(f"sqlite:///{tmp_path / 'multi_run.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        session.add(DailyPrice(
            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
        ))
        session.commit()
        for i, n_results in enumerate((3, 0, 2)):
            run = ScannerRun(
                asof_date=date(2024, 1, 2) + timedelta(days=i), created_at=datetime(2024, 1, 2 + i),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Choppy",
                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            for j in range(n_results):
                session.add(ScannerResult(
                    run_id=run.id, ticker=f"T{i}{j}", name=f"T{i}{j} Corp", leadership_score=1.0,
                    leadership_bucket="Leader", entry_quality_score=1.0, entry_quality_bucket="Good",
                    risk_score=1.0, risk_bucket="Low", setup_status="Actionable", rank=j + 1,
                    record_json="{}",
                ))
            session.commit()
    return engine


def test_api_runs_n_stocks_single_grouped_query_not_per_run(multi_run_engine):
    """TC-2 -- the number of ScannerResult queries issued for ONE GET /api/runs request is a small
    constant that does NOT scale with the number of stored runs (never one COUNT query per run)."""
    from app.api.runs import runs as runs_route

    statements: list[str] = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        if "scanner_results" in statement.lower():
            statements.append(statement)

    event.listen(multi_run_engine, "before_cursor_execute", _capture)
    try:
        with Session(multi_run_engine) as session:
            n_runs = session.exec(select(func.count()).select_from(ScannerRun)).one()
            if isinstance(n_runs, tuple):
                n_runs = n_runs[0]
            result = runs_route(session)
    finally:
        event.remove(multi_run_engine, "before_cursor_execute", _capture)

    assert n_runs == 3  # sanity: this fixture's own 3 runs
    assert len(result["runs"]) == n_runs
    # exactly one grouped query, regardless of n_runs -- would be n_runs under the old per-run COUNT loop
    assert len(statements) == 1, (
        f"expected exactly 1 grouped ScannerResult query, saw {len(statements)} for {n_runs} stored runs"
    )


def test_api_runs_n_stocks_byte_identical_to_per_run_count(multi_run_engine):
    """TC-3 -- every stored run's served n_stocks is byte-identical to a direct per-run COUNT (the
    pre-fix per-run computation) -- the grouped-query rewrite changes only the query plan, never the
    served value. Exercises the 3/0/2-result spread, including the ZERO-result run."""
    from app.api.runs import runs as runs_route

    with Session(multi_run_engine) as session:
        result = runs_route(session)
        run_ids = [r.id for r in session.exec(select(ScannerRun)).all()]
        expected_by_run_id = {
            rid: int(
                session.scalar(
                    select(func.count()).select_from(ScannerResult).where(ScannerResult.run_id == rid)
                ) or 0
            )
            for rid in run_ids
        }

    assert result["runs"]  # sanity: non-empty
    assert len(result["runs"]) == len(expected_by_run_id) == 3
    assert sorted(expected_by_run_id.values()) == [0, 2, 3]  # the fixture's own 3/0/2 spread, sanity
    for row in result["runs"]:
        assert row["n_stocks"] == expected_by_run_id[row["run_id"]]


def test_api_runs_n_stocks_zero_for_run_with_no_stored_results(multi_run_engine):
    """A ScannerRun with zero child ScannerResult rows reads n_stocks == 0 -- the grouped query's honest
    default for a run absent from the GROUP BY result, exactly what the old per-run COUNT() returned for
    an empty run (never a KeyError, never a fabricated count)."""
    from app.api.runs import runs as runs_route

    with Session(multi_run_engine) as session:
        result = runs_route(session)

    zero_result_rows = [row for row in result["runs"] if row["n_stocks"] == 0]
    assert len(zero_result_rows) == 1  # exactly the one 0-result run the fixture built
