# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-12
**Iteration:** 5

## In plain words

**What you can do now:** See the latest market regime and ranked stocks on a dashboard with a major-indexes chart; open any stock for a full score breakdown with a regime-banded price chart; step back to any past date with a single global switcher so every page reflects that snapshot; sort the stock leaderboard by any column (ticker, sector, score, setup) and restore the original scanner ranking with one click; copy or middle-click any in-app link while viewing a historical date and the link carries that date so the recipient lands on the same snapshot; click a leaderboard ticker to open the stock detail in a new tab without losing your place on the leaderboard; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness in the Research Lab; save stocks to a persistent watchlist; manage price-data imports including rate-limited jobs that pause and resume; and look up any term via a 118-term searchable glossary or inline info-tooltips.

**What changed this time:** Three improvements landed at once. You can now sort the leaderboard by any column — click any header to re-order, click it again to reverse, click the rank column to get back to the scanner's original order. No scores or values change when you sort; it is purely a view re-arrangement. Every in-app link now carries the selected historical date in it, so middle-clicking, ctrl-clicking, or copying and sharing any link while browsing a past date will take anyone who opens it to that same dated view. Leaderboard tickers now open the stock detail in a new tab, so the leaderboard stays exactly as you left it — same filters, sort, scroll position, and date — while you look at the stock.

**What's next:** Next we will make the dashboard's major-indexes and market-regime chart show the full stored history regardless of the current date selection, with a marker on the chart indicating where the selected date falls.

## Headline

Sortable leaderboard columns, app-wide dated hrefs, and new-tab ticker links (J-48 / J-50 / J-54) — all three land and pass browser QA

## Direction

**Signal:** improving
**Why:** This iteration opened the new J-48..J-54 extension batch and immediately passed three of the seven journeys (J-48 sortable leaderboard, J-50 href-embedded `?asof`, J-54 new-tab tickers). All ten browser-QA tests passed, the frontend-only diff was evaluator-verified (zero backend files touched), and no regressions or anti-goal violations occurred. Four extension journeys (J-49, J-51, J-52, J-53) are newly recorded as failing but were explicitly deferred by the spec — they are queued targets, not regressions. The known minor defect (nested `<button>` in `SortHeader`) is non-blocking and queued for iter-6.

**Trend (last 5 iters):**
- Newly passing this iter: J-48, J-50, J-54
- Newly passing in last 5 iters total: J-47 (iter-4), J-48, J-50, J-54 (iter-5)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** All three targets (J-48 sortable leaderboard, J-50 href-embedded `?asof`, J-54 new-tab tickers) landed and pass with verified evidence, and all seven required-still-passing journeys held — the evaluator independently confirmed the frontend-only diff (8 files, 216+/26-, zero `apps/backend/`), the pure view-transform sort comparators, and the single `useAsOfHref()` author of every `?asof` href. One minor defect was found that QA missed: the new `SortHeader` wraps `TermInfo` (whose `InfoTooltip` trigger is a `<button>`) inside its own `<button>` — invalid nested-button DOM that matches the new "1 error" Next dev-overlay badge visible on the iter-5 `/stocks` captures. Extension journeys J-49/J-51/J-52/J-53 remain unbuilt, so the goal is not yet achieved.

## What was done

- Added `useAsOfHref()` hook to `asof-provider.tsx` as the single canonical author of `?asof` query params in every in-app link — merges into existing query strings, preserves hash fragments, emits clean path at latest, never fabricates a date
- Applied the hook to all 10 sidebar nav entries, leaderboard row links, stock-detail back links, scanner-runs links, research subject links, and watchlist ticker links (8 frontend files total, zero backend files touched)
- Added client-side stable sort memo to `/stocks` leaderboard: 7 sortable column headers with asc/desc toggle, single visible sort indicator, `#` restores stored scanner rank, filter-then-sort compose, ties resolved by stored-rank index
- Added `target="_blank" rel="noopener noreferrer"` to leaderboard ticker anchors only; href uses the J-50 helper so new tabs land on the dated detail
- Verified 10/10 browser-QA tests pass; re-verified 7 required-still-passing journeys (J-02 with sort active, J-05, J-06, J-13, J-16 with sort active, J-18, J-43 reload + invalid-param degrade) and 3 new journeys (J-48, J-50, J-54)
- `tsc --noEmit` clean; 22 extracted pure-logic tests pass (14 for `useAsOfHref` merge cases, 8 for stable sort memo); review PASS, coherence COHERENCE-PASS

## What's left

- Journey J-49 (Major indexes and regime card shows full history — as-of is a marker, not a clamp) failing — deferred to iter-6; requires clamp-optional serving on `GET /api/indexes` + `GET /api/regime-history` plus a vertical as-of marker on the dashboard card
- Journey J-51 (Every research sample count is a link to its exact samples) failing — deferred to iter-7; needs a new read-only samples endpoint family and `/research/samples` drill-down page
- Journey J-52 (From a sample row to the dated stock detail) failing — depends on J-51; planned for iter-7
- Journey J-53 (Fetch and backfill reports stage timings and backfills dates in parallel) failing — concurrency-sensitive backend work; planned at full depth for iter-8
- Known minor defect: `SortHeader` nests `TermInfo`'s `InfoTooltip` `<button>` inside its own `<button>` — invalid DOM (React nesting error, visible as "1 error" dev-overlay badge on `/stocks`), info-icon click bubbles into a sort; fix queued for iter-6 bundle
- Deferred one-shot best-effort fetch for J-22/J-23/J-24 (data-walled, non-vetoing) earmarked for the J-53 iteration

## Next step

Iter-6 at lean depth, per the decomposer's batch plan: target J-49 (dashboard Major-indexes & regime card renders the full stored history regardless of the global as-of, with a vertical as-of marker when historical; clamp-optional serving on the existing `GET /api/indexes` + `GET /api/regime-history` endpoints — same stored values, no second path; J-45 stock-detail bands stay clamped, explicitly NOT amended). Required-still-passing should include J-44, J-45, J-20, J-13. Because the clamp-optional serving touches `apps/backend/` read endpoints, the full backend pytest suite becomes a gate (~35–46 min — hand to the pump, never two concurrently). Bundle the nested-button fix: render the header info affordance outside the sort `<button>` (sibling, not child) or use a non-button trigger, and have browser-QA confirm the `/stocks` dev-overlay error badge is gone and that clicking the info icon no longer changes the sort. Then iter-7 → J-51+J-52 (samples endpoint family + `/research/samples`), iter-8 → J-53 at full depth + the deferred one-shot J-22/J-23/J-24 + DIA best-effort fetch.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-5/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
