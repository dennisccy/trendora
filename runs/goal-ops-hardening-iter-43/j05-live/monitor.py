"""ops-hardening iter-41 (C8, audit finding B2) -- 1 Hz GET /api/health poll run CONCURRENTLY with the
induced-pressure job, sampling VmPeak/VmHWM from /proc/<pid>/status alongside each poll, until the job
polled via GET /api/data/jobs/{job_id} reaches a terminal status -- AND THEN KEEPS POLLING at the same
1 Hz interval for a fixed POST-TERMINAL window before stopping.

Extends iter-40's `wedge-drill/monitor.py` (copied verbatim from iter-39's `mem-drill/monitor.py`, itself
already closing iter-38's audit finding B2 -- a DIFFERENT B2, about the overall drill duration bound). THIS
iteration closes iter-40's OWN audit finding B2: "the 'wedge did not recur' claim is strongly evidenced
DURING the job and thinly evidenced AFTER it -- which is the window the previous wedge actually used."
iter-39's trial-3 wedge appeared "shortly after the job's own DB row was written ok" (`reports/perf-
budgets.md:4996`) -- iter-40's monitor.py broke its poll loop the INSTANT `job_status` first read a
terminal value, so its 28 clean polls all landed BEFORE that window, and the only post-terminal evidence
was a single manual follow-up probe. This script's loop now continues polling at the SAME 1 Hz interval
for `POST_TERMINAL_WINDOW_S` seconds PAST the first terminal `job_status` reading, recording every single
one of those additional polls in the same CSV (TC-7: "every additional poll's HTTP status/latency recorded
in the drill CSV") -- never a bare single manual follow-up.

`MAX_SECONDS_SAFETY_BACKSTOP` still exists as a generous SAFETY BACKSTOP (default 1800 s = 30 min, an
order of magnitude past any observed drill duration in this session's history) bounding BOTH phases
combined, so a genuine wedge/deadlock (in either the pre- or post-terminal window) does not hang this
script forever -- hitting it is flagged loudly as an anomaly.

Usage: <venv python> monitor.py <pid> <port> <job_id> <out_csv> [max_seconds_safety_backstop] [post_terminal_window_s]
Prints progress + a final summary (gap analysis, VmPeak, post-terminal poll count, whether the safety
backstop fired) to stdout.
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
# ops-hardening iter-41 (C8, audit B2): how long to keep polling PAST the first terminal `job_status`
# reading, at the same 1 Hz interval. 60s is well past iter-39's own trial-3 timing ("shortly after" the
# terminal write) with generous margin, while staying a small fraction of the 1800s safety backstop.
POST_TERMINAL_WINDOW_S = float(sys.argv[6]) if len(sys.argv) > 6 else 60.0

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
terminal_first_seen_epoch = None  # ops-hardening iter-41 (C8): set once, on the FIRST terminal reading
n_post_terminal_polls = 0

while True:
    if time.time() - t_start >= MAX_SECONDS_SAFETY_BACKSTOP:
        backstop_fired = True
        print(f"!!! SAFETY BACKSTOP ({MAX_SECONDS_SAFETY_BACKSTOP}s) FIRED -- job never reached a terminal "
              f"status, or the post-terminal window never completed. This is an ANOMALY (possible "
              f"wedge/deadlock), not expected drill behavior.")
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

    phase = "post_terminal" if terminal_first_seen_epoch is not None else "pre_terminal"
    rows.append([round(epoch - t_start, 3), health_status, round(health_latency, 4), vmpeak, vmhwm,
                 job_status, phase])
    print(
        f"t={epoch - t_start:6.2f}s health={health_status} latency={health_latency*1000:.1f}ms "
        f"vmpeak={vmpeak} job_status={job_status} phase={phase}"
    )

    if job_status in ("ok", "partial", "failed"):
        if terminal_first_seen_epoch is None:
            # ops-hardening iter-41 (C8): the OLD behavior was `break` right here. Instead, remember the
            # terminal reading (job_final is the DB-row snapshot at first terminal detection -- unchanged
            # contract for callers reading FINAL_JOB_STATUS_JSON) and keep polling for the post-terminal
            # window -- iter-39's own wedge appeared in exactly the window this used to stop covering.
            job_final = job_body
            terminal_first_seen_epoch = epoch
            print(f"--- job reached terminal status '{job_status}' at t={epoch - t_start:.2f}s -- "
                  f"continuing to poll for {POST_TERMINAL_WINDOW_S}s PAST this point (audit B2: iter-39's "
                  f"wedge appeared shortly after the terminal DB write) ---")
        else:
            n_post_terminal_polls += 1

    if terminal_first_seen_epoch is not None and (epoch - terminal_first_seen_epoch) >= POST_TERMINAL_WINDOW_S:
        print(f"--- post-terminal window ({POST_TERMINAL_WINDOW_S}s) elapsed with {n_post_terminal_polls} "
              f"additional poll(s) recorded -- stopping ---")
        break

    time.sleep(1.0)  # 1Hz per TC-2/TC-4 (iter-39), unchanged by the post-terminal extension

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["elapsed_s", "health_http_status", "health_latency_s", "vmpeak_kb", "vmhwm_kb",
                      "job_status", "phase"])
    writer.writerows(rows)

print(f"TOTAL_POLLS={len(rows)} NON_200={n_non200} MAX_GAP_S={max_gap:.3f} "
      f"POST_TERMINAL_POLLS={n_post_terminal_polls} SAFETY_BACKSTOP_FIRED={backstop_fired}")
if job_final is not None:
    print("FINAL_JOB_STATUS_JSON=" + json.dumps(job_final))
else:
    print("FINAL_JOB_STATUS_JSON=null  # safety backstop fired before a terminal status (see above)")
