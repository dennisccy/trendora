# Demo Script — goal-mcp-loop-iter-38

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3255
**Iteration:** 38

## Highlights

### Step 01 — Start at the Dashboard

- **Narration:** Every session starts here on the Dashboard — let's head over to the Watchlist to see what's new this time.
- **Action:** Navigate to /
- **Point out:** The familiar left sidebar, with Watchlist among the items.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-01.png

### Step 02 — Open the Watchlist  [NEW]

- **Narration:** The Watchlist page hasn't moved — same saved-stocks table as always — but scrolling down now reveals something brand new underneath it.
- **Action:** Click the "Watchlist" link
- **Point out:** The existing entries table for ABBV and MSFT, and below it a new "Concentration X-ray" card headlined "≈ 2.0 effective independent bets".
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-02.png

### Step 03 — See how correlated the two names really are  [NEW]

- **Narration:** A real, computed correlation shows exactly how ABBV and MSFT move relative to each other — a number, not just a guess or a color with nothing behind it.
- **Action:** Navigate to /watchlist
- **Point out:** The ABBV × MSFT cell reading "-0.11" in red, right where the two rows and columns cross.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-03.png

### Step 04 — See the cluster grouping  [NEW]

- **Narration:** Because ABBV and MSFT aren't correlated enough to move together, the X-ray keeps them as two separate clusters instead of merging them into one.
- **Action:** Navigate to /watchlist
- **Point out:** Two separate gray badges — "ABBV" and "MSFT" — under the Clusters heading, not one joined badge.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-04.png

### Step 05 — See where the watchlist is concentrated  [NEW]

- **Narration:** Three bar breakdowns show sector, theme, and shared-setup concentration for the whole list — including an honest "Unassigned" bucket for any stock without a mapped sector, never a blank or crashed row.
- **Action:** Navigate to /watchlist
- **Point out:** The "Technology" and "Unassigned" sector bars, three theme bars, and a single red "Avoid" setup bar that reuses the exact same red used in the table above.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-05.png

### Step 06 — Check the methodology behind the headline  [NEW]

- **Narration:** Clicking the small info icon next to "effective independent bets" opens a plain-language explanation of exactly how that number is worked out.
- **Action:** Click the "What is effective independent bets?" button
- **Point out:** The tooltip spelling out both the 126-trading-day window and the 60-day minimum-history requirement, in plain language.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-06.png

### Step 08 — Watch the X-ray update live

- **Narration:** Adding AAPL grows the correlation grid from 2×2 to 3×3 automatically — every figure recalculates from the real saved list, nothing is hand-entered.
- **Action:** Click the "Add" button
- **Point out:** The new AAPL row in the entries table, and the correlation grid now covering three names instead of two.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-38/step-08.png

## Full tour (text only)

### Step 07 — Add a new name

- **Narration:** Typing a new ticker into the existing Add form sets up a live test of the X-ray — the next step shows the whole grid grow to include it.
- **Action:** Type "AAPL" into "e.g. ANET"
- **Point out:** "AAPL" typed into the Ticker field, ready to add.

### Step 09 — Remove the demo name and confirm the list is restored

- **Narration:** Removing AAPL again shrinks the grid straight back to the original ABBV/MSFT view, confirming the new section never disturbs the existing watchlist.
- **Action:** Click the "Remove AAPL from the watchlist" button
- **Point out:** The entries table back to two rows, and the X-ray matching its original figures.
