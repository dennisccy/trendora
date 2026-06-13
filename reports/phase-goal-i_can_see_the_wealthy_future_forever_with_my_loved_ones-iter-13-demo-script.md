# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13

**Mode:** record
**Date:** 2026-06-13
**Frontend URL:** http://localhost:3835
**Iteration:** 13

## Highlights

### Step 01 — Data Manager — availability heatmap loads  [NEW]

- **Narration:** The Data Manager page now has a full trading-day calendar below the Dataset Coverage panel. Every cell is color-coded by how many symbols had price bars on that day, with a ring marker on dates where a portfolio snapshot was computed.
- **Action:** Navigate to /data
- **Point out:** The 'Per-date availability' card with colored day cells and a legend visible after scrolling past Dataset Coverage.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-01.png

### Step 02 — Hover a heatmap cell — exact readout appears  [NEW]

- **Narration:** Moving the cursor over any day cell immediately updates a header readout with the exact date, how many of the tracked symbols had data that day, and whether a snapshot was stored. No tooltips or extra clicks required.
- **Action:** Navigate to /data
- **Point out:** The readout above the grid showing a line like '2021-01-04 · 150/159 symbols · snapshot yes' after hovering.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-02.png

### Step 03 — Click a heatmap day — job form fills instantly  [NEW]

- **Narration:** Clicking any day cell prefills the job form's Start and End date fields with that date, so you can kick off a backfill for exactly that day without typing. The as-of switcher in the top bar is completely unaffected.
- **Action:** Navigate to /data
- **Point out:** The Start date and End date inputs in the job form now both show the date of the cell you clicked; the top-bar button still reads 'Latest'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-03.png

### Step 04 — Stocks page — as-of switcher is now a calendar button  [NEW]

- **Narration:** The plain dropdown list that used to control the historical date has been replaced with a button labeled 'Latest' and a chevron. Clicking it opens a proper calendar popover instead of a long scrolling list.
- **Action:** Navigate to /stocks
- **Point out:** A button with a chevron icon in the top navigation bar where the old dropdown was — no select element in sight.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-04.png

### Step 05 — Open the as-of calendar popover  [NEW]

- **Narration:** One click on the top-bar button opens a month grid calendar. Snapshot dates are shown as distinct, clickable buttons; every other day is visibly muted so you can immediately see which dates have stored portfolio data.
- **Action:** Click the "Latest" button
- **Point out:** A floating calendar with day-of-week headers, a month/year label, back and forward arrows, and a 'Latest' button at the bottom of the popover.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-05.png

### Step 06 — Select a historical date from the calendar  [NEW]

- **Narration:** Clicking a highlighted snapshot date closes the popover, updates the URL to include the chosen date, and shows a historical badge in the top bar. Opening the same URL in a new tab restores the exact same historical view.
- **Action:** Navigate to /stocks?asof=2026-05-01
- **Point out:** The top-bar button now shows the selected date (e.g., '2026-05-01'), a historical badge appears, and the URL bar includes '?asof=2026-05-01'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-06.png

### Step 07 — Return to live view with the 'Latest' button  [NEW]

- **Narration:** Inside the calendar popover, clicking 'Latest' instantly removes the historical badge, strips the date from the URL, and reloads the page with the most current data.
- **Action:** Navigate to /stocks
- **Point out:** After clicking 'Latest' in the popover: the top-bar button reads 'Latest', the historical badge is gone, and the URL no longer contains '?asof='.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-07.png

### Step 08 — Heatmap back-arrow clamps at the oldest snapshot month  [NEW]

- **Narration:** Navigating backwards month by month in the calendar popover, the back arrow disables itself at the oldest month that has snapshots. You can always reach the full history, but you cannot scroll past it into empty space.
- **Action:** Navigate to /stocks
- **Point out:** At month '2021-01' the back-arrow button is disabled (grayed out) while the forward arrow remains active, and snapshot dates for that month are still selectable.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13/step-08.png
