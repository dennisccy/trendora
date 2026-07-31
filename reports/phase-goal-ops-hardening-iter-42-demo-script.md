# Demo Script — goal-ops-hardening-iter-42

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Let's start by loading the home page to check that the backend is ready. You should see a green 'Ready' badge in the top-right corner.
- **Action:** Navigate to /
- **Point out:** The top-right badge shows 'Ready' with a green dot, confirming the backend is available.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-01.png

### Step 02 — Navigate to Data Manager

- **Narration:** Go to the Data Manager page. This is where you start backfill jobs to ingest historical trading data.
- **Action:** Navigate to /data
- **Point out:** The Data Manager form appears with 'Start date' and 'End date' fields, ready to accept a date range.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-02.png

### Step 03 — Run a backfill job

- **Narration:** Submit a backfill request for a specific date range. This will fetch and snapshot the trading data, and compute aggregates like market coverage during ingest—not on request later.
- **Action:** Type "2026-05-02" into the "Job start date" textbox
- **Point out:** The Job progress panel shows the job has finished, and the Run history lists which aggregates (like 'latest snapshot' and 'coverage') were computed and stored.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-03.png

### Step 04 — Set the end date and start the job

- **Narration:** Enter the end date and click Start. The job will accept any range—no artificial cap—and begin processing.
- **Action:** Type "2026-05-29" into the "Job end date" textbox
- **Point out:** The 'Start' button becomes active. Once clicked, the Job progress panel moves from 'running' to a terminal status, showing 'Refreshed:' with a list of aggregates that were computed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-04.png

### Step 05 — Click Start to submit the backfill

- **Narration:** Submit the job by clicking the Start button (the play icon).
- **Action:** Click the "Start" button
- **Point out:** The Job progress panel transitions to 'running', showing live heartbeat activity, then settles to a finished state.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-05.png

### Step 06 — View scanner runs

- **Narration:** Navigate to Scanner Runs to see the ingested snapshots. Click on a specific date to see the stored leaderboard—no recompute happens on click.
- **Action:** Navigate to /scanner-runs
- **Point out:** The Scanner Runs list displays the date (e.g. 2026-05-29) and a populated leaderboard table. The data was computed once at ingest time, not on demand.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-06.png

### Step 07 — Open the Backtest page

- **Narration:** View the Backtest page, which shows cached evidence values from past aggregates. Even during a heavy job in the background, this page renders instantly with stored data—never making the user wait for a cold recompute.
- **Action:** Navigate to /backtest
- **Point out:** The Backtest page displays evidence panels with real numbers or a 'Refreshing' banner, never a blank page or endless spinner.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-07.png

### Step 08 — Check the Data page for background compute status

- **Narration:** Return to the Data Manager and check the 'Background compute' panel. If any aggregates are being computed in the background, the badge shows a chip with a counter, and the panel lists elapsed time and progress.
- **Action:** Navigate to /data
- **Point out:** The Background compute panel displays in-flight windows or 'No background compute running' when idle. Any in-flight work is visible and measured.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-42/step-08.png
