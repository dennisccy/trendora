"""Research samples drill-down engine (iter-7 goal-mode, J-51 / J-52) — `app.engine.samples`.

The keystone proof is COUNT COHERENCE (coherence-auditor invariant 13): for every published `N=` chip
kind/slice on `/research`, the samples drill-down `total` EQUALS the n the corresponding aggregate
endpoint publishes under identical params — because membership is derived through the SAME observation
builders + the SAME slicing helpers the aggregates use (never a second membership rule). Also proven:
value-identity (row values are the stored per-observation inputs the aggregate consumed), the honest
n=0 strict-overlap case (empty list + total 0, never a fabricated row), the as_of-scoped mode, and the
explicit ValueError on an invalid cohort selector.

All math runs on tiny hand-built in-memory data — the engine READS stored rows, so no scan is needed.
The fixture helpers mirror `test_research.py` (one membership/value definition, asserted against it).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session

import app.engine.market_phase as market_phase
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.research import (
    compute_event_study,
    compute_factor_combination,
    compute_factor_lab,
    compute_phase_severity_lab,
    compute_regime_lab,
)
from app.engine.samples import KIND_PHASE_SEVERITY_LAB, KIND_REGIME_LAB, compute_samples
from app.models import ForwardReturn, ScannerResult, ScannerRun

H = 20  # a real config horizon used throughout


# ==================================================================================================
# Hand-built snapshot fixtures (no engine — exact values by construction; mirrors test_research.py)
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
        hv=hv, vcp_contraction=vcp_contraction, downside_vol=downside_vol,
        is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback_to_rising_dma,
        is_flat_base_breakout=is_flat_base_breakout,
    ))


def _add_fr(session, run_id, symbol, ret, horizon=H, mae=None, mfe=None):
    session.add(ForwardReturn(
        run_id=run_id, symbol=symbol, horizon=horizon, asof_date=date(2025, 1, 1),
        entry_close=100.0, measured_date=date(2025, 2, 1), realized_return=ret,
        mae=mae, mfe=mfe,
    ))


def _engine(tmp_path, name="samples.db"):
    engine = make_engine(f"sqlite:///{tmp_path / name}")
    create_db_and_tables(engine)
    return engine


@pytest.fixture()
def factor_engine(tmp_path):
    """20 stocks (leadership 1..20, return = score/1000) in ONE Risk-on run — a monotone factor so the
    deciles are well populated. The exact fixture the Factor-Lab decile/IC tests use."""
    engine = _engine(tmp_path, "factor.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i in range(1, 21):
            _add_result(session, run.id, f"S{i:02d}", rank=i, lead=float(i))
            _add_fr(session, run.id, f"S{i:02d}", ret=i / 1000)
        session.commit()
    return engine


@pytest.fixture()
def multi_regime_engine(tmp_path):
    """12 Risk-on + 8 Risk-off observations across two runs (different stored regime labels)."""
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


@pytest.fixture()
def event_study_engine(tmp_path):
    """A pooled cohort for the Breakout-watch setup across two regimes + two sectors, plus a different
    setup (Actionable) so the subject filter is exercised. Each member has a realized return."""
    engine = _engine(tmp_path, "eventstudy.db")
    with Session(engine) as session:
        run_on = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        run_off = _add_run(session, date(2025, 2, 10), regime_label="Risk-off")
        # Breakout-watch members: 4 Risk-on (Tech), 3 Risk-off (Energy)
        for i in range(1, 5):
            _add_result(session, run_on.id, f"B{i}", rank=i, setup="Breakout-watch", sector="Technology")
            _add_fr(session, run_on.id, f"B{i}", ret=i / 100)
        for i in range(1, 4):
            _add_result(session, run_off.id, f"E{i}", rank=i, setup="Breakout-watch", sector="Energy")
            _add_fr(session, run_off.id, f"E{i}", ret=-i / 100)
        # a different setup so the pool is filtered, not "everything"
        _add_result(session, run_on.id, "X1", rank=9, setup="Actionable", sector="Technology")
        _add_fr(session, run_on.id, "X1", ret=0.5)
        session.commit()
    return engine


# ==================================================================================================
# Factor cohort count-coherence + value-identity
# ==================================================================================================
def test_factor_total_coherence_and_value_identity(factor_engine):
    """The `n_total` (== rank-IC n) chip: the samples total equals `compute_factor_lab.n_total`, and each
    row carries the SAME stored factor value + realized return + snapshot date the aggregate pooled."""
    cfg = load_config()
    with Session(factor_engine) as session:
        agg = compute_factor_lab(session, "leadership_score", H, cfg)
        s = compute_samples(
            session, kind="factor", horizon=H, config=cfg,
            factor_key="leadership_score", slice_kind="total",
        )
    assert s["total"] == agg["n_total"] == 20
    # value identity: leadership 1..20 read verbatim, return = score/1000, all from the one 2025-01-10 run
    by_ticker = {r["ticker"]: r for r in s["rows"]}
    assert by_ticker["S05"]["values"][0]["value"] == pytest.approx(5.0)
    assert by_ticker["S05"]["values"][0]["key"] == "leadership_score"
    assert by_ticker["S05"]["forward_return"] == pytest.approx(5 / 1000)
    assert by_ticker["S05"]["snapshot_date"] == "2025-01-10"


def test_factor_decile_coherence_for_every_decile(factor_engine):
    """Per-decile chip: for EVERY D1…D10 the samples total equals that decile's published `n`, and the
    union of all deciles' member tickers equals the whole pool (no double-count, no drop)."""
    cfg = load_config()
    with Session(factor_engine) as session:
        agg = compute_factor_lab(session, "leadership_score", H, cfg)
        all_tickers: set[str] = set()
        for row in agg["deciles"]:
            s = compute_samples(
                session, kind="factor", horizon=H, config=cfg,
                factor_key="leadership_score", slice_kind="decile", decile=row["decile"],
            )
            assert s["total"] == row["n"], f"decile {row['decile']} coherence"
            all_tickers |= {r["ticker"] for r in s["rows"]}
    assert all_tickers == {f"S{i:02d}" for i in range(1, 21)}
    # D10 (highest factor) holds the two highest leadership scores by construction
    with Session(factor_engine) as session:
        d10 = compute_samples(
            session, kind="factor", horizon=H, config=cfg,
            factor_key="leadership_score", slice_kind="decile", decile=10,
        )
    assert {r["ticker"] for r in d10["rows"]} == {"S19", "S20"}


def test_factor_by_regime_coherence(multi_regime_engine):
    """By-regime chip: the samples total for each regime equals that by-regime row's published `n`."""
    cfg = load_config()
    with Session(multi_regime_engine) as session:
        agg = compute_factor_lab(session, "leadership_score", H, cfg)
        n_by_regime = {r["regime"]: r["n"] for r in agg["by_regime"]}
        for label in ("Risk-on", "Risk-off"):
            s = compute_samples(
                session, kind="factor", horizon=H, config=cfg,
                factor_key="leadership_score", slice_kind="regime", regime=label,
            )
            assert s["total"] == n_by_regime[label]
            assert all(r["regime"] == label for r in s["rows"])
    assert n_by_regime["Risk-on"] == 12 and n_by_regime["Risk-off"] == 8


# ==================================================================================================
# Regime-Lab cohort count-coherence (J-110 — by regime LABEL and by regime-score DECILE)
# ==================================================================================================
def test_regime_lab_label_and_decile_coherence(multi_regime_engine):
    """Each Regime-Lab `N=` chip — a regime LABEL row and a regime-score DECILE — drills into a cohort whose
    samples `total` equals the published bucket n (count-coherence keystone), in the pooled view. The
    fixture's two regimes published 12 (Risk-on) / 8 (Risk-off) at H, and the decile totals re-sum to n_total."""
    cfg = load_config()
    with Session(multi_regime_engine) as session:
        payload = compute_regime_lab(session, cfg, view="pooled")
        # by-label coherence at H.
        n_by_label = {}
        for row in payload["by_label"]:
            b = next(b for b in row["by_horizon"] if b["horizon"] == H)
            n_by_label[row["regime"]] = b["n"]
            s = compute_samples(
                session, kind=KIND_REGIME_LAB, horizon=H, config=cfg,
                slice_kind="label", regime=row["regime"], view="pooled",
            )
            assert s["total"] == b["n"], f"label drift {row['regime']}"
            assert all(r["regime"] == row["regime"] for r in s["rows"])
        assert n_by_label["Risk-on"] == 12 and n_by_label["Risk-off"] == 8

        # by-decile coherence at H; the decile totals re-sum to the whole pool (20 observations).
        total = 0
        for row in payload["by_decile"]:
            b = next(b for b in row["by_horizon"] if b["horizon"] == H)
            s = compute_samples(
                session, kind=KIND_REGIME_LAB, horizon=H, config=cfg,
                slice_kind="decile", decile=row["decile"], view="pooled",
            )
            assert s["total"] == b["n"], f"decile drift D{row['decile']}"
            total += b["n"]
        assert total == 20  # 12 Risk-on + 8 Risk-off, every observation in exactly one decile


# ==================================================================================================
# Phase & Severity-Lab cohort count-coherence (J-111 — by market-phase LABEL and by severity-score DECILE)
# ==================================================================================================
@pytest.fixture()
def phase_severity_engine(tmp_path, monkeypatch):
    """12 Expansion + 8 Bear observations across two runs, with the served `market_phase` timeline
    monkeypatched so the 2025-01-10 run reads (Expansion, severity 10) and the 2025-02-10 run reads
    (Bear, severity 85) — the SAME isolation `test_severity_velocity.py` uses for the served-velocity join."""
    engine = _engine(tmp_path, "phasesev.db")
    with Session(engine) as session:
        run_exp = _add_run(session, date(2025, 1, 10))
        run_bear = _add_run(session, date(2025, 2, 10))
        for i in range(1, 13):
            _add_result(session, run_exp.id, f"N{i:02d}", rank=i, lead=float(i))
            _add_fr(session, run_exp.id, f"N{i:02d}", ret=i / 1000)
        for i in range(1, 9):
            _add_result(session, run_bear.id, f"F{i:02d}", rank=i, lead=float(i))
            _add_fr(session, run_bear.id, f"F{i:02d}", ret=-i / 1000)
        session.commit()

    ctx = {
        "2025-01-10": {"phase": "Expansion", "severity": 10.0, "p_bear": 0.0},
        "2025-02-10": {"phase": "Bear", "severity": 85.0, "p_bear": 1.0},
    }

    def _fake_phase_ctx(session, as_of=None, config=None):
        if as_of is None:
            return {d: dict(v) for d, v in ctx.items()}
        return {d: dict(v) for d, v in ctx.items() if date.fromisoformat(d) <= as_of}

    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_phase_ctx)
    return engine


def test_phase_severity_lab_label_and_decile_coherence(phase_severity_engine):
    """Each Phase & Severity-Lab `N=` chip — a market-phase LABEL row and a severity-score DECILE — drills into
    a cohort whose samples `total` equals the published bucket n (count-coherence keystone), in the pooled view.
    The fixture's two phases published 12 (Expansion) / 8 (Bear) at H; the decile totals re-sum to n_total."""
    cfg = load_config()
    with Session(phase_severity_engine) as session:
        payload = compute_phase_severity_lab(session, cfg, view="pooled")
        # by-label coherence at H.
        n_by_label = {}
        for row in payload["by_label"]:
            b = next(b for b in row["by_horizon"] if b["horizon"] == H)
            n_by_label[row["phase"]] = b["n"]
            s = compute_samples(
                session, kind=KIND_PHASE_SEVERITY_LAB, horizon=H, config=cfg,
                slice_kind="label", phase=row["phase"], view="pooled",
            )
            assert s["total"] == b["n"], f"label drift {row['phase']}"
            assert all(r["phase"] == row["phase"] for r in s["rows"])
        assert n_by_label["Expansion"] == 12 and n_by_label["Bear"] == 8

        # by-decile coherence at H; the decile totals re-sum to the whole classified pool (20 observations).
        total = 0
        for row in payload["by_decile"]:
            b = next(b for b in row["by_horizon"] if b["horizon"] == H)
            s = compute_samples(
                session, kind=KIND_PHASE_SEVERITY_LAB, horizon=H, config=cfg,
                slice_kind="decile", decile=row["decile"], view="pooled",
            )
            assert s["total"] == b["n"], f"decile drift D{row['decile']}"
            total += b["n"]
        assert total == 20  # 12 Expansion + 8 Bear, every observation in exactly one severity decile


# ==================================================================================================
# Combination cohort count-coherence (baseline / single / composite / strict-overlap incl. n=0)
# ==================================================================================================
def test_combination_cohort_coherence_all_kinds(factor_engine):
    """Every combination chip — baseline / each single / composite / strict-overlap — has a samples total
    equal to the aggregate's published n. Uses the config default conditions (the default chips)."""
    cfg = load_config()
    comb = cfg.research.factor_lab.combination
    conditions = [
        {"factor": c.factor, "side": c.side, "quantile": c.quantile} for c in comb.default_conditions
    ]
    with Session(factor_engine) as session:
        agg = compute_factor_combination(session, conditions, H, cfg)
        # baseline == pool_n
        base = compute_samples(
            session, kind="combination", horizon=H, config=cfg,
            conditions=conditions, cohort_kind="baseline",
        )
        assert base["total"] == agg["pool_n"] == agg["baseline"]["stats"]["n"]
        # each single
        for idx, single in enumerate(agg["singles"]):
            s = compute_samples(
                session, kind="combination", horizon=H, config=cfg,
                conditions=conditions, cohort_kind="single", single_index=idx,
            )
            assert s["total"] == single["stats"]["n"], f"single {idx} coherence"
        # composite
        comp = compute_samples(
            session, kind="combination", horizon=H, config=cfg,
            conditions=conditions, cohort_kind="composite",
        )
        assert comp["total"] == agg["composite"]["stats"]["n"]
        # strict overlap
        strict = compute_samples(
            session, kind="combination", horizon=H, config=cfg,
            conditions=conditions, cohort_kind="strict_overlap",
        )
        assert strict["total"] == agg["strict_overlap"]["stats"]["n"]


def test_combination_strict_overlap_zero_is_honest_empty(tmp_path):
    """The n=0 strict-overlap case (opposing extremes of the same factor → empty AND-intersection): the
    aggregate publishes n=0 and the samples drill-down returns an empty `rows` + `total` 0 — never a
    fabricated row (anti-goal: No fabricated data)."""
    cfg = load_config()
    engine = _engine(tmp_path, "strictzero.db")
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10))
        for i in range(1, 11):
            _add_result(session, run.id, f"S{i}", rank=i, lead=float(i))
            _add_fr(session, run.id, f"S{i}", ret=i / 1000)
        session.commit()
    # top AND bottom of the SAME factor → the strict intersection is empty
    q = cfg.research.factor_lab.combination.quantiles[0].key
    conditions = [
        {"factor": "leadership_score", "side": "top", "quantile": q},
        {"factor": "leadership_score", "side": "bottom", "quantile": q},
    ]
    with Session(engine) as session:
        agg = compute_factor_combination(session, conditions, H, cfg)
        s = compute_samples(
            session, kind="combination", horizon=H, config=cfg,
            conditions=conditions, cohort_kind="strict_overlap",
        )
    assert agg["strict_overlap"]["stats"]["n"] == 0
    assert s["total"] == 0 and s["rows"] == []


def test_combination_row_carries_every_referenced_factor_value(factor_engine):
    """Value identity for a combination row: every referenced factor's STORED value rides each row
    (read verbatim), keyed by the catalog factor key."""
    cfg = load_config()
    q = cfg.research.factor_lab.combination.quantiles[0].key
    # two DISTINCT factors so the pool requires both non-null and each row carries both stored values
    conditions = [
        {"factor": "leadership_score", "side": "top", "quantile": q},
        {"factor": "risk_score", "side": "top", "quantile": q},
    ]
    with Session(factor_engine) as session:
        s = compute_samples(
            session, kind="combination", horizon=H, config=cfg,
            conditions=conditions, cohort_kind="baseline",
        )
    assert s["total"] == 20  # leadership + risk both non-null on all 20 stocks
    row = next(r for r in s["rows"] if r["ticker"] == "S20")
    keys = {v["key"]: v["value"] for v in row["values"]}
    assert keys["leadership_score"] == pytest.approx(20.0)
    assert keys["risk_score"] == pytest.approx(50.0)  # the fixture's default risk score
    assert row["forward_return"] == pytest.approx(20 / 1000)


# ==================================================================================================
# Event-study cohort count-coherence (pooled / by-regime / by-sector)
# ==================================================================================================
def test_event_study_pooled_coherence_and_subject_value(event_study_engine):
    """Pooled chip (== `n_total` / per-horizon n): the samples total equals `compute_event_study.n_total`
    for the Breakout-watch subject; each row's value is the matched subject (read-only)."""
    cfg = load_config()
    with Session(event_study_engine) as session:
        agg = compute_event_study(session, "Breakout-watch", H, cfg)
        s = compute_samples(
            session, kind="event-study", horizon=H, config=cfg,
            subject_key="Breakout-watch", slice_kind="pooled",
        )
    assert s["total"] == agg["n_total"] == 7  # 4 Risk-on + 3 Risk-off Breakout-watch members
    assert all(r["values"][0]["key"] == "Breakout-watch" for r in s["rows"])
    # the lone Actionable member must NOT leak into the Breakout-watch pool
    assert "X1" not in {r["ticker"] for r in s["rows"]}


def test_event_study_by_regime_and_by_sector_coherence(event_study_engine):
    """By-regime and by-sector chips: each slice's samples total equals the published per-regime /
    per-sector `n`."""
    cfg = load_config()
    with Session(event_study_engine) as session:
        agg = compute_event_study(session, "Breakout-watch", H, cfg)
        n_by_regime = {r["regime"]: r["n"] for r in agg["by_regime"]}
        n_by_sector = {r["sector"]: r["n"] for r in agg["by_sector"]}
        for label in ("Risk-on", "Risk-off"):
            s = compute_samples(
                session, kind="event-study", horizon=H, config=cfg,
                subject_key="Breakout-watch", slice_kind="regime", regime=label,
            )
            assert s["total"] == n_by_regime[label]
        for sector in ("Technology", "Energy"):
            s = compute_samples(
                session, kind="event-study", horizon=H, config=cfg,
                subject_key="Breakout-watch", slice_kind="sector", sector=sector,
            )
            assert s["total"] == n_by_sector[sector]
    # the populated slices (by-regime emits a row per configured label incl. 0; by-sector is non-padded)
    assert n_by_regime["Risk-on"] == 4 and n_by_regime["Risk-off"] == 3
    assert n_by_sector == {"Technology": 4, "Energy": 3}


# ==================================================================================================
# as_of-scoped mode coherence (J-32) — the single global as-of, a membership filter not a 2nd date
# ==================================================================================================
def test_as_of_scoping_matches_aggregate(multi_regime_engine):
    """With `as_of` = the earlier run date, BOTH the factor aggregate and the samples drill-down pool ONLY
    the snapshots dated <= D — and the samples total still equals the as-of-scoped published `n_total`."""
    cfg = load_config()
    cutoff = date(2025, 1, 10)  # the Risk-on run only (the Risk-off run is dated 2025-02-10 > D)
    with Session(multi_regime_engine) as session:
        agg = compute_factor_lab(session, "leadership_score", H, cfg, as_of=cutoff)
        s = compute_samples(
            session, kind="factor", horizon=H, config=cfg, as_of=cutoff,
            factor_key="leadership_score", slice_kind="total",
        )
    assert agg["n_total"] == 12  # only the 12 Risk-on observations are <= D
    assert s["total"] == agg["n_total"] == 12
    assert s["asof_date"] == "2025-01-10"
    assert all(r["snapshot_date"] == "2025-01-10" for r in s["rows"])


# ==================================================================================================
# Invalid cohort selectors → ValueError (the API turns these into an explicit 4xx, never a silent 200)
# ==================================================================================================
def test_invalid_selectors_raise(factor_engine):
    """Unknown kind/factor/subject, out-of-range decile, bad single index, malformed slice all raise
    ValueError (not a silent empty result) — the 4xx contract (an empty 200 is reserved for valid n=0)."""
    cfg = load_config()
    with Session(factor_engine) as session:
        with pytest.raises(ValueError):
            compute_samples(session, kind="not-a-kind", horizon=H, config=cfg)
        with pytest.raises(ValueError):
            compute_samples(session, kind="factor", horizon=H, config=cfg,
                            factor_key="nope", slice_kind="total")
        with pytest.raises(ValueError):
            compute_samples(session, kind="factor", horizon=H, config=cfg,
                            factor_key="leadership_score", slice_kind="decile", decile=999)
        with pytest.raises(ValueError):
            compute_samples(session, kind="event-study", horizon=H, config=cfg,
                            subject_key="not-a-subject", slice_kind="pooled")
        with pytest.raises(ValueError):
            compute_samples(
                session, kind="combination", horizon=H, config=cfg,
                conditions=[{"factor": "leadership_score", "side": "top",
                             "quantile": cfg.research.factor_lab.combination.quantiles[0].key}],
                cohort_kind="single", single_index=99,
            )


# ==================================================================================================
# J-63 — Event-study EPISODES ⇄ POOLED count-coherence in the samples drill-down (both modes). The
# drill-down reuses the SAME episode-collapse builder the aggregate uses, so total == published n in
# BOTH views (never a second grouping path); a continuous run drills to ONE first-trigger row.
# ==================================================================================================
@pytest.fixture()
def episode_samples_engine(tmp_path):
    """A VCP subject that PERSISTS across consecutive snapshots so episodes < pooled. Four stored
    run-dates (global ordinals 0..3): PERSIST is VCP on the first 3 (one continuous run → 1 episode at its
    first trigger), GAP is VCP on ordinals 0 and 2 (→ 2 episodes), ONESHOT is VCP on ordinal 3 (→ 1).
    Pooled VCP signal-days = 6; episodes = 4."""
    engine = _engine(tmp_path, "episode_samples.db")
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), regime_label="Risk-on")
        r2 = _add_run(session, date(2025, 1, 17), regime_label="Risk-on")
        r3 = _add_run(session, date(2025, 1, 24), regime_label="Risk-off")
        r4 = _add_run(session, date(2025, 1, 31), regime_label="Risk-on")
        rows = [
            ("PERSIST", r1, True,  0.11, "Technology"),
            ("PERSIST", r2, True,  0.12, "Technology"),
            ("PERSIST", r3, True,  0.13, "Technology"),
            ("GAP",     r1, True,  0.31, "Energy"),
            ("GAP",     r3, True,  0.33, "Energy"),
            ("ONESHOT", r4, True,  0.40, "Technology"),
        ]
        rank = 0
        for tkr, run, is_vcp, ret, sector in rows:
            rank += 1
            _add_result(session, run.id, tkr, rank=rank, setup="Actionable", is_vcp=is_vcp, sector=sector)
            _add_fr(session, run.id, tkr, ret, mae=-0.05, mfe=0.20)
        session.commit()
    return engine


def test_event_study_samples_count_coherence_both_views(episode_samples_engine):
    """Count-coherence in BOTH views (J-63): for the SAME (subject, horizon) the samples pooled total
    equals the event-study `n` under `view="episodes"` (4) AND under `view="pooled"` (6) — asserted
    SAME-INSTANT against the live aggregate, never a hardcoded N. Episodes < pooled here (a persisting
    subject), proving the drill-down honours the mode."""
    cfg = load_config()
    with Session(episode_samples_engine) as session:
        for view, expected in (("episodes", 4), ("pooled", 6)):
            agg = compute_event_study(session, "vcp", H, cfg, view=view)
            s = compute_samples(
                session, kind="event-study", horizon=H, config=cfg,
                subject_key="vcp", slice_kind="pooled", view=view,
            )
            assert agg["n"] == expected               # the aggregate's mode-dependent n
            assert s["total"] == agg["n"] == expected  # SAME-INSTANT count-coherence in this mode
            assert s["cohort"]["view"] == view


def test_event_study_samples_episodes_drilldown_is_first_trigger_rows(episode_samples_engine):
    """The episodes-mode drill-down lists the FIRST-TRIGGER rows (one row per continuous run), so the
    PERSIST continuous run appears as exactly ONE row at its first trigger date (2025-01-10) — NOT three.
    The pooled-mode drill-down lists all three PERSIST signal-days."""
    cfg = load_config()
    with Session(episode_samples_engine) as session:
        episodes = compute_samples(
            session, kind="event-study", horizon=H, config=cfg,
            subject_key="vcp", slice_kind="pooled", view="episodes",
        )
        pooled = compute_samples(
            session, kind="event-study", horizon=H, config=cfg,
            subject_key="vcp", slice_kind="pooled", view="pooled",
        )
    ep_persist = [r for r in episodes["rows"] if r["ticker"] == "PERSIST"]
    pool_persist = [r for r in pooled["rows"] if r["ticker"] == "PERSIST"]
    assert len(ep_persist) == 1 and ep_persist[0]["snapshot_date"] == "2025-01-10"  # ONE first-trigger row
    assert len(pool_persist) == 3  # pooled keeps every signal-day
    # GAP appears twice in BOTH modes (a real ordinal gap → two genuine episodes)
    assert len([r for r in episodes["rows"] if r["ticker"] == "GAP"]) == 2


def test_event_study_samples_pooled_view_byte_identical_membership(episode_samples_engine):
    """Byte-identity at the samples layer: `view="pooled"` reproduces the exact pre-J-63 member list
    (the unchanged `_event_study_members` rows) — same tickers, snapshot dates, and forward returns —
    so the prior drill-down is preserved one toggle away."""
    cfg = load_config()
    with Session(episode_samples_engine) as session:
        pooled = compute_samples(
            session, kind="event-study", horizon=H, config=cfg,
            subject_key="vcp", slice_kind="pooled", view="pooled",
        )
    got = sorted((r["ticker"], r["snapshot_date"], round(r["forward_return"], 4)) for r in pooled["rows"])
    assert got == sorted([
        ("PERSIST", "2025-01-10", 0.11), ("PERSIST", "2025-01-17", 0.12), ("PERSIST", "2025-01-24", 0.13),
        ("GAP", "2025-01-10", 0.31), ("GAP", "2025-01-24", 0.33), ("ONESHOT", "2025-01-31", 0.40),
    ])


def test_event_study_samples_default_view_is_episodes(episode_samples_engine):
    """The samples drill-down DEFAULTS to episodes (matching the aggregate default): no `view` → 4 rows."""
    cfg = load_config()
    with Session(episode_samples_engine) as session:
        default = compute_samples(
            session, kind="event-study", horizon=H, config=cfg,
            subject_key="vcp", slice_kind="pooled",
        )
    assert default["total"] == 4 and default["cohort"]["view"] == "episodes"


def test_event_study_samples_unknown_view_raises(episode_samples_engine):
    """An unknown event-study `view` raises ValueError (the API → 422), mirroring the aggregate."""
    cfg = load_config()
    with Session(episode_samples_engine) as session:
        with pytest.raises(ValueError, match="unknown view"):
            compute_samples(
                session, kind="event-study", horizon=H, config=cfg,
                subject_key="vcp", slice_kind="pooled", view="bogus",
            )
