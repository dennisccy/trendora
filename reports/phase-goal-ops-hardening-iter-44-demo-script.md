# Demo Script — goal-ops-hardening-iter-44

**Mode:** record
**Date:** 2026-08-03
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the home page

- **Narration:** Let's start by opening the application home page. You should see the dashboard with a ready badge at the top.
- **Action:** Navigate to /
- **Point out:** The badge in the top right reads 'Ready' with a green dot, and the page displays 'provider: seed'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-01.png

### Step 02 — Navigate to the Data Manager

- **Narration:** The Data Manager is where you run backfill jobs to ingest historical data. Navigate there to see the job controls.
- **Action:** Navigate to /data
- **Point out:** The page shows 'Data Manager' and includes a 'Start a fetch / backfill job' section with date input fields and a 'Run history' section below.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-02.png

### Step 03 — Start a focused backfill job

- **Narration:** We'll run a small backfill for a single day to show how the system accepts and processes these requests quickly.
- **Action:** Type "2026-05-02" into "job-start-date"
- **Point out:** After clicking Start, the Job progress panel shows the job moving through its lifecycle. The badge at the top stays 'Ready' throughout.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-03.png

### Step 06 — Show pages load efficiently

- **Narration:** One of this iteration's focuses is making sure every page in the application loads only the data it needs. Let's tour the main pages.
- **Action:** Navigate to /stocks
- **Point out:** The home page, Stocks list, and individual stock pages all load promptly with their expected content.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-06.png

### Step 09 — View the Backtest evidence page

- **Narration:** The Backtest page shows the forward-tested evidence from our backtesting system. This page always serves pre-computed results, never makes you wait for fresh computation.
- **Action:** Navigate to /backtest
- **Point out:** The page shows 'Forward-tested evidence' and displays the backtesting results.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-09.png

### Step 10 — Check background compute disclosure

- **Narration:** When heavy data processing happens in the background, the application tells you about it. Let's see the Background Compute panel on the Data Manager page.
- **Action:** Navigate to /data
- **Point out:** The Background Compute panel on the /data page explains what background work is happening and notes that it is process-lifetime only—it clears on restart.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-10.png

### Step 11 — Confirm the badge stays responsive

- **Narration:** Even while backfills and background work run, the top-right readiness badge stays responsive and honest. It shows 'Ready' for a healthy backend, 'Checking backend…' while verifying, or 'Backend unavailable' if the service is down.
- **Action:** Navigate to /
- **Point out:** The badge at the top right consistently shows a clear status—either 'Ready', initializing, or explicitly 'Backend unavailable', never a blank or confusing header.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-44/step-11.png

## Full tour (text only)

### Step 04 — Set the end date and start the job

- **Narration:** We're setting both the start and end date to the same day (May 2nd, 2026) to show a focused, single-day backfill.
- **Action:** Type "2026-05-02" into "job-end-date"
- **Point out:** The 'Start' button becomes active once both dates are filled in. The job begins executing immediately when you click it.

### Step 05 — Click the Start button

- **Narration:** Now we start the job. The system will fetch or compute the data for that date range.
- **Action:** Click the "Start" button
- **Point out:** The Job progress panel updates as the job runs. You can see the badge staying 'Ready' and available the whole time.

### Step 07 — View a specific stock

- **Narration:** We can drill down into individual stocks. Here's Apple (AAPL) as an example—the page loads with all the stock information.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The page heading shows 'AAPL' and the data loads efficiently.

### Step 08 — View the Sectors page

- **Narration:** The Sectors page shows how stocks are organized by sector. Each page loads only the data needed to display that view.
- **Action:** Navigate to /sectors
- **Point out:** The page title shows 'Sectors' and the page renders promptly without loading unnecessary data.
