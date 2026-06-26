#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Deterministic per-project port offset (mirror of
# incredible_auto_dev/scripts/automation/lib/common.sh::_project_port_offset).
# Strip trailing /incredible_auto_dev so running from the subtree or the
# project root produces the same offset for a given project.
_port_root="$ROOT_DIR"
[[ "$_port_root" == */incredible_auto_dev ]] && _port_root="${_port_root%/incredible_auto_dev}"
_offset=$(printf '%s' "$_port_root" | sha1sum | cut -c1-4)
_offset=$((16#$_offset % 1000))
BACKEND_PORT="${CHAIN_BACKEND_PORT:-$((8000 + _offset))}"
FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-$((3000 + _offset))}"

# The machine's primary LAN IP — dev.sh advertises the app at BOTH localhost and this LAN IP (see the
# banner below), so the backend CORS must ALSO accept the LAN-IP frontend origin (J-108). Computed here,
# BEFORE the backend starts, so CORS_ORIGINS / CORS_ORIGIN_REGEX can include it.
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

# Kill processes occupying the ports and wait until they are free
for PORT in $BACKEND_PORT $FRONTEND_PORT; do
  PIDS=$(lsof -ti :$PORT 2>/dev/null | sort -u || true)
  if [ -n "$PIDS" ]; then
    echo "Killing processes on port $PORT: $PIDS"
    kill -9 $PIDS 2>/dev/null || true
  fi
  # Also kill via fuser (catches child processes lsof may list under a different PID)
  fuser -k -9 $PORT/tcp 2>/dev/null || true
  # Wait until port is fully released: no owning process AND no lingering socket
  for i in $(seq 1 50); do
    if ! lsof -ti :$PORT >/dev/null 2>&1 && \
       ! ss -tlnH sport = :$PORT 2>/dev/null | grep -q .; then
      break
    fi
    # On each iteration, re-kill anything that's still holding the port
    fuser -k -9 $PORT/tcp 2>/dev/null || true
    sleep 0.1
  done
done

# Start backend
echo "Starting backend on :$BACKEND_PORT ..."
(
  cd "$ROOT_DIR/apps/backend"
  source .venv/bin/activate
  # J-108: accept the localhost origins AND the LAN-IP frontend origin advertised below, so a browser
  # opened at http://<LAN_IP>:<FRONTEND_PORT> is not CORS-blocked (which stuck the badge "unavailable").
  _lan_origin="${LOCAL_IP:+,http://${LOCAL_IP}:${FRONTEND_PORT}}"
  export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:${FRONTEND_PORT},http://localhost:3000,http://localhost:3001${_lan_origin}}"
  # Dev-only: also accept ANY private-LAN origin via regex (robust if the LAN IP changes between runs).
  # Never set in production — main.py reads it only when present, so prod CORS stays the explicit list.
  export CORS_ORIGIN_REGEX="${CORS_ORIGIN_REGEX:-http://(localhost|127\.0\.0\.1|10\.[0-9.]+|172\.(1[6-9]|2[0-9]|3[01])\.[0-9.]+|192\.168\.[0-9.]+)(:[0-9]+)?}"
  uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT
) &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on :$FRONTEND_PORT ..."
(
  cd "$ROOT_DIR/apps/frontend"
  NEXT_PUBLIC_API_URL="http://localhost:${BACKEND_PORT}" NEXT_PUBLIC_API_PORT="${BACKEND_PORT}" npx next dev -p "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo ""
echo "  Backend:   http://localhost:${BACKEND_PORT}   http://${LOCAL_IP}:${BACKEND_PORT}"
echo "  Frontend:  http://localhost:${FRONTEND_PORT}   http://${LOCAL_IP}:${FRONTEND_PORT}"
echo ""
echo "  Backend PID: $BACKEND_PID  |  Frontend PID: $FRONTEND_PID"
echo "  Press Ctrl+C to stop both."

# Propagate Ctrl+C to both children
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
