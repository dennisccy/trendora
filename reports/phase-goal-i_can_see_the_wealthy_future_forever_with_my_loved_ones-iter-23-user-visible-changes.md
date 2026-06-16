# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see how each theme's member stocks actually performed over the next 1, 5, 10, 20, and 60 trading days by navigating to `/themes` — the five forward-return columns appear directly in the leaderboard table alongside theme scores.
- Users can now sort the Themes leaderboard by any forward-return horizon (1d / 5d / 10d / 20d / 60d) by clicking the corresponding column header, reordering rows by realized returns without triggering a new server request.
- Users can now see each sector/industry ETF's own realized forward return at 1d / 5d / 10d / 20d / 60d by navigating to `/sectors` — the same five sortable, colour-graded columns appear on the Sectors leaderboard.
- Users can now cross-check a theme's or sector's forward return against the Backtest workspace and confirm they match exactly for the same date and horizon (both read from the same stored evidence).
- Users can now filter the Regime × Setup × Pattern table on `/research` by Regime, Setup, and Pattern using three "All"-default dropdowns, narrowing visible rows without reloading data.
- Users can now sort any numeric column on the Regime × Setup × Pattern table and see all rows displaying "NA" pushed to the bottom in both ascending and descending order, keeping meaningful values at the top.
- Users can now click the "N=" sample-count chip on every visible row of the Regime × Setup × Pattern table — including rows where no pattern was detected ("— (none)") — and open the exact underlying observation list in a new tab without receiving an error page.

---

## What Changed in the Visible UI

- The `/themes` leaderboard table now has five additional columns labelled with the forward-return horizons (e.g., 1d / 5d / 10d / 20d / 60d), each showing the equal-weight average return of the theme's member stocks, colour-graded green/red/neutral by sign.
- The `/sectors` leaderboard table now has the same five forward-return columns, each showing the sector/industry ETF's own realized return at that horizon, colour-graded the same way.
- The column headers for the new forward-return columns on `/themes` and `/sectors` are clickable sort controls; clicking once sorts ascending (NA last), clicking again sorts descending (NA last), and a third click restores the default served order.
- NA-honest cells appear as muted "NA" text on both leaderboards for any horizon where the forward data does not yet exist (e.g., near the latest available date or for ETFs/themes with no stored bars) — never a fabricated 0%.
- The `/research` Regime × Setup × Pattern section now shows three filter dropdowns (Regime / Setup / Pattern) in the section's existing controls row alongside the Episodes / Pooled toggle.
- The Regime × Setup × Pattern section on `/research` now opens in Pooled mode by default; the Episodes view is one click away via the existing toggle. All other sections on `/research` are unchanged and continue defaulting to Episodes.
- When all filter combinations produce no matching rows, the Regime × Setup × Pattern table shows an honest empty-after-filter state rather than a blank or broken layout.

---

## What Old Behavior Changed

- Regime × Setup × Pattern table sort (NA rows): previously a low-sample row whose raw value was a non-null number would float to the top when sorting, even though its cell displayed "NA". Now all displayed-NA rows consistently sink to the bottom in both sort directions.
- Research Regime × Setup × Pattern section default view: previously it opened in Episodes mode. Now it opens in Pooled mode (Episodes remains one click away). All other sections on `/research` still default to Episodes.
- Research samples drill-down for the combinations table (contract change): previously, requesting a `(regime, setup, pattern)` combination that was technically valid vocabulary but never appeared in the study returned an empty 200 response. Now it returns an error (4xx). This only affects the RSP combinations table's drill-down; clicking any visible chip (which always corresponds to an emitted combination) still works correctly. Other sample drill-downs (factor deciles, event-study slices) are unchanged.

---

## Not Visible Yet

- None. Every backend change made in this iteration is directly surfaced in the UI. The `forward_returns` field added to the Themes and Sectors API responses powers the new leaderboard columns; the samples-validation reconciliation powers the previously-erroring N= chip drill-downs.
