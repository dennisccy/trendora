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
from app.engine.prices import bars_asof, closes


def _pct(fraction: Optional[float]) -> Optional[float]:
    return round(fraction * 100, 2) if fraction is not None else None


def _index_ma_stack(session: Session, asof: date_cls, cfg: Config) -> Optional[float]:
    """Mean bullish MA-stack fraction across the configured broad-index ETFs."""
    values: list[float] = []
    for symbol in cfg.etfs.index:
        stack = ind.ma_stack(closes(bars_asof(session, symbol, asof)), cfg.indicators.ma_periods)
        if stack is not None:
            values.append(stack)
    return (sum(values) / len(values)) if values else None


def _universe_stats(session: Session, asof: date_cls, cfg: Config) -> dict:
    """Single pass over the universe: breadth above the short/long DMA + net new-high/low.
    Symbols without enough history for a given metric are excluded from that metric's
    denominator (universe-relative, never fabricated)."""
    icfg = cfg.indicators
    above_short = above_long = new_highs = new_lows = 0
    eval_short = eval_long = eval_hl = 0
    for symbol in cfg.universe.symbols:
        series = closes(bars_asof(session, symbol, asof))
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
    symbols = cfg.etfs.volatility
    if not symbols:
        return None
    series = closes(bars_asof(session, symbols[0], asof))
    return series[-1] if series else None


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
