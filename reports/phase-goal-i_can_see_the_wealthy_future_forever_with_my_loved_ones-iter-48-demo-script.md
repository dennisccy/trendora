# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48

**Mode:** record
**Date:** 2026-06-23
**Frontend URL:** http://localhost:3835
**Iteration:** 48

## Highlights

### Step 01 — Open the Research hub

- **Narration:** The Research hub is the gateway to all five analytical labs. From here, every evidence-based study the platform offers is one click away.
- **Action:** Navigate to /research
- **Point out:** The Factor Lab link is visible without scrolling — one click gets you there.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48/step-01.png

### Step 02 — Navigate to Factor Lab  [NEW]

- **Narration:** Clicking Factor Lab takes you directly to the decile-analysis tool where every factor in the universe is ranked by its predictive power.
- **Action:** Click the "Factor Lab" link
- **Point out:** The factor dropdown and horizon buttons load — the page is ready for a query.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48/step-02.png

### Step 04 — Factor Lab decile table loads with real figures  [NEW]

- **Narration:** After roughly 50 to 120 seconds, ten decile rows appear — each showing a real mean forward return and a sample count in the hundreds of thousands. This page was returning an error on every request before this fix; now it delivers the evidence.
- **Action:** Navigate to /research/factor-lab
- **Point out:** D1 through D10 each show a numeric mean return (around +0.61% to +0.92%) and an N count near 60,000 per decile — no blank cells, no error banner.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48/step-04.png

### Step 05 — Rank-IC statistic confirms factor predictiveness  [NEW]

- **Narration:** Below the decile table, the Rank-IC section breaks down factor predictiveness by market regime. Each regime shows a Spearman rank correlation — a positive number in risk-on periods, negative in risk-off — so you can see exactly when a factor's edge is strongest.
- **Action:** Navigate to /research/factor-lab
- **Point out:** Numeric Rank-IC values appear for every regime (strong risk-on through risk-off) — the value is a real figure, not blank or NaN.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48/step-05.png

### Step 07 — Factor Combination lab confirms real figures  [NEW]

- **Narration:** The Factor Combination lab lets you blend two factors and see how the overlap cohort performs. This iteration also hardened the cold-start path here, so first-time visitors no longer risk a memory error on the initial load.
- **Action:** Navigate to /research/factor-combination
- **Point out:** The combined cohort table shows baseline n=598,271 at +0.88% mean return, and the strict-overlap cohort has its own count and return — all real figures, no error banner.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48/step-07.png

### Step 08 — Honest error banner when the backend is unavailable

- **Narration:** When the backend genuinely cannot serve data, the Factor Lab shows a clear message explaining that no figures are displayed — never fabricated numbers. The platform never invents data to paper over a real problem.
- **Action:** Navigate to /research/factor-lab
- **Point out:** The error banner reads 'Backend unavailable — The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values.' The decile table is absent; only the honest message appears.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48/step-08.png

## Full tour (text only)

### Step 03 — Select the Leadership Score factor and 20-day horizon  [NEW]

- **Narration:** Choose the Leadership Score factor and a 20-day forward-return horizon. The platform now streams the full dataset rather than loading everything into memory at once, so this query completes reliably instead of crashing.
- **Action:** Click the "20d" button
- **Point out:** The factor dropdown shows 11 available factors; the horizon buttons (1d through 60d) are active.

### Step 06 — N= chip drills down to matching samples

- **Narration:** Every decile row carries an N= chip showing the exact observation count. Clicking it opens a samples page pre-filtered to that decile, so you can inspect the individual market readings behind each figure.
- **Action:** Navigate to /research/factor-lab
- **Point out:** The N= chip on D1 shows roughly 59,827 observations — that same count will appear as the total on the samples page it links to.
