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
import threading
import uuid
from dataclasses import dataclass, field
from datetime import date as date_cls, datetime, timezone
from typing import Optional

from sqlalchemy import func, insert
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import Config, get_config
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
        "snapshot_count": len(snapshot_dates),
        "snapshot_dates": [d.isoformat() for d in sorted(snapshot_dates, reverse=True)],
        "trading_day_count": len(trading_days),
        "gap_count": len(gaps),
        "gap_first": gaps[0].isoformat() if gaps else None,
        "gap_last": gaps[-1].isoformat() if gaps else None,
        "gaps_preview": [d.isoformat() for d in gaps[:preview]],
    }


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


def create_job(kind: str, start: date_cls, end: date_cls) -> JobProgress:
    """Register a new `running` job in the in-memory registry and return it (with a fresh job_id)."""
    job = JobProgress(job_id=uuid.uuid4().hex, kind=kind, start=start, end=end)
    with _LOCK:
        _JOBS[job.job_id] = job
    return job


def get_job(job_id: str) -> Optional[dict]:
    """A serializable snapshot of a job's live progress, or None for an unknown id."""
    with _LOCK:
        job = _JOBS.get(job_id)
    return job.to_dict() if job is not None else None


def validate_job_request(kind: str, start: date_cls, end: date_cls, config: Optional[Config] = None) -> None:
    """Reject an invalid job request explicitly (the API maps the raised `ValueError` to a 4xx — never a
    silent no-op): an unknown kind, an inverted range (start > end), or a span over the configured
    `data_manager.max_range_days`. Malformed dates are rejected earlier by the typed API model."""
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
    """The provider recorded on the run row: the LIVE provider when a fetch was involved, else the
    offline default provider (the backfill reads the committed seed)."""
    return cfg.data_manager.live_provider if prog.kind in _FETCH_KINDS else cfg.provider


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
) -> dict:
    """Run the registered job to completion SYNCHRONOUSLY (the worker body; `start_data_job` runs this in
    a thread). Opens its OWN DB session (never the request's). Updates the in-memory registry as it goes
    and persists the final summary to the append-only `DataProviderRun`. Returns the final snapshot."""
    cfg = config or get_config()
    eng = engine or get_engine()
    with _LOCK:
        prog = _JOBS[job_id]
    try:
        with Session(eng) as session:
            if prog.kind in _FETCH_KINDS:
                live = provider or make_provider(cfg.data_manager.live_provider)
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
    config: Optional[Config] = None,
    engine: Optional[Engine] = None,
) -> str:
    """Register a job and run it ASYNCHRONOUSLY in a daemon thread; return the `job_id` immediately so
    the POST handler responds without blocking. The thread opens its own session on the given engine."""
    cfg = config or get_config()
    eng = engine or get_engine()
    job = create_job(kind, start, end)
    thread = threading.Thread(
        target=run_data_job,
        args=(job.job_id,),
        kwargs={"config": cfg, "engine": eng},
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
