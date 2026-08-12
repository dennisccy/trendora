# Iteration Summary — goal-ops-hardening-iter-69

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-12
**Iteration:** 69

## In plain words

**What you can do now:** Browse stock rankings, sector and theme pages, backtests, and all the research tools, with an honest status message while the app starts up. Backfill any date range with no hidden limit, and get a clear "nothing new" message when there's no new data to fetch. Backtest results and other computed numbers load instantly because they were worked out ahead of time, pages only fetch what they need, and the app tells you when it's crunching numbers in the background. The app answers its own health check quickly almost all of the time, even during its biggest background job — but that last part is still not fully fixed.

**What changed this time:** Nothing changed on screen. Behind the scenes, the code that measures how the health-check page responds during a heavy background job now splits that measurement into three separate parts — database reads, a readiness check, and a daily pre-flight check — so the team can see exactly which one is slow. The measurement also turned up something new and less good: three health checks got no answer at all within 5 seconds during the busiest part of a background job, a first for this project. The app itself never crashed or showed an error; it was just slow to answer those three times.

**What's next:** Stop the health-check page from redoing those two slow checks (readiness and the daily pre-flight check) on every single request — serve them from an already-worked-out value instead, the way the rest of the app already works. That's a bigger change than the recent rounds, so the next round will move more carefully and get extra review.

## Headline

handler_compute_s decomposed into db_reads_s/readiness_s/preflight_s, unit-tested (15/15 passing)

## Direction

**Signal:** holding
**Why:** No journey changed status this round — all 7 previously-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) stayed passing and J-07 stayed `partial`, and no critical anti-goal violation fired (ledger: 0 unresolved critical), so mechanically this holds rather than regresses. But the raw evidence behind J-07 got materially worse this round — the live-drill breach rate jumped from 1/1,039 last round to 77/952 (8.09%) this round, and the session's first-ever 3 non-answers appeared. The evaluator chose ESCALATE (not CONTINUE) because the newly-identified fix — stop `GET /api/health` recomputing readiness and preflight on every request — is a design change to a value the whole app shares (badge, preflight banner, `/data` panels), not another diagnostic add, so next round needs full-depth audit/coherence review.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-69: 6 new (all minor), 3 closed; iter-68: count not visible in the trimmed log excerpt
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** "This round split the health-check timer into three parts, and the parts finally point at a place the team owns. When the app was busy with the heavy 'factor lab' step, the health check's own two inner computations — the readiness check and the daily preflight check — were the slow part in every single slow answer (43 and 31 of the 74 slow answers that still got a reply). At the same time the availability numbers got worse, not better: 83 of the round's 1,402 health checks took longer than 2 seconds, and for the first time in this whole session 3 health checks got no reply at all within 5 seconds."

## What was done

- Product changes: apps/backend/app/engine/health_watchdog.py, apps/backend/app/api/health.py, apps/backend/tests/test_health_watchdog.py, reports/perf-budgets.md
- Decomposed `record_handler_compute` into three timed sub-spans (`db_reads_s`, `readiness_s`, `preflight_s`) on the same record type, flag, and JSONL writer; added 6 new unit tests (15/15 passing).
- Ran a live-job drill (952 polls across a real 17m18.9s ingest) and an idle-control drill (330 polls); joined both against the new sub-spans and the pre-receive gap to attribute time-budget shares — median breach now ~94% named (residual 5.99%), `readiness_s` dominates 43/74 answered breaches, `preflight_s` the other 31.
- Reported the pre-receive gap from existing artifacts (no new instrument), closing iter-68/b.
- Corrected two prior write-up defects from iter-68 (the "full scorecard" mischaracterization and the watchdog's own write-cost note).
- Directed the browser-qa-agent, via this iteration's own testing requirements, to arm the diagnostic flag on its own lane; it could not do so this round and named the constraint explicitly rather than posting unattributed breaches again.
- Verified all 8 journeys pass browser QA (merged PASS 8/8; raw replay PASS 8/8, zero overturns).

## What's left

- Journey J-07 (Heavy aggregates never take the service down) remains `partial` — this round's live drill showed 77/952 polls over the 2.0s ceiling (8.09%) and, for the first time this session, 3 polls got no answer at all within the poller's 5.0s timeout, even though the server itself never returned an error.
- A genuine ~6% median time-budget residual remains unexplained after all five named components; the two most likely remaining sources (the watchdog's own two JSONL-write costs) are named but not separately instrumented yet.
- This round's much higher breach rate is only partly attributed — a confirmed concurrent caller (the session's own orchestration loop) was polling the backend throughout, but that alone doesn't explain why 96% of breaches landed inside one specific processing phase.
- The diagnostic flag still cannot be armed on the browser-QA/replay lane's own backend, a fourth consecutive round — the spec-level lever has now demonstrably hit its ceiling.
- The J-05 forward-aggregate walkthrough capture remains unrecorded, an 11th round running.
- Three long-parked owner decisions remain open: the 2-second health-check ceiling policy (asked 21 times), the one-line ordering-bug fix in the browser-QA launch script, and a cost-sanction decision on the recurring ~17-20 minute real data job each round.

## Next step

Run the next round at full depth and aim it at the health check's own work, not another measuring tool. Two things now point the same way: 74 of 77 slow answers and all 3 missing answers happened during one specific background-work phase, and the new timers show the slow part is inside the health check itself — the readiness check and the daily pre-flight check, both recomputed on every single health request. So the next round's work is to stop `GET /api/health` recomputing readiness and preflight on every request and instead serve them from a stored value, the way the project's own rule already says heavy work should be served — keeping one single place that computes them. Because this touches a value the whole app shares (the badge, the preflight banner, and the `/data` panels all read it), it needs the full pipeline's audit and coherence checks rather than another light round. Smaller items to fix alongside: three write-up corrections (a missing phase breakdown, a wrong record count, and a wrong horizon label), and a decision on whether the browser-check lane's diagnostic-flag gap should get a small automation-script fix or be accepted permanently.

## Assumptions made

- iter-69 · goal-evaluator (2 of 2) — Ambiguity: the standing "do not redo" ban on bounding `factor_lab_all_warm`/`coverage_membership_timeline_refresh` by code change was conditional on the handler-body sub-timing naming a component; this round's sub-timing named two (readiness, preflight), and nothing states who declares that release condition met. We chose: declare it satisfied and mark it released, while still recommending the narrower target (stop recomputing readiness/preflight per request) rather than bounding the phase. Reversible: yes.
- iter-69 · goal-evaluator (1 of 2) — Ambiguity: the journey's promise requires "no frozen or unresponsive window"; this round 3 of 952 polls got no answer within the poller's 5-second timeout, even though the server itself logged healthy replies and zero errors in the same window. The rules don't say whether a client-side timeout on a still-computing request should fail the journey or leave it partial. We chose: keep it partial, but state the worse evidence plainly in the gap note, the results table, and the first line of the owner message. Reversible: yes.
- iter-69 · goal-decomposer — Ambiguity: last round's order to arm the diagnostic flag on the browser-check lane's own backend didn't name how, and the only two guaranteed ways (editing the launch scripts, or turning the flag on by default) are both off-limits without owner sign-off. We chose: instruct the browser-check agent, through this round's own test instructions, to turn the flag on itself and say plainly if it can't. Reversible: yes.
- iter-68 · goal-evaluator — Ambiguity: the journey's step 2 doesn't say which health-check polls count; this round two separate test runs polled the same page with different timing and different background load (one run: 1,369 polls, 1 slow answer; the other: 240 polls, 9 slow answers). We chose: score the journey against all 1,609 polls combined (10 slow answers total) rather than reporting just the smaller, better-looking number. Reversible: yes.
- iter-67 · goal-evaluator — Ambiguity: two of the journey's four checks (peak memory use, and surviving a deliberate memory-pressure test) weren't re-run this round; nothing says whether a skipped re-check should count against the journey or simply carry forward. We chose: carry those two checks forward since the code they test hasn't changed, and keep the journey at "partial" based on the one check that did get worse. Reversible: yes.
- iter-67 · goal-decomposer — Ambiguity: the prior round's recommended fix — "watch a real health request live, in the running app" — was described only at a high level and could have been built several different ways. We chose: the smallest version — two timestamps around the health-check request plus a periodic background timing probe, switched on only by a new setting that stays off by default, writing to a new diagnostic-only log. Reversible: yes.
- iter-66 · goal-evaluator — Ambiguity: a standing rule said not to re-investigate one background-work phase because four earlier tests found nothing there, but this round's fresh measurement put nearly all of the slow answers inside exactly that phase's time window. Nothing says what should win when new evidence contradicts an old, standing rule. We chose: recommend re-opening that phase as the next target, but only using a different method this time (watching the live app, not re-running the calculation on its own). Reversible: yes.
- iter-66 · goal-decomposer (2 of 2) — Ambiguity: the prior round's instruction to "use one counter everywhere" could mean unifying the measurement tool itself, or editing the browser-check agent's own internal instructions — the second option is off-limits territory for a product round. We chose: unify the measurement tool into one shared, checked-in script and point this round's test instructions at it, without touching any framework or agent instruction file. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-69.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-69-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-69-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-69-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-69/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
