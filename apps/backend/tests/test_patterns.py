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
from app.engine.patterns import detect_vcp

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
