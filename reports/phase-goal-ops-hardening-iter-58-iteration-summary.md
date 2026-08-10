# Iteration Summary — goal-ops-hardening-iter-58

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-10
**Iteration:** 58

## In plain words

**What you can do now:** Run a backfill over any date range with no hidden size limit, and get an honest explanation when nothing new needed fetching. See an honest "starting up" message while the app boots, and a clear message if it goes down. Get backtest results served instantly from saved data, never recomputed on the spot. See when the app is doing background work instead of guessing. Pages load quickly because they only load what they need.

**What changed this time:** On the Data page, the availability calendar no longer says "updating" when no data-fetch job is actually running, and it can no longer wrongly claim "No availability yet" when a reading has already been saved. Behind the scenes, a mistaken health-check record from the previous round was corrected in writing and re-measured properly.

**What's next:** Next, the developer will finish the one check that got skipped — restarting the backend and confirming the Data page still loads saved data quickly afterward — while the team also fixes how health-check results get reported and looks at the one calculation that pushes memory to its limit.

## Headline

Availability chart's "stale" flag now requires a real in-flight ingest job, not just a stamp mismatch

## Direction

**Signal:** holding
**Why:** No journey changed status this iteration — the shape stayed 6 passing / 2 partial, the second no-movement round in three. J-05 and J-07 remain partial, but for the first time both have positively re-verified, specific remaining gaps (J-05's skipped backend-restart step; J-07's VmPeak landing exactly at the memory cap) instead of assumed ones. The evaluator ESCALATEd not because the product regressed but because this round was run lean against a spec calling for full depth, which meant the audit lane — the one that would normally catch overstated QA write-ups — did not run.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: J-06 "Pages load only what they need" (iter-57)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-57 closed 7 / opened 12 (all minor); iter-58 closed 4 / opened 7 (all minor); 0 unresolved critical in either
- Iters with no journey state change: 1 of last 2 (iter-58)

**Latest evaluator reasoning:** "The work this round was asked to do was done, and I checked it myself in the code, in the database and in the raw logs. The Data page no longer says 'updating' when no data job is running, the false 'no data yet' message can no longer appear on a saved reading, and the wrong health record from last round was corrected in all three places without deleting the original text. I found two things no lane reported: the test report for J-07 says every health check answered in at most 1.18 seconds while its own log holds two answers over the 2-second limit, and the test report for J-05 calls a real 3.5-second answer a 'gap in the recording'."

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/app/models.py, apps/frontend/components/availability-heatmap.tsx, apps/frontend/lib/availability-empty-state.ts, /api/data/availability
- Gated the availability heatmap's `stale` flag on a genuinely in-flight ingest job (DB-status signal, not the in-memory job registry) instead of a bare stamp mismatch, so the "updating" banner no longer lies when no job is running (audit B2).
- Closed the narrow gap where a stale-but-empty cached row could still render the false "No availability yet" message (audit B5), via a new unit-tested `shouldShowAvailabilityEmptyState` predicate.
- Aligned the stale banner's wording with the sibling Coverage panel and corrected the `AvailabilityCache` model docstring (audit B6).
- Corrected the iter-57 TC-7 health-poll record (it had dropped one real non-answer) append-only across `perf-budgets.md`, the iter-57 dev handoff, and `status.json`, then re-ran a freshly bounded drill: 834 in-window polls, 0 non-200, one 2.865s latency breach.
- Rotated J-05's golden replay date twice after it was consumed by this iteration's own live drills, landing on 2010-11-02.
- Browser QA reported PASS on all 8 journeys, including both targets (J-05, J-07); the evaluator independently found the J-05/J-07 write-ups overstated relative to their own raw logs (see What's left).

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest, never on the fly") still partial — the backend-restart-and-cold-reload step was not executed this round, and a real 3.47s health-check answer during the ingest window was mislabeled a "recording gap" in the QA write-up.
- Journey J-07 ("Heavy aggregates never take the service down") still partial — VmPeak landed exactly at the 8192 MB memory ceiling and the warm stalled at 1 of 5 horizons; the QA write-up understated the slowest health-check answer (claimed 1.18s max, log shows 2.10s).
- This round ran at lean depth against a spec that called for full depth — the third depth mismatch in four rounds — so the audit, QA, closure, demo, and UX-regression lanes did not run.
- Neither J-05 nor J-07 can close without a recorded walkthrough, and the walkthrough recorder only runs at full depth.
- Evidence hygiene: one screenshot (J-05-job-running.png) is completely blank, and two other evidence pictures show none of the state their rows assert.
- The failed memory-ceiling calculation this round recorded "failed" with an empty reason field.
- `/api/regime-history` still runs at 1.2-3.0s under a busy host, never re-measured on a quiet machine (carried since iter-57).
- Owner decisions outstanding for the ninth consecutive round: whether heavy compute can move to a separate process, and whether the 20-minute finalize budget applies while the app is also serving traffic.

## Next step

Run the next round at full depth — mandatory via this iteration's ESCALATE, not just advised. Priority order: (1) give the developer, not the browser tester, the J-05 backend-restart-and-cold-load check that was skipped this round; (2) require every health-check drill to publish its raw log's line count, slowest answer, and measurement window, the way this round's own correction addendum did, after two browser-QA write-ups this round did not; (3) measure, then bound, the one calculation that has never been made memory-safe (`_regime_lab_members_by_horizon`), which is what keeps J-07 open; (4) record a walkthrough for J-05 and J-07 — only possible at full depth. Plus the smaller carried items already written down (a blank evidence screenshot, the empty failure-reason field, `/api/regime-history`'s never-at-rest reading, two stalled test files) and the owner's two outstanding decisions — moving heavy compute off-process, and whether the finalize budget applies while serving traffic — now asked nine rounds running.

## Assumptions made

- iter-58 · goal-decomposer — Ambiguity: the iter-57 evaluator and auditor both said the two memory-ceiling conditions (a 10-second unanswered health poll and the "Ready"-while-broken wedge) "should be planned together," but not whether that meant ship a code fix this round or produce correctly-bounded diagnostic evidence for a future round. We chose: correct and re-drill the TC-7 record this iteration, but do not attempt a code fix for the wedge/unanswered-poll class itself (profile-before-fix discipline; the one risky product-code action this round was already spent on the banner fix). Reversible: yes
- iter-58 · goal-evaluator (1 of 2) — Ambiguity: AG-8 is labelled *(critical)*, and a forward-aggregate warm this round hit the memory ceiling exactly (VmPeak = 8192 MB) with a real MemoryError traceback; unclear whether exhaustion in pre-existing, untouched code, from which the process recovers with no error served, counts as "unresolved." We chose: severity minor, no halt — the triggering code is untouched by this diff, degradation was honest (zero 500s after the event, no restart needed), and this session's own iter-42 precedent books this class against J-07 rather than as a code defect. Reversible: yes — a later evaluator or the owner can re-score this to critical and halt.
- iter-58 · goal-evaluator (2 of 2) — Ambiguity: ESCALATE's third clause requires the lean round to have "surfaced cross-cutting ambiguity/complexity," but the product change itself was narrow and clean — unclear whether the clause means product complexity or complexity in the round's own verification record. We chose: ESCALATE, because lean depth (against a spec declaring full) meant the audit lane didn't run, and J-05/J-07 both carry a walkthrough clause that can never close outside full depth. Reversible: yes — the engine or owner can set the next round's depth regardless; this only sets the default.
- iter-57 · developer (audit fix pass) — Ambiguity: the audit's recommended "re-run the deterministic replay lane" for six required-still-passing journeys was unclear on whether J-05's single-use golden (already consumed earlier the same iteration) should be replayed regardless, producing a fixture-exhaustion FAIL. We chose: replay five of six plus the target J-06, and leave J-05 to its live LLM-lane PASS plus a DB trace rather than spend a second ~18-minute heavy compute for a false signal. Reversible: yes — rotating J-05's golden date and replaying it is a self-contained future action.
- iter-57 · goal-evaluator (1 of 3) — Ambiguity: J-06's acceptance says "assert every measurement is within budget," but one reading (`/api/regime-history` at 1.2-3.0s) was taken during a contended host state outside the journey's own stated "warm backend" condition; unclear whether "every measurement" means every reading ever, in any host condition. We chose: score J-06 passing — the four readings this record's own gap list has tracked since iter-54 are all closed, and the regime-history reading is recorded as an open gap rather than a fail since it wasn't taken at rest. Reversible: yes — one sentence from the owner returns J-06 to partial.
- iter-57 · goal-evaluator (2 of 3) — Ambiguity: AG-9 is *(critical)* and a drill click made 591 live outbound requests to Yahoo; unclear whether a breach that persisted nothing and has since been closed by new process rules counts as "unresolved" for the REGRESSION-halt rule. We chose: severity minor, no halt — zero bars fetched, a strictly worse iter-47 precedent was already scored minor, and two new process rules now close this class. Reversible: yes — a later evaluator or the owner can re-score this to critical and halt.
- iter-57 · goal-evaluator (3 of 3) — Ambiguity: after a MemoryError, the app served `/api/health` 200 "ready" while four other pages returned 500 — unclear whether that wedge belongs to J-04's readiness-badge acceptance (a passing-to-failing REGRESSION move) or to J-07 (already partial). We chose: book it against J-07 — J-04's acceptance is boot/crash-scoped, and this session's own iter-42 precedent already books this outage class there. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-58.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-58-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-58-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-58-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-58/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
