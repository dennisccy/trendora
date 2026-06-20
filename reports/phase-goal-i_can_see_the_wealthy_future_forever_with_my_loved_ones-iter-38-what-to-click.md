# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` (confirm with `curl http://localhost:8835/health` — expect a 200 response)
- Database seeded with at least one year of daily snapshots

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser in a fresh incognito window
   - **Expect:** The page loads and you can see two compact figures near the very top — one labelled "Market Regime" (showing a text label such as "Risk-On" and a number between 0 and 100) and one labelled "Market Phase & Severity" (showing a phase badge such as "Expansion" and a numeric severity). You should NOT see "Top Sectors", "Candidate Counts", or any breadth-metrics content without scrolling.

2. Click the "Why this regime — component breakdown" disclosure link directly below the "Market Regime" figure
   - **Expect:** A list of named driver rows expands inline below the figure on the same page. No new page opens. Click the disclosure again to collapse it.

3. Click the "Why this phase — component breakdown" disclosure link directly below the "Market Phase & Severity" figure
   - **Expect:** A list of named severity-component rows expands inline. Click again to collapse.

4. Scroll down past the Major-indexes chart and look for a card labelled "Regime x phase cross-view" or "Regime × phase cross-view"
   - **Expect:** The card is present and contains two stacked chart panes — the top pane shows coloured regime bands behind index lines; the bottom pane shows differently-coloured phase bands behind index lines, plus two additional lines (severity and P(bear)).

5. Place your mouse cursor over the bottom pane of the cross-view chart and hold it over any data point
   - **Expect:** A tooltip appears showing the hovered date, at least one index percentage value, a phase label (e.g., "Contraction"), a numeric severity value, and a P(bear) value. If no tooltip appears, move the cursor slowly across the pane.

6. Scroll the mouse wheel inward (zoom in) while hovering over the top pane of the cross-view chart
   - **Expect:** Both panes zoom together — the date range displayed on the bottom pane narrows to match the top pane. The x-axis date labels on both panes show the same window after zoom.

7. Scroll down to the "More detail" section header below the cross-view chart and click it
   - **Expect:** The section expands and you can now see at least four cards: a breadth metrics card, a "Candidate Counts" card, a "Top Sectors" card, and a "Top Themes" card. Each card shows data, not blank content.

8. Reload the page (press F5 or Cmd+R) while "More detail" is still expanded
   - **Expect:** After the reload, the "More detail" section remains expanded and the four supporting cards are still visible without clicking again — confirming the expand state was saved.

9. Scroll back to the top of the page and confirm the "Market Regime" and "Market Phase & Severity" figures are still the first visible elements (before any chart)
   - **Expect:** The two compact figures appear at the very top of the page content, before the Major-indexes chart and before the cross-view chart — confirming the Dashboard layout restructure is in place.

10. Locate the hide toggle on the "Regime × phase cross-view" card (typically an "X" or eye icon in the card header) and click it
    - **Expect:** The cross-view chart disappears. Reload the page (F5). The chart remains hidden after the reload — confirming the hide preference was persisted. If you need to restore the chart, clear your browser's local storage for this site (`localStorage.clear()` in the browser console) and reload.

---

## What "Working Correctly" Looks Like

- At first paint (no scrolling), you see exactly two compact summary figures at the top, then the Major-indexes chart, then the cross-view chart — nothing else
- Both panes of the cross-view chart are populated with coloured bands and lines (not blank, not skeleton)
- Scrolling either pane of the cross-view chart moves the date window on both panes simultaneously
- "More detail" starts collapsed and its expand/collapse state survives a page reload
- Phase band colours in the cross-view bottom pane and in the Market Phase detail card (inside "More detail") use matching colour tones for the same phase labels

## Common Issues

- **Blank page or "Checking backend..." stuck screen**: The backend may not be running or is still warming up. Run `curl http://localhost:8835/health` — if it fails, wait 60 seconds and try again. If the backend is fresh, it may take up to 2 minutes for the walk-forward backfill to complete.
- **Cross-view chart shows a skeleton that never resolves**: The `GET /api/market-phase?full=true` call may have timed out. Open browser DevTools (F12) > Network tab, reload the page, and look for the `market-phase` request. If it shows a 500 or hangs, check the backend logs.
- **Bottom pane of cross-view chart is empty (no bands or lines)**: This may be correct if the current as-of date is before the database has causal phase history. Try setting the as-of date to a more recent date (e.g., 2024-06-30) using the date selector.
- **"More detail" expand state not persisting**: This feature relies on browser local storage. Verify local storage is not blocked (Private/Incognito mode in some browsers may not persist local storage across tabs — use a regular window for the persistence check).
