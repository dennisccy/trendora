# Iteration Summary — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-13
**Iteration:** 13

## In plain words

**What you can do now:** See today's market regime and top-ranked stocks on a dashboard with a full-history indexes chart across five major benchmarks. Open any stock for a full explainable score breakdown with a regime-banded price chart. Step back to any past date with a single global switcher — that switcher is now a calendar popover that highlights only dates with real saved data, so you always know what is selectable. Share or open any link in a new tab to land on that same dated view. Sort the leaderboard by any column, search by ticker or company name, filter by theme, and browse each theme's complete member list. View the Sectors leaderboard with every ETF named and described, expandable to show exactly which stocks belong to it. Run walk-forward backtest evidence with control groups and return attribution. Explore factor effectiveness, multi-factor combinations, and setup/pattern event studies in the Research Lab, clicking any sample count to open the exact stored observations in a new tab. Save stocks to a persistent watchlist. Manage price-data imports with live progress, instant Run History entries, stage-aware resume that skips already-completed work, and per-date failure isolation. See at a glance, on the Data Manager page, a trading-day calendar heatmap showing how many symbols have data on each date and whether a portfolio snapshot was computed — and click any day to instantly prefill the job form's date inputs for a new fetch or backfill.

**What changed this time:** The Data Manager page now shows a new availability heatmap — a month-by-month calendar grid where each square represents a trading day, colored by how much price data exists for that day, with a ring marker on days that have a saved portfolio snapshot. Hovering a square shows the exact numbers. Clicking a square prefills the Start and End dates of the data-job form below it. The heatmap refreshes automatically after any job completes. Separately, the date-switcher in the top navigation bar changed from a plain dropdown list to a calendar popover: it shows only real snapshot dates as selectable, greying out all other days, with month navigation and a "Latest" button to return to the live view.

**What's next:** Next we'll make the event-study lab default to first-trigger episodes (collapsing consecutive same-stock signals into one observation) with the current pooled view one toggle away, closing the last open feature and completing the session.

## Headline

Per-date availability heatmap on /data (J-61) + as-of calendar popover replacing the flat select (J-62) — both newly passing, full backend suite green 767/4/0.

## Direction

**Signal:** improving
**Why:** Two Must-have journeys (J-61 and J-62) moved from failing to passing in this iteration, verified by 20/20 browser-QA tests, a 22/22 QA pass, and a GREEN full backend suite (767 passed / 4 skipped / 0 failed). The load-bearing single-date-state invariant holds — `asof-provider.tsx` is byte-unchanged, confirmed by the coherence auditor. J-63 is the sole remaining failing Must-have; J-22/J-23/J-24 stay data-walled blocked-NA (non-vetoing). Direction is healthy: iters 12 and 13 have each moved journeys forward with no regressions.

**Trend (last 5 iters):**
- Newly passing this iter: J-61, J-62
- Newly passing in last 5 iters total: J-59, J-60, J-66, J-67 (iter-12); J-61, J-62 (iter-13)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "Iter-13 (full depth) ships J-61 (per-date availability heatmap on `/data` via a new read-only `GET /api/data/availability`) and J-62 (as-of calendar popover replacing the flat `<select>`), both verified passing from primary evidence — evaluator-viewed heatmap + calendar screenshots, a diff-verified read-only availability derivation, and the byte-unchanged `asof-provider.tsx` that proves the single-date-state invariant holds. No anti-goal violation, COHERENCE-PASS, full backend suite GREEN (767 passed / 4 skipped / 0 failed). Not GOAL_ACHIEVED: J-63 (event-study first-trigger episodes) remains the last buildable failing Must-have; J-22/23/24 stay blocked-NA (data-walled, non-vetoing)."

## What was done

- Added `compute_availability()` read-only derivation in `data_manager.py` — for each SPY benchmark trading day, emits `{date, symbols_with_bars, total_symbols, snapshot_exists}` from the same stored bars and runs `compute_coverage` reads; no canonical value recomputed.
- Exposed `GET /api/data/availability` as one additive read-only route in `apps/backend/app/api/data.py`; all existing `/api/data` endpoints byte-unchanged.
- Added 4 unit tests (exact per-date counts, coverage-consistency, zero/sparse-day honesty, empty-DB) and 2 endpoint tests in the backend suite.
- Built `availability-heatmap.tsx` (new component): month-banded trading-day calendar grid with 6-step density color ramp, snapshot ring markers, legend, hover/focus readout, click-to-prefill and shift-click-to-range (writes `setStart`/`setEnd` only — never `setAsOf`), auto-re-fetch after any job completes.
- Built `asof-calendar.tsx` (new component) and rewrote `asof-switcher.tsx`: flat `<Select>` dropdown replaced by a month-grid calendar popover; selectable snapshot dates rendered as buttons, non-snapshot days as disabled spans; back/forward month nav clamped to oldest/newest stored month; "Latest" affordance; keyboard-operable (Tab/Enter/Escape); all selection routes through the existing `setAsOf` — `asof-provider.tsx` byte-unchanged.
- Mounted the heatmap on `/data` (`page.tsx`), wired `loadAvailability` to mount and job-completion events, wired `handleHeatmapPrefill` to job-form dates.
- Verified 20/20 browser-QA tests PASS and 22/22 QA test cases PASS; full backend suite GREEN 767/4/0.

## What's left

- Journey J-63 (Event study is overlap-honest — first-trigger episodes by default, pooled one toggle away) failing — last buildable Must-have; next iteration's target.
- J-22 (Transparent rule-based expanded universe ~500 names) — blocked-NA, data-walled (non-vetoing).
- J-23 (Multi-timeframe bars — intraday seed + pipeline) — blocked-NA, data-walled (non-vetoing).
- J-24 (Timeframe selector on the stock chart) — blocked-NA, data-walled (non-vetoing).

## Next step

Target **J-63** at **full** depth — the final buildable Must-have that closes the session.

J-63: the Setup & Pattern Lab (`/research`) defaults to a **first-trigger episode** view (consecutive same-symbol signal-days collapse into one observation), with the current pooled per-signal-day view one toggle away and **byte-identical to today's figures**. Both modes must disclose n, unique symbols, and episode count. Full depth is warranted: it is a backend research-module change with a hard byte-identity guard (the pooled toggle must reproduce the prior figures exactly), the episode collapse must come from the SAME observation builders (one membership rule, a deterministic stored-data-only grouping — never a recompute), and it must stay count-coherent with the J-64/J-65 `N=` samples drill-downs in both modes. Required-still-passing for that iter: **J-29** (event-study lab), **J-51/J-64/J-65** (samples drill-down count-coherence), and **J-25/J-26/J-32** (the other `/research` labs must read unchanged). After J-63 passes with no regression and a clean coherence audit, the session becomes a GOAL_ACHIEVED candidate (J-22/23/24 stay blocked-NA, non-vetoing).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-what-to-click.md`:

1. Navigate to `http://localhost:3835/data` — expect the Data Manager page with a new "Availability Heatmap" card visible below the Dataset Coverage panel, showing a month-by-month calendar grid with colored day cells and a legend.
2. Hover over any colored cell in the heatmap and hold for 1 second — expect the readout above the grid to update showing the exact date, symbols count, and snapshot flag.
3. Click any single day cell in the heatmap — expect the Job form's "Start date" and "End date" inputs to change to that date while the as-of switcher in the top bar remains unchanged ("Latest") and no `?asof=` appears in the URL.
4. Navigate to `http://localhost:3835/stocks` — expect the top-bar as-of control to be a button labeled "Latest" with a chevron icon, not a `<select>` dropdown.
5. Click the "Latest" button with chevron to open the as-of calendar, then click any highlighted snapshot date — expect the popover to close, the URL to gain `?asof=YYYY-MM-DD`, a historical badge to appear, and page data to reload for that date.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-dev.md |
| Review | PASS | reports/reviews/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-review.md |
| Browser QA | PASS | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-what-to-click.md |
| QA | PASS | reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-13/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/journey-history.json |
