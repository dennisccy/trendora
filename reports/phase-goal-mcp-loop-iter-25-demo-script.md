# Demo Script — goal-mcp-loop-iter-25

**Mode:** record
**Date:** 2026-07-09
**Frontend URL:** http://localhost:3255
**Iteration:** 25

## Highlights

### Step 01 — Today's market regime, at a glance

- **Narration:** Open the Trendora dashboard — no sign-in required. It shows today's market regime and links straight to the evidence behind that call.
- **Action:** Navigate to /
- **Point out:** The Market Regime panel reads 'Risk-on 72.25' with a link into the evidence ledger.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-01.png

### Step 02 — One click to the honest evidence ledger

- **Narration:** Follow the dashboard's link straight into the evidence ledger backing today's regime.
- **Action:** Click the "See evidence proven in this regime" link
- **Point out:** The Breakout-watch claim for this regime is honestly marked FAIL with its real holdout number — nothing is shown as proven unless it actually passed.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-02.png

### Step 03 — Browse the full leaderboard

- **Narration:** Head to the Stocks leaderboard, showing every company in the tracked universe with its scores.
- **Action:** Navigate to /stocks
- **Point out:** 541 / 541 confirms the whole universe is represented, and every score still carries an honest 'Not yet proven' tag.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-03.png

### Step 04 — Sort the leaderboard by sector

- **Narration:** Click the Sector column to regroup the whole leaderboard by industry.
- **Action:** Click the "Sort by Sector" button
- **Point out:** The table regroups alphabetically by sector (Communication Services, Consumer Discretionary, ...) with no crash or blank table.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-04.png

### Step 05 — A single stock's detail page

- **Narration:** Open a single company's detail page to see its price chart and the same honest scoring shown on the leaderboard.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The same 'Not yet proven' honesty label follows every score onto the stock's own page.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-05.png

### Step 06 — See decades of price history

- **Narration:** Click 'Full' on the chart toggle to expand from the recent window out to decades of price history.
- **Action:** Click "[data-testid="chart-range-full"]"
- **Point out:** The chart redraws with deep history and a note that older bars are weekly-sampled — a real re-render, not just a label flip.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-06.png

### Step 07 — The Data Manager page — proven solid again

- **Narration:** Visit the Data Manager page, which tracks how much data Trendora holds and how complete it is.
- **Action:** Navigate to /data
- **Point out:** Dataset coverage and Storage footprint both render fully — 541 companies, 3,293,160 price bars, 1.22 GB on disk. This is the exact page that could previously crash the whole app right after a restart; it now loads cleanly every time.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-25/step-07.png
