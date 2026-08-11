"""Iter-65 (J-07) — concurrent GIL-stall profile: `compute_factor_lab_all` vs a REAL `/api/health` call.

The solo profile (stall_profile.py) found ZERO stalls > 0.30s inside `compute_factor_lab_all` run alone
against the real committed DB -- iter-52's sort/GC fixes hold. But the live drills (iter-63/64) still
show 53-59 of ~930-983 `GET /api/health` polls breaching the 2.0s ceiling, almost all attributed to the
`factor_lab_all_warm` time window. The remaining hold must therefore only manifest under the SAME
concurrent condition the live drill has and the solo profile does not: a second thread actually issuing
the real `/api/health` route's own DB queries WHILE `compute_factor_lab_all` runs in the worker thread --
this script reproduces exactly that, in-process, against the real committed DB, with no ingest job
needed.

Method: worker thread runs `compute_factor_lab_all(session, cfg, as_of=None)` once (as_of=None, the SAME
all-history call `factor_lab_all_warm` makes). A second thread calls the ACTUAL `app.api.health.health()`
route function (not a re-implementation) once per second (own dedicated Session/connection, mirroring a
real request), timing each call. Any call exceeding HEALTH_CEILING_S is logged with the worker thread's
stack sampled the instant the slow call returns (iter-52's "captured at the instant each stall resolved"
technique, applied to the REAL blocking symptom instead of an idle probe)."""
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
from app.engine.research import compute_factor_lab_all  # noqa: E402

HEALTH_CEILING_S = 2.0  # the J-07 acceptance ceiling during a bounded background-compute window
POLL_INTERVAL_S = 1.0

health_polls: list[dict] = []
worker_result: dict = {}
worker_ident: list[int] = [0]
worker_done = threading.Event()


def _innermost_app_frame(stack_lines: list[str]) -> str:
    for line in reversed(stack_lines):
        if "research.py" in line or "data_manager.py" in line or "forward_testing.py" in line:
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
            entry["worker_stack"] = [ln.strip() for ln in stack_lines[-6:]]
            print(json.dumps(entry), flush=True)
        health_polls.append(entry)
        # keep ~1 Hz cadence regardless of how long the call itself took
        remaining = POLL_INTERVAL_S - (time.perf_counter() - t0)
        if remaining > 0:
            time.sleep(remaining)


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
    finally:
        session.close()
        worker_done.set()


def main() -> None:
    t_start = time.perf_counter()
    health_thread = threading.Thread(target=health_sim, name="health-sim", daemon=True)
    worker_thread = threading.Thread(target=worker, name="factor-lab-all-worker")

    worker_thread.start()
    time.sleep(0.05)
    health_thread.start()
    worker_thread.join()
    # let the health thread take one more full-cadence poll past completion (mirrors the live drill's
    # own tail window), then stop it.
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
        "health_polls_total": len(health_polls),
        "health_polls_breach_gt_2s": len(breaches),
        "health_polls_error": len(errors),
        "worst_health_elapsed_s": max((p["elapsed_s"] for p in health_polls), default=0.0),
        "breaches_by_worker_innermost_app_frame": by_frame.most_common(20),
    }
    print("=== SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    with open("stall_profile_concurrent_summary.json", "w") as f:
        json.dump({"summary": summary, "health_polls": health_polls}, f, indent=2)


if __name__ == "__main__":
    main()
