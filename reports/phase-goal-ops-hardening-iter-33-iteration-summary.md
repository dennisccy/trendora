# Iteration Summary — goal-ops-hardening-iter-33

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-29
**Iteration:** 33

## In plain words

**What you can do now:** Back-fill any historical date range, with an honest explanation whenever there's no new work to do and no size limit on the range. See a truthful status badge the whole time the app is starting up, updating, or recovering from a crash. Browse stock rankings, sector and theme views, and evidence-backed scores, all served from calculations already done in advance rather than computed while you wait. Open the Backtest page and always get results served instantly from storage, never a live recomputation. See when the app is doing background work through a status badge and a Data Manager panel. Every main page now loads quickly under genuine production conditions, and the Research → Regime Lab page gives an honest "still working" message instead of freezing during its occasional slow first load.

**What changed this time:** The script that starts the website in "production mode" for speed testing had actually been quietly starting it in slower developer mode this entire project — that's now genuinely fixed, and for the first time the team measured how fast all 11 main pages really load (well under budget on every one). That same measurement caught a real problem on the Research → Regime Lab page: it could sit on a blank, unlabelled loading spinner for up to a minute and a half on its first slow read. The page now shows a plain "Still computing — Ns elapsed" message with an explanation, and offers a Retry button if the load fails.

**What's next:** Next, the team will finish proving the app never goes down under heavy background work — timing how fast the health check answers while the app is busy, and running a deliberate test of what happens if the app runs low on memory mid-calculation.

## Headline

The frontend launcher now actually serves production mode.

## Direction

**Signal:** improving
**Why:** J-06 ("Pages load only what they need") newly crossed to passing this iteration after the frontend launcher's long-standing dev/prod bug was fixed and the real-browser 11-page TTI sweep finally ran for the first time in 33 iterations. All six required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) re-verified clean with zero FAIL rows, no regressions occurred, and a report-merging bug that risked laundering a real failure into a fake "pass" was fixed and evidence-checked — a clear net gain even though J-07 remains the one open journey and three new minor anti-goal findings were logged.

**Trend (last 3 iters):**
- Newly passing this iter: J-06
- Newly passing in last 3 iters total: J-06 (none in iter-31 or iter-32)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 5 minor (iter-31/e; iter-32/f; iter-33/g, iter-33/h, iter-33/i)
- Iters with no journey state change: 2 of last 3

**Latest evaluator reasoning:** A journey moved forward for the first time in five iterations. J-06 "Pages load only what they need" is now passing. The launcher script that starts the web app had always started it in "development" mode while every document called it "production" mode; this iteration fixed that, and then measured all 11 pages in a real browser.

## What was done

- Product changes: incredible_auto_dev/scripts/start-frontend.sh, incredible_auto_dev/scripts/measure-perf.sh, incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py, apps/backend/tests/test_start_frontend_script.py, apps/frontend/lib/lab-load-panel.ts, apps/frontend/lib/lab-load-panel.test.ts, apps/frontend/app/research/_labs.tsx
- Rewrote `start-frontend.sh` to build-if-stale then genuinely `exec next start` (never falls back to `next dev`); exits non-zero with the real build error on a genuine failure.
- Ran the real-browser 11-page time-to-interactive + on-load-latency sweep against the fixed prod-mode frontend and recorded it in `reports/perf-budgets.md`, closing J-06's core measurement gap for the first time in 33 iterations.
- Fixed a P1 UX defect QA found: Research → Regime Lab's cold-cache load now shows a labelled "Still computing — Ns elapsed" notice and a Retry control instead of an indefinite unlabelled skeleton (`lab-load-panel.ts`, `_labs.tsx`).
- Widened `merge_ui_test_results.py`'s row regex so a `TC-`-prefixed headline FAIL from either input file can no longer be silently laundered into a merged PASS — flagged by four consecutive evaluators.
- Fixed launcher-smoke-test flakiness (timeout too tight, leftover residue from a hard-killed run) in `test_start_frontend_script.py`.
- Re-verified 6 required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09) via deterministic golden replay — zero FAIL rows.
- Verified 7 target journey(s) pass browser QA (6 replay rows + 1 LLM-verified row for J-06).

## What's left

- Journey J-07 (Heavy aggregates never take the service down) stays partial — 2 of its 4 steps unverified: the `/api/health` latency budget during a live warm-up, and the induced-memory-pressure abort drill (deferred since iteration 14).
- Regime Lab's cold compute is still genuinely 60-90s on first read per dataset version; the wait is now honest but not faster, and one observed raw "Internal Server Error" response during that cold path is still undiagnosed.
- The four sibling research labs (Phase-Severity Lab, Regime-Phase-Factor, Factor Lab, Severity-Velocity) still show a bare unlabelled loading skeleton with no Retry — the same shape that just failed as a P1 on Regime Lab.
- Owner decision needed: should `start-frontend.sh` join the host-guard marker list now that it triggers a full production build inside automated lanes?
- Owner decision on the `/api/health` ≤0.1s budget: now measured 93.4ms at rest (inside budget) but 97.8-207.7ms under concurrent browser load (recorded as an honest WARN).
- UX regression review flagged non-blocking pipeline-artifact staleness: some UI-impact documents and the demo recording were captured before this iteration's fix landed and don't fully reflect the final shipped state.

## Next step

Target J-07 "Heavy aggregates never take the service down" and finish it: record how long the health check takes during a heavy warm-up and state plainly whether it is inside the written 0.1-second budget (already partly measured this iteration: 93.4ms at rest — inside; 97.8–207.7ms under concurrent load — WARN), then run the induced-memory-pressure drill (J-07 step 4, postponed since iteration 14), launched only through `scripts/start-backend.sh` so the host caps apply. What should happen next, in one sentence: approve one more full-depth iteration that finishes J-07 by recording the health-check timing and running the memory-pressure drill through the capped launch script — after that, all eight journeys are candidates for a final achievement check.

## Assumptions made

- iter-33 · goal-evaluator — Ambiguity: AG-10 requires heavy compute to launch only via project scripts applying host caps; `start-frontend.sh` now runs a full multi-worker `next build` from automated lanes but isn't a host-guard marker file, and a production frontend build isn't one of AG-10's enumerated categories. We chose: recorded it as a new minor, unresolved finding (iter-33/i) and an explicit owner decision item, not a critical violation or regression — both host-guard marker files are byte-unchanged, caps moved the safe direction, and the build measurably inherits the CPU affinity mask today. Reversible: yes
- iter-33 · goal-evaluator — Ambiguity: J-06's three steps are all executed for the first time, but the acceptance's `[NEW]`-flagged walkthrough is missing, the health-check reading is over budget under load, and the honest-status clause for Regime Lab's cold path is proven by a simulated (not live) reproduction. We chose: scored J-06 `passing` with `evidence_makeup: true` — a missing/mis-cropped walkthrough is a capture defect that never downgrades status, the honest-status clause names states (not a live-reproduction requirement) and two real screenshots show exactly those states, and the health budget now has an at-rest reading inside it plus an honestly-disclosed WARN under load. Reversible: yes
- iter-33 · goal-decomposer — Ambiguity: J-06 step 1 requires a real-browser TTI sweep in prod mode, but `start-frontend.sh` has execed `next dev` for the whole session; `docs/goal.md` offers two remedies (fix the launcher, or amend the goal wording) without picking one. We chose: fix `start-frontend.sh` to genuinely run `next build` + `next start`, not amend `docs/goal.md` — J-06's own step-1 text already calls this script "prod mode" and `measure-perf.sh`'s own header independently calls it "PROD MODE ONLY", both pointing at the script being the bug. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: a developer-disclosed run-count-proportional ORM materialization (`run_rows`, `forward_testing.py:1195`) sits on the same path AG-8 names, but it's small today and was accepted as "bounded, small" at iter-14. We chose: recorded it as a new minor watch item (iter-32/f) without blocking on it or making it the next iteration's goal, keeping the fact checkable without moving the goalposts on a pre-existing, explicitly-accepted line. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: J-07's named blocker (`stock_obs`) is closed with strong first-hand evidence, but two of J-07's own four steps (health-latency budget, induced-memory-pressure drill) remain unexecuted. We chose: scored J-07 `partial`, not `passing` — both steps are literal, checkable, and named verbatim in the Acceptance block, and this session has twice had a GOAL_ACHIEVED rejected at the second-key confirm for accepting a substitute artifact. Reversible: yes
- iter-32 · goal-decomposer — Ambiguity: J-07's acceptance requires bounded accumulators, but one downstream consumer (`distribution`'s median/dispersion) mathematically requires O(N) storage — no exact streaming median exists with O(1) memory. We chose: required every OTHER consumer of `stock_obs` to be bounded by group/run/ticker cardinality, while conceding `distribution` may keep one list of bare floats (an order-of-magnitude size cut) as the one place a true asymptotic bound isn't achievable without trading away exact-median correctness. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: J-06's acceptance requires re-asserting perf budgets whenever a change "touches the data path," but this iteration's memory fix only touched one research lab page's read path with a byte-identical served payload, and J-06's own golden script visits a different lab. We chose: counted it as touching the data path, so the missing perf-budgets re-assert is recorded as an unmet part of J-06, consistent with the iter-29 evaluator's reading of the same clause — though it wasn't the deciding factor since the real-browser TTI sweep was still J-06's primary open gap regardless. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: an AG-8 finding (iter-29/a, a live MemoryError crash on every Factor Lab visit) had its observed symptom fixed, but the fix was measured as a constant-factor reduction, not an asymptotic bound, so the same crash class returns at ~2.5-3x today's data scale. We chose: marked iter-29/a `resolved: true` (the recorded symptom is gone) and opened a separate new record (iter-31/e, minor) carrying the measured residual, rather than leaving a fixed crash permanently "open" or hiding the residual inside a resolved record. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: the iter-30 audit reported executing and passing a J-06 replay, but no results artifact or screenshot exists anywhere on disk for it, and `docs/goal.md` doesn't say whether a trusted agent's prose report of a passing verification can stand in for the missing artifact. We chose: scored J-06 `partial` with `evidence_makeup: true`, treating the missing artifact as a capture gap rather than crediting the prose, per the no-citation rail and because this session has twice had a GOAL_ACHIEVED rejected at the second-key confirm for accepting a substitute artifact. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-33-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Open your browser's DevTools console (press F12, then click the "Console" tab) and look at the bottom corners of the page
3. Click "Stocks" in the left sidebar
4. Type "AAPL" into the search box at the top of the leaderboard, then click the "AAPL" row
5. Click "Backtest" in the left sidebar

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-33.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-33-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-33-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-33-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-33-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-33-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-33-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-33-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-33-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-33-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-33-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-33-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-33-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-33/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
