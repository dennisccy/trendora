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

# iter-42 (J-100) — bounded-resource ops guards. EVERY bound is read from config (anti-goal: No magic
# numbers — no concurrency/timeout/memory literal lives in this script). The venv python prints the four
# tunables from `config.server`; env overrides (CHAIN_SERVER_*) win for an operator-tuned run. Under
# concurrent dashboard / goal-mode UI-test load these keep the backend responsive + memory-bounded: the
# uvicorn --limit-concurrency cap + the single-flight coverage cache mean N parallel /api/data probes cost
# ~one heavy compute (never N connection-holding resolves that exhaust the pool), and the ulimit -v cap
# OOM-kills ONE runaway process rather than swap-thrashing the whole VM.
read -r CFG_LIMIT_CONCURRENCY CFG_KEEP_ALIVE CFG_GRACEFUL CFG_MEMORY_CAP_MB CFG_MALLOC_ARENA_MAX < <(
  "$REPO_ROOT/apps/backend/.venv/bin/python" - <<'PY'
from app.config import load_config
s = load_config().server
print(s.limit_concurrency, s.timeout_keep_alive_seconds, s.graceful_timeout_seconds, s.memory_cap_mb, s.malloc_arena_max)
PY
)
LIMIT_CONCURRENCY="${CHAIN_SERVER_LIMIT_CONCURRENCY:-$CFG_LIMIT_CONCURRENCY}"
KEEP_ALIVE="${CHAIN_SERVER_KEEP_ALIVE:-$CFG_KEEP_ALIVE}"
GRACEFUL="${CHAIN_SERVER_GRACEFUL_TIMEOUT:-$CFG_GRACEFUL}"
MEMORY_CAP_MB="${CHAIN_SERVER_MEMORY_CAP_MB:-$CFG_MEMORY_CAP_MB}"
MALLOC_ARENA_MAX_CFG="${CHAIN_SERVER_MALLOC_ARENA_MAX:-$CFG_MALLOC_ARENA_MAX}"

# iter-27 (anti-goal #8) — cap glibc's per-thread malloc arenas BEFORE any allocation (the env var is read
# at allocator init). glibc defaults to up to 8*ncpus arenas (128 on a 16-core host); each retains its own
# freed-but-unreturned address space, so across the uvicorn threadpool + the parallel backfill workers VSZ
# fragments across many arenas and a SECOND full-universe rebuild pins the ulimit -v ceiling (the reproduced
# iter-26/iter-27 crash). Capping the arena count bounds that fragmentation — the dominant VSZ lever — with
# byte-identical outputs (it only changes allocator layout). Config-driven (No magic numbers); paired with
# the per-job gc.collect()+malloc_trim in data_manager that returns freed pages to the OS between rebuilds.
if [[ -n "$MALLOC_ARENA_MAX_CFG" && "$MALLOC_ARENA_MAX_CFG" -gt 0 ]]; then
  export MALLOC_ARENA_MAX="$MALLOC_ARENA_MAX_CFG"
fi

# Per-process virtual-memory cap (ulimit -v takes KiB). Bounds THIS process tree's address space so a
# pathological N-copy memory spike is OOM-killed as ONE backend process, never a VM-wide swap freeze.
# `ulimit -v` only LOWERS a soft limit (it cannot exceed a stricter inherited hard cap); if the host
# already enforces a lower cap we keep it (|| true) rather than fail the start.
if [[ -n "$MEMORY_CAP_MB" && "$MEMORY_CAP_MB" -gt 0 ]]; then
  ulimit -v $(( MEMORY_CAP_MB * 1024 )) 2>/dev/null || true
fi

exec "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --app-dir "$REPO_ROOT/apps/backend" \
  --limit-concurrency "$LIMIT_CONCURRENCY" \
  --timeout-keep-alive "$KEEP_ALIVE" \
  --timeout-graceful-shutdown "$GRACEFUL"
