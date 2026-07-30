"""ops-hardening iter-38 (J-07 closure, TC-1/TC-2) -- continuous VmPeak/VmHWM sampler.

Unlike iter-34/37's monitor scripts (which only sampled inside the per-item aggregate-warm sub-loops),
this one samples from BEFORE the backfill job is even submitted through AFTER it reaches a terminal status
-- covering the WHOLE finalize tail (coverage + membership_timeline + market_phase + forward_aggregates +
research_hot_keys + index_series + drawdown_expectations), not just one sub-loop. Runs until the job
polled via GET /api/data/jobs/{job_id} reaches a terminal status (ok/partial/failed) or a bounded max
duration elapses. Writes a CSV of every sample.

Usage: <venv python> monitor.py <pid> <port> <job_id> <out_csv> [max_seconds] [interval_seconds]
Prints the final job status JSON and a summary line to stdout.
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
MAX_SECONDS = float(sys.argv[5]) if len(sys.argv) > 5 else 240.0
INTERVAL_SECONDS = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5

STATUS_PATH = f"/proc/{PID}/status"


def _read_vm(field: str) -> str:
    with open(STATUS_PATH) as fh:
        for line in fh:
            if line.startswith(field + ":"):
                return line.split()[1]
    return ""


def _job_status() -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/data/jobs/{JOB_ID}", timeout=10) as resp:
        return json.loads(resp.read())


rows = []
t0 = time.time()
final = None
while time.time() - t0 < MAX_SECONDS:
    epoch = time.time()
    vmpeak = _read_vm("VmPeak")
    vmhwm = _read_vm("VmHWM")
    vmrss = _read_vm("VmRSS")
    try:
        job = _job_status()
        status = job.get("status", "")
    except Exception as exc:  # noqa: BLE001 -- keep sampling even through a transient poll miss
        status = f"poll_error:{exc}"
        job = {}
    rows.append([round(epoch - t0, 3), vmpeak, vmhwm, vmrss, status])
    print(f"t={epoch - t0:6.2f}s vmpeak={vmpeak} vmhwm={vmhwm} vmrss={vmrss} status={status}")
    if status in ("ok", "partial", "failed"):
        final = job
        break
    time.sleep(INTERVAL_SECONDS)

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["elapsed_s", "vmpeak_kb", "vmhwm_kb", "vmrss_kb", "job_status"])
    writer.writerows(rows)

print(f"TOTAL_SAMPLES={len(rows)}")
if final is not None:
    print("FINAL_JOB_STATUS_JSON=" + json.dumps(final))
else:
    print("FINAL_JOB_STATUS_JSON=null  # timed out before a terminal status")
