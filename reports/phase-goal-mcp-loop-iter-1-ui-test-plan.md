# Phase goal-mcp-loop-iter-1 — UI Test Plan

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- API-level and artifact tests are covered in reports/qa/goal-mcp-loop-iter-1-test-plan.md (TC-01 to TC-21). -->
<!-- These UI tests are human-executable operator checks with exact click paths. -->

---

### UT-01 — /evidence page loads without error (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load (allow up to 5 seconds)

**Expected Result:**
- Page renders without a blank screen, crash, or full-page error message
- The heading "Evidence" is visible near the top of the page
- No red error banner covering the entire page content

---

### UT-02 — /stocks leaderboard loads and evidence chips are present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and /api/stocks returns at least one stock row

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard rows to appear
3. Look at the score area of the first visible row (the columns for Leadership, Entry Quality, and Risk)

**Expected Result:**
- Leaderboard renders with at least one row visible
- At least one small chip reading "Not yet proven" is visible in the score area of the first row
- The page does not show a blank state or full-page error

---

### UT-03 — Stock detail page loads with evidence chips (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3255
- At least one stock row is visible on /stocks

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the first stock row in the leaderboard to open its detail page
3. Wait for the detail page to fully load

**Expected Result:**
- Detail page renders without a blank screen or error message
- Three score card blocks are visible (Leadership, Entry Quality, Risk)
- At least one small chip reading "Not yet proven" is visible beneath a score value
- The page URL changes to `/stocks/<ticker>` (the ticker of the row you clicked)

---

### UT-04 — User clicks "Evidence" nav link and lands on /evidence (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** Sidebar navigation / `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Look at the left sidebar navigation menu
3. Locate the "Evidence" entry in the sidebar (it has a ShieldCheck icon and should appear after "Research")
4. Click "Evidence" in the left sidebar

**Expected Result:**
- Browser navigates to `http://localhost:3255/evidence`
- The page heading "Evidence" is visible
- The "Evidence" sidebar link appears highlighted or active (visually distinct from other links)
- The page is not a 404 or blank screen

---

### UT-05 — All three evidence chips visible on every leaderboard row (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and leaderboard has at least 3 rows

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for all leaderboard rows to load
3. On the first visible row, look below the Leadership score badge — confirm a chip reading "Not yet proven" is visible directly below it
4. On the same row, look below the Entry Quality score badge — confirm a chip reading "Not yet proven" is visible directly below it
5. On the same row, look below the Risk score badge — confirm a chip reading "Not yet proven" is visible directly below it
6. Repeat steps 3–5 on the second and third visible rows

**Expected Result:**
- Every inspected row has exactly three "Not yet proven" chips: one each below Leadership, Entry Quality, and Risk
- The chips are styled in a muted/gray style (not bright green or red)
- The chips appear below the letter-grade badge and numeric score, not overlapping them
- No row is missing any chip for any of the three score columns
- The letter grades, numeric scores, and row ordering are unchanged from before this phase

---

### UT-06 — Evidence page shows honest empty state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with an empty certified-claims ledger (default state — no claims have been certified)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for any loading indicator to disappear
3. Read the main content area of the page

**Expected Result:**
- A card or panel is visible that reads "No certified claims yet" (exact text)
- Somewhere on the page the phrase "every signal currently reads Not yet proven" is visible
- There is no table or list of claim rows (the ledger is empty)
- There is no "Proven" badge or claim row displayed anywhere on the page

---

### UT-07 — Evidence empty state lists all five claim fields (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with an empty ledger (default state)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for any loading indicator to disappear
3. Locate the bullet list or field list inside the empty state card
4. Read each item in the list

**Expected Result:**
- The list contains exactly these five entries (any order is acceptable, but all five must be present):
  - "Hypothesis"
  - "Out-of-sample verdict"
  - "Control comparison (vs SPY)"
  - "Registration date"
  - "Forward-walk score-to-date"
- No item from the list is missing
- No extra claim-row fields appear beyond the five above

---

### UT-08 — Stock detail page evidence chips on all three score cards (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with an empty ledger (default state)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the first stock row to open its detail page
3. Wait for the detail page to fully load
4. Locate the Leadership score card — confirm a chip reading "Not yet proven" is visible directly below the numeric score
5. Locate the Entry Quality score card — confirm a chip reading "Not yet proven" is visible directly below the numeric score
6. Locate the Risk score card — confirm a chip reading "Not yet proven" is visible directly below the numeric score

**Expected Result:**
- All three score cards (Leadership, Entry Quality, Risk) each show a "Not yet proven" chip below the numeric score
- The existing numeric score value, the score label (e.g., "Leadership"), and any score description text are still present and unchanged
- The chips are styled in a muted/gray style (not bright green or red)
- No score card is missing its chip

---

### UT-09 — Evidence API failure degrades gracefully on /stocks leaderboard (error)

**Type:** error
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running but `/api/evidence` is blocked or returning an error (simulate by: opening browser DevTools > Network tab > right-click the `/api/evidence` request and block its URL, then reload; OR stop the backend, then restart without the evidence endpoint)

**Steps:**
1. Open browser DevTools (F12), navigate to the Network tab
2. Navigate to `http://localhost:3255/stocks`
3. Block the request to `/api/evidence` (right-click the request in the Network tab and select "Block request URL", or use the browser's network conditions to simulate offline for that endpoint)
4. Reload the page (`Ctrl+R` or `Cmd+R`)
5. Wait for the leaderboard to finish loading
6. Inspect the score area of the first few rows

**Expected Result:**
- The leaderboard rows are fully visible with their letter grades and numeric scores intact
- All evidence chips still display "Not yet proven" (the fail-safe fallback — not an error icon or blank)
- No full-page error or loading spinner that never resolves
- The leaderboard remains interactive (rows are clickable)
- No JavaScript crash or error overlay on the page

---

### UT-10 — /evidence shows "Backend unavailable" error card when API fails (error)

**Type:** error
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- `/api/evidence` endpoint is blocked or returning an error (stop the backend OR block the URL in browser DevTools Network tab)

**Steps:**
1. Open browser DevTools (F12), navigate to the Network tab
2. Block requests to `/api/evidence` (right-click the URL and select "Block request URL")
3. Navigate to `http://localhost:3255/evidence`
4. Wait for the page to finish its loading attempt (loading spinner should disappear)

**Expected Result:**
- A styled error card is visible on the page with the heading "Backend unavailable" (exact text)
- The error card contains a message indicating that nothing is fabricated and every signal remains "Not yet proven"
- The page does not crash or show a blank white screen
- There is no spinner that spins indefinitely without resolving

---

### UT-11 — Leaderboard scores, grades, and row order unchanged by evidence addition (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard to fully load
3. On the first visible row, note the Leadership score: the letter grade (e.g., "A") and the numeric value (e.g., "87.3")
4. On the same row, note the Entry Quality score letter grade and numeric value
5. On the same row, note the Risk score letter grade and numeric value
6. Confirm the letter grade badges and numeric values are still visible and readable — they are not hidden, truncated, or shifted out of the column

**Expected Result:**
- The letter grade badges (e.g., "A", "B+", "C") are visible on each row for all three score columns
- The numeric score values are visible alongside the badges
- The "Not yet proven" chips appear below the existing badges — they do NOT replace or overlap the letter grades or numeric values
- The existing row ordering (however stocks were sorted before this phase) is unchanged
- No leaderboard functionality (e.g., sorting columns if available) is broken

---

### UT-12 — Stock detail ScoreCard content unchanged by evidence addition (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend is running at http://localhost:3255
- At least one stock is visible in the leaderboard

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the first stock row to open its detail page
3. Locate the Leadership ScoreCard
4. Confirm the following elements are still present and readable: the numeric score value, the label "Leadership", and any descriptive text below the label
5. Locate the Entry Quality ScoreCard
6. Confirm the numeric score value and the label "Entry Quality" are still present and readable
7. Locate the Risk ScoreCard
8. Confirm the numeric score value and the label "Risk" are still present and readable

**Expected Result:**
- All three ScoreCards display their numeric score, label, and description text exactly as before
- The "Not yet proven" chip appears below the numeric score — it does NOT replace the score value or the label
- No ScoreCard content (score number, label, description) is missing or visually broken

---

### UT-13 — "Evidence" nav entry appears after "Research" and is styled correctly (ux)

**Type:** ux
**Priority:** P2
**Surface:** Sidebar navigation

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Look at the left sidebar navigation menu
3. Find the "Research" entry in the sidebar
4. Look at the entry immediately after "Research" in the sidebar list

**Expected Result:**
- The entry immediately after "Research" is labeled "Evidence"
- A ShieldCheck-style icon (shield with a checkmark) appears to the left of the "Evidence" label
- The "Evidence" link is visible without scrolling the sidebar
- The overall sidebar order places "Evidence" directly after "Research" (not before it and not at the bottom)

---

### UT-14 — Evidence page subtitle describes ledger purpose clearly (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Read the subtitle or description text that appears below the "Evidence" page heading

**Expected Result:**
- A subtitle or explanatory text is visible beneath the "Evidence" heading
- The subtitle references "certified-claims ledger" or similar phrasing that explains the purpose of the page
- An operator unfamiliar with the project can understand from the heading + subtitle alone that this page tracks verified/certified signal claims

---

### UT-15 — Loading skeleton appears while /evidence data loads (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Browser DevTools available for network throttling

**Steps:**
1. Open browser DevTools (F12) > Network tab
2. Set network throttling to "Slow 3G" (or the slowest available preset)
3. Navigate to `http://localhost:3255/evidence`
4. Observe the page during the brief loading window before content appears

**Expected Result:**
- An animated skeleton card or placeholder shape is visible in the main content area while the API call is in flight
- The skeleton disappears and is replaced by the actual content (empty state card) once the data arrives
- The page heading "Evidence" is visible even during loading — only the content area shows the skeleton

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /evidence page loads without error | smoke | P1 | `/evidence` |
| UT-02 | /stocks leaderboard loads with evidence chips | smoke | P1 | `/stocks` |
| UT-03 | Stock detail page loads with evidence chips | smoke | P1 | `/stocks/[ticker]` |
| UT-04 | User clicks "Evidence" nav link and lands on /evidence | happy-path | P1 | sidebar / `/evidence` |
| UT-05 | All three evidence chips visible on every leaderboard row | happy-path | P1 | `/stocks` |
| UT-06 | Evidence page shows honest empty state | happy-path | P1 | `/evidence` |
| UT-07 | Evidence empty state lists all five claim fields | happy-path | P1 | `/evidence` |
| UT-08 | Stock detail shows evidence chips on all three score cards | happy-path | P1 | `/stocks/[ticker]` |
| UT-09 | Evidence API failure degrades gracefully on leaderboard | error | P2 | `/stocks` |
| UT-10 | /evidence shows "Backend unavailable" card when API fails | error | P2 | `/evidence` |
| UT-11 | Leaderboard scores, grades, row order unchanged | regression | P1 | `/stocks` |
| UT-12 | Stock detail ScoreCard content unchanged | regression | P1 | `/stocks/[ticker]` |
| UT-13 | "Evidence" nav entry after "Research", correctly styled | ux | P2 | sidebar |
| UT-14 | Evidence page subtitle describes ledger purpose | ux | P2 | `/evidence` |
| UT-15 | Loading skeleton appears while /evidence data loads | ux | P3 | `/evidence` |

**P1 tests (UT-01 through UT-08, UT-11, UT-12) must all pass for browser QA verdict to be PASS.**
