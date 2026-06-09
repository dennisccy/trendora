# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-26

**Mode:** record
**Date:** 2026-06-09
**Frontend URL:** http://localhost:3835

## Highlights

### Step 01 — Data Manager loads with all panels intact

- **Narration:** We open the Data Manager page, which organises everything about your imported price history. All sections — Unfinished Imports, coverage table, and the fetch form — load cleanly with no errors.
- **Action:** Navigate to /data
- **Point out:** The 'Data Manager' heading, the Unfinished Imports panel showing its rows, and the fetch form are all visible without any blank boxes or error boundaries.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-26/step-01.png

### Step 02 — Unfinished Imports panel shows paused and partial runs

- **Narration:** The Unfinished Imports panel lists every import that didn't finish — partial runs and provider-paused jobs — so nothing is silently lost. Each row shows a plain-language status and action buttons.
- **Action:** Navigate to /data
- **Point out:** The rows in the Unfinished Imports panel with their status labels, Retry buttons, and Dismiss buttons are all visible and intact.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-26/step-02.png

### Step 03 — Retry an unfinished import queues a new job

- **Narration:** Clicking Retry on any unfinished import queues a fresh job attempt right away. The panel keeps all its rows — nothing disappears — and the job progress area updates to show the new job running.
- **Action:** Click the "Retry remaining" button
- **Point out:** After clicking Retry, the Job progress panel shows a new running job while the Unfinished Imports panel still shows its full list of rows.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-26/step-03.png

### Step 04 — Dismiss a row without losing the rest  [NEW]

- **Narration:** Dismissing a row removes just that one entry and leaves every other row in place. The panel does not flash empty or lose its remaining imports.
- **Action:** Navigate to /data
- **Point out:** The dismissed row is gone and the row count drops by one, but the rest of the panel is unchanged and the section heading is still present.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-26/step-04.png

### Step 05 — Exactly one global date selector — no accidental duplicates

- **Narration:** A core design rule is that the whole product shares a single 'View as-of date' control. This iteration's fixes touched the Unfinished Imports panel and added no extra date inputs anywhere on the page.
- **Action:** Navigate to /data
- **Point out:** Only one date-related selector — labelled 'View as-of date' — is present on the page. The fetch form's start/end date fields are job-entry fields, not a second viewing-date control.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-26/step-05.png

### Step 06 — Per-symbol coverage table confirms the dataset

- **Narration:** Below the Unfinished Imports panel the per-symbol coverage table shows how many price bars each ticker has. This lets you see exactly where the data is healthy versus where more history is needed.
- **Action:** Navigate to /data
- **Point out:** The coverage rows listing each symbol alongside its bar count are visible. No raw JSON or 'Something went wrong' message appears anywhere on the page.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-26/step-06.png
