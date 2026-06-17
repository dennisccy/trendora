# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-17
**Iteration:** 27

## In plain words

**What you can do now:** See today's market regime and a ranked top-five themes strip on the Stocks leaderboard header; step back to any past snapshot date using always-visible back/forward buttons, optional keyboard arrow keys, or the calendar popover with year/month jump menus; open any historical date link and see the correct data from the very first moment — no flash of today's figures; open any stock for an explainable score breakdown with a regime-banded price chart, a per-bar hover box, and realized forward returns at five horizons alongside a matching max-drawdown figure for each horizon; sort and search the stock leaderboard by any column; filter by theme and expand member stocks as dated new-tab links; browse the Sectors leaderboard with every ETF named and mapped; see five forward-return columns and five max-drawdown columns on the Themes and Sectors leaderboards, sortable and matching Backtest exactly; run walk-forward backtest evidence with control groups and see average max-drawdown alongside every group's returns; explore factor effectiveness, an event study showing average max-drawdown per horizon, and a Regime x Setup x Pattern ranked study; click any sample count to open the exact stored observations; save stocks to a watchlist; trigger a confirm-gated full snapshot rebuild from the Data page so newly-expanded universe members appear in every read surface; and manage imports with live progress, stage-aware resume, per-date failure isolation, a multi-hue availability heatmap, reliable multi-month backfill, a deliberate range-scoped data-removal flow, and an Expand-universe job that properly authenticates with the data provider.

**What changed this time:** The app can now rebuild its entire snapshot set from scratch on demand — useful after expanding the tracked universe — behind a confirm dialog on the Data page that makes it impossible to start accidentally, with live progress and a calm "all members present" note when no rebuild is needed. Every forward-return figure across the app (stocks, sectors, themes, stock detail, backtest breakdowns, and research tables) is now paired with a matching max-drawdown number stored from the same walk-forward calculation, so you can see how far a position could have fallen in the worst stretch across each time horizon. Two small defects remain to fix: the max-drawdown columns' colour shading is flat (not yet graded by how severe the drawdown is) and column sort clicks are not reordering the table yet.

**What's next:** Next we'll fix the max-drawdown colour grading and sort behaviour so those columns work the same as the forward-return columns, and then the goal will be fully achieved.

## Headline

J-85 snapshot rebuild + coverage diagnostic pass; J-86 MDD data correct everywhere but sort and colour grading need a small frontend fix

## Direction

**Signal:** improving

**Why:** J-85 (confirm-gated regenerate-from-scratch snapshot rebuild + coverage diagnostic) flipped from failing to passing this iteration with full browser-QA verification. J-86 (max-drawdown columns on every surface) delivered all data-correctness legs — 878-test full backend suite is GREEN, coherence COHERENCE-PASS — and is only a small frontend fix away from passing (sort selector artifact and flat colour grading, both source-confirmed and tractable). Zero regressions across all 27+ required-still-passing journeys; one journey newly passing = improving signal.

**Trend (last 5 iters):**
- Newly passing this iter: J-85
- Newly passing in last 5 iters total: J-83 (iter-25), J-84 (iter-26), J-85 (iter-27)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the lone ever-recorded iter-20 minor magic-number violation stays resolved since iter-21)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-85 is genuinely passing — coverage diagnostic served on GET /api/data (0 absent → calm "all members present" note, no banner), confirm-gated rebuild panel/modal with a persistent Confirm, and the destructive live rebuild correctly SKIPPED per guard while the real clear-then-create-once orchestration is proven OFFLINE by test_iter27_rebuild_mdd.py (13 passed). J-86's data is correct and complete everywhere (5 MDD cols ≤0, NA-honest, byte-identical to Backtest, aggregate mean-MDD on Backtest+Research), but two UI acceptance legs FAIL: the client-side MDD column sort does not reorder (UT-03/UT-09) and colour-grading is flat (UT-04, source-confirmed in forward-return.tsx mddClass). The full backend suite is GREEN (878 passed, 0 failed, EXIT_CODE=0) and coherence is COHERENCE-PASS, so this is a small frontend consolidation away from GOAL_ACHIEVED — not a regression, not done.

## What was done

- Added a `kind="rebuild"` job to the data manager that clears the entire snapshot set (scanner runs, scores, forward returns) then create-once recomputes every trading date via the existing parallel backfill path; committed price seed is never touched
- Added a read-only `_coverage_diagnostic_absent` count to the existing `GET /api/data` coverage block, showing how many resolved-universe members are absent from the latest snapshot
- Added a nullable `max_drawdown` column to the `forward_returns` table (registered in `_ADDITIVE_COLUMNS` for live-DB migration), computed once per (run, symbol, horizon) alongside realized return, using a running-peak peak-to-trough definition, always ≤ 0
- Surfaced five paired max-drawdown columns on `/stocks`, `/stocks/[ticker]`, `/themes`, and `/sectors`; added aggregate `mean_max_drawdown` to Backtest and Research tables; all read VERBATIM from stored data, no read-path recompute
- Updated the three `test_api_*_equals_engine_output` byte-equality guards to strip only the additive `max_drawdown` key while separately asserting it exists — full 878-test backend suite passes GREEN
- Added `/data` RebuildPanel with coverage diagnostic note/banner, confirm-gated rebuild modal (persistently-visible Confirm), and progress wiring through the existing job card
- Added frontend MDD cell formatters in `forward-return.tsx` (`fmtMdd`, `mddClass`, `MaxDrawdown`); MDD columns render on all four leaderboard pages plus Stock Detail, Backtest, and Research
- Verified 17/22 browser-QA tests pass, including all data-correctness legs; J-85 fully passing; J-86 two frontend legs (sort no-op and flat colour grading) still failing

## What's left

- Journey J-86 (max-drawdown columns everywhere) failing — two frontend legs: MDD column sort does not reorder (UT-03/UT-09, XPath selector artifact most likely; must be re-verified with aria-label selectors and fixed if genuinely broken) and MDD colour grading is flat rather than graduated by magnitude (UT-04, source-confirmed defect in `mddClass()`)
- Journey J-22 (transparent rule-based expanded universe ~500 names) blocked-NA — data-walled, non-vetoing per goal.md; auto-unblocks when a cap-capable data provider is reachable
- Journey J-23 (multi-timeframe bars) blocked-NA — data-walled, non-vetoing
- Journey J-24 (timeframe selector on stock chart) blocked-NA — data-walled, depends on J-23, non-vetoing

## Next step

Run a **lean** frontend-only consolidation (J-86 finish):
1. **Fix MDD colour grading (UT-04, confirmed defect):** `apps/frontend/components/forward-return.tsx` `mddClass()` returns a flat `text-neg` for all negatives — make it graduate by magnitude per the iter-27 spec ("colour-graded by magnitude (≤ 0)"). Use design tokens only (no hardcoded hex — J-70/J-74 token discipline). If a graduated scale is deliberately out of scope, the spec wording must be reconciled; otherwise grade it.
2. **Re-verify the column sort with CORRECT selectors and FIX if genuinely broken (UT-03/UT-09/UT-20):** the sort code path is byte-unchanged from what passed in iter-23/iter-20, and the failing browser-QA used `//th//button[text()='5d']` which cannot match a button whose label is in a nested `<span>`. Re-test by resolving the SortHeader button by its `aria-label` ("Sort by 5d", "Sort by 5d MDD") and assert the rendered row order changes (and the `data-testid="sort-indicator"` flips). Confirm J-48/J-75 forward-return sort still works (no genuine regression) and the new MDD columns sort NA-last.
3. Re-smoke the J-86 data legs (already PASS) only as needed; the backend is done and the full suite is GREEN — no backend change should be needed, so a lean depth is correct.

After the colour grading is graduated, the sort is confirmed working on all five MDD columns (and J-48/J-75 fwd-return sort confirmed unregressed), with COHERENCE-PASS and the suite still GREEN, J-86 flips to `passing` and every buildable Must-have is green — the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing).

Evidence-hygiene for next iter QA: the iter-27 evidence dir had multiple `-cors-block.png` frames (transient connectivity) and shared-byte frames (UT-08 cites UT-09-sectors-sort-fail.png; UT-21 cites UT-22-asof-nav-mdd.png) — md5sum first, resolve sort buttons by aria-label not text(), and capture the colour-graded MDD cells full-viewport wide (they sit to the RIGHT of the fwd-return columns).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-what-to-click.md`:

1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31` — confirm five "Xd MDD" column headers appear to the right of the return columns; all MDD cells are negative or "NA", none positive.
2. Click the "5d MDD" column header — confirm the table re-sorts (no page reload) with NA rows at the bottom; clicking again reverses real-value rows while NA stays at the bottom.
3. Click any stock ticker to open its detail page at `/stocks/[TICKER]?asof=2025-12-31` — confirm each of the five horizon cards shows a "Max drawdown" sub-line with a negative percentage or "NA".
4. Navigate to `http://localhost:3835/backtest?asof=2025-12-31` — confirm a "Mean MDD" column appears in breakdown evidence tables with negative values; summary header shows "Mean max drawdown".
5. Navigate to `http://localhost:3835/data` — confirm a rebuild button is present; clicking it opens a confirm modal (not an immediate job); clicking Cancel closes the modal with no job started.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-review.md |
| Browser QA | FAIL | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-ui-test-results.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-what-to-click.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-27/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
