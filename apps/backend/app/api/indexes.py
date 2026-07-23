"""GET /api/indexes — the CANONICAL normalized-% major-indexes display series (Data Contract:
`indexes:compute_index_series`).

Serves the server-side normalized-% lines for the config-listed index ETFs (rebased to the selected
range start) for the J-44 dashboard chart. `range` (a preset key) + `as_of` params; an unknown preset
returns an explicit 422 (never a silent fallback to a fabricated range); an invalid `as_of` returns the
shared 4xx/503. A configured symbol with no stored bars (e.g. DIA) is omitted honestly server-side. NO
return math is done in the frontend — the series is computed once here (anti-goal: The index chart is
honest and never data-gated).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import get_config
from app.db import get_session
from app.engine.indexes import UnknownRangeError, compute_index_series, index_series_cached
from app.engine.scanner import AsOfError
from app.engine.snapshot_serving import _http

router = APIRouter(tags=["indexes"])


@router.get("/indexes")
def indexes(
    range: Optional[str] = Query(default=None),
    as_of: Optional[str] = None,
    full: bool = Query(
        default=False,
        description=(
            "J-49 clamp-optional: when true, serve the full stored path through the latest date "
            "(display-only dashboard context past the as-of marker). Default false clamps at the "
            "resolved as-of (byte-identical to before) for the stock-detail-fed path."
        ),
    ),
    session: Session = Depends(get_session),
) -> dict:
    try:
        cfg = get_config()
        # ops-hardening iter-13 (J-06): the SINGLE unparameterized default hot key
        # (no/default range, full=True, no explicit historical as_of) is served from the ingest-warmed
        # `IndexSeriesCache` (PhaseCrossViewCard `/` and IndexVendorPanel `/data` both request exactly
        # this, unparameterized, on mount). Every other combination — an explicit non-default range, or
        # an explicit historical as_of — keeps calling `compute_index_series` directly, unchanged, lazy
        # (the existing "cannot be precomputed — user-parameterized" carve-out).
        is_hot_key = full and as_of is None and (range is None or range == cfg.index_chart.default_range)
        if is_hot_key:
            return index_series_cached(session, config=cfg)
        return compute_index_series(session, as_of=as_of, range_key=range, config=cfg, full=full)
    except UnknownRangeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except AsOfError as exc:
        raise _http(exc)
