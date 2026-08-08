"""TC-2 — the CONCURRENT ingest finalize-tail drill (iter-52 audit B3 / recommended next step 2).

Identical to Addendum 13's solo drill (`drill/run_drill.py`) in every respect — same launch script,
same dedicated health poller with the same 5.0s ceiling, same availability-driven target-date choice,
same 40s post-completion tail — with ONE addition: a separate process keeps a heavy research request
(`/api/research/factor-lab?all=true` / `/api/research/factor-combination`) outstanding throughout, which
is the scenario UT-08's 19-of-892 finding came from and the one a solo drill provably cannot cover.

Orchestrates only. The backend is launched by `scripts/start-backend.sh` (AG-10 caps live); health is
polled by a dedicated process; the research load runs in a second dedicated process; job status is polled
here. Also captures the J-06/TC-7 Factor Lab on-load API latency once the tail is complete (warm cache,
same still-running process) so TC-7's API half is measured against the shipped tree.

Usage: run_drill_concurrent.py <out_dir> <ceiling_seconds> [target_date]
"""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "/home/dennis-chan/Git/trendora"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
CEILING = float(sys.argv[2])
FORCED_DATE = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
PY = f"{REPO}/apps/backend/.venv/bin/python"


def api(path, method="GET", body=None, timeout=120):
    url = f"http://127.0.0.1:{PORT}/api{path}"
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


# ---- resolve the project's own default port exactly the way start-backend.sh does -------------
offset = int(hashlib.sha1(REPO.encode()).hexdigest()[:4], 16) % 1000
PORT = int(os.environ.get("CHAIN_BACKEND_PORT", 8000 + offset))
log(f"port={PORT}")

# ---- launch the backend through the project launch script (AG-10) ------------------------------
backend = subprocess.Popen(["bash", f"{REPO}/scripts/start-backend.sh"], cwd=REPO,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           start_new_session=True)
log(f"start-backend.sh launched (launcher pid={backend.pid})")


def backend_pid():
    out = subprocess.run(["pgrep", "-f", f"uvicorn main:app.*--port {PORT}"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


boot_t0 = time.time()
while time.time() - boot_t0 < 180:
    try:
        api("/health", timeout=10)
        break
    except Exception:
        time.sleep(1)
else:
    log("FATAL: backend never became reachable")
    sys.exit(2)
BOOT_S = time.time() - boot_t0
BPID = backend_pid()
log(f"backend serving, uvicorn pid={BPID}, boot took {BOOT_S:.1f}s")

# ---- start the dedicated health poller ---------------------------------------------------------
health_csv = os.path.join(OUT, "health-polls.csv")
poller = subprocess.Popen(
    [PY, os.path.join(HERE, "poll_health.py"),
     f"http://127.0.0.1:{PORT}/api/health", health_csv, str(CEILING + 300)],
    start_new_session=True)
log(f"health poller started (pid={poller.pid}) -> {health_csv}")
time.sleep(5)

# ---- pick the target date from the instance's own availability (never a hardcoded literal) ------
if FORCED_DATE:
    target = FORCED_DATE
    log(f"target date forced: {target}")
else:
    av = api("/data/availability")
    all_dates = sorted(c["date"] for c in av.get("cells", []))
    free = [c["date"] for c in av.get("cells", []) if not c.get("snapshot_exists")]
    cutoff = all_dates[-90] if len(all_dates) > 90 else all_dates[0]
    eligible = sorted(d for d in free if d < cutoff)
    if not eligible:
        log("FATAL: no unsnapshotted trading day with sufficient following calendar")
        sys.exit(3)
    target = eligible[-1]
    log(f"target date chosen from /api/data/availability: {target} "
        f"({len(eligible)} eligible unsnapshotted trading days, {len(free)} unsnapshotted overall)")

# ---- start the ingest job (offline / seed only -- AG-9, TC-11) ---------------------------------
job = api("/data/jobs", "POST", {"kind": "backfill", "start": target, "end": target})
JOB = job["job_id"]
log(f"job started id={JOB} kind={job['kind']} source={job.get('source')!r} range={target}..{target}")
job_t0 = time.time()

# ---- start the CONCURRENT research load (this is the only difference from the solo drill) -------
load_csv = os.path.join(OUT, "research-load.csv")
load = subprocess.Popen(
    [PY, os.path.join(HERE, "load_research.py"),
     f"http://127.0.0.1:{PORT}", load_csv, str(CEILING + 60)],
    stderr=open(os.path.join(OUT, "research-load.err"), "w"),
    start_new_session=True)
log(f"CONCURRENT research load started (pid={load.pid}) -> {load_csv}")

# ---- poll the job to terminal ------------------------------------------------------------------
terminal = {"ok", "partial", "failed", "resumable", "completed", "error", "interrupted", "cancelled"}
last_msg = None
status = None
while time.time() - job_t0 < CEILING:
    try:
        st = api(f"/data/jobs/{JOB}", timeout=30)
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
log(f"job finished status={status} after {job_secs:.2f}s")

with open(os.path.join(OUT, "job-record.json"), "w") as fh:
    json.dump(api(f"/data/jobs/{JOB}", timeout=60), fh, indent=2)

# ---- VmPeak / VmHWM (J-07 step 3) ---------------------------------------------------------------
vm = {}
try:
    with open(f"/proc/{BPID}/status") as fh:
        for line in fh:
            for k in ("VmPeak", "VmHWM", "VmRSS", "VmSize"):
                if line.startswith(k + ":"):
                    vm[k] = line.split()[1] + " kB"
except Exception as exc:
    log(f"VmPeak read failed: {exc}")
log(f"memory: {vm}")

# ---- keep polling 30s past completion (TC-1/TC-2 require the tail) ------------------------------
log("holding 40s past completion for the post-completion health tail")
time.sleep(40)

# ---- stop the concurrent load, then take the TC-7 warm on-load API latency ----------------------
load.terminate()
try:
    load.wait(timeout=20)
except Exception:
    load.kill()
log("concurrent research load stopped")

tc7 = []
for i in range(3):
    t0 = time.monotonic()
    try:
        payload = api("/research/factor-lab?all=true", timeout=600)
        el = time.monotonic() - t0
        tc7.append({"run": i, "status": 200, "elapsed_s": round(el, 4),
                    "n_factors": len(payload.get("factors_table", []))})
    except Exception as exc:
        tc7.append({"run": i, "status": None, "elapsed_s": round(time.monotonic() - t0, 4),
                    "error": str(exc)})
    log(f"TC-7 on-load factor-lab?all=true run {i}: {tc7[-1]}")

poller.terminate()
try:
    poller.wait(timeout=10)
except Exception:
    poller.kill()

with open(os.path.join(OUT, "summary.json"), "w") as fh:
    json.dump({"job_id": JOB, "target": target, "status": status,
               "job_seconds": round(job_secs, 2), "vmpeak": f"VmPeak:\t{vm.get('VmPeak', '?')}",
               "vm": vm, "boot_seconds": round(BOOT_S, 2),
               "port": PORT, "backend_pid": BPID,
               "job_started_epoch": job_t0,
               "tc7_factor_lab_all_warm_api": tc7}, fh, indent=2)

# ---- tear the backend down ----------------------------------------------------------------------
if BPID:
    subprocess.run(["kill", "-TERM", str(BPID)])
    time.sleep(8)
    subprocess.run(["pkill", "-f", f"uvicorn main:app.*--port {PORT}"])
log("backend stopped; drill complete")
