# Demo Script — goal-ops-hardening-iter-10

**Mode:** record
**Date:** 2026-07-22
**Frontend URL:** http://localhost:3255
**Iteration:** 10

## Highlights

### Step 01 — Open the home page  [NEW]

- **Narration:** Let's start on Trendora's home page — the small status pill at the top of every page is how the app tells you, at a glance, whether today's board can be trusted.
- **Action:** Navigate to /
- **Point out:** The top-bar pill reads 'Ready' in green, with a thin green banner underneath confirming 'GO — today's board is current' — even right after a fresh boot or a backend restart, the app never leaves you guessing about its own health.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-10/step-01.png

### Step 02 — Open the Data Manager

- **Narration:** The Data Manager page is where the dataset's coverage lives, and where new historical days get pulled in.
- **Action:** Navigate to /data
- **Point out:** The Dataset coverage panel shows real numbers for price history, universe size, and trading days — all computed and stored ahead of time, never recalculated on the spot while you wait.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-10/step-02.png

### Step 05 — Start the backfill job

- **Narration:** Clicking Start submits the request. Because this day was already pulled in earlier, Trendora is upfront about it instead of pretending something new happened.
- **Action:** Click the "Start" button
- **Point out:** The job status badge reads 'no new snapshots' in a neutral grey — a distinct, honest outcome, never dressed up as a fresh success.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-10/step-05.png

### Step 06 — Browse the Scanner Runs history

- **Narration:** Every day the scanner has run lives here as a dated, unchanging snapshot.
- **Action:** Navigate to /scanner-runs
- **Point out:** The row for May 15, 2026 shows its market regime and stock counts immediately — no loading skeleton, no refresh needed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-10/step-06.png

### Step 07 — Open a single day's scan

- **Narration:** Clicking into a date opens the exact view the scanner produced that day.
- **Action:** Click the "May 15, 2026" link
- **Point out:** The Scanner Run page reproduces the same regime and counts from the table, with a full leaderboard below it — pulled straight from storage, never recomputed live.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-10/step-07.png

### Step 11 — Start the large backfill

- **Narration:** Trendora accepts the whole range at once — no 'range too large' rejection — and works through it in visible chunks, so you can watch real progress even on a very large job.
- **Action:** Click the "Start" button
- **Point out:** The Job progress panel shows a chunk counter and an advancing progress bar, proving the big request was accepted and is actively running.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-10/step-11.png

## Full tour (text only)

### Step 03 — Enter a backfill start date

- **Narration:** Typing a start date into the backfill form begins a request to fill in a specific day's data.
- **Action:** Type "2026-05-15" into the "Start date" field

### Step 04 — Enter a backfill end date

- **Narration:** The end date completes the range — here it's the very same single day.
- **Action:** Type "2026-05-15" into the "End date" field

### Step 08 — Back to the Data Manager

- **Narration:** Back on the Data Manager page to see how it handles a much larger date range.
- **Action:** Navigate to /data

### Step 09 — Enter a much wider date range

- **Narration:** Setting the start date over a year back sets up a much bigger backfill request.
- **Action:** Type "2025-06-01" into the "Start date" field

### Step 10 — Enter the range's end date

- **Narration:** The end date extends the span past 400 days — well beyond what a size-capped system would allow.
- **Action:** Type "2026-07-17" into the "End date" field
