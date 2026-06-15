# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-15
**Iteration:** 20

## In plain words

**What you can do now:** See today's market regime and top-ranked stocks on a dashboard whose indexes chart opens on the full available history; open any stock for a full explainable score breakdown with a regime-banded price chart and a per-bar hover box; step back to any past snapshot date using a calendar or arrow keys, with historical data appearing immediately and without any flicker; share or open any historical link in a new tab; sort and search the stock leaderboard by any column; filter by theme and expand each theme's member stocks as dated new-tab links; browse the Sectors leaderboard with every ETF named and mapped to its universe; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness and overlap-honest event studies; click any sample count to open the exact stored observations; save stocks to a watchlist; and manage price-data imports with live progress, instant run history, stage-aware resume, per-date failure isolation, a compact multi-hue availability heatmap, reliable multi-month backfill, and a deliberate range-scoped data-removal flow. This iteration also built (but has not yet formally unlocked) five realized forward-return columns on every stock row, a matching forward-returns panel on each stock's detail page, and a new Regime × Setup × Pattern evidence table on the research page.

**What changed this time:** Three new research features were built and work correctly. Every stock on the leaderboard now shows how it performed 1, 5, 10, 20, and 60 trading days after any historical scan date — colour-graded green for positive, red for negative, and honestly blank ("NA") when not enough time has passed. The same five numbers appear on the individual stock page too. A brand-new study on the Research page shows which combinations of market regime, setup status, and detected chart pattern have historically produced the strongest results. You can sort that table, flip between "episodes" and "pooled" views, and click any row's count to see the exact underlying stocks in a new tab. The Research page's sections also now load independently, so a slow computation no longer freezes the whole page. These additions are functionally complete but are being held back by two small housekeeping issues in the test suite (a table name that needs registering and two internal code style literals that need removing), which will be resolved in the next step.

**What's next:** A quick cleanup step will fix the two minor test-suite issues and confirm all tests pass green, after which this set of features becomes formally available and the product goal will be achieved.

## Headline

Built J-72 (event-study cache), J-75 (per-stock forward returns 1/5/10/20/60d), J-77 (regime×setup×pattern study) — all functionally correct; held CONTINUE pending 2-failure suite fix in iter-21.

## Direction

**Signal:** improving
**Why:** Three new backend journeys (J-72, J-75, J-77) are fully implemented and functionally verified with byte-identity, count-coherence, and NA-honesty properties all confirmed. No prior-passing journey regressed across the 14 required-still-passing set. The sole blocker is two minor test-suite failures introduced by the iter-20 diff itself — a missing expected-table entry and two sort-sentinel float literals tripping a blanket guard — both trivially fixable in one lean pass. The product is functionally complete on all three targets; the gate is a one-iteration housekeeping step.

**Trend (last 5 iters):**
- Newly passing this iter: none (J-72/J-75/J-77 built but held failing — suite gate RED)
- Newly passing in last 5 iters total: J-73 (iter-19), J-78 (iter-19), J-74 (iter-18), J-76 (iter-18)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 minor (iter-20 — two `0.0` float literals in `research.py _rsp_rank_key` tripping the no-magic-numbers blanket guard; not critical)
- Iters with no journey state change: 2 of last 5 (iter-17: browser env down, no evidence; iter-20: journeys built but held failing)

**Latest evaluator reasoning:** "All three target journeys (J-72 event-study perf/cache, J-75 per-stock forward returns, J-77 Regime × Setup × Pattern) are functionally built and verified — byte-identity (both views, all-history + as-of), single-batched-read, cache-refresh-after-dataset-change, count-coherence SAME-INSTANT both modes, NA honesty, 4xx error paths, config-backed vocabularies — plus COHERENCE-PASS, review PASS, QA UI-PASS, and every required-still-passing journey re-verified green. BUT the authoritative full backend pytest suite is RED: 2 failed / 831 passed. (1) `test_db.py::test_create_all_produces_expected_tables` — the new standalone `event_study_cache` table was not added to the expected-tables set. (2) `test_no_magic_numbers.py` — two `0.0` float literals in `research.py _rsp_rank_key` trip the No-magic-numbers anti-goal guard. Both are minor and trivially fixable; neither is a critical anti-goal violation and neither regresses a prior-passing journey, so this is CONTINUE (one-step fix), not REGRESSION and not yet GOAL_ACHIEVED."

## What was done

- Replaced per-horizon re-scan in `compute_event_study` with a single batched `ForwardReturn` SELECT covering all configured horizons; added standalone `event_study_cache` table so repeated event-study requests serve from cache (~28s → ~0.02s)
- Wired `GET /api/research/event-study` to the new cache with auto-refresh on dataset change (backfill add or removal changes the dataset-version stamp)
- Extended `snapshot_serving.stored_stock_rows` to additively attach a `forward_returns` list (one entry per configured horizon, verbatim from stored `forward_returns` table) to every `/api/stocks` and `/api/stocks/{ticker}` row; NA where no stored row exists
- Added `research.compute_regime_setup_pattern_study` and `GET /api/research/regime-setup-pattern`: pure grouping of the enriched event-study observation set by (regime, setup, pattern), ranked by risk-adjusted return, with downside-only risk figures; honors `view` (Episodes/Pooled) and `as_of`
- Extended `GET /api/research/samples` with `kind=regime-setup-pattern` cohort; drill-down total equals study-row `n` same-instant in both modes (count-coherence keystone)
- Added `/research` frontend: five forward-return columns on the leaderboard (sortable, NA-last, colour-graded), a "Realized forward returns" panel on the stock detail page, and a new Regime × Setup × Pattern study section with its own Episodes/Pooled toggle, sortable table, and N= chips opening samples in a new tab
- Made `/research` page sections load independently (each section has its own fetch + skeleton state so a slow event-study computation does not block the rest of the page)
- Verified 14 required-still-passing journeys green (byte-identity tests + live API checks); COHERENCE-PASS; review PASS; QA UI-PASS

## What's left

- Journey J-72 (Research page loads fast — event-study cache) failing — held pending full suite GREEN (no J-72 assertion failed; `test_db.py` expected-tables needs `event_study_cache` added)
- Journey J-75 (Forward returns on leaderboard and stock detail 1/5/10/20/60d) failing — held pending full suite GREEN (no J-75 assertion failed; suite failure is in unrelated tests)
- Journey J-77 (Research — returns by regime × setup × pattern) failing — held pending full suite GREEN; the `_rsp_rank_key` two `0.0` sort-sentinel literals in `research.py:1435-1436` must be replaced with a named constant to clear `test_no_magic_numbers.py`
- `test_db.py::test_create_all_produces_expected_tables` — add `event_study_cache` to the expected-tables set (2 lines)
- `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` — remove two `0.0` float literals from `_rsp_rank_key` in `research.py`; replace with a named module-level sentinel constant or restructure the sort key
- Journey J-22 (Transparent expanded universe ~500 names) — blocked-NA, data-walled (non-vetoing)
- Journey J-23 (Multi-timeframe bars — intraday seed + pipeline) — blocked-NA, data-walled (non-vetoing)
- Journey J-24 (Timeframe selector on the stock chart) — blocked-NA, data-walled (non-vetoing)

## Next step

Dispatch a lean consolidation iteration (iter-21) that fixes exactly these two suite failures and re-runs the full suite to green — no new feature work: (1) add `event_study_cache` (or `'event_study_cache'`) to the `SNAPSHOT_TABLES` / appropriate expected-tables group in `apps/backend/tests/test_db.py`; (2) replace the two `0.0` sort-tie sentinels in `research.py:1435-1436` `_rsp_rank_key` with a named module-level constant (e.g. `_RANK_NA_SENTINEL`) or restructure so no float literal is present — confirm `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` passes; (3) re-run the FULL backend suite (~790 tests) via the pump (nohup background) and gate iter-21's GOAL_ACHIEVED candidacy on the flushed terminal summary line being 0 failed. The goal-evaluator must NOT block on the in-flight suite. Re-assert J-77 byte-identity (the existing iter-20 cluster test) once after the research.py fix since it touches calc code. After the suite is green with COHERENCE-PASS, iter-21 is the GOAL_ACHIEVED candidate — J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-what-to-click.md`:

*(what-to-click.md not present for this iteration — full-depth QA was via the dedicated test cluster)*

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-review.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-user-visible-changes.md |
| UI surface map | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-ui-surface-map.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-20/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
