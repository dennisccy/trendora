# Iteration Summary — goal-mcp-loop-iter-18

**Verdict:** REGRESSION
**Iteration type:** goal-full
**Date:** 2026-07-07
**Iteration:** 18

## In plain words

**What you can do now:** Browse a leaderboard of several hundred stocks (up from about 120) with up to 30 years of price history behind each one, switch any stock's chart between a short recent view and its full history, and check an honest "not yet proven" or "proven" status on every score and every past trading idea the team has tested. You can add many more stocks to a watchlist than before, and none of it requires logging in. One current caution: sorting the stock list by the "Sector" column crashes the page — the team is fixing this now.

**What changed this time:** The product switched over to real price history stretching back up to 30 years (previously about 5), now covering many more stocks. Because the underlying data changed, every previously "proven" trading idea was honestly re-checked against the deeper history, and none of them held up — so every score across the whole product now reads "not yet proven," which is the correct, honest result of that re-check, not a mistake. The same change also introduced a real problem: clicking the "Sector" column heading on the stock list now crashes the whole page for many of the newly added companies that don't have a sector on file yet. That crash was caught during testing and is being treated as the top priority to fix.

**What's next:** Next, the team will fix the Sector-sort crash, finish verifying a couple of pages that weren't fully re-checked after the data change, and make sure the status reports match reality before calling this round done.

## Headline

Atomic 30-year price-basis swap landed cleanly; sorting the stock list by Sector now crashes the page

## Direction

**Signal:** regressing
**Why:** This iteration landed the atomic 30-year data-basis swap and the sanctioned all-FAIL evidence-ledger reset cleanly (J-10 and J-11 newly passing; J-06..J-09 correctly held partial under the data-basis provision, not a regression), but a prior-passing journey broke: J-01's `/stocks` leaderboard — passing since iteration 2 — now crashes to a blank page when a user sorts by the Sector column, confirmed independently by both the ux-regression review and the closure audit. J-12 also stayed partial (its membership-timeline verification never finished) and the canonical browser-QA lane crashed before completing the required anti-goal language sweep. A prior-passing journey turning failing forces a REGRESSION verdict and a halt for human review.

**Trend (last 5 iters):**
- Newly passing this iter: J-10, J-11
- Newly passing in last 5 iters total: J-08 (iter-14), J-09 (iter-15), J-10 (iter-18), J-11 (iter-18)
- Regressions in last 5 iters: J-01 (iter-18)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5

**Latest evaluator reasoning:** "The atomic 30-year / 548-pool basis swap and the ONE sanctioned all-FAIL ledger reset landed correctly and honestly — I read both ledgers directly (7 canonical + 7 staging rows, all FAIL, register 2026-07-03, Bonferroni divisors 1..7 preserved, ZERO retired values), confirmed the shared certification engine is byte-untouched, and verified proven_signals={} forces every badge product-wide to 'Not yet proven.' That half is the system working as goal.md sanctions. But this iteration also shipped a confirmed, unfixed, reproducible full-page crash: /stocks — the product's most-prominent page — crashes to a blank 'Application error' (all navigation wiped) the moment a user sorts by the 'Sector' column, because the broadened pool now returns sector:null for ~78% of rows into an unguarded comparator (stocks/page.tsx:93) with no error boundary."

## What was done

- Landed the atomic 30-year / 548-name price-basis swap: charts and backtests now reach back toward 1996, honestly bounded per stock (no invented history for recent IPOs)
- Added a "Recent / Full history" chart-range toggle to Stock Detail with an honest depth-disclosure caption
- Regenerated both evidence ledgers from scratch on the new basis: all seven previously-certified claims honestly re-tested and re-labeled FAIL / "Not yet proven" (sanctioned reset — zero retried edges, zero hand-authored rows)
- Added a recency/staleness exclusion gate to the point-in-time universe (a new "stale series" reason surfaced on Methodology and Data diagnostics)
- Broadened the point-in-time candidate universe from ~122 to ~548 names, reflected on the leaderboard and membership timeline
- Ran the full backend test suite to completion (1364 passed, 0 net failures) after diagnosing and fixing 15 basis-change test-expectation failures across two fix rounds
- Canonical browser-QA lane crashed before finishing (exit 70); the evaluator independently confirmed the deep-history and ledger-reset journeys passing from the partial evidence captured, and caught a leaderboard-crash regression the same evidence exposed

## What's left

- Journey J-01 (every score shows an evidence status) regressed — the `/stocks` leaderboard crashes to a blank page when sorted by "Sector"; blocking, must fix before closing this iteration
- The canonical browser-QA lane never finished (crashed at exit 70): Watchlist negative-path tests, the Backtest as-of floor, and 3 of 4 quadrants of the required anti-goal language sweep never ran
- `status.json` and the QA report both claim "zero blockers / ready to ship" despite the crash screenshot sitting in their own cited evidence folder — needs reconciliation
- The audit did not incorporate the ux-regression review's FAIL finding — needs a re-run once the crash is fixed
- Journey J-12 (broad point-in-time dynamic universe) partial — the membership timeline, a mid-IPO absent-then-present name, and the stale-series card were not cleanly browser-verified
- Journey J-02 (drill into the proof behind a score) partial — structurally un-exercisable until a new claim re-certifies on the 30-year basis (sanctioned, not a regression)
- Journeys J-06..J-09 (four previously-certified edges) partial — all honestly failed re-certification on the deeper history; a future iteration may propose a new claim through the referee gate
- Journey J-13 (Data Manager reflects the broadened universe + legend) unbuilt — sequenced to the next iteration
- Sector labels for the ~400+ broadened-pool names are still missing (rendered blank, never fabricated); the deep index/macro chart overlays (J-14 steps 2-3) are loaded but not yet wired into any chart

## Next step

Halt for human review (`--acknowledge-regression` required before resuming). iter-19 (FULL) is a fix-and-complete-verification pass, no new feature or evidence work: (1) harden the Sector sort comparator and filter vocabulary against null values in `apps/frontend/app/stocks/page.tsx` and correct the `sector` type in `apps/frontend/lib/api.ts`, plus add `error.tsx` / `global-error.tsx` containment so a future uncaught exception can't wipe the whole page; (2) complete the canonical browser-qa lane, which crashed at exit 70 with tasks #18-22 pending — re-verify the sector-sort fix, Watchlist negative paths, the Backtest as-of floor, and the still-incomplete anti-goal language sweep; (3) cleanly browser-verify J-12's membership timeline, mid-IPO absent-then-present name, and stale-series card; (4) reconcile `status.json` and the QA report against the real evidence set and re-run the auditor with instructions to incorporate the ux-regression verdict; (5) non-blocking — confirm whether the Full-history chart plots pre-2018 weekly bars for long-tenured names. On a clean re-run, J-01 returns to passing and J-12 flips to passing.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-18-what-to-click.md`:

1. Open `http://localhost:3255/stocks/AAPL` in your browser
2. Click the "Full history" button
3. Click "Recent" to switch back
4. Navigate to `http://localhost:3255/stocks`
5. Navigate to `http://localhost:3255/evidence`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-18.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-18-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-18-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-18-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-18-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-18-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-18-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-18-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-18-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-mcp-loop-iter-18-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-18-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-18-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-18-closure-verdict.md |
| Goal evaluation | REGRESSION | runs/goal-session-mcp-loop/iter-18/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
