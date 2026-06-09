# Phase goal-i_can_see_the_wealthy_future_forever-iter-25 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /data page loads with all three panels present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8000 (verify with `curl http://localhost:8000/health`)
- At least one universe member exists in the database

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to finish loading (health badge in the header must show "Online", not "Checking backend...")
3. Scroll down through the page

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Data Manager" (or equivalent) is visible at the top
- A "Coverage" panel is visible on the page (existing J-36 panel)
- A "Missing-data diagnostic" panel is visible directly below the Coverage panel
- An "Unfinished-imports" panel is visible OR is absent entirely (absent means all imports are clean — both states are valid; a blank placeholder card is NOT acceptable)
- No red error banner or unhandled exception message appears anywhere on the page

---

### UT-02 — Missing-data diagnostic panel shows "No missing data" when universe is clean (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — `MissingDataDiagnosticPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835
- All universe members have sufficient history (bar count >= `min_history_bars`) and no intra-series gaps
- This state may require a freshly seeded or clean dataset — confirm by checking the Coverage panel shows no "insufficient" rows

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (health badge shows "Online")
3. Locate the "Missing-data diagnostic" panel (it appears directly below the Coverage panel)

**Expected Result:**
- The "Missing-data diagnostic" panel is present on the page
- The panel shows a clean empty-state message such as "No missing data" (exact text may vary, but a positive confirmation message must appear)
- No sub-sections labeled "No history", "Thin history", or "Intra-series gaps" are present
- No "Pull the missing data" buttons are visible anywhere in the diagnostic panel
- No "Pull all missing" button is visible

---

### UT-03 — Missing-data diagnostic renders three categories with exact shortfalls (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `MissingDataDiagnosticPanel`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend dataset contains at least one universe member in each of the three diagnostic categories:
  - One member with zero stored bars (no-history)
  - One member with bars below the `min_history_bars` threshold but above zero (thin)
  - One member with trading days missing inside its own first-to-last date range (intra-series gap)
- If no such members exist, this test requires a fixture or test dataset — coordinate with the backend developer

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the "Missing-data diagnostic" panel
4. Look for a section labeled "No history" within the panel
5. Verify the no-history member's row is present and shows the symbol name and a shortfall like "0 / 200 bars" (exact numbers depend on config)
6. Look for a section labeled "Thin history" within the panel
7. Verify the thin member's row shows the symbol name and a shortfall like "12 / 200 bars" (bars-have / bars-needed)
8. Look for a section labeled "Intra-series gaps" within the panel
9. Verify the gap member's row shows the symbol name, a missing-day count, and a date range like "3 missing 2025-01-15 → 2025-02-03"

**Expected Result:**
- All three labeled sections ("No history", "Thin history", "Intra-series gaps") are present in the diagnostic panel
- Each section contains at least one row with the expected symbol and an exact shortfall value
- Shortfall values are not empty, not "N/A", and not placeholder text
- The fine member (if one exists in the universe) does NOT appear in any section
- No section contains a fabricated or zero shortfall for a member that actually has sufficient data

---

### UT-04 — No-history and intra-series-gap rows show "Pull the missing data" button; thin rows do not (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `DiagnosticCategory` rows

**Preconditions:**
- Same as UT-03: dataset has members in all three diagnostic categories

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the "Missing-data diagnostic" panel
4. Find a row under the "No history" section
5. Inspect that row for a button labeled "Pull the missing data"
6. Find a row under the "Intra-series gaps" section
7. Inspect that row for a button labeled "Pull the missing data"
8. Find a row under the "Thin history" section
9. Inspect that row — look specifically for a "Pull the missing data" button

**Expected Result:**
- The "No history" row DOES have a "Pull the missing data" button visible
- The "Intra-series gaps" row DOES have a "Pull the missing data" button visible
- The "Thin history" row does NOT have a "Pull the missing data" button — the row shows the shortfall for transparency but no action button
- A "Pull all missing" button is visible somewhere in the diagnostic panel header area (covers all pullable rows)

---

### UT-05 — "Pull all missing" dispatches a job and surfaces it in the job card (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `pull-all-button`, job card

**Preconditions:**
- Dataset has at least one pullable diagnostic row (no-history or intra-series gap)
- Frontend is running at http://localhost:3835
- Backend is running
- No other jobs are currently running (check the job card area is idle or shows a completed state)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load and the diagnostic panel to show at least one pullable row
3. Locate the "Pull all missing" button in the Missing-data diagnostic panel
4. Click the "Pull all missing" button
5. Observe the job card area of the page (existing live job progress area)

**Expected Result:**
- After clicking "Pull all missing", a job card appears (or the existing job card updates) showing a running or queued state
- The job card shows progress indicators (e.g., "Fetching..." or a progress bar) — it must not remain empty or show a silent success
- The pull operation does not navigate away from the `/data` page
- No error message or red alert appears immediately after clicking (an error may appear later if the provider is unavailable, but not instantly for a valid dataset)

---

### UT-06 — Per-row "Pull the missing data" dispatches a gap-exact job for one symbol (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `pull-row-button`, job card

**Preconditions:**
- Dataset has at least one no-history or intra-series-gap member visible in the diagnostic panel
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate a row under "No history" or "Intra-series gaps" in the Missing-data diagnostic panel
4. Note the symbol name shown on that row (e.g., "AAPL")
5. Click the "Pull the missing data" button on that specific row (not the "Pull all missing" button)
6. Observe the job card area

**Expected Result:**
- A job card appears showing the noted symbol (e.g., "AAPL") in the job description
- The job card does NOT show the entire universe or all symbols — it scopes only to the one symbol
- The job card shows a running, queued, or completed status
- The `/data` page remains on screen (no redirect)

---

### UT-07 — After a pull completes, the diagnostic row clears and coverage updates (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — diagnostic panel row auto-clear, Coverage panel

**Preconditions:**
- A "Pull the missing data" job was just dispatched (from UT-06 or UT-05) using the offline injected provider (completes quickly)
- The job card shows the job in progress or just completed

**Steps:**
1. Remain on `http://localhost:3835/data` after dispatching a pull job
2. Wait for the job card to show a "completed" or equivalent finished state
3. Observe the Missing-data diagnostic panel — specifically the row for the pulled symbol

**Expected Result:**
- The row for the successfully pulled symbol is no longer visible in the diagnostic panel (it has been cleared or removed)
- If all pullable rows are now resolved, the panel shows the "No missing data" empty-state
- The Coverage panel (J-36) below the diagnostic now shows a non-zero bar count for the previously missing symbol (or an increased bar count for a gap member)
- No stale row remains for a symbol that now has sufficient data

---

### UT-08 — Unfinished-imports panel shows all three import states (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `UnfinishedImportsPanel`

**Preconditions:**
- Backend has at least one import in each of the three unfinished states:
  - One paused/resumable import (amber)
  - One partial import (some symbols failed; amber)
  - One failed import (all symbols failed; red)
- Frontend is running at http://localhost:3835
- This state may require a test fixture — coordinate with the backend developer if not present naturally

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Scroll to the "Unfinished imports" panel (it should appear separately from the Coverage panel and the diagnostic panel)
4. Observe each row in the panel

**Expected Result:**
- The panel heading reads "Unfinished imports" (or equivalent) — it does NOT say "Resumable imports"
- At least one row has an amber status badge and a plain-language state string containing the word "Paused" (e.g., "Paused — hit a provider rate-limit (429); progress saved")
- At least one row has an amber status badge and a plain-language state string containing the word "Partial" (e.g., "Partial — 5/10 symbols ok, 5 failed")
- At least one row has a red status badge and a plain-language state string containing the word "Failed" (e.g., "Failed — every symbol failed; provider unreachable")
- Each row has done/remaining/failed counts visible (numeric values, not empty)

---

### UT-09 — Unfinished-imports panel is hidden when no unfinished imports exist (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `UnfinishedImportsPanel` absent state

**Preconditions:**
- All imports are in a clean completed state (no resumable, partial, or failed imports)
- This may be the normal state on a freshly seeded database

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Scroll through the entire page looking for any panel with a heading containing "Unfinished" or "Resumable"

**Expected Result:**
- No "Unfinished imports" panel is visible anywhere on the page
- No blank or empty card labeled "Resumable imports" is visible (the old behavior was to show a blank card — this should be gone)
- The page shows only the Coverage panel and the Missing-data diagnostic panel (plus any other existing panels)

---

### UT-10 — Status badges are correct colors: amber for paused/partial, red for failed (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `UnfinishedImportsPanel` status badges

**Preconditions:**
- Unfinished-imports panel is visible with rows in multiple states (see UT-08 preconditions)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the "Unfinished imports" panel
4. Find a row whose plain-language state string starts with "Paused"
5. Observe the badge color on that row
6. Find a row whose plain-language state string starts with "Partial"
7. Observe the badge color on that row
8. Find a row whose plain-language state string starts with "Failed"
9. Observe the badge color on that row

**Expected Result:**
- The "Paused" row has an amber (yellow-orange) badge — NOT red or green
- The "Partial" row has an amber badge — NOT red or green
- The "Failed" row has a red badge — NOT amber or green
- All badge colors are distinct and legible against the dark background of the page

---

### UT-11 — "Resume" button continues a paused import (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `ResumeControl`

**Preconditions:**
- At least one resumable (paused) import row is visible in the Unfinished-imports panel
- The paused import has a plain-language state starting with "Paused"

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the Unfinished-imports panel and find the "Paused" row
4. Look at the action buttons on that row
5. Click the "Resume" button on the paused row

**Expected Result:**
- A job card appears (or updates) showing the resumed import is running
- The paused row either disappears from the Unfinished-imports panel (if the import completes) or updates to show running status
- No second date selector or new date-picker appears on the page as a result of clicking Resume
- The run-history table below the Unfinished-imports panel still shows the original run's audit entry

---

### UT-12 — "Retry remaining" button re-dispatches only failed work (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RetryControl`

**Preconditions:**
- At least one partial or failed import row is visible in the Unfinished-imports panel

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the Unfinished-imports panel
4. Find a row with a "Partial" or "Failed" state
5. Look at the action buttons on that row — find the button labeled "Retry remaining" (or similar, e.g., "Retry remaining/failed")
6. Click the "Retry remaining" button on that row

**Expected Result:**
- A new job card appears showing the retry in progress
- The job card description scopes only to the symbols that failed — not the entire original universe
- The Unfinished-imports panel either removes the row (if retry completes cleanly) or updates it with new progress
- The run-history table below remains unchanged — the original run's entry is still present

---

### UT-13 — "Dismiss" button removes the row from the panel but leaves run-history intact (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `DismissControl`

**Preconditions:**
- At least one row is visible in the Unfinished-imports panel (any state: paused, partial, or failed)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the Unfinished-imports panel
4. Note the first row's symbol(s) and state (e.g., "Partial — AAPL, MSFT")
5. Find the "Dismiss" button (or "Remove" button) on that row
6. Click the "Dismiss" button
7. Observe the Unfinished-imports panel immediately after clicking
8. Scroll down to the Run-history table below the Unfinished-imports panel

**Expected Result:**
- The dismissed row disappears from the Unfinished-imports panel immediately (within a second or two — no page refresh needed)
- The Run-history table below still contains the entry for that run (it was not deleted from the audit log)
- If no other unfinished imports remain, the entire Unfinished-imports panel disappears (not a blank card)
- No red error message appears after clicking Dismiss

---

### UT-14 — Session-only API key re-prompt appears when resuming a needs-key import (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `ResumeControl` session-key re-prompt

**Preconditions:**
- A paused import exists from a provider that requires an API key (e.g., Alpha Vantage, Tiingo)
- The import row shows a "Resume" button in the Unfinished-imports panel
- To set this up: use `source=alpha_vantage` with key `demo` — this throttles quickly and creates a resumable checkpoint (see project memory: "Alpha Vantage demo key drives resumable")

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the Unfinished-imports panel and find the paused row from a needs-key source (Alpha Vantage or similar)
4. Click the "Resume" button on that row
5. Observe what happens before the job is submitted

**Expected Result:**
- A key input field or prompt appears asking for the API key before the job is re-dispatched — the resume does NOT fire silently without a key
- The prompt is visible on the page (e.g., an inline input field or an overlay/modal)
- After entering a key and submitting, the key input field clears or disappears — the key is not displayed back to the user
- A job card appears showing the resumed import in progress

---

### UT-15 — Session key is not persisted or echoed back in any visible UI element (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — session-key re-prompt, job card, Unfinished-imports panel

**Preconditions:**
- A needs-key import is ready to Resume (see UT-14 preconditions)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the paused needs-key import row and click "Resume"
3. When the key prompt appears, type the value `test-sentinel-key-12345` into the key input field
4. Click the submit or confirm button for the key prompt
5. After the job is dispatched, observe the job card contents
6. Observe the Unfinished-imports panel for any row containing the entered key text
7. Observe the plain-language state string for any echo of the key value

**Expected Result:**
- The text `test-sentinel-key-12345` does NOT appear anywhere in the job card
- The text `test-sentinel-key-12345` does NOT appear in the Unfinished-imports panel state string or row content
- The key input field is cleared or removed from the UI after submission
- No tooltip, data attribute, or visible label echoes the entered key value

---

### UT-16 — "Thin history" category displays shortfall but has no Pull button (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `DiagnosticCategory` "Thin history"

**Preconditions:**
- Dataset has a thin-history universe member (bars present but below `min_history_bars`)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the "Thin history" section in the Missing-data diagnostic panel
4. Find the row for the thin-history member
5. Read the shortfall value displayed on the row
6. Look carefully at the row for any button labeled "Pull the missing data"
7. Look at the diagnostic panel header for a "Pull all missing" button — does it exist even if the only pullable rows are thin?

**Expected Result:**
- The "Thin history" row shows a non-empty shortfall value (e.g., "45 / 200 bars") — the numbers reflect actual bars-have / bars-needed
- The "Thin history" row does NOT have a "Pull the missing data" button on it
- If all diagnostic rows are thin (no no-history or gap rows), the "Pull all missing" button is absent from the panel header

---

### UT-17 — Existing Coverage panel (J-36) still displays correctly after new panels added (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — Coverage panel (J-36)

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one universe member exists with stored bars

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the Coverage panel (it should be near the top of the main content area, above the Missing-data diagnostic panel)
4. Check that the Coverage panel shows per-symbol rows with bar counts
5. Check that the as-of date selector is visible (a single date dropdown or date-picker control)

**Expected Result:**
- The Coverage panel is present and shows per-symbol rows — it has not been removed or hidden by the new panels
- Bar counts are visible per symbol
- Exactly ONE date selector control is visible on the entire `/data` page (the global as-of selector — not a second date control introduced by the new panels)
- The date selector is unchanged in appearance and position compared to prior behavior

---

### UT-18 — Exactly one date selector on /data page after new panels added (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — global as-of date selector

**Preconditions:**
- Frontend is running at http://localhost:3835
- Both new panels (Missing-data diagnostic and Unfinished-imports) are visible or expected to appear

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Scan the entire page — top to bottom — for any `<select>` dropdowns, date-picker inputs, or date-range controls
4. Count the total number of date controls visible on the page

**Expected Result:**
- Exactly ONE date selector (the existing global as-of date selector) is present on the page
- No second, third, or additional date control appears in the Missing-data diagnostic panel or in the Unfinished-imports panel
- The "Pull the missing data" action buttons and "Retry" buttons do NOT add a visible date control to the page

---

### UT-19 — Provider failure on pull-missing surfaces an explicit error state (error)

**Type:** error
**Priority:** P2
**Surface:** `/data` — `MissingDataDiagnosticPanel`, job card

**Preconditions:**
- A pullable diagnostic row exists (no-history or intra-series gap)
- The backend is configured to simulate an unreachable provider (test/mock mode), OR the live provider is rate-limited (Yahoo/Alpha Vantage may return 429)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Click "Pull the missing data" on a pullable diagnostic row
4. Wait for the job to complete or fail
5. Observe the job card when it reaches a terminal or rate-limited state

**Expected Result:**
- The job card shows a non-success state: either a "Failed" badge (red) or an amber "Paused" badge if rate-limited
- A human-readable error message is visible in or near the job card (e.g., "Provider unreachable" or "Rate-limited — import paused")
- The diagnostic row for the affected symbol is NOT removed from the panel (the data was not fetched successfully)
- No fabricated bar count or success message appears

---

### UT-20 — Missing-data diagnostic panel is present and labeled below Coverage panel (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — page layout, panel discoverability

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Scroll from the top of the page downward
4. Note the order of panels encountered

**Expected Result:**
- The Coverage panel appears before the Missing-data diagnostic panel (coverage is above, diagnostic is below)
- The Missing-data diagnostic panel has a visible heading label (e.g., "Missing-data diagnostic" or similar) — it is not an unlabeled card
- A new user unfamiliar with the app can identify the diagnostic panel without a tooltip or external explanation
- The panel layout matches the dark analytical aesthetic of the rest of the `/data` page (no bright white boxes or out-of-place styling)

---

### UT-21 — Unfinished-imports panel label is "Unfinished imports", not "Resumable imports" (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `UnfinishedImportsPanel` heading

**Preconditions:**
- At least one unfinished import exists so the panel is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the unfinished-imports panel
4. Read the panel heading text

**Expected Result:**
- The panel heading reads "Unfinished imports" (or a clearly equivalent label such as "Unfinished imports" — any label that communicates all three states is acceptable)
- The heading does NOT say "Resumable imports" (the old label that implied only paused imports)
- Each row in the panel has a clearly labeled action button ("Resume", "Retry remaining", or "Dismiss"/"Remove") — users can distinguish between the three actions without developer knowledge

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /data page loads with all three panels present | smoke | P1 | `/data` |
| UT-02 | Missing-data diagnostic shows "No missing data" when clean | smoke | P1 | `/data` — `MissingDataDiagnosticPanel` |
| UT-03 | Diagnostic renders three categories with exact shortfalls | happy-path | P1 | `/data` — `MissingDataDiagnosticPanel` |
| UT-04 | No-history and gap rows have Pull button; thin rows do not | happy-path | P1 | `/data` — `DiagnosticCategory` rows |
| UT-05 | "Pull all missing" dispatches a job and shows job card | happy-path | P1 | `/data` — `pull-all-button` |
| UT-06 | Per-row "Pull the missing data" dispatches gap-exact job | happy-path | P1 | `/data` — `pull-row-button` |
| UT-07 | After pull completes, diagnostic row clears and coverage updates | happy-path | P1 | `/data` — diagnostic panel + Coverage |
| UT-08 | Unfinished-imports panel shows all three import states | happy-path | P1 | `/data` — `UnfinishedImportsPanel` |
| UT-09 | Unfinished-imports panel is hidden when no unfinished imports | regression | P1 | `/data` — `UnfinishedImportsPanel` |
| UT-10 | Status badges correct: amber for paused/partial, red for failed | ux | P2 | `/data` — status badges |
| UT-11 | "Resume" button continues a paused import | happy-path | P1 | `/data` — `ResumeControl` |
| UT-12 | "Retry remaining" re-dispatches only failed work | happy-path | P1 | `/data` — `RetryControl` |
| UT-13 | "Dismiss" removes row from panel but leaves run-history intact | happy-path | P1 | `/data` — `DismissControl` |
| UT-14 | Session-only API key re-prompt appears for needs-key Resume | happy-path | P1 | `/data` — session-key re-prompt |
| UT-15 | Session key is not persisted or echoed back in visible UI | validation | P2 | `/data` — key prompt, job card |
| UT-16 | Thin-history row shows shortfall but has no Pull button | validation | P2 | `/data` — `DiagnosticCategory` thin |
| UT-17 | Existing Coverage panel still displays correctly | regression | P1 | `/data` — Coverage panel (J-36) |
| UT-18 | Exactly one date selector on /data after new panels added | regression | P1 | `/data` — global as-of date |
| UT-19 | Provider failure on pull-missing surfaces explicit error | error | P2 | `/data` — job card |
| UT-20 | Missing-data diagnostic panel is labeled and discoverable below Coverage | ux | P2 | `/data` — page layout |
| UT-21 | Unfinished-imports panel label is "Unfinished imports" not "Resumable imports" | ux | P2 | `/data` — panel heading |

**P1 tests must all pass for browser QA verdict to be PASS.**
