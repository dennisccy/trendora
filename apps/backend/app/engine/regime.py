"""Market Regime engine — the canonical Market Regime value (Data Contract: app.engine.regime).

`score_regime(session, asof)` produces the regime score (0-100) + one of the six configured
labels, computed EXACTLY ONCE here and served only by `GET /api/dashboard` (anti-goal: Single
source of truth). All inputs read bars through `bars_asof` (date <= asof; anti-goal: No
lookahead). Every period/weight/threshold comes from config (anti-goal: No magic numbers) — the
only numeric literals in this module are structural (0/1/2 arithmetic and 100, the percent unit).

Inputs (weights from `config.regime.weights`):
  - index MA-stack: mean bullish-stack fraction across the broad-index ETFs (SPY/QQQ/IWM/RSP).
  - universe breadth above the short/long DMA (universe-relative).
  - universe-relative net new-high/new-low.
  - VIX gate: dampens the risk-on score when ^VIX is above `config.regime.vix_threshold`
    (continuous, using only the threshold + the live VIX — no extra constant).
Breadth and new-high/low are UNIVERSE-RELATIVE (the seed universe, not full-market internals)
and are labelled as such wherever displayed.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlmodel import Session

from app.config import Config, get_config
from app.engine import indicators as ind
from app.engine.labels import label_for
from app.engine.prices import bars_asof_window, close_on, closes


def _pct(fraction: Optional[float]) -> Optional[float]:
    return round(fraction * 100, 2) if fraction is not None else None


def _index_ma_stack(session: Session, asof: date_cls, cfg: Config) -> Optional[float]:
    """Mean bullish MA-stack fraction across the configured broad-index ETFs.

    iter-27 (J-16 memory fix): `ma_stack` only ever reads a trailing window off the end of `closes`
    (the longest configured MA period), so this reads through the bounded `bars_asof_window` — trailing
    `cfg.indicators.max_lookback_bars` bars, the canonical bound already validated `>= max(ma_periods)`
    (`IndicatorsCfg._validate`) — instead of `bars_asof`'s whole `<= asof` prefix. Byte-identical result
    (`bars_asof_window(...) == bars_asof(...)[-max_lookback_bars:]` by construction); see
    `test_scoring_window.py`."""
    values: list[float] = []
    lookback = cfg.indicators.max_lookback_bars
    for symbol in cfg.etfs.index:
        bars = bars_asof_window(session, symbol, asof, lookback)
        stack = ind.ma_stack(closes(bars), cfg.indicators.ma_periods)
        if stack is not None:
            values.append(stack)
    return (sum(values) / len(values)) if values else None


def _universe_stats(session: Session, asof: date_cls, cfg: Config) -> dict:
    """Single pass over the universe: breadth above the short/long DMA + net new-high/low.
    Symbols without enough history for a given metric are excluded from that metric's
    denominator (universe-relative, never fabricated).

    iter-27 (J-16 memory fix): every metric below reads only a trailing window off the end of `series`
    (`sma`'s `breadth_short_ma`/`breadth_long_ma`, and the `high_window_52w`-bar `window` slice) — so
    this reads through the bounded `bars_asof_window` (trailing `max_lookback_bars` = 320 bars) instead
    of `bars_asof`'s whole `<= asof` prefix (up to ~5,300 bars on a late date, per symbol, across the
    full universe — the dominant per-(symbol,date) VSZ driver on the full-universe rebuild). `320 >=
    breadth_long_ma (200)` and `320 >= high_window_52w (252)` (validated: both are covered by
    `max(ma_periods)=200`/`high_window_52w` in `IndicatorsCfg._validate`'s `max_needed`), so `len(series)
    >= icfg.high_window_52w` and `series[-icfg.high_window_52w:]` below stay byte-identical — windowing
    only truncates bars OLDER than the tail these reads ever touch."""
    icfg = cfg.indicators
    above_short = above_long = new_highs = new_lows = 0
    eval_short = eval_long = eval_hl = 0
    lookback = icfg.max_lookback_bars
    for symbol in cfg.universe.symbols:
        series = closes(bars_asof_window(session, symbol, asof, lookback))
        if not series:
            continue
        last = series[-1]
        ma_short = ind.sma(series, icfg.breadth_short_ma)
        if ma_short is not None:
            eval_short += 1
            if last > ma_short:
                above_short += 1
        ma_long = ind.sma(series, icfg.breadth_long_ma)
        if ma_long is not None:
            eval_long += 1
            if last > ma_long:
                above_long += 1
        if len(series) >= icfg.high_window_52w:
            window = series[-icfg.high_window_52w:]
            eval_hl += 1
            if last >= max(window):
                new_highs += 1
            elif last <= min(window):
                new_lows += 1
    breadth_short = (above_short / eval_short) if eval_short else None
    breadth_long = (above_long / eval_long) if eval_long else None
    net = ((new_highs - new_lows) / eval_hl) if eval_hl else 0
    return {
        "breadth_short": breadth_short,
        "breadth_long": breadth_long,
        "new_highs": new_highs,
        "new_lows": new_lows,
        "evaluated_hl": eval_hl,
        "net": net,
    }


def _latest_vix(session: Session, asof: date_cls, cfg: Config) -> Optional[float]:
    """iter-27 (J-16 memory fix): the old body (`closes(bars_asof(...))[-1]`) built the WHOLE `<= asof`
    prefix only to read its last close. `close_on` is the already-optimized (iter-26) single-value
    accessor for exactly this read — O(1) via `_BarCache.close_on`'s bisect+index when a cache is
    active, a single-row `LIMIT 1` query otherwise — byte-identical (same `<= asof` boundary, same
    "no bar -> None" behavior as the old empty-series check)."""
    symbols = cfg.etfs.volatility
    if not symbols:
        return None
    return close_on(session, symbols[0], asof)


def score_regime(session: Session, asof: date_cls, config: Optional[Config] = None) -> dict:
    """Compute the canonical Market Regime value as of `asof`. Deterministic on the frozen seed."""
    cfg = config or get_config()
    weights = cfg.regime.weights

    index_ma_stack = _index_ma_stack(session, asof, cfg)
    stats = _universe_stats(session, asof, cfg)
    new_high_low_norm = (stats["net"] + 1) / 2  # net in [-1,1] -> [0,1]

    inputs = [
        ("index_ma_stack", index_ma_stack, weights["index_ma_stack"]),
        ("breadth_above_50dma", stats["breadth_short"], weights["breadth_above_50dma"]),
        ("breadth_above_200dma", stats["breadth_long"], weights["breadth_above_200dma"]),
        ("new_high_low", new_high_low_norm, weights["new_high_low"]),
    ]
    available = [(name, value, weight) for name, value, weight in inputs if value is not None]
    available_weight = sum(weight for _, _, weight in available)
    base = (sum(value * weight for _, value, weight in available) / available_weight) if available_weight else 0
    base_score = base * 100  # [0,100] before the VIX gate

    vix_close = _latest_vix(session, asof, cfg)
    vix_threshold = cfg.regime.vix_threshold
    if vix_close is not None and vix_close > 0:
        vix_factor = min(1, vix_threshold / vix_close)  # <= 1 once VIX exceeds the threshold
    else:
        vix_factor = 1
    vix_elevated = vix_close is not None and vix_close > vix_threshold

    score = max(0, min(100, round(base_score * vix_factor, 2)))
    label = label_for(score, cfg.regime.label_edges)

    components = []
    for name, value, weight in inputs:
        if value is None:
            components.append({
                "name": name, "value": None, "weight": weight,
                "contribution": None, "available": False,
            })
        else:
            contribution = round((value * weight / available_weight) * 100, 2) if available_weight else 0
            components.append({
                "name": name, "value": round(value, 4), "weight": weight,
                "contribution": contribution, "available": True,
            })
    components.append({
        "name": "vix_gate",
        "value": round(vix_close, 2) if vix_close is not None else None,
        "threshold": vix_threshold,
        "factor": round(vix_factor, 4),
        "elevated": vix_elevated,
        "contribution": round(score - base_score, 2),
        "available": vix_close is not None,
    })

    return {
        "score": score,
        "label": label,
        "breadth_above_50dma": _pct(stats["breadth_short"]),
        "breadth_above_200dma": _pct(stats["breadth_long"]),
        "new_high_low": {
            "new_highs": stats["new_highs"],
            "new_lows": stats["new_lows"],
            "evaluated": stats["evaluated_hl"],
            "net_pct": round(stats["net"] * 100, 2),
            "universe_relative": True,
        },
        "components": components,
        "asof_date": asof.isoformat(),
        "universe_relative": True,
    }
