# Goal Iteration 23 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23  
**Date:** 2026-06-07  
**Frontend Present:** yes

## Phase Goal

Implement the **Expand-universe** job (J-35) that reads the committed 548-name candidate pool, applies the config-driven screen, fetches real OHLCV and market-cap reference via the existing chunked/resumable import, and grows the universe toward 400–500 members while surfacing per-candidate screening decisions (passers + omitted-with-reason), with ineligible sources (no market-cap capability) visibly disabled and the live outcome recorded honestly (NA / rate-limited) when the provider is walled.

---

## Test Cases

### TC-01 — Unknown job kind is rejected (422)

**Type:** api  
**Preconditions:** Backend service is running; no pre-existing job in the database.

**Steps:**
1. POST to `http://localhost:8000/api/data/jobs` with:
   ```json
   {
     "kind": "invalid_kind",
     "source": "yahoo",
     "start_date": "2025-01-01",
     "end_date": "2025-01-31"
   }
   ```

**Expected outcome:** HTTP 422 Unprocessable Entity; error message indicates kind is invalid.  
**Pass criteria:** Status code is 422; response body contains error details for invalid job kind.

---

### TC-02 — Expand job over unsupported source is rejected (422)

**Type:** api  
**Preconditions:** Backend service running; alpha_vantage and stooq have `supports_market_cap: false` in config.

**Steps:**
1. POST to `http://localhost:8000/api/data/jobs` with:
   ```json
   {
     "kind": "expand",
     "source": "alpha_vantage",
     "start_date": "2025-01-01",
     "end_date": "2025-01-31"
   }
   ```

**Expected outcome:** HTTP 422 Unprocessable Entity with explicit error message indicating source does not support market cap.  
**Pass criteria:** Status code is 422; response contains "supports_market_cap" or "market cap" in error text; request is rejected at API layer.

---

### TC-03 — Expand job over unsupported source is rejected (engine layer)

**Type:** api  
**Preconditions:** Backend service running; API validation passes (mocked); engine receives expand request with stooq source.

**Steps:**
1. Inject a mock HTTP layer that bypasses API validation and calls the engine's `_run_job` directly with:
   - `kind="expand"`, `source="stooq"`, `supports_market_cap=False`
2. Verify the engine rejects it before attempting any fetch.

**Expected outcome:** Engine raises `ValueError` with explicit message indicating market-cap support requirement; job marked failed without attempting fetch or writing artifacts.  
**Pass criteria:** Engine rejects request immediately; no DailyPrice rows inserted; no universe.json modified; error is logged with clear message.

---

### TC-04 — Expand job kind is accepted (valid source)

**Type:** api  
**Preconditions:** Backend service running; yahoo (or tiingo/finnhub) has `supports_market_cap: true` in config.

**Steps:**
1. POST to `http://localhost:8000/api/data/jobs` with:
   ```json
   {
     "kind": "expand",
     "source": "yahoo",
     "start_date": "2025-01-01",
     "end_date": "2025-01-31"
   }
   ```

**Expected outcome:** HTTP 201 Created; response includes job_id, kind="expand", status="running" or similar initial state.  
**Pass criteria:** Status code is 201; `kind` in response is exactly "expand"; job_id is a valid UUID/string; status is one of the valid job states (running, completed, resumable, failed).

---

### TC-05 — Expand job progress includes chunked-fetch metadata (job status endpoint)

**Type:** api  
**Preconditions:** Backend running with a live/injected expand job in progress; at least one chunk has been processed.

**Steps:**
1. GET `http://localhost:8000/api/data/jobs/{job_id}` (replace job_id with the expand job from TC-04 or a mock job).
2. Parse the response JSON.

**Expected outcome:** Response includes `chunk_progress` (e.g., `{"current_chunk": 2, "total_chunks": 5}`), `passers` count, and `omitted` list with objects containing `{symbol, reason}`.  
**Pass criteria:** Response contains `chunk_progress` with numeric `current_chunk` and `total_chunks`; `passers` is a non-negative integer; `omitted` is a list (possibly empty) where each element has `symbol` (string) and `reason` (string).

---

### TC-06 — Expand job omitted-with-reason records all failure types

**Type:** api  
**Preconditions:** Expand job completed with an injected provider that returns partial data (some symbols missing bars, some lacking market cap, some failing entirely).

**Steps:**
1. Start an expand job with an injected provider that:
   - Returns bars + market cap for symbols A, B, C.
   - Returns bars but NO market cap for symbol D.
   - Raises HTTPError for symbol E.
   - Returns empty series for symbol F.
2. Wait for job completion (or mock completion).
3. GET `http://localhost:8000/api/data/jobs/{job_id}`.

**Expected outcome:** Response `omitted` list includes:
   - `{symbol: "D", reason: "no_market_cap"}`
   - `{symbol: "E", reason: "fetch_failed"}` (or similar)
   - `{symbol: "F", reason: "no_data"}` or `"empty_series"` (or similar)

**Pass criteria:** All three failure types are recorded with distinct, plain-language reason strings; no fabricated market-cap value appears for D; no symbol without a reason is silently omitted.

---

### TC-07 — Expand job writes universe.json with passers only

**Type:** artifact  
**Preconditions:** Expand job completed successfully with injected provider returning bars + market cap for 10 symbols (all meeting screen thresholds).

**Steps:**
1. Start expand job with injected provider.
2. Wait for completion.
3. Read `apps/backend/data/seed/universe.json`.
4. Parse JSON and verify structure.

**Expected outcome:** universe.json contains exactly 10 member objects, each with required fields: `symbol`, `sector`, `source`, `market_cap`, `reference_close`, `adv_dollar`, `bars`, `first`, `last`.  
**Pass criteria:** File exists and is valid JSON; member count matches expected passers; no symbol from the failed/omitted set (D, E, F from TC-06) appears; all fields are present and non-null; no duplicate symbols.

---

### TC-08 — Expand job applies screen_reasons predicate (single source)

**Type:** api  
**Preconditions:** Injected provider returning bars + market cap for test pool (K symbols total); exact thresholds known from config.

**Steps:**
1. Configure an injected provider with known OHLCV + market-cap values for K test symbols.
2. Run expand job.
3. For each symbol, independently call `screen_universe.screen_reasons(reference_close, adv_dollar, market_cap, config.universe.filters)`.
4. Compare engine's omitted list + passers to the independent predicate results.

**Expected outcome:** Engine's pass/omit decision for each symbol exactly matches the independent predicate for the same input values.  
**Pass criteria:** All K symbols' decisions match; no discrepancy; assert that the engine imports the SAME `screen_reasons` function (not a reimplementation).

---

### TC-09 — Expand job does not insert duplicate DailyPrice rows (idempotency)

**Type:** artifact  
**Preconditions:** Backend with DailyPrice table and seed data; expand job completed once with injected provider.

**Steps:**
1. Note the current row count in `DailyPrice` table (e.g., N rows).
2. Run the same expand job again (same symbols, same date range, same injected provider).
3. Query `DailyPrice` table again.

**Expected outcome:** New row count = N (no new rows inserted for bars already in the table).  
**Pass criteria:** Row count is identical before and after second run; no duplicate date entries for the same symbol; INSERT-new-only guard is respected.

---

### TC-10 — Expand job does not mutate immutable snapshots (no scanner_runs regen)

**Type:** artifact  
**Preconditions:** Database with pre-existing scanner_runs, scanner_results, *_scores, forward_returns rows; expand job completed.

**Steps:**
1. Query counts: `SELECT COUNT(*) FROM scanner_runs; SELECT COUNT(*) FROM scanner_results; SELECT COUNT(*) FROM *_scores; SELECT COUNT(*) FROM forward_returns;`
2. Run expand job.
3. Query counts again.

**Expected outcome:** All counts are identical; no new rows in scanner_runs, scanner_results, or *_scores; forward_returns unchanged.  
**Pass criteria:** Row counts match exactly; no DB regen occurred; expand writes only DailyPrice and universe.json.

---

### TC-11 — Expand job records DataProviderRun audit entry

**Type:** artifact  
**Preconditions:** Expand job completed; DataProviderRun audit table exists.

**Steps:**
1. Query `SELECT * FROM DataProviderRun WHERE job_id = '<expand-job-id>' AND kind = 'expand';`

**Expected outcome:** One row exists with:
   - `kind = "expand"`
   - `job_id` matching the completed expand job
   - `source` set to the provider used
   - Timestamps recorded (start, end)

**Pass criteria:** Exactly one audit row; all required fields are non-null; timestamps are in correct order (start < end).

---

### TC-12 — Config validation rejects missing required expand fields

**Type:** artifact  
**Preconditions:** Backend config loading; config.universe.filters and config.data_manager.import_chunking are required.

**Steps:**
1. Load config with `config.universe.filters` missing.
2. Attempt to instantiate DataManager.
3. Try again with `config.data_manager.import_chunking` missing.

**Expected outcome:** ConfigError raised immediately at boot for each missing field; expand job cannot be created without valid config.  
**Pass criteria:** Error message clearly indicates the missing field; no silent default fallback; config validation extends to expand requirements.

---

### TC-13 — Browser: Expand job kind appears in job-kind selector

**Type:** browser  
**Preconditions:** Frontend running on http://localhost:3000; backend running; user on `/data` page.

**Steps:**
1. Navigate to http://localhost:3000/data.
2. Locate the JobForm job-kind `<select>` control.
3. Click the dropdown.
4. Inspect options.

**Expected outcome:** Options include "fetch", "backfill", "both", and **"expand"**.  
**Pass criteria:** "expand" appears in the dropdown; can be selected (no validation error on selection).

---

### TC-14 — Browser: Ineligible sources are disabled with reason (Expand selected)

**Type:** browser  
**Preconditions:** Frontend running; backend serving source catalog with `supports_market_cap` field; user on `/data` page with Expand kind selected.

**Steps:**
1. Navigate to http://localhost:3000/data.
2. Select job-kind = "expand".
3. Locate the source `<select>` control.
4. Click dropdown and inspect options for alpha_vantage and stooq.

**Expected outcome:** alpha_vantage and stooq options are visibly **disabled** (grayed out, cursor: not-allowed, or similar); a reason string appears near or in the option (e.g., "cannot supply market cap — not selectable for expand").  
**Pass criteria:** Disabled state is CSS-enforced (`disabled` attribute or `:disabled` styling); user cannot select the option (click does not change selected value); reason text is readable inline.

---

### TC-15 — Browser: Eligible sources are enabled (Expand selected)

**Type:** browser  
**Preconditions:** Frontend running; yahoo/tiingo/finnhub configured with `supports_market_cap: true`; user on `/data` page with Expand kind selected.

**Steps:**
1. Navigate to http://localhost:3000/data.
2. Select job-kind = "expand".
3. Inspect the source `<select>` options.

**Expected outcome:** yahoo (and tiingo/finnhub if available) are **enabled** (normal appearance, not grayed).  
**Pass criteria:** Can be clicked and selected without error; selecting and clicking Start Job does not show a validation error about market cap.

---

### TC-16 — Browser: Expand job shows chunked progress (chunk x/N badge)

**Type:** browser  
**Preconditions:** Frontend running; backend running expand job with injected provider; user on `/data` page watching the job.

**Steps:**
1. Start an expand job via the form (Expand kind, eligible source, valid date range).
2. Watch the job card in real-time as chunks process.
3. Verify the progress badge updates.

**Expected outcome:** Job card shows a badge or label with text like "Chunk 2/5" or "Processing chunk 2 of 5" as chunks are processed.  
**Pass criteria:** Badge appears; text updates in real-time as chunks complete; final chunk shows "Chunk N/N" (e.g., "Chunk 5/5") when all chunks are done.

---

### TC-17 — Browser: Expand job shows passers count

**Type:** browser  
**Preconditions:** Expand job completed with injected provider; 10 passers expected; user on `/data` page.

**Steps:**
1. Locate the job card for the completed expand job.
2. Inspect for a "Passers" count or label.

**Expected outcome:** Card displays "Passers: 10" or similar label with the exact count.  
**Pass criteria:** Passers count is visible and matches the expected number of symbols that passed the screen; count is non-zero if any symbols passed.

---

### TC-18 — Browser: Expand job shows omitted-with-reason list

**Type:** browser  
**Preconditions:** Expand job completed with omissions (e.g., 4 symbols omitted from TC-06: D no_market_cap, E fetch_failed, F no_data, G below_threshold); user on `/data` page.

**Steps:**
1. Locate the job card for the completed expand job.
2. Scroll or look for an "Omitted" section, table, or list.
3. Inspect each entry for symbol and reason.

**Expected outcome:** List shows all 4 omitted candidates with their reasons:
   - D: "no_market_cap"
   - E: "fetch_failed"
   - F: "no_data"
   - G: "below_threshold" (or similar matching the screen rule)

**Pass criteria:** All omitted symbols are listed; reasons match the actual omission type from TC-06; list is readable (plain-language, not error codes); each entry clearly shows symbol + reason.

---

### TC-19 — Browser: Coverage universe-count reflects grown universe (J-22 invariant)

**Type:** browser  
**Preconditions:** Expand job completed with 10 passers; user on `/data` page; Coverage panel is visible.

**Steps:**
1. Locate the Coverage panel on the `/data` page.
2. Find the `universe-count` field (should have `data-testid="universe-count"`).
3. Record the displayed count.
4. Navigate to http://localhost:3000/methodology.
5. Locate the "Universe-Selection" section showing the resolved universe size.
6. Record the count.

**Expected outcome:** Both counts are equal (both = 10 in this test case) and match the number of symbols in `universe.json` from TC-07 and `len(config.universe.symbols)` after the expand.  
**Pass criteria:** Coverage `universe-count` == /methodology resolved size == len(config.universe.symbols) == passers written to universe.json (single source, all read the same value).

---

### TC-20 — Browser: Resume button works for rate-limited expand (J-34 reuse)

**Type:** browser  
**Preconditions:** Expand job started and stopped in resumable state (via injected provider returning RateLimitError mid-way); user on `/data` page.

**Steps:**
1. Start an expand job and let it reach resumable state (chunk 3/5 processed, then rate-limited).
2. Observe the job card displays a "Resume" button.
3. Click Resume.
4. Watch the job continue from chunk 4.

**Expected outcome:** Job resumes from the checkpoint (does not restart from chunk 1); continues processing remaining chunks; eventually completes.  
**Pass criteria:** Job state changes from "resumable" to "running"; chunks 4–5 are processed (no re-processing of chunks 1–3); final status is "completed"; no errors for resuming.

---

### TC-21 — Browser: J-18 Confirm exactly one date selector per page (expand adds no date state)

**Type:** browser  
**Preconditions:** Frontend running; user on `/data` page with Expand job form visible.

**Steps:**
1. Inspect the `/data` page DOM for `<select>` elements with role or class indicating a date picker.
2. Count date-related selectors (should be exactly one — the global as-of date selector).
3. Expand the job-kind selector and review all available job types (fetch, backfill, both, expand).
4. For each job type, verify that no additional date-state controls appear.

**Expected outcome:** Exactly **one** date selector on the page (the global as-of switcher); the expand job form introduces no new date field.  
**Pass criteria:** Only one date control is present; selecting Expand kind does not reveal a second date picker; start_date/end_date are job parameters (form inputs), not a persistent date state like the global as-of.

---

### TC-22 — Browser: J-17 Verify fetch/backfill/both still work unchanged (regression)

**Type:** browser  
**Preconditions:** Frontend running; backend running; user on `/data` page.

**Steps:**
1. Select job-kind = "fetch".
2. Select a source (yahoo).
3. Fill in start_date and end_date.
4. Click Start Job.
5. Verify the job runs (chunk progress, completion).
6. Repeat for job-kind = "backfill" and "both".

**Expected outcome:** All three original job kinds (fetch, backfill, both) run successfully without regression.  
**Pass criteria:** Each job completes; chunk progress is shown; final status is "completed"; no new errors introduced by expand code changes.

---

### TC-23 — Browser: Key safety — expand path does not echo or log session keys

**Type:** browser  
**Preconditions:** Backend running with a key-requiring source (e.g., needs an API key); user on `/data` page; dev tools console/network tab open.

**Steps:**
1. Select Expand kind and a needs-key source (mock one if necessary with an injected provider that requires a key parameter).
2. Paste a test key into the key-entry field (if visible, or it comes from env).
3. Start the expand job.
4. Inspect the job status response (`GET /api/data/jobs/{job_id}`) for any occurrence of the test key.
5. Check the browser console for any logged messages containing the key.
6. Check the network tab for any GET/POST requests with the key in the URL.

**Expected outcome:** Test key does not appear in any response body, console logs, or request URLs; only the job status and omitted/passers data are visible.  
**Pass criteria:** Key is not echoed back; no key appears in error messages (omitted reasons, fetch_failed reasons); `GET /api/data/jobs/{id}` response is clean (no URL query params with keys); test key is forgotten after the request.

---

### TC-24 — Backend: Pool CSV is read correctly (expand reads 548 symbols)

**Type:** artifact  
**Preconditions:** Pool file exists at `apps/backend/data/seed/universe_pool.csv` with 548 rows of symbols.

**Steps:**
1. Count lines in `universe_pool.csv` (excluding header).
2. Mock an expand job that reads the pool.
3. Verify the symbol list matches.

**Expected outcome:** Expand job reads exactly 548 symbols from the pool; all symbols are valid (non-empty strings).  
**Pass criteria:** Symbol count = 548; no duplicates in the input pool; expand starts with all 548 candidates before screening.

---

### TC-25 — Backend: expand reuses _chunk_plan and _run_chunked_fetch (no fork)

**Type:** api  
**Preconditions:** Backend source code analyzed; expand implementation reviewed.

**Steps:**
1. Search `app/engine/data_manager.py` for `_run_job` expand branch.
2. Verify the expand branch calls `_chunk_plan(...)` and `_run_chunked_fetch(...)`.
3. Confirm no parallel `_expand_chunk_plan` or `_expand_chunked_fetch` functions exist.

**Expected outcome:** The expand branch reuses the existing chunked-fetch machinery (same functions as J-17/J-34); no fork or duplicate implementation.  
**Pass criteria:** `_chunk_plan` is called exactly once for expand; `_run_chunked_fetch` is used (not redefined); code review confirms no parallel chunking logic.

---

### TC-26 — Backend: Test suite includes expand happy path

**Type:** artifact  
**Preconditions:** Test file `tests/test_data_manager.py` exists; expand tests are written.

**Steps:**
1. Run `pytest tests/test_data_manager.py::test_expand_happy_path -v` (or equivalent test name).

**Expected outcome:** Test runs and passes; it verifies:
   - Expand job is created (kind="expand").
   - Job reads the pool (548 symbols).
   - Injected provider returns bars + market cap for K symbols.
   - Screen is applied (passers and omitted are computed).
   - universe.json is written with correct passers.
   - Omitted-with-reason list matches expected failures.

**Pass criteria:** Test passes; assertions verify member set and omission reasons by value (exact match).

---

### TC-27 — Backend: Test suite covers eligibility gate (both API and engine)

**Type:** artifact  
**Preconditions:** Test files `tests/test_api_data.py` and `tests/test_data_manager.py` include eligibility tests.

**Steps:**
1. Run `pytest tests/test_api_data.py -k expand -v` to find expand-related tests.
2. Run the test(s) that verify API-layer rejection of unsupported sources.
3. Run `pytest tests/test_data_manager.py -k "expand.*eligibility" -v` for engine-layer test.

**Expected outcome:** Both tests pass:
   - API test: POST with expand + alpha_vantage returns 422.
   - Engine test: `_run_job` with expand + stooq raises ValueError.

**Pass criteria:** Both tests exist and pass; API returns correct status code; engine raises the correct exception type; no silent no-ops.

---

### TC-28 — Backend: Config validation covers expand requirements

**Type:** artifact  
**Preconditions:** Test file `tests/test_config.py` includes validation for expand-related fields.

**Steps:**
1. Run `pytest tests/test_config.py -v` to verify all config tests pass.
2. Verify that `config.universe.filters` (min_market_cap, min_dollar_vol, min_price) is validated.
3. Verify that `config.data_manager.import_chunking` (symbol_batch_size, chunk_sleep_sec) is validated.
4. Attempt to load a config with missing values and confirm ConfigError is raised.

**Expected outcome:** All config tests pass; missing required fields are caught at boot.  
**Pass criteria:** No ConfigError in normal load; ConfigError is raised for missing fields; error message is clear.

---

### TC-29 — Backend: Test fixtures include expand config

**Type:** artifact  
**Preconditions:** Test config fixtures exist in `tests/test_config.py`, `tests/test_config_engine.py`, `tests/test_sectors.py`, `tests/test_themes.py`.

**Steps:**
1. Inspect all 4 inline config fixtures (MINIMAL_VALID, VALID, test_sectors, test_themes).
2. Verify each includes:
   - `universe.filters` with min_market_cap, min_dollar_vol, min_price.
   - `data_manager.import_chunking` with symbol_batch_size, chunk_sleep_sec.

**Expected outcome:** All 4 fixtures are complete; no missing required keys.  
**Pass criteria:** Each fixture has all required fields; tests that use these fixtures do not raise ConfigError for missing keys.

---

### TC-30 — Backend: test_db.py expected-tables fix includes import_checkpoints

**Type:** artifact  
**Preconditions:** Test file `tests/test_db.py` includes `test_create_all_produces_expected_tables`.

**Steps:**
1. Run `pytest tests/test_db.py::test_create_all_produces_expected_tables -v`.

**Expected outcome:** Test passes; `import_checkpoints` is in the expected-tables set.  
**Pass criteria:** Test is green (no assertion failure); the fix is a one-liner: expected tables includes `'import_checkpoints'`.

---

### TC-31 — Backend: Single screen-reason source assertion (engine reuses script predicate)

**Type:** artifact  
**Preconditions:** Engine code and test code both import `screen_reasons`; test file includes a comparison assertion.

**Steps:**
1. Inspect `tests/test_data_manager.py` for expand test that applies the screen.
2. Find the assertion that compares engine's decision to the standalone predicate result.
3. Verify that the import path is the SAME for both (both use `from scripts.screen_universe import screen_reasons`).

**Expected outcome:** One import path; both engine and test use the exact same `screen_reasons` function.  
**Pass criteria:** No duplicate definitions of `screen_reasons` in the codebase (grep confirms only one); test assertion passes (engine decision matches predicate output).

---

## Summary

**Total test cases:** 31
- **API tests:** 7 (TC-01 through TC-06, TC-11)
- **Browser tests:** 9 (TC-13 through TC-23)
- **Artifact checks:** 15 (TC-07 through TC-10, TC-12, TC-24 through TC-31)

**Coverage:**
- **Backend acceptance criteria:** expand job kind, eligibility gate (API + engine), chunked/resumable reuse, screen_reason single source, no fabrication, idempotency, omitted-with-reason recording, universe.json write, DataProviderRun audit, config validation, test DB fix.
- **Frontend acceptance criteria:** Expand option in job-kind selector, source eligibility disabling with reason, progress + passers + omitted display, Resume button, J-18 (single date selector), J-17 (regression), J-22 (single-source universe count), key safety.
- **Integration:** Single source for screen rule, universe count read from correct source, immutable snapshots untouched, no DB regen.
- **Error cases:** Unknown job kind 422, expand on unsupported source 422, no fabrication on fetch failure, graceful resumable state on rate-limit.

All test cases are offline-provable using injected providers (except where noted as data-gated); the live market-cap expansion outcome is non-halting and recorded honestly (NA / rate-limited), not a test failure.
