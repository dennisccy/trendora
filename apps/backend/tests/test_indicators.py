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


def test_sma_series_byte_identical_to_original_unbounded_prefix_implementation():
    """ops-hardening iter-57 (TC-9, the J-06 `bars?through=latest` latency fix): `sma_series` now
    bounds each call's slice to `values[max(0, i+1-period):i+1]` instead of the full-growing prefix
    `values[:i+1]` -- an O(n) copy on every one of `len(values)` iterations that made the whole series
    O(n^2) (profiled: ~0.178s -> ~0.038s for a real 7,695-bar history across 4 configured MA periods,
    `reports/perf-budgets.md`). Per the iter-53 lesson ("compare against the ORIGINAL implementation,
    never another instance of the new one"), this test keeps a literal copy of the PRE-iter-57
    unbounded-prefix implementation and asserts byte-identity against it -- not merely against a second
    call of the current function -- across several periods and a warm-up-spanning, non-trivial series."""
    def _sma_series_original_unbounded_prefix(values, period):
        return [ind.sma(values[: i + 1], period) for i in range(len(values))]

    values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0, 9.0, 7.0, 9.0, 3.0]
    for period in (1, 2, 3, 5, 8, 16, 20):
        assert ind.sma_series(values, period) == _sma_series_original_unbounded_prefix(values, period)
    # the empty-series edge case both forms must agree on
    assert ind.sma_series([], 3) == _sma_series_original_unbounded_prefix([], 3) == []


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


# --- overnight_gap_profile (J-24 / B-201 risk-budget) ---------------------------------------
# Fixture derivation (window=4, 5 bars): overnight_ret_i is set to EXACTLY 0.5 * total_ret_i at every
# step, so Var(overnight) = 0.5^2 * Var(total) exactly regardless of Var(total)'s actual value, making
# overnight_variance_share = 0.25 (25.0%) an EXACT expected value, not an approximation of an
# approximation.
#   day1: total +10.0% (close 100->110),   overnight +5.0% (open 105 from prior close 100)
#   day2: total  -6.0% (close 110->103.4), overnight -3.0% (open 106.7 from prior close 110)
#   day3: total  +4.0% (close 103.4->107.536), overnight +2.0% (open 105.468 from prior close 103.4)
#   day4: total  -8.0% (close 107.536->98.93312), overnight -4.0% (open 103.23456 from prior close 107.536)
# abs gaps = [5.0, 3.0, 2.0, 4.0] -> sorted [2.0, 3.0, 4.0, 5.0] (percent)
#   median (linear-interp rank=1.5): 3.0 + (4.0-3.0)*0.5 = 3.5
#   p95    (linear-interp rank=2.85): 4.0 + (5.0-4.0)*0.85 = 4.85
#   worst = max = 5.0
_GAP_CLOSES = [100, 110, 103.4, 107.536, 98.93312]
_GAP_OPENS = [100, 105, 106.7, 105.468, 103.23456]


def test_overnight_gap_profile_exact():
    profile = ind.overnight_gap_profile(_GAP_OPENS, _GAP_CLOSES, 4)
    assert profile["median"] == pytest.approx(3.5)
    assert profile["p95"] == pytest.approx(4.85)
    assert profile["worst"] == pytest.approx(5.0)
    assert profile["overnight_variance_share"] == pytest.approx(25.0)


def test_overnight_gap_profile_na_when_too_short():
    # needs window+1 = 5 aligned bars; only 3 given
    assert ind.overnight_gap_profile([100, 101, 102], [100, 101, 102], 4) is None


def test_overnight_gap_profile_rejects_nonpositive_window():
    with pytest.raises(ValueError):
        ind.overnight_gap_profile(_GAP_OPENS, _GAP_CLOSES, 0)


def test_overnight_gap_profile_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        ind.overnight_gap_profile([100, 101], [100, 101, 102], 1)


def test_overnight_gap_profile_share_na_on_zero_total_variance():
    # closes flat at 100 (every total return is exactly 0 -> undefined variance ratio -> NA), but
    # opens still vary, so the gap distribution itself stays a real, non-fabricated number.
    closes = [100, 100, 100, 100, 100]
    opens = [100, 105, 95, 102, 98]
    profile = ind.overnight_gap_profile(opens, closes, 4)
    # abs gaps = [5, 5, 2, 2] -> sorted [2, 2, 5, 5]
    assert profile["median"] == pytest.approx(3.5)   # 2 + (5-2)*0.5
    assert profile["p95"] == pytest.approx(5.0)       # 5 + (5-5)*0.85
    assert profile["worst"] == pytest.approx(5.0)
    assert profile["overnight_variance_share"] is None


# --- worst_20d_window (J-24 / B-201 risk-budget) ---------------------------------------------
def test_worst_20d_window_exact():
    # window=3; trailing 3-day returns ending at each valid index:
    #   idx3: 80/100 - 1  = -20.0%
    #   idx4: 105/90 - 1  = +16.666...%
    #   idx5: 70/95  - 1  = -26.315...%   <- most negative (worst)
    closes = [100, 90, 95, 80, 105, 70]
    assert ind.worst_20d_window(closes, 3) == pytest.approx((70 / 95 - 1) * 100)


def test_worst_20d_window_na_when_too_short():
    assert ind.worst_20d_window([100, 90, 95], 3) is None  # needs window+1 = 4 closes


def test_worst_20d_window_rejects_nonpositive_window():
    with pytest.raises(ValueError):
        ind.worst_20d_window([100, 90, 95, 80], 0)
