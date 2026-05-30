"""GET /api/system-health — the forward-tested evidence dashboard source (Data Contract:
app.engine.forward_testing). Returns `compute_forward_aggregates(...)` VERBATIM — the SINGLE canonical
forward-return aggregation (forward return by bucket / setup / regime, excess vs SPY/QQQ, and the
control-group cohorts, each with sample size `n`, plus the survivorship-bias label and `min_sample`
threshold). The API re-serves stored evidence; it recomputes no return, excess, or bucket.

Query param `horizon` selects the forward window; it defaults to `config.walk_forward.default_horizon`
and MUST be one of `config.walk_forward.horizons`, else `422` (no fabricated horizon). `503` when no
price data exists at all (anti-goal: No fabricated data — never an invented evidence row).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import Config, get_config
from app.db import get_session
from app.engine.forward_testing import compute_forward_aggregates
from app.engine.prices import latest_data_date

router = APIRouter(tags=["system-health"])


@router.get("/system-health")
def system_health(
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the forward-tested evidence at the requested `horizon` (default = config default_horizon).
    Validates the horizon against `config.walk_forward.horizons` (422 otherwise); 503 when no price
    data exists. The payload is the canonical aggregation verbatim — never recomputed in the view."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    resolved = wf.default_horizon if horizon is None else horizon
    if resolved not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved}; valid horizons are {list(wf.horizons)}",
        )

    return compute_forward_aggregates(session, resolved, cfg)
