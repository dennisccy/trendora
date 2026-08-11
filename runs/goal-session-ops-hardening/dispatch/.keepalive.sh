#!/usr/bin/env bash
D="/home/dennis-chan/Git/trendora/runs/goal-session-ops-hardening/dispatch"
PUMP_PID=10078
while [ -e "$D/.pump-keepalive-on" ] && [ -d "/proc/$PUMP_PID" ]; do
  [ -e "$D/.pump-alive" ] && touch "$D/.pump-alive"
  sleep 20
done
