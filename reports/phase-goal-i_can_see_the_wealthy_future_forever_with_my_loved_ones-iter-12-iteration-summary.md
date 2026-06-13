# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-13
**Iteration:** 12

## In plain words

**What you can do now:** See today's market regime and top-ranked stocks on a dashboard with a full-history indexes chart spanning five major benchmarks. Open any stock for an explainable score breakdown with a regime-banded price chart. Step back to any past date with a single global switcher so every page reflects that exact stored snapshot. Sort the leaderboard by any column, search instantly by ticker or company name, filter by theme, and see each stock's theme memberships in the table. Browse every theme's complete member list and jump to any member's dated detail in a new tab. View the Sectors leaderboard with every ETF named, described, and expandable to show its exact universe members. Run walk-forward backtest evidence with return attribution and control groups. Explore factor effectiveness, multi-factor combinations, and setup/pattern event studies in the Research Lab. Click any sample count to open the exact observations in a new tab and sort or filter them without disturbing your lab view. Save stocks to a persistent watchlist. Grow the dataset by importing price data for new date ranges — jobs now show live per-symbol and per-date progress as they run, appear in Run History the moment they start, survive a process restart gracefully, and complete even if some dates encounter errors rather than aborting the whole job.

**What changed this time:** Behind the scenes, the import-job pipeline became significantly more reliable and honest. When a job finishes downloading data but then fails during the analysis step, it now remembers exactly where it stopped — so hitting "Resume" skips the download entirely and picks up at analysis, saving time and provider quota. A new "running" row appears in Run History the instant you start a job (not only when it finishes). While a job is active, a live activity line tells you exactly which stock or date is being processed right now, a heartbeat timestamp shows the progress was updated just seconds ago, and the symbols counter can no longer count past its own total. If one date in a multi-date batch fails, that date is logged honestly and the rest of the dates complete — the job does not abort and no fake snapshot is created. A bug found during testing (two database columns were not registered for automatic migration, causing a 500 error on the live database) was caught, fixed, and guarded with new regression tests so it cannot recur silently.

**What's next:** Next we will add a per-date availability heatmap to the Data Manager so you can see at a glance which dates already have data, and upgrade the as-of date picker to a calendar that highlights only the selectable snapshot dates.

## Headline

Jobs-pipeline hardened: stage-aware resume, instant Run History, honest live progress, sound parallel backfill (J-59/J-60/J-66/J-67 all passing)

## Direction

**Signal:** improving
**Why:** Four journeys (J-59, J-60, J-66, J-67) moved from failing to passing this iteration with no regressions and no anti-goal violations. The in-iteration QA-FAIL was a real deployment bug (missing additive-column registry entries) that was root-caused, fixed, re-tested, and migrated live within the same iteration. Three journeys remain (J-61, J-62, J-63), all unbuilt rather than regressed — the loop continues with a clear, tractable next target.

**Trend (last 5 iters):**
- Newly passing this iter: J-59, J-60, J-66, J-67
- Newly passing in last 5 iters total: J-55, J-56, J-57 (iter-9); J-64, J-65 (iter-10); J-58 (iter-11); J-59, J-60, J-66, J-67 (iter-12)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The jobs-pipeline cluster (J-59 stage-aware resume + covered-range skip, J-60 lifecycle record at start + interrupted boot sweep, J-66 honest fine-grained progress with the 318/159 distinct-symbol fix and the speedup derivation moved server-side, J-67 transaction-sound parallel backfill with per-date failure isolation) all landed on the existing `/data` home with no new page/route, and all four are now passing. The initial QA-FAIL was a real but narrow deployment bug — two new SQLModel columns were not registered in `db.py` `_ADDITIVE_COLUMNS`, 500ing the persistent live DB while fresh-DB unit tests stayed green — which was root-caused, fixed (registry entries + 2 regression tests + live DB migrated), and independently re-verified (`/api/data`=200, `/api/stocks`=200, health `ready`). This is not GOAL_ACHIEVED: J-61/J-62/J-63 remain deferred-failing, so the loop continues.

## What was done

- Implemented stage-aware checkpoint (`ImportCheckpoint.completed_stages_json`) so a Resume on a `failed_backfill` job skips the fetch stage entirely — zero provider calls, proven with an injected counting provider; covered ranges are also never re-fetched via `_plan_uncovered_chunks`
- Implemented job lifecycle record created at job start (`DataProviderRun` status `running`) with a single honest terminal transition; added boot sweep to mark orphaned `running` rows as `interrupted` on process restart
- Fixed the 318/159 symbol counter overflow by deduplicating symbols across date windows in the fetch counter; added `current_activity` line, `last_progress_at` heartbeat, and `JobLiveActivity` component to the `/data` job card
- Moved speedup computation server-side into `_compute_speedup` (clearing the iter-8 coherence-WARN residual); all progress/heartbeat/granularity knobs are config-backed in `config.yaml`
- Hardened parallel multi-date backfill with per-date failure isolation: a single bad date is rolled back, recorded in `date_failures`, and remaining dates continue — job ends `partial`, never aborts the whole stage, no fabricated snapshot
- Added 14 new jobs-pipeline offline tests and updated 10 parallel-backfill tests including byte-identity and per-date isolation assertions; 759 passed / 4 skipped / 0 failed on the v1 full suite
- Caught and fixed in-iteration: missing `_ADDITIVE_COLUMNS` entries for the two new model columns, which caused HTTP 500 on the live persistent DB; added 2 regression tests to `test_db.py` and migrated the live database
- Verified 10/15 browser-QA test cases pass (5 skipped for missing prerequisite data, none failed); live `/api/data` 200, `/api/stocks` 200, health `ready`

## What's left

- Journey J-61 (Per-date availability heatmap) failing — not yet built; new read-only descriptive endpoint + heatmap surface on `/data`
- Journey J-62 (As-of switcher becomes a calendar showing selectable dates) failing — not yet built; presentation upgrade of the single global as-of state
- Journey J-63 (Event study overlap-honest first-trigger episodes by default) failing — not yet built; backend research-module change
- Journey J-22 (Transparent rule-based expanded universe ~500 names) blocked-NA — data-walled (market-cap reference endpoint returns HTTP 401); non-vetoing per goal.md
- Journey J-23 (Multi-timeframe bars — intraday seed + pipeline) blocked-NA — no buildable intraday fetch path; non-vetoing per goal.md
- Journey J-24 (Timeframe selector on the stock chart) blocked-NA — depends on J-23; non-vetoing per goal.md

## Next step

Continue. Target the **J-61 / J-62** Data-Manager-availability + as-of-calendar cluster next:
- **J-61** — per-trading-date availability heatmap on `/data` (a new read-only descriptive endpoint deriving symbols-with-bars + snapshot-exists per date from stored bars + stored runs; honest partial-coverage rendering; click prefills the job form as a job parameter, never the global as-of).
- **J-62** — the global as-of switcher becomes a calendar popover marking exactly the selectable snapshot dates — a presentation upgrade of the **same single global as-of state** (must hold no second date state; J-13/J-18/J-43/J-50 semantics byte-unchanged; ISO `yyyy-MM-dd` via the shared formatter).

Run it **full**: J-61 introduces a new read-only endpoint + two new surfaces and J-62 touches the single-source as-of control (the no-second-date-state invariant and the ux-regression/closure gates matter). J-63 (event-study episode mode) follows after. J-22/J-23/J-24 stay blocked-NA (non-vetoing).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-what-to-click.md`:

1. Open `http://localhost:3835/data` in your browser — expect the Data Manager page loads with "Unfinished Imports" and "Run History" sections, no red error banners
2. Start a new import job: select any symbol and a short date range (1–2 months), then click the submit/start button — expect a live job card appears and a new "running" row with spinner appears in Run History before the job finishes
3. Watch the live job card for 10 seconds while the job runs — expect a current-activity line reading something like "scanning 2024-06-01 (3/12)" that changes as the job progresses, plus a heartbeat line reading "updated 1s ago" that increments
4. While watching, check the symbols counter — expect the left number never exceeds the right number (e.g. "3/3" is fine; "4/3" would be a bug)
5. After the job finishes, scroll to "Run History" — expect any "partial" job shows a failure detail block listing which specific dates failed and their error messages, with a note that remaining dates completed

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-ui-test-results.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-what-to-click.md |
| QA | FAIL | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-12/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
