# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` (verify: open `http://localhost:8835/health` — you should see a JSON response, not an error)
- Database seeded with 2021-2026 market history (the standard seed; no special setup required)

---

## Verification Steps

1. Open `http://localhost:3835` in your browser
   - **Expect:** The Dashboard loads with multiple cards. Only one market chart is visible — the two-pane "Regime x phase cross-view" card. If you see a separate card titled "Major indexes & regime" below or alongside the cross-view card, that is a regression.

2. Look at the chart legend below or above the cross-view chart panes
   - **Expect:** One of the legend swatches is labeled "Severity velocity (0-centered; + = worsening)". No swatch labeled "Filtered P(bear)" exists in the legend. If you see "Filtered P(bear)" as a legend label, the P(bear) line was not replaced correctly.

3. Look at the bottom pane of the cross-view chart (the phase pane)
   - **Expect:** A line in the bottom pane visibly crosses the dashed horizontal zero reference line — it goes both above and below the dashed midpoint. This is the severity-velocity line. If the line only runs from 0 to 1 without crossing zero, the wrong line (P(bear)) is still being drawn.

4. Hover your mouse over a point in the middle of the cross-view chart (aim for approximately the 2023–2024 area of the timeline)
   - **Expect:** A tooltip appears showing at least these rows: a date, an index percent value, a phase label, a severity value, a P(bear) value, a market-regime label with a 0–100 score (e.g., "Bull / 72"), and a severity-velocity value formatted with a sign prefix (e.g., "+0.44" or "-1.20"). If the tooltip is missing the regime label row or the severity-velocity row, the tooltip was not enriched. If the P(bear) row is gone, that is a separate regression.

5. Hover your mouse over the leftmost 4–5 data points on the cross-view chart (the earliest dates in the timeline, near the left edge)
   - **Expect:** The severity-velocity row in the tooltip shows "NA" rather than a numeric value. If it shows a number like "+0.00" at these earliest dates, a fabricated slope is being shown — that is a regression.

6. Locate the as-of date selector on the Dashboard (it is a custom control — not a browser native date picker — typically showing left/right navigation arrows or a dropdown)
   - Select a historical date in 2022 (e.g., navigate backwards until the as-of shows 2022-10-07 or any 2022 date)
   - **Expect:** The cross-view bottom pane's colored phase bands continue past the vertical as-of marker line to the right edge of the chart. The bands do NOT stop at the marker. If the bands end exactly at the marker, the full-history display fix was not applied.

7. Find the "Market Phase" compact card on the Dashboard (it is separate from the large cross-view chart)
   - **Expect:** The card still shows a P(bear) value. No severity-velocity line has been added to this card. The card looks unchanged from before this iteration.

---

## What "Working Correctly" Looks Like

- The Dashboard shows exactly one market chart (the two-pane cross-view card) — no duplicate "Major indexes & regime" card alongside it
- The cross-view bottom pane has a line that oscillates above and below a dashed zero reference line (not a probability curve constrained to 0–1)
- The cross-view legend reads "Severity velocity (0-centered; + = worsening)" — not "Filtered P(bear)"
- Hovering over a mid-history date shows a tooltip with both a regime label + score row AND a severity-velocity row, while also retaining P(bear) and all other prior rows
- Hovering over the earliest 4–5 dates shows "NA" in the severity-velocity tooltip row
- Selecting a historical as-of date shows phase bands spanning the full chart width with the as-of marker visible inside the bands, not truncating them

## Common Issues

- **Dashboard shows a loading spinner that never resolves:** Check that the backend is running — open `http://localhost:8835/health` in a new tab. If it returns an error, the backend is down.
- **Tooltip does not appear on hover:** Move the mouse slowly across the chart until it snaps to a data point. The tooltip appears when the cursor is near a plotted point, not in empty chart space.
- **Phase bands in the bottom pane look truncated at the as-of marker:** This means the full-history band clamp fix was not applied. Verify the frontend was built and the dev server was restarted after the code changes.
- **Legend still shows "Filtered P(bear)":** The frontend component changes did not deploy. Confirm the Next.js dev server compiled the latest version of `phase-cross-view-chart.tsx` without errors.
