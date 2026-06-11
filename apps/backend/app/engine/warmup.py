"""Background warm-up controller (Data Contract: app.engine.warmup) — iter-28, J-40/J-41.

The FastAPI `lifespan` (apps/backend/main.py) now does only the MINIMAL synchronous work needed to
serve the LATEST as-of snapshot before it yields (config -> tables -> seed -> `ensure_latest_snapshot`),
then begins accepting connections. The full historical walk-forward — the configured `bootstrap_runs`
cadence (minus the latest date already done synchronously) plus `backfill_forward_returns` — is produced
by THIS background warm-up task, launched AFTER `yield` so the boot path never blocks serving (not even
`/health`) on the multi-minute backfill (anti-goal: Startup must not block serving on historical warm-up).

It REUSES the EXISTING async-job machinery — the `data_manager.JobProgress` record + the `_JOBS` registry
+ the daemon-thread spawn pattern — rather than introducing a second job/threading abstraction (goal
capability #32). The warm-up calls the SAME canonical engines (`scanner.bootstrap_runs`,
`forward_testing.backfill_forward_returns`) — only the SCHEDULING moves; no second compute path, so the
warmed cadence snapshots + forward returns are byte-identical to the pre-change synchronous output.

Warm-up progress (`{done, total}` cadence snapshots produced / expected) lives in the in-memory
`JobProgress` record (`dates_done` / `dates_total`) — readiness is COMPUTED from the DB + this record, never
stored. A warm-up failure is CAUGHT, logged, and NON-FATAL (anti-goal: Warm-up ... is non-fatal): the
server keeps serving already-persisted snapshots, readiness reports the failure honestly (not a silent
green), and the NEXT boot completes the idempotent warm-up. Every startup tunable (the warm-up batch
size) comes from `config.startup` — no magic number here.
"""
from __future__ import annotations

import logging
import threading
from datetime import date as date_cls
from typing import Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.config import Config, get_config
from app.engine import data_manager
from app.engine.forward_testing import backfill_forward_returns, walk_forward_asof_dates
from app.engine.prices import bar_cache, latest_data_date
from app.engine.scanner import get_run_for_date, run_scan

logger = logging.getLogger("trendora.warmup")

# The single warm-up kind label carried on the reused JobProgress record (NOT a data-manager fetch/
# backfill kind — the warm-up reuses the SAME registry/record/thread pattern, not the _run_job worker).
WARMUP_KIND = "warmup"

# The id under which the (single) warm-up job is registered in data_manager._JOBS. Deterministic so the
# readiness module can find the current warm-up without threading an id through the app — there is at most
# one warm-up per process (the lifespan launches exactly one). A re-launch after completion/failure
# overwrites the prior record (the next boot finishes the idempotent remainder).
WARMUP_JOB_ID = "warmup"

# SINGLE-FLIGHT guard (J-41 re-spawn resilience): a reference to the in-process warm-up thread + a lock
# that serializes the check-and-spawn. While a warm-up is RUNNING in this process (the thread is alive),
# a re-invocation of `start_warmup` (a readiness-probe re-spawn, a uvicorn `--reload` double-fire, or —
# critically — every `TestClient(main.app)` lifespan entry over the shared test DB) MUST NOT spawn a
# duplicate concurrent worker; it returns the existing job id instead. A re-launch AFTER the worker has
# settled (completed/failed) IS allowed (the next boot completes the idempotent remainder). Without this
# guard, repeated TestClient entries spawned N concurrent daemon warm-ups all writing the one SQLite test
# DB — the source of the iter-28 QA-gate non-determinism + the multi-minute write-contention crawl.
_WARMUP_LOCK = threading.Lock()
_WARMUP_THREAD: Optional[threading.Thread] = None


def _warmup_dates(session: Session, cfg: Config) -> list[date_cls]:
    """The cadence as-of dates the BACKGROUND warm-up must still produce: the union of the configured
    `scanner.bootstrap_dates` and the walk-forward cadence (`walk_forward_asof_dates`), de-duplicated and
    ascending, EXCLUDING the latest data date (which the synchronous boot already persisted via
    `ensure_latest_snapshot`). This is exactly the historical work moved off the boot path — its length
    is the honest `total` of the readiness `{done, total}` progress."""
    latest = latest_data_date(session)
    if latest is None:
        return []
    dates: set[date_cls] = set(cfg.scanner.bootstrap_dates)
    dates.update(walk_forward_asof_dates(session, cfg))
    dates.discard(latest)  # the latest snapshot is produced synchronously before serving
    return sorted(dates)


def ensure_latest_snapshot(engine: Engine, config: Optional[Config] = None) -> Optional[date_cls]:
    """The MINIMAL synchronous boot step: persist (idempotently) ONLY the immutable snapshot for the
    LATEST data date, so the server can serve the core read pages for the latest as-of immediately on
    `yield`. Effectively instant on a warm DB (the run already exists -> `run_scan` returns it); on a
    fresh DB it is a single snapshot compute, bounded by `config.startup.readiness_budget_seconds`. Reads
    ONLY the committed frozen seed via the canonical engines (no network). Returns the latest data date,
    or None when no price data exists yet (the readiness signal then reports `unavailable`)."""
    cfg = config or get_config()
    with Session(engine) as session:
        latest = latest_data_date(session)
        if latest is None:
            return None
        run_scan(session, latest, cfg)  # idempotent + immutable; the SINGLE canonical compute path
        return latest


def warmup_total(engine: Engine, config: Optional[Config] = None) -> int:
    """How many cadence snapshots the BACKGROUND warm-up will produce (the readiness `total`). Computed
    from the same `_warmup_dates` set the worker iterates, so `done`/`total` are always consistent."""
    cfg = config or get_config()
    with Session(engine) as session:
        return len(_warmup_dates(session, cfg))


def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -> None:
    """The warm-up worker body (runs in the daemon thread). Persists each remaining cadence snapshot via
    the canonical `run_scan` (batched by `config.startup.warmup_batch_size` for progress ticks), then runs
    `backfill_forward_returns` for the realized forward returns — the SAME engines the synchronous boot
    used, only rescheduled. Any exception is CAUGHT + logged and marks the job `failed` (non-fatal): the
    server keeps serving, readiness reports the failure honestly, and the next boot finishes the
    idempotent remainder. INSERT-only + idempotent + concurrency-safe (the engines' own guards)."""
    batch_size = cfg.startup.warmup_batch_size
    try:
        with Session(engine) as session:
            dates = _warmup_dates(session, cfg)
            prog.dates_total = len(dates)
            prog.snapshots_created = sum(
                1 for d in dates if get_run_for_date(session, d) is not None
            )
            prog.dates_done = prog.snapshots_created
            prog.message = f"history {prog.dates_done}/{prog.dates_total}"
            # J-46 (Capability 33): the warm-up's cadence loop is the SAME read-only multi-date
            # `run_scan` pattern as the Data Manager backfill — activate the load-once bar cache so each
            # symbol's full series loads ONCE for the whole warm-up (not once per cadence date). This is
            # orthogonal to the iter-28 single-flight guard (which serializes the warm-up THREAD in
            # `start_warmup`); the cache only changes how this thread's own session loads bars. The cache
            # dies with the `with Session` block; the warm-up adds no bars, so no read sees a stale series.
            with bar_cache(session):
                for index, asof in enumerate(dates, start=1):
                    run_scan(session, asof, cfg)  # canonical engine; idempotent + concurrency-safe
                    prog.dates_done = index
                    prog.snapshots_created = index
                    # tick the message on each batch boundary (and the final date) so progress is live
                    if index % batch_size == 0 or index == len(dates):
                        prog.message = f"history {prog.dates_done}/{prog.dates_total}"
        # the realized forward returns over every persisted cadence snapshot (idempotent INSERT-only,
        # concurrency-safe) — the SAME engine the synchronous boot ran, only rescheduled.
        result = backfill_forward_returns(engine, cfg)
        prog.forward_returns_inserted = result["rows_inserted"]
        prog.status = "ok"
        prog.message = f"history {prog.dates_total}/{prog.dates_total}"
    except Exception as exc:  # NON-FATAL: caught + logged, never re-raised out of the thread
        prog.status = "failed"
        prog.errors.append(str(exc))
        prog.message = "warm-up failed (serving persisted snapshots; will retry on next boot)"
        logger.exception("background warm-up failed (non-fatal): %s", exc)
    finally:
        prog.finished_at = data_manager._utcnow()


def start_warmup(engine: Engine, config: Optional[Config] = None) -> str:
    """Register the (single) warm-up `JobProgress` in the EXISTING `data_manager._JOBS` registry and run
    it ASYNCHRONOUSLY in a daemon thread (the SAME pattern as `data_manager.start_data_job`) — returning
    the job id immediately so the lifespan never blocks on the historical backfill. The thread opens its
    own session on `engine`. Reuses the existing record/registry/thread machinery (no second job/threading
    abstraction). A warm-up exception is caught inside the worker (non-fatal), so the spawn never raises.

    SINGLE-FLIGHT (J-41): if a warm-up is ALREADY running in this process (its daemon thread is still
    alive), this is a no-op that returns the existing `WARMUP_JOB_ID` WITHOUT spawning a second concurrent
    worker — so a readiness-probe re-spawn / `--reload` double-fire / repeated `TestClient` lifespan entry
    never multiplies the work or races the shared DB. A re-launch after the prior warm-up has settled
    (completed/failed) proceeds normally (the next boot completes the idempotent remainder)."""
    cfg = config or get_config()
    global _WARMUP_THREAD
    with _WARMUP_LOCK:
        # Single-flight: a still-alive warm-up thread means a warm-up is in flight — do not spawn another.
        if _WARMUP_THREAD is not None and _WARMUP_THREAD.is_alive():
            return WARMUP_JOB_ID
        total = warmup_total(engine, cfg)
        prog = data_manager.JobProgress(
            job_id=WARMUP_JOB_ID, kind=WARMUP_KIND, start=date_cls.min, end=date_cls.min
        )
        prog.dates_total = total
        prog.message = f"history 0/{total}"
        with data_manager._LOCK:
            data_manager._JOBS[prog.job_id] = prog
        thread = threading.Thread(
            target=_run_warmup,
            args=(engine, cfg, prog),
            daemon=True,
            name=f"warmup-{prog.job_id}",
        )
        _WARMUP_THREAD = thread
        thread.start()
        return prog.job_id


def get_warmup() -> Optional[dict]:
    """A serializable snapshot of the current warm-up job's live progress (from the shared `_JOBS`
    registry), or None when no warm-up has been launched in this process. The readiness module reads this
    — there is NO second warm-up registry."""
    return data_manager.get_job(WARMUP_JOB_ID)
