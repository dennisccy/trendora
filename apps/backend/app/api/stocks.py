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
from app.engine.prices import latest_data_date
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
