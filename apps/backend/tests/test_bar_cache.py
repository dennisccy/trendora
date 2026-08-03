"""J-46 — the load-once bar cache (Capability 33): an OPT-IN, per-session optimization at the single
`prices.bars_asof` seam. The named proofs, each guarding a DoD / anti-goal item:

  - load-count        — a K-date (K >= 3) backfill loads each symbol's bar series AT MOST ONCE for the
                        whole job (vs >= K today), instrumented at the bar-store load point.
  - cached == uncached — the canonical `score_stocks(D)` output is BYTE-IDENTICAL through the cache and
                        through the default per-request path (the pure-refactor proof: same scores /
                        buckets / setups / VCP — anti-goal: Single source of truth).
  - no-lookahead slice — the cached `bars_asof(symbol, D)` returns EXACTLY the bars with date <= D, in
                        the same order as the uncached query — the cache slices `<= D` like `bars_asof`
                        does today (anti-goal: No lookahead — no future bar leaks through the cache).
  - default path / lifetime — with NO active context the read path is unchanged, and the cache dies when
                        its `with` block exits (it never outlives the job / serves a stale series).

These run on a SINGLE module-scoped seed load (the real engines), so the equality is over real data.
"""
from __future__ import annotations

import math
from datetime import date

import pytest
from sqlmodel import Session, select

from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine import prices
from app.engine.data_manager import _trading_days, create_job, run_data_job
from app.engine.prices import _BAR_CACHES, bar_cache, bars_asof
from app.engine.scoring import score_stocks
from app.models import DailyPrice, ScannerRun


# ==================================================================================================
# Tiny hand-built DB — the cache mechanics (slice correctness, default path, lifetime)
# ==================================================================================================
@pytest.fixture()
def tiny_engine(tmp_path):
    """One symbol with five consecutive bars + an SPY calendar — enough to prove the `<= D` slice."""
    engine = make_engine(f"sqlite:///{tmp_path / 'bc.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]
    with Session(engine) as session:
        for d in days:
            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
        for i, d in enumerate(days):
            session.add(
                DailyPrice(symbol="AAA", date=d, open=10.0 + i, high=11.0 + i, low=9.0 + i,
                           close=10.5 + i, volume=100.0 + i)
            )
        session.commit()
    return engine, days


def test_cached_bars_asof_slices_le_d_identically(tiny_engine):
    """Inside a `bar_cache` context, `bars_asof(symbol, D)` returns EXACTLY the bars with date <= D, in
    the same order and with the same values as the uncached per-request query — for every D (no future
    bar leaks; the slice boundary is the same `<= D` the default path uses)."""
    engine, days = tiny_engine
    with Session(engine) as plain:
        uncached = {d: [(b.date, b.close) for b in bars_asof(plain, "AAA", d)] for d in days}
    with Session(engine) as cached_session:
        with bar_cache(cached_session):
            cached = {d: [(b.date, b.close) for b in bars_asof(cached_session, "AAA", d)] for d in days}
    assert cached == uncached
    # exact contents: D == day index i ⇒ exactly i+1 bars, all with date <= D, ascending
    for i, d in enumerate(days):
        rows = cached[d]
        assert [r[0] for r in rows] == days[: i + 1]  # exactly the <= D dates, ascending
        assert all(bar_date <= d for bar_date, _ in rows)  # no future bar


def test_prefill_returns_bar_records_matching_plain_query_row_level(tiny_engine):
    """iter-19 (the OOM fix): `_BarCache.prefill()` now streams a COLUMN-PROJECTED query into lightweight
    `Bar` records instead of materializing whole `DailyPrice` ORM rows. Proves the rewrite changes HOW
    bars are loaded, never WHAT is loaded: the prefilled cache's rows/order/values for EVERY symbol match
    a plain reference `SELECT * FROM daily_prices ORDER BY symbol, date` exactly, and each cached bar is a
    `Bar` (not a `DailyPrice`) carrying the identical date/open/high/low/close/volume values."""
    engine, days = tiny_engine
    with Session(engine) as reference_session:
        reference = [
            (bar.symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in reference_session.exec(
                select(DailyPrice).order_by(DailyPrice.symbol, DailyPrice.date)
            ).all()
        ]
    with Session(engine) as session:
        cache = prices._BarCache()
        cache.prefill(session)
        # the prefilled record type is the lightweight `Bar`, never a hydrated `DailyPrice` ORM instance.
        assert all(isinstance(bar, prices.Bar) for bars in cache._by_symbol.values() for bar in bars)
        prefilled = [
            (symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for symbol in sorted(cache._by_symbol)
            for bar in cache._by_symbol[symbol]
        ]
    assert prefilled == reference


def _old_prefill_by_symbol(session) -> dict:
    """ops-hardening iter-41 (B5, TC-6) -- a faithful reimplementation of the PRE-iter-41
    `_BarCache.prefill` accumulation body (the exact code this iteration's B5 fix replaced): one `Bar`
    NamedTuple per row, appended into a plain `list[Bar]` per symbol. Kept here ONLY as a benchmark/
    test reference -- never imported by the shipped app (mirrors
    `runs/goal-ops-hardening-iter-41/bar-cache-prefill-bench/measure_prefill_peak.py`'s own `_old_
    prefill_peak`, the live-DB peak-memory measurement's OLD arm)."""
    from app.config import get_config

    batch = get_config().research.read_batch_size
    stmt = (
        select(
            DailyPrice.symbol, DailyPrice.date, DailyPrice.open, DailyPrice.high,
            DailyPrice.low, DailyPrice.close, DailyPrice.volume,
        )
        .order_by(DailyPrice.symbol, DailyPrice.date)
    )
    by_symbol: dict = {}
    for symbol, d, o, h, lo, c, v in session.exec(stmt).yield_per(batch):
        by_symbol.setdefault(symbol, []).append(prices.Bar(d, o, h, lo, c, v))
    return by_symbol


def test_prefill_old_vs_new_implementation_byte_identical(tiny_engine):
    """TC-6 -- the OLD (pre-iter-41, `list[Bar]`) and NEW (iter-41 B5, columnar `_SymbolColumns`)
    `_BarCache.prefill` implementations, run through the SAME fixture inputs, return byte-identical
    `Bar` values for every symbol/date -- the fixture-backed old-vs-new equality proof the B5 memory
    bound requires (byte-identical output, only the resident storage shape changed)."""
    engine, days = tiny_engine
    with Session(engine) as old_session:
        old_by_symbol = _old_prefill_by_symbol(old_session)
    with Session(engine) as new_session:
        cache = prices._BarCache()
        cache.prefill(new_session)
        new_by_symbol = cache._by_symbol

    assert set(old_by_symbol) == set(new_by_symbol) == {"SPY", "AAA"}
    for symbol in old_by_symbol:
        old_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in old_by_symbol[symbol]]
        new_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in new_by_symbol[symbol]]
        assert new_bars == old_bars, f"symbol {symbol}: NEW prefill output diverges from OLD"
        # every synthesized element is still a REAL `Bar` NamedTuple (supports `.date`/`._replace()`/
        # structural equality with the OLD implementation's own Bar instances) -- not merely
        # value-equal tuples of a different type.
        assert all(isinstance(b, prices.Bar) for b in new_by_symbol[symbol])
        assert list(new_by_symbol[symbol]) == list(old_by_symbol[symbol])


def test_prefill_expected_symbols_no_longer_filters_the_eager_scan(tiny_engine):
    """iter-43 (REVERT): `prefill(expected_symbols=...)` no longer filters its SELECT — TC-1's
    byte-identity oracle against the pre-iter-42 (unfiltered) reference body. Proves the revert is
    GENUINELY engaged (the iter-37 lesson, applied in reverse this time: assert the REMOVED condition
    is truly gone, not merely absent from the diff): SPY has real bars in this fixture and is NOT named
    in `expected_symbols=["AAA"]`, yet it must be FULLY PRESENT in the cache immediately after
    `prefill` returns — the eager scan loads the whole table regardless of `expected_symbols`, exactly
    like the `expected_symbols=None` case. A subsequent `bars_asof(session, "SPY", ...)` read issues
    ZERO additional queries (SPY was never lazily loaded — it was already eagerly scanned), unlike the
    iter-42 shape this test replaces (which required exactly one lazy-load query for SPY)."""
    engine, days = tiny_engine
    with Session(engine) as reference_session:
        reference_spy = [
            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in reference_session.exec(
                select(DailyPrice).where(DailyPrice.symbol == "SPY").order_by(DailyPrice.date)
            ).all()
        ]
        reference_aaa = [
            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in reference_session.exec(
                select(DailyPrice).where(DailyPrice.symbol == "AAA").order_by(DailyPrice.date)
            ).all()
        ]
    with Session(engine) as session:
        cache = prices._BarCache()
        cache.prefill(session, expected_symbols=["AAA"])
        # LIVE proof the filter is genuinely gone: SPY was excluded from expected_symbols but must be
        # present anyway — the eager scan is unconditional again, byte-identical to expected_symbols=None.
        assert set(cache._by_symbol) == {"AAA", "SPY"}, (
            f"SPY must be present after the revert (no filtering), got {set(cache._by_symbol)}"
        )
        aaa_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in cache._by_symbol["AAA"]]
        spy_bars = [(b.date, b.open, b.high, b.low, b.close, b.volume) for b in cache._by_symbol["SPY"]]
        assert aaa_bars == reference_aaa
        assert spy_bars == reference_spy
        assert all(isinstance(b, prices.Bar) for b in cache._by_symbol["AAA"])
        assert all(isinstance(b, prices.Bar) for b in cache._by_symbol["SPY"])

        # SPY was never in expected_symbols, but it was already eagerly loaded -> reading it now issues
        # ZERO additional queries (no lazy per-symbol fallback needed, unlike the pre-revert shape).
        calls = {"n": 0}
        orig_exec = session.exec

        def _counting_exec(stmt, *a, **kw):
            calls["n"] += 1
            return orig_exec(stmt, *a, **kw)

        session.exec = _counting_exec  # type: ignore[assignment]
        spy_via_cache = [
            (b.date, b.open, b.high, b.low, b.close, b.volume)
            for b in cache.bars_asof(session, "SPY", days[-1])
        ]
        assert calls["n"] == 0, (
            f"SPY was already eagerly loaded by the unconditional scan — a read must issue no query, "
            f"got {calls['n']}"
        )
        assert spy_via_cache == reference_spy


def test_prefill_empty_expected_symbols_still_loads_full_table(tiny_engine):
    """iter-43 (REVERT): `expected_symbols=[]` (a genuinely empty, but non-None, candidate set) no
    longer short-circuits to zero eagerly-loaded rows -- that iter-42 guard is removed along with the
    filter it protected. Post-revert, `[]` behaves EXACTLY like `expected_symbols=None`: the
    unconditional whole-table scan still runs and loads every symbol (byte-identical to the reference
    query), and the empty `expected_symbols` list only affects the SEPARATE "record a zero-bar
    candidate" bookkeeping loop at the end of `prefill` (a no-op here, since the list is empty) --
    never the SELECT itself."""
    engine, days = tiny_engine
    with Session(engine) as reference_session:
        reference = [
            (bar.symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in reference_session.exec(
                select(DailyPrice).order_by(DailyPrice.symbol, DailyPrice.date)
            ).all()
        ]
    with Session(engine) as session:
        cache = prices._BarCache()
        cache.prefill(session, expected_symbols=[])
        assert set(cache._by_symbol) == {"AAA", "SPY"}, (
            f"the full table must load even with an empty expected_symbols list, got {set(cache._by_symbol)}"
        )
        loaded = [
            (symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for symbol in sorted(cache._by_symbol)
            for bar in cache._by_symbol[symbol]
        ]
        assert loaded == reference
        assert cache._prefilled is True  # the (now-unconditional) scan still ran/completed once


def test_prefill_null_numeric_column_degrades_without_crashing(tiny_engine):
    """B6 (AG-8): a NULL numeric column in a `daily_prices` row -- a data-shape widening not
    reachable against the current schema's NOT NULL columns, but one AG-8 requires surviving --
    must not crash `_BarCache.prefill` with `array.array('d').append(None)`'s `TypeError`. Simulates
    the NULL by tampering with ONE row's `close` value as it streams out of the REAL query (the exact
    boundary this fix hardens) instead of fighting the DB's own NOT NULL constraint, which would
    reject the insert before `prefill` ever runs."""
    engine, days = tiny_engine

    class _NullInjectingResult:
        """Proxies every attribute to the real SQLAlchemy result except `yield_per`, whose stream it
        taps to null out exactly one row's `close` value -- an honest simulation of a NULL numeric
        column arriving from the DB, without needing to defeat the model's NOT NULL constraint."""

        def __init__(self, real):
            self._real = real

        def yield_per(self, n):
            tampered = False
            for row in self._real.yield_per(n):
                row = list(row)
                # prefill's own column-projected query yields 7-tuples (symbol, date, open, high,
                # low, close, volume); a per-symbol lazy load yields 6 (no symbol) -- so this only
                # ever tampers with prefill's accumulation loop, never the lazy fallback.
                if not tampered and len(row) == 7 and row[0] == "AAA" and row[1] == days[0]:
                    row[5] = None  # close
                    tampered = True
                yield tuple(row)

        def __getattr__(self, name):
            return getattr(self._real, name)

    with Session(engine) as session:
        orig_exec = session.exec

        def _exec_with_one_null_close(stmt, *a, **kw):
            return _NullInjectingResult(orig_exec(stmt, *a, **kw))

        session.exec = _exec_with_one_null_close  # type: ignore[assignment]
        cache = prices._BarCache()
        cache.prefill(session)  # must NOT raise TypeError

    bars = list(cache._by_symbol["AAA"])
    assert math.isnan(bars[0].close), f"a NULL close should degrade to the NA sentinel, got {bars[0].close!r}"
    # every OTHER field on that same row is unaffected.
    assert bars[0].date == days[0] and bars[0].open == 10.0 and bars[0].high == 11.0 and bars[0].low == 9.0
    # every other row/symbol is unaffected.
    assert not math.isnan(bars[1].close)
    assert all(not math.isnan(b.close) for b in cache._by_symbol["SPY"])


@pytest.mark.parametrize("accessor", ["bars_asof", "bars_asof_window"])
def test_lazy_load_is_published_atomically_to_a_concurrent_reader(tiny_engine, accessor):
    """iter-42 audit (B1): the lazy per-symbol load publishes into TWO dicts in sequence —
    `self._by_symbol[symbol] = full` and THEN `self._dates_by_symbol[symbol] = [...]` (a list
    comprehension over the whole series, thousands of elements at the live basis, so the GIL is
    released between them). `bars_asof`/`bars_asof_window` take their FAST path — no lock — as soon
    as `self._by_symbol.get(symbol)` is non-None, and then index `self._dates_by_symbol[symbol]`. A
    second thread that reads in that window therefore sees a half-published symbol and raises
    `KeyError`.

    Before iter-42 this was unreachable in production: `prefill` eagerly loaded EVERY symbol in
    `daily_prices` on the single orchestrating thread before any worker fan-out, so no worker ever
    entered the lazy branch. iter-42's `WHERE symbol IN (expected_symbols)` filter deliberately
    leaves the 43 non-pool symbols (SPY, QQQ, ^VIX, the XL* sector SPDRs, the theme ETFs) OUT of
    that eager scan, and those are read per snapshot date by `regime.py`/`market_phase.py`/
    `sectors.py`/`themes.py` — from the parallel backfill's worker threads. The dev handoff's own
    root-cause note for its test-instrumentation fix records the same new concurrency ("two threads
    can both observe 'not yet loaded'"; `max(load_counts.values()) == 3` observed), i.e. concurrent
    first-access of these symbols genuinely happens in a real job.

    This test forces the interleaving deterministically: the writer is held between its two
    publishes while a second thread (its OWN session — sessions are never shared) reads the same
    symbol, and asserts the reader gets the correct series instead of an exception."""
    import threading
    import time

    engine, days = tiny_engine
    with Session(engine) as reference_session:
        reference = [
            (bar.date, bar.close)
            for bar in reference_session.exec(
                select(DailyPrice).where(DailyPrice.symbol == "SPY").order_by(DailyPrice.date)
            ).all()
        ]

    cache = prices._BarCache()
    published = threading.Event()

    class _HeldPublish(dict):
        """Holds the writer between `_by_symbol[symbol] = ...` and the `_dates_by_symbol` publish
        that follows it — the exact window a real worker thread can land in."""

        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            if key == "SPY":
                published.set()
                time.sleep(0.5)

    cache._by_symbol = _HeldPublish()

    reader_error: "list[BaseException]" = []
    reader_result: "list[list]" = []

    def _reader():
        published.wait(5)
        try:
            with Session(engine) as reader_session:
                if accessor == "bars_asof":
                    bars = cache.bars_asof(reader_session, "SPY", days[-1])
                else:
                    bars = cache.bars_asof_window(reader_session, "SPY", days[-1], len(days))
                reader_result.append([(b.date, b.close) for b in bars])
        except BaseException as exc:  # noqa: BLE001 — the point of the test is to surface it
            reader_error.append(exc)

    thread = threading.Thread(target=_reader, name="concurrent-reader")
    thread.start()
    with Session(engine) as writer_session:
        cache.bars_asof(writer_session, "SPY", days[-1])
    thread.join(15)

    assert not reader_error, (
        f"a concurrent reader saw a half-published lazy load: {reader_error[0]!r}"
    )
    assert reader_result == [reference], reader_result


def test_lazy_load_returns_bar_records_matching_plain_query_row_level(tiny_engine):
    """The lazy per-symbol fallback inside `bars_asof` (already per-symbol-bounded — iter-19 only changes
    its record type, never its bounding) also returns `Bar` records whose values match a plain reference
    query for that symbol exactly."""
    engine, days = tiny_engine
    with Session(engine) as reference_session:
        reference = [
            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in reference_session.exec(
                select(DailyPrice).where(DailyPrice.symbol == "AAA").order_by(DailyPrice.date)
            ).all()
        ]
    with Session(engine) as session:
        cache = prices._BarCache()
        # no prefill — this exercises ONLY the lazy per-symbol branch inside bars_asof.
        loaded = cache.bars_asof(session, "AAA", days[-1])
    assert all(isinstance(bar, prices.Bar) for bar in loaded)
    assert [(bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume) for bar in loaded] == reference


def test_prefill_skips_requery_when_already_prefilled(tiny_engine):
    """iter-19: a SECOND `prefill()` call on an already-fully-loaded cache — the exact nested-call shape
    `_compute_coverage_uncached`'s own `prefilled_bar_cache` context plus `_membership_timeline`'s NESTED
    `prefilled_bar_cache` call (on a `membership_timeline_cached` cache miss) produce on the SAME session —
    must NOT re-run the expensive whole-table scan. Before this fix, `prefill()` re-queried unconditionally
    on every call (the `if symbol not in self._by_symbol` guard only skipped OVERWRITING already-loaded
    series, not the query itself), doubling the OOM'ing cost within a single request — invisible at ~122
    symbols/5 years, catastrophic at 583 symbols/30 years. Proven by counting `session.exec` calls: a
    second prefill with nothing new to load issues ZERO additional queries."""
    engine, days = tiny_engine
    with Session(engine) as session:
        cache = prices._BarCache()
        calls = {"n": 0}
        orig_exec = session.exec

        def _counting_exec(stmt, *a, **kw):
            calls["n"] += 1
            return orig_exec(stmt, *a, **kw)

        session.exec = _counting_exec  # type: ignore[assignment]
        cache.prefill(session)
        after_first = calls["n"]
        assert after_first > 0, "the first prefill should issue at least one query"

        # a second call — the nested-call shape (same session, an expected_symbols set that is a SUBSET
        # of what's already loaded) — must not re-scan the whole table.
        cache.prefill(session, expected_symbols=["AAA"])
        assert calls["n"] == after_first, (
            f"a second prefill on an already-loaded cache re-queried ({calls['n']} vs {after_first} calls)"
        )

        # a THIRD call adding a genuinely NEW (no-bar) expected symbol still records it — WITHOUT a query
        # (the cheap expected_symbols bookkeeping needs no DB round-trip).
        cache.prefill(session, expected_symbols=["AAA", "ZZZ_NO_BARS"])
        assert calls["n"] == after_first, "recording a new no-bar expected symbol must not issue a query"
        assert cache._by_symbol["ZZZ_NO_BARS"] == []


def test_prefill_expected_symbols_records_zero_bar_symbol_once(tiny_engine):
    """iter-37 regression guard (the root cause of the load-once break): a CANDIDATE-POOL symbol that has
    ZERO rows in `daily_prices` must be sourced from the prefilled cache as a count of 0 with AT MOST ONE
    bar-store load — never a fresh lazy per-date re-load. `prefill(expected_symbols=...)` records an empty
    series up front for every expected name (incl. the no-bar ones), so the resolver's per-date
    `trailing_count` reads 0 from the once-loaded cache instead of re-issuing a per-symbol query each date
    (the iter-36 defect that re-loaded a no-bar candidate every snapshot date of a parallel K-date job)."""
    engine, days = tiny_engine
    # instrument EVERY full-series bar-store load (the same instrument the K-date job test uses): a real
    # per-symbol DB query is exactly a `bars_asof`/`prefill` entry appearing in `_by_symbol`.
    load_counts: dict[str, int] = {}
    orig_bars_asof = prices._BarCache.bars_asof
    orig_prefill = prices._BarCache.prefill

    def _counting_bars_asof(self, session, symbol, d):
        if symbol not in self._by_symbol:
            load_counts[symbol] = load_counts.get(symbol, 0) + 1
        return orig_bars_asof(self, session, symbol, d)

    def _counting_prefill(self, session, expected_symbols=None):
        before = set(self._by_symbol)
        orig_prefill(self, session, expected_symbols=expected_symbols)
        for symbol in self._by_symbol:
            if symbol not in before:
                load_counts[symbol] = load_counts.get(symbol, 0) + 1

    prices._BarCache.bars_asof = _counting_bars_asof  # type: ignore[assignment]
    prices._BarCache.prefill = _counting_prefill  # type: ignore[assignment]
    try:
        with Session(engine) as session:
            with prices.prefilled_bar_cache(session, expected_symbols=["AAA", "ZZZ"]) as cache:
                # ZZZ has no bars at all — it is a candidate-pool name with zero daily_prices rows.
                for d in days:  # five per-date resolver reads of the SAME no-bar symbol
                    assert cache.trailing_count(session, "ZZZ", d) == 0  # honest descriptive count: 0
                # AAA (five bars) still slices correctly from the once-loaded series.
                assert cache.trailing_count(session, "AAA", days[-1]) == len(days)
    finally:
        prices._BarCache.bars_asof = orig_bars_asof  # type: ignore[assignment]
        prices._BarCache.prefill = orig_prefill  # type: ignore[assignment]

    # the invariant: the no-bar candidate symbol is loaded AT MOST ONCE for the whole context (it was
    # recorded as an empty series by `prefill`, so no per-date lazy re-load ever fires).
    assert load_counts.get("ZZZ", 0) == 1
    assert load_counts.get("AAA", 0) == 1
    assert max(load_counts.values()) == 1


def test_cache_loads_each_symbol_once_within_context(tiny_engine):
    """The FIRST `bars_asof` for a symbol loads its full series once; every later call slices in memory
    (zero extra bar-store loads). Instrumented at the bar-store load point (the per-symbol DailyPrice
    SELECT)."""
    engine, days = tiny_engine
    with Session(engine) as session:
        loads = _SymbolLoadCounter(session)
        with bar_cache(session):
            for d in days:  # five as-of reads of the SAME symbol
                bars_asof(session, "AAA", d)
        assert loads.count_for("AAA") == 1  # exactly ONE bar-store load for five reads


def test_default_path_unchanged_without_context(tiny_engine):
    """With NO active `bar_cache` context the read path is the original per-request query — and the
    module cache registry stays empty (the optimization is strictly opt-in)."""
    engine, days = tiny_engine
    with Session(engine) as session:
        assert _BAR_CACHES == {}  # no context active
        out = [(b.date, b.close) for b in bars_asof(session, "AAA", days[2])]
        assert _BAR_CACHES == {}  # still empty — the default path registered nothing
        assert [r[0] for r in out] == days[:3]


def test_cache_does_not_outlive_its_context(tiny_engine):
    """The cache is removed from the registry on `with` exit — it never outlives the job (so a later
    data-mutating stage / a new job never serves a stale cached series)."""
    engine, _ = tiny_engine
    with Session(engine) as session:
        with bar_cache(session):
            bars_asof(session, "AAA", date(2024, 1, 5))
            assert id(session) in _BAR_CACHES  # active inside the block
        assert id(session) not in _BAR_CACHES  # dropped on exit
    assert _BAR_CACHES == {}


def test_cache_sees_new_bars_in_a_fresh_context(tiny_engine):
    """A cache instance is per-context: bars added BETWEEN two contexts on the same session are visible
    in the second context (the cache dies with its block, so it never serves a stale series across a
    data-mutating stage — the exact reason a fetch stage runs OUTSIDE the backfill's cache)."""
    engine, days = tiny_engine
    new_day = date(2024, 1, 9)
    with Session(engine) as session:
        with bar_cache(session):
            assert len(bars_asof(session, "AAA", new_day)) == len(days)  # five bars cached
        # add a sixth bar OUTSIDE any cache context (a data-mutating stage)
        session.add(DailyPrice(symbol="AAA", date=new_day, open=20.0, high=21.0, low=19.0, close=20.5, volume=200.0))
        session.commit()
        with bar_cache(session):  # a FRESH context → reloads → sees the new bar (no staleness)
            assert len(bars_asof(session, "AAA", new_day)) == len(days) + 1


# ==================================================================================================
# ops-hardening iter-36 (J-07/J-96 AG-8 memory bound) — `_BarCache.load_only()`, the batched-REPLACE
# sibling of `prefill()` used by `_membership_timeline`'s memory-bounded loop (data_manager.py) when no
# outer job-scoped cache is already active.
# ==================================================================================================
def test_load_only_loads_exactly_the_given_symbols_byte_identical_to_lazy_path(tiny_engine):
    """`load_only(symbols)` loads ONLY the requested symbols, with values byte-identical to the default
    (uncached) per-symbol query — same rows, same order, same values."""
    engine, days = tiny_engine
    with Session(engine) as reference_session:
        reference = [
            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in reference_session.exec(
                select(DailyPrice).where(DailyPrice.symbol == "AAA").order_by(DailyPrice.date)
            ).all()
        ]
    with Session(engine) as session:
        cache = prices._BarCache()
        cache.load_only(session, ["AAA"])
        assert set(cache._by_symbol) == {"AAA"}  # ONLY the requested symbol loaded — never SPY too
        loaded = [
            (bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
            for bar in cache._by_symbol["AAA"]
        ]
    assert loaded == reference
    assert all(isinstance(bar, prices.Bar) for bar in cache._by_symbol["AAA"])


def test_load_only_records_zero_bar_symbol_as_empty_series(tiny_engine):
    """A symbol with no `daily_prices` rows at all is recorded as an EMPTY series (mirrors `prefill`'s
    `expected_symbols` bookkeeping) — `trailing_count` reads 0 with no crash and no further query."""
    engine, days = tiny_engine
    with Session(engine) as session:
        cache = prices._BarCache()
        cache.load_only(session, ["AAA", "ZZZ_NO_BARS"])
        assert cache._by_symbol["ZZZ_NO_BARS"] == []
        assert cache._dates_by_symbol["ZZZ_NO_BARS"] == []
        assert cache.trailing_count(session, "ZZZ_NO_BARS", days[-1]) == 0
        assert cache.trailing_count(session, "AAA", days[-1]) == len(days)


def test_load_only_replaces_prior_contents_never_accumulates_across_batches(tiny_engine):
    """A SECOND `load_only` call on the SAME instance (a later batch of a symbol-batched loop) DROPS the
    first batch's symbol entirely — the mechanism `_membership_timeline` relies on to bound peak resident
    bar data to one batch at a time, reusing ONE `_BarCache` instance rather than allocating a second."""
    engine, days = tiny_engine
    with Session(engine) as session:
        cache = prices._BarCache()
        cache.load_only(session, ["AAA"])
        assert set(cache._by_symbol) == {"AAA"}
        cache.load_only(session, ["SPY"])
        assert set(cache._by_symbol) == {"SPY"}, "the prior batch (AAA) must be dropped, not accumulated"
        assert len(cache._by_symbol["SPY"]) == len(days)


def test_load_only_does_not_touch_prefilled_flag_or_interact_with_prefill(tiny_engine):
    """`load_only` is independent of `prefill`'s whole-table-scan guard: it never sets `_prefilled`, and a
    cache driven by `load_only` never triggers (or is triggered by) `prefill`'s re-entrancy mechanics —
    the two loading mechanisms coexist without interaction."""
    engine, days = tiny_engine
    with Session(engine) as session:
        cache = prices._BarCache()
        assert cache._prefilled is False
        cache.load_only(session, ["AAA"])
        assert cache._prefilled is False, "load_only must never mark the whole-table scan as done"


# --- a small instrument: count per-symbol bar-store loads (the per-symbol DailyPrice SELECT) ----------
class _SymbolLoadCounter:
    """Wraps `session.exec` and tallies the bar-store loads per symbol (a SELECT over `daily_prices`
    filtered by a single symbol) — the faithful 'count at the bar-store load point' instrument."""

    def __init__(self, session: Session):
        self.counts: dict[str, int] = {}
        self._orig = session.exec

        def _counting_exec(stmt, *args, **kwargs):
            text = str(stmt)
            if "daily_prices" in text and "daily_prices.symbol" in text:
                # pull the bound symbol from the compiled params (best-effort; falls back to a generic key)
                try:
                    params = stmt.compile().params
                    sym = next((v for k, v in params.items() if "symbol" in k), "?")
                except Exception:  # noqa: BLE001 — instrumentation must never break the test
                    sym = "?"
                self.counts[sym] = self.counts.get(sym, 0) + 1
            return self._orig(stmt, *args, **kwargs)

        session.exec = _counting_exec  # type: ignore[assignment]

    def count_for(self, symbol: str) -> int:
        return self.counts.get(symbol, 0)


# ==================================================================================================
# Realistic seed: the load-count proof over a K-date backfill + cached-vs-uncached canonical equality
# ==================================================================================================
@pytest.fixture(scope="module")
def seed_engine(tmp_path_factory):
    """One seed load + a few trading days reserved for a K-date backfill (module-scoped for speed)."""
    cfg = load_config()
    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
    # are create-once/isolation/parallelism, not the bounded-density policy).
    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
    cfg = cfg.model_copy(update={"scanner": _sc})
    from app.seed_loader import load_seed
    db_path = tmp_path_factory.mktemp("bar_cache_seed") / "bc.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    return engine, cfg, trading


def test_kdate_backfill_loads_each_symbol_at_most_once(seed_engine, monkeypatch):
    """The J-46/J-53 crux: a K-date (K >= 3) PARALLEL backfill over seed data loads each symbol's bar
    series AT MOST ONCE for the WHOLE job — not once per date NOR once per worker — proven by counting
    every full-series bar-store load (the orchestrator's `prefill` up front + any lazy load) and
    asserting no symbol is loaded twice, while >= K dates are scanned (without the cache each symbol
    would be loaded >= K times). The shared pre-filled cache is what preserves load-once under the
    parallel build (workers READ the orchestrator's pre-loaded immutable series).

    iter-42 (bound attempt #5) instrumentation note: `prefill` now eager-loads only the candidate-pool
    subset (`expected_symbols`); a handful of non-pool symbols (SPY, QQQ, ^VIX, sector/thematic ETFs —
    read by regime/market-phase inputs) fall into the EXISTING lazy per-symbol path in `bars_asof`
    instead, and — for the FIRST time — that lazy path is now genuinely reachable from MULTIPLE
    parallel worker threads racing to read the SAME not-yet-loaded symbol during this job. A
    check-then-count wrapper around `bars_asof` (`if symbol not in self._by_symbol: count()`, called
    BEFORE the real load) races against that same concurrency: two threads can both observe "not yet
    loaded" before either has stored it, over-counting a symbol whose real, `_load_lock`-guarded
    assignment only ever happens once. Instrumenting the ACTUAL write to `_by_symbol` instead (a
    dict-subclass `__setitem__` hook — a single GIL-atomic operation, so it cannot double-fire even
    under concurrent access) removes that false-positive risk while proving the identical, real
    invariant: every entry in `_by_symbol` is written exactly once for the whole job, whichever of
    `prefill`'s eager scan, `prefill`'s no-bar bookkeeping, or `bars_asof`'s lazy fallback wrote it."""
    engine, cfg, trading = seed_engine
    # three CONSECUTIVE gap dates (no snapshot yet) → K = 3. iter-18: the snapshot cadence bounds the
    # DEEP region to monthly, so pick the K dates inside the config daily-density region (>= daily_start)
    # where every trading day is a valid backfill target — the load-once proof is cadence-independent.
    daily_start = cfg.scanner.snapshot_cadence.daily_start or trading[0]
    daily_idx = next(i for i, d in enumerate(trading) if d >= daily_start)
    assert daily_idx + 3 <= len(trading)
    r_start, r_end = trading[daily_idx], trading[daily_idx + 2]
    in_range = [d for d in trading if r_start <= d <= r_end]
    assert len(in_range) >= 3  # K >= 3
    # ensure the parallel path is actually exercised (workers > 1 over a >1-date range).
    assert cfg.data_manager.import_chunking.backfill_workers > 1

    # instrument the ACTUAL write to `_by_symbol` — race-free (see the docstring above) — rather than a
    # racy check-then-call wrapper around the read side.
    load_counts: dict[str, int] = {}
    lock = __import__("threading").Lock()

    def _count(symbol):
        with lock:
            load_counts[symbol] = load_counts.get(symbol, 0) + 1

    class _CountingBySymbol(dict):
        """A `_by_symbol` dict subclass that counts each key's FIRST write exactly once — the real load
        event, whichever code path performs it. `__setitem__` is one dict-level operation (GIL-atomic),
        so this cannot double-count even when several worker threads race to lazy-load the same symbol
        (only the one thread inside `_load_lock`'s critical section ever assigns a genuinely new key)."""

        def __setitem__(self, key, value):
            is_new = key not in self
            super().__setitem__(key, value)
            if is_new:
                _count(key)

    orig_init = prices._BarCache.__init__

    def _counting_init(self, *a, **kw):
        orig_init(self, *a, **kw)
        self._by_symbol = _CountingBySymbol()  # swap in the counting dict right after construction

    monkeypatch.setattr(prices._BarCache, "__init__", _counting_init)

    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    assert summary["status"] == "ok"
    assert summary["snapshots_created"] == len(in_range)  # K snapshots created over K dates
    assert load_counts, "the bar cache should have loaded at least one symbol"
    # the invariant: NO symbol is loaded more than once for the whole K-date PARALLEL job
    assert max(load_counts.values()) == 1
    assert all(c == 1 for c in load_counts.values())


def test_cached_snapshot_equals_uncached_row_level(seed_engine):
    """Pure-refactor proof: the canonical `score_stocks(D)` output is BYTE-IDENTICAL through the bar
    cache and through the default per-request path — same rows, same scores/buckets/setups/VCP (anti-goal:
    Single source of truth — the vectorized load changes HOW bars are read, never WHAT is computed)."""
    engine, cfg, trading = seed_engine
    d = trading[205]  # any seed date with full history before it
    with Session(engine) as plain:
        uncached = score_stocks(plain, d, cfg)
    with Session(engine) as cached_session:
        with bar_cache(cached_session):
            cached = score_stocks(cached_session, d, cfg)
    # row-level equality of the full canonical output (the dicts carry every score block + components)
    assert cached == uncached
    assert cached["rows"], "the sample date should produce scored rows"
    # spot-assert a concrete canonical value matches exactly (not just dict equality)
    by_ticker_cached = {r["ticker"]: r["leadership"]["score"] for r in cached["rows"]}
    by_ticker_uncached = {r["ticker"]: r["leadership"]["score"] for r in uncached["rows"]}
    assert by_ticker_cached == by_ticker_uncached


def test_bootstrap_snapshots_equal_with_cache(seed_engine):
    """The bootstrap cadence (also cache-wrapped) produces snapshots whose stored Leadership equals a
    fresh uncached `score_stocks(D)` — the cache changes no canonical scanner output."""
    engine, cfg, trading = seed_engine
    from app.engine import scanner
    from app.models import ScannerResult
    # iter-33 (J-93): the universe is point-in-time, so use a date PAST the deterministic warm-up boundary
    # where the resolved universe is non-empty. iter-18 (30y basis): the SPY trading calendar starts
    # 2005-02-25, so day 300 is ~2006-05 — deep names (AAPL/MSFT from 1996) are far past the
    # min_history_bars warm-up there and the resolved membership is comfortably non-empty.
    d = trading[300]
    with Session(engine) as session:
        run = scanner.run_scan(session, d, cfg)  # uses bars (cache inactive here — single date)
        stored = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == run.id)).all()
        }
    with Session(engine) as plain:
        fresh = {r["ticker"]: r["leadership"]["score"] for r in score_stocks(plain, d, cfg)["rows"]}
    assert stored == fresh
    assert stored
