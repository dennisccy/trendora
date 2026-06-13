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
    echoed back (anti-goal: Import keys are env-or-session, never persisted).

    `expand` (J-35) is the operator-facing universe-screen job: it screens the committed candidate pool
    over the selected source (which MUST be `supports_market_cap: true` — the engine rejects an ineligible
    source) and grows the scored universe; its `start`/`end` are the OHLCV-fetch window job parameters."""

    kind: Literal["fetch", "backfill", "both", "expand"]
    start: date_cls
    end: date_cls
    source: Optional[str] = None
    api_key: Optional[str] = None
    # J-37 pull-missing: when present, a FETCH covers EXACTLY these diagnosed-gap symbols instead of the
    # whole seed universe — the gap-exact pull dispatched through this SAME job-start path (no second fetch
    # engine). The chunked fetch is per-(symbol, date) idempotent, so it fills only the missing bars.
    # Ignored for a backfill (which reads the committed seed). These are JOB PARAMETERS, not a date control.
    symbols: Optional[list[str]] = None


class ResumeRequest(BaseModel):
    """POST body for resuming a paused (`resumable`) chunked import (J-34). `api_key` is the SESSION-ONLY
    key re-supplied for a needs-key source — request-only: it is forwarded to the resume worker and NEVER
    persisted (the checkpoint stores no key, so a restart-then-resume of a key source needs it again).
    Optional/empty for a no-key source."""

    api_key: Optional[str] = None


class RemoveScope(BaseModel):
    """POST body for the seed-safe Remove-data preview/execute (J-39). The scope is `symbols` and/or a
    `[start, end]` date range — these are ACTION PARAMETERS (which bars to remove), NOT a viewing as-of
    control (the global as-of switcher is untouched). At least one of symbols / range must be supplied (an
    empty scope is rejected with 400 — never an accidental wipe). The committed seed is never deletable:
    bars inside the committed-seed windows are excluded and a wholly-seed scope is refused. This body
    carries NO provider key — removal is a purely local destructive metadata operation (J-33 carry: the
    error surface is key-free)."""

    symbols: Optional[list[str]] = None
    start: Optional[date_cls] = None
    end: Optional[date_cls] = None


@router.get("/data")
def data_overview(session: Session = Depends(get_session)) -> dict:
    """Current dataset coverage + recent run history + the import provider catalog (J-33) + the paused
    resumable imports (J-34). Coverage is descriptive metadata (no canonical value recomputed); it serves
    gracefully even on an empty DB (null range / zero counts). `sources` is the config catalog with
    env-detected availability — it carries the env-var NAME + a boolean only, never a key value.
    `resumable_imports` are the durable checkpoints with `status == "resumable"` (newest first) so a
    rate-limited import stays discoverable + Resume-able after a backend restart — and it NEVER carries a
    key value (the checkpoint has no key column)."""
    cfg = get_config()
    jp = cfg.data_manager.job_progress
    return {
        "coverage": data_manager.compute_coverage(session, cfg),
        "runs": data_manager.recent_runs(session, cfg),
        "sources": data_manager.compute_provider_availability(cfg),
        "resumable_imports": data_manager.resumable_imports(session, cfg),
        # J-38: the UNIFIED Unfinished-imports list — resumable checkpoints + partial/failed runs (minus
        # soft-dismissed), each with a plain-language state + the right action. Generalizes
        # `resumable_imports` (kept for backward compatibility). Reads only job-control rows; carries no key.
        "unfinished_imports": data_manager.unfinished_imports(session, cfg),
        # J-66: the fine-grained progress knobs from config (No magic numbers) — the live job card reads
        # the poll interval + the heartbeat-stale threshold from here, never a hardcoded literal.
        "job_progress": {
            "poll_interval_seconds": jp.poll_interval_seconds,
            "heartbeat_stale_seconds": jp.heartbeat_stale_seconds,
            "per_symbol_ticks": jp.per_symbol_ticks,
        },
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
    # J-37 pull-missing: a FETCH may carry the diagnosed-gap `symbols` so it fetches EXACTLY that scope
    # (gap-exact) through the SAME engine. Empty/whitespace symbols are normalized away (a None ⇒ the
    # whole seed set, the generic-fetch behavior). Ignored for a backfill.
    symbols = None
    if payload.symbols:
        symbols = [s.strip() for s in payload.symbols if s and s.strip()] or None
    job_id = data_manager.start_data_job(
        payload.kind, payload.start, payload.end,
        source=source, api_key=payload.api_key, config=cfg, engine=get_engine(),
        symbols=symbols,
    )
    return {
        "job_id": job_id,
        "kind": payload.kind,
        "start": payload.start.isoformat(),
        "end": payload.end.isoformat(),
        "source": source,
        "symbols": symbols,
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


@router.post("/data/jobs/{import_id}/resume")
def resume_job(
    import_id: str,
    payload: Optional[ResumeRequest] = None,
    session: Session = Depends(get_session),
) -> dict:
    """Resume a paused (`resumable`) chunked import from its next un-fetched chunk (J-34). Validates
    explicitly before spawning the async resume worker: `404` for an unknown import_id, `409` for a
    non-resumable one (already `ok`/`failed`/`running` — never a fabricated job), and `400` for a
    needs-key source resumed without a key (the checkpoint stores no key, so a restart-then-resume of a
    key source must re-supply the SESSION-ONLY key). The re-supplied key is request-only and NEVER
    persisted; the response echoes the resolved `source` (not secret) and never the key."""
    cfg = get_config()
    checkpoint = data_manager.get_checkpoint(session, import_id)
    if checkpoint is None:
        raise HTTPException(status_code=404, detail=f"unknown import: {import_id}")
    if checkpoint.status not in data_manager.RESUMABLE_CHECKPOINT_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"import {import_id} is not resumable (status {checkpoint.status})",
        )
    api_key = payload.api_key if payload is not None else None
    # J-59: a `failed_backfill` resume skips the fetch stage entirely (zero provider calls), so it needs
    # NO key even for a needs-key source — only a `resumable` 429-pause (which re-fetches the un-fetched
    # chunk) requires the session key be re-supplied for a needs-key source with no env key.
    fetch_will_run = checkpoint.status == "resumable"
    entry = cfg.data_manager.provider_by_id(checkpoint.source)
    if (
        fetch_will_run
        and entry is not None
        and entry.needs_key
        and not data_manager.resolve_provider_key(entry, api_key)
    ):
        raise HTTPException(
            status_code=400,
            detail=f"source {checkpoint.source!r} requires a key; set ${entry.env_var} or paste a session key",
        )
    data_manager.start_resume_job(import_id, api_key=api_key, config=cfg, engine=get_engine())
    return {"import_id": import_id, "source": checkpoint.source, "status": "running"}


@router.post("/data/jobs/{run_id}/retry")
def retry_job(
    run_id: int,
    payload: Optional[ResumeRequest] = None,
    session: Session = Depends(get_session),
) -> dict:
    """J-38 Retry — re-dispatch ONLY the outstanding/failed work of a partial/failed `DataProviderRun`
    through the EXISTING J-34 chunked import engine (the ONE fetch path). Per-`(symbol, date)` idempotency
    means a Retry re-fetches/duplicates NOTHING already stored. Validates explicitly before spawning the
    async worker: `404` for an unknown run_id, `409` for a non-retryable run (not partial/failed, or not a
    Data Manager job), and `400` for a needs-key source retried without a key (the re-supplied SESSION-ONLY
    key is request-only and NEVER persisted). The original audit run is never mutated; a fresh
    DataProviderRun records the retry outcome (Run history is append-only)."""
    cfg = get_config()
    run = data_manager.get_provider_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"unknown run: {run_id}")
    if run.status not in ("partial", "failed"):
        raise HTTPException(
            status_code=409, detail=f"run {run_id} is not retryable (status {run.status})"
        )
    summary = data_manager.summarize_provider_run(run)
    if summary.get("kind") is None or summary.get("start") is None or summary.get("end") is None:
        raise HTTPException(
            status_code=409, detail=f"run {run_id} is not a retryable import job (no job parameters)"
        )
    api_key = payload.api_key if payload is not None else None
    entry = cfg.data_manager.provider_by_id(run.provider)
    if entry is not None and entry.needs_key and not data_manager.resolve_provider_key(entry, api_key):
        raise HTTPException(
            status_code=400,
            detail=f"source {run.provider!r} requires a key; set ${entry.env_var} or paste a session key",
        )
    job_id = data_manager.retry_run(run_id, api_key=api_key, config=cfg, engine=get_engine())
    return {"run_id": run_id, "job_id": job_id, "source": run.provider, "status": "running"}


@router.post("/data/jobs/{record_id}/dismiss")
def dismiss_job(
    record_id: str,
    record_type: str = "run",
    session: Session = Depends(get_session),
) -> dict:
    """J-38 Remove/Dismiss — drop ONLY the actionable JOB-CONTROL record so it leaves `unfinished_imports`:
    a resumable `ImportCheckpoint` is DELETED (`record_type=checkpoint`); a partial/failed `DataProviderRun`
    is SOFT-DISMISSED (`record_type=run`, the default) — it STAYS in the append-only Run-history audit and
    no immutable snapshot/forward-return/audit row is deleted, hidden, or mutated. `404` for an unknown id.
    The error surface carries no key (J-33 carry)."""
    try:
        return data_manager.dismiss_import(session, record_type, record_id, config=get_config())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/data/remove/preview")
def remove_preview(payload: RemoveScope, session: Session = Depends(get_session)) -> dict:
    """READ-ONLY confirm-preview for a seed-safe removal (J-39): returns exactly what WOULD be removed —
    removable `(symbol, date)` bar count + range + symbols, the not-removable committed-seed breakdown (per
    symbol, reason `"committed seed"`), and the cascade of dependent snapshot/forward-return rows — while
    DELETING NOTHING. A wholly-committed-seed scope returns `refused=True` (a 200 the UI renders to disable
    the destructive confirm, with the explicit reason). An empty/inverted/unknown scope is 400 (the engine
    `ValueError` mapped explicitly — never a silent no-op). The error surface carries no key (J-33 carry).

    The scope is ACTION PARAMETERS (which bars to remove), NOT the global as-of viewing control."""
    cfg = get_config()
    try:
        return data_manager.preview_removal(
            session, cfg, symbols=payload.symbols, start=payload.start, end=payload.end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/data/remove")
def remove_data_endpoint(payload: RemoveScope, session: Session = Depends(get_session)) -> dict:
    """DESTRUCTIVE seed-safe removal (J-39). Deletes ONLY the user-added bars in scope (the committed seed
    is excluded and un-deletable) and cascade-removes the snapshot/forward-return rows that derived SOLELY
    from them — a whole-row delete, never an in-place overwrite of a retained snapshot (Snapshots are
    immutable). The removal is recorded on the append-only `DataProviderRun` audit log. A wholly-committed-
    seed scope is REFUSED with 400 (never a silent partial); an empty/inverted/unknown scope is 400 too
    (the engine `ValueError` mapped explicitly). After this returns, `GET /api/data` reflects the smaller
    dataset (snapshot dates that existed only because of removed bars are gone). The error surface carries
    no key (J-33 carry)."""
    cfg = get_config()
    try:
        return data_manager.remove_data(
            session, cfg, symbols=payload.symbols, start=payload.start, end=payload.end,
            engine=get_engine(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
