"""GET /api/themes — the CANONICAL and only endpoint for the Theme Score (Data Contract:
app.engine.themes). Serves `score_themes(asof=latest_data_date)` verbatim — never recomputes or
reshapes a score (anti-goal: Single source of truth). The Dashboard's "Top Themes" reads THIS
endpoint and slices the top N (exactly as Top Sectors slices `/api/sectors`) — no second source.
`503` when no price data exists, so the frontend renders the explicit "Backend unavailable" state
rather than fabricated rows (anti-goal: No fabricated data).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.themes import score_themes

router = APIRouter(tags=["themes"])


@router.get("/themes")
def themes(session: Session = Depends(get_session)) -> dict:
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    return score_themes(session, asof, get_config())
