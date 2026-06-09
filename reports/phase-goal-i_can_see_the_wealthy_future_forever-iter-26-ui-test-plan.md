# Phase goal-i_can_see_the_wealthy_future_forever-iter-26 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /data page loads with Unfinished Imports panel visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running (confirm with `curl http://localhost:8000/health` returning 200)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (loading spinner disappears)
3. Observe the page layout

**Expected Result:**
- Page renders without a blank screen, "Checking backend…" spinner, or error overlay
- The heading "Data Manager" (or equivalent) is visible
- The "Unfinished Imports" panel is visible on the page
- No browser console errors related to React hydration or network failures

---

### UT-02 — Resume without key shows inline error and row stays (happy path for the fix)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `ResumeControl` in Unfinished Imports panel

**Preconditions:**
- Frontend and backend are running
- At least one paused/resumable import with `needs_key: true` is present in the Unfinished Imports panel (the row shows a "Resume" button and a session-key input field)
- The session key input field is empty (do not type anything into it)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the Unfinished Imports panel to load and display the resumable import row
3. Locate the resumable import row in the Unfinished Imports panel — it will show a "Resume" button and a key input next to or below the import label
4. Do NOT type anything into the session key input field
5. Click the "Resume" button on that import row

**Expected Result:**
- A red inline error message appears immediately next to or below the Resume button
- The error text reads "Enter the session key for [source label] to resume." (where `[source label]` is the specific provider name, e.g. "Alpha Vantage" or similar)
- The error element has `role="alert"` (verifiable via browser DevTools if needed)
- The import row REMAINS visible in the Unfinished Imports panel — it does NOT disappear or vanish from the list
- No page-level error overlay or toast replaces the inline message
- The page does NOT redirect away from `/data`

---

### UT-03 — Inline error disappears when key is entered (validation — recovery path)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `ResumeControl` in Unfinished Imports panel

**Preconditions:**
- Frontend and backend are running
- A resumable import with `needs_key: true` is present in the Unfinished Imports panel
- The inline error "Enter the session key for … to resume." is currently visible (run UT-02 first)

**Steps:**
1. Navigate to `http://localhost:3835/data` (or stay on it after UT-02)
2. Locate the resumable import row that is showing the red inline error
3. Click inside the session key input field on that row
4. Type any non-empty value (e.g. `test-key-12345`) into the session key input field
5. Observe whether the red inline error message is still visible

**Expected Result:**
- After typing in the key input, the red inline error message is either cleared (disappears) or is no longer shown in a hard-blocked state
- The Resume button remains clickable
- The import row is still present in the Unfinished Imports panel

---

### UT-04 — Row remains after failed resume (regression — row persistence)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — Unfinished Imports panel

**Preconditions:**
- Frontend and backend are running
- A resumable import with `needs_key: true` is present in the Unfinished Imports panel
- Session key input is empty

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Note the exact number of rows in the Unfinished Imports panel before any action (e.g. "1 row")
3. Click the "Resume" button on a needs-key import row without entering a session key
4. Wait 2–3 seconds for the error response to arrive
5. Count the rows in the Unfinished Imports panel again

**Expected Result:**
- The Unfinished Imports panel shows the same number of rows before and after the failed resume (e.g. still "1 row")
- The specific import row that was attempted is still visible with its original label and controls
- The panel does NOT show zero rows, a blank state, or an empty list after the failed resume
- No automatic page reload removed the row

---

### UT-05 — Inline error element has correct ARIA role (error — accessibility)

**Type:** error
**Priority:** P2
**Surface:** `/data` — `ResumeControl` inline error span

**Preconditions:**
- Frontend and backend are running
- A resumable import with `needs_key: true` is present in the Unfinished Imports panel

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Open browser DevTools (F12) and switch to the "Elements" panel
3. Click the "Resume" button on a needs-key import row without entering a session key
4. In the DevTools Elements panel, search for `role="alert"` or look for the inline error element near the Resume button
5. Inspect the inline error element's attributes

**Expected Result:**
- An element with `role="alert"` is present in the DOM immediately after clicking Resume without a key
- The element is visible (not hidden via `display:none` or `visibility:hidden`)
- The element's text content contains the source-specific message (e.g. "Enter the session key for … to resume.")
- The element is inside or adjacent to the Resume control row, not at the top of the page

---

### UT-06 — Prior Resume success path still present (regression — existing resume workflow)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `ResumeControl` in Unfinished Imports panel

**Preconditions:**
- Frontend and backend are running
- A resumable import is present in the Unfinished Imports panel
- If the import requires a key, a valid session key is available

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a resumable import row in the Unfinished Imports panel
3. If the row shows a session key input, type a valid session key into it
4. Click the "Resume" button
5. Watch the import row and the page for a response (allow up to 10 seconds)

**Expected Result:**
- If the resume is accepted by the backend: the row either updates its status, shows a job-in-progress indicator, or clears from the panel (indicating the job was successfully queued/resumed)
- No inline error appears when a valid key (or no key for a `needs_key: false` import) is provided
- The page does NOT crash or show a blank screen

---

### UT-07 — Retry on an existing unfinished import still works (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — Unfinished Imports panel Retry control

**Preconditions:**
- Frontend and backend are running
- At least one unfinished import row with a "Retry" button is visible in the Unfinished Imports panel

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate an unfinished import row that shows a "Retry" button
3. Note the run history shown on that row (e.g. "1 prior attempt")
4. Click the "Retry" button
5. Observe the row state and panel

**Expected Result:**
- Clicking Retry queues a new job attempt (row may show a new status or spinner)
- The panel does NOT flash empty and re-render with rows missing
- No inline error about a missing session key appears (Retry does not require a key re-entry unless it was already needed)
- The prior run history count is preserved or increases — it does NOT reset to zero

---

### UT-08 — Dismiss removes row but does not empty the panel unexpectedly (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — Unfinished Imports panel Dismiss control

**Preconditions:**
- Frontend and backend are running
- At least two unfinished import rows are present in the Unfinished Imports panel (so one can be dismissed and one remains visible)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Note the count of rows in the Unfinished Imports panel (e.g. "2 rows")
3. Locate a row with a "Dismiss" button (or close/X control)
4. Click the "Dismiss" button on that row
5. Observe the panel after dismissal

**Expected Result:**
- The dismissed row disappears from the Unfinished Imports panel
- The remaining row(s) are still visible and unchanged
- The panel does NOT become completely blank unless all rows were dismissed
- No page-level error appears after dismissing a row

---

### UT-09 — /data page has exactly one date selector (regression — J-18 watch risk)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Open browser DevTools (F12) and switch to the Console panel
4. Run the following command in the Console: `document.querySelectorAll('select, input[type="date"]').length`
5. Also inspect the page visually for any date picker, date input, or "as of" selector controls

**Expected Result:**
- The Console command returns a count consistent with exactly one global as-of date selector being present (typically 1, or a small count if other non-date selects are present — the key check is that NO new date input was added by the J-38 UX fix)
- Visually, the page shows exactly one date-picker/as-of control in the header or sidebar — not two
- The J-38 Resume error fix does NOT introduce any new `<select>`, `<input type="date">`, or calendar widget on the page

---

### UT-10 — Error message text is source-specific, not generic (UX — discoverability)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `ResumeControl` inline error

**Preconditions:**
- Frontend and backend are running
- A resumable import with `needs_key: true` is visible in the Unfinished Imports panel
- The source label of that import is known (e.g. "Alpha Vantage", "Tiingo", etc.)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the "Resume" button on the needs-key import row without entering a session key
3. Read the red inline error message that appears

**Expected Result:**
- The inline error message explicitly names the provider/source (e.g. "Enter the session key for Alpha Vantage to resume." — NOT a generic "Key required" or "Error" message)
- The message tells the user exactly what to do ("Enter the session key for …") — it is actionable, not just descriptive
- The message is visible without scrolling, placed near the Resume button it refers to
- The text is readable (not truncated, not hidden behind other elements)

---

### UT-11 — /data page loads and key data sections are visible (smoke — broader)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for all panels to load (no spinner on any panel)
3. Scroll through the entire page

**Expected Result:**
- The following sections are visible on the page (regardless of whether they have data): "Unfinished Imports" (or "Resumable Imports"), a panel showing import job history or current coverage, and a data source selector or "Fetch Data" control
- None of the sections shows a raw JSON error, a React error boundary fallback ("Something went wrong"), or a blank white box where content is expected
- The URL remains `http://localhost:3835/data` throughout

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /data page loads with Unfinished Imports panel visible | smoke | P1 | `/data` |
| UT-02 | Resume without key shows inline error and row stays | happy-path | P1 | `/data` — ResumeControl |
| UT-03 | Inline error disappears when key is entered | validation | P2 | `/data` — ResumeControl |
| UT-04 | Row remains after failed resume | regression | P1 | `/data` — Unfinished Imports panel |
| UT-05 | Inline error element has correct ARIA role | error | P2 | `/data` — ResumeControl |
| UT-06 | Prior Resume success path still present | regression | P1 | `/data` — ResumeControl |
| UT-07 | Retry on existing unfinished import still works | regression | P2 | `/data` — Unfinished Imports panel |
| UT-08 | Dismiss removes row without emptying panel unexpectedly | regression | P2 | `/data` — Unfinished Imports panel |
| UT-09 | /data page has exactly one date selector | regression | P1 | `/data` |
| UT-10 | Error message text is source-specific, not generic | ux | P2 | `/data` — ResumeControl |
| UT-11 | /data page loads and key data sections are visible | smoke | P1 | `/data` |

**P1 tests (must all pass for browser QA verdict to be PASS):** UT-01, UT-02, UT-04, UT-06, UT-09, UT-11
