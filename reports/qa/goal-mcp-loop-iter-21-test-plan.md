# Goal Iteration 21 — Functional Test Plan

**Phase:** goal-mcp-loop-iter-21  
**Date:** 2026-07-08  
**Frontend Present:** yes

## Phase Goal

Flip journey J-13 from `partial → passing` by executing the canonical browser-QA verification of the already-committed iter-20 Data Manager work (548-pool Fetch scope, Expand-universe removal, two-group availability legend) live against running services, capturing the missing evidence trail, and formally re-clearing the closure gate. No new source code.

---

## Test Cases

### TC-01 — Availability data page loads without backend unavailable error

**Type:** browser  
**Preconditions:**
- Backend service running at `:8255` and responding to `/health`
- Frontend service running at `:3255`
- User navigates to `/data`

**Steps:**
1. Navigate to `http://localhost:3255/data` (or the configured frontend URL)
2. Wait for the page to fully load (availability heatmap visible)
3. Inspect the page for the presence of the "Backend unavailable" error card
4. Verify all expected panels render (job-kind selector, availability heatmap, etc.)

**Expected outcome:** The data page loads fully with no "Backend unavailable" card; the availability heatmap is visible and the job-kind selector is rendered.  
**Pass criteria:** Page renders with all expected panels; zero "Backend unavailable" error cards present; HTTP status 200.

---

### TC-02 — Job-kind picker no longer shows "Expand universe" option

**Type:** browser  
**Preconditions:**
- User is on `/data` page with page fully loaded
- Job-kind selector is visible

**Steps:**
1. Locate the job-kind selector dropdown on `/data`
2. Click to open the dropdown menu
3. Inspect the list of available job options
4. Verify "Expand universe" option is NOT present
5. Confirm "Fetch", "Backfill", and "Fetch+backfill" options ARE present

**Expected outcome:** Dropdown shows three options (Fetch, Backfill, Fetch+backfill) with "Expand universe" removed.  
**Pass criteria:** "Expand universe" does not appear in the dropdown; the three core job kinds are all selectable.

---

### TC-03 — Fetch job starts without error

**Type:** browser  
**Preconditions:**
- User is on `/data` page
- Job-kind dropdown is open
- "Fetch" option is visible

**Steps:**
1. Click the "Fetch" option from the job-kind dropdown
2. Click "Start" or the equivalent action button to initiate the job
3. Wait for the job to begin and observe the UI feedback (loading state, progress indicator)
4. Verify no error message appears

**Expected outcome:** Fetch job starts cleanly; no error toast or inline error message; loading UI is shown.  
**Pass criteria:** Job starts successfully without blocking error; spinner or progress state is visible.

---

### TC-04 — Backfill job starts without error

**Type:** browser  
**Preconditions:**
- User is on `/data` page
- Job-kind dropdown is open
- "Backfill" option is visible

**Steps:**
1. Click the "Backfill" option from the job-kind dropdown
2. Click "Start" or the equivalent action button to initiate the job
3. Wait for the job to begin and observe the UI feedback
4. Verify no error message appears

**Expected outcome:** Backfill job starts cleanly; no error toast or inline error message; loading UI is shown.  
**Pass criteria:** Job starts successfully without blocking error; spinner or progress state is visible.

---

### TC-05 — Fetch+backfill job starts without error

**Type:** browser  
**Preconditions:**
- User is on `/data` page
- Job-kind dropdown is open
- "Fetch+backfill" option is visible

**Steps:**
1. Click the "Fetch+backfill" option from the job-kind dropdown
2. Click "Start" or the equivalent action button to initiate the job
3. Wait for the job to begin and observe the UI feedback
4. Verify no error message appears

**Expected outcome:** Fetch+backfill job starts cleanly; no error toast or inline error message; loading UI is shown.  
**Pass criteria:** Job starts successfully without blocking error; spinner or progress state is visible.

---

### TC-10 — Availability legend renders two labeled groups with non-amber top bucket

**Type:** browser  
**Preconditions:**
- User is on `/data` page with fully loaded heatmap
- Availability legend is visible (may need to scroll into view)

**Steps:**
1. Scroll the availability heatmap into full view (legend should be visible)
2. Inspect the legend visual structure for two distinct groups/sections
3. Locate the top density bucket (full bucket) and inspect its computed background-color
4. Verify the first group is labeled (e.g., "Price data — cell fill" or similar)
5. Verify a second group is labeled (e.g., "Scored snapshot — indicator" or similar)

**Expected outcome:** Legend shows two distinct, labeled groups; the top density bucket renders in blue.  
**Pass criteria:** `computed background-color` of top bucket is `rgb(166, 200, 242)` (blue) not `rgb(240, 180, 41)` (amber); both group labels are visible and distinct.

---

### TC-11 — Availability legend snapshot indicator renders violet color

**Type:** browser  
**Preconditions:**
- User is on `/data` page with fully loaded heatmap
- Availability legend is visible

**Steps:**
1. Scroll the availability heatmap and legend into full view
2. Locate the snapshot indicator ring/symbol in the legend (second group)
3. Inspect the computed color of the snapshot indicator
4. Verify it is violet, not green

**Expected outcome:** Snapshot indicator in the legend renders in violet color.  
**Pass criteria:** `computed color` or `background-color` of snapshot indicator is `rgb(167, 139, 250)` (violet) not `rgb(52, 211, 153)` (green); indicator is visibly distinct from the price-data density colors.

---

### TC-12 — All six density steps in legend are visibly distinct

**Type:** browser  
**Preconditions:**
- User is on `/data` page with fully loaded heatmap
- Availability legend is fully visible on screen

**Steps:**
1. Examine the price-data group (density steps) in the legend
2. Count the number of distinct color steps (should be 6 from empty to full)
3. Verify each step is visibly different from its neighbors
4. Note the color progression from empty to full (should be blue density ramp)

**Expected outcome:** All six density steps are visibly distinct colors; no two adjacent steps appear identical.  
**Pass criteria:** Six distinct shades are observable; color gradient is continuous and smooth; each step is distinguishable from its neighbors.

---

### TC-14 — Hover tooltip distinguishes backfill-gap day from snapshotted day

**Type:** browser  
**Preconditions:**
- User is on `/data` page with fully loaded heatmap
- Heatmap cells are visible
- At least one cell represents a backfill-gap day (no snapshot) and one represents a snapshotted day

**Steps:**
1. Identify a heatmap cell that represents a backfill-gap day (no computed snapshot)
2. Hover over that cell and inspect the tooltip
3. Verify the tooltip names "Fetch" in the text (e.g., "Fetch → fills")
4. Identify a different heatmap cell that represents a snapshotted day
5. Hover over that cell and inspect the tooltip
6. Verify the tooltip names "Backfill" in the text (e.g., "Backfill → scores")
7. Confirm tooltips are visibly different

**Expected outcome:** Two distinct tooltip messages: one naming Fetch (for backfill-gap), one naming Backfill (for snapshot).  
**Pass criteria:** Backfill-gap cell tooltip contains "Fetch"; snapshotted cell tooltip contains "Backfill"; tooltips are distinguishable and not identical.

---

### TC-16 — Availability card degrades gracefully on API failure

**Type:** browser  
**Preconditions:**
- User is on `/data` page
- Network or mock setup allows simulating a failed `GET /api/data/availability` call
- Frontend error boundary is in place

**Steps:**
1. Simulate or intercept a failed `GET /api/data/availability` call (500 or network error)
2. Observe the availability card's rendered state
3. Verify the card does not crash or show a blank application-error page
4. Inspect the error message for honesty (e.g., "Availability could not load... No cells are shown rather than fabricated values")
5. Confirm the rest of the page remains usable (other panels/controls still interactive)

**Expected outcome:** Availability card shows a graceful error message; the page does not crash or become unusable.  
**Pass criteria:** Error card is bounded within the error boundary; an honest "could not load" message is shown; no fabricated data is displayed; other page sections remain interactive.

---

### TC-17 — Stocks page with Sector sort completes without crash (regression: J-01/UT-17)

**Type:** browser  
**Preconditions:**
- User navigates to `/stocks`
- Stocks leaderboard is fully loaded
- Sector column is visible

**Steps:**
1. Navigate to `/stocks`
2. Wait for leaderboard to fully load
3. Click the "Sector" column header to sort by sector
4. Wait for sort to complete and observe the page
5. Verify no crash, no blank error page, no console errors

**Expected outcome:** Stocks page reorders by sector; leaderboard remains interactive and fully rendered.  
**Pass criteria:** Sort completes without error; leaderboard is sorted by sector; page is responsive and clickable.

---

### TC-18 — Evidence badges display "Not yet proven" status (regression: J-03/UT-18)

**Type:** browser  
**Preconditions:**
- User navigates to `/stocks`
- Stocks leaderboard is fully loaded
- Score columns are visible

**Steps:**
1. Navigate to `/stocks`
2. Locate any score column (Leadership, Entry Quality, or Risk)
3. Inspect the badge or status indicator next to the score
4. Verify the badge displays "Not yet proven" or equivalent status
5. Confirm the badge is visible and not hidden

**Expected outcome:** At least one score shows a "Not yet proven" evidence badge inline.  
**Pass criteria:** Badge text reads "Not yet proven"; badge is visibly rendered; it is clickable or otherwise interactive.

---

### TC-19 — Evidence page renders without crash (regression: J-05/UT-19)

**Type:** browser  
**Preconditions:**
- User can navigate to `/evidence`
- Evidence page is defined and linked from main navigation

**Steps:**
1. Navigate to `/evidence` via URL or navigation menu
2. Wait for page to fully load
3. Verify no "Backend unavailable" error card
4. Confirm the page content is visible (ledger table or evidence list is shown)
5. Verify no blank error page or console crash

**Expected outcome:** Evidence page loads and displays content.  
**Pass criteria:** Page renders with 200 status; no crash; ledger/evidence content is visible; navigation remains intact.

---

### TC-20 — Stock detail page full-history chart renders (regression: J-10/UT-20)

**Type:** browser  
**Preconditions:**
- User navigates to `/stocks/{ticker}` for a known stock
- Full-history chart component is defined on the detail page

**Steps:**
1. Navigate to `/stocks/{ticker}` (e.g., `/stocks/AAPL`)
2. Wait for page to fully load
3. Locate the full-history deep chart component
4. Verify the chart is rendered with data points or bars
5. Confirm no error state or blank chart container

**Expected outcome:** Stock detail page loads; full-history chart is visible with data.  
**Pass criteria:** Chart renders with axes and data; no "could not load chart" error; chart is responsive.

---

### TC-21 — Universe count consistent across Methodology and Stocks pages (regression: J-12/UT-21)

**Type:** browser  
**Preconditions:**
- User navigates to both `/methodology` and `/stocks` pages
- Universe count or pool size is displayed on both pages

**Steps:**
1. Navigate to `/methodology`
2. Locate and note the displayed universe count or pool size
3. Navigate to `/stocks`
4. Locate and note the displayed universe count or pool size
5. Compare the two values

**Expected outcome:** Both pages report the same universe/pool count.  
**Pass criteria:** Universe count on `/methodology` equals universe count on `/stocks`; both pages show consistent numeric values (e.g., "548" or similar).

---

### TC-50 — Backend J-13-relevant tests pass (unit/integration)

**Type:** api  
**Preconditions:**
- Backend environment set up with Python venv and dependencies
- Database seeded with test data
- Current working directory is `/apps/backend`

**Steps:**
1. Clear any stale pytest temp files: `rm -rf /tmp/pytest-of-*`
2. Run the scoped test suite:
   ```bash
   cd /home/dennis-chan/Git/trendora/apps/backend && \
   .venv/bin/python -m pytest \
     tests/test_data_manager.py \
     tests/test_data_manager_jobs_pipeline.py \
     tests/test_data_manager_parallel.py \
     tests/test_seed_loader_pool.py \
     -v
   ```
3. Capture exit code and output
4. Verify all tests pass (exit code 0)
5. Confirm no test regressed from iter-20

**Expected outcome:** All four test files pass; no failures or errors; test count matches or exceeds iter-20 baseline.  
**Pass criteria:** Exit code is 0; all test cases marked PASSED; no FAILED or ERROR states; output confirms byte-identical availability computation test passes.

---

### TC-51 — Git diff confirms zero source code changes

**Type:** artifact  
**Preconditions:**
- Repository is at HEAD after development turn
- No uncommitted changes are expected

**Steps:**
1. Run the following commands:
   ```bash
   cd /home/dennis-chan/Git/trendora && \
   git diff HEAD -- \
     apps/backend/app/engine/data_manager.py \
     apps/frontend/app/data/page.tsx \
     apps/frontend/components/availability-heatmap.tsx \
     apps/frontend/app/globals.css \
     apps/frontend/tailwind.config.ts
   ```
2. Capture the output
3. Verify the output is empty (no diffs)

**Expected outcome:** All five J-13 implementation files show zero changes from HEAD.  
**Pass criteria:** `git diff` command returns empty output; exit code is 0; all five files are untouched.

---

## Summary

**Total test cases:** 15  
**Browser tests:** 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-10, TC-11, TC-12, TC-14, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21)  
**API tests:** 1 (TC-50)  
**Artifact checks:** 1 (TC-51)

**Coverage map:**
- J-13 target: TC-01, TC-02, TC-03, TC-04, TC-05, TC-10, TC-11, TC-12, TC-14, TC-16 (10 cases)
- J-13 P1 priority: TC-02, TC-03, TC-04, TC-05, TC-10, TC-11, TC-12, TC-14 (8 cases, equiv. to iter-20 UT-02/03/04/05/10/11/12/14)
- Regression replay: TC-17, TC-18, TC-19, TC-20, TC-21 (5 cases, J-01/J-03/J-05/J-10/J-12)
- Code verification: TC-50, TC-51 (2 cases)

**Notes:**
- This is a verification-only iteration; all browser tests execute against live running services (`:3255` frontend, `:8255` backend).
- Screenshot capture is required for all visual assertions (TC-10, TC-11, TC-12, TC-14); screenshots must be saved to `reports/qa/goal-mcp-loop-iter-21-evidence/` with md5-distinct hashes and proper naming.
- Backend tests (TC-50) must complete successfully and quickly (scoped tests only; no full 30-year suite).
- No source code changes are expected; all implementation files must show zero diff from HEAD.
