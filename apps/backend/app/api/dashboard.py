"""GET /api/dashboard — the CANONICAL and only endpoint for the Market Regime value.

Serves the regime panel computed once by `app.engine.regime.score_regime` (anti-goal: Single
source of truth) plus the universe-relative breadth and the data-as-of date. `candidate_counts`
and `top_themes` are returned EXPLICITLY null/pending — they depend on per-stock + theme scoring
that lands in iter-3, and must never be shown as a fabricated zero (anti-goal: No fabricated
data). The Dashboard's "Top Sectors" list is NOT served here: the frontend reads the canonical
`GET /api/sectors` and slices the top N, so the sector score has exactly one serving path.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session)) -> dict:
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    regime = score_regime(session, asof, get_config())
    return {
        "regime": {
            "score": regime["score"],
            "label": regime["label"],
            "components": regime["components"],
            "asof_date": regime["asof_date"],
        },
        "breadth": {
            "above_50dma_pct": regime["breadth_above_50dma"],
            "above_200dma_pct": regime["breadth_above_200dma"],
            "new_high_low": regime["new_high_low"],
            "label": "universe-relative",
        },
        "asof_date": regime["asof_date"],
        "candidate_counts": None,  # pending — per-stock setups arrive in iter-3
        "top_themes": None,        # pending — theme scoring arrives in iter-3
    }
