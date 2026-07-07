"""iter-18 (J-10 performance) — `/api/stocks/{ticker}/bars` presentation bounding on the deep basis.

The chart never ships every deep bar by default:
  * DEFAULT (no `range`): the trailing `chart_bars.default_years` window before the resolved as-of —
    bounded, daily, no-lookahead (dates <= as-of only).
  * `range=full`: the explicit whole-real-history opt-in — reaches the symbol's REAL first bar, with
    bars older than `chart_bars.downsample_beyond_years` before the as-of sampled at weekly density.
    Every served bar is a REAL stored daily bar (sampling shows fewer bars; it never synthesizes or
    aggregates one) and the series' real first bar is always kept.
  * broadened ticker validation: a symbol with stored bars is servable even when outside the legacy
    `config.universe.symbols` list; a truly unknown ticker stays 404.

Synthetic handler-level tests (no seed boot): a tiny DB with ~11 years of daily bars exercises the
windowing/downsampling/no-lookahead contract in milliseconds.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.api.stocks import stock_bars
from app.config import load_config
from app.db import create_db_and_tables, make_engine
from app.engine.indicators import sma_series
from app.models import DailyPrice

START = date(2014, 1, 1)
N_DAYS = 4100  # ~11.2 calendar years of consecutive daily bars — deep + recent + downsample regions


@pytest.fixture(scope="module")
def deep_engine(tmp_path_factory):
    """One symbol ("AAA") with ~11 years of consecutive daily bars (closes strictly increasing so any
    served bar is uniquely identifiable against the stored series)."""
    engine = make_engine(f"sqlite:///{tmp_path_factory.mktemp('bw') / 'bw.db'}")
    create_db_and_tables(engine)
    with Session(engine) as session:
        rows = [
            {
                "symbol": "AAA",
                "date": START + timedelta(days=i),
                "open": 100.0 + i, "high": 101.0 + i, "low": 99.0 + i,
                "close": 100.5 + i, "volume": 1000.0 + i,
            }
            for i in range(N_DAYS)
        ]
        session.execute(DailyPrice.__table__.insert(), rows)
        session.commit()
    return engine


def _stored(session) -> dict[str, float]:
    from sqlmodel import select

    return {
        bar.date.isoformat(): bar.close
        for bar in session.exec(select(DailyPrice).where(DailyPrice.symbol == "AAA")).all()
    }


LATEST = START + timedelta(days=N_DAYS - 1)


def _years_before(d: date, years: int) -> date:
    """Calendar-year subtraction (mirrors the endpoint's month-arithmetic window bound)."""
    try:
        return d.replace(year=d.year - years)
    except ValueError:  # Feb 29
        return d.replace(year=d.year - years, day=28)


def test_default_range_is_bounded_trailing_window(deep_engine):
    """With no `range` param the served bars are exactly the trailing default_years window (bounded,
    daily, <= as-of) and the payload discloses the symbol's REAL first available date."""
    cfg = load_config()
    with Session(deep_engine) as session:
        body = stock_bars("AAA", session=session)
    window_start = _years_before(LATEST, cfg.chart_bars.default_years)

    assert body["range"] == "default"
    assert body["asof_date"] == LATEST.isoformat()
    assert body["first_available_date"] == START.isoformat()   # the real first stored bar (honest depth)
    dates = [b["date"] for b in body["bars"]]
    assert dates == sorted(dates)
    assert dates[0] >= window_start.isoformat()                 # bounded left edge
    assert dates[-1] == LATEST.isoformat()
    assert all(d <= body["asof_date"] for d in dates)           # no lookahead
    # the bounded window ships FAR fewer bars than the deep series, but a full daily recent window
    assert len(dates) < N_DAYS * 0.6
    assert len(dates) == (LATEST - max(window_start, START)).days + 1  # daily density in-window


def test_full_range_reaches_real_first_bar_and_downsamples_deep_region(deep_engine):
    """`range=full` serves the WHOLE real history: the series' real first bar is included, the deep
    region (older than downsample_beyond_years before as-of) is weekly-sampled, the recent region stays
    daily — and EVERY served bar byte-matches a stored daily bar (sampling, never synthesis)."""
    cfg = load_config()
    with Session(deep_engine) as session:
        body = stock_bars("AAA", range_="full", session=session)
        stored = _stored(session)

    dates = [b["date"] for b in body["bars"]]
    assert body["range"] == "full"
    assert body["downsampled"] is True
    assert dates[0] == START.isoformat()                        # the REAL first bar is always kept
    assert dates[-1] == LATEST.isoformat()

    deep_boundary = _years_before(LATEST, cfg.chart_bars.downsample_beyond_years).isoformat()
    deep = [d for d in dates if d < deep_boundary]
    recent = [d for d in dates if d >= deep_boundary]
    n_deep_days = sum(1 for d in stored if d < deep_boundary)
    # weekly sampling: roughly one bar per 7 stored days in the deep region (plus the kept first bar)
    assert 0 < len(deep) <= n_deep_days // 7 + 2
    # the recent region keeps FULL daily density
    assert len(recent) == sum(1 for d in stored if deep_boundary <= d <= LATEST.isoformat())
    # every served bar is a REAL stored daily bar — never synthesized/aggregated
    for b in body["bars"]:
        assert stored[b["date"]] == b["close"]


def test_full_range_ma_values_stay_canonical_daily_series_values(deep_engine):
    """The MA arrays align 1:1 with the served bars, and each value equals the canonical DAILY
    sma_series at that bar's position in the FULL stored series — sampling never recomputes an MA over
    the sampled subset (single source of truth)."""
    cfg = load_config()
    with Session(deep_engine) as session:
        body = stock_bars("AAA", range_="full", session=session)
        stored = _stored(session)

    all_dates = sorted(stored)
    all_closes = [stored[d] for d in all_dates]
    index_of = {d: i for i, d in enumerate(all_dates)}
    for period in cfg.indicators.ma_periods:
        series = body["ma"][str(period)]
        assert len(series) == len(body["bars"])                 # aligned 1:1 with the served bars
        full_ma = sma_series(all_closes, period)
        for b, got in zip(body["bars"], series):
            assert got == full_ma[index_of[b["date"]]]          # the canonical daily MA at that date


def test_default_range_ma_not_na_at_window_left_edge(deep_engine):
    """The bounded window's left-edge MA values come from the FULL daily series (bars exist before the
    window), so they are REAL numbers — not a fabricated warm-up NA gap."""
    with Session(deep_engine) as session:
        body = stock_bars("AAA", session=session)
    for period_series in body["ma"].values():
        assert period_series[0] is not None


def test_unknown_range_is_422(deep_engine):
    with Session(deep_engine) as session:
        with pytest.raises(HTTPException) as exc:
            stock_bars("AAA", range_="everything", session=session)
        assert exc.value.status_code == 422


def test_stored_symbol_outside_config_universe_is_served(deep_engine):
    """Broadened ticker validation (post-swap leaderboard members must not 404): AAA is NOT in
    `config.universe.symbols`, yet its stored bars are served; a truly unknown ticker stays 404."""
    cfg = load_config()
    assert "AAA" not in cfg.universe.symbols
    with Session(deep_engine) as session:
        body = stock_bars("aaa", session=session)               # case-insensitive too
        assert body["ticker"] == "AAA"
        with pytest.raises(HTTPException) as exc:
            stock_bars("NOTREAL", session=session)
        assert exc.value.status_code == 404


def test_default_window_at_historical_asof_no_lookahead(deep_engine):
    """At a historical as-of D the bounded window is relative to D (dates in (D - default_years, D]) —
    the right edge stays the no-lookahead boundary."""
    cfg = load_config()
    d = START + timedelta(days=3000)
    with Session(deep_engine) as session:
        body = stock_bars("AAA", as_of=d.isoformat(), session=session)
    dates = [b["date"] for b in body["bars"]]
    assert body["asof_date"] == d.isoformat()
    assert dates[-1] == d.isoformat()
    assert all(x <= d.isoformat() for x in dates)               # no bar after D
    assert dates[0] >= _years_before(d, cfg.chart_bars.default_years).isoformat()


def test_through_latest_composes_with_bounded_window(deep_engine):
    """`through=latest` (the J-20 display-only forward extension) composes with the bounded default:
    the left edge is windowed relative to D, the forward region (> D) is fully present and flagged."""
    cfg = load_config()
    d = START + timedelta(days=4000)  # a historical D with a real post-D region
    with Session(deep_engine) as session:
        body = stock_bars("AAA", as_of=d.isoformat(), through="latest", session=session)
    dates = [b["date"] for b in body["bars"]]
    assert body["latest_date"] == LATEST.isoformat()
    assert dates[0] >= _years_before(d, cfg.chart_bars.default_years).isoformat()
    forward = [b for b in body["bars"] if b["is_forward"]]
    assert len(forward) == (LATEST - d).days                    # every post-D daily bar is present
    assert all(b["date"] > d.isoformat() for b in forward)


def test_default_window_falls_back_to_symbol_trailing_window_when_series_ended(deep_engine):
    """A symbol whose data ENDED before the default window (a delisted name viewed at today's as-of)
    still charts honestly: the fallback is the trailing window relative to ITS OWN last bar — real
    bars, never an empty chart, never fabricated ones."""
    engine = make_engine("sqlite://")
    create_db_and_tables(engine)
    cfg = load_config()
    ended_last = date(2018, 6, 29)
    with Session(engine) as session:
        rows = [
            {
                "symbol": "END", "date": ended_last - timedelta(days=i),
                "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0,
            }
            for i in range(400)
        ]
        # a second, current symbol pins the latest data date well past END's last bar
        rows += [
            {
                "symbol": "CUR", "date": date(2026, 6, 1) + timedelta(days=i),
                "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0,
            }
            for i in range(10)
        ]
        session.execute(DailyPrice.__table__.insert(), rows)
        session.commit()
        body = stock_bars("END", session=session)
    dates = [b["date"] for b in body["bars"]]
    assert len(dates) > 0                                        # honest real history, not an empty chart
    assert dates[-1] == ended_last.isoformat()                   # …ending at ITS real last bar
    assert dates[0] >= _years_before(ended_last, cfg.chart_bars.default_years).isoformat()
