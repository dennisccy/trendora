# Demo Script — goal-ops-hardening-iter-77

**Mode:** record
**Date:** 2026-08-13
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the app's home page

- **Narration:** Let's start by opening the dashboard and checking the app's status.
- **Action:** Navigate to /
- **Point out:** The green Ready pill in the top-right corner indicates the app is connected to the backend.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-01.png

### Step 02 — Check the freshness indicator on the badge  [NEW]

- **Narration:** Next to the Ready pill, there's a small gray text showing how fresh this status reading is. This is new.
- **Action:** Click the "Ready" button
- **Point out:** Look for the 'as of Ns ago' text right next to the Ready badge. It tells you how many seconds old this status information is.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-02.png

### Step 03 — See the freshness note on the confirmation strip  [NEW]

- **Narration:** Below the top bar is a green strip confirming the board is current. It also shows the same freshness note.
- **Action:** Navigate to /
- **Point out:** The preflight banner reads 'GO — today's board is current. (as of Ns ago)' — the staleness note is now on this strip too.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-03.png

### Step 04 — Refresh the page to see the status update live

- **Narration:** Reload the page. You'll see the Ready pill and staleness text reappear instantly, showing it's a live reading each time.
- **Action:** Navigate to /
- **Point out:** The badge and staleness text don't freeze — they refresh on every page load.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-04.png

### Step 05 — Navigate to the backtest page

- **Narration:** Let's go to the backtest section to see the scorecard table. Click the Backtest link in the sidebar.
- **Action:** Navigate to /backtest
- **Point out:** The sidebar has a link to Backtest. This page shows forward-looking return metrics in a scorecard.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-05.png

### Step 06 — View the scorecard table with return horizons

- **Narration:** The scorecard shows forward returns for different time horizons: 1-day, 5-day, 10-day, 20-day, and 60-day.
- **Action:** Navigate to /backtest
- **Point out:** Each row in the table represents one horizon. The numbers show the median return (or '—' if the horizon hasn't elapsed yet).
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-06.png

### Step 07 — Navigate to a historical date to see background compute  [NEW]

- **Narration:** Click the left arrow next to the date selector to step back to a previous historical date. This may trigger background computation.
- **Action:** Click "asof-step-prev"
- **Point out:** When a compute window is active, a chip appears in the top bar saying 'background compute running (N)'. With this update, the Ready badge stays visible alongside it, even at narrow window widths.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-77/step-07.png
