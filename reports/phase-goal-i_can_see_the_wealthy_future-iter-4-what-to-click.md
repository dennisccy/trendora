# Phase goal-i_can_see_the_wealthy_future-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3836`
- Backend API running and seeded (NVDA present in the scanned universe with price history)
- No login required

---

## Verification Steps

<!-- Prioritized: 1) the new chart works, 2) themes + invalidation are real, 3) scores still match the leaderboard (J-06 regression). -->

1. Open `http://localhost:3836/stocks` in your browser
   - **Expect:** The leaderboard table loads with stock rows (e.g. NVDA), no error page

2. Click the "NVDA" row in the table
   - **Expect:** URL changes to `http://localhost:3836/stocks/NVDA`; heading "NVDA" is shown at the top

3. Find the "Price & moving averages" card and look at the chart
   - **Expect:** Green/red candlesticks are painted (not a blank box); the card header caption reads something like "1356 bars · as of 2026-05-29"
   - **Broken looks like:** an empty/grey rectangle where the chart should be, or a "0 bars" caption

4. Look at the four coloured lines over the candles and the legend below the chart
   - **Expect:** Four moving-average lines (each starting after a warm-up gap) and a legend reading "Candles (up / down)  20-DMA  50-DMA  150-DMA  200-DMA  Volume"; a volume histogram sits along the bottom of the chart

5. Find the "Themes" label (second card, top-left) and click the "Semiconductors" chip
   - **Expect:** Accent-coloured chips like "Ai Data Centre", "Semiconductors", "Megacap Leaders" are shown; clicking one navigates to `http://localhost:3836/themes`

6. Go back, then read the note under the "Invalidation" label (second card, top-right)
   - **Expect:** A plain-language line such as "Invalid below the 50-DMA at $198.73" with a real dollar value, in grey text
   - **Broken looks like:** "$0.00", a blank value, or a fabricated-looking number with no MA basis

7. Note the Leadership / Entry Quality / Risk bucket letters and numbers on this page, then open `http://localhost:3836/stocks` and find the NVDA row
   - **Expect:** The three bucket letters and 0–100 values on the detail page match the NVDA row on the leaderboard exactly (single source of truth — J-06 still holds)

8. Navigate to `http://localhost:3836/stocks/NOTREAL`
   - **Expect:** An amber "Unknown ticker" card reading ""NOTREAL" is not in the scanned universe…"; no chart and no fabricated data; the "leaderboard" link returns you to `/stocks`

---

## What "Working Correctly" Looks Like

- The "Price & moving averages" card shows a populated candlestick chart with four MA overlay lines, a volume histogram, and a complete legend
- The "Invalidation" note states a concrete dollar level tied to the 50-DMA (or an honest amber "Invalidation level NA — insufficient history" for short-history stocks)
- Theme chips link to `/themes`, and the three score cards remain byte-identical to the leaderboard row

## Common Issues

- **Blank/grey chart box:** Backend `/api/stocks/NVDA/bars` may be down — check the backend is running; an honest "Chart unavailable" amber box (not a blank canvas) is the correct degraded state
- **Whole page shows red "Backend unavailable":** the scores API is unreachable — restart the backend and reload
- **Scores differ between leaderboard and detail:** this is a J-06 regression — flag it; the detail row must equal the list row exactly
