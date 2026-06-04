"""Factor Lab research engine (iter-10, J-25) — read-only decile sort + downside risk-adjusted + rank-IC.

Named proofs, each guarding an anti-goal:
  - read-only keystone (patch-to-raise) — scoring/return/pattern math raising does NOT break the lab. *(Research lab is read-only)*
  - decile math exact            — membership / mean_return / n on a hand fixture; monotone factor -> monotone means.
  - rank-IC exact                — Spearman 1.0 / -1.0 / a known mixed value / NA on n<2 or zero variance.
  - risk-adjusted is downside    — symmetric cohort uses the downside leg only; all-non-negative -> NA (not total vol). *(Risk-adjusted honest)*
  - NA honesty                   — factor-NULL excluded; low-sample flag; all-NA factor -> n=0 / no fabricated rows. *(No fabricated data)*
  - consistency invariant        — pooled lab mean == compute_forward_aggregates.overall.mean_return (same stored pool). *(No recompute in the read path)*
  - config-driven / no magic #s  — deciles + catalog from config; a config-only factor appears with no code change; bad config -> ConfigError.

All math runs on tiny hand-built in-memory data (fast) — the lab READS stored rows, so no engine run is needed.
"""
from __future__ import annotations

import copy
import json
from datetime import date, datetime, timezone

import pytest
import yaml
from sqlmodel import Session

from app.config import ConfigError, load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import compute_forward_aggregates
from app.engine.research import (
    RESEARCH_CAVEAT,
    _average_ranks,
    _downside_deviation,
    _factor_observations,
    _quantile_cutoff,
    _rank_ic,
    _risk_adjusted,
    compute_event_study,
    compute_factor_combination,
    compute_factor_lab,
    factor_catalog,
    subject_catalog,
)
from app.models import ForwardReturn, ScannerResult, ScannerRun
from test_config import MINIMAL_VALID, _write

H = 20  # a real config horizon used throughout the hand fixtures


# ==================================================================================================
# Hand-built snapshot fixtures (no engine — exact values by construction)
# ==================================================================================================
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str = "Risk-on") -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label=regime_label, regime_components_json="[]",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _component_record(block: str, name: str, raw):
    """A minimal `record_json` carrying ONE named component `raw` under `<block>.components` — the exact
    shape `score_stocks` persists (components is a LIST of {name, raw, available, …} dicts)."""
    return json.dumps({
        block: {"components": [{"name": name, "raw": raw, "available": raw is not None}]}
    })


def _add_result(
    session, run_id, ticker, rank, *, lead=50.0, entry=50.0, risk=50.0, sector="Technology",
    bucket="C", setup="Breakout-watch", record_json="{}",
    hv=None, vcp_contraction=None, downside_vol=None,
    is_vcp=False, is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=lead, leadership_bucket=bucket,
        entry_quality_score=entry, entry_quality_bucket=bucket,
        risk_score=risk, risk_bucket=bucket,
        setup_status=setup, rank=rank, record_json=record_json,
        hv=hv, vcp_contraction=vcp_contraction, downside_vol=downside_vol,  # iter-13 volatility columns
        is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback_to_rising_dma,  # iter-14 event-study cohorts
        is_flat_base_breakout=is_flat_base_breakout,
    ))


def _add_fr(session, run_id, symbol, ret, horizon=H, mae=None, mfe=None):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret,
        mae=mae, mfe=mfe,  # iter-14 stored excursions (read verbatim by the event study)
    ))


def _engine(tmp_path, name="research.db"):
    engine = make_engine(f"sqlite:///{tmp_path / name}")
    create_db_and_tables(engine)
    return engine


@pytest.fixture()
def monotone_engine(tmp_path):
    """20 stocks with leadership_score 1..20 and return = score/1000 (a perfectly monotone factor), so
    with deciles=10 each decile holds exactly two adjacent scores and decile means rise monotonically."""
    engine = _engine(tmp_path)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i in range(1, 21):
            _add_result(session, run.id, f"S{i:02d}", rank=i, lead=float(i))
            _add_fr(session, run.id, f"S{i:02d}", ret=i / 1000)
        session.commit()
    return engine


# ==================================================================================================
# Pure stats helpers — downside-only risk + Spearman rank-IC (no DB)
# ==================================================================================================
def test_downside_deviation_uses_only_the_negative_leg():
    """sqrt(mean(min(r,0)^2)) — positive returns contribute ZERO (anti-goal: never total volatility)."""
    # only -0.10 contributes: sqrt(((-0.10)^2 + 0 + 0)/3) = sqrt(0.01/3)
    assert _downside_deviation([-0.10, 0.20, 0.30]) == pytest.approx((0.01 / 3) ** 0.5)
    # an all-non-negative cohort has zero downside deviation (no downside risk)
    assert _downside_deviation([0.05, 0.10, 0.20]) == 0.0
    assert _downside_deviation([]) == 0.0


def test_risk_adjusted_is_downside_only_and_na_when_no_downside():
    """risk_adjusted = mean / downside_deviation; NA (None) when n<2 or there is no downside risk —
    NEVER a huge total-volatility number for a healthy all-up cohort."""
    returns = [-0.05, 0.15]  # mean 0.05; downside dev = sqrt(((-0.05)^2 + 0)/2) = sqrt(0.00125)
    expected = 0.05 / (0.00125 ** 0.5)
    assert _risk_adjusted(returns) == pytest.approx(expected)
    # all non-negative -> downside deviation 0 -> NA (not a divide-by-tiny total-vol number)
    assert _risk_adjusted([0.10, 0.20, 0.30]) is None
    # n < 2 -> NA
    assert _risk_adjusted([0.10]) is None


def test_risk_adjusted_does_not_equal_total_volatility_ratio():
    """A symmetric up/down cohort: the downside ratio must differ from the total-stdev (Sharpe-like)
    ratio — proving 'risk' is the downside leg only, not total volatility (the anti-goal)."""
    from statistics import mean, stdev

    returns = [-0.10, 0.30]  # symmetric magnitude up vs down? mean 0.10
    downside_ratio = _risk_adjusted(returns)
    total_ratio = mean(returns) / stdev(returns)
    assert downside_ratio is not None
    assert downside_ratio != pytest.approx(total_ratio)  # downside-only != total-vol


def test_average_ranks_handles_ties():
    """Tied values share the mean of the positions they span (standard Spearman tie handling)."""
    assert _average_ranks([10.0, 20.0, 30.0]) == [1.0, 2.0, 3.0]
    assert _average_ranks([5.0, 5.0, 9.0]) == [1.5, 1.5, 3.0]  # the two 5s share ranks (1+2)/2


def test_rank_ic_exact_on_known_pairs():
    """Spearman rank-IC: perfectly monotone -> 1.0, perfectly inverse -> -1.0, NA on n<2 / zero variance."""
    assert _rank_ic([(1.0, 10.0), (2.0, 20.0), (3.0, 30.0)])["value"] == pytest.approx(1.0)
    assert _rank_ic([(1.0, 30.0), (2.0, 20.0), (3.0, 10.0)])["value"] == pytest.approx(-1.0)
    # a known mixed monotone-with-one-swap set: Spearman of factor[1,2,3,4] vs ranks[1,2,4,3]
    mixed = _rank_ic([(1.0, 0.01), (2.0, 0.02), (3.0, 0.09), (4.0, 0.05)])
    assert mixed["n"] == 4 and mixed["value"] == pytest.approx(0.8)  # 1 - 6*2/(4*15)
    assert _rank_ic([(1.0, 0.5)])["value"] is None and _rank_ic([(1.0, 0.5)])["n"] == 1
    assert _rank_ic([(5.0, 0.1), (5.0, 0.2), (5.0, 0.3)])["value"] is None  # zero factor rank variance


# ==================================================================================================
# Read-only keystone — scoring/return/pattern math raising does NOT break the lab
# ==================================================================================================
def test_factor_lab_is_read_only_no_scoring_or_return_or_pattern_call(monotone_engine, monkeypatch):
    """Read-only (the critical anti-goal): monkeypatch run_scan / score_stocks / forward_return /
    detect_* / score_regime to RAISE, then assert compute_factor_lab STILL returns a full payload
    INCLUDING the by_regime split — proving it reads stored values only (it issues SELECTs and pure
    math, never a scoring/return/factor/regime computation)."""
    import app.engine.forward_testing as ft
    import app.engine.patterns as patterns
    import app.engine.regime as regime
    import app.engine.scanner as scanner
    import app.engine.scoring as scoring

    def _boom(*args, **kwargs):  # pragma: no cover - must never be reached
        raise AssertionError("read path must not recompute a score/return/pattern/regime")

    monkeypatch.setattr(scanner, "run_scan", _boom)
    monkeypatch.setattr(scoring, "score_stocks", _boom)
    monkeypatch.setattr(ft, "forward_return", _boom)
    monkeypatch.setattr(patterns, "detect_vcp", _boom)
    monkeypatch.setattr(patterns, "detect_pullback_to_rising_dma", _boom)
    monkeypatch.setattr(patterns, "detect_flat_base_breakout", _boom)
    monkeypatch.setattr(regime, "score_regime", _boom)  # J-27: regime is READ from stored runs, never recomputed

    cfg = load_config()
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg)

    assert payload["factor"]["key"] == "leadership_score"
    assert payload["n_total"] == 20
    assert len(payload["deciles"]) == 10
    assert payload["rank_ic"]["value"] is not None
    # J-27 read-only keystone: by_regime is fully populated (one row per configured label) even with
    # score_regime patched to raise — the label is read VERBATIM from stored scanner_runs.regime_label.
    by_regime = payload["by_regime"]
    assert [r["regime"] for r in by_regime] == cfg.regime.labels
    on = next(r for r in by_regime if r["regime"] == "Risk-on")
    assert on["n"] == 20  # the fixture's single run is stored Risk-on; the regime is read, never recomputed


# ==================================================================================================
# Decile math — exact membership / mean / n; monotone factor -> monotone decile means
# ==================================================================================================
def test_decile_membership_means_and_monotonicity(monotone_engine):
    """Exact decile table on the monotone fixture: 10 deciles, each n=2, ascending factor ranges, and
    strictly increasing decile means (a perfectly monotone factor sorts future returns monotonically)."""
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, load_config())

    deciles = payload["deciles"]
    assert [d["decile"] for d in deciles] == list(range(1, 11))
    assert all(d["n"] == 2 for d in deciles)
    # ascending factor partitions: decile 1 holds scores {1,2}; decile 10 holds {19,20}
    assert deciles[0]["factor_min"] == 1.0 and deciles[0]["factor_max"] == 2.0
    assert deciles[-1]["factor_min"] == 19.0 and deciles[-1]["factor_max"] == 20.0
    # exact means: decile d holds scores {2d-1, 2d} with return=score/1000
    assert deciles[0]["mean_return"] == pytest.approx((1 + 2) / 2 / 1000)
    assert deciles[-1]["mean_return"] == pytest.approx((19 + 20) / 2 / 1000)
    means = [d["mean_return"] for d in deciles]
    assert means == sorted(means)  # monotone non-decreasing across D1->D10
    # all-non-negative returns -> every decile's downside risk-adjusted is honest NA
    assert all(d["risk_adjusted"] is None for d in deciles)


def test_decile_count_comes_from_config(monotone_engine):
    """No magic numbers: the decile count is config.research.factor_lab.deciles — set it to 4 and the
    table has exactly 4 (equal-count) rows, not a hard-coded 10."""
    cfg = load_config()
    fl4 = cfg.research.factor_lab.model_copy(update={"deciles": 4})
    cfg4 = cfg.model_copy(update={"research": cfg.research.model_copy(update={"factor_lab": fl4})})
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg4)
    assert payload["deciles_count"] == 4
    assert [d["decile"] for d in payload["deciles"]] == [1, 2, 3, 4]
    assert all(d["n"] == 5 for d in payload["deciles"])  # 20 obs / 4 deciles


def test_risk_adjusted_present_when_a_decile_has_downside(tmp_path):
    """A decile whose returns include a negative gets a NUMERIC downside risk-adjusted value (not NA);
    a sibling all-positive decile stays NA — proving the column is computed, downside-only, per decile."""
    engine = _engine(tmp_path, "ra.db")
    cfg = load_config()
    fl2 = cfg.research.factor_lab.model_copy(update={"deciles": 2})
    cfg2 = cfg.model_copy(update={"research": cfg.research.model_copy(update={"factor_lab": fl2})})
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        # low decile (scores 1,2) has a negative return; high decile (3,4) is all positive
        for tkr, score, ret in [("A", 1.0, -0.10), ("B", 2.0, 0.20), ("C", 3.0, 0.10), ("D", 4.0, 0.30)]:
            _add_result(session, run.id, tkr, rank=int(score), lead=score)
            _add_fr(session, run.id, tkr, ret)
        session.commit()
        payload = compute_factor_lab(session, "leadership_score", H, cfg2)
    low, high = payload["deciles"][0], payload["deciles"][1]
    assert low["n"] == 2 and low["risk_adjusted"] is not None  # has a downside leg
    assert high["n"] == 2 and high["risk_adjusted"] is None     # all non-negative -> NA


# ==================================================================================================
# Component sources + NA honesty
# ==================================================================================================
def test_component_source_read_from_record_json_and_factor_null_excluded(tmp_path):
    """A component factor reads `record_json[<block>].components[name].raw` VERBATIM; an observation whose
    component raw is null/`available:false` is EXCLUDED (factor-NULL, never bucketed)."""
    engine = _engine(tmp_path, "comp.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        _add_result(session, run.id, "AAA", 1, record_json=_component_record("leadership", "rs_spy_3m", 0.40))
        _add_result(session, run.id, "BBB", 2, record_json=_component_record("leadership", "rs_spy_3m", 0.10))
        _add_result(session, run.id, "CCC", 3, record_json=_component_record("leadership", "rs_spy_3m", None))  # NA
        for tkr, ret in [("AAA", 0.20), ("BBB", 0.05), ("CCC", -0.30)]:
            _add_fr(session, run.id, tkr, ret)
        session.commit()
        payload = compute_factor_lab(session, "rs_spy_3m", H, load_config())
    # CCC (factor-NULL) is excluded: only AAA + BBB are observations
    assert payload["n_total"] == 2
    assert payload["rank_ic"]["n"] == 2
    nonempty = [d for d in payload["deciles"] if d["n"] > 0]
    assert sum(d["n"] for d in nonempty) == 2  # CCC never bucketed


def test_all_na_factor_yields_empty_table_no_fabrication(tmp_path):
    """An all-NA factor (every component raw null) -> n_total 0, every decile honest n=0 / mean None,
    rank-IC value None / n 0 — never a fabricated row or number (anti-goal: No fabricated data)."""
    engine = _engine(tmp_path, "allna.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i, tkr in enumerate(["AAA", "BBB", "CCC"], start=1):
            _add_result(session, run.id, tkr, i, record_json=_component_record("leadership", "rs_spy_3m", None))
            _add_fr(session, run.id, tkr, 0.10)
        session.commit()
        payload = compute_factor_lab(session, "rs_spy_3m", H, load_config())
    assert payload["n_total"] == 0
    assert len(payload["deciles"]) == 10
    assert all(d["n"] == 0 and d["mean_return"] is None and d["risk_adjusted"] is None for d in payload["deciles"])
    assert payload["rank_ic"] == {"value": None, "n": 0}


def test_low_sample_decile_is_flagged_with_its_n(monotone_engine):
    """A decile with n < walk_forward.min_sample reports its honest `n` AND a low_sample flag (the UI
    renders NA + n) — never hidden, never fabricated. (min_sample=30; the fixture deciles are n=2.)"""
    cfg = load_config()
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
    assert payload["min_sample"] == cfg.walk_forward.min_sample
    assert all(d["low_sample"] is True and d["n"] == 2 for d in payload["deciles"])  # 2 < 30


def test_too_few_post_bars_horizon_has_no_observations(tmp_path):
    """A horizon with no stored forward returns (too few post-bars) -> n_total 0, honest NA rows — never
    fabricated. Forward returns exist only at H=20; horizon 60 has none in this fixture."""
    engine = _engine(tmp_path, "fewbars.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i in range(1, 6):
            _add_result(session, run.id, f"S{i}", rank=i, lead=float(i))
            _add_fr(session, run.id, f"S{i}", ret=i / 100, horizon=H)  # only horizon H persisted
        session.commit()
        payload = compute_factor_lab(session, "leadership_score", 60, load_config())
    assert payload["horizon"] == 60 and payload["n_total"] == 0
    assert all(d["n"] == 0 for d in payload["deciles"])


# ==================================================================================================
# Consistency invariant — the lab is a read-only slice, not a second computation
# ==================================================================================================
def test_pooled_lab_mean_equals_forward_aggregates_overall_mean(monotone_engine):
    """Read-only consistency (the critical anti-goal): for a never-NULL typed-column factor the pooled
    mean of all factor-lab observations at horizon H EQUALS compute_forward_aggregates(H).overall.
    mean_return — the SAME stored observation pool, grouped, never a second computation of any return."""
    from statistics import mean

    cfg = load_config()
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
        agg = compute_forward_aggregates(session, H, cfg)
    # reconstruct the pooled mean from the decile table (sum of per-decile sums / total n)
    pooled = mean(
        [d["mean_return"] for d in payload["deciles"] for _ in range(d["n"])]  # weight by decile n
    )
    assert payload["n_total"] == agg["overall"]["n"]
    assert pooled == pytest.approx(agg["overall"]["mean_return"])


# ==================================================================================================
# Config-driven catalog + boot validation (no magic numbers)
# ==================================================================================================
def test_factor_catalog_is_config_driven():
    """The catalog is exactly config.research.factor_lab.factors, in order — the dropdown vocabulary
    comes from config (a config-only factor needs no code change)."""
    cfg = load_config()
    catalog = factor_catalog(cfg)
    assert [c["key"] for c in catalog] == [f.key for f in cfg.research.factor_lab.factors]
    assert {"key", "label", "family", "direction", "source"} == set(catalog[0])
    # spans typed score columns AND component raws, incl. a volatility-family factor (J-30 extension)
    assert "leadership_score" in {c["key"] for c in catalog}
    assert any(c["family"] == "volatility" for c in catalog)


def test_adding_a_config_factor_appears_in_catalog_with_no_code_change(monotone_engine):
    """No magic numbers: appending a factor row to config makes it appear in the catalog + a computable
    lab with NO code change (the source resolves to a stored value)."""
    from app.config import FactorLabFactor

    cfg = load_config()
    extra = FactorLabFactor(
        key="rs_sector", label="RS vs sector", family="momentum",
        direction="higher_better", source="leadership.components.rs_sector.raw",
    )
    fl = cfg.research.factor_lab.model_copy(
        update={"factors": [*cfg.research.factor_lab.factors, extra]}
    )
    cfg2 = cfg.model_copy(update={"research": cfg.research.model_copy(update={"factor_lab": fl})})
    assert "rs_sector" in {c["key"] for c in factor_catalog(cfg2)}
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "rs_sector", H, cfg2)
    assert payload["factor"]["key"] == "rs_sector"  # computable, no code edit


def test_unknown_factor_raises_value_error(monotone_engine):
    """An unknown factor key raises ValueError (the API maps this to 422 — never a fabricated factor)."""
    with Session(monotone_engine) as session:
        with pytest.raises(ValueError):
            compute_factor_lab(session, "not_a_factor", H, load_config())


def test_volatility_column_factor_decile_ic_and_regime_from_stored_values(tmp_path):
    """J-30: a volatility-family factor (the NEW typed column `hv`) flows through the EXISTING read-only
    `compute_factor_lab` — a populated decile table + numeric rank-IC + by_regime split, all from STORED
    values read VERBATIM (no engine recomputation). A NULL `hv` observation (short history) is EXCLUDED
    (never bucketed). The decile sort is ascending by the stored raw — `direction: lower_better` is
    descriptive only (the engine never flips the sort). The risk-adjusted column stays downside-only."""
    engine = _engine(tmp_path, "vol.db")
    cfg = _cfg_with(deciles=2, min_sample=2)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        # ascending hv with a strictly descending return (higher volatility sorts to LOWER return here),
        # plus one NULL-hv row (short history) that must be excluded; the top decile carries a downside leg.
        specs = [("A", 1.0, 0.40), ("B", 2.0, 0.30), ("C", 3.0, 0.20), ("D", 4.0, -0.10), ("Z", None, -0.50)]
        for i, (tkr, hv, ret) in enumerate(specs, start=1):
            _add_result(session, run.id, tkr, rank=i, hv=hv)
            _add_fr(session, run.id, tkr, ret)
        session.commit()
        payload = compute_factor_lab(session, "hv", H, cfg)

    assert payload["factor"]["key"] == "hv" and payload["factor"]["family"] == "volatility"
    # Z (NULL hv) excluded — 4 real observations, never a fabricated bucket
    assert payload["n_total"] == 4
    deciles = payload["deciles"]
    assert [d["decile"] for d in deciles] == [1, 2]
    # bottom decile = lowest hv {A,B} returns {0.40,0.30} mean 0.35; top decile = highest hv {C,D} {0.20,-0.10} mean 0.05
    assert deciles[0]["factor_min"] == 1.0 and deciles[0]["factor_max"] == 2.0
    assert deciles[0]["mean_return"] == pytest.approx(0.35)
    assert deciles[-1]["mean_return"] == pytest.approx(0.05)
    # downside-only risk-adjusted: bottom decile all-positive -> NA; top decile has a negative -> numeric
    assert deciles[0]["risk_adjusted"] is None
    assert deciles[-1]["risk_adjusted"] is not None
    # higher hv -> lower return here -> a perfectly inverse rank-IC (an honest descriptive finding)
    assert payload["rank_ic"]["n"] == 4 and payload["rank_ic"]["value"] == pytest.approx(-1.0)
    # by_regime is the configured label list (read verbatim from scanner_runs) with Risk-on populated
    assert [r["regime"] for r in payload["by_regime"]] == cfg.regime.labels
    on = next(r for r in payload["by_regime"] if r["regime"] == "Risk-on")
    assert on["n"] == 4


def test_volatility_column_factor_short_history_all_null_is_empty_no_fabrication(tmp_path):
    """J-30 honest NA: when every stored `vcp_contraction` is NULL (short history), the factor yields
    n_total 0, every decile honest n=0 / mean None, and rank-IC value None / n 0 — never a fabricated
    row or number (anti-goal: No fabricated data)."""
    engine = _engine(tmp_path, "vol_allnull.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i, tkr in enumerate(["A", "B", "C"], start=1):
            _add_result(session, run.id, tkr, rank=i, vcp_contraction=None)  # NULL volatility
            _add_fr(session, run.id, tkr, 0.10)
        session.commit()
        payload = compute_factor_lab(session, "vcp_contraction", H, load_config())
    assert payload["n_total"] == 0
    assert all(d["n"] == 0 and d["mean_return"] is None for d in payload["deciles"])
    assert payload["rank_ic"] == {"value": None, "n": 0}


def test_payload_carries_survivorship_and_descriptive_labels(monotone_engine):
    """Honest limitations: the payload carries the survivorship-bias label AND the descriptive/
    universe-relative caveat verbatim (anti-goal: Research lab is read-only, honest & not predictive)."""
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, load_config())
    assert "survivorship" in payload["survivorship_bias"].lower()
    assert payload["descriptive_caveat"] == RESEARCH_CAVEAT
    assert "not a predictive model" in RESEARCH_CAVEAT.lower()


# --- boot validation (ConfigError) — deciles>1, unique keys, resolvable sources -------------------
def test_deciles_le_one_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["deciles"] = 1  # must be > 1
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_duplicate_factor_key_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    factors = data["research"]["factor_lab"]["factors"]
    factors.append(copy.deepcopy(factors[0]))  # duplicate the single factor's key
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_unresolvable_factor_source_raises(tmp_path):
    """A source that is neither a typed column nor a `<block>.components.<name>.raw` path fails the boot."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["factors"][0]["source"] = "bogus_source"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_component_source_with_unknown_component_raises(tmp_path):
    """A `<block>.components.<name>.raw` whose <name> is not in scores.<block>.weights fails the boot
    (the No-magic-numbers source keystone — never a silent default)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["factors"][0]["source"] = "leadership.components.not_a_component.raw"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# ==================================================================================================
# J-27 — regime-conditioned factor effectiveness (by_regime): per configured regime label the rank-IC
# + the top-minus-bottom-decile spread (raw + downside-risk-adjusted) + honest per-regime n / NA.
# The split reuses the SAME read-only observation pool (regime read VERBATIM from scanner_runs).
# ==================================================================================================
def _cfg_with(*, deciles=None, min_sample=None):
    """The real config with the Factor-Lab decile count and/or walk-forward min_sample overridden via
    model_copy (so a tiny hand fixture can be made non-low-sample) — the SAME config-driven code path,
    no magic number injected into the engine."""
    cfg = load_config()
    research = cfg.research
    if deciles is not None:
        research = cfg.research.model_copy(
            update={"factor_lab": cfg.research.factor_lab.model_copy(update={"deciles": deciles})}
        )
    walk_forward = cfg.walk_forward
    if min_sample is not None:
        walk_forward = cfg.walk_forward.model_copy(update={"min_sample": min_sample})
    return cfg.model_copy(update={"research": research, "walk_forward": walk_forward})


@pytest.fixture()
def multi_regime_engine(tmp_path):
    """Two runs with DIFFERENT stored regime labels — 12 Risk-on observations (monotone, positive) and
    8 Risk-off observations (monotone, negative). Proves the by_regime split groups every observation by
    its stored label and that the n's sum to the total."""
    engine = _engine(tmp_path, "multiregime.db")
    with Session(engine) as session:
        run_on = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        run_off = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        for i in range(1, 13):
            _add_result(session, run_on.id, f"N{i:02d}", rank=i, lead=float(i))
            _add_fr(session, run_on.id, f"N{i:02d}", ret=i / 1000)
        for i in range(1, 9):
            _add_result(session, run_off.id, f"F{i:02d}", rank=i, lead=float(i))
            _add_fr(session, run_off.id, f"F{i:02d}", ret=-i / 1000)
        session.commit()
    return engine


def test_by_regime_n_sums_to_total(multi_regime_engine):
    """Consistency invariant (the J-27 keystone): Σ over regimes of per-regime `n` == `n_total` — every
    observation carries exactly one configured regime label (read verbatim from scanner_runs), so the
    split partitions the SAME observation pool with no double-count and no drop."""
    cfg = load_config()
    with Session(multi_regime_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
    by_regime = payload["by_regime"]
    counts = {r["regime"]: r["n"] for r in by_regime}
    assert counts["Risk-on"] == 12 and counts["Risk-off"] == 8
    assert sum(r["n"] for r in by_regime) == payload["n_total"] == 20


def test_by_regime_rows_are_config_labels_in_order_with_honest_empty_rows(multi_regime_engine):
    """Config-driven vocabulary: by_regime is exactly `config.regime.labels` in order (no hard-coded
    regime list); a configured regime with no observations is an HONEST n=0 row (rank-IC + spreads
    None) — never omitted, never fabricated."""
    cfg = load_config()
    with Session(multi_regime_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
    by_regime = payload["by_regime"]
    assert [r["regime"] for r in by_regime] == cfg.regime.labels
    empty = next(r for r in by_regime if r["regime"] == "Choppy")  # no Choppy run in the fixture
    assert empty["n"] == 0 and empty["rank_ic"]["value"] is None
    assert empty["top_decile_mean"] is None and empty["bottom_decile_mean"] is None
    assert empty["spread"] is None and empty["risk_adjusted_spread"] is None


def test_by_regime_exact_spread_and_rank_ic(tmp_path):
    """Exact per-regime spread + rank-IC on a hand fixture: a monotone factor WITHIN one regime → a known
    positive spread (top-decile mean − bottom-decile mean) and rank_ic.value ≈ 1.0; an inverse regime →
    a negative spread and rank_ic.value ≈ -1.0. Distinct populations legitimately differ — only the n's
    reconcile (asserted separately), never the per-regime means."""
    engine = _engine(tmp_path, "regime_spread.db")
    cfg = _cfg_with(deciles=2, min_sample=2)
    with Session(engine) as session:
        up = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        down = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        for tkr, score, ret in [("UA", 1.0, 0.01), ("UB", 2.0, 0.02), ("UC", 3.0, 0.03), ("UD", 4.0, 0.04)]:
            _add_result(session, up.id, tkr, rank=int(score), lead=score)
            _add_fr(session, up.id, tkr, ret)
        for tkr, score, ret in [("DA", 1.0, 0.04), ("DB", 2.0, 0.03), ("DC", 3.0, 0.02), ("DD", 4.0, 0.01)]:
            _add_result(session, down.id, tkr, rank=int(score), lead=score)
            _add_fr(session, down.id, tkr, ret)
        session.commit()
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
    rows = {r["regime"]: r for r in payload["by_regime"]}
    up_row = rows["Risk-on"]
    assert up_row["n"] == 4 and up_row["low_sample"] is False
    # bottom decile {f1,f2} → returns {0.01,0.02} mean 0.015; top decile {f3,f4} → {0.03,0.04} mean 0.035
    assert up_row["bottom_decile_mean"] == pytest.approx(0.015)
    assert up_row["top_decile_mean"] == pytest.approx(0.035)
    assert up_row["spread"] == pytest.approx(0.02)  # 0.035 − 0.015
    assert up_row["rank_ic"]["value"] == pytest.approx(1.0)
    down_row = rows["Risk-off"]
    assert down_row["spread"] == pytest.approx(-0.02)  # inverse regime → negative long-short spread
    assert down_row["rank_ic"]["value"] == pytest.approx(-1.0)


def test_by_regime_risk_adjusted_spread_na_when_top_decile_all_non_negative(tmp_path):
    """Downside-only honesty per regime: a regime whose TOP decile is all-non-negative has no downside in
    that leg → its risk_adjusted leg is None → risk_adjusted_spread is None (NA), while the RAW spread
    stays numeric — a downside-only figure, never a total-volatility number."""
    engine = _engine(tmp_path, "regime_downside.db")
    cfg = _cfg_with(deciles=2, min_sample=2)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        # bottom decile {f1,f2} has a negative (downside present); top decile {f3,f4} all non-negative
        for tkr, score, ret in [("A", 1.0, -0.10), ("B", 2.0, 0.20), ("C", 3.0, 0.10), ("D", 4.0, 0.30)]:
            _add_result(session, run.id, tkr, rank=int(score), lead=score)
            _add_fr(session, run.id, tkr, ret)
        session.commit()
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
    row = next(r for r in payload["by_regime"] if r["regime"] == "Risk-on")
    assert row["n"] == 4 and row["low_sample"] is False
    # raw spread numeric: top mean (0.10+0.30)/2=0.20 − bottom mean (-0.10+0.20)/2=0.05 = 0.15
    assert row["spread"] == pytest.approx(0.15)
    assert row["risk_adjusted_spread"] is None  # top leg all-non-negative → NA (downside-only)


def test_by_regime_low_sample_regime_is_na_with_honest_n(monotone_engine):
    """Low-sample NA: a regime with n < walk_forward.min_sample carries low_sample=True + its HONEST n,
    and both spreads are None (the UI renders NA) — even though the per-decile means exist, the
    regime-TOTAL low sample gates the spread to honest NA, never a number on too few observations."""
    cfg = load_config()  # min_sample=30; the monotone fixture's single Risk-on run has n=20 (< 30)
    with Session(monotone_engine) as session:
        payload = compute_factor_lab(session, "leadership_score", H, cfg)
    row = next(r for r in payload["by_regime"] if r["regime"] == "Risk-on")
    assert row["n"] == 20 and row["low_sample"] is True
    assert row["spread"] is None and row["risk_adjusted_spread"] is None


# ==================================================================================================
# J-26 — multi-factor combination cohorts: the combined-AND cohort vs baseline vs each single-factor
# cohort (mean / median / hit-rate / downside-risk-adjusted / n), over the SAME read-only stored pool.
# ==================================================================================================
# Two DISTINCT typed-column factors (leadership_score L, risk_score R) laid out so the two single
# cohorts cross (neither a subset of the other) and the AND-intersection is a known, strictly-smaller
# set {S4,S5,S6} with a downside leg — exact algebra + stats are computable by hand.
_COMBO_ROWS = [
    # (ticker, leadership, risk, return)
    ("S1", 10, 50, 0.05), ("S2", 20, 60, 0.06), ("S3", 30, 10, -0.50), ("S4", 40, 20, -0.10),
    ("S5", 50, 30, 0.10), ("S6", 60, 40, 0.30), ("S7", 70, 70, 0.07), ("S8", 80, 80, 0.08),
]
_COMBO_CONDITIONS = [
    {"factor": "leadership_score", "side": "top", "quantile": "half"},
    {"factor": "risk_score", "side": "bottom", "quantile": "half"},
]


@pytest.fixture()
def combo_engine(tmp_path):
    """8 stocks with two distinct typed factors (leadership L, risk R). Under [L top-half, R bottom-half]:
    the L-top-half single = {S4..S8} (5), the R-bottom-half single = {S3,S4,S5,S6} (4), and the AND
    cohort = {S4,S5,S6} (3) — a proper subset of EACH single (interaction visible), with a downside leg."""
    engine = _engine(tmp_path, "combo.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i, (tkr, lead, risk, ret) in enumerate(_COMBO_ROWS, start=1):
            _add_result(session, run.id, tkr, rank=i, lead=float(lead), risk=float(risk))
            _add_fr(session, run.id, tkr, ret)
        session.commit()
    return engine


def _expected_membership(rows, key_index, side, fraction):
    """Independently reconstruct ONE condition's membership tickers from the stored `rows` using the SAME
    nearest-rank rule the engine documents — so the engine's grouping is checked, not assumed."""
    values = sorted(r[key_index] for r in rows)
    if side == "top":
        cutoff = _quantile_cutoff(values, 1 - fraction)
        return {r[0] for r in rows if r[key_index] >= cutoff}
    cutoff = _quantile_cutoff(values, fraction)
    return {r[0] for r in rows if r[key_index] <= cutoff}


# --- read-only keystone (critical) ----------------------------------------------------------------
def test_combination_is_read_only_no_scoring_or_return_or_pattern_call(monotone_engine, monkeypatch):
    """Read-only (the critical anti-goal): monkeypatch run_scan / score_stocks / forward_return /
    detect_* / score_regime to RAISE, then assert compute_factor_combination STILL returns a full payload
    (baseline + singles + composite + strict_overlap) — proving BOTH the composite rank-blend path AND the
    strict-AND path SELECT stored values + pure-group/rank only, recomputing no score/return/factor/regime.
    The composite is a deterministic ranking of STORED values (like the J-25 decile sort), not a fit."""
    import app.engine.forward_testing as ft
    import app.engine.patterns as patterns
    import app.engine.regime as regime
    import app.engine.scanner as scanner
    import app.engine.scoring as scoring

    def _boom(*args, **kwargs):  # pragma: no cover - must never be reached
        raise AssertionError("read path must not recompute a score/return/pattern/regime")

    monkeypatch.setattr(scanner, "run_scan", _boom)
    monkeypatch.setattr(scoring, "score_stocks", _boom)
    monkeypatch.setattr(ft, "forward_return", _boom)
    monkeypatch.setattr(patterns, "detect_vcp", _boom)
    monkeypatch.setattr(patterns, "detect_pullback_to_rising_dma", _boom)
    monkeypatch.setattr(patterns, "detect_flat_base_breakout", _boom)
    monkeypatch.setattr(regime, "score_regime", _boom)

    cfg = load_config()
    with Session(monotone_engine) as session:
        payload = compute_factor_combination(
            session,
            [
                {"factor": "leadership_score", "side": "top", "quantile": "half"},
                {"factor": "risk_score", "side": "bottom", "quantile": "half"},
            ],
            H,
            cfg,
        )
    assert payload["pool_n"] == 20
    assert payload["baseline"]["stats"]["n"] == 20
    assert len(payload["singles"]) == 2
    # the composite rank-blend path ran (no scoring/return/pattern call) and is non-empty
    assert payload["composite"]["stats"]["n"] >= 1
    # the strict-AND overlap path ran too: leadership-top-half ∩ (risk all-equal → all) is non-empty
    assert payload["strict_overlap"]["stats"]["n"] >= 1


# --- cohort algebra + exact stats -----------------------------------------------------------------
def test_combination_cohort_algebra_and_exact_stats(combo_engine):
    """Cohort algebra + stats on the controlled fixture: baseline.n == pool_n; each single.n <= pool_n;
    strict_overlap == the EXACT AND-intersection of the single memberships (reconstructed independently),
    strictly smaller than each single (interaction visible), with exact downside-only stats; the composite
    rank-blend cohort is non-empty, ⊆ baseline, populated, and a DISTINCT cohort from the strict overlap."""
    from statistics import mean as _mean, median as _median

    cfg = _cfg_with(min_sample=2)  # so the small cohorts are not low-sample (stats are numeric, not NA)
    with Session(combo_engine) as session:
        payload = compute_factor_combination(session, _COMBO_CONDITIONS, H, cfg)

    # independently reconstruct the two single memberships + their intersection from the stored rows
    members_lead = _expected_membership(_COMBO_ROWS, 1, "top", 0.5)     # L top-half
    members_risk = _expected_membership(_COMBO_ROWS, 2, "bottom", 0.5)  # R bottom-half
    strict_tickers = members_lead & members_risk
    assert members_lead == {"S4", "S5", "S6", "S7", "S8"}
    assert members_risk == {"S3", "S4", "S5", "S6"}
    assert strict_tickers == {"S4", "S5", "S6"}

    # baseline = whole pool
    assert payload["pool_n"] == len(_COMBO_ROWS) == 8
    assert payload["baseline"]["stats"]["n"] == 8

    singles = payload["singles"]
    assert [s["condition"]["factor"]["key"] for s in singles] == ["leadership_score", "risk_score"]
    assert singles[0]["stats"]["n"] == len(members_lead) == 5
    assert singles[1]["stats"]["n"] == len(members_risk) == 4
    assert all(s["stats"]["n"] <= payload["pool_n"] for s in singles)  # each single ⊆ baseline

    # SECONDARY strict_overlap == exact AND-intersection, strictly smaller than EACH single (⊆ each single)
    strict = payload["strict_overlap"]["stats"]
    assert strict["n"] == len(strict_tickers) == 3
    assert strict["n"] < singles[0]["stats"]["n"] and strict["n"] < singles[1]["stats"]["n"]
    assert strict["n"] <= min(s["stats"]["n"] for s in singles)

    # exact stats on the known strict-overlap returns {S4:-0.10, S5:0.10, S6:0.30}
    strict_returns = [r[3] for r in _COMBO_ROWS if r[0] in strict_tickers]
    assert strict_returns == [-0.10, 0.10, 0.30]
    assert strict["mean_return"] == pytest.approx(_mean(strict_returns))      # 0.10
    assert strict["median_return"] == pytest.approx(_median(strict_returns))  # 0.10
    assert strict["hit_rate"] == pytest.approx(2 / 3)                         # 2 of 3 positive
    assert strict["risk_adjusted"] == pytest.approx(_risk_adjusted(strict_returns))  # downside-only
    assert strict["risk_adjusted"] is not None and strict["low_sample"] is False

    # HEADLINE composite rank-blend: non-empty, ⊆ baseline, populated, not low-sample, and a DISTINCT cohort
    composite = payload["composite"]["stats"]
    assert composite["n"] >= 1 and composite["n"] <= payload["pool_n"]   # composite ⊆ baseline, non-empty
    assert composite["mean_return"] is not None and composite["low_sample"] is False
    assert payload["composite"]["label"] != payload["strict_overlap"]["label"]


# --- honest NA: empty (opposing extremes) + thin (low-sample) cohorts -----------------------------
def test_combination_opposing_extremes_empty_cohort_is_na_not_zero(monotone_engine):
    """The iter-18 HEADLINE bar-raise on the EXACT fixture that used to be 0/NA (the iter-11 membership-NA
    lesson — driven by membership, not horizon length): the AND of two OPPOSING extremes of the SAME factor
    (top-quintile AND bottom-quintile) is empty → the SECONDARY `strict_overlap` cohort shows stats `None`
    (NA) and n=0 (never a fabricated 0), WHILE the HEADLINE `composite` rank-blend stays POPULATED (non-
    empty, n > 0, numeric mean). The two opposing oriented ranks average to a flat blend, so the composite
    honestly selects the whole pool rather than collapsing to NA — proving the re-scoped acceptance is met
    on the precise selection that previously yielded only 0/NA. Each single cohort is itself non-empty."""
    cfg = _cfg_with(min_sample=2)  # so the populated composite (n = pool_n) is clearly not low-sample
    with Session(monotone_engine) as session:
        payload = compute_factor_combination(
            session,
            [
                {"factor": "leadership_score", "side": "top", "quantile": "quintile"},
                {"factor": "leadership_score", "side": "bottom", "quantile": "quintile"},
            ],
            H,
            cfg,
        )
    # SECONDARY strict overlap: the empty AND-intersection -> honest NA + n=0, never a fabricated 0
    strict = payload["strict_overlap"]["stats"]
    assert strict["n"] == 0
    assert strict["mean_return"] is None and strict["median_return"] is None
    assert strict["hit_rate"] is None and strict["risk_adjusted"] is None  # NA, never a fabricated 0
    assert strict["low_sample"] is True  # 0 < min_sample

    # HEADLINE composite: POPULATED where the strict overlap is empty (the bar-raise) — non-empty + numeric
    composite = payload["composite"]["stats"]
    assert composite["n"] > 0                       # non-empty (no longer perpetually 0/NA)
    assert composite["n"] == payload["pool_n"]      # opposing extremes blend flat -> honestly the whole pool
    assert composite["mean_return"] is not None     # populated mean (the UI shows a number, not NA)
    assert composite["low_sample"] is False         # n = 20 >= min_sample 2

    assert all(s["stats"]["n"] >= 1 for s in payload["singles"])  # the extremes themselves are non-empty


def test_combination_thin_cohort_is_low_sample_with_honest_n(combo_engine):
    """A thin but non-empty strict-overlap cohort (n < walk_forward.min_sample) carries low_sample=True +
    its HONEST n (the UI renders NA + n); the engine still computes the figure (the UI gates the display) —
    never hidden, never fabricated. (Real min_sample=30; the strict overlap here is n=3.)"""
    cfg = load_config()  # min_sample=30
    with Session(combo_engine) as session:
        payload = compute_factor_combination(session, _COMBO_CONDITIONS, H, cfg)
    assert payload["min_sample"] == cfg.walk_forward.min_sample == 30
    strict = payload["strict_overlap"]["stats"]
    assert strict["n"] == 3 and strict["low_sample"] is True
    assert strict["mean_return"] is not None  # computed; the UI renders NA because low_sample is True


# --- pool honesty: a factor-NULL observation is excluded from the multi-factor pool ----------------
def test_combination_pool_excludes_factor_null_observations(tmp_path):
    """Pool honesty (the iter-2 lesson): an observation NULL in ANY referenced factor is EXCLUDED from
    the multi-factor pool (never fabricated), so `pool_n` is a (possibly strict) subset of EACH single
    factor's own `_factor_observations` n — do NOT assert equality to the aggregate mean."""
    engine = _engine(tmp_path, "combo_pool.db")
    cfg = _cfg_with(min_sample=2)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        # (ticker, leadership typed-column, rs_spy_3m component raw, return). CCC's rs_spy_3m is NULL.
        specs = [("AAA", 10.0, 0.40, 0.20), ("BBB", 20.0, 0.10, 0.05),
                 ("CCC", 30.0, None, -0.30), ("DDD", 40.0, 0.20, 0.10)]
        for i, (tkr, lead, rs, ret) in enumerate(specs, start=1):
            _add_result(session, run.id, tkr, rank=i, lead=lead,
                        record_json=_component_record("leadership", "rs_spy_3m", rs))
            _add_fr(session, run.id, tkr, ret)
        session.commit()
        payload = compute_factor_combination(
            session,
            [
                {"factor": "rs_spy_3m", "side": "top", "quantile": "half"},
                {"factor": "leadership_score", "side": "top", "quantile": "half"},
            ],
            H,
            cfg,
        )
        lead_factor = next(f for f in cfg.research.factor_lab.factors if f.key == "leadership_score")
        rs_factor = next(f for f in cfg.research.factor_lab.factors if f.key == "rs_spy_3m")
        lead_n = len(_factor_observations(session, lead_factor, H))
        rs_n = len(_factor_observations(session, rs_factor, H))
    # CCC (rs_spy_3m NULL) is excluded from the multi-factor pool — never fabricated
    assert payload["pool_n"] == 3
    assert payload["baseline"]["stats"]["n"] == 3
    # pool ≤ EACH single factor's OWN _factor_observations n (a subset, not an equality to the agg mean)
    assert lead_n == 4 and rs_n == 3
    assert payload["pool_n"] <= lead_n and payload["pool_n"] <= rs_n


def test_combination_horizon_without_observations_is_all_na(combo_engine):
    """A horizon with no stored forward returns (too few post-bars) → pool_n 0 and every cohort NA — never
    fabricated. Forward returns exist only at H=20; horizon 60 has none in this fixture."""
    cfg = _cfg_with(min_sample=2)
    with Session(combo_engine) as session:
        payload = compute_factor_combination(session, _COMBO_CONDITIONS, 60, cfg)
    assert payload["horizon"] == 60 and payload["pool_n"] == 0
    assert payload["baseline"]["stats"]["mean_return"] is None
    # an empty pool -> BOTH the composite and the strict-overlap cohorts are honest NA (n=0), never a 0
    assert payload["composite"]["stats"]["n"] == 0 and payload["composite"]["stats"]["mean_return"] is None
    assert payload["strict_overlap"]["stats"]["n"] == 0
    assert payload["strict_overlap"]["stats"]["mean_return"] is None
    assert all(s["stats"]["n"] == 0 and s["stats"]["mean_return"] is None for s in payload["singles"])


# --- config-driven payload + ValueError on bad input ----------------------------------------------
def test_combination_payload_is_config_driven_with_labels(combo_engine):
    """No magic numbers / single source: the quantile vocabulary, condition limits, and factor catalog
    all come from config (no hard-coded list in the engine); the survivorship/descriptive labels are
    carried verbatim; each resolved condition carries the full factor descriptor + side + quantile."""
    cfg = load_config()
    comb = cfg.research.factor_lab.combination
    with Session(combo_engine) as session:
        payload = compute_factor_combination(session, _COMBO_CONDITIONS, H, cfg)
    assert [q["key"] for q in payload["quantiles"]] == [q.key for q in comb.quantiles]
    assert all({"key", "label", "fraction"} == set(q) for q in payload["quantiles"])
    assert payload["min_conditions"] == comb.min_conditions
    assert payload["max_conditions"] == comb.max_conditions
    assert [f["key"] for f in payload["factors"]] == [f.key for f in cfg.research.factor_lab.factors]
    assert "survivorship" in payload["survivorship_bias"].lower()
    assert payload["descriptive_caveat"] == RESEARCH_CAVEAT
    c0 = payload["conditions"][0]
    assert c0["factor"]["key"] == "leadership_score" and c0["side"] == "top"
    assert c0["quantile"]["key"] == "half" and "fraction" in c0["quantile"]
    assert payload["baseline"]["label"]
    # the headline composite + the secondary strict-overlap carry distinct server-built labels
    assert payload["composite"]["label"] and payload["strict_overlap"]["label"]
    assert payload["composite"]["label"] != payload["strict_overlap"]["label"]
    # the composite quantile + weighting are ECHOED from config (transparent, config-driven labels)
    assert payload["composite_quantile"]["key"] == comb.composite.quantile
    assert {"key", "label", "fraction"} == set(payload["composite_quantile"])
    assert payload["weighting"]["scheme"] == comb.composite.weighting.scheme
    assert payload["weighting"]["default_weight"] == comb.composite.weighting.default_weight


# --- composite rank-blend: orientation + config-driven cohort size (the iter-18 headline) -----------
@pytest.fixture()
def orient_engine(tmp_path):
    """10 stocks with leadership AND entry_quality both PERFECTLY MONOTONE in i (both = i) and returns =
    i/100 (a higher factor => a higher realized return). A two-condition composite with both sides `top`
    must select the HIGH-i names; both `bottom` must select the LOW-i names — orientation is by the user's
    side, never by the catalog `direction`/`family` descriptive metadata."""
    engine = _engine(tmp_path, "orient.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i in range(1, 11):
            _add_result(session, run.id, f"T{i:02d}", rank=i, lead=float(i), entry=float(i))
            _add_fr(session, run.id, f"T{i:02d}", ret=i / 100)
        session.commit()
    return engine


def test_combination_composite_orientation_top_vs_bottom(orient_engine):
    """Orientation correctness (the composite headline): on a monotone fixture a `top`-side composite
    selects the HIGH-factor names (high realized return) and a `bottom`-side composite selects the
    LOW-factor names (low realized return) — so the same factors at opposite sides yield clearly different,
    correctly-ordered composite cohorts. Returns are monotone in the factor, so the cohort mean return is
    an exact proxy for which names were selected (by hand: top {T08,T09,T10} mean 0.09; bottom
    {T01,T02,T03} mean 0.02)."""
    cfg = _cfg_with(min_sample=2)  # the n=3 cohorts are not low-sample (means are numeric)
    with Session(orient_engine) as session:
        top = compute_factor_combination(
            session,
            [
                {"factor": "leadership_score", "side": "top", "quantile": "quintile"},
                {"factor": "entry_quality_score", "side": "top", "quantile": "quintile"},
            ],
            H, cfg,
        )
        bottom = compute_factor_combination(
            session,
            [
                {"factor": "leadership_score", "side": "bottom", "quantile": "quintile"},
                {"factor": "entry_quality_score", "side": "bottom", "quantile": "quintile"},
            ],
            H, cfg,
        )
    top_mean = top["composite"]["stats"]["mean_return"]
    bottom_mean = bottom["composite"]["stats"]["mean_return"]
    # top-side composite picks the high-factor (high-return) names; bottom-side picks the low-factor names
    assert top_mean == pytest.approx(0.09)
    assert bottom_mean == pytest.approx(0.02)
    assert top_mean > bottom_mean
    # both composites are populated (non-empty) — the side flips WHICH extreme, never collapses to NA
    assert top["composite"]["stats"]["n"] > 0 and bottom["composite"]["stats"]["n"] > 0


def test_combination_composite_cohort_size_is_config_driven(combo_engine):
    """No magic numbers: the composite cohort fraction is config...combination.composite.quantile —
    widening it (quintile 0.20 -> half 0.50) ENLARGES the composite cohort n (proves the fraction is
    config-sourced, not a hard-coded literal) and the echoed `composite_quantile` re-points with it."""
    def _cfg_with_composite_quantile(qkey: str):
        cfg = load_config()
        comb = cfg.research.factor_lab.combination
        new_comb = comb.model_copy(update={"composite": comb.composite.model_copy(update={"quantile": qkey})})
        fl = cfg.research.factor_lab.model_copy(update={"combination": new_comb})
        research = cfg.research.model_copy(update={"factor_lab": fl})
        wf = cfg.walk_forward.model_copy(update={"min_sample": 2})
        return cfg.model_copy(update={"research": research, "walk_forward": wf})

    with Session(combo_engine) as session:
        narrow = compute_factor_combination(session, _COMBO_CONDITIONS, H, _cfg_with_composite_quantile("quintile"))
        wide = compute_factor_combination(session, _COMBO_CONDITIONS, H, _cfg_with_composite_quantile("half"))
    assert narrow["composite_quantile"]["key"] == "quintile" and wide["composite_quantile"]["key"] == "half"
    assert wide["composite"]["stats"]["n"] > narrow["composite"]["stats"]["n"]  # wider quantile -> larger cohort
    assert wide["composite"]["stats"]["n"] <= wide["pool_n"]  # still ⊆ baseline (config drives size, not membership rule)


def test_combination_unknown_factor_side_quantile_and_count_raise(monotone_engine):
    """The engine raises ValueError on an unknown factor/side/quantile or an out-of-range condition count
    (the API maps each to 422 — never a fabricated factor/side/quantile/cohort)."""
    cfg = load_config()
    with Session(monotone_engine) as session:
        with pytest.raises(ValueError):  # unknown factor
            compute_factor_combination(session, [
                {"factor": "not_a_factor", "side": "top", "quantile": "half"},
                {"factor": "risk_score", "side": "bottom", "quantile": "half"},
            ], H, cfg)
        with pytest.raises(ValueError):  # unknown side
            compute_factor_combination(session, [
                {"factor": "leadership_score", "side": "sideways", "quantile": "half"},
                {"factor": "risk_score", "side": "bottom", "quantile": "half"},
            ], H, cfg)
        with pytest.raises(ValueError):  # unknown quantile
            compute_factor_combination(session, [
                {"factor": "leadership_score", "side": "top", "quantile": "decile"},
                {"factor": "risk_score", "side": "bottom", "quantile": "half"},
            ], H, cfg)
        with pytest.raises(ValueError):  # too few conditions (1 < min_conditions 2)
            compute_factor_combination(session, [
                {"factor": "leadership_score", "side": "top", "quantile": "half"},
            ], H, cfg)
        with pytest.raises(ValueError):  # too many conditions (12 > max_conditions 11)
            compute_factor_combination(
                session,
                [{"factor": "leadership_score", "side": "top", "quantile": "half"}] * 12,
                H, cfg,
            )


# --- boot validation (ConfigError) for the combination block --------------------------------------
def test_combination_min_gt_max_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["min_conditions"] = 5  # > max_conditions 3
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_fraction_out_of_range_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["quantiles"][0]["fraction"] = 1.5  # ∉ (0, 1)
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_duplicate_quantile_key_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    quantiles = data["research"]["factor_lab"]["combination"]["quantiles"]
    quantiles.append(copy.deepcopy(quantiles[0]))  # duplicate the single quantile's key
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_default_unknown_factor_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["default_conditions"][0]["factor"] = "not_a_factor"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_default_unknown_quantile_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["default_conditions"][0]["quantile"] = "not_a_quantile"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_default_count_outside_range_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    # only 1 default condition while min_conditions=2 -> count out of [min, max]
    data["research"]["factor_lab"]["combination"]["default_conditions"] = [
        {"factor": "leadership_score", "side": "top", "quantile": "half"},
    ]
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_invalid_side_raises(tmp_path):
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["default_conditions"][0]["side"] = "sideways"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# --- iter-18 composite rank-blend boot validation (ConfigError) ------------------------------------
def test_combination_composite_unknown_quantile_raises(tmp_path):
    """composite.quantile must be a real `quantiles` key — an unknown key fails the boot loudly (anti-goal:
    No magic numbers — the composite cohort fraction is config-sourced, never a silent default)."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["composite"]["quantile"] = "not_a_quantile"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_composite_nonpositive_weight_raises(tmp_path):
    """composite.weighting.default_weight must be > 0 — a non-positive base weight fails the boot loudly."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["composite"]["weighting"]["default_weight"] = 0
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


def test_combination_composite_unknown_scheme_raises(tmp_path):
    """composite.weighting.scheme must be a known scheme (Literal['equal']) — an unknown scheme fails the
    boot loudly, never a silent default."""
    data = copy.deepcopy(MINIMAL_VALID)
    data["research"]["factor_lab"]["combination"]["composite"]["weighting"]["scheme"] = "ml_fitted"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, data))


# ==================================================================================================
# J-29 — Setup & Pattern event study: pooled cross-snapshot distribution + expectancy + MAE/MFE +
# downside-only risk-adjusted + best-exit-horizon + by-regime/by-sector, read-only over stored values.
# ==================================================================================================
@pytest.fixture()
def event_study_engine(tmp_path):
    """Two runs in DIFFERENT regimes with known setups, VCP flags, sectors, returns + stored MAE/MFE — so
    the event-study pooled stats, the by-regime/by-sector slices, and the consistency invariant vs
    `compute_forward_aggregates` (by_setup / by_vcp) are exact by construction. VCP names span both
    regimes (Risk-on AA,CC + Risk-off DD) and all VCP names are Technology (a present-only by-sector)."""
    engine = _engine(tmp_path, "eventstudy.db")
    with Session(engine) as session:
        on = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        off = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        # (ticker, run, setup, sector, is_vcp, ret, mae, mfe)
        rows = [
            ("AA", on,  "Actionable",         "Technology", True,  0.10, -0.05, 0.15),
            ("BB", on,  "Actionable",         "Energy",     False, 0.20, -0.02, 0.25),
            ("CC", on,  "Breakout-watch",     "Technology", True,  -0.10, -0.18, 0.05),
            ("DD", off, "Risk-off-watchlist", "Technology", True,  0.30, -0.08, 0.35),
            ("EE", off, "Risk-off-watchlist", "Energy",     False, 0.04, -0.03, 0.12),
        ]
        for i, (tkr, run, setup, sector, is_vcp, ret, mae, mfe) in enumerate(rows, start=1):
            _add_result(session, run.id, tkr, rank=i, setup=setup, sector=sector, is_vcp=is_vcp)
            _add_fr(session, run.id, tkr, ret, mae=mae, mfe=mfe)
        session.commit()
    return engine


# --- read-only keystone (critical) ----------------------------------------------------------------
def test_event_study_is_read_only_no_scoring_return_excursion_or_pattern_call(event_study_engine, monkeypatch):
    """Read-only (the critical anti-goal): monkeypatch run_scan / score_stocks / forward_return /
    forward_excursions / detect_* / score_regime to RAISE, then assert compute_event_study STILL returns a
    full payload (per-horizon rows + by-regime + by-sector) — proving it SELECTs stored values + pure-math
    only, recomputing no return/excursion/score/regime/pattern. The new `forward_excursions` is in the
    raise set because MAE/MFE are STORED and read verbatim, never recomputed in the read path."""
    import app.engine.forward_testing as ft
    import app.engine.patterns as patterns
    import app.engine.regime as regime
    import app.engine.scanner as scanner
    import app.engine.scoring as scoring

    def _boom(*args, **kwargs):  # pragma: no cover - must never be reached
        raise AssertionError("read path must not recompute a score/return/excursion/pattern/regime")

    monkeypatch.setattr(scanner, "run_scan", _boom)
    monkeypatch.setattr(scoring, "score_stocks", _boom)
    monkeypatch.setattr(ft, "forward_return", _boom)
    monkeypatch.setattr(ft, "forward_excursions", _boom)  # iter-14: excursions are STORED, read verbatim
    monkeypatch.setattr(patterns, "detect_vcp", _boom)
    monkeypatch.setattr(patterns, "detect_pullback_to_rising_dma", _boom)
    monkeypatch.setattr(patterns, "detect_flat_base_breakout", _boom)
    monkeypatch.setattr(regime, "score_regime", _boom)

    cfg = _cfg_with(min_sample=2)
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "vcp", H, cfg)
    assert payload["subject"]["key"] == "vcp" and payload["subject"]["kind"] == "pattern"
    row = next(r for r in payload["by_horizon"] if r["horizon"] == H)
    assert row["n"] == 3 and row["mean_return"] is not None
    assert [r["regime"] for r in payload["by_regime"]] == cfg.regime.labels
    assert [r["sector"] for r in payload["by_sector"]] == ["Technology"]


# --- consistency invariant (the read-only proof; iter-2 lesson: bind to compute_forward_aggregates) ---
def test_event_study_consistency_with_forward_aggregates(event_study_engine):
    """Consistency invariant (the iter-2-scoped read-only proof): the event-study pooled mean for a SETUP
    equals `compute_forward_aggregates(H).by_setup[setup].mean_return`, and for the VCP PATTERN equals the
    `by_vcp` flagged-cohort mean — the SAME stored observations grouped, never a second computation. (Bound
    to compute_forward_aggregates, NOT the per-date scorecard's top cohort — a different population.)"""
    cfg = load_config()
    with Session(event_study_engine) as session:
        es_setup = compute_event_study(session, "Actionable", H, cfg)
        es_vcp = compute_event_study(session, "vcp", H, cfg)
        agg = compute_forward_aggregates(session, H, cfg)

    by_setup = {r["setup"]: r for r in agg["by_setup"]}
    es_setup_row = next(r for r in es_setup["by_horizon"] if r["horizon"] == H)
    assert es_setup_row["n"] == by_setup["Actionable"]["n"] == 2
    assert es_setup_row["mean_return"] == pytest.approx(by_setup["Actionable"]["mean_return"])

    by_vcp = {r["vcp"]: r for r in agg["by_vcp"]}
    es_vcp_row = next(r for r in es_vcp["by_horizon"] if r["horizon"] == H)
    assert es_vcp_row["n"] == by_vcp["VCP"]["n"] == 3
    assert es_vcp_row["mean_return"] == pytest.approx(by_vcp["VCP"]["mean_return"])


# --- distribution + expectancy + MAE/MFE + downside-only risk-adjusted (exact) ---------------------
def test_event_study_distribution_expectancy_mae_mfe_exact(event_study_engine):
    """Exact per-horizon stats on the VCP cohort {AA:0.10, CC:-0.10, DD:0.30}: distribution
    (mean/median/%positive/dispersion), the expectancy decomposition (which equals the mean), the mean
    STORED MAE/MFE (read verbatim), and BOTH downside-only risk-adjusted ratios (numeric here — a downside
    leg and a non-zero mean|MAE| exist), each beside the raw mean."""
    from statistics import mean as _mean, median as _median, stdev as _stdev

    cfg = _cfg_with(min_sample=2)  # so n=3 is not low-sample (the engine computes either way; this is exact)
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "vcp", H, cfg)
    row = next(r for r in payload["by_horizon"] if r["horizon"] == H)
    returns = [0.10, -0.10, 0.30]
    assert row["n"] == 3 and row["low_sample"] is False
    assert row["mean_return"] == pytest.approx(_mean(returns))  # 0.10
    assert row["median"] == pytest.approx(_median(returns))     # 0.10
    assert row["pct_positive"] == pytest.approx(2 / 3)          # AA,DD > 0 ; CC not
    assert row["dispersion"] == pytest.approx(_stdev(returns))
    exp = row["expectancy"]
    assert exp["win_rate"] == pytest.approx(2 / 3)
    assert exp["avg_win"] == pytest.approx(_mean([0.10, 0.30]))  # 0.20
    assert exp["avg_loss"] == pytest.approx(-0.10)
    assert exp["expectancy"] == pytest.approx(_mean(returns))    # the identity: expectancy == mean
    assert row["mean_mae"] == pytest.approx(_mean([-0.05, -0.18, -0.08]))  # stored, read verbatim
    assert row["mean_mfe"] == pytest.approx(_mean([0.15, 0.05, 0.35]))
    assert row["return_per_downside_dev"] == pytest.approx(_risk_adjusted(returns))  # downside-only
    assert row["return_per_mae"] == pytest.approx(_mean(returns) / _mean([0.05, 0.18, 0.08]))


def test_event_study_risk_adjusted_na_when_no_downside_and_zero_mae(tmp_path):
    """Downside-only honesty (the iter-11 risk-adjusted-NA fixture): an all-non-negative subject cohort
    with zero MAE has no downside leg → BOTH return_per_downside_dev and return_per_mae are NA (None) —
    never a total-volatility number, never a fabricated ratio — while the raw mean is still shown."""
    engine = _engine(tmp_path, "es_downside.db")
    cfg = _cfg_with(min_sample=2)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        for i, (tkr, ret) in enumerate([("P", 0.10), ("Q", 0.20), ("R", 0.30)], start=1):
            _add_result(session, run.id, tkr, rank=i, setup="Actionable", is_vcp=True)
            _add_fr(session, run.id, tkr, ret, mae=0.0, mfe=0.30)  # all-up + zero adverse excursion
        session.commit()
        payload = compute_event_study(session, "vcp", H, cfg)
    row = next(r for r in payload["by_horizon"] if r["horizon"] == H)
    assert row["n"] == 3 and row["mean_return"] == pytest.approx(0.20)  # raw mean still shown
    assert row["return_per_downside_dev"] is None  # no downside leg → NA (not total volatility)
    assert row["return_per_mae"] is None           # mean|MAE| == 0 → NA


def test_event_study_single_member_risk_adjusted_na(tmp_path):
    """n < 2 → both downside-risk-adjusted ratios are NA (no dispersion / single excursion to divide by),
    while the raw mean is still shown — honest, never fabricated."""
    engine = _engine(tmp_path, "es_single.db")
    cfg = _cfg_with(min_sample=1)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        _add_result(session, run.id, "ONLY", rank=1, setup="Actionable", is_vcp=True)
        _add_fr(session, run.id, "ONLY", -0.10, mae=-0.20, mfe=0.05)
        session.commit()
        payload = compute_event_study(session, "vcp", H, cfg)
    row = next(r for r in payload["by_horizon"] if r["horizon"] == H)
    assert row["n"] == 1 and row["mean_return"] == pytest.approx(-0.10)
    assert row["return_per_downside_dev"] is None and row["return_per_mae"] is None


# --- by-regime: every config label, Σ n == pooled n, honest empty rows ------------------------------
def test_event_study_by_regime_sums_to_pooled_n_and_emits_every_label(event_study_engine):
    """The by-regime slice emits every CONFIGURED regime label in order (no hard-coded list); Σ per-regime
    n == the selected-horizon pooled n (each member carries exactly one stored label); an empty configured
    regime is an HONEST NA row (n=0, mean None) — never omitted, never fabricated."""
    cfg = _cfg_with(min_sample=2)
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "vcp", H, cfg)
    by_regime = payload["by_regime"]
    assert [r["regime"] for r in by_regime] == cfg.regime.labels
    counts = {r["regime"]: r["n"] for r in by_regime}
    assert counts["Risk-on"] == 2 and counts["Risk-off"] == 1
    assert sum(r["n"] for r in by_regime) == payload["n_total"] == 3  # Σ per-regime n == pooled n
    empty = next(r for r in by_regime if r["regime"] == "Choppy")  # no Choppy member in the fixture
    assert empty["n"] == 0 and empty["mean_return"] is None and empty["risk_adjusted"] is None


# --- by-sector: present-only (non-padded), config order, honest NA ---------------------------------
def test_event_study_by_sector_present_only(event_study_engine):
    """The by-sector slice is NON-padded — only sectors WITH subject members appear (config order). All
    three VCP names are Technology, so the slice is exactly [Technology] with the pooled mean."""
    cfg = _cfg_with(min_sample=2)
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "vcp", H, cfg)
    by_sector = payload["by_sector"]
    assert [r["sector"] for r in by_sector] == ["Technology"]
    assert by_sector[0]["n"] == 3 and by_sector[0]["mean_return"] == pytest.approx(0.10)


def test_event_study_low_count_subject_is_low_sample(event_study_engine):
    """A low-count subject (a pattern flagged on few names) carries low_sample=True + its honest n at the
    populated horizon (the UI renders NA + n) — never hidden, never fabricated. (Real min_sample=30.)"""
    cfg = load_config()  # min_sample 30
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "vcp", H, cfg)
    assert payload["min_sample"] == cfg.walk_forward.min_sample == 30
    row = next(r for r in payload["by_horizon"] if r["horizon"] == H)
    assert row["n"] == 3 and row["low_sample"] is True  # 3 < 30


# --- best exit-horizon: argmax of the primary metric among non-low-sample horizons -----------------
def test_event_study_best_exit_horizon_argmax_non_low_sample(tmp_path):
    """best_exit_horizon = the argmax horizon among NON-low-sample horizons of the primary metric
    (return_per_downside_dev, falling back to mean_return). Two populated horizons with the same downside
    but different means → the higher-metric horizon (60) wins; all-low-sample → None."""
    engine = _engine(tmp_path, "es_exit.db")
    cfg = _cfg_with(min_sample=2)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        for i, tkr in enumerate(["X", "Y"], start=1):
            _add_result(session, run.id, tkr, rank=i, setup="Actionable", is_vcp=True)
        # horizon 20: returns {0.02,-0.01} (low metric); horizon 60: {0.30,-0.01} (same downside, higher mean)
        _add_fr(session, run.id, "X", 0.02, horizon=20, mae=-0.05, mfe=0.05)
        _add_fr(session, run.id, "Y", -0.01, horizon=20, mae=-0.05, mfe=0.05)
        _add_fr(session, run.id, "X", 0.30, horizon=60, mae=-0.05, mfe=0.35)
        _add_fr(session, run.id, "Y", -0.01, horizon=60, mae=-0.05, mfe=0.05)
        session.commit()
        payload = compute_event_study(session, "vcp", 20, cfg)
    assert payload["best_exit_horizon"] == 60


def test_event_study_best_exit_horizon_na_when_all_low_sample(event_study_engine):
    """When EVERY horizon is low-sample (real min_sample=30, the fixture is tiny) best_exit_horizon is NA
    (None) — never a fabricated 'best' on thin evidence."""
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "vcp", H, load_config())
    assert payload["best_exit_horizon"] is None


# --- unknown subject + config-driven catalog + payload labels -------------------------------------
def test_event_study_unknown_subject_raises(event_study_engine):
    """An unknown subject key raises ValueError (the API maps this to 422 — never a fabricated subject)."""
    with Session(event_study_engine) as session:
        with pytest.raises(ValueError):
            compute_event_study(session, "not_a_subject", H, load_config())


def test_subject_catalog_is_config_driven_setups_then_patterns():
    """The subject catalog is config-driven: every setup status (ALL_STATUSES order) then every
    config.patterns key, each labelled from the single config-backed methodology copy (a config-only
    setup/pattern appears with no code change)."""
    from app.engine.setups import ALL_STATUSES

    cfg = load_config()
    subjects = subject_catalog(cfg)
    setups = [s for s in subjects if s["kind"] == "setup"]
    patterns = [s for s in subjects if s["kind"] == "pattern"]
    assert [s["key"] for s in setups] == ALL_STATUSES
    assert [s["key"] for s in patterns] == list(cfg.patterns.model_dump())
    assert {"key", "label", "kind"} == set(subjects[0])
    vcp = next(s for s in subjects if s["key"] == "vcp")
    assert vcp["label"] == next(e.name for e in cfg.methodology.entries if e.key == "vcp")


def test_event_study_payload_shape_and_labels(event_study_engine):
    """The payload carries the resolved subject, the config-driven subjects catalog + horizons +
    default_horizon + min_sample, the survivorship + descriptive labels verbatim, and one per-horizon row
    (full shape) per configured horizon."""
    cfg = load_config()
    with Session(event_study_engine) as session:
        payload = compute_event_study(session, "Actionable", H, cfg)
    assert payload["subject"] == {"key": "Actionable", "label": "Actionable", "kind": "setup"}
    assert payload["horizon"] == H and payload["horizons"] == list(cfg.walk_forward.horizons)
    assert payload["default_horizon"] == cfg.walk_forward.default_horizon
    assert [s["key"] for s in payload["subjects"]] == [s["key"] for s in subject_catalog(cfg)]
    assert "survivorship" in payload["survivorship_bias"].lower()
    assert payload["descriptive_caveat"] == RESEARCH_CAVEAT
    assert [r["horizon"] for r in payload["by_horizon"]] == list(cfg.walk_forward.horizons)
    for r in payload["by_horizon"]:
        assert {
            "horizon", "n", "low_sample", "mean_return", "median", "pct_positive", "dispersion",
            "expectancy", "mean_mae", "mean_mfe", "return_per_downside_dev", "return_per_mae",
        } <= set(r)
