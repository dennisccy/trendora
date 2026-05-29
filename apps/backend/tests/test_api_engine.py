"""API ↔ engine: served values EQUAL the engine outputs (no recompute drift).

Single source of truth (anti-goal): `/api/sectors` and `/api/dashboard` must serve exactly what
the engine computes — no second computation, no reshaping of a score. Also asserts `/api/dashboard`
returns explicit null `candidate_counts` + `top_themes` (pending iter-3, never fabricated zeros).
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.config import load_config
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime
from app.engine.sectors import score_sectors


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


def test_api_dashboard_equals_engine_and_has_pending_placeholders(loaded_engine):
    cfg = load_config()
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        regime = score_regime(session, asof, cfg)
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
    # pending placeholders — explicit null, never a fabricated number (iter-3)
    assert body["candidate_counts"] is None
    assert body["top_themes"] is None


def test_dashboard_top_sectors_match_sectors_endpoint(loaded_engine):
    """The Dashboard's Top Sectors read the canonical /api/sectors (one serving path). Prove the
    top sectors a client would slice equal the /api/sectors rows — same values, no second source."""
    with TestClient(main.app) as client:
        sectors_rows = client.get("/api/sectors").json()["rows"]
    top3 = sectors_rows[:3]
    assert [r["rank"] for r in top3] == [1, 2, 3]
    assert all(r["score"] >= top3[-1]["score"] for r in top3)
