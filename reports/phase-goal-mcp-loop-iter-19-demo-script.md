# Demo Script — goal-mcp-loop-iter-19

**Mode:** record
**Date:** 2026-07-07
**Frontend URL:** http://localhost:3255
**Iteration:** 19

## Highlights

### Step 01 — Open the Stock Leaderboard

- **Narration:** Let's start on the Stocks page — home to every company Trendora tracks, ranked by strength, entry quality, and risk.
- **Action:** Navigate to /stocks
- **Point out:** The full leaderboard of 541 companies loads cleanly with real numbers — no error banner, no stuck loading skeleton.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-01.png

### Step 02 — Sort by Sector without a hitch  [NEW]

- **Narration:** Now let's sort the leaderboard by Sector — this exact click used to crash the whole app, so it's worth seeing it work smoothly now.
- **Action:** Click the "Sort by Sector" button
- **Point out:** The table quietly re-sorts by sector name, an up arrow appears next to Sector, and the sidebar navigation stays right where it was.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-02.png

### Step 03 — Sort the other way too  [NEW]

- **Narration:** One more click reverses the order, just to make sure the fix holds up in both directions.
- **Action:** Click the "Sort by Sector, ascending" button
- **Point out:** The arrow flips to point down, and a large block of honestly-labeled 'Unassigned' companies now sits near the top — proof the sort is genuinely re-ordering the real data, not silently failing.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-03.png

### Step 04 — Isolate the unmapped companies  [NEW]

- **Narration:** The Sector filter now offers an honest 'Unassigned' option, so it's easy to see exactly which companies don't have an industry label yet.
- **Action:** Navigate to /stocks?sector=Unassigned
- **Point out:** The row count narrows from the full 541 down to just the Unassigned companies, and every visible row's Sector cell reads 'Unassigned' instead of being blank.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-04.png

### Step 05 — Check an individual unmapped company  [NEW]

- **Narration:** Opening one of those companies' own detail pages shows the same honest labeling carried all the way through.
- **Action:** Navigate to /stocks/GL
- **Point out:** Right beside the setup status, the page reads 'Unassigned' instead of a blank space or an error, and everything else on the page renders normally.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-05.png

### Step 06 — Open the Data Manager page  [NEW]

- **Narration:** The Data Manager page tracks how much price history is loaded — it used to risk hanging the whole app on a fresh visit, so let's confirm it now loads smoothly.
- **Action:** Navigate to /data
- **Point out:** The Dataset coverage panel appears quickly with real figures — no 'Backend unavailable' message and no long stall.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-06.png

### Step 07 — Browse the universe's history  [NEW]

- **Narration:** Further down the page, a timeline shows how the tracked universe has grown and changed over the decades — let's page back through a few earlier snapshots.
- **Action:** Click the "Next page of snapshot dates" button
- **Point out:** Each page shows a real historical snapshot date with its own companies entering and exiting the universe — nothing here is invented.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-07.png

### Step 08 — See the honest evidence ledger

- **Narration:** Finally, let's look at the Evidence page, where Trendora keeps itself honest about which patterns are actually proven.
- **Action:** Navigate to /evidence
- **Point out:** Every claim shows a clear pass/fail verdict and, where relevant, which market regime it was tested in — like this 'Regime: Risk-on' badge — and nothing is ever called proven until it has genuinely earned it.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-19/step-08.png

## Full tour (text only)

### Step 09 — Confirm a mapped company is unaffected

- **Narration:** As a sanity check, a well-known company like NVIDIA still shows its real sector, completely unaffected by this fix.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** NVDA's detail page still reads 'Technology,' exactly as before.

### Step 10 — See the full price history

- **Narration:** On that same page, switching to the full price history still works, showing years of data in one view.
- **Action:** Click the "Full history" button
- **Point out:** The chart widens and the caption updates to show just how far back the history goes.
