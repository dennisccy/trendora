"""GET /api/dashboard — the CANONICAL endpoint for the Market Regime value + the candidate counts.

iter-8: re-pointed to serve from the persisted IMMUTABLE snapshot for the resolved as-of date
(anti-goal: No recompute in the read path). It resolves `?as_of=` to its stored `ScannerRun` (the
latest stored run by default; create-once for a not-yet-stored date) and serves that run's STORED
regime panel, universe-relative breadth, and candidate counts — read from `candidate_counts_json`,
never re-derived. The values are unchanged in meaning: `run_scan` stored faithful copies of the
canonical `score_regime` + `summarize_candidates` outputs, so the latest-date payload is byte-identical
to the former on-request compute (single source of truth holds throughout). It echoes the resolved
`asof_date` so the UI can render the "viewing as-of D (historical)" indicator.

NOT served here (each has exactly one serving path):
  - **Top Sectors** -> the frontend reads the canonical `GET /api/sectors` and slices the top N.
  - **Top Themes** -> the frontend reads the canonical `GET /api/themes` and slices the top N
    (exactly as Top Sectors does). The Theme Score is therefore NOT re-served from this endpoint.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.engine.snapshot_serving import dashboard_payload, resolved_run

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    return dashboard_payload(resolved_run(session, as_of))
