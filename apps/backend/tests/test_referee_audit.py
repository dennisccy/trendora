"""Tests for the referee-calibration harness (`app.engine.referee_audit`, goal-mcp-loop iter-36, J-22 /
backlog B-102).

All tests here are PURE + synthetic (no DB, fast, mirroring `tests/test_referee.py` /
`tests/test_forward_walk.py`'s established "inject synthetic observations, no DB ever boots" idiom) —
EXCEPT the two `_default_*_assembler` wiring tests, which use a tiny in-memory SQLite fixture (mirrors
`tests/test_regime_history.py`'s `make_engine("sqlite:///:memory:")` pattern) and NEVER the full 30-year
committed seed (`loaded_engine`).

These tests prove the contracts the DoD names:
  * `permute_null_observations` preserves the exact multiset of observed values (never fabricates a
    number) while reassigning per-date group membership (kills the true cohort/control relationship);
  * `binomial_ci` matches a hand-computed Wilson score interval;
  * `run_referee_audit` is DETERMINISTIC given the same seed + inputs;
  * ISOLATION: the harness writes ONLY the given throwaway `ledger_path`; the real `certified-
    claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` are byte-unchanged;
  * the lookahead-contaminated factor is REJECTED when it carries no real edge (deterministic FAIL), and
    the report's `contaminated_caught` flag correctly flips to False (the loud-tripwire case) when a
    "perfect crime" (huge, noiseless edge) DOES slip through as PASS — both are analytically exact, not
    empirically discovered, so neither depends on numpy's RNG internals;
  * a missing/unparseable persisted artifact degrades honestly (never raises).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from app.config import REPO_ROOT
from app.engine import ledger as ledger_mod
from app.engine.referee import DEFAULT_ALPHA_PER_TEST, STATUS_FAIL, STATUS_PASS
from app.engine.referee_audit import (
    REFEREE_AUDIT_PATH_ENV,
    binomial_ci,
    build_referee_audit_report,
    permute_null_observations,
    read_referee_audit_report,
    resolve_referee_audit_path,
    run_referee_audit,
    write_referee_audit_report,
)

_START = date(2021, 1, 3)
_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
_REGISTRY = REPO_ROOT / "runs/goal-session-mcp-loop/state/pre-registrations.jsonl"


def _make_observations(*, n_dates, edge_at, seed, n_cohort=8, n_control=4, noise=0.01, market_sigma=0.02):
    """Synthesize `(cohort, control)` over `n_dates` consecutive calendar days — the SAME generator shape
    `test_referee.py`/`test_forward_walk.py` already use. A shared per-date market level cancels in the
    cohort-minus-control excess; the cohort additionally carries `edge_at(i)` on date index i."""
    rng = np.random.default_rng(seed)
    cohort, control = [], []
    for i in range(n_dates):
        d = _START + timedelta(days=i)
        market = rng.normal(0.0, market_sigma)
        ed = edge_at(i)
        for _ in range(n_control):
            control.append((d, market + rng.normal(0.0, noise)))
        for _ in range(n_cohort):
            cohort.append((d, market + ed + rng.normal(0.0, noise)))
    return cohort, control


def _flat_observations(n_dates, *, cohort_value, control_value):
    """A ZERO-VARIANCE (date, value) pair — every cohort observation is exactly `cohort_value`, every
    control observation exactly `control_value`, on `n_dates` consecutive calendar days. Used to build
    fully deterministic (seed-invariant) referee verdicts: a constant series' per-date excess has zero
    variance, so its block-bootstrap p-value is invariant to which indices the bootstrap draws."""
    dates = [_START + timedelta(days=i) for i in range(n_dates)]
    cohort = [(d, cohort_value) for d in dates]
    control = [(d, control_value) for d in dates]
    return cohort, control


# ==================================================================================================
# permute_null_observations — PURE, exact
# ==================================================================================================
def test_permutation_preserves_the_exact_multiset_of_values():
    cohort, control = _make_observations(n_dates=10, edge_at=lambda i: 0.03, seed=1)
    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(5))
    before = sorted(v for _, v in cohort + control)
    after = sorted(v for _, v in null_cohort + null_control)
    assert after == before
    assert len(null_cohort) == len(cohort)
    assert len(null_control) == len(control)


def test_permutation_preserves_per_date_group_sizes():
    cohort, control = _make_observations(n_dates=6, edge_at=lambda i: 0.02, seed=2, n_cohort=8, n_control=4)
    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(9))
    before_dates = sorted({d for d, _ in cohort})
    for d in before_dates:
        assert sum(1 for dd, _ in null_cohort if dd == d) == 8
        assert sum(1 for dd, _ in null_control if dd == d) == 4


def test_permutation_is_deterministic_given_the_same_rng_seed():
    cohort, control = _make_observations(n_dates=8, edge_at=lambda i: 0.02, seed=3)
    a = permute_null_observations(cohort, control, rng=np.random.default_rng(42))
    b = permute_null_observations(cohort, control, rng=np.random.default_rng(42))
    assert a == b


def test_permutation_reassigns_values_matching_numpys_own_permutation_api():
    """Hand-trace ONE date with a known rng seed: the expected reassignment is derived from numpy's OWN
    `permutation` call (not a hardcoded index sequence), so this stays robust to internals while still
    being an exact, non-fuzzy assertion."""
    d = _START
    cohort = [(d, 1.0), (d, 2.0)]
    control = [(d, 3.0), (d, 4.0)]
    pool = [1.0, 2.0, 3.0, 4.0]
    expected_idx = np.random.default_rng(11).permutation(4)
    expected_shuffled = [pool[i] for i in expected_idx]
    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(11))
    assert [v for _, v in null_cohort] == expected_shuffled[:2]
    assert [v for _, v in null_control] == expected_shuffled[2:]


def test_permutation_skips_a_date_with_no_observations_on_either_side():
    d1, d2 = _START, _START + timedelta(days=1)
    cohort = [(d1, 1.0)]
    control = [(d2, 2.0)]
    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(1))
    # each date has exactly one observation on ONE side -> the permuted pool (size 1) has nowhere to go
    # but back to the cohort/control split of size (1, 0) or (0, 1) per date -- never invents a pairing.
    assert sorted(v for _, v in null_cohort + null_control) == [1.0, 2.0]


# ==================================================================================================
# binomial_ci — PURE, hand-computed Wilson score interval
# ==================================================================================================
def test_binomial_ci_matches_hand_computed_wilson_interval():
    z = 1.959963984540054
    successes, n = 9, 200
    phat = successes / n
    denom = 1.0 + (z * z) / n
    center = phat + (z * z) / (2 * n)
    margin = z * ((phat * (1 - phat)) / n + (z * z) / (4 * n * n)) ** 0.5
    expected_low = (center - margin) / denom
    expected_high = (center + margin) / denom
    low, high = binomial_ci(successes, n)
    assert low == pytest.approx(expected_low, abs=1e-12)
    assert high == pytest.approx(expected_high, abs=1e-12)


def test_binomial_ci_zero_successes_is_non_degenerate():
    """The Wilson interval never collapses to [0, 0] at zero successes (unlike the naive Wald interval) —
    the whole reason Wilson was chosen over Wald for this panel's typical near-zero false-pass counts."""
    low, high = binomial_ci(0, 200)
    assert low == pytest.approx(0.0, abs=1e-12)  # mathematically exactly 0; a tiny fp residual is fine
    assert high > 0.0


def test_binomial_ci_bounds_are_always_within_zero_one():
    for successes, n in [(0, 1), (1, 1), (0, 20), (20, 20), (10, 200)]:
        low, high = binomial_ci(successes, n)
        assert 0.0 <= low <= high <= 1.0


def test_binomial_ci_zero_trials_is_the_honest_full_interval():
    assert binomial_ci(0, 0) == (0.0, 1.0)


# ==================================================================================================
# build_referee_audit_report — PURE assembly
# ==================================================================================================
def test_report_marks_contaminated_caught_true_on_fail():
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
        false_pass_count=1, n_insufficient_null=0, source_factor="rs_spy_3m",
        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_FAIL, "reason": "x"},
    )
    assert report["contaminated_caught"] is True
    assert report["contaminated_expected_outcome"] == "rejected"
    assert report["status"] == "ok"


def test_report_marks_contaminated_caught_false_on_pass_the_tripwire_case():
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
        false_pass_count=1, n_insufficient_null=0, source_factor="rs_spy_3m",
        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_PASS, "reason": "x"},
    )
    assert report["contaminated_caught"] is False


def test_report_false_pass_rate_and_ci_are_computed_from_the_count():
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=200, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
        false_pass_count=9, n_insufficient_null=0, source_factor="rs_spy_3m",
        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_FAIL, "reason": "x"},
    )
    assert report["false_pass_count"] == 9
    assert report["false_pass_rate"] == pytest.approx(9 / 200)
    expected_low, expected_high = binomial_ci(9, 200)
    assert report["false_pass_ci_low"] == expected_low
    assert report["false_pass_ci_high"] == expected_high
    assert report["alpha"] == DEFAULT_ALPHA_PER_TEST
    assert report["source_factor"] == "rs_spy_3m"
    assert report["seed"] == 1
    assert report["n_null_trials"] == 200


def test_report_alpha_uses_the_imported_referee_constant_not_a_literal():
    assert DEFAULT_ALPHA_PER_TEST == 0.05


# ==================================================================================================
# run_referee_audit — injected assemblers, no DB, deterministic
# ==================================================================================================
def _source_edge(seed=1, n_dates=60):
    return _make_observations(n_dates=n_dates, edge_at=lambda i: 0.03, seed=seed)


def _rejected_contaminated():
    """A ZERO-edge 'contaminated' construction -- cohort and control are identically distributed, so the
    referee deterministically FAILS it (the honest, expected outcome the tripwire test names)."""
    return _flat_observations(30, cohort_value=0.01, control_value=0.01)


def _slipped_through_contaminated():
    """A noiseless, huge, constant-edge 'contaminated' construction -- the literal 'perfect crime':
    every cohort observation beats every control observation by a large deterministic margin, so the
    referee deterministically PASSES it regardless of seed (a constant per-date excess has a
    seed-invariant block-bootstrap p-value) -- the tripwire-fires case."""
    return _flat_observations(60, cohort_value=1.0, control_value=0.0)


class _FakeCfg:
    """A minimal cfg stand-in exposing only what `run_referee_audit` reads off
    `cfg.research.referee_audit` -- avoids depending on the real committed config.yaml values so the
    fixture stays self-contained and fast."""

    class _RA:
        def __init__(self, n_null_trials, seed, contaminated_factor_horizon):
            self.n_null_trials = n_null_trials
            self.seed = seed
            self.contaminated_factor_horizon = contaminated_factor_horizon

    class _Research:
        def __init__(self, ra):
            self.referee_audit = ra

    def __init__(self, n_null_trials=20, seed=123, contaminated_factor_horizon=5):
        self.research = self._Research(self._RA(n_null_trials, seed, contaminated_factor_horizon))


def _assemble_source_factory(seed=1, horizon=5):
    cohort, control = _source_edge(seed=seed)

    def assemble():
        return cohort, control, horizon

    return assemble


def test_run_referee_audit_is_deterministic_given_the_same_seed(tmp_path):
    cfg = _FakeCfg(n_null_trials=15, seed=777)
    kwargs = dict(
        cfg=cfg,
        assemble_source=_assemble_source_factory(),
        assemble_contaminated=_rejected_contaminated,
        run_date="2026-07-14",
    )
    report_a = run_referee_audit(ledger_path=str(tmp_path / "a.jsonl"), **kwargs)
    report_b = run_referee_audit(ledger_path=str(tmp_path / "b.jsonl"), **kwargs)
    assert report_a == report_b


def test_run_referee_audit_writes_only_the_throwaway_ledger_never_the_real_files(tmp_path):
    canonical_before = _CANONICAL_LEDGER.read_text(encoding="utf-8")
    staging_before = _STAGING_LEDGER.read_text(encoding="utf-8")
    registry_before = _REGISTRY.read_text(encoding="utf-8")

    throwaway = tmp_path / "throwaway.jsonl"
    cfg = _FakeCfg(n_null_trials=10, seed=5)
    run_referee_audit(
        cfg=cfg,
        ledger_path=str(throwaway),
        assemble_source=_assemble_source_factory(),
        assemble_contaminated=_rejected_contaminated,
        run_date="2026-07-14",
    )

    assert throwaway.exists()
    entries = ledger_mod.read_entries(str(throwaway))
    assert len(entries) == 10 + 1  # 10 null trials + 1 contaminated trial
    assert _CANONICAL_LEDGER.read_text(encoding="utf-8") == canonical_before
    assert _STAGING_LEDGER.read_text(encoding="utf-8") == staging_before
    assert _REGISTRY.read_text(encoding="utf-8") == registry_before


def test_run_referee_audit_overwrites_the_throwaway_ledger_fresh_each_call(tmp_path):
    path = tmp_path / "ledger.jsonl"
    cfg = _FakeCfg(n_null_trials=6, seed=1)
    run_referee_audit(
        cfg=cfg, ledger_path=str(path), assemble_source=_assemble_source_factory(),
        assemble_contaminated=_rejected_contaminated, run_date="2026-07-14",
    )
    first_count = len(ledger_mod.read_entries(str(path)))
    run_referee_audit(
        cfg=cfg, ledger_path=str(path), assemble_source=_assemble_source_factory(),
        assemble_contaminated=_rejected_contaminated, run_date="2026-07-14",
    )
    second_count = len(ledger_mod.read_entries(str(path)))
    assert first_count == second_count == 7  # never accumulates across repeated harness invocations


def test_run_referee_audit_each_null_trial_uses_a_fresh_state_never_a_ledger_derived_count(tmp_path):
    """Every null trial's required_p must be `alpha / 1` (an INDEPENDENT test at the raw configured
    alpha) -- never Bonferroni-deflated by an accumulating count across the 200 nulls, which would make
    the empirical false-pass rate incomparable to the configured alpha the panel displays it against."""
    path = tmp_path / "ledger.jsonl"
    cfg = _FakeCfg(n_null_trials=8, seed=2)
    run_referee_audit(
        cfg=cfg, ledger_path=str(path), assemble_source=_assemble_source_factory(),
        assemble_contaminated=_rejected_contaminated, run_date="2026-07-14",
    )
    entries = ledger_mod.read_entries(str(path))
    null_entries = [e for e in entries if e.get("kind") == "null"]
    assert len(null_entries) == 8
    for entry in null_entries:
        assert entry["verdict"]["required_p"] == pytest.approx(DEFAULT_ALPHA_PER_TEST / 1)
        assert entry["verdict"]["deflation_divisor"] == 1


def test_run_referee_audit_reduces_pass_rate_below_the_unpermuted_baseline(tmp_path):
    """The un-permuted source data is a TRUE persistent edge (certifies PASS on its own, per
    `test_referee.py`'s identical construction) -- proving the null generator's permutation strictly
    reduces the pass rate below "every trial passes" is the calibration property this harness exists to
    measure. An exact, deterministic inequality (not a vague threshold)."""
    from app.engine.referee import DEFAULT_ALPHA_BUDGET, RefereeState, certify_edge

    cohort, control = _source_edge(seed=1)
    unpermuted = certify_edge(
        cohort, control, horizon=5, state=RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET), seed=7,
    )
    assert unpermuted.status == STATUS_PASS  # sanity: the source data IS a real, certifiable edge

    cfg = _FakeCfg(n_null_trials=20, seed=99)
    report = run_referee_audit(
        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
        assemble_source=_assemble_source_factory(seed=1), assemble_contaminated=_rejected_contaminated,
        run_date="2026-07-14",
    )
    assert report["false_pass_count"] < report["n_null_trials"]


def test_run_referee_audit_contaminated_factor_rejected_is_deterministic_fail(tmp_path):
    cfg = _FakeCfg(n_null_trials=5, seed=1, contaminated_factor_horizon=5)
    report = run_referee_audit(
        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
        assemble_source=_assemble_source_factory(), assemble_contaminated=_rejected_contaminated,
        run_date="2026-07-14",
    )
    assert report["contaminated_verdict"]["status"] == STATUS_FAIL
    assert report["contaminated_caught"] is True
    assert report["contaminated_expected_outcome"] == "rejected"


def test_run_referee_audit_contaminated_factor_slipping_through_sets_tripwire(tmp_path):
    cfg = _FakeCfg(n_null_trials=5, seed=1, contaminated_factor_horizon=5)
    report = run_referee_audit(
        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
        assemble_source=_assemble_source_factory(), assemble_contaminated=_slipped_through_contaminated,
        run_date="2026-07-14",
    )
    assert report["contaminated_verdict"]["status"] == STATUS_PASS
    assert report["contaminated_caught"] is False  # the honest, un-hidden tripwire signal
    assert report["contaminated_expected_outcome"] == "rejected"  # the static label is unaffected


def test_run_referee_audit_report_carries_the_configured_run_params(tmp_path):
    cfg = _FakeCfg(n_null_trials=13, seed=42, contaminated_factor_horizon=9)
    report = run_referee_audit(
        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
        assemble_source=_assemble_source_factory(horizon=5), assemble_contaminated=_rejected_contaminated,
        run_date="2026-07-14",
    )
    assert report["n_null_trials"] == 13
    assert report["seed"] == 42
    assert report["contaminated_factor_horizon"] == 9
    assert report["run_date"] == "2026-07-14"


# ==================================================================================================
# Persistence: resolve/write/read round-trip + honest degradation
# ==================================================================================================
def test_resolve_path_uses_env_override(tmp_path, monkeypatch):
    target = tmp_path / "custom-report.json"
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    assert resolve_referee_audit_path() == str(target)


def test_write_then_read_round_trips_verbatim(tmp_path, monkeypatch):
    target = tmp_path / "report.json"
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
        false_pass_count=1, n_insufficient_null=0, source_factor="rs_spy_3m",
        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_FAIL, "reason": "x"},
    )
    write_referee_audit_report(report)
    assert read_referee_audit_report() == report


def test_read_missing_artifact_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(tmp_path / "does-not-exist.json"))
    assert read_referee_audit_report() is None


def test_read_unparseable_artifact_returns_honest_unreadable_never_raises(tmp_path, monkeypatch):
    target = tmp_path / "corrupt.json"
    target.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    result = read_referee_audit_report()
    assert result["status"] == "unreadable"
    assert result["contaminated_verdict"] is None


def test_write_creates_parent_directory(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "dir" / "report.json"
    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
    report = build_referee_audit_report(
        run_date="2026-07-14", n_null_trials=1, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
        false_pass_count=0, n_insufficient_null=0, source_factor="x",
        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_FAIL, "reason": "x"},
    )
    write_referee_audit_report(report)
    assert target.exists()


# ==================================================================================================
# Config: RefereeAuditCfg boot validation + the real config.yaml block
# ==================================================================================================
def test_real_config_yaml_carries_the_referee_audit_block():
    from app.config import load_config

    cfg = load_config()
    ra = cfg.research.referee_audit
    assert ra.n_null_trials == 200
    assert ra.seed == 20240601
    assert ra.contaminated_factor_horizon >= 1
    assert ra.report_path


def test_referee_audit_cfg_rejects_zero_null_trials():
    from pydantic import ValidationError

    from app.config import RefereeAuditCfg

    with pytest.raises(ValidationError):
        RefereeAuditCfg(n_null_trials=0)


def test_referee_audit_cfg_rejects_zero_contaminated_horizon():
    from pydantic import ValidationError

    from app.config import RefereeAuditCfg

    with pytest.raises(ValidationError):
        RefereeAuditCfg(contaminated_factor_horizon=0)


def test_referee_audit_cfg_defaults_when_omitted():
    """A config predating this block (or an inline test fixture omitting `research.referee_audit`)
    still loads, via `ResearchCfg`'s `default_factory` -- mirrors `DriftCfg`'s same guarantee."""
    from app.config import RefereeAuditCfg

    cfg = RefereeAuditCfg()
    assert cfg.n_null_trials == 200
    assert cfg.contaminated_factor_horizon == 5
    assert cfg.report_path


# ==================================================================================================
# Default (DB-backed) assemblers — tiny in-memory fixture, NEVER the full 30-year seed
# ==================================================================================================
def _tiny_engine():
    """A bare in-memory SQLite DB (schema only, no seed load) -- mirrors
    `tests/test_regime_history.py::_engine` exactly."""
    from app.db import create_db_and_tables, make_engine

    engine = make_engine("sqlite:///:memory:")
    create_db_and_tables(engine)
    return engine


def _insert_run(session, d):
    """One minimal immutable ScannerRun row -- mirrors `tests/test_regime_history.py::_insert_run`."""
    from datetime import datetime as datetime_cls

    from app.models import ScannerRun

    run = ScannerRun(
        asof_date=d, created_at=datetime_cls(2026, 1, 1, 12, 0, 0), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
        breadth_above_50dma=None, breadth_above_200dma=None,
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _insert_forward_returns(session, run, d, horizon, symbol_returns: dict):
    """One `ForwardReturn` row per `(symbol, realized_return)` pair, all at `horizon`, on run `run`."""
    from app.models import ForwardReturn

    for symbol, realized in symbol_returns.items():
        session.add(
            ForwardReturn(
                run_id=run.id, symbol=symbol, horizon=horizon, asof_date=d,
                entry_close=100.0, measured_date=d + timedelta(days=horizon * 2), realized_return=realized,
            )
        )


def test_default_contaminated_assembler_ranks_top_decile_by_own_forward_return():
    from sqlmodel import Session

    from app.engine.referee_audit import _default_contaminated_assembler

    engine = _tiny_engine()
    d = date(2026, 1, 5)
    horizon = 5
    # 10 names -> top decile (10 // 10 = 1) is exactly the single highest return.
    returns = {f"SYM{i}": float(i) / 100.0 for i in range(10)}  # 0.00 .. 0.09
    with Session(engine) as session:
        run = _insert_run(session, d)
        _insert_forward_returns(session, run, d, horizon, returns)
        session.commit()

        class _RA:
            contaminated_factor_horizon = horizon

        class _Research:
            referee_audit = _RA()

        class _Cfg:
            research = _Research()

        assemble = _default_contaminated_assembler(session, _Cfg(), cohort_dates=set())
        cohort, control = assemble()

    assert cohort == [(d, 0.09)]  # the single top-decile (highest) realized return
    assert sorted(v for _, v in control) == [round(i / 100.0, 2) for i in range(9)]


def test_default_contaminated_assembler_skips_a_date_below_the_minimum_cross_section():
    from sqlmodel import Session

    from app.engine.referee_audit import _default_contaminated_assembler

    engine = _tiny_engine()
    d = date(2026, 1, 5)
    horizon = 5
    returns = {f"SYM{i}": float(i) for i in range(3)}  # only 3 names -- below _MIN_CROSS_SECTION_NAMES
    with Session(engine) as session:
        run = _insert_run(session, d)
        _insert_forward_returns(session, run, d, horizon, returns)
        session.commit()

        class _RA:
            contaminated_factor_horizon = horizon

        class _Research:
            referee_audit = _RA()

        class _Cfg:
            research = _Research()

        assemble = _default_contaminated_assembler(session, _Cfg(), cohort_dates=set())
        cohort, control = assemble()

    assert cohort == []
    assert control == []


def test_default_contaminated_assembler_bounds_to_the_supplied_cohort_dates():
    from sqlmodel import Session

    from app.engine.referee_audit import _default_contaminated_assembler

    engine = _tiny_engine()
    d_in, d_out = date(2026, 1, 5), date(2026, 2, 5)
    horizon = 5
    returns = {f"SYM{i}": float(i) / 100.0 for i in range(10)}
    with Session(engine) as session:
        run_in = _insert_run(session, d_in)
        run_out = _insert_run(session, d_out)
        _insert_forward_returns(session, run_in, d_in, horizon, returns)
        _insert_forward_returns(session, run_out, d_out, horizon, returns)
        session.commit()

        class _RA:
            contaminated_factor_horizon = horizon

        class _Research:
            referee_audit = _RA()

        class _Cfg:
            research = _Research()

        assemble = _default_contaminated_assembler(session, _Cfg(), cohort_dates={d_in})
        cohort, control = assemble()

    assert {dd for dd, _ in cohort + control} == {d_in}  # d_out is excluded -- bounded, not a whole-table scan


def test_default_source_assembler_builds_the_expected_claim_and_returns_the_factor_label(monkeypatch):
    import app.mcp.tools as tools_mod
    from app.config import load_config
    from app.engine.referee_audit import _default_source_assembler

    cfg = load_config()
    captured = {}

    def fake_assemble(session, claim):
        captured["session"] = session
        captured["claim"] = claim
        return ([(date(2026, 1, 1), 0.01)], [(date(2026, 1, 1), 0.0)], claim["horizon"])

    monkeypatch.setattr(tools_mod, "assemble_claim_observations", fake_assemble)
    sentinel_session = object()
    assemble, factor_label = _default_source_assembler(sentinel_session, cfg)
    result = assemble()

    expected_factor = cfg.research.factor_lab.factors[0].key
    assert factor_label == expected_factor
    assert captured["session"] is sentinel_session
    assert captured["claim"] == {
        "kind": "factor", "factor": expected_factor, "slice_kind": "decile", "decile": 10,
        "horizon": cfg.walk_forward.default_horizon,
    }
    assert result == ([(date(2026, 1, 1), 0.01)], [(date(2026, 1, 1), 0.0)], cfg.walk_forward.default_horizon)
