# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11

**Mode:** record
**Date:** 2026-06-13
**Frontend URL:** http://localhost:3835
**Iteration:** 11

## Highlights

### Step 01 — Sectors leaderboard loads with ranked ETFs  [NEW]

- **Narration:** The sectors page shows every tracked ETF ranked from strongest to weakest by a composite momentum score. Both sector-index ETFs and industry-group ETFs appear together in one ordered table.
- **Action:** Navigate to /sectors
- **Point out:** 31 ETF rows ordered by score — SOXX at rank 1 with 93.67, ITB at the bottom with 7.17. Both sector and industry ETFs are interleaved by score.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-01.png

### Step 02 — Expand SMH — human-readable industry name in header  [NEW]

- **Narration:** Clicking the expand toggle on an industry ETF row now shows a proper display name in the panel header instead of the bare ticker. SMH opens as Semiconductors (VanEck) so you instantly know what group you are looking at.
- **Action:** Click the "SMH" button
- **Point out:** Panel header reads 'SMH — Semiconductors (VanEck)', not just 'SMH'. The configured display name is shown.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-02.png

### Step 03 — SMH panel shows plain-language description  [NEW]

- **Narration:** Below the header, a one-line description tells you what the industry group actually covers in plain English — no guesswork about what SMH tracks.
- **Action:** Navigate to /sectors
- **Point out:** Description reads 'Largest US-listed semiconductor makers and equipment suppliers.' — distinct from the score breakdown table below it.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-03.png

### Step 04 — SMH members list with config-defined label and expand  [NEW]

- **Narration:** Each industry ETF panel now lists its mapped universe stocks as clickable ticker chips. The section heading 'Members (config-defined)' tells you these memberships come from the portfolio configuration, not an automated sector mapping.
- **Action:** Click the "+21" button
- **Point out:** Member chips ADI, AMAT, AMD, ARM, ASML, AVGO appear with a '+21' overflow button. The heading clearly reads 'Members (config-defined)'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-04.png

### Step 05 — XLK sector ETF shows universe members  [NEW]

- **Narration:** Sector-index ETFs like XLK also get the member chip list, showing every universe stock mapped to the Technology sector. Click any chip to jump straight to that stock's detail page in a new tab.
- **Action:** Navigate to /sectors
- **Point out:** XLK expanded panel shows 6 initial chips (AAPL, ADBE, ADI, AMAT, AMD, ANET) plus a '+52' button. Heading reads 'Members'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-05.png

### Step 06 — KRE unmapped ETF shows honest empty state  [NEW]

- **Narration:** When an ETF has no stocks mapped to it, the panel says so clearly with a single message — no fabricated names, no blank space, just a straightforward explanation.
- **Action:** Click the "KRE" button
- **Point out:** KRE panel header reads 'KRE — Regional Banks (SPDR)' and the members section shows 'No universe members are mapped to this ETF (config-defined).' with zero chips.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-06.png

### Step 07 — Historical snapshot — member chips carry the as-of date  [NEW]

- **Narration:** When you view the sectors leaderboard at a past date, every member chip link automatically picks up that date. Clicking a chip opens the stock detail at exactly the same historical snapshot, not today's data.
- **Action:** Navigate to /sectors?asof=2025-11-28
- **Point out:** On /sectors?asof=2025-11-28 the ADI chip href reads '/stocks/ADI?asof=2025-11-28' — the date travels with the link.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-07.png

### Step 08 — Score-component breakdown still intact alongside new sections

- **Narration:** The existing score-component breakdown — relative strength percentiles, moving average stack, distance from 52-week high — is untouched. The new name, description, and member sections sit alongside it, not in place of it.
- **Action:** Navigate to /sectors
- **Point out:** SMH expanded panel shows RS vs SPY 1m/3m/6m with percentile and contribution values, plus the description and member chips below — all coexisting in the same panel.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11/step-08.png
