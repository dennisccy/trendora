"""ops-hardening iter-44 -- combined J-05/J-07 live drill (ONE single trigger: a real backfill of a
CONFIRMED-unsnapshotted historical trading day against the full deep-basis committed-seed DB).

Rationale (recorded here since it drove the drill's design): `_refresh_ingest_aggregates` (the ingest
finalize hook `_run_job` calls after a backfill's snapshot-creation stage) warms the LATEST stored run's
forward-aggregates SYNCHRONOUSLY, in the job's own worker thread, looping `cfg.walk_forward.horizons` with
NO per-horizon progress counter anywhere on `JobProgress` -- confirmed by direct read, there is no
`horizons_done`-shaped field on the job. `background_compute.active[].horizons_done` (`GET /api/health`'s
J-09 disclosure field) is populated ONLY by the REQUEST-triggered async historical dispatch
(`ensure_historical_forward_aggregates_dispatched`, called from `GET /api/backtest?as_of=<historical>`
when that identity's evidence is not `"ready"`) -- a SEPARATE caller of the SAME underlying
`forward_aggregates_ingest_cached` compute. Both callers share the identical hot path, so a stall in one
is evidence for the other, but only the request-triggered path is directly observable via the accessor the
phase spec names.

This drill therefore polls BOTH signals every 1s:
  (a) `GET /api/data/jobs/{job_id}` -- the backfill's OWN status/heartbeat (`last_progress_at`,
      `aggregates_refreshed`) -- the literal iter-43 reproduction.
  (b) `GET /api/health`'s `background_compute.active[].horizons_done` -- the request-triggered path,
      armed by firing ONE `GET /api/backtest?as_of=<near-latest historical date>` request the moment the
      backfill's own snapshot-creation stage confirms the dataset_version has bumped (a SINGLE additional
      trigger, never a repeated manual probe).

Stall detection (bounded window, no new polling mechanism beyond what's already disclosed): if the JOB's
own `last_progress_at` heartbeat has not advanced for STALL_WINDOW_S, OR the historical dispatch's
`horizons_done` has not advanced for STALL_WINDOW_S past its own `started_at`, send `kill -USR1 <pid>`
EXACTLY ONCE and record the instant. Keeps polling afterward (SIGUSR1 does not kill the process).
"""
import json
import os
import signal
import sys
import time
import urllib.request

PID = int(sys.argv[1])
PORT = sys.argv[2]
OUT_DIR = sys.argv[3]
BACKFILL_DATE = sys.argv[4]
HISTORICAL_TRIGGER_ASOF = sys.argv[5]
MAX_SECONDS = float(sys.argv[6]) if len(sys.argv) > 6 else 1800.0
STALL_WINDOW_S = float(sys.argv[7]) if len(sys.argv) > 7 else 60.0

STATUS_PATH = f"/proc/{PID}/status"
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
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=15) as resp:
            body = json.loads(resp.read())
            return resp.status, time.perf_counter() - t0, body
    except Exception as exc:  # noqa: BLE001
        return 0, time.perf_counter() - t0, {"_error": str(exc)}


def _post(path: str, payload: dict) -> tuple[int, float, dict]:
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


# --- Step 1: trigger the ONE backfill (J-05's defining case + the dataset_version bump for J-07's trigger) ---
status, lat, body = _post("/api/data/jobs", {"kind": "backfill", "start": BACKFILL_DATE, "end": BACKFILL_DATE})
log(f"POST /api/data/jobs (backfill {BACKFILL_DATE}) -> status={status} latency={lat:.3f}s body={body}")
with open(os.path.join(OUT_DIR, "backfill-trigger-response.json"), "w") as fh:
    json.dump(body, fh, indent=2)
if status != 200 or "job_id" not in body:
    log("FATAL: backfill trigger did not return a job_id -- aborting drill")
    sys.exit(1)
job_id = body["job_id"]

rows = []
t_start = time.time()
snapshot_confirmed = False
historical_trigger_fired = False
concurrent_backtest_fired = False
job_last_progress_at = None
job_progress_stall_first_seen = None
hist_last_horizons_done = None
hist_stall_first_seen = None
sigusr1_sent = False
sigusr1_sent_at = None
sigusr1_reason = None
backstop_fired = False
n_non200 = 0
n_over_budget = 0

while True:
    if time.time() - t_start >= MAX_SECONDS:
        backstop_fired = True
        log(f"!!! SAFETY BACKSTOP ({MAX_SECONDS}s) FIRED -- ending observation")
        break

    epoch = time.time()

    # (a) job status
    jstatus, jlat, jbody = _get(f"/api/data/jobs/{job_id}")
    job_status = jbody.get("status") if isinstance(jbody, dict) else None
    last_progress_at = jbody.get("last_progress_at") if isinstance(jbody, dict) else None
    aggregates_refreshed = jbody.get("aggregates_refreshed") if isinstance(jbody, dict) else None
    snapshots_created = jbody.get("snapshots_created") if isinstance(jbody, dict) else None
    dates_done = jbody.get("dates_done") if isinstance(jbody, dict) else None

    if not snapshot_confirmed and (snapshots_created or 0) >= 1:
        snapshot_confirmed = True
        log(f"SNAPSHOT CONFIRMED CREATED at t={epoch - t_start:.2f}s: snapshots_created={snapshots_created} dates_done={dates_done}")

    # (b) health + background_compute
    hstatus, hlat, hbody = _get("/api/health")
    if hstatus != 200:
        n_non200 += 1
    if hstatus == 200 and hlat > BCW_LATENCY_BUDGET_S:
        n_over_budget += 1
    vmpeak = _read_vm("VmPeak")
    vmhwm = _read_vm("VmHWM")
    bg = hbody.get("background_compute", {}) if isinstance(hbody, dict) else {}
    active = bg.get("active") or []
    hist_entry = next((a for a in active if a.get("asof_key") == HISTORICAL_TRIGGER_ASOF), None)
    horizons_done = hist_entry.get("horizons_done") if hist_entry else None
    horizons_total = hist_entry.get("horizons_total") if hist_entry else None

    # Step 2: once the snapshot is confirmed (dataset_version bumped), fire the ONE historical trigger.
    if snapshot_confirmed and not historical_trigger_fired:
        bstatus, blat, bbody = _get(f"/api/backtest?as_of={HISTORICAL_TRIGGER_ASOF}")
        historical_trigger_fired = True
        log(
            f"GET /api/backtest?as_of={HISTORICAL_TRIGGER_ASOF} (THE ONE historical trigger) -> "
            f"status={bstatus} latency={blat:.3f}s evidence_status={bbody.get('evidence_status') if isinstance(bbody, dict) else None}"
        )
        with open(os.path.join(OUT_DIR, "historical-trigger-response.json"), "w") as fh:
            json.dump(bbody, fh, indent=2)

    # Step 3 (TC-6): fire exactly ONE concurrent cached (is_latest) /api/backtest read, roughly mid-drill,
    # AFTER the historical trigger has fired (never a repeated probe).
    if historical_trigger_fired and not concurrent_backtest_fired and (epoch - t_start) >= 5.0:
        cstatus, clat, cbody = _get("/api/backtest")
        concurrent_backtest_fired = True
        log(
            f"GET /api/backtest (concurrent cached is_latest read, TC-6, fired ONCE) -> status={cstatus} "
            f"latency={clat:.3f}s is_latest={cbody.get('is_latest') if isinstance(cbody, dict) else None}"
        )
        with open(os.path.join(OUT_DIR, "concurrent-backtest-response.json"), "w") as fh:
            json.dump(cbody, fh, indent=2)

    rows.append([
        round(epoch - t_start, 3), job_status, last_progress_at, snapshots_created, dates_done,
        json.dumps(aggregates_refreshed), hstatus, round(hlat, 4), vmpeak, vmhwm,
        horizons_done, horizons_total,
    ])
    log(
        f"t={epoch - t_start:7.2f}s job={job_status} last_progress_at={last_progress_at} "
        f"snapshots_created={snapshots_created} agg_refreshed={aggregates_refreshed} "
        f"health={hstatus}({hlat*1000:.0f}ms) vmpeak={vmpeak} hist_horizons={horizons_done}/{horizons_total}"
    )

    # --- stall detection (a): job heartbeat not advancing ---
    if job_status == "running" and not sigusr1_sent:
        if last_progress_at != job_last_progress_at:
            job_last_progress_at = last_progress_at
            job_progress_stall_first_seen = epoch
        elif job_progress_stall_first_seen is not None and (epoch - job_progress_stall_first_seen) >= STALL_WINDOW_S:
            log(
                f"*** STALL DETECTED (signal a: job heartbeat): last_progress_at={last_progress_at} unchanged "
                f"for {epoch - job_progress_stall_first_seen:.1f}s -- sending SIGUSR1 to pid {PID} ***"
            )
            os.kill(PID, signal.SIGUSR1)
            sigusr1_sent = True
            sigusr1_sent_at = epoch - t_start
            sigusr1_reason = "job_heartbeat_stalled"

    # --- stall detection (b): historical dispatch horizons_done not advancing ---
    if hist_entry is not None and not sigusr1_sent:
        if horizons_done != hist_last_horizons_done:
            hist_last_horizons_done = horizons_done
            hist_stall_first_seen = epoch
        elif hist_stall_first_seen is not None and (epoch - hist_stall_first_seen) >= STALL_WINDOW_S:
            log(
                f"*** STALL DETECTED (signal b: background_compute horizons_done): {horizons_done} unchanged "
                f"for {epoch - hist_stall_first_seen:.1f}s -- sending SIGUSR1 to pid {PID} ***"
            )
            os.kill(PID, signal.SIGUSR1)
            sigusr1_sent = True
            sigusr1_sent_at = epoch - t_start
            sigusr1_reason = "background_compute_horizons_done_stalled"

    if job_status in ("ok", "partial", "failed"):
        log(f"--- backfill job reached terminal status={job_status} at t={epoch - t_start:.2f}s ---")
        # keep observing a bit longer only if the historical dispatch is still active
        if hist_entry is None:
            break

    time.sleep(1.0)

with open(os.path.join(OUT_DIR, "drill-samples.csv"), "w") as fh:
    fh.write(
        "elapsed_s,job_status,last_progress_at,snapshots_created,dates_done,aggregates_refreshed,"
        "health_status,health_latency_s,vmpeak_kb,vmhwm_kb,hist_horizons_done,hist_horizons_total\n"
    )
    for r in rows:
        fh.write(",".join(str(x) for x in r) + "\n")

with open(os.path.join(OUT_DIR, "drill.log"), "w") as fh:
    fh.write("\n".join(log_lines) + "\n")

summary = {
    "total_polls": len(rows),
    "non_200": n_non200,
    "over_bcw_budget": n_over_budget,
    "backstop_fired": backstop_fired,
    "snapshot_confirmed": snapshot_confirmed,
    "historical_trigger_fired": historical_trigger_fired,
    "concurrent_backtest_fired": concurrent_backtest_fired,
    "sigusr1_sent": sigusr1_sent,
    "sigusr1_sent_at_elapsed_s": sigusr1_sent_at,
    "sigusr1_reason": sigusr1_reason,
    "final_job_status": job_status,
    "final_aggregates_refreshed": aggregates_refreshed,
    "final_hist_horizons_done": horizons_done,
    "final_hist_horizons_total": horizons_total,
}
with open(os.path.join(OUT_DIR, "drill-summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
log("SUMMARY: " + json.dumps(summary))
