# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38

**Mode:** record
**Date:** 2026-06-20
**Frontend URL:** http://localhost:3835

## Highlights

### Step 01 — Dashboard opens with compact market summary at the top  [NEW]

- **Narration:** The Dashboard now opens with two compact figures front and centre — Market Regime and Market Phase & Severity — so you can read the market's pulse at a glance without scrolling past any charts or tables.
- **Action:** Navigate to /
- **Point out:** Notice 'Market Regime' and 'Market Phase & Severity' are the very first elements visible, above the Major-indexes chart and everything else.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-01.png

### Step 02 — Market Regime shows live label and score  [NEW]

- **Narration:** The Market Regime figure displays the current regime label — such as 'Risk-on' — alongside a numeric score from 0 to 100, giving you an instant read on whether conditions favour risk-taking.
- **Action:** Navigate to /
- **Point out:** The label (e.g. 'Risk-on') and a score number appear together, with no loading spinner.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-02.png

### Step 03 — Market Phase & Severity shows badge, severity, and bear probability  [NEW]

- **Narration:** Right beside the regime figure, the Market Phase & Severity card shows the current phase badge, a 0–100 severity score, and a bear-probability chip — all the context you need to gauge how stretched or calm the market is right now.
- **Action:** Navigate to /
- **Point out:** Look for the phase badge (e.g. 'Expansion'), the severity number, and the 'P(bear)' chip all on one compact card.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-03.png

### Step 04 — Regime component breakdown expands inline  [NEW]

- **Narration:** Clicking 'Why this regime — component breakdown' reveals the named drivers behind the regime score without leaving the page — you can see exactly which signals are pushing the reading up or down.
- **Action:** Click the "Why this regime" button
- **Point out:** A list of named driver rows appears inline directly below the Market Regime figure; no new page opens.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-04.png

### Step 05 — Regime x phase cross-view chart appears below Major-indexes  [NEW]

- **Narration:** Scrolling down reveals the new 'Regime x phase cross-view' chart — a two-pane view that places regime-coloured bands and phase-coloured bands over the same index lines so you can see both market lenses together in one glance.
- **Action:** Navigate to /
- **Point out:** The cross-view card is present between the Major-indexes chart and the 'More detail' section, with a Hide toggle in the card header.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-05.png

### Step 06 — More detail section starts collapsed  [NEW]

- **Narration:** Below the cross-view chart, a 'More detail' section keeps the supporting cards — breadth metrics, Top Sectors, Top Themes, and Candidate Counts — tucked away until you want them, so the Dashboard stays uncluttered on first load.
- **Action:** Navigate to /
- **Point out:** The 'More detail' header is visible but none of the supporting cards (Top Sectors, Candidate Counts, etc.) are shown yet — the section is collapsed by default.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-06.png

### Step 07 — More detail expands to show supporting data cards  [NEW]

- **Narration:** One click on the 'More detail' header opens all five supporting cards — Top Sectors, Top Themes, Candidate Counts, breadth metrics, and the full Market Phase detail — each loaded with live data.
- **Action:** Click the "More detail" button
- **Point out:** After clicking, 'Top Sectors', 'Top Themes', and 'Candidate Counts' all appear with real data values.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-07.png

### Step 08 — Honest empty state for dates before phase history exists

- **Narration:** When an as-of date is set before enough market history exists to compute a phase, the dashboard shows a clear honest message rather than inventing a number — no fabricated data, ever.
- **Action:** Navigate to /
- **Point out:** The phase figure reads 'Not enough history to derive a market phase for this date — reported NA, never fabricated.' instead of a made-up score.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38/step-08.png
