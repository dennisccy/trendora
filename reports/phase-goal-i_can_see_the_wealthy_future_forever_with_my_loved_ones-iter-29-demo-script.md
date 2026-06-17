# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29

**Mode:** record
**Date:** 2026-06-17
**Frontend URL:** http://localhost:3835
**Iteration:** 29

## Highlights

### Step 01 — Dashboard with new Market Phase & Severity card  [NEW]

- **Narration:** The Dashboard homepage now shows a brand-new Market Phase & Severity card directly below the Major Indexes & Regime card. At today's date the card shows a green Expansion badge and a very low bear probability — the market is in a healthy expansion.
- **Action:** Navigate to /
- **Point out:** Look for the 'Market Phase & Severity' card heading and its green 'Expansion' badge alongside 'P(bear) 0.00'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-01.png

### Step 02 — Severity score and named component breakdown  [NEW]

- **Narration:** The card body breaks down the 0–100 severity score into five named drivers — drawdown depth, time underwater, market regime, breadth below the 200-day moving average, and the VIX stress gate — each with its own numeric value and point contribution. Nothing is a bare number; every figure is explained.
- **Action:** Navigate to /
- **Point out:** Read the five rows in the breakdown table (Drawdown depth, Time underwater, Market regime (stored), Breadth below 200-DMA, VIX stress gate) and the headline severity figure such as '28.75 / 100 severity'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-02.png

### Step 03 — Observation chips showing the bear-probability inputs  [NEW]

- **Narration:** Below the breakdown table, the card reveals the series of stress readings that fed into the bear-probability calculation — one small chip per observation, each hoverable for the per-date stress value and P(bear). The total count of observations is disclosed so the number is never opaque.
- **Action:** Navigate to /
- **Point out:** Notice the row labeled 'FILTER OBSERVATIONS · DRIVES P(BEAR)' and the row of date chips below the breakdown table, along with the count label such as 'SHOWING LATEST 60 OF 1170'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-03.png

### Step 04 — Time-travel to the 2022 bear market — red badge, severity 92  [NEW]

- **Narration:** Stepping the global as-of date back to October 2022 — the depth of the year's sell-off — the card switches to a bold red Bear badge, the severity jumps to 92 out of 100, and the bear probability reaches 1.00. No page reload is needed; the card repoints automatically with the existing date control.
- **Action:** Navigate to /?asof=2022-10-07
- **Point out:** The phase badge turns red and reads 'Bear'. The severity is 92.45 / 100. The P(bear) badge shows '1.00' in red. The drawdown figure shows approximately -23%.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-04.png

### Step 05 — P(bear) near 1.00 during the 2022 bear — fully causal  [NEW]

- **Narration:** At this same 2022 date the bear-probability filter, running only on information available on that day, produced a reading of 1.00 — reflecting the prolonged drawdown, elevated VIX, and weak breadth visible at the time. This is a historical replay, not a recomputed hindsight figure.
- **Action:** Navigate to /?asof=2022-10-07
- **Point out:** The 'P(bear) 1.00' badge next to the Bear label confirms the filter reached maximum confidence using only data known on 2022-10-07.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-05.png

### Step 06 — Pullback phase gets an amber badge — three distinct colors  [NEW]

- **Narration:** When the market is in a Pullback — a mild dip within a larger uptrend — the badge turns amber, sitting visually between the green of Expansion and the red of Bear. Three clearly distinct colors make it easy to read the market cycle state at a glance.
- **Action:** Navigate to /?asof=2024-12-31
- **Point out:** At 2024-12-31 the badge shows 'Pullback' in amber (yellow-orange), clearly different from both the green and red badges shown at other dates.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-06.png

### Step 07 — Insufficient-history date shows an honest NA — never fabricated  [NEW]

- **Narration:** On dates very early in the dataset, before enough benchmark bars exist to derive a phase, the card shows an explicit message rather than inventing a value. The app is honest about what it does not know.
- **Action:** Navigate to /?asof=2021-01-05
- **Point out:** At 2021-01-05 the card body shows 'Not enough history to derive a market phase for this date' with the minimum bar-count requirement. No severity number and no phase badge appear.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-07.png

### Step 08 — Stocks leaderboard unaffected — no regression

- **Narration:** The new market-phase panel is purely additive. The stocks leaderboard continues to work exactly as before — scores, setups, and detail pages are all intact.
- **Action:** Navigate to /stocks
- **Point out:** The /stocks page shows ranked stock rows with scores. Clicking any ticker opens the stock detail page without errors, confirming no regression from the new Dashboard card.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29/step-08.png
