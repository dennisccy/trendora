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
from app.engine.research import compute_factor_combination, compute_factor_lab, factor_catalog

router = APIRouter(tags=["research"])

# the two condition sides (a catalog factor's top or bottom quantile tail). A fixed structural
# vocabulary (not a tunable) — only the quantile fractions + condition limits + defaults are config.
_CONDITION_SIDES = ("top", "bottom")


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


@router.get("/research/factor-combination")
def factor_combination(
    condition: Optional[list[str]] = Query(
        default=None,
        description="repeatable '<factor_key>:<side>:<quantile_key>'; defaults to config default_conditions",
    ),
    horizon: Optional[int] = Query(
        default=None, description="forward window in trading days; defaults to config default_horizon"
    ),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the multi-factor combination cohort analysis (J-26) for the requested `condition`s +
    `horizon` (the SINGLE canonical endpoint for this NEW value). Each `condition` is
    `"<factor_key>:<side>:<quantile_key>"`; an empty/omitted `condition` uses
    `config.research.factor_lab.combination.default_conditions`. Validates the condition count against
    `[min_conditions, max_conditions]`, each `factor_key` against the config-driven catalog, `side`
    against {top, bottom}, `quantile_key` against the config quantiles, and `horizon` against
    `walk_forward.horizons` (422 on any violation — no fabricated factor/side/quantile/horizon); 503 when
    no price data exists. The payload is `compute_factor_combination(...)` verbatim — never recomputed in
    the view. A cross-date aggregate (like the Factor Lab) — there is NO as-of/date control (J-18)."""
    cfg: Config = get_config()
    comb = cfg.research.factor_lab.combination
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    # empty/omitted condition -> the config-driven canonical default; else parse each "f:side:q" triple.
    if not condition:
        conditions = [
            {"factor": c.factor, "side": c.side, "quantile": c.quantile}
            for c in comb.default_conditions
        ]
    else:
        conditions = []
        for spec in condition:
            parts = spec.split(":")  # exactly the 3 parts of "<factor_key>:<side>:<quantile_key>"
            if len(parts) != 3:
                raise HTTPException(
                    status_code=422,
                    detail=f"condition {spec!r} must be '<factor_key>:<side>:<quantile_key>'",
                )
            conditions.append({"factor": parts[0], "side": parts[1], "quantile": parts[2]})

    if not (comb.min_conditions <= len(conditions) <= comb.max_conditions):
        raise HTTPException(
            status_code=422,
            detail=(
                f"condition count {len(conditions)} must be in "
                f"[{comb.min_conditions}, {comb.max_conditions}]"
            ),
        )

    valid_factors = [f["key"] for f in factor_catalog(cfg)]
    valid_quantiles = [q.key for q in comb.quantiles]
    for c in conditions:
        if c["factor"] not in valid_factors:
            raise HTTPException(
                status_code=422,
                detail=f"unknown factor {c['factor']!r}; valid factors are {valid_factors}",
            )
        if c["side"] not in _CONDITION_SIDES:
            raise HTTPException(
                status_code=422,
                detail=f"unknown side {c['side']!r}; valid sides are {list(_CONDITION_SIDES)}",
            )
        if c["quantile"] not in valid_quantiles:
            raise HTTPException(
                status_code=422,
                detail=f"unknown quantile {c['quantile']!r}; valid quantiles are {valid_quantiles}",
            )

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    return compute_factor_combination(session, conditions, resolved_horizon, cfg)
