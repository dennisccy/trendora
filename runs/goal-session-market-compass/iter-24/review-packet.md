# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/docs/goal.md b/docs/goal.md
index 6c9aa707..3a37a6e6 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -2194,6 +2194,52 @@ manifest artifact (it must be self-describing and self-caveating).
       the demo requirement is replaced by the pre/post inventory, the mutation reconciliation, the
       cache-invalidation proof, and the manifest-immutability evidence.
 
+       ### OWNER RULING — J-11 CLOSED; one authorized launcher fix, then normal work resumes
+       *(owner, 2026-08-27 — binding)*
+
+       A **later** owner decision than the acceptance ruling above. It closes J-11 and sets the
+       continuation policy for this goal. It revises no earlier ruling, evidence or Stage result.
+
+       **1. J-11 is CLOSED.** The final serving/replay verification ran against the disposable clone
+       and passed. J-11 is accepted as **PASSING**. Do **not** reopen J-11 recovery or J-11 serving
+       verification.
+       ```
+       J-11 STATUS: PASSING — CLOSED
+       ```
+
+       **2. The accidental iteration-23 canonical-DB boot is a historical HARNESS contract violation,
+       not a Trendora product-data regression.** The 10 resulting rows across the five recomputable
+       derived cache tables are **accepted in place**. Do not delete them. Do not perform cleanup
+       writes merely to restore the pre-verification cache state. Do not manually delete or alter
+       `trendora.db-wal`.
+
+       **3. Exactly one narrow Goal Mode tooling fix is AUTHORIZED** — the demonstrated launcher
+       defect in `incredible_auto_dev/scripts/automation/goal-iter-lean.sh`. Scope, exhaustively:
+       - when an iteration supplies an alternate `TRENDORA_CONFIG` and/or `CHAIN_START_BACKEND_CMD`,
+         every browser-QA, deterministic-replay, retry and restart backend launch MUST preserve that
+         same launch context;
+       - it MUST never silently fall back to the canonical database while an alternate
+         verification/QA database is in force;
+       - missing required launch context MUST fail closed **before** backend boot;
+       - add a focused regression test reproducing the iteration-23 failure.
+       No broader Goal Mode refactor, stall-detector redesign, depth-system redesign or unrelated
+       automation cleanup is authorized.
+
+       **4. The iteration-23 disposable clone** (`runs/goal-market-compass-iter-23/verify-clone/`) is
+       kept only until this launcher fix is verified. It may then be deleted as disposable evidence
+       infrastructure.
+
+       **5. Normal Market Compass product work resumes immediately** once the launcher defect is fixed
+       and verified. No further owner authorization is needed for ordinary non-destructive product
+       iterations.
+
+       **6. Owner continuation policy for this goal (binding).** Do **not** STALL merely for reversible
+       cleanup choices, disposable-artifact cleanup, or correctly recomputable derived-cache residue —
+       prefer the non-destructive / no-cleanup default, record it, and continue. Owner approval is
+       still REQUIRED for: raw/canonical data repair; immutable-manifest mutation; schema migration;
+       new network/provider access; destructive user-state changes; or another genuinely irreversible
+       product-contract decision.
+
 <!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
      between the two markers below (see the goal-self-extension skill). The human-authored journeys
      above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-market-compass-index.html     |  15 +-
 runs/goal-session-market-compass/session.json      |   8 +-
 .../state/assumptions.md                           | 294 ++++-----------------
 .../state/assumptions.md.archive.md                | 247 +++++++++++++++++
 runs/goal-session-market-compass/state/lessons.md  |  23 +-
 .../state/lessons.md.archive.md                    |  32 +++
 runs/goal-session-market-compass/summary.md        |  21 +-
 runs/goal-session-market-compass/telemetry.jsonl   |  29 ++
 runs/goal-session-market-compass/trace/.next-step  |   2 +-
 runs/goal-session-market-compass/trace/trace.jsonl |   2 +
 10 files changed, 393 insertions(+), 280 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
