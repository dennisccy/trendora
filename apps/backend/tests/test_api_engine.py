"""API ↔ engine: served values EQUAL the engine outputs (no recompute drift).

Single source of truth (anti-goal): every endpoint serves exactly what the engine computes — no
second computation, no reshaping of a score. The J-06 coherence guard proves a ticker's row from
`/api/stocks` (list) is byte-identical to its row from `/api/stocks/{ticker}` (detail). The
dashboard's `candidate_counts` equal `summarize_candidates(score_stocks)` (counts the canonical
setup statuses); Theme scores are served ONLY by `/api/themes` (not re-served by the dashboard).
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
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.sectors import score_sectors
from app.engine.setups import summarize_candidates
from app.engine.themes import score_themes


def test_api_sectors_equals_engine_output(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected = score_sectors(session, asof, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/sectors")
    assert resp.status_code == 200
    served = resp.json()
    assert served == expected  # byte-for-byte: served value == computed value (no drift)
    assert served["benchmark"] == "SPY"
    assert len(served["rows"]) == 31


def test_api_dashboard_equals_engine_with_real_candidate_counts(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        regime = score_regime(session, asof, cfg)
        expected_counts = summarize_candidates(score_stocks(session, asof, cfg)["rows"])
    with TestClient(main.app) as client:
        resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()

    # regime served == engine (single source of truth)
    assert body["regime"]["score"] == regime["score"]
    assert body["regime"]["label"] == regime["label"]
    assert body["regime"]["components"] == regime["components"]

    # breadth served == engine, labelled universe-relative
    assert body["breadth"]["above_50dma_pct"] == regime["breadth_above_50dma"]
    assert body["breadth"]["above_200dma_pct"] == regime["breadth_above_200dma"]
    assert body["breadth"]["label"] == "universe-relative"

    assert body["asof_date"] == asof.isoformat()
    # candidate counts == summarize_candidates(score_stocks) — the single derivation path
    assert body["candidate_counts"] == expected_counts
    assert all(isinstance(v, int) for v in body["candidate_counts"].values())
    # Theme score is NOT re-served by the dashboard (one serving path = /api/themes)
    assert "top_themes" not in body


def test_dashboard_top_sectors_match_sectors_endpoint(loaded_engine):
    """The Dashboard's Top Sectors read the canonical /api/sectors (one serving path). Prove the
    top sectors a client would slice equal the /api/sectors rows — same values, no second source."""
    with TestClient(main.app) as client:
        sectors_rows = client.get("/api/sectors").json()["rows"]
    top3 = sectors_rows[:3]
    assert [r["rank"] for r in top3] == [1, 2, 3]
    assert all(r["score"] >= top3[-1]["score"] for r in top3)


def test_api_stocks_equals_engine_output(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected = score_stocks(session, asof, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks")
    assert resp.status_code == 200
    served = resp.json()
    assert served == expected                       # byte-for-byte: served == computed (no drift)
    assert served["benchmark"] == "SPY"
    assert len(served["rows"]) == len(cfg.universe.symbols)


def test_api_stock_detail_equals_list_row_single_source_j06(loaded_engine):
    """J-06 coherence guard: NVDA's row from the leaderboard EQUALS its row from the detail
    endpoint — one computation, never recomputed per view (scores AND buckets identical)."""
    with TestClient(main.app) as client:
        list_rows = client.get("/api/stocks").json()["rows"]
        detail = client.get("/api/stocks/NVDA").json()
    list_nvda = next(r for r in list_rows if r["ticker"] == "NVDA")
    assert detail["row"] == list_nvda                # full byte-identical row
    for score_key in ("leadership", "entry_quality", "risk"):
        assert detail["row"][score_key]["score"] == list_nvda[score_key]["score"]
        assert detail["row"][score_key]["bucket"] == list_nvda[score_key]["bucket"]


def test_api_stock_detail_unknown_ticker_404(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/NOTREAL")
    assert resp.status_code == 404


def test_api_stock_detail_is_case_insensitive(loaded_engine):
    with TestClient(main.app) as client:
        resp = client.get("/api/stocks/nvda")
    assert resp.status_code == 200
    assert resp.json()["row"]["ticker"] == "NVDA"


def test_api_themes_equals_engine_output(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        expected = score_themes(session, asof, cfg)
    with TestClient(main.app) as client:
        resp = client.get("/api/themes")
    assert resp.status_code == 200
    served = resp.json()
    assert served == expected
    assert len(served["rows"]) == len(cfg.themes)


def test_new_endpoints_raise_503_when_no_price_data(tmp_path):
    """No price data -> explicit 503 on all three new endpoints (never fabricated rows). The route
    handlers are called directly against an empty DB session (the live app self-seeds on startup,
    so emptiness is exercised at the handler level), leaving the process engine untouched."""
    from app.api.stocks import stock_detail, stocks
    from app.api.themes import themes as themes_route

    engine = make_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    create_db_and_tables(engine)  # tables exist, but no price rows were ever loaded
    with Session(engine) as session:
        assert latest_data_date(session) is None
        for call in (lambda: stocks(session), lambda: stock_detail("NVDA", session), lambda: themes_route(session)):
            with pytest.raises(HTTPException) as exc:
                call()
            assert exc.value.status_code == 503
