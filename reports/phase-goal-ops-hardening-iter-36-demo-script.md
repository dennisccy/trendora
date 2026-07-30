# Demo Script — goal-ops-hardening-iter-36

**Mode:** record
**Date:** 2026-07-30
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Factor Lab research page  [NEW]

- **Narration:** The Factor Lab is one of four research pages that have just gained honest feedback on slow or failed loads.
- **Action:** Navigate to /research/factor-lab
- **Point out:** Look for the heading 'Research — Factor Lab' and a data table of factors below it.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-36/step-01.png

### Step 02 — View the Phase Severity Lab  [NEW]

- **Narration:** The Phase Severity Lab now shows the same honest 'still computing' feedback as Regime Lab when a slow load occurs.
- **Action:** Navigate to /research/phase-severity-lab
- **Point out:** Notice the heading 'Research — Market Phase & Severity Lab' and tables showing phase and severity data.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-36/step-02.png

### Step 03 — Open the Regime × Phase × Factor page  [NEW]

- **Narration:** This page now displays the same computing notice and has a working Retry button if the backend becomes unavailable.
- **Action:** Navigate to /research/regime-phase-factor
- **Point out:** The page heading shows 'Research — Regime × Phase × Factor' with study controls visible immediately.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-36/step-03.png

### Step 04 — View the Severity-velocity × Regime study  [NEW]

- **Narration:** All four sibling research labs now provide identical, honest feedback during slow or failed loads — no more bare unlabelled skeletons.
- **Action:** Navigate to /research/severity-velocity
- **Point out:** The heading reads 'Research — Severity-velocity × Regime' and the study data displays normally.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-36/step-04.png

### Step 05 — Check the Regime Lab for consistency

- **Narration:** Regime Lab already had these features. The four sibling labs are now wired identically, so all five research pages behave the same way.
- **Action:** Navigate to /research/regime-lab
- **Point out:** This page continues to show the 'Still computing' card on a slow load, just as it did before.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-36/step-05.png

### Step 06 — Verify the Data page is unchanged

- **Narration:** The Data page looks and behaves the same as before. The backend improvements behind it are internal memory-bounding changes, not visible to users.
- **Action:** Navigate to /data
- **Point out:** The coverage panel shows the universe count, price history date range, and a membership timeline chart — all numbers match what they were before.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-36/step-06.png

## Full tour (text only)

### Step 07 — Check Evidence page per-claim expectations

- **Narration:** The Evidence page still shows real computed drawdown expectations for claims, thanks to the backend's new memory-bounded loading on the evidence serving path.
- **Action:** Navigate to /evidence
- **Point out:** Click into a certified claim row to expand the 'drawdown & dry-spell expectations' panel and confirm it shows real figures, not an 'unavailable' placeholder.
