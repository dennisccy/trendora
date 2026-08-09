#!/bin/bash
OUT=/home/dennis-chan/Git/trendora/reports/qa/goal-ops-hardening-iter-54-evidence/j05-health-poll.csv
for i in $(seq 1 900); do
  ts=$(date -u +%Y-%m-%dT%H:%M:%S)
  resp=$(curl -s -w "|%{http_code}|%{time_total}" http://localhost:8255/api/health)
  body="${resp%%|*}"
  rest="${resp#*|}"
  code="${rest%%|*}"
  ttime="${rest#*|}"
  readiness=$(echo "$body" | python3 -c "import json,sys;print(json.load(sys.stdin).get('readiness','?'))" 2>/dev/null || echo "PARSE_ERR")
  echo "$ts,$code,$ttime,$readiness" >> "$OUT"
  status=$(curl -s "http://localhost:8255/api/data" | python3 -c "
import json,sys
d=json.load(sys.stdin)
r=[x for x in d['runs'] if x['id']==351]
print(r[0]['status'] if r else 'NOTFOUND')
" 2>/dev/null)
  if [ "$status" != "running" ]; then
    echo "JOB_DONE:$status" >> "$OUT"
    break
  fi
  sleep 2
done
echo "poll loop finished, final status=$status"
