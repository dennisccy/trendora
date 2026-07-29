#!/usr/bin/env bash
# start-frontend.sh — Start the Next.js frontend for automated QA
# Used by browser-qa-phase.sh when frontend is not running.
# Respects CHAIN_FRONTEND_PORT (default: 3000) and CHAIN_BACKEND_PORT (default: 8000)
# for multi-project parallel runs.
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
# to the old name). process.env takes precedence over .env.local in Next.js,
# so a hardcoded .env.local URL does not stick when QA uses a different port.
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}"
export NEXT_PUBLIC_API_PORT="${BACKEND_PORT}"

# ==== build-if-stale, then serve PRODUCTION mode (ops-hardening iter-33) ============================
# Previously this script execed `npx next dev` unconditionally, despite every other doc calling it
# "prod mode" (measure-perf.sh's own header, goal.md's J-06 step-1 text) — two consecutive evaluators
# (iter-31, iter-32) named this the top blocking item, since a browser TTI sweep against `next dev`
# measures on-demand per-route compilation, not real production page-load time. `next.config.mjs`
# already wires `NEXT_DIST_DIR` -> `distDir` (default ".next"), so a verification build can target a
# scratch directory instead of clobbering a live `.next`.
DIST_DIR="${NEXT_DIST_DIR:-.next}"
BUILD_ID_FILE="$DIST_DIR/BUILD_ID"

_build_is_stale_or_missing() {
  # Missing entirely (never built, or a `next dev`-mode `.next` with no BUILD_ID at all) -> stale.
  # A bare directory-existence check would wrongly treat a dev-mode `.next` as a current prod build.
  if [[ ! -f "$BUILD_ID_FILE" ]]; then
    return 0
  fi
  # Otherwise stale iff any real source file (excluding node_modules/ and the dist dir itself) is
  # newer than the build marker — covers apps/frontend's tracked sources plus package.json/
  # package-lock.json, since none of those live under the excluded paths.
  local newer
  newer=$(find . \
    \( -path "./node_modules" -o -path "./$DIST_DIR" \) -prune -o \
    -type f -newer "$BUILD_ID_FILE" -print -quit)
  [[ -n "$newer" ]]
}

if _build_is_stale_or_missing; then
  echo "[start-frontend.sh] '$DIST_DIR' build missing or stale relative to sources — running 'next build'..." >&2
  if ! npx next build; then
    echo "[start-frontend.sh] next build FAILED (see output above) — refusing to fall back to" \
         "'next dev' or serve a stale build." >&2
    exit 1
  fi
else
  echo "[start-frontend.sh] existing '$DIST_DIR' build is current relative to sources — skipping rebuild." >&2
fi
# ==== end build-if-stale =============================================================================

exec npx next start -p "$FRONTEND_PORT"
