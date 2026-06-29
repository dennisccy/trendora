"""Tests for the referee (statistical-honesty core) + the certified-claims ledger.

All referee tests are PURE + synthetic (no DB, fast). They prove the five contracts the decision-quality
loop depends on:
  * a TRUE persistent edge (cohort > control in BOTH in-sample and holdout) is certified PASS,
  * a NOISE edge (in-sample only, ~0 holdout) is rejected FAIL,
  * multiple-testing DEFLATION turns a borderline PASS at n_trials=1 into a FAIL at n_trials=50,
  * an exhausted alpha budget refuses (INSUFFICIENT),
  * purge+embargo drops the in-sample observations whose forward window overlaps the holdout,
  * the verdict is DETERMINISTIC given a seed,
  * the append-only ledger round-trips + reports count_trials / alpha_spent (missing file ⇒ empty).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from app.engine import ledger as ledger_mod
from app.engine.referee import (
    DEFAULT_ALPHA_PER_TEST,
    RefereeState,
    Verdict,
    certify_edge,
    purge_embargo_split,
)

_START = date(2021, 1, 3)


def _make_observations(
    *,
    n_dates: int,
    edge_at,
    seed: int,
    n_cohort: int = 8,
    n_control: int = 4,
    cohort_noise: float = 0.01,
    control_noise: float = 0.01,
    market_sigma: float = 0.02,
):
    """Synthesize ``(cohort, control)`` over `n_dates` consecutive calendar days. Each date draws a
    shared market level (which CANCELS in the cohort-minus-control excess, so the control earns its
    keep) plus per-name noise; the cohort additionally carries ``edge_at(i)`` on date index i."""
    rng = np.random.default_rng(seed)
    cohort: list = []
    control: list = []
    for i in range(n_dates):
        d = _START + timedelta(days=i)
        market = rng.normal(0.0, market_sigma)
        ed = edge_at(i)
        for _ in range(n_control):
            control.append((d, market + rng.normal(0.0, control_noise)))
        for _ in range(n_cohort):
            cohort.append((d, market + ed + rng.normal(0.0, cohort_noise)))
    return cohort, control


# ==================================================================================================
# TRUE persistent edge -> PASS
# ==================================================================================================
def test_true_persistent_edge_certifies_pass():
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    verdict = certify_edge(
        cohort, control, horizon=5, state=RefereeState(n_trials=1, alpha_budget_remaining=1.0), seed=7
    )
    assert verdict.status == "PASS", verdict.reason
    assert verdict.holdout_edge is not None and verdict.holdout_edge > 0
    assert verdict.in_sample_edge is not None and verdict.in_sample_edge > 0
    assert verdict.control_excess == verdict.holdout_edge
    assert verdict.p_value < DEFAULT_ALPHA_PER_TEST
    assert verdict.effective_n == verdict.holdout_dates >= 5
    # a stable edge (holdout confirms in-sample) confirms cheaply — no budget charged.
    assert verdict.alpha_charged == 0.0


# ==================================================================================================
# NOISE edge (in-sample only, ~0 holdout) -> FAIL
# ==================================================================================================
def test_noise_edge_is_rejected_fail():
    # edge present only on the earlier ~70% of dates (in-sample); ~0 on the later holdout dates.
    cohort, control = _make_observations(
        n_dates=60, edge_at=lambda i: 0.03 if i < 42 else 0.0, seed=2
    )
    verdict = certify_edge(
        cohort, control, horizon=5, state=RefereeState(n_trials=1, alpha_budget_remaining=1.0), seed=7
    )
    assert verdict.status == "FAIL", verdict.reason
    # the in-sample edge is real, but the holdout edge collapses to ~0 (overfit signal).
    assert verdict.in_sample_edge > 0.01
    assert abs(verdict.holdout_edge) < 0.01
    # an overfit edge (holdout diverges from in-sample) DID cost budget (the Thresholdout charge).
    assert verdict.alpha_charged > 0.0


# ==================================================================================================
# Multiple-testing deflation: borderline PASS @ n_trials=1 -> FAIL @ n_trials=50
# ==================================================================================================
def test_deflation_flips_borderline_pass_to_fail():
    # a real-but-modest persistent edge: significant on its own, borderline after deflation.
    cohort, control = _make_observations(
        n_dates=60, edge_at=lambda i: 0.022, seed=3,
        n_cohort=4, n_control=3, cohort_noise=0.05, control_noise=0.05,
    )
    at_1 = certify_edge(
        cohort, control, horizon=5, state=RefereeState(n_trials=1, alpha_budget_remaining=1.0), seed=7
    )
    at_50 = certify_edge(
        cohort, control, horizon=5, state=RefereeState(n_trials=50, alpha_budget_remaining=1.0), seed=7
    )
    # the SAME edge + the SAME holdout p-value — only the deflated bar moved.
    assert at_1.p_value == at_50.p_value
    assert 0.001 < at_1.p_value < DEFAULT_ALPHA_PER_TEST, at_1.p_value
    assert at_1.status == "PASS", at_1.reason
    assert at_50.status == "FAIL", at_50.reason
    assert at_50.required_p < at_1.required_p  # alpha/50 < alpha/1


# ==================================================================================================
# Budget exhaustion -> INSUFFICIENT (refuse to certify)
# ==================================================================================================
def test_exhausted_alpha_budget_refuses_insufficient():
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=4)
    verdict = certify_edge(
        cohort, control, horizon=5,
        state=RefereeState(n_trials=10, alpha_budget_remaining=0.0), seed=7,
    )
    assert verdict.status == "INSUFFICIENT", verdict.reason
    assert "budget" in verdict.reason.lower()
    assert verdict.alpha_charged == 0.0


# ==================================================================================================
# Purge + embargo excludes the in-sample observations overlapping the holdout (assert counts)
# ==================================================================================================
def test_purge_embargo_excludes_overlapping_in_sample():
    # one observation per consecutive day, so the purge boundary is exactly countable.
    n_dates = 40
    cohort = [(_START + timedelta(days=i), 0.01) for i in range(n_dates)]
    control = [(_START + timedelta(days=i), 0.0) for i in range(n_dates)]
    split = purge_embargo_split(cohort, control, horizon=5, holdout_fraction=0.30, embargo_fraction=0.5)
    assert split is not None

    gap = split.forward_window_days + split.embargo_days
    assert gap > 0
    purge_cutoff = split.holdout_start - timedelta(days=gap)

    # every surviving in-sample observation is at or before the purge cutoff (no forward-window overlap)
    assert all(d <= purge_cutoff for d, _ in split.in_sample_cohort)
    # every holdout observation is at or after the holdout start (the sealed later segment)
    assert all(d >= split.holdout_start for d, _ in split.holdout_cohort)
    # the purge actually dropped the boundary-adjacent in-sample observations
    assert split.purged_in_sample > 0
    in_raw = [d for d, _ in cohort if d <= split.split_date]
    expected_kept = sum(1 for d in in_raw if d <= purge_cutoff)
    expected_purged = len(in_raw) - expected_kept
    assert len(split.in_sample_cohort) == expected_kept
    assert split.purged_in_sample == expected_purged
    # the purged observations are precisely those inside (purge_cutoff, split_date]
    assert all(purge_cutoff < d <= split.split_date for d in in_raw if d > purge_cutoff)


def test_split_returns_none_without_two_distinct_dates():
    one_date = [(_START, 0.01), (_START, 0.02), (_START, 0.03)]
    assert purge_embargo_split(one_date, one_date, horizon=5) is None


# ==================================================================================================
# Determinism: same inputs + seed -> identical Verdict
# ==================================================================================================
def test_determinism_same_inputs_and_seed():
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.018, seed=5,
                                         cohort_noise=0.03, control_noise=0.03)
    state = RefereeState(n_trials=3, alpha_budget_remaining=0.8)
    v1 = certify_edge(cohort, control, horizon=10, state=state, seed=42)
    v2 = certify_edge(cohort, control, horizon=10, state=state, seed=42)
    assert v1 == v2  # frozen dataclass equality over every field
    assert isinstance(v1, Verdict)
    # a different seed may shift the bootstrap p-value (still deterministic per seed)
    v3 = certify_edge(cohort, control, horizon=10, state=state, seed=43)
    assert v3 == certify_edge(cohort, control, horizon=10, state=state, seed=43)


# ==================================================================================================
# Ledger: append -> read-back; count_trials / alpha_spent; missing file -> empty
# ==================================================================================================
def test_ledger_missing_file_is_empty(tmp_path):
    path = str(tmp_path / "nope" / "ledger.jsonl")
    assert ledger_mod.read_entries(path) == []
    assert ledger_mod.count_trials(path) == 0
    assert ledger_mod.alpha_spent(path) == 0.0


def test_ledger_append_read_and_aggregates(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    ledger_mod.append_entry(path, {"claim": {"kind": "factor"}, "verdict": {"status": "PASS", "alpha_charged": 0.0}})
    ledger_mod.append_entry(path, {"claim": {"kind": "factor"}, "verdict": {"status": "FAIL", "alpha_charged": 0.05}})
    ledger_mod.append_entry(path, {"claim": {"kind": "event-study"}, "verdict": {"status": "FAIL", "alpha_charged": 0.05}})

    entries = ledger_mod.read_entries(path)
    assert len(entries) == 3
    assert entries[0]["verdict"]["status"] == "PASS"
    assert ledger_mod.count_trials(path) == 3
    assert abs(ledger_mod.alpha_spent(path) - 0.10) < 1e-9

    # append-only: a new entry never rewrites the prior lines
    ledger_mod.append_entry(path, {"claim": {"kind": "factor"}, "verdict": {"status": "INSUFFICIENT", "alpha_charged": 0.0}})
    assert ledger_mod.count_trials(path) == 4
    assert ledger_mod.read_entries(path)[:3] == entries  # earlier lines unchanged


def test_ledger_drives_referee_state_across_claims(tmp_path):
    """The ledger's count_trials + alpha_spent are exactly the two state inputs the referee deflates
    against — proven by threading them through a second certification."""
    path = str(tmp_path / "ledger.jsonl")
    # record one prior overfit claim that charged budget
    ledger_mod.append_entry(path, {"verdict": {"alpha_charged": 0.05}})
    n_trials = ledger_mod.count_trials(path) + 1  # this claim's ordinal
    remaining = 1.0 - ledger_mod.alpha_spent(path)
    assert n_trials == 2 and abs(remaining - 0.95) < 1e-9

    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=6)
    verdict = certify_edge(
        cohort, control, horizon=5,
        state=RefereeState(n_trials=n_trials, alpha_budget_remaining=remaining), seed=7,
    )
    assert verdict.n_trials_at_test == 2
    assert verdict.status in {"PASS", "FAIL", "INSUFFICIENT"}
