# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 5624baaf..327c4c2c 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -2486,7 +2486,34 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
       _prev_coh_file="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/coherence.md"
       _prev_budget_marker="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/budget-breached"
       _arb_decision="" _arb_reason=""
-      if [[ "${PRIOR_VERDICT:-}" == "ESCALATE" || "${PRIOR_VERDICT:-}" == "REGRESSION" ]]; then
+      if goal_full_depth_required "$ITER_SPEC_PATH"; then
+        # ── PRECEDENCE: a hard full-depth requirement outranks COST policy ─────
+        # Everything below this rung is a cost/performance heuristic answering
+        # "is full depth worth the wall-clock here?" — budget-breach, full-cap,
+        # cadence, and the evaluator's lean preference. None of them answers
+        # "can this engine execute full depth?", which is the only question that
+        # may override a safety requirement. When an iteration is hard-required
+        # full (CHAIN_REQUIRE_FULL_DEPTH, or a spec `Depth enforcement: required`
+        # line) the adversarial review/audit lane IS the control standing between
+        # a destructive write and an unreviewed mutation, so cost may not trade
+        # it away. The cost rungs stay fully intact for every ordinary iteration.
+        _arb_decision="full"; _arb_reason="hard-full-required"
+        # Evidence, not behaviour: record which cost rung WOULD have demoted this
+        # iteration, so the budget/cadence signal is preserved in telemetry
+        # rather than silently discarded. Markers on disk are never touched.
+        _overridden=""
+        if [[ -f "$_prev_budget_marker" && "${PRIOR_VERDICT:-}" == "CONTINUE" ]]; then
+          _overridden="budget-breach"
+        elif goal_full_ran_in_window "$GOAL_SESSION_DIR_LOCAL" "$CURRENT_ITER"; then
+          _overridden="full-cap"
+        elif [[ "$PRIOR_DEPTH" == "lean" || "$PRIOR_DEPTH" == "evidence" ]]; then
+          _overridden="evaluator-requested-${PRIOR_DEPTH}"
+        fi
+        if [[ -n "$_overridden" ]]; then
+          echo "[run-goal] Depth arbiter: HARD full-depth requirement overrides the cost rung '$_overridden' (the signal is recorded, not acted on; its marker is preserved)."
+          record_telemetry_event "depth_cost_overridden" "$(jq -cn --arg o "$_overridden" --arg pv "${PRIOR_VERDICT:-}" --arg pd "${PRIOR_DEPTH:-}" '{requirement:"hard-full-required", overridden_cost_rung:$o, prior_verdict:$pv, prior_depth:$pd}' 2>/dev/null || printf '{"requirement":"hard-full-required","overridden_cost_rung":"%s"}' "$_overridden")"
+        fi
+      elif [[ "${PRIOR_VERDICT:-}" == "ESCALATE" || "${PRIOR_VERDICT:-}" == "REGRESSION" ]]; then
         _arb_decision="full"; _arb_reason="prior-verdict-${PRIOR_VERDICT}"
       elif grep -qE '^\*\*Verdict:\*\* COHERENCE-FAIL' "$_prev_coh_file" 2>/dev/null; then
         _arb_decision="full"; _arb_reason="prior-coherence-fail"
@@ -2517,8 +2544,12 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
         _use_legacy_allowlist=1
       fi
       if [[ "$_arb_decision" == "lean" ]] && goal_full_depth_required "$ITER_SPEC_PATH"; then
-        # FAIL-CLOSED: full depth is a hard requirement here, so the cost ladder
-        # may not trade it away. Halt before dispatch instead of degrading.
+        # Defence in depth. With the precedence rung above, a hard-required
+        # iteration always resolves to full, so this is unreachable by design —
+        # AWAITING_FULL_DEPTH must mean "the engine cannot execute full depth",
+        # never "the cost ladder preferred lean". It stays as a backstop so a
+        # future edit that reorders or adds a cost rung cannot silently
+        # reintroduce the demotion this guard exists to stop.
         _full_depth_pause "arbiter-demotion:${_arb_reason}" "depth-arbiter"
       fi
       if [[ "$_arb_decision" == "lean" ]]; then
diff --git a/incredible_auto_dev/tests/automation/test-full-depth-required.sh b/incredible_auto_dev/tests/automation/test-full-depth-required.sh
index ccf7ddb6..cdd219a5 100755
--- a/incredible_auto_dev/tests/automation/test-full-depth-required.sh
+++ b/incredible_auto_dev/tests/automation/test-full-depth-required.sh
@@ -178,6 +178,118 @@ else
   assert "status: AWAITING_FULL_DEPTH is registered in the plain-language keys + explainer" "fail"
 fi
 
+
+# ══════════════════════════════════════════════════════════════════════════════
+# PRECEDENCE: a hard full-depth requirement outranks the COST ladder.
+#
+# These cases EXECUTE the real arbiter text rather than grepping it: the ladder
+# is inline in run-goal.sh, so we slice it out between two stable anchors and
+# eval it in a sandbox with the external predicates stubbed. That proves actual
+# branch behaviour without booting an engine (host-safe, no services, no DB).
+# ══════════════════════════════════════════════════════════════════════════════
+_arb_start="$(grep -n '_arb_decision="" _arb_reason=""' "$RG" | head -1 | cut -d: -f1)"
+_arb_end="$(grep -n 'PRIOR_DEPTH==full: the evaluator itself asked for full' "$RG" | head -1 | cut -d: -f1)"
+_arb_end=$(( _arb_end + 3 ))   # ..through the ladder's closing `fi`
+awk -v s="$_arb_start" -v e="$_arb_end" 'NR>=s && NR<=e' "$RG" > "$WORK/arb-block.sh"
+if bash -n "$WORK/arb-block.sh" 2>/dev/null; then
+  assert "harness: the arbiter ladder slices out as a syntactically complete block" "pass"
+else
+  assert "harness: the arbiter ladder slices out as a syntactically complete block" "fail"
+fi
+
+# run_arb <hard:0|1> <budget_marker:0|1> <full_in_window:0|1> <prior_verdict> <prior_depth>
+# -> echoes "<decision>:<reason>"
+run_arb() {
+  local hard="$1" budget="$2" inwin="$3" pv="$4" pd="$5"
+  (
+    set +e
+    PRIOR_VERDICT="$pv"; PRIOR_DEPTH="$pd"
+    CURRENT_ITER=8; LEAN_STREAK=0
+    GOAL_SESSION_DIR_LOCAL="$WORK/sess"; JOURNEY_HISTORY="$WORK/jh.json"
+    ITER_SPEC_PATH="$WORK/spec.md"; _budget_demoted=""; _use_legacy_allowlist=""
+    mkdir -p "$WORK/sess/iter-7"
+    _prev_coh_file="$WORK/sess/iter-7/coherence.md"
+    _prev_budget_marker="$WORK/sess/iter-7/budget-breached"
+    rm -f "$_prev_budget_marker"; [[ "$budget" == 1 ]] && : > "$_prev_budget_marker"
+    printf -- '- **Depth:** full\n- **Full trigger:** 1\n' > "$ITER_SPEC_PATH"
+    [[ "$hard" == 1 ]] && printf -- '- **Depth enforcement:** required\n' >> "$ITER_SPEC_PATH"
+    goal_full_ran_in_window() { [[ "$inwin" == 1 ]]; }
+    goal_cadence_forces_full() { return 1; }
+    goal_new_fullstack_journey() { return 1; }
+    record_telemetry_event() { :; }
+    # shellcheck disable=SC1090
+    . "$WORK/arb-block.sh" >/dev/null 2>&1
+    printf '%s:%s' "$_arb_decision" "$_arb_reason"
+  )
+}
+
+# 1. ordinary full + budget-breach -> still demoted to lean (cost policy intact)
+r="$(run_arb 0 1 0 CONTINUE full)"
+[[ "$r" == "lean:budget-breach" ]] \
+  && assert "ordinary: Depth full + budget-breach -> lean (cost arbiter unchanged)" "pass" \
+  || assert "ordinary: Depth full + budget-breach -> lean (got '$r')" "fail"
+
+# 2. hard-required + budget-breach -> stays FULL
+r="$(run_arb 1 1 0 CONTINUE full)"
+[[ "$r" == "full:hard-full-required" ]] \
+  && assert "precedence: hard-required + budget-breach -> FULL" "pass" \
+  || assert "precedence: hard-required + budget-breach -> FULL (got '$r')" "fail"
+
+# 3. hard-required + full-cap -> stays FULL
+r="$(run_arb 1 0 1 CONTINUE full)"
+[[ "$r" == "full:hard-full-required" ]] \
+  && assert "precedence: hard-required + full-cap -> FULL" "pass" \
+  || assert "precedence: hard-required + full-cap -> FULL (got '$r')" "fail"
+
+# 4. hard-required + evaluator recommends lean -> stays FULL
+r="$(run_arb 1 0 0 CONTINUE lean)"
+[[ "$r" == "full:hard-full-required" ]] \
+  && assert "precedence: hard-required + evaluator-recommends-lean -> FULL" "pass" \
+  || assert "precedence: hard-required + evaluator-recommends-lean -> FULL (got '$r')" "fail"
+
+# 9. ordinary full-cap and evaluator-lean demotions still fire for normal iters
+r="$(run_arb 0 0 1 CONTINUE full)"
+[[ "$r" == "lean:full-cap" ]] \
+  && assert "ordinary: Depth full + full-cap -> lean (cost arbiter unchanged)" "pass" \
+  || assert "ordinary: Depth full + full-cap -> lean (got '$r')" "fail"
+r="$(run_arb 0 0 0 CONTINUE lean)"
+[[ "$r" == "lean:evaluator-requested-lean" ]] \
+  && assert "ordinary: Depth full + evaluator-lean -> lean (cost arbiter unchanged)" "pass" \
+  || assert "ordinary: Depth full + evaluator-lean -> lean (got '$r')" "fail"
+
+# sanctioned fulls still win for ordinary iterations
+r="$(run_arb 0 1 1 ESCALATE lean)"
+[[ "$r" == "full:prior-verdict-ESCALATE" ]] \
+  && assert "ordinary: prior ESCALATE still grants full ahead of cost rungs" "pass" \
+  || assert "ordinary: prior ESCALATE still grants full ahead of cost rungs (got '$r')" "fail"
+
+# 6. AWAITING_FULL_DEPTH is no longer reachable from a COST demotion
+r="$(run_arb 1 1 1 CONTINUE lean)"
+[[ "$r" == full:* ]] \
+  && assert "no cost-driven pause: hard-required never resolves lean, so the arbiter cannot pause on cost" "pass" \
+  || assert "no cost-driven pause: hard-required never resolves lean (got '$r')" "fail"
+
+# 5/8. genuine INABILITY still pauses: the --no-finalize and unparseable-depth
+# guards are capability failures, not cost policy, and remain wired.
+if grep -q '_full_depth_pause "run-phase.sh lacks --no-finalize"' "$RG" \
+   && grep -q '_full_depth_pause "unparseable Depth' "$RG"; then
+  assert "genuine inability: capability guards (--no-finalize, unparseable depth) still pause" "pass"
+else
+  assert "genuine inability: capability guards (--no-finalize, unparseable depth) still pause" "fail"
+fi
+
+# 7. the historical budget marker is read, never written/removed by the arbiter
+if grep -qE '(rm|mv|:) *> *"\$_prev_budget_marker"' "$RG"; then
+  assert "evidence: arbiter never deletes/overwrites the budget-breached marker" "fail"
+else
+  assert "evidence: arbiter never deletes/overwrites the budget-breached marker" "pass"
+fi
+if grep -q 'depth_cost_overridden' "$RG"; then
+  assert "evidence: the overridden cost rung is recorded in telemetry" "pass"
+else
+  assert "evidence: the overridden cost rung is recorded in telemetry" "fail"
+fi
+
 echo ""
 echo "  ${PASS} passed, ${FAIL} failed"
 [[ "$FAIL" -eq 0 ]]
```

## Excluded-path stat (dependency/lockfile visibility)

 .../dispatch/.awaiting-pump                        |   1 -
 .../iter-8/depth-dispatched                        |   2 +-
 .../iter-8/goal-slice.md                           | 621 ++++++++++++++++++++-
 runs/goal-session-market-compass/session.json      |   2 +-
 .../state/assumptions.md                           | 188 -------
 .../state/assumptions.md.archive.md                | 191 +++++++
 runs/goal-session-market-compass/state/lessons.md  |  47 +-
 runs/goal-session-market-compass/telemetry.jsonl   |   7 +
 8 files changed, 811 insertions(+), 248 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
