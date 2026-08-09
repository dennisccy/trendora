# Iteration Summary — goal-ops-hardening-iter-54

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-09
**Iteration:** 54

## In plain words

**What you can do now:** Request a backfill over any date range with no hidden size limit and get an honest explanation of what actually needed fetching. See a live "starting up" status while the app boots and a "backend unavailable" message if it goes down, with any interrupted job clearly marked once it's back. View backtest results instantly, served from storage rather than recomputed on the spot. See a live indicator whenever the app is crunching numbers in the background.

**What changed this time:** Behind the scenes, the team fixed a subtle one-day gap in the market-risk calculation that could occasionally show the wrong risk label, sped up the slow read behind the market-phase history page, and closed the very last moment where the app's health signal went silent during its coverage-checking background step (zero silent moments now, across a large live test, down from one).

**What's next:** Next, the team will make the app's heaviest background step honest when it runs out of memory partway through a job — right now it can quietly skip part of its work while still marking the job "done" — and then close the handful of remaining moments where the health signal goes quiet during that same heaviest step.

## Headline

The four code repairs this round asked for were all made, and I checked each one in the source myself.

## Direction

**Signal:** holding
**Why:** Journey shape held at 5 passing / 3 partial / 0 failing — nothing moved either direction, so the mechanical journey-count test reads holding, not regressing or improving. J-05, J-06 and J-07 stay partial on the same core defect (the health check going silent or slow during the app's heaviest background step). The ESCALATE verdict is a process-integrity call, not a journey-count call: this round ran at "lean" depth against its own spec's "full", so the audit and QA lanes never ran, and the evaluator's own digging (not any lane report) found a heavy step that aborted under real memory pressure mid-job while its saved record still claims the work finished.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: J-04 (iter-53)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-53 opened 7 new (0 critical), iter-54 opened 6 new (0 critical) — 13 total, none critical
- Iters with no journey state change: 1 of last 2 (iter-54)

**Latest evaluator reasoning:** "The four code repairs this round asked for were all made, and I checked each one in the source myself. But no journey changed status. The two journeys that turn on 'the app keeps answering while a data job runs' still fail that step: the developer's own one-per-second test recorded 6 moments where the health check got no answer at all and 53 more that took over 2 seconds. And I found something no report mentions — during the very job the checks used to mark three journeys green, the heavy aggregate step ran out of memory and stopped early (one of the five time horizons was never computed), yet the saved record still says that work finished and the job reads 'ok'."

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/app/engine/market_phase.py, apps/backend/app/engine/universe_resolver.py
- Fixed the market-phase off-by-one (B1): the bounded window fetch now pulls one extra bar so it is a provable superset of the calendar filter it feeds; a new test compares the fixed code against an untreated oracle, not against another copy of itself.
- Fixed the retrospective page's unbounded per-request read (B3): `_benchmark_close_on_or_before` now uses the fast `close_on` helper instead of a full-history scan.
- Closed the session's last `/api/health` connection-level non-answer in the coverage-checking finalize step: zero non-answers across a 1,822-poll live drill, down from one at iter-53.
- Relocated the memory-fault-injection test probe (B2) to the finalize-tail phase it is actually named after, so a live fault drill can isolate that phase specifically.
- Restored a deleted regression-test assertion (T2) and ran the full 76-test `test_market_phase.py` suite clean, zero failures (T5).
- Authored new deterministic golden check scripts for J-04 and J-07.
- Browser QA lane recorded PASS for all 3 target journeys (J-05, J-06, J-07); the evaluator independently scored all three `partial` — see What's left.

## What's left

- Journey J-05 (Aggregates are precomputed at ingest) — partial: the health check went silent 6 times and answered slowly 53 times during a live backfill drill.
- Journey J-06 (Pages load only what they need) — partial: two API endpoints (job history, data availability) now take 5-21 seconds, well over budget, because the stored database has grown roughly 15x.
- Journey J-07 (Heavy aggregates never take the service down) — partial: the same health-check silence lands inside the app's heaviest background step.
- The heaviest background step ran out of memory mid-job and skipped one of its five time horizons, but the saved run record still claims the work finished ("status: ok").
- This iteration was dispatched at "lean" depth even though its own plan called for "full" — so no audit and no QA report ran this round.
- The live fault-injection drill for the relocated memory-fault probe was not run this dispatch — only proven by an in-process unit test.
- J-05's existing check script was not executed this dispatch — the second consecutive round it was skipped.
- The finalize-tail wall-clock budget is still over target (about 1,821s vs. a 1,200s goal), an expected consequence of deliberately deferring two other heavy background steps this round.

## Next step

Run the next round at **full depth** (this is now required, not a suggestion). Work in this order.

1. **Fix the heavy step that runs out of memory, and stop the record from claiming work it did not finish.** During a normal data job the app's heaviest calculation ran out of memory part way through and skipped the last of its five time settings — but the saved job record still says that work was done, and the job is marked "ok". First make the record honest (say "partial", and list only what really finished). Then apply to that step the same bounded, take-a-breath treatment that already worked twice on other steps.
2. **Close the last six moments where the app went silent.** All six fall inside that same heavy step, and none in the step this round fixed — so this is one job, not many.
3. **Find out why two screens' data calls now take 5 to 21 seconds.** The job-history list and the data-availability chart got very slow because the stored data has grown about fifteen times larger. Nothing about this round caused it, but it is what keeps J-06 "Pages load only what they need" from passing.
4. **Actually run the three saved check scripts that exist and were not run** — J-05's has now been skipped twice, and the two written this round (J-04, J-07) have never been replayed. Also make the J-04 script wait for the app to finish starting before it checks, so it stops failing for a reason that is really the app behaving correctly.
5. **Run the round at the depth its own plan asks for.** This round's plan said "deep" and the engine ran "shallow", so the audit stage never happened — and the audit is the stage that has caught the real story six rounds in a row. This round proves the point: nobody reported the memory failure above.
6. Small and already written down: the ~20-minute limit on a job's finishing work is still missed (30 minutes measured); the health check still does real database work on every call; the live fault drill for the relocated test switch is still owed.
7. Carried, untouched: iter-29/b + the badge wording after a permanently failed warm-up (27th round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. Deferred a twentieth time: iter-33/g, the Regime Lab — whose data ran out of memory again this round.
8. Capture only, never a round's goal: one screenshot came back completely blank (`J-05-job-running.png`); no walkthrough recording was made at all this round because the shallow setting skips that stage; J-07's is 24 rounds unrecorded.
9. Owner: two decisions, still unanswered since rounds 50 and 51 — (a) may a future round move the heavy calculation into a separate process? That is still the only way to guarantee the app never pauses. (b) Does the 20-minute limit on a job's finishing work apply while the app is also serving people, or only when it is idle? And three facts worth knowing: the market-phase window bug is fixed and now proven against the old slow version rather than against itself; the step this round targeted went from one silent moment to none; and the app survived running out of memory for real, mid-job, without needing a restart.

## Assumptions made

- iter-54 · goal-evaluator (second entry) — Ambiguity: run 351's forward-aggregate warm aborted at horizon 20 under real memory pressure while the persisted record still shows `status='ok'` and lists `forward_aggregates` as refreshed; unclear whether an overstated completeness/status field counts as "fabricated data" under the critical-severity anti-goal rules. We chose: severity minor, not critical, so the verdict is ESCALATE rather than REGRESSION — no served market number is wrong, only a completeness/status field. Reversible: yes.
- iter-54 · goal-evaluator — Ambiguity: the merged browser-lane report records PASS with an "8/8 journeys passed" headline for all three target journeys (J-05, J-06, J-07), but each row verifies only the browser-visible subset of that journey's full acceptance steps. We chose: score all three `partial`, not `passing`, consistent with the same shape scored `partial` at iters 51-53. Reversible: yes.
- iter-54 · goal-decomposer — Ambiguity: the iter-53 audit bundled three finalize-tail phases together in one next-step instruction, with no guidance on whether all three belong in one iteration. We chose: treat only the coverage-checking phase this iteration; explicitly defer the other two (lower-priority, unprofiled, and bundling them risks repeating this session's overreach pattern). Reversible: yes.
- iter-53 · goal-evaluator (second entry) — Ambiguity: this round showed a fail-open shape (QA reported PASS while the browser lane reported BLOCKED), but the methodology's ESCALATE trigger is written specifically about the review lane failing, not a QA-over-browser override. We chose: CONTINUE with a full-depth recommendation rather than ESCALATE, since none of ESCALATE's literal clauses fired and CONTINUE's own definition fired (J-04 newly passing). Reversible: yes.
- iter-53 · goal-evaluator — Ambiguity: J-04 had no journey-level test row of its own — the merged lane verdict was BLOCKED — but three other rows explicitly covered J-04's steps 3-6, and neither goal.md nor the methodology says whether a journey can pass on evidence filed under other IDs. We chose: score J-04 `passing`, flagging its still-unrecorded walkthrough, since real citations existed and the one reason it was held back at iter-52 no longer applied. Reversible: yes.
- iter-53 · goal-decomposer — Ambiguity: the prior evaluator's next-step item and the iteration-state digest named two finalize-tail phases for treatment, but the performance-budget report's own findings named a third phase as the largest untreated contributor. We chose: scope this iteration to only the two phases named in the binding digest, deferring the third un-profiled phase to avoid bundling a third risky diagnosis effort. Reversible: yes.
- iter-52 · goal-evaluator (second entry) — Ambiguity: the iter-52 UI test results recorded FAIL for both UT-J-05 and UT-J-07, but the methodology does not say whether a lane FAIL forces a journey's status to `failing` rather than `partial`. We chose: `partial` for both, since most steps held live with a screenshot or DB row and only one step failed, consistent with iter-51's precedent. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-54.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-54-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-54-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-54-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-54/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
