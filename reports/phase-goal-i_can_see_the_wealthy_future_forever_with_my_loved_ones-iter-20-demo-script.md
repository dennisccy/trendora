# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20

**Mode:** record
**Date:** 2026-06-15
**Frontend URL:** http://localhost:3835
**Iteration:** 20

## Highlights

### Step 01 — Stocks leaderboard with forward-return columns  [NEW]

- **Narration:** At any historical date, the leaderboard now shows five realized forward-return columns — 1d, 5d, 10d, 20d, and 60d. Cells are colour-graded green for positive returns and red for negative; where no post-date data exists the cell shows 'NA' in muted grey.
- **Action:** Navigate to /stocks?asof=2021-01-04
- **Point out:** Five new column headers ('1d', '5d', '10d', '20d', '60d') to the right of the existing score columns, with green and red values filled in for 2021-01-04.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-01.png

### Step 02 — Sort leaderboard by 5-day forward return  [NEW]

- **Narration:** Clicking a forward-return column header instantly re-orders the leaderboard client-side — no page reload. Rows with no return data always sink to the bottom, so you never have to hunt past NA cells to find the real performers.
- **Action:** Click the "5d" columnheader
- **Point out:** The table re-orders with the highest 5d return at the top; any 'NA' rows are pushed to the bottom of the list.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-02.png

### Step 03 — Stock Detail — Realized forward returns panel  [NEW]

- **Narration:** Every stock detail page now opens with a 'Realized forward returns' card above the price chart. It shows five tiles — one per horizon — colour-coded by sign, and the values match exactly what the leaderboard showed for the same date.
- **Action:** Navigate to /stocks/AAPL?asof=2021-01-04
- **Point out:** The 'Realized forward returns' panel with five horizon tiles (1d, 5d, 10d, 20d, 60d) appears above the price chart, values colour-graded green or red.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-03.png

### Step 04 — Forward returns show 'NA' honestly at the latest date  [NEW]

- **Narration:** At the latest scan date there are no future bars yet, so all five tiles honestly say 'NA'. The panel never fabricates a number — if the data is not there, it says so clearly.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** All five horizon tiles in the 'Realized forward returns' panel display 'NA' in muted grey text — no made-up values.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-04.png

### Step 05 — Research page — new Regime x Setup x Pattern study  [NEW]

- **Narration:** Scrolling down the Research page reveals a brand-new study table: which combinations of market regime, setup status, and detected chart pattern historically produced the strongest risk-adjusted forward returns. Each row shows the group's count, mean, median, hit-rate, and expectancy.
- **Action:** Navigate to /research
- **Point out:** A new sortable table labelled 'Regime x Setup x Pattern' (or similar) appears below the existing Event Study section, with rows showing Regime, Setup, Pattern, N, Mean, Median, Hit-rate, Expectancy columns and a survivorship-bias caveat banner.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-05.png

### Step 06 — Regime x Setup x Pattern — Episodes vs Pooled toggle  [NEW]

- **Narration:** The new study has its own independent Episodes / Pooled toggle. Switching to Pooled updates only this table — the Event Study and Combination Lab sections stay exactly as they are, with no flash or reload.
- **Action:** Click the "Pooled" button
- **Point out:** The N counts in the Regime x Setup x Pattern table change after switching to 'Pooled'; the Event Study and Combination Lab sections do not move or reload.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-06.png

### Step 07 — Research sections load independently  [NEW]

- **Narration:** Each section of the Research page now has its own loading skeleton and fetches data on its own schedule. A slow event-study computation no longer blocks the Combination Lab or the new Regime x Setup x Pattern table — each section becomes interactive as soon as its own data is ready.
- **Action:** Navigate to /research
- **Point out:** Individual loading skeletons per section; the Combination Lab and Regime x Setup x Pattern sections become interactive before the event study finishes, with no full-page spinner blocking the page.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-07.png

### Step 08 — Drill into a combination's samples  [NEW]

- **Narration:** Clicking the N= chip on any Regime x Setup x Pattern row opens a drill-down in a new tab. The samples page heading names the exact combination — regime, setup, and pattern — and the row count matches the N published in the table.
- **Action:** Navigate to /research/samples?kind=regime-setup-pattern&regime=Defensive&setup=Avoid&pattern=none&horizon=5&view=episodes
- **Point out:** The samples page heading names the specific combination (e.g., 'Defensive / Avoid / none — Episodes') and the table's total row count equals the N shown in the chip.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20/step-08.png
