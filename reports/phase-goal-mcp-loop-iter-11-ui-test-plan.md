# Phase goal-mcp-loop-iter-11 — UI Test Plan

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- API and unit tests are covered in reports/qa/goal-mcp-loop-iter-11-test-plan.md and are not duplicated here. -->

---

### UT-01 — Factor Lab page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Wait for the page to fully load (the factor table becomes visible)

**Expected Result:**
- Page renders without a blank screen, spinner stuck indefinitely, or red error message
- A table of factors is visible with at least one row
- The Evidence column exists in the table header
- No browser console errors visible in DevTools → Console tab

---

### UT-02 — Evidence page loads with five claim rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load (claim rows become visible)

**Expected Result:**
- Page renders without a blank screen or error message
- Exactly 5 claim rows are visible in the ledger
- No browser console errors visible in DevTools → Console tab

---

### UT-03 — Evidence column header reads "Evidence (D10 · per horizon)" (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Factor Lab table is visible (UT-01 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the column header for the Evidence column in the factor table

**Expected Result:**
- The Evidence column header reads exactly **"Evidence (D10 · per horizon)"**
- The header does NOT read "Evidence (D10 · 20d)" (the old text)
- No other column header is missing or malformed

---

### UT-04 — vcp_contraction h60 chip shows "Proven" and links to the h60 evidence anchor (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The `vcp_contraction` factor row is visible in the table
- The h60 certified claim is present in the evidence data

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the row for factor `vcp_contraction` in the table
3. In the Evidence column, find the chip for the 60-day horizon (labeled "60d" or positioned fifth in the chip strip)
4. Read the chip's display text
5. Right-click or hover over the chip to inspect its link destination (or check the URL shown in the browser status bar on hover)

**Expected Result:**
- The 60d chip displays the word **"Proven"** (with or without a checkmark symbol)
- The chip is a clickable hyperlink (cursor changes to pointer on hover)
- The link destination is exactly `/evidence#factor-vcp_contraction-d10-h60`
- The chip carries a `data-proven="true"` attribute (visible in DevTools → Elements)

---

### UT-05 — New vcp_contraction h60 evidence row shows all required fields (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The h60 certified claim is present in the evidence data

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the claim row titled **"vcp_contraction — top decile (D10)"** whose subtitle contains the text **"60-day hold"**
3. Read all visible fields on that row

**Expected Result:**
- Row title reads "vcp_contraction — top decile (D10)"
- Row subtitle contains the phrase "60-day hold" (to distinguish it from the existing 20-day row)
- Status indicator reads **"PASS"**
- Holdout edge figure reads **"+8.91%"**
- SPY benchmark comparison reads **"+8.91%"**
- A registration date is shown (any date value is acceptable — must not be blank)
- Forward-walk score reads **"Pending"**
- A link reading "Backs: Research factor lab →" is visible

---

### UT-06 — Clicking the h60 "Proven" chip navigates to the Evidence page at the h60 anchor (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-lab` → `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The vcp_contraction h60 chip is visible and shows "Proven" (UT-04 passes)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the `vcp_contraction` row in the factor table
3. Click the 60d "Proven" chip in the Evidence column
4. Observe where the browser navigates

**Expected Result:**
- The browser navigates to `http://localhost:3255/evidence#factor-vcp_contraction-d10-h60`
- The Evidence page loads (not a 404 or blank page)
- The URL in the browser address bar ends with `#factor-vcp_contraction-d10-h60`
- The page scrolls to or highlights the vcp_contraction 60-day claim row

---

### UT-07 — vcp_contraction h1, h5, h10 chips show "Not yet proven" without any link (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The `vcp_contraction` row is visible in the factor table
- No certified claims exist for vcp_contraction at horizons 1, 5, or 10 days

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the `vcp_contraction` row
3. In the Evidence column chip strip, identify the first chip (1d), second chip (5d), and third chip (10d)
4. Read the display text for each of those three chips
5. Hover over each chip and observe whether a link destination appears in the browser status bar

**Expected Result:**
- The 1d chip displays "Not yet proven" (no checkmark)
- The 5d chip displays "Not yet proven" (no checkmark)
- The 10d chip displays "Not yet proven" (no checkmark)
- None of the three chips is a hyperlink — no URL appears on hover, and clicking does not navigate away
- The chips carry `data-proven="false"` (visible in DevTools → Elements)

---

### UT-08 — A factor with no certified claims shows exactly five "Not yet proven" chips (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- At least one factor in the table has no certified claims at any horizon (e.g., any factor that is not `vcp_contraction` or `leadership_score`)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate any factor row that is NOT `vcp_contraction` and NOT `leadership_score` (for example, `breakout_watch` or `ma_stack`)
3. Count the chips shown in the Evidence column for that row
4. Read the display text on each chip

**Expected Result:**
- Exactly **5 chips** appear in the Evidence column for that row (one per horizon: 1d, 5d, 10d, 20d, 60d)
- Every chip on that row reads "Not yet proven"
- None of the five chips is a hyperlink

---

### UT-09 — Factor Lab evidence column shows a visible error state when the backend is unavailable (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Browser DevTools is open (press F12)

**Steps:**
1. Open `http://localhost:3255/research/factor-lab` in your browser
2. Wait for the page to load normally (factor table visible)
3. Open DevTools → Network tab → set throttling dropdown to **"Offline"**
4. Press F5 to refresh the page
5. Observe the Evidence column area while the page attempts to fetch data

**Expected Result:**
- The page does NOT show a blank white screen or an unhandled JavaScript error
- An error message or "unavailable" indicator is displayed in place of the evidence chips, OR the table shows fallback placeholder text
- The page remains functional enough to read (no full-page crash)

---

### UT-10 — vcp_contraction h20 chip still shows "Proven" linking to the h20 anchor (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The existing h20 certified claim for vcp_contraction is present (unchanged from prior iterations)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the `vcp_contraction` row in the factor table
3. In the Evidence column chip strip, identify the fourth chip (20d)
4. Read the display text
5. Hover over the chip and observe the link destination in the browser status bar

**Expected Result:**
- The 20d chip displays **"Proven"** (with or without a checkmark symbol)
- The chip is a hyperlink pointing to exactly `/evidence#factor-vcp_contraction-d10-h20`
- The chip does NOT link to `/evidence#factor-vcp_contraction-d10-h60` or any other anchor
- The chip carries `data-proven="true"` and `data-horizon="20"` (visible in DevTools → Elements)

---

### UT-11 — leadership_score h20 chip still shows "Proven" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The existing h20 certified claim for leadership_score is present (unchanged from iter-8)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate the `leadership_score` row in the factor table
3. In the Evidence column chip strip, identify the 20d chip (fourth chip)
4. Read the display text
5. Hover over the chip and observe the link destination

**Expected Result:**
- The 20d chip displays **"Proven"** (with or without a checkmark)
- The chip is a hyperlink pointing to `/evidence#signal-leadership_score` (the anchor for the score-column signal)
- The chip does NOT read "Not yet proven" or display without a link

---

### UT-12 — Four prior evidence rows render correctly and are unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The four prior certified claims are present in the evidence data

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the first row: **`leadership_score`** — confirm it shows status "PASS" and a holdout edge percentage
3. Locate the second row: **`Breakout-watch`** (or `breakout_watch`) — confirm it shows status "PASS"
4. Locate the third row: **`ma_stack`** — confirm it shows status "FAIL"
5. Locate the fourth row: **`vcp_contraction`** — confirm it shows status "PASS" and that its subtitle refers to the **20-day** horizon (not the 60-day horizon)

**Expected Result:**
- All four rows are present and readable
- `leadership_score` row: status "PASS" — no missing fields, no error indicators
- `Breakout-watch` row: status "PASS" — no missing fields
- `ma_stack` row: status "FAIL" — no missing fields
- `vcp_contraction` (first/h20 entry): status "PASS" — subtitle does NOT contain the words "60-day" or "h60"
- None of the four rows has been removed, reordered, or had its core fields altered

---

### UT-13 — vcp_contraction h20 evidence row subtitle does not reference "60-day" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Both the h20 and h60 vcp_contraction rows are present

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the two vcp_contraction rows (the 20-day row and the new 60-day row — there should be exactly two)
3. Read the subtitle text of the **earlier** vcp_contraction row (the h20 entry)

**Expected Result:**
- The h20 vcp_contraction row subtitle refers to a **20-day** hold (e.g., "Out-of-sample edge — factor top decile · 20-day hold" or equivalent)
- The subtitle does NOT contain "60-day", "h60", or any language implying the 60-day horizon
- The h60 row (the newer, fifth row) is the only one containing "60-day hold" in its subtitle

---

### UT-14 — All five horizon chips are visible and labeled in a factor row (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Factor table is visible

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-lab`
2. Locate any factor row in the table
3. Look at the Evidence column for that row — observe all chips rendered there

**Expected Result:**
- Exactly **5 chips** are displayed in the Evidence column per row
- Each chip has a visible horizon label — the set of labels covers 1-day, 5-day, 10-day, 20-day, and 60-day horizons (the exact display text such as "1d", "5d", etc. must appear on or near each chip)
- Chips are visually distinct from one another and individually readable without zooming in
- The chip strip fits within the Evidence column without overflowing into adjacent columns

---

### UT-15 — "Backs: Research factor lab →" linkback on h60 evidence row is clickable and navigates (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/evidence` → `/research/factor-lab`

**Preconditions:**
- Frontend is running at http://localhost:3255
- The new vcp_contraction h60 evidence row is visible (UT-05 passes)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate the `vcp_contraction` h60 row (subtitle contains "60-day hold")
3. Find the link labeled **"Backs: Research factor lab →"** on that row
4. Click the link
5. Observe where the browser navigates

**Expected Result:**
- The browser navigates to `/research/factor-lab` (the full URL should be `http://localhost:3255/research/factor-lab` or include that path with an optional anchor fragment)
- The Factor Lab page loads without error
- No 404 page, no blank page

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab page loads without errors | smoke | P1 | `/research/factor-lab` |
| UT-02 | Evidence page loads with five claim rows | smoke | P1 | `/evidence` |
| UT-03 | Column header reads "Evidence (D10 · per horizon)" | happy-path | P1 | `/research/factor-lab` |
| UT-04 | vcp_contraction h60 chip shows "Proven" with correct link | happy-path | P1 | `/research/factor-lab` |
| UT-05 | New vcp_contraction h60 evidence row shows all required fields | happy-path | P1 | `/evidence` |
| UT-06 | Clicking h60 "Proven" chip navigates to evidence h60 anchor | happy-path | P1 | `/research/factor-lab` |
| UT-07 | vcp_contraction h1/h5/h10 chips show "Not yet proven" without links | validation | P2 | `/research/factor-lab` |
| UT-08 | Factor with no certified claims shows 5 "Not yet proven" chips | validation | P2 | `/research/factor-lab` |
| UT-09 | Factor Lab shows error state when backend unavailable | error | P2 | `/research/factor-lab` |
| UT-10 | vcp_contraction h20 chip still shows "Proven" linking to h20 anchor | regression | P1 | `/research/factor-lab` |
| UT-11 | leadership_score h20 chip still shows "Proven" | regression | P1 | `/research/factor-lab` |
| UT-12 | Four prior evidence rows render correctly and are unchanged | regression | P1 | `/evidence` |
| UT-13 | vcp_contraction h20 evidence row subtitle does not reference "60-day" | regression | P1 | `/evidence` |
| UT-14 | All five horizon chips visible and labeled in a factor row | ux | P2 | `/research/factor-lab` |
| UT-15 | "Backs: Research factor lab →" linkback is clickable and navigates | ux | P2 | `/evidence` |

**P1 tests must all pass for browser QA verdict to be PASS.**
