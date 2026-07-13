"""Negative-results graveyard composition tests (goal-mcp-loop iter-31, J-19 / backlog B-902).

`app.engine.graveyard` is a PURE read-compose module: it reads BOTH the canonical and staging
certified-claims ledgers via the existing `app.engine.ledger.read_entries`, filters to NON-PASS
verdicts, tags each with its origin ledger, and attaches registration lineage via the EXISTING
`app.engine.registry.match_registration` (never a second matcher). These tests pin:

  - `resolve_staging_ledger_path` honors the `STAGING_LEDGER_PATH` env override (the SAME literal name
    `run-goal.sh` / `verify_claim.py` already use), else the config default (mirrors
    `test_registry.py`'s `resolve_registry_path` tests exactly).
  - `build_graveyard_payload` over fixture ledgers: non-PASS filter (a PASS fixture entry is excluded),
    forward-walk exclusion, ledger-origin tag + `deflation`/`deflation_divisor` re-displayed verbatim,
    lineage attachment via a REAL `match_registration` call (a matched row + an honest `None` for an
    unregistered selector-set), a "closed" status surfaced verbatim on a matched row, and a missing/empty
    ledger file (or both) degrading to an empty payload — never a crash.
  - The REVISIT_PROTOCOL constant is served alongside the entries and carries no proven-language.
  - At least one REAL committed ledger line (`ma_stack`, the one permanently-closed hypothesis) round-trips
    end-to-end through the payload (anti-goal #3 proof — not just a synthetic fixture).
"""
from __future__ import annotations

from pathlib import Path

from app.config import REPO_ROOT
from app.engine.graveyard import (
    LEDGER_CANONICAL,
    LEDGER_STAGING,
    REVISIT_PROTOCOL,
    STAGING_LEDGER_PATH_ENV,
    build_graveyard_payload,
    resolve_staging_ledger_path,
)
from app.engine.ledger import append_entry, read_entries
from app.engine.registry import REGISTRY_PATH_ENV

_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"


# ==================================================================================================
# resolve_staging_ledger_path — env override (STAGING_LEDGER_PATH), else config default
# ==================================================================================================
def test_resolve_staging_ledger_path_env_override(tmp_path, monkeypatch):
    override = tmp_path / "override-staging.jsonl"
    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(override))
    assert resolve_staging_ledger_path() == str(override)


def test_resolve_staging_ledger_path_config_default(monkeypatch):
    monkeypatch.delenv(STAGING_LEDGER_PATH_ENV, raising=False)
    resolved = resolve_staging_ledger_path()
    assert resolved == str(REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl")
    assert Path(resolved).is_absolute()


def test_staging_ledger_path_env_name_matches_the_harness_literal():
    """The harness (run-goal.sh / verify_claim.py) already exports/reads `STAGING_LEDGER_PATH` — this
    module MUST honor the same literal name, never a new `TRENDORA_STAGING_LEDGER_PATH`."""
    assert STAGING_LEDGER_PATH_ENV == "STAGING_LEDGER_PATH"


# ==================================================================================================
# build_graveyard_payload — fixture ledgers: filter / exclusion / tagging / lineage / degrade-empty
# ==================================================================================================
_FIXTURE_REGISTRY = [
    {
        "id": "factor-vcp_contraction-d10-h60",
        "selectors": {
            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
            "horizon": 60, "direction": "positive",
        },
        "rationale": "fixture rationale", "registered_by": "backfill", "registered_date": "2026-07-03",
        "source": "fixture", "status": "tested",
    },
    {
        "id": "factor-ma_stack-d10-h20",
        "selectors": {
            "kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10,
            "horizon": 20, "direction": "positive",
        },
        "rationale": "fixture rationale (closed)", "registered_by": "backfill",
        "registered_date": "2026-07-03", "source": "fixture", "status": "closed",
    },
]


def _write_registry(tmp_path, monkeypatch, rows=_FIXTURE_REGISTRY):
    path = tmp_path / "registry.jsonl"
    for row in rows:
        append_entry(str(path), row)
    monkeypatch.setenv(REGISTRY_PATH_ENV, str(path))
    return path


def _fail_entry(factor: str, decile: int = 10, horizon: int = 60, **verdict_extra) -> dict:
    verdict = {
        "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 3,
        "holdout_edge": -0.01, "control_excess": -0.01, "p_value": 0.9,
    }
    verdict.update(verdict_extra)
    return {
        "claim": {
            "kind": "factor", "factor": factor, "slice_kind": "decile", "decile": decile,
            "horizon": horizon, "direction": "positive",
        },
        "cohort_n": 100, "control_n": 50, "horizon": horizon, "register_date": "2026-07-03",
        "verdict": verdict,
    }


def test_non_pass_filter_excludes_a_pass_entry(tmp_path, monkeypatch):
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("vcp_contraction"))
    pass_entry = _fail_entry("vcp_contraction", horizon=61)
    pass_entry["verdict"]["status"] = "PASS"
    append_entry(str(canonical), pass_entry)
    staging = tmp_path / "staging.jsonl"  # missing/empty is fine for this assertion
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["verdict"]["status"] == "FAIL"


def test_insufficient_entry_is_included_non_pass(tmp_path, monkeypatch):
    """INSUFFICIENT is a non-PASS verdict too -- the filter is `!= PASS`, not `== FAIL`."""
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    entry = _fail_entry("vcp_contraction")
    entry["verdict"]["status"] = "INSUFFICIENT"
    append_entry(str(canonical), entry)
    staging = tmp_path / "staging.jsonl"
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["verdict"]["status"] == "INSUFFICIENT"


def test_forward_walk_records_are_excluded(tmp_path, monkeypatch):
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("vcp_contraction"))
    forward_walk = _fail_entry("vcp_contraction", horizon=61)
    forward_walk["type"] = "forward_walk"
    append_entry(str(canonical), forward_walk)
    staging = tmp_path / "staging.jsonl"
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["horizon"] == 60  # the original entry, not the horizon=61 forward-walk


def test_ledger_origin_tag_and_deflation_fields_reexposed_verbatim(tmp_path, monkeypatch):
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("vcp_contraction", deflation="bonferroni", deflation_divisor=3))
    staging = tmp_path / "staging.jsonl"
    append_entry(str(staging), _fail_entry("vcp_contraction", horizon=10, deflation="lord++", deflation_divisor=1))
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    by_ledger = {e["ledger"]: e for e in payload["entries"]}
    assert by_ledger[LEDGER_CANONICAL]["verdict"]["deflation"] == "bonferroni"
    assert by_ledger[LEDGER_CANONICAL]["verdict"]["deflation_divisor"] == 3
    assert by_ledger[LEDGER_STAGING]["verdict"]["deflation"] == "lord++"
    assert by_ledger[LEDGER_STAGING]["verdict"]["deflation_divisor"] == 1


def test_lineage_attached_via_real_match_registration_for_a_matched_claim(tmp_path, monkeypatch):
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("vcp_contraction", decile=10, horizon=60))
    staging = tmp_path / "staging.jsonl"
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    entry = payload["entries"][0]
    assert entry["lineage"] is not None
    assert entry["lineage"]["id"] == "factor-vcp_contraction-d10-h60"


def test_lineage_is_honest_none_for_an_unregistered_selector_set(tmp_path, monkeypatch):
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("some_never_registered_factor", decile=7, horizon=5))
    staging = tmp_path / "staging.jsonl"
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    entry = payload["entries"][0]
    assert entry["lineage"] is None  # no crash, no fabricated link


def test_closed_status_surfaced_verbatim_on_a_matched_row(tmp_path, monkeypatch):
    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("ma_stack", decile=10, horizon=20))
    staging = tmp_path / "staging.jsonl"
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    entry = payload["entries"][0]
    assert entry["lineage"]["status"] == "closed"


def test_missing_ledger_files_degrade_to_empty_payload_no_crash(tmp_path, monkeypatch):
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
    payload = build_graveyard_payload(
        canonical_path=str(tmp_path / "nope-canonical.jsonl"),
        staging_path=str(tmp_path / "nope-staging.jsonl"),
    )
    assert payload["entries"] == []
    assert payload["revisit_protocol"] == REVISIT_PROTOCOL


def test_empty_ledger_files_degrade_to_empty_payload_no_crash(tmp_path, monkeypatch):
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
    canonical = tmp_path / "canonical.jsonl"
    canonical.write_text("", encoding="utf-8")
    staging = tmp_path / "staging.jsonl"
    staging.write_text("", encoding="utf-8")
    payload = build_graveyard_payload(canonical_path=str(canonical), staging_path=str(staging))
    assert payload["entries"] == []


def test_build_graveyard_payload_defaults_to_the_resolvers(tmp_path, monkeypatch):
    """With BOTH path args omitted, resolution goes through `evidence.resolve_ledger_path()` (canonical)
    and `resolve_staging_ledger_path()` (staging) -- the endpoint's real, no-argument call shape."""
    from app.engine import evidence as evidence_mod

    _write_registry(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _fail_entry("vcp_contraction"))
    monkeypatch.setenv(evidence_mod.LEDGER_PATH_ENV, str(canonical))
    staging = tmp_path / "staging.jsonl"
    append_entry(str(staging), _fail_entry("vcp_contraction", horizon=10))
    monkeypatch.setenv(STAGING_LEDGER_PATH_ENV, str(staging))
    payload = build_graveyard_payload()
    assert len(payload["entries"]) == 2
    assert {e["ledger"] for e in payload["entries"]} == {LEDGER_CANONICAL, LEDGER_STAGING}


# ==================================================================================================
# REVISIT_PROTOCOL — a single served constant, no proven-language
# ==================================================================================================
def test_revisit_protocol_has_no_proven_language():
    banned = {"proven", "pass", "confirmed", "verified", "certified"}
    rule_text = REVISIT_PROTOCOL.get("rule", "").lower()
    for word in banned:
        assert word not in rule_text, f"revisit-protocol rule text leaked proven-language: {word!r}"


def test_revisit_protocol_states_final_and_materially_changed_precondition():
    rule_text = REVISIT_PROTOCOL.get("rule", "")
    assert "final" in rule_text.lower()
    assert "materially changed" in rule_text.lower()
    assert "NEW candidate" in rule_text or "new candidate" in rule_text.lower()


# ==================================================================================================
# Real-data round-trip (anti-goal #3 proof) — the committed ma_stack FAIL, end-to-end through payload
# ==================================================================================================
def test_real_ma_stack_entry_round_trips_end_to_end():
    """The one PERMANENTLY closed hypothesis (registry status "closed"): its real ledger line must
    appear in the real graveyard with byte-matching selectors/verdict AND its "closed" lineage."""
    assert _CANONICAL_LEDGER.exists()
    raw_entries = read_entries(str(_CANONICAL_LEDGER))
    ma_stack_raw = next(e for e in raw_entries if e["claim"].get("factor") == "ma_stack")

    payload = build_graveyard_payload()
    ma_stack_rows = [
        e for e in payload["entries"]
        if e["ledger"] == LEDGER_CANONICAL and e["claim"].get("factor") == "ma_stack"
    ]
    assert len(ma_stack_rows) == 1
    row = ma_stack_rows[0]
    assert row["claim"] == ma_stack_raw["claim"]
    assert row["verdict"] == ma_stack_raw["verdict"]
    assert row["register_date"] == ma_stack_raw["register_date"]
    assert row["verdict"]["status"] != "PASS"
    assert row["lineage"] is not None
    assert row["lineage"]["status"] == "closed"


def test_real_graveyard_has_fourteen_entries_today_all_non_pass():
    """Today BOTH real ledgers are 7/7 FAIL (goal.md's Evidence-frontier plateau note) -- every raw entry
    is non-PASS, so the graveyard shows all 14. This is a STATUS-DERIVED assertion (computed from the raw
    files), not a hardcoded expectation of the filter's behavior (a future PASS row would shrink this)."""
    canonical_raw = [e for e in read_entries(str(_CANONICAL_LEDGER)) if e.get("type") != "forward_walk"]
    staging_raw = [e for e in read_entries(str(_STAGING_LEDGER)) if e.get("type") != "forward_walk"]
    expected_non_pass = sum(1 for e in canonical_raw + staging_raw if e["verdict"]["status"] != "PASS")

    payload = build_graveyard_payload()
    assert len(payload["entries"]) == expected_non_pass
    assert all(e["verdict"]["status"] != "PASS" for e in payload["entries"])


def test_real_graveyard_entries_carry_no_proven_language_in_verdict_status():
    payload = build_graveyard_payload()
    for entry in payload["entries"]:
        assert entry["verdict"]["status"] in ("FAIL", "INSUFFICIENT")
