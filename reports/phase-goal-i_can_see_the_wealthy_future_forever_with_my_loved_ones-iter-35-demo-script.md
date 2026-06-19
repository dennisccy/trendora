# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35

**Mode:** record
**Date:** 2026-06-19
**Frontend URL:** http://localhost:3835
**Iteration:** 35

## Highlights

### Step 01 — Stock leaderboard — full universe at latest date  [NEW]

- **Narration:** The stock leaderboard now shows the complete, correctly-sized universe at today's date. After a full snapshot rebuild, 544 stocks appear instead of the stale 122-member flat list that had been served at every date.
- **Action:** Navigate to /stocks
- **Point out:** Row count near top of table reads 544/544 — all filters set to 'All'. Each row shows leadership, entry, and risk scores alongside sector and setup labels.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-01.png

### Step 02 — Honest empty universe at a pre-warm-up date  [NEW]

- **Narration:** Step the date back to January 2021 and the leaderboard honestly shows zero stocks. No data is fabricated — the system admits names only once they have the required price history, so the early universe is genuinely empty.
- **Action:** Navigate to /stocks?asof=2021-01-04
- **Point out:** The table is completely empty with a message confirming no stocks qualified on that date. The row counter reads 0, not 122.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-02.png

### Step 03 — Dynamic universe at a full-history date  [NEW]

- **Narration:** Jump to February 2022 and the same leaderboard fills with 504 stocks — the genuine point-in-time universe for that date. The count slides with the date rather than staying fixed at an arbitrary number.
- **Action:** Navigate to /stocks?asof=2022-02-01
- **Point out:** Table shows approximately 504 rows. The very first row displays a leadership score and ticker — confirming real data, not a placeholder.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-03.png

### Step 04 — NVDA leaderboard row — score snapshot

- **Narration:** Back at the latest date, NVDA appears on the leaderboard with three canonical scores. These values come from the single rebuilt snapshot — the same store that powers both the list and the detail page.
- **Action:** Navigate to /stocks?asof=2026-06-16
- **Point out:** NVDA row is visible with Leadership, Entry, and Risk score columns populated. Note the exact score values — we will confirm they match the detail page next.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-04.png

### Step 05 — NVDA detail page — scores match the leaderboard

- **Narration:** Opening the NVDA detail page shows the identical leadership, entry, and risk scores seen on the leaderboard. Both views read from the same rebuilt snapshot, confirming a single source of truth.
- **Action:** Navigate to /stocks/NVDA?asof=2026-06-16
- **Point out:** The scores shown under 'Leadership', 'Entry', and 'Risk' headings are numerically identical to the NVDA row on the list. The 'as of 2026-06-16' badge is visible alongside the setup status.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-05.png

### Step 06 — Risk-Off date — zero Actionable stocks

- **Narration:** On a bear-market date in June 2022 the regime reads Risk-Off and the leaderboard returns no Actionable stocks. The risk gate is working as intended — market conditions suppress all buy signals automatically.
- **Action:** Navigate to /stocks?asof=2022-06-13
- **Point out:** Market Regime badge shows 'Risk-off' with a low score. No rows carry an Actionable status — only watchlist-level entries remain.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-06.png

### Step 07 — Dashboard — market regime breakdown

- **Narration:** The dashboard at a Defensive-regime date shows the full market-phase panel with a score, regime label, and a component table. Breadth figures are labelled universe-relative, keeping the analysis honest about the dynamic universe size.
- **Action:** Navigate to /?asof=2022-02-01
- **Point out:** The 'Market Regime' panel displays a numeric score, a regime label such as 'Defensive', and a row-by-row component breakdown. Breadth metrics carry the 'universe-relative' label.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-07.png

### Step 08 — Backtest — no secondary date picker

- **Narration:** The Backtest page uses the single global as-of switcher as its only date control. No page-local date input exists anywhere, so there is no way to accidentally introduce a second, conflicting date state.
- **Action:** Navigate to /backtest
- **Point out:** The Backtest page is fully rendered. Scanning the entire page surface reveals no date input fields beyond the global switcher — just the survivorship-bias label and the scan-date cards loaded from the snapshot store.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35/step-08.png
