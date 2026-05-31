"""Methodology API test (iter-12, J-12) — GET /api/methodology returns the config-backed catalog.

Mounts ONLY the methodology router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB
and NO walk-forward boot — the endpoint reads config, not a snapshot (iter-10 slow-boot lesson)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import methodology
from app.config import get_config
from app.engine.methodology import build_catalog


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(methodology.router, prefix="/api")
    return TestClient(app)


def test_methodology_endpoint_returns_catalog():
    with _client() as client:
        resp = client.get("/api/methodology")
        assert resp.status_code == 200
        data = resp.json()
        # the endpoint re-formats config only — it serves build_catalog verbatim
        assert data == build_catalog(get_config())
        assert data["entries"]
        kinds = {e["kind"] for e in data["entries"]}
        assert kinds == {"setup", "pattern"}


def test_methodology_endpoint_documents_vcp():
    with _client() as client:
        data = client.get("/api/methodology").json()
        vcp = next(e for e in data["entries"] if e["key"] == "vcp")
        assert vcp["kind"] == "pattern"
        assert vcp["thresholds"]  # config-referenced VCP thresholds present
