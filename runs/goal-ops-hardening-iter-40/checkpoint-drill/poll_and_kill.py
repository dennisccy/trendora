"""ops-hardening iter-40 (iter-39/w, AG-3) -- TC-4 live checkpoint-honesty drill.

Polls `GET /api/data/jobs/{job_id}` at high frequency (0.15 s) to INDEPENDENTLY track the job's true
in-memory `dates_done` (a log line per poll, so M is never inferred after the fact). The instant
`dates_done` first reaches `--kill-at`, this script itself immediately sends `kill -9` to the backend
PID (in the SAME process, no round-trip back to an orchestrating shell) so the gap between the last
observed M and the actual kill instant is as small as this script's own poll interval, not a human
reaction time.

Usage: <venv python> poll_and_kill.py <port> <job_id> <backend_pid> <kill_at_dates_done> <out_csv>
Prints a final summary line (M, timestamp, poll count) to stdout.
"""
import csv
import json
import os
import signal
import sys
import time
import urllib.request

PORT = sys.argv[1]
JOB_ID = sys.argv[2]
BACKEND_PID = int(sys.argv[3])
KILL_AT = int(sys.argv[4])
OUT_CSV = sys.argv[5]

POLL_INTERVAL_S = 0.15


def _get_job() -> dict:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/data/jobs/{JOB_ID}", timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)}


rows = []
t_start = time.time()
last_dates_done = None

while True:
    epoch = time.time()
    body = _get_job()
    dates_done = body.get("dates_done")
    status = body.get("status")
    rows.append([round(epoch - t_start, 4), dates_done, status])
    if dates_done is not None:
        last_dates_done = dates_done
    print(f"t={epoch - t_start:7.3f}s dates_done={dates_done} status={status}")

    if status in ("ok", "partial", "failed"):
        print(f"JOB_FINISHED_BEFORE_KILL_THRESHOLD dates_done={dates_done}")
        break

    if dates_done is not None and dates_done >= KILL_AT:
        kill_epoch = time.time()
        os.kill(BACKEND_PID, signal.SIGKILL)
        rows.append([round(kill_epoch - t_start, 4), dates_done, "KILLED"])
        print(f"KILLED_AT_M={dates_done} t={kill_epoch - t_start:.3f}s pid={BACKEND_PID}")
        break

    time.sleep(POLL_INTERVAL_S)

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["elapsed_s", "dates_done", "status"])
    writer.writerows(rows)

print(f"TOTAL_POLLS={len(rows)} LAST_DATES_DONE={last_dates_done}")
