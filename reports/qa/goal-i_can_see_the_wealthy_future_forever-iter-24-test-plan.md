# Goal Iter-24 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-07
**Frontend Present:** yes

## Phase Goal

Users can see a descriptive coverage panel with universe-vs-symbols clarity, a per-symbol coverage table showing in-universe/has-data/date-range/bar-count/thin-or-missing for each priced symbol and universe member, safely remove imported data by symbol/date range through a confirm-preview that protects the committed seed and cascades only dependent snapshots/forward-returns, and finally see the Expand-universe happy-path captured end-to-end in the browser.

## Test Cases

### TC-01 — Coverage definitions block displays universe-vs-symbols distinction

**Type:** browser
**Preconditions:** `/data` page is loaded; the app has the committed seed dataset (at minimum)

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Locate the Coverage panel
3. Inspect the definitions block for the following figures: price-history date range, universe size, symbol count, trading days, snapshot dates, backfill gaps
4. Verify each figure has a one-line plain-language definition next to it
5. Confirm the definitions block explicitly states the distinction between "universe" (config-screened scored names) and "symbols" (every ticker with stored bars)
6. Verify "backfill gap" is defined (a trading day with bars but no scanner snapshot)

**Expected outcome:** The Coverage definitions block is visibly displayed with each aggregate figure labelled and the universe-vs-symbols distinction explicitly shown in plain language

**Pass criteria:** All six figures (price-history range, universe size, symbol count, trading days, snapshot dates, gaps) are labelled with definitions; the universe-vs-symbols distinction is stated explicitly (not implicit); the definitions block does not error

---

### TC-02 — Per-symbol coverage table renders with all required columns

**Type:** browser
**Preconditions:** `/data` page is loaded

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Locate the per-symbol coverage table (below or within the CoveragePanel)
3. Verify the table contains the following columns: symbol, in-universe, has-data, date-range (first → last), bar-count, thin-or-missing flag
4. Verify at least one row is present for each stored symbol AND each config.universe.symbols member
5. Inspect a full-history universe member row and confirm all columns have values (date range not null, bar-count > 0, thin=false, missing=false)
6. Inspect a universe member with no bars and confirm: has-data=false, missing=true, date-range shows "N/A", bar-count shows 0
7. Inspect a non-universe priced symbol (e.g., an ETF or ^VIX) and confirm: in-universe=false, other columns reflect its actual data

**Expected outcome:** The per-symbol coverage table renders with all required columns, one row per stored symbol and per universe member, accurate data for each row type

**Pass criteria:** Table contains all six columns (symbol, in-universe, has-data, date-range, bar-count, thin-or-missing); every universe member shows either data or missing=true (no member silently absent); no-bars members show NA range and zero bar-count

---

### TC-03 — Per-symbol table's distinct-symbol row count matches displayed symbol_count

**Type:** browser
**Preconditions:** `/data` page is loaded; backend has returned the extended coverage payload

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Count the number of distinct symbols in the per-symbol coverage table (unique symbol values, excluding duplicates if any)
3. Locate the displayed `symbol_count` figure in the Coverage definitions/aggregate section
4. Assert the two counts are equal

**Expected outcome:** The distinct-symbol row count in the table equals the displayed symbol_count aggregate

**Pass criteria:** DOM query for distinct symbol rows == displayed symbol_count value (data-testid="symbol-count" or equivalent)

---

### TC-04 — Per-symbol table's in-universe row count matches displayed universe_count

**Type:** browser
**Preconditions:** `/data` page is loaded

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Count the number of rows in the per-symbol table where in-universe=true
3. Locate the displayed `universe_count` figure in the Coverage definitions section
4. Assert the two counts are equal

**Expected outcome:** The in-universe row count in the table equals the displayed universe_count aggregate

**Pass criteria:** DOM query for in-universe rows == displayed universe_count value (data-testid="universe-count")

---

### TC-05 — Per-symbol table supports universe-members-only filter

**Type:** browser
**Preconditions:** `/data` page is loaded; the table contains both universe members and non-universe symbols

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Locate the per-symbol coverage table
3. Find and click the "universe-members-only" filter toggle/checkbox
4. Verify the table is now filtered to show only rows where in-universe=true
5. Visually confirm every visible member shows either has-data=true OR missing=true (no member silently absent)
6. Verify non-universe symbols are hidden

**Expected outcome:** The universe-members-only filter narrows the table to membership only; every member row shows data or missing

**Pass criteria:** Filter applied; table shows only in-universe=true rows; every universe member row includes either data or explicit missing=true flag

---

### TC-06 — Coverage table displays gracefully on empty dataset

**Type:** browser
**Preconditions:** A test instance with an empty dataset (no bars, no universe members)

**Steps:**
1. Start the app on an empty dataset (or use a fixture)
2. Navigate to `/data` (Data Manager)
3. Inspect the Coverage definitions block
4. Inspect the per-symbol coverage table

**Expected outcome:** The definitions block shows null/zero values without error; the per-symbol table is empty but styled appropriately

**Pass criteria:** No 500 error; definitions show "N/A" or "0" gracefully; table is empty, not error-state

---

### TC-07 — Remove-data control is present on /data page

**Type:** browser
**Preconditions:** `/data` page is loaded

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Locate the Remove-data control (a panel or button to initiate data removal)

**Expected outcome:** The Remove-data control is visible and clickable

**Pass criteria:** Remove-data control/button is present on the page

---

### TC-08 — Remove-data confirm-preview shows removable bar details

**Type:** browser
**Preconditions:** `/data` page is loaded; a scope with user-added bars is ready to remove

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Open the Remove-data control
3. Select a scope (e.g., a symbol or a date range known to have user-added bars)
4. Trigger the preview (click "Preview" or equivalent)
5. Inspect the confirm-preview dialog for the following information:
   - Removable bar count (exact count of (symbol, date) pairs)
   - Removable bar date range (first → last)
   - Not-removable committed-seed breakdown (count and reason "committed seed")
   - Cascade list (dependent scanner_runs, scanner_results, sector_scores, theme_scores, forward_returns rows that would be deleted)

**Expected outcome:** The confirm-preview dialog displays exact removable bar count + range, explicit committed-seed breakdown with reason, and the cascade of dependent rows

**Pass criteria:** Preview shows all four pieces of information; counts are exact integers; cascade list identifies only rows that derive solely from the to-be-removed bars

---

### TC-09 — Remove-data refuses seed-only removal with explicit reason

**Type:** browser
**Preconditions:** `/data` page is loaded; a user attempts to remove a scope that is entirely committed seed

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Open the Remove-data control
3. Select a scope known to be entirely committed seed (e.g., a symbol or date range fully covered by meta.json windows)
4. Attempt to trigger the removal (click Confirm or equivalent)

**Expected outcome:** The removal is refused; an explicit message states the reason: "committed seed cannot be removed"

**Pass criteria:** Removal is not executed (no bars deleted); an explicit 400/422-class error or a disabled confirm button with a clear reason message is shown

---

### TC-10 — Remove-data succeeds and updates coverage on user-added scope (fixture test)

**Type:** browser
**Preconditions:** A test fixture with user-added bars beyond the committed seed is set up; `/data` page is loaded

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Note the current per-symbol coverage table and as-of date switcher state
3. Open the Remove-data control
4. Select a scope known to have only user-added bars
5. Preview the removal
6. Confirm the removal
7. Wait for the page to re-read the coverage data
8. Inspect the per-symbol table and as-of date switcher

**Expected outcome:** The removal succeeds; the per-symbol coverage table is updated to reflect the smaller dataset (removed symbols/dates no longer appear or show zero bars); the as-of date switcher reflects only the remaining dataset dates

**Pass criteria:** Removal succeeds; per-symbol table updates immediately; removed rows or bar-counts reflect the smaller dataset; as-of dates list no longer shows dates with only removed bars

---

### TC-11 — Remove-data capture: preview screenshot shows all details

**Type:** browser
**Preconditions:** `/data` page with a user-added scope; preview dialog is open

**Steps:**
1. Open the Remove-data preview for a scope with both removable and not-removable bars
2. Take a screenshot of the preview dialog

**Expected outcome:** The screenshot captures the complete preview: removable bar count + range, committed-seed line + reason, and cascade list

**Pass criteria:** Screenshot is saved to reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-24-evidence/ as TC-10-remove-preview.png (or similar)

---

### TC-12 — Remove-data capture: refusal screenshot shows reason

**Type:** browser
**Preconditions:** `/data` page with a seed-only scope

**Steps:**
1. Open the Remove-data control
2. Select a seed-only scope
3. Attempt confirmation; the action is refused
4. Take a screenshot of the refusal state

**Expected outcome:** The screenshot shows the disabled/rejected state with the explicit "committed seed" reason message

**Pass criteria:** Screenshot is saved as TC-11-remove-seed-only-refused.png

---

### TC-13 — Expand-universe job renders chunk progress x/N

**Type:** browser
**Preconditions:** `/data` page is loaded; the Expand option is available for a market-cap-capable source; dev server is clean and hydrated

**Steps:**
1. Start the dev server cleanly:
   - Kill any stray frontend/backend processes by port (frontend :3835, backend :8835)
   - Remove .next cache: `rm -rf apps/frontend/.next`
   - Confirm `GET /_next/static/chunks/main-app.js` → 200 and health badge cleared
   - Start the dev server: `bash scripts/start-frontend.sh` (or npm run dev)
2. Navigate to `/data` (Data Manager)
3. Select **Expand universe** from the job-kind dropdown
4. Select a market-cap-capable injected source (or a test source)
5. Submit the Expand job
6. Observe the job progress: the page shows "chunk x/N" as the job progresses

**Expected outcome:** The job runs; the page shows chunk progress (e.g., "chunk 1/5", "chunk 2/5", ...) as the expand job processes batches

**Pass criteria:** Progress display updates with chunk numbers; the page does not error or freeze during processing

---

### TC-14 — Expand-universe job shows completion screen with passers + omitted-with-reason

**Type:** browser
**Preconditions:** An Expand job is running on `/data`; it has progressed to completion

**Steps:**
1. Monitor the Expand job to completion
2. Wait for the screen-result block (completion screen)
3. Inspect the completion screen for:
   - A passers list (names that were successfully added to the universe)
   - An omitted-with-reason list (names that were not eligible and why)
4. Note the final `universe_count` displayed

**Expected outcome:** The completion screen shows both passers and omitted-with-reason; the universe-count has grown

**Pass criteria:** Passers list is populated; omitted-with-reason list shows explicit reasons (e.g., "market cap below threshold"); universe-count is greater than the pre-expand value

---

### TC-15 — Expand-universe: universe-count growth matches /methodology

**Type:** browser
**Preconditions:** An Expand job has completed on `/data`; the universe-count has grown

**Steps:**
1. Note the final universe-count displayed on `/data`
2. Navigate to `/methodology` (Methodology page)
3. Locate the "Universe Selection" size displayed on that page
4. Compare the two values

**Expected outcome:** The universe-count on `/data` matches the Universe-Selection size on `/methodology`

**Pass criteria:** Both pages show the same grown universe-count

---

### TC-16 — J-18 cross-check: exactly one date selector per page on /data

**Type:** browser
**Preconditions:** `/data` page is loaded; all controls are visible (Coverage table, Remove-data, Expand)

**Steps:**
1. Navigate to `/data` (Data Manager)
2. Inspect the page for all `<select>` elements with date-scoped options
3. Count the date selectors:
   - The global top-bar as-of switcher (expected: 1)
   - Any additional date selectors (e.g., in the Remove-data date-range inputs, in the Coverage table) — these should be action parameters, NOT viewing-as-of controls
4. Confirm that the Remove-data date-range inputs and any table date filters do NOT change the global as-of viewing control

**Expected outcome:** Exactly one date `<select>` per page is the global as-of switcher; the new Coverage table + Remove-data controls add zero viewing-as-of date state

**Pass criteria:** DOM count of date selectors with "as-of" or viewing-scoped semantics == 1; Remove-data date-range inputs are action parameters (not tied to the global as-of)

---

### TC-17 — Compute-coverage returns per-symbol table with exact values (full-history member)

**Type:** api
**Preconditions:** Backend is running; a fixture dataset with a full-history universe member exists

**Steps:**
1. Call `GET /api/data` (or run the backend method directly)
2. Extract the extended coverage payload (per-symbol rows)
3. Find a row for a full-history universe member (e.g., a stock with 200+ bars across many years)
4. Verify the row contains:
   - symbol: the stock symbol
   - in_universe: true
   - has_data: true
   - first: the earliest bar date
   - last: the latest bar date
   - bar_count: total number of bars (integer > 200)
   - thin: false (because bar_count >= min_history_bars)
   - missing: false

**Expected outcome:** The per-symbol row for a full-history member has exact, correct values

**Pass criteria:** All eight fields are present and correct; bar_count >= 200 (assuming default min_history_bars = 200); thin and missing are false

---

### TC-18 — Compute-coverage returns per-symbol table with exact values (thin member)

**Type:** api
**Preconditions:** Backend is running; a fixture dataset with a thin universe member exists (0 < bar_count < min_history_bars)

**Steps:**
1. Call `GET /api/data`
2. Extract the per-symbol rows
3. Find a row for a thin universe member (0 < bars < 200, assuming min_history_bars = 200)
4. Verify:
   - symbol: the stock symbol
   - in_universe: true
   - has_data: true
   - first/last: valid date range
   - bar_count: an integer between 1 and 199
   - thin: true
   - missing: false

**Expected outcome:** The thin member row is correctly flagged with thin=true

**Pass criteria:** thin=true; bar_count is between 1 and min_history_bars-1; has_data=true; missing=false

---

### TC-19 — Compute-coverage returns per-symbol table with exact values (no-bars member)

**Type:** api
**Preconditions:** Backend is running; a fixture dataset has a universe member with zero bars

**Steps:**
1. Call `GET /api/data`
2. Extract the per-symbol rows
3. Find a row for a universe member with no bars (a symbol in config.universe.symbols but no DailyPrice rows)
4. Verify:
   - symbol: the universe member symbol
   - in_universe: true
   - has_data: false
   - first: null or "N/A"
   - last: null or "N/A"
   - bar_count: 0
   - thin: false
   - missing: true

**Expected outcome:** A no-bars universe member shows has_data=false + missing=true + NA range — never fabricated or zero-bar-faked-as-present

**Pass criteria:** has_data=false; missing=true; first and last are null/NA; bar_count=0

---

### TC-20 — Compute-coverage returns per-symbol table with exact values (non-universe symbol)

**Type:** api
**Preconditions:** Backend is running; a fixture has a non-universe priced symbol (e.g., an ETF, ^VIX)

**Steps:**
1. Call `GET /api/data`
2. Extract the per-symbol rows
3. Find a row for a non-universe priced symbol
4. Verify:
   - symbol: the symbol (e.g., "SPY", "^VIX")
   - in_universe: false
   - has_data: true
   - first/last: valid bar date range
   - bar_count: integer (actual count of bars)
   - thin: depends on bar_count vs min_history_bars
   - missing: false (because it has bars)

**Expected outcome:** Non-universe symbols are included in the table with in_universe=false

**Pass criteria:** in_universe=false; has_data and bar_count reflect the actual bars stored

---

### TC-21 — Compute-coverage per-symbol table distinct-symbol count equals symbol_count aggregate

**Type:** api
**Preconditions:** Backend is running; a fixture with known universe size and symbol count exists

**Steps:**
1. Call `GET /api/data`
2. Extract the extended coverage payload
3. Count distinct symbol values in the per-symbol rows
4. Extract the symbol_count aggregate from the same payload
5. Assert the counts are equal

**Expected outcome:** The number of distinct symbols in the per-symbol table equals the symbol_count aggregate

**Pass criteria:** len(set(row['symbol'] for row in per_symbol_rows)) == coverage['symbol_count']

---

### TC-22 — Compute-coverage per-symbol table in-universe count equals universe_count aggregate

**Type:** api
**Preconditions:** Backend is running

**Steps:**
1. Call `GET /api/data`
2. Extract the per-symbol rows and universe_count aggregate
3. Count rows where in_universe=true
4. Assert the count equals universe_count

**Expected outcome:** The in-universe row count equals the universe_count aggregate

**Pass criteria:** sum(1 for row in per_symbol_rows if row['in_universe']) == coverage['universe_count']

---

### TC-23 — Compute-coverage reads min_history_bars threshold from config (no magic number)

**Type:** api
**Preconditions:** Backend is running; config.yaml specifies indicators.min_history_bars

**Steps:**
1. Call `GET /api/data`
2. Extract a thin member row and note its bar_count
3. Read config.yaml and note indicators.min_history_bars
4. Verify: the thin member's bar_count is between 1 and min_history_bars-1
5. Assert no hardcoded magic number (200) is used in place of the config value

**Expected outcome:** The thin threshold is read from config, not a hardcoded literal

**Pass criteria:** A member with 0 < bar_count < config_value is flagged thin=true; a member with bar_count >= config_value is flagged thin=false

---

### TC-24 — Seed-vs-user-added classifier: seed window dates are protected

**Type:** api
**Preconditions:** Backend is running; apps/backend/data/seed/meta.json exists with seed windows

**Steps:**
1. Read meta.json and extract seed windows (e.g., symbol "AAPL": first="2020-01-01", last="2023-12-31", bars=200)
2. Call the seed-vs-user-added classifier with a date inside that window (e.g., "2021-06-15")
3. Assert the result is "protected" (committed-seed)
4. Call the classifier with a date outside (e.g., "2024-01-01" if last="2023-12-31")
5. Assert the result is "removable" (user-added)

**Expected outcome:** A (symbol, date) inside a seed window is protected; a date beyond is removable

**Pass criteria:** Classifier returns "protected" for in-window dates; "removable" for out-of-window dates

---

### TC-25 — Remove-data preview: returns exact removable bars without deleting

**Type:** api
**Preconditions:** Backend is running; a fixture has user-added bars (e.g., bars dated after the seed windows)

**Steps:**
1. Call the preview endpoint (e.g., `POST /api/data/remove/preview`) with a scope (symbols and/or date range)
2. Inspect the preview response:
   - removable_bar_count: exact count of (symbol, date) pairs to be removed
   - removable_bar_range: [first_date, last_date] of removable bars
   - not_removable_committed_seed: count of bars in scope that are committed-seed, with reason "committed seed"
   - cascade: list of dependent scanner_runs, scanner_results, sector_scores, theme_scores, forward_returns that would be deleted
3. Query the database (e.g., `SELECT COUNT(*) FROM daily_prices`) before and after the preview
4. Assert the database is unchanged

**Expected outcome:** Preview returns exact details without deleting anything; database is unchanged

**Pass criteria:** All preview fields are populated and exact; DB row count before == DB row count after preview

---

### TC-26 — Remove-data removal: deletes only user-added bars in scope

**Type:** api
**Preconditions:** Backend is running; a fixture has user-added bars; a preview has been validated

**Steps:**
1. Note the current daily_prices row count for the scope
2. Call the removal endpoint (e.g., `POST /api/data/remove`) with the scope
3. Query the database after removal
4. Verify: all bars outside the scope are still present
5. Verify: all bars in the scope that are committed-seed are still present
6. Verify: all bars in the scope that are user-added are deleted

**Expected outcome:** Only user-added bars in scope are deleted; committed-seed bars and bars outside scope are untouched

**Pass criteria:** Deleted bar count == removable_bar_count from preview; remaining daily_prices include all seed bars

---

### TC-27 — Remove-data cascade: deletes only snapshot/forward-return rows that depend solely on removed bars

**Type:** api
**Preconditions:** Backend is running; a fixture has user-added bars; user-added bars have generated snapshots and forward-returns

**Steps:**
1. Run the preview and note the cascade list (scanner_results, sector_scores, theme_scores, forward_returns to be deleted)
2. Run the removal
3. Query the database for remaining snapshot rows
4. For each snapshot that was NOT in the cascade, verify it still has all its underlying bars (the input bars used to compute it)
5. For each snapshot that WAS in the cascade, verify it is no longer in the database

**Expected outcome:** A snapshot with all its bars intact is untouched; a snapshot that lost a required input bar is wholly deleted (not mutated)

**Pass criteria:** Remaining snapshots have complete bar coverage; no snapshot has a reference to a deleted bar; no cascade row remains that depended solely on removed bars

---

### TC-28 — Remove-data: wholly-committed-seed scope is refused with reason

**Type:** api
**Preconditions:** Backend is running

**Steps:**
1. Call the preview endpoint with a scope that is entirely committed-seed (e.g., symbol "AAPL" with a date range fully covered by meta.json)
2. Verify the preview shows removable_bar_count=0 and all bars are in the not_removable breakdown
3. Call the removal endpoint with the same scope
4. Expect a 400/422 error with an explicit reason message containing "committed seed"

**Expected outcome:** The removal is refused; an explicit error is returned; nothing is deleted

**Pass criteria:** HTTP status 400 or 422; error message includes "committed seed"; database is unchanged

---

### TC-29 — Remove-data: removal is recorded on DataProviderRun audit log

**Type:** api
**Preconditions:** Backend is running; a successful removal has been completed

**Steps:**
1. Query the `DataProviderRun` table (the append-only audit log)
2. Find the most recent entry
3. Verify it records:
   - kind: "remove" (or similar)
   - removed_symbol_count: the number of distinct symbols removed
   - removed_bar_count: the exact count of bars deleted
   - removed_date_range: [start, end] of removed bars
   - timestamp: the removal time

**Expected outcome:** The removal is recorded as a new DataProviderRun entry

**Pass criteria:** A new audit log entry exists with the removal details; the entry is append-only (no existing rows modified)

---

### TC-30 — Remove-data: compute_coverage updates after removal

**Type:** api
**Preconditions:** Backend is running; a removal has completed; the per-symbol table and aggregates have been re-computed

**Steps:**
1. Run a removal that removes user-added bars
2. Call `GET /api/data` to get the updated coverage
3. Verify:
   - symbol_count reflects the removed symbols (smaller or same)
   - universe_count reflects any universe members now with missing=true (or unchanged if no universe members had only removed bars)
   - per-symbol rows for removed-only symbols no longer appear (or show zero bars)
   - per-symbol rows for partially-removed symbols show updated bar_count

**Expected outcome:** Coverage aggregates and per-symbol table reflect the smaller dataset after removal

**Pass criteria:** symbol_count matches the distinct symbols still in daily_prices; universe members with removed bars now show missing=true; bar_counts are updated

---

### TC-31 — Remove-data: scorer/scanner compute not reachable from remove path

**Type:** artifact
**Preconditions:** Backend source code exists

**Steps:**
1. Inspect the remove endpoint handler in `apps/backend/app/api/data.py`
2. Trace the call path to `app.engine.data_manager.remove_data` (or equivalent)
3. Search the remove path for any imports or calls to:
   - `score_stocks`
   - `run_scan`
   - Any scanner/scoring compute method
4. Verify no such calls exist

**Expected outcome:** The remove path is a pure delete operation; no scoring recompute is reachable

**Pass criteria:** No score_stocks/run_scan/scoring method call found in the remove path

---

### TC-32 — Key safety: coverage/remove error strings carry no secret key/token

**Type:** api
**Preconditions:** Backend is running

**Steps:**
1. Call the coverage endpoint with a bad scope and inspect the error message
2. Call the remove endpoint with a bad scope and inspect the error message
3. Call the remove preview with an invalid date range and inspect the error
4. Grep each error message for patterns: `?token=`, `?apikey=`, `key=`, `secret=`
5. Verify no such patterns appear

**Expected outcome:** Coverage and remove error strings carry no key or secret (J-33 carry)

**Pass criteria:** No `?token=` / `?apikey=` patterns found in error messages

---

### TC-33 — Coverage on empty dataset returns null/zero/empty gracefully

**Type:** api
**Preconditions:** Backend is running on an empty dataset (no daily_prices, no snapshots)

**Steps:**
1. Call `GET /api/data`
2. Inspect the coverage payload:
   - Aggregates (symbol_count, universe_count, etc.) should be 0 or null
   - per-symbol rows should be empty array
3. Verify no 500 error is returned

**Expected outcome:** Coverage gracefully serves null/zero/empty on empty dataset; no error

**Pass criteria:** HTTP 200; aggregates are 0/null; per-symbol array is empty; no error field

---

### TC-34 — J-17 regression: fetch/backfill/both/expand jobs still execute

**Type:** api
**Preconditions:** Backend is running; the job system is intact

**Steps:**
1. Submit a fetch job and verify it completes
2. Submit a backfill job and verify it completes
3. Submit a both job and verify it completes
4. Submit an expand job and verify it completes

**Expected outcome:** All four job kinds still execute without regression

**Pass criteria:** Each job completes and produces a result; no errors

---

### TC-35 — J-34 regression: chunked/resumable engine + Resume intact

**Type:** api
**Preconditions:** Backend is running; a chunked fetch job has been started and paused

**Steps:**
1. Submit a fetch job with chunking enabled
2. Observe progress and pause (simulate a halt or interrupt)
3. Call the Resume endpoint (e.g., `POST /api/data/jobs/{id}/resume`)
4. Verify the job continues from where it left off and completes

**Expected outcome:** The Resume functionality still works; the chunked engine still handles resumable jobs

**Pass criteria:** Paused job is successfully resumed and completed

---

### TC-36 — J-06/J-07 regression: scoring/snapshot byte-identical (no DB regen)

**Type:** artifact
**Preconditions:** Backend source code and database exist; a seed-only baseline snapshot exists

**Steps:**
1. Dump the scanner_results table hash before any removal
2. Run a removal that affects only user-added bars (if any; the committed-seed-only host has zero user-added bars, so this is a no-op)
3. Dump the scanner_results table hash after removal
4. Assert the hashes are identical

**Expected outcome:** Scoring and snapshots are byte-identical; no recompute or drift

**Pass criteria:** Scanner_results hash before == hash after (for seed-only datasets, should be exact match)

---

## Summary

Total test cases: 36
- API tests: 21 (TC-17 through TC-33, TC-34 through TC-36)
- Browser tests: 15 (TC-01 through TC-16)
- Artifact checks: 1 (TC-31)

Key focus areas:
- J-36 (coverage definitions + per-symbol table): TC-01 through TC-23
- J-39 (remove-data with seed safety + cascade): TC-24 through TC-32
- J-35 (expand-universe browser capture): TC-13 through TC-15
- J-18 cross-check (one date selector): TC-16
- Regressions (J-17, J-34, J-06, J-07): TC-34 through TC-36
- Error handling & empty dataset: TC-33
