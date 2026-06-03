# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-15

**Mode:** record
**Date:** 2026-06-03
**Frontend URL:** http://localhost:3835
**Iteration:** 15

## Highlights

### Step 01 — Start with the evidence in the Research labs

- **Narration:** We open the Research labs, where Trendora shows which signals actually sorted future returns — decile by decile, with a downside risk-adjusted column and a rank correlation, all read from stored history.
- **Action:** Navigate to /research
- **Point out:** The decile sort table and the rank-IC card: honest, descriptive evidence to start from, never a prediction.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-01.png

### Step 02 — A new one-click bridge from a pattern's study to the names  [NEW]

- **Narration:** Further down the same page, the Setup & Pattern Lab studies one setup or pattern. New this time: a link that jumps straight from that evidence to the live names expressing it.
- **Action:** Click "subject-select"
- **Point out:** The new accent link "View the names expressing this on the leaderboard →" with its plain-language caption right under the subject picker.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-02.png

### Step 03 — Land on the leaderboard already filtered  [NEW]

- **Narration:** Following that link opens the Stock Leaderboard pre-filtered to the matching names — here, the stocks showing a pullback to a rising moving average. No re-picking the filter by hand, and the whole view is shareable as a link.
- **Action:** Navigate to /stocks?pattern=pullback_to_rising_dma__only
- **Point out:** The Pattern filter is already applied, every row carries a "Pullback" badge, and the count is narrowed to just those names.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-03.png

### Step 04 — Open one name for the full detail

- **Narration:** Click any ticker to open its detail page — the very same scores from the leaderboard, computed once and read everywhere, alongside the pattern's pivot and invalidation level.
- **Action:** Click "table tbody tr:first-child a"
- **Point out:** Leadership, Entry Quality and Risk scores with their A–E grades, the pattern badge and the invalidation note — identical to the row you came from.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-04.png

### Step 05 — Share any filtered view as a link  [NEW]

- **Narration:** Because the filters now live in the web address, you can open a ready-made view directly — for example every name in one sector. The date never rides along; it stays in the single top-bar as-of switcher.
- **Action:** Navigate to /stocks?sector=Energy
- **Point out:** Opening the address with a sector pre-selects it: the Sector filter reads "Energy" and every visible row is an Energy name.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-05.png

### Step 06 — Honest when nothing matches

- **Narration:** Ask for a combination no stock satisfies today and Trendora says so plainly — it never invents a row to fill the screen.
- **Action:** Navigate to /stocks?pattern=vcp__only&sector=Energy
- **Point out:** The "No stocks match these filters" message instead of fabricated results; clearing a filter brings names back.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-06.png

### Step 07 — Robust to a broken link  [NEW]

- **Narration:** Even an unknown or broken filter in the address is handled gracefully — Trendora ignores it, falls back to showing everything, and never errors out.
- **Action:** Navigate to /stocks?pattern=garbage_value
- **Point out:** The unrecognized value is dropped: the Pattern filter returns to "All patterns" and the full ranked list is shown.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-15/step-07.png
