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

exec "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --app-dir "$REPO_ROOT/apps/backend" \
  >> "$LOG_FILE" 2>&1
