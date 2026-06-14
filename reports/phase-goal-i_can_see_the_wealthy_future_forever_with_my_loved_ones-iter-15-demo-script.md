# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15

**Mode:** record
**Date:** 2026-06-14
**Frontend URL:** http://localhost:3835

## Highlights

### Step 01 — Open the Data Manager

- **Narration:** The Data Manager at /data is your control center for all imported market data. Every section — coverage stats, the availability heatmap, the fetch panel, run history, and the new remove tool — loads cleanly on one page.
- **Action:** Navigate to /data
- **Point out:** Look for the 'Data Manager' heading and the row of panels beneath it, including 'Remove imported data' toward the bottom.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-01.png

### Step 02 — Remove panel: only two date fields  [NEW]

- **Narration:** The Remove imported data panel has been simplified to exactly two inputs — a From date and a To date. The old free-text Symbols box is gone, making it impossible to accidentally scope a removal to the wrong tickers.
- **Action:** Navigate to /data
- **Point out:** Notice there is no 'Symbols' field anywhere in the panel — just From, To, and the Preview removal button.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-02.png

### Step 03 — Preview button disabled until both dates are filled  [NEW]

- **Narration:** The Preview removal button stays grayed out until both a From and a To date carry a valid calendar date. Filling in only one field is not enough — the guard prevents you from launching a half-specified removal.
- **Action:** Type "2025-02-01" into "[data-testid='remove-start-date']"
- **Point out:** The Preview removal button should appear disabled (grayed out) right now with the fields empty.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-03.png

### Step 04 — Button enables the moment both dates are valid  [NEW]

- **Narration:** The moment you complete the To date with a valid ISO date, the Preview removal button activates instantly — no page reload needed. The button tracks the form state live so you always know when you are ready to proceed.
- **Action:** Type "2025-02-28" into "[data-testid='remove-end-date']"
- **Point out:** The Preview removal button should now be active and clickable.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-04.png

### Step 05 — Confirmation modal shows counts only  [NEW]

- **Narration:** Clicking Preview removal opens a compact confirmation that tells you exactly what will be removed: a bar count, how many symbols are affected, how many seed bars are protected, and how many snapshots will cascade away — all as plain numbers, never a long list of ticker names.
- **Action:** Click "[data-testid='remove-preview-button']"
- **Point out:** The modal body shows numbers like '19 bars', '1 affected symbol', and snapshot counts. There is no scrolling list of tickers.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-05.png

### Step 06 — Remove button visible without scrolling  [NEW]

- **Narration:** The Cancel and Remove buttons sit in a fixed footer outside the scrollable modal body. No matter how much detail the summary contains, the action buttons are always visible right in front of you — you never need to scroll down to find them.
- **Action:** Click the "Cancel" button
- **Point out:** Both Cancel and the Remove button should be visible at the bottom of the modal right now, with no scrolling required.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-06.png

### Step 07 — Backfill jobs run to completion without crashing  [NEW]

- **Narration:** Multi-month and full-history backfill jobs now run reliably to completion. If an individual day fails, that day is isolated with its own error while every other day still finishes — the overall job reaches 'ok' or 'partial', never an unrecoverable crash.
- **Action:** Navigate to /data
- **Point out:** The Run history table should show recent jobs with 'ok' or 'partial' status — no 'error' or 'crash' entries at the job level.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-07.png

### Step 08 — Rest of the Data page remains intact

- **Narration:** All the other Data Manager panels — the per-date availability heatmap, dataset coverage stats, and the fetch panel — continue to work exactly as before. This iteration only touched the remove flow; nothing else regressed.
- **Action:** Navigate to /data
- **Point out:** Scroll down to confirm the availability heatmap grid, coverage stats, and fetch panel are all visible and rendering without any error banners.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15/step-08.png
