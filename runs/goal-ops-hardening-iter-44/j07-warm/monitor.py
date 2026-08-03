"""ops-hardening iter-44 -- J-07 step 1 live diagnostic: 1 Hz GET /api/health poll run CONCURRENTLY with
the background forward-aggregate warm dispatched by a single backfill trigger (the SAME finalize-tail path
J-05 exercises -- app.engine.forward_testing.ensure_historical_forward_aggregates_dispatched), sampling
VmPeak/VmHWM from /proc/<pid>/status alongside each poll and tracking background_compute.active (J-09's
disclosure field) so completion/stall is read directly, never inferred.

NEW this iteration: when the target identity's horizons_done has not advanced for STALL_WINDOW_S past
started_at (bounded-window stall detection, reusing the existing accessor -- no new polling mechanism),
send `kill -USR1 <pid>` EXACTLY ONCE and record the wall-clock instant, so the resulting all-thread dump in
logs/backend.log can be correlated back to this exact moment. Keeps polling afterward (the diagnostic must
not itself kill the process) until the warm completes or MAX_SECONDS (safety backstop) elapses.

Usage: <venv python> monitor.py <pid> <port> <out_csv> <asof_key> <dataset_version> [max_seconds] [stall_window_s]
"""
import csv
import json
import os
import signal
import sys
import time
import urllib.request

PID = int(sys.argv[1])
PORT = sys.argv[2]
OUT_CSV = sys.argv[3]
ASOF_KEY = sys.argv[4]  # "AUTO" -> lock onto the first identity that appears in background_compute.active
DATASET_VERSION = sys.argv[5]  # "AUTO" likewise
MAX_SECONDS = float(sys.argv[6]) if len(sys.argv) > 6 else 1800.0
STALL_WINDOW_S = float(sys.argv[7]) if len(sys.argv) > 7 else 60.0
AUTO_LOCK = ASOF_KEY == "AUTO" or DATASET_VERSION == "AUTO"

STATUS_PATH = f"/proc/{PID}/status"
BCW_LATENCY_BUDGET_S = 2.0  # reports/perf-budgets.md OWNER AMENDMENT, section 2


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
n_over_budget = 0
warm_seen_active = False
final_outcome = None
backstop_fired = False
sigusr1_sent = False
sigusr1_sent_at = None
stall_first_seen_at = None
last_horizons_done = None

while True:
    if time.time() - t_start >= MAX_SECONDS:
        backstop_fired = True
        print(f"!!! SAFETY BACKSTOP ({MAX_SECONDS}s) FIRED -- the warm never showed as completed. ANOMALY.")
        break

    epoch = time.time()
    health_status, health_latency, health_body = _get("/api/health")
    if health_status != 200:
        n_non200 += 1
    if health_status == 200 and health_latency > BCW_LATENCY_BUDGET_S:
        n_over_budget += 1
    if last_poll_epoch is not None:
        gap = epoch - last_poll_epoch
        max_gap = max(max_gap, gap)
    last_poll_epoch = epoch

    vmpeak = _read_vm("VmPeak")
    vmhwm = _read_vm("VmHWM")

    bg = health_body.get("background_compute", {}) if isinstance(health_body, dict) else {}
    active = bg.get("active") or []
    if AUTO_LOCK and ASOF_KEY == "AUTO" and active:
        # lock onto the FIRST identity observed -- a single backfill trigger dispatches exactly one, so
        # the first (and only) entry seen is unambiguously the one this drill triggered.
        ASOF_KEY = active[0]["asof_key"]
        DATASET_VERSION = active[0]["dataset_version"]
        print(f"AUTO-LOCKED onto asof_key={ASOF_KEY} dataset_version={DATASET_VERSION}")
    is_target_active = any(
        a.get("asof_key") == ASOF_KEY and a.get("dataset_version") == DATASET_VERSION for a in active
    )
    if is_target_active:
        warm_seen_active = True
    horizons_done = next(
        (a.get("horizons_done") for a in active if a.get("asof_key") == ASOF_KEY), None
    )
    horizons_total = next(
        (a.get("horizons_total") for a in active if a.get("asof_key") == ASOF_KEY), None
    )
    started_at = next(
        (a.get("started_at") for a in active if a.get("asof_key") == ASOF_KEY), None
    )

    rows.append([
        round(epoch - t_start, 3), health_status, round(health_latency, 4), vmpeak, vmhwm,
        int(is_target_active), horizons_done, horizons_total, started_at,
    ])
    print(
        f"t={epoch - t_start:6.2f}s health={health_status} latency={health_latency*1000:.1f}ms "
        f"vmpeak={vmpeak} target_active={is_target_active} horizons={horizons_done}/{horizons_total} "
        f"started_at={started_at}"
    )

    # --- NEW (iter-44): bounded-window stall detection -> single kill -USR1 -> keep observing ---
    if is_target_active and not sigusr1_sent:
        if horizons_done != last_horizons_done:
            last_horizons_done = horizons_done
            stall_first_seen_at = epoch
        elif stall_first_seen_at is not None and (epoch - stall_first_seen_at) >= STALL_WINDOW_S:
            print(
                f"*** STALL DETECTED: horizons_done={horizons_done} unchanged for "
                f"{epoch - stall_first_seen_at:.1f}s (>= {STALL_WINDOW_S}s window) -- sending SIGUSR1 to pid {PID} ***"
            )
            os.kill(PID, signal.SIGUSR1)
            sigusr1_sent = True
            sigusr1_sent_at = epoch - t_start
            print(f"SIGUSR1_SENT_AT_ELAPSED_S={sigusr1_sent_at:.3f} WALL_CLOCK={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch))}")

    if warm_seen_active and not is_target_active:
        recent = bg.get("recent_outcomes") or []
        match = next(
            (r for r in recent if r.get("asof_key") == ASOF_KEY and r.get("dataset_version") == DATASET_VERSION),
            None,
        )
        final_outcome = match
        print(f"--- warm for {ASOF_KEY}/{DATASET_VERSION} no longer active; recent_outcomes match: {match} ---")
        break

    time.sleep(1.0)  # 1Hz per J-07 step 2's own acceptance wording

with open(OUT_CSV, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow([
        "elapsed_s", "health_http_status", "health_latency_s", "vmpeak_kb", "vmhwm_kb",
        "target_warm_active", "horizons_done", "horizons_total", "started_at",
    ])
    writer.writerows(rows)

print(
    f"TOTAL_POLLS={len(rows)} NON_200={n_non200} OVER_BCW_BUDGET={n_over_budget} MAX_GAP_S={max_gap:.3f} "
    f"WARM_SEEN_ACTIVE={warm_seen_active} BACKSTOP_FIRED={backstop_fired} SIGUSR1_SENT={sigusr1_sent} "
    f"SIGUSR1_SENT_AT_ELAPSED_S={sigusr1_sent_at}"
)
print("FINAL_OUTCOME_JSON=" + json.dumps(final_outcome))
