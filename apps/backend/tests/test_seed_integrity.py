"""KEYSTONE test (anti-goal: No fabricated data).

Runs on the REAL committed SPY bars and proves the seed naturally contains BOTH a sustained
risk-off stretch and a sustained risk-on stretch — without any fabricated or hand-edited bar.
Also asserts the key universe symbols + index/sector ETFs + ^VIX are present with a reasonable
bar count and unique (symbol, date).

The day-count cutoffs (20 / 40) are TEST PARAMETERS proving a stretch is *sustained* — they are
not scoring magic numbers (scoring config is separate and untouched here).
"""
from __future__ import annotations

import csv
from collections import deque
from datetime import date

from app.data_providers.seed_provider import symbol_to_filename

RISK_OFF_MIN_DAYS = 20  # contiguous trading days with close < SMA200
RISK_ON_MIN_DAYS = 40   # contiguous trading days with close > a *rising* SMA200
SMA_WINDOW = 200


def _load_series(seed_dir, symbol):
    dates, closes = [], []
    with (seed_dir / "prices" / symbol_to_filename(symbol)).open() as fh:
        for row in csv.DictReader(fh):
            dates.append(date.fromisoformat(row["date"]))
            closes.append(float(row["close"]))
    return dates, closes


def _sma(values, window):
    out = [None] * len(values)
    window_q: deque = deque()
    running = 0.0
    for i, v in enumerate(values):
        window_q.append(v)
        running += v
        if len(window_q) > window:
            running -= window_q.popleft()
        if len(window_q) == window:
            out[i] = running / window
    return out


def _longest_run(predicate, n):
    best = run = 0
    for i in range(n):
        if predicate(i):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def test_spy_contains_sustained_risk_off_stretch(seed_dir):
    _, closes = _load_series(seed_dir, "SPY")
    sma = _sma(closes, SMA_WINDOW)
    longest = _longest_run(lambda i: sma[i] is not None and closes[i] < sma[i], len(closes))
    assert longest >= RISK_OFF_MIN_DAYS, (
        f"expected a sustained risk-off stretch (>= {RISK_OFF_MIN_DAYS} contiguous days below "
        f"SMA200); longest found = {longest}"
    )


def test_spy_contains_sustained_risk_on_stretch(seed_dir):
    _, closes = _load_series(seed_dir, "SPY")
    sma = _sma(closes, SMA_WINDOW)

    def risk_on(i):
        return (
            i > 0
            and sma[i] is not None
            and sma[i - 1] is not None
            and closes[i] > sma[i]
            and sma[i] > sma[i - 1]  # SMA200 rising
        )

    longest = _longest_run(risk_on, len(closes))
    assert longest >= RISK_ON_MIN_DAYS, (
        f"expected a sustained risk-on stretch (>= {RISK_ON_MIN_DAYS} contiguous days above a "
        f"rising SMA200); longest found = {longest}"
    )


def test_key_symbols_present_with_reasonable_history(seed_dir, config):
    key = (
        list(config.etfs.index)               # SPY, QQQ, IWM, RSP
        + list(config.etfs.sector.keys())     # the 11 sector ETFs
        + list(config.etfs.volatility)        # ^VIX
        + ["NVDA", "AAPL", "MSFT", "AMD", "AVGO", "JPM", "XOM"]
    )
    for symbol in key:
        dates, _ = _load_series(seed_dir, symbol)
        assert len(dates) >= 400, f"{symbol} has too few bars ({len(dates)})"


def test_unique_symbol_date_in_fixtures(seed_dir):
    for symbol in ["SPY", "NVDA", "^VIX", "XLK"]:
        dates, _ = _load_series(seed_dir, symbol)
        assert len(dates) == len(set(dates)), f"{symbol} has duplicate dates"


def test_no_negative_or_zero_prices(seed_dir):
    """A cheap sanity guard: real adjusted prices are strictly positive."""
    for symbol in ["SPY", "NVDA"]:
        _, closes = _load_series(seed_dir, symbol)
        assert all(c > 0 for c in closes)
