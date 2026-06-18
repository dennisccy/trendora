# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (check: `curl http://localhost:8000/health`)
- Dataset contains at least one recovery-turn signal date and the 2022 bear episode

---

## Verification Steps

1. Navigate to `http://localhost:3835` and scroll down to the Market-Phase panel (approximately 1060 px below the top of the page)
   - **Expect:** A colored SVG chart appears showing a phase-colored step-function band (green/amber/red regions) behind a bear-probability polyline, plus a dashed vertical marker at today's date. A swatch legend with phase color names is visible. If you see only a loading skeleton, wait up to 60 s for the first cold computation to finish.
   - **Broken looks like:** The panel area is blank or shows a JavaScript error message.

2. In the Market-Phase panel, read the recovery-turn signal line (a labeled badge or callout just below the chart)
   - **Expect:** You see either a muted shield icon reading "No recovery turn at this date" (correct for current Expansion phase) or a green up-arrow "Recovery / turn signalled". Either way, a plain-language reason is printed directly beneath the icon — it is NOT a bare icon with no text.
   - **Broken looks like:** The signal area is absent, or the reason text is missing.

3. In the Market-Phase panel, read the downtrend-episode list beneath the timeline chart
   - **Expect:** At least one episode row is visible, showing a first-trigger date in early 2022, a numeric severity-at-trigger, a peak-P(bear) value, and a "closed" status badge. The 2022 bear appears as exactly one row, not multiple.
   - **Broken looks like:** The list is completely empty, or the same 2022 episode appears as multiple duplicate rows.

4. In the Market-Phase panel, click the "Show" button on the "Retrospective (full-sample / analysis-only)" toggle
   - **Expect:** A dashed-border sub-panel expands and shows a smoothed bear-probability chart plus the 2022 peak-to-trough true-bear dating (e.g., "2022-01-03 to 2022-10-12, −24.5%"). A disclosure statement visible inside the panel says this view is "future-aware analysis only" and never feeds any score or signal.
   - **Broken looks like:** Clicking "Show" does nothing, or the sub-panel expands but shows no smoothed chart or no disclosure text.

5. Click "Hide" on the retrospective sub-view, then navigate to `http://localhost:3835/?asof=2022-10-07`
   - **Expect:** The Market-Phase panel reloads for the 2022-10-07 as-of date. The timeline chart shows no dates after 2022-10-07. The 2022 downtrend episode row now shows an "open" badge (not "closed") because the downtrend was still active on that date.
   - **Broken looks like:** The timeline extends past 2022-10-07, or the 2022 episode still shows "closed".

6. Navigate to `http://localhost:3835/?asof=2023-02-02` and scroll to the Market-Phase panel recovery-turn signal line
   - **Expect:** The recovery-turn callout is green with an up-arrow icon and reads "Recovery / turn signalled" (or equivalent). A plain-language reason is visible explaining the trigger (e.g., "bear probability dropped below recovery threshold").
   - **Broken looks like:** The signal still shows "No recovery turn" at this known signal date, or no reason text is shown.

7. Navigate to `http://localhost:3835/research` and scroll down past the Regime×Setup×Pattern lab to find the "Recovery-Turn Edge" section
   - **Expect:** A clearly titled "Recovery-Turn Edge" section appears after the Regime×Setup×Pattern lab. It contains a per-horizon table with columns for Horizon, Mean Return, Win Rate, Expectancy, Max Drawdown, and a downside risk-adjusted metric. A survivorship-bias disclosure label is visible. No "buy" or "sell" button is present.
   - **Broken looks like:** No "Recovery-Turn Edge" section is present anywhere on the page, or it shows an error in place of the table.

8. In the Recovery-Turn Edge section, click the "Mean return" column header
   - **Expect:** The table rows reorder (highest mean return at top) and a sort-direction arrow appears on the "Mean return" column header. Clicking the same header a second time reverses the order (lowest at top).
   - **Broken looks like:** Clicking the column header does nothing.

9. In the Recovery-Turn Edge per-horizon table, click an "N=" chip (e.g., "N=6")
   - **Expect:** A new browser tab opens to a URL containing `/research/samples`. The cohort header on the samples page reads "All recovery-turn dates". The table on the samples page shows qualifying columns "Signal date", "Phase at signal", and "P(bear) at signal". The total row count on the samples page EXACTLY matches the N value from the chip you clicked.
   - **Broken looks like:** No new tab opens, or the samples page total count does not match the chip's N value, or the cohort header says something other than the recovery-turn cohort description.

10. Return to `http://localhost:3835` (no `?asof`) and confirm the existing Dashboard above-the-fold panels still show data
    - **Expect:** The primary risk score, stock list, or theme panels in the upper section of the Dashboard are still populated with data (not blank). The Market-Phase panel additions have not displaced or broken any above-the-fold content.
    - **Broken looks like:** The above-the-fold Dashboard panels show blank content, a loading spinner that never resolves, or a JavaScript error.

---

## What "Working Correctly" Looks Like

- The Market-Phase panel shows a multi-colored step-function SVG chart with a dashed as-of marker, at least one episode row with dates and a "closed" badge (on the live date), and a recovery-turn signal line with a plain-language reason
- Clicking "Show" on the retrospective toggle reveals a visually distinct dashed-border sub-panel with an explicit "analysis-only" disclosure — and clicking "Hide" collapses it cleanly
- Navigating to `?asof=2022-10-07` changes the episode status badge from "closed" to "open", confirming the as-of clamping is live
- The Recovery-Turn Edge lab on `/research` has a sortable per-horizon table, a survivorship-bias label, and N= chips that open count-coherent drill-downs in new tabs

## Common Issues

- **Market-Phase panel shows a loading skeleton for more than 60 s**: The backend cache is cold. Wait for the computation to complete; the skeleton should resolve once `/api/market-phase` returns. If it never resolves, check the backend logs for an error during market-phase computation.
- **Timeline or episode list is empty on the live date**: Confirm the backend has snapshot data. Run `curl http://localhost:8000/api/market-phase` and check that the response includes a non-empty `timeline` array.
- **Recovery-Turn Edge section is absent from `/research`**: The frontend build may be stale. Confirm the dev server is running and `apps/frontend/components/market-phase-card.tsx` includes the new sections.
- **N= chip count does not match samples page total**: This is a count-coherence regression. Note the exact N value from the chip and the total on the samples page, and report both values and the current Episodes/Pooled and As-of/All-history toggle states.
