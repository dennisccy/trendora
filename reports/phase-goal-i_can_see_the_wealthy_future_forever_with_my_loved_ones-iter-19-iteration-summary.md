# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-15
**Iteration:** 19

## In plain words

**What you can do now:** See today's market regime and top-ranked stocks on a dashboard with a full-history indexes chart that opens on the full available period by default; open any stock for a full explainable score breakdown with a regime-banded price chart and a crosshair hover box showing exact open, high, low, close, volume, and moving-average values per bar; use a calendar to step back to any past snapshot date or press arrow keys to scrub between dates; open any historical link in a new tab and see that date's data immediately, with no flicker; sort and search the stock leaderboard by any column; filter by theme and expand each theme's member stocks as dated links; browse the Sectors leaderboard with every ETF named and mapped to its universe; run walk-forward backtest evidence with control groups; explore factor effectiveness and overlap-honest event studies; click any sample count to open the exact stored observations; save stocks to a watchlist; and manage price-data imports with live progress, instant run history, stage-aware resume, per-date failure isolation, a compact multi-hue availability heatmap, reliable multi-month backfill, and a deliberate range-scoped data-removal flow.

**What changed this time:** Opening a historical date link now shows the correct data right away — there is no longer a brief flash of today's figures before the past date loads. This fix applies whether you deep-link, reload, open in a new tab, or navigate in-app from another historical page. Separately, the Dashboard's market-indexes chart now opens on the full available history (going back to 2021) by default instead of the previous six-month window.

**What's next:** Next the product will gain three backend improvements: faster research lab queries, forward-return columns (1, 5, 10, 20, and 60 days) on the stock leaderboard and individual stock pages, and a ranked regime-by-setup-by-pattern study table in the Research Lab. After those land the goal will be achieved again.

## Headline

No as-of date-flash (synchronous URL hydration) + dashboard indexes defaults to All; 9/9 browser QA PASS.

## Direction

**Signal:** improving
**Why:** J-73 and J-78 both moved from failing to passing this iteration. J-73 is the most critical one — it touched the core date-state code that drives every historical page — and it passed all six arrival-mode checks including post-hydration URL assertions. The required-still-passing set (J-18/J-43/J-50/J-13/J-44/J-49/J-42) all remained green, confirming no regression from editing the date-state core. Three unbuilt backend journeys (J-72/J-75/J-77) remain, targeted for iter-20 at full depth with the full test suite as the gate.

**Trend (last 5 iters):**
- Newly passing this iter: J-73, J-78
- Newly passing in last 5 iters total: J-68, J-69 (iter-15); J-70, J-71 (iter-16); J-74, J-76 (iter-18); J-73, J-78 (iter-19)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5 (iter-17 — environment failure, Chrome unavailable; no code failure)

**Latest evaluator reasoning:** "The two lean targets both land and verify cleanly. J-78 (dashboard major-indexes chart defaults to 'All') is a one-line `config.yaml` change with no code literal; J-73 (no as-of date-flash via synchronous `?asof` URL hydration) is a lazy `useState` initializer on the EXISTING single global as-of state — no second date state, sole `?asof` owner and the iter-2 `searchKey`/`restored` guards preserved. Browser-QA 9/9 PASS with post-hydration `window.location.href` assertions across all six J-73 arrival modes; required-still-passing J-18/J-43/J-50/J-13/J-44/J-49/J-42 all PASS; coherence COHERENCE-PASS. NOT GOAL_ACHIEVED because J-72, J-75, J-77 remain unbuilt (failing) — three buildable, non-data-dependent Must-haves of the appended J-72..J-78 extension."

## What was done

- Changed `config.yaml` `index_chart.default_range` from `"6M"` to `"all"` — a valid preset already in the list, no Python or frontend code change, no hardcoded literal added anywhere (J-78)
- Added a lazy `useState` initializer `readAsofFromUrl()` to the single global as-of state in `asof-provider.tsx` so a historical `?asof=D` URL seeds the state synchronously on first mount, eliminating the latest→D flash on arrival (J-73)
- Fixed the degrade branch to also call `setAsOf(null)` (not just strip the URL param) so a synchronously-seeded-but-unknown date cannot stick — invalid→latest, no fabricated date
- Preserved the iter-2 `searchKey` serialize dependency and the `restored` single-restore guard; asof-provider remains the sole `?asof` reader/writer with exactly 4 `useState` hooks (no second date state)
- Added 2 backend unit tests locking in that `default_range="all"` validates and resolves to full history, and that a non-preset value is still rejected; 124 targeted backend tests green, `tsc --noEmit` clean
- Verified 9/9 browser QA PASS — post-hydration `window.location.href` asserted across all 6 J-73 arrival modes (deep link, reload, new tab, in-app nav, latest, invalid-degrade); coherence COHERENCE-PASS; review PASS

## What's left

- Journey J-72 (Research / Setup & Pattern Lab event-study performance + cache) failing — unbuilt, non-data-dependent
- Journey J-75 (Forward returns 1/5/10/20/60-day on the stock leaderboard and stock detail, from the stored forward_returns table) failing — unbuilt, non-data-dependent
- Journey J-77 (Research lab ranked regime × setup × pattern combinations study, count-coherent with the N= sample chips) failing — unbuilt, non-data-dependent
- J-22 / J-23 / J-24 remain data-walled (unknown) — non-halting per goal.md; no code change expected, would need a live provider fetch

## Next step

Dispatch the backend cluster **J-72 / J-75 / J-77 at FULL depth** (the audit step earns its cost on backend research-module work with hard property gates): J-72 — Research / Setup & Pattern Lab event-study perf + cache: hard byte-identity guard on cached-vs-uncached figures (a performance property, never a recompute), reads the persisted aggregate. J-75 — Forward returns 1/5/10/20/60-day on the stock leaderboard + stock detail: served from the stored `forward_returns` table, no-lookahead/no-recompute gate (returns use only bars dated > D), figures must match the leaderboard. J-77 — Research returns by regime × setup × pattern (ranked combinations study): a pure grouping of the SAME enriched event-study observation set (additive `_event_study_members` enrichment per the memory note), count-coherent with the J-64/J-65 N= chip drill-downs. Because they touch backend code, the full ~790-test pytest suite becomes a gate — hand it to the pump and gate the evaluator on the flushed summary line (never block the evaluator dispatch on the in-flight suite). After J-72/J-75/J-77 close green with no regression and coherence clean, the next evaluation is a GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-19/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
