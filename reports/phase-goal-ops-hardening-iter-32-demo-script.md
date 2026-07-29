# Demo Script — goal-ops-hardening-iter-32

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Navigate to the homepage

- **Narration:** We start by visiting the homepage. The backend has completed its data-loading work and the readiness badge is stable.
- **Action:** Navigate to /
- **Point out:** The top bar shows the status badge with the dataset's as-of date.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-32/step-01.png

### Step 02 — Check the Data Manager panel

- **Narration:** The Data Manager shows the full historical coverage. Aggregates are precomputed at ingest time, never on the fly.
- **Action:** Click the "Data Manager" link
- **Point out:** The dataset panel displays the complete range of available data with all coverage counts computed upfront.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-32/step-02.png

### Step 03 — View the Evidence page

- **Narration:** The Evidence page loads certified claims with their drawdown expectations. Heavy aggregates are structured to never exhaust memory.
- **Action:** Click the "Evidence" link
- **Point out:** Real numerics appear for all certified claims in the evidence cards — no blanks, no error boundaries.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-32/step-03.png

### Step 04 — Open the backtest page

- **Narration:** The backtest page serves saved forward-test results without recalculating them. The underlying aggregates are now bounded, preventing memory escalation.
- **Action:** Navigate to /backtest
- **Point out:** The backtest renders real figures from storage, showing the current market regime and candidate counts.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-32/step-04.png

## Full tour (text only)

### Step 05 — Verify backend readiness remains stable

- **Narration:** The status badge at the top confirms the backend is ready. The service stays responsive even under concurrent requests.
- **Action:** Navigate to /
- **Point out:** The readiness indicator shows 'Ready' and any background activity is disclosed honestly in the status panel.
