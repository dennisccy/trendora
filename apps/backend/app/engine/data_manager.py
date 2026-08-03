"""Data Manager — on-demand dataset growth (Data Contract: app.engine.data_manager, J-17).

This module ORCHESTRATES the existing canonical create-once paths; it computes NO score, bucket, or
forward return of its own (the #1 coherence guard for this iteration). Specifically:

  * `compute_coverage` is READ-ONLY descriptive metadata over `daily_prices` + `scanner_runs`
    (price-history range, distinct symbol count, the set of snapshot/as-of dates, and the backfill
    GAPS = trading days that have bars but no snapshot). It recomputes no canonical value.

  * `run_data_job` runs a single fetch and/or backfill job over a date or `[start, end]` range:
      - BACKFILL (offline/deterministic): for each in-range trading day that has bars but no snapshot,
        it calls the EXISTING `scanner.run_scan` (create-once via `get_run_for_date`, bars <= D) then
        `forward_testing.backfill_run_forward_returns` (INSERT-only realized returns, bars > D). It
        never re-implements scan/return math and never overwrites a snapshot — so the new dates appear
        in the as-of switcher and the System Health sample size `n` grows (anti-goals: Snapshots
        immutable / No lookahead / Range backfill stays immutable & lookahead-free).
      - FETCH (live, real-data-only): pulls REAL EOD bars via the config-selected LIVE provider for the
        chosen range and persists only NEW `(symbol, date)` rows (never overwriting committed seed bars).
        On a per-symbol provider failure it counts the symbol failed, persists ZERO bars for it, and
        surfaces an explicit error — it NEVER fabricates a price (anti-goal: Live fetch is real-data-only).

Live progress lives in an in-memory job registry keyed by `job_id`; the FINAL summary is persisted ONCE
to the append-only `DataProviderRun` table (structured detail JSON-encoded in `message`). The default
boot path is untouched — this job is on-demand only and opens its OWN DB session (never the request's).
Every job limit / display cap is read from `config.data_manager` (anti-goal: No magic numbers)."""
from __future__ import annotations

import copy
import csv
import ctypes
import ctypes.util
import gc
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import delete, func, insert
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, ImportChunkingCfg, ProviderCatalogEntry, get_config
from app.data_providers import make_provider
from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
from app.data_providers.seed_provider import SeedProvider, symbol_to_filename
from app.db import get_engine
from app.engine import drift as drift_module
from app.engine import evidence  # ops-hardening iter-7 (J-06): the finalize hook warms drawdown_expectations
from app.engine import forward_testing, scanner
from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
from app.engine.prices import (
    _BarCache,
    active_bar_cache,
    attach_shared_cache,
    bar_cache,
    bars_asof,
    latest_data_date,
    prefilled_bar_cache,
)
from app.engine import universe_resolver
from app.engine.universe_screen import (
    DEFAULT_SEED_DIR,
    pool_survivorship,
    read_pool,
    screen_reasons,
)
from app.models import (
    CoverageSnapshot,
    DailyPrice,
    DataProviderRun,
    ForwardReturn,
    ImportCheckpoint,
    MacroSeries,
    MembershipTimelineCache,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)
from app.engine.research import (
    _dataset_version,  # single-sourced cache stamp (J-72/J-87) — never duplicated
    _membership_dataset_version,  # J-100: the NARROW membership-cache stamp (no forward-return term)
    event_study_cached,  # ops-hardening iter-2 (J-05): the ingest finalize hook warms one default hot key
    subject_catalog,
)
from app.seed_loader import price_load_symbols

logger = logging.getLogger("trendora.data_manager")

# Injectable sleep (J-34): the chunked fetch's inter-request delay + 429 backoff call this. Tests pass
# their own recorder so backoff/sleep add NO wall-clock (MEMORY: backend-test-suite-runtime).
_sleep: Callable[[float], None] = time.sleep

JOB_KINDS = ("fetch", "backfill", "both", "expand", "rebuild")
_FETCH_KINDS = ("fetch", "both")
_BACKFILL_KINDS = ("backfill", "both")
# J-85: the confirm-gated regenerate-from-scratch snapshot rebuild. It is neither a fetch nor a generic
# backfill — it CLEARS the entire snapshot set first, then drives the EXISTING create-once backfill over
# every covered trading date. Its own branch in `_run_job` (reusing `_do_backfill` + the J-66 progress).
_REBUILD_KINDS = ("rebuild",)
# J-34/J-59: the durable-checkpoint statuses a Resume can act on. `resumable` is a rate-limited 429 pause
# (resume re-attempts from the un-fetched chunk); `failed_backfill` (J-59) is a `both` job whose FETCH
# completed but whose BACKFILL failed — a Resume skips the completed fetch entirely (zero provider calls)
# and re-runs only the backfill stage.
RESUMABLE_CHECKPOINT_STATUSES = ("resumable", "failed_backfill")
# J-35: the expand kind reuses the chunked-fetch engine (over the pool) but is neither a generic fetch
# (it adds a market-cap fetch + the screen + the universe.json write) nor a backfill — its own branch.
_EXPAND_KINDS = ("expand",)
# Cap stored per-symbol error strings so a wholly-failed fetch (e.g. 158 symbols) keeps the job record
# bounded; the failed COUNT is always exact (this only truncates the example messages shown).
_MAX_ERROR_SAMPLES = 20
# J-35: cap the stored omitted-with-reason list so an all-omitted expand (e.g. ~548 candidates) keeps the
# job record + the persisted run bounded; the passer/omitted COUNTS stay exact (only the list is bounded).
_MAX_OMITTED_SAMPLES = 60


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _compute_speedup(
    per_date_seconds_sum: Optional[float],
    elapsed_seconds: Optional[float],
    *,
    override: Optional[float] = None,
) -> Optional[float]:
    """J-66 — the backfill speedup factor, derived SERVER-SIDE (the sequential per-date compute sum divided
    by the parallel wall-clock). Returns None (honest NA) when either figure is missing or non-positive —
    never a fabricated ratio. `override` (rare) supplies a pre-computed value verbatim. Moved here from the
    frontend `speedupFactor()` so the frontend only re-formats the backend number (coherence: one derivation
    site)."""
    if override is not None:
        return round(float(override), 4)
    if per_date_seconds_sum is None or elapsed_seconds is None:
        return None
    if per_date_seconds_sum <= 0 or elapsed_seconds <= 0:
        return None
    return round(per_date_seconds_sum / elapsed_seconds, 4)


# --------------------------------------------------------------------------------------------------
# Coverage — read-only descriptive metadata (recomputes no canonical score/return)
# --------------------------------------------------------------------------------------------------
def _trading_days(session: Session, cfg: Config) -> list[date_cls]:
    """The trading calendar = the benchmark's (SPY) seed bar dates, ascending — the SAME calendar the
    walk-forward uses. A date is a trading day iff SPY has a bar on it; this never fabricates a date."""
    latest = latest_data_date(session)
    if latest is None:
        return []
    benchmark = cfg.etfs.index[0]
    return [bar.date for bar in bars_asof(session, benchmark, latest)]


def _per_symbol_coverage(session: Session, cfg: Config) -> list[dict]:
    """J-36 — the per-symbol / per-universe-member coverage table: one row per stored `DailyPrice.symbol`
    AND one row per `config.universe.symbols` member, each a READ-ONLY descriptive metadata record that
    recomputes NO canonical score/return/bucket/setup. Each row carries:
      - `symbol`,
      - `in_universe`  — membership read from the SINGLE canonical `config.universe.symbols` (the same
                         source `universe_count` / /api/methodology read — no second universe computation),
      - `has_data`     — the symbol has >= 1 stored bar,
      - `first`/`last` — the bar-date range from `daily_prices` (NA / None when no bars — NEVER fabricated),
      - `bar_count`    — the stored bar count,
      - `thin`         — true iff `0 < bar_count < indicators.min_history_bars` (the thin threshold is read
                         from config — No magic number),
      - `missing`      — true iff a universe member has no data (shown missing, never a faked zero-bar row).

    The (range, count) come from a single grouped scan of `daily_prices`; membership comes from config.
    Rows are sorted: universe members first (alphabetical), then the remaining priced symbols (alphabetical)
    — purely presentational; the API serves one canonical ordered list and the UI re-sorts/filters only."""
    thin_threshold = cfg.indicators.min_history_bars  # the canonical "thin/insufficient" cutoff (config)
    universe = list(cfg.universe.symbols)
    universe_set = set(universe)

    # One grouped pass over daily_prices → {symbol: (bar_count, first, last)} for every PRICED symbol.
    stats_rows = session.exec(
        select(
            DailyPrice.symbol,
            func.count(DailyPrice.id),
            func.min(DailyPrice.date),
            func.max(DailyPrice.date),
        ).group_by(DailyPrice.symbol)
    ).all()
    stats: dict[str, tuple[int, Optional[date_cls], Optional[date_cls]]] = {
        symbol: (int(count or 0), first, last) for symbol, count, first, last in stats_rows
    }

    # The row set = every priced symbol ∪ every universe member (a member with no bars still gets a row).
    all_symbols = sorted(set(stats) | universe_set)

    def _row(symbol: str) -> dict:
        bar_count, first, last = stats.get(symbol, (0, None, None))
        in_universe = symbol in universe_set
        has_data = bar_count > 0
        return {
            "symbol": symbol,
            "in_universe": in_universe,
            "has_data": has_data,
            "first": first.isoformat() if first else None,  # NA when no bars — never fabricated
            "last": last.isoformat() if last else None,
            "bar_count": bar_count,
            "thin": 0 < bar_count < thin_threshold,  # strictly between 0 and the config threshold
            "missing": in_universe and not has_data,  # a universe member with no data is MISSING (NA), not faked
        }

    rows = [_row(s) for s in all_symbols]
    # universe members first (alphabetical), then the rest (alphabetical) — presentational only.
    rows.sort(key=lambda r: (not r["in_universe"], r["symbol"]))
    return rows


def _missing_data_diagnostic(session: Session, cfg: Config) -> dict:
    """J-37 — the Missing-data diagnostic: a READ-ONLY honest report of every universe member that is
    INSUFFICIENT FOR ANALYSIS, derived ONCE from the SAME stored bars + `config.universe.symbols` +
    `indicators.min_history_bars` + the benchmark trading calendar the J-36 table / walk-forward already
    use. It recomputes NO score/return/bucket/setup and fabricates nothing (a member with no/thin history
    is shown missing/thin, never a faked range or filled value). Three honest categories, each row carrying
    the symbol + the EXACT shortfall:

      (a) `no_history`   — a universe member with ZERO stored bars (`bars_have=0`, `bars_needed=threshold`).
      (b) `thin`         — `0 < bar_count < indicators.min_history_bars` (carries `bars_have`/`bars_needed`).
      (c) `intra_series_gap` — trading days MISSING inside the member's own first→last range, measured
                           against the benchmark calendar (carries `missing_day_count` +
                           `[first_gap, last_gap]` + a bounded preview of the missing dates).

    A member that is fine appears in NO category. The thin threshold and the trading calendar both come
    from config (No magic number). `pullable` flags the rows a one-click pull can act on: no-history and
    intra-series-gap members (a thin member's gap, if any, surfaces as an intra-series-gap row; a thin
    member with a contiguous-but-short series has no gap to pull and is shown for transparency only)."""
    threshold = cfg.indicators.min_history_bars  # canonical "insufficient-for-analysis" cutoff (config)
    universe = list(cfg.universe.symbols)
    universe_set = set(universe)
    calendar = _trading_days(session, cfg)  # benchmark (SPY) bar dates, ascending — the SAME calendar
    calendar_set = set(calendar)
    preview_cap = cfg.data_manager.gap_preview  # reuse the existing gap-preview display cap (No magic number)

    # One grouped pass over daily_prices → {symbol: (bar_count, first, last)} for the universe members.
    stats_rows = session.exec(
        select(
            DailyPrice.symbol,
            func.count(DailyPrice.id),
            func.min(DailyPrice.date),
            func.max(DailyPrice.date),
        )
        .where(DailyPrice.symbol.in_(universe))
        .group_by(DailyPrice.symbol)
    ).all()
    stats: dict[str, tuple[int, Optional[date_cls], Optional[date_cls]]] = {
        symbol: (int(count or 0), first, last) for symbol, count, first, last in stats_rows
    }

    # item H (iter-24 fast-platform pass): ONE bulk query for every universe member's own dates, bounded
    # to `universe` (~len(config.universe.symbols) members — its SCOPE is bounded, never a whole-table
    # scan) — replaces the FORMER one-`DailyPrice.date`-query-per-member loop (a query per member that
    # HAS data, run on every cold `/api/data` coverage compute). Grouped in Python into per-symbol date
    # sets BEFORE the existing gap-diff logic below, which is otherwise UNCHANGED — byte-identical output
    # (a symbol's bars outside its own [first, last] range, if any, are irrelevant to that logic either
    # way, so narrowing the query to `[first, last]` per symbol would have been equivalent; fetching the
    # full per-symbol series here is simpler and still strictly bounded to the universe).
    #
    # iter-40 (J-07 last blocker): being bounded IN SCOPE (the `WHERE ... IN (universe)` clause) is NOT
    # the same as being bounded IN MEMORY. Iterating `session.exec(select(...))` directly makes SQLAlchemy
    # materialize the WHOLE result via `cursor._raw_all_rows()` before this loop's body ever runs (see
    # `sqlalchemy/orm/loading.py::chunks`) — on the deep basis that is ~3.3M `(symbol, date)` rows held
    # live in one Python list, confirmed as the ACTUAL wedge site in iter-39's trial-3 drill (a `MemoryError`
    # raised from this exact line's `_raw_all_rows()` call,
    # `runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:17-29`) and the reason
    # three separate cap trials could never reach the aggregate-warm handlers this drill was actually
    # targeting. `.yield_per(cfg.research.read_batch_size)` streams the SAME query in bounded-size batches
    # instead — the SAME knob `prices.py`'s `_BarCache.prefill` / `research.py` / `forward_testing.py`
    # already use for this exact pattern (see `prices.py:132-141`). The grouping into
    # `own_dates_by_symbol` below and every downstream consumer are UNCHANGED — only the fetch strategy
    # (materialize-then-iterate vs. stream-in-batches) changes; the output is byte-identical (TC-1).
    own_dates_by_symbol: dict[str, set[date_cls]] = {}
    _diag_batch = cfg.research.read_batch_size
    for symbol, d in session.exec(
        select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))
    ).yield_per(_diag_batch):
        own_dates_by_symbol.setdefault(symbol, set()).add(d)

    no_history: list[dict] = []
    thin: list[dict] = []
    intra_gaps: list[dict] = []

    for symbol in sorted(universe_set):
        bar_count, first, last = stats.get(symbol, (0, None, None))

        if bar_count == 0:
            # (a) no-history — a member with zero stored bars. The pull target is the full benchmark
            # calendar window (first→last trading day) — exactly the dates a fetch would supply.
            no_history.append({
                "symbol": symbol,
                "category": "no_history",
                "bars_have": 0,
                "bars_needed": threshold,
                "pull_start": calendar[0].isoformat() if calendar else None,
                "pull_end": calendar[-1].isoformat() if calendar else None,
                "pullable": bool(calendar),
            })
            continue

        # (b) thin — strictly between 0 and the config threshold (insufficient history for analysis).
        if bar_count < threshold:
            thin.append({
                "symbol": symbol,
                "category": "thin",
                "bars_have": bar_count,
                "bars_needed": threshold,
                # a thin member's exact shortfall is bars; the actionable gap (if its series has holes)
                # surfaces separately as an intra_series_gap row, so a thin row alone is not pullable.
                "pullable": False,
            })

        # (c) intra-series gap — trading days (benchmark calendar) MISSING inside the member's own
        # first→last range. Measured against the SAME calendar; never a fabricated date.
        if first is not None and last is not None:
            own_dates = own_dates_by_symbol.get(symbol, set())
            missing_in_range = sorted(
                d for d in calendar_set if first <= d <= last and d not in own_dates
            )
            if missing_in_range:
                intra_gaps.append({
                    "symbol": symbol,
                    "category": "intra_series_gap",
                    "missing_day_count": len(missing_in_range),
                    "first_gap": missing_in_range[0].isoformat(),
                    "last_gap": missing_in_range[-1].isoformat(),
                    "missing_preview": [d.isoformat() for d in missing_in_range[:preview_cap]],
                    # the pull target is exactly the gap span (first_gap → last_gap); the chunked fetch's
                    # INSERT-new-only guard fills only the missing dates inside it (idempotent).
                    "pull_start": missing_in_range[0].isoformat(),
                    "pull_end": missing_in_range[-1].isoformat(),
                    "pullable": True,
                })

    affected = len(no_history) + len(thin) + len(intra_gaps)
    return {
        "threshold": threshold,  # indicators.min_history_bars — surfaced so the UI states the cutoff
        "no_history": no_history,
        "thin": thin,
        "intra_series_gaps": intra_gaps,
        "affected_count": affected,
    }


def _resolve_coverage_asof(session: Session, as_of: Optional[date_cls], cfg: Config) -> Optional[date_cls]:
    """The as-of date the coverage block resolves the dynamic universe at (J-93). A provided in-range
    `as_of` is used verbatim; `None` falls back to the latest STORED run date, then the latest data date.
    Returns None only on a wholly-empty DB (no bars at all). NEVER fabricates a date — it only picks an
    existing reference date so `universe_count` reflects a real point-in-time resolution."""
    if as_of is not None:
        return as_of
    latest_run = session.scalar(select(func.max(ScannerRun.asof_date)))
    if latest_run is not None:
        return latest_run
    return latest_data_date(session)


def _resolved_universe(
    session: Session, as_of: Optional[date_cls], cfg: Config
) -> dict:
    """The as-of-resolved universe contract (J-93/J-94) the coverage block + methodology read from ONE
    place: the members resolved AT the resolved as-of date, the candidate-pool denominator, and the
    per-date excluded-by-reason counts. Returns the resolver's descriptive payload PLUS the resolved
    `asof` (or an honest empty shape on a wholly-empty DB — no fabricated members/date)."""
    resolved_asof = _resolve_coverage_asof(session, as_of, cfg)
    if resolved_asof is None:
        pool = read_pool()
        return {
            "asof": None,
            "candidate_pool_count": len({row["symbol"] for row in pool}),
            "admitted": [],
            "admitted_count": 0,
            "excluded_counts": {r: 0 for r in universe_resolver.EXCLUSION_REASONS},
            "resolutions": [],
        }
    return universe_resolver.resolve_with_reasons(session, resolved_asof, cfg)


def _coverage_diagnostic_absent(
    session: Session, cfg: Config, *, universe: Optional[list[str]] = None
) -> dict:
    """J-85 — the universe-vs-latest-snapshot coverage diagnostic: the resolved-universe members
    (`config.universe.symbols` — the one canonical screen result) that are ABSENT from the LATEST scanner
    snapshot's scored set (`scanner_results.ticker` for the newest `ScannerRun`). This is a READ-ONLY
    descriptive derivation over stored rows + the resolved universe (no canonical score/return/bucket is
    recomputed). It surfaces the operator-facing signal "N members are not yet in the latest snapshot —
    rebuild to include them" after a universe expansion (J-84).

    Returns `{absent_count, absent_preview, latest_snapshot_date, universe_count}`:
      - `absent_count`        — the EXACT count of universe members absent from the latest snapshot's
                                scored tickers (0 when every member is present → the UI shows NO banner).
      - `absent_preview`      — a bounded, sorted sample of the absent tickers (`data_manager.gap_preview`).
      - `latest_snapshot_date`— the newest `ScannerRun.asof_date` (ISO), or None when no snapshot exists.
      - `universe_count`      — J-93: the members RESOLVED at the latest snapshot date (the as-of-dependent
                                membership, the same denominator coverage shows for that date), NOT the
                                static pool size.
      - `candidate_pool_count`— the full candidate-pool size carried beside the resolved count (J-93).

    J-93: the resolved universe at the latest snapshot date is computed via `universe_resolver` (the SINGLE
    membership path) — passed in by the caller as `universe` so it is resolved ONCE per coverage call (no
    second resolution). Honest edge cases: NO snapshot yet → `absent_count == universe_count` (every
    resolved member is absent because there is nothing scored), `latest_snapshot_date` None. An empty
    (pre-warm-up) resolved universe → `absent_count == 0`. Comparison is case-normalized (uppercased)."""
    pool_count = len({row["symbol"] for row in read_pool()})
    if universe is None:
        # standalone call (tests / fallback): resolve at the latest snapshot/data date once.
        universe = _resolved_universe(session, None, cfg)["admitted"]
    universe_count = len(universe)
    latest_date = session.scalar(select(func.max(ScannerRun.asof_date)))
    if latest_date is None:
        # no snapshot at all → every resolved member is absent (nothing scored), no fabricated coverage.
        preview = cfg.data_manager.gap_preview
        absent_sorted = sorted(universe)
        return {
            "absent_count": universe_count,
            "absent_preview": absent_sorted[:preview],
            "latest_snapshot_date": None,
            "universe_count": universe_count,
            "candidate_pool_count": pool_count,
        }
    latest_run_id = session.scalar(
        select(ScannerRun.id).where(ScannerRun.asof_date == latest_date)
    )
    scored = {
        t.upper()
        for t in session.exec(
            select(ScannerResult.ticker).where(ScannerResult.run_id == latest_run_id)
        ).all()
    }
    absent = sorted(sym for sym in universe if sym.upper() not in scored)
    preview = cfg.data_manager.gap_preview
    return {
        "absent_count": len(absent),
        "absent_preview": absent[:preview],
        "latest_snapshot_date": latest_date.isoformat(),
        "universe_count": universe_count,
        "candidate_pool_count": pool_count,
    }


def _universe_diagnostic(resolved: dict, cfg: Config) -> dict:
    """J-94 — the per-date coverage diagnostic for the resolved as-of: the admitted count and the
    excluded-by-reason counts (below_history / below_price / below_adv) against the candidate-pool
    denominator. A read-only re-projection of the already-computed `resolved` resolver payload (no
    second resolution, no canonical-value recompute). Carries the config thresholds VERBATIM so the UI
    states the exact cutoffs (No magic number — the values are config reads, not literals)."""
    filters = cfg.universe.filters
    excluded = resolved["excluded_counts"]
    return {
        "asof": resolved["asof"],
        "candidate_pool_count": resolved["candidate_pool_count"],
        "admitted_count": resolved["admitted_count"],
        "excluded_total": sum(excluded.values()),
        # keyed by the FULL resolver vocabulary in gate order (iter-18 adds `stale_series` — the recency
        # gate that exits a name whose data ended mid-history).
        "excluded": {reason: excluded[reason] for reason in universe_resolver.EXCLUSION_REASONS},
        # the exact cutoffs the resolver gated on (config reads — surfaced so the UI never re-types them).
        "thresholds": {
            "min_history_bars": cfg.indicators.min_history_bars,
            "min_price": filters.min_price,
            "min_dollar_vol": filters.min_dollar_vol,
            "adv_window_days": filters.adv_window_days,
            "max_staleness_days": filters.max_staleness_days,
        },
    }


def _warmup_boundary_date(session: Session, cfg: Config) -> Optional[date_cls]:
    """J-94 — the deterministic warm-up boundary: the FIRST benchmark (SPY) trading day on/after which a
    name starting at the seed price-start could have >= `indicators.min_history_bars` trailing bars.
    Computed structurally from the trading calendar (the seed-start + (min_history_bars - 1) trading
    days) — NOT a magic literal; None on a calendar shorter than the threshold (warm-up never reached)."""
    calendar = _trading_days(session, cfg)
    min_bars = cfg.indicators.min_history_bars
    if len(calendar) < min_bars:
        return None
    return calendar[min_bars - 1]  # the date on which the (min_bars)-th bar exists (0-indexed offset)


def _membership_labels(session: Session, cfg: Config) -> dict:
    """J-96 — the three HONEST labels carried verbatim beside the membership timeline (single source —
    the UI re-types none of this copy):
      - `survivorship`     — the candidate-pool current-constituent caveat (J-95b),
      - `warmup`           — the deterministic warm-up boundary (the date the universe can first be full),
      - `universe_relative`— the breadth/walk-forward universe-relative + dynamic-vs-static caveat.
    Plain-language, descriptive metadata — recomputes no canonical value."""
    boundary = _warmup_boundary_date(session, cfg)
    min_bars = cfg.indicators.min_history_bars
    return {
        "survivorship": pool_survivorship(),
        "warmup": {
            "min_history_bars": min_bars,
            "boundary_date": boundary.isoformat() if boundary else None,
            "label": (
                f"Warm-up: a name is admitted at a date only once it has at least {min_bars} trailing "
                f"bars from that date. Before the warm-up boundary"
                + (f" (~{boundary.isoformat()})" if boundary else "")
                + " the resolved universe is honestly smaller or empty — not an error."
            ),
        },
        "universe_relative": (
            "Breadth and walk-forward evidence are universe-relative. The dynamic point-in-time universe "
            "REDUCES survivorship versus the static current-membership universe (a 30-bar name is never "
            "ranked against a 1000-bar peer), while residual pool-survivorship remains until a true "
            "point-in-time index-constituent feed is added."
        ),
    }


def _membership_timeline(
    session: Session, cfg: Config, snapshot_dates: list[date_cls]
) -> dict:
    """J-96 — the dynamic-universe membership timeline: a READ-ONLY descriptive derivation over the
    stored per-snapshot `ScannerResult` membership (the persisted scored-ticker sets that ARE the
    membership — recomputes NO score/return/membership) producing, per snapshot date (ascending):
      - `size`            — the resolved universe size (the stored scored-ticker count) → a step function,
      - `entries`         — names appearing for the FIRST time across the timeline (first date a name is
                            in a snapshot's scored set),
      - `exits`           — names that disappear (present on the prior observed date, absent now),
      - `excluded`        — the per-date excluded-by-reason counts (below_history / below_price /
                            below_adv) from the resolver over the SAME candidate pool + bars <= that date.

    Strictly causal: each date is observed from its OWN <= D snapshot + bars <= D (no future leakage).
    Deterministic. An empty DB / no snapshots → an empty-but-valid timeline (no fabricated dates/members).

    ops-hardening iter-36 (J-07/J-96 AG-8 memory bound): the per-date excluded-by-reason counts are now
    sourced via `_excluded_counts_by_date` (below), which BOUNDS peak resident bar data to a config-driven
    symbol-batch width instead of the full candidate pool's whole price history, WHEN no outer job-scoped
    bar cache is already active (see that helper's docstring). `entries`/`exits`/`size` are unaffected —
    they read only the persisted `members_by_date` membership, never a bar."""
    dates = sorted(snapshot_dates)
    pool_symbols = {row["symbol"] for row in read_pool()}
    pool_count = len(pool_symbols)
    points: list[dict] = []
    seen: set[str] = set()
    prev_members: set[str] = set()

    # one query: every (run.asof_date, ticker) so each snapshot's scored set is read once (no per-date
    # round-trip). Reads the persisted membership — the SINGLE source — never a re-resolution.
    rows = session.exec(
        select(ScannerRun.asof_date, ScannerResult.ticker)
        .join(ScannerResult, ScannerResult.run_id == ScannerRun.id)
    ).all()
    members_by_date: dict[date_cls, set[str]] = {}
    for asof_date, ticker in rows:
        members_by_date.setdefault(asof_date, set()).add(ticker.upper())

    excluded_by_date = _excluded_counts_by_date(session, cfg, dates, pool_symbols)

    for d in dates:
        members = members_by_date.get(d, set())
        # entries = members never seen on any earlier observed date; exits = prior members now gone.
        entries = sorted(m for m in members if m not in seen)
        exits = sorted(m for m in prev_members if m not in members)
        seen |= members
        prev_members = members
        points.append({
            "date": d.isoformat(),
            "size": len(members),
            "entries": entries,
            "exits": exits,
            "excluded": excluded_by_date[d],
        })

    return {
        "candidate_pool_count": pool_count,
        "points": points,
        # J-95(b)/J-96: the three honest labels carried VERBATIM beside the timeline (single source).
        "labels": _membership_labels(session, cfg),
    }


def _excluded_counts_by_date(
    session: Session, cfg: Config, dates: list[date_cls], pool_symbols: set[str],
) -> dict[date_cls, dict[str, int]]:
    """ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — the per-date excluded-by-reason tally
    `_membership_timeline`'s points read, computed one of two ways depending on whether an OUTER
    job-scoped bar cache is already active on `session`:

      - ACTIVE outer cache (e.g. `_do_backfill` / `_persist_per_date_coverage_snapshots`, which each open
        their OWN `prefilled_bar_cache` around a whole multi-date job before ever reaching this function):
        reuse it exactly as before — no new loading, no batching. That whole-job-scoped cost is already
        paid/accepted by the caller's own job and amortized across every date + aggregate it computes;
        this iteration does not touch it.
      - NO active cache (the standalone entry point — `_compute_coverage_uncached` called directly, e.g.
        by `refresh_coverage_snapshot`'s ingest-finalize call for the CURRENT date, or a cold `/data`-class
        read): the committed candidate pool is walked in `research.membership_timeline_batch_symbols`-wide
        batches. ONE `_BarCache` instance is created and its contents REPLACED per batch (`load_only`) —
        never a second instance, never `prefill`'s whole-table scan — so peak resident bar data scales
        with the batch width, not the full ~590-symbol pool. Each batch resolves EVERY snapshot date
        before the next batch loads (so a batch's bars are read `len(dates)` times, then discarded).

    Byte-identical either way: `resolve_with_reasons`'s excluded tally is a pure per-symbol classification
    with no cross-symbol interaction, so summing it over disjoint symbol batches equals resolving the
    whole pool at once (and the active-cache branch is the SAME unbatched call this function replaces)."""
    totals: dict[date_cls, dict[str, int]] = {
        d: {reason: 0 for reason in universe_resolver.EXCLUSION_REASONS} for d in dates
    }
    if active_bar_cache(session) is not None:
        for d in dates:
            diag = universe_resolver.resolve_with_reasons(session, d, cfg)
            for reason, n in diag["excluded_counts"].items():
                totals[d][reason] += n
        return totals

    batch_width = max(1, cfg.research.membership_timeline_batch_symbols)
    ordered_pool = sorted(pool_symbols)
    if not ordered_pool:
        return totals
    batch_cache = _BarCache()  # ONE instance for the whole loop below — its contents are REPLACED per
    # batch (`load_only`), never a second cache instance and never the whole-table `prefill` scan.
    with attach_shared_cache(session, batch_cache):
        for i in range(0, len(ordered_pool), batch_width):
            batch = ordered_pool[i : i + batch_width]
            batch_cache.load_only(session, batch)  # discards the PRIOR batch's bars, loads only this one
            for d in dates:
                diag = universe_resolver.resolve_with_reasons(session, d, cfg, symbols=batch)
                for reason, n in diag["excluded_counts"].items():
                    totals[d][reason] += n
    return totals


def membership_timeline_cached(
    session: Session, cfg: Config, snapshot_dates: list[date_cls]
) -> dict:
    """Serve the J-96 membership timeline from the iter-36 cache (mirrors `market_phase_cached` /
    `research.event_study_cached`): on a cache HIT for the current `dataset_version` stamp, deserialize
    and return the stored payload (NO recompute — the O(dates × pool) `resolve_with_reasons` loop is
    skipped); on a MISS, compute it ONCE via `_membership_timeline`, persist it under the current
    dataset-version stamp, prune any stale rows (older `dataset_version`), and return it. The returned
    payload is BYTE-IDENTICAL to `_membership_timeline(...)` — the cache is a pure performance layer
    (No recompute in the read path; permitted by the "derived once… persisted/cached, read from storage"
    clause for a deterministic read-only derivation).

    iter-42 (J-100): the key now carries the NARROW `_membership_dataset_version` stamp (the snapshot set
    + bars manifest + `min_history_bars`), NOT the J-72/J-87 `_dataset_version` (which folds in the
    forward-return row count). The membership timeline reads NO forward return, so a warm-up forward-return
    insert MUST NOT invalidate it — under the old broad stamp every forward-return insert churned the key
    and re-ran the O(dates × pool) resolver loop (the recompute storm J-100 closes). The narrow stamp still
    REFRESHES on a real membership change — a backfill add, a removal, or the J-85 rebuild — because each
    of those changes the snapshot set or the bars manifest; a stale row keyed to an older narrow stamp is
    never hit (and is pruned on write). The cached timeline spans the WHOLE history, so the key has no
    as-of slot — exactly one row per membership dataset version."""
    version = _membership_dataset_version(session, cfg)

    hit = session.exec(
        select(MembershipTimelineCache).where(
            MembershipTimelineCache.dataset_version == version,
        )
    ).first()
    if hit is not None:
        return json.loads(hit.payload_json)

    # MISS — compute once (the cold, BOUNDED compute) and persist under the current stamp.
    # ops-hardening iter-38 (audit B7, iter-36 — stale-docstring fix): `_membership_timeline`'s per-date
    # excluded-by-reason counts are sourced via `_excluded_counts_by_date` (above), which reuses an ACTIVE
    # outer job-scoped bar cache when one is already open (e.g. a `_do_backfill`/`_persist_per_date_
    # coverage_snapshots` caller), or else walks the candidate pool in `membership_timeline_batch_symbols`-
    # wide batches — ONE `_BarCache` instance whose contents are REPLACED per batch, never a single
    # whole-pool `prefilled_bar_cache` scan — so peak resident bar data is bounded by batch width, not by
    # the full candidate pool's price history (the O(dates) grouped-count round-trip this replaced no
    # longer runs either way). The warm-up daemon precomputes this off the boot path so the FIRST request
    # after a boot/rebuild is already a hit.
    payload = _membership_timeline(session, cfg, snapshot_dates)

    # prune stale rows (any older dataset_version) so the cache table does not grow unbounded as the
    # dataset matures; the current-version row is then inserted (idempotent upsert on the unique key).
    stale = session.exec(
        select(MembershipTimelineCache).where(
            MembershipTimelineCache.dataset_version != version,
        )
    ).all()
    for row in stale:
        session.delete(row)

    session.add(MembershipTimelineCache(
        dataset_version=version,
        payload_json=json.dumps(payload),
        created_at=datetime.now(timezone.utc),
    ))
    try:
        session.commit()
    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
        session.rollback()  # source of truth; the freshly computed payload is byte-identical, so return it
    return payload


# --------------------------------------------------------------------------------------------------
# J-100 (iter-42) — single-flight + result cache around `compute_coverage`'s heavy work.
#
# The iter-35/36/37 saga left ONE residual cost on the `/api/data` read path: even with the membership
# timeline cached, EVERY `compute_coverage` call still resolved `_resolved_universe` (`resolve_with_reasons`,
# ~8 s warm on the post-rebuild DB) per request with no single-flight. So N concurrent `/api/data` probes
# cost N heavy resolves — each holding a DB connection ~10 s — exhausting the pool (size 5 + overflow 10)
# and swap-thrashing the whole VM (the documented intermittent freeze). This single-flight makes N
# concurrent callers for the SAME resolved as-of + SAME membership-dataset stamp share ONE computation:
# the first computes (inside ONE shared process-level bar cache, scope (c) — load-once, memory-bounded);
# the rest WAIT on a per-key event and return the SAME cached payload. The served payload is BYTE-IDENTICAL
# to today's single-request output (it IS today's compute, run once and shared).
#
# It REUSES the warm-up controller's idiom (`warmup._WARMUP_LOCK` + a per-key in-flight guard) rather than
# inventing a new abstraction. The cache key is `(resolved_as_of_iso, membership_dataset_version)` — the
# membership stamp (scope (b)) changes on a real snapshot/bar change but NOT on a forward-return insert, so
# the cached coverage refreshes EXACTLY when a served value could change and is reused across the warm-up's
# forward-return churn. The cache holds only the LATEST few keys (bounded; a stale-stamp entry is dropped),
# never persisted to the DB — it is an in-process responsiveness layer, not a source of truth.
_COVERAGE_LOCK = threading.Lock()
# per-key in-flight events: key -> threading.Event set when the first computer finishes (so waiters wake).
_COVERAGE_INFLIGHT: dict[tuple, threading.Event] = {}
# the cached coverage payloads: key -> the computed dict. Bounded to the most-recent keys (see prune below).
_COVERAGE_RESULTS: dict[tuple, dict] = {}
# how many distinct (as_of, stamp) keys to retain — the live page asks for at most a handful of as-of
# dates at a time, and a stamp change invalidates the rest; this just bounds the dict against churn.
_COVERAGE_CACHE_MAX_KEYS = 8


def _db_identity(session: Session) -> str:
    """The bound database URL — scopes the in-process coverage cache to the ACTUAL data source. In
    production there is exactly one DB (one URL) so this is a constant; in tests each tmp-DB engine gets
    its OWN cache key space, so two distinct in-memory engines that happen to share a membership stamp
    (e.g. two empty three-snapshot fixtures, both `r3-rc3-bnone-bc0`) never serve each other's payload (a
    real stale-cache class the stamp alone would not catch — iter-38/39 cached-payload trap)."""
    try:
        return str(session.get_bind().url)
    except Exception:  # extremely defensive: a session with no resolvable bind → a single shared bucket.
        return "default"


# config-fingerprint memo: coverage output also depends on config values the membership stamp does NOT
# fold in (`gap_preview`, the per-symbol thin threshold, `universe.filters`, `universe.symbols`, …). In
# production exactly ONE cfg object lives for the process lifetime (reused per request), so the fingerprint
# is computed ONCE and reused; tests that pass a DISTINCT cfg get a DISTINCT fingerprint, so a second call
# with a different config never serves the first config's cached payload (the thin-threshold test trap).
# Memoized by `id(cfg)`, holding a reference to the cfg so its id cannot be recycled while the memo lives.
_CFG_FINGERPRINTS: dict[int, tuple] = {}


def _config_fingerprint(cfg: Config) -> str:
    """A stable content hash of the full config — folds EVERY coverage-affecting config value into the
    cache key so a different config never serves a cached payload computed under another (the thin-
    threshold / filter / gap-preview class the membership stamp alone would miss). Memoized by `id(cfg)`
    (production reuses one cfg object, so this hashes once); the memo holds the cfg reference so its id is
    not recycled into a stale fingerprint."""
    memo = _CFG_FINGERPRINTS.get(id(cfg))
    if memo is not None and memo[0] is cfg:
        return memo[1]
    fingerprint = hashlib.sha1(cfg.model_dump_json().encode()).hexdigest()
    _CFG_FINGERPRINTS[id(cfg)] = (cfg, fingerprint)
    # bound the memo (configs are rarely many; this just guards a pathological churn of throwaway configs).
    if len(_CFG_FINGERPRINTS) > _COVERAGE_CACHE_MAX_KEYS * 2:
        _CFG_FINGERPRINTS.clear()
        _CFG_FINGERPRINTS[id(cfg)] = (cfg, fingerprint)
    return fingerprint


def _coverage_cache_key(session: Session, as_of: Optional[date_cls], cfg: Config) -> tuple:
    """The single-flight / result-cache key: the bound DB identity + a full-config fingerprint + the
    RESOLVED as-of (the actual date the universe is resolved at, so `None`-falls-back-to-latest and an
    explicit-latest map to the SAME key) + the NARROW membership-dataset stamp (scope (b) — changes on a
    snapshot/bar change, NOT on a forward-return insert). Two callers share a compute iff they read the
    SAME DB under the SAME config and would produce the byte-identical payload."""
    resolved_asof = _resolve_coverage_asof(session, as_of, cfg)
    asof_key = resolved_asof.isoformat() if resolved_asof is not None else None
    stamp = _membership_dataset_version(session, cfg)
    return (_db_identity(session), _config_fingerprint(cfg), asof_key, stamp)


def compute_coverage(
    session: Session, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None
) -> dict:
    """Current dataset coverage — single-flight + result-cached (J-100), byte-identical to the underlying
    `_compute_coverage_uncached`. Concurrent `/api/data` callers for the SAME resolved as-of + membership
    stamp share ONE heavy compute (the first computes inside one shared bar cache; the rest wait and reuse
    the cached payload) — so N parallel probes cost ~one resolve, not N (the pool-exhaustion / VM-freeze
    fix). Returns a deep COPY of the cached payload so a caller mutating its result never corrupts a shared
    cache entry. The cache refreshes on any real membership change (the narrow stamp) and is reused across
    the warm-up's forward-return churn (which leaves the stamp unchanged). A `config` override or a
    standalone-test path with no concurrency still goes through this wrapper (correct + cheap)."""
    cfg = config or get_config()
    key = _coverage_cache_key(session, as_of, cfg)

    # fast path: an already-cached payload for this exact key — return a deep copy (no recompute, no lock
    # contention beyond the brief dict read). This is the warm-hit path N-1 of N concurrent probes take.
    with _COVERAGE_LOCK:
        cached = _COVERAGE_RESULTS.get(key)
        if cached is not None:
            return copy.deepcopy(cached)
        event = _COVERAGE_INFLIGHT.get(key)
        if event is None:
            # we are the FIRST caller for this key — claim it: register an unset event, then compute below
            # OUTSIDE the lock (so we never hold the global lock across the ~8 s resolve).
            event = threading.Event()
            _COVERAGE_INFLIGHT[key] = event
            is_owner = True
        else:
            is_owner = False

    if not is_owner:
        # another caller is computing this exact key — wait for it, then return the shared cached payload.
        event.wait()
        with _COVERAGE_LOCK:
            cached = _COVERAGE_RESULTS.get(key)
        if cached is not None:
            return copy.deepcopy(cached)
        # defensive: the owner failed to cache (an exception). Fall through and compute ourselves (rare).

    # OWNER path (or the defensive fall-through): compute ONCE, publish, wake any waiters.
    try:
        payload = _compute_coverage_uncached(session, cfg, as_of=as_of)
        with _COVERAGE_LOCK:
            _COVERAGE_RESULTS[key] = payload
            # bound the cache: drop the oldest keys (insertion order) beyond the retention cap so a long-
            # running process that sees many as-of/stamp keys never grows the dict unbounded.
            while len(_COVERAGE_RESULTS) > _COVERAGE_CACHE_MAX_KEYS:
                oldest = next(iter(_COVERAGE_RESULTS))
                del _COVERAGE_RESULTS[oldest]
        return copy.deepcopy(payload)
    finally:
        # release the in-flight slot + wake waiters whether we succeeded or raised (a waiter then either
        # finds the cached payload or computes defensively — never deadlocks on a failed owner).
        with _COVERAGE_LOCK:
            _COVERAGE_INFLIGHT.pop(key, None)
        event.set()


def reset_coverage_cache() -> None:
    """Clear the in-process single-flight coverage caches (J-100). For tests that mutate the DB and need a
    fresh compute, and for any explicit invalidation hook — the cache is keyed on the membership stamp so a
    real data change already invalidates it, but a test that asserts the compute COUNT wants a clean slate."""
    with _COVERAGE_LOCK:
        _COVERAGE_RESULTS.clear()
        _COVERAGE_INFLIGHT.clear()
        _CFG_FINGERPRINTS.clear()


def _compute_coverage_uncached(
    session: Session, cfg: Config, *, as_of: Optional[date_cls] = None
) -> dict:
    """Current dataset coverage — purely descriptive, recomputing NO canonical value:
      - price-history date range (min/max `DailyPrice.date`) and distinct symbol count,
      - the set of snapshot/as-of dates (`ScannerRun.asof_date`), newest first,
      - GAPS = trading days (bars present) with no snapshot — the actionable backfill targets — with a
        count plus a bounded preview (`config.data_manager.gap_preview`),
      - (J-36) `per_symbol` — the per-symbol / per-universe-member coverage table (see
        `_per_symbol_coverage`), consistency-bound: the distinct-symbol (has-data) row count ==
        `symbol_count` and the in-universe row count == `candidate_universe_count` (the static
        `config.universe.symbols` count — the data-table membership view).

    J-93/J-94: the universe contract is now AS-OF-DEPENDENT. `universe_count` is the members RESOLVED at
    `as_of` (the single global as-of; falls back to the latest stored run date when None) — the dynamic
    point-in-time membership the scored snapshot for that date scores — NOT the static pool size. The
    full-pool denominator (`candidate_pool_count`) and the static candidate-universe count
    (`candidate_universe_count`) are carried beside it. `universe_diagnostic` (J-94) is the per-date
    admitted + excluded-by-reason counts at `as_of`; `membership_timeline` (J-96) is the per-snapshot-date
    resolved-size step function + entries/exits + per-date excluded counts. Every figure is read-only
    descriptive metadata over the stored bars + config thresholds (recomputes no canonical score/return).

    iter-42 (J-100), scope (c): when this call is reached from WITHIN an outer job-scoped
    `prefilled_bar_cache` context (e.g. `_do_backfill` / `_persist_per_date_coverage_snapshots`, each
    already wrapping a whole multi-date job before calling this function per date), `_resolved_universe`'s
    `resolve_with_reasons` and the membership cold-compute both reuse that SAME already-loaded cache
    (`active_bar_cache`) — no new loading, one load amortized across the whole job, unchanged from before.

    ops-hardening iter-36 (J-07 AG-8 memory bound): this function no longer opens its OWN whole-table
    `prefilled_bar_cache` when called standalone (e.g. `refresh_coverage_snapshot`'s ingest-finalize call
    for the CURRENT date, or a cold test/tooling call with no outer job context) — that unconditional
    eager whole-candidate-pool prefill was the confirmed peak-memory driver for exactly this scenario
    (TC-1). `_resolved_universe`'s single-date resolve now runs the resolver's own default (no active
    context) per-symbol-bounded path in that case (already byte-identical and already the resolver's own
    documented fallback — see `resolve_with_reasons`); the membership cold-compute bounds its OWN loading
    via `_excluded_counts_by_date`'s config-driven symbol batching (see that helper). Byte-identical
    figures either way: only HOW bars are loaded changes (a pure performance/memory refactor), never what
    is computed."""
    return _compute_coverage_body(session, cfg, as_of=as_of)


def _compute_coverage_body(
    session: Session, cfg: Config, *, as_of: Optional[date_cls] = None
) -> dict:
    """The coverage derivation body. When an outer job-scoped bar cache is already active on `session`
    (see `_compute_coverage_uncached`'s docstring), every read below (the resolver + the membership
    cold-compute + the per-symbol table) reuses it automatically (`active_bar_cache`) — no signature
    change at any call site. With no outer cache active, each heavy sub-derivation bounds its OWN loading
    independently (the resolver's default per-symbol path; `_excluded_counts_by_date`'s symbol batching)."""
    price_min = session.scalar(select(func.min(DailyPrice.date)))
    price_max = session.scalar(select(func.max(DailyPrice.date)))
    symbol_count = session.scalar(select(func.count(func.distinct(DailyPrice.symbol))))

    snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
    snapshot_set = set(snapshot_dates)
    trading_days = _trading_days(session, cfg)
    gaps = [d for d in trading_days if d not in snapshot_set]
    preview = cfg.data_manager.gap_preview

    # J-93/J-94: resolve the dynamic universe at the as-of (single global as-of; None ⇒ latest stored run
    # date) ONCE — the SINGLE membership resolution this coverage call reads from (no second resolution).
    resolved = _resolved_universe(session, as_of, cfg)
    resolved_admitted = resolved["admitted"]

    # iter-36: the J-85 absent-from-latest diagnostic resolves the universe at the LATEST stored run date.
    # When THIS coverage call already resolved at that same latest date (the `as_of=None` default page
    # load, or an explicit as_of that equals the latest run), reuse `resolved_admitted` so the latest-date
    # universe is resolved ONCE — not twice — eliminating a redundant per-symbol resolve (~8 s on the
    # post-rebuild DB). Byte-identical: the same resolver over the same as-of yields the same admitted set
    # (the function's own `universe=` parameter is documented for exactly this single-resolution reuse).
    # When the requested as_of differs from the latest run date, pass None so J-85 resolves at the latest
    # date itself (its contract is "absent from the LATEST snapshot", independent of the page's as_of).
    latest_run_date = session.scalar(select(func.max(ScannerRun.asof_date)))
    absent_universe = resolved_admitted if resolved["asof"] == (
        latest_run_date.isoformat() if latest_run_date is not None else None
    ) else None

    return {
        "price_start": price_min.isoformat() if price_min else None,
        "price_end": price_max.isoformat() if price_max else None,
        "symbol_count": int(symbol_count or 0),
        # J-93: the AS-OF-RESOLVED universe size — the members the point-in-time resolver admits at the
        # resolved as-of (the dynamic membership the scored snapshot scores). Distinct from `symbol_count`
        # (distinct priced symbols incl. ETFs+^VIX) and from the static counts below.
        "universe_count": len(resolved_admitted),
        # J-93: the resolved as-of (ISO) the dynamic `universe_count` was computed at (None on an empty DB).
        "universe_asof": resolved["asof"],
        # the full candidate-pool denominator (the read_pool listing) the resolver screens — J-93.
        "candidate_pool_count": resolved["candidate_pool_count"],
        # the STATIC candidate-universe count (`len(config.universe.symbols)`) the per-symbol coverage
        # table's `in_universe` rows count (the data-table membership view — NOT date-scoped).
        "candidate_universe_count": len(cfg.universe.symbols),
        "snapshot_count": len(snapshot_dates),
        "snapshot_dates": [d.isoformat() for d in sorted(snapshot_dates, reverse=True)],
        "trading_day_count": len(trading_days),
        "gap_count": len(gaps),
        "gap_first": gaps[0].isoformat() if gaps else None,
        "gap_last": gaps[-1].isoformat() if gaps else None,
        "gaps_preview": [d.isoformat() for d in gaps[:preview]],
        # J-36: the per-symbol / per-universe-member coverage table (read-only descriptive metadata).
        "per_symbol": _per_symbol_coverage(session, cfg),
        # J-37: the Missing-data diagnostic — three honest categories of universe members insufficient
        # for analysis (no-history / thin / intra-series gap), each with its EXACT shortfall, derived from
        # the SAME stored bars + threshold + calendar above. Recomputes no canonical value; fabricates nothing.
        "diagnostic": _missing_data_diagnostic(session, cfg),
        # J-94: the per-date coverage diagnostic — for the resolved as-of, the admitted count + the
        # excluded-by-reason counts (below_history / below_price / below_adv) against the candidate-pool
        # denominator. Read-only descriptive derivation over the SAME stored bars + config thresholds.
        "universe_diagnostic": _universe_diagnostic(resolved, cfg),
        # J-96: the dynamic-universe membership timeline — per snapshot date the resolved size (step
        # function) + entries/exits + per-date excluded-by-reason counts. Strictly causal (each date
        # observed from its own <= D snapshot). Read-only over the stored ScannerResult membership + bars.
        # iter-36: served through the dataset-version-keyed cache (warmed off the boot path) so the
        # O(dates × pool) resolver loop is paid ONCE per dataset version, never per request — the served
        # payload is byte-identical to a fresh `_membership_timeline(...)` compute (No recompute in the
        # read path; the cache invalidates in lockstep with the J-72/J-87 caches on any dataset change).
        "membership_timeline": membership_timeline_cached(session, cfg, snapshot_dates),
        # J-85: the universe-vs-latest-snapshot coverage diagnostic — the count of resolved-universe
        # members ABSENT from the latest scanner snapshot's scored set (the operator-facing "rebuild to
        # include the new members" signal). Read-only descriptive derivation; 0 absent → the UI shows no
        # banner. Served on the SAME coverage block (no new endpoint).
        "absent_from_latest_snapshot": _coverage_diagnostic_absent(session, cfg, universe=absent_universe),
    }


# --------------------------------------------------------------------------------------------------
# ops-hardening iter-2 (J-05) — the coverage_snapshot persisted table. `GET /api/data` is served ONLY
# from this table (never a live `compute_coverage`/`_compute_coverage_uncached` call on the request path
# — that whole-table bar-prefill is the documented OOM/hang source, iter-24 evidence). The row is written
# by the ingest finalize hook (`_refresh_ingest_aggregates`, below) and the boot warm-up safety net
# (`app.engine.warmup._run_warmup`) — both reuse `_compute_coverage_uncached` verbatim, never a second
# derivation of the coverage figure.
# --------------------------------------------------------------------------------------------------
def _coverage_not_yet_computed_payload(cfg: Config) -> dict:
    """The honest 'not yet computed' coverage sentinel `coverage_from_storage` serves when no
    `CoverageSnapshot` row exists yet for the resolved key (before the first ingest finalize hook or the
    boot warm-up safety net has run). Issues ZERO database queries — only the committed-pool FILE read
    (`read_pool`, the same file `pool_survivorship`/`_resolved_universe` already read) plus config reads —
    so this fallback can never pay the whole-table bar-prefill cost the persisted snapshot exists to avoid
    (AG-8). Every DB-derived figure is honestly zero/null/empty — the SAME shape
    `_compute_coverage_uncached` already serves for a genuinely empty DB (never a fabricated value)."""
    pool_count = len({row["symbol"] for row in read_pool()})
    threshold = cfg.indicators.min_history_bars
    filters = cfg.universe.filters
    return {
        "price_start": None,
        "price_end": None,
        "symbol_count": 0,
        "universe_count": 0,
        "universe_asof": None,
        "candidate_pool_count": pool_count,
        "candidate_universe_count": len(cfg.universe.symbols),
        "snapshot_count": 0,
        "snapshot_dates": [],
        "trading_day_count": 0,
        "gap_count": 0,
        "gap_first": None,
        "gap_last": None,
        "gaps_preview": [],
        "per_symbol": [],
        "diagnostic": {
            "threshold": threshold,
            "no_history": [],
            "thin": [],
            "intra_series_gaps": [],
            "affected_count": 0,
        },
        "universe_diagnostic": {
            "asof": None,
            "candidate_pool_count": pool_count,
            "admitted_count": 0,
            "excluded_total": 0,
            "excluded": {reason: 0 for reason in universe_resolver.EXCLUSION_REASONS},
            "thresholds": {
                "min_history_bars": threshold,
                "min_price": filters.min_price,
                "min_dollar_vol": filters.min_dollar_vol,
                "adv_window_days": filters.adv_window_days,
                "max_staleness_days": filters.max_staleness_days,
            },
        },
        "membership_timeline": {
            "candidate_pool_count": pool_count,
            "points": [],
            "labels": {
                "survivorship": pool_survivorship(),
                "warmup": {
                    "min_history_bars": threshold,
                    "boundary_date": None,
                    "label": (
                        "Coverage has not been computed yet for this database — an ingest job or the "
                        "background warm-up will populate it shortly."
                    ),
                },
                "universe_relative": (
                    "Breadth and walk-forward evidence are universe-relative. The dynamic point-in-time "
                    "universe REDUCES survivorship versus the static current-membership universe (a "
                    "30-bar name is never ranked against a 1000-bar peer), while residual pool-survivorship "
                    "remains until a true point-in-time index-constituent feed is added."
                ),
            },
        },
        "absent_from_latest_snapshot": {
            "absent_count": 0,
            "absent_preview": [],
            "latest_snapshot_date": None,
            "universe_count": 0,
            "candidate_pool_count": pool_count,
        },
    }


def _upsert_coverage_snapshot(
    session: Session, asof_key: str, dataset_version: str, payload: dict
) -> None:
    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: reclaims
    EVERY row in the table left under a superseded `dataset_version` — ops-hardening iter-3 (B2), widened
    from the iter-2 original, which pruned only a stale row for THIS SAME `asof_key` and left every OTHER
    `asof_key`'s row under an old stamp orphaned forever once the dataset version moved on — then updates
    the current-stamp row in place if one already exists or inserts a fresh one. The reclaim is ONE bounded
    SQL `DELETE ... WHERE dataset_version != :current` (never a per-row Python scan), so it stays cheap
    regardless of how many stale `asof_key` rows have accumulated (this table is small — bounded by the
    handful of distinct as-of dates ever selected — never the multi-million-row `daily_prices` scale AG-8
    guards against). Mirrors `market_phase_cached`'s prune-stale-then-write upsert, generalized to also
    cover a repeat call under the SAME stamp — this is called unconditionally at the end of every
    successful ingest (not gated behind a cache-miss check, unlike the `*_cached` read-through caches).
    Shared by every caller — the ingest finalize hook's rich backfill/rebuild path AND its fetch/expand
    path (B1), plus `warmup.py`'s boot safety net — so all benefit automatically from one shared fix."""
    session.execute(delete(CoverageSnapshot).where(CoverageSnapshot.dataset_version != dataset_version))

    existing = session.exec(
        select(CoverageSnapshot).where(
            CoverageSnapshot.asof_key == asof_key,
            CoverageSnapshot.dataset_version == dataset_version,
        )
    ).first()
    now = datetime.now(timezone.utc)
    if existing is not None:
        existing.payload_json = json.dumps(payload)
        existing.computed_at = now
        session.add(existing)
    else:
        session.add(CoverageSnapshot(
            asof_key=asof_key, dataset_version=dataset_version,
            payload_json=json.dumps(payload), computed_at=now,
        ))
    try:
        session.commit()
    except Exception:  # a concurrent writer raced us to the same key — best-effort, not a source of truth
        session.rollback()


def refresh_coverage_snapshot_for(session: Session, cfg: Config, resolved_asof: date_cls) -> dict:
    """Compute + persist the `CoverageSnapshot` row for ONE SPECIFIC already-resolved as-of date (reusing
    the canonical `_compute_coverage_uncached` verbatim — byte-identical to a fresh compute FOR THAT as-of,
    never a second derivation). Shared by `refresh_coverage_snapshot` (the current stamp), the ingest
    finalize hook's per-date warm loop (`_persist_per_date_coverage_snapshots`), and `coverage_from_storage`'s
    read-path safety net for an already-ingested HISTORICAL as-of that predates this table. Returns the
    freshly persisted payload."""
    asof_key = resolved_asof.isoformat()
    dataset_version = _membership_dataset_version(session, cfg)
    # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls `membership_timeline_cached`
    # internally as part of computing this SAME payload — warming that cache is a free side effect of this
    # one call, never a second derivation.
    payload = _compute_coverage_uncached(session, cfg, as_of=resolved_asof)
    _upsert_coverage_snapshot(session, asof_key, dataset_version, payload)
    return payload


def refresh_coverage_snapshot(session: Session, cfg: Config) -> Optional[dict]:
    """Compute the CURRENT coverage payload (reusing the canonical `_compute_coverage_uncached` verbatim —
    never a second derivation) and persist it as the `CoverageSnapshot` row for the CURRENT `(asof_key,
    dataset_version)` key, upserting idempotently. Called by the ingest finalize hook (unconditionally, on
    every successful backfill/both/rebuild — including a zero-work re-run — AND, ops-hardening iter-3 B1,
    on a successful fetch/expand that the cheap `_coverage_snapshot_is_current` gate below found stale) and
    the boot warm-up safety net (only when no row exists yet for the current stamp). Returns the freshly
    persisted payload, or `None` on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns
    None only then; nothing to snapshot yet). The current stamp resolves `None`→latest, so this is
    `refresh_coverage_snapshot_for` at that resolved date (byte-identical: `_compute_coverage_uncached
    (as_of=None)` and `(as_of=latest)` both resolve through `_resolve_coverage_asof` to the SAME latest
    date)."""
    resolved_asof = _resolve_coverage_asof(session, None, cfg)
    if resolved_asof is None:
        return None
    return refresh_coverage_snapshot_for(session, cfg, resolved_asof)


def _coverage_snapshot_is_current(session: Session, cfg: Config) -> bool:
    """ops-hardening iter-3 (B1) — the cheap "already fresh" gate the fetch/expand finalize branch checks
    BEFORE ever calling `refresh_coverage_snapshot` (which would invoke the heavy `_compute_coverage_uncached`
    whole-bar-cache derivation): true iff a `CoverageSnapshot` row already exists for the CURRENT `(asof_key,
    dataset_version)` key, i.e. the persisted snapshot already reflects this exact dataset version, so a
    refresh would be redundant. Issues only the SAME cheap resolve `refresh_coverage_snapshot` itself needs
    (`_resolve_coverage_asof` — a couple of bounded scalar reads, never a table scan) plus one indexed row
    lookup — it NEVER invokes `_compute_coverage_uncached` (the zero-work fetch call-count contract, TC-2).
    A wholly-empty DB (`resolved_asof is None`) has nothing to snapshot yet — treated as "already current"
    (a no-op), mirroring `refresh_coverage_snapshot`'s own no-op contract for that case."""
    resolved_asof = _resolve_coverage_asof(session, None, cfg)
    if resolved_asof is None:
        return True
    asof_key = resolved_asof.isoformat()
    dataset_version = _membership_dataset_version(session, cfg)
    row = session.exec(
        select(CoverageSnapshot).where(
            CoverageSnapshot.asof_key == asof_key,
            CoverageSnapshot.dataset_version == dataset_version,
        )
    ).first()
    return row is not None


def _scanner_run_exists(session: Session, asof: date_cls) -> bool:
    """Whether a real `ScannerRun` snapshot exists for exactly this as-of date — the signal that `asof` is
    genuinely-ingested historical data (the app-wide as-of switcher, `GET /api/runs`, only ever offers such
    dates), not a dataless/pre-ingest as-of that must honestly serve the 'not yet computed' sentinel."""
    return session.exec(
        select(ScannerRun.asof_date).where(ScannerRun.asof_date == asof).limit(1)
    ).first() is not None


def _tag_coverage_status(
    payload: dict,
    status: str,
    *,
    stale_dataset_version: Optional[str] = None,
    stale_computed_at: Optional[str] = None,
) -> dict:
    """ops-hardening iter-27 (AG-3) — stamp the additive `coverage_status`/`stale_dataset_version`/
    `stale_computed_at` sibling fields onto an already-resolved coverage payload (never a second
    derivation of any coverage figure — every caller below passes through a payload some OTHER path
    already computed/persisted verbatim). `stale_dataset_version`/`stale_computed_at` are non-null ONLY
    when `status == "stale"`. Mutates and returns `payload` in place (each caller's `payload` is a fresh
    dict — `json.loads(...)` or a freshly-computed literal — never a shared/cached object)."""
    payload["coverage_status"] = status
    payload["stale_dataset_version"] = stale_dataset_version
    payload["stale_computed_at"] = stale_computed_at
    return payload


def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date_cls] = None) -> dict:
    """`GET /api/data`'s coverage block, served from the persisted `CoverageSnapshot` row for the resolved
    `(asof_key, dataset_version)` key — REPLACES the former request-path call to `compute_coverage`/
    `_compute_coverage_uncached` (the whole-table bar-prefill OOM/hang source, iter-24 evidence —
    `compute_coverage` itself is UNCHANGED and still used directly by the ingest finalize hook / boot
    warm-up safety net / tests that want a genuine live compute).

    Explicit-historical-as-of safety net (iter-2 review, CRITICAL): the ingest finalize hook persists a row
    for EVERY newly-created snapshot date, so the app-wide as-of switcher normally reads every selectable
    date straight from storage. If a row is nonetheless missing for an EXPLICIT `as_of` (the switcher
    selected a date — `data_overview` passes `None` for the default latest-date visit, a concrete date only
    for an explicit `?as_of=`) that is backed by a REAL `ScannerRun` (an already-ingested historical date,
    e.g. one ingested BEFORE this table existed), serve the CORRECT coverage for that date — computed once
    and persisted so the next visit is instant (self-healing) — rather than the false all-zero sentinel.
    This is an AG-3 correctness guarantee (displayed numbers MUST match the engine's computation) that
    overrides the AG-8 no-request-compute preference for this rare, deliberate, one-time-per-date path.

    ops-hardening iter-27 (AG-3 ESCALATE fix): `_membership_dataset_version` is a GLOBAL stamp bumped by
    ANY new `ScannerRun` row — including one created by a request-path historical `/backtest` create-once
    view for a date decades in the past. When that bump makes the exact-match lookup above miss, a real,
    previously-computed row for this SAME `asof_key` can still exist under the now-OLDER stamp (it
    survives only because no ingest ran since — `_upsert_coverage_snapshot` reclaims every non-current-
    stamp row at the end of every ingest). One bounded, INDEXED lookup by `asof_key` alone (never a
    `daily_prices`/`scanner_runs` scan) tried AFTER both paths above miss serves that row's figures
    labeled `coverage_status: "stale"` — honest, non-zero prior-scan figures — instead of falling through
    to the all-zero 'not yet computed' sentinel for a database that plainly has real coverage on file.
    Every returned payload now carries `coverage_status` ("current" / "stale" / "not_yet_computed") plus
    `stale_dataset_version`/`stale_computed_at` (non-null only for "stale") — additive fields, the
    pre-existing payload shape is otherwise unchanged.

    The common default (`as_of=None`) visit and a genuinely dataless as-of (no `ScannerRun`, e.g. pre-first-
    ingest) still take the honest zero-query 'not yet computed' sentinel — NEVER a live whole-table compute,
    never a blank/500 response (AG-8)."""
    resolved_asof = _resolve_coverage_asof(session, as_of, cfg)
    if resolved_asof is not None:
        asof_key = resolved_asof.isoformat()
        dataset_version = _membership_dataset_version(session, cfg)
        row = session.exec(
            select(CoverageSnapshot).where(
                CoverageSnapshot.asof_key == asof_key,
                CoverageSnapshot.dataset_version == dataset_version,
            )
        ).first()
        if row is not None:
            return _tag_coverage_status(json.loads(row.payload_json), "current")
        # no persisted row: heal an explicit switcher selection of a real already-ingested historical date
        # (see docstring) — real coverage, self-healed to storage — rather than a false empty-DB sentinel.
        if as_of is not None and _scanner_run_exists(session, resolved_asof):
            return _tag_coverage_status(refresh_coverage_snapshot_for(session, cfg, resolved_asof), "current")
        # iter-27: the exact-match key missed (current stamp) — check for a real row under an OLDER stamp
        # for this SAME asof_key before conceding to the all-zero sentinel (see docstring above).
        stale_row = session.exec(
            select(CoverageSnapshot)
            .where(CoverageSnapshot.asof_key == asof_key)
            .order_by(CoverageSnapshot.computed_at.desc())
            .limit(1)
        ).first()
        if stale_row is not None:
            return _tag_coverage_status(
                json.loads(stale_row.payload_json),
                "stale",
                stale_dataset_version=stale_row.dataset_version,
                stale_computed_at=stale_row.computed_at.isoformat(),
            )
    return _tag_coverage_status(_coverage_not_yet_computed_payload(cfg), "not_yet_computed")


def compute_availability(session: Session, config: Optional[Config] = None) -> dict:
    """J-61 — the per-trading-date availability derivation. READ-ONLY descriptive metadata over the
    SAME stored bars + stored runs `compute_coverage` reads (never a second derivation of a coverage
    figure, never a canonical score/return/bucket/setup recompute). For EVERY benchmark (SPY) trading
    day in `_trading_days` (the SAME calendar `compute_coverage` / the walk-forward use), emit:

      - `date`               — the trading day (ISO `yyyy-MM-dd`),
      - `symbols_with_bars`  — the DISTINCT count of symbols that have a bar ON THAT DATE (point-in-time,
                               NOT cumulative). A zero-bar trading day is `0` — present, never omitted as
                               if covered (honest empty-but-present).
      - `snapshot_exists`    — whether a `ScannerRun` snapshot exists for that as-of date (the SAME
                               `ScannerRun.asof_date` set `compute_coverage` reads for snapshot dates/gaps).

    Plus the descriptive header:
      - `total_symbols`      — the DISTINCT stored-symbol universe (== `compute_coverage`'s `symbol_count`,
                               all priced symbols incl. ETFs + ^VIX) — the density denominator the existing
                               coverage surfaces already use, so "3-of-158" reads against the same base.
      - `trading_day_count`  — `len(cells)` (== `compute_coverage`'s `trading_day_count`).

    Honest empty-DB behavior: an empty / bars-less DB → `cells == []`, `total_symbols == 0` (no fabricated
    cells, never a synthesized covered day). This function computes NO canonical value; it only counts +
    flags over the stored bars/runs."""
    cfg = config or get_config()
    trading_days = _trading_days(session, cfg)  # benchmark (SPY) bar dates, ascending — the SAME calendar
    # The density denominator = the DISTINCT stored-symbol universe — identical to compute_coverage's
    # `symbol_count` (all priced symbols incl. the benchmark/sector/industry ETFs + ^VIX), so the heatmap
    # "n-of-total" reads against the SAME base the coverage surfaces already show (no second universe).
    total_symbols = int(session.scalar(select(func.count(func.distinct(DailyPrice.symbol)))) or 0)

    if not trading_days:
        # Empty / bars-less DB (no benchmark calendar) → an empty-but-valid payload, no fabricated cells.
        return {"total_symbols": total_symbols, "trading_day_count": 0, "cells": []}

    # ONE grouped pass over daily_prices → {date: distinct-symbol-count-on-that-date}. Restricted to the
    # benchmark calendar (a stored bar on a non-trading date — there should be none — never invents a cell).
    cal_min, cal_max = trading_days[0], trading_days[-1]
    counts_rows = session.exec(
        select(DailyPrice.date, func.count(func.distinct(DailyPrice.symbol)))
        .where(DailyPrice.date >= cal_min)
        .where(DailyPrice.date <= cal_max)
        .group_by(DailyPrice.date)
    ).all()
    symbols_on_date: dict[date_cls, int] = {d: int(n or 0) for d, n in counts_rows}

    # The SAME snapshot/as-of date set compute_coverage reads (ScannerRun.asof_date) — no second source.
    snapshot_set = set(session.exec(select(ScannerRun.asof_date)).all())

    cells = [
        {
            "date": d.isoformat(),
            # point-in-time distinct symbols WITH a bar on d (0 for a zero-bar trading day — honest, present)
            "symbols_with_bars": symbols_on_date.get(d, 0),
            "total_symbols": total_symbols,
            # the SAME snapshot existence compute_coverage uses for snapshot-dates / gaps
            "snapshot_exists": d in snapshot_set,
        }
        for d in trading_days
    ]
    return {
        "total_symbols": total_symbols,
        "trading_day_count": len(cells),
        "cells": cells,
    }


def compute_capacity(session: Session, config: Optional[Config] = None) -> dict:
    """iter-24 fast-platform item K — the DB storage-footprint snapshot: on-disk file size + row counts
    for the three largest tables (`daily_prices` / `scanner_results` / `forward_returns`). PURE DB
    introspection over stored rows — it recomputes NO canonical score/return/bucket and reads no engine
    output; it exists purely so an operator can see the platform's current storage footprint on the Data
    Manager (goal.md fast-platform item K), served as an additive `capacity` field on the existing
    `GET /api/data` payload. `config` is accepted for the SAME uniform `(session, config=None)` signature
    every `compute_*` function here has (unused today; a natural home for a future capacity-tripwire
    threshold, per goal.md's item K). Honest all-zero snapshot on a cold/empty DB (file absent or a
    non-file bind, e.g. an in-memory test URL) — never an error."""
    db_file_bytes = 0
    try:
        database = session.get_bind().url.database
        if database:
            path = Path(database)
            if path.is_file():
                db_file_bytes = path.stat().st_size
    except Exception:
        db_file_bytes = 0  # defensive: an unresolvable bind never crashes this read-only snapshot

    return {
        "db_file_bytes": db_file_bytes,
        "daily_prices_rows": int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0),
        "scanner_results_rows": int(session.scalar(select(func.count()).select_from(ScannerResult)) or 0),
        "forward_returns_rows": int(session.scalar(select(func.count()).select_from(ForwardReturn)) or 0),
    }


# --------------------------------------------------------------------------------------------------
# J-39 — seed-safe Remove-data: the seed-vs-user-added classifier + confirm-preview + destructive
# cascade. The session's FIRST destructive data path.
#
# Boundaries (each guarding a critical anti-goal):
#   * The committed seed is UN-DELETABLE — `meta.json` per-symbol {first,last} windows are the
#     authoritative seed manifest; a `(symbol, date)` inside a window is PROTECTED and excluded from every
#     removal; a wholly-seed scope is REFUSED with an explicit reason (never a silent partial).
#   * Removal only DELETES user-added bars and cascade-removes the derived snapshot/forward-return rows
#     that depended SOLELY on them — a WHOLE-ROW delete of a derived row together with its provenance,
#     NEVER an in-place UPDATE/overwrite of a retained snapshot (the *Snapshots are immutable* identity =
#     "never overwritten in place", which a consistency-preserving whole-row delete respects). A snapshot
#     that still has ALL its underlying bars after the removal is left UNTOUCHED.
#   * Removal FABRICATES NOTHING — it only deletes; it never recomputes or invents a replacement value
#     (no scoring/scanner recompute is reachable from this path).
# --------------------------------------------------------------------------------------------------
def _read_seed_meta_rows(seed_dir: Optional[str | Path] = None) -> list[dict]:
    """The raw `symbols[]` rows from the committed-seed manifest (`<seed_dir>/meta.json`) — the ONE parse
    path `load_seed_windows` (J-39) and `load_seed_meta` (J-14) both build their views from, so there is
    never a second `json.loads(meta.json)` call anywhere. An absent/unreadable manifest yields `[]`, never
    a crash (each caller degrades honestly from there)."""
    path = Path(seed_dir or DEFAULT_SEED_DIR) / "meta.json"
    if not path.exists():
        return []
    try:
        meta = json.loads(path.read_text())
    except (ValueError, OSError):
        return []
    return meta.get("symbols") or []


def load_seed_windows(seed_dir: Optional[str | Path] = None) -> dict[str, tuple[date_cls, date_cls]]:
    """Read the committed-seed manifest (`<seed_dir>/meta.json`) into the per-symbol seed window map
    `{symbol: (first_date, last_date)}` — the authoritative seed-vs-user-added boundary J-39 reads. A
    `(symbol, date)` with `first <= date <= last` is the COMMITTED SEED (protected); a date beyond `last`
    (or a symbol absent from the manifest) is USER-ADDED (removable). An absent/unreadable manifest yields
    an empty map (so every bar is treated user-added — the safe default for a host with no committed seed
    manifest), never a crash."""
    windows: dict[str, tuple[date_cls, date_cls]] = {}
    for row in _read_seed_meta_rows(seed_dir):
        symbol = row.get("symbol")
        first = row.get("first")
        last = row.get("last")
        if symbol and first and last:
            windows[symbol] = (date_cls.fromisoformat(first), date_cls.fromisoformat(last))
    return windows


def load_seed_meta(seed_dir: Optional[str | Path] = None) -> dict[str, dict]:
    """iter-22 (J-14) — the SIBLING seed-manifest reader `indexes.compute_index_series` uses for the
    per-series data-VENDOR label + honest first-bar disclosure. Shares `load_seed_windows`'s exact parse
    (`_read_seed_meta_rows` — never a second `json.loads(meta.json)` call) but returns a per-symbol dict
    `{symbol: {"first": date|None, "last": date|None, "vendor": str|None}}`. `vendor` is the raw manifest
    key (e.g. `"stooq"`/`"yahoo"`/`"fred-macro-proxy"`) — display-label mapping is the presentation
    layer's job (`indexes._vendor_label`), not this reader's. A symbol with no vendor record in the
    manifest (e.g. the SPY/QQQ/IWM/RSP/DIA ETF lines) yields `vendor: None` — never a fabricated vendor.
    An absent/unreadable manifest yields an empty map, never a crash (mirrors `load_seed_windows`)."""
    entries: dict[str, dict] = {}
    for row in _read_seed_meta_rows(seed_dir):
        symbol = row.get("symbol")
        if not symbol:
            continue
        first = row.get("first")
        last = row.get("last")
        entries[symbol] = {
            "first": date_cls.fromisoformat(first) if first else None,
            "last": date_cls.fromisoformat(last) if last else None,
            "vendor": row.get("vendor"),
        }
    return entries


def is_seed_bar(
    symbol: str, d: date_cls, windows: dict[str, tuple[date_cls, date_cls]]
) -> bool:
    """True iff `(symbol, date)` falls inside the symbol's committed-seed window (inclusive) — i.e. it is
    COMMITTED SEED and PROTECTED from removal. A symbol absent from the manifest, or a date beyond its
    window, is user-added (removable) → False."""
    window = windows.get(symbol)
    if window is None:
        return False
    first, last = window
    return first <= d <= last


def _scope_bars(
    session: Session, symbols: Optional[list[str]], start: Optional[date_cls], end: Optional[date_cls]
) -> list[DailyPrice]:
    """The stored `DailyPrice` rows matching the removal scope (`symbols` and/or `[start, end]`). At least
    one of symbols / range must be given (an empty scope is rejected by the caller — never an accidental
    wipe). Ordered by (symbol, date) for deterministic previews."""
    stmt = select(DailyPrice)
    if symbols:
        stmt = stmt.where(DailyPrice.symbol.in_(symbols))
    if start is not None:
        stmt = stmt.where(DailyPrice.date >= start)
    if end is not None:
        stmt = stmt.where(DailyPrice.date <= end)
    stmt = stmt.order_by(DailyPrice.symbol, DailyPrice.date)
    return list(session.exec(stmt).all())


def _validate_remove_scope(
    session: Session,
    symbols: Optional[list[str]],
    start: Optional[date_cls],
    end: Optional[date_cls],
    *,
    require_range: bool = False,
) -> None:
    """Reject an invalid removal scope explicitly (the API maps the `ValueError` to a 4xx — never a silent
    no-op or accidental wipe): an empty scope (neither symbols nor a range), an inverted range
    (start > end), or an unknown symbol (named but with NO stored bars anywhere).

    J-69 — when `require_range=True` (the accident-proof destructive UI flow on `/data`) the scope is
    range-only over ALL symbols: BOTH `start` and `end` are REQUIRED and a single-ended or empty date
    scope is rejected explicitly (so a slip can never delete everything). This guard runs FIRST so a
    single-ended range is rejected before the generic empty-scope check. The internal symbol-scoped
    pull-missing path keeps `require_range=False` (its default), so it is unaffected."""
    if require_range and (start is None or end is None):
        # the destructive range-only flow: both dates mandatory (guards against accidental delete-everything).
        raise ValueError(
            "a date range removal requires BOTH a start and an end date "
            "(both From and To are mandatory)"
        )
    if not symbols and start is None and end is None:
        raise ValueError("removal scope is empty: provide symbols and/or a date range (start/end)")
    if start is not None and end is not None and start > end:
        raise ValueError(
            f"start date {start.isoformat()} must be on or before end date {end.isoformat()}"
        )
    if symbols:
        for symbol in symbols:
            exists = session.scalar(select(DailyPrice.id).where(DailyPrice.symbol == symbol).limit(1))
            if exists is None:
                raise ValueError(f"unknown symbol {symbol!r}: no stored bars to remove")


def _classify_scope(
    bars: list[DailyPrice], windows: dict[str, tuple[date_cls, date_cls]]
) -> tuple[list[DailyPrice], dict[str, int]]:
    """Split the in-scope bars into REMOVABLE (user-added) and NOT-REMOVABLE (committed seed). Returns
    `(removable_bars, not_removable_by_symbol)` where the second maps each protected symbol → its
    protected-bar count (for the preview's committed-seed breakdown). The committed seed is NEVER in the
    removable list (it is un-deletable)."""
    removable: list[DailyPrice] = []
    not_removable: dict[str, int] = {}
    for bar in bars:
        if is_seed_bar(bar.symbol, bar.date, windows):
            not_removable[bar.symbol] = not_removable.get(bar.symbol, 0) + 1
        else:
            removable.append(bar)
    return removable, not_removable


def _cascade_targets(
    session: Session, removable: list[DailyPrice]
) -> tuple[list[int], list[date_cls], int]:
    """Identify the snapshot runs whose scorecard depended SOLELY on the removable bars and so must be
    cascade-removed (whole-row, together with their children + forward returns). A `ScannerRun` D is
    invalidated iff:
      (a) any removed bar has `date <= D`  — its as-of INPUT set (bars <= D, the scoring side) shrank, OR
      (b) any of its stored `ForwardReturn` rows has `measured_date` among the removed bar dates — a
          forward-measurement bar (date > D) it was built from is gone.
    A snapshot that still has ALL its underlying bars after the removal satisfies NEITHER and is left
    UNTOUCHED. Returns `(run_ids, asof_dates, forward_return_count)` for the invalidated runs — descriptive
    only; this function recomputes NO score/return (it only reads keys to decide what whole rows to delete)."""
    if not removable:
        return [], [], 0
    removed_dates = {bar.date for bar in removable}
    max_removed = max(removed_dates)

    runs = session.exec(select(ScannerRun)).all()
    invalidated_ids: list[int] = []
    invalidated_dates: list[date_cls] = []
    for run in runs:
        # (a) an input bar (date <= D) was removed → the run's as-of dataset changed.
        input_hit = min(removed_dates) <= run.asof_date <= max_removed or any(
            d <= run.asof_date for d in removed_dates
        )
        # (b) a forward-measurement bar this run stored a return into was removed.
        forward_hit = False
        if not input_hit:
            measured = session.exec(
                select(ForwardReturn.measured_date).where(ForwardReturn.run_id == run.id)
            ).all()
            forward_hit = any(md in removed_dates for md in measured)
        if input_hit or forward_hit:
            invalidated_ids.append(run.id)
            invalidated_dates.append(run.asof_date)

    fr_count = 0
    if invalidated_ids:
        fr_count = int(
            session.scalar(
                select(func.count(ForwardReturn.id)).where(ForwardReturn.run_id.in_(invalidated_ids))
            )
            or 0
        )
    return invalidated_ids, sorted(invalidated_dates), fr_count


def _build_removal_plan(
    session: Session,
    config: Optional[Config],
    symbols: Optional[list[str]],
    start: Optional[date_cls],
    end: Optional[date_cls],
    seed_dir: Optional[str | Path],
    *,
    require_range: bool = False,
) -> dict:
    """The shared read-only analysis behind both the preview and the destructive removal: validate the
    scope, classify in-scope bars into removable (user-added) vs not-removable (committed seed), and
    determine the cascade. Returns a plan dict carrying the removable bars (objects, for the deleter), the
    committed-seed breakdown, the cascade run-ids/dates/counts, and a `refused` flag (+ reason) when the
    scope is wholly committed seed (nothing removable). This function DELETES NOTHING.

    `require_range` (J-69) enforces the accident-proof destructive range-only contract (both dates
    mandatory) — see `_validate_remove_scope`."""
    _validate_remove_scope(session, symbols, start, end, require_range=require_range)
    windows = load_seed_windows(seed_dir)
    bars = _scope_bars(session, symbols, start, end)
    removable, not_removable = _classify_scope(bars, windows)

    removable_dates = sorted({b.date for b in removable})
    removable_symbols = sorted({b.symbol for b in removable})
    not_removable_count = sum(not_removable.values())

    refused = len(removable) == 0
    reason = ""
    if refused:
        if not_removable_count > 0:
            reason = (
                "refused: every bar in this scope is committed seed — the committed seed is never "
                "deletable. Choose user-added (beyond-seed) symbols/dates."
            )
        else:
            reason = "refused: no removable bars found in this scope."

    run_ids, cascade_dates, fr_count = _cascade_targets(session, removable)

    return {
        "removable_bars": removable,  # objects — the destructive deleter consumes these
        "removable_bar_count": len(removable),
        "removable_symbol_count": len(removable_symbols),
        "removable_symbols": removable_symbols,
        "removable_first": removable_dates[0].isoformat() if removable_dates else None,
        "removable_last": removable_dates[-1].isoformat() if removable_dates else None,
        "not_removable_bar_count": not_removable_count,
        "not_removable_by_symbol": [
            {"symbol": s, "bar_count": c, "reason": "committed seed"}
            for s, c in sorted(not_removable.items())
        ],
        "cascade": {
            "run_ids": run_ids,
            "snapshot_count": len(run_ids),
            "snapshot_dates": [d.isoformat() for d in cascade_dates],
            "forward_return_count": fr_count,
        },
        "refused": refused,
        "reason": reason,
    }


def _public_plan(plan: dict) -> dict:
    """A JSON-serializable view of a removal plan WITHOUT the internal `removable_bars` objects (the
    preview/remove API surface)."""
    return {k: v for k, v in plan.items() if k != "removable_bars"}


def preview_removal(
    session: Session,
    config: Optional[Config] = None,
    *,
    symbols: Optional[list[str]] = None,
    start: Optional[date_cls] = None,
    end: Optional[date_cls] = None,
    seed_dir: Optional[str | Path] = None,
    require_range: bool = False,
) -> dict:
    """READ-ONLY confirm-preview for a removal scope (J-39): returns exactly what WOULD be removed —
    removable `(symbol, date)` bar count + range + symbols, the not-removable committed-seed breakdown
    (per symbol, reason `"committed seed"`), and the cascade of dependent snapshot/forward-return rows —
    DELETING NOTHING (the DB is byte-unchanged afterward). A wholly-committed-seed scope returns
    `refused=True` with an explicit reason. Raises `ValueError` for an empty/inverted/unknown scope (the
    API maps it to 4xx).

    `require_range` (J-69): when True (the destructive UI flow) BOTH `start` and `end` are mandatory and a
    single-ended/empty date scope is rejected with an explicit `ValueError` (→ 4xx)."""
    plan = _build_removal_plan(
        session, config, symbols, start, end, seed_dir, require_range=require_range
    )
    return _public_plan(plan)


def _record_removal_run(engine: Engine, cfg: Config, plan: dict) -> None:
    """Record the removal as its own append-only `DataProviderRun` audit entry (own session; INSERT only —
    the audit trail is the permanent record and is NEVER deleted). Structured detail (kind `remove`, the
    scope, removed counts, and the cascade) is JSON-encoded in `message`, exactly like a fetch/backfill run."""
    detail = {
        "kind": "remove",
        "removed_bar_count": plan["removable_bar_count"],
        "removed_symbol_count": plan["removable_symbol_count"],
        "removed_first": plan["removable_first"],
        "removed_last": plan["removable_last"],
        "not_removable_bar_count": plan["not_removable_bar_count"],
        "cascade": plan["cascade"],
        "summary": (
            f"removed {plan['removable_bar_count']} user-added bars "
            f"({plan['removable_symbol_count']} symbols); cascade-removed "
            f"{plan['cascade']['snapshot_count']} snapshots + "
            f"{plan['cascade']['forward_return_count']} forward returns"
        ),
    }
    with Session(engine) as session:
        session.add(
            DataProviderRun(
                provider=cfg.provider,
                started_at=_utcnow(),
                finished_at=_utcnow(),
                symbols_ok=plan["removable_symbol_count"],
                symbols_failed=0,
                status="ok",
                message=json.dumps(detail),
            )
        )
        session.commit()


def remove_data(
    session: Session,
    config: Optional[Config] = None,
    *,
    symbols: Optional[list[str]] = None,
    start: Optional[date_cls] = None,
    end: Optional[date_cls] = None,
    seed_dir: Optional[str | Path] = None,
    engine: Optional[Engine] = None,
    require_range: bool = False,
) -> dict:
    """DESTRUCTIVE, seed-safe, cascade-consistent removal (J-39). Deletes ONLY the user-added `DailyPrice`
    rows in scope (whole-row deletes — the committed seed is excluded and un-deletable) and cascade-removes
    the derived snapshot rows (`ScannerRun` + its `ScannerResult` / `SectorScoreRow` / `ThemeScoreRow`
    children) and `ForwardReturn` rows that depended SOLELY on the removed bars — a WHOLE-ROW delete of
    each derived row, NEVER an in-place overwrite of a retained snapshot (so the *Snapshots are immutable*
    identity holds: a fully-covered snapshot is left UNTOUCHED). It FABRICATES NOTHING and never recomputes
    a score/return — it only deletes. The removal is recorded on the append-only `DataProviderRun` audit
    log (the audit trail is NOT deleted). A wholly-committed-seed scope is REFUSED (`ValueError`); raises
    `ValueError` for an empty/inverted/unknown scope too (the API maps these to 4xx).

    `require_range` (J-69): when True (the destructive UI flow) BOTH `start` and `end` are mandatory and a
    single-ended/empty date scope is rejected with an explicit `ValueError` (→ 4xx) — the accident-proof
    range-only contract."""
    cfg = config or get_config()
    plan = _build_removal_plan(session, cfg, symbols, start, end, seed_dir, require_range=require_range)
    if plan["refused"]:
        raise ValueError(plan["reason"])

    run_ids: list[int] = plan["cascade"]["run_ids"]
    # 1) cascade-remove the dependent snapshot children + forward returns + runs (whole-row deletes only).
    if run_ids:
        session.execute(delete(ForwardReturn).where(ForwardReturn.run_id.in_(run_ids)))
        session.execute(delete(ScannerResult).where(ScannerResult.run_id.in_(run_ids)))
        session.execute(delete(SectorScoreRow).where(SectorScoreRow.run_id.in_(run_ids)))
        session.execute(delete(ThemeScoreRow).where(ThemeScoreRow.run_id.in_(run_ids)))
        session.execute(delete(ScannerRun).where(ScannerRun.id.in_(run_ids)))

    # 2) delete the user-added bars themselves (by exact id — the committed seed is never in this list).
    bar_ids = [bar.id for bar in plan["removable_bars"]]
    if bar_ids:
        session.execute(delete(DailyPrice).where(DailyPrice.id.in_(bar_ids)))

    # 3) defensive consistency sweep: drop ANY remaining forward-return row that still references a removed
    #    bar (by measured_date) — guarantees "no remaining row references an absent bar" even if a future
    #    cascade predicate change missed a case. With the predicate above this set is already empty.
    removed_dates = {bar.date for bar in plan["removable_bars"]}
    if removed_dates:
        session.execute(
            delete(ForwardReturn).where(ForwardReturn.measured_date.in_(list(removed_dates)))
        )

    session.commit()

    # 4) record the removal on the append-only audit log (own session — never deleted).
    eng = engine or get_engine()
    _record_removal_run(eng, cfg, plan)

    result = _public_plan(plan)
    result["removed_bar_count"] = plan["removable_bar_count"]  # explicit done-count alias
    return result


# --------------------------------------------------------------------------------------------------
# J-85 — confirm-gated regenerate-from-scratch snapshot rebuild: CLEAR the entire snapshot set then
# CREATE-ONCE recompute every covered trading date over the resolved universe. The committed PRICE seed
# is NEVER deleted; no canonical formula changes (only the membership scanned over). It is a wholesale
# rebuild (every snapshot is cleared then recomputed deterministically) — never an in-place UPDATE of a
# live snapshot row (anti-goal: Snapshots are immutable; a wholesale create-once rebuild is permitted).
# --------------------------------------------------------------------------------------------------
def clear_snapshot_set(session: Session) -> dict:
    """DELETE every row of the scanner snapshot layer (whole-row deletes only) so the subsequent backfill
    recomputes the entire set FROM SCRATCH over the current resolved universe (J-85). Clears
    `forward_returns` → `scanner_results` / `sector_scores` / `theme_scores` → `scanner_runs` (children
    before parents). It NEVER touches `daily_prices` (the committed PRICE seed is un-deletable — this
    function does not even reference it) and NEVER an in-place UPDATE (whole-row deletes only). Returns
    `{runs_cleared, bars_before, bars_after}` so the caller can ASSERT the price seed was untouched
    (`bars_before == bars_after`) — a hard guarantee the rebuild refuses to delete the committed seed.
    The orphaned-run boot sweep / append-only run-history audit are unaffected (different tables)."""
    bars_before = int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)
    runs_cleared = int(session.scalar(select(func.count()).select_from(ScannerRun)) or 0)
    # children first (FK order), then the parent runs. Whole-row deletes; the price seed is never referenced.
    session.execute(delete(ForwardReturn))
    session.execute(delete(ScannerResult))
    session.execute(delete(SectorScoreRow))
    session.execute(delete(ThemeScoreRow))
    session.execute(delete(ScannerRun))
    session.commit()
    bars_after = int(session.scalar(select(func.count()).select_from(DailyPrice)) or 0)
    # hard seed-safety invariant: the rebuild's clear step MUST leave the committed price seed intact.
    if bars_after != bars_before:
        raise RuntimeError(
            f"rebuild clear corrupted the price seed: {bars_before} bars before, {bars_after} after"
        )
    return {"runs_cleared": runs_cleared, "bars_before": bars_before, "bars_after": bars_after}


# --------------------------------------------------------------------------------------------------
# Import provider catalog + env-detected availability (J-33) — descriptive metadata, NO key value
# --------------------------------------------------------------------------------------------------
# iter-26: the deterministic, OFFLINE `seed` import source — the browser-capture enabler for the
# defining J-37 pull / J-35 expand multi-step flows. It is a TEST/DEV affordance only: exposed in the
# import-source picker and accepted by the job-source validator ONLY when the env flag below is set
# (off by default, NEVER in the committed `config.yaml` `data_manager.providers` catalog, NEVER in
# production). It serves the REAL committed seed bars through the EXISTING J-34 chunked engine +
# `screen_reasons` predicate (NO second fetch path, NO second screen rule) — so it serves real data,
# never request-time-fabricated prices (anti-goals *No fabricated data* / *Live fetch is real-data-only*
# preserved). `make_provider("seed", ...)` already resolves it to `SeedProvider` (no change there).
SEED_IMPORT_SOURCE_ID = "seed"
SEED_IMPORT_ENV_FLAG = "TRENDORA_ENABLE_SEED_IMPORT_SOURCE"


def seed_import_source_enabled() -> bool:
    """True when the env-gated offline `seed` import source is enabled (the env flag is set to a non-empty
    value). Off by default — the `seed` source is a test/dev harness affordance, never selectable in
    production. Read at REQUEST time (like `compute_provider_availability`) so the QA harness can toggle
    it per process without a config edit."""
    return bool(os.environ.get(SEED_IMPORT_ENV_FLAG))


def _seed_import_entry() -> ProviderCatalogEntry:
    """The single in-memory catalog entry for the env-gated offline `seed` import source. Built in ONE
    place so the availability list and the job-source validator agree on its shape. It is a no-key,
    market-cap-capable, always-available source serving committed seed bars — it carries NO key and NO
    env-var (the seed reads no credential)."""
    return ProviderCatalogEntry(
        id=SEED_IMPORT_SOURCE_ID,
        label="Seed (offline test data)",
        needs_key=False,
        env_var=None,
        supports_market_cap=True,
    )


def seed_import_overlay_dir() -> Optional[Path]:
    """The throwaway OVERLAY seed dir for the env-gated `seed` import source (set by the QA harness via
    `TRENDORA_SEED_IMPORT_DIR`), or None. When set, a `seed`-source EXPAND writes its grown universe.json /
    per-symbol CSVs / meta.json HERE — never the committed `data/seed/` tree (so an offline J-35 capture
    never mutates the committed seed). Only honored while the seed import source is enabled."""
    if not seed_import_source_enabled():
        return None
    raw = os.environ.get("TRENDORA_SEED_IMPORT_DIR")
    return Path(raw) if raw else None


def _expand_seed_dir_for_source(source: Optional[str]) -> Optional[Path]:
    """For a `seed`-source expand, the artifact write-dir is the throwaway overlay (never the committed
    seed); for any other source it is None (the default committed `DEFAULT_SEED_DIR` is used as before —
    the committed-universe-grow behavior is unchanged for real providers)."""
    if source == SEED_IMPORT_SOURCE_ID:
        return seed_import_overlay_dir()
    return None


def _provider_entry_with_seed(cfg: Config, source_id: str) -> Optional[ProviderCatalogEntry]:
    """Resolve a job `source` id to its catalog entry, transparently including the env-gated offline
    `seed` source (which is deliberately absent from the committed `config.yaml` catalog). Returns the
    config catalog entry when `source_id` is a real provider; the in-memory seed entry when `source_id`
    is `seed` AND the env flag is set; else None (an unknown source — the validator rejects it)."""
    entry = cfg.data_manager.provider_by_id(source_id)
    if entry is not None:
        return entry
    if source_id == SEED_IMPORT_SOURCE_ID and seed_import_source_enabled():
        return _seed_import_entry()
    return None


def resolve_provider_key(entry: ProviderCatalogEntry, pasted_key: Optional[str]) -> Optional[str]:
    """The effective credential for one import source: the SESSION-ONLY pasted key if present, else the
    value of the source's configured environment variable (by NAME). Returns None when the source needs
    no key, or when neither a pasted nor an env key is available. The result is used in-memory only
    (request-scoped) and is NEVER persisted/logged (anti-goal: Import keys are env-or-session, never
    persisted). A no-key source returns None and ignores any pasted value."""
    if not entry.needs_key:
        return None
    if pasted_key:
        return pasted_key
    return os.environ.get(entry.env_var) if entry.env_var else None


def compute_provider_availability(config: Optional[Config] = None) -> list[dict]:
    """The import-source catalog with per-source availability, computed from config + the environment at
    REQUEST time (J-33). For each catalog entry: `available = (not needs_key) or the env var is set`. The
    output carries ONLY the env-var NAME, the boolean requirement/availability, and a human `reason` — it
    NEVER contains the env value or any key (anti-goal: Import keys are env-or-session, never persisted).
    This is descriptive availability metadata — NOT a duplicate of any canonical score/return/bucket."""
    cfg = config or get_config()
    sources: list[dict] = []
    catalog = list(cfg.data_manager.providers)
    # iter-26: append the env-gated offline `seed` source ONLY when the flag is set (off by default,
    # absent from the committed catalog). It is a no-key, always-available, market-cap-capable test/dev
    # source — descriptive metadata only, NO key value (anti-goal: keys are env-or-session, never
    # persisted). It serves committed seed bars through the existing engine — no second serving path.
    if seed_import_source_enabled():
        catalog = catalog + [_seed_import_entry()]
    for entry in catalog:
        available = (not entry.needs_key) or bool(entry.env_var and os.environ.get(entry.env_var))
        if not entry.needs_key:
            reason = "no key required"
        elif available:
            reason = f"key present in ${entry.env_var}"
        else:
            reason = f"set ${entry.env_var} or paste a session key"
        sources.append({
            "id": entry.id,
            "label": entry.label,
            "needs_key": entry.needs_key,
            "env_var": entry.env_var,
            "supports_market_cap": entry.supports_market_cap,
            "available": available,
            "reason": reason,
        })
    return sources


def compute_macro_availability(session: Session, config: Optional[Config] = None) -> dict:
    """The OPTIONAL FRED macro feed's read-only catalog + availability for the Data Manager (J-92). Reports
    the macro provider's env-detected availability (the FRED key is read from `config.macro.env_var` — the
    NAME only, NEVER the value), the per-leg config-default-OFF enable flags, and each configured series'
    COMMITTED-SEED coverage (a count of `macro_series` rows + an honest blocked/unavailable NA state when a
    series has no rows — a walled/uncommitted series, never a fabricated value). The output carries ONLY the
    env-var NAME + a boolean + counts/labels — NEVER any key value (anti-goal: keys are env-or-session,
    never persisted). Descriptive availability metadata — NOT a canonical score/return/bucket."""
    cfg = config or get_config()
    macro = cfg.macro
    key_present = bool(macro.env_var and os.environ.get(macro.env_var))
    series_rows: list[dict] = []
    for s in macro.series:
        count = int(
            session.scalar(
                select(func.count()).select_from(MacroSeries).where(MacroSeries.symbol == s.id)
            )
            or 0
        )
        series_rows.append({
            "id": s.id,
            "label": s.label,
            "fred_series_id": s.fred_series_id,
            "publication_lag_days": s.publication_lag_days,
            "proxy_symbol": s.proxy_symbol,
            "committed_rows": count,
            # honest blocked/unavailable when no committed rows AND no live key (a walled/uncommitted
            # series) — never a fabricated value. With committed seed rows the series is available offline.
            "available": count > 0,
            "reason": (
                f"{count} committed seed observations"
                if count > 0
                else (
                    f"no committed seed; live pull needs ${macro.env_var}"
                    if not key_present
                    else f"no committed seed; live pull available via ${macro.env_var}"
                )
            ),
        })
    return {
        "provider": "fred",
        "label": "FRED (macro feed)",
        "env_var": macro.env_var,  # the NAME only — never a key value
        "live_available": key_present,
        "enable": {
            "severity": macro.enable.severity,
            "regime_switching": macro.enable.regime_switching,
            "study": macro.enable.study,
        },
        "series": series_rows,
        "publication_lag_note": (
            "Macro inputs are optional and config-default-OFF, so default figures are unchanged. A macro "
            "value is used for a date only once published (publication-lag aligned, published_date ≤ D) — "
            "never the reference-date value. A walled or uncommitted series is shown as NA, never fabricated."
        ),
    }


# --------------------------------------------------------------------------------------------------
# In-memory job registry (live progress) — the FINAL summary is persisted to DataProviderRun
# --------------------------------------------------------------------------------------------------
@dataclass
class JobProgress:
    """Live progress for one fetch/backfill job (in-memory; the API polls `to_dict()`)."""

    job_id: str
    kind: str
    start: date_cls
    end: date_cls
    # The chosen import `source` id (J-33) — NOT secret; recorded so the run history shows which provider
    # a fetch used. The pasted `api_key` is DELIBERATELY ABSENT from this in-memory record (and from the
    # persisted run / detail JSON / logs) — it is request-only (anti-goal: keys are env-or-session, never
    # persisted). Defaults to None for a backfill-only job (no fetch ⇒ no source).
    source: Optional[str] = None
    status: str = "running"  # running | ok | partial | failed | resumable (J-34: a rate-limited pause)
    symbols_total: int = 0
    symbols_ok: int = 0
    symbols_failed: int = 0
    bars_fetched: int = 0
    # J-66: a thread-safe set of DISTINCT symbols that have completed (ok). The fetch progress counter
    # ticks at per-SYMBOL granularity by recording each completed symbol HERE, and `symbols_ok` is derived
    # as `len(symbols_done)` so a symbol fetched across MULTIPLE date-windows is counted ONCE — fixing the
    # observed `318/159` reading (a counter that exceeded its distinct-symbol total). NOT serialized
    # directly (the derived `symbols_ok` is). Mutated only on the orchestrating thread (workers return
    # results; the orchestrator records completions), so the set itself needs no lock.
    symbols_done: set[str] = field(default_factory=set)
    # J-66: the DISTINCT set of symbols that failed. `symbols_failed` is derived as the count of failed
    # symbols that never later succeeded (`symbols_failed_set - symbols_done`), so a symbol failing across
    # windows counts ONCE and one that fails-then-succeeds is OK — the failed counter likewise never
    # exceeds the distinct-symbol total. Mutated only on the orchestrating thread.
    symbols_failed_set: set[str] = field(default_factory=set)
    dates_total: int = 0
    dates_done: int = 0
    snapshots_created: int = 0
    forward_returns_inserted: int = 0
    # ops-hardening iter-1 (J-01/J-03) — the backfill/both/rebuild run-summary exclusion breakdown,
    # computed ONCE by `_do_backfill` and carried on both the live progress (`to_dict()`) and the
    # persisted run detail (`_run_detail()`): a single computation, two servings, never a second
    # derivation. `dates_total` above is REDEFINED this iteration to mean "trading days in the
    # REQUESTED range" (was: the post-cadence/already-snapshotted-filtered target count).
    # `calendar_days` is the inclusive calendar span of [start, end]; `non_trading_days` is calendar
    # days in range that are not trading days; `already_snapshotted` is trading days in range that
    # already had a snapshot before this run started; `error_other` mirrors `len(date_failures)`. All
    # 0 for a fetch/expand-only job (no backfill stage ran). Invariants (enforced by construction for
    # backfill/both, whose cadence gate is bypassed — see `_do_backfill`):
    # `non_trading_days + dates_total == calendar_days`;
    # `snapshots_created + already_snapshotted + error_other == dates_total`.
    calendar_days: int = 0
    non_trading_days: int = 0
    already_snapshotted: int = 0
    error_other: int = 0
    # ops-hardening iter-2 (J-05) — the ingest finalize hook's inputs/output. `new_snapshot_dates` is
    # INTERNAL scratch (not serialized, like `_backfill_per_date_seconds_sum` below): the dates THIS run's
    # `_do_backfill` genuinely persisted a NEW `ScannerRun` for (populated in `_persist()` exactly where it
    # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
    # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
    # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
    # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
    # "index_series"]` it actually refreshed — empty/default until the hook has actually run (never
    # fabricated on an interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc.
    # already are).
    new_snapshot_dates: list[date_cls] = field(default_factory=list)
    aggregates_refreshed: list[str] = field(default_factory=list)
    # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
    # checkpoint's resume point); `chunk_total` = the deterministic plan size (symbol-batches × date-
    # windows). Both 0 for a non-chunked job (e.g. backfill-only) so the UI hides the chunk indicator.
    chunk_index: int = 0
    chunk_total: int = 0
    # J-35 expand: the screen result. `passers` = candidates that PASSED the config screen (became
    # universe members); `omitted` = a BOUNDED list of {symbol, reason} for candidates omitted (threshold-
    # failed / no_market_cap / fetch_failed / empty_series) — never fabricated. `omitted_total` is the
    # EXACT omitted count (the list is capped at `_MAX_OMITTED_SAMPLES`). All 0/empty for a non-expand job.
    passers: int = 0
    omitted_total: int = 0
    omitted: list[dict] = field(default_factory=list)
    # J-53: per-stage operational timings, recorded ONCE by the job runner per EXECUTED stage. Each
    # entry is descriptive operational metadata (NOT a canonical score) — a stage that never ran is
    # ABSENT from this dict (never a fabricated zero). The backfill entry additionally carries
    # `per_date_seconds_sum` (the sum of each date's compute time), so the job's OWN payload evidences
    # the >=~2x speedup (parallel wall-clock `elapsed_seconds` vs the sequential `per_date_seconds_sum`).
    #   fetch:    {elapsed_seconds, items_processed (symbols ok+failed), concurrency}
    #   backfill: {elapsed_seconds, items_processed (dates done), concurrency, per_date_seconds_sum}
    stages: dict[str, dict] = field(default_factory=dict)
    # J-66: a CURRENT-ACTIVITY line naming what the job is working on RIGHT NOW (the symbol/chunk during
    # fetch, the date being scanned during backfill — e.g. "scanning 2021-03-11 (12/22)") and a
    # LAST-PROGRESS HEARTBEAT timestamp (the UI renders "updated Ns ago"), so a slow-but-alive job is
    # visually distinguishable from a stalled one. Honest descriptive metadata — never fabricated. The
    # heartbeat is stamped on every progress mutation via `_tick`.
    current_activity: str = ""
    last_progress_at: datetime = field(default_factory=_utcnow)
    # J-59: the set of COMPLETED pipeline stages (fetch / screen / backfill), mirrored to the durable
    # checkpoint's `completed_stages_json` so a Resume can route straight to the backfill stage with ZERO
    # provider calls. Seeded from the checkpoint on a resume.
    completed_stages: list[str] = field(default_factory=list)
    message: str = ""
    errors: list[str] = field(default_factory=list)
    # J-67: per-date backfill failures — the dates that failed (with their honest error) while the rest
    # completed, so a multi-date backfill ends `partial` with the per-date detail instead of aborting the
    # whole stage. Each entry is {date, error}. Empty for a clean run. Never a fabricated snapshot.
    date_failures: list[dict] = field(default_factory=list)
    # ops-hardening iter-1 (J-01) — the UNCAPPED count of per-date backfill failures. `date_failures`
    # above is a BOUNDED sample list (capped at `_MAX_ERROR_SAMPLES`), so `len()` of it undercounts once
    # more than 20 dates fail. `error_other` is derived from THIS total (never from the sample `len()`),
    # so the exclusion-breakdown invariant `snapshots_created + already_snapshotted + error_other ==
    # dates_total` stays EXACT even on a large backfill with many failures — mirroring the existing
    # `omitted` (bounded sample) / `omitted_total` (unconditional total) precedent. 0 for a clean run.
    date_failures_total: int = 0
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None
    # J-53 backfill-stage scratch (NOT serialized — internal accumulators the orchestrator fills during
    # the backfill, read once by `_run_job` to `record_stage("backfill", ...)`): the sum of each date's
    # per-date compute seconds (the sequential baseline the parallel wall-clock beats) and the actual
    # concurrency the pool used (min(config workers, target dates)).
    _backfill_per_date_seconds_sum: float = 0.0
    _backfill_concurrency: int = 0
    # ops-hardening iter-37 (J-07 closure) — the ONE prefilled `_BarCache` `_do_backfill` builds for the
    # whole job (NOT serialized — internal scratch, like the two accumulators above): stashed here instead
    # of being dropped/released the moment `_do_backfill` returns, so the ingest finalize hook's per-date
    # coverage warm (`_persist_per_date_coverage_snapshots`) can ATTACH the SAME already-loaded cache
    # (`attach_shared_cache`) instead of opening a SECOND independent whole-table `daily_prices` load for
    # the same job. None until `_do_backfill` populates it on a successful run with >= 1 in-range target
    # (a fetch/expand-only job, or a backfill with no targets, never sets it — nothing to share; a whole-
    # stage `_do_backfill` failure releases it immediately instead of stashing it — see `_do_backfill`).
    # The finalize hook nulls this out immediately before releasing it back to the OS
    # (`_release_process_memory`) so `gc.collect()` can actually reclaim it — a lingering reference here
    # would defeat that release entirely (iter-27's "second consecutive rebuild starts lean" guarantee).
    _shared_bar_cache: Optional["_BarCache"] = None
    # ops-hardening iter-9 (F1 / J-04 step 6) — `time.monotonic()` of the last durable progress checkpoint
    # written onto this job's OPEN run-history row (NOT serialized — internal throttle scratch, like the
    # two accumulators above). 0.0 means "never checkpointed", so the first advance always writes.
    _last_checkpoint_monotonic: float = 0.0
    # ops-hardening iter-41 (D9, dev Known Issue #2 from iter-40's own handoff) — dates completed since
    # the last durable checkpoint write (NOT serialized — internal throttle scratch, like
    # `_last_checkpoint_monotonic` above). The time-based throttle alone (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`)
    # lets an extremely fast per-date compute (iter-40's live drill observed ~120-140 ms/date bursts) run
    # several dates between checkpoints; this count-based floor (see `_RUN_RECORD_CHECKPOINT_DATE_FLOOR`)
    # forces a write on every Kth date regardless of elapsed time, bounding the OTHER axis of staleness.
    _dates_since_checkpoint: int = 0

    def tick(self, activity: Optional[str] = None) -> None:
        """J-66 — stamp the last-progress HEARTBEAT (and optionally the current-activity line) on a
        progress advance. Called on the orchestrating thread whenever a unit of work completes (a symbol
        fetched, a date backfilled), so the UI's "updated Ns ago" reflects real liveness. Honest metadata
        only — never a fabricated timestamp."""
        self.last_progress_at = _utcnow()
        if activity is not None:
            self.current_activity = activity

    def _recount_symbols(self) -> None:
        """Derive the distinct ok / failed counters from the dedup sets (J-66): a symbol that EVER
        succeeded counts ok (and is removed from the failed tally), so neither counter exceeds the
        distinct-symbol total and a fail-then-succeed across windows is honestly OK."""
        self.symbols_ok = len(self.symbols_done)
        self.symbols_failed = len(self.symbols_failed_set - self.symbols_done)

    def mark_symbol_done(self, symbol: str) -> None:
        """J-66 — record ONE symbol as completed at per-SYMBOL granularity, deduped across date-windows so
        the same symbol fetched in multiple windows counts ONCE. `symbols_ok` is derived as the distinct
        count, so the symbols counter can NEVER exceed `symbols_total` (the distinct-symbol plan size) —
        fixing the observed `318/159`. Stamps the heartbeat + current-activity line."""
        self.symbols_done.add(symbol)
        self._recount_symbols()
        self.tick(f"fetched {symbol} ({self.symbols_ok}/{self.symbols_total} symbols)")

    def mark_symbol_failed(self, symbol: str) -> None:
        """J-66 — record ONE symbol as failed (distinct-deduped across windows). Stamps the heartbeat."""
        self.symbols_failed_set.add(symbol)
        self._recount_symbols()
        self.tick(f"failed {symbol}")

    def complete_stage(self, stage: str) -> None:
        """J-59 — mark a pipeline stage (fetch / screen / backfill) COMPLETED on the live job (mirrored to
        the durable checkpoint so a Resume can skip a completed fetch entirely — zero provider calls)."""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)

    def record_stage(
        self,
        stage: str,
        *,
        elapsed_seconds: float,
        items_processed: int,
        concurrency: int,
        per_date_seconds_sum: Optional[float] = None,
        speedup_factor: Optional[float] = None,
    ) -> None:
        """Record one EXECUTED stage's honest timings ONCE (J-53). Called by the job runner on the
        orchestrating thread after a stage finishes (or, for a paused/failed stage, with the honest
        partial figures for the portion that ran). `elapsed_seconds` is wall-clock; `items_processed`
        is symbols (fetch) or dates (backfill); `concurrency` is the config pool size actually used.
        `per_date_seconds_sum` (backfill only) is the sequential per-date baseline the parallel
        wall-clock beats. A stage is only ever recorded when it actually ran — never fabricated."""
        entry: dict = {
            "elapsed_seconds": round(float(elapsed_seconds), 4),
            "items_processed": int(items_processed),
            "concurrency": int(concurrency),
        }
        if per_date_seconds_sum is not None:
            entry["per_date_seconds_sum"] = round(float(per_date_seconds_sum), 4)
            # J-66: compute the backfill SPEEDUP figure SERVER-SIDE (the sequential per-date sum divided
            # by the parallel wall-clock) and carry it in the stages payload so the frontend only
            # re-formats it — clearing the iter-8 coherence-WARN residual (no client-side division).
            # Honest NA (None) when either figure is missing/zero — never a fabricated ratio. Use the
            # explicit override when given, else derive from the two timings.
            entry["speedup_factor"] = _compute_speedup(
                per_date_seconds_sum if speedup_factor is None else None,
                elapsed_seconds if speedup_factor is None else None,
                override=speedup_factor,
            )
        elif speedup_factor is not None:
            entry["speedup_factor"] = round(float(speedup_factor), 4)
        self.stages[stage] = entry

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "source": self.source,  # the chosen import provider id (not secret); never the key
            "status": self.status,
            "symbols_total": self.symbols_total,
            "symbols_ok": self.symbols_ok,
            "symbols_failed": self.symbols_failed,
            "bars_fetched": self.bars_fetched,
            "dates_total": self.dates_total,
            "dates_done": self.dates_done,
            "snapshots_created": self.snapshots_created,
            "forward_returns_inserted": self.forward_returns_inserted,
            # ops-hardening iter-1: the live exclusion breakdown (0 for a fetch/expand-only job — see
            # the JobProgress field docstring above).
            "calendar_days": self.calendar_days,
            "non_trading_days": self.non_trading_days,
            "already_snapshotted": self.already_snapshotted,
            "error_other": self.error_other,
            # ops-hardening iter-2 (J-05): the live job's finalize-hook output so far — empty while running/
            # before the hook has run (honest; never fabricated), populated once the finalize hook completes
            # (mirrors how the OTHER live fields above simply read the current in-memory value).
            "aggregates_refreshed": list(self.aggregates_refreshed),
            "chunk_index": self.chunk_index,  # J-34: completed chunks (== checkpoint resume point)
            "chunk_total": self.chunk_total,  # J-34: total planned chunks
            "passers": self.passers,  # J-35: candidates that passed the screen (became members)
            "omitted_total": self.omitted_total,  # J-35: exact omitted count (the list below is bounded)
            "omitted": list(self.omitted),  # J-35: bounded [{symbol, reason}] — never fabricated
            # J-53: per-stage operational timings (fetch / backfill: elapsed, items, concurrency; backfill
            # also per_date_seconds_sum + the J-66 server-computed speedup_factor) — only stages that
            # actually RAN appear; absent = never ran (NA).
            "stages": {k: dict(v) for k, v in self.stages.items()},
            # J-66: fine-grained, honest live-progress fields. `current_activity` names what is being worked
            # on right now; `last_progress_at` is the heartbeat (the UI renders "updated Ns ago"). Both are
            # honest descriptive metadata — never fabricated.
            "current_activity": self.current_activity,
            "last_progress_at": self.last_progress_at.isoformat() if self.last_progress_at else None,
            # J-59: the completed pipeline stages (so the UI can render "failed at backfill — resumable
            # from the backfill stage" and the resume routes correctly).
            "completed_stages": list(self.completed_stages),
            # J-67: per-date backfill failures (honest error + which dates) on a `partial` job.
            "date_failures": [dict(f) for f in self.date_failures],
            "message": self.message,
            "errors": list(self.errors),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


_JOBS: dict[str, JobProgress] = {}
_LOCK = threading.Lock()


def create_job(kind: str, start: date_cls, end: date_cls, source: Optional[str] = None) -> JobProgress:
    """Register a new `running` job in the in-memory registry and return it (with a fresh job_id). The
    optional `source` is the chosen import provider id (J-33; not secret) — the pasted key is NEVER
    stored on the job, only threaded to the worker as a request-only argument."""
    job = JobProgress(job_id=uuid.uuid4().hex, kind=kind, start=start, end=end, source=source)
    with _LOCK:
        _JOBS[job.job_id] = job
    return job


def get_job(job_id: str) -> Optional[dict]:
    """A serializable snapshot of a job's live progress, or None for an unknown id."""
    with _LOCK:
        job = _JOBS.get(job_id)
    return job.to_dict() if job is not None else None


def validate_job_request(
    kind: str,
    start: date_cls,
    end: date_cls,
    config: Optional[Config] = None,
    *,
    source: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """Reject an invalid job request explicitly (the API maps the raised `ValueError` to a 4xx — never a
    silent no-op): an unknown kind, an inverted range (start > end), an unknown import `source`, or a
    fetch against a `needs_key` source with neither an env key nor a pasted session key. Malformed dates
    are rejected earlier by the typed API model. `source`/`api_key` are validated only when a `source` is
    supplied; the key is read request-only for the gate and is never persisted (anti-goal: keys are
    env-or-session, never persisted).

    ops-hardening iter-1 (J-03): there is NO range-span cap here (or anywhere) — an explicit request of
    any span is accepted; `_do_backfill`'s date-window chunking (`import_chunking.date_window_days`) is
    the safety mechanism for an unbounded span, never a request-time rejection."""
    cfg = config or get_config()
    if kind not in JOB_KINDS:
        raise ValueError(f"unknown job kind {kind!r}; expected one of {list(JOB_KINDS)}")
    # J-85: a rebuild ignores the supplied date range entirely — it CLEARS then create-once recomputes the
    # snapshot set over EVERY covered trading day (the full calendar by design), reading the committed seed
    # offline (no source/key). So it bypasses the range-span + source/key gates below; only the
    # unknown-kind guard above applies. The endpoint still passes the latest data date as start==end.
    if kind in _REBUILD_KINDS:
        return
    if start > end:
        raise ValueError(f"start date {start.isoformat()} must be on or before end date {end.isoformat()}")
    # A job that FETCHES over the network = a generic fetch OR an expand (which fetches OHLCV + a cap).
    fetches = kind in _FETCH_KINDS or kind in _EXPAND_KINDS
    if source is not None:
        # Resolve through the seed-aware helper so the env-gated offline `seed` source (absent from the
        # committed catalog) is accepted ONLY when its env flag is set — mirroring the same gate the
        # availability list uses. No second fetch/screen path: a `seed` job routes through the existing
        # engine + `screen_reasons` predicate exactly like any other source.
        entry = _provider_entry_with_seed(cfg, source)
        if entry is None:
            raise ValueError(
                f"unknown import source {source!r}; expected one of {cfg.data_manager.provider_ids()}"
            )
        # J-35 eligibility gate: an expand job MUST use a market-cap-capable source — a provider that
        # cannot supply the cap the screen gates on is rejected EXPLICITLY (never a silent no-op, never a
        # fabricated cap). Reuses the config `supports_market_cap` flag (no hardcoded provider list).
        if kind in _EXPAND_KINDS and not entry.supports_market_cap:
            raise ValueError(
                f"source {source!r} cannot supply market cap — not selectable for an expand job "
                f"(eligible sources: {sorted(p.id for p in cfg.data_manager.providers if p.supports_market_cap)})"
            )
        # A key is only required for a job that actually FETCHES (backfill reads the committed seed).
        if fetches and entry.needs_key and not resolve_provider_key(entry, api_key):
            raise ValueError(
                f"source {source!r} requires a key; set ${entry.env_var} or paste a session key"
            )


# --------------------------------------------------------------------------------------------------
# Job execution — fetch (live, real-data-only) and backfill (offline, create-once orchestration)
# --------------------------------------------------------------------------------------------------
def _record_error(prog: JobProgress, message: str) -> None:
    if len(prog.errors) < _MAX_ERROR_SAMPLES:
        prog.errors.append(message)


def _record_omitted(prog: JobProgress, symbol: str, reason: str) -> None:
    """Record one omitted candidate (J-35): always bump the EXACT `omitted_total`; append to the bounded
    sample list only while under the cap (so an all-omitted expand stays bounded). The omission is the
    honest record of a candidate that did NOT become a member — it is NEVER a fabricated member/cap/bar."""
    prog.omitted_total += 1
    if len(prog.omitted) < _MAX_OMITTED_SAMPLES:
        prog.omitted.append({"symbol": symbol, "reason": reason})


def _existing_dates(session: Session, symbol: str, start: date_cls, end: date_cls) -> set[date_cls]:
    """The `(symbol, date)` dates already persisted in `[start, end]` — so the fetch only INSERTs NEW
    bars and never overwrites a committed seed bar (anti-goal: range fetch never overwrites)."""
    stmt = (
        select(DailyPrice.date)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date >= start)
        .where(DailyPrice.date <= end)
    )
    return set(session.exec(stmt).all())


def _make_scrubber(key: Optional[str]) -> Callable[[str], str]:
    """A redactor that removes a resolved key literal from any error string (defense-in-depth on top of
    the `_http.py` URL redaction — important because J-34 surfaces richer per-chunk errors). When no key
    was resolved it is the identity. The key itself is NEVER logged or persisted — the closure only
    REMOVES it (anti-goal: Import keys are env-or-session, never persisted)."""
    if not key:
        return lambda s: s
    return lambda s: s.replace(key, "***")


def _fetch_message(prog: JobProgress) -> str:
    return f"fetched {prog.symbols_ok}/{prog.symbols_total} symbols ({prog.symbols_failed} failed)"


# --------------------------------------------------------------------------------------------------
# J-34 chunk plan — deterministic symbol-batches × date-windows (chunk count derives from config)
# --------------------------------------------------------------------------------------------------
def _date_windows(start: date_cls, end: date_cls, window_days: int) -> list[tuple[date_cls, date_cls]]:
    """Split `[start, end]` (inclusive) into consecutive windows of at most `window_days` calendar days."""
    windows: list[tuple[date_cls, date_cls]] = []
    ws = start
    while ws <= end:
        we = min(ws + timedelta(days=window_days - 1), end)
        windows.append((ws, we))
        ws = we + timedelta(days=1)
    return windows


def _chunk_plan(
    cfg: Config, symbols: list[str], start: date_cls, end: date_cls
) -> list[tuple[list[str], tuple[date_cls, date_cls]]]:
    """The deterministic chunk plan = (symbol-batches of `symbol_batch_size` over the STABLE symbol
    ordering) × (date-windows of `date_window_days` over `[start, end]`). `chunk_total` = len(batches) ×
    len(windows), so varying either config dimension changes the plan size (No magic numbers — both come
    from `config.data_manager.import_chunking`)."""
    chunking = cfg.data_manager.import_chunking
    batch = chunking.symbol_batch_size
    batches = [symbols[i:i + batch] for i in range(0, len(symbols), batch)]
    windows = _date_windows(start, end, chunking.date_window_days)
    return [(b, w) for b in batches for w in windows]


# --------------------------------------------------------------------------------------------------
# J-59 covered-range fetch planner — skip the provider call for any (symbol, window) already FULLY
# covered against the benchmark trading calendar (a re-run over a covered range reaches backfill in
# seconds, never ~45min of no-op re-fetching to add `0 new bars`).
# --------------------------------------------------------------------------------------------------
def _trading_days_in_window(
    calendar: list[date_cls], ws: date_cls, we: date_cls
) -> list[date_cls]:
    """The benchmark trading days falling inside `[ws, we]` (inclusive) — the EXACT dates a fully-covered
    fetch would need to have. Built off the benchmark calendar (not a naive min/max range), so a window
    with internal gaps is judged honestly."""
    return [d for d in calendar if ws <= d <= we]


def _symbol_window_fully_covered(
    session: Session, symbol: str, ws: date_cls, we: date_cls, calendar: list[date_cls]
) -> bool:
    """J-59 — True iff `symbol` already has a stored bar for EVERY benchmark trading day in `[ws, we]`, so
    a fetch over this window would add `0 new bars` and can be SKIPPED (zero provider calls). Exact: a
    single missing trading day in the window returns False (the window still fetches). Built off the
    benchmark calendar intersected with the symbol's stored dates — never a naive range that would mask an
    internal gap. A window the benchmark calendar does NOT yet cover (no trading day of the calendar falls
    in it — e.g. we are fetching dates BEYOND the current seed range) is NOT skippable: we cannot prove
    coverage of dates the calendar does not yet know, so the fetch proceeds (returns False)."""
    needed = _trading_days_in_window(calendar, ws, we)
    if not needed:
        return False  # the calendar doesn't yet cover this window — cannot prove coverage; fetch it
    have = _existing_dates(session, symbol, ws, we)
    return all(d in have for d in needed)


def _plan_uncovered_chunks(
    session: Session,
    cfg: Config,
    chunks: list[tuple[list[str], tuple[date_cls, date_cls]]],
    *,
    start_chunk: int,
) -> tuple[set[int], list[str]]:
    """J-59 — for the chunk plan (from `start_chunk` onward), determine which chunks are FULLY covered
    (every symbol in the batch already has every trading day in the window) and so can be SKIPPED with
    ZERO provider calls, and which DISTINCT symbols are already fully covered across ALL their windows (so
    the per-symbol completion counter can credit them honestly without a fetch). Returns
    `(fully_covered_chunk_indexes, covered_symbols)`. A partially-covered chunk is NOT skipped (it still
    fetches; the per-(symbol,date) INSERT-new-only guard fills only the missing bars — no duplicate row)."""
    calendar = _trading_days(session, cfg)
    fully_covered: set[int] = set()
    # track, per symbol, whether EVERY window it appears in (from start_chunk on) is fully covered.
    symbol_all_covered: dict[str, bool] = {}
    for idx in range(start_chunk, len(chunks)):
        sym_batch, (ws, we) = chunks[idx]
        chunk_covered = True
        for symbol in sym_batch:
            covered = _symbol_window_fully_covered(session, symbol, ws, we, calendar)
            if not covered:
                chunk_covered = False
            prev = symbol_all_covered.get(symbol, True)
            symbol_all_covered[symbol] = prev and covered
        if chunk_covered:
            fully_covered.add(idx)
    covered_symbols = [s for s, ok in symbol_all_covered.items() if ok]
    return fully_covered, covered_symbols


# --------------------------------------------------------------------------------------------------
# J-34 durable checkpoint — MUTABLE job-control state on import_checkpoints (NEVER a key; NOT a snapshot)
# --------------------------------------------------------------------------------------------------
def _load_checkpoint(session: Session, import_id: str) -> Optional[ImportCheckpoint]:
    return session.exec(select(ImportCheckpoint).where(ImportCheckpoint.import_id == import_id)).first()


def get_checkpoint(session: Session, import_id: str) -> Optional[ImportCheckpoint]:
    """The durable import checkpoint for `import_id`, or None — used by the resume endpoint to map an
    unknown id → 404 and a non-resumable id → 409 (never a fabricated job)."""
    return _load_checkpoint(session, import_id)


def _start_checkpoint(
    session: Session, cfg: Config, prog: JobProgress, symbols: list[str], chunk_total: int
) -> ImportCheckpoint:
    """Create the durable checkpoint row for a fresh fetch job (status `running`, resume point 0) and
    record the chunk plan on the live `JobProgress`. Stores the deterministic symbol plan + chunk_total;
    NEVER a key value."""
    cp = ImportCheckpoint(
        import_id=prog.job_id,
        source=prog.source or cfg.data_manager.default_source,
        kind=prog.kind,
        start=prog.start,
        end=prog.end,
        symbol_plan_json=json.dumps(symbols),
        chunk_total=chunk_total,
        next_chunk_index=0,
        status="running",
        created_at=prog.started_at,
        updated_at=_utcnow(),
    )
    session.add(cp)
    session.commit()
    session.refresh(cp)
    prog.chunk_total = chunk_total
    prog.chunk_index = 0
    return cp


def _advance_checkpoint(
    session: Session, checkpoint: ImportCheckpoint, prog: JobProgress, *, next_idx: int, status: str
) -> None:
    """Persist the checkpoint after a chunk completes (or on a graceful 429 `resumable` stop / terminal
    state): the resume point + cumulative counters + status + `updated_at` + the J-59 completed stages.
    Committed so the row survives a backend restart (the durability the Resume affordance depends on)."""
    checkpoint.next_chunk_index = next_idx
    checkpoint.symbols_ok = prog.symbols_ok
    checkpoint.symbols_failed = prog.symbols_failed
    checkpoint.bars_fetched = prog.bars_fetched
    checkpoint.status = status
    checkpoint.completed_stages_json = json.dumps(list(prog.completed_stages))  # J-59 stage-awareness
    checkpoint.updated_at = _utcnow()
    session.add(checkpoint)
    session.commit()


def _finalize_checkpoint(session: Session, checkpoint: ImportCheckpoint, prog: JobProgress) -> None:
    """Mark a completed (un-paused) fetch's checkpoint terminal: `failed` iff a fetch was attempted and
    EVERY symbol failed, else `ok` — so it never lingers as `resumable` (a completed import is not
    resumable: a resume of it → 409)."""
    terminal = "failed" if (prog.symbols_total > 0 and prog.symbols_ok == 0) else "ok"
    _advance_checkpoint(session, checkpoint, prog, next_idx=checkpoint.chunk_total, status=terminal)


def _mark_checkpoint_failed_backfill(
    session: Session, checkpoint: ImportCheckpoint, prog: JobProgress
) -> None:
    """J-59 — mark a `both` job's durable checkpoint `failed_backfill` after its FETCH stage completed but
    its BACKFILL stage failed/was interrupted, so the Unfinished-imports surface offers it as **resumable
    from the backfill stage** (a Resume skips the completed fetch entirely — zero provider calls). Keeps
    the `completed_stages` (with `fetch`) so the resume routes to backfill. The fetch resume point is left
    at chunk_total (the fetch is done — never re-fetched)."""
    checkpoint.next_chunk_index = checkpoint.chunk_total
    checkpoint.status = "failed_backfill"
    checkpoint.completed_stages_json = json.dumps(list(prog.completed_stages))
    checkpoint.updated_at = _utcnow()
    session.add(checkpoint)
    session.commit()


# --------------------------------------------------------------------------------------------------
# J-34 chunked fetch engine — batched, idempotent, 429-backoff → graceful resumable (the ONE fetch path)
# --------------------------------------------------------------------------------------------------
def _fetch_symbol_with_retry(
    provider: PriceProvider,
    symbol: str,
    start: date_cls,
    end: date_cls,
    *,
    chunking: ImportChunkingCfg,
    sleep_fn: Callable[[float], None],
):
    """Fetch one symbol's bars, retrying ONLY on `RateLimitError` with exponential backoff
    `min(base * 2**attempt, cap)` up to `max_retries` retries (after the first try). Returns bars on
    success; re-raises `RateLimitError` once the retries are exhausted (caller pauses resumable); lets a
    non-429 `ProviderUnavailableError` propagate immediately (caller counts it failed). No chunk/backoff
    literal here — all from `chunking` (No magic numbers)."""
    attempt = 0
    while True:
        try:
            return provider.get_daily(symbol, start=start, end=end)
        except RateLimitError:
            if attempt >= chunking.max_retries:
                raise  # exhausted — the provider is persistently rate-limited
            sleep_fn(min(chunking.backoff_base_seconds * (2 ** attempt), chunking.backoff_cap_seconds))
            attempt += 1


@dataclass
class _SymbolFetchResult:
    """One symbol's outcome from a worker thread (network I/O ONLY — no session/JobProgress touch). The
    orchestrating thread consumes these IN BATCH ORDER to apply DB writes + progress mutations, so the
    workers stay side-effect-free (anti-goal: SQLite writes serialized; progress mutated on one thread)."""

    symbol: str
    outcome: str  # "ok" | "failed" | "ratelimited"
    bars: list = field(default_factory=list)  # the fetched Bars (only for "ok")
    error: Optional[str] = None  # the RAW (un-scrubbed) error text (only for "failed"); scrubbed on-thread


def _fetch_one_symbol(
    provider: PriceProvider,
    symbol: str,
    ws: date_cls,
    we: date_cls,
    *,
    chunking: ImportChunkingCfg,
    sleep_fn: Callable[[float], None],
) -> _SymbolFetchResult:
    """The WORKER body (runs on a pool thread): fetch ONE symbol's bars over the chunk's date-window with
    the existing 429-backoff retry, honoring `inter_request_sleep_seconds` as the polite per-worker delay.
    It does NO DB I/O and mutates NO shared state — it only calls the provider + the injected sleep and
    returns a plain result object the orchestrating thread interprets. A persistent 429 (retries exhausted)
    ⇒ `ratelimited`; a non-429 `ProviderUnavailableError` ⇒ `failed` (carrying the RAW error text, scrubbed
    later on the orchestrating thread before it is recorded — httpx errors embed `?apikey=`)."""
    try:
        bars = _fetch_symbol_with_retry(provider, symbol, ws, we, chunking=chunking, sleep_fn=sleep_fn)
    except RateLimitError:
        return _SymbolFetchResult(symbol=symbol, outcome="ratelimited")
    except ProviderUnavailableError as exc:
        return _SymbolFetchResult(symbol=symbol, outcome="failed", error=f"{symbol}: {exc}")
    if chunking.inter_request_sleep_seconds:
        sleep_fn(chunking.inter_request_sleep_seconds)  # polite per-worker delay (injectable; no wall-clock in tests)
    return _SymbolFetchResult(symbol=symbol, outcome="ok", bars=bars)


def _fetch_chunk_symbols(
    provider: PriceProvider,
    sym_batch: list[str],
    ws: date_cls,
    we: date_cls,
    *,
    chunking: ImportChunkingCfg,
    sleep_fn: Callable[[float], None],
    workers: int,
) -> list[_SymbolFetchResult]:
    """Fetch a chunk's symbol batch on a BOUNDED pool of at most `workers` threads (network I/O only),
    returning the per-symbol results IN BATCH ORDER (deterministic, regardless of completion order) so the
    orchestrating thread applies DB writes + progress in a stable sequence. With `workers == 1` this is
    effectively serial. EVERY submitted worker is awaited before this returns (no thread outlives the
    chunk — the iter-28 determinism lesson: no daemon outlives the job)."""
    if workers <= 1 or len(sym_batch) <= 1:
        return [
            _fetch_one_symbol(provider, s, ws, we, chunking=chunking, sleep_fn=sleep_fn)
            for s in sym_batch
        ]
    results: dict[str, _SymbolFetchResult] = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(sym_batch))) as pool:
        future_to_symbol = {
            pool.submit(
                _fetch_one_symbol, provider, s, ws, we, chunking=chunking, sleep_fn=sleep_fn
            ): s
            for s in sym_batch
        }
        # as_completed drains every future (the `with` also joins on exit) — nothing is left in flight.
        for future in as_completed(future_to_symbol):
            res = future.result()  # a worker exception would surface here, not deadlock the pool
            results[res.symbol] = res
    return [results[s] for s in sym_batch]  # re-order to the deterministic batch order


def _run_chunked_fetch(
    session: Session,
    cfg: Config,
    prog: JobProgress,
    provider: PriceProvider,
    *,
    chunks: list[tuple[list[str], tuple[date_cls, date_cls]]],
    checkpoint: ImportCheckpoint,
    scrub: Callable[[str], str],
    sleep_fn: Callable[[float], None],
    start_chunk: int,
    covered_chunks: Optional[set[int]] = None,
    overlap_sink: Optional[dict[str, list[Bar]]] = None,
    overlap_days: int = 0,
) -> None:
    """Run the chunk plan from `start_chunk`, persisting the checkpoint AFTER each completed chunk (so
    `next_chunk_index` only advances once a chunk's bars are durably committed). Within EACH chunk the
    symbol batch is fetched on a bounded pool of `fetch_workers` threads (network I/O only — J-46); ALL
    DB reads/writes and ALL `JobProgress` mutations stay on THIS orchestrating thread, and the chunk's
    new `(symbol, date)` rows are written in ONE transaction (one INSERT + one `commit()` per chunk, not
    per symbol). Only NEW rows are written (the existing INSERT-new-only `_existing_dates` guard) — so a
    committed bar is NEVER overwritten and a resume re-fetches/duplicates nothing (per-`(symbol, date)`
    idempotency).

      * `RateLimitError` beyond `max_retries` for ANY symbol in the chunk ⇒ stop GRACEFULLY: DISCARD the
        interrupted chunk's fetched bars (nothing is committed for it — chunk-atomic), set the job +
        checkpoint `resumable` (distinct from `failed`) with `next_chunk_index` at the UN-finished chunk,
        and RETURN — never raise, never fabricate a bar (anti-goals: No fabricated data; Live fetch is
        real-data-only). Resume re-attempts the whole chunk; its already-committed PRIOR chunks are
        skipped by `_existing_dates`, so no duplicate fetch of committed bars.
      * a non-429 `ProviderUnavailableError` for a symbol ⇒ count it failed, record a REDACTED error
        (the resolved key scrubbed on THIS thread), and continue the chunk — unchanged semantics.

    iter-35 (J-21/B-304): when `overlap_sink` is given, every "ok" result's freshly-fetched bars are
    accumulated into it (keyed by symbol), trimmed to the last `overlap_days` entries per symbol as they
    arrive — a BOUNDED per-symbol window, never the whole fetched history (the iter-24/26 anti-goal-#8
    lesson). This captures the RAW fetch BEFORE the `_existing_dates` new-only filter below, because a
    date already covered by a prior fetch/backfill is exactly the "overlap" the live-vs-seed drift check
    needs to see — the INSERT-new-only DB write silently discards a re-adjusted value for an
    already-stored date, so the drift artifact must be built from what the provider ACTUALLY returned,
    never a DB re-read. `overlap_sink` defaults to `None`, so every pre-iter-35 call site is unaffected."""
    chunking = cfg.data_manager.import_chunking
    workers = chunking.fetch_workers  # the bounded pool size (config — No magic numbers)
    covered_chunks = covered_chunks or set()
    prog.chunk_index = start_chunk
    for chunk_idx in range(start_chunk, len(chunks)):
        sym_batch, (ws, we) = chunks[chunk_idx]
        # J-59 covered-range planner: a chunk whose every (symbol, window) is already FULLY covered against
        # the benchmark trading calendar adds `0 new bars` — SKIP the provider call entirely (zero network
        # calls), credit the batch's symbols as completed (per-symbol counter stays honest), advance the
        # durable resume point, and move on in seconds. A partially-covered chunk is NOT in this set, so it
        # still fetches (the per-(symbol,date) INSERT-new-only guard fills only the missing bars).
        if chunk_idx in covered_chunks:
            for symbol in sym_batch:
                prog.mark_symbol_done(symbol)
            prog.tick(f"skipped covered window {ws.isoformat()}→{we.isoformat()} (0 new bars)")
            prog.message = _fetch_message(prog)
            prog.chunk_index = chunk_idx + 1
            _advance_checkpoint(session, checkpoint, prog, next_idx=chunk_idx + 1, status="running")
            continue
        # fetch the whole batch on the bounded pool (network only); results come back in batch order.
        results = _fetch_chunk_symbols(
            provider, sym_batch, ws, we, chunking=chunking, sleep_fn=sleep_fn, workers=workers
        )
        if any(r.outcome == "ratelimited" for r in results):
            # Persistent rate-limit somewhere in the chunk → graceful resumable stop. Do NOT commit the
            # chunk's bars (chunk-atomic: it is committed entirely or not at all) and do NOT advance
            # next_chunk_index: the current chunk is un-finished, so Resume re-attempts it (idempotent —
            # prior chunks' committed bars are skipped by _existing_dates). Discard any pending ORM state,
            # then persist resumable and return (no raise, no fabrication).
            session.rollback()  # drop any in-session changes; the chunk's bars were never committed
            prog.status = "resumable"
            _advance_checkpoint(session, checkpoint, prog, next_idx=chunk_idx, status="resumable")
            prog.message = _final_summary(prog)
            return
        # Apply the chunk's outcomes on THIS thread: collect new rows for ok symbols, count failures —
        # in deterministic batch order. (Idempotency: each symbol appears once per chunk; prior chunks
        # are already committed, so _existing_dates reflects committed reality and dedups correctly.)
        chunk_rows: list[dict] = []
        for res in results:
            if res.outcome == "failed":
                # J-66: distinct-dedup the failed symbol across windows (a symbol that succeeds in another
                # window stays `ok`, not double-counted) so the failed counter never exceeds the total.
                prog.mark_symbol_failed(res.symbol)
                _record_error(prog, scrub(res.error or f"{res.symbol}: provider error"))
                prog.message = _fetch_message(prog)
                continue
            if overlap_sink is not None and res.bars:
                # iter-35 (J-21/B-304): capture the RAW fetch for the post-fetch drift check, bounded to
                # the last `overlap_days` bars per symbol (see the docstring above) -- independent of
                # whether these dates end up written below (an already-covered date is exactly what the
                # overlap check needs to see, and INSERT-new-only would otherwise hide it).
                bucket = overlap_sink.setdefault(res.symbol, [])
                bucket.extend(res.bars)
                if overlap_days > 0 and len(bucket) > overlap_days:
                    del bucket[:-overlap_days]
            already = _existing_dates(session, res.symbol, ws, we)
            for bar in res.bars:
                if bar.date not in already:
                    chunk_rows.append({
                        "symbol": res.symbol,
                        "date": bar.date,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                    })
            # J-66: per-SYMBOL completion tick — dedup across windows so symbols_ok counts DISTINCT
            # symbols and never exceeds symbols_total (the 318/159 fix). Stamps the heartbeat + activity.
            prog.mark_symbol_done(res.symbol)
            prog.message = _fetch_message(prog)
        # ONE transaction per chunk: a single INSERT of every new row, then a single commit — so the
        # durable resume point only advances once the chunk's bars are committed (a crash before this
        # leaves next_chunk_index at the chunk, and Resume re-fetches it idempotently).
        if chunk_rows:
            session.execute(insert(DailyPrice.__table__), chunk_rows)
        session.commit()
        prog.bars_fetched += len(chunk_rows)
        # the chunk fully completed + committed → advance the durable resume point + cumulative counters
        prog.chunk_index = chunk_idx + 1
        _advance_checkpoint(session, checkpoint, prog, next_idx=chunk_idx + 1, status="running")


# --------------------------------------------------------------------------------------------------
# iter-35 (J-21/B-304) -- the post-fetch live-vs-seed drift validation stage
# --------------------------------------------------------------------------------------------------
def _check_drift(
    cfg: Config,
    seed_dir: Path,
    fetched_bars: dict[str, list[Bar]],
    prog: JobProgress,
    scrub: Callable[[str], str],
) -> None:
    """The post-fetch validation stage (J-21/B-304): byte/fixed-precision compare this job's freshly-
    fetched bars (`overlap_sink`, accumulated by `_run_chunked_fetch`) against the COMMITTED SEED CSVs
    (via the SAME `SeedProvider` the offline default path reads — no second CSV parser) over the
    configured overlap window, and persist the SINGLE drift-report artifact via
    `app.engine.drift.write_drift_report` (re-read by `compute_preflight` and `GET /api/data`). A symbol
    with no committed seed history (e.g. a brand-new universe member) is honestly skipped — no crash, no
    fabricated comparison.

    Best-effort: this is a VALIDATION side-check, never the primary job — any failure here is recorded
    (scrubbed, so a redacted key never leaks) and SWALLOWED, mirroring the `_create_run_record`
    bookkeeping-failure discipline elsewhere in this module. It NEVER mutates/reconciles the fetched bars
    (B-304 "Do NOT touch the fetched data") and never queries the DB (a tiny per-symbol CSV read only)."""
    if not fetched_bars:
        return  # nothing was actually fetched this job (e.g. every symbol failed) -- nothing to compare
    try:
        seed_provider = SeedProvider(seed_dir)
        seed_bars: dict[str, list[Bar]] = {}
        for symbol in fetched_bars:
            try:
                seed_bars[symbol] = seed_provider.get_daily(symbol)
            except ProviderUnavailableError:
                continue  # no committed seed history for this symbol -- honest skip, not a crash
        report = drift_module.build_drift_report(
            fetched_bars, seed_bars,
            overlap_days=cfg.data_quality.drift.overlap_days,
            # a DETERMINISTIC job parameter (never `date.today()` -- anti-goal #5), mirroring the J-20
            # freshness-anchor precedent.
            reference=prog.end.isoformat(),
        )
        drift_module.write_drift_report(report)
    except Exception as exc:  # noqa: BLE001 -- a drift-check failure must not crash the fetch job
        _record_error(prog, scrub(f"drift check failed: {exc}"))


def _compute_one_backfill_date(
    eng: Engine, cfg: Config, d: date_cls, shared_cache
) -> tuple[date_cls, Optional[dict], float]:
    """Worker body (J-53): compute ONE date's canonical snapshot payload on this worker's OWN read-only
    session (a separate SQLite connection — concurrent readers are safe; the worker NEVER writes). Returns
    `(d, payload, per_date_seconds)` where `payload` is None when the date already has a snapshot (the
    create-once fast-path — nothing to compute) so the orchestrator skips the write. The worker ATTACHES
    the orchestrator's pre-filled SHARED bar cache to its session, so each symbol's full series is loaded
    ONCE for the whole job (the J-46 load-once-per-job guarantee, preserved under parallelism) — the
    worker reads the shared immutable series, it does not reload bars. The engines are deterministic and
    read the SAME bars the sequential path reads, so the payload is byte-identical to an inline compute
    (asserted by the parallel-vs-sequential equality test). A worker exception propagates to the
    orchestrator (surfaced as an explicit per-date failure — never a silent partial)."""
    t0 = time.perf_counter()
    with Session(eng) as wsession:
        if scanner.get_run_for_date(wsession, d) is not None:
            return d, None, time.perf_counter() - t0  # create-once: existing snapshot, no compute/overwrite
        with attach_shared_cache(wsession, shared_cache):
            payload = scanner.compute_run_payload(wsession, d, cfg)
    return d, payload, time.perf_counter() - t0


def _record_date_failure(prog: JobProgress, d: date_cls, error: str) -> None:
    """J-67 — record ONE per-date backfill failure (honest error + which date) so the stage ends `partial`
    with the per-date detail instead of aborting the whole stage. The other dates still complete; no
    snapshot is fabricated for the failed date. The sample list is bounded like the per-symbol error list;
    ops-hardening iter-1: the UNCAPPED `date_failures_total` is ALWAYS bumped so `error_other` stays exact
    past `_MAX_ERROR_SAMPLES` failures (the sample `len()` would undercount)."""
    prog.date_failures_total += 1
    if len(prog.date_failures) < _MAX_ERROR_SAMPLES:
        prog.date_failures.append({"date": d.isoformat(), "error": error})


def _cadence_allowed_dates(
    session: Session, trading_days: list[date_cls], cfg: Config
) -> Optional[set]:
    """iter-18 — the BOUNDED deep-history snapshot cadence (`scanner.snapshot_cadence`): the set of
    trading days a job may target, or None for "no filter" (daily density everywhere — the pre-iter-18
    behavior, byte-identical, which is also the config default).

    ops-hardening iter-1 (J-01): `_do_backfill` now calls this ONLY for a `rebuild` job — an explicit
    `backfill`/`both` request's date range always wins over this cadence (see `_do_backfill`'s docstring).
    This function's own logic is unchanged; only its caller's usage narrowed.

    Days ON/AFTER `daily_start` keep FULL daily density (the referee's recent-window power is
    preserved). Days BEFORE it keep only the FIRST trading day of each calendar month (`monthly`) or
    ISO week (`weekly`). Walk-forward cadence dates (`forward_testing.walk_forward_asof_dates` — the
    `/api/backtest` as-of set) and `scanner.bootstrap_dates` are ALWAYS allowed, never filtered out, so
    the replay + the seeded regime runs stay fully backed. Every allowed date is a REAL trading day
    from the passed calendar — the cadence never fabricates a date."""
    cadence = cfg.scanner.snapshot_cadence
    if cadence.daily_start is None or cadence.deep_cadence == "daily":
        return None  # daily everywhere — no filtering (the documented default)
    allowed = {d for d in trading_days if d >= cadence.daily_start}
    seen_buckets: set = set()
    for d in trading_days:
        if d >= cadence.daily_start:
            break  # trading_days is ascending — the deep region is the prefix
        bucket = (d.year, d.month) if cadence.deep_cadence == "monthly" else d.isocalendar()[:2]
        if bucket not in seen_buckets:
            seen_buckets.add(bucket)
            allowed.add(d)  # the first trading day of this calendar month / ISO week
    # the walk-forward as-of set + the bootstrap dates are snapshot dates BY CONTRACT — never filtered.
    allowed.update(forward_testing.walk_forward_asof_dates(session, cfg))
    allowed.update(cfg.scanner.bootstrap_dates)
    return allowed


def _cleanup_orphan_run(session: Session, d: date_cls) -> None:
    """J-68 — drop a half-written snapshot for `d` (whole-row): the create-once helpers COMMIT the
    `ScannerRun` (+ its children) before the forward-return INSERT, so a forward-return failure can leave
    a committed-but-childless run. This deletes that orphan run + its `ScannerResult` / `SectorScoreRow` /
    `ThemeScoreRow` children + any partial `ForwardReturn` rows, so a failed date leaves NO inconsistent
    snapshot and the create-once re-run is clean (no stranded run → no UNIQUE crash). It runs on the
    per-date write session AFTER its `rollback()` (a fresh transaction) and commits its own delete; if the
    cleanup itself fails it is swallowed (best-effort — the failed date is already recorded) so it never
    masks the original per-date error nor aborts the stage."""
    try:
        session.rollback()  # clear the failed transaction state on THIS per-date session before cleanup
        run = scanner.get_run_for_date(session, d)
        if run is None:
            return  # nothing committed for this date (the run INSERT itself rolled back) — nothing to clean
        run_id = run.id
        session.execute(delete(ForwardReturn).where(ForwardReturn.run_id == run_id))
        session.execute(delete(ScannerResult).where(ScannerResult.run_id == run_id))
        session.execute(delete(SectorScoreRow).where(SectorScoreRow.run_id == run_id))
        session.execute(delete(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id))
        session.execute(delete(ScannerRun).where(ScannerRun.id == run_id))
        session.commit()
    except Exception:  # noqa: BLE001 — best-effort cleanup; never mask the original failure or abort the stage
        session.rollback()


_libc_malloc_trim_cache: dict = {}


def _resolve_libc_malloc_trim():
    """ops-hardening iter-9 (B2) — resolve the libc `malloc_trim` handle AT MOST ONCE per process
    (module-level, first-call-cached), instead of re-running `ctypes.util.find_library` +
    `ctypes.CDLL` — each its own library-resolution fork/exec on some platforms — on EVERY
    `_release_process_memory()` call. This matters most on the exact memory-pressure path this session
    hardened: a warm loop's `MemoryError`-abort calls `_release_process_memory()` once per aborted loop,
    so a single heavy ingest can invoke it several times. Caches a permanent resolution FAILURE too
    (non-glibc / symbol absent) so it is never retried either. Returns the cached `libc.malloc_trim`
    callable, or `None` when unavailable."""
    if "fn" not in _libc_malloc_trim_cache:
        try:
            libc_name = ctypes.util.find_library("c") or "libc.so.6"
            libc = ctypes.CDLL(libc_name)
            _libc_malloc_trim_cache["fn"] = libc.malloc_trim
        except (OSError, AttributeError):  # non-glibc / symbol absent — a PERMANENT failure, cached
            _libc_malloc_trim_cache["fn"] = None
        except MemoryError:
            # ops-hardening iter-44 AUDIT (B2): the resolution ITSELF allocates — `ctypes.util.find_library`
            # forks `ldconfig` and regexes its whole stdout — so under an exhausted `ulimit -v` it raises
            # `MemoryError`. That is precisely WHEN `_release_process_memory()` is called: from inside the
            # per-horizon `except MemoryError` abort handler in `_refresh_ingest_aggregates`. With only
            # `(OSError, AttributeError)` caught here, the abort handler's own cleanup re-raised and the
            # "log + continue, never raise" contract broke — the live escape captured by
            # `test_ingest_finalize_memory_pressure.py`'s child probe (returncode 1,
            # `ctypes/util.py:297 in _findSoname_ldconfig` under a 750,000 KB cap). Return None WITHOUT
            # caching it: unlike a non-glibc host this is a TRANSIENT condition, and caching would
            # permanently disable the iter-27 `malloc_trim` memory-return path for the process's whole
            # life (an AG-8 regression). Applies the binding iter-43 lesson — key the guard to the whole
            # exception set the incident actually produces, not its headline exception.
            return None
    return _libc_malloc_trim_cache["fn"]


def _release_process_memory() -> None:
    """iter-27 (J-16, anti-goal #8) — after a heavy full-universe backfill/rebuild stage finishes, return
    the just-freed memory to the OS so a SECOND consecutive full-universe rebuild in the SAME long-lived
    server process starts from a lean baseline instead of stacking on the first run's retained address space.

    Root cause this addresses (iter-27 audit finding B2, re-confirmed here by a two-run in-process probe):
    the per-job `_BarCache` object IS dropped when `_do_backfill`'s `with prefilled_bar_cache(...)` block
    exits — the accumulation is NOT a leaked Python object. It is at the process VSZ / glibc malloc-arena
    level: the ~1.5 GB of `Bar` lists (plus per-(date,symbol) transients and SQLAlchemy result buffers) are
    freed back to the allocator's arenas, but glibc does not automatically return that (fragmented) address
    space to the OS — so run 1 leaves VmSize inflated and run 2 re-allocates on top of it, pinning VSZ at
    the `ulimit -v` ceiling and wedging the backend (the reproduced iter-26/iter-27 crash signature).

    Two best-effort, fully byte-identity-NEUTRAL steps (they change WHEN freed memory is returned, never any
    computed value): `gc.collect()` reclaims the now-unreferenced cache/transients deterministically (not at
    the next cyclic-GC threshold, so they cannot linger resident into the next job's prefill), and glibc
    `malloc_trim(0)` hands the emptied arenas' pages back to the OS. Paired with the `MALLOC_ARENA_MAX` cap
    the start script exports (which bounds how many independently-fragmenting arenas glibc creates across the
    server's worker threads on a many-core host — the dominant VSZ lever), consecutive rebuilds stay under
    the cap with margin. `malloc_trim` is glibc-only; on any other libc the `gc.collect()` still runs and the
    trim is silently skipped.

    ops-hardening iter-9 (B2): the libc handle resolution itself is memoized by `_resolve_libc_malloc_trim`
    (module-level, first-call-cached) — this function's own `gc.collect()` + `malloc_trim(0)` timing and
    effect are unchanged; only the redundant repeated resolution is removed."""
    gc.collect()
    malloc_trim = _resolve_libc_malloc_trim()
    if malloc_trim is not None:
        try:
            malloc_trim(0)  # glibc: return free heap/arena pages to the OS (no-op elsewhere)
        except OSError:  # defensive — a resolved-but-failing call still must never mask the caller
            pass


# --------------------------------------------------------------------------------------------------
# ops-hardening iter-39 (audit finding B3 / J-07 step 4) — TEST-ONLY `MemoryError` fault injection.
#
# J-07 step 4's own text sanctions exactly this: "Induce memory pressure during a warm (TEST HOOK or a
# tightened cap in a throwaway process)". Three live calibration trials this iteration (3420/2700/2650 MB)
# failed to reach the two NAMED per-item aggregate-warm handlers, because `_missing_data_diagnostic`'s
# whole-`daily_prices` materialization runs EARLIER in the same finalize sequence and exhausts any cap
# tight enough to threaten them first (audit B3). Continuing to tune the cap is the wrong-direction
# pattern in `.claude/judgment-rubrics.md` §4; this hook makes the same proof DETERMINISTIC — and, because
# it induces no real memory pressure at all, it is also strictly safer for this host (AG-10).
#
# Contract: unset in every real deployment (the env var is read once per warm call and is absent, so the
# behavior is byte-identical to before this hook existed — no second code path, no config surface). Same
# class of test-only env escape hatch as `TRENDORA_FORCE_LEGACY_BAR_CACHE` (iter-38), and it is deliberately
# NOT a config.yaml key: a fault injector must not be reachable through the product's own configuration.
# --------------------------------------------------------------------------------------------------
_FAULT_INJECT_MEMORY_ERROR_ENV = "TRENDORA_FAULT_INJECT_MEMORY_ERROR"
# The call sites this hook understands. Each is the exact per-item boundary whose `except MemoryError`
# handler J-07's acceptance names; an unknown name in the env var injects nothing (a typo must not
# silently look like a passing drill).
_FAULT_INJECT_SITES = frozenset({"forward_aggregates", "drawdown_expectations", "backfill_worker"})


def _fault_inject_memory_error(site: str) -> None:
    """Raise `MemoryError` at `site` when this process was started with `site` listed in
    `TRENDORA_FAULT_INJECT_MEMORY_ERROR` (comma-separated). A no-op — one `os.environ.get` — otherwise.

    The raised exception carries the site name so the drill/test asserts WHICH stage aborted from a direct
    read of the log line, never inferring it from "a `MemoryError` fired somewhere" (the binding iter-37/38
    lesson). An unrecognized site name is ignored (see `_FAULT_INJECT_SITES`)."""
    if site not in _FAULT_INJECT_SITES:
        return
    raw = os.environ.get(_FAULT_INJECT_MEMORY_ERROR_ENV, "")
    if site in {token.strip() for token in raw.split(",") if token.strip()}:
        raise MemoryError(f"injected at fault-injection site {site!r} ({_FAULT_INJECT_MEMORY_ERROR_ENV})")


def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engine) -> None:
    """For each in-range trading day with bars but NO snapshot, create the immutable snapshot then INSERT
    its realized forward returns (bars > D). No scan/return math is re-implemented and no snapshot is
    overwritten — pure orchestration of the registered canonical paths.

    J-53 — the per-date COMPUTE (the expensive scoring engines) is fanned out to a bounded pool of
    `backfill_workers` threads (each worker on its OWN read-only session — pure compute, no DB write),
    while THIS orchestrating thread owns EVERY write: it persists each computed payload via the create-
    once/idempotent `scanner.persist_run_payload`, then INSERTs forward returns — both on `session`,
    serially, in date order. So SQLite writes stay serialized/transactional, snapshots stay create-once/
    concurrency-safe (J-41 guards intact), and the parallel output is byte-identical to the sequential
    path (the worker engines read the same bars). With `backfill_workers == 1` this is the sequential
    baseline (still correct). The stage's per-stage timings are recorded ONCE by the caller (`_run_job`)
    from the figures this populates: `prog._backfill_per_date_seconds_sum` accumulates each date's
    compute time (the sequential baseline the parallel wall-clock beats).

    J-67 / J-68 — per-date FAILURE ISOLATION + transaction soundness: every per-date WRITE runs on a
    FRESH session the orchestrator opens and owns for exactly that date (its own transaction boundary), so
    a single date's compute OR persist failure is caught, recorded per-date (honest error), and rolls back
    ONLY that date's own session — never the shared orchestrating `session` (which never writes in this
    stage). This removes the multi-month `'committed'`-state crash (the old code rolled back the SHARED
    session after an earlier date had committed on it). The per-date persist is ATOMIC: the create-once
    helpers commit the run before the forward-return INSERT, so on a forward-return failure the half-written
    run is cleaned up whole-row (`_cleanup_orphan_run`) — a failed date leaves NO inconsistent snapshot and
    the create-once re-run is clean. The stage ends `partial` (graded by the caller from
    `prog.date_failures`); no snapshot is fabricated for a failed date. The worker sessions are independent
    read-only connections (never shared mid-transaction); only THIS thread writes.

    ops-hardening iter-1 (J-01/J-03) — an explicit `backfill`/`both` request's `[prog.start, prog.end]`
    ALWAYS WINS over the deep-history snapshot cadence: every trading day in range is a candidate,
    regardless of `_cadence_allowed_dates` (automatic warm-up cadence still governs only elsewhere). A
    `rebuild` job (whose range the caller already widened to the full covered calendar) keeps the
    EXISTING cadence-filtered target selection, unchanged — out of scope this iteration. The honest
    run-summary breakdown (`calendar_days`/`non_trading_days`/`already_snapshotted`/`error_other`) is
    computed from the SAME in-range set this function already derives — one computation, no second
    derivation anywhere else. Execution is chunked into `import_chunking.date_window_days`-sized date
    windows (reusing `_date_windows`, the same helper the fetch stage's chunk plan already uses),
    advancing the existing `chunk_index`/`chunk_total` fields window-by-window — the safety mechanism for
    an unbounded span now that `max_range_days` no longer rejects one (AG-8: memory stays bounded per
    window; the shared bar cache is still loaded ONCE for the whole job, unaffected by this — its size is
    a function of universe breadth, not date-range length)."""
    trading_days = _trading_days(session, cfg)
    snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
    in_range = [d for d in trading_days if prog.start <= d <= prog.end]

    # J-01: `dates_total` is REDEFINED to mean "trading days in the REQUESTED range" — independent of
    # cadence/already-snapshotted status (was: the post-filter target count). The calendar/non-trading
    # split is exact by construction: every calendar day in [start, end] is either a trading day (counted
    # in dates_total) or not (non_trading_days) — never approximated.
    prog.calendar_days = (prog.end - prog.start).days + 1
    prog.dates_total = len(in_range)
    prog.non_trading_days = prog.calendar_days - prog.dates_total

    # iter-18 cadence gate: still applies to `rebuild` (unchanged behavior, out of scope this iteration);
    # bypassed entirely for an explicit `backfill`/`both` request (J-01 — "requested range always wins").
    allowed = _cadence_allowed_dates(session, trading_days, cfg) if prog.kind in _REBUILD_KINDS else None
    already = [d for d in in_range if d in snapshot_dates]
    prog.already_snapshotted = len(already)
    targets = [
        d for d in in_range
        if d not in snapshot_dates
        and (allowed is None or d in allowed)
    ]
    # `dates_done` starts PRE-SEEDED with the already-accounted-for count, so a zero-work run's progress
    # reads N/N (fully accounted for, nothing new needed) rather than a misleading 0/N on a completed job;
    # it advances only as NEW dates are actually persisted below — unchanged accounting for a fresh range
    # (already_snapshotted == 0 there, so this is a no-op byte-identical to the pre-iter-1 starting point).
    prog.dates_done = prog.already_snapshotted
    prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
    workers = cfg.data_manager.import_chunking.backfill_workers  # config pool size (No magic numbers)
    prog._backfill_concurrency = min(workers, len(targets)) if targets else workers
    prog._backfill_per_date_seconds_sum = 0.0

    # J-03: the date-window chunk plan derives from the REQUESTED range (config `import_chunking.
    # date_window_days`) — the SAME plan shape + progress fields the frontend's existing chunk-progress
    # badge already renders for a chunked fetch, so a large backfill looks identical.
    windows = _date_windows(prog.start, prog.end, cfg.data_manager.import_chunking.date_window_days)
    prog.chunk_total = len(windows)
    prog.chunk_index = 0
    if not targets:
        prog.chunk_index = prog.chunk_total  # nothing to do — the (empty) plan is trivially complete
        prog.error_other = prog.date_failures_total  # 0 — no per-date attempt was made
        return

    # ops-hardening iter-9 AUDIT (F1 completion / J-04 step 6): checkpoint the PLAN the moment it is
    # known — BEFORE the shared bar-cache prefill below, which on the deep basis runs for minutes. The
    # per-date checkpoint in `_persist_isolated` only starts writing once the FIRST date has been
    # persisted, so a process killed during the prefill window would otherwise still leave the very
    # "0 snapshots · 0 trading days in range" row this fix exists to remove. This one write makes the
    # honest range/plan (`calendar_days`/`dates_total`/`non_trading_days`/`already_snapshotted`) durable
    # from the start; the counts it carries are the ones this function just computed — no second
    # derivation, same throttled writer, same open row.
    _checkpoint_run_record(eng, prog)

    def _persist(d: date_cls, payload: Optional[dict], per_date_seconds: float) -> None:
        """Apply ONE date's result on the orchestrating thread (serial, in date order): persist the
        snapshot (or read the existing one — create-once) then INSERT its forward returns. The ONLY
        place a write happens.

        J-68 — the per-date write runs on a FRESH write session that the orchestrator OPENS AND OWNS for
        exactly this date (its own transaction boundary), NOT on the shared orchestrating `session`. This
        is the fix for the multi-month `'committed'`-state crash: `scanner.persist_run_payload` commits
        (scanner.py:205) and `forward_testing.backfill_run_forward_returns` commits (forward_testing.py:289)
        on whatever session they receive; previously both committed on the SHARED `session`, so when a
        LATER date's persist failed the isolation handler's `session.rollback()` ran on that already-
        committed shared session — the invalid 'committed' state. With a per-date session, a failure
        rolls back only THAT date's own session (see `_persist_isolated`), the shared orchestrating
        session is NEVER rolled back after a commit, and the already-committed earlier dates are untouched.

        Writes stay serialized + transactional: only THIS thread opens per-date write sessions, one date
        at a time, in date order (the parallel path fans out only the read-only COMPUTE). The shared
        pre-filled read-only bar cache is ATTACHED to the per-date session (keyed by `id(session)`), so
        the forward-return reads (and the rare race-fallback compute) stay load-once-per-job — the
        canonical output is byte-identical to the prior shared-session path (the engines read the same
        bars). The session is committed by the inner create-once helpers; this context just owns its
        lifetime and guarantees it is closed."""
        prog._backfill_per_date_seconds_sum += per_date_seconds
        prog.tick(f"scanning {d.isoformat()} ({prog.dates_done + 1}/{prog.dates_total})")
        # J-68: a FRESH write session per date — the orchestrator owns this date's transaction boundary,
        # so a failure here can only ever roll back THIS session (never the shared, already-committed one).
        with Session(eng) as wsession, attach_shared_cache(wsession, shared_cache):
            existed_before = scanner.get_run_for_date(wsession, d) is not None
            try:
                if payload is None:
                    run = scanner.get_run_for_date(wsession, d)  # already present (worker fast-path) — read, don't write
                    if run is None:  # a concurrent date created it between the worker check and here — compute now
                        run = scanner.run_scan(wsession, d, cfg)
                else:
                    run = scanner.persist_run_payload(wsession, d, payload, cfg)  # create-once; recomputes nothing
                result = forward_testing.backfill_run_forward_returns(wsession, run, cfg)  # INSERT-only, bars > D
            except Exception:  # noqa: BLE001 — make the per-date persist ATOMIC (run + forward returns)
                # J-68: the snapshot run + its forward returns are ONE per-date transaction. The inner
                # create-once helpers COMMIT the run before the forward-return INSERT, so a forward-return
                # failure leaves a committed-but-childless run. If this call CREATED the run (it did not
                # exist before), delete that orphan WHOLE-ROW (run + its children + any partial forward
                # returns) so the failed date leaves NO half-written snapshot — the create-once re-run is
                # then clean (no stranded ScannerRun → no UNIQUE crash) and nothing inconsistent persists.
                # A run that ALREADY existed before this call is left untouched (immutable; not ours to drop).
                if not existed_before:
                    _cleanup_orphan_run(wsession, d)
                raise
        prog.snapshots_created += 1
        prog.forward_returns_inserted += result["rows_inserted"]
        prog.dates_done += 1
        prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
        # ops-hardening iter-2 (J-05): record every date THIS call genuinely created a NEW snapshot for
        # (never one that already existed — a rare inter-job race, see `existed_before` above) so the
        # ingest finalize hook knows exactly which as-ofs to warm in `MarketPhaseCache`.
        if not existed_before:
            prog.new_snapshot_dates.append(d)

    def _persist_isolated(d: date_cls, payload: Optional[dict], secs: float, compute_error: Optional[str]) -> None:
        """J-67 + J-68 — write ONE date with failure isolation: if the worker COMPUTE already failed
        (`compute_error` set), record it and skip the write; else attempt the persist and, on a write
        failure, record the date failed — the remaining dates still write.

        J-68: the per-date write owns its OWN session (`_persist` opens one inside its `with` block),
        which is rolled back and closed automatically when that block exits on the exception. We therefore
        do NOT (and must not) `rollback()` the shared orchestrating `session` here — that shared session
        never wrote in this stage and rolling it back after an earlier date had committed on a per-date
        session is exactly the invalid 'committed'-state path this fix removes. A failed date leaves no
        half-written snapshot (its per-date transaction was rolled back whole), so the create-once re-run
        is clean (no stranded ScannerRun → no UNIQUE crash)."""
        if compute_error is not None:
            prog._backfill_per_date_seconds_sum += secs
            _record_date_failure(prog, d, compute_error)
        else:
            try:
                _persist(d, payload, secs)
            except Exception as exc:  # noqa: BLE001 — isolate this date; the stage continues
                # the per-date write session (owned inside `_persist`) is already rolled back + closed by
                # its `with` block; the shared orchestrating session is left untouched (never rolled back
                # post-commit).
                _record_date_failure(prog, d, str(exc))
        # ops-hardening iter-9 (F1 / J-04 step 6): freeze this date's progress onto the job's OPEN
        # run-history row (throttled — see `_checkpoint_run_record`), so a process killed mid-backfill
        # leaves an `interrupted` row carrying the progress it really reached instead of zeros.
        _checkpoint_run_record(eng, prog)

    # J-46/J-53: pre-fill ONE shared bar cache on the orchestrating session (every symbol's full series
    # loaded ONCE in one query). Workers ATTACH this same cache (read-only) so the whole K-date job does
    # at most one bar-store load per symbol — load-once-per-job, not once per date NOR once per worker.
    # The orchestrator's own forward-return reads + the race-fallback run_scan also read from it.
    #
    # iter-37 (load-once restored): pass the candidate-pool symbols so a name with ZERO bars is recorded as
    # an empty series in the single prefill — the per-date resolver's `trailing_count` then reads 0 from the
    # once-loaded cache instead of re-issuing a per-symbol lazy load EVERY snapshot date / per worker
    # session (the iter-36 defect that broke load-once for no-bar candidates). Byte-identical served values.
    pool_symbols = {row["symbol"] for row in read_pool()}
    # iter-27 (anti-goal #8): the `with prefilled_bar_cache(...)` block drops the ~1.5 GB shared `_BarCache`
    # on exit, but glibc retains that freed address space by default — so a SECOND consecutive full-universe
    # rebuild in the same long-lived process stacks on run 1's inflated VSZ and hits the `ulimit -v` ceiling.
    # `_release_process_memory()` (gc.collect + malloc_trim) in the `finally` returns it to the OS on EVERY
    # exit path (window loop done or an exception), so each rebuild starts lean. Loaded ONCE for the whole
    # job (every window shares it) — its size is bounded by universe breadth, not by how many date-window
    # chunks the requested range is split into (J-03 chunking is an execution/progress concept only).
    try:
        with prefilled_bar_cache(session, expected_symbols=pool_symbols) as shared_cache:
            # ops-hardening iter-37 (J-07 closure): the same `shared_cache` this `with` block just built
            # is what the ingest finalize hook's per-date coverage warm needs next (`_refresh_ingest_
            # aggregates` -> `_persist_per_date_coverage_snapshots`, reached after this function returns).
            # Stash the reference on `prog` NOW (before the `with` block exits and pops it from the
            # per-session registry) so that hook can `attach_shared_cache` it to ITS OWN session instead of
            # opening a SECOND independent whole-table `daily_prices` prefill for the same job — closing
            # the exact gap `test_kdate_backfill_loads_each_symbol_at_most_once` measures. Deliberately set
            # unconditionally here (not only after the loop below): a per-date compute/persist failure is
            # already isolated inside `_run_targets` (never raised out of this `with` block), so reaching
            # this line only fails for a whole-stage exception (e.g. `read_pool()`/`prefill` itself), which
            # is caught below and releases the cache immediately instead of leaving it stashed.
            #
            # ops-hardening iter-38 (J-07 closure measurement): a TEST-ONLY escape hatch to force the
            # pre-iter-37 fallback behavior (never stash/reuse the shared cache) for a genuine two-arm
            # live-cache-vs-forced-fallback VmPeak comparison on a throwaway drill DB (see
            # runs/goal-ops-hardening-iter-38/mem-drill/) — unset in every real deployment. This is the
            # ONE choke point: skipping the stash here means every downstream consumer's own
            # `prog._shared_bar_cache is not None` check (`_persist_per_date_coverage_snapshots`,
            # `_refresh_ingest_aggregates`) falls back to its own independent `prefilled_bar_cache`/
            # `nullcontext()` path, unchanged from pre-iter-37 behavior — no second code path needed.
            #
            # ops-hardening iter-39 (audit B5 fix): the prior `if not os.environ.get(...)` treated ANY
            # non-empty value as "force legacy" — including `"0"`/`"false"`, so a caller trying to
            # explicitly DISABLE the toggle by setting it to `"0"` silently ENABLED legacy mode instead.
            # An explicit truthy allowlist closes that: only a recognized truthy token forces legacy mode;
            # unset, empty, `"0"`, or any other value takes the normal (live shared-cache) path.
            if os.environ.get("TRENDORA_FORCE_LEGACY_BAR_CACHE", "").strip().lower() not in (
                "1", "true", "yes",
            ):
                prog._shared_bar_cache = shared_cache

            # ops-hardening iter-39 (audit finding B2) — per-JOB memory-pressure latch for the per-date
            # compute. Set by `_compute_one_isolated` the first time any date's compute raises
            # `MemoryError`; every date still pending then short-circuits without attempting its own
            # allocation. This is the iter-8 finalize-tail convention ("on the first `MemoryError` that ONE
            # loop stops attempting further items, instead of hammering the next item's allocation under
            # real pressure — the confirmed root cause of iter-7's 7+ minute health hang") applied to the
            # ONE per-item loop that never carried it: `_do_backfill`'s per-date compute. A `threading.Event`
            # rather than a plain bool because the parallel arm reads/writes it from `backfill_workers`
            # threads concurrently.
            memory_pressure = threading.Event()

            def _compute_one_isolated(
                d: date_cls,
            ) -> tuple[date_cls, Optional[dict], float, Optional[str]]:
                """Compute ONE date INSIDE the calling (worker) thread with per-item failure isolation,
                returning `(d, payload, seconds, compute_error)` — never raising.

                ops-hardening iter-39 (audit finding B2): before this, `_compute_one_backfill_date` was
                submitted to the pool bare, so a `MemoryError` in a worker was stored on its `Future` —
                WITH its `__traceback__`, which pins every frame's locals (the half-materialized payload,
                the ORM result buffers) alive until the orchestrating thread drains that future — while the
                worker thread immediately picked up the NEXT date and started allocating again. Under
                genuine pressure that is the amplifier, not the accident: N workers each retaining a failing
                frame chain while N more allocations are attempted. Catching in the worker's own frame ends
                both — the traceback dies with the `except` block and only a plain string crosses the thread
                boundary, and the latch stops the remaining dates from piling on.

                HONESTY: a short-circuited date is recorded as a per-date FAILURE (`error_other`), never as
                a success and never silently dropped — so `snapshots_created + already_snapshotted +
                error_other == dates_total` still holds exactly (the run-summary contract in goal.md).

                Deviation from the finalize-tail loops' `logger.exception(...)`-then-`_release_process_
                memory()` order, deliberately: formatting a traceback ALLOCATES, and this iteration's own
                trial-3 evidence shows that failing under real exhaustion
                (`runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:50` —
                "Exception ignored in thread started by: <object repr() failed>"). Freeing first buys the
                headroom the log line needs, and the log line is what makes the abort diagnosable at all."""
                if memory_pressure.is_set():
                    return d, None, 0.0, (
                        "skipped — this job already aborted a date for memory pressure "
                        "(remaining dates not attempted)"
                    )
                try:
                    _fault_inject_memory_error("backfill_worker")
                    _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
                    return d, payload, secs, None
                except MemoryError:
                    memory_pressure.set()  # latch FIRST so in-flight siblings stop allocating immediately
                    _release_process_memory()
                    logger.exception(
                        "backfill per-date compute aborted at %s — memory pressure, skipping the remaining "
                        "dates in this job", d,
                    )
                    return d, None, 0.0, f"aborted for memory pressure at {d.isoformat()}"
                except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure (unchanged)
                    return d, None, 0.0, str(exc)

            def _run_targets(window_targets: list[date_cls]) -> None:
                """Compute + persist exactly this window's target dates — serial (workers<=1 or a single
                date) or fanned-out parallel, byte-identical to the pre-chunking body (only the INPUT
                LIST now scopes to one date-window instead of the whole requested range)."""
                if workers <= 1 or len(window_targets) <= 1:
                    # serial baseline — compute + persist inline, one date at a time, in order. A per-date
                    # compute failure is caught here (isolated), not raised — the rest still run.
                    for d in window_targets:
                        _, payload, secs, compute_error = _compute_one_isolated(d)
                        _persist_isolated(d, payload, secs, compute_error)
                    return
                # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as
                # they arrive. A worker compute exception is captured PER DATE (never raised out of the
                # drain loop, so it never aborts the whole stage or deadlocks); the `with ThreadPoolExecutor`
                # joins every worker before returning, so no thread outlives the job (iter-28 determinism).
                pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
                next_idx = 0
                with ThreadPoolExecutor(max_workers=min(workers, len(window_targets))) as pool:
                    # iter-39 (audit B2): submit the ISOLATING wrapper, not the bare compute — a worker's
                    # `MemoryError` is now caught in that worker's own frame (traceback dropped there,
                    # memory released there, latch set there) and arrives here as a plain error string.
                    future_to_date = {
                        pool.submit(_compute_one_isolated, d): d
                        for d in window_targets
                    }
                    for future in as_completed(future_to_date):
                        d = future_to_date[future]
                        try:
                            _, payload, secs, compute_error = future.result()
                            pending[d] = (payload, secs, compute_error)
                        except Exception as exc:  # noqa: BLE001 — defensive: `_compute_one_isolated` never
                            # raises, so this can now only fire for a pool-level fault (e.g. the
                            # `RuntimeError: can't start new thread` iter-38's drill hit at the `ulimit -v`
                            # ceiling). Still captured per date so the drain loop never deadlocks.
                            pending[d] = (None, 0.0, str(exc))
                        # drain any now-contiguous prefix in target (date) order — writes stay strictly
                        # ordered within the window.
                        while next_idx < len(window_targets) and window_targets[next_idx] in pending:
                            cur = window_targets[next_idx]
                            cur_payload, cur_secs, cur_err = pending.pop(cur)
                            _persist_isolated(cur, cur_payload, cur_secs, cur_err)
                            next_idx += 1

            # J-03: walk the date-window plan IN ORDER, advancing chunk_index once each window's targets
            # (possibly none — an all-non-trading or all-already-snapshotted window) are accounted for.
            for ws, we in windows:
                window_targets = [d for d in targets if ws <= d <= we]
                if window_targets:
                    _run_targets(window_targets)
                prog.chunk_index += 1
    except Exception:
        # ops-hardening iter-37 (J-07 closure): a whole-stage exception here (e.g. `read_pool()`/`prefill`
        # itself faulting — every per-date compute/persist failure below this point is already isolated
        # inside `_run_targets`, never raised out of the `with` block) means the ingest finalize hook that
        # would otherwise reuse and release `prog._shared_bar_cache` never runs for this job. Release
        # immediately — same discipline as before this change — and clear the stashed reference so nothing
        # downstream mistakes it for a still-usable cache.
        prog._shared_bar_cache = None
        _release_process_memory()
        raise
    # success: deliberately NOT released here. `prog._shared_bar_cache` (stashed above, before the `with`
    # block exited) is now the ONLY reference keeping this ~1.13 GB whole-table cache alive — kept alive on
    # purpose so the ingest finalize hook (`_refresh_ingest_aggregates` -> `_persist_per_date_coverage_
    # snapshots`, this job's ONLY other bar-cache consumer, reached after this function returns) can
    # ATTACH the same already-loaded cache instead of opening a SECOND whole-table `daily_prices` prefill
    # for the same job. That hook's own `finally` releases it (nulling the reference first so `gc.collect()`
    # can actually reclaim it) once it is done — iter-27's "second consecutive rebuild starts lean"
    # guarantee still holds; only the release's TIMING moves, from immediately here to right after that
    # hook finishes.
    # UNCAPPED total (not `len(date_failures)`, a bounded sample) so `error_other` — and the invariant
    # `snapshots_created + already_snapshotted + error_other == dates_total` — stays exact past 20 failures.
    prog.error_other = prog.date_failures_total


# --------------------------------------------------------------------------------------------------
# ops-hardening iter-2 (J-05) — the ingest finalize hook: reached at the end of a successful
# backfill/both/rebuild job (`_run_job`, below). Persists a fresh coverage_snapshot, warms
# MarketPhaseCache for each snapshot date this run newly created, and warms one default EventStudyCache
# hot key — reusing each cache's existing compute function, never a second derivation of any of them.
# --------------------------------------------------------------------------------------------------
def _persist_per_date_coverage_snapshots(
    session: Session, cfg: Config, dates: list[date_cls], prog: JobProgress
) -> None:
    """Persist a byte-identical `CoverageSnapshot` row for each as-of in `dates` (the snapshot dates a
    backfill NEWLY created), so the app-wide as-of switcher serves REAL coverage for each from storage —
    never the all-zero 'not yet computed' sentinel (the iter-2 review's CRITICAL AG-3 regression: only the
    single current stamp was persisted, so every OTHER already-ingested date read as an empty DB).

    The CURRENT resolved as-of is skipped (already persisted by `refresh_coverage_snapshot`), so the common
    single-latest-date backfill filters to nothing and pays NO bar-cache load at all. When there IS extra
    work, ONE shared bar cache covers the whole loop — the whole-table bar scan runs at most once regardless
    of date count (each per-date `_compute_coverage_uncached` reuses it), so warming N dates costs one load,
    not N. Each row equals a fresh `_compute_coverage_uncached(as_of=d)`. Per-date isolation (log + continue)
    so one date's failure never drops the rest; the caller wraps this whole call non-fatally too. Reads only
    committed bars (backfill adds none), writes only `CoverageSnapshot` rows — so the shared cache never
    serves a stale series (AG-8: no unbounded request-path load; this is ingest).

    ops-hardening iter-37 (J-07 closure): when `prog` carries a `_shared_bar_cache` (stashed by `_do_backfill`
    right before it returns — the common case: this hook always runs after a `_do_backfill` call for the
    SAME job), this function ATTACHES that already-loaded cache to `session` instead of opening its OWN
    `prefilled_bar_cache` — closing the "loaded twice per job" gap `test_kdate_backfill_loads_each_symbol_
    at_most_once` measures (previously TWO independent whole-table `daily_prices` prefills ran per backfill
    job: one here, one in `_do_backfill`). `_refresh_ingest_aggregates` (the caller) releases the shared
    cache once this loop returns. When no shared cache is present — this function called directly (e.g. a
    unit test), or a backfill with zero in-range targets whose `_do_backfill` never built one — it falls
    back to opening its own `prefilled_bar_cache`, byte-identical to this function's pre-iter-37 behavior.

    ops-hardening iter-4 (F1 fix, re-review CRITICAL): calls the bare `prog.tick()` (heartbeat-only — no
    `activity` argument, so it stamps ONLY `last_progress_at` and never overwrites the "scanning ..." line;
    see `_refresh_ingest_aggregates`'s docstring) once per date at the TOP of the `todo` loop, BEFORE that
    date's heavy `refresh_coverage_snapshot_for` (`_compute_coverage_uncached`) compute. This per-date
    coverage warm is the FIRST half of the finalize tail (the market-phase loop is the second, measured
    together at ~729s for a full 378-date rebuild, `reports/perf-budgets.md` Item L); without a tick here
    `last_progress_at` froze across the whole coverage half — the exact false-'possibly stalled' defect the
    market-phase tick alone did not close."""
    if not dates:
        return
    current = _resolve_coverage_asof(session, None, cfg)
    todo = [d for d in dates if d != current]
    if not todo:
        return  # the only newly-created date IS the current stamp (already persisted) — no extra load
    aborted_for_memory = False
    shared = prog._shared_bar_cache
    if shared is not None:
        # iter-37: reuse the ONE cache `_do_backfill` already built for this job (zero re-scan) — released
        # later by `_refresh_ingest_aggregates`'s own `finally`, not by this function.
        cache_ctx = attach_shared_cache(session, shared)
    else:
        # no shared cache handed down — fall back to this function's own prefill, unchanged from before.
        pool_symbols = {row["symbol"] for row in read_pool()}
        cache_ctx = prefilled_bar_cache(session, expected_symbols=pool_symbols)
    with cache_ctx:
        for d in todo:
            prog.tick()  # F1 fix (iter-4): per-date heartbeat stamp before this date's heavy coverage compute
            try:
                refresh_coverage_snapshot_for(session, cfg, d)
            # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` under real pressure must NOT be
            # treated like any other per-date failure (the generic `except Exception` below would log it and
            # immediately retry the NEXT date's allocation, hammering further large allocations instead of
            # backing off — the confirmed root cause of iter-7's 7+ minute health hang). Caught distinctly,
            # BEFORE the generic handler: stop this loop immediately (no further dates attempted) and force
            # freed memory back to the OS before returning to the caller's next independent block.
            except MemoryError as exc:
                logger.exception(
                    "ingest per-date coverage warm aborted at %s — memory pressure, stopping remaining "
                    "dates in this loop: %s", d, exc,
                )
                _release_process_memory()
                aborted_for_memory = True
                break
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
                logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
    # iter-8 AUDIT (B1 fix): the `_release_process_memory()` inside the loop above necessarily runs while
    # `cache_ctx`'s cache is still referenced by the enclosing `with`, so the single largest freeable block
    # cannot be trimmed there and the caller's NEXT independent warm block (market-phase, forward-
    # aggregates, drawdown) would start on the same un-trimmed arena — i.e. without the headroom this fix
    # exists to restore. Trim again AFTER the context manager exits. Own-cache (fallback) path: this
    # actually reclaims the ~1.5 GB block, mirroring `_do_backfill`'s own post-`prefilled_bar_cache`
    # release. Shared-cache path (iter-37, the common case): `prog._shared_bar_cache` still references the
    # cache at this point, so this trim reclaims only OTHER freed garbage — the shared block itself is
    # reclaimed later by `_refresh_ingest_aggregates`'s own release, after nulling that reference. Memory-
    # abort path only: the normal completion path keeps its pre-existing behavior byte-unchanged.
    if aborted_for_memory:
        _release_process_memory()


def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress) -> list[str]:
    """The ingest finalize hook (J-05). Each aggregate is refreshed independently (its own try/except: log
    + continue) so one aggregate's failure never prevents another from refreshing, and this function itself
    never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
    `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
    flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
    "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys",
    "drawdown_expectations", "index_series"]` ACTUALLY refreshed — never a fabricated category (mirrors
    the `omitted`/`passers` honesty convention already used elsewhere in this module).

    ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
    the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
    ..." line from the main scan loop is left honest/unchanged) at this function's own start, at each
    per-date step of the per-date COVERAGE warm loop (`_persist_per_date_coverage_snapshots`, threaded `prog`
    — iter-4 re-review CRITICAL: this loop's per-date `_compute_coverage_uncached` is the OTHER heavy half of
    the finalize tail, ~half of the ~729s), AND at each per-date step of the market-phase warm loop below —
    mirroring the main scan loop's own per-date heartbeat convention (`data_manager.py:2863`). Without ticks
    across BOTH per-date loops, `last_progress_at` freezes for the WHOLE finalize tail once the main scan
    completes (measured ~729s for a full rebuild, `reports/perf-budgets.md` Item L), and the frontend's
    stale-heartbeat flag (`job_progress.heartbeat_stale_seconds`) falsely renders "· possibly stalled" on a
    perfectly healthy job.

    ops-hardening iter-8 (J-05 REGRESSION fix): the four per-item warm loops this function drives directly
    or calls into (per-date coverage in `_persist_per_date_coverage_snapshots`, per-date market-phase, per-
    horizon forward-aggregates, per-claim drawdown-expectations) each catch `MemoryError` DISTINCTLY from
    their existing generic `except Exception: log + continue` — on the first `MemoryError`, that ONE loop
    stops attempting further items (never hammering the next item's allocation under real pressure),
    `_release_process_memory()` (`gc.collect()` + `malloc_trim`) runs before moving on, and the "actually
    warmed" honesty gate still reports the category when >= 1 item warmed before the abort. Every other
    loop's own try/except boundary — and the generic non-memory isolate-and-continue behavior within each
    loop — is unchanged. Root cause + live before/after measurement: `reports/perf-budgets.md` (Item L
    iter-8 update)."""
    refreshed: list[str] = []
    prog.tick()  # F1 fix: heartbeat-only stamp at the start of the finalize tail — see docstring above.

    if prog.new_snapshot_dates:
        # this run's own date-loop already created + committed these snapshots (scanner.persist_run_payload
        # / run_scan, inside `_do_backfill._persist`) before this hook runs — nothing further to compute
        # here; just acknowledge honestly that a fresh snapshot now exists.
        refreshed.append("latest_snapshot")

    # ops-hardening iter-37 (J-07 closure): attach `_do_backfill`'s already-loaded shared `_BarCache` (if
    # any — stashed on `prog`, see `_do_backfill`'s own docstring) to THIS session for the WHOLE finalize
    # tail below, not just the coverage sub-call. `bar_cache`/`prefilled_bar_cache` are RE-ENTRANT on
    # session id (see `bar_cache`'s own docstring): every warm call this function drives that internally
    # opens `with bar_cache(session):` on a cache miss — `market_phase.market_phase_cached` ->
    # `compute_market_phase`, and `forward_testing.compute_drawdown_expectations_cached` ->
    # `phase_context_by_date` -> `_causal_timeline`, both of which read the benchmark (SPY) series per
    # date/claim — finds THIS session's id already registered and transparently REUSES the one pre-loaded
    # cache instead of opening its own fresh (unprefilled) one and lazily reloading SPY on every call. That
    # was the remaining gap `test_kdate_backfill_loads_each_symbol_at_most_once` measured beyond the
    # coverage-snapshot double-load this iteration's other fix (`_persist_per_date_coverage_snapshots`)
    # closes: SPY has real bars, so it is already loaded from `_do_backfill`'s single whole-table prefill —
    # every OTHER caller just needs to find that cache instead of not knowing it exists. `_persist_per_date_
    # coverage_snapshots` below ALSO re-checks `prog._shared_bar_cache` itself for its own direct-call
    # test-compat fallback; attaching it here first is harmless/idempotent (`attach_shared_cache` is
    # re-entrant-safe on an already-registered session id — see its own docstring). A no-op (`nullcontext`)
    # when no shared cache was ever stashed (fetch/expand-only job, or a backfill with zero in-range
    # targets) — every warm call below then falls back to its own pre-iter-37 behavior, unchanged.
    shared = prog._shared_bar_cache
    cache_ctx = attach_shared_cache(session, shared) if shared is not None else nullcontext()
    # ops-hardening iter-38 (J-07 closure): an explicit, grep-able liveness assertion for THIS job — the
    # binding iter-37 lesson is that a drill on a conditional path (a stashed reference, an attach/fallback
    # context) must ASSERT the condition was live, never assume it from the lexical `with cache_ctx:` wrap
    # alone. One line per job, corroborable against a bounded range of the live `logs/backend.log`.
    # ops-hardening iter-39: downgraded `.warning` -> `.info`, its honest level — this is routine liveness
    # telemetry, not a warning condition. Safe now that `app.logging_config.configure_app_logging()` (wired
    # from `main.py` at import time) attaches a root-logger handler at INFO, so this no longer needs to
    # masquerade as a warning to reach `logs/backend.log` (iter-38's workaround; confirmed live via TC-12 —
    # see `test_data_manager.py` — that an `.info`-level record from this logger now reaches the configured
    # handler).
    logger.info(
        "J-07 finalize-tail cache_ctx liveness: job=%s resolved=%s",
        prog.job_id,
        "attach_shared_cache(live shared cache)" if shared is not None else "nullcontext(no shared cache)",
    )
    try:
        with cache_ctx:
            try:
                payload = refresh_coverage_snapshot(session, cfg)
                if payload is not None:
                    refreshed.append("coverage")
                    # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
                    # `membership_timeline_cached` internally as part of computing the payload just persisted
                    # above — warmed for free by that SAME call, never a second/separate derivation.
                    refreshed.append("membership_timeline")
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
                logger.exception("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)

            # iter-2 review (CRITICAL): also persist a per-date coverage_snapshot for every date THIS run
            # newly created, so the app-wide as-of switcher serves REAL coverage for each historical date
            # from storage — not the all-zero "not yet computed" sentinel. Still the "coverage" category
            # (no new one); own try/except (log + continue) so it never flips the job. Skips the current
            # stamp (persisted above) and is a no-op — no bar-cache load — for the common single-latest-
            # date backfill.
            try:
                _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates, prog)
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
                logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)

            market_phase_warmed = False
            for d in prog.new_snapshot_dates:
                prog.tick()  # F1 fix: per-date heartbeat stamp -- see function docstring above.
                try:
                    market_phase.market_phase_cached(session, d, cfg)
                    market_phase_warmed = True
                # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-date isolate-and-
                # continue below — a `MemoryError` stops THIS loop immediately (no further dates attempted)
                # and forces memory back to the OS, instead of hammering the next date's allocation under
                # pressure. `market_phase_warmed` already honestly reflects any dates that succeeded before
                # the abort.
                except MemoryError as exc:
                    logger.exception(
                        "ingest market-phase warm aborted at %s — memory pressure, stopping remaining dates "
                        "in this loop: %s", d, exc,
                    )
                    _release_process_memory()
                    break
                except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
                    logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
            if market_phase_warmed:
                refreshed.append("market_phase")

            # ops-hardening iter-5 (J-06): warm the CURRENT latest stored run's per-horizon forward-aggregate
            # cache (GET /api/backtest's `evidence_by_horizon`, ~34.77s pre-fix over all 5 configured horizons
            # — reports/perf-budgets.md). Unconditional (not gated on `prog.new_snapshot_dates`, unlike the
            # per-date coverage/market-phase loops above): the dataset-version stamp is GLOBAL, so ANY ingest
            # anywhere (even a historical-gap backfill far from the latest date) can invalidate the latest
            # run's already-cached aggregate — e.g. a backfilled EARLIER date's forward returns newly enter
            # the latest as-of's expanding "<= D" window. Warming only the ONE current-latest key (not every
            # historical as-of) mirrors the "research_hot_keys" default-key philosophy just below, not the
            # per-date coverage/market-phase sweep — each per-horizon compute can itself be as expensive as
            # the measured 34.77s violation, so sweeping every `new_snapshot_dates` entry here (as coverage/
            # market_phase do) would risk turning a full-universe rebuild's finalize tail into a multi-hour
            # operation instead of the intended fix. A user-navigated HISTORICAL as-of on `/backtest` still
            # computes-once-and-caches on first view (the same cold-miss contract EventStudyCache/
            # MarketPhaseCache already carry) — never pre-warmed here.
            try:
                latest_run_date = scanner._latest_stored_run_date(session)
                if latest_run_date is not None:
                    forward_aggregates_warmed = False
                    for h in cfg.walk_forward.horizons:
                        prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
                                     # compute here can take up to ~35s pre-warm; 5 sequential horizons could
                                     # otherwise freeze the heartbeat for minutes without a per-horizon tick).
                        # ops-hardening iter-8 (J-05 REGRESSION fix): a `MemoryError` on one horizon is caught
                        # HERE, distinctly, so a horizon that already succeeded before it is still honestly
                        # reported — the outer `except Exception` below (unchanged for every OTHER exception
                        # type) has no per-horizon granularity, so a non-memory failure still aborts the whole
                        # block exactly as before (no regression to that existing behavior). On MemoryError
                        # this loop stops immediately (no further horizons attempted) and forces memory back
                        # to the OS.
                        try:
                            # iter-39 (audit B3 / J-07 step 4): test-only injection point — a no-op unless
                            # this process was started with the env var naming this site. See
                            # `_fault_inject_memory_error`.
                            _fault_inject_memory_error("forward_aggregates")
                            forward_testing.forward_aggregates_ingest_cached(
                                session, h, cfg, as_of=latest_run_date
                            )
                            forward_aggregates_warmed = True
                        except MemoryError as exc:
                            logger.exception(
                                "ingest forward-aggregate warm aborted at horizon %s — memory pressure, "
                                "stopping remaining horizons in this loop: %s", h, exc,
                            )
                            _release_process_memory()
                            break
                    if forward_aggregates_warmed:
                        refreshed.append("forward_aggregates")
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
                logger.exception("ingest forward-aggregate warm failed (non-fatal): %s", exc)

            try:
                subjects = subject_catalog(cfg)
                if subjects:
                    # the SAME default (first catalog subject, config default_horizon, episodes view,
                    # all-history) a fresh `/research/event-study` page load with no query params would
                    # request — the one hot key worth warming at ingest (goal.md: "warm default
                    # (subject,horizon,all-history) keys").
                    event_study_cached(session, subjects[0]["key"], cfg.walk_forward.default_horizon, cfg)
                    refreshed.append("research_hot_keys")
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
                logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)

            # ops-hardening iter-13 (J-06, aggregation candidate #7): warm the SINGLE unparameterized default
            # hot key for `GET /api/indexes` (`range_key=cfg.index_chart.default_range`, `full=True` —
            # `PhaseCrossViewCard` on `/` and `IndexVendorPanel` on `/data` both request exactly this,
            # unparameterized, on mount). Mirrors the `research_hot_keys` block just above: a single-key warm,
            # unconditional (NOT gated on `prog.new_snapshot_dates`) because `IndexSeriesCache`'s
            # dataset-version stamp is scoped to the configured `index_chart.symbols`' bar freshness (not to
            # "this run's new snapshot dates") — ANY ingest that lands a bar for a configured index symbol,
            # anywhere, must invalidate it, mirroring `forward_aggregates`'s "the stamp is global" reasoning
            # above. Deferred import (not at module level): `indexes.py` already imports `load_seed_meta` FROM
            # this module at ITS OWN module level, so importing `indexes` back here at data_manager's module
            # scope would cycle; the deferred, function-scoped import breaks the cycle exactly like
            # `forward_aggregates_ingest_cached`'s own deferred `_dataset_version` import from `research.py`.
            #
            # iter-8 MemoryError-isolation convention: caught distinctly from the generic exception below,
            # stops immediately (a single key, not a loop — nothing further to attempt) and calls
            # `_release_process_memory()` before moving on to the next aggregate category. "index_series" is
            # appended ONLY when this call actually persisted a new row this run (`persisted` is False on a
            # cache HIT — an honest "was skipped" omission, never a fabricated refresh, mirroring every other
            # category's honesty gate above).
            try:
                # ops-hardening iter-44 AUDIT (B2): the deferred import stays INSIDE this block's guards.
                # Sitting one line above the `try`, it was the only unguarded statement left in this
                # otherwise fully-isolated finalize sequence — and importing a not-yet-loaded module
                # allocates (read + compile of `indexes.py`), so under an exhausted `ulimit -v` it raised
                # `MemoryError` and escaped `_refresh_ingest_aggregates` entirely, breaking its documented
                # "log + continue, never raise" contract. Live-captured by
                # `test_ingest_finalize_memory_pressure.py`'s child probe (`<frozen
                # importlib._bootstrap_external>:1191 in get_data`, returncode 1). Import position is
                # unchanged in every other respect — still deferred, still breaking the module-load cycle.
                from app.engine import indexes  # deferred: see comment above (breaks a module-load cycle)

                _, index_series_persisted = indexes.index_series_cached_with_status(session, cfg)
                if index_series_persisted:
                    refreshed.append("index_series")
            except MemoryError as exc:
                logger.exception(
                    "ingest index-series warm aborted — memory pressure: %s", exc,
                )
                _release_process_memory()
            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
                logger.exception("ingest index-series warm failed (non-fatal): %s", exc)

            # ops-hardening iter-7 (J-06 closeout, audit B1): warm the per-claim `drawdown_expectations`
            # EventStudyCache view slot — the SAME cache slot `build_evidence_payload` looks up lazily via
            # `forward_testing.compute_drawdown_expectations_cached` on a live `/api/evidence` request.
            # Without this warm, the FIRST `/evidence` view after any ingest pays a per-claim cold-miss
            # compute (measured ~73s on the grown live dev DB, reports/perf-budgets.md iter-6 CORRECTION).
            # Mirrors the `research_hot_keys` block just above: its own top-level try/except (a missing/
            # corrupt ledger file degrades to zero warm calls — an honest omission, never an exception that
            # aborts the rest of this finalize hook), the SAME `type == FORWARD_WALK_TYPE` filter `build_
            # evidence_payload` already applies (a forward-walk record re-scores an existing claim — it is
            # not itself a claim to warm a panel for), and the SAME `entry.get("claim")` extraction `evidence.
            # _claim_row` uses (so the cache subject hash matches exactly what `/api/evidence` looks up). A
            # `prog.tick()` heartbeat stamps before each claim's warm call (mirrors the `forward_aggregates`
            # per-horizon tick above), and each claim's own try/except (log + continue) means one
            # unresolvable/erroring claim never blocks another or fails the ingest job.
            try:
                ledger_entries = read_entries(evidence.resolve_ledger_path())
            except Exception as exc:  # noqa: BLE001 — non-fatal: a missing/corrupt ledger degrades to zero
                                       # warm calls
                logger.exception("ingest drawdown-expectations ledger read failed (non-fatal): %s", exc)
                ledger_entries = []

            drawdown_warmed = False
            for entry in ledger_entries:
                if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
                    continue
                claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
                prog.tick()  # heartbeat stamp before each claim's warm call — see docstring above.
                try:
                    # iter-39 (audit B3 / J-07 step 4): test-only injection point — see
                    # `_fault_inject_memory_error` (a no-op unless this process names this site in the env).
                    _fault_inject_memory_error("drawdown_expectations")
                    result = forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)
                    # gate on an ACTUAL non-None payload (never just "the call didn't raise") — an
                    # out-of-scope horizon or an unresolvable cohort returns None honestly and must NOT be
                    # reported as refreshed (mirrors the `market_phase`/`research_hot_keys` "actually did
                    # something" convention above).
                    if result is not None:
                        drawdown_warmed = True
                # ops-hardening iter-8 (J-05 REGRESSION fix): distinct from the generic per-claim isolate-and-
                # continue below — a `MemoryError` stops THIS loop immediately (no further claims attempted)
                # and forces memory back to the OS, instead of hammering the next claim's allocation under
                # pressure. `drawdown_warmed` already honestly reflects any claim that succeeded before the
                # abort.
                except MemoryError as exc:
                    logger.exception(
                        "ingest drawdown-expectations warm aborted — memory pressure, stopping remaining "
                        "claims in this loop: %s", exc,
                    )
                    _release_process_memory()
                    break
                except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next claim
                    logger.exception(
                        "ingest drawdown-expectations warm failed for one claim (non-fatal): %s", exc
                    )
            if drawdown_warmed:
                refreshed.append("drawdown_expectations")
    finally:
        # ops-hardening iter-37 (J-07 closure): `_do_backfill` deferred releasing its shared whole-table
        # `_BarCache` (~1.13 GB) until THIS point — every warm call in the `with cache_ctx:` block above is
        # its ONLY other consumer for this job (reused via re-entrant `bar_cache`/`attach_shared_cache`,
        # zero re-scan). Release it back to the OS here, exactly once, regardless of whether any individual
        # warm above succeeded or raised — mirrors `_do_backfill`'s own release discipline (iter-27) so a
        # second consecutive rebuild in the same long-lived process still starts lean. Null the reference
        # FIRST so `gc.collect()` can actually reclaim the block (a lingering reference on `prog` would
        # defeat `_release_process_memory()` entirely). A no-op when no shared cache was ever stashed (a
        # fetch/expand-only job never reaches this function at all; a backfill/rebuild with zero in-range
        # targets never builds one).
        if prog._shared_bar_cache is not None:
            prog._shared_bar_cache = None
            _release_process_memory()

    return refreshed


# --------------------------------------------------------------------------------------------------
# J-35 expand — screen the committed pool over a market-cap-capable source, grow universe.json
# --------------------------------------------------------------------------------------------------
def _write_universe_csv(seed_dir: Path, symbol: str, bars: list[DailyPrice]) -> None:
    """Write one passer's committed per-symbol price CSV (the same frozen, internally split/div-adjusted
    shape the offline screen + SeedProvider use). The bars are REAL committed `DailyPrice` rows read back
    from the DB — nothing is fabricated."""
    prices_dir = seed_dir / "prices"
    prices_dir.mkdir(parents=True, exist_ok=True)
    path = prices_dir / symbol_to_filename(symbol)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for bar in bars:
            writer.writerow({
                "date": bar.date.isoformat(), "open": bar.open, "high": bar.high,
                "low": bar.low, "close": bar.close, "volume": bar.volume,
            })


_CAP_NOT_PREFETCHED = object()  # sentinel: this candidate's cap was NOT supplied by a batched pre-fetch


def _screen_one_candidate(
    session: Session,
    cfg: Config,
    provider: PriceProvider,
    asof: date_cls,
    symbol: str,
    *,
    scrub: Callable[[str], str],
    prefetched_cap: object = _CAP_NOT_PREFETCHED,
) -> tuple[Optional[dict], Optional[str]]:
    """Screen ONE pool candidate against REAL committed bars + a REAL market-cap reference, returning
    either `(member_dict, None)` for a passer or `(None, reason)` for an omission. The reference values
    come from stored `DailyPrice` bars (the OHLCV fetch already INSERTed them); the cap comes from either
    a BATCHED pre-fetch (`prefetched_cap` — Yahoo's cookie+crumb `get_market_caps`, J-84) when supplied,
    or the per-symbol `get_market_cap` capability otherwise (the per-symbol providers, e.g. Tiingo). A
    fetch failure / empty series / missing cap / threshold failure is an OMISSION (a reason string) —
    never a fabricated member/cap/bar. Re-raises `RateLimitError` so the caller pauses the WHOLE expand
    gracefully (the live feed is rate-limited)."""
    filters = cfg.universe.filters
    bars = bars_asof(session, symbol, asof)
    if not bars:
        return None, "empty_series"
    reference_close = bars[-1].close
    adv_rows = bars[-filters.adv_window_days:]
    adv_dollar = sum(b.close * b.volume for b in adv_rows) / len(adv_rows)
    if prefetched_cap is not _CAP_NOT_PREFETCHED:
        # the batched cookie+crumb pre-fetch already resolved this symbol's cap (a systemic auth/limit
        # failure was raised UPFRONT before the loop, pausing the whole expand — so here it is a REAL cap
        # or an honest per-candidate absence (`None` → `no_market_cap`), never fabricated.
        market_cap = prefetched_cap  # type: ignore[assignment]
    else:
        try:
            market_cap = provider.get_market_cap(symbol)  # REAL cap or None — never fabricated
        except RateLimitError:
            raise  # persistent rate-limit on the cap feed → caller pauses the expand resumable
        except ProviderUnavailableError as exc:
            return None, scrub(f"market_cap_fetch_failed: {exc}")
    reasons = screen_reasons(
        reference_close, adv_dollar, market_cap,
        min_price=filters.min_price, min_dollar_vol=filters.min_dollar_vol,
        min_market_cap=filters.min_market_cap,
    )
    if reasons:
        return None, "; ".join(reasons)
    return {
        "symbol": symbol,
        "market_cap": round(float(market_cap), 2),
        "reference_close": round(float(reference_close), 4),
        "adv_dollar": round(float(adv_dollar), 2),
        "bars": len(bars),
        "first": bars[0].date.isoformat(),
        "last": bars[-1].date.isoformat(),
    }, None


def _write_expand_artifacts(
    seed_dir: Path, cfg: Config, members: list[dict], omitted: list[dict], asof: date_cls
) -> None:
    """Write the canonical universe artifacts the running app READS (J-22 single source): `universe.json`
    (the per-member screen-pass record + the omitted-with-reason list), refreshed `meta.json`, and each
    passer's per-symbol price CSV. Matches the member/omitted record shape written by the offline
    `screen_universe.screen()` so the two writers stay interchangeable (one canonical artifact)."""
    filters = cfg.universe.filters
    members = sorted(members, key=lambda m: m["symbol"])
    universe = {
        "membership_rule": ("Union of the S&P 500 and Nasdaq-100 index constituents (real memberships) "
                            "and the prior committed universe, then screened by the config "
                            "liquidity/price/market-cap filters (universe.filters)."),
        "screen_thresholds": {
            "min_market_cap": filters.min_market_cap,
            "min_dollar_vol": filters.min_dollar_vol,
            "min_price": filters.min_price,
            "adv_window_days": filters.adv_window_days,
        },
        "source": {
            "ohlcv": "Data Manager expand job (chunked/resumable import via the config-selected source)",
            "market_cap": "the config-selected source's market-cap reference capability (real data only)",
        },
        "generated_at": _utcnow().isoformat(),
        "window": {"asof": asof.isoformat()},
        "member_count": len(members),
        "members": members,
        "omitted_count": len(omitted),
        "omitted": omitted,
    }
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "universe.json").write_text(json.dumps(universe, indent=2) + "\n")

    meta = {
        "source": "Data Manager expand job (J-35) — chunked/resumable import + config screen",
        "note": ("REAL EOD OHLCV + a REAL market-cap reference; the universe is the config-recorded screen "
                 "(universe.filters) applied to the committed candidate pool; see universe.json for "
                 "per-member screen-pass values and omitted candidates."),
        "generated_at": _utcnow().isoformat(),
        "window": {"asof": asof.isoformat()},
        "universe_members": len(members),
        "omitted_candidates": len(omitted),
    }
    (seed_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")


def _run_expand_screen(
    session: Session,
    cfg: Config,
    prog: JobProgress,
    provider: PriceProvider,
    pool: list[dict],
    *,
    scrub: Callable[[str], str],
    seed_dir: Path,
) -> None:
    """The screen half of an expand job (run AFTER the chunked OHLCV fetch stored the pool's bars). For
    each pool candidate, screen it against its REAL committed bars + a REAL market-cap reference via the
    SINGLE `screen_reasons` predicate; accumulate passers (members) and omissions (with reason); then
    write `universe.json` / per-symbol CSVs / `meta.json`. A persistent `RateLimitError` on the cap feed
    pauses the expand gracefully `resumable` (the durable checkpoint already records the OHLCV resume
    point). Nothing is fabricated — a failed/missing candidate is OMITTED with a reason."""
    asof = latest_data_date(session)
    if asof is None:
        return  # no price data — the POST handler already 503s before we get here
    members: list[dict] = []
    sector_by_symbol = {row["symbol"]: row.get("sector") for row in pool}
    source_by_symbol = {row["symbol"]: row.get("source") for row in pool}
    pool_symbols = [row["symbol"] for row in pool]

    # J-84: BATCHED market-cap pre-fetch (cookie+crumb acquired ONCE, reused). A provider that supports
    # batching (Yahoo) returns a {symbol: cap|None} map and raises `RateLimitError` UPFRONT on a SYSTEMIC
    # auth/limit failure (cookie/crumb step or a 401/429 on the batched quote) — so a whole-batch auth
    # outage pauses the expand resumable WITHOUT recording every candidate omitted. A provider with no
    # batch capability returns `None` → the per-candidate `get_market_cap` path is used (unchanged).
    try:
        cap_map = provider.get_market_caps(pool_symbols)
    except RateLimitError:
        prog.status = "resumable"
        prog.message = _final_summary(prog)
        return

    for row in pool:
        symbol = row["symbol"]
        try:
            if cap_map is not None:
                member, reason = _screen_one_candidate(
                    session, cfg, provider, asof, symbol, scrub=scrub,
                    prefetched_cap=cap_map.get(symbol),
                )
            else:
                member, reason = _screen_one_candidate(session, cfg, provider, asof, symbol, scrub=scrub)
        except RateLimitError:
            # the (per-symbol) cap feed is persistently rate-limited → pause the expand resumable
            # (honest, non-fab). The batched path raises upfront above; this covers the per-symbol path.
            prog.status = "resumable"
            prog.message = _final_summary(prog)
            return
        if member is not None:
            member["sector"] = sector_by_symbol.get(symbol)
            member["source"] = source_by_symbol.get(symbol)
            members.append(member)
            prog.passers += 1
            _write_universe_csv(seed_dir, symbol, bars_asof(session, symbol, asof))
        else:
            _record_omitted(prog, symbol, reason or "omitted")
        prog.message = _expand_message(prog)
    _write_expand_artifacts(seed_dir, cfg, members, list(prog.omitted), asof)
    prog.message = _expand_message(prog)


def _expand_message(prog: JobProgress) -> str:
    return (
        f"expand: {prog.passers} passers, {prog.omitted_total} omitted "
        f"(of {prog.symbols_total} candidates)"
    )


def _final_status(prog: JobProgress) -> str:
    """Combine the per-phase outcomes into the job status. A fetch that fully fails (every symbol) with
    no backfill work done is `failed`; any partial success is `partial`; otherwise `ok`. An expand is
    graded on its OHLCV-fetch outcome (the screen step is deterministic): the whole pool failing to fetch
    → `failed`; some symbols failing → `partial`; else `ok` (an all-threshold-omitted expand is still a
    SUCCESSFUL honest screen — `ok`, not failed)."""
    statuses: list[str] = []
    if prog.kind in _FETCH_KINDS or prog.kind in _EXPAND_KINDS:
        if prog.symbols_total == 0:
            statuses.append("ok")
        elif prog.symbols_ok == 0:
            statuses.append("failed")
        elif prog.symbols_failed > 0:
            statuses.append("partial")
        else:
            statuses.append("ok")
    if prog.kind in _BACKFILL_KINDS or prog.kind in _REBUILD_KINDS:
        # J-67: a single date's failure is ISOLATED (recorded per-date) — the backfill/rebuild ends
        # `partial` (others completed), never aborting the whole stage. With NO per-date failures it is
        # `ok`. A whole-stage exception (e.g. the trading-calendar read itself) is still graded `failed` by
        # the `_run_job` except-handler separately. A rebuild grades on its create-once backfill outcome.
        statuses.append("partial" if prog.date_failures else "ok")
    if statuses == ["failed"]:
        return "failed"
    if "failed" in statuses or "partial" in statuses:
        return "partial"
    return "ok"


def _final_summary(prog: JobProgress) -> str:
    parts: list[str] = []
    if prog.kind in _FETCH_KINDS:
        parts.append(
            f"fetch: {prog.symbols_ok}/{prog.symbols_total} symbols ok, "
            f"{prog.symbols_failed} failed, {prog.bars_fetched} new bars"
        )
    if prog.kind in _EXPAND_KINDS:
        parts.append(
            f"expand: {prog.passers} passers, {prog.omitted_total} omitted "
            f"of {prog.symbols_total} candidates ({prog.bars_fetched} new bars)"
        )
    if prog.kind in _BACKFILL_KINDS or prog.kind in _REBUILD_KINDS:
        label = "rebuild" if prog.kind in _REBUILD_KINDS else "backfill"
        backfill = (
            f"{label}: {prog.snapshots_created} snapshots over {prog.dates_total} dates, "
            f"{prog.forward_returns_inserted} forward returns"
        )
        if prog.date_failures:  # J-67: surface the per-date failures honestly on a `partial` job
            failed_dates = ", ".join(f["date"] for f in prog.date_failures[:5])
            more = "…" if len(prog.date_failures) > 5 else ""
            backfill += f" ({len(prog.date_failures)} date(s) failed: {failed_dates}{more})"
        parts.append(backfill)
    summary = "; ".join(parts) if parts else "no work performed"
    if prog.status == "resumable":  # J-34: a graceful 429 pause — surface the resume point honestly
        remaining = max(prog.symbols_total - prog.symbols_ok - prog.symbols_failed, 0)
        return (
            f"rate-limited — resumable at chunk {prog.chunk_index}/{prog.chunk_total} "
            f"({remaining} symbols remaining); {summary}"
        )
    return summary


def _provider_label(prog: JobProgress, cfg: Config) -> str:
    """The provider recorded on the run row: the CHOSEN import source id when a fetch was involved (J-33;
    the source is not secret — the pasted key is never recorded), else the offline default provider (the
    backfill reads the committed seed). Falls back to the config `default_source` when a fetch job was
    created without an explicit source. An expand also fetches → it records its chosen source."""
    if prog.kind in _FETCH_KINDS or prog.kind in _EXPAND_KINDS:
        return prog.source or cfg.data_manager.default_source
    return cfg.provider


def _run_detail(prog: JobProgress) -> dict:
    """The structured detail JSON encoded into a `DataProviderRun.message` — descriptive job-control
    values, NEVER a key (anti-goal: keys are env-or-session, never persisted)."""
    _is_backfill_like = prog.kind in _BACKFILL_KINDS or prog.kind in _REBUILD_KINDS
    # ops-hardening iter-1: serve the breakdown ONLY once `_do_backfill` has actually computed it. Two
    # rows are persisted BEFORE the backfill stage runs its computation and carry the JobProgress defaults
    # (calendar_days == 0): the `running` row `_create_run_record` writes at job start, and the
    # `interrupted` row the boot sweep freezes from it when a job's process dies mid-run. Since
    # `calendar_days == (end - start).days + 1 >= 1` for EVERY real requested range, calendar_days == 0
    # uniquely marks "breakdown not computed yet" → serve null there (the frontend `BackfillBreakdown`
    # suppresses an all-null breakdown) rather than a fabricated "0 calendar days · 0 already snapshotted ·
    # 0 non-trading" for an interrupted run whose range was really hundreds of days (AG-3: never surface a
    # number that is not the engine's real computation; matches the fetch/seed-load null convention).
    _breakdown_computed = _is_backfill_like and prog.calendar_days > 0
    return {
        "kind": prog.kind,
        "start": prog.start.isoformat(),
        "end": prog.end.isoformat(),
        "snapshots_created": prog.snapshots_created,
        "dates_done": prog.dates_done,
        "dates_total": prog.dates_total,
        "forward_returns_inserted": prog.forward_returns_inserted,
        "bars_fetched": prog.bars_fetched,
        # ops-hardening iter-1 (J-01) — the run-summary exclusion breakdown on the permanent audit row:
        # present for backfill/both/rebuild kinds only once actually computed (None for fetch/expand and
        # for a not-yet-computed running/interrupted row — see `_breakdown_computed` above), mirroring the
        # passers/omitted_total nullability. Read directly off `prog` — the SAME single computation
        # `_do_backfill` already performed; never re-derived here.
        "calendar_days": prog.calendar_days if _breakdown_computed else None,
        "non_trading_days": prog.non_trading_days if _breakdown_computed else None,
        "already_snapshotted": prog.already_snapshotted if _breakdown_computed else None,
        "error_other": prog.error_other if _breakdown_computed else None,
        # ops-hardening iter-2 (J-05): the finalize-hook output on the permanent audit row — present for
        # backfill/both/rebuild kinds ONLY once the finalize hook has actually run (matching the SAME
        # `_breakdown_computed` gate the breakdown fields above use, PLUS an explicit non-empty check, so a
        # not-yet-computed/interrupted row, and a fetch/expand row — for which `_breakdown_computed` is
        # already False — all serve `null`, never a fabricated list; AG-3).
        "aggregates_refreshed": (
            prog.aggregates_refreshed if (_breakdown_computed and prog.aggregates_refreshed) else None
        ),
        # J-35 expand: the screen outcome on the audit row (descriptive job-control values — NOT a recompute
        # of any canonical score/return/bucket). Present only for an expand kind.
        "passers": prog.passers if prog.kind in _EXPAND_KINDS else None,
        "omitted_total": prog.omitted_total if prog.kind in _EXPAND_KINDS else None,
        # J-53: the per-stage operational timings on the permanent audit row (descriptive metadata, NOT a
        # canonical score) so a completed job's timings survive past the in-memory registry. Only stages
        # that actually ran are present (a stage that never ran is absent — never a fabricated zero).
        "stages": {k: dict(v) for k, v in prog.stages.items()},
        # J-67: per-date backfill failures (honest error + which dates) on a `partial` job.
        "date_failures": [dict(f) for f in prog.date_failures],
        # J-59: which pipeline stages completed (so a `failed`/`interrupted` record stays honest about how
        # far it got).
        "completed_stages": list(prog.completed_stages),
        # iter-43 AUDIT (B2): serve `prog.message` on a terminal FAILED row. Provably a no-op for every
        # pre-existing path: `_run_job`'s `finally` assigns `prog.message = _final_summary(prog)` and then
        # calls `_finalize_run_record` without mutating any field `_final_summary` reads, so the two
        # expressions are the SAME string there; the only other callers (`_create_run_record`,
        # `_checkpoint_run_record`) serialize a still-`running` job, which this guard never matches. What
        # it DOES carry through is `_fail_unlaunched_job`'s reason line — the thread-launch failure TC-3/
        # TC-4 require the run-history row's message to name, which `_final_summary` (a summary of WORK
        # DONE) structurally cannot express for a job that never started.
        "summary": prog.message if (prog.status == "failed" and prog.message) else _final_summary(prog),
    }


def _create_run_record(engine: Engine, cfg: Config, prog: JobProgress) -> None:
    """J-60 — create the job's run-history record IMMEDIATELY at job start (status `running`, carrying
    kind / date range / source, NO finished_at) so the job appears in Run history from the moment it
    starts. INSERTs ONE row keyed by `job_id`; the terminal transition (`_finalize_run_record`) UPDATEs
    THIS SAME row (one record per job, one terminal transition). The key is NEVER persisted onto it."""
    with Session(engine) as session:
        session.add(
            DataProviderRun(
                provider=_provider_label(prog, cfg),
                started_at=prog.started_at,
                finished_at=None,
                symbols_ok=prog.symbols_ok,
                symbols_failed=prog.symbols_failed,
                status="running",
                message=json.dumps(_run_detail(prog)),
                job_id=prog.job_id,
            )
        )
        session.commit()


def _open_run_record(session: Session, job_id: Optional[str]) -> Optional[DataProviderRun]:
    """The OPEN (non-terminal) run-history row for `job_id` — the `running` or `resumable` record this job
    is currently working under, newest first. None when there is none (a fresh job, or all rows terminal)."""
    if not job_id:
        return None
    return session.exec(
        select(DataProviderRun)
        .where(DataProviderRun.job_id == job_id)
        .where(DataProviderRun.status.in_(["running", "resumable"]))
        .order_by(DataProviderRun.id.desc())
    ).first()


def _has_open_run_record(engine: Engine, job_id: Optional[str]) -> bool:
    """True iff an OPEN (running/resumable) run-history row exists for `job_id` — so a resume reuses it
    instead of writing a second record."""
    with Session(engine) as session:
        return _open_run_record(session, job_id) is not None


# ops-hardening iter-9 (F1) — how often a long-running backfill re-writes its CURRENT progress onto its
# OPEN run-history row. One small UPDATE per interval bounds the write amplification regardless of how
# fast dates complete, while keeping a killed job's persisted progress at most one interval stale.
#
# iter-40 (iter-39/w, AG-3 checkpoint honesty): tightened 10.0 -> 1.0. At 10s, a job whose ENTIRE run
# completes faster than one interval only ever writes its first checkpoint (the pre-loop plan write, or
# the first per-date call — whichever lands first after process start, since `time.monotonic()` at boot
# is already far past 10s) and then throttles away every later per-date call for the rest of the job, so
# a `kill -9` anywhere after that leaves the persisted row stuck near the START regardless of how far the
# job really got — iter-39's live drill measured 18/18 dates done in memory against a persisted row still
# reading single digits, an order-of-magnitude gap (`runs/goal-ops-hardening-iter-39/live-restart/
# kill-test-mid-flight-state.json` vs `pre-kill-runs-state.json`). At ~1-2.5s observed per-date wall time
# (`kill-test-mid-flight-state.json`: 18 dates / 45.18s elapsed), a 1.0s interval checkpoints roughly once
# per date instead of once per 4-10 dates — the SAME throttled-write mechanism (unchanged call sites,
# unchanged `message` field, unchanged `_run_detail()` serializer), just dense enough that a fast job's
# kill-time progress is never stale by more than about one date. 1.0s also matches `job_progress.
# poll_interval_seconds` (no UI consumer reads the row faster than that anyway, so sub-second precision
# would buy nothing); write amplification stays bounded to at most one UPDATE per second per running job.
_RUN_RECORD_CHECKPOINT_INTERVAL_S = 1.0

# ops-hardening iter-41 (D9, dev Known Issue #2 from iter-40's own handoff) — a COUNT-based floor added
# to the time-based throttle above: even an EXTREMELY fast per-date compute (iter-40's own live drill
# observed a burst rate of ~120-140 ms/date, well under the 1.0s interval) forces a durable checkpoint
# write at least once every this-many completed dates, regardless of how little wall-clock time has
# elapsed. Same throttled writer, same `message` field, same `_run_detail()` serializer — this only
# widens WHEN a write is forced, never what gets written. 5 mirrors the density iter-40's own tightened
# 1.0s interval already achieves at a typical ~1-2.5s/date rate (roughly one checkpoint every 1-2 dates
# there); at a pathologically fast sub-200ms/date rate this floor caps the worst-case staleness at 5
# dates instead of the ~5-8 dates the time-only throttle would otherwise allow (1.0s / 0.14s ~= 7).
_RUN_RECORD_CHECKPOINT_DATE_FLOOR = 5


def _checkpoint_run_record(engine: Engine, prog: JobProgress) -> None:
    """ops-hardening iter-9 (F1 — J-04 step 6): freeze the job's CURRENT progress onto its OPEN
    (`running`/`resumable`) run-history row, so a process that dies mid-run leaves an `interrupted` row
    carrying its LAST PERSISTED PROGRESS.

    Why this exists: the numeric detail fields were previously written into the persisted row exactly
    ONCE, by `_finalize_run_record` — which a `kill -9`/host reset never reaches. The boot sweep
    (`sweep_orphaned_runs`) only flips `status`/`finished_at` and never touches `message`, so an
    interrupted row's detail stayed at its creation-time defaults and rendered as "0 snapshots · 0 trading
    days in range" no matter how far the job actually got (live-verified: J-04 step 6 / UT-10).

    Contract: this writes ONLY `message` (the detail JSON `_finalize_run_record` and `_create_run_record`
    already serialize — one representation, no second derivation). It never sets `status`/`finished_at`,
    so the row stays OPEN and the boot sweep can still claim it, and it never INSERTs — a job with no open
    row (already terminal) is a silent no-op. Throttled to one write per
    `_RUN_RECORD_CHECKPOINT_INTERVAL_S` — OR forced on every `_RUN_RECORD_CHECKPOINT_DATE_FLOOR`th call
    regardless of elapsed time (ops-hardening iter-41, D9: the time-based throttle alone lets an
    extremely fast per-date compute run several dates between writes; this count-based floor bounds that
    OTHER axis of staleness). Best-effort telemetry: a write failure is logged and swallowed, never
    propagated into the backfill loop (the job's own outcome must not depend on its progress
    bookkeeping)."""
    now = time.monotonic()
    prog._dates_since_checkpoint += 1
    time_due = (now - prog._last_checkpoint_monotonic) >= _RUN_RECORD_CHECKPOINT_INTERVAL_S
    count_due = prog._dates_since_checkpoint >= _RUN_RECORD_CHECKPOINT_DATE_FLOOR
    if not time_due and not count_due:
        return
    prog._last_checkpoint_monotonic = now
    prog._dates_since_checkpoint = 0
    # Keep the breakdown internally consistent at the checkpoint instant: `error_other` is derived from
    # the SAME uncapped `date_failures_total` the end of `_do_backfill` uses (one derivation, applied
    # earlier), so a checkpointed row never shows failures in its summary and 0 in its breakdown.
    prog.error_other = prog.date_failures_total
    try:
        with Session(engine) as session:
            row = _open_run_record(session, prog.job_id)
            if row is None:
                return
            row.message = json.dumps(_run_detail(prog))
            session.add(row)
            session.commit()
    except Exception as exc:  # noqa: BLE001 — progress bookkeeping must never fail the job
        logger.warning("run-record progress checkpoint failed for job %s (non-fatal): %s", prog.job_id, exc)


def _finalize_run_record(engine: Engine, cfg: Config, prog: JobProgress) -> None:
    """J-60 — close the job's run-history record with ONE honest transition. UPDATEs the OPEN (running/
    resumable) row this job runs under (found by `job_id`) to its new status / finished_at / counts /
    summary — one record per attempt, never overwriting an already-terminal row. A `resumable` pause UPDATEs
    the open row to `resumable` (keeping it open + finished_at NULL) so it shows that way and the boot sweep
    (which only touches `running`) leaves it alone; the eventual completed resume closes THIS SAME row. If
    no open row exists (a legacy/edge path), INSERT a fresh row so the audit stays complete. Key never
    persisted."""
    detail = _run_detail(prog)
    with Session(engine) as session:
        row = _open_run_record(session, prog.job_id)
        if row is not None:
            row.status = prog.status
            row.finished_at = prog.finished_at
            row.symbols_ok = prog.symbols_ok
            row.symbols_failed = prog.symbols_failed
            row.message = json.dumps(detail)
            session.add(row)
        else:
            session.add(
                DataProviderRun(
                    provider=_provider_label(prog, cfg),
                    started_at=prog.started_at,
                    finished_at=prog.finished_at,
                    symbols_ok=prog.symbols_ok,
                    symbols_failed=prog.symbols_failed,
                    status=prog.status,
                    message=json.dumps(detail),
                    job_id=prog.job_id,
                )
            )
        session.commit()


def sweep_orphaned_runs(engine: Engine) -> int:
    """J-60 boot sweep — mark any orphaned `running` `DataProviderRun` rows as `interrupted` (an honest
    terminal state) so a job whose process died mid-run never lingers as a stuck `running` forever and
    never vanishes from history. A fresh process boot owns NO in-flight jobs (the in-memory `_JOBS`
    registry is empty), so ANY `running` row found at boot is by definition orphaned from a prior, now-dead
    process — swept to `interrupted`. Idempotent + non-fatal. Returns the number swept. Never fabricates a
    status; never touches an immutable snapshot/forward-return row."""
    swept = 0
    with Session(engine) as session:
        rows = session.exec(
            select(DataProviderRun).where(DataProviderRun.status == "running")
        ).all()
        now = _utcnow()
        for row in rows:
            row.status = "interrupted"
            if row.finished_at is None:
                row.finished_at = now
            session.add(row)
            swept += 1
        if swept:
            session.commit()
    return swept


def _resolve_live_provider(
    cfg: Config, source: Optional[str], api_key: Optional[str]
) -> PriceProvider:
    """Build the live client for a fetch: resolve the job `source` (or the config default) against the
    catalog, resolve its key (env or the pasted session key — request-only), and `make_provider`. The key
    is used in-memory only and never persisted."""
    resolved_source = source or cfg.data_manager.default_source
    entry = cfg.data_manager.provider_by_id(resolved_source)
    key = resolve_provider_key(entry, api_key) if entry is not None else api_key
    return make_provider(resolved_source, api_key=key)


def _resolved_key(cfg: Config, source: Optional[str], api_key: Optional[str]) -> Optional[str]:
    """The effective key for a job's source (used ONLY to build the defense-in-depth error scrubber — it
    is never stored/logged). None when the source needs no key or none is available."""
    entry = cfg.data_manager.provider_by_id(source) if source else None
    return resolve_provider_key(entry, api_key) if entry is not None else None


def _run_job(
    prog: JobProgress,
    *,
    cfg: Config,
    eng: Engine,
    provider: Optional[PriceProvider],
    api_key: Optional[str],
    sleep_fn: Callable[[float], None],
    is_resume: bool,
    seed_dir: Path = DEFAULT_SEED_DIR,
    symbols_override: Optional[list[str]] = None,
) -> dict:
    """The shared worker body for a fresh job (`is_resume=False`) and a resume (`is_resume=True`). Opens
    its OWN DB session (never the request's). The live FETCH is CHUNKED + checkpointed; a persistent 429
    pauses GRACEFULLY in a `resumable` state (the checkpoint carries it across a restart) WITHOUT raising
    or fabricating. A resume rebuilds the SAME deterministic plan from the stored symbol list and runs
    from the checkpoint's `next_chunk_index` — re-fetching/duplicating nothing.

    `api_key` is the SESSION-ONLY pasted key (request-only): a LOCAL argument resolved into the provider
    and the error scrubber here, NEVER written to the job registry, the checkpoint, the persisted run, the
    detail JSON, or any log (anti-goal: Import keys are env-or-session, never persisted)."""
    scrub = _make_scrubber(_resolved_key(cfg, prog.source, api_key))
    paused = False
    is_expand = prog.kind in _EXPAND_KINDS
    # J-59: a `both`/`backfill` resume whose FETCH stage already completed routes STRAIGHT to the backfill
    # stage with ZERO provider calls — the fetch stage is skipped entirely.
    skip_fetch = is_resume and "fetch" in prog.completed_stages
    # Both a generic FETCH and an EXPAND run the SAME chunked/resumable OHLCV fetch engine (J-34, reused
    # not forked); they differ only in the symbol set (all seed symbols vs the committed POOL) and in the
    # EXTRA screen step expand runs afterward.
    pool: list[dict] = []
    # iter-35 (J-21/B-304): the bounded per-symbol accumulator `_run_chunked_fetch` fills with this job's
    # RAW freshly-fetched bars (tail-trimmed to `overlap_days`) for the post-fetch drift check below. Left
    # `None` when the feature is config-disabled, so `_run_chunked_fetch` skips the accumulation entirely.
    overlap_sink: Optional[dict[str, list]] = {} if cfg.data_quality.drift.enabled else None
    checkpoint: Optional[ImportCheckpoint] = None  # hoisted: an expand finalizes it AFTER the screen step
    backfill_failed = False  # J-59: a `both`/`backfill` backfill-stage failure (drives failed_backfill)
    # J-60: create the run-history record IMMEDIATELY (status `running`) so the job appears in Run history
    # from the moment it starts. The SAME row is UPDATEd to its terminal state in `finally` (one record,
    # one transition). A RESUME of a still-OPEN record (a `resumable` 429-pause whose row stayed
    # `running`/`resumable`) reuses that row; a resume of an ALREADY-TERMINAL record (a `failed_backfill`
    # whose `both`-job row finalized to `failed`) is a fresh attempt and writes its OWN honest record
    # (like J-38 Retry) — so the audit trail of every attempt stays complete.
    if not is_resume or not _has_open_run_record(eng, prog.job_id):
        try:
            _create_run_record(eng, cfg, prog)
        except Exception as exc:  # noqa: BLE001 — a bookkeeping failure must not crash the worker
            _record_error(prog, scrub(f"failed to create run record: {exc}"))
    try:
        with Session(eng) as session:
            if (prog.kind in _FETCH_KINDS or is_expand) and not skip_fetch:
                _fetch_t0 = time.perf_counter()  # J-53: fetch-stage wall-clock (honest even on a pause/fail)
                live = provider if provider is not None else _resolve_live_provider(cfg, prog.source, api_key)
                if is_expand:
                    pool = read_pool(seed_dir)  # the committed candidate pool (raises if not built — explicit)
                if is_resume:
                    checkpoint = _load_checkpoint(session, prog.job_id)
                    if checkpoint is None:  # defensive — the endpoint pre-validates existence
                        raise LookupError(f"unknown import: {prog.job_id}")
                    symbols = json.loads(checkpoint.symbol_plan_json)
                    chunks = _chunk_plan(cfg, symbols, prog.start, prog.end)
                    start_chunk = checkpoint.next_chunk_index
                    prog.chunk_total = checkpoint.chunk_total
                    checkpoint.status = "running"  # re-arm the durable row for this resume attempt
                    checkpoint.updated_at = _utcnow()
                    session.add(checkpoint)
                    session.commit()
                else:
                    # the symbol set for a fresh fetch, in priority order:
                    #   - an EXPAND fetches the committed POOL (J-35),
                    #   - a J-37 PULL fetches EXACTLY the diagnosed-gap symbols (`symbols_override`) — the
                    #     gap-exact fetch dispatched through this SAME chunked engine (no second fetch path),
                    #   - otherwise a generic fetch keeps the WHOLE committed pool ∪ context fresh (J-13,
                    #     iter-20) — `price_load_symbols` is the SAME union `load_prices` already uses, so
                    #     the generic Fetch job covers every pool name (not just the ~122-name context set)
                    #     WITHOUT dropping the context symbols (benchmarks/ETFs/^VIX/macro proxies) the old
                    #     `all_seed_symbols`-only default kept fresh (an honest-coverage regression to avoid).
                    # Everything downstream (plan, checkpoint, per-(symbol,date) idempotency) is reused.
                    if is_expand:
                        symbols = [row["symbol"] for row in pool]
                    elif symbols_override is not None:
                        symbols = list(symbols_override)
                    else:
                        symbols = price_load_symbols(cfg, seed_dir)
                    chunks = _chunk_plan(cfg, symbols, prog.start, prog.end)
                    start_chunk = 0
                    checkpoint = _start_checkpoint(session, cfg, prog, symbols, len(chunks))
                prog.symbols_total = len(symbols)
                # J-59 covered-range planner: skip the provider call for any chunk already FULLY covered
                # against the benchmark trading calendar (a re-run over a covered range reaches backfill in
                # seconds — never ~45min of no-op re-fetching to add 0 new bars). Partially-covered chunks
                # still fetch (INSERT-new-only idempotency fills only the missing bars).
                covered_chunks, _covered_symbols = _plan_uncovered_chunks(
                    session, cfg, chunks, start_chunk=start_chunk
                )
                _run_chunked_fetch(
                    session, cfg, prog, live, chunks=chunks, checkpoint=checkpoint,
                    scrub=scrub, sleep_fn=sleep_fn, start_chunk=start_chunk,
                    covered_chunks=covered_chunks,
                    overlap_sink=overlap_sink, overlap_days=cfg.data_quality.drift.overlap_days,
                )
                # J-59: record fetch-stage completion (so a `both`/`backfill` resume skips it; the durable
                # checkpoint mirrors it). Only when the fetch actually completed (not on a graceful pause).
                if prog.status != "resumable":
                    prog.complete_stage("fetch")
                # J-53: record the fetch-stage timing ONCE — honest for the portion that ran (a paused/
                # failed fetch records its elapsed + the symbols it DID process; `items_processed` = the
                # symbols accounted ok+failed, `concurrency` = the config fetch pool size).
                prog.record_stage(
                    "fetch",
                    elapsed_seconds=time.perf_counter() - _fetch_t0,
                    items_processed=prog.symbols_ok + prog.symbols_failed,
                    concurrency=cfg.data_manager.import_chunking.fetch_workers,
                )
                # iter-35 (J-21/B-304): the post-fetch drift validation stage -- ONLY when the fetch
                # actually completed (never on a `resumable` pause, whose chunk's bars were discarded, not
                # committed) and the feature is config-enabled (`overlap_sink` is None when disabled).
                if overlap_sink is not None and prog.status != "resumable":
                    _check_drift(cfg, seed_dir, overlap_sink, prog, scrub)
                if prog.status == "resumable":
                    paused = True  # graceful pause — checkpoint already persisted resumable
                elif not is_expand:
                    # an EXPAND's checkpoint is finalized only AFTER the screen step completes (so a cap-feed
                    # pause in the screen leaves the durable row `resumable` — see below); a generic fetch
                    # has no further step. A `both` job's checkpoint is finalized only AFTER its backfill
                    # stage (so a backfill failure can mark it `failed_backfill` — see below); a fetch-only
                    # job finalizes now.
                    if prog.kind not in _BACKFILL_KINDS:
                        _finalize_checkpoint(session, checkpoint, prog)
            elif skip_fetch and is_resume:
                # J-59 resume-at-backfill (and J-84 resume-at-screen): the fetch stage already completed, so
                # NO OHLCV chunk is fetched now (zero duplicate provider calls). Load the existing checkpoint
                # so the post-stage finalize/fail-marking has it. For an EXPAND whose SCREEN step paused
                # resumable (a systemic cap-auth/limit failure — J-84), the screen step below re-runs and
                # needs the live provider + the committed pool, so bind them here too (the screen re-fetches
                # the market caps — that is exactly what the resume retries; the OHLCV chunks stay covered).
                checkpoint = _load_checkpoint(session, prog.job_id)
                if checkpoint is not None:
                    prog.chunk_total = checkpoint.chunk_total
                    checkpoint.status = "running"
                    checkpoint.updated_at = _utcnow()
                    session.add(checkpoint)
                    session.commit()
                if is_expand:
                    live = provider if provider is not None else _resolve_live_provider(cfg, prog.source, api_key)
                    pool = read_pool(seed_dir)
                    prog.current_activity = "resuming at the screen stage (fetch already complete)"
                else:
                    prog.current_activity = "resuming at the backfill stage (fetch already complete)"
            if not paused and is_expand:
                # screen the pool against the freshly-stored bars + a real market-cap reference, writing
                # universe.json / CSVs / meta.json (the single screen source — screen_reasons). A persistent
                # cap-feed 429 sets `resumable` (paused) inside the screen step.
                if not pool:  # a resume re-enters here with pool empty (it was read pre-fetch on a fresh run)
                    pool = read_pool(seed_dir)
                _run_expand_screen(session, cfg, prog, live, pool, scrub=scrub, seed_dir=seed_dir)
                if prog.status == "resumable":
                    paused = True
                    # the cap feed walled mid-screen → leave the durable checkpoint `resumable` so the import
                    # stays discoverable + Resume-able (a re-run re-screens; the OHLCV chunks are idempotent).
                    if checkpoint is not None:
                        _advance_checkpoint(
                            session, checkpoint, prog, next_idx=checkpoint.next_chunk_index, status="resumable"
                        )
                else:
                    prog.complete_stage("screen")  # J-59: screen stage done
                    if checkpoint is not None:
                        _finalize_checkpoint(session, checkpoint, prog)  # expand fully done → terminal
            if prog.kind in _REBUILD_KINDS:
                # J-85: a wholesale regenerate-from-scratch. (1) CLEAR the entire snapshot set (whole-row
                # deletes — the committed PRICE seed is never touched / referenced). (2) widen the range to
                # the FULL trading calendar so `_do_backfill` (the EXISTING create-once path) recomputes a
                # snapshot + forward returns for EVERY covered trading day over the resolved universe. No
                # canonical formula changes — only the membership scanned over. The J-66 progress machinery
                # (per-date ticks, counters) and the J-41 create-once/concurrency guards are intact.
                cleared = clear_snapshot_set(session)
                prog.current_activity = (
                    f"cleared {cleared['runs_cleared']} snapshot(s); rebuilding all covered dates "
                    f"(price seed intact: {cleared['bars_after']} bars)"
                )
                calendar = _trading_days(session, cfg)
                if calendar:
                    prog.start, prog.end = calendar[0], calendar[-1]  # the FULL covered calendar
                _backfill_t0 = time.perf_counter()  # J-53: backfill-stage wall-clock (parallel)
                try:
                    _do_backfill(session, cfg, prog, eng=eng)
                except Exception:  # noqa: BLE001 — a whole-stage rebuild failure surfaces as `failed`
                    backfill_failed = True
                    raise
                finally:
                    prog.record_stage(
                        "backfill",
                        elapsed_seconds=time.perf_counter() - _backfill_t0,
                        items_processed=prog.dates_done,
                        concurrency=prog._backfill_concurrency,
                        per_date_seconds_sum=prog._backfill_per_date_seconds_sum,
                    )
            if not paused and prog.kind in _BACKFILL_KINDS:
                _backfill_t0 = time.perf_counter()  # J-53: backfill-stage wall-clock (parallel)
                try:
                    _do_backfill(session, cfg, prog, eng=eng)
                except Exception:  # noqa: BLE001 — a whole-stage backfill failure (not a per-date one)
                    backfill_failed = True
                    raise  # surfaced as an explicit `failed` job by the outer handler
                else:
                    if prog.date_failures:
                        # J-67 + J-59: the backfill ran but ISOLATED one or more failed dates (`partial`).
                        # For a job carrying a checkpoint (a `both` job whose fetch completed, or a resumed
                        # backfill) leave the durable row `failed_backfill` so the operator can Resume JUST
                        # the backfill (zero provider calls) to retry the failed dates — the completed dates
                        # are create-once, untouched. A pure `backfill` job (no checkpoint) ends `partial`
                        # without a resume affordance (Retry re-dispatches it).
                        if checkpoint is not None and "fetch" in prog.completed_stages:
                            _mark_checkpoint_failed_backfill(session, checkpoint, prog)
                    else:
                        prog.complete_stage("backfill")  # J-59: backfill stage cleanly done
                        # a `both` job's fetch-stage checkpoint is finalized only now (after the backfill ran).
                        if checkpoint is not None:
                            _finalize_checkpoint(session, checkpoint, prog)
                finally:
                    # J-53: record the backfill-stage timing ONCE — elapsed wall-clock, dates processed, the
                    # concurrency the pool actually used, and the SUM of per-date compute seconds (the
                    # sequential baseline the parallel wall-clock beats — so the >=~2x speedup is evidenced
                    # by the job's OWN payload: elapsed_seconds vs per_date_seconds_sum). The server-computed
                    # speedup_factor is carried in the stages payload (J-66 — no client-side division).
                    prog.record_stage(
                        "backfill",
                        elapsed_seconds=time.perf_counter() - _backfill_t0,
                        items_processed=prog.dates_done,
                        concurrency=prog._backfill_concurrency,
                        per_date_seconds_sum=prog._backfill_per_date_seconds_sum,
                    )
        if not paused:
            final_status = _final_status(prog)
            # ops-hardening iter-2 (J-05): run the ingest finalize hook BEFORE the status flip below
            # becomes observable — never after. `prog.status`/`aggregates_refreshed` are polled LIVE by
            # `GET /api/data/jobs/{id}` (via `to_dict()`); flipping `status` to its terminal value first
            # would let a poller observe "ok"/"partial" while `aggregates_refreshed` is still empty and
            # `finished_at` is still None — a misleading inconsistent window this project's honesty
            # conventions do not allow (and one this hook's own real work would make newly observable,
            # unlike the negligible few-line gap that existed here before). Reached ONLY on a successful
            # backfill/both/rebuild (never fetch/expand, never a failed/resumable outcome). The request/
            # job session (`session`, above) has already closed by this point, so this opens its OWN fresh
            # session. Wrapped in its own try/except (log + continue, never raise) mirroring
            # `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure
            # must never flip an otherwise-successful ingest job to failed.
            if final_status in ("ok", "partial") and (
                prog.kind in _BACKFILL_KINDS or prog.kind in _REBUILD_KINDS
            ):
                try:
                    with Session(eng) as agg_session:
                        prog.aggregates_refreshed = _refresh_ingest_aggregates(agg_session, cfg, prog)
                except Exception as exc:  # noqa: BLE001 — non-fatal: never flips a successful job to failed
                    logger.exception("ingest aggregate refresh failed (non-fatal): %s", exc)
            elif final_status in ("ok", "partial") and (
                prog.kind in _FETCH_KINDS or prog.kind in _EXPAND_KINDS
            ):
                # ops-hardening iter-3 (B1): a pure fetch/expand does not run the rich backfill-style hook
                # above (no per-date snapshot loop, no market-phase/research-hot-key warm — not asked for
                # here — `elif` naturally excludes "both", which is ALSO in `_BACKFILL_KINDS` and already
                # ran through the branch above), but it CAN change the bars/membership manifest
                # (`_membership_dataset_version`), which silently staled the persisted `coverage_snapshot`
                # row `GET /api/data`'s default view reads — until this fix, only an unrelated restart or
                # backfill/rebuild ever refreshed it (audit finding B1). Calls `refresh_coverage_snapshot`
                # directly (the SAME canonical compute the rich path uses) — never a second derivation —
                # gated by `_coverage_snapshot_is_current` so a zero-work fetch (the common offline case)
                # pays no extra compute/write (TC-2). Deliberately does NOT set `prog.aggregates_refreshed`
                # — that field's existing backfill/both/rebuild-only nullability contract is unchanged
                # (already gated to null for fetch/expand via `_breakdown_computed`, `_run_detail` above).
                try:
                    with Session(eng) as agg_session:
                        if not _coverage_snapshot_is_current(agg_session, cfg):
                            refresh_coverage_snapshot(agg_session, cfg)
                except Exception as exc:  # noqa: BLE001 — non-fatal: never flips a successful job to failed
                    logger.exception("ingest coverage refresh failed for fetch/expand (non-fatal): %s", exc)
            prog.status = final_status
    except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job (scrubbed)
        prog.status = "failed"
        # ops-hardening iter-44 AUDIT (B1): `str(MemoryError())` is the EMPTY STRING — and `MemoryError`
        # is THE exception class this session's real failures actually raise (see `logs/backend.log`'s
        # caught-MemoryError storm during the 2026-08-03 browser-lane incident). With a bare
        # `scrub(str(exc))` the whole honesty fix below collapsed for exactly that class: `prog.message`
        # became `""`, whose falsiness sends `_run_detail`'s `prog.message if (... and prog.message)`
        # guard straight back to `_final_summary`'s generic "0 snapshots over N dates" text — the precise
        # string this iteration's TC-10 exists to eliminate (live-observed on run 272). Name the
        # exception TYPE when it carries no text, so a failed job's persisted reason is never blank.
        # Applies the binding iter-43 lesson: key the guard to the WHOLE exception set the diagnosed
        # incident produces, not its headline (text-carrying) exception.
        reason = scrub(str(exc)) or f"{type(exc).__name__} (no message)"
        _record_error(prog, reason)
        # ops-hardening iter-44 (reviewer MINOR, carried from iter-43 B5): capture the REAL reason on
        # `prog.message` itself (not just `prog.errors`) so the `finally` block below — which no longer
        # unconditionally overwrites a failed job's message with `_final_summary` (a summary of WORK DONE,
        # which structurally cannot name a failure that happened before any work was recorded) — has
        # something honest to preserve. This is also what makes the iter-43 audit's `_run_detail` B2 fix
        # (line ~4037, `"summary": prog.message if (prog.status == "failed" and prog.message) else
        # _final_summary(prog)`) stop being a no-op: that guard already special-cased a failed status, but
        # until now `prog.message` at that point was ALWAYS `_final_summary(prog)` too (assigned
        # unconditionally by this same `finally` block), so the two branches collided and always produced
        # the identical string (audit B5's finding).
        prog.message = reason
        # J-59: a `both`/`backfill` job whose FETCH completed but whose BACKFILL failed is marked
        # `failed_backfill` on its durable checkpoint, so Unfinished-imports offers it as "failed at
        # backfill — resumable from the backfill stage" (a Resume skips the completed fetch — zero
        # provider calls). Only when the fetch stage genuinely completed (checkpoint carries it).
        if backfill_failed and "fetch" in prog.completed_stages:
            try:
                with Session(eng) as fsession:
                    cp = _load_checkpoint(fsession, prog.job_id)
                    if cp is not None:
                        _mark_checkpoint_failed_backfill(fsession, cp, prog)
            except Exception as exc2:  # noqa: BLE001 — bookkeeping failure must not crash the worker
                _record_error(prog, scrub(f"failed to mark checkpoint resumable-at-backfill: {exc2}"))
    finally:
        # ops-hardening iter-37 AUDIT (B1) — LAST-RESORT release of the shared whole-table `_BarCache`
        # `_do_backfill` stashes on `prog` (`prog._shared_bar_cache`) for the ingest finalize hook to reuse.
        # `_refresh_ingest_aggregates`'s own `finally` is the NORMAL release point, so this is a plain no-op
        # on every job that reaches it (the reference is already None by then). It exists for the paths that
        # DON'T reach it after a SUCCESSFUL `_do_backfill`: the `_finalize_checkpoint` /
        # `_mark_checkpoint_failed_backfill` / `record_stage` writes between the two, or `Session(eng)`
        # itself, faulting (a `MemoryError` under real pressure, a locked DB) — the hook is then skipped and
        # nothing else would EVER clear the reference, because `_JOBS` keeps every finished `JobProgress`
        # for the life of the process. That would pin the ~1.13 GB block permanently in a long-lived server
        # — exactly the AG-8/J-07 failure ("heavy aggregates never take the service down") this iteration
        # exists to prevent, and structurally impossible before the release moved out of `_do_backfill`'s
        # own `finally`. Null the reference FIRST so `gc.collect()` can actually reclaim the block.
        if prog._shared_bar_cache is not None:
            prog._shared_bar_cache = None
            _release_process_memory()
        # ops-hardening iter-44 (reviewer MINOR, carried from iter-43 B5): a job that failed via the outer
        # exception handler above already has its real captured reason on `prog.message` (set at the
        # `except Exception as exc` block, alongside `_record_error`) — do NOT clobber it with
        # `_final_summary`'s generic "work done" text. Every other terminal status (`ok`/`partial`/
        # `resumable`) keeps getting `_final_summary`'s descriptive summary, byte-identical to before.
        if prog.status != "failed":
            prog.message = _final_summary(prog)
        # J-60: close the SAME run-history record this job created at start (one record per job, one
        # transition). A graceful `resumable` pause is NOT a terminal state — its run row is UPDATEd to
        # `resumable` (so it shows that way in Run history AND is skipped by the boot sweep, which only
        # touches `running` rows) but keeps `finished_at` NULL (it has not finished); the durable
        # checkpoint carries the resume point, and the eventual completed resume closes THIS SAME row to
        # its terminal state. Every other state is terminal → set finished_at + UPDATE.
        if prog.status != "resumable":
            prog.finished_at = _utcnow()
        try:
            _finalize_run_record(eng, cfg, prog)
        except Exception as exc:  # noqa: BLE001 — persistence failure must not crash the worker thread
            _record_error(prog, scrub(f"failed to persist run summary: {exc}"))
    return prog.to_dict()


def run_data_job(
    job_id: str,
    *,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
    provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
    seed_dir: Optional[str | Path] = None,
    symbols: Optional[list[str]] = None,
) -> dict:
    """Run the registered job to completion SYNCHRONOUSLY (the worker body; `start_data_job` runs this in
    a thread). Updates the in-memory registry as it goes and persists the final summary. Returns the final
    snapshot. `sleep_fn` is injectable so the 429-backoff + inter-request sleeps add NO wall-clock in
    tests (defaults to `time.sleep`). For a fetch, the job-selected `source` is resolved against the
    catalog and `make_provider(source, api_key=key)` builds the live client; an injected `provider`
    (tests) bypasses that entirely. `seed_dir` (J-35) is where an `expand` job reads the candidate pool +
    writes universe.json/CSVs/meta.json — injectable so tests write to a temp dir, never the committed seed.
    `symbols` (J-37 pull) restricts a FETCH to EXACTLY the diagnosed-gap symbols — dispatched through this
    SAME chunked engine (no second fetch path); None ⇒ the full seed set (generic fetch behavior)."""
    cfg = config or get_config()
    eng = engine or get_engine()
    with _LOCK:
        prog = _JOBS[job_id]
    return _run_job(
        prog, cfg=cfg, eng=eng, provider=provider, api_key=api_key,
        sleep_fn=sleep_fn or _sleep, is_resume=False,
        seed_dir=Path(seed_dir) if seed_dir else DEFAULT_SEED_DIR,
        symbols_override=symbols,
    )


def _progress_from_checkpoint(cfg: Config, cp: ImportCheckpoint) -> JobProgress:
    """The in-memory `JobProgress` a resume of `cp` runs under — seeded from the durable checkpoint so the
    resumed job continues from the work already recorded rather than from zero.

    iter-43 AUDIT (B1): extracted verbatim from `resume_data_job` (its only caller until now) so the
    unlaunched-resume guard (`_fail_unlaunched_resume`) can build the SAME shape. That matters because
    `_finalize_run_record` UPDATEs the OPEN run-history row's `symbols_ok`/`symbols_failed`/detail JSON
    straight off whatever progress it is handed: closing the paused attempt's row with a bare
    `JobProgress(...)` erased its recorded counts (live-proved: `symbols_ok` 1 -> 0, `bars_fetched`
    10 -> 0, summary "fetch: 0/0 symbols ok, 0 failed, 0 new bars") on the permanent audit record."""
    prog = JobProgress(job_id=cp.import_id, kind=cp.kind, start=cp.start, end=cp.end, source=cp.source)
    plan_symbols = json.loads(cp.symbol_plan_json)
    # J-66: reconstruct the distinct per-symbol completion sets from the COMPLETED chunks so the
    # per-symbol counter continues from the right point (rather than double-counting or resetting).
    # The chunks already committed (< next_chunk_index) fetched their symbol batches successfully, so
    # those distinct symbols are `done`; the persisted failed count is honored as-is (its symbols are
    # outside the committed batches). This keeps symbols_ok == distinct done across the resume.
    completed_chunks = _chunk_plan(cfg, plan_symbols, cp.start, cp.end)[: cp.next_chunk_index]
    for sym_batch, _window in completed_chunks:
        prog.symbols_done.update(sym_batch)
    prog.symbols_total = len(plan_symbols)
    prog.bars_fetched = cp.bars_fetched
    prog.chunk_total = cp.chunk_total
    prog.chunk_index = cp.next_chunk_index
    # J-59: seed the completed-stages from the durable checkpoint so a resume can skip a completed
    # fetch stage entirely (zero provider calls) and route straight to the remaining stage(s).
    try:
        prog.completed_stages = list(json.loads(cp.completed_stages_json or "[]"))
    except (ValueError, TypeError):
        prog.completed_stages = []
    prog._recount_symbols()
    # honor any persisted failed count not captured by the reconstructed sets (defensive: a legacy
    # checkpoint may carry a failed tally without per-symbol detail).
    if cp.symbols_failed > prog.symbols_failed:
        prog.symbols_failed = cp.symbols_failed
    prog.message = _fetch_message(prog)
    return prog


def resume_data_job(
    import_id: str,
    *,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
    provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
    seed_dir: Optional[str | Path] = None,
) -> dict:
    """Resume a paused (`resumable`) chunked import: load its durable `ImportCheckpoint`, re-register a
    fresh in-memory `JobProgress` seeded from it (SAME `import_id`), and run the chunk loop from
    `next_chunk_index` — re-fetching nothing already stored (per-`(symbol, date)` idempotency via the
    existing INSERT-new-only `DailyPrice` guard). Raises `LookupError` for an unknown id and `ValueError`
    for a non-resumable id (the API maps these to 404/409). The session-only `api_key` is re-supplied
    request-only for a needs-key source — it is NEVER read from the checkpoint (no key is stored there). A
    resumed `expand` import re-runs the screen step after the OHLCV catch-up completes (`seed_dir` injectable)."""
    cfg = config or get_config()
    eng = engine or get_engine()
    with Session(eng) as session:
        cp = _load_checkpoint(session, import_id)
        if cp is None:
            raise LookupError(f"unknown import: {import_id}")
        if cp.status not in RESUMABLE_CHECKPOINT_STATUSES:
            raise ValueError(f"import {import_id} is not resumable (status {cp.status})")
        prog = _progress_from_checkpoint(cfg, cp)
    with _LOCK:
        _JOBS[prog.job_id] = prog
    return _run_job(
        prog, cfg=cfg, eng=eng, provider=provider, api_key=api_key,
        sleep_fn=sleep_fn or _sleep, is_resume=True,
        seed_dir=Path(seed_dir) if seed_dir else DEFAULT_SEED_DIR,
    )


def _fail_unlaunched_job(prog: JobProgress, cfg: Config, eng: Engine, exc: BaseException) -> None:
    """ops-hardening iter-43 (J-05 regression fix) — a `threading.Thread(...).start()` failure (the live
    incident: `RuntimeError: can't start new thread`) happens OUTSIDE `_run_job`'s own outer `except
    Exception` handler (`:4504-4506`), which only ever runs INSIDE the thread body once it is running.
    Left unguarded, the just-created job stays at its `create_job()`-time `running` default forever — a
    silent zero-work job goal.md's own "Zero silent zero-work jobs" promise forbids. Mirrors `_run_job`'s
    OWN failure mechanism (`prog.status = "failed"` + `_record_error`) so both the live in-memory registry
    (a poller's `GET /api/data/jobs/{id}`) and the persisted run-history row read the SAME honest outcome
    every other job failure already produces. `_finalize_run_record`'s own documented no-open-row fallback
    (an INSERT, not an UPDATE) is exactly the right shape here, since a launch failure never reaches
    `_create_run_record` (that only runs inside `_run_job`, on the thread that never started)."""
    reason = f"failed to launch job worker thread: {exc}"
    prog.status = "failed"
    _record_error(prog, reason)
    # iter-43 AUDIT (B2): `_run_job`'s `finally` sets `prog.message = _final_summary(prog)` on every
    # in-flight failure; this path must set it too, or the persisted row (and a live poller's
    # `to_dict()["message"]`) carries an all-zeros work summary with no hint of WHY — TC-3/TC-4 ask for a
    # message that NAMES the thread-launch failure. Prefixed to the same summary `_final_summary` would
    # produce, mirroring that function's own "rate-limited — resumable at chunk N/M; {summary}" idiom, so
    # the reason AND whatever work the attempt had already recorded both survive on one honest line.
    prog.message = f"{reason}; {_final_summary(prog)}"
    prog.finished_at = _utcnow()
    with _LOCK:
        # Ensures a live poller sees the failure even when the caller (a resume) never registered this
        # `prog` itself — see `_fail_unlaunched_resume`. A no-op re-assignment for the normal
        # `start_data_job` case, where `create_job()` already registered this exact object.
        _JOBS[prog.job_id] = prog
    try:
        _finalize_run_record(eng, cfg, prog)
    except Exception:  # noqa: BLE001 — persistence failure must not crash the launch-failure path further
        logger.exception("failed to persist run summary for unlaunched job %s", prog.job_id)


def _fail_unlaunched_resume(import_id: str, cfg: Config, eng: Engine, exc: BaseException) -> None:
    """The RESUME sibling of `_fail_unlaunched_job`. Unlike `start_data_job` (whose `create_job()` already
    registered a `JobProgress` before `thread.start()` is attempted), a resume's `JobProgress` is normally
    built INSIDE `resume_data_job` (the thread target) from the durable checkpoint — since the thread never
    ran, nothing has built or registered one yet. Rebuilds it via the SAME `_progress_from_checkpoint`
    `resume_data_job` itself uses so the EXISTING open run-history row (left `resumable`/`running` by the
    paused attempt this resume was trying to continue) is closed to `failed` via the same mechanism,
    instead of staying open forever. The caller (`POST /api/data/jobs/{import_id}/resume`) already
    validated the checkpoint exists and is resumable before calling `start_resume_job`, so a missing
    checkpoint here is defensive only.

    iter-43 AUDIT (B1): this originally built a BARE `JobProgress(job_id=..., kind=..., start=..., end=...,
    source=...)` — only the constructor line of what `resume_data_job` does, not its checkpoint seeding.
    Because `_finalize_run_record` UPDATEs the open row's `symbols_ok`/`symbols_failed`/detail JSON
    straight off the progress it is handed, that ERASED the paused attempt's recorded work from the
    permanent audit row (live-proved: `symbols_ok` 1 -> 0, `bars_fetched` 10 -> 0) and left
    `_run_state_text` rendering the fabricated "Failed — every symbol failed (0 of 0); provider
    unreachable" for an import that had really completed a chunk. The checkpoint itself is untouched
    either way, so Resume still works — but the audit record must not lie about what already happened."""
    try:
        # build INSIDE the session (as `resume_data_job` does): the seeding reads several checkpoint
        # columns, and reading a detached instance is only safe while every one of them happens to be
        # already loaded — not a property to depend on.
        with Session(eng) as session:
            cp = _load_checkpoint(session, import_id)
            if cp is None:
                logger.error("cannot record unlaunched-resume failure — unknown checkpoint %s", import_id)
                return
            prog = _progress_from_checkpoint(cfg, cp)
    except Exception:  # noqa: BLE001 — never let this bookkeeping path itself crash the launch-failure path
        logger.exception("failed to rebuild job progress for unlaunched resume %s", import_id)
        return
    _fail_unlaunched_job(prog, cfg, eng, exc)


def start_data_job(
    kind: str,
    start: date_cls,
    end: date_cls,
    *,
    source: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
    symbols: Optional[list[str]] = None,
) -> str:
    """Register a job and run it ASYNCHRONOUSLY in a daemon thread; return the `job_id` immediately so
    the POST handler responds without blocking. The thread opens its own session on the given engine.

    `source` (J-33) is recorded on the job ONLY for a kind that FETCHES — a backfill-only job reads the
    committed seed, so its progress header carries no import source (iter-21 Finding #2). `api_key` is the
    SESSION-ONLY pasted key — passed to the worker as a request-only thread argument and NEVER stored on
    the job/registry (anti-goal: keys are env-or-session, never persisted). `symbols` (J-37 pull) restricts
    a fetch to exactly the diagnosed-gap symbols (the SAME chunked engine — no second fetch path)."""
    cfg = config or get_config()
    eng = engine or get_engine()
    # record the source on any job that FETCHES (a generic fetch OR an expand) — a backfill-only job
    # reads the committed seed, so it carries no import source (iter-21 Finding #2).
    fetches = kind in _FETCH_KINDS or kind in _EXPAND_KINDS
    job_source = (source or cfg.data_manager.default_source) if fetches else None
    job = create_job(kind, start, end, source=job_source)
    # iter-26: a `seed`-source EXPAND writes its grown universe.json/CSVs/meta.json to the THROWAWAY
    # overlay dir (never the committed seed) so an offline J-35 capture cannot mutate `data/seed/`.
    job_kwargs = {"config": cfg, "engine": eng, "api_key": api_key, "symbols": symbols}
    expand_seed_dir = _expand_seed_dir_for_source(job_source) if kind in _EXPAND_KINDS else None
    if expand_seed_dir is not None:
        job_kwargs["seed_dir"] = expand_seed_dir
    thread = threading.Thread(
        target=run_data_job,
        args=(job.job_id,),
        kwargs=job_kwargs,
        daemon=True,
        name=f"data-job-{job.job_id}",
    )
    try:
        thread.start()
    except Exception as exc:  # noqa: BLE001 — see below; ALWAYS re-raised, never swallowed
        # ops-hardening iter-43 (J-05 regression fix) — see `_fail_unlaunched_job`. Re-raised so the
        # caller (`POST /api/data/jobs`) can return an honest error instead of a 200 over a dead job.
        # iter-43 AUDIT (B3): deliberately NOT keyed to `RuntimeError`. `Thread.start()` itself catches a
        # bare `Exception` around `_start_new_thread` (CPython `Lib/threading.py`) because the C-level
        # `thread.start_new_thread` has two distinct failure exits under one memory ceiling:
        # `RuntimeError("can't start new thread")` when the OS refuses the thread, and `PyErr_NoMemory()`
        # -> `MemoryError` when its own bootstate allocation fails first. iter-42's outage produced BOTH
        # side by side, so a `RuntimeError`-only guard left this iteration's "zero silent zero-work jobs"
        # promise open on its nearest sibling path (live-proved by
        # `test_start_data_job_non_runtimeerror_launch_failure_also_marks_job_failed`, which orphaned the
        # job at `running` with no run-history row at all before this widening). The `raise` below is
        # unconditional — this handler only ever ADDS an honest record, it never converts a launch
        # failure into a success.
        _fail_unlaunched_job(job, cfg, eng, exc)
        raise
    return job.job_id


def start_resume_job(
    import_id: str,
    *,
    api_key: Optional[str] = None,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
) -> str:
    """Spawn the resume worker in a daemon thread and return immediately (the endpoint pre-validates the
    import exists + is resumable + has a key before calling this). `api_key` is the re-supplied
    SESSION-ONLY key — a request-only thread argument, never persisted."""
    cfg = config or get_config()
    eng = engine or get_engine()
    thread = threading.Thread(
        target=resume_data_job,
        args=(import_id,),
        kwargs={"config": cfg, "engine": eng, "api_key": api_key},
        daemon=True,
        name=f"data-resume-{import_id}",
    )
    try:
        thread.start()
    except Exception as exc:  # noqa: BLE001 — same contract as `start_data_job`; ALWAYS re-raised
        # ops-hardening iter-43 (J-05 regression fix) — see `_fail_unlaunched_resume`. Re-raised so the
        # caller (`POST /api/data/jobs/{import_id}/resume`) can return an honest error instead of a 200
        # over a resume that never started. iter-43 AUDIT (B3): not keyed to `RuntimeError` — see the
        # matching comment in `start_data_job` for why `MemoryError` is the evidenced sibling exit.
        _fail_unlaunched_resume(import_id, cfg, eng, exc)
        raise
    return import_id


# --------------------------------------------------------------------------------------------------
# Run history (GET /api/data) — read the append-only DataProviderRun log
# --------------------------------------------------------------------------------------------------
def summarize_provider_run(run: DataProviderRun) -> dict:
    """One run-history row for the UI. A Data Manager job encodes structured detail as JSON in
    `message`; a plain seed-load row (non-JSON message) renders with null job fields + its raw message."""
    detail: dict = {}
    if run.message:
        try:
            parsed = json.loads(run.message)
            if isinstance(parsed, dict):
                detail = parsed
        except (ValueError, TypeError):
            detail = {}
    is_job = "kind" in detail
    return {
        "id": run.id,
        "provider": run.provider,
        "kind": detail.get("kind"),
        "start": detail.get("start"),
        "end": detail.get("end"),
        "status": run.status,
        "symbols_ok": run.symbols_ok,
        "symbols_failed": run.symbols_failed,
        "snapshots_created": detail.get("snapshots_created"),
        "dates_done": detail.get("dates_done"),
        "dates_total": detail.get("dates_total"),
        # ops-hardening iter-1 (J-01): the run-summary exclusion breakdown — None for a fetch/expand run
        # or a plain non-JSON seed-load row (mirrors the passers/omitted_total nullability immediately
        # below). Surfaced verbatim from the persisted detail JSON — no second computation path.
        "calendar_days": detail.get("calendar_days"),
        "non_trading_days": detail.get("non_trading_days"),
        "already_snapshotted": detail.get("already_snapshotted"),
        "error_other": detail.get("error_other"),
        # ops-hardening iter-2 (J-05): the finalize hook's output on this persisted run — None for a
        # fetch/expand run or a not-yet-computed/interrupted row (mirrors the breakdown fields' nullability
        # immediately above). Surfaced verbatim from the persisted detail JSON — no second computation path.
        "aggregates_refreshed": detail.get("aggregates_refreshed"),
        "bars_fetched": detail.get("bars_fetched"),
        "passers": detail.get("passers"),  # J-35 expand screen outcome (None for non-expand runs)
        "omitted_total": detail.get("omitted_total"),  # J-35 expand screen outcome (None otherwise)
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "message": detail.get("summary") if is_job else run.message,
    }


def recent_runs(session: Session, config: Optional[Config] = None) -> list[dict]:
    """The recent fetch/backfill (and seed-load) run history, newest first, capped at
    `config.data_manager.run_history_limit`."""
    cfg = config or get_config()
    rows = session.exec(
        select(DataProviderRun)
        .order_by(DataProviderRun.started_at.desc(), DataProviderRun.id.desc())
        .limit(cfg.data_manager.run_history_limit)
    ).all()
    return [summarize_provider_run(run) for run in rows]


# --------------------------------------------------------------------------------------------------
# Resumable imports (GET /api/data) — the paused chunked imports, surviving a backend restart (J-34)
# --------------------------------------------------------------------------------------------------
def _summarize_checkpoint(cp: ImportCheckpoint) -> dict:
    """One `resumable_imports` row for the UI: per-import chunk progress + symbols done vs remaining.
    Descriptive job-control metadata ONLY — it carries NO key value (anti-goal: keys are env-or-session,
    never persisted; the checkpoint has no key column to leak)."""
    try:
        symbols_total = len(json.loads(cp.symbol_plan_json)) if cp.symbol_plan_json else 0
    except (ValueError, TypeError):
        symbols_total = 0
    symbols_remaining = max(symbols_total - cp.symbols_ok - cp.symbols_failed, 0)
    try:
        completed_stages = list(json.loads(cp.completed_stages_json or "[]"))
    except (ValueError, TypeError):
        completed_stages = []
    return {
        "import_id": cp.import_id,
        "source": cp.source,
        "kind": cp.kind,
        "start": cp.start.isoformat(),
        "end": cp.end.isoformat(),
        "chunk_index": cp.next_chunk_index,  # completed chunks == the resume point
        "chunk_total": cp.chunk_total,
        "symbols_total": symbols_total,
        "symbols_ok": cp.symbols_ok,
        "symbols_failed": cp.symbols_failed,
        "symbols_remaining": symbols_remaining,
        "bars_fetched": cp.bars_fetched,
        "status": cp.status,  # resumable | failed_backfill (J-59) | running | ok | failed
        "completed_stages": completed_stages,  # J-59: which stages completed (drives the resume route)
        "updated_at": cp.updated_at.isoformat() if cp.updated_at else None,
    }


def resumable_imports(session: Session, config: Optional[Config] = None) -> list[dict]:
    """The resumable chunked imports, newest first — the durable Resume affordance that SURVIVES a backend
    restart (the in-memory job is gone, but the checkpoint persists). Includes both a `resumable` (429
    pause) and a `failed_backfill` (J-59: fetch done, backfill failed → resumable from the backfill stage).
    NEVER carries a key value."""
    rows = session.exec(
        select(ImportCheckpoint)
        .where(ImportCheckpoint.status.in_(list(RESUMABLE_CHECKPOINT_STATUSES)))
        .order_by(ImportCheckpoint.updated_at.desc(), ImportCheckpoint.id.desc())
    ).all()
    return [_summarize_checkpoint(cp) for cp in rows]


# --------------------------------------------------------------------------------------------------
# J-38 — Unified Unfinished-imports (GET /api/data) — one read-only union of every import that did NOT
# finish cleanly, each with a PLAIN-LANGUAGE state + the right action. Reads the canonical job-control
# rows ONLY (the resumable `import_checkpoints` + the partial/failed `data_provider_runs`); recomputes NO
# canonical score/return/bucket. NEVER carries a key value.
# --------------------------------------------------------------------------------------------------
def _resumable_state_text(cp: ImportCheckpoint, symbols_remaining: int) -> str:
    """The plain-language state for a resumable checkpoint row (J-38 / J-59). A `failed_backfill` row
    (J-59: fetch completed, backfill failed) reads "failed at backfill — resumable from the backfill
    stage" (a Resume skips the completed fetch — zero provider calls); a `resumable` 429 pause reads the
    chunk-resume text."""
    if cp.status == "failed_backfill":
        return (
            "Failed at backfill — the fetch stage completed but the backfill stage failed. "
            "Resumable from the backfill stage (the fetch is skipped — zero provider calls)."
        )
    return (
        f"Paused — hit a provider rate-limit (429); progress saved at chunk "
        f"{cp.next_chunk_index}/{cp.chunk_total} ({symbols_remaining} symbols remaining). Resume to continue."
    )


def _run_state_text(run: DataProviderRun) -> str:
    """The plain-language state for a partial/failed operational `DataProviderRun` row (J-38)."""
    total = run.symbols_ok + run.symbols_failed
    if run.status == "failed":
        return f"Failed — every symbol failed ({run.symbols_failed} of {total}); provider unreachable."
    return (
        f"Partial — {run.symbols_ok}/{total} symbols ok, {run.symbols_failed} failed. "
        f"Retry re-fetches only the outstanding/failed work (idempotent — no duplicate bar)."
    )


def _checkpoint_unfinished_row(cp: ImportCheckpoint) -> dict:
    """One unified Unfinished-imports row for a resumable CHECKPOINT (action: Resume / Remove). Generalizes
    `_summarize_checkpoint` with a stable `record_type`/`id`/`state`/`actions` shape shared with run rows."""
    base = _summarize_checkpoint(cp)
    base.update({
        "record_type": "checkpoint",
        "id": cp.import_id,  # the import_id drives resume/dismiss/retry endpoints
        "state": _resumable_state_text(cp, base["symbols_remaining"]),
        "actions": ["resume", "remove"],
    })
    return base


def _run_unfinished_row(run: DataProviderRun) -> dict:
    """One unified Unfinished-imports row for a partial/failed operational RUN (action: Retry / Dismiss).
    Reads the canonical run-history summary (so kind/start/end/counts match Run history exactly) and adds
    the unified shape. NEVER carries a key value (the summarized run has no key column)."""
    summary = summarize_provider_run(run)
    return {
        "record_type": "run",
        "id": run.id,  # the run id drives retry/dismiss endpoints
        "import_id": None,  # a run is not a durable checkpoint (no chunk resume point)
        "source": run.provider,
        "kind": summary.get("kind"),
        "start": summary.get("start"),
        "end": summary.get("end"),
        "chunk_index": None,
        "chunk_total": None,
        "symbols_total": run.symbols_ok + run.symbols_failed,
        "symbols_ok": run.symbols_ok,
        "symbols_failed": run.symbols_failed,
        "symbols_remaining": run.symbols_failed,  # the outstanding (failed) work a Retry re-attempts
        "bars_fetched": summary.get("bars_fetched"),
        "status": run.status,  # partial | failed
        "updated_at": run.finished_at.isoformat() if run.finished_at else (
            run.started_at.isoformat() if run.started_at else None
        ),
        "state": _run_state_text(run),
        "actions": ["retry", "dismiss"],
    }


def unfinished_imports(session: Session, config: Optional[Config] = None) -> list[dict]:
    """J-38 — the UNIFIED Unfinished-imports list: a read-only union of every import that did NOT finish
    cleanly, newest first, each with a PLAIN-LANGUAGE state + the right action:
      - resumable `import_checkpoints` (status `resumable` 429-pause OR `failed_backfill` J-59:
        fetch-done/backfill-failed → resumable from the backfill stage)         → Resume / Remove
      - operational `DataProviderRun` rows with status ∈ {partial, failed}, EXCLUDING soft-dismissed
        ones (`dismissed == True`), the plain seed-load row (a non-job message), AND any run whose
        `job_id` is already offered as a `failed_backfill` checkpoint (so a `both` job stopped at backfill
        appears ONCE — as the Resume-at-backfill row, not also as a Retry row)  → Retry / Dismiss
    Reads the canonical job-control rows ONLY (it neither recomputes a canonical value nor reads a snapshot);
    NEVER carries a key value (neither the checkpoint nor the run summary has a key column)."""
    cp_rows = session.exec(
        select(ImportCheckpoint)
        .where(ImportCheckpoint.status.in_(list(RESUMABLE_CHECKPOINT_STATUSES)))
        .order_by(ImportCheckpoint.updated_at.desc(), ImportCheckpoint.id.desc())
    ).all()
    run_rows = session.exec(
        select(DataProviderRun)
        .where(DataProviderRun.status.in_(["partial", "failed"]))
        .where(DataProviderRun.dismissed == False)  # noqa: E712 — soft-dismissed runs are not offered
        .order_by(DataProviderRun.started_at.desc(), DataProviderRun.id.desc())
    ).all()
    # J-59: a `both` job stopped at its backfill stage has BOTH a `failed_backfill` checkpoint (Resume) and
    # a `failed` run record — offer it ONCE as the Resume-at-backfill row, not also as a duplicate Retry.
    backfill_resumable_job_ids = {cp.import_id for cp in cp_rows if cp.status == "failed_backfill"}
    # A run only counts as an actionable import if it is a Data Manager JOB (has a JSON `kind` detail) —
    # a plain seed-load failure (raw-text message) is not a retryable import job.
    rows: list[dict] = [_checkpoint_unfinished_row(cp) for cp in cp_rows]
    for run in run_rows:
        if run.job_id in backfill_resumable_job_ids:
            continue  # already offered as a Resume-at-backfill checkpoint row (J-59 dedup)
        if summarize_provider_run(run).get("kind") is not None:
            rows.append(_run_unfinished_row(run))
    return rows


# --------------------------------------------------------------------------------------------------
# J-38 — Retry / Dismiss actions (engine helpers; the API maps unknown ids → 404, etc.)
# --------------------------------------------------------------------------------------------------
def get_provider_run(session: Session, run_id: int) -> Optional[DataProviderRun]:
    """The operational run row for `run_id`, or None — used by the API to map an unknown id → 404."""
    return session.get(DataProviderRun, run_id)


def retry_run(
    run_id: int,
    *,
    api_key: Optional[str] = None,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
) -> str:
    """J-38 Retry — re-dispatch ONLY the outstanding/failed work of a partial/failed `DataProviderRun`
    through the EXISTING J-34 chunked import engine (`start_data_job`, the ONE fetch path). The re-run
    covers the SAME job kind + `[start, end]` window; per-`(symbol, date)` idempotency (the INSERT-new-only
    `DailyPrice` guard) means it re-fetches/duplicates NOTHING already stored, so a Retry that fully
    succeeds reaches the SAME dataset it would have without the failure. The session-only `api_key` is
    threaded request-only (never persisted). Returns the NEW job_id. The original audit run is NEVER
    mutated/deleted (a fresh DataProviderRun records the retry outcome). Raises `LookupError` for an
    unknown id and `ValueError` for a non-retryable run (not partial/failed, or not a Data Manager job)."""
    cfg = config or get_config()
    eng = engine or get_engine()
    with Session(eng) as session:
        run = session.get(DataProviderRun, run_id)
        if run is None:
            raise LookupError(f"unknown run: {run_id}")
        if run.status not in ("partial", "failed"):
            raise ValueError(f"run {run_id} is not retryable (status {run.status})")
        summary = summarize_provider_run(run)
        kind = summary.get("kind")
        start_s = summary.get("start")
        end_s = summary.get("end")
        source = run.provider
    if kind is None or start_s is None or end_s is None:
        raise ValueError(f"run {run_id} is not a retryable import job (no job parameters recorded)")
    return start_data_job(
        kind, date_cls.fromisoformat(start_s), date_cls.fromisoformat(end_s),
        source=source, api_key=api_key, config=cfg, engine=eng,
    )


def dismiss_import(
    session: Session,
    record_type: str,
    record_id: str,
    *,
    config: Optional[Config] = None,
) -> dict:
    """J-38 Remove/Dismiss — drop ONLY the actionable JOB-CONTROL record so the item stops being offered
    in `unfinished_imports`:
      - `record_type == "checkpoint"`: DELETE the resumable `ImportCheckpoint` row (a durable resume
        point — pure job-control state, NOT a snapshot).
      - `record_type == "run"`: set the soft-dismiss flag (`DataProviderRun.dismissed = True`) — the run
        STAYS in the append-only Run-history audit (it is only filtered out of the actionable list).
    It MUST NOT delete/hide/mutate any immutable `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns`
    row OR the append-only `data_provider_runs` audit entry (the run still appears in Run history). Raises
    `LookupError` for an unknown id (the API maps it to 404)."""
    if record_type == "checkpoint":
        cp = session.exec(
            select(ImportCheckpoint).where(ImportCheckpoint.import_id == record_id)
        ).first()
        if cp is None:
            raise LookupError(f"unknown import: {record_id}")
        session.delete(cp)  # delete ONLY the job-control checkpoint — no bar/snapshot is touched
        session.commit()
        return {"record_type": "checkpoint", "id": record_id, "dismissed": True}
    if record_type == "run":
        try:
            run_id = int(record_id)
        except (TypeError, ValueError) as exc:
            raise LookupError(f"unknown run: {record_id}") from exc
        run = session.get(DataProviderRun, run_id)
        if run is None:
            raise LookupError(f"unknown run: {record_id}")
        run.dismissed = True  # soft-dismiss ONLY — the audit row is preserved in Run history
        session.add(run)
        session.commit()
        return {"record_type": "run", "id": run_id, "dismissed": True}
    raise LookupError(f"unknown record type: {record_type!r}")
