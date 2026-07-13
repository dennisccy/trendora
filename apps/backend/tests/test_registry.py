"""Pre-registration registry loader tests (goal-mcp-loop iter-30, J-18 / backlog B-901).

`app.engine.registry` is the SINGLE pure loader both `GET /api/research/registry` and the post-decompose
gate (`verify_claim.py`) read through. These tests pin:

  - `resolve_registry_path` honors the `TRENDORA_REGISTRY_PATH` env override, else the config default
    (mirrors `test_evidence.py`'s `resolve_ledger_path` tests exactly);
  - `load_registrations` is honest about a missing/empty file (`[]`, never a crash) and reads real rows
    in append order;
  - `claim_selectors` builds the EXACT selector-set shape (`kind` + present cohort keys + `horizon` +
    `direction`, excluding display-routing keys like `signal`/`ledger`);
  - `match_registration` is EXACT-equality only: a real match returns the row, a near-miss (one differing
    selector — proves matching is exact, never fuzzy) and a fully unregistered claim both return `None`;
  - the COMMITTED backfill (`state/pre-registrations.jsonl`) is complete: 11 distinct rows (the union of
    both ledgers' 14 raw entries, deduplicated by exact selector-set — 3 pairs are identical selector-sets
    promoted staging->canonical, see the iter-30 dev handoff), append-only, every row's stated
    `registered_date` is the ledgers' own 2026-07-03 register date (never a fabricated "today"), and every
    row in BOTH real ledgers round-trips through `match_registration` back to a backfilled row.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import REPO_ROOT
from app.engine.ledger import append_entry, read_entries
from app.engine.registry import (
    REGISTRY_PATH_ENV,
    claim_selectors,
    load_registrations,
    match_registration,
    resolve_registry_path,
)

_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
_COMMITTED_REGISTRY = REPO_ROOT / "runs/goal-session-mcp-loop/state/pre-registrations.jsonl"


# ==================================================================================================
# resolve_registry_path — env override, else config default (mirrors test_evidence.py verbatim)
# ==================================================================================================
def test_resolve_registry_path_env_override(tmp_path, monkeypatch):
    override = tmp_path / "override-registry.jsonl"
    monkeypatch.setenv(REGISTRY_PATH_ENV, str(override))
    assert resolve_registry_path() == str(override)


def test_resolve_registry_path_config_default(monkeypatch):
    monkeypatch.delenv(REGISTRY_PATH_ENV, raising=False)
    resolved = resolve_registry_path()
    # the SAME file the post-decompose gate cross-checks against, resolved absolute against the repo root
    assert resolved == str(REPO_ROOT / "runs/goal-session-mcp-loop/state/pre-registrations.jsonl")
    assert Path(resolved).is_absolute()


# ==================================================================================================
# load_registrations — honest empty on missing/absent file, real rows in append order otherwise
# ==================================================================================================
def test_load_registrations_missing_file_is_empty(tmp_path):
    assert load_registrations(str(tmp_path / "nope.jsonl")) == []


def test_load_registrations_empty_file_is_empty(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    assert load_registrations(str(path)) == []


def test_load_registrations_reads_rows_in_append_order(tmp_path):
    path = str(tmp_path / "registry.jsonl")
    append_entry(path, {"id": "a", "selectors": {"kind": "factor"}})
    append_entry(path, {"id": "b", "selectors": {"kind": "event-study"}})
    rows = load_registrations(path)
    assert [r["id"] for r in rows] == ["a", "b"]


def test_load_registrations_defaults_to_resolve_registry_path(tmp_path, monkeypatch):
    override = tmp_path / "env-registry.jsonl"
    append_entry(str(override), {"id": "z", "selectors": {"kind": "factor"}})
    monkeypatch.setenv(REGISTRY_PATH_ENV, str(override))
    # no explicit path -> resolves via resolve_registry_path() (the endpoint's own call shape)
    assert [r["id"] for r in load_registrations()] == ["z"]


# ==================================================================================================
# claim_selectors — the EXACT selector-set shape (kind + present cohort keys + horizon + direction)
# ==================================================================================================
def test_claim_selectors_factor_cohort_shape():
    claim = {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive", "ledger": "canonical",
    }
    # `ledger` is a display-ROUTING key, not part of the hypothesis identity -- excluded.
    assert claim_selectors(claim) == {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive",
    }


def test_claim_selectors_excludes_signal_key():
    claim = {
        "kind": "factor", "factor": "leadership_score", "slice_kind": "decile", "decile": 10,
        "horizon": 20, "direction": "positive", "signal": "leadership_score",
    }
    selectors = claim_selectors(claim)
    assert "signal" not in selectors
    assert selectors["factor"] == "leadership_score"


def test_claim_selectors_combination_cohort_shape():
    claim = {
        "kind": "combination", "cohort": "composite",
        "condition": ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"],
        "horizon": 20, "direction": "positive",
    }
    assert claim_selectors(claim) == claim  # every key here IS a selector key -- nothing dropped


def test_claim_selectors_defaults_direction_positive_when_absent():
    claim = {"kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10, "horizon": 20}
    assert claim_selectors(claim)["direction"] == "positive"


def test_claim_selectors_omits_horizon_when_claim_omits_it():
    claim = {"kind": "factor", "factor": "ma_stack", "slice_kind": "decile", "decile": 10}
    assert "horizon" not in claim_selectors(claim)


# ==================================================================================================
# match_registration — EXACT equality only: real match / near-miss (one differing selector) / no match
# ==================================================================================================
_FIXTURE_REGISTRATIONS = [
    {
        "id": "factor-vcp_contraction-d10-h60",
        "selectors": {
            "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
            "horizon": 60, "direction": "positive",
        },
        "rationale": "fixture", "registered_by": "backfill", "registered_date": "2026-07-03",
        "source": "fixture", "status": "tested",
    },
]


def test_match_registration_exact_match_returns_the_row():
    claim = {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive", "ledger": "canonical",  # a routing key, irrelevant to match
    }
    matched = match_registration(claim, registrations=_FIXTURE_REGISTRATIONS)
    assert matched is not None
    assert matched["id"] == "factor-vcp_contraction-d10-h60"


def test_match_registration_near_miss_decile_returns_none():
    """A single differing selector (decile 10 -> 9) is a near-miss -- refused, proving EXACT matching,
    never fuzzy/superset."""
    claim = {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 9,
        "horizon": 60, "direction": "positive",
    }
    assert match_registration(claim, registrations=_FIXTURE_REGISTRATIONS) is None


def test_match_registration_near_miss_horizon_returns_none():
    """A single differing selector (horizon 60 -> 61) is a near-miss -- refused."""
    claim = {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 61, "direction": "positive",
    }
    assert match_registration(claim, registrations=_FIXTURE_REGISTRATIONS) is None


def test_match_registration_wholly_unregistered_claim_returns_none():
    claim = {"kind": "factor", "factor": "hv", "slice_kind": "decile", "decile": 10, "horizon": 20}
    assert match_registration(claim, registrations=_FIXTURE_REGISTRATIONS) is None


def test_match_registration_empty_registry_returns_none():
    claim = {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive",
    }
    assert match_registration(claim, registrations=[]) is None


def test_match_registration_combination_leg_order_is_part_of_the_exact_match():
    """`condition` list ORDER is part of the exact match (a known, accepted sharp edge -- normalizing it
    would itself be a step toward fuzzy matching, B-901's named dominant trap)."""
    registrations = [{
        "id": "combination-x", "selectors": {
            "kind": "combination", "cohort": "composite",
            "condition": ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"],
            "horizon": 20, "direction": "positive",
        },
        "rationale": "fixture", "registered_by": "backfill", "registered_date": "2026-07-03",
        "source": "fixture", "status": "tested",
    }]
    reordered = {
        "kind": "combination", "cohort": "composite",
        "condition": ["atr_pct:bottom:tertile", "rs_spy_3m:top:quintile"],  # legs swapped
        "horizon": 20, "direction": "positive",
    }
    assert match_registration(reordered, registrations=registrations) is None


def test_match_registration_defaults_to_load_registrations(tmp_path, monkeypatch):
    """With `registrations` omitted, `match_registration` reads via `load_registrations()` (the gate's
    real one-argument call shape)."""
    path = tmp_path / "registry.jsonl"
    append_entry(str(path), _FIXTURE_REGISTRATIONS[0])
    monkeypatch.setenv(REGISTRY_PATH_ENV, str(path))
    claim = {
        "kind": "factor", "factor": "vcp_contraction", "slice_kind": "decile", "decile": 10,
        "horizon": 60, "direction": "positive",
    }
    matched = match_registration(claim)
    assert matched is not None and matched["id"] == "factor-vcp_contraction-d10-h60"


# ==================================================================================================
# The COMMITTED backfill (state/pre-registrations.jsonl) — completeness + no-deletion + round-trip
# ==================================================================================================
def test_committed_registry_backfill_is_complete_and_deduplicated():
    """The DoD anchor: the committed registry is the UNION of proposer-guidance.md §4.1 (4) + §4.2 (3)
    candidates and every distinct claim selector-set in BOTH ledgers (7 canonical + 7 staging = 14 raw
    entries), deduplicated by EXACT selector-set — 3 pairs are identical selector-sets (a staging
    candidate later promoted/re-tested under "ledger":"canonical" with the identical cohort selectors:
    vcp_contraction d10 h60; rs_spy_3m d10 h60; the rs_spy_3m x high_proximity h20 combination). Since
    `match_registration` returns ONE row for an exact selector-set, the registry cannot hold two rows
    sharing an identical selector tuple -- 14 raw entries dedup to 11 distinct rows (see the iter-30 dev
    handoff for the full reasoning; the spec's literal "≥14" undercounts the cross-ledger overlap)."""
    assert _COMMITTED_REGISTRY.exists(), f"missing committed registry at {_COMMITTED_REGISTRY}"
    rows = load_registrations(str(_COMMITTED_REGISTRY))
    assert len(rows) == 11
    # append-only: every row is a well-formed registration (no partial/malformed row).
    required_fields = {"id", "selectors", "rationale", "registered_by", "registered_date", "source", "status"}
    for row in rows:
        assert required_fields.issubset(row.keys()), f"row missing fields: {row}"
        assert row["registered_by"] == "backfill"
        assert row["registered_date"] == "2026-07-03"  # the ledgers' own register_date, never today
        assert row["status"] in ("tested", "closed")  # descriptive process vocabulary, NEVER proven-language
    # ids are unique (stable, collision-free rows).
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == len(ids)
    # selector-sets are unique (the dedup requirement itself -- match_registration must resolve to ONE row).
    # (a `condition` value is a list -- unhashable -- so compare via a canonical JSON string, not a tuple.)
    selector_keys = [json.dumps(r["selectors"], sort_keys=True) for r in rows]
    assert len(set(selector_keys)) == len(selector_keys)
    # the one PERMANENTLY closed hypothesis (J-19's forward acceptance text: "the ma_stack closed FAIL").
    ma_stack_rows = [r for r in rows if r["selectors"].get("factor") == "ma_stack"]
    assert len(ma_stack_rows) == 1 and ma_stack_rows[0]["status"] == "closed"


def test_committed_registry_round_trips_every_canonical_ledger_claim():
    """Every claim in the LIVE canonical ledger matches a backfilled registry row -- the backfill's
    completeness proven against real data, not just a hand-count."""
    assert _CANONICAL_LEDGER.exists()
    rows = load_registrations(str(_COMMITTED_REGISTRY))
    for entry in read_entries(str(_CANONICAL_LEDGER)):
        matched = match_registration(entry["claim"], registrations=rows)
        assert matched is not None, f"canonical claim has NO registry match: {entry['claim']}"


def test_committed_registry_round_trips_every_staging_ledger_claim():
    """Every claim in the LIVE staging ledger matches a backfilled registry row too (both ledgers feed
    the same registry -- a hypothesis tested under either economy is still a registered hypothesis)."""
    assert _STAGING_LEDGER.exists()
    rows = load_registrations(str(_COMMITTED_REGISTRY))
    for entry in read_entries(str(_STAGING_LEDGER)):
        matched = match_registration(entry["claim"], registrations=rows)
        assert matched is not None, f"staging claim has NO registry match: {entry['claim']}"


def test_committed_registry_has_no_proven_language():
    """Anti-goal #1: the registry's `status` vocabulary is descriptive process state, never a proven/
    not-proven signal -- a "tested" row may have FAILED out-of-sample (every row here did)."""
    rows = load_registrations(str(_COMMITTED_REGISTRY))
    banned = {"proven", "pass", "confirmed", "verified", "certified"}
    for row in rows:
        assert row["status"].lower() not in banned
