# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running at `http://localhost:8835` (verify with `curl http://localhost:8835/health` — expect HTTP 200)
- Frontend running at `http://localhost:3835`
- No login required — the Dashboard is publicly accessible

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser and wait up to 10 seconds for it to load
   - **Expect:** The Dashboard renders — you see a page with market data figures near the top, not a blank white screen or a "Checking backend..." spinner that never clears

2. Without scrolling yet, look near the top of the Dashboard for the compact at-a-glance "Market Phase & Severity" figure
   - **Expect:** A phase label (e.g., "Recovery", "Distribution", "Accumulation") and a number between 0 and 100 are displayed side by side — not a blank area or "undefined"
   - **If broken:** The compact figure is empty or shows "—" instead of a label and number. This means the cache fix did not take effect for the current as-of date.

3. Scroll down the Dashboard page until a two-pane stacked chart comes into view (labeled "Cross-View" or similar) — the top pane shows index lines, and the bottom pane is below it
   - **Expect:** The bottom pane is NOT a blank white rectangle. It shows colored background bands (one color per market phase period) with a line drawn over them. A numeric scale (0–100) appears on the vertical axis of the bottom pane.
   - **If broken:** The bottom pane is completely empty (white canvas with no bands and no lines). This is the specific defect this iteration fixed — if you see this, the backend cache key fix is not deployed.

4. Still on the cross-view chart, click and drag across a portion of the top pane's chart area (left to right, covering roughly one third of the chart width) to zoom into that time range
   - **Expect:** Both the top pane and the bottom pane immediately narrow their x-axis to show the time range you selected. The bottom pane still shows colored bands and a line (not empty) after the zoom. The date labels on both panes show the same narrower range.
   - **If broken:** Only the top pane zooms and the bottom pane stays blank (or only the bottom pane zooms). This means the pane sync is not working.

5. Scroll back up to the as-of date selector near the top of the Dashboard. Click it and pick `2026-06-10` (approximately one week earlier)
   - **Expect:** The date picker updates to show `2026-06-10`. The at-a-glance figures re-render with data for that date. After scrolling back down, the cross-view chart bottom pane still shows phase bands (not empty) and the vertical as-of marker line moves to `2026-06-10`.

6. Click the as-of date selector again and pick a very early date — type or select `2010-01-15`
   - **Expect:** The cross-view chart bottom pane is visually empty (no colored bands, no lines) for this early date. This is correct behavior — market-phase history does not exist this far back. The pane should show an empty canvas, not an error message.

7. Click the as-of date selector one more time and return to today's date (or the most recent date available in the picker)
   - **Expect:** The bottom pane repopulates with colored phase bands and the P(bear) line. The at-a-glance Market Phase & Severity figure shows a phase label and severity score again.

---

## What "Working Correctly" Looks Like

- The cross-view chart bottom pane shows colored bands (distinct background colors across time) and at least one overlaid line when viewing any recent date with market-phase data
- The compact at-a-glance Market Phase & Severity figure always shows a non-blank phase label and a 0–100 severity number at the current date
- Zooming on either pane moves both panes to the same time window simultaneously

## Common Issues

- **Bottom pane blank at the current date:** The backend cache from before this fix was served with the old key. After deploying this iteration's fix, the backend should recompute once on the first request and re-cache. If the pane is still blank after a hard refresh (Ctrl+Shift+R), check that the backend was restarted with the new code (`curl -s 'http://localhost:8835/api/market-phase?asof=2026-06-16&full=true' | python3 -m json.tool | grep timeline_full` should return a non-empty array).
- **Dashboard shows "Checking backend..." indefinitely:** The backend is not running. Start it before testing.
- **At-a-glance figure shows blank or "undefined":** This draws from the same endpoint as the cross-view chart. If the bottom pane has data but the at-a-glance figure is blank, clear the browser cache (Ctrl+Shift+Delete) and reload.
