# Iteration Summary — goal-ops-hardening-iter-39

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-07-31
**Iteration:** 39

## In plain words

**What you can do now:** Ask the system to backfill any historical date range and get an honest explanation when there's nothing new to add, with no artificial length limit. Watch a truthful status badge while the app starts up, updates, or recovers from a crash. Heavy calculations are done ahead of time so pages load fast, backtest evidence always comes from saved results (never a live recompute), every research page shows an honest "still working" message instead of a blank screen, and a live indicator shows when background work is running.

**What changed this time:** Nothing changed on any screen, but the team proved a big safety promise behind the scenes: when a heavy background calculation runs low on memory, the app now catches that failure cleanly, in the exact right spot, and keeps answering every request instead of crashing. They also fixed an automatic test checker that used to wrongly report "broken" when the backend was simply switched off, and fixed a backend testing switch that had been working backwards. Along the way they found a new problem — at a very tight memory limit the app can still freeze for several minutes after a job finishes — which is not fixed yet.

**What's next:** Next, the team will fix the part of the code that loads millions of price rows into memory all at once, reading them in small batches instead — the last piece needed to fully prove heavy background work can never crash the service.

## Headline

Deterministic replay lane now tells a down backend apart from a real test failure

## Direction

**Signal:** holding
**Why:** Journey J-07 "Heavy aggregates never take the service down" stayed `partial` for a fifth straight iteration, but this round genuinely closed its last untested acceptance clause: a fault-injected `MemoryError` fired inside the exact aggregate-warm handler J-07 names, with the process still answering 1,486/1,486 requests. The evaluator ESCALATEd for a fourth consecutive time on this journey — the audit lane caught a critical `MemoryError`-isolation gap that review and QA both passed, and the drill itself honestly surfaced two new open issues (a 7-minute process wedge and a second unbounded whole-table scan). No journey regressed and none newly crossed to `passing` this iteration, so direction reads as holding: real evidence progress happened inside J-07, but its status field hasn't moved.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none (J-06's restoration to `passing` happened at iter-36, just outside this 3-iter window)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 7 new, all minor, 0 critical (iter-38: 3 new, one resolved same iteration; iter-39: 4 new, all open)
- Iters with no journey state change: 3 of last 3

**Latest evaluator reasoning:** "The team finally proved the last open piece of J-07 'Heavy aggregates never take the service down': they made the memory failure happen on purpose, inside the exact step the journey names, in a real running server, and the server kept answering every single request while it happened. I checked those numbers myself in the live log file, not in the report. Seven other journeys were re-checked against a live app and all seven passed with real, different screenshots."

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/main.py, apps/backend/app/logging_config.py, apps/backend/tests/test_data_manager.py, apps/backend/tests/test_logging_config.py, apps/backend/tests/test_ingest_finalize_fault_injection.py, apps/backend/tests/test_data_manager_backfill_parallel.py, incredible_auto_dev/scripts/automation/lib/demo_runner.py, incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py, incredible_auto_dev/scripts/automation/lib/goal_gate.py, incredible_auto_dev/scripts/automation/lib/replay-lane.sh, incredible_auto_dev/tests/automation/test-replay-lane.sh
- Proved J-07 step 4 (memory-pressure isolation) via a deterministic fault-injection hook inside the named aggregate-warm handler, with the live server answering 1,486/1,486 requests during the drill.
- Hardened `backfill_workers`' per-date compute with per-thread `MemoryError` isolation, closing a critical gap the audit's first pass caught (a worker's traceback no longer pins failed-frame locals alive).
- Repaired the deterministic replay lane: a new `BLOCKED` verdict class fires when the backend is unreachable, so a downed backend can no longer masquerade as journey regressions (7/7 replay PASS against a live stack this iteration, versus 1/7 last iteration).
- Fixed the reconciliation footer to report every overturned journey with accurate per-journey wording, instead of a blanket "re-confirmed" claim.
- Fixed the `TRENDORA_FORCE_LEGACY_BAR_CACHE` env-toggle guard (`=0` no longer silently forces legacy mode) and added a root-logger config so routine `.info` logging reaches `logs/backend.log`.
- Ran a genuine live `kill -9` + restart cycle confirming J-04's interrupted-run status and J-05's cold-boot coverage panel both serve real, non-zero values.
- Verified 7 target journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) pass browser QA.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) still `partial` — 5th consecutive iteration; the mechanical root cause is `_missing_data_diagnostic`'s unbounded whole-table scan (`apps/backend/app/engine/data_manager.py:271`), not yet fixed.
- A genuine ~7-minute process freeze observed at a tightened memory cap (2650 MB trial) remains unretired and its root cause unattributed.
- iter-39/w: post-crash Run History panel under-reports progress (shows 2/18 days done when 18 were completed in memory).
- iter-39/x: the merged results artifact can still headline PASS/SKIPPED for a run whose journeys were all BLOCKED (the machine achievement gate is already closed; the human-readable headline is not).
- Owner decision: the `GET /api/health` ≤0.1s budget, now missed 6 consecutive times (3/68 polls this iteration, max 1.297s).
- Owner decision: whether `start-frontend.sh` should join the host-guard marker list.
- J-07's `[NEW]` demo walkthrough remains unrecorded for a 9th iteration (capture-only, never an iteration's own goal).
- Deferred a 4th time: Regime Lab's cold `view=pooled` background dispatch (iter-33/g).
- Golden replay-script selector refresh, carried to the pipeline's autoderive step (no browser access available in the developer role).

## Next step

Run the next iteration at full depth (mandatory via ESCALATE). One target: replace `_missing_data_diagnostic`'s whole-table materialization (`apps/backend/app/engine/data_manager.py:271`) with a bounded `yield_per` fetch — output-identical, the grouping loop unchanged — and correct the in-code comment that currently claims no unbounded whole-table scan exists. This is the change most likely to close J-07's last blocker, the most likely cause of the process wedge, and the mechanical reason earlier live-cap trials could never reach the handlers J-07 names. Then, in order: re-run the tightened-cap drill once to see whether the freeze survives the bound; make the post-crash Run History figure honest (iter-39/w); teach `merge_ui_test_results.parse_rows` a `BLOCKED` class so the merged headline cannot read PASS/SKIPPED for an all-BLOCKED run (iter-39/x); record J-07's still-unmade `[NEW]` walkthrough (capture only); and give Regime Lab's cold `view=pooled` compute the same background dispatch `/api/backtest` already has (iter-33/g, deferred a fourth time). Two owner decisions remain open and should be settled before any GOAL_ACHIEVED attempt: the `GET /api/health` ≤0.1s budget disposition (missed six times) and whether `start-frontend.sh` should join the host-guard marker list.

## Assumptions made

- iter-39 · goal-evaluator — Ambiguity: whether decision-tree clause C.4 ("same journey failed 2+ consecutive iterations") should trigger a fourth consecutive ESCALATE even though this iteration delivered its mandated target. We chose: ESCALATE again — first-match-wins precedent plus an independent trigger (the audit lane caught a critical MemoryError-isolation gap that review and QA both missed). Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: whether J-07's acceptance clause "no unbounded whole-table ORM materialization" is scoped only to the two named tables (forward_returns/scanner_results) or governed by the broader headline sentence, given the newly-found site is on daily_prices. We chose: the broad reading — the clause is not satisfied — following this session's own iter-37 precedent and goal.md's Success Criteria, which name daily_prices explicitly. Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: whether J-04 ("Non-blocking boot with visible status") should stay `passing` when neither this iteration's lanes supplied fresh live verification (the deterministic replay FAILed only because the backend was down, and the browser lane declined to restart it). We chose: kept J-04 `passing` on evidence durability but deliberately did not advance its verification date, and named every uncovered step. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: whether to escalate a third consecutive time on the same J-07 blocker even though the iteration was already run at full depth. We chose: ESCALATE again — the review and QA lanes had both passed a real regression and an unmeasured-claim gap that only the audit lane caught. Reversible: yes
- iter-37 · goal-evaluator — Ambiguity: whether J-07 should cross to `passing` when its steps 1 and 4 were demonstrated through a different trigger path than the journey's own acceptance text names. We chose: kept J-07 `partial` for a third consecutive iteration — the acceptance text's own words require this-iteration evidence, not inference. Reversible: yes
- iter-37 · goal-decomposer — Ambiguity: whether running J-07's own already-implemented verification drill counts as a second "risky" item alongside a genuine structural code change under rule 5 ("never bundle two risky changes"). We chose: bundle both into one iteration — rule 5's precedent in this session applies to code changes, not verification-only passes. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether J-06 should return to `passing` when the specific clause that downgraded it was fixed but a sibling clause's fresh measurement was still missing. We chose: restored J-06 to `passing` and cleared the evidence-makeup flag — evidence expires with change, not time, and the sibling gap was carried as a named capture-only ride-along instead. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-39.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-39-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-39-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-39-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-39-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-39-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-39-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-39-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-39-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-39-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-39-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-39-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-39-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-39/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
