"""GET /api/research/graveyard API tests (goal-mcp-loop iter-31, J-19 / backlog B-902).

Mounts ONLY the graveyard router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB and
NO walk-forward boot -- the endpoint reads the two append-only ledger state files, not a snapshot
(mirrors `test_api_registry.py`'s DB-free pattern exactly).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import graveyard
from app.engine.evidence import LEDGER_PATH_ENV
from app.engine.graveyard import (
    LEDGER_CANONICAL,
    LEDGER_STAGING,
    STAGING_LEDGER_PATH_ENV,
    build_graveyard_payload,
)
from app.engine.ledger import append_entry, read_entries
from app.engine.registry import REGISTRY_PATH_ENV


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(graveyard.router, prefix="/api")
    return TestClient(app)


def test_graveyard_endpoint_200_empty_on_missing_ledger_files(tmp_path, monkeypatch):
    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing-canonical.jsonl"))
    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
    with _client() as client:
        resp = client.get("/api/research/graveyard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["entries"] == []
    assert "revisit_protocol" in body


def test_graveyard_endpoint_serves_a_fixture_entry_verbatim(tmp_path, monkeypatch):
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
    canonical = tmp_path / "canonical.jsonl"
    entry = {
        "claim": {
            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
            "horizon": 60, "direction": "positive",
        },
        "cohort_n": 100, "control_n": 50, "horizon": 60, "register_date": "2026-07-03",
        "verdict": {
            "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 3,
        },
    }
    append_entry(str(canonical), entry)
    monkeypatch.setenv(LEDGER_PATH_ENV, str(canonical))
    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
    with _client() as client:
        resp = client.get("/api/research/graveyard")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["entries"]) == 1
    served = body["entries"][0]
    assert served["ledger"] == LEDGER_CANONICAL
    assert served["claim"] == entry["claim"]
    assert served["verdict"] == entry["verdict"]
    assert served["register_date"] == entry["register_date"]
    assert served["horizon"] == entry["horizon"]
    assert served["cohort_n"] == entry["cohort_n"]
    assert served["control_n"] == entry["control_n"]


def test_graveyard_endpoint_equals_build_graveyard_payload_directly(monkeypatch):
    """Single-source assertion: the endpoint's response equals `build_graveyard_payload()` called
    directly against the SAME (real, committed) ledger files -- the page can never disagree with the
    composition module."""
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
    with _client() as client:
        resp = client.get("/api/research/graveyard")
    assert resp.status_code == 200
    assert resp.json() == build_graveyard_payload()


def test_graveyard_endpoint_real_ledgers_today_serve_fourteen_non_pass_entries(monkeypatch):
    """Status-derived, not a hardcoded literal (iter-30 lesson): the expected count is COMPUTED from the
    two real committed ledger files' own non-PASS rows, not asserted as a bare "14"."""
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
    from app.engine.evidence import resolve_ledger_path
    from app.engine.graveyard import resolve_staging_ledger_path

    canonical_raw = [e for e in read_entries(resolve_ledger_path()) if e.get("type") != "forward_walk"]
    staging_raw = [e for e in read_entries(resolve_staging_ledger_path()) if e.get("type") != "forward_walk"]
    expected = sum(1 for e in canonical_raw + staging_raw if e["verdict"]["status"] != "PASS")

    with _client() as client:
        resp = client.get("/api/research/graveyard")
    body = resp.json()
    assert len(body["entries"]) == expected
    assert {e["ledger"] for e in body["entries"]} <= {LEDGER_CANONICAL, LEDGER_STAGING}
