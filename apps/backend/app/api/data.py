"""GET/POST /api/data — the Data Manager surface (Data Contract: app.engine.data_manager, J-17).

Three endpoints, all thin wrappers over `app.engine.data_manager` (which ORCHESTRATES the existing
canonical create-once paths — it computes no score/return of its own):

  - `GET  /api/data`               → current dataset coverage (price range, symbol count, snapshot/
                                     as-of dates, backfill gaps) + the recent fetch/backfill run history.
  - `POST /api/data/jobs`          → validate the date range + kind, START the async job, return
                                     `{job_id}` IMMEDIATELY. Malformed dates / unknown kind → 422 (typed
                                     model); inverted or over-long range → 400; no price data → 503.
  - `GET  /api/data/jobs/{job_id}` → live status/progress for polling, ending in the final summary; an
                                     unknown id → 404 (never a fabricated job).

The job runs in a background thread with its OWN DB session (never this request's), so the default boot
path and the request/response cycle are untouched. The `/data` date inputs are JOB PARAMETERS (which
dates to fetch/backfill) — NOT a viewing as-of control; this router never touches the as-of read path.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.config import get_config
from app.db import get_engine, get_session
from app.engine import data_manager
from app.engine.prices import latest_data_date

router = APIRouter(tags=["data"])


class JobCreate(BaseModel):
    """POST body — the job kind, the date range it covers (a single date ⇒ start == end), and the J-33
    import `source` + session-only `api_key`. `kind` and the `date` fields are typed, so an unknown kind
    or a malformed date is rejected with 422 before the handler runs. These dates are JOB PARAMETERS, not
    a viewing as-of control. `source` is an optional catalog provider id (defaults to
    `data_manager.default_source`; validated against the catalog in the handler). `api_key` is the pasted
    SESSION-ONLY key — request-only: it is forwarded to the fetch worker and NEVER persisted, logged, or
    echoed back (anti-goal: Import keys are env-or-session, never persisted)."""

    kind: Literal["fetch", "backfill", "both"]
    start: date_cls
    end: date_cls
    source: Optional[str] = None
    api_key: Optional[str] = None


@router.get("/data")
def data_overview(session: Session = Depends(get_session)) -> dict:
    """Current dataset coverage + recent run history + the import provider catalog (J-33). Coverage is
    descriptive metadata (no canonical value recomputed); it serves gracefully even on an empty DB (null
    range / zero counts). `sources` is the config catalog with env-detected availability — it carries the
    env-var NAME + a boolean only, never a key value or the run history's key (there is none)."""
    cfg = get_config()
    return {
        "coverage": data_manager.compute_coverage(session, cfg),
        "runs": data_manager.recent_runs(session, cfg),
        "sources": data_manager.compute_provider_availability(cfg),
    }


@router.post("/data/jobs")
def start_job(payload: JobCreate, session: Session = Depends(get_session)) -> dict:
    """Validate the request, START the async fetch/backfill job, and return its `job_id` immediately
    (the job runs in a background thread). `503` when no price data exists; `400` for an inverted or
    over-long range, an unknown import source, or a fetch against a needs-key source with no env/pasted
    key (an explicit rejection — never a silent no-op). The response echoes the resolved `source` (not
    secret) and NEVER the pasted key."""
    cfg = get_config()
    if latest_data_date(session) is None:
        raise HTTPException(status_code=503, detail="no price data available")
    source = payload.source or cfg.data_manager.default_source
    try:
        data_manager.validate_job_request(
            payload.kind, payload.start, payload.end, cfg, source=source, api_key=payload.api_key
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job_id = data_manager.start_data_job(
        payload.kind, payload.start, payload.end,
        source=source, api_key=payload.api_key, config=cfg, engine=get_engine(),
    )
    return {
        "job_id": job_id,
        "kind": payload.kind,
        "start": payload.start.isoformat(),
        "end": payload.end.isoformat(),
        "source": source,
        "status": "running",
    }


@router.get("/data/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    """Live status/progress for a job (polled by the UI), ending in the final summary. `404` for an
    unknown id — never a fabricated job record."""
    job = data_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"unknown job: {job_id}")
    return job
