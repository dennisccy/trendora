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
"""
from __future__ import annotations

import pytest
from sqlmodel import Session

from app.config import Config, load_config
from app.db import create_db_and_tables, make_engine
from app.engine.data_manager import _trading_days
from app.engine.prices import bar_cache, bars_asof
from app.engine.scoring import score_stocks
from app.engine.universe_resolver import resolve_members
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
