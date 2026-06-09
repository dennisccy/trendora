# Goal Iteration 25 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-08
**Frontend Present:** yes

## Phase Goal

Surface a read-only Missing-data diagnostic (no-history / thin / intra-series gaps) with a one-click "pull exactly the gap" (J-37), unify every unfinished import into one Resume/Retry/Remove panel with plain-language state (J-38), and capture two already-built-but-uncaptured Data-Manager browser flows (J-39 seed-safe Remove-data confirm-preview; J-35 injected-provider expand end-to-end).

## Test Cases

### TC-01 — J-37 Missing-data diagnostic renders all three categories with exact shortfalls

**Type:** browser
**Preconditions:** 
- Frontend running cleanly (dev `.next` cleared, `next dev` restarted, `/_next/static/chunks/main-app.js` → 200, health badge cleared "Checking backend…")
- Backend seeded with injected fixture containing: one universe member with zero bars (no-history), one member with `0 < bar_count < indicators.min_history_bars` (thin), one member with a trading-day gap inside its own first→last range (intra-series gap)

**Steps:**
1. Navigate to `/data` page
2. Locate the "Missing-data diagnostic" panel
3. Verify it displays three rows, one per affected category
4. For each row, verify it shows: symbol name, category label (no-history / thin / intra-series gap), exact shortfall (e.g., "bars-have: 2 / bars-needed: 30" for thin; "missing days: 5 [2026-01-15 to 2026-01-20]" for intra-series gap)

**Expected outcome:** All three diagnostic categories render correctly with exact shortfalls; no universe member marked as "fine" appears in the diagnostic

**Pass criteria:** 
- The diagnostic displays exactly 3 rows (no more, no less) for the injected fixture
- Each row shows symbol, category, and exact shortfall values matching the fixture data
- No fabricated or computed values appear; all text comes directly from backend diagnostic payload

---

### TC-02 — J-37 "Pull the missing data" constructs a gap-exact job

**Type:** api
**Preconditions:** 
- Backend seeded with fixture from TC-01
- Frontend running
- Missing-data diagnostic visible

**Steps:**
1. On the Missing-data diagnostic panel, click "Pull the missing data" for the thin member
2. Capture the HTTP `POST /api/data/jobs` request body
3. Verify the request contains: `symbols` array with only the affected symbol, `[start, end]` date range that covers ONLY the shortfall (not the whole universe window)
4. Call `GET /api/data/jobs/{id}` with the returned job ID
5. Verify the job's `source` matches the configured source and the job's `symbols`/`date_range` match the diagnosed shortfall

**Expected outcome:** The job is created with `symbols` and date range exactly matching the diagnosed gap, not the whole universe or a broader window

**Pass criteria:** 
```
curl -X POST http://localhost:8000/api/data/jobs \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["THIN_SYMBOL"], "start": "2026-01-01", "end": "2026-02-01"}' \
  | jq '.id' > job_id

curl http://localhost:8000/api/data/jobs/$(cat job_id) | jq '.symbols, .date_range' \
  | grep -E "THIN_SYMBOL|2026-01-01|2026-02-01"
```
Response must show job with exact symbols + range; not `symbols: ["*"]` or a broader window

---

### TC-03 — J-37 "Pull all missing" dispatches a job over all diagnosed gaps

**Type:** browser
**Preconditions:** 
- Missing-data diagnostic visible with multiple affected members (from TC-01)
- Frontend running

**Steps:**
1. Click "Pull all missing" button at the top of the diagnostic panel
2. Wait for the job to start (verify a live progress indicator appears)
3. Verify the job card displays progress (e.g., "Fetching 3 symbols...")
4. Verify the backend's job object includes all three affected symbols in `symbols` array

**Expected outcome:** A single job is created that covers all diagnosed gaps at once; job status progresses normally

**Pass criteria:** 
- Exactly one job is dispatched (not three separate jobs)
- The job's `symbols` array contains all three affected symbols
- Job status transitions from `queued` → `running` → `completed` or `paused` (if hit a rate limit)

---

### TC-04 — J-37 pull-missing completes and clears the diagnostic row

**Type:** browser
**Preconditions:** 
- A pull-missing job dispatched from TC-02 or TC-03
- Job using offline injected-provider (completes quickly)
- Backend responding normally

**Steps:**
1. Wait for the pull job to reach `completed` status
2. Observe the Missing-data diagnostic panel
3. Verify that the affected row(s) are removed/cleared from the diagnostic (the symbol no longer appears)
4. Verify the J-36 Coverage panel (per-symbol table below the diagnostic) now reflects the new bars (symbol moves from "insufficient" state to showing bar count, or bars-count increases)

**Expected outcome:** Pulling missing data completes; the diagnostic row vanishes; coverage table updates to reflect new bars

**Pass criteria:** 
- Row no longer visible in the Missing-data diagnostic panel
- J-36 per-symbol coverage table reflects the newly fetched bars (either new symbol entry or increased bar count)
- Job final status is `completed`

---

### TC-05 — J-37 pull-missing on provider failure surfaces explicit error (not fabricated bar)

**Type:** api
**Preconditions:** 
- Backend configured to force a provider error (mock/test mode simulating unreachable provider)
- Missing-data diagnostic visible

**Steps:**
1. Trigger a pull-missing job against the mocked unreachable provider
2. Wait for the job to complete with an error
3. Call `GET /api/data/jobs/{id}` to retrieve the job status
4. Verify the job status is either `paused` (if rate-limited) or `failed` (if provider unreachable)
5. Verify the `errors[]` array in the job response contains an explicit error message (not empty)
6. Verify no bars were created for the affected symbol in the database

**Expected outcome:** Pull fails with an explicit error message; no fabricated bars created; diagnostic still shows the symbol as missing

**Pass criteria:** 
```
curl http://localhost:8000/api/data/jobs/<id> | jq '.status, .errors'
# Must show: status: "paused" or "failed", errors: [<explicit error string>]
# Not: status: "completed" with empty errors or bars in DB
```

---

### TC-06 — J-38 Unified Unfinished-imports panel shows paused/partial/failed rows with plain-language state

**Type:** browser
**Preconditions:** 
- Backend seeded with: one resumable (paused) import checkpoint, one partial (some symbols failed), one failed (all symbols failed)
- Frontend running
- `/data` page rendered

**Steps:**
1. Locate the "Unfinished-imports" panel on `/data`
2. Verify it displays three rows (paused, partial, failed)
3. For the paused row: verify it shows "Paused — hit a provider rate-limit (429); progress saved" (or similar plain-language text)
4. For the partial row: verify it shows "Partial — X/Y symbols ok, Z failed" with counts
5. For the failed row: verify it shows "Failed — every symbol failed; provider unreachable"
6. Each row should show done/remaining/failed counts and chunk progress where applicable

**Expected outcome:** Unfinished-imports panel displays all three job-control states with clear, descriptive text and counts

**Pass criteria:** 
- Exactly 3 rows visible (paused, partial, failed)
- Each row contains the plain-language state string + numeric counts
- State strings match the expected descriptions (not generic or empty)
- No soft-dismissed jobs appear in the list

---

### TC-07 — J-38 Resume button continues from next_chunk_index and survives restart

**Type:** api
**Preconditions:** 
- Backend seeded with a resumable import checkpoint at `next_chunk_index = 2` (2 chunks completed, more remaining)
- Frontend running

**Steps:**
1. On the Unfinished-imports panel, click "Resume" for the paused/resumable row
2. Verify the HTTP call is `POST /api/data/jobs/{import_id}/resume`
3. Wait for the job to progress and complete (or pause again if another rate limit)
4. Call `GET /api/data` and check the unfinished_imports list
5. Verify the checkpoint's `next_chunk_index` has advanced (e.g., from 2 to 3)
6. Verify no duplicate bars were created for chunks already completed in step 1

**Expected outcome:** Resume continues from the saved checkpoint; job progresses without re-fetching already-fetched chunks

**Pass criteria:** 
```
curl -X POST http://localhost:8000/api/data/jobs/<import_id>/resume

curl http://localhost:8000/api/data | jq '.unfinished_imports[] | select(.id == "<import_id>") | .chunk_progress'
# Must show: next_chunk_index has advanced (or import removed if fully completed)
```

---

### TC-08 — J-38 Retry re-runs only outstanding/failed work with no duplicate rows

**Type:** api
**Preconditions:** 
- Backend seeded with a partial import (some symbols ok, some failed; run completed with failures)
- Frontend running
- Database snapshot of bar count for symbols that succeeded before

**Steps:**
1. On the Unfinished-imports panel, click "Retry remaining/failed" for the partial row
2. Verify the HTTP call is `POST /api/data/jobs/{import_id}/retry`
3. Wait for the retry job to complete
4. Call `SELECT COUNT(*) FROM daily_prices WHERE symbol = <succeeded_symbol> AND date = <test_date>` before and after
5. Verify the count did not increase (no duplicate row)
6. For a failed symbol, verify it now has bars (or another explicit error if provider still unavailable)

**Expected outcome:** Retry dispatches only outstanding/failed symbols; per-`(symbol, date)` idempotency prevents duplicates

**Pass criteria:** 
- New job created with `symbols` only including previously-failed symbols (not all original symbols)
- No duplicate rows in `daily_prices` table for symbols that succeeded before the retry
- Successfully-fetched symbols now appear in coverage with updated bar count

---

### TC-09 — J-38 Remove/Dismiss drops job-control record only; audit trail preserved

**Type:** api
**Preconditions:** 
- Backend seeded with an unfinished import (resumable checkpoint or partial run)
- Frontend running
- Snapshot of the import's ID and the `data_provider_runs` audit row

**Steps:**
1. Note the import's ID and the corresponding `data_provider_runs.id` in the audit table
2. On the Unfinished-imports panel, click "Remove" or "Dismiss"
3. Verify the HTTP call is `POST /api/data/jobs/{id}/dismiss`
4. Verify the import is removed from the Unfinished-imports list
5. Query the database: verify the `ImportCheckpoint` or `DataProviderRun.dismissed` flag changed
6. Query `SELECT * FROM data_provider_runs WHERE id = <audit_id>` and verify the row still exists (not deleted)

**Expected outcome:** The import stops appearing in Unfinished-imports; job-control state is marked dismissed/deleted; immutable audit trail remains intact

**Pass criteria:** 
```
curl -X POST http://localhost:8000/api/data/jobs/<id>/dismiss

# Query audit table directly:
SELECT * FROM data_provider_runs WHERE id = '<audit_id>';
# Must return: row present, status unchanged (or dismissed flag added)

# Verify no scanner/price rows deleted:
SELECT COUNT(*) FROM daily_prices WHERE ... # Should match before-dismiss count
```

---

### TC-10 — J-38 Resume/Retry of needs-key source re-prompts for key (request-only, never stored)

**Type:** browser
**Preconditions:** 
- Backend seeded with a paused import from a key-required source (e.g., alpha-vantage, tiingo)
- Frontend running

**Steps:**
1. On the Unfinished-imports panel, click "Resume" (or "Retry") for a needs-key import
2. Verify a modal/dialog appears asking for the API key
3. Paste a test sentinel key (e.g., "test-key-sentinel")
4. Click "Resume"
5. Wait for the job to fail (or complete) and check the database and backend logs
6. Verify the sentinel key does NOT appear in: the job's `errors[]` response, the `unfinished_imports` payload, the `ImportCheckpoint`, the `data_provider_runs` audit row, or any log file
7. Verify the key is also NOT present in the HTTP response body of `GET /api/data/jobs/{id}` or any related endpoint

**Expected outcome:** Key is accepted in the request, used for the fetch, and immediately discarded; no persistence or echo

**Pass criteria:** 
```
grep -r "test-key-sentinel" reports/qa/ logs/ .claude/ || echo "Key leak test PASS"

curl http://localhost:8000/api/data/jobs/<id> | grep -i "test-key-sentinel" || echo "No key in response"

# Database audit log must not contain the key:
sqlite3 trendora.db "SELECT * FROM data_provider_runs WHERE id = '<id>';" | grep -i "test-key-sentinel" && echo "FAIL" || echo "PASS"
```

---

### TC-11 — J-37 and J-38 key-leak regression: REAL httpx error with ?token= scrubbed from UI surface

**Type:** api
**Preconditions:** 
- Backend configured to use mocked httpx transport with a key-in-URL sentinel
- Test key embedded in request (e.g., `?token=test-api-key`)

**Steps:**
1. Trigger a J-37 pull-missing job that hits the mocked provider (forced to error with a 401 / rate-limit containing the key in the URL)
2. Wait for the job to fail
3. Call `GET /api/data/jobs/{id}` and extract the job's error payload
4. Call `GET /api/data` to retrieve `unfinished_imports` (which includes the failed run's error state)
5. Search the response body for the sentinel key and for `?token=` / `?apikey=` patterns
6. Verify that the key and the `?token=...` URL fragment are NOT present in any response

**Expected outcome:** Even though the provider's actual error includes the key in the URL, the backend scrubs it before returning to the frontend

**Pass criteria:** 
```
# Trigger a J-37 pull with a sentinel key embedded:
curl -X POST http://localhost:8000/api/data/jobs \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["TEST"], "start": "2026-01-01", "end": "2026-01-31", "api_key": "test-key-sentinel"}' \
  | jq '.id' > job_id

# Wait for error, then check responses:
curl http://localhost:8000/api/data/jobs/$(cat job_id) | grep -i "token" && echo "FAIL: key in response" || echo "PASS"
curl http://localhost:8000/api/data | jq '.unfinished_imports[].errors' | grep -i "token" && echo "FAIL" || echo "PASS"
```

---

### TC-12 — J-39 Remove-data confirm-preview renders protected committed-seed breakdown (preview path only)

**Type:** browser
**Preconditions:** 
- Frontend running cleanly
- Backend seeded with live data including both committed-seed bars and user-added bars for a symbol
- Live database is NOT modified (preview only, never destructive confirm)

**Steps:**
1. Navigate to `/data` page
2. Locate the "Remove data" panel (J-39 existing feature)
3. Enter a symbol that has both committed-seed bars and user-added bars (e.g., NVDA)
4. Click the "Preview" button (NOT "Confirm")
5. Observe the preview modal showing:
   - Total removable bars (symbol count)
   - Date range of removable bars
   - Breakdown: X committed-seed bars (protected, shown as non-removable) vs Y user-added bars (removable)
   - Dependent cascade: rows/snapshots/metrics that would be affected if removal proceeds
6. Click "Close" (do NOT click Confirm)
7. Verify the database remains unchanged (bar count unchanged in live DB)

**Expected outcome:** Preview renders protected seed bars as non-removable; cascade is calculated; no database modification occurs

**Pass criteria:** 
- Preview modal displays the committed-seed breakdown (e.g., "Protected seed: 50 bars, User-added: 6 bars")
- Dependent cascade list shows affected snapshots/metrics
- Database query: `SELECT COUNT(*) FROM daily_prices WHERE symbol = 'NVDA'` returns same count before and after preview

---

### TC-13 — J-39 seed-only scope refusal (seed bars only in removal scope)

**Type:** browser
**Preconditions:** 
- Backend seeded with a symbol that has ONLY committed-seed bars and zero user-added bars
- Frontend running

**Steps:**
1. Navigate to `/data` → Remove data panel
2. Enter a symbol with only seed bars (e.g., AAPL with all original committed bars)
3. Click "Preview"
4. Observe the preview message (e.g., "Cannot remove — all bars are committed seed data (protected)")
5. Verify the "Confirm" button is disabled or not present

**Expected outcome:** Removal is refused with a clear message when the scope contains only seed bars

**Pass criteria:** 
- Preview modal displays an explicit refusal message mentioning seed-only protection
- "Confirm" button is disabled or hidden
- No database modification

---

### TC-14 — J-35 Injected-provider expand end-to-end: passers + omitted-with-reason + universe-count increase

**Type:** browser
**Preconditions:** 
- Frontend running cleanly
- Backend seeded with injected-provider that returns a specific universe expansion
- Initial `universe_count` < final `universe_count`

**Steps:**
1. Navigate to `/data` page
2. Locate the "Expand universe" control / button (J-35 existing feature)
3. Trigger an expand from the injected-provider
4. Wait for the expand job to complete
5. Verify the result shows:
   - "Passers": list of symbols newly added to universe
   - "Omitted with reason": list of symbols rejected by the provider with explanations
   - `universe_count` has increased (e.g., from 122 to 130)
6. Verify the Coverage panel (J-36) now includes the newly-added symbols

**Expected outcome:** Expand completes; universe-count increases; passers and omitted lists are displayed; coverage table reflects new members

**Pass criteria:** 
- Job status is `completed`
- `universe_count` displayed in Coverage header increased from baseline
- Expand result modal shows "X passers, Y omitted" with symbol lists
- New symbols appear in the per-symbol coverage table

---

### TC-15 — J-18 Single date selector (no pull/retry date state added)

**Type:** browser
**Preconditions:** 
- Frontend running with J-37 and J-38 panels visible
- `/data` page loaded

**Steps:**
1. Inspect the `/data` page for all `<select>` elements (or date-picker inputs)
2. Count the number of date selectors
3. Trigger a pull-missing job (J-37)
4. Verify the pull job is submitted without adding a second date state
5. Trigger a retry job (J-38)
6. Verify the retry is also submitted with job parameters, not a separate viewing-date control

**Expected outcome:** Exactly one date selector remains on the page; pull/retry/resume are job parameters, not date-state mutations

**Pass criteria:** 
```
# Browser DevTools inspection:
document.querySelectorAll('select, input[type="date"]').length === 1  # Exactly one date control

# Job submission:
curl -X POST http://localhost:8000/api/data/jobs/... | jq '.date_range'
# Must show: job has its own [start, end], not a page-level viewing date
```

---

### TC-16 — Backend unit/integration: J-37 diagnostic categories with exact shortfalls vs fixture

**Type:** artifact
**Preconditions:** 
- Test fixture with: no-history member, thin member, intra-series-gap member

**Steps:**
1. Run `pytest apps/backend/tests/test_data_manager.py::test_missing_data_diagnostic -xvs`
2. Verify the test passes with assertions on:
   - No-history member detected and shortfall calculated as "bars-have: 0, bars-needed: 30"
   - Thin member detected and shortfall as "bars-have: 5, bars-needed: 30"
   - Intra-series-gap member detected with gap dates and missing-day count
   - A fine member (30+ bars, no gaps) does NOT appear in the diagnostic
3. Verify `indicators.min_history_bars` threshold is read from config, not a literal number in the code

**Expected outcome:** All three diagnostic categories produce exact shortfalls; no magic numbers; fine member absent

**Pass criteria:** 
```
pytest apps/backend/tests/test_data_manager.py::test_missing_data_diagnostic -xvs
# Output must show: 3 detected categories, exact shortfall values, no recompute of scores/returns
```

---

### TC-17 — Backend unit: J-37 pull constructor gap-exact + idempotent + reuses J-34

**Type:** artifact
**Preconditions:** 
- Test fixture with diagnosed gap

**Steps:**
1. Run `pytest apps/backend/tests/test_data_manager.py::test_pull_missing_constructor -xvs`
2. Verify the test passes with assertions on:
   - Pull job's `symbols` == diagnosed shortfall symbols only (not whole universe)
   - Pull job's `[start, end]` == diagnosed shortfall date range only (not whole window)
   - Job is dispatched via `run_data_job` (EXISTING J-34 engine, not a new fetch path)
   - Fetching the same gap twice produces NO duplicate bars (per-`(symbol, date)` INSERT-new-only guard)
   - A provider error is surfaced as `resumable` / explicit error, no fabricated bar

**Expected outcome:** Pull constructor creates gap-exact, idempotent jobs over the EXISTING J-34 engine

**Pass criteria:** 
```
pytest apps/backend/tests/test_data_manager.py::test_pull_missing_constructor -xvs
# Output: symbols match shortfall, date range matches shortfall, reuses J-34, idempotent pass, error handling pass
```

---

### TC-18 — Backend unit: J-38 unfinished_imports union + state strings + Dismiss preserves audit

**Type:** artifact
**Preconditions:** 
- Test fixture with: resumable checkpoint, partial run, failed run, soft-dismissed run

**Steps:**
1. Run `pytest apps/backend/tests/test_data_manager.py::test_unfinished_imports_union -xvs`
2. Verify the test passes with assertions on:
   - Union includes resumable + partial + failed
   - Soft-dismissed runs are excluded from the list
   - Each row has plain-language state string (e.g., "Paused — ...", "Partial — X ok, Y failed")
   - State strings match expected descriptions
3. Run `pytest apps/backend/tests/test_data_manager.py::test_dismiss_preserves_audit -xvs`
4. Verify the test passes with assertions on:
   - Dismiss API deletes the `ImportCheckpoint` row OR sets `dismissed=True` on `DataProviderRun`
   - The `data_provider_runs` audit row is NOT deleted
   - No `daily_prices` / `scanner_runs` / `forward_returns` row is touched

**Expected outcome:** Unfinished-imports correctly surfaces all unfinished job-control states with plain-language text; Dismiss is audit-safe

**Pass criteria:** 
```
pytest apps/backend/tests/test_data_manager.py::test_unfinished_imports_union -xvs
pytest apps/backend/tests/test_data_manager.py::test_dismiss_preserves_audit -xvs
# Output: union/state-strings pass, audit row verified intact, no immutable rows touched
```

---

### TC-19 — Backend unit: test_db.py expected-tables set updated for new dismissed column

**Type:** artifact
**Preconditions:** 
- A new `dismissed: bool` column added to `DataProviderRun` model

**Steps:**
1. Run `pytest apps/backend/tests/test_db.py::test_expected_tables -xvs`
2. Verify the test passes (no AssertionError about missing tables)
3. If the test fails, verify that `tests/test_db.py:37` has been updated to include the new column in the expected-tables set

**Expected outcome:** test_db.py passes with all expected tables/columns accounted for

**Pass criteria:** 
```
pytest apps/backend/tests/test_db.py::test_expected_tables -xvs
# Output: PASSED (no AssertionError about missing/extra tables)
```

---

### TC-20 — Backend integration: full pytest suite passes (run once at QA gate)

**Type:** artifact
**Preconditions:** 
- All backend code changes in place
- Test database ready (fresh seed or fixture-loaded)

**Steps:**
1. Run the full backend test suite: `pytest apps/backend/tests/ -x`
2. Capture all output (pass/fail counts, any errors)
3. Note the total runtime (~14 minutes expected)

**Expected outcome:** All tests pass with no regressions

**Pass criteria:** 
```
pytest apps/backend/tests/ -x
# Output: all tests PASSED, no FAILED or ERROR, exit code 0
# Do NOT run this concurrently with another pytest invocation (MEMORY backend-test-suite-runtime)
```

---

### TC-21 — Frontend API types: MissingDataDiagnostic + UnfinishedImport on response

**Type:** artifact
**Preconditions:** 
- Frontend code built and type-checked

**Steps:**
1. Verify `apps/frontend/lib/api.ts` defines `MissingDataDiagnostic` type with fields: symbol, category, shortfall
2. Verify `apps/frontend/lib/api.ts` defines `UnfinishedImport` type with fields: id, state, symbols, progress
3. Verify `DataCoverage` type on the `GET /api/data` response includes `diagnostic: MissingDataDiagnostic[]` and `unfinished_imports: UnfinishedImport[]`
4. Run `npm run type-check` in `apps/frontend`

**Expected outcome:** TypeScript compilation succeeds; types match backend response shape

**Pass criteria:** 
```
cd apps/frontend && npm run type-check
# Output: no TS errors, exit code 0
```

---

### TC-22 — Environment setup: frontend dev server cleanly started and hydrated

**Type:** browser
**Preconditions:** 
- No existing `next dev` processes on port 3000
- `.next` directory cleaned (`rm -rf apps/frontend/.next`)

**Steps:**
1. Kill any stray Next.js processes by port: `lsof -i :3000` and `kill` by PID, or use `pkill -f "next dev.*3000"` (port-specific, not broad pkill)
2. Clean the dev cache: `rm -rf apps/frontend/.next`
3. Start the frontend: `cd apps/frontend && npm run dev`
4. Wait 10 seconds for build
5. Verify `GET http://localhost:3000/_next/static/chunks/main-app.js` returns 200
6. Open the browser to `http://localhost:3000` and check the health badge (should show "Online" or no "Checking backend…" message)

**Expected outcome:** Frontend dev server runs cleanly with no dead-shell symptoms

**Pass criteria:** 
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/_next/static/chunks/main-app.js
# Output: 200

curl -s http://localhost:3000 | grep -i "checking backend" || echo "PASS: no dead-shell"
```

---

## Summary

**Total test cases:** 22

| Category | Count |
|----------|-------|
| Browser tests | 8 (TC-01, TC-02-preview, TC-03, TC-04, TC-06, TC-10, TC-12, TC-13, TC-14, TC-15) |
| API tests | 6 (TC-02, TC-05, TC-07, TC-08, TC-09, TC-11) |
| Artifact/Unit tests | 6 (TC-16, TC-17, TC-18, TC-19, TC-20, TC-21) |
| Environment/Setup tests | 2 (TC-22, prerequisite for all browser tests) |

**Execution order:**
1. TC-22 (environment setup — prerequisite for all browser tests)
2. TC-20 (full backend suite — run once, blocks on long runtime)
3. TC-01 through TC-04 (J-37 missing-data diagnostic and pull-missing)
4. TC-05 (J-37 error handling)
5. TC-06 through TC-10 (J-38 unified unfinished-imports)
6. TC-11 (critical key-leak regression)
7. TC-12 through TC-14 (J-39 and J-35 captures)
8. TC-15 (J-18 regression: single date selector)
9. TC-16 through TC-21 (unit tests and type checks — can run in parallel with browser tests after TC-20)

**Critical assertions:**
- TC-02: Job symbols/range == diagnosed shortfall exactly (not universe-wide)
- TC-08: Retry idempotency (no duplicate bars in daily_prices)
- TC-09: Dismiss safety (audit row preserved, no immutable rows touched)
- TC-11: Key-leak regression (sentinel key absent from all responses)
- TC-18: Dismiss audit preservation (data_provider_runs row intact)
- TC-19: test_db.py expects new columns (if added)
