"""iter-26 (J-16, fast-platform item F) — the byte-identity harness (the correctness gate for the
bounded scoring-input window).

`scoring.py` now slices each member's as-of bar series to the trailing `indicators.max_lookback_bars`
bars (`bars[-N:]`) at both `bars_asof` call sites (`_raw_components` and pass-3) BEFORE any indicator/
pattern runs on it — a pure LOADING optimization: a 30-year `bars_asof` series can carry ~5,300 bars on
a late as-of date, but every indicator/pattern reads only a trailing window off the end (the largest is
`high_window_52w` = 252), so bounding the window to 320 must never change a single displayed value
(anti-goal: Single source of truth).

This proves `score_stocks` is IDENTICAL with the real committed window (320) vs. an effectively-disabled
(huge) window — over >= 3 real cadence dates x the full resolved pool, PLUS a dedicated near-warm-up-
boundary date where at least one resolved member genuinely has fewer than `max_lookback_bars` own bars
(the short-history path). Modeled on `test_bar_cache.py`'s `test_cached_snapshot_equals_uncached_row_level`
/ `test_bootstrap_snapshots_equal_with_cache` idiom (a real seed load, real `score_stocks` calls, full
dict equality) rather than inventing a new comparison style.

iter-27 (J-16 memory fix) adds two sibling proofs to the same file:
  - `bars_asof_window(session, symbol, d, lookback)` (the new additive `prices.py` accessor that avoids
    materializing the whole `<= d` prefix) is BYTE-IDENTICAL to `bars_asof(session, symbol, d)[-lookback:]`
    — both the default (no-context) path and the cache-active path, for a long- and a short-history
    symbol, covering the boundary cases from the plan (empty/no-bar symbol, `d` before the first bar, `d`
    after the last bar, `lookback` larger than available history).
  - `score_regime` (now routed through `bars_asof_window` at its three call sites) is BYTE-IDENTICAL with
    the committed windowed config (320) vs. an effectively-disabled window — over the same >= 3 real
    cadence dates the `score_stocks` harness above uses.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlmodel import Session

from app.config import Config, load_config
from app.db import create_db_and_tables, make_engine
from app.engine.data_manager import _trading_days
from app.engine.prices import bar_cache, bars_asof, bars_asof_window
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.universe_resolver import resolve_members
from app.models import DailyPrice
from app.seed_loader import load_seed

# An effectively-"disabled" window: larger than any real bar series in the committed seed (~30 years is
# well under 10,000 trading days), so `bars[-DISABLED_WINDOW:]` returns every member's WHOLE series
# unchanged — the exact pre-iter-26 (unwindowed) behavior, without a second code path/flag.
DISABLED_WINDOW = 1_000_000


@pytest.fixture(scope="module")
def seed_engine(tmp_path_factory):
    """One seed load (prices only — `score_stocks` is a pure read/compute needing no persisted
    snapshot), module-scoped for speed. Mirrors `test_bar_cache.py`'s `seed_engine` fixture."""
    cfg = load_config()
    db_path = tmp_path_factory.mktemp("scoring_window_seed") / "sw.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)
    with Session(engine) as session:
        trading = _trading_days(session, cfg)
    return engine, cfg, trading


def _with_max_lookback_bars(cfg: Config, value: int) -> Config:
    """`cfg` with `indicators.max_lookback_bars` overridden to `value` — the ONE knob under test."""
    icfg = cfg.indicators.model_copy(update={"max_lookback_bars": value})
    return cfg.model_copy(update={"indicators": icfg})


def test_score_stocks_windowed_equals_unwindowed_across_dates(seed_engine):
    """The DoD correctness gate: score_stocks(D) is BYTE-IDENTICAL with the committed windowed config
    (max_lookback_bars=320) vs. an effectively-unwindowed config, over >= 3 real, well-spread cadence
    dates x the full resolved pool — 0 diffs (every score, bucket, setup, detected pattern)."""
    engine, cfg, trading = seed_engine
    windowed_cfg = cfg  # config.yaml's real committed value (320)
    unwindowed_cfg = _with_max_lookback_bars(cfg, DISABLED_WINDOW)

    # 3 real, well-spread trading days (proportional indices so this stays valid regardless of the
    # exact SPY-calendar length): an early-mid, a mid, and the deepest available (near-latest) date —
    # the highest-risk case (the longest per-symbol bar series to slice).
    n = len(trading)
    assert n >= 20, "the seed calendar should have plenty of trading days"
    indexes = sorted({n // 5, n // 2, n - 5})
    assert len(indexes) == 3, "the 3 sample indexes must be distinct"
    dates = [trading[i] for i in indexes]

    # Guard against a VACUOUS pass: on the deepest (latest) date, at least one resolved member must
    # actually carry MORE than `max_lookback_bars` own bars — otherwise "windowed vs unwindowed" would
    # be comparing two configs that slice nothing differently, and equality would prove nothing about
    # the windowing code path itself.
    deepest = dates[-1]
    with Session(engine) as probe_session:
        members = resolve_members(probe_session, deepest, cfg)
        deep_counts = [len(bars_asof(probe_session, t, deepest)) for t in members]
    assert deep_counts and max(deep_counts) > cfg.indicators.max_lookback_bars, (
        f"expected >= 1 member with > {cfg.indicators.max_lookback_bars} bars on {deepest} "
        f"(max found: {max(deep_counts) if deep_counts else 0}) — the windowing path would be untested"
    )

    for d in dates:
        with Session(engine) as windowed_session:
            windowed = score_stocks(windowed_session, d, windowed_cfg)
        with Session(engine) as unwindowed_session:
            unwindowed = score_stocks(unwindowed_session, d, unwindowed_cfg)
        assert windowed == unwindowed, f"windowed vs unwindowed score_stocks diverged on {d}"
        assert windowed["rows"], f"the sample date {d} should produce scored rows"


def test_score_stocks_windowed_equals_unwindowed_for_short_history_member(seed_engine):
    """The short-history path (DoD: 'a member with fewer than max_lookback_bars bars scores byte-
    identically'): finds the EARLIEST real date where >= 1 resolved member genuinely has fewer than
    `max_lookback_bars` own trailing bars (a name whose point-in-time entry is recent relative to that
    date — confirmed by probing the seed, never assumed), then asserts row-level equality there. The
    day-by-day probe runs inside the load-once `bar_cache` so it pays each symbol's bar-store load ONCE
    for the whole scan, not once per probed date."""
    engine, cfg, trading = seed_engine
    windowed_cfg = cfg
    unwindowed_cfg = _with_max_lookback_bars(cfg, DISABLED_WINDOW)

    d = None
    short_history_tickers: list[str] = []
    with Session(engine) as probe_session, bar_cache(probe_session):
        for day in trading:
            members = resolve_members(probe_session, day, cfg)
            shorts = [
                t for t in members
                if len(bars_asof(probe_session, t, day)) < cfg.indicators.max_lookback_bars
            ]
            if shorts:
                d, short_history_tickers = day, shorts
                break
    assert d is not None, (
        f"expected >= 1 (date, member) pair with < {cfg.indicators.max_lookback_bars} own bars "
        "somewhere in the committed seed's calendar — none found"
    )

    with Session(engine) as windowed_session:
        windowed = score_stocks(windowed_session, d, windowed_cfg)
    with Session(engine) as unwindowed_session:
        unwindowed = score_stocks(unwindowed_session, d, unwindowed_cfg)
    assert windowed == unwindowed
    windowed_by_ticker = {r["ticker"]: r for r in windowed["rows"]}
    unwindowed_by_ticker = {r["ticker"]: r for r in unwindowed["rows"]}
    for ticker in short_history_tickers:
        assert windowed_by_ticker[ticker] == unwindowed_by_ticker[ticker]


# ==================================================================================================
# iter-27 (J-16 memory fix) — score_regime windowed-vs-unwindowed (the regime routing gate)
# ==================================================================================================
def test_score_regime_windowed_equals_unwindowed_across_dates(seed_engine):
    """The iter-27 correctness gate for `regime.py`'s new `bars_asof_window`/`close_on` routing:
    `score_regime(D)` is BYTE-IDENTICAL with the committed windowed config (max_lookback_bars=320) vs.
    an effectively-unwindowed config, over the SAME 3 real, well-spread cadence dates x the full pool
    the `score_stocks` harness above uses — 0 diffs across every value `score_regime` returns (index
    MA-stack, universe breadth, new-high/low, the VIX gate)."""
    engine, cfg, trading = seed_engine
    windowed_cfg = cfg  # config.yaml's real committed value (320)
    unwindowed_cfg = _with_max_lookback_bars(cfg, DISABLED_WINDOW)

    n = len(trading)
    assert n >= 20, "the seed calendar should have plenty of trading days"
    indexes = sorted({n // 5, n // 2, n - 5})
    assert len(indexes) == 3, "the 3 sample indexes must be distinct"
    dates = [trading[i] for i in indexes]

    # Guard against a VACUOUS pass: on the deepest (latest) date, at least one of the regime engine's OWN
    # inputs (an index ETF, a universe symbol, or the VIX symbol) must genuinely carry MORE than
    # `max_lookback_bars` own bars — otherwise windowed vs unwindowed would compare two configs that slice
    # nothing differently here, proving nothing about the new `_index_ma_stack`/`_universe_stats` routing.
    deepest = dates[-1]
    with Session(engine) as probe_session:
        regime_symbols = list(cfg.etfs.index) + list(cfg.universe.symbols) + list(cfg.etfs.volatility)
        deep_counts = [len(bars_asof(probe_session, s, deepest)) for s in regime_symbols]
    assert deep_counts and max(deep_counts) > cfg.indicators.max_lookback_bars, (
        f"expected >= 1 regime input symbol with > {cfg.indicators.max_lookback_bars} bars on {deepest} "
        f"(max found: {max(deep_counts) if deep_counts else 0}) — the windowing path would be untested"
    )

    for d in dates:
        with Session(engine) as windowed_session:
            windowed = score_regime(windowed_session, d, windowed_cfg)
        with Session(engine) as unwindowed_session:
            unwindowed = score_regime(unwindowed_session, d, unwindowed_cfg)
        assert windowed == unwindowed, f"windowed vs unwindowed score_regime diverged on {d}"
        assert windowed["score"] is not None, f"the sample date {d} should produce a regime score"


# ==================================================================================================
# iter-27 (J-16 memory fix) — bars_asof_window direct unit coverage (default + cache-active paths)
# ==================================================================================================
@pytest.fixture()
def window_price_engine(tmp_path):
    """A hand-built two-symbol DB for `bars_asof_window` unit coverage: "SHORT" (5 gapped bars, the same
    shape `test_forward_testing.py`'s `tiny_price_engine` uses) and "LONG" (60 consecutive daily bars) —
    enough for a `lookback` to both TRUNCATE (LONG) and EXCEED available history (SHORT). A third,
    never-inserted symbol ("NOBAR") covers the empty-cache / zero-bar case."""
    engine = make_engine(f"sqlite:///{tmp_path / 'window.db'}")
    create_db_and_tables(engine)
    short_days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]  # a gap at the 6th/7th (weekend-like)
    long_days = [date(2024, 2, 1) + timedelta(days=i) for i in range(60)]  # consecutive, no gap
    with Session(engine) as session:
        for i, d in enumerate(short_days):
            c = float(10 + i)
            session.add(
                DailyPrice(symbol="SHORT", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=100.0 + i)
            )
        for i, d in enumerate(long_days):
            c = float(100 + i)
            session.add(
                DailyPrice(symbol="LONG", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=1000.0 + i)
            )
        session.commit()
    return engine, short_days, long_days


def _tail_via_bars_asof(session: Session, symbol: str, d: date, lookback: int) -> list[tuple]:
    """The reference definition `bars_asof_window` must match exactly: the ordinary `bars_asof(...)[-
    lookback:]` slice's `(date, close)` pairs, same order — computed the OLD (unbounded-prefix) way."""
    full = bars_asof(session, symbol, d)
    tail = full[-lookback:] if lookback > 0 else []
    return [(b.date, b.close) for b in tail]


def test_bars_asof_window_matches_tail_slice_default_and_cached(window_price_engine):
    """`bars_asof_window` is BYTE-IDENTICAL to `bars_asof(...)[-lookback:]`, in BOTH the default
    (no-context) path and the cache-active path — the same cache-vs-default pairing style
    `test_forward_testing.py`'s `close_on`/`bars_after` cache-awareness tests use — covering every
    boundary case from the iter-27 plan: a lookback that truncates a long series (`cut > lookback`), a
    lookback that EXCEEDS a short series' whole history (`cut < lookback`), `d` before the symbol's
    first bar (`cut == 0`), `d` on/after the last bar (`cut == len(full)`), and a symbol with NO bars at
    all (empty cache)."""
    engine, short_days, long_days = window_price_engine
    probes = [
        ("LONG", long_days[45], 10),                      # mid-series: lookback (10) truncates a 46-bar prefix
        ("LONG", long_days[-1], 10),                       # cut == len(full): the last bar itself
        ("LONG", long_days[-1] + timedelta(days=5), 10),   # d strictly after the last bar: cut == len(full)
        ("LONG", long_days[0], 10),                        # cut == 1: lookback (10) exceeds the 1-bar prefix
        ("SHORT", short_days[2], 10),                       # lookback (10) EXCEEDS SHORT's whole history (5 bars)
        ("SHORT", date(2023, 12, 31), 10),                 # d before SHORT's first bar: cut == 0
        ("NOBAR", date(2024, 6, 1), 10),                   # a symbol with zero bars: empty cache, cut == 0
    ]
    with Session(engine) as plain:
        reference = {p: _tail_via_bars_asof(plain, p[0], p[1], p[2]) for p in probes}
    with Session(engine) as plain2:
        uncached = {
            p: [(b.date, b.close) for b in bars_asof_window(plain2, p[0], p[1], p[2])] for p in probes
        }
    assert uncached == reference
    with Session(engine) as cached_session, bar_cache(cached_session):
        cached = {
            p: [(b.date, b.close) for b in bars_asof_window(cached_session, p[0], p[1], p[2])]
            for p in probes
        }
    assert cached == reference
    # sanity: the truncating, whole-history, and empty cases actually exercise different branches.
    assert len(reference[("LONG", long_days[45], 10)]) == 10  # truncated
    assert len(reference[("SHORT", short_days[2], 10)]) == 3  # whole (SHORT's <= d prefix is 3 bars)
    assert reference[("NOBAR", date(2024, 6, 1), 10)] == []
