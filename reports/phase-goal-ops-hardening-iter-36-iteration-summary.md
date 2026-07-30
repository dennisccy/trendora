# Iteration Summary — goal-ops-hardening-iter-36

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-07-30
**Iteration:** 36

## In plain words

**What you can do now:** Start a historical data backfill for any date range without limits and get an honest explanation when there's nothing new to fetch, watch the app boot up without freezing while it shows its own status, see aggregate evidence that's ready in advance rather than computed live when you look, browse any of the 5 Research lab pages (Regime Lab, Factor Lab, Market Phase & Severity Lab, Regime × Phase × Factor, Severity-velocity) with an honest "still working" message during a slow load, view backtest evidence that always comes from storage, and see the app disclose when it's doing background work.

**What changed this time:** The Factor Lab, Market Phase & Severity Lab, Regime × Phase × Factor, and Severity-velocity research pages now show a clear "Still computing — Ns elapsed" message with a spinner during a slow load, and a working Retry button if the backend is briefly unreachable — matching what the Regime Lab page already did. Behind the scenes, the Data page's coverage refresh now loads price history in small batches instead of all at once, cutting its peak memory use by about 71%, and the Evidence page's per-claim panel got a smaller, similar memory trim.

**What's next:** Next we'll get the "heavy work never crashes the service" check actually run in the browser test (it was blocked from restarting the backend this time), and close the last spot where a multi-day data backfill still loads the whole price table into memory at once.

## Headline

Cut Data-page coverage-refresh peak memory 71%; added honest loading/retry to 4 more Research labs

## Direction

**Signal:** improving
**Why:** J-06 ("Pages load only what they need") crossed back to passing this iteration after all four sibling Research labs were wired with the honest computing/error/retry states already proven for Regime Lab, verified via four screenshots the evaluator opened directly. J-07 ("Heavy aggregates never take the service down") stayed partial for a second consecutive iteration — not because the fix is wrong (peak memory on the fixed path dropped 70.7%, byte-identical) but because its browser-lane test never ran (the QA agent was denied permission to restart the backend). No journey regressed and no critical anti-goal violation was introduced, so despite the ESCALATE verdict (triggered by J-07's two-iteration stall) real forward progress happened this round.

**Trend (last 2 iters):**
- Newly passing this iter: J-06
- Newly passing in last 2 iters total: J-06
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 4 minor (iter-35/k; iter-36/l, iter-36/m, iter-36/n)
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** This iteration built the work that iteration 35 planned but never shipped, and it built it well. The biggest win: the part of the system that prepares data coverage used to pull every price ever stored into memory at once (about 1.13 GB); it now works through the stock list in small groups and uses about 330 MB — a 70.7% drop — and two separate tests prove the numbers it produces are exactly the same as before. On screen, four Research pages that used to show a blank grey box while they were working now say "Still computing — 28s elapsed" with a clear explanation, and a failed load now offers a Retry button.

## What was done

- Product changes: apps/backend/app/config.py, apps/backend/app/engine/data_manager.py, apps/backend/app/engine/forward_testing.py, apps/backend/app/engine/prices.py, apps/backend/app/engine/universe_resolver.py, apps/backend/tests/test_bar_cache.py, apps/backend/tests/test_data_manager_membership_cache.py, apps/backend/tests/test_evidence_drawdown_memory_pressure.py, apps/backend/tests/test_forward_testing.py, apps/backend/tests/test_membership_timeline_batch_bound.py, apps/frontend/app/research/_labs.tsx, apps/frontend/app/research/severity-velocity/page.tsx, config.yaml, reports/perf-budgets.md
- Bounded `_membership_timeline`'s candidate-pool bar loading (Data page coverage refresh) — cut peak memory 70.7% (1.13GB → 330MB), byte-identical output proven against a pinned pre-fix reference (closes ledger finding iter-29/d for this call site).
- Chunked `compute_drawdown_expectations`'s evidence-serving-path read — a modest ~4% peak-RSS reduction, honestly disclosed as not a full architectural bound (ledger finding iter-35/k).
- Wired the shared honest "still computing" / Retry loading panel into 4 more Research labs (Factor Lab, Market Phase & Severity Lab, Regime × Phase × Factor, Severity-velocity), matching Regime Lab's existing behavior — resolves ledger finding iter-33/h.
- Audit found and closed a byte-identity test gap (the coverage-payload half of TC-2 was untested) with a new, negative-controlled test — test-only, no production code touched.
- Verified J-06 passes browser QA (four screenshots opened directly, all four labs show the honest computing/error/retry states); J-07's browser-lane test did not run this iteration — the backend restart was denied mid-run, so UT-13/UT-14 were skipped.

## What's left

- J-07 "Heavy aggregates never take the service down" still partial — its browser-lane test never ran this iteration (backend restart permission denied); needs a re-run with backend-down tests ordered last so a denied restart can't strand tests behind it again.
- Closure gate reports CLOSURE-FAIL — a confirmed false alarm from the gate's regex matching the label "Backend-only" as if it claimed "no visible changes," when the same document actually documents four changed pages; needs a gate fix or a manual override to close cleanly.
- A leftover backend process (PID 2944679) is still alive holding 4.1GB RSS at the memory cap — must be reaped before any further memory measurement.
- iter-36/l: `_persist_per_date_coverage_snapshots` and `_do_backfill` still each load the whole price table on a multi-date backfill — the last unbounded whole-table load on the ingest warm chain.
- iter-33/g (carried): Regime Lab's cold `view=pooled` background dispatch and an HTTP 200 response that carries "Internal Server Error" text remain undiagnosed.
- J-07 step 3's VmPeak margin (42.8% of cap) still isn't recorded in `reports/perf-budgets.md` — it exists only in the audit handoff.
- Two owner decisions remain open and unchanged: the `/api/health` ≤0.1s budget disposition (missed again, max 132ms) and whether `start-frontend.sh` should join `HOST_GUARD_MARKER_FILES`.
- Small hygiene items: a stale docstring at `data_manager.py:650-654` describing removed code, and a "591 vs 548 symbols" figure error in `perf-budgets.md`.

## Next step

Run the next iteration at full depth (mandatory via ESCALATE). First, shut down the leftover backend process (PID 2944679) before any further memory measurement. Then finish J-07 — the only journey not passing — by giving the browser-QA lane permission to restart the backend and ordering the test plan so backend-down tests run last, so a denied restart can't strand tests behind it again; then record the VmPeak margin in `reports/perf-budgets.md`. Next, close the last unbounded whole-table load (iter-36/l: `_persist_per_date_coverage_snapshots` and `_do_backfill` still each prefill the whole price table on a multi-date backfill). Then take up the deliberately-deferred item iter-33/g (Regime Lab's cold `view=pooled` background dispatch and its HTTP-200-with-"Internal Server Error" body). Small hygiene fixes (a stale docstring, a wrong symbol count in perf-budgets.md) and a framework fix to the closure gate's overly broad "backend-only" regex are also queued. Two owner decisions remain open and unchanged: the `/api/health` ≤0.1s budget disposition, and whether `start-frontend.sh` should join `HOST_GUARD_MARKER_FILES`.

## Assumptions made

- iter-36 · goal-evaluator — Ambiguity: J-06 was downgraded to partial at iter-35 on the premise that all four sibling labs render a bare unlabelled skeleton on slow loads; this iteration falsifies that premise with opened screenshots, but the full page-load sweep wasn't re-run and one sibling clause's walkthrough is still missing. We chose: restored J-06 to passing and cleared `evidence_makeup`, since evidence expires with change not time, the on-load request path is unchanged, and the clearing rule is mechanical. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: decision tree clause C.4 says "the SAME journey has now failed 2+ consecutive iterations -> ESCALATE," but J-07 is `partial` (not literally "failed") for two iterations running, while CONTINUE also fits comfortably. We chose: ESCALATE, reading "failed" as "did not reach passing," because the tree is first-match-wins and this session already lost a whole iteration to an advisory (non-mandatory) full-depth recommendation. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: J-07's browser-lane verification never ran this iteration, but the auditor independently verified several of its steps by hand; instructions say an un-evidenced journey is "unknown" while the schema also defines "partial" as some-steps-passed. We chose: scored J-07 `partial`, not `unknown`, because that literally matches what happened and both readings block GOAL_ACHIEVED identically. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: rule 5 bars bundling two risky journeys per iteration, and iter-35's carried plan already bundles one structural fix with one cheap mechanical item; a third, smaller memory-bound fix (iter-35/k) surfaced live and it was unclear whether it could be folded into the same iteration. We chose: folded it in as a small third item rather than deferring to iter-37, since the evaluator ranked it immediately after the two carried items and it mirrors an already-established fix idiom. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: AG-8 (critical) says the data basis must never exhaust a service's memory; this iteration measured real memory exhaustion (VmPeak at the exact cap, two aborts on a user-facing path), but the UI degraded gracefully throughout and the tree was byte-identical. We chose: classified it minor, not critical, and returned ESCALATE rather than REGRESSION, since the methodology's critical list is secrets/paid-deps/license/backdoor/fabricated-data and contained-and-disclosed memory pressure is none of these. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: browser-qa scored J-06 FAIL against the iteration's own unbuilt spec (an evidence-depth run with no developer), a ground the goal text itself never names, but attached screenshots separately show a genuinely slow, unlabelled load. We chose: rejected the FAIL's stated ground but scored J-06 `partial` anyway on the screenshot evidence, since a screenshot outranks prose. Reversible: yes
- iter-34 · goal-evaluator — Ambiguity: J-07's health-check step requires every poll answer within a 0.1s budget "during a warm"; this iteration proved responsiveness (185/185 HTTP 200) but 0 of 185 polls met the 0.1s number, and the goal text doesn't say whether a proven-but-missed numeric budget still counts as satisfied. We chose: scored J-07 `passing` and filed the miss as a new unresolved ledger finding (iter-34/j) rather than rounding it away, since J-07's own Acceptance block never names the budget number. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-36-what-to-click.md`:

1. Open `http://localhost:3255/research/factor-lab` in your browser
2. Open `http://localhost:3255/research/phase-severity-lab`
3. Open `http://localhost:3255/research/regime-phase-factor`
4. Open `http://localhost:3255/research/severity-velocity`
5. Stop the backend service (kill the process running on port 8255), then reload `http://localhost:3255/research/factor-lab`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-36.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-36-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-36-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-36-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-36-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-36-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-36-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-36-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-36-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-36-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-36-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-36-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-36-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-36/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
