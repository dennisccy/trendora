#!/usr/bin/env bash
# QA poller for J-07/J-08 live BCW verification (goal-ops-hardening-iter-23, browser-qa-agent).
# Polls GET /api/health and GET /api/backtest?as_of=2026-07-08 once per second, records VmPeak
# of the backend PID, and stops early once forward_aggregate_cache shows all 5 horizons present
# for (asof_key=2026-07-08, dataset_version=r1865-f3954530) -- i.e. the window is complete.
set -u
OUT_CSV="/home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-23/qa-bcw-poll.csv"
DONE_MARKER="/home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-23/qa-bcw-poll.done"
BACKEND_PID=1134166
DB="/home/dennis-chan/Git/trendora/apps/backend/data/trendora.db"
DATASET_VERSION="r1865-f3954530"
ASOF="2026-07-08"
MAX_ITERS=100

rm -f "$DONE_MARKER"
echo "iter,elapsed_s,health_code,health_time_s,backtest_code,backtest_time_s,vmpeak_kb,horizons_done,readiness" > "$OUT_CSV"

START_TS=$(date +%s.%N)
for i in $(seq 1 "$MAX_ITERS"); do
  NOW_TS=$(date +%s.%N)
  ELAPSED=$(python3 -c "print(f'{$NOW_TS-$START_TS:.2f}')")

  H_OUT=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" http://localhost:8255/api/health)
  H_CODE=$(echo "$H_OUT" | cut -d' ' -f1)
  H_TIME=$(echo "$H_OUT" | cut -d' ' -f2)

  B_OUT=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" "http://localhost:8255/api/backtest?as_of=${ASOF}")
  B_CODE=$(echo "$B_OUT" | cut -d' ' -f1)
  B_TIME=$(echo "$B_OUT" | cut -d' ' -f2)

  VMPEAK=$(grep VmPeak /proc/"$BACKEND_PID"/status 2>/dev/null | awk '{print $2}')
  READINESS=$(curl -s http://localhost:8255/api/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('readiness','?'))" 2>/dev/null)

  HORIZONS=$(python3 - <<PYEOF
import sqlite3
con = sqlite3.connect("file:${DB}?mode=ro", uri=True)
cur = con.cursor()
cur.execute("SELECT COUNT(DISTINCT horizon) FROM forward_aggregate_cache WHERE asof_key=? AND dataset_version=?", ("${ASOF}", "${DATASET_VERSION}"))
print(cur.fetchone()[0])
PYEOF
)

  echo "${i},${ELAPSED},${H_CODE},${H_TIME},${B_CODE},${B_TIME},${VMPEAK},${HORIZONS},${READINESS}" >> "$OUT_CSV"

  if [ "$HORIZONS" -ge 5 ]; then
    echo "window complete at iter=${i} elapsed=${ELAPSED}s" > "$DONE_MARKER"
    break
  fi
  sleep 1
done

if [ ! -f "$DONE_MARKER" ]; then
  echo "MAX_ITERS reached without completion" > "$DONE_MARKER"
fi
