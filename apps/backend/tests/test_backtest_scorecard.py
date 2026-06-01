"""Per-date forward-test scorecard engine (J-14) — the single-date drill-down proofs.

`compute_run_scorecard(session, run)` is the SINGLE canonical per-date scorecard: it READS the stored
`forward_returns` for ONE run joined to the stored `scanner_results` (bucket/setup/sector/rank verbatim)
and recomputes nothing. `backfill_run_forward_returns(session, run)` is the create-once INSERT-only
population of one run's forward returns, factored to share the ONE forward-return formula with `_backfill`
(via `_insert_run_forward_returns`).

Named proofs, each guarding a critical anti-goal:
  - no-lookahead boundary      — a run dated D measures returns ONLY from bars with date > D (entry close
                                 ON D); no bar with date <= D is the measured close.            *(No lookahead)*
  - honest partial / NA        — a horizon with < h post-bars yields mean_return None / n 0; never a 0%. *(No fabricated data)*
  - create-once + idempotent   — a 2nd backfill inserts 0 rows and mutates no snapshot row.      *(Snapshots immutable)*
  - read stored, don't rebucket— the cohort groups by the STORED rank/bucket/sector verbatim.    *(Single source)*
  - shared math (cross-check)  — the scorecard's control cohorts equal compute_forward_aggregates'
                                 for the same single run + horizon (one formula, factored).      *(Single source)*
  - keystone (no recompute)    — with the forward-return + scoring engines patched to RAISE, the scorecard
                                 still serves from stored rows.                                  *(No recompute)*
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import forward_testing
from app.engine.forward_testing import (
    backfill_run_forward_returns,
    compute_forward_aggregates,
    compute_run_scorecard,
)
from app.engine.prices import close_on
from app.models import DailyPrice, ForwardReturn, ScannerResult, ScannerRun


# ==================================================================================================
# Hand-built helpers (exact values by construction — no engine)
# ==================================================================================================
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str = "Risk-on") -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label=regime_label,
        regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(session, run_id, ticker, bucket, setup, sector, rank):
    session.add(
        ScannerResult(
            run_id=run_id, ticker=ticker, name=ticker, sector=sector,
            leadership_score=50.0, leadership_bucket=bucket,
            entry_quality_score=0.0, entry_quality_bucket="E",
            risk_score=0.0, risk_bucket="E",
            setup_status=setup, rank=rank, record_json="{}",
        )
    )


def _add_fr(session, run_id, symbol, horizon, ret, asof):
    session.add(
        ForwardReturn(
            run_id=run_id, symbol=symbol, horizon=horizon,
            asof_date=asof, entry_close=100.0,
            measured_date=date(2025, 2, 1), realized_return=ret,
        )
    )


@pytest.fixture()
def scorecard_engine(tmp_path):
    """ONE Risk-on run with known forward returns at horizon 20 (full) and horizon 1 (partial); the
    other horizons (5/10/60) have NO stored return (the NA case). Tech sector ETF = XLK, Energy = XLE."""
    engine = make_engine(f"sqlite:///{tmp_path / 'scorecard.db'}")
    create_db_and_tables(engine)
    asof = date(2025, 1, 10)
    with Session(engine) as session:
        run = _add_run(session, asof, "Risk-on")
        _add_result(session, run.id, "AAA", "A", "Actionable", "Technology", 1)
        _add_result(session, run.id, "BBB", "A", "Breakout-watch", "Technology", 2)
        _add_result(session, run.id, "CCC", "E", "Avoid", "Technology", 3)
        _add_result(session, run.id, "DDD", "E", "Avoid", "Energy", 4)
        # horizon 20 — full cohort + benchmarks + sector ETFs
        for sym, ret in [("AAA", 0.10), ("BBB", 0.20), ("CCC", 0.00), ("DDD", -0.10),
                         ("SPY", 0.05), ("QQQ", 0.06), ("XLK", 0.04), ("XLE", -0.02)]:
            _add_fr(session, run.id, sym, 20, ret, asof)
        # horizon 1 — only a subset has a realized return yet (AAA, BBB, SPY)
        for sym, ret in [("AAA", 0.01), ("BBB", 0.02), ("SPY", 0.005)]:
            _add_fr(session, run.id, sym, 1, ret, asof)
        session.commit()
        run_id = run.id
    return engine, run_id, asof


def _scorecard(engine, run_id):
    with Session(engine) as session:
        run = session.get(ScannerRun, run_id)
        return compute_run_scorecard(session, run, load_config())


def _horizon(card: dict, h: int) -> dict:
    return next(row for row in card["scorecard"]["by_horizon"] if row["horizon"] == h)


# ==================================================================================================
# Payload shape + carried honesty metadata
# ==================================================================================================
def test_scorecard_payload_shape_and_metadata(scorecard_engine):
    engine, run_id, asof = scorecard_engine
    cfg = load_config()
    card = _scorecard(engine, run_id)

    assert card["asof_date"] == asof.isoformat()
    assert card["min_sample"] == cfg.walk_forward.min_sample
    assert card["horizons"] == list(cfg.walk_forward.horizons)
    assert "survivorship" in card["survivorship_bias"].lower()
    # one row per configured horizon, in config order
    assert [r["horizon"] for r in card["scorecard"]["by_horizon"]] == list(cfg.walk_forward.horizons)
    for row in card["scorecard"]["by_horizon"]:
        assert {"horizon", "cohort", "excess", "control_group"} <= set(row)
        assert {"mean_return", "n"} <= set(row["cohort"])
        assert {"vs_spy", "vs_qqq", "vs_sector"} <= set(row["excess"])
        assert {c["key"] for c in row["control_group"]} == {
            "top_ranked", "random_same_sector", "spy", "qqq", "sector_etf"
        }


def test_scorecard_full_horizon_cohort_excess_and_controls_exact(scorecard_engine):
    """Horizon 20 (full window): the top-ranked cohort mean, excess vs SPY/QQQ/sector, and the 5 control
    cohorts are exact. cohort = stocks ranked <= top_n (20) = all four results."""
    engine, run_id, asof = scorecard_engine
    h20 = _horizon(_scorecard(engine, run_id), 20)

    # cohort = AAA,BBB,CCC,DDD -> mean(0.10,0.20,0.00,-0.10) = 0.05
    assert h20["cohort"]["n"] == 4
    assert h20["cohort"]["mean_return"] == pytest.approx(0.05)

    cg = {c["key"]: c for c in h20["control_group"]}
    assert cg["top_ranked"]["n"] == 4 and cg["top_ranked"]["mean_return"] == pytest.approx(0.05)
    assert cg["spy"]["n"] == 1 and cg["spy"]["mean_return"] == pytest.approx(0.05)
    assert cg["qqq"]["n"] == 1 and cg["qqq"]["mean_return"] == pytest.approx(0.06)
    # sector ETF = XLK (Technology) + XLE (Energy) over the sectors the cohort occupies
    assert cg["sector_etf"]["n"] == 2 and cg["sector_etf"]["mean_return"] == pytest.approx((0.04 - 0.02) / 2)
    assert cg["random_same_sector"]["n"] >= 1 and cg["random_same_sector"]["mean_return"] is not None

    # excess = cohort mean - benchmark mean
    assert h20["excess"]["vs_spy"]["mean_excess"] == pytest.approx(0.05 - 0.05)
    assert h20["excess"]["vs_qqq"]["mean_excess"] == pytest.approx(0.05 - 0.06)
    assert h20["excess"]["vs_sector"]["mean_excess"] == pytest.approx(0.05 - 0.01)
    # every excess figure carries the cohort sample size n
    assert h20["excess"]["vs_spy"]["n"] == 4
    assert h20["excess"]["vs_qqq"]["benchmark"] == "QQQ"


def test_scorecard_partial_horizon_renders_observable_and_na(scorecard_engine):
    """Honest partial: horizon 1 has only AAA/BBB/SPY realized -> cohort = AAA,BBB (numeric); QQQ and the
    sector ETF have no h=1 return -> NA (n=0); excess vs those is None (never a fabricated 0%)."""
    engine, run_id, asof = scorecard_engine
    h1 = _horizon(_scorecard(engine, run_id), 1)

    assert h1["cohort"]["n"] == 2 and h1["cohort"]["mean_return"] == pytest.approx(0.015)  # AAA,BBB
    cg = {c["key"]: c for c in h1["control_group"]}
    assert cg["spy"]["n"] == 1 and cg["spy"]["mean_return"] == pytest.approx(0.005)
    assert cg["qqq"]["n"] == 0 and cg["qqq"]["mean_return"] is None        # no h=1 QQQ return -> NA
    assert cg["sector_etf"]["n"] == 0 and cg["sector_etf"]["mean_return"] is None

    assert h1["excess"]["vs_spy"]["mean_excess"] == pytest.approx(0.015 - 0.005)
    assert h1["excess"]["vs_qqq"]["mean_excess"] is None   # benchmark NA -> excess NA, not 0%
    assert h1["excess"]["vs_sector"]["mean_excess"] is None


def test_scorecard_unobserved_horizon_is_all_na(scorecard_engine):
    """Horizons with NO stored return (5/10/60 here) are all-NA: cohort + every control n=0 / mean None."""
    engine, run_id, asof = scorecard_engine
    card = _scorecard(engine, run_id)
    for h in (5, 10, 60):
        row = _horizon(card, h)
        assert row["cohort"]["n"] == 0 and row["cohort"]["mean_return"] is None
        for c in row["control_group"]:
            assert c["n"] == 0 and c["mean_return"] is None
        assert row["excess"]["vs_spy"]["mean_excess"] is None


def test_scorecard_groups_by_stored_rank_not_rescored(tmp_path):
    """Single-source: the cohort is stocks with STORED rank <= top_n, read verbatim. A row stored at
    rank 1 is IN the cohort and a row stored beyond top_n is OUT — regardless of its leadership score."""
    cfg = load_config()
    top_n = cfg.walk_forward.control_group.top_n
    engine = make_engine(f"sqlite:///{tmp_path / 'rank.db'}")
    create_db_and_tables(engine)
    asof = date(2025, 3, 3)
    with Session(engine) as session:
        run = _add_run(session, asof)
        _add_result(session, run.id, "INRANK", "A", "Actionable", "Technology", 1)            # rank 1 <= top_n
        _add_result(session, run.id, "OUTRANK", "A", "Actionable", "Technology", top_n + 1)   # beyond top_n
        _add_fr(session, run.id, "INRANK", 20, 0.30, asof)
        _add_fr(session, run.id, "OUTRANK", 20, 0.99, asof)   # huge return but OUT of the cohort by rank
        session.commit()
        run_id = run.id

    h20 = _horizon(_scorecard(engine, run_id), 20)
    # only the in-rank row contributes to the cohort — the out-of-rank row is excluded by STORED rank
    assert h20["cohort"]["n"] == 1 and h20["cohort"]["mean_return"] == pytest.approx(0.30)


def test_scorecard_controls_equal_aggregates_for_single_run(scorecard_engine):
    """Shared math: with exactly one run carrying forward returns, the scorecard's control-group cohorts
    at horizon 20 are byte-identical to compute_forward_aggregates(20)'s control group — proving both go
    through the ONE `_control_groups` implementation (no second formula)."""
    engine, run_id, asof = scorecard_engine
    cfg = load_config()
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, 20, cfg)
        run = session.get(ScannerRun, run_id)
        card = compute_run_scorecard(session, run, cfg)
    h20 = _horizon(card, 20)
    assert h20["control_group"] == agg["control_group"]


def test_scorecard_keystone_recomputes_nothing(scorecard_engine, monkeypatch):
    """KEYSTONE (no recompute): with the forward-return math AND the scoring/regime/sector/theme engines
    patched to RAISE, compute_run_scorecard STILL serves the scorecard from the stored rows — proving it
    reads storage and recomputes no return/score/bucket."""
    engine, run_id, asof = scorecard_engine

    def boom(*args, **kwargs):
        raise AssertionError("the scorecard must not recompute a return/score for a stored run")

    monkeypatch.setattr("app.engine.forward_testing.forward_return", boom)
    for name in ("score_stocks", "score_regime", "score_sectors", "score_themes"):
        monkeypatch.setattr(f"app.engine.scanner.{name}", boom)

    with Session(engine) as session:
        run = session.get(ScannerRun, run_id)
        card = compute_run_scorecard(session, run, load_config())
    assert _horizon(card, 20)["cohort"]["mean_return"] == pytest.approx(0.05)  # served from storage


# ==================================================================================================
# Return attribution (J-19) — per-horizon slices ride each by_horizon entry
# ==================================================================================================
def test_scorecard_horizon_carries_attribution(scorecard_engine):
    """J-19 per-date: each by_horizon entry carries the four attribution slices for THAT horizon,
    derived from the same stored observations as the cohort (no recomputed return). At horizon 20 the
    full observed set is AAA,BBB,CCC,DDD; BBB (+0.20) is the top contributor, DDD (-0.10) the detractor."""
    engine, run_id, asof = scorecard_engine
    h20 = _horizon(_scorecard(engine, run_id), 20)
    attr = h20["attribution"]
    assert {"per_stock", "by_sector", "by_rank_band", "distribution"} <= set(attr)
    # distribution is over the FULL observed set at h20 (AAA,BBB,CCC,DDD) -> mean 0.05, n 4
    assert attr["distribution"]["n"] == 4 and attr["distribution"]["mean_return"] == pytest.approx(0.05)
    assert attr["per_stock"]["contributors"][0]["ticker"] == "BBB"
    assert attr["per_stock"]["contributors"][0]["mean_return"] == pytest.approx(0.20)
    assert attr["per_stock"]["detractors"][0]["ticker"] == "DDD"
    assert sum(r["n"] for r in attr["by_sector"]) == 4  # every observation has a stored sector


def test_scorecard_attribution_partial_and_unobserved_horizons_are_honest(scorecard_engine):
    """Honest partial: horizon 1 has only AAA,BBB observed -> distribution over those two (n=2); the
    unobserved horizons (5/10/60) have empty attribution (n=0, NA, no named tickers) — never fabricated.
    by_rank_band stays padded (all bands present) even when empty."""
    engine, run_id, asof = scorecard_engine
    card = _scorecard(engine, run_id)
    h1 = _horizon(card, 1)["attribution"]
    assert h1["distribution"]["n"] == 2 and h1["distribution"]["mean_return"] == pytest.approx(0.015)
    for h in (5, 10, 60):
        attr = _horizon(card, h)["attribution"]
        assert attr["distribution"]["n"] == 0 and attr["distribution"]["mean_return"] is None
        assert attr["per_stock"]["contributors"] == [] and attr["per_stock"]["detractors"] == []
        assert sum(r["n"] for r in attr["by_sector"]) == 0
        assert all(r["n"] == 0 for r in attr["by_rank_band"])  # padded, complete, all NA


# ==================================================================================================
# backfill_run_forward_returns — create-once, INSERT-only, no-lookahead (real config symbols, tiny seed)
# ==================================================================================================
@pytest.fixture()
def one_symbol_run(tmp_path):
    """A tiny price history for ONE real universe symbol (NVDA) on five dates + a hand run dated D with
    NVDA ranked 1. D has exactly three POST-D bars, so horizon 1 is observable and 5/10/20/60 are NA."""
    engine = make_engine(f"sqlite:///{tmp_path / 'one.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]
    asof = days[1]  # 2024-01-03 -> three post-D bars (the 4th, 5th, 8th)
    with Session(engine) as session:
        for i, d in enumerate(days):
            close = float(10 + i)  # 10, 11, 12, 13, 14
            session.add(DailyPrice(symbol="NVDA", date=d, open=close, high=close, low=close, close=close, volume=1.0))
        run = _add_run(session, asof)
        _add_result(session, run.id, "NVDA", "A", "Actionable", "Technology", 1)
        session.commit()
        run_id = run.id
        entry = close_on(session, "NVDA", asof)
    return engine, run_id, asof, days, entry


def test_backfill_run_is_no_lookahead_and_insert_only(one_symbol_run):
    """No-lookahead: every stored forward return for run D uses the entry close ON D (date <= D) and a
    measured bar strictly AFTER D (date > D) — no bar with date <= D is ever the measured close."""
    engine, run_id, asof, days, entry = one_symbol_run
    with Session(engine) as session:
        run = session.get(ScannerRun, run_id)
        summary = backfill_run_forward_returns(session, run, load_config())
        frs = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run_id)).all()

    # only horizon 1 is observable (3 post-D bars) -> exactly one inserted row, for NVDA at horizon 1
    assert summary["rows_inserted"] == 1
    assert [(fr.symbol, fr.horizon) for fr in frs] == [("NVDA", 1)]
    fr = frs[0]
    assert fr.entry_close == entry == 11.0           # close ON D (2024-01-03)
    assert fr.asof_date == asof
    assert fr.measured_date == days[2]               # 2024-01-04, strictly > D
    assert fr.measured_date > asof
    assert fr.realized_return == pytest.approx(12.0 / 11.0 - 1)


def test_backfill_run_is_create_once_idempotent(one_symbol_run):
    """Create-once: a 2nd backfill of the same run inserts ZERO new rows and never UPDATEs a snapshot
    row (the stored ScannerResult is byte-identical before vs after)."""
    engine, run_id, asof, days, entry = one_symbol_run
    with Session(engine) as session:
        run = session.get(ScannerRun, run_id)
        first = backfill_run_forward_returns(session, run, load_config())
        before = session.exec(select(ScannerResult).where(ScannerResult.run_id == run_id)).one()
        before_fp = (before.ticker, before.rank, before.leadership_bucket, before.record_json)
        n_before = session.scalar(select(func.count()).select_from(ForwardReturn))

        second = backfill_run_forward_returns(session, run, load_config())
        after = session.exec(select(ScannerResult).where(ScannerResult.run_id == run_id)).one()
        after_fp = (after.ticker, after.rank, after.leadership_bucket, after.record_json)
        n_after = session.scalar(select(func.count()).select_from(ForwardReturn))

    assert first["rows_inserted"] == 1
    assert second["rows_inserted"] == 0   # idempotent — nothing new the 2nd time
    assert n_after == n_before
    assert after_fp == before_fp          # the snapshot result row was NOT mutated


def test_backfill_run_partial_window_scorecard_is_honest_na(one_symbol_run):
    """After backfill, the scorecard shows the observable horizon (1) numerically and the unobservable
    horizons (5/10/20/60) as NA (n=0) — never a fabricated number."""
    engine, run_id, asof, days, entry = one_symbol_run
    with Session(engine) as session:
        run = session.get(ScannerRun, run_id)
        backfill_run_forward_returns(session, run, load_config())
    card = _scorecard(engine, run_id)

    assert _horizon(card, 1)["cohort"]["n"] == 1
    assert _horizon(card, 1)["cohort"]["mean_return"] == pytest.approx(12.0 / 11.0 - 1)
    for h in (5, 10, 20, 60):
        assert _horizon(card, h)["cohort"]["n"] == 0
        assert _horizon(card, h)["cohort"]["mean_return"] is None
