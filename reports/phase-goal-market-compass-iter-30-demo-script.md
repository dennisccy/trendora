# Demo Script — goal-market-compass-iter-30

**Mode:** record
**Date:** 2026-09-01
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the default landing page  [NEW]

- **Narration:** The default landing page now displays real direction words across all three Market state badges. Regime, Market phase, and Breadth all show 'little changed' instead of placeholder values.
- **Action:** Navigate to /
- **Point out:** Notice the three direction badges in the Market state card all show real words, and the Summary card confirms the same condition.
- **Screenshot:** reports/demo/goal-market-compass-iter-30/step-01.png

### Step 02 — Navigate to full market context

- **Narration:** The market context link takes you to a detailed market view showing regime and phase analysis, sectors, and themes for deeper understanding.
- **Action:** Click the "Full market context (regime × phase, sectors, themes)" link
- **Point out:** The full market context page loaded, showing additional analysis tools beyond the quick summary on the homepage.
- **Screenshot:** reports/demo/goal-market-compass-iter-30/step-02.png

### Step 03 — Compare with a previous date

- **Narration:** A previous date shows different direction words, confirming that this update only affects the most current data snapshot and leaves historical records unchanged.
- **Action:** Navigate to /?asof=2026-08-03
- **Point out:** The badges here show 'improving' instead of 'little changed', proving each date has its own independent snapshot.
- **Screenshot:** reports/demo/goal-market-compass-iter-30/step-03.png

### Step 04 — Verify older dates still load

- **Narration:** Dates from two years ago load normally, showing that this change has no impact on historical data and the system remains fully backward compatible.
- **Action:** Navigate to /?asof=2025-04-15
- **Point out:** The page renders normally for a date from two years ago, confirming no regression across the full historical range.
- **Screenshot:** reports/demo/goal-market-compass-iter-30/step-04.png
