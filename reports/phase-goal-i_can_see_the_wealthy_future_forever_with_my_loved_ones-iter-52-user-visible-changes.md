# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see every catalog factor's top-decile forward return AND its paired max-drawdown at all five horizons (1, 5, 10, 20, 60 trading days) simultaneously in one table on `/research/factor-lab` — without ever selecting a horizon.
- Users can now expand any factor row on the Factor Lab all-factors table to reveal the full ten-decile grid (D1 lowest … D10 highest), each decile showing paired forward-return and max-drawdown figures at every horizon plus a per-decile sample count.
- Users can now sort the Factor Lab table by any per-horizon forward-return or max-drawdown column (clicking the column header) to rank factors by edge or risk at that specific horizon; cells with no data (NA) always sink to the bottom.
- Users can now click the "N=<count>" chip on any decile/horizon forward-return cell to open the Research Samples page in a new browser tab, scoped to that exact (factor, horizon, decile) cohort; the total shown there will always match the chip count.
- Users can now read max-drawdown severity at a glance: max-drawdown cells are colour-graded from mild (lighter) to severe (deeper red) using the app's existing colour scale.

---

## What Changed in the Visible UI

- The single-horizon dropdown (`<select>`) on the Factor Lab page has been removed. There is no longer a control to choose "view horizon 1d" or "view horizon 60d" — all horizons are shown at once.
- The all-factors table now has ten additional data columns: a paired "Fwd {h}d" (forward return) and "MDD {h}d" (max-drawdown) column for each of the five configured horizons (1d, 5d, 10d, 20d, 60d), each showing the factor's top-decile cohort aggregate. The table scrolls horizontally on narrow screens to accommodate all columns.
- The "Rank-IC" and "Risk-adjusted" columns in the all-factors table are now labelled with the fixed default horizon (e.g., "Rank-IC (20d)") rather than reflecting the previously-selected horizon.
- Max-drawdown cells appear beside each forward-return cell in both the all-factors table and the expanded decile grid, colour-graded by drawdown severity using the app's existing `mdd-color` tokens. A deeper drawdown reads as a more intense red.
- Expanding a factor row now reveals an all-horizon decile grid (D1–D10 rows × all-horizon paired columns) instead of a single-horizon decile list. Each forward-return cell carries a per-`(factor, horizon, decile)` "N=" chip.
- The expanded decile grid shows a "Factor range" column at the default horizon; hovering a forward-return cell shows that horizon's own factor range in a tooltip.

---

## What Old Behavior Changed

- **Factor Lab horizon control:** Previously the page showed data for one user-selected horizon at a time; switching horizon triggered a new fetch and re-rendered the table. Now all horizons are fetched in a single request and rendered as paired columns; the horizon selector is gone entirely.
- **Factor Lab API request:** Previously `fetchFactorLabAll` was called with a horizon parameter. Now the frontend sends `?all=true` with no horizon; the response shape changed to a `by_horizon` block per factor (the old top-level `horizon` field is gone; `deciles` is replaced by per-horizon decile tables inside `by_horizon`). Any pre-existing cached Factor Lab response is automatically discarded and recomputed on the first load after this change.
- **Rank-IC and risk-adjusted reporting horizon:** Previously these figures reflected the user-selected horizon. Now they are always computed at the configured default horizon (20 days) and are labelled accordingly; the user can no longer change which horizon these statistics reflect.
- **Expandable decile sort:** Previously expanding a factor showed that factor's deciles for the currently-selected horizon only. Now the expansion always shows all-horizon paired columns regardless of any sort state.

---

## Not Visible Yet

- J-110 (Regime Lab at `/research/regime-lab`), J-111 (Phase & Severity Lab at `/research/phase-severity-lab`), and J-112 (Regime × Phase × Factor at `/research/regime-phase-factor`) are implemented in a future iteration; no corresponding UI page or navigation entry exists yet.
- The single-factor Factor Lab API response (`GET /api/research/factor-lab?factor=&horizon=`) now additively includes `mean_max_drawdown` per decile, but this endpoint is used only by the Research Samples drill-down; no dedicated single-factor Factor Lab UI view exposes this field separately from the all-factors table.
