"""ops-hardening iter-14 (J-07, AG-8 REGRESSION recovery) — byte-identity proof for the bounded/streamed
rewrite of `compute_forward_aggregates`'s two whole-partition ORM reads
(`apps/backend/app/engine/forward_testing.py`): the `ForwardReturn` scan (`fr_stmt` / `.all()`) and the
`ScannerResult` scan (`select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`). Both
were replaced with column-projected, `yield_per(cfg.research.read_batch_size)`-streamed reads (mirroring
this module's own `_streamed_existing_keys` and `research.py`'s `_subject_matching_result_rows` /
`_event_study_members` precedent) because both tables had grown ~9x since first measured and the unbounded
pattern was the confirmed root cause of this session's two full-availability outages (iter-7, iter-13).

`_reference_compute_forward_aggregates` below is a PINNED COPY of the pre-rewrite function body (the two
whole-partition `.all()` reads), calling the SAME unchanged downstream helpers
(`benchmark_symbols`/`_group_means`/`_control_groups`/`_attribution_slices`/`_mean_or_none`) the real,
rewritten function still uses. Any divergence between the real function's output and this reference can
therefore only come from the two rewritten read steps, never from a second aggregation formula — this is
the "capture the original's output ... or keep a reference implementation in the test" fixture-backed
equality proof the iter-14 plan calls for (TC-1/TC-2).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import (
    BUCKET_ORDER,
    FLAT_BASE_LABELS,
    PULLBACK_LABELS,
    SURVIVORSHIP_BIAS_LABEL,
    VCP_LABELS,
    _attribution_slices,
    _control_groups,
    _group_means,
    _mean_or_none,
    benchmark_symbols,
    compute_forward_aggregates,
)
from app.engine.setups import ALL_STATUSES
from app.models import ForwardReturn, ScannerResult, ScannerRun

# --------------------------------------------------------------------------------------------------
# Pinned pre-rewrite reference implementation (the two `.all()` reads this iteration replaces)
# --------------------------------------------------------------------------------------------------
def _reference_compute_forward_aggregates(session: Session, horizon: int, config, *, as_of=None) -> dict:
    cfg = config
    bm = benchmark_symbols(cfg)

    fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_rows = session.exec(fr_stmt).all()
    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
    mdd_by_run_symbol = {(fr.run_id, fr.symbol): fr.max_drawdown for fr in fr_rows}
    runs_with_fr = sorted({fr.run_id for fr in fr_rows})

    results = (
        session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    run_rows = (
        session.exec(select(ScannerRun).where(ScannerRun.id.in_(runs_with_fr))).all()
        if runs_with_fr else []
    )
    regime_by_run = {run.id: run.regime_label for run in run_rows}

    stock_obs: list[dict] = []
    for res in results:
        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
        if realized is None:
            continue
        stock_obs.append({
            "run_id": res.run_id,
            "ticker": res.ticker,
            "return": realized,
            "max_drawdown": mdd_by_run_symbol.get((res.run_id, res.ticker)),
            "bucket": res.leadership_bucket,
            "setup": res.setup_status,
            "sector": res.sector,
            "rank": res.rank,
            "regime": regime_by_run.get(res.run_id),
            "is_vcp": res.is_vcp,
            "is_pullback_to_rising_dma": res.is_pullback_to_rising_dma,
            "is_flat_base_breakout": res.is_flat_base_breakout,
        })

    stock_returns = [o["return"] for o in stock_obs]
    overall_mean = _mean_or_none(stock_returns)
    overall_mdds = [o["max_drawdown"] for o in stock_obs if o["max_drawdown"] is not None]
    overall_mean_mdd = _mean_or_none(overall_mdds)
    spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
    qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]
    spy_mean = _mean_or_none(spy_returns)
    qqq_mean = _mean_or_none(qqq_returns)

    excess = {
        "vs_spy": {
            "benchmark": bm["spy"],
            "mean_excess": (overall_mean - spy_mean) if (overall_mean is not None and spy_mean is not None) else None,
            "stock_mean": overall_mean,
            "benchmark_mean": spy_mean,
            "n": len(stock_returns),
            "benchmark_n": len(spy_returns),
        },
        "vs_qqq": {
            "benchmark": bm["qqq"],
            "mean_excess": (overall_mean - qqq_mean) if (overall_mean is not None and qqq_mean is not None) else None,
            "stock_mean": overall_mean,
            "benchmark_mean": qqq_mean,
            "n": len(stock_returns),
            "benchmark_n": len(qqq_returns),
        },
    }

    asof_dates = sorted((run.asof_date.isoformat() for run in run_rows), reverse=True)

    by_vcp = [
        {"vcp": VCP_LABELS[row["vcp"]], "mean_return": row["mean_return"],
         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
        for row in _group_means(stock_obs, "is_vcp", "vcp", [True, False], pad=True)
    ]
    by_pullback_to_rising_dma = [
        {"pullback_to_rising_dma": PULLBACK_LABELS[row["pullback_to_rising_dma"]], "mean_return": row["mean_return"],
         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
        for row in _group_means(stock_obs, "is_pullback_to_rising_dma", "pullback_to_rising_dma", [True, False], pad=True)
    ]
    by_flat_base_breakout = [
        {"flat_base_breakout": FLAT_BASE_LABELS[row["flat_base_breakout"]], "mean_return": row["mean_return"],
         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
        for row in _group_means(stock_obs, "is_flat_base_breakout", "flat_base_breakout", [True, False], pad=True)
    ]

    return {
        "horizon": horizon,
        "horizons": list(cfg.walk_forward.horizons),
        "default_horizon": cfg.walk_forward.default_horizon,
        "min_sample": cfg.walk_forward.min_sample,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "n_runs": len(runs_with_fr),
        "asof_dates": asof_dates,
        "overall": {"mean_return": overall_mean, "mean_max_drawdown": overall_mean_mdd, "n": len(stock_returns)},
        "by_bucket": _group_means(stock_obs, "bucket", "bucket", BUCKET_ORDER, pad=True),
        "by_setup": _group_means(stock_obs, "setup", "setup", ALL_STATUSES, pad=False),
        "by_regime": _group_means(stock_obs, "regime", "regime", cfg.regime.labels, pad=False),
        "by_vcp": by_vcp,
        "by_pullback_to_rising_dma": by_pullback_to_rising_dma,
        "by_flat_base_breakout": by_flat_base_breakout,
        "excess": excess,
        "control_group": _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg),
        "attribution": _attribution_slices(stock_obs, cfg),
    }


# --------------------------------------------------------------------------------------------------
# Fixture: multi-run, multi-sector, multi-horizon snapshot basis (small, hand-built — no seed load)
# --------------------------------------------------------------------------------------------------
HORIZONS = (1, 5, 10, 20, 60)
# ticker -> (sector, bucket, setup, rank, is_vcp, is_pullback, is_flat_base) — CONSTANT across every run
# this ticker appears in (a real stock's sector/pattern-detector identity does not flip run to run; this
# also sidesteps the one theoretical order-sensitivity this file's plan review flagged: `_per_stock_
# attribution`'s `sector_by_ticker.setdefault` picks whichever occurrence is seen FIRST — with a single
# constant sector per ticker, every occurrence agrees, so stream order can never change the result).
_STOCKS = {
    "AAA": ("Technology", "A", "Actionable", 1, True, False, False),
    "BBB": ("Technology", "A", "Breakout-watch", 5, False, True, False),
    "CCC": ("Energy", "B", "Pullback-watch", 12, True, False, False),
    "DDD": ("Energy", "C", "Avoid", 25, False, True, False),
    "EEE": ("Financials", "D", "Risk-off-watchlist", 45, False, False, True),
    "FFF": ("Financials", "E", "Avoid", 60, False, False, False),
    "GGG": ("Technology", "B", "Actionable", 90, False, False, True),
    "HHH": ("Energy", "E", "Extended", 150, False, False, False),
}
_BENCHMARKS = ("SPY", "QQQ", "XLK", "XLE")
# (asof_date, regime_label) — r4 is the newest snapshot; a historical as_of at r3's date excludes it.
_RUNS = (
    (date(2024, 1, 15), "Risk-off"),
    (date(2024, 4, 15), "Risk-on"),
    (date(2024, 7, 15), "Risk-on"),
    (date(2025, 1, 15), "Risk-off"),
)
HISTORICAL_AS_OF = date(2024, 7, 15)  # == r3's date; excludes r4 (the newest snapshot)


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _fr_value(run_idx: int, key_idx: int, horizon: int) -> float:
    """A deterministic, distinct-per-(run, key, horizon) pseudo-return — no two cells collide, so a
    misaligned column projection or a dropped row would show up as a wrong mean rather than a coincidental
    match."""
    return round(0.01 * (run_idx + 1) + 0.002 * key_idx - 0.0001 * horizon, 6)


@pytest.fixture()
def multi_run_engine(tmp_path):
    """4 runs across distinct dates, 8 stocks over 3 real config sectors (Technology/Energy/Financials),
    ranks spanning all 3 config rank bands, a mix of VCP/pullback/flat-base flags, both Risk-on and
    Risk-off regimes, and forward returns at all 5 configured horizons for every stock + the 4 benchmark
    symbols (SPY/QQQ/XLK/XLE) in every run — plus a 5th run with ScannerResults but NO forward returns at
    all (the n=0 / zero-post-bar case, `runs_with_fr` must exclude it)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'multi.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for run_idx, (asof, regime) in enumerate(_RUNS):
            run = ScannerRun(
                asof_date=asof, created_at=_utc(), provider="seed", benchmark="SPY",
                regime_score=50.0, regime_label=regime, regime_components_json="[]",
                new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.flush()
            for ticker, (sector, bucket, setup, rank, is_vcp, is_pullback, is_flat_base) in _STOCKS.items():
                session.add(ScannerResult(
                    run_id=run.id, ticker=ticker, name=ticker, sector=sector,
                    leadership_score=50.0, leadership_bucket=bucket,
                    entry_quality_score=0.0, entry_quality_bucket="E",
                    risk_score=0.0, risk_bucket="E",
                    setup_status=setup, rank=rank, record_json="{}",
                    is_vcp=is_vcp, is_pullback_to_rising_dma=is_pullback, is_flat_base_breakout=is_flat_base,
                ))
            for key_idx, symbol in enumerate(list(_STOCKS) + list(_BENCHMARKS)):
                for horizon in HORIZONS:
                    session.add(ForwardReturn(
                        run_id=run.id, symbol=symbol, horizon=horizon,
                        asof_date=asof, entry_close=100.0, measured_date=date(2025, 12, 31),
                        realized_return=_fr_value(run_idx, key_idx, horizon),
                        max_drawdown=-abs(_fr_value(run_idx, key_idx, horizon)) / 2,
                    ))
        # 5th run: ScannerResults exist but ZERO forward returns (the honest n=0 case) — dated even later
        # than r4 so it is also excluded by HISTORICAL_AS_OF, and its own bucket/rank should never
        # contribute to any as_of=None aggregate either (no realized return -> the NA gate drops it).
        r5 = ScannerRun(
            asof_date=date(2025, 6, 15), created_at=_utc(), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(r5)
        session.flush()
        session.add(ScannerResult(
            run_id=r5.id, ticker="AAA", name="AAA", sector="Technology",
            leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0, entry_quality_bucket="E",
            risk_score=0.0, risk_bucket="E", setup_status="Actionable", rank=1, record_json="{}",
        ))
        session.commit()
    return engine


# --------------------------------------------------------------------------------------------------
# TC-1 / TC-2 — byte-identity across all 5 horizons x {as_of=None, a historical as_of}, at several
# streaming batch sizes (proves the rewrite's behavior is independent of the chunk size)
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("batch", [1, 3, 1_000_000])
@pytest.mark.parametrize("horizon", HORIZONS)
@pytest.mark.parametrize("as_of", [None, HISTORICAL_AS_OF])
def test_compute_forward_aggregates_byte_identical_to_pre_rewrite_reference(
    multi_run_engine, batch, horizon, as_of
):
    """TC-1/TC-2: the rewritten (column-projected, `yield_per`-streamed) `compute_forward_aggregates`
    returns a dict `==` to the pinned pre-rewrite reference implementation, for every configured horizon,
    with `as_of=None` and with a historical `as_of` that excludes the newest snapshot — at streaming batch
    sizes smaller than, equal to, and far larger than the fixture's row count, so the equality does not
    depend on any particular chunking."""
    cfg = load_config()
    cfg = cfg.model_copy(update={"research": cfg.research.model_copy(update={"read_batch_size": batch})})
    with Session(multi_run_engine) as session:
        new_payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
        reference_payload = _reference_compute_forward_aggregates(session, horizon, cfg, as_of=as_of)

    assert new_payload == reference_payload, (
        f"byte-identity broken at horizon={horizon} as_of={as_of} batch={batch}"
    )
    # sanity: the fixture is non-trivial for every horizon/as_of combination exercised here (a passing
    # equality check on two empty dicts would prove nothing about the rewrite).
    assert new_payload["overall"]["n"] > 0
    assert new_payload["n_runs"] > 0


def test_compute_forward_aggregates_as_of_excludes_newest_snapshot_from_reference_too(multi_run_engine):
    """Sanity check on the fixture's own `as_of` design: the historical cutoff genuinely narrows the pool
    relative to `as_of=None` (both on the new function and the reference), so the parametrized byte-
    identity test above is not silently comparing two identical all-history reads under the "as_of" label."""
    cfg = load_config()
    with Session(multi_run_engine) as session:
        all_history = compute_forward_aggregates(session, 20, cfg, as_of=None)
        scoped = compute_forward_aggregates(session, 20, cfg, as_of=HISTORICAL_AS_OF)
    assert scoped["n_runs"] < all_history["n_runs"]
    assert scoped["overall"]["n"] < all_history["overall"]["n"]


def test_compute_forward_aggregates_zero_fr_run_excluded_from_runs_with_fr(multi_run_engine):
    """The 5th run (ScannerResults but zero ForwardReturn rows) never enters `runs_with_fr` — its
    `asof_date` (2025-06-15, the actual latest ScannerRun) must not appear in `asof_dates`, on both the
    rewritten function and the reference."""
    cfg = load_config()
    with Session(multi_run_engine) as session:
        new_payload = compute_forward_aggregates(session, 20, cfg, as_of=None)
        reference_payload = _reference_compute_forward_aggregates(session, 20, cfg, as_of=None)
    assert "2025-06-15" not in new_payload["asof_dates"]
    assert new_payload == reference_payload
