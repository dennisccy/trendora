# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Date:** 2026-06-13
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /sectors page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running (scan has completed at least once)

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to fully load (rows appear with scores)

**Expected Result:**
- Page renders without a blank screen or "Backend unavailable" message
- A table of ranked ETF rows is visible with tickers (e.g., XLK, SMH, KRE) and numeric scores
- No JavaScript error banner is visible on the page

---

### UT-02 — Expanding an industry ETF row shows config display name in panel header (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — expanded ETF row panel header

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; at least one industry ETF row is present in the ranked table
- User is on the `/sectors` page with the table loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "SMH" in the ranked table
4. Click the expand toggle (chevron/arrow icon) on the "SMH" row to open its panel
5. Read the panel header text that appears in the expanded section

**Expected Result:**
- The expanded panel opens below the "SMH" row
- The panel header displays a name such as "Semiconductors (VanEck)" or the configured display name — NOT the bare ticker "SMH"
- The score-component breakdown (existing content) is still visible in the panel

---

### UT-03 — Expanding an industry ETF row shows a description line (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — expanded ETF row panel description

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; the SMH industry ETF has a `description` in config
- User is on `/sectors` with the table loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "SMH"
4. Click the expand toggle on the "SMH" row
5. Look for a description paragraph in the expanded panel body, below the header name

**Expected Result:**
- A plain-language description sentence is visible below the panel header (e.g., text describing what the Semiconductors industry group represents)
- The description is distinct from the score-component breakdown table
- The description text is not blank, not "null", and not "undefined"

---

### UT-04 — Expanding a sector ETF row (XLK) shows universe member ticker chips (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — expanded ETF row panel member chip list (sector ETF)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; XLK is a sector ETF with Technology-sector stocks mapped to it
- User is on `/sectors` with the table loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "XLK"
4. Click the expand toggle on the "XLK" row
5. Scroll down to the members section within the expanded panel
6. Count the number of ticker chips visible

**Expected Result:**
- At least one ticker chip (e.g., "AAPL", "MSFT", or another Technology-sector stock) is visible in the expanded panel
- Each chip is rendered as a bordered clickable element
- If more than 6 members exist, exactly 6 chips are visible initially and a "+N" button is shown (tested separately in UT-06)
- The section heading reads "Members (config-defined)" is NOT shown for a sector ETF (sector ETF uses `stock_sectors`; the "(config-defined)" label applies to industry ETFs — verify the heading text matches the implemented label)

---

### UT-05 — Expanding an industry ETF row (SMH) shows member chip list with "Members (config-defined)" header (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — expanded ETF row panel member chip list (industry ETF)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; SMH is mapped to NVDA, AMD, and other stocks in `stock_industries` config
- User is on `/sectors` with the table loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "SMH"
4. Click the expand toggle on the "SMH" row
5. Scroll to the members section in the expanded panel
6. Read the section heading text above the chip list

**Expected Result:**
- The section heading reads exactly "Members (config-defined)"
- Ticker chips including "NVDA" and "AMD" are visible
- Each chip is rendered as a bordered clickable element

---

### UT-06 — "+N" expand button reveals all members, "Show fewer" collapses back to 6 (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — member expand/collapse toggle

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; XLK (or another sector/industry ETF) has more than 6 mapped universe members
- User is on `/sectors` with the XLK row collapsed

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "XLK" and click its expand toggle
4. Count the visible ticker chips — verify exactly 6 chips are shown
5. Locate the "+N" button (dashed-border chip showing e.g. "+5 more" or similar) and click it
6. Count the visible chips again
7. Locate the "Show fewer" button and click it
8. Count the visible chips again

**Expected Result:**
- After step 4: exactly 6 chips are visible and the "+N" button is present
- After step 5 (clicking "+N"): all chips are visible (more than 6), "Show fewer" button appears, "+N" button is gone
- After step 7 (clicking "Show fewer"): exactly 6 chips are visible again, "+N" button reappears

---

### UT-07 — Unmapped ETF (KRE) shows explicit empty-state message, no fabricated chips (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — expanded ETF row panel zero-member empty state

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; KRE ("Regional Banks (SPDR)") has no stocks mapped to it in config
- User is on `/sectors` with the table loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "KRE" in the ranked table
4. Click the expand toggle on the "KRE" row
5. Read the text in the members section of the expanded panel

**Expected Result:**
- The panel header shows the display name "Regional Banks (SPDR)" — NOT the bare ticker "KRE"
- The members section shows the text "No universe members are mapped to this ETF (config-defined)."
- Zero ticker chips are visible in the expanded panel
- No placeholder tickers or fabricated names appear

---

### UT-08 — Member chip opens stock detail in new browser tab (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — member chip link behavior

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; at least one ETF row with members is present
- User is on `/sectors` at the current (latest) date (no `?asof` query string)

**Steps:**
1. Navigate to `http://localhost:3835/sectors` (no query string)
2. Wait for the ranked table to load
3. Locate the row with ticker "XLK" and click its expand toggle
4. Find a ticker chip in the member list (e.g., "AAPL")
5. Right-click the chip and inspect its link destination, OR click it and observe the browser tab behavior

**Expected Result:**
- Clicking the chip opens the stock detail page in a NEW browser tab (not the same tab)
- The URL of the new tab is `http://localhost:3835/stocks/AAPL` (or the relevant ticker) with NO `?asof=` parameter
- The original `/sectors` tab remains open and unchanged

---

### UT-09 — Member chip carries ?asof parameter when viewing historical snapshot (changed behavior)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — member chip href under historical as-of

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; at least one historical snapshot is available
- User navigates to `/sectors` with a historical `?asof` date

**Steps:**
1. Navigate to `http://localhost:3835/sectors?asof=2026-05-15`
2. Wait for the ranked table to load (confirm the date shown matches 2026-05-15)
3. Locate any ETF row with member chips and click its expand toggle
4. Right-click one of the ticker chips and select "Copy link address" (or hover to see the URL in the browser status bar)
5. Inspect the link URL

**Expected Result:**
- The link URL contains `?asof=2026-05-15` (the same date as the page URL)
- The link URL contains the stock path (e.g., `/stocks/NVDA?asof=2026-05-15`)
- If clicked, the new tab opens the stock detail at the historical date, not the latest date

---

### UT-10 — Sector ETF without description does not show description line or crash (validation / error)

**Type:** validation
**Priority:** P2
**Surface:** `/sectors` — expanded ETF row panel for sector-type ETF

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; XLK is a sector-type ETF (not industry) and has no `description` configured

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the row with ticker "XLK"
4. Click the expand toggle on the "XLK" row
5. Look at the expanded panel content — specifically check whether a description line or blank paragraph appears

**Expected Result:**
- No description paragraph or label appears in the expanded panel for XLK
- The panel does NOT show blank/empty text, "null", or "undefined" where a description would be
- The panel does NOT crash or show a JavaScript error
- The score-component breakdown and member chip list are still rendered correctly

---

### UT-11 — /sectors page score-component breakdown still works as before (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/sectors` — expanded ETF row panel score components

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; the sectors scan has completed
- User is on `/sectors` with the table loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate any ETF row (e.g., "XLK")
4. Click the expand toggle on the row
5. Look at the score-component breakdown section in the expanded panel

**Expected Result:**
- The score-component breakdown table/list is still visible in the expanded panel
- Numeric score components (e.g., RS vs SPY, distance from 52-week high) are shown
- The components section has not been replaced or hidden by the new name/description/members sections
- Values appear consistent (not all zeros, not blank)

---

### UT-12 — /sectors ranked table ordering unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/sectors` — ranked ETF table

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; sectors scan has completed

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Read the rank or order of the first three rows in the table
4. Verify rows are ordered from highest score to lowest score (the score values decrease from top to bottom)

**Expected Result:**
- The ranked table shows ETF rows ordered by score descending (rank 1 at the top)
- No rows are duplicated, missing, or appear out of order
- Both sector-type and industry-type ETFs appear in the table, interleaved by score

---

### UT-13 — Member section heading distinguishes config-defined vs stock_sectors members (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/sectors` — member section labels

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; both an industry ETF (SMH) and a sector ETF (XLK) have members
- User is on `/sectors`

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Click the expand toggle on the "SMH" row (industry ETF)
4. Read the heading above the member chip list in the "SMH" expanded panel
5. Click the expand toggle on the "XLK" row (sector ETF) to open it alongside SMH
6. Read the heading above the member chip list in the "XLK" expanded panel

**Expected Result:**
- The "SMH" (industry ETF) member section heading reads "Members (config-defined)" — communicating the data source
- The "XLK" (sector ETF) member section heading is clearly labelled (either "Members" or "Members (sector)" — whatever the implementation uses; confirm it is not identical to the industry label in a misleading way)
- Both labels are legible and not truncated

---

### UT-14 — Industry ETF name in expanded panel differs from bare ticker (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/sectors` — expanded ETF panel header for industry ETFs

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running; KRE is an industry ETF in the table

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the ranked table to load
3. Locate the "KRE" row in the ranked table — note that the table row itself shows "KRE"
4. Click the expand toggle on the "KRE" row
5. Read the panel header text in the expanded section

**Expected Result:**
- The panel header text is "Regional Banks (SPDR)" (or the configured display name), NOT "KRE"
- The display name is clearly human-readable and represents the industry group, not a code/ticker abbreviation
- The ticker "KRE" still appears in the table row itself (unchanged); only the expanded panel shows the full name

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /sectors page loads without errors | smoke | P1 | `/sectors` |
| UT-02 | Industry ETF panel header shows config name (SMH) | happy-path | P1 | `/sectors` |
| UT-03 | Industry ETF panel shows description line (SMH) | happy-path | P1 | `/sectors` |
| UT-04 | Sector ETF panel shows universe member chips (XLK) | happy-path | P1 | `/sectors` |
| UT-05 | Industry ETF panel shows members with "Members (config-defined)" header | happy-path | P1 | `/sectors` |
| UT-06 | "+N" expand button reveals all members; "Show fewer" collapses | happy-path | P1 | `/sectors` |
| UT-07 | Unmapped ETF (KRE) shows empty-state message, no fabricated chips | happy-path | P1 | `/sectors` |
| UT-08 | Member chip opens stock detail in new browser tab (latest) | happy-path | P1 | `/sectors` |
| UT-09 | Member chip carries ?asof when viewing historical snapshot | happy-path | P1 | `/sectors` |
| UT-10 | Sector ETF without description shows no description line | validation | P2 | `/sectors` |
| UT-11 | Score-component breakdown still renders in expanded panel | regression | P1 | `/sectors` |
| UT-12 | Ranked table ordering unchanged | regression | P1 | `/sectors` |
| UT-13 | Member section heading distinguishes industry vs sector ETFs | ux | P2 | `/sectors` |
| UT-14 | Industry ETF name in expanded panel is human-readable, not a bare ticker | ux | P2 | `/sectors` |

**P1 tests must all pass for browser QA verdict to be PASS.**
