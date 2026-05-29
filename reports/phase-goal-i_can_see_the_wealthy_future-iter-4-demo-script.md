# Demo Script — goal-i_can_see_the_wealthy_future-iter-4

**Mode:** record
**Date:** 2026-05-30
**Frontend URL:** http://localhost:3836
**Iteration:** 4

## Highlights

### Step 01 — Open the Stock Leaderboard

- **Narration:** We start on the Stock Leaderboard, where every scanned stock is ranked and each row shows its Leadership, Entry Quality, and Risk scores alongside a setup status and a plain-language reason.
- **Action:** Navigate to /stocks
- **Point out:** The ranked table of stocks — every row carries three scores, a setup badge, and a short reason.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-4/step-01.png

### Step 02 — Open NVDA's full research view  [NEW]

- **Narration:** Clicking the NVDA row opens its detail page — the complete per-stock research view. Right at the top we can see which themes NVDA belongs to and the concrete price level where the trade idea would be wrong.
- **Action:** Click the "NVDA" link
- **Point out:** The clickable theme chips (such as Semiconductors) and the invalidation note in plain language — “Invalid below the 50-DMA at $…” — with a real dollar level, not a placeholder.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-4/step-02.png

### Step 03 — Study the price and moving-average chart  [NEW]

- **Narration:** Scrolling to the price chart, we can read NVDA's daily candles with the 20-, 50-, 150-, and 200-day moving averages drawn on top and a volume histogram pinned along the bottom.
- **Action:** Click "Candles (up / down)"
- **Point out:** Green and red candles, four coloured moving-average lines (each starting after a warm-up gap), the volume bars below them, and a legend mapping every colour to its period.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-4/step-03.png

### Step 04 — Read the three explainable scores

- **Narration:** Further down, the three scores each show an A-to-E grade, a value out of 100, and the named components behind it — so no score is ever shown as a bare number. These values are the same ones we saw on the leaderboard.
- **Action:** Click "How strong the stock is"
- **Point out:** The Leadership, Entry Quality, and Risk cards — each with a bucket grade, a 0-to-100 value, and a component breakdown of the reasons.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-4/step-04.png

### Step 05 — Jump from a theme chip to the Themes leaderboard  [NEW]

- **Narration:** The theme chips are live links. Clicking the Semiconductors chip takes us straight to the Themes leaderboard to explore that whole group.
- **Action:** Click the "Semiconductors" link
- **Point out:** The browser navigates to the Themes leaderboard, where Semiconductors is ranked among the tracked themes.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-4/step-05.png

### Step 06 — An honest state for an unknown ticker

- **Narration:** Finally, asking for a ticker that isn't in the scanned universe shows an honest amber notice instead of inventing data, with a link back to the leaderboard.
- **Action:** Navigate to /stocks/NOTREAL
- **Point out:** The amber “Unknown ticker” card — no chart and no fabricated numbers, just a clear message and a way back to the leaderboard.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-4/step-06.png
