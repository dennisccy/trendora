# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and fully warmed (the first cold load of the Factor Lab all-factors table takes ~25–120 s; subsequent requests are instant from cache)
- No login required for Research pages

---

## Verification Steps

1. Navigate to `http://localhost:3255/research/factor-lab`
   - **Expect:** A table appears with multiple rows — one per catalog factor. Each row shows a factor name, family, a Rank-IC value with sample count (N), and a risk-adjusted figure. No dropdown to select a single factor is visible anywhere on the page.
   - **Broken looks like:** A blank page, a spinner that never resolves, or a "Select a factor" dropdown shown instead of the table.

2. Look at the column headers of the table and click the "Rank-IC" column header once
   - **Expect:** The rows immediately reorder so the factor with the highest Rank-IC value appears at the top. Any factors showing "NA" (zero observations) remain at the very bottom of the list.
   - **Broken looks like:** The rows do not change order, or NA rows appear mixed in among numeric rows.

3. Click the "Rank-IC" column header a second time
   - **Expect:** The sort reverses — the factor with the lowest numeric Rank-IC value is now at the top. NA rows remain at the bottom regardless of direction.
   - **Broken looks like:** Clicking a second time has no effect, or NA rows jump to the top.

4. Click anywhere on any factor row in the table (the first row is fine)
   - **Expect:** A full-width panel expands directly below that row showing a decile breakdown table with 10 rows labeled D1 through D10. Each decile row shows a mean return, a risk-adjusted value, and an N count. The expand row itself shows a visual cue (arrow or highlight) that it is open.
   - **Broken looks like:** Nothing happens on click, or the entire page reloads.

5. Inside the expanded decile panel, find the "N=" chip in the D1 row (e.g., "N=145") and note the number, then click it
   - **Expect:** A new browser tab opens showing the Research Samples page. The sample count visible on that page matches the number from the chip (e.g., 145). The Factor Lab tab remains open and unchanged.
   - **Broken looks like:** No new tab opens, the same tab navigates away from Factor Lab, or the sample count on the Samples page does not match the N value.

6. Return to the Factor Lab tab and click the same expanded row again to collapse it
   - **Expect:** The decile panel disappears and the row returns to its compact one-line height. The table looks exactly as it did before the row was expanded.
   - **Broken looks like:** The panel stays open, or other rows disappear.

7. In the controls bar at the top, locate the horizon selector (buttons or dropdown labeled with time periods such as "5d", "10d", "20d", "60d") and click a different horizon than the one currently selected
   - **Expect:** The Rank-IC values and risk-adjusted figures in the table rows update to reflect the new horizon. All rows update at once (not one at a time). No page reload occurs.
   - **Broken looks like:** Values do not change after selecting a new horizon, or only some rows update.

8. Scroll through the entire page from top to bottom and check for any table or section with regime labels (e.g., "Bull", "Bear", "Risk-Off") or a "Regime Effectiveness" heading
   - **Expect:** No market-regime effectiveness table exists anywhere on the page. The only table on the page is the all-factors comparison table.
   - **Broken looks like:** A "Regime Effectiveness" or "by_regime" table section appears below the all-factors table.

---

## What "Working Correctly" Looks Like

- The Factor Lab page loads a multi-row table (no dropdown, no single-factor body) showing every catalog factor with family, Rank-IC value+N, and risk-adjusted figure
- Clicking any column header instantly reorders the table, with NA values always sinking to the bottom
- Clicking a factor row toggles an in-place decile panel open and closed — no page navigation required
- Clicking a decile N= chip opens Research Samples in a new tab with a matching sample count
- Changing the horizon selector updates all rows at once
- No factor selector dropdown, no standalone RankIC card, and no regime effectiveness table appear anywhere on the page

## Common Issues

- **Table never loads / spinner runs indefinitely:** The first cold load of the all-factors table triggers a backend compute that can take up to 120 seconds. Wait at least 2 minutes before concluding something is broken. Check that the backend is running (`curl http://localhost:8000/health` or the configured backend URL).
- **Table loads but shows only 1 row:** The frontend may be in single-factor mode — this means the all-factors flag is not being sent. Reload the page and check the browser network tab for a request to `/api/research/factor-lab?view=all` or similar.
- **Sort click has no effect:** Ensure you are clicking the column header text itself (it is a button). If the sort indicator does not appear, the header may not have been registered as clickable — check the browser console for JS errors.
- **N= chip opens same tab instead of new tab:** The SampleLink is configured to open `target="_blank"`. If a browser pop-up blocker is active, allow pop-ups for `localhost:3255` and retry.
