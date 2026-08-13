# Demo Script — goal-ops-hardening-iter-75

**Mode:** record
**Date:** 2026-08-13
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the home page

- **Narration:** Let's start by visiting the Trendora dashboard. This is the main entry point where users see the readiness status and latest market overview.
- **Action:** Navigate to /
- **Point out:** Notice the top-right readiness badge displays 'Ready' — this means the backend is fully initialized and serving data.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-01.png

### Step 02 — Navigate to the Data page

- **Narration:** The Data page is where users manage historical data backfills and see job history. This is the command center for keeping the database up to date.
- **Action:** Click the "Data" link
- **Point out:** The job history panel shows persisted records of all previous ingest jobs — backfills, fetches, and rebuilds — with their outcomes and per-date exclusion counts.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-02.png

### Step 03 — Start a backfill job

- **Narration:** Users can request backfills over any date range without limits. Here we'll start a small backfill of a single historical day to demonstrate how the system handles data ingestion.
- **Action:** Click the "Start" button
- **Point out:** The job begins executing with live progress updates. The system accepts any range — no artificial caps — and the ingest process runs chunked and memory-bounded.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-03.png

### Step 04 — View the backtest evidence page during background compute  [NEW]

- **Narration:** Once a backfill completes, the system computes forward-aggregate evidence in the background. Let's visit the Backtest page to see how it handles this refresh window.
- **Action:** Click the "Backtest" link
- **Point out:** Notice the 'Refreshing' banner at the top explaining the current state. While the background compute is in flight, the page serves the last-complete evidence version instantly (well under 1.5 seconds). No skeleton, no frozen frame — just honest transparency.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-04.png

### Step 05 — Observe the background-compute disclosure in the badge and data panel  [NEW]

- **Narration:** The system is transparent about its own state. The top-right badge now shows 'Ready' alongside a note about background compute running. On the Data page, a dedicated panel displays the exact same information: what is computing, how long it has been running, and the progress on each horizon.
- **Action:** Navigate to /data
- **Point out:** The badge and the Data panel's background-compute panel both read from the same source (GET /api/health) — a single source of truth. They show the as-of, elapsed time, horizons done/total, and dataset version. No estimates, no hidden activity.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-05.png

### Step 06 — Wait for background compute to complete  [NEW]

- **Narration:** The background compute runs to completion in the background. When done, the panel shows the last outcome with the actual measured duration.
- **Action:** Navigate to /data
- **Point out:** The panel transitions from an active 'computing' state to a completed state showing 'No background compute running' and the final duration. This gives operators full visibility into how long heavy operations actually took.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-06.png

### Step 07 — Return to backtest with fresh evidence  [NEW]

- **Narration:** Now that the background compute has finished, let's go back to the Backtest page to see the fresh evidence.
- **Action:** Click the "Backtest" link
- **Point out:** The 'Refreshing' banner is gone. The page now displays the freshly computed evidence, served from storage in under 1.5 seconds. This demonstrates that heavy aggregates are computed at ingest time and persisted — never recomputed on the fly at request time.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-07.png

### Step 08 — Verify quick page loads

- **Narration:** The final piece of ops-hardening is ensuring every page loads fast by fetching only what it needs. Let's check the Stocks page — it loads instantly with lazy, indexed queries rather than whole-table scans.
- **Action:** Click the "Stocks" link
- **Point out:** Pages render quickly even with a large historical dataset. The backend never streams the full 3.3M-row daily_prices table into memory. Aggregates are precomputed and persisted at ingest time, and every request path reads only indexed rows.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-75/step-08.png
