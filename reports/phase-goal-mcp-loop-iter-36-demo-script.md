# Demo Script — goal-mcp-loop-iter-36

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3255
**Iteration:** 36

## Highlights

### Step 01 — Discover the new Referee Audit card  [NEW]

- **Narration:** Let's check out the newest addition to the Research hub — a report that checks whether Trendora's own fact-checker can be trusted.
- **Action:** Navigate to /research
- **Point out:** Scroll to 'Governance & process' — there are 4 cards now instead of 3, and the newest one is 'Referee audit.'
- **Screenshot:** reports/demo/goal-mcp-loop-iter-36/step-01.png

### Step 02 — Open the Referee Audit report  [NEW]

- **Narration:** Opening it shows how well that fact-checker grades itself, tested against 200 fake patterns it should always reject.
- **Action:** Click "[data-testid='research-governance-link-referee-audit']"
- **Point out:** Four numbers load right away — 200 test trials, a 0.08 false-alarm rate, the 0.05 bar it's held to, and the date this check last ran.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-36/step-02.png

### Step 03 — See the tripwire warning  [NEW]

- **Narration:** The real test: a pattern that secretly peeks at future prices was slipped in, just to see if the fact-checker would catch the cheat.
- **Action:** Navigate to /research/referee-audit
- **Point out:** It didn't catch it this time — so instead of staying quiet, the page shows a loud red warning explaining exactly what happened.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-36/step-03.png

### Step 04 — Back to the Research hub

- **Narration:** Heading back to Research shows the new report sitting comfortably alongside the ones that were already there.
- **Action:** Click the "Back to Research" link
- **Point out:** All four governance cards are present, in the same order as before — nothing else moved.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-36/step-04.png

### Step 05 — Confirm the budget card still works

- **Narration:** A quick check that nothing else broke — the existing budget-tracking card still opens exactly like it always has.
- **Action:** Click "[data-testid='research-governance-link-budget']"
- **Point out:** Its own numbers load normally, confirming this update didn't disturb its neighbors.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-36/step-05.png

### Step 06 — Confirm the evidence ledger is untouched

- **Narration:** One last check: did any of those 200 practice trials accidentally sneak into Trendora's real evidence ledger?
- **Action:** Navigate to /evidence
- **Point out:** They didn't — the evidence page looks exactly as it did before, still honestly marked, with nothing new added.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-36/step-06.png
