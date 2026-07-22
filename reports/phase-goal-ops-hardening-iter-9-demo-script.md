# Demo Script — goal-ops-hardening-iter-9

**Mode:** record
**Date:** 2026-07-22
**Frontend URL:** http://localhost:3255
**Iteration:** 9

## Highlights

### Step 01 — Open the home page

- **Narration:** Let's start on Trendora's home page, where the Market Phase & Severity card gives an at-a-glance read on today's market regime.
- **Action:** Navigate to /
- **Point out:** The Market Phase & Severity card renders a live severity score and regime label the moment the page loads — never a blank or 'unavailable' state.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-01.png

### Step 02 — Open the Data Manager

- **Narration:** Next, the Data Manager page — this is where the dataset's coverage is tracked and where new historical days get backfilled into the scanner.
- **Action:** Navigate to /data
- **Point out:** The Dataset coverage panel shows real numbers for price history, universe size, trading days, and any backfill gaps — all computed and cached ahead of time, not recomputed on the spot.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-02.png

### Step 05 — Start the backfill job

- **Narration:** Clicking Start submits the job. Because this particular day was already covered by an earlier run, Trendora immediately and honestly reports there was no new work to do — a distinct, clearly-labeled outcome rather than a misleading 'success'.
- **Action:** Click the "Start" button
- **Point out:** The job status badge reads 'no new snapshots' in a neutral grey — visually different from the green badge used for a truly new backfill.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-05.png

### Step 06 — Browse the Scanner Runs history

- **Narration:** Every day the scanner has run lives here as an immutable, dated snapshot — including the day we just looked up.
- **Action:** Navigate to /scanner-runs
- **Point out:** The row for May 15, 2026 shows its regime, actionable count, and stock count immediately — no loading skeleton, no refresh needed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-06.png

### Step 07 — Open a single day's scan

- **Narration:** Clicking into a date opens the exact, unchanging view the scanner produced that day.
- **Action:** Click the "May 15, 2026" link
- **Point out:** The Scanner Run page reproduces the same regime and counts seen in the table, with a full leaderboard of stocks below it — pulled straight from the stored snapshot, not recomputed live.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-07.png

### Step 11 — See the inline validation

- **Narration:** Moving focus away from the field reveals a clear, specific error — and the Start button stays disabled until the date is fixed.
- **Action:** Click "Data Manager"
- **Point out:** A red inline message reads 'Enter a valid date as yyyy-MM-dd', and no job is ever submitted for an invalid date.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-11.png

### Step 14 — Start the large backfill

- **Narration:** Trendora accepts the whole range at once — no 'range too large' rejection — and processes it in visible chunks, so you can watch real progress on even a very large job.
- **Action:** Click the "Start" button
- **Point out:** The Job progress panel shows a chunk counter and an advancing progress bar, proving the big request was accepted and is actively executing.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-9/step-14.png

## Full tour (text only)

### Step 03 — Enter a backfill start date

- **Narration:** Typing a start date into the backfill form is the first step in growing the dataset for a specific day.
- **Action:** Type "2026-05-15" into the "Start date" field

### Step 04 — Enter a backfill end date

- **Narration:** The end date completes the range — here it's the very same single day.
- **Action:** Type "2026-05-15" into the "End date" field

### Step 08 — Return to the run list

- **Narration:** The 'All runs' link takes you straight back to the full history.
- **Action:** Click the "All runs" link

### Step 09 — Back to the Data Manager

- **Narration:** Back on the Data Manager page to see the form's validation and how it handles a much larger date range.
- **Action:** Navigate to /data

### Step 10 — Try an invalid date

- **Narration:** Typing an impossible calendar date shows how the form catches mistakes before they ever reach the server.
- **Action:** Type "2026-13-40" into the "Start date" field

### Step 12 — Enter a much wider date range

- **Narration:** Fixing the start date to a real, far earlier day sets up a much bigger backfill — over a year of history in one request.
- **Action:** Type "2025-06-01" into the "Start date" field

### Step 13 — Enter the range's end date

- **Narration:** The end date extends the span past 370 days — well beyond what older, capped systems would allow.
- **Action:** Type "2026-07-17" into the "End date" field
