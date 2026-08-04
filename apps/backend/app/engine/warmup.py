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
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine import data_manager, evidence, forward_testing
from app.engine.forward_testing import backfill_forward_returns, walk_forward_asof_dates
from app.engine.ledger import FORWARD_WALK_TYPE, read_entries
from app.engine.prices import bar_cache, latest_data_date
from app.engine.scanner import get_run_for_date, run_scan
from app.models import ScannerRun

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


def _warm_membership_timeline(engine: Engine, cfg: Config) -> None:
    """iter-36 (J-96): precompute + persist the dynamic-universe membership-timeline cache so the FIRST
    `GET /api/data` after a boot/rebuild serves the cached payload instead of paying the O(dates × pool)
    `resolve_with_reasons` derivation synchronously. Opens its OWN session on `engine` (never a request
    session). Calls `data_manager.membership_timeline_cached` with the FULL stored snapshot-date set — on
    a cold cache it computes once and upserts under the current membership-dataset stamp (J-100: the NARROW
    `_membership_dataset_version` — the snapshot set + bars manifest, NOT the forward-return count); if a
    row already exists for the current stamp it is a cheap no-op hit. NON-FATAL: any exception is caught + logged here
    so a timeline-cache failure never aborts the otherwise-successful warm-up (the cold-miss read still
    serves the bounded compute). Reads the committed bars/runs only; computes no canonical value."""
    try:
        with Session(engine) as session:
            snapshot_dates = sorted(session.exec(select(ScannerRun.asof_date)).all())
            data_manager.membership_timeline_cached(session, cfg, snapshot_dates)
            logger.info("membership-timeline cache warmed (%d snapshot dates)", len(snapshot_dates))
    except Exception as exc:  # NON-FATAL: a timeline-cache warm failure must not fail the whole warm-up
        logger.exception("membership-timeline cache warm failed (non-fatal): %s", exc)


def _warm_coverage_snapshot(engine: Engine, cfg: Config) -> None:
    """ops-hardening iter-2 (J-05): the boot-time safety net for a not-yet-ingested-once database — persist
    a `CoverageSnapshot` row for the CURRENT `(asof_key, dataset_version)` stamp ONLY IF no row exists yet
    for it. Mirrors `_warm_membership_timeline`'s exact contract: opens its OWN session on `engine` (never a
    request session), is idempotent (a no-op when a row already exists — this is a bootstrap safety net,
    not a per-boot refresh; the ingest finalize hook is what keeps it fresh thereafter), and is NON-FATAL
    (any exception is caught + logged here so a coverage-warm failure never aborts the otherwise-successful
    warm-up). Reads the committed bars/runs only; computes no canonical value — it reuses
    `data_manager.refresh_coverage_snapshot`, which itself reuses `_compute_coverage_uncached` verbatim."""
    try:
        with Session(engine) as session:
            resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
            if resolved_asof is None:
                return  # wholly empty DB (no bars at all) — nothing to snapshot yet
            asof_key = resolved_asof.isoformat()
            dataset_version = data_manager._membership_dataset_version(session, cfg)
            existing = session.exec(
                select(data_manager.CoverageSnapshot).where(
                    data_manager.CoverageSnapshot.asof_key == asof_key,
                    data_manager.CoverageSnapshot.dataset_version == dataset_version,
                )
            ).first()
            if existing is not None:
                return  # already computed under the current stamp — idempotent no-op
            data_manager.refresh_coverage_snapshot(session, cfg)
            logger.info("coverage snapshot warmed (asof=%s)", asof_key)
    except Exception as exc:  # NON-FATAL: a coverage-snapshot warm failure must not fail the whole warm-up
        logger.exception("coverage snapshot warm failed (non-fatal): %s", exc)


def _warm_drawdown_expectations(engine: Engine, cfg: Config) -> None:
    """ops-hardening iter-46 FIX PASS (QA blocker 3 — J-06/J-07): precompute the per-claim
    `drawdown_expectations` EventStudyCache rows `GET /api/evidence` looks up lazily, so the FIRST Evidence
    page view after a BOOT is a cache hit instead of a multi-minute synchronous cold compute on the request
    path.

    WHY THIS EXISTS: the ingest finalize tail already warms exactly this cache
    (`data_manager._refresh_ingest_aggregates`'s ledger loop, iter-7/audit B1), but nothing warmed it after
    a plain RESTART — so every backend restart left the next Evidence viewer paying the full cold miss.
    Measured on this host against the live DB, with the backend idle and NO ingest job running: a cold
    `GET /api/evidence` returned HTTP 200 in **163.3s**; the immediately-following requests served in
    **11-52ms**. The committed budget (`reports/perf-budgets.md` Item I) is the WARM steady-state ≤3s, so
    closing the post-restart cold window is what makes that budget real for a user who simply opens the
    page after a restart.

    CONTRACT — mirrors `_warm_membership_timeline` / `_warm_coverage_snapshot` verbatim: opens its OWN
    session on `engine` (never a request session); is IDEMPOTENT (each claim's call is
    `compute_drawdown_expectations_cached`, so an already-warm row is a cheap HIT, never a recompute);
    computes no canonical value (the cached payload IS the canonical compute, persisted); and is NON-FATAL
    at BOTH levels — one unresolvable/erroring claim never blocks the others, and no failure here can flip
    an otherwise-successful warm-up to `failed`.

    Applies the SAME two filters `evidence.build_evidence_payload` and the finalize tail already apply, so
    the warmed cache subjects match exactly what a live `/api/evidence` request looks up: skip
    `type == FORWARD_WALK_TYPE` monitoring records (they re-score an existing claim — not a claim with a
    panel of its own), and take the claim via `entry.get("claim")`.

    SEQUENCING (load-bearing): `_run_warmup` calls this only AFTER it has set `prog.status = "ok"`. This
    step is expensive, and the readiness badge J-04 and J-07 step 1 depend on must flip `Ready` on exactly
    the schedule it did before this fix — so this warm is deliberately OUTSIDE the readiness path. The
    consequence is disclosed honestly: an Evidence view landing inside the short window between `ok` and
    this warm's completion still pays the cold miss."""
    try:
        entries = read_entries(evidence.resolve_ledger_path())
    except Exception as exc:  # NON-FATAL: a missing/corrupt ledger degrades to zero warm calls
        logger.exception("evidence drawdown-expectations ledger read failed (non-fatal): %s", exc)
        return
    warmed = 0
    try:
        with Session(engine) as session:
            for entry in entries:
                if not isinstance(entry, dict) or entry.get("type") == FORWARD_WALK_TYPE:
                    continue
                claim = entry.get("claim") if isinstance(entry.get("claim"), dict) else {}
                try:
                    if forward_testing.compute_drawdown_expectations_cached(session, claim, cfg) is not None:
                        warmed += 1
                # A `MemoryError` stops THIS loop immediately rather than hammering the next claim's
                # allocation under real pressure — the module-wide iter-8 isolation convention. Caught
                # distinctly from the generic per-claim continue below, and tested against a TEXTLESS
                # `MemoryError` (`str(MemoryError())` is `""`).
                except MemoryError as exc:
                    # ops-hardening iter-47 (carried from iter-44/45/46): `_log_isolation_failure`, NOT a
                    # bare `logger.exception` — under the SAME exhausted `ulimit -v` cap that raised this
                    # `MemoryError`, rendering the full traceback can itself allocate and raise a SECOND
                    # exception that would escape this handler before `_release_process_memory()` runs.
                    data_manager._log_isolation_failure(
                        "evidence drawdown-expectations warm aborted — memory pressure, stopping remaining "
                        "claims: %r", exc,
                    )
                    data_manager._release_process_memory()
                    break
                except Exception as exc:  # NON-FATAL: one bad claim never blocks the others
                    data_manager._log_isolation_failure(
                        "evidence drawdown-expectations warm failed for one claim (non-fatal): %r", exc
                    )
        logger.info("evidence drawdown-expectations cache warmed (%d claim panels)", warmed)
    except Exception as exc:  # NON-FATAL: must never fail the otherwise-successful warm-up
        logger.exception("evidence drawdown-expectations cache warm failed (non-fatal): %s", exc)


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
                # iter-26 (J-16, item F): the realized forward returns over every persisted cadence
                # snapshot (idempotent INSERT-only, concurrency-safe) — the SAME engine the synchronous
                # boot ran, only rescheduled. Moved INSIDE this `with bar_cache(session):` block AND
                # passed `session` (not `engine`): `backfill_forward_returns` branches on
                # `isinstance(session_or_engine, Session)` — passed the engine, it used to open a BRAND
                # NEW session with a different id(), which the cache registry (keyed by id(session))
                # never finds, so every close_on/bars_after call re-queried the DB per (run, symbol)
                # regardless of the cache above. Passing this SAME session reuses the exact cache already
                # active, so its close_on/bars_after calls (now cache-aware — see prices.py) read the
                # already-loaded series instead of round-tripping the DB. Output is byte-identical either
                # way (same rows/values; only the load path changes).
                result = backfill_forward_returns(session, cfg)
                prog.forward_returns_inserted = result["rows_inserted"]
        # iter-36 (J-96): precompute the dynamic-universe membership-timeline cache OFF the boot path so
        # the FIRST `GET /api/data` after a boot/rebuild serves the cached payload rather than paying the
        # O(dates × pool) `resolve_with_reasons` derivation synchronously (the iter-35 regression). This is
        # the J-40/J-41 serve-fast precedent. iter-42 (J-100): the membership cache now keys on the NARROW
        # `_membership_dataset_version` (snapshot set + bars manifest), which is INDEPENDENT of the
        # forward-return inserts above — so the warmed row stays VALID across the forward-return backfill
        # (no recompute storm) and is the exact stamp a subsequent read looks up. The cached payload is byte-identical to a fresh
        # compute (it IS a fresh compute, persisted). Wrapped in its OWN guard so a timeline-cache failure
        # is logged but does NOT flip an otherwise-successful warm-up to `failed` (the cadence snapshots +
        # forward returns already succeeded; a cold `GET /api/data` still serves the bounded miss).
        _warm_membership_timeline(engine, cfg)
        # ops-hardening iter-2 (J-05): the coverage_snapshot boot-time safety net — own guard, own session,
        # non-fatal, idempotent (no-op once a row exists) — so a not-yet-ingested-once DB still has a
        # coverage_snapshot row before the first `GET /api/data` request, without the boot path itself
        # gaining any new synchronous compute (this step runs strictly in this background warm-up thread,
        # after `yield`).
        _warm_coverage_snapshot(engine, cfg)
        prog.status = "ok"
        prog.message = f"history {prog.dates_total}/{prog.dates_total}"
    except Exception as exc:  # NON-FATAL: caught + logged, never re-raised out of the thread
        prog.status = "failed"
        prog.errors.append(str(exc))
        prog.message = "warm-up failed (serving persisted snapshots; will retry on next boot)"
        logger.exception("background warm-up failed (non-fatal): %s", exc)
    finally:
        prog.finished_at = data_manager._utcnow()
    # ops-hardening iter-46 FIX PASS (QA blocker 3 — J-06/J-07): warm the per-claim evidence
    # (drawdown-expectations) cache LAST, strictly AFTER the warm-up record has fully settled above — this
    # step is expensive (163.3s measured live for the 7 committed claims) and the readiness badge J-04 and
    # J-07 step 1 depend on must flip `Ready` on exactly the schedule it did before this fix. Placed after
    # the `finally` (not inside the `try`) so it can never influence the warm-up's own status/timing, and
    # gated on a SUCCESSFUL warm-up: a failed warm-up leaves the basis partial, and the ingest finalize
    # tail already owns the post-ingest warm for that path. `_warm_drawdown_expectations` never raises (it
    # is fully guarded at both the ledger-read and per-claim levels), so this call cannot break the thread.
    if prog.status == "ok":
        _warm_drawdown_expectations(engine, cfg)


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
