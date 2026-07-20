# Iteration diff (bounded)

Files changed: 12. Shown in full: 9.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `apps/frontend/app/data/page.tsx` (82 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/engine/data_manager.py` (60 lines not shown)
- `apps/backend/tests/test_data_manager.py` (25 lines not shown)

```diff
diff --git a/README.md b/README.md
index 35f9c83..2f25c2c 100644
--- a/README.md
+++ b/README.md
@@ -37,7 +37,7 @@ Current capabilities:
 - **Referee audit**: a fourth card, "Referee audit," alongside Pre-registration registry, Negative-results graveyard, and Certification-budget accounting, completes the Research hub's "Governance & process" section as a four-card grid and opens a dedicated `/research/referee-audit` page that asks whether the platform's own statistical certifier can itself be trusted. A four-stat summary row reports the number of deliberately meaningless ("null") signal trials the certifier was tested against and their source factor; the certifier's empirical false-pass rate — how often it wrongly calls a null pattern "real" — with its 95% confidence interval, shown beside the configured significance threshold (α) it is supposed to respect (currently: false-pass rate 0.08 across 200 trials, 95% CI [0.0498, 0.126], against α = 0.05); and the run date plus its seed and horizon parameters. Below that, a single verdict card reports whether an intentionally "cheating" factor — built from its own future outcome, the "perfect crime" a broken certifier would rubber-stamp — was caught and rejected; right now it was not caught, and the page renders that as a loud red "tripwire" warning rather than a quiet pass, with the verdict badge always styled as a failure warning in this case even though the underlying statistical result is technically a "pass." If the backend is unreachable a contained "Backend unavailable" card is shown instead of a broken page. The check itself runs only as an offline, config-seeded job with no in-app trigger; the page always re-reads whatever that job last wrote, and it does not affect any other score, ranking, or evidence status shown elsewhere in the product.
 - **Watchlist**: persists across backend restarts; accepts any ticker in the platform's broadened, ~548-name price-history universe rather than a small preset list; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level. A **Concentration X-ray** section below the entries table (shown once at least one stock is saved) answers "how concentrated is my watchlist really?": a ticker-by-ticker correlation heatmap shows exactly how correlated every pair of saved stocks is over a trailing lookback window (126 trading days by default), correlation-threshold clusters group names that move together, and a headline **"effective independent bets"** figure — with its trailing window stated inline — reports how many genuinely different bets the list represents versus how many names are just duplicates of each other in disguise; an info icon opens a plain-language explanation of the methodology and its minimum-history floor. Sector, theme, and shared-setup-status concentration bars sit beneath the matrix, using the same status colours as the entries table's own Setup column. Hovering any matrix cell shows the exact correlation value, or — for a stock without enough price history — the exact reason it reads "not enough data" rather than a guessed number. A watchlist with 0 or 1 saved names shows an honest "not enough names yet for an X-ray" message instead of an empty or broken chart. The section is purely descriptive — read-only, no new controls — and rides the same single watchlist data call the page already made, so it shares the page's existing loading and error states.
 - **Methodology / Glossary**: a searchable, categorized glossary of over 120 terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence (including "Episode" and "Pooled (per-signal-day)"), and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded. The Universe Selection section documents two layers: the candidate-pool screen (market cap, price, liquidity) and the per-date membership rule (history + price + liquidity + data recency, with the market-cap criterion dropped for per-date use because it has no historical series). The per-date rule is displayed verbatim as prose on the page — showing the candidate pool size, the exact minimum-history-bar threshold, and how stocks are admitted or excluded per snapshot date — pulled live from the same API endpoint that drives the Data Manager diagnostic.
-- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
+- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots — a Fetch (or Fetch + backfill) run refreshes the platform's entire committed stock pool (roughly 548 names, ~590 symbols including benchmark/context series) in one action rather than a smaller reference subset. The coverage header shows two universe figures side by side: **"Universe (as of date)"** — the point-in-time count for the date you are viewing, which changes as you step the global date switcher — and **"Candidate universe"** — the full screened candidate count it is drawn from. Directly below the coverage panel, a **Storage footprint** card reports the database's on-disk file size in human-readable form alongside live counts of stored price bars, scanner rows, and forward-return records, so anyone can see at a glance how large the dataset has grown; a brand-new, empty database reads as zero across the board rather than erroring. A **Live-vs-seed drift** card directly below it reports whether the most recent Fetch job's freshly-pulled prices matched the platform's trusted, committed reference data over their date overlap, in four honest states — a quiet gray "no fetch has run yet" message, a quiet green "matched the seed" line, a loud amber alert naming every affected symbol and its exact mismatching dates as an "adjustment seam" (typically caused by a data provider retroactively revising history around a dividend or stock split), or a loud amber "could not be read" fallback if the report is corrupted; hovering the card's title explains that the check is a descriptive byte/fixed-precision comparison only — it recomputes nothing and never auto-repairs or re-fetches. A detected drift also degrades the site-wide preflight banner (see below) on every page, not just Data Manager, and clears automatically once a later clean fetch supersedes it. A **Universe Diagnostic** panel below the coverage metrics explains exactly why the universe is the size it is at the current date — admitted count plus excluded-by-reason counts (below history / below price / below liquidity / stale data — a price feed untouched for more than 10 calendar days) with exact threshold values; at an early date before enough history has accumulated it shows an honest empty-universe banner. A **Membership Timeline** panel charts how the universe size grew across snapshot dates as an SVG step-function, lists which names entered and exited on which date with a per-date entries/exits/excluded breakdown, and displays three plain-English honesty labels: a survivorship caveat, a warm-up boundary note, and a universe-relative breadth note. The history list is paginated (10 dates per page) with **Year and Month filter dropdowns** so you can jump directly to any period; an honest count shows exactly how many dates match the selected filters, and an empty state is shown when no dates match. An **Extend history backward** section offers a confirm-gated button that attempts a best-effort fetch of earlier price history so the universe can resolve further into the past; when the data provider is unreachable it records an honest blocked/limited-coverage (NA) outcome and never invents data. Import jobs now appear in **Run History the instant they start** (as a "running" entry with its kind, date range, and source) and update in place to an honest final state — ok, partial, failed, resumable, or interrupted — rather than only appearing when the job finishes. If the backend is restarted mid-job, the orphaned entry is marked **"interrupted"** on next boot so nothing is ever stuck on "running" permanently. A **live job card** shows a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates each poll tick, an "updated Ns ago" heartbeat that turns amber if the job stops advancing for longer than the stale threshold, and a symbols counter that is guaranteed to never exceed its own total. Live imports retry automatically on rate-limit responses with exponential backoff, save progress durably, and expose an amber "rate-limited — resumable" state with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. **Stage-aware resume**: if a job completes its price-history download but fails during the snapshot-building stage, hitting Resume skips the download entirely and picks up at the snapshot stage — saving time and provider quota. **Covered-range skip**: re-running a job over a date range already fully downloaded completes in seconds (adding "0 new bars") instead of re-downloading all the data. **Reliable multi-month backfill**: a full-history or multi-month backfill job now runs to completion without crashing — if a single date genuinely fails, that one date is isolated and reported while every other date finishes; re-running the same range fills only what is missing without creating duplicates. **Backfill honors the exact range you request, with no length limit**: an explicit backfill (or fetch-and-backfill) submission always processes every trading day in the date range you ask for — the platform's own "keep it light on old history" background snapshot cadence governs only its automatic upkeep, never something explicitly requested — and there is no maximum request length; a very large range (previously capped at roughly a year) is instead split automatically into chunks and shows the same "chunk N/M" progress badge already used for large downloads. Every completed backfill or rebuild reports an honest breakdown of how many calendar days were in the range, how many were non-trading days, how many were already snapshotted, and how many failed, with the counts guaranteed to add up; a run that does zero new work — because the range was already fully covered, or contains no trading days at all — shows a distinct neutral "no new snapshots" badge and explanation rather than looking like an ordinary success. The Job progress panel also shows the most recently completed run's outcome immediately on page reload or in a fresh browser session, instead of defaulting to "No job has been started this session" whenever run history already exists. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed, number of parallel workers, and the "per-date sum" versus actual wall-clock time so you can see the speed-up directly (the speed-up figure is computed on the server). A **seed-safe Remove imported data** panel removes data by date range — enter a From and To date (both required; no free-text symbol field) and click "Preview removal" to see a compact count summary: bars to remove, symbols affected, protected seed bars kept, and snapshots that will cascade away; the Confirm button is always visible without scrolling, and the committed seed can never be deleted. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories, with one-click fix buttons. A **Rebuild snapshots** panel shows a coverage diagnostic: when newly-expanded universe members are absent from the latest snapshot, an amber banner lists the missing tickers and prompts a rebuild; when all members are present a calm "all members present" note is shown instead. Clicking "Rebuild snapshots for current universe" opens a confirm dialog — the rebuild never starts accidentally — and on confirmation clears all existing snapshots and recomputes every trading date from scratch via the parallel backfill path (committed price seed is never touched); live progress is tracked in the existing job card. **Known limitation:** on the full committed dataset (up to ~30 years of history across the whole symbol universe), this rebuild currently risks exhausting the backend's memory ceiling and crashing the backend before it finishes; a fix for this is in progress and the action should be treated as at-risk on the full dataset until it lands. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), failed, or failed at the backfill stage — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume, Retry, or Remove/Dismiss. A **Macro feed** panel lists the four configured FRED economic series (Treasury yield-curve spread, unemployment trend, credit spread, dollar index) with their publication lags, OHLCV proxy tickers, and committed-seed observation counts; shows whether a live API key is detected (env-var name only — no key value is ever displayed); and indicates which wiring legs (severity scoring, regime-switching, study conditioning) are enabled. All macro legs are off by default, so existing dashboard scores and research figures are unchanged unless a leg is deliberately enabled in config. An **Index & benchmark data provenance** panel, placed directly beneath the Macro feed panel, lists every line from the Dashboard's cross-view chart together with its data vendor and true first-recorded date in one place, so auditing the chart's data sources never requires hovering over each line individually; it has its own independent loading, error ("Vendor disclosure unavailable"), and no-data states so a problem there never affects the rest of the page.
 - **Availability heatmap on Data Manager**: a month-by-month trading-day calendar grid where each day cell is color-coded across a perceptually-ordered six-step blue density scale (dark for empty days through bright blue for fully-covered days) and ringed in violet when a scored snapshot exists for that day — two visually distinct signals that never collide in color. The legend is split into two clearly labeled groups, one for the price-data density scale and one for the scored-snapshot ring, so it is always clear which signal you are reading. Day numbers are clearly legible against every shade of cell (per-bucket design tokens chosen for contrast, no hardcoded hex). Months are ordered newest first and two months appear side by side so you see more history without scrolling. Hovering or focusing any cell shows the exact figures — date, symbols with bars versus total, and whether a snapshot exists — worded to name which action is responsible (for example, a day with price data but no snapshot yet reads as a backfill gap, while a scored day reads as a snapshot produced by backfill). Clicking a day prefills the job form's Start and End date inputs; shift-clicking a second day fills in a date range. The heatmap refreshes automatically after any data job completes or data is removed, so coverage changes are always visible immediately.
 - **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports three honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), or **Backend unavailable** (red) — whether the app is opened at `localhost` or the machine's local network (LAN) address. While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed. The backend is hardened for concurrent use: multiple visitors opening the Data page simultaneously share a single coverage computation instead of each triggering a separate expensive one; memory is bounded to one shared copy of the dataset regardless of how many people are connected at once; opening the Data Manager page for the first time after a restart, or several people opening it at once, now reliably finishes loading in roughly 10-20 seconds instead of risking a memory-exhaustion hang, because its price-history load streams data in smaller chunks rather than reading everything at once; and the start script enforces hard limits on concurrent connections, request timeouts, and process memory so that a traffic spike isolates to one process without freezing the host machine.
 - **Daily preflight verdict banner**: every page — Dashboard, Stocks, any stock's detail page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology, and Scanner Runs — shows one shared status strip directly below the header naming a single verdict: **GO** (a quiet green line reading "today's board is current"), **DEGRADED** (a loud amber banner with a bulleted list of the concrete reasons, for example data that has gone several trading days stale, or a live Fetch's freshly-pulled prices disagreeing with the platform's saved, committed reference history — a "live-vs-seed drift" / adjustment seam), or **NO-GO** (a loud red banner that always contains the sentence "do not rely on today's board" — for a serious problem such as the underlying data files being unreadable). Before the first check finishes loading the strip honestly shows "Checking board status…" instead of defaulting to green, and if the backend cannot be reached at all it still renders — in the same red treatment — rather than leaving the page blank. The verdict is computed once and shown identically everywhere, so no two pages can ever disagree about whether today's data is trustworthy.
diff --git a/apps/backend/app/api/data.py b/apps/backend/app/api/data.py
index 3db3561..2450569 100644
--- a/apps/backend/app/api/data.py
+++ b/apps/backend/app/api/data.py
@@ -119,7 +119,12 @@ def data_overview(
         except scanner.AsOfError:
             resolved_asof = None  # graceful: descriptive coverage falls back to the latest stored date
     return {
-        "coverage": data_manager.compute_coverage(session, cfg, as_of=resolved_asof),
+        # ops-hardening iter-2 (J-05): served ONLY from the persisted `coverage_snapshot` row — never a
+        # live `compute_coverage` call on this request path (the whole-table bar-prefill OOM/hang source,
+        # iter-24 evidence). A genuinely missing row serves an honest "not yet computed" partial payload —
+        # never a 500/blank response. The row is written by the ingest finalize hook and the boot warm-up
+        # safety net (`app.engine.data_manager._refresh_ingest_aggregates` / `app.engine.warmup._run_warmup`).
+        "coverage": data_manager.coverage_from_storage(session, cfg, as_of=resolved_asof),
         "runs": data_manager.recent_runs(session, cfg),
         "sources": data_manager.compute_provider_availability(cfg),
         # J-92: the OPTIONAL FRED macro feed catalog + availability (env-detected; committed-seed coverage;
diff --git a/apps/backend/app/engine/data_manager.py b/apps/backend/app/engine/data_manager.py
index e187033..9f6b7cd 100644
--- a/apps/backend/app/engine/data_manager.py
+++ b/apps/backend/app/engine/data_manager.py
@@ -32,6 +32,7 @@ import ctypes.util
 import gc
 import hashlib
 import json
+import logging
 import os
 import threading
 import time
@@ -53,6 +54,7 @@ from app.data_providers.seed_provider import SeedProvider, symbol_to_filename
 from app.db import get_engine
 from app.engine import drift as drift_module
 from app.engine import forward_testing, scanner
+from app.engine import market_phase  # ops-hardening iter-2 (J-05): the ingest finalize hook warms this
 from app.engine.prices import attach_shared_cache, bar_cache, bars_asof, latest_data_date, prefilled_bar_cache
 from app.engine import universe_resolver
 from app.engine.universe_screen import (
@@ -62,6 +64,7 @@ from app.engine.universe_screen import (
     screen_reasons,
 )
 from app.models import (
+    CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
     ForwardReturn,
@@ -76,9 +79,13 @@ from app.models import (
 from app.engine.research import (
     _dataset_version,  # single-sourced cache stamp (J-72/J-87) — never duplicated
     _membership_dataset_version,  # J-100: the NARROW membership-cache stamp (no forward-return term)
+    event_study_cached,  # ops-hardening iter-2 (J-05): the ingest finalize hook warms one default hot key
+    subject_catalog,
 )
 from app.seed_loader import price_load_symbols
 
+logger = logging.getLogger("trendora.data_manager")
+
 # Injectable sleep (J-34): the chunked fetch's inter-request delay + 429 backoff call this. Tests pass
 # their own recorder so backoff/sleep add NO wall-clock (MEMORY: backend-test-suite-runtime).
 _sleep: Callable[[float], None] = time.sleep
@@ -888,6 +895,214 @@ def _compute_coverage_body(
     }
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-2 (J-05) — the coverage_snapshot persisted table. `GET /api/data` is served ONLY
+# from this table (never a live `compute_coverage`/`_compute_coverage_uncached` call on the request path
+# — that whole-table bar-prefill is the documented OOM/hang source, iter-24 evidence). The row is written
+# by the ingest finalize hook (`_refresh_ingest_aggregates`, below) and the boot warm-up safety net
+# (`app.engine.warmup._run_warmup`) — both reuse `_compute_coverage_uncached` verbatim, never a second
+# derivation of the coverage figure.
+# --------------------------------------------------------------------------------------------------
+def _coverage_not_yet_computed_payload(cfg: Config) -> dict:
+    """The honest 'not yet computed' coverage sentinel `coverage_from_storage` serves when no
+    `CoverageSnapshot` row exists yet for the resolved key (before the first ingest finalize hook or the
+    boot warm-up safety net has run). Issues ZERO database queries — only the committed-pool FILE read
+    (`read_pool`, the same file `pool_survivorship`/`_resolved_universe` already read) plus config reads —
+    so this fallback can never pay the whole-table bar-prefill cost the persisted snapshot exists to avoid
+    (AG-8). Every DB-derived figure is honestly zero/null/empty — the SAME shape
+    `_compute_coverage_uncached` already serves for a genuinely empty DB (never a fabricated value)."""
+    pool_count = len({row["symbol"] for row in read_pool()})
+    threshold = cfg.indicators.min_history_bars
+    filters = cfg.universe.filters
+    return {
+        "price_start": None,
+        "price_end": None,
+        "symbol_count": 0,
+        "universe_count": 0,
+        "universe_asof": None,
+        "candidate_pool_count": pool_count,
+        "candidate_universe_count": len(cfg.universe.symbols),
+        "snapshot_count": 0,
+        "snapshot_dates": [],
+        "trading_day_count": 0,
+        "gap_count": 0,
+        "gap_first": None,
+        "gap_last": None,
+        "gaps_preview": [],
+        "per_symbol": [],
+        "diagnostic": {
+            "threshold": threshold,
+            "no_history": [],
+            "thin": [],
+            "intra_series_gaps": [],
+            "affected_count": 0,
+        },
+        "universe_diagnostic": {
+            "asof": None,
+            "candidate_pool_count": pool_count,
+            "admitted_count": 0,
+            "excluded_total": 0,
+            "excluded": {reason: 0 for reason in universe_resolver.EXCLUSION_REASONS},
+            "thresholds": {
+                "min_history_bars": threshold,
+                "min_price": filters.min_price,
+                "min_dollar_vol": filters.min_dollar_vol,
+                "adv_window_days": filters.adv_window_days,
+                "max_staleness_days": filters.max_staleness_days,
+            },
+        },
+        "membership_timeline": {
+            "candidate_pool_count": pool_count,
+            "points": [],
+            "labels": {
+                "survivorship": pool_survivorship(),
+                "warmup": {
+                    "min_history_bars": threshold,
+                    "boundary_date": None,
+                    "label": (
+                        "Coverage has not been computed yet for this database — an ingest job or the "
+                        "background warm-up will populate it shortly."
+                    ),
+                },
+                "universe_relative": (
+                    "Breadth and walk-forward evidence are universe-relative. The dynamic point-in-time "
+                    "universe REDUCES survivorship versus the static current-membership universe (a "
+                    "30-bar name is never ranked against a 1000-bar peer), while residual pool-survivorship "
+                    "remains until a true point-in-time index-constituent feed is added."
+                ),
+            },
+        },
+        "absent_from_latest_snapshot": {
+            "absent_count": 0,
+            "absent_preview": [],
+            "latest_snapshot_date": None,
+            "universe_count": 0,
+            "candidate_pool_count": pool_count,
+        },
+    }
+
+
+def _upsert_coverage_snapshot(
+    session: Session, asof_key: str, dataset_version: str, payload: dict
+) -> None:
+    """Idempotent upsert for ONE `CoverageSnapshot` row keyed by `(asof_key, dataset_version)`: prunes any
+    STALE row for this `asof_key` (an older `dataset_version`), then updates the current-stamp row in
+    place if one already exists or inserts a fresh one. Mirrors `market_phase_cached`'s prune-stale-then-
+    write upsert, generalized to also cover a repeat call under the SAME stamp — this is called
+    unconditionally at the end of every successful ingest (not gated behind a cache-miss check, unlike the
+    `*_cached` read-through caches)."""
+    stale = session.exec(
+        select(CoverageSnapshot).where(
+            CoverageSnapshot.asof_key == asof_key,
+            CoverageSnapshot.dataset_version != dataset_version,
+        )
+    ).all()
+    for row in stale:
+        session.delete(row)
+
+    existing = session.exec(
+        select(CoverageSnapshot).where(
+            CoverageSnapshot.asof_key == asof_key,
+            CoverageSnapshot.dataset_version == dataset_version,
+        )
+    ).first()
+    now = datetime.now(timezone.utc)
+    if existing is not None:
+        existing.payload_json = json.dumps(payload)
+        existing.computed_at = now
+        session.add(existing)
+    else:
+        session.add(CoverageSnapshot(
+            asof_key=asof_key, dataset_version=dataset_version,
+            payload_json=json.dumps(payload), computed_at=now,
+        ))
+    try:
+        session.commit()
+    except Exception:  # a concurrent writer raced us to the same key — best-effort, not a source of truth
+        session.rollback()
+
+
+def refresh_coverage_snapshot_for(session: Session, cfg: Config, resolved_asof: date_cls) -> dict:
+    """Compute + persist the `CoverageSnapshot` row for ONE SPECIFIC already-resolved as-of date (reusing
+    the canonical `_compute_coverage_uncached` verbatim — byte-identical to a fresh compute FOR THAT as-of,
+    never a second derivation). Shared by `refresh_coverage_snapshot` (the current stamp), the ingest
+    finalize hook's per-date warm loop (`_persist_per_date_coverage_snapshots`), and `coverage_from_storage`'s
+    read-path safety net for an already-ingested HISTORICAL as-of that predates this table. Returns the
+    freshly persisted payload."""
+    asof_key = resolved_asof.isoformat()
+    dataset_version = _membership_dataset_version(session, cfg)
+    # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls `membership_timeline_cached`
+    # internally as part of computing this SAME payload — warming that cache is a free side effect of this
+    # one call, never a second derivation.
+    payload = _compute_coverage_uncached(session, cfg, as_of=resolved_asof)
+    _upsert_coverage_snapshot(session, asof_key, dataset_version, payload)
+    return payload
+
+
+def refresh_coverage_snapshot(session: Session, cfg: Config) -> Optional[dict]:
+    """Compute the CURRENT coverage payload (reusing the canonical `_compute_coverage_uncached` verbatim —
+    never a second derivation) and persist it as the `CoverageSnapshot` row for the CURRENT `(asof_key,
+    dataset_version)` key, upserting idempotently. Called by the ingest finalize hook (unconditionally, on
+    every successful backfill/both/rebuild — including a zero-work re-run) and the boot warm-up safety net
+    (only when no row exists yet for the current stamp). Returns the freshly persisted payload, or `None`
+    on a wholly-empty DB (no bars at all — `_resolve_coverage_asof` returns None only then; nothing to
+    snapshot yet). The current stamp resolves `None`→latest, so this is `refresh_coverage_snapshot_for` at
+    that resolved date (byte-identical: `_compute_coverage_uncached(as_of=None)` and `(as_of=latest)` both
+    resolve through `_resolve_coverage_asof` to the SAME latest date)."""
+    resolved_asof = _resolve_coverage_asof(session, None, cfg)
+    if resolved_asof is None:
+        return None
+    return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
+
+
+def _scanner_run_exists(session: Session, asof: date_cls) -> bool:
+    """Whether a real `ScannerRun` snapshot exists for exactly this as-of date — the signal that `asof` is
+    genuinely-ingested historical data (the app-wide as-of switcher, `GET /api/runs`, only ever offers such
+    dates), not a dataless/pre-ingest as-of that must honestly serve the 'not yet computed' sentinel."""
+    return session.exec(
+        select(ScannerRun.asof_date).where(ScannerRun.asof_date == asof).limit(1)
+    ).first() is not None
+
+
+def coverage_from_storage(session: Session, cfg: Config, *, as_of: Optional[date_cls] = None) -> dict:
+    """`GET /api/data`'s coverage block, served from the persisted `CoverageSnapshot` row for the resolved
+    `(asof_key, dataset_version)` key — REPLACES the former request-path call to `compute_coverage`/
+    `_compute_coverage_uncached` (the whole-table bar-prefill OOM/hang source, iter-24 evidence —
+    `compute_coverage` itself is UNCHANGED and still used directly by the ingest finalize hook / boot
+    warm-up safety net / tests that want a genuine live compute).
+
+    Explicit-historical-as-of safety net (iter-2 review, CRITICAL): the ingest finalize hook persists a row
+    for EVERY newly-created snapshot date, so the app-wide as-of switcher normally reads every selectable
+    date straight from storage. If a row is nonetheless missing for an EXPLICIT `as_of` (the switcher
+    selected a date — `data_overview` passes `None` for the default latest-date visit, a concrete date only
+    for an explicit `?as_of=`) that is backed by a REAL `ScannerRun` (an already-ingested historical date,
+    e.g. one ingested BEFORE this table existed), serve the CORRECT coverage for that date — computed once
+    and persisted so the next visit is instant (self-healing) — rather than the false all-zero sentinel.
+    This is an AG-3 correctness guarantee (displayed numbers MUST match the engine's computation) that
+    overrides the AG-8 no-request-compute preference for this rare, deliberate, one-time-per-date path.
+
+    The common default (`as_of=None`) visit and a genuinely dataless as-of (no `ScannerRun`, e.g. pre-first-
+    ingest) still take the honest zero-query 'not yet computed' sentinel — NEVER a live whole-table compute,
+    never a blank/500 response (AG-8)."""
+    resolved_asof = _resolve_coverage_asof(session, as_of, cfg)
+    if resolved_asof is not None:
+        asof_key = resolved_asof.isoformat()
+        dataset_version = _membership_dataset_version(session, cfg)
+        row = session.exec(
+            select(CoverageSnapshot).where(
+                CoverageSnapshot.asof_key == asof_key,
+                CoverageSnapshot.dataset_version == dataset_version,
+            )
+        ).first()
+        if row is not None:
+            return json.loads(row.payload_json)
+        # no persisted row: heal an explicit switcher selection of a real already-ingested historical date
+        # (see docstring) — real coverage, self-healed to storage — rather than a false empty-DB sentinel.
+        if as_of is not None and _scanner_run_exists(session, resolved_asof):
+            return refresh_coverage_snapshot_for(session, cfg, resolved_asof)
+    return _coverage_not_yet_computed_payload(cfg)
+
+
 def compute_availability(session: Session, config: Optional[Config] = None) -> dict:
     """J-61 — the per-trading-date availability derivation. READ-ONLY descriptive metadata over the
     SAME stored bars + stored runs `compute_coverage` reads (never a second derivation of a coverage
@@ -1637,6 +1852,17 @@ class JobProgress:
     non_trading_days: int = 0
     already_snapshotted: int = 0
     error_other: int = 0
+    # ops-hardening iter-2 (J-05) — the ingest finalize hook's inputs/output. `new_snapshot_dates` is
+    # INTERNAL scratch (not serialized, like `_backfill_per_date_seconds_sum` below): the dates THIS run's
+    # `_do_backfill` genuinely persisted a NEW `ScannerRun` for (populated in `_persist()` exactly where it
+    # already branches on `existed_before`), so the finalize hook knows which as-ofs to warm in
+    # `MarketPhaseCache` ("for each newly-created snapshot date" — never every stored date).
+    # `aggregates_refreshed` is the finalize hook's honest output — the subset of `["latest_snapshot",
+    # "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` it actually refreshed —
+    # empty/default until the hook has actually run (never fabricated on an interrupted/failed row; gated
+    # in `_run_detail()` the SAME way `calendar_days` etc. already are).
+    new_snapshot_dates: list[date_cls] = field(default_factory=list)
+    aggregates_refreshed: list[str] = field(default_factory=list)
     # J-34: chunked-fetch progress. `chunk_index` = number of fully-completed chunks (== the durable
     # checkpoint's resume point); `chunk_total` = the deterministic plan size (symbol-batches × date-
     # windows). Both 0 for a non-chunked job (e.g. backfill-only) so the UI hides the chunk indicator.
@@ -1786,6 +2012,10 @@ class JobProgress:
             "non_trading_days": self.non_trading_days,
             "already_snapshotted": self.already_snapshotted,
             "error_other": self.error_other,
+            # ops-hardening iter-2 (J-05): the live job's finalize-hook output so far — empty while running/
+            # before the hook has run (honest; never fabricated), populated once the finalize hook completes
+            # (mirrors how the OTHER live fields above simply read the current in-memory value).
+            "aggregates_refreshed": list(self.aggregates_refreshed),
             "chunk_index": self.chunk_index,  # J-34: completed chunks (== checkpoint resume point)
             "chunk_total": self.chunk_total,  # J-34: total planned chunks
             "passers": self.passers,  # J-35: candidates that passed the screen (became members)
@@ -2632,6 +2862,11 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
         prog.forward_returns_inserted += result["rows_inserted"]
         prog.dates_done += 1
         prog.message = f"snapshots {prog.dates_done}/{prog.dates_total} dates"
+        # ops-hardening iter-2 (J-05): record every date THIS call genuinely created a NEW snapshot for
+        # (never one that already existed — a rare inter-job race, see `existed_before` above) so the
+        # ingest finalize hook knows exactly which as-ofs to warm in `MarketPhaseCache`.
+        if not existed_before:
+            prog.new_snapshot_dates.append(d)
 
     def _persist_isolated(d: date_cls, payload: Optional[dict], secs: float, compute_error: Optional[str]) -> None:
         """J-67 + J-68 — write ONE date with failure isolation: if the worker COMPUTE already failed
@@ -2733,6 +2968,105 @@ def _do_backfill(session: Session, cfg: Config, prog: JobProgress, *, eng: Engin
     prog.error_other = prog.date_failures_total
 
 
+# --------------------------------------------------------------------------------------------------
+# ops-hardening iter-2 (J-05) — the ingest finalize hook: reached at the end of a successful
+# backfill/both/rebuild job (`_run_job`, below). Persists a fresh coverage_snapshot, warms
+# MarketPhaseCache for each snapshot date this run newly created, and warms one default EventStudyCache
+# hot key — reusing each cache's existing compute function, never a second derivation of any of them.
+# --------------------------------------------------------------------------------------------------
+def _persist_per_date_coverage_snapshots(
+    session: Session, cfg: Config, dates: list[date_cls]
+) -> None:
+    """Persist a byte-identical `CoverageSnapshot` row for each as-of in `dates` (the snapshot dates a
+    backfill NEWLY created), so the app-wide as-of switcher serves REAL coverage for each from storage —
+    never the all-zero 'not yet computed' sentinel (the iter-2 review's CRITICAL AG-3 regression: only the
+    single current stamp was persisted, so every OTHER already-ingested date read as an empty DB).
+
+    The CURRENT resolved as-of is skipped (already persisted by `refresh_coverage_snapshot`), so the common
+    single-latest-date backfill filters to nothing and pays NO bar-cache load at all. When there IS extra
+    work, ONE shared, re-entrant `prefilled_bar_cache` covers the whole loop — the whole-table bar scan runs
+    at most once regardless of date count (each per-date `_compute_coverage_uncached` reuses it), so warming
+    N dates costs one load, not N. Each row equals a fresh `_compute_coverage_uncached(as_of=d)`. Per-date
+    isolation (log + continue) so one date's failure never drops the rest; the caller wraps this whole call
+    non-fatally too. Reads only committed bars (backfill adds none), writes only `CoverageSnapshot` rows —
+    so the shared cache never serves a stale series (AG-8: no unbounded request-path load; this is ingest)."""
+    if not dates:
+        return
+    current = _resolve_coverage_asof(session, None, cfg)
+    todo = [d for d in dates if d != current]
+    if not todo:
+        return  # the only newly-created date IS the current stamp (already persisted) — no extra load
+    pool_symbols = {row["symbol"] for row in read_pool()}
+    with prefilled_bar_cache(session, expected_symbols=pool_symbols):
+        for d in todo:
+            try:
+                refresh_coverage_snapshot_for(session, cfg, d)
+            except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date
+                logger.exception("ingest per-date coverage warm failed for %s (non-fatal): %s", d, exc)
+
+
+def _refresh_ingest_aggregates(session: Session, cfg: Config, prog: JobProgress) -> list[str]:
+    """The ingest finalize hook (J-05). Each aggregate is refreshed independently (its own try/except: log
+    + continue) so one aggregate's failure never prevents another from refreshing, and this function itself
+    never raises (the caller in `_run_job` wraps the whole call in its own try/except too, mirroring
+    `_warm_membership_timeline`'s non-fatal contract in warmup.py — an aggregate-refresh failure must never
+    flip an otherwise-successful ingest job to failed). Returns the subset of `["latest_snapshot",
+    "coverage", "membership_timeline", "market_phase", "research_hot_keys"]` ACTUALLY refreshed — never a
+    fabricated category (mirrors the `omitted`/`passers` honesty convention already used elsewhere in this
+    module)."""
+    refreshed: list[str] = []
+
+    if prog.new_snapshot_dates:
+        # this run's own date-loop already created + committed these snapshots (scanner.persist_run_payload
+        # / run_scan, inside `_do_backfill._persist`) before this hook runs — nothing further to compute
+        # here; just acknowledge honestly that a fresh snapshot now exists.
+        refreshed.append("latest_snapshot")
+
+    try:
+        payload = refresh_coverage_snapshot(session, cfg)
+        if payload is not None:
+            refreshed.append("coverage")
+            # `_compute_coverage_uncached` (via `_compute_coverage_body`) already calls
+            # `membership_timeline_cached` internally as part of computing the payload just persisted above
+            # — warmed for free by that SAME call, never a second/separate derivation.
+            refreshed.append("membership_timeline")
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest coverage/membership-timeline refresh failed (non-fatal): %s", exc)
+
+    # iter-2 review (CRITICAL): also persist a per-date coverage_snapshot for every date THIS run newly
+    # created, so the app-wide as-of switcher serves REAL coverage for each historical date from storage —
+    # not the all-zero "not yet computed" sentinel. Still the "coverage" category (no new one); own
+    # try/except (log + continue) so it never flips the job. Skips the current stamp (persisted above) and
+    # is a no-op — no bar-cache load — for the common single-latest-date backfill.
+    try:
+        _persist_per_date_coverage_snapshots(session, cfg, prog.new_snapshot_dates)
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next aggregate
+        logger.exception("ingest per-date coverage warm failed (non-fatal): %s", exc)
+
+    market_phase_warmed = False
+    for d in prog.new_snapshot_dates:
+        try:
+            market_phase.market_phase_cached(session, d, cfg)
+            market_phase_warmed = True
+        except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue to the next date/aggregate
+            logger.exception("ingest market-phase warm failed for %s (non-fatal): %s", d, exc)
+    if market_phase_warmed:
+        refreshed.append("market_phase")
+
+    try:
+        subjects = subject_catalog(cfg)
+        if subjects:
+            # the SAME default (first catalog subject, config default_horizon, episodes view, all-history)
+            # a fresh `/research/event-study` page load with no query params would request — the one hot
+            # key worth warming at ingest (goal.md: "warm default (subject,horizon,all-history) keys").
+            event_study_cached(session, subjects[0]["key"], cfg.walk_forward.default_horizon, cfg)
+            refreshed.append("research_hot_keys")
+    except Exception as exc:  # noqa: BLE001 — non-fatal: log + continue
+        logger.exception("ingest research hot-key warm failed (non-fatal): %s", exc)
+
+    return refreshed
+
... [diff_bound] apps/backend/app/engine/data_manager.py: 60 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/engine/warmup.py b/apps/backend/app/engine/warmup.py
index d9d8189..61c3b21 100644
--- a/apps/backend/app/engine/warmup.py
+++ b/apps/backend/app/engine/warmup.py
@@ -119,6 +119,36 @@ def _warm_membership_timeline(engine: Engine, cfg: Config) -> None:
         logger.exception("membership-timeline cache warm failed (non-fatal): %s", exc)
 
 
+def _warm_coverage_snapshot(engine: Engine, cfg: Config) -> None:
+    """ops-hardening iter-2 (J-05): the boot-time safety net for a not-yet-ingested-once database — persist
+    a `CoverageSnapshot` row for the CURRENT `(asof_key, dataset_version)` stamp ONLY IF no row exists yet
+    for it. Mirrors `_warm_membership_timeline`'s exact contract: opens its OWN session on `engine` (never a
+    request session), is idempotent (a no-op when a row already exists — this is a bootstrap safety net,
+    not a per-boot refresh; the ingest finalize hook is what keeps it fresh thereafter), and is NON-FATAL
+    (any exception is caught + logged here so a coverage-warm failure never aborts the otherwise-successful
+    warm-up). Reads the committed bars/runs only; computes no canonical value — it reuses
+    `data_manager.refresh_coverage_snapshot`, which itself reuses `_compute_coverage_uncached` verbatim."""
+    try:
+        with Session(engine) as session:
+            resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+            if resolved_asof is None:
+                return  # wholly empty DB (no bars at all) — nothing to snapshot yet
+            asof_key = resolved_asof.isoformat()
+            dataset_version = data_manager._membership_dataset_version(session, cfg)
+            existing = session.exec(
+                select(data_manager.CoverageSnapshot).where(
+                    data_manager.CoverageSnapshot.asof_key == asof_key,
+                    data_manager.CoverageSnapshot.dataset_version == dataset_version,
+                )
+            ).first()
+            if existing is not None:
+                return  # already computed under the current stamp — idempotent no-op
+            data_manager.refresh_coverage_snapshot(session, cfg)
+            logger.info("coverage snapshot warmed (asof=%s)", asof_key)
+    except Exception as exc:  # NON-FATAL: a coverage-snapshot warm failure must not fail the whole warm-up
+        logger.exception("coverage snapshot warm failed (non-fatal): %s", exc)
+
+
 def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -> None:
     """The warm-up worker body (runs in the daemon thread). Persists each remaining cadence snapshot via
     the canonical `run_scan` (batched by `config.startup.warmup_batch_size` for progress ticks), then runs
@@ -174,6 +204,12 @@ def _run_warmup(engine: Engine, cfg: Config, prog: "data_manager.JobProgress") -
         # is logged but does NOT flip an otherwise-successful warm-up to `failed` (the cadence snapshots +
         # forward returns already succeeded; a cold `GET /api/data` still serves the bounded miss).
         _warm_membership_timeline(engine, cfg)
+        # ops-hardening iter-2 (J-05): the coverage_snapshot boot-time safety net — own guard, own session,
+        # non-fatal, idempotent (no-op once a row exists) — so a not-yet-ingested-once DB still has a
+        # coverage_snapshot row before the first `GET /api/data` request, without the boot path itself
+        # gaining any new synchronous compute (this step runs strictly in this background warm-up thread,
+        # after `yield`).
+        _warm_coverage_snapshot(engine, cfg)
         prog.status = "ok"
         prog.message = f"history {prog.dates_total}/{prog.dates_total}"
     except Exception as exc:  # NON-FATAL: caught + logged, never re-raised out of the thread
diff --git a/apps/backend/app/models.py b/apps/backend/app/models.py
index 3a19595..f09fc15 100644
--- a/apps/backend/app/models.py
+++ b/apps/backend/app/models.py
@@ -590,6 +590,57 @@ class MembershipTimelineCache(SQLModel, table=True):
     created_at: datetime
 
 
+# --- ops-hardening iter-2 (J-05) coverage derived-aggregate snapshot (a PERFORMANCE cache, not a
+# snapshot) -----------------------------------------------------------------------------------
+class CoverageSnapshot(SQLModel, table=True):
+    """A STANDALONE, create_all-managed persisted snapshot of `GET /api/data`'s coverage block
+    (`app.engine.data_manager._compute_coverage_uncached`).
+
+    Like `EventStudyCache` / `MarketPhaseCache` / `MembershipTimelineCache`, this is EXPLICITLY NOT a
+    scanner snapshot — the *Snapshots are immutable* critical anti-goal binds ONLY `scanner_runs` /
+    `scanner_results` / `*_scores` / `forward_returns`. This is legitimately mutable derived/cache state:
+    it stores the SERIALIZED `_compute_coverage_uncached(...)` payload (byte-identical to a fresh compute
+    — a cache of the deterministic read-only derivation, never a second computation or a hand-authored
+    value) keyed by the resolved as-of + a dataset-version stamp, so `GET /api/data` serves the stored
+    aggregate instead of recomputing it on the request path (No recompute in the read path).
+
+    WHY: `_compute_coverage_uncached` wraps the whole derivation in one shared `prefilled_bar_cache`
+    (a one-time whole-universe bar load) so a cold `/api/data` request paid this cost synchronously on
+    the request path — the documented OOM/hang source (iter-24 evidence). This table moves that compute
+    to the ingest finalize hook (`app.engine.data_manager._run_job`, on a successful backfill/both/rebuild)
+    and a boot-time warm-up safety net (`app.engine.warmup._run_warmup`), so the request path only ever
+    reads a stored row (or serves an honest "not yet computed" sentinel — never a live whole-table
+    compute on that path).
+
+    A STANDALONE table (its own `create_all`-managed table) is used deliberately so the iter-12
+    `_ADDITIVE_COLUMNS` trap does NOT apply — a fresh DB carries it from `create_db_and_tables`, and no
+    existing table gains a column.
+
+    CACHE KEY: `(asof_key, dataset_version)`:
+      - `asof_key` is the resolved as-of cutoff ISO date — the SAME value `_coverage_cache_key` already
+        computes for the in-process single-flight cache (`_resolve_coverage_asof`).
+      - `dataset_version` is the SAME narrow `_membership_dataset_version` stamp (J-100) the in-process
+        coverage cache and `MembershipTimelineCache` already key on (snapshot set + bars manifest +
+        `min_history_bars` — NOT the forward-return count), so this row refreshes exactly when a real
+        membership/bars change could change the served coverage, and is reused across the warm-up's
+        forward-return churn.
+
+    `payload_json` is the full serialized `_compute_coverage_uncached(...)` derivation (byte-identical to
+    a fresh compute); `computed_at` is bookkeeping/audit only (no freshness indicator is rendered this
+    iteration). Unique on the composite key so a write is an idempotent upsert."""
+
+    __tablename__ = "coverage_snapshot"
+    __table_args__ = (
+        UniqueConstraint("asof_key", "dataset_version", name="uq_coverage_snapshot_key"),
+    )
+
+    id: Optional[int] = Field(default=None, primary_key=True)
+    asof_key: str = Field(index=True)  # resolved as-of ISO cutoff date (matches _coverage_cache_key)
+    dataset_version: str  # the SAME narrow stamp _membership_dataset_version produces
+    payload_json: str  # the serialized _compute_coverage_uncached(...) derivation (byte-identical)
+    computed_at: datetime  # UTC bookkeeping/audit timestamp — not rendered as a freshness indicator
+
+
 # --- iter-7 watchlist (USER-MUTABLE — the product's FIRST user-write surface; J-11) ----------
 class Watchlist(SQLModel, table=True):
     """One user-saved stock on the persistent research watchlist (iter-7). The product's FIRST
diff --git a/apps/backend/tests/test_api_data.py b/apps/backend/tests/test_api_data.py
index d6f87ff..10a1292 100644
--- a/apps/backend/tests/test_api_data.py
+++ b/apps/backend/tests/test_api_data.py
@@ -42,7 +42,14 @@ from app.models import DailyPrice, DataProviderRun, ImportCheckpoint
 def data_api_engine(tmp_path):
     """A tiny isolated DB (a few SPY bars so a trading calendar + latest date exist), set as the process
     engine for the duration of the test and restored afterward — so a job's appended DataProviderRun
-    row writes here, never to the shared `loaded_engine`."""
+    row writes here, never to the shared `loaded_engine`.
+
+    ops-hardening iter-2 (J-05): `GET /api/data`'s coverage block is now served ONLY from the persisted
+    `coverage_snapshot` row (never a live compute on the request path) — this fixture represents a DB that
+    has already been through an ingest, so it seeds that row here (via the SAME `refresh_coverage_snapshot`
+    the real ingest finalize hook / boot warm-up safety net use — never a second derivation), keeping
+    every existing coverage-shape assertion in this file reading the SAME live-equivalent numbers as
+    before this iteration."""
     prev = db_module._engine
     engine = make_engine(f"sqlite:///{tmp_path / 'data_api.db'}")
     create_db_and_tables(engine)
@@ -50,6 +57,8 @@ def data_api_engine(tmp_path):
         for d in (date(2024, 1, 2), date(2024, 1, 3)):
             session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
         session.commit()
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, get_config())
     db_module.set_engine(engine)
     yield engine
     db_module.set_engine(prev)
@@ -95,6 +104,68 @@ def test_get_data_overview_shape(data_api_engine):
         assert set(s) == {"id", "label", "needs_key", "env_var", "supports_market_cap", "available", "reason"}
 
 
+def test_get_data_overview_serves_coverage_from_storage_zero_prefill_calls(data_api_engine, monkeypatch):
+    """ops-hardening iter-2 (J-05 / TC-6 pytest-level proxy) — GET /api/data's coverage block is served
+    BYTE-IDENTICAL from the persisted `coverage_snapshot` row (seeded by the fixture, representing "already
+    ingested") with ZERO calls to `_compute_coverage_uncached`/`prefilled_bar_cache` on the request —
+    simulating "restart, then first request": a fresh session reading an already-ingested DB never pays a
+    live whole-table compute on this path (AG-8)."""
+    with Session(data_api_engine) as session:
+        cfg = get_config()
+        expected = data_manager._compute_coverage_uncached(session, cfg, as_of=None)  # ground truth
+
+    def _boom(*_a, **_k):
+        raise AssertionError("data_overview must never call this on the request path")
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _boom)
+    monkeypatch.setattr(data_manager, "prefilled_bar_cache", _boom)
+    with Session(data_api_engine) as session:
+        payload = data_overview(session=session)
+    assert payload["coverage"] == expected
+
+
+def test_get_data_overview_zero_coverage_rows_serves_honest_sentinel_never_500(tmp_path, monkeypatch):
+    """TC-9 — a database with zero `coverage_snapshot` rows (a simulated pre-ingest state; real bars ARE
+    present) still serves an honest all-zero/empty coverage block (never an exception, never a live
+    whole-table compute) — the API layer's 200-vs-500 status is FastAPI's own concern; what this proves is
+    that `data_overview` itself does not raise and does not call the whole-table-prefill path."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'no_snapshot_yet.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        for d in (date(2024, 1, 2), date(2024, 1, 3)):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+
+    def _boom(*_a, **_k):
+        raise AssertionError("must never call _compute_coverage_uncached when no coverage_snapshot row exists")
+
+    monkeypatch.setattr(data_manager, "_compute_coverage_uncached", _boom)
+    monkeypatch.setattr(data_manager, "prefilled_bar_cache", _boom)
+    with Session(engine) as session:
+        payload = data_overview(session=session)  # must not raise — never a 500/blank page
+    cov = payload["coverage"]
+    assert cov["symbol_count"] == 0  # honest sentinel — never a live-derived 1, despite real SPY bars
+    assert cov["snapshot_count"] == 0
+    assert cov["per_symbol"] == []
+    assert cov["universe_diagnostic"]["excluded"] == {
+        "below_history": 0, "stale_series": 0, "below_price": 0, "below_adv": 0,
+    }
+    assert cov["membership_timeline"]["points"] == []
+    assert cov["absent_from_latest_snapshot"]["absent_count"] == 0
+
+
+def test_get_data_overview_coverage_from_storage_empty_db_still_graceful(tmp_path):
+    """A wholly empty DB (no bars at all) also serves the honest sentinel gracefully — no crash on the
+    genuinely-empty-DB edge (`_resolve_coverage_asof` returns None; `coverage_from_storage` short-circuits
+    straight to the static sentinel)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'wholly_empty.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        payload = data_overview(session=session)
+    assert payload["coverage"]["symbol_count"] == 0
+    assert payload["coverage"]["price_start"] is None
+
+
 def test_get_data_overview_carries_capacity_snapshot(data_api_engine):
     """Item K (iter-24 fast-platform pass): GET /api/data carries an additive `capacity` key — the DB
     storage-footprint snapshot (file size + row counts for the three largest tables), exact on the tiny
diff --git a/apps/backend/tests/test_data_manager.py b/apps/backend/tests/test_data_manager.py
index e111fbd..4933157 100644
--- a/apps/backend/tests/test_data_manager.py
+++ b/apps/backend/tests/test_data_manager.py
@@ -17,6 +17,7 @@ backfill proof loads the committed seed and runs the real engines ONCE (module-s
 from __future__ import annotations
 
 import json
+import socket
 import time
 from datetime import date, datetime, timedelta
 from pathlib import Path
@@ -30,7 +31,7 @@ from app.config import load_config
 from app.db import create_db_and_tables, make_engine
 from app.data_providers.base import Bar, PriceProvider, ProviderUnavailableError, RateLimitError
 from app.engine import data_manager
-from app.engine import forward_testing, scanner
+from app.engine import forward_testing, market_phase, scanner
 from app.engine.data_manager import (
     JobProgress,
     _chunk_plan,
@@ -64,6 +65,7 @@ from app.engine.data_manager import (
 from app.engine.forward_testing import compute_forward_aggregates
 from app.engine.scoring import score_stocks
 from app.models import (
+    CoverageSnapshot,
     DailyPrice,
     DataProviderRun,
     ForwardReturn,
@@ -1000,6 +1002,395 @@ def test_backfill_error_other_uncapped_past_sample_limit(backfilled_job, monkeyp
     assert prog.snapshots_created + prog.already_snapshotted + prog.error_other == prog.dates_total
 
 
+# ==================================================================================================
+# ops-hardening iter-2 (J-05): the ingest finalize hook — coverage_snapshot persistence, market-phase/
+# membership-timeline/research hot-key warming, and the aggregates_refreshed honesty gate.
+#
+# `finalize_hook_engine` is a TINY hand-built DB (mirrors `coverage_engine`'s own style) — fast, no full
+# seed load needed: the finalize hook's sub-steps (`_compute_coverage_uncached`, `market_phase_cached`,
+# `event_study_cached`) all degrade gracefully on sparse data (the SAME graceful-empty-DB behavior
+# `coverage_engine`'s own tests already exercise, since `read_pool()` always reads the REAL committed
+# candidate-pool file regardless of this tiny DB's contents).
+# ==================================================================================================
+@pytest.fixture()
+def finalize_hook_engine(tmp_path):
+    """A tiny hand-built DB with one stored ScannerRun + ScannerResult on a single as-of date — enough for
+    every finalize-hook sub-step to run for real."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'finalize.db'}")
+    create_db_and_tables(engine)
+    d = date(2024, 3, 4)
+    with Session(engine) as session:
+        session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        run = ScannerRun(
+            asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+            regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+            new_high_low_json="{}", candidate_counts_json="{}",
+        )
+        session.add(run)
+        session.commit()
+        session.refresh(run)
+        session.add(ScannerResult(
+            run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+            entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+            setup_status="Actionable", rank=1, record_json="{}",
+        ))
+        session.commit()
+    return engine, d
+
+
+def test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates(finalize_hook_engine):
+    """TC-1/TC-5 — a finalize hook call for a job that newly created a snapshot on `d` persists exactly one
+    `coverage_snapshot` row for the current stamp and reports every category this fixture's data supports
+    as refreshed: `latest_snapshot` (this run created a snapshot), `coverage` + `membership_timeline` (one
+    compute warms both), `market_phase` (the new date), `research_hot_keys` (the default hot key)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="finalize-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert set(refreshed) == {
+        "latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys",
+    }
+    with Session(engine) as session:
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1
+        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+        assert rows[0].asof_key == resolved_asof.isoformat()
+        assert rows[0].dataset_version == data_manager._membership_dataset_version(session, cfg)
+
+
+def test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute(finalize_hook_engine):
+    """TC-8 — the persisted payload_json is byte-identical (field-by-field) to a direct fresh
+    `_compute_coverage_uncached` call for the same session state (AG-3: storage is re-served, never
+    re-derived)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="byte-identity-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    with Session(engine) as session:
+        row = session.exec(select(CoverageSnapshot)).one()
+        stored = json.loads(row.payload_json)
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+    assert stored == fresh
+
+
+def test_finalize_hook_market_phase_computed_exactly_once_not_on_subsequent_read(
+    finalize_hook_engine, monkeypatch
+):
+    """TC-4 — `compute_market_phase` executes exactly once per newly-created date, during the finalize
+    hook; a subsequent read of the SAME as-of serves from `MarketPhaseCache` (zero further compute calls)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    calls: list[int] = []
+    orig = market_phase.compute_market_phase
+
+    def _counting(*args, **kwargs):
+        calls.append(1)
+        return orig(*args, **kwargs)
+
+    monkeypatch.setattr(market_phase, "compute_market_phase", _counting)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="market-phase-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert len(calls) == 1, "compute_market_phase should run exactly once, during the finalize hook"
+
+    # a subsequent read of the SAME as-of must serve from the cache — zero additional compute calls.
+    with Session(engine) as session:
+        market_phase.market_phase_cached(session, d, cfg)
+    assert len(calls) == 1, "a subsequent read must serve from MarketPhaseCache, not recompute"
+
+
+def test_finalize_hook_only_warms_market_phase_for_newly_created_dates(finalize_hook_engine):
+    """A finalize hook call with an EMPTY `new_snapshot_dates` (e.g. a zero-work re-run) warms neither
+    `market_phase` nor `latest_snapshot` — never a fabricated category for work that did not happen —
+    while `coverage`/`membership_timeline`/`research_hot_keys` still refresh unconditionally."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+    with Session(engine) as session:
+        prog = JobProgress(job_id="zero-work-probe", kind="backfill", start=d, end=d)
+        # prog.new_snapshot_dates deliberately left empty — simulates a zero-work re-run.
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "market_phase" not in refreshed
+    assert "latest_snapshot" not in refreshed
+    assert {"coverage", "membership_timeline", "research_hot_keys"} <= set(refreshed)
+
+
+def test_finalize_hook_partial_failure_isolated_other_aggregates_still_refresh(
+    finalize_hook_engine, monkeypatch
+):
+    """A single aggregate's failure (research hot-key warm, forced) does not prevent the OTHERS
+    (`latest_snapshot`/`coverage`/`membership_timeline`/`market_phase`) from refreshing — log + continue,
+    never raise (mirrors `_warm_membership_timeline`'s non-fatal contract)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced research hot-key failure")
+
+    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="partial-failure-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert "research_hot_keys" not in refreshed
+    assert {"latest_snapshot", "coverage", "membership_timeline", "market_phase"} <= set(refreshed)
+
+
+def test_finalize_hook_never_raises_even_when_everything_fails(finalize_hook_engine, monkeypatch):
+    """The finalize hook never raises even when EVERY compute-based sub-step fails (only the
+    zero-compute `latest_snapshot` acknowledgment survives) — `_run_job`'s own call site additionally
+    wraps this call, but the function itself is designed to never propagate."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _boom(*_a, **_k):
+        raise RuntimeError("forced failure")
+
+    monkeypatch.setattr(data_manager, "refresh_coverage_snapshot", _boom)
+    monkeypatch.setattr(market_phase, "market_phase_cached", _boom)
+    monkeypatch.setattr(data_manager, "event_study_cached", _boom)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="all-fail-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)  # must not raise
+    assert refreshed == ["latest_snapshot"]
+
+
+def test_finalize_hook_makes_no_network_call(finalize_hook_engine, monkeypatch):
+    """AG-9 / TC-19 — the finalize hook's aggregate-refresh calls issue ZERO outbound network calls (every
+    reused compute function is a pure DB-backed derivation, never a live provider)."""
+    engine, d = finalize_hook_engine
+    cfg = load_config()
+
+    def _no_network(*_a, **_k):
+        raise AssertionError("unexpected network call during the ingest finalize hook")
+
+    monkeypatch.setattr(socket.socket, "connect", _no_network)
+    with Session(engine) as session:
+        prog = JobProgress(job_id="no-network-probe", kind="backfill", start=d, end=d)
+        prog.new_snapshot_dates = [d]
+        refreshed = data_manager._refresh_ingest_aggregates(session, cfg, prog)
+    assert refreshed  # completed successfully with zero socket.connect calls
+
+
+def test_run_detail_omits_aggregates_refreshed_until_computed():
+    """TC-13/TC-14 — mirrors `test_run_detail_omits_breakdown_until_computed`: a not-yet-computed (fresh,
+    `_create_run_record`-time) backfill row serves `aggregates_refreshed` null; an INTERRUPTED row whose
+    finalize hook never ran also serves null (the breakdown fields ARE computed — the date-loop ran — but
+    `aggregates_refreshed` stays at its empty JobProgress default, never a fabricated list — TC-13); a
+    fetch/expand row serves null unconditionally (`_breakdown_computed` is always False for those kinds —
+    TC-14); a genuinely computed row serves its real list."""
+    fresh = JobProgress(job_id="never-ran", kind="backfill", start=date(2024, 1, 1), end=date(2025, 6, 1))
+    assert data_manager._run_detail(fresh)["aggregates_refreshed"] is None
+
+    # TC-13: interrupted between the date-loop and the finalize hook — calendar_days IS computed (the
+    # date-loop ran and set it), but aggregates_refreshed stays empty (the hook never ran).
+    interrupted = JobProgress(
+        job_id="interrupted", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29)
+    )
+    interrupted.calendar_days, interrupted.dates_total, interrupted.non_trading_days = 28, 19, 9
+    interrupted.already_snapshotted, interrupted.snapshots_created, interrupted.error_other = 0, 19, 0
+    assert data_manager._run_detail(interrupted)["aggregates_refreshed"] is None
+
+    # TC-14: a fetch kind never routes through the finalize hook — null regardless of any (hypothetical,
+    # impossible-in-practice) populated field, since `_breakdown_computed` is always False for this kind.
+    fetch_kind = JobProgress(job_id="fetch-kind", kind="fetch", start=date(2024, 1, 1), end=date(2024, 1, 1))
+    fetch_kind.aggregates_refreshed = ["coverage"]
+    assert data_manager._run_detail(fetch_kind)["aggregates_refreshed"] is None
+
+    done = JobProgress(job_id="ran", kind="backfill", start=date(2026, 5, 2), end=date(2026, 5, 29))
+    done.calendar_days, done.dates_total, done.non_trading_days = 28, 19, 9
+    done.already_snapshotted, done.snapshots_created, done.error_other = 0, 19, 0
+    done.aggregates_refreshed = ["coverage", "market_phase"]
+    assert data_manager._run_detail(done)["aggregates_refreshed"] == ["coverage", "market_phase"]
+
+
+def test_do_backfill_new_snapshot_dates_tracks_genuinely_new_dates_only(backfilled_job):
+    """ops-hardening iter-2 (J-05) — `_persist` populates `prog.new_snapshot_dates` with exactly the dates
+    THIS call genuinely created a NEW snapshot for (never a date that already existed) — the finalize
+    hook's input for which as-ofs to warm in `MarketPhaseCache`. A fresh single-date window (re-queried
+    live, so this is safe regardless of what other tests in this module already touched) proves the
+    fresh-create case; re-running the SAME date proves the already-exists case records nothing new."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in trading if d not in snapshotted)
+
+    prog = JobProgress(job_id="new-snapshot-dates-probe", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog, eng=engine)
+    assert prog.new_snapshot_dates == [fresh_date]
+    assert prog.snapshots_created == 1
+
+    # re-run the SAME date: it already exists now -> nothing new is recorded.
+    prog2 = JobProgress(job_id="new-snapshot-dates-probe-2", kind="backfill", start=fresh_date, end=fresh_date)
+    with Session(engine) as session:
+        data_manager._do_backfill(session, cfg, prog2, eng=engine)
+    assert prog2.new_snapshot_dates == []
+    assert prog2.snapshots_created == 0
+    assert prog2.already_snapshotted == 1
+
+
+def test_run_data_job_backfill_wires_finalize_hook_end_to_end(backfilled_job):
+    """ops-hardening iter-2 (J-05) end-to-end: a real backfill job dispatched through `run_data_job` (the
+    SAME path the API uses) reaches the finalize hook, persists a `coverage_snapshot` row, and the job's
+    final summary (the SAME dict `GET /api/data/jobs/{id}` serves) carries a non-empty
+    `aggregates_refreshed`. Searches from the LATEST end of the trading calendar (the other new-date test
+    above searches from the earliest) so the two never contend for the same fresh date."""
+    engine = backfilled_job["engine"]
+    cfg = backfilled_job["cfg"]
+    with Session(engine) as session:
+        trading = _trading_days(session, cfg)
+        snapshotted = set(session.exec(select(ScannerRun.asof_date)).all())
+    fresh_date = next(d for d in reversed(trading) if d not in snapshotted)
+
+    job = create_job("backfill", fresh_date, fresh_date)
+    summary = run_data_job(job.job_id, config=cfg, engine=engine)
+    assert summary["status"] == "ok"
+    assert set(summary["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}
+
+    with Session(engine) as session:
+        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+        version = data_manager._membership_dataset_version(session, cfg)
+        row = session.exec(
+            select(CoverageSnapshot).where(
+                CoverageSnapshot.asof_key == resolved_asof.isoformat(),
+                CoverageSnapshot.dataset_version == version,
+            )
+        ).first()
+        assert row is not None
+
+    # the SAME dict shape GET /api/data's `runs` list serves (`recent_runs` -> `_run_detail` for the
+    # persisted row) also carries the finalize hook's output — one computation, two servings.
+    with Session(engine) as session:
+        persisted = recent_runs(session, cfg)
+    this_run = next(r for r in persisted if r["kind"] == "backfill" and r["start"] == fresh_date.isoformat())
+    assert set(this_run["aggregates_refreshed"]) >= {"latest_snapshot", "coverage", "membership_timeline"}
+
+
+def test_fetch_kind_run_never_carries_aggregates_refreshed(tmp_path):
+    """TC-14 — a completed `fetch` run's persisted detail always carries `aggregates_refreshed: null` (the
+    finalize hook is gated to backfill/both/rebuild-like kinds only in `_run_job`; a fetch never reaches
+    it)."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'fetch_only.db'}")
+    create_db_and_tables(engine)
+    with Session(engine) as session:
+        session.add(DailyPrice(
+            symbol="SPY", date=date(2024, 1, 2), open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0,
+        ))
+        session.commit()
+    cfg = load_config()
+
+    class _EmptyProvider(PriceProvider):
+        def get_daily(self, symbol, start=None, end=None):
+            return []  # a successful fetch that finds no new bars — never a fabricated one
+
+    job = create_job("fetch", date(2024, 1, 2), date(2024, 1, 2), source="yahoo")
+    summary = run_data_job(
+        job.job_id, config=cfg, engine=engine, provider=_EmptyProvider(), sleep_fn=_noop_sleep,
+        seed_dir=tmp_path,
+    )
+    assert summary["aggregates_refreshed"] == []  # the live in-memory default (never populated for fetch)
+    with Session(engine) as session:
+        persisted = recent_runs(session, cfg)
+    this_run = next(r for r in persisted if r["kind"] == "fetch")
+    assert this_run["aggregates_refreshed"] is None  # the persisted/served view: null for a fetch kind
+
+
+# ==================================================================================================
+# iter-2 review (CRITICAL regression): the app-wide as-of switcher (J-93/J-94) must serve REAL coverage
+# for EVERY already-ingested date — not just the DB's single current stamp. Before the fix, only the
+# current stamp got a coverage_snapshot row, so any OTHER selectable historical date read as an all-zero
+# empty-DB sentinel (an AG-3 violation on the shipped switcher). Two layers close it: (1) the ingest
+# finalize hook persists a per-date row for every NEWLY-created date; (2) coverage_from_storage self-heals
+# an explicit historical selection that has a real ScannerRun but no row (a legacy pre-table date).
+# ==================================================================================================
+@pytest.fixture()
+def two_snapshot_dates_engine(tmp_path):
+    """A tiny DB with TWO stored ScannerRun/ScannerResult dates (an older historical date + a newer/latest
+    date), each with one priced bar — enough to prove per-date coverage differs from the current stamp."""
+    engine = make_engine(f"sqlite:///{tmp_path / 'two_dates.db'}")
+    create_db_and_tables(engine)
+    d_old, d_new = date(2024, 3, 1), date(2024, 3, 4)
+    with Session(engine) as session:
+        for d in (d_old, d_new):
+            session.add(DailyPrice(symbol="SPY", date=d, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0))
+        session.commit()
+        for d in (d_old, d_new):
+            run = ScannerRun(
+                asof_date=d, created_at=datetime(2024, 3, 4), provider="seed", benchmark="SPY",
+                regime_score=50.0, regime_label="Choppy", regime_components_json="[]",
+                new_high_low_json="{}", candidate_counts_json="{}",
+            )
+            session.add(run)
+            session.commit()
+            session.refresh(run)
+            session.add(ScannerResult(
+                run_id=run.id, ticker="AAA", name="AAA Corp", leadership_score=1.0, leadership_bucket="Leader",
+                entry_quality_score=1.0, entry_quality_bucket="Good", risk_score=1.0, risk_bucket="Low",
+                setup_status="Actionable", rank=1, record_json="{}",
+            ))
+            session.commit()
+    return engine, d_old, d_new
+
+
+def test_finalize_hook_persists_per_date_coverage_for_historical_switcher_date(two_snapshot_dates_engine):
+    """iter-2 review fix, layer 1 — a backfill that newly created a NON-latest (historical) snapshot date
+    persists a per-date coverage_snapshot for it, so coverage_from_storage serves REAL coverage for that
+    date (byte-identical to a fresh compute-at-that-date; AG-3) — never the all-zero sentinel. The CURRENT
+    stamp row is unaffected, and there are now exactly two rows (old + latest), not one."""
+    engine, d_old, d_new = two_snapshot_dates_engine
+    cfg = load_config()
+    # a backfill whose date-loop newly created the OLDER (historical, non-latest) date
+    with Session(engine) as session:
+        prog = JobProgress(job_id="hist-per-date-probe", kind="backfill", start=d_old, end=d_old)
+        prog.new_snapshot_dates = [d_old]
+        data_manager._refresh_ingest_aggregates(session, cfg, prog)
+
+    with Session(engine) as session:
+        # the historical date is served from storage, byte-identical to a fresh compute-at-d_old...
+        cov_old = data_manager.coverage_from_storage(session, cfg, as_of=d_old)
+        fresh_old = data_manager._compute_coverage_uncached(session, cfg, as_of=d_old)
+        assert cov_old == fresh_old
+        assert cov_old["symbol_count"] == 1  # REAL coverage (the sentinel would be 0) — the regression
+        assert cov_old["universe_asof"] == d_old.isoformat()
+        # ...and the current/latest stamp is still served correctly too (two distinct rows now exist)
+        cov_new = data_manager.coverage_from_storage(session, cfg, as_of=d_new)
+        assert cov_new["universe_asof"] == d_new.isoformat()
+        assert len(session.exec(select(CoverageSnapshot)).all()) == 2
+
+
+def test_coverage_from_storage_self_heals_explicit_legacy_historical_asof(two_snapshot_dates_engine):
+    """iter-2 review fix, layer 2 — an EXPLICIT historical as-of backed by a real ScannerRun but with NO
+    persisted coverage_snapshot row (a legacy date ingested before this table existed) is served REAL
... [diff_bound] apps/backend/tests/test_data_manager.py: 25 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_warmup.py b/apps/backend/tests/test_warmup.py
index bb283a3..0b34d55 100644
--- a/apps/backend/tests/test_warmup.py
+++ b/apps/backend/tests/test_warmup.py
@@ -32,6 +32,7 @@ early as-of date (less history → faster) and never the latest.
 """
 from __future__ import annotations
 
+import json
 import threading
 from datetime import date
 
@@ -56,6 +57,7 @@ from app.engine.warmup import (
 from app.engine.data_manager import _membership_timeline, membership_timeline_cached
 from app.engine.research import _membership_dataset_version
 from app.models import (
+    CoverageSnapshot,
     ForwardReturn,
     MembershipTimelineCache,
     ScannerResult,
@@ -329,6 +331,80 @@ def test_membership_timeline_cache_warm_failure_is_nonfatal(early_engine, monkey
     warmup_mod._WARMUP_THREAD = None
 
 
+# ==================================================================================================
+# ops-hardening iter-2 (J-05) — the coverage_snapshot boot-time safety net: a not-yet-ingested-once DB
+# gets exactly one persisted coverage_snapshot row after the background warm-up finishes, computed
+# strictly in this background thread (never on the boot/request path), idempotent, and non-fatal.
+# ==================================================================================================
+def test_warmup_precomputes_coverage_snapshot_if_missing(warmed_engine):
+    """After the background warm-up finishes, a `CoverageSnapshot` row exists for the CURRENT (asof_key,
+    dataset_version) stamp — the boot-time safety net for a not-yet-ingested-once DB, run strictly in this
+    background warm-up thread (never blocking `yield`/serving). Byte-identical to a fresh
+    `_compute_coverage_uncached` compute (a cache of the deterministic derivation, not a second
+    computation)."""
+    engine, cfg = warmed_engine["engine"], warmed_engine["cfg"]
+    with Session(engine) as session:
+        resolved_asof = data_manager._resolve_coverage_asof(session, None, cfg)
+        version = data_manager._membership_dataset_version(session, cfg)
+        rows = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows) == 1, f"expected exactly one warmed coverage_snapshot row, got {len(rows)}"
+        assert rows[0].asof_key == resolved_asof.isoformat()
+        assert rows[0].dataset_version == version
+        fresh = data_manager._compute_coverage_uncached(session, cfg, as_of=None)
+        stored = json.loads(rows[0].payload_json)
+    assert stored == fresh
+
+
+def test_warmup_coverage_snapshot_is_noop_when_already_present(early_engine):
+    """The boot safety net is a no-op when a `coverage_snapshot` row already exists for the current stamp
+    — it does not recompute/overwrite on every boot; only the ingest finalize hook refreshes it
+    thereafter."""
+    engine, cfg = early_engine
+    ensure_latest_snapshot(engine, cfg)  # latest servable
+    with Session(engine) as session:
+        data_manager.refresh_coverage_snapshot(session, cfg)  # seed one row directly (a prior ingest)
+        rows_before = session.exec(select(CoverageSnapshot)).all()
+        assert len(rows_before) == 1
+        computed_at_before = rows_before[0].computed_at
+
+    warmup_mod._warm_coverage_snapshot(engine, cfg)  # the safety net — must see the row and no-op
+
+    with Session(engine) as session:
+        rows_after = session.exec(select(CoverageSnapshot)).all()
+    assert len(rows_after) == 1
+    assert rows_after[0].computed_at == computed_at_before  # untouched — no recompute
+
+
+def test_warmup_coverage_snapshot_warm_failure_is_nonfatal(early_engine, monkeypatch, caplog):
+    """A failure precomputing the coverage snapshot during warm-up is CAUGHT + logged and does NOT flip an
+    otherwise-successful warm-up to `failed` (mirrors
+    `test_membership_timeline_cache_warm_failure_is_nonfatal`)."""
+    engine, cfg = early_engine
+    ensure_latest_snapshot(engine, cfg)  # latest servable before the warm-up
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+
+    def _boom(*_args, **_kwargs):
+        raise RuntimeError("forced coverage snapshot warm failure")
+
+    monkeypatch.setattr(warmup_mod.data_manager, "refresh_coverage_snapshot", _boom)
+    with caplog.at_level("ERROR"):
+        job_id = start_warmup(engine, cfg)
+        _join_warmup(job_id)
+
+    rec = data_manager.get_job(job_id)
+    # the warm-up still settled OK (the coverage-warm failure is non-fatal — it did not fail the job).
+    assert rec is not None and rec["status"] == "ok"
+    assert any("coverage snapshot warm failed" in r.message.lower() for r in caplog.records)
+    # no stale/garbage row was written by the failed warm (the inner compute raised before persist).
+    with Session(engine) as session:
+        assert session.exec(select(CoverageSnapshot)).all() == []
+
+    monkeypatch.undo()
+    _clear_warmup_registry()
+    warmup_mod._WARMUP_THREAD = None
+
+
 def test_lifespan_serves_dashboard_200_while_warmup_in_flight(tmp_path_factory, monkeypatch):
     """The J-40 keystone integration proof named verbatim in goal.md acceptance: the SERVER is serving —
     the lifespan has yielded, the latest snapshot is present, `GET /api/dashboard` returns 200 and the
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 78ee308..017d1ed 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -2366,6 +2366,11 @@ export interface DataRun {
   non_trading_days: number | null;
   already_snapshotted: number | null;
   error_other: number | null;
+  // ops-hardening iter-2 (J-05) — which downstream aggregates (coverage, latest snapshot, membership
+  // timeline, market phase, research hot-keys) this run's ingest finalize hook refreshed. null for a
+  // fetch/expand run and for a not-yet-computed/interrupted row (matches the calendar_days-style
+  // nullability convention above — never a fabricated list).
+  aggregates_refreshed: string[] | null;
   bars_fetched: number | null;
   passers: number | null; // J-35 expand screen outcome (null for non-expand runs)
   omitted_total: number | null; // J-35 expand screen outcome (null otherwise)
@@ -2581,6 +2586,9 @@ export interface DataJob {
   non_trading_days?: number;
   already_snapshotted?: number;
   error_other?: number;
+  // ops-hardening iter-2 (J-05): the live job's finalize-hook output so far — empty/absent while running
+  // or before the hook has run (honest; never fabricated), populated once the finalize hook completes.
+  aggregates_refreshed?: string[] | null;
   chunk_index?: number; // J-34: completed chunks (== checkpoint resume point)
   chunk_total?: number; // J-34: total planned chunks (chunk x/N); 0/absent for a non-chunked job
   passers?: number; // J-35 expand: candidates that passed the screen (became universe members)
diff --git a/incredible_auto_dev/scripts/start-backend.sh b/incredible_auto_dev/scripts/start-backend.sh
index ff31d48..58fb00a 100755
--- a/incredible_auto_dev/scripts/start-backend.sh
+++ b/incredible_auto_dev/scripts/start-backend.sh
@@ -28,7 +28,45 @@ if [[ -d alembic ]]; then
   "$REPO_ROOT/apps/backend/.venv/bin/alembic" upgrade head 2>/dev/null || true
 fi
 
+# ops-hardening iter-2 (J-04 remainder) — actually ENFORCE the declared memory cap + malloc-arena cap and
+# write a PERSISTENT boot logfile. goal.md's binding note: prior to this iteration none of these three were
+# enforced by this script at all (confirmed by a direct read: no ulimit, no env export, no logfile redirect
+# anywhere in it) — do not trust reports/perf-budgets.md's or config.yaml's prose claiming otherwise; this
+# is where the enforcement actually lives now. Values come from config.yaml via the venv Python (No magic
+# numbers — the same `app.config.get_config()` every engine reads).
+read -r MEMORY_CAP_MB MALLOC_ARENA_MAX_VALUE <<< "$(
+  "$REPO_ROOT/apps/backend/.venv/bin/python" -c '
+from app.config import get_config
+cfg = get_config()
+print(cfg.server.memory_cap_mb, cfg.server.malloc_arena_max)
+'
+)"
+
+# ulimit -v is KiB; config.server.memory_cap_mb is MB. Set on THIS shell BEFORE exec — a ulimit is a
+# process attribute inherited across exec() (same PID, new program image), so the cap applies to the
+# uvicorn process itself, not just this launcher shell.
+ulimit -v $((MEMORY_CAP_MB * 1024))
+# iter-27 (anti-goal #8): bound how many independently-fragmenting malloc arenas glibc creates across the
+# uvicorn threadpool + parallel backfill workers (the dominant VSZ-fragmentation lever behind the
+# iter-26/iter-27 rebuild crash). Exported before exec so glibc reads it at the process's own startup.
+export MALLOC_ARENA_MAX="$MALLOC_ARENA_MAX_VALUE"
+
+# A PERSISTENT backend logfile (today uvicorn writes only to the launching terminal, lost the moment that
+# terminal closes or the process is backgrounded). One fixed, repo-relative path — `logs/` is already
+# gitignored — so a boot's log survives the launching shell and a crash test can read it afterward. Append
+# (not truncate) across restarts so a crash's abrupt ending stays visible in the SAME file the next boot's
+# lines are appended to (a real operational history, not a wiped-per-restart snapshot).
+LOG_DIR="$REPO_ROOT/logs"
+mkdir -p "$LOG_DIR"
+LOG_FILE="$LOG_DIR/backend.log"
+{
+  echo ""
+  echo "=== start-backend.sh: launching at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
+  echo "    port=$PORT memory_cap_mb=$MEMORY_CAP_MB malloc_arena_max=$MALLOC_ARENA_MAX_VALUE"
+} >> "$LOG_FILE"
+
 exec "$REPO_ROOT/apps/backend/.venv/bin/uvicorn" main:app \
   --host 0.0.0.0 \
   --port "$PORT" \
-  --app-dir "$REPO_ROOT/apps/backend"
+  --app-dir "$REPO_ROOT/apps/backend" \
+  >> "$LOG_FILE" 2>&1
diff --git a/apps/backend/tests/test_start_backend_script.py b/apps/backend/tests/test_start_backend_script.py
new file mode 100644
index 0000000..a9fc998
--- /dev/null
+++ b/apps/backend/tests/test_start_backend_script.py
@@ -0,0 +1,190 @@
+"""Script-level checks for `scripts/start-backend.sh` (ops-hardening iter-2, J-04 remainder): the memory
+cap / `MALLOC_ARENA_MAX` / persistent-logfile enforcement goal.md's binding note requires and this
+iteration adds — previously this script set NO ulimit, exported NO env var, and wrote NO logfile
+(confirmed by a direct read before this iteration). There is nothing to mock here: the assertions are
+about a REAL LAUNCHED PROCESS's actual resource limits / environment / logfile, so this spawns the real
+script as a subprocess against the real repo checkout, on an isolated test-only port so it never collides
+with an already-running dev/QA backend on this machine.
+
+TC-15 (RLIMIT_AS + MALLOC_ARENA_MAX), TC-16 (persistent logfile has boot events), TC-17 (a SIGKILL leaves
+the logfile ending abruptly, no clean-shutdown entry)."""
+from __future__ import annotations
+
+import hashlib
+import os
+import signal
+import subprocess
+import time
+from dataclasses import dataclass
+from pathlib import Path
+
+import httpx
+import pytest
+
+# apps/backend/tests/test_start_backend_script.py -> tests -> backend -> apps -> <repo root>
+REPO_ROOT = Path(__file__).resolve().parents[3]
+SCRIPT = REPO_ROOT / "scripts" / "start-backend.sh"
+LOG_FILE = REPO_ROOT / "logs" / "backend.log"
+
+# A deterministic-but-distinct port range (offset +10000 from the scripts' own 8000-8999 per-project
+# range) so this test never collides with an already-running dev/QA backend on this machine, while still
+# being reproducible across runs of the SAME checkout.
+_offset = int(hashlib.sha1(str(REPO_ROOT).encode()).hexdigest()[:4], 16) % 1000
+_TEST_PORT = 18000 + _offset
+
+
+def _read_proc_limits_max_address_space_bytes(pid: int) -> int:
+    """Parse `/proc/<pid>/limits`'s "Max address space" row -> the soft limit in bytes (RLIMIT_AS)."""
+    with open(f"/proc/{pid}/limits") as fh:
+        for line in fh:
+            if line.startswith("Max address space"):
+                parts = line.split()
+                # "Max address space         <soft>         <hard>         bytes"
+                return int(parts[3])
+    raise AssertionError(f"no 'Max address space' row in /proc/{pid}/limits")
+
+
+def _read_proc_environ(pid: int) -> dict[str, str]:
+    with open(f"/proc/{pid}/environ", "rb") as fh:
+        raw = fh.read()
+    env: dict[str, str] = {}
+    for entry in raw.split(b"\x00"):
+        if b"=" in entry:
+            k, _, v = entry.partition(b"=")
+            env[k.decode(errors="replace")] = v.decode(errors="replace")
+    return env
+
+
+def _wait_for_health(port: int, timeout: float) -> None:
+    deadline = time.monotonic() + timeout
+    last_exc: Exception | None = None
+    while time.monotonic() < deadline:
+        try:
+            resp = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1.0)
+            if resp.status_code == 200:
+                return
+        except Exception as exc:  # noqa: BLE001 — keep polling until the deadline
+            last_exc = exc
+        time.sleep(0.25)
+    raise AssertionError(f"backend on :{port} did not become healthy within {timeout}s (last error: {last_exc})")
+
+
+def _pid_alive(pid: int) -> bool:
+    """True iff `pid` (a DIRECT child of this pytest process, spawned via `subprocess.Popen` in the
+    `spawned_backend` fixture) is still actually running. `os.kill(pid, 0)` alone is NOT sufficient here:
+    once a child is killed but not yet reaped, it becomes a zombie — still present in the process table
+    (so `os.kill(pid, 0)` keeps succeeding) until something calls `waitpid` on it. `os.waitpid(pid,
+    os.WNOHANG)` both correctly distinguishes "still running" from "exited, zombie" and reaps it in the
+    same call, so a dead child is never mistaken for a live one on a later check."""
+    try:
+        reaped_pid, _status = os.waitpid(pid, os.WNOHANG)
+    except ChildProcessError:
+        return False  # already reaped (e.g., by Popen.wait() elsewhere) — definitely gone
+    if reaped_pid == 0:
+        return True  # still running (WNOHANG returns (0, 0) immediately when not yet exited)
+    return False  # reaped just now — it had exited
+
+
+@dataclass
+class SpawnedBackend:
+    """`pid` is the launched uvicorn process (see the fixture docstring for why this equals the launching
+    shell's own pid). `log_offset_before` is `logs/backend.log`'s size (bytes) immediately BEFORE this
+    fixture spawned anything — since the logfile is PERSISTENT and APPEND-mode BY DESIGN (this same
+    iteration's own feature), it may already carry content from earlier boots/restarts in this same test
+    session (or a developer's own manual verification pass); a test that cares about what THIS spawn wrote
+    must slice from this offset, never blindly read "the tail of the whole file"."""
+
+    pid: int
+    log_offset_before: int
+
+
+@pytest.fixture()
+def spawned_backend():
+    """Start the REAL `scripts/start-backend.sh` as a subprocess on the isolated test port, yield its pid
+    (+ the pre-spawn logfile offset) once `/api/health` responds, and guarantee it is killed afterward
+    (even on assertion failure) — never leaks a live backend process."""
+    if not SCRIPT.exists():
+        pytest.skip(f"{SCRIPT} not found")
+    log_offset_before = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
+    env = dict(os.environ)
+    env["CHAIN_BACKEND_PORT"] = str(_TEST_PORT)
+    env["CHAIN_FRONTEND_PORT"] = str(_TEST_PORT + 1000)
+    proc = subprocess.Popen(
+        ["bash", str(SCRIPT)],
+        cwd=str(REPO_ROOT),
+        env=env,
+        stdout=subprocess.DEVNULL,
+        stderr=subprocess.DEVNULL,
+    )
+    try:
+        # the script's own `exec` replaces the launching shell with uvicorn (same pid, new program image),
+        # so `proc.pid` IS the uvicorn process once that exec has happened (well before health responds).
+        _wait_for_health(_TEST_PORT, timeout=60.0)
+        yield SpawnedBackend(pid=proc.pid, log_offset_before=log_offset_before)
+    finally:
+        if _pid_alive(proc.pid):
+            os.kill(proc.pid, signal.SIGKILL)
+            deadline = time.monotonic() + 10.0
+            while _pid_alive(proc.pid) and time.monotonic() < deadline:
+                time.sleep(0.1)
+        # `_pid_alive` reaps via its own `os.waitpid` (see its docstring) — it may have ALREADY reaped the
+        # child here (either just above, or earlier inside the test body itself, e.g. the simulated-crash
+        # test). `Popen` has no way to know that happened, so `proc.wait()` would raise `ChildProcessError`
+        # on an already-reaped child; that is the expected/harmless case here, not a real failure.
+        try:
+            proc.wait(timeout=10)
+        except ChildProcessError:
+            pass
+
+
+def test_start_backend_enforces_memory_cap_and_malloc_arena_max(spawned_backend):
+    """TC-15 — the launched process's RLIMIT_AS reflects `config.server.memory_cap_mb` (6144 MB) and
+    `MALLOC_ARENA_MAX` (2) is present in its environment."""
+    pid = spawned_backend.pid
+    from app.config import get_config
+
+    cfg = get_config()
+    soft_limit_bytes = _read_proc_limits_max_address_space_bytes(pid)
+    expected_bytes = cfg.server.memory_cap_mb * 1024 * 1024
+    assert soft_limit_bytes == expected_bytes, (
+        f"expected RLIMIT_AS soft limit {expected_bytes} bytes ({cfg.server.memory_cap_mb} MB), "
+        f"got {soft_limit_bytes} bytes"
+    )
+    env = _read_proc_environ(pid)
+    assert env.get("MALLOC_ARENA_MAX") == str(cfg.server.malloc_arena_max)
+
+
+def test_start_backend_writes_persistent_logfile_with_boot_events(spawned_backend):
+    """TC-16 — the documented persistent logfile (`logs/backend.log`, repo-relative) exists and contains
+    THIS spawn's boot sequence's log lines (sliced from `log_offset_before` — the file is persistent/
+    append-mode by design, so it may carry earlier boots' content too; this test only cares about what
+    THIS spawn wrote), surviving past the launching shell (unlike the pre-iteration behavior of writing
+    only to whatever terminal launched it)."""
+    assert LOG_FILE.exists(), f"expected a persistent logfile at {LOG_FILE}"
+    content = LOG_FILE.read_text(errors="replace")[spawned_backend.log_offset_before:]
+    assert "start-backend.sh: launching at" in content
+    # uvicorn's own startup lines land in the SAME redirected file (config load -> tables -> orphan sweep
+    # -> readiness-ready all happen inside this same launched process's stdout/stderr stream).
+    assert "Uvicorn running" in content or "Application startup complete" in content
+
+
+def test_start_backend_logfile_ends_abruptly_after_simulated_crash(spawned_backend):
+    """TC-17 — after a simulated crash (SIGKILL), the persistent logfile ends abruptly: no clean-shutdown
+    entry follows THIS spawn's boot lines (a killed process gets no chance to run any shutdown/cleanup
+    code, so uvicorn's normal graceful-shutdown log lines are absent). Sliced from `log_offset_before` —
+    the file is persistent/append-mode by design and may already carry an EARLIER, genuinely clean
+    shutdown from a prior boot in this same session; blindly tailing the whole file would wrongly attribute
+    that older content to THIS spawn's kill."""
+    pid = spawned_backend.pid
+    os.kill(pid, signal.SIGKILL)
+    deadline = time.monotonic() + 10.0
+    while _pid_alive(pid) and time.monotonic() < deadline:
+        time.sleep(0.1)
+    assert not _pid_alive(pid), "the simulated-crash process should be gone after SIGKILL"
+
+    content_after = LOG_FILE.read_text(errors="replace")[spawned_backend.log_offset_before:]
+    assert "start-backend.sh: launching at" in content_after  # this spawn's own boot IS in its own slice
+    for phrase in ("Shutting down", "Application shutdown complete", "Finished server process"):
+        assert phrase not in content_after, (
+            f"unexpected clean-shutdown phrase {phrase!r} after this spawn's own simulated SIGKILL"
+        )
```
