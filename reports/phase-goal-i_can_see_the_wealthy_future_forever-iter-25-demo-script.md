# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-25

**Mode:** record
**Date:** 2026-06-09
**Frontend URL:** http://localhost:3835
**Iteration:** 25

## Highlights

### Step 01 — Data Manager — all three panels load  [NEW]

- **Narration:** Opening the Data Manager shows three panels at once: the existing Coverage table, the new Missing-data diagnostic below it, and the Unfinished-imports tracker at the bottom. The page is fully hydrated with no red error banners.
- **Action:** Navigate to /data
- **Point out:** Look for the 'Data Manager' heading, the 'Online' health badge, and the 'Missing-data diagnostic' panel appearing directly below the Coverage panel.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-01.png

### Step 02 — Missing-data diagnostic — clean empty state  [NEW]

- **Narration:** When every universe member has enough price history and no internal gaps, the diagnostic panel shows a reassuring 'No missing data' confirmation instead of hiding silently or showing a blank card.
- **Action:** Navigate to /data
- **Point out:** The panel reads 'No missing data' with a plain-language explanation. No 'Pull' buttons or shortfall rows are visible.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-02.png

### Step 03 — Coverage panel unchanged — one date selector

- **Narration:** The Coverage panel with per-symbol bar counts remains exactly as before, positioned above the new diagnostic panel. Across the entire page there is still exactly one date selector — the global as-of switcher — not a second one introduced by the new panels.
- **Action:** Navigate to /data
- **Point out:** The Coverage panel rows are visible with bar counts. Scan the full page and confirm only the top-right 'View as-of date' dropdown is present; no extra date control appears in the diagnostic or unfinished-imports areas.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-03.png

### Step 04 — Unfinished imports — three import states visible  [NEW]

- **Narration:** The new Unfinished-imports panel consolidates every import that did not finish cleanly. Paused and partial rows carry an amber badge; failed rows carry a red badge. Each row shows a plain-language explanation plus done, remaining, and failed counts.
- **Action:** Navigate to /data
- **Point out:** Find the 'Unfinished imports' heading (not the old 'Resumable imports'). Amber badges on rows that say 'Paused' or 'Partial'; red badges on rows that say 'Failed'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-04.png

### Step 05 — Retry remaining — re-dispatches only failed work  [NEW]

- **Narration:** Clicking 'Retry remaining' on a partial import creates a new job scoped only to the symbols that previously failed. The job card updates to show the retry running, and the original run-history entry below stays intact.
- **Action:** Click the "Retry remaining" button
- **Point out:** After clicking Retry, a job card appears showing the symbol range from the partial import. The run-history table below is unchanged.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-05.png

### Step 06 — Dismiss — row leaves panel, audit log stays  [NEW]

- **Narration:** The Dismiss button removes a row from the Unfinished-imports panel immediately, but the corresponding entry in the run-history audit table below is untouched. The permanent record of what ran is always preserved.
- **Action:** Click "[data-testid='dismiss-button']"
- **Point out:** After clicking Dismiss, the row count in the Unfinished-imports panel drops by one. Scroll down to confirm the run-history table still shows the entry for that import.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-06.png

### Step 07 — Session key re-prompt — inline, masked, never echoed  [NEW]

- **Narration:** When a paused or failed import came from a provider that requires an API key, the Retry or Resume row shows an inline key input before dispatching. The key is masked as a password field and never appears in the job card or any state string.
- **Action:** Navigate to /data
- **Point out:** Look for the 'Session API key' input field inline on the row. After entering and submitting a key, the job card shows the import running but contains no trace of the key text.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-07.png

### Step 08 — Panel label — 'Unfinished imports', not 'Resumable imports'  [NEW]

- **Narration:** The panel heading now reads 'Unfinished imports', reflecting that it covers all three states — paused, partial, and failed — not just imports waiting to be resumed.
- **Action:** Navigate to /data
- **Point out:** The panel heading reads exactly 'Unfinished imports'. The old label 'Resumable imports' does not appear anywhere on the page.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-25/step-08.png
