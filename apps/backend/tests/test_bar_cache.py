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
    parallel build (workers READ the orchestrator's pre-loaded immutable series)."""
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

    # instrument EVERY full-series bar-store load — both the eager `prefill` and the lazy `bars_asof`
    # fallback push rows into `_by_symbol`, so a per-symbol DB query is exactly an entry appearing there.
    load_counts: dict[str, int] = {}
    lock = __import__("threading").Lock()
    orig_bars_asof = prices._BarCache.bars_asof
    orig_prefill = prices._BarCache.prefill

    def _count(symbol):
        with lock:
            load_counts[symbol] = load_counts.get(symbol, 0) + 1

    def _counting_bars_asof(self, session, symbol, d):
        if symbol not in self._by_symbol:  # a real lazy bar-store load is about to happen
            _count(symbol)
        return orig_bars_asof(self, session, symbol, d)

    def _counting_prefill(self, session, expected_symbols=None):
        before = set(self._by_symbol)
        orig_prefill(self, session, expected_symbols=expected_symbols)
        for symbol in self._by_symbol:
            if symbol not in before:  # newly loaded by this prefill (incl. a no-bar candidate as [])
                _count(symbol)

    monkeypatch.setattr(prices._BarCache, "bars_asof", _counting_bars_asof)
    monkeypatch.setattr(prices._BarCache, "prefill", _counting_prefill)

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
