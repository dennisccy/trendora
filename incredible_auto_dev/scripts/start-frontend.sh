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

# ==== HOST-GUARD (goal.md AG-10) — DO NOT REMOVE OR WEAKEN ==========================================
# ops-hardening iter-43 (goal.md "Additional binding notes", the iter-33/i owner item): apply this
# host's declared CPU-affinity mask + BLAS/OMP/numexpr thread caps to whatever this script launches —
# mirrors scripts/start-backend.sh's own block (env var names, HOST_GUARD_ENV_FILE test seam, and the
# "prefix the launched process with taskset" mechanism) byte-for-byte in structure. Placed BEFORE the
# build-if-stale section below (not just around the final `next start`) because a stale-build path
# execs a real `next build`, which spins up its own multi-worker TypeScript/webpack compile — genuine
# CPU/thread pressure from the QA / demo lanes that this project's host-guard envelope must cover, not
# only the eventual long-lived server. Absent file or HOST_GUARD_ENABLED=0 -> zero behavior change —
# host-guard stays fully project-neutral per its own header contract
# (project-extensions/host-guard/host-guard.env). Every value below comes from that file; no magic
# numbers here. Stripping this block is a REGRESSION regardless of test outcome (goal.md AG-10) — the
# caps are a physical hardware constraint (two instant hard resets under all-core vectorized ingest
# bursts, 2026-07-20/21), not a perf knob. HOST_GUARD_ENV_FILE lets tests point at a scratch copy (to
# exercise the absent/disabled branches without ever touching the real, safety-critical committed
# file) — unset in every real launch, so production always resolves to the committed path below.
HOST_GUARD_ENV="${HOST_GUARD_ENV_FILE:-$REPO_ROOT/project-extensions/host-guard/host-guard.env}"
HOST_GUARD_CMD_PREFIX=()
if [[ -f "$HOST_GUARD_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$HOST_GUARD_ENV"
  if [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]]; then
    export OMP_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
    export OPENBLAS_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
    export MKL_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
    export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
    HOST_GUARD_CMD_PREFIX=(taskset -c "$HOST_GUARD_CPU_LIST")
    echo "[start-frontend.sh] host-guard: cpu_list=$HOST_GUARD_CPU_LIST blas_threads=$HOST_GUARD_BLAS_THREADS" >&2
  fi
fi
# ==== end HOST-GUARD =================================================================================

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
  if ! "${HOST_GUARD_CMD_PREFIX[@]}" npx next build; then
    echo "[start-frontend.sh] next build FAILED (see output above) — refusing to fall back to" \
         "'next dev' or serve a stale build." >&2
    exit 1
  fi
else
  echo "[start-frontend.sh] existing '$DIST_DIR' build is current relative to sources — skipping rebuild." >&2
fi
# ==== end build-if-stale =============================================================================

exec "${HOST_GUARD_CMD_PREFIX[@]}" npx next start -p "$FRONTEND_PORT"
