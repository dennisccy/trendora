# Iteration 48 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48
**Date:** 2026-06-22
**Frontend Present:** yes

## Phase Goal

Stream the final two unstreamed `select(ScannerResult)…all()` reads in Factor Lab and Factor Combination to eliminate MemoryError on the full 3.3 GB live dataset, restoring J-25 and closing the iter-46 regression with byte-identical figures preserved.

## Test Cases

### TC-01 — Factor Lab loads with real figures on live dataset

**Type:** browser
**Preconditions:** 
- Backend server running at `localhost:8835` (health "ready", warm-up complete)
- Frontend running at `localhost:3000`
- Live 3.3 GB database available
- At least one past snapshot with ForwardReturn rows exists

**Steps:**
1. Navigate to `http://localhost:3000/research/factor-lab`
2. Wait for the page to load fully (no skeleton/loading spinner)
3. Select a **column factor** from the factor dropdown (e.g., RS 3m)
4. Select a **component factor** that reads from `record_json` (e.g., one not in typed columns)
5. Select a horizon from the available options
6. Observe the decile table (D1 through D10) with mean return, risk-adjusted return, and sample count (n)
7. Observe the rank-IC value rendering as a numeric figure
8. Check browser console for any errors

**Expected outcome:** The Factor Lab page displays a complete decile table with real numeric values and a rank-IC figure; no error banners or skeletons; page responds within ~50–60s for cold compute over ~598K rows.
**Pass criteria:** 
- HTTP 200 response code
- Decile table renders with all 10 rows (D1…D10) showing numeric mean return, risk-adjusted return, and n values
- Rank-IC displays a numeric value (not "Loading…" or error text)
- No "Backend unavailable" banner
- Browser console shows no JavaScript errors
- Backend log shows **no `MemoryError` at `research.py:216`**

---

### TC-02 — Factor Lab component factor (record_json) computation is byte-identical

**Type:** api
**Preconditions:**
- Backend server running with `/api/research/factor-lab` endpoint accessible
- Live database with at least 100 stored ScannerResult rows with filled `record_json` field
- At least one stored component factor defined in config

**Steps:**
1. Fetch `/api/research/factor-lab?factor_key=<component-factor>&horizon=5d&as_of=<date>&scope=all`
   (where `<component-factor>` reads from `record_json`, e.g., a multi-part component)
2. Capture the full `compute_factor_lab` JSON payload (deciles array, rank_ic value, by_regime object, n_total)
3. Store payload as reference (e.g., `original_deciles.json`)
4. On the same backend, fetch the same endpoint again with identical parameters
5. Compare the second payload to the reference

**Expected outcome:** The two fetches return byte-identical decile arrays, rank_ic values, by_regime sub-objects, and n_total counts across all regimes.
**Pass criteria:**
- `HTTP 200` on both fetches
- `deciles` array (all 10 elements) matches exactly: same mean_return, risk_adjusted_return, n for each decile
- `rank_ic` numeric value matches exactly
- `by_regime` object keys and values match exactly (same cohort counts per regime)
- `n_total` matches exactly

---

### TC-03 — Factor Combination cold-miss (cache MISS) renders real figures

**Type:** browser
**Preconditions:**
- Backend server running at `localhost:8835` (warmed, idle)
- Frontend running at `localhost:3000`
- Live database available
- Cache backend (Redis or in-memory) is cleared or restarted to ensure MISS
- At least two factors available in config for combination

**Steps:**
1. Ensure the factor-combination cache is cleared (or service is freshly restarted)
2. Navigate to `http://localhost:3000/research/factor-combination`
3. Wait for the page to load (expected slower than Factor Lab because of full ORM read)
4. Select two **factors** from the available list (mix of column and component factors)
5. Confirm the multi-factor combination is applied
6. Observe the Combined cohort table with composite return and overlap counts
7. Wait for ~60s for the cold computation to complete

**Expected outcome:** The Factor Combination page renders a Combined cohort table with real numeric values on a cold cache MISS; no skeleton or "Backend unavailable" error; page completes even though the ScannerResult read is unstreamed in the cold path.
**Pass criteria:**
- HTTP 200 response
- Combined cohort row displays numeric mean return and sample count (n)
- No error banner
- No skeleton/loading spinner persists past ~60s
- Backend log shows no `MemoryError` at `research.py:421`

---

### TC-04 — All five heavy labs serve HTTP 200 (J-104 acceptance)

**Type:** api
**Preconditions:**
- Backend running at `localhost:8835`
- Live database available
- At least one snapshot with complete data exists

**Steps:**
1. Fetch `/api/research/event-study?as_of=<date>&scope=all` (allow ~5s)
2. Fetch `/api/research/factor-lab?factor_key=<key>&horizon=5d&as_of=<date>&scope=all` (allow ~60s)
3. Fetch `/api/research/factor-combination?factors=<f1>,<f2>&as_of=<date>&scope=all` (allow ~50s)
4. Fetch `/api/research/regime-setup-pattern?as_of=<date>&scope=all` (allow ~10s)
5. Fetch `/api/research/downtrend-opportunity?as_of=<date>&scope=all` (allow ~5s)
6. Do not fetch concurrently; space each by at least ~10s to avoid contention

**Expected outcome:** All five endpoints return HTTP 200 with complete payloads (no truncation, no 500 errors, no timeouts).
**Pass criteria:**
- Event-study returns `HTTP 200` with `event_study_cells` array
- Factor Lab returns `HTTP 200` with `deciles` array and `rank_ic` value
- Factor Combination returns `HTTP 200` with composite and strict_overlap cohorts
- Regime×Setup×Pattern returns `HTTP 200` with `by_regime_setup_pattern` table
- Downtrend Opportunity returns `HTTP 200` with downtrend observations
- No endpoint takes longer than its budgeted time (~120s total for all five)

---

### TC-05 — Streamed reads honor the `as_of` cutoff parameter

**Type:** api
**Preconditions:**
- Backend running
- Live database with snapshots at multiple dates (at least two dates 5+ days apart)
- At least two ScannerRun rows with different `asof_date` values

**Steps:**
1. Fetch `/api/research/factor-lab?factor_key=<key>&horizon=5d&as_of=<earlier-date>&scope=all`
2. Capture the `n_total` (total observation count)
3. Fetch `/api/research/factor-lab?factor_key=<key>&horizon=5d&as_of=<later-date>&scope=all`
4. Capture the second `n_total`
5. Verify both queries use the exact URL parameter `?as_of=` (underscore spelling, not `asOf`)

**Expected outcome:** The two fetches return different observation counts because the earlier date's query filters to `ScannerRun.asof_date <= <earlier-date>`, while the later date query includes more runs. Both queries respect the `as_of` parameter correctly.
**Pass criteria:**
- First fetch with earlier date returns `HTTP 200` and `n_total` = N1
- Second fetch with later date returns `HTTP 200` and `n_total` = N2 (where N2 ≥ N1)
- The `?as_of=` parameter spelling is preserved in the URL (not rewritten to `asOf`)
- Observation filtering by date is consistent across the two fetches

---

### TC-06 — Unknown factor key returns 422 (unchanged error behavior)

**Type:** api
**Preconditions:**
- Backend running
- Live database available

**Steps:**
1. Fetch `/api/research/factor-lab?factor_key=nonexistent_factor&horizon=5d&as_of=<date>&scope=all`
2. Inspect the response status and error message

**Expected outcome:** The endpoint returns HTTP 422 (Unprocessable Entity) with a validation error message mentioning the unknown factor key.
**Pass criteria:**
- Response status code is `HTTP 422`
- Error message references the invalid `factor_key` parameter
- No 500 error (MemoryError or server fault)

---

### TC-07 — Zero-N cohort returns honest NA (no fabricated data)

**Type:** api
**Preconditions:**
- Backend running
- Live database with at least one configuration where a factor×horizon combination produces zero observations

**Steps:**
1. Fetch `/api/research/factor-lab?factor_key=<key>&horizon=60d&as_of=<recent-date>&scope=all` 
   (choose a recent date and a long horizon such that few/no forward-return rows exist yet)
2. Inspect the response payload for any cohorts with zero observations

**Expected outcome:** Cohorts with zero observations display an honest "NA" or explicit null value in fields like `mean_return` and `rank_ic`, never a fabricated or extrapolated figure.
**Pass criteria:**
- Zero-observation cohort rows display `null` or `"NA"` for return/IC fields (not a synthetic 0.0 or a placeholder)
- The `n` field for that cohort is exactly `0`
- No error is raised; the endpoint returns `HTTP 200`

---

### TC-08 — Byte-identity test: column factor (typed attribute) observation list

**Type:** artifact
**Preconditions:**
- Backend test suite can access the database
- `test_research_streaming.py` (or equivalent) is in place

**Steps:**
1. Run the unit test suite targeting `test_research_streaming.py` test methods for column factors (typed attributes)
2. The test should:
   - Compute `_factor_observations` using the **streamed** `yield_per(batch)` path (new code)
   - Compute the same observations using the prior `.all()` reference path (on a subset or via a test fixture)
   - Deep-compare the two observation lists (each dict in the list: same keys, same values)
   - Deep-compare the resulting `compute_factor_lab` payloads (deciles, rank_ic, by_regime, n_total)
   - Repeat across at least two different `as_of` dates (including all-history scope)
   - Repeat with at least two different `read_batch_size` values (e.g., 1 and 10000) to verify chunk-independence

**Expected outcome:** The streamed path and the reference path produce byte-identical observation lists and identical final payloads regardless of batch size or as-of date.
**Pass criteria:**
- Test `PASSED` (not FAILED)
- Assertion message confirms: "column-factor observations match (streamed vs reference, all-history, as-of dates)"
- No batch-size sensitivity: `read_batch_size=1` and `read_batch_size=10000` produce the same observations

---

### TC-09 — Byte-identity test: component factor (record_json) observation list

**Type:** artifact
**Preconditions:**
- Backend test suite available
- `test_research_streaming.py` includes a test case for component factors that read `record_json`

**Steps:**
1. Run the unit test targeting component-factor byte-identity in `test_research_streaming.py`
2. The test should:
   - Compute `_factor_observations` with the streamed path for a **component factor** (one that reads from `record_json`)
   - Compare to the reference `.all()` path observation list
   - Deep-compare deciles, rank_ic, by_regime, n_total of the `compute_factor_lab` payload
   - Verify that `record_json` field is preserved on each streamed row (not dropped by column projection)
   - Repeat across multiple as-of dates and batch sizes

**Expected outcome:** Component factors that extract values from `record_json` produce byte-identical observations and payloads via the streamed path.
**Pass criteria:**
- Test `PASSED`
- `record_json` field is present in streamed rows and used correctly by `_extract_factor_value`
- All observation dicts match between streamed and reference paths
- No batch-size dependency

---

### TC-10 — Byte-identity test: factor-combination composite/strict-overlap cohorts

**Type:** artifact
**Preconditions:**
- Backend test suite available
- `test_research_streaming.py` includes a factor-combination byte-identity test case

**Steps:**
1. Run the unit test for factor-combination streamed byte-identity
2. The test should:
   - Compute `_combination_observations` using the streamed `yield_per(batch)` path
   - Compare to the reference `.all()` path observation list
   - Deep-compare `compute_factor_combination` payloads (composite and strict_overlap cohort values)
   - Verify byte-identity across as-of dates and batch sizes

**Expected outcome:** The Factor Combination streamed path produces byte-identical composite and strict-overlap cohort figures.
**Pass criteria:**
- Test `PASSED`
- `composite` cohort rows match (mean_return, n, sample count per regime)
- `strict_overlap` cohort rows match exactly
- No regressions in existing `test_research.py` or `test_samples.py`

---

### TC-11 — Required-still-passing journeys: J-29 (event-study) renders real figures

**Type:** browser
**Preconditions:**
- Backend running (freshly warmed, quiet)
- Frontend running
- Live database available

**Steps:**
1. Navigate to `/research/setup-pattern` (Event-Study view)
2. Select a setup type or pattern
3. Select a horizon (e.g., 5-day forward return)
4. Observe the event-study cells rendering real numeric values
5. Check that the "episodes" toggle (first-trigger vs pooled) works and swaps figures

**Expected outcome:** Event-study page renders with real numeric return values, episode counts, and sample sizes; figures remain byte-identical to pre-iter-46 values.
**Pass criteria:**
- HTTP 200 response
- Event-study cells display numeric mean_return, risk_adjusted_return, and n values
- First-trigger and pooled modes both show real figures (not NA/skeleton)
- Figures match the pre-iter-46 aggregation (byte-identical)

---

### TC-12 — Required-still-passing journeys: J-26 (factor-combination) renders on cache HIT

**Type:** browser
**Preconditions:**
- Backend running
- Frontend running
- EventStudyCache populated (backend has started and J-104 setup-pattern is cached)
- Live database available

**Steps:**
1. Navigate to `/research/factor-combination` 
2. Select two factors (e.g., RS 3m and Volatility)
3. Observe the page renders quickly (cache HIT, ~2–5s)
4. Read the Combined cohort table values

**Expected outcome:** Factor-combination page loads from cache and displays byte-identical figures.
**Pass criteria:**
- HTTP 200 response
- Page loads within ~5s (cache HIT, not a cold compute)
- Combined cohort displays real numeric mean_return and n values
- Figures match pre-iter-46 byte-identical baseline

---

### TC-13 — Critical J-18: no native date input on research surfaces; single global as-of

**Type:** browser
**Preconditions:**
- Frontend running
- At least one research page loaded (`/research/factor-lab`, `/research/factor-combination`, etc.)

**Steps:**
1. Navigate to `/research/factor-lab`
2. Open browser DevTools (F12)
3. Search the DOM for HTML `<input type="date">` elements on the page
4. Check URL for `?asof=` parameter encoding

**Expected outcome:** No native date picker input elements; single global as-of date state serialized into the URL as `?asof=yyyy-MM-dd` (when historical).
**Pass criteria:**
- Zero `<input type="date">` elements found in the page DOM
- Historical navigation uses `?asof=<date>` URL parameter (underscore spelling)
- Single date control governs all research-page as-of scoping

---

### TC-14 — Critical J-07: Risk-Off regime → zero Actionable stocks on snapshot-served path

**Type:** browser
**Preconditions:**
- Backend running
- Frontend running
- Live database with at least one snapshot dated in a known Risk-Off regime period

**Steps:**
1. Navigate to `/stocks` for a historical as-of date known to be in a Risk-Off regime
2. Observe the Actionable column/filter
3. Verify the stock count in Actionable category is exactly zero
4. Verify other categories (Breakout-watch, Pullback-watch) may have entries

**Expected outcome:** On a Risk-Off regime date, zero stocks are marked Actionable; the regime gate is enforced identically across snapshots.
**Pass criteria:**
- Actionable stock count = 0 when viewing a Risk-Off regime as-of date
- Other setup categories (Breakout-watch, Pullback-watch) are unaffected
- The same Risk-Off regime snapshot read from `/stocks` shows identical behavior on `/research` surfaces

---

### TC-15 — Critical J-06: single-source reconciliation (diagnostic vs served)

**Type:** api
**Preconditions:**
- Backend running
- Live database available
- Diagnostic endpoint `/api/data/diagnostic` accessible

**Steps:**
1. Fetch `/api/data/diagnostic?as_of=<date>` (diagnostic/computed view)
2. Capture the Leadership, Entry Quality, Risk, and regime scores for one stock and the regime itself
3. Fetch `/api/stocks?as_of=<date>` (served/persisted view)
4. Find the same stock in the response and compare its scores
5. Fetch `/api/stocks/{symbol}?as_of=<date>` (detail served view) and compare again

**Expected outcome:** The same canonical score (e.g., Leadership Score for NVDA on a given date) reads identically across the diagnostic, leaderboard, and detail endpoints (no recompute, single source of truth).
**Pass criteria:**
- Leadership score from `/api/data/diagnostic` = `/api/stocks` leaderboard value = `/api/stocks/{symbol}` detail value
- Entry Quality, Risk, and regime scores match across all three endpoints
- All endpoints return HTTP 200 with consistent data

---

## Summary

Total test cases: 15
- **API tests**: 5 (TC-02, TC-04, TC-05, TC-06, TC-07, TC-15)
- **Browser tests**: 7 (TC-01, TC-03, TC-11, TC-12, TC-13, TC-14)
- **Artifact tests**: 3 (TC-08, TC-09, TC-10)

**Key focus**: The iteration fixes the MemoryError in Factor Lab and Factor Combination by streaming the final two `select(ScannerResult)…all()` reads. Test cases TC-01 through TC-10 directly validate the streaming fix (memory-safe, byte-identical figures). Test cases TC-11 through TC-15 ensure required journeys and critical anti-goals remain unbroken. All tests run on the **live 3.3 GB database** with a freshly warmed, quiet backend to confirm the fix works at production scale.
