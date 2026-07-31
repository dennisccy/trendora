"""ops-hardening iter-40 (iter-39/w, AG-3) -- TC-4 live checkpoint-honesty drill, combined trigger+poll.

Combines the job-trigger POST and the high-frequency poll-and-kill loop into ONE script (no round-trip
delay between an orchestrating shell issuing the trigger and a SEPARATE process starting to poll --
iter-40's own first attempt at this drill lost the mid-flight kill window entirely that way: the 20-date
job finished between the trigger call and the poller's first poll). Polls `GET /api/data/jobs/{job_id}`
every 0.1 s from the FIRST instant after the trigger response returns; the instant `dates_done` first
reaches `--kill-at`, sends `kill -9` to the backend PID immediately, in the same process.

Usage: <venv python> trigger_and_poll_and_kill.py <port> <start> <end> <backend_pid> <kill_at_dates_done> <out_csv>
Prints the job_id, then a poll log, then a final summary line to stdout.
"""
import csv
import json
import os
import signal
import sys
import time
import urllib.request

PORT = sys.argv[1]
START = sys.argv[2]
END = sys.argv[3]
BACKEND_PID = int(sys.argv[4])
KILL_AT = int(sys.argv[5])
OUT_CSV = sys.argv[6]

POLL_INTERVAL_S = 0.1


def _post_job() -> dict:
    payload = json.dumps({"kind": "backfill", "start": START, "end": END, "source": "yahoo"}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/api/data/jobs", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _get_job(job_id: str) -> dict:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/data/jobs/{job_id}", timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)}


trigger_epoch = time.time()
trigger_resp = _post_job()
job_id = trigger_resp["job_id"]
print(f"TRIGGERED job_id={job_id} at_epoch={trigger_epoch}")
print(json.dumps(trigger_resp))

rows = []
t_start = time.time()
last_dates_done = None

while True:
    epoch = time.time()
    body = _get_job(job_id)
    dates_done = body.get("dates_done")
    status = body.get("status")
    rows.append([round(epoch - t_start, 4), dates_done, status])
    print(f"t={epoch - t_start:7.3f}s dates_done={dates_done} status={status}")

    if dates_done is not None:
        last_dates_done = dates_done

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

print(f"JOB_ID={job_id} TOTAL_POLLS={len(rows)} LAST_DATES_DONE={last_dates_done}")
