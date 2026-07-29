# Iteration Summary — goal-ops-hardening-iter-31

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-29
**Iteration:** 31

## In plain words

**What you can do now:** Back-fill any historical date range with no size limit and get an honest explanation when there's nothing new to fetch. Watch a status badge that stays truthful through startup, updates, and background work. Open the Backtest page and get results instantly because they were computed ahead of time, not while you wait. See the Evidence page tell you plainly when one figure couldn't be computed rather than hiding it. Get a live signal whenever the system is busy working in the background.

**What changed this time:** One research screen, the Factor Lab "all factors" view, used to show an error box every single time it was opened. It now loads successfully and displays the same real numbers for every scoring factor and every time horizon — nothing else about the page changed, it simply works now. The team also made sure that if two people open it at the exact same moment, the heavy calculation only runs once instead of twice.

**What's next:** Next, the team will fix the one remaining unbounded memory spot in the background calculation behind the "heavy work never takes the site down" promise, and settle how page-loading speed should be measured before finishing that work.

## Headline

The Factor Lab "all factors" view no longer crashes with a memory error.

## Direction

**Signal:** holding
**Why:** This iteration closed the session's oldest open critical finding (iter-29/a, the Factor Lab `MemoryError` crash) with live, self-verified proof — zero MemoryError since this run's own boot line, 23/23 successful requests, byte-identical output. No journey's overall status changed: the six required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) stayed `passing`, and the two target journeys (J-06, J-07) stayed `partial` for the third consecutive iteration, each on a different, already-known gap. No regression, no newly-passing journey, no failing journey — direction is holding at 6-of-8 Must-have journeys passing.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total (iters 29-31): none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 5 new (all minor: 4 at iter-29, 1 at iter-31); 1 resolved (iter-31, closing iter-29/a)
- Iters with no journey state change: 2 of last 3 (iters 30 and 31; iter-29 moved J-06/J-07 from passing to partial)

**Latest evaluator reasoning:** "This iteration had one job, and it did it. The Factor Lab page — the one that showed an error box instead of numbers for the last two iterations — now loads and shows real figures for all 11 factors. I checked this myself in the backend log rather than trusting the report: zero out-of-memory errors after this run's own start-up line, and 23 successful page requests. Both remaining journeys, J-06 'Pages load only what they need' and J-07 'Heavy aggregates never take the service down', are still partly done. Neither got worse."

## What was done

- Product changes: apps/backend/app/engine/research.py, apps/backend/app/config.py, config.yaml, apps/backend/tests/test_factor_lab_all.py, apps/backend/tests/test_research_streaming.py
- Bounded the Factor Lab all-factors view's return-value memory representation, closing AG-8 finding iter-29/a (a 100%-reproducible `MemoryError` on `/research/factor-lab?all=true`), deferred at both iter-29 and iter-30.
- Added a single-flight de-dup guard to `factor_lab_all_cached` so concurrent requests for the same identity share one compute instead of duplicating it (fixes audit-found gap B5); review caught the first cut's 45s wait as far shorter than the measured ~300s compute, fixed to a derived 900s.
- Added a config-driven safety tripwire (`research.factor_pool_max_observations`) that logs a warning — never crashes or truncates — if a future data-scale widening approaches the ceiling again.
- Verified 9/9 journeys pass browser QA (6 required-still-passing + J-06/J-07 target journeys + the Factor Lab smoke check); the audit independently re-verified the crash path end-to-end and fixed 2 additional gaps (an unreachable disclosure warning, a memory-bound test that checked a config integer instead of the actual data structure).

## What's left

- Journey J-06 (Pages load only what they need) partial — the real-browser 11-page time-to-interactive sweep still hasn't been run; `reports/perf-budgets.md` wasn't re-asserted despite this iteration touching a data-path file; the frontend's `next dev` launcher may invalidate any future speed measurement (flagged for the first time this iteration, after 31 iterations unflagged).
- Journey J-07 (Heavy aggregates never take the service down) partial — `stock_obs` (`forward_testing.py:988`) remains unbounded inside its own named canonical producer, deferred a third time; the full warm, the health-poll drill, the induced-pressure abort, and the perf-budgets VmPeak record are all still undone.
- New anti-goal finding iter-31/e (minor, unresolved): the Factor Lab fix is a measured 2.63x constant-factor reduction, not an asymptotic bound — the same crash class returns at roughly 2.5-3x today's data scale.
- Carried anti-goal findings (all minor, unresolved): iter-29/b boot warm-up `MemoryError` (`warmup.py:194`, readiness pill wording undecided); iter-29/c `stock_obs` `MemoryError` (`forward_testing.py:988`); iter-29/d whole-table `daily_prices` prefill (`prices.py:141`).
- `merge_ui_test_results.py`'s `_ROW_RE` regex still matches only `UT-`-prefixed rows, silently dropping `TC-`-prefixed rows (and any FAIL headline) from the merged report — flagged since iter-30, still unfixed.
- Owner decision pending: `GET /api/health` measured 0.128s vs its ≤0.1s budget; until amended or rescoped, J-06 and J-07's step-2 acceptance can never both read true.
- Owner decision pending, unsettled since iter-29: whether data-provider run 201's "coverage refreshed" disclosure was truthful given a same-window `MemoryError` in that refresh.

## Next step

Run the next iteration at full depth. First, bound `stock_obs` (`forward_testing.py:988`) inside `compute_forward_aggregates` — the last unbounded accumulator and J-07's own named canonical producer — which requires deliberately re-pinning `_attribution_slices`'s frozen, test-asserted signature; record the warm's peak memory and margin in `reports/perf-budgets.md` (J-07 step 3, never done). Second, settle how the frontend is started before measuring page speed: either change `scripts/start-frontend.sh` to build and serve a production build, or amend `docs/goal.md` to say J-06's numbers are development-mode numbers. Third, once that's settled, run J-06's real-browser 11-page speed sweep and write the numbers into `reports/perf-budgets.md`. Fourth, track down the stray `/research/factor-lab?all=true` request missing its `/api` prefix that returns a 404 and puts an error badge on an otherwise clean page. Fifth, as a framework fix outside the journey loop: widen `merge_ui_test_results.py`'s row-matching regex to also catch `TC-`-prefixed rows, and have browser-qa verify each journey's screenshot is a genuinely fresh, distinct capture (an 11th recurrence of stale captures was found again this iteration). Carried unchanged: the boot warm-up failure and the whole-table price scan during data refresh; what the status badge should say if start-up work fails for good; the fresh-install database case; four pinned test monkeypatches in `test_forward_testing_serving_split.py`. For the owner, non-blocking: the health check still measures 0.128s against a 0.1s budget, and a newly-noted availability edge — a non-owner caller of the new single-flight guard can block a worker thread for up to 15 minutes if an owner computation genuinely wedges (bounded, not a regression, worth watching).

## Assumptions made

- iter-31 · goal-evaluator — Ambiguity: does an AG-8 finding close when its observed crash stops, or only when the unbounded growth term is fully removed? We chose: marked iter-29/a resolved (the crash symptom is gone, verified first-hand) and opened a separate new finding (iter-31/e) carrying the audit's measured residual, keeping the unresolved-finding count unchanged. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: does a backend-only memory fix on one lab page's read path, with no served value change, count as "touching the data path" for J-06's perf-budgets re-assert clause? We chose: counted it as touching the data path, so the missing re-assert is recorded as an unmet part of J-06 (consistent with iter-29's reading), though J-06 would be partial regardless because the real-browser TTI sweep is still the primary open gap. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: can a trusted-agent's prose report of a passing verification (the auditor's claimed J-06 replay execution) stand in for the artifact it claims to have produced, when no results file or screenshot could be found anywhere? We chose: scored J-06 partial with evidence_makeup true, treating the missing artifact as a capture gap rather than crediting the prose, per the no-citation rail. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: does a caught memory exhaustion that leaves the process serving and the UI showing a contained, honest error box count as AG-8's "critical" violation, or a minor open finding? We chose: kept the four AG-8 findings minor (not critical), since the page renders a calm bordered error box with nothing fabricated, the host was never under real memory pressure, and every unblock path is agent work. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: does J-07's acceptance clause "no unbounded whole-table ORM materialization on the warm or serving path" break the journey when a caught memory failure occurs inside its own named producer, or merely dent it? We chose: scored J-07 partial (not passing, not failing) since the service was never taken down but the clause is contradicted by live evidence inside its own function. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: does measuring-and-comparing page speed without recording it in `reports/perf-budgets.md` satisfy J-06's step 2? We chose: scored J-06 partial rather than passing — the step is literal, checkable, and unmet, and a budgets table that silently stops being re-asserted is how a never-regress budget quietly stops being enforced. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: is a caught, non-fatal memory exhaustion that leaves the service serving and the UI showing a contained error box the "critical" violation AG-8 forbids, or a minor open finding? We chose: recorded all four findings minor, not critical, so the verdict is CONTINUE rather than a REGRESSION halt — the page renders calmly with nothing fabricated and every unblock path is agent work. Reversible: yes
- iter-29 · goal-decomposer — Ambiguity: does reusing the Evidence page's existing silent-omission behavior already satisfy AG-8's "honest NA placeholder" for a new, distinct failure cause, or must the new cause be visually distinguishable? We chose: made it distinguishable with a new `expectations_status: "unavailable"` field and an inline note, following this session's established precedent of naming new states explicitly rather than collapsing them into an existing one. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: is J-07's "no unbounded whole-table ORM materialization" clause scoped to its own named producer, or to every warm and serving path in the backend? We chose: scored J-07 passing that iteration, reading the clause as scoped to its own named producer and serving path, while tracking the neighbouring `research.py` defect as a separate, already-open AG-8 finding. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-31.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-31-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-31-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-31-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-31-implementation-summary.md |
| User-visible changes | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-31-user-visible-changes.md |
| What to click | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-31-what-to-click.md |
| UI surface map | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-31-ui-surface-map.md |
| UI test plan | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-31-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-31-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-31-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-31-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-31-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-31/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
