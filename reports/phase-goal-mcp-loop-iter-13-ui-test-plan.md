# Phase goal-mcp-loop-iter-13 — UI Test Plan

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Combination lab page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Wait for the page to fully load (all table rows visible)

**Expected Result:**
- Page renders without a blank screen or error message
- A heading or title for the Multi-factor combination lab is visible in the page
- The combination table is present with multiple cohort rows (quintile rows, composite row, etc.)
- The composite cohort row (`data-testid="combination-row-composite"`) is visible
- No red error banner or "Something went wrong" message appears

---

### UT-02 — Evidence page loads and shows six claim rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load (all claim rows visible)
3. Count the number of claim rows displayed on the page

**Expected Result:**
- Page renders without a blank screen or error message
- Exactly 6 claim rows are visible (previously 5; the 6th is the new combination entry)
- Each row has hypothesis chips visible
- No "Unmapped signal" text appears anywhere on the page
- No red error banner or "Something went wrong" message appears

---

### UT-03 — "Proven" badge appears when the certified combination is selected (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- `GET http://localhost:8000/api/evidence` returns 6 claims including the combination entry with `proven: true`

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Wait for the combination table to finish loading
3. Set the horizon selector to **20** (look for a horizon or holding-period control on the page)
4. Set Leg 1 to **rs_spy_3m**, bucket **top**, grouping **quintile**
5. Set Leg 2 to **high_proximity**, bucket **top**, grouping **tertile**
6. Scroll down until the composite cohort row (`data-testid="combination-row-composite"`) is visible in the viewport
7. Locate the evidence badge element (`data-testid="combination-evidence-badge"`) on the composite row

**Expected Result:**
- The badge on the composite row reads **"Proven"**
- The badge `data-proven` attribute value is `true`
- The badge contains a clickable link (an `<a>` tag with `href` pointing to `/evidence#combination-high_proximity-rs_spy_3m-h20`)
- The badge text is rendered with an accent colour (not muted/grey)
- A ShieldCheck icon or similar visual indicator appears alongside the "Proven" label

---

### UT-04 — "Not yet proven" badge appears for any non-certified combination (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Wait for the combination table to finish loading
3. Confirm the default selection is **rs_spy_3m × atr_pct** (this is the default pair and is NOT certified)
4. Scroll down until the composite cohort row (`data-testid="combination-row-composite"`) is visible in the viewport
5. Locate the evidence badge element (`data-testid="combination-evidence-badge"`) on the composite row

**Expected Result:**
- The badge on the composite row reads **"Not yet proven"**
- The badge `data-proven` attribute value is `false`
- No `<a>` link element is present inside or wrapping the badge
- The badge text is rendered in a muted or neutral colour (not accent)
- A Shield icon (without a checkmark) or similar visual indicator appears alongside the label

---

### UT-05 — Clicking the "Proven" badge navigates to the combination evidence anchor (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/factor-combination` → `/evidence#combination-high_proximity-rs_spy_3m-h20`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- Horizon is 20, Leg 1 is rs_spy_3m / top / quintile, Leg 2 is high_proximity / top / tertile (as set in UT-03)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Set horizon to **20**, Leg 1 to **rs_spy_3m / top / quintile**, Leg 2 to **high_proximity / top / tertile**
3. Scroll down until the composite cohort row is visible in the viewport
4. Verify the badge reads "Proven"
5. Click the **"Proven"** badge (the link text or the ShieldCheck icon — both should be part of the same anchor)

**Expected Result:**
- Browser navigates to `http://localhost:3255/evidence`
- The URL contains the fragment `#combination-high_proximity-rs_spy_3m-h20`
- The page scrolls so that the combination claim row (the 6th row, with the rs_spy_3m × high_proximity chips) is visible in the viewport
- The combination claim row is not hidden below or above the visible area — it must be scrolled into view
- The user does not need to manually scroll to find the combination row

---

### UT-06 — Sixth evidence row shows correct combination data (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- `GET http://localhost:8000/api/evidence` returns the combination claim with `holdout_edge: 0.04693`, `control_excess: 0.04693`, `verdict.status: "PASS"`, `register_date: 2026-07-01`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for all 6 claim rows to load
3. Scroll to the bottom of the claim list to locate the 6th (last) row — it should be the combination row with `id="combination-high_proximity-rs_spy_3m-h20"`
4. Inspect the hypothesis chips on the 6th row

**Expected Result:**
- The 6th row carries hypothesis chips that include:
  - A chip indicating **rs_spy_3m:top:quintile** (first condition leg)
  - A chip indicating **high_proximity:top:tertile** (second condition leg)
  - A horizon chip showing **20**
  - A direction chip showing **positive**
  - A cohort chip showing **composite**
- The verdict indicator reads **"PASS"** (or a green check/badge equivalent)
- The holdout edge displayed reads **"+4.69%"** (or equivalent representation of 0.04693)
- The control vs. SPY figure reads **"+4.69%"** (or equivalent representation of 0.04693)
- The registration date reads **"2026-07-01"**
- A forward-walk status of **"Pending"** is shown
- The linkback text reads **"Backs: Multi-factor combination lab →"**
- No row shows the text **"Unmapped signal"** anywhere on the evidence page

---

### UT-07 — "Backs: Multi-factor combination lab →" linkback navigates to the combination lab (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence` → `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- The 6th claim row is visible on `/evidence`

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll to the 6th (last) claim row (the combination row)
3. Locate the link text **"Backs: Multi-factor combination lab →"** at the bottom of the 6th row
4. Click the **"Backs: Multi-factor combination lab →"** link

**Expected Result:**
- Browser navigates to `http://localhost:3255/research/factor-combination`
- The combination lab page loads without errors
- The combination table is visible with cohort rows

---

### UT-08 — Badge updates reactively when leg selection changes (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Set horizon to **20**, Leg 1 to **rs_spy_3m / top / quintile**, Leg 2 to **high_proximity / top / tertile**
3. Scroll to the composite cohort row and verify the badge reads **"Proven"**
4. Change Leg 2 from **high_proximity** to **atr_pct** (any other available factor)
5. Observe the composite row badge without reloading the page

**Expected Result:**
- Immediately after changing Leg 2, the badge on the composite row changes from **"Proven"** to **"Not yet proven"**
- No page reload is required — the change is reactive
- The link on the badge disappears (no `<a>` tag present)
- The badge style changes from accent/highlighted to muted/neutral

**Then:**
6. Change Leg 2 back to **high_proximity / top / tertile**

**Expected Result:**
- Badge immediately returns to **"Proven"** with the deep-link restored
- The `<a href="/evidence#combination-high_proximity-rs_spy_3m-h20">` link is present again

---

### UT-09 — Badge horizon sensitivity: certified legs at non-certified horizon show "Not yet proven" (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Set Leg 1 to **rs_spy_3m / top / quintile**, Leg 2 to **high_proximity / top / tertile**
3. Set the horizon to **60** (a horizon other than 20)
4. Scroll to the composite cohort row and observe the badge

**Expected Result:**
- The badge reads **"Not yet proven"** despite using the correct legs
- No `<a>` deep-link is present
- This confirms the badge is horizon-aware: only h20 with the certified legs triggers "Proven"

---

### UT-10 — Prior 5 evidence rows are unchanged after this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for all 6 claim rows to load
3. Scroll to the **first row** (leadership score) and verify:
   - Linkback text reads **"Backs: Leadership Lab →"** (or equivalent)
   - Verdict badge is present (PASS or equivalent)
4. Scroll to the **second row** (vcp_contraction at h20) and verify:
   - Horizon chip shows **20**
   - Condition chip shows **vcp_contraction**
   - Linkback text reads **"Backs: Factor Lab →"** (or equivalent)
5. Scroll to the **third row** (vcp_contraction at h60) and verify:
   - Horizon chip shows **60**
   - Condition chip shows **vcp_contraction**
6. Verify rows 4 and 5 (entry_quality and risk_score) are present with their respective hypothesis chips and linkbacks intact
7. Verify the total count is exactly **6** rows (not 7 or more)

**Expected Result:**
- Rows 1–5 display identically to prior iterations (same chips, verdicts, linkbacks)
- No existing row has had its text, chips, or linkback changed
- The total count is 6 (not 5 from a regression that removes the new row, not 7 from a duplicate)

---

### UT-11 — Combination table statistical data is intact alongside the new badge (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Wait for the combination table to fully load
3. Scroll through the cohort rows (not just the composite row) and verify that:
   - Individual quintile/tertile cohort rows display numeric cell data (percentages, counts, or performance figures)
   - The composite cohort row still shows its cohort statistical cells alongside the new evidence badge
   - The composite row has not lost its existing data cells — only the badge was added
4. Verify that the overall table layout is intact (no misaligned columns, no blank rows)

**Expected Result:**
- All cohort rows (not just composite) are present with numeric data in cells
- The composite row shows both its statistical cohort data AND the new evidence badge — neither is missing
- Table column alignment is normal (no layout breakage from the badge insertion)
- No existing cell value in the table has changed

---

### UT-12 — Stocks page shows no combination evidence badge (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the stock list to load
3. Locate the inline evidence badges on the first visible stock entry (Leadership Score badge should read "Proven")
4. Inspect all inline badges visible on the stocks listing page
5. Navigate to `http://localhost:3255/stocks/SPY` (a single stock detail page)
6. Inspect all inline badges on the SPY detail page

**Expected Result:**
- On `/stocks`, the Leadership Score badge reads **"Proven"**
- Entry Quality and Risk badges read **"Not yet proven"**
- No new badge labelled "Combination", "Composite", "rs_spy_3m × high_proximity", or any variant appears inline on `/stocks` or `/stocks/SPY`
- The badge count on each stock entry is the same as in prior iterations (no new badge added)
- This confirms the combination claim (which has `signal: null`) does not light any inline stock badge

---

### UT-13 — Badge is visually prominent and discoverable on the composite row (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research/factor-combination`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000
- Certified combination selected (rs_spy_3m × high_proximity at h20)

**Steps:**
1. Navigate to `http://localhost:3255/research/factor-combination`
2. Set the certified combination: horizon **20**, Leg 1 **rs_spy_3m / top / quintile**, Leg 2 **high_proximity / top / tertile**
3. Scroll slowly through the combination table from top to bottom
4. Note at what point the composite row badge becomes visible

**Expected Result:**
- The "Proven" badge is visually distinguishable from the surrounding cell data (accent colour, icon, or both)
- A new user scrolling through the table would notice the badge without being told to look for it
- The badge label "Proven" is readable at normal zoom (100%) without requiring hover or tooltip
- The badge is not hidden under any overflow or clipped by a container

---

### UT-14 — Evidence anchor scroll positions the combination row in the viewport (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate directly to `http://localhost:3255/evidence#combination-high_proximity-rs_spy_3m-h20` (deep-link with anchor)
2. Observe the page without scrolling

**Expected Result:**
- The combination claim row (the 6th row) is visible in the viewport immediately on page load — the browser has scrolled to the anchor
- The combination row is not hidden at the very bottom of the page requiring further manual scrolling
- The row is clearly the combination entry (rs_spy_3m × high_proximity chips visible)
- The first 5 rows above it may be partially or fully off-screen, which is acceptable — the anchor row itself must be in view

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Combination lab page loads without errors | smoke | P1 | `/research/factor-combination` |
| UT-02 | Evidence page loads with six claim rows | smoke | P1 | `/evidence` |
| UT-03 | "Proven" badge appears for certified combination | happy-path | P1 | `/research/factor-combination` |
| UT-04 | "Not yet proven" badge for non-certified combination | happy-path | P1 | `/research/factor-combination` |
| UT-05 | Proven badge deep-link navigates to evidence anchor | happy-path | P1 | `/research/factor-combination` → `/evidence` |
| UT-06 | Sixth evidence row shows correct combination data | happy-path | P1 | `/evidence` |
| UT-07 | Linkback navigates from evidence row to combination lab | happy-path | P1 | `/evidence` → `/research/factor-combination` |
| UT-08 | Badge updates reactively when leg selection changes | validation | P2 | `/research/factor-combination` |
| UT-09 | Certified legs at non-certified horizon show "Not yet proven" | validation | P2 | `/research/factor-combination` |
| UT-10 | Prior 5 evidence rows unchanged | regression | P1 | `/evidence` |
| UT-11 | Combination table statistical data intact alongside badge | regression | P1 | `/research/factor-combination` |
| UT-12 | Stocks page shows no combination evidence badge | regression | P1 | `/stocks` |
| UT-13 | Badge is visually prominent and discoverable | ux | P2 | `/research/factor-combination` |
| UT-14 | Evidence anchor scrolls combination row into viewport | ux | P2 | `/evidence` |

**P1 tests (UT-01 through UT-07, UT-10, UT-11, UT-12) must all pass for browser QA verdict to be PASS.**
