# Demo Script — goal-ops-hardening-iter-7

**Mode:** record
**Date:** 2026-07-21
**Frontend URL:** http://localhost:3255
**Iteration:** 7

## Highlights

### Step 01 — Open the Data Manager

- **Narration:** We start on the Data Manager, the page that tracks every backfill and refresh job that keeps the site's market data up to date.
- **Action:** Navigate to /data
- **Point out:** The 'Start a fetch / backfill job' panel, and a summary of the most recent job the site has run.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-7/step-01.png

### Step 04 — Start the job — and watch the ingest-time warm-up  [NEW]

- **Narration:** Clicking Start kicks off the backfill. When it finishes, the summary line now also lists 'drawdown expectations' — a background calculation that used to wait until someone opened the Evidence page, but now runs automatically as part of the job itself.
- **Action:** Click the "Start" button
- **Point out:** The 'Refreshed:' line growing to include 'drawdown expectations' once the job completes.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-7/step-04.png

### Step 05 — Open Evidence right after the job — instantly  [NEW]

- **Narration:** We open the Evidence ledger, the page that lists every certified trading claim and its historical drawdown expectations. Because the warm-up already ran during the job, this very first view loads just as fast as any later one.
- **Action:** Navigate to /evidence
- **Point out:** The claim cards and their 'Historical drawdown & dry-spell expectations' tables appearing right away, with no long spinner.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-7/step-05.png

### Step 06 — Refresh Evidence — same numbers, still fast

- **Narration:** Reloading the page shows the exact same figures. The only thing that changed this iteration is how quickly the first view loads — never the numbers themselves.
- **Action:** Navigate to /evidence
- **Point out:** Every claim's verdict, hypothesis, and expectations table look identical to before the reload.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-7/step-06.png

### Step 07 — Confirm it in Run History too  [NEW]

- **Narration:** Back on the Data Manager, the job we just ran shows up in Run History with the same 'drawdown expectations' note — the same background pre-computation, visible from every place this page reports on a job.
- **Action:** Navigate to /data
- **Point out:** The Run history row for 2015-06-18 → 2015-06-18, with 'drawdown expectations' in its small gray Refreshed note.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-7/step-07.png

## Full tour (text only)

### Step 02 — Choose a date to refresh

- **Narration:** We ask it to refresh a single day, 2015-06-18, so we can watch a job run from start to finish.
- **Action:** Type "2015-06-18" into the "Job start date" field
- **Point out:** The Start date field now shows the chosen date.

### Step 03 — Set the end of the range

- **Narration:** The end date is the same day, so this is a small, quick job.
- **Action:** Type "2015-06-18" into the "Job end date" field
- **Point out:** The End date field now shows the chosen date.
