# Iteration Summary — goal-mcp-loop-iter-22

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-08
**Iteration:** 22

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of companies with an honest evidence status shown on every score, and drill into a fully auditable history of every past trading idea the system has tested — each one clearly marked "proven" or "not yet proven," tied to the current market mood. You can view up to thirty years of price history for any stock, switching between a recent view and the full history, and you can look at the company list the way it looked on any past date. On the Data Manager page you can see a coverage calendar showing what price and scoring data is available across the whole company list.

**What changed this time:** The dashboard's main chart now shows three decades of market history for the S&P 500, Nasdaq, and Dow — back to 1996, three times further than before — plus a volatility gauge and an economic-indicator line, and every line now honestly discloses which data provider it came from, both on the chart and in a new section of the Data Manager page. Partway through, the team caught a bug where that deep history was loading correctly but staying hidden off-screen unless someone scrolled far back manually; that's now fixed so the full three decades show automatically when the page opens. The team's own process still calls for one more hands-on confirmation check before this feature is officially marked finished, so it isn't quite checked off yet.

**What's next:** Next, the team will do that final confirming check on the new deep-history chart (making sure it looks right for everyone, not just in one test) and then mark it fully complete.

## Headline

Dashboard chart now shows S&P 500/Nasdaq/Dow back to 1996, labeled by data vendor

## Direction

**Signal:** holding
**Why:** iter-22 shipped J-14 (deep 1996 index/vendor context) code-complete and multi-channel verified — audit PASS_WITH_GAPS, review PASS, QA PASS — but the canonical browser-qa-agent and ux-regression-reviewer were never re-run against the post-audit-fix build, so phase-closure returned CLOSURE-FAIL and J-14 landed at partial rather than passing, the same verification-gap pattern seen in iter-13 and iter-20. No journey regressed, all six required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-12) re-verified live, and all anti-goals held, so the project is holding steady rather than moving backward, with one clearly-scoped verification re-run standing between it and the next passing flip.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-10, J-11 (iter-18), J-01, J-12 (iter-19), J-13 (iter-21)
- Regressions in last 5 iters: J-01 (iter-18)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The J-14 code deliverable landed COMPLETE and is independently verified correct on multiple channels — deep ^SPX/^NDX/^DJI/^VIX/^TNX context surfaced on the Dashboard chart with honest per-series vendor labels, plus a new /data provenance panel, all byte-matching meta.json — but the DoD's "pass via browser-qa-agent" was not satisfied on the FIXED code. An audit-FAIL → dev-fix (minBarSpacing: 0.02, which surfaces the deep 1996 window) → re-review/re-QA/re-audit cycle happened, yet the canonical browser-qa-agent and ux-regression-reviewer were never re-run against the fixed build, so both reports-of-record are stale FAILs and phase-closure returned CLOSURE-FAIL (status.json = blocked / closure_failed). Per the iter-13/iter-20 precedent, J-14 advances unknown → partial, not passing. No journey regressed; all anti-goals upheld; coherence is COHERENCE-WARN (not FAIL) → CONTINUE.

## What was done

- Added deep `^SPX`/`^NDX`/`^DJI` equity-index benchmarks (to 1996) plus `^VIX` and a `^TNX` macro proxy to the Dashboard chart, now defaulting to the full 30-year view.
- Labeled every chart line with its honest data vendor (Stooq / Yahoo / FRED-macro proxy) in the legend and tooltip; omitted the label where no vendor record exists.
- Added a new "Index & benchmark data provenance" panel on `/data` listing every series' vendor and first-bar date, reading the same `/api/indexes` payload.
- Extended the chart's color palette from 5 to 10 distinct, CVD-checked colors so no two lines collide.
- Fixed an audit-flagged critical defect (`minBarSpacing: 0.02`) so the deep 1996 history renders in the chart's default view instead of staying hidden off-screen.
- Loaded the 3 new deep-index symbols into `daily_prices` via a new idempotent loader script; existing lines' math stayed byte-identical and the scored universe stayed at 541 symbols (no leak).
- Live-replayed the 6 required-still-passing regression journeys (J-01, J-03, J-04, J-05, J-10, J-12) clean via browser QA; target journey J-14 did not cleanly pass the canonical browser-qa lane and stays partial pending a re-run.

## What's left

- J-14 (deep index/vendor context, this iteration's target) is partial — the code is complete and independently verified, but not yet cleanly canonical-verified.
- Closure blocker: the canonical browser-qa-agent report is a stale pre-fix FAIL and must be re-run against the current build (the Definition of Done names this specific agent).
- Closure blocker: the ux-regression-reviewer report is a stale FAIL that explicitly calls the same gap "Blocking" and must be re-run against fresh evidence.
- Closure blocker: the user-visible-changes report's "renders automatically" claim was disproven pre-fix and needs independent (not developer self-assessed) reconciliation.
- J-13 (Data Manager availability legend) carries forward on byte-identity grounds but is owed a dedicated live replay — its last full canonical check was iteration 21.
- J-02, J-06, J-07, J-08, J-09 (evidence re-certification) remain sanctioned-partial — no staging candidate yet clears the divisor-8 statistical bar needed to re-promote a proven edge.
- J-15, J-16 (platform speed budgets) remain unbuilt.
- `test_api_indexes.py`'s full test run had not finished at handoff time; byte-identity is covered at the unit level and via a live API check in the meantime.

## Next step

iter-23 (FULL) — verification-only re-run, no new feature code (the J-14 implementation and the `minBarSpacing: 0.02` fix are done and correct). Clear `apps/frontend/.next`, bring up both prod-mode services, and confirm reachability before dispatching QA. Re-run the canonical browser-qa-agent live over all 19 ui-test-plan cases against the fixed build to flip UT-03 FAIL→PASS; add a dedicated J-13 live replay to close the audit-B5/ux-regression coverage gap; re-run ux-regression-reviewer to UX-REGRESSION-PASS and reconcile user-visible-changes.md; then re-run phase-closure to CLOSURE-PASS. On a clean run J-14 flips partial→passing. GOAL_ACHIEVED is still not reachable next iteration regardless: J-02/J-06/J-07/J-08/J-09 need a new-basis staging-discovery + honest promotion (no staging winner clears the divisor-8 bar today), and J-15/J-16 (fast-platform perf) remain unbuilt.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-22-what-to-click.md`:

1. Open `http://localhost:3255` in your browser
2. Look at the row of labels (the legend) directly below the chart, and the small colored dot to the left of each label
3. Move your mouse pointer anywhere over the chart's plotted lines
4. Refresh the page (press F5)
5. Click **"Data Manager"** in the left sidebar

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-22.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-22-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-22-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-22-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-22-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-22-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-22-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-22-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-mcp-loop-iter-22-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-22-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-22-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-22-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-22/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
