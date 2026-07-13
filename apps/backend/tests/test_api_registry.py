"""GET /api/research/registry API tests (goal-mcp-loop iter-30, J-18 / backlog B-901).

Mounts ONLY the registry router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB and NO
walk-forward boot — the endpoint reads the append-only state file, not a snapshot (mirrors
test_api_methodology.py's DB-free pattern exactly).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import registry
from app.engine.ledger import append_entry
from app.engine.registry import REGISTRY_PATH_ENV, load_registrations


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(registry.router, prefix="/api")
    return TestClient(app)


def test_registry_endpoint_empty_on_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv(REGISTRY_PATH_ENV, str(tmp_path / "missing" / "pre-registrations.jsonl"))
    with _client() as client:
        resp = client.get("/api/research/registry")
    assert resp.status_code == 200
    assert resp.json() == {"registrations": []}


def test_registry_endpoint_serves_backfilled_rows_verbatim(tmp_path, monkeypatch):
    path = tmp_path / "pre-registrations.jsonl"
    row = {
        "id": "factor-vcp_contraction-d10-h60",
        "selectors": {
            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
            "horizon": 60, "direction": "positive",
        },
        "rationale": "Does the post-contraction expansion edge persist over a quarter?",
        "registered_by": "backfill",
        "registered_date": "2026-07-03",
        "source": "proposer-guidance.md §4.1 #2; certified-claims.jsonl",
        "status": "tested",
    }
    append_entry(str(path), row)
    monkeypatch.setenv(REGISTRY_PATH_ENV, str(path))
    with _client() as client:
        resp = client.get("/api/research/registry")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["registrations"]) == 1
    served = body["registrations"][0]
    # re-formats verbatim -- every field byte-matches what was written, nothing recomputed.
    for key, value in row.items():
        assert served[key] == value


def test_registry_endpoint_equals_loader_output_directly(monkeypatch):
    """Single-source assertion: the endpoint's response equals `load_registrations()` called directly
    against the SAME (real, committed) file — the page and the gate can never disagree."""
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)  # use the real config-resolved committed file
    with _client() as client:
        resp = client.get("/api/research/registry")
    assert resp.status_code == 200
    assert resp.json() == {"registrations": load_registrations()}
    assert len(resp.json()["registrations"]) == 11  # the committed iter-30 backfill
