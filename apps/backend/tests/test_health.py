"""GET /api/health via FastAPI TestClient against the loaded temp DB."""
from __future__ import annotations

from fastapi.testclient import TestClient

import main


def test_health_returns_ok_shape(loaded_engine):
    # loaded_engine registers the temp DB as the process engine (see conftest).
    with TestClient(main.app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db_ok"] is True
    assert body["provider"] == "seed"
    assert body["last_run_date"] is None
    assert body["seed_latest_date"] is not None
    assert body["symbol_count"] > 100
