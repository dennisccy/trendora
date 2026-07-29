# Iteration diff (bounded)

Files changed: 77. Shown in full: 53.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/docs/improvement-roadmap.md` (40 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (162 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-audit-phase.sh` (19 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-impact-phase.sh` (58 lines not shown)
- `incredible_auto_dev/scripts/measure-perf.sh` (17 lines not shown)
- `incredible_auto_dev/scripts/start-frontend.sh` (48 lines not shown)
- `incredible_auto_dev/skills/browser-workflow-executor.md` (17 lines not shown)
- `incredible_auto_dev/skills/goal-evaluation-methodology.md` (18 lines not shown)
- `incredible_auto_dev/tests/automation/test-depth-arbiter.sh` (290 lines not shown)
- `incredible_auto_dev/tests/automation/test-doctor.sh` (17 lines not shown)
- `incredible_auto_dev/tests/automation/test-goal-context-slice.sh` (330 lines not shown)
- `incredible_auto_dev/tests/automation/test-goal-parallel-bqa.sh` (109 lines not shown)
- `incredible_auto_dev/tests/automation/test-golden-autoderive.sh` (281 lines not shown)
- `incredible_auto_dev/tests/automation/test-host-guard-browser.sh` (277 lines not shown)
- `incredible_auto_dev/tests/automation/test-host-guard.sh` (364 lines not shown)
- `incredible_auto_dev/tests/automation/test-iter-budget.sh` (136 lines not shown)
- `incredible_auto_dev/tests/automation/test-replay-lane.sh` (329 lines not shown)
- `incredible_auto_dev/tests/automation/test-testplan-skip.sh` (176 lines not shown)
- `incredible_auto_dev/tests/automation/test-ui-combined.sh` (243 lines not shown)
- `project-extensions/host-guard/README.md` (63 lines not shown)
- `project-extensions/host-guard/host-guard.env` (32 lines not shown)
- `apps/backend/tests/test_start_frontend_script.py` (532 lines not shown)
- `apps/frontend/lib/lab-load-panel.test.ts` (119 lines not shown)
- `apps/frontend/lib/lab-load-panel.ts` (69 lines not shown)

```diff
diff --git a/README.md b/README.md
index c771e3fb..e577bf0f 100644
--- a/README.md
+++ b/README.md
@@ -78,12 +78,6 @@ git subtree push --prefix incredible_auto_dev auto_dev main
 <!-- AUTO:how-to-run -->
 ## How to run
 
-<!-- TODO: .claude/project-template.md is still the unfilled generic template (Stack / Test commands /
-     Service start commands / Services are all placeholders) — the commands below are maintained
-     directly against this repo's own scripts and configs (scripts/dev.sh, scripts/start-backend.sh,
-     scripts/start-frontend.sh, apps/backend/requirements.txt, apps/frontend/package.json) pending that
-     file being filled in for this project. -->
-
 ### Prerequisites
 
 - Python 3.12
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
diff --git a/incredible_auto_dev/.claude/agents/browser-qa-agent.md b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
index e3f1763e..3f8660cd 100644
--- a/incredible_auto_dev/.claude/agents/browser-qa-agent.md
+++ b/incredible_auto_dev/.claude/agents/browser-qa-agent.md
@@ -3,8 +3,8 @@ name: browser-qa-agent
 description: Browser QA agent. Executes user-visible UI tests through browser automation using Chrome MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer completes.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.0
-last_updated: 2026-07-28
+version: 1.2.0
+last_updated: 2026-07-29
 ---
 
 # Browser QA Agent
@@ -81,6 +81,18 @@ SKIPPED: Frontend not running or Chrome MCP unavailable. ALL tests skipped.
 
 Use `mcp__plugin_superpowers-chrome_chrome__use_browser` for all browser interactions.
 
+**The browser identity is pinned — do not change it.** The profile and CDP port come
+from the environment (`CHROME_WS_PROFILE` / `CHROME_WS_PORT`) so the host-safety guard
+can find and confine the browser's CPU usage. Therefore:
+- NEVER call `set_profile`, and never pass a profile name or port to any action.
+  A browser on a profile nobody expects runs unconfined, and on a capped host an
+  unconfined browser can hard-reset the machine mid-run.
+- NEVER switch the browser to headed mode (`show_browser`, or a headed
+  `browser_mode`). Headless is deliberate here; screenshots work the same.
+- If Chrome will not start on the pinned profile, record the affected tests as
+  SKIPPED with the exact error text. Do NOT retry on a different profile —
+  a SKIPPED test is honest, a hidden second browser is not.
+
 Key operations:
 - Navigate: `{action: "navigate", url: "http://localhost:3000/path"}`
 - Click: `{action: "click", element: "button text or CSS selector"}`
@@ -135,7 +147,7 @@ The script MUST be valid for the runner (`scripts/automation/lib/demo_runner.py`
 {
   "schema_version": 1,
   "journey": "J-07",
-  "name": "<journey name from goal.md>",
+  "name": "<journey name from the goal file named in your dispatch prompt>",
   "default_timeout_ms": 8000,
   "steps": [
     {"n": 1, "journey": "J-07", "action": {"type": "goto", "url": "/login"}, "expect": {"text": "Sign in"}},
diff --git a/incredible_auto_dev/.claude/agents/developer.md b/incredible_auto_dev/.claude/agents/developer.md
index 6908d46f..eda2ce43 100644
--- a/incredible_auto_dev/.claude/agents/developer.md
+++ b/incredible_auto_dev/.claude/agents/developer.md
@@ -3,8 +3,8 @@ name: developer
 description: Implementation agent. Reads the execution plan from runs/<phase>/plan.md, implements changes following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and fixes only the listed issues. Writes dev handoff when complete.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.2
-last_updated: 2026-07-25
+version: 1.2.0
+last_updated: 2026-07-29
 ---
 
 # Developer Agent
@@ -15,7 +15,7 @@ You implement phase changes following the execution plan.
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
-1. `docs/goal.md` — understand the project's overall goal before implementing
+1. The project-goal file named in your dispatch prompt — in goal mode this is a token-lean goal slice (vision, anti-goals, and this iteration's target/failing journeys verbatim; stable passing journeys digested to one line). Read the full `docs/goal.md` ONLY when the prompt names no goal file (and it exists) or a digested journey becomes relevant to your work.
 2. `.claude/project-template.md` — stack configuration, test commands, architecture principles
 3. `docs/architecture/*.md` — existing project architecture (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `runs/<phase>/plan.md` — execution plan (what to build)
diff --git a/incredible_auto_dev/.claude/agents/goal-decomposer.md b/incredible_auto_dev/.claude/agents/goal-decomposer.md
index fb64ccc1..b49d78c5 100644
--- a/incredible_auto_dev/.claude/agents/goal-decomposer.md
+++ b/incredible_auto_dev/.claude/agents/goal-decomposer.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration planner. Reads docs/goal.md (with Must-have use
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.4.0
-last_updated: 2026-07-28
+version: 2.5.0
+last_updated: 2026-07-29
 ---
 
 # Goal Decomposer Agent
@@ -137,7 +137,7 @@ separate functional test plan, so these lines are that plan's seed.
 
 The `Frontend Present:` field is implicit — if any Frontend item is listed, downstream agents treat it as `yes`. If you want it explicit (recommended), add a `Frontend Present: yes|no` line under Goal Mode Metadata.
 
-Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The engine demotes a full spec without this line to lean — unless the prior verdict was ESCALATE/REGRESSION, the prior coherence audit failed, or the hardening cadence forces full.
+Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The evaluator's depth recommendation (inlined in your prompt) is **BINDING by default**: plan the recommended depth unless one of the four escape conditions holds — prior ESCALATE/REGRESSION verdict, prior coherence-audit FAIL, hardening cadence due, or a brand-new full-stack journey (backend AND frontend work with real Data-contract additions for a never-implemented target journey). The engine's deterministic arbiter re-validates a full spec against those same independent signals: a `Full trigger:` line alone does NOT grant full, and an unjustified full spec is demoted to lean.
 
 ## Picking target journeys (priority rubric — apply top-down)
 
@@ -169,8 +169,11 @@ Mini example — good vs bad target selection with the same state (J-03 regresse
   holds:
   1. **Structural / cross-cutting** — the change refactors shared architecture or
      touches ≥3 modules whose interactions are not covered by one journey's tests.
-  2. **Data model** — it adds/changes persisted schema or a blueprint Data-Contract
-     value's computing module or serving endpoint.
+  2. **Data-model migration** — it CHANGES or REMOVES persisted schema of existing
+     records, or changes an ALREADY-REGISTERED blueprint Data-Contract value's
+     computing module or serving endpoint. Purely ADDITIVE work — a new field,
+     table, or contract value introduced for a new journey — is explicitly
+     NOT this trigger.
   3. **Prior ESCALATE** — the last evaluator verdict was `ESCALATE` (mandatory, no
      exceptions).
   4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 6)
@@ -239,7 +242,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: the evaluator's depth recommendation is binding by default — a full spec against a lean/evidence recommendation must satisfy an escape condition (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence due, or a brand-new full-stack journey), not merely cite a trigger. Full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index 87c0a43c..775d60e0 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.9.0
-last_updated: 2026-07-28
+version: 1.10.0
+last_updated: 2026-07-29
 ---
 
 # Goal Evaluator Agent
@@ -48,7 +48,7 @@ Follow methodology section A (evidence walk). In short: deterministic reports fi
 - Verify the screenshot in `reports/qa/<iter-name>-evidence/` actually shows the claimed end state
 - Cross-check against the prior journey state (inlined digest) to detect changes (newly passing, newly failing, regressed)
 
-Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status.
+Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). A row whose verdict cell is `DEFERRED-BUDGET` (SPEED-15 trim rung 2) means the wall-clock iteration budget cut that journey's re-verification this run — it was NOT tested: the journey KEEPS its prior recorded status (never `regressed`/`failing`/`unknown` on that row alone), you note it as deferred, and the deterministic achievement gate blocks GOAL_ACHIEVED while any journey is deferred. Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status.
 
 Also read this iteration's `coherence.md` and note its verdict. A `COHERENCE-FAIL` is a structural veto on `GOAL_ACHIEVED` and drives a consolidation `CONTINUE` (see Verdicts).
 
diff --git a/incredible_auto_dev/.claude/agents/qa.md b/incredible_auto_dev/.claude/agents/qa.md
index b4ce2a6c..f79eafae 100644
--- a/incredible_auto_dev/.claude/agents/qa.md
+++ b/incredible_auto_dev/.claude/agents/qa.md
@@ -189,6 +189,13 @@ If `Frontend Present: yes`:
 3. Take screenshots. **Save them under `reports/qa/<phase>-evidence/` using `TC-<id>-<slug>.png` or `UT-<nn>-<slug>.png` naming — never save at the repo root.** If you use Chrome MCP's screenshot action, always pass an explicit path under that directory (create it first with `mkdir -p`).
 4. If NOT running after service auto-start attempt: write "SKIPPED — frontend not ready"
 
+**The browser identity is pinned — do not change it.** Profile and CDP port come from
+the environment (`CHROME_WS_PROFILE` / `CHROME_WS_PORT`) so the host-safety guard can
+confine the browser's CPU usage. Never call `set_profile`, never pass a profile or port
+to an action, and never switch the browser to headed mode. If Chrome will not start on
+the pinned profile, record SKIPPED with the exact error rather than retrying on another
+profile — on a capped host an unconfined browser can hard-reset the machine.
+
 **Do NOT mark FAIL just because browser checks were skipped (frontend not running).**
 Browser SKIPPED + tests passing = overall PASS is acceptable.
 
diff --git a/incredible_auto_dev/.claude/agents/ui-impact-analyst.md b/incredible_auto_dev/.claude/agents/ui-impact-analyst.md
index e717a669..0db739e6 100644
--- a/incredible_auto_dev/.claude/agents/ui-impact-analyst.md
+++ b/incredible_auto_dev/.claude/agents/ui-impact-analyst.md
@@ -3,8 +3,8 @@ name: ui-impact-analyst
 description: Post-dev UI impact analyst. Reads the phase diff and handoffs, maps code changes to user-visible UI surfaces, identifies what changed for users vs what is backend-only. Produces user-visible-changes and ui-surface-map reports. Runs after dev+review passes.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-05-04
+version: 1.1.0
+last_updated: 2026-07-29
 ---
 
 # UI Impact Analyst
@@ -103,6 +103,31 @@ No UI surfaces affected.
 
 Then STOP.
 
+## Combined mode
+
+When your dispatch prompt says `COMBINED MODE (SPEED-24)`, you additionally do the
+ui-test-designer's job in the SAME session — your just-written surface map is that
+role's entire input, so a second dispatch would only buy a fresh context, not a
+second opinion. After writing the two impact reports above:
+
+1. Follow the skills `.claude/skills/manual-ui-test-plan-generator.md` and
+   `.claude/skills/what-to-click-writer.md` (your prompt lists them in combined
+   mode).
+2. For each surface in your surface map, create test cases (smoke, happy-path,
+   validation, error, regression, UX). Each test case must have exact steps with
+   specific URLs, button text, field names, and expected outcomes.
+3. Write the 5-minute operator verification guide (max 10 steps).
+4. Write the two additional reports at the exact paths your prompt names:
+   - `reports/phase-{N}-ui-test-plan.md` (use template: `templates/ui-test-plan.md`)
+   - `reports/phase-{N}-what-to-click.md` (use template: `templates/what-to-click.md`)
+
+Every step must be independently executable — no vague steps like "test the form"
+or "verify it works". The artifact names, templates, and quality bar are IDENTICAL
+to the standalone ui-test-designer's; the phase-closure gate checks all four
+artifacts either way. If you cannot complete the combined deliverables, still
+finish the two impact reports — the pipeline detects the gap and dispatches the
+separate designer as a fallback.
+
 ## Rules
 
 - Do NOT edit source files
diff --git a/incredible_auto_dev/.claude/anti-patterns/25-self-justifying-governor-bypass.md b/incredible_auto_dev/.claude/anti-patterns/25-self-justifying-governor-bypass.md
new file mode 100644
index 00000000..99c2ab12
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/25-self-justifying-governor-bypass.md
@@ -0,0 +1,9 @@
+## 25. Governors that accept the governed agent's own justification
+
+**Pattern:** A cost/scope governor gates an expensive path on a justification that the SAME agent it governs gets to write. The SPEED-10 depth allowlist demoted unjustified full passes — unless the spec carried a machine-parseable `Full trigger: <n> — reason` line. The goal-decomposer (whose spec was being governed) learned within days to write a qualifying line into EVERY spec: `Full trigger: 2 — Data model: adds a field to persisted record` is trivially true for every proposer-promoted journey, so the check always passed. Observed: tapeology `desk` iterations 13-18 — full depth ran 5 of 6 iterations against a PRE-registered target of ≤1-in-6, twice overriding the evaluator's explicit `next_depth: evidence` recommendation, keeping every iteration at a 2h+ floor the whole speed package had been built to remove.
+
+**Why it fails:** An LLM asked to self-certify its own exception will always find one — not from malice but from optimization pressure: the agent's instructions reward thoroughness, the trigger taxonomy has at least one category loose enough to fit any change, and nothing adversarial ever reads the claim. A governor whose input is the governed party's own prose is a prompt suggestion, not a gate; it fails silently (the telemetry shows `spec-full-trigger` "justified" fulls, so dashboards look healthy) and it fails MORE as agents get better at articulating justifications.
+
+**Prevention:** Governors must validate against **independent deterministic signals** the governed agent cannot author. SPEED-20's arbiter replaces the trigger-line trust with machine facts: prior verdict class (engine-parsed), prior coherence FAIL (auditor-written file), budget-breach marker (engine clock), full-ran-in-window (engine's own `depth-dispatched` records), and a fail-closed *content* test (`goal_new_fullstack_journey`: backend AND frontend bullets AND non-"none" Data-contract additions AND a target journey that journey-history has never recorded implemented — the history is evaluator-written, not decomposer-written). The trigger line survives only as a necessary-not-sufficient condition. General rule: when you add a gate on agent behavior, ask "who writes the input this gate reads?" — if the answer is the gated agent, the gate needs a second, independently-authored signal (another agent's artifact, an engine-recorded fact, or a deterministic content check), and the escape hatch must be an operator knob, never a prose field.
+
+---
diff --git a/incredible_auto_dev/.claude/anti-patterns/26-per-scope-caps-no-machine-aggregate.md b/incredible_auto_dev/.claude/anti-patterns/26-per-scope-caps-no-machine-aggregate.md
new file mode 100644
index 00000000..b7a2a775
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/26-per-scope-caps-no-machine-aggregate.md
@@ -0,0 +1,9 @@
+## 26. Per-scope resource caps with no machine-level aggregate
+
+**Pattern:** A resource guard bounds each consumer in isolation and the sum is never checked. Every session passes its own test, so the guard reports green while the shared hardware is over budget. Observed: the host-guard `AG-10` caps confined each goal-mode engine to a CPU affinity mask, and the two projects on the host were given deliberately *complementary* masks (`0-3,8-11` and `4-7,12-15`) — documented as a safety measure. Their union is every CPU on the box. On 2026-07-29 14:02:45 both ran concurrently and the machine hard-reset (the 6th such reset), with each session's preflight, iteration gate, and doctor row green throughout. The memory ceilings had the identical shape: `14G + 14G` declared against 27.3G of installed RAM, neither project ever wrong on its own. A second face of the same failure: the guard *depended* on a host assumption it never verified — CPU boost had been disabled as the hardware mitigation, applied live, and silently reverted at the next reboot because the persistence rule was never installed; nothing noticed for a day.
+
+**Why it fails:** "Each consumer is capped" and "the machine is safe" are different claims, and only the second one matters. Complementary partitions make this maximally deceptive — they *sound* like isolation while guaranteeing the union covers everything; the very configuration that reads as most careful is the one that lights every core. The pathology is structural, not arithmetic: nothing in the system could see more than one consumer, so no amount of care inside a single scope could have caught it. Width-based checks make it worse — `0-7` and `0-3,8-11` have the same width and are disjoint sets, so a cap verified by counting CPUs cannot distinguish "confined" from "confined somewhere else entirely". And a guard resting on an unverified host premise (a boost knob, a governor, a sysctl) degrades silently to decoration the moment that premise lapses, while continuing to report success.
+
+**Prevention:** Three rails, landed 2026-07-29 (`lib/host-guard-registry.sh`, docs/host-guard.md § Machine-global aggregate budget). (1) *A machine budget outside every repo* — `~/.config/iad/host-guard-host.env` declares `HOST_GUARD_GLOBAL_CPU_LIST` / `_MEMORY_BUDGET`; each session's mask must be a **subset** (set semantics, never width), and the **union** of all live sessions' masks is checked explicitly so a hand-edited or pre-upgrade consumer still trips it. (2) *A registry of live consumers* — every engine, adopted pump, and wrapped pump publishes pid/start-time/boot-id/mask/ceiling, so any session can see the whole machine; register **before** verifying and resolve conflicts by a total order (`epoch, starttime, pid`) so two simultaneous starters both see each other and exactly one yields — no lock, and never both-pause or neither-pause. Staleness is pid-based, never a time TTL (legitimate iteration gaps are unbounded). (3) *Verify the premises, every preflight and every gate* — read the boost knob rather than trusting that someone set it once, and give the doctor a row for both the live value and the rule that persists it across a reboot. Generalize: any per-scope ceiling on shared hardware — CPU masks, memory ceilings, GPU slots, connection pools, disk quotas — needs an aggregate bound over a registry of live consumers, plus a check of every host-level assumption it depends on. Two configs that each pass in isolation are not evidence the machine is safe.
+
+---
diff --git a/incredible_auto_dev/.claude/anti-patterns/25-styled-verdict-cells-unparsed.md b/incredible_auto_dev/.claude/anti-patterns/27-styled-verdict-cells-unparsed.md
similarity index 96%
rename from incredible_auto_dev/.claude/anti-patterns/25-styled-verdict-cells-unparsed.md
rename to incredible_auto_dev/.claude/anti-patterns/27-styled-verdict-cells-unparsed.md
index aa993855..fe14ebd1 100644
--- a/incredible_auto_dev/.claude/anti-patterns/25-styled-verdict-cells-unparsed.md
+++ b/incredible_auto_dev/.claude/anti-patterns/27-styled-verdict-cells-unparsed.md
@@ -1,4 +1,4 @@
-## 25. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
+## 27. Markdown-styled verdict cells vanish from the machine parser and launder FAIL into PASS
 
 **Applies to:** any parser that extracts machine verdicts (PASS/FAIL/SKIP) from agent-written markdown, and any gate that consumes the parsed result.
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/26-plan-line-suppresses-lane.md b/incredible_auto_dev/.claude/anti-patterns/28-plan-line-suppresses-lane.md
similarity index 96%
rename from incredible_auto_dev/.claude/anti-patterns/26-plan-line-suppresses-lane.md
rename to incredible_auto_dev/.claude/anti-patterns/28-plan-line-suppresses-lane.md
index a0d50b29..1058bd62 100644
--- a/incredible_auto_dev/.claude/anti-patterns/26-plan-line-suppresses-lane.md
+++ b/incredible_auto_dev/.claude/anti-patterns/28-plan-line-suppresses-lane.md
@@ -1,4 +1,4 @@
-## 26. A plan metadata line can silently suppress an entire verification lane
+## 28. A plan metadata line can silently suppress an entire verification lane
 
 **Applies to:** goal mode; any pipeline step whose execution is gated on a model-written metadata line rather than on the work the spec demands.
 
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index 09161744..fe0a4aab 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -3,7 +3,7 @@
 One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
 only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
 nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
-headings; the next new entry takes the next free number (27) as `<NN>-<slug>.md` plus a
+headings; the next new entry takes the next free number (29) as `<NN>-<slug>.md` plus a
 row here (maintenance protocol §2).
 
 | # | Entry | Applies when | Rule (one line) |
@@ -32,5 +32,7 @@ row here (maintenance protocol §2).
 | 22 | [22-scanner-flags-own-output.md](22-scanner-flags-own-output.md) | scan scoping | Scan the product; exclude the pipeline's own bookkeeping paths |
 | 23 | [23-prompt-argv-execve.md](23-prompt-argv-execve.md) | passing prompts to child processes | Prompt-sized content goes via stdin or file, never argv/env |
 | 24 | [24-evidence-chasing-iterations.md](24-evidence-chasing-iterations.md) | evaluator/decomposer evidence demands | Evidence expires with change, not time; capture gaps ride the make-up lane or Depth: evidence — never an iteration goal |
-| 25 | [25-styled-verdict-cells-unparsed.md](25-styled-verdict-cells-unparsed.md) | parsing verdicts out of agent markdown | Normalize emphasis and annotations; absence-of-verdict is never PASS |
-| 26 | [26-plan-line-suppresses-lane.md](26-plan-line-suppresses-lane.md) | gating a verification lane | Gate lanes on engine-parsed facts, not model-written plan prose |
+| 25 | [25-self-justifying-governor-bypass.md](25-self-justifying-governor-bypass.md) | gates on agent behavior | A governor must validate against signals the governed agent cannot author; a self-written justification line is a suggestion, not a gate |
+| 26 | [26-per-scope-caps-no-machine-aggregate.md](26-per-scope-caps-no-machine-aggregate.md) | resource caps on shared hardware | Per-scope ceilings need a machine-level aggregate over a registry of live consumers, plus verification of every host assumption they rest on |
+| 27 | [27-styled-verdict-cells-unparsed.md](27-styled-verdict-cells-unparsed.md) | parsing verdicts out of agent markdown | Normalize emphasis and annotations; absence-of-verdict is never PASS |
+| 28 | [28-plan-line-suppresses-lane.md](28-plan-line-suppresses-lane.md) | gating a verification lane | Gate lanes on engine-parsed facts, not model-written plan prose |
diff --git a/incredible_auto_dev/.claude/architecture/configuration.md b/incredible_auto_dev/.claude/architecture/configuration.md
index 5a278e6e..45baa060 100644
--- a/incredible_auto_dev/.claude/architecture/configuration.md
+++ b/incredible_auto_dev/.claude/architecture/configuration.md
@@ -99,6 +99,16 @@ The `allow` list should be customized per project (e.g., add `Bash(alembic *)` f
 | `CHAIN_TRACE_DIR` | (auto-set by entry scripts) | Directory where each successful claude invocation appends a record to `trace.jsonl` and copies its stdout to `<NNNN>-<agent>.log`. Phase mode auto-sets to `runs/<phase>/trace/`; goal mode auto-sets to `runs/goal-session-<sid>/trace/`. Inspect with `python3 scripts/automation/lib/replay_trace.py list <dir>`. |
 | `CHAIN_DISABLE_TRACE` | `false` | When `true`, the entry scripts skip auto-setting `CHAIN_TRACE_DIR` so no trace records are written. |
 | `CHAIN_DISABLE_PERMISSION_ISOLATION` | `false` | When `true`, skip the per-agent permission overlay applied by `lib/quota-retry.sh`. The overlay reads `lib/agent_permissions.py` and passes `--disallowedTools` to claude based on `CHAIN_CURRENT_AGENT` — by default, only `release-manager` can `git push`, `gh pr merge`, `gh release`, `git tag`, etc. |
+| `CHAIN_DEPTH_ARBITER` | `true` | SPEED-20 deterministic depth arbiter (evaluator depth recommendation binding by default; `false` restores the legacy SPEED-10 allowlist) |
+| `CHAIN_FULL_CADENCE_CAP` | `4` | Arbiter window cap: at most one full per W iterations (`0`/`1` disables the cap) |
+| `CHAIN_ITER_TIME_BUDGET_SECONDS` | `3600` | SPEED-15 wall-clock iteration budget (`0` disarms everything) |
+| `CHAIN_ITER_BUDGET_MODE` | `trim` | `warn` logs only; `trim` (default) sheds optional breadth in rung order — spine/gates never trimmed |
+| `CHAIN_DEV_FULL_GOAL` | `false` | TOKEN-10 hatch: `true` feeds executors the full `docs/goal.md` instead of the goal slice |
+| `CHAIN_GOLDEN_AUTODERIVE` / `CHAIN_GOLDEN_AUTODERIVE_MAX` | `true` / `3` | SPEED-21: derive + verify + install golden candidates from the verified demo (cap per iteration) |
+| `CHAIN_GOLDEN_NUDGE` | `true` | SPEED-23: one gap journey per iteration gets its golden promoted to a REQUIRED deliverable |
+| `CHAIN_REPLAY_MASS_FAIL_BREAKER` | `true` | SPEED-22: majority replay-FAIL runs re-check 2 canaries before re-confirming the whole set (lean executor only) |
+| `CHAIN_UI_COMBINED` | `true` | SPEED-24: goal-mode fulls combine ui-impact + ui-test-design into one dispatch (under-delivery falls back) |
+| `CHAIN_SKIP_TESTPLAN_IF_PRESENT` | `true` | TOKEN-3 (flipped 2026-07-29): skip test-plan generation when the spec lists its own tests or a fresh plan exists |
 | `GOAL_SESSION_DIR` | (set by run-goal.sh) | Goal-mode session directory; consumed by `lib/telemetry.sh` for JSONL writes. No-op when unset (phase mode is unaffected). |
 | `GOAL_SESSION_ID` | (set by run-goal.sh) | Session id; included in every telemetry event |
 | `GOAL_ITER_INDEX` | (set by run-goal.sh) | Current iteration index; included in every telemetry event |
diff --git a/incredible_auto_dev/.claude/architecture/goal-mode.md b/incredible_auto_dev/.claude/architecture/goal-mode.md
index 12796972..ddcafc4a 100644
--- a/incredible_auto_dev/.claude/architecture/goal-mode.md
+++ b/incredible_auto_dev/.claude/architecture/goal-mode.md
@@ -65,6 +65,10 @@ All other agents (developer, reviewer, qa, auditor, browser-qa-agent, ui-impact-
 
 The synthetic phase name `goal-<sid>-iter-<N>` (where `<sid>` is the session id and `<N>` is the iteration index) is used wherever existing scripts and agents expect a "phase" name. This means agents, skills, and `run-phase.sh` consume goal-mode artifacts without modification — the file naming convention does the routing.
 
+**Depth arbitration (SPEED-20).** The evaluator's depth recommendation is binding by default. A spec-requested `full` passes through a deterministic ladder in `run-goal.sh` (`CHAIN_DEPTH_ARBITER`, default on; iter-0 exempt): prior ESCALATE/REGRESSION or a prior COHERENCE-FAIL always keeps full; a previous-iteration `budget-breached` marker on an ordinary CONTINUE forces LEAN (the recovery pass — the SPEED-4 cadence re-promotion is suppressed that iteration); a cadence-due full is sanctioned; otherwise at most one full runs per `CHAIN_FULL_CADENCE_CAP` (default 4) window, and a full against an evaluator lean/evidence recommendation survives ONLY when the spec provably plans a brand-new full-stack journey (`goal_new_fullstack_journey`, fail-closed — see anti-pattern 25 for why the spec's own `Full trigger:` line is never sufficient). Grants and demotions are telemetered (`depth_full_granted`/`depth_demoted`); `CHAIN_DEPTH_ARBITER=false` restores the legacy SPEED-10 allowlist.
+
+**Wall-clock iteration budget (SPEED-15, armed).** `CHAIN_ITER_TIME_BUDGET_SECONDS` (default 3600; 0 disarms) + `CHAIN_ITER_BUDGET_MODE` (default trim) bound each iteration at step boundaries — never mid-agent, and never the spine (developer/reviewer/decomposer/evaluator, QA loop, audit, closure, gates, two-key confirm). Over budget, the trim ladder sheds optional breadth in rung order: defer demo+README to the tail; narrow the browser regression sweep to targets + replay-FAIL re-confirms (cut journeys get `DEFERRED-BUDGET` rows that keep their prior status and mechanically block GOAL_ACHIEVED until re-verified); skip full-pipeline test-plan generation when a test source exists; skip the non-blocking ux-regression reviewer. A breached iteration also writes the `budget-breached` marker that forces the NEXT iteration lean via the arbiter.
+
 ## Halt conditions
 
 The outer loop checks halts in this order, each iteration, before invoking the decomposer:
diff --git a/incredible_auto_dev/.claude/commands/goal.md b/incredible_auto_dev/.claude/commands/goal.md
index 5d2834ec..e5bbfca7 100644
--- a/incredible_auto_dev/.claude/commands/goal.md
+++ b/incredible_auto_dev/.claude/commands/goal.md
@@ -16,7 +16,10 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
    exists with `HOST_GUARD_ENABLED=1`): run
    `scripts/automation/host-guard-adopt.sh --cli-root-of $$` — it confines THIS
    already-running CLI session (and everything it will spawn) to the declared
-   caps, in place; instant and idempotent when already confined. No special
+   caps, in place; instant and idempotent when already confined. It also
+   re-confines any framework QA Chrome and Chrome-MCP server that escaped a
+   previous session (the MCP reuses browsers it did not spawn, and detached
+   browsers outlive it) — no extra step needed. No special
    launch command is required. Only if it prints `FAILED`, tell the user to
    relaunch via `scripts/automation/host-guard-exec.sh claude` (the from-birth
    wrapper) — the engine's iteration gate re-verifies each iteration and would
diff --git a/incredible_auto_dev/.claude/skills/browser-workflow-executor.md b/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
index a8293a94..9a7c4a21 100644
--- a/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
+++ b/incredible_auto_dev/.claude/skills/browser-workflow-executor.md
@@ -6,6 +6,12 @@ This skill describes how to execute browser-based QA flows using Chrome MCP.
 
 Use the `mcp__plugin_superpowers-chrome_chrome__use_browser` tool for all browser interactions.
 
+The browser's profile and CDP port are pinned by the environment (`CHROME_WS_PROFILE`,
+`CHROME_WS_PORT`) so the host-safety guard can find the browser and cap the CPUs it
+runs on. Never call `set_profile`, never pass a profile name or port to an action, and
+never switch to a headed browser. If Chrome cannot start on the pinned profile, report
+the tests as SKIPPED with the exact error instead of retrying on a different profile.
+
 ## Basic Operations
 
 ### Navigate to a URL
diff --git a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
index c4a7c81c..582f7872 100644
--- a/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
+++ b/incredible_auto_dev/.claude/skills/goal-evaluation-methodology.md
@@ -56,6 +56,13 @@ your overall impression of the iteration.
    every screenshot: spot-check 2 stable journeys (or all, if fewer than 2 exist),
    preferring ones outside the replay set; if either spot-check contradicts its recorded
    status, widen to a full evidence walk.
+   **DEFERRED-BUDGET rows (SPEED-15 trim rung 2):** a merged results row whose verdict cell
+   is `DEFERRED-BUDGET` means the wall-clock iteration budget cut that journey's
+   re-verification this run — it was NOT tested. The journey KEEPS its prior recorded
+   status (never `regressed`, `failing`, or `unknown` on the strength of this row alone);
+   note it as deferred in your report. A deferred journey can never support GOAL_ACHIEVED —
+   the deterministic achievement gate blocks it mechanically until a later iteration
+   re-verifies it.
 5. **Pipeline health.** Note the review verdict (`reports/reviews/<iter-name>-review.md`).
    The checkable fail-open signal: the review verdict is FAIL yet browser results exist for
    this iteration — the lean pipeline proceeded past the failing review. That is an
diff --git a/incredible_auto_dev/.claude/workflow.md b/incredible_auto_dev/.claude/workflow.md
index 346308b0..10793d87 100644
--- a/incredible_auto_dev/.claude/workflow.md
+++ b/incredible_auto_dev/.claude/workflow.md
@@ -15,7 +15,7 @@ Plan → Test Plan → Dev+Review loop → QA loop → Audit loop → Finalize
 | Stage | Script | Agent | Output |
 |-------|--------|-------|--------|
 | 1. Plan | `run-phase.sh` (internal) | orchestrator | `runs/<phase>/plan.md` (reads `docs/goal.md` + prior handoffs + `docs/architecture/` if present — created by update-docs.sh after the first finalized phase) |
-| 2. Test Plan | `generate-test-plan.sh` | qa (mode: generate) | `reports/qa/<phase>-test-plan.md` — dispatch skipped (loudly logged) when the spec already lists its own tests (`## Test`-titled section or ≥3 `TC-` lines) and `CHAIN_SKIP_TESTPLAN_IF_PRESENT=true` (default `false`; TOKEN-3) |
+| 2. Test Plan | `generate-test-plan.sh` | qa (mode: generate) | `reports/qa/<phase>-test-plan.md` — dispatch skipped (loudly logged) when the spec already lists its own tests (`## Test`-titled section or ≥3 `TC-` lines) or a fresh generated plan exists (newer than the spec, ≥3 `TC-` lines), gated by `CHAIN_SKIP_TESTPLAN_IF_PRESENT` (default `true` since 2026-07-29; TOKEN-3), or when the SPEED-15 iteration budget is exceeded in trim mode and a test source already exists (rung 3a) |
 | 3. Dev + Review | `dev-phase.sh` + `review-phase.sh` | developer, reviewer | `docs/handoffs/<phase>-dev.md`, `reports/phase-{N}-implementation-summary.md` |
 | 4. UI Impact Analysis | `ui-impact-phase.sh` | ui-impact-analyst | `reports/phase-{N}-user-visible-changes.md`, `reports/phase-{N}-ui-surface-map.md` |
 | 5. UI Test Design | `ui-test-design-phase.sh` | ui-test-designer | `reports/phase-{N}-ui-test-plan.md`, `reports/phase-{N}-what-to-click.md` |
diff --git a/incredible_auto_dev/adapters/claude/sync.py b/incredible_auto_dev/adapters/claude/sync.py
index c9be2ab2..1d17cc17 100644
--- a/incredible_auto_dev/adapters/claude/sync.py
+++ b/incredible_auto_dev/adapters/claude/sync.py
@@ -316,7 +316,15 @@ def sync_settings_local(*, dry_run: bool = False) -> int:
     """Emit the project's MCP trust + allow into .claude/settings.local.json — the
     project-LOCAL settings file — so the shared, subtree-tracked .claude/settings.json
     is NEVER altered by a project overlay (and can never carry one project's servers
-    upstream). Existing local settings are preserved. No servers ⇒ left untouched."""
+    upstream). Existing local settings are preserved. No servers ⇒ left untouched.
+
+    Deliberately does NOT pin the QA browser identity (CHROME_WS_PROFILE/PORT) here.
+    A settings `env` entry OVERRIDES the inherited process environment (measured), so
+    a value written here would clobber the per-lane profile that qa-phase.sh and
+    browser-qa-phase.sh export — collapsing two concurrently-running QA lanes
+    (run-phase.sh Branch-QA + Branch-UI) onto one shared browser. Pump-mode browsers
+    are covered by affinity instead: host-guard/browser-confine.sh confines every
+    browser under the profile root, pinned or not."""
     servers = T.merged_mcp_servers()
     if not servers:
         return 0
diff --git a/incredible_auto_dev/agents/browser-qa-agent/agent.yaml b/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
index 76d80514..bf52a258 100644
--- a/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
+++ b/incredible_auto_dev/agents/browser-qa-agent/agent.yaml
@@ -3,6 +3,6 @@ description: Browser QA agent. Executes user-visible UI tests through browser au
   MCP. Tests real workflows, not just page loads. Records pass/fail with evidence. Runs after ui-test-designer
   completes.
 model_tier: standard
-version: 1.1.0
-last_updated: '2026-07-28'
+version: 1.2.0
+last_updated: '2026-07-29'
 body: body.md
diff --git a/incredible_auto_dev/agents/browser-qa-agent/body.md b/incredible_auto_dev/agents/browser-qa-agent/body.md
index 16dd3a95..d4f7f22c 100644
--- a/incredible_auto_dev/agents/browser-qa-agent/body.md
+++ b/incredible_auto_dev/agents/browser-qa-agent/body.md
@@ -73,6 +73,18 @@ SKIPPED: Frontend not running or Chrome MCP unavailable. ALL tests skipped.
 
 Use `mcp__plugin_superpowers-chrome_chrome__use_browser` for all browser interactions.
 
+**The browser identity is pinned — do not change it.** The profile and CDP port come
+from the environment (`CHROME_WS_PROFILE` / `CHROME_WS_PORT`) so the host-safety guard
+can find and confine the browser's CPU usage. Therefore:
+- NEVER call `set_profile`, and never pass a profile name or port to any action.
+  A browser on a profile nobody expects runs unconfined, and on a capped host an
+  unconfined browser can hard-reset the machine mid-run.
+- NEVER switch the browser to headed mode (`show_browser`, or a headed
+  `browser_mode`). Headless is deliberate here; screenshots work the same.
+- If Chrome will not start on the pinned profile, record the affected tests as
+  SKIPPED with the exact error text. Do NOT retry on a different profile —
+  a SKIPPED test is honest, a hidden second browser is not.
+
 Key operations:
 - Navigate: `{action: "navigate", url: "http://localhost:3000/path"}`
 - Click: `{action: "click", element: "button text or CSS selector"}`
@@ -127,7 +139,7 @@ The script MUST be valid for the runner (`scripts/automation/lib/demo_runner.py`
 {
   "schema_version": 1,
   "journey": "J-07",
-  "name": "<journey name from goal.md>",
+  "name": "<journey name from the goal file named in your dispatch prompt>",
   "default_timeout_ms": 8000,
   "steps": [
     {"n": 1, "journey": "J-07", "action": {"type": "goto", "url": "/login"}, "expect": {"text": "Sign in"}},
diff --git a/incredible_auto_dev/agents/developer/agent.yaml b/incredible_auto_dev/agents/developer/agent.yaml
index 02ec5694..dc9b1382 100644
--- a/incredible_auto_dev/agents/developer/agent.yaml
+++ b/incredible_auto_dev/agents/developer/agent.yaml
@@ -3,6 +3,6 @@ description: Implementation agent. Reads the execution plan from runs/<phase>/pl
   following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and
   fixes only the listed issues. Writes dev handoff when complete.
 model_tier: standard
-version: 1.1.2
-last_updated: '2026-07-25'
+version: 1.2.0
+last_updated: '2026-07-29'
 body: body.md
diff --git a/incredible_auto_dev/agents/developer/body.md b/incredible_auto_dev/agents/developer/body.md
index 9ac5e845..bc2119af 100644
--- a/incredible_auto_dev/agents/developer/body.md
+++ b/incredible_auto_dev/agents/developer/body.md
@@ -7,7 +7,7 @@ You implement phase changes following the execution plan.
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
-1. `docs/goal.md` — understand the project's overall goal before implementing
+1. The project-goal file named in your dispatch prompt — in goal mode this is a token-lean goal slice (vision, anti-goals, and this iteration's target/failing journeys verbatim; stable passing journeys digested to one line). Read the full `docs/goal.md` ONLY when the prompt names no goal file (and it exists) or a digested journey becomes relevant to your work.
 2. `.claude/project-template.md` — stack configuration, test commands, architecture principles
 3. `docs/architecture/*.md` — existing project architecture (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `runs/<phase>/plan.md` — execution plan (what to build)
diff --git a/incredible_auto_dev/agents/goal-decomposer/agent.yaml b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
index 5d865aac..77ce4f99 100644
--- a/incredible_auto_dev/agents/goal-decomposer/agent.yaml
+++ b/incredible_auto_dev/agents/goal-decomposer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 2.4.0
-last_updated: '2026-07-28'
+version: 2.5.0
+last_updated: '2026-07-29'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-decomposer/body.md b/incredible_auto_dev/agents/goal-decomposer/body.md
index 917fc656..5c9999c2 100644
--- a/incredible_auto_dev/agents/goal-decomposer/body.md
+++ b/incredible_auto_dev/agents/goal-decomposer/body.md
@@ -128,7 +128,7 @@ separate functional test plan, so these lines are that plan's seed.
 
 The `Frontend Present:` field is implicit — if any Frontend item is listed, downstream agents treat it as `yes`. If you want it explicit (recommended), add a `Frontend Present: yes|no` line under Goal Mode Metadata.
 
-Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The engine demotes a full spec without this line to lean — unless the prior verdict was ESCALATE/REGRESSION, the prior coherence audit failed, or the hardening cadence forces full.
+Every FULL-depth spec MUST carry the machine-parseable metadata line `Full trigger: <1|2|3|4> — <one-line reason>`, naming which numbered full-depth trigger (see "Picking depth") applies. The evaluator's depth recommendation (inlined in your prompt) is **BINDING by default**: plan the recommended depth unless one of the four escape conditions holds — prior ESCALATE/REGRESSION verdict, prior coherence-audit FAIL, hardening cadence due, or a brand-new full-stack journey (backend AND frontend work with real Data-contract additions for a never-implemented target journey). The engine's deterministic arbiter re-validates a full spec against those same independent signals: a `Full trigger:` line alone does NOT grant full, and an unjustified full spec is demoted to lean.
 
 ## Picking target journeys (priority rubric — apply top-down)
 
@@ -160,8 +160,11 @@ Mini example — good vs bad target selection with the same state (J-03 regresse
   holds:
   1. **Structural / cross-cutting** — the change refactors shared architecture or
      touches ≥3 modules whose interactions are not covered by one journey's tests.
-  2. **Data model** — it adds/changes persisted schema or a blueprint Data-Contract
-     value's computing module or serving endpoint.
+  2. **Data-model migration** — it CHANGES or REMOVES persisted schema of existing
+     records, or changes an ALREADY-REGISTERED blueprint Data-Contract value's
+     computing module or serving endpoint. Purely ADDITIVE work — a new field,
+     table, or contract value introduced for a new journey — is explicitly
+     NOT this trigger.
   3. **Prior ESCALATE** — the last evaluator verdict was `ESCALATE` (mandatory, no
      exceptions).
   4. **Hardening cadence** — the last `CHAIN_HARDENING_CADENCE` (default 6)
@@ -230,7 +233,7 @@ Always restate the anti-goals from `docs/goal.md` verbatim under Goal Mode Metad
 1. **Anti-goals restated verbatim** under Goal Mode Metadata (copy-paste, not paraphrase — paraphrase drifts).
 2. **Every new displayed value is registered**: each Data-contract addition names ONE computing module + ONE serving endpoint, and you edited `blueprint.md` to match. "None" is written explicitly when true.
 3. **DEFINITION OF DONE is binary**: every checkbox is machine-checkable or browser-verifiable ("J-07 passes via browser-qa" ✚; "search works well" ✖). If you can't phrase a criterion binarily, the scope is too vague — narrow it.
-4. **Depth is justified**: full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
+4. **Depth is justified**: the evaluator's depth recommendation is binding by default — a full spec against a lean/evidence recommendation must satisfy an escape condition (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence due, or a brand-new full-stack journey), not merely cite a trigger. Full cites which numbered trigger (1-4) in BACKGROUND AND carries the matching `Full trigger: <1|2|3|4> — <one-line reason>` metadata line (the engine demotes a full spec without it to lean); lean states "no full trigger holds" — needing unit tests is never the cited reason. ESCALATE from last eval ⇒ full, and a met hardening cadence ⇒ full, no exceptions.
 5. **Target selection followed the priority rubric** — if you deviated (e.g., skipped a regressed journey), the reason is stated in BACKGROUND.
 6. **Test-first weighting holds (D6)**: every DEFINITION OF DONE checkbox and every Data-contract addition maps to ≥1 `TC-` scenario line in TESTING REQUIREMENTS (given / when / then with an observable result; no banned vague terms), and each Data-contract addition carries exact field name(s) + type/shape. IN SCOPE implementation bullets stay coarse — name the surface or file, not the code inside it. If the spec must shrink, cut implementation narrative — NEVER TC- scenarios or Data-contract definitions.
 
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index a20bbd18..860c3048 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.9.0
-last_updated: '2026-07-28'
+version: 1.10.0
+last_updated: '2026-07-29'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index bb57fa50..92f32755 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -39,7 +39,7 @@ Follow methodology section A (evidence walk). In short: deterministic reports fi
 - Verify the screenshot in `reports/qa/<iter-name>-evidence/` actually shows the claimed end state
 - Cross-check against the prior journey state (inlined digest) to detect changes (newly passing, newly failing, regressed)
 
-Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status.
+Stable `passing`/`already_passing` journeys inside this iteration's **Required-still-passing set** are re-verified mechanically by the deterministic replay lane at BOTH depths — the lean executor and the full pipeline's browser-qa step (those with stored golden scripts; a required journey WITHOUT a golden is routed to the LLM browser-qa lane the same iteration). Their rows land in the merged `ui-test-results.md` you already read. The raw `regression-replay-results.md` is a lane artifact, not an input: where it disagrees with the merged file, the merged file wins — a dated reconciliation footer on the raw file records any replay FAIL the LLM lane overturned (golden-script false positive). A row whose verdict cell is `DEFERRED-BUDGET` (SPEED-15 trim rung 2) means the wall-clock iteration budget cut that journey's re-verification this run — it was NOT tested: the journey KEEPS its prior recorded status (never `regressed`/`failing`/`unknown` on that row alone), you note it as deferred, and the deterministic achievement gate blocks GOAL_ACHIEVED while any journey is deferred. Stable journeys OUTSIDE the set carry over unverified. Spot-check 2 stable journeys (or all, if fewer) — prefer ones outside the replay set — instead of re-reading every screenshot; widen to a full walk if a spot-check contradicts its recorded status.
 
 Also read this iteration's `coherence.md` and note its verdict. A `COHERENCE-FAIL` is a structural veto on `GOAL_ACHIEVED` and drives a consolidation `CONTINUE` (see Verdicts).
 
diff --git a/incredible_auto_dev/agents/qa/body.md b/incredible_auto_dev/agents/qa/body.md
index 4c97ce36..a14f48ab 100644
--- a/incredible_auto_dev/agents/qa/body.md
+++ b/incredible_auto_dev/agents/qa/body.md
@@ -181,6 +181,13 @@ If `Frontend Present: yes`:
 3. Take screenshots. **Save them under `reports/qa/<phase>-evidence/` using `TC-<id>-<slug>.png` or `UT-<nn>-<slug>.png` naming — never save at the repo root.** If you use Chrome MCP's screenshot action, always pass an explicit path under that directory (create it first with `mkdir -p`).
 4. If NOT running after service auto-start attempt: write "SKIPPED — frontend not ready"
 
+**The browser identity is pinned — do not change it.** Profile and CDP port come from
+the environment (`CHROME_WS_PROFILE` / `CHROME_WS_PORT`) so the host-safety guard can
+confine the browser's CPU usage. Never call `set_profile`, never pass a profile or port
+to an action, and never switch the browser to headed mode. If Chrome will not start on
+the pinned profile, record SKIPPED with the exact error rather than retrying on another
+profile — on a capped host an unconfined browser can hard-reset the machine.
+
 **Do NOT mark FAIL just because browser checks were skipped (frontend not running).**
 Browser SKIPPED + tests passing = overall PASS is acceptable.
 
diff --git a/incredible_auto_dev/agents/ui-impact-analyst/agent.yaml b/incredible_auto_dev/agents/ui-impact-analyst/agent.yaml
index 5bf6f34d..256ce520 100644
--- a/incredible_auto_dev/agents/ui-impact-analyst/agent.yaml
+++ b/incredible_auto_dev/agents/ui-impact-analyst/agent.yaml
@@ -3,6 +3,6 @@ description: Post-dev UI impact analyst. Reads the phase diff and handoffs, maps
   UI surfaces, identifies what changed for users vs what is backend-only. Produces user-visible-changes
   and ui-surface-map reports. Runs after dev+review passes.
 model_tier: standard
-version: 1.0.0
-last_updated: '2026-05-04'
+version: 1.1.0
+last_updated: '2026-07-29'
 body: body.md
diff --git a/incredible_auto_dev/agents/ui-impact-analyst/body.md b/incredible_auto_dev/agents/ui-impact-analyst/body.md
index cf73d296..49fa5387 100644
--- a/incredible_auto_dev/agents/ui-impact-analyst/body.md
+++ b/incredible_auto_dev/agents/ui-impact-analyst/body.md
@@ -95,6 +95,31 @@ No UI surfaces affected.
 
 Then STOP.
 
+## Combined mode
+
+When your dispatch prompt says `COMBINED MODE (SPEED-24)`, you additionally do the
+ui-test-designer's job in the SAME session — your just-written surface map is that
+role's entire input, so a second dispatch would only buy a fresh context, not a
+second opinion. After writing the two impact reports above:
+
+1. Follow the skills `.claude/skills/manual-ui-test-plan-generator.md` and
+   `.claude/skills/what-to-click-writer.md` (your prompt lists them in combined
+   mode).
+2. For each surface in your surface map, create test cases (smoke, happy-path,
+   validation, error, regression, UX). Each test case must have exact steps with
+   specific URLs, button text, field names, and expected outcomes.
+3. Write the 5-minute operator verification guide (max 10 steps).
+4. Write the two additional reports at the exact paths your prompt names:
+   - `reports/phase-{N}-ui-test-plan.md` (use template: `templates/ui-test-plan.md`)
+   - `reports/phase-{N}-what-to-click.md` (use template: `templates/what-to-click.md`)
+
+Every step must be independently executable — no vague steps like "test the form"
+or "verify it works". The artifact names, templates, and quality bar are IDENTICAL
+to the standalone ui-test-designer's; the phase-closure gate checks all four
+artifacts either way. If you cannot complete the combined deliverables, still
+finish the two impact reports — the pipeline detects the gap and dispatches the
+separate designer as a fallback.
+
 ## Rules
 
 - Do NOT edit source files
diff --git a/incredible_auto_dev/benchmarks/experiments.md b/incredible_auto_dev/benchmarks/experiments.md
index 9dbb672a..608807e1 100644
--- a/incredible_auto_dev/benchmarks/experiments.md
+++ b/incredible_auto_dev/benchmarks/experiments.md
@@ -944,3 +944,73 @@ Entry format contract (grep-able; pinned by
 - hypothesis: the SPEED-9..19 + REP-4 + TOKEN-9 package cuts typical goal-mode iteration wall time under 60 min without journey-quality regressions. Baseline (desk, 15 iters): ~153 agent-min/iter; verification = 54% of agent minutes; full depth 4 of last 6 iters; browser-qa >100 turns/invocation; 3 of last 5 iterations were evidence-only waste (~6h); zero quota-pause events recorded (attribution bug).
 - metrics + prediction (manual grading): median wall for lean/evidence/zero-change iterations < 60m; evidence-class gaps resolved in < 45m via the evidence micro-path (no developer dispatch); full-depth ratio <= 1 in 6; browser-qa <= 60 turns/invocation; demo-narrator+readme token cost ~1/3 of sonnet baseline; NO journey regressions or golden verdict-class flips attributable to the package; summaries name concrete files/screens (grep for 'Product changes:' rows).
 - note: pre-registered manually (G8) — the package is engine+contract work, not a run-benchmark.sh invocation; grade against the next session's telemetry with analyze_telemetry.py --wall.
+
+## POST speed-package-20260728 · 2026-07-29T12:30:00Z
+- graded against: LIVE tapeology desk session iters 15-18 (the first iterations
+  running the full package — vendored sync to main 48a3b97 on Jul 29 00:22,
+  engine restart 01:04; iters 0-14 ran OLD code and are excluded), telemetry +
+  trace analysis performed 2026-07-29 during the iteration-shape investigation.
+- arm-by-arm:
+  · median lean/evidence/zero-change wall < 60m — **UNTESTED**: no lean or
+    evidence iteration ran in the window; every iteration 15-18 dispatched
+    FULL (see next arm — the same defect).
+  · full-depth ratio <= 1 in 6 — **FAILED (5 of 6 full)**: the decomposer wrote
+    a qualifying `Full trigger: 2 — adds a field to persisted record` line
+    into EVERY spec (trivially true for every proposer-promoted journey) and
+    the SPEED-10 allowlist trusted it; the evaluator's `next_depth: evidence`
+    recommendation (iters 16, 17) was overridden both times. Root cause of
+    the surviving 2h+ floor; promoted to anti-pattern 25 and fixed by
+    SPEED-20 (iteration-shape package).
+  · browser-qa <= 60 turns/invocation — **FAILED**: 104-132 turns observed
+    (J-06-class no-golden journeys keep riding the LLM lane; golden-first
+    regression SPEED-21/22/23 targets this).
+  · demo-narrator+readme cost ~1/3 sonnet baseline — **PASSED (better)**:
+    demo-narrator 26m → ~90s per iteration after the haiku routing.
+  · no journey regressions / golden verdict-class flips — **PASSED**: 13/14
+    journeys passing after iter-18, 1 partial (J-14, new scope); zero
+    package-attributable regressions; iter-14's 8/9 replay false-FAIL was
+    selector drift (pre-package code), not a golden flip.
+  · summaries name concrete files/screens — **PASSED** (Product changes: rows
+    present in the post-sync summaries).
+  · (headline, unregistered but the package's stated goal) full-depth
+    productive time 210m → 133m (−37%); steady-state iterations 15-18 =
+    118-151 min of near-continuous first-try LLM work across 16-18 SEQUENTIAL
+    dispatches, zero quota pauses (0s across 174 dispatches — SPEED-13's
+    attribution fix held), zero retry loops. The remaining floor is the
+    pipeline's SHAPE, not failures — which is what the iteration-shape
+    package (PRE below) attacks.
+- verdict: package effective where it aimed (−37% productive time, showcase
+  costs collapsed, honesty fixes held) but the <60m target was structurally
+  unreachable while the depth governor could be self-certified around —
+  full-ratio arm decisively failed. Follow-up package pre-registered below.
+
+## PRE iteration-shape-20260729 · 2026-07-29T12:45:00Z
+- framework-sha: 48a3b97 + the iteration-shape package (SPEED-20..24, TOKEN-10,
+  REP-5, SPEED-15 armed 3600/trim, TOKEN-3 flip) landing on branch
+  speed-iteration-shape this session; dirty during authoring.
+- fixture: the next 6 REAL goal-session iterations running this package
+  (tapeology desk session after the operator's next vendored sync, or any
+  adopter session), graded with `analyze_telemetry.py --wall`.
+- hypothesis: with the depth governor deterministic (arbiter), the budget
+  armed with teeth (3600s/trim + next-iter lean ratchet), executor context
+  sliced, and the regression sweep golden-first, the typical iteration
+  becomes lean/evidence by construction and lands under an hour.
+- metrics + prediction (manual grading, G8):
+  · median iteration wall < 60 min over the next 6 real-session iterations;
+  · full-depth ratio <= 1 in 4 (arbiter window cap W=4), with every full
+    carrying a `depth_full_granted` reason that is NOT `new-fullstack-journey`
+    unless journey-history confirms the journey was genuinely new;
+  · developer mean wall < 25 min (TOKEN-10 slice; desk baseline 31→77m);
+  · >= 2 goldens auto-derived and installed (`golden_autoderived` events) OR
+    zero eligible PASS-without-golden journeys existed;
+  · zero journey regressions and zero golden verdict-class flips attributable
+    to the package; any DEFERRED-BUDGET row is re-verified within 2 iterations;
+  · no GOAL_ACHIEVED certified while a DEFERRED-BUDGET row exists (mechanical,
+    goal_gate).
+- note: pre-registered manually (G8) — engine+contract work, not a
+  run-benchmark.sh invocation. Rollback ladder if the prediction fails:
+  CHAIN_DEPTH_ARBITER=false / CHAIN_ITER_TIME_BUDGET_SECONDS=0 /
+  CHAIN_ITER_BUDGET_MODE=warn / CHAIN_DEV_FULL_GOAL=true /
+  CHAIN_GOLDEN_AUTODERIVE=false / CHAIN_REPLAY_MASS_FAIL_BREAKER=false /
+  CHAIN_UI_COMBINED=false / CHAIN_SKIP_TESTPLAN_IF_PRESENT=false — each knob
+  reverts exactly one item.
diff --git a/incredible_auto_dev/commands/goal.md b/incredible_auto_dev/commands/goal.md
index 5d2834ec..e5bbfca7 100644
--- a/incredible_auto_dev/commands/goal.md
+++ b/incredible_auto_dev/commands/goal.md
@@ -16,7 +16,10 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
    exists with `HOST_GUARD_ENABLED=1`): run
    `scripts/automation/host-guard-adopt.sh --cli-root-of $$` — it confines THIS
    already-running CLI session (and everything it will spawn) to the declared
-   caps, in place; instant and idempotent when already confined. No special
+   caps, in place; instant and idempotent when already confined. It also
+   re-confines any framework QA Chrome and Chrome-MCP server that escaped a
+   previous session (the MCP reuses browsers it did not spawn, and detached
+   browsers outlive it) — no extra step needed. No special
    launch command is required. Only if it prints `FAILED`, tell the user to
    relaunch via `scripts/automation/host-guard-exec.sh claude` (the from-birth
    wrapper) — the engine's iteration gate re-verifies each iteration and would
diff --git a/incredible_auto_dev/docs/goal-mode-telemetry.md b/incredible_auto_dev/docs/goal-mode-telemetry.md
index 38baf70c..a97e9d4a 100644
--- a/incredible_auto_dev/docs/goal-mode-telemetry.md
+++ b/incredible_auto_dev/docs/goal-mode-telemetry.md
@@ -163,12 +163,19 @@ python3 scripts/automation/lib/analyze_telemetry.py runs/goal-session-<sid>/tele
 
 | Event | Written by | Payload highlights |
 |---|---|---|
-| `step_skipped` | `goal-iter-lean.sh`, `run-goal.sh` | `{step, iter_name, reason:"checkpoint"}` — a resume reused a completed step instead of re-running it |
+| `step_skipped` | `goal-iter-lean.sh`, `run-goal.sh`, `run-phase.sh` | `{step, iter_name|phase, reason}` — a step was skipped instead of dispatched. Reasons: `checkpoint` (resume reused a completed step), `zero-change` (SPEED-14), `iter-budget-trim` (SPEED-15 rungs 3a/3b: `test-plan`/`ux-regression`, payload key `phase`), `ui-combined` (SPEED-24: `ui-test-design` folded into the ui-impact dispatch, payload key `phase`) |
 | `dispatch_wait` | `lib/interactive-dispatch.sh` | `{agent, wait_seconds, run_seconds, status, rc}` — pickup-wait vs run split per interactive dispatch attempt (`ok` \| `pickup-timeout` \| `inflight-timeout` \| `inflight-timeout-requeued`) |
 | `review_verdict` | `goal-iter-lean.sh` | `{verdict, attempt, iter_name}` — reviewer outcome per attempt (feeds the tripwire) |
 | `iter_config` | `run-goal.sh` | `{key, value}` — an opt-in experiment knob (e.g. `CHAIN_AGENT_EFFORT`) was active this iteration |
-| `golden_coverage` | `goal-iter-lean.sh`, `browser-qa-phase.sh` (goal iterations) | `{passing, missing_goldens, iter_name}` — PASSing journeys still lacking a replay golden |
+| `golden_coverage` | `goal-iter-lean.sh`, `browser-qa-phase.sh` (goal iterations) | `{passing, missing_goldens, iter_name}` — PASSing journeys still lacking a replay golden (also persisted to `state/golden-gaps`, SPEED-23) |
 | `experiment_reverted` | `run-goal.sh` | `{key, value}` — the tripwire auto-reverted an experiment knob |
+| `depth_full_granted` / `depth_demoted` | `run-goal.sh` | `{reason, prior_verdict, prior_depth}` — the SPEED-20 deterministic depth arbiter granted a spec-requested full (`prior-verdict-*`, `prior-coherence-fail`, `cadence-due`, `new-fullstack-journey`) or demoted it to lean (`budget-breach`, `full-cap`, `evaluator-requested-*`, legacy `no-full-trigger`) |
+| `iter_budget` | `lib/common.sh` (any budget-aware script) | `{budget, elapsed, mode, at_step}` — first over-budget check of the process (SPEED-15; defaults 3600s/trim) |
+| `iter_budget_trim` | `run-goal.sh`, `goal-iter-lean.sh`, `run-phase.sh`, `browser-qa-phase.sh` | `{rung}` — a trim rung actually shed work (`showcase-defer`, `replay-narrow`, `testplan-skip`, `ux-regression-skip`) |
+| `goal_slice_fallback` | `lib/common.sh` (executor dispatch sites) | `{iter_name, rc}` — the TOKEN-10 executor goal-slice build failed; the dispatch fell back loudly to the full `docs/goal.md` |
+| `golden_autoderived` / `golden_autoderive_rejected` | `lib/replay-lane.sh` (via `demo-phase.sh`) | `{journey, iter_name}` — a SPEED-21 demo-derived golden candidate replayed green and was installed, or failed its verify pass and was discarded |
+| `golden_nudge` | `goal-iter-lean.sh`, `browser-qa-phase.sh` | `{journey, iter_name}` — SPEED-23 promoted this journey's golden to a REQUIRED deliverable this dispatch |
+| `replay_mass_fail_voided` / `replay_mass_fail_confirmed` | `lib/replay-lane.sh` / `goal-iter-lean.sh` | `{iter_name, journeys, canaries}` — SPEED-22 mass-false-FAIL breaker outcome: green canaries voided the replay FAILs (drift), or a canary failure kept the full re-confirm path |
 
 ### `missing_evidence` (REL-11 tripwire)
 Written when a dispatch returns — any exit code, including 0 — without its expected report artifact on disk: full-mode QA (`qa-phase.sh`), the lean browser-qa LLM lane (`goal-iter-lean.sh`; quota pauses excluded), and the retro-analyst (`run-goal.sh`). The telemetry counterpart of the loud `[missing-evidence]` stderr banner (`lib/common.sh` `warn_missing_evidence`). Non-blocking — a tripwire, never a gate.
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index cd4d634d..faadd1f5 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -28,10 +28,129 @@ disables everything.
 | `HOST_GUARD_REQUIRE_MARKERS` + `HOST_GUARD_MARKER_FILES` | require HOST-GUARD cap blocks in listed launcher scripts | project-specific |
 | `HOST_GUARD_TCTL_PAUSE` / `_RESUME` / `_MAX_WAIT` | thermal gate thresholds (°C, °C, s) | `90` / `80` / `1800` |
 | `HOST_GUARD_SAMPLER_INTERVAL` / `_MAX_BYTES` | forensics sampler cadence / csv ring size | `1` / `10485760` |
+| `HOST_GUARD_BROWSER_CONFINE` | `0` disables the QA-browser confinement pass | `1` (default) |
 
-Running two projects' goal modes on one host: give them **complementary masks**
-(e.g. `0-3,8-11` and `4-7,12-15` on an 8-core/16-thread part) so a burst can
-never light every core, and size `MEMORY_HIGH` so the sum fits in RAM.
+## Machine-global aggregate budget
+
+Everything in the table above bounds **one session**. That is not the same as
+bounding the machine, and the difference is not academic:
+
+> On 2026-07-29 at 14:02:45 the reference host hard-reset with two goal modes
+> running under *complementary* masks — `0-3,8-11` and `4-7,12-15`. Each session
+> passed every check it had. Their union was all 16 CPUs: every physical core
+> available to a single burst. The memory ceilings had the same shape, 14G + 14G
+> against 27.3G of RAM. **Complementary masks are not a safety property — they
+> are a guarantee that the machine can be fully lit.** (Earlier revisions of this
+> document recommended them. That advice was wrong and is retracted.)
+
+So a second file, owned by the machine rather than by any repo, declares what
+*all* guarded sessions may consume together:
+
+```bash
+# ~/.config/iad/host-guard-host.env   (never committed to any project)
+HOST_GUARD_GLOBAL_CPU_LIST="0-3,8-11"   # every session's mask must be a SUBSET
+HOST_GUARD_GLOBAL_MEMORY_BUDGET="22G"   # Σ over projects of max(MemoryHigh)
+HOST_GUARD_REQUIRE_BOOST_OFF=1          # /sys/.../cpufreq/boost must read 0
+HOST_GUARD_GLOBAL_ON_CONFLICT=pause     # only 'pause' is implemented
+```
+
+Every guarded context publishes a record (pid, start time, boot id, project,
+mask, memory ceiling) into a registry under
+`${CHAIN_TMP_ROOT:-~/.cache/iad}/host-guard/registry/`, so any session can see
+the whole machine. Preflight and every iteration boundary then check:
+
+1. CPU **boost** is off (when required) — see *Boost persistence* below;
+2. this session's mask ⊆ the global list — a violation always pauses, seniority
+   does not excuse a misconfigured session;
+3. the **union** of all live masks ⊆ the global list (checked explicitly, so a
+   hand-edited record or a session started before this feature still trips it);
+4. the per-project memory ceilings sum within the budget. Memory is summed as
+   *max per project*, because a project's engine scope and its adopted-pump
+   scope are separate cgroups carrying the same ceiling — a naive sum would
+   double-count every project.
+
+**Who yields.** Sessions register *before* they verify, so two engines starting
+at the same instant each see the other. Both then compute the same loser from a
+total order — `(epoch, start time, pid)` — and the junior one pauses
+`AWAITING_HOST_GUARD` while the senior logs a warning and continues. There is no
+lock, and no outcome where both pause or neither does.
+
+**Staleness is pid-based, never time-based.** A record dies when its pid is gone,
+when the pid was recycled (start time differs), or when the boot id no longer
+matches. Iteration gaps here are legitimately unbounded — a thermal cooldown can
+last 30 minutes — so an mtime TTL would evict live sessions.
+
+Absent budget file ⇒ enforcement off, exactly as before. The registry is still
+maintained, and once two *different* projects are guarded simultaneously the
+engine says so loudly rather than pretending the machine is bounded.
+
+A future `narrow` conflict mode (re-exec the junior session inside the remaining
+budget instead of pausing) is deliberately **not** implemented: an already-running
+pump tree cannot be narrowed safely mid-session.
+
+## Boost persistence
+
+The guard verifies its own premises. CPU boost was disabled on this class of host
+as a hardware mitigation, applied live — and silently reverted at the next reboot
+because the persistence rule was never installed. Nothing noticed for a day. With
+`HOST_GUARD_REQUIRE_BOOST_OFF=1` a re-enabled boost now pauses the engine.
+
+```bash
+echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost
+printf 'w /sys/devices/system/cpu/cpufreq/boost - - - - 0\n' \
+  | sudo tee /etc/tmpfiles.d/cpufreq-boost.conf
+sudo systemd-tmpfiles --create /etc/tmpfiles.d/cpufreq-boost.conf
+cat /sys/devices/system/cpu/cpufreq/boost      # must print 0
+```
+
+`scripts/automation/doctor.sh --only cpu-boost` reports both the live knob and
+whether the rule that survives a reboot exists.
+
+## Browser QA confinement
+
+Confining process *trees* is not enough for browser QA. The Chrome MCP does not
+always spawn its browser: it **reconnects** to one recorded in
+`<profile>.meta.json` and **adopts** orphans it finds by scanning for its
+`--user-data-dir`. A browser born in an unconfined session therefore keeps its
+wide CPU mask forever. And because Chrome is spawned detached, it outlives its
+MCP server and is reparented to init — out of reach of any descendant walk.
+
+`host-guard/browser-confine.sh` closes that hole. It runs before every browser
+dispatch (`browser-qa-phase.sh`, `qa-phase.sh`, `goal-iter-lean.sh`,
+`ui-audit-phase.sh`) and on **both** exits of `host-guard-adopt.sh` — including
+the "already confined" early return, which is the common path and exactly where
+an escaped browser would otherwise go unnoticed. It:
+
+- re-tasksets any browser under the profile root that is outside the mask,
+  preferring re-confinement over killing so warm browsers survive;
+- kills only when taskset fails *and* the profile is this project's own; another
+  project's browser is confined-if-unconfined and otherwise left alone, never
+  killed;
+- confines Chrome-MCP servers too (never kills them — the live pump depends on
+  its server) so their *future* browsers are born inside the mask;
+- sweeps `.meta.json` / `.mcp.lock` files whose pid is gone, with a 30 s age
+  guard so a server mid-launch is not disturbed.
+
+Engine-mode QA additionally runs the browser **headless** (`DISPLAY` and
+`WAYLAND_DISPLAY` are unset before the dispatch, which is the only signal the MCP
+uses), dropping GPU compositing and the raster thread pool. Screenshots are
+unaffected. `CHAIN_BQA_HEADED=1` restores a visible browser for debugging;
+`CHAIN_BQA_REAP=1` additionally terminates this project's QA browsers when an
+engine-mode phase finishes (default is leave-warm — a cold start costs seconds
+and an idle browser inside the mask costs nothing).
+
+| Var | Meaning | Default |
+|---|---|---|
+| `CHROME_WS_PROFILE` / `CHROME_WS_PORT` | pinned QA browser identity, per project and lane (`iad-qa-<project>` on `10000+hash`, the qa lane on `11000+hash`) | set by `ensure_qa_browser_env` |
+| `CHAIN_BQA_HEADED` | `1` keeps a visible browser in engine mode | `0` |
+| `CHAIN_BQA_REAP` | `1` reaps this project's QA browsers at phase end (engine mode only) | `0` |
+| `HOST_GUARD_BROWSER_CONFINE` | `0` disables the pass entirely | `1` |
+
+Pump sessions deliberately get **no** profile pin. A Claude Code `env` setting
+overrides the inherited process environment, so a pinned value there would clobber
+the per-lane profile the phase scripts export and collapse the two concurrently
+running QA lanes (`run-phase.sh` Branch-QA and Branch-UI) onto one shared browser.
+Pump browsers are made safe by affinity instead, which needs no name.
 
 ## Enforcement layers (all in `scripts/automation/`)
 
@@ -57,13 +176,21 @@ never light every core, and size `MEMORY_HIGH` so the sum fits in RAM.
    inject into a running process). The fallback when adoption fails.
 4. **Preflight** (`preflight_host_guard`) — before the loop: forensics sampler
    alive (auto-started if not), affinity wrap took effect, launcher marker
-   blocks intact. Failure pauses the session `AWAITING_HOST_GUARD` (resumable).
+   blocks intact, and the machine-global budget + boost assumption hold.
+   Failure pauses the session `AWAITING_HOST_GUARD` (resumable).
 5. **Iteration gate** (`host_guard_iteration_gate`, top of loop) — thermal
-   cooldown between iterations (wait out heat-soak, bounded), and — when
-   `HOST_GUARD_REQUIRE_PUMP_CONFINED=1` — pump-cpuset verification (via the
-   `pid=` line in `.pump-alive`, or the CLI root captured at engine launch)
-   with automatic in-place re-confinement; pauses only when that fails.
-6. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
+   cooldown between iterations (wait out heat-soak, bounded); pump-cpuset
+   verification when `HOST_GUARD_REQUIRE_PUMP_CONFINED=1` (via the `pid=` line
+   in `.pump-alive`, or the CLI root captured at engine launch) with automatic
+   in-place re-confinement, pausing only when that fails; then a re-check of the
+   machine-global budget and boost, since the *other* project's session may have
+   started after this one's preflight.
+6. **Machine-global bound** (`lib/host-guard-registry.sh`) — the live-session
+   registry and the aggregate CPU/memory/boost checks described above. This is
+   the layer that sees more than one project at a time.
+7. **Browser confinement** (`host-guard/browser-confine.sh`) — QA browsers and
+   Chrome-MCP servers that escaped the process tree, see below.
+8. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
    pressure/memory to `<repo>/logs/hwmon/hwmon.csv`, fsync per line, so the
    final pre-reset second survives a hard reset. `{run|start|stop|status|watch}`;
    `status`/`start` recognize an externally-run sampler (e.g. a systemd user
@@ -84,6 +211,11 @@ load has hard-reset a host.
 Built after a GEEKOM A7 Max (Ryzen 9 7940HS) hard-reset five times in eight
 days (2026-07-20 → 2026-07-28) under goal-mode load, three of the resets
 captured at 1 Hz with benign temperatures and low package power — a
-millisecond-scale power transient. Incident forensics and the cap-widening
-verification ladder live in the originating project:
-`trendora/project-extensions/host-guard/README.md`.
+millisecond-scale power transient.
+
+A sixth reset on 2026-07-29 came *after* per-session confinement was in place,
+and produced the machine-global layer: two correctly-confined projects were
+still collectively unbounded, a QA browser could keep a pre-confinement CPU
+mask, and the boost mitigation had silently lapsed at a reboot. Incident
+forensics and the cap-widening verification ladder live in the originating
+project: `trendora/project-extensions/host-guard/README.md`.
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index bf3cd80f..557ba36b 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -155,6 +155,42 @@ signal that says "do this now").
     *G8 fresh-session certification 2026-07-29 (non-implementer): steps 1-5
     verified green; items remain IN-PROGRESS pending the real-session
     telemetry (PRE speed-package-20260728).*
+12. **SPEED-20…24 + TOKEN-10 + REP-5** — the iteration-shape package (promoted
+    2026-07-29 by direct user request: tapeology still spent 2h+ per iteration
+    from iter-14 on AFTER the speed package; telemetry attributed the floor to
+    the pipeline's SHAPE — the depth governor routed around via self-certified
+    `Full trigger:` lines, no enforced ceiling, and recurring taxes). Root-cause
+    killers: SPEED-20 deterministic depth arbiter (evaluator recommendation
+    binding) + SPEED-15 completion (budget armed 3600s/trim — both
+    gate-default changes sanctioned by the user task, incl. the TOKEN-3 flip);
+    plus TOKEN-10 executor goal slices, SPEED-21/22/23 golden-first regression,
+    SPEED-24 combined UI dispatch, REP-5 confirm attribution. Grades the PRE
+    speed-package-20260728 entry as POST (full-ratio arm FAILED — 5/6, the
+    governor bypass; productive-time arm PASSED −37%) and registers PRE
+    `iteration-shape-20260729`. Judgment spot-run GREEN 2026-07-29 (the
+    DEFERRED-BUDGET evaluator-contract wording touches evaluator inputs):
+    goal-evaluator 6/6 verdict classes on claude-opus-5 @ max, incl. case-01
+    GOAL_ACHIEVED and case-06 pending-infra CONTINUE. Adversarially reviewed
+    same session (6-lens workflow, 34 raw → 11 confirmed findings, all fixed —
+    incl. a canary-dispatch unbound goal-line crash now pinned end-to-end by
+    test-goal-parallel-bqa scenario L). G8 fresh-session certification + the
+    next real session's telemetry still owed before any item flips to DONE.
+    *G8 fresh-session certification 2026-07-29 (non-implementer): steps 1-5
+    verified green (run-evals 147/0; self-tests goal-gates OK incl. the REP-5
+    confirm-attribution case, goal_gate.py OK incl. the DEFERRED-BUDGET block,
+    demo_runner 22/0, merge_ui_test_results 8/0; suites depth-arbiter 33,
+    depth-cadence 23, iter-budget 33, replay-lane 59, replay-lane-full 24,
+    goal-parallel-bqa 103 incl. scenario L, goal-context-slice 26,
+    golden-autoderive 22, testplan-skip 30, ui-combined 18 — all 0 FAIL;
+    defaults 3600/trim + CHAIN_SKIP_TESTPLAN_IF_PRESENT/CHAIN_DEPTH_ARBITER
+    default-true with the legacy allowlist intact; the five trim consult sites
+    shed only showcase/replay-breadth/test-plan/ux-regression — never the
+    spine; DEFERRED-BUDGET spelling identical in all five sources + mirrors;
+    4a1ce4f leaves the evaluator dispatch prompt and run-judgment-evals.sh
+    untouched; rung-3 traced end-to-end — iter-N/budget-breached written after
+    the verdict gate, read by iter-N+1 under PRIOR_VERDICT=CONTINUE, SPEED-4
+    re-promotion suppressed). Items remain IN-PROGRESS pending the real-session
+    telemetry (PRE iteration-shape-20260729).*
 
 ---
 
@@ -1162,6 +1198,12 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Rollback:** `CHAIN_DEPTH_ALLOWLIST=false`; `CHAIN_HARDENING_CADENCE=4`.
 - **Stop-and-ask:** a demoted-full iteration producing an ESCALATE in the first
   real session — report before tuning anything.
+- **SUPERSEDED as the default (2026-07-29):** the desk session proved the
+  allowlist's `Full trigger:` arm is self-certifying — the decomposer wrote a
+  qualifying line into every spec and full ran 5-of-6 (anti-pattern 25).
+  SPEED-20's deterministic arbiter is now the default path; this allowlist
+  survives verbatim as the arbiter's PRIOR_DEPTH=full rung and as the
+  `CHAIN_DEPTH_ARBITER=false` escape hatch.
 
 ### SPEED-11 · Lean replay-fork default flip (off→replay)
 - **Priority:** P1 · **Effort:** S · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
@@ -1236,22 +1278,39 @@ benchmark (or a real session's telemetry) before AND after (G8).
   its escape is the pre-existing `CHAIN_README_EVERY_ITER=true`).
 - **Stop-and-ask:** none.
 
-### SPEED-15 · Wall-clock iteration budget (warn-first)
-- **Priority:** P2 · **Effort:** M (slice a landed; slice b TODO) · **Risk:** LOW
-  (warn) / MED (trim) · **Status:** IN-PROGRESS — slice (a) implemented
-  2026-07-28: knobs `CHAIN_ITER_TIME_BUDGET_SECONDS` (default 0=off; suggest
-  5400) + `CHAIN_ITER_BUDGET_MODE` (warn|trim, default warn), step-boundary
-  checks (never mid-agent), one loud warn + `iter_budget` telemetry, trim ladder
-  for showcase-class steps only (defer demo+readme; summarizer kept; spine and
-  gates NEVER trimmed — grep-pinned by the test).
-- **Slice (b) TODO:** trim-mode browser-set narrowing — drop only the no-golden
-  regression re-drives with mandatory `DEFERRED-BUDGET` result rows + the
-  one-line evaluator contract ("a DEFERRED-BUDGET row keeps prior status;
-  schedule next iteration", pending_infra pattern). Requires one full warn-mode
-  session of telemetry FIRST (G8) — do not build trim-b before that exists.
-- **Verify:** `bash tests/automation/test-iter-budget.sh` (17 cases).
-- **Rollback:** default off — unset the env.
-- **Stop-and-ask:** before enabling trim as any default.
+### SPEED-15 · Wall-clock iteration budget (armed by default: 3600s / trim)
+- **Priority:** P0 (promoted from P2 by the desk 2h-floor evidence) ·
+  **Effort:** M · **Risk:** MED · **Status:** IN-PROGRESS — slice (a) implemented
+  2026-07-28 (warn-first); slice (b) + the default flip implemented 2026-07-29
+  (iteration-shape package); G8 certification pending.
+- **Change spec (landed 07-29):** **gate-default change, sanctioned by the
+  user's 2026-07-29 iteration-shape task (maintenance-protocol §1); Dennis
+  picked 3600s/trim explicitly.** Defaults `CHAIN_ITER_TIME_BUDGET_SECONDS`
+  0→3600 and `CHAIN_ITER_BUDGET_MODE` warn→trim — the slice-(b) precondition
+  ("one warn-mode session of telemetry first") is satisfied by the desk
+  session's iters 15-18 (118-151 min productive, zero quota pauses). Trim
+  ladder, in rung order, each with `iter_budget_trim{rung}` telemetry:
+  rung 1 defer demo+README to the tail (existed); rung 2 browser-set narrowing —
+  `replay_lane_deferred_budget_set` defers only the no-golden regression
+  journeys (targets + replay-FAIL re-confirms NEVER cut), post-merge
+  `DEFERRED-BUDGET` rows keep prior status per the evaluator contract
+  (goal-evaluator body + methodology A), and `goal_gate.py results` blocks
+  GOAL_ACHIEVED while any row is deferred; rung 3a skip test-plan generation
+  when the spec carries TC- lines or a fresh plan exists; rung 3b skip
+  ux-regression-reviewer with a SKIPPED (never FAIL) stub. `run-phase.sh` +
+  `browser-qa-phase.sh` join the engine clock via `CHAIN_ITER_START_EPOCH`
+  (standalone phase mode stays inert). Never-trim list grep-pinned:
+  developer, reviewer, decomposer, evaluator, QA loop, audit, closure,
+  deterministic gates, two-key confirm. A breach also forces the NEXT
+  iteration lean via the `budget-breached` marker (SPEED-20 rung 3).
+- **Verify:** `bash tests/automation/test-iter-budget.sh` (33 cases) ·
+  `test-replay-lane.sh` (rung-2 cases) · `test-testplan-skip.sh` (rung-3a) ·
+  `goal_gate.py self-test` (DEFERRED row blocks).
+- **Rollback:** `CHAIN_ITER_TIME_BUDGET_SECONDS=0` disarms everything;
+  `CHAIN_ITER_BUDGET_MODE=warn` keeps warnings only.
+- **Stop-and-ask:** a DEFERRED-BUDGET journey turning out to be a REAL
+  regression discovered late — bring the iteration, don't widen never-trim
+  silently.
 
 ### SPEED-16 · Browser-qa turn diet
 - **Priority:** P0 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
@@ -1326,6 +1385,124 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Rollback:** revert body + version (single hunk).
 - **Stop-and-ask:** any auditor golden verdict-class flip ⇒ revert immediately.
 
+### SPEED-20 · Deterministic depth arbiter — evaluator recommendation binding by default
+- **Priority:** P0 · **Effort:** M · **Risk:** MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package); G8 certification pending.
+- **Problem:** SPEED-10's allowlist trusted the spec's own `Full trigger:` line
+  and the decomposer learned to write a trivially-true one (trigger 2 "adds a
+  field to persisted record") into EVERY spec — desk iters 13-18 ran full 5 of
+  6 against a PRE-registered target of ≤1-in-6, twice overriding an explicit
+  evaluator `next_depth: evidence` recommendation (anti-pattern 25).
+- **Change spec (landed):** engine ladder (`CHAIN_DEPTH_ARBITER`, default on,
+  iter>0) replaces the allowlist for spec-requested fulls, precedence:
+  prior ESCALATE/REGRESSION → full; prior COHERENCE-FAIL → full; prev-iteration
+  `budget-breached` marker + CONTINUE → LEAN (SPEED-4 re-promotion suppressed
+  that pass); cadence-due → full; full ran inside the
+  `CHAIN_FULL_CADENCE_CAP` (default 4) window → LEAN (`full-cap`); evaluator
+  recommended lean/evidence → full ONLY on `Full trigger:` line AND
+  `goal_new_fullstack_journey` (backend+frontend bullets, real Data-contract
+  additions, ≥1 never-implemented target; fail-closed python) else LEAN
+  (`evaluator-requested-*`); evaluator recommended full → legacy allowlist.
+  Grants/demotions telemetered (`depth_full_granted`/`depth_demoted`).
+  Decomposer trigger 2 tightened to Data-model MIGRATION (purely additive is
+  explicitly NOT the trigger); binding-recommendation language in body,
+  self-check 4, and the engine prompt line. New helpers
+  `goal_full_ran_in_window` + `goal_new_fullstack_journey` in `lib/common.sh`.
+- **Verify:** `bash tests/automation/test-depth-arbiter.sh` (29 cases) ·
+  `test-depth-cadence.sh` still green · run-evals.
+- **Files:** `run-goal.sh`, `lib/common.sh`, `agents/goal-decomposer/*`, tests.
+- **Rollback:** `CHAIN_DEPTH_ARBITER=false` (legacy SPEED-10 allowlist verbatim);
+  `CHAIN_FULL_CADENCE_CAP=0` removes just the window cap.
+- **Stop-and-ask:** a demoted full producing an ESCALATE, or the full ratio
+  staying >1-in-4 over the next 6 real iterations (the PRE entry grades it).
+
+### SPEED-21 · Golden auto-derivation from the verified demo
+- **Priority:** P1 · **Effort:** M · **Risk:** LOW-MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package); G8 certification pending.
+- **Problem:** goldens depend on the browser-qa agent's best-effort authoring —
+  desk J-06 rode the slow LLM lane for 8 straight iterations because its golden
+  never got written; goldens and demo scripts are the SAME runner format.
+- **Change spec (landed):** `demo_runner.py --mode derive` (pure transform,
+  fail-closed: demo must validate, ≥1 tagged step, derived sequence opens with
+  goto, ≥1 tagged expect; writes `<J>.json.candidate`, always rc 0) +
+  `replay_lane_autoderive_goldens` (gate `CHAIN_GOLDEN_AUTODERIVE`, default on;
+  want = PASS-without-golden ∪ PASS∩`goldens-regen-pending`, cap
+  `CHAIN_GOLDEN_AUTODERIVE_MAX`=3): each candidate gets a REAL verify pass in a
+  throwaway scripts-dir against the live frontend — rc 0 → atomic install +
+  `golden_autoderived`; rc 5 → discard (`golden_autoderive_rejected`); rc 6 →
+  discard the batch. Hooked in `demo-phase.sh` after a GREEN record run of a
+  goal iteration (services still up; both depths share the hook).
+- **Verify:** `python3 scripts/automation/lib/demo_runner.py self-test`
+  (`_t_derive_*`) · `bash tests/automation/test-golden-autoderive.sh` · run-evals.
+- **Rollback:** `CHAIN_GOLDEN_AUTODERIVE=false`.
+- **Stop-and-ask:** an auto-derived golden producing a verdict-class flip a
+  hand-written golden would not have (bring the JSON pair).
+
+### SPEED-22 · Mass-false-FAIL breaker — canary re-check before re-confirming the world
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package); G8 certification pending.
+- **Problem:** desk iter-14's replay lane false-FAILed 8/9 journeys (selector
+  drift after a UI change) and the LLM lane spent ~28 min re-confirming every
+  one individually.
+- **Change spec (landed):** in the shared lane, a >2-FAIL majority
+  (2·n_fail > n_ran; 8/9 triggers, 2/9 and 3/6 do not) arms the breaker
+  (`CHAIN_REPLAY_MASS_FAIL_BREAKER`, default on) — ONLY when
+  `REPLAY_LANE_CANARY_CAPABLE=1` (set by goal-iter-lean.sh; the full pipeline
+  is byte-identical). The lean lane dispatches the 2 lowest-ID FAILs as
+  canaries first: both green → `merge_ui_test_results.py void` rewrites every
+  listed FAIL row to SKIP + voided note, recomputes the headline, appends a
+  dated loud footer; voided journeys queue in `goldens-regen-pending`
+  (SPEED-21 re-derives them verified-green); `REPLAY_FAILED` cleared;
+  `replay_mass_fail_voided`. Any canary FAIL or unusable canary file →
+  conservative: today's re-confirm path for the remaining set +
+  `replay_mass_fail_confirmed`. The canary results file rides the merge as a
+  middle input either way; breaker state crosses the SPEED-2 fork via
+  `_bqa_state_save`.
+- **Verify:** `python3 scripts/automation/lib/merge_ui_test_results.py self-test`
+  (void cases) · `bash tests/automation/test-replay-lane.sh` (cases 14-16) ·
+  `test-goal-parallel-bqa.sh`.
+- **Rollback:** `CHAIN_REPLAY_MASS_FAIL_BREAKER=false`.
+- **Stop-and-ask:** a voided FAIL that was REAL (a canary passed while a
+  sibling journey had genuinely regressed) — bring the evidence, do not widen
+  the canary count silently.
+
+### SPEED-23 · Bounded golden-coverage nudge (one required golden per iteration)
+- **Priority:** P2 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package); G8 certification pending.
+- **Problem:** golden authoring is best-effort by design, so a journey can ride
+  the slow LLM lane indefinitely (J-06: 8 iterations) — nothing ever escalates
+  one specific golden to "required".
+- **Change spec (landed):** `replay_lane_golden_coverage` now persists the gap
+  list to `state/golden-gaps`; `replay_lane_golden_nudge_pick` (gate
+  `CHAIN_GOLDEN_NUDGE`, default on) picks ONE gap∩LLM-set journey per
+  iteration — min nudge-count rotation persisted in `state/golden-nudge.json` —
+  and both browser-qa prompts (lean + full) carry it as an explicit REQUIRED
+  DELIVERABLE line; `golden_nudge` telemetry.
+- **Verify:** `bash tests/automation/test-golden-autoderive.sh` (cases 7-9).
+- **Rollback:** `CHAIN_GOLDEN_NUDGE=false`.
+- **Stop-and-ask:** none (one journey per dispatch is the bound).
+
+### SPEED-24 · Combined UI dispatch — ui-impact + ui-test-design in one agent call
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package); G8 certification pending.
+- **Problem:** the designer's ONLY inputs are exactly the analyst's outputs —
+  a second sequential dispatch buys a fresh context (and ~13-17 min per full),
+  not a second opinion.
+- **Change spec (landed):** goal-mode full iterations only (gate
+  `CHAIN_UI_COMBINED`, default on): Branch-A dispatches ui-impact with
+  `CHAIN_UI_COMBINED_DISPATCH=1` — the analyst's new `## Combined mode` section
+  writes all FOUR artifacts (same names/templates/skills); the phase script's
+  failure stubs still cover only the two impact artifacts, so combined
+  under-delivery (plan or what-to-click missing/empty) falls back LOUDLY to the
+  separate ui-test-design dispatch (browser-qa hard-errors without a plan).
+  ui-test-designer agent untouched (phase mode + fallback); closure gate
+  unchanged (all four names still checked) = the quality net.
+- **Verify:** `bash tests/automation/test-ui-combined.sh` (18 cases: combined
+  skips designer / under-delivery fallback / knob-off / plain phase unchanged).
+- **Rollback:** `CHAIN_UI_COMBINED=false`.
+- **Stop-and-ask:** closure-gate FAILs on combined-authored plan/click quality
+  that the standalone designer did not produce ⇒ report before tuning prompts.
+
 ### TOKEN-1 · Per-agent project-template slicing
 - **Priority:** P1 · **Effort:** M · **Risk:** LOW · **Status:** DONE 2026-07-14 —
   release-manager/reviewer/qa converted; developer conversion deliberately LAST per this
@@ -1461,34 +1638,41 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Trigger:** decomposer cost is a top-3 line in per-agent telemetry.
 
 ### TOKEN-3 · Skip test-plan generation when the spec already lists tests
-- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS
-  (mechanics landed + sandbox-proven 2026-07-16; ships **default `false`** per G4 —
-  the default flip to `true` is the real finish line and awaits **one observed clean
-  full-mode phase with the skip active**, riding the same wait as TOKEN-8's live DoD:
-  the next natural full-depth iteration/phase) *(absorbed: README Token-Opt Tier-2)*
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  mechanics landed + sandbox-proven 2026-07-16; **default flipped `true`
+  2026-07-29** (iteration-shape package; gate-default change sanctioned by the
+  user's task per maintenance-protocol §1 — the pre-registered "one observed
+  clean full-mode phase" evidence is the desk session's clean full iterations
+  15-18). A SECOND arm landed with the flip: an existing generated plan that is
+  non-empty, has ≥3 `TC-` lines, and is NEWER than the spec also skips
+  (per-iteration filenames make cross-iteration staleness structurally
+  impossible); the log names which arm matched. G8 certification pending.
+  *(absorbed: README Token-Opt Tier-2)*
 - **Problem:** full-mode Step 2 generates a functional test plan even when the phase
   spec already contains explicit test scenarios — a wasted dispatch.
-- **Current state (post-mechanics):** `run-phase.sh` Step 2 gates the generator
-  dispatch behind `CHAIN_SKIP_TESTPLAN_IF_PRESENT` (default `false` = today's
-  always-generate behavior; `true` + heuristic match → dispatch skipped with ONE loud
-  log line naming the matched heuristic, checkpoint still advances to
-  `test_plan_generated`). Heuristic `_spec_lists_tests_reason()`: word-bounded
-  `## Test`-titled section (`## Tests`, `## Test Scenarios`, `## Test Plan` —
-  deliberately NOT the boilerplate `## TESTING REQUIREMENTS` heading, which
-  `templates/phase-spec.md` ships in every spec while its comment says the generator
-  is still expected to run) OR ≥3 `TC-` test-case lines (the decomposer TC- scenario
-  contract, REL-9 — a spec meeting that contract auto-earns the skip once the knob
-  flips).
+- **Current state (post-flip, 2026-07-29):** `run-phase.sh` Step 2 gates the
+  generator dispatch behind `CHAIN_SKIP_TESTPLAN_IF_PRESENT`, **default `true`**
+  (`false` = the rollback to always-generate; a match → dispatch skipped with ONE
+  loud log line naming the matched arm, checkpoint still advances to
+  `test_plan_generated`). Two arms: (1) heuristic `_spec_lists_tests_reason()` —
+  word-bounded `## Test`-titled section (`## Tests`, `## Test Scenarios`,
+  `## Test Plan` — deliberately NOT the boilerplate `## TESTING REQUIREMENTS`
+  heading, which `templates/phase-spec.md` ships in every spec while its comment
+  says the generator is still expected to run) OR ≥3 `TC-` test-case lines (the
+  decomposer TC- scenario contract, REL-9); (2) an existing generated plan that
+  is non-empty, has ≥3 `TC-` lines, and is NEWER than the spec.
 - **Change spec:** deterministic heuristic (spec contains a `## Test` section or ≥3
-  `TC-` lines) → skip generation and note the skip in the run log; NEVER skip silently.
-  Knob `CHAIN_SKIP_TESTPLAN_IF_PRESENT` default `true` after one observed clean phase.
+  `TC-` lines, or a fresh generated plan exists) → skip generation and note the skip
+  in the run log; NEVER skip silently. ✅ shipped, including the default flip.
 - **DoD:** sandbox phase with tests-in-spec skips with a logged reason; phase without
-  them generates as today; evals green. ✅ *Sandbox half met 2026-07-16:*
-  `tests/automation/test-testplan-skip.sh` (17 assertions; full stubbed run-phase.sh
-  pipeline runs: heading-skip + TC-skip with logged reasons and zero generator
-  dispatches on the canary, plain spec generates as today, knob-off default generates,
-  `## TESTING REQUIREMENTS` boilerplate does NOT suppress). *Default flip: pending the
-  observed clean phase above.*
+  them generates as today; evals green. ✅ *Sandbox half met 2026-07-16, extended
+  2026-07-29:* `tests/automation/test-testplan-skip.sh` (30 assertions; full stubbed
+  run-phase.sh pipeline runs: heading-skip + TC-skip with logged reasons and zero
+  generator dispatches on the canary, plain spec generates as today, knob unset
+  now SKIPS (the flip) while knob=false generates (the rollback), fresh-plan arm
+  skips while a stale plan generates, `## TESTING REQUIREMENTS` boilerplate does
+  NOT suppress). ✅ *Default flip landed 2026-07-29* (iteration-shape package;
+  evidence = the desk session's clean full iterations 15-18).
   *Coupling note (2026-07-16):* REL-9 landed — the decomposer template now
   CONTRACTS ≥1 TC- scenario line per DoD checkbox (≥3 in any real spec), so
   specs meeting the TC- heuristic become the norm rather than the exception;
@@ -1874,6 +2058,34 @@ benchmark (or a real session's telemetry) before AND after (G8).
 - **Stop-and-ask:** haiku demo JSON failing lint more than occasionally, or ONE
   README AUTO-block corruption of hand-written prose ⇒ revert that agent.
 
+### TOKEN-10 · Executor context diet — developer + browser-qa get the goal slice
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package; PROMOTED from
+  CAND-DEV-CONTEXT sketch (a) with the desk evidence attached: developer wall
+  grew 31→77 min while feeding the full 97KB/1,150-line goal.md that the
+  proposer keeps extending); G8 certification pending.
+- **Change spec (landed):** `goal_slice_for_exec` in `lib/common.sh` wraps the
+  EXISTING `goal_gate.py goal-slice` builder (unmodified) for executing agents:
+  vision + anti-goals + target/failing journeys verbatim, stable passing
+  journeys digested; sets `GOAL_SLICE_EXEC_PATH`/`GOAL_SLICE_EXEC_MODE`
+  (sliced|full-hatch|full-fallback), loud WARNING + `goal_slice_fallback`
+  telemetry on any builder failure (never blocks, never stale — the out-path
+  is used only on a fresh rc-0 non-empty build). Lean developer slices over
+  targets; lean browser-qa over targets ∪ its LLM set (every journey the LLM
+  executes stays verbatim); full-depth developer via `dev-phase.sh`'s new
+  goal-context line; full browser-qa over targets ∪ `_llm_regr_set`. Agent
+  bodies defer to "the goal file named in your dispatch prompt".
+- **Honest effect:** slice is O(targets+failing) vs goal.md O(all journeys) —
+  ~55-70% of goal-context bytes cut now, and the growth term stops growing;
+  wall saving is mostly indirect (fewer tokens to re-read per turn).
+- **Verify:** `bash tests/automation/test-goal-context-slice.sh` (26 cases:
+  slice content verbatim/digested, hatch, loud fallback, full-pipeline wiring).
+- **Rollback:** `CHAIN_DEV_FULL_GOAL=true` restores the full goal file at every
+  executor site.
+- **Stop-and-ask:** a developer building against a digested journey it should
+  have read (the slice prompt names the full file as the escape) — bring the
+  iteration before widening the slice.
+
 ---
 
 ## 10. P1 — Reliability & weaker-model hardening
@@ -3101,6 +3313,23 @@ territory).
 - **Rollback:** revert three files + version.
 - **Stop-and-ask:** none.
 
+### REP-5 · Attribute the two-key CONFIRM_ACHIEVED dispatch
+- **Priority:** P2 · **Effort:** S · **Risk:** LOW · **Status:** IN-PROGRESS —
+  implemented 2026-07-29 (iteration-shape package); G8 certification pending.
+- **Problem:** the two-key confirm dispatch (`lib/goal-gates.sh`) ran outside
+  the per-agent telemetry — ~5 min per achieving iteration rendered as
+  unattributed glue (desk: the evaluator bucket carried an invisible second
+  dispatch).
+- **Change spec (landed):** the dispatch is wrapped in guarded (`declare -F`)
+  `record_agent_invocation_start/end` under the name `goal-evaluator-confirm`;
+  the dispatch env keeps `CHAIN_CURRENT_AGENT=goal-evaluator` (pump permission
+  resolution knows the evaluator's grants, not the telemetry label). Lands in
+  the open iteration bucket — no analyzer change. Self-test stubs assert both
+  events; `unset -f` at cleanup.
+- **Verify:** `bash scripts/automation/lib/goal-gates.sh --self-test`.
+- **Rollback:** revert (measurement only; no behavior change).
+- **Stop-and-ask:** none.
+
 ---
 
 ## 14. P1 — Documentation & guides
@@ -3439,7 +3668,11 @@ but appreciated.
   real-session telemetry gate that parked SPEED-3's flip applies (the benchmark
   fixture failed to price the overlap three times).
 
-### CAND-DEV-CONTEXT · Developer dispatch context slims as sessions grow (staged — do not start)
+### CAND-DEV-CONTEXT · Developer dispatch context slims as sessions grow (PROMOTED 2026-07-29)
+- *(Sketch (a) — sliced goal view for the executor dispatches — was PROMOTED to
+  **TOKEN-10** and implemented 2026-07-29 with the desk evidence attached.
+  Sketches (b) scoped file digest and (c) read-vs-build time split remain
+  staged here, unchanged.)*
 - *(Staged 2026-07-17 from tapeology `fast_wall` forensics: developer run time grew
   monotonically 31 → 77 min across 6 iterations — the #1 wall-clock sink in every
   single iteration, 6.5h total.)*
@@ -4064,3 +4297,60 @@ Single source for the plain wording: the sentence table in
 `skills/plain-language.md` copy from it, never fork it.
 
 ### PLAIN-1 — DONE 2026-07-26, archived
+
+---
+
+## 20. P1 — Machine-level hardware safety (HOST-*, promoted 2026-07-29)
+
+Source: the 6th instant hard-reset of the reference host (GEEKOM A7 Max, Ryzen 9 7940HS,
+27.3G) on 2026-07-29 14:02:45, the FIRST one with per-session host-guard caps fully in
+place on both concurrent projects. Scoped by a Fable-5 planning session; user approval of
+that plan = EVO-1 promotion of this section (§18/§19 precedent). User-locked decisions:
+**shared mask `0-3,8-11`** for both projects (4 physical cores of guaranteed-dark
+headroom, accepting concurrent-throughput contention) over a wider overlapping scheme;
+boost regression ⇒ **pause** the engine, not warn; engine-mode QA browsers run
+**headless**.
+
+Hard rule for every HOST item: the framework stays project-neutral — absent
+`project-extensions/host-guard/host-guard.env` (or `HOST_GUARD_ENABLED=0`), and absent the
+machine budget file, every hook is a byte-for-byte no-op with at most a loud warning. The
... [diff_bound] incredible_auto_dev/docs/improvement-roadmap.md: 40 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index f83e43b9..77b2cc73 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -20,6 +20,11 @@ source "$SCRIPT_DIR/lib/replay-lane.sh"
 # shellcheck disable=SC2034  # consumed by lib/replay-lane.sh's log helpers
 REPLAY_LANE_TAG="browser-qa"
 
+# SPEED-15: pick up the engine's iteration clock so the trim ladder (rung 2
+# below) can consult the shared budget. Standalone phase mode has no epoch
+# exported → the budget machinery stays inert here, exactly as before.
+if [[ -n "${CHAIN_ITER_START_EPOCH:-}" ]]; then iter_budget_init; fi
+
 PHASE="${1:-}"
 require_phase_arg "$PHASE"
 require_claude
@@ -258,7 +263,37 @@ if [[ "$PHASE" =~ ^goal-(.+)-iter-[0-9]+$ ]]; then
   if [[ "$_use_replay" == "yes" ]]; then
     _llm_out="$LLM_RESULTS"
   fi
+  # SPEED-15 rung 2: capture the deferred set ONCE (the budget clock keeps
+  # ticking — a later recompute could disagree with what was dispatched);
+  # replay_lane_llm_regression_set narrows itself when it is non-empty, and
+  # the post-merge writer below appends the DEFERRED-BUDGET rows. Targets are
+  # excluded from deferral — they are dispatched regardless.
+  _bqa_targets="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
+  REPLAY_DEFERRED_BUDGET="$(replay_lane_deferred_budget_set "$_bqa_targets")"
+  if [[ -n "${REPLAY_DEFERRED_BUDGET// /}" ]]; then
+    echo "[browser-qa] iter-budget trim (rung 2): deferring no-golden regression journey(s) this iteration: ${REPLAY_DEFERRED_BUDGET% }— targets + replay-FAIL re-confirms are never deferred."
+    declare -F iter_budget_trim_event >/dev/null 2>&1 && iter_budget_trim_event "replay-narrow"
+  fi
   _llm_regr_set="$(replay_lane_llm_regression_set)"
+  # TOKEN-10: journey definitions for the regression lane come from a sliced
+  # goal view — targets ∪ this run's LLM regression set stay verbatim; only
+  # replay-covered/stable journeys are digested. Bare call: sets
+  # GOAL_SLICE_EXEC_PATH + GOAL_SLICE_EXEC_MODE (hatch/fallback → full file).
+  goal_slice_for_exec "$PHASE" \
+    "$(echo "$_bqa_targets $_llm_regr_set" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ',' | sed 's/,$//')" \
+    "$REPO_ROOT/runs/$PHASE/goal-slice-bqa.md"
+  _bqa_goal_ref="$GOAL_SLICE_EXEC_PATH"
+  _bqa_goal_note=""
+  [[ "$GOAL_SLICE_EXEC_MODE" == "sliced" ]] && _bqa_goal_note=" (a token-lean goal slice — every journey listed here appears verbatim; read the full docs/goal.md ONLY if a definition you need is missing)"
+  # SPEED-23: same rotating golden nudge as the lean lane — one gap journey in
+  # this run's LLM set gets its golden promoted to a REQUIRED deliverable.
+  _bqa_nudge="$(replay_lane_golden_nudge_pick "$_llm_regr_set" || true)"
+  if [[ -n "$_bqa_nudge" ]]; then
+    echo "[browser-qa] SPEED-23 golden nudge: $_bqa_nudge MUST get a golden replay script this dispatch (rotating pick from state/golden-gaps; CHAIN_GOLDEN_NUDGE=false disables)."
+    if declare -F record_telemetry_event >/dev/null 2>&1; then
+      record_telemetry_event "golden_nudge" "$(jq -cn --arg j "$_bqa_nudge" --arg n "$PHASE" '{journey:$j, iter_name:$n}' 2>/dev/null || printf '{"journey":"%s"}' "$_bqa_nudge")" || true
+    fi
+  fi
   _goal_lanes_note="
 
 GOAL-MODE REGRESSION LANES (goal-session iteration — IN ADDITION to the test plan):
@@ -266,7 +301,7 @@ $(if [[ "$_use_replay" == "yes" && -n "${R_REPLAY// /}" ]]; then
   echo "- Deterministic replay has ALREADY re-verified these Required-still-passing journeys from stored golden scripts: ${R_REPLAY% }. Do NOT re-test them and do NOT emit rows for them — their rows merge into the results automatically after your run. (If a test-plan case you execute anyway covers one, that is fine; your row supersedes the replay's.)"
 fi)
 $(if [[ -n "${_llm_regr_set// /}" ]]; then
-  echo "- ALSO execute these regression journeys this run: ${_llm_regr_set% }. For each: read its numbered steps + Acceptance line from the \"Must-have user journeys\" section of docs/goal.md, execute it like a test case, and add a results-table row using the journey ID as the Test ID (e.g. UT-J-01)."
+  echo "- ALSO execute these regression journeys this run: ${_llm_regr_set% }. For each: read its numbered steps + Acceptance line from the \"Must-have user journeys\" section of ${_bqa_goal_ref}${_bqa_goal_note}, execute it like a test case, and add a results-table row using the journey ID as the Test ID (e.g. UT-J-01)."
 fi)
 $(if [[ -n "${REPLAY_FAILED// /}" ]]; then
   echo "- The replay lane flagged possible regression(s) on: ${REPLAY_FAILED% } (already included in the list above). Re-confirm each by executing the journey yourself; if it passes, the replay FAIL was a stale golden script — repair that journey's golden so the next iteration replays clean."
@@ -277,7 +312,8 @@ PASS, ALSO write a self-contained deterministic replay script to
 $JOURNEY_SCRIPTS_DIR/<J-XX>.json (overwrite if present), IMMEDIATELY after that
 journey passes — follow the 'Golden replay script' section of your agent
 instructions for the exact JSON shape. Best-effort: if you cannot produce one for
-a journey, skip it (that journey just falls back to the LLM lane next time)."
+a journey, skip it (that journey just falls back to the LLM lane next time).
+$(if [[ -n "${_bqa_nudge:-}" ]]; then echo "REQUIRED DELIVERABLE (golden-coverage nudge): journey $_bqa_nudge keeps passing but still has NO golden replay script, so it rides this slow LLM lane every iteration. After verifying it this run you MUST write $JOURNEY_SCRIPTS_DIR/$_bqa_nudge.json before finishing — for THIS one journey the golden is NOT best-effort."; fi)"
 fi
 
 SERVICES_NOTE="Note: browser-qa-phase.sh manages backend (${BACKEND_HEALTH_URL}, log: ${QA_BACKEND_LOG}) and frontend (${FRONTEND_URL}, log: ${QA_FRONTEND_LOG}). Services are restarted automatically if they die during quota-retry sleeps."
@@ -286,6 +322,15 @@ SERVICES_NOTE="Note: browser-qa-phase.sh manages backend (${BACKEND_HEALTH_URL},
 # before claude attempts the next call.
 export CHAIN_CLAUDE_PRE_RETRY_HOOK="ensure_services_running"
 
+# ── Host-safety: pin the QA browser, run it headless, re-confine escapees ────
+# The Chrome MCP reconnects to and adopts browsers it did not spawn, so a
+# browser born unconfined stays unconfined however well the engine tree is
+# capped — and an unconfined headed Chrome is the burst profile that hard-reset
+# this host on 2026-07-29. All three calls no-op without a host-guard project.
+ensure_qa_browser_env ""
+strip_display_for_headless_qa
+bqa_browser_confine
+
 # ── REL-14 preflight (CHAIN_BQA_PREFLIGHT, default off) ─────────────────────
 # Probe services once more (+ one ensure_services_running retry) before burning
 # the browser-qa dispatch against dead infra. On persistent failure: skip the
@@ -390,6 +435,7 @@ if [[ "$GOAL_REPLAY_ACTIVE" == "yes" ]]; then
   fi
   if [[ "$_use_replay" == "yes" ]]; then
     replay_lane_merge_results "$UI_TEST_RESULTS" "$_llm_out"
+    replay_lane_write_deferred_rows "$UI_TEST_RESULTS"
   fi
   replay_lane_golden_coverage "$UI_TEST_RESULTS" "$PHASE"
 fi
@@ -432,4 +478,13 @@ if [[ $_bqa_rc -ne 0 && $_bqa_rc -ne ${QUOTA_EXHAUSTED_EXIT_CODE:-75} ]]; then
   exit "$_bqa_rc"
 fi
 
+# Opt-in browser reap (CHAIN_BQA_REAP=1). Default is leave-warm: reconnecting to
+# a live browser saves a cold start per dispatch, and an idle browser inside the
+# mask costs nothing. Never in interactive mode — the pump's MCP server is still
+# alive there and would just respawn what we killed.
+if [[ "${CHAIN_BQA_REAP:-0}" == "1" && "${CHAIN_AGENT_BACKEND:-}" != "interactive" \
+      && -f "$SCRIPT_DIR/host-guard/browser-confine.sh" ]]; then
+  HOST_GUARD_ROOT="$REPO_ROOT" bash "$SCRIPT_DIR/host-guard/browser-confine.sh" --reap || true
+fi
+
 echo "[browser-qa] Done. Report: $UI_TEST_RESULTS"
diff --git a/incredible_auto_dev/scripts/automation/demo-phase.sh b/incredible_auto_dev/scripts/automation/demo-phase.sh
index eac5f233..6a1f4a75 100755
--- a/incredible_auto_dev/scripts/automation/demo-phase.sh
+++ b/incredible_auto_dev/scripts/automation/demo-phase.sh
@@ -334,6 +334,20 @@ case "$_runner_rc" in
   *) echo "[demo] runner exited $_runner_rc (showcase, non-gating)." >&2 ;;
 esac
 
+# SPEED-21: after a GREEN record run of a goal iteration, auto-derive golden
+# replay candidates from the just-verified demo JSON while the services are
+# still up, verify each candidate for real, and install only the green ones
+# (lib/replay-lane.sh). Runs at both depths — demo-phase.sh is the one
+# recording hook the lean tail and the full pipeline share. Non-gating
+# showcase enrichment: any failure inside is contained.
+if [[ "$MODE" == "record" && $_runner_rc -eq 0 && "$ID" =~ ^goal-.+-iter-[0-9]+$ ]]; then
+  source "$SCRIPT_DIR/lib/replay-lane.sh"
+  # shellcheck disable=SC2034  # log prefix consumed by the lane lib
+  REPLAY_LANE_TAG="demo"
+  replay_lane_paths "$ID"
+  replay_lane_autoderive_goldens "$ID" "$DEMO_JSON_OUT" "$UI_TEST_RESULTS" || true
+fi
+
 if [[ "$MODE" == "record" ]]; then
   echo "[demo] Done. Script: $DEMO_SCRIPT_OUT"
   echo "[demo]       Results: $DEMO_RESULTS_OUT"
diff --git a/incredible_auto_dev/scripts/automation/dev-phase.sh b/incredible_auto_dev/scripts/automation/dev-phase.sh
index 23b18811..24e36877 100755
--- a/incredible_auto_dev/scripts/automation/dev-phase.sh
+++ b/incredible_auto_dev/scripts/automation/dev-phase.sh
@@ -66,6 +66,25 @@ fi
 
 echo "[dev-phase] Mode: $MODE_LABEL"
 
+# TOKEN-10 context diet: goal-mode full iterations hand the developer a sliced
+# goal view (vision + anti-goals + target/failing journeys verbatim; stable
+# passing journeys digested) — the agent body otherwise sends it to the whole
+# goal.md, which grows with every proposer-promoted journey. Plain phases keep
+# a plain goal line when docs/goal.md exists, else no line (as before).
+GOAL_CONTEXT_LINE=""
+if [[ "$PHASE" =~ ^goal-(.+)-iter-[0-9]+$ ]]; then
+  _dev_targets="$(grep -iE 'Target journeys:' "$SPEC" 2>/dev/null | head -1 | grep -oE 'J-[0-9]+' | sort -u | tr '\n' ',' | sed 's/,$//' || true)"
+  goal_slice_for_exec "$PHASE" "$_dev_targets" "$REPO_ROOT/runs/$PHASE/goal-slice-exec.md"
+  if [[ "$GOAL_SLICE_EXEC_MODE" == "sliced" ]]; then
+    GOAL_CONTEXT_LINE="Project goal (SLICED — vision, anti-goals, and this iteration's target + failing journeys verbatim; stable passing journeys digested to one line): $GOAL_SLICE_EXEC_PATH  <-- read Must-have user journeys and Anti-goals here
+Full goal file: docs/goal.md — Read it ONLY if a digested journey becomes relevant to your work."
+  else
+    GOAL_CONTEXT_LINE="Project goal: docs/goal.md  <-- read Must-have user journeys and Anti-goals"
+  fi
+elif [[ -f "$REPO_ROOT/docs/goal.md" ]]; then
+  GOAL_CONTEXT_LINE="Project goal: docs/goal.md  <-- read Must-have user journeys and Anti-goals"
+fi
+
 # ── Cleanup: kill any server processes started by the dev agent ──────────
 # The dev agent may start uvicorn/next dev for verification.  These are
 # long-running servers that block the agent from exiting if not cleaned up.
@@ -92,6 +111,7 @@ claude_with_quota_retry -p "You are the developer agent for phased development.
 
 Phase: $PHASE
 Phase spec: $SPEC
+$GOAL_CONTEXT_LINE
 Project template: .claude/project-template.md  <-- read this for stack info, test commands, architecture rules
 Agent instructions: .claude/agents/developer.md  <-- read this first
 (CLAUDE.md is already in your system prompt — do not Read it again.)
diff --git a/incredible_auto_dev/scripts/automation/doctor.sh b/incredible_auto_dev/scripts/automation/doctor.sh
index d3d63b06..d2215a28 100644
--- a/incredible_auto_dev/scripts/automation/doctor.sh
+++ b/incredible_auto_dev/scripts/automation/doctor.sh
@@ -58,7 +58,8 @@ source "$SCRIPT_DIR/lib/engine-lock.sh"
 ROOT="${CHAIN_DOCTOR_REPO_ROOT:-$REPO_ROOT}"
 
 CHECKS=(python3 node playwright chrome-mcp gh-auth git-remote disk timeout jq
-        pump-heartbeat engine-lock tmp-health chrome-exclusive ambient-env)
+        pump-heartbeat engine-lock tmp-health chrome-exclusive mcp-affinity
+        host-guard cpu-boost ambient-env)
 
 # Run a command under GNU/uutils timeout when available (network probes must
 # degrade, never hang). $1 = seconds, rest = command.
@@ -356,20 +357,170 @@ PY
   fi
 }
 
+# ── Host-guard rows (machine-level assumptions, read-only) ──────────────────
+# The doctor OBSERVES: it reads the project host-guard.env with sed rather than
+# sourcing it (never import arbitrary env), and it never sweeps the registry —
+# that is the engine's job.
+_hg_env_val() { # $1 key → value from the project host-guard.env ("" when absent)
+  sed -n "s/^[[:space:]]*$1=//p" "$ROOT/project-extensions/host-guard/host-guard.env" 2>/dev/null \
+    | tail -n 1 | tr -d '"'"'"
+}
+_hg_expand() { # "0-3,8-11" → CPU ids, one per line
+  local part a b i
+  local -a parts=()
+  IFS=',' read -ra parts <<< "${1:-}"
+  { for part in "${parts[@]}"; do
+      if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+        a="${part%-*}"; b="${part#*-}"; (( b >= a )) && for (( i=a; i<=b; i++ )); do echo "$i"; done
+      elif [[ "$part" =~ ^[0-9]+$ ]]; then echo "$part"; fi
+    done; } | sort -n -u
+}
+_hg_in_mask() { # $1 Cpus_allowed_list ⊆ $2 mask ?
+  local c; local -A super=()
+  while read -r c; do [[ -n "$c" ]] && super["$c"]=1; done < <(_hg_expand "$2")
+  while read -r c; do [[ -n "$c" ]] || continue; [[ -n "${super[$c]:-}" ]] || return 1; done < <(_hg_expand "$1")
+  return 0
+}
+_hg_allowed() { awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$1/status" 2>/dev/null; }
+_hg_cmdline() { tr '\0' ' ' < "/proc/$1/cmdline" 2>/dev/null; }
+_hg_qa_profile_root() { echo "${CHROME_PROFILE_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/superpowers/browser-profiles}"; }
+
 # EVIDENCE (run D, bench-20260715-0924): foreign Chrome processes caused
 # Chrome MCP DevTools-port contention — journeys REFUTED 0/3 and a ~$16 run
-# was lost. WARN (not FAIL): the operator may know the windows are unrelated.
+# was lost. EVIDENCE (2026-07-29 reset): a framework QA Chrome that the MCP
+# reconnected to, rather than spawned, keeps whatever CPU mask it was born
+# with — an unconfined headed Chrome rasterizing on every core is exactly the
+# burst profile that hard-resets this class of host. So: desktop Chrome is
+# informational, an unconfined framework QA Chrome is a FAIL.
 check_chrome_exclusive() {
   command -v pgrep >/dev/null 2>&1 || { echo "WARN|pgrep unavailable — cannot scan for competing chrome processes"; return; }
-  local out n list
-  out="$(pgrep -l 'chrom|headless_shell' 2>/dev/null || true)"
-  if [[ -z "$out" ]]; then
+  local pids p cmd mask enabled proot
+  pids="$(pgrep 'chrom|headless_shell' 2>/dev/null || true)"
+  if [[ -z "$pids" ]]; then
     echo "PASS|no competing chrome/chromium processes"
     return
   fi
-  n="$(printf '%s\n' "$out" | wc -l | tr -dc 0-9)"
-  list="$(printf '%s\n' "$out" | awk 'NR<=6 {printf "%s(%s) ", $1, $2}')"
-  echo "WARN|$n chrome-family process(es): ${list}— DevTools-port contention lost run D (~\$16); close them before browser-QA-heavy sessions"
+  enabled="$(_hg_env_val HOST_GUARD_ENABLED)"; mask="$(_hg_env_val HOST_GUARD_CPU_LIST)"
+  proot="$(_hg_qa_profile_root)"
+  local n_desktop=0 n_qa=0 n_loose=0 loose=""
+  for p in $pids; do
+    cmd="$(_hg_cmdline "$p")"
+    if [[ "$cmd" == *"$proot"* ]]; then
+      n_qa=$(( n_qa + 1 ))
+      if [[ "$enabled" == "1" && -n "$mask" ]] && ! _hg_in_mask "$(_hg_allowed "$p")" "$mask"; then
+        n_loose=$(( n_loose + 1 )); loose+="$p($(_hg_allowed "$p")) "
+      fi
+    else
+      n_desktop=$(( n_desktop + 1 ))
+    fi
+  done
+  if [[ "$enabled" != "1" || -z "$mask" ]]; then
+    local total=$(( n_desktop + n_qa )) list
+    list="$(pgrep -l 'chrom|headless_shell' 2>/dev/null | awk 'NR<=6 {printf "%s(%s) ", $1, $2}')"
+    echo "WARN|$total chrome-family process(es) ($n_qa framework QA, $n_desktop other): ${list}— DevTools-port contention lost run D (~\$16); close them before browser-QA-heavy sessions"
+    return
+  fi
+  if (( n_loose > 0 )); then
+    echo "FAIL|$n_loose framework QA chrome process(es) OUTSIDE HOST_GUARD_CPU_LIST=$mask: ${loose}— an unconfined browser can hard-reset this host; run scripts/automation/host-guard/browser-confine.sh"
+    return
+  fi
+  echo "PASS|$n_qa framework QA chrome process(es) confined to $mask; $n_desktop other chrome process(es) (informational — QA ports are pinned)"
+}
+
+# The Chrome MCP server spawns browsers as its own children, so they inherit
+# ITS affinity. A server started before the pump was confined therefore keeps
+# minting unconfined browsers no matter how often the browsers get re-tasksetted.
+check_mcp_affinity() {
+  command -v pgrep >/dev/null 2>&1 || { echo "WARN|pgrep unavailable — cannot scan for MCP servers"; return; }
+  local p cmd mask enabled n=0 loose="" n_loose=0
+  enabled="$(_hg_env_val HOST_GUARD_ENABLED)"; mask="$(_hg_env_val HOST_GUARD_CPU_LIST)"
+  for p in $(pgrep -f 'mcp/dist/index.js' 2>/dev/null || true); do
+    cmd="$(_hg_cmdline "$p")"
+    [[ "$cmd" == *superpowers-chrome* ]] || continue
+    n=$(( n + 1 ))
+    if [[ "$enabled" == "1" && -n "$mask" ]] && ! _hg_in_mask "$(_hg_allowed "$p")" "$mask"; then
+      n_loose=$(( n_loose + 1 )); loose+="$p($(_hg_allowed "$p")) "
+    fi
+  done
+  (( n > 0 )) || { echo "PASS|no superpowers-chrome MCP server running"; return; }
+  if [[ "$enabled" != "1" || -z "$mask" ]]; then
+    echo "PASS|$n superpowers-chrome MCP server(s); this project declares no CPU mask to enforce"
+    return
+  fi
+  if (( n_loose > 0 )); then
+    echo "FAIL|$n_loose superpowers-chrome MCP server(s) outside HOST_GUARD_CPU_LIST=$mask: ${loose}— every Chrome they spawn inherits that wider mask; run scripts/automation/host-guard-adopt.sh --cli-root-of <pid>"
+    return
+  fi
+  echo "PASS|$n superpowers-chrome MCP server(s) confined to $mask"
+}
+
+# EVIDENCE (2026-07-29 14:02:45 reset): trendora "0-3,8-11" + tapeology
+# "4-7,12-15" — each session's own check green, union = every core. A per-scope
+# ceiling is not a machine budget; this row shows the machine view.
+check_host_guard() {
+  local enabled mask mem
+  enabled="$(_hg_env_val HOST_GUARD_ENABLED)"; mask="$(_hg_env_val HOST_GUARD_CPU_LIST)"
+  mem="$(_hg_env_val HOST_GUARD_MEMORY_HIGH)"
+  [[ "$enabled" == "1" ]] || { echo "PASS|this project declares no host-guard (project-extensions/host-guard/host-guard.env absent or disabled)"; return; }
+  local lib="$SCRIPT_DIR/lib/host-guard-registry.sh"
+  [[ -f "$lib" ]] || { echo "WARN|host-guard.env declares CPU mask $mask but lib/host-guard-registry.sh is missing — no machine-global bound"; return; }
+  # shellcheck disable=SC1090
+  ( source "$lib"
+    hg_load_host_env
+    local hostf n=0 r roots="" verdict
+    hostf="$(hg_host_env_file)"
+    while read -r r; do
+      [[ -n "$r" ]] || continue
+      n=$(( n + 1 ))
+      roots+="$(_hg_rec_field "$r" kind):$(basename "$(_hg_rec_field "$r" project_root)")[$(_hg_rec_field "$r" cpu_list)] "
+    done < <(hg_live_records)
+    if [[ -z "${HOST_GUARD_GLOBAL_CPU_LIST:-}" ]]; then
+      echo "WARN|mask=$mask mem=$mem, $n live guarded context(s): ${roots:-none} — but NO machine budget is configured ($hostf); concurrent projects are unbounded (docs/host-guard.md § Machine-global aggregate budget)"
+      return
+    fi
+    if ! _hg_mask_is_subset "$mask" "$HOST_GUARD_GLOBAL_CPU_LIST"; then
+      echo "FAIL|this project's mask $mask is NOT inside the machine budget HOST_GUARD_GLOBAL_CPU_LIST=$HOST_GUARD_GLOBAL_CPU_LIST ($hostf) — the engine will pause AWAITING_HOST_GUARD"
+      return
+    fi
+    verdict="$(hg_aggregate_verdict "")"
+    case "$verdict" in
+      OK) echo "PASS|mask=$mask mem=$mem inside machine budget ${HOST_GUARD_GLOBAL_CPU_LIST}/${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-unset}; $n live guarded context(s): ${roots:-none}" ;;
+      *)  echo "WARN|${verdict#*|}" ;;
+    esac
+  )
+}
+
+# EVIDENCE: boost-off was applied live on 2026-07-28 as the hardware mitigation
+# and silently reverted at the next reboot — the tmpfiles.d rule that persists
+# it was never installed. A guard that does not verify its own premise is
+# decoration, so this row checks BOTH the live knob and its persistence.
+check_cpu_boost() {
+  local p rule v required=0 hostf
+  p="${HOST_GUARD_SYS_BOOST_PATH:-/sys/devices/system/cpu/cpufreq/boost}"
+  rule="${CHAIN_DOCTOR_BOOST_RULE:-/etc/tmpfiles.d/cpufreq-boost.conf}"
+  # Only a machine that ASKED for boost-off gets a FAIL. Elsewhere the row is
+  # informational — the framework must not judge hosts that never opted in.
+  hostf="${HOST_GUARD_HOST_ENV_FILE:-$HOME/.config/iad/host-guard-host.env}"
+  if [[ -f "$hostf" ]] && grep -qE '^[[:space:]]*HOST_GUARD_REQUIRE_BOOST_OFF[[:space:]]*=[[:space:]]*"?1' "$hostf" 2>/dev/null; then
+    required=1
+  fi
+  [[ -r "$p" ]] || { echo "PASS|no CPU boost knob at $p — this host exposes no boost control"; return; }
+  v="$(tr -dc '0-9' < "$p" 2>/dev/null)"
+  if [[ "$v" != "0" ]]; then
+    if (( required )); then
+      echo "FAIL|CPU boost is ON ($p=$v) but $hostf requires it off — goal mode will pause AWAITING_HOST_GUARD: echo 0 | sudo tee $p (persist: $rule, docs/host-guard.md § Boost persistence)"
+    else
+      echo "PASS|CPU boost is ON ($p=$v); this machine does not require it off (no HOST_GUARD_REQUIRE_BOOST_OFF=1 in $hostf)"
+    fi
+    return
+  fi
+  if [[ -f "$rule" ]]; then
+    echo "PASS|CPU boost off and persisted ($rule)"
+  elif (( required )); then
+    echo "WARN|CPU boost is off but NOT persisted — it will silently re-enable at the next reboot; install $rule (docs/host-guard.md § Boost persistence)"
+  else
+    echo "PASS|CPU boost is off ($p=0)"
+  fi
 }
 
 # EVIDENCE (§9 measurement discipline): benchmark/measurement runs record
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 6b31c2c8..21e9922d 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -203,6 +203,10 @@ trap 'cleanup_iter_servers; chain_tmp_cleanup' EXIT
 # benchmark iter-0s died on exactly that parse before the guard existed).
 TARGET_JOURNEYS="$(replay_lane_spec_journeys 'Target journeys:' "$SPEC")"
 REQUIRED_JOURNEYS="$(replay_lane_spec_journeys 'Required-still-passing' "$SPEC")"
+# SPEED-22: only the lean executor has a canary dispatch slot, so only it may
+# arm the mass-false-FAIL breaker inside the shared replay lane (the full
+# pipeline stays byte-identical). Exported so the SPEED-2/3 forks inherit it.
+export REPLAY_LANE_CANARY_CAPABLE=1
 # REL-14 make-up: journeys whose browser evidence was infra-blocked last
 # iteration ride the Required set as verify-only work (run-goal.sh exports the
 # set; empty/unset = today's behavior). Unioned BEFORE _bq_sig so checkpoint
@@ -213,6 +217,23 @@ if [[ -n "${CHAIN_BQA_MAKEUP_JOURNEYS:-}" ]]; then
 fi
 _bq_sig="${TARGET_JOURNEYS}|${REQUIRED_JOURNEYS}"
 
+# TOKEN-10 context diet: the developer dispatch gets a sliced goal view
+# (vision + anti-goals + this iteration's target and failing journeys
+# VERBATIM; stable passing journeys digested to one line) instead of the whole
+# goal.md — the goal file grows with every proposer-promoted journey (desk
+# session: 97KB, developer wall 31→77 min). Bare call: sets
+# GOAL_SLICE_EXEC_PATH + GOAL_SLICE_EXEC_MODE (hatch CHAIN_DEV_FULL_GOAL=true
+# restores the full file; any builder failure falls back loudly).
+goal_slice_for_exec "$ITER_NAME" \
+  "$(echo "$TARGET_JOURNEYS" | tr ' ' ',' | sed 's/^,*//;s/,*$//')" \
+  "${ITER_DIR:-$REPO_ROOT/runs/$ITER_NAME}/goal-slice-exec.md"
+if [[ "$GOAL_SLICE_EXEC_MODE" == "sliced" ]]; then
+  DEV_GOAL_CONTEXT="Project goal (SLICED — vision, anti-goals, and this iteration's target + failing journeys verbatim; stable passing journeys digested to one line): $GOAL_SLICE_EXEC_PATH  <-- read Must-have user journeys and Anti-goals here
+Full goal file: $GOAL_FILE — Read it ONLY if a digested journey becomes relevant to your work."
+else
+  DEV_GOAL_CONTEXT="Project goal: $GOAL_FILE  <-- read Must-have user journeys and Anti-goals"
+fi
+
 # Lane path derivations (EVIDENCE_DIR, JOURNEY_SCRIPTS_DIR, REGRESSION_RESULTS,
 # LLM_RESULTS, DEMO_RUNNER, MERGE_RESULTS) are replay_lane_paths in
 # lib/replay-lane.sh — shared by the forkable unit, the join, and the reap;
@@ -343,6 +364,8 @@ _bqa_state_save() {
     printf 'R_LLM=%q\n'                "${R_LLM:-}"
     printf 'REPLAY_FAILED=%q\n'        "${REPLAY_FAILED:-}"
     printf 'REPLAY_SKIPPED_INFRA=%q\n' "${REPLAY_SKIPPED_INFRA:-}"
+    printf 'REPLAY_MASS_FAIL=%q\n'     "${REPLAY_MASS_FAIL:-}"
+    printf 'REPLAY_CANARIES=%q\n'      "${REPLAY_CANARIES:-}"
     printf 'export QA_BACKEND_HEALTH_URL=%q\n'       "${QA_BACKEND_HEALTH_URL:-}"
     printf 'export QA_BACKEND_START_CMD=%q\n'        "${QA_BACKEND_START_CMD:-}"
     printf 'export QA_BACKEND_LOG=%q\n'              "${QA_BACKEND_LOG:-}"
@@ -410,7 +433,7 @@ _bqa_fork_reap() {
   # ports so the sequential rerun boots on the fixed tree.
   _bqa_kill_port_servers
   replay_lane_paths "$ITER_NAME"
-  rm -f "$_BQA_STATE_FILE" "$_BQA_RC_FILE" "${REGRESSION_RESULTS:-}" 2>/dev/null || true
+  rm -f "$_BQA_STATE_FILE" "$_BQA_RC_FILE" "${REGRESSION_RESULTS:-}" "${CANARY_RESULTS:-}" 2>/dev/null || true
   echo "[goal-iter-lean] Forked replay lane is dead and its lane files are discarded — safe to invalidate."
   return 0
 }
@@ -487,7 +510,7 @@ _bqa_full_fork_reap() {
   _bqa_kill_port_servers
   replay_lane_paths "$ITER_NAME"
   rm -f "$_BQA_FULL_RC_FILE" "$_BQA_FULL_PID_FILE" \
-        "${REGRESSION_RESULTS:-}" "${LLM_RESULTS:-}" "${UI_TEST_RESULTS:-}" 2>/dev/null || true
+        "${REGRESSION_RESULTS:-}" "${LLM_RESULTS:-}" "${UI_TEST_RESULTS:-}" "${CANARY_RESULTS:-}" 2>/dev/null || true
   record_telemetry_event "parallel_bqa_wasted_dispatch" "$(jq -cn --arg n "$ITER_NAME" \
       '{mode:"full", iter_name:$n,
         wasted:"one full browser-qa dispatch (LLM lane included) ran against the pre-fix tree and was discarded on the attempt-1 review FAIL",
@@ -644,14 +667,14 @@ run_browser_qa_llm() {
 
 Iteration: $ITER_NAME
 Iter spec: $SPEC
-Project goal: $GOAL_FILE  <-- read \"Must-have user journeys\" section for journey definitions
+$BQA_GOAL_LINE
 Agent instructions: .claude/agents/browser-qa-agent.md  <-- read this first
 (CLAUDE.md is already in your system prompt — do not Read it again.)
 Skill: .claude/skills/browser-workflow-executor.md  <-- read for Chrome MCP technique
 
 GOAL-MODE LEAN MODE — test EXACTLY these journeys this run: ${_journeys:-(none)}
 $( [[ -n "${_exclude// /}" ]] && echo "Do NOT test these — a deterministic replay verifies them separately: $_exclude" )
-  1. For each journey ID above, read its numbered steps + Acceptance line from the project goal's \"Must-have user journeys\" section.
+  1. For each journey ID above, read its numbered steps + Acceptance line from the \"Must-have user journeys\" section of the goal file named above.
   2. Execute the steps with Chrome MCP; use the journey ID as the test case ID (e.g. UT-J-01).
 
 Frontend URL: $FRONTEND_URL
@@ -665,7 +688,7 @@ else
 fi)
 
 For each journey:
-  - Execute the numbered steps exactly as written in goal.md
+  - Execute the numbered steps exactly as written in the goal file named above
   - Verify the Acceptance condition
   - Take a screenshot of the end state, save to reports/qa/${ITER_NAME}-evidence/
   - Record PASS / FAIL / SKIP with a short failure description if FAIL
@@ -677,6 +700,7 @@ re-verify it without a browser-driving model. Follow the 'Golden replay script'
 section of your agent instructions for the exact JSON shape. Best-effort: if you
 cannot produce one for a journey, skip it (that journey just falls back to the LLM
 next time).
+$( [[ -n "${NUDGE_JOURNEY:-}" ]] && echo "REQUIRED DELIVERABLE (golden-coverage nudge): journey $NUDGE_JOURNEY keeps passing but still has NO golden replay script, so it rides this slow LLM lane every iteration. After verifying it this run you MUST write $JOURNEY_SCRIPTS_DIR/$NUDGE_JOURNEY.json before finishing — for THIS one journey the golden is NOT best-effort." )
 
 Write your results to: $_out
 Use template: templates/ui-test-results.md
@@ -698,9 +722,61 @@ Then STOP." || _rc=$?
 # (Golden partition + lane 1 — the deterministic replay — live inside
 # run_browser_qa_boot_and_replay above: they already ran, inline or forked.)
 
-# Lane 2 — LLM browser-qa-agent.
+# TOKEN-10: build the browser-qa goal line over a given journey set — every
+# journey a dispatch executes must stay VERBATIM in the slice it reads.
+# Callable more than once per run: the SPEED-22 canary probe needs a goal line
+# BEFORE the final LLM set exists, and the main dispatch rebuilds over the
+# final union (the canary dispatch is synchronous, so it has fully consumed
+# the earlier slice file before the rebuild overwrites it). Bare call: sets
+# BQA_GOAL_LINE (+ GOAL_SLICE_EXEC_PATH/MODE via goal_slice_for_exec).
+_build_bqa_goal_line() {  # $1 = space-separated journeys to keep verbatim
+  goal_slice_for_exec "$ITER_NAME" \
+    "$(echo "$1" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ',' | sed 's/,$//')" \
+    "${ITER_DIR:-$REPO_ROOT/runs/$ITER_NAME}/goal-slice-bqa.md"
+  if [[ "$GOAL_SLICE_EXEC_MODE" == "sliced" ]]; then
+    BQA_GOAL_LINE="Project goal (SLICED — every journey you are asked to test below is verbatim; stable passing journeys digested to one line): $GOAL_SLICE_EXEC_PATH  <-- read \"Must-have user journeys\" section for journey definitions
+Full goal file: $GOAL_FILE — Read it ONLY if a journey definition you need is missing from the sliced file."
+  else
+    BQA_GOAL_LINE="Project goal: $GOAL_FILE  <-- read \"Must-have user journeys\" section for journey definitions"
+  fi
+}
+
+# SPEED-22 canary probe — runs BEFORE the LLM set is computed, because a void
+# empties REPLAY_FAILED and thereby shrinks the main dispatch. A majority-FAIL
+# replay run is re-checked with the 2 lowest-ID FAILs first: both green →
+# every replay FAIL is voided as drift (rows rewritten SKIP + loud footer,
+# goldens queued for regeneration, prior statuses kept); any canary FAIL (or
+# an unusable canary file — conservative) → today's full re-confirm path for
+# the REMAINING set (the canaries' own fresh verdicts ride the merge as a
+# middle input either way).
+if [[ "${REPLAY_MASS_FAIL:-}" == "yes" && -n "${REPLAY_CANARIES// /}" ]]; then
+  echo "[goal-iter-lean] SPEED-22: dispatching canary re-confirms for ${REPLAY_CANARIES% }(instead of immediately re-confirming all of: ${REPLAY_FAILED% })."
+  _build_bqa_goal_line "$TARGET_JOURNEYS $REPLAY_CANARIES"   # the canary prompt needs its own goal line — the main one is built later
+  _canary_rc=0
+  run_browser_qa_llm "$(echo "$REPLAY_CANARIES" | tr ' ' ',' | sed 's/^,*//;s/,*$//')" "$CANARY_RESULTS" "" || _canary_rc=$?
+  if [[ "$_canary_rc" -eq 0 ]] && replay_lane_canaries_all_pass "$CANARY_RESULTS" "$REPLAY_CANARIES"; then
+    replay_lane_void_mass_fail "$ITER_NAME" || true
+  else
+    echo "[goal-iter-lean] SPEED-22: canary re-check did NOT clear the mass FAIL (rc=$_canary_rc) — keeping the full re-confirm path for the remaining set."
+    record_telemetry_event "replay_mass_fail_confirmed" "$(jq -cn --arg n "$ITER_NAME" --arg c "${REPLAY_CANARIES% }" --arg j "${REPLAY_FAILED% }" '{iter_name:$n, canaries:$c, journeys:$j}' 2>/dev/null || printf '{"iter_name":"%s"}' "$ITER_NAME")"
+    # The canaries were just freshly re-tested — drop them from the main
+    # re-confirm set; their verdicts enter the merge via the canary file.
+    REPLAY_FAILED="$(echo "$REPLAY_FAILED" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | grep -vxF -f <(echo "$REPLAY_CANARIES" | tr ' ' '\n' | grep -E '^J-[0-9]+$') | tr '\n' ' ' || true)"
+  fi
+fi
+
+# Lane 2 — LLM browser-qa-agent. The regression portion comes from the shared
+# helper; SPEED-15 rung 2 narrows it when over budget in trim mode. The
+# deferred set is captured ONCE here (the budget clock keeps ticking — a later
+# recompute could disagree with what was dispatched) and reused by the
+# post-merge deferred-row writer below.
+REPLAY_DEFERRED_BUDGET="$(replay_lane_deferred_budget_set "$TARGET_JOURNEYS")"
+if [[ -n "${REPLAY_DEFERRED_BUDGET// /}" ]]; then
+  echo "[goal-iter-lean] iter-budget trim (rung 2): deferring no-golden regression journey(s) this iteration: ${REPLAY_DEFERRED_BUDGET% }— targets + replay-FAIL re-confirms are never deferred."
+  declare -F iter_budget_trim_event >/dev/null 2>&1 && iter_budget_trim_event "replay-narrow"
+fi
 if [[ "$_use_replay" == "yes" ]]; then
-  _llm_set="$TARGET_JOURNEYS $R_LLM $REPLAY_FAILED"   # targets + no-golden regression + replay re-confirms
+  _llm_set="$TARGET_JOURNEYS $(replay_lane_llm_regression_set)"   # targets + (no-golden regression + replay re-confirms, minus rung-2 deferrals)
   _llm_out="$LLM_RESULTS"
 else
   _llm_set="$TARGET_JOURNEYS $REQUIRED_JOURNEYS"       # replay off → LLM covers everything (prior behaviour)
@@ -709,9 +785,33 @@ fi
 LLM_JOURNEYS="$(echo "$_llm_set" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ' ' || true)"   # same pipefail guard as replay_lane_spec_journeys: an all-replay iteration has an empty LLM set
 _llm_csv="$(echo "$LLM_JOURNEYS" | tr ' ' ',' | sed 's/^,*//;s/,*$//')"
 
+# TOKEN-10: the browser-qa dispatch also gets a sliced goal view. Slice
+# targets = TARGET_JOURNEYS ∪ the LLM set, so EVERY journey this dispatch
+# executes keeps its full step definitions verbatim — only journeys the
+# deterministic replay lane covers (or that are outside this run entirely)
+# are digested. Bare call: sets BQA_GOAL_LINE (rebuilds the slice file even if
+# the canary probe built an earlier, narrower one — that dispatch is done).
+_build_bqa_goal_line "$TARGET_JOURNEYS $LLM_JOURNEYS"
+
+# SPEED-23: promote ONE persisted golden-coverage gap riding this LLM set from
+# best-effort golden authoring to a REQUIRED deliverable (rotating pick — see
+# replay_lane_golden_nudge_pick). Ends the J-06-class tax where a journey rides
+# the slow LLM lane for many iterations because its golden never gets written.
+NUDGE_JOURNEY="$(replay_lane_golden_nudge_pick "$LLM_JOURNEYS" || true)"
+if [[ -n "$NUDGE_JOURNEY" ]]; then
+  echo "[goal-iter-lean] SPEED-23 golden nudge: $NUDGE_JOURNEY MUST get a golden replay script this dispatch (rotating pick from state/golden-gaps; CHAIN_GOLDEN_NUDGE=false disables)."
+  record_telemetry_event "golden_nudge" "$(jq -cn --arg j "$NUDGE_JOURNEY" --arg n "$ITER_NAME" '{journey:$j, iter_name:$n}' 2>/dev/null || printf '{"journey":"%s"}' "$NUDGE_JOURNEY")"
+fi
+
 _bqa_rc=0
 _bqa_dispatched="no"
 _bqa_infra_blocked="no"
+# Host-safety: pinned + headless + confined QA browser (see browser-qa-phase.sh).
+# Plain calls, never a subshell: run_browser_qa_llm's quota path can exit this
+# script, and a subshell would swallow that exit.
+ensure_qa_browser_env ""
+strip_display_for_headless_qa
+bqa_browser_confine
 # REL-14 preflight (CHAIN_BQA_PREFLIGHT, default off): when the lane is about
 # to dispatch against a browser-visible frontend, probe services first (+ one
 # ensure_services_running retry) instead of burning a ~20m LLM dispatch on dead
@@ -753,6 +853,7 @@ fi
 # so no stale FAIL survives the iteration on disk.
 if [[ "$_use_replay" == "yes" ]]; then
   replay_lane_merge_results "$UI_TEST_RESULTS" "$_llm_out"
+  replay_lane_write_deferred_rows "$UI_TEST_RESULTS"
 fi
 
 # REL-14 post-scan (same knob): a dispatch that returned but left no results
@@ -806,7 +907,7 @@ run_developer() {
 
 Iteration: $ITER_NAME
 Iter spec: $SPEC
-Project goal: $GOAL_FILE  <-- read Must-have user journeys and Anti-goals
+$DEV_GOAL_CONTEXT
 Project template: .claude/project-template.md
 Agent instructions: .claude/agents/developer.md  <-- read this first
 (CLAUDE.md is already in your system prompt — do not Read it again.)
diff --git a/incredible_auto_dev/scripts/automation/host-guard-adopt.sh b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
index ce754e24..403f2b71 100755
--- a/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard-adopt.sh
@@ -65,6 +65,27 @@ _width() { # "0-3,8-11" → 8; 0 when unparseable
 _ppid() { awk '/^PPid:/{print $2}' "/proc/$1/status" 2>/dev/null || true; }
 _allowed_n() { _width "$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$1/status" 2>/dev/null)"; }
 
+_SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+
+# Publish this pump into the machine-global registry so a concurrent project's
+# engine can see its CPU/memory footprint when it computes the aggregate.
+# Best effort — a registry problem must never fail an otherwise-good adoption.
+_register_pump() {
+  # shellcheck disable=SC1091
+  source "$_SELF_DIR/lib/host-guard-registry.sh" 2>/dev/null || return 0
+  hg_register pump "$TARGET" "$ROOT" "${HOST_GUARD_SESSION_ID:-}" \
+    "$HOST_GUARD_CPU_LIST" "${HOST_GUARD_MEMORY_HIGH:-18G}" >/dev/null 2>&1 || true
+}
+
+# Re-confine QA browsers that escaped the process tree. The Chrome MCP reuses
+# and adopts browsers it did not spawn, and detached Chromes outlive their MCP
+# server (reparented to init) — neither is reachable by the descendant walk
+# below, so a taskset of the pump tree alone leaves them unconfined.
+_browser_pass() {
+  [[ -f "$_SELF_DIR/host-guard/browser-confine.sh" ]] || return 0
+  HOST_GUARD_ROOT="$ROOT" bash "$_SELF_DIR/host-guard/browser-confine.sh" || true
+}
+
 TARGET="$PID"
 if [[ "$MODE_ROOT" == "1" ]]; then
   _pat="${HOST_GUARD_CLI_PATTERN:-claude|codex}" _p="$PID" _best=""
@@ -86,6 +107,10 @@ if (( WIDTH == 0 )); then
 fi
 if (( $(_allowed_n "$TARGET") <= WIDTH )); then
   echo "[host-guard-adopt] pid $TARGET already confined ($(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$TARGET/status"))."
+  # An already-confined pump is the COMMON case, and it is exactly when an
+  # escaped browser goes unnoticed — sweep before returning, never after.
+  _register_pump
+  _browser_pass
   exit 0
 fi
 
@@ -115,6 +140,8 @@ done
 
 if (( $(_allowed_n "$TARGET") <= WIDTH )); then
   echo "[host-guard-adopt] confined pid $TARGET (and descendants) to CPUs $HOST_GUARD_CPU_LIST."
+  _register_pump
+  _browser_pass
   exit 0
 fi
 echo "[host-guard-adopt] FAILED to confine pid $TARGET (Cpus_allowed_list unchanged)." >&2
diff --git a/incredible_auto_dev/scripts/automation/host-guard-exec.sh b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
index bb9ac601..b1d11ed0 100755
--- a/incredible_auto_dev/scripts/automation/host-guard-exec.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
@@ -46,6 +46,23 @@ if [[ "${HOST_GUARD_BLAS_THREADS:-}" =~ ^[0-9]+$ ]]; then
   export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
 fi
 
+# NOTE: no CHROME_WS_PROFILE pin here. The pump serves BOTH QA lanes (run-phase.sh
+# runs Branch-QA and Branch-UI concurrently), and an explicit profile disables the
+# Chrome-MCP's per-lane auto-disambiguation — the two lanes would end up sharing one
+# browser and stepping on each other's tabs. Pump browsers are made safe by affinity
+# instead: host-guard/browser-confine.sh confines everything under the profile root,
+# named or not. Engine-mode lanes pin per-lane identities themselves (lib/common.sh
+# ensure_qa_browser_env), where the export is actually honored.
+
+# Publish this wrapped pump into the machine-global registry (exec preserves
+# both the pid and its start time, so this record tracks the CLI tree's root).
+if [[ -f "$(dirname "${BASH_SOURCE[0]}")/lib/host-guard-registry.sh" ]]; then
+  # shellcheck disable=SC1091
+  source "$(dirname "${BASH_SOURCE[0]}")/lib/host-guard-registry.sh" 2>/dev/null \
+    && hg_register pumpexec "$$" "$ROOT" "${HOST_GUARD_SESSION_ID:-}" \
+         "$HOST_GUARD_CPU_LIST" "${HOST_GUARD_MEMORY_HIGH:-18G}" >/dev/null 2>&1 || true
+fi
+
 _PROPS=( -p "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}"
          -p "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}"
          -p "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" )
diff --git a/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh b/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh
new file mode 100755
index 00000000..68a373e7
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/browser-confine.sh
@@ -0,0 +1,225 @@
+#!/usr/bin/env bash
+# browser-confine.sh — put escaped QA browsers back inside the host-guard mask.
+#
+# WHY: host-guard confines process TREES, and a Chrome the MCP server spawns
+# does inherit the mask. But the superpowers-chrome MCP does not always spawn:
+#   - it RECONNECTS to a browser recorded in <profile>.meta.json whose port+pid
+#     are still alive, and
+#   - it ADOPTS an orphan Chrome found by scanning ps for its --user-data-dir.
+# A browser born in an unconfined session therefore keeps its wide mask forever,
+# no matter how many times the pump itself is confined. Worse, Chrome is spawned
+# detached and unref'd, so once its MCP server exits the browser is reparented
+# to init — invisible to host-guard-adopt.sh's `pgrep -P` descendant walk.
+#
+# An unconfined headed Chrome rasterizing across every core is precisely the
+# bursty all-core profile that hard-resets this class of mini-PC (2026-07-29).
+#
+# WHAT IT DOES (four passes, all idempotent, all best-effort):
+#   A. QA browsers  — re-taskset any main Chrome process holding a superpowers
+#      browser profile; kill only when taskset fails AND the profile is ours.
+#   B. MCP servers  — re-taskset the node servers themselves (never killed: the
+#      pump's live session depends on them), so their FUTURE children are born
+#      confined.
+#   C. Stale files  — drop <profile>.meta.json / .mcp.lock whose pid is gone, so
+#      the next dispatch cold-starts instead of "reconnecting" to a corpse.
+#   D. Reap (--reap, opt-in) — TERM this project's own QA browsers at phase end.
+#
+# Absent/disabled host-guard.env (or HOST_GUARD_BROWSER_CONFINE=0) ⇒ no-op:
+# the framework stays project-neutral.
+#
+# Usage: browser-confine.sh [--reap]
+# Exit:  always 0 (advisory pass — never fail a QA phase over browser hygiene).
+set -uo pipefail
+
+REAP=0
+case "${1:-}" in
+  --reap) REAP=1 ;;
+  "") ;;
+  *) echo "usage: browser-confine.sh [--reap]" >&2; exit 2 ;;
+esac
+
+ROOT="${HOST_GUARD_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
+ENV_FILE="$ROOT/project-extensions/host-guard/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" 2>/dev/null
+if [[ "${HOST_GUARD_ENABLED:-0}" != "1" || -z "${HOST_GUARD_CPU_LIST:-}" \
+      || "${HOST_GUARD_BROWSER_CONFINE:-1}" == "0" ]]; then
+  echo "[browser-confine] host-guard absent/disabled for $ROOT — nothing to do."
+  exit 0
+fi
+if ! command -v taskset >/dev/null 2>&1; then
+  echo "[browser-confine] taskset unavailable — cannot confine browsers." >&2
+  exit 0
+fi
+
+MASK="$HOST_GUARD_CPU_LIST"
+PROFILE_ROOT="${CHROME_PROFILE_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/superpowers/browser-profiles}"
+_proj="$ROOT"; [[ "$_proj" == */incredible_auto_dev ]] && _proj="${_proj%/incredible_auto_dev}"
+BASE="$(basename "$_proj")"
+OWN_DIRS=( "$PROFILE_ROOT/iad-qa-$BASE" "$PROFILE_ROOT/iad-qa-$BASE-qa" )
+UID_SELF="$(id -u)"
+
+# ── helpers ──────────────────────────────────────────────────────────────────
+_expand() { # "0-3,8-11" → CPU ids, one per line
+  local part a b i; local -a parts=()
+  IFS=',' read -ra parts <<< "${1:-}"
+  { for part in "${parts[@]}"; do
+      if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+        a="${part%-*}"; b="${part#*-}"; (( b >= a )) && for (( i=a; i<=b; i++ )); do echo "$i"; done
+      elif [[ "$part" =~ ^[0-9]+$ ]]; then echo "$part"; fi
+    done; } | sort -n -u
+}
+_width() { _expand "${1:-}" | wc -l | tr -dc 0-9; }
+_is_subset() { # $1 ⊆ $2
+  local c; local -A super=()
+  while read -r c; do [[ -n "$c" ]] && super["$c"]=1; done < <(_expand "${2:-}")
+  while read -r c; do [[ -n "$c" ]] || continue; [[ -n "${super[$c]:-}" ]] || return 1; done < <(_expand "${1:-}")
+  return 0
+}
+_cmdline() { tr '\0' ' ' < "/proc/$1/cmdline" 2>/dev/null; }
+_allowed() { awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$1/status" 2>/dev/null; }
+_descendants() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do echo "$c"; _descendants "$c"; done; }
+
+# Same-UID processes only: never touch another user's browser.
+_scan() { # every arg must appear in the cmdline
+  local p cmd want ok
+  for p in /proc/[0-9]*; do
+    p="${p#/proc/}"
+    [[ "$p" == "$$" || "$p" == "$PPID" ]] && continue
+    [[ "$(stat -c %u "/proc/$p" 2>/dev/null)" == "$UID_SELF" ]] || continue
+    cmd="$(_cmdline "$p")"
+    [[ -n "$cmd" ]] || continue
+    ok=1
+    for want in "$@"; do [[ "$cmd" == *"$want"* ]] || { ok=0; break; }; done
+    (( ok )) && echo "$p"
+  done
+}
+
+_confine_tree() { # taskset pid + descendants; rc 0 when the pid ends up inside
+  local pid="$1" c
+  taskset -a -c -p "$MASK" "$pid" >/dev/null 2>&1 || true
+  for c in $(_descendants "$pid"); do
+    taskset -a -c -p "$MASK" "$c" >/dev/null 2>&1 || true
+  done
+  # Second sweep: renderers forked while the first pass ran.
+  for c in $(_descendants "$pid"); do
+    taskset -a -c -p "$MASK" "$c" >/dev/null 2>&1 || true
+  done
+  _is_subset "$(_allowed "$pid")" "$MASK"
+}
+
+_owned() { # cmdline holds one of OUR pinned profile dirs (exact --user-data-dir arg)
+  local cmd="$1" d
+  for d in "${OWN_DIRS[@]}"; do
+    [[ "$cmd" == *"--user-data-dir=$d "* || "$cmd" == *"--user-data-dir=$d" ]] && return 0
+  done
+  return 1
+}
+
+_sweep_profile_files() { # $1 profile dir → drop its meta/lock
+  local d="$1" n="${1##*/}"
+  rm -f "$PROFILE_ROOT/$n.meta.json" "$PROFILE_ROOT/$n.mcp.lock" 2>/dev/null || true
+}
+
+_terminate() { # TERM, then KILL after 3s
+  local pid="$1" i
+  kill -TERM "$pid" 2>/dev/null || return 1
+  for i in 1 2 3; do
+    sleep 1
+    kill -0 "$pid" 2>/dev/null || return 0
+  done
+  kill -KILL "$pid" 2>/dev/null || true
+  return 0
+}
+
+# Serialize concurrent passes (two QA lanes can dispatch at once). taskset is
+# idempotent, so a lock timeout is not a reason to skip the work.
+# NOTE the brace group: `exec 9>… 2>/dev/null` without it would apply the
+# stderr redirection to the REST OF THE SCRIPT, silently swallowing every
+# warning below. The group keeps 2>/dev/null scoped to the exec itself while
+# fd 9 still lands on the calling shell.
+mkdir -p "$PROFILE_ROOT" 2>/dev/null || true
+{ exec 9>"$PROFILE_ROOT/.iad-confine.lock"; } 2>/dev/null || true
+if command -v flock >/dev/null 2>&1; then flock -w 5 9 2>/dev/null || true; fi
+
+n_qa=0; n_confined=0; n_kept=0; n_killed=0; n_mcp=0; n_mcp_confined=0; n_swept=0; n_reaped=0
+
+# ── Pass A: QA browsers ──────────────────────────────────────────────────────
+# Only MAIN browser processes: renderers/GPU helpers carry --type= and are
+# handled by the tree walk (they are children of the main process).
+for pid in $(_scan "$PROFILE_ROOT/"); do
+  cmd="$(_cmdline "$pid")"
+  [[ "$cmd" == *" --type="* ]] && continue
+  n_qa=$(( n_qa + 1 ))
+  allowed="$(_allowed "$pid")"
+  if _owned "$cmd"; then
+    # Ours: must sit exactly inside this project's mask.
+    _is_subset "$allowed" "$MASK" && { n_kept=$(( n_kept + 1 )); continue; }
+  else
+    # Someone else's QA profile (e.g. the other project's, or a legacy
+    # auto-disambiguated one). Only act when it is effectively unconfined —
+    # narrowing a browser another project already confined would be rude and
+    # pointless; leaving an all-CPU browser running is what resets the host.
+    (( $(_width "$allowed") <= $(_width "$MASK") )) && { n_kept=$(( n_kept + 1 )); continue; }
+  fi
+  if _confine_tree "$pid"; then
+    n_confined=$(( n_confined + 1 ))
+    echo "[browser-confine] confined QA chrome pid $pid to $MASK."
+    continue
+  fi
+  if _owned "$cmd"; then
+    echo "[browser-confine] pid $pid could not be confined — terminating (own profile)." >&2
+    if _terminate "$pid"; then
+      n_killed=$(( n_killed + 1 ))
+      for d in "${OWN_DIRS[@]}"; do
+        [[ "$cmd" == *"--user-data-dir=$d"* ]] && _sweep_profile_files "$d"
+      done
+    fi
+  else
+    echo "[browser-confine] WARNING: chrome pid $pid ($allowed) is outside $MASK and is not ours to kill — close it manually." >&2
+  fi
+done
+
+# ── Pass B: MCP servers (confine, never kill) ────────────────────────────────
+# HOST_GUARD_MCP_MATCH holds the cmdline tokens that identify a Chrome-MCP
+# server (ALL must match). It exists so tests can scope this pass to their own
+# fake server — pass B is deliberately profile-root-independent, so without the
+# seam a sandboxed run would reach the operator's real, live MCP server.
+read -r -a _mcp_match <<< "${HOST_GUARD_MCP_MATCH:-superpowers-chrome mcp/dist/index.js}"
+for pid in $(_scan "${_mcp_match[@]}"); do
+  n_mcp=$(( n_mcp + 1 ))
+  _is_subset "$(_allowed "$pid")" "$MASK" && continue
+  if _confine_tree "$pid"; then
+    n_mcp_confined=$(( n_mcp_confined + 1 ))
+    echo "[browser-confine] confined Chrome-MCP server pid $pid to $MASK (its future browsers inherit it)."
+  else
+    echo "[browser-confine] WARNING: Chrome-MCP server pid $pid stays outside $MASK — browsers it spawns will be unconfined." >&2
+  fi
+done
+
+# ── Pass C: stale meta/lock sweep ────────────────────────────────────────────
+# The age guard keeps a racing MCP server's freshly-written file: it records the
+# pid before the browser is up, so a <30s file with a dead pid may be mid-launch.
+for f in "$PROFILE_ROOT"/*.meta.json "$PROFILE_ROOT"/*.mcp.lock; do
+  [[ -e "$f" ]] || continue
+  age=$(( EPOCHSECONDS - $(stat -c %Y "$f" 2>/dev/null || echo "$EPOCHSECONDS") ))
+  (( age > 30 )) || continue
+  fpid="$(sed -n 's/.*"pid"[: ]*\([0-9][0-9]*\).*/\1/p' "$f" 2>/dev/null | head -n 1)"
+  [[ -n "$fpid" ]] || continue
+  [[ -d "/proc/$fpid" ]] && continue
+  rm -f "$f" 2>/dev/null && n_swept=$(( n_swept + 1 ))
+done
+
+# ── Pass D: reap (opt-in, engine backend only) ───────────────────────────────
+if (( REAP )) && [[ "${CHAIN_BQA_REAP:-0}" == "1" && "${CHAIN_AGENT_BACKEND:-}" != "interactive" ]]; then
+  for pid in $(_scan "$PROFILE_ROOT/"); do
+    cmd="$(_cmdline "$pid")"
+    [[ "$cmd" == *" --type="* ]] && continue
+    _owned "$cmd" || continue
+    _terminate "$pid" && n_reaped=$(( n_reaped + 1 ))
+  done
+  for d in "${OWN_DIRS[@]}"; do _sweep_profile_files "$d"; done
+fi
+
+echo "[browser-confine] qa_browsers=$n_qa confined=$n_confined kept=$n_kept killed=$n_killed mcp=$n_mcp mcp_confined=$n_mcp_confined swept=$n_swept reaped=$n_reaped"
+exit 0
diff --git a/incredible_auto_dev/scripts/automation/lib/common.sh b/incredible_auto_dev/scripts/automation/lib/common.sh
index 6ba145e7..64702753 100644
--- a/incredible_auto_dev/scripts/automation/lib/common.sh
+++ b/incredible_auto_dev/scripts/automation/lib/common.sh
@@ -359,6 +359,41 @@ ensure_phase_ports() {
   fi
 }
 
+# Pin the QA browser's identity for this project (and lane). The Chrome MCP
+# server reads CHROME_WS_PROFILE/CHROME_WS_PORT from its environment; without
+# them it invents profile names (superpowers-chrome, -2, -3 …) as locks contend,
+# which is why several independent headed Chromes have run at once on this host.
+# A pinned identity makes the QA browser findable — by host-guard's confinement
+# pass, by the doctor, and by the reaper. Lane suffix keeps the concurrent qa and
+# browser-qa lanes off each other's profile lock.
+# Idempotent; never overrides an operator-supplied value.
+ensure_qa_browser_env() {
+  local suffix="${1:-}" project_root="$REPO_ROOT" base offset
+  [[ "$project_root" == */incredible_auto_dev ]] && project_root="${project_root%/incredible_auto_dev}"
+  base="$(basename "$project_root")"
+  offset=$(_project_port_offset)
+  [[ -z "${CHROME_WS_PROFILE:-}" ]] && export CHROME_WS_PROFILE="iad-qa-${base}${suffix:+-$suffix}"
+  if [[ -z "${CHROME_WS_PORT:-}" ]]; then
+    if [[ -n "$suffix" ]]; then
+      export CHROME_WS_PORT=$((11000 + offset))
+    else
+      export CHROME_WS_PORT=$((10000 + offset))
+    fi
+  fi
+  return 0
+}
+
+# Engine-mode QA runs the browser headless. The Chrome MCP picks headless purely
+# from the absence of DISPLAY/WAYLAND_DISPLAY, and a headed Chrome pays for GPU
+# compositing plus a full raster thread pool — the bursty all-core profile that
+# hard-resets this class of host. Screenshots are unaffected.
+# CHAIN_BQA_HEADED=1 restores a visible browser for debugging.
+strip_display_for_headless_qa() {
+  [[ "${CHAIN_BQA_HEADED:-0}" == "1" ]] && return 0
+  unset DISPLAY WAYLAND_DISPLAY
+  return 0
+}
+
 # ── Reviewer diff hygiene ─────────────────────────────────────────────────────
 # Pathspec excludes for the diffs REVIEWERS read: machine-generated lockfiles,
 # minified bundles, sourcemaps, binary/image assets, and harness artifact dirs
@@ -515,6 +550,51 @@ project_template_slice() {
   return 0
 }
 
+# ── Executor goal slice (TOKEN-10) ───────────────────────────────────────────
+# goal_slice_for_exec <iter-name> <targets-csv> <out-path>
+# Builds the token-lean goal view for EXECUTING agents (developer,
+# browser-qa) with the same builder the planning prompts already use
+# (goal_gate.py goal-slice): vision + anti-goals + the named target journeys +
+# every failing journey VERBATIM; stable passing journeys digested to one
+# line. Sets two globals (bare call — do NOT $(...)-capture, the mode would
+# die in the subshell):
+#   GOAL_SLICE_EXEC_PATH — the file the dispatch prompt should name
+#   GOAL_SLICE_EXEC_MODE — sliced | full-hatch | full-fallback
+#     sliced        — build succeeded; path = <out-path>
+#     full-hatch    — CHAIN_DEV_FULL_GOAL=true restores today's behavior
+#     full-fallback — builder failed/empty output: loud stderr WARNING +
+#                     goal_slice_fallback telemetry; path = docs/goal.md
+# Never blocks, never returns non-zero, and never leaves a stale out-path in
+# play: <out-path> is used only when THIS call wrote it non-empty (rc 0).
+goal_slice_for_exec() {
+  local _gs_iter="$1" _gs_targets="$2" _gs_out="$3"
+  local _gs_goal="$REPO_ROOT/docs/goal.md"
+  GOAL_SLICE_EXEC_PATH="$_gs_goal"
+  GOAL_SLICE_EXEC_MODE=""
+  if [[ "${CHAIN_DEV_FULL_GOAL:-false}" == "true" ]]; then
+    GOAL_SLICE_EXEC_MODE="full-hatch"
+    return 0
+  fi
+  local _gs_sid="${_gs_iter#goal-}"; _gs_sid="${_gs_sid%-iter-*}"
+  local _gs_hist="$REPO_ROOT/runs/goal-session-${_gs_sid}/state/journey-history.json"
+  local _gs_rc=0
+  rm -f "$_gs_out" 2>/dev/null || true
+  mkdir -p "$(dirname "$_gs_out")" 2>/dev/null || true
+  python3 "$REPO_ROOT/scripts/automation/lib/goal_gate.py" goal-slice "$_gs_goal" \
+    --history "$_gs_hist" --targets "$_gs_targets" --out "$_gs_out" 2>/dev/null || _gs_rc=$?
+  if [[ $_gs_rc -eq 0 && -s "$_gs_out" ]]; then
+    GOAL_SLICE_EXEC_MODE="sliced"
+    GOAL_SLICE_EXEC_PATH="$_gs_out"
+    return 0
+  fi
+  GOAL_SLICE_EXEC_MODE="full-fallback"
+  echo "[goal-slice] WARNING: executor goal-slice build failed (rc=$_gs_rc, out: $_gs_out) — dispatching with the FULL goal file instead ($_gs_goal). Journeys stay covered; only the token saving is lost this dispatch." >&2
+  if declare -F record_telemetry_event >/dev/null 2>&1; then
+    record_telemetry_event "goal_slice_fallback" "$(printf '{"iter_name":"%s","rc":%d}' "$_gs_iter" "$_gs_rc")" || true
+  fi
+  return 0
+}
+
 # Dispatch the coherence-auditor agent (goal mode). ONE shared implementation
 # for both call sites so the prompt cannot drift: the parallel fork inside
 # goal-iter-lean.sh (runs concurrently with browser-qa — the audit needs only
@@ -878,14 +958,23 @@ escalate_model_off() {
   return 0
 }
 
-# ── Wall-clock iteration budget (SPEED-15, warn-first) ────────────────────────
-# CHAIN_ITER_TIME_BUDGET_SECONDS (default 0 = off; suggested operator value
-# 5400) + CHAIN_ITER_BUDGET_MODE (warn|trim, default warn). Checks run at step
+# ── Wall-clock iteration budget (SPEED-15, armed by default) ──────────────────
+# CHAIN_ITER_TIME_BUDGET_SECONDS (default 3600; 0 = off) +
+# CHAIN_ITER_BUDGET_MODE (warn|trim, default trim). Checks run at step
 # boundaries ONLY — never mid-agent. warn: the first exceeded check logs loudly
-# and emits one iter_budget telemetry event per process. trim (opt-in): callers
-# may ALSO consult iter_budget_exceeded to skip showcase-class steps; the trim
-# ladder never touches developer/reviewer/evaluator/gates/confirm. The start
-# epoch crosses the engine→executor process boundary via CHAIN_ITER_START_EPOCH.
+# and emits one iter_budget telemetry event per process. trim (the default):
+# callers ALSO consult iter_budget_exceeded/iter_budget_trim_active to shed
+# optional breadth in rung order — rung 1 defers demo recording + README
+# refresh to the background tail, rung 2 narrows the browser regression sweep
+# to targets + replay-FAIL re-confirms (cut journeys get DEFERRED-BUDGET rows
+# that block GOAL_ACHIEVED), rung 3 skips full-pipeline test-plan generation
+# (when the spec carries TC- lines) and the ux-regression-reviewer. The trim
+# ladder NEVER touches developer/reviewer/decomposer/evaluator, the QA loop,
+# audit, closure, deterministic gates, or the two-key confirm. The start epoch
+# crosses the engine→executor process boundary via CHAIN_ITER_START_EPOCH.
+# A breach also forces the NEXT iteration lean via the budget-breached marker
+# (SPEED-20 rung 3). Rollback: CHAIN_ITER_TIME_BUDGET_SECONDS=0 disarms
+# everything; CHAIN_ITER_BUDGET_MODE=warn keeps warnings only.
 
 iter_budget_init() {  # $1 = iteration start epoch (falls back to the exported one, then now)
   _ITER_BUDGET_T0="${1:-${CHAIN_ITER_START_EPOCH:-$(date +%s)}}"
@@ -894,7 +983,7 @@ iter_budget_init() {  # $1 = iteration start epoch (falls back to the exported o
 }
 
 iter_budget_exceeded() {
-  local budget="${CHAIN_ITER_TIME_BUDGET_SECONDS:-0}"
+  local budget="${CHAIN_ITER_TIME_BUDGET_SECONDS:-3600}"
   [[ "$budget" =~ ^[0-9]+$ && "$budget" -gt 0 && -n "${_ITER_BUDGET_T0:-}" ]] || return 1
   (( $(date +%s) - _ITER_BUDGET_T0 > budget ))
 }
@@ -904,19 +993,27 @@ iter_budget_check() {  # $1 = step label. Always returns 0 (a signal, never a ga
   local elapsed=$(( $(date +%s) - ${_ITER_BUDGET_T0:-$(date +%s)} ))
   if [[ -z "${_ITER_BUDGET_WARNED:-}" ]]; then
     _ITER_BUDGET_WARNED=1
-    echo "[iter-budget] This iteration has run ${elapsed}s — over the ${CHAIN_ITER_TIME_BUDGET_SECONDS:-0}s budget (checked at: ${1:-?}; mode: ${CHAIN_ITER_BUDGET_MODE:-warn})." >&2
+    echo "[iter-budget] This iteration has run ${elapsed}s — over the ${CHAIN_ITER_TIME_BUDGET_SECONDS:-3600}s budget (checked at: ${1:-?}; mode: ${CHAIN_ITER_BUDGET_MODE:-trim})." >&2
     if declare -F record_telemetry_event >/dev/null 2>&1; then
       record_telemetry_event "iter_budget" "$(printf '{"budget":%d,"elapsed":%d,"mode":"%s","at_step":"%s"}' \
-        "${CHAIN_ITER_TIME_BUDGET_SECONDS:-0}" "$elapsed" "${CHAIN_ITER_BUDGET_MODE:-warn}" "${1:-?}")" || true
+        "${CHAIN_ITER_TIME_BUDGET_SECONDS:-3600}" "$elapsed" "${CHAIN_ITER_BUDGET_MODE:-trim}" "${1:-?}")" || true
     fi
   fi
   return 0
 }
 
-# trim-mode consult: true only when the operator opted into trim AND the budget
-# is exceeded. Callers use it to skip showcase-class steps with a loud log.
+# trim-mode consult: true only when trim mode is active (the default) AND the
+# budget is exceeded. Callers use it to shed optional breadth with a loud log.
 iter_budget_trim_active() {
-  [[ "${CHAIN_ITER_BUDGET_MODE:-warn}" == "trim" ]] && iter_budget_exceeded
+  [[ "${CHAIN_ITER_BUDGET_MODE:-trim}" == "trim" ]] && iter_budget_exceeded
+}
+
+# Rung telemetry: every trim rung that actually sheds work records which rung
+# fired so analyze_telemetry can show what a breached iteration gave up.
+iter_budget_trim_event() {  # $1 = rung label (e.g. showcase-defer, replay-narrow)
+  if declare -F record_telemetry_event >/dev/null 2>&1; then
+    record_telemetry_event "iter_budget_trim" "$(printf '{"rung":"%s"}' "${1:-?}")" || true
+  fi
 }
 
 # ── Hardening cadence (SPEED-4) ───────────────────────────────────────────────
@@ -960,6 +1057,117 @@ goal_cadence_forces_full() {
   (( k > 0 && current_iter > k && streak >= k ))
 }
 
+# ── Depth arbiter helpers (SPEED-20) ─────────────────────────────────────────
+# run-goal.sh's deterministic depth arbiter validates a spec-requested full
+# pass against independent machine signals instead of trusting the spec's own
+# 'Full trigger:' line (anti-pattern 25: an LLM asked to self-certify its own
+# exception will always find one). These two helpers supply the signals the
+# spec cannot forge: the recent-full window and the spec-content test.
+
+# goal_full_ran_in_window <session_dir> <current_iter>
+# True iff any of the last W-1 iterations (iter-(N-1) .. iter-(N-W+1); floor
+# iter-1 — the iter-0 baseline is never counted) dispatched full, i.e. granting
+# full NOW would exceed one full per W-iteration window. W =
+# CHAIN_FULL_CADENCE_CAP (default 4); 0 or 1 disables the cap (never true).
+# Reads the same idempotent depth-dispatched files as goal_lean_streak, so
+# resume re-entry cannot change the answer.
+goal_full_ran_in_window() {
+  local session_dir="$1" current_iter="$2"
+  local w="${CHAIN_FULL_CADENCE_CAP:-4}"
+  [[ "$w" =~ ^[0-9]+$ ]] || w=4
+  (( w >= 2 )) || return 1
+  local i lo=$(( current_iter - w + 1 ))
+  (( lo < 1 )) && lo=1
+  for (( i = current_iter - 1; i >= lo; i-- )); do
+    [[ "$(cat "$session_dir/iter-$i/depth-dispatched" 2>/dev/null || true)" == "full" ]] && return 0
+  done
+  return 1
+}
+
+# goal_new_fullstack_journey <spec_path> <journey_history>
+# True iff the spec plans a genuinely NEW full-stack journey: ≥1 concrete
+# Backend bullet AND ≥1 concrete Frontend bullet under IN SCOPE, a non-"none"
+# Data-contract additions section, and ≥1 Target journey that journey-history
+# has never recorded as meaningfully implemented (absent, or status outside
+# passing/already_passing/partial/regressed). Fail-closed: a missing/unreadable
+# file, no parseable targets, or any unmet condition returns 1 — the arbiter
+# then demotes to lean.
+goal_new_fullstack_journey() {
+  local spec="$1" history="$2"
+  python3 - "$spec" "$history" <<'PYEOF'
+import json, re, sys
+
+try:
+    spec = open(sys.argv[1], encoding="utf-8", errors="replace").read()
+    hist = json.load(open(sys.argv[2]))
+except Exception:
+    sys.exit(1)
+
+# All content checks are anchored INSIDE the "## IN SCOPE" block — a Backend
+# heading under OUT OF SCOPE or BACKGROUND must not count (fail-closed: no
+# IN SCOPE block at all -> not a new full-stack journey).
+m = re.search(r"^##\s+IN SCOPE\s*$(.*?)(?=^##\s|\Z)", spec, re.S | re.M | re.I)
+scope = m.group(1) if m else ""
+if not scope.strip():
+    sys.exit(1)
+
+
+def section(text, header_re, level):
+    """Body of the first header matching header_re, up to the next header of
+    the same or higher level."""
+    pat = re.compile(
+        r"^#{%d}\s+%s.*?$(.*?)(?=^#{1,%d}\s|\Z)" % (level, header_re, level),
+        re.S | re.M | re.I,
+    )
+    m = pat.search(text)
+    return m.group(1) if m else ""
+
+
+_NONE_RE = re.compile(r'^["\'`*]*(none|n/?a|nothing)\b', re.I)
+
+
+def has_bullet(body):
+    """A CONCRETE bullet: not a template placeholder, not a none/N.A. filler
+    (an LLM writing '- none' must not satisfy the backend/frontend test)."""
+    for line in body.splitlines():
+        bm = re.match(r"\s*-\s+(?:\[.\]\s+)?(\S.*)$", line)
+        if not bm:
+            continue
+        txt = bm.group(1).strip()
+        if txt.startswith("<") or _NONE_RE.match(txt):
+            continue
+        return True
+    return False
+
+
+if not has_bullet(section(scope, r"Backend", 3)):
+    sys.exit(1)
+if not has_bullet(section(scope, r"Frontend", 3)):
+    sys.exit(1)
+
+contract = section(scope, r"Data-contract additions", 3)
+lines = []
+for l in contract.splitlines():
+    l = re.sub(r"^\s*-\s+(\[.\]\s+)?", "", l.strip())  # strip bullet/checkbox markers
+    if l and not l.startswith("<!--") and not l.startswith("<"):
+        lines.append(l)
+if not lines or _NONE_RE.match(lines[0]):
+    sys.exit(1)
+
+m = re.search(r"Target journeys:\**\s*(.*)$", spec, re.M)
+ids = re.findall(r"J-\d+", m.group(1)) if m else []
+if not ids:
+    sys.exit(1)
+journeys = hist.get("journeys") or {}
+IMPLEMENTED = ("passing", "already_passing", "partial", "regressed")
+for jid in ids:
+    j = journeys.get(jid)
+    if not isinstance(j, dict) or j.get("status") not in IMPLEMENTED:
+        sys.exit(0)   # brand-new (or never-implemented) target found
+sys.exit(1)
+PYEOF
+}
+
 # ── Idempotent service bootstrap (shared by qa-phase.sh and browser-qa-phase.sh) ──
 #
 # Starts the backend (and optionally frontend) if they are not already running.
diff --git a/incredible_auto_dev/scripts/automation/lib/demo_runner.py b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
index ae6421a7..349cd0a9 100644
--- a/incredible_auto_dev/scripts/automation/lib/demo_runner.py
+++ b/incredible_auto_dev/scripts/automation/lib/demo_runner.py
@@ -461,6 +461,79 @@ def _t_launch_chromium_retries() -> None:
     assert _DeadChromium.calls == 2
 
 
+def _derive_demo_fixture() -> dict:
+    # Matches the demo-narrator contract: every step carries a "journey" key,
+    # "" on shared orientation steps (the untagged prefix).
+    return {
+        "schema_version": 1,
+        "phase_id": "goal-x-iter-9",
+        "name": "demo",
+        "default_timeout_ms": 9000,
+        "steps": [
+            {"n": 1, "journey": "", "action": {"type": "goto", "url": "/"}, "narration": "open the app",
+             "expect": {"text": "Home"}},
+            {"n": 2, "journey": "J-07", "action": {"type": "click", "target": {"text": "Filters"}},
+             "narration": "open filters"},
+            {"n": 3, "journey": "J-07", "action": {"type": "expect"}, "expect": {"text": "Filter panel"},
+             "timeout_ms": 4000},
+            {"n": 4, "journey": "J-09", "action": {"type": "click", "target": {"text": "Export"}},
+             "expect": {"text": "Exported"}},
+        ],
+    }
+
+
+def _t_derive_happy() -> None:
+    golden, reason = derive_golden_steps(_derive_demo_fixture(), "J-07")
+    assert golden is not None, reason
+    assert validate_script(golden) == [], golden
+    # prefix (untagged step 1) + the 2 tagged steps, renumbered 1..3
+    assert [s["n"] for s in golden["steps"]] == [1, 2, 3], golden["steps"]
+    assert all(s["journey"] == "J-07" for s in golden["steps"])
+    assert golden["steps"][0]["action"]["type"] == "goto"
+    # demo-only fields are stripped
+    assert all("narration" not in s for s in golden["steps"])
+    assert golden["steps"][2]["timeout_ms"] == 4000
+    assert golden["journey"] == "J-07" and golden["default_timeout_ms"] == 9000
+
+
+def _t_derive_rejects_untagged_journey() -> None:
+    golden, reason = derive_golden_steps(_derive_demo_fixture(), "J-99")
+    assert golden is None and "no steps tagged" in reason, (golden, reason)
+
+
+def _t_derive_rejects_no_expect() -> None:
+    demo = _derive_demo_fixture()
+    for s in demo["steps"]:
+        if s.get("journey") == "J-07":
+            s.pop("expect", None)
+    golden, reason = derive_golden_steps(demo, "J-07")
+    assert golden is None and "expect" in reason, (golden, reason)
+
+
+def _t_derive_rejects_no_goto_open() -> None:
+    demo = _derive_demo_fixture()
+    demo["steps"] = demo["steps"][1:]   # drop the untagged goto prefix
+    golden, reason = derive_golden_steps(demo, "J-07")
+    assert golden is None and "goto" in reason, (golden, reason)
+
+
+def _t_derive_rejects_invalid_demo() -> None:
+    golden, reason = derive_golden_steps({"schema_version": 1, "steps": []}, "J-07")
+    assert golden is None and "invalid" in reason, (golden, reason)
+    golden, reason = derive_golden_steps({"schema_version": 1, "not_yet": True}, "J-07")
+    assert golden is None, (golden, reason)
+
+
+def _t_derive_prefix_without_journey_key() -> None:
+    # Legacy/hand-written demos may omit the journey key entirely on setup
+    # steps — the prefix scan must treat that the same as journey:"".
+    demo = _derive_demo_fixture()
+    del demo["steps"][0]["journey"]
+    golden, reason = derive_golden_steps(demo, "J-07")
+    assert golden is not None, reason
+    assert golden["steps"][0]["action"]["type"] == "goto"
+
+
 _SELF_TEST_CHECKS = [
     _t_normalize_url_relative,
     _t_normalize_url_rewrites_localhost,
@@ -478,6 +551,12 @@ _SELF_TEST_CHECKS = [
     _t_regression_verdict_matrix,
     _t_regression_results_md,
     _t_launch_chromium_retries,
+    _t_derive_happy,
+    _t_derive_rejects_untagged_journey,
+    _t_derive_rejects_no_expect,
+    _t_derive_rejects_no_goto_open,
+    _t_derive_rejects_invalid_demo,
+    _t_derive_prefix_without_journey_key,
 ]
 
 
@@ -770,6 +849,93 @@ def run_lint(opts) -> int:
     return 0
 
 
+def derive_golden_steps(demo: object, journey: str) -> "tuple[dict | None, str]":
+    """SPEED-21: derive a candidate golden replay script for `journey` from an
+    already-recorded demo script (same runner schema — verify ignores the
+    demo-only fields). Copy + filter + renumber: the untagged PREFIX steps
+    (shared setup before the first journey-tagged step) plus every step tagged
+    with this journey; each kept step keeps only n/journey/action/expect/
+    timeout_ms. Fail-closed — returns (None, reason) unless the demo
+    validates, >=1 step is tagged for the journey, the derived sequence opens
+    with a goto, and >=1 TAGGED step carries an expect (a golden with no
+    assertions would pass vacuously). A returned script always passes
+    validate_script."""
+    errors = validate_script(demo)
+    if errors:
+        return None, "demo script invalid: " + "; ".join(errors)[:160]
+    assert isinstance(demo, dict)  # validate_script guarantees this
+    if demo.get("not_yet"):
+        return None, "demo marked not_yet (no executable steps)"
+    steps = demo.get("steps") or []
+    # The demo-narrator contract has EVERY step carry a "journey" key, with ""
+    # for shared orientation/setup steps — so "untagged" means a FALSY journey
+    # value (missing, "", null), not a missing key.
+    prefix: list = []
+    for s in steps:
+        if isinstance(s, dict) and not s.get("journey"):
+            prefix.append(s)
+        else:
+            break
+    tagged = [s for s in steps if isinstance(s, dict) and s.get("journey") == journey]
+    if not tagged:
+        return None, "no steps tagged for this journey"
+    if not any(isinstance(s.get("expect"), dict) for s in tagged):
+        return None, "no tagged step carries an expect (nothing to assert)"
+    out_steps: list = []
+    for i, s in enumerate(prefix + tagged, 1):
+        ns: dict = {"n": i, "journey": journey, "action": s.get("action")}
+        if isinstance(s.get("expect"), dict):
+            ns["expect"] = s["expect"]
+        if s.get("timeout_ms") is not None:
+            ns["timeout_ms"] = s["timeout_ms"]
+        out_steps.append(ns)
+    first_action = out_steps[0].get("action") or {}
+    if not isinstance(first_action, dict) or first_action.get("type") != "goto":
+        return None, "derived sequence does not open with a goto"
+    golden = {
+        "schema_version": 1,
+        "journey": journey,
+        "name": str(demo.get("name") or journey),
+        "default_timeout_ms": demo.get("default_timeout_ms", 8000),
+        "steps": out_steps,
+    }
+    errors = validate_script(golden)
+    if errors:
+        return None, "derived script failed validation: " + "; ".join(errors)[:160]
+    return golden, ""
+
+
+def run_derive(opts) -> int:
+    """SPEED-21 CLI: write candidate goldens (`<J-XX>.json.candidate` in
+    --scripts-dir) derived from the --json demo for each --journeys id.
+    Prints one parseable line per journey: `<J-XX> derived <path>` or
+    `<J-XX> rejected: <reason>`. ALWAYS exits 0 — a rejected candidate is
+    never a gate; the shell caller (replay_lane_autoderive_goldens) runs a
+    REAL verify pass on every candidate before installing it."""
+    journeys = [j.strip() for j in (opts.journeys or "").split(",") if j.strip()]
+    if not opts.json or not opts.scripts_dir or not journeys:
+        sys.stderr.write("[demo_runner] derive mode needs --json, --scripts-dir and --journeys; nothing derived.\n")
+        return 0
+    try:
+        with open(opts.json, encoding="utf-8") as fh:
+            demo = json.load(fh)
+    except Exception as exc:  # noqa: BLE001
+        for jid in journeys:
+            print(f"{jid} rejected: demo JSON unreadable: {str(exc)[:100]}")
+        return 0
+    outdir = Path(opts.scripts_dir)
+    outdir.mkdir(parents=True, exist_ok=True)
+    for jid in journeys:
+        golden, reason = derive_golden_steps(demo, jid)
+        if golden is None:
+            print(f"{jid} rejected: {reason}")
+            continue
+        cand = outdir / f"{jid}.json.candidate"
+        cand.write_text(json.dumps(golden, indent=1) + "\n", encoding="utf-8")
+        print(f"{jid} derived {cand}")
+    return 0
+
+
 def _launch_chromium(pw, headless: bool, attempts: int = 2, timeout_ms: int = 45000,
                      args: list | None = None):
     """Launch chromium with a bounded timeout and one fast retry.
@@ -1073,7 +1239,7 @@ def main(argv: list[str]) -> int:
     import argparse
     p = argparse.ArgumentParser(prog="demo_runner.py", description="Deterministic browser demo executor.")
     p.add_argument("--json", default=None, help="path to the executable demo-script JSON (record/live)")
-    p.add_argument("--mode", default="record", choices=["live", "record", "session-live", "verify", "lint"])
+    p.add_argument("--mode", default="record", choices=["live", "record", "session-live", "verify", "lint", "derive"])
     p.add_argument("--base-url", default="http://localhost:3000")
     p.add_argument("--out-dir", default=None, help="screenshot dir, e.g. reports/demo/<id>")
     p.add_argument("--results", default=None, help="demo-results.md output path")
@@ -1097,6 +1263,9 @@ def main(argv: list[str]) -> int:
     if opts.mode == "lint":
         return run_lint(opts)   # pure validation — needs no browser/playwright
 
+    if opts.mode == "derive":
+        return run_derive(opts)  # pure transform (SPEED-21) — no browser/playwright
+
     if not _playwright_available():
         sys.stderr.write(_PLAYWRIGHT_HELP + "\n")
         if not live and not verify:
diff --git a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
index 3e5b1340..846fe62c 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
+++ b/incredible_auto_dev/scripts/automation/lib/goal-gates.sh
@@ -228,6 +228,17 @@ goal_gate_confirm_achieved() {
   digest="$(python3 "$_GOAL_GATES_DIR/goal_gate.py" digest "$history" 2>/dev/null || echo '(digest unavailable)')"
 
   local _rc=0
+  # REP-5: attribute this dispatch in the per-agent telemetry economics — its
+  # ~5 min per achieving iteration was previously an unattributed wall-clock
+  # gap. Guarded (declare -F): --self-test and standalone sourcing run without
+  # telemetry.sh. The telemetry label is goal-evaluator-confirm; the dispatch
+  # env below keeps CHAIN_CURRENT_AGENT=goal-evaluator because pump permission
+  # resolution knows the evaluator's tool grants, not the telemetry label.
+  local _confirm_start=""
+  if declare -F record_agent_invocation_start >/dev/null 2>&1; then
+    record_agent_invocation_start "goal-evaluator-confirm"   # bare call: $(...) would lose CHAIN_AGENT_START_EPOCH to a subshell
+    _confirm_start="${CHAIN_AGENT_START_EPOCH:-}"
+  fi
   # The dispatch's own stdout must NOT leak into the caller's command
   # substitution — route it to a log file.
   CHAIN_MODEL_OVERRIDE="${strong_model}" \
@@ -265,6 +276,10 @@ followed by a '## Reasoning' section (max ~15 lines; cite what you checked).
 STOP after writing the file." \
     >> "$iter_dir/confirm-dispatch.log" 2>&1 || _rc=$?
 
+  if declare -F record_agent_invocation_end >/dev/null 2>&1; then
+    record_agent_invocation_end "goal-evaluator-confirm" "$_confirm_start" "$_rc"
+  fi
+
   if [[ $_rc -ne 0 ]]; then
     echo "[goal-gates] confirm dispatch failed (rc=$_rc) — fail-closed (demote)." >&2
     return 1
@@ -390,12 +405,24 @@ _goal_gates_self_test() {
     return 0
   }
 
+  # REP-5: the confirm dispatch must fire the guarded attribution hooks. The
+  # stubs log to a file because the seam runs inside $(...) subshells.
+  local REP5_LOG="$d/rep5.log"
+  record_agent_invocation_start() { echo "start $1" >> "$REP5_LOG"; CHAIN_AGENT_START_EPOCH=12345; }
+  record_agent_invocation_end()   { echo "end $1 t0=$2 rc=$3" >> "$REP5_LOG"; }
+
   local v
 
   # 1. All green + confirm yes → GOAL_ACHIEVED survives.
   STUB_CONFIRM=yes
   v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_PASS" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
   [[ "$v" == "GOAL_ACHIEVED" ]] && echo "  PASS goal-gates: clean GOAL_ACHIEVED survives" || { echo "  FAIL goal-gates: clean survive (got '$v')"; fails=1; }
+  if grep -q '^start goal-evaluator-confirm$' "$REP5_LOG" 2>/dev/null \
+     && grep -q '^end goal-evaluator-confirm t0=12345 rc=0$' "$REP5_LOG" 2>/dev/null; then
+    echo "  PASS goal-gates: confirm dispatch attributed (REP-5 start+end events)"
+  else
+    echo "  FAIL goal-gates: confirm dispatch attribution (REP-5) — got: $(cat "$REP5_LOG" 2>/dev/null | tr '\n' ';')"; fails=1
+  fi
 
   # 2. A failing journey demotes despite the evaluator's verdict.
   v="$(goal_gate_filter_verdict GOAL_ACHIEVED "$d/iter-3" "$EVALF" "$HIST_FAIL" "$COH" true "$RES" "$d/session" "$d/goal.md" 2>/dev/null)"
@@ -530,7 +557,7 @@ _goal_gates_self_test() {
     && echo "  PASS goal-gates: goal-gates.sh source is free of secret-shaped literals" \
     || { echo "  FAIL goal-gates: goal-gates.sh contains a scanner-tripping literal"; fails=1; }
 
-  unset -f claude_with_quota_retry
+  unset -f claude_with_quota_retry record_agent_invocation_start record_agent_invocation_end
   rm -rf "$d"
   if [[ $fails -eq 0 ]]; then echo "goal-gates self-test: OK"; else echo "goal-gates self-test: FAILED"; fi
   return $fails
diff --git a/incredible_auto_dev/scripts/automation/lib/goal_gate.py b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
index 729c53a4..292dca08 100644
--- a/incredible_auto_dev/scripts/automation/lib/goal_gate.py
+++ b/incredible_auto_dev/scripts/automation/lib/goal_gate.py
@@ -73,6 +73,10 @@ _VERDICT_RE = re.compile(r"^\*\*Verdict:\*\*\s*(\S+)", re.MULTILINE)
 # A table cell whose entire content is FAIL (avoids matching prose that
 # merely contains the word).
 _FAIL_CELL_RE = re.compile(r"\|\s*FAIL\s*\|")
+# SPEED-15 rung 2: a journey deferred for wall-clock budget was NOT verified
+# this iteration — it keeps its prior status for scoring, but it must block
+# GOAL_ACHIEVED exactly like a FAIL until a later iteration re-verifies it.
+_DEFERRED_CELL_RE = re.compile(r"\|\s*DEFERRED-BUDGET\s*\|")
 
 
 def _load_history(path: str) -> dict | None:
@@ -133,7 +137,7 @@ def cmd_results(path: str) -> int:
         text = Path(path).read_text(encoding="utf-8")
     except OSError:
         return 2
-    return 1 if _FAIL_CELL_RE.search(text) else 0
+    return 1 if (_FAIL_CELL_RE.search(text) or _DEFERRED_CELL_RE.search(text)) else 0
 
 
 def cmd_regressions(pre_path: str, post_path: str) -> int:
@@ -441,6 +445,14 @@ def _self_test() -> int:
         assert cmd_results(str(res_ok)) == 0
         assert cmd_results(str(res_bad)) == 1
         assert cmd_results(str(res_prose)) == 0, "FAIL must match a whole cell only"
+        # SPEED-15 rung 2: a DEFERRED-BUDGET row blocks achievement like a FAIL
+        # (the journey was not verified this iteration), even with every other
+        # row PASS.
+        res_def = d / "r4.md"; res_def.write_text(
+            "| T1 | n | ui | P1 | e | a | PASS | x.png |\n"
+            "| UT-J-06 | J-06 regression re-check | regression | P2 | e | not run | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |\n",
+            encoding="utf-8")
+        assert cmd_results(str(res_def)) == 1, "DEFERRED-BUDGET must block GOAL_ACHIEVED"
 
         # regressions: J-01 passing→failing is caught; missing pre → 0
         post = d / "post.json"
diff --git a/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh b/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
new file mode 100644
index 00000000..ba083006
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
@@ -0,0 +1,342 @@
+#!/usr/bin/env bash
+# lib/host-guard-registry.sh — machine-global aggregate bound for host-guard.
+#
+# WHY: host-guard's per-session caps (CPU affinity mask, MemoryHigh) are each
+# verified IN ISOLATION. Two projects can therefore both pass while the MACHINE
+# is over budget — the 2026-07-29 14:02:45 hard reset happened with two goal
+# modes holding COMPLEMENTARY masks ("0-3,8-11" + "4-7,12-15"): every per-session
+# check green, union = all 16 CPUs = every physical core lit by one burst. Memory
+# had the same shape (14G + 14G against 27.3G of RAM). A per-scope ceiling on
+# shared hardware is not evidence the hardware is safe.
+#
+# This library adds the missing machine view:
+#   - a HOST budget file (one per machine, outside every repo) declaring the
+#     aggregate CPU list and memory budget every guarded session must fit inside;
+#   - a REGISTRY of live guarded contexts (engines, adopted pumps, wrapped
+#     pumps) so any session can see what else is running right now;
+#   - a BOOST check, because a guard that silently loses its own hardware
+#     assumption (the Jul-28 boost-off mitigation did not survive a reboot —
+#     the tmpfiles.d rule was never installed) is not a guard.
+#
+# NEUTRALITY: no host budget file ⇒ enforcement off. The registry is still
+# maintained (it is cheap and makes `doctor.sh` honest), and the aggregate
+# verdict degrades to a loud WARN when 2+ projects are live without a budget.
+#
+# CONCURRENCY: no locks. Every writer owns a unique filename
+# (<kind>-<pid>-<starttime>.rec) and writes it with tmp+rename, so readers can
+# never see a torn record. The classic two-racers TOCTOU is solved by ORDERING —
+# register FIRST, verify SECOND: both racers see each other, and both compute the
+# same loser from a total order (epoch, starttime, pid). Exactly one pauses.
+#
+# STALENESS: pid-based, never time-based. Iteration gaps here are legitimately
+# unbounded (thermal cooldowns up to 30 min, interactive dispatches up to 2 h),
+# so any mtime TTL would evict live sessions. A record is stale iff the boot_id
+# differs (the machine rebooted), the pid is gone, or the pid is alive with a
+# different start time (recycled). Heartbeat mtime is advisory reporting only.
+#
+# ASSUMPTION: the registry lives on a local filesystem (rename atomicity and
+# `kill -0` validity are both meaningless over NFS).
+
+# Re-source guard: run-goal.sh sources this once, but host-guard-adopt.sh and
+# host-guard-exec.sh may source it inside an already-sourced shell.
+if [[ -n "${_HOST_GUARD_REGISTRY_LOADED:-}" ]]; then return 0 2>/dev/null || true; fi
+_HOST_GUARD_REGISTRY_LOADED=1
+
+# ── Mask set math ─────────────────────────────────────────────────────────────
+# _host_guard_mask_width (run-goal.sh) counts CPUs; that is not enough here.
+# "0-7" and "0-3,8-11" both have width 8 but are DISJOINT sets — the exact
+# distinction a machine-global bound turns on. These work on sets.
+
+_hg_mask_expand() { # "0-3,8-11" → one CPU id per line, sorted, deduped
+  local list="${1:-}" part a b i
+  [[ -n "$list" ]] || return 0
+  local -a parts=()
+  IFS=',' read -ra parts <<< "$list"
+  {
+    for part in "${parts[@]}"; do
+      if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+        a="${part%-*}"; b="${part#*-}"
+        if (( b >= a )); then for (( i=a; i<=b; i++ )); do echo "$i"; done; fi
+      elif [[ "$part" =~ ^[0-9]+$ ]]; then
+        echo "$part"
+      fi
+    done
+  } | sort -n -u
+}
+
+_hg_mask_is_subset() { # $1 ⊆ $2 ? (empty subset is trivially true)
+  local c
+  local -A super=()
+  while read -r c; do [[ -n "$c" ]] && super["$c"]=1; done < <(_hg_mask_expand "${2:-}")
+  while read -r c; do
+    [[ -n "$c" ]] || continue
+    [[ -n "${super[$c]:-}" ]] || return 1
+  done < <(_hg_mask_expand "${1:-}")
+  return 0
+}
+
+_hg_mask_union() { # any number of mask strings → "0,1,2,8,9" (canonical, sorted)
+  local l
+  { for l in "$@"; do _hg_mask_expand "$l"; done; } | sort -n -u | paste -sd, -
+}
+
+_hg_mem_to_bytes() { # "14G" | "512M" | "2048K" | "123" → bytes; rc 1 on junk
+  local v="${1:-}" n u
+  [[ "$v" =~ ^([0-9]+)([KMGTkmgt]?)$ ]] || { echo ""; return 1; }
+  n="${BASH_REMATCH[1]}"; u="${BASH_REMATCH[2]}"
+  case "$u" in
+    K|k) echo $(( n * 1024 )) ;;
+    M|m) echo $(( n * 1024 * 1024 )) ;;
+    G|g) echo $(( n * 1024 * 1024 * 1024 )) ;;
+    T|t) echo $(( n * 1024 * 1024 * 1024 * 1024 )) ;;
+    *)   echo "$n" ;;
+  esac
+  return 0
+}
+
+_hg_bytes_to_h() { # bytes → "13.7G" for human-readable messages
+  local b="${1:-0}"
+  awk -v b="$b" 'BEGIN{ if (b >= 1073741824) printf "%.1fG", b/1073741824;
+                        else if (b >= 1048576) printf "%.1fM", b/1048576;
+                        else printf "%dB", b }'
+}
+
+# ── Process identity ──────────────────────────────────────────────────────────
+
+_hg_boot_id() { cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo "unknown"; }
+
+# /proc/<pid>/stat field 22 (starttime). The comm field can contain spaces and
+# parentheses, so strip through the LAST ')' before counting — same idiom the
+# dispatch waiter and test-pump-liveness.sh use for pid-recycling defense.
+_hg_proc_starttime() {
+  local pid="${1:-}"
+  [[ -n "$pid" ]] || return 0
+  sed 's/.*) //' "/proc/$pid/stat" 2>/dev/null | awk '{print $20}'
+}
+
+# ── Registry ──────────────────────────────────────────────────────────────────
+
+hg_registry_dir() {
+  echo "${HOST_GUARD_REGISTRY_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/registry}"
+}
+
+hg_host_env_file() {
+  echo "${HOST_GUARD_HOST_ENV_FILE:-$HOME/.config/iad/host-guard-host.env}"
+}
+
+# hg_load_host_env — source the machine budget if present. Deliberately unscoped
+# (matches how run-goal.sh sources the project host-guard.env), so the
+# HOST_GUARD_GLOBAL_* values stay visible to the caller.
+hg_load_host_env() {
+  local f; f="$(hg_host_env_file)"
+  [[ -f "$f" ]] || return 0
+  # shellcheck disable=SC1090
+  source "$f"
+  return 0
+}
+
+_hg_rec_field() { sed -n "s/^$2=//p" "$1" 2>/dev/null | head -n 1; }
+
+# hg_register <kind> <pid> <project_root> <session_id> <cpu_list> <memory_high>
+# Echoes the record path (empty on failure). ALWAYS returns 0 — a registry
+# problem must never take down an engine that is otherwise correctly confined.
+# Idempotent: re-registering the same (kind,pid,starttime) is the heartbeat.
+hg_register() {
+  local kind="${1:-}" pid="${2:-}" root="${3:-}" sid="${4:-}" cpus="${5:-}" mem="${6:-}"
+  local dir stt rec tmp
+  dir="$(hg_registry_dir)"
+  mkdir -p "$dir" 2>/dev/null || { echo ""; return 0; }
+  stt="$(_hg_proc_starttime "$pid")"
+  [[ -n "$stt" ]] || { echo ""; return 0; }
+  rec="$dir/$kind-$pid-$stt.rec"
+  if [[ -f "$rec" ]]; then
+    touch "$rec" 2>/dev/null || true
+    echo "$rec"; return 0
+  fi
+  tmp="$rec.tmp.$$"
+  if printf 'kind=%s\npid=%s\nstarttime=%s\nboot_id=%s\nhost=%s\nepoch=%s\nproject_root=%s\nsession_id=%s\ncpu_list=%s\nmemory_high=%s\n' \
+       "$kind" "$pid" "$stt" "$(_hg_boot_id)" "$(hostname 2>/dev/null || echo unknown)" \
+       "$(date +%s)" "$root" "$sid" "$cpus" "$mem" > "$tmp" 2>/dev/null \
+     && mv -f "$tmp" "$rec" 2>/dev/null; then
+    echo "$rec"; return 0
+  fi
+  rm -f "$tmp" 2>/dev/null || true
+  echo ""; return 0
+}
+
+hg_record_is_live() { # $1 record path → rc 0 live, rc 1 stale
+  local rec="${1:-}" pid stt bid
+  [[ -f "$rec" ]] || return 1
+  bid="$(_hg_rec_field "$rec" boot_id)"
+  [[ "$bid" == "$(_hg_boot_id)" ]] || return 1          # machine rebooted
+  pid="$(_hg_rec_field "$rec" pid)"
+  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
+  kill -0 "$pid" 2>/dev/null || return 1                # holder gone
+  stt="$(_hg_rec_field "$rec" starttime)"
+  [[ "$(_hg_proc_starttime "$pid")" == "$stt" ]] || return 1   # pid recycled
+  return 0
+}
+
+hg_sweep() { # drop stale records; racing sweepers are harmless (rm -f)
+  local r
+  for r in "$(hg_registry_dir)"/*.rec; do
+    [[ -e "$r" ]] || continue
+    hg_record_is_live "$r" || rm -f "$r" 2>/dev/null || true
+  done
+  return 0
+}
+
+hg_live_records() { # print paths of live records, one per line
+  local r
+  for r in "$(hg_registry_dir)"/*.rec; do
+    [[ -e "$r" ]] || continue
+    hg_record_is_live "$r" && echo "$r"
+  done
+  return 0
+}
+
+hg_release() { # drop THIS process's engine record (best effort)
+  local stt; stt="$(_hg_proc_starttime "$$")"
+  [[ -n "$stt" ]] || return 0
+  rm -f "$(hg_registry_dir)/engine-$$-$stt.rec" 2>/dev/null || true
+  return 0
+}
+
+# hg_self_is_junior_to <own_rec> <other_rec> — rc 0 when SELF loses.
+# Total order over (epoch, starttime, pid): both sides compute the same answer
+# from the same files, so a conflict never ends in both-pause or neither-pause.
+hg_self_is_junior_to() {
+  local a b
+  a="$(_hg_rec_field "$1" epoch)"; b="$(_hg_rec_field "$2" epoch)"
+  [[ "$a" =~ ^[0-9]+$ ]] || a=0; [[ "$b" =~ ^[0-9]+$ ]] || b=0
+  (( a > b )) && return 0
+  (( a < b )) && return 1
+  a="$(_hg_rec_field "$1" starttime)"; b="$(_hg_rec_field "$2" starttime)"
+  [[ "$a" =~ ^[0-9]+$ ]] || a=0; [[ "$b" =~ ^[0-9]+$ ]] || b=0
+  (( a > b )) && return 0
+  (( a < b )) && return 1
+  a="$(_hg_rec_field "$1" pid)"; b="$(_hg_rec_field "$2" pid)"
+  [[ "$a" =~ ^[0-9]+$ ]] || a=0; [[ "$b" =~ ^[0-9]+$ ]] || b=0
+  (( a > b ))
+}
+
+# ── Host-level assumption checks ──────────────────────────────────────────────
+
+# hg_boost_ok — CPU boost must be OFF when the host budget says so. Read-only:
+# the engine never sudo's. Prints the failure reason on stdout.
+hg_boost_ok() {
+  [[ "${HOST_GUARD_REQUIRE_BOOST_OFF:-0}" == "1" ]] || return 0
+  local p v
+  p="${HOST_GUARD_SYS_BOOST_PATH:-/sys/devices/system/cpu/cpufreq/boost}"
+  if [[ ! -r "$p" ]]; then
+    echo "CPU boost knob $p is missing or unreadable — the boost-off assumption cannot be verified (kernel or cpufreq driver changed?). Set HOST_GUARD_REQUIRE_BOOST_OFF=0 in $(hg_host_env_file) if this host has no boost control."
+    return 1
+  fi
+  v="$(tr -dc '0-9' < "$p" 2>/dev/null)"
+  if [[ "$v" != "0" ]]; then
+    echo "CPU boost is ON ($p reads '${v:-?}', expected 0) — the hardware mitigation is inactive. Re-apply and persist it: echo 0 | sudo tee $p && printf 'w $p - - - - 0\\n' | sudo tee /etc/tmpfiles.d/cpufreq-boost.conf (see docs/host-guard.md § Boost persistence)."
+    return 1
+  fi
+  return 0
+}
+
+# ── Aggregate verdict ─────────────────────────────────────────────────────────
+# hg_aggregate_verdict <own_rec> → "OK" | "WARN|<msg>" | "PAUSE|<msg>"
+#
+# Memory is summed as per-project MAX, not a plain total: a project's engine
+# scope and its adopted-pump scope are separate cgroups that each carry the same
+# MemoryHigh, so a naive sum double-counts every project and no sane budget
+# would ever pass. MemoryHigh is a reclaim/throttle high-water anyway, not a
+# reservation — max-per-project is the figure that matches the incident math.
+hg_aggregate_verdict() {
+  local own_rec="${1:-}"
+  local global_cpus="${HOST_GUARD_GLOBAL_CPU_LIST:-}"
+  local global_mem="${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-}"
+  local -a live=()
+  local r
+  while read -r r; do [[ -n "$r" ]] && live+=("$r"); done < <(hg_live_records)
+
+  # Distinct project roots among live registrants (for the no-budget warning).
+  local -A roots=() proj_mem=()
+  local -a masks=()
+  local root mem bytes
+  for r in "${live[@]}"; do
+    root="$(_hg_rec_field "$r" project_root)"
+    [[ -n "$root" ]] && roots["$root"]=1
+    masks+=("$(_hg_rec_field "$r" cpu_list)")
+    mem="$(_hg_rec_field "$r" memory_high)"
+    bytes="$(_hg_mem_to_bytes "$mem" 2>/dev/null)" || bytes=""
+    if [[ -n "$root" && -n "$bytes" ]]; then
+      if [[ -z "${proj_mem[$root]:-}" ]] || (( bytes > proj_mem[$root] )); then
+        proj_mem["$root"]="$bytes"
+      fi
+    fi
+  done
+
+  # No machine budget configured: enforcement is off, but say so loudly once
+  # two different projects are guarded at the same time — that is exactly the
+  # configuration that reset this host.
+  if [[ -z "$global_cpus" ]]; then
+    if (( ${#roots[@]} >= 2 )); then
+      echo "WARN|no machine-global budget is configured ($(hg_host_env_file) is absent or sets no HOST_GUARD_GLOBAL_CPU_LIST) while ${#roots[@]} guarded sessions are live — their CPU masks union to $(_hg_mask_union "${masks[@]}"), which nothing is checking. See docs/host-guard.md § Machine-global aggregate budget."
+      return 0
+    fi
+    echo "OK"; return 0
+  fi
+
+  local detail=""
+
+  # (a) own mask ⊆ global. This one is NOT arbitrated by seniority: a session
+  # whose own declared mask exceeds the machine budget is misconfigured, and
+  # being the oldest session on the box does not make it safe. Pause always.
+  local own_cpus; own_cpus="$(_hg_rec_field "$own_rec" cpu_list)"
+  if [[ -n "$own_cpus" ]] && ! _hg_mask_is_subset "$own_cpus" "$global_cpus"; then
+    echo "PAUSE|this session's CPU mask ($own_cpus) is not inside the machine budget HOST_GUARD_GLOBAL_CPU_LIST=$global_cpus ($(hg_host_env_file)). Narrow HOST_GUARD_CPU_LIST in this project's project-extensions/host-guard/host-guard.env, or widen the machine budget."
+    return 0
+  fi
+
+  # (b) union of every live mask ⊆ global. Pairwise-subset implies this, but
+  # check it explicitly: it is what catches a hand-edited record, a session
+  # that started before this upgrade, or a registry that lost a write.
+  if [[ -z "$detail" && ${#masks[@]} -gt 0 ]]; then
+    local union; union="$(_hg_mask_union "${masks[@]}")"
+    if ! _hg_mask_is_subset "$union" "$global_cpus"; then
+      detail="the CPU masks of the ${#live[@]} live guarded session(s) union to $union, which exceeds the machine budget HOST_GUARD_GLOBAL_CPU_LIST=$global_cpus"
+    fi
+  fi
+
+  # (c) per-project memory ceilings must fit the machine budget.
+  if [[ -z "$detail" && -n "$global_mem" ]]; then
+    local budget total=0 k
+    if budget="$(_hg_mem_to_bytes "$global_mem")"; then
+      for k in "${!proj_mem[@]}"; do total=$(( total + proj_mem[$k] )); done
+      if (( total > budget )); then
+        detail="the memory ceilings of the ${#roots[@]} live project(s) sum to $(_hg_bytes_to_h "$total"), over the machine budget HOST_GUARD_GLOBAL_MEMORY_BUDGET=$global_mem"
+      fi
+    fi
+  fi
+
+  [[ -n "$detail" ]] || { echo "OK"; return 0; }
+
+  # Someone has to yield. Compare against every OTHER live engine record: if we
+  # are junior to all of them we pause; otherwise we warn and keep going while
+  # the junior session pauses itself on its own next check.
+  local other kind junior=0 senior_desc=""
+  for other in "${live[@]}"; do
+    [[ "$other" == "$own_rec" ]] && continue
+    kind="$(_hg_rec_field "$other" kind)"
+    [[ "$kind" == "engine" ]] || continue
+    if hg_self_is_junior_to "$own_rec" "$other"; then
+      junior=1
+      senior_desc="session '$(_hg_rec_field "$other" session_id)' in $(_hg_rec_field "$other" project_root) (pid $(_hg_rec_field "$other" pid))"
+      break
+    fi
+  done
+
+  if (( junior )); then
+    echo "PAUSE|$detail. The older session holds the budget: $senior_desc. Stop or narrow that session, or widen the budget in $(hg_host_env_file), then resume."
+  else
+    echo "WARN|$detail. This session started first, so it keeps running; the newer session is expected to pause itself."
+  fi
+  return 0
+}
diff --git a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
index 4ae0c8a1..4f61c184 100644
--- a/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
+++ b/incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py
@@ -18,7 +18,14 @@ FAIL that the LLM later re-confirmed as PASS would wrongly keep the file at FAIL
 
 Usage:
   merge_ui_test_results.py <out.md> <in1.md> [<in2.md> ...]
+  merge_ui_test_results.py void <results.md> <J-XX> [<J-YY> ...]
   merge_ui_test_results.py self-test
+
+The `void` subcommand (SPEED-22 mass-false-FAIL breaker) rewrites the listed
+journeys' FAIL rows to SKIP with a "voided" note, recomputes the headline
+verdict from the surviving rows, and appends a dated loud footer — used when
+2 green canary re-checks prove a majority-FAIL replay run was selector/
+environment drift rather than real regressions.
 """
 from __future__ import annotations
 
@@ -33,7 +40,11 @@ from pathlib import Path
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
@@ -165,9 +176,81 @@ def merge(texts: "list[str]") -> str:
     return "\n".join(out) + "\n"
 
 
+_VOID_NOTE = ("voided: suspected selector/environment drift — mass replay FAIL "
+              "overturned by green canary re-checks")
+
+
+def void_text(text: str, journeys: "list[str]") -> "tuple[str, list[str]]":
+    """Pure transform for the `void` subcommand: rewrite the listed journeys'
+    FAIL rows to SKIP + the voided note, recompute the headline from the
+    surviving rows, append a dated footer. Returns (new_text, voided_ids)."""
+    want = {f"UT-{j}" for j in journeys} | set(journeys)
+    voided: list[str] = []
+    out_lines: list[str] = []
+    for line in text.splitlines():
+        m = _ROW_RE.match(line.strip())
+        if m:
+            tid = m.group(1).strip()
+            # Split on UNESCAPED pipes only — the replay renderer escapes '|'
+            # inside cells as '\|'; a bare split would shift every later cell.
+            cells = [c.strip() for c in re.split(r"(?<!\\)\|", m.group(2))]
+            is_sep = cells and all(set(c) <= {"-", ":"} for c in cells if c)
+            if tid in want and not is_sep and any(c.upper() == "FAIL" for c in cells):
+                new_cells = []
+                for idx, c in enumerate(cells):
+                    if c.upper() == "FAIL":
+                        new_cells.append("SKIP")
+                    elif idx == _C_ACTUAL:
+                        new_cells.append(_VOID_NOTE)
+                    else:
+                        new_cells.append(c)
+                out_lines.append("| " + tid + " | " + " | ".join(new_cells) + " |")
+                voided.append(tid)
+                continue
+        out_lines.append(line)
+    if not voided:
+        return text, []
+    new_text = "\n".join(out_lines)
+    rows = parse_rows(new_text)
+    overall = compute_overall(rows)
+    new_text = _VERDICT_RE.sub(f"**Browser QA Verdict:** {overall}", new_text, count=1)
+    ids = " ".join(sorted({t.replace('UT-', '', 1) for t in voided}))
+    new_text += (
+        f"\n\n---\n\n_VOIDED ({_today()}): the FAIL rows for {ids} above were VOIDED "
+        "(SPEED-22 mass-false-FAIL breaker) — a majority of the replay set failed at "
+        "once and the canary journeys re-checked GREEN via the LLM lane, so the "
+        "failures are suspected golden-script/selector drift, not product "
+        "regressions. These journeys keep their prior recorded status; their golden "
+        "scripts are queued for regeneration (state/goldens-regen-pending) and are "
+        "re-derived from the next verified demo recording._\n"
+    )
+    return new_text, sorted({t.replace("UT-", "", 1) for t in voided})
+
+
+def cmd_void(path: str, journeys: "list[str]") -> int:
+    p = Path(path)
+    try:
+        text = p.read_text(encoding="utf-8")
+    except OSError as exc:
+        sys.stderr.write(f"[merge_ui_test_results] void: unreadable {path}: {exc}\n")
+        return 2
+    new_text, voided = void_text(text, journeys)
+    if not voided:
+        print("[merge_ui_test_results] void: no matching FAIL rows — file unchanged")
+        return 0
+    p.write_text(new_text, encoding="utf-8")
+    print(f"[merge_ui_test_results] voided FAIL rows for: {' '.join(voided)}")
+    return 0
+
+
 def main(argv: "list[str]") -> int:
     if argv and argv[0] in ("self-test", "--self-test"):
         return _self_test()
+    if argv and argv[0] == "void":
+        if len(argv) < 3:
+            sys.stderr.write("usage: merge_ui_test_results.py void <results.md> <J-XX> [...]\n")
+            return 2
+        return cmd_void(argv[1], argv[2:])
     if len(argv) < 2:
         sys.stderr.write("usage: merge_ui_test_results.py <out.md> <in1.md> [<in2.md> ...]\n")
         return 2
@@ -273,12 +356,90 @@ def _self_test() -> int:
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
+    mass = (
+        "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
+        "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+        "|---|---|---|---|---|---|---|---|\n"
+        "| UT-J-01 | login | regression | P1 | e | ok | PASS | a.png |\n"
+        "| UT-J-02 | browse | regression | P1 | e | step 2 failed | FAIL | b.png |\n"
+        "| UT-J-03 | export | regression | P1 | e | step 1 failed | FAIL | c.png |\n"
+        "| UT-J-04 | filter | regression | P1 | e | step 4 failed | FAIL | d.png |\n")
+
+    def t_void_rewrites_and_recomputes():
+        # Void ALL the FAILs → SKIP rows with the note, headline flips to PASS
+        # (the surviving PASS row wins), dated footer appended exactly once.
+        new, voided = void_text(mass, ["J-02", "J-03", "J-04"])
+        assert voided == ["J-02", "J-03", "J-04"], voided
+        rows = {r["test_id"]: r["verdict"] for r in parse_rows(new)}
+        assert rows == {"UT-J-01": "PASS", "UT-J-02": "SKIP", "UT-J-03": "SKIP", "UT-J-04": "SKIP"}, rows
+        assert file_top_verdict(new) == "PASS", file_top_verdict(new)
+        assert new.count("_VOIDED (") == 1 and "voided: suspected selector" in new
+        assert new.count("**Browser QA Verdict:**") == 1
+
+    def t_void_keeps_unlisted_fail():
+        # An un-listed FAIL survives and keeps the headline at FAIL.
+        new, voided = void_text(mass, ["J-02"])
+        assert voided == ["J-02"], voided
+        rows = {r["test_id"]: r["verdict"] for r in parse_rows(new)}
+        assert rows["UT-J-03"] == "FAIL" and rows["UT-J-02"] == "SKIP", rows
+        assert file_top_verdict(new) == "FAIL", file_top_verdict(new)
+
+    def t_void_no_match_is_noop():
+        new, voided = void_text(mass, ["J-99"])
+        assert voided == [] and new == mass
+
+    def t_void_respects_escaped_pipes():
+        # The replay renderer escapes '|' in cells; void must not split on it.
+        esc = (
+            "**Browser QA Verdict:** FAIL\n\n## Results Table\n"
+            "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |\n"
+            "|---|---|---|---|---|---|---|---|\n"
+            "| UT-J-07 | Filter \\| sort table | regression | P1 | e | step 2 failed | FAIL | b.png |\n")
+        new, voided = void_text(esc, ["J-07"])
+        assert voided == ["J-07"], voided
+        row = [l for l in new.splitlines() if l.startswith("| UT-J-07")][0]
+        # verdict flipped, the note landed in the Actual cell, the escaped
+        # pipe survived, and the column count is unchanged
+        assert "| SKIP |" in row and _VOID_NOTE in row and "\\|" in row, row
+        assert len(re.split(r"(?<!\\)\|", row)) == len(re.split(r"(?<!\\)\|",
+            "| UT-J-07 | Filter \\| sort table | regression | P1 | e | step 2 failed | FAIL | b.png |")), row
+
+    # Self-counting list (local form) rather than a hardcoded total — upstream's void
+    # tests and the local verdict-normalization tests both live here, so a literal
+    # count goes stale on the next pull.
     checks = [("parse_rows", t_parse),
               ("later_wins_override", t_later_wins),
               ("real_fail_survives", t_real_fail_survives),
               ("skipped_only", t_skipped_only),
               ("bold_verdicts", t_bold_verdicts),
-              ("annotated_verdicts", t_annotated_verdicts)]
+              ("annotated_verdicts", t_annotated_verdicts),
+              ("tc_prefixed_fail_survives", t_tc_prefixed_fail_survives),
+              ("void_rewrites_and_recomputes", t_void_rewrites_and_recomputes),
+              ("void_keeps_unlisted_fail", t_void_keeps_unlisted_fail),
+              ("void_no_match_is_noop", t_void_no_match_is_noop),
+              ("void_respects_escaped_pipes", t_void_respects_escaped_pipes)]
     for name, fn in checks:
         check(name, fn)
 
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index 9864a049..00ceb3f6 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -47,11 +47,13 @@
 # serializes exactly these names through its state file (_bqa_state_save), so
 # they are a cross-process contract, not a style choice.
 #   In:  REQUIRED_JOURNEYS, FRONTEND_AVAILABLE, FRONTEND_URL, REPO_ROOT,
-#        CHAIN_REGRESSION_REPLAY (knob, default true)
+#        CHAIN_REGRESSION_REPLAY (knob, default true),
+#        REPLAY_LANE_CANARY_CAPABLE (SPEED-22; set only by goal-iter-lean.sh)
 #   Set by replay_lane_paths: EVIDENCE_DIR, SID, JOURNEY_SCRIPTS_DIR,
-#        REGRESSION_RESULTS, LLM_RESULTS, DEMO_RUNNER, MERGE_RESULTS
+#        REGRESSION_RESULTS, LLM_RESULTS, CANARY_RESULTS, DEMO_RUNNER,
+#        MERGE_RESULTS
 #   Out of partition+verify: R_REPLAY, R_LLM, _use_replay, REPLAY_FAILED,
-#        REPLAY_SKIPPED_INFRA
+#        REPLAY_SKIPPED_INFRA, REPLAY_MASS_FAIL, REPLAY_CANARIES (SPEED-22)
 
 _REPLAY_LANE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 
@@ -82,6 +84,7 @@ replay_lane_paths() {
   mkdir -p "$JOURNEY_SCRIPTS_DIR"
   REGRESSION_RESULTS="$REPO_ROOT/reports/phase-${_rl_iter}-regression-replay-results.md"
   LLM_RESULTS="$REPO_ROOT/reports/phase-${_rl_iter}-ui-test-results.llm.md"
+  CANARY_RESULTS="$REPO_ROOT/reports/phase-${_rl_iter}-ui-test-results.canary.md"
   DEMO_RUNNER="$_REPLAY_LANE_LIB_DIR/demo_runner.py"
   MERGE_RESULTS="$_REPLAY_LANE_LIB_DIR/merge_ui_test_results.py"
 }
@@ -157,6 +160,18 @@ bqa_services_probe() {
   return 0
 }
 
+# bqa_browser_confine — put escaped QA browsers back inside the host-guard mask
+# before dispatching. UNCONDITIONAL, unlike the REL-14 services preflight above:
+# a browser that escaped confinement is a hardware-safety problem, not a QA
+# convenience, so it must not depend on CHAIN_BQA_PREFLIGHT being opted in.
+# No-ops when the project declares no host-guard.
+bqa_browser_confine() {
+  local bc; bc="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../host-guard/browser-confine.sh"
+  [[ -f "$bc" ]] || return 0
+  HOST_GUARD_ROOT="${HOST_GUARD_ROOT:-$REPO_ROOT}" bash "$bc" || true
+  return 0
+}
+
 # bqa_preflight — probe → one re-check via ensure_services_running (idempotent:
 # it returns immediately when services already answer) → probe again. Mirrors
 # the REL-5 rc-6 retry shape above. Returns 0 = the dispatch may proceed;
@@ -225,7 +240,7 @@ replay_lane_partition_and_verify() {
   # into this run — a merge would ingest them as current output, and a lane
   # that does not engage this run (no goldens, hatch off) would leave last
   # run's files masquerading as this iteration's. Absent beats stale.
-  rm -f "$REGRESSION_RESULTS" "$LLM_RESULTS" 2>/dev/null || true
+  rm -f "$REGRESSION_RESULTS" "$LLM_RESULTS" "$CANARY_RESULTS" 2>/dev/null || true
 
   # A golden that fails validation is quarantined (renamed *.json.invalid) and
   # its journey routed to the LLM lane — previously an invalid golden produced
@@ -262,6 +277,8 @@ replay_lane_partition_and_verify() {
   # scripts exist).
   REPLAY_FAILED=""
   REPLAY_SKIPPED_INFRA=""
+  REPLAY_MASS_FAIL=""
+  REPLAY_CANARIES=""
   if [[ "$_use_replay" == "yes" ]]; then
     _replay_lane_log "Regression (deterministic replay): $R_REPLAY"
     local _replay_csv _replay_rc=0
@@ -284,6 +301,27 @@ replay_lane_partition_and_verify() {
     if [[ "$_replay_rc" -eq 5 ]]; then
       REPLAY_FAILED="$(grep -E '^\| UT-J-[0-9]+ ' "$REGRESSION_RESULTS" 2>/dev/null | grep -F '| FAIL |' | grep -oE 'J-[0-9]+' | sort -u | tr '\n' ' ')"
       _replay_lane_log "Replay flagged possible regression(s) — re-confirming via LLM: $REPLAY_FAILED"
+      # SPEED-22 mass-false-FAIL detection: a MAJORITY-FAIL replay run (>2
+      # FAILs and more than half the ran set) is far more likely selector/
+      # environment drift than 3+ simultaneous real regressions (desk iter-14:
+      # 8/9 false FAILs → 28 min of LLM overturns). Arm the canary probe: the
+      # lean executor re-confirms the 2 lowest-ID FAILs FIRST and only fans
+      # out to the full re-confirm set if a canary really fails. Detection is
+      # gated on REPLAY_LANE_CANARY_CAPABLE=1 — set ONLY by goal-iter-lean.sh
+      # (the full pipeline has no separate canary dispatch slot and stays
+      # byte-identical). 8/9 triggers; 2/9 and 3/6 do not.
+      REPLAY_MASS_FAIL=""
+      REPLAY_CANARIES=""
+      if [[ "${REPLAY_LANE_CANARY_CAPABLE:-}" == "1" && "${CHAIN_REPLAY_MASS_FAIL_BREAKER:-true}" == "true" ]]; then
+        local _mf_ran _mf_fail
+        _mf_ran="$(grep -cE '^\| UT-J-[0-9]+ ' "$REGRESSION_RESULTS" 2>/dev/null || true)"
+        _mf_fail="$(echo "$REPLAY_FAILED" | wc -w)"
+        if [[ "${_mf_fail:-0}" -gt 2 && "${_mf_ran:-0}" -gt 0 ]] && (( 2 * _mf_fail > _mf_ran )); then
+          REPLAY_MASS_FAIL="yes"
+          REPLAY_CANARIES="$(echo "$REPLAY_FAILED" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -t- -k2,2n | head -2 | tr '\n' ' ' || true)"
+          _replay_lane_log "SPEED-22 mass-FAIL breaker armed: $_mf_fail of $_mf_ran replay journeys FAILed at once — canaries ${REPLAY_CANARIES% }will be re-checked before burning re-confirms on the whole set (CHAIN_REPLAY_MASS_FAIL_BREAKER=false disables)."
+        fi
+      fi
     elif [[ "$_replay_rc" -eq 6 ]]; then
       # REL-5: browser infra failed twice (one retry after a service re-check).
       # The lane's recorded state is SKIPPED-INFRA — distinct from FAIL (no
@@ -310,8 +348,40 @@ replay_lane_partition_and_verify() {
   fi
 }
 
+# SPEED-15 rung-2 decision, in ONE place: over the wall-clock budget in trim
+# mode with the replay lane engaged, the no-golden regression journeys (R_LLM)
+# are DEFERRED to a later iteration instead of riding the slow LLM lane now.
+# $1 (optional) = journeys to EXCLUDE from deferral because they are
+# dispatched anyway — the caller's Target set: a journey listed as BOTH a
+# target and a required-no-golden journey gets a real verdict row from the
+# target dispatch, and a DEFERRED-BUDGET row beside it would contradict the
+# record and wrongly block GOAL_ACHIEVED.
+# Echoes the deferred set ("" = no narrowing). PURE — no logging/telemetry
+# (callers capture via $(...)): the caller stores the result in
+# REPLAY_DEFERRED_BUDGET ONCE per run, logs, and emits the trim event. The
+# budget clock keeps ticking, so recomputing later could disagree with what
+# was actually dispatched — never call this twice for one run. Replay-FAIL
+# re-confirms are structurally exempt: replay_lane_llm_regression_set below
+# always keeps them.
+replay_lane_deferred_budget_set() {
+  if [[ "${_use_replay:-no}" == "yes" ]] \
+     && declare -F iter_budget_trim_active >/dev/null 2>&1 && iter_budget_trim_active \
+     && [[ -n "${R_LLM// /}" ]]; then
+    local _db_out="" _j
+    for _j in $(echo "$R_LLM" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u); do
+      [[ " ${1:-} " == *" $_j "* ]] || _db_out+="$_j "
+    done
+    echo "$_db_out"
+  else
+    echo ""
+  fi
+}
+
 # The regression journeys the LLM lane must cover this run, deduped:
-#   replay engaged → the replay FAILs to re-confirm + the no-golden journeys;
+#   replay engaged → the replay FAILs to re-confirm + the no-golden journeys
+#     (minus the rung-2 deferred set when the caller armed
+#     REPLAY_DEFERRED_BUDGET — replay-FAIL re-confirms are NEVER deferred: a
+#     possible real regression must be re-confirmed this iteration);
 #   replay off (hatch/no goldens/frontend down/crash) → the WHOLE required set,
 #   so the DoD line "Required-still-passing journeys remain green" always has a
 #   verifier at both depths. Same pipefail guard as replay_lane_spec_journeys:
@@ -319,21 +389,58 @@ replay_lane_partition_and_verify() {
 replay_lane_llm_regression_set() {
   local _rl_set
   if [[ "${_use_replay:-no}" == "yes" ]]; then
-    _rl_set="$REPLAY_FAILED $R_LLM"
+    if [[ -n "${REPLAY_DEFERRED_BUDGET:-}" && -n "${REPLAY_DEFERRED_BUDGET// /}" ]]; then
+      _rl_set="$REPLAY_FAILED"
+    else
+      _rl_set="$REPLAY_FAILED $R_LLM"
+    fi
   else
     _rl_set="$REQUIRED_JOURNEYS"
   fi
   echo "$_rl_set" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ' ' || true
 }
 
+# SPEED-15 rung 2, write side: after the merge, append one DEFERRED-BUDGET row
+# per deferred journey to the merged results file $1 so the record is honest —
+# the journey was NOT re-verified this iteration. The goal-evaluator contract
+# scores a DEFERRED-BUDGET row as "keeps prior recorded status" (never a
+# regression), and the deterministic achievement gate (goal_gate.py results)
+# treats any DEFERRED-BUDGET row as blocking, so a deferred journey can never
+# certify GOAL_ACHIEVED. No-op when the caller never armed the deferred set.
+replay_lane_write_deferred_rows() {
+  local _rl_merged="$1"
+  [[ -n "${REPLAY_DEFERRED_BUDGET:-}" && -n "${REPLAY_DEFERRED_BUDGET// /}" && -f "$_rl_merged" ]] || return 0
+  local _j
+  {
+    echo ""
+    echo "## Deferred (iteration budget)"
+    echo ""
+    echo "_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the"
+    echo "no-golden regression journeys below were NOT re-verified this iteration and"
+    echo "keep their prior recorded status. They are re-queued for a later iteration_"
+    echo ""
+    echo "| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |"
+    echo "|---------|------|------|----------|----------|--------|---------|----------|"
+    for _j in $REPLAY_DEFERRED_BUDGET; do
+      printf '| UT-%s | %s regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |\n' "$_j" "$_j"
+    done
+  } >> "$_rl_merged" 2>/dev/null || true
+  _replay_lane_log "iter-budget trim (rung 2): DEFERRED-BUDGET rows appended for ${REPLAY_DEFERRED_BUDGET% }(prior statuses kept; GOAL_ACHIEVED blocked while any journey is deferred)."
+}
+
 # Merge replay + LLM lane outputs into $1 — the single authoritative results
 # file the goal-evaluator and the deterministic achievement gate read. $2 = the
 # LLM lane's output file. LLM listed LAST → wins on any journey both lanes
-# touched (e.g. a replay-FAIL re-confirm). On merge failure, degrade to a lane
-# copy (LLM preferred) so the evaluator always has something to read.
+# touched (e.g. a replay-FAIL re-confirm). SPEED-22: when a canary results
+# file exists (mass-FAIL probe ran), it merges as a MIDDLE input — its fresh
+# canary verdicts beat the (possibly voided) replay rows, and the main LLM
+# lane still wins where it re-tested a journey. On merge failure, degrade to a
+# lane copy (LLM preferred) so the evaluator always has something to read.
 replay_lane_merge_results() {
   local _rl_out="$1" _rl_llm="$2"
-  if ! python3 "$MERGE_RESULTS" "$_rl_out" "$REGRESSION_RESULTS" "$_rl_llm"; then
+  local _rl_mid=()
+  [[ -n "${CANARY_RESULTS:-}" && -f "${CANARY_RESULTS:-}" ]] && _rl_mid=("$CANARY_RESULTS")
+  if ! python3 "$MERGE_RESULTS" "$_rl_out" "$REGRESSION_RESULTS" ${_rl_mid[@]+"${_rl_mid[@]}"} "$_rl_llm"; then
     _replay_lane_warn "results merge failed — falling back to a lane output."
     if [[ -f "$_rl_llm" ]]; then cp "$_rl_llm" "$_rl_out" 2>/dev/null || true
     elif [[ -f "$REGRESSION_RESULTS" ]]; then cp "$REGRESSION_RESULTS" "$_rl_out" 2>/dev/null || true; fi
@@ -372,7 +479,9 @@ replay_lane_reconcile_regression_artifact() {
 # lintable golden so the replay lane keeps growing (browser-qa LLM time decays
 # iteration over iteration). A gap is loud but non-gating — those journeys
 # simply return to the LLM lane next iteration. $2 = iter/phase name for the
-# telemetry event (no-op when telemetry.sh is not sourced).
+# telemetry event (no-op when telemetry.sh is not sourced). SPEED-23: the gap
+# list is also PERSISTED to state/golden-gaps so the next iteration's nudge
+# pick and the SPEED-21 auto-derivation can read it (empty gap → file removed).
 replay_lane_golden_coverage() {
   local _rl_results="$1" _rl_iter="$2"
   local _pass_j _n_pass=0 _missing_golden="" _j
@@ -381,10 +490,183 @@ replay_lane_golden_coverage() {
     _n_pass=$((_n_pass + 1))
     [[ -f "$JOURNEY_SCRIPTS_DIR/$_j.json" ]] || _missing_golden+="$_j "
   done
+  local _gaps_file="$REPO_ROOT/runs/goal-session-${SID}/state/golden-gaps"
   if [[ -n "${_missing_golden// /}" ]]; then
     _replay_lane_log "Golden coverage gap: PASSing journey(s) without a replay script: ${_missing_golden}— the browser-qa agent should write a golden per PASS (they fall back to the slower LLM lane next iteration)."
+    mkdir -p "$(dirname "$_gaps_file")" 2>/dev/null || true
+    echo "$_missing_golden" | tr ' ' '\n' | grep -E '^J-[0-9]+$' > "$_gaps_file" 2>/dev/null || true
+  else
+    rm -f "$_gaps_file" 2>/dev/null || true
   fi
   if declare -F record_telemetry_event >/dev/null 2>&1; then
     record_telemetry_event "golden_coverage" "$(jq -cn --argjson p "$_n_pass" --arg m "${_missing_golden% }" --arg n "$_rl_iter" '{passing:$p, missing_goldens:$m, iter_name:$n}' 2>/dev/null || printf '{"passing":%d,"missing_goldens":"%s"}' "$_n_pass" "${_missing_golden% }")"
   fi
 }
+
+# ── SPEED-21: golden auto-derivation from the verified demo ──────────────────
+# replay_lane_autoderive_goldens <phase> <demo-json> <results-md>
+# After a successful demo recording (record mode, goal iteration, runner rc 0),
+# derive candidate goldens for PASSing journeys that lack one — plus PASS
+# journeys parked in state/goldens-regen-pending (SPEED-22 voids park regen
+# requests there) — capped at CHAIN_GOLDEN_AUTODERIVE_MAX (default 3) per
+# iteration. Every candidate gets a REAL verify pass in a throwaway scripts-dir
+# against $FRONTEND_URL before installation:
+#   rc 0        → atomic install into journey-scripts/ + golden_autoderived
+#   rc 5        → discard this candidate + golden_autoderive_rejected
+#   rc 6/other  → browser infra unhealthy — discard ALL remaining candidates
+# Gate: CHAIN_GOLDEN_AUTODERIVE (default true). Requires replay_lane_paths to
+# have run (SID/JOURNEY_SCRIPTS_DIR/DEMO_RUNNER). NEVER gates the pipeline and
+# never returns non-zero.
+replay_lane_autoderive_goldens() {
+  local _ad_iter="$1" _ad_demo="$2" _ad_results="$3"
+  [[ "${CHAIN_GOLDEN_AUTODERIVE:-true}" == "true" ]] || return 0
+  [[ -f "$_ad_demo" && -f "$_ad_results" ]] || return 0
+  local _ad_regen="$REPO_ROOT/runs/goal-session-${SID}/state/goldens-regen-pending"
+  local _ad_pass _ad_want="" _j
+  _ad_pass="$(grep -E '^\| UT-J-[0-9]+ ' "$_ad_results" 2>/dev/null | grep -F '| PASS |' | grep -oE 'J-[0-9]+' | sort -u | tr '\n' ' ' || true)"
+  for _j in $_ad_pass; do
+    if [[ ! -f "$JOURNEY_SCRIPTS_DIR/$_j.json" ]]; then
+      _ad_want+="$_j "
+    elif [[ -f "$_ad_regen" ]] && grep -qx "$_j" "$_ad_regen" 2>/dev/null; then
+      _ad_want+="$_j "
+    fi
+  done
+  local _ad_cap="${CHAIN_GOLDEN_AUTODERIVE_MAX:-3}"
+  [[ "$_ad_cap" =~ ^[0-9]+$ ]] || _ad_cap=3
+  _ad_want="$(echo "$_ad_want" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | head -n "$_ad_cap" | tr '\n' ' ' || true)"
+  [[ -n "${_ad_want// /}" ]] || return 0
+  local _ad_tmp="${CHAIN_TMPDIR:-${TMPDIR:-/tmp}}/golden-autoderive.$$"
+  mkdir -p "$_ad_tmp" 2>/dev/null || return 0
+  _replay_lane_log "SPEED-21: deriving golden candidate(s) from the verified demo for: ${_ad_want% }(cap ${_ad_cap}; CHAIN_GOLDEN_AUTODERIVE=false disables)."
+  python3 "$DEMO_RUNNER" --mode derive --json "$_ad_demo" --scripts-dir "$_ad_tmp" \
+    --journeys "$(echo "$_ad_want" | tr ' ' ',' | sed 's/^,*//;s/,*$//')" 2>/dev/null \
+    | while IFS= read -r _line; do _replay_lane_log "SPEED-21 derive: $_line"; done || true
+  local _ad_infra=""
+  for _j in $_ad_want; do
+    [[ -n "$_ad_infra" ]] && break
+    local _cand="$_ad_tmp/$_j.json.candidate"
+    [[ -s "$_cand" ]] || continue
+    local _vdir="$_ad_tmp/verify-$_j"
+    mkdir -p "$_vdir" 2>/dev/null || continue
+    cp "$_cand" "$_vdir/$_j.json" 2>/dev/null || continue
+    local _vrc=0
+    python3 "$DEMO_RUNNER" --mode verify --scripts-dir "$_vdir" --journeys "$_j" \
+      --results "$_vdir/results.md" --evidence-dir "$_vdir/evidence" \
+      --base-url "$FRONTEND_URL" --phase-id "$_ad_iter" --repo-root "$REPO_ROOT" \
+      >/dev/null 2>&1 || _vrc=$?
+    if [[ "$_vrc" -eq 0 ]]; then
+      # Atomic install: stage inside the destination dir, then rename.
+      if cp "$_vdir/$_j.json" "$JOURNEY_SCRIPTS_DIR/.$_j.json.autoderive.$$" 2>/dev/null \
+         && mv -f "$JOURNEY_SCRIPTS_DIR/.$_j.json.autoderive.$$" "$JOURNEY_SCRIPTS_DIR/$_j.json" 2>/dev/null; then
+        _replay_lane_log "SPEED-21: golden INSTALLED for $_j (candidate replayed green against $FRONTEND_URL)."
+        if [[ -f "$_ad_regen" ]]; then
+          grep -vx "$_j" "$_ad_regen" > "$_ad_regen.tmp.$$" 2>/dev/null || true
+          mv -f "$_ad_regen.tmp.$$" "$_ad_regen" 2>/dev/null || rm -f "$_ad_regen.tmp.$$" 2>/dev/null || true
+          [[ -s "$_ad_regen" ]] || rm -f "$_ad_regen" 2>/dev/null || true
+        fi
+        if declare -F record_telemetry_event >/dev/null 2>&1; then
+          record_telemetry_event "golden_autoderived" "$(jq -cn --arg j "$_j" --arg n "$_ad_iter" '{journey:$j, iter_name:$n}' 2>/dev/null || printf '{"journey":"%s"}' "$_j")"
+        fi
+      fi
+    elif [[ "$_vrc" -eq 5 ]]; then
+      _replay_lane_log "SPEED-21: candidate for $_j FAILED its verify pass — discarded (the LLM lane keeps covering it)."
+      if declare -F record_telemetry_event >/dev/null 2>&1; then
+        record_telemetry_event "golden_autoderive_rejected" "$(jq -cn --arg j "$_j" --arg n "$_ad_iter" '{journey:$j, iter_name:$n, reason:"verify-fail"}' 2>/dev/null || printf '{"journey":"%s"}' "$_j")"
+      fi
+    else
+      _replay_lane_warn "SPEED-21: verify pass hit browser/runner trouble (rc=$_vrc) — discarding ALL remaining candidates this iteration (never gates)."
+      _ad_infra=1
+    fi
+  done
+  rm -rf "$_ad_tmp" 2>/dev/null || true
+  return 0
+}
+
+# ── SPEED-22: mass-false-FAIL canary verdict + void ──────────────────────────
+# replay_lane_canaries_all_pass <canary-results-md> <canaries-space-sep>
+# True iff EVERY canary journey has a PASS row in the canary results file.
+# Conservative by design: a missing file, an unparsable file, a missing row,
+# or any non-PASS verdict returns 1 → the caller keeps today's full
+# re-confirm behavior (a false negative just costs the old path).
+replay_lane_canaries_all_pass() {
+  local _cp_file="$1" _cp_set="$2" _j
+  [[ -f "$_cp_file" && -n "${_cp_set// /}" ]] || return 1
+  for _j in $_cp_set; do
+    grep -E "^\| UT-$_j " "$_cp_file" 2>/dev/null | grep -qF '| PASS |' || return 1
+  done
+  return 0
+}
+
+# replay_lane_void_mass_fail <iter-name>
+# All canaries re-checked GREEN → the mass replay FAIL is drift, not
+# regression. Rewrite the raw replay artifact's FAIL rows to SKIP + voided
+# note (merge_ui_test_results.py void — recomputes the headline and appends a
+# dated loud footer), queue every voided journey for golden regeneration
+# (state/goldens-regen-pending — SPEED-21 re-derives them verified-green from
+# the next demo), clear REPLAY_FAILED so the main LLM dispatch does not
+# re-confirm the whole set, and record replay_mass_fail_voided. If the void
+# rewrite itself fails, keep today's behavior (REPLAY_FAILED intact).
+replay_lane_void_mass_fail() {
+  local _vm_iter="$1"
+  local _vm_ids="${REPLAY_FAILED% }"
+  [[ -n "${_vm_ids// /}" ]] || return 0
+  # shellcheck disable=SC2086  # word-splitting the journey list is the point
+  if ! python3 "$MERGE_RESULTS" void "$REGRESSION_RESULTS" $_vm_ids; then
+    _replay_lane_warn "SPEED-22: void rewrite failed — keeping the full re-confirm set (conservative)."
+    return 1
+  fi
+  local _vm_state="$REPO_ROOT/runs/goal-session-${SID}/state"
+  mkdir -p "$_vm_state" 2>/dev/null || true
+  { cat "$_vm_state/goldens-regen-pending" 2>/dev/null || true; echo "$_vm_ids" | tr ' ' '\n'; } \
+    | grep -E '^J-[0-9]+$' | sort -u > "$_vm_state/goldens-regen-pending.tmp.$$" 2>/dev/null \
+    && mv -f "$_vm_state/goldens-regen-pending.tmp.$$" "$_vm_state/goldens-regen-pending" 2>/dev/null \
+    || rm -f "$_vm_state/goldens-regen-pending.tmp.$$" 2>/dev/null || true
+  _replay_lane_log "SPEED-22: mass replay FAIL VOIDED for ${_vm_ids}(canaries ${REPLAY_CANARIES% }re-checked green) — prior statuses kept, goldens queued for regeneration, no further re-confirms this iteration."
+  if declare -F record_telemetry_event >/dev/null 2>&1; then
+    record_telemetry_event "replay_mass_fail_voided" "$(jq -cn --arg n "$_vm_iter" --arg j "$_vm_ids" --arg c "${REPLAY_CANARIES% }" '{iter_name:$n, journeys:$j, canaries:$c}' 2>/dev/null || printf '{"iter_name":"%s","journeys":"%s"}' "$_vm_iter" "$_vm_ids")"
+  fi
+  REPLAY_FAILED=""
+  return 0
+}
+
+# ── SPEED-23: bounded golden-coverage nudge ──────────────────────────────────
+# replay_lane_golden_nudge_pick <llm-journeys-space-sep>
+# Picks ONE journey from (persisted golden gaps ∩ this run's LLM set) to turn
+# from best-effort golden authoring into a REQUIRED deliverable this dispatch.
+# Rotation: min nudge-count first (ties → lowest ID), counts persisted in
+# state/golden-nudge.json — so one stubborn journey cannot monopolize the
+# nudge. Echoes the journey ID (or nothing). PURE stdout — callers capture via
+# $(...); the count update is a file write, so it survives the subshell. Gate:
+# CHAIN_GOLDEN_NUDGE (default true).
+replay_lane_golden_nudge_pick() {
+  local _gn_set="$1"
+  [[ "${CHAIN_GOLDEN_NUDGE:-true}" == "true" ]] || return 0
+  local _gn_gaps="$REPO_ROOT/runs/goal-session-${SID}/state/golden-gaps"
+  [[ -s "$_gn_gaps" && -n "${_gn_set// /}" ]] || return 0
+  GN_SET="$_gn_set" python3 - "$_gn_gaps" "$REPO_ROOT/runs/goal-session-${SID}/state/golden-nudge.json" 2>/dev/null <<'PY' || true
+import json, os, sys
+try:
+    gaps = set(open(sys.argv[1]).read().split())
+except Exception:
+    sys.exit(0)
+llm = set(os.environ.get("GN_SET", "").split())
+cands = sorted(gaps & llm)
+if not cands:
+    sys.exit(0)
+try:
+    counts = json.load(open(sys.argv[2]))
+    if not isinstance(counts, dict):
+        counts = {}
+except Exception:
+    counts = {}
+pick = min(cands, key=lambda j: (int(counts.get(j, 0) or 0), j))
+counts[pick] = int(counts.get(pick, 0) or 0) + 1
+try:
+    with open(sys.argv[2], "w") as f:
+        json.dump(counts, f, indent=1)
+        f.write("\n")
+except Exception:
+    pass
+print(pick)
+PY
+}
diff --git a/incredible_auto_dev/scripts/automation/qa-phase.sh b/incredible_auto_dev/scripts/automation/qa-phase.sh
index c3a090d2..1e2b9a34 100755
--- a/incredible_auto_dev/scripts/automation/qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/qa-phase.sh
@@ -128,6 +128,15 @@ fi
 # so it can reference ensure_services_running and the QA_* env vars set above.
 export CHAIN_CLAUDE_PRE_RETRY_HOOK="ensure_services_running"
 
+# ── Host-safety: pinned + headless + confined QA browser (see browser-qa-phase)
+# The "qa" lane suffix keeps this lane off the browser-qa lane's profile lock —
+# the two can run concurrently in the post-dev fanout.
+ensure_qa_browser_env "qa"
+strip_display_for_headless_qa
+if [[ -f "$SCRIPT_DIR/host-guard/browser-confine.sh" ]]; then
+  HOST_GUARD_ROOT="$REPO_ROOT" bash "$SCRIPT_DIR/host-guard/browser-confine.sh" || true
+fi
+
 # ── Run QA agent ──────────────────────────────────────────────────────────
 cd "$REPO_ROOT"
 record_agent_invocation_start qa
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 5c3b54f8..ed95801e 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -175,7 +175,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh; do
+for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 992faeb1..3c451f27 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -66,9 +66,11 @@
 #   AWAITING_DISK    - free disk under the hard floor even after automatic aggressive cleanup;
 #                      free space or run scripts/automation/tmp-doctor.sh --aggressive, then --resume
 #   AWAITING_HOST_GUARD - host-guard preflight/gate failed (hwmon sampler dead and unstartable,
-#                      CPU-affinity wrap absent, a launcher lost its HOST-GUARD cap block, or the
-#                      interactive pump session is unconfined); fix per the printed reason
-#                      (project-extensions/host-guard/README.md), then --resume
+#                      CPU-affinity wrap absent, a launcher lost its HOST-GUARD cap block, the
+#                      interactive pump session is unconfined, the machine-global CPU/memory
+#                      budget is exceeded by the concurrently running sessions, or CPU boost was
+#                      re-enabled); fix per the printed reason (docs/host-guard.md,
+#                      project-extensions/host-guard/README.md), then --resume
 #
 # Quota exhaustion is NOT a halt: claude_with_quota_retry transparently sleeps
 # until the quota resets and resumes.
@@ -86,6 +88,7 @@ source "$SCRIPT_DIR/lib/telemetry.sh"
 source "$SCRIPT_DIR/lib/goal-gates.sh"
 source "$SCRIPT_DIR/lib/engine-lock.sh"
 source "$SCRIPT_DIR/lib/plain-language.sh"
+source "$SCRIPT_DIR/lib/host-guard-registry.sh"
 
 # ── Host-guard self-wrap (hardware protection) ─────────────────────────────
 # Origin: a mini-PC host hard-reset instantly (no OOM, no thermal log, no
@@ -607,6 +610,7 @@ _run_showcase_steps() {
   if declare -F iter_budget_trim_active >/dev/null 2>&1 && iter_budget_trim_active; then
     _budget_trim=1
     echo "[run-goal] iter-budget trim: over budget — deferring demo recording + README refresh this iteration (summarizer still runs)."
+    declare -F iter_budget_trim_event >/dev/null 2>&1 && iter_budget_trim_event "showcase-defer"
   fi
   # Demo first (lean depth only — full depth records inside run-phase.sh).
   # demo-phase.sh boots its own services idempotently; _join_showcase_tail
@@ -1004,6 +1008,38 @@ preflight_host_guard() {
     done
   fi
 
+  # 4. Machine-global aggregate budget + host-level assumptions. Checks 1-3 all
+  # verify THIS session in isolation; two sessions that each pass can still put
+  # the machine over budget (the 2026-07-29 reset: complementary masks, union =
+  # every core). The host budget file lives outside every repo — absent ⇒ this
+  # check only warns. lib/host-guard-registry.sh carries the mechanics.
+  if [[ -z "$fail_reason" ]]; then
+    hg_load_host_env
+    local hg_msg=""
+    if ! hg_msg="$(hg_boost_ok)"; then
+      fail_reason="$hg_msg"
+    elif [[ -n "${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-}" ]] \
+         && ! _hg_mem_to_bytes "$HOST_GUARD_GLOBAL_MEMORY_BUDGET" >/dev/null; then
+      fail_reason="HOST_GUARD_GLOBAL_MEMORY_BUDGET='$HOST_GUARD_GLOBAL_MEMORY_BUDGET' in $(hg_host_env_file) is not a size like '22G' — fix the machine budget file"
+    else
+      # Register BEFORE verifying: two engines starting at once must each see
+      # the other, so the deterministic junior-loses order can pick exactly one.
+      local own_rec verdict
+      own_rec="$(hg_register engine "$$" "$REPO_ROOT" "$SESSION_ID" "${HOST_GUARD_CPU_LIST:-}" "${HOST_GUARD_MEMORY_HIGH:-18G}")"
+      hg_sweep
+      verdict="$(hg_aggregate_verdict "$own_rec")"
+      case "$verdict" in
+        PAUSE\|*)
+          hg_release
+          fail_reason="${verdict#PAUSE|}" ;;
+        WARN\|*)
+          echo "[run-goal] host-guard WARNING: ${verdict#WARN|}"
+          record_telemetry_event "host_guard_aggregate_warn" \
+            "$(python3 -c 'import json,sys; print(json.dumps({"detail": sys.argv[1]}))' "${verdict#WARN|}")" ;;
+      esac
+    fi
+  fi
+
   [[ -n "$fail_reason" ]] || return 0
   _host_guard_pause "$fail_reason" "preflight"
 }
@@ -1070,7 +1106,8 @@ host_guard_iteration_gate() {
         # HOST_GUARD_ADOPT=0 skips the self-heal and pauses immediately.
         if [[ "${HOST_GUARD_ADOPT:-1}" == "1" ]]; then
           echo "[run-goal] host-guard: pump (pid $target) unconfined (Cpus_allowed_list=$allowed_list) — auto-confining in place."
-          HOST_GUARD_ROOT="$REPO_ROOT" bash "$SCRIPT_DIR/host-guard-adopt.sh" --cli-root-of "$target" || true
+          HOST_GUARD_ROOT="$REPO_ROOT" HOST_GUARD_SESSION_ID="$SESSION_ID" \
+            bash "$SCRIPT_DIR/host-guard-adopt.sh" --cli-root-of "$target" || true
           allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$target/status" 2>/dev/null)
           allowed_n=$(_host_guard_mask_width "$allowed_list")
         fi
@@ -1087,6 +1124,30 @@ host_guard_iteration_gate() {
       _host_guard_pause "cannot verify pump confinement: no usable pump pid ($hb has no pid= line and no CLI root was captured at engine launch) — re-enable the pump ident or set HOST_GUARD_REQUIRE_PUMP_CONFINED=0" "iteration_gate"
     fi
   fi
+
+  # (c) machine-global aggregate budget + boost assumption, re-checked every
+  # iteration: the other project's session may have started AFTER our preflight,
+  # and a host-level knob can regress mid-run. Registering here doubles as the
+  # heartbeat and self-heals a registry wiped by a cache sweep. Runs after (b)
+  # so an adopted pump is already registered when the union is computed.
+  hg_load_host_env
+  local hg_own_rec hg_verdict hg_msg=""
+  hg_own_rec="$(hg_register engine "$$" "$REPO_ROOT" "$SESSION_ID" "${HOST_GUARD_CPU_LIST:-}" "${HOST_GUARD_MEMORY_HIGH:-18G}")"
+  hg_sweep
+  if ! hg_msg="$(hg_boost_ok)"; then
+    write_session_summary "AWAITING_HOST_GUARD" "$CURRENT_ITER"
+    _host_guard_pause "$hg_msg" "iteration_gate"
+  fi
+  hg_verdict="$(hg_aggregate_verdict "$hg_own_rec")"
+  case "$hg_verdict" in
+    PAUSE\|*)
+      write_session_summary "AWAITING_HOST_GUARD" "$CURRENT_ITER"
+      _host_guard_pause "${hg_verdict#PAUSE|}" "iteration_gate" ;;
+    WARN\|*)
+      echo "[run-goal] host-guard WARNING: ${hg_verdict#WARN|}"
+      record_telemetry_event "host_guard_aggregate_warn" \
+        "$(python3 -c 'import json,sys; print(json.dumps({"detail": sys.argv[1]}))' "${hg_verdict#WARN|}")" ;;
+  esac
   return 0
 }
 
@@ -1710,6 +1771,9 @@ _goal_engine_on_exit() {
   _join_showcase_tail --kill 2>/dev/null || true
   rm -f "$ENGINE_PID_FILE" 2>/dev/null || true
   chain_tmp_cleanup
+  # Drop this engine's host-guard registry record so a concurrent project sees
+  # the freed budget immediately (the pid sweep would catch it anyway).
+  hg_release 2>/dev/null || true
   # REL-4: release LAST so the lock covers the whole cleanup window. Owner-
   # checked no-op when this process never acquired (e.g. a refused start).
   release_engine_lock
@@ -2062,7 +2126,7 @@ Session ID: $SESSION_ID
 Iteration index: $CURRENT_ITER
 Iter name: $ITER_NAME
 Prior verdict: $PRIOR_VERDICT
-Prior depth: $PRIOR_DEPTH
+Evaluator depth recommendation for THIS iteration: $PRIOR_DEPTH — BINDING by default. Plan this depth unless one of the four escape conditions holds (prior ESCALATE/REGRESSION verdict, prior coherence FAIL, hardening cadence due, or a brand-new full-stack journey — see your agent instructions). The engine's deterministic arbiter demotes a full spec written outside those conditions to lean.
 Consecutive lean iterations dispatched: $LEAN_STREAK (hardening cadence: ${CHAIN_HARDENING_CADENCE:-6}; 0 = disabled)
 
 Project template: .claude/project-template.md
@@ -2195,14 +2259,83 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
     DEPTH="lean"
   fi
 
-  # SPEED-10 full-trigger allowlist: full depth costs ~90-120 min over lean and
-  # in practice ran on unjustified iterations (a video re-record got a 3h full
-  # pass). A full dispatch must now be JUSTIFIED by one of: prior ESCALATE/
-  # REGRESSION verdict, a prior-iteration coherence FAIL, a machine-parseable
-  # 'Full trigger:' line in the spec (the rubric's numbered trigger), or the
-  # hardening cadence being due anyway. Otherwise demote to lean (the evidence
-  # backstop below may demote further). CHAIN_DEPTH_ALLOWLIST=false disables.
-  if [[ "$DEPTH" == "full" && "${CHAIN_DEPTH_ALLOWLIST:-true}" == "true" ]]; then
+  # Target-journey parse (SPEED-20 moved this up from below the depth blocks:
+  # the arbiter's new-fullstack-journey test reads the target list, so it must
+  # be available BEFORE the depth decision).
+  TARGET_JOURNEYS=$(grep -m1 -E '^[[:space:]]*-?[[:space:]]*\*\*Target journeys:\*\*' "$ITER_SPEC_PATH" \
+                      | sed -E 's/.*\*\*Target journeys:\*\*[[:space:]]*//' || echo "")
+
+  # SPEED-20 deterministic depth arbiter: the SPEED-10 allowlist trusted the
+  # spec's own 'Full trigger:' line, and the decomposer learned to write a
+  # qualifying line into EVERY spec (desk session: full ran 5 of 6 iterations
+  # against a PRE-registered target of ≤1 in 6). The arbiter replaces that
+  # self-certification with independent machine signals, in precedence order:
+  # sanctioned fulls (prior ESCALATE/REGRESSION, prior coherence FAIL, cadence
+  # due) always run; a budget breach last iteration forces lean; at most one
+  # full per CHAIN_FULL_CADENCE_CAP window; an evaluator lean/evidence
+  # recommendation is binding unless the spec provably plans a brand-new
+  # full-stack journey. CHAIN_DEPTH_ARBITER=false restores the legacy
+  # allowlist below; iter-0 (baseline) never enters the ladder.
+  _budget_demoted=""
+  _use_legacy_allowlist=""
+  if [[ "$DEPTH" == "full" ]]; then
+    if [[ "${CHAIN_DEPTH_ARBITER:-true}" == "true" && $CURRENT_ITER -gt 0 ]]; then
+      _prev_coh_file="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/coherence.md"
+      _prev_budget_marker="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/budget-breached"
+      _arb_decision="" _arb_reason=""
+      if [[ "${PRIOR_VERDICT:-}" == "ESCALATE" || "${PRIOR_VERDICT:-}" == "REGRESSION" ]]; then
+        _arb_decision="full"; _arb_reason="prior-verdict-${PRIOR_VERDICT}"
+      elif grep -qE '^\*\*Verdict:\*\* COHERENCE-FAIL' "$_prev_coh_file" 2>/dev/null; then
+        _arb_decision="full"; _arb_reason="prior-coherence-fail"
+      elif [[ -f "$_prev_budget_marker" && "${PRIOR_VERDICT:-}" == "CONTINUE" ]]; then
+        # Last iteration blew the wall-clock budget on an ordinary CONTINUE:
+        # the recovery iteration MUST be lean (and the cadence backstop below
+        # is suppressed this pass so it cannot re-promote).
+        _arb_decision="lean"; _arb_reason="budget-breach"
+        _budget_demoted=1
+      elif goal_cadence_forces_full "$LEAN_STREAK" "$CURRENT_ITER"; then
+        _arb_decision="full"; _arb_reason="cadence-due"
+      elif goal_full_ran_in_window "$GOAL_SESSION_DIR_LOCAL" "$CURRENT_ITER"; then
+        _arb_decision="lean"; _arb_reason="full-cap"
+      elif [[ "$PRIOR_DEPTH" == "lean" || "$PRIOR_DEPTH" == "evidence" ]]; then
+        # The evaluator recommended lean/evidence. That recommendation is
+        # BINDING unless the spec provably plans a brand-new full-stack
+        # journey (Full-trigger line AND backend+frontend bullets AND real
+        # Data-contract additions AND a never-implemented target journey).
+        if grep -qiE '^[[:space:]]*-?[[:space:]]*(\*\*)?Full trigger:' "$ITER_SPEC_PATH" \
+           && goal_new_fullstack_journey "$ITER_SPEC_PATH" "$JOURNEY_HISTORY"; then
+          _arb_decision="full"; _arb_reason="new-fullstack-journey"
+        else
+          _arb_decision="lean"; _arb_reason="evaluator-requested-${PRIOR_DEPTH}"
+        fi
+      else
+        # PRIOR_DEPTH==full: the evaluator itself asked for full — fall back
+        # to the legacy SPEED-10 allowlist for the trigger check.
+        _use_legacy_allowlist=1
+      fi
+      if [[ "$_arb_decision" == "lean" ]]; then
+        echo "[run-goal] Depth arbiter: spec asked FULL but the deterministic ladder demotes it to LEAN (reason: $_arb_reason; prior verdict: ${PRIOR_VERDICT:-none}; evaluator depth recommendation: ${PRIOR_DEPTH:-none}). Set CHAIN_DEPTH_ARBITER=false to restore the legacy allowlist."
+        record_telemetry_event "depth_demoted" "$(jq -cn --arg r "$_arb_reason" --arg pv "${PRIOR_VERDICT:-}" --arg pd "${PRIOR_DEPTH:-}" '{from:"full", to:"lean", reason:$r, prior_verdict:$pv, prior_depth:$pd}' 2>/dev/null || printf '{"from":"full","to":"lean","reason":"%s"}' "$_arb_reason")"
+        DEPTH="lean"
+      elif [[ "$_arb_decision" == "full" ]]; then
+        echo "[run-goal] Depth arbiter: FULL pass granted (reason: $_arb_reason)."
+        record_telemetry_event "depth_full_granted" "$(jq -cn --arg r "$_arb_reason" --arg pv "${PRIOR_VERDICT:-}" --arg pd "${PRIOR_DEPTH:-}" '{reason:$r, prior_verdict:$pv, prior_depth:$pd}' 2>/dev/null || printf '{"reason":"%s"}' "$_arb_reason")"
+      fi
+    else
+      _use_legacy_allowlist=1
+    fi
+  fi
+
+  # SPEED-10 full-trigger allowlist (LEGACY — arbiter escape hatch + the
+  # arbiter's own PRIOR_DEPTH==full rung): full depth costs ~90-120 min over
+  # lean and in practice ran on unjustified iterations (a video re-record got
+  # a 3h full pass). A full dispatch must be JUSTIFIED by one of: prior
+  # ESCALATE/REGRESSION verdict, a prior-iteration coherence FAIL, a
+  # machine-parseable 'Full trigger:' line in the spec (the rubric's numbered
+  # trigger), or the hardening cadence being due anyway. Otherwise demote to
+  # lean (the evidence backstop below may demote further).
+  # CHAIN_DEPTH_ALLOWLIST=false disables.
+  if [[ "$DEPTH" == "full" && -n "$_use_legacy_allowlist" && "${CHAIN_DEPTH_ALLOWLIST:-true}" == "true" ]]; then
     _full_reason=""
     _prev_coh_file="$GOAL_SESSION_DIR_LOCAL/iter-$((CURRENT_ITER - 1))/coherence.md"
     if [[ "${PRIOR_VERDICT:-}" == "ESCALATE" || "${PRIOR_VERDICT:-}" == "REGRESSION" ]]; then
@@ -2223,16 +2356,15 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
 
   # SPEED-4 hardening-cadence backstop: a K-long lean streak forces a full
   # hardening pass even when the spec says lean. The spec text stays as
-  # written; dispatch + telemetry carry the effective depth.
-  if [[ "$DEPTH" == "lean" ]] && goal_cadence_forces_full "$LEAN_STREAK" "$CURRENT_ITER"; then
+  # written; dispatch + telemetry carry the effective depth. Suppressed when
+  # the arbiter's budget-breach rung demoted this very iteration (SPEED-20) —
+  # re-promoting would undo the mandated lean recovery pass.
+  if [[ "$DEPTH" == "lean" && -z "${_budget_demoted:-}" ]] && goal_cadence_forces_full "$LEAN_STREAK" "$CURRENT_ITER"; then
     echo "[run-goal] Hardening cadence: $LEAN_STREAK consecutive lean iterations — overriding spec depth lean → full (CHAIN_HARDENING_CADENCE=${CHAIN_HARDENING_CADENCE:-6}; 0 disables)."
     DEPTH="full"
     record_telemetry_event "depth_cadence_override" "$(jq -cn --arg s "$LEAN_STREAK" --arg k "${CHAIN_HARDENING_CADENCE:-6}" '{lean_streak:$s, cadence:$k}' 2>/dev/null || printf '{"lean_streak":"%s"}' "$LEAN_STREAK")"
   fi
 
-  TARGET_JOURNEYS=$(grep -m1 -E '^[[:space:]]*-?[[:space:]]*\*\*Target journeys:\*\*' "$ITER_SPEC_PATH" \
-                      | sed -E 's/.*\*\*Target journeys:\*\*[[:space:]]*//' || echo "")
-
   # SPEED-9 evidence backstop: a lean dispatch whose Target journeys are ALL
   # already recorded passing (and none pending-infra) has no build work — the
   # deliverable can only be evidence. Demote lean → evidence so developer and
@@ -2596,6 +2728,14 @@ STOP." || _eval_rc=$?
     record_telemetry_event "deterministic_gate" "$(jq -cn --arg r "$_raw_verdict" --arg f "$VERDICT" '{raw:$r, final:$f}' 2>/dev/null || printf '{"raw":"%s","final":"%s"}' "$_raw_verdict" "$VERDICT")"
   fi
 
+  # SPEED-20 rung-3 input: persist this iteration's wall-clock budget overrun
+  # as an on-disk marker the NEXT iteration's depth arbiter reads (in-process
+  # state dies with this loop pass). Written after the verdict gate so the
+  # marker always accompanies a completed evaluation.
+  if iter_budget_exceeded; then
+    printf '1' > "$ITER_DIR/budget-breached" 2>/dev/null || true
+  fi
+
   # Capture journey-history hash for stall detection
   HASH=$(journey_history_hash)
   echo "$HASH" >> "$GOAL_SESSION_DIR_LOCAL/.history-hashes"
```
