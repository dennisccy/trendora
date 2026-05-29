"""GET /api/dashboard — the CANONICAL endpoint for the Market Regime value + the candidate counts.

Serves the regime panel computed once by `app.engine.regime.score_regime`, the universe-relative
breadth (also from the regime engine — never recomputed here), and — wired in iter-3 — the
**candidate counts** derived once by `app.engine.setups.summarize_candidates` from the canonical
`score_stocks` rows (counting the per-stock setup statuses; the iter-5 scanner must READ these,
never recompute). Single source of truth holds throughout.

NOT served here (each has exactly one serving path):
  - **Top Sectors** → the frontend reads the canonical `GET /api/sectors` and slices the top N.
  - **Top Themes** → the frontend reads the canonical `GET /api/themes` and slices the top N
    (exactly as Top Sectors does). The Theme Score is therefore NOT re-served from this endpoint —
    that would be a second serving path for a contract value (blueprint Data Contract).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.regime import score_regime
from app.engine.scoring import score_stocks
from app.engine.setups import summarize_candidates

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session)) -> dict:
    asof = latest_data_date(session)
    if asof is None:
        raise HTTPException(status_code=503, detail="no price data available")
    cfg = get_config()
    regime = score_regime(session, asof, cfg)
    # candidate counts: the SINGLE place they are derived — counting the canonical per-stock
    # setup statuses from score_stocks (re-format, not a second computation).
    candidate_counts = summarize_candidates(score_stocks(session, asof, cfg)["rows"])
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
        "candidate_counts": candidate_counts,
    }
