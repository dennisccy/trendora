# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-13

**Mode:** record
**Date:** 2026-06-02
**Frontend URL:** http://localhost:3835
**Iteration:** 13

## Highlights

### Step 01 — Open the Factor Lab  [NEW]

- **Narration:** We begin in the Research Factor Lab, which asks an honest question of any signal — did it actually sort future returns? This iteration makes volatility a first-class family: the Factor menu (top right) now groups four volatility measures together — ATR%, Historical volatility, a VCP-style contraction measure, and downside (semi) volatility.
- **Action:** Navigate to /research
- **Point out:** The 'Factor' menu is now organized into families with a four-strong Volatility group, and whatever you pick fills the decile table and rank-correlation card shown here — under an amber banner that flags this as descriptive evidence, not a prediction.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-13/step-01.png

### Step 02 — Forward-tested at any horizon

- **Narration:** The evidence isn't tied to one timeframe. Pick a forward horizon and every decile's mean return is recomputed from the stored forward-tested returns at that horizon — here we switch to 60 days.
- **Action:** Click the "60d" button
- **Point out:** The horizon control moves to 60d and the 'Mean fwd return' column updates to the 60-day figures — the same forward-test engine each volatility measure now feeds into.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-13/step-02.png

### Step 03 — Explainable scores, one source of truth

- **Narration:** That same forward-tested discipline runs through the whole product. Open any stock — here NVDA — for three explainable scores (Leadership, Entry Quality, and Risk), each read straight from the immutable daily snapshot.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** Leadership 47.48 (E), Entry Quality 66.24 (D), and Risk 33.79 (E) are byte-identical to the leaderboard — one source of truth — and the new volatility values are deliberately kept off this page, so no score moved.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-13/step-03.png

### Step 04 — The ranked leaderboard

- **Narration:** Finally, the Stock Leaderboard — the daily at-a-glance view that ranks the whole universe by Leadership, alongside independent Entry Quality and Risk scores, a setup status, and a plain-language reason for each name.
- **Action:** Navigate to /stocks
- **Point out:** Every number here matches the detail page exactly — leaderboard, stock detail, and the research lab all read the same canonical scores.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-13/step-04.png
