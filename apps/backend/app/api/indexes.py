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

from app.db import get_session
from app.engine.indexes import UnknownRangeError, compute_index_series
from app.engine.scanner import AsOfError
from app.engine.snapshot_serving import _http

router = APIRouter(tags=["indexes"])


@router.get("/indexes")
def indexes(
    range: Optional[str] = Query(default=None),
    as_of: Optional[str] = None,
    session: Session = Depends(get_session),
) -> dict:
    try:
        return compute_index_series(session, as_of=as_of, range_key=range)
    except UnknownRangeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except AsOfError as exc:
        raise _http(exc)
