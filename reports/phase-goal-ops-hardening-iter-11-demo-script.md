# Demo Script — goal-ops-hardening-iter-11

**Mode:** record
**Date:** 2026-07-22
**Frontend URL:** http://localhost:3255
**Iteration:** 11

## Highlights

### Step 01 — Open the home page

- **Narration:** Let's start on Trendora's home page — a small status pill up top tells you at a glance whether today's board of rankings can be trusted.
- **Action:** Navigate to /
- **Point out:** The status pill reads 'Ready' with a thin green banner underneath saying 'GO — today's board is current,' even right after the app restarts.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-11/step-01.png

### Step 02 — Open the Data Manager

- **Narration:** The Data Manager page is where the dataset's day-by-day coverage lives, and where new historical days get pulled in.
- **Action:** Navigate to /data
- **Point out:** The Dataset coverage panel shows real numbers for price history, universe size, and trading days — all computed and stored ahead of time, never recalculated while you wait.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-11/step-02.png

### Step 05 — Start the backfill job

- **Narration:** Clicking Start submits the request. Because this short span falls on a weekend and was already covered by an earlier run, Trendora is upfront about it instead of pretending something new happened.
- **Action:** Click the "Start" button
- **Point out:** The job status reads 'no new snapshots' — a distinct, honest outcome, never dressed up as a fresh success.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-11/step-05.png

### Step 09 — Start the large backfill

- **Narration:** Trendora accepts the whole range at once — no 'range too large' rejection — and works through it so even a very large request finishes cleanly.
- **Action:** Click the "Start" button
- **Point out:** The Data Manager reports the full 412-calendar-day span was accepted and processed, proving there's no hidden per-run size cap.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-11/step-09.png

### Step 10 — Browse the Scanner Runs history

- **Narration:** Every day the scanner has run lives here as a dated, unchanging snapshot.
- **Action:** Navigate to /scanner-runs
- **Point out:** The most recent run appears immediately with its stored results — no loading skeleton, no recomputation needed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-11/step-10.png

### Step 11 — Open a scan from years ago

- **Narration:** Clicking into a much older date opens the exact view the scanner produced back then — instantly, because it was already computed and stored at the time.
- **Action:** Navigate to /scanner-runs/1193
- **Point out:** The page reads 'as of 2021-09-15' and renders its full leaderboard immediately, proving these results are never recalculated on the spot.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-11/step-11.png

## Full tour (text only)

### Step 03 — Enter a backfill start date

- **Narration:** Typing a start date into the backfill form begins a request to fill in a specific day's data.
- **Action:** Type "2026-05-02" into "job-start-date"

### Step 04 — Enter a backfill end date

- **Narration:** The end date completes the range — here it's just the next calendar day.
- **Action:** Type "2026-05-03" into "job-end-date"

### Step 06 — Back to the Data Manager

- **Narration:** Back on the Data Manager page to try a much larger date range.
- **Action:** Navigate to /data

### Step 07 — Enter a much wider date range

- **Narration:** Setting the start date over a year back sets up a much bigger backfill request.
- **Action:** Type "2025-06-01" into "job-start-date"

### Step 08 — Enter the range's end date

- **Narration:** The end date extends the span past 400 days — well beyond what a size-capped system would allow.
- **Action:** Type "2026-07-17" into "job-end-date"
