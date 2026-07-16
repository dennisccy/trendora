"""Walk-forward forward-testing engine (Data Contract: app.engine.forward_testing).

This module turns the immutable as-of snapshots into hard, forward-tested evidence — the product's
keystone "does the ranking actually work?" capability (J-09, J-10). The as-of-scoped aggregate
(`compute_forward_aggregates(..., as_of=D)`, an expanding window of snapshots dated <= D) is served on
`GET /api/backtest` under the single global as-of control (iter-17 relocated it off the retired
System Health page, so the evidence has exactly one home).

THREE no-negotiable disciplines, each unit-proved:

  1. NO LOOKAHEAD (forward direction). A realized forward return is measured ONLY from POST-snapshot
     bars: the entry is the close ON the run's `asof_date` D (`close_on`, date <= D) and the exit is
     the close of the h-th bar with date > D (`bars_after`, date > D). A future bar can therefore
     never influence an as-of score — the scoring side reads `bars_asof` (date <= D), this side reads
     strictly date > D, and the two never overlap.

  2. IMMUTABLE SNAPSHOTS. Forward returns are written ONLY to the separate append-only `forward_returns`
     table, keyed to the snapshot by `run_id`. The backfill performs INSERTs exclusively — it never
     UPDATEs a `scanner_runs` / `scanner_results` / `*_scores` row — and is idempotent (a second boot
     inserts zero new rows).

  3. SINGLE SOURCE OF TRUTH. `compute_forward_aggregates` READS the stored canonical bucket / setup /
     sector / rank / VCP flag (from `scanner_results`) and regime label (from `scanner_runs`) VERBATIM
     and groups the stored realized returns by them. It NEVER recomputes a score, bucket, setup, or
     VCP flag from a second formula — they are read, not re-derived (the `by_vcp` cohort breakdown
     groups the stored `is_vcp` mirror exactly like `by_setup`/`by_bucket`).

Every aggregate cell carries its sample size `n`, the payload carries the `min_sample` honesty
threshold and a `survivorship_bias` label, and a (symbol, horizon) with fewer than `horizon` post-
snapshot bars contributes NO row (n=0) — never a fabricated 0% (anti-goal: No fabricated data). Every
tunable (replay window, cadence, horizons, min_sample, control-group seed/top_n/peers_per_sector,
benchmark symbols) comes from config — no walk-forward literal lives here (anti-goal: No magic numbers).
"""
from __future__ import annotations

import json
import random
from calendar import monthrange
from collections import defaultdict
from datetime import date as date_cls, datetime, timedelta, timezone
from statistics import mean, median, stdev
from typing import Optional, Union

from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
from app.engine.scanner import run_scan
from app.engine.setups import ALL_STATUSES
from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun

# The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). iter-18: the
# basis now spans ~30 years (1996 -> present, per-name real listing depth) over the broadened
# point-in-time candidate pool — but the pool itself is built from CURRENT index constituents, so
# truly delisted names (absent from the free feed) are still missing across that whole span.
SURVIVORSHIP_BIAS_LABEL = (
    "Walk-forward evidence now spans up to ~30 years of history (1996 to present, each name from its "
    "real first bar), but it is measured over a candidate pool built from CURRENT index members and "
    "therefore carries survivorship bias: names that were delisted or dropped along the way are absent "
    "from the whole span, so realized forward returns may be overstated. Read the edge as an upper "
    "bound, not a guarantee."
)

# The A-E bucket vocabulary (string labels, not tunables) in display order — strongest to weakest.
BUCKET_ORDER = ("A", "B", "C", "D", "E")

# The VCP cohort labels (iter-11): the stored `is_vcp` boolean -> its display cohort label. Two
# cohorts always emitted (VCP first, then non-VCP), padded to n=0 when a cohort has no observation.
VCP_LABELS = {True: "VCP", False: "non-VCP"}
# The two new detected-pattern cohort labels (iter-9), same design as VCP_LABELS — the stored
# `is_<name>` boolean -> its display cohort label; flagged cohort first, then the non-flagged one.
PULLBACK_LABELS = {True: "Pullback-to-DMA", False: "non-Pullback"}
FLAT_BASE_LABELS = {True: "Flat-base", False: "non-Flat-base"}

MONTHS_PER_YEAR = 12  # calendar constant (structural, not a scoring tunable)
QUARTER_MONTHS = 3    # calendar constant (structural, not a scoring tunable)


# --------------------------------------------------------------------------------------------------
# Benchmark + forward-return symbol sets (from config — never literal tickers)
# --------------------------------------------------------------------------------------------------
def benchmark_symbols(cfg: Config) -> dict:
    """The benchmark tickers, all read from config: SPY + QQQ (`etfs.index`) and the sector ETFs
    (`etfs.sector`). Used both as forward-return symbols and as control-group comparators."""
    return {
        "spy": cfg.etfs.index[0],
        "qqq": cfg.etfs.index[1],
        "sector_etfs": list(cfg.etfs.sector.keys()),
    }


def forward_symbols(cfg: Config) -> list[str]:
    """Every benchmark symbol a forward return is ALWAYS stored for (the excess-return controls): the
    index ETFs SPY + QQQ and the sector ETFs, de-duplicated and order-preserving. PLUS the full static
    `config.universe.symbols` list as a back-compat superset.

    J-93: the WRITE paths no longer apply this list uniformly to every run — they call
    `forward_symbols_for_run(run, cfg)` so each run stores forward returns for the names that run
    ACTUALLY scored (its point-in-time-resolved membership) ∪ the benchmarks. Kept here as the
    order-preserving union for callers that still want the global superset and for the benchmark base."""
    bm = benchmark_symbols(cfg)
    ordered: list[str] = []
    seen: set[str] = set()
    for symbol in [*cfg.universe.symbols, bm["spy"], bm["qqq"], *bm["sector_etfs"]]:
        if symbol not in seen:
            seen.add(symbol)
            ordered.append(symbol)
    return ordered


def forward_symbols_for_run(session: Session, run: "ScannerRun", cfg: Config) -> list[str]:
    """J-93: the forward-return symbol set for ONE run = that run's STORED `ScannerResult` tickers
    (its point-in-time-resolved membership — the SINGLE source, never a second universe computation)
    UNION the benchmark ETFs (SPY/QQQ/sector ETFs always present, so the excess-return math has its
    controls on every run). De-duplicated, order-preserving (the run's scored members first, then the
    benchmarks). The no-lookahead boundary is unchanged: each (symbol, horizon) still reads `close_on`
    on D and `bars_after` (date > D) — only WHICH symbols are iterated narrows to the run's membership,
    so a name not resolved at the run's date stores no return for it (honest n=0), and a name that WAS
    resolved stores byte-identical returns to before."""
    bm = benchmark_symbols(cfg)
    scored = list(
        session.exec(
            select(ScannerResult.ticker).where(ScannerResult.run_id == run.id).order_by(ScannerResult.rank)
        ).all()
    )
    ordered: list[str] = []
    seen: set[str] = set()
    for symbol in [*scored, bm["spy"], bm["qqq"], *bm["sector_etfs"]]:
        if symbol not in seen:
            seen.add(symbol)
            ordered.append(symbol)
    return ordered


def _sector_etf_by_name(cfg: Config) -> dict[str, str]:
    """sector NAME -> sector ETF ticker (reverse of config.etfs.sector). A stored stock row carries
    its sector NAME (config.stock_sectors), so this resolves the matching sector ETF for a control."""
    return {name: ticker for ticker, name in cfg.etfs.sector.items()}


# --------------------------------------------------------------------------------------------------
# Pure forward-return math (the keystone no-lookahead boundary)
# --------------------------------------------------------------------------------------------------
def forward_return(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[float]:
    """Realized return over `horizon` trading days = close of the h-th POST-snapshot bar / `entry_close`
    - 1, where `entry_close` is the close ON the as-of date D and `bars_after_list` is the ascending
    list of bars with date > D (from `bars_after`). Only the first `horizon` post-bars matter, so the
    result is unchanged when later bars are removed.

    Returns None (NA) — NEVER a fabricated/truncated number — when `entry_close` is missing or zero, or
    when fewer than `horizon` post-snapshot bars exist (the realized return is not yet observable)."""
    if entry_close is None or entry_close == 0:
        return None
    if len(bars_after_list) < horizon:
        return None
    measured_close = bars_after_list[horizon - 1].close
    return measured_close / entry_close - 1


def forward_excursions(
    bars_after_list: list, entry_close: Optional[float], horizon: int
) -> Optional[dict]:
    """Post-snapshot path excursions over `horizon` trading days (iter-14, J-29): the max ADVERSE
    excursion `mae = min(low_i)/entry_close - 1` (<= ~0) and max FAVORABLE excursion
    `mfe = max(high_i)/entry_close - 1` (>= ~0) over the FIRST `horizon` bars of `bars_after_list`
    (date > D, from `bars_after`), reading each bar's `.low` / `.high`. `entry_close` is the close ON
    the as-of date D — the SAME entry the realized return uses — so the realized close at h lies within
    the [mae, mfe] band (asserted in tests).

    Shares the EXACT no-lookahead NA gate as `forward_return`: returns None (NA) — NEVER a fabricated/
    truncated excursion — when `entry_close` is missing or zero, or when fewer than `horizon` post-
    snapshot bars exist. Only the first `horizon` post-bars matter, so the result is unchanged when
    later bars are removed (the keystone no-lookahead-of-the-future-tail property)."""
    if entry_close is None or entry_close == 0:
        return None
    if len(bars_after_list) < horizon:
        return None
    window = bars_after_list[:horizon]
    low = min(bar.low for bar in window)
    high = max(bar.high for bar in window)
    return {"mae": low / entry_close - 1, "mfe": high / entry_close - 1}


def max_drawdown(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[float]:
    """The TRUE max drawdown (worst peak-to-trough decline, J-86) over the FIRST `horizon` post-snapshot
    bars (date > D, from `bars_after`):

        MDD = min over j of ( low_j / max(entry_close, high_1..high_j) - 1 )

    i.e. for each post-snapshot bar j we measure the drop from the RUNNING PEAK (the highest high seen so
    far, seeded at the as-of-D `entry_close`) down to that bar's low, and keep the worst (most negative)
    such drop. The running peak is seeded at `entry_close` so the very first bar's drawdown is measured
    from the entry, and a bar that prints a new high raises the peak for subsequent bars only. The result
    is <= 0 always (a flat/rising series with no low below its running peak yields 0.0 — never positive).

    Forward-side only and shares the EXACT no-lookahead NA gate as `forward_return`/`forward_excursions`:
    returns None (NA) — NEVER a fabricated 0 — when `entry_close` is missing or zero, or when fewer than
    `horizon` post-snapshot bars exist. Only the first `horizon` post-bars matter (the running peak +
    trough scan stops at bar `horizon`), so the result is unchanged when later bars are removed (the
    keystone no-lookahead-of-the-future-tail property)."""
    if entry_close is None or entry_close == 0:
        return None
    if len(bars_after_list) < horizon:
        return None
    window = bars_after_list[:horizon]
    running_peak = entry_close  # the running peak seeded at the as-of-D close (the entry)
    drawdowns: list[float] = []
    for bar in window:
        if bar.high > running_peak:
            running_peak = bar.high
        # drop from the running peak to this bar's low. Since low <= high <= running_peak (the running max
        # high, >= entry_close), `low / running_peak - 1` is intrinsically <= 0 for every bar — so the
        # min over them is <= 0 WITHOUT any seed literal (the window is non-empty: len >= horizon >= 1).
        drawdowns.append(bar.low / running_peak - 1)
    return min(drawdowns)


def underwater_days(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[int]:
    """iter-41 (J-25): the count of the FIRST `horizon` post-snapshot bars (date > D, from `bars_after`)
    whose CLOSE sits below the RUNNING high-water mark — the SAME running-peak convention `max_drawdown`
    uses (seeded at the as-of-D `entry_close`; a bar that prints a new HIGH raises the peak for THAT
    bar's own close-check too, mirroring `max_drawdown`'s bar-by-bar order of operations exactly: the
    peak is updated with `bar.high` BEFORE the bar's own close is compared to it). A bar that closes
    exactly AT its own freshly-raised peak (`close == running_peak`) is NOT counted underwater.

    Shares the EXACT no-lookahead NA gate as `forward_return`/`max_drawdown`: returns None (NA) — NEVER
    a fabricated 0 — when `entry_close` is missing or zero, or when fewer than `horizon` post-snapshot
    bars exist. Only the first `horizon` post-bars matter, so the result is unchanged when later bars
    are removed (the keystone no-lookahead-of-the-future-tail property)."""
    if entry_close is None or entry_close == 0:
        return None
    if len(bars_after_list) < horizon:
        return None
    window = bars_after_list[:horizon]
    running_peak = entry_close
    count = 0
    for bar in window:
        if bar.high > running_peak:
            running_peak = bar.high
        if bar.close < running_peak:
            count += 1
    return count


def time_to_recover_days(bars_after_list: list, entry_close: Optional[float], horizon: int) -> Optional[int]:
    """iter-41 (J-25): the number of bars from the max-drawdown TROUGH (the SAME running-peak trough
    `max_drawdown` identifies as the worst peak-to-trough drop, over the FIRST `horizon` post-snapshot
    bars) until the close FIRST returns to/above the entry level (`close >= entry_close`), counted
    within the SAME `horizon`-bar window. 0 when the trough bar's own close already sits at/above the
    entry level. None (NA — never a fabricated horizon-sentinel) when the close never recovers to the
    entry level within the window, or when the shared NA gate applies.

    Internally re-derives the SAME running-peak per-bar drawdown series `max_drawdown` computes, ONLY to
    locate the trough's bar INDEX (which `max_drawdown` does not expose) — it does not re-implement or
    alter the canonical `max_drawdown` function itself (never forked; `test_time_to_recover_days_
    counts_bars_from_trough_to_entry_reclaim` pins the located trough's value against `max_drawdown`'s
    own return value for the SAME inputs).

    Shares the EXACT no-lookahead NA gate as `forward_return`/`max_drawdown`. Only the first `horizon`
    post-bars matter, so the result is unchanged when later bars are removed (the keystone no-lookahead-
    of-the-future-tail property)."""
    if entry_close is None or entry_close == 0:
        return None
    if len(bars_after_list) < horizon:
        return None
    window = bars_after_list[:horizon]
    running_peak = entry_close
    drawdowns: list[float] = []
    for bar in window:
        if bar.high > running_peak:
            running_peak = bar.high
        drawdowns.append(bar.low / running_peak - 1)
    trough_index = min(range(len(drawdowns)), key=lambda i: drawdowns[i])  # first index at the worst drop
    for offset, bar in enumerate(window[trough_index:]):
        if bar.close >= entry_close:
            return offset
    return None  # never recovered within the horizon window


# --------------------------------------------------------------------------------------------------
# Walk-forward as-of date set (cadence intersected with real seed trading days)
# --------------------------------------------------------------------------------------------------
def _add_months(d: date_cls, months: int) -> date_cls:
    """`d` shifted by `months` (may be negative), clamping the day to the target month's length."""
    total = d.month - 1 + months
    year = d.year + total // MONTHS_PER_YEAR
    month = total % MONTHS_PER_YEAR + 1
    day = min(d.day, monthrange(year, month)[1])
    return date_cls(year, month, day)


def _advance(d: date_cls, asof_cadence: str) -> date_cls:
    """The next calendar cadence target after `d` (snapped to a real trading day by the caller)."""
    if asof_cadence == "daily":
        return d + timedelta(days=1)
    if asof_cadence == "weekly":
        return d + timedelta(weeks=1)
    if asof_cadence == "monthly":
        return _add_months(d, 1)
    return _add_months(d, QUARTER_MONTHS)  # quarterly


def _snap_back(target: date_cls, trading_days: list[date_cls]) -> Optional[date_cls]:
    """The latest trading day <= `target` (no fabricated as-of dates), or None if before all data."""
    lo, hi = 0, len(trading_days)
    while lo < hi:
        mid = (lo + hi) // 2
        if trading_days[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return trading_days[lo - 1] if lo > 0 else None


def walk_forward_asof_dates(session: Session, config: Optional[Config] = None) -> list[date_cls]:
    """The bounded walk-forward as-of date set: starting `history_years` before the latest data date,
    stepping at `asof_cadence`, each target snapped to the latest real trading day <= it, and capped at
    the cutoff that still leaves >= max(horizons) POST-snapshot bars (so every cadence run has a full
    forward window). Intersected with actual seed trading days; de-duplicated and ascending."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    benchmark = cfg.etfs.index[0]  # SPY defines the trading calendar
    latest = latest_data_date(session)
    if latest is None:
        return []
    trading_days = [bar.date for bar in bars_asof(session, benchmark, latest)]
    max_h = max(wf.horizons)
    if len(trading_days) <= max_h:
        return []
    cutoff = trading_days[-(max_h + 1)]  # this date has exactly max_h trading days after it
    window_start = _add_months(latest, -MONTHS_PER_YEAR * wf.history_years)

    targets: list[date_cls] = []
    target = window_start
    while target <= cutoff:
        targets.append(target)
        target = _advance(target, wf.asof_cadence)

    asof: set[date_cls] = set()
    for target in targets:
        snapped = _snap_back(target, trading_days)
        if snapped is not None and snapped <= cutoff:
            asof.add(snapped)
    return sorted(asof)


# --------------------------------------------------------------------------------------------------
# Backfill — persist the cadence snapshots, then INSERT realized forward returns (idempotent)
# --------------------------------------------------------------------------------------------------
def _insert_run_forward_returns(
    session: Session,
    run: ScannerRun,
    symbols: list[str],
    horizons,
    max_h: int,
    existing: set,
) -> int:
    """INSERT the missing realized forward returns for ONE run; return how many rows were inserted.

    This is the SINGLE implementation of the forward-return INSERT (entry = the close ON D via
    `close_on`, exit = the h-th post-D bar via `bars_after` + `forward_return`), factored out of
    `_backfill` so the walk-forward boot AND the per-date `backfill_run_forward_returns` share exactly
    ONE forward-return formula (no second math path). Only keys absent from `existing` are inserted
    (idempotent), and `existing` is updated in place. INSERT-only — it never UPDATEs/overwrites a
    snapshot row. A (symbol, horizon) with fewer than `horizon` post-D bars contributes nothing
    (NA, n=0) — never a fabricated 0% (anti-goal: No fabricated data)."""
    inserted = 0
    for symbol in symbols:
        # Idempotency fast-path: if every horizon for this (run, symbol) is already persisted, skip the
        # price fetches entirely — so a warm re-run does no redundant bar materialization.
        needed = [h for h in horizons if (run.id, symbol, h) not in existing]
        if not needed:
            continue
        entry_close = close_on(session, symbol, run.asof_date)  # close ON D (date <= D)
        if entry_close is None:
            continue
        post_bars = bars_after(session, symbol, run.asof_date, limit=max_h)  # date > D, bounded
        if not post_bars:
            continue  # no post-snapshot bar -> nothing to measure (n=0)
        for horizon in needed:
            realized = forward_return(post_bars, entry_close, horizon)
            if realized is None:
                continue  # fewer than `horizon` post-bars -> NA, no fabricated row
            # iter-14 (J-29): the SAME post_bars/entry_close/horizon already in hand, no extra query —
            # excursions share forward_return's NA gate, so they are non-None whenever realized is.
            excursions = forward_excursions(post_bars, entry_close, horizon)
            # iter-27 (J-86): the max-drawdown over the SAME first-`horizon` post-bars window, computed
            # once here beside mae/mfe via the pure helper that shares the EXACT NA gate — so a row's
            # max_drawdown is non-None iff realized_return is (never a fabricated 0 for a short window).
            mdd = max_drawdown(post_bars, entry_close, horizon)
            # iter-41 (J-25): the two "dry spell" columns over the SAME post_bars/entry_close/horizon
            # already in hand — zero extra bar reads. underwater_days shares the EXACT NA gate as
            # max_drawdown (non-None iff realized is); time_to_recover_days is additionally None when the
            # close never reclaims the entry level within the window (never a fabricated sentinel).
            uw_days = underwater_days(post_bars, entry_close, horizon)
            ttr_days = time_to_recover_days(post_bars, entry_close, horizon)
            session.add(
                ForwardReturn(
                    run_id=run.id,
                    symbol=symbol,
                    horizon=horizon,
                    asof_date=run.asof_date,
                    entry_close=entry_close,
                    measured_date=post_bars[horizon - 1].date,
                    realized_return=realized,
                    mae=excursions["mae"] if excursions else None,
                    mfe=excursions["mfe"] if excursions else None,
                    max_drawdown=mdd,
                    underwater_days=uw_days,
                    time_to_recover_days=ttr_days,
                )
            )
            existing.add((run.id, symbol, horizon))
            inserted += 1
    return inserted


def _commit_forward_returns_concurrency_safe(session: Session) -> None:
    """Commit pending forward-return INSERTs, tolerating a concurrent-INSERT race (iter-28, J-41).

    The forward-return INSERT path builds an in-process `existing` set then INSERTs only the missing
    (run_id, symbol, horizon) keys. When two warm-ups (e.g. an in-flight background warm-up and a
    concurrent boot) both pass that in-memory check for the SAME key, one commit wins and the other
    fires the `(run_id, symbol, horizon)` UNIQUE constraint (`IntegrityError`). Because forward returns
    are a DETERMINISTIC function of the frozen seed, the winning writer's row is byte-identical to ours,
    so the safe resolution is to ROLL BACK our duplicate INSERTs (discarding only the redundant rows) —
    never raising, never writing a duplicate, never overwriting an existing append-only row (anti-goal:
    Snapshots are immutable; forward_returns is append-only + idempotent). The caller re-reads `existing`
    on the next pass / next boot and INSERTs only the genuinely-missing remainder (idempotent)."""
    try:
        session.commit()
    except IntegrityError:
        session.rollback()  # a concurrent writer already inserted these keys — our duplicates are dropped


def _streamed_existing_keys(session: Session, batch: int) -> set:
    """The forward-return idempotency key set `{(run_id, symbol, horizon)}`, built by STREAMING a
    COLUMN-PROJECTED scan (`select(ForwardReturn.run_id, .symbol, .horizon)` consumed with `yield_per`)
    instead of materializing every stored `ForwardReturn` ORM row at once (iter-47, J-105). The projected
    Row values are the EXACT same plain `(int, str, int)` tuples as ORM attribute access, so the resulting
    set is identical to the prior full-table set — idempotency + the INSERT-only/append-only contract are
    preserved, the read is bounded on the grown table."""
    existing: set = set()
    stmt = select(ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.horizon)
    for run_id, symbol, horizon in session.exec(stmt).yield_per(batch):
        existing.add((run_id, symbol, horizon))
    return existing


def _backfill(session: Session, cfg: Config) -> dict:
    latest = latest_data_date(session)
    if latest is None:
        return {"asof_dates": [], "runs_with_returns": 0, "rows_inserted": 0}

    wf = cfg.walk_forward
    horizons = wf.horizons
    max_h = max(horizons)

    # (1)+(2): ensure a persisted immutable snapshot for every cadence as-of date. run_scan is
    # idempotent and recomputes nothing — the snapshot is the canonical bucket/setup/sector source.
    asof_dates = walk_forward_asof_dates(session, cfg)
    for asof in asof_dates:
        run_scan(session, asof, cfg)

    # Idempotency: only INSERT (run, symbol, horizon) keys that do not already exist. iter-47 (J-105):
    # built by STREAMING a column-projected scan (bounded by config) — not a full-table ORM `.all()`.
    batch = cfg.research.read_batch_size
    existing = _streamed_existing_keys(session, batch)

    # (3): for EVERY persisted run with >= 1 post-snapshot bar (including the bootstrap Risk-off runs,
    # so the by-regime sample carries both regimes), INSERT the realized per-(run, symbol, horizon)
    # forward returns. Runs with no post-snapshot bars (the latest seed-date run) insert nothing (n=0).
    # NOTE: `runs` is materialized (not streamed): there is one ScannerRun per cadence date (bounded,
    # small) and the loop body mutates the session (add + flush + bar queries) — streaming a server-side
    # cursor while mutating the same session would interleave unsafely. The memory lever is the millions-
    # row `forward_returns` idempotency scan above (now streamed), not the bounded run list.
    runs = session.exec(select(ScannerRun)).all()
    rows_inserted = 0
    runs_with_returns = 0
    for run in runs:
        # J-93: each run stores forward returns for ITS OWN resolved membership ∪ benchmarks (the run's
        # stored ScannerResult tickers — the single source) rather than the global universe list.
        symbols = forward_symbols_for_run(session, run, cfg)
        run_inserted = _insert_run_forward_returns(session, run, symbols, horizons, max_h, existing)
        rows_inserted += run_inserted
        if run_inserted:
            runs_with_returns += 1

    _commit_forward_returns_concurrency_safe(session)  # iter-28 (J-41): tolerate a concurrent INSERT race
    return {
        "asof_dates": [d.isoformat() for d in asof_dates],
        "runs_with_returns": runs_with_returns,
        "rows_inserted": rows_inserted,
    }


def backfill_forward_returns(
    session_or_engine: Union[Session, Engine], config: Optional[Config] = None
) -> dict:
    """Idempotently persist the walk-forward cadence snapshots and INSERT their realized forward
    returns into the append-only `forward_returns` table. Frozen-seed-only (reads the committed seed
    via `bars_asof`/`bars_after`/`close_on` — never the network), mirroring `scanner.bootstrap_runs`.
    Accepts a `Session` (tests) or an `Engine` (the app lifespan). A second call inserts zero new rows."""
    cfg = config or get_config()
    if isinstance(session_or_engine, Session):
        return _backfill(session_or_engine, cfg)
    with Session(session_or_engine) as session:
        return _backfill(session, cfg)


# --------------------------------------------------------------------------------------------------
# Aggregation — the SINGLE canonical forward-return analysis (reads stored buckets/setups verbatim)
# --------------------------------------------------------------------------------------------------
def _mean_or_none(values: list[float]) -> Optional[float]:
    return mean(values) if values else None


def _group_mdd(observations: list[dict], group_attr: str) -> dict[str, list[float]]:
    """`group value -> [stored max_drawdown over the group's observations that HAVE one]` (iter-27, J-86).
    A group's mean-MDD is the mean over only the observations whose stored `max_drawdown` is non-None
    (absent ones excluded — never counted as a fabricated 0); the SAME observation set the mean return
    groups, intersected with "has a stored drawdown" (which is the same set whenever the return exists,
    since both share the NA gate)."""
    by_group: dict[str, list[float]] = defaultdict(list)
    for obs in observations:
        value = obs.get(group_attr)
        if value is not None and obs.get("max_drawdown") is not None:
            by_group[value].append(obs["max_drawdown"])
    return by_group


def _group_means(observations: list[dict], group_attr: str, label_key: str, order, pad: bool) -> list[dict]:
    """Mean realized return + n per stored group value (`group_attr`), ordered by `order` first then any
    extras. With `pad`, every value in `order` is emitted even at n=0 (mean None) so the table is
    complete (used for the A-E bucket rows); otherwise only non-empty groups appear.

    iter-27 (J-86): each row ADDITIVELY carries `mean_max_drawdown` — the mean of the group's stored
    max-drawdowns (read-only, over only observations with a stored drawdown; None when the group has none),
    beside the existing `mean_return`. A purely additive key — every existing reader (which keys off
    `mean_return` / `n` / the label) is unaffected."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for obs in observations:
        value = obs.get(group_attr)
        if value is not None:
            buckets[value].append(obs["return"])
    mdd_buckets = _group_mdd(observations, group_attr)

    def _row(value, returns: list[float]) -> dict:
        return {
            label_key: value,
            "mean_return": mean(returns) if returns else None,
            "mean_max_drawdown": _mean_or_none(mdd_buckets.get(value, [])),
            "n": len(returns),
        }

    rows: list[dict] = []
    emitted: set = set()
    for value in order:
        if value in buckets:
            rows.append(_row(value, buckets[value]))
            emitted.add(value)
        elif pad:
            rows.append(_row(value, []))
            emitted.add(value)
    for value in sorted(buckets):
        if value not in emitted:
            rows.append(_row(value, buckets[value]))
    return rows


def _control_groups(
    horizon: int,
    stock_obs: list[dict],
    ret_by_run_symbol: dict,
    runs_with_fr: list[int],
    cfg: Config,
) -> list[dict]:
    """The control-group cohorts at `horizon` (J-10): the top-ranked cohort vs a random same-sector
    cohort vs SPY / QQQ / sector-ETF — each numeric, labelled, with n. The random same-sector cohort is
    drawn with a deterministic RNG re-seeded from `control_group.seed` (reproducible across calls and
    restarts), sampling `peers_per_sector` stocks per sector that the top-ranked cohort occupies."""
    cg = cfg.walk_forward.control_group
    bm = benchmark_symbols(cfg)
    etf_by_sector = _sector_etf_by_name(cfg)
    rng = random.Random(cg.seed)  # re-seeded every computation -> reproducible cohort

    obs_by_run: dict[int, list[dict]] = defaultdict(list)
    for obs in stock_obs:
        obs_by_run[obs["run_id"]].append(obs)

    top_returns: list[float] = []
    random_returns: list[float] = []
    sector_etf_returns: list[float] = []
    # deterministic iteration order (sorted runs, sorted sectors, sorted pools) so RNG draws reproduce
    for run_id in sorted(obs_by_run):
        run_obs = obs_by_run[run_id]
        top_sectors = sorted(
            {o["sector"] for o in run_obs if o["rank"] is not None and o["rank"] <= cg.top_n and o["sector"]}
        )
        by_sector: dict[str, list[dict]] = defaultdict(list)
        for o in run_obs:
            if o["sector"]:
                by_sector[o["sector"]].append(o)
        for o in run_obs:
            if o["rank"] is not None and o["rank"] <= cg.top_n:
                top_returns.append(o["return"])
        for sector in top_sectors:
            pool = sorted(by_sector.get(sector, []), key=lambda o: o["ticker"])
            if pool:
                sample = rng.sample(pool, min(cg.peers_per_sector, len(pool)))
                random_returns.extend(o["return"] for o in sample)
            etf_ret = ret_by_run_symbol.get((run_id, etf_by_sector.get(sector)))
            if etf_ret is not None:
                sector_etf_returns.append(etf_ret)

    spy_returns = [ret_by_run_symbol[(r, bm["spy"])] for r in runs_with_fr if (r, bm["spy"]) in ret_by_run_symbol]
    qqq_returns = [ret_by_run_symbol[(r, bm["qqq"])] for r in runs_with_fr if (r, bm["qqq"]) in ret_by_run_symbol]

    return [
        {"key": "top_ranked", "label": f"Top-ranked cohort (rank ≤ {cg.top_n})",
         "mean_return": _mean_or_none(top_returns), "n": len(top_returns)},
        {"key": "random_same_sector", "label": "Random same-sector peers",
         "mean_return": _mean_or_none(random_returns), "n": len(random_returns)},
        {"key": "spy", "label": bm["spy"], "mean_return": _mean_or_none(spy_returns), "n": len(spy_returns)},
        {"key": "qqq", "label": bm["qqq"], "mean_return": _mean_or_none(qqq_returns), "n": len(qqq_returns)},
        {"key": "sector_etf", "label": "Sector ETF (same sectors)",
         "mean_return": _mean_or_none(sector_etf_returns), "n": len(sector_etf_returns)},
    ]


# --------------------------------------------------------------------------------------------------
# Return attribution (J-19) — four READ-ONLY slices of the ALREADY-BUILT per-observation stock_obs
# --------------------------------------------------------------------------------------------------
def _rank_band_label(rank: Optional[int], rank_bands) -> Optional[str]:
    """The config rank-band label a STORED rank falls in (`min <= rank <= max`, `max=None` = open top
    band), or None when `rank is None` or it matches no band — those observations are EXCLUDED from the
    by-rank-band slice (never bucketed into a band)."""
    if rank is None:
        return None
    for band in rank_bands:
        if rank >= band.min and (band.max is None or rank <= band.max):
            return band.label
    return None


def _per_stock_attribution(stock_obs: list[dict], top_k: int) -> dict:
    """Per-stock contributors / detractors: each ticker's mean realized return + n + STORED sector over
    the SAME observations (no recomputed return), the highest `top_k` means as contributors and the
    lowest `top_k` as detractors (deterministic ticker tie-break). Empty observations -> empty lists."""
    returns_by_ticker: dict[str, list[float]] = defaultdict(list)
    sector_by_ticker: dict[str, Optional[str]] = {}
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


def _distribution(returns: list[float]) -> dict:
    """The distribution & hit-rate of the SAME observed returns: mean, median, `pct_positive` (the share
    with return > 0), `dispersion` (sample stdev; None when n < 2 — no spurious zero), and n. Empty ->
    all-None with n 0 (honest NA — never a fabricated 0%)."""
    n = len(returns)
    if n == 0:
        return {"mean_return": None, "median": None, "pct_positive": None, "dispersion": None, "n": 0}
    positive = sum(1 for r in returns if r > 0)
    return {
        "mean_return": mean(returns),
        "median": median(returns),
        "pct_positive": positive / n,
        "dispersion": stdev(returns) if n >= 2 else None,
        "n": n,
    }


def _attribution_slices(stock_obs: list[dict], cfg: Config) -> dict:
    """The four READ-ONLY return-attribution slices (J-19), derived ENTIRELY from the ALREADY-BUILT
    per-observation `stock_obs` (stored realized returns joined to stored `scanner_results`, read
    verbatim) + config. It recomputes NO return and takes NO Session, so it can issue no second
    forward_returns / price-bar query — this IS the anti-goal "Attribution is read-only": the slices
    are pure groupings of the SAME observations the aggregate / scorecard already measured (no second
    formula, no second data source; consistency with the aggregate mean is unit-asserted).

      - per_stock     contributors (highest mean) / detractors (lowest mean), each `top_contributors_k`
      - by_sector     mean realized return + n per STORED sector (config sector-name order; non-padded)
      - by_rank_band  mean realized return + n per config rank band (every band padded to n=0)
      - distribution  mean / median / % positive (hit rate) / dispersion (stdev) of the same returns
    """
    attribution = cfg.walk_forward.attribution
    sector_order = list(cfg.etfs.sector.values())  # config sector NAMES (never a literal sector list)
    band_order = [band.label for band in attribution.rank_bands]
    banded_obs = [
        {**obs, "rank_band": _rank_band_label(obs.get("rank"), attribution.rank_bands)}
        for obs in stock_obs
    ]
    return {
        "per_stock": _per_stock_attribution(stock_obs, attribution.top_contributors_k),
        "by_sector": _group_means(stock_obs, "sector", "sector", sector_order, pad=False),
        "by_rank_band": _group_means(banded_obs, "rank_band", "rank_band", band_order, pad=True),
        "distribution": _distribution([obs["return"] for obs in stock_obs]),
    }


def _leadership_returns(
    ret_by_symbol: dict[str, float],
    cfg: Config,
    mdd_by_symbol: Optional[dict[str, Optional[float]]] = None,
) -> dict:
    """The READ-ONLY leadership-return projection (J-21): the realized forward return of each Top Sector
    / Top Theme / Ranked-Cohort row at ONE horizon, derived ENTIRELY from the already-built
    `ret_by_symbol` (symbol -> the stored `realized_return` for this run+horizon) + config. It issues NO
    query, takes NO Session, and recomputes NO return — this IS the "Attribution is read-only" discipline,
    mirroring `_attribution_slices`: it is a pure projection of the SAME stored `forward_returns` rows the
    scorecard already read, never a second computation or a second data source (J-21).

    Three COMPLETE keyed lists (the frontend joins these onto rows it already fetches and slices what it
    shows — so no row-count literal lives here):
      - `sectors`: one row per config sector ETF -> its OWN stored return (the ETF's realized return,
        sector ETF -> name via `cfg.etfs.sector`); `n` 1 if present else 0.
      - `themes`:  one row per config theme slug -> the EQUAL-WEIGHT mean of its member stocks' stored
        returns over ONLY the members that HAVE a stored return (absent members are skipped, never
        counted as 0); `n` = that member count.
      - `cohort`:  one row per universe ticker (the stored `scanner_results` set) -> its OWN stored
        return; `n` 1 if present else 0.
    A (row, horizon) with no stored return -> `mean_return` None / `n` 0 (honest NA — never a fabricated
    0%, anti-goal: No fabricated data).

    iter-27 (J-86): when `mdd_by_symbol` (symbol -> the stored `max_drawdown` for this run+horizon, read
    VERBATIM) is supplied, EACH row ADDITIVELY carries `max_drawdown` paired to its `mean_return`, derived
    by the SAME projection rule (sector = the ETF's OWN stored drawdown; theme = the equal-weight mean of
    its members' stored drawdowns over ONLY members that have one; cohort = its OWN stored drawdown). It
    recomputes NO drawdown — a pure projection of the SAME stored values. A row with no stored drawdown ->
    `max_drawdown` None (honest NA). `mdd_by_symbol=None` keeps the pre-J-86 shape (no `max_drawdown` key),
    so the Backtest scorecard path is byte-identical until it opts in."""
    mdd = mdd_by_symbol  # alias; None means "do not project max_drawdown" (pre-J-86 callers)
    sectors = []
    for etf, name in cfg.etfs.sector.items():
        row = {
            "sector_etf": etf,
            "sector": name,
            "mean_return": ret_by_symbol.get(etf),
            "n": 1 if etf in ret_by_symbol else 0,
        }
        if mdd is not None:
            row["max_drawdown"] = mdd.get(etf)  # the ETF's OWN stored drawdown (verbatim); NA when absent
        sectors.append(row)
    themes = []
    for slug, members in cfg.themes.items():
        member_returns = [ret_by_symbol[m] for m in members if m in ret_by_symbol]
        row = {
            "slug": slug,
            "mean_return": _mean_or_none(member_returns),  # equal-weight; None when no member has a return
            "n": len(member_returns),
        }
        if mdd is not None:
            # equal-weight member-basket drawdown over ONLY members with a stored drawdown (absent members
            # skipped, never counted as 0); None when no member has one — the SAME rule as the basket return.
            member_mdds = [mdd[m] for m in members if mdd.get(m) is not None]
            row["max_drawdown"] = _mean_or_none(member_mdds)
        themes.append(row)
    cohort = []
    for ticker in cfg.universe.symbols:
        row = {
            "ticker": ticker,
            "mean_return": ret_by_symbol.get(ticker),
            "n": 1 if ticker in ret_by_symbol else 0,
        }
        if mdd is not None:
            row["max_drawdown"] = mdd.get(ticker)  # the cohort symbol's OWN stored drawdown (verbatim)
        cohort.append(row)
    return {"sectors": sectors, "themes": themes, "cohort": cohort}


def compute_forward_aggregates(
    session: Session,
    horizon: int,
    config: Optional[Config] = None,
    *,
    as_of: Optional[date_cls] = None,
) -> dict:
    """The SINGLE canonical forward-return aggregation at `horizon` (Data Contract value, served on
    `GET /api/backtest`). Joins the stored realized returns (`forward_returns`) to the stored canonical
    bucket / setup / sector / rank (`scanner_results`) and regime label (`scanner_runs`), all READ
    VERBATIM — no score/bucket/setup is ever recomputed. Returns, each cell carrying `n`: forward return
    by bucket (A-E), by setup, by regime; excess vs SPY and QQQ; and the control-group cohorts. Carries
    the `min_sample` threshold and the survivorship-bias label. A run with no post-snapshot bars
    contributes nothing (n=0).

    `as_of` (iter-17, J-09/J-10) optionally scopes the pool to an EXPANDING WALK-FORWARD WINDOW: when
    set, ONLY snapshots with `ScannerRun.asof_date <= as_of` contribute, so a run dated > D leaks nothing
    into the as-of-D evidence (the No-lookahead / No-recompute / Single-source criticals). It is a SINGLE
    membership filter on the `fr_rows` step, so it equally bounds `runs_with_fr`, `results`, `run_rows`,
    and the SPY/QQQ benchmark lists (all derived from it) — the grouping / excess / control-group /
    attribution math is untouched. `as_of=None` keeps the all-history behaviour BYTE-IDENTICAL (== the
    latest-date case, since no run is dated after the latest). The cutoff is the resolved global as-of
    date transmitted on the snapshot-served read — never a second date state (J-18)."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    bm = benchmark_symbols(cfg)

    # The SINGLE as-of membership filter (iter-17): restrict the pool to runs dated <= D by joining each
    # forward return to its run's canonical `asof_date`. `as_of=None` adds NO clause -> the query (and
    # thus every derived set) is byte-identical to the all-history path. The cutoff is read from
    # `ScannerRun.asof_date` (the canonical snapshot date) — not the denormalized `ForwardReturn.asof_date`
    # — so it is exactly the "snapshots dated <= D" membership the expanding walk-forward window requires.
    fr_stmt = select(ForwardReturn).where(ForwardReturn.horizon == horizon)
    if as_of is not None:
        fr_stmt = fr_stmt.join(ScannerRun, ScannerRun.id == ForwardReturn.run_id).where(
            ScannerRun.asof_date <= as_of
        )
    fr_rows = session.exec(fr_stmt).all()
    ret_by_run_symbol = {(fr.run_id, fr.symbol): fr.realized_return for fr in fr_rows}
    # iter-27 (J-86): the stored max_drawdown for each (run, symbol) at this horizon, read VERBATIM — so
    # the aggregate mean-MDD is a read-only grouping of the SAME stored values (no recomputed drawdown).
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

    # Per-stock observations: each stored result joined to its stored realized return at this horizon.
    # The bucket / setup / sector / rank / regime are READ from the snapshot — never recomputed here.
    stock_obs: list[dict] = []
    for res in results:
        realized = ret_by_run_symbol.get((res.run_id, res.ticker))
        if realized is None:
            continue  # this stock has no realized return at this horizon in this run (n=0 contribution)
        stock_obs.append({
            "run_id": res.run_id,
            "ticker": res.ticker,
            "return": realized,
            # iter-27 (J-86): the stored max_drawdown for this observation (read verbatim) — paired to the
            # return so the aggregate mean-MDD groups exactly the same observation set as the mean return.
            "max_drawdown": mdd_by_run_symbol.get((res.run_id, res.ticker)),
            "bucket": res.leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
            "setup": res.setup_status,         # stored canonical setup status (verbatim)
            "sector": res.sector,
            "rank": res.rank,
            "regime": regime_by_run.get(res.run_id),  # stored regime label for the run
            "is_vcp": res.is_vcp,              # stored VCP flag (verbatim — never re-detected here)
            # stored new-pattern flags (verbatim — never re-detected here), iter-9
            "is_pullback_to_rising_dma": res.is_pullback_to_rising_dma,
            "is_flat_base_breakout": res.is_flat_base_breakout,
        })

    stock_returns = [o["return"] for o in stock_obs]
    overall_mean = _mean_or_none(stock_returns)
    # iter-27 (J-86): the overall mean max-drawdown over only observations with a stored drawdown (the same
    # NA discipline the return aggregate uses) — read-only over the SAME stored values, recomputes nothing.
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

    # by_vcp (iter-11, J-16): mean forward return for the VCP-flagged vs non-VCP cohorts, grouping the
    # STORED `is_vcp` flag verbatim (never re-detected here) exactly like by_setup/by_bucket. Both
    # cohorts always emitted (padded to n=0 / mean None when empty); each carries `n` so the UI flags
    # n < min_sample and shows NA honestly. No new endpoint, no second formula — one grouping path.
    by_vcp = [
        {"vcp": VCP_LABELS[row["vcp"]], "mean_return": row["mean_return"],
         "mean_max_drawdown": row["mean_max_drawdown"], "n": row["n"]}
        for row in _group_means(stock_obs, "is_vcp", "vcp", [True, False], pad=True)
    ]
    # by_<name> (iter-9, J-28): the SAME stored-mirror grouping as by_vcp for the two new detected
    # patterns — read the persisted `is_<name>` flag verbatim (never re-detected), both cohorts always
    # emitted (padded n=0 / mean None when empty), each carrying `n` so the UI shows honest NA below
    # min_sample. No new endpoint, no second formula — one grouping path.
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
        "horizons": list(wf.horizons),
        "default_horizon": wf.default_horizon,
        "min_sample": wf.min_sample,
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
        # J-19: the four read-only attribution slices for this horizon, derived from the SAME stock_obs
        # (no recomputed return). distribution.mean_return == overall.mean_return (asserted in tests).
        "attribution": _attribution_slices(stock_obs, cfg),
    }


# --------------------------------------------------------------------------------------------------
# Per-date scorecard (J-14) — create-once population + the SINGLE per-date forward-test read
# --------------------------------------------------------------------------------------------------
def backfill_run_forward_returns(
    session: Session, run: ScannerRun, config: Optional[Config] = None
) -> dict:
    """Create-once population of ONE run's realized forward returns into the append-only
    `forward_returns` table, via the shared `_insert_run_forward_returns` helper (the single
    forward-return formula). INSERT-only + idempotent — a 2nd call inserts 0 rows and it never UPDATEs
    a `scanner_runs` / `scanner_results` / `*_scores` row (anti-goal: Snapshots immutable). Frozen-seed-
    only. This is the "first view computes once" path the No-recompute-in-the-read-path anti-goal
    explicitly permits; for a run the iter-6 boot backfill already covered it inserts nothing."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    horizons = wf.horizons
    max_h = max(horizons)
    # J-93: this run's OWN resolved membership ∪ benchmarks (its stored ScannerResult tickers — single
    # source), not the global universe list. A name absent from the run's snapshot stores no return (n=0).
    symbols = forward_symbols_for_run(session, run, cfg)
    existing = {
        (fr.run_id, fr.symbol, fr.horizon)
        for fr in session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()
    }
    inserted = _insert_run_forward_returns(session, run, symbols, horizons, max_h, existing)
    _commit_forward_returns_concurrency_safe(session)  # iter-28 (J-41): tolerate a concurrent INSERT race
    return {"run_id": run.id, "asof_date": run.asof_date.isoformat(), "rows_inserted": inserted}


def _scorecard_excess(cohort_mean: Optional[float], cohort_n: int, bench: dict) -> dict:
    """Cohort excess vs one benchmark cohort = cohort mean − benchmark mean (NA when either side is
    NA — never a fabricated 0%). Mirrors `compute_forward_aggregates`'s excess subtraction; the
    benchmark label / mean / n are READ from the shared control-group cohort, so there is no second
    source for the benchmark figure."""
    bench_mean = bench["mean_return"]
    return {
        "benchmark": bench["label"],
        "mean_excess": (cohort_mean - bench_mean)
        if (cohort_mean is not None and bench_mean is not None) else None,
        "cohort_mean": cohort_mean,
        "benchmark_mean": bench_mean,
        "n": cohort_n,
        "benchmark_n": bench["n"],
    }


def compute_run_scorecard(session: Session, run: ScannerRun, config: Optional[Config] = None) -> dict:
    """The SINGLE canonical per-date forward-test scorecard (Data Contract value, J-14). READS the
    stored `forward_returns` for THIS `run.id` joined to the stored `scanner_results` (leadership
    bucket / setup / sector / rank, read VERBATIM) — it RECOMPUTES no score, bucket, or return. For
    EACH configured horizon it returns: the as-of cohort mean realized return + `n` (cohort = stocks
    ranked <= `control_group.top_n`, i.e. the control-group "top_ranked" definition); the excess
    (cohort mean − benchmark mean) vs SPY / QQQ / sector, each with `n`; and the five control-group
    cohorts, each with `mean_return` + `n`. A horizon (or cohort) with no stored realized return for
    the run -> `mean_return: None` / `n: 0` (honest NA — never a fabricated 0%). Reuses the iter-6
    `_control_groups` so the cohort + control-group math has exactly ONE implementation. Each horizon
    entry also rides the J-19 read-only `attribution` slices and the J-21 read-only `leadership_returns`
    projection (Top Sector / Top Theme / Ranked-Cohort realized returns), both pure projections of the
    SAME stored `forward_returns` — no recomputed return, no second query."""
    cfg = config or get_config()
    wf = cfg.walk_forward

    results = session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
    fr_rows = session.exec(select(ForwardReturn).where(ForwardReturn.run_id == run.id)).all()

    by_horizon: list[dict] = []
    for horizon in wf.horizons:
        fr_at_h = [fr for fr in fr_rows if fr.horizon == horizon]
        ret_by_symbol = {fr.symbol: fr.realized_return for fr in fr_at_h}
        # iter-27 (J-86): the SAME stored rows' max_drawdown (read verbatim) so the Top Sector / Top Theme
        # / cohort leadership-return projection carries a paired MDD identical to the leaderboard (J-06).
        mdd_by_symbol = {fr.symbol: fr.max_drawdown for fr in fr_at_h}
        ret_by_run_symbol = {(run.id, sym): ret for sym, ret in ret_by_symbol.items()}
        runs_with_fr = sorted({fr.run_id for fr in fr_at_h})  # [] or [run.id]

        # Per-stock observations at this horizon: each stored result joined to its stored realized
        # return — the bucket / setup / sector / rank are READ from the snapshot, never recomputed.
        stock_obs: list[dict] = []
        for res in results:
            realized = ret_by_symbol.get(res.ticker)
            if realized is None:
                continue  # no realized return at this horizon for this stock (n=0 contribution)
            stock_obs.append({
                "run_id": run.id,
                "ticker": res.ticker,
                "return": realized,
                "bucket": res.leadership_bucket,   # stored canonical A-E (verbatim — no re-bucketing)
                "setup": res.setup_status,         # stored canonical setup status (verbatim)
                "sector": res.sector,
                "rank": res.rank,                  # stored canonical rank (verbatim — cohort membership)
            })

        cohorts = _control_groups(horizon, stock_obs, ret_by_run_symbol, runs_with_fr, cfg)
        by_key = {c["key"]: c for c in cohorts}
        cohort = by_key["top_ranked"]
        cohort_mean, cohort_n = cohort["mean_return"], cohort["n"]

        by_horizon.append({
            "horizon": horizon,
            "cohort": {"mean_return": cohort_mean, "n": cohort_n},
            "excess": {
                "vs_spy": _scorecard_excess(cohort_mean, cohort_n, by_key["spy"]),
                "vs_qqq": _scorecard_excess(cohort_mean, cohort_n, by_key["qqq"]),
                "vs_sector": _scorecard_excess(cohort_mean, cohort_n, by_key["sector_etf"]),
            },
            "control_group": cohorts,
            # J-19: the four read-only attribution slices over THIS horizon's observed set (the full
            # stock_obs, not just the rank<=top_n cohort) — derived from the same stored observations.
            "attribution": _attribution_slices(stock_obs, cfg),
            # J-21: the read-only leadership-return projection (sector ETF / theme members / cohort
            # symbol) over the SAME stored `ret_by_symbol` — no recomputed return, no second query.
            # iter-27 (J-86): paired with the stored max_drawdown projection (the SAME builder the
            # leaderboard reads), so a sector/theme MDD reads identically on Backtest and its leaderboard.
            "leadership_returns": _leadership_returns(ret_by_symbol, cfg, mdd_by_symbol),
        })

    return {
        "asof_date": run.asof_date.isoformat(),
        "min_sample": wf.min_sample,
        "horizons": list(wf.horizons),
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "scorecard": {"by_horizon": by_horizon},
    }


# --------------------------------------------------------------------------------------------------
# Drawdown & dry-spell expectations (iter-41, J-25) — phase-conditional historical distributions over
# ONE certified claim's cohort, additively served on GET /api/evidence. Pure read-compose: resolves the
# cohort via the SAME `app.engine.samples.compute_samples` selectors the Research labs publish (no
# second cohort resolver), reads each observation's STORED `max_drawdown` / `underwater_days` /
# `time_to_recover_days` VERBATIM off `ForwardReturn` (recomputes no existing canonical value), and joins
# to the CAUSAL phase-at-entry via `app.engine.market_phase.phase_context_by_date` (the SAME causal
# timeline `compute_market_phase` reads — never a smoothed/retrospective one).
#
# `app.engine.samples` imports `SURVIVORSHIP_BIAS_LABEL` FROM this module, and `app.engine.market_phase`
# imports `app.engine.research` which ALSO imports FROM this module — so a MODULE-LEVEL import of either
# back into this file would be circular. Both are LAZY-imported inside `compute_drawdown_expectations`,
# mirroring `app.engine.research`'s own established "lazy import (avoids a market_phase<->research
# cycle)" pattern for the identical reason.
# --------------------------------------------------------------------------------------------------

# The ledger claim's own selector-field name -> the `compute_samples` kwarg name (identity when
# unlisted). Mirrors `app.mcp.tools._CLAIM_SELECTOR_KEYS` / `drill_samples`'s translation — the SAME
# vocabulary `/api/research/samples` accepts and `app.mcp.tools.assemble_claim_observations` (the
# referee's own cohort assembly) already applies. A pure key rename/repackage: the cohort MEMBERSHIP
# RULE stays 100% inside `compute_samples` — this decides nothing about who is IN a cohort, only which
# keyword each already-stored selector value arrives under. Kept as a small local mirror (rather than an
# import from `app.mcp.tools`) because `app.mcp.tools` sits ABOVE this module in the dependency graph
# (it imports FROM `app.engine.samples`/`research`, which import FROM this module) — importing it here
# would invert that layering.
_CLAIM_SELECTOR_KEYS = (
    "factor", "slice_kind", "decile", "regime", "sector", "condition", "cohort", "single_index",
    "subject", "view", "setup", "pattern", "phase", "dimension", "family", "velocity_sign",
    "regime_decile", "severity_decile", "factor_decile",
)
_CLAIM_KWARG_RENAMES = {"factor": "factor_key", "cohort": "cohort_kind", "subject": "subject_key"}

# The walk-forward-cadence method note (B-205 trap): a loss streak counted per-observation (per ticker
# per date) would double-count multiple names sharing one snapshot date, or overlapping-horizon returns,
# as if they were independent consecutive "days". Collapsing to one mean-return-per-date point first
# avoids both.
LOSS_STREAK_METHOD_NOTE = (
    "Longest losing streak is counted at the walk-forward cadence (one point per snapshot date — the "
    "cohort's mean forward return that date), not per name per day, so multiple names sharing a "
    "snapshot date are never double-counted as separate consecutive losses."
)


def _claim_samples_kwargs(claim: dict) -> Optional[dict]:
    """Translate a ledger claim's cohort selectors into `compute_samples` kwargs (module note above).
    Returns None for a malformed `condition` leg (never raises — an honest unresolvable cohort)."""
    kwargs: dict = {}
    for key in _CLAIM_SELECTOR_KEYS:
        if key not in claim:
            continue
        if key == "condition":
            parsed = []
            for spec in claim["condition"]:
                parts = spec.split(":")
                if len(parts) != 3:
                    return None
                parsed.append({"factor": parts[0], "side": parts[1], "quantile": parts[2]})
            kwargs["conditions"] = parsed
            continue
        kwargs[_CLAIM_KWARG_RENAMES.get(key, key)] = claim[key]
    return kwargs


def _median_p90(values: list[float]) -> dict:
    """{median, p90} of `values` via linear-interpolation percentiles — the SAME 'standard definition'
    `app.engine.indicators._percentile` uses for the risk-budget gap profile (J-24), mirrored locally
    (a two-line formula) rather than imported cross-domain."""
    ordered = sorted(values)
    n = len(ordered)

    def _pct(p: float) -> float:
        if n == 1:
            return ordered[0]
        rank = p * (n - 1)
        lower = int(rank)
        upper = min(lower + 1, n - 1)
        frac = rank - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * frac

    return {"median": _pct(0.5), "p90": _pct(0.9)}


def _distribution_cell(values: list[float], floor: int) -> dict:
    """One `{median, p90, n, insufficient}` cell — an honest 'insufficient' (no median/p90, never a
    fabricated distribution) below `floor`."""
    n = len(values)
    if n < floor:
        return {"median": None, "p90": None, "n": n, "insufficient": True}
    stats = _median_p90(values)
    return {"median": stats["median"], "p90": stats["p90"], "n": n, "insufficient": False}


def _longest_negative_streak(ordered_dated_returns: list[tuple]) -> int:
    """The longest run of consecutive entries in `ordered_dated_returns` (ALREADY sorted ascending by
    date) whose return is < 0. Pure sequence scan; 0 when no entry is negative or the list is empty."""
    best = 0
    current = 0
    for _date, ret in ordered_dated_returns:
        if ret < 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _loss_streak_cell(dated_returns: list[tuple], floor: int) -> dict:
    """One `{value, n, insufficient}` loss-streak cell at the WALK-FORWARD CADENCE (the B-205 trap):
    `dated_returns` (`[(snapshot_date_iso, forward_return), ...]`, any order) is first collapsed to ONE
    MEAN cohort return per distinct date (so multiple tickers sharing a snapshot date contribute a SINGLE
    data point, never inflating the streak), sorted chronologically, then the longest run of consecutive
    NEGATIVE dates is counted (`_longest_negative_streak`). `n` is the number of distinct cadence dates
    examined — the honesty floor for THIS measure is `streak_min_n`, deliberately smaller than the
    per-observation `min_sample` floor the other three measures use."""
    by_date: dict[str, list[float]] = defaultdict(list)
    for d, ret in dated_returns:
        by_date[d].append(ret)
    ordered = sorted((d, mean(rets)) for d, rets in by_date.items())
    n = len(ordered)
    if n < floor:
        return {"value": None, "n": n, "insufficient": True}
    return {"value": _longest_negative_streak(ordered), "n": n, "insufficient": False}


def compute_drawdown_expectations(
    session: Session, claim: dict, config: Optional[Config] = None
) -> Optional[dict]:
    """iter-41 (J-25) — the SINGLE canonical phase-conditional drawdown & dry-spell expectations payload
    for ONE certified-claims ledger `claim` (Data Contract value, additive on `GET /api/evidence`). For
    the claim's own cohort (resolved via the SAME `compute_samples` selectors the Research labs publish)
    at the claim's own `horizon`, groups the STORED `max_drawdown` / `underwater_days` /
    `time_to_recover_days` (read VERBATIM — recomputes nothing) by the CAUSAL phase-at-entry
    (`phase_context_by_date`, keyed by the observation's own snapshot date), and emits per configured
    phase label a `{median, p90, n}` cell for each of the three distribution measures plus a
    walk-forward-cadence longest-losing-streak cell. EVERY configured `market_phase.labels` value is
    emitted (padded, even at n=0) so a cohort that never saw a phase still discloses that honestly.

    Returns None — the caller (`build_evidence_payload`) then omits the `expectations` key entirely, the
    honest 'no panel' signal — when: the claim's `horizon` is missing or outside the configured
    `walk_forward.underwater_horizons` scope, the cohort selectors are malformed/unresolvable (an unknown
    kind, an out-of-range decile, a malformed combination `condition`, …), or the cohort resolves to zero
    observations with BOTH a snapshot date and a realized forward return. Never raises into the caller —
    `GET /api/evidence` always stays 200."""
    cfg = config or get_config()
    wf = cfg.walk_forward
    horizon = claim.get("horizon")
    if horizon not in wf.underwater_horizons:
        return None
    kwargs = _claim_samples_kwargs(claim)
    if kwargs is None:
        return None

    # lazy imports — both `samples` and `market_phase` import FROM this module at load time (see the
    # module note above), so a module-level import of either back into this file would be circular.
    from app.engine.market_phase import phase_context_by_date
    from app.engine.samples import compute_samples

    try:
        samples = compute_samples(
            session, kind=claim.get("kind"), horizon=horizon, config=cfg, as_of=None, **kwargs
        )
    except ValueError:
        return None  # an unknown kind / unresolvable / malformed cohort selector -> honest empty

    rows = [r for r in samples["rows"] if r.get("snapshot_date") and r.get("forward_return") is not None]
    if not rows:
        return None

    # ONE additive read of the SAME (ticker, horizon, snapshot-date) rows `compute_samples` already
    # resolved — the cohort MEMBERSHIP is unchanged; this only fetches the three stored columns
    # `compute_samples`'s own row shape does not carry. `ForwardReturn.asof_date` is stored verbatim on
    # each row (no ScannerRun join needed) and is the SAME date `_run_date_map` derives `snapshot_date`
    # from, so the (symbol, asof_date-ISO) key matches every `compute_samples` row exactly.
    tickers = sorted({r["ticker"] for r in rows})
    fr_stmt = select(
        ForwardReturn.symbol, ForwardReturn.asof_date, ForwardReturn.max_drawdown,
        ForwardReturn.underwater_days, ForwardReturn.time_to_recover_days,
    ).where(ForwardReturn.horizon == horizon, ForwardReturn.symbol.in_(tickers))
    stored_by_key = {
        (symbol, asof_date.isoformat()): (mdd, uw, ttr)
        for symbol, asof_date, mdd, uw, ttr in session.exec(fr_stmt).all()
    }

    # the SAME causal timeline `compute_market_phase` reads (all-history — the expectations panel is
    # descriptive over the claim's WHOLE tested cohort, not scoped to a single "today" as-of).
    phases = phase_context_by_date(session, as_of=None, config=cfg)

    by_phase_mdd: dict[str, list[float]] = defaultdict(list)
    by_phase_uw: dict[str, list[float]] = defaultdict(list)
    by_phase_ttr: dict[str, list[float]] = defaultdict(list)
    by_phase_returns: dict[str, list[tuple]] = defaultdict(list)

    for row in rows:
        date_iso = row["snapshot_date"]
        ctx = phases.get(date_iso)
        if ctx is None:
            continue  # no causal phase classification for this date (short benchmark window) -> excluded
        phase = ctx["phase"]
        by_phase_returns[phase].append((date_iso, row["forward_return"]))
        stored = stored_by_key.get((row["ticker"], date_iso))
        if stored is None:
            continue
        mdd, uw, ttr = stored
        if mdd is not None:
            by_phase_mdd[phase].append(mdd)
        if uw is not None:
            by_phase_uw[phase].append(uw)
        if ttr is not None:
            by_phase_ttr[phase].append(ttr)

    by_phase = [
        {
            "phase": phase,
            "n": len(by_phase_returns.get(phase, [])),
            "max_drawdown": _distribution_cell(by_phase_mdd.get(phase, []), wf.min_sample),
            "underwater_days": _distribution_cell(by_phase_uw.get(phase, []), wf.min_sample),
            "time_to_recover_days": _distribution_cell(by_phase_ttr.get(phase, []), wf.min_sample),
            "loss_streak": _loss_streak_cell(by_phase_returns.get(phase, []), wf.streak_min_n),
        }
        for phase in cfg.market_phase.labels
    ]

    return {
        "horizon": horizon,
        "min_sample": wf.min_sample,
        "streak_min_n": wf.streak_min_n,
        "survivorship_bias": SURVIVORSHIP_BIAS_LABEL,
        "method_note": LOSS_STREAK_METHOD_NOTE,
        "by_phase": by_phase,
    }


# --- cached serving (J-72 performance layer) — REQUIRED because /api/evidence calls this ONCE PER CLAIM ---
# `compute_drawdown_expectations` resolves a full research cohort (`compute_samples`, the SAME cost a
# Factor/Combination/Event-study lab request pays), which costs several hundred ms to ~1s+ on the deep
# 30-year/590-symbol basis. `/api/evidence` renders EVERY claim's panel on ONE page load (7 claims today),
# so an uncached call multiplies that cost by the claim count — measured ~9.4s total for 7 claims,
# regressing the J-15 latency budget by ~3x. Every OTHER research-derived aggregate in this codebase (the
# Factor/Combination/Event-study/Regime/Phase-Severity/Regime-Phase-Factor labs) already solves this
# EXACT problem the SAME way: serve from the shared `EventStudyCache` table (J-72), keyed by
# `(subject, view, asof_key, dataset_version, horizon)`, computed once and refreshed automatically when
# the dataset changes. This reuses that SAME table (a namespaced `subject` prevents any cross-feature
# collision) rather than adding a parallel cache mechanism.
_DD_EXPECTATIONS_VIEW = "drawdown_expectations"  # the EventStudyCache `view` slot reserved for this feature
_DD_EXPECTATIONS_ASOF_KEY = "all"  # this aggregation is always all-history (mirrors research._ASOF_ALL)


def _drawdown_expectations_cache_subject(claim: dict) -> str:
    """A STABLE, BOUNDED `EventStudyCache.subject` for ONE claim: a namespaced SHA-256 of its canonical
    (sorted-key) JSON, so distinct claims never collide, identical claims always hit the SAME row, and an
    arbitrarily long combination `condition` list never risks a column-length surprise. The `dd_exp:`
    namespace prefix guarantees no collision with another feature's subject on this SHARED cache table."""
    import hashlib

    canonical = json.dumps(claim, sort_keys=True, default=str)
    return f"dd_exp:{hashlib.sha256(canonical.encode()).hexdigest()}"


def compute_drawdown_expectations_cached(
    session: Session, claim: dict, config: Optional[Config] = None
) -> Optional[dict]:
    """Serve `compute_drawdown_expectations` from the shared J-72 `EventStudyCache` (a pure performance
    layer — No recompute in the read path): a HIT for the current `(subject, view, asof_key,
    dataset_version, horizon)` key deserializes and returns the stored payload; a MISS computes it ONCE via
    `compute_drawdown_expectations`, persists it (a `None` result is cached too — an honestly-unresolvable
    cohort is still a stable answer for this dataset version, and caching it avoids re-paying the SAME
    expensive miss every request), prunes stale rows for this claim, and returns it. The returned payload
    is BYTE-IDENTICAL to a fresh `compute_drawdown_expectations(...)` call. `GET /api/evidence` calls THIS
    function, never the uncached one directly."""
    cfg = config or get_config()
    horizon = claim.get("horizon")
    if horizon not in cfg.walk_forward.underwater_horizons:
        return None  # the same scope gate compute_drawdown_expectations applies — skip the DB round-trip

    # lazy import — app.engine.research imports FROM this module, so a module-level import back would be
    # circular (mirrors this file's other lazy imports of market_phase/samples, immediately above).
    from app.engine.research import _dataset_version

    subject = _drawdown_expectations_cache_subject(claim)
    version = _dataset_version(session)

    hit = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject,
            EventStudyCache.view == _DD_EXPECTATIONS_VIEW,
            EventStudyCache.asof_key == _DD_EXPECTATIONS_ASOF_KEY,
            EventStudyCache.dataset_version == version,
            EventStudyCache.horizon == horizon,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once and persist under the current dataset-version stamp.
    payload = compute_drawdown_expectations(session, claim, cfg)

    # prune stale rows for THIS claim (any older dataset_version) so the cache table does not grow
    # unbounded as the dataset matures; the current-version row is then inserted.
    stale = session.exec(
        select(EventStudyCache).where(
            EventStudyCache.subject == subject,
            EventStudyCache.view == _DD_EXPECTATIONS_VIEW,
            EventStudyCache.asof_key == _DD_EXPECTATIONS_ASOF_KEY,
            EventStudyCache.horizon == horizon,
            EventStudyCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(EventStudyCache(
        subject=subject, view=_DD_EXPECTATIONS_VIEW, asof_key=_DD_EXPECTATIONS_ASOF_KEY,
        dataset_version=version, horizon=horizon, payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # a concurrent writer raced us to the same key — best-effort cache, not a source of
        session.rollback()  # truth; the freshly computed payload is still byte-identical, so return it
    return payload
