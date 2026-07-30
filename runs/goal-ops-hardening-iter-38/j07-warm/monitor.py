"""ops-hardening iter-38 (J-07 steps 1-2, live full-deep-basis re-trigger) -- 1Hz GET /api/health poll run
CONCURRENTLY with the ingest-finalize forward-aggregate warm, sampling VmPeak/VmHWM from /proc/<pid>/status
alongside each poll. Unlike iter-37's own monitor (which polled GET /api/backtest and read
background_compute.active), this drill's warm is triggered by a REAL backfill's ingest-finalize hook (not
GET /api/backtest's daemon-thread dispatch), so THIS script instead polls the backfill JOB's own status
endpoint to know when the finalize tail has completed, while independently polling /api/health once per
second for the whole duration -- the exact TC-4 measurement.

Usage: <venv python> monitor.py <pid> <port> <job_id> <out_csv> [max_seconds]
Prints progress + a final summary (gap analysis, VmPeak) to stdout.
"""
import csv
import json
import sys
import time
import urllib.request

PID = sys.argv[1]
PORT = sys.argv[2]
JOB_ID = sys.argv[3]
OUT_CSV = sys.argv[4]
MAX_SECONDS = float(sys.argv[5]) if len(sys.argv) > 5 else 300.0

STATUS_PATH = f"/proc/{PID}/status"


def _read_vm(field: str) -> str:
    with open(STATUS_PATH) as fh:
        for line in fh:
            if line.startswith(field + ":"):
                return line.split()[1]
    return ""


def _get(path: str) -> tuple[int, float, dict]:
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10) as resp:
            body = json.loads(resp.read())
            return resp.status, time.perf_counter() - t0, body
    except Exception as exc:  # noqa: BLE001 -- record the miss, keep polling
        return 0, time.perf_counter() - t0, {"_error": str(exc)}


rows = []
t_start = time.time()
last_poll_epoch = None
max_gap = 0.0
n_non200 = 0
job_final = None

while time.time() - t_start < MAX_SECONDS:
    epoch = time.time()
    health_status, health_latency, health_body = _get("/api/health")
    if health_status != 200:
        n_non200 += 1
    if last_poll_epoch is not None:
        gap = epoch - last_poll_epoch
        max_gap = max(max_gap, gap)
    last_poll_epoch = epoch

    vmpeak = _read_vm("VmPeak")
    vmhwm = _read_vm("VmHWM")

    job_status_code, _, job_body = _get(f"/api/data/jobs/{JOB_ID}")
    job_status = job_body.get("status", "") if job_status_code == 200 else f"poll_error:{job_status_code}"

    rows.append([round(epoch - t_start, 3), health_status, round(health_latency, 4), vmpeak, vmhwm, job_status])
    print(
        f"t={epoch - t_start:6.2f}s health={health_status} latency={health_latency*1000:.1f}ms "
        f"vmpeak={vmpeak} job_status={job_status}"
    )
    if job_status in ("ok", "partial", "failed"):
        job_final = job_body
        break
    time.sleep(1.0)  # 1Hz per TC-4

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["elapsed_s", "health_http_status", "health_latency_s", "vmpeak_kb", "vmhwm_kb", "job_status"])
    writer.writerows(rows)

print(f"TOTAL_POLLS={len(rows)} NON_200={n_non200} MAX_GAP_S={max_gap:.3f}")
if job_final is not None:
    print("FINAL_JOB_STATUS_JSON=" + json.dumps(job_final))
else:
    print("FINAL_JOB_STATUS_JSON=null  # timed out before a terminal status")
