# goal-ops-hardening-iter-2 Functional Test Plan

**Phase:** goal-ops-hardening-iter-2
**Date:** 2026-07-19
**Frontend Present:** yes

## Phase Goal

Build persistent coverage_snapshot table and ingest-finalize hooks so `/data` and all reader pages serve heavy aggregates instantly from storage (never recomputed on request), backend startup enforces declared memory caps and writes a persistent logfile, and `aggregates_refreshed` list transparently names which caches a completed run maintained.

## Test Cases

### TC-01 — Coverage snapshot persisted on backfill completion

**Type:** api
**Preconditions:** Database initialized; no prior `coverage_snapshot` row for 2026-05-15

**Steps:**
1. Start backend via `scripts/start-backend.sh`
2. Via `/data` UI or direct POST to `GET /api/data/jobs`, submit a backfill job for exactly `2026-05-15` → `2026-05-15`
3. Poll job status until `finished_at` is non-null and `status` indicates completion
4. Query database: `SELECT * FROM coverage_snapshot WHERE asof_key = <resolved-asof> AND dataset_version = <current-stamp>`

**Expected outcome:** One row exists with non-null `payload_json`, `computed_at` set to a recent timestamp; the job's persisted `aggregates_refreshed` field is a non-empty list containing `"coverage"`

**Pass criteria:** Row count = 1; `payload_json` is valid JSON; `aggregates_refreshed` in the run record is non-null and non-empty

---

### TC-02 — Scanner runs visible immediately after backfill for new date

**Type:** browser
**Preconditions:** TC-01 passed; backfill for 2026-05-15 completed; `/data` shows the run

**Steps:**
1. Navigate to `/scanner-runs` immediately after backfill completion
2. Search or filter for date 2026-05-15
3. Verify a run row for that date is listed

**Expected outcome:** The 2026-05-15 run appears in the list without a page reload

**Pass criteria:** Run row visible for 2026-05-15; timestamp column shows recent completion time

---

### TC-03 — Leaderboard renders stored snapshot for new date

**Type:** browser
**Preconditions:** TC-02 passed; `/scanner-runs` shows the 2026-05-15 run

**Steps:**
1. On `/scanner-runs`, click the 2026-05-15 row to expand or open its leaderboard
2. Verify the leaderboard table renders with stock rankings and metrics
3. Spot-check one stock's values (e.g., score, entry quality) against the stored `ScannerResult` row

**Expected outcome:** Leaderboard renders with a non-empty table; values match the database `scanner_results` payload

**Pass criteria:** Table renders ≥10 rows; spot-checked values match DB within floating-point precision

---

### TC-04 — Market phase served from cache on request, computed once during finalize

**Type:** api
**Preconditions:** TC-01 passed; backfill for 2026-05-15 completed; market-phase cache warmed during finalize

**Steps:**
1. Instrument `compute_market_phase` call count (e.g., via mock.patch wraps)
2. Trigger the backfill again (same date); record call count during finalize hook
3. Reset call count; query market phase for 2026-05-15 as-of via the serving endpoint
4. Record call count after request

**Expected outcome:** Call count during finalize hook = 1; call count during request = 0 (served from cache)

**Pass criteria:** `compute_market_phase` called exactly once per finalize, zero times on subsequent reads for the same as-of

---

### TC-05 — Aggregates refreshed field matches what finalize hook computed

**Type:** api
**Preconditions:** TC-01 passed; backfill completed; run record persisted with `aggregates_refreshed`

**Steps:**
1. Query `GET /api/data` → `runs` list for the completed backfill job
2. Extract the `aggregates_refreshed` field from the run's `message` JSON
3. For each aggregate name (e.g., "coverage", "market_phase", "membership_timeline"), verify a compute-call-count counter was incremented exactly once during that run's finalize hook (using instrumented mocks)

**Expected outcome:** `aggregates_refreshed` is a subset of `["latest_snapshot", "coverage", "membership_timeline", "market_phase", "research_hot_keys"]`; each name in the list has exactly 1 compute call during finalize; names not in the list have 0 finalize calls

**Pass criteria:** All aggregates in the list have compute count = 1; all aggregates not in list have compute count = 0

---

### TC-06 — Cold restart serves coverage from storage, zero prefill calls

**Type:** api
**Preconditions:** TC-01 passed; coverage_snapshot row exists for current as-of; backend running

**Steps:**
1. Kill backend process (SIGKILL or `pkill -f uvicorn`)
2. Instrument `prefilled_bar_cache` and `_compute_coverage_uncached` call counts (reset to 0)
3. Start backend via `scripts/start-backend.sh` (real process restart, no dev.sh)
4. Immediately query `GET /api/data` (first request post-restart)
5. Record call counts for `prefilled_bar_cache` and `_compute_coverage_uncached` during that request

**Expected outcome:** Coverage block in response is byte-identical to pre-restart payload; call counts = 0

**Pass criteria:** HTTP 200; `coverage` field in response matches JSON serialization of prior `coverage_snapshot` row; both prefill and compute_uncached called 0 times

---

### TC-07 — Cold restart GET /api/data completes within budget

**Type:** api
**Preconditions:** TC-06 passed; backend restarted with fresh process; first request pending

**Steps:**
1. Kill backend; start fresh via `scripts/start-backend.sh`
2. Measure wall time of `GET /api/data` (e.g., `curl -w '%{time_total}'`)
3. Record the time (in seconds)

**Expected outcome:** Request completes in ≤ 2.0 seconds

**Pass criteria:** Wall time ≤ 2.0 s (recorded in `reports/perf-budgets.md`)

---

### TC-08 — Coverage snapshot payload byte-identical to fresh compute

**Type:** api
**Preconditions:** coverage_snapshot row exists for a given (asof_key, dataset_version); same session state

**Steps:**
1. Retrieve persisted `coverage_snapshot.payload_json` from DB for (asof_key, dataset_version)
2. In a test session with the same state, call `_compute_coverage_uncached` directly
3. Serialize both to JSON and compare field-by-field (universe_count, per-symbol table, gaps, etc.)

**Expected outcome:** Every field is byte-identical (per AG-3)

**Pass criteria:** JSON equality check passes; no field mismatches or precision differences

---

### TC-09 — Missing coverage snapshot serves honest partial payload, never 500

**Type:** api
**Preconditions:** Database with zero `coverage_snapshot` rows for current (asof_key, dataset_version); simulates pre-ingest state

**Steps:**
1. Delete all `coverage_snapshot` rows for the current as-of/dataset-version
2. Query `GET /api/data`
3. Inspect response status and coverage block

**Expected outcome:** HTTP 200; coverage block carries an honest "not yet computed" sentinel (e.g., `null` or a partial payload with explanatory note); zero whole-table prefill calls occur

**Pass criteria:** Status = 200; coverage block is not null and contains a sentinel or honest partial state; `prefilled_bar_cache` call count = 0

---

### TC-10 — Warm-up thread creates coverage snapshot after boot, post-yield only

**Type:** api
**Preconditions:** Database with zero `coverage_snapshot` rows for current as-of/dataset-version; backend not running

**Steps:**
1. Delete all `coverage_snapshot` rows
2. Start backend via `scripts/start-backend.sh`; capture the timestamp of the first `GET /api/health` returning HTTP 200 (readiness)
3. Query DB for `coverage_snapshot` rows created for the current as-of
4. Verify the row's `computed_at` timestamp is AFTER the readiness timestamp (proof it ran post-yield)

**Expected outcome:** Exactly one `coverage_snapshot` row exists for current as-of after boot completes; `computed_at` > first-200-timestamp

**Pass criteria:** Row count = 1; `computed_at` is later than readiness-ready time

---

### TC-11 — Health endpoint responsive throughout heavy ingest job

**Type:** api
**Preconditions:** Backend running in prod mode; ready to ingest

**Steps:**
1. Start a heavy backfill/rebuild job (e.g., spanning 100+ days)
2. Poll `GET /api/health` at ≤ 250 ms intervals throughout the job's duration
3. Record status code and response time for each poll

**Expected outcome:** Every poll returns HTTP 200 within 1 second; zero timeouts or non-200 responses

**Pass criteria:** Response count with 200 status = number of polls; zero 5xx, zero timeouts; max response time ≤ 1.0 s

---

### TC-12 — Heavy ingest job memory stays under ulimit cap

**Type:** api
**Preconditions:** Backend started via `scripts/start-backend.sh` with ulimit -v enforcing `config.server.memory_cap_mb` (6144 MB); heavy job pending

**Steps:**
1. Start a heavy backfill/rebuild job (same as TC-11)
2. Sample `/proc/<pid>/status` VmSize and VmPeak every 5 seconds during the job
3. Determine peak VmPeak value (in MB)

**Expected outcome:** Peak VmPeak < 6144 MB (the ulimit cap); stays within existing Item H margin (~5500 MB estimated)

**Pass criteria:** VmPeak max ≤ 5500 MB; no OOM kills; job completes or exits cleanly

---

### TC-13 — Interrupted run carries empty aggregates refreshed, never fabricated

**Type:** api
**Preconditions:** Backend running; backfill job mid-flight and ready to be killed

**Steps:**
1. Start a backfill job; allow it to complete its date-loop
2. Kill the backend process (SIGKILL) BEFORE the finalize hook completes (between date-loop and aggregate-refresh)
3. Boot orphan sweep runs and marks the job `interrupted`
4. Query the run record via `GET /api/data/jobs/{job_id}`

**Expected outcome:** Run status = `interrupted`; `aggregates_refreshed` field is empty/null (never a fabricated list)

**Pass criteria:** `aggregates_refreshed` is null or empty list (same as if finalize never ran); no compute calls attributed to the run

---

### TC-14 — Fetch and expand jobs carry null aggregates refreshed

**Type:** api
**Preconditions:** Backend running; database ready

**Steps:**
1. Submit a `fetch` job via the `/data` job form
2. Submit an `expand` job via the `/data` job form
3. Allow both to complete
4. Query their run records via `GET /api/data`

**Expected outcome:** Both runs' `aggregates_refreshed` fields are `null` (not empty list, but null, matching the convention for non-applicable kinds like `fetch`/`expand`)

**Pass criteria:** `aggregates_refreshed` is null for both fetch and expand runs; no compute calls attributed to them

---

### TC-15 — Start script enforces memory cap and malloc arena limit

**Type:** api
**Preconditions:** Backend not running

**Steps:**
1. Start backend via `scripts/start-backend.sh`
2. Read `/proc/<pid>/status` to extract RLIMIT_AS (VmLimit)
3. Read `/proc/<pid>/environ` to check MALLOC_ARENA_MAX

**Expected outcome:** RLIMIT_AS = config.server.memory_cap_mb × 1024 KB (6144 MB = 6442450944 bytes); MALLOC_ARENA_MAX=2 present in environment

**Pass criteria:** RLIMIT_AS matches config value; `MALLOC_ARENA_MAX=2` found in environ

---

### TC-16 — Backend logfile contains boot sequence

**Type:** artifact
**Preconditions:** Backend started via `scripts/start-backend.sh`; running and ready

**Steps:**
1. Read the persistent backend logfile (path documented in dev handoff)
2. Check for expected log lines: config load, table creation, orphan sweep, readiness-ready

**Expected outcome:** Logfile contains all boot milestones

**Pass criteria:** Lines present for: "Loading config", "Creating tables", "Orphan sweep", "Ready to serve" (or equivalent per actual code)

---

### TC-17 — Backend logfile ends abruptly after simulated crash

**Type:** artifact
**Preconditions:** Backend running; logfile written; ready to crash

**Steps:**
1. Capture the current line count of the backend logfile
2. Kill backend process (SIGKILL)
3. Read logfile again; compare final lines

**Expected outcome:** Logfile ends abruptly after the last boot/serving line; no clean-shutdown entry (e.g., "Graceful shutdown" or "Goodbye")

**Pass criteria:** Final line is a boot/serving line; no graceful-shutdown line present; line count increased by 0-1 (only unflush buffer, if any)

---

### TC-18 — Existing J-01/J-03 breakdown and chunking tests still pass

**Type:** api
**Preconditions:** Full test suite available; `test_data_manager.py` loaded

**Steps:**
1. Run only the breakdown and chunking test cases: `dates_total`, `calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other`, `chunk_index`, `chunk_total` assertions
2. Ensure no changes to existing J-01/J-03 shipped fields
3. Verify all assertions pass unedited

**Expected outcome:** All existing tests pass without modification

**Pass criteria:** Test exit code = 0; no assertion failures; no new test modifications required

---

### TC-19 — New finalize-hook calls make zero outbound network requests

**Type:** api
**Preconditions:** Backend running; network monitoring active (test fixture that fails on any `socket`/`requests`/`httpx` call)

**Steps:**
1. Instrument the test to fail on any outbound network call (e.g., mock `socket.socket` and `requests.get` to raise an exception)
2. Run a backfill job that triggers the finalize hook
3. Observe whether any network call is attempted

**Expected outcome:** Finalize hook completes without any network call; no exception raised

**Pass criteria:** Job completes successfully; zero network calls logged (per AG-9)

---

### TC-20 — Aggregates refreshed line renders on /data run detail

**Type:** browser
**Preconditions:** Completed backfill with non-empty `aggregates_refreshed` list visible on `/data`

**Steps:**
1. Navigate to `/data`
2. Locate the completed backfill run in the run history or last-run panel
3. Expand or inspect the run's detail
4. Check for the new line naming the refreshed aggregates

**Expected outcome:** The UI renders a line such as "Aggregates refreshed: coverage, market phase, membership timeline, research hot-keys"

**Pass criteria:** Line is visible; lists at least one aggregate name; text is clear and readable

---

### TC-21 — Dev handoff documents logfile path and sample aggregates refreshed value

**Type:** artifact
**Preconditions:** Implementation completed; dev handoff written at `docs/handoffs/goal-ops-hardening-iter-2-dev.md`

**Steps:**
1. Read the dev handoff file
2. Verify it documents:
   - The exact filesystem path of the persistent backend logfile
   - A sample `aggregates_refreshed` value from a real run (e.g., `["coverage", "market_phase", "membership_timeline"]`)

**Expected outcome:** Both the path and sample value are present and documented

**Pass criteria:** Logfile path is absolute and matches what the start script writes; sample value is a valid JSON array with at least one aggregate name

---

## Summary

**Total test cases:** 21
- **API tests:** 13 (TC-01, TC-04 through TC-09, TC-11 through TC-15, TC-19)
- **Browser tests:** 3 (TC-02, TC-03, TC-20)
- **Artifact checks:** 5 (TC-10 timestamp comparison, TC-16, TC-17, TC-18, TC-21)

All test cases derive directly from the phase spec's 21 test-first contracts (TC-1 through TC-21 in `docs/phases/goal-ops-hardening-iter-2.md`). Each test case verifies:
- Coverage snapshot creation and persistence
- Aggregate warm-up and cache serving
- Byte-identity and freshness of served data
- Memory/responsiveness bounds
- Honesty gating for interrupted/non-applicable runs
- Script enforcement of memory caps and logfile persistence
- UI transparency about refreshed aggregates
- No regressions to J-01/J-03 shipped fields
- Anti-goal compliance (AG-3, AG-8, AG-9)
