#!/usr/bin/env bash
# start-backend.sh — Start the FastAPI backend for automated QA
# Used by qa-phase.sh and browser-qa-phase.sh when backend is not running.
# Respects CHAIN_BACKEND_PORT (default: 8000) for multi-project parallel runs.
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Deterministic per-project port fallback (matches ensure_phase_ports in
# incredible_auto_dev/scripts/automation/lib/common.sh) so standalone runs
# don't collide with other projects on this machine.
_port_root="$REPO_ROOT"
[[ "$_port_root" == */incredible_auto_dev ]] && _port_root="${_port_root%/incredible_auto_dev}"
_offset=$(printf '%s' "$_port_root" | sha1sum | cut -c1-4)
_offset=$((16#$_offset % 1000))
PORT="${CHAIN_BACKEND_PORT:-$((8000 + _offset))}"
FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-$((3000 + _offset))}"

# Tell FastAPI which origins are allowed. Mirrors scripts/dev.sh so QA-spawned
# backends accept requests from the QA-spawned frontend (which uses the
# offset port). Without this, browser tests hit CORS errors and the operator
# has to re-bootstrap manually.
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:${FRONTEND_PORT},http://localhost:3000,http://localhost:3001}"

# Run pending migrations before starting
cd "$REPO_ROOT/apps/backend"
if [[ -d alembic ]]; then
  "$REPO_ROOT/apps/backend/.venv/bin/alembic" upgrade head 2>/dev/null || true
fi

# ops-hardening iter-2 (J-04 remainder) — actually ENFORCE the declared memory cap + malloc-arena cap and
# write a PERSISTENT boot logfile. goal.md's binding note: prior to this iteration none of these three were
# enforced by this script at all (confirmed by a direct read: no ulimit, no env export, no logfile redirect
# anywhere in it) — do not trust reports/perf-budgets.md's or config.yaml's prose claiming otherwise; this
# is where the enforcement actually lives now. Values come from config.yaml via the venv Python (No magic
# numbers — the same `app.config.get_config()` every engine reads).
read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE <<< "$(
  "$REPO_ROOT/apps/backend/.venv/bin/python" -c '
from app.config import get_config
cfg = get_config()
print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
'
)"

# ulimit -v is KiB; config.server.memory_cap_mb is MB. Set on THIS shell BEFORE exec — a ulimit is a
# process attribute inherited across exec() (same PID, new program image), so the cap applies to the
# uvicorn process itself, not just this launcher shell.
ulimit -v $((MEMORY_CAP_MB * 1024))
# iter-27 (anti-goal #8): bound how many independently-fragmenting malloc arenas glibc creates across the
# uvicorn threadpool + parallel backfill workers (the dominant VSZ-fragmentation lever behind the
# iter-26/iter-27 rebuild crash). Exported before exec so glibc reads it at the process's own startup.
export MALLOC_ARENA_MAX="$MALLOC_ARENA_MAX_VALUE"

# A PERSISTENT backend logfile (today uvicorn writes only to the launching terminal, lost the moment that
# terminal closes or the process is backgrounded). One fixed, repo-relative path — `logs/` is already
# gitignored — so a boot's log survives the launching shell and a crash test can read it afterward. Append
# (not truncate) across restarts so a crash's abrupt ending stays visible in the SAME file the next boot's
# lines are appended to (a real operational history, not a wiped-per-restart snapshot).
LOG_DIR="$REPO_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/backend.log"
{
  echo ""
  echo "=== start-backend.sh: launching at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "    port=$PORT memory_cap_mb=$MEMORY_CAP_MB malloc_arena_max=$MALLOC_ARENA_MAX_VALUE"
} >> "$LOG_FILE"

# ==== HOST-GUARD (goal.md AG-10) — DO NOT REMOVE OR WEAKEN ==========================================
# ops-hardening iter-9: apply this host's declared CPU-affinity mask + BLAS/OMP/numexpr thread caps to
# the launched uvicorn process, additive to the ulimit/MALLOC_ARENA_MAX enforcement above (never a
# replacement for it). Absent file or HOST_GUARD_ENABLED=0 -> zero behavior change — host-guard stays
# fully project-neutral per its own header contract (project-extensions/host-guard/host-guard.env).
# Every value below comes from that file; no magic numbers here. Stripping this block is a REGRESSION
# regardless of test outcome (goal.md AG-10) — the caps are a physical hardware constraint (two instant
# hard resets under all-core vectorized ingest bursts, 2026-07-20/21), not a perf knob.
# HOST_GUARD_ENV_FILE lets tests point at a scratch copy (to exercise the absent/disabled branches
# without ever touching the real, safety-critical committed file) — unset in every real launch, so
# production always resolves to the committed path below.
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
    echo "    host-guard: cpu_list=$HOST_GUARD_CPU_LIST blas_threads=$HOST_GUARD_BLAS_THREADS" >> "$LOG_FILE"
  fi
fi
# ==== end HOST-GUARD =================================================================================

exec "${HOST_GUARD_CMD_PREFIX[@]}" "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --app-dir "$REPO_ROOT/apps/backend" \
  >> "$LOG_FILE" 2>&1
