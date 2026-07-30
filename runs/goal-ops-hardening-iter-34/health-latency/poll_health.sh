#!/usr/bin/env bash
# ops-hardening iter-34 (J-07 step 2): poll GET /api/health at 1Hz, recording HTTP status AND round-trip
# latency (curl's own %{time_total}, a real client-observed measurement -- not a server-side timer) for
# each poll, into a CSV: epoch_s,http_code,time_total_s. Runs for DURATION_S seconds then exits.
set -u
PORT="${1:-8255}"
DURATION_S="${2:-90}"
OUT="${3:-/dev/stdout}"
echo "epoch_s,http_code,time_total_s" > "$OUT"
END=$(( $(date +%s) + DURATION_S ))
while [ "$(date +%s)" -lt "$END" ]; do
  EPOCH=$(date +%s.%N)
  READING=$(curl -s -o /dev/null -w "%{http_code},%{time_total}" "http://127.0.0.1:${PORT}/api/health")
  echo "${EPOCH},${READING}" >> "$OUT"
  sleep 1
done
