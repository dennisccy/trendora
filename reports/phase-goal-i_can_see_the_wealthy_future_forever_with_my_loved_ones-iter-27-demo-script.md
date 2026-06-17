# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27

**Mode:** record
**Date:** 2026-06-17
**Frontend URL:** http://localhost:3835

## Highlights

### Step 01 — Stocks leaderboard with Max Drawdown columns  [NEW]

- **Narration:** The stocks leaderboard now shows five Max Drawdown columns alongside the existing forward-return columns, one for each horizon from 1 day out to 60 days. Every cell shows a negative percentage — the true worst peak-to-trough drop during that window — or NA when the window has not yet closed.
- **Action:** Navigate to /stocks?asof=2025-12-16
- **Point out:** Five new column headers labelled '1d MDD', '5d MDD', '10d MDD', '20d MDD', '60d MDD' appear to the right of the return columns, with negative percentage values in each row.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-01.png

### Step 02 — MDD values are always negative  [NEW]

- **Narration:** Every Max Drawdown cell across the table is a negative percentage — none are zero or positive. This gives an honest picture of downside risk at each time horizon for every stock in the universe.
- **Action:** Navigate to /stocks?asof=2025-12-16
- **Point out:** Sample cells show values like -3.51%, -12.73%, -21.93% across different rows and horizons. No cell shows a positive number.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-02.png

### Step 03 — Stock detail — Max drawdown beneath each horizon card  [NEW]

- **Narration:** Opening any stock's detail page now shows a second line on each horizon card. Under the realized return sits a 'Max drawdown' figure — the worst intra-window drop — so you can immediately see how rough the ride was, not just the final number.
- **Action:** Navigate to /stocks/WDC?asof=2025-12-16
- **Point out:** Each of the five horizon cards (1d through 60d) shows two lines: the return on top and 'Max drawdown' below it with a negative value.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-03.png

### Step 04 — MDD columns persist when navigating to a different date  [NEW]

- **Narration:** Using the date navigation arrows to step to an earlier snapshot keeps all five Max Drawdown columns in place, fully populated with data for that historical date. The layout never breaks when you move through time.
- **Action:** Click the "Previous available date" button
- **Point out:** After clicking the back arrow the URL updates to a different date and all five MDD column headers remain, with fresh values like -8.60%, -14.94%, -17.70% for the new date.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-04.png

### Step 05 — Themes leaderboard with MDD columns and expandable members  [NEW]

- **Narration:** The themes leaderboard gained the same five Max Drawdown columns. Expanding any theme row to see its member stocks works correctly — the expanded section spans the full table width including the new MDD columns, so nothing is clipped.
- **Action:** Navigate to /themes?asof=2025-12-16
- **Point out:** Five MDD column headers appear on the themes table, and clicking the expand control on Semiconductors shows member stocks whose row covers the full table width.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-05.png

### Step 06 — Backtest — Mean MDD in evidence panels  [NEW]

- **Narration:** The Backtest evidence panels now include a 'Mean MDD' column alongside the mean return statistics in every breakdown table. The evidence summary header also shows a 'Mean max drawdown' figure, so the risk side of each setup is visible right next to its reward.
- **Action:** Navigate to /backtest?asof=2025-12-16
- **Point out:** A 'Mean MDD' column appears in the by-bucket breakdown table with negative values, and 'Mean max drawdown' is visible in the summary header at the top of the evidence panel.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-06.png

### Step 07 — Research — Mean MDD in event-study and RSP tables  [NEW]

- **Narration:** The Research page event-study table and the Regime x Setup x Pattern table both now carry a 'Mean MDD' column. Low-sample rows show NA — only setups with enough observations get a drawdown estimate.
- **Action:** Navigate to /research
- **Point out:** Both the per-horizon event-study table and the RSP table show a 'Mean MDD' column, with values like -13.11% for high-count rows and NA for sparse rows.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-07.png

### Step 08 — Data page — Rebuild panel with confirm-gated modal  [NEW]

- **Narration:** The Data page now shows a Rebuild panel telling you exactly how many universe members are covered by the current snapshot. When all members are present you see a calm confirmation note. Clicking 'Rebuild snapshots for current universe' opens a confirm dialog — no destructive job starts until you explicitly confirm.
- **Action:** Navigate to /data
- **Point out:** A 'Rebuild snapshots for current universe' button is visible alongside an 'all members present' note. Clicking the button brings up a modal with a visible Confirm and Cancel button — nothing runs until you confirm.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27/step-08.png
