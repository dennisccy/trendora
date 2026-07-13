"""Post-decompose gate — pre-registration cross-check tests (goal-mcp-loop iter-30, J-18 / backlog B-901).

Loads `project-extensions/gates/verify_claim.py` via `importlib.util.spec_from_file_location`, exactly as
`test_staging_ledger_routing.py::_load_gate` already does. `tools.verify_edge` is monkeypatched to a spy
stub (never touches the DB) so these tests need NO seeded DB / warm-up — they pin the GATE's pre-check
DECISION only (call vs no-call), which is the load-bearing B-901 contract:

  (a) a claim whose EXACT selectors match a registry row, with enforcement ON -> the gate proceeds to
      `verify_edge` (the referee IS reached);
  (b) an UNREGISTERED claim, enforcement ON -> refused BEFORE `verify_edge` runs (never called), the
      target ledger file is left byte-identical (no write), and the BLOCKED reason names the registry;
  (c) a NEAR-MISS claim (one differing selector — decile 10 -> 9), enforcement ON -> refused the same way
      as (b), proving the match is EXACT, never fuzzy;
  (d) enforcement OFF -> an unregistered claim still reaches `verify_edge` (byte-identical to the
      pre-iter-30 gate behavior) — the regression guard for every iteration that predates its own
      registry row being backfilled.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from sqlmodel import create_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GATE_PATH = _REPO_ROOT / "project-extensions" / "gates" / "verify_claim.py"

_REGISTERED_CLAIM = {
    "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
    "horizon": 60, "direction": "positive",
}
_UNREGISTERED_CLAIM = {
    "kind": "factor", "factor": "hv", "slice_kind": "decile", "decile": 10,
    "horizon": 20, "direction": "positive",
}
# A NEAR-MISS of _REGISTERED_CLAIM: one selector differs (decile 10 -> 9).
_NEAR_MISS_CLAIM = {**_REGISTERED_CLAIM, "decile": 9}

_FIXTURE_REGISTRY_ROW = {
    "id": "factor-vcp_contraction-d10-h60",
    "selectors": _REGISTERED_CLAIM,
    "rationale": "fixture", "registered_by": "backfill", "registered_date": "2026-07-03",
    "source": "fixture", "status": "tested",
}


def _load_gate():
    """Mirrors test_staging_ledger_routing.py::_load_gate exactly."""
    spec = importlib.util.spec_from_file_location("verify_claim_gate_registry_test", _GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_spec(tmp_path: Path, claim: dict) -> Path:
    spec_path = tmp_path / "iter-spec.md"
    spec_path.write_text(
        "# Fixture iteration spec\n\n## Evidence Claim\n```json\n" + json.dumps(claim) + "\n```\n",
        encoding="utf-8",
    )
    return spec_path


def _spy_verify_edge(calls):
    def _fake(session, claim, ledger_path, *, register_date, ledger):
        calls.append({"claim": claim, "ledger_path": ledger_path, "ledger": ledger})
        return {"verdict": {"status": "PASS", "reason": "stub"}}
    return _fake


def _wire_gate(gate, monkeypatch, *, enforce: bool, registry_path: Path):
    """Shared fixture wiring: a harmless in-memory engine (verify_edge is stubbed, so the session is never
    queried), a fresh config with `evidence.registry.enforce` set explicitly, and the registry pointed at
    an isolated fixture file — never the real committed one."""
    from app.config import load_config

    monkeypatch.setattr(gate, "get_engine", lambda: create_engine("sqlite://"))
    cfg = load_config()  # a FRESH load (not the process cache) so mutating it is test-local
    cfg.evidence.registry.enforce = enforce
    monkeypatch.setattr(gate, "get_config", lambda: cfg)
    monkeypatch.setenv(gate.registry_mod.REGISTRY_PATH_ENV, str(registry_path))


def _seed_registry(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


# ==================================================================================================
# (a) registered exact-match claim, enforcement ON -> proceeds to verify_edge
# ==================================================================================================
def test_registered_claim_reaches_verify_edge_when_enforced(tmp_path, monkeypatch):
    gate = _load_gate()
    registry_path = tmp_path / "pre-registrations.jsonl"
    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])
    _wire_gate(gate, monkeypatch, enforce=True, registry_path=registry_path)

    calls: list[dict] = []
    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))

    spec_path = _write_spec(tmp_path, _REGISTERED_CLAIM)
    monkeypatch.setenv("SPEC_PATH", str(spec_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)

    rc = gate.main()

    assert len(calls) == 1  # the referee WAS reached
    assert calls[0]["claim"] == _REGISTERED_CLAIM
    assert rc == 0  # the stub returns PASS -> the iteration is not blocked


# ==================================================================================================
# (b) unregistered claim, enforcement ON -> refused BEFORE verify_edge; ledger left untouched
# ==================================================================================================
def test_unregistered_claim_is_refused_before_verify_edge(tmp_path, monkeypatch):
    gate = _load_gate()
    registry_path = tmp_path / "pre-registrations.jsonl"
    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])  # does NOT cover _UNREGISTERED_CLAIM
    _wire_gate(gate, monkeypatch, enforce=True, registry_path=registry_path)

    calls: list[dict] = []
    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))

    spec_path = _write_spec(tmp_path, _UNREGISTERED_CLAIM)
    staging_ledger = tmp_path / "staging-ledger.jsonl"
    staging_ledger.write_text("", encoding="utf-8")  # pre-existing (empty) — must stay byte-identical
    before = staging_ledger.read_bytes()

    monkeypatch.setenv("SPEC_PATH", str(spec_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(staging_ledger))
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
    verdict_path = tmp_path / "gate-verdict.json"
    monkeypatch.setenv("GATE_VERDICT_PATH", str(verdict_path))

    rc = gate.main()

    assert calls == []  # verify_edge was NEVER called
    assert staging_ledger.read_bytes() == before  # the target ledger is untouched (no write)
    assert rc == 3  # BLOCKED
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    assert verdict["blocked"] is True
    assert verdict["results"][0]["status"] == "BLOCKED"
    # the message names the registry requirement (loud + actionable, not a bare "no").
    reason = verdict["results"][0]["reason"]
    assert "registry" in reason.lower() and "register" in reason.lower()


# ==================================================================================================
# (c) near-miss claim (one differing selector), enforcement ON -> refused the same way (EXACT match)
# ==================================================================================================
def test_near_miss_claim_is_refused_proving_exact_match(tmp_path, monkeypatch):
    gate = _load_gate()
    registry_path = tmp_path / "pre-registrations.jsonl"
    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])
    _wire_gate(gate, monkeypatch, enforce=True, registry_path=registry_path)

    calls: list[dict] = []
    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))

    # sanity: the near-miss really does differ from the registered row by exactly one selector.
    assert _NEAR_MISS_CLAIM != _REGISTERED_CLAIM
    assert _NEAR_MISS_CLAIM["decile"] == 9 and _REGISTERED_CLAIM["decile"] == 10

    spec_path = _write_spec(tmp_path, _NEAR_MISS_CLAIM)
    monkeypatch.setenv("SPEC_PATH", str(spec_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)

    rc = gate.main()

    assert calls == []  # the near-miss never reaches the referee
    assert rc == 3
    assert not (tmp_path / "staging-ledger.jsonl").exists()  # no ledger ever created


# ==================================================================================================
# (d) enforcement OFF -> an unregistered claim still proceeds (byte-identical pre-iter-30 behavior)
# ==================================================================================================
def test_enforcement_off_unregistered_claim_still_proceeds(tmp_path, monkeypatch):
    gate = _load_gate()
    registry_path = tmp_path / "pre-registrations.jsonl"
    _seed_registry(registry_path, [_FIXTURE_REGISTRY_ROW])  # present but irrelevant -- enforcement is off
    _wire_gate(gate, monkeypatch, enforce=False, registry_path=registry_path)

    calls: list[dict] = []
    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))

    spec_path = _write_spec(tmp_path, _UNREGISTERED_CLAIM)
    monkeypatch.setenv("SPEC_PATH", str(spec_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)

    rc = gate.main()

    assert len(calls) == 1  # the pre-iter-30 behavior: no registry gate, straight to the referee
    assert calls[0]["claim"] == _UNREGISTERED_CLAIM
    assert rc == 0


# ==================================================================================================
# missing registry file, enforcement ON -> every claim refused (an absent registry registers nothing)
# ==================================================================================================
def test_missing_registry_file_enforced_refuses_every_claim(tmp_path, monkeypatch):
    gate = _load_gate()
    missing_registry = tmp_path / "does-not-exist" / "pre-registrations.jsonl"
    _wire_gate(gate, monkeypatch, enforce=True, registry_path=missing_registry)

    calls: list[dict] = []
    monkeypatch.setattr(gate.tools, "verify_edge", _spy_verify_edge(calls))

    spec_path = _write_spec(tmp_path, _REGISTERED_CLAIM)  # would have matched, HAD the file existed
    monkeypatch.setenv("SPEC_PATH", str(spec_path))
    monkeypatch.setenv("STAGING_LEDGER_PATH", str(tmp_path / "staging-ledger.jsonl"))
    monkeypatch.setenv("LEDGER_PATH", str(tmp_path / "certified-claims.jsonl"))
    monkeypatch.delenv("GATE_VERDICT_PATH", raising=False)

    rc = gate.main()

    assert calls == []
    assert rc == 3  # fail-closed, never a silent pass-through on a missing registry
