# Demo Script — goal-ops-hardening-iter-57

**Mode:** record
**Date:** 2026-08-10
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Sign in and reach the homepage

- **Narration:** We start on the homepage where the global readiness badge in the header confirms the backend is ready to serve pages quickly.
- **Action:** Navigate to /
- **Point out:** The badge in the top-right of the header reads 'Ready' (green dot) within about a second — no long stall.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-01.png

### Step 02 — Open the Data Manager page

- **Narration:** The Data Manager shows a calendar grid of all the dates with price snapshots. Each colored cell represents a day when the ingest job successfully captured data.
- **Action:** Click the "Data Manager" link
- **Point out:** The 'Per-date availability' card shows a real colored calendar grid of days — not the message 'No availability yet'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-02.png

### Step 03 — View the stock detail page for AAPL  [NEW]

- **Narration:** The stock detail page loads its price chart and moving-average lines much faster than before. The chart caption shows the bar count, as-of date, and full history span.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The chart caption displays real text like 'N bars · as of YYYY-MM-DD · history since YYYY-MM-DD' with moving-average lines rendered below.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-03.png

### Step 04 — Check the health call timing in the browser Network tab  [NEW]

- **Narration:** Open DevTools to inspect the performance of the GET /api/health call. This global readiness check now answers in about 10–15 milliseconds at rest, down from 160–240 milliseconds.
- **Action:** Click the "Data Manager" link
- **Point out:** The GET /api/health request in the Network tab completes in well under 100 milliseconds on every page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-04.png

### Step 05 — Check the stock bars call timing in the browser Network tab  [NEW]

- **Narration:** On the stock detail page, the GET /api/stocks/AAPL/bars?through=latest call now returns in well under 1.5 seconds. This improvement is especially noticeable on stocks with deep price histories.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The GET /api/stocks/AAPL/bars?through=latest request in the Network tab completes in under 1.5 seconds, measured via browser resource timing.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-05.png

### Step 06 — Observe the calendar grid during an active ingest  [NEW]

- **Narration:** When a data-fetch job is running in the background, the availability heatmap no longer falsely claims 'No availability yet'. Instead, it shows the real, previously-computed calendar grid with an honest 'updating' banner above it.
- **Action:** Navigate to /data
- **Point out:** The per-date availability card shows colored day cells with a calm 'Data as of <version> — updating' banner directly above the grid. The grid never disappears into an empty state.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-06.png

### Step 07 — Verify the stale banner is calm and clear, not alarming  [NEW]

- **Narration:** The stale banner uses muted gray text and a calm border — the same visual treatment as other 'as of' notices on the page. It communicates the status factually: the data is real but slightly behind the very latest ingest.
- **Action:** Navigate to /data
- **Point out:** The stale banner reads 'Data as of <version> — updating' and sits directly above the calendar grid with calm, muted styling (no red or alarm colors).
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-07.png

### Step 08 — Backfill honors large date ranges without a cap

- **Narration:** Large backfills (370+ days) are accepted and chunked into batches, so the UI never rejects a reasonable request. The job history shows all the details: date count, already-snapshotted count, and non-trading days.
- **Action:** Navigate to /data
- **Point out:** The job runs to completion, showing stage timings and the breakdown: 'N calendar days · M already snapshotted · P non-trading'.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-57/step-08.png
