# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-2

**Mode:** record
**Date:** 2026-06-01
**Frontend URL:** http://localhost:3835
**Iteration:** 2

## Highlights

### Step 01 — Open System Health

- **Narration:** We start on the System Health page, which gathers the forward-tested evidence behind Trendora's rankings.
- **Action:** Navigate to /system-health
- **Point out:** The page already shows how each ranked cohort actually performed; the brand-new Return attribution section further down will explain why.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-2/step-01.png

### Step 02 — Which tickers drove the return  [NEW]

- **Narration:** Scrolling down reveals the new Return attribution section. Its first panel names the individual stocks that most drove — or dragged — the cohort's forward return.
- **Action:** Click the "Top contributors & detractors" heading
- **Point out:** Each named ticker shows its sector, its realized mean return (green for gains, red for losses) and its sample size; the panel beside it opens up the full distribution — mean, median, hit rate and dispersion.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-2/step-02.png

### Step 03 — By sector and by rank band  [NEW]

- **Narration:** The other two panels break the very same return down by sector and by rank band.
- **Action:** Click the "Forward return by rank band" heading
- **Point out:** Every configured rank band (1-10, 11-50, 51+) is listed with its own sample size, and higher-ranked bands tend to show stronger returns — you can watch the ranking earn its keep.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-2/step-03.png

### Step 05 — Attribution follows the horizon  [NEW]

- **Narration:** The whole section instantly re-reads itself for the 5-day window — the same stored evidence, a different holding period.
- **Action:** Click the "Top contributors & detractors" heading
- **Point out:** The intro now reads 'Open the 5-day forward return', and the contributors and detractors are re-ranked for that shorter window.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-2/step-05.png

### Step 06 — Open the Backtest page

- **Narration:** The same attribution also lives on the Backtest page, which focuses on a single chosen date.
- **Action:** Navigate to /backtest
- **Point out:** One global as-of date governs the page — here it is showing the latest scan and its forward-test scorecard.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-2/step-06.png

### Step 07 — Honest gaps, never faked  [NEW]

- **Narration:** Backtest carries the same four panels, plus its own horizon view selector. At the latest date the forward windows have not elapsed yet.
- **Action:** Click the "5d" button
- **Point out:** Switching horizons here is instant — no reload and the date never changes — and rather than invent a figure, every panel honestly shows a dash with its sample size when no measurable return exists yet.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-2/step-07.png

## Full tour (text only)

### Step 04 — Switch the holding period  [NEW]

- **Narration:** A single horizon selector at the top of the page drives everything at once. We switch it to five trading days.
- **Action:** Click the "5d" button
- **Point out:** There is just one horizon control here — the attribution section rides it rather than introducing a second control.
