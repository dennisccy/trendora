"""ops-hardening iter-39 (J-07 step 4, TC-2) -- 1 Hz GET /api/health poll run CONCURRENTLY with the
induced-pressure job, sampling VmPeak/VmHWM from /proc/<pid>/status alongside each poll, until the job
polled via GET /api/data/jobs/{job_id} reaches a terminal status.

Closes audit finding B2 (iter-38): that iteration's own health-poll script (j07-warm/monitor.py) bounded
its main loop with `while time.time() - t_start < MAX_SECONDS` (default 300.0 s) -- for a 338 s job, the
loop stopped polling at t~=299s, one single poll landed AFTER the job had already reached `ok`, leaving a
~37 s UNPOLLED window (~31 s of it mid-tail) that the published "2.355 s max gap" figure never disclosed.
This script's main loop is bounded ONLY by the job reaching a terminal status -- never a wall-clock window
shorter than a real run. `MAX_SECONDS` still exists as a generous SAFETY BACKSTOP (default 1800 s = 30 min,
an order of magnitude past any observed drill duration in this session's history) so a genuine wedge/deadlock
does not hang this script forever -- hitting it is flagged loudly as an anomaly, not treated as a normal
"coverage window" the way iter-38's 300 s bound was.

Usage: <venv python> monitor.py <pid> <port> <job_id> <out_csv> [max_seconds_safety_backstop]
Prints progress + a final summary (gap analysis, VmPeak, whether the safety backstop fired) to stdout.
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
# Safety backstop only -- NOT a coverage window (see module docstring). 1800s is generous; a real drill in
# this session's history has never exceeded ~340s.
MAX_SECONDS_SAFETY_BACKSTOP = float(sys.argv[5]) if len(sys.argv) > 5 else 1800.0

STATUS_PATH = f"/proc/{PID}/status"


def _read_vm(field: str) -> str:
    try:
        with open(STATUS_PATH) as fh:
            for line in fh:
                if line.startswith(field + ":"):
                    return line.split()[1]
    except FileNotFoundError:
        return "PROCESS_GONE"
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
backstop_fired = False

while True:
    if time.time() - t_start >= MAX_SECONDS_SAFETY_BACKSTOP:
        backstop_fired = True
        print(f"!!! SAFETY BACKSTOP ({MAX_SECONDS_SAFETY_BACKSTOP}s) FIRED -- job never reached a terminal "
              f"status. This is an ANOMALY (possible wedge/deadlock), not expected drill behavior.")
        break

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
    time.sleep(1.0)  # 1Hz per TC-2/TC-4

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["elapsed_s", "health_http_status", "health_latency_s", "vmpeak_kb", "vmhwm_kb", "job_status"])
    writer.writerows(rows)

print(f"TOTAL_POLLS={len(rows)} NON_200={n_non200} MAX_GAP_S={max_gap:.3f} SAFETY_BACKSTOP_FIRED={backstop_fired}")
if job_final is not None:
    print("FINAL_JOB_STATUS_JSON=" + json.dumps(job_final))
else:
    print("FINAL_JOB_STATUS_JSON=null  # safety backstop fired before a terminal status (see above)")
