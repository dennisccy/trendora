"""Detected price patterns (Data Contract: app.engine.patterns).

This module holds the config-driven price-pattern detectors. The FIRST is VCP (iter-11);
iter-9 adds two MORE — `detect_pullback_to_rising_dma` and `detect_flat_base_breakout` — each held
to the IDENTICAL contract: pure, deterministic, **price+volume only**, NA-graceful, config-driven
(EVERY threshold from `config.patterns.<name>`; only structural literals 0/1/2/4/100 in code), reading
ONLY the passed as-of series (date <= D, no lookahead), and returning the SAME dict shape so every
caller reads ONE contract. Each is a PATTERN, not a status: it rides ALONGSIDE the setup status, never
enters the setup-status enum, and never by itself promotes a name to Actionable. On insufficient
history or no qualifying pattern each returns `flagged=False` with an honest reason and NO fabricated
pivot/invalidation level (anti-goal: No fabricated data).

`detect_vcp(closes, highs, lows, volumes, cfg)` is a pure, deterministic, **price+volume only**,
NA-graceful, config-driven detector of the Volatility Contraction Pattern: a sequence of
progressively-shallower pullbacks (contractions) with volume drying up into a pivot near the base
high. It reads ONLY the passed series — which the caller derives from `bars_asof` (date <= D) — so a
flag for a snapshot dated D uses NO future bar (anti-goal: No lookahead). EVERY threshold comes from
`config.patterns.vcp`; the only numeric literals here are structural (0/1/2/4 for indexing, arithmetic
and rounding precision; 100 for the percent unit) — no detection tunable is hard-coded (anti-goal:
No magic numbers).

VCP is a PATTERN, not a status: the returned flag + evidence ride each stock row ALONGSIDE the setup
status — it never enters the setup-status enum and never by itself promotes a name to Actionable
(anti-goal: VCP is a pattern, not a status). On insufficient history or no qualifying base the
detector returns `flagged=False` with an honest reason and NO fabricated pivot/invalidation level
(anti-goal: No fabricated data).

Returned dict shape (the same whether flagged or not, so every caller reads one contract):
    {
      "flagged": bool,
      "reason": str,                 # plain-language, server-built (rendered verbatim by the UI)
      "pivot": float | None,         # the breakout level = the base high (None when not flagged)
      "invalidation": {"level": float | None, "note": str},  # last-contraction low + verbatim sentence
      "contractions": list[float],   # detected contraction depths (percent); [] when not flagged
      "detail": dict,                # n_contractions, volume_ratio, dist_from_pivot_pct (explainability)
    }
"""
from __future__ import annotations

from typing import Optional, Sequence

from app.config import FlatBaseBreakoutCfg, PullbackToRisingDmaCfg, VcpCfg
from app.engine import indicators as ind


def _not_flagged(reason: str, detail: Optional[dict] = None) -> dict:
    """A not-flagged VCP result: an honest reason and NO fabricated pivot/level (anti-goal: No
    fabricated data). `detail` carries whatever diagnostics were computed before the disqualifying
    test (or empties when history was too short to evaluate anything)."""
    return {
        "flagged": False,
        "reason": reason,
        "pivot": None,
        "invalidation": {"level": None, "note": "No VCP pattern detected."},
        "contractions": [],
        "detail": detail or {"n_contractions": 0, "volume_ratio": None, "dist_from_pivot_pct": None},
    }


def _swing_pivots(highs: Sequence[float], lows: Sequence[float], reversal_pct: float) -> list[tuple[str, float]]:
    """Alternating swing pivots via a percent-reversal ZigZag (reversal threshold = `reversal_pct`),
    oldest->newest, each `("H"|"L", price)`. A swing HIGH is confirmed when price falls >= `reversal_pct`
    below the running high; a swing LOW when it rises >= `reversal_pct` above the running low. Because a
    swing only registers after a real reversal, the detector sees contractions formed by LOWER highs
    coiling below an established pivot (the canonical VCP shape), not only pullbacks between equal/higher
    highs — and a smooth uptrend (no reversal) yields no swing-high/low pair. Pure; depends only on the
    passed series."""
    pivots: list[tuple[str, float]] = []
    hi = highs[0]
    lo = lows[0]
    direction = 0  # 0 undecided; 1 up-swing (seeking a swing high); -1 down-swing (seeking a swing low)
    for i in range(1, len(highs)):
        if highs[i] > hi:
            hi = highs[i]
        if lows[i] < lo:
            lo = lows[i]
        if direction >= 0 and hi > 0 and (hi - lows[i]) / hi * 100 >= reversal_pct:
            pivots.append(("H", hi))
            direction = -1
            lo = lows[i]
        elif direction <= 0 and lo > 0 and (highs[i] - lo) / lo * 100 >= reversal_pct:
            pivots.append(("L", lo))
            direction = 1
            hi = highs[i]
    return pivots


def _contractions(highs: Sequence[float], lows: Sequence[float], min_contraction_pct: float) -> list[dict]:
    """The base's pullback depths (percent), oldest->newest: each confirmed swing HIGH to the FOLLOWING
    swing LOW is one contraction (depth = (peak - trough) / peak * 100); the most recent H->L is the
    final (tightest) contraction. Swings are detected by `_swing_pivots` with `min_contraction_pct` as
    the reversal threshold, so a pullback shallower than that is noise and never becomes a contraction.
    Each entry is {depth_pct, peak, trough}. Pure — depends only on the passed series."""
    pivots = _swing_pivots(highs, lows, min_contraction_pct)
    contractions: list[dict] = []
    for j in range(len(pivots) - 1):
        kind, peak = pivots[j]
        next_kind, trough = pivots[j + 1]
        if kind == "H" and next_kind == "L" and peak > 0:
            contractions.append({"depth_pct": (peak - trough) / peak * 100, "peak": peak, "trough": trough})
    return contractions


def detect_vcp(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    volumes: Sequence[float],
    cfg: VcpCfg,
) -> dict:
    """Detect a VCP from the as-of series (date <= D), using ONLY `config.patterns.vcp` thresholds.

    Flagged only when ALL hold: at least `min_contractions` (and at most `max_contractions`, the most
    recent) qualifying contractions; the deepest <= `max_base_depth_pct`; each <= the prior *
    `contraction_shrink_ratio` (progressively tightening); the final <= `max_last_contraction_pct`;
    the latest close within `pivot_proximity_pct` below the base high; and recent volume (over
    `volume_window` bars) <= `volume_dryup_ratio` of the base average (volume drying up)."""
    n = len(closes)
    if n == 0 or n < cfg.min_history_bars:
        return _not_flagged(
            f"Insufficient history ({n} bars) to evaluate VCP — needs at least {cfg.min_history_bars}."
        )

    window = min(cfg.lookback_bars, n)
    w_highs = list(highs[-window:])
    w_lows = list(lows[-window:])
    w_vols = list(volumes[-window:])
    last_close = closes[-1]
    base_high = max(w_highs)

    contractions = _contractions(w_highs, w_lows, cfg.min_contraction_pct)
    # consider at most the most recent `max_contractions` (those nearest the pivot)
    if len(contractions) > cfg.max_contractions:
        contractions = contractions[-cfg.max_contractions:]
    depths = [c["depth_pct"] for c in contractions]
    n_contractions = len(contractions)

    # explainability diagnostics — always computed, honest even when not flagged
    base_vol = (sum(w_vols) / len(w_vols)) if w_vols else None
    recent_window = min(cfg.volume_window, len(w_vols))
    recent_vol = (sum(w_vols[-recent_window:]) / recent_window) if recent_window else None
    volume_ratio = (recent_vol / base_vol) if (base_vol not in (None, 0) and recent_vol is not None) else None
    dist_from_pivot_pct = ((base_high - last_close) / base_high * 100) if base_high else None
    detail = {
        "n_contractions": n_contractions,
        "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
        "dist_from_pivot_pct": round(dist_from_pivot_pct, 4) if dist_from_pivot_pct is not None else None,
    }

    # --- qualifying tests (every threshold from config) -------------------------------------
    if n_contractions < cfg.min_contractions:
        return _not_flagged(
            f"No VCP: only {n_contractions} qualifying contraction(s) in the base — needs {cfg.min_contractions}.",
            detail,
        )
    if max(depths) > cfg.max_base_depth_pct:
        return _not_flagged(
            f"No VCP: the base is too deep ({max(depths):.0f}% > {cfg.max_base_depth_pct:.0f}% max).",
            detail,
        )
    shrinking = all(depths[i + 1] <= depths[i] * cfg.contraction_shrink_ratio for i in range(len(depths) - 1))
    if not shrinking:
        return _not_flagged("No VCP: contractions are not progressively tightening.", detail)
    if depths[-1] > cfg.max_last_contraction_pct:
        return _not_flagged(
            f"No VCP: the final contraction ({depths[-1]:.0f}%) is wider than the "
            f"{cfg.max_last_contraction_pct:.0f}% pivot-tightness limit.",
            detail,
        )
    if dist_from_pivot_pct is None or dist_from_pivot_pct > cfg.pivot_proximity_pct:
        return _not_flagged(
            f"No VCP: price is not near the pivot ({dist_from_pivot_pct:.0f}% below the base high; "
            f"needs <= {cfg.pivot_proximity_pct:.0f}%)."
            if dist_from_pivot_pct is not None else "No VCP: pivot distance is NA.",
            detail,
        )
    if volume_ratio is None or volume_ratio > cfg.volume_dryup_ratio:
        return _not_flagged(
            f"No VCP: volume has not dried up (recent volume is {volume_ratio:.0%} of the base; "
            f"needs <= {cfg.volume_dryup_ratio:.0%})."
            if volume_ratio is not None else "No VCP: volume ratio is NA.",
            detail,
        )

    # --- flagged: a qualifying VCP ----------------------------------------------------------
    last_contraction_low = contractions[-1]["trough"]
    pivot = base_high
    contraction_str = "→".join(f"{d:.0f}%" for d in depths)
    reason = (
        f"{n_contractions} contractions tightening {contraction_str}, "
        f"volume drying up to {volume_ratio:.0%} of the base, "
        f"{dist_from_pivot_pct:.0f}% below the ${pivot:.2f} pivot."
    )
    invalidation = {
        "level": last_contraction_low,
        "note": f"VCP invalid below the last-contraction low at ${last_contraction_low:.2f}",
    }
    return {
        "flagged": True,
        "reason": reason,
        "pivot": pivot,
        "invalidation": invalidation,
        "contractions": [round(d, 2) for d in depths],
        "detail": detail,
    }


# --- iter-9: pullback to a rising DMA ---------------------------------------------------------
def _no_pullback(reason: str, detail: Optional[dict] = None) -> dict:
    """A not-flagged pullback-to-rising-DMA result: an honest reason, NO fabricated pivot/level
    (anti-goal: No fabricated data). Same contract dict shape as `detect_vcp` (minus VCP-only
    `contractions`)."""
    return {
        "flagged": False,
        "reason": reason,
        "pivot": None,
        "invalidation": {"level": None, "note": "No pullback-to-rising-DMA pattern detected."},
        "detail": detail
        or {"dma": None, "slope_pct": None, "dist_from_dma_pct": None, "pullback_depth_pct": None, "volume_ratio": None},
    }


def detect_pullback_to_rising_dma(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    volumes: Sequence[float],
    cfg: PullbackToRisingDmaCfg,
) -> dict:
    """Detect a pullback to a RISING moving average from the as-of series (date <= D), using ONLY
    `config.patterns.pullback_to_rising_dma` thresholds.

    Flagged only when ALL hold: the `ma_period`-day MA is computable now and `trend_lookback_bars`
    ago and has risen >= `min_dma_slope_pct` over that span (an established uptrend); the latest close
    is within `max_dist_above_dma_pct` ABOVE the MA and no more than `max_undercut_pct` below it (pulled
    back TO the MA, neither extended nor broken-down); and the pullback from the recent
    (`trend_lookback_bars`-bar) high is <= `max_pullback_depth_pct` (a pullback, not a crash). The pivot
    is the recent high (reclaiming it resumes the trend); invalidation is the rising MA itself. Recent
    volume over `volume_window` is reported for context — it does not gate the flag."""
    n = len(closes)
    if n == 0 or n < cfg.min_history_bars:
        return _no_pullback(
            f"Insufficient history ({n} bars) to evaluate the pullback-to-rising-DMA pattern — "
            f"needs at least {cfg.min_history_bars}."
        )

    dma_now = ind.sma(closes, cfg.ma_period)
    dma_then = ind.sma(closes[: n - cfg.trend_lookback_bars], cfg.ma_period)
    if dma_now is None or dma_then is None or dma_then == 0:
        return _no_pullback("No pullback-to-rising-DMA: the moving average is not computable over the lookback.")

    last_close = closes[-1]
    slope_pct = (dma_now - dma_then) / dma_then * 100
    dist_from_dma_pct = ((last_close - dma_now) / dma_now * 100) if dma_now else None  # + above / - below
    trend_highs = list(highs[-cfg.trend_lookback_bars:])
    recent_high = max(trend_highs) if trend_highs else None
    pullback_depth_pct = ((recent_high - last_close) / recent_high * 100) if recent_high else None

    # volume diagnostic (reported, not a gate): recent pullback volume vs the trend-window average
    trend_vols = list(volumes[-cfg.trend_lookback_bars:])
    trend_vol = (sum(trend_vols) / len(trend_vols)) if trend_vols else None
    recent_window = min(cfg.volume_window, len(trend_vols))
    recent_vol = (sum(trend_vols[-recent_window:]) / recent_window) if recent_window else None
    volume_ratio = (recent_vol / trend_vol) if (trend_vol not in (None, 0) and recent_vol is not None) else None

    detail = {
        "dma": round(dma_now, 4),
        "slope_pct": round(slope_pct, 4),
        "dist_from_dma_pct": round(dist_from_dma_pct, 4) if dist_from_dma_pct is not None else None,
        "pullback_depth_pct": round(pullback_depth_pct, 4) if pullback_depth_pct is not None else None,
        "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
    }

    # --- qualifying tests (every threshold from config) -------------------------------------
    if slope_pct < cfg.min_dma_slope_pct:
        return _no_pullback(
            f"No pullback-to-rising-DMA: the {cfg.ma_period}-day MA is not rising enough "
            f"({slope_pct:.1f}% over {cfg.trend_lookback_bars} bars; needs >= {cfg.min_dma_slope_pct:.1f}%).",
            detail,
        )
    if dist_from_dma_pct is None:
        return _no_pullback("No pullback-to-rising-DMA: distance from the MA is NA.", detail)
    if dist_from_dma_pct > cfg.max_dist_above_dma_pct:
        return _no_pullback(
            f"No pullback-to-rising-DMA: price is {dist_from_dma_pct:.1f}% above the MA — too extended "
            f"(needs <= {cfg.max_dist_above_dma_pct:.1f}% above).",
            detail,
        )
    if dist_from_dma_pct < -cfg.max_undercut_pct:
        return _no_pullback(
            f"No pullback-to-rising-DMA: price is {-dist_from_dma_pct:.1f}% below the MA — support broken "
            f"(tolerates <= {cfg.max_undercut_pct:.1f}% undercut).",
            detail,
        )
    if pullback_depth_pct is None or pullback_depth_pct > cfg.max_pullback_depth_pct:
        return _no_pullback(
            f"No pullback-to-rising-DMA: the pullback is too deep ({pullback_depth_pct:.0f}% off the "
            f"recent high; needs <= {cfg.max_pullback_depth_pct:.0f}%)."
            if pullback_depth_pct is not None else "No pullback-to-rising-DMA: pullback depth is NA.",
            detail,
        )

    # --- flagged: a qualifying pullback to a rising DMA -------------------------------------
    pivot = recent_high
    invalidation_level = dma_now  # the rising support being tested
    where = "above" if dist_from_dma_pct >= 0 else "below"
    volume_clause = f" on volume {volume_ratio:.0%} of the trend average." if volume_ratio is not None else "."
    reason = (
        f"Pulled back to a rising {cfg.ma_period}-day MA (up {slope_pct:.1f}% over "
        f"{cfg.trend_lookback_bars} bars); close {abs(dist_from_dma_pct):.1f}% {where} the MA, "
        f"{pullback_depth_pct:.0f}% off the recent high{volume_clause}"
    )
    invalidation = {
        "level": invalidation_level,
        "note": f"Pullback invalid on a decisive close below the rising {cfg.ma_period}-day MA at ${invalidation_level:.2f}",
    }
    return {"flagged": True, "reason": reason, "pivot": pivot, "invalidation": invalidation, "detail": detail}


# --- iter-9: flat-base breakout ---------------------------------------------------------------
def _no_flat_base(reason: str, detail: Optional[dict] = None) -> dict:
    """A not-flagged flat-base-breakout result: an honest reason, NO fabricated pivot/level
    (anti-goal: No fabricated data). Same contract dict shape as `detect_vcp` (minus VCP-only
    `contractions`)."""
    return {
        "flagged": False,
        "reason": reason,
        "pivot": None,
        "invalidation": {"level": None, "note": "No flat-base-breakout pattern detected."},
        "detail": detail or {"base_depth_pct": None, "dist_below_pivot_pct": None, "volume_ratio": None},
    }


def detect_flat_base_breakout(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    volumes: Sequence[float],
    cfg: FlatBaseBreakoutCfg,
) -> dict:
    """Detect a flat-base breakout setup from the as-of series (date <= D), using ONLY
    `config.patterns.flat_base_breakout` thresholds.

    Flagged only when ALL hold: the `base_window`-bar base is FLAT (high-to-low range <=
    `max_base_depth_pct`); the base sits AT the highs of the wider `lookback_bars` window (the base
    high is the window high — a continuation base, not a bottoming one); the latest close is within
    `pivot_proximity_pct` at/below the base high (coiled under the pivot, breakout-ready); and recent
    volume over `volume_window` is >= `min_breakout_volume_ratio` of the base average (volume building
    into the pivot). The pivot is the base high (the breakout level); invalidation is the base low."""
    n = len(closes)
    if n == 0 or n < cfg.min_history_bars:
        return _no_flat_base(
            f"Insufficient history ({n} bars) to evaluate the flat-base-breakout pattern — "
            f"needs at least {cfg.min_history_bars}."
        )

    window = min(cfg.lookback_bars, n)
    w_highs = list(highs[-window:])
    base_highs = list(highs[-cfg.base_window:])
    base_lows = list(lows[-cfg.base_window:])
    base_vols = list(volumes[-cfg.base_window:])
    last_close = closes[-1]
    base_high = max(base_highs)
    base_low = min(base_lows)
    lookback_high = max(w_highs)

    base_depth_pct = ((base_high - base_low) / base_high * 100) if base_high else None
    dist_below_pivot_pct = ((base_high - last_close) / base_high * 100) if base_high else None
    base_vol = (sum(base_vols) / len(base_vols)) if base_vols else None
    recent_window = min(cfg.volume_window, len(base_vols))
    recent_vol = (sum(base_vols[-recent_window:]) / recent_window) if recent_window else None
    volume_ratio = (recent_vol / base_vol) if (base_vol not in (None, 0) and recent_vol is not None) else None

    detail = {
        "base_depth_pct": round(base_depth_pct, 4) if base_depth_pct is not None else None,
        "dist_below_pivot_pct": round(dist_below_pivot_pct, 4) if dist_below_pivot_pct is not None else None,
        "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
    }

    # --- qualifying tests (every threshold from config) -------------------------------------
    if base_depth_pct is None:
        return _no_flat_base("No flat-base breakout: the base high is NA.", detail)
    if base_high < lookback_high:
        return _no_flat_base(
            f"No flat-base breakout: the base is below the {window}-bar high — not a base at the highs.",
            detail,
        )
    if base_depth_pct > cfg.max_base_depth_pct:
        return _no_flat_base(
            f"No flat-base breakout: the base is too deep ({base_depth_pct:.0f}% > "
            f"{cfg.max_base_depth_pct:.0f}% max).",
            detail,
        )
    if dist_below_pivot_pct is None or dist_below_pivot_pct > cfg.pivot_proximity_pct:
        return _no_flat_base(
            f"No flat-base breakout: price is not near the pivot ({dist_below_pivot_pct:.0f}% below the "
            f"base high; needs <= {cfg.pivot_proximity_pct:.0f}%)."
            if dist_below_pivot_pct is not None else "No flat-base breakout: pivot distance is NA.",
            detail,
        )
    if volume_ratio is None or volume_ratio < cfg.min_breakout_volume_ratio:
        return _no_flat_base(
            f"No flat-base breakout: volume is not building (recent volume is {volume_ratio:.0%} of the "
            f"base; needs >= {cfg.min_breakout_volume_ratio:.0%})."
            if volume_ratio is not None else "No flat-base breakout: volume ratio is NA.",
            detail,
        )

    # --- flagged: a qualifying flat-base breakout setup -------------------------------------
    pivot = base_high
    invalidation_level = base_low
    reason = (
        f"Flat {cfg.base_window}-bar base only {base_depth_pct:.0f}% deep at the {window}-bar highs, "
        f"{dist_below_pivot_pct:.0f}% below the ${pivot:.2f} pivot, "
        f"recent volume {volume_ratio:.0%} of the base."
    )
    invalidation = {
        "level": invalidation_level,
        "note": f"Flat-base breakout invalid below the base low at ${invalidation_level:.2f}",
    }
    return {"flagged": True, "reason": reason, "pivot": pivot, "invalidation": invalidation, "detail": detail}
