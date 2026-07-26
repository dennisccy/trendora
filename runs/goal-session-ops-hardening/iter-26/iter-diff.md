# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (31 diff lines)

```diff
diff --git a/README.md b/README.md
index fc5f7d4a..24391f65 100644
--- a/README.md
+++ b/README.md
@@ -40,7 +40,7 @@ Current capabilities:
 - **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently, and now retains the real progress the job had made — snapshots produced and trading days processed — instead of always reading zero, so a job killed partway through is never mistaken for one that did nothing. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold — staying accurate through a large job's entire final aggregate-refresh stretch, so a healthy job never falsely reads "possibly stalled" near the end — and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A completed backfill, Fetch + backfill, or rebuild job's detail also names exactly which stored aggregates that run refreshed — a **"Refreshed: ..."** line (for example "Refreshed: coverage, market phase, forward aggregates, research hot keys, drawdown expectations, index series") shown identically on the live job card, the last-run summary shown when no job has started this browser session, and that run's Run History row — confirming the background bookkeeping actually happened, not just that the job finished; the list names "drawdown expectations" whenever the run refreshed the Evidence page's historical drawdown/dry-spell figures, so those panels are ready and fast the moment anyone next opens the Evidence page; it also names "index series" whenever the run refreshed the major-indexes chart's precomputed cache, so the Dashboard's chart and this page's index-vendor panel load quickly the next time anyone opens them, instead of being recalculated from scratch; a plain fetch or an expand job now refreshes those same stored aggregates too, and the Data page's coverage numbers reflect it immediately — live in the same tab once the job finishes, and again on the next page reload — but this particular status line stays reserved for the backfill/rebuild family: it is omitted for a fetch or expand run, and for any run that hasn't finished yet. A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. A full rebuild across the platform's entire up-to-30-year, whole-symbol-universe dataset has now been live-measured end to end (a real run took about 16 minutes): memory stayed roughly 41% under the backend's configured ceiling throughout and the backend never crashed or stopped responding; the one caveat found is that the health check can occasionally take up to about 3 seconds (versus its usual under-1-second) during the busiest opening minutes of the job — every single check still succeeded, and response times settle back down for the rest of the run. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
 - **Availability heatmap on Data Manager**: a month-by-month trading-day calendar grid where each day cell is color-coded across a perceptually-ordered six-step blue density scale (dark for empty days through bright blue for fully-covered days) and ringed in violet when a scored snapshot exists for that day — two visually distinct signals that never collide in color. The legend is split into two clearly labeled groups, one for the price-data density scale and one for the scored-snapshot ring, so it is always clear which signal you are reading. Day numbers are clearly legible against every shade of cell (per-bucket design tokens chosen for contrast, no hardcoded hex). Months are ordered newest first and two months appear side by side so you see more history without scrolling. Hovering or focusing any cell shows the exact figures — date, symbols with bars versus total, and whether a snapshot exists — worded to name which action is responsible (for example, a day with price data but no snapshot yet reads as a backfill gap, while a scored day reads as a snapshot produced by backfill). Clicking a day prefills the job form's Start and End date inputs; shift-clicking a second day fills in a date range. The heatmap refreshes automatically after any data job completes or data is removed, so coverage changes are always visible immediately.
 - **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports four honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), **Snapshot pending** (a calm, steady accent-coloured state, visually distinct from both Initializing and Backend unavailable, shown when a new price bar has landed for the platform's benchmark index but hasn't yet been folded into a snapshot — it names the pending date and the recovery action, "run a backfill or rebuild on Data Manager to produce it"), or **Backend unavailable** (red, reserved for a genuinely unreachable backend or a database that has never produced a single scan) — whether the app is opened at `localhost` or the machine's local network (LAN) address. An everyday fetch for any ordinary (non-benchmark) stock never changes the badge at all, and the small "provider", "seed date", and "N symbols" badges beside the status pill refresh automatically whenever the pill's own state changes, not only once per page load. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one, and memory is bounded to one shared copy of the dataset regardless of how many people are connected at once. The Data page's coverage panel is no longer computed live at all on the common path: every fetch, backfill, Fetch + backfill, or rebuild job that actually lands new price data refreshes a stored coverage snapshot (plus market phase, the membership timeline, and research hot-key caches) the moment it finishes — a job that finds nothing new to add skips this refresh at no extra cost or delay — so a cold `/data` load now completes in well under a second — down from roughly 9-10 seconds previously — and stepping the as-of switcher to any already-ingested historical date shows that date's own correct, non-zero coverage rather than a blank panel; a genuinely brand-new, never-ingested database instead shows an honest all-zero state that fills itself in within seconds of boot, with no hang, crash, or manual step required. The start script enforces the process's configured memory ceiling and writes a permanent, append-only startup/crash log to disk (`logs/backend.log`), so a crash always leaves a readable trace even though neither the memory cap nor the log file has any on-screen representation.
-- **Background compute visibility**: a small "background compute running (N)" badge appears next to the top-bar readiness pill on every page the instant the backend starts computing evidence for a historical date that isn't ready yet, and disappears the instant it finishes — nothing to click, always live. The Data Manager page has a matching "Background compute" panel listing each currently-running window's as-of date, elapsed time, and how many calculation steps are done, plus the most recently finished window's outcome (succeeded or failed, with a reason if it failed); when nothing has run since the backend last started it shows an explicit "No background compute running. Last outcome: none yet." message instead of a blank panel, alongside a note that this history is process-lifetime only and resets on every backend restart.
+- **Background compute visibility**: a small "background compute running (N)" badge appears next to the top-bar readiness pill on every page the instant the backend starts computing evidence for a historical date that isn't ready yet, and disappears the instant it finishes — nothing to click, always live. The Data Manager page has a matching "Background compute" panel listing each currently-running window's as-of date, elapsed time, and how many calculation steps are done, plus the most recently finished window's outcome (succeeded or failed, with a reason if it failed); when nothing has run since the backend last started it shows an explicit "No background compute running. Last outcome: none yet." message instead of a blank panel, alongside a note that this history is process-lifetime only and resets on every backend restart. If the panel's own check-in with the backend fails, it now honestly shows "state unknown — the backend is unreachable" instead of quietly falling back to the calm idle message, so a real connectivity problem is never mistaken for "nothing is running."
 - **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale, or a live Fetch's freshly-pulled prices disagreeing with the platform's saved, committed reference history — a "live-vs-seed drift" / adjustment seam), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
 - **Contained error recovery**: if an unexpected error occurs on any page, the app shows a calm "Something went wrong on this page" message with a "Try again" button instead of going blank — the sidebar and header stay visible and usable while you retry or navigate elsewhere. In the rare case where the outer application shell itself fails, a simple fallback page appears instead of a blank browser tab.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/tests/test_health.py b/apps/backend/tests/test_health.py
index daff798a..b26fdda5 100644
--- a/apps/backend/tests/test_health.py
+++ b/apps/backend/tests/test_health.py
@@ -142,6 +142,36 @@ def test_health_background_compute_is_single_source(loaded_engine, tmp_path, mon
     assert _background_compute_identity(served) == _background_compute_identity(direct)
 
 
+def test_health_background_compute_serves_failed_outcome_verbatim(loaded_engine, tmp_path, monkeypatch):
+    """goal-ops-hardening iter-26 (J-09 confirm-gap 2): a crafted `failed` outcome -- the branch every
+    captured panel state to date has never exercised -- is composed and served VERBATIM, field-for-field,
+    never dropped/re-derived/silently swallowed. Monkeypatches the ONE producer accessor
+    (`app.engine.forward_testing.get_background_compute_status`) rather than a byte-frozen module's
+    internals -- `compute_readiness`/`app/api/health.py` themselves are untouched by this iteration."""
+    import app.engine.forward_testing as forward_testing_module
+
+    monkeypatch.setenv(readiness.VERDICT_HISTORY_PATH_ENV, str(tmp_path / "history.jsonl"))
+    crafted = {
+        "active": [],
+        "recent_outcomes": [{
+            "asof_key": "2026-01-04",
+            "dataset_version": "r1-f2",
+            "outcome": "failed",
+            "started_at": "2026-01-04T00:00:00+00:00",
+            "finished_at": "2026-01-04T00:00:05+00:00",
+            "duration_ms": 5000,
+            "reason": "forced test failure — simulated dispatch error",
+        }],
+    }
+    monkeypatch.setattr(forward_testing_module, "get_background_compute_status", lambda: crafted)
+    with TestClient(main.app) as client:
+        body = client.get("/api/health").json()
+    served = body["background_compute"]["recent_outcomes"][0]
+    assert served == crafted["recent_outcomes"][0]
+    assert served["outcome"] == "failed"
+    assert served["reason"] == "forced test failure — simulated dispatch error"
+
+
 def test_health_background_compute_degrades_honestly_when_readiness_fails(loaded_engine, monkeypatch):
     """A total `compute_readiness` failure degrades the WHOLE readiness payload to `unavailable` (the
     pre-existing convention) -- `background_compute` still serves the honest empty shape, never omitted
diff --git a/apps/frontend/lib/background-compute-last-outcome.test.ts b/apps/frontend/lib/background-compute-last-outcome.test.ts
new file mode 100644
index 00000000..aa1c70fc
--- /dev/null
+++ b/apps/frontend/lib/background-compute-last-outcome.test.ts
@@ -0,0 +1,57 @@
+/**
+ * Unit tests for the J-09 goal-ops-hardening iter-26 `LastOutcomeSummary` render-decision extraction
+ * (lib/background-compute-last-outcome.ts).
+ *
+ * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
+ *   node lib/background-compute-last-outcome.test.ts
+ * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
+ * build locally — see docs/handoffs/*iter-49-dev.md; these run in the CI/QA Node environment either
+ * way, same as every other `lib/*.test.ts` file here.)
+ *
+ * TC-5: `completed` (reason: null) -> { reasonText: null, badgeVariant: "ok" }; `failed` (reason: <str>)
+ * -> { reasonText: <that exact string>, badgeVariant: "danger" }.
+ */
+import assert from "node:assert";
+
+import { resolveLastOutcomeSummary } from "./background-compute-last-outcome.ts";
+import type { BackgroundComputeOutcome } from "./api.ts";
+
+const COMPLETED: BackgroundComputeOutcome = {
+  asof_key: "2026-07-17",
+  dataset_version: "r1-f2",
+  outcome: "completed",
+  started_at: "2026-07-17T00:00:00+00:00",
+  finished_at: "2026-07-17T00:01:15+00:00",
+  duration_ms: 75000,
+  reason: null,
+};
+
+const FAILED: BackgroundComputeOutcome = {
+  asof_key: "2026-01-04",
+  dataset_version: "r1-f2",
+  outcome: "failed",
+  started_at: "2026-01-04T00:00:00+00:00",
+  finished_at: "2026-01-04T00:00:05+00:00",
+  duration_ms: 5000,
+  reason: "forced test failure — simulated dispatch error",
+};
+
+let passed = 0;
+function check(name: string, fn: () => void) {
+  fn();
+  passed += 1;
+  console.log(`  ok - ${name}`);
+}
+
+check("a completed outcome resolves to reasonText null and badgeVariant ok (TC-5, existing case)", () => {
+  assert.deepStrictEqual(resolveLastOutcomeSummary(COMPLETED), { reasonText: null, badgeVariant: "ok" });
+});
+
+check("a failed outcome resolves to reasonText equal to the exact reason string and badgeVariant danger (TC-5)", () => {
+  assert.deepStrictEqual(resolveLastOutcomeSummary(FAILED), {
+    reasonText: "forced test failure — simulated dispatch error",
+    badgeVariant: "danger",
+  });
+});
+
+console.log(`${passed} passed`);
diff --git a/apps/frontend/lib/background-compute-last-outcome.ts b/apps/frontend/lib/background-compute-last-outcome.ts
new file mode 100644
index 00000000..ca9ec2ee
--- /dev/null
+++ b/apps/frontend/lib/background-compute-last-outcome.ts
@@ -0,0 +1,28 @@
+import type { BackgroundComputeOutcome } from "./api";
+
+/**
+ * goal-ops-hardening iter-26 (J-09 confirm-gap 2) — the single, pure authority for HOW
+ * `LastOutcomeSummary` (`app/data/page.tsx`) renders a completed/failed background-compute outcome. No
+ * React, no DOM types, so it is unit-testable under `node` (the existing frontend convention — see
+ * `lib/background-compute-panel-branch.ts`).
+ *
+ * Pure extraction of the decision that was previously inline in `LastOutcomeSummary` — refactor only,
+ * no behavior change. The `completed` case renders byte-identically (badge `"ok"`, no reason line); the
+ * `failed` case (never exercised by a captured panel state before this iteration) now has direct,
+ * citable test coverage of exactly what it produces.
+ */
+export interface LastOutcomeSummary {
+  /** The failure reason to render, or `null` when there is none (the `completed` case). */
+  reasonText: string | null;
+  /** The badge variant `LastOutcomeSummary` passes straight to `<Badge variant=...>`. */
+  badgeVariant: "ok" | "danger";
+}
+
+/** Resolve how a single `background_compute.recent_outcomes[0]` entry should render. */
+export function resolveLastOutcomeSummary(outcome: BackgroundComputeOutcome): LastOutcomeSummary {
+  const failed = outcome.outcome === "failed";
+  return {
+    reasonText: failed ? outcome.reason : null,
+    badgeVariant: failed ? "danger" : "ok",
+  };
+}
```
