# Phase goal-i_can_see_the_wealthy_future_forever-iter-23 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Date:** 2026-06-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Data Manager page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8000
- No job is currently running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (the "Checking backend…" spinner resolves)

**Expected Result:**
- Page renders without a blank screen or "Checking backend…" stuck state
- The heading "Data Manager" (or equivalent page title) is visible
- The JobForm card is visible, showing a job-kind selector and a "Start job" button
- The Coverage panel is visible with a `universe-count` value displayed
- The RunHistoryPanel (run history table) is visible below the form
- No red error banner is displayed

---

### UT-02 — "Expand universe" option appears in the job-kind dropdown (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — `JobForm` job-kind selector

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the job-kind `<select>` control in the "Start a fetch / backfill / expand job" card
3. Click the job-kind dropdown to open it

**Expected Result:**
- The dropdown shows exactly four options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill", and "Expand universe"
- "Expand universe" is not grayed out or disabled
- Clicking "Expand universe" selects it without an error

---

### UT-03 — Panel subtitle mentions "expand" as a job type requiring a source (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data` — `JobForm` card header

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the subtitle text below the "Start a fetch / backfill / expand job" card heading

**Expected Result:**
- The subtitle text reads (or contains): "…and — for a fetch or expand — an import source"
- The old copy ("…and — for a fetch — an import source") does NOT appear

---

### UT-04 — Import source picker appears when "Expand universe" is selected (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm` source picker

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and serving the provider catalog

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown and select "Expand universe"
3. Observe whether the Import source picker is now visible

**Expected Result:**
- The Import source `<select>` control appears below the job-kind selector (it was previously hidden when no fetch/expand job was selected)
- The source picker shows all available sources (yahoo, tiingo, finnhub, alpha_vantage, stooq, etc.)

---

### UT-05 — Ineligible sources are disabled when "Expand universe" is selected (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm` source picker

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend serving `GET /api/data` with source catalog including `supports_market_cap` flags
- "Expand universe" is selected in the job-kind dropdown

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown and select "Expand universe"
3. Click the Import source dropdown to open it
4. Locate the "Alpha Vantage" option in the list
5. Locate the "Stooq" option in the list

**Expected Result:**
- The "Alpha Vantage" option is visually disabled (grayed out) and its label includes the text "cannot supply market cap — not selectable for expand"
- The "Stooq" option is visually disabled (grayed out) and its label includes the text "cannot supply market cap — not selectable for expand"
- The "Yahoo" option is not disabled (normal appearance, no reason text appended)
- Clicking the "Alpha Vantage" option does NOT change the currently selected source

---

### UT-06 — Amber alert appears when an ineligible source is selected for expand (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm` ineligible-reason alert (`data-testid="expand-ineligible-reason"`)

**Preconditions:**
- Frontend is running at http://localhost:3835
- "Expand universe" is selected in the job-kind dropdown
- The source picker is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown and select "Expand universe"
3. In the Import source picker, attempt to select "Alpha Vantage" (or if the option is HTML-disabled, use browser developer tools to temporarily enable it and select it, OR test with "Stooq" if any ineligible source is selectable via JS)

**Expected Result:**
- An amber (yellow-orange) alert block appears below the Import source picker
- The alert contains text indicating "Alpha Vantage cannot supply market cap — not selectable for an expand job"
- The alert suggests Yahoo as an alternative
- The element with `data-testid="expand-ineligible-reason"` is present in the DOM

---

### UT-07 — Start button is disabled when an ineligible source is selected for expand (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data` — `JobForm` Start button

**Preconditions:**
- Frontend is running at http://localhost:3835
- "Expand universe" is selected in the job-kind dropdown
- An ineligible source (Alpha Vantage or Stooq) is selected or the form is in the ineligible state

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown and select "Expand universe"
3. If the ineligible source can be selected, select "Alpha Vantage" from the source picker; otherwise observe the Start button state with the ineligible-reason alert visible
4. Locate the "Start job" button

**Expected Result:**
- The "Start job" button is disabled (cannot be clicked)
- The button shows visual disabled state: opacity-50 and cursor-not-allowed styling
- Clicking the button does nothing (no API call is fired, no job is started)

---

### UT-08 — Eligible source (Yahoo) allows Start button when "Expand universe" is selected (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data` — `JobForm` Start button

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running
- Date range fields are filled in the job form

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown and select "Expand universe"
3. Select "Yahoo" from the Import source picker
4. Fill in the "Start date" field with "2025-01-01"
5. Fill in the "End date" field with "2025-01-31"
6. Observe the "Start job" button

**Expected Result:**
- The "Start job" button is enabled (not disabled, normal cursor)
- No amber alert block appears below the source picker
- The ineligible-reason element (`data-testid="expand-ineligible-reason"`) is NOT visible

---

### UT-09 — Expand job card shows "Universe screen" result block with passers and omitted badges (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` ExpandScreenResult block (`data-testid="expand-screen-result"`)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running with an injected/test provider that completes an expand job with known results (e.g., 10 passers, 3 omitted)
- An expand job has completed and its job card is visible on the `/data` page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the completed expand job card in the active or recent jobs section
3. Look for a "Universe screen" section within the job card
4. Observe the element with `data-testid="expand-screen-result"`

**Expected Result:**
- A "Universe screen" section is visible on the job card
- A green badge with `data-testid="expand-passers"` shows text like "10 passed" (the actual passer count)
- An amber badge with `data-testid="expand-omitted-count"` shows text like "3 omitted" (the actual omitted count)
- The passers count plus the omitted count equals the total candidates processed, shown as "of N candidates"
- The element `data-testid="expand-screen-result"` is present in the DOM

---

### UT-10 — Expand job card shows scrollable omitted-with-reason list (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `ExpandScreenResult` omitted list (`data-testid="expand-omitted-list"`)

**Preconditions:**
- Frontend is running at http://localhost:3835
- An expand job has completed with at least one omitted candidate
- The job card is visible on the `/data` page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the completed expand job card
3. Find the "Universe screen" section
4. Locate the element with `data-testid="expand-omitted-list"`
5. Look for at least one entry in the omitted list

**Expected Result:**
- The omitted list shows each omitted symbol alongside its plain-language reason string (e.g., "market_cap below threshold", "price below $10", "no_market_cap", "fetch_failed")
- Each entry clearly shows both the symbol ticker and the reason — not just a code
- If the list contains many entries, the container is scrollable (has a max-height with overflow:scroll or overflow:auto applied)

---

### UT-11 — Empty-omissions state shows confirmation message when all candidates pass (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data` — `ExpandScreenResult` empty omissions state

**Preconditions:**
- Frontend is running at http://localhost:3835
- An expand job has completed where all candidates passed the screen (0 omissions)
- The job card is visible on the `/data` page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the completed expand job card with 0 omitted candidates
3. Find the "Universe screen" section on the card

**Expected Result:**
- The amber omitted badge shows "0 omitted"
- Instead of an omitted list, the text "All screened candidates passed — no omissions." appears in the omitted section
- The element `data-testid="expand-omitted-list"` is either absent or empty

---

### UT-12 — Expand job shows chunk progress badge during run (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` chunk progress badge (`data-testid="chunk-progress"`)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running an expand job that is currently in progress (chunking through candidates)
- The job card is visible and live-updating

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Start an expand job (select "Expand universe", choose "Yahoo", enter a valid date range, click "Start job")
3. While the job is running, observe the job card for a progress indicator

**Expected Result:**
- A chunk progress badge with `data-testid="chunk-progress"` appears on the job card
- The badge shows text in the format "Chunk X/N" (e.g., "Chunk 2/5") where X is the current chunk and N is the total
- The badge updates as chunks are processed (visible without page reload)

---

### UT-13 — Rate-limited expand job shows amber resumable state with Resume button (error)

**Type:** error
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` resumable state block (`data-testid="resumable-state"`)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has processed an expand job that hit a rate limit mid-run (the job is in "resumable" state)
- The job card is visible on the `/data` page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the job card for the expand job that stopped in the resumable/rate-limited state
3. Observe the job card styling and available controls

**Expected Result:**
- The job card shows an amber (yellow) styling for the resumable state block (`data-testid="resumable-state"`)
- The block contains text indicating the job was rate-limited and can be resumed
- A "Resume" button is visible on the job card
- The chunk progress badge (`data-testid="chunk-progress"`) shows the chunk at which the job paused (e.g., "Chunk 3/5")

---

### UT-14 — Resume button continues an expand job from where it stopped (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` Resume button

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend has an expand job in "resumable" state (paused at chunk 3 of 5)
- The "Resume" button is visible on the job card

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the expand job card showing the "resumable" state with a "Resume" button
3. Note the current chunk number shown in the chunk progress badge (e.g., "Chunk 3/5")
4. Click the "Resume" button on the job card

**Expected Result:**
- The job card transitions from amber "resumable" state back to an active/running state
- The chunk progress badge updates to show progress from chunk 4 onwards (does not restart from "Chunk 1/5")
- If the job completes, the "Universe screen" result block appears with passers and omitted badges
- No error message appears about restarting from the beginning

---

### UT-15 — Coverage panel universe-count reflects grown universe after expand (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `CoveragePanel` universe-count (`data-testid="universe-count"`)

**Preconditions:**
- Frontend is running at http://localhost:3835
- An expand job has completed with N passing members (where N differs from the pre-expand universe count)
- The Coverage panel is visible on the `/data` page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the Coverage panel on the page
3. Find the element with `data-testid="universe-count"`
4. Record the displayed value

**Expected Result:**
- The `universe-count` element shows a numeric value
- The value matches the number of passers from the most recently completed expand job (not the pre-expand YAML-only count)
- The Coverage panel does NOT require a page reload to show the updated count after the expand completes

---

### UT-16 — Run history table shows expand kind rows with screen outcome (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `RunHistoryPanel` run-history table

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one expand job has completed
- The RunHistoryPanel is visible on the `/data` page

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down to the run history table in the RunHistoryPanel
3. Look for a row corresponding to the completed expand job

**Expected Result:**
- A row with the "expand" kind badge is present in the run history table
- The Summary column for that row contains text describing the screen outcome (e.g., "X passed, Y omitted" or similar)
- The expand row appears alongside existing fetch/backfill/both rows without visual conflict
- The expand row does NOT show an error where a summary would appear

---

### UT-17 — Existing job kinds (fetch, backfill, both) still appear and work after expand addition (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `JobForm` job-kind selector

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown
3. Verify "Backfill snapshots", "Fetch EOD prices", and "Fetch + backfill" are all present
4. Select "Fetch EOD prices"
5. Confirm the Import source picker appears
6. Select "Yahoo" from the source picker
7. Fill in "Start date" with "2025-01-01" and "End date" with "2025-01-07"
8. Click the "Start job" button

**Expected Result:**
- All three original job kinds are present in the dropdown alongside "Expand universe"
- Selecting "Fetch EOD prices" shows the source picker (as before)
- No source options are disabled for "Fetch EOD prices" (the ineligible-reason alert does NOT appear for fetch jobs)
- The "Start job" button is enabled when a valid source and dates are selected
- The job starts (job card appears) without a 422 or validation error

---

### UT-18 — Source picker shows enabled sources (no ineligible alert) when non-expand kind is selected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `JobForm` source picker

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the job-kind dropdown and select "Fetch EOD prices"
3. Open the Import source picker and inspect the "Alpha Vantage" option
4. Inspect the "Stooq" option

**Expected Result:**
- "Alpha Vantage" is NOT disabled (normal appearance, no "cannot supply market cap" text in its label)
- "Stooq" is NOT disabled (normal appearance)
- The ineligible-reason alert (`data-testid="expand-ineligible-reason"`) is NOT present anywhere on the page
- Both sources can be selected without triggering the amber alert

---

### UT-19 — Exactly one date selector exists per page after adding expand controls (regression / J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — global date selector (J-18 invariant)

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Select "Expand universe" from the job-kind dropdown so all expand-related controls are visible
3. Count all `<select>` or date-picker elements on the page that represent a date state control
4. Distinguish between: (a) the single global as-of date switcher (a persistent date state selector), and (b) job parameter form inputs like "Start date" and "End date" (these are form inputs, not a second date state)

**Expected Result:**
- There is exactly ONE element acting as a global date-state selector (the as-of switcher that affects all page content)
- The expand form may include "Start date" and "End date" form inputs, but these are job parameters — they do NOT constitute a second persistent date state
- Adding the expand controls does NOT introduce a new date-scoped page element that persists independently of the global as-of control

---

### UT-20 — Panel footer description text mentions expand job explanation (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `JobForm` card footer description

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate the footer description text at the bottom of the "Start a fetch / backfill / expand job" card

**Expected Result:**
- The footer text includes a sentence explaining the expand job, such as: "Expand screens the committed candidate pool… over a market-cap-capable source and grows the scored universe — every omitted candidate is listed with its reason."
- The expand job description is present alongside (not replacing) the explanations for fetch and backfill jobs

---

### UT-21 — "Expand universe" option is discoverable from the job form without developer knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `JobForm`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Without any prior knowledge of the feature, locate the job-kind selector
3. Open the dropdown and read the available options

**Expected Result:**
- The label "Expand universe" is clearly visible as a fourth option in the job-kind dropdown
- The label is plain English — a user unfamiliar with the codebase can understand it refers to growing the universe of stocks
- No developer-facing code string (e.g., "expand", "kind_expand", "J-35") is shown as the option label to the user

---

### UT-22 — Ineligible source reason text is legible and actionable (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — disabled source options and ineligible-reason alert

**Preconditions:**
- Frontend is running at http://localhost:3835
- "Expand universe" is selected in the job-kind dropdown

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Select "Expand universe" from the job-kind dropdown
3. Open the Import source picker
4. Read the label text for the disabled "Alpha Vantage" option
5. If the ineligible-reason alert is visible, read its content

**Expected Result:**
- The disabled option label reads in plain English, e.g., "Alpha Vantage · cannot supply market cap — not selectable for expand"
- The alert text (if present) names the specific source, explains the limitation, and suggests an eligible alternative such as Yahoo
- A non-technical operator reading the label or alert immediately understands what to do next (switch to Yahoo or Tiingo)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads without errors | smoke | P1 | `/data` |
| UT-02 | "Expand universe" option appears in job-kind dropdown | smoke | P1 | `/data` — job-kind select |
| UT-03 | Panel subtitle mentions "expand" as source-requiring job | smoke | P1 | `/data` — card header |
| UT-04 | Import source picker appears when Expand is selected | happy-path | P1 | `/data` — source picker |
| UT-05 | Ineligible sources are disabled when Expand is selected | happy-path | P1 | `/data` — source options |
| UT-06 | Amber alert appears when ineligible source selected | happy-path | P1 | `/data` — ineligible-reason alert |
| UT-07 | Start button disabled for ineligible source + expand | validation | P1 | `/data` — Start button |
| UT-08 | Eligible source (Yahoo) allows Start with Expand | validation | P1 | `/data` — Start button |
| UT-09 | Expand job card shows Universe screen result block | happy-path | P1 | `/data` — ExpandScreenResult |
| UT-10 | Expand job card shows omitted-with-reason list | happy-path | P1 | `/data` — omitted list |
| UT-11 | Empty omissions shows "All passed" confirmation | happy-path | P2 | `/data` — empty omissions |
| UT-12 | Expand job shows chunk progress badge during run | happy-path | P1 | `/data` — chunk-progress |
| UT-13 | Rate-limited expand shows amber resumable state | error | P1 | `/data` — resumable-state |
| UT-14 | Resume button continues expand from checkpoint | happy-path | P1 | `/data` — Resume button |
| UT-15 | Coverage universe-count reflects grown universe | happy-path | P1 | `/data` — universe-count |
| UT-16 | Run history table shows expand rows with outcome | happy-path | P1 | `/data` — run history |
| UT-17 | Existing job kinds still appear and work (regression) | regression | P1 | `/data` — job-kind select |
| UT-18 | Source picker shows no ineligible alert for non-expand | regression | P1 | `/data` — source picker |
| UT-19 | Exactly one date selector exists (J-18 invariant) | regression | P1 | `/data` — date controls |
| UT-20 | Panel footer description mentions expand job | ux | P2 | `/data` — card footer |
| UT-21 | "Expand universe" is discoverable from job form | ux | P2 | `/data` — JobForm |
| UT-22 | Ineligible source reason text is legible and actionable | ux | P2 | `/data` — source options |

**P1 tests (UT-01 through UT-19 except UT-11) must all pass for browser QA verdict to be PASS.**
