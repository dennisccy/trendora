# Iteration Summary — goal-mcp-loop-iter-22

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-08
**Iteration:** 22

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with up to 30 years of price history each, sort that list by sector, and switch any stock's chart between a recent view and its full history. Every score, evidence entry, and past trading idea carries an honest "proven" or "not yet proven" status tied to the current market regime, backed by a full evidence ledger you can audit yourself, and companies join and leave the list honestly as their real trading histories start and end. On the Data Manager page, refreshing prices covers the entire company list in one click, with a calendar that clearly separates "we have price data for this day" from "we've already scored it." If something goes wrong on a page, you get a calm retry message instead of a blank screen.

**What changed this time:** The team built a deeper view of market history — three major stock-market benchmarks (the S&P 500, Nasdaq, and Dow) now show on the dashboard's chart going back to 1996, three decades instead of one, plus a volatility gauge and an economic-indicator line — and every line on that chart, plus a new page section, now honestly says which data provider it came from. Along the way, they found and fixed a bug where that deep history loaded correctly but stayed hidden off-screen by default; the fix works in every check run so far, but the team wants one more specific hands-on check on the fixed version before calling this feature fully done.

**What's next:** Next, the team will do one more hands-on check to confirm the new dashboard chart and data-source labels display correctly by default, then mark this feature complete.

## Headline

J-14 deep 1996 index/vendor-label chart shipped and fixed; CLOSURE-FAIL pending a fresh browser-QA re-run

## Direction

**Signal:** holding
**Why:** J-14's underlying code (deep 1996 benchmark lines + honest vendor labels) is built and independently confirmed correct by the reviewer, the QA agent's own spot-check, and the auditor's pixel-level comparison, but the phase is blocked on a process/evidence gap, not a product gap: the canonical browser-qa-agent report and the ux-regression report were both written against the pre-fix build and were never regenerated after the chart-config fix, so CLOSURE-FAIL (this iteration's controlling verdict, since the goal-evaluator has not yet run) keeps J-14 from being marked passing. No journey regressed — J-01, J-03, J-04, J-05, J-10, and J-12 were all freshly re-confirmed via live browser evidence in the same run — and no anti-goal was violated, so this reads as holding rather than regressing or stalling.

**Trend (last 5 iters):**
- Newly passing this iter: none (J-14 targeted but blocked at CLOSURE-FAIL before the evaluator ran; not yet confirmed passing)
- Newly passing in last 5 iters total: J-01, J-10, J-11, J-12, J-13 (iters 18-21)
- Regressions in last 5 iters: J-01 (iter-18)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "The iter-20 verification gap is closed and I verified every status change against artifacts I personally opened, not the handoffs. The canonical browser-qa-agent lane RAN LIVE this time (~59 min, engine.log 10:34->11:33; it correctly overrode a stale dispatch SKIP flag by independently re-verifying both services at HTTP 200 — the exact iter-20 blanket-SKIP failure this iteration existed to retire) and produced a non-empty, 12-PNG md5-distinct evidence dir." (goal-mcp-loop-iter-21 evaluator log entry — no eval.md exists yet for iter-22, which is still blocked pre-evaluation.)

## What was done

- Added three deep equity-index benchmarks (S&P 500, Nasdaq 100, Dow Jones) to the Dashboard chart, extending history back to 1996-01-02, and loaded their bars into the live database (+23,022 rows, 590 distinct symbols).
- Added a CBOE Volatility Index line and a "10Y-2Y spread proxy" macro line to the same chart.
- Labeled every chart line (legend + tooltip) with its honest data vendor (Stooq / Yahoo / FRED-macro proxy), added a matching disclosure panel on `/data`, and extended the chart's color palette from 5 to 10 distinct colors.
- Preserved byte-identity on the existing five ETF chart lines and the scored `/stocks` universe (541 symbols, zero leaked index rows).
- Found and fixed a critical bug where the new 1996 history loaded correctly but stayed hidden off-screen by default; a chart-config fix now makes the full 30-year window the default view, independently confirmed by the reviewer and the auditor.
- The canonical browser-qa-agent lane recorded FAIL for the sole target journey (J-14) against the pre-fix build and has not yet been re-run against the fix (0 of 1 target journeys confirmed passing this iteration); the same run confirmed 6 of 7 required-still-passing regression journeys (J-01, J-03, J-04, J-05, J-10, J-12) remain intact.
- Re-ran review and the audit after the fix (PASS / PASS_WITH_GAPS), but the canonical browser-qa-agent and ux-regression reports were not regenerated — phase closure FAILED on that unreconciled evidence gap.

## What's left

- Blocking: the canonical browser-qa-agent report for J-14 is stale (written before the fix) and must be regenerated end-to-end against the fixed build before it can count as a pass.
- Blocking: the UX-regression report is also stale and still labels the same defect "Blocking" — needs re-running once fresh browser-qa evidence exists.
- Blocking: the user-visible-changes report's claim that the deep lines render automatically was disproven by QA and has only been "corrected" by the developer's own say-so, not independent re-verification — needs reconciling once the re-run confirms the fix.
- J-14 (this iteration's target journey) has not yet flipped to passing — blocked behind the three items above, not because the underlying feature is wrong.
- J-13 (required-still-passing) did not get a dedicated live regression replay this iteration (non-blocking, low risk since its component is unmodified, but flagged for the next regression pass).
- Non-blocking: the macro-proxy line's disclosed "first bar" date (2021-01-04) understates its actual database history (back to 2005) — a pre-existing, spec-compliant inconsistency with no in-scope fix.
- Not visible yet: the same vendor-label/palette fix was also applied to an orphaned chart component that no page currently links to (a cleanup candidate, not a defect).
- The full backend test run for the new API fields (using an expensive 30-year test fixture) had not finished at handoff time and should be confirmed green.

## Next step

Re-invoke the browser-qa-agent against the current, already-fixed build (clear the frontend build cache and confirm both services are reachable first) to regenerate a full, fresh `ui-test-results.md` covering all 19 planned cases — not just the one that failed — and confirm it now reads PASS. Then re-run the ux-regression-reviewer against that fresh evidence so its blocking flag lifts, and reconcile or regenerate `user-visible-changes.md` so its capability claim rests on independent verification rather than the developer's own assessment. Do not reopen the J-14 implementation itself — the phase auditor and closure auditor agree the underlying fix is correct; this is expected to be a fast confirmatory re-run, not a rediscovery of a defect.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-22-what-to-click.md`:

1. Open `http://localhost:3255` in your browser
2. Look at the row of labels (the legend) directly below the chart, and the small colored dot to the left of each label
3. Move your mouse pointer anywhere over the chart's plotted lines
4. Refresh the page (press F5)
5. Click "Data Manager" in the left sidebar

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
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
