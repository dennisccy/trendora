# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Date:** 2026-06-14
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
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (all panels should be visible)

**Expected Result:**
- Page renders without a blank screen or error overlay
- A panel labeled "Remove imported data" (or similar) is visible on the page
- No "Checking backend..." spinner remains after load completes

---

### UT-02 — Remove Data panel shows only two date fields and no symbols input (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down to locate the panel labeled "Remove imported data"
3. Count the visible input fields in that panel

**Expected Result:**
- Exactly two date input fields are visible: one labeled "From" and one labeled "To"
- No text input field labeled "Symbols", "Symbol list", or any variant of it is present anywhere in the panel
- The panel is compact: only the two date fields and the "Preview removal" button are visible

---

### UT-03 — Preview removal button is disabled with no dates entered (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The "From" and "To" fields in the Remove panel are empty

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Confirm both the "From" and "To" date fields are empty (clear them if pre-filled)
4. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button is visually disabled (grayed out or cursor shows "not-allowed")
- Clicking the button has no effect — no modal appears, no API call is made

---

### UT-04 — Preview removal button remains disabled with only the From date filled (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Click the "From" date field and type `2025-02-01`
4. Leave the "To" field empty
5. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button remains disabled after entering only the "From" date
- No modal or confirmation dialog appears
- The "To" field is visually empty (unfilled)

---

### UT-05 — Preview removal button remains disabled with only the To date filled (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Leave the "From" field empty
4. Click the "To" date field and type `2025-02-28`
5. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button remains disabled
- No modal or confirmation dialog appears

---

### UT-06 — Preview removal button remains disabled when an invalid date is entered (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Type `2024-13-01` in the "From" field (month 13 is invalid)
4. Type `2025-02-28` in the "To" field (valid)
5. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button remains disabled because the "From" date is not a valid ISO date
- No modal or confirmation dialog appears

---

### UT-07 — Preview removal button becomes enabled when both dates are valid (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Click the "From" date field and type `2025-02-01`
4. Click the "To" date field and type `2025-02-28`
5. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button becomes enabled (no longer grayed out) immediately after both dates are filled
- No page reload is required for the button state to update

---

### UT-08 — Preview removal button re-disables when a date is cleared (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Both "From" and "To" fields have valid ISO dates so the "Preview removal" button is enabled

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Fill in "From" with `2025-02-01` and "To" with `2025-02-28` — confirm button is enabled
4. Clear the "To" field (select all and delete)
5. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button returns to a disabled state immediately after clearing the "To" field
- No modal or confirmation dialog appears

---

### UT-09 — Confirm modal shows counts only (no symbol lists) (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RemoveConfirmModal`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running with user-added bars available for a small date range (e.g., at least some data exists in the system beyond the committed seed)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Click the "From" date field and type `2025-02-01`
4. Click the "To" date field and type `2025-02-28`
5. Click the now-enabled "Preview removal" button
6. Wait for the confirmation modal to appear
7. Inspect the modal body content

**Expected Result:**
- The confirmation modal appears
- The modal body shows numeric count summaries: a bar count (e.g., "123 bars"), an affected symbol count (e.g., "5 symbols"), a protected-seed bar count, and a cascade snapshot count — all as plain numbers with labels
- No list of individual symbol names (e.g., "AAPL, MSFT, GOOG") appears in the modal body
- No per-symbol breakdown table appears
- The date range (`2025-02-01` to `2025-02-28`) is stated in the modal header or body

---

### UT-10 — Confirm (Remove) button is visible in the modal footer without scrolling (ux)

**Type:** ux
**Priority:** P1
**Surface:** `/data` — `RemoveConfirmModal`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A confirmation modal is open (follow steps 1–6 of UT-09)

**Steps:**
1. Navigate to `http://localhost:3835/data`, open the removal confirmation modal following the steps in UT-09
2. Without scrolling within the modal, look at the visible area of the modal
3. Locate the "Remove" (or "Confirm") button and the "Cancel" button

**Expected Result:**
- Both the "Cancel" button and the "Remove" (or "Confirm") button are visible in the footer area of the modal without any scrolling
- The footer row containing these buttons appears below or separate from the scrollable body area of the modal

---

### UT-11 — Modal body is scrollable while footer remains fixed (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `RemoveConfirmModal`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A confirmation modal is open (follow steps 1–6 of UT-09)
- The modal body content is present

**Steps:**
1. Open the removal confirmation modal by following the steps in UT-09
2. Attempt to scroll within the modal body area (scroll the inner content, not the page behind the modal)
3. While scrolling the body, observe the position of the "Remove" and "Cancel" buttons in the footer

**Expected Result:**
- If the body content exceeds the visible height, a scrollbar appears inside the modal body
- The footer row (containing the "Cancel" and "Remove" buttons) does not move — it remains anchored at the bottom of the modal regardless of scrolling the body
- The modal itself does not overflow the viewport

---

### UT-12 — Clicking Cancel closes the modal without removing data (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `RemoveConfirmModal`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The confirmation modal is open

**Steps:**
1. Open the removal confirmation modal by following steps 1–6 of UT-09
2. Click the "Cancel" button in the modal footer
3. Observe the state of the page

**Expected Result:**
- The modal closes immediately
- The page returns to the `/data` view with the Remove panel visible
- No data removal job is started (no job card appears, no status update for a removal job)
- The "From" and "To" date fields in the Remove panel still contain the previously entered values (or may be cleared — either is acceptable, but the key requirement is that no removal was triggered)

---

### UT-13 — Backfill job card shows completed or partial status (not crash) for a multi-date range (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Backfill job card

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running
- The Data Manager panel on `/data` shows a mechanism to start a backfill job (e.g., "Fetch data" or "Backfill" action with a date range)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the Data Manager or "Fetch data" panel
3. Set a date range spanning multiple months (e.g., From `2025-01-01` to `2025-03-31`) and select a backfill action
4. Submit or start the backfill job
5. Observe the job card that appears in the active jobs area
6. Wait for the job card to reach a terminal status (this may take several minutes for a real date range; use a narrow range like 2 weeks if the environment has limited data)

**Expected Result:**
- A job card appears in the active-jobs area after submission
- The job card's status progresses from "running" or "in-progress" to a terminal state of either "complete", "ok", or "partial"
- The job card does NOT show a terminal status of "error", "crashed", or "failed" at the whole-job level
- If any individual day failed, the job card's error section may list that date, but the overall job status is "partial" or "complete" — not an unrecoverable crash

---

### UT-14 — Navigating away and back does not break the Remove panel state (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Remove imported data" panel
3. Fill in "From" with `2025-02-01` and "To" with `2025-02-15`
4. Navigate away from the page by clicking any navigation link (e.g., "Stocks" or "Home" in the header/sidebar)
5. Navigate back to `http://localhost:3835/data`
6. Scroll to the "Remove imported data" panel and observe its state

**Expected Result:**
- The page loads without errors on return
- The Remove panel renders correctly with the "From" and "To" date fields visible and the "Preview removal" button present
- (Date values may or may not persist — either is acceptable; the panel must render without a crash or blank section)

---

### UT-15 — Other sections of the /data page still function after this phase (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — general page integrity

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Verify the availability heatmap section is visible (a date-by-symbol grid or colored tile display)
3. Verify at least one other panel or section (e.g., "Fetch data", "Data coverage", job list) is visible and renders without an error state
4. If a job list is present, confirm it shows job entries (or an empty state message) rather than an error

**Expected Result:**
- The availability heatmap section renders without a blank panel or "Error loading" message
- At least one other panel (Fetch data, coverage, jobs) renders correctly
- No section of the `/data` page shows a React error boundary ("Something went wrong") overlay

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | `/data` |
| UT-02 | Remove panel shows only two date fields (no symbols input) | smoke | P1 | `/data` — RemoveDataPanel |
| UT-03 | Preview button disabled with no dates entered | validation | P1 | `/data` — RemoveDataPanel |
| UT-04 | Preview button disabled with only From date | validation | P1 | `/data` — RemoveDataPanel |
| UT-05 | Preview button disabled with only To date | validation | P1 | `/data` — RemoveDataPanel |
| UT-06 | Preview button disabled with an invalid date | validation | P2 | `/data` — RemoveDataPanel |
| UT-07 | Preview button enabled when both dates are valid | happy-path | P1 | `/data` — RemoveDataPanel |
| UT-08 | Preview button re-disables when a date is cleared | validation | P2 | `/data` — RemoveDataPanel |
| UT-09 | Confirm modal shows counts only (no symbol lists) | happy-path | P1 | `/data` — RemoveConfirmModal |
| UT-10 | Confirm button visible without scrolling | ux | P1 | `/data` — RemoveConfirmModal |
| UT-11 | Modal body scrollable, footer remains fixed | ux | P2 | `/data` — RemoveConfirmModal |
| UT-12 | Cancel closes modal without removing data | regression | P1 | `/data` — RemoveConfirmModal |
| UT-13 | Backfill job card shows complete/partial (not crash) | happy-path | P1 | `/data` — Backfill job card |
| UT-14 | Navigating away and back does not break Remove panel | regression | P2 | `/data` — RemoveDataPanel |
| UT-15 | Other /data sections still function after this phase | regression | P1 | `/data` — general |

**P1 tests must all pass for browser QA verdict to be PASS.**
