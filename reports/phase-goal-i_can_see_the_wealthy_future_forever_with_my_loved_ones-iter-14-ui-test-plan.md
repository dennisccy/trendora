# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — /research page loads with Episodes toggle visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (allow up to 10 seconds for data fetch)
3. Observe the Setup & Pattern Lab section

**Expected Result:**
- The `/research` page renders without a blank screen or error message
- A segmented button group labeled "Episodes" and "Pooled" is visible in or near the event-study lab
- The "Episodes" button appears highlighted/active (not "Pooled")
- No full-page crash or "Checking backend..." spinner persists indefinitely

---

### UT-02 — /methodology page loads with Episode and Pooled glossary entries (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/methodology`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Wait for the page to fully load
3. Scroll through the glossary or use Ctrl+F to search for the word "Episode"

**Expected Result:**
- The `/methodology` page renders without error
- A glossary entry titled "Episode" is visible on the page with a definition
- A glossary entry titled "Pooled (per-signal-day)" is visible on the page with a definition
- Neither entry is duplicated on the page

---

### UT-03 — /research/samples page loads and shows cohort detail line (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- At least one event study subject (e.g., "Risk-off-watchlist") exists with forward-tested observations

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to load showing data for any subject
3. Locate an "N=" chip (e.g., a link or chip labeled "N=707" or similar) in the event study figures
4. Right-click the "N=" chip and select "Open link in new tab"
5. Switch to the newly opened tab

**Expected Result:**
- The new tab opens at a URL matching `http://localhost:3835/research/samples?...&view=episodes` (or with `view=episodes` present)
- The `/research/samples` page renders without blank screen or error
- A cohort detail header line is visible somewhere near the top of the samples list

---

### UT-04 — Toggling from Episodes to Pooled updates the active pill and changes n (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded with at least one subject selected that has observations (e.g., "Risk-off-watchlist")
- The view toggle shows "Episodes" as the active/highlighted state

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to load and display figures (n value, disclosure line visible)
3. Note the number shown as `n` or the observation count in the disclosure line (e.g., "707")
4. Click the "Pooled" button in the segmented toggle
5. Wait 2–3 seconds for the lab figures to refresh
6. Note the new `n` value in the disclosure line

**Expected Result:**
- After clicking "Pooled", the "Pooled" button appears highlighted/active and "Episodes" appears inactive
- The `n` value in the disclosure line increases to the signal-day count (e.g., "2,242" instead of "707")
- The disclosure line still shows three values: n, Unique symbols, and Episodes
- No page reload or navigation occurs — the update is in-place
- Click "Episodes" again: the pill returns to "Episodes" active and `n` drops back to the episode count

---

### UT-05 — Disclosure line shows all three values in Episodes mode (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded with a subject that has multiple observations
- The view is in "Episodes" mode (default on page load)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to display figures
3. Locate the disclosure line (element with `data-testid="event-study-disclosure"` or a muted/faint text line near the event study figures)
4. Read the three values displayed in the line

**Expected Result:**
- The disclosure line is visible and contains three labeled values:
  - "n" followed by a number (the episode-collapsed observation count)
  - "Unique symbols" followed by a number (count of distinct tickers)
  - "Episodes" followed by a number (count of first-trigger episodes)
- All three numbers are non-zero for a subject with observations
- The label "Episode" or "Episodes" in the disclosure line shows a tooltip or TermInfo indicator when hovered or clicked

---

### UT-06 — N= chip in Episodes mode links to samples with view=episodes (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded with at least one subject
- The view is in "Episodes" mode

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to show N= chips (links or chips labeled with a number, e.g., "N=707")
3. Hover over or right-click an "N=" chip
4. Inspect the destination URL (hover shows the URL in the browser status bar, or right-click and "Copy Link Address")
5. Verify the URL contains `view=episodes`

**Expected Result:**
- The N= chip URL includes `view=episodes` as a query parameter
- The chip label reads "episodes" (not "occurrences") when in Episodes mode
- Right-clicking and opening in a new tab navigates to `/research/samples?...&view=episodes`

---

### UT-07 — N= chip in Pooled mode links to samples with view=pooled (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded
- Toggle the view to "Pooled" mode

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to load
3. Click the "Pooled" button in the segmented toggle and wait for figures to refresh
4. Hover over or right-click the same N= chip that was inspected in UT-06
5. Inspect the destination URL of the chip

**Expected Result:**
- The N= chip URL now includes `view=pooled` as a query parameter (replacing `view=episodes`)
- The chip label reads "occurrences" (not "episodes") when in Pooled mode
- The N= count in the chip is larger than it was in Episodes mode

---

### UT-08 — Samples drill-down from Episodes chip shows "Episodes (first-trigger)" cohort label (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded in Episodes mode (default)
- At least one N= chip is visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to load in Episodes mode
3. Click an N= chip (or right-click and open in new tab)
4. Switch to the new tab showing `/research/samples`
5. Look at the cohort detail header line near the top of the page

**Expected Result:**
- The cohort detail line reads "Episodes (first-trigger)" somewhere in the header or near the top of the drill-down
- The total row count on the page matches the N= number that was shown in the chip
- The label "Episodes (first-trigger)" is clearly visible (not a blank or missing label)

---

### UT-09 — Samples drill-down from Pooled chip shows "Pooled (per-signal-day)" cohort label (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab has been toggled to Pooled mode
- At least one N= chip is visible with a higher count than in Episodes mode

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Click the "Pooled" button in the segmented toggle and wait for figures to refresh
3. Click an N= chip (or right-click and open in new tab)
4. Switch to the new tab showing `/research/samples?...&view=pooled`
5. Look at the cohort detail header line near the top of the page

**Expected Result:**
- The cohort detail line reads "Pooled (per-signal-day)" somewhere in the header or near the top of the drill-down
- The total row count on the page is larger than the Episodes-mode row count for the same subject/cohort
- The label "Pooled (per-signal-day)" is clearly visible

---

### UT-10 — Disclosure line tooltip appears on "Episode" term click (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research` with the event study lab loaded in Episodes mode

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the disclosure line to appear (element with `data-testid="event-study-disclosure"` or muted text near figures)
3. Locate the word "Episode" or "Episodes" within the disclosure line (it should have a TermInfo or tooltip indicator such as an underline, info icon, or similar)
4. Click on the "Episode" term in the disclosure line

**Expected Result:**
- A tooltip or popover appears with the definition of "Episode" (first-trigger observation, consecutive same-symbol signal-days collapsed)
- The tooltip does NOT navigate to another page
- The tooltip can be dismissed by clicking elsewhere

---

### UT-11 — Toggling view does not change the as-of date or page URL parameter (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Note the current URL in the browser address bar (look for any `?asof=` parameter or its absence)
3. Click the "Pooled" button in the segmented toggle and wait for figures to refresh
4. Note the URL again
5. Click "Episodes" and note the URL again

**Expected Result:**
- The `?asof=` query parameter in the URL (if present) is unchanged after toggling
- No full page navigation occurs (back button does not show a new history entry for each toggle)
- The URL change (if any) is limited to reflecting the view selection, NOT a change in the analysis date

---

### UT-12 — Event study figures (hit-rate, expectancy) are present in both modes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research`
- The event study lab is loaded with a subject that has sufficient observations to show figures

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the event study lab to load and show the full set of figures in Episodes mode
3. Confirm the following figure types are visible: hit-rate percentage, expectancy value, MAE/MFE figures, by-regime breakdown, by-sector breakdown
4. Click the "Pooled" button in the segmented toggle and wait for figures to refresh
5. Confirm the same set of figure types is still visible in Pooled mode

**Expected Result:**
- In Episodes mode: hit-rate %, expectancy, MAE/MFE, by-regime, by-sector figures all render (not blank, not "N/A" unless the subject has truly zero observations)
- In Pooled mode: the same complete set of figures renders — no figure disappears or shows an error placeholder
- The numeric values differ between Episodes and Pooled modes (confirming both modes are correctly computing from different observation sets)

---

### UT-13 — /research/samples sort and filter controls still work after view parameter addition (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Navigate to `/research/samples` via an N= chip from the event study lab (Episodes or Pooled mode)
- The samples page loads with rows visible

**Steps:**
1. Navigate to `http://localhost:3835/research` and click an N= chip in Episodes mode to open `/research/samples` in a new tab
2. On the samples page, locate the sort controls (column headers or sort dropdowns)
3. Click a sort control (e.g., click the "Return" or "Symbol" column header) to sort the rows
4. Verify the rows re-order

**Expected Result:**
- Sort controls are present on the `/research/samples` page
- Clicking a sort control changes the order of the displayed rows
- No error or blank page appears after sorting
- The row count does not change when sorting (same total as the N= value from the chip)

---

### UT-14 — "Episode" and "Pooled (per-signal-day)" glossary entries on /methodology are complete (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/methodology`

**Preconditions:**
- Navigate to `http://localhost:3835/methodology`

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Wait for the page to fully load
3. Use Ctrl+F (browser find) to search for "Episode"
4. Read the definition shown for the "Episode" glossary entry
5. Use Ctrl+F to search for "Pooled"
6. Read the definition shown for the "Pooled (per-signal-day)" glossary entry

**Expected Result:**
- "Episode" entry is present with a definition that explains first-trigger observation and consecutive same-symbol collapse (does NOT just say "Episode" with no definition)
- "Pooled (per-signal-day)" entry is present with a definition that explains per-signal-day observation counting (does NOT just say "Pooled" with no definition)
- Both entries have distinct, authored definitions that are different from each other
- No other existing glossary entries are missing or broken

---

### UT-15 — Episodes mode is the default on every fresh page load (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Browser has no cached state for `/research` (use a private/incognito window or clear state)

**Steps:**
1. Open a private/incognito browser window
2. Navigate to `http://localhost:3835/research`
3. Wait for the event study lab to load
4. Without clicking anything, observe the state of the Episodes/Pooled toggle

**Expected Result:**
- On every fresh load, the "Episodes" button is highlighted/active
- The "Pooled" button is visible but not highlighted
- The disclosure line shows episode-collapsed counts (not pooled signal-day counts)
- The n value is the lower (collapsed) count, not the higher per-signal-day count

---

### UT-16 — Episodes/Pooled toggle is visually distinct and labelled clearly (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Navigate to `http://localhost:3835/research` and wait for the event study lab to load

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Visually locate the Episodes/Pooled toggle without using browser DevTools
3. Verify the toggle is positioned near the subject selector or event study controls (not buried in a footer or collapsed section)
4. Verify the active state of the toggle is clearly distinguished from the inactive state

**Expected Result:**
- The "Episodes" and "Pooled" buttons are visible without scrolling (or are in a prominent, expected location)
- The active button (Episodes by default) has a visually distinct style from the inactive button (e.g., filled background vs outline, different color, bold text)
- The label text "Episodes" and "Pooled" is human-readable and not just an icon

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /research loads with Episodes toggle visible | smoke | P1 | `/research` |
| UT-02 | /methodology loads with Episode and Pooled entries | smoke | P1 | `/methodology` |
| UT-03 | /research/samples loads with cohort detail line | smoke | P1 | `/research/samples` |
| UT-04 | Toggling Episodes to Pooled updates pill and n | happy-path | P1 | `/research` |
| UT-05 | Disclosure line shows n, Unique symbols, Episodes in Episodes mode | happy-path | P1 | `/research` |
| UT-06 | N= chip in Episodes mode links with view=episodes | happy-path | P1 | `/research` |
| UT-07 | N= chip in Pooled mode links with view=pooled | happy-path | P1 | `/research` |
| UT-08 | Samples drill-down from Episodes chip shows "Episodes (first-trigger)" | happy-path | P1 | `/research/samples` |
| UT-09 | Samples drill-down from Pooled chip shows "Pooled (per-signal-day)" | happy-path | P1 | `/research/samples` |
| UT-10 | Disclosure line tooltip appears on Episode term click | validation | P2 | `/research` |
| UT-11 | Toggling view does not change as-of date or URL | validation | P2 | `/research` |
| UT-12 | Event study figures present in both Episodes and Pooled modes | regression | P1 | `/research` |
| UT-13 | /research/samples sort/filter controls still work | regression | P1 | `/research/samples` |
| UT-14 | Episode and Pooled glossary entries are complete on /methodology | regression | P2 | `/methodology` |
| UT-15 | Episodes mode is default on every fresh page load | ux | P2 | `/research` |
| UT-16 | Episodes/Pooled toggle is visually distinct and labelled clearly | ux | P2 | `/research` |

**P1 tests must all pass for browser QA verdict to be PASS.**
