"""GET /api/evidence + the stocks no-recompute regression (goal-mcp-loop iter-1).

The endpoint is the read-only certified-claims ledger surface: it must serve a 200 with an empty payload
against the EMPTY/absent ledger (never a 500), and re-display a seeded PASS claim verbatim in both
`claims` and `proven_signals`. The regression guard proves the additive evidence work changed NOTHING in
the canonical `/api/stocks` payload (no recompute, no leaked evidence field on the scored rows).
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

import main
from app.engine.evidence import LEDGER_PATH_ENV
from app.engine.ledger import append_entry
from app.engine.snapshot_serving import resolved_run, stocks_payload


def test_api_evidence_empty_ledger_returns_200_empty(loaded_engine, tmp_path, monkeypatch):
    # point at a path that does not exist — an absent ledger is an EMPTY ledger, never a 500.
    monkeypatch.setenv(LEDGER_PATH_ENV, str(tmp_path / "missing" / "certified-claims.jsonl"))
    with TestClient(main.app) as client:
        resp = client.get("/api/evidence")
    assert resp.status_code == 200
    assert resp.json() == {"claims": [], "proven_signals": {}}


def test_api_evidence_seeded_pass_claim_is_served(loaded_engine, tmp_path, monkeypatch):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(
        str(ledger),
        {
            "claim": {
                "kind": "factor",
                "factor": "leadership_score",
                "signal": "leadership_score",
                "slice_kind": "decile",
                "decile": 10,
                "horizon": 20,
                "direction": "positive",
            },
            "register_date": "2024-06-01",
            "horizon": 20,
            "cohort_n": 42,
            "control_n": 40,
            "verdict": {"status": "PASS", "reason": "certified", "control_excess": 0.018},
        },
    )
    monkeypatch.setenv(LEDGER_PATH_ENV, str(ledger))
    with TestClient(main.app) as client:
        body = client.get("/api/evidence").json()

    assert len(body["claims"]) == 1
    assert list(body["proven_signals"].keys()) == ["leadership_score"]
    served = body["proven_signals"]["leadership_score"]
    assert served["proven"] is True
    assert served["register_date"] == "2024-06-01"
    assert served["verdict"]["status"] == "PASS"
    assert served["verdict"]["control_excess"] == 0.018


def test_api_stocks_unchanged_no_recompute_regression(loaded_engine, monkeypatch):
    """Regression: the additive evidence work must not touch the canonical `/api/stocks` payload. The
    served rows stay byte-identical to the engine's stored snapshot (no recompute in the read path), and
    NO evidence/proven field leaks onto a scored row (the badge is a purely additive FRONTEND overlay)."""
    # an empty ledger must not matter to /api/stocks at all.
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    with TestClient(main.app) as client:
        served = client.get("/api/stocks").json()
    with Session(loaded_engine) as session:
        expected = stocks_payload(session, resolved_run(session, None))

    assert served == expected  # byte-for-byte: the read path serves the stored snapshot, unchanged
    for row in served["rows"]:
        # the three canonical scores are present + numeric, and carry NO evidence/proven key
        for key in ("leadership", "entry_quality", "risk"):
            assert isinstance(row[key]["score"], (int, float))
        assert "evidence" not in row
        assert "proven" not in row
        assert "proven_signals" not in row
    assert "proven_signals" not in served
