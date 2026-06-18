# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32

**Mode:** record
**Date:** 2026-06-18
**Frontend URL:** http://localhost:3835
**Iteration:** 32

## Highlights

### Step 01 — Dashboard — market phase at a glance

- **Narration:** We start on the dashboard, where the market-phase panel shows the current regime, severity score, and drawdown — all unchanged and unaffected by this iteration's additions.
- **Action:** Navigate to /
- **Point out:** The regime label and severity score are visible. No new date pickers or macro-conditioned values have appeared here.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-01.png

### Step 02 — Research page — new Downtrend Opportunity section  [NEW]

- **Narration:** On the Research page, scrolling below the Recovery-Turn Edge lab reveals the brand-new Downtrend Opportunity study. Three ranked tables appear side by side: stocks that held up best, fell hardest, and the recovery-turn edge — all conditioned on the market state at the time each signal fired.
- **Action:** Navigate to /research
- **Point out:** Three table panels labelled 'Held up best', 'Fell hardest', and 'Recovery-turn edge by phase' are visible below the existing labs.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-02.png

### Step 03 — Switch conditioning dimension to Severity band  [NEW]

- **Narration:** The 'Condition on' control lets you slice the tables by the market state at each signal date. Switching to Severity band instantly replaces the phase-label rows with severity-band cohort labels across all three tables — no page reload.
- **Action:** Click the "Severity band" button
- **Point out:** Row labels in all three tables update to show Calm, Elevated, Severe, and Stressed bands.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-03.png

### Step 04 — Sort a column — NA rows stay last  [NEW]

- **Narration:** Clicking any column header re-sorts the table client-side. Rows with insufficient data show NA and are always pinned to the bottom regardless of sort direction, so the most informative rows stay at the top.
- **Action:** Click the "Severity band" button
- **Point out:** After clicking the Mean column header, numeric rows rise to the top and NA rows remain at the bottom.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-04.png

### Step 05 — N= chip drills into raw samples  [NEW]

- **Narration:** Every table row carries an N= chip showing exactly how many observations back the statistic. Clicking it opens the raw sample rows in a new tab, and the count on that page always matches the chip — count coherence is enforced.
- **Action:** Navigate to /research/samples?kind=downtrend-opportunity&horizon=20&dimension=phase&cohort=Expansion&view=episodes
- **Point out:** A new tab at /research/samples shows the cohort description header and individual ticker rows whose count matches the N= chip.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-05.png

### Step 06 — 'Fell hardest' carries a research-only label  [NEW]

- **Narration:** The 'Fell hardest' angle is historical evidence about what weakened most during past downtrends. It is clearly labelled 'Research evidence only' and has no order, short, or trade button anywhere near it — the platform takes no position and offers no short-deployment path.
- **Action:** Navigate to /research
- **Point out:** The 'RESEARCH EVIDENCE ONLY' label appears directly on the Fell hardest panel. There are no trade or action buttons.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-06.png

### Step 07 — Survivorship-bias and macro disclosure notices  [NEW]

- **Narration:** Two transparency notices live inside the section. One discloses that the walk-forward evidence is measured on the current-membership universe and therefore carries survivorship bias. The other explains that macro inputs are optional and off by default, and that any macro figure used for a past date must have been published on or before that date — never a fabricated value.
- **Action:** Navigate to /research
- **Point out:** Both the 'Survivorship bias' caveat and the 'Macro inputs (FRED) are optional and off by default' notice are readable without expanding any accordion.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-07.png

### Step 08 — Data Manager — FRED macro feed panel  [NEW]

- **Narration:** The Data Manager now shows a Macro feed panel listing the four FRED series that power optional macro conditioning. The env-var name is displayed with a 'not set' status — no actual key value is ever shown. All three wiring legs report as off, confirming that default figures everywhere in the app are unchanged.
- **Action:** Navigate to /data
- **Point out:** The 'FRED (macro feed)' panel is visible below the missing-data diagnostic, with four series rows and three wiring legs all showing 'off'. The FRED_API_KEY name appears but no key string is revealed.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32/step-08.png
