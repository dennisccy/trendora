"""Sector/industry leadership engine — the canonical Sector Score (Data Contract:
app.engine.sectors), served only by `GET /api/sectors` (anti-goal: Single source of truth).

`score_sectors(session, asof)` ranks every sector ETF (the 11 GICS SPDRs, kind="sector") and
industry-group ETF (kind="industry") by a 0-100 **Sector Score**. The score is a config-weighted
blend of each row's CROSS-SECTIONAL percentile on six leadership components (RS-vs-SPY over
1m/3m/6m, MA-stack, distance-from-52w-high, volume-trend) — leadership is inherently relative, so
ranking peers needs no magic scale constant. Weights come from `config.sectors.weights`; the
trend label from `config.sectors.trend_edges`; the A-E bucket from the single `to_bucket`.

SPY is the RS benchmark and is NOT ranked (it lives in `etfs.index`, never in the ranked rows).
Short-history ETFs (< `config.indicators.min_history_bars` bars) report NA for their long-window
components (6m RS, 52w-high distance) — handled gracefully, never fabricated. All bars are read
through `bars_asof` (no lookahead). Numeric literals here are structural only (0/1/2/4/100).
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Optional

from sqlmodel import Session

from app.config import Config, get_config
from app.engine import indicators as ind
from app.engine.buckets import to_bucket
from app.engine.labels import label_for
from app.engine.prices import bars_asof, closes, volumes

# component key -> the human ordering is given by config.sectors.weights; these are the six
# canonical leadership components (each "higher raw = stronger").
RS_1M, RS_3M, RS_6M = "rs_spy_1m", "rs_spy_3m", "rs_spy_6m"
MA_STACK, DIST_FROM_HIGH, VOL_TREND = "ma_stack", "dist_from_high", "vol_trend"


def _raw_components(session: Session, asof: date_cls, ticker: str, bench_closes: list[float], cfg: Config) -> dict:
    """Raw (un-normalized) component values for one ETF. Long-window components are NA when the
    symbol has fewer than `min_history_bars` bars (graceful, never fabricated)."""
    icfg = cfg.indicators
    bars = bars_asof(session, ticker, asof)
    series = closes(bars)
    vols = volumes(bars)
    long_ok = len(series) >= icfg.min_history_bars
    return {
        RS_1M: ind.rs_vs(series, bench_closes, icfg.rs_windows["1m"]),
        RS_3M: ind.rs_vs(series, bench_closes, icfg.rs_windows["3m"]),
        RS_6M: ind.rs_vs(series, bench_closes, icfg.rs_windows["6m"]) if long_ok else None,
        MA_STACK: ind.ma_stack(series, icfg.ma_periods),
        DIST_FROM_HIGH: ind.dist_from_high(series, icfg.high_window_52w) if long_ok else None,
        VOL_TREND: ind.vol_trend(vols, icfg.vol_avg_period),
    }


def _percentiles(values_by_ticker: dict[str, float]) -> dict[str, float]:
    """Cross-sectional percentile in [0,1] (highest raw -> 1.0). Ties broken by ticker so the
    output is deterministic on the frozen seed."""
    ordered = sorted(values_by_ticker.items(), key=lambda kv: (kv[1], kv[0]))
    count = len(ordered)
    result: dict[str, float] = {}
    for index, (ticker, _) in enumerate(ordered):
        result[ticker] = (index / (count - 1)) if count > 1 else 1
    return result


def score_sectors(session: Session, asof: date_cls, config: Optional[Config] = None) -> dict:
    """Compute the canonical Sector/industry leadership ranking as of `asof`."""
    cfg = config or get_config()
    weights = cfg.sectors.weights
    benchmark = cfg.etfs.index[0]  # SPY — the RS benchmark; excluded from the ranked rows
    bench_closes = closes(bars_asof(session, benchmark, asof))

    targets: list[tuple[str, str, str]] = []
    for ticker, sector_name in cfg.etfs.sector.items():
        targets.append((ticker, "sector", sector_name))
    for ticker in cfg.etfs.industry:
        targets.append((ticker, "industry", ticker))

    raws = {
        ticker: _raw_components(session, asof, ticker, bench_closes, cfg)
        for ticker, _, _ in targets
    }

    # cross-sectional percentile per component (only over rows where the component is available)
    percentiles: dict[str, dict[str, float]] = {}
    for component in weights:
        present = {ticker: raw[component] for ticker, raw in raws.items() if raw[component] is not None}
        percentiles[component] = _percentiles(present)

    rows: list[dict] = []
    for ticker, kind, name in targets:
        raw = raws[ticker]
        available = [
            (component, percentiles[component].get(ticker), weight)
            for component, weight in weights.items()
        ]
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

        rs3 = raw[RS_3M]
        dist = raw[DIST_FROM_HIGH]
        rows.append({
            "ticker": ticker,
            "kind": kind,
            "name": name,
            "score": score,
            "bucket": to_bucket(score, cfg),
            "rs_vs_spy": round((rs3 - 1) * 100, 2) if rs3 is not None else None,
            "dist_from_52w_high_pct": round(dist, 2) if dist is not None else None,
            "trend_label": label_for(score, cfg.sectors.trend_edges),
            "components": components,
            "rank": None,
        })

    rows.sort(key=lambda row: (-row["score"], row["ticker"]))
    for index, row in enumerate(rows):
        row["rank"] = index + 1

    return {"asof_date": asof.isoformat(), "benchmark": benchmark, "rows": rows}
