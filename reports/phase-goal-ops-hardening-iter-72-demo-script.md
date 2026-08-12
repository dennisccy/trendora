# Demo Script — goal-ops-hardening-iter-72

**Mode:** record
**Date:** 2026-08-13
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Dashboard loads with readiness badge

- **Narration:** The application starts on the Dashboard. The readiness badge at the top confirms the backend is ready and responsive to serve data.
- **Action:** Navigate to /
- **Point out:** Readiness badge showing 'Ready' status at top of page
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-01.png

### Step 02 — Data Manager shows current status

- **Narration:** The Data Manager page displays the latest run status and the complete history of past backfill jobs. Each entry shows what was completed and what remains.
- **Action:** Navigate to /data
- **Point out:** Run history panel listing past jobs with their status; last run status showing a real value
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-02.png

### Step 03 — Zero-work backfill explains itself clearly

- **Narration:** When a backfill requests dates that are already fully processed, the system explains this honestly. Here, a weekend-only span is submitted and immediately reports zero work to do.
- **Action:** Type "2026-05-02" into the element
- **Point out:** Job report showing '0/0 dates' with neutral gray explanation '2 calendar days · 0 already snapshotted · 2 non-trading'
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-03.png

### Step 04 — Complete the weekend backfill request

- **Narration:** The end date is set to complete the weekend span that contains no trading data.
- **Action:** Type "2026-05-03" into the element
- **Point out:** End date field filled; page ready for job submission
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-04.png

### Step 05 — Submit and watch the job complete instantly

- **Narration:** The Start button triggers the backfill. Since all dates are already snapshotted or non-trading, the job finishes within seconds and reports its work clearly.
- **Action:** Click the "Start" button
- **Point out:** Job card showing completion status and the zero-work explanation displayed in neutral styling
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-05.png

### Step 06 — Scanner Runs page lists all stored snapshots

- **Narration:** The Scanner Runs page shows the complete history of every trading day's snapshot. Each row represents data that has been processed and stored. No range restrictions apply—months-long spans execute to completion.
- **Action:** Navigate to /scanner-runs
- **Point out:** Table showing multiple scanner run rows, each with a date as-of value and leaderboard data
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-06.png

### Step 07 — Backtest page serves results instantly from storage

- **Narration:** The Backtest page displays evidence and summary information immediately, without any recomputation delay. All data is served from pre-computed snapshots, staying responsive even during background compute.
- **Action:** Navigate to /backtest
- **Point out:** Backtest page with 'Snapshots contributing' text visible immediately upon load
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-07.png

### Step 08 — All pages remain responsive under load

- **Narration:** Every page in the application—Stocks, Sectors, Themes, Evidence, and Regime Lab—loads with real content quickly. The system handles background compute activity without freezing or stalling.
- **Action:** Navigate to /stocks
- **Point out:** Navigation through multiple pages works smoothly; no blank pages or spinners; background-compute panel shows real status
- **Screenshot:** reports/demo/goal-ops-hardening-iter-72/step-08.png
