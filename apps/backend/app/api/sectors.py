"""GET /api/sectors — the CANONICAL and only endpoint for the Sector Score (Data Contract).

iter-8: re-pointed to serve from the persisted IMMUTABLE snapshot for the resolved as-of date
(anti-goal: No recompute in the read path). It resolves `?as_of=` to its stored `ScannerRun` (latest by
default; create-once for a not-yet-stored date) and serves that run's stored `SectorScoreRow` children,
echoing the resolved `asof_date`. Because `run_scan` stored faithful copies of `score_sectors`, the
latest-date payload is byte-identical to the former on-request compute (anti-goal: Single source of
truth). `503` when no price data exists / `4xx` for an invalid `as_of` — never fabricated rows.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.engine.snapshot_serving import resolved_run, sectors_payload

router = APIRouter(tags=["sectors"])


@router.get("/sectors")
def sectors(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    return sectors_payload(session, resolved_run(session, as_of))
