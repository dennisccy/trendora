# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-10

**Mode:** record
**Date:** 2026-06-02
**Frontend URL:** http://localhost:3835
**Iteration:** 10

## Highlights

### Step 01 — Open the Trendora workstation

- **Narration:** We start on Trendora's daily dashboard — the dark, research-only workstation that ranks the market after each close. The left sidebar now carries a brand-new Research section.
- **Action:** Navigate to /
- **Point out:** The left sidebar — a new 'Research' item with a microscope icon now sits between System Health and Watchlist.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-10/step-01.png

### Step 02 — Open the new Research → Factor Lab  [NEW]

- **Narration:** One click on Research opens the new Factor Lab, which answers a sharp question: does a factor actually sort future returns? Every figure is read from forward-tested evidence the product already stored — nothing is recomputed or invented.
- **Action:** Click the "Research" link
- **Point out:** The 'Research — Factor Lab' heading, the D1–D10 decile table of mean forward return, the Rank-IC card, and the amber survivorship-bias honesty banner.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-10/step-02.png

### Step 03 — Switch the factor to ATR % (volatility)  [NEW]

- **Narration:** Pick a different factor — here, ATR % volatility — and the whole table and the headline correlation re-point to that factor's real forward returns. The choices in the dropdown come straight from the server's own catalog.
- **Action:** Type "ATR % (volatility level)" into "[data-testid="factor-select"]"
- **Point out:** The metadata line now reads 'volatility · lower better', and the decile returns and the Rank-IC value have changed from the Leadership view.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-10/step-03.png

### Step 04 — Re-point to the 60-day forward horizon  [NEW]

- **Narration:** Now switch the forward horizon to 60 days to see how the same factor's edge holds over a longer window. The evidence re-points again, all from stored observations.
- **Action:** Click the "60d" button
- **Point out:** 'Horizon: 60d' in the metadata, the 60d button highlighted, and the decile means shifting to their 60-day values.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-10/step-04.png

## Full tour (text only)

### Step 05 — The existing evidence page still works

- **Narration:** The new lab is modeled on Trendora's System Health page, the established home for forward-tested evidence — which keeps working exactly as before. The Research section adds depth without disturbing anything that was already there.
- **Action:** Click the "System Health" link
- **Point out:** System Health's existing by-bucket and control-group forward-test tables still render — no regression from adding Research.
