"""J-07 step 4 / TC-3 outcome-(b) / TC-11 — LIVE induced-memory-pressure drill (iter-59 fix pass).

The iter-59 audit's DoD item 2 is NOT MET partly because "step 4's induced-pressure abort was never run
live": every isolate-and-continue proof this iteration shipped is a unit/HTTP test in-process. J-07's own
acceptance clause asks for something a unit test cannot give — that the SAME long-lived server process
that just aborted a heavy compute under memory pressure keeps serving `/api/health` and previously cached
reads, with no deadlock, wedge, or restart requirement.

What this drill does, in one long-lived backend process launched through `scripts/start-backend.sh`
(AG-10: host-guard caps applied, never bypassed) with the EXISTING test-only hook
`TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` armed:

  1. baseline    — health + a set of already-warm reads, BEFORE any fault fires
  2. arm/fire    — `GET /api/research/regime-lab` on a guaranteed-cache-MISS key, so the request really
                   enters `compute_regime_lab` and the injected `MemoryError` really fires
  3. honesty     — the response must be HTTP 200 (never a raw 500, never a blank body) carrying the
                   honest degrade markers, with NO fabricated number in any degraded cell
  4. survival    — the SAME pid must still answer `/api/health` and still serve the same previously
                   cached reads afterwards, byte-identical to the baseline capture
  5. no-poison   — the degraded payload must NOT have been written to the cache: a repeat request on the
                   SAME key with the fault DISARMED must come back clean (the never-cache-degraded guard)

Every assertion is written to fault-drill.json as measured values, not booleans alone, so the write-up
quotes the instrument rather than restating it.

Usage: fault_drill.py <out_dir>
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "/home/dennis-chan/Git/trendora"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
PORT = int(os.environ.get("CHAIN_BACKEND_PORT", "8255"))
DB = f"{REPO}/apps/backend/data/trendora.db"
RESULT = {"steps": []}


def rec(**kw):
    kw["at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"
    RESULT["steps"].append(kw)
    print(json.dumps(kw)[:600], flush=True)


def http(path, timeout=900):
    """Return (status, body_bytes, elapsed) — never raises on a 4xx/5xx, because 'did it 500?' is the
    question under test and an exception would hide the answer."""
    t0 = time.monotonic()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read(), time.monotonic() - t0
    except Exception as e:  # noqa: BLE001 — a connection failure IS a wedge signal; record it
        return 0, str(e).encode(), time.monotonic() - t0


def stop_backend():
    subprocess.run(["pkill", "-f", f"uvicorn main:app.*--port {PORT}"], capture_output=True)
    for _ in range(60):
        s, _b, _e = http("/api/health", timeout=3)
        if s == 0:
            return True
        time.sleep(0.5)
    return False


def start_backend(env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    subprocess.Popen(["bash", f"{REPO}/scripts/start-backend.sh"], cwd=REPO, env=env,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 180:
        s, _b, _e = http("/api/health", timeout=5)
        if s == 200:
            return round(time.time() - t0, 3)
        time.sleep(0.25)
    raise SystemExit("backend never became reachable")


def pid():
    out = subprocess.run(["pgrep", "-f", f"uvicorn main:app.*--port {PORT}"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


# A cache key this instance has (almost certainly) never computed: pooled view scoped to an old as-of.
# Read the actual oldest snapshot date from the DB so the key is real, not invented.
import sqlite3  # noqa: E402 — deliberately after the constants, this is a script

conn = sqlite3.connect(DB)
OLDEST = conn.execute("select min(asof_date) from scanner_runs").fetchone()[0]
conn.close()
MISS_KEY = f"/api/research/regime-lab?view=pooled&as_of={OLDEST}"
rec(step="key", miss_key=MISS_KEY, oldest_asof=OLDEST)

# Reads that must keep working across the abort — chosen because each is a DIFFERENT serving path
# (coverage payload, stored run list, stored market phase, stored backtest evidence).
CACHED_READS = ["/api/health", "/api/data", "/api/runs", "/api/market-phase", "/api/backtest"]

# ---------------------------------------------------------------------------------------------------
# 0. restart with the fault ARMED (through the launch script — AG-10 caps intact)
# ---------------------------------------------------------------------------------------------------
stop_backend()
boot = start_backend({"TRENDORA_FAULT_INJECT_MEMORY_ERROR": "regime_lab"})
ARMED_PID = pid()
rec(step="boot_armed", boot_seconds=boot, pid=ARMED_PID,
    env="TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab", launcher="scripts/start-backend.sh")

# ---------------------------------------------------------------------------------------------------
# 1. baseline — capture each cached read BEFORE the fault fires
# ---------------------------------------------------------------------------------------------------
baseline = {}
for p in CACHED_READS:
    s, b, e = http(p, timeout=120)
    baseline[p] = {"status": s, "bytes": len(b), "seconds": round(e, 3)}
    if p != "/api/health":          # /api/health legitimately changes between reads (uptime/phase)
        baseline[p]["body"] = b
rec(step="baseline", reads={k: {kk: vv for kk, vv in v.items() if kk != "body"}
                            for k, v in baseline.items()})

# ---------------------------------------------------------------------------------------------------
# 2/3. fire the fault on a guaranteed-MISS key and check the response is honest, not a 500
# ---------------------------------------------------------------------------------------------------
s, body, elapsed = http(MISS_KEY)
parsed, parse_err = None, None
try:
    parsed = json.loads(body)
except Exception as exc:  # noqa: BLE001
    parse_err = str(exc)

degraded_cells, fabricated = 0, []
whole_status = None
if isinstance(parsed, dict):
    whole_status = parsed.get("regime_lab_status")
    for group in ("by_label", "by_decile"):
        for row in parsed.get(group, []) or []:
            for cell in row.get("by_horizon", []) or []:
                if cell.get("status") == "unavailable":
                    degraded_cells += 1
                    # honest == no fabricated number anywhere in a degraded cell
                    for k in ("mean_return", "mean_max_drawdown"):
                        if cell.get(k) is not None:
                            fabricated.append({"group": group, "horizon": cell.get("horizon"), k: cell[k]})
                    if cell.get("n") not in (0, None):
                        fabricated.append({"group": group, "horizon": cell.get("horizon"), "n": cell.get("n")})

rec(step="fault_fired", request=MISS_KEY, http_status=s, seconds=round(elapsed, 3),
    bytes=len(body), json_parse_error=parse_err, regime_lab_status=whole_status,
    degraded_by_horizon_cells=degraded_cells, fabricated_values_in_degraded_cells=fabricated,
    never_500=(s == 200), body_non_empty=(len(body) > 0))

# ---------------------------------------------------------------------------------------------------
# 4. survival — SAME pid, health + the same cached reads, byte-identical
# ---------------------------------------------------------------------------------------------------
after_pid = pid()
survival = {}
for p in CACHED_READS:
    s2, b2, e2 = http(p, timeout=120)
    entry = {"status": s2, "bytes": len(b2), "seconds": round(e2, 3)}
    if p != "/api/health":
        entry["byte_identical_to_baseline"] = (b2 == baseline[p].get("body"))
    survival[p] = entry
rec(step="survival", pid_before=ARMED_PID, pid_after=after_pid,
    same_process=(ARMED_PID == after_pid and after_pid is not None), reads=survival)

# ---------------------------------------------------------------------------------------------------
# 5. no-poison — restart DISARMED, same key must come back clean (never-cache-degraded guard)
# ---------------------------------------------------------------------------------------------------
stop_backend()
boot2 = start_backend({"TRENDORA_FAULT_INJECT_MEMORY_ERROR": ""})
s3, body3, e3 = http(MISS_KEY)
parsed3 = None
try:
    parsed3 = json.loads(body3)
except Exception:  # noqa: BLE001
    pass
clean_status = parsed3.get("regime_lab_status", "ABSENT") if isinstance(parsed3, dict) else "n/a"
clean_degraded = 0
if isinstance(parsed3, dict):
    for group in ("by_label", "by_decile"):
        for row in parsed3.get(group, []) or []:
            for cell in row.get("by_horizon", []) or []:
                if cell.get("status") == "unavailable":
                    clean_degraded += 1
rec(step="no_poison_recheck", boot_seconds=boot2, pid=pid(), http_status=s3,
    seconds=round(e3, 3), bytes=len(body3), regime_lab_status_after_disarm=clean_status,
    degraded_cells_after_disarm=clean_degraded,
    degraded_payload_was_not_served_from_cache=(clean_degraded == 0 and clean_status == "ABSENT"))

with open(os.path.join(OUT, "fault-drill.json"), "w") as fh:
    json.dump(RESULT, fh, indent=1, default=str)
print("WROTE", os.path.join(OUT, "fault-drill.json"))
