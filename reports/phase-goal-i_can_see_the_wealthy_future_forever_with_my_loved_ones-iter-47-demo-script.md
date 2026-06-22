# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47

**Mode:** record
**Date:** 2026-06-22
**Frontend URL:** http://localhost:3835
**Iteration:** 47

## Highlights

### Step 01 — Dashboard — current market regime at a glance

- **Narration:** We open the dashboard to see today's market regime score and phase. The data is served instantly from persisted snapshots with no recomputation.
- **Action:** Navigate to /
- **Point out:** Regime score, phase label (e.g. Expansion or Risk-on), and the as-of date shown in the panel.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-01.png

### Step 02 — As-of toggle — step back to a historical date

- **Narration:** Clicking the back-navigation control on the as-of panel steps the entire dashboard to a past date, showing how the regime and scores looked at that moment in time.
- **Action:** Navigate to /?asof=2026-05-15
- **Point out:** The regime score and phase label update to the historical values — the as-of date indicator in the panel changes to match.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-02.png

### Step 03 — Research hub — all seven labs one click away

- **Narration:** The Research section is always visible in the sidebar. Opening it shows all seven analytical labs with descriptions and direct links — no hidden menus required.
- **Action:** Navigate to /research
- **Point out:** Seven lab cards listed on the hub page, each with a title, description, and a link to its dedicated route.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-03.png

### Step 04 — Event-Study matrix — per-horizon mean return and win-rate  [NEW]

- **Narration:** The Setup and Pattern event-study lab now loads reliably on the full live dataset. Each row shows a horizon window with a mean return, win-rate, and sample count — figures the backend previously failed to serve without running out of memory.
- **Action:** Navigate to /research/event-study
- **Point out:** Five horizon rows (1d through 60d) each showing a numeric mean return percentage, a win-rate, and an N= sample count chip.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-04.png

### Step 05 — Event-Study N= drill-down — count coherence confirmed  [NEW]

- **Narration:** Clicking any N= chip on the event-study matrix navigates to the sample-level drill-down. The total count on that page matches the integer shown on the chip exactly.
- **Action:** Navigate to /research/samples?kind=event-study&horizon=20&subject=Actionable&slice=pooled&view=episodes
- **Point out:** The samples page header showing a total of 455 observations — the same number displayed on the 20d chip in the matrix.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-05.png

### Step 06 — Factor-combination lab — composite cohort with real figures  [NEW]

- **Narration:** The multi-factor combination lab aggregates across the full pool of 598,271 symbol-dates and shows how a composite rank-blend narrows the field. All cohort rows render with numeric mean return and hit-rate — no backend error.
- **Action:** Navigate to /research/factor-combination
- **Point out:** A pool size of 598,271, a composite cohort row showing mean return and hit-rate, and per-condition breakdowns beneath.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-06.png

### Step 07 — Regime x Setup x Pattern — ranked combination table  [NEW]

- **Narration:** This lab ranks every combination of market regime, setup, and pattern by forward return. The table loads with over 100 rows of real figures — low-sample combinations correctly show NA rather than fabricated values.
- **Action:** Navigate to /research/regime-setup-pattern
- **Point out:** The top-ranked row showing Defensive regime, Actionable setup, mean return of +5.66%, and an honest NA marker on rows where sample counts are too small.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-07.png

### Step 08 — Downtrend Opportunity — which stocks held up best  [NEW]

- **Narration:** The Downtrend Opportunity lab shows which market phases historically produced the best recoveries. The Expansion phase row leads with a mean return of +5.18% across 591 episodes — data that now loads immediately from the warm cache.
- **Action:** Navigate to /research/downtrend-opportunity
- **Point out:** The Held-up-best table with the Expansion row at n=591 and mean return +5.18%, alongside the Recovery-Turn Edge section below.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47/step-08.png
