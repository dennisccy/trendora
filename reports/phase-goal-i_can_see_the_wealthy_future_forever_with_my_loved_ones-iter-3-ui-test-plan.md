# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 — UI Test Plan

**Phase:** J-46 — Parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill cache, committed advisory benchmark
**Date:** 2026-06-11
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Context

This is a backend-only performance iteration. No frontend files were changed. The UI surfaces below are unchanged in layout, labels, and interaction model. All test cases are **regression**-scoped: they verify that the parallel-engine rewrite leaves the user-facing Data Manager and Stocks pages behaviorally identical to pre-iteration values.

The alpha_vantage `demo` key is the only way to trigger a live rate-limit (amber resumable state) in a browser session. It throttles to a 429 in approximately 3 minutes when multiple symbols are fetched.

---

## Test Cases

---

### UT-01 — Data Manager page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835 (verify: `curl http://localhost:8835/health` returns `200`)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (allow up to 10 seconds for the backend health check to pass)
3. Observe the page heading and main content area

**Expected Result:**
- Page renders without a blank screen, "Checking backend…" infinite spinner, or error message
- The "Data Manager" heading (or equivalent page title) is visible
- A section for starting a new import job is visible on the page
- No 404 error is shown for `_next/static/chunks/main-app.js` in the browser network tab

---

### UT-02 — Stocks list page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Seed data is loaded (NVDA must appear in the list)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load
3. Observe the stock rows in the list

**Expected Result:**
- Page renders without a blank screen or error message
- At least one stock row is visible
- NVDA appears in the list with a non-empty bucket label (one of: A, B, C, D, E)
- No JavaScript error banner is shown on the page

---

### UT-03 — Live progress counter does not exceed total during parallel fetch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- The Data Manager fetch form is accessible
- You have the alpha_vantage `demo` key available (no registration required)
- Note: this test requires approximately 2–3 minutes of active monitoring

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the "Start New Import" form (or equivalent section for starting a fetch job)
3. Select or type `alpha_vantage` as the data source
4. Type `demo` into the API key field
5. Select a batch of at least 3 symbols (e.g., AAPL, MSFT, NVDA) — use the symbols available in the import form
6. Click the "Start" (or "Fetch" or "Import") button to begin the job
7. Observe the live progress display immediately after the job starts — note the "X / Y symbols" counter format
8. Watch the counter continuously for 60 seconds, noting each value displayed
9. Continue watching until either the job completes or the job pauses with a rate-limited state (whichever comes first)

**Expected Result:**
- The progress counter showing fetched symbols (e.g., "2 / 5 symbols") is visible on the job card
- At no point during the job does the displayed fetched-symbol count exceed the declared total (e.g., a counter showing "6 / 5" is a failure)
- The counter increases monotonically (never decreases)
- The bar count (if displayed separately) also never exceeds its declared total

---

### UT-04 — Amber "rate-limited — resumable" state appears on 429 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A fetch job using source=alpha_vantage key=demo has been started (continue from UT-03, or start a new job)
- The demo key is known to trigger a 429 rate limit within approximately 3 minutes of multi-symbol fetching

**Steps:**
1. Navigate to `http://localhost:3835/data` (or remain on the page from UT-03)
2. Confirm a fetch job with source=alpha_vantage and key=demo is running (job card shows a "running" or in-progress state)
3. Wait until the alpha_vantage demo key triggers a rate limit — this typically takes 2–4 minutes
4. Observe the job card status label when the rate limit occurs

**Expected Result:**
- The job card transitions from a running/in-progress state to an amber-colored (or visually distinct) label containing the text "rate-limited" or "resumable" (exact phrasing depends on the UI implementation)
- The job card does NOT show the label "failed" or "error" — a rate-limit must never be displayed as a permanent failure
- A "Resume" button becomes visible on the job card
- No JavaScript crash or blank card appears when the rate limit is reached

---

### UT-05 — Resume button continues job from checkpoint (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A fetch job has reached the amber "rate-limited — resumable" state (complete UT-04 first)
- The "Resume" button is visible on the job card

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the job card in the amber resumable state
3. Note the current "symbols fetched" count shown on the job card (record the exact number)
4. Click the "Resume" button on the amber job card
5. Observe the job card immediately after clicking Resume
6. Wait for the resumed job to either complete or reach another rate-limit pause
7. When the job completes (state shows "ok" or equivalent success label), note the final "symbols fetched" and "bars fetched" summary counts

**Expected Result:**
- Immediately after clicking "Resume", the job card transitions back to a running/in-progress state (no longer shows the amber resumable label)
- The "symbols fetched" counter continues from approximately where it left off — it does not reset to 0
- The final job summary shows a total "bars fetched" count that equals the sum of bars committed before the pause plus bars committed during the resumed run — there are no duplicate bars (the final count is not higher than the true total for the fetched symbols)
- The job card shows a success/ok state when all symbols are processed

---

### UT-06 — Backfill-only job completes with ok summary (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- Seed data is already loaded (at least one symbol with historical bars exists in the database)
- A backfill-only job does not require a network fetch or API key

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the backfill form or section (look for a "Backfill" tab, button, or form distinct from the import/fetch form)
3. Set the date range to a small seed range (e.g., 3–5 dates within the already-loaded seed data period)
4. Select 1–2 symbols that exist in the seed dataset
5. Click the "Run Backfill" (or equivalent) button
6. Observe the job card that appears for the backfill job
7. Wait for the job to complete — backfill jobs on seed data should finish within 60 seconds

**Expected Result:**
- A job card appears showing the backfill job in progress
- The job progresses through a running state and reaches a completion state
- The final job card shows a success/ok status label (not "failed" or "error")
- The job summary shows a symbol count and bar count consistent with the seed data range selected
- No error messages appear on the job card

---

### UT-07 — NVDA scores on /stocks list match known values (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- NVDA is present in the seed dataset
- The page is showing the current/latest snapshot (default view, no historical toggle applied)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the stock list to fully load
3. Locate the row for "NVDA" in the stock list
4. Read and record the following values from the NVDA row:
   - Leadership Score (the first numeric score column)
   - Entry Quality Score (the second numeric score column)
   - Risk Score (the third numeric score column)
   - Bucket label (the A–E letter grade)
5. Write down all four values (you will compare these to the detail page in UT-08)

**Expected Result:**
- The NVDA row is visible and displays three numeric scores and a letter bucket (A, B, C, D, or E)
- All four values are non-empty (no blank cells, no "—" placeholders, no "N/A")
- The scores are plausible numeric values (not 0.000 / 0.000 / 0.000, which would indicate a scoring engine failure)

---

### UT-08 — NVDA scores on detail page match the list page values (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/NVDA`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- NVDA is present in the seed dataset
- UT-07 has been completed and the four NVDA values from `/stocks` have been recorded

**Steps:**
1. Navigate to `http://localhost:3835/stocks/NVDA`
2. Wait for the detail page to fully load
3. Locate the three score values and the bucket label on the detail page
4. Read and record:
   - Leadership Score
   - Entry Quality Score
   - Risk Score
   - Bucket label (A–E)
5. Compare each of the four values to the values recorded in UT-07

**Expected Result:**
- The NVDA detail page loads without errors
- The Leadership Score on this page is identical to the value recorded from `/stocks` in UT-07
- The Entry Quality Score on this page is identical to the value recorded from `/stocks` in UT-07
- The Risk Score on this page is identical to the value recorded from `/stocks` in UT-07
- The Bucket label on this page is identical to the value recorded from `/stocks` in UT-07
- Scores match to the displayed decimal precision (e.g., both show "72.4" not one shows "72.4" and the other "72.40")

---

### UT-09 — Error text on a failed symbol does not contain API key substring (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A fetch job using source=alpha_vantage key=demo has run and at least one symbol has failed (not rate-limited — a non-429 provider error)
- If no failure has occurred naturally, this test can be deferred or noted as "not triggered in this session"

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate any job card that shows at least one failed symbol (a "failed_count" or "errors" indicator)
3. Click the job card or expand the error details to see the error text for the failed symbol
4. Read the displayed error message carefully
5. Check whether the error message contains the substring `apikey=` or `token=` or `key=demo`

**Expected Result:**
- The error message for the failed symbol is visible in the job card or an expanded error section
- The error message does NOT contain the substring `apikey=` or `token=` or `key=demo` (API keys must be scrubbed from all displayed error messages)
- The error message is human-readable text describing the failure reason, not a raw HTTP URL

---

### UT-10 — Dead shell detection guard (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- This check should be performed before any other test in this plan

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Open the browser's developer tools (press F12)
3. Click on the "Network" tab in developer tools
4. Press F5 to refresh the page
5. In the Network tab, filter by "JS" or search for `main-app.js`
6. Observe whether the request to `_next/static/chunks/main-app.js` returns 200 or 404

**Expected Result:**
- The request to `_next/static/chunks/main-app.js` returns HTTP 200
- The page renders with interactive content (not a static "Checking backend…" message that never resolves)
- If the request returns 404: record this test as SKIPPED (not FAIL) with the note "stale .next cache — clear the .next folder and restart the frontend dev server before running UI tests"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | `/data` |
| UT-02 | Stocks list page loads without errors | smoke | P1 | `/stocks` |
| UT-03 | Live progress counter does not exceed total during parallel fetch | regression | P1 | `/data` |
| UT-04 | Amber "rate-limited — resumable" state appears on 429 | regression | P1 | `/data` |
| UT-05 | Resume button continues job from checkpoint | regression | P1 | `/data` |
| UT-06 | Backfill-only job completes with ok summary | regression | P1 | `/data` |
| UT-07 | NVDA scores on /stocks list match known values | regression | P1 | `/stocks` |
| UT-08 | NVDA scores on detail page match the list page values | regression | P1 | `/stocks/NVDA` |
| UT-09 | Error text on a failed symbol does not contain API key substring | regression | P2 | `/data` |
| UT-10 | Dead shell detection guard | regression | P1 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**

### Notes on UT-03 through UT-05

UT-03, UT-04, and UT-05 form a sequential chain: start a job (UT-03), wait for rate-limit (UT-04), then resume (UT-05). They share state. Run them in order without navigating away between steps. Budget 5–10 minutes for the full chain due to the ~3-minute throttle window on the alpha_vantage demo key.

### Notes on UT-09

This test requires a non-rate-limit provider failure, which may not occur naturally in a demo-key session. If no failed symbol appears during the UT-03/UT-04 run, mark UT-09 as SKIPPED with note "no non-429 failure observed in session — cannot verify error scrubbing visually".
