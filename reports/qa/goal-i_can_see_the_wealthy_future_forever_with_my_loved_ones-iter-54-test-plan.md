# Goal Iteration 54 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-54
**Date:** 2026-06-27
**Frontend Present:** yes

## Phase Goal

Ship a new Research — Market Phase & Severity Lab at `/research/phase-severity-lab` showing descriptive, survivorship-biased cross-sectional evidence of how realized forward returns and max-drawdowns differ across the five canonical market-phase labels (Expansion / Recovery / Pullback / Correction / Bear) and across severity-score deciles (D1–D10), at every configured horizon.

## Test Cases

### TC-01 — Market Phase & Severity Lab page loads with correct tables

**Type:** browser
**Preconditions:** 
- Backend is running with seeded data
- User navigates to `/research/phase-severity-lab`

**Steps:**
1. Open the Research hub at `/research`
2. Verify the **Market Phase & Severity Lab** tile is visible in the LABS list
3. Click the tile to navigate to `/research/phase-severity-lab`
4. Wait for the page to render

**Expected outcome:** 
- Page loads successfully
- Two tables are rendered: (a) by-phase-label table with 5 rows (Expansion, Recovery, Pullback, Correction, Bear) and (b) severity-score decile table with D1–D10 rows
- Both tables show paired forward-return + max-drawdown columns per configured horizon (1/5/10/20/60 days)
- Rank-IC row visible in decile table
- Per-bucket n (sample size) displayed in all rows
- Per-decile score range column visible (decile table only)
- Survivorship-bias and descriptive-evidence labels present

**Pass criteria:** 
- Page HTTP 200; tables render with no skeleton or "Backend unavailable" state
- `<table>` elements exist with correct row counts: 5 phase rows + 1 header, 11 decile rows (D1…D10 + rank-IC row) + 1 header
- Every cell with a forward return shows a value or NA (never blank or "–" for legitimate buckets with n>0 at configured horizons)
- `aria-label` attributes on all sortable column headers
- No native `input[type=date]` present anywhere on the page

---

### TC-02 — By-phase-label table renders correct canonical values

**Type:** api
**Preconditions:**
- Market phase causal timeline is populated with known phase labels for the test date range
- Forward returns and max-drawdowns are precomputed in the database for those dates

**Steps:**
1. Call `curl -s "http://localhost:8000/api/research/phase-severity-lab?view=pooled&as_of=<test-date>" -H "Accept: application/json"`
2. Parse the JSON response
3. Verify the `by_phase` array with five objects (one per canonical phase label: Expansion, Recovery, Pullback, Correction, Bear)
4. For each phase, check that `realized_return` and `max_drawdown` per horizon equal the reference aggregation (mean over all observations where `snapshot_date` matches the `market_phase` timeline value for that snapshot date)

**Expected outcome:** 
- HTTP 200
- Response shape: `{ by_phase: [...], by_severity_decile: [...] }`
- Each `by_phase[i]` has structure: `{ phase_label: string, horizons: [{ horizon_days: int, realized_return: number | null, max_drawdown: number | null, n: int }, ...] }`
- Values are read verbatim from stored `forward_returns` and `market_phase` timeline (no recomputation)
- Every value matches reference aggregation per (phase_label, horizon)

**Pass criteria:**
- HTTP status 200
- Response keys exist and are populated
- Deep equality: each (phase_label, horizon) tuple's mean return / mean MDD / n matches the reference calculation over the same observation set
- No phase label appears that is not in the canonical five or config

---

### TC-03 — Severity-score decile table groups by decile and computes rank-IC

**Type:** api
**Preconditions:**
- Severity scores (0–100) are populated in the `market_phase` timeline
- Observations are grouped and cached

**Steps:**
1. Call `curl -s "http://localhost:8000/api/research/phase-severity-lab?view=pooled&as_of=<test-date>" -H "Accept: application/json"`
2. Parse the `by_severity_decile` array (11 objects: D1…D10 + rank-IC row)
3. For each decile D1…D10, verify `score_range` (min–max severity value for that decile) is correct
4. For the rank-IC row, verify the Spearman rank correlation coefficient between severity score and forward return per horizon is computed and present

**Expected outcome:**
- `by_severity_decile[0-9]` objects each have: `{ decile: int (1–10), score_range: [number, number], horizons: [...] }`
- Each horizon in the decile has `realized_return`, `max_drawdown`, `n`, and `rank_ic` fields
- `by_severity_decile[10]` (rank-IC row) has `decile: null` and per-horizon rank-IC values

**Pass criteria:**
- Decile boundaries correctly divide the 0–100 severity score range into equal-weight tenths
- Rank-IC values are between –1.0 and +1.0 (Spearman coefficient)
- n and mean values match the decile's observation set
- No fabricated row exists; rank-IC row is the 11th and last element

---

### TC-04 — As-of parameter filters observation set without creating second date control

**Type:** browser
**Preconditions:**
- Page is loaded at latest as-of date (no `?asof` param in URL)
- Backend has historical data for a date ~30 days prior

**Steps:**
1. On the loaded page, locate the "As-of vs All-history" toggle or button
2. Toggle from "All-history" to a historical date (or navigate with `?asof=<YYYY-MM-DD>` in the URL)
3. Compare the rendered n values to a snapshot of n from the latest date
4. Verify no new date picker element appears (no native `<input type="date">` and no page-local date control)
5. Open Developer Tools and verify the fetch request includes `as_of=<YYYY-MM-DD>` (not `asof=`)

**Expected outcome:**
- n values DECREASE when filtering to historical dates (fewer observations in the smaller date range)
- Single global as-of state is the ONLY date control on the page (the Research hub's global as-of toggle)
- URL carries `?asof=<YYYY-MM-DD>` (if historical)
- No second date selector created

**Pass criteria:**
- n values decrease monotonically as as-of date moves back in history
- No `input[type="date"]` element on the page
- Fetch request parameter is exactly `as_of=` (verified in network tab)
- Page state does NOT change if the global as-of is toggled (state flows through the URL and fetch, not page-local state)

---

### TC-05 — Sort columns are byte-distinct and NA-last

**Type:** browser
**Preconditions:**
- Page is fully loaded with both tables rendered
- md5sum of the current DOM/frame is recorded

**Steps:**
1. Identify a sortable column header (e.g., forward-return at 1-day horizon)
2. Resolve the header by its `aria-label` attribute (not by visible text)
3. Click the header to toggle sort (ascending → descending or vice versa)
4. Wait for the table to re-render
5. Record a new md5sum of the DOM
6. Click the header again to reverse sort direction
7. Record a third md5sum

**Expected outcome:**
- After first sort toggle, md5 is DIFFERENT from the original (byte-distinct re-render)
- After second toggle (opposite direction), md5 is DIFFERENT from both previous states
- NA values always appear at the bottom of the sorted column, regardless of sort direction
- No API call is made on sort; only the rendered rows are reordered (client-side sort)

**Pass criteria:**
- md5sum(original) ≠ md5sum(after-first-sort)
- md5sum(after-first-sort) ≠ md5sum(after-second-sort)
- NA rows are always last (verified by visual inspection or DOM order check)

---

### TC-06 — N= chip drill-down opens Samples cohort with count coherence

**Type:** browser
**Preconditions:**
- Page is loaded with both tables visible
- Both browser windows (current + new tab) are available

**Steps:**
1. Identify an `N=` chip (sample size) in the by-phase-label table (e.g., Expansion phase, 1-day horizon)
2. Note the displayed n value (e.g., n=254)
3. Right-click or Ctrl+click the `N=` chip to open in a new tab
4. Switch to the new tab and wait for `/research/samples` to load
5. Verify the cohort filter is set to the exact phase label (e.g., "Expansion") and horizon (e.g., 1 day)
6. Check the "Total observations" figure at the top of the Samples page

**Expected outcome:**
- New tab opens `/research/samples?view=pooled&<cohort-params>&asof=<date>` (if historical, `asof` is carried)
- The exact `(phase label, horizon)` is selected in the Samples filter
- "Total observations" count equals the clicked n value

**Pass criteria:**
- New tab URL includes `view=pooled` (pinned, not toggled)
- Cohort params correctly identify the phase and horizon
- Total observations == displayed n (count-coherent, no drift)

---

### TC-07 — Decile table N= chip opens Samples with severity-decile cohort

**Type:** browser
**Preconditions:**
- Page is loaded with severity-decile table visible
- A decile row (e.g., D5) with a non-zero n exists

**Steps:**
1. Find an `N=` chip in the severity-decile table (e.g., D5, 5-day horizon, n=187)
2. Right-click to open in a new tab
3. Switch to the new tab and verify the Samples filter is set to the exact `(decile label, horizon)` pair
4. Check the "Total observations" count

**Expected outcome:**
- `/research/samples` opens with `view=pooled`, the correct decile label (e.g., "D5"), and the horizon
- "Total observations" == the n from the chip

**Pass criteria:**
- Cohort correctly resolves to the severity-decile observation set
- Count-coherent (total == chip n)

---

### TC-08 — Backend observation builder uses bounded streaming (no unbounded .all())

**Type:** artifact
**Preconditions:**
- Code inspection of the implementation

**Steps:**
1. Read `apps/backend/app/engine/research.py` to find `compute_phase_severity_lab` and the helper function(s) that fetch observations
2. Search for any `select(...).all()` calls over `ForwardReturn` or `ScannerResult` without a `limit()` or explicit iteration boundary
3. Verify `ScannerResult` queries are ordered by `(run_id, id)` (not bare `id`)
4. Verify the observation builder streams/yields rows (column-projected) rather than loading all into memory

**Expected outcome:**
- No unbounded `select(...).all()` over observation tables
- `ScannerResult` reads are ordered `(run_id, id)` and use an index (`ix_scanner_results_run_id`)
- Streaming/iterator pattern is used to avoid OOM on large result sets

**Pass criteria:**
- Grep for `\.all\(\)` returns no results for observation queries (or only bounded queries with explicit limit)
- `order_by(run_id, id)` or similar appears on ScannerResult queries
- No temp B-tree spill (implementation uses bounded memory)

---

### TC-09 — Cache schema token and market-phase stamp are folded into cache key

**Type:** artifact
**Preconditions:**
- Code inspection of cache implementation

**Steps:**
1. Read `apps/backend/app/engine/research.py` to find the cache key generation for the Phase & Severity Lab study
2. Verify the key includes:
   - A schema token (e.g., `_PHASE_SEVERITY_LAB_SCHEMA_TOKEN`)
   - The `_dataset_version` (standard study cache element)
   - The `market_phase.SCHEMA_VERSION` stamp (to invalidate on phase/severity refresh)
3. Verify the cache model is `event_study_cache` (not a new table)

**Expected outcome:**
- Cache key is a string or tuple combining: `_dataset_version`, study-specific schema token, and `market_phase.SCHEMA_VERSION`
- A change to the phase/severity timeline causes the key to change, invalidating old cache

**Pass criteria:**
- Key generation includes all three components
- No new `table=True` model created (reuses `event_study_cache`)
- Unit test exists to verify old-schema cache rows MISS and are repopulated

---

### TC-10 — Unit test: old-schema cache row misses and is repopulated

**Type:** artifact
**Preconditions:**
- Unit test exists in `apps/backend/tests/test_phase_severity_lab.py`

**Steps:**
1. Read `test_phase_severity_lab.py` to find the test that seeds an old-schema cache row
2. Verify the test:
   - Inserts a pre-existing `event_study_cache` row with an OLD schema token
   - Calls `compute_phase_severity_lab` with the same parameters
   - Asserts the old row is NOT used (MISS), and a NEW row is inserted with the new schema token
   - Verifies the new row's values are computed correctly and are byte-identical to a reference aggregation

**Expected outcome:**
- Test is labeled (e.g., `test_phase_severity_lab_schema_cache_miss_and_repopulate`)
- Old-schema row MISS is verified
- New row is HIT and byte-identical on subsequent calls

**Pass criteria:**
- Test runs and passes
- Old-schema logic is confirmed in code

---

### TC-11 — Unit test: market-phase refresh invalidates cache

**Type:** artifact
**Preconditions:**
- Unit test exists in `apps/backend/tests/test_phase_severity_lab.py`

**Steps:**
1. Read the test that verifies cache invalidation on `market_phase.SCHEMA_VERSION` change
2. Verify the test:
   - Computes and caches the Phase & Severity Lab
   - Bumps `market_phase.SCHEMA_VERSION` (simulating a phase/severity refresh)
   - Calls `compute_phase_severity_lab` again
   - Asserts the cache key has changed (due to the bumped version) and a new cache row is inserted
   - Verifies new values are computed (phase/severity may have changed)

**Expected outcome:**
- Test is labeled (e.g., `test_phase_severity_lab_invalidates_on_phase_stamp_change`)
- Version bump triggers cache MISS and re-compute

**Pass criteria:**
- Test passes and confirms cache-key evolution with phase-stamp change

---

### TC-12 — Unit test: byte-identity across views (Pooled and Episodes)

**Type:** artifact
**Preconditions:**
- Unit test exists in `apps/backend/tests/test_phase_severity_lab.py`
- Test data includes Episodes (consecutive signal-days for the same symbol)

**Steps:**
1. Read the byte-identity test for Pooled vs Episodes views
2. Verify:
   - Both views are computed for the same parameters
   - Per-bucket (phase or decile) n, mean realized_return, mean max_drawdown are compared between views
   - Assertion is deep equality (not just count, but exact values)

**Expected outcome:**
- Pooled and Episodes produce byte-identical aggregates (same observation set, grouped identically)
- n values are identical

**Pass criteria:**
- Test passes and confirms byte-identity across views

---

### TC-13 — Unit test: phase/severity provenance from market_phase timeline

**Type:** artifact
**Preconditions:**
- Unit test exists in `apps/backend/tests/test_phase_severity_lab.py`

**Steps:**
1. Read the provenance test that validates phase/severity labels
2. Verify the test:
   - For a sample of observations, reads the `market_phase._timeline_series` / `timeline_full` value for the snapshot date
   - Asserts each observation's tagged phase label and severity score match the timeline value (not a recomputation)
   - Tests both a known phase (e.g., Expansion on a specific date) and a warm-up-head date (should yield NA/unclassified)

**Expected outcome:**
- Phase and severity values are read verbatim from the timeline, not recomputed
- Warm-up-head dates yield an honest NA/unclassified state (no fabricated phase)

**Pass criteria:**
- Test passes and confirms join correctness

---

### TC-14 — No magic numbers: phase labels from config, decile count from config

**Type:** artifact
**Preconditions:**
- Code inspection of `apps/backend/app/engine/research.py` and config usage

**Steps:**
1. Search for hardcoded strings matching phase labels (Expansion, Recovery, Pullback, Correction, Bear)
2. Verify they are sourced from `config.market_phase.labels` or similar (not string literals)
3. Search for hardcoded decile count (10) in the Phase & Severity Lab logic
4. Verify it is sourced from config (e.g., `config.walk_forward.deciles` or similar)
5. Run `pytest apps/backend/tests/test_no_magic_numbers.py` and verify it passes (no new literals detected)

**Expected outcome:**
- No phase label or decile count literals in the computation code
- All sourced from config

**Pass criteria:**
- `test_no_magic_numbers` passes
- Grep for phase label strings in `research.py` returns only imports/config reads, not literals

---

### TC-15 — test_db.py expected-tables guard unchanged

**Type:** artifact
**Preconditions:**
- Unit test `apps/backend/tests/test_db.py` exists

**Steps:**
1. Read the expected-tables guard in `test_db.py`
2. Run `pytest apps/backend/tests/test_db.py::test_expected_tables` (or similar)
3. Verify it passes and that no new table is added

**Expected outcome:**
- Test passes
- No new `table=True` model created (Phase & Severity Lab reuses `event_study_cache`)

**Pass criteria:**
- Test passes; table count is unchanged from the baseline

---

### TC-16 — J-111 target journey: full browser flow

**Type:** browser
**Preconditions:**
- Backend is freshly restarted and warmed
- Frontend is running
- md5sum of the screenshot directory is recorded at start

**Steps:**
1. Navigate to `/research`
2. Verify the **Market Phase & Severity Lab** tile is visible and clickable
3. Click the tile
4. Wait for the page to render with both tables
5. Verify the by-phase-label table (5 rows) and severity-decile table (D1…D10 + rank-IC) are displayed
6. Verify columns include paired forward-return + max-drawdown per horizon, n, score range (decile only), and rank-IC (decile only)
7. Verify the survivorship-bias label is present
8. Click a sort header (resolved by `aria-label`)
9. Verify the table re-renders with rows in a different order and md5 is distinct
10. Toggle the As-of filter to a historical date
11. Verify n values decrease and the page re-fetches with the correct `as_of=` parameter
12. Click an `N=` chip in the by-phase-label table
13. Verify a new tab opens to `/research/samples` with the correct cohort and total observations == n

**Expected outcome:**
- Page loads, renders both tables with correct structure and values
- Sort is byte-distinct, NA-last
- As-of toggle filters (no second date control)
- Drill-down opens count-coherent Samples cohort
- No skeleton or "Backend unavailable" state at any step

**Pass criteria:**
- HTTP 200 on all fetches
- md5sum of evidence screenshots are distinct before/after sort
- No native date input
- No Episodes/Pooled toggle
- Samples "Total observations" == clicked n

---

### TC-17 — Required-still-passing J-110 (Regime Lab) renders real figures

**Type:** browser
**Preconditions:**
- Backend is running
- User navigates to `/research/regime-lab`

**Steps:**
1. Open the Research hub at `/research`
2. Click the **Regime Lab** tile
3. Verify the page loads with the by-regime-score table and regime-setup-pattern table
4. Verify at least one cell in the forward-return column has a numeric value (not NA or empty)
5. Spot-check one figure by calling the API directly:
   - `curl -s "http://localhost:8000/api/research/regime-lab?view=pooled&as_of=latest" | jq '.by_regime[0]'`
   - Verify the API returns numeric values for realized_return and max_drawdown

**Expected outcome:**
- Regime Lab page renders successfully
- Real figures are displayed (not all NA or stale)
- API returns numeric values

**Pass criteria:**
- HTTP 200 on both browser and API calls
- At least one numeric forward-return value is visible

---

### TC-18 — Required-still-passing J-06 (single-source): score appears identically across pages

**Type:** browser
**Preconditions:**
- Backend is running
- User has navigated to multiple pages (e.g., Stocks leaderboard and Sectors)

**Steps:**
1. Open `/stocks` (leaderboard) and note a sector's Leadership Score (e.g., Technology: 72)
2. Open `/sectors` and find the same sector row
3. Verify the Leadership Score is identical (72, not 71 or 73)
4. Open the sector detail page
5. Verify the same score appears

**Expected outcome:**
- Scores are identical across all pages (no recomputation or caching drift)

**Pass criteria:**
- Three or more instances of the same score across different pages are all identical

---

### TC-19 — Required-still-passing J-18 (exactly one date selector): no native date inputs

**Type:** browser
**Preconditions:**
- User is on any page with as-of filtering (e.g., `/research/phase-severity-lab`, `/stocks`, `/dashboard`)

**Steps:**
1. Open the page
2. Use Developer Tools to search for all `<input type="date">` elements
3. Verify zero matches
4. Verify the ONLY date control is the global as-of toggle in the Research hub (or sidebar)

**Expected outcome:**
- No native `<input type="date">` anywhere
- Single global as-of is the only date state mechanism

**Pass criteria:**
- Grep of the DOM for `type="date"` returns zero matches

---

### TC-20 — Required-still-passing J-07 (Risk-Off regime): zero Actionable stocks

**Type:** browser
**Preconditions:**
- The backend data includes a historical date where the market regime is Risk-Off
- User can navigate to that date

**Steps:**
1. Open the dashboard
2. Toggle As-of to a Risk-Off regime date (or navigate with `?asof=<risk-off-date>`)
3. Open the `/stocks` leaderboard
4. Filter by "Actionable" status (if a filter exists)
5. Verify zero stocks are displayed
6. Verify all stocks show "Watchlist-only" or similar non-Actionable status

**Expected outcome:**
- Zero stocks are marked Actionable when regime is Risk-Off
- All stocks are labeled as Watchlist-only or Pullback-watch

**Pass criteria:**
- Actionable count == 0 when Risk-Off regime is active

---

## Summary

Total test cases: 20
- API tests: 3 (TC-02, TC-03, TC-15 fetch validation)
- Browser tests: 11 (TC-01, TC-04, TC-05, TC-06, TC-07, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21)
- Artifact/code inspection tests: 6 (TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15)

**Key Gates:**
- Byte-identity across cache schemas and views (TC-10, TC-11, TC-12)
- Phase/severity provenance from `market_phase` timeline (TC-13)
- No magic numbers (TC-14)
- Bounded observation streaming (TC-08)
- Full live browser journey (TC-16)
- Required journeys remain green (TC-17, TC-18, TC-19, TC-20)
