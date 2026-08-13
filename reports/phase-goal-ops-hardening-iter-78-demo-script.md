# Demo Script — goal-ops-hardening-iter-78

**Mode:** record
**Date:** 2026-08-13
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Dashboard shows live freshness indicators  [NEW]

- **Narration:** The dashboard loads with a green Ready badge in the top-right. A small gray label next to it updates every second to show data freshness — this is new behavior that continuously updates rather than freezing. The green GO banner below also has a live freshness label.
- **Action:** Navigate to /
- **Point out:** The Ready badge with its freshness label ('as of Ns ago') in the top-right. The GO banner below the header with its own freshness label in parentheses.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-78/step-01.png

### Step 02 — Data page maintains freshness visibility

- **Narration:** Navigate to the Data page. The Ready badge and freshness labels appear here too — they work consistently across every page of the app.
- **Action:** Click the "Data" link
- **Point out:** The Ready badge and freshness label in the header, and the GO banner below. The SNAPSHOT dates count on this page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-78/step-02.png

### Step 03 — Backtest shows historical evidence scorecard

- **Narration:** The Backtest page displays historical performance data across multiple time horizons. The ready badge remains visible in the header, confirming the data is current.
- **Action:** Click the "Backtest" link
- **Point out:** The scorecard showing return and risk metrics (1d, 5d, 10d, etc.). Notice the Ready badge with freshness label in the header.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-78/step-03.png

### Step 04 — Background compute work is transparently disclosed

- **Narration:** Request a historical date that needs fresh computation. When the app does heavy work, a 'background compute running' indicator appears in the header alongside the Ready badge, showing you when the system is actively computing.
- **Action:** Navigate to /backtest?asof=2026-07-30
- **Point out:** The 'background compute running (N)' chip in the header showing real-time work in progress.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-78/step-04.png

### Step 05 — Data page shows live computation progress details

- **Narration:** The Data page displays a live progress row whenever background compute is running. It shows the as-of date, elapsed time, and horizon completion counts so you can monitor active work in real time.
- **Action:** Click the "Data" link
- **Point out:** The background compute progress row with elapsed time and horizon details (e.g., 'elapsed Xs/1m27s · horizons 0/5→3/5').
- **Screenshot:** reports/demo/goal-ops-hardening-iter-78/step-05.png
