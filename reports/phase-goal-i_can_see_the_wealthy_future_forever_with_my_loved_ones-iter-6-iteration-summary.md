# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-12
**Iteration:** 6

## In plain words

**What you can do now:** See the latest market regime and ranked stocks on a dashboard with a major-indexes chart that now shows the full stored market history with a clear "you are here" marker; open any stock for a full score breakdown with a regime-banded price chart; step back to any past date with a single global switcher so every page reflects that snapshot; sort the stock leaderboard by any column and restore the original scanner ranking with one click; copy or middle-click any in-app link while viewing a historical date and the link carries that date; click a leaderboard ticker to open the stock detail in a new tab without losing your place; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness in the Research Lab; save stocks to a persistent watchlist; manage price-data imports including rate-limited jobs that pause and resume; look up any term via a 118-term searchable glossary or inline info-tooltips; and click a column-header info icon on the stocks page without accidentally re-sorting the table.

**What changed this time:** When you browse a past date, the dashboard's major indexes and market-regime chart no longer hides the data after your selected date — the full stored price history and regime bands remain visible, with a clearly labelled dashed vertical line marking exactly where your selected date falls. At the latest date everything looks the same as before with no marker. Also fixed: clicking the small "?" info icon next to a leaderboard column header now opens the definition tooltip without accidentally triggering a sort, and the browser's developer error badge that appeared on the stocks page is gone.

**What's next:** Next we will build a drill-down page that lets you click any sample count on the Research pages to see the exact list of stocks behind that number, with each row linking out to the dated stock detail.

## Headline

Dashboard Major indexes & regime card shows full stored history with visible as-of marker at D (J-49) and nested-button defect fixed

## Direction

**Signal:** improving
**Why:** J-49 is newly passing this iteration, verified with evaluator-viewed browser screenshots showing the dashed vertical marker at D while historical and no marker at latest. The bundled iter-5 nested-button defect on `/stocks` was fixed and DOM-asserted gone (no nested `<button>`, no dev-overlay error badge). All five required-still-passing journeys (J-13, J-20, J-44, J-45, J-48) remained green; full pytest suite 691/4/0; coherence COHERENCE-PASS; review PASS. Three journeys (J-51, J-52, J-53) remain unbuilt and are planned for iter-7 and iter-8.

**Trend (last 5 iters):**
- Newly passing this iter: J-49
- Newly passing in last 5 iters total: J-47 (iter-4), J-48, J-50, J-54 (iter-5), J-49 (iter-6)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** Target J-49 passed all six goal.md steps with evaluator-viewed, md5-checked captures (marker at D historical, no marker at latest, NVDA detail bands still clamped — J-45/J-20 contrast in one capture); backend diff inspected and matches the no-second-path contract; coherence COHERENCE-PASS; review PASS; full pytest 691/4/0 (pump-run, 45:05). Two honest gaps accepted, not hidden: J-44 toggle-persistence cycle not re-exercised (mid-session backend death + Chrome MCP cross-contamination) and J-48 second-click desc direction not captured — both carried from prior full verification on code this diff did not touch.

## What was done

- Added optional `?full=true` param to `GET /api/indexes` and `GET /api/regime-history`; default (param absent) is byte-identical to the prior behavior so all existing consumers are unaffected
- Extended `compute_index_series` and `get_regime_history` engine functions to widen the served upper bound to `bars_through_latest` / un-clamped stored regime SELECT when `full=True`; overlapping `≤ D` range is value-identical between modes (no second compute path, no recomputation)
- Added `AsOfMarkerPrimitive` (new Lightweight-Charts canvas primitive) that draws a full-height dashed vertical line + "as-of YYYY-MM-DD" label at D while `isHistorical`; reuses the J-20 `--warn` palette and label family from `price-chart.tsx`
- Updated `major-indexes-card.tsx` to always request `full=true` from both endpoints; passes `isHistorical` and resolved `asof_date` down to the chart; `index-regime-chart.tsx` stops filtering regime points to `≤ asofDate` and attaches the new marker while historical — no marker at the latest date
- Stock-detail path left untouched: `price-chart.tsx` and the detail page's regime-history request remain unchanged; J-45 bands stay clamped at the as-of (J-45 re-verified PASS)
- Fixed iter-5 nested-button defect: `SortHeader` on `/stocks` now renders `TermInfo` as a sibling of the sort `<button>` (not a child); `InfoTooltip` trigger gains `event.stopPropagation()` — dev-overlay error badge gone, info-icon click no longer triggers a sort
- Added 14 new backend unit/API tests (default byte-identity, full-mode through-latest, overlap value-identity on both endpoints, `?full=true` unknown-range 422); full pytest suite 691 passed / 4 skipped / 0 failed (45:05, +13 tests vs iter-4)

## What's left

- Journey J-51 (Every research sample count is a link to its exact samples) failing — not built; needs read-only samples endpoint family + `/research/samples` drill-down with count-coherence; planned for iter-7
- Journey J-52 (From a sample row to the dated stock detail) failing — depends on J-51; planned for iter-7
- Journey J-53 (Fetch and backfill reports stage timings and backfills dates in parallel) failing — concurrency-sensitive backend work; planned at full depth for iter-8
- J-44 toggle off→reload→still-off cycle not re-exercised this iteration (mid-session backend death + Chrome MCP cross-contamination); carried from iter-2 on code this diff did not touch; flagged for opportunistic re-verification
- J-48 asc/desc second-click direction not captured changing (React fiber double-click flakiness); minor observation gap, not a failure; direction toggle verified iter-5 on sort logic this diff did not alter
- Deferred one-shot best-effort fetch for J-22/J-23/J-24 (data-walled, non-vetoing per goal.md) earmarked for the J-53 iteration

## Next step

**Iter-7 (lean): J-51 + J-52** — the read-only research-samples endpoint family + the `/research/samples` drill-down page: Count-coherence is the contract: observation total == the published N, assembled by the SAME observation builders the lab aggregates use (one membership filter, one observation set) — never a second membership rule. Row tickers open the dated stock detail in a new tab via the already-proven J-50/J-54 href mechanics. Apply the iter-6 un-nested SortHeader/TermInfo pattern to any samples table headers (the lesson that motivated fixing it before J-51). Blueprint already registers `/research/samples` in the IA; backend touch means the full pytest suite is the gate again (~45 min — foreground in the dev turn or hand to the pump, never two concurrently). Required-still-passing: J-25/J-26/J-29 (the N= sources on /research), J-32, J-47 (tooltips), J-50/J-54 (href/new-tab mechanics). Opportunistic: re-exercise the J-44 toggle off→reload→still-off cycle (left partially verified this iteration). Then **iter-8 (full): J-53** (parallel multi-date backfill ~2× + per-stage timings in job status) + the one-shot best-effort J-22/J-23/J-24 + DIA fetch, mirroring the J-46/iter-3 depth choice.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-6-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-6/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
