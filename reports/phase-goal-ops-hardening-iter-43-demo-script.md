# Demo Script — goal-ops-hardening-iter-43

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the dashboard

- **Narration:** The dashboard displays a ready status and confirms the system is initialized with seed data.
- **Action:** Navigate to /
- **Point out:** The top-right badge shows a green Ready state; the page shows 'provider: seed'
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-01.png

### Step 02 — Start a simple backfill job

- **Narration:** Navigate to the Data Manager to run a backfill. We'll start with a single date range.
- **Action:** Navigate to /data
- **Point out:** The Data Manager page loads with the backfill form ready to use.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-02.png

### Step 03 — Enter dates and start the backfill

- **Narration:** Backfill a small, single-day range to see how the system handles zero-work scenarios.
- **Action:** Type "2026-05-02" into "job-start-date"
- **Point out:** After the job finishes, reload to see the job summary explains why no work was needed—'2 non-trading'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-03.png

### Step 04 — Set end date and start

- **Narration:** Complete the range and trigger the backfill to run.
- **Action:** Type "2026-05-03" into "job-end-date"
- **Point out:** The job progresses to completion; the system explains what it did.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-04.png

### Step 05 — Start the job

- **Narration:** Click Start to queue the backfill.
- **Action:** Click the "Start" button
- **Point out:** Job progress panel updates as the job runs.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-05.png

### Step 06 — View the completed job in history

- **Narration:** After the job finishes, reload the Data Manager to see its summary. The system explains that it found 2 non-trading days—zero work needed.
- **Action:** Navigate to /data
- **Point out:** Run history shows the completed job with its explanation: '2 non-trading'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-06.png

### Step 07 — Run a wide date range without rejection

- **Narration:** This iteration removed any per-run date range cap. We'll backfill a full year plus—412 calendar days—to prove the system accepts it.
- **Action:** Type "2025-06-01" into "job-start-date"
- **Point out:** The wide range (2025-06-01 to 2026-07-17) is accepted and begins processing.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-07.png

### Step 08 — Set the wide range end date

- **Narration:** Enter the end date for the 412-day range.
- **Action:** Type "2026-07-17" into "job-end-date"
- **Point out:** The form accepts both dates without complaints.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-08.png

### Step 09 — Start the wide backfill

- **Narration:** Submit the 412-day range. No 'date range too large' error appears; the job begins processing.
- **Action:** Click the "Start" button
- **Point out:** The job shows it is running and accepting the full, wide range.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-43/step-09.png

## Full tour (text only)

### Step 10 — Navigate to Stocks

- **Narration:** Tour the main surfaces to verify they load quickly and stay responsive. Start with Stocks.
- **Action:** Navigate to /stocks
- **Point out:** The Stocks page renders with the list of available symbols.

### Step 11 — View a stock detail page

- **Narration:** Each symbol loads its details on demand, avoiding unnecessary preloading.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** AAPL details render with its chart and metrics.

### Step 12 — View the Evidence page

- **Narration:** The Evidence page loads with stored backtest results, never recomputing on the fly.
- **Action:** Navigate to /backtest
- **Point out:** Forward-tested evidence values display from storage.

### Step 13 — View background compute disclosure

- **Narration:** Return to the Data Manager to see the background compute panel. It discloses any in-flight aggregation work and its scope.
- **Action:** Navigate to /data
- **Point out:** If work is running, the panel lists the window with elapsed time and horizon progress; it states the work is 'process-lifetime only, never persisted'.
