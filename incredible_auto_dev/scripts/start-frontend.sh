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
# ops-hardening iter-77 AUDIT FIX — provenance marker for "this launcher produced the build now on
# disk". WHY: the staleness check below compares SOURCE MTIMES against BUILD_ID, which cannot see that
# the build itself was produced OUT OF BAND (a bare `npx next build` in apps/frontend — the exact
# command this iteration's own dev handoff and QA report each record running as a verification step).
# Such a build carries NO `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` (this script exports them above;
# a bare `next build` does not), so Next bakes the client fallback `http://localhost:8000` into the
# bundle instead of this project's deterministic backend port — every page then renders the global
# "Backend unavailable" state while the backend is perfectly healthy. Reproduced live during the
# iter-77 audit: the tree's `.next` (built out of band) served that state to every fresh browser
# session, this script logged "build is current ... skipping rebuild" over it, and the iteration's own
# demo lane soft-failed all 7 steps against it; a rebuild through THIS script fixed it outright.
# The marker is written INSIDE the dist dir, so any out-of-band `next build` (which rewrites the dist
# dir and always mints a fresh BUILD_ID) invalidates it two ways over: the file is gone, or its
# recorded build id no longer matches. A launcher-produced build always matches, so an ordinary
# sequential restart still skips the rebuild exactly as before.
# SCOPE NOTE (deliberate, not an oversight): the gate compares ONLY provenance + build id, not the
# recorded api_url/api_port below. Gating on those too would make two CONCURRENT invocations that
# differ only in backend port (`test_concurrent_invocations_never_serve_partial_build`'s fixture)
# rebuild over each other's live dist dir — the very race the build lock above closes. The values are
# recorded for diagnosis and can be promoted into the gate once that fixture pins one backend port.
# ROUND-2 UPDATE: that promotion happened, without pinning the fixture — `_bundle_targets_configured_
# backend` below checks the EMITTED BUNDLES (the ground truth, not this recorded value) and skips the
# rebuild when another live server owns the dist dir, so the concurrent-invocation case stays safe.
BUILD_ENV_FILE="$DIST_DIR/.trendora-launch-build"

# ops-hardening iter-77 AUDIT FIX #2 (finding B2) — "who is SERVING this dist dir right now" marker.
# Written immediately before this script `exec`s `next start`, so the pid it records IS the serving
# process (exec keeps $$). `apps/frontend/next.config.mjs`'s build guard reads it and REFUSES any
# non-launcher `next build` targeting a dist dir a live server is serving — the second half of B1 (a
# foreign build tearing a running server mid-round, which is how iter-77's own demo lane captured five
# consecutive full-page crash frames). Self-invalidating: a marker whose pid is gone reads as "nothing is
# serving", so a hard-killed server never blocks a later build.
SERVING_MARKER_FILE="$DIST_DIR/.trendora-serving"

_write_launch_build_marker() {
  {
    printf 'launcher=start-frontend.sh\n'
    printf 'build_id=%s\n' "$(cat "$BUILD_ID_FILE" 2>/dev/null || true)"
    printf 'api_url=%s\n' "${NEXT_PUBLIC_API_URL}"
    printf 'api_port=%s\n' "${NEXT_PUBLIC_API_PORT}"
  } >"$BUILD_ENV_FILE"
}

_write_serving_marker() {
  {
    printf 'pid=%s\n' "$$"
    printf 'port=%s\n' "$FRONTEND_PORT"
    printf 'dist=%s\n' "$DIST_DIR"
    printf 'started_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >"$SERVING_MARKER_FILE"
}

# True iff some OTHER live process is currently serving this dist dir (per its serving marker).
_dist_dir_has_live_server() {
  [[ -f "$SERVING_MARKER_FILE" ]] || return 1
  local pid
  pid="$(grep -m1 '^pid=' "$SERVING_MARKER_FILE" 2>/dev/null | cut -d= -f2)"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  [[ "$pid" != "$$" ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  # Guard against PID reuse: the recorded pid must still look like a Node/Next server process.
  tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | grep -qE '(^|[ /])(next|npx|node|taskset)( |$)'
}

# ops-hardening iter-77 AUDIT FIX #3 (finding B3 — "the shipped root cause was never instrumented").
# The concrete failure this DETECTS (rather than reasons about): the bundle on disk was built for a
# DIFFERENT backend than this launch is configured for, so every page renders "Backend unavailable"
# while the backend is healthy. Next inlines NEXT_PUBLIC_API_URL as a literal at build time
# (`lib/api.ts`'s CONFIGURED_API_BASE), so its presence in the emitted client/server bundles is a direct,
# checkable fact — exactly the `grep -rl "localhost:<port>" .next` the iter-77 audit had to run by hand
# after the fact. Cheap (a grep over the emitted chunks) and runs on EVERY launch, so this class of
# breakage now surfaces at startup in the launcher's own log instead of hours later in forensics.
_bundle_targets_configured_backend() {
  [[ -n "${NEXT_PUBLIC_API_URL:-}" ]] || return 0
  grep -rqF "$NEXT_PUBLIC_API_URL" "$DIST_DIR/static" "$DIST_DIR/server" 2>/dev/null
}

# True iff the build currently on disk is one THIS launcher produced (marker present AND its recorded
# build id is the one on disk right now).
_launch_build_marker_matches() {
  [[ -f "$BUILD_ENV_FILE" ]] || return 1
  local recorded current
  recorded="$(grep -m1 '^build_id=' "$BUILD_ENV_FILE" 2>/dev/null || true)"
  current="build_id=$(cat "$BUILD_ID_FILE" 2>/dev/null || true)"
  [[ -n "$recorded" && "$recorded" == "$current" ]]
}

# ==== BUILD LOCK (ops-hardening iter-77, closes the iter-72/c intermittent asset-less-frontend
# defect) — serialize the staleness-check -> `next build` decision per dist-dir ===================
# Root cause confirmed by direct code reading (this iteration's instrumentation target, per the
# assumption-ledger's iter-77 entry): this script had NO lock against a SECOND concurrent invocation
# targeting the SAME `$DIST_DIR`. Two overlapping invocations (e.g. an orchestration script restarting
# the frontend while a still-running prior invocation's `next build` has not yet finished) would both
# see the build as stale and both run `next build` concurrently against the SAME output directory —
# `next build` is not safe for two concurrent writers into one dist dir (webpack/Next both write many
# intermediate files throughout the build, not atomically, and there is no coordination between two
# independent `next build` processes). Whichever invocation's build happens to finish (or appear to
# finish) first `exec`s into `next start` and begins serving while the OTHER invocation's build may
# still be mid-write to the exact same files — a client request landing in that window can be served a
# torn mix of two builds' output (missing/corrupt static chunks, a manifest that does not match what is
# actually on disk), which is exactly the asset-less/unstyled page symptom this closes.
#
# Fix: an exclusive `flock` keyed to the resolved dist-dir path wraps the ENTIRE staleness-check ->
# build decision below. Whichever invocation acquires the lock first performs (or skips) its build to
# completion before releasing it; every other concurrent invocation targeting the SAME dist dir blocks
# until then, and its OWN staleness check (deliberately re-run AFTER acquiring the lock, not before)
# then correctly observes a just-completed, fully-written build and skips the redundant/racing rebuild.
# The lock is released before the final `exec ... next start` below — serving needs no cross-invocation
# exclusivity once the build on disk is known-consistent, so a legitimate sequential restart is never
# blocked by a stale lock hold. `TRENDORA_FRONTEND_LOCK_DIR` is a test-only seam (defaults to `/tmp`,
# never changed in a real launch) so tests can inspect lock files without touching a shared path.
LOCK_DIR="${TRENDORA_FRONTEND_LOCK_DIR:-/tmp}"
mkdir -p "$LOCK_DIR"
_dist_dir_abs="$REPO_ROOT/apps/frontend/$DIST_DIR"
BUILD_LOCK_FILE="$LOCK_DIR/trendora-frontend-build-$(printf '%s' "$_dist_dir_abs" | sha1sum | cut -c1-16).lock"
exec {BUILD_LOCK_FD}>"$BUILD_LOCK_FILE"
if ! flock -n "$BUILD_LOCK_FD"; then
  echo "[start-frontend.sh] another invocation is already building/checking '$DIST_DIR' —" \
       "waiting for its build lock ($BUILD_LOCK_FILE) before proceeding..." >&2
  flock "$BUILD_LOCK_FD"
fi
echo "[start-frontend.sh] acquired build lock for '$DIST_DIR'" >&2
# ==== end BUILD LOCK acquisition ======================================================================

_build_is_stale_or_missing() {
  # Missing entirely (never built, or a `next dev`-mode `.next` with no BUILD_ID at all) -> stale.
  # A bare directory-existence check would wrongly treat a dev-mode `.next` as a current prod build.
  if [[ ! -f "$BUILD_ID_FILE" ]]; then
    return 0
  fi
  # Built out of band (no launcher marker, or a marker for a different BUILD_ID) -> stale, whatever the
  # source mtimes say: its baked NEXT_PUBLIC_* config is unknown and, for a bare `npx next build`,
  # provably wrong for this project's ports (see BUILD_ENV_FILE's comment above).
  if ! _launch_build_marker_matches; then
    echo "[start-frontend.sh] '$DIST_DIR' was not built by this launcher (no matching build marker) —" \
         "treating it as stale so its baked NEXT_PUBLIC_API_URL cannot silently point at the wrong backend." >&2
    return 0
  fi
  # Built for a DIFFERENT backend than this launch is configured for -> stale, whatever the mtimes say
  # (see _bundle_targets_configured_backend above). The one exception: another live server is already
  # serving this dist dir, in which case rebuilding would tear ITS assets mid-flight — the exact harm
  # finding B2 names — so we warn loudly and serve what is there instead. (This is the audit's own
  # "can be promoted into the gate" note on the launch marker, promoted with that safety carve-out
  # rather than by pinning the concurrent-launch fixture to one backend port.)
  if ! _bundle_targets_configured_backend; then
    if _dist_dir_has_live_server; then
      echo "[start-frontend.sh] WARNING: the build in '$DIST_DIR' does not reference this launch's" \
           "backend ($NEXT_PUBLIC_API_URL), but another live server is serving that directory —" \
           "serving it as-is rather than tearing that server's assets. Pages may show 'Backend" \
           "unavailable'; stop the other server and relaunch to rebuild." >&2
    else
      echo "[start-frontend.sh] '$DIST_DIR' was built for a different backend (no reference to" \
           "$NEXT_PUBLIC_API_URL in its emitted bundles) — treating it as stale so the served app can" \
           "actually reach this launch's backend." >&2
      return 0
    fi
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
  # TRENDORA_LAUNCH_BUILD tells next.config.mjs's build guard that THIS build is the launcher's own: it
  # holds the per-dist-dir build lock, exports NEXT_PUBLIC_API_URL/_PORT (above), and is the process that
  # will serve the result. Every other `next build` targeting a live-served dist dir is refused there.
  if ! TRENDORA_LAUNCH_BUILD=1 "${HOST_GUARD_CMD_PREFIX[@]}" npx next build; then
    echo "[start-frontend.sh] next build FAILED (see output above) — refusing to fall back to" \
         "'next dev' or serve a stale build." >&2
    flock -u "$BUILD_LOCK_FD"
    exit 1
  fi
  # Record that THIS launcher produced the build now on disk (see BUILD_ENV_FILE above). Written under
  # the build lock, after a successful build, so a concurrent invocation's post-lock staleness re-check
  # observes a fully-written build AND its marker together.
  _write_launch_build_marker
else
  echo "[start-frontend.sh] existing '$DIST_DIR' build is current relative to sources — skipping rebuild." >&2
fi

# Claim the dist dir as SERVED by this process (pid survives the `exec` below) BEFORE releasing the
# build lock — a concurrent invocation that acquires the lock next then reliably observes the claim
# instead of racing it. See SERVING_MARKER_FILE above.
_write_serving_marker

# Release the build lock — the dist dir is now known-consistent on disk; serving it needs no
# cross-invocation exclusivity (see the lock-acquisition comment above).
flock -u "$BUILD_LOCK_FD"
exec {BUILD_LOCK_FD}>&-
# ==== end build-if-stale =============================================================================

exec "${HOST_GUARD_CMD_PREFIX[@]}" npx next start -p "$FRONTEND_PORT"
