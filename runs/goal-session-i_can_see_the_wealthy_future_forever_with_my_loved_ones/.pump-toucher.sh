#!/usr/bin/env bash
DIR="$1"; SESSDIR="$2"
echo $$ > "$DIR/.pump-toucher.pid"
while true; do
  touch "$DIR/.pump-alive" 2>/dev/null || true
  [ -f "$SESSDIR/.pump-toucher.stop" ] && break
  EP=$(cat "$SESSDIR/.engine-pid" 2>/dev/null || true)
  if [ -n "$EP" ] && ! kill -0 "$EP" 2>/dev/null; then break; fi
  sleep 1
done
rm -f "$DIR/.pump-toucher.pid" 2>/dev/null || true
