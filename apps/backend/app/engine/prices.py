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
from typing import Iterable, Iterator, NamedTuple, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import get_config
from app.models import DailyPrice


class Bar(NamedTuple):
    """A lightweight, immutable row-slice used by the load-once bar cache (J-46) instead of a full
    `DailyPrice` ORM instance (iter-19 — the OOM fix). Exposes EXACTLY the attributes every downstream
    consumer reads off a cached bar — `.date/.open/.high/.low/.close/.volume` (confirmed by inspection:
    `closes`/`highs`/`lows`/`volumes` below, `_visible_indices`/the chart payload in `api/stocks.py`, the
    VCP/pattern detectors via those extractors) — so NO consumer code changes. It carries no `.id`/
    `.symbol`: the cache already partitions bars by symbol (the dict key), and no consumer reads either
    off a bar object. NOT a table/model — a plain in-memory column-projected record, built by streaming a
    column-projected SELECT instead of materializing full `DailyPrice` ORM rows (~8 attributes + ORM
    instrumentation each) for the whole 3.27M-row table at once."""

    date: date_cls
    open: float
    high: float
    low: float
    close: float
    volume: float


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
        self._by_symbol: dict[str, list[Bar]] = {}
        self._dates_by_symbol: dict[str, list[date_cls]] = {}
        self._load_lock = threading.Lock()
        # iter-19: whether the ONE expensive whole-table scan has already run on this cache instance. A
        # nested `prefilled_bar_cache` call on the SAME already-prefilled session (the exact shape
        # `_compute_coverage_uncached`'s own context + `_membership_timeline`'s NESTED context produce)
        # must not re-pay the whole-table scan — see `prefill` below.
        self._prefilled = False

    def prefill(self, session: Session, expected_symbols: Optional[Iterable[str]] = None) -> None:
        """Load EVERY symbol's full date-ordered series ONCE, in ONE STREAMED query, on `session` (the
        orchestrating thread, before any worker fan-out). After this, a shared read across worker
        threads needs no further bar-store load — so a K-date parallel backfill loads each symbol once
        for the whole job (J-46), not once per worker session. Same rows/order as the lazy path: ordered
        by (symbol, date); the (symbol, date) unique constraint guarantees no ties.

        iter-19 (the OOM fix): the query is now COLUMN-PROJECTED (`symbol, date, open, high, low, close,
        volume` — not a whole `DailyPrice` ORM row) and consumed via `yield_per(batch)` (the
        `_streamed_existing_keys` idiom in `forward_testing.py`) instead of `.all()`, which previously
        materialized all 3.27M rows as hydrated ORM instances at once (~6.8 GB peak against the 6144 MB
        cap). Each row builds a lightweight `Bar` record — same values, far less memory/object overhead.
        `ORDER BY symbol, date` and the served contents are UNCHANGED (a pure loading-mechanism refactor;
        see `test_bar_cache.py`'s byte-identical snapshot tests).

        iter-19 (the nested-call cost): this whole-table scan now runs AT MOST ONCE per cache instance —
        guarded by `self._prefilled`. Before this, a SECOND `prefill` call on an already-loaded cache (the
        `if symbol not in self._by_symbol` guard only skipped OVERWRITING already-loaded series; the
        expensive query itself re-ran unconditionally every call) re-paid the full scan for no new data.
        That nested shape is not hypothetical: `_compute_coverage_uncached` opens its own
        `prefilled_bar_cache`, and `_membership_timeline` (called from inside it, via
        `membership_timeline_cached` on a cache miss) opens ANOTHER `prefilled_bar_cache` on the SAME
        session — `bar_cache`'s re-entrancy meant the cache instance was reused, but `prefill` still
        re-scanned. Invisible at ~122 symbols / 5 years; a doubled OOM at 583 symbols / 30 years. Skipping
        the re-scan changes NOTHING about the final `_by_symbol`/`_dates_by_symbol` contents (the discarded
        second scan's rows were always thrown away for already-loaded symbols) — a pure performance fix.

        iter-37 (load-once restored): the one prefill query only returns symbols that HAVE bars in
        `daily_prices`; a candidate-pool symbol with ZERO bars is therefore absent from the cache, so the
        resolver's per-date `trailing_count` would fall into the lazy per-symbol load — re-issued once per
        snapshot date / per worker session, breaking the J-46 load-once-per-job invariant. `expected_symbols`
        (the candidate pool the resolver will ask about) closes that hole: every expected name NOT already
        loaded is recorded with an EMPTY series up front, so a no-bar symbol resolves to a trailing count of
        0 from the once-loaded cache with NO per-date re-load. The served value is byte-identical — an empty
        series has 0 trailing bars, exactly the grouped-count path's result (`below_history`). Recording an
        absent symbol as `[]` is descriptive, not fabricated: it means "this name has no bars at/through D".
        This cheap bookkeeping still runs on EVERY call (even when the whole-table scan is skipped), so a
        later call passing a WIDER `expected_symbols` set still records any newly-named no-bar candidate."""
        with self._load_lock:
            need_scan = not self._prefilled
        if need_scan:
            batch = get_config().research.read_batch_size
            stmt = (
                select(
                    DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
                    DailyPrice.low, DailyPrice.close, DailyPrice.volume,
                )
                .order_by(DailyPrice.symbol, DailyPrice.date)
            )
            by_symbol: dict[str, list[Bar]] = {}
            for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
                by_symbol.setdefault(symbol, []).append(Bar(d, o, h, lo, c, v))
            # publish atomically under the lock so a concurrent reader sees a fully-built map, not a
            # partial one; re-check `_prefilled` in case another thread raced us to the scan (rare —
            # `_BarCache` is normally driven by one orchestrating thread — but the merge below is
            # idempotent either way, so a lost race just discards redundant work, never corrupts state).
            with self._load_lock:
                if not self._prefilled:
                    for symbol, full in by_symbol.items():
                        if symbol not in self._by_symbol:  # never overwrite a series already loaded
                            self._by_symbol[symbol] = full
                            self._dates_by_symbol[symbol] = [bar.date for bar in full]
                    self._prefilled = True
        # record an EMPTY series for every expected (candidate-pool) symbol with no bars, so it is never
        # lazy-loaded per-date later — load-once-per-job holds for no-bar names too. Cheap (no query), so
        # it always runs, even when the whole-table scan above was skipped as already-done.
        if expected_symbols is not None:
            with self._load_lock:
                for symbol in expected_symbols:
                    if symbol not in self._by_symbol:
                        self._by_symbol[symbol] = []
                        self._dates_by_symbol[symbol] = []

    def bars_asof(self, session: Session, symbol: str, d: date_cls) -> list[Bar]:
        full = self._by_symbol.get(symbol)
        if full is None:
            # lazy load (defensive — a pre-filled cache rarely reaches here): guard the mutation so a
            # shared cache loads a missing symbol exactly once even under concurrent worker access.
            with self._load_lock:
                full = self._by_symbol.get(symbol)
                if full is None:
                    # one ordered, COLUMN-PROJECTED query for the symbol's WHOLE series (iter-19: a `Bar`
                    # record, not a hydrated `DailyPrice` ORM row) — the SAME ordering today's bars_asof
                    # uses (order by date; the unique constraint guarantees no ties). Already per-symbol
                    # bounded (a single name's history, not the whole table), so `.all()` stays exactly as
                    # bounded as before — only the record type changes.
                    stmt = (
                        select(
                            DailyPrice.date, DailyPrice.open, DailyPrice.high,
                            DailyPrice.low, DailyPrice.close, DailyPrice.volume,
                        )
                        .where(DailyPrice.symbol == symbol)
                        .order_by(DailyPrice.date)
                    )
                    full = [Bar(*row) for row in session.exec(stmt).all()]
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
        round-trips (it reads the once-loaded series instead). A symbol not yet recorded is loaded exactly
        ONCE — and a no-bar symbol is MEMOIZED as an empty series under the lock — so it is never re-loaded
        on later dates / other worker sessions reading the shared cache (the J-46 load-once-per-job
        invariant holds even for a candidate-pool name that has zero bars and was not pre-recorded)."""
        dates = self._dates_by_symbol.get(symbol)
        if dates is None:
            # ensure the series is loaded (re-uses bars_asof's lazy-load + lock); we discard the slice.
            # `bars_asof` records the result (an empty list for a no-bar symbol) under the load lock, so a
            # later `trailing_count`/`bars_asof` for this symbol finds it pre-loaded and never re-queries.
            self.bars_asof(session, symbol, d)
            dates = self._dates_by_symbol.get(symbol)
            if dates is None:
                return 0  # defensive: still unrecorded — zero trailing bars
        return bisect.bisect_right(dates, d)


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
def prefilled_bar_cache(
    session: Session, expected_symbols: Optional[Iterable[str]] = None
) -> Iterator[_BarCache]:
    """Like `bar_cache`, but PRE-FILLS every symbol's full series up front in ONE query (J-53). Returns
    the cache so it can be SHARED with worker sessions via `attach_shared_cache` — so a parallel
    multi-date backfill loads each symbol ONCE for the whole job (the J-46 load-once-per-job guarantee),
    not once per worker session. The orchestrating thread owns this context; workers only READ the
    pre-loaded immutable series.

    `expected_symbols` (iter-37): the candidate-pool symbols the resolver will ask `trailing_count` about.
    Any expected name WITHOUT bars is recorded as an empty series in the single prefill, so a no-bar
    candidate resolves to a trailing count of 0 from the once-loaded cache with NO per-date lazy re-load —
    restoring load-once-per-job for no-bar names too, byte-identically (empty series ⇒ 0 trailing bars)."""
    with bar_cache(session) as cache:
        cache.prefill(session, expected_symbols=expected_symbols)
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


def bars_asof(session: Session, symbol: str, d: date_cls) -> list[DailyPrice] | list[Bar]:
    """All bars for `symbol` with date <= `d`, ascending. The backward no-lookahead boundary.

    When a `bar_cache(session)` context is active (J-46), this slices the symbol's once-loaded full
    series in memory (iter-19: lightweight `Bar` records); otherwise it runs the original per-request
    date-bounded query against `DailyPrice` (the default path, byte-identical to before). Either way it
    returns exactly the bars with date <= d, ascending, exposing the same `.date/.open/.high/.low/.close/
    .volume` attributes — every consumer reads bars structurally and never depends on the concrete type."""
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
# `bars` may be `DailyPrice` rows (the default, uncached path) or `Bar` records (iter-19: the cache
# path) — both expose the same `.close/.high/.low/.volume` attributes, so these read structurally.
def closes(bars: list[DailyPrice] | list[Bar]) -> list[float]:
    return [b.close for b in bars]


def highs(bars: list[DailyPrice] | list[Bar]) -> list[float]:
    return [b.high for b in bars]


def lows(bars: list[DailyPrice] | list[Bar]) -> list[float]:
    return [b.low for b in bars]


def volumes(bars: list[DailyPrice] | list[Bar]) -> list[float]:
    return [b.volume for b in bars]
