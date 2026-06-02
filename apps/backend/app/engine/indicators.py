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

from math import sqrt
from typing import Optional, Sequence

NA = None  # explicit alias: "insufficient history" — never a fabricated number


def _daily_returns(closes: Sequence[float]) -> Optional[list[float]]:
    """Daily simple returns `r_i = closes[i]/closes[i-1] - 1` over the given price window (length
    `len(closes) - 1`). NA (`None`) if any prior close is zero (an undefined return) — never fabricated."""
    out: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev == 0:
            return None
        out.append(closes[i] / prev - 1)
    return out


def _population_stdev(values: Sequence[float]) -> float:
    """Population standard deviation (mean-centered RMS deviation) of `values`. Empty -> 0."""
    if not values:
        return 0
    mean_value = sum(values) / len(values)
    return sqrt(sum((v - mean_value) ** 2 for v in values) / len(values))


def sma(values: Sequence[float], period: int) -> Optional[float]:
    """Simple moving average of the last `period` values. NA if fewer than `period` values."""
    if period <= 0:
        raise ValueError(f"sma period must be positive, got {period}")
    if len(values) < period:
        return NA
    window = values[-period:]
    return sum(window) / period


def sma_series(values: Sequence[float], period: int) -> list[Optional[float]]:
    """Rolling simple moving average aligned 1:1 with `values`: element `i` is the SMA of the
    `period` values ending at `i`, or NA (`None`) for the warm-up prefix with fewer than `period`
    prior values. Built by reusing `sma` over each prefix, so there is ONE MA definition and the
    invariant `sma_series(values, p)[-1] == sma(values, p)` holds by construction (single source:
    the chart overlay, the invalidation level and the scoring MA components never disagree)."""
    if period <= 0:
        raise ValueError(f"sma_series period must be positive, got {period}")
    return [sma(values[: i + 1], period) for i in range(len(values))]


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


# --- iter-13 volatility factor family (J-30) ------------------------------------------------
# Three NA-graceful volatility measures, each taking its window(s) as an ARGUMENT (the periods come
# from `config.indicators`). Computed once in the scoring/snapshot path from bars <= D (no lookahead)
# and STORED for the read-only Factor Lab to consume — they NEVER enter any weighted score.

def hist_volatility(closes: Sequence[float], window: int) -> Optional[float]:
    """Historical volatility (level): population standard deviation of the last `window` daily simple
    returns, expressed as a PERCENT (so it is directly comparable to ATR%). Higher = more volatile.
    NA if fewer than `window`+1 bars (need `window` returns) or a price in the window is zero."""
    if window <= 0:
        raise ValueError(f"hist_volatility window must be positive, got {window}")
    if len(closes) < window + 1:
        return NA
    rets = _daily_returns(closes[-(window + 1):])
    if rets is None:
        return NA
    return _population_stdev(rets) * 100


def vol_contraction(closes: Sequence[float], recent: int, prior: int) -> Optional[float]:
    """Volatility contraction (change/contraction — the VCP-style measure, expressed CONTINUOUSLY):
    the realized volatility of the most recent `recent` daily returns divided by that of the `prior`
    daily returns immediately before them. A value < 1 means volatility is drying up (contracting —
    the VCP thesis); > 1 means expanding. NA if fewer than `recent`+`prior`+1 bars or the prior
    volatility is zero (an undefined ratio — never a fabricated/infinite number). Price-only and a
    pre-snapshot stock characteristic from bars <= D; it touches no setup status and no score."""
    if recent <= 0 or prior <= 0:
        raise ValueError(f"vol_contraction windows must be positive, got recent={recent}, prior={prior}")
    if len(closes) < recent + prior + 1:
        return NA
    rets = _daily_returns(closes[-(recent + prior + 1):])
    if rets is None:
        return NA
    prior_vol = _population_stdev(rets[:prior])      # the earlier (baseline) block
    if prior_vol == 0:
        return NA
    return _population_stdev(rets[-recent:]) / prior_vol  # the later (recent) block / baseline


def downside_vol(closes: Sequence[float], window: int) -> Optional[float]:
    """Downside / semi-volatility (downside leg ONLY): the trailing downside semideviation of the last
    `window` daily simple returns about MAR=0 — `sqrt(mean(min(r, 0)**2))`. Only NEGATIVE returns
    contribute (NEVER total volatility, which would penalise healthy upside). An all-non-negative
    window yields 0.0 (no downside dispersion), not a fabricated number. NA if fewer than `window`+1
    bars or a price in the window is zero. A pre-snapshot stock characteristic from bars <= D —
    DISTINCT from the FORWARD-return downside deviation the lab uses for its risk-adjusted column."""
    if window <= 0:
        raise ValueError(f"downside_vol window must be positive, got {window}")
    if len(closes) < window + 1:
        return NA
    rets = _daily_returns(closes[-(window + 1):])
    if rets is None:
        return NA
    return sqrt(sum(min(r, 0) ** 2 for r in rets) / len(rets))
