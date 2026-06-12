# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (all spinner/loading indicators disappear)

**Expected Result:**
- Page renders without a blank screen or error message
- The heading or section title for the data management page is visible
- No "Failed to load" or error banner appears
- No browser console errors relating to component crashes

---

### UT-02 — Dashboard loads and shows five index lines including DIA (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (dashboard)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835 with seed data loaded (including DIA bars from 2021-01-04 onward)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the "Major indexes & regime" chart to fully render (lines appear on the chart canvas)

**Expected Result:**
- The "Major indexes & regime" chart is visible on the page
- The chart legend shows exactly five entries: SPY, QQQ, IWM, RSP, and "Dow 30 (DIA)" (or similar label including DIA)
- Five distinct colored lines are drawn across the chart area
- No error banner or empty-chart placeholder appears

---

### UT-03 — Methodology page loads and shows new glossary entries (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/methodology`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Wait for the glossary list to fully render

**Expected Result:**
- The methodology page loads without error
- A glossary section is visible
- At least the terms "stage timings" and "concurrency" appear in the list
- No "Failed to load glossary" or empty-list placeholder

---

### UT-04 — DIA appears in the Major-indexes chart legend with a drawn line (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (dashboard — Major-indexes & regime chart)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend seed contains DIA daily bars from 2021-01-04 onward (1356+ bars)
- `/api/indexes` endpoint returns DIA data

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Major indexes & regime" chart (typically in the upper portion of the dashboard)
3. Inspect the chart legend — read the list of labeled series
4. Confirm "Dow 30 (DIA)" (or "DIA") is listed as a fifth legend entry alongside SPY, QQQ, IWM, and RSP
5. Visually confirm that a fifth line is drawn across the chart, not just a legend label with no line

**Expected Result:**
- The legend shows five entries; the fifth one is labeled with DIA
- A fifth line is visible on the chart spanning the historical date range (the line should not be flat/zero)
- The four existing lines (SPY, QQQ, IWM, RSP) are still drawn and unchanged

---

### UT-05 — Completed job card shows Stage timings block (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — job card `StageTimings` block

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- At least one fetch+backfill job has been completed (the job card should show status "completed" or "done")
- If no completed job exists: on `/data`, start a new job and wait for it to finish before proceeding

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a completed job card in the job list (look for a status indicator showing success/done)
3. Expand the job card or scroll to its detail section if the timings block is not immediately visible
4. Find the "Stage timings" section on the job card
5. Within the "Stage timings" section, locate the Fetch sub-block (if the job performed a fetch stage) and verify it shows: a non-empty "Elapsed" duration (e.g. "2.3 s"), a non-zero "Symbols" count, and a "Concurrency" value (e.g. "4×")
6. Locate the Backfill sub-block (if the job performed a backfill stage) and verify it shows: a non-empty "Elapsed" duration, a non-zero "Dates" count, a "Concurrency" value, a "Per-date sum" duration, and a "X.X× faster than the per-date sum" line

**Expected Result:**
- The "Stage timings" heading is visible on the job card
- Each executed stage (Fetch and/or Backfill) has its own sub-block with non-zero, non-placeholder values
- The Backfill sub-block shows a speed-up ratio greater than 1 (e.g. "2.1× faster than the per-date sum")
- No sub-block shows "0 s", "N/A", or a blank value for elapsed time

---

### UT-06 — Backfill-only job card shows only Backfill sub-block, no Fetch sub-block (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — job card `StageTimings` block (honest NA)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8835
- A backfill-only job has completed (one that ran only the backfill stage, not a new-symbol fetch)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a completed backfill-only job card
3. Find the "Stage timings" section on the job card
4. Look for any "Fetch" sub-block within the "Stage timings" section

**Expected Result:**
- The "Stage timings" section is present on the job card
- A "Backfill" sub-block is shown with non-zero Elapsed, Dates, and Concurrency values
- No "Fetch" sub-block appears anywhere on the job card (the section should be entirely absent, not showing zeros or a dash)

---

### UT-07 — TermInfo tooltip appears when hovering the info icon next to "Stage timings" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — TermInfo tooltip on "Stage timings" label

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one completed job card with a "Stage timings" section is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a completed job card showing the "Stage timings" section
3. Find the info icon (typically a circle with "i" inside, or a question-mark icon) placed immediately next to the "Stage timings" section header text
4. Hover the mouse cursor over that info icon (do not click — just hover)
5. Wait up to 2 seconds for a tooltip or popover to appear

**Expected Result:**
- A tooltip or popover appears containing a plain-language definition of "stage timings"
- The tooltip text is non-empty and is not the raw term key (i.e., it should not read "stage_timings" or "{term}" — it should be a readable sentence or phrase)
- The tooltip disappears when the cursor moves away from the icon

---

### UT-08 — TermInfo tooltip appears when hovering the info icon next to "Concurrency" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — TermInfo tooltip on "Concurrency" stat label

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one completed job card with a "Stage timings" section is visible (the Concurrency label is inside a stage sub-block)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a completed job card showing the "Stage timings" section and its sub-blocks
3. Within any stage sub-block (Fetch or Backfill), find the "Concurrency" stat row
4. Find the info icon placed immediately next to the "Concurrency" label text
5. Hover the mouse cursor over that info icon (do not click — just hover)
6. Wait up to 2 seconds for a tooltip or popover to appear

**Expected Result:**
- A tooltip or popover appears containing a plain-language definition of "concurrency"
- The tooltip text is non-empty and is not the raw term key
- Moving the cursor away dismisses the tooltip

---

### UT-09 — "stage timings" and "concurrency" appear in the methodology glossary with definitions (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/methodology` — glossary term list

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Scroll through the glossary section to locate the term "stage timings"
3. Read the definition text shown next to or below "stage timings"
4. Continue scrolling and locate the term "concurrency"
5. Read the definition text shown next to or below "concurrency"

**Expected Result:**
- "stage timings" appears as a glossary entry with a non-empty definition (more than one word; not a placeholder)
- "concurrency" appears as a glossary entry with a non-empty definition (more than one word; not a placeholder)
- Both entries are alphabetically or logically ordered within the existing glossary list
- No duplicate entries for either term

---

### UT-10 — Backfill speed-up ratio is greater than 1 on a multi-date job card (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Backfill sub-block speed-up line

**Preconditions:**
- Frontend is running at http://localhost:3835
- A completed multi-date backfill job exists (ran across at least 5 dates, with `backfill_workers >= 4`)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a completed job card for a multi-date backfill (check the job's date range covers several dates)
3. Find the "Stage timings" section and open the Backfill sub-block
4. Locate the line showing the speed-up ratio (expected text similar to "2.1× faster than the per-date sum")
5. Read the numeric ratio value (the "X.X" part of "X.X× faster")

**Expected Result:**
- The speed-up line is visible and contains a numeric ratio
- The ratio is greater than 1.0 (e.g., "2.1×", "3.4×")
- The "Per-date sum" duration is shown alongside the actual "Elapsed" duration, and "Per-date sum" is visibly larger than "Elapsed"
- The label text includes the phrase "faster than the per-date sum" or equivalent

---

### UT-11 — Existing job progress bars and summary still present on job card (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — job card progress panel

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one completed job card is visible in the job list

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Locate a completed job card
3. Inspect the job card for the progress or summary section that existed before this iteration (e.g., a completion summary, stage status indicators, overall elapsed time)
4. Verify that progress or summary elements are still visible on the card alongside the new "Stage timings" block

**Expected Result:**
- The existing progress or summary section on the job card is still rendered
- The new "Stage timings" block appears as an additive section — it does not replace the existing elements
- No existing job card elements are missing compared to previous behavior

---

### UT-12 — Dashboard four existing index lines (SPY, QQQ, IWM, RSP) still displayed (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (dashboard — Major-indexes chart)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend seed data present for all five indexes

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Major indexes & regime" chart
3. Inspect the chart legend

**Expected Result:**
- The legend shows SPY, QQQ, IWM, and RSP as labeled entries (all four previously existing lines)
- All four lines are drawn on the chart canvas (not blank or missing)
- DIA is a fifth addition and has not replaced any of the existing four

---

### UT-13 — "Stage timings" section header info icon is discoverable without developer knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — job card

**Preconditions:**
- A completed job card with a "Stage timings" section is visible

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Without reading any documentation, look at the job card of a completed job
3. Identify whether there is a help or info affordance (icon) next to the "Stage timings" label
4. Attempt to discover what the icon does by hovering over it

**Expected Result:**
- The info icon is visually distinct and obvious (e.g., a circled "i" or question mark) — it should not require a developer to find it
- Hovering the icon reveals a tooltip with a readable explanation
- The icon is placed directly adjacent to the "Stage timings" label text, not hidden below a fold or in a collapsed section

---

### UT-14 — DIA line is labeled clearly in the chart legend so it is distinguishable from other indexes (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` (dashboard — Major-indexes chart)

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Locate the "Major indexes & regime" chart
3. Read all five legend entries without hovering over the chart lines

**Expected Result:**
- The DIA entry in the legend includes a human-readable name (e.g., "Dow 30 (DIA)" or "DIA — Dow Jones") — it is not just "DIA" with no context
- The DIA legend color swatch visually distinguishes it from the other four lines
- An operator who is not a developer can identify which line is the Dow 30 without looking it up

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` page loads without errors | smoke | P1 | `/data` |
| UT-02 | Dashboard loads with five index lines | smoke | P1 | `/` |
| UT-03 | Methodology page shows new glossary entries | smoke | P1 | `/methodology` |
| UT-04 | DIA appears in Major-indexes chart legend with drawn line | happy-path | P1 | `/` |
| UT-05 | Completed job card shows Stage timings block | happy-path | P1 | `/data` |
| UT-06 | Backfill-only job shows only Backfill sub-block | happy-path | P1 | `/data` |
| UT-07 | TermInfo tooltip on "Stage timings" label | happy-path | P1 | `/data` |
| UT-08 | TermInfo tooltip on "Concurrency" stat label | happy-path | P1 | `/data` |
| UT-09 | Glossary entries with definitions for new terms | happy-path | P1 | `/methodology` |
| UT-10 | Backfill speed-up ratio > 1 on job card | happy-path | P1 | `/data` |
| UT-11 | Existing job progress bars/summary still present | regression | P1 | `/data` |
| UT-12 | Four existing index lines still displayed | regression | P1 | `/` |
| UT-13 | Stage timings info icon discoverable by non-developer | ux | P2 | `/data` |
| UT-14 | DIA legend label is human-readable and distinguishable | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
