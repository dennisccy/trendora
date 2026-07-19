# Demo Script — goal-ops-hardening-iter-1

**Mode:** record
**Date:** 2026-07-19
**Frontend URL:** http://localhost:3255
**Iteration:** 1

## Highlights

### Step 01 — Open the Data Manager

- **Narration:** Start on the Data Manager page, where an operator can grow the dataset on demand and see exactly what every past job did.
- **Action:** Navigate to /data
- **Point out:** Four panels are visible — Dataset coverage, the job submission form, Job progress, and Run history with real past runs already listed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-01.png

### Step 04 — Run the backfill  [NEW]

- **Narration:** Submit the job. Ranges like this used to report success while quietly doing nothing — now the app tells you exactly what happened.
- **Action:** Click the "Start" button
- **Point out:** The status badge, and the plain-English breakdown line underneath it: calendar days, non-trading days, and how many were already covered.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-04.png

### Step 07 — Submit the weekend range  [NEW]

- **Narration:** Submit this zero-trading-day range and see how the app now handles it.
- **Action:** Click the "Start" button
- **Point out:** A distinct grey "no new snapshots" badge, plus a note box explaining every requested day was already covered or wasn't a trading day — never mistaken for a normal successful run.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-07.png

### Step 08 — Reload the page  [NEW]

- **Narration:** Refresh the browser entirely, as if starting a brand-new visit.
- **Action:** Navigate to /data
- **Point out:** Run history is still right there, including the jobs just submitted — nothing resets to a blank slate.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-08.png

### Step 11 — Submit the invalid range

- **Narration:** Try to submit this backwards range. Even though much larger ranges are now accepted, basic checks like date order still hold.
- **Action:** Click the "Start" button
- **Point out:** A red error message explaining the start date must be on or before the end date — the job is never submitted.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-11.png

### Step 12 — Open Scanner Runs  [NEW]

- **Narration:** Head over to the Scanner Runs page, which lists every daily snapshot the system has ever produced.
- **Action:** Navigate to /scanner-runs
- **Point out:** New dates from May 2026 now appear in the list — dates that only exist because that backfill actually ran.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-12.png

### Step 13 — Open the May 4 scanner run  [NEW]

- **Narration:** Open one of those new runs to see the full daily snapshot it created.
- **Action:** Click the "2026-05-04" link
- **Point out:** A regime badge and a populated table of stocks for that day — a real, immutable snapshot, not an empty page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-13.png

### Step 17 — Submit the large range  [NEW]

- **Narration:** Submit this long-span request and watch it actually get accepted.
- **Action:** Click the "Start" button
- **Point out:** The job starts running immediately, and a "chunk N of M" badge appears — the range is processed in manageable pieces instead of being rejected.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-1/step-17.png

## Full tour (text only)

### Step 02 — Enter the start of a May 2026 range

- **Narration:** Type in a start date from May 2026 — a month that used to get silently skipped by backfill requests.
- **Action:** Type "2026-05-02" into the "Start date" field
- **Point out:** The Start date field now holds 2026-05-02.

### Step 03 — Enter the end of the range

- **Narration:** Add an end date to complete the range, covering nearly a full month.
- **Action:** Type "2026-05-29" into the "End date" field
- **Point out:** The End date field now holds 2026-05-29.

### Step 05 — Try a weekend-only start date

- **Narration:** Now try a range that's only a Saturday — no trading days in it at all.
- **Action:** Type "2026-05-02" into the "Start date" field
- **Point out:** The Start date field holds 2026-05-02 again.

### Step 06 — Try a weekend-only end date

- **Narration:** Finish the range with the following Sunday.
- **Action:** Type "2026-05-03" into the "End date" field
- **Point out:** The End date field holds 2026-05-03.

### Step 09 — Enter a start date after the end date

- **Narration:** Type in a start date that's actually later than the end date, to check the app still catches this mistake.
- **Action:** Type "2026-06-01" into the "Start date" field
- **Point out:** The Start date field holds 2026-06-01.

### Step 10 — Enter an end date before the start date

- **Narration:** Add an end date that comes before it.
- **Action:** Type "2026-05-01" into the "End date" field
- **Point out:** The End date field holds 2026-05-01.

### Step 14 — Head back to the Data Manager

- **Narration:** Return to the Data Manager page for one more request.
- **Action:** Navigate to /data
- **Point out:** The same four panels as before.

### Step 15 — Enter a start date over a decade back

- **Narration:** This time, ask for a much bigger range — the kind of request that used to be rejected outright for being too large.
- **Action:** Type "2012-01-01" into the "Start date" field
- **Point out:** The Start date field holds 2012-01-01.

### Step 16 — Enter an end date over a year later

- **Narration:** Set the end date more than 370 days after the start — well past the old limit.
- **Action:** Type "2013-06-01" into the "End date" field
- **Point out:** The End date field holds 2013-06-01.
