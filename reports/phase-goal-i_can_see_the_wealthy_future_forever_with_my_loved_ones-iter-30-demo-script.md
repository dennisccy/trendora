# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30

**Mode:** record
**Date:** 2026-06-18
**Frontend URL:** http://localhost:3835
**Iteration:** 30

## Highlights

### Step 01 — Dashboard — full market-phase history timeline  [NEW]

- **Narration:** The Dashboard now shows the complete history of market conditions as a color-coded step-function chart — green bands for Expansion and Recovery, amber for Pullback, red for Correction and Bear — with a filtered bear-probability line running across every snapshot date.
- **Action:** Navigate to /
- **Point out:** The multi-year SVG chart with its color bands, bear-probability polyline, and dashed as-of marker at today's date.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-01.png

### Step 02 — 2022 downtrend episode — dated and closed  [NEW]

- **Narration:** Beneath the timeline chart, a dated causal episode list shows exactly when each historical downtrend began — including the 2022 bear market — with its first-trigger date, severity at trigger, peak bear probability, and an open or closed badge indicating whether it had resolved by the selected date.
- **Action:** Navigate to /
- **Point out:** The 2022 episode row showing a first-trigger date in early 2022, a non-zero severity, and a 'closed' badge on the live date.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-02.png

### Step 03 — Historical as-of — 2022 episode shows open  [NEW]

- **Narration:** Navigating to a date inside the 2022 bear market clamps the entire timeline to that point in time: the chart shows no data after October 2022, and the 2022 episode badge switches from 'closed' to 'open' because the downtrend had not yet ended at that date.
- **Action:** Navigate to /?asof=2022-10-07
- **Point out:** The episode row now showing an 'open' badge, and the timeline chart ending at the as-of date with no future bars.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-03.png

### Step 04 — Retrospective view — fenced smoothed bear-probability and true-bear dating  [NEW]

- **Narration:** A clearly-labelled 'Retrospective (full-sample / analysis-only)' toggle lets you peek at the hindsight-smoothed bear probability and the after-the-fact peak-to-trough true-bear dates — such as the 2022 bear spanning roughly −24.5% — while a prominent disclosure ensures this future-aware view is never confused with a live signal.
- **Action:** Navigate to /
- **Point out:** The dashed-border sub-panel that expands after clicking Show, containing the smoothed probability and the 2022 peak-to-trough dating with an explicit analysis-only disclosure.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-04.png

### Step 05 — Recovery-turn signal — green at a confirmed turn date  [NEW]

- **Narration:** Stepping to a date when the market genuinely turned — early 2023, when bear probability dropped below the recovery threshold and the index reclaimed its trailing average — lights up a green up-arrow signal with a plain-language reason explaining exactly why the turn was called.
- **Action:** Navigate to /?asof=2023-02-02
- **Point out:** The green recovery-turn signal callout with its up-arrow icon, the affirmative phrasing, and the plain-language reason printed beneath it.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-05.png

### Step 06 — Recovery-turn signal — muted on today's Expansion date  [NEW]

- **Narration:** Back on the live date, with the market in Expansion and bear probability near zero, the signal correctly shows a muted shield icon and 'No recovery turn at this date' — the system is honest that a recovery signal applies only at downtrend exits, not during an ongoing expansion.
- **Action:** Navigate to /
- **Point out:** The muted shield-icon callout and 'No recovery turn' text, confirming the signal only fires when the conditions are genuinely met.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-06.png

### Step 07 — Research — Recovery-Turn Edge lab with sortable per-horizon table  [NEW]

- **Narration:** The Research page gains a new Recovery-Turn Edge lab showing the forward-return track record at every historical recovery-turn date — mean return, median, win rate, expectancy, average max-drawdown, and a downside risk-adjusted figure — broken out per holding horizon and by the market phase at the time of each signal.
- **Action:** Navigate to /research
- **Point out:** The Recovery-Turn Edge section after the existing Regime x Setup x Pattern lab, with its sortable per-horizon table, survivorship-bias disclosure, and N= count chips.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-07.png

### Step 08 — N= chip opens count-coherent samples drill-down  [NEW]

- **Narration:** Every N= chip in the Recovery-Turn Edge lab opens an exact list of the signal dates behind that count in a new tab, with columns for signal date, market phase at the time, and bear probability — and the total on the samples page always matches the number shown on the chip.
- **Action:** Navigate to /research
- **Point out:** The samples page opening with a cohort header for recovery-turn dates and a row count that matches the N value from the chip you clicked.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30/step-08.png
