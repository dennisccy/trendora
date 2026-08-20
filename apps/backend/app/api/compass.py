"""GET /api/compass — the next-session manifest (goal-market-compass iter-2, J-02/J-03/J-04 CONTENT
block; iter-3, J-05/J-06 freeze/integrity block). Serves the LATEST stored `NextSessionManifest` version
for the resolved `as_of`, computing + persisting version 1 ONCE if absent (create-once — TC-1: zero
producer calls on a warm hit) and serving from storage on every subsequent hit for that `as_of`. Reuses
`snapshot_serving`'s as-of error mapping so a requested `as_of` with no stored run returns the SAME
honest error shape every other as-of-aware endpoint does — never a fabricated payload.

`POST /api/compass/regenerate` (iter-3) is an ACTION route, not a second read path — `GET /api/compass`
remains the sole READ endpoint. It is confirm-gated (`confirm=true` required) and mints a NEW version for
an as_of that already has a manifest; it never mints a first version (that stays `GET`'s / the ingest
finalize hook's job).
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.engine.compass import (
    ManifestNotFoundError,
    ManifestNotYetFrozen,
    basis_disclosure,
    get_or_create_manifest,
    list_manifest_versions,
    manifest_row_payload,
    regenerate_manifest,
)
from app.engine.snapshot_serving import resolved_date, resolved_run

router = APIRouter(tags=["compass"])


def _read_time_additions(session: Session, row) -> dict:  # noqa: ANN001 -- NextSessionManifest, avoids an import cycle w/ typing-only use
    """The read-time-only `basis` + `versions` fields BOTH routes attach on top of `manifest_row_payload`'s
    pure reconstruction -- never part of what `manifest_hash` covers (TC-4/TC-22 verification must strip
    these first). Factored out so GET and the regenerate action serve the IDENTICAL shape (a caller that
    stores either response as `CompassResponse` never hits a missing-field crash)."""
    versions = list_manifest_versions(session, row.as_of)
    return {
        "basis": basis_disclosure(session, row),
        "versions": [
            {
                "version": v.version, "mode": v.mode, "frozen": v.frozen,
                "prospective_eligible": v.prospective_eligible,
                "generated_at": (
                    json.loads(v.generation_json).get("generated_at") if v.generation_json else None
                ),
            }
            for v in versions
        ],
    }


@router.get("/compass")
def compass(as_of: Optional[str] = None, session: Session = Depends(get_session)) -> dict:
    run = resolved_run(session, as_of)
    try:
        row = get_or_create_manifest(session, run)
    except ManifestNotYetFrozen as exc:
        # J-05 step 7 / TC-8: the CURRENT frontier's manifest is minted only by the ingest finalize
        # freeze or an explicit regenerate -- a plain GET never mints it. Honest 404, never a
        # fabricated payload; the frontend's existing compass-card "unavailable" states degrade
        # gracefully on any non-2xx (J-07's dedicated "not yet frozen" UI treatment is out of scope
        # this iteration).
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = manifest_row_payload(row)
    payload.update(_read_time_additions(session, row))
    return payload


@router.post("/compass/regenerate")
def compass_regenerate(
    as_of: str, confirm: bool = False, session: Session = Depends(get_session),
) -> dict:
    if not confirm:
        raise HTTPException(status_code=400, detail="regenerate requires confirm=true — no row was created")
    resolved = resolved_date(session, as_of)  # honest as-of resolution error mapping, reused verbatim
    try:
        row = regenerate_manifest(session, resolved)
    except ManifestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = manifest_row_payload(row)
    payload.update(_read_time_additions(session, row))
    return payload
