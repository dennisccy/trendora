# Demo Script — goal-market-compass-iter-29

**Mode:** record
**Date:** 2026-09-01
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Today page

- **Narration:** We're looking at the Today page, which gives a ten-second read of market conditions after the close. Let's start by opening it.
- **Action:** Navigate to /
- **Point out:** The page shows the heading 'Today', the subtitle 'The ten-second read after the close', and a date badge in the top right.
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-01.png

### Step 02 — Open the date picker

- **Narration:** The top bar has a date selector button showing 'Latest'. Let's click it to see available snapshot dates.
- **Action:** Click the element
- **Point out:** A calendar popover opens, showing August 2026 with clickable day cells.
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-02.png

### Step 03 — Jump to August 3rd  [NEW]

- **Narration:** August 3rd, 2026 is a date we've prepared with real market data. Clicking it will load the Today page for that date.
- **Action:** Click the element
- **Point out:** The URL changes to include 'asof=2026-08-03', and the top-bar badge turns amber showing 'Viewing as-of 2026-08-03 (historical)'.
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-03.png

### Step 04 — Read the market state badges  [NEW]

- **Narration:** The 'Market state' card shows three key indicators. For the first time on this page, instead of placeholder text, they now display real market conditions in plain English.
- **Action:** Click the element
- **Point out:** Three small badges appear: 'improving' next to Regime, 'improving' next to Market phase, and 'little changed' next to Breadth. None of them says 'NA'.
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-04.png

### Step 05 — Check the summary for consistency  [NEW]

- **Narration:** Let's scroll down to the Summary card and read its opening sentence. It should agree with the Regime badge we just saw.
- **Action:** Click the element
- **Point out:** The Summary card's first sentence reads 'Conditions are improving since the prior session (+4.7 regime-score points).' The word 'improving' matches the Regime badge.
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-05.png

### Step 06 — Refresh to verify the data is permanent

- **Narration:** Let's refresh the page to make sure this data is permanently stored, not just a one-time display.
- **Action:** Navigate to /?asof=2026-08-03
- **Point out:** After the refresh, the URL is still '?asof=2026-08-03' and all three badges show the exact same words as before.
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-06.png

### Step 07 — Return to Latest to confirm the feature is scoped

- **Narration:** Let's go back to the Latest date to confirm that this new real-word rendering is scoped only to August 3rd. Other dates should still show placeholders.
- **Action:** Navigate to /
- **Point out:** The three badges in the Market state card revert to 'NA', and the date badge shows 'Data as-of 2026-08-12' (the current frontier).
- **Screenshot:** reports/demo/goal-market-compass-iter-29/step-07.png
