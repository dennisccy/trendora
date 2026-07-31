# Iteration Summary — goal-ops-hardening-iter-40

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-07-31
**Iteration:** 40

## In plain words

**What you can do now:** Request a very large historical backfill without hitting an artificial length limit. View backtest results that always come from stored data, never a slow live recalculation. See a live indicator whenever the system is doing background work. Four other things that worked last round — backfilling with an honest zero-work explanation, a truthful startup/crash status badge, calculations done ahead of time, and an honest "still working" message on research pages — should still work, but were not re-checked this round, so we're holding off on re-promising them until they are.

**What changed this time:** Behind the scenes, the team fixed a spot in the Data page's supporting calculations that used to pull millions of price rows into memory all at once — it now reads them in small batches, so it can no longer freeze the app during heavy work. They also made the Data page's crash-recovery progress count far more accurate after a hard restart (off by one day now, instead of off by a factor of ten). Nothing changed on any screen. But this round's automatic re-check of seven already-working features looked at the wrong web address and wrongly reported "can't test — app is down," even though the app was answering normally — so those features need a fresh check before we promise them again.

**What's next:** Next, we'll fix that testing check so it looks at the right address and actually re-verifies everything, then track down exactly what froze the server during the toughest version of the memory-stress test.

## Headline

No new user-facing capability — bounded a memory-unsafe query and fixed crash-recovery honesty (J-07/J-04)

## Direction

**Signal:** holding
**Why:** J-07 "Heavy aggregates never take the service down" stayed `partial` for a sixth consecutive iteration, though its last acceptance clause is now genuinely closed (the unbounded diagnostic query is fixed and independently measured by the auditor) and a post-fix wedge-recurrence drill showed no freeze. No journey regressed, but four required-still-passing journeys (J-01, J-04, J-05, J-06) dropped from `passing` to `unknown` because the browser-QA lane skipped all seven required journeys entirely — its precondition probed the wrong health-check URL against a backend that was actually up — and only the auditor caught that DoD gap, the fourth consecutive iteration where only the auditor caught a substantive defect. The evaluator ESCALATEd for a fifth consecutive time.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 5 new (iter-39: 4, iter-40: 1), all minor, 0 critical
- Iters with no journey state change: 1 of last 2 (iter-39 had none; iter-40 downgraded four journeys to unknown)

**Latest evaluator reasoning:** "The one code change this iteration promised was delivered well. The `/data` coverage screen used to load every price row for every stock into memory at once before it started working; it now reads them in small batches, and I checked myself that the answer it produces is exactly the same as before. But this iteration also shipped with a hole that no one but the auditor noticed: seven journeys that the plan required to be re-checked were not checked at all."

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/tests/test_data_manager.py, incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py, reports/perf-budgets.md
- Streamed `_missing_data_diagnostic`'s second query via `.yield_per` instead of materializing ~3.3M rows in memory at once — proven byte-identical output (TC-1); closes J-07's last standing acceptance clause.
- Corrected the in-code comment at `data_manager.py:262-274` that previously claimed no unbounded whole-table scan existed.
- Tightened the `/data` Run History checkpoint-write interval 10.0s → 1.0s so crash recovery reports a much closer date count (live `kill -9` drill: 1-date gap vs. the prior iteration's order-of-magnitude gap).
- Re-ran the tightened-cap wedge-recurrence drill once post-fix: the wedge did not recur (28/28 health polls HTTP 200, VmPeak pinned at the declared 2650 MB cap).
- Corrected `reports/perf-budgets.md`'s retracted `backfill_workers` wedge attribution in place.
- Taught `merge_ui_test_results.py` a `BLOCKED` verdict class (`FAIL > BLOCKED > PASS > SKIP` priority) so a merged run can no longer headline PASS/SKIPPED when every surviving row is BLOCKED.
- 247 automated tests passed (142 backend + 26 regression + 14 merge-tool self-tests + 65 replay-lane integration); an audit-added regression pin now catches a revert of the checkpoint constant.
- Verified 0 target journeys pass browser QA — the browser-QA lane SKIPPED all 8 rows because its precondition probed `/health` instead of `/api/health` against a backend that was actually answering.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) still `partial` — sixth consecutive iteration; a process wedge at the 2650 MB test cap remains reachable and its frozen thread is still unidentified.
- Seven required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) got zero fresh verification this iteration; four of them (J-01, J-04, J-05, J-06) were downgraded to `unknown` as a result and need a fresh browser check before any achievement attempt.
- `apps/backend/app/engine/prices.py:132-142` still builds every `daily_prices` row into one in-memory dictionary — the last unbounded whole-table load the project's own success criteria forbid.
- Checkpoint honesty is still time-based, not count-based — an extremely fast future job could still show more than a 1-date gap.
- Owner decision: the `GET /api/health` ≤0.1s budget missed a seventh time (0 of 28 polls this iteration).
- Owner decision: whether `start-frontend.sh` should join the host-guard marker file list.
- J-07's `[NEW]` demo walkthrough remains unrecorded for a tenth iteration.
- Deferred a fifth time: Regime Lab's cold `view=pooled` background dispatch (iter-33/g).

## Next step

Run the next iteration at full depth (mandatory via ESCALATE). Verification coverage comes first this time, ahead of J-07: fix the browser-QA precondition to probe `/api/health` instead of `/health`, and stop `Frontend Present: no` from suppressing the required-still-passing regression replay, so all seven journeys get a fresh screenshot before any achievement attempt. Then identify the thread that froze the server in wedge-drill run 1 using Python's built-in `faulthandler` stack dump rather than tuning the memory cap again; bound `prices.py`'s remaining unbounded whole-table accumulator; and keep the drill's health monitor polling past terminal job status, since the earlier wedge appeared just after the job reported done. Small, already-written-down items: give the checkpoint cadence a count-based floor alongside the time-based one, and add `BLOCKED` to the framework's own verdict vocabulary so it stops disagreeing across files. Two owner decisions remain open and should be settled before any GOAL_ACHIEVED attempt: the `GET /api/health` ≤0.1s budget disposition (now missed seven times) and whether `start-frontend.sh` should join the host-guard marker list.

## Assumptions made

- iter-40 · goal-evaluator — Ambiguity: decision tree C.4 matches for a fifth consecutive ESCALATE on J-07 even though this iteration delivered its mandated code target well. We chose: ESCALATE again — first-match-wins precedent across the session, ESCALATE only makes full depth mandatory rather than advisory, and an iteration-specific trigger (a DoD checkbox left entirely unexecuted, seven required journeys unverified, caught only by the auditor) is the strongest of the session. Reversible: yes
- iter-40 · goal-evaluator — Ambiguity: whether the seven required-still-passing journeys, zero-verified this iteration, should stay `passing` on durability or drop to `unknown`, given the diff's behaviour-neutrality is unusually well proven. We chose: a code-path split — a journey keeps `passing` only when no diff hunk lies on the path producing what it asserts (J-03/J-08/J-09); the other four (J-01/J-04/J-05/J-06) drop to `unknown` since zero fresh evidence plus a touched path forbids `passing` under the no-screenshot rule. Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: whether decision tree C.4 should trigger a fourth consecutive ESCALATE even though this iteration delivered its mandated target well. We chose: ESCALATE again — first-match-wins precedent, plus an independent trigger (the audit lane caught a critical MemoryError-isolation gap review and QA both passed). Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: whether J-07's "no unbounded whole-table ORM materialization" acceptance clause is scoped only to the two named tables (forward_returns/scanner_results) or governed by the broader headline sentence, given the newly-found site is on `daily_prices`. We chose: the broad reading — the clause is not satisfied — following this session's own iter-37 precedent and goal.md's Success Criteria, which name `daily_prices` explicitly. Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: whether J-04 should stay `passing` when the deterministic replay FAILed only because the backend was down and the browser lane declined to restart it (no lane supplied fresh live verification). We chose: kept J-04 `passing` on evidence durability but deliberately did not advance its `last_verified_iter`, and named every uncovered step. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: whether to ESCALATE a third consecutive time on the same J-07 blocker even though the iteration was already run at full depth with review/QA/audit/closure all passing. We chose: ESCALATE again — the review and QA lanes had both passed a real AG-8 regression and an unmeasured-claim gap that only the audit lane caught. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: whether J-07 should cross to `passing` when its steps 1 and 4 were demonstrated through a different trigger path than the journey's own acceptance text names, and whether it may pass while the iteration's own newly-created state was never measured. We chose: kept J-07 `partial` for a third consecutive iteration — the acceptance text's own words require this-iteration evidence, not inference. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-40.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-40-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-40-review.md |
| Browser QA | SKIPPED | reports/phase-goal-ops-hardening-iter-40-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-40-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-40-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-40-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-40-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-40-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-40-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-40-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-40-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-40-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-40/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
