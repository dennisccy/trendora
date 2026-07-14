"""GET /api/research/budget API tests (goal-mcp-loop iter-32, J-17 / backlog B-903).

Mounts ONLY the budget router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB and NO
walk-forward boot -- the endpoint reads the two append-only ledger state files, not a snapshot (mirrors
`test_api_graveyard.py`'s DB-free four-test shape exactly: 200-on-missing, verbatim serving,
endpoint-equals-module, real-ledger status-derived count).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import budget
from app.engine.budget_accounting import build_budget_payload
from app.engine.evidence import LEDGER_PATH_ENV, resolve_ledger_path
from app.engine.graveyard import STAGING_LEDGER_PATH_ENV, resolve_staging_ledger_path
from app.engine.ledger import append_entry, count_trials


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(budget.router, prefix="/api")
    return TestClient(app)


def test_budget_endpoint_200_honest_empty_on_missing_ledger_files(tmp_path, monkeypatch):
    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing-canonical.jsonl"))
    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
    with _client() as client:
        resp = client.get("/api/research/budget")
    assert resp.status_code == 200
    body = resp.json()
    assert body["canonical"]["n_trials_to_date"] == 0
    assert body["canonical"]["required_p"] == 0.05
    assert body["canonical"]["spend_over_time"] == []
    assert body["staging"]["n_trials_to_date"] == 0
    assert body["staging"]["spend_over_time"] == []


def test_budget_endpoint_serves_a_fixture_entry_verbatim(tmp_path, monkeypatch):
    canonical = tmp_path / "canonical.jsonl"
    entry = {
        "claim": {
            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
            "horizon": 60, "direction": "positive",
        },
        "cohort_n": 100, "control_n": 50, "horizon": 60, "register_date": "2026-07-14",
        "verdict": {
            "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 1,
            "required_p": 0.05, "alpha_charged": 0.0,
        },
    }
    append_entry(str(canonical), entry)
    monkeypatch.setenv(LEDGER_PATH_ENV, str(canonical))
    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(tmp_path / "missing-staging.jsonl"))
    with _client() as client:
        resp = client.get("/api/research/budget")
    assert resp.status_code == 200
    body = resp.json()
    assert body["canonical"]["n_trials_to_date"] == 1
    assert body["canonical"]["n_trials_next"] == 2
    assert body["canonical"]["required_p"] == 0.05 / 2
    point = body["canonical"]["spend_over_time"][0]
    assert point["required_p"] == 0.05
    assert point["deflation_divisor"] == 1
    assert point["alpha_charged"] == 0.0
    assert point["register_date"] == "2026-07-14"
    assert point["status"] == "FAIL"


def test_budget_endpoint_equals_build_budget_payload_directly(monkeypatch):
    """Single-source assertion: the endpoint's response equals `build_budget_payload()` called directly
    against the SAME (real, committed) ledger files -- the page can never disagree with the composition
    module."""
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
    with _client() as client:
        resp = client.get("/api/research/budget")
    assert resp.status_code == 200
    assert resp.json() == build_budget_payload()


def test_budget_endpoint_real_ledgers_today_status_derived_trial_counts(monkeypatch):
    """Status-derived, not a hardcoded literal (iter-30/31 lesson): the expected counts are COMPUTED
    from the two real committed ledger files, not asserted as a bare "7"."""
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
    expected_canonical = count_trials(resolve_ledger_path())
    expected_staging = count_trials(resolve_staging_ledger_path())

    with _client() as client:
        resp = client.get("/api/research/budget")
    body = resp.json()
    assert body["canonical"]["n_trials_to_date"] == expected_canonical
    assert body["staging"]["n_trials_to_date"] == expected_staging
