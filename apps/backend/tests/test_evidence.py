"""Read-side evidence resolver units (goal-mcp-loop iter-1).

`app.engine.evidence` is the SINGLE source of displayed proven-ness — it RECOMPUTES NOTHING; it projects
the append-only certified-claims ledger into the read-only `/api/evidence` payload. These tests pin the
fail-safe contract:
  - absent/empty ledger => empty payload (every signal reads "Not yet proven");
  - a `verdict.status == "PASS"` entry that NAMES a signal => that signal is Proven;
  - a `FAIL` / `INSUFFICIENT` entry => the signal stays NOT proven;
  - a real PASS entry WITHOUT a `signal` key (the actual `verify_edge` writer shape today) => no KeyError,
    not surfaced as a proven signal (fail-safe);
  - forward-walk MONITORING records are excluded from the claim list (they re-score, they aren't claims);
  - `resolve_ledger_path()` honors the `TRENDORA_LEDGER_PATH` env override, else the config default
    resolved against the repo root.
"""
from __future__ import annotations

from pathlib import Path

from app.config import REPO_ROOT
from app.engine.evidence import (
    LEDGER_PATH_ENV,
    build_evidence_payload,
    resolve_ledger_path,
)
from app.engine.ledger import append_entry


def _pass_entry(signal: str | None) -> dict:
    """A certified (PASS) ledger entry. When `signal` is given it is stamped on the claim (the read-side
    convention iter-1 establishes); when None it mirrors the REAL `verify_edge` writer, which stamps no
    `signal` key on the cohort-selector claim."""
    claim = {
        "kind": "factor",
        "factor": "leadership_score",
        "slice_kind": "decile",
        "decile": 10,
        "horizon": 20,
        "direction": "positive",
    }
    if signal is not None:
        claim["signal"] = signal
    return {
        "claim": claim,
        "register_date": "2024-06-01",
        "horizon": 20,
        "cohort_n": 42,
        "control_n": 40,
        "verdict": {
            "status": "PASS",
            "reason": "certified out-of-sample",
            "holdout_edge": 0.031,
            "control_excess": 0.018,
            "p_value": 0.004,
        },
    }


def _verdict_entry(signal: str, status: str) -> dict:
    return {
        "claim": {"kind": "factor", "factor": signal, "signal": signal, "horizon": 20},
        "register_date": "2024-06-01",
        "horizon": 20,
        "cohort_n": 12,
        "control_n": 12,
        "verdict": {"status": status, "reason": f"{status} out-of-sample", "control_excess": -0.004},
    }


def test_build_payload_absent_ledger_is_empty(tmp_path):
    missing = tmp_path / "nope" / "certified-claims.jsonl"
    payload = build_evidence_payload(str(missing))
    assert payload == {"claims": [], "proven_signals": {}}


def test_build_payload_pass_entry_marks_signal_proven(tmp_path):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    payload = build_evidence_payload(str(ledger))

    assert list(payload["proven_signals"].keys()) == ["leadership_score"]
    proven = payload["proven_signals"]["leadership_score"]
    assert proven["proven"] is True
    assert proven["signal"] == "leadership_score"
    assert proven["register_date"] == "2024-06-01"
    assert proven["horizon"] == 20
    assert proven["cohort_n"] == 42
    assert proven["control_n"] == 40
    # verdict fields are re-displayed VERBATIM (no recompute)
    assert proven["verdict"]["status"] == "PASS"
    assert proven["verdict"]["control_excess"] == 0.018
    assert proven["verdict"]["holdout_edge"] == 0.031
    # forward-walk score-to-date is the layout placeholder (None until a certified iteration monitors it)
    assert proven["forward_walk"] is None
    # hypothesis = the cohort selectors, read verbatim
    assert proven["claim"]["factor"] == "leadership_score"
    assert proven["claim"]["decile"] == 10

    assert len(payload["claims"]) == 1
    assert payload["claims"][0] is not proven or payload["claims"][0] == proven


def test_build_payload_fail_and_insufficient_not_proven(tmp_path):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _verdict_entry("entry_quality_score", "FAIL"))
    append_entry(str(ledger), _verdict_entry("risk_score", "INSUFFICIENT"))
    payload = build_evidence_payload(str(ledger))

    # neither a FAIL nor an INSUFFICIENT verdict surfaces a proven signal (fail-safe)
    assert payload["proven_signals"] == {}
    # both rows are still audit-listed on the ledger page, honestly carrying their verdict + proven=False
    assert len(payload["claims"]) == 2
    statuses = {row["verdict"]["status"]: row["proven"] for row in payload["claims"]}
    assert statuses == {"FAIL": False, "INSUFFICIENT": False}


def test_build_payload_pass_without_signal_key_is_failsafe(tmp_path):
    # the REAL verify_edge writer stamps NO `signal` on the claim — a signal-less PASS must NOT KeyError
    # and must NOT light up any UI signal (it stays "Not yet proven" everywhere).
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry(None))
    payload = build_evidence_payload(str(ledger))

    assert payload["proven_signals"] == {}          # no signal named => nothing proven on the badge
    assert len(payload["claims"]) == 1
    row = payload["claims"][0]
    assert row["proven"] is True                     # the verdict IS a PASS (honestly shown on the ledger)
    assert row["signal"] is None                     # but it maps to NO UI signal key (defensive read)


def test_build_payload_excludes_forward_walk_monitoring_records(tmp_path):
    ledger = tmp_path / "certified-claims.jsonl"
    append_entry(str(ledger), _pass_entry("leadership_score"))
    append_entry(str(ledger), {"type": "forward_walk", "claim": {"signal": "leadership_score"},
                               "verdict": {"status": "PASS"}})
    payload = build_evidence_payload(str(ledger))

    # the monitoring re-score is NOT a new claim row (it re-scores an existing claim)
    assert len(payload["claims"]) == 1
    assert payload["claims"][0]["register_date"] == "2024-06-01"
    # the original certified claim still proves its signal
    assert list(payload["proven_signals"].keys()) == ["leadership_score"]


def test_resolve_ledger_path_env_override(tmp_path, monkeypatch):
    override = tmp_path / "override-ledger.jsonl"
    monkeypatch.setenv(LEDGER_PATH_ENV, str(override))
    assert resolve_ledger_path() == str(override)


def test_resolve_ledger_path_config_default(monkeypatch):
    monkeypatch.delenv(LEDGER_PATH_ENV, raising=False)
    resolved = resolve_ledger_path()
    # the SAME file the post-decompose gate writes, resolved absolute against the repo root
    assert resolved == str(REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl")
    assert Path(resolved).is_absolute()
