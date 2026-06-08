# Phase goal-i_can_see_the_wealthy_future_forever-iter-24 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-08
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /data page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- At minimum the committed seed dataset is loaded

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (the "Checking backend..." spinner disappears)

**Expected Result:**
- Page renders without blank screen, "Checking backend...", or error message
- A "Dataset coverage" panel heading is visible
- A "Remove imported data" panel is visible below the Resumable imports section
- No red error banners are displayed

---

### UT-02 — Coverage panel shows defined metric blocks with plain-language definitions (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `CoveragePanel` `DefinedMetric` blocks

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has committed seed data loaded (at minimum)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Locate the "Dataset coverage" panel
4. Find the "Universe" figure and read the text directly below the number

**Expected Result:**
- The "Universe" figure shows a positive integer AND a one-sentence definition directly below it — the definition must refer to "config-screened" or "scored names" (not just repeat the label)
- The "Symbols" figure shows a positive integer AND a one-sentence definition directly below it explaining it includes every ticker with stored bars (including ETFs and index symbols)
- The "Price history" figure shows a date range AND a one-sentence definition
- The "Trading days" figure shows an integer AND a one-sentence definition
- The "Snapshot dates" figure shows an integer AND a one-sentence definition
- The "Backfill gaps" figure shows an integer AND a one-sentence definition describing a trading day with bars but no scanner snapshot

---

### UT-03 — Universe-vs-symbols prose line is visible at bottom of coverage panel (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `CoveragePanel` universe-vs-symbols prose line

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has committed seed data loaded

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down within the "Dataset coverage" panel to its bottom section

**Expected Result:**
- A prose sentence is visible that names both "universe" and "symbols" and explains the distinction — for example, "The universe is the config-screened, scored set of names; symbols includes every ticker with stored bars"
- The sentence is not simply two numbers side by side; it must contain plain-language words explaining what each count means

---

### UT-04 — Per-symbol coverage table renders with all required columns (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has committed seed data with at least one universe member that has bars

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the per-symbol coverage table (it appears inside or below the Dataset coverage card)
4. Inspect the column headers of the table

**Expected Result:**
- The table is visible and scrollable
- The following column headers are present: "Symbol", "In universe", "Has data", "Date range", "Bars", "Flag"
- At least one row is present
- A universe member row shows a badge or "yes" indicator in the "In universe" column
- The "Date range" cell for a universe member with bars shows two dates (e.g., "2020-01-02 → 2023-12-29"), not "NA"
- The "Bars" cell shows a positive integer

---

### UT-05 — Symbol search filter narrows the per-symbol table (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` symbol search input

**Preconditions:**
- Frontend is running at http://localhost:3835
- Per-symbol coverage table is visible and has at least 2 rows

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Locate the text input labeled "Filter symbol..." or similar above the per-symbol coverage table
4. Type "AAPL" into the "Filter symbol..." input field

**Expected Result:**
- Only rows whose symbol contains "AAPL" remain visible in the table
- All other rows are hidden while the filter text is in the input
- If no row contains "AAPL", an empty-state message is shown (not an error)

---

### UT-06 — Clearing the symbol search filter restores all rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` symbol search input

**Preconditions:**
- Frontend is running at http://localhost:3835
- The symbol search input currently contains "AAPL" (continuing from UT-05)

**Steps:**
1. Navigate to `http://localhost:3835/data` (or continue from UT-05)
2. Click inside the "Filter symbol..." input field and select all text (Ctrl+A)
3. Press the Delete key to clear the input

**Expected Result:**
- The filter input is empty
- All rows reappear in the per-symbol coverage table (same count as before UT-05 was performed)

---

### UT-07 — "Universe members only" toggle filters table to in-universe rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` universe-members-only toggle

**Preconditions:**
- Frontend is running at http://localhost:3835
- Per-symbol coverage table has both universe-member rows and non-universe rows

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Count the total number of rows in the per-symbol coverage table (note this number)
4. Click the "Universe members only" button or toggle above the per-symbol table (`data-testid="universe-members-only-toggle"`)

**Expected Result:**
- The row count decreases (assuming non-universe symbols exist)
- Every remaining visible row has a badge or "yes" indicator in the "In universe" column
- No row with an empty/no indicator in "In universe" is visible
- Every visible row shows either "yes" or a checkmark in "Has data", OR shows a "missing" badge in the "Flag" column — no universe member is silently absent

---

### UT-08 — Symbol column sort sorts rows A to Z then Z to A (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` Symbol column sort header

**Preconditions:**
- Frontend is running at http://localhost:3835
- Per-symbol coverage table has at least 3 rows with different symbols

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Click the "Symbol" column header in the per-symbol coverage table
4. Note the symbol in the first row and the symbol in the last visible row
5. Click the "Symbol" column header a second time
6. Note the symbol in the first row and the symbol in the last visible row again

**Expected Result:**
- After the first click: symbols are ordered A to Z (the first row shows a symbol that alphabetically precedes the last row's symbol)
- After the second click: symbols are ordered Z to A (the order is reversed from step 4)

---

### UT-09 — Bars column sort orders rows by bar count descending (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` Bars column sort header

**Preconditions:**
- Frontend is running at http://localhost:3835
- Per-symbol coverage table has at least 2 rows with different bar counts

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Click the "Bars" column header in the per-symbol coverage table

**Expected Result:**
- The rows reorder so the symbol with the highest bar count appears in the first row
- The "Bars" value in the first row is greater than or equal to the "Bars" value in the second row

---

### UT-10 — Thin badge rows are visually distinct and have a date range (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` thin badge rows

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one row in the per-symbol coverage table shows a "thin" badge in the Flag column

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Locate a row that shows a "thin" badge in the "Flag" column
4. Inspect the "Date range" cell of that row
5. Inspect the "Bars" cell of that row
6. Compare the row's background color to a normal (non-flagged) row

**Expected Result:**
- The "Date range" cell shows a non-null date range (two dates, e.g., "2022-03-01 → 2022-11-30")
- The "Bars" cell shows a positive integer (greater than 0)
- The row has a visually distinct background — amber or muted styling — compared to unflagged rows

---

### UT-11 — Missing badge rows show NA date range and zero bars (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `PerSymbolCoverageTable` missing badge rows

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one universe member has no bars (shows "missing" in Flag column). If none exist in the live dataset, activate the "Universe members only" toggle and look for any row with "no" in Has data.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Click the "Universe members only" toggle to filter to in-universe rows
4. Locate any row that shows a "missing" badge in the "Flag" column
5. Inspect the "Has data" cell of that row
6. Inspect the "Date range" cell of that row

**Expected Result:**
- The "Has data" cell shows "no" or an empty/cross indicator
- The "Date range" cell shows "NA" — not a fabricated date range
- The "Bars" cell shows 0 or is empty

---

### UT-12 — Remove imported data panel is present with correct controls (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down past the "Resumable imports" panel
4. Locate the panel labeled "Remove imported data" (`data-testid="remove-data"`)

**Expected Result:**
- The "Remove imported data" panel is visible
- A text field for symbols is present (for typing ticker symbols like "AAPL, MSFT")
- A "From date" date input is present
- A "To date" date input is present
- A "Preview removal" button is present and has a red-border or destructive visual style

---

### UT-13 — Preview removal button is disabled when no inputs are filled (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `RemoveDataPanel` Preview removal button

**Preconditions:**
- Frontend is running at http://localhost:3835
- The "Remove imported data" panel is visible with all inputs empty

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the "Remove imported data" panel
4. Confirm the symbols field is empty, the "From date" field is empty, and the "To date" field is empty
5. Attempt to click the "Preview removal" button (`data-testid="remove-preview-button"`)

**Expected Result:**
- The "Preview removal" button is disabled (it cannot be clicked or clicking it has no effect)
- No modal or dialog appears
- No error message about missing inputs appears — the button state alone communicates the requirement

---

### UT-14 — Preview removal button becomes enabled after entering a symbol (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `RemoveDataPanel` Preview removal button

**Preconditions:**
- Frontend is running at http://localhost:3835
- The "Remove imported data" panel is visible with all inputs empty

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the "Remove imported data" panel
4. Click the symbols text field and type "NVDA"
5. Observe the state of the "Preview removal" button

**Expected Result:**
- The "Preview removal" button becomes enabled (clickable) after typing "NVDA" in the symbols field
- The button now has an active appearance (not grayed out)

---

### UT-15 — Preview removal modal opens and shows removable bar details (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RemoveConfirmModal`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has at least one symbol with user-added bars (bars outside the committed seed windows). On a seed-only dataset, use a symbol that has bars and accept that the "Will be removed" count may be 0 while the "Not removable" section will show seed bars.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the "Remove imported data" panel
4. Click the symbols text field and type "NVDA"
5. Click the "Preview removal" button (`data-testid="remove-preview-button"`)
6. Wait for the modal to open

**Expected Result:**
- A full-screen overlay modal appears (`data-testid="remove-confirm-modal"`)
- The modal contains a section labeled "Will be removed (user-added)" or equivalent, showing a bar count (may be 0 on a seed-only dataset) and a date range or "none"
- The modal contains a "Not removable — committed seed (protected)" section (`data-testid="remove-not-removable"`) that lists per-symbol bar counts and the reason text "committed seed"
- The modal contains a "Cascade" section (`data-testid="remove-cascade"`) showing a snapshot count and forward returns count

---

### UT-16 — Preview modal for seed-only scope shows amber refusal and disabled confirm button (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data` — `RemoveConfirmModal` refused state

**Preconditions:**
- Frontend is running at http://localhost:3835
- A symbol is entered in the Remove panel that has bars only within the committed seed windows (i.e., all its bars are protected). On a seed-only dataset, any symbol works.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the "Remove imported data" panel
4. Click the symbols field and type the symbol that has only seed bars (e.g., "AAPL" on a seed-only host)
5. Leave "From date" and "To date" empty to scope to all dates
6. Click the "Preview removal" button
7. Wait for the modal to open
8. Locate the refusal message in the modal (`data-testid="remove-refused"`)
9. Locate the "Remove N bars" confirm button (`data-testid="remove-confirm-button"`)

**Expected Result:**
- The modal shows an amber-colored refusal message containing the text "committed seed"
- The "Remove N bars" button is disabled (grayed out, not clickable)
- No bars are deleted — this is a read-only preview

---

### UT-17 — Cancel button in preview modal closes modal without deleting data (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RemoveConfirmModal` Cancel button

**Preconditions:**
- Frontend is running at http://localhost:3835
- The preview modal is open (having followed steps 1–6 from UT-15)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the "Remove imported data" panel
4. Type "NVDA" in the symbols field and click "Preview removal"
5. Wait for the modal to open
6. Note the number of rows shown in the per-symbol coverage table (visible behind/around the modal, or close modal and check)
7. Click the "Cancel" button in the modal footer

**Expected Result:**
- The modal closes immediately
- The per-symbol coverage table is unchanged (same rows and bar counts as before the preview was opened)
- The "Remove imported data" panel is still visible with the "NVDA" text still in the symbols field (or cleared — either is acceptable, but no data was deleted)
- No success or error notice appears in the Remove panel

---

### UT-18 — Successful removal shows green success notice and updates table (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RemoveDataPanel` post-removal success notice

**Preconditions:**
- Frontend is running at http://localhost:3835
- A fixture or test environment with user-added bars is available (bars outside the committed seed windows). NOTE: Do NOT run this test against a live production database with real user-added bars that cannot be restored. Use a test instance or fixture environment.

**Steps:**
1. Navigate to `http://localhost:3835/data` on a test instance with user-added bars
2. Wait for page to fully load
3. Note the bar count shown in the per-symbol table for the test symbol (e.g., "TEST")
4. Type "TEST" in the symbols field of the "Remove imported data" panel
5. Click the "Preview removal" button
6. Wait for the modal to open
7. Confirm the "Will be removed (user-added)" section shows a bar count greater than 0
8. Click the "Remove N bars" button (`data-testid="remove-confirm-button"`)
9. Wait for the modal to close

**Expected Result:**
- The modal closes after clicking "Remove N bars"
- A green success notice appears in the "Remove imported data" panel (`data-testid="remove-done"`) stating how many bars, snapshots, and forward returns were removed (e.g., "Removed 45 bars, 3 snapshots, 45 forward returns")
- The per-symbol coverage table refreshes and the removed symbol's bar count is reduced (or the symbol row disappears if all its bars were removed)

---

### UT-19 — As-of date switcher drops removed dates after a successful removal (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — global as-of switcher after removal

**Preconditions:**
- A successful removal has been performed (test instance with user-added bars, continuing from UT-18)
- The removed bars were the only bars on certain dates (so those snapshot dates would be eliminated)

**Steps:**
1. Continuing from UT-18 after a successful removal
2. Locate the global as-of date switcher in the top navigation bar
3. Open the switcher (click the dropdown or date selector)
4. Check for the dates that corresponded only to the removed bars

**Expected Result:**
- Dates that previously appeared only because of the removed bars are no longer present in the global as-of date switcher
- Dates that still have remaining bars continue to appear in the switcher

---

### UT-20 — Existing Resumable imports panel still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — Resumable imports panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down to the "Resumable imports" panel (it should appear above the new "Remove imported data" panel)
4. Confirm the panel is visible

**Expected Result:**
- The "Resumable imports" panel is present and visible
- It shows either "No resumable imports" or a list of paused import jobs — it does not show an error message
- The panel is not replaced or hidden by the new "Remove imported data" panel

---

### UT-21 — Existing job submission (fetch/backfill) still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — job submission form

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Locate the job submission form (source selector and job-kind dropdown)
4. Select any available source from the source dropdown
5. Select "fetch" or "backfill" from the job-kind dropdown
6. Do NOT submit the job (this regression check is visual only — confirm the controls are present and enabled)

**Expected Result:**
- The job submission form is fully rendered with a source selector, a job-kind dropdown, and a Submit button
- The controls are enabled (not grayed out or missing)
- The new "Remove imported data" panel has not replaced or overlapped the job submission form

---

### UT-22 — /data page has exactly one as-of viewing date selector in the top navigation (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — global as-of switcher

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Count all `<select>` elements on the page that contain date options in the format YYYY-MM-DD in the top navigation bar
4. Check whether the "From date" and "To date" inputs in the Remove panel are `<input type="date">` elements (action parameters) versus a `<select>` with snapshot dates (viewing control)

**Expected Result:**
- Exactly one date-selection dropdown in the top navigation bar controls the global as-of viewing date
- The "From date" and "To date" inputs in the Remove panel are date range action parameters, not additional global as-of viewing controls
- Changing the Remove panel date inputs does NOT change the global as-of date displayed in the top navigation

---

### UT-23 — Coverage panel definitions are all present after page reload (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `CoveragePanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Press F5 (or Cmd+R) to reload the page
4. Wait for page to fully load again
5. Inspect the "Dataset coverage" panel for all six metric blocks

**Expected Result:**
- All six metric blocks (Price history, Universe, Symbols, Trading days, Snapshot dates, Backfill gaps) are still present with their definition sentences after the reload
- The per-symbol coverage table is also still present and populated
- No metric shows "undefined", "null", or an empty definition sentence

---

### UT-24 — Coverage panel is discoverable from top navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** Navigation — `/data` link

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835` (home page)
2. Look at the top navigation bar

**Expected Result:**
- A navigation link labeled "Data" or "Data Manager" is visible in the top navigation bar
- Clicking it navigates to `http://localhost:3835/data`
- On the /data page, the "Dataset coverage" panel is visible without scrolling (or is the first major panel encountered when scrolling)

---

### UT-25 — Remove panel is discoverable by scrolling /data (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `RemoveDataPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Scroll down through the page from top to bottom without using Ctrl+F or searching
4. Observe the order of panels encountered

**Expected Result:**
- The "Remove imported data" panel is visible on the page by scrolling
- It appears below the "Resumable imports" panel and above or near the run history table
- The panel heading "Remove imported data" is legible and clearly identifies the section's purpose
- The "Preview removal" button has a visually distinct (red-border or destructive) appearance that signals it is a careful-action button

---

### UT-26 — Per-symbol table is discoverable within the coverage panel (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `PerSymbolCoverageTable`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for page to fully load
3. Without using browser search (Ctrl+F), locate the per-symbol coverage table by reading the visible page content

**Expected Result:**
- The per-symbol coverage table has a visible heading or label that identifies it (e.g., "Per-symbol coverage" or similar)
- The column headers (Symbol, In universe, Has data, Date range, Bars, Flag) are readable without horizontal scrolling on a standard 1280px-wide viewport
- The "Filter symbol..." input and "Universe members only" toggle are visually grouped near the top of the table, not buried below it

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /data page loads without errors | smoke | P1 | `/data` |
| UT-02 | Coverage panel shows defined metric blocks | happy-path | P1 | `/data` |
| UT-03 | Universe-vs-symbols prose line is visible | happy-path | P1 | `/data` |
| UT-04 | Per-symbol coverage table renders with all columns | happy-path | P1 | `/data` |
| UT-05 | Symbol search filter narrows table | happy-path | P1 | `/data` |
| UT-06 | Clearing search filter restores all rows | happy-path | P1 | `/data` |
| UT-07 | Universe members only toggle filters table | happy-path | P1 | `/data` |
| UT-08 | Symbol column sort A to Z then Z to A | happy-path | P1 | `/data` |
| UT-09 | Bars column sort orders rows descending | happy-path | P1 | `/data` |
| UT-10 | Thin badge rows are visually distinct | happy-path | P1 | `/data` |
| UT-11 | Missing badge rows show NA date range | happy-path | P1 | `/data` |
| UT-12 | Remove imported data panel is present | smoke | P1 | `/data` |
| UT-13 | Preview removal button disabled with no inputs | validation | P2 | `/data` |
| UT-14 | Preview removal button enabled after entering symbol | validation | P2 | `/data` |
| UT-15 | Preview modal opens with removable bar details | happy-path | P1 | `/data` |
| UT-16 | Seed-only scope shows amber refusal and disabled button | validation | P1 | `/data` |
| UT-17 | Cancel button closes modal without deleting data | happy-path | P1 | `/data` |
| UT-18 | Successful removal shows green notice and updates table | happy-path | P1 | `/data` |
| UT-19 | As-of switcher drops removed dates after removal | happy-path | P1 | `/data` |
| UT-20 | Resumable imports panel still works | regression | P1 | `/data` |
| UT-21 | Job submission controls still present and enabled | regression | P1 | `/data` |
| UT-22 | Exactly one as-of date selector in top navigation | regression | P2 | `/data` |
| UT-23 | Coverage definitions present after page reload | regression | P2 | `/data` |
| UT-24 | Coverage panel discoverable from navigation | ux | P2 | navigation |
| UT-25 | Remove panel discoverable by scrolling | ux | P2 | `/data` |
| UT-26 | Per-symbol table discoverable within coverage panel | ux | P2 | `/data` |

**P1 tests (UT-01 through UT-12, UT-15 through UT-21) must all pass for browser QA verdict to be PASS.**

Note: UT-18 and UT-19 require a fixture/test environment with user-added bars. On a seed-only live host, these tests must be skipped or run against a disposable test database to avoid permanent data loss.
