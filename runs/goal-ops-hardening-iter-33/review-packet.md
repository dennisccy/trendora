# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/frontend/app/research/_labs.tsx b/apps/frontend/app/research/_labs.tsx
index 041ef365..f5594c35 100644
--- a/apps/frontend/app/research/_labs.tsx
+++ b/apps/frontend/app/research/_labs.tsx
@@ -9,6 +9,7 @@ import {
   ArrowUpDown,
   ChevronDown,
   ChevronRight,
+  Loader2,
   Microscope,
   Plus,
   Shield,
@@ -28,6 +29,7 @@ import { Card } from "@/components/ui/card";
 import { Select } from "@/components/ui/select";
 import { TermInfo } from "@/components/ui/term-info";
 import { SampleLink } from "@/components/sample-link";
+import { formatElapsedSeconds, resolveLabLoadPanel } from "@/lib/lab-load-panel";
 import { groupedHorizonColumns, horizonColumnKey } from "@/lib/research-lab-columns";
 import { type CohortParams, type SampleScope } from "@/lib/samples-link";
 import { cn } from "@/lib/utils";
@@ -170,22 +172,85 @@ export function ResearchCaveat({
   );
 }
 
-/** The shared "backend unavailable" card every lab route renders on a fetch error (single source). */
-export function ResearchError({ what }: { what: string }) {
+/** The shared "backend unavailable" card every lab route renders on a fetch error (single source).
+ *  ops-hardening iter-33 (UT-11): an optional `onRetry` adds an in-page Retry control, so a lab whose
+ *  read can genuinely fail mid-compute offers a way out instead of requiring a manual page reload.
+ *  Call sites that pass no `onRetry` render exactly as before. */
+export function ResearchError({ what, onRetry }: { what: string; onRetry?: () => void }) {
   return (
-    <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
-      <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
-      <div>
+    <Card className="flex items-start gap-3 border-neg bg-surface p-5 text-sm text-neg">
+      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
+      <div className="space-y-2">
         <p className="font-medium">Backend unavailable</p>
         <p className="text-text-muted">
           {what} could not load from the API. No figures are shown rather than fabricated values. Confirm
           the backend is running and retry.
         </p>
+        {onRetry ? (
+          <button
+            type="button"
+            onClick={onRetry}
+            data-testid="research-error-retry"
+            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface-2 px-3 text-xs font-medium text-text transition-colors hover:border-border-strong hover:bg-surface focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent active:bg-border"
+          >
+            Retry
+          </button>
+        ) : null}
+      </div>
+    </Card>
+  );
+}
+
+/** ops-hardening iter-33 (UT-11) — the honest "still computing" notice a lab renders once its fetch has
+ *  been in flight longer than the grace window in `lib/lab-load-panel.ts`. Replaces the previous
+ *  behaviour on `/research/regime-lab`, where a cold-cache read (60-90 s on the deep basis) left an
+ *  UNLABELLED animated skeleton on screen indefinitely with no explanation, no elapsed time and no way
+ *  out. It states plainly what is happening, how long it has been going, and that the table will appear
+ *  by itself — it fabricates and estimates nothing (the elapsed count is this page's own measured wait,
+ *  never a predicted completion time). */
+export function SlowComputeNotice({
+  what,
+  elapsedSeconds,
+}: {
+  what: string;
+  elapsedSeconds: number;
+}) {
+  return (
+    <Card
+      className="flex items-start gap-3 border-warn bg-surface p-5 text-sm"
+      data-testid="slow-compute-notice"
+    >
+      <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-warn" aria-hidden />
+      <div className="space-y-1">
+        <p className="font-medium text-warn">
+          Still computing — <span className="num">{formatElapsedSeconds(elapsedSeconds)}</span> elapsed
+        </p>
+        <p className="text-text-muted">
+          {what} is derived once per dataset from the whole stored forward-return history. The first read
+          after a data change computes it, which can take a minute or two on a deep history; every later
+          read is served from that stored result. The table appears here automatically when it finishes —
+          nothing is shown in the meantime rather than a partial or fabricated result.
+        </p>
       </div>
     </Card>
   );
 }
 
+/** ops-hardening iter-33 (UT-11) — seconds the current fetch has been in flight, ticking once a second
+ *  while `active` and reset to 0 the moment it settles (or a retry starts a new attempt). It measures
+ *  this page's own wait; it neither predicts nor reports backend progress. */
+export function useElapsedSeconds(active: boolean): number {
+  const [seconds, setSeconds] = useState(0);
+  useEffect(() => {
+    setSeconds(0);
+    if (!active) return;
+    const startedAt = Date.now();
+    const timer = setInterval(() => setSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000);
+    return () => clearInterval(timer);
+  }, [active]);
+  return seconds;
+}
+
 /** iter-52 (J-109) — the Factor Lab on its OWN route (`/research/factor-lab`). The page fires the
  *  ALL-FACTORS fetch (`?all=true`) and renders the sortable, expandable all-factors table showing EVERY
  *  config horizon at once as paired (forward-return, max-drawdown) columns — the top-decile edge and its
@@ -4155,7 +4220,13 @@ type RegimeLabState =
  *  and re-presented; the page recomputes nothing and the sort is a pure view transform. */
 export function RegimeLabPage() {
   const [state, setState] = useState<RegimeLabState>({ kind: "loading" });
+  // ops-hardening iter-33 (UT-11): a manual re-fetch counter. The Regime Lab's read is the one lab whose
+  // backing derivation is computed once per dataset over the whole stored history (60-90 s measured on the
+  // deep basis on a cold cache) and can therefore genuinely fail mid-compute — so the error card gets a
+  // Retry that starts a fresh attempt without a full page reload.
+  const [attempt, setAttempt] = useState(0);
   const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
+  const elapsedSeconds = useElapsedSeconds(state.kind === "loading");
 
   useEffect(() => {
     const controller = new AbortController();
@@ -4166,9 +4237,13 @@ export function RegimeLabPage() {
         if (!controller.signal.aborted) setState({ kind: "error" });
       });
     return () => controller.abort();
-  }, [asofCutoff, readiness]);
+  }, [asofCutoff, readiness, attempt]);
 
   const data = state.kind === "ok" ? state.data : null;
+  // The single honest pre-data state (lib/lab-load-panel.ts): a brief load stays a plain skeleton; a wait
+  // past the grace window becomes an explicit, time-stamped "still computing" notice; a failure becomes a
+  // retryable error card. Never an unlabelled skeleton that hangs with no feedback (UT-11).
+  const panel = resolveLabLoadPanel(state.kind, elapsedSeconds);
 
   return (
     <div className="space-y-4">
@@ -4184,8 +4259,16 @@ export function RegimeLabPage() {
         <WarmingState what="The Regime Lab" />
       ) : (
         <>
-          {state.kind === "loading" ? <LabSkeleton /> : null}
-          {state.kind === "error" ? <ResearchError what="The Regime-Lab evidence" /> : null}
+          {panel.kind === "computing" ? (
+            <SlowComputeNotice what="The Regime Lab" elapsedSeconds={panel.elapsedSeconds} />
+          ) : null}
+          {panel.kind === "skeleton" || panel.kind === "computing" ? <LabSkeleton /> : null}
+          {panel.kind === "error" ? (
+            <ResearchError
+              what="The Regime-Lab evidence"
+              onRetry={() => setAttempt((previous) => previous + 1)}
+            />
+          ) : null}
           {data ? (
             <>
               <RegimeLabByLabelTable data={data} scope={scope} />
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index 4ae0c8a1..98881f95 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -33,7 +33,11 @@ from pathlib import Path
 # iters 9/12).
 _VERDICT_RE = re.compile(r"\*\*Browser QA Verdict:\*\*\s*[*_`~\s]*([A-Z_]+)")
 # A results-table data row: | UT-xx | name | type | prio | expected | actual | VERDICT | evidence |
-_ROW_RE = re.compile(r"^\|\s*(UT-[^|]+?)\s*\|(.*)\|\s*$")
+# ops-hardening iter-33: also match `TC-`-prefixed ids — four consecutive evaluators flagged that a
+# QA input file whose rows are ALL `TC-`-prefixed (e.g. a smoke-test report for a launcher/tooling
+# fix) previously failed to parse as rows at all, silently falling back to `compute_overall`'s
+# file-level-verdict path and risking a laundered PASS over a real headline FAIL.
+_ROW_RE = re.compile(r"^\|\s*((?:UT|TC)-[^|]+?)\s*\|(.*)\|\s*$")
 
 
 def _norm_verdict_cell(c: str) -> str:
@@ -273,12 +277,35 @@ def _self_test() -> int:
         rows = parse_rows(ann)
         assert [r["verdict"] for r in rows] == ["PASS", "FAIL", "PASS"], rows
 
+    def t_tc_prefixed_fail_survives():
+        # ops-hardening iter-33 (TC-10) — a QA input file whose ONLY rows use `TC-`-prefixed ids (e.g. a
+        # launcher/tooling smoke-test report, as opposed to the usual `UT-` journey ids) and a headline
+        # FAIL must have that FAIL survive the merge, not get silently laundered into a PASS/SKIPPED
+        # because `_ROW_RE` failed to parse any row and `compute_overall` fell back to the file's own
+        # headline verdict. RED against the pre-iter-33 `UT-`-only regex (every row here is unparsed,
+        # `parse_rows` returns []); GREEN after the `(?:UT|TC)-` widen.
+        tc_only = (
+            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| TC-1 | Stale build rebuilds | smoke | P1 | e | build ran, next start bound to port | PASS | a.png |\n"
+            "| TC-3 | Broken source fails clean | smoke | P1 | e | stale next dev process left running | FAIL | b.png |\n")
+        rows = parse_rows(tc_only)
+        assert [r["test_id"] for r in rows] == ["TC-1", "TC-3"], rows
+        assert rows[1]["verdict"] == "FAIL", rows[1]
+        md = merge([tc_only])
+        assert file_top_verdict(md) == "FAIL", (
+            f"expected the TC-3 FAIL to survive the merge, got headline {file_top_verdict(md)!r}"
+        )
+        assert "## Failed Tests" in md and "TC-3" in md
+
     checks = [("parse_rows", t_parse),
               ("later_wins_override", t_later_wins),
               ("real_fail_survives", t_real_fail_survives),
               ("skipped_only", t_skipped_only),
               ("bold_verdicts", t_bold_verdicts),
-              ("annotated_verdicts", t_annotated_verdicts)]
+              ("annotated_verdicts", t_annotated_verdicts),
+              ("tc_prefixed_fail_survives", t_tc_prefixed_fail_survives)]
     for name, fn in checks:
         check(name, fn)
 
diff --git a/incredible_auto_dev/scripts/measure-perf.sh b/incredible_auto_dev/scripts/measure-perf.sh
index 4c70c70a..aea6da28 100755
--- a/incredible_auto_dev/scripts/measure-perf.sh
+++ b/incredible_auto_dev/scripts/measure-perf.sh
@@ -10,8 +10,10 @@
 #
 # Runs against PROD MODE ONLY (scripts/start-backend.sh / scripts/start-frontend.sh — this script does
 # NOT start them; bring them up first, UNLESS you pass --boot, see below). `next dev`'s per-route
-# compile is not product latency, so this script refuses to measure against a `next dev` frontend (no
-# reliable way to detect that from here, so it just documents the requirement — see the header + --help).
+# compile is not product latency, so measuring against it would be measuring the wrong thing. As of
+# ops-hardening iter-33, `scripts/start-frontend.sh` itself guarantees prod mode (it build-if-stales
+# then execs `next start`, never `next dev`), so bringing the frontend up via that script is sufficient
+# — there is no longer an undetectable dev-mode risk this script needs to separately guard against.
 #
 # iter-5 (J-06 capstone) additions:
 #   --boot   TC-1: measure backend cold-boot wall time (process start -> first GET /api/health HTTP
diff --git a/incredible_auto_dev/scripts/start-frontend.sh b/incredible_auto_dev/scripts/start-frontend.sh
index 4a38ae1e..e2075b6c 100755
--- a/incredible_auto_dev/scripts/start-frontend.sh
+++ b/incredible_auto_dev/scripts/start-frontend.sh
@@ -25,4 +25,42 @@ cd "$REPO_ROOT/apps/frontend"
 export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}"
 export NEXT_PUBLIC_API_PORT="${BACKEND_PORT}"
 
-exec npx next dev -p "$FRONTEND_PORT"
+# ==== build-if-stale, then serve PRODUCTION mode (ops-hardening iter-33) ============================
+# Previously this script execed `npx next dev` unconditionally, despite every other doc calling it
+# "prod mode" (measure-perf.sh's own header, goal.md's J-06 step-1 text) — two consecutive evaluators
+# (iter-31, iter-32) named this the top blocking item, since a browser TTI sweep against `next dev`
+# measures on-demand per-route compilation, not real production page-load time. `next.config.mjs`
+# already wires `NEXT_DIST_DIR` -> `distDir` (default ".next"), so a verification build can target a
+# scratch directory instead of clobbering a live `.next`.
+DIST_DIR="${NEXT_DIST_DIR:-.next}"
+BUILD_ID_FILE="$DIST_DIR/BUILD_ID"
+
+_build_is_stale_or_missing() {
+  # Missing entirely (never built, or a `next dev`-mode `.next` with no BUILD_ID at all) -> stale.
+  # A bare directory-existence check would wrongly treat a dev-mode `.next` as a current prod build.
+  if [[ ! -f "$BUILD_ID_FILE" ]]; then
+    return 0
+  fi
+  # Otherwise stale iff any real source file (excluding node_modules/ and the dist dir itself) is
+  # newer than the build marker — covers apps/frontend's tracked sources plus package.json/
+  # package-lock.json, since none of those live under the excluded paths.
+  local newer
+  newer=$(find . \
+    \( -path "./node_modules" -o -path "./$DIST_DIR" \) -prune -o \
+    -type f -newer "$BUILD_ID_FILE" -print -quit)
+  [[ -n "$newer" ]]
+}
+
+if _build_is_stale_or_missing; then
+  echo "[start-frontend.sh] '$DIST_DIR' build missing or stale relative to sources — running 'next build'..." >&2
+  if ! npx next build; then
+    echo "[start-frontend.sh] next build FAILED (see output above) — refusing to fall back to" \
+         "'next dev' or serve a stale build." >&2
+    exit 1
+  fi
+else
+  echo "[start-frontend.sh] existing '$DIST_DIR' build is current relative to sources — skipping rebuild." >&2
+fi
+# ==== end build-if-stale =============================================================================
+
+exec npx next start -p "$FRONTEND_PORT"
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                           | 151 ++++++++++++++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl   |  47 +++++++
 runs/goal-session-ops-hardening/trace/.next-step  |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl |  11 ++
 4 files changed, 210 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
