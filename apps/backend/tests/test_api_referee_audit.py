"""GET /api/research/referee-audit API tests (goal-mcp-loop iter-36, J-22 / backlog B-102).

Mounts ONLY the referee-audit router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB
and NO walk-forward boot -- the endpoint reads a single state-file artifact, not a snapshot (mirrors
`test_api_budget.py` / `test_api_graveyard.py`'s DB-free pattern exactly).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import referee_audit
from app.engine.referee import STATUS_FAIL
from app.engine.referee_audit import (
    REFEREE_AUDIT_PATH_ENV,
    build_referee_audit_report,
    read_referee_audit_report,
    write_referee_audit_report,
)


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(referee_audit.router, prefix="/api")
    return TestClient(app)


def test_referee_audit_endpoint_200_honest_empty_on_missing_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(tmp_path / "does-not-exist.json"))
    with _client() as client:
        resp = client.get("/api/research/referee-audit")
    assert resp.status_code == 200
    assert resp.json() == {"report": None}


def test_referee_audit_endpoint_200_honest_unreadable_on_corrupt_artifact_never_500(tmp_path, monkeypatch):
    target = tmp_path / "corrupt.json"
    target.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    with _client() as client:
        resp = client.get("/api/research/referee-audit")
    assert resp.status_code == 200
    body = resp.json()
    assert body["report"]["status"] == "unreadable"
    assert body["report"]["contaminated_verdict"] is None


def test_referee_audit_endpoint_serves_a_fixture_artifact_verbatim(tmp_path, monkeypatch):
    target = tmp_path / "report.json"
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=200, seed=20240601, alpha=0.05,
        false_pass_count=9, n_insufficient_null=0, source_factor="leadership_score",
        contaminated_factor_horizon=5,
        contaminated_verdict={"status": STATUS_FAIL, "reason": "fixture", "p_value": 0.9},
    )
    write_referee_audit_report(report)
    with _client() as client:
        resp = client.get("/api/research/referee-audit")
    assert resp.status_code == 200
    body = resp.json()
    assert body["report"] == report
    assert body["report"]["false_pass_count"] == 9
    assert body["report"]["contaminated_expected_outcome"] == "rejected"
    assert body["report"]["contaminated_caught"] is True


def test_referee_audit_endpoint_equals_read_referee_audit_report_directly(tmp_path, monkeypatch):
    """Single-source assertion: the endpoint's response equals `read_referee_audit_report()` called
    directly against the SAME artifact -- the page can never disagree with the reader module."""
    target = tmp_path / "report.json"
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=0.05,
        false_pass_count=0, n_insufficient_null=0, source_factor="rs_spy_3m",
        contaminated_factor_horizon=5,
        contaminated_verdict={"status": STATUS_FAIL, "reason": "fixture"},
    )
    write_referee_audit_report(report)
    with _client() as client:
        resp = client.get("/api/research/referee-audit")
    assert resp.status_code == 200
    assert resp.json() == {"report": read_referee_audit_report()}


def test_referee_audit_endpoint_never_recomputes_beyond_the_persisted_artifact(tmp_path, monkeypatch):
    """The endpoint must not re-derive `false_pass_rate` / CI from `false_pass_count` -- it re-serves
    whatever the artifact carries VERBATIM, even a deliberately inconsistent fixture value (proves no
    recompute path exists in the router)."""
    target = tmp_path / "report.json"
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=200, seed=1, alpha=0.05,
        false_pass_count=9, n_insufficient_null=0, source_factor="x",
        contaminated_factor_horizon=5,
        contaminated_verdict={"status": STATUS_FAIL, "reason": "fixture"},
    )
    report["false_pass_rate"] = 0.9999  # deliberately inconsistent with false_pass_count/n_null_trials
    write_referee_audit_report(report)
    with _client() as client:
        resp = client.get("/api/research/referee-audit")
    assert resp.json()["report"]["false_pass_rate"] == 0.9999  # verbatim, not recomputed to 0.045
