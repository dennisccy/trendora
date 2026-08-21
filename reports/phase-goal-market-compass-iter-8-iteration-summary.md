# Iteration Summary — goal-market-compass-iter-8

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-21
**Iteration:** 8

## In plain words

**What you can do now:** Every stock in the scanner shows its real market sector instead of an unlabeled placeholder. Each candidate the compass suggests for your next trading session comes with a plain-English reason why it was picked, and why others were not.

**What changed this time:** Nothing changed on screen this round. Behind the scenes, the team rebuilt the tool that puts back missing stock prices after last month's data-deletion accident and used it for real for the first time: 20 of the 587 companies missing prices for 11 and 12 August now have them back, with the other 567 still missing on purpose while the team checks the fix in small, careful batches.

**What's next:** Before touching the price data again, the team will fix a background checking tool that keeps switching itself on when it should stay off. Then they'll continue restoring the remaining 567 companies' missing prices, a careful batch at a time.

## Headline

This iteration put real data back for the first time.

## Direction

**Signal:** regressing
**Why:** A CRITICAL AG-17 violation occurred this iteration — the contract-forbidden J-01/J-04 replay lane ran a second time, this time during the very full-depth re-run meant to add the missing audit lane, and overwrote two quarantined incident-evidence screenshots before the in-pipeline auditor restored them byte-for-byte. Audit finding P2 proves the underlying cause (the pipeline's lane gate ignoring goal.md's TC-19 prohibition) is unfixed at either depth, so a third recurrence is live risk, even though this iteration also made real forward progress on J-10 (40 rows / 20 of 587 symbols genuinely restored). No journey itself regressed and the evaluator's verdict stays CONTINUE, but the recurring, still-open process fault is why the trend reads regressing rather than holding.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: none
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 2 critical (iter-7 AG-9 fail-open convention gate — found and fixed in-iteration; iter-8 AG-17 forbidden-lane evidence overwrite — found and fixed in-iteration, root cause still open per audit finding P2)
- Iters with no journey state change: 1 of last 4

**Latest evaluator reasoning:** "This iteration put real data back for the first time. Twenty of the 587 missing company codes now have prices again on both 11 and 12 August — 40 rows, and not one row outside those two days. [...] the gate's clean result was measured against the same supplier, so it proves the gate is built, not that it can tell two suppliers apart; and a browser test lane that this project's rules forbid ran twice, the second time during the very re-run that was meant to add the missing safety review, and it overwrote two protected evidence pictures before the reviewer put them back."

## What was done

- Product changes: apps/backend/app/engine/j10_recovery.py, apps/backend/app/data_providers/yahoo_provider.py, apps/backend/tests/test_j10_recovery.py, apps/backend/tests/test_provider_clients.py
- Rebuilt J-10's convention gate as a per-symbol, two-part test (path agreement + stable multiplicative bridge), with both thresholds fixed as module constants before the live run and removed from the production entry point's parameters (resolves prior audit findings B2, B3, B5, B6).
- Ran the gated recovery for real against the live database: all 20 sampled symbols passed and 40 `daily_prices` rows were restored for 20 of the 587 missing symbols across 2026-08-11/2026-08-12; the remaining 567 symbols were deliberately not attempted this iteration (precommitted, documented scope).
- Restructured/added backend tests: 37 tests in `test_j10_recovery.py` (all passing) plus 6 new synthetic-payload tests in `test_provider_clients.py`; 87/87 backend tests pass total, independently re-run by both the reviewer and the in-pipeline auditor.
- In-pipeline full-depth audit found and fixed a CRITICAL AG-17 breach: a contract-forbidden replay lane ran a second time and overwrote two quarantined incident-evidence screenshots, restored byte-for-byte from commit `47d50d04` with the recurrence bytes preserved alongside.
- Audit corrected three false claims that had propagated into the dev handoff: the "agreement" result is a same-vendor (Yahoo-vs-Yahoo) comparison, not cross-vendor validation; the 2026-05-12 ScannerRun is unrepaired iter-5 drill damage, not an unrelated gap; and 14 tables/~4,600 rows were written this iteration, not the 3 originally reported.
- No admissible browser-QA/replay evidence exists for J-01/J-04 this iteration — the only rows produced came from the forbidden lane and are quarantined; J-10 itself has no UI surface and was verified instead via direct read-only database queries and a transient `GET /api/compass` call.

## What's left

- J-10 "Bounded recovery of the two trading days the iter-5 drill deleted" stays partial: 567 of 587 proven-missing symbols still not attempted; goal.md's Completion rule states it cannot close at 20/587.
- Journey J-07 (The Today page answers the ten-second read) failing — unchanged since iter-0, out of scope this iteration.
- Journey J-08 (Market page moves over intact and history stays honest) failing — unchanged since iter-1, out of scope this iteration.
- J-02 (What changed since the previous session) and J-03 (Plain-English summary with cited facts) stay partial, blocked behind J-10's remaining 567 symbols and the new J-11 Stage G clean-regeneration step.
- J-05 and J-06 (the manifest-freeze journeys) stay partial, blocked behind the same make-up run, now additionally gated behind J-11 Stage G.
- New Must-have journey J-11 (Incident-bounded clean regeneration of derived state), inserted by the owner this iteration, is status `unknown` and never measured — blocks GOAL_ACHIEVED by definition.
- The forbidden J-01/J-04 replay lane's root cause (the pipeline's lane gate) is still unfixed — it ran a second time at full depth this iteration; audit finding P2 shows correcting the depth marker alone did not stop it.
- The `docs/goal.md` sentence crediting a Yahoo-vs-Stooq price match is factually wrong (the comparison was Yahoo-vs-Yahoo) and still needs an owner correction.
- Closure gate reports CLOSURE-FAIL on two bookkeeping artifacts (`runs/goal-market-compass-iter-8/plan.md` and `implementation-summary.md`) — a process gap, not a product defect.

## Next step

Per the evaluator: three things next turn, in order, at full depth. First — before any further database write — fix the pipeline's lane gate so the forbidden J-01/J-04 replay lane stops running against the damaged database at either depth; it has now run twice, started a second backend/frontend both times, and overwritten protected evidence once. Second, continue the recovery from 20/587 without restarting: judge each of the remaining 567 symbols under the same fixed per-symbol gate, name any that fail by reason, and commit the recovery driver script this time so the run is reproducible. Third, one item needs the owner: correct the `docs/goal.md` sentence that credits Stooq for prices that were actually Yahoo's (the comparison was Yahoo-vs-Yahoo for this window) — the underlying conclusion that one series end-to-end fixed the earlier false alarm still stands. Only after the recovery reaches its accepted end state should iteration 9 move to J-11's incident-bounded clean regeneration of derived state, which is also where J-01–J-04 finally get re-checked.

## Assumptions made

- iter-8 · goal-evaluator — Ambiguity: The decision tree returns REGRESSION on an unresolved critical anti-goal violation; AG-17 (critical) was genuinely breached this iteration (the forbidden replay lane overwrote two quarantined incident-evidence screenshots), but the instance was repaired in-iteration while the underlying cause (audit finding P2: the lane runs at full depth too) stays open. We chose: Scored it `resolved: true` and returned CONTINUE — the same reading iters 3 and 7 used for their own in-iteration critical fixes — after verifying the restore byte-for-byte and making the unfixed cause the first item of the next-step recommendation. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: Evidence durability formally still holds for J-01/J-04 (their product code is byte-unchanged this iteration), but the live data basis moved underneath them (the "Latest" as-of is now 2026-08-12, served by a 20-of-587 recovery-era price layer goal.md itself calls non-authoritative), and the only rows produced this iteration for either journey came from the forbidden replay lane. We chose: Kept both at `passing`, unchanged, rather than downgrading on reasoning alone, and recorded the risk explicitly in each journey's `gap` field, naming J-11 Stage G as where both must be re-measured. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: The iter-8 spec said to "expect a partial outcome, and that is acceptable," but `docs/goal.md` was then amended (after this iteration's product commit) with a Completion rule stating J-10 cannot close at 20/587 and no partial-completion threshold may be invented. We chose: Scored J-10's status against the CURRENT goal.md text, while judging the developer's conduct against the spec text they were actually given — declining to widen the sample was correct discipline at the time. Reversible: yes.
- iter-8 · developer — Ambiguity: A mid-task coordinator message directed extending the run to the remaining 567 symbols after the sampled 20 all passed cleanly, but this iteration's own spec explicitly forbids widening the comparison sample after seeing an early result. We chose: Declined the coordinator's mid-task directive and proceeded with exactly the precommitted 20-symbol outcome; the other 567 are recorded as "not attempted," never sampled. Reversible: yes.
- iter-8 · developer — Ambiguity: The redesigned two-part test (path agreement + bridge dispersion) named no specific numeric bound, having been explicitly delegated to the developer by the goal-decomposer. We chose: `PATH_AGREEMENT_TOLERANCE = 0.5%`, `BRIDGE_DISPERSION_BOUND = 1.5%` (deliberately different magnitudes so the two tests stay independently meaningful) and `MIN_COMPARABLE_PAIRS_PER_SYMBOL = 3`, all fixed and tested before the live comparison ran, never adjusted after seeing the result. Reversible: yes.
- iter-8 · goal-decomposer — Ambiguity: The dispatching coordinator's context permitted planning browser-QA for J-01–J-04 conditionally on this iteration's recovery succeeding, but a goal-mode spec is fixed before dispatch with no mechanism to make a lane's execution conditional on an earlier step's runtime result. We chose: Kept Required-still-passing empty and named zero browser/replay targets for J-01–J-04, deferring their verification to iteration 9 unconditionally regardless of this iteration's outcome. Reversible: yes.
- iter-8 · goal-decomposer — Ambiguity: AG-9's addendum authorizes the comparison fetch for "a SAMPLE" of proven-missing symbols while J-10's redesigned text is fail-closed per-symbol, leaving open whether this iteration should widen the comparison sample toward all 587 or may keep a smaller sample. We chose: Directed the developer to keep the comparison sample-based, treating a resulting partial restoration as a fully acceptable, non-blocking outcome rather than a shortfall to force-widen after seeing results. Reversible: yes.
- iter-8 · goal-decomposer — Ambiguity: J-10 step 2a's redesigned test requires precommitted numeric thresholds, but unlike the superseded absolute-level test (whose 0.75% goal.md itself proposed), the current text states the discipline without proposing specific numeric values. We chose: Directed the developer, not the goal-decomposer, to choose and precommit the specific numeric values with a documented empirical basis before the live run. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-8.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-8-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-8-review.md |
| Browser QA | BLOCKED | reports/phase-goal-market-compass-iter-8-ui-test-results.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-8-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-8-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-8-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-8-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-market-compass-iter-8-ux-regression.md |
| QA | PASS | reports/qa/goal-market-compass-iter-8-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-8-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-market-compass-iter-8-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-8/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
