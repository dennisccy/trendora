# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/engine/research.py b/apps/backend/app/engine/research.py
index ef78fb1f..d7b87df8 100644
--- a/apps/backend/app/engine/research.py
+++ b/apps/backend/app/engine/research.py
@@ -4430,28 +4430,61 @@ def compute_regime_lab(
     cfg = config or get_config()
     wf = cfg.walk_forward
     fl = cfg.research.factor_lab
-    horizons = list(wf.horizons)
 
     if view not in ALL_VIEWS:
         raise ValueError(f"unknown view {view!r}; valid views are {list(ALL_VIEWS)}")
 
-    labels = list(cfg.regime.labels)
-
     # lazy import — app.engine.data_manager imports FROM this module, so a module-level import back would
     # be circular (mirrors compute_factor_lab_all's own lazy import). Used only for the test-only
     # `_fault_inject_memory_error` hook below (a no-op in production).
     from app.engine import data_manager
 
-    # the run-ordinal index is bounded by TOTAL RUN COUNT (a lightweight two-column read over every stored
-    # `scanner_runs` row, never the heavy FR/ScannerResult tables) — shared across horizons, built once.
-    run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
-
-    by_horizon_per_label: dict[str, list[dict]] = {label: [] for label in labels}
-    by_horizon_per_decile: dict[int, list[dict]] = {d: [] for d in range(1, fl.deciles + 1)}
+    by_horizon_per_label: dict[str, list[dict]] = {}
+    by_horizon_per_decile: dict[int, list[dict]] = {}
     rank_ic_by_horizon: list[dict] = []
     any_degraded = False
 
-    for h in horizons:
+    # ops-hardening iter-60 (J-05/J-07 closeout, the iter-59 evaluator's named small defect): this
+    # prologue — the horizon list, the configured label vocabulary, and (for the episodes view) the
+    # run-ordinal index (`_run_position_index`, a real `scanner_runs` DB read) — used to sit OUTSIDE any
+    # try/except, so a DB-read failure here propagated as an unhandled exception straight to
+    # `GET /api/research/regime-lab`, a 500. It now shares the SAME isolate-and-continue discipline the
+    # per-horizon loop body below already uses: on ANY prologue failure, every configured horizon degrades
+    # honestly (via `_degrade_regime_lab_horizon`, the SAME degraded-entry shape the loop body's own catch
+    # produces) and the per-horizon loop body is skipped entirely (there is nothing trustworthy left to
+    # iterate with) — never a raw exception reaching the endpoint.
+    try:
+        horizons = list(wf.horizons)
+        labels = list(cfg.regime.labels)
+        # the run-ordinal index is bounded by TOTAL RUN COUNT (a lightweight two-column read over every
+        # stored `scanner_runs` row, never the heavy FR/ScannerResult tables) — shared across horizons,
+        # built once.
+        run_position = _run_position_index(session, as_of) if view == VIEW_EPISODES else None
+    except Exception as exc:  # noqa: BLE001 — mirrors the per-horizon loop's broad catch (AG-8): any
+        # prologue failure (not just MemoryError) must degrade honestly, never 500 the endpoint.
+        logger.exception(
+            "compute_regime_lab: prologue (labels/horizons/run-position) failed -- isolate-and-continue "
+            "(AG-8), degrading the WHOLE response honestly rather than propagating an unhandled exception "
+            "to GET /api/research/regime-lab as a 500: %s", exc,
+        )
+        # re-derive from config directly (never from the possibly-unset try-block locals above) — these
+        # are the same two pure, in-memory config reads, so degrading here does not risk a second failure.
+        horizons = list(cfg.walk_forward.horizons)
+        labels = list(cfg.regime.labels)
+        any_degraded = True
+        by_horizon_per_label.update({label: [] for label in labels})
+        by_horizon_per_decile.update({d: [] for d in range(1, fl.deciles + 1)})
+        for h in horizons:
+            _degrade_regime_lab_horizon(
+                h, labels, fl.deciles, by_horizon_per_label, by_horizon_per_decile, rank_ic_by_horizon,
+            )
+        horizons_to_process: list[int] = []  # already degraded every configured horizon above
+    else:
+        by_horizon_per_label.update({label: [] for label in labels})
+        by_horizon_per_decile.update({d: [] for d in range(1, fl.deciles + 1)})
+        horizons_to_process = horizons
+
+    for h in horizons_to_process:
         # a real scheduling yield once per horizon, mirrors compute_factor_lab_all's own iter-52 per-entry
         # yield (forces an OS-level GIL hand-off so a concurrent request gets a fair chance to be scheduled).
         time.sleep(0)
diff --git a/apps/backend/tests/test_regime_lab.py b/apps/backend/tests/test_regime_lab.py
index e2bab233..2c8c87db 100644
--- a/apps/backend/tests/test_regime_lab.py
+++ b/apps/backend/tests/test_regime_lab.py
@@ -771,6 +771,60 @@ def test_compute_regime_lab_one_horizon_non_memory_failure_degrades_only_that_ho
     )
 
 
+def test_compute_regime_lab_prologue_failure_degrades_honestly(lab_engine, monkeypatch, caplog):
+    """iter-60 (J-05/J-07 closeout, TC-4): a DB-read failure in the pre-loop PROLOGUE — resolving
+    `horizons`, `labels`, or the run-ordinal index via `_run_position_index` (a real `scanner_runs` read,
+    BEFORE the per-horizon loop even starts) — used to propagate straight out of `compute_regime_lab` as an
+    unhandled exception (a live `GET /api/research/regime-lab` 500). It must now share the SAME
+    isolate-and-continue discipline the per-horizon loop body already has: the WHOLE response degrades
+    honestly (every configured horizon gets an `unavailable` entry) instead of raising.
+
+    Teeth: `_run_position_index` is monkeypatched to raise unconditionally, so the VIEW_EPISODES default
+    (the only view that calls it) cannot reach the loop without the fix. A control run (VIEW_POOLED, which
+    never calls `_run_position_index`) proves the same monkeypatch is inert for the path that never reaches
+    the faulted call, so a broken patch cannot be mistaken for the fix working."""
+    import app.engine.research as research
+
+    cfg = load_config()
+    horizons = list(cfg.walk_forward.horizons)
+    labels = list(cfg.regime.labels)
+
+    def _boom(*args, **kwargs):
+        raise RuntimeError("simulated DB-read failure resolving the run-ordinal index")
+
+    monkeypatch.setattr(research, "_run_position_index", _boom)
+
+    # control arm: VIEW_POOLED never calls `_run_position_index`, so the monkeypatch must be inert here —
+    # proves the assertions below are exercising the faulted path, not a globally-broken function.
+    with Session(lab_engine) as session:
+        control = compute_regime_lab(session, cfg, view=VIEW_POOLED)
+    assert "regime_lab_status" not in control, "control run (pooled view) must be unaffected by the fault"
+
+    with caplog.at_level("ERROR", logger="trendora.research"):
+        with Session(lab_engine) as session:
+            payload = compute_regime_lab(session, cfg, view=VIEW_EPISODES)  # must not raise
+
+    assert payload["regime_lab_status"] == "unavailable"
+    assert payload["horizons"] == horizons, "the full configured horizon list is still echoed, even degraded"
+    assert payload["regime_labels"] == labels, "the full configured label vocabulary is still echoed"
+    assert payload["by_label"], "the label vocabulary must still be listed even on a prologue failure"
+    assert payload["by_decile"], "the decile vocabulary must still be listed even on a prologue failure"
+    for row in payload["by_label"] + payload["by_decile"]:
+        assert [bh["horizon"] for bh in row["by_horizon"]] == horizons, (
+            "every configured horizon must carry exactly one degraded entry, in config order"
+        )
+        for bh in row["by_horizon"]:
+            assert bh["status"] == "unavailable"
+            assert bh["n"] == 0
+            assert bh["mean_return"] is None and bh["mean_max_drawdown"] is None
+    for r in payload["rank_ic_by_horizon"]:
+        assert r["status"] == "unavailable"
+        assert r["rank_ic"] == {"value": None, "n": 0}
+    assert "isolate-and-continue" in caplog.text, (
+        "the prologue failure must be logged, never swallowed silently"
+    )
+
+
 def test_regime_lab_cached_never_persists_a_degraded_payload(lab_engine, monkeypatch):
     """A payload where at least one horizon degraded under memory pressure (the isolate-and-continue bound
     inside `compute_regime_lab`, which returns NORMALLY rather than raising) must NEVER be persisted to the
diff --git a/apps/frontend/app/research/_labs.tsx b/apps/frontend/app/research/_labs.tsx
index a69f58b4..2cdd14ed 100644
--- a/apps/frontend/app/research/_labs.tsx
+++ b/apps/frontend/app/research/_labs.tsx
@@ -30,6 +30,7 @@ import { Select } from "@/components/ui/select";
 import { TermInfo } from "@/components/ui/term-info";
 import { SampleLink } from "@/components/sample-link";
 import { formatElapsedSeconds, resolveLabLoadPanel } from "@/lib/lab-load-panel";
+import { isRegimeCellUnavailable } from "@/lib/regime-cell-status";
 import { groupedHorizonColumns, horizonColumnKey } from "@/lib/research-lab-columns";
 import { type CohortParams, type SampleScope } from "@/lib/samples-link";
 import { cn } from "@/lib/utils";
@@ -3948,7 +3949,14 @@ function RegimeReturnCell({
           {fmtPct(cell.mean_return)}
         </span>
       )}
-      <SampleLink n={cell.n} min={min} scope={scope} cohort={cohort} label={chipLabel} />
+      <SampleLink
+        n={cell.n}
+        min={min}
+        scope={scope}
+        cohort={cohort}
+        label={chipLabel}
+        unavailable={isRegimeCellUnavailable(cell)}
+      />
     </span>
   );
 }
diff --git a/apps/frontend/components/sample-link.tsx b/apps/frontend/components/sample-link.tsx
index 16f1942e..277b319c 100644
--- a/apps/frontend/components/sample-link.tsx
+++ b/apps/frontend/components/sample-link.tsx
@@ -1,6 +1,7 @@
 "use client";
 
 import Link from "next/link";
+import { AlertTriangle } from "lucide-react";
 
 import { useAsOfHref } from "@/components/asof-provider";
 import { SampleSize } from "@/components/forward-return";
@@ -25,6 +26,13 @@ import { cn } from "@/lib/utils";
  * now: stocks-leaderboard tickers (J-54), samples-row tickers (J-52), theme/sector member tickers
  * (J-57/J-58), and these `N=` chips (J-65); every OTHER in-app link (incl. the samples page's own "Back to
  * Research") stays same-window. Hover/focus underline the chip.
+ *
+ * `unavailable` (ops-hardening iter-60, J-05/J-07 closeout) is ADDITIVE and OPTIONAL, defaulting to
+ * `false` — every existing call site that never passes it renders byte-unchanged. When `true` (a
+ * `by_horizon` cell whose payload reports `status: "unavailable"` — a DEGRADED horizon, not a genuinely
+ * empty cohort), the chip is a plain, non-tooltip-only "Unavailable" indicator, never the `n=0` link: the
+ * cohort the link would drill into does not honestly exist for this response, so no `data-testid=
+ * "sample-link"` element is rendered at all.
  */
 export function SampleLink({
   n,
@@ -32,6 +40,7 @@ export function SampleLink({
   cohort,
   scope,
   label,
+  unavailable = false,
 }: {
   n: number;
   min: number;
@@ -40,8 +49,24 @@ export function SampleLink({
   scope: SampleScope;
   /** Accessible label describing which cohort this chip drills into. */
   label: string;
+  /** True for a degraded horizon (`status === "unavailable"`) — renders a non-link indicator instead. */
+  unavailable?: boolean;
 }) {
   const asofHref = useAsOfHref();
+
+  if (unavailable) {
+    return (
+      <span
+        className="inline-flex items-center gap-1 text-xs text-text-faint"
+        data-testid="sample-link-unavailable"
+        title="Temporarily unavailable — degraded under memory pressure"
+      >
+        <AlertTriangle className="h-3 w-3" aria-hidden />
+        Unavailable
+      </span>
+    );
+  }
+
   const href = asofHref(buildSamplesHref(cohort, scope));
   return (
     <Link
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index bd707b98..0d9a390b 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -251,10 +251,23 @@ replay_lane_partition_and_verify() {
   # a replay SKIP that nothing re-confirmed (silently unverified journey). A
   # lint crash (no output) conservatively keeps the old file-exists behavior:
   # the verify runner re-validates at replay time anyway.
+  #
+  # ops-hardening iter-60 (J-05/J-07 closeout, TOP-PRIORITY lane-coverage gap): the lint pass now covers
+  # TARGET_JOURNEYS too (union with REQUIRED_JOURNEYS, deduped) — a target journey's on-file golden must
+  # be validated the SAME way a required journey's is before the partition loop below can trust it.
   local _lint_out=""
-  if [[ -n "${REQUIRED_JOURNEYS// /}" ]]; then
+  local _rl_lint_set
+  # ${TARGET_JOURNEYS:-} — NOT a bare reference: some callers (e.g. plain phase mode, and this file's own
+  # test sandbox for pre-iter-60 scenarios) never assign TARGET_JOURNEYS at all, and every caller here runs
+  # under `set -u` (nounset) per the header contract, so a bare reference would abort the whole lane. The
+  # trailing `|| true` is load-bearing too, mirroring replay_lane_spec_journeys's own guard (see its
+  # comment above): both journey sets empty is a legitimate parse result (e.g. an iteration-0 baseline with
+  # no Required-still-passing AND no Target journeys) — `grep` then matches nothing and exits 1, which
+  # under this whole file's `set -e`+pipefail discipline would otherwise silently kill the caller.
+  _rl_lint_set="$(printf '%s %s\n' "$REQUIRED_JOURNEYS" "${TARGET_JOURNEYS:-}" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ' ' || true)"
+  if [[ -n "${_rl_lint_set// /}" ]]; then
     _lint_out="$(python3 "$DEMO_RUNNER" --mode lint --scripts-dir "$JOURNEY_SCRIPTS_DIR" \
-      --journeys "$(echo "$REQUIRED_JOURNEYS" | tr ' ' ',' | sed 's/^,*//;s/,*$//')" 2>/dev/null || true)"
+      --journeys "$(echo "$_rl_lint_set" | tr ' ' ',' | sed 's/^,*//;s/,*$//')" 2>/dev/null || true)"
   fi
   R_REPLAY=""; R_LLM=""
   local _j
@@ -272,6 +285,37 @@ replay_lane_partition_and_verify() {
     fi
   done
 
+  # ops-hardening iter-60 (J-05/J-07 closeout, TOP-PRIORITY lane-coverage gap, iter-59 lesson entry 1):
+  # this loop previously scanned ONLY REQUIRED_JOURNEYS — a TARGET_JOURNEYS entry's already-on-file
+  # golden sat unexecuted every run, so `merge_results.py --target` could only ever FLAG the journey as
+  # having zero rows (BLOCKED), never actually close the gap by replaying it. A target journey with a
+  # valid golden now joins R_REPLAY too (skipping one already placed above by the required-journeys loop,
+  # so a journey listed as BOTH required and target is never double-entered) and is ACTUALLY REPLAYED by
+  # demo_runner.py below. A missing or lint-invalid target golden is deliberately left OFF R_LLM here —
+  # that set feeds `replay_lane_llm_regression_set`'s "required-still-passing regression re-check"
+  # dispatch, a different semantic from "this iteration's own Target journey", which the iteration's
+  # primary browser-QA dispatch already covers independent of this lane (the "existing fallback path"
+  # TC's error case relies on); an invalid golden is still quarantined for hygiene, same as a required
+  # journey's.
+  local _rl_target_only
+  # `|| true`: TARGET_JOURNEYS is legitimately empty on most iterations (this journey set is often
+  # empty even when REQUIRED_JOURNEYS is not) — same silent-death pipefail gotcha as above.
+  _rl_target_only="$(echo "${TARGET_JOURNEYS:-}" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u || true)"
+  for _j in $_rl_target_only; do
+    if [[ " $R_REPLAY " == *" $_j "* || " $R_LLM " == *" $_j "* ]]; then
+      continue  # already routed by the required-journeys loop above (required AND target)
+    fi
+    if [[ -f "$JOURNEY_SCRIPTS_DIR/$_j.json" ]]; then
+      if printf '%s\n' "$_lint_out" | grep -q "^$_j invalid"; then
+        _replay_lane_log "Golden for target journey $_j failed lint — quarantining ($_j.json.invalid); the iteration's own target-journey QA dispatch still covers it: $(printf '%s\n' "$_lint_out" | grep -m1 "^$_j invalid" | cut -d' ' -f2-)"
+        mv -f "$JOURNEY_SCRIPTS_DIR/$_j.json" "$JOURNEY_SCRIPTS_DIR/$_j.json.invalid" 2>/dev/null || true
+      else
+        _replay_lane_log "Target journey $_j has an on-file, lint-valid golden — routed into the deterministic replay set (closes the iter-59 lane-coverage gap)."
+        R_REPLAY+="$_j "
+      fi
+    fi
+  done
+
   _use_replay="no"
   if [[ "${CHAIN_REGRESSION_REPLAY:-true}" == "true" && "$FRONTEND_AVAILABLE" == "yes" && -n "${R_REPLAY// /}" ]]; then
     _use_replay="yes"
diff --git a/incredible_auto_dev/tests/automation/test-replay-lane.sh b/incredible_auto_dev/tests/automation/test-replay-lane.sh
index b8b8f49b..4b970d07 100644
--- a/incredible_auto_dev/tests/automation/test-replay-lane.sh
+++ b/incredible_auto_dev/tests/automation/test-replay-lane.sh
@@ -17,6 +17,15 @@
 #   2. replay_lane_paths: SID derivation + all lane path globals + mkdir.
 #   3. Partition: golden on file → R_REPLAY; missing → R_LLM; lint-invalid →
 #      quarantined (*.json.invalid) + R_LLM.
+#      3b (ops-hardening iter-60): TARGET_JOURNEYS entries join the SAME partition —
+#      an on-file golden joins R_REPLAY and is ACTUALLY REPLAYED (the iter-59
+#      lane-coverage gap: a target journey's golden used to sit unexecuted every
+#      run); a lint-invalid one is quarantined but NOT routed to R_LLM (a
+#      different semantic set — the iteration's own target-journey QA dispatch
+#      already covers it); a missing one is left untouched (same fallback); a
+#      journey in BOTH sets is never double-entered; TARGET_JOURNEYS being
+#      entirely unset (the common case, and every pre-iter-60 scenario below)
+#      must not crash the lane under set -u.
 #   4. Verify rc=0 → _use_replay=yes, REPLAY_FAILED empty, results file has the
 #      UT-J row.
 #   5. Verify rc=5 (journey FAIL) → REPLAY_FAILED extracted for LLM re-confirm.
@@ -166,13 +175,19 @@ PYEOF
 
 # Run a lane scenario in a fresh production-discipline subshell. Env knobs are
 # passed via the caller's environment. Prints the outcome globals on one line.
-run_partition() {  # $1 = REQUIRED_JOURNEYS value
+# $1 = REQUIRED_JOURNEYS value, $2 = optional TARGET_JOURNEYS value (ops-hardening
+# iter-60 — defaults to unset, exactly like every pre-iter-60 scenario below, so
+# the lib must survive TARGET_JOURNEYS never being assigned at all under set -u).
+run_partition() {  # $1 = REQUIRED_JOURNEYS value, $2 = optional TARGET_JOURNEYS value
   (
     set -euo pipefail
     # shellcheck source=/dev/null
     source "$LIB"
     REPO_ROOT="$SBX"
     REQUIRED_JOURNEYS="$1"
+    if [[ -n "${2:-}" ]]; then
+      TARGET_JOURNEYS="$2"
+    fi
     FRONTEND_AVAILABLE="${FRONTEND_AVAILABLE_OVERRIDE:-yes}"
     FRONTEND_URL="http://localhost:9"
     # REL-5: the retry path re-checks services when the function exists (in
@@ -268,6 +283,50 @@ out="$(STUB_LINT_INVALID="J-03" STUB_VERIFY_STAMP="$WORK/stamp3" run_partition "
   && assert "partition: invalid golden quarantined (.json.invalid)" pass \
   || assert "partition: invalid golden quarantined (.json.invalid)" fail
 
+# ── 3b. Partition: TARGET_JOURNEYS with an on-file golden joins R_REPLAY too (ops-hardening
+#       iter-60, TC-1 — the lane-coverage gap: J-05/J-07 passed LIVE but never got replayed because
+#       this loop previously scanned ONLY REQUIRED_JOURNEYS). J-01 is BOTH required and target (must
+#       not double-enter); J-05 is target-only with a valid golden (must join R_REPLAY and be
+#       ACTUALLY REPLAYED); J-07 is target-only with a lint-invalid golden (quarantined, not R_LLM —
+#       a different set with a different semantic, see the fix's own comment); J-09 is target-only
+#       with NO golden at all (must stay untouched — the "existing fallback path" the error-case
+#       test below relies on, not this lane's R_LLM). ─────────────────────────────────────────────
+reset_goldens
+golden "J-01"
+golden "J-05"
+golden "J-07"
+out="$(STUB_LINT_INVALID="J-07" STUB_VERIFY_STAMP="$WORK/stamp3b" run_partition "J-01 " "J-01 J-05 J-07 J-09")"
+[[ "$out" == "R_REPLAY=<J-01 J-05 >|R_LLM=<>|use=<yes>|failed=<>" ]] \
+  && assert "partition: TARGET-only journey with an on-file golden joins R_REPLAY (TC-1)" pass \
+  || { assert "partition: TARGET-only journey with an on-file golden joins R_REPLAY (TC-1)" fail; echo "    got: $out"; }
+[[ -f "$SBX/runs/goal-session-rltest/journey-scripts/J-07.json.invalid" && ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-07.json" ]] \
+  && assert "partition: lint-invalid TARGET-only golden is still quarantined" pass \
+  || assert "partition: lint-invalid TARGET-only golden is still quarantined" fail
+[[ ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-09.json" && ! -f "$SBX/runs/goal-session-rltest/journey-scripts/J-09.json.invalid" ]] \
+  && assert "partition: TARGET-only journey with no golden is left untouched (existing fallback path, not R_LLM)" pass \
+  || assert "partition: TARGET-only journey with no golden is left untouched" fail
+[[ "$(cat "$WORK/stamp3b" 2>/dev/null)" == "J-01 J-05" ]] \
+  && assert "partition: demo_runner actually invoked WITH the target journey (ACTUALLY REPLAYED, TC-1)" pass \
+  || assert "partition: demo_runner actually invoked WITH the target journey (got '$(cat "$WORK/stamp3b" 2>/dev/null)')" fail
+grep -q '^| UT-J-05 ' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
+  && assert "partition: J-05 produced a REAL row in the raw replay results file (TC-1)" pass \
+  || assert "partition: J-05 produced a REAL row in the raw replay results file (TC-1)" fail
+
+# ── 3c. Partition: TARGET_JOURNEYS never assigned at all does not crash the lane (set -u safety —
+#       most callers/scenarios, including every one above, never set it). ──────────────────────────
+out="$(STUB_VERIFY_STAMP="$WORK/stamp3c" run_partition "J-01 ")"
+[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<>|use=<yes>|failed=<>" ]] \
+  && assert "partition: TARGET_JOURNEYS unset entirely does not crash the lane (set -u safety)" pass \
+  || { assert "partition: TARGET_JOURNEYS unset entirely does not crash the lane (set -u safety)" fail; echo "    got: $out"; }
+
+# ── 3d. Partition: a journey listed as BOTH required and target is never double-entered ─────────
+reset_goldens
+golden "J-01"
+out="$(STUB_VERIFY_STAMP="$WORK/stamp3d" run_partition "J-01 " "J-01 ")"
+[[ "$out" == "R_REPLAY=<J-01 >|R_LLM=<>|use=<yes>|failed=<>" ]] \
+  && assert "partition: a journey in BOTH required and target sets is not double-entered" pass \
+  || { assert "partition: a journey in BOTH required and target sets is not double-entered" fail; echo "    got: $out"; }
+
 # ── 4. Verify rc=0 (all pass) ────────────────────────────────────────────────
 [[ -f "$SBX/reports/phase-$ITER-regression-replay-results.md" ]] \
   && grep -q '^| UT-J-01 ' "$SBX/reports/phase-$ITER-regression-replay-results.md" \
diff --git a/apps/frontend/lib/regime-cell-status.test.ts b/apps/frontend/lib/regime-cell-status.test.ts
new file mode 100644
index 00000000..8ddcb90a
--- /dev/null
+++ b/apps/frontend/lib/regime-cell-status.test.ts
@@ -0,0 +1,52 @@
+/**
+ * Unit tests for the J-05/J-07 closeout Regime-Lab degraded-cell predicate (lib/regime-cell-status.ts).
+ *
+ * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
+ *   node lib/regime-cell-status.test.ts
+ *
+ * TC-5/TC-6 (ops-hardening iter-60): a DEGRADED horizon (`status: "unavailable"`, `n: 0`) must be
+ * reported unavailable — `RegimeReturnCell` uses this to suppress the active `SampleLink` drill-down in
+ * favor of a visible "Unavailable" indicator. A genuinely low-sample-but-not-degraded cell (`status`
+ * absent, a real `n` below `min`) must NOT be reported unavailable — its existing chip and link render
+ * exactly as before.
+ */
+import assert from "node:assert";
+
+import { isRegimeCellUnavailable } from "./regime-cell-status.ts";
+import type { RegimeLabHorizonCell } from "./api.ts";
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+// --- TC-5: a degraded horizon (status: "unavailable", n: 0) is reported unavailable ----------------
+
+check("a degraded cell (status: unavailable, n=0) is reported unavailable", () => {
+  const cell: RegimeLabHorizonCell = {
+    horizon: 20, n: 0, low_sample: true, mean_return: null, mean_max_drawdown: null, status: "unavailable",
+  };
+  assert.strictEqual(isRegimeCellUnavailable(cell), true);
+});
+
+// --- TC-6: a genuine low-sample cell (status absent, real n below min) is NOT reported unavailable ---
+
+check("a genuine low-sample cell (status absent, n=3 below min) is NOT reported unavailable", () => {
+  const cell: RegimeLabHorizonCell = {
+    horizon: 20, n: 3, low_sample: true, mean_return: -0.012, mean_max_drawdown: -0.041,
+  };
+  assert.strictEqual(isRegimeCellUnavailable(cell), false);
+});
+
+// --- a clean, well-sampled cell is NOT reported unavailable (the ordinary case) ----------------------
+
+check("a clean, well-sampled cell (status absent, low_sample false) is NOT reported unavailable", () => {
+  const cell: RegimeLabHorizonCell = {
+    horizon: 20, n: 512, low_sample: false, mean_return: 0.031, mean_max_drawdown: -0.058,
+  };
+  assert.strictEqual(isRegimeCellUnavailable(cell), false);
+});
+
+console.log(`\nregime-cell-status: ${passed} checks passed`);
diff --git a/apps/frontend/lib/regime-cell-status.ts b/apps/frontend/lib/regime-cell-status.ts
new file mode 100644
index 00000000..52cb3fe8
--- /dev/null
+++ b/apps/frontend/lib/regime-cell-status.ts
@@ -0,0 +1,18 @@
+import type { RegimeLabHorizonCell } from "./api";
+
+/**
+ * ops-hardening iter-60 (J-05/J-07 closeout) — the single, pure authority for whether `RegimeReturnCell`
+ * (`app/research/_labs.tsx`) suppresses its `SampleLink` drill-down in favor of a visible,
+ * non-tooltip-only "Unavailable" indicator. No React, no DOM types, so it is unit-testable under `node`
+ * (the existing frontend convention — see `lib/availability-empty-state.ts`).
+ *
+ * `status === "unavailable"` means THIS horizon's aggregation degraded under memory pressure
+ * (`compute_regime_lab`'s per-horizon isolate-and-continue bound, ops-hardening iter-59/60) — its `n=0`
+ * is an honest placeholder for a cohort that does not really exist for this response, not a genuinely
+ * empty one, so a LIVE drill-down link into it would be misleading (previously distinguishable from a
+ * real n=0 only by hovering the `title`). A genuine low-sample cell (`low_sample: true`, `status` absent)
+ * is unaffected — its chip and link stay exactly as before.
+ */
+export function isRegimeCellUnavailable(cell: RegimeLabHorizonCell): boolean {
+  return cell.status === "unavailable";
+}
```
