# Demo Script — goal-ops-hardening-iter-41

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Dashboard loads with ready status

- **Narration:** The app boots and shows the main dashboard. The top-right badge displays a green Ready indicator, confirming the backend is available and listening.
- **Action:** Navigate to /
- **Point out:** The badge in the top-right reads 'Ready' with a green dot; the dashboard is fully rendered.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-01.png

### Step 02 — Data page opens with the backfill job panel

- **Narration:** Navigate to the Data section, where operators can start fetch and backfill jobs. The form shows date-range inputs and a job-kind dropdown.
- **Action:** Navigate to /data
- **Point out:** The 'Start a fetch / backfill job' panel is visible with Start date and End date fields; the Job kind dropdown reads 'Backfill snapshots'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-02.png

### Step 03 — Submit a backfill job for May 2026

- **Narration:** Fill in the date range from May 2 to May 29, 2026, and start the job. The system will backfill historical snapshots for those trading days.
- **Action:** Type "2026-05-02" into the element
- **Point out:** After clicking Start, the Job progress panel shows the job moving toward completion; the summary will report how many trading days were processed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-03.png

### Step 04 — Backfill job finishes and reports results

- **Narration:** The job completes and shows its final status. If this is a fresh range, it will report 19 trading days snapshotted. If the range was already backfilled, a distinct 'no new snapshots' badge explains the zero-work run.
- **Action:** Type "2026-05-29" into the element
- **Point out:** The Job progress panel shows a terminal status (not 'running'); the summary mentions either '19' trading days or a 'no new snapshots' badge.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-04.png

### Step 05 — Click Start to launch the backfill

- **Narration:** The Start button submits the backfill request. Watch the Job progress panel update as the system processes the date range.
- **Action:** Click the "Start" button
- **Point out:** The Job progress panel becomes active and shows the job running; then it moves to a finished state.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-05.png

### Step 06 — Scanner Runs detail page shows the stored leaderboard

- **Narration:** Navigate to Scanner Runs and open the row for May 29, 2026. The page loads the immutable leaderboard that was computed and stored during the backfill.
- **Action:** Navigate to /scanner-runs
- **Point out:** A populated leaderboard table is visible with stock symbols and rankings; never an empty 'No stored stock rows' message.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-06.png

### Step 07 — Backtest page loads evidence from storage, never recomputing

- **Narration:** Open the Backtest page, which displays precomputed evidence. If a background aggregation is in flight, an honest 'Refreshing' banner appears. Once complete, the banner disappears and fresh values display.
- **Action:** Navigate to /backtest
- **Point out:** The evidence panel loads with either normal values or a 'Refreshing — showing the last complete evidence' banner; the page never shows a blank or spinning state.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-07.png

### Step 08 — Ready badge discloses background compute in flight

- **Narration:** If a background aggregation is still running, the top-right badge shows 'Ready' plus an extra chip reading 'background compute running (N)', disclosing the in-flight compute. Once complete, the chip disappears.
- **Action:** Navigate to /data
- **Point out:** The top-right badge either shows just 'Ready' (if no compute is in flight), or 'Ready' with an additional 'background compute running' chip showing the count.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-41/step-08.png
