# Iteration Summary — goal-mcp-loop-iter-33

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 33

## In plain words

**What you can do now:** You can scan a leaderboard of hundreds of stocks where every score is honestly labeled as either backed by tested evidence or "not yet proven," open the full evidence behind any score, and browse a complete, auditable record of every trading idea the system has tested — moving-average, breakout, multi-factor, and relative-strength ideas, all still honestly unproven on the current data. You can view up to thirty years of price history and market-index context for any stock, and the page that manages your data connections stays fast even on its heaviest job. The system refuses to test a new idea unless it was registered first, lets you browse a graveyard of every rejected idea with a working link back to its registration, and shows at a glance how much of the platform's testing budget has been used.

**What changed this time:** Every page in the app now shows a small status strip near the top telling you, at a glance, whether today's information is safe to rely on — a quiet green line on a normal day, or an unmissable colored banner naming the exact problem in plain English (for example, data going stale, or a record-keeping file going missing) when something's wrong. It's the same single answer everywhere, so no page can ever quietly disagree with another.

**What's next:** Next, the team needs to finish double-checking that this new status strip didn't disturb a handful of older pages, then formally wrap up this round before moving on to a live-data watchdog or a self-check on the testing process itself.

## Headline

Daily preflight verdict banner (GO/DEGRADED/NO-GO) ships on every page, computed once in the backend

## Direction

**Signal:** holding
**Why:** This iteration's formal Verdict is FAIL only because phase-closure-auditor caught a process gap, not a product regression: J-20 (the preflight GO/DEGRADED/NO-GO banner) shipped cleanly through review, QA (20/20 browser tests), and ux-regression, but the DoD-mandated deterministic replay for six required-still-passing journeys (J-01, J-02, J-04, J-05, J-13, J-18) was never actually run — QA and ux-regression both pointed to a "next pipeline step" that doesn't exist for a Depth:full iteration. Journey-history still shows J-01..J-19 passing with zero regressions and zero anti-goal violations, and the fix is a few minutes of replaying six existing golden scripts, so direction reads holding rather than regressing.

**Trend (last 5 iters):**
- Newly passing this iter: none (closure gate blocked before the goal-evaluator could run; J-20 remains unconfirmed)
- Newly passing in last 5 iters total: J-02, J-06, J-07, J-08, J-09, J-17, J-18, J-19
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** No goal-evaluator has run for iter-33 yet (the closure gate failed first); most recent verified reasoning is from iter-32: "iter-32 is a clean, textbook additive read-only iteration that shipped J-17 AND closed the iter-31 J-19 partial in one pass, and I verified every status change against artifacts I personally opened, not the handoffs. THE REGRESSION PROOF (iter-9 lesson, spec NOTES): the iter-diff is 10 files, entirely additive — 6 new files (budget_accounting.py, api/budget.py, budget/page.tsx, lib/budget.ts, 2 tests) + 4 additive edits (main.py router include, research/page.tsx third card, lib/api.ts fetchBudget, README bullet); certified-claims.jsonl / staging-ledger.jsonl / pre-registrations.jsonl + referee.py/ledger.py/online_fdr.py/evidence.py/tools.py/scoring.py + registry/page.tsx are ALL git-diff EMPTY vs HEAD (canonical divisor stays 8), so there is no regression mechanism for J-01..J-16/J-18."

## What was done

- Shipped J-20: one canonical daily preflight verdict (`GO`/`DEGRADED`/`NO-GO` + plain-language reasons), computed once by a new `compute_preflight` composer and rendered as a single layout-level banner mounted once in `app/layout.tsx`, appearing on all 27 routes.
- Added the verdict as an additive `preflight` field on the existing `GET /api/health` response; all pre-existing fields (state/warmup) stay byte-identical.
- Made the DEGRADED-vs-NO-GO severity mapping and the freshness threshold config-driven (`ReadinessCfg` / new `readiness:` block) instead of hardcoded.
- Added an append-only verdict-transition history log that writes only when the verdict actually changes.
- Investigated and closed the iter-32 J-11 replay gap — confirmed J-11 passes live via a dedicated `demo_runner.py` verify run.
- Added a per-input-combination backend fixture-matrix test (8 rows) plus config-wiring, byte-identity, and error-case tests for the new composer.
- Verified 1 target journey (J-20) passes browser QA: 20/20 UI test cases across all 5 required decision surfaces in all three verdict states, single-source confirmed, zero regressions to the readiness badge, leaderboard badges, evidence ledger, or nav.

## What's left

- Required-still-passing deterministic replay for J-01, J-02, J-04, J-05, J-13, J-18 was never executed this iteration (only J-11 got a genuine re-verification) — phase-closure-auditor returned CLOSURE-FAIL on this gap, and QA/ux-regression's claim that it would run "in the next phase step" does not apply to a Depth:full iteration.
- J-20 cannot be scored `passing` in the journey ledger until the replay above runs clean and phase-closure-auditor is re-run — the goal-evaluator has not yet executed for this iteration.
- The banner shows only the flattened reasons text; the backend's per-check breakdown (servability/freshness/integrity) and the freshness reference date aren't shown anywhere in the UI yet (by design, deferred).
- The new verdict-change history log has no page to view it yet (feeds a future "digest" journey).
- Three future inputs that would enrich the verdict — an anomaly detector, a live-vs-seed drift check (J-21), and a "replay as of a past date" check — are not built yet.
- 18 of the 25 new backend tests (the loaded_engine-dependent correctness matrix) still haven't completed a formal in-pipeline pytest run (the auditor independently reproduced the same assertions outside pytest and judges the risk closed, but the canonical run itself remains outstanding).
- Six Must-have journeys remain fully unbuilt: J-21 (live-data drift), J-22 (certifier self-audit), J-23 (watchlist concentration), J-24 (per-stock risk-budget card), J-25 (drawdown-expectations panel).

## Next step

Run the deterministic replay against the six golden scripts that already exist for J-01, J-02, J-04, J-05, J-13, and J-18 (`demo_runner.py --mode verify` against `runs/goal-session-mcp-loop/journey-scripts/`), fold the results into the browser-QA evidence, correct the QA/ux-regression reports' incorrect "runs in the next phase step" claim (that replay lane only exists for Depth:lean iterations), and re-run phase-closure-auditor. This is expected to be a quick, low-risk fix — none of the six journeys' own files were touched this iteration — after which the goal-evaluator can run and score J-20.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-33-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Look directly below the header bar (below the "Research-only · decision support · no orders" text, underneath the top row)
3. Click "Stocks" in the left sidebar
4. Click "Watchlist" in the left sidebar, then click "Evidence" in the left sidebar
5. Look at the top-right of the header bar (to the right of the date control)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-33.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-33-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-33-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-33-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-33-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-33-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-33-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-33-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-33-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-33-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-33-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-33-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-33-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
