# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/README.md b/README.md
index 2f25c2c..469159e 100644
--- a/README.md
+++ b/README.md
@@ -37,9 +37,9 @@ Current capabilities:
 - **Referee audit**: a fourth card, "Referee audit," alongside Pre-registration registry, Negative-results graveyard, and Certification-budget accounting, completes the Research hub's "Governance & process" section as a four-card grid and opens a dedicated `/research/referee-audit` page that asks whether the platform's own statistical certifier can itself be trusted. A four-stat summary row reports the number of deliberately meaningless ("null") signal trials the certifier was tested against and their source factor; the certifier's empirical false-pass rate — how often it wrongly calls a null pattern "real" — with its 95% confidence interval, shown beside the configured significance threshold (α) it is supposed to respect (currently: false-pass rate 0.08 across 200 trials, 95% CI [0.0498, 0.126], against α = 0.05); and the run date plus its seed and horizon parameters. Below that, a single verdict card reports whether an intentionally "cheating" factor — built from its own future outcome, the "perfect crime" a broken certifier would rubber-stamp — was caught and rejected; right now it was not caught, and the page renders that as a loud red "tripwire" warning rather than a quiet pass, with the verdict badge always styled as a failure warning in this case even though the underlying statistical result is technically a "pass." If the backend is unreachable a contained "Backend unavailable" card is shown instead of a broken page. The check itself runs only as an offline, config-seeded job with no in-app trigger; the page always re-reads whatever that job last wrote, and it does not affect any other score, ranking, or evidence status shown elsewhere in the product.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level. A **Concentration X-ray** section below the entries table (shown once at least one stock is saved) answers "how concentrated is my watchlist really?": a ticker-by-ticker correlation heatmap shows exactly how correlated every pair of saved stocks is over a trailing lookback window (126 trading days by default), correlation-threshold clusters group names that move together, and a headline **"effective independent bets"** figure — with its trailing window stated inline — reports how many genuinely different bets the list represents versus how many names are just duplicates of each other in disguise; an info icon opens a plain-language explanation of the methodology and its minimum-history floor. Sector, theme, and shared-setup-status concentration bars sit beneath the matrix, using the same status colours as the entries table's own Setup column. Hovering any matrix cell shows the exact correlation value, or — for a stock without enough price history — the exact reason it reads "not enough data" rather than a guessed number. A watchlist with 0 or 1 saved names shows an honest "not enough names yet for an X-ray" message instead of an empty or broken chart. The section is purely descriptive — read-only, no new controls — and rides the same single watchlist data call the page already made, so it shares the page's existing loading and error states.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
-- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
+- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A completed backfill, Fetch + backfill, or rebuild job's detail also names exactly which stored aggregates that run refreshed — a **"Refreshed: ..."** line (for example "Refreshed: coverage, market phase, membership timeline, research hot keys") shown identically on the live job card, the last-run summary shown when no job has started this browser session, and that run's Run History row — confirming the background bookkeeping actually happened, not just that the job finished; the line is omitted for job kinds that don't refresh those aggregates (a plain fetch or an expand) and for a run that hasn't finished yet. A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
 - **Availability heatmap on Data Manager**: a month-by-month trading-day calendar grid where each day cell is color-coded across a perceptually-ordered six-step blue density scale (dark for empty days through bright blue for fully-covered days) and ringed in violet when a scored snapshot exists for that day — two visually distinct signals that never collide in color. The legend is split into two clearly labeled groups, one for the price-data density scale and one for the scored-snapshot ring, so it is always clear which signal you are reading. Day numbers are clearly legible against every shade of cell (per-bucket design tokens chosen for contrast, no hardcoded hex). Months are ordered newest first and two months appear side by side so you see more history without scrolling. Hovering or focusing any cell shows the exact figures — date, symbols with bars versus total, and whether a snapshot exists — worded to name which action is responsible (for example, a day with price data but no snapshot yet reads as a backfill gap, while a scored day reads as a snapshot produced by backfill). Clicking a day prefills the job form's Start and End date inputs; shift-clicking a second day fills in a date range. The heatmap refreshes automatically after any data job completes or data is removed, so coverage changes are always visible immediately.
-- **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports three honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), or **Backend unavailable** (red) — whether the app is opened at `localhost` or the machine's local network (LAN) address. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one; memory is bounded to one shared copy of the dataset regardless of how many people are connected at once; opening the Data Manager page for the first time after a restart, or several people opening it at once, now reliably finishes loading in roughly 10-20 seconds instead of risking a memory-exhaustion hang, because its price-history load streams data in smaller chunks rather than reading everything at once; and the start script enforces hard limits on concurrent connections, request timeouts, and process memory so that a traffic spike isolates to one process without freezing the host machine.
+- **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports three honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), or **Backend unavailable** (red) — whether the app is opened at `localhost` or the machine's local network (LAN) address. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one, and memory is bounded to one shared copy of the dataset regardless of how many people are connected at once. The Data page's coverage panel is no longer computed live at all on the common path: every backfill, Fetch + backfill, or rebuild job refreshes a stored coverage snapshot (plus market phase, the membership timeline, and research hot-key caches) the moment it finishes, so a cold `/data` load now completes in well under a second — down from roughly 9-10 seconds previously — and stepping the as-of switcher to any already-ingested historical date shows that date's own correct, non-zero coverage rather than a blank panel; a genuinely brand-new, never-ingested database instead shows an honest all-zero state that fills itself in within seconds of boot, with no hang, crash, or manual step required. The start script enforces the process's configured memory ceiling and writes a permanent, append-only startup/crash log to disk (`logs/backend.log`), so a crash always leaves a readable trace even though neither the memory cap nor the log file has any on-screen representation.
 - **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale, or a live Fetch's freshly-pulled prices disagreeing with the platform's saved, committed reference history — a "live-vs-seed drift" / adjustment seam), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
 - **Contained error recovery**: if an unexpected error occurs on any page, the app shows a calm "Something went wrong on this page" message with a "Try again" button instead of going blank — the sidebar and header stay visible and usable while you retry or navigate elsewhere. In the rare case where the outer application shell itself fails, a simple fallback page appears instead of a blank browser tab.
 <!-- /AUTO:capabilities -->
@@ -79,8 +79,9 @@ git subtree push --prefix incredible_auto_dev auto_dev main
 
 <!-- TODO: .claude/project-template.md is still the unfilled generic template (Stack / Test commands /
      Service start commands / Services are all placeholders) — the commands below are maintained
-     directly against this repo's own scripts and configs (scripts/dev.sh, apps/backend/requirements.txt,
-     apps/frontend/package.json) pending that file being filled in for this project. -->
+     directly against this repo's own scripts and configs (scripts/dev.sh, scripts/start-backend.sh,
+     scripts/start-frontend.sh, apps/backend/requirements.txt, apps/frontend/package.json) pending that
+     file being filled in for this project. -->
 
 ### Prerequisites
 
@@ -126,6 +127,21 @@ cd apps/frontend
 NEXT_PUBLIC_API_URL=http://localhost:8255 npx next dev -p 3255
 ```
 
+### Start backend + frontend (hardened, no auto-reload)
+
+```bash
+bash scripts/start-backend.sh
+bash scripts/start-frontend.sh
+```
+
+Same ports as `./scripts/dev.sh` (deterministic per-project offset; override with
+`CHAIN_BACKEND_PORT` / `CHAIN_FRONTEND_PORT`). Differences from the quick-start/manual
+commands above: `start-backend.sh` runs pending Alembic migrations first, does not
+auto-reload on file changes, applies the memory ceiling and `MALLOC_ARENA_MAX` declared in
+`config.yaml` to the process, and appends every boot's output to a permanent, git-ignored
+log file at `logs/backend.log` — so a crash always leaves a readable trace (boot lines with
+no matching clean-shutdown line) even with no terminal left open to read it from.
+
 ### Run backend tests
 
 ```bash
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index 9f6b7cd..82729c9 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -985,20 +985,20 @@ def _coverage_not_yet_computed_payload(cfg: Config) -> dict:
 def _upsert_coverage_snapshot(
     session: Session, asof_key: str, dataset_version: str, payload: dict
 ) -> None:
-    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: prunes any
-    STALE row for this `asof_key` (an older `dataset_version`), then updates the current-stamp row in
-    place if one already exists or inserts a fresh one. Mirrors `market_phase_cached`'s prune-stale-then-
-    write upsert, generalized to also cover a repeat call under the SAME stamp — this is called
-    unconditionally at the end of every successful ingest (not gated behind a cache-miss check, unlike the
-    `*_cached` read-through caches)."""
-    stale = session.exec(
-        select(CoverageSnapshot).where(
-            CoverageSnapshot.asof_key == asof_key,
-            CoverageSnapshot.dataset_version != dataset_version,
-        )
-    ).all()
-    for row in stale:
-        session.delete(row)
+    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: reclaims
+    EVERY row in the table left under a superseded `dataset_version` — ops-hardening iter-3 (B2), widened
+    from the iter-2 original, which pruned only a stale row for THIS SAME `asof_key` and left every OTHER
+    `asof_key`'s row under an old stamp orphaned forever once the dataset version moved on — then updates
+    the current-stamp row in place if one already exists or inserts a fresh one. The reclaim is ONE bounded
+    SQL `DELETE ... WHERE dataset_version != :current` (never a per-row Python scan), so it stays cheap
+    regardless of how many stale `asof_key` rows have accumulated (this table is small — bounded by the
+    handful of distinct as-of dates ever selected — never the multi-million-row `daily_prices` scale AG-8
+    guards against). Mirrors `market_phase_cached`'s prune-stale-then-write upsert, generalized to also
+    cover a repeat call under the SAME stamp — this is called unconditionally at the end of every
+    successful ingest (not gated behind a cache-miss check, unlike the `*_cached` read-through caches).
+    Shared by every caller — the ingest finalize hook's rich backfill/rebuild path AND its fetch/expand
+    path (B1), plus `warmup.py`'s boot safety net — so all benefit automatically from one shared fix."""
+    session.execute(delete(CoverageSnapshot).where(CoverageSnapshot.dataset_version != dataset_version))
 
     existing = session.exec(
         select(CoverageSnapshot).where(
@@ -1043,18 +1043,44 @@ def refresh_coverage_snapshot(session: Session, cfg: Config) -> Optional[dict]:
     """Compute the CURRENT coverage payload (reusing the canonical `_compute_coverage_uncached` verbatim —
     never a second derivation) and persist it as the `CoverageSnapshot` row for the CURRENT `(asof_key,
     dataset_version)` key, upserting idempotently. Called by the ingest finalize hook (unconditionally, on
-    every successful backfill/both/rebuild — including a zero-work re-run) and the boot warm-up safety net
-    (only when no row exists yet for the current stamp). Returns the freshly persisted payload, or `None`
-    on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns None only then; nothing to
-    snapshot yet). The current stamp resolves `None`→latest, so this is `refresh_coverage_snapshot_for` at
-    that resolved date (byte-identical: `_compute_coverage_uncached(as_of=None)` and `(as_of=latest)` both
-    resolve through `_resolve_coverage_asof` to the SAME latest date)."""
+    every successful backfill/both/rebuild — including a zero-work re-run — AND, ops-hardening iter-3 B1,
+    on a successful fetch/expand that the cheap `_coverage_snapshot_is_current` gate below found stale) and
+    the boot warm-up safety net (only when no row exists yet for the current stamp). Returns the freshly
+    persisted payload, or `None` on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns
+    None only then; nothing to snapshot yet). The current stamp resolves `None`→latest, so this is
+    `refresh_coverage_snapshot_for` at that resolved date (byte-identical: `_compute_coverage_uncached
+    (as_of=None)` and `(as_of=latest)` both resolve through `_resolve_coverage_asof` to the SAME latest
+    date)."""
     resolved_asof = _resolve_coverage_asof(session, None, cfg)
     if resolved_asof is None:
         return None
     return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
 
 
+def _coverage_snapshot_is_current(session: Session, cfg: Config) -> bool:
+    """ops-hardening iter-3 (B1) — the cheap "already fresh" gate the fetch/expand finalize branch checks
+    BEFORE ever calling `refresh_coverage_snapshot` (which would invoke the heavy `_compute_coverage_uncached`
+    whole-bar-cache derivation): true iff a `CoverageSnapshot` row already exists for the CURRENT `(asof_key,
+    dataset_version)` key, i.e. the persisted snapshot already reflects this exact dataset version, so a
+    refresh would be redundant. Issues only the SAME cheap resolve `refresh_coverage_snapshot` itself needs
+    (`_resolve_coverage_asof` — a couple of bounded scalar reads, never a table scan) plus one indexed row
+    lookup — it NEVER invokes `_compute_coverage_uncached` (the zero-work fetch call-count contract, TC-2).
+    A wholly-empty DB (`resolved_asof is None`) has nothing to snapshot yet — treated as "already current"
+    (a no-op), mirroring `refresh_coverage_snapshot`'s own no-op contract for that case."""
+    resolved_asof = _resolve_coverage_asof(session, None, cfg)
+    if resolved_asof is None:
+        return True
+    asof_key = resolved_asof.isoformat()
+    dataset_version = _membership_dataset_version(session, cfg)
+    row = session.exec(
+        select(CoverageSnapshot).where(
+            CoverageSnapshot.asof_key == asof_key,
+            CoverageSnapshot.dataset_version == dataset_version,
+        )
+    ).first()
+    return row is not None
+
+
 def _scanner_run_exists(session: Session, asof: date_cls) -> bool:
     """Whether a real `ScannerRun` snapshot exists for exactly this as-of date — the signal that `asof` is
     genuinely-ingested historical data (the app-wide as-of switcher, `GET /api/runs`, only ever offers such
@@ -3764,6 +3790,27 @@ def _run_job(
                         prog.aggregates_refreshed = _refresh_ingest_aggregates(agg_session, cfg, prog)
                 except Exception as exc:  # noqa: BLE001 — non-fatal: never flips a successful job to failed
                     logger.exception("ingest aggregate refresh failed (non-fatal): %s", exc)
+            elif final_status in ("ok", "partial") and (
+                prog.kind in _FETCH_KINDS or prog.kind in _EXPAND_KINDS
+            ):
+                # ops-hardening iter-3 (B1): a pure fetch/expand does not run the rich backfill-style hook
+                # above (no per-date snapshot loop, no market-phase/research-hot-key warm — not asked for
+                # here — `elif` naturally excludes "both", which is ALSO in `_BACKFILL_KINDS` and already
+                # ran through the branch above), but it CAN change the bars/membership manifest
+                # (`_membership_dataset_version`), which silently staled the persisted `coverage_snapshot`
+                # row `GET /api/data`'s default view reads — until this fix, only an unrelated restart or
+                # backfill/rebuild ever refreshed it (audit finding B1). Calls `refresh_coverage_snapshot`
+                # directly (the SAME canonical compute the rich path uses) — never a second derivation —
+                # gated by `_coverage_snapshot_is_current` so a zero-work fetch (the common offline case)
+                # pays no extra compute/write (TC-2). Deliberately does NOT set `prog.aggregates_refreshed`
+                # — that field's existing backfill/both/rebuild-only nullability contract is unchanged
+                # (already gated to null for fetch/expand via `_breakdown_computed`, `_run_detail` above).
+                try:
+                    with Session(eng) as agg_session:
+                        if not _coverage_snapshot_is_current(agg_session, cfg):
+                            refresh_coverage_snapshot(agg_session, cfg)
+                except Exception as exc:  # noqa: BLE001 — non-fatal: never flips a successful job to failed
+                    logger.exception("ingest coverage refresh failed for fetch/expand (non-fatal): %s", exc)
             prog.status = final_status
     except Exception as exc:  # noqa: BLE001 — any failure must surface as an explicit failed job (scrubbed)
         prog.status = "failed"
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index 4933157..9b02846 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -1303,6 +1303,205 @@ def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
     assert this_run["aggregates_refreshed"] is None  # the persisted/served view: null for a fetch kind
 
 
+# ==================================================================================================
+# ops-hardening iter-3 (audit B1/B2): a fetch/expand that changes the bars manifest must ALSO refresh the
+# persisted coverage_snapshot (today only backfill/both/rebuild do) — closing the fetch-then-view gap the
+# iter-2 audit found live: a fully-ingested DB silently kept serving the false all-zero sentinel until an
+# unrelated restart or backfill/rebuild. A zero-work fetch/expand (the common offline case) must pay ZERO
+# extra compute. Stale coverage_snapshot rows under a superseded dataset_version must be reclaimed in one
+# bounded SQL DELETE, across every asof_key, not just the one being written (B2).
+# ==================================================================================================
+def test_fetch_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
+    """TC-1/TC-6 (B1) — given a committed DB with a current-stamp coverage_snapshot row already persisted,
+    when a `fetch` job lands >= 1 new bar (changing `_membership_dataset_version`) and completes, the
+    finalize hook persists a FRESH coverage_snapshot row for the new current stamp, and
+    `coverage_from_storage` (what `GET /api/data`'s default view reads) serves the fresh symbol_count —
+    byte-identical to an independent fresh `_compute_coverage_uncached` call — never the stale pre-fetch
+    value."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_refresh.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 1, 2)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    cfg = load_config()
+
+    with Session(engine) as session:
+        pre_payload = data_manager.refresh_coverage_snapshot(session, cfg)  # the pre-existing current row
+        pre_version = data_manager._membership_dataset_version(session, cfg)
+    assert pre_payload["symbol_count"] == 1  # SPY only, before the fetch
+
+    class _OneBarProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return [Bar(date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0)]
+
+    # J-13: an empty temp seed_dir degrades the fetch target to the small context-only set (fast/small),
+    # exactly the pattern `test_fetch_forced_failure_writes_no_bars_or_snapshots` already relies on.
+    job = create_job("fetch", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_OneBarProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "ok"
+    assert summary["bars_fetched"] > 0
+
+    with Session(engine) as session:
+        new_version = data_manager._membership_dataset_version(session, cfg)
+        assert new_version != pre_version  # real new bars landed -> the stamp actually changed
+
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1  # the stale pre-fetch-stamp row was reclaimed (B2), not left alongside
+        assert rows[0].dataset_version == new_version
+        stored = json.loads(rows[0].payload_json)
+        assert stored["symbol_count"] > 1  # more than SPY alone -- the fresh count, not the stale 1
+
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+        assert stored == fresh  # TC-6: byte-identical to an independent fresh compute
+        served = data_manager.coverage_from_storage(session, cfg, as_of=None)  # GET /api/data's default read
+        assert served == fresh
+
+
+def test_zero_work_fetch_skips_coverage_recompute_and_row_write(tmp_path, monkeypatch):
+    """TC-2 — given the same setup as TC-1 but the fetch lands ZERO new bars (the common offline no-op),
+    `_compute_coverage_uncached` is NEVER invoked (a call-count assertion — the 'already fresh' gate must
+    resolve off the cheap dataset-version comparison + one row lookup alone) and no coverage_snapshot row
+    is written or re-timestamped."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_zero_work.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 1, 2)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    cfg = load_config()
+
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, cfg)  # the pre-existing current-stamp row
+        rows_before = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows_before) == 1
+        computed_at_before = rows_before[0].computed_at
+
+    calls: list[int] = []
+    orig = data_manager._compute_coverage_uncached
+
+    def _counting(*args, **kwargs):
+        calls.append(1)
+        return orig(*args, **kwargs)
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _counting)
+
+    class _EmptyProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return []  # a successful fetch that finds no new bars -- never a fabricated one
+
+    job = create_job("fetch", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_EmptyProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "ok"
+    assert summary["bars_fetched"] == 0
+    assert calls == []  # never invoked -- the skip gate resolved first, off the stamp comparison alone
+
+    with Session(engine) as session:
+        rows_after = session.exec(select(CoverageSnapshot)).all()
+    assert len(rows_after) == 1
+    assert rows_after[0].computed_at == computed_at_before  # untouched -- no re-timestamp
+
+
+def test_fully_failed_fetch_writes_no_coverage_snapshot(tmp_path):
+    """Error case (TESTING REQUIREMENTS) — a fetch that fails for every symbol must not leave a
+    partially-written/inconsistent coverage_snapshot row: `final_status == "failed"` never reaches the new
+    refresh branch (it is gated the same as the existing backfill/rebuild branch: `ok`/`partial` only)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_failed.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+    cfg = load_config()
+
+    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_FailingProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "failed"
+    with Session(engine) as session:
+        assert session.exec(select(CoverageSnapshot)).all() == []
+
+
+def test_stale_dataset_version_rows_pruned_via_one_bulk_delete(tmp_path):
+    """TC-4 (B2) — multiple coverage_snapshot rows under a now-superseded dataset_version, across DIFFERENT
+    asof_keys, are ALL deleted the next time a write detects the dataset version has changed -- via one
+    bounded SQL DELETE (asserted by counting DELETE statements against coverage_snapshot), not a per-row
+    Python scan."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'stale_prune.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        # three rows under an OLD stamp, across three DIFFERENT asof_keys -- today's per-asof_key-only
+        # prune would leave two of these three orphaned forever (the B2 bug).
+        for asof_key in ("2024-01-01", "2024-02-01", "2024-03-01"):
+            session.add(CoverageSnapshot(
+                asof_key=asof_key, dataset_version="old-v1", payload_json="{}",
+                computed_at=datetime(2024, 1, 1),
+            ))
+        session.commit()
+
+    delete_statements: list[str] = []
+
+    def _count_deletes(conn, cursor, statement, parameters, context, executemany):
+        lowered = statement.lower()
+        if "coverage_snapshot" in lowered and lowered.strip().startswith("delete"):
+            delete_statements.append(statement)
+
+    event.listen(engine, "before_cursor_execute", _count_deletes)
+    try:
+        with Session(engine) as session:
+            # a write under a NEW dataset_version, for a FOURTH, different asof_key.
+            data_manager._upsert_coverage_snapshot(session, "2024-04-01", "new-v2", {"fake": "payload"})
+    finally:
+        event.remove(engine, "before_cursor_execute", _count_deletes)
+
+    assert len(delete_statements) == 1  # ONE bounded SQL DELETE -- not a per-row scan
+
+    with Session(engine) as session:
+        rows = session.exec(select(CoverageSnapshot)).all()
+    assert len(rows) == 1  # every old-v1 row (all three asof_keys) reclaimed; only the new row remains
+    assert rows[0].asof_key == "2024-04-01" and rows[0].dataset_version == "new-v2"
+
+
+def test_fetch_coverage_refresh_makes_no_network_call(tmp_path, monkeypatch):
+    """TC-7 (AG-9) — the widened finalize trigger for a fetch that lands a new bar issues ZERO outbound
+    network/socket calls during the whole job (the stub provider itself is offline; the new coverage-
+    refresh branch reuses only DB-backed derivations)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_no_network.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 1, 2)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+    cfg = load_config()
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, cfg)
+
+    def _no_network(*_a, **_k):
+        raise AssertionError("unexpected network call during the fetch coverage refresh")
+
+    monkeypatch.setattr(socket.socket, "connect", _no_network)
+
+    class _OneBarProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return [Bar(date=d, open=2.0, high=2.0, low=2.0, close=2.0, volume=2.0)]
+
+    job = create_job("fetch", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_OneBarProvider(),
+        sleep_fn=_noop_sleep, seed_dir=tmp_path,
+    )
+    assert summary["status"] == "ok"  # completed successfully with zero socket.connect calls
+
+
 # ==================================================================================================
 # iter-2 review (CRITICAL regression): the app-wide as-of switcher (J-93/J-94) must serve REAL coverage
 # for EVERY already-ingested date — not just the DB's single current stamp. Before the fix, only the
@@ -2168,6 +2367,51 @@ def test_expand_kind_is_in_job_kinds():
     assert "expand" in data_manager.JOB_KINDS
 
 
+def test_expand_that_lands_new_bar_refreshes_coverage_snapshot(tmp_path):
+    """TC-3/TC-6 (B1) — an `expand` job whose bars manifest changes (a new passer's history is added)
+    triggers the SAME fetch-path finalize behavior as a plain fetch: a fresh coverage_snapshot row is
+    persisted for the current stamp, byte-identical to a direct fresh `_compute_coverage_uncached` call."""
+    cfg = load_config()
+    # job-mechanics tests are cadence-independent: neutralize the iter-18 deep-history snapshot
+    # cadence so every trading day in the chosen range is a valid target (the mechanics under test
+    # are create-once/isolation/parallelism, not the bounded-density policy).
+    _sc = cfg.scanner.model_copy(update={"snapshot_cadence": cfg.scanner.snapshot_cadence.model_copy(update={"daily_start": None})})
+    cfg = cfg.model_copy(update={"scanner": _sc})
+    seed_dir = tmp_path / "seed"
+    _write_pool(seed_dir)
+    engine = make_engine(f"sqlite:///{tmp_path / 'expand_refresh.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 3, 1)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        pre_payload = data_manager.refresh_coverage_snapshot(session, cfg)
+        pre_version = data_manager._membership_dataset_version(session, cfg)
+    assert pre_payload["symbol_count"] == 1  # SPY only, before the expand lands any passer bars
+
+    job = create_job("expand", d, d, source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_ExpandProvider(),
+        sleep_fn=_noop_sleep, seed_dir=seed_dir,
+    )
+    assert summary["status"] == "partial"  # FETCHFAIL's OHLCV fetch fails; the two passers still land bars
+    assert summary["passers"] == 2
+
+    with Session(engine) as session:
+        new_version = data_manager._membership_dataset_version(session, cfg)
+        assert new_version != pre_version
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1  # the stale pre-expand-stamp row was reclaimed (B2), not left alongside
+        assert rows[0].dataset_version == new_version
+        stored = json.loads(rows[0].payload_json)
+        # SPY + every candidate whose OHLCV fetch succeeded (5 of 6 — FETCHFAIL's fetch itself fails, so it
+        # stores no bar; the other four are OMITTED by the screen but still get their fetched bar stored,
+        # per test_expand_omitted_candidates_contribute_no_member_and_no_fabricated_bar's own contract).
+        assert stored["symbol_count"] == 6
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+        assert stored == fresh  # TC-6: byte-identical to an independent fresh compute
+
+
 class _ExpandCap429Provider(PriceProvider):
     """An expand provider whose OHLCV fetch always succeeds but whose market-cap feed is PERSISTENTLY
     rate-limited — so the screen step pauses the expand gracefully `resumable` (never fabricates a cap)."""
```
