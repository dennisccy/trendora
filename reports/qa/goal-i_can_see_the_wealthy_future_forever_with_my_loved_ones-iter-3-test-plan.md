# Goal Iteration 3 (J-46) Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3
**Date:** 2026-06-11
**Frontend Present:** yes

## Phase Goal

Parallelize multi-symbol fetch jobs on a bounded worker pool (config-set `fetch_workers`), commit bar writes per-chunk in a single transaction, and load bars once per symbol for entire backfill jobs via an in-memory cache—measurably faster while preserving byte-identical canonical outputs, immutable snapshots, and strict no-lookahead invariants.

## Test Cases

### TC-01 — Config key `fetch_workers` boot validation

**Type:** api
**Preconditions:** Backend service not running; `config.yaml` contains `data_manager.import_chunking` block.

**Steps:**
1. Set `data_manager.import_chunking.fetch_workers: 0` in `config.yaml` and start the backend with `bash scripts/start-backend.sh`.
2. Observe the boot sequence and check for an explicit error message.
3. Repeat with `fetch_workers: -1`.
4. Repeat with `fetch_workers: 1` (valid).
5. Repeat with `fetch_workers: 4` (valid).

**Expected outcome:** Boot fails immediately with `ConfigError` for 0 or negative; boots successfully and accepts API requests for 1 or 4.
**Pass criteria:** Stderr during boot contains `ConfigError` mentioning `fetch_workers` for invalid values; backend is listening on port 8835 after valid config values and responds `200 OK` to `GET http://localhost:8835/health`.

---

### TC-02 — Config fixture coverage — all five test dicts contain `fetch_workers`

**Type:** artifact
**Preconditions:** Source files exist: `tests/test_config.py`, `tests/test_config_engine.py`, `tests/test_sectors.py`, `tests/test_themes.py`, `tests/test_indexes.py`.

**Steps:**
1. Read each of the five test files and locate inline config dicts (`MINIMAL_VALID`, `VALID`, `_SYNTH_CFG`, test config blocks, etc.).
2. For each dict, verify the presence of `data_manager.import_chunking.fetch_workers` with a value ≥ 1.

**Expected outcome:** All five dicts contain the `fetch_workers` field with valid values.
**Pass criteria:** `grep -n "fetch_workers" tests/test_config.py tests/test_config_engine.py tests/test_sectors.py tests/test_themes.py tests/test_indexes.py` returns 5+ matches (at least one per file).

---

### TC-03 — Parallel bounded fetch—max concurrent workers ≤ `fetch_workers`

**Type:** api
**Preconditions:** Backend running; test suite has a stub provider spy that instruments concurrent worker calls; `config.yaml` has `fetch_workers: 2`; a multi-symbol chunk is ready to fetch.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_data_manager.py::test_parallel_fetch_bounded_workers -v` (or equivalent test with concurrency instrumentation).
2. Capture the test output and the instrumentation log showing concurrent in-flight calls.

**Expected outcome:** The test passes; instrumentation log shows no more than 2 concurrent fetch calls in flight at any instant.
**Pass criteria:** Pytest exit code 0; instrumentation data in test output or log file shows `max_concurrent ≤ 2`.

---

### TC-04 — Per-chunk single-transaction commit

**Type:** api
**Preconditions:** Backend running; test suite has commit-count instrumentation or row-state checks; a multi-symbol chunk fetch is triggered with an injected stub provider that returns bars successfully for the entire chunk.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_data_manager.py::test_per_chunk_single_commit -v`.
2. Capture the test output and verify the commit count or the state of `daily_prices` rows before/after.

**Expected outcome:** For a chunk of N symbols, exactly one `commit()` is issued (not N per-symbol commits); all N symbols' bars are durably written atomically.
**Pass criteria:** Pytest exit code 0; test asserts `commit_count == 1 per chunk` or equivalent row-consistency check passes.

---

### TC-05 — Mid-chunk 429 pauses resumable with chunk-consistent checkpoint

**Type:** api
**Preconditions:** Backend running; test suite has an injected stub provider that returns bars for the first symbol, then raises `RateLimitError` (429) on the second symbol of a 3-symbol chunk; the checkpoint table is empty (no prior job state).

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_data_manager.py::test_mid_chunk_429_resumable -v`.
2. Capture job status via `GET /api/data/jobs/{id}`.
3. Verify the job state, checkpoint `next_chunk_index`, progress counters, and `resumable` flag.
4. Resume the job via `POST /api/data/jobs/{id}/resume`.
5. Verify that the second attempt fetches all 3 symbols again (or fetches only the 2nd and 3rd if the 1st is idempotent-skipped) with zero duplicate `(symbol, date)` rows in the database.

**Expected outcome:** Job pauses with `resumable=true`, `next_chunk_index` points to the unfinished chunk, progress counts are ≤ totals, Resume continues from the checkpoint and completes the chunk without duplicating the 1st symbol's bars.
**Pass criteria:** Pytest exit code 0; job status `state=resumable`; checkpoint `next_chunk_index` matches the interrupted chunk number; `daily_prices` row count after Resume is consistent with idempotent fetch (no duplicates).

---

### TC-06 — Non-429 provider error counts as failed, not resumable

**Type:** api
**Preconditions:** Backend running; test suite has an injected stub provider that returns bars for the first symbol, then raises `ProviderUnavailableError` on the second symbol of a 3-symbol chunk.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_data_manager.py::test_non_429_error_continues_chunk -v`.
2. Capture job status via `GET /api/data/jobs/{id}`.
3. Inspect the job's `errors[]` array and the `failed_symbols` or `failed_count`.

**Expected outcome:** The chunk continues; the second symbol is marked failed with a scrubbed error message; the chunk completes with a mixed result (1 successful, 1 failed, 1 successful).
**Pass criteria:** Pytest exit code 0; job status shows `failed_count >= 1`; `errors[]` array exists but contains no API key substring (e.g., `?apikey=` is absent).

---

### TC-07 — Worker exception does not deadlock pool or strand job in running

**Type:** api
**Preconditions:** Backend running; test suite has an injected stub provider that raises an unexpected exception (e.g., `ValueError` or `socket.timeout`) in a worker thread; the main orchestrating thread is instrumented to detect deadlock/hang.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_data_manager.py::test_worker_exception_no_deadlock -v --timeout=30`.
2. Capture the job state and thread status.

**Expected outcome:** The job completes within the timeout (never hangs); the pool is drained and all workers are joined before the job thread returns; the job state is one of `ok`, `failed`, or `resumable`, never stuck in `running`.
**Pass criteria:** Pytest exit code 0; test completes in < 30 seconds; no threads left alive after test cleanup.

---

### TC-08 — Load-bars-once bar cache—≤ 1 load per symbol for K-date backfill

**Type:** api
**Preconditions:** Backend running; test suite has instrumentation at the `prices.bars_asof` load point; a K-date (K ≥ 3) backfill is performed over seeded symbols using the bar cache.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_bar_cache.py::test_load_count_instrumented_backfill -v`.
2. Capture the load-count instrumentation for each symbol.

**Expected outcome:** For a 3-symbol, 3-date backfill, each symbol's bar series is loaded exactly once; all subsequent `bars_asof(symbol, D)` calls within the job hit the in-memory cache.
**Pass criteria:** Pytest exit code 0; instrumentation data shows `loads_per_symbol == {symbol_1: 1, symbol_2: 1, symbol_3: 1}` (or similar counts proving ≤ 1 per symbol for the entire job).

---

### TC-09 — Cached vs uncached snapshot equality

**Type:** api
**Preconditions:** Backend running; test suite has two snapshot generation paths: one with the bar cache active, one without; a sample date is selected from the seeded history.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_bar_cache.py::test_cached_uncached_snapshot_equality -v`.
2. Capture the two snapshot objects (or their JSON representation) for the sample date.

**Expected outcome:** The two snapshots are row-level identical: all canonical scores, buckets, regime labels, and forward-return records match exactly.
**Pass criteria:** Pytest exit code 0; assertion compares the two snapshot dicts/rows and reports 100% equality (or 0 differences).

---

### TC-10 — Existing scanner/scoring/forward-testing suites pass unchanged

**Type:** api
**Preconditions:** Backend running; test files exist: `tests/test_scanner.py`, `tests/test_scoring.py`, `tests/test_forward_returns.py`, and similar immutability/no-lookahead tests.

**Steps:**
1. Run the full backend test suite: `cd apps/backend && python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/backend_tests.log`.
2. Allow the full suite to complete (budget ~46 minutes).
3. Extract the final summary line from the log.

**Expected outcome:** All existing tests pass with zero regressions; the summary line reports the recorded baseline: 659 passed / 4 skipped / 0 failed.
**Pass criteria:** Pytest exit code 0; no new failures introduced; `passed ≥ 659, skipped = 4, failed = 0` or unchanged counts (the recorded green run for this iteration).

---

### TC-11 — Benchmark script runs offline end-to-end

**Type:** artifact
**Preconditions:** Script file exists: `apps/backend/scripts/benchmark_pipeline.py`; the script uses only the offline `seed_import` provider (no network, no API keys); the seeded dataset is present in the database.

**Steps:**
1. Run `cd apps/backend && python scripts/benchmark_pipeline.py --format=text 2>&1 | tee /tmp/benchmark_output.txt`.
2. Inspect the output for a stage-timing table and per-stage duration rows (fetch serial vs pool, scan cached vs uncached, forward returns).
3. Repeat with `--format=json` and verify JSON output structure.

**Expected outcome:** Script completes without errors; output contains a table or JSON object with stage-timing data (e.g., `{"fetch_serial": X, "fetch_parallel_4workers": Y, "scan_uncached": Z, ...}` in seconds).
**Pass criteria:** Exit code 0; output contains at least 3 stage-timing entries (fetch, scan, forward-returns); times are positive floats; script makes no network calls (inspect with `strace` or similar if needed).

---

### TC-12 — Browser J-46 step 1–2: live progress accurate during parallel fetch

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running at http://localhost:8835; `/data` page is accessible; the test uses the **alpha_vantage** provider with key `demo` (known to throttle and trigger 429 in ~3 minutes).

**Steps:**
1. Navigate to http://localhost:3000/data in Chrome.
2. Start a new fetch job with symbol batch, source=alpha_vantage, key=demo.
3. Monitor the live progress display (symbol count, bar count, elapsed time).
4. Record screenshots of the progress state at 30-second intervals.
5. Wait for the job to pause with a **rate-limited — resumable** state (should occur in ~3 minutes).
6. Verify progress counters (symbols_fetched, bars_fetched) do not exceed totals at any point.
7. Click Resume and monitor the resume phase.
8. Wait for the job to complete (or pause again if multi-page throttling occurs).

**Expected outcome:** Live progress displays update continuously; symbol and bar counts never exceed the job's total; the resumable pause occurs with accurate state; Resume continues and completes without duplicate bars for already-fetched symbols.
**Pass criteria:** All progress counts ≤ totals throughout; screenshots show coherent progression; job completion summary shows accurate totals (no duplication); backend logs show workers joined and no dangling threads.

---

### TC-13 — Browser J-17 regression: backfill-only async job to `ok` summary

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running at http://localhost:8835; `/data` page is accessible; seed data is loaded; no network fetch required (backfill-only, offline mode).

**Steps:**
1. Navigate to http://localhost:3000/data.
2. Start a small backfill job (3–5 dates, 1–2 symbols from the seed, offline mode).
3. Monitor the live progress and job state.
4. Wait for the job to complete with an `ok` summary.
5. Verify the job summary shows correct symbol count, bar count, and no errors.

**Expected outcome:** Backfill job runs async with live progress; completes with `state=ok` and accurate summary.
**Pass criteria:** Job summary displayed correctly; symbol and bar counts match seeded data; no error messages in the job card.

---

### TC-14 — Browser J-06 spot check: NVDA scores identical on `/stocks` and `/stocks/NVDA`

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running at http://localhost:8835; NVDA is present in the seed dataset; both pages are accessible.

**Steps:**
1. Navigate to http://localhost:3000/stocks in Chrome.
2. Locate the NVDA row and record its Leadership Score, Entry Quality Score, Risk Score, and bucket (A–E).
3. Click on the NVDA row to navigate to http://localhost:3000/stocks/NVDA.
4. Record the same three scores and bucket from the detail page.
5. Compare the recorded values.

**Expected outcome:** All three scores and the A–E bucket are identical on both pages.
**Pass criteria:** Leadership/Entry Quality/Risk scores match to the displayed decimal precision; A–E bucket label matches exactly.

---

### TC-15 — Browser dead shell detection (regression guard)

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; `.next` folder may be stale due to prior prod build.

**Steps:**
1. Navigate to http://localhost:3000/data.
2. Observe the page DOM and network requests.
3. If the page shows "Checking backend…" and network tab shows 404 on `_next/static/chunks/main-app.js`, note the stale `.next` cache.

**Expected outcome:** Either the page loads normally (no dead shell), or it shows the dead-shell symptom.
**Pass criteria:** If dead shell is observed, record the test as **SKIPPED** with a note "stale .next cache — .next folder should be cleared before running browser QA" (not a FAIL).

---

## Summary

| Test Type | Count |
|-----------|-------|
| API tests | 11 (TC-01 through TC-11) |
| Browser tests | 4 (TC-12 through TC-15) |
| **Total** | **15** |

**Key validations:**
- Config validation and fixture coverage (2 tests: boot validation for 0/negative/missing, all five test dicts contain `fetch_workers`)
- Parallel worker pool correctness (3 tests: bounded concurrency ≤ `fetch_workers`, per-chunk single commit, exception non-deadlock)
- Resumable semantics under parallelism (2 tests: mid-chunk 429 ⇒ resumable with chunk-consistent checkpoint, non-429 error ⇒ failed count with scrubbed message)
- Bar-cache load efficiency (2 tests: load-count instrumentation ≤ 1/symbol for K-date backfill, cached-vs-uncached snapshot row-level equality)
- Existing test suite regression (1 test: full pytest run 659 passed / 4 skipped / 0 failed, ~46 min)
- Benchmark script offline execution (1 test: per-stage timing table, no network)
- Browser regression (4 tests: J-46 live progress accuracy + resume, J-17 backfill async, J-06 NVDA score identity, dead-shell guard)

All tests are designed to verify the phase's critical invariants: bounded parallelism, chunk-consistent checkpoints, immutable snapshots, no lookahead, idempotent resume, and measurably faster execution with byte-identical outputs.
