# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- A historical snapshot exists with post-date price bars (any date at least 60 trading days before the most recent available date — e.g., 2024-01-15)
- No login required

---

## Verification Steps

1. Navigate to `http://localhost:3835/themes` and set the global as-of date picker to a historical date with data (e.g., 2024-01-15).
   - **Expect:** The Themes leaderboard table gains five new columns in the header row labelled "1d", "5d", "10d", "20d", and "60d". Each theme row shows a coloured percentage in those columns (green for positive, red for negative) or the text "NA" in muted grey. No cell shows "0%" or is blank.
   - **Broken looks like:** The five column headers are missing entirely, every cell shows "0%", or the page crashes with an error message.

2. On the same `/themes` page, click the "5d" column header.
   - **Expect:** The rows immediately reorder smallest-to-largest by 5d return. Any "NA" rows move to the bottom. No loading spinner or page reload occurs.
   - **Broken looks like:** Clicking the header does nothing, or "NA" rows float to the top, or a network spinner appears.

3. Click the "5d" column header a second time.
   - **Expect:** Rows reorder largest-to-smallest (descending). "NA" rows remain at the bottom, not the top.
   - **Broken looks like:** NA rows appear above numeric rows in descending sort.

4. Navigate to `http://localhost:3835/sectors` and keep the same historical as-of date.
   - **Expect:** The Sectors leaderboard table also shows five new forward-return columns (1d / 5d / 10d / 20d / 60d) with numeric values colour-graded green/red, or "NA" where data is absent. Existing sector columns (name, ETF ticker, score) are still present and correct.
   - **Broken looks like:** The five columns are missing, or existing columns have disappeared or shifted.

5. Navigate to `http://localhost:3835/research` (fresh page load — do not use browser back button).
   - **Expect:** After the page loads, scroll down to the Regime × Setup × Pattern section. Without clicking anything, confirm the "Pooled" toggle or tab is already highlighted/active. The RSP table displays pooled data by default. Other research sections (Event Study, etc.) still show "Episodes" as their default.
   - **Broken looks like:** The RSP section opens in "Episodes" mode, or the page shows no toggle, or other sections default to "Pooled".

6. In the RSP section, click the "Regime" dropdown (currently showing "All") and select any one specific regime label (e.g., the first non-"All" option in the list).
   - **Expect:** The RSP table immediately redraws to show only rows matching the selected regime. No page reload. The row count decreases or stays the same. The other two dropdowns (Setup, Pattern) still show "All".
   - **Broken looks like:** The dropdown has no options, selecting a regime does not change the table, or the page reloads.

7. In the RSP section, click a numeric column header (e.g., "Win Rate" or "Return 1d") to sort ascending.
   - **Expect:** Numeric rows sort smallest-to-largest at the top. All rows displaying "NA" in that column appear below every numeric row — none appear between two numeric rows.
   - **Broken looks like:** NA rows appear at the top or interspersed among numeric rows when sorted ascending.

8. Locate any RSP row with an N= chip (e.g., "N=24"). Click the chip.
   - **Expect:** A new browser tab opens to `/research/samples` with query parameters for the selected combination (Regime, Setup, Pattern visible in the URL). The samples page loads successfully showing observations — no 404, no 500, no error message. The total count displayed on the samples page matches the N value you clicked.
   - **Broken looks like:** The tab opens to a "404 Not Found" or error page, or the samples count does not match the chip value.

9. Return to the RSP section. Use the "Pattern" dropdown to select a value that is unlikely to exist together with your currently selected Regime (choose a combination you expect to yield no results).
   - **Expect:** Either a small set of rows matching both filters appears, or the table shows an empty state with a clear message (e.g., "No matching combinations") — never a broken blank layout with no explanation.
   - **Broken looks like:** The table appears blank with no message, or the page crashes.

10. Reset both the Regime and Pattern dropdowns back to "All".
    - **Expect:** All original RSP rows reappear. The full table is restored without a page reload.
    - **Broken looks like:** Some rows do not return after resetting, or a reload is required to restore them.

---

## What "Working Correctly" Looks Like

- `/themes` and `/sectors` each have five new sortable forward-return columns; green/red colour grading is consistent; "NA" appears in muted text (never "0%") where data is absent
- Clicking a forward-return column header sorts the table client-side instantly with NA rows always at the bottom, in both ascending and descending order
- `/research` RSP section opens in Pooled mode by default; three filter dropdowns (Regime, Setup, Pattern) are visible and filter the table without reloading the page; NA sort works correctly; every N= chip opens a working samples page

## Common Issues

- **Five forward-return columns missing from `/themes` or `/sectors`**: Confirm the backend is returning `forward_returns` in the API response — run `curl http://localhost:8835/api/themes | grep forward_returns` to check; if absent, the backend service may need a restart
- **RSP section defaults to Episodes instead of Pooled**: This is a frontend state issue; try a hard refresh (Ctrl+Shift+R) to clear any cached page state
- **N= chip drill-down returns a 404 or 422 error**: The specific combination clicked may be a "pattern=none" row; this was a known bug fixed in this iteration — if the error persists, check the backend is running the updated code (`curl http://localhost:8835/health`)
- **Backend unavailable / "Checking backend…" on every page**: Run `curl http://localhost:8835/health` to confirm the backend is up; if not, restart it (kill by port 8835, not by process name)
