"""Staging-ledger routing + injectable-deflation-policy tests (goal-mcp-loop iter-9).

The iter-9 economy is INJECTABLE and DEFAULT-OFF. These tests pin the load-bearing invariants that keep
the canonical `/evidence` bar byte-identical while enabling an isolated staging economy:

  * `ledger.rejection_offsets` derives the PASS ordinals (`[1, 2, 4, 5, 6]` on the live canonical ledger after
    iter-11 promoted the vcp_contraction h60 winner and iter-13 promoted the rs_spy_3m × high_proximity
    combination winner) — the wealth history the online-FDR economy reconstructs from — with NO prior entry
    rewritten;
  * the referee's deflation is an INJECTABLE policy whose DEFAULT reproduces strict Bonferroni
    byte-identically, and a supplied `test_level` threads through as the exact bar;
  * `verify_edge` is the SINGLE writer routed to the target ledger: a staging-routed claim writes the
    staging file ONLY (canonical untouched), and a canonical-routed claim writes canonical under strict
    Bonferroni ONLY — cross-contamination is impossible in either direction;
  * the forward-walk reproduce-contract holds for BOTH policies: reconstructing `test_level` from a
    recorded `required_p` reproduces the original verdict byte-for-byte;
  * the gate routes per-claim and FAIL-CLOSES an unrecognized ledger value / an unset required path.
"""
from __future__ import annotations

import importlib.util
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest
from sqlmodel import Session

from app.engine import forward_walk
from app.engine import ledger as ledger_mod
from app.engine.referee import (
    DEFLATION_BONFERRONI,
    DEFLATION_ONLINE_FDR,
    RefereeState,
    certify_edge,
)
from app.mcp import tools

_START = date(2021, 1, 3)
# The repo-root canonical certified-claims ledger (the live 4-entry honest history).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CANONICAL_LEDGER = _REPO_ROOT / "runs" / "goal-session-mcp-loop" / "state" / "certified-claims.jsonl"
# goal-mcp-loop iter-10 — the committed INTERNAL staging ledger (the multi-horizon discovery, 4 verdicts).
_STAGING_LEDGER = _REPO_ROOT / "runs" / "goal-session-mcp-loop" / "state" / "staging-ledger.jsonl"


def _make_observations(*, n_dates, edge_at, seed, n_cohort=8, n_control=4,
                       cohort_noise=0.01, control_noise=0.01, market_sigma=0.02):
    """Synthetic ``(cohort, control)`` — the SAME shape as tests/test_referee.py. A shared per-date market
    level cancels in the excess; the cohort carries ``edge_at(i)`` on date i. Seeding once + looping means
    the first K dates of an n=K+M draw are byte-identical to an n=K draw (so matured data extends cleanly)."""
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


def _pass_fail_ledger(path: str) -> None:
    """Write a synthetic 4-entry ledger mirroring the canonical PASS/PASS/FAIL/PASS shape (lines 1/2/4
    PASS, line 3 FAIL) so `rejection_offsets` derives `[1, 2, 4]` exactly as it does on the live file."""
    for status in ("PASS", "PASS", "FAIL", "PASS"):
        ledger_mod.append_entry(path, {"claim": {"kind": "factor"}, "verdict": {"status": status, "alpha_charged": 0.05}})


# ==================================================================================================
# ledger.rejection_offsets — the PASS ordinals feeding the LORD++ wealth reconstruction
# ==================================================================================================
def test_rejection_offsets_derives_pass_ordinals(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    _pass_fail_ledger(path)
    assert ledger_mod.rejection_offsets(path) == [1, 2, 4]
    assert ledger_mod.count_trials(path) == 4  # unchanged — offsets are DERIVED, nothing rewritten


def test_rejection_offsets_skips_forward_walk_records(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    ledger_mod.append_entry(path, {"claim": {"kind": "factor"}, "verdict": {"status": "PASS"}})       # ordinal 1 PASS
    ledger_mod.append_entry(path, {"type": "forward_walk", "verdict": {"status": "FAIL"}})            # skipped
    ledger_mod.append_entry(path, {"claim": {"kind": "factor"}, "verdict": {"status": "PASS"}})       # ordinal 2 PASS
    # the forward-walk MONITORING row neither advances the ordinal nor appears as a rejection.
    assert ledger_mod.rejection_offsets(path) == [1, 2]
    assert ledger_mod.count_trials(path) == 2


def test_rejection_offsets_missing_file_is_empty(tmp_path):
    assert ledger_mod.rejection_offsets(str(tmp_path / "nope.jsonl")) == []


def test_rejection_offsets_on_live_canonical_ledger():
    """The DoD anchor: on the live canonical `certified-claims.jsonl` the derived rejection ordinals track the
    honest history WITHOUT rewriting any entry. After iter-11 (J-07) promoted the vcp_contraction h60 winner
    and iter-13 (J-08) promoted the rs_spy_3m × high_proximity combination winner, the ledger is lines
    1/2/4/5/6 PASS, line 3 `ma_stack` FAIL — so the rejection ordinals are `[1, 2, 4, 5, 6]` over 6 trials
    (the FAIL at position 3 advances the ordinal but is not a rejection)."""
    assert _CANONICAL_LEDGER.exists(), f"missing canonical ledger at {_CANONICAL_LEDGER}"
    assert ledger_mod.rejection_offsets(str(_CANONICAL_LEDGER)) == [1, 2, 4, 5, 6]
    assert ledger_mod.count_trials(str(_CANONICAL_LEDGER)) == 6


# ==================================================================================================
# The referee deflation is an INJECTABLE policy — DEFAULT reproduces Bonferroni byte-identically
# ==================================================================================================
def test_default_policy_is_bonferroni_byte_identical():
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    v = certify_edge(cohort, control, horizon=5,
                     state=RefereeState(n_trials=3, alpha_budget_remaining=1.0), seed=7)
    # the default path: required_p = alpha_per_test / n_trials, policy named "bonferroni".
    assert v.deflation == DEFLATION_BONFERRONI
    assert v.deflation_divisor == 3
    assert v.required_p == pytest.approx(0.05 / 3, abs=1e-15)
    # the reason still renders the exact Bonferroni bar description ("alpha/{divisor}=...").
    assert f"alpha/3={0.05 / 3:.4g}" in v.reason


def test_injected_test_level_threads_through_as_the_bar():
    """A supplied `test_level` becomes the EXACT significance bar the verdict is judged at (the staging
    online-FDR seam). The SAME data + seed flips PASS<->FAIL purely on the injected level — proving the
    policy is the only thing that moved."""
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    loose = certify_edge(cohort, control, horizon=5,
                         state=RefereeState(n_trials=1, alpha_budget_remaining=1.0,
                                            deflation=DEFLATION_ONLINE_FDR, test_level=0.5), seed=7)
    tight = certify_edge(cohort, control, horizon=5,
                         state=RefereeState(n_trials=1, alpha_budget_remaining=1.0,
                                            deflation=DEFLATION_ONLINE_FDR, test_level=1e-9), seed=7)
    assert loose.required_p == 0.5 and tight.required_p == 1e-9
    assert loose.deflation == DEFLATION_ONLINE_FDR and tight.deflation == DEFLATION_ONLINE_FDR
    # a real persistent edge clears a generous bar and fails a near-zero one — same p_value, different bar.
    assert loose.p_value == tight.p_value
    assert loose.status == "PASS" and tight.status == "FAIL"
    assert "lord++ level" in tight.reason  # the FDR bar description, not "alpha/divisor="


# ==================================================================================================
# Ledger isolation — staging and canonical never share state (pure, no DB)
# ==================================================================================================
def test_staging_and_canonical_ledgers_are_isolated(tmp_path):
    canonical = str(tmp_path / "certified-claims.jsonl")
    staging = str(tmp_path / "staging-ledger.jsonl")
    ledger_mod.append_entry(canonical, {"claim": {"k": 1}, "verdict": {"status": "PASS", "alpha_charged": 0.0}})
    for _ in range(5):
        ledger_mod.append_entry(staging, {"claim": {"k": 2}, "verdict": {"status": "PASS", "alpha_charged": 0.0}})
    # each file's aggregates are independent — a staging write never advances the canonical counters.
    assert ledger_mod.count_trials(canonical) == 1
    assert ledger_mod.count_trials(staging) == 5
    assert ledger_mod.rejection_offsets(canonical) == [1]
    assert ledger_mod.rejection_offsets(staging) == [1, 2, 3, 4, 5]


# ==================================================================================================
# forward-walk reproduce-contract for BOTH policies (reconstruct test_level from recorded required_p)
# ==================================================================================================
def _seed_claim(path, claim, cohort, control, *, state):
    verdict = certify_edge(cohort, control, horizon=5, state=state, seed=7)
    ledger_mod.append_entry(path, {"claim": claim, "register_date": "2021-06-01", "horizon": 5,
                                   "verdict": verdict.to_dict()})
    return verdict


def test_forward_walk_reproduces_bonferroni_and_fdr_verdicts(tmp_path):
    cohort, control = _make_observations(n_dates=60, edge_at=lambda i: 0.02, seed=1)
    same = lambda _c: (cohort, control, 5)

    # a Bonferroni original: the re-score re-derives alpha/divisor from the ordinal (test_level None) — unchanged.
    bon_path = str(tmp_path / "bon.jsonl")
    bon = _seed_claim(bon_path, {"kind": "factor", "factor": "a"}, cohort, control,
                      state=RefereeState(n_trials=1, alpha_budget_remaining=1.0))
    assert bon.deflation == DEFLATION_BONFERRONI
    bon_rescore = forward_walk.run(None, bon_path, as_of_date="2021-09-01", assemble=same)
    assert bon_rescore[0]["verdict"] == bon.to_dict()

    # a staging online-FDR original: the re-score reconstructs `test_level` from the recorded `required_p`,
    # so the LORD++ bar is pinned and the verdict reproduces byte-for-byte (only newer DATA could move it).
    fdr_path = str(tmp_path / "fdr.jsonl")
    fdr = _seed_claim(fdr_path, {"kind": "factor", "factor": "b"}, cohort, control,
                      state=RefereeState(n_trials=1, alpha_budget_remaining=1.0,
                                         deflation=DEFLATION_ONLINE_FDR, test_level=0.03))
    assert fdr.deflation == DEFLATION_ONLINE_FDR and fdr.required_p == 0.03
    fdr_rescore = forward_walk.run(None, fdr_path, as_of_date="2021-09-01", assemble=same)
    assert fdr_rescore[0]["verdict"] == fdr.to_dict()  # byte-for-byte reproduction under the FDR policy


# ==================================================================================================
# The gate routes per-claim and FAIL-CLOSES bad routing (unrecognized value / unset path)
# ==================================================================================================
def _load_gate():
    gate_path = _REPO_ROOT / "project-extensions" / "gates" / "verify_claim.py"
    spec = importlib.util.spec_from_file_location("verify_claim_gate", gate_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_resolves_ledger_and_fails_closed(monkeypatch):
    gate = _load_gate()
    monkeypatch.setenv("LEDGER_PATH", "/tmp/canonical.jsonl")
    monkeypatch.setenv("STAGING_LEDGER_PATH", "/tmp/staging.jsonl")

    # default (no "ledger" key) -> staging.
    kind, env, path, err = gate.resolve_claim_ledger({"kind": "factor"})
    assert (kind, env, path, err) == ("staging", "STAGING_LEDGER_PATH", "/tmp/staging.jsonl", None)
    # explicit canonical -> the canonical path.
    kind, env, path, err = gate.resolve_claim_ledger({"kind": "factor", "ledger": "canonical"})
    assert (kind, env, path, err) == ("canonical", "LEDGER_PATH", "/tmp/canonical.jsonl", None)
    # an UNRECOGNIZED ledger value -> fail-closed (no path, a blocking error).
    kind, env, path, err = gate.resolve_claim_ledger({"ledger": "production"})
    assert kind == "production" and path is None and err and "unrecognized" in err
    # a required path UNSET -> fail-closed.
    monkeypatch.delenv("STAGING_LEDGER_PATH", raising=False)
    kind, env, path, err = gate.resolve_claim_ledger({"kind": "factor"})
    assert path is None and err and "STAGING_LEDGER_PATH unset" in err


# ==================================================================================================
# DB integration — verify_edge is the SINGLE writer, routed to the target ledger with the right policy
# ==================================================================================================
def test_verify_edge_routes_to_staging_only_and_leaves_canonical_untouched(loaded_engine, tmp_path):
    canonical = str(tmp_path / "certified-claims.jsonl")
    staging = str(tmp_path / "staging-ledger.jsonl")
    with Session(loaded_engine) as session:
        fl = tools.query_factor_lab(session)
        claim = {"kind": "factor", "horizon": fl["horizon"], "factor": fl["factor"]["key"], "slice_kind": "total"}

        # a STAGING-routed claim writes the staging file ONLY (canonical stays absent — never touched).
        out_s = tools.verify_edge(session, claim, staging, register_date="2026-06-29", ledger="staging")
        assert out_s["ledger"] == "staging"
        assert ledger_mod.count_trials(staging) == 1
        assert ledger_mod.read_entries(canonical) == []  # canonical is untouched by a staging write

        # a CANONICAL-routed claim writes the canonical file ONLY, under strict Bonferroni.
        out_c = tools.verify_edge(session, claim, canonical, register_date="2026-06-29", ledger="canonical")
        assert out_c["ledger"] == "canonical"
        assert out_c["verdict"]["deflation"] == DEFLATION_BONFERRONI
        assert out_c["verdict"]["required_p"] == pytest.approx(0.05 / 1, abs=1e-15)  # trial 1, divisor 1
        assert ledger_mod.count_trials(canonical) == 1
        assert ledger_mod.count_trials(staging) == 1  # the staging file did not gain a second entry


def test_verify_edge_fdr_runs_in_staging_but_canonical_stays_bonferroni(loaded_engine, tmp_path, monkeypatch):
    """The HONESTY FENCE (anti-goal #1/#4): with the online-FDR economy ENABLED, a STAGING claim is judged
    at the LORD++ level, but a CANONICAL claim is STILL strict Bonferroni — FDR (weaker than family-wise
    control) never touches the user-facing `/evidence` bar."""
    from app.config import load_config
    from app.engine import online_fdr

    cfg = load_config()               # a FRESH load (not the process cache) so mutating it is test-local
    cfg.evidence.fdr.enabled = True
    monkeypatch.setattr(tools, "get_config", lambda: cfg)

    staging = str(tmp_path / "staging-ledger.jsonl")
    canonical = str(tmp_path / "certified-claims.jsonl")
    with Session(loaded_engine) as session:
        fl = tools.query_factor_lab(session)
        claim = {"kind": "factor", "horizon": fl["horizon"], "factor": fl["factor"]["key"], "slice_kind": "total"}
        out_s = tools.verify_edge(session, claim, staging, register_date="2026-06-29", ledger="staging")
        out_c = tools.verify_edge(session, claim, canonical, register_date="2026-06-29", ledger="canonical")

    # STAGING ran under the online-FDR economy: the bar is the LORD++ level for trial 1, no prior rejections.
    assert out_s["verdict"]["deflation"] == DEFLATION_ONLINE_FDR
    expected_level = online_fdr.test_level(
        1, [], alpha=cfg.evidence.fdr.alpha, w0_fraction=cfg.evidence.fdr.w0_fraction,
        gamma_exponent=cfg.evidence.fdr.gamma_exponent, gamma_terms=cfg.evidence.fdr.gamma_terms,
    )
    assert out_s["verdict"]["required_p"] == expected_level
    # CANONICAL stayed strict Bonferroni despite FDR being enabled — the fence holds.
    assert out_c["verdict"]["deflation"] == DEFLATION_BONFERRONI
    assert out_c["verdict"]["required_p"] == pytest.approx(0.05 / 1, abs=1e-15)


# ==================================================================================================
# goal-mcp-loop iter-10 (Part B Phase 1) — the multi-horizon STAGING exploration
# (`app.engine.triad_scan.explore_multi_horizon_staging`). It runs the PRE-REGISTERED candidate set
# through the referee into the INTERNAL staging ledger ONLY, under the online-FDR economy, never
# touching the canonical Bonferroni bar. These tests pin: determinism + staging-isolation, the
# thin-fixture INSUFFICIENT path, the fail-closed canonical-path guard, and the committed frozen ledger.
# ==================================================================================================
from app.engine.triad_scan import (  # noqa: E402
    explore_combination_staging,
    explore_multi_horizon_staging,
)

# The claim shape each pre-registered candidate projects to (config.triad.candidates, in order).
_EXPECTED_CANDIDATES = [
    ("vcp_contraction", 10, 10),
    ("vcp_contraction", 60, 10),
    ("rs_spy_3m", 60, 10),
    ("leadership_score", 60, 10),
]  # (factor, horizon, decile)

# iter-12: the condition-leg pairs each pre-registered COMBINATION candidate projects to (config order,
# config.triad.combination_candidates). Every one is a composite-cohort claim at horizon 20, direction positive.
_EXPECTED_COMBINATION_CANDIDATES = [
    ["rs_spy_3m:top:quintile", "atr_pct:bottom:tertile"],
    ["leadership_score:top:quintile", "atr_pct:bottom:tertile"],
    ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
]


def test_explore_multi_horizon_staging_is_deterministic_and_staging_only(loaded_engine, tmp_path):
    """The exploration is DETERMINISTIC (same DB + seed + fixed register_date -> byte-identical) and writes
    the staging file ONLY: two runs to fresh paths produce identical ledger bytes, one verdict per
    pre-registered candidate, and the canonical ledger is never created/touched."""
    canonical = str(tmp_path / "certified-claims.jsonl")
    staging_a = str(tmp_path / "a" / "staging-ledger.jsonl")
    staging_b = str(tmp_path / "b" / "staging-ledger.jsonl")
    with Session(loaded_engine) as session:
        out_a = explore_multi_horizon_staging(session, ledger_path=staging_a)
    with Session(loaded_engine) as session:
        out_b = explore_multi_horizon_staging(session, ledger_path=staging_b)

    # byte-identical re-run (determinism — the load-bearing reproduce contract).
    assert Path(staging_a).read_text() == Path(staging_b).read_text()
    # one verdict per pre-registered candidate, in the config order (NEVER the full cross-product).
    assert out_a["n_candidates"] == len(_EXPECTED_CANDIDATES)
    assert ledger_mod.count_trials(staging_a) == len(_EXPECTED_CANDIDATES)
    got = [(r["claim"]["factor"], r["claim"]["horizon"], r["claim"]["decile"]) for r in out_a["results"]]
    assert got == _EXPECTED_CANDIDATES
    for r in out_a["results"]:
        assert r["claim"]["direction"] == "positive"
        assert r["ledger"] == "staging"
    # the canonical ledger was never created by a staging exploration.
    assert not Path(canonical).exists()
    assert ledger_mod.read_entries(canonical) == []


def test_explore_multi_horizon_staging_records_insufficient_on_thin_fixture(loaded_engine, tmp_path):
    """The ERROR path (surfaced, not dropped, not crashing): on the thin quarterly test fixture every
    candidate's sealed holdout has too few dates for the block bootstrap, so each is honestly recorded as
    INSUFFICIENT — and every verdict carries `deflation == "lord++"`, proving the online-FDR economy is
    ACTIVE in staging under the real (iter-10) config (`evidence.fdr.enabled: true`)."""
    staging = str(tmp_path / "staging-ledger.jsonl")
    with Session(loaded_engine) as session:
        out = explore_multi_horizon_staging(session, ledger_path=staging)
    assert len(out["results"]) == len(_EXPECTED_CANDIDATES)
    for r in out["results"]:
        v = r["verdict"]
        assert v["status"] == "INSUFFICIENT"           # thin sealed holdout -> honestly refused
        assert v["holdout_dates"] < 5                   # below DEFAULT_MIN_HOLDOUT_DATES (why it refused)
        assert v["deflation"] == DEFLATION_ONLINE_FDR   # FDR economy active in staging (iter-10 activation)


def test_explore_multi_horizon_staging_refuses_the_canonical_ledger(loaded_engine, config):
    """Fail-closed guard: the staging exploration REFUSES to operate on the canonical ledger path — a
    mis-wired call can never write or clear the user-facing `/evidence` ledger."""
    canonical_path = config.evidence.ledger_path  # relative; the function resolves + compares against it
    with Session(loaded_engine) as session:
        with pytest.raises(ValueError, match="refuses to write the CANONICAL ledger"):
            explore_multi_horizon_staging(session, config, ledger_path=str(_CANONICAL_LEDGER))
        # also blocked when the config-relative canonical path is passed verbatim.
        with pytest.raises(ValueError, match="CANONICAL"):
            explore_multi_horizon_staging(session, config, ledger_path=canonical_path)


def test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery():
    """The DoD anchor: the COMMITTED `staging-ledger.jsonl` is the frozen staging discovery — now 7 entries,
    ALL under the online-FDR (`lord++`) economy: the 4 pre-registered SINGLE-FACTOR multi-horizon candidates
    (iter-10, entries #1-4 — the discovery iter-11 promoted J-07 from) FOLLOWED BY the 3 pre-registered
    2-factor COMBINATION candidates (iter-12, entries #5-7 — the basis iter-13 promotes J-08 from). This
    staging exploration NEVER writes the canonical ledger (which iter-11 grew 4→5 by promoting the h60 winner).

    Single-factor prefix (unchanged, iter-10): the economy visibly REPLENISHES — after the h10 FAIL and the
    h60 PASSes the required_p LOOSENS, and 3 of 4 clear even the strict canonical divisor-5 bar (p<0.010).
    Combination suffix (iter-12): the two 'obvious' anchor pairs FAIL out-of-sample at h20 (the low-ATR filter
    HURTS the momentum/leadership edge — an honest referee refusal, anti-goal #1/#4 upheld), while `rs_spy_3m`
    leaders that are ALSO near their 52-week high PASS with a raw block-bootstrap p that clears even the
    canonical divisor-6 bar (p<0.00833) with margin — the real recorded basis iter-13 promotes to surface J-08."""
    assert _STAGING_LEDGER.exists(), f"missing committed staging ledger at {_STAGING_LEDGER}"
    entries = ledger_mod.read_entries(str(_STAGING_LEDGER))
    assert len(entries) == 7

    # -- the SINGLE-FACTOR prefix (iter-10, entries #1-4) — the unchanged frozen multi-horizon discovery ----
    sf = entries[:4]
    sf_claims = [(e["claim"]["factor"], e["claim"]["horizon"], e["claim"]["decile"]) for e in sf]
    assert sf_claims == _EXPECTED_CANDIDATES
    sf_verdicts = [e["verdict"] for e in sf]
    assert all(v["deflation"] == DEFLATION_ONLINE_FDR for v in sf_verdicts)
    # the honest status pattern: h10 did NOT persist (FAIL); all three h60 cohorts PASS.
    assert [v["status"] for v in sf_verdicts] == ["FAIL", "PASS", "PASS", "PASS"]
    # the EXACT LORD++ required-p levels — the economy replenishing after each discovery (bar LOOSENS).
    sf_required_p = [v["required_p"] for v in sf_verdicts]
    assert sf_required_p == [
        pytest.approx(0.010937254144361815, abs=1e-15),  # trial 1, no priors  -> W0*g(1)
        pytest.approx(0.003607948341404759, abs=1e-15),  # trial 2, no priors  -> W0*g(2)
        pytest.approx(0.012823135192663515, abs=1e-15),  # trial 3, prior [2]  -> replenished
        pytest.approx(0.026672635724664270, abs=1e-15),  # trial 4, prior [2,3]-> replenished more
    ]
    assert sf_required_p[3] > sf_required_p[2] > sf_required_p[1]  # wealth loosens the bar as discoveries land
    # >= 1 SIGNAL-LESS single-factor candidate clears the canonical divisor-5 bar (the J-07 promotion winner).
    signalless_pass_clears = [
        e for e in sf
        if e["verdict"]["status"] == "PASS"
        and e["claim"]["factor"] != "leadership_score"          # signal-less (non-score column)
        and e["verdict"]["p_value"] < 0.010                     # clears strict Bonferroni divisor-5
    ]
    assert len(signalless_pass_clears) >= 1

    # -- the COMBINATION suffix (iter-12, entries #5-7) — the J-08 enablement basis -----------------------
    comb = entries[4:]
    comb_claims = [
        (e["claim"]["kind"], e["claim"]["cohort"], e["claim"]["horizon"], e["claim"]["condition"]) for e in comb
    ]
    assert comb_claims == [
        ("combination", "composite", 20, _EXPECTED_COMBINATION_CANDIDATES[0]),
        ("combination", "composite", 20, _EXPECTED_COMBINATION_CANDIDATES[1]),
        ("combination", "composite", 20, _EXPECTED_COMBINATION_CANDIDATES[2]),
    ]
    comb_verdicts = [e["verdict"] for e in comb]
    assert all(v["deflation"] == DEFLATION_ONLINE_FDR for v in comb_verdicts)  # judged in the same economy
    # honest referee: the two 'obvious' anchor pairs FAIL out-of-sample at h20; the RS-near-high pair PASSES.
    assert [v["status"] for v in comb_verdicts] == ["FAIL", "FAIL", "PASS"]
    # the EXACT LORD++ required-p levels for trials 5-7 (the economy continues from the 4 single-factor trials;
    # trials 5+6 FAIL so the PASS-ordinal history stays [2,3,4] across the whole combination run).
    comb_required_p = [v["required_p"] for v in comb_verdicts]
    assert comb_required_p == [
        pytest.approx(0.03180911589706088, abs=1e-15),   # trial 5, prior rejections [2,3,4]
        pytest.approx(0.012799946614451493, abs=1e-15),  # trial 6, still [2,3,4] (#5 FAILed)
        pytest.approx(0.007471079062231945, abs=1e-15),  # trial 7, still [2,3,4] (#6 FAILed)
    ]
    # each combination verdict carries the fields iter-13 reads to pick a promotable winner (DoD).
    for e in comb:
        v = e["verdict"]
        for key in ("status", "p_value", "holdout_edge", "control_excess",
                    "cohort_n", "control_n", "deflation", "required_p"):
            assert key in v, f"combination verdict missing {key!r}"
        assert e["horizon"] == 20               # the horizon is recorded on the entry
        assert len(e["claim"]["condition"]) == 2  # the two condition legs are recorded
    # PASS iff p_value < required_p (honest clear / non-clear) — the same rule as the single-factor prefix.
    for v in comb_verdicts:
        if v["status"] == "PASS":
            assert v["p_value"] < v["required_p"]
        else:
            assert v["p_value"] >= v["required_p"]

    # the iter-13 deliverable: the WINNER (rs_spy_3m + high_proximity) clears the canonical divisor-6 bar —
    # its RAW block-bootstrap p (economy-independent) is < 0.05/6 ≈ 0.00833 with margin — a real recorded
    # basis to PROMOTE + surface J-08. The two anchor pairs are honest FAILs (a thin/weak composite refused).
    winner = comb[2]
    assert winner["claim"]["condition"] == _EXPECTED_COMBINATION_CANDIDATES[2]
    assert winner["verdict"]["status"] == "PASS"
    assert winner["verdict"]["p_value"] == pytest.approx(0.0009995002498750624, abs=1e-15)
    assert winner["verdict"]["p_value"] < 0.05 / 6       # clears the canonical Bonferroni divisor-6 bar
    assert winner["verdict"]["holdout_edge"] > 0         # a genuine positive out-of-sample edge

    # -- whole-ledger aggregates + the untouched canonical ledger ----------------------------------------
    # PASS ordinals over the 7 entries: #2,#3,#4 (single-factor) + #7 (the combination winner).
    assert ledger_mod.rejection_offsets(str(_STAGING_LEDGER)) == [2, 3, 4, 7]
    assert ledger_mod.count_trials(str(_STAGING_LEDGER)) == 7
    # the canonical ledger is UNTOUCHED by any staging exploration — it grew ONLY by DELIBERATE promotion:
    # iter-11's 5 strict-Bonferroni entries PLUS iter-13's promoted combination winner = 6 entries (PASS
    # ordinals 1,2,4,5,6). None of the 7 staging FDR trials above ever wrote canonical. The honesty fence:
    # FDR is fenced to staging; canonical stays strict Bonferroni and only receives explicitly promoted winners.
    assert ledger_mod.count_trials(str(_CANONICAL_LEDGER)) == 6
    assert ledger_mod.rejection_offsets(str(_CANONICAL_LEDGER)) == [1, 2, 4, 5, 6]


# ==================================================================================================
# goal-mcp-loop iter-12 (Part B Phase 1 — combinations half) — the 2-factor COMBINATION STAGING
# exploration (`app.engine.triad_scan.explore_combination_staging`). It runs the PRE-REGISTERED
# `config.triad.combination_candidates` set through the referee into the INTERNAL staging ledger ONLY,
# under the online-FDR economy, projecting each pair into a `kind:"combination"` composite-cohort claim
# (REUSING the referee cert path unchanged) — never touching the canonical Bonferroni bar. These tests
# pin: the exact composite-claim projection + staging-isolation, determinism, the fail-closed
# canonical-path guard, and that a malformed candidate raises loudly (never a silent skip).
# (The pre-registered pairs are pinned in `_EXPECTED_COMBINATION_CANDIDATES` near the top of this file.)
# ==================================================================================================
def test_explore_combination_staging_projects_composite_claims_and_is_staging_only(loaded_engine, tmp_path):
    """The combination exploration projects each `config.triad.combination_candidates` entry into the EXACT
    `{kind:"combination", cohort:"composite", horizon:20, direction:"positive", condition:[leg1, leg2]}`
    claim, certifies each via `verify_edge(ledger="staging")`, and writes the staging file ONLY: one verdict
    per pre-registered pair (in config order — NEVER the full cross-product), canonical never created."""
    canonical = str(tmp_path / "certified-claims.jsonl")
    staging = str(tmp_path / "staging-ledger.jsonl")
    with Session(loaded_engine) as session:
        out = explore_combination_staging(session, ledger_path=staging)

    assert out["ledger"] == "staging"
    assert out["n_candidates"] == len(_EXPECTED_COMBINATION_CANDIDATES)
    assert ledger_mod.count_trials(staging) == len(_EXPECTED_COMBINATION_CANDIDATES)
    # one verdict per pre-registered pair, in the config order, each the exact composite claim shape.
    got = [r["claim"]["condition"] for r in out["results"]]
    assert got == _EXPECTED_COMBINATION_CANDIDATES
    for r in out["results"]:
        c = r["claim"]
        assert c["kind"] == "combination"
        assert c["cohort"] == "composite"
        assert c["horizon"] == 20
        assert c["direction"] == "positive"
        assert r["ledger"] == "staging"
    # the canonical ledger was never created/touched by a combination staging exploration.
    assert not Path(canonical).exists()
    assert ledger_mod.read_entries(canonical) == []


def test_explore_combination_staging_is_deterministic(loaded_engine, tmp_path):
    """Determinism (same DB + fixed seed + fixed register_date -> byte-identical): two runs to fresh paths
    produce identical ledger bytes — the reproduce contract iter-13 relies on to re-derive the staging p."""
    staging_a = str(tmp_path / "a" / "staging-ledger.jsonl")
    staging_b = str(tmp_path / "b" / "staging-ledger.jsonl")
    with Session(loaded_engine) as session:
        explore_combination_staging(session, ledger_path=staging_a)
    with Session(loaded_engine) as session:
        explore_combination_staging(session, ledger_path=staging_b)
    assert Path(staging_a).read_text() == Path(staging_b).read_text()


def test_explore_combination_staging_refuses_the_canonical_ledger(loaded_engine, config):
    """Fail-closed guard: the combination exploration REFUSES to operate on the canonical ledger path (same
    as the single-factor explorer) — a mis-wired call can never write or clear the user-facing `/evidence`
    ledger. Blocked for both an absolute canonical path and the config-relative one passed verbatim."""
    with Session(loaded_engine) as session:
        with pytest.raises(ValueError, match="refuses to write the CANONICAL ledger"):
            explore_combination_staging(session, config, ledger_path=str(_CANONICAL_LEDGER))
        with pytest.raises(ValueError, match="CANONICAL"):
            explore_combination_staging(session, config, ledger_path=config.evidence.ledger_path)


def test_explore_combination_staging_raises_loudly_on_a_malformed_candidate(loaded_engine, tmp_path):
    """Error cases surface LOUDLY (`ValueError`), never silently skipped: an unknown factor key, a malformed
    condition string (not `<factor>:<side>:<quantile>`), and an unknown quantile each raise. Uses a FRESH
    config so the bad candidate never contaminates the real registered set nor the committed ledger."""
    from app.config import load_config
    staging = str(tmp_path / "staging-ledger.jsonl")

    def _run(condition):
        cfg = load_config()  # fresh (not the process cache) — the bad candidate stays test-local
        cfg.triad = {"combination_candidates": [
            {"condition": condition, "horizon": 20, "direction": "positive"}
        ]}
        with Session(loaded_engine) as session:
            explore_combination_staging(session, cfg, ledger_path=staging)

    with pytest.raises(ValueError, match="unknown factor"):
        _run(["bogus_factor:top:quintile", "atr_pct:bottom:tertile"])
    with pytest.raises(ValueError, match="must be '<factor_key>:<side>:<quantile_key>'"):
        _run(["rs_spy_3m:top", "atr_pct:bottom:tertile"])          # malformed leg — only 2 colon-parts
    with pytest.raises(ValueError, match="unknown quantile"):
        _run(["rs_spy_3m:top:decile", "atr_pct:bottom:tertile"])   # 'decile' is not a combination quantile key
    # nothing was ever appended on the error path — no partial/silent staging write.
    assert not Path(staging).exists() or ledger_mod.read_entries(staging) == []
