# Demo Script — goal-ops-hardening-iter-31

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Navigate to the homepage

- **Narration:** We start by visiting the homepage. The backend is ready with all its data-loading work complete.
- **Action:** Navigate to /
- **Point out:** The top bar shows the status badge and the dataset's as-of date.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-31/step-01.png

### Step 02 — Open the Evidence page

- **Narration:** The Evidence page shows drawdown expectations for backtest claims. This page was fixed in an earlier iteration and stays reliable.
- **Action:** Click the "Evidence" link
- **Point out:** The evidence page loads real numbers for certified claims, no blank spaces where figures should be.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-31/step-02.png

### Step 03 — Check the backtest data page

- **Narration:** The Data Manager panel shows the coverage of historical data. Background compute is organized and bounded now.
- **Action:** Click the "Data Manager" link
- **Point out:** The dataset panel shows the full range of available data with coverage counts, all computed at ingest time.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-31/step-03.png

### Step 04 — Visit Factor Lab to verify the crash is fixed  [NEW]

- **Narration:** Factor Lab shows every factor in the catalog with its rank correlations at every horizon. This page crashed with out-of-memory errors until now.
- **Action:** Navigate to /research/factor-lab
- **Point out:** The decile table loads with real rank-IC values for all factors across all horizons — no crash, no error boundary.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-31/step-04.png

## Full tour (text only)

### Step 05 — Confirm the backend health is stable

- **Narration:** The status badge at the top right confirms the backend readiness and background compute activity. A single-flight guard prevents duplicate work under concurrent load.
- **Action:** Navigate to /
- **Point out:** The readiness badge shows 'Ready' and any background work is disclosed honestly.

### Step 06 — Check a backtest result

- **Narration:** The backtest page loads saved results efficiently. Heavy aggregates stay bounded and never risk taking the service down.
- **Action:** Navigate to /backtest
- **Point out:** The backtest result displays real numerics from the saved computation, not a recalculated value.
