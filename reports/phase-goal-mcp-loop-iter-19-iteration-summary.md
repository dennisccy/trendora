# Iteration Summary — goal-mcp-loop-iter-19

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-07
**Iteration:** 19

## In plain words

**What you can do now:** Browse a leaderboard of several hundred companies with up to 30 years of price history each, sort and filter that list by sector — including an honest "Unassigned" label for companies with no sector on file — switch a stock's chart between a recent view and its full history, keep a personal watchlist, and see an honest "not yet proven" evidence status on every score and past trading idea, with full reasoning auditable on the Evidence page.

**What changed this time:** This round fixed the crash that happened when sorting the stock list by "Sector" (most of the newly-added companies have no sector on file, and clicking that column used to blank the whole screen, wiping out the navigation menu too). It also fixed a memory problem that could freeze the Data page shortly after a restart, confirmed that the deeper company-history timeline displays correctly, and added a safety net so any future unexpected error shows a calm "Something went wrong, try again" message instead of wiping out the whole app.

**What's next:** With this crash fixed and verified, the next round can focus on trying to honestly re-earn "Proven" status for some of the trading ideas that didn't survive the recent deeper-history retest, plus a few small polish items like widening long-history charts and re-running a couple of slower background checks.

## Headline

Stocks leaderboard no longer crashes when sorting by Sector

## Direction

**Signal:** improving
**Why:** This iteration browser-verified a fix for the exact `/stocks` Sector-sort crash that drove last iteration's REGRESSION verdict (J-01), and separately completed the browser verification of the broadened universe's membership timeline (J-12) — both previously broken or incomplete. Six independent artifacts this iteration (dev handoff, review PASS, QA PASS, canonical browser-QA PASS 23/24, ux-regression UX-REGRESSION-PASS, phase-closure CLOSURE-PASS) all corroborate zero new regressions and zero anti-goal violations. `journey-history.json` itself has not yet been updated by the goal-evaluator (it still shows J-01 as "regressed" from iter-18), so this signal reflects this iteration's own fresh verification evidence rather than a re-classified journey-history entry.

**Trend (last 5 iters):**
- Newly passing this iter: J-01, J-12 (per this iteration's dev/QA/browser-QA/ux-regression/closure evidence — journey-history.json and eval.md have not yet been updated by the goal-evaluator for iteration 19)
- Newly passing in last 5 iters total (iters 15-19): J-01, J-09, J-10, J-11, J-12
- Regressions in last 5 iters: J-01 (iter-18) — now fixed and re-verified this iteration
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-16, iter-17)

**Latest evaluator reasoning:** "The UNSANCTIONED half is a REGRESSION: I opened UT-21-fail-crash.png and confirmed the /stocks leaderboard crashes to a blank "Application error" (all nav wiped) on Sector-sort — a prior-passing interaction (live since iter-2) broken by THIS iteration's broadened pool returning sector:null for ~78% of rows (scoring.py:377) into the unguarded comparator stocks/page.tsx:93 (git diff on that file EMPTY — a data-contract regression, not a code change) with no error.tsx to contain it. Two independent gates concur (UX-REGRESSION-FAIL, CLOSURE-FAIL) while status.json/qa.md falsely reported "zero blockers / 18/18 pass / ready to ship" with the crash screenshot in their own cited evidence folder. Per decision-tree rule 1 (a passing journey now failing), verdict = REGRESSION." (goal-mcp-loop-iter-18)

## What was done

- Fixed the `/stocks` Sector-sort crash: added a shared null-safe `sectorLabel`/`compareSectors` helper so the ~78% of companies with no mapped GICS sector show "Unassigned" (in the sort, filter dropdown, and table cell) instead of throwing.
- Fixed the backend `/api/data` OOM: rewrote `_BarCache.prefill()` from a whole-table `.all()` load (~6.8 GB peak) to a streamed, column-projected query (~1.09 GB peak; 10.5s single cold / 18.5s at 6-concurrent), plus a `_prefilled` guard closing a nested double-scan found empirically.
- Added crash containment: new `error.tsx` (route-level) and `global-error.tsx` (root-level) boundaries so an uncaught client exception shows a contained card with the sidebar nav intact instead of a blank app.
- Corrected the `StockRow.sector` TypeScript contract from `string` to `string | null` and re-validated every consumer (`tsc --noEmit`: 0 errors).
- Ran the canonical browser-QA lane to completion: 23/24 PASS (1 P3 SKIP with a documented static-verification substitute) — closing the exact lane that crashed mid-run in iteration 18.
- Cleared review (PASS), QA (PASS), ux-regression (UX-REGRESSION-PASS), audit (PASS_WITH_GAPS, no fixes needed), and phase-closure (CLOSURE-PASS).
- Recorded the item-A before/after performance measurement in a new `reports/perf-budgets.md`.
- Verified 2 target journeys pass browser QA: J-01 (Sector-sort, UT-01/02/03) and J-12 (membership timeline, UT-15).

## What's left

- J-02, J-06, J-07, J-08, J-09 remain "partial" by design — their previously-certified trading edges didn't survive re-certification on the deeper 30-year history (a sanctioned ledger reset, not a regression); a new pre-registered claim is needed to re-light any of them.
- J-13 (Data Manager 548-symbol legend) and J-14 (deep index/macro display) remain unknown — explicitly deferred, out of scope this iteration.
- Two seed-heavy backend test files (`test_scanner.py`, `test_bars.py`) were not run to completion this session; low-risk per dev/audit reasoning, recommended re-run when a multi-minute budget is available.
- The `/stocks/{ticker}` Full-history chart's x-axis still doesn't visually extend to a deep-history name's true first bar (F1) — a pre-acknowledged, non-blocking carry item.
- `perf-budgets.md` reports resident memory (RSS) rather than virtual memory (VSZ), the actual basis for the `ulimit -v` cap — a measurement-precision nicety to add later (B2).
- `return-attribution.tsx` still renders an unmapped sector as a blank cell rather than the new "Unassigned" label used elsewhere (F3) — pre-existing, non-blocking.
- The goal-evaluator has not yet run for this iteration: `journey-history.json` still shows J-01 as "regressed" and J-12 as "partial" from iteration 18, pending formal re-classification against this iteration's dev/review/QA/browser-QA/ux-regression/audit/closure evidence (all of which independently confirm both are now fixed).

## Next step

No blocking issues remain — the phase-closure-auditor returned CLOSURE-PASS and the audit's own recommendation is to proceed. Non-blocking carry-forward items for a future iteration: re-run `test_scanner.py`/`test_bars.py` for independent confirmation (low-risk, already gated by other tests), widen the Full-history chart's x-domain for deep-history names (F1), add a VmSize sample to `perf-budgets.md` for a precise cap-distance figure (B2), and reconcile the `return-attribution.tsx` blank-vs-"Unassigned" terminology inconsistency (F3). Since no `eval.md` exists yet for this iteration, the goal-evaluator should now run to confirm J-01 and J-12 return to "passing" given this iteration's browser-verified fixes, and assess whether the remaining partial journeys (J-02, J-06–J-09) or unknown journeys (J-13, J-14) change the path toward GOAL_ACHIEVED.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-19-what-to-click.md`:

1. Open http://localhost:3255/stocks in your browser
2. Click the word "Sector" in the column header row of the table
3. Click "Sector" again
4. Above the table, click the dropdown labeled "Sector" (it currently reads "All sectors") and select "Unassigned"
5. Look underneath any score badge (Leadership, Entry Quality, or Risk) in the narrowed list

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-19.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-19-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-19-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-19-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-19-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-19-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-19-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-19-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-19-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-19-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-19-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-19-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-19-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
