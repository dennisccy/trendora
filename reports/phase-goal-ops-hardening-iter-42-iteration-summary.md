# Iteration Summary — goal-ops-hardening-iter-42

**Verdict:** REGRESSION
**Iteration type:** goal-full
**Date:** 2026-07-31
**Iteration:** 42

## In plain words

**What you can do now:** Request a backfill for any date range and get an honest explanation when nothing new needs fetching, see a clear startup/crash status badge instead of a blank screen, browse pages that only load the data they need, view backtest results served instantly from storage, and see a live indicator whenever background work is running.

**What changed this time:** The team fixed the automated testing system so it actually checks the features currently being worked on instead of silently skipping them — and the very first time it ran, it caught two real problems: starting a single-day price backfill on the Data page can now hang forever showing nothing, and heavy background calculations can use up all the app's memory and make the Backtest and Data pages show "Backend unavailable." The team also tried to shrink the memory used by price-history loading behind the Data page, but a closer check found it actually used slightly more memory than before, not less.

**What's next:** Before any more building happens, the product owner needs to decide how to fit 30 years of price history inside the app's protective memory limit — raise the limit, use less history, or let the heavy calculation run in smaller pieces over more time — after which the team can fix the stuck backfill job and recheck everything.

## Headline

Target-journey verification lane closes the clean-pass-over-unverified-target gap

## Direction

**Signal:** regressing
**Why:** J-05 "Aggregates are precomputed at ingest, never on the fly" moved from `passing` (last confirmed iter-39) to `regressed` this iteration — a backfill job now accepts and then never starts its worker, stalling forever with zero progress. J-07 "Heavy aggregates never take the service down" moved from seven straight iterations of `partial` to a hard `failing`: a heavy background warm exhausted the 6GB memory cap, producing real HTTP 500s on `/api/health` and "Backend unavailable" on `/backtest`. This is the session's first REGRESSION in 42 iterations; the evaluator attributes the memory ceiling to a pre-existing condition (7,004 MemoryErrors logged across the prior 10 days) but the journey itself is now demonstrably broken.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-01, J-04, J-06 (iter-41, unknown → passing)
- Regressions in last 3 iters: J-05 (iter-42, passing at iter-39 → regressed)
- Anti-goal violations in last 3 iters: iter-41: 3 new (all minor — 2 open, 1 resolved-in-audit); iter-42: 3 new (all minor — 2 open, 1 resolved-in-audit); 0 critical in either iteration; iter-40's full delta data was outside the pre-trimmed log window
- Iters with no journey state change: 0 of 2 fully-visible iters (41, 42); iter-40's journey-delta table was not visible in the pre-trimmed log

**Latest evaluator reasoning:** "The tool fix this iteration was built to make worked, and the first thing it found is bad news. Until now, when the team picked a journey to work on, that journey stopped being checked. This iteration closed that hole. The moment the checks ran, two journeys came back broken — and one of them, J-05 'Aggregates are precomputed at ingest', was last checked as working three rounds ago."

## What was done

- Product changes: apps/backend/app/engine/prices.py, apps/backend/tests/test_bar_cache.py, incredible_auto_dev/agents/ui-test-designer/body.md, incredible_auto_dev/.claude/agents/ui-test-designer.md, incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py, incredible_auto_dev/scripts/automation/lib/replay-lane.sh, incredible_auto_dev/scripts/automation/browser-qa-phase.sh, incredible_auto_dev/scripts/automation/lib/common.sh, incredible_auto_dev/tests/automation/test-replay-lane.sh, incredible_auto_dev/tests/automation/test-frontend-restart-reprobe.sh, reports/perf-budgets.md
- Closed the target-journey verification gap: `ui-test-designer` now emits a test row for `Target journeys:` too, and `merge_ui_test_results.py` forces `BLOCKED` when a target journey has zero rows or an all-SKIP row.
- Fixed a frontend-restart race (B4) centrally in `ensure_services_running` so mid-run restarts get a bounded re-probe instead of the whole regression run going silently all-SKIP.
- Fifth attempt at bounding `_BarCache.prefill`'s memory footprint (symbol-filtered `WHERE IN` query) plus NULL-tolerance (B6); auditor found the claimed 2.5% VmPeak reduction is actually a measured +5.1% regression once the compensating lazy loads it forces are counted.
- Auditor found and fixed a newly-reachable `KeyError` race in the parallel backfill path that the prefill filter opened.
- Verified 0 of 2 target journeys pass browser QA: the repaired test lane immediately caught J-05 (stuck backfill, zero progress for ~10 min) and J-07 (memory-driven service outage, HTTP 500s) both FAIL.
- Recorded a new T2 finding: `bars_asof` reads are ~70-80x slower per call since last iteration's columnar storage change (measured this iteration, not fixed).

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest, never on the fly") regressed — a backfill job can be accepted and then never start, stalling forever with no progress or error.
- Journey J-07 ("Heavy aggregates never take the service down") failing — a heavy background warm exhausts the 6GB memory cap and takes `/api/health` and `/backtest` down for several minutes.
- Owner decision required (blocks everything else): raise the memory cap, use a shorter price history, or relax the goal's timing promise so heavy work can run in smaller pieces.
- A stuck backfill job needs to report its own "cannot start" failure instead of showing "running" forever.
- This iteration's `_BarCache.prefill` filter (now measured a net +5.1% memory regression, not the claimed 2.5% saving) needs a keep/undo/finish decision.
- All eight journeys need re-verification once the memory decision lands — the six that passed this round were photographed minutes before the crash, not proof the server stays healthy.
- The newly-found ~70-80x slower price-read path (from last iteration's storage change) is unaddressed.
- Carried owner-only items: the `GET /api/health` ≤0.1s budget (now a hard failure, not just slow) and whether `start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`.

## Next step

HALT — one owner decision blocks everything. The app is asked to hold 30 years of prices (~3.3M rows) inside a 6GB memory cap, and the heavy background calculation no longer fits: it runs out of room and takes the whole service down. No agent may raise the cap (goal.md names it a physical hardware protection after two real crashes). The owner must pick one of three: raise the cap if the machine can safely take it, shorten the price history so the work fits, or relax the goal so heavy work runs in smaller pieces over more time. Only after that: make a stuck job report its own failure instead of hanging silently, decide the fate of this round's prefill change (keep/undo/finish — undo is simplest), and re-run all eight journey checks against the settled build.

## Assumptions made

- iter-42 · goal-evaluator — Ambiguity: the six required-still-passing journeys have genuine dated evidence, but it was captured minutes before the same run's memory-driven outage; the agent's own rules require positive evidence but don't say whether evidence from before a same-run crash still certifies a journey. We chose: keep all six `passing`, with the caveat recorded verbatim in each journey's note — the evidence clears the positive-evidence bar and the outage was induced by a different journey's own warm, not these six journeys' paths. Reversible: yes
- iter-42 · goal-evaluator — Ambiguity: J-05's immediately-prior recorded status was `unknown` (not tested for 2 rounds), not `passing`, so decision-tree clause C.1 ("passing → failing") doesn't literally match; but the journey-history schema defines `regressed` as "was passing in a prior iteration, now failing," and J-05 passed at iter-39. We chose: score `regressed` and return REGRESSION — `unknown` was recorded as "not tested," never as "not broken," so the last known truth about J-05 was that it worked; treating an unverified gap as erasing a prior pass would let a regression launder itself by going unchecked. Reversible: yes
- iter-42 · goal-decomposer — Ambiguity: the prior evaluator's next-step item ("settle what 'no whole-table load' means") offered two dispositions (bound it, or amend goal.md's budget) without marking either as owner-only, after four prior attempts at this exact code each fell short. We chose: plan a fifth, narrower-scoped dev attempt (query-time symbol filtering, a genuinely different lever than the prior four) rather than escalate straight to a goal.md amendment, with an explicit honest-disposition fallback if it still falls short. Reversible: yes
- iter-41 · goal-evaluator — Ambiguity: J-04's replay script covers only 2 of its 6 goal-text steps, and this iteration changed the mechanism behind an uncovered step; unclear whether partial script coverage is enough to score `passing` when the uncovered code just changed. We chose: `passing`, with every uncovered step named explicitly in journey-history and eval.md, because the covered evidence is real/dated/live and the changed step only makes checkpoints more frequent (unit-proven, cannot make results staler). Reversible: yes
- iter-41 · goal-evaluator — Ambiguity: decision tree clause C.4 (2+ consecutive iterations failing) matches on this session's established reading, but this would be the sixth consecutive ESCALATE, and the methodology says to use it sparingly on what was otherwise the best iteration in six. We chose: ESCALATE again — five prior evaluators recorded the identical reading on the identical journey, and an independent trigger existed (the audit caught a CRITICAL that review and QA both missed, the fifth consecutive iteration where only the auditor caught the substantive defect). Reversible: yes
- iter-41 · goal-decomposer — Ambiguity: the prior evaluator's five ordered next-step items didn't say whether they were one iteration's scope or should split across several. We chose: bundle all five into one iteration, since only one item (the `_BarCache.prefill` bound) was risky product code and the rest were tooling/instrumentation — keeping the "one risky item per iteration" rule intact while avoiding stranding the risky change unverified for an extra iteration. Reversible: yes
- iter-40 · goal-evaluator — Ambiguity: this would be the fifth consecutive ESCALATE on the same journey-failure reading, versus the methodology's "use sparingly" guidance and an iteration that delivered its planned code target well. We chose: ESCALATE again for consistency with four prior evaluators' identical reading, and because an independent trigger existed (a DoD checkbox shipped entirely unexecuted and seven required journeys unverified, caught only by the auditor). Reversible: yes
- iter-40 · goal-evaluator — Ambiguity: whether a journey should keep `passing` on durability when the diff touches code on the path it asserts on, given goal.md doesn't say which of two readings wins. We chose: a code-path split — a journey keeps `passing` only when no diff hunk lies on the path producing what it asserts; otherwise it drops to `unknown` with zero fresh evidence discarded honestly rather than papered over, per the auditor's own stated risk that a stale `passing` row could carry an unverified journey into a GOAL_ACHIEVED attempt. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-42-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Click "Data" in the top navigation (or go directly to `http://localhost:3255/data`)
3. Type `2026-05-02` in "Start date" and `2026-05-29` in "End date", then click the "Start" button
4. Scroll down to "Run history" and find the row for the run you just started
5. Refresh the page (press F5)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-42.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-42-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-42-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-42-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-42-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-42-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-42-what-to-click.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-42-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-42-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-42-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-42-closure-verdict.md |
| Goal evaluation | REGRESSION | runs/goal-session-ops-hardening/iter-42/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
