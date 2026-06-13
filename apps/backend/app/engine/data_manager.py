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

import csv
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import delete, func, insert
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, ImportChunkingCfg, ProviderCatalogEntry, get_config
from app.data_providers import make_provider
from app.data_providers.base import PriceProvider, ProviderUnavailableError, RateLimitError
from app.data_providers.seed_provider import symbol_to_filename
from app.db import get_engine
from app.engine import forward_testing, scanner
from app.engine.prices import attach_shared_cache, bar_cache, bars_asof, latest_data_date, prefilled_bar_cache
from app.engine.universe_screen import DEFAULT_SEED_DIR, read_pool, screen_reasons
from app.models import (
    DailyPrice,
    DataProviderRun,
    ForwardReturn,
    ImportCheckpoint,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)
from app.seed_loader import all_seed_symbols

# Injectable sleep (J-34): the chunked fetch's inter-request delay + 429 backoff call this. Tests pass
# their own recorder so backoff/sleep add NO wall-clock (MEMORY: backend-test-suite-runtime).
_sleep: Callable[[float], None] = time.sleep

JOB_KINDS = ("fetch", "backfill", "both", "expand")
_FETCH_KINDS = ("fetch", "both")
_BACKFILL_KINDS = ("backfill", "both")
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
            own_dates = set(session.exec(
                select(DailyPrice.date)
                .where(DailyPrice.symbol == symbol)
                .where(DailyPrice.date >= first)
                .where(DailyPrice.date <= last)
            ).all())
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


def compute_coverage(session: Session, config: Optional[Config] = None) -> dict:
    """Current dataset coverage — purely descriptive, recomputing NO canonical value:
      - price-history date range (min/max `DailyPrice.date`) and distinct symbol count,
      - the set of snapshot/as-of dates (`ScannerRun.asof_date`), newest first,
      - GAPS = trading days (bars present) with no snapshot — the actionable backfill targets — with a
        count plus a bounded preview (`config.data_manager.gap_preview`),
      - (J-36) `per_symbol` — the per-symbol / per-universe-member coverage table (see
        `_per_symbol_coverage`), consistency-bound to the aggregates below: the distinct-symbol (has-data)
        row count == `symbol_count` and the in-universe row count == `universe_count` (same sources)."""
    cfg = config or get_config()
    price_min = session.scalar(select(func.min(DailyPrice.date)))
    price_max = session.scalar(select(func.max(DailyPrice.date)))
    symbol_count = session.scalar(select(func.count(func.distinct(DailyPrice.symbol))))

    snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
    snapshot_set = set(snapshot_dates)
    trading_days = _trading_days(session, cfg)
    gaps = [d for d in trading_days if d not in snapshot_set]
    preview = cfg.data_manager.gap_preview

    return {
        "price_start": price_min.isoformat() if price_min else None,
        "price_end": price_max.isoformat() if price_max else None,
        "symbol_count": int(symbol_count or 0),
        # the RESOLVED UNIVERSE size — the one canonical `config.universe.symbols` (the committed screen
        # result), read live here and on /api/methodology so the two surfaces never drift (J-22, single
        # source / no recompute). Distinct from `symbol_count` (DISTINCT priced symbols, incl. ETFs+^VIX).
        "universe_count": len(cfg.universe.symbols),
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
def load_seed_windows(seed_dir: Optional[str | Path] = None) -> dict[str, tuple[date_cls, date_cls]]:
    """Read the committed-seed manifest (`<seed_dir>/meta.json`) into the per-symbol seed window map
    `{symbol: (first_date, last_date)}` — the authoritative seed-vs-user-added boundary J-39 reads. A
    `(symbol, date)` with `first <= date <= last` is the COMMITTED SEED (protected); a date beyond `last`
    (or a symbol absent from the manifest) is USER-ADDED (removable). An absent/unreadable manifest yields
    an empty map (so every bar is treated user-added — the safe default for a host with no committed seed
    manifest), never a crash."""
    path = Path(seed_dir or DEFAULT_SEED_DIR) / "meta.json"
    if not path.exists():
        return {}
    try:
        meta = json.loads(path.read_text())
    except (ValueError, OSError):
        return {}
    windows: dict[str, tuple[date_cls, date_cls]] = {}
    for row in meta.get("symbols") or []:
        symbol = row.get("symbol")
        first = row.get("first")
        last = row.get("last")
        if symbol and first and last:
            windows[symbol] = (date_cls.fromisoformat(first), date_cls.fromisoformat(last))
    return windows


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
) -> None:
    """Reject an invalid removal scope explicitly (the API maps the `ValueError` to a 4xx — never a silent
    no-op or accidental wipe): an empty scope (neither symbols nor a range), an inverted range
    (start > end), or an unknown symbol (named but with NO stored bars anywhere)."""
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
) -> dict:
    """The shared read-only analysis behind both the preview and the destructive removal: validate the
    scope, classify in-scope bars into removable (user-added) vs not-removable (committed seed), and
    determine the cascade. Returns a plan dict carrying the removable bars (objects, for the deleter), the
    committed-seed breakdown, the cascade run-ids/dates/counts, and a `refused` flag (+ reason) when the
    scope is wholly committed seed (nothing removable). This function DELETES NOTHING."""
    _validate_remove_scope(session, symbols, start, end)
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
) -> dict:
    """READ-ONLY confirm-preview for a removal scope (J-39): returns exactly what WOULD be removed —
    removable `(symbol, date)` bar count + range + symbols, the not-removable committed-seed breakdown
    (per symbol, reason `"committed seed"`), and the cascade of dependent snapshot/forward-return rows —
    DELETING NOTHING (the DB is byte-unchanged afterward). A wholly-committed-seed scope returns
    `refused=True` with an explicit reason. Raises `ValueError` for an empty/inverted/unknown scope (the
    API maps it to 4xx)."""
    plan = _build_removal_plan(session, config, symbols, start, end, seed_dir)
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
) -> dict:
    """DESTRUCTIVE, seed-safe, cascade-consistent removal (J-39). Deletes ONLY the user-added `DailyPrice`
    rows in scope (whole-row deletes — the committed seed is excluded and un-deletable) and cascade-removes
    the derived snapshot rows (`ScannerRun` + its `ScannerResult` / `SectorScoreRow` / `ThemeScoreRow`
    children) and `ForwardReturn` rows that depended SOLELY on the removed bars — a WHOLE-ROW delete of
    each derived row, NEVER an in-place overwrite of a retained snapshot (so the *Snapshots are immutable*
    identity holds: a fully-covered snapshot is left UNTOUCHED). It FABRICATES NOTHING and never recomputes
    a score/return — it only deletes. The removal is recorded on the append-only `DataProviderRun` audit
    log (the audit trail is NOT deleted). A wholly-committed-seed scope is REFUSED (`ValueError`); raises
    `ValueError` for an empty/inverted/unknown scope too (the API maps these to 4xx)."""
    cfg = config or get_config()
    plan = _build_removal_plan(session, cfg, symbols, start, end, seed_dir)
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
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None
    # J-53 backfill-stage scratch (NOT serialized — internal accumulators the orchestrator fills during
    # the backfill, read once by `_run_job` to `record_stage("backfill", ...)`): the sum of each date's
    # per-date compute seconds (the sequential baseline the parallel wall-clock beats) and the actual
    # concurrency the pool used (min(config workers, target dates)).
    _backfill_per_date_seconds_sum: float = 0.0
    _backfill_concurrency: int = 0

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
    silent no-op): an unknown kind, an inverted range (start > end), a span over the configured
    `data_manager.max_range_days`, an unknown import `source`, or a fetch against a `needs_key` source
    with neither an env key nor a pasted session key. Malformed dates are rejected earlier by the typed
    API model. `source`/`api_key` are validated only when a `source` is supplied; the key is read
    request-only for the gate and is never persisted (anti-goal: keys are env-or-session, never
    persisted)."""
    cfg = config or get_config()
    if kind not in JOB_KINDS:
        raise ValueError(f"unknown job kind {kind!r}; expected one of {list(JOB_KINDS)}")
    if start > end:
        raise ValueError(f"start date {start.isoformat()} must be on or before end date {end.isoformat()}")
    span_days = (end - start).days + 1
    if span_days > cfg.data_manager.max_range_days:
        raise ValueError(
            f"date range too large: {span_days} days exceeds the configured maximum "
            f"{cfg.data_manager.max_range_days}"
        )
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
    """
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
    snapshot is fabricated for the failed date. Bounded like the per-symbol error list."""
    if len(prog.date_failures) < _MAX_ERROR_SAMPLES:
        prog.date_failures.append({"date": d.isoformat(), "error": error})


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

    J-67 — per-date FAILURE ISOLATION + transaction soundness: a single date's compute OR persist failure
    is caught, recorded per-date (honest error), and the orchestrating session is ROLLED BACK to a clean
    state so the REMAINING dates still write (the failure never leaves the session emitting SQL in an
    invalid 'committed' state, and never aborts the whole stage). The stage ends `partial` (graded by the
    caller from `prog.date_failures`); no snapshot is fabricated for a failed date. The worker sessions are
    independent read-only connections (never shared mid-transaction); only THIS thread writes."""
    trading_days = _trading_days(session, cfg)
    snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
    targets = [d for d in trading_days if prog.start <= d <= prog.end and d not in snapshot_dates]
    prog.dates_total = len(targets)
    prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
    workers = cfg.data_manager.import_chunking.backfill_workers  # config pool size (No magic numbers)
    prog._backfill_concurrency = min(workers, len(targets)) if targets else workers
    prog._backfill_per_date_seconds_sum = 0.0
    if not targets:
        return

    def _persist(d: date_cls, payload: Optional[dict], per_date_seconds: float) -> None:
        """Apply ONE date's result on the orchestrating thread (serial, in date order): persist the
        snapshot (or read the existing one — create-once) then INSERT its forward returns. The ONLY
        place a write happens. The pre-filled SHARED cache on THIS session keeps the forward-return reads
        (and the rare race-fallback compute) load-once. A per-date failure here is isolated by the caller
        (it ROLLs BACK the session and records the date failed), so a single bad date never aborts the
        stage nor strands the session in an invalid 'committed' state."""
        prog._backfill_per_date_seconds_sum += per_date_seconds
        prog.tick(f"scanning {d.isoformat()} ({prog.dates_done + 1}/{prog.dates_total})")
        if payload is None:
            run = scanner.get_run_for_date(session, d)  # already present (worker fast-path) — read, don't write
            if run is None:  # a concurrent date created it between the worker check and here — compute now
                run = scanner.run_scan(session, d, cfg)
        else:
            run = scanner.persist_run_payload(session, d, payload, cfg)  # create-once; recomputes nothing
        result = forward_testing.backfill_run_forward_returns(session, run, cfg)  # INSERT-only, bars > D
        prog.snapshots_created += 1
        prog.forward_returns_inserted += result["rows_inserted"]
        prog.dates_done += 1
        prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"

    def _persist_isolated(d: date_cls, payload: Optional[dict], secs: float, compute_error: Optional[str]) -> None:
        """J-67 — write ONE date with failure isolation: if the worker COMPUTE already failed
        (`compute_error` set), record it and skip the write; else attempt the persist and, on a write
        failure, ROLL BACK the orchestrating session (clearing any half-applied SQL so it never lands in
        an invalid 'committed' state) and record the date failed — the remaining dates still write."""
        if compute_error is not None:
            prog._backfill_per_date_seconds_sum += secs
            _record_date_failure(prog, d, compute_error)
            return
        try:
            _persist(d, payload, secs)
        except Exception as exc:  # noqa: BLE001 — isolate this date; the stage continues
            session.rollback()  # clear any half-applied write so the session is usable for the next date
            _record_date_failure(prog, d, str(exc))

    # J-46/J-53: pre-fill ONE shared bar cache on the orchestrating session (every symbol's full series
    # loaded ONCE in one query). Workers ATTACH this same cache (read-only) so the whole K-date job does
    # at most one bar-store load per symbol — load-once-per-job, not once per date NOR once per worker.
    # The orchestrator's own forward-return reads + the race-fallback run_scan also read from it.
    with prefilled_bar_cache(session) as shared_cache:
        if workers <= 1 or len(targets) <= 1:
            # serial baseline (workers=1) — compute + persist inline, one date at a time, in order. A
            # per-date compute failure is caught here (isolated), not raised — the rest still run.
            for d in targets:
                compute_error: Optional[str] = None
                payload: Optional[dict] = None
                secs = 0.0
                try:
                    _, payload, secs = _compute_one_backfill_date(eng, cfg, d, shared_cache)
                except Exception as exc:  # noqa: BLE001 — isolate this date's compute failure
                    compute_error = str(exc)
                _persist_isolated(d, payload, secs, compute_error)
            return
        # PARALLEL: fan out the per-date compute; persist results IN DATE ORDER on this thread as they
        # arrive. A worker compute exception is captured PER DATE (never raised out of the drain loop, so
        # it never aborts the whole stage or deadlocks); the `with ThreadPoolExecutor` joins every worker
        # before returning, so no thread outlives the job (the iter-28 determinism lesson).
        pending: dict[date_cls, tuple[Optional[dict], float, Optional[str]]] = {}
        next_idx = 0
        with ThreadPoolExecutor(max_workers=min(workers, len(targets))) as pool:
            future_to_date = {
                pool.submit(_compute_one_backfill_date, eng, cfg, d, shared_cache): d for d in targets
            }
            for future in as_completed(future_to_date):
                d = future_to_date[future]
                try:
                    _, payload, secs = future.result()
                    pending[d] = (payload, secs, None)
                except Exception as exc:  # noqa: BLE001 — capture this date's compute failure, keep draining
                    pending[d] = (None, 0.0, str(exc))
                # drain any now-contiguous prefix in target (date) order, so writes are strictly ordered.
                while next_idx < len(targets) and targets[next_idx] in pending:
                    cur = targets[next_idx]
                    cur_payload, cur_secs, cur_err = pending.pop(cur)
                    _persist_isolated(cur, cur_payload, cur_secs, cur_err)
                    next_idx += 1


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


def _screen_one_candidate(
    session: Session,
    cfg: Config,
    provider: PriceProvider,
    asof: date_cls,
    symbol: str,
    *,
    scrub: Callable[[str], str],
) -> tuple[Optional[dict], Optional[str]]:
    """Screen ONE pool candidate against REAL committed bars + a REAL market-cap reference, returning
    either `(member_dict, None)` for a passer or `(None, reason)` for an omission. The reference values
    come from stored `DailyPrice` bars (the OHLCV fetch already INSERTed them); the cap comes from the
    provider's market-cap capability. A fetch failure / empty series / missing cap / threshold failure is
    an OMISSION (a reason string) — never a fabricated member/cap/bar. Re-raises `RateLimitError` so the
    caller pauses the WHOLE expand gracefully (the live feed is rate-limited)."""
    filters = cfg.universe.filters
    bars = bars_asof(session, symbol, asof)
    if not bars:
        return None, "empty_series"
    reference_close = bars[-1].close
    adv_rows = bars[-filters.adv_window_days:]
    adv_dollar = sum(b.close * b.volume for b in adv_rows) / len(adv_rows)
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
    for row in pool:
        symbol = row["symbol"]
        try:
            member, reason = _screen_one_candidate(session, cfg, provider, asof, symbol, scrub=scrub)
        except RateLimitError:
            # the cap feed is persistently rate-limited → pause the expand resumable (honest, non-fab).
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
    if prog.kind in _BACKFILL_KINDS:
        # J-67: a single date's failure is ISOLATED (recorded per-date) — the backfill ends `partial`
        # (others completed), never aborting the whole stage. With NO per-date failures it is `ok`. A
        # whole-stage exception (e.g. the trading-calendar read itself) is still graded `failed` by the
        # `_run_job` except-handler separately.
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
    if prog.kind in _BACKFILL_KINDS:
        backfill = (
            f"backfill: {prog.snapshots_created} snapshots over {prog.dates_total} dates, "
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
    return {
        "kind": prog.kind,
        "start": prog.start.isoformat(),
        "end": prog.end.isoformat(),
        "snapshots_created": prog.snapshots_created,
        "dates_done": prog.dates_done,
        "dates_total": prog.dates_total,
        "forward_returns_inserted": prog.forward_returns_inserted,
        "bars_fetched": prog.bars_fetched,
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
        "summary": _final_summary(prog),
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
                    #   - otherwise a generic fetch fetches the existing seed set.
                    # Everything downstream (plan, checkpoint, per-(symbol,date) idempotency) is reused.
                    if is_expand:
                        symbols = [row["symbol"] for row in pool]
                    elif symbols_override is not None:
                        symbols = list(symbols_override)
                    else:
                        symbols = all_seed_symbols(cfg)
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
                # J-59 resume-at-backfill: the fetch stage already completed (zero provider calls now). Load
                # the existing checkpoint so the post-backfill finalize/fail-marking has it. NO live provider
                # is built, NO chunk is fetched.
                checkpoint = _load_checkpoint(session, prog.job_id)
                if checkpoint is not None:
                    prog.chunk_total = checkpoint.chunk_total
                    checkpoint.status = "running"
                    checkpoint.updated_at = _utcnow()
                    session.add(checkpoint)
                    session.commit()
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
            prog.status = _final_status(prog)
    except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job (scrubbed)
        prog.status = "failed"
        _record_error(prog, scrub(str(exc)))
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
    with _LOCK:
        _JOBS[prog.job_id] = prog
    return _run_job(
        prog, cfg=cfg, eng=eng, provider=provider, api_key=api_key,
        sleep_fn=sleep_fn or _sleep, is_resume=True,
        seed_dir=Path(seed_dir) if seed_dir else DEFAULT_SEED_DIR,
    )


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
    thread.start()
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
    thread.start()
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
