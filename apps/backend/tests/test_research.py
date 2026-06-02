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
    _rank_ic,
    _risk_adjusted,
    compute_factor_lab,
    factor_catalog,
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
):
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector=sector,
        leadership_score=lead, leadership_bucket=bucket,
        entry_quality_score=entry, entry_quality_bucket=bucket,
        risk_score=risk, risk_bucket=bucket,
        setup_status=setup, rank=rank, record_json=record_json,
    ))


def _add_fr(session, run_id, symbol, ret, horizon=H):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret,
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
