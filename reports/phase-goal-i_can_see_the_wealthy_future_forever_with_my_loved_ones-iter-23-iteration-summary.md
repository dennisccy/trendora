# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-16
**Iteration:** 23

## In plain words

**What you can do now:** See today's market regime, regime score, and a top-five themes strip directly on the Stocks leaderboard header; step back to any past snapshot date using always-visible back/forward buttons, optional keyboard arrow keys, or the calendar popover with year/month jump menus; view a dashboard whose indexes chart opens on the full available history; open any stock for an explainable score breakdown with a regime-banded price chart, a per-bar hover box, and realized forward returns at 1, 5, 10, 20, and 60 days; sort and search the stock leaderboard by any column; filter by theme and expand member stocks as dated new-tab links; browse the Sectors leaderboard with every ETF named and mapped; see five forward-return columns (1/5/10/20/60 days, colour-graded green or red) directly on the Themes and Sectors leaderboards — sortable and cross-checkable against Backtest; explore factor effectiveness, a ranked Regime x Setup x Pattern study with filter dropdowns and correct NA-last sorting, and click any sample count to open the exact stored observations with no errors; save stocks to a watchlist; and manage imports with live progress, stage-aware resume, per-date failure isolation, a multi-hue availability heatmap, and a deliberate range-scoped data-removal flow.

**What changed this time:** The Themes and Sectors leaderboards now each show five forward-return columns (1, 5, 10, 20, and 60 days). The values are colour-graded green or red, show "NA" honestly where data is not yet available, sort client-side with NA rows always at the bottom, and match the numbers shown on the Backtest page exactly. The Research page's Regime x Setup x Pattern table also gained three filter dropdowns (Regime, Setup, and Pattern), correct NA-last sorting in both directions, and a fix so that clicking any sample count chip — including rows with no detected pattern — opens the correct samples page without an error. The section also now opens in "Pooled" view by default instead of "Episodes".

**What's next:** Next we'll reconcile two stale automated test guards (which do not reflect a real issue in the product) so the full test suite runs clean — after which the product reaches its final goal.

## Headline

J-81 + J-82 pass 23/23 browser QA; two stale over-strict test guards block GOAL_ACHIEVED (full suite EXIT_CODE=1).

## Direction

**Signal:** improving
**Why:** J-81 (Themes/Sectors forward-return columns) and J-82 (RSP table NA-last sort + filters + emitted-combination drill-down + Pooled default) are both newly passing this iteration, verified by a clean 23/23 browser QA run and 12 targeted backend tests proving byte-identity to Backtest's `_leadership_returns`. The only remaining blocker is two stale `test_api_engine.py` guards that do not reflect a real feature regression — iter-24 clears them, then GOAL_ACHIEVED is appropriate.

**Trend (last 5 iters):**
- Newly passing this iter: J-81, J-82
- Newly passing in last 5 iters total: J-79, J-80 (iter-22), J-81, J-82 (iter-23)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (the iter-20 minor magic-numbers violation was resolved in iter-21)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-81 (themes/sectors forward-return columns) and J-82 (RSP table NA-last sort + filters + emitted-combination drill-down + Pooled default) both landed correctly and newly pass: browser QA is a clean 23/23, the 12 targeted backend tests in `test_iter23_leaderboard_returns.py` prove the J-06 single-source byte-identity of the new forward returns to Backtest's `_leadership_returns`, and coherence is COHERENCE-PASS. But the standing GOAL_ACHIEVED gate — a GREEN full backend suite — is NOT met: the flushed authoritative full-suite result is `2 failed, 844 passed, 4 skipped, EXIT_CODE=1`. The two failures are STALE `served == engine_output` byte-equality guards that the dev did not update for J-81's legitimate additive `forward_returns` field — not a coherence break, but a red suite that blocks GOAL_ACHIEVED.

## What was done

- Added five forward-return columns (1/5/10/20/60d) to `/themes` — equal-weight member-basket realized returns, read via the same `_leadership_returns` builder Backtest uses (one SELECT per request, no second query per row)
- Added the same five forward-return columns to `/sectors` — each sector/industry ETF's own realized return, same builder
- Proved byte-identity of themes/sectors forward returns to Backtest Top Themes/Top Sectors for the same date+horizon (12 targeted tests all pass, incl. equal-weight basket, NA-at-latest, config-driven horizons)
- Fixed RSP table NA-last sorting — display predicate reused for sort so low-sample rows always sink to the bottom in both directions
- Added three config-driven filter dropdowns (Regime / Setup / Pattern, each default "All") to the RSP section, composing AND-style with the sort and with an honest empty-after-filter state
- Reconciled `_regime_setup_pattern_samples` validation to the emitted-combination set so every N= chip (including `pattern=none` rows) opens without a 4xx, with `total == row n` by construction in both Episodes/Pooled and All-history/As-of modes
- Set the RSP section's toggle initial state to Pooled without touching the canonical `compute_regime_setup_pattern_study` default or the rest of `/research` (Event Study keeps Episodes)
- Verified 23/23 browser QA tests PASS; verified coherence COHERENCE-PASS; review PASS

## What's left

- Two stale over-strict test guards (`test_api_engine.py::test_api_themes_equals_engine_output`, `::test_api_sectors_equals_engine_output`) assert byte-equality of the served payload to raw engine output — the J-81 additive `forward_returns` key (a legitimate read surface, not a recomputed score) breaks that blanket guard; full suite is EXIT_CODE=1 (2 failed / 844 passed), blocking GOAL_ACHIEVED
- J-22 (Transparent rule-based expanded universe ~500 names) — blocked-NA (data-walled, non-vetoing)
- J-23 (Multi-timeframe bars — intraday seed + pipeline) — blocked-NA (data-walled, non-vetoing)
- J-24 (Timeframe selector on the stock chart) — blocked-NA (depends on J-23, non-vetoing)

## Next step

Run a small full-depth consolidation iteration that turns the full backend suite GREEN, then declare GOAL_ACHIEVED. Exactly one defect blocks completion: `apps/backend/tests/test_api_engine.py::test_api_themes_equals_engine_output` and `::test_api_sectors_equals_engine_output` assert the served `/api/themes` and `/api/sectors` payloads are byte-for-byte equal to the raw engine output (`score_themes`/`score_sectors`). J-81 additively attached a `forward_returns` key to each served row — a value the engine score functions never compute (forward returns come from the separate walk-forward engine, read verbatim from the append-only `forward_returns` table, byte-identical to Backtest). The guards are now over-strict and must be reconciled to the legitimate additive surface, mirroring iter-20→iter-21's fix. Fix options: compare `served` modulo the additive `forward_returns` key (strip it before the byte-equality assert and separately assert the field exists with the configured horizons), or build `expected` from the served-payload helper so the comparison reflects the real serve shape. Then re-run the FULL backend pytest suite to `EXIT_CODE=0` (nohup-async, never blocking the evaluator dispatch). No browser re-QA is needed for a test-only change beyond a smoke that `/themes` + `/sectors` still serve. After the suite is GREEN with zero regressions, every buildable Must-have is passing and J-22/J-23/J-24 stay honestly blocked-NA — GOAL_ACHIEVED is then appropriate.

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-what-to-click.md`:

1. Navigate to `http://localhost:3835/themes` and set the global as-of date picker to a historical date with data (e.g., 2024-01-15).
2. On the same `/themes` page, click the "5d" column header.
3. Click the "5d" column header a second time.
4. Navigate to `http://localhost:3835/sectors` and keep the same historical as-of date.
5. Navigate to `http://localhost:3835/research` (fresh page load — do not use browser back button) and scroll to the Regime × Setup × Pattern section.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-ui-test-results.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-what-to-click.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-23/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
