# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 1.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (49 diff lines)

```diff
diff --git a/apps/frontend/components/phase-cross-view-card.tsx b/apps/frontend/components/phase-cross-view-card.tsx
index 3adb974e..9b941a0f 100644
--- a/apps/frontend/components/phase-cross-view-card.tsx
+++ b/apps/frontend/components/phase-cross-view-card.tsx
@@ -32,7 +32,18 @@ import {
  * computation, no second endpoint. Exactly one date selector (J-18): the synced two-pane zoom is a view
  * transform, NOT a second date state — this card holds NO date `useState` and adds NO keydown listener;
  * it re-points only with the single global as-of from `useAsOf()`.
+ *
+ * iter-6 (J-06): this card's 3-request `Promise.all` fetch is DEFERRED by `FETCH_STAGGER_MS` after mount
+ * instead of firing immediately. Real-browser measurement (iter-5 dev handoff, reconfirmed by browser-qa)
+ * found `GET /api/indexes?full=true` queued behind Chrome's 6-connections-per-origin cap when this card's
+ * fetch fired the instant the page mounted, alongside the initial Next.js asset burst — 1.68-2.19s
+ * real-browser vs a ≤1.5s budget, even though curl's own baseline (0.79-0.95s) was comfortably under it.
+ * The deferral is pure request TIMING: the same 3 calls, same states, same `AbortController` cleanup —
+ * only WHEN they fire changes. The skeleton (`status === "loading"`, set synchronously before the
+ * deferral) covers the whole deferred window, so there is never a blank gap.
  */
+const FETCH_STAGGER_MS = 250;
+
 export function PhaseCrossViewCard() {
   const { asOf, isHistorical } = useAsOf();
   const [enabled, setEnabled] = usePersistedToggle("trendora.dashboard.phaseCrossView", true);
@@ -46,25 +57,33 @@ export function PhaseCrossViewCard() {
     const controller = new AbortController();
     setStatus("loading");
     const asof = asOf ?? undefined;
-    Promise.all([
-      // full history on every source so the whole market path is the synced context (J-49 precedent).
-      fetchIndexes(undefined, asof, controller.signal, true),
-      fetchRegimeHistory(asof, controller.signal, true).catch(
-        () => ({ asof_date: "", points: [] as RegimePoint[] }),
-      ),
-      // J-97: the full-history causal phase timeline (retrospective=false, full=true).
-      fetchMarketPhase(asof, controller.signal, false, true),
-    ])
-      .then(([ix, rh, mp]) => {
-        setIndexes(ix);
-        setRegimePoints(rh.points);
-        setPhase(mp);
-        setStatus(ix.series.length > 0 ? "ok" : "empty");
-      })
-      .catch(() => {
-        if (!controller.signal.aborted) setStatus("error");
-      });
-    return () => controller.abort();
+    // iter-6 (J-06): stagger this card's on-mount fetch burst behind the page's own initial same-origin
+    // connection burst (see the module-level comment above) — the skeleton above already covers this
+    // window, so the deferral is invisible except for when the network calls actually fire.
+    const timer = window.setTimeout(() => {
+      Promise.all([
+        // full history on every source so the whole market path is the synced context (J-49 precedent).
+        fetchIndexes(undefined, asof, controller.signal, true),
+        fetchRegimeHistory(asof, controller.signal, true).catch(
+          () => ({ asof_date: "", points: [] as RegimePoint[] }),
+        ),
+        // J-97: the full-history causal phase timeline (retrospective=false, full=true).
+        fetchMarketPhase(asof, controller.signal, false, true),
+      ])
+        .then(([ix, rh, mp]) => {
+          setIndexes(ix);
+          setRegimePoints(rh.points);
+          setPhase(mp);
+          setStatus(ix.series.length > 0 ? "ok" : "empty");
+        })
+        .catch(() => {
+          if (!controller.signal.aborted) setStatus("error");
+        });
+    }, FETCH_STAGGER_MS);
+    return () => {
+      window.clearTimeout(timer);
+      controller.abort();
+    };
   }, [enabled, asOf]);
 
   if (!enabled) {
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/perf-budgets.md                            | 164 +++++++++++++++++++++
 .../journey-scripts/J-01.json                      |   2 +-
 runs/goal-session-ops-hardening/telemetry.jsonl    |  24 +++
 runs/goal-session-ops-hardening/trace/.next-step   |   2 +-
 runs/goal-session-ops-hardening/trace/trace.jsonl  |  11 ++
 5 files changed, 201 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
