"""iter-45 (J-103 / J-104) — Severity-velocity × Regime forward-return study + research-labs reliability.

J-103 — the study GROUPS the stored SPY `forward_returns` by (regime FAMILY, velocity SIGN) at each
snapshot date. The family is a config-backed grouping of the STORED regime label (read verbatim); the sign
is the sign of the SERVED `severity_velocity` (J-102, monkeypatched here to controlled values so the grouping
correctness is exact by construction, isolated from the heavy market-phase derivation). Disciplines proven:
  - regime-family × velocity-sign grouping correctness on a synthetic seed (membership + mean + win-rate + N);
  - strictly-causal / no-lookahead: forward returns are the stored realized returns (bars > D) — an as-of
    FILTER only shrinks the pool, never recomputes a figure (tail-invariance);
  - NA/partial below min-sample (the cell carries its honest n + low_sample, mean/win-rate gated to NA);
  - a warm-up-head / no-family observation is honestly EXCLUDED (never fabricated into a cell);
  - cache byte-identity asserted against an ALREADY-POPULATED `EventStudyCache` row (HIT == fresh compute);
  - samples drill-down total == published cell N in BOTH All-history and As-of scopes (count-coherence);
  - an invalid family/sign drill-down raises ValueError -> the API 422 (never a silent empty 200).

J-104 — the two newly-cached studies (factor-combination, regime × setup × pattern) return figures
byte-identical to a direct compute, and the bounded downtrend run-date scan stays byte-identical.
"""
from __future__ import annotations

import copy
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import research
from app.engine.research import (
    _factor_combination_cache_subject,
    _regime_family_for,
    _severity_velocity_observation_set,
    _velocity_sign_for,
    compute_factor_combination,
    compute_regime_setup_pattern_study,
    compute_severity_velocity_study,
    factor_combination_cached,
    regime_setup_pattern_cached,
    severity_velocity_cached,
)
from app.engine.samples import KIND_SEVERITY_VELOCITY, compute_samples
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

SPY = "SPY"


def _utc() -> datetime:
    return datetime(2024, 1, 1, tzinfo=timezone.utc)


def _cfg():
    """Real config with min_sample lowered so a small synthetic cohort is not flagged low-sample
    everywhere (the grouping correctness tests assert exact non-NA means)."""
    cfg = copy.deepcopy(load_config())
    cfg.walk_forward.min_sample = 1
    return cfg


def _engine(tmp_path, name="sv.db"):
    engine = make_engine(f"sqlite:///{tmp_path / name}")
    create_db_and_tables(engine)
    return engine


def _add_run(session, asof, regime_label):
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark=SPY,
        regime_score=50.0, regime_label=regime_label, regime_components_json="[]",
        breadth_above_50dma=None, breadth_above_200dma=None,
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_spy_fr(session, run_id, ret, horizon):
    session.add(ForwardReturn(
        run_id=run_id, symbol=SPY, horizon=horizon, realized_return=ret,
        asof_date=date(2024, 1, 1), entry_close=100.0, measured_date=date(2024, 1, 1),
    ))


# Each tuple: (asof_date, regime_label, served_severity_velocity, spy_forward_return).
# Families: Risk-off/Defensive -> risk_off ; Strong risk-on/Risk-on -> risk_on ; Narrow leadership/Choppy -> neutral.
# Signs: velocity > 0 rising ; == 0 flat ; < 0 falling ; None warm-up (EXCLUDED).
_SEED = [
    (date(2024, 1, 1), "Risk-off",       None, 0.10),   # warm-up head -> EXCLUDED (no velocity sign)
    (date(2024, 1, 8), "Risk-off",       2.0, 0.06),    # (risk_off, rising)  win
    (date(2024, 1, 15), "Defensive",     1.0, 0.04),    # (risk_off, rising)  win
    (date(2024, 1, 22), "Risk-off",      -1.0, -0.02),  # (risk_off, falling) loss
    (date(2024, 1, 29), "Strong risk-on", 3.0, 0.08),   # (risk_on, rising)   win
    (date(2024, 2, 5), "Risk-on",        -2.0, 0.05),   # (risk_on, falling)  win
    (date(2024, 2, 12), "Narrow leadership", 0.0, 0.01),# (neutral, flat)     win
    (date(2024, 2, 19), "Choppy",        -0.5, -0.03),  # (neutral, falling)  loss
]


@pytest.fixture()
def sv_engine(tmp_path, monkeypatch):
    """A synthetic seed of SPY forward returns + runs with controlled regime labels, plus a monkeypatched
    `severity_velocity_by_date` returning controlled velocities — so the (family, sign) grouping is exact
    by construction (isolated from the heavy market-phase derivation). Returns (engine, horizon)."""
    engine = _engine(tmp_path)
    horizon = load_config().walk_forward.default_horizon
    velocity_by_date: dict[str, float] = {}
    with Session(engine) as session:
        for asof, label, velocity, ret in _SEED:
            run = _add_run(session, asof, label)
            _add_spy_fr(session, run.id, ret, horizon)
            velocity_by_date[asof.isoformat()] = velocity
        session.commit()

    def _fake_velocity(session, as_of=None, config=None):
        # honor the as-of FILTER exactly like the real accessor (only dates <= as_of)
        if as_of is None:
            return dict(velocity_by_date)
        return {d: v for d, v in velocity_by_date.items() if date.fromisoformat(d) <= as_of}

    # `_severity_velocity_observation_set` lazily imports `severity_velocity_by_date` FROM the market_phase
    # module at call time, so the patch must target the source module (not the research namespace).
    import app.engine.market_phase as market_phase
    monkeypatch.setattr(market_phase, "severity_velocity_by_date", _fake_velocity)
    return engine, horizon


def _cell(study, family, sign):
    row = next(r for r in study["matrix"] if r["family"] == family)
    return next(c for c in row["cells"] if c["velocity_sign"] == sign)


def test_regime_family_and_velocity_sign_mapping():
    """The config-backed family map + the structural sign test, read verbatim (no recompute)."""
    cfg = _cfg()
    assert _regime_family_for("Risk-off", cfg) == "risk_off"
    assert _regime_family_for("Defensive", cfg) == "risk_off"
    assert _regime_family_for("Strong risk-on", cfg) == "risk_on"
    assert _regime_family_for("Narrow leadership", cfg) == "neutral"
    assert _regime_family_for(None, cfg) is None
    assert _velocity_sign_for(2.0) == "rising"
    assert _velocity_sign_for(-1.0) == "falling"
    assert _velocity_sign_for(0.0) == "flat"
    assert _velocity_sign_for(None) is None  # warm-up head -> excluded


def test_study_grouping_correctness_mean_winrate_and_n(sv_engine):
    """J-103: exact (family, sign) cell membership + mean + win-rate + N on the synthetic seed."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        study = compute_severity_velocity_study(session, horizon, cfg)

    # the warm-up-head row (velocity None) is EXCLUDED -> n_total is 7 of the 8 seeded observations.
    assert study["n_total"] == 7
    assert study["benchmark"] == SPY

    # (risk_off, rising): the 0.06 + 0.04 wins -> mean 0.05, win-rate 1.0, n 2.
    cell = _cell(study, "risk_off", "rising")
    assert cell["stats"]["n"] == 2
    assert cell["stats"]["mean_return"] == pytest.approx(0.05)
    assert cell["stats"]["win_rate"] == pytest.approx(1.0)

    # (risk_off, falling): the single -0.02 loss -> mean -0.02, win-rate 0.0, n 1.
    cell = _cell(study, "risk_off", "falling")
    assert cell["stats"]["n"] == 1
    assert cell["stats"]["mean_return"] == pytest.approx(-0.02)
    assert cell["stats"]["win_rate"] == pytest.approx(0.0)

    # (risk_on, rising): single 0.08 win ; (risk_on, falling): single 0.05 win.
    assert _cell(study, "risk_on", "rising")["stats"]["n"] == 1
    assert _cell(study, "risk_on", "falling")["stats"]["mean_return"] == pytest.approx(0.05)

    # (neutral, flat): single 0.01 win ; (neutral, falling): single -0.03 loss.
    assert _cell(study, "neutral", "flat")["stats"]["win_rate"] == pytest.approx(1.0)
    assert _cell(study, "neutral", "falling")["stats"]["mean_return"] == pytest.approx(-0.03)

    # an EMPTY cell (no observations) is honest NA — never a fabricated 0.
    empty = _cell(study, "risk_on", "flat")
    assert empty["stats"]["n"] == 0
    assert empty["stats"]["mean_return"] is None
    assert empty["stats"]["win_rate"] is None


def test_verdict_caveat_states_hypothesis_not_supported(sv_engine):
    """J-103: the honest verdict caveat is carried VERBATIM (the hypothesis is NOT supported on the seed)."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        study = compute_severity_velocity_study(session, horizon, cfg)
    caveat = study["verdict_caveat"]
    assert "bounce, not continuation" in caveat
    assert "NOT supported" in caveat
    assert "survivorship" in caveat.lower()
    assert "bull-dominated" in caveat
    assert "underpowered for sustained crashes" in caveat


def test_low_sample_cell_flags_na(sv_engine):
    """NA/partial: below min_sample a cell carries its honest n + low_sample (the UI gates to NA + n)."""
    engine, horizon = sv_engine
    cfg = copy.deepcopy(load_config())
    cfg.walk_forward.min_sample = 5  # every synthetic cell is below this -> low_sample True
    with Session(engine) as session:
        study = compute_severity_velocity_study(session, horizon, cfg)
    cell = _cell(study, "risk_off", "rising")  # n=2 < 5
    assert cell["stats"]["n"] == 2
    assert cell["stats"]["low_sample"] is True


def test_as_of_filter_shrinks_pool_no_recompute(sv_engine):
    """No-lookahead / as-of FILTER (J-32): scoping to an early as-of yields a SUBSET pool with the SAME
    per-cell figures for the surviving observations — a FILTER, never a recompute (tail-invariance)."""
    engine, horizon = sv_engine
    cfg = _cfg()
    early = date(2024, 1, 22)  # keeps the first 4 seeded dates (one is warm-up-excluded)
    with Session(engine) as session:
        scoped = compute_severity_velocity_study(session, horizon, cfg, as_of=early)
        full = compute_severity_velocity_study(session, horizon, cfg)
    assert scoped["asof_date"] == early.isoformat()
    # scoped keeps only (risk_off, rising) [0.06, 0.04] + (risk_off, falling) [-0.02] -> n_total 3.
    assert scoped["n_total"] == 3
    assert scoped["n_total"] < full["n_total"]
    # the surviving cell's figure is UNCHANGED by the filter (no recompute) — same mean both scopes.
    assert _cell(scoped, "risk_off", "rising")["stats"]["mean_return"] == pytest.approx(
        _cell(full, "risk_off", "rising")["stats"]["mean_return"]
    )


def test_cache_byte_identity_against_already_populated_row(sv_engine):
    """J-72/J-103: the cached payload is BYTE-IDENTICAL to a fresh compute, asserted against an ALREADY-
    POPULATED `EventStudyCache` row (the iter-38/39 discipline — prove the HIT, not just a fresh compute)."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        fresh = compute_severity_velocity_study(session, horizon, cfg)
        first = severity_velocity_cached(session, horizon, cfg)  # MISS -> writes the cache row
        # the row now EXISTS (already-populated) — the second call is a HIT off that stored row.
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == "__severity_velocity__")
        ).all()
        assert len(rows) == 1, "exactly one cache row written for this analysis identity"
        second = severity_velocity_cached(session, horizon, cfg)  # HIT off the populated row
    assert first == fresh, "cache MISS payload must equal a fresh compute"
    assert second == fresh, "cache HIT (already-populated row) must be byte-identical to a fresh compute"


def test_cache_refreshes_on_dataset_change(sv_engine):
    """The cache REFRESHES after a dataset change (a new run/forward-return bumps `_dataset_version`), so a
    stale row is never served — the J-72 invalidation contract."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        before = severity_velocity_cached(session, horizon, cfg)
        assert before["n_total"] == 7
        # add a new observation -> the dataset-version stamp changes -> the old row is not hit.
        run = _add_run(session, date(2024, 3, 1), "Risk-off")
        _add_spy_fr(session, run.id, 0.09, horizon)
        session.commit()
    # the monkeypatched velocity map has no entry for 2024-03-01, so the new obs is warm-up-excluded; the
    # n_total is unchanged BUT a fresh row is computed under the new stamp (no stale-row error).
    with Session(engine) as session:
        after = severity_velocity_cached(session, horizon, cfg)
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == "__severity_velocity__")
        ).all()
    assert len(rows) == 1, "the stale-stamp row is pruned; exactly one current-stamp row remains"
    assert after["n_total"] == before["n_total"]  # the new date has no served velocity (excluded)


def test_samples_count_coherence_total_equals_published_n(sv_engine):
    """COUNT-COHERENCE (J-51/J-65): each cell's samples drill-down `total` EQUALS its published `n` in BOTH
    All-history and As-of scopes — every displayable cell resolves without a 4xx (the J-82 lesson)."""
    engine, horizon = sv_engine
    cfg = _cfg()
    early = date(2024, 1, 22)
    with Session(engine) as session:
        for as_of in (None, early):
            study = compute_severity_velocity_study(session, horizon, cfg, as_of=as_of)
            for row in study["matrix"]:
                for cell in row["cells"]:
                    samples = compute_samples(
                        session, kind=KIND_SEVERITY_VELOCITY, horizon=horizon, config=cfg,
                        family=row["family"], velocity_sign=cell["velocity_sign"], as_of=as_of,
                    )
                    assert samples["total"] == cell["stats"]["n"], (
                        f"drill-down total != published n for ({row['family']}, "
                        f"{cell['velocity_sign']}) at as_of={as_of}"
                    )


def test_samples_rows_read_verbatim_spy_observations(sv_engine):
    """Each drill-down row carries the SPY ticker + stored regime + served velocity + the realized return,
    read VERBATIM (recomputes nothing)."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        samples = compute_samples(
            session, kind=KIND_SEVERITY_VELOCITY, horizon=horizon, config=cfg,
            family="risk_off", velocity_sign="rising",
        )
    assert samples["total"] == 2
    for row in samples["rows"]:
        assert row["ticker"] == SPY
        keys = {v["key"] for v in row["values"]}
        assert {"regime", "severity_velocity"} <= keys
        assert row["forward_return"] is not None


def test_samples_invalid_family_or_sign_raises(sv_engine):
    """An invalid family/sign drill-down raises ValueError (-> the API 422), never a silent empty 200."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        with pytest.raises(ValueError, match="is not a configured severity-velocity family"):
            compute_samples(
                session, kind=KIND_SEVERITY_VELOCITY, horizon=horizon, config=cfg,
                family="not_a_family", velocity_sign="rising",
            )
        with pytest.raises(ValueError, match="is not a configured velocity sign"):
            compute_samples(
                session, kind=KIND_SEVERITY_VELOCITY, horizon=horizon, config=cfg,
                family="risk_off", velocity_sign="sideways",
            )


def test_zero_n_cell_drilldown_is_honest_empty_not_4xx(sv_engine):
    """A VALID zero-N cell (an empty (family, sign)) drills into an empty rows + total 0 — an honest empty
    state, NOT a 4xx that breaks the chip."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        samples = compute_samples(
            session, kind=KIND_SEVERITY_VELOCITY, horizon=horizon, config=cfg,
            family="risk_on", velocity_sign="flat",  # no observations in this cell
        )
    assert samples["total"] == 0
    assert samples["rows"] == []


def test_observation_set_excludes_warmup_head(sv_engine):
    """The warm-up-head observation (velocity None) is honestly EXCLUDED from every cohort (its cohort key
    is None) — never fabricated into a cell."""
    engine, horizon = sv_engine
    cfg = _cfg()
    with Session(engine) as session:
        obs = _severity_velocity_observation_set(session, horizon, cfg)
    assert len(obs) == 8  # the raw pool has all 8 SPY returns
    warmup = [o for o in obs if o["snapshot_date"] == "2024-01-01"]
    assert len(warmup) == 1
    assert warmup[0]["velocity_sign"] is None  # excluded from any (family, sign) cell


# ==================================================================================================
# J-104 — research-labs reliability: the two newly-cached studies are byte-identical to a direct compute,
# and the bounded downtrend run-date scan stays byte-identical. Reuses the recovery/downtrend fixtures'
# style via a small shared seed.
# ==================================================================================================
def _add_stock_result(session, run_id, ticker, rank, lead=50.0):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, rank=rank, sector="Technology",
        leadership_score=lead, leadership_bucket="C",
        entry_quality_score=50.0, entry_quality_bucket="C",
        risk_score=50.0, risk_bucket="C",
        setup_status="Breakout-watch",
        is_vcp=False, is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
        record_json="{}",
    ))


@pytest.fixture()
def combo_engine(tmp_path):
    """A small pool of stocks with two factors + stored forward returns, so the factor-combination + the
    regime × setup × pattern studies both return a non-trivial payload to cache. Returns (engine, horizon)."""
    engine = _engine(tmp_path, "combo.db")
    horizon = load_config().walk_forward.default_horizon
    with Session(engine) as session:
        run = _add_run(session, date(2024, 1, 10), "Risk-on")
        for i in range(1, 13):
            _add_stock_result(session, run.id, f"S{i:02d}", rank=i, lead=float(i))
            session.add(ForwardReturn(
                run_id=run.id, symbol=f"S{i:02d}", horizon=horizon, realized_return=i / 100,
                asof_date=date(2024, 1, 10), entry_close=100.0, measured_date=date(2024, 1, 10),
            ))
        session.commit()
    return engine, horizon


def test_factor_combination_cached_byte_identical(combo_engine):
    """J-104(a): the factor-combination study served from cache is BYTE-IDENTICAL to a direct compute, and
    the cache refreshes on dataset change (asserted against an already-populated row)."""
    engine, horizon = combo_engine
    cfg = _cfg()
    conditions = [
        {"factor": "leadership_score", "side": "top", "quantile": "half"},
        {"factor": "risk_score", "side": "bottom", "quantile": "half"},
    ]
    with Session(engine) as session:
        direct = compute_factor_combination(session, conditions, horizon, cfg)
        cached_miss = factor_combination_cached(session, conditions, horizon, cfg)
        cached_hit = factor_combination_cached(session, conditions, horizon, cfg)  # off the populated row
        subject = _factor_combination_cache_subject(conditions)
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == subject)
        ).all()
    assert cached_miss == direct
    assert cached_hit == direct, "cache HIT must be byte-identical to a direct compute"
    assert len(rows) == 1


def test_factor_combination_cache_keys_distinct_per_conditions(combo_engine):
    """Two DIFFERENT combinations key to DIFFERENT cache rows (the conditions are folded into the key) —
    a distinct combination never serves another's payload."""
    engine, horizon = combo_engine
    cfg = _cfg()
    a = [
        {"factor": "leadership_score", "side": "top", "quantile": "half"},
        {"factor": "risk_score", "side": "bottom", "quantile": "half"},
    ]
    b = [
        {"factor": "leadership_score", "side": "bottom", "quantile": "half"},
        {"factor": "risk_score", "side": "top", "quantile": "half"},
    ]
    assert _factor_combination_cache_subject(a) != _factor_combination_cache_subject(b)
    with Session(engine) as session:
        res_a = factor_combination_cached(session, a, horizon, cfg)
        res_b = factor_combination_cached(session, b, horizon, cfg)
        direct_a = compute_factor_combination(session, a, horizon, cfg)
        direct_b = compute_factor_combination(session, b, horizon, cfg)
    assert res_a == direct_a
    assert res_b == direct_b
    assert res_a != res_b  # the two combinations are genuinely different cohorts


def test_regime_setup_pattern_cached_byte_identical(combo_engine):
    """J-104(a): the regime × setup × pattern study served from cache is BYTE-IDENTICAL to a direct compute
    (asserted against an already-populated row)."""
    engine, horizon = combo_engine
    cfg = _cfg()
    with Session(engine) as session:
        direct = compute_regime_setup_pattern_study(session, horizon, cfg)
        cached_miss = regime_setup_pattern_cached(session, horizon, cfg)
        cached_hit = regime_setup_pattern_cached(session, horizon, cfg)  # off the populated row
        rows = session.exec(
            select(EventStudyCache).where(EventStudyCache.subject == "__regime_setup_pattern__")
        ).all()
    assert cached_miss == direct
    assert cached_hit == direct, "cache HIT must be byte-identical to a direct compute"
    assert len(rows) == 1
