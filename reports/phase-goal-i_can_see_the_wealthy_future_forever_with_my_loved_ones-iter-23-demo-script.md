# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23

**Mode:** record
**Date:** 2026-06-16
**Frontend URL:** http://localhost:3835

## Highlights

### Step 01 — Themes leaderboard — five forward-return columns  [NEW]

- **Narration:** The Themes leaderboard now shows how each theme's stocks actually performed over the next 1, 5, 10, 20, and 60 trading days. Every column is colour-graded — green for gains, red for losses — and cells read 'NA' (never '0%') when the future data doesn't exist yet.
- **Action:** Navigate to /themes?asof=2025-01-15
- **Point out:** Five new column headers — 1D, 5D, 10D, 20D, 60D — appear in the header row, each showing a coloured percentage for every theme.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-01.png

### Step 02 — Sort themes by 5-day forward return  [NEW]

- **Narration:** Clicking any forward-return column header instantly reorders the table — no page reload. 'NA' rows always sink to the bottom so real numbers stay on top.
- **Action:** Click the "Sort by 5d" button
- **Point out:** After clicking '5D', the row order changes immediately and any NA rows appear at the very bottom.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-02.png

### Step 03 — Sectors leaderboard — same five forward-return columns  [NEW]

- **Narration:** The Sectors leaderboard carries the same five realised-return columns for each sector and industry ETF. ETFs without stored price bars show 'NA' in muted text rather than a misleading zero.
- **Action:** Navigate to /sectors?asof=2025-01-15
- **Point out:** Sector ETFs like XLF and XLE show coloured percentages across all five horizons; industry ETFs without bars show muted 'NA'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-03.png

### Step 04 — Sort sectors by 20-day forward return — NA stays at the bottom  [NEW]

- **Narration:** Sorting the sectors table by the 20-day column pushes all 'NA' rows below every numeric row, in both ascending and descending directions.
- **Action:** Click the "Sort by 20d" button
- **Point out:** After sorting, numeric rows appear first and all NA-bearing rows are grouped at the very bottom of the table.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-04.png

### Step 05 — Research — RSP opens in Pooled view by default  [NEW]

- **Narration:** The Regime × Setup × Pattern table on the Research page now opens in Pooled mode on every fresh load, giving you the aggregated statistics right away. Other sections on the same page still default to Episodes — nothing else changed.
- **Action:** Navigate to /research
- **Point out:** The 'Pooled' toggle button appears highlighted in the RSP section controls row without any click needed.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-05.png

### Step 06 — RSP filter — narrow by regime  [NEW]

- **Narration:** Three new filter dropdowns — Regime, Setup, and Pattern — sit in the same controls row as the Pooled toggle. Selecting a regime instantly hides every non-matching row without reloading the page.
- **Action:** Navigate to /research
- **Point out:** After selecting a regime from the dropdown, the RSP table shrinks to show only rows for that regime, while the other two dropdowns still read 'All'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-06.png

### Step 07 — RSP empty-state message when filters produce no rows  [NEW]

- **Narration:** When a Regime and Pattern combination yields no stored data, the table area shows a clear explanatory message rather than a blank or broken layout. The dropdowns stay active so you can easily widen the filter.
- **Action:** Navigate to /research
- **Point out:** The RSP table disappears and a message like 'No combinations match these filters' appears in its place, with the dropdowns still visible above.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-07.png

### Step 08 — RSP samples drill-down — N= chip opens observation list  [NEW]

- **Narration:** Every N= chip in the RSP table — including rows where no chart pattern was detected — opens the exact underlying observation list in a new tab. The count on the samples page always matches the chip you clicked.
- **Action:** Navigate to /research/samples?kind=regime-setup-pattern&horizon=20&regime=Narrow+leadership&setup=Extended&pattern=flat_base_breakout&view=pooled
- **Point out:** Clicking an N= chip opens /research/samples in a new tab with the correct number of rows and no error message.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23/step-08.png
