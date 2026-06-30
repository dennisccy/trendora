# Phase goal-mcp-loop-iter-3 — UI Test Plan

**Phase:** goal-mcp-loop-iter-3
**Date:** 2026-06-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context

No frontend source files were modified this iteration. The only code change was to `scripts/start-frontend.sh` (a QA infrastructure script — not part of the deployed product). All test cases below are regression and smoke tests verifying that the evidence layer surfaces already shipped in earlier iterations render correctly.

Surfaces tested: `/stocks`, `/stocks/{ticker}`, `/evidence`.

---

## Test Cases

---

### UT-01 — Stocks leaderboard page loads without errors

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255 and `/api/health` returns 200

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to fully load (leaderboard rows appear)

**Expected Result:**
- Page renders without a blank screen or error message
- The leaderboard table is visible with at least 5 rows populated
- No "Checking backend…" spinner is present
- No "Backend unavailable" message is present

---

### UT-02 — Leadership column displays green "Proven" chip on every visible row

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` leaderboard is loaded and shows at least 5 rows

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to populate
3. Locate the Leadership column in the table header
4. Examine the evidence badge in the Leadership column on the first 5 visible rows

**Expected Result:**
- Every row shows a green (accent-colored) chip with the text "Proven" in the Leadership column
- No row in the Leadership column is blank or shows "Not yet proven"
- The chip color is visually distinct from grey/muted chips

---

### UT-03 — Entry Quality column displays muted "Not yet proven" chip

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` leaderboard is loaded and shows at least 5 rows

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to populate
3. Locate the Entry Quality column in the table header
4. Examine the evidence badge in the Entry Quality column on the first 5 visible rows
5. Click one of the "Not yet proven" chips in the Entry Quality column

**Expected Result:**
- Every row shows a muted (grey) chip with the text "Not yet proven" in the Entry Quality column
- Clicking the chip does NOT open a drill-down panel or "Why proven?" toggle
- The chip color is visually duller than the green "Proven" chip in the Leadership column

---

### UT-04 — Risk column displays muted "Not yet proven" chip

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` leaderboard is loaded and shows at least 5 rows

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to populate
3. Locate the Risk column in the table header
4. Examine the evidence badge in the Risk column on the first 5 visible rows
5. Click one of the "Not yet proven" chips in the Risk column

**Expected Result:**
- Every row shows a muted (grey) chip with the text "Not yet proven" in the Risk column
- Clicking the chip does NOT open a drill-down panel or "Why proven?" toggle
- The chip is styled identically to the Entry Quality "Not yet proven" chip

---

### UT-05 — Health badge reads "Ready" when both services are up

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255 and `/api/health` returns 200

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to fully load
3. Locate the health status badge (typically in the header or top of the page)

**Expected Result:**
- The health badge reads "Ready" (not "Checking backend…" and not "Backend unavailable")
- The badge is present and visible on the page
- The leaderboard rows are populated (not empty), confirming the backend connection is live

---

### UT-06 — Stock detail page for MU loads with three score cards

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/MU`

**Preconditions:**
- `/stocks` leaderboard is loaded
- MU ticker is present in the leaderboard (or navigate directly)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard to populate
3. Click the row for ticker "MU" to navigate to its detail page (alternatively navigate directly to `http://localhost:3255/stocks/MU`)
4. Wait for the detail page to fully load

**Expected Result:**
- Page renders at URL `/stocks/MU` (or `/stocks/MU?as_of=...`)
- Three score cards are visible: one labeled "Leadership", one labeled "Entry Quality", and one labeled "Risk"
- No blank screen, no "404", and no error message

---

### UT-07 — Leadership score card "Why proven?" toggle expands proof panel

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/MU`

**Preconditions:**
- Stock detail page for MU is open at `/stocks/MU`
- All three score cards are visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks/MU`
2. Locate the Leadership score card
3. Find the "Why proven?" button or toggle on the Leadership card
4. Click the "Why proven?" button

**Expected Result:**
- A proof panel expands below or within the Leadership card
- The panel is visible and contains text (not blank)
- The panel includes the word "PASS" as the OOS verdict
- The "Why proven?" button is still visible and the panel remains open

---

### UT-08 — Expanded proof panel displays correct OOS evidence values

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/MU`

**Preconditions:**
- Stock detail page for MU is open
- "Why proven?" panel is expanded on the Leadership card (see UT-07)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/MU`
2. Click "Why proven?" on the Leadership score card to expand the proof panel
3. Read the values displayed in the expanded panel

**Expected Result:**
- The panel displays "PASS" as the out-of-sample verdict
- The panel shows a holdout edge value of "+6.36%"
- The panel shows a p-value of approximately "0.0005" (displayed as "p ≈ 0.0005" or "p-value: 0.0005")
- The panel shows a cohort size of "n = 12,297" (or "n = 12297")
- The panel shows "vs SPY" as the benchmark control
- The panel shows the claim id "leadership_score"
- The panel shows the registration date "2026-06-30" (displayed as "registered 2026-06-30" or similar)

---

### UT-09 — "View backing evidence row" link navigates to evidence anchor

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/MU`

**Preconditions:**
- Stock detail page for MU is open
- "Why proven?" panel is expanded on the Leadership card

**Steps:**
1. Navigate to `http://localhost:3255/stocks/MU`
2. Click "Why proven?" on the Leadership score card to expand the proof panel
3. Locate the link labeled "View backing evidence row →" inside the expanded panel
4. Click the "View backing evidence row →" link

**Expected Result:**
- Browser navigates to `/evidence` (URL becomes `http://localhost:3255/evidence` or `http://localhost:3255/evidence#signal-leadership_score`)
- The evidence ledger page is visible
- The `leadership_score` claim row is visible on the page (scrolled into view if anchored)

---

### UT-10 — Entry Quality score card has no "Why proven?" toggle

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/MU`

**Preconditions:**
- Stock detail page for MU is open at `/stocks/MU`
- All three score cards are visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks/MU`
2. Locate the Entry Quality score card
3. Examine the card for any "Why proven?" button, toggle, or drill-down element

**Expected Result:**
- The Entry Quality card does NOT contain a "Why proven?" button or any interactive proof drill-down
- The card shows the score value and the "Not yet proven" badge only
- No panel expands when clicking on the card or its badge

---

### UT-11 — Risk score card has no "Why proven?" toggle

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/MU`

**Preconditions:**
- Stock detail page for MU is open at `/stocks/MU`
- All three score cards are visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks/MU`
2. Locate the Risk score card
3. Examine the card for any "Why proven?" button, toggle, or drill-down element

**Expected Result:**
- The Risk card does NOT contain a "Why proven?" button or any interactive proof drill-down
- The card shows the score value and the "Not yet proven" badge only
- No panel expands when clicking on the card or its badge

---

### UT-12 — Evidence ledger page loads with leadership_score row

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and `/api/evidence` returns data with `leadership_score` present

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- A table or list of evidence claims is visible
- At least one row is labeled or keyed with "leadership_score"
- No "404" and no error state

---

### UT-13 — leadership_score claim row shows all five required evidence fields

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` page is loaded and the `leadership_score` row is visible

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the ledger to load
3. Locate the row for `leadership_score`
4. Read all visible fields in that row

**Expected Result:**
- The row contains a hypothesis statement (non-empty text describing what leadership_score measures)
- The row shows "PASS" as the OOS verdict
- The row shows "+6.36%" as the holdout edge
- The row shows "SPY" as the benchmark control
- The row shows the registration date "2026-06-30"
- No field is blank or shows a placeholder like "N/A" or "—"

---

### UT-14 — "Backs: Stocks leaderboard" link returns to /stocks

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` page is loaded and the `leadership_score` row is visible

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the ledger to load
3. Locate the `leadership_score` row
4. Find the link labeled "Backs: Stocks leaderboard →" within that row
5. Click "Backs: Stocks leaderboard →"

**Expected Result:**
- Browser navigates to `/stocks` (URL becomes `http://localhost:3255/stocks` or `/stocks?as_of=...`)
- The leaderboard is visible with populated rows
- The Leadership column still shows the green "Proven" chip on all visible rows

---

### UT-15 — "Proven" badge is visually distinct from "Not yet proven" badges

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` leaderboard is loaded and shows at least 5 rows
- Leadership, Entry Quality, and Risk columns are all visible

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard to populate
3. Look at the Leadership column and the Entry Quality column side by side on any row

**Expected Result:**
- The Leadership "Proven" chip is clearly different in color/styling from the Entry Quality and Risk "Not yet proven" chips
- The difference is immediately visible without clicking — an operator can distinguish the two states at a glance
- The "Proven" chip appears in an accent or positive color (e.g., green); the "Not yet proven" chips appear muted (e.g., grey)

---

### UT-16 — Evidence proof drill-down is discoverable within 2 clicks from leaderboard

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`, `/stocks/{ticker}`

**Preconditions:**
- `/stocks` leaderboard is loaded and shows at least 1 row with a "Proven" chip in the Leadership column

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click any stock ticker row to open its detail page (1st click)
3. On the detail page, click "Why proven?" on the Leadership card (2nd click)

**Expected Result:**
- After 2 clicks from the leaderboard, the proof panel is visible and expanded
- The panel shows the OOS PASS result and numeric evidence values
- No additional navigation steps are required to reach the proof

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stocks leaderboard page loads without errors | smoke | P1 | `/stocks` |
| UT-02 | Leadership column displays green "Proven" chip | regression | P1 | `/stocks` |
| UT-03 | Entry Quality column displays "Not yet proven" chip | regression | P1 | `/stocks` |
| UT-04 | Risk column displays "Not yet proven" chip | regression | P1 | `/stocks` |
| UT-05 | Health badge reads "Ready" when both services are up | regression | P1 | `/stocks` |
| UT-06 | Stock detail page for MU loads with three score cards | smoke | P1 | `/stocks/MU` |
| UT-07 | Leadership "Why proven?" toggle expands proof panel | happy-path | P1 | `/stocks/MU` |
| UT-08 | Expanded proof panel displays correct OOS evidence values | regression | P1 | `/stocks/MU` |
| UT-09 | "View backing evidence row" link navigates to evidence anchor | regression | P1 | `/stocks/MU` |
| UT-10 | Entry Quality score card has no "Why proven?" toggle | regression | P1 | `/stocks/MU` |
| UT-11 | Risk score card has no "Why proven?" toggle | regression | P1 | `/stocks/MU` |
| UT-12 | Evidence ledger page loads with leadership_score row | smoke | P1 | `/evidence` |
| UT-13 | leadership_score claim row shows all five required evidence fields | regression | P1 | `/evidence` |
| UT-14 | "Backs: Stocks leaderboard" link returns to /stocks | regression | P1 | `/evidence` |
| UT-15 | "Proven" badge is visually distinct from "Not yet proven" badges | ux | P2 | `/stocks` |
| UT-16 | Evidence proof drill-down is discoverable within 2 clicks | ux | P2 | `/stocks`, `/stocks/{ticker}` |

**P1 tests must all pass for browser QA verdict to be PASS.**

Note: These are human-executable regression tests for surfaces that are unchanged but were browser-verified this iteration. The API-level checks (byte-identical value comparison, empty-ledger 200, backend-down health badge) are covered by the functional test plan (TC series) and are not duplicated here.
