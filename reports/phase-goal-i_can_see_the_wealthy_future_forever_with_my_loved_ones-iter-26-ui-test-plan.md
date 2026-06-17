# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26
**Date:** 2026-06-17
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
- Backend is running at http://localhost:8835
- No particular job state required

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (spinner disappears or content is visible)
3. Look for the Data Manager heading or title at the top of the page
4. Look for the Unfinished-imports section on the page

**Expected Result:**
- The page renders without a blank screen, "Error" banner, or crash message
- A heading containing "Data" or "Data Manager" is visible
- The Unfinished-imports section is present (even if it shows "No unfinished imports" when no paused jobs exist)
- No red error overlay or full-page error boundary is visible

---

### UT-02 — Paused Expand-universe job shows honest message in Unfinished-imports panel (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Unfinished-imports panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A paused-resumable Expand-universe job exists in the database (triggered by a Yahoo auth/rate-limit failure). If no such job exists, ask a developer to seed one via the test helper or trigger an Expand job against Yahoo with the network blocked.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the section labeled "Unfinished imports" or "Unfinished-imports" on the page
3. Find the row or card for the paused Expand-universe job
4. Read the status indicator on that job row (look for an amber badge, "Resumable" label, or similar visual state marker)
5. Read the message text displayed on the job card (look for any text describing why the job paused)
6. Confirm a "Resume" button or "Resume" link is present on the job row

**Expected Result:**
- The Unfinished-imports panel is visible and contains the paused Expand-universe job row
- The job row displays an amber or "Resumable" state indicator (NOT a green "Completed" badge and NOT a red "Failed" badge)
- The job message text contains words like "auth failed", "market-cap provider", or "Resume to retry" — it does NOT read "0 passers, 548 omitted" or show a silent success summary
- A "Resume" button or "Resume" link is visible and appears clickable on the job row
- The job card does NOT display a raw Yahoo URL with query parameters or a crumb/token string

---

### UT-03 — Resume button on paused Expand job transitions job to active state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Unfinished-imports panel / Resume affordance

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A paused-resumable Expand-universe job is visible in the Unfinished-imports panel (see UT-02 preconditions)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the paused Expand-universe job row in the Unfinished-imports section
3. Note the current status shown on the job row (e.g., "Resumable" or amber badge)
4. Click the "Resume" button or "Resume" link on the paused job row
5. Wait up to 10 seconds for the UI to respond
6. Observe the job card or Unfinished-imports panel for any state change

**Expected Result:**
- After clicking "Resume", the UI either shows the job transitioning out of the "Resumable" state (e.g., the status badge changes to "Running", "In progress", or similar) OR the Unfinished-imports entry disappears (indicating the job was handed off to the active jobs queue)
- The page does NOT crash or display a full-page error after clicking Resume
- The browser does NOT navigate away from `/data` unless the app is designed to do so
- If the resume results in an error, the error message shown is human-readable (NOT a raw stack trace or an HTTP status code alone)

---

### UT-04 — Job card message does not expose Yahoo crumb, token, or raw URL (error / security)

**Type:** error
**Priority:** P1
**Surface:** `/data` — job card message field

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A paused-resumable Expand-universe job is visible in the Unfinished-imports panel

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Find the paused Expand-universe job row in the Unfinished-imports section
3. Read the full text of the message or description shown on the job card
4. Look carefully for any of the following in the visible message text:
   - A URL containing `?crumb=` or `?token=` or `&crumb=` or `&apikey=`
   - A long alphanumeric string (32+ characters) that looks like a session token
   - The domain `finance.yahoo.com` followed by query parameters
5. Expand or open any "details" or "view more" section of the job card (if one exists) and repeat the check

**Expected Result:**
- The job card message is human-readable plain text such as "market-cap provider auth failed — Resume to retry" or similar
- No raw URL with query parameters (e.g., `https://query2.finance.yahoo.com/v7/finance/quote?symbols=...&crumb=ABC123`) is visible anywhere in the UI
- No crumb token (a 20–40 character alphanumeric string) is visible in the displayed message
- No bearer token, cookie value, or API key is visible in the message text

---

### UT-05 — Unfinished-imports panel shows nothing unusual when no paused jobs exist (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — Unfinished-imports panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- No paused-resumable jobs currently exist in the database (all jobs are completed or the database is freshly seeded)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the Unfinished-imports section on the page
3. Observe what the section displays when it is empty

**Expected Result:**
- The Unfinished-imports section either:
  - Is not visible (hidden when no unfinished imports exist), OR
  - Shows an empty state message like "No unfinished imports" or similar placeholder text
- The section does NOT show a paused job that does not exist
- The rest of the Data Manager page (other sections, navigation) renders correctly

---

### UT-06 — Other Data Manager sections are unaffected by this iteration's changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- The seed data with 159 committed price symbols is intact

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Look for the Stocks universe section or "Committed symbols" / "Price seed" section on the page
3. Verify the count or list of committed symbols is present and non-zero
4. Look for the Data Sources section or import sources list
5. Verify at least one import source (e.g., Yahoo Finance or Tiingo) is listed
6. Navigate to `http://localhost:3835/stocks` (Stocks page)
7. Verify the Stocks page loads and shows at least some stock data

**Expected Result:**
- The Stocks universe / committed symbols count on `/data` reflects the seeded price history (should show 159 symbols or a non-zero number)
- The import sources list is visible and contains at least one source
- The Stocks page at `/stocks` loads successfully and is not blank
- None of these sections show errors introduced by the iter-26 backend changes

---

### UT-07 — Global as-of date switcher operates independently of the Expand job form (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — global as-of switcher vs. job form date

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the global as-of date switcher in the top navigation bar or header
3. Note the current as-of date displayed
4. Click the as-of date switcher and navigate to a different date (e.g., use the back arrow to go to a prior date)
5. Observe the Data Manager page after changing the as-of date
6. Look at any job date inputs or date-range fields in the Expand or import forms on the page

**Expected Result:**
- After changing the global as-of date, the page URL updates to include `?asof=<new-date>` or the as-of indicator in the header updates to the new date
- The Expand job form date input (if visible) does NOT change to match the global as-of date — they remain independent controls
- The Unfinished-imports panel still displays correctly after the date change

---

### UT-08 — Paused Expand job row is discoverable without developer knowledge (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — Unfinished-imports panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A paused-resumable Expand-universe job exists in the Unfinished-imports panel

**Steps:**
1. Navigate to `http://localhost:3835/data` without any prior knowledge of where paused jobs appear
2. Scan the page from top to bottom
3. Identify the Unfinished-imports section by its label alone
4. Read the job row without hovering or clicking anything
5. Determine from the visible text alone what the operator should do next (e.g., click Resume)

**Expected Result:**
- The Unfinished-imports section heading is clearly labeled (operator can find it without scrolling past unrelated content)
- The paused job's status is visually distinct from a completed job (different color badge or label)
- The "Resume" action is labeled as "Resume" (or a clearly equivalent label like "Retry") — it is NOT unlabeled, icon-only, or hidden behind a dropdown with no hint
- An operator who has never seen this page before would understand within 30 seconds that there is a paused job requiring their attention and that clicking Resume will restart it

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | `/data` |
| UT-02 | Paused Expand job shows honest message in Unfinished-imports panel | happy-path | P1 | `/data` |
| UT-03 | Resume button transitions paused Expand job to active state | happy-path | P1 | `/data` |
| UT-04 | Job card message does not expose Yahoo crumb or raw URL | error | P1 | `/data` |
| UT-05 | Unfinished-imports panel shows nothing unusual when no paused jobs exist | regression | P1 | `/data` |
| UT-06 | Other Data Manager sections unaffected by iter-26 changes | regression | P1 | `/data`, `/stocks` |
| UT-07 | Global as-of date switcher is independent of Expand job form date | regression | P2 | `/data` |
| UT-08 | Paused Expand job row is discoverable without developer knowledge | ux | P2 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**
