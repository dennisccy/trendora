"""Iter-65 (J-07) — interrupt-driven GIL-stall profile of `compute_factor_lab_all`.

Re-runs iter-52's own method (see docs/handoffs/goal-ops-hardening-iter-52-dev.md, "FIX PASS — Root
cause"): `compute_factor_lab_all` runs in a WORKER thread against the real committed DB
(apps/backend/data/trendora.db, as_of=None -- the SAME all-history call `factor_lab_all_warm` makes at
ingest finalize); a PROBE thread does nothing but a short `time.sleep(PROBE_INTERVAL)` in a tight loop,
timing how long each sleep call actually took. When the observed overrun beyond the requested interval
exceeds STALL_THRESHOLD, the GIL was almost certainly held elsewhere for that whole span (a Python
thread that is ready to run and briefly sleeping should be rescheduled close to on time -- CPython's
default switch interval is 5ms) -- capture the WORKER thread's stack at that instant via
`sys._current_frames()` (the same "captured at the instant each stall resolved" technique iter-52 used).

Output: one JSON line per stall to stdout (also collected in-memory), plus a final summary grouping by
(function, filename, lineno) of the innermost frame, printed at the end.
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
from app.engine.research import compute_factor_lab_all  # noqa: E402

PROBE_INTERVAL = 0.02  # seconds -- fine-grained so short stalls are not missed
STALL_THRESHOLD = 0.30  # seconds -- matches iter-52's own threshold

stalls: list[dict] = []
worker_result: dict = {}
worker_ident: list[int] = [0]
stop_probe = threading.Event()


def _innermost_app_frame(stack_lines: list[str]) -> str:
    """The last `research.py`/`data_manager.py`/`forward_testing.py` line in a formatted stack -- the
    frame most likely to be the actual hold, filtering out probe/thread bookkeeping frames."""
    for line in reversed(stack_lines):
        if "research.py" in line or "data_manager.py" in line or "forward_testing.py" in line:
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
                "stack": [ln.strip() for ln in stack_lines[-6:]],
            }
            stalls.append(entry)
            print(json.dumps(entry), flush=True)
        last = now


def worker() -> None:
    worker_ident[0] = threading.get_ident()
    cfg = get_config()
    session = Session(get_engine())
    try:
        t0 = time.perf_counter()
        payload = compute_factor_lab_all(session, cfg, as_of=None)
        elapsed = time.perf_counter() - t0
        n_total = sum(
            bh.get("n_total", 0)
            for entry in payload.get("factors_table", [])
            for bh in entry.get("by_horizon", [])
        )
        worker_result["elapsed_s"] = round(elapsed, 2)
        worker_result["sum_n_total"] = n_total
        worker_result["n_factors"] = len(payload.get("factors_table", []))
        worker_result["horizons"] = payload.get("horizons")
    finally:
        session.close()


def main() -> None:
    t_start = time.perf_counter()
    probe_thread = threading.Thread(target=probe, name="health-probe-sim", daemon=True)
    worker_thread = threading.Thread(target=worker, name="factor-lab-all-worker")

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
        "stall_count_gt_0.30s": len(stalls),
        "worst_stall_s": max((s["stall_s"] for s in stalls), default=0.0),
        "stalls_by_innermost_app_frame": by_frame.most_common(20),
    }
    print("=== SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    with open("stall_summary.json", "w") as f:
        json.dump({"summary": summary, "stalls": stalls}, f, indent=2)


if __name__ == "__main__":
    main()
