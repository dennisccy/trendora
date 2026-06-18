# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Research page loads with Downtrend Opportunity section visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running with seed data loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (all labs should render; allow up to 10 seconds for the warm-up state to resolve)
3. Scroll down past the Recovery-Turn Edge lab until the "Downtrend Opportunity" heading is in view

**Expected Result:**
- The page renders without a blank screen or error message
- The heading "Downtrend Opportunity" is visible below the Recovery-Turn Edge lab
- Three table panels are rendered side by side (or stacked): "Held up best", "Fell hardest", and "Recovery-turn edge by phase"
- No browser console errors are present

---

### UT-02 — Downtrend Opportunity conditioning dropdown changes table rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible on `/research` (scroll down past Recovery-Turn Edge lab)
- At least one conditioned cohort row is populated with numeric data (n > 0)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down until the "Downtrend Opportunity" section heading is visible
3. Locate the "Condition on" dropdown control in the Downtrend Opportunity section
4. Note the current cohort label on the first row in the "Held up best" table (e.g., "Bear" or a phase name)
5. Click the "Condition on" dropdown and select "Severity band" (if not already selected)
6. Verify the rows in all three tables update to show severity-band cohort labels (e.g., "Mild", "Moderate", "Severe") instead of phase labels
7. Click the "Condition on" dropdown again and select "P(bear) band"
8. Verify the rows in all three tables update to show P(bear) cohort labels (e.g., "Low", "Medium", "High")

**Expected Result:**
- Each change in the "Condition on" dropdown causes all three angle tables to re-render with cohort labels matching the selected dimension
- The as-of date shown in the global as-of control does NOT change when the dimension is switched
- No browser console errors appear during the interaction
- The page does NOT navigate away or reload

---

### UT-03 — N= chip opens count-coherent samples in a new tab (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` and `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The "Held up best" table in the Downtrend Opportunity section has at least one row with a visible `N=` chip and a count greater than 0

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Locate the first row in the "Held up best" table that shows an `N=` chip (e.g., "N=14")
4. Note the exact number shown in the chip (e.g., 14)
5. Click the `N=` chip — confirm it opens a new browser tab (middle-click or Ctrl+click if needed to force new tab)
6. In the new tab, wait for the `/research/samples` page to load
7. Confirm the URL contains `kind=downtrend_opportunity` as a query parameter
8. Read the total sample count displayed on the samples page (e.g., a row count or a "N=14 observations" heading)

**Expected Result:**
- A new browser tab opens at a URL matching `http://localhost:3835/research/samples?kind=downtrend_opportunity&...`
- The samples page renders a cohort header that identifies the conditioning dimension and cohort (e.g., "Downtrend opportunity — Phase: Bear", NOT a blank or generic header)
- The total sample count shown on the samples page exactly matches the number that was in the `N=` chip in step 4
- No "404" or "Invalid parameters" error appears on the samples page

---

### UT-04 — Horizon toggle updates Downtrend Opportunity table stats (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible and showing at least one table row with numeric values

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Locate the horizon toggle control (e.g., tabs or buttons labelled with day counts such as "5d", "10d", "20d")
4. Note the current "Mean" value in the first data row of the "Held up best" table
5. Click a different horizon (e.g., click "20d" if "5d" is currently selected)
6. Observe the "Mean", "Hit-rate", and "Expectancy" columns in all three tables

**Expected Result:**
- The numeric values in the "Mean", "Hit-rate", and "Expectancy" columns change to reflect the newly selected horizon
- The column headers do not change
- The `N=` chips may show different counts for the new horizon (this is expected)
- No browser console errors appear

---

### UT-05 — Episodes / Pooled toggle changes table row counts (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible and showing rows

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Note the count shown in the first `N=` chip in the "Held up best" table while in Episodes view
4. Locate the Episodes / Pooled toggle (shared with other labs; this toggle may appear near the top of the Research page or within the Downtrend Opportunity section)
5. Click the toggle to switch from "Episodes" to "Pooled"
6. Observe the row counts (`N=` chips) and stat values in the Downtrend Opportunity tables

**Expected Result:**
- The `N=` chip counts in the Downtrend Opportunity tables change when switching between Episodes and Pooled
- The tables above (existing event-study, regime-setup-pattern, recovery-turn-edge labs) are NOT affected — their data does not change when the toggle is used in the Downtrend Opportunity section
- No browser console errors appear

---

### UT-06 — As-of / All-history toggle scopes Downtrend Opportunity observations (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A historical as-of date is already selected via the global as-of switcher (e.g., a date in 2023 or 2024)

**Steps:**
1. Navigate to `http://localhost:3835/research` with a historical as-of date set in the URL or selected via the global as-of control
2. Scroll down to the "Downtrend Opportunity" section
3. Note the `N=` count in the first row of the "Held up best" table — this reflects the as-of-scoped observation set
4. Locate the As-of / All-history toggle in or near the Downtrend Opportunity section
5. Click to switch from "As-of" to "All-history"
6. Observe the `N=` chip counts in the Downtrend Opportunity tables

**Expected Result:**
- The `N=` counts increase (or differ) when switching from As-of to All-history, because All-history includes the full seed window while As-of filters to observations ≤ the selected date
- The global as-of date shown in the page header or as-of control does NOT change
- No second date picker or date input appears anywhere in the Downtrend Opportunity section

---

### UT-07 — Column header click sorts table; NA rows sort last (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The "Held up best" table in the Downtrend Opportunity section has multiple rows, at least one with numeric values and at least one with NA

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Held up best" table in the Downtrend Opportunity section
3. Click the "Mean" column header
4. Observe the row order — rows should re-sort ascending or descending by the Mean value
5. Click the "Mean" column header a second time
6. Observe the row order reverses
7. Locate any row showing "NA" in the Mean column and confirm it appears at the bottom of the sorted list in both ascending and descending order

**Expected Result:**
- Clicking a column header re-orders the table rows by that column's value
- A second click reverses the sort direction
- Rows with NA in the sorted column appear last regardless of sort direction (NA-last contract)
- No network request is made during the sort (client-side only — the page does NOT briefly show a loading spinner)

---

### UT-08 — Weakness angle "Fell hardest" table shows EVIDENCE ONLY label (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible on `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Locate the "Fell hardest" table panel
4. Read the label or badge displayed on or near the "Fell hardest" table header area
5. Inspect the table for any Buy, Sell, Short, Trade, Execute, or similar action buttons or links

**Expected Result:**
- A label reading "Research evidence only" or "EVIDENCE ONLY" is visible on or near the "Fell hardest" table
- There are NO buttons, links, or affordances suggesting order placement, short selling, or trade execution anywhere in or adjacent to the "Fell hardest" table

---

### UT-09 — Low-sample row shows NA and sample count (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A conditioned cohort (specific phase, severity band, or P(bear) band) has fewer observations than the minimum sample threshold, causing it to render NA

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Use the "Condition on" dropdown to select a dimension that produces at least one sparse cohort row (try "Severity band" or "P(bear) band" with a narrow filter if available)
4. Locate a table row where "Mean", "Hit-rate", and "Expectancy" cells all show "NA" or a dash
5. Read the `N=` chip or the "n" column value for that row

**Expected Result:**
- The NA row is rendered in the table (not hidden, not replaced by an error state)
- The "Mean", "Hit-rate", "Expectancy", and "Ret/DD" cells display "NA" or an empty/dash state
- The row still shows an integer value in the "n" or `N=` area, indicating the actual sample count
- No 500 error or blank panel appears

---

### UT-10 — Survivorship-bias caveat banner is present in Downtrend Opportunity section (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Read all text labels, banners, footnotes, or callout boxes within the Downtrend Opportunity section

**Expected Result:**
- A caveat banner or label is visible in the Downtrend Opportunity section that mentions survivorship bias (e.g., "Results are scoped to the current-membership universe" or "Survivorship bias applies")
- The label is clearly readable, not hidden behind a hover or collapsed accordion

---

### UT-11 — Macro publication-lag limitation label is visible in Downtrend Opportunity section (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible (macro is config-default-OFF; the label should appear regardless)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Read all text labels and disclosure notices within the section

**Expected Result:**
- A label is visible in the Downtrend Opportunity section indicating that macro inputs are optional and off by default (e.g., "Macro inputs are optional and off by default" or similar wording)
- The label also states that any macro value used for a date is only applied once that value was published on or before that date (i.e., the publication-lag contract is disclosed)
- No actual macro-conditioned values are shown in the tables (because macro is off by default)

---

### UT-12 — Data Manager Macro feed panel renders with four series rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Scroll down past the existing missing-data diagnostic section until the "Macro feed" panel is in view

**Expected Result:**
- A panel with the heading "Macro feed" is visible below the missing-data diagnostic section
- The panel contains a table with at least four rows, each describing a macro series (with columns for FRED id, publication lag, proxy symbol, and status/seed count)
- No blank panel, spinner-forever, or error message appears

---

### UT-13 — Macro feed panel shows env-var name without revealing the key value (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The FRED_API_KEY environment variable is NOT set (the default state)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down to the "Macro feed" panel
3. Locate the area that shows the FRED provider status or API key detection
4. Read the text carefully

**Expected Result:**
- The panel shows the environment variable NAME (e.g., "FRED_API_KEY") next to a status label like "not set (NA)" or "not detected"
- The panel does NOT display any actual API key value, token string, or credential anywhere on the page
- If the key were set, the label would read "detected" — but the key value itself would never appear

---

### UT-14 — Macro feed panel shows all three wiring legs as "off" in default config (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Macro is in the default configuration (all three wiring legs are off)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll down to the "Macro feed" panel
3. Locate the section that shows per-leg enable flags (severity / regime switching / study)

**Expected Result:**
- The severity wiring leg is shown as "off" or disabled
- The regime switching wiring leg is shown as "off" or disabled
- The study conditioning wiring leg is shown as "off" or disabled
- A note is visible in the panel stating that default figures are unchanged while all legs are off (e.g., "Default figures are unchanged — all wiring legs off")

---

### UT-15 — Samples drill-down page shows correct cohort header for downtrend-opportunity kind (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/samples`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section on `/research` is visible and has at least one `N=` chip with count > 0

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down to the "Downtrend Opportunity" section
3. Click the `N=` chip on any row in any of the three tables (this opens a new tab)
4. In the new tab, wait for `http://localhost:3835/research/samples` to fully load

**Expected Result:**
- The samples page renders with a cohort description header that identifies this as a downtrend-opportunity drill-down (e.g., "Downtrend opportunity — Phase: Bear" or "Downtrend opportunity — Severity band: Severe")
- The header is NOT blank, NOT "Unknown cohort", and NOT the generic event-study or regime-setup-pattern header
- A list or table of individual sample observations is rendered

---

### UT-16 — Existing event-study lab on /research still works after iter-32 changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Research page is accessible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the existing "Event Study" lab (it should appear above the new Downtrend Opportunity section)
3. Note the values shown in the first row of the event-study table for the default horizon
4. Click the Episodes / Pooled toggle and confirm the event-study table data changes
5. Click the toggle back to the original state

**Expected Result:**
- The Event Study lab renders with data (not empty, not a loading spinner frozen indefinitely)
- The Episodes / Pooled toggle affects the event-study table independently
- The `N=` chips in the event-study table link to samples via the prior-iteration kind (not "downtrend_opportunity")
- No data previously shown in the event-study table has disappeared or changed

---

### UT-17 — Existing recovery-turn-edge lab on /research still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Recovery-Turn Edge" lab (above the new Downtrend Opportunity section)
3. Verify the table renders with at least one row of data
4. Compare the "Recovery-turn edge by phase" table in the Downtrend Opportunity section (the third angle, "angle c") to the standalone Recovery-Turn Edge lab
5. Confirm both show the same row data for the same horizon

**Expected Result:**
- The standalone Recovery-Turn Edge lab shows the same rows and stats as the "Recovery-turn edge by phase" panel inside the Downtrend Opportunity section
- The standalone lab did NOT change its data or layout from the prior iteration

---

### UT-18 — Dashboard Market-Phase panel is unchanged after iter-32 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard)

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running with seed data

**Steps:**
1. Navigate to `http://localhost:3835/` (the Dashboard)
2. Locate the Market-Phase panel
3. Note the regime label (e.g., "Risk-On", "Risk-Off", "Transitional") and severity score displayed
4. Note whether any macro-influenced score indicator or label is visible

**Expected Result:**
- The Market-Phase panel renders with a regime label and severity score
- No new date picker or second date control appears in the Market-Phase panel
- No macro-conditioned values are shown (macro is off by default; the panel is unchanged from the prior iteration)
- The date shown corresponds to the global as-of, not any new panel-local date

---

### UT-19 — Global as-of control is the single date selector; no new date picker added (regression / critical anti-goal)

**Type:** regression
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Downtrend Opportunity section is visible on `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Count every date-input, date-picker, calendar widget, or date text-field visible on the entire page
3. Scroll through the full Downtrend Opportunity section (conditioning controls, horizon toggle, Episodes/Pooled, As-of/All-history) and confirm none of these controls is a date picker
4. Confirm the As-of / All-history toggle is a MODE control, not a date input — it switches between two data views without asking for a date

**Expected Result:**
- Exactly ONE date control exists on the page: the global as-of switcher (the same one used by all other Research labs and all other pages)
- The Downtrend Opportunity section does NOT contain any date `<input type="date">`, calendar popover, or text field for entering a date
- J-92's macro surfaces also add NO date control anywhere on the page

---

### UT-20 — Downtrend Opportunity section is scroll-reachable without new nav entry (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Look at the top-level navigation (sidebar or header) for any new menu item or link related to "Downtrend Opportunity" or "Macro"
3. Scroll down the `/research` page without clicking anything

**Expected Result:**
- There is NO new top-level navigation entry for "Downtrend Opportunity" or "Macro" — the feature is accessible by scrolling within the existing `/research` page
- The Downtrend Opportunity section is reachable by scrolling down past the existing labs (event-study, regime-setup-pattern, recovery-turn-edge)
- The section heading "Downtrend Opportunity" is clearly visible without requiring a dropdown or accordion to be expanded first

---

### UT-21 — Downtrend Opportunity panel shows loading state then data (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835 with a clean page load (no prior cached result)

**Steps:**
1. Navigate to `http://localhost:3835/research` (fresh load or hard-refresh with Ctrl+Shift+R)
2. Immediately scroll to the Downtrend Opportunity section
3. Observe the state before data arrives

**Expected Result:**
- The Downtrend Opportunity section shows a loading skeleton or spinner while data is being fetched (not a blank white area)
- After a few seconds, the skeleton transitions to the actual tables
- The loading state is localized to the Downtrend Opportunity section — other labs can load independently

---

### UT-22 — Macro feed panel in Data Manager shows honest NA for walled FRED provider (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The FRED_API_KEY environment variable is NOT set (simulating a walled/unavailable provider)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Scroll to the "Macro feed" panel
3. Read the status column for each macro series row
4. Observe whether any macro series shows a fabricated or estimated value

**Expected Result:**
- Each macro series row shows "NA", "unavailable", "not set", or "blocked" in the status column
- No fabricated, interpolated, or estimated macro values are displayed
- The panel does not show an unhandled error page or crash the Data Manager page

---

### UT-23 — Existing Data Manager page loads without regression (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate the existing missing-data diagnostic section and the existing provider catalog (Yahoo, Tiingo, Alpha Vantage, etc.)

**Expected Result:**
- The Data Manager page loads without a blank screen or crash
- The existing missing-data diagnostic section is still present and renders data
- The existing provider catalog shows the same providers as before (Yahoo, Tiingo, Alpha Vantage, etc.)
- The new "Macro feed" panel appears AFTER (below) the existing sections, not replacing them

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research page loads with Downtrend Opportunity section visible | smoke | P1 | `/research` |
| UT-02 | Conditioning dropdown changes table rows | happy-path | P1 | `/research` |
| UT-03 | N= chip opens count-coherent samples in new tab | happy-path | P1 | `/research`, `/research/samples` |
| UT-04 | Horizon toggle updates table stats | happy-path | P1 | `/research` |
| UT-05 | Episodes/Pooled toggle changes row counts | happy-path | P1 | `/research` |
| UT-06 | As-of/All-history toggle scopes observations | happy-path | P1 | `/research` |
| UT-07 | Column sort works; NA rows sort last | happy-path | P1 | `/research` |
| UT-08 | Fell hardest table shows EVIDENCE ONLY label | validation | P1 | `/research` |
| UT-09 | Low-sample row shows NA and sample count | validation | P1 | `/research` |
| UT-10 | Survivorship-bias caveat banner present | validation | P1 | `/research` |
| UT-11 | Macro publication-lag limitation label visible | validation | P1 | `/research` |
| UT-12 | Data Manager Macro feed panel renders | smoke | P1 | `/data` |
| UT-13 | Macro panel shows env-var name, not key value | validation | P1 | `/data` |
| UT-14 | All three wiring legs shown as off by default | validation | P1 | `/data` |
| UT-15 | Samples page shows correct cohort header for downtrend-opportunity | smoke | P1 | `/research/samples` |
| UT-16 | Existing event-study lab still works | regression | P1 | `/research` |
| UT-17 | Existing recovery-turn-edge lab still works | regression | P1 | `/research` |
| UT-18 | Dashboard Market-Phase panel unchanged | regression | P1 | `/` |
| UT-19 | Global as-of is the only date selector | regression | P1 | `/research` |
| UT-20 | Downtrend Opportunity reachable by scroll, no new nav entry | ux | P2 | `/research` |
| UT-21 | Panel shows loading skeleton then data | ux | P2 | `/research` |
| UT-22 | Macro panel shows honest NA for walled FRED provider | error | P2 | `/data` |
| UT-23 | Existing Data Manager page loads without regression | regression | P1 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**
