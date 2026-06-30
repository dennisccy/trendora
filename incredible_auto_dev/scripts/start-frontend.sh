#!/usr/bin/env bash
# start-frontend.sh — Start the Next.js frontend for automated QA
# Used by browser-qa-phase.sh when frontend is not running.
# Respects CHAIN_FRONTEND_PORT (default: 3000) and CHAIN_BACKEND_PORT (default: 8000)
# for multi-project parallel runs.
#
# Serves a PRE-BUILT production bundle via `next start` (NOT `next dev`).
# WHY (iter-3 bring-up fix): the QA browser lane needs a fast, stable readiness 2xx and
# routes that are ready the instant they are first requested. `next dev` compiles each
# route ON FIRST REQUEST and runs a heavy turbopack/swc worker tree; under the full-pipeline
# fanout that produced compile-races / process death / a dev-vs-prod `.next` clobber — the
# iter-2 "Frontend not running at :PORT" SKIP that lost the whole browser lane. `next start`
# serves ONE consistent, fully pre-compiled bundle: the root AND every /stocks, /stocks/[t]
# and /evidence route answer in <15ms (measured) with no per-request compile, so the harness
# readiness probe is deterministic and the browser never races a mid-compile / empty frame.
# Interactive human dev (hot reload) still uses `next dev` via scripts/dev.sh — unchanged.
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Deterministic per-project port fallback (matches ensure_phase_ports in
# incredible_auto_dev/scripts/automation/lib/common.sh).
_port_root="$REPO_ROOT"
[[ "$_port_root" == */incredible_auto_dev ]] && _port_root="${_port_root%/incredible_auto_dev}"
_offset=$(printf '%s' "$_port_root" | sha1sum | cut -c1-4)
_offset=$((16#$_offset % 1000))
FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-$((3000 + _offset))}"
BACKEND_PORT="${CHAIN_BACKEND_PORT:-$((8000 + _offset))}"

cd "$REPO_ROOT/apps/frontend"

# Tell the Next.js frontend where the backend is. Export both a full URL
# (what the app actually reads) and the port (for scripts that still refer
# to the old name). For a PRODUCTION build these NEXT_PUBLIC_* values are inlined
# at BUILD time (not read at runtime like `next dev`), so the bundle must be built
# with the same backend base it will serve against — the stamp below enforces that.
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}"
export NEXT_PUBLIC_API_PORT="${BACKEND_PORT}"

# Build OUTSIDE the readiness window: only (re)build when a usable production bundle for
# THIS backend base is absent. The stamp records the baked NEXT_PUBLIC_API_URL|PORT so that
#   - a backend-port change forces a rebuild (stale baked URL would 'Backend unavailable'), and
#   - a prior `next dev` (which writes no stamp) is never mistaken for a prod build.
# A from-scratch production build of this app is ~18s (measured) — well under the harness's
# 60s first-attempt budget — so even a cold fallback build stays inside the gate; the normal
# pipeline path finds the developer's pre-built, correctly-stamped .next and skips the build.
_stamp=".next/.qa-serve-base"
_want="${NEXT_PUBLIC_API_URL}|${NEXT_PUBLIC_API_PORT}"
if [[ ! -f .next/BUILD_ID ]] || [[ "$(cat "$_stamp" 2>/dev/null)" != "$_want" ]]; then
  echo "[start-frontend] No usable production build for ${_want} — building (~18s)…" >&2
  npx next build
  printf '%s' "$_want" > "$_stamp"
fi

# Pre-bind port-free (iter-5 QA-harness fix): guarantee nothing still holds $FRONTEND_PORT
# before `next start`. This script is launched by the QA browser lane; if a prior run's
# next-server still owns the port, `next start` either fails to bind — the canonical
# browser-qa lane then SKIPs every check with "frontend not running" (the exact iter-4
# failure) — or the readiness probe answers from the STALE bundle instead of the one just
# built above. We mirror the proven free-the-port pattern from scripts/dev.sh (lines 22-41),
# scoped to $FRONTEND_PORT ONLY (start-backend.sh owns the backend port). The wait loop
# breaks immediately when the port is already free, so the normal pipeline path is unaffected.
PIDS=$(lsof -ti :$FRONTEND_PORT 2>/dev/null | sort -u || true)
if [ -n "$PIDS" ]; then
  echo "[start-frontend] Freeing port $FRONTEND_PORT (held by: $PIDS)" >&2
  kill -9 $PIDS 2>/dev/null || true
fi
# Also kill via fuser (catches child processes lsof may list under a different PID)
fuser -k -9 $FRONTEND_PORT/tcp 2>/dev/null || true
# Wait until the port is fully released: no owning process AND no lingering socket
for i in $(seq 1 50); do
  if ! lsof -ti :$FRONTEND_PORT >/dev/null 2>&1 && \
     ! ss -tlnH sport = :$FRONTEND_PORT 2>/dev/null | grep -q .; then
    break
  fi
  # On each iteration, re-kill anything that's still holding the port
  fuser -k -9 $FRONTEND_PORT/tcp 2>/dev/null || true
  sleep 0.1
done

exec npx next start -p "$FRONTEND_PORT"
