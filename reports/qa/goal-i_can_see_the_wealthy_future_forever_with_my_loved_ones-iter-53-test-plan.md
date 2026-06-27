# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53
**Date:** 2026-06-27
**Frontend Present:** yes

## Phase Goal

Ship Research → Regime Lab (`/research/regime-lab`), a new read-only cross-sectional study showing how realized forward returns and paired max-drawdowns relate to market regime (by regime label and regime-score decile) at every configured horizon, with rank-IC and count-coherent drill-downs.

## Test Cases

### TC-01 — Regime Lab hub tile visible and navigable

**Type:** browser
**Preconditions:** Frontend is running; as-of is set to latest; user is on `/research` hub page

**Steps:**
1. Navigate to `/research`
2. Inspect the LABS array for a "Regime Lab" tile
3. Verify tile is clickable and carries the correct link target

**Expected outcome:** The Regime Lab tile is visible on the `/research` hub, positioned alongside other lab tiles (Factor Lab, Regime × Setup × Pattern, Severity-velocity × Regime)
**Pass criteria:** Tile is present and `href="/research/regime-lab"` is set; clicking navigates to `/research/regime-lab`

---

### TC-02 — Regime Lab page renders without errors (J-110 main flow)

**Type:** browser
**Preconditions:** Frontend is running; as-of is latest; backend is responding with HTTP 200 to `/api/research/regime-lab`

**Steps:**
1. Navigate to `/research/regime-lab`
2. Wait for page to fully load
3. Inspect the DOM for the by-label table and the regime-score decile table
4. Verify no "Backend unavailable" or error skeleton is displayed

**Expected outcome:** The page renders with two stacked tables: the 6-row by-label summary table and the D1–D10 regime-score decile table
**Pass criteria:** Both tables are present; DOM contains `<table>` elements with regime labels and decile labels; no error state card

---

### TC-03 — By-label table structure and content (J-110 required columns)

**Type:** browser
**Preconditions:** `/research/regime-lab` page is rendered; backend API returned data

**Steps:**
1. Locate the "by-label summary" table
2. Count table rows (excluding header)
3. Verify header includes columns for: mean forward-return per horizon (1d, 5d, 10d, 20d, 60d), paired mean max-drawdown per horizon, n, rank-IC
4. Inspect a sample cell for numeric content or NA label

**Expected outcome:** Table has exactly 6 data rows (six canonical regime labels); columns follow the paired (return, MDD) layout with n and rank-IC
**Pass criteria:** Row count == 6; column headers resolve via `aria-label` (not bare text); cells contain numeric values or "NA"; no all-zero or fabricated values

---

### TC-04 — Regime-score decile table structure and content (J-110 decile view)

**Type:** browser
**Preconditions:** `/research/regime-lab` page is rendered; backend API returned data

**Steps:**
1. Locate the "regime-score decile" table
2. Count table rows (excluding header)
3. Verify columns include: regime-score range (min–max), mean forward-return per horizon, paired mean max-drawdown, n, rank-IC per horizon
4. Inspect the decile labels (D1–D10)

**Expected outcome:** Table has exactly 10 data rows (D1…D10); columns include score range and paired return/MDD per horizon with rank-IC
**Pass criteria:** Row count == 10; decile labels D1–D10 are present; score-range cells show "min–max" format; rank-IC values are numeric or NA

---

### TC-05 — Survivorship-bias label present on page

**Type:** browser
**Preconditions:** `/research/regime-lab` page is rendered

**Steps:**
1. Search the page text for survivorship bias or descriptive-evidence language
2. Verify the label is visible and legible

**Expected outcome:** Page displays an explicit survivorship-bias disclaimer or descriptive-evidence label stating the evidence is based on current-membership universe
**Pass criteria:** Label text includes "survivorship" or "descriptive" or "current membership"; is not hidden behind a collapsed details element

---

### TC-06 — No native date input on page (J-18 critical compliance)

**Type:** artifact
**Preconditions:** Page is rendered

**Steps:**
1. Query the DOM for all `input[type="date"]` elements
2. Record count

**Expected outcome:** No native HTML date input elements are present
**Pass criteria:** `document.querySelectorAll('input[type="date"]').length === 0`

---

### TC-07 — Sort toggle produces byte-distinct frame (J-110 sort interaction)

**Type:** browser
**Preconditions:** `/research/regime-lab` page is rendered; md5 of the initial rendered frame is recorded as `before_md5`

**Steps:**
1. Take a screenshot and compute md5 of initial frame
2. Locate a sortable column header by `aria-label` (e.g., `aria-label="sort by 1-day return"`)
3. Click the header to toggle sort direction
4. Wait for table to re-render
5. Take a screenshot and compute md5 of the new frame

**Expected outcome:** The rendered table rows are reordered; the new screenshot md5 differs from the initial md5
**Pass criteria:** `md5(after_frame) !== md5(before_frame)`; row order visibly changes; no page reload occurs

---

### TC-08 — Sort NA-last behavior both directions (J-110 sort NA-last)

**Type:** browser
**Preconditions:** `/research/regime-lab` page is rendered; a column with NA values is visible

**Steps:**
1. Identify a column with both numeric and NA values
2. Click the column header to sort ascending
3. Inspect the rendered rows; note the order of NA cells
4. Click the header again to sort descending
5. Inspect the rows; note the order of NA cells

**Expected outcome:** In both ascending and descending order, NA values appear at the bottom of the list
**Pass criteria:** NA cells always render after all numeric values in both sort directions; observable visually in the table

---

### TC-09 — As-of toggle filters observation set (J-110 As-of FILTER)

**Type:** browser
**Preconditions:** `/research/regime-lab` is rendered with as-of at latest; a historical date with fewer observations exists in the backend

**Steps:**
1. Record the current rendered n values in each cell
2. Locate and click the "As-of vs All-history" toggle to filter to a historical date
3. Wait for table to re-fetch and re-render
4. Record the new rendered n values

**Expected outcome:** The n values in the filtered view are smaller than or equal to the all-history view (fewer observations matched)
**Pass criteria:** At least one cell's n value decreases after toggling As-of; rows remain the same (no new regime labels/deciles added); URL query param changes to `?asof=<date>`

---

### TC-10 — As-of param sent as `as_of=` not `asof=` (J-110 param spelling)

**Type:** api
**Preconditions:** Browser dev tools are open; Network tab is active

**Steps:**
1. Navigate to `/research/regime-lab`
2. Inspect the Network tab for a request to `GET /api/research/regime-lab`
3. Check the query string in the request URL

**Expected outcome:** The query parameter in the request is spelled `as_of=<date>` (not `asof=`)
**Pass criteria:** Network request shows `GET /api/research/regime-lab?view=...&as_of=...` with `as_of` (underscore, not bare word)

---

### TC-11 — N= chip drill-down opens count-coherent Samples cohort (J-110 drill, J-65 coherence)

**Type:** browser
**Preconditions:** `/research/regime-lab` is rendered; user hovers over or clicks an n cell

**Steps:**
1. Locate a cell with an `N=` chip (e.g., `N=42` for a given regime label + horizon)
2. Right-click or middle-click the chip to open in a new tab (or use `Ctrl+click` / `Cmd+click`)
3. Switch to the new tab
4. Verify the page is `/research/samples`
5. Read the "Total observations" value or count the rendered rows
6. Compare to the original n value from the chip

**Expected outcome:** The Samples page opens in a new tab with the exact cohort filtered (regime label or decile + horizon); the total observation count equals the clicked n
**Pass criteria:** `location.href` contains `/research/samples?...`; `total === n_chip` (count-coherence); cohort parameters in URL identify the exact bucket

---

### TC-12 — N= chip href carries as_of param (J-50 date serialization)

**Type:** artifact
**Preconditions:** `/research/regime-lab?asof=<historical-date>` is loaded; user is viewing a historical as-of state

**Steps:**
1. Inspect an `N=` chip element's `href` attribute
2. Parse the URL for the `asof` or `as_of` query param
3. Verify it matches the current page's as-of date

**Expected outcome:** The chip's href includes the same as-of date as the current page (e.g., if page is `?asof=2025-06-15`, chip href is `/research/samples?...&asof=2025-06-15`)
**Pass criteria:** `href.includes('asof=' + current_date)` or `href.includes('as_of=' + current_date)` is true

---

### TC-13 — API endpoint GET /api/research/regime-lab returns correct shape

**Type:** api
**Preconditions:** Backend is running; at least one snapshot exists

**Steps:**
1. Run the following curl command (assuming backend at `http://localhost:8000`):
   ```bash
   curl -s 'http://localhost:8000/api/research/regime-lab?view=Pooled' -H 'Accept: application/json'
   ```
2. Capture the response status and JSON body
3. Inspect the response structure for the expected fields

**Expected outcome:** HTTP 200; response is a JSON object with a `by_label` array and a `by_decile` array, each containing buckets with: mean_return, mean_max_drawdown, n, (decile: score_min, score_max, rank_ic)
**Pass criteria:** Status 200; response JSON parses; both `by_label` and `by_decile` arrays exist; each array element has required fields; all numeric values are valid JSON numbers or null

---

### TC-14 — API endpoint respects view parameter (Episodes vs Pooled)

**Type:** api
**Preconditions:** Backend is running with both Episodes and Pooled views supported

**Steps:**
1. Fetch `/api/research/regime-lab?view=Episodes`
2. Record the response and note the n values
3. Fetch `/api/research/regime-lab?view=Pooled`
4. Record the response and compare n values

**Expected outcome:** Both requests return HTTP 200; responses have different n values or differ in structure according to the view contract (Episodes = individual event-study snapshots; Pooled = aggregated cross-snapshot)
**Pass criteria:** Both requests succeed; response bodies are distinct when view differs; no 4xx errors for valid view values

---

### TC-15 — API endpoint handles as_of filter correctly

**Type:** api
**Preconditions:** Backend has data spanning multiple dates

**Steps:**
1. Fetch `/api/research/regime-lab?as_of=<latest-date>`
2. Record the total n across all buckets as `n_latest`
3. Fetch `/api/research/regime-lab?as_of=<earlier-date>` (e.g., 30 days prior)
4. Record the total n as `n_earlier`

**Expected outcome:** HTTP 200 for both; n_earlier ≤ n_latest (earlier date has fewer or equal observations)
**Pass criteria:** Both requests succeed; n_earlier <= n_latest; response structure is consistent

---

### TC-16 — Empty/unknown regime label returns honest empty state

**Type:** api
**Preconditions:** Backend is running; an invalid regime label is attempted

**Steps:**
1. Attempt to fetch `/research/samples?regime_label=UnknownRegime&horizon=1d`
2. Record the response status

**Expected outcome:** Either HTTP 400 (malformed param) or HTTP 200 with an empty observations list (honest empty state)
**Pass criteria:** Status is 400 or 200; if 200, response contains `total === 0` or an empty array; no fabricated row is served

---

### TC-17 — Out-of-range decile request returns honest empty state

**Type:** api
**Preconditions:** Backend is running; deciles are D1–D10

**Steps:**
1. Attempt to fetch `/research/samples?regime_decile=D11&horizon=1d`
2. Record the response status

**Expected outcome:** Either HTTP 400 (invalid decile) or HTTP 200 with empty observations (honest empty state)
**Pass criteria:** Status is 400 or 200; if 200, no fabricated row appears; message or field indicates the decile is out of range or not applicable

---

### TC-18 — Thin/zero-n buckets show NA, not fabricated number (error case)

**Type:** browser
**Preconditions:** `/research/regime-lab` page is loaded; backend returns data including thin buckets or at/near-latest horizons

**Steps:**
1. Inspect a cell in the table that should have n < min_sample (e.g., a 60-day horizon on the latest date, or a rare regime label)
2. Read the cell content

**Expected outcome:** Cell displays "NA" or "—" plus the actual n value (e.g., "NA (n=2)"), never a fabricated return figure
**Pass criteria:** Cell text matches the pattern `NA.*n=\d+` or similar; no numeric return value appears for cells with insufficient observations

---

### TC-19 — Bounded read: no unbounded select().all() over ForwardReturn (architecture compliance)

**Type:** artifact
**Preconditions:** Backend code has been implemented

**Steps:**
1. Search `apps/backend/app/engine/research.py` for calls to `compute_regime_lab`
2. Inspect the implementation for any unbounded `select(...).all()` on the `ForwardReturn` table
3. Verify that ScannerResult reads are ordered by `(run_id, id)`

**Expected outcome:** The observation pool is built using the J-105 streamed/column-projected path; no single `select(...).all()` call on `ForwardReturn` or `ScannerResult` without explicit bounds
**Pass criteria:** Code inspection shows streaming reads with order-by `(run_id, id)`; test suite passes the bounded-read assertion in `test_regime_lab.py` or sibling

---

### TC-20 — Cache schema-token MISS on old-schema row, then repopulate (iter-38/39/44 compliance)

**Type:** api
**Preconditions:** A seeded old-schema `event_study_cache` row exists in the DB (pre-computed with an old `_dataset_version` value); the new `_REGIME_LAB_SCHEMA_TOKEN` is in the code

**Steps:**
1. Run the backend
2. Make a request to `/api/research/regime-lab` that would hit the seeded cache row
3. Observe that the row is a MISS (a fresh compute is triggered, not a cache hit)
4. After compute completes, verify the cache row is updated with the new schema token
5. Make the same request again; verify it is a HIT (byte-identical figures served from cache)

**Expected outcome:** The old-schema cache row is evicted (MISS); a new row with the folded schema token is inserted; subsequent requests hit the cache
**Pass criteria:** Test case `test_regime_lab_cache_schema_token_miss_then_hit` in `test_regime_lab.py` passes; cache statistics show a MISS followed by a HIT

---

### TC-21 — Compute regime-lab byte-identity across views (Episodes vs Pooled, All-history vs As-of)

**Type:** artifact
**Preconditions:** Backend test suite is set up; `test_regime_lab.py` exists

**Steps:**
1. Run `python -m pytest apps/backend/tests/test_regime_lab.py::test_compute_regime_lab_byte_identity -v`
2. Inspect the test output for pass/fail

**Expected outcome:** Test passes, verifying that each per-(bucket, horizon) mean return / mean max-drawdown / n equals the reference aggregation over the same observation set across both Episodes/Pooled views and All-history/As-of filters
**Pass criteria:** Test returns exit code 0; test log shows "PASSED"; deep-equality assertion passes

---

### TC-22 — Samples cohort kind resolves all displayable buckets without 4xx (count-coherence)

**Type:** artifact
**Preconditions:** Backend is running; test suite includes `test_samples.py`

**Steps:**
1. Run `python -m pytest apps/backend/tests/test_samples.py::test_regime_lab_cohort_no_4xx -v` (or similar)
2. Inspect the test output

**Expected outcome:** Test passes, verifying that the `regime-lab` cohort kind resolves all buckets the study emits (all regime labels, all deciles, all horizons) without returning 4xx errors; the samples total equals the published bucket n
**Pass criteria:** Test returns exit code 0; test log shows all buckets resolved; count-coherence assertion passes

---

### TC-23 — test_db.py expected-tables guard UNCHANGED (no new table added)

**Type:** artifact
**Preconditions:** Backend code is implemented; `test_db.py` exists

**Steps:**
1. Run `python -m pytest apps/backend/tests/test_db.py -v`
2. Inspect the output for pass/fail on the expected-tables guard

**Expected outcome:** Test passes; no new `table=True` model was added (only the existing `event_study_cache` table is reused)
**Pass criteria:** Test returns exit code 0; test name includes "expected_tables" and shows PASSED; no migration or schema change is required

---

### TC-24 — test_no_magic_numbers green (no inline numeric literals in CALC code)

**Type:** artifact
**Preconditions:** Backend code is implemented; `test_no_magic_numbers.py` exists

**Steps:**
1. Run `python -m pytest apps/backend/tests/test_no_magic_numbers.py -v`
2. Inspect the output for pass/fail on the regime_lab.py module

**Expected outcome:** Test passes; no hardcoded numeric literals (thresholds, horizon counts, decile counts) in `apps/backend/app/engine/research.py` compute_regime_lab function; all values are sourced from `config`
**Pass criteria:** Test returns exit code 0; test shows PASSED; error message does not flag any integer or float literal in `research.py` CALC code

---

### TC-25 — Required-still-passing J-06 (single-source smoke test)

**Type:** browser
**Preconditions:** Frontend is running; user is on the dashboard or detail pages where scores are displayed

**Steps:**
1. Navigate to `/stocks` or a stock detail page
2. Inspect a score value (Leadership, Entry Quality, Risk)
3. Navigate to a different page that displays the same stock
4. Inspect the same score value

**Expected outcome:** The score value is identical across pages (no recompute in the read path)
**Pass criteria:** Score value matches exactly (same digits, same styling, same bucket letter); no value differs by view or page

---

### TC-26 — Required-still-passing J-18 (zero native date inputs on all relevant pages)

**Type:** artifact
**Preconditions:** All pages are rendered

**Steps:**
1. Query DOM for `input[type="date"]` across the entire app
2. Record count

**Expected outcome:** No native date input elements exist; only the global as-of toggle and URL serialization are used
**Pass criteria:** Count === 0; all date controls are custom UI elements or URL params

---

### TC-27 — Required-still-passing J-07 (Risk-Off gates Actionable status)

**Type:** browser
**Preconditions:** Frontend is running; a snapshot with Risk-Off regime is available (or can be mocked in dev)

**Steps:**
1. Navigate to `/stocks` with a Risk-Off as-of date (e.g., from config if seeded)
2. Count the number of stocks marked "Actionable"

**Expected outcome:** In Risk-Off regime, zero stocks are marked "Actionable"; all stocks show "Watchlist" or similar
**Pass criteria:** Actionable count === 0 when regime === Risk-Off; this critical anti-goal rule is not violated

---

## Summary

Total test cases: 27
- API tests: 6 (TC-13, TC-14, TC-15, TC-16, TC-17, TC-10)
- Browser tests: 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-08, TC-09, TC-11, TC-12, TC-25, TC-26, TC-27)
- Artifact/unit tests: 8 (TC-06, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-18)
