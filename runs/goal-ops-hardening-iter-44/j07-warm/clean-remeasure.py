"""ops-hardening iter-44 -- CLEAN, single-trigger re-measurement for TC-5/TC-6/TC-7 (separate from the
diagnostic drill above, which deliberately combined the ingest trigger with an additional historical
/api/backtest dispatch and is therefore NOT a clean single-warm reading -- this run avoids that confound:
ONE backfill trigger only, GET /api/health polled at 1Hz throughout, and exactly ONE concurrent cached
(is_latest) GET /api/backtest read fired once mid-run (TC-6) -- never a repeated manual probe.
"""
import json
import os
import sys
import time
import urllib.request

PORT = sys.argv[1]
OUT_DIR = sys.argv[2]
BACKFILL_DATE = sys.argv[3]
MAX_SECONDS = float(sys.argv[4]) if len(sys.argv) > 4 else 600.0

BCW_LATENCY_BUDGET_S = 2.0


def _get(path: str):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=15) as resp:
            body = json.loads(resp.read())
            return resp.status, time.perf_counter() - t0, body
    except Exception as exc:  # noqa: BLE001
        return 0, time.perf_counter() - t0, {"_error": str(exc)}


def _post(path: str, payload: dict):
    t0 = time.perf_counter()
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
            return resp.status, time.perf_counter() - t0, body
    except Exception as exc:  # noqa: BLE001
        return 0, time.perf_counter() - t0, {"_error": str(exc)}


log_lines = []


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {msg}"
    print(line, flush=True)
    log_lines.append(line)


status, lat, body = _post("/api/data/jobs", {"kind": "backfill", "start": BACKFILL_DATE, "end": BACKFILL_DATE})
log(f"POST /api/data/jobs (backfill {BACKFILL_DATE}, THE ONE clean trigger) -> status={status} latency={lat:.3f}s body={body}")
if status != 200 or "job_id" not in body:
    log("FATAL: trigger failed")
    sys.exit(1)
job_id = body["job_id"]

rows = []
t_start = time.time()
n_polls = n_non200 = n_over_budget = 0
concurrent_fired = False
max_latency = 0.0

while True:
    if time.time() - t_start >= MAX_SECONDS:
        log(f"backstop ({MAX_SECONDS}s) reached, ending clean observation window")
        break
    epoch = time.time()
    hstatus, hlat, hbody = _get("/api/health")
    n_polls += 1
    if hstatus != 200:
        n_non200 += 1
    else:
        max_latency = max(max_latency, hlat)
        if hlat > BCW_LATENCY_BUDGET_S:
            n_over_budget += 1
    jstatus, jlat, jbody = _get(f"/api/data/jobs/{job_id}")
    job_status = jbody.get("status") if isinstance(jbody, dict) else None

    if not concurrent_fired and (epoch - t_start) >= 5.0:
        cstatus, clat, cbody = _get("/api/backtest")
        concurrent_fired = True
        log(f"GET /api/backtest (concurrent cached is_latest read, TC-6, ONCE) -> status={cstatus} latency={clat:.3f}s")
        with open(os.path.join(OUT_DIR, "clean-concurrent-backtest-response.json"), "w") as fh:
            json.dump(cbody, fh, indent=2)

    rows.append([round(epoch - t_start, 3), hstatus, round(hlat, 4), job_status, jbody.get("snapshots_created"), jbody.get("aggregates_refreshed")])
    log(f"t={epoch-t_start:7.2f}s health={hstatus}({hlat*1000:.0f}ms) job={job_status} snapshots={jbody.get('snapshots_created')} agg={jbody.get('aggregates_refreshed')}")

    if job_status in ("ok", "partial", "failed"):
        log(f"--- job reached terminal status={job_status} at t={epoch-t_start:.2f}s ---")
        break
    time.sleep(1.0)

with open(os.path.join(OUT_DIR, "clean-remeasure.log"), "w") as fh:
    fh.write("\n".join(log_lines) + "\n")

summary = {
    "total_health_polls": n_polls,
    "non_200": n_non200,
    "over_2s_budget": n_over_budget,
    "over_2s_budget_pct": round(100 * n_over_budget / max(n_polls, 1), 1),
    "max_latency_s": round(max_latency, 3),
    "concurrent_backtest_fired": concurrent_fired,
    "final_job_status": job_status,
    "elapsed_s": round(time.time() - t_start, 2),
}
with open(os.path.join(OUT_DIR, "clean-remeasure-summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
log("SUMMARY: " + json.dumps(summary))
