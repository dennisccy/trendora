# Iteration Summary — goal-ops-hardening-iter-30

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-29
**Iteration:** 30

## In plain words

**What you can do now:** Back-fill any historical date range and get an honest explanation when there's nothing new to fetch, with no hidden size limit. Watch a truthful status badge while the app starts up. See ranking, regime and backtest numbers that load instantly because they were computed ahead of time rather than while you wait — the Backtest page always shows saved results, never a live recalculation. See a live indicator whenever the app is working in the background.

**What changed this time:** No new screens. The background calculation that builds the Backtest page's numbers (and the matching research tool) now processes history in smaller batches instead of loading it all into memory at once — an independent check measured about a one-fifth cut in peak memory use, and a full-scale trial run finished cleanly for the first time. A separate research page, Factor Lab, still crashes with a memory error when opened — that problem was found last round and is still unfixed.

**What's next:** Next, the team will stop the Factor Lab research page from crashing when it's opened, and finish tightening the one remaining memory bottleneck in the Backtest calculation.

## Headline

Backtest-evidence calculation now runs in memory-bounded batches; Factor Lab page still crashes on load

## Direction

**Signal:** holding
**Why:** No journey moved to `passing` or to `failing`/`regressed` this iteration — J-06 and J-07 both stayed `partial` despite real, audited progress (a measured 16.4%/21.6% peak-memory cut in `compute_forward_aggregates`, a clean full-basis warm, zero new MemoryError frames), because the exact container that crashed before (`stock_obs`) is still unbounded and neither journey has a fresh capture or replay artifact. The four open AG-8 findings (led by the Factor Lab crash, reconfirmed for a 2nd consecutive iteration) stay classified `minor`, not `critical`, so the tree lands on CONTINUE rather than a regression halt — but the iteration also surfaced a critical pipeline-integrity bug (a P1 browser-QA FAIL silently merged into a canonical "PASS 6/6") that must be fixed before any future GOAL_ACHIEVED claim can be trusted.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-05, J-06, J-07, J-08 (all at iter-28; J-06/J-07 later slipped back to `partial` at iter-29 and stayed there at iter-30)
- Regressions in last 3 iters: none formally declared — the evaluator explicitly rejected REGRESSION at both iter-29 and iter-30 (no journey moved `passing`→`failing`); J-06/J-07 did move `passing`→`partial` at iter-29 on newly-found AG-8 evidence and have not recovered since
- Anti-goal violations in last 3 iters: iter-29 introduced 4 new findings (all minor: Factor Lab crash, boot warm-up, `compute_forward_aggregates`, ingest coverage refresh) while closing the session's oldest AG-8 finding; iter-30 introduced 0 new findings and carried the same 4 (all minor, unresolved)
- Iters with no journey state change: 1 of last 3 (iter-30)

**Latest evaluator reasoning:** This iteration did what it set out to do, and the proof holds up when checked. The background job that builds backtest figures used to run out of memory; it now finishes cleanly over the full 30-year data set, and the health check answered 273 out of 273 times while it ran. Two things stop this from being finished: only two of the three memory containers named in the plan were fixed (the third is the exact line that crashed before, and it is still unbounded — the audit measured the improvement at about 16-22 percent, which is breathing room, not a fix), and the Factor Lab page still runs out of memory and shows no figures. Nothing that was working before broke: all six other journeys replayed green.

## What was done

- Product changes: apps/backend/app/engine/forward_testing.py, apps/backend/app/config.py, config.yaml, apps/backend/tests/test_forward_testing_aggregates_streaming.py, reports/perf-budgets.md, docs/handoffs/goal-ops-hardening-iter-30-dev.md
- Bounded two of `compute_forward_aggregates`'s three named accumulators (`ret_by_run_symbol`/`mdd_by_run_symbol`), merged into a chunk-scoped `_forward_agg_slice_map` walked by run id via a new dedicated `walk_forward.forward_agg_run_chunk` config knob (default 100), proven to actually chunk against the live ~1,858 runs/horizon basis.
- Added byte-identity + shipped-chunk-binds unit tests (51 new/updated, all passing) proving output is unchanged across 5 horizons, 4 chunk widths, with/without `as_of`.
- Closed J-06's mechanical gap: appended a fresh 11-page curl sweep + boot-to-health measurement to `reports/perf-budgets.md` with explicit PASS/WARN scoring.
- Live full-basis ingest warm completed with zero `MemoryError` carrying a `compute_forward_aggregates` frame; `/api/health` answered 200 on 273/273 polls.
- Audit independently measured a real but partial win (-16.4% traced peak / -21.6% RSS) and proved `stock_obs` — the exact allocation site that raised the original production crash — is still unbounded.
- Verified 0 of 2 target journeys (J-06, J-07) reached `passing`; both remain `partial`. All 6 required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) replayed PASS.
- Audit found and disclosed a framework bug: the merge script's row-ID pattern silently dropped browser-QA's `TC-`-prefixed rows, turning a P1 Factor Lab FAIL into a canonical "PASS 6/6" report.

## What's left

- Journey J-06 ("Pages load only what they need") partial — no fresh real-browser TTI sweep and no deterministic replay artifact for `J-06.json` exists this run (the audit's claim of running it is prose-only, no results file or screenshot found).
- Journey J-07 ("Heavy aggregates never take the service down") partial — `stock_obs`, the exact frame that crashed before, is still unbounded; the residual ~922MB still scales linearly with the horizon-partition, and no J-07 capture exists this iteration.
- Closure blocker: the UX-regression report is UX-REGRESSION-FAIL on the Factor Lab crash, so closure is CLOSURE-FAIL until it is fixed and ux-regression is re-run.
- The Factor Lab research page still raises a `MemoryError` on load — reconfirmed for a 2nd consecutive iteration; its returned `pools[h]` list is deliberately unbounded and there is no single-flight guard against concurrent duplicate computes.
- Framework bug: `merge_ui_test_results.py`'s row-ID regex only matches `UT-` IDs, so a `TC-`-labelled P1 FAIL can be silently merged into a canonical "PASS" — must be fixed before any GOAL_ACHIEVED claim can be trusted.
- `GET /api/health` measured 0.127787s vs its ≤0.1s budget (WARN) — an owner decision to amend or rescope this budget is needed before J-06/J-07 can both honestly read "within budget."
- Known, deferred, unchanged this run: the boot warm-up (`warmup.py:194`) and ingest coverage refresh (`prices.py:141`) memory faults did not recur this window but remain unfixed in code; `_backfill`'s cross-call rollback residual (audit B2); UT-04's fresh-install database fixture or a written waiver.

## Next step

Run the next iteration at full depth with one main target: stop the Factor Lab page from running out of memory by bounding `pools[h]` (`research.py:583`) the same way its accumulator was bounded last round, and add the single-flight de-dup guard `factor_lab_all_cached` lacks — then open the page in a real browser on an idle host and confirm the decile table and rank-IC figures render real numbers. Second, finish J-07 by bounding `stock_obs` (`forward_testing.py:988`), which deliberately means re-pinning `_attribution_slices`'s frozen signature, and record the warm's peak memory under the declared cap in `reports/perf-budgets.md`. As ride-alongs (never the iteration's own goal): get a real `J-06.json` deterministic replay row and a real-browser TTI sweep. Outside the journey loop, widen `merge_ui_test_results.py`'s row-ID pattern to accept `TC-` IDs so a FAIL headline can never again be silently merged into a canonical PASS. Owner, non-blocking: decide whether to amend or rescope the `GET /api/health` ≤0.1s budget.

## Assumptions made

- iter-30 · goal-evaluator — Ambiguity: the auditor claimed it executed and passed the `J-06.json` deterministic replay (TC-07) but left no results artifact or screenshot behind; goal.md doesn't say whether a trusted agent's prose report can stand in for the artifact it claims to have produced. We chose: scored J-06 `partial` with `evidence_makeup: true`, treating the missing artifact as a capture gap rather than crediting the prose — no artifact means no status advance. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: AG-8 (critical) forbids the widening basis from crashing a page or exhausting memory; this iteration's own TC-05 spot-check reproduced a live MemoryError on Factor Lab with browser-QA/ux-regression/closure all returning FAIL, and goal.md doesn't say whether a caught exhaustion that leaves the process serving a contained, honest error box is the critical violation or a minor finding. We chose: kept all four AG-8 findings `minor` (verdict CONTINUE, not REGRESSION) — the page renders a calm honest error box, the log disproves the "terminated the whole process" claim, the host was never under real memory pressure, and every unblock path is agent work. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: J-07's acceptance clause requires no unbounded ORM materialization on the warm/serving path; `compute_forward_aggregates` itself (its own named producer) raised a caught MemoryError this iteration, and goal.md doesn't say whether a caught failure inside the named producer breaks the journey or merely dents it. We chose: scored J-07 `partial` (not passing, not failing) — the acceptance clause is contradicted but the service was never taken down. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: J-06 step 2 requires recording fresh measurements in `reports/perf-budgets.md`; this iteration measured but never wrote to the file, and goal.md doesn't say whether measuring-without-recording satisfies the step. We chose: scored J-06 `partial` rather than `passing` — the step is literal, checkable, and unmet. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: AG-8 (critical) vs. a caught, non-fatal memory exhaustion that leaves the UI showing a contained error box — goal.md doesn't say which this is. We chose: recorded four new AG-8 findings as `minor`, not `critical`, so the verdict is CONTINUE not a REGRESSION halt — the pages render calm, honest error states and every failure is caught and non-fatal. Reversible: yes
- iter-29 · goal-decomposer — Ambiguity: AG-8 requires the UI to degrade gracefully with an honest NA placeholder; goal.md doesn't say whether reusing the Evidence page's existing silent-omission behavior already satisfies that for a new failure cause, or whether the new cause must be visually distinguishable. We chose: to make it distinguishable — added a new `expectations_status: "unavailable"` field and a calm inline note, rather than silently reusing the existing "render nothing" path. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: J-07's acceptance clause (no unbounded ORM materialization on the warm/serving path) could be scoped to J-07's own named producer or to every warm/serving path in the backend; the still-open AG-8 finding in `research.py` sits on a neighbouring aggregate. We chose: scored J-07 `passing`, reading the clause as scoped to its own named producer, and tracked `research.py`'s defect as a separate open AG-8 finding. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: the DoD lists TC-4 (a coverage panel's "not yet computed" state) among J-05's pass criteria, but that state is only reachable on a genuinely fresh-install database; goal.md doesn't say whether an environmentally unreachable DoD sub-case blocks the journey it's attached to. We chose: scored J-05 `passing` with the skip recorded as an open gap, since the state isn't one of J-05's own four goal.md steps. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: after a build touched only part of a journey's path, goal.md doesn't say how much of the journey must be re-exercised to restore `passing`. We chose: scored J-07/J-08 `passing` on a scope-of-change test (confirming via git diff which functions were untouched) rather than a re-run-everything test. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-30.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-30-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-30-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-30-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-30-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-30-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-30-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-30-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-30-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-ops-hardening-iter-30-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-30-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-30-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-30-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-30/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
