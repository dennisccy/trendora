# Demo Script — goal-ops-hardening-iter-53

**Mode:** record
**Date:** 2026-08-08
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Navigate to the Dashboard

- **Narration:** The dashboard loads normally, showing the current market state without errors.
- **Action:** Navigate to /
- **Point out:** Look for the Market Phase & Severity card with a real numeric severity score and phase label.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-53/step-01.png

### Step 02 — Check the readiness badge at the top right

- **Narration:** The header's readiness pill shows a solid green state with a clear status.
- **Action:** Click the "Data Manager" link
- **Point out:** The pill in the top-right corner should read 'Ready' with a green indicator.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-53/step-02.png

### Step 03 — View the Data Manager and coverage panels

- **Narration:** The Data Manager page displays the dataset coverage and universe resolution information with real numbers for universe counts and admissions.
- **Action:** Click the "Backtest" link
- **Point out:** The Dataset coverage panel shows the Universe count, Admitted count, and the breakdown of excluded items by reason. All figures should be real numbers, not blanks.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-53/step-03.png

### Step 04 — View the Backtest page with evidence scorecard

- **Narration:** The Backtest page shows the forward-test scorecard with real historical data and evidence metrics, confirming that evidence is served from storage, not computed on demand.
- **Action:** Click the "Data Manager" link
- **Point out:** Scroll down to the evidence section to see the 'Snapshots contributing' count displayed as a real number, not a loading spinner.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-53/step-04.png

### Step 05 — Check the background-compute panel on Data Manager

- **Narration:** The background-compute panel discloses any active or recently-completed background computation, with a footer explaining the scope ('process-lifetime only, never persisted').
- **Action:** Click the "Dashboard" link
- **Point out:** Look for either an active in-flight entry or a 'Last outcome' summary, confirming the backend honestly reports its background work.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-53/step-05.png

### Step 06 — Confirm badge consistency across Dashboard

- **Narration:** The readiness badge and preflight banner render consistently in the header across all three pages, confirming a single global element.
- **Action:** Click "body"
- **Point out:** The pill in the top-right corner should show the same 'Ready' state and position as it did on the earlier pages.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-53/step-06.png
