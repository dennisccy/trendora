# Demo Script — goal-ops-hardening-iter-47

**Mode:** record
**Date:** 2026-08-04
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Evidence page

- **Narration:** The Evidence page shows a dashboard of certified trading claims. Let's check it loads quickly and shows no stale-data warnings.
- **Action:** Navigate to /evidence
- **Point out:** The 'Evidence' heading and claim cards should appear within a couple seconds with no 'Refreshing' badge visible.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-01.png

### Step 02 — Verify idle Evidence page shows real numbers with no 'Refreshing' badge

- **Narration:** When the backend is idle and data is fresh, every claim's table shows real median, p90, and sample numbers. No claim should show the amber 'Refreshing' badge yet.
- **Action:** Click "[data-testid='evidence-claim-row']"
- **Point out:** Look for tables with percentages and numbers like 'p90' and 'n=…' — no amber 'Refreshing' badges alongside the heading.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-02.png

### Step 03 — Open the Data Manager to start a backfill

- **Narration:** To trigger the 'Refreshing' badge on Evidence, we'll start a backfill job. Let's open the Data Manager page where we can schedule a new date range.
- **Action:** Navigate to /data
- **Point out:** The Data Manager should show the 'Dataset coverage' panel with the current 'Price history' date range.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-03.png

### Step 05 — Fill in a new date range starting the day after the latest bar

- **Narration:** To trigger the 'Refreshing' badge, we need to backfill a date that is NOT yet in the database — the day after the current end date. We'll fill the Start and End date fields with the same new date.
- **Action:** Type "2026-08-02" into "job-start-date"
- **Point out:** The 'Start date' and 'End date' fields should be populated with the new date in yyyy-MM-dd format.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-05.png

### Step 07 — Click Start to begin the backfill job

- **Narration:** Now we'll kick off the backfill. This will insert new data, which will trigger the Evidence page's background catch-up and cause the 'Refreshing' badge to appear.
- **Action:** Click the "Start" button
- **Point out:** A job progress panel should appear or update, showing the job as 'running' with a spinner icon.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-07.png

### Step 08 — Return to the Evidence page to observe the 'Refreshing' badge  [NEW]

- **Narration:** Now that a backfill is running, let's check the Evidence page. We should see an amber 'Refreshing' badge appear next to at least one claim's 'Historical drawdown & dry-spell expectations' heading — along with a sentence explaining that a newer version is being computed in the background.
- **Action:** Navigate to /evidence
- **Point out:** Look for the small amber 'Refreshing' badge next to the heading. The table should still show real numbers, never a blank or loading state. The page should load quickly despite the background job running.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-08.png

### Step 09 — Verify the home page stays responsive while the backfill runs

- **Narration:** A key improvement this iteration is that the Evidence page's background computation no longer blocks the rest of the app. Let's check that the home page loads quickly even while a catch-up is happening.
- **Action:** Navigate to /
- **Point out:** The home page should load and show 'Ready' — no hang, no freeze, no errors.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-09.png

### Step 10 — Observe the honest 'Refreshing' badge disclosure  [NEW]

- **Narration:** The new badge not only tells users something is catching up — it also explains honestly that the table below is the last complete version, not a fabricated or partial one. This is a key UX improvement: no silent stale data.
- **Action:** Navigate to /evidence
- **Point out:** When you navigate back to /evidence, read the sentence under the 'Refreshing' badge that explains: 'A newer version is computing in the background after a recent data update — the table below is the last complete version, not a partial or fabricated one.'
- **Screenshot:** reports/demo/goal-ops-hardening-iter-47/step-10.png

## Full tour (text only)

### Step 04 — Read the current Price history end date

- **Narration:** We need to note the latest date already ingested (the end date of the 'Price history' range). We'll backfill one day after that to trigger the new-data catch-up.
- **Action:** Click the "Price history" field
- **Point out:** In the 'Dataset coverage' panel, find the 'Price history' row — read the second date, which is the latest bar already in the database.

### Step 06 — Fill the End date field with the same new date

- **Narration:** Both Start and End date need the same value to backfill just one day of new data.
- **Action:** Type "2026-08-02" into "job-end-date"
- **Point out:** The End date field should match the Start date we just entered.
