"""GET /api/stocks (+ /{ticker}) — the CANONICAL and only endpoint for the per-stock scores
(Data Contract: app.engine.scoring). Both routes serve `score_stocks(asof=latest_data_date)`
verbatim from the SAME computation, so the leaderboard row and the detail row are byte-identical
(anti-goal: Single source of truth → J-06). `503` when no price data exists, `404` for an unknown
ticker — never a fabricated row (anti-goal: No fabricated data). iter-3 computes on-request,
deterministically, from the frozen seed; persistence into snapshot tables arrives in iter-5.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.indicators import sma_series
from app.engine.prices import bars_asof, closes, latest_data_date
from app.engine.scoring import score_stocks

router = APIRouter(tags=["stocks"])


@router.get("/stocks")
def stocks(session: Session = Depends(get_session)) -> dict:
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    return score_stocks(session, asof, get_config())


@router.get("/stocks/{ticker}")
def stock_detail(ticker: str, session: Session = Depends(get_session)) -> dict:
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    result = score_stocks(session, asof, get_config())
    target = ticker.upper()
    for row in result["rows"]:
        if row["ticker"].upper() == target:
            # the SAME row object the leaderboard serves — never recomputed per-ticker (J-06)
            return {"asof_date": result["asof_date"], "benchmark": result["benchmark"], "row": row}
    raise HTTPException(status_code=404, detail=f"unknown ticker: {ticker}")


@router.get("/stocks/{ticker}/bars")
def stock_bars(ticker: str, session: Session = Depends(get_session)) -> dict:
    """Canonical price/MA/volume series for the Stock Detail chart. OHLCV bars read ONLY via
    `bars_asof` (date <= as-of, no lookahead); the `ma` map is keyed by every
    `config.indicators.ma_periods` entry and holds the canonical `sma_series` aligned 1:1 with the
    bars (a number, or `null`/NA for the warm-up prefix and any short-history gap). The frontend
    plots this server series and never computes a moving average client-side. Mirrors the
    `/api/stocks/{ticker}` contract: `503` when no price data exists, `404` for an unknown ticker —
    never a fabricated row (anti-goal: No fabricated data)."""
    cfg = get_config()
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    target = ticker.upper()
    symbol = next((s for s in cfg.universe.symbols if s.upper() == target), None)
    if symbol is None:
        raise HTTPException(status_code=404, detail=f"unknown ticker: {ticker}")
    bars = bars_asof(session, symbol, asof)
    if not bars:
        raise HTTPException(status_code=503, detail=f"no price data for {symbol}")
    closes_asof = closes(bars)
    return {
        "asof_date": asof.isoformat(),
        "ticker": symbol,
        "bars": [
            {
                "date": bar.date.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ],
        # one rolling MA series per configured period (no MA literal here — periods come from config)
        "ma": {str(period): sma_series(closes_asof, period) for period in cfg.indicators.ma_periods},
    }
