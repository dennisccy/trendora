# Iteration diff (bounded)

Files changed: 12. Shown in full: 10.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/referee_audit.py` (84 lines not shown)
- `apps/backend/tests/test_referee_audit.py` (245 lines not shown)

```diff
diff --git a/README.md b/README.md
index 855e3e6..6371614 100644
--- a/README.md
+++ b/README.md
@@ -35,10 +35,10 @@ Current capabilities:
 - **Certification-budget accounting**: a third card, alongside Pre-registration registry and Negative-results graveyard, in the Research hub's "Governance & process" section (completing that section's three-card grid) opens a dedicated `/research/budget` page that shows, before any new scan is proposed, exactly how much of the platform's statistical credibility budget has already been spent. Four cards report: the total number of canonical trials run to date (currently 7) and the trial number that comes next (#8); the exact significance bar the next canonical trial must clear — shown both as a number (currently 0.00625) and as its Bonferroni formula (0.05 ÷ the trial number), so the growth of the multiple-testing divisor is visible, not just its result; how much of the reusable-holdout (Thresholdout) alpha budget remains before a new scan can be proposed (currently 90% remaining); and an internal staging exploration economy's next-trial significance level and trial number — an internal budget that was never surfaced anywhere in the product before now. Each card carries a small inline trend sparkline showing how that figure has moved trial by trial, re-read verbatim from the recorded ledger history rather than freshly recomputed. A loading state shows four pulsing placeholder cards while data loads; if the backend is unreachable a single contained error card appears with the "Back to Research" link still usable; if the underlying ledgers were ever empty the same four cards would render honest zero/starting values rather than an error or blank state.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
-- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
+- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
 - **Availability heatmap on Data Manager**: a month-by-month trading-day calendar grid where each day cell is color-coded across a perceptually-ordered six-step blue density scale (dark for empty days through bright blue for fully-covered days) and ringed in violet when a scored snapshot exists for that day — two visually distinct signals that never collide in color. The legend is split into two clearly labeled groups, one for the price-data density scale and one for the scored-snapshot ring, so it is always clear which signal you are reading. Day numbers are clearly legible against every shade of cell (per-bucket design tokens chosen for contrast, no hardcoded hex). Months are ordered newest first and two months appear side by side so you see more history without scrolling. Hovering or focusing any cell shows the exact figures — date, symbols with bars versus total, and whether a snapshot exists — worded to name which action is responsible (for example, a day with price data but no snapshot yet reads as a backfill gap, while a scored day reads as a snapshot produced by backfill). Clicking a day prefills the job form's Start and End date inputs; shift-clicking a second day fills in a date range. The heatmap refreshes automatically after any data job completes or data is removed, so coverage changes are always visible immediately.
 - **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports three honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), or **Backend unavailable** (red) — whether the app is opened at `localhost` or the machine's local network (LAN) address. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one; memory is bounded to one shared copy of the dataset regardless of how many people are connected at once; opening the Data Manager page for the first time after a restart, or several people opening it at once, now reliably finishes loading in roughly 10-20 seconds instead of risking a memory-exhaustion hang, because its price-history load streams data in smaller chunks rather than reading everything at once; and the start script enforces hard limits on concurrent connections, request timeouts, and process memory so that a traffic spike isolates to one process without freezing the host machine.
-- **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
+- **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale, or a live Fetch's freshly-pulled prices disagreeing with the platform's saved, committed reference history — a "live-vs-seed drift" / adjustment seam), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
 - **Contained error recovery**: if an unexpected error occurs on any page, the app shows a calm "Something went wrong on this page" message with a "Try again" button instead of going blank — the sidebar and header stay visible and usable while you retry or navigate elsewhere. In the rare case where the outer application shell itself fails, a simple fallback page appears instead of a blank browser tab.
 <!-- /AUTO:capabilities -->
 
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 5c717cd..2cef887 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1294,6 +1294,11 @@ class ResearchCfg(BaseModel):
     severity_velocity: "SeverityVelocityCfg" = Field(
         default_factory=lambda: _default_severity_velocity()
     )
+    # iter-36 (J-22) — the referee-calibration harness tunables (backlog B-102). Defaulted so a config /
+    # inline test fixture predating this block still loads unchanged — the harness runs ONLY when
+    # explicitly invoked (`python -m app.engine.referee_audit`), so adding this block alone changes no
+    # runtime behavior.
+    referee_audit: "RefereeAuditCfg" = Field(default_factory=lambda: _default_referee_audit())
 
     @model_validator(mode="after")
     def _validate(self) -> "ResearchCfg":
@@ -1345,6 +1350,63 @@ def _default_severity_velocity() -> "SeverityVelocityCfg":
     )
 
 
+_DEFAULT_REFEREE_AUDIT_REPORT_PATH = "runs/goal-session-mcp-loop/state/referee-audit-report.json"
+# Mirrors `referee.DEFAULT_SEED` — a deterministic default so a fresh config still reproduces the same
+# calibration run byte-for-byte without an explicit override.
+_DEFAULT_REFEREE_AUDIT_SEED = 20240601
+_DEFAULT_CONTAMINATED_FACTOR_HORIZON = 5
+
+
+class RefereeAuditCfg(BaseModel):
+    """Referee-calibration harness tunables (goal-mcp-loop iter-36, J-22 / backlog B-102).
+    `app.engine.referee_audit` reads every tunable from here — no magic number in the module (anti-goal:
+    No magic numbers).
+
+      - `n_null_trials` — how many seeded null (per-date label-permuted) certifications the harness runs
+        to measure the empirical false-pass rate. 200 for the real offline artifact; a test/CI fixture
+        overrides this down to ~20 via an explicit `cfg` override passed to `run_referee_audit`, NEVER by
+        editing this committed default.
+      - `seed` — the harness's own deterministic seed. Every null trial's permutation + bootstrap draw
+        derives from `seed + trial_ordinal`, so the SAME seed reproduces the SAME false-pass rate
+        byte-identically (mirrors `referee.DEFAULT_SEED`'s role for the harness itself).
+      - `contaminated_factor_horizon` — the forward-return horizon the lookahead-contaminated factor's
+        "value equals its own realized forward return" construction uses, both to rank the per-date
+        top-decile cohort and as the horizon `certify_edge` purges/embargoes against.
+      - `report_path` — the persisted audit-report artifact location. Resolved relative to `REPO_ROOT`
+        when relative; the resolver (`app.engine.referee_audit.resolve_referee_audit_path`, NOT this
+        model) applies the runtime `TRENDORA_REFEREE_AUDIT_PATH` override, mirroring
+        `DriftCfg.report_path` / `resolve_drift_report_path()` exactly.
+
+    Boot-validated: `n_null_trials >= 1`, `contaminated_factor_horizon >= 1`. Default-populated so a
+    config / inline test fixture predating this block still loads unchanged — the harness runs ONLY when
+    explicitly invoked (job-style; adding this block alone changes no runtime behavior, since nothing
+    calls `run_referee_audit` automatically)."""
+
+    model_config = ConfigDict(extra="allow")
+    n_null_trials: int = 200
+    seed: int = _DEFAULT_REFEREE_AUDIT_SEED
+    contaminated_factor_horizon: int = _DEFAULT_CONTAMINATED_FACTOR_HORIZON
+    report_path: str = Field(default=_DEFAULT_REFEREE_AUDIT_REPORT_PATH, min_length=1)
+
+    @model_validator(mode="after")
+    def _validate(self) -> "RefereeAuditCfg":
+        if self.n_null_trials < 1:
+            raise ValueError(f"research.referee_audit.n_null_trials must be >= 1, got {self.n_null_trials}")
+        if self.contaminated_factor_horizon < 1:
+            raise ValueError(
+                "research.referee_audit.contaminated_factor_horizon must be >= 1, got "
+                f"{self.contaminated_factor_horizon}"
+            )
+        return self
+
+
+def _default_referee_audit() -> "RefereeAuditCfg":
+    """The built-in default referee-audit config — used when a config predating the block (or an inline
+    test fixture) omits `research.referee_audit`. The real `config.yaml` restates it explicitly as the
+    single documented source."""
+    return RefereeAuditCfg()
+
+
 # iter-29 (J-87 / J-88) — the named severity-component weight set. The deterministic drawdown-severity
 # score blends EXACTLY these five named components, so `config.market_phase.weights` MUST cover this
 # set (completeness) and sum ~1.0 (mirroring `regime.weights` / `scores.<block>.weights`). Each weight
diff --git a/apps/backend/main.py b/apps/backend/main.py
index bce536f..c0bb531 100644
--- a/apps/backend/main.py
+++ b/apps/backend/main.py
@@ -26,6 +26,7 @@ from app.api import (
     indexes,
     market_phase,
     methodology,
+    referee_audit,
     regime_history,
     registry,
     research,
@@ -140,6 +141,9 @@ def create_app() -> FastAPI:
     # goal-mcp-loop iter-32 (J-17) — the read-only certification-budget accounting panel
     # (GET /api/research/budget).
     application.include_router(budget.router, prefix="/api")
+    # goal-mcp-loop iter-36 (J-22) — the read-only referee-calibration report
+    # (GET /api/research/referee-audit).
+    application.include_router(referee_audit.router, prefix="/api")
     return application
 
 
diff --git a/apps/frontend/app/research/page.tsx b/apps/frontend/app/research/page.tsx
index 3917a37..c7d2500 100644
--- a/apps/frontend/app/research/page.tsx
+++ b/apps/frontend/app/research/page.tsx
@@ -11,6 +11,7 @@ import {
   Layers,
   LineChart,
   Microscope,
+  ShieldCheck,
   Thermometer,
   TrendingDown,
   TrendingUp,
@@ -77,10 +78,11 @@ export default function ResearchHubPage() {
         })}
       </div>
 
-      {/* goal-mcp-loop iter-30 (J-18) / iter-31 (J-19) / iter-32 (J-17) — Governance & process:
-          registry + graveyard + budget now; referee-audit still to follow. Kept a SEPARATE section,
-          not an 11th RESEARCH_LABS entry — that array's reading order is a J-113 contract over the ten
-          analytical labs; a governance/process link is architecturally distinct, not a lab. */}
+      {/* goal-mcp-loop iter-30 (J-18) / iter-31 (J-19) / iter-32 (J-17) / iter-36 (J-22) — Governance &
+          process: registry + graveyard + budget + referee-audit — the cluster is now complete (4/4).
+          Kept a SEPARATE section, not an 11th RESEARCH_LABS entry — that array's reading order is a
+          J-113 contract over the ten analytical labs; a governance/process link is architecturally
+          distinct, not a lab. */}
       <div className="space-y-3">
         <h2 className="text-sm font-semibold uppercase tracking-wide text-text-faint">Governance &amp; process</h2>
         <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="research-governance">
@@ -148,6 +150,30 @@ export default function ResearchHubPage() {
               staging LORD++ wealth — each over time, re-read from the same referee/ledger accounting.
             </p>
           </Link>
+
+          {/* goal-mcp-loop iter-36 (J-22) — the referee-calibration report: the certifier's own measured
+              false-pass rate against α over seeded null factors, plus the lookahead-contaminated-factor
+              tripwire — computed once by an isolated offline job, never the real certification economy. */}
+          <Link
+            href={asofHref("/research/referee-audit")}
+            data-testid="research-governance-link-referee-audit"
+            className={cn(
+              "group flex flex-col gap-2 rounded-lg border border-border bg-surface p-4 transition-colors",
+              "hover:border-accent hover:bg-surface-2",
+              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
+            )}
+          >
+            <div className="flex items-center gap-2">
+              <ShieldCheck className="h-5 w-5 text-accent" aria-hidden />
+              <h3 className="text-base font-semibold text-text">Referee audit</h3>
+              <ArrowRight className="ml-auto h-4 w-4 text-text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
+            </div>
+            <p className="text-sm text-text-muted">
+              Is the certifier itself calibrated? The measured false-pass rate over seeded null factors
+              against α, plus a lookahead-contaminated-factor tripwire — computed once by an isolated
+              offline job against a throwaway ledger.
+            </p>
+          </Link>
         </div>
       </div>
     </div>
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 8a3d796..9597b21 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -14,6 +14,11 @@ import type {
 } from "@/lib/evidence";
 import type { GraveyardEntry, GraveyardResponse, RevisitProtocol } from "@/lib/graveyard";
 import type { PreRegistrationRow, RegistryResponse } from "@/lib/registry";
+import type {
+  RefereeAuditContaminatedVerdict,
+  RefereeAuditReport,
+  RefereeAuditResponse,
+} from "@/lib/referee-audit";
 
 // Re-export the read-side evidence types (goal-mcp-loop iter-1) so callers import them from the API client
 // alongside `fetchEvidence`. These are DISTINCT from `EvidenceAggregate` below (the Backtest forward-tested
@@ -29,6 +34,9 @@ export type { GraveyardEntry, GraveyardResponse, RevisitProtocol };
 // Re-export the certification-budget accounting types (goal-mcp-loop iter-32, J-17) alongside `fetchBudget`.
 export type { BudgetResponse, BudgetSpendPoint, CanonicalBudget, StagingBudget };
 
+// Re-export the referee-calibration report types (goal-mcp-loop iter-36, J-22) alongside `fetchRefereeAudit`.
+export type { RefereeAuditContaminatedVerdict, RefereeAuditReport, RefereeAuditResponse };
+
 /** The build-time configured backend base (`NEXT_PUBLIC_API_URL`, default localhost). The configured
  *  backend PORT (`NEXT_PUBLIC_API_PORT`) is read alongside so the runtime resolver can host-swap to the
  *  page's own host when the page is opened at a non-localhost (LAN-IP) origin (J-108). Both are inlined
@@ -417,6 +425,16 @@ export async function fetchBudget(signal?: AbortSignal): Promise<BudgetResponse>
   return getJSON<BudgetResponse>("/api/research/budget", signal);
 }
 
+// --- referee-calibration report (goal-mcp-loop iter-36, J-22 / backlog B-102) ---------------
+/** GET /api/research/referee-audit — the read-only referee-calibration report: the empirical false-pass
+ *  rate + binomial CI over seeded null factors, the configured α, and the lookahead-contaminated-factor
+ *  verdict (labeled "expected: rejected") — re-read VERBATIM from the persisted offline-audit artifact
+ *  (`report: null` when the harness has never run). Introduces no proven-language. Throws on network
+ *  error or non-200 so the page renders an explicit "Backend unavailable" state. */
+export async function fetchRefereeAudit(signal?: AbortSignal): Promise<RefereeAuditResponse> {
+  return getJSON<RefereeAuditResponse>("/api/research/referee-audit", signal);
+}
+
 // --- stock price/MA/volume series for the detail chart (iter-4) -----------------------------
 /** One ascending OHLCV bar. By default date <= as-of (no lookahead — the backend reads only
  *  `bars_asof`). With the J-20 `through=latest` opt-in the series extends through the latest seed bar
diff --git a/config.yaml b/config.yaml
index 029a421..2e093ed 100644
--- a/config.yaml
+++ b/config.yaml
@@ -960,6 +960,16 @@ research:
       - { key: rising,  label: "Rising stress (velocity > 0)" }
       - { key: flat,    label: "Flat (velocity = 0)" }
       - { key: falling, label: "Falling stress (velocity < 0)" }
+  # iter-36 CONSUMED — the referee-calibration harness (J-22 / backlog B-102). Every tunable
+  # app.engine.referee_audit reads lives here (anti-goal: No magic numbers). `n_null_trials` is the real
+  # offline-run count (200); a test/CI fixture overrides this down to ~20 via an explicit cfg override,
+  # NEVER by editing this committed default. The harness runs ONLY when explicitly invoked
+  # (`python -m app.engine.referee_audit`) — this block alone changes no runtime behavior.
+  referee_audit:
+    n_null_trials: 200
+    seed: 20240601
+    contaminated_factor_horizon: 5
+    report_path: runs/goal-session-mcp-loop/state/referee-audit-report.json
 
 # ----------------------------------------------------------------------------------------
 # iter-29 CONSUMED — Market Phase & drawdown-Severity layer (J-87). The read-only derivation
diff --git a/apps/backend/app/api/referee_audit.py b/apps/backend/app/api/referee_audit.py
new file mode 100644
index 0000000..b83fbdf
--- /dev/null
+++ b/apps/backend/app/api/referee_audit.py
@@ -0,0 +1,31 @@
+"""GET /api/research/referee-audit — the read-only referee-calibration report (goal-mcp-loop iter-36,
+J-22 / backlog B-102).
+
+Serves `app.engine.referee_audit.read_referee_audit_report` verbatim (re-format only — no recompute): the
+null-trial count, the empirical false-pass rate + binomial CI, the configured α, the lookahead-
+contaminated-factor verdict (labeled "expected: rejected"), the run date, and the run parameters — all
+re-read from the persisted artifact the offline harness job (`python -m app.engine.referee_audit`) wrote.
+
+No DB/session is needed (the artifact is a state file, not the snapshot DB). The artifact path is
+config/env-driven via the existing resolver (anti-goal: No magic numbers — no path literal here). A
+missing artifact (the harness has never run) returns 200 with an honest `null` `report`, never a 500
+(anti-goal: resilience to data-shape change).
+
+READ-ONLY, always: no proven-language — this endpoint audits the certifier, it certifies nothing. It never
+touches `app.engine.evidence` / `GET /api/evidence`, the real ledgers, or the real Thresholdout budget.
+"""
+from __future__ import annotations
+
+from fastapi import APIRouter
+
+from app.engine.referee_audit import read_referee_audit_report
+
+router = APIRouter(tags=["referee-audit"])
+
+
+@router.get("/research/referee-audit")
+def get_referee_audit() -> dict:
+    """The referee-calibration report, verbatim: `{"report": {...} | None}`. READ-ONLY — recomputes
+    nothing; a missing artifact (the offline harness has never run) yields `{"report": None}` (200, never
+    500), the honest empty state the panel renders as "no audit run yet"."""
+    return {"report": read_referee_audit_report()}
diff --git a/apps/backend/app/engine/referee_audit.py b/apps/backend/app/engine/referee_audit.py
new file mode 100644
index 0000000..52ece45
--- /dev/null
+++ b/apps/backend/app/engine/referee_audit.py
@@ -0,0 +1,478 @@
+"""The **referee-calibration harness** — placebo + lookahead-tripwire audit of the certifier itself
+(goal-mcp-loop iter-36, J-22 / backlog B-102).
+
+`app.engine.referee` (`certify_edge`) has never been negatively controlled: it stamps "PASS"/"FAIL" but
+nobody has measured whether its own false-pass rate matches the α it claims to enforce. This module is
+that calibration battery:
+
+  1. **Seeded null factors** — `permute_null_observations` takes a REAL factor's per-date cross-section
+     (a real cohort/control observation pair from an existing Research-lab claim) and, independently for
+     each of `n_null_trials`, randomly reassigns which observed VALUES belong to "cohort" vs "control" on
+     each date. This preserves the EXACT multiset of realized returns observed (the distribution is
+     untouched) while destroying any true relationship between group membership and outcome — the
+     textbook permutation-test null. Each permuted pair is certified through the SAME PURE
+     `referee.certify_edge` used everywhere else; since there is by construction no real signal left, a
+     well-calibrated referee should PASS roughly a fraction α of these (never more) — the "empirical
+     false-pass rate" the report discloses.
+  2. **One lookahead-contaminated factor** — a "factor" whose value literally equals the stock's own
+     realized forward return at `contaminated_factor_horizon` (the "perfect crime" a broken harness would
+     certify instantly, since ranking BY the very quantity being evaluated guarantees an enormous
+     apparent edge). The referee's sealed-holdout machinery has no way to detect this class of
+     contamination (it is baked into the OBSERVATIONS themselves, not a temporal boundary leak), so
+     either the referee legitimately REJECTS it (an honest, welcome outcome) or it PASSES — in which case
+     the report's `contaminated_caught` flag is False and the panel must render a LOUD, un-hideable
+     tripwire failure state. Both outcomes are honest; only HIDING a PASS would be dishonest.
+
+ISOLATION (the dominant failure mode — B-102's own naming): every certification this module runs — every
+null trial AND the one contaminated trial — uses a FRESH `RefereeState(n_trials=1, ...)` (never derived
+from any ledger's accumulated count) and writes ONLY to an explicit, caller-supplied THROWAWAY
+`ledger_path` via the ordinary `app.engine.ledger.append_entry` seam. It NEVER opens, reads, or writes the
+real `certified-claims.jsonl`, `staging-ledger.jsonl`, or the real Thresholdout budget — there is no code
+path in this module that can reach those files. `run_referee_audit` also NEVER writes anything to the
+`certified-claims.jsonl`/`staging-ledger.jsonl` writer (`app.mcp.tools.verify_edge`); it calls
+`referee.certify_edge` directly.
+
+DB-FREE WHEN INJECTED (mirrors `app.engine.forward_walk`'s `Assembler` idiom exactly): `run_referee_audit`
+accepts injectable `assemble_source` / `assemble_contaminated` callables. Omit them (the production call
+shape used by `_main`, the offline job) and this module lazily imports `app.mcp.tools.assemble_claim_
+observations` plus the stored `forward_returns` table to pull REAL data — `session` is required only
+then. Inject synthetic ones (as every test here does) and NO database is ever touched, exactly like
+`tests/test_referee.py` / `tests/test_forward_walk.py`'s established pattern — this is what makes the CI
+variant fast and seed-independent of the 30-year committed seed.
+
+Persistence mirrors `app.engine.drift` exactly: `resolve_referee_audit_path()` (env override, else
+config, resolved against `REPO_ROOT`), `write_referee_audit_report()` (temp-file-then-rename), and
+`read_referee_audit_report()` (missing artifact -> `None`; unparseable -> an honest `status: "unreadable"`
+dict — NEVER a raise).
+
+Run the real offline job::
+
+    python -m app.engine.referee_audit
+
+(200 null trials by default via `config.research.referee_audit.n_null_trials`; persists the artifact at
+the configured `report_path`.)
+"""
+from __future__ import annotations
+
+import json
+import math
+import os
+from pathlib import Path
+from typing import Callable, Optional
+
+import numpy as np
+
+from app.config import REPO_ROOT, get_config
+from app.engine import ledger as ledger_mod
+from app.engine.referee import (
+    DEFAULT_ALPHA_BUDGET,
+    DEFAULT_ALPHA_PER_TEST,
+    STATUS_INSUFFICIENT,
+    STATUS_PASS,
+    RefereeState,
+    certify_edge,
+)
+
+# The environment-variable NAME (the NAME only — never a path VALUE literal in code) the runtime
+# referee-audit report path may be overridden with. Mirrors `app.engine.drift.DRIFT_REPORT_PATH_ENV`.
+REFEREE_AUDIT_PATH_ENV = "TRENDORA_REFEREE_AUDIT_PATH"
+
+# Minimum names in one date's stored `forward_returns` cross-section to form a meaningful top-decile
+# split for the lookahead-contaminated factor's construction — a date with fewer names than this is
+# honestly skipped, never a fabricated 1-name "decile" (mirrors the referee's own thin-sample honesty).
+_MIN_CROSS_SECTION_NAMES = 10
+# "top decile" — the same 1/10 convention every Factor-Lab cohort in this codebase uses.
+_DECILE_DIVISOR = 10
+
+# The 97.5th percentile of the standard normal distribution — the two-sided z-score for a 95% Wilson
+# score confidence interval on a binomial proportion. A named constant (never an inline magic number).
+_WILSON_Z_95 = 1.959963984540054
+
+# An assembler returning the REAL source claim's `(cohort_obs, control_obs, horizon)` the null generator
+# permutes. Mirrors `app.engine.forward_walk.Assembler`.
+SourceAssembler = Callable[[], tuple[list, list, int]]
+# An assembler returning the lookahead-contaminated `(cohort_obs, control_obs)` (the horizon is the
+# config-sourced `contaminated_factor_horizon`, supplied by the caller, not the assembler).
+ContaminatedAssembler = Callable[[], tuple[list, list]]
+
+# The two kinds of throwaway-ledger entries this harness appends (an audit trail of the run, never the
+# real certified-claims schema's `claim`/`register_date` shape — these rows are diagnostic only).
+_KIND_NULL = "null"
+_KIND_CONTAMINATED = "contaminated"
+
+# Every field key a fully-built report carries — used to construct the honest, uniformly-None fallback
+# when a persisted artifact exists but cannot be parsed (mirrors `app.engine.drift`'s unreadable shape).
+_REPORT_FIELDS = (
+    "run_date", "n_null_trials", "seed", "alpha", "source_factor", "false_pass_count",
+    "false_pass_rate", "false_pass_ci_low", "false_pass_ci_high", "n_insufficient_null",
+    "contaminated_factor_horizon", "contaminated_verdict", "contaminated_expected_outcome",
+    "contaminated_caught",
+)
+
+
+# ==================================================================================================
+# Persistence — mirrors app.engine.drift exactly
+# ==================================================================================================
+def resolve_referee_audit_path() -> str:
+    """The referee-audit report artifact path: the `TRENDORA_REFEREE_AUDIT_PATH` env override if set,
+    else `config.research.referee_audit.report_path` resolved against `REPO_ROOT` when relative. Mirrors
+    `app.engine.drift.resolve_drift_report_path()` exactly, so every reader/writer agrees on the SAME
+    file. No path literal lives here — the default lives in config (anti-goal: No magic numbers)."""
+    override = os.environ.get(REFEREE_AUDIT_PATH_ENV)
+    if override:
+        return override
+    configured = Path(get_config().research.referee_audit.report_path)
+    if not configured.is_absolute():
+        configured = REPO_ROOT / configured
+    return str(configured)
+
+
+def _default_throwaway_ledger_path() -> str:
+    """The default ISOLATED throwaway ledger the harness certifies null/contaminated trials against when
+    the caller supplies none — co-located with the report artifact's directory, NEVER one of the real
+    ledger paths (`evidence.resolve_ledger_path()` / `graveyard.resolve_staging_ledger_path()` are never
+    referenced anywhere in this module). Overwritten fresh at the start of every `run_referee_audit` call
+    (see `run_referee_audit`'s docstring) — a disposable per-run audit trail, not an accumulating ledger."""
+    report_path = resolve_referee_audit_path()
+    parent = os.path.dirname(os.path.abspath(report_path))
+    return str(Path(parent) / "referee-audit-throwaway-ledger.jsonl")
+
+
+def write_referee_audit_report(report: dict) -> None:
+    """Persist the SINGLE referee-audit report artifact (OVERWRITE — only the latest run matters).
+    Creates the parent directory on first write. Written via a temp-file-then-rename so a reader never
+    observes a partially-written file. Mirrors `app.engine.drift.write_drift_report` exactly."""
+    path = resolve_referee_audit_path()
+    parent = os.path.dirname(os.path.abspath(path))
+    os.makedirs(parent, exist_ok=True)
+    tmp_path = f"{path}.tmp"
+    with open(tmp_path, "w", encoding="utf-8") as handle:
+        json.dump(report, handle, sort_keys=True, default=str)
+    os.replace(tmp_path, path)
+
+
+def read_referee_audit_report() -> Optional[dict]:
+    """The SINGLE reader the endpoint (and any future consumer) calls — no second parse path.
+
+    - Missing artifact (the offline job has never run) -> `None`, the honest inert case.
+    - Unparseable artifact -> an honest `{"status": "unreadable", ...all other fields None...}` dict —
+      NEVER a raise, and never silently treated as a clean/passing run."""
+    path = resolve_referee_audit_path()
+    if not os.path.exists(path):
+        return None
+    try:
+        with open(path, "r", encoding="utf-8") as handle:
+            data = json.load(handle)
+    except (OSError, json.JSONDecodeError):
+        data = None
+    if not isinstance(data, dict) or "run_date" not in data:
+        return {"status": "unreadable", **{key: None for key in _REPORT_FIELDS}}
+    return data
+
+
+# ==================================================================================================
+# (1) Seeded null-factor generator — PURE, exact
+# ==================================================================================================
+def permute_null_observations(cohort_obs: list, control_obs: list, *, rng: np.random.Generator) -> tuple[list, list]:
+    """The seeded null-factor generator (B-102 How #1): a PER-DATE random permutation of a real factor's
+    cross-section. For each date present in `cohort_obs` and/or `control_obs`, pool the values observed
+    that date, randomly reassign them back into groups of the SAME original per-date sizes, and repeat
+    independently per date. This preserves the EXACT multiset of realized values (the distribution is
+    untouched — nothing is fabricated) while destroying any true relationship between group membership
+    and value (the textbook permutation-test null). PURE: no filesystem/DB access; deterministic given
+    `rng`'s own state."""
+    by_date_cohort: dict = {}
+    by_date_control: dict = {}
+    for d, v in cohort_obs:
+        by_date_cohort.setdefault(d, []).append(v)
+    for d, v in control_obs:
+        by_date_control.setdefault(d, []).append(v)
+
+    null_cohort: list = []
+    null_control: list = []
+    for d in sorted(set(by_date_cohort) | set(by_date_control)):
+        cohort_vals = by_date_cohort.get(d, [])
+        control_vals = by_date_control.get(d, [])
+        pool = cohort_vals + control_vals
+        if not pool:
+            continue
+        n_cohort = len(cohort_vals)
+        idx = rng.permutation(len(pool))
+        shuffled = [pool[i] for i in idx]
+        for v in shuffled[:n_cohort]:
+            null_cohort.append((d, v))
+        for v in shuffled[n_cohort:]:
+            null_control.append((d, v))
+    return null_cohort, null_control
+
+
+# ==================================================================================================
+# Binomial proportion confidence interval — PURE, numpy/scipy-free (mirrors referee.py's own discipline)
+# ==================================================================================================
+def binomial_ci(successes: int, n: int) -> tuple[float, float]:
+    """The 95% Wilson score confidence interval for a binomial proportion (`successes` out of `n`
+    trials). Chosen over the naive Wald interval because it stays well-behaved at the extremes this audit
+    routinely sees (0, or very few, false-passes out of ~200 trials) — Wald degenerates to a zero-width
+    `[0, 0]` at zero successes, which would misleadingly read as "we are CERTAIN the true rate is exactly
+    0". A closed-form formula anyone can hand-verify; no scipy dependency. Returns `(low, high)`, clamped
+    to `[0, 1]`. `n == 0` returns the honest full interval `(0.0, 1.0)` — no observations, no information."""
+    if n <= 0:
+        return (0.0, 1.0)
+    z = _WILSON_Z_95
+    phat = successes / n
+    denom = 1.0 + (z * z) / n
+    center = phat + (z * z) / (2 * n)
+    margin = z * math.sqrt((phat * (1 - phat)) / n + (z * z) / (4 * n * n))
+    low = (center - margin) / denom
+    high = (center + margin) / denom
+    return (max(0.0, low), min(1.0, high))
+
+
+# ==================================================================================================
+# Report assembly — PURE
+# ==================================================================================================
+def build_referee_audit_report(
+    *,
+    run_date: str,
+    n_null_trials: int,
+    seed: int,
+    alpha: float,
+    false_pass_count: int,
+    n_insufficient_null: int,
+    source_factor: str,
+    contaminated_factor_horizon: int,
+    contaminated_verdict: dict,
+) -> dict:
+    """PURE assembly of the `/research/referee-audit` report dict from already-computed pieces —
+    recomputes nothing beyond the `binomial_ci` formula on the supplied count. `contaminated_expected_
+    outcome` is a STATIC disclosure label (`"rejected"`) per B-102's report spec — it is NOT a claim
+    about what actually happened; `contaminated_caught` is the honest DERIVED boolean
+    (`status != "PASS"`) the panel uses to choose between its calm and its loud tripwire-failure
+    treatment. `status: "ok"` marks a report that was actually built by a real run (vs. the `read_referee_
+    audit_report` "unreadable" fallback, which never calls this function)."""
+    false_pass_rate = false_pass_count / n_null_trials if n_null_trials > 0 else 0.0
+    ci_low, ci_high = binomial_ci(false_pass_count, n_null_trials)
+    return {
+        "status": "ok",
+        "run_date": run_date,
+        "n_null_trials": n_null_trials,
+        "seed": seed,
+        "alpha": alpha,
+        "source_factor": source_factor,
+        "false_pass_count": false_pass_count,
+        "false_pass_rate": false_pass_rate,
+        "false_pass_ci_low": ci_low,
+        "false_pass_ci_high": ci_high,
+        "n_insufficient_null": n_insufficient_null,
+        "contaminated_factor_horizon": contaminated_factor_horizon,
+        "contaminated_verdict": contaminated_verdict,
+        "contaminated_expected_outcome": "rejected",
+        "contaminated_caught": contaminated_verdict.get("status") != STATUS_PASS,
+    }
+
+
+# ==================================================================================================
+# The harness orchestrator
+# ==================================================================================================
+def run_referee_audit(
+    session=None,
+    *,
+    cfg=None,
+    ledger_path: Optional[str] = None,
+    run_date: Optional[str] = None,
+    assemble_source: Optional[SourceAssembler] = None,
+    assemble_contaminated: Optional[ContaminatedAssembler] = None,
+    source_factor_label: Optional[str] = None,
+) -> dict:
+    """Run the full referee-calibration harness and return the (UNPERSISTED) report dict — the single
+    orchestration entry point both `_main()` (the real offline job) and every test in this module
+    exercise. Call `write_referee_audit_report(report)` separately to persist it (mirrors `app.engine.
+    drift`'s build/write split).
+
+    ISOLATION (the dominant failure mode): every null trial AND the one contaminated trial runs through
+    `referee.certify_edge` DIRECTLY (never `app.mcp.tools.verify_edge`) against a FRESH
+    `RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET)` — never derived from any
+    ledger's accumulated count — and each verdict is appended ONLY to `ledger_path` (a THROWAWAY file,
+    freshly overwritten at the start of THIS call so repeated invocations never accumulate). This module
+    contains no reference anywhere to `evidence.resolve_ledger_path()` or `graveyard.resolve_staging_
+    ledger_path()`, so there is no code path that could reach the real `certified-claims.jsonl` /
+    `staging-ledger.jsonl`. `ledger_path` defaults to a co-located throwaway file
+    (`_default_throwaway_ledger_path()`) when omitted; tests pass an explicit `tmp_path`-backed path.
+
+    DB-FREE WHEN INJECTED: `assemble_source` / `assemble_contaminated` mirror `app.engine.forward_walk`'s
+    `Assembler` idiom. Omit them (the production call shape `_main` uses) and this pulls REAL data via
+    `app.mcp.tools.assemble_claim_observations` (the first configured Factor-Lab factor's top decile) plus
+    the stored `forward_returns` table (lazily imported — `session` is required only then, mirroring
+    `forward_walk._default_assembler`). Inject synthetic ones (every test in this module) and NO
+    session/DB is ever touched.
+
+    DETERMINISM: given the same `cfg.research.referee_audit.seed` and the same source/contaminated
+    observations, every null trial's permutation + bootstrap draws a per-trial `seed + i`, so the whole
+    run (false-pass rate, CI, contaminated verdict) reproduces byte-identically."""
+    cfg = cfg or get_config()
+    ra_cfg = cfg.research.referee_audit
+    if ledger_path is None:
+        ledger_path = _default_throwaway_ledger_path()
+    # Fresh start every run — a disposable audit trail for THIS run only, never an accumulating ledger.
+    if os.path.exists(ledger_path):
+        os.remove(ledger_path)
+
+    if assemble_source is None:
+        assemble_source, source_factor_label = _default_source_assembler(session, cfg)
+    source_cohort, source_control, source_horizon = assemble_source()
+
+    if assemble_contaminated is None:
+        cohort_dates = {d for d, _ in source_cohort} | {d for d, _ in source_control}
+        assemble_contaminated = _default_contaminated_assembler(session, cfg, cohort_dates)
+    contaminated_cohort, contaminated_control = assemble_contaminated()
+
+    if run_date is None:
+        run_date = _default_run_date(session)
+
+    false_pass = 0
+    n_insufficient = 0
+    for i in range(1, ra_cfg.n_null_trials + 1):
+        trial_seed = ra_cfg.seed + i
+        null_cohort, null_control = permute_null_observations(
+            source_cohort, source_control, rng=np.random.default_rng(trial_seed)
+        )
+        verdict = certify_edge(
+            null_cohort, null_control, horizon=source_horizon,
+            state=RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET),
+            seed=trial_seed,
+        )
+        ledger_mod.append_entry(
+            ledger_path, {"trial": i, "kind": _KIND_NULL, "verdict": verdict.to_dict()}
+        )
+        if verdict.status == STATUS_PASS:
+            false_pass += 1
+        elif verdict.status == STATUS_INSUFFICIENT:
+            n_insufficient += 1
+
+    contaminated_verdict = certify_edge(
+        contaminated_cohort, contaminated_control, horizon=ra_cfg.contaminated_factor_horizon,
+        state=RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET),
+        seed=ra_cfg.seed,
+    )
+    ledger_mod.append_entry(
+        ledger_path, {"kind": _KIND_CONTAMINATED, "verdict": contaminated_verdict.to_dict()}
+    )
+
+    return build_referee_audit_report(
+        run_date=run_date,
+        n_null_trials=ra_cfg.n_null_trials,
+        seed=ra_cfg.seed,
+        alpha=DEFAULT_ALPHA_PER_TEST,
+        false_pass_count=false_pass,
+        n_insufficient_null=n_insufficient,
+        source_factor=source_factor_label or "unknown",
+        contaminated_factor_horizon=ra_cfg.contaminated_factor_horizon,
+        contaminated_verdict=contaminated_verdict.to_dict(),
+    )
+
+
+# ==================================================================================================
+# Default (DB-backed) assemblers — lazily imported, exactly like app.engine.forward_walk's
+# ==================================================================================================
+def _default_source_assembler(session, cfg) -> tuple[SourceAssembler, str]:
+    """The PRODUCTION source assembler: the first configured Factor-Lab factor's top-decile claim (a REAL
+    Research-lab cohort), via the SHARED `assemble_claim_observations` seam `verify_edge` also uses.
+    Imported LAZILY so importing this module stays light (numpy + referee + ledger only) and DB-free
+    tests never drag in the MCP/tools/SQLAlchemy stack — mirrors `forward_walk._default_assembler`."""
+    from app.mcp.tools import assemble_claim_observations
+
+    factor_key = cfg.research.factor_lab.factors[0].key
+    claim = {
+        "kind": "factor", "factor": factor_key, "slice_kind": "decile", "decile": 10,
+        "horizon": cfg.walk_forward.default_horizon,
+    }
+
+    def assemble():
+        return assemble_claim_observations(session, claim)
+
+    return assemble, factor_key
+
... [diff_bound] apps/backend/app/engine/referee_audit.py: 84 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_api_referee_audit.py b/apps/backend/tests/test_api_referee_audit.py
new file mode 100644
index 0000000..a724970
--- /dev/null
+++ b/apps/backend/tests/test_api_referee_audit.py
@@ -0,0 +1,102 @@
+"""GET /api/research/referee-audit API tests (goal-mcp-loop iter-36, J-22 / backlog B-102).
+
+Mounts ONLY the referee-audit router on a bare FastAPI app (NO lifespan) so the test needs NO seeded DB
+and NO walk-forward boot -- the endpoint reads a single state-file artifact, not a snapshot (mirrors
+`test_api_budget.py` / `test_api_graveyard.py`'s DB-free pattern exactly).
+"""
+from __future__ import annotations
+
+from fastapi import FastAPI
+from fastapi.testclient import TestClient
+
+from app.api import referee_audit
+from app.engine.referee import STATUS_FAIL
+from app.engine.referee_audit import (
+    REFEREE_AUDIT_PATH_ENV,
+    build_referee_audit_report,
+    read_referee_audit_report,
+    write_referee_audit_report,
+)
+
+
+def _client() -> TestClient:
+    app = FastAPI()
+    app.include_router(referee_audit.router, prefix="/api")
+    return TestClient(app)
+
+
+def test_referee_audit_endpoint_200_honest_empty_on_missing_artifact(tmp_path, monkeypatch):
+    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(tmp_path / "does-not-exist.json"))
+    with _client() as client:
+        resp = client.get("/api/research/referee-audit")
+    assert resp.status_code == 200
+    assert resp.json() == {"report": None}
+
+
+def test_referee_audit_endpoint_200_honest_unreadable_on_corrupt_artifact_never_500(tmp_path, monkeypatch):
+    target = tmp_path / "corrupt.json"
+    target.write_text("{not valid json", encoding="utf-8")
+    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
+    with _client() as client:
+        resp = client.get("/api/research/referee-audit")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["report"]["status"] == "unreadable"
+    assert body["report"]["contaminated_verdict"] is None
+
+
+def test_referee_audit_endpoint_serves_a_fixture_artifact_verbatim(tmp_path, monkeypatch):
+    target = tmp_path / "report.json"
+    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
+    report = build_referee_audit_report(
+        run_date="2026-07-14", n_null_trials=200, seed=20240601, alpha=0.05,
+        false_pass_count=9, n_insufficient_null=0, source_factor="leadership_score",
+        contaminated_factor_horizon=5,
+        contaminated_verdict={"status": STATUS_FAIL, "reason": "fixture", "p_value": 0.9},
+    )
+    write_referee_audit_report(report)
+    with _client() as client:
+        resp = client.get("/api/research/referee-audit")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["report"] == report
+    assert body["report"]["false_pass_count"] == 9
+    assert body["report"]["contaminated_expected_outcome"] == "rejected"
+    assert body["report"]["contaminated_caught"] is True
+
+
+def test_referee_audit_endpoint_equals_read_referee_audit_report_directly(tmp_path, monkeypatch):
+    """Single-source assertion: the endpoint's response equals `read_referee_audit_report()` called
+    directly against the SAME artifact -- the page can never disagree with the reader module."""
+    target = tmp_path / "report.json"
+    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
+    report = build_referee_audit_report(
+        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=0.05,
+        false_pass_count=0, n_insufficient_null=0, source_factor="rs_spy_3m",
+        contaminated_factor_horizon=5,
+        contaminated_verdict={"status": STATUS_FAIL, "reason": "fixture"},
+    )
+    write_referee_audit_report(report)
+    with _client() as client:
+        resp = client.get("/api/research/referee-audit")
+    assert resp.status_code == 200
+    assert resp.json() == {"report": read_referee_audit_report()}
+
+
+def test_referee_audit_endpoint_never_recomputes_beyond_the_persisted_artifact(tmp_path, monkeypatch):
+    """The endpoint must not re-derive `false_pass_rate` / CI from `false_pass_count` -- it re-serves
+    whatever the artifact carries VERBATIM, even a deliberately inconsistent fixture value (proves no
+    recompute path exists in the router)."""
+    target = tmp_path / "report.json"
+    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
+    report = build_referee_audit_report(
+        run_date="2026-07-14", n_null_trials=200, seed=1, alpha=0.05,
+        false_pass_count=9, n_insufficient_null=0, source_factor="x",
+        contaminated_factor_horizon=5,
+        contaminated_verdict={"status": STATUS_FAIL, "reason": "fixture"},
+    )
+    report["false_pass_rate"] = 0.9999  # deliberately inconsistent with false_pass_count/n_null_trials
+    write_referee_audit_report(report)
+    with _client() as client:
+        resp = client.get("/api/research/referee-audit")
+    assert resp.json()["report"]["false_pass_rate"] == 0.9999  # verbatim, not recomputed to 0.045
diff --git a/apps/backend/tests/test_referee_audit.py b/apps/backend/tests/test_referee_audit.py
new file mode 100644
index 0000000..f82503e
--- /dev/null
+++ b/apps/backend/tests/test_referee_audit.py
@@ -0,0 +1,639 @@
+"""Tests for the referee-calibration harness (`app.engine.referee_audit`, goal-mcp-loop iter-36, J-22 /
+backlog B-102).
+
+All tests here are PURE + synthetic (no DB, fast, mirroring `tests/test_referee.py` /
+`tests/test_forward_walk.py`'s established "inject synthetic observations, no DB ever boots" idiom) —
+EXCEPT the two `_default_*_assembler` wiring tests, which use a tiny in-memory SQLite fixture (mirrors
+`tests/test_regime_history.py`'s `make_engine("sqlite:///:memory:")` pattern) and NEVER the full 30-year
+committed seed (`loaded_engine`).
+
+These tests prove the contracts the DoD names:
+  * `permute_null_observations` preserves the exact multiset of observed values (never fabricates a
+    number) while reassigning per-date group membership (kills the true cohort/control relationship);
+  * `binomial_ci` matches a hand-computed Wilson score interval;
+  * `run_referee_audit` is DETERMINISTIC given the same seed + inputs;
+  * ISOLATION: the harness writes ONLY the given throwaway `ledger_path`; the real `certified-
+    claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` are byte-unchanged;
+  * the lookahead-contaminated factor is REJECTED when it carries no real edge (deterministic FAIL), and
+    the report's `contaminated_caught` flag correctly flips to False (the loud-tripwire case) when a
+    "perfect crime" (huge, noiseless edge) DOES slip through as PASS — both are analytically exact, not
+    empirically discovered, so neither depends on numpy's RNG internals;
+  * a missing/unparseable persisted artifact degrades honestly (never raises).
+"""
+from __future__ import annotations
+
+from datetime import date, timedelta
+
+import numpy as np
+import pytest
+
+from app.config import REPO_ROOT
+from app.engine import ledger as ledger_mod
+from app.engine.referee import DEFAULT_ALPHA_PER_TEST, STATUS_FAIL, STATUS_PASS
+from app.engine.referee_audit import (
+    REFEREE_AUDIT_PATH_ENV,
+    binomial_ci,
+    build_referee_audit_report,
+    permute_null_observations,
+    read_referee_audit_report,
+    resolve_referee_audit_path,
+    run_referee_audit,
+    write_referee_audit_report,
+)
+
+_START = date(2021, 1, 3)
+_CANONICAL_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/certified-claims.jsonl"
+_STAGING_LEDGER = REPO_ROOT / "runs/goal-session-mcp-loop/state/staging-ledger.jsonl"
+_REGISTRY = REPO_ROOT / "runs/goal-session-mcp-loop/state/pre-registrations.jsonl"
+
+
+def _make_observations(*, n_dates, edge_at, seed, n_cohort=8, n_control=4, noise=0.01, market_sigma=0.02):
+    """Synthesize `(cohort, control)` over `n_dates` consecutive calendar days — the SAME generator shape
+    `test_referee.py`/`test_forward_walk.py` already use. A shared per-date market level cancels in the
+    cohort-minus-control excess; the cohort additionally carries `edge_at(i)` on date index i."""
+    rng = np.random.default_rng(seed)
+    cohort, control = [], []
+    for i in range(n_dates):
+        d = _START + timedelta(days=i)
+        market = rng.normal(0.0, market_sigma)
+        ed = edge_at(i)
+        for _ in range(n_control):
+            control.append((d, market + rng.normal(0.0, noise)))
+        for _ in range(n_cohort):
+            cohort.append((d, market + ed + rng.normal(0.0, noise)))
+    return cohort, control
+
+
+def _flat_observations(n_dates, *, cohort_value, control_value):
+    """A ZERO-VARIANCE (date, value) pair — every cohort observation is exactly `cohort_value`, every
+    control observation exactly `control_value`, on `n_dates` consecutive calendar days. Used to build
+    fully deterministic (seed-invariant) referee verdicts: a constant series' per-date excess has zero
+    variance, so its block-bootstrap p-value is invariant to which indices the bootstrap draws."""
+    dates = [_START + timedelta(days=i) for i in range(n_dates)]
+    cohort = [(d, cohort_value) for d in dates]
+    control = [(d, control_value) for d in dates]
+    return cohort, control
+
+
+# ==================================================================================================
+# permute_null_observations — PURE, exact
+# ==================================================================================================
+def test_permutation_preserves_the_exact_multiset_of_values():
+    cohort, control = _make_observations(n_dates=10, edge_at=lambda i: 0.03, seed=1)
+    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(5))
+    before = sorted(v for _, v in cohort + control)
+    after = sorted(v for _, v in null_cohort + null_control)
+    assert after == before
+    assert len(null_cohort) == len(cohort)
+    assert len(null_control) == len(control)
+
+
+def test_permutation_preserves_per_date_group_sizes():
+    cohort, control = _make_observations(n_dates=6, edge_at=lambda i: 0.02, seed=2, n_cohort=8, n_control=4)
+    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(9))
+    before_dates = sorted({d for d, _ in cohort})
+    for d in before_dates:
+        assert sum(1 for dd, _ in null_cohort if dd == d) == 8
+        assert sum(1 for dd, _ in null_control if dd == d) == 4
+
+
+def test_permutation_is_deterministic_given_the_same_rng_seed():
+    cohort, control = _make_observations(n_dates=8, edge_at=lambda i: 0.02, seed=3)
+    a = permute_null_observations(cohort, control, rng=np.random.default_rng(42))
+    b = permute_null_observations(cohort, control, rng=np.random.default_rng(42))
+    assert a == b
+
+
+def test_permutation_reassigns_values_matching_numpys_own_permutation_api():
+    """Hand-trace ONE date with a known rng seed: the expected reassignment is derived from numpy's OWN
+    `permutation` call (not a hardcoded index sequence), so this stays robust to internals while still
+    being an exact, non-fuzzy assertion."""
+    d = _START
+    cohort = [(d, 1.0), (d, 2.0)]
+    control = [(d, 3.0), (d, 4.0)]
+    pool = [1.0, 2.0, 3.0, 4.0]
+    expected_idx = np.random.default_rng(11).permutation(4)
+    expected_shuffled = [pool[i] for i in expected_idx]
+    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(11))
+    assert [v for _, v in null_cohort] == expected_shuffled[:2]
+    assert [v for _, v in null_control] == expected_shuffled[2:]
+
+
+def test_permutation_skips_a_date_with_no_observations_on_either_side():
+    d1, d2 = _START, _START + timedelta(days=1)
+    cohort = [(d1, 1.0)]
+    control = [(d2, 2.0)]
+    null_cohort, null_control = permute_null_observations(cohort, control, rng=np.random.default_rng(1))
+    # each date has exactly one observation on ONE side -> the permuted pool (size 1) has nowhere to go
+    # but back to the cohort/control split of size (1, 0) or (0, 1) per date -- never invents a pairing.
+    assert sorted(v for _, v in null_cohort + null_control) == [1.0, 2.0]
+
+
+# ==================================================================================================
+# binomial_ci — PURE, hand-computed Wilson score interval
+# ==================================================================================================
+def test_binomial_ci_matches_hand_computed_wilson_interval():
+    z = 1.959963984540054
+    successes, n = 9, 200
+    phat = successes / n
+    denom = 1.0 + (z * z) / n
+    center = phat + (z * z) / (2 * n)
+    margin = z * ((phat * (1 - phat)) / n + (z * z) / (4 * n * n)) ** 0.5
+    expected_low = (center - margin) / denom
+    expected_high = (center + margin) / denom
+    low, high = binomial_ci(successes, n)
+    assert low == pytest.approx(expected_low, abs=1e-12)
+    assert high == pytest.approx(expected_high, abs=1e-12)
+
+
+def test_binomial_ci_zero_successes_is_non_degenerate():
+    """The Wilson interval never collapses to [0, 0] at zero successes (unlike the naive Wald interval) —
+    the whole reason Wilson was chosen over Wald for this panel's typical near-zero false-pass counts."""
+    low, high = binomial_ci(0, 200)
+    assert low == pytest.approx(0.0, abs=1e-12)  # mathematically exactly 0; a tiny fp residual is fine
+    assert high > 0.0
+
+
+def test_binomial_ci_bounds_are_always_within_zero_one():
+    for successes, n in [(0, 1), (1, 1), (0, 20), (20, 20), (10, 200)]:
+        low, high = binomial_ci(successes, n)
+        assert 0.0 <= low <= high <= 1.0
+
+
+def test_binomial_ci_zero_trials_is_the_honest_full_interval():
+    assert binomial_ci(0, 0) == (0.0, 1.0)
+
+
+# ==================================================================================================
+# build_referee_audit_report — PURE assembly
+# ==================================================================================================
+def test_report_marks_contaminated_caught_true_on_fail():
+    report = build_referee_audit_report(
+        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
+        false_pass_count=1, n_insufficient_null=0, source_factor="rs_spy_3m",
+        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_FAIL, "reason": "x"},
+    )
+    assert report["contaminated_caught"] is True
+    assert report["contaminated_expected_outcome"] == "rejected"
+    assert report["status"] == "ok"
+
+
+def test_report_marks_contaminated_caught_false_on_pass_the_tripwire_case():
+    report = build_referee_audit_report(
+        run_date="2026-07-14", n_null_trials=20, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
+        false_pass_count=1, n_insufficient_null=0, source_factor="rs_spy_3m",
+        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_PASS, "reason": "x"},
+    )
+    assert report["contaminated_caught"] is False
+
+
+def test_report_false_pass_rate_and_ci_are_computed_from_the_count():
+    report = build_referee_audit_report(
+        run_date="2026-07-14", n_null_trials=200, seed=1, alpha=DEFAULT_ALPHA_PER_TEST,
+        false_pass_count=9, n_insufficient_null=0, source_factor="rs_spy_3m",
+        contaminated_factor_horizon=5, contaminated_verdict={"status": STATUS_FAIL, "reason": "x"},
+    )
+    assert report["false_pass_count"] == 9
+    assert report["false_pass_rate"] == pytest.approx(9 / 200)
+    expected_low, expected_high = binomial_ci(9, 200)
+    assert report["false_pass_ci_low"] == expected_low
+    assert report["false_pass_ci_high"] == expected_high
+    assert report["alpha"] == DEFAULT_ALPHA_PER_TEST
+    assert report["source_factor"] == "rs_spy_3m"
+    assert report["seed"] == 1
+    assert report["n_null_trials"] == 200
+
+
+def test_report_alpha_uses_the_imported_referee_constant_not_a_literal():
+    assert DEFAULT_ALPHA_PER_TEST == 0.05
+
+
+# ==================================================================================================
+# run_referee_audit — injected assemblers, no DB, deterministic
+# ==================================================================================================
+def _source_edge(seed=1, n_dates=60):
+    return _make_observations(n_dates=n_dates, edge_at=lambda i: 0.03, seed=seed)
+
+
+def _rejected_contaminated():
+    """A ZERO-edge 'contaminated' construction -- cohort and control are identically distributed, so the
+    referee deterministically FAILS it (the honest, expected outcome the tripwire test names)."""
+    return _flat_observations(30, cohort_value=0.01, control_value=0.01)
+
+
+def _slipped_through_contaminated():
+    """A noiseless, huge, constant-edge 'contaminated' construction -- the literal 'perfect crime':
+    every cohort observation beats every control observation by a large deterministic margin, so the
+    referee deterministically PASSES it regardless of seed (a constant per-date excess has a
+    seed-invariant block-bootstrap p-value) -- the tripwire-fires case."""
+    return _flat_observations(60, cohort_value=1.0, control_value=0.0)
+
+
+class _FakeCfg:
+    """A minimal cfg stand-in exposing only what `run_referee_audit` reads off
+    `cfg.research.referee_audit` -- avoids depending on the real committed config.yaml values so the
+    fixture stays self-contained and fast."""
+
+    class _RA:
+        def __init__(self, n_null_trials, seed, contaminated_factor_horizon):
+            self.n_null_trials = n_null_trials
+            self.seed = seed
+            self.contaminated_factor_horizon = contaminated_factor_horizon
+
+    class _Research:
+        def __init__(self, ra):
+            self.referee_audit = ra
+
+    def __init__(self, n_null_trials=20, seed=123, contaminated_factor_horizon=5):
+        self.research = self._Research(self._RA(n_null_trials, seed, contaminated_factor_horizon))
+
+
+def _assemble_source_factory(seed=1, horizon=5):
+    cohort, control = _source_edge(seed=seed)
+
+    def assemble():
+        return cohort, control, horizon
+
+    return assemble
+
+
+def test_run_referee_audit_is_deterministic_given_the_same_seed(tmp_path):
+    cfg = _FakeCfg(n_null_trials=15, seed=777)
+    kwargs = dict(
+        cfg=cfg,
+        assemble_source=_assemble_source_factory(),
+        assemble_contaminated=_rejected_contaminated,
+        run_date="2026-07-14",
+    )
+    report_a = run_referee_audit(ledger_path=str(tmp_path / "a.jsonl"), **kwargs)
+    report_b = run_referee_audit(ledger_path=str(tmp_path / "b.jsonl"), **kwargs)
+    assert report_a == report_b
+
+
+def test_run_referee_audit_writes_only_the_throwaway_ledger_never_the_real_files(tmp_path):
+    canonical_before = _CANONICAL_LEDGER.read_text(encoding="utf-8")
+    staging_before = _STAGING_LEDGER.read_text(encoding="utf-8")
+    registry_before = _REGISTRY.read_text(encoding="utf-8")
+
+    throwaway = tmp_path / "throwaway.jsonl"
+    cfg = _FakeCfg(n_null_trials=10, seed=5)
+    run_referee_audit(
+        cfg=cfg,
+        ledger_path=str(throwaway),
+        assemble_source=_assemble_source_factory(),
+        assemble_contaminated=_rejected_contaminated,
+        run_date="2026-07-14",
+    )
+
+    assert throwaway.exists()
+    entries = ledger_mod.read_entries(str(throwaway))
+    assert len(entries) == 10 + 1  # 10 null trials + 1 contaminated trial
+    assert _CANONICAL_LEDGER.read_text(encoding="utf-8") == canonical_before
+    assert _STAGING_LEDGER.read_text(encoding="utf-8") == staging_before
+    assert _REGISTRY.read_text(encoding="utf-8") == registry_before
+
+
+def test_run_referee_audit_overwrites_the_throwaway_ledger_fresh_each_call(tmp_path):
+    path = tmp_path / "ledger.jsonl"
+    cfg = _FakeCfg(n_null_trials=6, seed=1)
+    run_referee_audit(
+        cfg=cfg, ledger_path=str(path), assemble_source=_assemble_source_factory(),
+        assemble_contaminated=_rejected_contaminated, run_date="2026-07-14",
+    )
+    first_count = len(ledger_mod.read_entries(str(path)))
+    run_referee_audit(
+        cfg=cfg, ledger_path=str(path), assemble_source=_assemble_source_factory(),
+        assemble_contaminated=_rejected_contaminated, run_date="2026-07-14",
+    )
+    second_count = len(ledger_mod.read_entries(str(path)))
+    assert first_count == second_count == 7  # never accumulates across repeated harness invocations
+
+
+def test_run_referee_audit_each_null_trial_uses_a_fresh_state_never_a_ledger_derived_count(tmp_path):
+    """Every null trial's required_p must be `alpha / 1` (an INDEPENDENT test at the raw configured
+    alpha) -- never Bonferroni-deflated by an accumulating count across the 200 nulls, which would make
+    the empirical false-pass rate incomparable to the configured alpha the panel displays it against."""
+    path = tmp_path / "ledger.jsonl"
+    cfg = _FakeCfg(n_null_trials=8, seed=2)
+    run_referee_audit(
+        cfg=cfg, ledger_path=str(path), assemble_source=_assemble_source_factory(),
+        assemble_contaminated=_rejected_contaminated, run_date="2026-07-14",
+    )
+    entries = ledger_mod.read_entries(str(path))
+    null_entries = [e for e in entries if e.get("kind") == "null"]
+    assert len(null_entries) == 8
+    for entry in null_entries:
+        assert entry["verdict"]["required_p"] == pytest.approx(DEFAULT_ALPHA_PER_TEST / 1)
+        assert entry["verdict"]["deflation_divisor"] == 1
+
+
+def test_run_referee_audit_reduces_pass_rate_below_the_unpermuted_baseline(tmp_path):
+    """The un-permuted source data is a TRUE persistent edge (certifies PASS on its own, per
+    `test_referee.py`'s identical construction) -- proving the null generator's permutation strictly
+    reduces the pass rate below "every trial passes" is the calibration property this harness exists to
+    measure. An exact, deterministic inequality (not a vague threshold)."""
+    from app.engine.referee import DEFAULT_ALPHA_BUDGET, RefereeState, certify_edge
+
+    cohort, control = _source_edge(seed=1)
+    unpermuted = certify_edge(
+        cohort, control, horizon=5, state=RefereeState(n_trials=1, alpha_budget_remaining=DEFAULT_ALPHA_BUDGET), seed=7,
+    )
+    assert unpermuted.status == STATUS_PASS  # sanity: the source data IS a real, certifiable edge
+
+    cfg = _FakeCfg(n_null_trials=20, seed=99)
+    report = run_referee_audit(
+        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
+        assemble_source=_assemble_source_factory(seed=1), assemble_contaminated=_rejected_contaminated,
+        run_date="2026-07-14",
+    )
+    assert report["false_pass_count"] < report["n_null_trials"]
+
+
+def test_run_referee_audit_contaminated_factor_rejected_is_deterministic_fail(tmp_path):
+    cfg = _FakeCfg(n_null_trials=5, seed=1, contaminated_factor_horizon=5)
+    report = run_referee_audit(
+        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
+        assemble_source=_assemble_source_factory(), assemble_contaminated=_rejected_contaminated,
+        run_date="2026-07-14",
+    )
+    assert report["contaminated_verdict"]["status"] == STATUS_FAIL
+    assert report["contaminated_caught"] is True
+    assert report["contaminated_expected_outcome"] == "rejected"
+
+
+def test_run_referee_audit_contaminated_factor_slipping_through_sets_tripwire(tmp_path):
+    cfg = _FakeCfg(n_null_trials=5, seed=1, contaminated_factor_horizon=5)
+    report = run_referee_audit(
+        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
+        assemble_source=_assemble_source_factory(), assemble_contaminated=_slipped_through_contaminated,
+        run_date="2026-07-14",
+    )
+    assert report["contaminated_verdict"]["status"] == STATUS_PASS
+    assert report["contaminated_caught"] is False  # the honest, un-hidden tripwire signal
+    assert report["contaminated_expected_outcome"] == "rejected"  # the static label is unaffected
+
+
+def test_run_referee_audit_report_carries_the_configured_run_params(tmp_path):
+    cfg = _FakeCfg(n_null_trials=13, seed=42, contaminated_factor_horizon=9)
+    report = run_referee_audit(
+        cfg=cfg, ledger_path=str(tmp_path / "ledger.jsonl"),
+        assemble_source=_assemble_source_factory(horizon=5), assemble_contaminated=_rejected_contaminated,
+        run_date="2026-07-14",
+    )
+    assert report["n_null_trials"] == 13
+    assert report["seed"] == 42
+    assert report["contaminated_factor_horizon"] == 9
+    assert report["run_date"] == "2026-07-14"
+
+
+# ==================================================================================================
+# Persistence: resolve/write/read round-trip + honest degradation
+# ==================================================================================================
+def test_resolve_path_uses_env_override(tmp_path, monkeypatch):
+    target = tmp_path / "custom-report.json"
+    monkeypatch.setenv(REFEREE_AUDIT_PATH_ENV, str(target))
... [diff_bound] apps/backend/tests/test_referee_audit.py: 245 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/app/research/referee-audit/page.tsx b/apps/frontend/app/research/referee-audit/page.tsx
new file mode 100644
index 0000000..d1aea89
--- /dev/null
+++ b/apps/frontend/app/research/referee-audit/page.tsx
@@ -0,0 +1,294 @@
+"use client";
+
+import { useEffect, useState } from "react";
+import Link from "next/link";
+import { AlertTriangle, ArrowLeft, ShieldAlert, ShieldCheck } from "lucide-react";
+
+import { useAsOfHref } from "@/components/asof-provider";
+import { PageHeading } from "@/components/page-heading";
+import { Badge } from "@/components/ui/badge";
+import { Card, CardContent } from "@/components/ui/card";
+import { fetchRefereeAudit, type RefereeAuditReport, type RefereeAuditResponse } from "@/lib/api";
+import { formatIsoDate } from "@/lib/dates";
+import { formatPValue } from "@/lib/evidence";
+import { cn } from "@/lib/utils";
+
+/**
+ * /research/referee-audit — the referee-calibration report (goal-mcp-loop iter-36, J-22 / backlog
+ * B-102).
+ *
+ * A read-only view of whether the certifier itself is calibrated: the empirical false-pass rate (with a
+ * binomial CI) measured over seeded null (label-permuted) factors against the configured significance
+ * level α, plus a lookahead-contaminated-factor tripwire result — all computed ONCE by an ISOLATED
+ * offline job against a throwaway ledger (the real certified-claims/staging ledgers and the real
+ * Thresholdout budget are never touched) and re-read VERBATIM here. Reads ONLY
+ * `GET /api/research/referee-audit`; no forms, no mutations, no UI action triggers the audit run.
+ *
+ * NO proven-language anywhere on this page: every figure is descriptive calibration accounting (a trial
+ * count, a false-pass rate, a verdict kind) — never a "Proven"/"Not yet proven" signal. The single source
+ * of "Proven" stays `/evidence`; this page never resolves or displays evidence status, and the audit's
+ * own throwaway trials never appear on that ledger.
+ */
+export default function RefereeAuditPage() {
+  const [state, setState] = useState<State>({ kind: "loading" });
+
+  useEffect(() => {
+    const controller = new AbortController();
+    setState({ kind: "loading" });
+    fetchRefereeAudit(controller.signal)
+      .then((data) => setState({ kind: "ok", data }))
+      .catch(() => {
+        if (!controller.signal.aborted) setState({ kind: "error" });
+      });
+    return () => controller.abort();
+  }, []);
+
+  return (
+    <div className="space-y-4">
+      <div className="space-y-2">
+        <BackToResearch />
+        <PageHeading
+          title="Referee audit"
+          subtitle="Is the certifier itself calibrated? The measured empirical false-pass rate over seeded null factors, against the configured significance level, plus a lookahead-contaminated-factor tripwire — computed once by an isolated offline job against a throwaway ledger. Descriptive calibration accounting only; nothing here is a proven/not-proven signal."
+        />
+      </div>
+
+      {state.kind === "loading" ? <RefereeAuditSkeleton /> : null}
+
+      {state.kind === "error" ? (
+        <Card
+          className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg"
+          data-testid="referee-audit-error"
+        >
+          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
+          <div>
+            <p className="font-medium">Backend unavailable</p>
+            <p className="text-text-muted">
+              The referee-audit report could not load from the API. Confirm the backend is running and
+              reload.
+            </p>
+          </div>
+        </Card>
+      ) : null}
+
+      {state.kind === "ok" ? <ReportBody report={state.data.report} /> : null}
+    </div>
+  );
+}
+
+type State = { kind: "loading" } | { kind: "ok"; data: RefereeAuditResponse } | { kind: "error" };
+
+/** A same-window link back to the Research hub (mirrors `research/budget/page.tsx`'s pattern exactly). */
+function BackToResearch() {
+  const asofHref = useAsOfHref();
+  return (
+    <Link
+      href={asofHref("/research")}
+      className="inline-flex items-center gap-1 text-xs font-medium text-text-muted hover:text-accent focus-visible:text-accent focus-visible:outline-none"
+    >
+      <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Back to Research
+    </Link>
+  );
+}
+
+function ReportBody({ report }: { report: RefereeAuditReport | null }) {
+  if (report === null) {
+    return <EmptyState />;
+  }
+  if (report.status === "unreadable") {
+    return <UnreadableState />;
+  }
+  return <ReportPanel report={report} />;
+}
+
+/** The honest empty state — no offline harness run has ever persisted an artifact yet. The audit is a
+ *  config-seeded job, not a UI action, so this page never offers a "run it" button (J-22 is read-only). */
+function EmptyState() {
+  return (
+    <Card data-testid="referee-audit-empty">
+      <CardContent className="space-y-3 p-6">
+        <div className="flex items-center gap-2">
+          <ShieldAlert className="h-5 w-5 text-text-faint" aria-hidden />
+          <h2 className="text-sm font-semibold text-text">No audit run yet</h2>
+        </div>
+        <p className="max-w-2xl text-sm text-text-muted">
+          The referee-calibration harness has not been run yet. It runs as a config-seeded offline job
+          (<code className="rounded bg-surface-2 px-1 py-0.5 text-xs">python -m app.engine.referee_audit</code>),
+          never as a UI action here — once it runs, its persisted report appears on this page.
+        </p>
+      </CardContent>
+    </Card>
+  );
+}
+
+/** An artifact exists but could not be parsed — an honest degraded read, distinct from "never run"
+ *  (EmptyState) and distinct from the tripwire failure (this is a data-integrity hiccup, not a caught
+ *  leak). Amber, not red — mirrors `DriftReportPanel`'s own unreadable-artifact treatment on /data. */
+function UnreadableState() {
+  return (
+    <Card className="border-warn bg-warn/10" data-testid="referee-audit-unreadable">
+      <CardContent className="flex items-start gap-3 p-6">
+        <AlertTriangle className="h-5 w-5 shrink-0 text-warn" aria-hidden />
+        <div>
+          <p className="font-medium text-warn">Audit artifact unreadable</p>
+          <p className="text-text-muted">
+            A referee-audit report exists but could not be parsed. Re-run the offline harness
+            (<code className="rounded bg-surface-2 px-1 py-0.5 text-xs">python -m app.engine.referee_audit</code>)
+            to regenerate it.
+          </p>
+        </div>
+      </CardContent>
+    </Card>
+  );
+}
+
+/** The verdict-kind badge variant — mirrors `research/graveyard/page.tsx`'s `verdictKindVariant` mapping
+ *  for FAIL/INSUFFICIENT. A PASS here is the tripwire-fired case (the contaminated factor slipped
+ *  through) — mapped to `danger`, NEVER `accent` (this page must never render a "Proven"-looking badge,
+ *  anti-goal #1), since a PASS on the perfect-crime factor is alarming, not a proof of anything. */
+function contaminatedStatusVariant(status: string | null | undefined): "danger" | "warn" | "default" {
+  if (status === "FAIL" || status === "PASS") return "danger";
+  if (status === "INSUFFICIENT") return "warn";
+  return "default";
+}
+
+function ReportPanel({ report }: { report: RefereeAuditReport }) {
+  return (
+    <div className="space-y-4">
+      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="referee-audit-grid">
+        <StatCard
+          testId="referee-audit-null-trials"
+          title="Null trials"
+          headline={String(report.n_null_trials ?? "—")}
+          subtext={`source factor: ${report.source_factor ?? "—"}`}
+        />
+        <StatCard
+          testId="referee-audit-false-pass-rate"
+          title="Empirical false-pass rate"
+          headline={formatPValue(report.false_pass_rate)}
+          subtext={`${report.false_pass_count ?? "—"} of ${report.n_null_trials ?? "—"} trials · 95% CI [${formatPValue(report.false_pass_ci_low)}, ${formatPValue(report.false_pass_ci_high)}]`}
+        />
+        <StatCard
+          testId="referee-audit-alpha"
+          title="Configured α"
+          headline={formatPValue(report.alpha)}
+          subtext="the significance level the null trials are judged against"
+        />
+        <StatCard
+          testId="referee-audit-run-date"
+          title="Run date"
+          headline={formatIsoDate(report.run_date)}
+          subtext={`seed ${report.seed ?? "—"} · contaminated horizon ${report.contaminated_factor_horizon ?? "—"}d`}
+        />
+      </div>
+
+      {report.contaminated_caught ? (
+        <CalmContaminatedCard report={report} />
+      ) : (
+        <TripwireCard report={report} />
+      )}
+    </div>
+  );
+}
+
+/** The calm, quiet treatment — the contaminated "perfect crime" factor was correctly rejected (or ruled
+ *  insufficient), exactly as expected. Styling stays consistent with the rest of the evidence-status
+ *  language: unremarkable, never celebratory hype. */
+function CalmContaminatedCard({ report }: { report: RefereeAuditReport }) {
+  const status = report.contaminated_verdict?.status ?? null;
+  return (
+    <Card data-testid="referee-audit-contaminated-caught">
+      <CardContent className="space-y-2 p-5">
+        <div className="flex items-center gap-2">
+          <ShieldCheck className="h-5 w-5 text-pos" aria-hidden />
+          <h3 className="text-sm font-semibold text-text">Lookahead-contaminated factor: caught</h3>
+        </div>
+        <p className="text-sm text-text-muted">
+          A factor whose value equals its own realized {report.contaminated_factor_horizon ?? "—"}-day
+          forward return (the &quot;perfect crime&quot; a broken harness would certify instantly) was
+          submitted to the referee — expected: {report.contaminated_expected_outcome ?? "rejected"}.
+          Verdict:{" "}
+          <Badge variant={contaminatedStatusVariant(status)} data-testid="referee-audit-contaminated-status">
+            {status ?? "—"}
+          </Badge>
+          .
+        </p>
+        {report.contaminated_verdict?.reason ? (
+          <p className="text-xs text-text-faint">{String(report.contaminated_verdict.reason)}</p>
+        ) : null}
+      </CardContent>
+    </Card>
+  );
+}
+
+/** The LOUD, un-hideable failure state — the contaminated factor was NOT rejected. This is a
+ *  correctness-critical signal (the harness may be leaking), never decoration: prominent red, always
+ *  rendered when `contaminated_caught` is false, never suppressed or softened. */
+function TripwireCard({ report }: { report: RefereeAuditReport }) {
+  const status = report.contaminated_verdict?.status ?? null;
+  return (
+    <Card className="border-neg bg-neg/10" data-testid="referee-audit-tripwire">
+      <CardContent className="flex items-start gap-3 p-6">
+        <AlertTriangle className="h-6 w-6 shrink-0 text-neg" aria-hidden />
+        <div className="space-y-1.5">
+          <h3 className="text-base font-semibold text-neg">
+            Tripwire: the lookahead-contaminated factor was NOT rejected
+          </h3>
+          <p className="text-sm text-neg">
+            A factor whose value equals its own realized {report.contaminated_factor_horizon ?? "—"}-day
+            forward return should have been rejected by the referee (expected:{" "}
+            {report.contaminated_expected_outcome ?? "rejected"}) — instead it certified{" "}
+            <Badge variant={contaminatedStatusVariant(status)} data-testid="referee-audit-contaminated-status">
+              {status ?? "—"}
+            </Badge>
+            . This means the certification harness may be leaking signal it should not — treat every
+            certified claim from this basis with suspicion until this is investigated.
+          </p>
+          {report.contaminated_verdict?.reason ? (
+            <p className="text-xs text-neg/80">{String(report.contaminated_verdict.reason)}</p>
+          ) : null}
+        </div>
+      </CardContent>
+    </Card>
+  );
+}
+
+function StatCard({
+  testId,
+  title,
+  headline,
+  subtext,
+}: {
+  testId: string;
+  title: string;
+  headline: string;
+  subtext: string;
+}) {
+  return (
+    <Card data-testid={testId}>
+      <CardContent className="space-y-2 p-5">
+        <h3 className="text-xs font-medium uppercase tracking-wide text-text-faint">{title}</h3>
+        <p className="num text-2xl font-semibold text-text" data-testid={`${testId}-value`}>
+          {headline}
+        </p>
+        <p className="text-xs text-text-muted">{subtext}</p>
+      </CardContent>
+    </Card>
+  );
+}
+
+function RefereeAuditSkeleton() {
+  return (
+    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="referee-audit-skeleton">
+      {Array.from({ length: 4 }).map((_, i) => (
+        <Card key={i} className="p-5">
+          <div className="space-y-3">
+            <div className={cn("h-3 w-24 animate-pulse rounded bg-surface-2")} />
+            <div className={cn("h-7 w-16 animate-pulse rounded bg-surface-2")} />
+            <div className={cn("h-3 w-full animate-pulse rounded bg-surface-2")} />
+          </div>
+        </Card>
+      ))}
+    </div>
+  );
+}
diff --git a/apps/frontend/lib/referee-audit.ts b/apps/frontend/lib/referee-audit.ts
new file mode 100644
index 0000000..997c09d
--- /dev/null
+++ b/apps/frontend/lib/referee-audit.ts
@@ -0,0 +1,53 @@
+/**
+ * Referee-calibration report types (goal-mcp-loop iter-36, J-22 / backlog B-102).
+ *
+ * Mirrors `lib/budget.ts`'s types-only pattern for the SEPARATE `GET /api/research/referee-audit`
+ * payload — the certifier's own measured empirical false-pass rate (with a binomial CI) against the
+ * configured α over seeded null factors, plus the lookahead-contaminated-factor tripwire result —
+ * computed once by an ISOLATED offline audit job against a throwaway ledger and re-read VERBATIM here.
+ *
+ * This module carries NO proven-language: every figure is descriptive calibration accounting (a trial
+ * count, a false-pass rate, a verdict kind) — never a "Proven"/"Not yet proven" signal. The ONLY source
+ * of "Proven" stays the certified-claims ledger via `lib/evidence.ts` / `GET /api/evidence`; this file
+ * never touches that path, and the audit's throwaway trials never appear there.
+ */
+
+import type { Verdict } from "@/lib/evidence";
+
+/** The lookahead-contaminated factor's referee verdict — the SAME `Verdict` shape a certified-claims row
+ *  carries (status/reason/edge/p-value/etc.), re-displayed verbatim. Its `status` is expected to be
+ *  "FAIL" or "INSUFFICIENT" (caught) but MAY legitimately be "PASS" (the tripwire case) — the page must
+ *  render whichever the artifact actually recorded, never assume it away. */
+export type RefereeAuditContaminatedVerdict = Verdict;
+
+/** One persisted referee-calibration run, read VERBATIM from `GET /api/research/referee-audit`.
+ *  `status === "unreadable"` is the honest degraded-parse state (a corrupt artifact) — every OTHER field
+ *  is `null` in that case; `status === "ok"` is a real, successfully-built run and every field below is
+ *  populated. `contaminated_caught` is the DERIVED boolean (`contaminated_verdict.status !== "PASS"`)
+ *  the page uses to choose its calm vs. its loud tripwire-failure treatment;
+ *  `contaminated_expected_outcome` is always the STATIC label `"rejected"` (a caption, not a claim about
+ *  what happened). */
+export interface RefereeAuditReport {
+  status: "ok" | "unreadable";
+  run_date: string | null;
+  n_null_trials: number | null;
+  seed: number | null;
+  alpha: number | null;
+  source_factor: string | null;
+  false_pass_count: number | null;
+  false_pass_rate: number | null;
+  false_pass_ci_low: number | null;
+  false_pass_ci_high: number | null;
+  n_insufficient_null: number | null;
+  contaminated_factor_horizon: number | null;
+  contaminated_verdict: RefereeAuditContaminatedVerdict | null;
+  contaminated_expected_outcome: "rejected" | null;
+  contaminated_caught: boolean | null;
+}
+
+/** The `GET /api/research/referee-audit` payload: `report` is `null` when the offline harness has never
+ *  run (the honest empty state — distinct from `status === "unreadable"`, which means a run DID happen
+ *  but its artifact could not be parsed). */
+export interface RefereeAuditResponse {
+  report: RefereeAuditReport | null;
+}
```
