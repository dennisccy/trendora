"""Iter-66 (J-07) -- concurrent GIL-stall profile: the `coverage_membership_timeline_refresh` sub-chain
vs a REAL `/api/health` call, mirroring iter-65's own `stall_profile_concurrent.py` methodology
(perf-budgets.md Addendum 31), retargeted to this phase per this iteration's own spec.

The solo profile (stall_profile_coverage.py, same directory) found ZERO stalls > 0.30s across the whole
`_compute_coverage_body` read-only sub-chain run alone against the real committed DB. But iter-61/63/65's
own live TC-1 drills each still measured exactly ONE `GET /api/health` breach landing inside
`coverage_membership_timeline_refresh`'s own logged window (2.849s / 2.420s / 2.370s respectively) despite
iter-63's cooperative-yield fix to `_missing_data_diagnostic`'s own-dates loop. Per Addendum 29's own
"Honest next-step note" ("profile `_missing_data_diagnostic` UNDER live concurrent load specifically... the
isolated 1.426s figure alone does not explain the full 7.05s logged phase duration"), this script
reproduces the concurrent condition the solo profile cannot: a second thread issuing the REAL `/api/health`
route's own DB queries WHILE the coverage sub-chain runs in the worker thread, in-process, against the
real committed DB, no ingest job needed.

Deliberately OMITS `membership_timeline_cached` (the one write in `_compute_coverage_body`'s chain) for
the same safety reason as `stall_profile_coverage.py` -- see that script's own docstring; it was already
independently measured at 0.040s / zero stalls in iter-63's own isolated pass."""
from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from collections import Counter

sys.path.insert(0, ".")  # run with cwd = apps/backend

from sqlmodel import Session  # noqa: E402

from app.api.health import health as health_route  # noqa: E402
from app.config import get_config  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.engine import data_manager  # noqa: E402
from app.engine.prices import prefilled_bar_cache  # noqa: E402
from app.engine.universe_screen import read_pool  # noqa: E402

HEALTH_CEILING_S = 2.0  # the J-07 acceptance ceiling during a bounded background-compute window
POLL_INTERVAL_S = 1.0

health_polls: list[dict] = []
worker_result: dict = {}
worker_ident: list[int] = [0]
worker_done = threading.Event()
phase_marks: list[dict] = []


def _innermost_app_frame(stack_lines: list[str]) -> str:
    for line in reversed(stack_lines):
        if "data_manager.py" in line or "universe_resolver.py" in line or "prices.py" in line:
            return line.strip()
    return stack_lines[-1].strip() if stack_lines else ""


def health_sim() -> None:
    poll_id = 0
    while not worker_done.is_set():
        t0 = time.perf_counter()
        session = Session(get_engine())
        ok = True
        err = None
        try:
            health_route(session=session)
        except Exception as exc:  # noqa: BLE001 -- record, never crash the drill
            ok = False
            err = repr(exc)
        finally:
            session.close()
        elapsed = time.perf_counter() - t0
        poll_id += 1
        entry = {
            "poll_id": poll_id,
            "t": round(t0, 3),
            "elapsed_s": round(elapsed, 3),
            "ok": ok,
            "err": err,
            "breach": elapsed > HEALTH_CEILING_S,
        }
        if entry["breach"] or not ok:
            frames = sys._current_frames()
            frame = frames.get(worker_ident[0])
            stack_lines = traceback.format_stack(frame) if frame is not None else []
            entry["worker_innermost_app_frame"] = _innermost_app_frame(stack_lines)
            entry["worker_stack"] = [ln.strip() for ln in stack_lines[-8:]]
            print(json.dumps(entry), flush=True)
        health_polls.append(entry)
        remaining = POLL_INTERVAL_S - (time.perf_counter() - t0)
        if remaining > 0:
            time.sleep(remaining)


def _mark(name: str, t0: float) -> None:
    elapsed = time.perf_counter() - t0
    phase_marks.append({"step": name, "elapsed_s": round(elapsed, 3)})
    print(f"=== STEP {name}: {elapsed:.3f}s ===", flush=True)


def worker() -> None:
    worker_ident[0] = threading.get_ident()
    cfg = get_config()
    session = Session(get_engine())
    try:
        pool_symbols = {row["symbol"] for row in read_pool()}
        t0 = time.perf_counter()
        with prefilled_bar_cache(session, expected_symbols=pool_symbols) as _cache:
            _mark("prefill", t0)

            as_of = None
            t0 = time.perf_counter()
            trading_days = data_manager._trading_days(session, cfg)
            _mark("_trading_days", t0)

            t0 = time.perf_counter()
            resolved = data_manager._resolved_universe(session, as_of, cfg)
            _mark("_resolved_universe", t0)

            t0 = time.perf_counter()
            _per_symbol = data_manager._per_symbol_coverage(session, cfg)
            _mark("_per_symbol_coverage", t0)

            t0 = time.perf_counter()
            _diag = data_manager._missing_data_diagnostic(session, cfg, calendar=trading_days)
            _mark("_missing_data_diagnostic", t0)

            t0 = time.perf_counter()
            _udiag = data_manager._universe_diagnostic(resolved, cfg)
            _mark("_universe_diagnostic", t0)

            t0 = time.perf_counter()
            _absent = data_manager._coverage_diagnostic_absent(
                session, cfg, universe=resolved["admitted"]
            )
            _mark("_coverage_diagnostic_absent", t0)

        worker_result["trading_days_count"] = len(trading_days)
        worker_result["universe_count"] = len(resolved["admitted"])
        worker_result["per_symbol_rows"] = len(_per_symbol)
        worker_result["missing_data_affected"] = _diag.get("affected_count")
        worker_result["absent_count"] = _absent.get("absent_count")
    finally:
        session.close()
        worker_done.set()


def main() -> None:
    t_start = time.perf_counter()
    health_thread = threading.Thread(target=health_sim, name="health-sim", daemon=True)
    worker_thread = threading.Thread(target=worker, name="coverage-refresh-worker")

    worker_thread.start()
    time.sleep(0.05)
    health_thread.start()
    worker_thread.join()
    time.sleep(POLL_INTERVAL_S + 0.5)
    worker_done.set()
    health_thread.join(timeout=5.0)
    total_elapsed = time.perf_counter() - t_start

    breaches = [p for p in health_polls if p["breach"]]
    errors = [p for p in health_polls if not p["ok"]]
    by_frame = Counter(p.get("worker_innermost_app_frame", "") for p in breaches + errors)
    summary = {
        "total_elapsed_s": round(total_elapsed, 2),
        "worker_result": worker_result,
        "phase_marks": phase_marks,
        "health_polls_total": len(health_polls),
        "health_polls_breach_gt_2s": len(breaches),
        "health_polls_error": len(errors),
        "worst_health_elapsed_s": max((p["elapsed_s"] for p in health_polls), default=0.0),
        "breaches_by_worker_innermost_app_frame": by_frame.most_common(20),
    }
    print("=== SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    with open("stall_profile_coverage_concurrent_summary.json", "w") as f:
        json.dump({"summary": summary, "health_polls": health_polls}, f, indent=2)


if __name__ == "__main__":
    main()
