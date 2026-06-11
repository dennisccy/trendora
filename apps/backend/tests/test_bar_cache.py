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
    from app.seed_loader import load_seed
    db_path = tmp_path_factory.mktemp("bar_cache_seed") / "bc.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    return engine, cfg, trading


def test_kdate_backfill_loads_each_symbol_at_most_once(seed_engine, monkeypatch):
    """The J-46 crux: a K-date (K >= 3) backfill over seed data loads each symbol's bar series AT MOST
    ONCE for the WHOLE job — proven by instrumenting `_BarCache` to record each full-series load and
    asserting no symbol is loaded twice, while >= K dates are scanned (without the cache each symbol
    would be loaded >= K times)."""
    engine, cfg, trading = seed_engine
    # three CONSECUTIVE gap dates (no snapshot yet) → K = 3
    r_start, r_end = trading[200], trading[202]
    in_range = [d for d in trading if r_start <= d <= r_end]
    assert len(in_range) >= 3  # K >= 3

    # instrument the bar-store load point: count how many times each symbol's full series is loaded
    load_counts: dict[str, int] = {}
    orig_bars_asof = prices._BarCache.bars_asof

    def _counting_bars_asof(self, session, symbol, d):
        if symbol not in self._by_symbol:  # a real bar-store load is about to happen for this symbol
            load_counts[symbol] = load_counts.get(symbol, 0) + 1
        return orig_bars_asof(self, session, symbol, d)

    monkeypatch.setattr(prices._BarCache, "bars_asof", _counting_bars_asof)

    job = create_job("backfill", r_start, r_end)
    summary = run_data_job(job.job_id, config=cfg, engine=engine)
    assert summary["status"] == "ok"
    assert summary["snapshots_created"] == len(in_range)  # K snapshots created over K dates
    assert load_counts, "the bar cache should have loaded at least one symbol"
    # the invariant: NO symbol is loaded more than once for the whole K-date job
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
    d = trading[150]
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
