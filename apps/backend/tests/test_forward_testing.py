"""Walk-forward forward-testing engine — the critical-anti-goal proofs (iter-6).

Named proofs, each guarding a critical anti-goal:
  - bars_after / close_on boundary  — the forward side reads ONLY bars with date > D.   *(No lookahead)*
  - forward_return purity           — h-th post-bar, NA when short, unchanged by later bars. *(No lookahead)*
  - aggregates read stored bucket   — grouping uses the STORED leadership_bucket verbatim.  *(Single source)*
  - aggregates exact means          — by-bucket/setup/regime/excess/control on a hand fixture.
  - control-group determinism       — same config seed -> identical random cohort.
  - no fabrication                  — zero-post-bar run = n=0; both regimes present.       *(No fabricated data)*
  - backfill INSERT-only+idempotent — no UPDATE of any snapshot row; 2nd backfill inserts 0. *(Snapshots immutable)*
  - scores never fed back           — a run's stored scores are identical with/without forward returns. *(No lookahead)*

The pure / hand-fixture tests run on tiny in-memory data (fast). The backfill integration proof runs the
real engines on the committed seed under a REDUCED walk-forward cadence (module-scoped, once).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from statistics import stdev

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

import app.engine.market_phase as market_phase
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.forward_testing import (
    _claim_samples_kwargs,
    _drawdown_expectations_cache_subject,
    backfill_forward_returns,
    compute_drawdown_expectations,
    compute_drawdown_expectations_cached,
    compute_forward_aggregates,
    forward_excursions,
    forward_return,
    max_drawdown,
    time_to_recover_days,
    underwater_days,
    walk_forward_asof_dates,
)
from app.engine.prices import bar_cache, bars_after, bars_asof, close_on, latest_data_date
from app.engine.scanner import run_scan
from app.models import (
    DailyPrice,
    EventStudyCache,
    ForwardReturn,
    ScannerResult,
    ScannerRun,
    SectorScoreRow,
    ThemeScoreRow,
)
from app.seed_loader import load_seed


# ==================================================================================================
# Pure helpers / tiny stand-ins
# ==================================================================================================
class _Bar:
    """A minimal post-snapshot bar stand-in. `.close` drives forward_return; `.high`/`.low` drive
    forward_excursions (iter-14). `high`/`low` default to `close` so the pure forward_return fixtures
    that pass only closes are unaffected."""

    def __init__(self, close: float, d: date | None = None, high: float | None = None, low: float | None = None):
        self.close = close
        self.date = d
        self.high = close if high is None else high
        self.low = close if low is None else low


def _bars(closes: list[float]) -> list[_Bar]:
    return [_Bar(c) for c in closes]


def _ex_bars(rows: list[tuple[float, float, float]]) -> list[_Bar]:
    """Post-snapshot bars with explicit (high, low, close) — only high/low matter to forward_excursions."""
    return [_Bar(close=c, high=h, low=lo) for (h, lo, c) in rows]


# ==================================================================================================
# bars_after / close_on — the forward no-lookahead boundary
# ==================================================================================================
@pytest.fixture()
def tiny_price_engine(tmp_path):
    """A temp DB with one symbol's bars on five known dates (no engine, no seed)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'tiny.db'}")
    create_db_and_tables(engine)
    days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]
    with Session(engine) as session:
        for i, d in enumerate(days):
            close = float(10 + i)  # 10, 11, 12, 13, 14
            session.add(DailyPrice(symbol="AAA", date=d, open=close, high=close, low=close, close=close, volume=1.0))
        session.commit()
    return engine, days


def test_bars_after_returns_only_future_bars_ascending(tiny_price_engine):
    """No-lookahead (forward): bars_after(D) returns ONLY bars with date > D, ascending, and never a
    bar with date <= D — and it partitions the history with bars_asof at exactly D (no overlap)."""
    engine, days = tiny_price_engine
    d = days[1]  # 2024-01-03
    with Session(engine) as session:
        after = bars_after(session, "AAA", d)
        asof = bars_asof(session, "AAA", d)

    assert [b.date for b in after] == days[2:]  # strictly the later dates, ascending
    assert all(b.date > d for b in after)
    assert all(b.date <= d for b in asof)
    # disjoint + complete partition at D (this disjointness IS the no-lookahead guarantee)
    assert {b.date for b in asof}.isdisjoint({b.date for b in after})
    assert {b.date for b in asof} | {b.date for b in after} == set(days)


def test_bars_after_limit_is_the_unbounded_prefix(tiny_price_engine):
    """The bounded backfill call equals the unbounded boundary truncated to `limit` (same bars)."""
    engine, days = tiny_price_engine
    d = days[0]
    with Session(engine) as session:
        full = bars_after(session, "AAA", d)
        limited = bars_after(session, "AAA", d, limit=2)
    assert [b.date for b in limited] == [b.date for b in full[:2]]
    assert [b.close for b in limited] == [b.close for b in full[:2]]


def test_close_on_is_the_asof_close(tiny_price_engine):
    """close_on(D) is the close of the latest bar with date <= D (the entry close on D)."""
    engine, days = tiny_price_engine
    with Session(engine) as session:
        assert close_on(session, "AAA", days[2]) == 12.0  # the bar ON 2024-01-04
        # a non-trading gap date resolves to the latest prior bar (<= D)
        assert close_on(session, "AAA", date(2024, 1, 7)) == 13.0  # latest <= 2024-01-07 is 2024-01-05
        assert close_on(session, "AAA", date(2023, 12, 31)) is None  # before all data
        assert close_on(session, "MISSING", days[0]) is None


# ==================================================================================================
# iter-26 (J-16, fast-platform item F) — close_on / bars_after cache-awareness
#
# `close_on`/`bars_after` are now cache-aware: inside an active `bar_cache(session)` context they
# derive their answer from the once-loaded cached series instead of issuing a raw query. Proves the
# cache-aware path is BYTE-IDENTICAL to the default (no-context) path, for both a long-history and a
# short-history symbol. ADDITIVE — the tests above (`test_close_on_is_the_asof_close`,
# `test_bars_after_returns_only_future_bars_ascending`, `test_bars_after_limit_is_the_unbounded_prefix`)
# are unedited; a new fixture keeps this proof independent of `tiny_price_engine`.
# ==================================================================================================
@pytest.fixture()
def two_symbol_price_engine(tmp_path):
    """"AAA": short history (5 bars, same shape/gap as `tiny_price_engine`) and "BBB": long history (30
    consecutive daily bars, no gap) — sharing no dates, so each symbol's cache load is independent."""
    engine = make_engine(f"sqlite:///{tmp_path / 'two_symbol.db'}")
    create_db_and_tables(engine)
    short_days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]  # a gap at the 6th/7th (weekend-like)
    long_days = [date(2024, 2, 1) + timedelta(days=i) for i in range(30)]  # consecutive, no gap
    with Session(engine) as session:
        for i, d in enumerate(short_days):
            c = float(10 + i)
            session.add(DailyPrice(symbol="AAA", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=100.0 + i))
        for i, d in enumerate(long_days):
            c = float(100 + i)
            session.add(DailyPrice(symbol="BBB", date=d, open=c, high=c + 1, low=c - 1, close=c, volume=1000.0 + i))
        session.commit()
    return engine, short_days, long_days


def test_close_on_cache_aware_matches_uncached(two_symbol_price_engine):
    """close_on's cache-aware path (an active bar_cache) is byte-identical to the default uncached
    query, for a long-history symbol ("BBB") and a short-history symbol ("AAA"), each probed at an
    in-range date, a gap/non-trading date, and a before-all-data date."""
    engine, short_days, long_days = two_symbol_price_engine
    probes = {
        "AAA": [short_days[2], date(2024, 1, 7), date(2023, 12, 31)],
        "BBB": [long_days[10], long_days[-1], date(2024, 1, 31)],
    }
    with Session(engine) as plain:
        uncached = {(sym, d): close_on(plain, sym, d) for sym, ds in probes.items() for d in ds}
    with Session(engine) as cached_session, bar_cache(cached_session):
        cached = {(sym, d): close_on(cached_session, sym, d) for sym, ds in probes.items() for d in ds}
    assert cached == uncached
    assert cached[("AAA", short_days[2])] == 12.0  # the bar ON 2024-01-04
    assert cached[("BBB", long_days[10])] == 110.0  # the bar 10 days into BBB's series


def test_bars_after_cache_aware_matches_uncached(two_symbol_price_engine):
    """bars_after's cache-aware path is byte-identical to the default uncached query — unlimited AND
    with a limit — for both a long-history and a short-history symbol."""
    engine, short_days, long_days = two_symbol_price_engine
    cuts = {"AAA": short_days[0], "BBB": long_days[5]}
    with Session(engine) as plain:
        uncached_full = {s: [(b.date, b.close) for b in bars_after(plain, s, d)] for s, d in cuts.items()}
        uncached_limited = {
            s: [(b.date, b.close) for b in bars_after(plain, s, d, limit=2)] for s, d in cuts.items()
        }
    with Session(engine) as cached_session, bar_cache(cached_session):
        cached_full = {
            s: [(b.date, b.close) for b in bars_after(cached_session, s, d)] for s, d in cuts.items()
        }
        cached_limited = {
            s: [(b.date, b.close) for b in bars_after(cached_session, s, d, limit=2)]
            for s, d in cuts.items()
        }
    assert cached_full == uncached_full
    assert cached_limited == uncached_limited
    for sym in cuts:
        assert cached_limited[sym] == cached_full[sym][:2]
        assert all(bar_date > cuts[sym] for bar_date, _ in cached_full[sym])  # no-lookahead: strictly > D


# ==================================================================================================
# forward_return — pure no-lookahead math
# ==================================================================================================
def test_forward_return_uses_the_hth_post_bar():
    """Realized return over h days = close of the h-th POST-snapshot bar / entry_close - 1."""
    post = _bars([110.0, 121.0, 133.0])  # entry 100 -> +10% / +21% / +33%
    assert forward_return(post, 100.0, 1) == pytest.approx(0.10)
    assert forward_return(post, 100.0, 2) == pytest.approx(0.21)
    assert forward_return(post, 100.0, 3) == pytest.approx(0.33)


def test_forward_return_is_na_when_fewer_than_h_post_bars():
    """NA (None) — never a fabricated/truncated number — when fewer than h post-bars exist."""
    post = _bars([110.0, 120.0])
    assert forward_return(post, 100.0, 3) is None
    assert forward_return([], 100.0, 1) is None


def test_forward_return_unchanged_when_later_bars_removed():
    """Only the first h post-bars matter: removing bars dated > d+h does not change the h-day return
    (the keystone no-lookahead-of-the-future-tail proof)."""
    full = _bars([110.0, 121.0, 133.0, 145.0, 160.0])
    truncated = _bars([110.0, 121.0, 133.0])  # everything after the 3rd post-bar removed
    assert forward_return(full, 100.0, 3) == forward_return(truncated, 100.0, 3) == pytest.approx(0.33)


def test_forward_return_na_on_missing_or_zero_entry():
    post = _bars([110.0])
    assert forward_return(post, None, 1) is None
    assert forward_return(post, 0.0, 1) is None


# ==================================================================================================
# forward_excursions — pure no-lookahead MAE/MFE math (iter-14, J-29)
# ==================================================================================================
def test_forward_excursions_uses_only_first_h_post_bars():
    """MAE/MFE = min-low / max-high over the FIRST h post-bars, measured from entry_close. A later bar
    with an extreme high/low (the 3rd here) must NOT influence the h=2 window."""
    post = _ex_bars([(110, 95, 105), (120, 90, 115), (200, 10, 150)])  # 3rd bar is outside an h<=2 window
    ex1 = forward_excursions(post, 100.0, 1)
    assert ex1["mfe"] == pytest.approx(110 / 100 - 1)  # +10% (max high over bar 1)
    assert ex1["mae"] == pytest.approx(95 / 100 - 1)   # -5%  (min low  over bar 1)
    ex2 = forward_excursions(post, 100.0, 2)
    assert ex2["mfe"] == pytest.approx(120 / 100 - 1)  # +20% (max high over bars 1-2; 200 excluded)
    assert ex2["mae"] == pytest.approx(90 / 100 - 1)   # -10% (min low  over bars 1-2; 10 excluded)


def test_forward_excursions_na_when_fewer_than_h_post_bars_or_no_entry():
    """NA (None) — never a fabricated excursion — when fewer than h post-bars exist or entry is
    missing/zero (the EXACT same gate as forward_return)."""
    post = _ex_bars([(110, 95, 105), (120, 90, 115)])
    assert forward_excursions(post, 100.0, 3) is None
    assert forward_excursions([], 100.0, 1) is None
    assert forward_excursions(post, None, 1) is None
    assert forward_excursions(post, 0.0, 1) is None


def test_forward_excursions_unchanged_when_later_bars_removed():
    """No-lookahead (the keystone proof): removing bars dated > d+h does not change the h-day MAE/MFE —
    the future tail can never influence the as-of-h excursions."""
    full = _ex_bars([(110, 95, 105), (120, 90, 115), (300, 5, 200), (90, 80, 85)])
    truncated = _ex_bars([(110, 95, 105), (120, 90, 115)])  # everything after the 2nd post-bar removed
    assert forward_excursions(full, 100.0, 2) == forward_excursions(truncated, 100.0, 2)


def test_forward_excursions_band_contains_realized_return():
    """The close-to-close return at h lies WITHIN the [mae, mfe] band (MFE >= realized >= MAE): the
    entry is shared and the h-th close sits between the window's low-min and high-max."""
    post = _ex_bars([(110, 95, 105), (130, 92, 121)])  # h=2 close 121 -> realized +21%
    realized = forward_return(post, 100.0, 2)
    ex = forward_excursions(post, 100.0, 2)
    assert realized == pytest.approx(0.21)
    assert ex["mae"] <= realized <= ex["mfe"]
    assert ex["mfe"] == pytest.approx(130 / 100 - 1) and ex["mae"] == pytest.approx(92 / 100 - 1)


# ==================================================================================================
# max_drawdown — pure no-lookahead true peak-to-trough math (iter-27, J-86)
# ==================================================================================================
def test_max_drawdown_running_peak_seeded_at_entry():
    """The running peak is seeded at the as-of-D entry_close, so the FIRST bar's drawdown is measured
    from the entry; a later bar that prints a new HIGH raises the peak for subsequent bars only — the
    worst (most negative) peak-to-trough drop is returned."""
    # entry 100; bar1 high110/low95; bar2 high120/low90; bar3 high118/low80
    post = _ex_bars([(110, 95, 100), (120, 90, 115), (118, 80, 100)])
    # h=1: peak max(100,110)=110, trough low 95 -> 95/110-1
    assert max_drawdown(post, 100.0, 1) == pytest.approx(95 / 110 - 1)
    # h=3: running peak rises to 120 by bar2; bar3 low 80 against peak 120 is the worst -> 80/120-1
    assert max_drawdown(post, 100.0, 3) == pytest.approx(80 / 120 - 1)


def test_max_drawdown_is_always_non_positive():
    """MDD is <= 0 always: a flat/rising path whose low never dips below its running peak yields exactly
    0.0 (never a positive 'drawdown')."""
    flat = _ex_bars([(100, 100, 100)])  # peak 100, low 100 -> 100/100-1 == 0.0
    assert max_drawdown(flat, 100.0, 1) == 0.0
    rising = _ex_bars([(110, 100, 108), (130, 120, 128)])  # every low == prior peak; no dip below peak
    assert max_drawdown(rising, 100.0, 2) <= 0.0


def test_max_drawdown_na_when_fewer_than_h_post_bars_or_no_entry():
    """Shares the EXACT no-lookahead NA gate as forward_return/forward_excursions: None (NA) — never a
    fabricated 0 — when fewer than `horizon` post-bars exist or the entry is missing/zero."""
    post = _ex_bars([(110, 95, 105), (120, 90, 115)])
    assert max_drawdown(post, 100.0, 3) is None      # < horizon post-bars
    assert max_drawdown([], 100.0, 1) is None         # no post-bar
    assert max_drawdown(post, None, 1) is None         # no entry
    assert max_drawdown(post, 0.0, 1) is None          # zero entry


def test_max_drawdown_unchanged_when_later_bars_removed():
    """No-lookahead (the keystone proof): removing bars dated > d+h does not change the h-day MDD — the
    future tail can never influence the as-of-h drawdown."""
    full = _ex_bars([(110, 95, 105), (120, 90, 115), (300, 5, 200), (90, 80, 85)])
    truncated = _ex_bars([(110, 95, 105), (120, 90, 115)])
    assert max_drawdown(full, 100.0, 2) == max_drawdown(truncated, 100.0, 2)


def test_max_drawdown_within_mae_relationship():
    """For a single-running-peak window the MDD is at least as adverse as the MAE (MDD <= MAE <= 0): the
    drawdown measures from the RUNNING PEAK (>= entry), so its denominator is never smaller than the
    entry the MAE divides by — the trough/peak ratio is <= trough/entry."""
    post = _ex_bars([(130, 95, 120), (140, 88, 100)])  # peak rises to 140; trough 88
    mdd = max_drawdown(post, 100.0, 2)
    ex = forward_excursions(post, 100.0, 2)
    assert mdd <= ex["mae"] <= 0


# ==================================================================================================
# underwater_days / time_to_recover_days — pure no-lookahead "dry spell" math (iter-41, J-25)
# ==================================================================================================
def test_underwater_days_counts_closes_below_running_peak():
    """The running peak is seeded at entry (mirrors max_drawdown) and raised by each bar's HIGH before
    that SAME bar's close is checked against it — a bar that closes exactly AT its own fresh peak is not
    counted underwater; every other bar whose close sits below the running peak is."""
    # entry 100; bar0 high102/low98/close99 (peak->102, 99<102 underwater);
    # bar1 high101/low85/close90 (peak stays 102, 90<102 underwater);
    # bar2 high105/low92/close105 (peak->105, close==peak -> NOT underwater);
    # bar3 high112/low108/close110 (peak stays 105... wait 112>105 -> peak->112, 110<112 underwater)
    post = _ex_bars([(102, 98, 99), (101, 85, 90), (105, 92, 105), (112, 108, 110)])
    assert underwater_days(post, 100.0, 4) == 3  # bar0, bar1, bar3 underwater; bar2 closes at its own peak


def test_underwater_days_seeded_at_entry_first_bar_below_entry():
    """The peak is seeded at entry_close, so a FIRST bar entirely below entry is measured against the
    entry itself (not fabricated as 'above peak')."""
    post = _ex_bars([(98, 90, 92)])  # high/low/close all below entry 100 -> peak stays 100, 92<100
    assert underwater_days(post, 100.0, 1) == 1


def test_underwater_days_na_when_fewer_than_h_post_bars_or_no_entry():
    """Shares the EXACT no-lookahead NA gate as forward_return/max_drawdown: None — never a fabricated
    0 — when fewer than `horizon` post-bars exist or the entry is missing/zero."""
    post = _ex_bars([(110, 95, 105), (120, 90, 115)])
    assert underwater_days(post, 100.0, 3) is None
    assert underwater_days([], 100.0, 1) is None
    assert underwater_days(post, None, 1) is None
    assert underwater_days(post, 0.0, 1) is None


def test_underwater_days_unchanged_when_later_bars_removed():
    """No-lookahead: removing bars dated > d+h does not change the h-day underwater count."""
    full = _ex_bars([(110, 95, 105), (120, 90, 115), (300, 5, 200), (90, 80, 85)])
    truncated = _ex_bars([(110, 95, 105), (120, 90, 115)])
    assert underwater_days(full, 100.0, 2) == underwater_days(truncated, 100.0, 2)


def test_time_to_recover_days_counts_bars_from_trough_to_entry_reclaim():
    """time_to_recover = bars from the max_drawdown TROUGH (the SAME running-peak trough max_drawdown
    identifies) until close first reaches >= entry_close, within the horizon window."""
    # entry 100; trough is bar1 (worst peak-to-trough drop) as established by max_drawdown's own math.
    post = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (105, 92, 104)])
    mdd = max_drawdown(post, 100.0, 4)
    assert mdd == pytest.approx(85 / 102 - 1)  # confirms the trough is bar1 (peak 102 by then)
    # bar1 close=90 (no), bar2 close=93 (no), bar3 close=104 (recovers) -> 2 bars after the trough
    assert time_to_recover_days(post, 100.0, 4) == 2


def test_time_to_recover_days_zero_when_trough_bar_itself_recovers():
    """0 when the trough bar's OWN close already sits at/above the entry level (never a fabricated
    positive count for an immediate same-bar reclaim)."""
    post = _ex_bars([(130, 95, 129)])  # single bar: low 95 is the trough, but close 129 >= entry 100
    assert time_to_recover_days(post, 100.0, 1) == 0


def test_time_to_recover_days_na_when_never_recovers_in_window():
    """None (NA — never a fabricated horizon-sentinel) when the close never reclaims the entry level
    within the horizon window."""
    post = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (99, 92, 96)])  # never closes >= 100 again
    assert time_to_recover_days(post, 100.0, 4) is None


def test_time_to_recover_days_na_when_fewer_than_h_post_bars_or_no_entry():
    """Shares the EXACT no-lookahead NA gate as forward_return/max_drawdown."""
    post = _ex_bars([(110, 95, 105), (120, 90, 115)])
    assert time_to_recover_days(post, 100.0, 3) is None
    assert time_to_recover_days([], 100.0, 1) is None
    assert time_to_recover_days(post, None, 1) is None
    assert time_to_recover_days(post, 0.0, 1) is None


def test_time_to_recover_days_unchanged_when_later_bars_removed():
    """No-lookahead: removing bars dated > d+h does not change the h-day time-to-recover."""
    full = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (105, 92, 104), (300, 5, 250)])
    truncated = _ex_bars([(102, 98, 99), (101, 85, 90), (95, 88, 93), (105, 92, 104)])
    assert time_to_recover_days(full, 100.0, 4) == time_to_recover_days(truncated, 100.0, 4) == 2


# ==================================================================================================
# Hand-built snapshot fixture for the aggregation proofs (no engine — exact values by construction)
# ==================================================================================================
def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _add_run(session: Session, asof: date, regime_label: str) -> ScannerRun:
    run = ScannerRun(
        asof_date=asof,
        created_at=_utc(),
        provider="seed",
        benchmark="SPY",
        regime_score=50.0,
        regime_label=regime_label,
        regime_components_json="[]",
        new_high_low_json="{}",
        candidate_counts_json="{}",
    )
    session.add(run)
    session.flush()
    return run


def _add_result(
    session, run_id, ticker, bucket, setup, sector, rank, lead_score=50.0,
    is_vcp=False, is_pullback_to_rising_dma=False, is_flat_base_breakout=False,
):
    session.add(
        ScannerResult(
            run_id=run_id, ticker=ticker, name=ticker, sector=sector,
            leadership_score=lead_score, leadership_bucket=bucket,
            entry_quality_score=0.0, entry_quality_bucket="E",
            risk_score=0.0, risk_bucket="E",
            setup_status=setup, rank=rank, record_json="{}", is_vcp=is_vcp,
            is_pullback_to_rising_dma=is_pullback_to_rising_dma,
            is_flat_base_breakout=is_flat_base_breakout,
        )
    )


def _add_fr(session, run_id, symbol, horizon, ret):
    session.add(
        ForwardReturn(
            run_id=run_id, symbol=symbol, horizon=horizon,
            asof_date=date(2025, 1, 1), entry_close=100.0,
            measured_date=date(2025, 2, 1), realized_return=ret,
        )
    )


@pytest.fixture()
def aggregates_engine(tmp_path):
    """A hand-built two-run snapshot with known forward returns at horizon H, plus a third run with NO
    forward returns (the n=0 case). Tech sector ETF = XLK, Energy = XLE (real config mapping)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'agg.db'}")
    create_db_and_tables(engine)
    H = 20
    with Session(engine) as session:
        # run1 — Risk-on
        r1 = _add_run(session, date(2025, 1, 10), "Risk-on")
        _add_result(session, r1.id, "AAA", "A", "Actionable", "Technology", 1)
        _add_result(session, r1.id, "BBB", "A", "Breakout-watch", "Technology", 2)
        _add_result(session, r1.id, "CCC", "E", "Avoid", "Technology", 3)
        _add_result(session, r1.id, "DDD", "E", "Avoid", "Energy", 4)
        for sym, ret in [("AAA", 0.10), ("BBB", 0.20), ("CCC", 0.00), ("DDD", -0.10),
                         ("SPY", 0.05), ("QQQ", 0.06), ("XLK", 0.04), ("XLE", -0.02)]:
            _add_fr(session, r1.id, sym, H, ret)
        # run2 — Risk-off
        r2 = _add_run(session, date(2024, 7, 10), "Risk-off")
        _add_result(session, r2.id, "AAA", "B", "Pullback-watch", "Technology", 1)
        _add_result(session, r2.id, "EEE", "E", "Risk-off-watchlist", "Technology", 2)
        for sym, ret in [("AAA", 0.30), ("EEE", 0.10), ("SPY", 0.08), ("QQQ", 0.07), ("XLK", 0.05)]:
            _add_fr(session, r2.id, sym, H, ret)
        # run3 — no forward returns at all (the n=0 / zero-post-bar demonstration)
        r3 = _add_run(session, date(2026, 5, 1), "Risk-on")
        _add_result(session, r3.id, "AAA", "A", "Actionable", "Technology", 1)
        session.commit()
    return engine, H


def _by(rows, key, value):
    for row in rows:
        if row[key] == value:
            return row
    return None


def test_aggregates_by_bucket_setup_regime_exact(aggregates_engine):
    """Exact by-bucket / by-setup / by-regime means + n on the hand fixture (single canonical math)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, cfg)

    # by-bucket A..E always present (padded); means exact
    by_bucket = {r["bucket"]: r for r in agg["by_bucket"]}
    assert [r["bucket"] for r in agg["by_bucket"]] == ["A", "B", "C", "D", "E"]
    assert by_bucket["A"]["n"] == 2 and by_bucket["A"]["mean_return"] == pytest.approx(0.15)  # AAA,BBB
    assert by_bucket["B"]["n"] == 1 and by_bucket["B"]["mean_return"] == pytest.approx(0.30)  # AAA(run2)
    assert by_bucket["C"]["n"] == 0 and by_bucket["C"]["mean_return"] is None
    assert by_bucket["E"]["n"] == 3 and by_bucket["E"]["mean_return"] == pytest.approx(0.0)  # CCC,DDD,EEE

    # by-setup (only non-empty groups)
    assert _by(agg["by_setup"], "setup", "Actionable")["mean_return"] == pytest.approx(0.10)
    assert _by(agg["by_setup"], "setup", "Avoid")["n"] == 2
    assert _by(agg["by_setup"], "setup", "Avoid")["mean_return"] == pytest.approx(-0.05)  # CCC 0, DDD -0.10

    # by-regime — BOTH regimes present (no-fabrication: both Risk-on and Risk-off in the sample)
    regimes = {r["regime"]: r for r in agg["by_regime"]}
    assert "Risk-on" in regimes and "Risk-off" in regimes
    assert regimes["Risk-on"]["n"] == 4 and regimes["Risk-on"]["mean_return"] == pytest.approx(0.05)
    assert regimes["Risk-off"]["n"] == 2 and regimes["Risk-off"]["mean_return"] == pytest.approx(0.20)


def test_aggregates_excess_vs_spy_and_qqq_exact(aggregates_engine):
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())

    # overall stock mean = mean(0.10,0.20,0.00,-0.10,0.30,0.10) = 0.10 over n=6
    assert agg["overall"]["n"] == 6 and agg["overall"]["mean_return"] == pytest.approx(0.10)
    # SPY mean over the two runs = mean(0.05, 0.08) = 0.065 ; excess = 0.10 - 0.065
    assert agg["excess"]["vs_spy"]["benchmark"] == "SPY"
    assert agg["excess"]["vs_spy"]["mean_excess"] == pytest.approx(0.035)
    assert agg["excess"]["vs_spy"]["n"] == 6 and agg["excess"]["vs_spy"]["benchmark_n"] == 2
    # QQQ mean = mean(0.06, 0.07) = 0.065 ; excess = 0.035
    assert agg["excess"]["vs_qqq"]["mean_excess"] == pytest.approx(0.035)


def test_aggregates_control_groups(aggregates_engine):
    """Control-group cohorts: top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF, each numeric+n."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    cg = {c["key"]: c for c in agg["control_group"]}
    assert set(cg) == {"top_ranked", "random_same_sector", "spy", "qqq", "sector_etf"}

    # top_n=20 (config) covers every rank -> top-ranked cohort = all 6 stock observations
    assert cg["top_ranked"]["n"] == 6 and cg["top_ranked"]["mean_return"] == pytest.approx(0.10)
    # SPY/QQQ controls = the per-run benchmark returns
    assert cg["spy"]["n"] == 2 and cg["spy"]["mean_return"] == pytest.approx(0.065)
    assert cg["qqq"]["n"] == 2 and cg["qqq"]["mean_return"] == pytest.approx(0.065)
    # sector-ETF control = XLK (run1+run2) and XLE (run1) for the sectors the top cohort occupies
    assert cg["sector_etf"]["n"] == 3 and cg["sector_etf"]["mean_return"] == pytest.approx((0.04 + 0.05 - 0.02) / 3)
    # random same-sector cohort: numeric, with n, and labelled
    assert cg["random_same_sector"]["n"] >= 1
    assert cg["random_same_sector"]["mean_return"] is not None
    assert "random" in cg["random_same_sector"]["label"].lower()


def test_aggregates_group_by_stored_bucket_not_rescored(tmp_path):
    """Single-source: by-bucket grouping uses the STORED leadership_bucket VERBATIM — never re-derived
    from the score. A row whose stored bucket contradicts its score is grouped by the STORED bucket."""
    engine = make_engine(f"sqlite:///{tmp_path / 'verbatim.db'}")
    create_db_and_tables(engine)
    H = 20
    with Session(engine) as session:
        run = _add_run(session, date(2025, 3, 3), "Risk-on")
        # X: a 95-score row STORED as bucket E ; Y: a 5-score row STORED as bucket A (deliberately inverted)
        _add_result(session, run.id, "X", "E", "Avoid", "Technology", 2, lead_score=95.0)
        _add_result(session, run.id, "Y", "A", "Actionable", "Technology", 1, lead_score=5.0)
        _add_fr(session, run.id, "X", H, 0.11)
        _add_fr(session, run.id, "Y", H, 0.22)
        session.commit()
        agg = compute_forward_aggregates(session, H, load_config())

    by_bucket = {r["bucket"]: r for r in agg["by_bucket"]}
    # grouped by STORED bucket: E has X (0.11), A has Y (0.22) — the OPPOSITE of a score re-bucketing
    assert by_bucket["E"]["n"] == 1 and by_bucket["E"]["mean_return"] == pytest.approx(0.11)
    assert by_bucket["A"]["n"] == 1 and by_bucket["A"]["mean_return"] == pytest.approx(0.22)


@pytest.fixture()
def vcp_aggregates_engine(tmp_path):
    """A hand-built run with known forward returns split across the VCP / non-VCP cohorts at horizon
    H, so the by_vcp means are exact by construction (AAA,BBB flagged VCP; CCC non-VCP)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'vcp_agg.db'}")
    create_db_and_tables(engine)
    H = 20
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), "Risk-on")
        _add_result(session, r1.id, "AAA", "A", "Breakout-watch", "Technology", 1, is_vcp=True)
        _add_result(session, r1.id, "BBB", "B", "Pullback-watch", "Technology", 2, is_vcp=True)
        _add_result(session, r1.id, "CCC", "C", "Avoid", "Technology", 3, is_vcp=False)
        for sym, ret in [("AAA", 0.20), ("BBB", 0.10), ("CCC", -0.06), ("SPY", 0.05), ("QQQ", 0.06)]:
            _add_fr(session, r1.id, sym, H, ret)
        session.commit()
    return engine, H


def test_aggregates_by_vcp_exact(vcp_aggregates_engine):
    """by_vcp groups the STORED `is_vcp` flag VERBATIM: the VCP cohort (AAA,BBB) and the non-VCP
    cohort (CCC), each with an exact mean + n; both cohorts always present and labelled."""
    engine, H = vcp_aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    by_vcp = {r["vcp"]: r for r in agg["by_vcp"]}
    assert set(by_vcp) == {"VCP", "non-VCP"}
    assert by_vcp["VCP"]["n"] == 2 and by_vcp["VCP"]["mean_return"] == pytest.approx(0.15)   # (0.20+0.10)/2
    assert by_vcp["non-VCP"]["n"] == 1 and by_vcp["non-VCP"]["mean_return"] == pytest.approx(-0.06)


def test_aggregates_by_vcp_empty_cohort_is_na_padded(aggregates_engine):
    """No fabrication: the base fixture flags NO VCP names, so the VCP cohort is padded n=0 / mean
    None while non-VCP carries all observations — an honest NA, never a fabricated 0%."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    by_vcp = {r["vcp"]: r for r in agg["by_vcp"]}
    assert set(by_vcp) == {"VCP", "non-VCP"}
    assert by_vcp["VCP"]["n"] == 0 and by_vcp["VCP"]["mean_return"] is None
    assert by_vcp["non-VCP"]["n"] == 6  # all six realized observations are non-VCP (default is_vcp=False)


@pytest.fixture()
def new_pattern_aggregates_engine(tmp_path):
    """A hand-built run with known forward returns split across the new-pattern cohorts at horizon H,
    so the by_<name> means are exact by construction. AAA,BBB flag pullback-to-rising-DMA; AAA,CCC flag
    flat-base-breakout (a name may flag MORE than one pattern — the flags are independent)."""
    engine, H = make_engine(f"sqlite:///{tmp_path / 'newpat_agg.db'}"), 20
    create_db_and_tables(engine)
    with Session(engine) as session:
        r1 = _add_run(session, date(2025, 1, 10), "Risk-on")
        _add_result(session, r1.id, "AAA", "A", "Breakout-watch", "Technology", 1,
                    is_pullback_to_rising_dma=True, is_flat_base_breakout=True)
        _add_result(session, r1.id, "BBB", "B", "Pullback-watch", "Technology", 2,
                    is_pullback_to_rising_dma=True, is_flat_base_breakout=False)
        _add_result(session, r1.id, "CCC", "C", "Avoid", "Technology", 3,
                    is_pullback_to_rising_dma=False, is_flat_base_breakout=True)
        for sym, ret in [("AAA", 0.20), ("BBB", 0.10), ("CCC", -0.06), ("SPY", 0.05), ("QQQ", 0.06)]:
            _add_fr(session, r1.id, sym, H, ret)
        session.commit()
    return engine, H


def test_aggregates_by_new_patterns_exact(new_pattern_aggregates_engine):
    """by_<name> groups the STORED `is_<name>` flag VERBATIM (never re-detected): each pattern's flagged
    vs non-flagged cohort, with exact mean + n; both cohorts always present and labelled."""
    engine, H = new_pattern_aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())

    by_pb = {r["pullback_to_rising_dma"]: r for r in agg["by_pullback_to_rising_dma"]}
    assert set(by_pb) == {"Pullback-to-DMA", "non-Pullback"}
    assert by_pb["Pullback-to-DMA"]["n"] == 2 and by_pb["Pullback-to-DMA"]["mean_return"] == pytest.approx(0.15)  # (0.20+0.10)/2
    assert by_pb["non-Pullback"]["n"] == 1 and by_pb["non-Pullback"]["mean_return"] == pytest.approx(-0.06)

    by_fb = {r["flat_base_breakout"]: r for r in agg["by_flat_base_breakout"]}
    assert set(by_fb) == {"Flat-base", "non-Flat-base"}
    assert by_fb["Flat-base"]["n"] == 2 and by_fb["Flat-base"]["mean_return"] == pytest.approx(0.07)  # (0.20-0.06)/2
    assert by_fb["non-Flat-base"]["n"] == 1 and by_fb["non-Flat-base"]["mean_return"] == pytest.approx(0.10)


def test_aggregates_by_new_patterns_empty_cohort_is_na_padded(aggregates_engine):
    """No fabrication: the base fixture flags NEITHER new pattern, so each flagged cohort is padded
    n=0 / mean None while the non-flagged cohort carries all observations — honest NA, never a 0%."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    for key, flagged_label, non_label in [
        ("by_pullback_to_rising_dma", "Pullback-to-DMA", "non-Pullback"),
        ("by_flat_base_breakout", "Flat-base", "non-Flat-base"),
    ]:
        cohorts = {r[key.removeprefix("by_")]: r for r in agg[key]}
        assert set(cohorts) == {flagged_label, non_label}
        assert cohorts[flagged_label]["n"] == 0 and cohorts[flagged_label]["mean_return"] is None
        assert cohorts[non_label]["n"] == 6  # all six realized observations are non-flagged (defaults False)


def test_aggregates_zero_post_bar_run_contributes_n0(aggregates_engine):
    """No fabrication: run3 (no forward returns) contributes nothing — n counts only realized returns."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        # run3 has a result (AAA, bucket A) but NO forward_returns -> it must not inflate any n
        total_n = sum(r["n"] for r in compute_forward_aggregates(session, H, load_config())["by_bucket"])
    assert total_n == 6  # exactly the 6 stocks that HAVE a realized return (run1: 4, run2: 2)


def test_control_group_determinism_same_seed_same_cohort(aggregates_engine):
    """Control-group determinism: same config seed -> identical random same-sector cohort across two
    independent computations (reproducible across calls / a simulated restart)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        a = compute_forward_aggregates(session, H, cfg)
    with Session(engine) as session:  # fresh session == a simulated restart
        b = compute_forward_aggregates(session, H, cfg)
    rng_a = next(c for c in a["control_group"] if c["key"] == "random_same_sector")
    rng_b = next(c for c in b["control_group"] if c["key"] == "random_same_sector")
    assert rng_a["n"] == rng_b["n"]
    assert rng_a["mean_return"] == rng_b["mean_return"]


def test_aggregates_carry_survivorship_label_and_min_sample(aggregates_engine):
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    assert "survivorship" in agg["survivorship_bias"].lower()
    assert agg["min_sample"] == load_config().walk_forward.min_sample
    assert agg["horizon"] == H and H in agg["horizons"]


# ==================================================================================================
# As-of scoping (iter-17, J-09/J-10) — the aggregate over an EXPANDING WINDOW of snapshots dated <= D.
# The cutoff filters on the RUN's `ScannerRun.asof_date` (run1=2025-01-10 Risk-on, run2=2024-07-10
# Risk-off; run3 has no forward returns). The membership filter is the ONLY change — grouping/excess/
# control-group/attribution math is untouched and `as_of=None` stays byte-identical to all-history.
# ==================================================================================================
def test_aggregates_as_of_pools_only_runs_on_or_before_cutoff(aggregates_engine):
    """as_of=D pools ONLY runs whose ScannerRun.asof_date <= D. At D = run2's date (2024-07-10) only
    run2's two observations contribute (AAA 0.30 bucket B, EEE 0.10 bucket E); run1 (2025-01-10 > D) is
    excluded entirely — the keystone expanding-window walk-forward semantics (J-09)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        early = compute_forward_aggregates(session, H, cfg, as_of=date(2024, 7, 10))
    assert early["n_runs"] == 1
    assert early["overall"]["n"] == 2
    assert early["overall"]["mean_return"] == pytest.approx(0.20)  # mean(0.30, 0.10)
    by_bucket = {r["bucket"]: r for r in early["by_bucket"]}
    assert by_bucket["B"]["n"] == 1 and by_bucket["B"]["mean_return"] == pytest.approx(0.30)
    assert by_bucket["E"]["n"] == 1 and by_bucket["E"]["mean_return"] == pytest.approx(0.10)
    # run1's A-bucket names (run dated 2025-01-10 > D) must NOT leak in
    assert by_bucket["A"]["n"] == 0 and by_bucket["A"]["mean_return"] is None


def test_aggregates_as_of_sample_grows_toward_latest(aggregates_engine):
    """The sample size is non-decreasing toward the latest date: n at an early D (run2 only) is strictly
    LESS than n at a later D that also admits run1 (J-09 'move the date earlier → n drops')."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        early = compute_forward_aggregates(session, H, cfg, as_of=date(2024, 7, 10))   # run2 only
        later = compute_forward_aggregates(session, H, cfg, as_of=date(2025, 1, 10))   # run1 + run2
    assert early["overall"]["n"] == 2 and later["overall"]["n"] == 6
    assert early["overall"]["n"] < later["overall"]["n"]


def test_aggregates_as_of_none_equals_latest_equals_all_history(aggregates_engine):
    """as_of=None is BYTE-IDENTICAL to today's all-history result AND equals as_of=latest (a date on or
    after every run) AND a far-future date — with no run dated > latest, all coincide (DoD:
    as_of=None == as_of=latest == all-history, byte-identical top-level + per-group n/means)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        all_history = compute_forward_aggregates(session, H, cfg)                         # no filter
        at_latest = compute_forward_aggregates(session, H, cfg, as_of=date(2025, 1, 10))  # latest run
        far_future = compute_forward_aggregates(session, H, cfg, as_of=date(2099, 1, 1))  # >> latest
    assert all_history == at_latest == far_future  # byte-identical dicts (incl. control-group draws)


def test_aggregates_as_of_no_future_run_leak(aggregates_engine):
    """No >D leak (critical anti-goal): a run dated strictly AFTER D contributes 0 to EVERY group. At D
    one day before run1's date, run1 (2025-01-10) is fully excluded — its Risk-on regime and all its
    observations are absent from overall / by_regime / control_group; only run2 (Risk-off) remains."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        before_run1 = compute_forward_aggregates(session, H, cfg, as_of=date(2025, 1, 9))
    assert before_run1["overall"]["n"] == 2
    assert {r["regime"] for r in before_run1["by_regime"]} == {"Risk-off"}  # run1's Risk-on did not leak
    cg = {c["key"]: c for c in before_run1["control_group"]}
    assert cg["top_ranked"]["n"] == 2  # run2's 2 obs only — no leak from the later run


def test_aggregates_as_of_before_all_runs_is_honest_empty(aggregates_engine):
    """An as-of date before EVERY run yields an empty, honest-NA aggregate — n=0 everywhere, no
    fabricated rows; the A-E bucket table is still padded at n=0 / mean None (never a fabricated 0%)."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        empty = compute_forward_aggregates(session, H, cfg, as_of=date(2000, 1, 1))
    assert empty["n_runs"] == 0
    assert empty["overall"]["n"] == 0 and empty["overall"]["mean_return"] is None
    assert [r["bucket"] for r in empty["by_bucket"]] == ["A", "B", "C", "D", "E"]
    assert all(r["n"] == 0 and r["mean_return"] is None for r in empty["by_bucket"])


def test_aggregates_as_of_scoped_consistency_invariant_relocated(aggregates_engine):
    """Relocated consistency invariant (iter-2 lesson — the System Health invariant MOVED to the
    as-of-scoped aggregate, not deleted): for the as-of-scoped pool the attribution distribution mean
    EQUALS overall.mean_return and the by-sector / by-rank-band sample sizes each sum to overall.n —
    the slices are the SAME filtered observations grouped, never a recomputed return."""
    engine, H = aggregates_engine
    cfg = load_config()
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, cfg, as_of=date(2024, 7, 10))
    attr, overall = agg["attribution"], agg["overall"]
    assert overall["n"] == 2  # run2 only — the slices below must reflect exactly this filtered pool
    assert attr["distribution"]["mean_return"] == pytest.approx(overall["mean_return"])
    assert attr["distribution"]["n"] == overall["n"]
    assert sum(r["n"] for r in attr["by_sector"]) == overall["n"]
    assert sum(r["n"] for r in attr["by_rank_band"]) == overall["n"]


# ==================================================================================================
# walk-forward as-of date set (real seed trading calendar; no run_scan -> cheap)
# ==================================================================================================
def test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon(loaded_engine, config):
    """The cadence as-of set is non-empty, strictly ascending, all real trading days, all far enough
    before the latest date to leave >= max(horizons) post-snapshot bars, and within ~history_years."""
    with Session(loaded_engine) as session:
        asof = walk_forward_asof_dates(session, config)
        latest = latest_data_date(session)
        spy_days = [b.date for b in bars_asof(session, config.etfs.index[0], latest)]

    assert asof, "expected a non-empty walk-forward as-of set on the seed"
    assert asof == sorted(set(asof))  # ascending, de-duplicated
    trading = set(spy_days)
    assert all(d in trading for d in asof)  # only real trading days (no fabricated dates)

    max_h = max(config.walk_forward.horizons)
    index_of = {d: i for i, d in enumerate(spy_days)}
    for d in asof:
        assert len(spy_days) - 1 - index_of[d] >= max_h  # >= max_h post-snapshot bars for every run
    # within (a little slack on) the configured look-back window
    span_years = (latest - asof[0]).days / 365.0
    assert span_years <= config.walk_forward.history_years + 1


# ==================================================================================================
# Backfill integration — INSERT-only, idempotent, snapshot never mutated (reduced cadence, real seed)
# ==================================================================================================
def _fast_cfg():
    """The real config with a REDUCED walk-forward look-back so the backfill scans only a few cadence
    dates (keeps this integration proof fast); everything else (universe, engines) is real."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"history_years": 1, "asof_cadence": "quarterly"})
    return cfg.model_copy(update={"walk_forward": wf})


def _child_fingerprint(session: Session, run_id: int) -> dict:
    """Content-only fingerprint of a run's snapshot children (excludes PKs/FKs) — identical before vs
    after a backfill proves the snapshot was not mutated."""
    results = session.exec(
        select(ScannerResult).where(ScannerResult.run_id == run_id).order_by(ScannerResult.rank)
    ).all()
    sectors = session.exec(select(SectorScoreRow).where(SectorScoreRow.run_id == run_id)).all()
    themes = session.exec(select(ThemeScoreRow).where(ThemeScoreRow.run_id == run_id)).all()
    return {
        "results": [r.record_json for r in results],
        "sector_count": len(sectors),
        "theme_count": len(themes),
        "lead_by_ticker": {r.ticker: r.leadership_score for r in results},
    }


@pytest.fixture(scope="module")
def backfilled_engine(tmp_path_factory):
    """Load the seed, capture a pre-existing run's fingerprint, then run the reduced backfill ONCE."""
    cfg = _fast_cfg()
    db_path = tmp_path_factory.mktemp("backfill_db") / "bf.db"
    engine = make_engine(f"sqlite:///{db_path}")
    create_db_and_tables(engine)
    load_seed(engine, cfg)

    # a pre-existing snapshot (the latest data date) created BEFORE any forward returns exist
    with Session(engine) as session:
        latest = latest_data_date(session)
        pre_run = run_scan(session, latest, cfg)
        pre_id = pre_run.id
        before = {
            "fingerprint": _child_fingerprint(session, pre_id),
            "n_runs": session.scalar(select(func.count()).select_from(ScannerRun)),
            "n_results": session.scalar(select(func.count()).select_from(ScannerResult)),
            "n_sector_scores": session.scalar(select(func.count()).select_from(SectorScoreRow)),
            "n_theme_scores": session.scalar(select(func.count()).select_from(ThemeScoreRow)),
            "n_forward_returns": session.scalar(select(func.count()).select_from(ForwardReturn)),
        }

    first = backfill_forward_returns(engine, cfg)
    return engine, cfg, latest, pre_id, before, first


def test_backfill_inserts_forward_returns_without_mutating_snapshot(backfilled_engine):
    """Snapshots-immutable: the backfill only INSERTs forward_returns — every pre-existing snapshot row
    is untouched (counts unchanged for runs/results that pre-existed; the pre-existing run's child
    fingerprint is byte-identical before vs after)."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    assert before["n_forward_returns"] == 0  # none existed before the backfill
    assert first["rows_inserted"] > 0  # the backfill inserted realized returns

    with Session(engine) as session:
        after_fp = _child_fingerprint(session, pre_id)
        n_fr = session.scalar(select(func.count()).select_from(ForwardReturn))
    assert after_fp == before["fingerprint"]  # the pre-existing snapshot was NOT mutated
    assert n_fr == first["rows_inserted"]


def test_backfill_is_idempotent(backfilled_engine):
    """A second backfill inserts ZERO new forward_returns and creates no new runs (idempotent)."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    with Session(engine) as session:
        runs_before = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_before = session.scalar(select(func.count()).select_from(ForwardReturn))

    second = backfill_forward_returns(engine, cfg)

    with Session(engine) as session:
        runs_after = session.scalar(select(func.count()).select_from(ScannerRun))
        fr_after = session.scalar(select(func.count()).select_from(ForwardReturn))
    assert second["rows_inserted"] == 0
    assert runs_after == runs_before
    assert fr_after == fr_before


def test_backfill_populates_mae_mfe_within_band(backfilled_engine):
    """iter-14 (J-29): every INSERTed forward return carries a non-None mae/mfe (computed ONCE with the
    realized return on the SAME post_bars, sharing forward_return's NA gate), and the realized close-to-
    close return lies within the [mae, mfe] band — proving the excursions are stored, lookahead-free, and
    consistent with the realized return (mae = adverse <= mfe = favorable)."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    with Session(engine) as session:
        rows = session.exec(select(ForwardReturn)).all()
    assert rows  # the backfill inserted realized returns
    # populated on fresh INSERT — a row exists iff realized_return does, so mae/mfe are never NULL here
    assert all(r.mae is not None and r.mfe is not None for r in rows)
    for r in rows:
        assert r.mae <= r.realized_return <= r.mfe  # close-to-close return within the excursion band
        assert r.mae <= r.mfe  # adverse (min-low) <= favorable (max-high)


def test_backfill_populates_max_drawdown_same_na_gate(backfilled_engine):
    """iter-27 (J-86): every INSERTed forward return carries a non-None max_drawdown (computed ONCE with
    the realized return on the SAME post_bars, sharing forward_return's NA gate — a row's max_drawdown is
    non-None iff realized_return is), the drawdown is <= 0 (a true peak-to-trough drop), and it is at
    least as adverse as the MAE (MDD <= MAE <= 0, since the drawdown denominator is the running peak >=
    the entry the MAE divides by). Proves the column is stored, lookahead-free, and honest."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    with Session(engine) as session:
        rows = session.exec(select(ForwardReturn)).all()
    assert rows  # the backfill inserted realized returns
    # populated on fresh INSERT — a row exists iff realized_return does, so max_drawdown is never NULL here
    assert all(r.max_drawdown is not None for r in rows)
    for r in rows:
        assert r.max_drawdown <= 1e-12  # <= 0 (true peak-to-trough drop; tolerate float noise at 0)
        assert r.max_drawdown <= r.mae + 1e-12  # MDD is at least as adverse as the MAE


def test_backfill_latest_run_has_zero_post_bars(backfilled_engine):
    """No fabrication: the latest seed-date run has no post-snapshot bar, so it gets NO forward_returns
    (the natural n=0 demonstration) — never a fabricated 0%."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    with Session(engine) as session:
        latest_run = session.exec(select(ScannerRun).where(ScannerRun.asof_date == latest)).one()
        n_fr_latest = session.scalar(
            select(func.count()).select_from(ForwardReturn).where(ForwardReturn.run_id == latest_run.id)
        )
    assert n_fr_latest == 0


# ==================================================================================================
# Return attribution (J-19) — four READ-ONLY slices derived from the SAME stored stock_obs
# ==================================================================================================
def test_attribution_consistency_with_aggregate(aggregates_engine):
    """Read-only consistency (the critical anti-goal): the attribution distribution mean EQUALS the
    existing `overall.mean_return`, and the by-sector / by-rank-band sample sizes each sum to
    `overall.n` — the slices are the SAME observations grouped, never a recomputed return."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        agg = compute_forward_aggregates(session, H, load_config())
    attr, overall = agg["attribution"], agg["overall"]
    assert attr["distribution"]["mean_return"] == pytest.approx(overall["mean_return"])
    assert attr["distribution"]["n"] == overall["n"]
    assert sum(r["n"] for r in attr["by_sector"]) == overall["n"]
    assert sum(r["n"] for r in attr["by_rank_band"]) == overall["n"]


def test_attribution_distribution_exact(aggregates_engine):
    """The distribution panel is exact on the hand fixture: mean, median, hit-rate (% positive), and
    dispersion (sample stdev), with n — over the SAME six observed returns as the aggregate."""
    engine, H = aggregates_engine
    observed = [0.10, 0.20, 0.00, -0.10, 0.30, 0.10]  # the six realized stock returns at H
    with Session(engine) as session:
        dist = compute_forward_aggregates(session, H, load_config())["attribution"]["distribution"]
    assert dist["n"] == 6
    assert dist["mean_return"] == pytest.approx(0.10)
    assert dist["median"] == pytest.approx(0.10)
    assert dist["pct_positive"] == pytest.approx(4 / 6)  # 0.10,0.20,0.30,0.10 > 0 (0.00 / -0.10 are not)
    assert dist["dispersion"] == pytest.approx(stdev(observed))


def test_attribution_per_stock_named_contributors_and_detractors(aggregates_engine):
    """Per-stock: each NAMED ticker's mean realized return + n + stored sector over the same
    observations; contributors are the highest means, detractors the lowest. AAA aggregates its two
    runs to +0.20 (n=2); DDD is the sole detractor at -0.10."""
    engine, H = aggregates_engine
    with Session(engine) as session:
        per_stock = compute_forward_aggregates(session, H, load_config())["attribution"]["per_stock"]
    contributors, detractors = per_stock["contributors"], per_stock["detractors"]

    aaa = next(r for r in contributors if r["ticker"] == "AAA")
    assert aaa["mean_return"] == pytest.approx(0.20) and aaa["n"] == 2 and aaa["sector"] == "Technology"
    assert contributors[0]["ticker"] == "AAA" and contributors[0]["mean_return"] == pytest.approx(0.20)
    assert detractors[0]["ticker"] == "DDD" and detractors[0]["mean_return"] == pytest.approx(-0.10)
    # contributors are ordered high->low, detractors low->high (robust to tie order)
    assert [r["mean_return"] for r in contributors] == sorted(
        (r["mean_return"] for r in contributors), reverse=True
    )
    assert [r["mean_return"] for r in detractors] == sorted(r["mean_return"] for r in detractors)


def test_attribution_top_contributors_k_controls_list_length(aggregates_engine):
    """No magic numbers: the list length is `config.walk_forward.attribution.top_contributors_k`, not a
    code literal — shrinking it shrinks the contributor / detractor lists."""
    engine, H = aggregates_engine
    cfg = load_config()
    attr_cfg = cfg.walk_forward.attribution.model_copy(update={"top_contributors_k": 2})
    cfg2 = cfg.model_copy(
        update={"walk_forward": cfg.walk_forward.model_copy(update={"attribution": attr_cfg})}
    )
    with Session(engine) as session:
        per_stock = compute_forward_aggregates(session, H, cfg2)["attribution"]["per_stock"]
    assert len(per_stock["contributors"]) == 2 and len(per_stock["detractors"]) == 2


def test_attribution_rank_bands_come_from_config(aggregates_engine):
    """No magic numbers: the rank-band labels / edges come from config — redefining the bands changes
    both the emitted labels and which observations fall in each (no band edge literal in calc code)."""
    from app.config import RankBand

    engine, H = aggregates_engine
    cfg = load_config()
    bands = [RankBand(label="1–2", min=1, max=2), RankBand(label="3+", min=3, max=None)]
    attr_cfg = cfg.walk_forward.attribution.model_copy(update={"rank_bands": bands})
    cfg2 = cfg.model_copy(
        update={"walk_forward": cfg.walk_forward.model_copy(update={"attribution": attr_cfg})}
    )
    with Session(engine) as session:
        by_rank_band = compute_forward_aggregates(session, H, cfg2)["attribution"]["by_rank_band"]
    assert [r["rank_band"] for r in by_rank_band] == ["1–2", "3+"]
    band = {r["rank_band"]: r for r in by_rank_band}
    # ranks 1,2 -> "1–2": AAA(run1)=0.10, BBB=0.20, AAA(run2)=0.30, EEE=0.10
    assert band["1–2"]["n"] == 4
    assert band["1–2"]["mean_return"] == pytest.approx((0.10 + 0.20 + 0.30 + 0.10) / 4)
    # ranks 3,4 -> "3+": CCC=0.00, DDD=-0.10
    assert band["3+"]["n"] == 2 and band["3+"]["mean_return"] == pytest.approx(-0.05)


def test_attribution_rank_band_with_no_members_is_padded(aggregates_engine):
    """A rank band with no members is still emitted (padded n=0 / mean None) so the table is complete.
    On the default config bands every fixture rank (1..4) falls in the first band; the higher bands pad."""
    engine, H = aggregates_engine
    cfg = load_config()
    labels = [b.label for b in cfg.walk_forward.attribution.rank_bands]
    with Session(engine) as session:
        by_rank_band = compute_forward_aggregates(session, H, cfg)["attribution"]["by_rank_band"]
    assert [r["rank_band"] for r in by_rank_band] == labels  # config order, complete
    band = {r["rank_band"]: r for r in by_rank_band}
    assert band[labels[0]]["n"] == 6 and band[labels[0]]["mean_return"] == pytest.approx(0.10)
    for lbl in labels[1:]:
        assert band[lbl]["n"] == 0 and band[lbl]["mean_return"] is None


def test_attribution_empty_observations_are_all_na():
    """Honesty: empty observations -> every slice NA with n=0 (no fabricated 0%). by_rank_band stays
    padded (every config band present at n=0); by_sector (non-padded) is empty."""
    from app.engine.forward_testing import _attribution_slices

    cfg = load_config()
    attr = _attribution_slices([], cfg)
    assert attr["per_stock"]["contributors"] == [] and attr["per_stock"]["detractors"] == []
    assert attr["distribution"] == {
        "mean_return": None, "median": None, "pct_positive": None, "dispersion": None, "n": 0
    }
    assert attr["by_sector"] == []  # pad=False -> no rows when there is nothing to group
    assert [r["rank_band"] for r in attr["by_rank_band"]] == [
        b.label for b in cfg.walk_forward.attribution.rank_bands
    ]
    assert all(r["n"] == 0 and r["mean_return"] is None for r in attr["by_rank_band"])


def test_attribution_single_observation_dispersion_is_null():
    """A single-observation slice has no defined standard deviation -> dispersion null (no spurious 0
    stdev); mean / median equal the single value and the hit-rate is 1.0."""
    from app.engine.forward_testing import _attribution_slices

    dist = _attribution_slices(
        [{"ticker": "AAA", "return": 0.05, "sector": "Technology", "rank": 1}], load_config()
    )["distribution"]
    assert dist["n"] == 1
    assert dist["mean_return"] == pytest.approx(0.05) and dist["median"] == pytest.approx(0.05)
    assert dist["pct_positive"] == pytest.approx(1.0)
    assert dist["dispersion"] is None


def test_attribution_is_pure_over_passed_observations_no_new_query():
    """Read-only / no new query (the critical anti-goal, structural proof): `_attribution_slices` is a
    pure function of the ALREADY-BUILT `stock_obs` + cfg — it takes NO Session, so it can issue no
    forward_returns / price-bar query. The same observation list that feeds the aggregate feeds the
    slices: no second formula, no second data source."""
    import inspect

    from app.engine.forward_testing import _attribution_slices

    assert set(inspect.signature(_attribution_slices).parameters) == {"stock_obs", "cfg"}
    attr = _attribution_slices(
        [{"ticker": "AAA", "return": 0.10, "sector": "Technology", "rank": 1}], load_config()
    )
    assert attr["distribution"]["n"] == 1  # produced from a hand list with no DB access at all


def test_stored_scores_identical_with_and_without_forward_returns(backfilled_engine):
    """No-lookahead (forward never feeds back): the latest run's stored Leadership scores are byte-
    identical to a fresh score_stocks(latest) computed AFTER forward returns exist — so persisting
    forward returns cannot have altered (fed back into) any as-of score."""
    engine, cfg, latest, pre_id, before, first = backfilled_engine
    from app.engine.scoring import score_stocks

    with Session(engine) as session:
        stored = {
            r.ticker: r.leadership_score
            for r in session.exec(select(ScannerResult).where(ScannerResult.run_id == pre_id)).all()
        }
        live_now = {row["ticker"]: row["leadership"]["score"] for row in score_stocks(session, latest, cfg)["rows"]}
    assert stored == live_now  # the snapshot's scores never changed when forward returns landed
    # and the pre-backfill fingerprint's scores match too (the definitive before/after equality)
    assert stored == before["fingerprint"]["lead_by_ticker"]


# ==================================================================================================
# _claim_samples_kwargs — pure claim-selector -> compute_samples kwarg translation (iter-41, J-25)
# ==================================================================================================
def test_claim_samples_kwargs_factor_claim():
    claim = {
        "decile": 10, "direction": "positive", "factor": "vcp_contraction", "horizon": 20,
        "kind": "factor", "slice_kind": "decile",
    }
    assert _claim_samples_kwargs(claim) == {"factor_key": "vcp_contraction", "slice_kind": "decile", "decile": 10}


def test_claim_samples_kwargs_combination_claim_parses_condition_and_renames_cohort():
    # the EXACT shape of the real promoted composite claim in certified-claims.jsonl.
    claim = {
        "cohort": "composite",
        "condition": ["rs_spy_3m:top:quintile", "high_proximity:top:tertile"],
        "direction": "positive", "horizon": 20, "kind": "combination", "ledger": "canonical",
    }
    assert _claim_samples_kwargs(claim) == {
        "cohort_kind": "composite",
        "conditions": [
            {"factor": "rs_spy_3m", "side": "top", "quantile": "quintile"},
            {"factor": "high_proximity", "side": "top", "quantile": "tertile"},
        ],
    }


def test_claim_samples_kwargs_event_study_claim():
    # the EXACT shape of the real Breakout-watch x Risk-on promoted claim in certified-claims.jsonl.
    claim = {
        "direction": "positive", "horizon": 20, "kind": "event-study", "regime": "Risk-on",
        "slice_kind": "regime", "subject": "Breakout-watch", "view": "pooled",
    }
    assert _claim_samples_kwargs(claim) == {
        "subject_key": "Breakout-watch", "slice_kind": "regime", "regime": "Risk-on", "view": "pooled",
    }


def test_claim_samples_kwargs_malformed_condition_returns_none():
    claim = {"kind": "combination", "cohort": "composite", "condition": ["not-three-parts"], "horizon": 20}
    assert _claim_samples_kwargs(claim) is None


def test_claim_samples_kwargs_ignores_non_selector_claim_fields():
    """`direction` / `signal` / `ledger` / `horizon` / `kind` are NOT selector keys (they are handled
    separately by the caller) — they must never leak into the compute_samples kwargs dict."""
    claim = {
        "kind": "factor", "factor": "leadership_score", "signal": "leadership_score",
        "slice_kind": "total", "horizon": 20, "direction": "positive",
    }
    assert _claim_samples_kwargs(claim) == {"factor_key": "leadership_score", "slice_kind": "total"}


# ==================================================================================================
# compute_drawdown_expectations — phase-conditional drawdown & dry-spell expectations (iter-41, J-25)
# ==================================================================================================
DD_H = 20  # forward horizon used throughout this fixture (in config.walk_forward.horizons)


def _dd_cfg(min_sample: int = 3, streak_min_n: int = 2):
    """The real config with REDUCED min_sample / streak_min_n floors so a small hand-built fixture can
    exercise both the 'sufficient' and 'insufficient' cells cheaply (mirrors test_research.py's own
    `min_sample`-reduction technique for the identical reason)."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"min_sample": min_sample, "streak_min_n": streak_min_n})
    return cfg.model_copy(update={"walk_forward": wf})


def _add_dd_fr(session, run, symbol, horizon, ret, mdd=None, uw=None, ttr=None):
    """A ForwardReturn row carrying its OWN run's REAL asof_date (unlike the generic `_add_fr` helper
    above, which hardcodes a fixed date for tests that never read `ForwardReturn.asof_date` directly).
    `compute_drawdown_expectations` reads `ForwardReturn.asof_date` verbatim (no ScannerRun join) to key
    its lookup, exactly as the real `_insert_run_forward_returns` INSERT path keeps it in sync with
    `run.asof_date` — this fixture must do the same or the join would silently miss every row."""
    session.add(ForwardReturn(
        run_id=run.id, symbol=symbol, horizon=horizon,
        asof_date=run.asof_date, entry_close=100.0,
        measured_date=run.asof_date + timedelta(days=horizon * 2),
        realized_return=ret, max_drawdown=mdd, underwater_days=uw, time_to_recover_days=ttr,
    ))


# Expansion phase: 4 dates, ticker AAA — fully populated except the 3rd date's time_to_recover_days
# (honest NA, never recovered in-window). Values chosen so median/p90 are exact by construction.
_EXP_DATES = [date(2025, 1, 10), date(2025, 2, 10), date(2025, 3, 10), date(2025, 4, 10)]
_EXP_MDD = [-0.05, -0.10, -0.15, -0.20]
_EXP_UW = [2, 4, 6, 8]
_EXP_TTR = [3, 5, None, 10]
_EXP_RET = [0.01, -0.01, -0.02, 0.03]  # date order pos/neg/neg/pos -> longest negative streak == 2

# Correction phase: 2 dates, tickers BBB/DDD — BBB fully populated, DDD's THREE dry-spell/MDD columns are
# NULL (a live DB not yet rebuilt) so the phase's return-count (both count) and its distribution n (BBB
# only) diverge on purpose — proving the null columns are excluded from those measures, never crashed.
_CORR_DATES = [date(2025, 5, 10), date(2025, 6, 10)]
_CORR_TICKERS = ["BBB", "DDD"]
_CORR_MDD = [-0.30, None]
_CORR_UW = [15, None]
_CORR_TTR = [1, None]
_CORR_RET = [-0.05, -0.08]  # both negative -> a 2-long streak (n=2 dates clears the reduced streak floor)

_UNCLASSIFIED_DATE = date(2025, 7, 10)  # ticker CCC — deliberately ABSENT from the mocked phase map


def _fake_phase_ctx(session=None, as_of=None, config=None):
    """The served `market_phase` timeline, monkeypatched (mirrors test_regime_phase_factor.py /
    test_phase_severity_lab.py's established pattern) so the by-phase join is exact by construction — the
    UNCLASSIFIED date is deliberately absent, mirroring a warm-up-head date with insufficient benchmark
    history (an honest gap, never a fabricated phase)."""
    ctx = {
        _EXP_DATES[0].isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05},
        _EXP_DATES[1].isoformat(): {"phase": "Expansion", "severity": 12.0, "p_bear": 0.05},
        _EXP_DATES[2].isoformat(): {"phase": "Expansion", "severity": 15.0, "p_bear": 0.06},
        _EXP_DATES[3].isoformat(): {"phase": "Expansion", "severity": 11.0, "p_bear": 0.05},
        _CORR_DATES[0].isoformat(): {"phase": "Correction", "severity": 55.0, "p_bear": 0.40},
        _CORR_DATES[1].isoformat(): {"phase": "Correction", "severity": 58.0, "p_bear": 0.42},
    }
    if as_of is None:
        return dict(ctx)
    return {d: v for d, v in ctx.items() if date.fromisoformat(d) <= as_of}


@pytest.fixture()
def dd_expectations_engine(tmp_path, monkeypatch):
    engine = make_engine(f"sqlite:///{tmp_path / 'dd_expectations.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        for d, mdd, uw, ttr, ret in zip(_EXP_DATES, _EXP_MDD, _EXP_UW, _EXP_TTR, _EXP_RET):
            run = _add_run(session, d, "Risk-on")
            _add_result(session, run.id, "AAA", "A", "Actionable", "Technology", 1)
            _add_dd_fr(session, run, "AAA", DD_H, ret, mdd=mdd, uw=uw, ttr=ttr)
        for d, ticker, mdd, uw, ttr, ret in zip(
            _CORR_DATES, _CORR_TICKERS, _CORR_MDD, _CORR_UW, _CORR_TTR, _CORR_RET
        ):
            run = _add_run(session, d, "Risk-off")
            _add_result(session, run.id, ticker, "C", "Avoid", "Technology", 1)
            _add_dd_fr(session, run, ticker, DD_H, ret, mdd=mdd, uw=uw, ttr=ttr)
        # a valid observation with NO causal phase entry (excluded, never fabricated into a bucket).
        run = _add_run(session, _UNCLASSIFIED_DATE, "Risk-on")
        _add_result(session, run.id, "CCC", "B", "Breakout-watch", "Technology", 1)
        _add_dd_fr(session, run, "CCC", DD_H, 0.10, mdd=-0.02, uw=1, ttr=2)
        session.commit()
    monkeypatch.setattr(market_phase, "phase_context_by_date", _fake_phase_ctx)
    return engine


_FACTOR_CLAIM = {
    "kind": "factor", "factor": "leadership_score", "slice_kind": "total", "horizon": DD_H,
    "direction": "positive",
}


def _by_phase(payload, phase):
    return next(row for row in payload["by_phase"] if row["phase"] == phase)


def test_compute_drawdown_expectations_exact_per_phase_median_p90_n(dd_expectations_engine):
    """Expansion (n=4, >= the reduced floor): exact median/p90 for max_drawdown / underwater_days (both
    fully populated) and time_to_recover_days (3 of 4 populated — the 3rd date's None is excluded from
    ITS OWN n, honest NA) — hand-computed via the SAME linear-interpolation percentile the risk-budget
    gap profile uses (J-24). The loss streak is counted at the walk-forward cadence."""
    with Session(dd_expectations_engine) as session:
        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
    assert payload is not None
    assert payload["horizon"] == DD_H
    assert payload["min_sample"] == 3
    assert payload["streak_min_n"] == 2
    assert payload["survivorship_bias"]  # non-empty, the shared module-level caveat constant
    assert payload["method_note"]

    exp = _by_phase(payload, "Expansion")
    assert exp["n"] == 4
    mdd = exp["max_drawdown"]
    assert mdd["insufficient"] is False and mdd["n"] == 4
    assert mdd["median"] == pytest.approx(-0.125)
    assert mdd["p90"] == pytest.approx(-0.065)
    uw = exp["underwater_days"]
    assert uw["insufficient"] is False and uw["n"] == 4
    assert uw["median"] == pytest.approx(5)
    assert uw["p90"] == pytest.approx(7.4)
    ttr = exp["time_to_recover_days"]
    assert ttr["insufficient"] is False and ttr["n"] == 3  # the None (3rd date) excluded from ITS OWN n
    assert ttr["median"] == pytest.approx(5)
    assert ttr["p90"] == pytest.approx(9)
    streak = exp["loss_streak"]
    assert streak["insufficient"] is False and streak["n"] == 4
    assert streak["value"] == 2  # d2,d3 (both negative) are the longest consecutive run


def test_compute_drawdown_expectations_insufficient_phase_and_null_columns_excluded(dd_expectations_engine):
    """Correction (n=2 returns, >= the streak floor but < the distribution floor): the phase-level `n`
    counts BOTH dates (every observation with a realized return), but max_drawdown/underwater_days/
    time_to_recover_days each carry n=1 (only BBB — DDD's stored dry-spell/MDD columns are NULL,
    simulating a live DB not yet rebuilt) and read 'insufficient' — never crash, never a fabricated
    distribution over the missing values. The loss-streak floor is satisfied independently of the
    distribution floor (the two floors are genuinely separate honesty gates)."""
    with Session(dd_expectations_engine) as session:
        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
    corr = _by_phase(payload, "Correction")
    assert corr["n"] == 2  # both BBB and DDD counted (each had a realized return)
    for measure in ("max_drawdown", "underwater_days", "time_to_recover_days"):
        cell = corr[measure]
        assert cell["n"] == 1 and cell["insufficient"] is True
        assert cell["median"] is None and cell["p90"] is None
    streak = corr["loss_streak"]
    assert streak["n"] == 2 and streak["insufficient"] is False
    assert streak["value"] == 2  # both dates negative -> a 2-long streak


def test_compute_drawdown_expectations_every_configured_phase_padded(dd_expectations_engine):
    """Every configured `market_phase.labels` value is emitted, in config order, even at n=0 (a cohort
    that never saw Pullback/Bear/Recovery still discloses that honestly rather than omitting the row)."""
    with Session(dd_expectations_engine) as session:
        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
    assert [row["phase"] for row in payload["by_phase"]] == [
        "Expansion", "Pullback", "Correction", "Bear", "Recovery",
    ]
    for phase in ("Pullback", "Bear", "Recovery"):
        row = _by_phase(payload, phase)
        assert row["n"] == 0
        for measure in ("max_drawdown", "underwater_days", "time_to_recover_days"):
            assert row[measure] == {"median": None, "p90": None, "n": 0, "insufficient": True}
        assert row["loss_streak"] == {"value": None, "n": 0, "insufficient": True}


def test_compute_drawdown_expectations_unclassified_date_excluded_never_fabricated(dd_expectations_engine):
    """A valid observation whose snapshot date carries NO causal phase entry (mirrors a warm-up-head date
    with insufficient benchmark history) is EXCLUDED from every phase bucket — never fabricated into one,
    and never silently inflates a phase's n."""
    with Session(dd_expectations_engine) as session:
        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
    total_classified = sum(row["n"] for row in payload["by_phase"])
    assert total_classified == 6  # 4 Expansion + 2 Correction; the unclassified CCC date is excluded


def test_compute_drawdown_expectations_max_drawdown_reused_verbatim_not_recomputed(dd_expectations_engine):
    """The served max_drawdown values are the STORED figures read VERBATIM — proven structurally: this
    fixture carries NO `DailyPrice` bar at all, so recomputing a drawdown from bars would be impossible
    (no price series exists to read). The served Expansion median exactly matches the hand-set stored
    values, confirming a pure read, never a recompute."""
    with Session(dd_expectations_engine) as session:
        assert session.scalar(select(func.count()).select_from(DailyPrice)) == 0
        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
    assert _by_phase(payload, "Expansion")["max_drawdown"]["median"] == pytest.approx(-0.125)


def test_compute_drawdown_expectations_none_when_horizon_outside_underwater_horizons(dd_expectations_engine):
    """A claim's horizon outside the configured `underwater_horizons` scope yields no panel — an honest
    scope gate, never a crash or a cross-horizon-mismatched figure."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"underwater_horizons": [1, 5]})  # 20 excluded
    cfg = cfg.model_copy(update={"walk_forward": wf})
    with Session(dd_expectations_engine) as session:
        assert compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg) is None


def test_compute_drawdown_expectations_none_when_cohort_unresolvable(dd_expectations_engine):
    """An unknown factor key (`compute_samples` raises ValueError) resolves to None — never a 500, never
    a crash into the caller."""
    claim = {**_FACTOR_CLAIM, "factor": "does_not_exist_factor"}
    with Session(dd_expectations_engine) as session:
        assert compute_drawdown_expectations(session, claim, _dd_cfg()) is None


def test_compute_drawdown_expectations_none_when_zero_observations(tmp_path):
    """A validly-resolvable cohort with zero matching observations (no stored ForwardReturn at this
    claim's horizon) is an honest empty panel (None), never a fabricated one."""
    engine = make_engine(f"sqlite:///{tmp_path / 'empty_cohort.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        run = _add_run(session, date(2025, 1, 10), "Risk-on")
        _add_result(session, run.id, "AAA", "A", "Actionable", "Technology", 1)
        _add_dd_fr(session, run, "AAA", 5, 0.02)  # only horizon 5 stored; the claim below asks for h=20
        session.commit()
    with Session(engine) as session:
        assert compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg()) is None


def test_compute_drawdown_expectations_loss_streak_cadence_not_daily_double_count(tmp_path, monkeypatch):
    """B-205 trap: multiple tickers sharing ONE snapshot date must collapse to a SINGLE cadence point (the
    cohort's MEAN return that date) before the streak is counted — never one point per ticker, which would
    fabricate a longer 'streak' than the cohort actually experienced as a single period."""
    engine = make_engine(f"sqlite:///{tmp_path / 'streak.db'}")
    create_db_and_tables(engine)
    dates = [date(2025, 1, 10), date(2025, 2, 10), date(2025, 3, 10)]
    # date1: all 3 negative (mean<0); date2: mostly positive (mean>0); date3: all 3 negative (mean<0).
    signs = [[-0.01, -0.02, -0.03], [-0.05, 0.10, 0.10], [-0.01, -0.02, -0.03]]
    with Session(engine) as session:
        for d, rets in zip(dates, signs):
            run = _add_run(session, d, "Risk-on")
            for i, ret in enumerate(rets):
                ticker = f"T{i}"
                _add_result(session, run.id, ticker, "C", "Avoid", "Technology", i + 1)
                _add_dd_fr(session, run, ticker, DD_H, ret, mdd=-0.01, uw=1, ttr=1)
        session.commit()

    def _ctx(session=None, as_of=None, config=None):
        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05} for d in dates}

    monkeypatch.setattr(market_phase, "phase_context_by_date", _ctx)
    with Session(engine) as session:
        payload = compute_drawdown_expectations(session, _FACTOR_CLAIM, _dd_cfg())
    streak = _by_phase(payload, "Expansion")["loss_streak"]
    # A per-observation (WRONG) scan over the 9 raw rows would see several consecutive negatives (>= 3).
    # At the walk-forward cadence there are only 3 dates: mean<0, mean>0, mean<0 -> longest run == 1.
    assert streak["n"] == 3  # 3 distinct cadence dates, never the 9 raw observations
    assert streak["value"] == 1


def test_compute_drawdown_expectations_combination_claim_kind_resolves(tmp_path, monkeypatch):
    """A real combination-shaped ledger claim (mirrors the actual promoted `rs_spy_3m x high_proximity`
    composite claim's JSON shape) resolves through `compute_drawdown_expectations` end-to-end — proving
    the `cohort`->`cohort_kind` rename + `condition`-string parsing integrate correctly with
    `compute_samples`'s combination path (not just in isolation, per the `_claim_samples_kwargs` unit
    tests above)."""
    engine = make_engine(f"sqlite:///{tmp_path / 'combo.db'}")
    create_db_and_tables(engine)
    combo_dates = [date(2025, 1, 10), date(2025, 2, 10), date(2025, 3, 10), date(2025, 4, 10)]
    with Session(engine) as session:
        for i, d in enumerate(combo_dates):
            run = _add_run(session, d, "Risk-on")
            session.add(ScannerResult(
                run_id=run.id, ticker="AAA", name="AAA", sector="Technology",
                leadership_score=90.0, leadership_bucket="A",
                entry_quality_score=90.0, entry_quality_bucket="A",
                risk_score=50.0, risk_bucket="C",
                setup_status="Actionable", rank=1, record_json="{}",
            ))
            _add_dd_fr(session, run, "AAA", DD_H, 0.02 if i % 2 == 0 else -0.01, mdd=-0.03, uw=2, ttr=1)
        session.commit()

    def _ctx(session=None, as_of=None, config=None):
        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05} for d in combo_dates}

    monkeypatch.setattr(market_phase, "phase_context_by_date", _ctx)
    claim = {
        "kind": "combination", "cohort": "composite",
        "condition": ["leadership_score:top:half", "entry_quality_score:top:half"],
        "direction": "positive", "horizon": DD_H,
    }
    with Session(engine) as session:
        payload = compute_drawdown_expectations(session, claim, _dd_cfg())
    assert payload is not None
    assert _by_phase(payload, "Expansion")["n"] == 4  # AAA scores top-half on both legs every date


def test_compute_drawdown_expectations_event_study_claim_kind_resolves(tmp_path, monkeypatch):
    """A real event-study-shaped ledger claim (mirrors the actual `Breakout-watch x Risk-on` promoted
    claim's JSON shape) resolves through `compute_drawdown_expectations` end-to-end."""
    engine = make_engine(f"sqlite:///{tmp_path / 'event_study.db'}")
    create_db_and_tables(engine)
    es_dates = [date(2025, 1, 10), date(2025, 2, 10), date(2025, 3, 10)]
    with Session(engine) as session:
        for d in es_dates:
            run = _add_run(session, d, "Risk-on")
            _add_result(session, run.id, "AAA", "A", "Breakout-watch", "Technology", 1)
            _add_dd_fr(session, run, "AAA", DD_H, 0.02, mdd=-0.04, uw=3, ttr=2)
        session.commit()

    def _ctx(session=None, as_of=None, config=None):
        return {d.isoformat(): {"phase": "Expansion", "severity": 10.0, "p_bear": 0.05} for d in es_dates}

    monkeypatch.setattr(market_phase, "phase_context_by_date", _ctx)
    claim = {
        "kind": "event-study", "subject": "Breakout-watch", "slice_kind": "regime", "regime": "Risk-on",
        "view": "pooled", "direction": "positive", "horizon": DD_H,
    }
    with Session(engine) as session:
        payload = compute_drawdown_expectations(session, claim, _dd_cfg())
    assert payload is not None
    assert _by_phase(payload, "Expansion")["n"] == 3


# ==================================================================================================
# compute_drawdown_expectations_cached — the J-72 EventStudyCache performance layer (iter-41, J-25)
# ==================================================================================================
def test_compute_drawdown_expectations_cached_byte_identical_and_single_row(dd_expectations_engine):
    """A cache MISS then HIT both return a payload BYTE-IDENTICAL to a fresh uncached
    `compute_drawdown_expectations` call, and exactly ONE `EventStudyCache` row is written for this claim
    (no duplicate insert on the second call)."""
    cfg = _dd_cfg()
    with Session(dd_expectations_engine) as session:
        fresh = compute_drawdown_expectations(session, _FACTOR_CLAIM, cfg)
        miss = compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)
        hit = compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)
        subject = _drawdown_expectations_cache_subject(_FACTOR_CLAIM)
        rows = session.exec(select(EventStudyCache).where(EventStudyCache.subject == subject)).all()
    assert json.dumps(fresh, sort_keys=True) == json.dumps(miss, sort_keys=True) == json.dumps(hit, sort_keys=True)
    assert len(rows) == 1


def test_compute_drawdown_expectations_cached_avoids_recompute_on_hit(dd_expectations_engine, monkeypatch):
    """The SECOND call for the SAME claim never re-invokes the uncached `compute_drawdown_expectations` —
    proven by monkeypatching it to raise if called a second time (a call-count proof, not just a
    byte-match, so a bug that silently recomputed-but-still-matched would still fail this test)."""
    import app.engine.forward_testing as forward_testing_module

    cfg = _dd_cfg()
    call_count = {"n": 0}
    real = forward_testing_module.compute_drawdown_expectations

    def _counting(*args, **kwargs):
        call_count["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(forward_testing_module, "compute_drawdown_expectations", _counting)
    with Session(dd_expectations_engine) as session:
        compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)  # MISS -> 1 call
        compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)  # HIT -> 0 more calls
        compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)  # HIT -> 0 more calls
    assert call_count["n"] == 1


def test_compute_drawdown_expectations_cached_refreshes_on_dataset_version_change(dd_expectations_engine):
    """The cache refreshes when the dataset changes (no stale figure): adding one more forward_returns row
    bumps `_dataset_version`, so the next call recomputes (a genuinely different cohort — one more
    Expansion-phase observation, on the SAME already-classified date) rather than serving the pre-change
    payload, and the stale row is pruned."""
    cfg = _dd_cfg()
    with Session(dd_expectations_engine) as session:
        before = compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)
        subject = _drawdown_expectations_cache_subject(_FACTOR_CLAIM)
        from app.engine.research import _dataset_version
        v_before = _dataset_version(session)
        rows_before = session.exec(select(EventStudyCache).where(EventStudyCache.subject == subject)).all()
        assert len(rows_before) == 1 and rows_before[0].dataset_version == v_before

        # change the dataset: one more leadership_score observation on the FIRST Expansion date (a new
        # ticker on the ALREADY-classified _EXP_DATES[0] run — genuinely grows the classified cohort by 1,
        # unlike a brand-new date the fixture's mocked phase map does not cover).
        existing_run = session.exec(
            select(ScannerRun).where(ScannerRun.asof_date == _EXP_DATES[0])
        ).one()
        _add_result(session, existing_run.id, "ZZZ", "A", "Actionable", "Technology", 2)
        _add_dd_fr(session, existing_run, "ZZZ", DD_H, 0.05, mdd=-0.01, uw=1, ttr=1)
        session.commit()
        v_after = _dataset_version(session)
        assert v_after != v_before

        after = compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg)
        rows_after = session.exec(select(EventStudyCache).where(EventStudyCache.subject == subject)).all()
    # the stale (v_before) row was pruned; exactly one row remains, keyed to the new stamp.
    assert len(rows_after) == 1 and rows_after[0].dataset_version == v_after
    assert _by_phase(before, "Expansion")["n"] == 4
    assert _by_phase(after, "Expansion")["n"] == 5  # the recompute picked up the new observation


def test_compute_drawdown_expectations_cached_none_when_horizon_outside_scope_skips_db(dd_expectations_engine):
    """The scope gate short-circuits BEFORE any cache lookup (never writes a row for a claim that can
    never resolve, regardless of dataset state)."""
    cfg = load_config()
    wf = cfg.walk_forward.model_copy(update={"underwater_horizons": [1, 5]})
    cfg = cfg.model_copy(update={"walk_forward": wf})
    with Session(dd_expectations_engine) as session:
        assert compute_drawdown_expectations_cached(session, _FACTOR_CLAIM, cfg) is None
        assert session.scalar(select(func.count()).select_from(EventStudyCache)) == 0
