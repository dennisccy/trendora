# goal-mcp-loop-iter-24 Functional Test Plan

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Frontend Present:** yes

## Phase Goal

Make Trendora's core pages and APIs measurably fast on the 30-year / 590-symbol basis by tuning SQLite, optimizing index hygiene, eliminating N+1 queries, and cheapening the readiness probe. Commit latency budgets as never-regress contracts in `reports/perf-budgets.md`. Add a new read-only storage card on `/data` (Data Manager) displaying the platform's current database footprint (file size + row counts).

## Test Cases

### TC-01 — Item B: SQLite pragmas apply only to SQLite URLs

**Type:** api
**Preconditions:**
- `app/db.py:make_engine` is callable with both a SQLite URL and a non-SQLite URL
- `config.yaml` contains a new `database.pragmas` block with keys: `journal_mode`, `synchronous`, `busy_timeout`, `cache_size`, `mmap_size`, `temp_store`

**Steps:**
1. Create a test SQLite URL (e.g., `sqlite:///tmp/test.db`)
2. Call `make_engine(sqlite_url)` and obtain the connection
3. Execute `PRAGMA journal_mode;` and verify it returns `wal`
4. Execute `PRAGMA synchronous;` and verify it returns `1` (NORMAL)
5. Execute `PRAGMA busy_timeout;` and verify it returns `30000`
6. Create a test non-SQLite URL (e.g., `postgresql://localhost/dummy` without connecting)
7. Verify that the pragma hook does NOT execute for non-SQLite URLs (no error, no dialect-specific code runs)

**Expected outcome:** SQLite URLs apply all configured pragmas; non-SQLite URLs skip the pragma hook entirely
**Pass criteria:** SQLite pragmas are readable and match config values; non-SQLite engine creation succeeds without attempting pragma application

---

### TC-02 — Item C: Duplicate index removed, date index added, query plans correct

**Type:** artifact
**Preconditions:**
- Database schema has been initialized post-startup
- `models.py` no longer contains `Index("ix_daily_prices_symbol_date", "symbol", "date")` or `Index("ix_forward_returns_run_symbol", "run_id", "symbol")`
- `Index("ix_daily_prices_date", "date")` has been added

**Steps:**
1. Query `sqlite_master` for all indexes on `daily_prices` table
2. Assert that `ix_daily_prices_symbol_date` does NOT exist
3. Assert that `ix_daily_prices_date` DOES exist
4. Query `sqlite_master` for all indexes on `forward_returns` table
5. Assert that `ix_forward_returns_run_symbol` does NOT exist
6. Execute `EXPLAIN QUERY PLAN SELECT * FROM daily_prices WHERE symbol='AAPL' AND date='2024-01-01'` and verify it uses the unique index (not a table scan)
7. Execute `EXPLAIN QUERY PLAN SELECT MAX(date) FROM daily_prices` and verify it uses `ix_daily_prices_date`
8. Execute `EXPLAIN QUERY PLAN SELECT * FROM daily_prices GROUP BY date` and verify it uses `ix_daily_prices_date`

**Expected outcome:** Duplicate indexes are removed, new date index is present, and query plans use the expected indexes
**Pass criteria:** Index list matches exactly (only expected indexes present); query plans show SEARCH or SEARCH with the specific index name, never SCAN

---

### TC-03 — Item D: Ticker-filtered fetch is byte-identical to full deserialize

**Type:** api
**Preconditions:**
- `snapshot_serving.stored_stock_rows` is the prior full-deserialize path
- A new filtered variant exists that queries by ticker list instead of deserializing all rows
- A stock detail payload exists for at least one ticker (e.g., 'AAPL')

**Steps:**
1. Call the old path: `stored_stock_rows(session, run)` to get all rows
2. Deserialize and locate the row for ticker='AAPL'
3. Call the new filtered path: `stored_stock_rows_filtered(session, run, ['AAPL'])`
4. Verify the returned list contains exactly one row for 'AAPL'
5. Byte-compare the serialized JSON for both paths (same `record_json` content)
6. Call `GET /api/stocks/AAPL` and verify the payload matches both paths
7. Verify existing `test_api_engine.py` tests pass UNEDITED

**Expected outcome:** Filtered fetch returns byte-identical payload to the full-deserialize path; existing API tests remain green without modification
**Pass criteria:** Serialized record_json is identical (byte-for-byte); `test_api_engine.py` passes without any test file edits

---

### TC-04 — Item G: Readiness probe memoizes SPY calendar and uses one grouped query

**Type:** api
**Preconditions:**
- `readiness.py:compute_readiness` is callable
- The warmup calendar for SPY has been memoized
- The previous loop at `readiness.py:80` has been replaced with a single grouped query

**Steps:**
1. Call `compute_readiness(session, config)` with the same `(latest_date, cfg)` tuple twice
2. Verify that the SPY calendar is NOT re-fetched on the second call (memoization hit)
3. Run a query-count profiler (or mock the session to count queries)
4. Verify that exactly ONE `select(ScannerRun.asof_date).where(asof_date.in_(cadence_dates))` query is issued (not N queries, one per date)
5. Verify the returned `{state, warmup:{done, total, status, message}}` shape and values match the prior behavior

**Expected outcome:** The readiness probe issues exactly one grouped query and uses memoization; returned shape and values are unchanged
**Pass criteria:** Query count = 1 for the cadence-dates existence check; memoization prevents re-fetch on repeated calls; warmup counts match

---

### TC-05 — Item H: Missing data diagnostic uses one bounded query, not N+1

**Type:** api
**Preconditions:**
- `data_manager._missing_data_diagnostic` is callable with a universe of symbols
- The prior N+1 loop at `:244-281` has been replaced with a single grouped/windowed query

**Steps:**
1. Call `_missing_data_diagnostic(session, universe, first_bar, last_bar)` where universe has ~120 symbols
2. Profile query count (or mock session)
3. Verify exactly ONE query is issued that fetches `(symbol, date)` tuples for all universe members in one call
4. Verify the returned diagnostic structure is unchanged: `{no_history, thin, intra_series_gaps, affected_count}`
5. Byte-compare the diagnostic output against a prior run with the same data

**Expected outcome:** Diagnostic uses a single bounded query instead of N queries; output is byte-identical
**Pass criteria:** Query count = 1 (not 120+); diagnostic structure and values match prior behavior exactly

---

### TC-06 — Item K (backend): compute_capacity returns correct counts and file size

**Type:** api
**Preconditions:**
- `app.engine.data_manager:compute_capacity(session, config)` is implemented
- The database contains sample data (or is empty for the zero-state test)

**Steps:**
1. Call `compute_capacity(session, config)` on a database with known data
2. Verify the returned dict contains: `file_size` (bytes), `daily_prices_count` (int), `scanner_results_count` (int), `forward_returns_count` (int)
3. Verify counts match `select(func.count()).select_from(Model)` for each table
4. Verify `file_size` is the byte size of the DB file on disk (matches `os.path.getsize(db_path)`)
5. Call `compute_capacity` on an empty/cold database and verify it returns all zeros (no error, no crash)

**Expected outcome:** `compute_capacity` returns correct row counts and file size; works gracefully on an empty database
**Pass criteria:** Counts match direct SQL queries; file size matches actual file on disk; empty-DB case returns `{file_size: 0, daily_prices_count: 0, scanner_results_count: 0, forward_returns_count: 0}`

---

### TC-07 — Item K (API): capacity field is additive on GET /api/data, not recomputed

**Type:** api
**Preconditions:**
- `GET /api/data` returns a `data_overview` payload
- The `capacity` field has been added to the existing payload structure (not a new endpoint)
- The payload already contains `coverage`, `runs`, `sources`, `macro`, etc.

**Steps:**
1. Call `GET /api/data` with an as-of date
2. Verify the response contains all prior keys (coverage, runs, sources, macro, etc.) unchanged
3. Verify the response contains a NEW `capacity` key with the structure `{file_size, daily_prices_count, scanner_results_count, forward_returns_count}`
4. Verify that the capacity values are stable across repeated calls (not recomputed on every request)
5. Verify no other payload shape has changed (byte-compare against expected structure)

**Expected outcome:** `capacity` field is additive to the existing payload; all prior fields are unchanged; capacity is computed once and served
**Pass criteria:** Response is valid JSON; `capacity` key exists and is well-formed; all prior keys present and unchanged

---

### TC-08 — Item K (harness): measure-perf.sh exists, runs in prod mode, records budgets

**Type:** artifact
**Preconditions:**
- `scripts/measure-perf.sh` has been created
- Services can be started in prod mode (`scripts/start-backend.sh` / `scripts/start-frontend.sh`)
- `reports/perf-budgets.md` file exists

**Steps:**
1. Verify `scripts/measure-perf.sh` is executable and contains curl commands (not dev.sh)
2. Start backend in prod mode and verify it listens on the configured port
3. Run `scripts/measure-perf.sh` and capture output
4. Verify it measures warm latencies for: `GET /api/stocks`, `/api/stocks/{ticker}`, `/api/data`, `/api/health`
5. Verify it runs one bounded backfill job via the jobs API and records timing
6. Verify it calls `compute_capacity` and appends results to `reports/perf-budgets.md`
7. Check `reports/perf-budgets.md` contains a new row with before/after latencies

**Expected outcome:** Script runs successfully, measures all endpoints, records budgets in the markdown file
**Pass criteria:** `scripts/measure-perf.sh` completes without error; `reports/perf-budgets.md` contains at least one new measurement row

---

### TC-09 — Performance budgets met: warm latencies within targets

**Type:** artifact
**Preconditions:**
- `reports/perf-budgets.md` has been updated with fresh measurements
- Target budgets: pages ≤ 3 s warm; `/api/stocks` ≤ 1.5 s; `/api/stocks/{ticker}` ≤ 0.3 s; `/api/data` ≤ 1.5 s warm; `/api/health` ≤ 0.1 s

**Steps:**
1. Read the most recent measurement row from `reports/perf-budgets.md`
2. Extract warm latencies for each endpoint
3. Compare each against the budget: `/api/health` ≤ 0.1 s, `/api/stocks/{ticker}` ≤ 0.3 s, `/api/stocks` ≤ 1.5 s, `/api/data` ≤ 1.5 s
4. For pages: measure time-to-interactive for `/stocks`, `/stocks/AAPL` (with Full-history toggle), `/data`, `/evidence` and verify all ≤ 3 s
5. If a budget is infeasible, verify it is recorded WITH the measured value as the new contract (not omitted)

**Expected outcome:** All measured endpoints meet their budgets OR a budget is explicitly recorded as infeasible with its measured value
**Pass criteria:** Each endpoint's measured latency ≤ budget, OR infeasible budget is documented with evidence

---

### TC-10 — Cold /api/data path completes ≤ 60s without OOM

**Type:** api
**Preconditions:**
- Backend is running with 6144 MB memory cap
- `/api/data` has been cold-started (no prior requests)
- Item H (N+1 fix) has been applied

**Steps:**
1. Stop backend and clear any caches
2. Start backend fresh with memory monitoring
3. Call `GET /api/data?as_of=2024-01-01` (a cold path request)
4. Measure elapsed time and memory usage
5. Verify the request completes and returns HTTP 200
6. Verify elapsed time ≤ 60 seconds
7. Verify memory usage does not exceed 6144 MB

**Expected outcome:** Cold /api/data completes within 60 seconds without OOM
**Pass criteria:** Elapsed time ≤ 60 s; HTTP 200 response; memory never exceeds 6144 MB cap; response is valid JSON

---

### TC-11 — Byte-identity verified: GET /api/stocks returns same values

**Type:** api
**Preconditions:**
- Pre-change golden snapshot of `GET /api/stocks` response exists (or a prior run is recorded)
- All optimizations (items B, C, D, G, H) have been applied

**Steps:**
1. Call `GET /api/stocks?as_of=2024-06-01` (a date with data)
2. Capture the response JSON
3. Byte-compare against the golden snapshot (or a prior known-good response)
4. Verify no fields have changed, no values have changed, no ordering has changed

**Expected outcome:** API response is byte-identical to the pre-change golden
**Pass criteria:** Binary diff is zero; JSON parse-tree is identical

---

### TC-12 — Frontend storage card displays capacity snapshot

**Type:** browser
**Preconditions:**
- Frontend is running in prod mode (`scripts/start-frontend.sh`)
- Backend has data and `GET /api/data` returns capacity field
- `apps/frontend/app/data/page.tsx` contains the new storage card

**Steps:**
1. Open Chrome and navigate to `http://localhost:3255/data`
2. Wait for page to load and settle
3. Scroll to find the storage card (should be after CoveragePanel)
4. Verify the card displays: file size (e.g., "12.4 MB"), row counts for daily_prices, scanner_results, forward_returns
5. Verify the values match the backend's `compute_capacity` output
6. On an empty/cold database, verify the card shows "0 B" and "0 rows" (not an error)

**Expected outcome:** Storage card renders the capacity snapshot with correct values; handles empty-DB case gracefully
**Pass criteria:** Card is visible on the /data page; values match compute_capacity; no error on cold DB

---

### TC-13 — Journey J-15 target: pages render and are interactive within budget

**Type:** browser
**Preconditions:**
- Both backend and frontend are running in prod mode
- `rm -rf apps/frontend/.next` has been run to clear next cache
- User can navigate to core pages

**Steps:**
1. Navigate to `/stocks` and measure time-to-interactive; verify ≤ 3 s warm and renders without blank/frozen frame
2. Navigate to `/stocks/AAPL` and measure time-to-interactive; verify ≤ 3 s warm
3. Toggle the Full-history button and verify page updates smoothly without OOM
4. Navigate to `/data` and verify the storage card is visible with real numbers
5. Navigate to `/evidence` and verify page renders and is interactive within 3 s
6. Verify all pages show honest initializing/progress state if slow (never a blank/frozen/application-error page)

**Expected outcome:** All target pages load within budget, remain interactive, and display the new storage card
**Pass criteria:** All pages time-to-interactive ≤ 3 s; no blank/frozen/error frames; storage card visible on /data

---

### TC-14 — Journey J-15 regression check: required journeys J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-14 still pass

**Type:** browser
**Preconditions:**
- Browser QA has captured evidence for J-15 (new storage card, performance budgets)
- Live replay of required journeys is configured

**Steps:**
1. Execute the live-replay for journey J-01 (some initial workflow, e.g., user sees the homepage)
2. Execute the live-replay for journey J-03 (e.g., user can view stock detail)
3. Execute the live-replay for journey J-04, J-05, J-10, J-12, J-13, J-14 in sequence
4. Record any failures or regressions
5. Take screenshots for any regressions found

**Expected outcome:** All required journeys remain green; no new regressions
**Pass criteria:** All 8 journeys complete successfully with no visual/functional changes

---

### TC-15 — Existing unit tests remain unedited and pass

**Type:** artifact
**Preconditions:**
- Existing unit test files: `test_api_engine.py`, `test_api_watchlist.py`, relevant sections of `test_data_manager.py`, `test_health.py`
- These files are NOT modified during this iteration

**Steps:**
1. Verify git status shows NO edits to `test_api_engine.py` and `test_api_watchlist.py`
2. Run `pytest apps/backend/tests/test_api_engine.py -v` and capture output
3. Run `pytest apps/backend/tests/test_api_watchlist.py -v` and capture output
4. Count total pass/fail for byte-identity gate tests
5. Verify no test has been edited to pass

**Expected outcome:** Existing tests are unedited and pass (regression proof)
**Pass criteria:** Test files show no git modifications; 100% of existing tests pass without any expectation edits

---

### TC-16 — Error path: invalid as_of on /api/data falls back gracefully

**Type:** api
**Preconditions:**
- `/api/data` has fallback logic for invalid as_of dates

**Steps:**
1. Call `GET /api/data?as_of=2099-12-31` (a future date with no data)
2. Verify the response is HTTP 200 (not 500)
3. Verify the response contains capacity field and honest zero/null values for coverage
4. Verify no crash or OOM occurs

**Expected outcome:** Invalid as_of falls back gracefully with a valid response
**Pass criteria:** HTTP 200 response; capacity field present; no error frame

---

## Summary

**Total test cases:** 16
**API tests:** 9 (TC-01, TC-03, TC-04, TC-05, TC-06, TC-07, TC-10, TC-11, TC-16)
**Artifact checks:** 5 (TC-02, TC-08, TC-09, TC-15)
**Browser tests:** 2 (TC-12, TC-13, TC-14 browser replay)

All test cases validate the fast-platform optimizations (SQLite tuning, index hygiene, N+1 fixes, cheap readiness probe), the new storage card, performance budgets, byte-identity of optimized paths, graceful error handling, and regression-free journeys per the DEFINITION OF DONE and TESTING REQUIREMENTS.
