# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (confirm with `curl http://localhost:8000/health`)
- No login required for Factor Lab (public research page)

---

## Verification Steps

1. Navigate to `http://localhost:3255/research/factor-lab`
   - **Expect:** The Factor Lab page loads with an all-factors table visible. No spinner persists beyond 10 seconds. No "Backend unavailable" or error banner is shown.
   - **Broken looks like:** Blank white page, a persistent loading spinner, or a "Something went wrong" message.

2. Look at the page controls area above the table for any horizon dropdown or "Select horizon" selector
   - **Expect:** No horizon dropdown exists anywhere on the page. The table already shows data across all horizons without requiring a selection.
   - **Broken looks like:** A `<select>` dropdown labelled "Horizon" or a set of radio buttons for "1d / 5d / 10d / 20d / 60d" is present.

3. Read the column header row of the all-factors table
   - **Expect:** You can see ten paired columns in the header: "Fwd 1d" followed by "MDD 1d", "Fwd 5d" followed by "MDD 5d", "Fwd 10d" followed by "MDD 10d", "Fwd 20d" followed by "MDD 20d", "Fwd 60d" followed by "MDD 60d". Scroll the table right if needed. Also confirm that the "Rank-IC" and "Risk-Adj" column headers each include "(20d)" in their text.
   - **Broken looks like:** Only one horizon's data columns are visible, or the "Rank-IC" header reads "Rank-IC" without any horizon label.

4. Click the "Fwd 1d" column header once, then click it a second time
   - **Expect:** First click: the table rows reorder instantly so the factor with the highest "Fwd 1d" value is in row 1; any factor showing "NA" in that column appears at the very bottom. No spinner. Second click: the order reverses (lowest "Fwd 1d" first); "NA" rows remain at the bottom.
   - **Broken looks like:** The table does not change order, a spinner appears, or "NA" rows move above numeric values.

5. Click the expand chevron (triangle or arrow icon) at the left edge of any factor row
   - **Expect:** A decile sub-grid appears below that factor row with exactly 10 rows labelled D1 through D10. The sub-grid columns include "Fwd 1d / MDD 1d" through "Fwd 60d / MDD 60d" — all five paired horizon columns. Each decile row shows a "N=" chip on at least one forward-return cell.
   - **Broken looks like:** Only one horizon's decile data appears, fewer than 10 decile rows, or the sub-grid shows a blank or error state.

6. In the expanded decile sub-grid, locate the D5 row, find the "Fwd 5d" cell, note the exact N= chip value (e.g., "N=4,512"), then click that chip
   - **Expect:** A new browser tab opens automatically. The new tab navigates to `/research/samples` with query parameters identifying the factor, horizon=5d, and decile=D5. The "Total observations" figure on the Samples page matches the N= chip value you noted (e.g., 4,512). No 404 error page.
   - **Broken looks like:** The click does nothing, the tab opens but shows a 404 or error, or the observation count on the Samples page does not match the chip value.

7. Switch to "All-history" mode using the global date control in the top navigation bar, then look at the N= chip values in the decile sub-grid
   - **Expect:** The N= chip values in the decile grid change (in All-history mode counts are larger because all historical data is included). No second date picker or date input appears inside the Factor Lab page body — the only date control remains in the top navigation bar.
   - **Broken looks like:** N= values do not change at all, a second date picker appears inside the Factor Lab content area, or the page shows an error on mode switch.

8. Scroll the all-factors table and count the factor rows
   - **Expect:** At least 11 factor rows are visible (e.g., MeanRev, Seasonality, and others). Every row has a factor name — no rows display "Loading…" or a blank name.
   - **Broken looks like:** Fewer than 11 factor rows are present, or some rows show "undefined" or blank names.

---

## What "Working Correctly" Looks Like

- The Factor Lab page shows a wide table with 10 paired horizon columns (5 Fwd + 5 MDD) — no dropdown to switch horizon
- Expanding any factor row reveals 10 decile rows (D1–D10) each with all-horizon paired columns and clickable N= chips
- Clicking a N= chip opens the Research Samples page in a new tab showing the matching observation count
- Rank-IC and Risk-Adj column headers display "(20d)" as a static label
- The global as-of date control is the only date control on the page

## Common Issues

- **Persistent spinner or blank table:** Check that the backend is running (`curl http://localhost:8000/health`). The first Factor Lab load may take a few seconds if the cache is cold.
- **N= chip click opens wrong count:** Confirm you are reading the chip value before clicking — the number shown in the chip must equal the "Total observations" on the Samples page.
- **Decile grid does not expand:** Try clicking directly on the chevron/triangle icon at the far left of the factor row; the expand target is small.
- **No "(20d)" in Rank-IC header:** This indicates the old label is still in place — the column-label fix may not have been deployed.
