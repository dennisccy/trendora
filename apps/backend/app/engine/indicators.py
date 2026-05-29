"""Pure, DB-free, deterministic indicator math (anti-goal: No magic numbers).

Every function operates on a plain ascending price/volume series and takes its period/window
as an ARGUMENT — the actual periods come from `config.indicators`, so NO period or threshold
literal lives in this module (a grep over the engine calc files finds none). Insufficient
history returns `None` (NA) — these functions NEVER fabricate a value (anti-goal: No
fabricated data). `None` propagates upward so the engine reports NA for short-history symbols.

The only numeric literals here are structural: 0/1/2 (indexing & arithmetic) and 100 (the
percent unit). None of them is a tunable scoring parameter.
"""
from __future__ import annotations

from typing import Optional, Sequence

NA = None  # explicit alias: "insufficient history" — never a fabricated number


def sma(values: Sequence[float], period: int) -> Optional[float]:
    """Simple moving average of the last `period` values. NA if fewer than `period` values."""
    if period <= 0:
        raise ValueError(f"sma period must be positive, got {period}")
    if len(values) < period:
        return NA
    window = values[-period:]
    return sum(window) / period


def rs_vs(series: Sequence[float], benchmark: Sequence[float], window: int) -> Optional[float]:
    """Relative strength = series total return / benchmark total return over `window` bars.

    > 1 means the series outperformed the benchmark. NA if either series lacks `window`+1 bars
    (need the bar `window` ago and the latest bar) or the benchmark return is zero.
    """
    if window <= 0:
        raise ValueError(f"rs_vs window must be positive, got {window}")
    if len(series) < window + 1 or len(benchmark) < window + 1:
        return NA
    base_series = series[-1 - window]
    base_bench = benchmark[-1 - window]
    if base_series == 0 or base_bench == 0:
        return NA
    series_ret = series[-1] / base_series
    bench_ret = benchmark[-1] / base_bench
    if bench_ret == 0:
        return NA
    return series_ret / bench_ret


def atr_pct(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int,
) -> Optional[float]:
    """Average True Range as a percent of the latest close. NA if fewer than `period`+1 bars."""
    if period <= 0:
        raise ValueError(f"atr_pct period must be positive, got {period}")
    n = len(closes)
    if n != len(highs) or n != len(lows):
        raise ValueError("atr_pct requires highs/lows/closes of equal length")
    if n < period + 1:
        return NA
    true_ranges: list[float] = []
    for i in range(1, n):
        prev_close = closes[i - 1]
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - prev_close),
            abs(lows[i] - prev_close),
        )
        true_ranges.append(tr)
    atr = sum(true_ranges[-period:]) / period
    last_close = closes[-1]
    if last_close == 0:
        return NA
    return atr / last_close * 100


def dist_from_high(closes: Sequence[float], window: int) -> Optional[float]:
    """Distance of the latest close BELOW the rolling high over `window` bars, as a percent.

    Result is <= 0 (0 at a fresh high). NA if fewer than `window` bars.
    """
    if window <= 0:
        raise ValueError(f"dist_from_high window must be positive, got {window}")
    if len(closes) < window:
        return NA
    rolling_high = max(closes[-window:])
    if rolling_high == 0:
        return NA
    return (closes[-1] - rolling_high) / rolling_high * 100


def ma_stack(closes: Sequence[float], periods: Sequence[int]) -> Optional[float]:
    """Fraction in [0,1] of satisfied bullish MA-stack conditions.

    Conditions: latest close above each computable MA, and each shorter MA above the next
    longer MA (a bullish stack). Long MAs that lack history are skipped (NA) and the fraction
    is taken over the conditions that COULD be evaluated — no fabrication. NA only if no MA at
    all is computable.
    """
    available = [(p, sma(closes, p)) for p in periods]
    available = [(p, m) for p, m in available if m is not None]
    if not available:
        return NA
    last_close = closes[-1]
    conditions: list[bool] = [last_close > m for _, m in available]
    for (_, shorter_ma), (_, longer_ma) in zip(available, available[1:]):
        conditions.append(shorter_ma > longer_ma)
    return sum(1 for c in conditions if c) / len(conditions)


def vol_trend(volumes: Sequence[float], period: int) -> Optional[float]:
    """Recent volume momentum: mean volume over the last `period` bars / mean over the prior
    `period` bars. > 1 means expanding volume. NA if fewer than 2*`period` bars.
    """
    if period <= 0:
        raise ValueError(f"vol_trend period must be positive, got {period}")
    if len(volumes) < 2 * period:
        return NA
    recent = sum(volumes[-period:]) / period
    prior = sum(volumes[-2 * period:-period]) / period
    if prior == 0:
        return NA
    return recent / prior
