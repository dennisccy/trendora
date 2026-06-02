"""VCP detector (`app.engine.patterns.detect_vcp`) — pure, deterministic, config-driven proofs.

Named proofs:
  - positive          — a constructed VCP series flags, pivot == base high, invalidation == the
                        last-contraction low, contractions progressively shrink.            (J-16)
  - steady uptrend    — no pullback -> no contractions -> NOT flagged (no false positive).
  - expanding vol     — contractions GROWING -> not progressively tightening -> NOT flagged.
  - short history     — fewer than min_history_bars -> flagged=False / NA, NO fabricated pivot. (No fabricated data)
  - config-driven     — the SAME series flips flagged when a config threshold changes (no literal). (No magic numbers)

The constructed series use highs == lows == closes so peaks/troughs are exact close values, making the
expected pivot / last-contraction low exact and the depths reproducible by construction.
"""
from __future__ import annotations

from app.config import load_config
from app.engine import indicators as ind
from app.engine.patterns import (
    detect_flat_base_breakout,
    detect_pullback_to_rising_dma,
    detect_vcp,
)

PIVOT = 100.0  # the base high all the rebounds touch in the constructed series


def _vcp_closes() -> list[float]:
    """A textbook VCP: a long monotonic rise (no contraction), then three progressively-shallower
    pullbacks (-18% -> -9% -> -5%) each rebounding to the 100 pivot, ending 2% below the pivot."""
    prefix = [float(v) for v in range(42, 90)]  # 48 bars, monotonic -> zero contractions
    base = [
        90, 92, 94, 96, 98, 100,   # rise to the pivot (100)
        96, 90, 85, 82,            # contraction 1: -18% (trough 82)
        88, 94, 100,               # rebound to the pivot -> records -18%
        97, 93, 91,                # contraction 2: -9% (trough 91)
        95, 100,                   # rebound to the pivot -> records -9%
        98, 95,                    # contraction 3: -5% (trough 95 -> the last-contraction low)
        100,                       # rebound to the pivot -> records -5%
        98,                        # final close: 2% below the pivot (no qualifying 4th contraction)
    ]
    return prefix + [float(v) for v in base]


def _flat_volumes(closes: list[float]) -> list[float]:
    """Volume drying up: the base trades at 1000, the last 10 bars at 500 (recent/base ~ 0.54)."""
    vols = [1000.0] * len(closes)
    for i in range(len(closes) - 10, len(closes)):
        vols[i] = 500.0
    return vols


def test_constructed_vcp_series_flags_with_pivot_and_invalidation():
    cfg = load_config().patterns.vcp
    closes = _vcp_closes()
    vcp = detect_vcp(closes, closes, closes, _flat_volumes(closes), cfg)

    assert vcp["flagged"] is True
    assert vcp["pivot"] == PIVOT == max(closes)          # pivot is the base high
    assert vcp["invalidation"]["level"] == 95.0          # the last-contraction low
    assert "VCP invalid below the last-contraction low at $95.00" == vcp["invalidation"]["note"]
    # three progressively-shallower contractions, strictly decreasing
    assert vcp["contractions"] == [18.0, 9.0, 5.0]
    assert all(a > b for a, b in zip(vcp["contractions"], vcp["contractions"][1:]))
    assert vcp["detail"]["n_contractions"] == 3
    assert vcp["detail"]["dist_from_pivot_pct"] == 2.0   # 100 -> 98 is 2% below the pivot
    assert isinstance(vcp["reason"], str) and "contractions tightening" in vcp["reason"]


def test_steady_uptrend_does_not_flag():
    """A smooth monotonic uptrend has no pullbacks -> zero contractions -> not flagged."""
    cfg = load_config().patterns.vcp
    closes = [float(v) for v in range(50, 130)]  # 80 bars, strictly increasing
    vcp = detect_vcp(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert vcp["flagged"] is False
    assert vcp["pivot"] is None
    assert vcp["contractions"] == []
    assert vcp["detail"]["n_contractions"] == 0


def test_expanding_volatility_does_not_flag():
    """Contractions GROWING (5% -> 9% -> 18%) are not progressively tightening -> not flagged."""
    cfg = load_config().patterns.vcp
    prefix = [float(v) for v in range(42, 90)]
    base = [
        90, 92, 94, 96, 98, 100,   # to the pivot
        98, 95,                    # -5%
        100,
        97, 93, 91,                # -9%
        100,
        96, 90, 85, 82,            # -18% (widening — the opposite of a VCP)
        85,
    ]
    closes = prefix + [float(v) for v in base]
    vcp = detect_vcp(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert vcp["flagged"] is False


def test_short_history_is_na_never_fabricated():
    """Fewer than min_history_bars -> flagged=False with an honest reason and NO fabricated pivot."""
    cfg = load_config().patterns.vcp
    closes = [float(v) for v in range(50, 80)]  # 30 bars < min_history_bars
    vcp = detect_vcp(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert vcp["flagged"] is False
    assert vcp["pivot"] is None
    assert vcp["invalidation"]["level"] is None
    assert "Insufficient history" in vcp["reason"]


def test_detection_is_config_driven_not_hard_coded():
    """The SAME series flags under the real volume-dry-up threshold but NOT under a stricter one —
    proving the threshold is read from config, never a literal (anti-goal: No magic numbers)."""
    closes = _vcp_closes()
    vols = _flat_volumes(closes)
    base_cfg = load_config().patterns.vcp
    assert detect_vcp(closes, closes, closes, vols, base_cfg)["flagged"] is True

    # recent/base volume ratio is ~0.54; demand <= 0.40 and the SAME series no longer qualifies
    stricter = base_cfg.model_copy(update={"volume_dryup_ratio": 0.40})
    assert detect_vcp(closes, closes, closes, vols, stricter)["flagged"] is False


def test_detect_vcp_is_deterministic():
    cfg = load_config().patterns.vcp
    closes = _vcp_closes()
    vols = _flat_volumes(closes)
    assert detect_vcp(closes, closes, closes, vols, cfg) == detect_vcp(closes, closes, closes, vols, cfg)


# =====================================================================================================
# iter-9: pullback-to-rising-DMA detector — same pure/deterministic/config-driven proofs as VCP (J-28)
# =====================================================================================================
def _pullback_closes() -> list[float]:
    """A 110-bar steady rise (so the 50-DMA is clearly rising) then a shallow 6-bar pullback that
    brings the latest close back down NEAR the rising MA — the textbook pulled-back-to-the-DMA shape."""
    rise = [80.0 + i * 0.5 for i in range(110)]      # 80 -> 134.5, steadily rising -> 50-DMA rises
    pullback = [134.0, 132.0, 130.0, 128.5, 127.5, 127.0]  # dip back toward the rising MA (~6% off the high)
    return rise + pullback


def test_constructed_pullback_series_flags_with_pivot_and_invalidation():
    cfg = load_config().patterns.pullback_to_rising_dma
    closes = _pullback_closes()
    res = detect_pullback_to_rising_dma(closes, closes, closes, [1000.0] * len(closes), cfg)

    assert res["flagged"] is True
    # invalidation level == the canonical rising MA (the SAME sma the chart/scoring use), not re-typed
    assert res["invalidation"]["level"] == ind.sma(closes, cfg.ma_period)
    # pivot == the recent (trend-lookback) high — reclaiming it resumes the trend
    assert res["pivot"] == max(closes[-cfg.trend_lookback_bars:])
    assert res["detail"]["slope_pct"] > cfg.min_dma_slope_pct      # the MA really is rising
    assert res["detail"]["pullback_depth_pct"] <= cfg.max_pullback_depth_pct
    assert "rising" in res["reason"] and f"{cfg.ma_period}-day MA" in res["reason"]
    assert f"${ind.sma(closes, cfg.ma_period):.2f}" in res["invalidation"]["note"]


def test_extended_uptrend_does_not_flag_pullback():
    """A steep monotonic rise leaves the close far ABOVE the rising MA (not pulled back) -> not flagged."""
    cfg = load_config().patterns.pullback_to_rising_dma
    closes = [80.0 + i for i in range(110)]  # close ~189 sits well above the lagging 50-DMA
    res = detect_pullback_to_rising_dma(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert res["flagged"] is False
    assert res["pivot"] is None and res["invalidation"]["level"] is None  # never fabricated


def test_downtrend_does_not_flag_pullback():
    """A falling MA is not a rising DMA -> the slope test fails -> not flagged."""
    cfg = load_config().patterns.pullback_to_rising_dma
    closes = [200.0 - i * 0.5 for i in range(116)]  # steady decline -> 50-DMA falling
    res = detect_pullback_to_rising_dma(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert res["flagged"] is False


def test_short_history_pullback_is_na_never_fabricated():
    cfg = load_config().patterns.pullback_to_rising_dma
    closes = [100.0 + i for i in range(cfg.min_history_bars - 1)]  # one bar short of min_history
    res = detect_pullback_to_rising_dma(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert res["flagged"] is False
    assert res["pivot"] is None and res["invalidation"]["level"] is None
    assert "Insufficient history" in res["reason"]


def test_pullback_detection_is_config_driven_not_hard_coded():
    """The SAME series flags under the real slope threshold but NOT under an impossibly steep one —
    proving min_dma_slope_pct is read from config, never a literal (anti-goal: No magic numbers)."""
    closes = _pullback_closes()
    vols = [1000.0] * len(closes)
    base_cfg = load_config().patterns.pullback_to_rising_dma
    assert detect_pullback_to_rising_dma(closes, closes, closes, vols, base_cfg)["flagged"] is True
    stricter = base_cfg.model_copy(update={"min_dma_slope_pct": 99.0})
    assert detect_pullback_to_rising_dma(closes, closes, closes, vols, stricter)["flagged"] is False


def test_detect_pullback_is_deterministic():
    cfg = load_config().patterns.pullback_to_rising_dma
    closes = _pullback_closes()
    vols = [1000.0] * len(closes)
    assert detect_pullback_to_rising_dma(closes, closes, closes, vols, cfg) == detect_pullback_to_rising_dma(
        closes, closes, closes, vols, cfg
    )


# =====================================================================================================
# iter-9: flat-base-breakout detector — same pure/deterministic/config-driven proofs as VCP (J-28)
# =====================================================================================================
_FLAT_BASE = [
    96, 98, 100, 97, 95, 99, 98, 96, 100, 97, 95, 98, 99, 96, 97, 100, 98, 95, 97, 99, 98, 96, 99, 97, 98,
]  # 25-bar base oscillating 95..100 (5% deep) — base high 100 is the pivot, base low 95 the invalidation


def _flat_base_series() -> list[float]:
    """A 20-bar advance into a 25-bar FLAT base (range 95..100) sitting AT the highs, the close (98)
    coiled just under the 100 pivot — the textbook breakout-ready flat base."""
    pre = [85.0 + i * 0.75 for i in range(20)]  # 85 -> ~99.25, all below the 100 base high
    return pre + [float(v) for v in _FLAT_BASE]


def _building_volumes(n: int) -> list[float]:
    """Volume building into the pivot: the last 10 bars trade above the earlier base average."""
    return [1000.0] * (n - 10) + [1300.0] * 10


def test_constructed_flat_base_series_flags_with_pivot_and_invalidation():
    cfg = load_config().patterns.flat_base_breakout
    closes = _flat_base_series()
    res = detect_flat_base_breakout(closes, closes, closes, _building_volumes(len(closes)), cfg)

    assert res["flagged"] is True
    assert res["pivot"] == max(closes[-cfg.base_window:]) == 100.0       # the base high (breakout level)
    assert res["invalidation"]["level"] == min(closes[-cfg.base_window:]) == 95.0  # the base low
    assert res["detail"]["base_depth_pct"] == 5.0                        # (100-95)/100
    assert res["detail"]["dist_below_pivot_pct"] == 2.0                  # close 98 -> 2% below the pivot
    assert "Flat" in res["reason"]
    assert "Flat-base breakout invalid below the base low at $95.00" == res["invalidation"]["note"]


def test_deep_base_does_not_flag_flat_base():
    """A base whose range exceeds max_base_depth_pct is not FLAT -> not flagged."""
    cfg = load_config().patterns.flat_base_breakout
    deep = [float(v) for v in [82, 90, 100, 84, 95, 100, 83, 92, 100, 85, 96, 99, 84, 97, 100, 86, 95, 100, 84, 98, 100, 83, 99, 96, 98]]
    closes = [70.0 + i * 0.5 for i in range(20)] + deep  # base range 82..100 ~ 18% deep > 15% max
    res = detect_flat_base_breakout(closes, closes, closes, _building_volumes(len(closes)), cfg)
    assert res["flagged"] is False
    assert res["pivot"] is None and res["invalidation"]["level"] is None  # never fabricated


def test_base_below_prior_high_does_not_flag_flat_base():
    """A flat base sitting BELOW a prior peak is not a base at the highs -> not flagged."""
    cfg = load_config().patterns.flat_base_breakout
    # a spike to 130 in the pre-window leaves the 95..100 base below the lookback high
    pre = [85.0] * 10 + [130.0] + [85.0] * 9
    closes = pre + [float(v) for v in _FLAT_BASE]
    res = detect_flat_base_breakout(closes, closes, closes, _building_volumes(len(closes)), cfg)
    assert res["flagged"] is False


def test_short_history_flat_base_is_na_never_fabricated():
    cfg = load_config().patterns.flat_base_breakout
    closes = [float(v) for v in range(cfg.min_history_bars - 1)]  # one bar short of min_history
    res = detect_flat_base_breakout(closes, closes, closes, [1000.0] * len(closes), cfg)
    assert res["flagged"] is False
    assert res["pivot"] is None and res["invalidation"]["level"] is None
    assert "Insufficient history" in res["reason"]


def test_flat_base_detection_is_config_driven_not_hard_coded():
    """The SAME series flags under the real base-depth cap but NOT under an impossibly tight one —
    proving max_base_depth_pct is read from config, never a literal (anti-goal: No magic numbers)."""
    closes = _flat_base_series()
    vols = _building_volumes(len(closes))
    base_cfg = load_config().patterns.flat_base_breakout
    assert detect_flat_base_breakout(closes, closes, closes, vols, base_cfg)["flagged"] is True
    stricter = base_cfg.model_copy(update={"max_base_depth_pct": 1.0})
    assert detect_flat_base_breakout(closes, closes, closes, vols, stricter)["flagged"] is False


def test_flat_base_volume_floor_is_config_driven():
    """A base with QUIET recent volume (below the base average) fails the building-volume floor —
    proving min_breakout_volume_ratio gates from config (volume part of price+VOLUME only)."""
    cfg = load_config().patterns.flat_base_breakout
    closes = _flat_base_series()
    quiet = [1000.0] * (len(closes) - 10) + [600.0] * 10  # recent volume DROPS below the base average
    assert detect_flat_base_breakout(closes, closes, closes, quiet, cfg)["flagged"] is False


def test_detect_flat_base_is_deterministic():
    cfg = load_config().patterns.flat_base_breakout
    closes = _flat_base_series()
    vols = _building_volumes(len(closes))
    assert detect_flat_base_breakout(closes, closes, closes, vols, cfg) == detect_flat_base_breakout(
        closes, closes, closes, vols, cfg
    )
