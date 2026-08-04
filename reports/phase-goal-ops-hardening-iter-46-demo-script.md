# Demo Script — goal-ops-hardening-iter-46

**Mode:** record
**Date:** 2026-08-04
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the dashboard

- **Narration:** The homepage shows the app is ready with a green 'Ready' badge. This iteration fixed two backend memory accumulators to prevent the app from running out of memory when loading the evidence page, even under heavy concurrent load.
- **Action:** Navigate to /
- **Point out:** The top-right badge reads 'Ready' in green, and the page shows 'provider: seed'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-46/step-01.png

### Step 02 — Check data manager and verify gaps

- **Narration:** The Data Manager shows the backfill status, including the current number of unfilled historical gaps. Backfill jobs can now run without the bounded memory accumulators causing out-of-memory crashes.
- **Action:** Navigate to /data
- **Point out:** A 'Backfill gaps' statistic appears showing a number around 2,531 unfilled dates.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-46/step-02.png

### Step 03 — View backtest evidence

- **Narration:** The backtest page renders forward-tested evidence without requiring a cold recompute on every request. This demonstrates that stored evidence serves promptly even during background aggregation.
- **Action:** Navigate to /backtest
- **Point out:** The page shows 'Forward-tested evidence' with a scorecard containing real values like 'n=14647' (byte-identical after this iteration's refactor).
- **Screenshot:** reports/demo/goal-ops-hardening-iter-46/step-03.png

### Step 04 — Check health endpoint responsiveness

- **Narration:** The backend health check stays responsive throughout the app's operation. This iteration's memory bounds ensure that even heavy processing tasks don't starve the health-monitoring path.
- **Action:** Navigate to /
- **Point out:** The badge remains green ('Ready') and the backend responds quickly to health checks.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-46/step-04.png

## Full tour (text only)

### Step 05 — Navigate to stocks page

- **Narration:** Other pages in the app load quickly without requiring full data prefills. The bounded accumulators keep memory usage predictable across all pages.
- **Action:** Navigate to /stocks
- **Point out:** The stocks page loads within budget and displays stock data normally.

### Step 06 — View a specific stock

- **Narration:** Individual stock pages render promptly, confirming the lazy-loading improvements work end-to-end.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** AAPL stock page loads with price and performance data.

### Step 07 — Check background compute disclosure

- **Narration:** When background processes run, the app discloses this on the badge and data panel, allowing users to understand what the system is doing. The bounded memory fix ensures these processes don't exhaust resources.
- **Action:** Navigate to /data
- **Point out:** If background compute is active, a chip appears on the badge and the data panel shows elapsed time and progress.

### Step 08 — Return to data manager

- **Narration:** The Run history table persists across reloads and shows all historical jobs submitted in this session, confirming job tracking remains reliable.
- **Action:** Navigate to /data
- **Point out:** Run history displays accumulated job records from earlier backfill attempts.
