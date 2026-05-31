"""Detected price patterns — the FIRST is VCP (Data Contract: app.engine.patterns).

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

from app.config import VcpCfg


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
