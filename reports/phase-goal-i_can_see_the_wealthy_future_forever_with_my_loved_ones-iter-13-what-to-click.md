# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (confirm with: `curl http://localhost:8000/health`)
- Backend has at least 10 trading days of price bars data (the seed data is sufficient)
- No login required

---

## Verification Steps

1. Navigate to `http://localhost:3835/data` in your browser
   - **Expect:** The Data Manager page loads. You can see the "Dataset Coverage" panel. Scrolling down reveals a new "Availability Heatmap" card below it — a month-by-month calendar grid with colored day cells and a legend. No error banner or blank area appears.

2. Hover the mouse over any colored cell in the Availability Heatmap grid and hold for 1 second
   - **Expect:** The readout area above the grid (or a tooltip) updates to show text like "2026-01-15 | 158 / 158 | snapshot: yes" (exact date, symbols count, snapshot flag). The readout changes as you move the cursor to other cells.

3. Click any single day cell in the Availability Heatmap grid (click, do not shift-click)
   - **Expect:** The Job form's "Start date" and "End date" inputs both change to the date of the cell you clicked. The as-of switcher button in the top navigation bar remains unchanged (still "Latest" or whatever date it showed before). The URL does not gain a `?asof=` parameter.

4. Navigate to `http://localhost:3835/stocks`
   - **Expect:** The Stocks page loads normally. In the top navigation bar, the as-of date control now appears as a **button** (labeled "Latest" with a chevron icon) — NOT a `<select>` dropdown. The rest of the stocks page is unchanged.

5. Click the "Latest" button (with chevron) in the top navigation bar to open the as-of calendar
   - **Expect:** A calendar popover opens. It shows the current month's grid with day-of-week headers, a month/year label, back (`<`) and forward (`>`) navigation arrows, and a "Latest" button. Some day cells appear as distinct, clickable buttons (these are dates with stored snapshots); others appear muted/grayed out (no snapshot).

6. Click the back-arrow (`<`) in the calendar popover once to go to the previous month
   - **Expect:** The calendar header changes to the previous month and year. Day cells for that month are displayed. Selectable snapshot dates (if any) appear as distinct buttons. Click the forward-arrow (`>`) once to return to the current month — it should work correctly.

7. Click any visually highlighted (enabled) snapshot date cell inside the calendar popover
   - **Expect:** The popover closes. The top-bar button label changes from "Latest" to the selected date (e.g., "2026-05-15"). A historical indicator ("Historical" or similar badge) appears in the top bar. The URL changes to include `?asof=2026-05-15`. The stocks data on the page reloads to show the historical snapshot.

8. With a historical date selected, click the top-bar as-of button again to reopen the calendar popover, then click the "Latest" button inside the popover
   - **Expect:** The popover closes. The top-bar button label returns to "Latest". The historical badge disappears from the top bar. The `?asof=` parameter is removed from the URL. Page data reverts to the live (non-historical) view.

9. Navigate to `http://localhost:3835/data`, scroll to the Availability Heatmap, and click a cell to prefill the job form. Then verify the top-bar as-of switcher is still "Latest"
   - **Expect:** Job form "Start date" and "End date" both show the clicked cell's date. The top-bar as-of button still shows "Latest". No historical badge appears. This confirms that the heatmap click and the as-of calendar are independent controls that do not interfere with each other.

10. With the as-of calendar popover open (click the top-bar button), press the Escape key
    - **Expect:** The popover closes immediately. The as-of button label is unchanged. No date selection was made. The keyboard dismisses the popover correctly.

---

## What "Working Correctly" Looks Like

- The `/data` page has a visible calendar heatmap card below the Dataset Coverage panel, with colored cells and a legend
- Hovering a heatmap cell shows exact numbers (date, symbol count, snapshot flag) in a readout above the grid
- Clicking a heatmap cell fills in only the Job form dates — the as-of switcher and URL are unaffected
- The top-bar as-of control is a button with a chevron, not a `<select>` dropdown
- Clicking the top-bar button opens a calendar popover with a month grid, navigation arrows, and a "Latest" button
- Selecting a snapshot date from the popover updates the URL (`?asof=YYYY-MM-DD`), shows a historical badge, and reloads page data
- Clicking "Latest" in the popover removes the historical badge and `?asof=` from the URL

## Common Issues

- **Blank page or "Failed to load" in heatmap card**: Confirm the backend is running — `curl http://localhost:8000/api/data/availability` should return a JSON array (not a connection error)
- **No selectable dates in the calendar popover**: Confirm the backend has completed scan runs — `curl http://localhost:8000/api/runs | jq '.runs | length'` should return a non-zero count; if zero, trigger a scan job from the `/data` page first
- **Heatmap cells all appear the same color (no density variation)**: Check that the backend has mixed coverage data — all symbols being fetched on every day will make all cells the same color (full coverage); sparse vs. full variation only shows if some days have fewer symbols
- **As-of switcher still appears as a dropdown**: Hard-refresh the browser (Ctrl+Shift+R / Cmd+Shift+R) to clear the cached `.next/static` bundles; if problem persists, check that the dev server rebuilt successfully
