"""GET /api/sectors — the CANONICAL and only endpoint for the Sector Score (Data Contract).

Serves `score_sectors(asof=latest_data_date)` verbatim — it never recomputes or reshapes a score
(anti-goal: Single source of truth). When no price data exists it returns an explicit 503 so the
frontend renders the "Backend unavailable" state rather than fabricated rows (anti-goal: No
fabricated data). iter-2 computes on-request, deterministically, from the frozen seed; persistence
into the immutable snapshot tables arrives in iter-5.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.sectors import score_sectors

router = APIRouter(tags=["sectors"])


@router.get("/sectors")
def sectors(session: Session = Depends(get_session)) -> dict:
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    return score_sectors(session, asof, get_config())
