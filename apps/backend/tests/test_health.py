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


def test_health_carries_readiness_and_warmup(loaded_engine):
    """iter-28 (J-40): the single canonical readiness endpoint extends /api/health with the honest
    readiness state + warm-up progress. The TestClient runs the lifespan (fast latest-snapshot + the
    background warm-up), so by the time we read /api/health the latest snapshot is servable -> the state
    is one of the three honest labels and the warm-up progress is a real {done, total} (never fabricated)."""
    with TestClient(main.app) as client:
        body = client.get("/api/health").json()
    assert body["readiness"] in {"ready", "initializing", "unavailable"}
    # the latest snapshot is produced synchronously before serving, so it is never 'unavailable' here.
    assert body["readiness"] != "unavailable"
    warmup = body["warmup"]
    assert set(warmup) == {"done", "total", "status", "message"}
    assert isinstance(warmup["done"], int) and warmup["done"] >= 0
    assert isinstance(warmup["total"], int) and warmup["total"] >= 0
    assert warmup["done"] <= warmup["total"]
    assert warmup["message"] == f"history {warmup['done']}/{warmup['total']}"
    # the config-derived poll cadences the frontend badge reads (no client-side poll literal)
    assert body["poll_interval_seconds"] > 0
    assert body["poll_idle_interval_seconds"] >= body["poll_interval_seconds"]
