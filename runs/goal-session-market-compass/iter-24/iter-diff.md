# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index bc5e3f59..a332b2d3 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -96,6 +96,19 @@ mkdir -p "$REPO_ROOT/docs/handoffs"
 # expensive developer build. Any doubt → the step re-runs (today's behavior).
 ITER_DIR="$(goal_iter_dir "$ITER_NAME" 2>/dev/null || true)"
 
+# ── Backend/frontend launch-context lock (iter-24 fix) ────────────────────
+# Resolve BACKEND_START_CMD/FRONTEND_START_CMD from CHAIN_START_BACKEND_CMD/
+# CHAIN_START_FRONTEND_CMD (or the plain scripts/start-*.sh default) EXACTLY
+# ONCE for this run, as early as possible — before any backend can start —
+# and lock the result (lib/common.sh::goal_iter_lock_backend_launch_context).
+# run_browser_qa_boot_and_replay below reads the locked value instead of
+# re-deriving it, and ensure_services_running's own guard refuses any backend
+# launch whose QA_BACKEND_START_CMD has drifted from what was locked here —
+# closing the gap that let iteration 23's routine regression re-test silently
+# boot the canonical database while a disposable-clone override was in force
+# for the same run (goal.md OWNER RULING item 3).
+goal_iter_lock_backend_launch_context "$ITER_DIR"
+
 # ── TOKEN-7: pre-baked review packet ──────────────────────────────────────
 # Built once the developer settles — BEFORE the SPEED-2/3 fork spawn points
 # (the packet's stat tail reads tracked runs/ paths, and a forked lane
@@ -251,14 +264,14 @@ run_browser_qa_boot_and_replay() {
 QA_BACKEND_LOG=$(_qa_log_path "goal-iter-backend")
 QA_FRONTEND_LOG=$(_qa_log_path "goal-iter-frontend")
 
-BACKEND_START_CMD="${CHAIN_START_BACKEND_CMD:-}"
-FRONTEND_START_CMD="${CHAIN_START_FRONTEND_CMD:-}"
-if [[ -z "$BACKEND_START_CMD" && -f "$REPO_ROOT/scripts/start-backend.sh" ]]; then
-  BACKEND_START_CMD="bash $REPO_ROOT/scripts/start-backend.sh"
-fi
-if [[ -z "$FRONTEND_START_CMD" && -f "$REPO_ROOT/scripts/start-frontend.sh" ]]; then
-  FRONTEND_START_CMD="bash $REPO_ROOT/scripts/start-frontend.sh"
-fi
+# iter-24 fix: reuse the launch command locked ONCE at the top of this script
+# (goal_iter_lock_backend_launch_context) instead of independently re-deriving
+# it from CHAIN_START_BACKEND_CMD/CHAIN_START_FRONTEND_CMD here every time this
+# function runs (inline, or inside the SPEED-2/3 fork) — that independent
+# re-derivation is exactly what let an override established elsewhere in the
+# same run go unhonored (iteration 23's canonical-DB boot).
+BACKEND_START_CMD="${GOAL_ITER_BACKEND_LAUNCH_CMD:-}"
+FRONTEND_START_CMD="${GOAL_ITER_FRONTEND_LAUNCH_CMD:-}"
 
 _BACKEND_PORT="${CHAIN_BACKEND_PORT:-8000}"
 _FRONTEND_PORT="${CHAIN_FRONTEND_PORT:-3000}"
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index feba8945..ec3f428d 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -1432,6 +1432,87 @@ sys.exit(1)
 PYEOF
 }
 
+# ── Backend/frontend launch-context lock (iter-24 fix) ────────────────────
+# Root cause (goal.md OWNER RULING item 3, iter-23 eval "The violation,
+# precisely"): goal-iter-lean.sh used to resolve BACKEND_START_CMD from
+# CHAIN_START_BACKEND_CMD independently, INSIDE run_browser_qa_boot_and_replay,
+# every time that function ran. A disposable-clone/alternate-DB override
+# supplied for one part of an iteration was never guaranteed to reach every
+# other backend-launch point in the SAME run (the deterministic-replay lane's
+# routine J-01/J-04 re-test silently fell back to `bash scripts/start-backend.sh`
+# with no TRENDORA_CONFIG, booting the protected canonical database and writing
+# 10 rows into it).
+#
+# The fix: resolve the launch commands EXACTLY ONCE per goal-iter-lean.sh
+# invocation, as early as possible (before any backend can start), and lock
+# the result into GOAL_ITER_BACKEND_LAUNCH_CMD / GOAL_ITER_FRONTEND_LAUNCH_CMD
+# (exported — inherited by the SPEED-2/3 forked subshells and by the
+# quota-retry pre-hook, since all of them are subshells/callbacks of THIS
+# process, never a fresh process that could lose the export) plus a
+# per-iteration sentinel file (inspectable/auditable evidence of what was
+# locked). Every backend-launch call site must resolve from this locked value
+# — never re-derive independently. `ensure_services_running`'s own guard
+# (below) enforces that: it is the single chokepoint every self-boot path
+# (initial boot, REL-5 restart, REL-14 preflight retry, the quota-retry
+# pre-hook) already funnels through, so checking there closes the gap for all
+# of them at once instead of patching each call site separately.
+#
+# A caller that never locks a context (every script besides goal-iter-lean.sh
+# — qa-phase.sh, browser-qa-phase.sh, demo-phase.sh, run-phase.sh,
+# run-benchmark.sh) leaves GOAL_ITER_BACKEND_LAUNCH_CMD unset, so the guard is
+# a complete no-op for them — this fix changes nothing outside goal-iter-lean.sh
+# (owner ruling item 3's explicit scope; a broader refactor is NOT authorized).
+goal_iter_lock_backend_launch_context() {
+  local iter_dir="${1:-}"
+  local backend_cmd="${CHAIN_START_BACKEND_CMD:-}"
+  local frontend_cmd="${CHAIN_START_FRONTEND_CMD:-}"
+  local override_active="no"
+  [[ -n "${CHAIN_START_BACKEND_CMD:-}" ]] && override_active="yes"
+  if [[ -z "$backend_cmd" && -n "${REPO_ROOT:-}" && -f "$REPO_ROOT/scripts/start-backend.sh" ]]; then
+    backend_cmd="bash $REPO_ROOT/scripts/start-backend.sh"
+  fi
+  if [[ -z "$frontend_cmd" && -n "${REPO_ROOT:-}" && -f "$REPO_ROOT/scripts/start-frontend.sh" ]]; then
+    frontend_cmd="bash $REPO_ROOT/scripts/start-frontend.sh"
+  fi
+  export GOAL_ITER_BACKEND_LAUNCH_CMD="$backend_cmd"
+  export GOAL_ITER_FRONTEND_LAUNCH_CMD="$frontend_cmd"
+  if [[ -n "$iter_dir" ]]; then
+    mkdir -p "$iter_dir" 2>/dev/null || true
+    { printf 'LOCKED_AT=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
+      printf 'BACKEND_START_CMD=%q\n'  "$backend_cmd"
+      printf 'FRONTEND_START_CMD=%q\n' "$frontend_cmd"
+      printf 'OVERRIDE_ACTIVE=%s\n' "$override_active"
+    } > "$iter_dir/.backend-launch-context.tmp.$$" 2>/dev/null \
+      && mv -f "$iter_dir/.backend-launch-context.tmp.$$" "$iter_dir/.backend-launch-context" 2>/dev/null \
+      || rm -f "$iter_dir/.backend-launch-context.tmp.$$" 2>/dev/null || true
+  fi
+  echo "[goal-iter-lean] Backend launch context locked for this run (override active: $override_active)." >&2
+}
+
+# backend_launch_context_refuse <operation> [detail]
+# FAIL CLOSED, same shape as maintenance_isolation_refuse above: a backend
+# launch whose QA_BACKEND_START_CMD has drifted from the context
+# goal_iter_lock_backend_launch_context locked at iteration start is refused —
+# loudly, recorded, and BEFORE any backend process is spawned — rather than
+# silently proceeding with whatever command this call site happened to end up
+# with (iteration 23's exact failure mode).
+backend_launch_context_refuse() {
+  local op="${1:-unknown-operation}" detail="${2:-}"
+  echo "[backend-launch-context] REFUSING to start a backend whose launch command does not match the context locked at iteration start: ${op}${detail:+ — $detail}" >&2
+  echo "[backend-launch-context] Failing closed (iter-24 fix) instead of silently falling back to a different launch command — see goal_iter_lock_backend_launch_context in lib/common.sh." >&2
+  local dir="${ITER_DIR:-}"
+  if [[ -n "$dir" ]]; then
+    mkdir -p "$dir" 2>/dev/null || true
+    printf '%s\toperation=%s\tdetail=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$op" "$detail" \
+      >> "$dir/backend-launch-context-refusals" 2>/dev/null || true
+  fi
+  if declare -F record_telemetry_event >/dev/null 2>&1; then
+    record_telemetry_event "backend_launch_context_refused" \
+      "$(printf '{"operation":"%s","detail":"%s"}' "$op" "$detail")" 2>/dev/null || true
+  fi
+  return 1
+}
+
 # ── Idempotent service bootstrap (shared by qa-phase.sh and browser-qa-phase.sh) ──
 #
 # Starts the backend (and optionally frontend) if they are not already running.
@@ -1476,17 +1557,36 @@ ensure_services_running() {
 
   # Backend: 2 attempts × 45s = the same 90s ceiling as the previous single shot,
   # but now re-SPAWNS on failure and reclaims a stale/drifted uvicorn by cwd.
-  if [[ -n "${QA_BACKEND_HEALTH_URL:-}" && -n "${QA_BACKEND_START_CMD:-}" ]]; then
-    # Backend ready_re is permissive: a 404/405 on /health still proves uvicorn is
-    # listening and routing. Projects that namespace routes (e.g. /api/health) would
-    # otherwise be wrongly judged DOWN and torn down on every attempt. QA_BACKEND_UP
-    # is advisory only (no verdict gates on it), so "reachable" is the right bar.
-    if _start_service_with_retries "backend" \
-         "$QA_BACKEND_HEALTH_URL" "$QA_BACKEND_START_CMD" "${QA_BACKEND_LOG:-/dev/null}" \
-         45 2 QA_BACKEND_LOG_TAIL "kill_stale_backend_server" '^[1-5][0-9][0-9]$'; then
-      export QA_BACKEND_UP="yes"
-    else
+  if [[ -n "${QA_BACKEND_HEALTH_URL:-}" ]]; then
+    # Launch-context guard (iter-24 fix): when goal-iter-lean.sh has locked a
+    # backend launch command for this run (GOAL_ITER_BACKEND_LAUNCH_CMD, set by
+    # goal_iter_lock_backend_launch_context), THIS call's QA_BACKEND_START_CMD
+    # must be byte-identical to it — whether the mismatch is a different
+    # command or empty/unset (a call site that lost the override entirely).
+    # Refuse and return BEFORE _start_service_with_retries ever runs: no
+    # process is spawned and no log file is created for a refused attempt.
+    # A caller that never locked a context (every script besides
+    # goal-iter-lean.sh) leaves GOAL_ITER_BACKEND_LAUNCH_CMD unset, so this is
+    # a no-op there — unchanged behavior outside goal-iter-lean.sh.
+    if [[ -n "${GOAL_ITER_BACKEND_LAUNCH_CMD:-}" \
+          && "${QA_BACKEND_START_CMD:-}" != "${GOAL_ITER_BACKEND_LAUNCH_CMD}" ]]; then
       export QA_BACKEND_UP="no"
+      export QA_BACKEND_LOG_TAIL="refused: backend launch command drifted from the context locked at iteration start (locked: ${GOAL_ITER_BACKEND_LAUNCH_CMD}; this call: ${QA_BACKEND_START_CMD:-<empty>})"
+      backend_launch_context_refuse "ensure_services_running/backend" "$QA_BACKEND_LOG_TAIL"
+      return 1
+    fi
+    if [[ -n "${QA_BACKEND_START_CMD:-}" ]]; then
+      # Backend ready_re is permissive: a 404/405 on /health still proves uvicorn is
+      # listening and routing. Projects that namespace routes (e.g. /api/health) would
+      # otherwise be wrongly judged DOWN and torn down on every attempt. QA_BACKEND_UP
+      # is advisory only (no verdict gates on it), so "reachable" is the right bar.
+      if _start_service_with_retries "backend" \
+           "$QA_BACKEND_HEALTH_URL" "$QA_BACKEND_START_CMD" "${QA_BACKEND_LOG:-/dev/null}" \
+           45 2 QA_BACKEND_LOG_TAIL "kill_stale_backend_server" '^[1-5][0-9][0-9]$'; then
+        export QA_BACKEND_UP="yes"
+      else
+        export QA_BACKEND_UP="no"
+      fi
     fi
   fi
 
@@ -1528,8 +1628,12 @@ ensure_services_running() {
     fi
   fi
 
-  # ALWAYS 0: the five bare call sites run under `set -e`. Failure is surfaced
-  # via QA_*_UP / QA_*_LOG_TAIL, never a non-zero return.
+  # ALWAYS 0 for an ordinary boot failure: the five bare call sites run under
+  # `set -e`. Failure is surfaced via QA_*_UP / QA_*_LOG_TAIL, never a
+  # non-zero return. The two FAIL-CLOSED refusals above (maintenance
+  # isolation; a backend launch command that drifted from the context locked
+  # at iteration start) are the deliberate exceptions — those return 1
+  # specifically so `set -e` aborts the caller instead of a silent boot.
   return 0
 }
 
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 6312e036..c998a8f5 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -184,7 +184,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh tests/automation/test-output-style.sh tests/automation/test-review-verdict-event.sh tests/automation/test-full-depth-required.sh tests/automation/test-maintenance-isolation.sh; do
+for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh tests/automation/test-output-style.sh tests/automation/test-review-verdict-event.sh tests/automation/test-full-depth-required.sh tests/automation/test-maintenance-isolation.sh tests/automation/test-backend-launch-context.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
diff --git a/incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh b/incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh
index 7988f629..25fe0d39 100644
--- a/incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh
+++ b/incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh
@@ -370,6 +370,11 @@ grep -q "Forking browser-qa service boot" "$WORK/lean-A.log" \
 # journey-history, so the builder fail-safes to the full goal text, but the
 # slice FILES still land). state/golden-gaps added — SPEED-23 persists the
 # golden-coverage gap (J-02 passes via the LLM lane with no golden here).
+# 2026-08-27: iter-1/.backend-launch-context added — the iter-24 fix
+# (goal_iter_lock_backend_launch_context, lib/common.sh) locks the resolved
+# backend/frontend launch command into this sentinel file ONCE per run,
+# unconditionally, before the SPEED-2/3 fork spawn points — so it lands in
+# every mode's tree (off, replay, full alike).
 EXPECTED_TREE="./docs/goal.md
 ./docs/handoffs/${ITER}-dev.md
 ./docs/phases/${ITER}.md
@@ -377,6 +382,7 @@ EXPECTED_TREE="./docs/goal.md
 ./reports/phase-${ITER}-ui-test-results.llm.md
 ./reports/phase-${ITER}-ui-test-results.md
 ./reports/reviews/${ITER}-review.md
+./runs/goal-session-pbtest/iter-1/.backend-launch-context
 ./runs/goal-session-pbtest/iter-1/.steps/browser-qa.done
 ./runs/goal-session-pbtest/iter-1/.steps/developer.done
 ./runs/goal-session-pbtest/iter-1/.steps/review-1.done
diff --git a/incredible_auto_dev/tests/automation/test-backend-launch-context.sh b/incredible_auto_dev/tests/automation/test-backend-launch-context.sh
new file mode 100644
index 00000000..6d30d70d
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-backend-launch-context.sh
@@ -0,0 +1,251 @@
+#!/usr/bin/env bash
+# test-backend-launch-context.sh — iter-24 fix: goal-iter-lean.sh must make every backend-launch
+# call site (initial boot, SPEED-2/3 forked boot, REL-5 restart-after-failure, REL-14 preflight
+# retry, the quota-retry pre-hook) preserve the SAME CHAIN_START_BACKEND_CMD/TRENDORA_CONFIG
+# override an iteration established, never independently re-derive the bare
+# `bash scripts/start-backend.sh` default once an override is in force, and fail closed BEFORE any
+# backend process spawns when the expected override is missing/mismatched.
+#
+# Root cause reproduced here (goal.md OWNER RULING item 3; iter-23 eval "The violation,
+# precisely"): `goal-iter-lean.sh:256-257` (pre-fix) resolved BACKEND_START_CMD from
+# CHAIN_START_BACKEND_CMD INDEPENDENTLY inside run_browser_qa_boot_and_replay every time that
+# function ran, with no cross-check against what an earlier launch point in the same run had
+# already established. A disposable-clone override active for one part of iteration 23 never
+# reached the routine J-01/J-04 regression re-test in the SAME run, which silently fell back to the
+# bare default and booted the protected canonical database.
+#
+# The fix (lib/common.sh): goal_iter_lock_backend_launch_context resolves the launch command ONCE
+# per run and locks it into GOAL_ITER_BACKEND_LAUNCH_CMD; ensure_services_running -- the single
+# chokepoint every self-boot path (initial boot, REL-5, REL-14, the quota-retry pre-hook) already
+# funnels through -- refuses (fail closed, before _start_service_with_retries ever runs) when a
+# call's QA_BACKEND_START_CMD has drifted from that locked value.
+#
+# Per iter-22b's lesson, this test exercises the REAL lib/common.sh code (sourced, not
+# reimplemented) and stubs only its callee `_start_service_with_retries` (the function that would
+# actually spawn a process and open a log file) as a SPY -- same technique
+# tests/automation/test-frontend-restart-reprobe.sh already uses to prove
+# ensure_services_running's OWN orchestration logic. The stub start commands used below
+# (`echo ...`) never touch a real port, process, or file -- and never reference
+# apps/backend/data/trendora.db -- so this test cannot boot or write to the canonical database
+# (TC-9; the NOTES section of docs/phases/goal-market-compass-iter-24.md explicitly permits an
+# inert stub command for a pure launch-context unit test).
+#
+# Offline, no model, no real network/process/service, <1s.
+#
+# To reproduce iteration 23's defect against the PRE-fix tree (TC-5) and confirm this same test
+# passes against the fixed tree (TC-6), see the dev handoff
+# (docs/handoffs/goal-market-compass-iter-24-dev.md) for the exact `git stash` / restore commands
+# and their outputs.
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+CM="$REPO_ROOT/scripts/automation/lib/common.sh"
+GIL="$REPO_ROOT/scripts/automation/goal-iter-lean.sh"
+
+PASS=0
+FAIL=0
+assert() {
+  local label="$1" result="$2"
+  if [[ "$result" == "pass" ]]; then
+    echo "  PASS  $label"; PASS=$((PASS+1))
+  else
+    echo "  FAIL  $label"; FAIL=$((FAIL+1))
+  fi
+}
+
+WORK="$(mktemp -d)"
+trap 'rm -rf "$WORK"' EXIT
+
+[[ -f "$CM" ]] && bash -n "$CM" && assert "lib/common.sh exists and parses (bash -n)" pass \
+  || { assert "lib/common.sh exists and parses (bash -n)" fail; echo "RESULT: $PASS passed, $((FAIL)) failed"; exit 1; }
+[[ -f "$GIL" ]] && bash -n "$GIL" && assert "goal-iter-lean.sh exists and parses (bash -n)" pass \
+  || { assert "goal-iter-lean.sh exists and parses (bash -n)" fail; echo "RESULT: $PASS passed, $((FAIL)) failed"; exit 1; }
+
+OVERRIDE_CMD="echo stub-disposable-clone-backend"
+BARE_DEFAULT_CMD="bash $REPO_ROOT/scripts/start-backend.sh"
+
+# ── A. TC-1/TC-3: an override locked at run start is reused BYTE-IDENTICAL by a later launch
+#      point (simulating REL-5's restart-after-failure / REL-14's preflight retry, both of which
+#      call only ensure_services_running -- see lib/replay-lane.sh) -- never silently swapped for
+#      the bare default.
+outA="$(
+  (
+    set -euo pipefail
+    # shellcheck source=/dev/null
+    source "$CM"
+    ITER_DIR="$WORK/iterA"
+    export CHAIN_START_BACKEND_CMD="$OVERRIDE_CMD"
+    goal_iter_lock_backend_launch_context "$ITER_DIR"
+    SPY_LOG="$(mktemp)"
+    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
+    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
+    export QA_BACKEND_LOG=/dev/null
+    # Launch point 1: initial boot (mirrors run_browser_qa_boot_and_replay's own assignment,
+    # post-fix: read the locked value, never re-derive).
+    export QA_BACKEND_START_CMD="$GOAL_ITER_BACKEND_LAUNCH_CMD"
+    ensure_services_running
+    echo "RC1=$?"; echo "UP1=$QA_BACKEND_UP"
+    # Launch point 2: a later restart/retry in the SAME run. A caller reusing the locked value
+    # (the fixed goal-iter-lean.sh's only pattern now) resolves to the identical string.
+    export QA_BACKEND_START_CMD="$GOAL_ITER_BACKEND_LAUNCH_CMD"
+    ensure_services_running
+    echo "RC2=$?"; echo "UP2=$QA_BACKEND_UP"
+    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
+    cat "$SPY_LOG"
+  )
+)" || true
+echo "$outA" | grep -q '^UP1=yes$' && echo "$outA" | grep -q '^UP2=yes$' \
+  && assert "TC-1/TC-3: locked override honored on both the initial boot and a later restart" pass \
+  || { assert "TC-1/TC-3: locked override honored on both the initial boot and a later restart" fail; echo "    got: $outA"; }
+echo "$outA" | grep -q '^SPY_CALLS=2$' \
+  && assert "TC-1/TC-3: exactly 2 backend starts attempted (both launch points actually ran)" pass \
+  || { assert "TC-1/TC-3: exactly 2 backend starts attempted (both launch points actually ran)" fail; echo "    got: $outA"; }
+_calls="$(echo "$outA" | grep '^cmd=' | sort -u | wc -l)"
+[[ "$_calls" -eq 1 ]] \
+  && assert "TC-3: the first and later launch commands are byte-identical (zero mismatch)" pass \
+  || { assert "TC-3: the first and later launch commands are byte-identical (zero mismatch)" fail; echo "    got: $outA"; }
+echo "$outA" | grep -qF "cmd=$OVERRIDE_CMD" \
+  && assert "TC-1: the honored command is the override, not the bare default" pass \
+  || { assert "TC-1: the honored command is the override, not the bare default" fail; echo "    got: $outA"; }
+
+# ── B. TC-4 (missing): an override is locked, but a launch point's QA_BACKEND_START_CMD comes in
+#      EMPTY (a call site that lost the override entirely) -- must fail closed, and the callee that
+#      would spawn a process must never be invoked.
+outB="$(
+  (
+    set -euo pipefail
+    source "$CM"
+    ITER_DIR="$WORK/iterB"
+    export CHAIN_START_BACKEND_CMD="$OVERRIDE_CMD"
+    goal_iter_lock_backend_launch_context "$ITER_DIR"
+    SPY_LOG="$(mktemp)"
+    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
+    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
+    export QA_BACKEND_LOG=/dev/null
+    export QA_BACKEND_START_CMD=""   # simulates a call site that lost the override
+    _rc=0
+    ensure_services_running || _rc=$?
+    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"; echo "TAIL=$QA_BACKEND_LOG_TAIL"
+    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
+  )
+)" || true
+echo "$outB" | grep -q '^RC=1$' \
+  && assert "TC-4: a missing-but-expected override fails closed (non-zero return)" pass \
+  || { assert "TC-4: a missing-but-expected override fails closed (non-zero return)" fail; echo "    got: $outB"; }
+echo "$outB" | grep -q '^UP=no$' \
+  && assert "TC-4: QA_BACKEND_UP=no (not a silent success)" pass \
+  || { assert "TC-4: QA_BACKEND_UP=no (not a silent success)" fail; echo "    got: $outB"; }
+echo "$outB" | grep -q '^TAIL=refused:' \
+  && assert "TC-4: an explicit 'refused' error is recorded before any boot attempt" pass \
+  || { assert "TC-4: an explicit 'refused' error is recorded before any boot attempt" fail; echo "    got: $outB"; }
+echo "$outB" | grep -q '^SPY_CALLS=0$' \
+  && assert "TC-4: no backend process is spawned for the refused attempt" pass \
+  || { assert "TC-4: no backend process is spawned for the refused attempt" fail; echo "    got: $outB"; }
+
+# ── C. TC-5/TC-6 reproduction: an override is locked, but a launch point's QA_BACKEND_START_CMD
+#      resolves to the BARE DEFAULT instead (the exact iteration-23 shape -- a call site silently
+#      fell back). Pre-fix: no guard exists, so the callee that would spawn the backend process IS
+#      invoked with the wrong (bare-default) command -- this assertion FAILS against the reverted
+#      diff, proving it reproduces the defect (TC-5), and PASSES against the fix (TC-6).
+outC="$(
+  (
+    set -euo pipefail
+    source "$CM"
+    ITER_DIR="$WORK/iterC"
+    export CHAIN_START_BACKEND_CMD="$OVERRIDE_CMD"
+    goal_iter_lock_backend_launch_context "$ITER_DIR"
+    SPY_LOG="$(mktemp)"
+    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
+    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
+    export QA_BACKEND_LOG=/dev/null
+    export QA_BACKEND_START_CMD="$BARE_DEFAULT_CMD"   # simulates the pre-fix independent re-derivation
+    _rc=0
+    ensure_services_running || _rc=$?
+    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"
+    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
+    cat "$SPY_LOG"
+  )
+)" || true
+echo "$outC" | grep -q '^SPY_CALLS=0$' \
+  && assert "TC-5/TC-6: a launch point that drifted to the bare default is refused, never started" pass \
+  || { assert "TC-5/TC-6: a launch point that drifted to the bare default is refused, never started" fail; echo "    got: $outC"; }
+echo "$outC" | grep -q '^RC=1$' && echo "$outC" | grep -q '^UP=no$' \
+  && assert "TC-5/TC-6: the drift is a hard fail-closed refusal, not a soft skip" pass \
+  || { assert "TC-5/TC-6: the drift is a hard fail-closed refusal, not a soft skip" fail; echo "    got: $outC"; }
+
+# ── D. TC-7: the ordinary no-override case is completely unaffected -- when CHAIN_START_BACKEND_CMD
+#      is unset, the locked value IS the bare default, and every call site using it succeeds exactly
+#      as before this fix.
+outD="$(
+  (
+    set -euo pipefail
+    source "$CM"
+    ITER_DIR="$WORK/iterD"
+    unset CHAIN_START_BACKEND_CMD 2>/dev/null || true
+    goal_iter_lock_backend_launch_context "$ITER_DIR"
+    SPY_LOG="$(mktemp)"
+    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
+    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
+    export QA_BACKEND_LOG=/dev/null
+    export QA_BACKEND_START_CMD="$GOAL_ITER_BACKEND_LAUNCH_CMD"
+    _rc=0
+    ensure_services_running || _rc=$?
+    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"
+    echo "LOCKED=$GOAL_ITER_BACKEND_LAUNCH_CMD"
+  )
+)" || true
+echo "$outD" | grep -q '^RC=0$' && echo "$outD" | grep -q '^UP=yes$' \
+  && assert "TC-7: the unset-override (ordinary) path is unaffected -- no spurious refusal" pass \
+  || { assert "TC-7: the unset-override (ordinary) path is unaffected -- no spurious refusal" fail; echo "    got: $outD"; }
+echo "$outD" | grep -qF "LOCKED=$BARE_DEFAULT_CMD" \
+  && assert "TC-7: with no override, the locked value is the plain scripts/start-backend.sh default" pass \
+  || { assert "TC-7: with no override, the locked value is the plain scripts/start-backend.sh default" fail; echo "    got: $outD"; }
+
+# ── E. A caller that never locks a context (every script besides goal-iter-lean.sh) sees no
+#      behavior change -- the guard is a complete no-op when GOAL_ITER_BACKEND_LAUNCH_CMD is unset.
+outE="$(
+  (
+    set -euo pipefail
+    source "$CM"
+    unset GOAL_ITER_BACKEND_LAUNCH_CMD 2>/dev/null || true
+    SPY_LOG="$(mktemp)"
+    _start_service_with_retries() { echo "cmd=$3" >> "$SPY_LOG"; return 0; }
+    export QA_BACKEND_HEALTH_URL="http://localhost:19999/api/health"
+    export QA_BACKEND_LOG=/dev/null
+    export QA_BACKEND_START_CMD="$BARE_DEFAULT_CMD"
+    _rc=0
+    ensure_services_running || _rc=$?
+    echo "RC=$_rc"; echo "UP=$QA_BACKEND_UP"
+    echo "SPY_CALLS=$(wc -l < "$SPY_LOG")"
+  )
+)" || true
+echo "$outE" | grep -q '^RC=0$' && echo "$outE" | grep -q '^UP=yes$' && echo "$outE" | grep -q '^SPY_CALLS=1$' \
+  && assert "no-lock callers (qa-phase.sh, browser-qa-phase.sh, demo-phase.sh, ...) are unaffected" pass \
+  || { assert "no-lock callers (qa-phase.sh, browser-qa-phase.sh, demo-phase.sh, ...) are unaffected" fail; echo "    got: $outE"; }
+
+# ── F. Structural: goal-iter-lean.sh locks the context ONCE, before either the SPEED-2 or SPEED-3
+#      fork spawn points, and run_browser_qa_boot_and_replay no longer independently re-derives
+#      BACKEND_START_CMD from CHAIN_START_BACKEND_CMD (the exact pattern that caused iteration 23's
+#      defect) -- it must read the locked value instead.
+_lock_line="$(grep -n '^goal_iter_lock_backend_launch_context "\$ITER_DIR"$' "$GIL" | head -1 | cut -d: -f1)"
+_fork_line="$(grep -n '^_BQA_PID=""$' "$GIL" | head -1 | cut -d: -f1)"
+[[ -n "$_lock_line" && -n "$_fork_line" && "$_lock_line" -lt "$_fork_line" ]] \
+  && assert "goal-iter-lean.sh: launch context is locked before the SPEED-2/3 fork spawn points" pass \
+  || { assert "goal-iter-lean.sh: launch context is locked before the SPEED-2/3 fork spawn points" fail; echo "    lock@$_lock_line fork@$_fork_line"; }
+_fn_body="$(sed -n '/^run_browser_qa_boot_and_replay() {/,/^}$/p' "$GIL")"
+# Assignment form only ("BACKEND_START_CMD=...CHAIN_START_BACKEND_CMD...") -- a comment merely
+# naming the old pattern (to explain why it was removed) must not false-positive this check.
+if echo "$_fn_body" | grep -qE '^\s*BACKEND_START_CMD="\$\{CHAIN_START_BACKEND_CMD'; then
+  assert "run_browser_qa_boot_and_replay no longer re-derives from CHAIN_START_BACKEND_CMD" fail
+else
+  assert "run_browser_qa_boot_and_replay no longer re-derives from CHAIN_START_BACKEND_CMD" pass
+fi
+echo "$_fn_body" | grep -q 'BACKEND_START_CMD="\${GOAL_ITER_BACKEND_LAUNCH_CMD:-}"' \
+  && assert "run_browser_qa_boot_and_replay reads the locked GOAL_ITER_BACKEND_LAUNCH_CMD" pass \
+  || { assert "run_browser_qa_boot_and_replay reads the locked GOAL_ITER_BACKEND_LAUNCH_CMD" fail; }
+
+echo ""
+echo "=== Results: $PASS passed, $FAIL failed ==="
+[[ $FAIL -gt 0 ]] && exit 1
+exit 0
```
