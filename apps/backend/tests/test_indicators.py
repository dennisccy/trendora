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
