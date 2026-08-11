#!/usr/bin/env bash
# ops-hardening iter-59 AUDIT-FIX pass — one disciplined lane that produces BOTH pieces of evidence the
# audit found missing, from the SAME run:
#
#   * J-05's journey-level verdict (DoD item 1) — the deterministic golden replayed end to end through a
#     real browser, driving a real in-app backfill of one unsnapshotted historical trading day.
#   * TC-3/TC-4/TC-5 (DoD item 6, J-07 steps 1-3) — 1 Hz /api/health polling, a 1 Hz VmPeak time series,
#     and a repeating concurrent GET /api/research/regime-lab, all running THROUGHOUT that same backfill's
#     heavy finalize tail.
#
# Running them together is not a shortcut: J-05's backfill IS the "forward-aggregate warm covering all
# configured horizons" TC-3/TC-4/TC-5 require as their background load, so one job gives both journeys a
# single, jointly-reconcilable evidence base with ONE set of the job's own OPEN/CLOSED markers.
#
# The backend is (re)started through scripts/start-backend.sh — never a hand-rolled uvicorn — so AG-10's
# host-guard caps apply and the job's markers land in the persistent logs/backend.log the reconciler reads.
# (scripts/dev.sh's backend runs under --reload and writes no persistent logfile, which is why it is not
# used for a measured drill.)
set -uo pipefail

REPO=/home/dennis-chan/Git/trendora
OUT="$REPO/runs/goal-ops-hardening-iter-59/evidence-drill/pass2"
PY="$REPO/apps/backend/.venv/bin/python"
PORT="${CHAIN_BACKEND_PORT:-8255}"
FRONTEND="http://localhost:${CHAIN_FRONTEND_PORT:-3255}"
mkdir -p "$OUT"
exec > >(tee -a "$OUT/lane.log") 2>&1
say() { echo "[$(date -u +%H:%M:%SZ)] $*"; }

say "=== restarting backend via scripts/start-backend.sh (persistent logfile + host-guard caps) ==="
pkill -f "uvicorn main:app.*--port $PORT" 2>/dev/null
for _ in $(seq 1 60); do curl -s -m 2 -o /dev/null "http://127.0.0.1:$PORT/api/health" || break; sleep 0.5; done
setsid bash "$REPO/scripts/start-backend.sh" > "$OUT/start-backend.out" 2>&1 < /dev/null &
for _ in $(seq 1 240); do
  curl -s -m 3 -o /dev/null "http://127.0.0.1:$PORT/api/health" && break
  sleep 0.5
done
BPID=$(pgrep -f "uvicorn main:app.*--port $PORT" | head -1)
say "backend up, uvicorn pid=$BPID"
[ -z "$BPID" ] && { say "FATAL: backend did not start"; exit 2; }

# Pre-lane watermarks (TC-2 / TC-8 / AG-9) — recorded BEFORE anything runs.
"$PY" - <<PYEOF > "$OUT/watermarks-before.json"
import json, sqlite3
c = sqlite3.connect("$REPO/apps/backend/data/trendora.db")
q = lambda s: c.execute(s).fetchone()[0]
json.dump({
  "scanner_results_max_id": q("select max(id) from scanner_results"),
  "forward_returns_max_id": q("select max(id) from forward_returns"),
  "data_provider_runs_max_id": q("select max(id) from data_provider_runs"),
  "scanner_runs_rows_for_target": q("select count(*) from scanner_runs where asof_date='2010-11-15'"),
}, open("/dev/stdout", "w"), indent=1)
PYEOF
say "pre-lane watermarks: $(tr -d '\n ' < "$OUT/watermarks-before.json")"

say "=== starting the three standalone instruments (each a process that does nothing else) ==="
setsid "$PY" "$REPO/runs/goal-ops-hardening-iter-59/evidence-drill/poll_health.py" \
  "http://127.0.0.1:$PORT/api/health" "$OUT/tc5-health-poll.csv" 3000 < /dev/null &
POLLER=$!
setsid "$PY" "$REPO/runs/goal-ops-hardening-iter-59/evidence-drill/sample_mem.py" \
  "$BPID" "$OUT/tc4-vmpeak.csv" 3000 < /dev/null &
SAMPLER=$!
setsid "$PY" "$REPO/runs/goal-ops-hardening-iter-59/evidence-drill/load_regime_lab.py" \
  "http://127.0.0.1:$PORT" "$OUT/tc3-regime-lab-poll.csv" 3000 \
  2> "$OUT/tc3-regime-lab-poll.err" < /dev/null &
LOADER=$!
say "instruments: poller=$POLLER sampler=$SAMPLER regime-lab-loader=$LOADER"
sleep 5

say "=== replaying the J-05 golden (drives the real backfill; this is the heavy warm) ==="
"$PY" -c "import sys; print(sys.version)" >/dev/null
timeout 3000 python3 "$REPO/scripts/automation/lib/demo_runner.py" --mode verify \
  --scripts-dir "$REPO/runs/goal-session-ops-hardening/journey-scripts" \
  --journeys J-05,J-07 \
  --results "$REPO/reports/phase-goal-ops-hardening-iter-59-dev-journey-replay.md" \
  --evidence-dir "$REPO/reports/qa/goal-ops-hardening-iter-59-dev-evidence" \
  --base-url "$FRONTEND" --phase-id goal-ops-hardening-iter-59 \
  --backend-health-url "http://127.0.0.1:$PORT/api/health" \
  --repo-root "$REPO"
say "replay rc=$? (demo_runner records BLOCKED/FAIL in the results file, not always via rc)"

say "holding 45s past the replay for the post-completion health tail"
sleep 45

kill "$POLLER" "$SAMPLER" "$LOADER" 2>/dev/null
sleep 2
pkill -f "poll_health.py .*pass2" 2>/dev/null
pkill -f "sample_mem.py" 2>/dev/null
pkill -f "load_regime_lab.py .*pass2" 2>/dev/null
say "instruments stopped"

JOB=$("$PY" - <<PYEOF
import json, sqlite3
c = sqlite3.connect("$REPO/apps/backend/data/trendora.db")
r = c.execute("select job_id, id, status, started_at, finished_at, message from data_provider_runs "
              "order by id desc limit 1").fetchone()
print(r[0])
json.dump({"job_id": r[0], "dpr_id": r[1], "status": r[2], "started_at": r[3],
           "finished_at": r[4], "message": r[5]}, open("$OUT/job-record.json", "w"), indent=1)
PYEOF
)
say "job under measurement: $JOB"

"$PY" - <<PYEOF > "$OUT/watermarks-after.json"
import json, sqlite3
c = sqlite3.connect("$REPO/apps/backend/data/trendora.db")
q = lambda s: c.execute(s).fetchone()[0]
json.dump({
  "scanner_results_max_id": q("select max(id) from scanner_results"),
  "forward_returns_max_id": q("select max(id) from forward_returns"),
  "data_provider_runs_max_id": q("select max(id) from data_provider_runs"),
  "scanner_runs_rows_for_target": q("select count(*) from scanner_runs where asof_date='2010-11-15'"),
  "new_provider_runs": c.execute("select id, provider, status from data_provider_runs order by id desc limit 5").fetchall(),
}, open("/dev/stdout", "w"), indent=1)
PYEOF

say "=== reconciling (every published figure derived from the raw artifacts) ==="
python3 "$REPO/runs/goal-ops-hardening-iter-59/evidence-drill/reconcile_drill.py" "$OUT" "$JOB"
say "=== LANE DONE ==="
