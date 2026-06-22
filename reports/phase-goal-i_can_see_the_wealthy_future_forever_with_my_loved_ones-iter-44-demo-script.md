# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44

**Mode:** record
**Date:** 2026-06-22
**Frontend URL:** http://localhost:3835
**Iteration:** 44

## Highlights

### Step 01 — Dashboard loads — single market chart  [NEW]

- **Narration:** The Dashboard now shows exactly one market chart. The separate 'Major indexes & regime' card has been removed — its index lines and regime bands were already inside the two-pane cross-view chart above it, so nothing was lost, just the clutter.
- **Action:** Navigate to /
- **Point out:** Only the two-pane 'Regime x phase cross-view' card is visible. No second chart card appears below it.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44/step-01.png

### Step 02 — Cross-view chart renders both stacked panes

- **Narration:** The cross-view card stacks two panes that share a single time axis. The top pane carries the index percent lines and colored regime bands; the bottom pane shows market-phase coloring and the new severity-velocity line.
- **Action:** Navigate to /
- **Point out:** Two distinct chart panes are visible, one above the other, with neither showing a spinner or 'No data' message.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44/step-02.png

### Step 03 — Legend shows 'Severity velocity' — no 'Filtered P(bear)'  [NEW]

- **Narration:** The chart legend now labels the bottom-pane line 'Severity velocity (0-centered; + = worsening)'. The old 'Filtered P(bear)' swatch is gone. A positive reading means market stress is building; a negative reading means it is easing.
- **Action:** Navigate to /
- **Point out:** Look for the legend entry 'Severity velocity (0-centered; + = worsening)' — it should be there without any 'Filtered P(bear)' swatch alongside it.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44/step-03.png

### Step 04 — Tooltip shows regime label, score, and severity velocity  [NEW]

- **Narration:** Hovering over the cross-view chart now reveals two new rows in the tooltip: the stored market-regime label with its 0–100 score, and the severity-velocity value with an explicit sign prefix. All the existing rows — date, index percent, phase, severity, and P(bear) — are still present.
- **Action:** Navigate to /
- **Point out:** The tooltip should show a line like 'Narrow leadership · 59/100' for the regime and a line like 'Severity velocity +1.25' alongside the existing P(bear) row.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44/step-04.png

### Step 06 — Phase bands span full history at a historical as-of  [NEW]

- **Narration:** Selecting a historical date now moves only the vertical marker — the phase color bands in the bottom pane continue all the way to today's date as display-only context. You can see both where the market was then and everything that followed.
- **Action:** Navigate to /?asof=2022-10-07
- **Point out:** After setting the as-of to 2022-10-07, the bottom pane should show phase coloring extending well past the vertical marker all the way to the right edge of the chart.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44/step-06.png

### Step 08 — Market Phase card still shows P(bear) unchanged

- **Narration:** The compact Market Phase card on the Dashboard is untouched. It still displays the P(bear) value exactly as before — only the plotted line in the chart was replaced, not the card.
- **Action:** Navigate to /
- **Point out:** The Market Phase card should show 'P(bear)' with a numeric value, looking exactly as it did before this update.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44/step-08.png

## Full tour (text only)

### Step 05 — Severity velocity shows 'NA' at the earliest warm-up dates  [NEW]

- **Narration:** For the first few dates in stored history — before five prior snapshots exist to measure a slope — the tooltip honestly reports 'NA' instead of a fabricated number. No synthetic velocity is ever shown.
- **Action:** Navigate to /
- **Point out:** Hovering near the very left edge of the chart should show 'Severity velocity NA' in the tooltip, not a numeric value.

### Step 07 — Honest empty pane at a pre-history as-of  [NEW]

- **Narration:** When the selected date predates all stored history, the bottom pane renders cleanly empty — no fabricated phase coloring. The Market Phase card tells you plainly that there is not enough history to report a phase for that date.
- **Action:** Navigate to /?asof=2021-01-04
- **Point out:** At the 2021-01-04 as-of, the Market Phase card should read 'Not enough history to derive a market phase for this date — reported NA, never fabricated.' and the bottom pane should appear empty.
