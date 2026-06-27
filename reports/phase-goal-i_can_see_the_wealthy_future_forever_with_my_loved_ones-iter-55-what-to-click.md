# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255`
- The database contains at least one completed scanner run with forward-return data (the combination table is not empty)
- No credentials required — all research pages are read-only and publicly accessible on a local instance

---

## Verification Steps

1. Navigate to `http://localhost:3255/research`
   - **Expect:** The Research hub page loads and a tile labelled "Regime × Phase × Factor" (with a grid-of-squares / Boxes icon) is visible in the LABS section alongside the existing "Regime Lab" and "Phase & Severity Lab" tiles.
   - **Broken looks like:** No such tile in the list, or the page shows "Backend unavailable" / blank.

2. Click the "Regime × Phase × Factor" tile
   - **Expect:** The browser navigates to `http://localhost:3255/research/regime-phase-factor`. The page loads and shows: a factor selector dropdown at the top, an As-of / All-history toggle, a table with rows (each row has three leftmost columns for regime decile, severity decile, and factor decile), and a Previous / Next pagination footer at the bottom.
   - **Broken looks like:** 404 page, blank screen, or the page renders but shows "could not load" as the final state with no table rows.

3. Click the factor selector dropdown and select a factor different from the default (e.g. if the default is "leadership_score", select "entry_quality_score")
   - **Expect:** The combination table re-renders. The n values on the first visible row are different from the values shown before you switched. No error message appears.
   - **Broken looks like:** The table shows identical rows after the switch, or a "Backend unavailable" skeleton replaces the table.

4. Locate the "Regime Decile" filter dropdown and select "D10" (or whichever highest decile is listed)
   - **Expect:** The table immediately narrows to show only rows whose regime-decile column reads "D10". Rows with any other regime decile disappear. The filter is instant with no loading spinner.
   - **Broken looks like:** Rows with other regime decile values remain visible, or the table becomes empty when it shouldn't.
   - Reset: select "All" in the Regime Decile filter to restore all rows before continuing.

5. Click the sort-header button for the first forward-return column (labelled "1d" or "1-day return")
   - **Expect:** The rows reorder. Any rows that showed "NA" in that column have moved to the bottom of the table — below all rows with numeric values. Click the same header again: the sort reverses direction and "NA" rows remain at the bottom, not the top.
   - **Broken looks like:** Rows do not reorder, or "NA" rows appear mixed with numeric rows or at the top after a reverse sort.

6. Confirm the pagination footer shows exactly 30 rows on the current page (count the visible rows), then click the "Next" button
   - **Expect:** The page advances and the next set of rows (different regime/severity/factor decile labels than page 1) is displayed. The row count on page 2 is either 30 or fewer if fewer rows remain.
   - Click "Previous" — the original page-1 rows reappear.
   - **Broken looks like:** Clicking "Next" shows the same rows as page 1, or more than 30 rows are visible on the first page.

7. Locate the As-of / All-history toggle and note the n value in the first visible table row. Click the toggle to switch to the "As-of" (historical) mode.
   - **Expect:** The table re-fetches and the n value in the first row is now lower than the value noted before toggling. Confirm only one date-related control is visible — no second date text field appears anywhere on the page.
   - Click the toggle again to switch back to All-history — the n value returns to the original count.
   - **Broken looks like:** n values do not change after toggling, or a second date `<input>` control appears on the page.

8. Find a table row with a non-zero n value (not "NA") in the 1-day column. Middle-click (or Ctrl+click / Cmd+click) the "N=..." chip to open it in a new tab.
   - **Expect:** A new tab opens at a URL starting with `http://localhost:3255/research/samples`. The Samples page shows a human-readable cohort description that names the regime decile, severity decile, factor decile, and horizon. The "Total observations" count exactly matches the number shown on the chip you clicked.
   - **Broken looks like:** A 4xx error page, an "Unknown cohort" label, or the "Total observations" count does not match the chip's n value.

9. Navigate to `http://localhost:3255/research/regime-lab`
   - **Expect:** The Regime Lab page loads without error. A table with numeric regime-score figures is visible. No "Backend unavailable" or crash.
   - **Broken looks like:** Blank page, "could not load" error, or the page was broken by the new Regime × Phase × Factor lab.

10. Navigate to `http://localhost:3255/research/phase-severity-lab`
    - **Expect:** The Phase & Severity Lab page loads without error. A table with numeric severity figures is visible. No "Backend unavailable" or crash. Both sibling labs continue to work exactly as before.
    - **Broken looks like:** Blank page, "could not load" error, or the layout is visually corrupted.

---

## What "Working Correctly" Looks Like

- The Research hub shows four or more tiles in the LABS section including the new "Regime × Phase × Factor" tile
- The new lab page renders a ranked combination table with at least one row per combination, paired return and max-drawdown columns for each of the five horizons (1d, 5d, 10d, 20d, 60d), and a survivorship-bias / descriptive-evidence disclaimer visible on the page
- Clicking an N= chip opens a Research Samples page that names the exact (regime decile, severity decile, factor decile, horizon) cohort and whose "Total observations" count matches the chip

## Common Issues

- **Blank page or "Backend unavailable" skeleton:** Confirm the backend is running with `curl http://localhost:8255/health`. If the backend just started, wait 10–15 seconds for the cache to warm before loading the lab page.
- **Table shows no rows or only "NA":** The database may not contain enough scanner runs with forward-return data. Check with the team whether forward returns have been calculated for the current snapshot.
- **n values do not decrease when switching to As-of mode:** The observation set may not extend back to the date the toggle selects. Try a more recent historical date (e.g. the previous quarter end) rather than an early date that predates all data.
- **N= chip opens a 4xx page in Samples:** Confirm the backend `compute_samples` endpoint supports the `regime-phase-factor` cohort kind (check `http://localhost:8255/api/research/samples?kind=regime-phase-factor` for a basic response).
