# Demo Script — goal-ops-hardening-iter-24

**Mode:** record
**Date:** 2026-07-26
**Frontend URL:** http://localhost:3255
**Iteration:** 24

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Trendora opens straight to its main dashboard. The top-right corner always shows whether the system is ready.
- **Action:** Navigate to /
- **Point out:** The green status pill next to the data provider details in the top-right corner.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-24/step-01.png

### Step 02 — Open the Backtest page

- **Narration:** Move to the Backtest page, where you can review evidence for the latest date, or step back to any earlier date.
- **Action:** Click the "Backtest" link
- **Point out:** A small "Latest" badge appears next to the calendar icon in the top-right corner.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-24/step-02.png

### Step 03 — Step back to an earlier date

- **Narration:** Clicking the left arrow moves the view to an earlier date. If that date's evidence hasn't been prepared yet, Trendora quietly starts preparing it in the background instead of making you wait.
- **Action:** Click "asof-step-prev"
- **Point out:** The badge switches to an amber "(historical)" label for the date you picked.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-24/step-03.png

### Step 04 — Open Data Manager

- **Narration:** Data Manager holds every operational detail about the data pipeline in one place.
- **Action:** Click the "Data Manager" link
- **Point out:** Dataset coverage details load right at the top of the page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-24/step-04.png

## Full tour (text only)

### Step 05 — See the new background-compute panel  [NEW]

- **Narration:** Scroll to the very bottom of Data Manager and a new panel appears. It honestly shows whether anything is computing right now, and what happened the last time something did, without ever guessing or estimating.
- **Action:** Click "background-compute-panel"
- **Point out:** A line at the bottom always states this history resets whenever the backend restarts, so an empty panel is never mistaken for nothing having happened.
