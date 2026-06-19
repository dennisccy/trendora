"""bars_asof / bars_after — the two no-lookahead boundaries (anti-goal: No lookahead).

`bars_asof(session, symbol, d)` returns the symbol's `daily_prices` rows with **date <= d**,
ascending by date. EVERY scoring/regime/sector computation reads bars through this accessor and
never touches a bar with date > d, so a snapshot dated D is computed only from information
available on D (the backward boundary — the AS-OF score side).

`bars_after(session, symbol, d)` is its strict inverse: the rows with **date > d**, ascending.
The iter-6 walk-forward forward-testing engine measures realized forward returns ONLY through
`bars_after` (date > D), so realized returns are drawn exclusively from POST-snapshot data and a
future bar can never influence an as-of score. Together the two accessors partition a symbol's
history at D with no overlap (date <= d vs date > d) — that disjointness IS the no-lookahead proof.

Also provides the tiny ascending-series extractors the indicator functions consume.
"""
from __future__ import annotations

import bisect
import threading
from contextlib import contextmanager
from datetime import date as date_cls
from typing import Iterator, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import DailyPrice


def latest_data_date(session: Session) -> Optional[date_cls]:
    """The latest date present in `daily_prices` = the deterministic as-of date for a request.
    None when no price data exists (callers surface an explicit unavailable state)."""
    return session.scalar(select(func.max(DailyPrice.date)))


# --------------------------------------------------------------------------------------------------
# J-46 — load-once bar cache (Capability 33): an OPT-IN, per-session optimization at the single
# `bars_asof` seam. A multi-date backfill calls `bars_asof(symbol, D)` once PER DATE today, so each
# symbol's full history is loaded K+ times for a K-date job. When a `bar_cache(session)` context is
# active, the FIRST `bars_asof` for a symbol loads its FULL stored series ONCE (one ordered query) and
# every subsequent call slices `date <= D` IN MEMORY — preserving today's exact ordering/contents (the
# `(symbol, date)` unique constraint means the date-ordered list has no ties, so a date-filtered slice
# of the full ordered list is byte-identical to today's date-filtered query).
#
# It is a LOADING optimization beneath the registered engines — NOT a second source of bar truth: it
# reads the SAME `daily_prices` rows the per-request path reads, is keyed by `id(session)` (so only the
# session inside the `with` block is cached), and dies when the block exits (no staleness across jobs;
# a fetch job that ADDS bars must run OUTSIDE any cache context — the backfill stage opens its own).
# The default per-request read path (no active context) is completely unchanged.
# --------------------------------------------------------------------------------------------------
class _BarCache:
    """A per-session memo of each symbol's FULL date-ordered series, loaded once on first request.

    A cache may be SHARED read-only across threads (J-53: the parallel multi-date backfill pre-fills one
    cache on the orchestrating session, then every worker session reads bars from that SAME pre-loaded
    cache so each symbol's series is loaded ONCE for the whole job — the J-46 load-once-per-job
    guarantee, preserved under parallelism). A small lock guards the lazy-load mutation so a symbol NOT
    pre-loaded (defensive) is still loaded exactly once even if two workers race for it; once `prefill`
    has loaded every symbol up front, the hot path is a pure lock-free read of immutable lists."""

    def __init__(self) -> None:
        self._by_symbol: dict[str, list[DailyPrice]] = {}
        self._dates_by_symbol: dict[str, list[date_cls]] = {}
        self._load_lock = threading.Lock()

    def prefill(self, session: Session) -> None:
        """Load EVERY symbol's full date-ordered series ONCE, in ONE query, on `session` (the
        orchestrating thread, before any worker fan-out). After this, a shared read across worker
        threads needs no further bar-store load — so a K-date parallel backfill loads each symbol once
        for the whole job (J-46), not once per worker session. Same rows/order as the lazy path: ordered
        by (symbol, date); the (symbol, date) unique constraint guarantees no ties."""
        stmt = select(DailyPrice).order_by(DailyPrice.symbol, DailyPrice.date)
        by_symbol: dict[str, list[DailyPrice]] = {}
        for bar in session.exec(stmt).all():
            by_symbol.setdefault(bar.symbol, []).append(bar)
        # publish atomically under the lock so a concurrent reader sees a fully-built map, not a partial.
        with self._load_lock:
            for symbol, full in by_symbol.items():
                if symbol not in self._by_symbol:  # never overwrite a series already loaded
                    self._by_symbol[symbol] = full
                    self._dates_by_symbol[symbol] = [bar.date for bar in full]

    def bars_asof(self, session: Session, symbol: str, d: date_cls) -> list[DailyPrice]:
        full = self._by_symbol.get(symbol)
        if full is None:
            # lazy load (defensive — a pre-filled cache rarely reaches here): guard the mutation so a
            # shared cache loads a missing symbol exactly once even under concurrent worker access.
            with self._load_lock:
                full = self._by_symbol.get(symbol)
                if full is None:
                    # one ordered query for the symbol's WHOLE series — the SAME ordering today's
                    # bars_asof uses (order by date; the unique constraint guarantees no ties).
                    stmt = (
                        select(DailyPrice)
                        .where(DailyPrice.symbol == symbol)
                        .order_by(DailyPrice.date)
                    )
                    full = list(session.exec(stmt).all())
                    self._by_symbol[symbol] = full
                    self._dates_by_symbol[symbol] = [bar.date for bar in full]
        # slice `date <= d` from the ascending series: bisect_right gives the count of dates <= d, so the
        # returned list equals `[bar for bar in full if bar.date <= d]` exactly (same rows, same order).
        cut = bisect.bisect_right(self._dates_by_symbol[symbol], d)
        return full[:cut]

    def trailing_count(self, session: Session, symbol: str, d: date_cls) -> int:
        """The number of bars for `symbol` with date <= `d` — BYTE-IDENTICAL to
        `len(self.bars_asof(session, symbol, d))` and to a `SELECT count(*) ... WHERE date <= d` grouped
        count (the `(symbol, date)` unique constraint means the date-ordered series has no ties, so the
        bisect over the pre-loaded date list equals the row count exactly). Used by the resolver's
        history-gate prefilter so a multi-date timeline derivation needs ZERO per-date grouped-count
        round-trips (it reads the once-loaded series instead). Lazy-loads a missing symbol exactly once
        (the same guard `bars_asof` uses) so the count is correct even on an un-prefilled cache."""
        if symbol not in self._dates_by_symbol:
            # ensure the series is loaded (re-uses bars_asof's lazy-load + lock); we discard the slice.
            self.bars_asof(session, symbol, d)
        if symbol not in self._dates_by_symbol:
            return 0  # the symbol has no bars at all (never loaded) — zero trailing bars
        return bisect.bisect_right(self._dates_by_symbol[symbol], d)


# Registry keyed by id(session) — a cache is consulted by `bars_asof` ONLY while its session's context
# is active. id(session) is stable for a live session object; the context removes its own entry on exit.
# The registry is guarded by a lock so the J-53 parallel backfill — where several worker threads, each
# with its OWN session, enter/exit a `bar_cache` context concurrently — registers/clears its (distinct)
# keys without racing on the shared dict. Each session keys a SEPARATE cache (distinct `id(session)`),
# so a per-session `_BarCache` is still only ever touched by its own single thread (no shared mutation
# of a cache instance) — the lock guards only the registry dict's insert/lookup/pop.
_BAR_CACHES: dict[int, _BarCache] = {}
_BAR_CACHES_LOCK = threading.Lock()


@contextmanager
def bar_cache(session: Session) -> Iterator[_BarCache]:
    """Activate the load-once bar cache for `session` for the duration of the `with` block (J-46).

    While active, every `bars_asof(session, symbol, d)` call — at EVERY engine call site, with no
    signature change — loads each symbol's full series once and slices `date <= d` in memory. On exit
    the cache is dropped, so it never outlives the job and never serves a stale series across a
    data-mutating stage. Re-entrant for the SAME session: a nested context reuses the outer cache (so a
    backfill that nests sub-loops shares one load); only the OUTERMOST exit clears it.

    Thread-safe registry (J-53): the insert/lookup/pop of the shared `_BAR_CACHES` dict is lock-guarded
    so concurrent backfill workers (each on its OWN session ⇒ a distinct key) never race the dict; a
    given session's `_BarCache` is still only ever read/written by that session's single owning thread.

    USE ONLY around READ-ONLY multi-date snapshot loops (`_do_backfill`, the warm-up cadence): a stage
    that ADDS bars must run outside the context so a later read never sees a stale cached series."""
    key = id(session)
    with _BAR_CACHES_LOCK:
        existing = _BAR_CACHES.get(key)
        if existing is None:
            cache = _BarCache()
            _BAR_CACHES[key] = cache
        else:
            cache = existing
    if existing is not None:
        # already cached for this session (re-entrant / nested) — reuse it; the outer context owns cleanup
        yield existing
        return
    try:
        yield cache
    finally:
        with _BAR_CACHES_LOCK:
            _BAR_CACHES.pop(key, None)


@contextmanager
def prefilled_bar_cache(session: Session) -> Iterator[_BarCache]:
    """Like `bar_cache`, but PRE-FILLS every symbol's full series up front in ONE query (J-53). Returns
    the cache so it can be SHARED with worker sessions via `attach_shared_cache` — so a parallel
    multi-date backfill loads each symbol ONCE for the whole job (the J-46 load-once-per-job guarantee),
    not once per worker session. The orchestrating thread owns this context; workers only READ the
    pre-loaded immutable series."""
    with bar_cache(session) as cache:
        cache.prefill(session)
        yield cache


@contextmanager
def attach_shared_cache(session: Session, cache: _BarCache) -> Iterator[None]:
    """Bind an EXISTING (pre-filled) `_BarCache` to `session`'s id for the `with` block so this session's
    `bars_asof` reads the SHARED pre-loaded series (J-53 worker side) — no extra bar-store load. The
    shared cache's series are immutable after `prefill`, so concurrent worker reads are safe; the lazy-
    load lock covers the rare un-prefilled symbol. The orchestrating context owns the cache's lifetime;
    this only registers/unregisters the worker session's view of it."""
    key = id(session)
    with _BAR_CACHES_LOCK:
        had = key in _BAR_CACHES
        if not had:
            _BAR_CACHES[key] = cache
    try:
        yield
    finally:
        if not had:
            with _BAR_CACHES_LOCK:
                _BAR_CACHES.pop(key, None)


def active_bar_cache(session: Session) -> Optional["_BarCache"]:
    """The load-once bar cache bound to `session` (inside an active `bar_cache`/`prefilled_bar_cache`
    context), or None when no context is active. A read-path helper (the resolver's history-gate
    prefilter) uses this to source trailing-bar counts from the once-loaded series instead of a per-date
    grouped-count round-trip — WITHOUT changing the default (no-context) path, which stays byte-identical."""
    return _BAR_CACHES.get(id(session))


def bars_asof(session: Session, symbol: str, d: date_cls) -> list[DailyPrice]:
    """All bars for `symbol` with date <= `d`, ascending. The backward no-lookahead boundary.

    When a `bar_cache(session)` context is active (J-46), this slices the symbol's once-loaded full
    series in memory; otherwise it runs the original per-request date-bounded query (the default path,
    byte-identical to before). Either way it returns exactly the bars with date <= d, ascending."""
    cache = _BAR_CACHES.get(id(session))
    if cache is not None:
        return cache.bars_asof(session, symbol, d)
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date <= d)
        .order_by(DailyPrice.date)
    )
    return list(session.exec(stmt).all())


def close_on(session: Session, symbol: str, d: date_cls) -> Optional[float]:
    """The close of the latest bar with **date <= `d`** (the as-of close on D), or None when the
    symbol has no bar on/before D. This is the single-bar form of `bars_asof(session, symbol, d)[-1]
    .close` — the SAME backward boundary (date <= d, no lookahead) — but it fetches only the one bar
    instead of materializing the symbol's full pre-history, so the walk-forward backfill can read each
    forward return's entry close cheaply."""
    stmt = (
        select(DailyPrice.close)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date <= d)
        .order_by(DailyPrice.date.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def bars_after(
    session: Session, symbol: str, d: date_cls, limit: Optional[int] = None
) -> list[DailyPrice]:
    """All bars for `symbol` with **date > `d`**, ascending — the strict inverse of `bars_asof`
    and the forward no-lookahead boundary used by the walk-forward forward-testing engine.

    `limit` (optional) caps the number of leading post-snapshot bars returned. A forward return
    over `horizon` trading days only needs the first `horizon` post-bars, so the backfill passes
    `limit=max(horizons)` to avoid materializing the full multi-year tail per (symbol, run); the
    result is byte-identical to the unbounded call truncated to `limit` (the boundary is unchanged,
    only later, irrelevant bars are not fetched). The no-lookahead boundary test calls it WITHOUT a
    limit and asserts no returned bar has date <= d."""
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date > d)
        .order_by(DailyPrice.date)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(session.exec(stmt).all())


def bars_through_latest(session: Session, symbol: str) -> list[DailyPrice]:
    """All bars for `symbol`, ascending — the symbol's FULL price path, NOT bounded by any as-of date
    (distinct from `bars_asof`). DISPLAY-ONLY (J-20): the Stock-Detail chart renders this full path so a
    user viewing a historical as-of D can see what happened AFTER the snapshot, with D marked and the
    post-D region labelled forward/after-as-of.

    CRITICAL no-lookahead carve-out: the bars this returns with date > D are VISUALIZATION ONLY. They
    MUST NOT feed any score, bucket, setup status, VCP flag, factor, or ranking — all of which keep
    reading `bars_asof` (date <= D). This accessor is therefore NEVER routed into `scoring.score_stocks`
    / `patterns.detect_vcp` / `scanner.run_scan`; its sole caller is the chart endpoint. For a historical
    D the full path equals `bars_asof(symbol, D)` ++ `bars_after(symbol, D)` exactly (a disjoint partition
    at D), so the labelled forward region is precisely the post-D bars the scoring side never reads."""
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.symbol == symbol)
        .order_by(DailyPrice.date)
    )
    return list(session.exec(stmt).all())


# --- ascending-series extractors (the indicator functions take plain float lists) ----------
def closes(bars: list[DailyPrice]) -> list[float]:
    return [b.close for b in bars]


def highs(bars: list[DailyPrice]) -> list[float]:
    return [b.high for b in bars]


def lows(bars: list[DailyPrice]) -> list[float]:
    return [b.low for b in bars]


def volumes(bars: list[DailyPrice]) -> list[float]:
    return [b.volume for b in bars]
