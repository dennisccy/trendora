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
from app.engine.prices import bars_asof, latest_data_date
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
    for entry in cfg.data_manager.providers:
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
    message: str = ""
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None

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
        entry = cfg.data_manager.provider_by_id(source)
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
    state): the resume point + cumulative counters + status + `updated_at`. Committed so the row survives
    a backend restart (the durability the Resume affordance depends on)."""
    checkpoint.next_chunk_index = next_idx
    checkpoint.symbols_ok = prog.symbols_ok
    checkpoint.symbols_failed = prog.symbols_failed
    checkpoint.bars_fetched = prog.bars_fetched
    checkpoint.status = status
    checkpoint.updated_at = _utcnow()
    session.add(checkpoint)
    session.commit()


def _finalize_checkpoint(session: Session, checkpoint: ImportCheckpoint, prog: JobProgress) -> None:
    """Mark a completed (un-paused) fetch's checkpoint terminal: `failed` iff a fetch was attempted and
    EVERY symbol failed, else `ok` — so it never lingers as `resumable` (a completed import is not
    resumable: a resume of it → 409)."""
    terminal = "failed" if (prog.symbols_total > 0 and prog.symbols_ok == 0) else "ok"
    _advance_checkpoint(session, checkpoint, prog, next_idx=checkpoint.chunk_total, status=terminal)


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
) -> None:
    """Run the chunk plan from `start_chunk`, persisting the checkpoint AFTER each completed chunk (so
    `next_chunk_index` only advances once a chunk fully finishes). Per chunk, fetch each symbol over the
    chunk's date-window and persist only NEW `(symbol, date)` rows via the existing INSERT-new-only
    `_existing_dates` guard — so a committed bar is NEVER overwritten and a resume re-fetches/duplicates
    nothing (per-`(symbol, date)` idempotency).

      * `RateLimitError` beyond `max_retries` ⇒ stop GRACEFULLY: set the job + checkpoint `resumable`
        (distinct from `failed`), leave `next_chunk_index` at the un-finished chunk, and RETURN — never
        raise, never fabricate a bar (anti-goals: No fabricated data; Live fetch is real-data-only).
      * a non-429 `ProviderUnavailableError` for a symbol ⇒ count it failed, record a REDACTED error
        (the resolved key scrubbed), and continue — unchanged from the single-shot loop.
    """
    chunking = cfg.data_manager.import_chunking
    prog.chunk_index = start_chunk
    for chunk_idx in range(start_chunk, len(chunks)):
        sym_batch, (ws, we) = chunks[chunk_idx]
        for symbol in sym_batch:
            try:
                bars = _fetch_symbol_with_retry(
                    provider, symbol, ws, we, chunking=chunking, sleep_fn=sleep_fn
                )
            except RateLimitError:
                # Persistent rate-limit → graceful resumable stop. Do NOT advance next_chunk_index: the
                # current chunk is un-finished, so Resume re-attempts from it (idempotent — committed
                # bars are skipped by _existing_dates). Persist, then return (no raise, no fabrication).
                prog.status = "resumable"
                _advance_checkpoint(session, checkpoint, prog, next_idx=chunk_idx, status="resumable")
                prog.message = _final_summary(prog)
                return
            except ProviderUnavailableError as exc:
                prog.symbols_failed += 1
                _record_error(prog, scrub(f"{symbol}: {exc}"))
                prog.message = _fetch_message(prog)
                continue
            already = _existing_dates(session, symbol, ws, we)
            new_rows = [
                {
                    "symbol": symbol,
                    "date": bar.date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                for bar in bars
                if bar.date not in already
            ]
            if new_rows:
                session.execute(insert(DailyPrice.__table__), new_rows)
                session.commit()
                prog.bars_fetched += len(new_rows)
            prog.symbols_ok += 1
            prog.message = _fetch_message(prog)
            if chunking.inter_request_sleep_seconds:
                sleep_fn(chunking.inter_request_sleep_seconds)  # polite delay between requests (injectable)
        # the chunk fully completed → advance the durable resume point + persist cumulative counters
        prog.chunk_index = chunk_idx + 1
        _advance_checkpoint(session, checkpoint, prog, next_idx=chunk_idx + 1, status="running")


def _do_backfill(session: Session, cfg: Config, prog: JobProgress) -> None:
    """For each in-range trading day with bars but NO snapshot, create the immutable snapshot via the
    EXISTING `scanner.run_scan` (create-once, bars <= D) then INSERT its realized forward returns via
    `forward_testing.backfill_run_forward_returns` (bars > D). No scan/return math is re-implemented and
    no snapshot is overwritten — this is pure orchestration of the registered canonical paths."""
    trading_days = _trading_days(session, cfg)
    snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
    targets = [d for d in trading_days if prog.start <= d <= prog.end and d not in snapshot_dates]
    prog.dates_total = len(targets)
    prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
    for d in targets:
        run = scanner.run_scan(session, d, cfg)  # create-once; recomputes nothing
        result = forward_testing.backfill_run_forward_returns(session, run, cfg)  # INSERT-only, bars > D
        prog.snapshots_created += 1
        prog.forward_returns_inserted += result["rows_inserted"]
        prog.dates_done += 1
        prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"


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
        statuses.append("ok")  # deterministic; an exception is handled separately as `failed`
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
        parts.append(
            f"backfill: {prog.snapshots_created} snapshots over {prog.dates_total} dates, "
            f"{prog.forward_returns_inserted} forward returns"
        )
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


def _persist_run(engine: Engine, cfg: Config, prog: JobProgress) -> None:
    """Persist the FINAL job summary ONCE to the append-only `DataProviderRun` (own session; INSERT
    only — never an UPDATE of an existing row). Structured detail is JSON-encoded in `message`."""
    detail = {
        "kind": prog.kind,
        "start": prog.start.isoformat(),
        "end": prog.end.isoformat(),
        "snapshots_created": prog.snapshots_created,
        "dates_done": prog.dates_done,
        "dates_total": prog.dates_total,
        "forward_returns_inserted": prog.forward_returns_inserted,
        "bars_fetched": prog.bars_fetched,
        # J-35 expand: the screen outcome on the append-only audit row (descriptive job-control values —
        # NOT a recompute of any canonical score/return/bucket). Present only for an expand kind.
        "passers": prog.passers if prog.kind in _EXPAND_KINDS else None,
        "omitted_total": prog.omitted_total if prog.kind in _EXPAND_KINDS else None,
        "summary": _final_summary(prog),
    }
    with Session(engine) as session:
        session.add(
            DataProviderRun(
                provider=_provider_label(prog, cfg),
                started_at=prog.started_at,
                finished_at=prog.finished_at,
                symbols_ok=prog.symbols_ok,
                symbols_failed=prog.symbols_failed,
                status=prog.status,
                message=json.dumps(detail),
            )
        )
        session.commit()


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
    # Both a generic FETCH and an EXPAND run the SAME chunked/resumable OHLCV fetch engine (J-34, reused
    # not forked); they differ only in the symbol set (all seed symbols vs the committed POOL) and in the
    # EXTRA screen step expand runs afterward.
    pool: list[dict] = []
    checkpoint: Optional[ImportCheckpoint] = None  # hoisted: an expand finalizes it AFTER the screen step
    try:
        with Session(eng) as session:
            if prog.kind in _FETCH_KINDS or is_expand:
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
                _run_chunked_fetch(
                    session, cfg, prog, live, chunks=chunks, checkpoint=checkpoint,
                    scrub=scrub, sleep_fn=sleep_fn, start_chunk=start_chunk,
                )
                if prog.status == "resumable":
                    paused = True  # graceful pause — checkpoint already persisted resumable
                elif not is_expand:
                    # an EXPAND's checkpoint is finalized only AFTER the screen step completes (so a cap-feed
                    # pause in the screen leaves the durable row `resumable` — see below); a generic fetch
                    # has no further step, so finalize now.
                    _finalize_checkpoint(session, checkpoint, prog)
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
                elif checkpoint is not None:
                    _finalize_checkpoint(session, checkpoint, prog)  # expand fully done → terminal checkpoint
            if not paused and prog.kind in _BACKFILL_KINDS:
                _do_backfill(session, cfg, prog)
        if not paused:
            prog.status = _final_status(prog)
    except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job (scrubbed)
        prog.status = "failed"
        _record_error(prog, scrub(str(exc)))
    finally:
        prog.finished_at = _utcnow()
        prog.message = _final_summary(prog)
        # A resumable pause is recorded DURABLY on the checkpoint (it survives a restart and drives
        # `resumable_imports`); it is NOT a terminal run, so it is not appended to the run-history log —
        # the eventual completed resume appends its own DataProviderRun.
        if prog.status != "resumable":
            try:
                _persist_run(eng, cfg, prog)
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
        if cp.status != "resumable":
            raise ValueError(f"import {import_id} is not resumable (status {cp.status})")
        prog = JobProgress(job_id=cp.import_id, kind=cp.kind, start=cp.start, end=cp.end, source=cp.source)
        prog.symbols_ok = cp.symbols_ok
        prog.symbols_failed = cp.symbols_failed
        prog.bars_fetched = cp.bars_fetched
        prog.chunk_total = cp.chunk_total
        prog.chunk_index = cp.next_chunk_index
        prog.symbols_total = len(json.loads(cp.symbol_plan_json))
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
    thread = threading.Thread(
        target=run_data_job,
        args=(job.job_id,),
        kwargs={"config": cfg, "engine": eng, "api_key": api_key, "symbols": symbols},
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
        "status": cp.status,
        "updated_at": cp.updated_at.isoformat() if cp.updated_at else None,
    }


def resumable_imports(session: Session, config: Optional[Config] = None) -> list[dict]:
    """The paused (`status == "resumable"`) chunked imports, newest first — the durable Resume
    affordance that SURVIVES a backend restart (the in-memory job is gone, but the checkpoint persists).
    NEVER carries a key value."""
    rows = session.exec(
        select(ImportCheckpoint)
        .where(ImportCheckpoint.status == "resumable")
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
    """The plain-language state for a paused/resumable checkpoint row (J-38)."""
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
      - paused/resumable `import_checkpoints` (status `resumable`)            → Resume / Remove
      - operational `DataProviderRun` rows with status ∈ {partial, failed}, EXCLUDING soft-dismissed
        ones (`dismissed == True`) and EXCLUDING the plain seed-load row (a non-job message)  → Retry / Dismiss
    Reads the canonical job-control rows ONLY (it neither recomputes a canonical value nor reads a snapshot);
    NEVER carries a key value (neither the checkpoint nor the run summary has a key column)."""
    cp_rows = session.exec(
        select(ImportCheckpoint)
        .where(ImportCheckpoint.status == "resumable")
        .order_by(ImportCheckpoint.updated_at.desc(), ImportCheckpoint.id.desc())
    ).all()
    run_rows = session.exec(
        select(DataProviderRun)
        .where(DataProviderRun.status.in_(["partial", "failed"]))
        .where(DataProviderRun.dismissed == False)  # noqa: E712 — soft-dismissed runs are not offered
        .order_by(DataProviderRun.started_at.desc(), DataProviderRun.id.desc())
    ).all()
    # A run only counts as an actionable import if it is a Data Manager JOB (has a JSON `kind` detail) —
    # a plain seed-load failure (raw-text message) is not a retryable import job.
    rows: list[dict] = [_checkpoint_unfinished_row(cp) for cp in cp_rows]
    for run in run_rows:
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
