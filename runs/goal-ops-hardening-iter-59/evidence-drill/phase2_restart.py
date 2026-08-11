"""J-05 step 3 / TC-1 / TC-2 — kill -9, restart, cold-serve-from-storage (iter-59 audit-fix pass).

Re-executed in this pass so J-05's four acceptance steps all rest on ONE coherent run against ONE DB
state, rather than step 3 sitting alone in an earlier, interrupted drill. Deliberately uses the date the
J-05 golden's own lane just ingested, NOT the golden's newly-rotated reserve date (TC-12: a verification
exercise must never consume another fixture's precondition).

  TC-1  kill -9 the backend (no clean shutdown) after a COMPLETED backfill -> relaunch via
        scripts/start-backend.sh -> time boot-to-first-200 and a COLD GET /api/data -> confirm the
        coverage panel's numbers come from the persisted payload and that no daily_prices-scale
        (3.3M-row) prefill appears in this boot's own logs/backend.log slice.
  TC-2  watermark max(scanner_results.id)/max(forward_returns.id) immediately after the restart and
        again after loading /api/runs and /api/market-phase -> equal watermarks prove the page loads
        served stored values and computed nothing on read.

Usage: phase2_restart.py <out_dir>
"""
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.request

REPO = "/home/dennis-chan/Git/trendora"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
PORT = int(os.environ.get("CHAIN_BACKEND_PORT", "8255"))
DB = f"{REPO}/apps/backend/data/trendora.db"
BACKEND_LOG = f"{REPO}/logs/backend.log"
R = {}


def api(path, timeout=120):
    t0 = time.monotonic()
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout) as r:
        body = r.read()
    return json.loads(body), time.monotonic() - t0


def q(sql):
    c = sqlite3.connect(DB)
    try:
        return c.execute(sql).fetchone()[0]
    finally:
        c.close()


def pid():
    out = subprocess.run(["pgrep", "-f", f"uvicorn main:app.*--port {PORT}"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def wait_health(timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=5).read()
            return time.time() - t0
        except Exception:  # noqa: BLE001
            time.sleep(0.1)
    raise SystemExit("backend never came back")


# The log line count BEFORE the kill, so the "no whole-table prefill" check reads ONLY this boot's own
# slice of logs/backend.log — never the whole file, where an older boot's line would answer for this one.
log_lines_before = sum(1 for _ in open(BACKEND_LOG, errors="replace"))
old_pid = pid()
R["pid_before_kill"] = old_pid
R["backend_log_lines_before_kill"] = log_lines_before
print("killing", old_pid, "with SIGKILL (no clean shutdown — TC-1's precondition)", flush=True)
os.kill(old_pid, signal.SIGKILL)
time.sleep(3)
R["pid_alive_after_sigkill"] = subprocess.run(["kill", "-0", str(old_pid)],
                                              capture_output=True).returncode == 0

subprocess.Popen(["bash", f"{REPO}/scripts/start-backend.sh"], cwd=REPO,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
R["boot_seconds_to_first_health_200"] = round(wait_health(), 3)
R["pid_after_restart"] = pid()
print("restarted:", R["pid_after_restart"], "boot", R["boot_seconds_to_first_health_200"], "s", flush=True)

# TC-2 watermark BEFORE any page load
R["wm_scanner_results_before"] = q("select max(id) from scanner_results")
R["wm_forward_returns_before"] = q("select max(id) from forward_returns")

data, t_data = api("/api/data", timeout=120)
cov = data.get("coverage", {})
R["cold_data_seconds"] = round(t_data, 3)
R["cold_data_universe_count"] = cov.get("universe_count")
R["cold_data_coverage_status"] = cov.get("coverage_status")
R["cold_data_gaps"] = len(cov.get("gaps", []) or []) if isinstance(cov.get("gaps"), list) else cov.get("gaps")

runs, t_runs = api("/api/runs", timeout=120)
R["runs_seconds"] = round(t_runs, 3)
R["runs_count"] = len(runs.get("runs", []) or [])
mp, t_mp = api("/api/market-phase", timeout=120)
R["market_phase_seconds"] = round(t_mp, 3)
R["market_phase_asof"] = mp.get("asof_date")
R["market_phase"] = mp.get("phase") or mp.get("market_phase")

R["wm_scanner_results_after"] = q("select max(id) from scanner_results")
R["wm_forward_returns_after"] = q("select max(id) from forward_returns")
R["no_new_rows_created_by_page_loads"] = (
    R["wm_scanner_results_before"] == R["wm_scanner_results_after"]
    and R["wm_forward_returns_before"] == R["wm_forward_returns_after"])

# TC-1's "no 3.3M-row prefill" check, over THIS boot's slice only.
slice_lines = []
with open(BACKEND_LOG, errors="replace") as fh:
    for i, line in enumerate(fh):
        if i >= log_lines_before:
            slice_lines.append(line)
needles = ("prefill", "daily_prices", "bar_cache", "whole-table", "loading all bars")
R["backend_log_lines_this_boot"] = len(slice_lines)
R["prefill_suspect_lines"] = [ln.strip()[:300] for ln in slice_lines
                              if any(n in ln.lower() for n in needles)]
R["daily_prices_row_count"] = q("select count(*) from daily_prices")
with open(os.path.join(OUT, "phase2-backend-log-slice.txt"), "w") as fh:
    fh.writelines(slice_lines)

with open(os.path.join(OUT, "phase2-restart.json"), "w") as fh:
    json.dump(R, fh, indent=1)
print(json.dumps(R, indent=1))
