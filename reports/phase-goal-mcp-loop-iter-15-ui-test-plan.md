# Phase goal-mcp-loop-iter-15 — UI Test Plan

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /evidence page loads with 7 rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- The canonical ledger (`certified-claims.jsonl`) contains 7 rows

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load (all rows visible, no loading spinner)
3. Count the number of claim rows displayed on the page

**Expected Result:**
- Page renders without a blank screen, crash, or "Backend unavailable" pill
- Exactly 7 claim rows are visible on the page
- A page heading or title related to "Evidence" is present
- No JavaScript errors appear in the browser console

---

### UT-02 — New rs_spy_3m D10 h60 evidence row displays correct values (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- Canonical ledger row 7 (`rs_spy_3m`, h60, PASS) is present in `certified-claims.jsonl`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load (no loading spinner, all rows rendered)
3. Scroll to the bottom of the evidence ledger list to locate the newest row
4. Locate the row titled "rs_spy_3m — top decile (D10)" with subtitle "Out-of-sample edge — factor top decile · 60-day hold"
5. Confirm the displayed out-of-sample edge reads "+21.34%"
6. Confirm the displayed p-value reads "0.0005" or "0.00050" (acceptable rounding of 0.0004997…)
7. Confirm the displayed registration date reads "2026-07-01"
8. Confirm the displayed Bonferroni divisor reads "7"
9. Confirm a "Backs: Research factor lab →" link is present within the row

**Expected Result:**
- A 7th row titled "rs_spy_3m — top decile (D10)" with subtitle "Out-of-sample edge — factor top decile · 60-day hold" is visible
- Edge value shows "+21.34%", p-value shows "0.0005" or "0.00050", registration date shows "2026-07-01", and divisor shows "7"
- A "Backs: Research factor lab →" link is present in the row
- No field is blank, "—", or missing

---

### UT-03 — Deep-link anchor #factor-rs_spy_3m-d10-h60 scrolls to rs_spy_3m row (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- The 7th evidence row (`rs_spy_3m` D10 h60) is rendered with anchor id `factor-rs_spy_3m-d10-h60`

**Steps:**
1. Navigate directly to `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60` (type the full URL including the fragment)
2. Wait for the page to fully load
3. Observe which row the browser scrolls into view

**Expected Result:**
- The browser scrolls to and places the "rs_spy_3m — top decile (D10)" row in the visible viewport
- The row with anchor `factor-rs_spy_3m-d10-h60` is highlighted or in view — NOT the page top and NOT another factor's row
- The browser URL bar shows `…/evidence#factor-rs_spy_3m-d10-h60`
- No 404 error, blank page, or unresolved anchor behavior

---

### UT-04 — /evidence page shows a graceful state when backend is unavailable (error)

**Type:** error
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is NOT running (or temporarily stopped so `/api/evidence` returns an error)

**Steps:**
1. Ensure the backend process is not running (stop the backend service)
2. Navigate to `http://localhost:3255/evidence`
3. Wait for the page to finish attempting to load

**Expected Result:**
- Page does NOT crash or show a completely blank white screen
- A visible indicator such as a "Backend unavailable" pill, error message, or empty-state placeholder is displayed
- The page remains navigable (no unhandled JavaScript exception visible in the browser console)
- The page does NOT silently display 0 rows as if the ledger is empty

---

### UT-05 — First 6 evidence rows are unchanged after iteration 15 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load
3. Scroll to view rows 1 through 6 (the rows that existed before this iteration)
4. Confirm the `vcp_contraction` h20 row is present with its existing title and field values (do NOT check rs_spy_3m for this step)
5. Confirm the `vcp_contraction` h60 row is present with its existing title and field values
6. Confirm no prior row has been removed, reordered, or had its values replaced with blanks

**Expected Result:**
- All 6 prior claim rows are present and appear in their original order
- The `vcp_contraction` h20 and h60 rows are visible with their respective verdicts and numeric values unchanged
- No existing row shows a blank value, a changed title, or a missing "Backs" link that was present before

---

### UT-06 — /research/factor-lab page loads with rs_spy_3m factor row visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load (factor table visible, no loading spinner)
3. Locate the `rs_spy_3m` factor row in the factor table

**Expected Result:**
- Page renders without blank screen, crash, or "Backend unavailable" pill
- The factor table is visible and includes an `rs_spy_3m` (or "3-month Relative Strength") factor row
- Per-horizon evidence chips are visible in the `rs_spy_3m` row (h1, h5, h10, h20, h60 columns all present)

---

### UT-07 — rs_spy_3m h60 evidence chip shows "Proven" badge (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- Canonical ledger row 7 (`rs_spy_3m`, h60, PASS) is present and served by `/api/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load
3. Locate the `rs_spy_3m` factor row in the factor table
4. Within the evidence column for `rs_spy_3m`, locate the h60 (60-day hold) evidence chip
5. Confirm the h60 chip displays the text "Proven" (not "Not yet proven")
6. Confirm the h60 chip has a visually distinct proven state — a checkmark styling, active/green pill — that is different from the muted grey of "Not yet proven"

**Expected Result:**
- The `rs_spy_3m` h60 chip reads "Proven" in a proven-checkmark pill style
- The chip is visually different from the "Not yet proven" muted state shown on h1, h5, h10, and h20 of the same row
- No "Not yet proven" text is visible on the h60 chip

---

### UT-08 — Clicking rs_spy_3m "Proven" chip navigates to /evidence#factor-rs_spy_3m-d10-h60 (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- The `rs_spy_3m` h60 chip displays "Proven" (UT-07 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load
3. Locate the `rs_spy_3m` factor row and the h60 "Proven" chip
4. Click the "Proven" chip in the h60 cell of the `rs_spy_3m` factor row

**Expected Result:**
- The browser navigates to `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60`
- The `/evidence` page loads and scrolls to the "rs_spy_3m — top decile (D10)" row (the 7th row)
- The browser URL bar shows the path ending in `/evidence#factor-rs_spy_3m-d10-h60`
- The row scrolled into view is the `rs_spy_3m` h60 row — NOT the page top and NOT another factor's row

---

### UT-09 — rs_spy_3m uncertified horizons (h1/h5/h10/h20) still show "Not yet proven" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- Only `rs_spy_3m` h60 is certified in the canonical ledger; h1, h5, h10, and h20 are NOT certified

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load
3. Locate the `rs_spy_3m` factor row in the factor table
4. Confirm the h1 chip displays "Not yet proven" and does NOT display "Proven"
5. Confirm the h5 chip displays "Not yet proven" and does NOT display "Proven"
6. Confirm the h10 chip displays "Not yet proven" and does NOT display "Proven"
7. Confirm the h20 chip displays "Not yet proven" and does NOT display "Proven"

**Expected Result:**
- All four chips — h1, h5, h10, h20 — display the muted "Not yet proven" state
- None of h1, h5, h10, or h20 show a "Proven" pill, checkmark styling, or a deep-link to any evidence row
- The h60 chip is the ONLY "Proven" chip in the `rs_spy_3m` row

---

### UT-10 — End-to-end audit trail: factor lab → "Proven" badge → evidence row → back to factor lab (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`, `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`
- `rs_spy_3m` h60 chip shows "Proven" (UT-07 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load
3. Locate the `rs_spy_3m` factor row and find the h60 "Proven" chip
4. Click the "Proven" chip
5. Wait for `http://localhost:3255/evidence#factor-rs_spy_3m-d10-h60` to load
6. Confirm the "rs_spy_3m — top decile (D10)" row is visible and in the viewport
7. Locate the "Backs: Research factor lab →" link within the `rs_spy_3m` h60 evidence row
8. Click the "Backs: Research factor lab →" link
9. Confirm the browser navigates back to `/research/factor-lab`

**Expected Result:**
- The full round-trip works without any dead ends: factor lab → h60 Proven chip → evidence row → back to factor lab
- Each step lands on the correct page with the correct content visible
- The "Backs: Research factor lab →" link is clearly visible in the evidence row and is clickable
- After clicking "Backs: Research factor lab →", the URL ends with `/research/factor-lab` (or similar factor lab path)

---

### UT-11 — vcp_contraction h20 and h60 badges still show "Proven" after iter-15 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and serving `/api/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load
3. Locate the `vcp_contraction` factor row in the factor table
4. Confirm the h20 (20-day hold) chip for `vcp_contraction` displays "Proven" (not "Not yet proven")
5. Confirm the h60 (60-day hold) chip for `vcp_contraction` displays "Proven" (not "Not yet proven")

**Expected Result:**
- The `vcp_contraction` factor's h20 and h60 chips both display "Proven" in the proven-checkmark pill style
- These chips are unchanged from prior iterations — no regression in their display state caused by the addition of `rs_spy_3m` h60

---

### UT-12 — /stocks per-stock score badge columns are unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to fully load (stock list visible with score badge columns)
3. Count the number of score badge columns displayed in the stock list header
4. Confirm the column headers match prior iterations (leadership_score and two other score columns — not a new "rs_spy_3m" or "Relative Strength 3M" column)
5. Confirm no per-stock row shows a new badge, evidence indicator, or score value associated with `rs_spy_3m`

**Expected Result:**
- The `/stocks` page loads with the same score badge columns as prior iterations — no new column added
- No column header, badge label, or tooltip contains the text "rs_spy_3m", "3-month Relative Strength", or "Relative Strength 3M"
- No stock entry in the list shows a new score badge from the `rs_spy_3m` h60 certification
- The existing column layout and badge values are unchanged

---

### UT-13 — rs_spy_3m does not appear in proven_signals on /stocks (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for page to fully load
3. Scan every column header, badge label, and any visible "Evidence" panel or "Proven signals" section on the page
4. Look for any text containing "rs_spy_3m", "3-month Relative Strength", "Relative Strength 3M", or similar

**Expected Result:**
- No column, badge label, or evidence panel on the `/stocks` page references "rs_spy_3m" or the 3-month Relative Strength factor
- If the page displays a "proven signals" set (in a panel or tooltip), it shows only "leadership_score" — not "rs_spy_3m"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /evidence page loads with 7 rows | smoke | P1 | `/evidence` |
| UT-02 | New rs_spy_3m D10 h60 evidence row displays correct values | happy-path | P1 | `/evidence` |
| UT-03 | Deep-link anchor #factor-rs_spy_3m-d10-h60 scrolls to rs_spy_3m row | happy-path | P1 | `/evidence` |
| UT-04 | /evidence page shows graceful state when backend unavailable | error | P2 | `/evidence` |
| UT-05 | First 6 evidence rows unchanged after iteration 15 | regression | P1 | `/evidence` |
| UT-06 | /research/factor-lab loads with rs_spy_3m factor row visible | smoke | P1 | `/research/factor-lab` |
| UT-07 | rs_spy_3m h60 evidence chip shows "Proven" badge | happy-path | P1 | `/research/factor-lab` |
| UT-08 | Clicking rs_spy_3m "Proven" chip navigates to /evidence#factor-rs_spy_3m-d10-h60 | happy-path | P1 | `/research/factor-lab` |
| UT-09 | rs_spy_3m uncertified horizons (h1/h5/h10/h20) still show "Not yet proven" | regression | P1 | `/research/factor-lab` |
| UT-10 | End-to-end audit trail: factor lab → Proven badge → evidence row → back | ux | P2 | `/research/factor-lab`, `/evidence` |
| UT-11 | vcp_contraction h20 and h60 badges still show "Proven" | regression | P1 | `/research/factor-lab` |
| UT-12 | /stocks per-stock score badge columns are unchanged | regression | P1 | `/stocks` |
| UT-13 | rs_spy_3m does not appear in proven_signals on /stocks | ux | P2 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.**
