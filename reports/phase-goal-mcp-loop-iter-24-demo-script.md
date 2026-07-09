# Demo Script — goal-mcp-loop-iter-24

**Mode:** record
**Date:** 2026-07-09
**Frontend URL:** http://localhost:3255
**Iteration:** 24

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Let's start at Trendora's home dashboard, where traders get their first look at the market each day.
- **Action:** Navigate to /
- **Point out:** A green status badge in the corner confirms the backend is up and ready to serve real data.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-24/step-01.png

### Step 02 — Check the Data Manager's storage footprint  [NEW]

- **Narration:** From the sidebar we head into the Data Manager, which now shows exactly how much data the platform is holding.
- **Action:** Click the "Data Manager" link
- **Point out:** Right below the existing dataset numbers, a brand-new Storage footprint card shows the database's file size plus the price-bar, scanner-result, and forward-return counts it holds.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-24/step-02.png

### Step 04 — Search for Apple (AAPL)

- **Narration:** Typing a ticker into the search box instantly narrows hundreds of rows down to the one we want.
- **Action:** Type "AAPL" into "Search ticker or name…"
- **Point out:** AAPL's row shows its sector and its "Megacap Leaders" theme alongside its scores.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-24/step-04.png

### Step 05 — Open AAPL's own page

- **Narration:** Clicking straight into AAPL's detail page confirms it tells the exact same story as the leaderboard row.
- **Action:** Click the "AAPL" link
- **Point out:** The leadership score reads 55.78, matching the leaderboard exactly, with no discrepancy between the two views.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-24/step-05.png

### Step 06 — Switch to the full price history

- **Narration:** Toggling the chart from Recent to Full history pulls up decades of price action for the same stock.
- **Action:** Click the "Full history" button
- **Point out:** The chart redraws with far more history, and a small note explains the older bars are weekly-sampled to keep the chart readable.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-24/step-06.png

### Step 08 — Test the job form with a bad date

- **Narration:** We try entering a nonsense date into the data-job form to make sure it still catches the mistake.
- **Action:** Type "2024-13-40" into the "Start date" field
- **Point out:** A clear red message flags the invalid date, and the Start button stays disabled until it's corrected.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-24/step-08.png

## Full tour (text only)

### Step 03 — Browse the stock leaderboard

- **Narration:** Next stop is the stock leaderboard, where hundreds of companies are ranked side by side on the same scores.
- **Action:** Navigate to /stocks
- **Point out:** Each row carries its own leadership, entry-quality, risk, and setup scores.

### Step 07 — Back to the Data Manager

- **Narration:** Returning to the Data Manager confirms the same storage numbers we saw earlier haven't drifted.
- **Action:** Navigate to /data
- **Point out:** The Storage footprint figures read exactly the same as before, even after browsing elsewhere.

### Step 09 — Peek at the watchlist

- **Narration:** A quick stop at the watchlist shows the names being tracked, each still carrying its trusted scores.
- **Action:** Navigate to /watchlist
- **Point out:** Saved tickers appear here with the reason they were added, alongside the same scores shown on the leaderboard.

### Step 10 — Visit the evidence ledger

- **Narration:** Last stop is the evidence ledger, the audit trail behind every trading idea this product has tested.
- **Action:** Navigate to /evidence
- **Point out:** Every idea's real, out-of-sample track record lives here, so nothing is ever called proven unless it actually earned that label.
