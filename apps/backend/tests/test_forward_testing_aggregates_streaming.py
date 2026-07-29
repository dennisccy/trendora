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

ops-hardening iter-30 (AG-8, J-07) ADDITIVE section (bottom of this file): streaming the two source
queries was not enough on its own — the JOIN ACCUMULATOR built from those streamed rows
(`ret_by_run_symbol`/`mdd_by_run_symbol`, exactly what `_reference_compute_forward_aggregates` above still
builds via one un-sliced `.all()`) still held every distinct (run_id, symbol) pair of the FULL
horizon-partition at once (770K-803K measured live per horizon) — the confirmed live `MemoryError` site
this iteration bounds via `_forward_agg_slice_map` + `walk_forward.forward_agg_run_chunk`-sized run
slices. Because `_reference_compute_forward_aggregates` never chunks, it doubles as the byte-identity
oracle for the run-chunking dimension too (reused, not re-pinned a second time) — the new tests below
compare the SAME real `compute_forward_aggregates` against this SAME reference, just varying
`forward_agg_run_chunk` instead of `research.read_batch_size`.
"""
from __future__ import annotations

import sqlite3
import tracemalloc
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import pytest
from sqlmodel import Session, select

import app.engine.forward_testing as forward_testing_module
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import (
    BUCKET_ORDER,
    FLAT_BASE_LABELS,
    PULLBACK_LABELS,
    SURVIVORSHIP_BIAS_LABEL,
    VCP_LABELS,
    _accumulate_group,
    _AttributionAccumulator,
    _control_groups,
    _distribution,
    _GroupAcc,
    _group_means,
    _mean_or_none,
    _rank_band_label,
    benchmark_symbols,
    compute_forward_aggregates,
)
from app.engine.setups import ALL_STATUSES
from app.models import ForwardReturn, ScannerResult, ScannerRun

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_DB = REPO_ROOT / "apps/backend/data/trendora.db"


# --------------------------------------------------------------------------------------------------
# Pinned PRE-iter-32 attribution implementation (audit iter-32).
#
# `_attribution_slices` was restructured this iteration to read an `_AttributionAccumulator` instead of a
# full `stock_obs` list, and `_per_stock_attribution` was folded into that class. If the reference below
# simply called the NEW `_attribution_slices` (as the developer's first version did), the byte-identity
# oracle would compare the new implementation against ITSELF for the `attribution` key -- one of the ten
# top-level keys TC-2 requires -- and could never detect an attribution behavior change. These two
# functions are the verbatim pre-iter-32 bodies (`git show HEAD:...forward_testing.py`), so the oracle
# stays an INDEPENDENT reference for every key. `_group_means`/`_distribution`/`_rank_band_label` are
# imported from the module because this iteration left them byte-unchanged.
# --------------------------------------------------------------------------------------------------
def _reference_per_stock_attribution(stock_obs: list[dict], top_k: int) -> dict:
    returns_by_ticker: dict[str, list[float]] = defaultdict(list)
    sector_by_ticker: dict[str, object] = {}
    for obs in stock_obs:
        returns_by_ticker[obs["ticker"]].append(obs["return"])
        sector_by_ticker.setdefault(obs["ticker"], obs.get("sector"))
    rows = [
        {"ticker": ticker, "mean_return": mean(rets), "n": len(rets), "sector": sector_by_ticker[ticker]}
        for ticker, rets in returns_by_ticker.items()
    ]
    contributors = sorted(rows, key=lambda r: (-r["mean_return"], r["ticker"]))[:top_k]
    detractors = sorted(rows, key=lambda r: (r["mean_return"], r["ticker"]))[:top_k]
    return {"contributors": contributors, "detractors": detractors}


def _reference_attribution_slices(stock_obs: list[dict], cfg) -> dict:
    attribution = cfg.walk_forward.attribution
    sector_order = list(cfg.etfs.sector.values())
    band_order = [band.label for band in attribution.rank_bands]
    banded_obs = [
        {**obs, "rank_band": _rank_band_label(obs.get("rank"), attribution.rank_bands)}
        for obs in stock_obs
    ]
    return {
        "per_stock": _reference_per_stock_attribution(stock_obs, attribution.top_contributors_k),
        "by_sector": _group_means(stock_obs, "sector", "sector", sector_order, pad=False),
        "by_rank_band": _group_means(banded_obs, "rank_band", "rank_band", band_order, pad=True),
        "distribution": _distribution([obs["return"] for obs in stock_obs]),
    }


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
        # ops-hardening iter-32: `_attribution_slices`'s frozen `(stock_obs, cfg)` signature was lifted ON
        # PURPOSE for the real function's restructuring (TC-3). AUDIT iter-32: this reference calls the
        # PINNED pre-iter-32 attribution body above rather than the new `_attribution_slices` -- otherwise
        # this key would be compared against itself and TC-2 would cover only 9 of its 10 keys.
        "attribution": _reference_attribution_slices(stock_obs, cfg),
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


# ====================================================================================================
# ops-hardening iter-30 (AG-8, J-07) — `compute_forward_aggregates`'s OWN join-accumulator chunking.
#
# iter-14 above bounded the two SOURCE queries (streamed `.all()` -> `yield_per`); iter-30 bounds the
# CONTAINER those streamed rows land in (`ret_by_run_symbol`/`mdd_by_run_symbol`, still built as one
# un-sliced accumulator by `_reference_compute_forward_aggregates` above), which iter-29's audit found
# still held every distinct (run_id, symbol) pair of the FULL horizon-partition at once — the confirmed
# live `MemoryError` site (`forward_testing.py:965`). `_forward_agg_slice_map` + `walk_forward.
# forward_agg_run_chunk` (its OWN dedicated RUN-count knob — never `research.read_batch_size`, a ROWS
# knob, or `research.factor_join_run_chunk`, a different function's own knob) replace it with bounded,
# per-run-id-slice accumulation. `_reference_compute_forward_aggregates` never chunks by run, so it is
# reused (not re-pinned) as the byte-identity oracle for this dimension too.
# ====================================================================================================
def _cfg_run_chunk(run_chunk: int):
    """The real config with `walk_forward.forward_agg_run_chunk` overridden (chunk-width probe) — mirrors
    the row-batch `cfg.model_copy(update={"research": ...})` override pattern used above, for this
    iteration's own dedicated run-count knob."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"forward_agg_run_chunk": run_chunk})
    return cfg.model_copy(update={"walk_forward": wf})


def test_forward_agg_run_chunk_accumulator_is_bounded(multi_run_engine, monkeypatch):
    """TC-1: `compute_forward_aggregates`'s join accumulator (`_forward_agg_slice_map`'s return value,
    observed via monkeypatch) never holds more entries than ONE bounded chunk at any point — never one
    entry per distinct (run_id, symbol) pair across the whole 4-run (excluding the zero-FR 5th run)
    fixture (8 stocks + 4 benchmarks = 12 symbols/run)."""
    cfg = _cfg_run_chunk(1)  # 4 runs at width 1 -> 4 slices, one run id each
    observed_sizes: list[int] = []
    real_slice_map = forward_testing_module._forward_agg_slice_map

    def _wrapped(session, horizon, slice_run_ids, batch):
        result = real_slice_map(session, horizon, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(forward_testing_module, "_forward_agg_slice_map", _wrapped)
    with Session(multi_run_engine) as session:
        agg = compute_forward_aggregates(session, 20, cfg)

    total_pairs = 4 * (len(_STOCKS) + len(_BENCHMARKS))  # 4 runs x 12 symbols = 48, if ever unbounded
    assert agg["n_runs"] == 4, "sanity: the zero-FR 5th run must stay excluded"
    assert len(observed_sizes) == 4, f"expected 4 chunks (4 run ids at width 1), got {len(observed_sizes)}"
    assert max(observed_sizes) == len(_STOCKS) + len(_BENCHMARKS), (
        f"a single run's own slice must hold exactly its own symbol count, got {observed_sizes}"
    )
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once"
    )


@pytest.mark.parametrize("run_chunk", [1, 2, 4, 100])
@pytest.mark.parametrize("as_of", [None, HISTORICAL_AS_OF])
def test_compute_forward_aggregates_chunked_equals_reference_across_run_chunk_widths(
    multi_run_engine, run_chunk, as_of
):
    """TC-2: for EVERY configured horizon, the chunked `compute_forward_aggregates` stays byte-identical
    to the pinned (never-chunks-by-run) reference at run-chunk widths that produce 1 chunk (100, >= the
    4-run fixture), an even split (2), and maximum fragmentation (1, one run per chunk) — with and
    without `as_of`."""
    cfg = _cfg_run_chunk(run_chunk)
    with Session(multi_run_engine) as session:
        for horizon in HORIZONS:
            new_payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
            reference_payload = _reference_compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
            assert new_payload == reference_payload, (
                f"chunked != reference at run_chunk={run_chunk} horizon={horizon} as_of={as_of}"
            )


def test_forward_agg_run_chunk_boundary_never_splits_a_run(multi_run_engine):
    """Error case: a chunk boundary adjacent to (or isolating) every run must not double-count or drop
    that run's contribution — proved directly (not just via the full-dict equality above) by pinning a
    specific by-regime count/mean at maximum fragmentation (run_chunk=1) against the SAME figures at zero
    fragmentation (run_chunk=100, one chunk): r0/r3 are Risk-off, r1/r2 are Risk-on (2 runs each), so
    Risk-on's `n` must be exactly 2 runs' worth of stock observations at both widths, never doubled or
    dropped by isolating each run into its own chunk."""
    horizon = 20
    with Session(multi_run_engine) as session:
        fragmented = compute_forward_aggregates(session, horizon, _cfg_run_chunk(1))
        single_chunk = compute_forward_aggregates(session, horizon, _cfg_run_chunk(100))
    frag_regime = {r["regime"]: r for r in fragmented["by_regime"]}
    single_regime = {r["regime"]: r for r in single_chunk["by_regime"]}
    for label in ("Risk-on", "Risk-off"):
        assert frag_regime[label]["n"] == single_regime[label]["n"] == 2 * len(_STOCKS)
        assert frag_regime[label]["mean_return"] == pytest.approx(single_regime[label]["mean_return"])


@pytest.fixture()
def sparse_chunk_engine(tmp_path):
    """A run (r_sparse) that DOES carry a forward return (so it legitimately enters `runs_with_fr` and its
    chunk IS processed) but whose OWN scored ticker has NO matching forward return at all — an
    ALL-EXCLUDED chunk (zero qualifying `stock_obs` rows) when isolated at `forward_agg_run_chunk=1`, the
    error case a run-chunked merge must survive without crashing or fabricating a value."""
    engine = make_engine(f"sqlite:///{tmp_path / 'sparse_chunk.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        run = ScannerRun(
            asof_date=date(2025, 8, 1), created_at=_utc(), provider="seed", benchmark="SPY",
            regime_score=50.0, regime_label="Risk-on", regime_components_json="[]",
            new_high_low_json="{}", candidate_counts_json="{}",
        )
        session.add(run)
        session.flush()
        # scored, but NEVER given a ForwardReturn at any horizon -> always excluded, never fabricated
        session.add(ScannerResult(
            run_id=run.id, ticker="NOFR", name="NOFR", sector="Technology",
            leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0, entry_quality_bucket="E",
            risk_score=0.0, risk_bucket="E", setup_status="Actionable", rank=1, record_json="{}",
        ))
        # the ONLY forward return this run carries is a benchmark's -> the run legitimately enters
        # runs_with_fr / the SPY benchmark list, even though its own chunk yields zero stock_obs rows.
        session.add(ForwardReturn(
            run_id=run.id, symbol="SPY", horizon=20, asof_date=date(2025, 8, 1),
            entry_close=100.0, measured_date=date(2025, 9, 1), realized_return=0.07, max_drawdown=-0.03,
        ))
        session.commit()
    return engine


def test_forward_agg_all_excluded_chunk_does_not_crash_the_merge(sparse_chunk_engine):
    """Error case: an all-excluded chunk (zero qualifying `stock_obs` observations) must not crash the
    merge, and must never fabricate a value for the excluded ticker — it simply contributes nothing, while
    the run still legitimately counts via its own benchmark return."""
    cfg = _cfg_run_chunk(1)  # isolates the sparse run into its own (all-excluded) chunk
    with Session(sparse_chunk_engine) as session:
        agg = compute_forward_aggregates(session, 20, cfg)
    assert agg["n_runs"] == 1, "the run still legitimately enters runs_with_fr via its SPY return"
    assert agg["overall"]["n"] == 0, "NOFR has no forward return anywhere -> zero stock observations"
    assert agg["excess"]["vs_spy"]["benchmark_n"] == 1
    assert agg["excess"]["vs_spy"]["benchmark_mean"] == pytest.approx(0.07)
    tickers = {
        row["ticker"]
        for row in agg["attribution"]["per_stock"]["contributors"] + agg["attribution"]["per_stock"]["detractors"]
    }
    assert "NOFR" not in tickers


# ----------------------------------------------------------------------------------------------------
# TC-3 — the SHIPPED `walk_forward.forward_agg_run_chunk` must actually chunk on the live basis
# (iter-29's binding lesson: a knob that degenerates to one chunk on the real basis binds nothing).
# ----------------------------------------------------------------------------------------------------
# The live basis measured during the iter-30 audit (direct read of the committed `trendora.db`,
# 2026-07-29): 1,813-1,872 distinct scanner runs per horizon. A run-chunk width at/above the run count
# degenerates to a single chunk, so the shipped width must stay well below it with room for years of
# further daily-cadence growth; 500 is the loosest ceiling that still forces real chunking on today's
# basis (>=3 chunks) and would have caught a shipped value re-using `research.read_batch_size` (2000).
_MAX_MEANINGFUL_RUN_CHUNK = 500


def test_shipped_forward_agg_run_chunk_actually_binds_on_the_live_basis():
    """The SHIPPED `walk_forward.forward_agg_run_chunk` must be small enough to produce real chunking
    against a multi-year daily-cadence basis — the regression guard for iter-29's binding lesson (a width
    reused from another function's own knob, or otherwise too close to the live run count, means one
    chunk and zero peak reduction, while every unit proof still passes because it typically overrides the
    knob to a small fixture-sized value)."""
    width = load_config().walk_forward.forward_agg_run_chunk
    assert 1 <= width <= _MAX_MEANINGFUL_RUN_CHUNK, (
        f"walk_forward.forward_agg_run_chunk={width} cannot bound the join accumulator on the live basis "
        f"(1,813-1,872 distinct runs/horizon): it must be <= {_MAX_MEANINGFUL_RUN_CHUNK}"
    )


def test_forward_aggregates_chunks_at_the_shipped_config(tmp_path, monkeypatch):
    """The accumulator is chunk-bounded under the SHIPPED config — no override. Builds a fixture with
    (shipped width + 3) runs so real chunking is REQUIRED, then asserts `compute_forward_aggregates` made
    >= 2 slice reads and no single slice ever held the whole fixture's (run_id, symbol) pairs."""
    cfg = load_config()  # the REAL config.yaml — deliberately NOT overridden
    width = cfg.walk_forward.forward_agg_run_chunk
    horizon = cfg.walk_forward.horizons[0]
    n_runs, tickers = width + 3, ("AA", "BB")
    engine = make_engine(f"sqlite:///{tmp_path / 'shipped_chunk.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for i in range(n_runs):
            run = ScannerRun(
                asof_date=date(2025, 1, 1) + timedelta(days=i), created_at=_utc(),
                provider="seed", benchmark="SPY", regime_score=50.0, regime_label="Risk-on",
                regime_components_json="[]", new_high_low_json="{}", candidate_counts_json="{}",
            )
            session.add(run)
            session.flush()
            for j, base in enumerate(tickers):
                ticker = f"{base}{i}"
                session.add(ScannerResult(
                    run_id=run.id, ticker=ticker, name=ticker, sector="Technology",
                    leadership_score=50.0, leadership_bucket="A", entry_quality_score=0.0,
                    entry_quality_bucket="E", risk_score=0.0, risk_bucket="E",
                    setup_status="Actionable", rank=j + 1, record_json="{}",
                ))
                session.add(ForwardReturn(
                    run_id=run.id, symbol=ticker, horizon=horizon, asof_date=run.asof_date,
                    entry_close=100.0, measured_date=date(2025, 12, 31),
                    realized_return=0.01 * (i + 1) + 0.001 * j, max_drawdown=-0.02,
                ))
        session.commit()

    observed_sizes: list[int] = []
    real_slice_map = forward_testing_module._forward_agg_slice_map

    def _wrapped(session, h, slice_run_ids, batch):
        result = real_slice_map(session, h, slice_run_ids, batch)
        observed_sizes.append(len(result))
        return result

    monkeypatch.setattr(forward_testing_module, "_forward_agg_slice_map", _wrapped)
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, horizon, cfg)

    total_pairs = n_runs * len(tickers)
    assert agg["overall"]["n"] == total_pairs, "sanity: every fixture pair must surface as an observation"
    assert len(observed_sizes) >= 2, (
        f"the SHIPPED config produced {len(observed_sizes)} chunk(s) over {n_runs} runs — the accumulator "
        f"bound is inert at the real configuration (width={width})"
    )
    assert max(observed_sizes) <= width * len(tickers), "a slice exceeded its configured run-chunk width"
    assert max(observed_sizes) < total_pairs, (
        "the live accumulator must never hold the WHOLE fixture's pairs at once under the shipped config"
    )


def test_shipped_forward_agg_run_chunk_binds_against_the_real_committed_seed():
    """TC-3 (literal): against the LIVE committed seed DB's ACTUAL distinct-run count for a representative
    horizon (never a fixture-sized width) — read-only, no ORM/engine machinery, a single indexed
    COUNT(DISTINCT run_id) query — the shipped chunk width produces more than one chunk. Skips when the
    committed seed DB is absent (matches `test_start_backend_script.py`'s established `REAL_DB`
    convention)."""
    if not REAL_DB.exists():
        pytest.skip(f"real committed seed DB not found at {REAL_DB} — nothing to measure against")
    cfg = load_config()
    width = cfg.walk_forward.forward_agg_run_chunk
    horizon = cfg.walk_forward.default_horizon
    conn = sqlite3.connect(f"file:{REAL_DB}?mode=ro", uri=True)
    try:
        cur = conn.execute(
            "SELECT COUNT(DISTINCT run_id) FROM forward_returns WHERE horizon = ?", (horizon,)
        )
        (live_run_count,) = cur.fetchone()
    finally:
        conn.close()
    assert live_run_count > 0, "sanity: the committed seed must carry forward returns at the default horizon"
    n_chunks = (live_run_count + width - 1) // width
    assert n_chunks > 1, (
        f"walk_forward.forward_agg_run_chunk={width} against the LIVE seed's {live_run_count} distinct "
        f"runs at horizon={horizon} produces only {n_chunks} chunk(s) — the bound is inert on the real basis"
    )


# ====================================================================================================
# ops-hardening iter-32 (AG-8, J-07) — `stock_obs`, the LAST unbounded accumulator in this function's own
# family, is gone: `_group_means`/`_group_mdd`/`_control_groups`'s per-group/per-run consumers and
# `_attribution_slices`'s `per_stock`/`by_sector`/`by_rank_band` are now driven by state built
# INCREMENTALLY inside the per-chunk loop, bounded by the number of distinct groups/runs/tickers rather
# than by the observation count. This section proves the bound (TC-1) — a test that fails if the
# restructuring were reverted to the old full-`stock_obs` design.
#
# This test feeds synthetic observations DIRECTLY into the same accumulation primitives
# `compute_forward_aggregates` uses internally (`_GroupAcc`/`_accumulate_group`/`_AttributionAccumulator`),
# bypassing the DB/ORM read path entirely -- a dev-pass measurement discovered that going through the real
# `compute_forward_aggregates(session, ...)` call confounds this iteration's accumulators with `run_rows`
# (`session.exec(select(ScannerRun)...).all()`, one ORM object per RUN, unchanged since iter-14 and
# EXPLICITLY documented there as "bounded, small... not one of the named unbounded offenders this
# iteration fixes" -- verified separately: tripling run count alone roughly triples `run_rows`'s own
# tracemalloc peak, which would make a whole-function measurement fail for a reason THIS iteration never
# claimed to fix). Isolating the accumulation step targets exactly what TC-1 asks about; the live
# full-deep-basis warm (TC-4/TC-5, see the dev handoff) is the end-to-end proof that the real function
# does not crash at the actual ~800K-observation live scale.
# ====================================================================================================
def _accumulate_synthetic_observations(n_obs: int, rank_bands, *, retain_distribution: bool = True):
    """Feeds `n_obs` synthetic observations through the SAME per-observation accumulation primitives
    `compute_forward_aggregates` calls inside its per-chunk loop, at a FIXED small cardinality (3 tickers,
    1 sector, 1 bucket, 1 setup, 2 regimes) -- returns the resulting accumulators (never a per-observation
    list).

    `retain_distribution=False` drops each observation's realized return immediately after it has been
    accumulated, so the measured state is EXACTLY the quantity TC-1 names -- "peak size attributable to
    the by-group/per-stock accumulation paths" -- with the spec's ONE disclosed still-O(N) exception
    (`_AttributionAccumulator.returns`, the bare-float list the exact median/dispersion needs) excluded by
    construction. Nothing else reads that list, so clearing it changes no accumulated group/ticker state
    (audit iter-32)."""
    bucket_accs: dict = defaultdict(_GroupAcc)
    setup_accs: dict = defaultdict(_GroupAcc)
    regime_accs: dict = defaultdict(_GroupAcc)
    attribution_acc = _AttributionAccumulator(rank_bands)
    tickers = ("AAA", "BBB", "CCC")
    for i in range(n_obs):
        realized, mdd = 0.001 * (i + 1), -0.01
        obs = {"ticker": tickers[i % 3], "return": realized, "max_drawdown": mdd, "sector": "Technology", "rank": 1}
        _accumulate_group(bucket_accs, "A", realized, mdd)
        _accumulate_group(setup_accs, "Actionable", realized, mdd)
        _accumulate_group(regime_accs, "Risk-on" if i % 2 == 0 else "Risk-off", realized, mdd)
        attribution_acc.add(obs)
        if not retain_distribution:
            attribution_acc.returns.clear()
    return bucket_accs, setup_accs, regime_accs, attribution_acc


def test_accumulator_peak_size_does_not_scale_with_observation_count_at_fixed_cardinality():
    """TC-1: at a FIXED small group/ticker cardinality (3 tickers, 1 sector, 1 bucket, 1 setup, 2 regimes),
    quintupling the observation count (40 -> 200) must not come CLOSE to quintupling the tracemalloc-
    measured peak of the by-group/per-stock accumulation paths -- calibrated against a dev-pass
    measurement of the OLD full-`stock_obs`-list design under the SAME 5x delta (peak ratio ~5.6x, close
    to proportional, as expected for a genuine per-observation list): the new design's ratio measures
    ~2.0-2.8x across several (n_small, n_large) pairs at this delta (the ONE disclosed exception,
    `_AttributionAccumulator.returns`'s bare-float `distribution` list, does still grow linearly, so the
    ratio is not 1.0x -- only proportional-to-old growth would be a regression). The 4.0x threshold below
    sits with margin above the new design's observed range and with margin below the old design's, so this
    test fails if the restructuring were reverted.

    AUDIT iter-32 -- second assertion added. The first assertion's metric INCLUDES the spec's disclosed
    still-O(N) `distribution` list, so it is scale-dependent by construction: measured on the SHIPPED
    (correct) code it is 2.00x at 40->200 but 4.70x at 5,000->25,000 and 4.77x at 20,000->100,000, i.e. it
    converges on fully-proportional growth as the surviving linear term stops being diluted by fixed
    overhead. It therefore discriminates against the old design only at the small n it was calibrated at.
    The second assertion below measures what TC-1 actually names -- the by-group/per-stock accumulation
    paths alone -- at a 5x delta two orders of magnitude larger, where the shipped design measures 1.29x
    (25.5 kB -> 27.8 kB; the residual growth is `_ExactMeanAcc`'s DISTINCT-denominator partials, bounded by
    the exponent range of IEEE-754 doubles, never by n) against ~5.1x for the reverted full-`stock_obs`
    design. That assertion is scale-robust: it holds at 20,000->100,000 too (1.09x)."""
    rank_bands = load_config().walk_forward.attribution.rank_bands
    n_small, n_large = 40, 200

    def _peak(n: int, *, retain_distribution: bool = True) -> int:
        # warm up (import/dict-resize caches)
        _accumulate_synthetic_observations(n, rank_bands, retain_distribution=retain_distribution)
        tracemalloc.start()
        try:
            _accumulate_synthetic_observations(n, rank_bands, retain_distribution=retain_distribution)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        return peak

    peak_small, peak_large = _peak(n_small), _peak(n_large)

    assert peak_large < peak_small * 4.0, (
        f"peak memory grew from {peak_small} to {peak_large} bytes when observation count went from "
        f"{n_small} to {n_large} (5x) at a fixed 3-ticker/1-sector/1-bucket/1-setup/2-regime cardinality — "
        f"the by-group/per-stock accumulation paths must not scale proportionally with observation count "
        f"(TC-1)"
    )

    # TC-1 as the spec words it: the by-group/per-stock accumulation paths ALONE (the disclosed bare-float
    # `distribution` list excluded), at a delta where a per-observation retention would be unmistakable.
    iso_small, iso_large = 5_000, 25_000
    iso_peak_small = _peak(iso_small, retain_distribution=False)
    iso_peak_large = _peak(iso_large, retain_distribution=False)

    assert iso_peak_large < iso_peak_small * 2.0, (
        f"by-group/per-stock accumulation state grew from {iso_peak_small} to {iso_peak_large} bytes when "
        f"observation count went from {iso_small} to {iso_large} (5x) at FIXED group/ticker cardinality — "
        f"these paths must be bounded by the number of DISTINCT groups/tickers, never by the observation "
        f"count (TC-1; shipped design measures ~1.3x here, the reverted full-`stock_obs` design ~5.1x)"
    )
