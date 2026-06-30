# Phase goal-mcp-loop-iter-2 — UI Test Plan

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- API and unit tests covered by QA test plan (TC-XX) are not duplicated here. -->

---

### UT-01 — Stock detail page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running (at least one stock exists in the database)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to render (stock rows visible)
3. Click on any stock ticker in the first visible row
4. Wait for the stock detail page to fully load

**Expected Result:**
- Stock detail page renders at a URL matching `http://localhost:3255/stocks/{ticker}` (e.g., `/stocks/AAPL`)
- Page shows at least three score cards: Leadership, Entry Quality, and Risk
- No blank screen, "Something went wrong" message, or error overlay is visible
- The Leadership score card is visible and shows a numeric score value

---

### UT-02 — "Why proven?" toggle is present on the Leadership score card (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255
- A stock detail page is open (from UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker to open its detail page
3. Locate the Leadership score card on the detail page

**Expected Result:**
- The Leadership score card displays a badge chip reading exactly "Proven" (styled in accent green, not grayed out)
- Immediately below or adjacent to the "Proven" badge, a button or disclosure labeled "Why proven?" is visible
- The "Why proven?" element shows a chevron, arrow, or similar indicator that it is expandable

---

### UT-03 — Stocks leaderboard page loads with "Proven" badge in Leadership column (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to render
3. Locate the "Leadership" column header and the first data row beneath it

**Expected Result:**
- The page renders without blank screen or error message
- The Leadership column is visible in the leaderboard table
- The Leadership score badge in the first visible stock row reads "Proven" in accent green styling (not "Not yet proven")

---

### UT-04 — Evidence page loads with the leadership_score claim row (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without blank screen or error message
- At least one claim row is visible (the page is not in its previous empty state)
- A row labeled or anchored as `leadership_score` is present on the page

---

### UT-05 — Expand "Why proven?" panel and verify it shows OOS test result (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255
- A stock detail page is open with the Leadership score card visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker to open its detail page
3. Locate the Leadership score card with the "Proven" badge
4. Click the "Why proven?" disclosure button below the badge
5. Wait for the proof panel to expand (approximately 0.5 seconds animation)
6. Look at the "Out-of-sample test" section within the expanded panel

**Expected Result:**
- The proof panel becomes visible below the "Why proven?" button
- The out-of-sample section shows a chip or label reading "PASS" (not "FAIL" or blank)
- The holdout edge value reads "+6.36%" (or "6.36%")
- The p-value reads "0.0004998" (or "p ≈ 0.0005")
- A cohort size reference (e.g., "12,297 observations" or "n=12297") is visible

---

### UT-06 — Proof panel shows SPY benchmark control comparison (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- A stock detail page is open and the "Why proven?" panel is expanded (follow steps 1–4 from UT-05)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker to open its detail page
3. Click the "Why proven?" button on the Leadership score card
4. Within the expanded proof panel, locate the control comparison section

**Expected Result:**
- A row or field is visible with the label "vs SPY (benchmark control)" or "SPY benchmark control"
- The value shown reads "+6.36%" (or "6.36%")
- The word "SPY" is explicitly visible in the label (not just a number without context)
- No other benchmark tickers (QQQ, sector ETF) are listed alongside SPY

---

### UT-07 — Proof panel shows certified claim id and registration date (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- A stock detail page is open and the "Why proven?" panel is expanded (follow steps 1–4 from UT-05)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker to open its detail page
3. Click the "Why proven?" button on the Leadership score card
4. Within the expanded proof panel, locate the certified claim section

**Expected Result:**
- The claim identifier reads "leadership_score · registered 2026-06-30" (exact text, including the center-dot separator)
- The registration date shown is exactly "2026-06-30"
- A clickable link labeled "View backing evidence row →" is present within the claim section

---

### UT-08 — "View backing evidence row →" link navigates to evidence page anchor (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}` → `/evidence`

**Preconditions:**
- A stock detail page is open and the "Why proven?" panel is expanded (follow steps 1–4 from UT-05)
- The "View backing evidence row →" link is visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker
3. Click the "Why proven?" button on the Leadership score card
4. Click the "View backing evidence row →" link inside the expanded proof panel
5. Wait for the page to load

**Expected Result:**
- Browser navigates to the Evidence page
- The URL in the address bar reads `http://localhost:3255/evidence#signal-leadership_score`
- The page auto-scrolls so the `leadership_score` claim row is visible in the viewport (the row with the leadership_score header or label is not hidden above the fold)

---

### UT-09 — Evidence page leadership_score claim row shows all five required fields (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the claim row for leadership_score
3. Inspect the row for each of the five fields listed in the expected result below

**Expected Result:**
- Field 1 — Hypothesis: A description mentioning "leadership_score" or "top decile" (not blank)
- Field 2 — Out-of-sample verdict: A chip or label reading "PASS" and a value of approximately "+6.36% edge" and "p ≈ 0.0005"
- Field 3 — SPY benchmark control: A value of approximately "+6.36%" with "vs SPY" or "SPY" label visible
- Field 4 — Registration date: The date "2026-06-30" is visible
- Field 5 — Forward-walk status: A label such as "Pending" or "In progress" (not blank)
- All five fields are populated — none show blank, "N/A", or placeholder dashes

---

### UT-10 — "Backs: Stocks leaderboard →" link on evidence page navigates to /stocks (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence` → `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The leadership_score claim row is visible on the evidence page

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the leadership_score claim row
3. Within that row, find the link labeled "Backs: Stocks leaderboard →"
4. Click "Backs: Stocks leaderboard →"
5. Wait for navigation to complete

**Expected Result:**
- Browser navigates to `http://localhost:3255/stocks`
- The Stocks leaderboard table renders with stock rows visible
- No error page or blank screen appears

---

### UT-11 — Full round-trip navigation: leaderboard → detail → proof panel → evidence → leaderboard (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`, `/stocks/{ticker}`, `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker in the leaderboard to open its detail page
3. On the detail page, click "Why proven?" on the Leadership score card
4. In the expanded proof panel, click "View backing evidence row →"
5. On the `/evidence` page, confirm the URL shows `#signal-leadership_score`
6. Click "Backs: Stocks leaderboard →" in the leadership_score claim row
7. Confirm the browser returns to `/stocks`

**Expected Result:**
- Each navigation step completes successfully — no error pages, 404 pages, or blank screens
- The final URL is `http://localhost:3255/stocks`
- The leaderboard table is visible with stock rows

---

### UT-12 — Stocks leaderboard "Proven" badge clicks through to /evidence#signal-leadership_score (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Locate the Leadership score badge in the first visible stock row — it should read "Proven"
3. Click the "Proven" badge chip in the Leadership column

**Expected Result:**
- Browser navigates to `http://localhost:3255/evidence#signal-leadership_score`
- The leadership_score claim row is visible on the evidence page
- The URL in the address bar includes the `#signal-leadership_score` fragment

---

### UT-13 — Entry Quality score card on stock detail has no "Why proven?" toggle (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- A stock detail page is open at `http://localhost:3255/stocks/{ticker}`

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker to open its detail page
3. Locate the Entry Quality score card
4. Observe whether a "Why proven?" button or any disclosure/expand control is present

**Expected Result:**
- The Entry Quality badge reads "Not yet proven" (not "Proven")
- No "Why proven?" button, toggle, chevron, or expandable panel is present on the Entry Quality score card
- The Entry Quality score card appears identical in structure to its state before this phase

---

### UT-14 — Risk score card on stock detail has no "Why proven?" toggle (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- A stock detail page is open at `http://localhost:3255/stocks/{ticker}`

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on any stock ticker to open its detail page
3. Locate the Risk score card
4. Observe whether a "Why proven?" button or any disclosure/expand control is present

**Expected Result:**
- The Risk badge reads "Not yet proven" (not "Proven")
- No "Why proven?" button, toggle, chevron, or expandable panel is present on the Risk score card
- The Risk score card appears identical in structure to its state before this phase

---

### UT-15 — Entry Quality and Risk columns on the stocks leaderboard still read "Not yet proven" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to render
3. Locate the Entry Quality column in the first visible stock row
4. Observe the badge text
5. Locate the Risk column in the same stock row
6. Observe the badge text

**Expected Result:**
- The Entry Quality badge reads "Not yet proven"
- The Risk badge reads "Not yet proven"
- Neither badge is styled with the same accent green color used for the Leadership "Proven" badge

---

### UT-16 — "Why proven?" panel collapses when toggle is clicked a second time (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- A stock detail page is open with the Leadership score card visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click any stock ticker to open its detail page
3. Click the "Why proven?" button to expand the proof panel — confirm the panel is visible
4. Click the "Why proven?" button again (or the close/collapse control now showing)

**Expected Result:**
- The proof panel collapses — its contents (OOS test, SPY control, claim id) become hidden
- The "Why proven?" button remains visible and clickable after collapse
- No page error or scroll jump occurs during the collapse animation

---

### UT-17 — "Why proven?" feature is discoverable within 2 clicks from the leaderboard (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`, `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks` (the starting point)
2. Without any prior instructions, look at the Leadership score badges — count the clicks needed to reach the proof panel
3. Click 1: click any stock ticker row
4. Click 2: click "Why proven?" on the Leadership score card

**Expected Result:**
- The proof panel content is fully visible after exactly 2 clicks from the leaderboard
- The "Why proven?" label is self-explanatory — an operator unfamiliar with the app can understand it without documentation
- The expanded panel's content (PASS chip, percentages, dates) reads naturally in plain English without requiring developer context

---

### UT-18 — Leadership "Proven" badge on leaderboard is visually distinct from "Not yet proven" badges (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Look at any visible stock row with all three score badges (Leadership, Entry Quality, Risk) side by side
3. Compare the visual styling of the Leadership badge with the Entry Quality and Risk badges

**Expected Result:**
- The Leadership "Proven" badge is styled in an accent green or primary color
- The Entry Quality and Risk "Not yet proven" badges are styled in a neutral, muted, or gray color
- The visual contrast between the "Proven" and "Not yet proven" badges is immediately apparent without reading the text

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stock detail page loads without errors | smoke | P1 | `/stocks/{ticker}` |
| UT-02 | "Why proven?" toggle is present on Leadership score card | smoke | P1 | `/stocks/{ticker}` |
| UT-03 | Stocks leaderboard page loads with "Proven" badge | smoke | P1 | `/stocks` |
| UT-04 | Evidence page loads with leadership_score claim row | smoke | P1 | `/evidence` |
| UT-05 | Expand "Why proven?" panel shows OOS test result | happy-path | P1 | `/stocks/{ticker}` |
| UT-06 | Proof panel shows SPY benchmark control comparison | happy-path | P1 | `/stocks/{ticker}` |
| UT-07 | Proof panel shows certified claim id and registration date | happy-path | P1 | `/stocks/{ticker}` |
| UT-08 | "View backing evidence row →" link navigates to evidence anchor | happy-path | P1 | `/stocks/{ticker}` → `/evidence` |
| UT-09 | Evidence claim row shows all five required fields | happy-path | P1 | `/evidence` |
| UT-10 | "Backs: Stocks leaderboard →" link navigates to /stocks | happy-path | P1 | `/evidence` → `/stocks` |
| UT-11 | Full round-trip: leaderboard → detail → proof panel → evidence → leaderboard | happy-path | P1 | multi-surface |
| UT-12 | Stocks leaderboard "Proven" badge links to /evidence anchor | regression | P1 | `/stocks` |
| UT-13 | Entry Quality score card has no "Why proven?" toggle | regression | P1 | `/stocks/{ticker}` |
| UT-14 | Risk score card has no "Why proven?" toggle | regression | P1 | `/stocks/{ticker}` |
| UT-15 | Entry Quality and Risk leaderboard badges read "Not yet proven" | regression | P1 | `/stocks` |
| UT-16 | "Why proven?" panel collapses on second click | ux | P2 | `/stocks/{ticker}` |
| UT-17 | "Why proven?" feature discoverable within 2 clicks | ux | P2 | `/stocks`, `/stocks/{ticker}` |
| UT-18 | "Proven" badge visually distinct from "Not yet proven" badges | ux | P2 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.**
