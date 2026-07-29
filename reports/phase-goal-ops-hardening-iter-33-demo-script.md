# Demo Script — goal-ops-hardening-iter-33

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Dashboard

- **Narration:** We're visiting the homepage to see the daily snapshot at a glance, verifying the frontend loads cleanly in production mode.
- **Action:** Navigate to /
- **Point out:** The Dashboard heading, subtitle, and regime/phase panels load without errors or the Next.js dev-overlay pill.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-01.png

### Step 02 — Navigate to the Stocks leaderboard

- **Narration:** Click Stocks in the sidebar to browse the ranked stock leaderboard—still clean and responsive in production mode.
- **Action:** Click the "Stocks" link
- **Point out:** The Stocks heading appears and the leaderboard table populates with ranked rows.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-02.png

### Step 03 — Search for AAPL and click its row

- **Narration:** Type 'AAPL' into the search field and click the matching row to drill into the stock's detail page, confirming cross-page navigation works.
- **Action:** Type "AAPL" into "Search ticker or name…"
- **Point out:** The leaderboard filters to show AAPL, then clicking it navigates to the stock detail page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-03.png

### Step 04 — View the AAPL stock detail with three explainable scores

- **Narration:** The stock detail page shows Leadership, Entry Quality, and Risk scores—three explainable figures, never blank or undefined.
- **Action:** Click the element
- **Point out:** Three score cards render with numeric scores or honest NA states; no dev-overlay pill appears anywhere on the page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-04.png

### Step 05 — Navigate to Data Manager and verify the run history

- **Narration:** The Data Manager shows coverage stats and ingest job history—the page loads without spinners or blank panels, confirming that data-loading endpoints work under production mode.
- **Action:** Click the "Data Manager" link
- **Point out:** The Data Manager heading, coverage tiles, and run history panel all render with real data.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-05.png

### Step 06 — Open Research and click the Regime Lab card

- **Narration:** The Research page hosts the Regime Lab—a two-click path from the Dashboard, unchanged by the launcher fix, demonstrating stable navigation.
- **Action:** Click the "Research" link
- **Point out:** The Research page shows available lab cards, and clicking Regime Lab navigates to that research tool.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-06.png

### Step 07 — View the Backtest page with past scan evidence

- **Narration:** The Backtest page lets you rewind to a past scan date and see forward-test evidence—a complete, data-rich page that loads cleanly, confirming the platform's core analytical pages work in production mode.
- **Action:** Click the "Backtest" link
- **Point out:** The Backtest heading and 'As-of scan summary' section render fully with honest NA or real figures; no loading skeleton lingers.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-07.png

### Step 08 — Browse the Watchlist—your saved stocks

- **Narration:** The Watchlist page displays your saved stocks with concentration analysis—the page loads without errors, showing that production mode handles multiple data sources gracefully.
- **Action:** Click the "Watchlist" link
- **Point out:** The Watchlist heading and saved stock rows render; if saved tickers exist, the concentration X-ray panels appear.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-33/step-08.png
