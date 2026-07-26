# Iteration diff (bounded)

Files changed: 6. Shown in full: 5.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (79 diff lines)

```diff
diff --git a/README.md b/README.md
index 07daac24..fc5f7d4a 100644
--- a/README.md
+++ b/README.md
@@ -40,6 +40,7 @@ Current capabilities:
 - **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently, and now retains the real progress the job had made — snapshots produced and trading days processed — instead of always reading zero, so a job killed partway through is never mistaken for one that did nothing. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold — staying accurate through a large job's entire final aggregate-refresh stretch, so a healthy job never falsely reads "possibly stalled" near the end — and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A completed backfill, Fetch + backfill, or rebuild job's detail also names exactly which stored aggregates that run refreshed — a **"Refreshed: ..."** line (for example "Refreshed: coverage, market phase, forward aggregates, research hot keys, drawdown expectations, index series") shown identically on the live job card, the last-run summary shown when no job has started this browser session, and that run's Run History row — confirming the background bookkeeping actually happened, not just that the job finished; the list names "drawdown expectations" whenever the run refreshed the Evidence page's historical drawdown/dry-spell figures, so those panels are ready and fast the moment anyone next opens the Evidence page; it also names "index series" whenever the run refreshed the major-indexes chart's precomputed cache, so the Dashboard's chart and this page's index-vendor panel load quickly the next time anyone opens them, instead of being recalculated from scratch; a plain fetch or an expand job now refreshes those same stored aggregates too, and the Data page's coverage numbers reflect it immediately — live in the same tab once the job finishes, and again on the next page reload — but this particular status line stays reserved for the backfill/rebuild family: it is omitted for a fetch or expand run, and for any run that hasn't finished yet. A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. A full rebuild across the platform's entire up-to-30-year, whole-symbol-universe dataset has now been live-measured end to end (a real run took about 16 minutes): memory stayed roughly 41% under the backend's configured ceiling throughout and the backend never crashed or stopped responding; the one caveat found is that the health check can occasionally take up to about 3 seconds (versus its usual under-1-second) during the busiest opening minutes of the job — every single check still succeeded, and response times settle back down for the rest of the run. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
 - **Availability heatmap on Data Manager**: a month-by-month trading-day calendar grid where each day cell is color-coded across a perceptually-ordered six-step blue density scale (dark for empty days through bright blue for fully-covered days) and ringed in violet when a scored snapshot exists for that day — two visually distinct signals that never collide in color. The legend is split into two clearly labeled groups, one for the price-data density scale and one for the scored-snapshot ring, so it is always clear which signal you are reading. Day numbers are clearly legible against every shade of cell (per-bucket design tokens chosen for contrast, no hardcoded hex). Months are ordered newest first and two months appear side by side so you see more history without scrolling. Hovering or focusing any cell shows the exact figures — date, symbols with bars versus total, and whether a snapshot exists — worded to name which action is responsible (for example, a day with price data but no snapshot yet reads as a backfill gap, while a scored day reads as a snapshot produced by backfill). Clicking a day prefills the job form's Start and End date inputs; shift-clicking a second day fills in a date range. The heatmap refreshes automatically after any data job completes or data is removed, so coverage changes are always visible immediately.
 - **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports four honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), **Snapshot pending** (a calm, steady accent-coloured state, visually distinct from both Initializing and Backend unavailable, shown when a new price bar has landed for the platform's benchmark index but hasn't yet been folded into a snapshot — it names the pending date and the recovery action, "run a backfill or rebuild on Data Manager to produce it"), or **Backend unavailable** (red, reserved for a genuinely unreachable backend or a database that has never produced a single scan) — whether the app is opened at `localhost` or the machine's local network (LAN) address. An everyday fetch for any ordinary (non-benchmark) stock never changes the badge at all, and the small "provider", "seed date", and "N symbols" badges beside the status pill refresh automatically whenever the pill's own state changes, not only once per page load. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one, and memory is bounded to one shared copy of the dataset regardless of how many people are connected at once. The Data page's coverage panel is no longer computed live at all on the common path: every fetch, backfill, Fetch + backfill, or rebuild job that actually lands new price data refreshes a stored coverage snapshot (plus market phase, the membership timeline, and research hot-key caches) the moment it finishes — a job that finds nothing new to add skips this refresh at no extra cost or delay — so a cold `/data` load now completes in well under a second — down from roughly 9-10 seconds previously — and stepping the as-of switcher to any already-ingested historical date shows that date's own correct, non-zero coverage rather than a blank panel; a genuinely brand-new, never-ingested database instead shows an honest all-zero state that fills itself in within seconds of boot, with no hang, crash, or manual step required. The start script enforces the process's configured memory ceiling and writes a permanent, append-only startup/crash log to disk (`logs/backend.log`), so a crash always leaves a readable trace even though neither the memory cap nor the log file has any on-screen representation.
+- **Background compute visibility**: a small "background compute running (N)" badge appears next to the top-bar readiness pill on every page the instant the backend starts computing evidence for a historical date that isn't ready yet, and disappears the instant it finishes — nothing to click, always live. The Data Manager page has a matching "Background compute" panel listing each currently-running window's as-of date, elapsed time, and how many calculation steps are done, plus the most recently finished window's outcome (succeeded or failed, with a reason if it failed); when nothing has run since the backend last started it shows an explicit "No background compute running. Last outcome: none yet." message instead of a blank panel, alongside a note that this history is process-lifetime only and resets on every backend restart.
 - **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale, or a live Fetch's freshly-pulled prices disagreeing with the platform's saved, committed reference history — a "live-vs-seed drift" / adjustment seam), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
 - **Contained error recovery**: if an unexpected error occurs on any page, the app shows a calm "Something went wrong on this page" message with a "Try again" button instead of going blank — the sidebar and header stay visible and usable while you retry or navigate elsewhere. In the rare case where the outer application shell itself fails, a simple fallback page appears instead of a blank browser tab.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index 137cc6a8..daff798a 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -110,16 +110,36 @@ def test_health_carries_additive_background_compute_field(loaded_engine, tmp_pat
     assert isinstance(bg["recent_outcomes"], list)
 
 
+def _background_compute_identity(status: dict) -> dict:
+    """Reduce a `background_compute` payload to the parts two back-to-back LIVE reads of the SAME
+    process-lifetime registry can be compared on without flaking (audit T1 fix): `elapsed_ms` on each
+    active entry is computed fresh at READ TIME from its own `started_at`, so it can legitimately grow
+    between two reads of a genuinely in-flight window -- it is excluded here. `recent_outcomes` is
+    reduced to its ordering/length (the identifying `(asof_key, dataset_version)` sequence), since a
+    window completing between the two reads would append a new entry -- a real state change, not a
+    flake, but also not what this test is pinning."""
+    return {
+        "active": [{k: v for k, v in entry.items() if k != "elapsed_ms"} for entry in status["active"]],
+        "recent_outcomes_order": [(o["asof_key"], o["dataset_version"]) for o in status["recent_outcomes"]],
+        "recent_outcomes_count": len(status["recent_outcomes"]),
+    }
+
+
 def test_health_background_compute_is_single_source(loaded_engine, tmp_path, monkeypatch):
-    """The served `background_compute` field equals a DIRECT `compute_readiness` call's own composed
-    value for the same session/config -- re-displayed verbatim, never re-derived by the endpoint."""
+    """The served `background_compute` field matches a DIRECT `compute_readiness` call's own composed
+    value for the same session/config -- re-displayed verbatim, never re-derived by the endpoint.
+    Compared on identity/shape (active-window keys/count, recent_outcomes ordering/length) excluding the
+    read-time-volatile `elapsed_ms` field, rather than raw equality of two live reads (closes audit T1 --
+    a false-alarm risk whenever an earlier test in the same whole-file run left a real background
+    compute in flight)."""
     monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
     cfg = load_config()
     with TestClient(main.app) as client:
         served = client.get("/api/health").json()["background_compute"]
     with Session(loaded_engine) as session:
         direct = readiness.compute_readiness(session, config=cfg)["background_compute"]
-    assert served == direct
+    assert len(served["active"]) == len(direct["active"])
+    assert _background_compute_identity(served) == _background_compute_identity(direct)
 
 
 def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
diff --git a/apps/backend/tests/test_readiness.py b/apps/backend/tests/test_readiness.py
index 3475706d..ac64458a 100644
--- a/apps/backend/tests/test_readiness.py
+++ b/apps/backend/tests/test_readiness.py
@@ -289,9 +289,25 @@ def test_compute_readiness_shape_unchanged_by_preflight_addition(loaded_engine):
 # registry's OWN bookkeeping (started_at/horizons_done/ring cap/failure path) is covered in
 # test_forward_testing_concurrency.py, the producer module's own test file.
 # ==================================================================================================
+def _background_compute_identity(status: dict) -> dict:
+    """Reduce a `background_compute` payload to the parts two back-to-back LIVE reads of the SAME
+    process-lifetime registry can be compared on without flaking (audit T1 fix): `elapsed_ms` on each
+    active entry is computed fresh at READ TIME from its own `started_at`, so it can legitimately grow
+    between two reads of a genuinely in-flight window -- it is excluded here. `recent_outcomes` is
+    reduced to its ordering/length (the identifying `(asof_key, dataset_version)` sequence)."""
+    return {
+        "active": [{k: v for k, v in entry.items() if k != "elapsed_ms"} for entry in status["active"]],
+        "recent_outcomes_order": [(o["asof_key"], o["dataset_version"]) for o in status["recent_outcomes"]],
+        "recent_outcomes_count": len(status["recent_outcomes"]),
+    }
+
+
 def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine):
     """A process that has never dispatched a historical background compute reports the honest empty
-    shape -- never omitted, never fabricated non-empty."""
+    shape -- never omitted, never fabricated non-empty. Compares two back-to-back live reads of the SAME
+    registry on identity/shape rather than raw equality, excluding the read-time-volatile `elapsed_ms`
+    field (closes audit T1 -- a false-alarm risk on any whole-file run where a background thread left by
+    an earlier test may still be in flight between the two reads below)."""
     import app.engine.forward_testing as forward_testing_module
 
     cfg = load_config()
@@ -301,9 +317,11 @@ def test_compute_readiness_composes_background_compute_empty_shape(loaded_engine
         # compute_readiness composes it VERBATIM regardless of what it currently holds.
         direct = forward_testing_module.get_background_compute_status()
         result = compute_readiness(session, config=cfg)
-    assert result["background_compute"] == direct
-    assert isinstance(result["background_compute"]["active"], list)
-    assert isinstance(result["background_compute"]["recent_outcomes"], list)
+    composed = result["background_compute"]
+    assert isinstance(composed["active"], list)
+    assert isinstance(composed["recent_outcomes"], list)
+    assert len(composed["active"]) == len(direct["active"])
+    assert _background_compute_identity(composed) == _background_compute_identity(direct)
 
 
 def test_compute_readiness_composes_background_compute_active_entry(loaded_engine, monkeypatch):
diff --git a/apps/frontend/lib/background-compute-panel-branch.test.ts b/apps/frontend/lib/background-compute-panel-branch.test.ts
new file mode 100644
index 00000000..7d73a596
--- /dev/null
+++ b/apps/frontend/lib/background-compute-panel-branch.test.ts
@@ -0,0 +1,89 @@
+/**
+ * Unit tests for the J-09 / audit-F1 `BackgroundComputePanel` branch resolver
+ * (lib/background-compute-panel-branch.ts).
+ *
+ * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
+ *   node lib/background-compute-panel-branch.test.ts
+ * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
+ * build locally — see docs/handoffs/*iter-49-dev.md; these run in the CI/QA Node environment either
+ * way, same as every other `lib/*.test.ts` file here.)
+ *
+ * TC-3 (poll-failure -> "unknown", never the idle sentence) and TC-4 (poll succeeds, zero active ->
+ * idle, unchanged) are both covered below, plus the active-window and outcome-visibility branches.
+ */
+import assert from "node:assert";
+
+import { resolveBackgroundComputePanelBranch } from "./background-compute-panel-branch.ts";
+import type { BackgroundComputeStatus } from "./api.ts";
+
+const EMPTY: BackgroundComputeStatus = { active: [], recent_outcomes: [] };
+
+const ONE_ACTIVE: BackgroundComputeStatus = {
+  active: [{
+    asof_key: "2026-07-17", dataset_version: "r1-f2", started_at: "2026-07-17T00:00:00+00:00",
+    elapsed_ms: 41800, horizons_done: 2, horizons_total: 5,
+  }],
+  recent_outcomes: [],
+};
+
+const ONE_OUTCOME: BackgroundComputeStatus = {
+  active: [],
+  recent_outcomes: [{
+    asof_key: "2026-07-17", dataset_version: "r1-f2", outcome: "completed",
+    started_at: "2026-07-17T00:00:00+00:00", finished_at: "2026-07-17T00:01:15+00:00",
+    duration_ms: 75000, reason: null,
+  }],
+};
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+// --- TC-3: poll failure / backend unreachable -> "unknown", regardless of the stale backgroundCompute
+//     value the provider may still be holding -------------------------------------------------------
+
+check("state 'unavailable' resolves to 'unknown' even when backgroundCompute is null (the provider's own catch-branch pairing)", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("unavailable", null), { kind: "unknown" });
+});
+
+check("state 'unavailable' resolves to 'unknown' even with a (stale) non-empty backgroundCompute value", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("unavailable", ONE_ACTIVE), { kind: "unknown" });
+});
+
+// --- TC-4: poll succeeds, zero active windows -> idle, unchanged from before this fix ----------------
+
+check("state 'ready' with the empty shape resolves to idle with no last outcome (TC-4, the existing idle case)", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", EMPTY), { kind: "idle", showLastOutcome: false });
+});
+
+check("state 'initializing' with the empty shape also resolves to idle (readiness state doesn't gate this)", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("initializing", EMPTY), { kind: "idle", showLastOutcome: false });
+});
+
+// --- pre-first-poll (state === null, backgroundCompute === null): unchanged prior behavior -----------
+
+check("state null (before the first poll resolves) falls through to idle, never 'unknown' (no regression)", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch(null, null), { kind: "idle", showLastOutcome: false });
+});
+
+// --- idle with a last outcome present -----------------------------------------------------------------
+
+check("zero active windows but a recorded outcome resolves to idle WITH a last outcome to show", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", ONE_OUTCOME), { kind: "idle", showLastOutcome: true });
+});
+
+// --- active window, with and without a prior outcome ---------------------------------------------------
+
+check("an active window with no prior outcome resolves to active, no last outcome", () => {
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", ONE_ACTIVE), { kind: "active", showLastOutcome: false });
+});
+
+check("an active window alongside a prior outcome resolves to active WITH a last outcome to show", () => {
+  const both: BackgroundComputeStatus = { active: ONE_ACTIVE.active, recent_outcomes: ONE_OUTCOME.recent_outcomes };
+  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", both), { kind: "active", showLastOutcome: true });
+});
+
+console.log(`${passed} passed`);
diff --git a/apps/frontend/lib/background-compute-panel-branch.ts b/apps/frontend/lib/background-compute-panel-branch.ts
new file mode 100644
index 00000000..a2cb8335
--- /dev/null
+++ b/apps/frontend/lib/background-compute-panel-branch.ts
@@ -0,0 +1,41 @@
+import type { BackgroundComputeStatus, ReadinessState } from "./api";
+
+/**
+ * ops-hardening iter-25 (J-09, audit F1 fix) — the single, pure authority for WHICH copy branch
+ * `BackgroundComputePanel` (`app/data/page.tsx`) renders. No React, no DOM types, so it is
+ * unit-testable under `node` (the existing frontend convention — see `lib/asof-step.ts`).
+ *
+ * Before this fix, the panel read only `backgroundCompute` (from `useReadiness()`) and fell through to
+ * the idle "No background compute running…" copy whenever that value was `null` — which is EXACTLY what
+ * the provider also sets on a poll failure (`readiness-provider.tsx`'s catch branch), so a genuinely
+ * unreachable backend was misreported as an honestly-idle one. This resolver reads the SAME shared
+ * `state` the provider already exposes (the poll-failure signal `HealthBadge` uses for its own
+ * "Backend unavailable" pill) to distinguish the two cases -- no second fetch, no new signal.
+ */
+export type BackgroundComputePanelBranch =
+  | { kind: "unknown" }
+  | { kind: "idle"; showLastOutcome: boolean }
+  | { kind: "active"; showLastOutcome: boolean };
+
+/**
+ * Resolve which branch the panel should render.
+ *
+ * @param state             the shared readiness state from `useReadiness()` (`null` before the first
+ *                          poll resolves, `"unavailable"` when the most recent poll failed).
+ * @param backgroundCompute the shared `background_compute` value from `useReadiness()` (`null` before
+ *                          the first poll resolves, or when the poll failed).
+ */
+export function resolveBackgroundComputePanelBranch(
+  state: ReadinessState | null,
+  backgroundCompute: BackgroundComputeStatus | null,
+): BackgroundComputePanelBranch {
+  // The poll-failure signal: `state === "unavailable"` — the SAME condition `HealthBadge` already
+  // renders "Backend unavailable" for. Never confused with the pre-first-poll `state === null` moment
+  // (that one still falls through to the idle branch below, unchanged from before this fix).
+  if (state === "unavailable") return { kind: "unknown" };
+
+  const active = backgroundCompute?.active ?? [];
+  const recentOutcomes = backgroundCompute?.recent_outcomes ?? [];
+  const showLastOutcome = recentOutcomes.length > 0;
+  return active.length === 0 ? { kind: "idle", showLastOutcome } : { kind: "active", showLastOutcome };
+}
```
