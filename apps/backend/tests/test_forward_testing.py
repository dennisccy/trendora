"""Walk-forward forward-testing engine — the critical-anti-goal proofs (iter-6).

Named proofs, each guarding a critical anti-goal:
  - bars_after / close_on boundary  — the forward side reads ONLY bars with date > D.   *(No lookahead)*
  - forward_return purity           — h-th post-bar, NA when short, unchanged by later bars. *(No lookahead)*
  - aggregates read stored bucket   — grouping uses the STORED leadership_bucket verbatim.  *(Single source)*
  - aggregates exact means          — by-bucket/setup/regime/excess/control on a hand fixture.
  - control-group determinism       — same config seed -> identical random cohort.
  - no fabrication                  — zero-post-bar run = n=0; both regimes present.       *(No fabricated data)*
  - backfill INSERT-only+idempotent — no UPDATE of any snapshot row; 2nd backfill inserts 0. *(Snapshots immutable)*
  - scores never fed back           — a run's stored scores are identical with/without forward returns. *(No lookahead)*

The pure / hand-fixture tests run on tiny in-memory data (fast). The backfill integration proof runs the
real engines on the committed seed under a REDUCED walk-forward cadence (module-scoped, once).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from statistics import stdev

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import (
    backfill_forward_returns,
    compute_forward_aggregates,
    forward_return,
    walk_forward_asof_dates,
)
from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
from app.engine.scanner import run_scan
from app.models import (
    DailyPrice,
    ForwardReturn,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)
from app.seed_loader import load_seed


# ==================================================================================================
# Pure helpers / tiny stand-ins
# ==================================================================================================
class _Bar:
    """A minimal post-snapshot bar stand-in for the pure forward_return tests (only `.close` matters)."""

    def __init__(self, close: float, d: date | None = None):
        self.close = close
        self.date = d


def _bars(closes: list[float]) -> list[_Bar]:
    return [_Bar(c) for c in closes]


# ==================================================================================================
# bars_after / close_on — the forward no-lookahead boundary
# ==================================================================================================
@pytest.fixture()
def tiny_price_engine(tmp_path):
    """A temp DB with one symbol's bars on five known dates (no engine, no seed)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'tiny.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]
    with Session(engine) as session:
        for i, d in enumerate(days):
            close = float(10 + i)  # 10, 11, 12, 13, 14
            session.add(DailyPrice(symbol="AAA", date=d, open=close, high=close, low=close, close=close, volume=1.0))
        session.commit()
    return engine, days


def test_bars_after_returns_only_future_bars_ascending(tiny_price_engine):
    """No-lookahead (forward): bars_after(D) returns ONLY bars with date > D, ascending, and never a
    bar with date <= D — and it partitions the history with bars_asof at exactly D (no overlap)."""
    engine, days = tiny_price_engine
    d = days[1]  # 2024-01-03
    with Session(engine) as session:
        after = bars_after(session, "AAA", d)
        asof = bars_asof(session, "AAA", d)

    assert [b.date for b in after] == days[2:]  # strictly the later dates, ascending
    assert all(b.date > d for b in after)
    assert all(b.date <= d for b in asof)
    # disjoint + complete partition at D (this disjointness IS the no-lookahead guarantee)
    assert {b.date for b in asof}.isdisjoint({b.date for b in after})
    assert {b.date for b in asof} | {b.date for b in after} == set(days)


def test_bars_after_limit_is_the_unbounded_prefix(tiny_price_engine):
    """The bounded backfill call equals the unbounded boundary truncated to `limit` (same bars)."""
    engine, days = tiny_price_engine
    d = days[0]
    with Session(engine) as session:
        full = bars_after(session, "AAA", d)
        limited = bars_after(session, "AAA", d, limit=2)
    assert [b.date for b in limited] == [b.date for b in full[:2]]
    assert [b.close for b in limited] == [b.close for b in full[:2]]


def test_close_on_is_the_asof_close(tiny_price_engine):
    """close_on(D) is the close of the latest bar with date <= D (the entry close on D)."""
    engine, days = tiny_price_engine
    with Session(engine) as session:
        assert close_on(session, "AAA", days[2]) == 12.0  # the bar ON 2024-01-04
        # a non-trading gap date resolves to the latest prior bar (<= D)
        assert close_on(session, "AAA", date(2024, 1, 7)) == 13.0  # latest <= 2024-01-07 is 2024-01-05
        assert close_on(session, "AAA", date(2023, 12, 31)) is None  # before all data
        assert close_on(session, "MISSING", days[0]) is None


# ==================================================================================================
# forward_return — pure no-lookahead math
# ==================================================================================================
def test_forward_return_uses_the_hth_post_bar():
    """Realized return over h days = close of the h-th POST-snapshot bar / entry_close - 1."""
    post = _bars([110.0, 121.0, 133.0])  # entry 100 -> +10% / +21% / +33%
    assert forward_return(post, 100.0, 1) == pytest.approx(0.10)
    assert forward_return(post, 100.0, 2) == pytest.approx(0.21)
    assert forward_return(post, 100.0, 3) == pytest.approx(0.33)


def test_forward_return_is_na_when_fewer_than_h_post_bars():
    """NA (None) — never a fabricated/truncated number — when fewer than h post-bars exist."""
    post = _bars([110.0, 120.0])
    assert forward_return(post, 100.0, 3) is None
    assert forward_return([], 100.0, 1) is None


def test_forward_return_unchanged_when_later_bars_removed():
    """Only the first h post-bars matter: removing bars dated > d+h does not change the h-day return
    (the keystone no-lookahead-of-the-future-tail proof)."""
    full = _bars([110.0, 121.0, 133.0, 145.0, 160.0])
    truncated = _bars([110.0, 121.0, 133.0])  # everything after the 3rd post-bar removed
    assert forward_return(full, 100.0, 3) == forward_return(truncated, 100.0, 3) == pytest.approx(0.33)


def test_forward_return_na_on_missing_or_zero_entry():
    post = _bars([110.0])
    assert forward_return(post, None, 1) is None
    assert forward_return(post, 0.0, 1) is None


# ==================================================================================================
# Hand-built snapshot fixture for the aggregation proofs (no engine — exact values by construction)
# ==================================================================================================
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof,
        created_at=_utc(),
        provider="seed",
        benchmark="SPY",
        regime_score=50.0,
        regime_label=regime_label,
        regime_components_json="[]",
        new_high_low_json="{}",
        candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(session, run_id, ticker, bucket, setup, sector, rank, lead_score=50.0, is_vcp=False):
    session.add(
        ScannerResult(
            run_id=run_id, ticker=ticker, name=ticker, sector=sector,
            leadership_score=lead_score, leadership_bucket=bucket,
            entry_quality_score=0.0, entry_quality_bucket="E",
            risk_score=0.0, risk_bucket="E",
            setup_status=setup, rank=rank, record_json="{}", is_vcp=is_vcp,
        )
    )


def _add_fr(session, run_id, symbol, horizon, ret):
    session.add(
        ForwardReturn(
            run_id=run_id, symbol=symbol, horizon=horizon,
            asof_date=date(2025, 1, 1), entry_close=100.0,
            measured_date=date(2025, 2, 1), realized_return=ret,
        )
    )


@pytest.fixture()
def aggregates_engine(tmp_path):
    """A hand-built two-run snapshot with known forward returns at horizon H, plus a third run with NO
    forward returns (the n=0 case). Tech sector ETF = XLK, Energy = XLE (real config mapping)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'agg.db'}")
    create_db_and_tables(engine)
    H = 20
    with Session(engine) as session:
        # run1 — Risk-on
        r1 = _add_run(session, date(2025, 1, 10), "Risk-on")
        _add_result(session, r1.id, "AAA", "A", "Actionable", "Technology", 1)
        _add_result(session, r1.id, "BBB", "A", "Breakout-watch", "Technology", 2)
        _add_result(session, r1.id, "CCC", "E", "Avoid", "Technology", 3)
        _add_result(session, r1.id, "DDD", "E", "Avoid", "Energy", 4)
        for sym, ret in [("AAA", 0.10), ("BBB", 0.20), ("CCC", 0.00), ("DDD", -0.10),
                         ("SPY", 0.05), ("QQQ", 0.06), ("XLK", 0.04), ("XLE", -0.02)]:
            _add_fr(session, r1.id, sym, H, ret)
        # run2 — Risk-off
        r2 = _add_run(session, date(2024, 7, 10), "Risk-off")
        _add_result(session, r2.id, "AAA", "B", "Pullback-watch", "Technology", 1)
        _add_result(session, r2.id, "EEE", "E", "Risk-off-watchlist", "Technology", 2)
        for sym, ret in [("AAA", 0.30), ("EEE", 0.10), ("SPY", 0.08), ("QQQ", 0.07), ("XLK", 0.05)]:
            _add_fr(session, r2.id, sym, H, ret)
        # run3 — no forward returns at all (the n=0 / zero-post-bar demonstration)
        r3 = _add_run(session, date(2026, 5, 1), "Risk-on")
        _add_result(session, r3.id, "AAA", "A", "Actionable", "Technology", 1)
        session.commit()
    return engine, H


def _by(rows, key, value):
    for row in rows:
        if row[key] == value:
            return row
    return None


def test_aggregates_by_bucket_setup_regime_exact(aggregates_engine):
    """Exact by-bucket / by-setup / by-regime means + n on the hand fixture (single canonical math)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, cfg)

    # by-bucket A..E always present (padded); means exact
    by_bucket = {r["bucket"]: r for r in agg["by_bucket"]}
    assert [r["bucket"] for r in agg["by_bucket"]] == ["A", "B", "C", "D", "E"]
    assert by_bucket["A"]["n"] == 2 and by_bucket["A"]["mean_return"] == pytest.approx(0.15)  # AAA,BBB
    assert by_bucket["B"]["n"] == 1 and by_bucket["B"]["mean_return"] == pytest.approx(0.30)  # AAA(run2)
    assert by_bucket["C"]["n"] == 0 and by_bucket["C"]["mean_return"] is None
    assert by_bucket["E"]["n"] == 3 and by_bucket["E"]["mean_return"] == pytest.approx(0.0)  # CCC,DDD,EEE

    # by-setup (only non-empty groups)
    assert _by(agg["by_setup"], "setup", "Actionable")["mean_return"] == pytest.approx(0.10)
    assert _by(agg["by_setup"], "setup", "Avoid")["n"] == 2
    assert _by(agg["by_setup"], "setup", "Avoid")["mean_return"] == pytest.approx(-0.05)  # CCC 0, DDD -0.10

    # by-regime — BOTH regimes present (no-fabrication: both Risk-on and Risk-off in the sample)
    regimes = {r["regime"]: r for r in agg["by_regime"]}
    assert "Risk-on" in regimes and "Risk-off" in regimes
    assert regimes["Risk-on"]["n"] == 4 and regimes["Risk-on"]["mean_return"] == pytest.approx(0.05)
    assert regimes["Risk-off"]["n"] == 2 and regimes["Risk-off"]["mean_return"] == pytest.approx(0.20)


def test_aggregates_excess_vs_spy_and_qqq_exact(aggregates_engine):
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())

    # overall stock mean = mean(0.10,0.20,0.00,-0.10,0.30,0.10) = 0.10 over n=6
    assert agg["overall"]["n"] == 6 and agg["overall"]["mean_return"] == pytest.approx(0.10)
    # SPY mean over the two runs = mean(0.05, 0.08) = 0.065 ; excess = 0.10 - 0.065
    assert agg["excess"]["vs_spy"]["benchmark"] == "SPY"
    assert agg["excess"]["vs_spy"]["mean_excess"] == pytest.approx(0.035)
    assert agg["excess"]["vs_spy"]["n"] == 6 and agg["excess"]["vs_spy"]["benchmark_n"] == 2
    # QQQ mean = mean(0.06, 0.07) = 0.065 ; excess = 0.035
    assert agg["excess"]["vs_qqq"]["mean_excess"] == pytest.approx(0.035)


def test_aggregates_control_groups(aggregates_engine):
    """Control-group cohorts: top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF, each numeric+n."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    cg = {c["key"]: c for c in agg["control_group"]}
    assert set(cg) == {"top_ranked", "random_same_sector", "spy", "qqq", "sector_etf"}

    # top_n=20 (config) covers every rank -> top-ranked cohort = all 6 stock observations
    assert cg["top_ranked"]["n"] == 6 and cg["top_ranked"]["mean_return"] == pytest.approx(0.10)
    # SPY/QQQ controls = the per-run benchmark returns
    assert cg["spy"]["n"] == 2 and cg["spy"]["mean_return"] == pytest.approx(0.065)
    assert cg["qqq"]["n"] == 2 and cg["qqq"]["mean_return"] == pytest.approx(0.065)
    # sector-ETF control = XLK (run1+run2) and XLE (run1) for the sectors the top cohort occupies
    assert cg["sector_etf"]["n"] == 3 and cg["sector_etf"]["mean_return"] == pytest.approx((0.04 + 0.05 - 0.02) / 3)
    # random same-sector cohort: numeric, with n, and labelled
    assert cg["random_same_sector"]["n"] >= 1
    assert cg["random_same_sector"]["mean_return"] is not None
    assert "random" in cg["random_same_sector"]["label"].lower()


def test_aggregates_group_by_stored_bucket_not_rescored(tmp_path):
    """Single-source: by-bucket grouping uses the STORED leadership_bucket VERBATIM — never re-derived
    from the score. A row whose stored bucket contradicts its score is grouped by the STORED bucket."""
    engine = make_engine(f"sqlite:///{tmp_path / 'verbatim.db'}")
    create_db_and_tables(engine)
    H = 20
    with Session(engine) as session:
        run = _add_run(session, date(2025, 3, 3), "Risk-on")
        # X: a 95-score row STORED as bucket E ; Y: a 5-score row STORED as bucket A (deliberately inverted)
        _add_result(session, run.id, "X", "E", "Avoid", "Technology", 2, lead_score=95.0)
        _add_result(session, run.id, "Y", "A", "Actionable", "Technology", 1, lead_score=5.0)
        _add_fr(session, run.id, "X", H, 0.11)
        _add_fr(session, run.id, "Y", H, 0.22)
        session.commit()
        agg = compute_forward_aggregates(session, H, load_config())

    by_bucket = {r["bucket"]: r for r in agg["by_bucket"]}
    # grouped by STORED bucket: E has X (0.11), A has Y (0.22) — the OPPOSITE of a score re-bucketing
    assert by_bucket["E"]["n"] == 1 and by_bucket["E"]["mean_return"] == pytest.approx(0.11)
    assert by_bucket["A"]["n"] == 1 and by_bucket["A"]["mean_return"] == pytest.approx(0.22)


@pytest.fixture()
def vcp_aggregates_engine(tmp_path):
    """A hand-built run with known forward returns split across the VCP / non-VCP cohorts at horizon
    H, so the by_vcp means are exact by construction (AAA,BBB flagged VCP; CCC non-VCP)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'vcp_agg.db'}")
    create_db_and_tables(engine)
    H = 20
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), "Risk-on")
        _add_result(session, r1.id, "AAA", "A", "Breakout-watch", "Technology", 1, is_vcp=True)
        _add_result(session, r1.id, "BBB", "B", "Pullback-watch", "Technology", 2, is_vcp=True)
        _add_result(session, r1.id, "CCC", "C", "Avoid", "Technology", 3, is_vcp=False)
        for sym, ret in [("AAA", 0.20), ("BBB", 0.10), ("CCC", -0.06), ("SPY", 0.05), ("QQQ", 0.06)]:
            _add_fr(session, r1.id, sym, H, ret)
        session.commit()
    return engine, H


def test_aggregates_by_vcp_exact(vcp_aggregates_engine):
    """by_vcp groups the STORED `is_vcp` flag VERBATIM: the VCP cohort (AAA,BBB) and the non-VCP
    cohort (CCC), each with an exact mean + n; both cohorts always present and labelled."""
    engine, H = vcp_aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    by_vcp = {r["vcp"]: r for r in agg["by_vcp"]}
    assert set(by_vcp) == {"VCP", "non-VCP"}
    assert by_vcp["VCP"]["n"] == 2 and by_vcp["VCP"]["mean_return"] == pytest.approx(0.15)   # (0.20+0.10)/2
    assert by_vcp["non-VCP"]["n"] == 1 and by_vcp["non-VCP"]["mean_return"] == pytest.approx(-0.06)


def test_aggregates_by_vcp_empty_cohort_is_na_padded(aggregates_engine):
    """No fabrication: the base fixture flags NO VCP names, so the VCP cohort is padded n=0 / mean
    None while non-VCP carries all observations — an honest NA, never a fabricated 0%."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    by_vcp = {r["vcp"]: r for r in agg["by_vcp"]}
    assert set(by_vcp) == {"VCP", "non-VCP"}
    assert by_vcp["VCP"]["n"] == 0 and by_vcp["VCP"]["mean_return"] is None
    assert by_vcp["non-VCP"]["n"] == 6  # all six realized observations are non-VCP (default is_vcp=False)


def test_aggregates_zero_post_bar_run_contributes_n0(aggregates_engine):
    """No fabrication: run3 (no forward returns) contributes nothing — n counts only realized returns."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        # run3 has a result (AAA, bucket A) but NO forward_returns -> it must not inflate any n
        total_n = sum(r["n"] for r in compute_forward_aggregates(session, H, load_config())["by_bucket"])
    assert total_n == 6  # exactly the 6 stocks that HAVE a realized return (run1: 4, run2: 2)


def test_control_group_determinism_same_seed_same_cohort(aggregates_engine):
    """Control-group determinism: same config seed -> identical random same-sector cohort across two
    independent computations (reproducible across calls / a simulated restart)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        a = compute_forward_aggregates(session, H, cfg)
    with Session(engine) as session:  # fresh session == a simulated restart
        b = compute_forward_aggregates(session, H, cfg)
    rng_a = next(c for c in a["control_group"] if c["key"] == "random_same_sector")
    rng_b = next(c for c in b["control_group"] if c["key"] == "random_same_sector")
    assert rng_a["n"] == rng_b["n"]
    assert rng_a["mean_return"] == rng_b["mean_return"]


def test_aggregates_carry_survivorship_label_and_min_sample(aggregates_engine):
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    assert "survivorship" in agg["survivorship_bias"].lower()
    assert agg["min_sample"] == load_config().walk_forward.min_sample
    assert agg["horizon"] == H and H in agg["horizons"]


# ==================================================================================================
# walk-forward as-of date set (real seed trading calendar; no run_scan -> cheap)
# ==================================================================================================
def test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon(loaded_engine, config):
    """The cadence as-of set is non-empty, strictly ascending, all real trading days, all far enough
    before the latest date to leave >= max(horizons) post-snapshot bars, and within ~history_years."""
    with Session(loaded_engine) as session:
        asof = walk_forward_asof_dates(session, config)
        latest = latest_data_date(session)
        spy_days = [b.date for b in bars_asof(session, config.etfs.index[0], latest)]

    assert asof, "expected a non-empty walk-forward as-of set on the seed"
    assert asof == sorted(set(asof))  # ascending, de-duplicated
    trading = set(spy_days)
    assert all(d in trading for d in asof)  # only real trading days (no fabricated dates)

    max_h = max(config.walk_forward.horizons)
    index_of = {d: i for i, d in enumerate(spy_days)}
    for d in asof:
        assert len(spy_days) - 1 - index_of[d] >= max_h  # >= max_h post-snapshot bars for every run
    # within (a little slack on) the configured look-back window
    span_years = (latest - asof[0]).days / 365.0
    assert span_years <= config.walk_forward.history_years + 1


# ==================================================================================================
# Backfill integration — INSERT-only, idempotent, snapshot never mutated (reduced cadence, real seed)
# ==================================================================================================
def _fast_cfg():
    """The real config with a REDUCED walk-forward look-back so the backfill scans only a few cadence
    dates (keeps this integration proof fast); everything else (universe, engines) is real."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"history_years": 1, "asof_cadence": "quarterly"})
    return cfg.model_copy(update={"walk_forward": wf})


def _child_fingerprint(session: Session, run_id: int) -> dict:
    """Content-only fingerprint of a run's snapshot children (excludes PKs/FKs) — identical before vs
    after a backfill proves the snapshot was not mutated."""
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run_id).order_by(ScannerResult.rank)
    ).all()
    sectors = session.exec(select(SectorScoreRow).where(SectorScoreRow.run_id == run_id)).all()
    themes = session.exec(select(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id)).all()
    return {
        "results": [r.record_json for r in results],
        "sector_count": len(sectors),
        "theme_count": len(themes),
        "lead_by_ticker": {r.ticker: r.leadership_score for r in results},
    }


@pytest.fixture(scope="module")
def backfilled_engine(tmp_path_factory):
    """Load the seed, capture a pre-existing run's fingerprint, then run the reduced backfill ONCE."""
    cfg = _fast_cfg()
    db_path = tmp_path_factory.mktemp("backfill_db") / "bf.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)

    # a pre-existing snapshot (the latest data date) created BEFORE any forward returns exist
    with Session(engine) as session:
        latest = latest_data_date(session)
        pre_run = run_scan(session, latest, cfg)
        pre_id = pre_run.id
        before = {
            "fingerprint": _child_fingerprint(session, pre_id),
            "n_runs": session.scalar(select(func.count()).select_from(ScannerRun)),
            "n_results": session.scalar(select(func.count()).select_from(ScannerResult)),
            "n_sector_scores": session.scalar(select(func.count()).select_from(SectorScoreRow)),
            "n_theme_scores": session.scalar(select(func.count()).select_from(ThemeScoreRow)),
            "n_forward_returns": session.scalar(select(func.count()).select_from(ForwardReturn)),
        }

    first = backfill_forward_returns(engine, cfg)
    return engine, cfg, latest, pre_id, before, first


def test_backfill_inserts_forward_returns_without_mutating_snapshot(backfilled_engine):
    """Snapshots-immutable: the backfill only INSERTs forward_returns — every pre-existing snapshot row
    is untouched (counts unchanged for runs/results that pre-existed; the pre-existing run's child
    fingerprint is byte-identical before vs after)."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    assert before["n_forward_returns"] == 0  # none existed before the backfill
    assert first["rows_inserted"] > 0  # the backfill inserted realized returns

    with Session(engine) as session:
        after_fp = _child_fingerprint(session, pre_id)
        n_fr = session.scalar(select(func.count()).select_from(ForwardReturn))
    assert after_fp == before["fingerprint"]  # the pre-existing snapshot was NOT mutated
    assert n_fr == first["rows_inserted"]


def test_backfill_is_idempotent(backfilled_engine):
    """A second backfill inserts ZERO new forward_returns and creates no new runs (idempotent)."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    with Session(engine) as session:
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_before = session.scalar(select(func.count()).select_from(ForwardReturn))

    second = backfill_forward_returns(engine, cfg)

    with Session(engine) as session:
        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_after = session.scalar(select(func.count()).select_from(ForwardReturn))
    assert second["rows_inserted"] == 0
    assert runs_after == runs_before
    assert fr_after == fr_before


def test_backfill_latest_run_has_zero_post_bars(backfilled_engine):
    """No fabrication: the latest seed-date run has no post-snapshot bar, so it gets NO forward_returns
    (the natural n=0 demonstration) — never a fabricated 0%."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    with Session(engine) as session:
        latest_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == latest)).one()
        n_fr_latest = session.scalar(
            select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == latest_run.id)
        )
    assert n_fr_latest == 0


# ==================================================================================================
# Return attribution (J-19) — four READ-ONLY slices derived from the SAME stored stock_obs
# ==================================================================================================
def test_attribution_consistency_with_aggregate(aggregates_engine):
    """Read-only consistency (the critical anti-goal): the attribution distribution mean EQUALS the
    existing `overall.mean_return`, and the by-sector / by-rank-band sample sizes each sum to
    `overall.n` — the slices are the SAME observations grouped, never a recomputed return."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    attr, overall = agg["attribution"], agg["overall"]
    assert attr["distribution"]["mean_return"] == pytest.approx(overall["mean_return"])
    assert attr["distribution"]["n"] == overall["n"]
    assert sum(r["n"] for r in attr["by_sector"]) == overall["n"]
    assert sum(r["n"] for r in attr["by_rank_band"]) == overall["n"]


def test_attribution_distribution_exact(aggregates_engine):
    """The distribution panel is exact on the hand fixture: mean, median, hit-rate (% positive), and
    dispersion (sample stdev), with n — over the SAME six observed returns as the aggregate."""
    engine, H = aggregates_engine
    observed = [0.10, 0.20, 0.00, -0.10, 0.30, 0.10]  # the six realized stock returns at H
    with Session(engine) as session:
        dist = compute_forward_aggregates(session, H, load_config())["attribution"]["distribution"]
    assert dist["n"] == 6
    assert dist["mean_return"] == pytest.approx(0.10)
    assert dist["median"] == pytest.approx(0.10)
    assert dist["pct_positive"] == pytest.approx(4 / 6)  # 0.10,0.20,0.30,0.10 > 0 (0.00 / -0.10 are not)
    assert dist["dispersion"] == pytest.approx(stdev(observed))


def test_attribution_per_stock_named_contributors_and_detractors(aggregates_engine):
    """Per-stock: each NAMED ticker's mean realized return + n + stored sector over the same
    observations; contributors are the highest means, detractors the lowest. AAA aggregates its two
    runs to +0.20 (n=2); DDD is the sole detractor at -0.10."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        per_stock = compute_forward_aggregates(session, H, load_config())["attribution"]["per_stock"]
    contributors, detractors = per_stock["contributors"], per_stock["detractors"]

    aaa = next(r for r in contributors if r["ticker"] == "AAA")
    assert aaa["mean_return"] == pytest.approx(0.20) and aaa["n"] == 2 and aaa["sector"] == "Technology"
    assert contributors[0]["ticker"] == "AAA" and contributors[0]["mean_return"] == pytest.approx(0.20)
    assert detractors[0]["ticker"] == "DDD" and detractors[0]["mean_return"] == pytest.approx(-0.10)
    # contributors are ordered high->low, detractors low->high (robust to tie order)
    assert [r["mean_return"] for r in contributors] == sorted(
        (r["mean_return"] for r in contributors), reverse=True
    )
    assert [r["mean_return"] for r in detractors] == sorted(r["mean_return"] for r in detractors)


def test_attribution_top_contributors_k_controls_list_length(aggregates_engine):
    """No magic numbers: the list length is `config.walk_forward.attribution.top_contributors_k`, not a
    code literal — shrinking it shrinks the contributor / detractor lists."""
    engine, H = aggregates_engine
    cfg = load_config()
    attr_cfg = cfg.walk_forward.attribution.model_copy(update={"top_contributors_k": 2})
    cfg2 = cfg.model_copy(
        update={"walk_forward": cfg.walk_forward.model_copy(update={"attribution": attr_cfg})}
    )
    with Session(engine) as session:
        per_stock = compute_forward_aggregates(session, H, cfg2)["attribution"]["per_stock"]
    assert len(per_stock["contributors"]) == 2 and len(per_stock["detractors"]) == 2


def test_attribution_rank_bands_come_from_config(aggregates_engine):
    """No magic numbers: the rank-band labels / edges come from config — redefining the bands changes
    both the emitted labels and which observations fall in each (no band edge literal in calc code)."""
    from app.config import RankBand

    engine, H = aggregates_engine
    cfg = load_config()
    bands = [RankBand(label="1–2", min=1, max=2), RankBand(label="3+", min=3, max=None)]
    attr_cfg = cfg.walk_forward.attribution.model_copy(update={"rank_bands": bands})
    cfg2 = cfg.model_copy(
        update={"walk_forward": cfg.walk_forward.model_copy(update={"attribution": attr_cfg})}
    )
    with Session(engine) as session:
        by_rank_band = compute_forward_aggregates(session, H, cfg2)["attribution"]["by_rank_band"]
    assert [r["rank_band"] for r in by_rank_band] == ["1–2", "3+"]
    band = {r["rank_band"]: r for r in by_rank_band}
    # ranks 1,2 -> "1–2": AAA(run1)=0.10, BBB=0.20, AAA(run2)=0.30, EEE=0.10
    assert band["1–2"]["n"] == 4
    assert band["1–2"]["mean_return"] == pytest.approx((0.10 + 0.20 + 0.30 + 0.10) / 4)
    # ranks 3,4 -> "3+": CCC=0.00, DDD=-0.10
    assert band["3+"]["n"] == 2 and band["3+"]["mean_return"] == pytest.approx(-0.05)


def test_attribution_rank_band_with_no_members_is_padded(aggregates_engine):
    """A rank band with no members is still emitted (padded n=0 / mean None) so the table is complete.
    On the default config bands every fixture rank (1..4) falls in the first band; the higher bands pad."""
    engine, H = aggregates_engine
    cfg = load_config()
    labels = [b.label for b in cfg.walk_forward.attribution.rank_bands]
    with Session(engine) as session:
        by_rank_band = compute_forward_aggregates(session, H, cfg)["attribution"]["by_rank_band"]
    assert [r["rank_band"] for r in by_rank_band] == labels  # config order, complete
    band = {r["rank_band"]: r for r in by_rank_band}
    assert band[labels[0]]["n"] == 6 and band[labels[0]]["mean_return"] == pytest.approx(0.10)
    for lbl in labels[1:]:
        assert band[lbl]["n"] == 0 and band[lbl]["mean_return"] is None


def test_attribution_empty_observations_are_all_na():
    """Honesty: empty observations -> every slice NA with n=0 (no fabricated 0%). by_rank_band stays
    padded (every config band present at n=0); by_sector (non-padded) is empty."""
    from app.engine.forward_testing import _attribution_slices

    cfg = load_config()
    attr = _attribution_slices([], cfg)
    assert attr["per_stock"]["contributors"] == [] and attr["per_stock"]["detractors"] == []
    assert attr["distribution"] == {
        "mean_return": None, "median": None, "pct_positive": None, "dispersion": None, "n": 0
    }
    assert attr["by_sector"] == []  # pad=False -> no rows when there is nothing to group
    assert [r["rank_band"] for r in attr["by_rank_band"]] == [
        b.label for b in cfg.walk_forward.attribution.rank_bands
    ]
    assert all(r["n"] == 0 and r["mean_return"] is None for r in attr["by_rank_band"])


def test_attribution_single_observation_dispersion_is_null():
    """A single-observation slice has no defined standard deviation -> dispersion null (no spurious 0
    stdev); mean / median equal the single value and the hit-rate is 1.0."""
    from app.engine.forward_testing import _attribution_slices

    dist = _attribution_slices(
        [{"ticker": "AAA", "return": 0.05, "sector": "Technology", "rank": 1}], load_config()
    )["distribution"]
    assert dist["n"] == 1
    assert dist["mean_return"] == pytest.approx(0.05) and dist["median"] == pytest.approx(0.05)
    assert dist["pct_positive"] == pytest.approx(1.0)
    assert dist["dispersion"] is None


def test_attribution_is_pure_over_passed_observations_no_new_query():
    """Read-only / no new query (the critical anti-goal, structural proof): `_attribution_slices` is a
    pure function of the ALREADY-BUILT `stock_obs` + cfg — it takes NO Session, so it can issue no
    forward_returns / price-bar query. The same observation list that feeds the aggregate feeds the
    slices: no second formula, no second data source."""
    import inspect

    from app.engine.forward_testing import _attribution_slices

    assert set(inspect.signature(_attribution_slices).parameters) == {"stock_obs", "cfg"}
    attr = _attribution_slices(
        [{"ticker": "AAA", "return": 0.10, "sector": "Technology", "rank": 1}], load_config()
    )
    assert attr["distribution"]["n"] == 1  # produced from a hand list with no DB access at all


def test_stored_scores_identical_with_and_without_forward_returns(backfilled_engine):
    """No-lookahead (forward never feeds back): the latest run's stored Leadership scores are byte-
    identical to a fresh score_stocks(latest) computed AFTER forward returns exist — so persisting
    forward returns cannot have altered (fed back into) any as-of score."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    from app.engine.scoring import score_stocks

    with Session(engine) as session:
        stored = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == pre_id)).all()
        }
        live_now = {row["ticker"]: row["leadership"]["score"] for row in score_stocks(session, latest, cfg)["rows"]}
    assert stored == live_now  # the snapshot's scores never changed when forward returns landed
    # and the pre-backfill fingerprint's scores match too (the definitive before/after equality)
    assert stored == before["fingerprint"]["lead_by_ticker"]
