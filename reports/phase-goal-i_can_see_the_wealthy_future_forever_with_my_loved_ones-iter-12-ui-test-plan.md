# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Date:** 2026-06-13
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Data Manager page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running (verify with `curl http://localhost:8000/health` or equivalent)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (up to 5 seconds)

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Data Manager" (or equivalent page title) is visible
- The "Unfinished Imports" section is visible (even if empty)
- The "Run History" section is visible (even if empty)
- No red error banners are displayed

---

### UT-02 — Live job card shows current-activity line during an active job (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` (current-activity line)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running with at least one symbol and a short date range available to import (e.g., AAPL over 1 month)
- No job is currently running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the "Import Data" or "Start Job" form on the page
3. Select a symbol (e.g., "AAPL") and a date range of approximately 1 month
4. Click the "Start" (or "Import" / "Submit") button to dispatch the job
5. Observe the live job card that appears in the page
6. Watch the area below the progress bar within the live job card

**Expected Result:**
- A live job card appears on the page showing job progress
- Below the progress bar, a current-activity line appears reading something like "fetching AAPL (1/1)" or "scanning 2024-06-01 (12/22)" — the exact text updates as the job progresses
- The text changes at least once during the job run, confirming it is live and not static

---

### UT-03 — Live job card heartbeat updates every second and turns amber when stalled (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` (heartbeat)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A job is actively running (use a multi-symbol, multi-date job for best visibility)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Start a job (select any symbol and date range, click the submit button)
3. Observe the live job card while the job runs
4. Locate the "updated Ns ago" heartbeat line near the bottom of the live job card
5. Watch the counter for 5 seconds

**Expected Result:**
- A heartbeat line reading "updated 0s ago" or "updated 1s ago" (or similar) is visible in the live job card
- The number in the heartbeat line increments by approximately 1 each second
- The text remains in the default (non-amber) color while the job is actively making progress

---

### UT-04 — Heartbeat turns amber and says "possibly stalled" when job stops advancing (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` (heartbeat stale state)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A job is available that can be made to stall (or a job that naturally has long gaps between progress updates)
- The stale threshold is set to the default 20 seconds in `config.yaml`

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Start a job and observe the live job card's heartbeat line
3. Wait for approximately 25 seconds without the job advancing (or artificially create a stall if possible)
4. Observe the heartbeat line's color and text

**Expected Result:**
- After ~20 seconds without a progress update, the heartbeat line text changes to include "possibly stalled" (or equivalent warning text)
- The heartbeat line text color changes to amber (orange/yellow warning color)
- The color and text revert to normal if the job resumes advancing

---

### UT-05 — Symbols counter never exceeds its total in the live job card (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` (symbols counter)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A multi-symbol import job can be dispatched (at least 2 symbols over a multi-month range that creates multiple fetch windows)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Start a job with at least 2 symbols and a date range of 3+ months (which will create multiple fetch windows per symbol)
3. Watch the live job card during the fetch stage
4. Read the symbols counter line (e.g., "12 / 159 symbols" or "Symbols: 2/5")

**Expected Result:**
- The left number in the symbols counter (completed count) never exceeds the right number (total symbols)
- For example, if the total is 5, the counter shows values like "0/5", "1/5", "2/5", "3/5", "4/5", "5/5" — never "6/5" or "10/5"
- The counter reaches exactly the total when all symbols finish

---

### UT-06 — Run History shows a "running" row immediately when a job is dispatched (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RunHistoryPanel` (running status)

**Preconditions:**
- Frontend is running at http://localhost:3835
- No job is currently running
- The Run History section is visible on the page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down to the "Run History" section and note the current number of rows
3. Start a new job (select any symbol and date range, click the submit button)
4. Within 2 seconds of clicking submit, scroll back to the Run History section

**Expected Result:**
- A new row appears in the Run History table with status "running"
- The row displays the job's kind (e.g., "both"), date range, and source
- An inline spinner icon is visible next to the "running" status text
- The row appears before the job finishes — it does not wait for job completion

---

### UT-07 — Run History shows "interrupted" row after backend restart with an abandoned job (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RunHistoryPanel` (interrupted status)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A job was started and is currently showing as "running" in Run History
- The backend process can be restarted

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Confirm a job is visible in Run History with status "running" and an inline spinner
3. Restart the backend process (kill and restart the backend server)
4. Navigate to `http://localhost:3835/data` again (or refresh the page after backend restarts)
5. Scroll to the Run History section

**Expected Result:**
- The previously-"running" job row now shows status "interrupted"
- The status styling is neutral/muted (not red/error styling)
- The row is still present — it was not deleted
- No spinner is shown next to "interrupted"

---

### UT-08 — Unfinished Imports shows "failed at backfill" entry with amber badge and Resume button (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `UnfinishedImportsPanel` (failed_backfill checkpoint)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A job exists that completed the fetch stage but failed during backfill (a `failed_backfill` checkpoint must exist in the database; this may require a seeded state or a prior run that failed at backfill)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Unfinished Imports" section
3. Locate the entry for the job that failed during backfill

**Expected Result:**
- An entry is visible in the Unfinished Imports section for the failed job
- The status badge reads "failed at backfill" and is displayed in amber (orange/yellow) color
- The description text mentions "Resumable from the backfill stage (the fetch is skipped — zero provider calls)" or equivalent
- A "Resume" button is visible and enabled (not greyed out) next to the entry

---

### UT-09 — Resume button on a failed_backfill entry starts a new job that skips fetch (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `UnfinishedImportsPanel` (Resume button action)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A `failed_backfill` entry is visible in the Unfinished Imports section (from UT-08 preconditions)
- No job is currently running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Unfinished Imports" section
3. Locate the entry with the amber "failed at backfill" status badge
4. Click the "Resume" button on that entry
5. Observe the live job card and Run History table

**Expected Result:**
- Clicking "Resume" triggers a new job that appears in the live job card
- The live job card shows the job progressing through the backfill stage (not the fetch stage) — the current-activity line should say something like "scanning YYYY-MM-DD (N/M)" rather than a fetch-stage message
- A new "running" row appears in Run History for the resumed job
- The job completes with status "ok" or "partial" (not "failed")

---

### UT-10 — Partial job in Run History shows per-date failure detail (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RunHistoryPanel` (partial job failure detail block)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A job exists that completed with "partial" status (at least one date failed during backfill, while others succeeded)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Run History" section
3. Locate a row with status "partial"
4. Click on the row to expand it or look for a failure detail block that is directly visible below the row

**Expected Result:**
- A "Failed dates" or "Per-date errors" block is visible (either inline or on expand) for the partial job
- At least one failed date is listed, showing the specific date (e.g., "2024-02-15") and the associated error message (non-empty text)
- The block also notes that the remaining dates completed successfully (e.g., "remaining dates completed" or equivalent)

---

### UT-11 — Stage Timings section shows server-computed speedup factor without JS error (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `StageTimings` (speedup factor display)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A parallel backfill job has completed (status "ok" or "partial")
- Browser developer tools console is accessible (F12)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Open the browser developer tools (press F12) and switch to the "Console" tab
3. Scroll to the Run History section and find a completed backfill job
4. Locate the Stage Timings section for that job
5. Read the speedup factor text displayed

**Expected Result:**
- The Stage Timings section shows a speedup figure formatted as a number followed by "x faster" (e.g., "3.2x faster")
- The speedup value is a positive, reasonable number (e.g., between 1.0 and 10.0)
- The browser console shows no JavaScript errors related to the speedup calculation (no "NaN", "Infinity", or "TypeError" related to division)

---

### UT-12 — Config-driven poll interval: live job card updates approximately every second (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `JobProgressPanel` (poll interval behavior)

**Preconditions:**
- Frontend is running at http://localhost:3835
- A job is actively running
- `config.yaml` has `data_manager.job_progress.poll_interval_seconds` set to 1 (the default)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Start a job (select any symbol and date range, click the submit button)
3. Open browser developer tools (F12), switch to the "Network" tab, and filter by XHR/Fetch requests
4. Watch the network requests to the job-status endpoint while the job card is visible

**Expected Result:**
- Network requests to the job-status API endpoint (e.g., `/api/data/jobs/{id}`) appear approximately every 1 second
- The interval matches the configured `poll_interval_seconds` value (1 second by default)
- The live job card content visually updates at approximately the same cadence

---

### UT-13 — Run History existing entries still display correctly after this phase (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `RunHistoryPanel` (existing ok/failed statuses)

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one job with status "ok" exists in Run History from a prior run

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Run History" section
3. Locate a row with status "ok"
4. Verify the row displays the expected information

**Expected Result:**
- Rows with status "ok" show green or positive-color status styling (not amber, not red)
- The job's kind, date range, and source are still visible in the row
- No row is missing or blank compared to what was visible before this phase

---

### UT-14 — New status tokens in Run History are visually distinct from each other (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `RunHistoryPanel` (status badge styling)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Run History contains rows with at least two different statuses (e.g., "ok" and "running", or "partial" and "interrupted")

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Run History" section
3. Observe the status badges across different rows

**Expected Result:**
- Status "running" displays with an inline spinner animation
- Status "interrupted" displays with a neutral/muted color (not red, not green)
- Status "resumable" displays with an amber color (matching the Unfinished Imports amber style)
- Status "ok" displays with a green or positive color
- Status "partial" displays with an amber or warning color
- Status "failed" displays with a red or error color
- All statuses are visually distinguishable from each other at a glance

---

### UT-15 — Unfinished Imports section is discoverable without scrolling (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data` — `UnfinishedImportsPanel` (discoverability)

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one unfinished import entry exists (from a prior failed job)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Without scrolling, observe the visible page area
3. If "Unfinished Imports" is not immediately visible, scroll only once (one page-down key press)

**Expected Result:**
- The "Unfinished Imports" section heading is visible within the first or second screen of the `/data` page
- The section is not buried below a long list of unrelated content
- A user seeing the page for the first time would understand that this section lists jobs that need attention

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | `/data` |
| UT-02 | Live job card shows current-activity line during an active job | happy-path | P1 | `/data` — `JobProgressPanel` |
| UT-03 | Live job card heartbeat updates every second | happy-path | P1 | `/data` — `JobProgressPanel` |
| UT-04 | Heartbeat turns amber and says "possibly stalled" when job stops advancing | happy-path | P1 | `/data` — `JobProgressPanel` |
| UT-05 | Symbols counter never exceeds its total in the live job card | regression | P1 | `/data` — `JobProgressPanel` |
| UT-06 | Run History shows a "running" row immediately when a job is dispatched | happy-path | P1 | `/data` — `RunHistoryPanel` |
| UT-07 | Run History shows "interrupted" row after backend restart | happy-path | P1 | `/data` — `RunHistoryPanel` |
| UT-08 | Unfinished Imports shows "failed at backfill" entry with amber badge and Resume button | happy-path | P1 | `/data` — `UnfinishedImportsPanel` |
| UT-09 | Resume button on a failed_backfill entry starts a new job that skips fetch | happy-path | P1 | `/data` — `UnfinishedImportsPanel` |
| UT-10 | Partial job in Run History shows per-date failure detail | happy-path | P1 | `/data` — `RunHistoryPanel` |
| UT-11 | Stage Timings section shows server-computed speedup factor without JS error | regression | P2 | `/data` — `StageTimings` |
| UT-12 | Config-driven poll interval: live job card updates approximately every second | regression | P2 | `/data` — `JobProgressPanel` |
| UT-13 | Run History existing entries still display correctly after this phase | regression | P1 | `/data` — `RunHistoryPanel` |
| UT-14 | New status tokens in Run History are visually distinct from each other | ux | P2 | `/data` — `RunHistoryPanel` |
| UT-15 | Unfinished Imports section is discoverable without scrolling | ux | P3 | `/data` — `UnfinishedImportsPanel` |

**P1 tests must all pass for browser QA verdict to be PASS.**
