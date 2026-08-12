"""Iter-66 (J-07) -- interrupt-driven GIL-stall profile of `coverage_membership_timeline_refresh`'s
finalize-tail phase, re-running iter-52/53/63's own method (thread-stack sampling on any handler blocked
>0.30s -- see docs/handoffs/goal-ops-hardening-iter-52-dev.md and reports/perf-budgets.md Addendum 29 for
the precedent) against the REAL, unmocked coverage sub-derivations.

Unlike iter-63's own profile (which ran against a throwaway `shutil.copy2` DB copy and disclosed an
18-200x wall-clock slowdown from the cold copy / missing WAL sidecar -- perf-budgets.md Addendum 29), this
pass profiles directly against the REAL committed DB at production speed (warm OS page cache, live WAL),
while staying provably safe: it calls ONLY the read-only sub-derivations `_compute_coverage_body` itself
calls, in the SAME order, and deliberately OMITS `membership_timeline_cached` (the one sub-step that
writes) -- that step was already independently measured at 0.040s / zero stalls in iter-63's own isolated
live pass (Addendum 29, "confirming the fix targeted the right function"), so skipping it here costs
nothing and this script issues no INSERT/UPDATE/DELETE/commit against the real DB.

The worker thread runs, in the real `_compute_coverage_body` order, with a REAL `prefilled_bar_cache`
active (the exact shape `_do_backfill`/`_refresh_ingest_aggregates` set up for a live ingest -- see
`data_manager.py`'s own `_refresh_ingest_aggregates` docstring, "attach `_do_backfill`'s already-loaded
shared `_BarCache`... for the WHOLE finalize tail"):
  1. `_trading_days(session, cfg)`
  2. `_resolved_universe(session, as_of, cfg)`      (-> `universe_resolver.resolve_with_reasons`)
  3. `_per_symbol_coverage(session, cfg)`
  4. `_missing_data_diagnostic(session, cfg, calendar=trading_days)`
  5. `_universe_diagnostic(resolved, cfg)`
  6. `_coverage_diagnostic_absent(session, cfg, universe=...)`

A probe thread samples `time.monotonic()` for gaps > STALL_THRESHOLD and captures the worker thread's live
stack via `sys._current_frames()` at the instant each gap resolves -- identical technique to
runs/goal-ops-hardening-iter-65/evidence-drill/stall_profile.py, retargeted to this phase's own call chain.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from collections import Counter
from datetime import date

# --- repo/env wiring -------------------------------------------------------------------------------
sys.path.insert(0, ".")  # run with cwd = apps/backend

from sqlmodel import Session  # noqa: E402

from app.config import get_config  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.engine import data_manager  # noqa: E402
from app.engine.prices import prefilled_bar_cache  # noqa: E402
from app.engine.universe_screen import read_pool  # noqa: E402

PROBE_INTERVAL = 0.02  # seconds -- fine-grained so short stalls are not missed
STALL_THRESHOLD = 0.30  # seconds -- matches iter-52/53/this session's own binding threshold

stalls: list[dict] = []
worker_result: dict = {}
worker_ident: list[int] = [0]
stop_probe = threading.Event()
phase_marks: list[dict] = []  # wall-clock start/end of each named sub-step, for cross-reference


def _innermost_app_frame(stack_lines: list[str]) -> str:
    """The last data_manager.py/universe_resolver.py/prices.py line in a formatted stack -- the frame
    most likely to be the actual hold, filtering out probe/thread bookkeeping frames."""
    for line in reversed(stack_lines):
        if (
            "data_manager.py" in line
            or "universe_resolver.py" in line
            or "prices.py" in line
        ):
            return line.strip()
    return stack_lines[-1].strip() if stack_lines else ""


def probe() -> None:
    last = time.perf_counter()
    while not stop_probe.is_set():
        time.sleep(PROBE_INTERVAL)
        now = time.perf_counter()
        overrun = (now - last) - PROBE_INTERVAL
        if overrun > STALL_THRESHOLD:
            frames = sys._current_frames()
            frame = frames.get(worker_ident[0])
            stack_lines = traceback.format_stack(frame) if frame is not None else []
            entry = {
                "t": round(now, 3),
                "stall_s": round(overrun + PROBE_INTERVAL, 3),
                "innermost_app_frame": _innermost_app_frame(stack_lines),
                "stack": [ln.strip() for ln in stack_lines[-8:]],
            }
            stalls.append(entry)
            print(json.dumps(entry), flush=True)
        last = now


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
        t_prefill = time.perf_counter()
        with prefilled_bar_cache(session, expected_symbols=pool_symbols) as _cache:
            _mark("prefill", t_prefill)

            t0 = time.perf_counter()
            as_of = None  # mirrors _compute_coverage_body's default (None -> latest run date)
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


def main() -> None:
    t_start = time.perf_counter()
    probe_thread = threading.Thread(target=probe, name="health-probe-sim", daemon=True)
    worker_thread = threading.Thread(target=worker, name="coverage-refresh-worker")

    probe_thread.start()
    time.sleep(0.05)  # let the probe get its first baseline timestamp before the worker starts
    worker_thread.start()
    worker_thread.join()
    stop_probe.set()
    probe_thread.join(timeout=2.0)
    total_elapsed = time.perf_counter() - t_start

    by_frame = Counter(s["innermost_app_frame"] for s in stalls)
    summary = {
        "total_elapsed_s": round(total_elapsed, 2),
        "worker_result": worker_result,
        "phase_marks": phase_marks,
        "stall_count_gt_0.30s": len(stalls),
        "worst_stall_s": max((s["stall_s"] for s in stalls), default=0.0),
        "stalls_by_innermost_app_frame": by_frame.most_common(20),
    }
    print("=== SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    with open("stall_summary_coverage.json", "w") as f:
        json.dump({"summary": summary, "stalls": stalls}, f, indent=2)


if __name__ == "__main__":
    main()
