"""Tests for the forward-walk monitor (`app.engine.forward_walk`) — the *renewing holdout*.

These prove the monitor's contract WITHOUT a database (fast + synthetic), mirroring how
`tests/test_referee.py` injects synthetic observations and using the monitor's INJECTED assembler seam
(`assemble=`) so no DB ever boots:

  * UNCHANGED data -> the forward-walk verdict reproduces the original certification byte-for-byte;
  * MATURED data (extra later dates on which the edge has decayed) -> the forward-walk verdict FLIPS
    PASS -> FAIL (an edge that held out-of-sample at registration now fails forward);
  * the forward-walk record is APPENDED (type=forward_walk), REFERENCES the original claim, and is
    IDEMPOTENT (a second run at the same as-of appends nothing; a new as-of records a fresh re-score);
  * forward-walk monitoring does NOT change `count_trials` / `alpha_spent` for FUTURE certifications —
    even when the re-score itself is UNSTABLE and charges alpha inside its own verdict.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from app.engine import forward_walk
from app.engine import ledger as ledger_mod
from app.engine.referee import RefereeState, certify_edge

_START = date(2021, 1, 3)
_SEED = 7        # the original certification seed (the re-score must reuse it to reproduce the verdict)
_HORIZON = 5


def _make_observations(
    *, n_dates, edge_at, seed, n_cohort=8, n_control=4,
    cohort_noise=0.01, control_noise=0.01, market_sigma=0.02,
):
    """Synthesize ``(cohort, control)`` over `n_dates` consecutive calendar days — the SAME generator shape
    as `tests/test_referee.py`. A shared per-date market level CANCELS in the cohort-minus-control excess;
    the cohort additionally carries ``edge_at(i)`` on date index i. Seeding once and looping ``range(n)``
    means the first K dates of an n=K+M draw are byte-identical to an n=K draw — so the 100-date series is
    genuinely the 60-date registration series PLUS 40 newer dates."""
    rng = np.random.default_rng(seed)
    cohort, control = [], []
    for i in range(n_dates):
        d = _START + timedelta(days=i)
        market = rng.normal(0.0, market_sigma)
        ed = edge_at(i)
        for _ in range(n_control):
            control.append((d, market + rng.normal(0.0, control_noise)))
        for _ in range(n_cohort):
            cohort.append((d, market + ed + rng.normal(0.0, cohort_noise)))
    return cohort, control


def _seed_original_claim(path, claim, cohort, control, *, n_trials=1):
    """Write ONE original claim verdict to a fresh ledger exactly as `verify_edge` would (a row carrying
    `claim` + `register_date` + the referee's `verdict`), and return that `Verdict`. The verdict is the
    PURE referee on the supplied synthetic observations (no DB), seeded with `_SEED`."""
    verdict = certify_edge(
        cohort, control, horizon=_HORIZON,
        state=RefereeState(n_trials=n_trials, alpha_budget_remaining=1.0), seed=_SEED,
    )
    ledger_mod.append_entry(path, {
        "claim": claim, "register_date": "2021-06-01", "horizon": _HORIZON,
        "verdict": verdict.to_dict(),
    })
    return verdict


_CLAIM = {"kind": "factor", "horizon": _HORIZON, "factor": "mom", "slice_kind": "decile", "decile": 10}


# ==================================================================================================
# UNCHANGED data -> the re-score reproduces the original verdict exactly + records it referencing the claim
# ==================================================================================================
def test_unchanged_data_reproduces_original_verdict(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    original = _seed_original_claim(path, _CLAIM, cohort, control)
    assert original.status == "PASS"  # a true persistent edge certifies at registration

    # the assembler returns the SAME observations the claim was certified on (no new data has arrived yet).
    same = lambda _claim: (cohort, control, _HORIZON)
    appended = forward_walk.run(None, path, as_of_date="2021-09-01", assemble=same)

    assert len(appended) == 1
    rec = appended[0]
    assert rec["type"] == "forward_walk"
    assert rec["claim_ref"] == 0              # references the original entry (its index in the ledger)
    assert rec["as_of_date"] == "2021-09-01"
    # identical data + the original seed + the original ordinal => the re-score IS the original verdict.
    assert rec["verdict"] == original.to_dict()
    assert rec["verdict"]["status"] == "PASS"

    # the record was actually persisted (append-only): 1 original + 1 forward-walk = 2 lines, original kept.
    entries = ledger_mod.read_entries(path)
    assert len(entries) == 2
    assert entries[0]["claim"] == _CLAIM       # the original row is unchanged
    assert entries[1] == rec


# ==================================================================================================
# MATURED data -> an edge that held out-of-sample at registration FAILS forward (PASS -> FAIL)
# ==================================================================================================
def test_matured_data_flips_pass_to_fail_forward(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    base_cohort, base_control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    original = _seed_original_claim(path, _CLAIM, base_cohort, base_control)
    assert original.status == "PASS"

    # MATURED data: the SAME 60 registration dates PLUS 40 newer dates on which the edge has DECAYED
    # (gone negative). The renewed holdout (later ~30%) is now dominated by those new dates -> fails forward.
    ext_cohort, ext_control = _make_observations(
        n_dates=100, edge_at=lambda i: 0.02 if i < 60 else -0.02, seed=1,
    )
    matured = lambda _claim: (ext_cohort, ext_control, _HORIZON)

    appended = forward_walk.run(None, path, as_of_date="2022-01-01", assemble=matured)
    assert len(appended) == 1
    fw_verdict = appended[0]["verdict"]
    assert fw_verdict["status"] == "FAIL"                 # the edge no longer holds on matured data
    assert fw_verdict["status"] != original.status        # ... a genuine change from the original PASS
    assert fw_verdict["holdout_edge"] < 0                 # the renewed holdout edge went negative

    # the re-score used the claim's ORIGINAL ordinal (1), NOT a new trial — monitoring never inflates it.
    assert fw_verdict["n_trials_at_test"] == original.n_trials_at_test == 1


# ==================================================================================================
# Forward-walk monitoring does NOT consume the certification budget nor inflate the trial count
# ==================================================================================================
def test_forward_walk_does_not_consume_budget_or_inflate_trials(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    claim = {"kind": "factor", "horizon": _HORIZON, "factor": "mom", "slice_kind": "total"}
    base_cohort, base_control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    original = _seed_original_claim(path, claim, base_cohort, base_control)
    assert original.status == "PASS" and original.alpha_charged == 0.0  # stable -> charged nothing

    trials_before = ledger_mod.count_trials(path)
    alpha_before = ledger_mod.alpha_spent(path)
    assert trials_before == 1 and alpha_before == 0.0

    # re-score against matured data whose edge flipped -> the re-score itself is UNSTABLE (in-sample +,
    # holdout -) and charges alpha INSIDE its own verdict ... which must NOT touch the certification budget.
    ext_cohort, ext_control = _make_observations(
        n_dates=100, edge_at=lambda i: 0.02 if i < 60 else -0.02, seed=1,
    )
    matured = lambda _claim: (ext_cohort, ext_control, _HORIZON)
    appended = forward_walk.run(None, path, as_of_date="2022-01-01", assemble=matured)
    assert len(appended) == 1
    assert appended[0]["verdict"]["alpha_charged"] > 0.0  # the unstable re-score DID charge inside itself

    # ... yet the ledger's certification state is UNCHANGED: forward-walk records are excluded from BOTH
    # the multiple-testing count and the spent budget, so a FUTURE certification deflates exactly as before.
    assert ledger_mod.count_trials(path) == trials_before
    assert ledger_mod.alpha_spent(path) == alpha_before
    # there are physically 2 lines (1 original + 1 forward-walk) — the monitoring row exists, just excluded.
    assert len(ledger_mod.read_entries(path)) == 2


# ==================================================================================================
# Idempotency: re-running at the SAME as-of appends nothing; a NEW as-of records a fresh re-score
# ==================================================================================================
def test_forward_walk_is_idempotent(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    claim = {"kind": "factor", "horizon": _HORIZON, "factor": "mom", "slice_kind": "total"}
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    _seed_original_claim(path, claim, cohort, control)
    same = lambda _claim: (cohort, control, _HORIZON)

    first = forward_walk.run(None, path, as_of_date="2021-09-01", assemble=same)
    assert len(first) == 1
    after_first = ledger_mod.read_entries(path)

    # a SECOND run at the SAME as-of appends NOTHING (idempotent per (claim_ref, as_of_date)).
    second = forward_walk.run(None, path, as_of_date="2021-09-01", assemble=same)
    assert second == []
    assert ledger_mod.read_entries(path) == after_first  # the ledger is unchanged

    # but a LATER as-of (a new data frontier) DOES record a fresh re-score for the same claim.
    third = forward_walk.run(None, path, as_of_date="2021-12-01", assemble=same)
    assert len(third) == 1
    assert third[0]["as_of_date"] == "2021-12-01"
    assert third[0]["claim_ref"] == 0
    assert len(ledger_mod.read_entries(path)) == 3  # 1 original + 2 forward-walk (distinct as-ofs)


# ==================================================================================================
# Two claims -> a stable claim ref per original; an empty ledger -> a clean no-op
# ==================================================================================================
def test_multiple_claims_each_get_a_referenced_record(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    c0, k0 = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    c1, k1 = _make_observations(n_dates=60, edge_at=lambda i: 0.025, seed=2)
    _seed_original_claim(path, {"kind": "factor", "factor": "a", "slice_kind": "total"}, c0, k0)
    _seed_original_claim(path, {"kind": "factor", "factor": "b", "slice_kind": "total"}, c1, k1, n_trials=2)

    by_factor = {"a": (c0, k0, _HORIZON), "b": (c1, k1, _HORIZON)}
    assemble = lambda claim: by_factor[claim["factor"]]
    appended = forward_walk.run(None, path, as_of_date="2021-09-01", assemble=assemble)

    assert {rec["claim_ref"] for rec in appended} == {0, 1}  # one record per original, by ledger index
    assert ledger_mod.count_trials(path) == 2                # still two ORIGINAL trials (records excluded)


def test_empty_ledger_is_a_noop(tmp_path):
    path = str(tmp_path / "empty.jsonl")
    # missing file => no originals => nothing appended (and no DB touched: session=None, explicit as-of).
    assert forward_walk.run(None, path, as_of_date="2022-01-01", assemble=lambda _c: ([], [], _HORIZON)) == []
    assert ledger_mod.read_entries(path) == []


def test_module_imports_cleanly():
    import app.engine.forward_walk as fw

    assert callable(fw.run)
    assert fw.FORWARD_WALK_TYPE == "forward_walk"
