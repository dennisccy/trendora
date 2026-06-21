# Goal Iteration 42 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42
**Date:** 2026-06-20
**Frontend Present:** no

## Phase Goal

Backend hardening: ensure `/api/data` and related read paths stay responsive and memory-bounded under concurrent load, with every served coverage/membership value byte-identical to pre-optimization output.

## Test Cases

### TC-01 — Concurrency load test: K parallel `/api/data` calls return within latency bound

**Type:** api
**Preconditions:**
- Backend running on localhost:8000
- Database seeded and warm
- Concurrency cap (`--limit-concurrency`) configured in `start-backend.sh`
- Memory cap (`ulimit -v`) configured

**Steps:**
1. Launch K=10 parallel HTTP requests to `GET /api/data?as_of=<latest_date>` with no stagger (all fire within 100ms)
2. Record wall-clock time for each request start to response complete
3. Record process RSS (peak memory) during the load
4. Record `/health` response time sampled every 2 seconds during the load

**Expected outcome:**
- All K requests return a 200 status
- P95 latency ≤ 35 seconds (reasonable bound for heavy compute)
- Peak process RSS ≤ configured cap (set high enough to allow the one shared bar cache, ~1.5GB estimated)
- `/health` latency stays ≤ 500ms throughout (light endpoint not starved)

**Pass criteria:**
- `HTTP 200` for all K requests
- `latency_p95 <= 35000` milliseconds
- `process_rss_peak <= configured_memory_cap_bytes`
- `/health` response time never exceeds 500ms during load

---

### TC-02 — Membership cache not invalidated by forward-return-only inserts

**Type:** api
**Preconditions:**
- Backend running
- Database with committed seed + at least one forward-return row already present
- `membership_timeline_cached` table has at least one pre-computed row with the membership-specific stamp

**Steps:**
1. Query the current `/api/data` payload; extract and record the `membership_timeline` array
2. Insert a NEW `ForwardReturn` row into the database (with a symbol and date not in the current snapshot) via backend API or direct DB access
3. Query `/api/data` again (SAME as_of date, CURRENT snapshot date)
4. Compare the `membership_timeline` array from step 3 to the baseline from step 1

**Expected outcome:**
- The `membership_timeline` array is byte-identical (same members, same order, same values)
- The cache was HIT (not recomputed) — verify by adding a log/instrumentation point in `membership_timeline_cached` and confirming it was not called

**Pass criteria:**
- `deep_equals(response_1.membership_timeline, response_2.membership_timeline) == True`
- Cache HIT recorded (log line or counter) in step 3

---

### TC-03 — Membership cache IS invalidated by snapshot add

**Type:** api
**Preconditions:**
- Backend running
- Current `/api/data` payload recorded (step 1 of TC-02 baseline)
- `membership_timeline_cached` has a pre-populated row

**Steps:**
1. Insert a NEW `ScannerRun` snapshot row (new date, new run_id) via the backend data-manager API or direct DB
2. Trigger a backfill/refresh of that new snapshot so it has bars + membership data
3. Query `/api/data?as_of=<new_date>` to retrieve the new snapshot's data
4. Verify the membership_timeline_cached table shows a DIFFERENT stamp for the new snapshot

**Expected outcome:**
- The new snapshot's membership data is computed fresh (cache MISS / recompute, not a stale HIT from the previous stamp)
- The new `membership_timeline` payload differs from the previous baseline (new snapshot, new members or different counts)

**Pass criteria:**
- `GET /api/data?as_of=<new_snapshot_date>` returns HTTP 200
- `membership_dataset_stamp` differs from the pre-change baseline
- `membership_timeline` content differs (new members or count change)

---

### TC-04 — Single-flight concurrency: N concurrent `/api/data` calls cost ~1 heavy compute, not N

**Type:** api
**Preconditions:**
- Backend running with instrumentation/logging enabled
- Concurrency load test setup (K=5 or more parallel callers)
- Instrumentation in `compute_coverage` to log/count each heavy compute (e.g., `_resolved_universe` resolve)

**Steps:**
1. Enable DEBUG logging for `compute_coverage` so each invocation logs a unique marker
2. Fire K=5 parallel `GET /api/data` requests for the SAME as_of date, all starting within 100ms
3. Wait for all K requests to complete
4. Count the number of `_resolved_universe` resolve log markers in the backend logs during the K-request window

**Expected outcome:**
- Heavy-compute count ≈ 1 (or at most 2 if there is a brief race window)
- NOT K or close to K (which would indicate no single-flight)

**Pass criteria:**
- `count(_resolved_universe_resolve_log_markers) <= 2` (allowing for a brief startup race)

---

### TC-05 — Byte-identity: `compute_coverage` output unchanged before/after optimization

**Type:** api
**Preconditions:**
- Backend running (iter-42 implementation)
- A baseline payload from a pre-optimization reference snapshot available (or commit hash of iter-41)
- Current seed database (1369+ dates of history)

**Steps:**
1. Call `GET /api/data?as_of=<latest_date>` and extract the `coverage` object
2. Deep-compare the `coverage` object to a baseline (pre-iter-42) reference payload for the same as_of date
3. For each coverage field (coverage_pct, missing_data, insufficient_for_analysis, etc.), verify exact equality

**Expected outcome:**
- Coverage object is byte-identical (same structure, same numeric values, same explanatory text)
- No new keys added to the coverage payload
- No rounding differences or floating-point drift

**Pass criteria:**
- `coverage_response == baseline_coverage` (deep equality)
- No extra keys in the response payload

---

### TC-06 — Invalid `?as_of` gracefully falls back to latest stored run date

**Type:** api
**Preconditions:**
- Backend running
- Database with seed snapshots for multiple dates

**Steps:**
1. Query `/api/data?as_of=2099-12-31` (a future date with no snapshot)
2. Record the HTTP status code and the `as_of_resolved` field in the response

**Expected outcome:**
- HTTP 200 (not 4xx; graceful fallback)
- `as_of_resolved` is set to the latest stored snapshot date (not 2099-12-31)
- `coverage` is the latest snapshot's coverage, NOT an error or empty state

**Pass criteria:**
- `HTTP 200`
- `as_of_resolved < 2099-12-31` (fallback to a real date)

---

### TC-07 — Required-still-passing rendered journeys: J-94 (universe diagnostic + timeline)

**Type:** browser
**Preconditions:**
- Frontend running on localhost:3000
- Backend running and seeded
- A screenshot baseline of J-94 from iter-41 available for comparison

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Wait for page hydration (max 30 seconds; record actual hydration time)
3. Scroll down to the "Universe Diagnostic" section (below the fold)
4. Screenshot the diagnostic block: legend, heatmap/timeline, and the three honesty labels
5. Compare the numbers (coverage %, missing-data count, insufficient-for-analysis count) to the iter-41 baseline

**Expected outcome:**
- Page loads with no 404 / 500 error
- Hydration completes within 45 seconds
- Universe Diagnostic section is visible and populated with data
- Coverage %, missing-data count, and insufficient-for-analysis values are byte-identical to baseline
- The membership-timeline step function shows the same rising/falling pattern

**Pass criteria:**
- No blank/skeleton state in the diagnostic block
- `coverage_pct_displayed == baseline_coverage_pct` (exact numeric match in rendered HTML)
- Membership count changes match baseline (Entries and Exits columns populated)

---

### TC-08 — Required-still-passing rendered journeys: J-96 (rising timeline with populated Entries/Exits)

**Type:** browser
**Preconditions:**
- Frontend running on localhost:3000
- Backend running and seeded
- Baseline screenshot from iter-41

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Wait for hydration
3. Locate the "Membership Timeline" chart on the page (typically a step-function graph)
4. Verify the chart renders with at least 3 data points (rising/falling steps)
5. Check the "Entries" and "Exits" columns are populated with numbers (not 0 or N/A for all rows)
6. Screenshot the chart and compare the visible data points to the baseline

**Expected outcome:**
- Chart renders (not a blank canvas or error state)
- The step function shows clear rises and falls (membership changes over time)
- Entries and Exits columns have non-zero values for at least 2 rows
- The shape and values of the timeline match the baseline

**Pass criteria:**
- Chart is rendered with SVG/canvas elements (not a placeholder)
- `membership_timeline_entry_count >= baseline_entry_count` (same data range)
- Visual shape of the step function matches baseline (same peaks and troughs)

---

### TC-09 — Required-still-passing rendered journeys: J-93 (`/stocks` slides)

**Type:** browser
**Preconditions:**
- Frontend running on localhost:3000
- Backend running and seeded
- Baseline screenshot or data export from iter-41 `/stocks` page

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Wait for page hydration
3. Verify the main table/grid loads and shows at least 10 stocks
4. Check that the "Leadership Score" and "Entry Quality Score" columns show numeric values (A–E buckets with 0–100 scores)
5. Scroll horizontally to verify all score columns are present and populated
6. Compare a sample of 3 stocks' scores to the baseline

**Expected outcome:**
- Page loads and renders a stocks table
- Leadership and Entry Quality columns display scores
- Risk Score column is visible and populated
- Sample stock scores match baseline (byte-identical or very close if rounding is allowed)

**Pass criteria:**
- Table has at least 10 rows with non-empty leadership and entry-quality scores
- Sample stock A: leadership score matches baseline ± 0 points (byte-identical per anti-goal)
- Sample stock B: leadership score matches baseline ± 0 points
- Sample stock C: leadership score matches baseline ± 0 points

---

### TC-10 — Dashboard cluster required-still-passing: J-87/J-88/J-89/J-90/J-97/J-98/J-99

**Type:** browser
**Preconditions:**
- Frontend running on localhost:3000
- Backend running and seeded
- Baseline screenshots/data exports from iter-41 Dashboard page

**Steps:**
1. Navigate to `http://localhost:3000/` (or `/dashboard`)
2. Wait for page hydration
3. Verify the main dashboard layout loads (header, theme rankings, sector rankings, regime indicator)
4. Check that the regime label (e.g., "Risk-On", "Risk-Off") is rendered
5. Verify theme rankings table shows at least 5 themes with scores
6. Verify sector rankings table shows at least 5 sectors with scores
7. Sample 2 themes and 2 sectors from the current page and compare their scores to the baseline

**Expected outcome:**
- Dashboard page loads and hydrates
- Regime label is visible and matches baseline (e.g., both say "Risk-On" or both say "Risk-Off")
- Theme rankings table shows the same top N themes in the same order as baseline
- Sector rankings show the same top N sectors in the same order as baseline
- Sampled scores are byte-identical to baseline

**Pass criteria:**
- Regime label == baseline regime label
- Top 3 theme names and order match baseline
- Top 3 sector names and order match baseline
- Sample theme X score == baseline score ± 0
- Sample sector Y score == baseline score ± 0

---

### TC-11 — Critical journey J-18: no new native date inputs

**Type:** artifact
**Preconditions:**
- Frontend source code at `apps/frontend/src`
- No new frontend files added in this iteration

**Steps:**
1. Search the frontend source for all `input[type="date"]` elements
2. Search the frontend source for all `<input.*date` patterns (case-insensitive)
3. Count the total occurrences
4. Compare to the iter-41 baseline count (expect 0 new additions)

**Expected outcome:**
- The count of native date inputs is the SAME as iter-41 baseline (no new date pickers added)
- If there are any date inputs, verify they are pre-existing (not new)

**Pass criteria:**
- `count(input[type="date"]) == baseline_count` (0 new date inputs added)
- Frontend diff shows NO new `input[type="date"]` patterns

---

### TC-12 — Critical journey J-07: Risk-Off regime → 0 Actionable stocks

**Type:** browser
**Preconditions:**
- Backend seeded with a Risk-Off snapshot available
- Frontend running on localhost:3000

**Steps:**
1. Query the backend to find a snapshot date where the regime is Risk-Off
2. Navigate to `/stocks?as_of=<risk-off-date>` to view that date's stocks
3. Check the "Setup Status" or "Actionable" column for all visible stocks
4. Count the number of stocks marked "Actionable" (should be zero)

**Expected outcome:**
- All visible stocks show a non-Actionable status (e.g., "Watchlist Only", "Breakout Watch", "Pullback Watch" — but NOT "Actionable")
- The count of Actionable stocks is 0

**Pass criteria:**
- `actionable_stock_count == 0` for the Risk-Off snapshot
- All stocks display a setup status other than "Actionable"

---

### TC-13 — Load once per symbol: `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes

**Type:** api
**Preconditions:**
- Backend test suite available
- Database seeded

**Steps:**
1. Run the specific test: `pytest apps/backend/tests/test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once -v`
2. Capture the test output and exit code

**Expected outcome:**
- Test passes (exit code 0)
- The test assertion confirming load count (not just value equality) succeeds

**Pass criteria:**
- `pytest exit code == 0`
- Test log shows "PASSED"

---

### TC-14 — No new table added (or registered if added)

**Type:** artifact
**Preconditions:**
- Backend source code at `apps/backend/`
- `test_db.py` expected-tables guard present

**Steps:**
1. Inspect `apps/backend/app/engine/data_manager.py` for new SQLModel classes with `table=True`
2. If a new model is found, check that it is registered in `apps/backend/tests/test_db.py` in the expected-tables guard
3. Run: `pytest apps/backend/tests/test_db.py::test_db_expected_tables_match -v`

**Expected outcome:**
- No unexpected new tables are created
- If a new table IS created (e.g., a new cache model), it is explicitly registered in `test_db.py`
- The expected-tables test passes

**Pass criteria:**
- `pytest exit code == 0` for the expected-tables test
- If a new table was added, verify it is in the `test_db.py` expected set

---

### TC-15 — `/health` endpoint stays responsive under heavy load

**Type:** api
**Preconditions:**
- Backend running with load-test scenario active (from TC-01)
- Concurrency cap enforced

**Steps:**
1. Start the concurrency load test (K=10 parallel `/api/data` requests)
2. During the load, send 10 `/health` requests in quick succession (within 2 seconds of when the heavy load is running)
3. Record the latency of each `/health` response

**Expected outcome:**
- All `/health` requests return HTTP 200
- Latency is under 500ms for all 10 requests (even while heavy `/api/data` is in flight)

**Pass criteria:**
- `HTTP 200` for all 10 health checks
- `latency_p95(/health) <= 500ms` during the load

---

## Summary

Total test cases: 15
API tests: 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-13, TC-15)
Browser tests: 5 (TC-07, TC-08, TC-09, TC-10, TC-12)
Artifact checks: 2 (TC-11, TC-14)

**Critical tests (MUST pass for GOAL_ACHIEVED):**
- TC-01: Concurrency latency and RSS bounded
- TC-02, TC-03: Membership cache invalidation logic correct
- TC-04: Single-flight reduces compute count
- TC-05: Byte-identity of coverage preserved
- TC-07, TC-08, TC-09, TC-10: Required journeys still pass live
- TC-11, TC-12: J-18 and J-07 critical invariants hold
- TC-13: Iter-37 load-once invariant preserved
