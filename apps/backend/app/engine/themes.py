"""Theme leadership engine — the canonical Theme Score (Data Contract: app.engine.themes),
served only by `GET /api/themes` (anti-goal: Single source of truth).

`score_themes(session, asof)` ranks every theme in `config.themes` by a 0-100 **price-confirmed**
Theme Score — a config-weighted blend of each theme's CROSS-SECTIONAL percentile (across themes)
on four price components: equal-weight basket RS-vs-SPY over 1m and 3m, member breadth above the
50-DMA (universe-relative), and mean member MA-stack participation. It is NOT news-driven. Weights
come from `config.theme_scores.weights`; the trend label from `config.theme_scores.trend_edges`
(via the shared `labels.label_for`); the A-E bucket from the single `to_bucket`.

Each row also exposes display fields: member tickers, 1m and 3m basket return (%), member breadth
(%), and the trend label. A theme whose members lack history reports NA for the affected component
(graceful, never fabricated). All bars read through `bars_asof` (no lookahead). Numeric literals
here are structural only (0/1/2/4/100); every period comes from config.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlmodel import Session

from app.config import Config, get_config
from app.engine import indicators as ind
from app.engine.buckets import to_bucket
from app.engine.labels import label_for
from app.engine.normalize import cross_sectional_percentiles
from app.engine.prices import bars_asof, closes

# the four theme-score components (keys match config.theme_scores.weights)
RS_1M, RS_3M, BREADTH, MA_PART = "rs_spy_1m", "rs_spy_3m", "breadth", "ma_participation"


def theme_name(slug: str) -> str:
    """Display name for a theme slug — the SINGLE naming derivation, shared by `score_themes`
    (theme rows) and `score_stocks` (per-stock theme-membership chips) so a theme reads identically
    on the Themes leaderboard and on a Stock Detail chip."""
    return slug.replace("_", " ").title()


def total_return(series: list[float], window: int) -> Optional[float]:
    """Multiplicative total return over `window` bars (e.g. 1.05 = +5%). NA if fewer than
    `window`+1 bars or the base price is zero (never fabricated)."""
    if len(series) < window + 1:
        return None
    base = series[-1 - window]
    if base == 0:
        return None
    return series[-1] / base


def basket_return(session: Session, members: list[str], asof: date_cls, window: int) -> Optional[float]:
    """Equal-weight basket multiplicative return over `window` bars — the mean of each member's
    own total return (members lacking history are excluded). NA if no member qualifies. Shared
    with `scoring.py` (the `rs_theme` component) so a theme's basket math has one definition."""
    returns: list[float] = []
    for ticker in members:
        ret = total_return(closes(bars_asof(session, ticker, asof)), window)
        if ret is not None:
            returns.append(ret)
    return (sum(returns) / len(returns)) if returns else None


def members_above_ma(session: Session, members: list[str], asof: date_cls, period: int) -> tuple[int, int]:
    """(# members whose latest close is above their `period`-DMA, # members evaluable).
    Universe-relative breadth — members without enough history are not counted in either total."""
    above = evaluated = 0
    for ticker in members:
        series = closes(bars_asof(session, ticker, asof))
        ma = ind.sma(series, period)
        if ma is not None:
            evaluated += 1
            if series[-1] > ma:
                above += 1
    return above, evaluated


def _mean_member_ma_stack(session: Session, members: list[str], asof: date_cls, periods: list[int]) -> Optional[float]:
    """Mean bullish MA-stack fraction across members with enough history. NA if none qualify."""
    values: list[float] = []
    for ticker in members:
        stack = ind.ma_stack(closes(bars_asof(session, ticker, asof)), periods)
        if stack is not None:
            values.append(stack)
    return (sum(values) / len(values)) if values else None


def score_themes(session: Session, asof: date_cls, config: Optional[Config] = None) -> dict:
    """Compute the canonical Theme leadership ranking as of `asof`. Deterministic on the seed."""
    cfg = config or get_config()
    weights = cfg.theme_scores.weights
    icfg = cfg.indicators
    benchmark = cfg.etfs.index[0]  # SPY
    spy = closes(bars_asof(session, benchmark, asof))
    window_1m = icfg.rs_windows["1m"]
    window_3m = icfg.rs_windows["3m"]
    spy_1m = total_return(spy, window_1m)
    spy_3m = total_return(spy, window_3m)

    raws: dict[str, dict] = {}
    display: dict[str, dict] = {}
    for slug, members in cfg.themes.items():
        basket_1m = basket_return(session, members, asof, window_1m)
        basket_3m = basket_return(session, members, asof, window_3m)
        rs_1m = (basket_1m / spy_1m) if (basket_1m is not None and spy_1m not in (None, 0)) else None
        rs_3m = (basket_3m / spy_3m) if (basket_3m is not None and spy_3m not in (None, 0)) else None
        above, evaluated = members_above_ma(session, members, asof, icfg.breadth_short_ma)
        breadth = (above / evaluated) if evaluated else None
        ma_part = _mean_member_ma_stack(session, members, asof, icfg.ma_periods)
        raws[slug] = {RS_1M: rs_1m, RS_3M: rs_3m, BREADTH: breadth, MA_PART: ma_part}
        display[slug] = {
            "members": list(members),
            "return_1m": round((basket_1m - 1) * 100, 2) if basket_1m is not None else None,
            "return_3m": round((basket_3m - 1) * 100, 2) if basket_3m is not None else None,
            "breadth_pct": round(breadth * 100, 2) if breadth is not None else None,
        }

    # cross-sectional percentile per component (only over themes where it is available)
    percentiles: dict[str, dict[str, float]] = {}
    for component in weights:
        present = {slug: raw[component] for slug, raw in raws.items() if raw[component] is not None}
        percentiles[component] = cross_sectional_percentiles(present)

    rows: list[dict] = []
    for slug, members in cfg.themes.items():
        raw = raws[slug]
        available = [(component, percentiles[component].get(slug), weight) for component, weight in weights.items()]
        available_weight = sum(weight for _, pct, weight in available if pct is not None)
        if available_weight:
            score01 = sum(pct * weight for _, pct, weight in available if pct is not None) / available_weight
        else:
            score01 = 0
        score = round(score01 * 100, 2)

        components = []
        for component, pct, weight in available:
            if pct is None:
                components.append({
                    "name": component, "raw": None, "percentile": None,
                    "weight": weight, "contribution": None, "available": False,
                })
            else:
                contribution = round((pct * weight / available_weight) * 100, 2) if available_weight else 0
                components.append({
                    "name": component, "raw": round(raw[component], 4),
                    "percentile": round(pct, 4), "weight": weight,
                    "contribution": contribution, "available": True,
                })

        info = display[slug]
        rows.append({
            "slug": slug,
            "name": theme_name(slug),
            "score": score,
            "bucket": to_bucket(score, cfg),
            "members": info["members"],
            "return_1m": info["return_1m"],
            "return_3m": info["return_3m"],
            "breadth_pct": info["breadth_pct"],
            "breadth_label": "universe-relative",
            "trend_label": label_for(score, cfg.theme_scores.trend_edges),
            "components": components,
            "rank": None,
        })

    rows.sort(key=lambda row: (-row["score"], row["slug"]))
    for index, row in enumerate(rows):
        row["rank"] = index + 1

    return {"asof_date": asof.isoformat(), "rows": rows}
