"""GET /api/stocks (+ /{ticker}) — the CANONICAL and only endpoint for the per-stock scores
(Data Contract: app.engine.scoring).

iter-8: re-pointed to serve from the persisted IMMUTABLE snapshot for the resolved as-of date
(anti-goal: No recompute in the read path). Both routes resolve `?as_of=` to its stored `ScannerRun`
(latest by default; create-once for a not-yet-stored date) and serve that run's per-stock results
rehydrated from the lossless `record_json`. The list row and the detail row come from the SAME stored
row, so they are byte-identical (anti-goal: Single source of truth -> J-06). Because `run_scan` stored
faithful copies of `score_stocks`, the latest-date payload is byte-identical to the former on-request
compute. `503` when no price data exists, `404` for an unknown ticker, `4xx` for an invalid `as_of` —
never a fabricated row (anti-goal: No fabricated data).

`/stocks/{ticker}/bars` serves the raw price/MA/volume series. Raw bars are NOT a recomputed score, so
the chart endpoint needs no snapshot row — only the as-of slice (`bars_asof`, date <= D, no lookahead)
and the canonical server MA series. It accepts and validates `?as_of=` identically (the as-of chart).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.indicators import sma_series
from app.engine.prices import bars_asof, closes
from app.engine.snapshot_serving import resolved_date, resolved_run, stock_detail_payload, stocks_payload

router = APIRouter(tags=["stocks"])


@router.get("/stocks")
def stocks(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    return stocks_payload(session, resolved_run(session, as_of))


@router.get("/stocks/{ticker}")
def stock_detail(ticker: str, as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    # the SAME stored row the leaderboard serves — never recomputed per-ticker (J-06)
    return stock_detail_payload(session, resolved_run(session, as_of), ticker)


@router.get("/stocks/{ticker}/bars")
def stock_bars(ticker: str, as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    """Canonical price/MA/volume series for the Stock Detail chart, as-of the resolved date. OHLCV bars
    read ONLY via `bars_asof` (date <= as-of, no lookahead); the `ma` map is keyed by every
    `config.indicators.ma_periods` entry and holds the canonical `sma_series` aligned 1:1 with the bars
    (a number, or `null`/NA for the warm-up prefix and any short-history gap). The frontend plots this
    server series and never computes a moving average client-side. Mirrors the `/api/stocks/{ticker}`
    contract: `503` when no price data exists, `404` for an unknown ticker, `4xx` for an invalid `as_of`
    — never a fabricated row (anti-goal: No fabricated data)."""
    cfg = get_config()
    asof = resolved_date(session, as_of, cfg)
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
