# Demo Script — goal-mcp-loop-iter-21

**Mode:** record
**Date:** 2026-07-08
**Frontend URL:** http://localhost:3255
**Iteration:** 21

## Highlights

### Step 01 — Open the Data Manager

- **Narration:** Let's check out the Data Manager — this is where Trendora keeps its price history current.
- **Action:** Navigate to /data
- **Point out:** The page loads cleanly with a form for starting a data job, and there's no 'service unavailable' message anywhere.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-01.png

### Step 02 — Choose Fetch EOD prices

- **Narration:** The job picker offers three clear choices — let's pick Fetch EOD prices to pull in the latest numbers.
- **Action:** Type "Fetch EOD prices" into the "Job kind" field
- **Point out:** As soon as Fetch is selected, a source picker appears, already defaulted to a working, available data source.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-02.png

### Step 03 — Start the Fetch job

- **Narration:** One click starts the job, and now it refreshes the whole tracked company list instead of just a small slice of it.
- **Action:** Click the "Start" button
- **Point out:** The progress panel shows the job working through 588 symbols in total — the entire tracked list, not the roughly 162 it used to cover.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-03.png

### Step 04 — See the redesigned availability calendar

- **Narration:** Scrolling down this same page, a daily calendar shows exactly what price data exists for every trading day.
- **Action:** Click "[data-testid="availability-legend-snapshot"]"
- **Point out:** The legend is now split into two clearly labeled groups — a blue scale for how much price data exists, and a separate violet ring for whether a day has been fully scored — so the two ideas can never be confused, and hovering any day spells out the difference in plain words.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-04.png

### Step 06 — Sort by Sector without a hitch

- **Narration:** Clicking Sector re-orders the whole list by industry, instantly and cleanly.
- **Action:** Click the "Sort by Sector" button
- **Point out:** The table quietly re-sorts by industry, an arrow appears next to Sector, and the page never goes blank.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-06.png

### Step 07 — Sort the other way, too

- **Narration:** One more click reverses the order just as smoothly, confirming both directions work.
- **Action:** Click the "Sort by Sector, ascending" button
- **Point out:** The arrow flips the other way, and every leadership, entry-quality, and risk score still honestly reads 'Not yet proven' rather than overclaiming a result that hasn't been certified.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-07.png

### Step 08 — Check the honest evidence ledger

- **Narration:** Let's look at the Evidence page, where Trendora tracks which trading ideas have actually proven themselves.
- **Action:** Navigate to /evidence
- **Point out:** Every claim shows a clear pass or fail against a holdout test, and nothing is ever marked proven without genuinely earning it.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-08.png

### Step 10 — Expand to full price history

- **Narration:** Switching to full history stretches the same chart back across decades in one click.
- **Action:** Click the "Full history" button
- **Point out:** The bar count more than doubles and the chart still renders cleanly, with no errors and no blank space.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-21/step-10.png

## Full tour (text only)

### Step 05 — Head to the Stock Leaderboard

- **Narration:** Now let's head over to the Stocks page, home to every company Trendora tracks.
- **Action:** Navigate to /stocks
- **Point out:** The full leaderboard of 541 companies loads with real rankings, ready for the next check.

### Step 09 — Open a company's detail page

- **Narration:** Opening a well-known company's own page shows just how deep its price history goes.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** NVIDIA's chart loads with over a thousand recent trading days ready to explore.
