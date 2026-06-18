"""iter-33 (J-93/J-94/J-95/J-96) — the dynamic point-in-time universe: the scoring/forward repoint,
the universe_count migration, the J-96 membership timeline, J-95 survivorship + seed-undeletable.

FAST synthetic tests use tiny hand-made DBs (no seed boot). The byte-identity cross-check against the
real seed uses `loaded_engine` and is clearly marked.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.data_manager import clear_snapshot_set, compute_coverage
from app.engine.forward_testing import benchmark_symbols, forward_symbols_for_run
from app.engine.scoring import score_stocks
from app.models import DailyPrice, ScannerResult, ScannerRun


def _mk_run(session: Session, asof: date) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof, created_at=datetime.now(timezone.utc), provider="seed", benchmark="SPY",
        regime_score=50.0, regime_label="Choppy", regime_components_json="{}",
        new_high_low_json="{}", candidate_counts_json="{}",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _mk_result(session: Session, run_id: int, ticker: str, rank: int) -> None:
    session.add(ScannerResult(
        run_id=run_id, ticker=ticker, name=ticker, sector="Technology",
        leadership_score=float(100 - rank), leadership_bucket="A",
        entry_quality_score=1.0, entry_quality_bucket="A", risk_score=1.0, risk_bucket="A",
        setup_status="Watchlist", rank=rank, record_json="{}",
    ))
    session.commit()


# ==================================================================================================
# J-93 — forward_symbols_for_run = this run's stored ScannerResult tickers ∪ benchmarks
# ==================================================================================================
def test_forward_symbols_for_run_is_members_union_benchmarks(tmp_path):
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'fr.db'}")
    create_db_and_tables(engine)
    bm = benchmark_symbols(cfg)
    bench_set = {bm["spy"], bm["qqq"], *bm["sector_etfs"]}
    with Session(engine) as session:
        run = _mk_run(session, date(2024, 1, 5))
        # this run scored only two names
        _mk_result(session, run.id, "AAA", rank=1)
        _mk_result(session, run.id, "BBB", rank=2)
        symbols = forward_symbols_for_run(session, run, cfg)
    # the run's scored members come first (rank order), then the benchmarks — de-duplicated.
    assert symbols[:2] == ["AAA", "BBB"]
    # every benchmark is present on EVERY run (the excess-return controls).
    assert bench_set <= set(symbols)
    # no name outside (this run's members ∪ benchmarks) leaks in.
    assert set(symbols) == {"AAA", "BBB"} | bench_set


def test_forward_symbols_for_run_empty_membership_is_just_benchmarks(tmp_path):
    """An early/warm-up run with NO scored members → forward_symbols is exactly the benchmarks (so the
    excess-return math always has its controls), never a fabricated member."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'fr2.db'}")
    create_db_and_tables(engine)
    bm = benchmark_symbols(cfg)
    bench_set = {bm["spy"], bm["qqq"], *bm["sector_etfs"]}
    with Session(engine) as session:
        run = _mk_run(session, date(2021, 3, 1))  # no ScannerResult rows → empty membership
        symbols = forward_symbols_for_run(session, run, cfg)
    assert set(symbols) == bench_set


# ==================================================================================================
# J-96 — membership timeline: per-date size step function + entries/exits, deterministic + causal
# ==================================================================================================
def test_membership_timeline_entries_exits_deterministic_and_causal(tmp_path):
    """Over three hand-made snapshots the timeline derives the size step function + deterministic
    entries (first appearance) / exits (disappearance after presence), strictly from each date's own
    stored membership (causal). No bars needed — the timeline reads the persisted ScannerResult sets."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'tl.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _mk_run(session, date(2022, 1, 3))
        for i, t in enumerate(["AAA", "BBB"]):
            _mk_result(session, r1.id, t, rank=i + 1)
        r2 = _mk_run(session, date(2022, 6, 1))
        for i, t in enumerate(["AAA", "CCC"]):  # BBB exits, CCC enters
            _mk_result(session, r2.id, t, rank=i + 1)
        r3 = _mk_run(session, date(2022, 12, 1))
        for i, t in enumerate(["AAA", "BBB", "CCC"]):  # BBB re-appears (not a new entry — seen before)
            _mk_result(session, r3.id, t, rank=i + 1)
        cov = compute_coverage(session, cfg)
        cov2 = compute_coverage(session, cfg)  # determinism: a second call is byte-identical
    tl = cov["membership_timeline"]
    pts = {p["date"]: p for p in tl["points"]}
    assert pts["2022-01-03"]["size"] == 2 and pts["2022-01-03"]["entries"] == ["AAA", "BBB"]
    assert pts["2022-01-03"]["exits"] == []
    # BBB disappears, CCC appears for the first time
    assert pts["2022-06-01"]["size"] == 2
    assert pts["2022-06-01"]["entries"] == ["CCC"] and pts["2022-06-01"]["exits"] == ["BBB"]
    # BBB re-appears: NOT a new entry (it was seen before); size grows to 3
    assert pts["2022-12-01"]["size"] == 3
    assert pts["2022-12-01"]["entries"] == [] and pts["2022-12-01"]["exits"] == []
    assert cov2["membership_timeline"] == tl  # deterministic


def test_membership_timeline_empty_db_is_honest_empty(tmp_path):
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'empty_tl.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)
    tl = cov["membership_timeline"]
    assert tl["points"] == []  # no snapshots → no fabricated dates/members
    assert "labels" in tl and tl["labels"]["survivorship"]["basis"] == "current_constituent"


# ==================================================================================================
# J-94 — coverage block: the as-of-dependent universe_count + per-date diagnostic shape
# ==================================================================================================
def test_coverage_universe_diagnostic_shape_and_thresholds(tmp_path):
    """The coverage block carries the J-94 per-date diagnostic with the admitted count + excluded-by-
    reason counts + the exact config thresholds (No magic number — the values are config reads)."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'cov.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        cov = compute_coverage(session, cfg)  # empty DB
    ud = cov["universe_diagnostic"]
    assert set(ud) == {
        "asof", "candidate_pool_count", "admitted_count", "excluded_total", "excluded", "thresholds",
    }
    assert set(ud["excluded"]) == {"below_history", "below_price", "below_adv"}
    assert ud["thresholds"]["min_history_bars"] == cfg.indicators.min_history_bars
    assert ud["thresholds"]["min_price"] == cfg.universe.filters.min_price
    assert ud["thresholds"]["min_dollar_vol"] == cfg.universe.filters.min_dollar_vol
    assert ud["thresholds"]["adv_window_days"] == cfg.universe.filters.adv_window_days
    # the static + pool counts are carried beside the dynamic universe_count
    assert cov["candidate_universe_count"] == len(cfg.universe.symbols)
    assert cov["candidate_pool_count"] >= cov["candidate_universe_count"]
    assert cov["universe_count"] == 0  # empty DB → honest empty resolved universe


# ==================================================================================================
# J-95 — clear_snapshot_set keeps the price seed (bars_before == bars_after); seed un-deletable
# ==================================================================================================
def test_clear_snapshot_set_preserves_price_seed(tmp_path):
    """The backward-history / rebuild clear deletes ONLY the snapshot layer — the committed price bars
    are never touched (`bars_before == bars_after`), the hard guarantee the resolver-populated rebuild
    relies on (anti-goal: Snapshots immutable / committed seed never deleted)."""
    cfg = load_config()
    engine = make_engine(f"sqlite:///{tmp_path / 'clr.db'}")
    create_db_and_tables(engine)
    start = date(2024, 1, 1)
    with Session(engine) as session:
        for i in range(10):
            session.add(DailyPrice(
                symbol="AAA", date=start + timedelta(days=i),
                open=20.0, high=20.0, low=20.0, close=20.0, volume=1000.0,
            ))
        session.commit()
        run = _mk_run(session, date(2024, 1, 9))
        _mk_result(session, run.id, "AAA", rank=1)
        bars_before = session.scalar(select(func.count()).select_from(DailyPrice))
        cleared = clear_snapshot_set(session)
        bars_after = session.scalar(select(func.count()).select_from(DailyPrice))
    assert cleared["bars_before"] == cleared["bars_after"] == bars_before == bars_after == 10
    assert cleared["runs_cleared"] == 1


# ==================================================================================================
# J-06 / J-93 byte-identity — per-stock scores identical for the SAME resolved membership (REAL seed)
# ==================================================================================================
def test_scores_byte_identical_for_resolved_membership(loaded_engine):
    """The universe_count migration changes ONLY which names are scored — every scored member's canonical
    record is byte-identical across two calls (single source / no recompute / no formula change). The
    scored set == the resolved members (J-93), and at a fully-warm date it is a non-empty subset of the
    candidate universe."""
    cfg = load_config()
    from app.engine.prices import latest_data_date
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        a = score_stocks(session, asof, cfg)
        b = score_stocks(session, asof, cfg)
    # the row dicts are byte-identical (deterministic, single source).
    assert json.dumps(a["rows"], sort_keys=True) == json.dumps(b["rows"], sort_keys=True)
    # the scored set equals the resolved members (one row per member; no second universe computation).
    scored = {r["ticker"] for r in a["rows"]}
    assert scored == set(a["members"])
    assert 0 < len(scored) <= len(cfg.universe.symbols)  # a non-empty subset at a warm date


def test_resolved_membership_persisted_rows_match_members(loaded_engine):
    """The persisted ScannerResult rows for a run ARE the membership: the latest run's scored tickers ==
    the resolver's resolved-at-that-date members (single source — no drift)."""
    cfg = load_config()
    from app.engine.prices import latest_data_date
    from app.engine.universe_resolver import resolve_members
    with Session(loaded_engine) as session:
        asof = latest_data_date(session)
        members = set(resolve_members(session, asof, cfg))
        latest_run_id = session.scalar(select(ScannerRun.id).where(ScannerRun.asof_date == asof))
        scored = set(
            session.exec(
                select(ScannerResult.ticker).where(ScannerResult.run_id == latest_run_id)
            ).all()
        )
    assert scored == members and len(members) > 0
