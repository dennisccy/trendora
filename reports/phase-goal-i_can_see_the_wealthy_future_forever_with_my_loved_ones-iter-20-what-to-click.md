# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and healthy (verify: `curl http://localhost:8000/health` returns 200)
- At least one historical scan date with data is available in the system (e.g., 2021-01-04 — ask the developer which date has complete forward-return data if unsure)

---

## Verification Steps

1. Navigate to `http://localhost:3835/stocks?asof=2021-01-04` in your browser
   - **Expect:** The leaderboard table renders with five new column headers visible to the right of the existing columns: "1d", "5d", "10d", "20d", "60d". Some cells show green or red numbers; cells without data show "NA" in grey.
   - **Broken if:** The five columns are missing entirely, or every cell in all five columns shows "NA" at this historical date.

2. Click the "5d" column header in the leaderboard table
   - **Expect:** The table instantly re-orders (no page reload) so the highest 5d return values appear at the top. Any rows showing "NA" in the 5d column sink to the bottom of the list.
   - **Broken if:** Clicking the header does nothing, or "NA" rows appear mixed in between numeric rows.

3. Click on any stock ticker name in the leaderboard to open its Stock Detail page
   - **Expect:** The Stock Detail page loads. A "Realized forward returns" panel appears above the price chart, containing five tiles labelled 1d, 5d, 10d, 20d, 60d. The 5d tile shows the same value that was displayed in the "5d" column for that stock in the leaderboard.
   - **Broken if:** The "Realized forward returns" panel is missing, or any tile value differs from what the leaderboard showed.

4. Navigate to `http://localhost:3835/stocks/AAPL` (no `?asof` — latest date)
   - **Expect:** The "Realized forward returns" panel is present and all five tiles display "NA" in muted grey text (no numeric values, since no future bars exist at the latest date).
   - **Broken if:** Any tile shows a numeric value, or the panel is hidden/absent.

5. Navigate to `http://localhost:3835/research` and scroll down past the Event Study and Combination Lab sections
   - **Expect:** A new "Regime x Setup x Pattern" study section appears below the existing sections. It shows a table with columns including Regime, Setup, Pattern, N, Mean, Median, Hit-rate, Expectancy, and risk-adjusted return columns. A caveat/disclaimer about survivorship bias is visible.
   - **Broken if:** The section is absent, the table is empty with no rows, or the disclaimer is missing.

6. Click the "Mean" column header in the Regime x Setup x Pattern table
   - **Expect:** The table instantly re-orders by Mean value (highest first). No other sections on the page (Event Study, Combination Lab) reload or flash.
   - **Broken if:** Clicking the header does nothing, or the Event Study / Combination Lab sections reset or reload.

7. In the Regime x Setup x Pattern section, locate the "Episodes / Pooled" toggle and click "Pooled"
   - **Expect:** The Regime x Setup x Pattern table re-fetches and updates independently. The N counts in the table change (Pooled typically shows higher N). The Event Study and Combination Lab sections do NOT change or reload.
   - **Broken if:** The toggle does nothing, or switching it causes other sections to reset their own toggles.

8. Find any row in the Regime x Setup x Pattern table where the N column shows a clickable chip (e.g., "N=7" or similar). Click that chip.
   - **Expect:** A new browser tab opens at `/research/samples`. The page heading in the new tab names the specific combination (e.g., "Bull / Trending / VCP — Episodes"), NOT a generic or blank heading. A table of sample observations loads, and the total row count matches the N shown in the chip you clicked.
   - **Broken if:** No new tab opens, the heading says "Unknown cohort" or is blank, or the row count differs from the N in the chip.

9. Navigate to `http://localhost:3835/research`, wait for the Event Study section to finish loading, note one figure (e.g., the mean return for the first horizon shown). Then press F5 (or Cmd+R) to reload the page. Wait for the Event Study section to load again.
   - **Expect:** The figure you noted is identical after the reload. The second load is noticeably faster than the first (cache hit). No values changed.
   - **Broken if:** The figure changes between loads, or the second load takes the same long time as the first.

10. Navigate to `http://localhost:3835/stocks?asof=2021-01-04` and confirm existing leaderboard columns are intact
    - **Expect:** All existing columns (Score, Rank, Setup status, Patterns, Themes) are present and populated alongside the five new forward-return columns. The page has not lost any pre-existing functionality.
    - **Broken if:** Any existing columns are missing, empty, or displaced by the new forward-return columns.

---

## What "Working Correctly" Looks Like

- The `/stocks` leaderboard at a historical date shows five new columns with colour-coded return values (green = positive, red = negative, grey "NA" = no data)
- Clicking any of the five new column headers re-orders the table client-side instantly with NA values at the bottom
- Every Stock Detail page shows a "Realized forward returns" panel above the chart with matching values to the leaderboard
- The `/research` page has a new sortable "Regime x Setup x Pattern" table with its own independent Episodes/Pooled toggle
- Clicking an N= chip in the new table opens a correctly-headed drill-down in a new tab with matching row counts

## Common Issues

- **Forward-return columns all show "NA" at a historical date:** The as-of date may be too recent for enough trailing bars to have accumulated. Try `?asof=2021-01-04` or ask the developer for a confirmed historical date with complete data.
- **Regime x Setup x Pattern section does not appear:** Check browser console for API errors; the `/api/research/regime-setup-pattern` endpoint may not be responding. Verify backend health at `http://localhost:8000/health`.
- **Blank page / error screen on any route:** Check that both the frontend (port 3835) and backend (port 8000) services are running.
- **N= chip heading shows blank or "Unknown cohort":** This indicates the samples page did not receive the expected cohort parameters in the URL — check the full URL in the new tab for missing query parameters.
