"""ops-hardening iter-59 combined drill: TC-3/TC-4/TC-5 (Regime-Lab bound under a concurrent
forward-aggregate warm) + J-05 step 3 / TC-1/TC-2 (kill -9, restart, cold /data + /scanner-runs +
market-phase serve from storage).

Phase 1 (mirrors iter-53/54/55's `run_drill_concurrent.py`, target read swapped to Regime Lab):
  - launch backend via scripts/start-backend.sh (AG-10 caps live)
  - dedicated 1 Hz health poller for the whole drill
  - pick an unsnapshotted trading day from the instance's own GET /api/data/availability, EXCLUDING the
    J-05.json golden precondition date (never consume another journey's reserved fixture -- iter-55 lesson)
  - start a real backfill job (offline/seed only -- AG-9)
  - concurrent GET /api/research/regime-lab?view=pooled load for the whole finalize tail
  - poll the job to terminal; capture VmPeak; hold 40s past completion

Phase 2 (J-05 step 3 / TC-1/TC-2, executed by the developer per the iter-58 evaluator's explicit
assignment -- browser-QA may not restart the app):
  - kill -9 the SAME backend process (no clean shutdown) right after Phase 1's backfill completed
  - restart via scripts/start-backend.sh (fresh boot, host-guard caps unchanged)
  - time first GET /api/health 200 (J-04 <=5s budget)
  - watermark scanner_results/forward_returns max ids, then time a cold GET /api/data (<=3000ms committed
    /data budget), then load GET /api/runs and GET /api/market-phase for the just-restarted process,
    watermark again -- confirms no new rows were created by the page loads themselves

Usage: run_drill.py <out_dir>
"""
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.request

REPO = "/home/dennis-chan/Git/trendora"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
PY = f"{REPO}/apps/backend/.venv/bin/python"
DB_PATH = f"{REPO}/apps/backend/data/trendora.db"
GOLDEN_DATE = "2010-11-05"  # J-05.json's reserved precondition date -- never consumed by this drill
BACKEND_LOG = f"{REPO}/logs/backend.log"


def api(port, path, method="GET", body=None, timeout=120):
    url = f"http://127.0.0.1:{port}/api{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(OUT, "drill.log"), "a") as fh:
        fh.write(line + "\n")


def db_scalar(sql):
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


def backend_pid(port):
    out = subprocess.run(["pgrep", "-f", f"uvicorn main:app.*--port {port}"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def launch_backend():
    proc = subprocess.Popen(["bash", f"{REPO}/scripts/start-backend.sh"], cwd=REPO,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    log(f"start-backend.sh launched (launcher pid={proc.pid})")
    return proc


def wait_for_health(port, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            api(port, "/health", timeout=10)
            return time.time() - t0
        except Exception:
            time.sleep(0.2)
    log("FATAL: backend never became reachable")
    sys.exit(2)


offset = int(__import__("hashlib").sha1(REPO.encode()).hexdigest()[:4], 16) % 1000
PORT = int(os.environ.get("CHAIN_BACKEND_PORT", 8000 + offset))
log(f"port={PORT}")

# ---- TC-8/AG-9 pre-lane watermark: every data_provider_runs row this drill creates must read
# provider='seed' (offline committed-seed only -- never a live fetch). Recorded BEFORE either phase.
wm_dpr_before = db_scalar("select coalesce(max(id), 0) from data_provider_runs")
log(f"TC-8/AG-9 pre-lane watermark: data_provider_runs.id={wm_dpr_before}")

# =================================================================================================
# PHASE 1 -- Regime-Lab bound under a concurrent forward-aggregate warm (TC-3/TC-4/TC-5)
# =================================================================================================
backend = launch_backend()
boot_s_1 = wait_for_health(PORT)
BPID_1 = backend_pid(PORT)
log(f"phase 1: backend serving, uvicorn pid={BPID_1}, boot took {boot_s_1:.2f}s")

health_csv = os.path.join(OUT, "tc5-health-poll.csv")
poller = subprocess.Popen(
    [PY, os.path.join(HERE, "poll_health.py"),
     f"http://127.0.0.1:{PORT}/api/health", health_csv, "2400"],
    start_new_session=True)
log(f"health poller started (pid={poller.pid}) -> {health_csv}")
time.sleep(5)

av = api(PORT, "/data/availability")
all_dates = sorted(c["date"] for c in av.get("cells", []))
free = [c["date"] for c in av.get("cells", []) if not c.get("snapshot_exists")]
cutoff = all_dates[-90] if len(all_dates) > 90 else all_dates[0]
eligible = sorted(d for d in free if d < cutoff and d != GOLDEN_DATE)
if not eligible:
    log("FATAL: no eligible unsnapshotted trading day (excluding the golden date)")
    sys.exit(3)
target = eligible[-1]
log(f"target date chosen from /api/data/availability: {target} "
    f"({len(eligible)} eligible, golden {GOLDEN_DATE} excluded)")

job = api(PORT, "/data/jobs", "POST", {"kind": "backfill", "start": target, "end": target})
JOB = job["job_id"]
job_t0 = time.time()
job_t0_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(job_t0))
log(f"job started id={JOB} kind={job['kind']} source={job.get('source')!r} range={target}..{target} "
    f"at {job_t0_iso}")

load_csv = os.path.join(OUT, "tc3-regime-lab-poll.csv")
load = subprocess.Popen(
    [PY, os.path.join(HERE, "load_regime_lab.py"),
     f"http://127.0.0.1:{PORT}", load_csv, "2400"],
    stderr=open(os.path.join(OUT, "tc3-regime-lab-poll.err"), "w"),
    start_new_session=True)
log(f"CONCURRENT regime-lab load started (pid={load.pid}) -> {load_csv}")

terminal = {"ok", "partial", "failed", "resumable", "completed", "error", "interrupted", "cancelled"}
last_msg = None
status = None
while time.time() - job_t0 < 2400:
    try:
        st = api(PORT, f"/data/jobs/{JOB}", timeout=30)
    except Exception as exc:
        log(f"job poll error (non-fatal): {exc}")
        time.sleep(5)
        continue
    status = st.get("status")
    msg = f"{status} | {st.get('message')} | stage={st.get('stage')}"
    if msg != last_msg:
        log(f"t+{time.time()-job_t0:7.1f}s  {msg}")
        last_msg = msg
    if status in terminal:
        break
    time.sleep(2)
job_secs = time.time() - job_t0
job_finished_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
log(f"job finished status={status} after {job_secs:.2f}s")

job_record = api(PORT, f"/data/jobs/{JOB}", timeout=60)
with open(os.path.join(OUT, "job-record.json"), "w") as fh:
    json.dump(job_record, fh, indent=2)

vm = {}
try:
    with open(f"/proc/{BPID_1}/status") as fh:
        for line in fh:
            for k in ("VmPeak", "VmHWM", "VmRSS", "VmSize"):
                if line.startswith(k + ":"):
                    vm[k] = line.split()[1] + " kB"
except Exception as exc:
    log(f"VmPeak read failed: {exc}")
log(f"memory (phase 1, right after job terminal): {vm}")

log("holding 40s past completion for the post-completion health tail")
time.sleep(40)

load.terminate()
try:
    load.wait(timeout=20)
except Exception:
    load.kill()
log("concurrent regime-lab load stopped")

poller.terminate()
try:
    poller.wait(timeout=10)
except Exception:
    poller.kill()
log("health poller (phase 1) stopped")

# re-read VmPeak one more time (monotonic non-decreasing since process start) after the 40s tail, in case
# the tail itself touched a new peak.
vm2 = dict(vm)
try:
    with open(f"/proc/{BPID_1}/status") as fh:
        for line in fh:
            for k in ("VmPeak", "VmHWM", "VmRSS", "VmSize"):
                if line.startswith(k + ":"):
                    vm2[k] = line.split()[1] + " kB"
except Exception as exc:
    log(f"VmPeak re-read failed: {exc}")
log(f"memory (phase 1, final, post-tail): {vm2}")

# ---- extract this job's OWN ingest heavy-warm OPEN/CLOSED markers from logs/backend.log --------
open_ts = closed_ts = None
try:
    with open(BACKEND_LOG) as fh:
        for line in fh:
            if f"ingest heavy-warm window OPEN: job={JOB}" in line:
                m = re.match(r"^\S+\s+(\S+)", line)
                open_ts = line
            if f"ingest heavy-warm window CLOSED: job={JOB}" in line:
                closed_ts = line
except Exception as exc:
    log(f"backend.log marker read failed: {exc}")
log(f"OPEN marker line: {open_ts!r}")
log(f"CLOSED marker line: {closed_ts!r}")

phase1_summary = {
    "job_id": JOB, "target": target, "status": status, "job_seconds": round(job_secs, 2),
    "job_started_iso": job_t0_iso, "job_finished_iso": job_finished_iso,
    "vm_at_terminal": vm, "vm_final_post_tail": vm2,
    "boot_seconds": round(boot_s_1, 2), "port": PORT, "backend_pid": BPID_1,
    "open_marker_line": open_ts, "closed_marker_line": closed_ts,
    "aggregates_refreshed": job_record.get("aggregates_refreshed"),
}
with open(os.path.join(OUT, "phase1-summary.json"), "w") as fh:
    json.dump(phase1_summary, fh, indent=2)
log(f"PHASE 1 SUMMARY: {json.dumps(phase1_summary)}")

# =================================================================================================
# PHASE 2 -- J-05 step 3 / TC-1/TC-2: kill -9 (no clean shutdown), restart, cold verify
# =================================================================================================
assert status == "ok", f"refusing to proceed to phase 2 -- phase 1 backfill did not complete cleanly: {status}"

# pre-kill watermark (belt-and-suspenders; the REAL TC-2 watermark is taken fresh after restart, below)
wm_scanner_results_pre = db_scalar("select max(id) from scanner_results")
wm_forward_returns_pre = db_scalar("select max(id) from forward_returns")
log(f"pre-kill DB watermark: scanner_results.id={wm_scanner_results_pre} "
    f"forward_returns.id={wm_forward_returns_pre}")

log(f"KILL -9 pid={BPID_1} (TC-1 precondition: kill -9 AFTER a completed backfill, no clean shutdown)")
os.kill(BPID_1, signal.SIGKILL)
time.sleep(2)
alive = subprocess.run(["kill", "-0", str(BPID_1)], capture_output=True).returncode == 0
log(f"backend pid {BPID_1} alive after SIGKILL: {alive}")

log("restarting via scripts/start-backend.sh (fresh boot, host-guard caps unchanged)")
backend2 = launch_backend()
boot_t0 = time.time()
boot_s_2 = wait_for_health(PORT)
BPID_2 = backend_pid(PORT)
log(f"phase 2: RESTARTED backend serving, uvicorn pid={BPID_2}, boot-to-health-200 took {boot_s_2:.3f}s")

# ---- TC-2 watermark, taken immediately after the restart, BEFORE any page load ------------------
wm_sr_before = db_scalar("select max(id) from scanner_results")
wm_fr_before = db_scalar("select max(id) from forward_returns")
log(f"TC-2 watermark BEFORE page loads: scanner_results.id={wm_sr_before} forward_returns.id={wm_fr_before}")

# ---- TC-1: cold GET /api/data, timed --------------------------------------------------------------
t0 = time.monotonic()
data_payload = api(PORT, "/data", timeout=60)
data_elapsed = time.monotonic() - t0
log(f"TC-1: cold GET /api/data took {data_elapsed:.3f}s "
    f"(coverage_status={data_payload.get('coverage', {}).get('coverage_status')}, "
    f"universe_count={data_payload.get('coverage', {}).get('universe_count')})")

# ---- TC-2: GET /api/runs (Scanner Runs page) + GET /api/market-phase (home card) ------------------
t0 = time.monotonic()
runs_payload = api(PORT, "/runs", timeout=60)
runs_elapsed = time.monotonic() - t0
t0 = time.monotonic()
mp_payload = api(PORT, "/market-phase", timeout=60)
mp_elapsed = time.monotonic() - t0
log(f"TC-2: GET /api/runs took {runs_elapsed:.3f}s ({len(runs_payload.get('runs', []))} runs); "
    f"GET /api/market-phase took {mp_elapsed:.3f}s (asof={mp_payload.get('asof_date')}, "
    f"phase={mp_payload.get('phase') or mp_payload.get('market_phase')})")

wm_sr_after = db_scalar("select max(id) from scanner_results")
wm_fr_after = db_scalar("select max(id) from forward_returns")
log(f"TC-2 watermark AFTER page loads: scanner_results.id={wm_sr_after} forward_returns.id={wm_fr_after}")

# ---- TC-8/AG-9 post-lane check: every data_provider_runs row created by this WHOLE drill (both
# phases) must read provider='seed' -- never a live fetch.
conn = sqlite3.connect(DB_PATH)
try:
    new_dpr_rows = conn.execute(
        "select id, provider, job_id, status from data_provider_runs where id > ? order by id",
        (wm_dpr_before,),
    ).fetchall()
finally:
    conn.close()
non_seed = [r for r in new_dpr_rows if r[1] != "seed"]
log(f"TC-8/AG-9: {len(new_dpr_rows)} new data_provider_runs row(s) this drill: {new_dpr_rows}")
log(f"TC-8/AG-9: non-seed rows: {non_seed!r} (must be empty)")

# ---- grab the tail of logs/backend.log around this boot for the "no daily_prices-scale prefill" check
log_tail = ""
try:
    with open(BACKEND_LOG) as fh:
        lines = fh.readlines()
    log_tail = "".join(lines[-400:])
except Exception as exc:
    log(f"backend.log tail read failed: {exc}")
with open(os.path.join(OUT, "phase2-backend-log-tail.txt"), "w") as fh:
    fh.write(log_tail)

phase2_summary = {
    "killed_pid": BPID_1, "restarted_pid": BPID_2,
    "boot_seconds_to_health_200": round(boot_s_2, 3),
    "cold_data_seconds": round(data_elapsed, 3),
    "cold_data_coverage_status": data_payload.get("coverage", {}).get("coverage_status"),
    "cold_data_universe_count": data_payload.get("coverage", {}).get("universe_count"),
    "runs_seconds": round(runs_elapsed, 3),
    "market_phase_seconds": round(mp_elapsed, 3),
    "wm_scanner_results_before": wm_sr_before, "wm_scanner_results_after": wm_sr_after,
    "wm_forward_returns_before": wm_fr_before, "wm_forward_returns_after": wm_fr_after,
    "no_new_rows_from_page_loads": (wm_sr_before == wm_sr_after and wm_fr_before == wm_fr_after),
    "target_date": target,
    "wm_data_provider_runs_before": wm_dpr_before,
    "new_data_provider_runs_rows": [list(r) for r in new_dpr_rows],
    "all_new_data_provider_runs_are_seed": not non_seed,
}
with open(os.path.join(OUT, "phase2-summary.json"), "w") as fh:
    json.dump(phase2_summary, fh, indent=2)
log(f"PHASE 2 SUMMARY: {json.dumps(phase2_summary)}")

# ---- tear the (restarted) backend down cleanly ----------------------------------------------------
if BPID_2:
    subprocess.run(["kill", "-TERM", str(BPID_2)])
    time.sleep(8)
    subprocess.run(["pkill", "-f", f"uvicorn main:app.*--port {PORT}"])
log("backend stopped; drill complete")
