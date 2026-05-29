# Demo Script — goal-i_can_see_the_wealthy_future-iter-3

**Mode:** record
**Date:** 2026-05-29
**Frontend URL:** http://localhost:3836
**Iteration:** 3

## Highlights

### Step 01 — Your daily market snapshot  [NEW]

- **Narration:** We start on the Dashboard, Trendora's at-a-glance view of the market today. It shows the overall market regime, how many stocks are worth acting on right now, and the strongest sectors and themes.
- **Action:** Navigate to /
- **Point out:** The Candidate Counts and Top Themes cards are now filled with real numbers — the old 'pending' placeholders are gone, so the daily snapshot is finally complete.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-3/step-01.png

### Step 02 — The Stock Leaderboard  [NEW]

- **Narration:** Next we open the Stock Leaderboard, where every stock is ranked by Leadership and carries three independent A-to-E scores: Leadership, Entry Quality, and Risk, alongside a setup status and a plain-language reason.
- **Action:** Navigate to /stocks
- **Point out:** The Sector and Setup dropdowns and the visible / total count at the top let you narrow the table down to a single sector or setup status.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-3/step-02.png

### Step 03 — Open NVDA's stock detail  [NEW]

- **Narration:** Clicking a ticker opens that stock's detail page. Here are NVDA's three scores shown as full cards, each with its raw value out of 100 and the named components behind it.
- **Action:** Click the "NVDA" link
- **Point out:** These three scores are identical to NVDA's row on the leaderboard — each score is computed once and read everywhere, so two pages can never disagree.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-3/step-03.png

### Step 04 — The Theme Leaderboard  [NEW]

- **Narration:** Now to the Theme Leaderboard, which ranks market themes by a price-confirmed Theme Score. Each row shows the one-month and three-month basket return, member breadth, and a trend label.
- **Action:** Navigate to /themes
- **Point out:** Themes are ranked purely on price action, not news, and the top row carries the highest Theme Score.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-3/step-04.png

### Step 05 — Expand a theme to see its members  [NEW]

- **Narration:** Clicking any theme row expands it to reveal the member tickers and the component breakdown behind its score.
- **Action:** Click "tbody tr"
- **Point out:** The member chips and the named-component breakdown appear right under the row — every score stays fully explainable.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-3/step-05.png

### Step 06 — Sectors still rank as before

- **Narration:** Finally we revisit the Sector Leaderboard from the earlier iteration to confirm it still works exactly as it did.
- **Action:** Navigate to /sectors
- **Point out:** Sectors are still ranked by Sector Score with the same buckets and labels — this iteration's behind-the-scenes refactor changed nothing a user sees here.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-3/step-06.png
