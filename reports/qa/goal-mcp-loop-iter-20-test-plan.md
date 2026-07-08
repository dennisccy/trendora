# goal-mcp-loop-iter-20 Functional Test Plan

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-07
**Frontend Present:** yes

## Phase Goal

Data Manager achieves coherence with the committed 548-name pool: the generic Fetch job covers the entire pool (not just the ~122 context symbols), the "Expand universe" job option is removed, and the per-date availability heatmap's legend unambiguously separates price-data completeness (cell fill) from scored-snapshot existence (indicator) so no two visual encodings collide.

## Test Cases

### TC-01 — Generic Fetch job covers the full 548-name pool + context symbols

**Type:** api
**Preconditions:** Backend is running; a clean seed directory with the full committed 548-name pool exists at `apps/backend/data/seed-stooq-30y/prices/`.

**Steps:**
1. Call `GET /api/data/jobs/check?kind=fetch`
2. Parse the response to extract the target symbol set for a fresh-fetch job
3. Count the total symbols and verify they form a superset of the 548 committed-pool names
4. Verify that all context symbols (benchmarks, ETFs, `^VIX`, macro proxies) are present

**Expected outcome:** The Fetch job's symbol set includes every pool name plus all context symbols.
**Pass criteria:** `symbols_total ≥ 548` AND every symbol in `read_pool(seed_dir)` is present AND every context symbol from `all_seed_symbols(cfg)` is present.

---

### TC-02 — compute_availability output is byte-identical before and after the wiring change

**Type:** api
**Preconditions:** Backend is running; the seed directory and database state are identical to before the change.

**Steps:**
1. Call `GET /api/data/availability?as_of=<recent_date>`
2. Record the response fields: `symbols_with_bars`, `total_symbols`, `snapshot_exists`
3. Verify the response matches a known baseline snapshot (same date, same database state)

**Expected outcome:** The availability data fields are unchanged from the committed baseline.
**Pass criteria:** `symbols_with_bars`, `total_symbols`, and `snapshot_exists` byte-match the pre-change snapshot for the same as-of date.

---

### TC-03 — "Expand universe" option is removed from the job-kind picker

**Type:** browser
**Preconditions:** Frontend is running at `http://localhost:3000`; user navigates to `/data`.

**Steps:**
1. Load `/data` page
2. Locate the job-kind `<select>` element (labeled "Job kind" or similar)
3. Inspect the available `<option>` elements
4. Verify the text content of all options

**Expected outcome:** The `<select>` contains exactly three options: "Fetch", "Backfill", and "Both". No "Expand universe" option is present.
**Pass criteria:** DOM contains `<option value="fetch">`, `<option value="backfill">`, `<option value="both">` and NO `<option value="expand">`.

---

### TC-04 — Fetch and Backfill jobs still start without error after Expand removal

**Type:** browser
**Preconditions:** Frontend is running; user is on `/data` page; backend is ready to accept job requests.

**Steps:**
1. Select "Fetch" from the job-kind picker
2. Click "Start" or the submit button
3. Observe the page for 2–3 seconds; verify no error toast or console error is thrown
4. Repeat for "Backfill" job
5. Repeat for "Both" job

**Expected outcome:** Each job kind submits successfully; the job form clears or the page transitions to a job-progress panel without errors.
**Pass criteria:** All three job kinds submit without throwing a client-side error or showing an error toast notification.

---

### TC-05 — Availability legend renders two labeled groups (Price data vs. Scored snapshot)

**Type:** browser
**Preconditions:** Frontend is running at `/data`; the availability heatmap is fully rendered (may require scrolling the page).

**Steps:**
1. Scroll the heatmap and legend into view
2. Inspect the legend DOM for the presence of two labeled groups
3. Verify one group is labeled "Price data — cell fill" (or similar) and the other is "Scored snapshot — indicator"
4. Take a screenshot of the legend area (save to `reports/qa/goal-mcp-loop-iter-20-evidence/TC-05-legend-groups.png`)

**Expected outcome:** The legend clearly shows two distinct labeled groups separating the meaning of cell fill from the snapshot indicator.
**Pass criteria:** DOM contains two labeled legend sections with text distinguishing "Price data" and "Scored snapshot"; screenshot shows both labels clearly visible.

---

### TC-06 — Density ramp top bucket is not amber; snapshot indicator is not green

**Type:** browser
**Preconditions:** Frontend is running at `/data`; the availability heatmap is visible; browser dev tools can inspect computed styles.

**Steps:**
1. Scroll the availability heatmap legend into view
2. Inspect the computed background color of the density ramp's top ("full") bucket cell
3. Verify it is NOT the old amber hex `#f0b429`
4. Inspect the computed color of the snapshot indicator (the ring or marker element on heatmap cells)
5. Verify it is NOT green (NOT `#34d399`)
6. Take a screenshot showing both the color ramp and a cell with the snapshot indicator (save to `reports/qa/goal-mcp-loop-iter-20-evidence/TC-06-colors.png`)

**Expected outcome:** The top density bucket and snapshot indicator use visibly distinct, non-colliding colors that read clearly in the dark theme.
**Pass criteria:** Computed background-color of top bucket ≠ `#f0b429` AND computed color/ring of snapshot indicator ≠ `#34d399` AND neither collides perceptually with the density ramp.

---

### TC-07 — Hover a "bars-but-no-snapshot" date vs. a "has-snapshot" date; tooltip distinguishes them

**Type:** browser
**Preconditions:** Frontend is running at `/data`; the heatmap is loaded with mixed snapshot/no-snapshot cells; user can hover.

**Steps:**
1. Scroll the heatmap into view and locate a date (column) with at least one price-data-complete cell (high fill) but NO snapshot indicator
2. Hover that cell and record the tooltip text
3. Locate a nearby date with a complete cell (high fill) AND a snapshot indicator
4. Hover that cell and record the tooltip text
5. Compare the two tooltips; verify the difference is obvious and names the Fetch→fills / Backfill→scores workflow
6. Take a screenshot of each hover state (save to `reports/qa/goal-mcp-loop-iter-20-evidence/TC-07-no-snapshot-tooltip.png` and `TC-07-with-snapshot-tooltip.png`)

**Expected outcome:** The two tooltips are visibly and textually distinct; the no-snapshot tooltip acknowledges bars exist but no snapshot; the with-snapshot tooltip confirms both data and snapshot.
**Pass criteria:** Tooltip text explicitly mentions or implies "price data" vs "snapshot" difference AND names the Fetch and Backfill actions OR clearly states one has data/the other has a snapshot.

---

### TC-08 — Required-still-passing journey J-01: /stocks leaderboard + Sector sort renders correctly

**Type:** browser
**Preconditions:** Frontend is running; backend is running in prod mode (not dev mode); `/data` page has been loaded and a Fetch job has completed at least once.

**Steps:**
1. Navigate to `/stocks`
2. Observe the leaderboard rows
3. Verify each row renders without crashing and displays scores
4. Click the "Sector" column header to sort by sector
5. Observe the sorted leaderboard; verify no crash or blank panel

**Expected outcome:** The leaderboard renders, rows are sortable by sector, and no error occurs.
**Pass criteria:** Leaderboard rows are visible, Sector sort produces a visible change in row order, no application error or blank page.

---

### TC-09 — Required-still-passing journey J-03: Evidence status badges render as "Not yet proven" where applicable

**Type:** browser
**Preconditions:** Frontend is running; `/stocks` leaderboard is rendered.

**Steps:**
1. Navigate to `/stocks`
2. Inspect the score columns (Leadership, Entry Quality, Risk) on at least two rows
3. Verify that each score area includes an evidence badge
4. Locate at least one badge reading "Not yet proven" (if no evidence claim backs it)

**Expected outcome:** Evidence status badges are present on scores; at least one reads "Not yet proven".
**Pass criteria:** Each score row contains a visible evidence status badge; no score is displayed without a status label.

---

### TC-10 — Required-still-passing journey J-05: Evidence ledger renders

**Type:** browser
**Preconditions:** Frontend is running; user can navigate to `/evidence`.

**Steps:**
1. Click "Evidence" in the main navigation
2. Wait for the page to load
3. Verify a list or table of certified claims is rendered
4. Observe at least one row with: hypothesis, out-of-sample verdict, control comparison, registration date

**Expected outcome:** The Evidence ledger page loads and displays a list of claims with the expected columns.
**Pass criteria:** `/evidence` page renders without error; at least one row is visible with claim metadata fields.

---

### TC-11 — Required-still-passing journey J-10: Deep-history chart on /stocks/{ticker} displays long history

**Type:** browser
**Preconditions:** Frontend is running; a long-tenured stock (AAPL/MSFT) is loadable via the seed data.

**Steps:**
1. Navigate to `/stocks`
2. Click on a long-tenured ticker (e.g., AAPL)
3. Wait for the stock detail page `/stocks/AAPL` to load
4. Locate the price chart or historical data display
5. Verify the chart shows a history spanning well beyond 5 years (back toward 1996 or earlier)

**Expected outcome:** The chart displays deep historical data (20+ years) and does not crop at a 2021 floor.
**Pass criteria:** Chart x-axis shows dates before 2020 (e.g., 2015 or earlier); data is continuous and not synthesized.

---

### TC-12 — Required-still-passing journey J-12: Point-in-time universe on /methodology and /stocks is consistent

**Type:** browser
**Preconditions:** Frontend is running; `/methodology` and `/stocks` pages are loadable.

**Steps:**
1. Navigate to `/methodology`
2. Observe the universe breadth metric (total symbols under consideration)
3. Navigate to `/stocks`
4. Observe the leaderboard's symbol count or total universe size
5. Verify the counts are consistent (the same universe is used)

**Expected outcome:** The universe size is consistent across both pages; no data misalignment.
**Pass criteria:** Universe metadata on `/methodology` matches the symbol set rendered on `/stocks` leaderboard.

---

### TC-13 — Frontend typecheck (tsc --noEmit) is clean; no dangling references

**Type:** artifact
**Preconditions:** Frontend source code is present; TypeScript compiler is installed.

**Steps:**
1. Change directory to `apps/frontend`
2. Run `npx tsc --noEmit`
3. Capture the exit code and any error output

**Expected outcome:** The TypeScript compiler reports zero errors.
**Pass criteria:** Exit code is 0; no lines containing "error TS" appear in stderr.

---

### TC-14 — Backend unit tests pass: Fetch symbol set ⊇ committed pool + context, compute_availability byte-identical

**Type:** artifact
**Preconditions:** Backend source code is present; Python test environment is set up.

**Steps:**
1. Change directory to `apps/backend`
2. Run `python -m pytest tests/test_data_manager.py tests/test_data_manager_jobs_pipeline.py tests/test_seed_loader_pool.py -v`
3. Capture the output and exit code
4. Verify tests related to fetch symbol scope, pool membership, and compute_availability pass

**Expected outcome:** All targeted backend tests pass; no test failures related to symbol count, pool coverage, or availability output.
**Pass criteria:** Test suite exit code is 0; no FAILED lines for symbol/pool/availability tests; symbols_total count reflects the full 548 + context union.

---

### TC-15 — Market-cap display remains honest: no copy implies caps are on-demand-refreshable

**Type:** artifact
**Preconditions:** Frontend source code is present; `/data` page copy is visible.

**Steps:**
1. Open `apps/frontend/app/data/page.tsx`
2. Search for text mentioning "market cap", "refresh", "update caps", or similar
3. Verify no copy claims that market caps are dynamically or on-demand refreshable
4. Load `/data` in browser and inspect all visible text related to market caps

**Expected outcome:** The page makes no claim that market caps are fresh or on-demand-updated now that Expand is removed.
**Pass criteria:** No text containing "fresh", "refresh", "on-demand", or "update" appears in association with market cap; caps are presented as static/committed.

---

### TC-16 — No client error on `/data` page; degrades gracefully to error boundary

**Type:** browser
**Preconditions:** Frontend is running; backend is running or unavailable.

**Steps:**
1. Navigate to `/data`
2. If backend is temporarily unavailable, simulate a network error in dev tools or stop the backend
3. Observe whether an error boundary catches the error or if a blank page appears
4. Verify the page does NOT show a blank application-error page; instead, an error message or fallback UI appears

**Expected outcome:** The page degrades gracefully if data fails to load; no unhandled errors escape to a blank page.
**Pass criteria:** If data fetch fails, an error message or contained error UI is shown (not a blank page); no JavaScript console error is uncaught.

---

## Summary

**Total test cases:** 16
**API tests:** 2 (TC-01, TC-02)
**Browser tests:** 11 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-16)
**Artifact checks:** 3 (TC-13, TC-14, TC-15)

**Test categories:**
- **Core change validation:** TC-01 (Fetch scope), TC-02 (availability byte-identical), TC-03 (Expand removed)
- **Frontend functionality:** TC-04 (job form still works), TC-05–TC-07 (legend clarity and colors)
- **Regression replay:** TC-08–TC-12 (J-01, J-03, J-05, J-10, J-12 still pass)
- **Code quality & honesty:** TC-13 (typecheck), TC-14 (tests pass), TC-15 (market-cap copy), TC-16 (error handling)

