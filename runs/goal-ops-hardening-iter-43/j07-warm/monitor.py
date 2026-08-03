"""ops-hardening iter-43 (J-07 steps 1-3 live re-verification against memory_cap_mb: 8192, post
_BarCache.prefill revert) -- 1 Hz GET /api/health poll run CONCURRENTLY with the background
forward-aggregate warm GET /api/backtest?as_of=<uncached> dispatches (app.engine.forward_testing
.ensure_historical_forward_aggregates_dispatched), sampling VmPeak/VmHWM from /proc/<pid>/status
alongside each poll and tracking background_compute.active/recent_outcomes (J-09's own disclosure
field) so completion is read directly, never inferred. Mirrors iter-32/34/37/38's own methodology
(same 1Hz cadence, same /proc sampling) adapted to poll background_compute instead of a job_id,
since THIS warm is dispatched by GET /api/backtest's daemon thread, not a Data Manager job.

Usage: <venv python> monitor.py <pid> <port> <out_csv> <asof_key> <dataset_version> [max_seconds]
Runs until background_compute.active no longer lists (asof_key, dataset_version), or MAX_SECONDS
elapses (safety backstop, not a coverage window). Prints progress + a final summary.
"""
import csv
import json
import sys
import time
import urllib.request

PID = sys.argv[1]
PORT = sys.argv[2]
OUT_CSV = sys.argv[3]
ASOF_KEY = sys.argv[4]
DATASET_VERSION = sys.argv[5]
MAX_SECONDS = float(sys.argv[6]) if len(sys.argv) > 6 else 600.0

STATUS_PATH = f"/proc/{PID}/status"
# The rescoped bounded-compute-window budget (reports/perf-budgets.md OWNER AMENDMENT, section 2):
# steady state <=0.1s unchanged; during an in-flight ingest/warm, <=2s, 100% HTTP 200.
BCW_LATENCY_BUDGET_S = 2.0


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

    rows.append([
        round(epoch - t_start, 3), health_status, round(health_latency, 4), vmpeak, vmhwm,
        int(is_target_active), horizons_done, horizons_total,
    ])
    print(
        f"t={epoch - t_start:6.2f}s health={health_status} latency={health_latency*1000:.1f}ms "
        f"vmpeak={vmpeak} target_active={is_target_active} horizons={horizons_done}/{horizons_total}"
    )

    if warm_seen_active and not is_target_active:
        # the target warm was seen active at least once and has now disappeared from `active` -- read
        # `recent_outcomes` for its terminal reason (completed / aborted), never inferred.
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
        "target_warm_active", "horizons_done", "horizons_total",
    ])
    writer.writerows(rows)

print(
    f"TOTAL_POLLS={len(rows)} NON_200={n_non200} OVER_BCW_BUDGET={n_over_budget} MAX_GAP_S={max_gap:.3f} "
    f"WARM_SEEN_ACTIVE={warm_seen_active} BACKSTOP_FIRED={backstop_fired}"
)
print("FINAL_OUTCOME_JSON=" + json.dumps(final_outcome))
