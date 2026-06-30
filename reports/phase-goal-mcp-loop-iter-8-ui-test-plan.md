# Phase goal-mcp-loop-iter-8 — UI Test Plan

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /research/factor-lab loads with Evidence column present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and `/api/evidence` is reachable

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load (factors table is visible)
3. Look at the column headers of the factors table

**Expected Result:**
- Page renders without a blank screen, error message, or JavaScript crash
- The factors table is visible with its existing columns
- A column header reading exactly "Evidence (D10 · 20d)" is present to the right of the existing statistics columns
- No red error banner or "Something went wrong" message appears anywhere on the page

---

### UT-02 — /evidence page loads with four claim rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and `/api/evidence` returns all four certified-claims entries

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load
3. Count the number of claim rows visible on the page (scroll if needed)

**Expected Result:**
- Page renders without a blank screen or error message
- Exactly four claim rows are present on the page: Leadership Score, Breakout-watch, ma_stack, and vcp_contraction
- No "Failed to load" or empty-state message replaces the claim list

---

### UT-03 — vcp_contraction "Proven" badge appears on factor lab with correct styling (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` is returning the 4-entry ledger including the vcp_contraction PASS entry
- Page at `/research/factor-lab` is loaded

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the factors table to load
3. Scroll down to locate the row for the **vcp_contraction** factor
4. Look at the "Evidence (D10 · 20d)" cell on that row

**Expected Result:**
- The vcp_contraction row's evidence cell contains a chip reading exactly **"Proven"**
- The chip is rendered in an accent color (not muted/grey), visually distinct from "Not yet proven" chips on other rows
- A ShieldCheck icon is visible inside or beside the "Proven" chip
- The chip appears as a clickable link (underline or pointer cursor on hover)

---

### UT-04 — "Proven" badge on vcp_contraction deep-links to evidence anchor (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` → `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- UT-03 passes (vcp_contraction "Proven" badge is visible and is a link)
- Browser is at `http://localhost:3255/research/factor-lab`

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Scroll to the vcp_contraction factor row
3. Click the **"Proven"** badge/chip on the vcp_contraction row
4. Wait for navigation to complete

**Expected Result:**
- Browser navigates to `/evidence` with the URL hash `#factor-vcp_contraction-d10-h20` — the full URL should be `http://localhost:3255/evidence#factor-vcp_contraction-d10-h20`
- The vcp_contraction claim row on the Evidence page is scrolled into view (visible in the viewport without manual scrolling)
- The vcp_contraction factor row on the factor lab page was NOT expanded or collapsed by this click — it was a navigation, not a row-toggle

---

### UT-05 — /evidence vcp_contraction row renders all required fields (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` returns the vcp_contraction entry with: edge +3.33%, p-value 0.01149, register_date 2026-06-30

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll to the bottom of the claim list to locate the **vcp_contraction** row (the fourth/last row)
3. Read the title field on that row
4. Read the subtitle field on that row
5. Read the holdout edge value displayed on that row
6. Read the p-value displayed on that row
7. Read the control label displayed on that row
8. Read the registration date displayed on that row
9. Look for the linkback text at the bottom of the row

**Expected Result:**
- Title reads exactly **"vcp_contraction — top decile (D10)"**
- Subtitle reads exactly **"Out-of-sample edge — factor top decile"**
- Holdout edge reads exactly **"+3.33%"**
- P-value reads **"0.01149"** (or "p 0.01149" or "p = 0.01149" — the number must be present)
- Control label reads **"vs SPY"**
- Registration date reads **"2026-06-30"**
- The linkback text reads exactly **"Backs: Research factor lab →"**
- A forward-walk status indicator is present (same format as the other claim rows above it)

---

### UT-06 — vcp_contraction anchor scrolls row into view on direct navigation (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and the vcp_contraction claim row exists on the Evidence page

**Steps:**
1. Type `http://localhost:3255/evidence#factor-vcp_contraction-d10-h20` directly in the browser address bar and press Enter
2. Wait for the page to finish loading
3. Observe which part of the page is visible in the viewport without scrolling

**Expected Result:**
- The page loads the Evidence page
- The vcp_contraction claim row is scrolled into view — it is visible in the viewport without the operator needing to scroll manually
- The row displays the title "vcp_contraction — top decile (D10)" as described in UT-05
- The browser does NOT land on a different row or a blank anchor target

---

### UT-07 — "Backs: Research factor lab →" link on vcp_contraction row navigates back to factor lab (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence` → `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- UT-05 passes (vcp_contraction claim row is visible with "Backs: Research factor lab →" text)
- Browser is at `http://localhost:3255/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll to the vcp_contraction claim row (fourth row from top)
3. Click the **"Backs: Research factor lab →"** link on the vcp_contraction row
4. Wait for navigation to complete

**Expected Result:**
- Browser navigates to `http://localhost:3255/research/factor-lab`
- The Research factor lab page loads with the factors table visible
- The vcp_contraction row and its "Proven" badge are present in the table (confirming it is the correct destination)

---

### UT-08 — Leadership score row on /research/factor-lab shows "Proven" chip linking to signal-leadership_score (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` includes the leadership_score PASS entry

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the factors table to load
3. Scroll to locate the **Leadership score** factor row
4. Look at the "Evidence (D10 · 20d)" cell on that row
5. Click the **"Proven"** chip on the Leadership score row
6. Wait for navigation to complete

**Expected Result:**
- The Leadership score row's evidence cell contains a chip reading exactly **"Proven"** (accent color, ShieldCheck icon)
- After clicking, the browser navigates to `http://localhost:3255/evidence#signal-leadership_score` (the score-based anchor, not a cohort anchor)
- The Leadership claim row on the Evidence page is scrolled into view

---

### UT-09 — ma_stack badge shows "Not yet proven" with no link (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` includes the ma_stack FAIL entry

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the factors table to load
3. Scroll to locate the **ma_stack** factor row
4. Look at the "Evidence (D10 · 20d)" cell on that row
5. Attempt to click the badge on the ma_stack row

**Expected Result:**
- The ma_stack row's evidence cell contains a chip reading exactly **"Not yet proven"**
- The chip is rendered in a muted or default color (not the accent green used for "Proven")
- An outline Shield icon (not a filled ShieldCheck) is visible inside or beside the chip
- The chip does NOT have an underline or link appearance — it is not clickable
- Clicking the chip does NOT navigate to `/evidence` or any other page
- The ma_stack factor row itself remains unchanged (not expanded or collapsed) after the click attempt

---

### UT-10 — All non-proven factor rows show "Not yet proven" with no link (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` is running (only vcp_contraction and leadership_score have PASS verdicts)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the factors table to load
3. Scan every factor row that is NOT vcp_contraction and NOT Leadership score
4. For each of those rows, look at the "Evidence (D10 · 20d)" cell

**Expected Result:**
- Every factor row that is not vcp_contraction and not Leadership score shows a chip reading exactly **"Not yet proven"**
- None of these "Not yet proven" chips have an underline or appear as a link
- None of these chips use the accent color reserved for "Proven"
- No factor row outside of vcp_contraction and Leadership score shows a ShieldCheck icon

---

### UT-11 — Evidence fetch failure causes all badges to show "Not yet proven" (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` is unavailable or returns a non-200 response (simulate by stopping the backend or using browser DevTools to block the request)

**Steps:**
1. If using DevTools: open Browser DevTools, go to the Network tab, add a request block for `*/api/evidence`
2. Navigate to `http://localhost:3255/research/factor-lab`
3. Wait for the factors table to load
4. Observe all badges in the "Evidence (D10 · 20d)" column, including the vcp_contraction and Leadership score rows

**Expected Result:**
- The factors table still loads and renders all factor rows (the table does NOT disappear on evidence fetch failure)
- Every badge in the "Evidence (D10 · 20d)" column reads **"Not yet proven"**, including the rows that would normally show "Proven"
- No JavaScript error overlay or crash screen is displayed
- No "Proven" chip or ShieldCheck icon appears anywhere in the table

---

### UT-12 — ma_stack row on /evidence shows updated framing and correct verdict (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend `/api/evidence` includes the ma_stack FAIL entry

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll to locate the **ma_stack** claim row (third row from top, between Breakout-watch and vcp_contraction)
3. Read the title field on that row
4. Read the subtitle field on that row
5. Look at the verdict chip on that row
6. Look for the linkback text at the bottom of that row

**Expected Result:**
- Title reads exactly **"ma_stack — top decile (D10)"** (not a generic untitled label)
- Subtitle reads exactly **"Out-of-sample edge — factor top decile"**
- The verdict chip reads **"Not yet proven"** (the ma_stack edge FAILED — this must NOT read "Proven")
- The linkback text reads **"Backs: Research factor lab →"**

---

### UT-13 — /evidence leadership_score anchor still scrolls row into view (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running with the leadership_score claim entry present

**Steps:**
1. Type `http://localhost:3255/evidence#signal-leadership_score` directly in the browser address bar and press Enter
2. Wait for the page to finish loading
3. Observe which part of the page is visible in the viewport without scrolling

**Expected Result:**
- The Leadership claim row is scrolled into view and is visible in the viewport without manual scrolling
- The Leadership row still displays the linkback **"Backs: Stocks leaderboard →"** (not "Backs: Research factor lab →")
- The Leadership row's anchor id has NOT been replaced by a cohort anchor — the URL hash `#signal-leadership_score` correctly targets the Leadership row

---

### UT-14 — /evidence Breakout-watch row is unchanged after iter-8 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend includes the Breakout-watch regime-conditioned evidence claim

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll to locate the **Breakout-watch** claim row (second row from top)
3. Read the hypothesis/title text on that row
4. Read the linkback text on that row

**Expected Result:**
- The Breakout-watch row hypothesis/title contains **"Regime: Risk-on"** (exact text)
- The linkback does NOT read "Backs: Research factor lab →" — it links to a non-factor-lab research surface
- The row content is identical to what it showed before this iteration's changes

---

### UT-15 — /stocks page shows Leadership "Proven", Entry Quality and Risk "Not yet proven", no vcp_contraction badge (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is fully running with the evidence payload populated

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard to load
3. Look at the score column header badges for Leadership, Entry Quality, and Risk on at least the first three stock rows
4. Search the entire visible page for any label or badge containing the text "vcp_contraction"

**Expected Result:**
- The Leadership score column shows a **"Proven"** badge
- The Entry Quality score column shows a **"Not yet proven"** badge
- The Risk score column shows a **"Not yet proven"** badge
- The text "vcp_contraction" does NOT appear anywhere on the `/stocks` page — no badge, no column, no label

---

### UT-16 — /stocks/{ticker} Leadership proof drill-down panel still renders (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255
- At least one stock ticker is visible on the `/stocks` leaderboard

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on the first stock ticker visible in the leaderboard
3. Wait for the stock detail page to load at `/stocks/{ticker}`
4. Locate the **Leadership score** section on the detail page
5. Click the "Proven" badge or proof-expansion control next to the Leadership score

**Expected Result:**
- The proof drill-down panel opens without a crash or blank state
- The panel shows an out-of-sample test result (e.g., text referencing "SPY" or "holdout")
- The panel shows **"vs SPY"** as the control comparison label
- The panel shows a certification date (format: YYYY-MM-DD)
- The panel content is identical to what displayed before this iteration (no regression in rendering)

---

### UT-17 — vcp_contraction row click does NOT toggle factor row expansion (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- vcp_contraction "Proven" badge is visible (UT-03 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Scroll to the vcp_contraction factor row
3. Note the current expansion state of the vcp_contraction factor row (expanded or collapsed)
4. Click the **"Proven"** badge on the vcp_contraction row
5. Immediately before the navigation completes (or after pressing Back), observe whether the row expansion state changed

**Expected Result:**
- Clicking the "Proven" badge initiates navigation to `/evidence#factor-vcp_contraction-d10-h20`
- The vcp_contraction factor row does NOT expand or collapse as a result of this click — the badge click is a navigation action only, not a row-toggle
- Clicking elsewhere on the vcp_contraction row body (not on the badge) still toggles the row expansion as before

---

### UT-18 — Evidence column is discoverable without extra steps from factor lab (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Without scrolling horizontally, look at the factors table column headers
3. Without any filtering or toggling, look at the evidence status of the vcp_contraction row

**Expected Result:**
- The "Evidence (D10 · 20d)" column header is visible in the default table view without needing to enable a setting or toggle a column
- The "Proven" badge on the vcp_contraction row is visible without needing to expand or click on the row first
- A new user would be able to identify the "Proven" badge as a clickable link from its visual styling (accent color, link cursor) without needing instructions

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /research/factor-lab loads with Evidence column present | smoke | P1 | `/research/factor-lab` |
| UT-02 | /evidence page loads with four claim rows | smoke | P1 | `/evidence` |
| UT-03 | vcp_contraction "Proven" badge appears with correct styling | happy-path | P1 | `/research/factor-lab` |
| UT-04 | "Proven" badge on vcp_contraction deep-links to evidence anchor | happy-path | P1 | `/research/factor-lab` → `/evidence` |
| UT-05 | /evidence vcp_contraction row renders all required fields | happy-path | P1 | `/evidence` |
| UT-06 | vcp_contraction anchor scrolls row into view on direct navigation | happy-path | P1 | `/evidence` |
| UT-07 | "Backs: Research factor lab →" link navigates back to factor lab | happy-path | P1 | `/evidence` → `/research/factor-lab` |
| UT-08 | Leadership score row shows "Proven" chip linking to signal-leadership_score | happy-path | P1 | `/research/factor-lab` |
| UT-09 | ma_stack badge shows "Not yet proven" with no link | validation | P2 | `/research/factor-lab` |
| UT-10 | All non-proven factor rows show "Not yet proven" with no link | validation | P2 | `/research/factor-lab` |
| UT-11 | Evidence fetch failure causes all badges to show "Not yet proven" | error | P2 | `/research/factor-lab` |
| UT-12 | ma_stack row on /evidence shows updated framing and correct verdict | regression | P1 | `/evidence` |
| UT-13 | /evidence leadership_score anchor still scrolls row into view | regression | P1 | `/evidence` |
| UT-14 | /evidence Breakout-watch row is unchanged after iter-8 | regression | P1 | `/evidence` |
| UT-15 | /stocks page shows correct score badges and no vcp_contraction badge | regression | P1 | `/stocks` |
| UT-16 | /stocks/{ticker} Leadership proof drill-down panel still renders | regression | P1 | `/stocks/{ticker}` |
| UT-17 | vcp_contraction row click does NOT toggle factor row expansion | ux | P2 | `/research/factor-lab` |
| UT-18 | Evidence column is discoverable without extra steps from factor lab | ux | P2 | `/research/factor-lab` |

**P1 tests must all pass for browser QA verdict to be PASS.**
