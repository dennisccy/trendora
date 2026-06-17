# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — /stocks leaderboard loads with MDD columns present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and responding (verify with `curl http://localhost:8835/health`)
- Seed data is present (at least one stock row is visible on the leaderboard)

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the leaderboard table to fully load (spinner disappears, rows are visible)
3. Scan the column headers of the leaderboard table from left to right

**Expected Result:**
- The page renders with no blank screen or error banner
- Column headers for five forward-return columns are visible (e.g., "1d", "5d", "10d", "20d", "60d")
- Five additional MDD column headers appear to the right of the forward-return columns, labelled "1d MDD", "5d MDD", "10d MDD", "20d MDD", "60d MDD" (exact labels may vary; the pattern is `{horizon} MDD`)
- At least one table row is visible with values in the MDD cells (either a negative percentage like "−3.2%" or the text "NA")
- No JavaScript error banner or "Something went wrong" text is present on the page

---

### UT-02 — /stocks MDD cells show negative percentages or NA only (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Navigate to `/stocks?asof=2025-12-31` and confirm that at least five rows are visible with non-NA values in the forward-return columns (these rows should also have MDD data)

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the table to load
3. Inspect any cell in the "1d MDD" column where the adjacent "1d" forward-return cell shows a non-"NA" value
4. Read the value displayed in that MDD cell
5. Inspect any cell in the "60d MDD" column where the adjacent "60d" forward-return cell shows "NA"

**Expected Result:**
- Every MDD cell where the paired forward-return is a real number shows a value that is either "NA" or a percentage with a negative sign (e.g., "−0.5%", "−12.3%"); no positive MDD values appear anywhere in the table
- Every MDD cell where the paired forward-return shows "NA" also shows "NA" (never a fabricated 0.0% or any number)

---

### UT-03 — /stocks MDD column sort puts NA rows at the bottom (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Navigate to `/stocks?asof=2025-12-31` and confirm the table has a mix of rows with real MDD values and rows showing "NA" in the "5d MDD" column

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the table to load
3. Click the "5d MDD" column header once
4. Observe the order of rows in the table
5. Click the "5d MDD" column header a second time
6. Observe the order of rows again

**Expected Result:**
- After the first click: rows with real MDD values appear at the top of the table; all "NA" rows are pushed to the bottom; no "NA" row appears above a row with a real value
- After the second click: the sort order is reversed among the real-value rows; "NA" rows remain at the bottom regardless of the sort direction
- No page reload or API request is triggered — the table reorders instantly (client-side sort)

---

### UT-04 — /stocks MDD colour grading: more negative = redder (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Navigate to `/stocks?asof=2025-12-31` and confirm that the "10d MDD" column contains at least two rows with different MDD magnitudes (e.g., one row showing around −1% and another showing around −10% or worse)

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the table to load
3. Click the "10d MDD" column header to sort ascending by MDD (least negative first)
4. Compare the background or text colour of the cell in row 1 (smallest absolute drawdown, e.g., "−0.3%") against the cell near the bottom of the non-NA rows (largest absolute drawdown, e.g., "−18%")

**Expected Result:**
- The cell with the smaller absolute MDD (e.g., "−0.3%") has a lighter red or muted colour compared to the cell with the larger absolute MDD
- The cell with the largest absolute MDD shows a clearly darker or more saturated red colour
- No MDD cell uses a green colour; the colour scale is exclusively in the red/negative spectrum

---

### UT-05 — /stocks/[ticker] detail page shows Max drawdown beneath each horizon card (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- At least one stock ticker must be visible on the `/stocks?asof=2025-12-31` leaderboard
- The detail link for that ticker must be accessible (either click the ticker row or navigate directly)

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the table to load; note the ticker symbol in the first visible row (e.g., "AAPL")
3. Click on that ticker row or the ticker symbol link to open its detail page
4. On the detail page, locate the forward-return panel (a set of horizon cards labelled "1d", "5d", "10d", "20d", "60d")
5. Inspect each horizon card for a second line of text beneath the return value

**Expected Result:**
- The Stock Detail page opens without error (URL changes to `/stocks/AAPL?asof=2025-12-31` or similar)
- Each of the five horizon cards (1d, 5d, 10d, 20d, 60d) shows two lines: the top line is the return value (e.g., "+2.1%" or "NA") and the bottom line is labelled "Max drawdown" followed by a negative percentage or "NA"
- No horizon card is missing the "Max drawdown" sub-line
- The "Max drawdown" value on every card is either "NA" or a negative percentage (never positive)

---

### UT-06 — /themes leaderboard shows five MDD columns (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running
- Seed data contains at least one theme entry

**Steps:**
1. Navigate to `http://localhost:3835/themes?asof=2025-12-31`
2. Wait for the themes leaderboard table to load (rows are visible)
3. Scan the column headers of the table

**Expected Result:**
- The page renders without error
- Five forward-return column headers are visible (e.g., "1d", "5d", "10d", "20d", "60d")
- Five additional MDD column headers appear to the right of the forward-return columns (e.g., "1d MDD", "5d MDD", "10d MDD", "20d MDD", "60d MDD")
- At least one theme row displays values (real percentages or "NA") in the MDD cells

---

### UT-07 — /themes expanded-member row colspan covers MDD columns (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- At least one theme on the `/themes?asof=2025-12-31` table has an expand/collapse control (a "+" icon, chevron, or similar) to reveal its member stocks

**Steps:**
1. Navigate to `http://localhost:3835/themes?asof=2025-12-31`
2. Wait for the table to load
3. Click the expand control (e.g., the "+" button or row toggle) on the first theme that has it
4. Observe the expanded member row that appears below the theme row

**Expected Result:**
- The member row expands and is visible beneath the theme row
- The expanded member content spans the full width of the table including the five new MDD columns — there is no visual gap or truncation where the MDD columns are (the expanded row should not end mid-table)
- The member row does not throw a layout error or hide any column headers

---

### UT-08 — /sectors leaderboard shows five MDD columns (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running
- Seed data contains at least one sector entry

**Steps:**
1. Navigate to `http://localhost:3835/sectors?asof=2025-12-31`
2. Wait for the sectors leaderboard table to load
3. Scan the column headers of the table

**Expected Result:**
- The page renders without error
- Five forward-return column headers are visible
- Five additional MDD column headers appear immediately to the right of the forward-return columns
- At least one sector row displays values in the MDD cells

---

### UT-09 — /sectors MDD column sort: NA rows land last (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- At least one sector row on `/sectors?asof=2025-12-31` shows "NA" in the "20d MDD" column

**Steps:**
1. Navigate to `http://localhost:3835/sectors?asof=2025-12-31`
2. Wait for the table to load
3. Click the "20d MDD" column header

**Expected Result:**
- The table re-sorts by the "20d MDD" column
- All rows showing "NA" in the "20d MDD" column appear at the bottom of the table, below all rows with real negative MDD values
- No "NA" row appears above any row that has a real value in the "20d MDD" column

---

### UT-10 — /backtest evidence table contains Mean MDD column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend is running at http://localhost:3835
- A historical as-of date with available backtest data must be selected (use `?asof=2025-12-31`)
- The Backtest page must show an evidence/breakdown panel after loading

**Steps:**
1. Navigate to `http://localhost:3835/backtest?asof=2025-12-31`
2. Wait for the page to load; confirm the Backtest evidence section is visible
3. Locate and expand (or scroll to) the by-bucket breakdown table within the evidence panel
4. Inspect the column headers of that breakdown table

**Expected Result:**
- A column labelled "Mean MDD" (or equivalent, e.g., "Avg MDD", "Mean max drawdown") appears in the breakdown table alongside the mean-return and MAE/MFE columns
- Each "Mean MDD" cell shows either a negative percentage or "NA" (for rows with fewer observations than the minimum sample threshold)
- No "Mean MDD" cell shows a positive value

---

### UT-11 — /backtest evidence summary header contains Mean max drawdown figure (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Navigate to `/backtest?asof=2025-12-31` and confirm the evidence summary panel is visible

**Steps:**
1. Navigate to `http://localhost:3835/backtest?asof=2025-12-31`
2. Wait for the page to load
3. Locate the evidence summary header (the top-level summary card above the breakdown tables)
4. Look for a "Mean max drawdown" or "Mean MDD" figure in that header

**Expected Result:**
- A figure labelled "Mean max drawdown" (or "Mean MDD") is visible in the evidence summary header
- The value shown is a negative percentage (e.g., "−4.2%") or "NA"
- The figure is NOT a positive number

---

### UT-12 — /research event-study table contains Mean MDD column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The Research page must be accessible and an event study must be available (either pre-computed or runnable from the UI)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to load
3. Navigate to the "Setup & Pattern Lab" or "Event Study" tab/section
4. If an event study must be triggered, use the default settings and click the "Run" or "Compute" button; wait for results to load
5. Locate the per-horizon aggregates table in the event-study results
6. Inspect its column headers

**Expected Result:**
- A "Mean MDD" column is present in the per-horizon results table alongside the mean-return column
- Rows with sufficient observations show a negative percentage in the "Mean MDD" cell
- Rows with fewer observations than the minimum-sample threshold show "NA" in the "Mean MDD" cell (same NA discipline as other cells)

---

### UT-13 — /research Regime x Setup x Pattern table contains Mean MDD column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- The Research RSP (Regime x Setup x Pattern) table is visible on the Research page

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to load
3. Navigate to the "Regime × Setup × Pattern" tab or section
4. Wait for the RSP table to load
5. Inspect the column headers and a sample of cell values in the "Mean MDD" column

**Expected Result:**
- A "Mean MDD" column is present in the RSP table
- Each cell in the "Mean MDD" column shows either a negative percentage (e.g., "−2.8%") or "NA"
- No cell in the "Mean MDD" column shows a positive number

---

### UT-14 — /data page RebuildPanel loads with "all members present" note (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3835
- The backend universe snapshot is fully up to date (all members are present in the latest snapshot)
- Verify via the API: `curl -s http://localhost:8835/api/data | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('coverage',{}).get('absent_from_latest_snapshot',{}).get('absent_count',0))"` should return `0`

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to load
3. Look for the RebuildPanel section on the page
4. Inspect the coverage status note within the RebuildPanel

**Expected Result:**
- The page renders without error
- A RebuildPanel section is visible on the page
- A calm note indicating "all members present" (or equivalent phrasing) is shown within the RebuildPanel (the element with `data-testid="coverage-absent-none"` is present)
- No amber/yellow banner listing absent tickers is shown
- A "Rebuild snapshots for current universe" button is visible and its text is readable

---

### UT-15 — /data RebuildPanel shows amber banner when members are absent (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- The `/api/data` response shows `coverage.absent_from_latest_snapshot.absent_count > 0` (there are one or more tickers in the scanned universe that are missing from the latest snapshot)
- If the seed is fully rebuilt and no members are absent, this test may need to be verified by inspecting the component's conditional rendering logic rather than live browser state

**Steps:**
1. When the backend reports absent members, navigate to `http://localhost:3835/data`
2. Wait for the page to load
3. Look for an amber/yellow diagnostic banner within the RebuildPanel section
4. Read the text of the banner

**Expected Result:**
- An amber/yellow banner is visible (the element with `data-testid="coverage-absent-banner"` is present)
- The banner text includes a count of absent members (e.g., "3 members absent — rebuild to include them" or similar phrasing)
- The banner lists the absent ticker symbols
- No banner is shown when the count is 0 (the two states are mutually exclusive)

---

### UT-16 — /data rebuild button opens confirm modal without starting a job (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Navigate to `http://localhost:3835/data`
- The "Rebuild snapshots for current universe" button is visible and enabled (no rebuild job is currently running)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to load
3. Locate the "Rebuild snapshots for current universe" button (the element with `data-testid="rebuild-button"`)
4. Click the "Rebuild snapshots for current universe" button
5. Observe the modal that appears

**Expected Result:**
- A confirm modal overlay appears (the element with `data-testid="rebuild-confirm-modal"` is present)
- The modal contains a description of the rebuild action
- A "Confirm" button (`data-testid="rebuild-confirm-button"`) is visible within the modal without needing to scroll
- A cancel/dismiss option (e.g., "Cancel" button or close icon) is also visible
- No rebuild job has started yet — the page is still in the same state, no job card progress is visible

---

### UT-17 — /data confirm modal dismiss cancels the rebuild (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- The confirm modal is open (complete UT-16 first)

**Steps:**
1. With the confirm modal open (from UT-16), click the "Cancel" button or the close icon in the modal
2. Wait for the modal to close
3. Observe the state of the page

**Expected Result:**
- The modal closes and the page returns to its previous state
- No rebuild job has been started (no job progress card appears or advances)
- The "Rebuild snapshots for current universe" button is still visible and enabled
- No error message or warning is shown

---

### UT-18 — /data rebuild confirm starts a job and disables the rebuild button (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Navigate to `http://localhost:3835/data`
- No rebuild job is currently running (the rebuild button is enabled)
- The operator accepts that clicking Confirm will start a long-running rebuild job

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Click the "Rebuild snapshots for current universe" button (`data-testid="rebuild-button"`)
3. Wait for the confirm modal to appear
4. Click the "Confirm" button (`data-testid="rebuild-confirm-button"`)
5. Observe the page immediately after clicking Confirm

**Expected Result:**
- The confirm modal closes after clicking Confirm
- A job progress card appears on the `/data` page (the existing J-66 job card surface) showing the rebuild job is in progress
- The "Rebuild snapshots for current universe" button is now disabled (greyed out) while the job is running
- The job card shows progress counters (e.g., "processed X / Y") that are valid (X does not exceed Y)

---

### UT-19 — /data rebuild job appears in run-history after completion (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- A rebuild job has been started and completed (UT-18 must have been run and the job finished)
- The run-history section is visible on the `/data` page

**Steps:**
1. After the rebuild job finishes (job card shows a terminal status such as "completed" or "done"), scroll to the run-history section on `http://localhost:3835/data`
2. Look for an entry corresponding to the rebuild job that just ran

**Expected Result:**
- The run-history section contains an entry for the completed rebuild job
- The entry shows a terminal status (e.g., "completed", "done", or green indicator)
- The existing run-history entries from prior jobs are still visible (the rebuild did not erase history)

---

### UT-20 — Forward-return columns on /stocks remain functional after this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Navigate to `/stocks?asof=2025-12-31` and confirm at least five rows are visible

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the table to load
3. Click the "5d" (or "5d return") column header to sort the table by 5-day forward return
4. Observe that the table re-sorts by that column

**Expected Result:**
- The table re-sorts by the 5d forward return with NA values at the bottom (existing sort contract unchanged)
- No MDD columns interfere with the sort behaviour of the return columns
- The return values themselves are unchanged from what they were before this iteration (MDD columns are additive — return values must not be displaced or altered)

---

### UT-21 — MDD value is never positive anywhere on /stocks, /themes, /sectors (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`, `/themes`, `/sectors`

**Preconditions:**
- Seed data is loaded; historical as-of date with forward-return data available

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Sort by "1d MDD" ascending
3. Read the value in the topmost non-NA cell in the "1d MDD" column
4. Navigate to `http://localhost:3835/themes?asof=2025-12-31`
5. Read any non-NA value in the "1d MDD" column
6. Navigate to `http://localhost:3835/sectors?asof=2025-12-31`
7. Read any non-NA value in the "1d MDD" column

**Expected Result:**
- Every non-NA MDD value observed across all three pages is a negative percentage (includes a "−" sign or is shown in red)
- No MDD cell on any of the three pages shows a positive value such as "+1.2%" or "3.0%"

---

### UT-22 — /stocks as-of date control still works alongside MDD columns (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Historical seed data exists for at least two different dates

**Steps:**
1. Navigate to `http://localhost:3835/stocks?asof=2025-12-31`
2. Wait for the table to load and note the MDD column values for the first row
3. Use the as-of date control on the page to change to a different historical date (e.g., click the back arrow "◀" to move to an earlier date or select from the calendar)
4. Wait for the table to reload with the new date

**Expected Result:**
- The table reloads with data for the newly selected as-of date
- The MDD columns are still present and contain values (or NA) appropriate for that date
- The as-of date change does not break the MDD column rendering (columns still visible, no layout error)
- The URL updates to reflect the new as-of date (e.g., `?asof=2025-11-28` or similar)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | /stocks leaderboard loads with MDD columns present | smoke | P1 | `/stocks` |
| UT-02 | /stocks MDD cells show negative percentages or NA only | happy-path | P1 | `/stocks` |
| UT-03 | /stocks MDD column sort puts NA rows at the bottom | happy-path | P1 | `/stocks` |
| UT-04 | /stocks MDD colour grading: more negative = redder | ux | P2 | `/stocks` |
| UT-05 | /stocks/[ticker] detail page shows Max drawdown beneath each horizon card | happy-path | P1 | `/stocks/[ticker]` |
| UT-06 | /themes leaderboard shows five MDD columns | smoke | P1 | `/themes` |
| UT-07 | /themes expanded-member row colspan covers MDD columns | regression | P1 | `/themes` |
| UT-08 | /sectors leaderboard shows five MDD columns | smoke | P1 | `/sectors` |
| UT-09 | /sectors MDD column sort: NA rows land last | happy-path | P1 | `/sectors` |
| UT-10 | /backtest evidence table contains Mean MDD column | happy-path | P1 | `/backtest` |
| UT-11 | /backtest evidence summary header contains Mean max drawdown figure | smoke | P1 | `/backtest` |
| UT-12 | /research event-study table contains Mean MDD column | happy-path | P1 | `/research` |
| UT-13 | /research Regime x Setup x Pattern table contains Mean MDD column | happy-path | P1 | `/research` |
| UT-14 | /data page RebuildPanel loads with "all members present" note | smoke | P1 | `/data` |
| UT-15 | /data RebuildPanel shows amber banner when members are absent | validation | P2 | `/data` |
| UT-16 | /data rebuild button opens confirm modal without starting a job | happy-path | P1 | `/data` |
| UT-17 | /data confirm modal dismiss cancels the rebuild | validation | P2 | `/data` |
| UT-18 | /data rebuild confirm starts a job and disables the rebuild button | happy-path | P1 | `/data` |
| UT-19 | /data rebuild job appears in run-history after completion | regression | P1 | `/data` |
| UT-20 | Forward-return columns on /stocks remain functional after this iteration | regression | P1 | `/stocks` |
| UT-21 | MDD value is never positive anywhere on /stocks, /themes, /sectors | ux | P2 | `/stocks`, `/themes`, `/sectors` |
| UT-22 | /stocks as-of date control still works alongside MDD columns | regression | P1 | `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.**
