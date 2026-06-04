"""Research-lab API (Data Contract: app.engine.research). Three read-only endpoints, each returning the
canonical engine analysis VERBATIM — the view recomputes nothing; it serves aggregations of ALREADY-
STORED forward returns + factor values + excursions:

  - GET /api/research/factor-lab        — `compute_factor_lab` (per factor × horizon: decile table of
    mean forward return + downside risk-adjusted + n, plus rank-IC).
  - GET /api/research/factor-combination — `compute_factor_combination` (the headline composite
    rank-blend cohort + the secondary strict-overlap AND cohort vs baseline vs each single-factor cohort).
  - GET /api/research/event-study        — `compute_event_study` (J-29: per setup/pattern subject ×
    horizon, the forward-return distribution + expectancy + MAE/MFE + downside risk-adjusted ratios +
    best-exit-horizon + by-regime/by-sector slices, from stored values incl. the iter-14 excursions).

Each validates its selectors against the config-driven catalog / `walk_forward.horizons` (422 on an
unknown factor / subject / side / quantile / horizon — no fabricated input); `503` when no price data
exists at all (mirrors the Backtest evidence endpoint; anti-goal: No fabricated data — never an invented
evidence row). All three are cross-date all-history aggregates — NONE has an as-of/date control (J-18).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import Config, get_config
from app.db import get_session
from app.engine.prices import latest_data_date
from app.engine.research import (
    compute_event_study,
    compute_factor_combination,
    compute_factor_lab,
    factor_catalog,
    subject_catalog,
)

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


@router.get("/research/event-study")
def event_study(
    subject: Optional[str] = Query(default=None, description="subject key (setup or pattern); defaults to the first catalog subject"),
    horizon: Optional[int] = Query(default=None, description="forward window in trading days; defaults to config default_horizon"),
    session: Session = Depends(get_session),
) -> dict:
    """Serve the Setup & Pattern event study (J-29) for the requested `subject` + `horizon` (defaults:
    the first catalog subject / config default_horizon). Validates `subject` against the config-driven
    subject catalog (setups + patterns) and `horizon` against `walk_forward.horizons` (422 otherwise);
    503 when no price data exists — mirroring the factor-lab / factor-combination handlers exactly. The
    payload is `compute_event_study(...)` verbatim — a read-only aggregation of ALREADY-STORED forward
    returns + excursions, never recomputed in the view. A cross-date aggregate (like the Factor Lab) —
    there is NO as-of/date control (J-18)."""
    cfg: Config = get_config()
    wf = cfg.walk_forward

    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")

    valid_subjects = [s["key"] for s in subject_catalog(cfg)]
    resolved_subject = valid_subjects[0] if subject is None else subject
    if resolved_subject not in valid_subjects:
        raise HTTPException(
            status_code=422,
            detail=f"unknown subject {resolved_subject!r}; valid subjects are {valid_subjects}",
        )

    resolved_horizon = wf.default_horizon if horizon is None else horizon
    if resolved_horizon not in wf.horizons:
        raise HTTPException(
            status_code=422,
            detail=f"unknown horizon {resolved_horizon}; valid horizons are {list(wf.horizons)}",
        )

    return compute_event_study(session, resolved_subject, resolved_horizon, cfg)
