#!/bin/bash
OUT="/home/dennis-chan/Git/trendora/runs/goal-ops-hardening-iter-34/bqa-health-poll/health-poll.csv"
echo "epoch,http_code,time_total" > "$OUT"
for i in $(seq 1 100); do
  epoch=$(date +%s.%N)
  line=$(curl -s -o /dev/null -w "%{http_code},%{time_total}" http://localhost:8255/api/health)
  echo "$epoch,$line" >> "$OUT"
  sleep 1
done
