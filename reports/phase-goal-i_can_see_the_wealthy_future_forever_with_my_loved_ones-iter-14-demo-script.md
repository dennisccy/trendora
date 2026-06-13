# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14

**Mode:** record
**Date:** 2026-06-13
**Frontend URL:** http://localhost:3835
**Iteration:** 14

## Highlights

### Step 01 — Open the Research lab — Episodes mode by default  [NEW]

- **Narration:** The event study lab now opens in Episodes mode every time, showing a clean segmented toggle with 'Episodes' highlighted. This is the new starting point for all pattern research.
- **Action:** Navigate to /research
- **Point out:** The 'Episodes' button is highlighted in the toggle next to the subject selector — 'Pooled' is visible but inactive.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-01.png

### Step 02 — Read the three-value disclosure line in Episodes mode  [NEW]

- **Narration:** Below the event study figures, a disclosure line now shows three labeled values — the observation count, how many distinct stock symbols are represented, and how many first-trigger episodes collapsed into that count.
- **Action:** Navigate to /research
- **Point out:** Look for the muted text line reading 'n … Unique symbols … Episodes …' — all three numbers should be non-zero.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-02.png

### Step 03 — Switch to Pooled mode — n count jumps  [NEW]

- **Narration:** Clicking 'Pooled' switches the lab to count every signal day instead of collapsing runs into a single episode per stock. The observation count rises immediately — no page reload needed.
- **Action:** Click the "Pooled" button
- **Point out:** Watch the n value in the disclosure line increase after clicking Pooled, and the 'Pooled' button become the active pill.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-03.png

### Step 04 — All figures update in Pooled mode

- **Narration:** Every chart in the lab — hit-rate, expectancy, MAE/MFE, by-regime breakdown, and by-sector breakdown — recalculates for the pooled observation set. No figure goes blank; the numbers simply reflect a larger, per-signal-day cohort.
- **Action:** Navigate to /research
- **Point out:** Confirm that hit-rate, expectancy, and the by-regime/by-sector panels are all populated with values that differ from the Episodes numbers.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-04.png

### Step 05 — N= chip carries the active view into its link  [NEW]

- **Narration:** Every N= chip in the lab dynamically encodes the current mode in its URL. In Episodes mode the link says view=episodes; switch to Pooled and the same chip changes to view=pooled. The drill-down will always match what you were looking at.
- **Action:** Navigate to /research
- **Point out:** Hover over an N= chip and check the URL shown in the browser status bar — it should contain 'view=episodes' when Episodes is active.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-05.png

### Step 06 — Episodes drill-down — cohort header confirms 'Episodes (first-trigger)'  [NEW]

- **Narration:** Opening an N= chip from Episodes mode lands on a samples page that names exactly what it shows: 'Episodes (first-trigger)'. The row count on the page matches the N you clicked — no mystery about what the sample represents.
- **Action:** Navigate to /research/samples?kind=event-study&horizon=1&subject=Actionable&slice=pooled&view=episodes
- **Point out:** The header line near the top of the samples page should read 'Slice: Episodes (first-trigger) · All occurrences' and the total observation count should match the chip.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-06.png

### Step 07 — Pooled drill-down — cohort header confirms 'Pooled (per-signal-day)'  [NEW]

- **Narration:** The same drill-down page opened from a Pooled-mode chip shows a larger sample and states 'Pooled (per-signal-day)' in the header. Both views are fully supported — the cohort label removes any ambiguity about which counting method produced the rows.
- **Action:** Navigate to /research/samples?kind=event-study&horizon=1&subject=Actionable&slice=pooled&view=pooled
- **Point out:** The header reads 'Slice: Pooled (per-signal-day) · All occurrences' and the total observation count is higher than in the Episodes drill-down.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-07.png

### Step 08 — Methodology glossary — Episode and Pooled definitions  [NEW]

- **Narration:** The methodology page now includes two new glossary entries. 'Episode' explains that consecutive same-stock signal days are collapsed into a single first-trigger observation. 'Pooled (per-signal-day)' explains the unrestricted counting method — both definitions are distinct and authored.
- **Action:** Navigate to /methodology
- **Point out:** Scroll the methodology glossary and confirm both 'Episode' and 'Pooled (per-signal-day)' entries are present with full, non-empty definitions.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14/step-08.png
