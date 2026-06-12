"""GET /api/regime-history — the CANONICAL stored per-date market-regime series (Data Contract:
`regime_history:get_regime_history`).

Serves the stored `date -> {label, score}` series read VERBATIM from the immutable `scanner_runs`
rows, bounded to dates `<= the resolved as-of date` (J-44 dashboard regime bands + J-45 stock-detail
regime bands both consume this one endpoint, so the same date shows the same stored label/color
everywhere). `?as_of=` resolves exactly like the other read endpoints; an invalid as-of maps to an
explicit 4xx/503 (via the shared `AsOfError` translation), never a fabricated row. NO regime value is
recomputed here (anti-goal: Regime overlays read stored regime only / No recompute in the read path).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.engine.regime_history import get_regime_history
from app.engine.scanner import AsOfError
from app.engine.snapshot_serving import _http

router = APIRouter(tags=["regime-history"])


@router.get("/regime-history")
def regime_history(
    as_of: Optional[str] = None,
    full: bool = Query(
        default=False,
        description=(
            "J-49 clamp-optional: when true, serve the full stored regime series through the latest "
            "run (display-only dashboard context past the as-of marker). Default false clamps at the "
            "resolved as-of (the stock-detail regime-band consumer keeps it — J-45)."
        ),
    ),
    session: Session = Depends(get_session),
) -> dict:
    try:
        return get_regime_history(session, as_of, full=full)
    except AsOfError as exc:
        raise _http(exc)
