# Iteration Summary — goal-ops-hardening-iter-55

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-10
**Iteration:** 55

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, and all five research tools. Start a backfill over any date range with no hidden size cap, and get an honest explanation when there's nothing new to fetch. See backtest results appear instantly from storage instead of waiting on a live recompute. See an honest "starting up" message while the app boots, and a "backend unavailable" message if it goes down. See the app openly disclose when it's still crunching numbers in the background.

**What changed this time:** The Data page's job-history "Refreshed: …" line will now correctly leave "forward aggregates" off the list when a heavy background job ran out of memory partway through, instead of wrongly claiming that work was finished — this fix is proven by a background test but hasn't yet been seen happening live, since no job actually ran out of memory during this round's own test job. Separately, this round tried to stop the app's status light from briefly going quiet during heavy jobs, and that attempt did not work — it happened slightly more often this time (11 times instead of 6, out of about 1,839 checks).

**What's next:** Next, fix an automated check that is about to start failing for a reason that has nothing to do with the app, stop the checking tool from erasing its own results, make the quality report reflect what the browser check actually found, and figure out why two screens (job history and the data-availability chart) have gotten slow as the stored data has grown.

## Headline

Job-history record no longer over-claims a computation's completion after a memory-limited abort

## Direction

**Signal:** holding
**Why:** The headline fix (honest completion-accounting for the forward-aggregates warm) shipped and was independently re-verified in the source, by unit test, and against a live run's DB row and logs — but it moved no journey's status. J-05 and J-07 stay `partial`, and the health-availability gap they're blocked on actually widened (6 → 11 connection-level non-answers); J-06 stays `partial`, deferred and unexercised this round. Shape has held at 5 passing / 3 partial / 0 failing for two consecutive rounds with no journey at `failing`, so this reads as holding rather than stalling or regressing.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-54: 6 new (all minor); iter-55: 8 new (all minor, 0 critical)
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** "The code change this round asked for was built and it works. The saved record of a data job no longer claims it finished work it did not finish... The second aim missed: the app still went silent to the health check 11 times during a heavy job, worse than the 6 last round, and the report says so plainly. Nothing broke: 5 journeys still pass, 3 are still part-way."

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/app/engine/forward_testing.py
- Fixed the `forward_aggregates_warmed` completeness gate so it only claims a refresh when every configured horizon actually completed, not just any one of them — closes the exact bug that let a memory-aborted job (run 351) claim a full refresh.
- Added intra-chunk scheduling yields to `compute_forward_aggregates`'s per-horizon loop to reduce health-check starvation during heavy compute; proven byte-identical for every horizon, but the live drill showed the availability metric got worse (11 vs. 6 non-answers), root-caused to a separate concurrent research computation contending for the same process.
- Fixed a race in the J-04 golden test script (it now waits for the readiness badge to settle before asserting its state, instead of asserting immediately after boot).
- Executed the J-05 and J-07 golden test scripts for the first time this session via the regression-replay lane (both passed on the developer's original run).
- Verified 5 required-still-passing journeys (J-01, J-03, J-04, J-08, J-09) pass deterministic replay; the two target journeys (J-05, J-07) have no surviving lane row after a later replay run overwrote the results file, so they were scored from primary DB/log evidence instead.

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest") stays `partial` — the health-check drops during the heavy compute persist (11/1,839 non-answers, up from 6).
- Journey J-07 ("Heavy aggregates never take the service down") stays `partial` — same non-answer issue, worse under concurrent load.
- Journey J-06 ("Pages load only what they need") stays `partial`, not re-verified this round — two screens (job history list, data-availability chart) now take 3–21 seconds because the stored data grew about fifteen times larger.
- Declared closure blocker: zero connection-level health non-answers during the forward-aggregates warm was not met, root-caused to cross-process contention with a concurrent research computation — an architectural decision (moving heavy compute to a separate process) that only the product owner can make.
- J-05's golden test script used its only safe test date this round and is guaranteed to fail on its next run unless the date is rotated first.
- The tool that records replay results overwrites its own file on a later run, which destroyed this round's own J-05/J-07 result rows; the quality report then cited those (already-deleted) rows as a PASS while the browser report's own headline read BLOCKED.
- One large test file (`test_forward_testing.py`, 93 tests) did not finish running within this round's time budget and needs a dedicated early re-run.
- No walkthrough video was recorded this round — the recording script itself has a bug.

## Next step

Run the next round at full depth. In order: (1) rotate J-05's golden test date before anything else runs — it used up its only safe date this round; (2) stop the replay tool from overwriting its own results, and re-run the J-05/J-07 checks so they're recorded properly; (3) make the quality report read the browser check's own verdict line first, instead of citing results that no longer exist — this is the fifth round this exact problem has recurred; (4) find out why the job-history and data-availability screens have gotten slow, since that's the one thing keeping J-06 from passing; (5) stop spending rounds on the health-check availability lever — five rounds of scheduling tweaks have shown it's exhausted, and closing it fully now needs the owner's decision on moving heavy compute to a separate process.

## Assumptions made

- iter-55 · goal-evaluator — Ambiguity: this round repeats the shape where the quality report says PASS over a browser report that says BLOCKED, but literally none of the "escalate" trigger conditions fire (no journey is `failing`, the review verdict is PASS_WITH_NOTES not FAIL, and this was a full — not a shortened — round). We chose: continue with a full-depth recommendation on the merits, not escalate. Reversible: yes
- iter-55 · goal-evaluator — Ambiguity: J-05 and J-07's result rows were destroyed by a later replay run and the browser report lists them as unverified, but strong direct evidence (database rows, matching screenshots, log timing) survives. We chose: score both from that direct evidence and keep them at their prior status (`partial`), rather than marking them unknown. Reversible: yes
- iter-55 · goal-decomposer — Ambiguity: whether last round's note about two slow screens (J-06) belonged in this round's scope alongside the memory-abort fix. We chose: treat only the memory-abort fix this round; explicitly defer the slow-screens issue as a separate, not-yet-investigated problem. Reversible: yes
- iter-55 · goal-decomposer — Ambiguity: whether "make the record say partial" meant adding a literal new status value, or reusing the existing "just leave it off the list" convention. We chose: reuse the existing convention — no new field or status value added. Reversible: yes
- iter-54 · goal-evaluator — Ambiguity: whether a saved job record that overstates how much work finished (still marked "ok", still listing an item as refreshed when it actually stopped partway) counts as fabricated data under the most serious rule violations. We chose: treat it as a minor issue, not a critical one. Reversible: yes
- iter-54 · goal-evaluator — Ambiguity: whether a browser check that only verifies the on-screen part of a journey's requirements should count that journey as fully passing. We chose: mark J-05/J-06/J-07 as partly-working, not fully passing, consistent with how prior rounds scored the same situation. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-55-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Look at the "Start a fetch / backfill job" panel — leave "Start date" and "End date" as their pre-filled values, confirm "Job kind" reads "Backfill snapshots"
3. Click the "Start" button
4. Watch the readiness pill (top-right header) and the banner just below it while the job runs, for the next several minutes — this is the iteration's own target and its known, disclosed miss
5. Once the job's status badge reaches a terminal, non-spinner label (e.g. "ok") — this can take several minutes for a job that runs a full forward-aggregate warm — read the "Refreshed: …" line just below it

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-55.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-55-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-55-review.md |
| Browser QA | BLOCKED | reports/phase-goal-ops-hardening-iter-55-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-55-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-55-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-55-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-55-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-55-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-55-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-55-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-55-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-55-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-55/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
