"""Data Manager — on-demand dataset growth (Data Contract: app.engine.data_manager, J-17).

This module ORCHESTRATES the existing canonical create-once paths; it computes NO score, bucket, or
forward return of its own (the #1 coherence guard for this iteration). Specifically:

  * `compute_coverage` is READ-ONLY descriptive metadata over `daily_prices` + `scanner_runs`
    (price-history range, distinct symbol count, the set of snapshot/as-of dates, and the backfill
    GAPS = trading days that have bars but no snapshot). It recomputes no canonical value.

  * `run_data_job` runs a single fetch and/or backfill job over a date or `[start, end]` range:
      - BACKFILL (offline/deterministic): for each in-range trading day that has bars but no snapshot,
        it calls the EXISTING `scanner.run_scan` (create-once via `get_run_for_date`, bars <= D) then
        `forward_testing.backfill_run_forward_returns` (INSERT-only realized returns, bars > D). It
        never re-implements scan/return math and never overwrites a snapshot — so the new dates appear
        in the as-of switcher and the System Health sample size `n` grows (anti-goals: Snapshots
        immutable / No lookahead / Range backfill stays immutable & lookahead-free).
      - FETCH (live, real-data-only): pulls REAL EOD bars via the config-selected LIVE provider for the
        chosen range and persists only NEW `(symbol, date)` rows (never overwriting committed seed bars).
        On a per-symbol provider failure it counts the symbol failed, persists ZERO bars for it, and
        surfaces an explicit error — it NEVER fabricates a price (anti-goal: Live fetch is real-data-only).

Live progress lives in an in-memory job registry keyed by `job_id`; the FINAL summary is persisted ONCE
to the append-only `DataProviderRun` table (structured detail JSON-encoded in `message`). The default
boot path is untouched — this job is on-demand only and opens its OWN DB session (never the request's).
Every job limit / display cap is read from `config.data_manager` (anti-goal: No magic numbers)."""
from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import date as date_cls, datetime, timezone
from typing import Optional

from sqlalchemy import func, insert
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, ProviderCatalogEntry, get_config
from app.data_providers import make_provider
from app.data_providers.base import PriceProvider, ProviderUnavailableError
from app.db import get_engine
from app.engine import forward_testing, scanner
from app.engine.prices import bars_asof, latest_data_date
from app.models import DailyPrice, DataProviderRun, ScannerRun
from app.seed_loader import all_seed_symbols

JOB_KINDS = ("fetch", "backfill", "both")
_FETCH_KINDS = ("fetch", "both")
_BACKFILL_KINDS = ("backfill", "both")
# Cap stored per-symbol error strings so a wholly-failed fetch (e.g. 158 symbols) keeps the job record
# bounded; the failed COUNT is always exact (this only truncates the example messages shown).
_MAX_ERROR_SAMPLES = 20


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------------------------------
# Coverage — read-only descriptive metadata (recomputes no canonical score/return)
# --------------------------------------------------------------------------------------------------
def _trading_days(session: Session, cfg: Config) -> list[date_cls]:
    """The trading calendar = the benchmark's (SPY) seed bar dates, ascending — the SAME calendar the
    walk-forward uses. A date is a trading day iff SPY has a bar on it; this never fabricates a date."""
    latest = latest_data_date(session)
    if latest is None:
        return []
    benchmark = cfg.etfs.index[0]
    return [bar.date for bar in bars_asof(session, benchmark, latest)]


def compute_coverage(session: Session, config: Optional[Config] = None) -> dict:
    """Current dataset coverage — purely descriptive, recomputing NO canonical value:
      - price-history date range (min/max `DailyPrice.date`) and distinct symbol count,
      - the set of snapshot/as-of dates (`ScannerRun.asof_date`), newest first,
      - GAPS = trading days (bars present) with no snapshot — the actionable backfill targets — with a
        count plus a bounded preview (`config.data_manager.gap_preview`)."""
    cfg = config or get_config()
    price_min = session.scalar(select(func.min(DailyPrice.date)))
    price_max = session.scalar(select(func.max(DailyPrice.date)))
    symbol_count = session.scalar(select(func.count(func.distinct(DailyPrice.symbol))))

    snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
    snapshot_set = set(snapshot_dates)
    trading_days = _trading_days(session, cfg)
    gaps = [d for d in trading_days if d not in snapshot_set]
    preview = cfg.data_manager.gap_preview

    return {
        "price_start": price_min.isoformat() if price_min else None,
        "price_end": price_max.isoformat() if price_max else None,
        "symbol_count": int(symbol_count or 0),
        # the RESOLVED UNIVERSE size — the one canonical `config.universe.symbols` (the committed screen
        # result), read live here and on /api/methodology so the two surfaces never drift (J-22, single
        # source / no recompute). Distinct from `symbol_count` (DISTINCT priced symbols, incl. ETFs+^VIX).
        "universe_count": len(cfg.universe.symbols),
        "snapshot_count": len(snapshot_dates),
        "snapshot_dates": [d.isoformat() for d in sorted(snapshot_dates, reverse=True)],
        "trading_day_count": len(trading_days),
        "gap_count": len(gaps),
        "gap_first": gaps[0].isoformat() if gaps else None,
        "gap_last": gaps[-1].isoformat() if gaps else None,
        "gaps_preview": [d.isoformat() for d in gaps[:preview]],
    }


# --------------------------------------------------------------------------------------------------
# Import provider catalog + env-detected availability (J-33) — descriptive metadata, NO key value
# --------------------------------------------------------------------------------------------------
def resolve_provider_key(entry: ProviderCatalogEntry, pasted_key: Optional[str]) -> Optional[str]:
    """The effective credential for one import source: the SESSION-ONLY pasted key if present, else the
    value of the source's configured environment variable (by NAME). Returns None when the source needs
    no key, or when neither a pasted nor an env key is available. The result is used in-memory only
    (request-scoped) and is NEVER persisted/logged (anti-goal: Import keys are env-or-session, never
    persisted). A no-key source returns None and ignores any pasted value."""
    if not entry.needs_key:
        return None
    if pasted_key:
        return pasted_key
    return os.environ.get(entry.env_var) if entry.env_var else None


def compute_provider_availability(config: Optional[Config] = None) -> list[dict]:
    """The import-source catalog with per-source availability, computed from config + the environment at
    REQUEST time (J-33). For each catalog entry: `available = (not needs_key) or the env var is set`. The
    output carries ONLY the env-var NAME, the boolean requirement/availability, and a human `reason` — it
    NEVER contains the env value or any key (anti-goal: Import keys are env-or-session, never persisted).
    This is descriptive availability metadata — NOT a duplicate of any canonical score/return/bucket."""
    cfg = config or get_config()
    sources: list[dict] = []
    for entry in cfg.data_manager.providers:
        available = (not entry.needs_key) or bool(entry.env_var and os.environ.get(entry.env_var))
        if not entry.needs_key:
            reason = "no key required"
        elif available:
            reason = f"key present in ${entry.env_var}"
        else:
            reason = f"set ${entry.env_var} or paste a session key"
        sources.append({
            "id": entry.id,
            "label": entry.label,
            "needs_key": entry.needs_key,
            "env_var": entry.env_var,
            "supports_market_cap": entry.supports_market_cap,
            "available": available,
            "reason": reason,
        })
    return sources


# --------------------------------------------------------------------------------------------------
# In-memory job registry (live progress) — the FINAL summary is persisted to DataProviderRun
# --------------------------------------------------------------------------------------------------
@dataclass
class JobProgress:
    """Live progress for one fetch/backfill job (in-memory; the API polls `to_dict()`)."""

    job_id: str
    kind: str
    start: date_cls
    end: date_cls
    # The chosen import `source` id (J-33) — NOT secret; recorded so the run history shows which provider
    # a fetch used. The pasted `api_key` is DELIBERATELY ABSENT from this in-memory record (and from the
    # persisted run / detail JSON / logs) — it is request-only (anti-goal: keys are env-or-session, never
    # persisted). Defaults to None for a backfill-only job (no fetch ⇒ no source).
    source: Optional[str] = None
    status: str = "running"  # running | ok | partial | failed
    symbols_total: int = 0
    symbols_ok: int = 0
    symbols_failed: int = 0
    bars_fetched: int = 0
    dates_total: int = 0
    dates_done: int = 0
    snapshots_created: int = 0
    forward_returns_inserted: int = 0
    message: str = ""
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "source": self.source,  # the chosen import provider id (not secret); never the key
            "status": self.status,
            "symbols_total": self.symbols_total,
            "symbols_ok": self.symbols_ok,
            "symbols_failed": self.symbols_failed,
            "bars_fetched": self.bars_fetched,
            "dates_total": self.dates_total,
            "dates_done": self.dates_done,
            "snapshots_created": self.snapshots_created,
            "forward_returns_inserted": self.forward_returns_inserted,
            "message": self.message,
            "errors": list(self.errors),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


_JOBS: dict[str, JobProgress] = {}
_LOCK = threading.Lock()


def create_job(kind: str, start: date_cls, end: date_cls, source: Optional[str] = None) -> JobProgress:
    """Register a new `running` job in the in-memory registry and return it (with a fresh job_id). The
    optional `source` is the chosen import provider id (J-33; not secret) — the pasted key is NEVER
    stored on the job, only threaded to the worker as a request-only argument."""
    job = JobProgress(job_id=uuid.uuid4().hex, kind=kind, start=start, end=end, source=source)
    with _LOCK:
        _JOBS[job.job_id] = job
    return job


def get_job(job_id: str) -> Optional[dict]:
    """A serializable snapshot of a job's live progress, or None for an unknown id."""
    with _LOCK:
        job = _JOBS.get(job_id)
    return job.to_dict() if job is not None else None


def validate_job_request(
    kind: str,
    start: date_cls,
    end: date_cls,
    config: Optional[Config] = None,
    *,
    source: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """Reject an invalid job request explicitly (the API maps the raised `ValueError` to a 4xx — never a
    silent no-op): an unknown kind, an inverted range (start > end), a span over the configured
    `data_manager.max_range_days`, an unknown import `source`, or a fetch against a `needs_key` source
    with neither an env key nor a pasted session key. Malformed dates are rejected earlier by the typed
    API model. `source`/`api_key` are validated only when a `source` is supplied; the key is read
    request-only for the gate and is never persisted (anti-goal: keys are env-or-session, never
    persisted)."""
    cfg = config or get_config()
    if kind not in JOB_KINDS:
        raise ValueError(f"unknown job kind {kind!r}; expected one of {list(JOB_KINDS)}")
    if start > end:
        raise ValueError(f"start date {start.isoformat()} must be on or before end date {end.isoformat()}")
    span_days = (end - start).days + 1
    if span_days > cfg.data_manager.max_range_days:
        raise ValueError(
            f"date range too large: {span_days} days exceeds the configured maximum "
            f"{cfg.data_manager.max_range_days}"
        )
    if source is not None:
        entry = cfg.data_manager.provider_by_id(source)
        if entry is None:
            raise ValueError(
                f"unknown import source {source!r}; expected one of {cfg.data_manager.provider_ids()}"
            )
        # A key is only required for a job that actually FETCHES (backfill reads the committed seed).
        if kind in _FETCH_KINDS and entry.needs_key and not resolve_provider_key(entry, api_key):
            raise ValueError(
                f"source {source!r} requires a key; set ${entry.env_var} or paste a session key"
            )


# --------------------------------------------------------------------------------------------------
# Job execution — fetch (live, real-data-only) and backfill (offline, create-once orchestration)
# --------------------------------------------------------------------------------------------------
def _record_error(prog: JobProgress, message: str) -> None:
    if len(prog.errors) < _MAX_ERROR_SAMPLES:
        prog.errors.append(message)


def _existing_dates(session: Session, symbol: str, start: date_cls, end: date_cls) -> set[date_cls]:
    """The `(symbol, date)` dates already persisted in `[start, end]` — so the fetch only INSERTs NEW
    bars and never overwrites a committed seed bar (anti-goal: range fetch never overwrites)."""
    stmt = (
        select(DailyPrice.date)
        .where(DailyPrice.symbol == symbol)
        .where(DailyPrice.date >= start)
        .where(DailyPrice.date <= end)
    )
    return set(session.exec(stmt).all())


def _do_fetch(session: Session, cfg: Config, prog: JobProgress, provider: PriceProvider) -> None:
    """Pull REAL EOD bars for the universe + ETFs over the range and persist only NEW `(symbol, date)`
    rows. A per-symbol provider failure counts the symbol failed, persists ZERO bars for it, and records
    an explicit error — never a fabricated price (anti-goal: Live fetch is real-data-only)."""
    symbols = all_seed_symbols(cfg)
    prog.symbols_total = len(symbols)
    for symbol in symbols:
        try:
            bars = provider.get_daily(symbol, start=prog.start, end=prog.end)
        except ProviderUnavailableError as exc:
            prog.symbols_failed += 1
            _record_error(prog, f"{symbol}: {exc}")
            prog.message = f"fetched {prog.symbols_ok}/{prog.symbols_total} symbols ({prog.symbols_failed} failed)"
            continue
        already = _existing_dates(session, symbol, prog.start, prog.end)
        new_rows = [
            {
                "symbol": symbol,
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
            if bar.date not in already
        ]
        if new_rows:
            session.execute(insert(DailyPrice.__table__), new_rows)
            session.commit()
            prog.bars_fetched += len(new_rows)
        prog.symbols_ok += 1
        prog.message = f"fetched {prog.symbols_ok}/{prog.symbols_total} symbols ({prog.symbols_failed} failed)"


def _do_backfill(session: Session, cfg: Config, prog: JobProgress) -> None:
    """For each in-range trading day with bars but NO snapshot, create the immutable snapshot via the
    EXISTING `scanner.run_scan` (create-once, bars <= D) then INSERT its realized forward returns via
    `forward_testing.backfill_run_forward_returns` (bars > D). No scan/return math is re-implemented and
    no snapshot is overwritten — this is pure orchestration of the registered canonical paths."""
    trading_days = _trading_days(session, cfg)
    snapshot_dates = set(session.exec(select(ScannerRun.asof_date)).all())
    targets = [d for d in trading_days if prog.start <= d <= prog.end and d not in snapshot_dates]
    prog.dates_total = len(targets)
    prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
    for d in targets:
        run = scanner.run_scan(session, d, cfg)  # create-once; recomputes nothing
        result = forward_testing.backfill_run_forward_returns(session, run, cfg)  # INSERT-only, bars > D
        prog.snapshots_created += 1
        prog.forward_returns_inserted += result["rows_inserted"]
        prog.dates_done += 1
        prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"


def _final_status(prog: JobProgress) -> str:
    """Combine the per-phase outcomes into the job status. A fetch that fully fails (every symbol) with
    no backfill work done is `failed`; any partial success is `partial`; otherwise `ok`."""
    statuses: list[str] = []
    if prog.kind in _FETCH_KINDS:
        if prog.symbols_total == 0:
            statuses.append("ok")
        elif prog.symbols_ok == 0:
            statuses.append("failed")
        elif prog.symbols_failed > 0:
            statuses.append("partial")
        else:
            statuses.append("ok")
    if prog.kind in _BACKFILL_KINDS:
        statuses.append("ok")  # deterministic; an exception is handled separately as `failed`
    if statuses == ["failed"]:
        return "failed"
    if "failed" in statuses or "partial" in statuses:
        return "partial"
    return "ok"


def _final_summary(prog: JobProgress) -> str:
    parts: list[str] = []
    if prog.kind in _FETCH_KINDS:
        parts.append(
            f"fetch: {prog.symbols_ok}/{prog.symbols_total} symbols ok, "
            f"{prog.symbols_failed} failed, {prog.bars_fetched} new bars"
        )
    if prog.kind in _BACKFILL_KINDS:
        parts.append(
            f"backfill: {prog.snapshots_created} snapshots over {prog.dates_total} dates, "
            f"{prog.forward_returns_inserted} forward returns"
        )
    return "; ".join(parts) if parts else "no work performed"


def _provider_label(prog: JobProgress, cfg: Config) -> str:
    """The provider recorded on the run row: the CHOSEN import source id when a fetch was involved (J-33;
    the source is not secret — the pasted key is never recorded), else the offline default provider (the
    backfill reads the committed seed). Falls back to the config `default_source` when a fetch job was
    created without an explicit source."""
    if prog.kind in _FETCH_KINDS:
        return prog.source or cfg.data_manager.default_source
    return cfg.provider


def _persist_run(engine: Engine, cfg: Config, prog: JobProgress) -> None:
    """Persist the FINAL job summary ONCE to the append-only `DataProviderRun` (own session; INSERT
    only — never an UPDATE of an existing row). Structured detail is JSON-encoded in `message`."""
    detail = {
        "kind": prog.kind,
        "start": prog.start.isoformat(),
        "end": prog.end.isoformat(),
        "snapshots_created": prog.snapshots_created,
        "dates_done": prog.dates_done,
        "dates_total": prog.dates_total,
        "forward_returns_inserted": prog.forward_returns_inserted,
        "bars_fetched": prog.bars_fetched,
        "summary": _final_summary(prog),
    }
    with Session(engine) as session:
        session.add(
            DataProviderRun(
                provider=_provider_label(prog, cfg),
                started_at=prog.started_at,
                finished_at=prog.finished_at,
                symbols_ok=prog.symbols_ok,
                symbols_failed=prog.symbols_failed,
                status=prog.status,
                message=json.dumps(detail),
            )
        )
        session.commit()


def run_data_job(
    job_id: str,
    *,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
    provider: Optional[PriceProvider] = None,
    api_key: Optional[str] = None,
) -> dict:
    """Run the registered job to completion SYNCHRONOUSLY (the worker body; `start_data_job` runs this in
    a thread). Opens its OWN DB session (never the request's). Updates the in-memory registry as it goes
    and persists the final summary to the append-only `DataProviderRun`. Returns the final snapshot.

    `api_key` is the SESSION-ONLY pasted key (request-only): it is a LOCAL argument resolved into the
    fetch provider here and is NEVER written to the job registry, the persisted run, the detail JSON, or
    any log (anti-goal: Import keys are env-or-session, never persisted). For a fetch, the job-selected
    `source` is resolved against the config catalog and `make_provider(source, api_key=key)` builds the
    live client; an injected `provider` (tests) bypasses that entirely."""
    cfg = config or get_config()
    eng = engine or get_engine()
    with _LOCK:
        prog = _JOBS[job_id]
    try:
        with Session(eng) as session:
            if prog.kind in _FETCH_KINDS:
                if provider is not None:
                    live = provider
                else:
                    source = prog.source or cfg.data_manager.default_source
                    entry = cfg.data_manager.provider_by_id(source)
                    key = resolve_provider_key(entry, api_key) if entry is not None else api_key
                    live = make_provider(source, api_key=key)
                _do_fetch(session, cfg, prog, live)
            if prog.kind in _BACKFILL_KINDS:
                _do_backfill(session, cfg, prog)
        prog.status = _final_status(prog)
    except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job
        prog.status = "failed"
        _record_error(prog, str(exc))
    finally:
        prog.finished_at = _utcnow()
        prog.message = _final_summary(prog)
        try:
            _persist_run(eng, cfg, prog)
        except Exception as exc:  # noqa: BLE001 — persistence failure must not crash the worker thread
            _record_error(prog, f"failed to persist run summary: {exc}")
    return prog.to_dict()


def start_data_job(
    kind: str,
    start: date_cls,
    end: date_cls,
    *,
    source: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
) -> str:
    """Register a job and run it ASYNCHRONOUSLY in a daemon thread; return the `job_id` immediately so
    the POST handler responds without blocking. The thread opens its own session on the given engine.

    `source` (J-33) is the chosen import provider id, recorded on the job (not secret) and defaulted to
    `data_manager.default_source`. `api_key` is the SESSION-ONLY pasted key — passed to the worker as a
    request-only thread argument and NEVER stored on the job/registry (anti-goal: keys are env-or-session,
    never persisted)."""
    cfg = config or get_config()
    eng = engine or get_engine()
    job = create_job(kind, start, end, source=source or cfg.data_manager.default_source)
    thread = threading.Thread(
        target=run_data_job,
        args=(job.job_id,),
        kwargs={"config": cfg, "engine": eng, "api_key": api_key},
        daemon=True,
        name=f"data-job-{job.job_id}",
    )
    thread.start()
    return job.job_id


# --------------------------------------------------------------------------------------------------
# Run history (GET /api/data) — read the append-only DataProviderRun log
# --------------------------------------------------------------------------------------------------
def summarize_provider_run(run: DataProviderRun) -> dict:
    """One run-history row for the UI. A Data Manager job encodes structured detail as JSON in
    `message`; a plain seed-load row (non-JSON message) renders with null job fields + its raw message."""
    detail: dict = {}
    if run.message:
        try:
            parsed = json.loads(run.message)
            if isinstance(parsed, dict):
                detail = parsed
        except (ValueError, TypeError):
            detail = {}
    is_job = "kind" in detail
    return {
        "id": run.id,
        "provider": run.provider,
        "kind": detail.get("kind"),
        "start": detail.get("start"),
        "end": detail.get("end"),
        "status": run.status,
        "symbols_ok": run.symbols_ok,
        "symbols_failed": run.symbols_failed,
        "snapshots_created": detail.get("snapshots_created"),
        "dates_done": detail.get("dates_done"),
        "dates_total": detail.get("dates_total"),
        "bars_fetched": detail.get("bars_fetched"),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "message": detail.get("summary") if is_job else run.message,
    }


def recent_runs(session: Session, config: Optional[Config] = None) -> list[dict]:
    """The recent fetch/backfill (and seed-load) run history, newest first, capped at
    `config.data_manager.run_history_limit`."""
    cfg = config or get_config()
    rows = session.exec(
        select(DataProviderRun)
        .order_by(DataProviderRun.started_at.desc(), DataProviderRun.id.desc())
        .limit(cfg.data_manager.run_history_limit)
    ).all()
    return [summarize_provider_run(run) for run in rows]
