"""Staging-ledger routing + injectable-deflation-policy tests (goal-mcp-loop iter-9).

The iter-9 economy is INJECTABLE and DEFAULT-OFF. These tests pin the load-bearing invariants that keep
the canonical `/evidence` bar byte-identical while enabling an isolated staging economy:

  * `ledger.rejection_offsets` derives the PASS ordinals (`[1, 2, 4]` on the live canonical ledger) —
    the wealth history the online-FDR economy reconstructs from — with NO entry rewritten;
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
    """The DoD anchor: on the live canonical `certified-claims.jsonl` (lines 1/2/4 PASS, line 3 `ma_stack`
    FAIL) the derived rejection ordinals are exactly `[1, 2, 4]` — proven WITHOUT rewriting any entry."""
    assert _CANONICAL_LEDGER.exists(), f"missing canonical ledger at {_CANONICAL_LEDGER}"
    assert ledger_mod.rejection_offsets(str(_CANONICAL_LEDGER)) == [1, 2, 4]
    assert ledger_mod.count_trials(str(_CANONICAL_LEDGER)) == 4


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
from app.engine.triad_scan import explore_multi_horizon_staging  # noqa: E402

# The claim shape each pre-registered candidate projects to (config.triad.candidates, in order).
_EXPECTED_CANDIDATES = [
    ("vcp_contraction", 10, 10),
    ("vcp_contraction", 60, 10),
    ("rs_spy_3m", 60, 10),
    ("leadership_score", 60, 10),
]  # (factor, horizon, decile)


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
    """The DoD anchor: the COMMITTED `staging-ledger.jsonl` is the frozen multi-horizon discovery iter-11
    promotes from. It carries EXACTLY the 4 pre-registered candidates (in order), all under the online-FDR
    (`lord++`) economy, with the referee's honest verdicts — and the canonical ledger stays byte-identical.

    The economy visibly REPLENISHES: after the h10 FAIL and the h60 PASSes, the required_p LOOSENS across
    trials (the exact LORD++ levels), and 3 of 4 candidates clear even the strict canonical divisor-5 bar
    (p < 0.010) — including 2 SIGNAL-LESS ones (the promotable J-07 winners)."""
    assert _STAGING_LEDGER.exists(), f"missing committed staging ledger at {_STAGING_LEDGER}"
    entries = ledger_mod.read_entries(str(_STAGING_LEDGER))
    assert len(entries) == 4

    claims = [(e["claim"]["factor"], e["claim"]["horizon"], e["claim"]["decile"]) for e in entries]
    assert claims == _EXPECTED_CANDIDATES
    verdicts = [e["verdict"] for e in entries]

    # every staging verdict was judged under the online-FDR economy (never Bonferroni).
    assert all(v["deflation"] == DEFLATION_ONLINE_FDR for v in verdicts)
    # the honest status pattern: h10 did NOT persist (FAIL); all three h60 cohorts PASS.
    assert [v["status"] for v in verdicts] == ["FAIL", "PASS", "PASS", "PASS"]

    # the EXACT LORD++ required-p levels — the economy replenishing after each discovery (bar LOOSENS).
    required_p = [v["required_p"] for v in verdicts]
    assert required_p == [
        pytest.approx(0.010937254144361815, abs=1e-15),  # trial 1, no priors  -> W0*g(1)
        pytest.approx(0.003607948341404759, abs=1e-15),  # trial 2, no priors  -> W0*g(2)
        pytest.approx(0.012823135192663515, abs=1e-15),  # trial 3, prior [2]  -> replenished
        pytest.approx(0.026672635724664270, abs=1e-15),  # trial 4, prior [2,3]-> replenished more
    ]
    assert required_p[3] > required_p[2] > required_p[1]  # wealth loosens the bar as discoveries land

    # PASS iff p_value < required_p; the FAIL's p_value is >= its bar (the honest non-clear).
    for v in verdicts:
        if v["status"] == "PASS":
            assert v["p_value"] < v["required_p"]
        else:
            assert v["p_value"] >= v["required_p"]

    # the deliverable for iter-11: >= 1 SIGNAL-LESS candidate clears the canonical divisor-5 bar (p<0.010).
    signalless_pass_clears = [
        e for e in entries
        if e["verdict"]["status"] == "PASS"
        and e["claim"]["factor"] != "leadership_score"          # signal-less (non-score column)
        and e["verdict"]["p_value"] < 0.010                     # clears strict Bonferroni divisor-5
    ]
    assert len(signalless_pass_clears) >= 1

    # the staging PASS ordinals feed iter-11's LORD++ wealth; the canonical ledger is UNCHANGED.
    assert ledger_mod.rejection_offsets(str(_STAGING_LEDGER)) == [2, 3, 4]
    assert ledger_mod.count_trials(str(_STAGING_LEDGER)) == 4
    assert ledger_mod.count_trials(str(_CANONICAL_LEDGER)) == 4          # canonical untouched (still 4)
    assert ledger_mod.rejection_offsets(str(_CANONICAL_LEDGER)) == [1, 2, 4]
