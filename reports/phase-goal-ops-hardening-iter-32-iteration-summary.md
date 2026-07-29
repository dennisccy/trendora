# Iteration Summary — goal-ops-hardening-iter-32

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-29
**Iteration:** 32

## In plain words

**What you can do now:** Back-fill any historical date range — including long spans — and get an honest explanation when there's nothing new to fetch. Watch a status badge that stays truthful while the app starts up, updates, or does background work. Open the Backtest page and get results instantly because they were computed ahead of time, never while you wait. See a clear signal whenever the system is busy working in the background, and trust that it never quietly recomputes evidence live.

**What changed this time:** The calculation behind the Backtest page's numbers — the one that had already crashed the server twice before — was rebuilt so it no longer needs to hold roughly 800,000 individual data points in memory at once. It now keeps only small running totals instead. Nothing on the Backtest page looks different; the same numbers appear as before. What changed is under the hood: a live test against the full real history ran the calculation twice in a row with zero memory errors and well over half the memory ceiling still free, and the app's memory-safety record now got written down for the first time in 32 rounds of this work.

**What's next:** Next, the team needs to settle whether the "production" launch script actually starts a production version of the site, because that decision is blocking an honest page-speed measurement. After that, they'll finish the two small checks still owed on the "heavy background work never takes the site down" promise — timing the health check against its speed limit, and running a deliberate low-memory drill.

## Headline

Internal reliability fix: removed the last crash-risk memory accumulator in Backtest's evidence calculation

## Direction

**Signal:** holding
**Why:** J-07's target work landed cleanly this iteration — `stock_obs` is now fully bounded (not just shrunk), a live full-deep-basis warm showed zero MemoryError, and its VmPeak margin was finally recorded in `reports/perf-budgets.md` for the first time in 32 iterations — closing the session's oldest anti-goal finding (iter-29/c). But J-07 stays `partial` because two of its own four acceptance steps (the health-check latency record and the induced-pressure drill) remain unmeasured, and J-06 stays `partial`, carried unchanged since iter-28. No journey crossed to fully `passing`; the six required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) simply re-verified. This is the fourth consecutive iteration with no journey-status change, but each of those iterations closed a distinct, real gap rather than spinning in place, so direction holds steady rather than stalling.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total (iters 30-32): none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 2 new (both minor: iter-31/e Factor-Lab constant-factor residual, iter-32/f `run_rows` watch item); 2 resolved (iter-31 closed iter-29/a; iter-32 closed iter-29/c)
- Iters with no journey state change: 3 of last 3

**Latest evaluator reasoning:** "This iteration fixed the biggest memory problem left in the app, and the fix is real. The part of the code that builds the backtest evidence used to hold one record in memory for every single observation — about 800,000 of them at once. It now keeps only small running totals. Measured on the real data, memory use dropped from 981 MB to 170 MB, the answers it produces are identical byte-for-byte, and the app stayed healthy through two full live rebuilds."

## What was done

- Product changes: apps/backend/app/engine/forward_testing.py, apps/backend/tests/test_forward_testing.py, apps/backend/tests/test_forward_testing_aggregates_streaming.py, reports/perf-budgets.md
- Eliminated `stock_obs`, the last unbounded per-observation accumulator inside `compute_forward_aggregates`, replacing it with bounded per-group/per-run/per-ticker accumulators (`_ExactMeanAcc`, `_GroupAcc`, `_ControlGroupBuilder`, `_AttributionAccumulator`) fed incrementally inside the existing per-chunk loop.
- Ran a live full-deep-basis warm across all 5 horizons, twice: zero `MemoryError`, `VmPeak` flat at 2,691,600 kB / 57.2% headroom under the 6144 MB cap, 77/77 health polls HTTP 200 — recorded in `reports/perf-budgets.md` (J-07 step 3, never done across the prior 31 iterations).
- Extended the byte-identity reference oracle to cover the restructuring and updated all nine `_attribution_slices` unit tests to the deliberately-lifted `(acc, cfg)` signature; 143 backend tests passed.
- Closed the session's oldest AG-8 finding (iter-29/c, `stock_obs`); the auditor independently re-derived the bound at live scale (981 MB → 170 MB peak RSS, SHA-256-identical payload) and fixed two verification defects (a test that measured the spec's exempt term, and an oracle that compared attribution against itself).
- Verified 7/7 journeys pass browser QA (the six required-still-passing journeys plus J-07's target check); J-01, J-03, J-04, J-05, J-08, J-09 all re-verified `passing` via deterministic golden replay.

## What's left

- Journey J-06 (Pages load only what they need) partial — the real-browser 11-page time-to-interactive sweep still hasn't run in 32 iterations, blocked on a launcher decision: `scripts/start-frontend.sh` execs `next dev`, not a production build.
- Journey J-07 (Heavy aggregates never take the service down) partial — step 2's health-check latency was never recorded against its ≤0.1s budget; step 4's induced memory-pressure drill has never been run.
- Carried anti-goal finding (iter-29/d, minor): `prices.py:141`'s whole-table `daily_prices` prefill inside the ingest-finalize warm — now the one thing keeping J-07's "no unbounded whole-table ORM materialization on the warm path" clause from reading fully true.
- Carried anti-goal finding (iter-29/b, minor): boot warm-up `MemoryError` at `warmup.py:194` — the wording the status badge should show after a permanently failed warm-up is still undecided, three iterations on.
- Carried anti-goal finding (iter-31/e, minor): the Factor-Lab-all `pools[h]` fix is a 2.63x constant-factor reduction, not an asymptotic bound.
- New WATCH ITEM (iter-32/f, minor, explicitly not a blocker): a `run_rows` ORM list at `forward_testing.py:1195` grows proportionally with run count; deliberately deferred, not to become a future iteration's own goal.
- Framework bug flagged for the fourth consecutive iteration: `merge_ui_test_results.py`'s `_ROW_RE` only matches `UT-` ids and can silently drop `TC-`-prefixed FAIL rows — must be fixed before any run that declares the goal achieved.
- Owner decision pending: `GET /api/health` measures ~0.128s against its written ≤0.1s budget; until amended, rescoped, or accepted as a recorded WARN, J-06 step 2 and J-07 step 2 can never both read true.

## Next step

Run the next iteration at full depth, with J-06 first. Its blocking decision must be made before any measurement: either change `scripts/start-frontend.sh` to build-and-serve a real production build, or amend `docs/goal.md` to say J-06's numbers are development-mode numbers — then run the real-browser 11-page sweep, write the timings into `reports/perf-budgets.md`, and write the code-level on-load audit into the dev handoff. Second, close J-07 with two contained items: record `GET /api/health`'s latency through a live warm and state plainly whether it's inside budget, and run the induced-memory-pressure drill that has been deferred since iter-14. As ride-alongs only (never an iteration's own goal): add both crash-free-warm and healthy-health sequences to the demo as `[NEW]` steps, and get a J-07 capture that shows the "Forward-tested evidence" tables instead of the top of the page. As a framework fix outside the journey loop, flagged for the fourth consecutive iteration: widen `merge_ui_test_results.py`'s `_ROW_RE` to catch `TC-`-prefixed rows too. For the owner, non-blocking but load-bearing on two journeys: `GET /api/health` at 0.128s vs its ≤0.1s budget needs to be amended, rescoped, or accepted as a recorded WARN.

## Assumptions made

- iter-32 · goal-evaluator — Ambiguity: does a run-count-proportional ORM materialization (`run_rows`, small today, pre-existing and accepted at iter-14) count as an AG-8 violation. We chose: recorded it as a new minor finding (iter-32/f) explicitly labelled a WATCH ITEM rather than a blocker, so it cannot become the next iteration's own goal. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: does J-07 pass when its headline promise is now strongly proven but two of its own four enumerated steps were never executed. We chose: scored J-07 `partial`, not `passing` — the two steps are literal, checkable, and unexecuted, and this session has twice had a GOAL_ACHIEVED rejected for accepting a substitute artifact. Reversible: yes
- iter-32 · goal-decomposer — Ambiguity: what "bounded accumulator" means for a slice (`distribution`) whose exact median/dispersion computation fundamentally requires O(N) access to the full value multiset. We chose: required every OTHER consumer to be bounded by group/run/ticker cardinality, while allowing `distribution` to keep one list of bare floats only — the one mathematically-forced exception. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: does a backend-only memory fix on one lab page's read path, with no served value change, count as "touching the data path" for J-06's perf-budgets re-assert clause. We chose: counted it as touching the data path, so the missing re-assert stays recorded as an unmet part of J-06, consistent with iter-29's reading. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: does an AG-8 finding close when its observed crash stops, or only when the unbounded growth term is fully removed. We chose: marked iter-29/a resolved (the crash symptom is gone, verified first-hand) and opened a separate new finding (iter-31/e) carrying the audit's measured residual, keeping the unresolved-finding count unchanged. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: can a trusted agent's prose report of a passing verification stand in for the artifact it claims to have produced, when no results file or screenshot could be found anywhere. We chose: scored J-06 `partial` with `evidence_makeup: true`, treating the missing artifact as a capture gap rather than crediting the prose. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: does a caught memory exhaustion that leaves the process serving and the UI showing a contained, honest error box count as AG-8's "critical" violation, or a minor open finding. We chose: kept the four AG-8 findings `minor`, not critical — the page renders a calm bordered error box with nothing fabricated, the host was never under real memory pressure, and every unblock path is agent work. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: does J-07's acceptance clause break the journey when a caught memory failure occurs inside its own named producer, or merely dent it. We chose: scored J-07 `partial` — the service was never taken down, but the clause is contradicted by live evidence inside its own function. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: does measuring-and-comparing page speed without recording it in `reports/perf-budgets.md` satisfy J-06's step 2. We chose: scored J-06 `partial` rather than `passing` — the step is literal, checkable, and unmet, and a budgets table that silently stops being re-asserted is how a never-regress budget quietly stops being enforced. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-32.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-32-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-32-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-32-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-32-implementation-summary.md |
| User-visible changes | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-32-user-visible-changes.md |
| What to click | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-32-what-to-click.md |
| UI surface map | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-32-ui-surface-map.md |
| UI test plan | N/A (backend-only) | reports/phase-goal-ops-hardening-iter-32-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-32-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-32-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-32-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-32-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-32/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
