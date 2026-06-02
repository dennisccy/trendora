"""GET /api/research/factor-lab — the Factor Lab source (Data Contract: app.engine.research). Returns
`compute_factor_lab(...)` VERBATIM — the SINGLE canonical Factor-Lab analysis (per factor × horizon:
the decile table of mean forward return + a downside risk-adjusted column, each with `n`, plus the
factor's rank-IC). The view recomputes nothing; it serves a read-only aggregation of ALREADY-STORED
forward returns + factor values.

Query params `factor` (default = the first catalog factor) and `horizon` (default =
`config.walk_forward.default_horizon`). An unknown `factor` -> 422; a `horizon` not in
`config.walk_forward.horizons` -> 422 (no fabricated factor/horizon); `503` when no price data exists
at all (mirrors `system_health.py`; anti-goal: No fabricated data — never an invented evidence row).
The Factor Lab is a cross-date aggregate (like System Health) — it has NO as-of/date control (J-18).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import Config, get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.research import compute_factor_lab, factor_catalog

router = APIRouter(tags=["research"])


@router.get("/research/factor-lab")
def factor_lab(
    factor: Optional[str] = Query(default=None, description="factor key; defaults to the first catalog factor"),
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Factor Lab for the requested `factor` + `horizon` (defaults: first catalog factor /
    config default_horizon). Validates both against the config-driven catalog / `walk_forward.horizons`
    (422 otherwise); 503 when no price data exists. The payload is the canonical analysis verbatim —
    never recomputed in the view."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    valid_factors = [f["key"] for f in factor_catalog(cfg)]
    resolved_factor = valid_factors[0] if factor is None else factor
    if resolved_factor not in valid_factors:
        raise HTTPException(
            status_code=422,
            detail=f"unknown factor {resolved_factor!r}; valid factors are {valid_factors}",
        )

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    return compute_factor_lab(session, resolved_factor, resolved_horizon, cfg)
