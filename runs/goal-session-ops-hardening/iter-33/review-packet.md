# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 172 +++++++++++++++++
 runs/goal-session-ops-hardening/.engine.lock/epoch |   2 +-
 runs/goal-session-ops-hardening/.engine.lock/pid   |   2 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-ops-hardening/engine.pid         |   2 +-
 .../state/assumptions.md                           | 203 --------------------
 .../state/assumptions.md.archive.md                | 206 +++++++++++++++++++++
 runs/goal-session-ops-hardening/state/lessons.md   |  78 +-------
 .../state/lessons.md.archive.md                    |  99 ++++++++++
 runs/goal-session-ops-hardening/telemetry.jsonl    |  82 ++++++++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  17 ++
 12 files changed, 589 insertions(+), 280 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
