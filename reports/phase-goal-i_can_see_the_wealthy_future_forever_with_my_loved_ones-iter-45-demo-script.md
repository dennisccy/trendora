# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45

**Mode:** record
**Date:** 2026-06-22
**Frontend URL:** http://localhost:3835
**Iteration:** 45

## Highlights

### Step 01 — Research hub — seven focused labs  [NEW]

- **Narration:** The Research section is now a clean hub that lists seven named labs as cards. Opening it no longer fires four heavy data requests at once — only the labs you actually visit load their analysis.
- **Action:** Navigate to /research
- **Point out:** Seven named lab cards appear on the page, each with a short description. No heavy matrix or analysis table is shown here — just a fast menu.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-01.png

### Step 02 — Navigate to the Severity-velocity study  [NEW]

- **Narration:** Click the Severity-velocity card to open the new study page. Only this lab's data loads — no other labs fetch in the background.
- **Action:** Click the "Severity-velocity" link
- **Point out:** The browser navigates to /research/severity-velocity and begins loading the regime-family matrix. The other labs remain unloaded.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-02.png

### Step 03 — Severity-velocity matrix with mean returns and win-rates  [NEW]

- **Narration:** The new Severity-velocity study shows a 3-by-3 matrix — rows for Risk-on, Neutral, and Risk-off regimes; columns for Rising, Flat, and Falling stress velocity. Each cell displays the mean forward SPY return, win-rate, and observation count.
- **Action:** Navigate to /research/severity-velocity
- **Point out:** Look at the matrix cells: each one shows a mean return percentage, a win-rate, and an N= count. The default horizon is 20-day forward returns.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-03.png

### Step 04 — Switch the forward-return horizon to 5 days  [NEW]

- **Narration:** The horizon selector lets you change the forward-return window without reloading the page. Clicking '5d' immediately updates every cell with the 5-day forward-return figures.
- **Action:** Click the "5d" button
- **Point out:** After clicking 5d, the matrix heading updates to show '(5d)' and the numeric values in the cells change — confirming the in-place update works correctly.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-04.png

### Step 05 — Honest verdict card with caveats  [NEW]

- **Narration:** Scroll down to find the verdict card, which states plainly that the hypothesis is NOT supported on this data. Rising stress under a Risk-off regime historically preceded a bounce — not a continued decline — and the card names all three data limitations up front.
- **Action:** Navigate to /research/severity-velocity
- **Point out:** The verdict card reads 'NOT supported', mentions 'survivorship', 'bull-dominated', and 'underpowered for sustained crashes'. No positive or optimistic conclusion contradicts this finding.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-05.png

### Step 06 — N= chip opens the reproducing cohort in a new tab  [NEW]

- **Narration:** Every N= count in the matrix is a clickable link. Clicking it opens the exact list of dates and SPY returns behind that cell in a new tab, so you can verify the figures yourself.
- **Action:** Navigate to /research/samples?kind=severity-velocity&horizon=20&family=risk_on&velocity_sign=rising
- **Point out:** The new tab opens at /research/samples with a human-readable description — for example 'Risk on · Velocity: rising / Horizon: 20d' — and the total observation count matches the chip you clicked exactly.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-06.png

### Step 07 — As-of date carried from hub to sub-route  [NEW]

- **Narration:** When you open the Research hub with a historical as-of date in the URL, every lab card link already includes that date. Clicking a card drops you straight into the lab scoped to the chosen point in time.
- **Action:** Navigate to /research?asof=2025-06-30
- **Point out:** The browser URL shows asof=2025-06-30 after navigating from the hub — no extra step is needed to apply the date filter to the lab.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-07.png

### Step 08 — Regime × Setup × Pattern lab loads at its own URL  [NEW]

- **Narration:** The existing Regime × Setup × Pattern study now lives at its own dedicated URL and loads only when you visit it directly. The figures are byte-identical to those shown before the research section was split.
- **Action:** Navigate to /research/regime-setup-pattern
- **Point out:** The page heading reads 'Research — Regime × Setup × Pattern' and N= chips are visible in the matrix. This lab did not reload or re-compute when you visited other labs earlier.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45/step-08.png
