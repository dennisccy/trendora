"""Certification-budget accounting composition tests (goal-mcp-loop iter-32, J-17 / backlog B-903).

`app.engine.budget_accounting` is a PURE read-compose module: it re-reads the SAME `ledger` /
`online_fdr` / `referee` seams `app.mcp.tools.verify_edge` uses -- it computes NO canonical value
independently (B-903's named failure mode is "UI-recompute"). These tests pin:

  - Single-source: the payload's canonical trials / `required_p` / budget-remaining, and the staging
    next-trial level, equal values independently derived by calling those SAME seams directly against
    the live ledgers (proves no parallel bookkeeping).
  - Fixture-spend: appending fixture claims to a THROWAWAY `tmp_path` ledger moves the figures exactly
    as hand-computed (trials n -> n+1; `required_p = 0.05/(n+1)`; a stable fixture charges
    `alpha_charged=0` vs an overfit one charging the per-claim cost; the staging level recomputes per
    LORD++). The REAL `certified-claims.jsonl` / `staging-ledger.jsonl` are never written by these tests.
  - Resilience: missing/empty ledger -> the honest empty-ledger snapshot (0 trials, `required_p =
    0.05/1`, the full starting budget, the staging economy's initial wealth); an all-FAIL ledger
    depletes the staging next-trial level with no replenishment; spend-over-time series length ==
    `count_trials` for that ledger; forward-walk monitoring records are excluded from both.
"""
from __future__ import annotations

from app.config import REPO_ROOT, get_config
from app.engine import online_fdr
from app.engine.budget_accounting import build_budget_payload
from app.engine.evidence import resolve_ledger_path
from app.engine.graveyard import resolve_staging_ledger_path
from app.engine.ledger import alpha_spent, append_entry, count_trials, rejection_offsets
from app.engine.referee import DEFAULT_ALPHA_BUDGET, DEFAULT_ALPHA_PER_TEST

_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"


def _entry(factor: str, *, horizon: int = 20, **verdict_extra) -> dict:
    verdict = {
        "status": "FAIL", "reason": "fixture", "deflation": "bonferroni", "deflation_divisor": 1,
        "required_p": 0.05, "alpha_charged": 0.0, "holdout_edge": -0.01, "p_value": 0.9,
    }
    verdict.update(verdict_extra)
    return {
        "claim": {
            "kind": "factor", "factor": factor, "slice_kind": "decile", "decile": 10,
            "horizon": horizon, "direction": "positive",
        },
        "cohort_n": 100, "control_n": 50, "horizon": horizon, "register_date": "2026-07-14",
        "verdict": verdict,
    }


# ==================================================================================================
# Single-source: payload figures equal values independently derived via the SAME seams verify_edge uses
# ==================================================================================================
def test_canonical_single_source_against_live_ledger():
    payload = build_budget_payload()
    canonical = payload["canonical"]
    resolved = resolve_ledger_path()
    expected_trials = count_trials(resolved)
    expected_spent = alpha_spent(resolved)
    assert canonical["n_trials_to_date"] == expected_trials
    assert canonical["n_trials_next"] == expected_trials + 1
    assert canonical["required_p"] == DEFAULT_ALPHA_PER_TEST / (expected_trials + 1)
    assert canonical["alpha_spent"] == expected_spent
    assert canonical["alpha_budget_remaining"] == DEFAULT_ALPHA_BUDGET - expected_spent


def test_staging_single_source_against_live_ledger():
    payload = build_budget_payload()
    staging = payload["staging"]
    resolved = resolve_staging_ledger_path()
    expected_trials = count_trials(resolved)
    fdr_cfg = get_config().evidence.fdr
    expected_level = online_fdr.test_level(
        expected_trials + 1,
        rejection_offsets(resolved),
        alpha=fdr_cfg.alpha,
        w0_fraction=fdr_cfg.w0_fraction,
        gamma_exponent=fdr_cfg.gamma_exponent,
        gamma_terms=fdr_cfg.gamma_terms,
    )
    assert staging["n_trials_to_date"] == expected_trials
    assert staging["n_trials_next"] == expected_trials + 1
    assert staging["next_level"] == expected_level


def test_canonical_required_p_uses_the_imported_referee_constant_not_a_literal():
    """`DEFAULT_ALPHA_PER_TEST` must be `app.engine.referee`'s own constant (0.05 today) -- the module
    imports it rather than hard-coding "0.05" anywhere (anti-goal: No magic numbers)."""
    assert DEFAULT_ALPHA_PER_TEST == 0.05
    assert DEFAULT_ALPHA_BUDGET == 1.0


def test_real_ledgers_today_seven_trials_each_status_derived():
    """Grounds the single-source tests in the documented plateau state (goal.md's Evidence-frontier
    plateau note) -- status-derived from the real files, not a bare hardcoded assumption."""
    payload = build_budget_payload()
    assert payload["canonical"]["n_trials_to_date"] == count_trials(str(_CANONICAL_LEDGER))
    assert payload["staging"]["n_trials_to_date"] == count_trials(str(_STAGING_LEDGER))


def test_real_ledger_spend_over_time_all_fail_today_matches_plateau_note():
    """goal.md's Evidence-frontier plateau note: 7/7 canonical + 7/7 staging verdicts FAIL today."""
    payload = build_budget_payload()
    assert len(payload["canonical"]["spend_over_time"]) == 7
    assert all(p["status"] == "FAIL" for p in payload["canonical"]["spend_over_time"])
    assert len(payload["staging"]["spend_over_time"]) == 7
    assert all(p["status"] == "FAIL" for p in payload["staging"]["spend_over_time"])


# ==================================================================================================
# Fixture-spend: a THROWAWAY tmp_path ledger, hand-computed figures, real ledgers never written
# ==================================================================================================
def test_fixture_spend_canonical_trial_count_and_required_p_move_exactly(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    missing_staging = str(tmp_path / "nope-staging.jsonl")
    for i in range(3):
        append_entry(str(canonical), _entry(f"f{i}", horizon=20 + i))
    before = build_budget_payload(canonical_path=str(canonical), staging_path=missing_staging)
    assert before["canonical"]["n_trials_to_date"] == 3
    assert before["canonical"]["n_trials_next"] == 4
    assert before["canonical"]["required_p"] == DEFAULT_ALPHA_PER_TEST / 4

    append_entry(str(canonical), _entry("f3", horizon=99))
    after = build_budget_payload(canonical_path=str(canonical), staging_path=missing_staging)
    assert after["canonical"]["n_trials_to_date"] == 4
    assert after["canonical"]["n_trials_next"] == 5
    assert after["canonical"]["required_p"] == DEFAULT_ALPHA_PER_TEST / 5


def test_fixture_spend_stable_vs_overfit_alpha_charged(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _entry("stable", alpha_charged=0.0))
    append_entry(str(canonical), _entry("overfit", alpha_charged=0.05))
    payload = build_budget_payload(
        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
    )
    assert payload["canonical"]["alpha_spent"] == 0.05
    assert payload["canonical"]["alpha_budget_remaining"] == DEFAULT_ALPHA_BUDGET - 0.05
    charges = [p["alpha_charged"] for p in payload["canonical"]["spend_over_time"]]
    assert charges == [0.0, 0.05]


def test_fixture_spend_staging_level_recomputes_per_lord_plusplus(tmp_path):
    staging = tmp_path / "staging.jsonl"
    fdr_cfg = get_config().evidence.fdr
    for i in range(2):
        append_entry(str(staging), _entry(f"s{i}", horizon=20 + i, deflation="lord++"))
    payload = build_budget_payload(
        canonical_path=str(tmp_path / "nope-canonical.jsonl"), staging_path=str(staging),
    )
    expected = online_fdr.test_level(
        3, [], alpha=fdr_cfg.alpha, w0_fraction=fdr_cfg.w0_fraction,
        gamma_exponent=fdr_cfg.gamma_exponent, gamma_terms=fdr_cfg.gamma_terms,
    )
    assert payload["staging"]["next_level"] == expected
    assert payload["staging"]["n_trials_next"] == 3


def test_fixture_spend_series_carries_required_p_and_deflation_divisor_verbatim(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _entry("f0", required_p=0.05, deflation_divisor=1))
    append_entry(str(canonical), _entry("f1", required_p=0.025, deflation_divisor=2))
    payload = build_budget_payload(
        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
    )
    points = payload["canonical"]["spend_over_time"]
    assert [p["required_p"] for p in points] == [0.05, 0.025]
    assert [p["deflation_divisor"] for p in points] == [1, 2]
    assert [p["trial"] for p in points] == [1, 2]


def test_fixture_spend_never_writes_the_real_ledgers(tmp_path):
    canonical_before = _CANONICAL_LEDGER.read_text(encoding="utf-8")
    staging_before = _STAGING_LEDGER.read_text(encoding="utf-8")
    # Exercise the module against a throwaway ledger only.
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _entry("f0"))
    build_budget_payload(canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"))
    # And against the real files, read-only -- still no mutation.
    build_budget_payload(canonical_path=str(_CANONICAL_LEDGER), staging_path=str(_STAGING_LEDGER))
    assert _CANONICAL_LEDGER.read_text(encoding="utf-8") == canonical_before
    assert _STAGING_LEDGER.read_text(encoding="utf-8") == staging_before


# ==================================================================================================
# Resilience: missing/empty ledger -> honest snapshot; all-FAIL -> no replenishment; series length
# ==================================================================================================
def test_missing_ledgers_degrade_to_honest_empty_snapshot_no_crash(tmp_path):
    payload = build_budget_payload(
        canonical_path=str(tmp_path / "nope-canonical.jsonl"),
        staging_path=str(tmp_path / "nope-staging.jsonl"),
    )
    canonical = payload["canonical"]
    assert canonical["n_trials_to_date"] == 0
    assert canonical["n_trials_next"] == 1
    assert canonical["required_p"] == DEFAULT_ALPHA_PER_TEST / 1
    assert canonical["alpha_budget_remaining"] == DEFAULT_ALPHA_BUDGET
    assert canonical["spend_over_time"] == []
    staging = payload["staging"]
    assert staging["n_trials_to_date"] == 0
    assert staging["n_trials_next"] == 1
    assert staging["spend_over_time"] == []
    assert staging["next_level"] > 0  # the staging economy's initial wealth -- finite, never a crash


def test_empty_ledger_files_degrade_to_honest_empty_snapshot_no_crash(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    canonical.write_text("", encoding="utf-8")
    staging = tmp_path / "staging.jsonl"
    staging.write_text("", encoding="utf-8")
    payload = build_budget_payload(canonical_path=str(canonical), staging_path=str(staging))
    assert payload["canonical"]["n_trials_to_date"] == 0
    assert payload["staging"]["n_trials_to_date"] == 0


def test_all_fail_ledger_staging_next_level_depletes_no_replenishment(tmp_path):
    """No PASS ever -> `rejection_offsets` is always empty -> the staging next-trial level keeps
    shrinking trial over trial (no replenishment), never climbing back up."""
    staging = tmp_path / "staging.jsonl"
    levels = []
    for i in range(5):
        append_entry(str(staging), _entry(f"f{i}", horizon=20 + i, deflation="lord++"))
        payload = build_budget_payload(
            canonical_path=str(tmp_path / "nope-canonical.jsonl"), staging_path=str(staging),
        )
        levels.append(payload["staging"]["next_level"])
    for earlier, later in zip(levels, levels[1:]):
        assert later < earlier


def test_spend_over_time_length_equals_count_trials_fixture(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    for i in range(4):
        append_entry(str(canonical), _entry(f"f{i}", horizon=20 + i))
    payload = build_budget_payload(
        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
    )
    assert len(payload["canonical"]["spend_over_time"]) == count_trials(str(canonical)) == 4


def test_forward_walk_entries_excluded_from_trial_count_and_spend_over_time(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    append_entry(str(canonical), _entry("f0"))
    forward_walk = _entry("f0", horizon=999)
    forward_walk["type"] = "forward_walk"
    append_entry(str(canonical), forward_walk)
    payload = build_budget_payload(
        canonical_path=str(canonical), staging_path=str(tmp_path / "nope-staging.jsonl"),
    )
    assert payload["canonical"]["n_trials_to_date"] == 1
    assert len(payload["canonical"]["spend_over_time"]) == 1


def test_spend_over_time_length_equals_count_trials_real_ledgers():
    payload = build_budget_payload()
    assert len(payload["canonical"]["spend_over_time"]) == count_trials(str(_CANONICAL_LEDGER))
    assert len(payload["staging"]["spend_over_time"]) == count_trials(str(_STAGING_LEDGER))
