"""Pure indicator functions — exact hand-computed values + NA on short history.

These are DB-free pure functions; every expected value below is computed by hand so the
test asserts an exact number (anti-pattern: "something returned"). Insufficient history
returns NA (None) — never a fabricated value (anti-goal: No fabricated data).
"""
from __future__ import annotations

import pytest

from app.engine import indicators as ind


# --- sma -----------------------------------------------------------------------------------
def test_sma_exact():
    assert ind.sma([1, 2, 3, 4, 5], 5) == 3.0
    assert ind.sma([1, 2, 3, 4, 5], 3) == 4.0  # (3+4+5)/3


def test_sma_na_when_too_short():
    assert ind.sma([1, 2], 3) is None
    assert ind.sma([], 1) is None


def test_sma_rejects_nonpositive_period():
    with pytest.raises(ValueError):
        ind.sma([1, 2, 3], 0)


# --- sma_series ----------------------------------------------------------------------------
def test_sma_series_warmup_na_then_rolling():
    # period 3: first two indices lack enough history (NA), then the rolling SMA.
    assert ind.sma_series([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0]
    # period 5: only the last index has a full window.
    assert ind.sma_series([1, 2, 3, 4, 5], 5) == [None, None, None, None, 3.0]


def test_sma_series_aligned_to_input_length():
    values = [10, 20, 30, 40]
    assert len(ind.sma_series(values, 2)) == len(values)
    assert ind.sma_series([], 3) == []


def test_sma_series_last_equals_sma_invariant():
    # the headline single-source invariant: the series' final element is exactly `sma`
    # for every period — one MA definition feeds the chart overlay, invalidation and scoring.
    values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0]
    for period in range(1, len(values) + 1):
        assert ind.sma_series(values, period)[-1] == ind.sma(values, period)


def test_sma_series_rejects_nonpositive_period():
    with pytest.raises(ValueError):
        ind.sma_series([1, 2, 3], 0)


# --- rs_vs ---------------------------------------------------------------------------------
def test_rs_vs_exact():
    # series +50% over 1 bar, benchmark flat -> RS 1.5
    assert ind.rs_vs([100, 150], [100, 100], 1) == 1.5
    # series -10% over 2 bars, benchmark flat -> RS 0.9
    assert ind.rs_vs([100, 120, 90], [100, 100, 100], 2) == 0.9


def test_rs_vs_na_when_too_short():
    # window+1 = 2 bars required
    assert ind.rs_vs([100], [100], 1) is None
    assert ind.rs_vs([100, 110], [100], 1) is None


# --- atr_pct -------------------------------------------------------------------------------
def test_atr_pct_exact():
    highs = [11, 11, 11]
    lows = [9, 9, 9]
    closes = [10, 10, 10]
    # TR each bar = max(11-9, |11-10|, |9-10|) = 2 -> ATR=2 -> 2/10*100 = 20.0
    assert ind.atr_pct(highs, lows, closes, 2) == 20.0


def test_atr_pct_na_when_too_short():
    assert ind.atr_pct([11, 11], [9, 9], [10, 10], 5) is None


# --- dist_from_high ------------------------------------------------------------------------
def test_dist_from_high_exact():
    # high over window=3 is 100; last close 80 -> -20%
    assert ind.dist_from_high([100, 90, 80], 3) == -20.0
    # at a fresh high -> 0%
    assert ind.dist_from_high([80, 90, 100], 3) == 0.0


def test_dist_from_high_na_when_too_short():
    assert ind.dist_from_high([100, 90], 3) is None


# --- ma_stack ------------------------------------------------------------------------------
def test_ma_stack_fully_bullish():
    # rising series: price above both MAs and MA2 > MA3 -> all 3 conditions true -> 1.0
    assert ind.ma_stack([1, 2, 3, 4, 5], [2, 3]) == 1.0


def test_ma_stack_fully_bearish():
    # falling series: none of the 3 conditions hold -> 0.0
    assert ind.ma_stack([5, 4, 3, 2, 1], [2, 3]) == 0.0


def test_ma_stack_long_ma_na_uses_available_only():
    # only the 2-period MA is computable (200 is NA); no crash, no fabrication.
    # last=3 > sma(.,2)=2.5 -> single condition true -> 1.0
    assert ind.ma_stack([1, 2, 3], [2, 200]) == 1.0


def test_ma_stack_na_when_no_ma_computable():
    assert ind.ma_stack([1, 2, 3], [200]) is None


# --- vol_trend -----------------------------------------------------------------------------
def test_vol_trend_exact():
    # recent 2-day avg vol 20 vs prior 2-day avg vol 10 -> ratio 2.0
    assert ind.vol_trend([10, 10, 20, 20], 2) == 2.0


def test_vol_trend_na_when_too_short():
    # needs 2*period bars
    assert ind.vol_trend([1, 2, 3], 2) is None


# --- hist_volatility (J-30 volatility-family level) ----------------------------------------
def test_hist_volatility_exact():
    # closes -> daily simple returns [+0.10, -0.10]; mean 0; population stdev sqrt(0.01)=0.10;
    # expressed as a percent (x100) -> 10.0 (comparable to ATR%).
    assert ind.hist_volatility([100, 110, 99], 2) == pytest.approx(10.0)


def test_hist_volatility_na_when_too_short():
    # needs window+1 closes to form `window` returns
    assert ind.hist_volatility([100, 110], 2) is None
    assert ind.hist_volatility([], 1) is None


def test_hist_volatility_rejects_nonpositive_window():
    with pytest.raises(ValueError):
        ind.hist_volatility([100, 110, 99], 0)


# --- vol_contraction (J-30 volatility-family change/contraction; VCP-style, continuous) ----
def test_vol_contraction_exact_ratio_below_one_is_contracting():
    # returns in order [+0.10, -0.10, +0.05, -0.05]: prior window (first two) realized vol 0.10,
    # recent window (last two) realized vol 0.05 -> ratio 0.5 (< 1 = volatility drying up).
    closes = [100, 110, 99, 103.95, 98.7525]
    assert ind.vol_contraction(closes, 2, 2) == pytest.approx(0.5)


def test_vol_contraction_na_when_too_short():
    # needs recent + prior + 1 closes
    assert ind.vol_contraction([100, 110, 99, 103.95], 2, 2) is None


def test_vol_contraction_na_when_prior_vol_zero():
    # prior window has constant price (zero realized vol) -> ratio undefined -> NA (never inf/fabricated)
    assert ind.vol_contraction([100, 100, 100, 105, 99.75], 2, 2) is None


def test_vol_contraction_rejects_nonpositive_windows():
    with pytest.raises(ValueError):
        ind.vol_contraction([100, 110, 99, 103.95, 98.7525], 0, 2)
    with pytest.raises(ValueError):
        ind.vol_contraction([100, 110, 99, 103.95, 98.7525], 2, 0)


# --- downside_vol (J-30 volatility-family downside/semivol; negative leg only) --------------
def test_downside_vol_uses_only_the_negative_leg():
    # two equal down moves of 10% -> sqrt(mean([0.10^2, 0.10^2])) = sqrt(0.01) = 0.10
    assert ind.downside_vol([100, 90, 81], 2) == pytest.approx(0.10)


def test_downside_vol_all_up_series_is_zero_never_penalises_upside():
    # an all-non-negative series has NO downside dispersion -> 0.0 (NOT a fabricated/total-vol number)
    assert ind.downside_vol([100, 110, 121], 2) == 0.0


def test_downside_vol_na_when_too_short():
    assert ind.downside_vol([100], 2) is None


def test_downside_vol_rejects_nonpositive_window():
    with pytest.raises(ValueError):
        ind.downside_vol([100, 90, 81], 0)
