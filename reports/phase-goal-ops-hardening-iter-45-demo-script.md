# Demo Script — goal-ops-hardening-iter-45

**Mode:** record
**Date:** 2026-08-04
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Let's start by viewing the main dashboard and confirming the system is ready to use.
- **Action:** Navigate to /
- **Point out:** The top-right badge should show 'Ready' in green, indicating the backend is available.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-01.png

### Step 02 — View the Data Manager

- **Narration:** Now let's visit the Data Manager to see the backfill interface and current dataset status.
- **Action:** Navigate to /data
- **Point out:** You should see a 'Start a fetch / backfill job' panel with date fields and a 'Run history' section showing prior backfill attempts.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-02.png

### Step 03 — Check the dataset coverage panel

- **Narration:** The Data Manager shows key dataset statistics. Look at the coverage metrics to understand what date ranges are already snapshotted.
- **Action:** Click "[data-testid='universe-count']"
- **Point out:** You should see numeric values for 'Backfill gaps' and other coverage metrics—not a blank or error state.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-03.png

### Step 04 — Navigate to the Stocks section

- **Narration:** Let's verify that navigation between pages remains fast and responsive, even after this backend iteration.
- **Action:** Navigate to /stocks
- **Point out:** The page should load promptly and display the stocks list.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-04.png

### Step 05 — View a stock detail page

- **Narration:** Opening a specific stock's page should load quickly with only the data it needs.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The page should show the stock symbol and relevant data within the expected load time.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-05.png

### Step 06 — Check the Backtest results page

- **Narration:** The Backtest page displays pre-computed evidence. This iteration ensures it always serves from storage rather than recomputing on request.
- **Action:** Navigate to /backtest
- **Point out:** You should see 'Forward-tested evidence' and populated evidence values—never a blank loading screen.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-06.png

### Step 07 — Return to Data Manager to view background compute

- **Narration:** Let's check the background compute panel to confirm the system properly discloses any in-flight compute activity.
- **Action:** Navigate to /data
- **Point out:** If any background processes are running, the panel should list them with elapsed time and progress—never silently omit them.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-07.png

### Step 08 — Confirm the readiness badge remains stable

- **Narration:** Throughout this tour, the top-bar badge should have stayed responsive and visible. This is the key reliability property this iteration verifies.
- **Action:** Click "[data-testid='readiness-badge']"
- **Point out:** The readiness badge in the top-right corner should display either 'Ready' or an explicit status—never blank or stuck on 'Checking...'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-45/step-08.png
