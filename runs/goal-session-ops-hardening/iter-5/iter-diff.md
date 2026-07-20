# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/README.md b/README.md
index 4642963e..7bee3bce 100644
--- a/README.md
+++ b/README.md
@@ -37,9 +37,9 @@ Current capabilities:
 - **Referee audit**: a fourth card, "Referee audit," alongside Pre-registration registry, Negative-results graveyard, and Certification-budget accounting, completes the Research hub's "Governance & process" section as a four-card grid and opens a dedicated `/research/referee-audit` page that asks whether the platform's own statistical certifier can itself be trusted. A four-stat summary row reports the number of deliberately meaningless ("null") signal trials the certifier was tested against and their source factor; the certifier's empirical false-pass rate — how often it wrongly calls a null pattern "real" — with its 95% confidence interval, shown beside the configured significance threshold (α) it is supposed to respect (currently: false-pass rate 0.08 across 200 trials, 95% CI [0.0498, 0.126], against α = 0.05); and the run date plus its seed and horizon parameters. Below that, a single verdict card reports whether an intentionally "cheating" factor — built from its own future outcome, the "perfect crime" a broken certifier would rubber-stamp — was caught and rejected; right now it was not caught, and the page renders that as a loud red "tripwire" warning rather than a quiet pass, with the verdict badge always styled as a failure warning in this case even though the underlying statistical result is technically a "pass." If the backend is unreachable a contained "Backend unavailable" card is shown instead of a broken page. The check itself runs only as an offline, config-seeded job with no in-app trigger; the page always re-reads whatever that job last wrote, and it does not affect any other score, ranking, or evidence status shown elsewhere in the product.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level. A **Concentration X-ray** section below the entries table (shown once at least one stock is saved) answers "how concentrated is my watchlist really?": a ticker-by-ticker correlation heatmap shows exactly how correlated every pair of saved stocks is over a trailing lookback window (126 trading days by default), correlation-threshold clusters group names that move together, and a headline **"effective independent bets"** figure — with its trailing window stated inline — reports how many genuinely different bets the list represents versus how many names are just duplicates of each other in disguise; an info icon opens a plain-language explanation of the methodology and its minimum-history floor. Sector, theme, and shared-setup-status concentration bars sit beneath the matrix, using the same status colours as the entries table's own Setup column. Hovering any matrix cell shows the exact correlation value, or — for a stock without enough price history — the exact reason it reads "not enough data" rather than a guessed number. A watchlist with 0 or 1 saved names shows an honest "not enough names yet for an X-ray" message instead of an empty or broken chart. The section is purely descriptive — read-only, no new controls — and rides the same single watchlist data call the page already made, so it shares the page's existing loading and error states.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
-- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A completed backfill, Fetch + backfill, or rebuild job's detail also names exactly which stored aggregates that run refreshed — a **"Refreshed: ..."** line (for example "Refreshed: coverage, market phase, membership timeline, research hot keys") shown identically on the live job card, the last-run summary shown when no job has started this browser session, and that run's Run History row — confirming the background bookkeeping actually happened, not just that the job finished; a plain fetch or an expand job now refreshes those same stored aggregates too, and the Data page's coverage numbers reflect it immediately — live in the same tab once the job finishes, and again on the next page reload — but this particular status line stays reserved for the backfill/rebuild family: it is omitted for a fetch or expand run, and for any run that hasn't finished yet. A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. A full rebuild across the platform's entire up-to-30-year, whole-symbol-universe dataset has now been live-measured end to end (a real run took about 16 minutes): memory stayed roughly 41% under the backend's configured ceiling throughout and the backend never crashed or stopped responding; the one caveat found is that the health check can occasionally take up to about 3 seconds (versus its usual under-1-second) during the busiest opening minutes of the job — every single check still succeeded, and response times settle back down for the rest of the run. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
+- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold — staying accurate through a large job's entire final aggregate-refresh stretch, so a healthy job never falsely reads "possibly stalled" near the end — and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A completed backfill, Fetch + backfill, or rebuild job's detail also names exactly which stored aggregates that run refreshed — a **"Refreshed: ..."** line (for example "Refreshed: coverage, market phase, membership timeline, research hot keys") shown identically on the live job card, the last-run summary shown when no job has started this browser session, and that run's Run History row — confirming the background bookkeeping actually happened, not just that the job finished; a plain fetch or an expand job now refreshes those same stored aggregates too, and the Data page's coverage numbers reflect it immediately — live in the same tab once the job finishes, and again on the next page reload — but this particular status line stays reserved for the backfill/rebuild family: it is omitted for a fetch or expand run, and for any run that hasn't finished yet. A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. A full rebuild across the platform's entire up-to-30-year, whole-symbol-universe dataset has now been live-measured end to end (a real run took about 16 minutes): memory stayed roughly 41% under the backend's configured ceiling throughout and the backend never crashed or stopped responding; the one caveat found is that the health check can occasionally take up to about 3 seconds (versus its usual under-1-second) during the busiest opening minutes of the job — every single check still succeeded, and response times settle back down for the rest of the run. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
 - **Availability heatmap on Data Manager**: a month-by-month trading-day calendar grid where each day cell is color-coded across a perceptually-ordered six-step blue density scale (dark for empty days through bright blue for fully-covered days) and ringed in violet when a scored snapshot exists for that day — two visually distinct signals that never collide in color. The legend is split into two clearly labeled groups, one for the price-data density scale and one for the scored-snapshot ring, so it is always clear which signal you are reading. Day numbers are clearly legible against every shade of cell (per-bucket design tokens chosen for contrast, no hardcoded hex). Months are ordered newest first and two months appear side by side so you see more history without scrolling. Hovering or focusing any cell shows the exact figures — date, symbols with bars versus total, and whether a snapshot exists — worded to name which action is responsible (for example, a day with price data but no snapshot yet reads as a backfill gap, while a scored day reads as a snapshot produced by backfill). Clicking a day prefills the job form's Start and End date inputs; shift-clicking a second day fills in a date range. The heatmap refreshes automatically after any data job completes or data is removed, so coverage changes are always visible immediately.
-- **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports three honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), or **Backend unavailable** (red) — whether the app is opened at `localhost` or the machine's local network (LAN) address. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one, and memory is bounded to one shared copy of the dataset regardless of how many people are connected at once. The Data page's coverage panel is no longer computed live at all on the common path: every fetch, backfill, Fetch + backfill, or rebuild job that actually lands new price data refreshes a stored coverage snapshot (plus market phase, the membership timeline, and research hot-key caches) the moment it finishes — a job that finds nothing new to add skips this refresh at no extra cost or delay — so a cold `/data` load now completes in well under a second — down from roughly 9-10 seconds previously — and stepping the as-of switcher to any already-ingested historical date shows that date's own correct, non-zero coverage rather than a blank panel; a genuinely brand-new, never-ingested database instead shows an honest all-zero state that fills itself in within seconds of boot, with no hang, crash, or manual step required. The start script enforces the process's configured memory ceiling and writes a permanent, append-only startup/crash log to disk (`logs/backend.log`), so a crash always leaves a readable trace even though neither the memory cap nor the log file has any on-screen representation.
+- **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports four honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), **Snapshot pending** (a calm, steady accent-coloured state, visually distinct from both Initializing and Backend unavailable, shown when a new price bar has landed for the platform's benchmark index but hasn't yet been folded into a snapshot — it names the pending date and the recovery action, "run a backfill or rebuild on Data Manager to produce it"), or **Backend unavailable** (red, reserved for a genuinely unreachable backend or a database that has never produced a single scan) — whether the app is opened at `localhost` or the machine's local network (LAN) address. An everyday fetch for any ordinary (non-benchmark) stock never changes the badge at all, and the small "provider", "seed date", and "N symbols" badges beside the status pill refresh automatically whenever the pill's own state changes, not only once per page load. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one, and memory is bounded to one shared copy of the dataset regardless of how many people are connected at once. The Data page's coverage panel is no longer computed live at all on the common path: every fetch, backfill, Fetch + backfill, or rebuild job that actually lands new price data refreshes a stored coverage snapshot (plus market phase, the membership timeline, and research hot-key caches) the moment it finishes — a job that finds nothing new to add skips this refresh at no extra cost or delay — so a cold `/data` load now completes in well under a second — down from roughly 9-10 seconds previously — and stepping the as-of switcher to any already-ingested historical date shows that date's own correct, non-zero coverage rather than a blank panel; a genuinely brand-new, never-ingested database instead shows an honest all-zero state that fills itself in within seconds of boot, with no hang, crash, or manual step required. The start script enforces the process's configured memory ceiling and writes a permanent, append-only startup/crash log to disk (`logs/backend.log`), so a crash always leaves a readable trace even though neither the memory cap nor the log file has any on-screen representation.
 - **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale, or a live Fetch's freshly-pulled prices disagreeing with the platform's saved, committed reference history — a "live-vs-seed drift" / adjustment seam), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
 - **Contained error recovery**: if an unexpected error occurs on any page, the app shows a calm "Something went wrong on this page" message with a "Try again" button instead of going blank — the sidebar and header stay visible and usable while you retry or navigate elsewhere. In the rare case where the outer application shell itself fails, a simple fallback page appears instead of a blank browser tab.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/app/api/backtest.py b/apps/backend/app/api/backtest.py
index 0a20a844..82c2b785 100644
--- a/apps/backend/app/api/backtest.py
+++ b/apps/backend/app/api/backtest.py
@@ -36,8 +36,8 @@ from app.config import Config, get_config
 from app.db import get_session
 from app.engine.forward_testing import (
     backfill_run_forward_returns,
-    compute_forward_aggregates,
     compute_run_scorecard,
+    forward_aggregates_cached,
 )
 from app.engine.scanner import _latest_stored_run_date
 from app.engine.snapshot_serving import resolved_run
@@ -65,8 +65,11 @@ def backtest(
     # is scoped to the EXPANDING WINDOW of snapshots dated <= the resolved run's asof_date (the SAME global
     # as-of already resolved — no second date control, J-18). Read-only grouping over the stored
     # forward_returns — recomputes no return/score/bucket (the same model the retired System Health used).
+    # ops-hardening iter-5 (J-06): served from the ingest-warmed cache (byte-identical to a fresh compute;
+    # `compute_forward_aggregates` itself is unchanged and stays the sole producer) — a live 5-horizon
+    # request here measured 34.77s pre-fix (reports/perf-budgets.md).
     evidence_by_horizon = {
-        h: compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)
+        h: forward_aggregates_cached(session, h, cfg, as_of=run.asof_date)
         for h in cfg.walk_forward.horizons
     }
     # `is_latest` reuses the canonical "latest stored run date" (no second query/source for it).
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index d1fdd8ce..ef226f09 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -1884,9 +1884,9 @@ class JobProgress:
     # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
     # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
     # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
-    # "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` it actually refreshed —
-    # empty/default until the hook has actually run (never fabricated on an interrupted/failed row; gated
-    # in `_run_detail()` the SAME way `calendar_days` etc. already are).
+    # "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]` it
+    # actually refreshed — empty/default until the hook has actually run (never fabricated on an
+    # interrupted/failed row; gated in `_run_detail()` the SAME way `calendar_days` etc. already are).
     new_snapshot_dates: list[date_cls] = field(default_factory=list)
     aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
@@ -3047,9 +3047,9 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
     `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
     flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
-    "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` ACTUALLY refreshed — never a
-    fabricated category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this
-    module).
+    "coverage", "membership_timeline", "market_phase", "forward_aggregates", "research_hot_keys"]`
+    ACTUALLY refreshed — never a fabricated category (mirrors the `omitted`/`passers` honesty convention
+    already used elsewhere in this module).
 
     ops-hardening iter-4 (F1 fix): calls the bare `prog.tick()` (no `activity` argument — it stamps ONLY
     the `last_progress_at` heartbeat, never overwriting `current_activity`, so an already-pinned "scanning
@@ -3103,6 +3103,32 @@ def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress)
     if market_phase_warmed:
         refreshed.append("market_phase")
 
+    # ops-hardening iter-5 (J-06): warm the CURRENT latest stored run's per-horizon forward-aggregate
+    # cache (GET /api/backtest's `evidence_by_horizon`, ~34.77s pre-fix over all 5 configured horizons —
+    # reports/perf-budgets.md). Unconditional (not gated on `prog.new_snapshot_dates`, unlike the
+    # per-date coverage/market-phase loops above): the dataset-version stamp is GLOBAL, so ANY ingest
+    # anywhere (even a historical-gap backfill far from the latest date) can invalidate the latest run's
+    # already-cached aggregate — e.g. a backfilled EARLIER date's forward returns newly enter the
+    # latest as-of's expanding "<= D" window. Warming only the ONE current-latest key (not every
+    # historical as-of) mirrors the "research_hot_keys" default-key philosophy just below, not the
+    # per-date coverage/market-phase sweep — each per-horizon compute can itself be as expensive as the
+    # measured 34.77s violation, so sweeping every `new_snapshot_dates` entry here (as coverage/
+    # market_phase do) would risk turning a full-universe rebuild's finalize tail into a multi-hour
+    # operation instead of the intended fix. A user-navigated HISTORICAL as-of on `/backtest` still
+    # computes-once-and-caches on first view (the same cold-miss contract EventStudyCache/
+    # MarketPhaseCache already carry) — never pre-warmed here.
+    try:
+        latest_run_date = scanner._latest_stored_run_date(session)
+        if latest_run_date is not None:
+            for h in cfg.walk_forward.horizons:
+                prog.tick()  # F1-style heartbeat stamp before each horizon's compute (a cold-cache
+                             # compute here can take up to ~35s pre-warm; 5 sequential horizons could
+                             # otherwise freeze the heartbeat for minutes without a per-horizon tick).
+                forward_testing.forward_aggregates_cached(session, h, cfg, as_of=latest_run_date)
+            refreshed.append("forward_aggregates")
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest forward-aggregate warm failed (non-fatal): %s", exc)
+
     try:
         subjects = subject_catalog(cfg)
         if subjects:
diff --git a/apps/backend/app/engine/forward_testing.py b/apps/backend/app/engine/forward_testing.py
index 043c6936..9436658f 100644
--- a/apps/backend/app/engine/forward_testing.py
+++ b/apps/backend/app/engine/forward_testing.py
@@ -49,7 +49,7 @@ from app.config import Config, get_config
 from app.engine.prices import bars_after, bars_asof, close_on, latest_data_date
 from app.engine.scanner import run_scan
 from app.engine.setups import ALL_STATUSES
-from app.models import EventStudyCache, ForwardReturn, ScannerResult, ScannerRun
+from app.models import EventStudyCache, ForwardAggregateCache, ForwardReturn, ScannerResult, ScannerRun
 
 # The honest caveat carried on every payload (anti-goal: Honest limitations surfaced). iter-18: the
 # basis now spans ~30 years (1996 -> present, per-name real listing depth) over the broadened
@@ -936,6 +936,79 @@ def compute_forward_aggregates(
     }
 
 
+def forward_aggregates_cached(
+    session: Session, horizon: int, config: Optional[Config] = None, *, as_of: Optional[date_cls] = None,
+) -> dict:
+    """Serve `compute_forward_aggregates` from an ingest-time warm cache (ops-hardening iter-5, J-06),
+    mirroring `research.event_study_cached` / `market_phase.market_phase_cached`: on a cache HIT for the
+    current `(horizon, asof_key, dataset_version)` key, deserialize and return the stored aggregate (NO
+    recompute); on a MISS, compute it ONCE via `compute_forward_aggregates` (the SOLE producer — this
+    function is a pure serving/persistence wrapper, never a second derivation), persist it under the
+    current dataset-version stamp, prune any stale rows for this `(horizon, asof_key)` identity, and
+    return it. The returned payload is BYTE-IDENTICAL to `compute_forward_aggregates(...)` (No recompute
+    in the read path).
+
+    WHY: `GET /api/backtest` called `compute_forward_aggregates` once per configured horizon (5) on
+    EVERY request — each call scans the WHOLE horizon-partition of `forward_returns` (~1.5-1.7M rows /
+    5 horizons at the current DB depth) and groups it in Python. Measured live
+    (`reports/perf-budgets.md`, iter-5): 34.77s for one `GET /api/backtest` request — the confirmed J-06
+    violation this cache fixes.
+
+    Because the key carries the `dataset_version` stamp (the SAME stamp `research._dataset_version`
+    produces — single-sourced with J-72/J-87/J-96/J-100), the cache REFRESHES automatically after any
+    dataset change (a backfill add or a removal, anywhere in the dataset — not just at this `as_of`,
+    since a backfilled EARLIER date can newly enter an already-cached LATER as-of's expanding window) —
+    a stale row is never hit. Unlike `EventStudyCache`/`MarketPhaseCache`, this cache carries no separate
+    "all-history" sentinel: `compute_forward_aggregates`'s one call site always resolves `as_of` to a
+    concrete `ScannerRun.asof_date` first (never the bare `as_of=None` case), so `asof_key` is always a
+    real ISO date.
+
+    Deferred import below (not at module level): `research.py` already imports names FROM this module,
+    so this module cannot import `research.py` at load time without a circular import; importing
+    `_dataset_version` lazily, inside this function, breaks the cycle (the same fix has no effect on
+    behavior — both modules are fully loaded by the time this function actually runs)."""
+    from app.engine.research import _dataset_version  # deferred: avoids a forward_testing<->research cycle
+
+    cfg = config or get_config()
+    version = _dataset_version(session)
+    asof_key = as_of.isoformat() if as_of is not None else "all"
+
+    hit = session.exec(
+        select(ForwardAggregateCache).where(
+            ForwardAggregateCache.horizon == horizon,
+            ForwardAggregateCache.asof_key == asof_key,
+            ForwardAggregateCache.dataset_version == version,
+        )
+    ).first()
+    if hit is not None:
+        return json.loads(hit.payload_json)
+
+    # MISS — compute once (the SOLE producer, unchanged) and persist.
+    payload = compute_forward_aggregates(session, horizon, cfg, as_of=as_of)
+
+    # prune stale rows for THIS (horizon, asof_key) identity (any older dataset_version) so the cache
+    # table does not grow unbounded as the dataset matures; the current-version row is then upserted.
+    stale = session.exec(
+        select(ForwardAggregateCache).where(
+            ForwardAggregateCache.horizon == horizon,
+            ForwardAggregateCache.asof_key == asof_key,
+            ForwardAggregateCache.dataset_version != version,
+        )
+    ).all()
+    for row in stale:
+        session.delete(row)
+
+    session.add(ForwardAggregateCache(
+        horizon=horizon, asof_key=asof_key, dataset_version=version,
+        payload_json=json.dumps(payload), created_at=datetime.now(timezone.utc),
+    ))
+    try:
+        session.commit()
+    except Exception:  # a concurrent writer raced us to the same key — the cache is best-effort, not a
+        session.rollback()  # source of truth; the freshly computed payload is still byte-identical, so return it
+    return payload
+
+
 # --------------------------------------------------------------------------------------------------
 # Per-date scorecard (J-14) — create-once population + the SINGLE per-date forward-test read
 # --------------------------------------------------------------------------------------------------
diff --git a/apps/backend/app/mcp/tools.py b/apps/backend/app/mcp/tools.py
index 815bf9ff..39721ecd 100644
--- a/apps/backend/app/mcp/tools.py
+++ b/apps/backend/app/mcp/tools.py
@@ -31,8 +31,8 @@ from app.engine import online_fdr
 from app.engine.forward_testing import (
     backfill_run_forward_returns,
     benchmark_symbols,
-    compute_forward_aggregates,
     compute_run_scorecard,
+    forward_aggregates_cached,
 )
 from app.engine.referee import (
     DEFAULT_ALPHA_BUDGET,
@@ -198,8 +198,11 @@ def query_backtest(session: Session, asof: Optional[str] = None) -> dict:
     run = resolved_run(session, asof, cfg)
     backfill_run_forward_returns(session, run, cfg)  # create-once realized forward returns (as the endpoint does)
     card = compute_run_scorecard(session, run, cfg)
+    # ops-hardening iter-5 (J-06): served from the SAME ingest-warmed cache GET /api/backtest now uses
+    # (this function's own docstring says it "mirrors the endpoint exactly" — kept true for the cache
+    # swap too; byte-identical output, `compute_forward_aggregates` itself is unchanged).
     evidence_by_horizon = {
-        h: compute_forward_aggregates(session, h, cfg, as_of=run.asof_date)
+        h: forward_aggregates_cached(session, h, cfg, as_of=run.asof_date)
         for h in cfg.walk_forward.horizons
     }
     return {
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index f09fc157..73f3fa05 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -504,6 +504,61 @@ class MarketPhaseCache(SQLModel, table=True):
     created_at: datetime
 
 
+# --- ops-hardening iter-5 (J-06) forward-aggregate derived-cache ---------------------------------
+class ForwardAggregateCache(SQLModel, table=True):
+    """A STANDALONE, create_all-managed cache of the derived per-horizon forward-return aggregate
+    (`app.engine.forward_testing.compute_forward_aggregates`), served on `GET /api/backtest`'s
+    `evidence_by_horizon` (ops-hardening iter-5, J-06).
+
+    Like `EventStudyCache` / `MarketPhaseCache` / `CoverageSnapshot`, this is EXPLICITLY NOT a scanner
+    snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
+    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache
+    state: it stores the SERIALIZED `compute_forward_aggregates(...)` payload (forward return by
+    bucket/setup/regime, excess vs SPY/QQQ, VCP/new-pattern breakdowns, control-group cohorts — each
+    with `n`) keyed by the horizon + the resolved as-of cutoff + a dataset-version stamp, so a read
+    serves the stored aggregate instead of re-deriving it per request (No recompute in the read path).
+    The cached figures are BYTE-IDENTICAL to a fresh compute — a cache of the deterministic read-only
+    aggregation, never a second computation.
+
+    WHY: `compute_forward_aggregates` scans the WHOLE horizon-partition of `forward_returns`
+    (`select(ForwardReturn).where(horizon == h)`, then groups it in Python) — `GET /api/backtest`
+    called it once per configured horizon (5) on EVERY request. Measured live at the current DB depth
+    (`reports/perf-budgets.md`, iter-5): 34.77s for one request — the confirmed J-06 violation.
+
+    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
+    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
+    existing table gains a column.
+
+    CACHE KEY: `(horizon, asof_key, dataset_version)`:
+      - `horizon` is the requested horizon (one of `config.walk_forward.horizons`).
+      - `asof_key` is the resolved as-of cutoff ISO date — `compute_forward_aggregates`'s `as_of` is
+        always a concrete date at its one call site (`GET /api/backtest` always resolves `?as_of=` to a
+        real `ScannerRun.asof_date` before calling it — never the bare `as_of=None` all-history case),
+        so unlike `EventStudyCache`/`MarketPhaseCache` this key carries no separate "all" sentinel.
+      - `dataset_version` is the SAME stamp `app.engine.research._dataset_version` produces
+        (single-sourced with J-72/J-87/J-96/J-100) — a read computes the current stamp and looks up
+        THIS exact key; a stale row keyed to an older stamp is never hit (and is pruned on write), so
+        the cache can NEVER serve a stale figure (it refreshes after any dataset change — a backfill
+        that adds runs/returns anywhere changes the global stamp, correctly invalidating even an
+        unrelated as-of's cached row, since an expanding as-of window can gain new in-range runs from a
+        backfill dated earlier than it).
+
+    `payload_json` is the full serialized aggregate. Unique on the composite key so a write is an
+    idempotent upsert."""
+
+    __tablename__ = "forward_aggregate_cache"
+    __table_args__ = (
+        UniqueConstraint("horizon", "asof_key", "dataset_version", name="uq_forward_aggregate_cache_key"),
+    )
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    horizon: int = Field(index=True)
+    asof_key: str  # resolved as-of ISO cutoff date (compute_forward_aggregates's concrete `as_of`)
+    dataset_version: str  # the SAME stamp research._dataset_version produces; changes on any dataset change
+    payload_json: str  # the serialized compute_forward_aggregates(...) aggregate (byte-identical to a fresh compute)
+    created_at: datetime
+
+
 class MacroSeries(SQLModel, table=True):
     """A STANDALONE, create_all-managed table of optional FRED macro-feed observations (iter-32, J-92).
 
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index bb6aa772..0e45a424 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -68,6 +68,7 @@ from app.models import (
     CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
+    ForwardAggregateCache,
     ForwardReturn,
     ImportCheckpoint,
     ScannerResult,
@@ -1042,7 +1043,8 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
     """TC-1/TC-5 — a finalize hook call for a job that newly created a snapshot on `d` persists exactly one
     `coverage_snapshot` row for the current stamp and reports every category this fixture's data supports
     as refreshed: `latest_snapshot` (this run created a snapshot), `coverage` + `membership_timeline` (one
-    compute warms both), `market_phase` (the new date), `research_hot_keys` (the default hot key)."""
+    compute warms both), `market_phase` (the new date), `forward_aggregates` (ops-hardening iter-5: the
+    current latest run's per-horizon forward-aggregate cache), `research_hot_keys` (the default hot key)."""
     engine, d = finalize_hook_engine
     cfg = load_config()
     with Session(engine) as session:
@@ -1050,7 +1052,8 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         prog.new_snapshot_dates = [d]
         refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
     assert set(refreshed) == {
-        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys",
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "forward_aggregates",
+        "research_hot_keys",
     }
     with Session(engine) as session:
         rows = session.exec(select(CoverageSnapshot)).all()
@@ -1060,6 +1063,52 @@ def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_
         assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)
 
 
+def test_finalize_hook_warms_forward_aggregates_for_every_configured_horizon(finalize_hook_engine):
+    """ops-hardening iter-5 (J-06) — the finalize hook warms `ForwardAggregateCache` for the CURRENT
+    latest stored run's as-of, once per configured `walk_forward.horizons` — proven directly: after the
+    hook runs, exactly one cached row exists per configured horizon at that as-of."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="forward-agg-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "forward_aggregates" in refreshed
+    with Session(engine) as session:
+        rows = session.exec(
+            select(ForwardAggregateCache).where(ForwardAggregateCache.asof_key == d.isoformat())
+        ).all()
+    assert {row.horizon for row in rows} == set(cfg.walk_forward.horizons)
+
+
+def test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read(
+    finalize_hook_engine, monkeypatch
+):
+    """A `GET /api/backtest`-shaped read for the SAME (horizon, as-of) the finalize hook just warmed
+    hits the cache — zero further `compute_forward_aggregates` calls. This is the actual perf fix this
+    iteration makes: a live request no longer pays the 5-horizon full-table scan the finalize hook
+    already paid at ingest (measured 34.77s pre-fix for one request, `reports/perf-budgets.md`)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="forward-agg-hit-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    call_count = {"n": 0}
+    real = forward_testing.compute_forward_aggregates
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(forward_testing, "compute_forward_aggregates", _counting)
+    with Session(engine) as session:
+        for h in cfg.walk_forward.horizons:
+            forward_testing.forward_aggregates_cached(session, h, cfg, as_of=d)
+    assert call_count["n"] == 0, "the finalize hook's warm should have already cached every horizon"
+
+
 def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finalize_hook_engine):
     """TC-8 — the persisted payload_json is byte-identical (field-by-field) to a direct fresh
     `_compute_coverage_uncached` call for the same session state (AG-3: storage is re-served, never
@@ -1152,6 +1201,7 @@ def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_eng
 
     monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _boom)
     monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
+    monkeypatch.setattr(forward_testing, "forward_aggregates_cached", _boom)
     monkeypatch.setattr(data_manager, "event_study_cached", _boom)
     with Session(engine) as session:
         prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
diff --git a/apps/backend/tests/test_forward_testing.py b/apps/backend/tests/test_forward_testing.py
index 51bc5bcd..397576cd 100644
--- a/apps/backend/tests/test_forward_testing.py
+++ b/apps/backend/tests/test_forward_testing.py
@@ -33,6 +33,7 @@ from app.engine.forward_testing import (
     compute_drawdown_expectations,
     compute_drawdown_expectations_cached,
     compute_forward_aggregates,
+    forward_aggregates_cached,
     forward_excursions,
     forward_return,
     max_drawdown,
@@ -45,6 +46,7 @@ from app.engine.scanner import run_scan
 from app.models import (
     DailyPrice,
     EventStudyCache,
+    ForwardAggregateCache,
     ForwardReturn,
     ScannerResult,
     ScannerRun,
@@ -810,6 +812,99 @@ def test_aggregates_as_of_scoped_consistency_invariant_relocated(aggregates_engi
     assert sum(r["n"] for r in attr["by_rank_band"]) == overall["n"]
 
 
+# ==================================================================================================
+# forward_aggregates_cached (ops-hardening iter-5, J-06) — the ForwardAggregateCache performance layer.
+# GET /api/backtest called compute_forward_aggregates once per configured horizon (5) on EVERY request;
+# measured live at 34.77s for one request (reports/perf-budgets.md). This cache mirrors
+# research.event_study_cached / market_phase.market_phase_cached / this module's own
+# compute_drawdown_expectations_cached exactly.
+# ==================================================================================================
+def test_forward_aggregates_cached_byte_identical_and_single_row(aggregates_engine):
+    """A cache MISS then HIT both return a payload BYTE-IDENTICAL to a fresh uncached
+    `compute_forward_aggregates` call, and exactly ONE `ForwardAggregateCache` row is written for this
+    (horizon, as_of) (no duplicate insert on the second call)."""
+    engine, H = aggregates_engine
+    cfg = load_config()
+    as_of = date(2025, 1, 10)
+    with Session(engine) as session:
+        fresh = compute_forward_aggregates(session, H, cfg, as_of=as_of)
+        miss = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        hit = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        rows = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == H,
+                ForwardAggregateCache.asof_key == as_of.isoformat(),
+            )
+        ).all()
+    assert json.dumps(fresh, sort_keys=True) == json.dumps(miss, sort_keys=True) == json.dumps(hit, sort_keys=True)
+    assert len(rows) == 1
+
+
+def test_forward_aggregates_cached_avoids_recompute_on_hit(aggregates_engine, monkeypatch):
+    """The SECOND call for the SAME (horizon, as_of) never re-invokes the uncached
+    `compute_forward_aggregates` — proven by monkeypatching it to count calls (a call-count proof, not
+    just a byte-match, so a bug that silently recomputed-but-still-matched would still fail this test)."""
+    import app.engine.forward_testing as forward_testing_module
+
+    engine, H = aggregates_engine
+    cfg = load_config()
+    as_of = date(2025, 1, 10)
+    call_count = {"n": 0}
+    real = forward_testing_module.compute_forward_aggregates
+
+    def _counting(*args, **kwargs):
+        call_count["n"] += 1
+        return real(*args, **kwargs)
+
+    monkeypatch.setattr(forward_testing_module, "compute_forward_aggregates", _counting)
+    with Session(engine) as session:
+        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # MISS -> 1 call
+        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
+        forward_testing_module.forward_aggregates_cached(session, H, cfg, as_of=as_of)  # HIT -> 0 more
+    assert call_count["n"] == 1
+
+
+def test_forward_aggregates_cached_refreshes_on_dataset_version_change(aggregates_engine):
+    """The cache refreshes when the dataset changes (no stale figure): adding one more forward-return
+    observation on the SAME already-included run bumps `_dataset_version`, so the next call for the SAME
+    (horizon, as_of) recomputes (a genuinely larger cohort) rather than serving the pre-change payload,
+    and the stale row is pruned (iter-2 B1 lesson: a fingerprint-only invalidation must not serve a
+    false/stale figure — this reuses the SAME already-hardened `research._dataset_version` stamp, never
+    a new invalidation mechanism)."""
+    engine, H = aggregates_engine
+    cfg = load_config()
+    as_of = date(2025, 1, 10)
+    with Session(engine) as session:
+        before = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        from app.engine.research import _dataset_version
+        v_before = _dataset_version(session)
+        rows_before = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == H, ForwardAggregateCache.asof_key == as_of.isoformat(),
+            )
+        ).all()
+        assert len(rows_before) == 1 and rows_before[0].dataset_version == v_before
+
+        # change the dataset: one more forward-return observation on run1 (the already-included latest
+        # run) -- a genuinely different cohort at the SAME (horizon, as_of) key.
+        run1 = session.exec(select(ScannerRun).where(ScannerRun.asof_date == as_of)).one()
+        _add_result(session, run1.id, "ZZZ", "A", "Actionable", "Technology", 5)
+        _add_fr(session, run1.id, "ZZZ", H, 1.00)
+        session.commit()
+        v_after = _dataset_version(session)
+        assert v_after != v_before
+
+        after = forward_aggregates_cached(session, H, cfg, as_of=as_of)
+        rows_after = session.exec(
+            select(ForwardAggregateCache).where(
+                ForwardAggregateCache.horizon == H, ForwardAggregateCache.asof_key == as_of.isoformat(),
+            )
+        ).all()
+    assert len(rows_after) == 1 and rows_after[0].dataset_version == v_after
+    assert before["overall"]["n"] == 6
+    assert after["overall"]["n"] == 7  # the recompute picked up the new ZZZ observation
+
+
 # ==================================================================================================
 # walk-forward as-of date set (real seed trading calendar; no run_scan -> cheap)
 # ==================================================================================================
diff --git a/incredible_auto_dev/scripts/measure-perf.sh b/incredible_auto_dev/scripts/measure-perf.sh
index e3bdbb5d..4c70c70a 100755
--- a/incredible_auto_dev/scripts/measure-perf.sh
+++ b/incredible_auto_dev/scripts/measure-perf.sh
@@ -9,18 +9,38 @@
 # reports/perf-budgets.md so the growth/perf slope is visible run-over-run (goal.md J-15/J-16).
 #
 # Runs against PROD MODE ONLY (scripts/start-backend.sh / scripts/start-frontend.sh — this script does
-# NOT start them; bring them up first). `next dev`'s per-route compile is not product latency, so this
-# script refuses to measure against a `next dev` frontend (no reliable way to detect that from here, so
-# it just documents the requirement — see the header + --help).
+# NOT start them; bring them up first, UNLESS you pass --boot, see below). `next dev`'s per-route
+# compile is not product latency, so this script refuses to measure against a `next dev` frontend (no
+# reliable way to detect that from here, so it just documents the requirement — see the header + --help).
+#
+# iter-5 (J-06 capstone) additions:
+#   --boot   TC-1: measure backend cold-boot wall time (process start -> first GET /api/health HTTP
+#            200) on the warm committed-seed DB. Off by default (a normal run still expects the
+#            backend already warm/running, unchanged). When passed, this script refuses to run if
+#            something already answers on the backend port (a cold-boot measurement needs a REAL
+#            process start — never stomping a live instance), then launches
+#            scripts/start-backend.sh itself and leaves it running afterward so the rest of this
+#            script's warm measurements proceed normally against it. The frontend is still never
+#            started by this script — bring it up yourself.
+#   Also captures the 7 previously-unmeasured pages/endpoints named in goal.md J-06: the Dashboard
+#   cluster (/api/dashboard, /api/market-phase, /api/sectors, /api/themes, /api/indexes?full=true,
+#   /api/regime-history?full=true, /api/market-phase?full=true — the cross-view chart's own calls),
+#   /api/sectors, /api/themes, /api/runs, /api/backtest, /api/watchlist, /api/research/event-study —
+#   and their pages (/, /sectors, /themes, /scanner-runs, /backtest, /watchlist,
+#   /research/event-study).
 #
 # Usage:
 #   bash scripts/start-backend.sh &
 #   bash scripts/start-frontend.sh &
 #   # wait for both to answer 200, then:
 #   bash scripts/measure-perf.sh [--ticker AAPL] [--backfill-days 5] [--out reports/perf-budgets.md]
+#   # OR, to also measure cold-boot (TC-1) and let this script start the backend itself:
+#   bash scripts/start-frontend.sh &
+#   bash scripts/measure-perf.sh --boot [--out reports/perf-budgets.md]
 #
-# Every bound/scope this script uses (the backfill window size, the default ticker) is a NAMED
-# default below or a flag override — never a bare literal buried in logic (goal.md item K's own rule).
+# Every bound/scope this script uses (the backfill window size, the default ticker, the boot poll
+# interval/timeout/budget) is a NAMED default below or a flag override — never a bare literal buried
+# in logic (goal.md item K's own rule).
 set -euo pipefail
 
 REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
@@ -40,11 +60,23 @@ DEFAULT_TICKER="AAPL"
 DEFAULT_BACKFILL_DAYS=5
 DEFAULT_OUT="$REPO_ROOT/reports/perf-budgets.md"
 DEFAULT_BACKFILL_POLL_TIMEOUT_S=120
+# iter-5 TC-1: cold-boot measurement bounds. TIMEOUT is this SCRIPT's own safety bound (so a wedged
+# boot fails loud instead of polling forever); BUDGET is the PRODUCT's committed ceiling (goal.md
+# Success Criteria: "process start -> first GET /api/health HTTP 200 in <= 5 seconds").
+DEFAULT_BOOT_TIMEOUT_S=30
+DEFAULT_BOOT_POLL_INTERVAL_S=0.1
+DEFAULT_BOOT_BUDGET_S=5
+# iter-5 TC-2/TC-5/TC-6/TC-9/TC-10/TC-11/TC-12: the generic newly-committed budgets, matching every
+# existing non-tiny-payload endpoint/page already on file (e.g. `/api/stocks`/`/api/data` <= 1.5 s;
+# `/stocks`/`/data`/`/evidence` <= 3 s) — a single named default, not 11 more hand-copied numbers.
+DEFAULT_API_BUDGET_S=1.5
+DEFAULT_PAGE_BUDGET_S=3
 
 TICKER="$DEFAULT_TICKER"
 BACKFILL_DAYS="$DEFAULT_BACKFILL_DAYS"
 OUT_FILE="$DEFAULT_OUT"
 SKIP_BACKFILL=0
+MEASURE_BOOT=0
 
 while [[ $# -gt 0 ]]; do
   case "$1" in
@@ -52,8 +84,9 @@ while [[ $# -gt 0 ]]; do
     --backfill-days) BACKFILL_DAYS="$2"; shift 2 ;;
     --out) OUT_FILE="$2"; shift 2 ;;
     --skip-backfill) SKIP_BACKFILL=1; shift ;;
+    --boot) MEASURE_BOOT=1; shift ;;
     -h|--help)
-      sed -n '2,25p' "$0"
+      sed -n '2,43p' "$0"
       exit 0
       ;;
     *)
@@ -84,6 +117,40 @@ _require_200() {
 
 echo "== measure-perf.sh — backend :${BACKEND_PORT}, frontend :${FRONTEND_PORT} ==" >&2
 
+# iter-5 TC-1: backend cold-boot wall time (process start -> first GET /api/health HTTP 200) on the
+# warm committed-seed DB. Off by default — see --boot in --help.
+boot_line="skipped (pass --boot to measure cold-boot-to-health)"
+if [[ "$MEASURE_BOOT" -eq 1 ]]; then
+  echo "-- TC-1: backend cold-boot timing (process start -> first GET /api/health HTTP 200) --" >&2
+  # Refuse to stomp a live instance — a cold-boot measurement needs a REAL process start; if something
+  # already answers here, this script would either fail to bind the port or (worse) silently measure
+  # the wrong process's startup.
+  existing_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 1 "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
+  if [[ "$existing_code" == "200" ]]; then
+    echo "measure-perf.sh --boot: $BACKEND_URL/api/health already answers 200 — stop the running backend first (this measurement needs a real cold process start)." >&2
+    exit 1
+  fi
+  boot_start=$(date +%s.%N)
+  bash "$REPO_ROOT/scripts/start-backend.sh" >/dev/null 2>&1 &
+  boot_pid=$!
+  boot_code="000"
+  boot_deadline=$(( $(date +%s) + DEFAULT_BOOT_TIMEOUT_S ))
+  while [[ "$boot_code" != "200" && $(date +%s) -lt $boot_deadline ]]; do
+    sleep "$DEFAULT_BOOT_POLL_INTERVAL_S"
+    boot_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 0.5 "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
+  done
+  boot_end=$(date +%s.%N)
+  boot_elapsed=$(awk "BEGIN {printf \"%.3f\", $boot_end - $boot_start}")
+  if [[ "$boot_code" == "200" ]]; then
+    boot_holds=$(awk "BEGIN {print ($boot_elapsed <= $DEFAULT_BOOT_BUDGET_S) ? \"yes\" : \"NO\"}")
+    boot_line="**${boot_elapsed}s** (process start -> first HTTP 200), launcher pid ${boot_pid} — holds <= ${DEFAULT_BOOT_BUDGET_S}s budget: ${boot_holds}"
+    echo "  boot-to-health: ${boot_elapsed}s (holds <= ${DEFAULT_BOOT_BUDGET_S}s: ${boot_holds})" >&2
+  else
+    boot_line="FAILED — no HTTP 200 within ${DEFAULT_BOOT_TIMEOUT_S}s of process start (last code: ${boot_code})"
+    echo "  measure-perf.sh --boot: $boot_line" >&2
+  fi
+fi
+
 # Confirm both services are reachable BEFORE measuring (never silently measure a dead endpoint as 0s).
 for probe in "$BACKEND_URL/api/health" "$FRONTEND_URL/"; do
   code=$(curl -s -o /dev/null -w "%{http_code}" "$probe" || echo "000")
@@ -122,6 +189,64 @@ _require_200 "/data (page)" "$data_page_s" "$data_page_code"
 read -r evidence_page_s evidence_page_code <<<"$(_curl_timed "$FRONTEND_URL/evidence")"
 _require_200 "/evidence (page)" "$evidence_page_s" "$evidence_page_code"
 
+# --- iter-5 (J-06 capstone): the 7 previously-unmeasured pages' backing endpoints + their pages ----
+# NAMED endpoint/page maps (label -> URL), measured with the SAME warm-up-then-timed pattern as the
+# endpoints above — a loop rather than 18 more hand-copied blocks (TC-2..TC-12 name this many pairs at
+# once; this is the 3rd+ occurrence of the identical warm+timed-hit shape). Order is a fixed array
+# (bash associative arrays are unordered) so the appended table always reads in the TC-2..TC-12 sequence.
+NEW_ENDPOINT_ORDER=(
+  "GET /api/dashboard" "GET /api/market-phase" "GET /api/sectors" "GET /api/themes"
+  "GET /api/indexes?full=true" "GET /api/regime-history?full=true" "GET /api/market-phase?full=true"
+  "GET /api/runs" "GET /api/backtest" "GET /api/watchlist" "GET /api/research/event-study"
+)
+declare -A NEW_ENDPOINT_URL=(
+  ["GET /api/dashboard"]="$BACKEND_URL/api/dashboard"
+  ["GET /api/market-phase"]="$BACKEND_URL/api/market-phase"
+  ["GET /api/sectors"]="$BACKEND_URL/api/sectors"
+  ["GET /api/themes"]="$BACKEND_URL/api/themes"
+  ["GET /api/indexes?full=true"]="$BACKEND_URL/api/indexes?full=true"
+  ["GET /api/regime-history?full=true"]="$BACKEND_URL/api/regime-history?full=true"
+  ["GET /api/market-phase?full=true"]="$BACKEND_URL/api/market-phase?full=true"
+  ["GET /api/runs"]="$BACKEND_URL/api/runs"
+  ["GET /api/backtest"]="$BACKEND_URL/api/backtest"
+  ["GET /api/watchlist"]="$BACKEND_URL/api/watchlist"
+  # the real first-load call: no subject/horizon (backend picks the default) — `view=episodes` is the
+  # page's own initial state (apps/frontend/app/research/_labs.tsx's EventStudyLab effect).
+  ["GET /api/research/event-study"]="$BACKEND_URL/api/research/event-study?view=episodes"
+)
+NEW_PAGE_ORDER=(
+  "/ (Dashboard)" "/sectors" "/themes" "/scanner-runs" "/backtest" "/watchlist" "/research/event-study"
+)
+declare -A NEW_PAGE_URL=(
+  ["/ (Dashboard)"]="$FRONTEND_URL/"
+  ["/sectors"]="$FRONTEND_URL/sectors"
+  ["/themes"]="$FRONTEND_URL/themes"
+  ["/scanner-runs"]="$FRONTEND_URL/scanner-runs"
+  ["/backtest"]="$FRONTEND_URL/backtest"
+  ["/watchlist"]="$FRONTEND_URL/watchlist"
+  ["/research/event-study"]="$FRONTEND_URL/research/event-study"
+)
+
+echo "-- iter-5: warm-up hits (the 11 not-yet-measured endpoints/pages) --" >&2
+for label in "${NEW_ENDPOINT_ORDER[@]}"; do curl -s -o /dev/null "${NEW_ENDPOINT_URL[$label]}" || true; done
+for label in "${NEW_PAGE_ORDER[@]}"; do curl -s -o /dev/null "${NEW_PAGE_URL[$label]}" || true; done
+
+echo "-- iter-5: warm endpoint latencies (TC-2, TC-5, TC-6, TC-9, TC-10, TC-11, TC-12) --" >&2
+declare -A NEW_ENDPOINT_RESULT=()
+for label in "${NEW_ENDPOINT_ORDER[@]}"; do
+  read -r seconds code <<<"$(_curl_timed "${NEW_ENDPOINT_URL[$label]}")"
+  _require_200 "$label" "$seconds" "$code"
+  NEW_ENDPOINT_RESULT["$label"]="${seconds}|${code}"
+done
+
+echo "-- iter-5: warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity) --" >&2
+declare -A NEW_PAGE_RESULT=()
+for label in "${NEW_PAGE_ORDER[@]}"; do
+  read -r seconds code <<<"$(_curl_timed "${NEW_PAGE_URL[$label]}")"
+  _require_200 "$label (page)" "$seconds" "$code"
+  NEW_PAGE_RESULT["$label"]="${seconds}|${code}"
+done
+
 echo "-- DB capacity snapshot (from GET /api/data's additive 'capacity' field) --" >&2
 data_body=$(curl -s "$BACKEND_URL/api/data")
 db_file_bytes=$(echo "$data_body" | jq -r '.capacity.db_file_bytes')
@@ -188,7 +313,12 @@ host_info="$(uname -srm 2>/dev/null || echo unknown)"
 
 {
   echo ""
-  echo "## Items B/C/D/G/H/K — mechanical backend pass + storage-footprint card (iter-24)"
+  # iter-5: this title used to hardcode "(iter-24)" regardless of which iteration actually ran the
+  # script, so every re-run silently mislabeled its own fresh measurements as iter-24's (iter-25's own
+  # dev handoff had to work around this by transcribing to a scratch file instead of appending
+  # directly). Fixed here: the title now carries the real measurement timestamp instead of a frozen
+  # iteration number — the "items B/C/D/G/H/K" methodology reference is historical and stays accurate.
+  echo "## Mechanical backend + page pass — items B/C/D/G/H/K methodology, re-measured $timestamp"
   echo ""
   echo "Measured $timestamp on this host ($host_info) via \`scripts/measure-perf.sh\` against PROD MODE"
   echo "(\`start-backend.sh\`/\`start-frontend.sh\`, backend :${BACKEND_PORT} / frontend :${FRONTEND_PORT})."
@@ -224,4 +354,42 @@ host_info="$(uname -srm 2>/dev/null || echo unknown)"
   echo ""
 } >> "$OUT_FILE"
 
+# iter-5 (J-06 capstone): a SEPARATE, freshly-dated section for the boot timing + the 7
+# previously-unmeasured pages — appended to the SAME file (TC-15: no second budgets artifact anywhere).
+{
+  echo ""
+  echo "## J-06 capstone — boot-to-health + the 7 previously-unmeasured pages (iter-5)"
+  echo ""
+  echo "Measured $timestamp on this host ($host_info) via \`scripts/measure-perf.sh\` (extended this"
+  echo "iteration) against PROD MODE (\`start-backend.sh\`/\`start-frontend.sh\`, backend"
+  echo ":${BACKEND_PORT} / frontend :${FRONTEND_PORT})."
+  echo ""
+  echo "**TC-1 — backend cold-boot wall time (process start -> first \`GET /api/health\` HTTP 200):**"
+  echo ""
+  echo "${boot_line}"
+  echo ""
+  echo "**Warm endpoint latencies (TC-2, TC-5, TC-6, TC-9, TC-10, TC-11, TC-12 — generic <= ${DEFAULT_API_BUDGET_S}s"
+  echo "API budget, matching this file's existing \`/api/stocks\`/\`/api/data\` budgets):**"
+  echo ""
+  echo "| Endpoint | Wall time | Budget | Holds? |"
+  echo "|---|---|---|---|"
+  for label in "${NEW_ENDPOINT_ORDER[@]}"; do
+    IFS='|' read -r seconds code <<<"${NEW_ENDPOINT_RESULT[$label]}"
+    holds=$(awk "BEGIN {print ($seconds <= $DEFAULT_API_BUDGET_S) ? \"yes\" : \"NO\"}")
+    echo "| \`${label}\` | ${seconds}s | <= ${DEFAULT_API_BUDGET_S} s | ${holds} (HTTP ${code}) |"
+  done
+  echo ""
+  echo "**Warm page latencies (HTTP response time; the browser-qa lane verifies true interactivity —"
+  echo "TC-2's Dashboard TTI budget is <= 3 s; the rest share the generic <= ${DEFAULT_PAGE_BUDGET_S}s page budget):**"
+  echo ""
+  echo "| Page | Wall time | Budget | Holds? |"
+  echo "|---|---|---|---|"
+  for label in "${NEW_PAGE_ORDER[@]}"; do
+    IFS='|' read -r seconds code <<<"${NEW_PAGE_RESULT[$label]}"
+    holds=$(awk "BEGIN {print ($seconds <= $DEFAULT_PAGE_BUDGET_S) ? \"yes\" : \"NO\"}")
+    echo "| \`${label}\` | ${seconds}s | <= ${DEFAULT_PAGE_BUDGET_S} s | ${holds} (HTTP ${code}) |"
+  done
+  echo ""
+} >> "$OUT_FILE"
+
 echo "== appended measurements to $OUT_FILE ==" >&2
```
