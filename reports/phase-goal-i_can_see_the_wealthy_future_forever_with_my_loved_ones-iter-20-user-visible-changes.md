# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see how every stock performed 1, 5, 10, 20, and 60 trading days after any historical scan date, by visiting `/stocks` — the five forward-return columns appear directly in the leaderboard table, colour-graded green (positive) or red (negative).
- Users can now sort the leaderboard on `/stocks` by any of the five forward-return columns (1d/5d/10d/20d/60d) by clicking the column header; the table re-orders client-side with NA values always sorted last.
- Users can now see the same five realized forward returns for a single stock on the Stock Detail page (`/stocks/[ticker]`) in a new "Realized forward returns" panel displayed above the price chart, for the resolved as-of date.
- Users can now explore which combinations of market regime, setup status, and detected chart pattern historically produced the strongest risk-adjusted forward returns, by scrolling to the new "Regime × Setup × Pattern" study table on `/research`.
- Users can now sort the Regime × Setup × Pattern study table by any column (n, mean, median, hit-rate, expectancy, risk-adjusted return) by clicking the column header; default order is the served risk-adjusted rank.
- Users can now flip the Regime × Setup × Pattern study between "Episodes" and "Pooled" views using its own toggle, independently of other study sections on `/research`.
- Users can now drill into the exact observations behind any Regime × Setup × Pattern row by clicking its `N=` chip, which opens `/research/samples` in a new tab showing the matching sample list with a count that exactly equals the published row count.
- Users can now watch each section of `/research` load independently; a slow event-study computation no longer blocks the Combination Lab or the new Regime × Setup × Pattern table from becoming interactive.

---

## What Changed in the Visible UI

- The `/stocks` leaderboard table now has five additional columns to the right of the existing score/rank columns: "1d", "5d", "10d", "20d", "60d" forward returns. Each cell is colour-graded; cells where no post-date return data exists display "NA" in muted text.
- The `/stocks/[ticker]` Stock Detail page now has a "Realized forward returns" card panel above the price chart, showing five tiles (one per horizon) colour-graded by sign. Near the latest date all five tiles show "NA" honestly.
- The `/research` page now has a new "Regime × Setup × Pattern" study section below the existing Event Study / Combination Lab sections. It contains a dense sortable table with columns: Regime, Setup, Pattern, N, Mean, Median, Hit-rate, Expectancy, and two downside risk-adjusted figures. Combinations with too few observations display NA + n. A survivorship-bias caveat banner is present. The section has its own Episodes/Pooled toggle.
- The `/research/samples` drill-down page now displays a meaningful heading when the cohort is a Regime × Setup × Pattern combination (e.g., "Bull / Trending / VCP — Pooled"), where previously this cohort type was unrecognized.
- The `/research` page's individual study sections (Combination Lab, Event Study, Regime × Setup × Pattern) each show their own loading skeleton; previously a slow event-study fetch could delay the whole page becoming interactive.

---

## What Old Behavior Changed

- Event Study (`/research`): previously recomputed figures on every page load (slow, ~28 seconds). Now serves from a self-refreshing cache (identical numbers, subsequent requests ~0.02 seconds). No change to the displayed figures.
- `/stocks` leaderboard: previously each stock row carried scores, setup status, patterns, and themes. Each row now additionally carries five realized forward returns. All existing values are unchanged — this is an additive extension.

---

## Not Visible Yet

- None. Every backend addition in this iteration has a corresponding UI surface: the new `/api/research/regime-setup-pattern` endpoint drives the new study table on `/research`; the extended `/api/research/samples?kind=regime-setup-pattern` cohort drives its drill-down; the new per-stock `forward_returns` field on `/api/stocks` drives the `/stocks` columns and the Stock Detail panel. The internal `EventStudyCache` database table is a speed optimization with no user-facing representation.
