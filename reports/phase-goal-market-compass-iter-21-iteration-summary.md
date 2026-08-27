# Iteration Summary — goal-market-compass-iter-21
**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-27
**Iteration:** 21

## In plain words

**What you can do now:** See each stock's honest sector label on the newest rankings, see why each next-session candidate stock was picked (and why others weren't), and browse the two trading days recovered from the August data incident — with their volume numbers corrected — in the price history.

**What changed this time:** Behind the scenes, step three of a four-step data repair ran, clearing out five old stores of stale numbers left over from before the repair began — 1,643 outdated rows gone. Once the app switches back on, the Data page's "Per-date availability" card will no longer quietly show old, pre-incident numbers as current — it will honestly say there's nothing there yet and rebuild itself fresh. Two other old number-stores were checked and deliberately kept, because they're still safe and clearing them would have slowed one page down.

**What's next:** Next comes the fourth and final repair step — a full check that decides whether the incident is truly fixed — while the app and browser testing stay switched off until it passes.

## Headline

J-11 Stage F executed: 1,643 stale cache rows deleted across 5 of 7 tables

## Direction

**Signal:** holding
**Why:** J-11 advanced from Stage E to Stage F this iteration — the third clean, fully live-verified repair step in a row (Stages D, E, F across iterations 19-21), with zero regressions and zero new anti-goal violations — but no journey crossed into `passing`, so J-11 ("Incident-bounded clean regeneration of derived state") stays `partial`. J-07 ("The Today page answers the ten-second read") and J-08 ("Market page moves over intact and history stays honest") remain `failing`, but both are deliberately blocked behind the loop-mechanics gate until Stage G passes, not newly broken or newly worked this iteration. Direction reads as holding: steady, independently-verified forward motion on the one authorized repair track, not yet enough to flip a journey's status.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none (ledger holds steady at 7 total, 0 unresolved, across iterations 19-21)
- Iters with no journey state change: 0 of last 3 (J-11 advanced within `partial` — Stage D, then Stage E, then Stage F — in each of the last 3 iterations)

**Latest evaluator reasoning:** The one job the owner's written plan allowed was done, and it worked. This step cleared out old saved answers that the app had kept from before the accident, so that when the app is finally switched back on it cannot show pre-accident figures as if they were current. I did not take that from anyone's write-up: I opened the 8.4 GB database read-only and re-measured everything myself.

## What was done

- Product changes: apps/backend/app/engine/j11_stage_f_execute.py, apps/backend/scripts/run_j11_stage_f_execute.py, apps/backend/tests/test_j11_stage_f_execute.py, apps/backend/tests/test_j11_stage_f_execute_cli_script.py
- Executed J-11 Stage F live: classified all 7 dependency-aware derived-cache tables and deleted 1,643 stale rows across 5 (event_study_cache, market_phase_cache, forward_aggregate_cache, availability_cache, coverage_snapshot); 2 tables (index_series_cache, membership_timeline_cache) proven safe and deliberately preserved.
- Fixed the availability_cache correctness risk found during planning: deleting its stale row stops the app from silently serving pre-repair coverage data labeled "current" the first time `/data` loads after reboot.
- Proved live, before deciding, that preserving membership_timeline_cache's stale row is safe — the cheap "historical gap-insert" repair path will run on the next real request, not the >300s cold-compute sweep that once hung the page.
- Ran 76 fixture-scoped tests (never against the live database); reviewer PASS (zero issues), QA PASS, auditor PASS_WITH_GAPS (one IMPORTANT finding — a false Definition-of-Done checkbox — corrected in-audit).
- Re-verified live database state read-only before and after the write: only the 5 authorized tables changed; all other tables (prices, scanner runs, forward returns, manifests, maintenance boundary) identical to iteration 20's recorded state.
- Browser QA and application boot stayed off all iteration under maintenance isolation (0 journeys re-verified via browser this round); J-11's progress was instead verified through live, read-only database checks by three independent lanes.
- Committed and pushed iteration 21's 4 new backend files and evidence folder as commit `5768c930`, closing the "untracked at scoring" pattern flagged in iterations 19 and 20.

## What's left

- Journey J-07 ("The Today page answers the ten-second read") — failing, blocked until Stage G passes.
- Journey J-08 ("Market page moves over intact and history stays honest") — failing, blocked until Stage G passes.
- Stage G, the final repair check, has not run yet — it is the only step allowed to declare the August data incident repaired.
- Until Stage G passes, normal Market Compass work (journeys J-01 through J-09) stays blocked and the maintenance boundary stays active; the app and browser testing remain switched off.
- Two framework defects remain open by owner instruction until after Stage G: the ordinary-request-path / Data-Manager write-path guard gaps, and a duplicate-journey-heading defect in the goal-tracking tool.

## Next step

Do the last step of the repair — Stage G, the final acceptance check. No further owner approval is needed: the 2026-08-26 ruling already authorizes it once Stage F succeeded, and it did. Keep the app and browser testing off until Stage G passes — this iteration's evaluator found a new, previously unrecorded risk: once the app reboots, an ordinary page request against a quarantined day would silently rewrite the coverage cache Stage F just cleared, and would also discard the membership-timeline row Stage F deliberately preserved. Stage G's design must re-prove that preserved row's safety immediately before boot (today's proof is a snapshot, not a standing guarantee), let background cache warm-up finish before any request lands (the host froze once before from memory pressure), and treat the goal text's claim that undamaged days carry forward-return gaps as false for this codebase. This iteration's four new backend files and evidence folder are now committed and pushed (`5768c930`), closing the tracking gap flagged at the last two iterations' scoring time.

## Assumptions made

- iter-21 · goal-decomposer — Ambiguity: the owner's ruling authorizes the full Stage D→E→F→G sequence in one instruction and authorizes Stage F unconditionally once Stage E succeeds, but nothing requires delivering the whole sequence inside one iteration. We chose: scope iteration 21 to Stage F alone — re-verify Stage D/E's frozen state, classify and invalidate the seven caches, then stop — leaving Stage G to a later iteration, continuing the same one-stage-per-iteration discipline iterations 19 and 20 already established. Reversible: yes.
- iter-21 · goal-decomposer — Ambiguity: docs/goal.md step 6 requires classifying each of seven caches into one of three dispositions but does not assign a specific disposition to any specific cache, nor say how to resolve a same-count/same-ID stamp collision. We chose: use each cache row's `created_at` compared against Stage D's frozen execution-start instant as the decisive classification signal (corroborated by, not replacing, the dataset-version stamp comparison); default five caches to explicit deletion (required outright for `availability_cache`, a live risk found this planning pass); preserve `index_series_cache` untouched; give `membership_timeline_cache` a conditional preserve contingent on a live safety proof, falling back to deletion if that proof failed. Reversible: yes.
- iter-21 · goal-evaluator — Ambiguity: AG-10 requires heavy compute be launched only via the project's capped launch scripts; Stage F's cache deletions make an existing in-process compute path heavier and more likely to run cold on the next request, and the goal text doesn't say whether that counts as "launching heavy compute" on a host with a documented freeze history. We chose: score this as an operational risk and a binding Stage-G design input, not an anti-goal violation — the future compute still runs inside the normal capped backend process with no cap removed or bypassed, and the app stays off so no request can land before Stage G designs the boot sequence. Reversible: yes.
- iter-20 · goal-decomposer — Ambiguity: the owner's ruling authorizes the full Stage D→G sequence in one instruction and authorizes Stage E unconditionally once Stage D succeeds, but nothing requires delivering it in one iteration. We chose: scope iteration 20 to Stage E alone, leaving Stage F and Stage G to later iterations, continuing the same per-stage discipline already established for Stage D. Reversible: yes.
- iter-20 · goal-decomposer — Ambiguity: docs/goal.md names two existing functions side by side for Stage E's forward-return backfill without stating which one to call, or whether the choice matters. We chose: require the per-run `backfill_run_forward_returns` loop over every existing scanner run, and forbid the whole-database `backfill_forward_returns()` entry point, because reading that whole-DB function's body shows it could mint a scanner run outside the 11-date incident boundary as a side effect. Reversible: yes.
- iter-20 · goal-evaluator — Ambiguity: the owner's ruling voids the attempt on any "failure, refusal or unmet gate," and the developer's first attempt to run the Stage E CLI was refused by the coding tool's own permission classifier before the process started — the ruling doesn't say whether a tooling-permission denial counts as that "refusal." We chose: read "refusal" as a refusal by the recovery machinery itself, not a harness-level permission denial — the denial produced zero database side effects, and the owner then ran the identical command themselves and it completed cleanly. Reversible: yes.
- iter-20 · goal-evaluator — Ambiguity: docs/goal.md step 5 asserts forward-return holes exist on retained (non-rebuilt) runs, but Stage E inserted zero rows on all 3,117 retained runs, and the goal text doesn't say what a zero count means. We chose: score that population as correctly zero, not an unmet requirement, based on re-deriving the deletion-cascade code directly and confirming it live — but carried this forward as a binding design input for Stage G's acceptance check. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-21-what-to-click.md`:

1. Open `docs/handoffs/goal-market-compass-iter-21-dev.md` and find the status block near the top.
2. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-execution-result.json` and find `total_rows_deleted` and the `per_table` object.
3. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-verification-result.json` and find `ok` and each table's `post_count`.
4. Run the read-only query: `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT (SELECT COUNT(*) FROM event_study_cache), (SELECT COUNT(*) FROM market_phase_cache), (SELECT COUNT(*) FROM forward_aggregate_cache), (SELECT COUNT(*) FROM coverage_snapshot), (SELECT COUNT(*) FROM availability_cache), (SELECT COUNT(*) FROM index_series_cache), (SELECT COUNT(*) FROM membership_timeline_cache), (SELECT COUNT(*) FROM scanner_runs), (SELECT COUNT(*) FROM forward_returns);"`
5. Open `runs/goal-market-compass-iter-21/j11-stage-f-execute-mutation-accounting.json` and find `table_sweep_diff.changed_existing_tables`.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-21.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-21-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-21-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-21-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-21-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-21-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-21-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-21-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-21-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-21-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-21-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-21-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-21/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
