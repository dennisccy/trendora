# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- See every factor in the catalog at a glance by navigating to Research → Factor Lab — the page now shows one row per factor (family, rank-IC value + sample count, downside risk-adjusted figure) instead of requiring selection from a dropdown first.
- Sort the factor table by any column (Factor, Family, Rank-IC, N, or Risk-adjusted) by clicking a column header — the table reorders instantly client-side, with factors that have too few observations always sinking to the bottom regardless of sort direction.
- Expand any factor row in place by clicking it (or pressing Enter/Space) to reveal that factor's full D1–D10 decile sort without leaving the page or re-loading data.
- Collapse an expanded factor row by clicking it again, returning the table to the compact summary view.
- Drill into the observation evidence for any decile by clicking the "N=" chip inside an expanded factor row — this opens the Research Samples view in a new browser tab showing the exact cohort of observations that produced that decile's figure.

---

## What Changed in the Visible UI

- The Research → Factor Lab page (`/research/factor-lab`) now opens to an all-factors comparison table (`FactorsTable`) with one row per catalog factor instead of opening to a blank/single-factor state with a dropdown selector.
- Each row in the all-factors table shows: factor label + direction hint, family, Rank-IC value + N (sample count), and downside risk-adjusted return for that factor's top decile.
- Each row header in the table is a clickable sort button (`FactorSortHeader`) — clicking the same header twice reverses the sort; factors with no reportable value always appear last.
- Expanded rows display the full decile breakdown (`DecileTable`) in a panel beneath the summary row — the same 10-bucket table the old single-factor view showed.
- The page subtitle now reads "Which factors actually sort future returns" reflecting the new multi-factor scope.
- The HorizonSelector (horizon dropdown) and the All-history / As-of date mode toggle remain in the controls bar — changing the horizon or toggling As-of updates all rows in the table simultaneously.
- The ResearchCaveat survivorship and descriptive warnings, the WarmingState indicator, the ResearchError panel, and the LabSkeleton loading placeholder are all still present on the page in their existing positions.

---

## What Old Behavior Changed

- Factor Lab dropdown removed: previously the user had to pick a single factor from a dropdown, then the page loaded that factor's rank-IC card, decile table, and per-regime effectiveness table. Now the page loads every factor at once — there is no dropdown, no single-factor body, and no rank-IC card as a separate card.
- Per-regime effectiveness table removed from this view: the market-regime breakdown table (`RegimeEffectivenessTable`) is no longer shown on the Factor Lab page. The underlying data is still computed by the backend, but it is not displayed anywhere on this page.
- First paint after a data change takes approximately 25 seconds: the first time the all-factors table is requested after the dataset changes, the backend scans and computes the full pool before responding. Subsequent loads (including other horizons and as-of dates after their first load) are instant from the cache. The old single-factor view had no comparable cold-compute delay for a full-page initial load.
- As-of mode at the earliest available date shows N = 0 for all factors: restricting to the oldest snapshot yields no completed forward returns, so the table correctly shows zero observations. This was not a visible behavior in the old single-factor view because a user had to explicitly select a factor to see its N.

---

## Not Visible Yet

- The `GET /api/research/factor-lab` endpoint's existing single-factor mode (`?factor=<key>`) is unchanged and still works — it is consumed internally by the Research Samples drill-down cohort links, but there is no direct user-facing route that shows the old single-factor layout anymore.
- The backend still computes the per-regime effectiveness table (`_regime_effectiveness` / `by_regime`) for single-factor requests — this data exists in the API response for direct API consumers but is no longer rendered anywhere in the UI.
