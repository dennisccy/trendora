"""Readiness state producer (Data Contract: app.engine.readiness) — iter-28, J-40.

The SINGLE honest readiness computer. It returns ONE state ∈ {`ready`, `initializing`, `unavailable`}
plus the background warm-up progress `{done, total}` (cadence snapshots produced / expected — "history
n/m"), computed ONCE here and served by the SINGLE canonical readiness endpoint (the extended
`GET /api/health`). It is descriptive operational/job-control state — NOT a canonical score/return/bucket
and NOT a duplicate of any existing value; it recomputes nothing (anti-goal: No recompute in the read path
does not apply — readiness is not a snapshot value, it is liveness about whether the snapshots are servable).

The state is reported HONESTLY (anti-goal: Readiness is reported honestly):
  - `unavailable` — the DB is unreachable, OR there is no latest snapshot servable yet (no price data /
    the synchronous latest-snapshot step has not produced the latest run). NEVER a fabricated `ready`.
  - `initializing` — the latest snapshot IS servable (so the core read pages work) but the background
    historical warm-up is still in flight (or has not started / has failed): `done < total`, or the
    warm-up record reports `running`/`failed`. A still-warming backend is NEVER mislabeled `unavailable`.
  - `ready` — the latest snapshot is servable AND the historical warm-up has finished (`done >= total`,
    e.g. all cadence snapshots present). `ready` is NEVER reported before the latest snapshot is servable.

`warmup` carries `{done, total, status, message}` so the frontend badge renders live "history n/m"
progress and the analytics pages show their "warming up (n/m)" state — both reading THIS single value
(the frontend never computes readiness itself).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import Config, get_config
from app.engine.prices import latest_data_date
from app.engine.scanner import get_run_for_date
from app.engine.warmup import _warmup_dates, get_warmup
from app.models import DailyPrice, ScannerRun

READY = "ready"
INITIALIZING = "initializing"
UNAVAILABLE = "unavailable"


def _latest_run_date(session: Session):
    """The most recent persisted run's as-of date, or None when no snapshot is stored yet."""
    return session.scalar(select(func.max(ScannerRun.asof_date)))


def compute_readiness(
    session: Session, engine=None, config: Optional[Config] = None
) -> dict:
    """Compute the single honest readiness state + warm-up progress (Data Contract value).

    `engine` is used only to compute the warm-up `total` (the expected cadence-snapshot count) when no
    warm-up record exists yet (e.g. readiness probed before `start_warmup`); when a warm-up record is
    present its own `dates_total`/`dates_done` are authoritative. Reads ONLY the DB + the in-memory
    warm-up record — it never recomputes a canonical score/return/bucket."""
    cfg = config or get_config()

    # DB reachability + the servable-latest check, both in one guarded block: a DB error -> unavailable
    # (surfaced, never faked).
    try:
        latest_data = latest_data_date(session)
        latest_run = _latest_run_date(session)
        db_ok = True
    except Exception:  # pragma: no cover - DB unreachable is surfaced, never faked
        latest_data = None
        latest_run = None
        db_ok = False

    # The latest snapshot is "servable" when the latest data date has a persisted run (the synchronous
    # boot's `ensure_latest_snapshot` produced it). No data / no latest run -> not yet servable.
    latest_servable = bool(latest_data is not None and latest_run is not None and latest_run >= latest_data)

    # The honest cadence-warm-up progress. The expected `total` is the full historical cadence set (the
    # background warm-up's denominator); `done` is how many of those snapshots are ACTUALLY persisted in
    # the DB right now — the ground truth, independent of whether the in-process warm-up thread is alive.
    # The in-memory warm-up record (when present) supplies the live `status`/`message` for the badge, but
    # the DB-derived `done`/`total` keep the signal correct on a warm DB even with no thread running.
    if db_ok and latest_data is not None:
        cadence_dates = _warmup_dates(session, cfg)
        total = len(cadence_dates)
        done = sum(1 for d in cadence_dates if get_run_for_date(session, d) is not None)
    else:
        cadence_dates = []
        total = 0
        done = 0

    warmup = get_warmup()
    if warmup is not None:
        status = warmup.get("status", "running")
        # prefer the live record's progress when it is ahead of the DB read (covers the brief window
        # before a just-committed snapshot is visible to this session), but never below the DB ground truth
        done = max(done, int(warmup.get("dates_done", 0)))
        if int(warmup.get("dates_total", 0)) > total:
            total = int(warmup.get("dates_total", 0))
    else:
        # No warm-up launched in this process (readiness probed during the synchronous boot, or a test
        # that never starts the background task). The DB ground truth above is authoritative.
        status = "ok" if done >= total else "pending"

    message = f"history {done}/{total}"

    # The honest state. unavailable dominates (no servable latest). Otherwise ready iff the historical
    # warm-up is COMPLETE (every cadence snapshot persisted) AND the warm-up is not still actively running
    # and did not fail — so the badge truthfully shows the flip to Ready only once warm-up settles. A
    # `running` record stays `initializing` even when its snapshots are all present (its forward-returns
    # backfill may still be in flight); a `failed` record never reports `ready` (honest, not a silent
    # green); `pending` (no in-process warm-up / DB-derived-complete on a warm DB) with all snapshots
    # present is ready. A still-warming / failed backend is NEVER mislabeled unavailable.
    if not db_ok or not latest_servable:
        state = UNAVAILABLE
    elif done >= total and status in ("ok", "pending"):
        state = READY
    else:
        state = INITIALIZING

    return {
        "state": state,
        "warmup": {
            "done": done,
            "total": total,
            "status": status,
            "message": message,
        },
    }
