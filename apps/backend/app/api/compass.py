"""GET /api/compass — the next-session manifest CONTENT block (goal-market-compass iter-2, J-02/J-03/
J-04). Serves the stored `NextSessionManifest` row for the resolved `as_of`, computing + persisting it
ONCE if absent (create-once-on-GET — zero producer calls on a warm hit, TC-1) and serving from storage
on every subsequent hit for that `as_of`. Reuses `snapshot_serving`'s as-of error mapping so a requested
`as_of` with no stored run returns the SAME honest error shape every other as-of-aware endpoint does —
never a fabricated payload.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.engine.compass import get_or_create_manifest, manifest_row_payload
from app.engine.snapshot_serving import resolved_run

router = APIRouter(tags=["compass"])


@router.get("/compass")
def compass(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    run = resolved_run(session, as_of)
    row = get_or_create_manifest(session, run)
    return manifest_row_payload(row)
