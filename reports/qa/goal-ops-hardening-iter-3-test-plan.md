# goal-ops-hardening-iter-3 Functional Test Plan

**Phase:** goal-ops-hardening-iter-3
**Date:** 2026-07-20
**Frontend Present:** yes

## Phase Goal

Close the fetch/expand coverage-freshness gap (audit findings B1/B2) so that `/data`'s default coverage view accurately reflects the data after ANY ingest kind (including `fetch`/`expand`, not just `backfill`/`rebuild`), and measure J-05's final unmeasured acceptance step: backend health and memory ceiling during a real heavy ingest job.

## Test Cases

### TC-1 — Fetch with new bars triggers coverage refresh

**Type:** api
**Preconditions:** Backend running; a committed DB with a current-stamp `coverage_snapshot` row already persisted; a `fetch` job that lands ≥1 new bar (changing `_membership_dataset_version`)

**Steps:**
1. Execute the `fetch` job via the ingest API (or test harness) that changes the bars manifest
2. Wait for the job to complete with status "ok" or "partial"
3. Call `GET /api/data?as_of=None` (default path)
4. Compare the returned `coverage.symbol_count` and `coverage.snapshot_count` against a fresh independent `_compute_coverage_uncached()` call for the same stamp

**Expected outcome:** After a successful `fetch` that lands new bars, the finalize hook persists a fresh `coverage_snapshot` row with an updated `computed_at` timestamp

**Pass criteria:** The `GET /api/data` response's coverage block `symbol_count`/`snapshot_count` match the freshly-computed values (byte-identical), not the pre-fetch stale values

---

### TC-2 — Fetch with zero new bars skips compute

**Type:** api
**Preconditions:** Backend running; a committed DB with a current `coverage_snapshot` row; a `fetch` job that lands zero new bars (the common offline no-op case)

**Steps:**
1. Instrument `_compute_coverage_uncached()` with a call-count assertion
2. Execute the `fetch` job that lands zero new bars (e.g., all fixtures already present)
3. Wait for the job to complete
4. Assert that `_compute_coverage_uncached()` was never invoked (call count == 0)
5. Verify no new `coverage_snapshot` row was written and the existing row's `computed_at` was not updated

**Expected outcome:** A zero-bar `fetch` incurs zero extra compute cost; the persistent row is untouched

**Pass criteria:** Call-count to `_compute_coverage_uncached()` is 0; existing row unchanged in DB

---

### TC-3 — Expand with new passer history triggers coverage refresh

**Type:** api
**Preconditions:** Backend running; a committed DB with a current `coverage_snapshot` row; an `expand` job that adds new passer history (changes the bars manifest)

**Steps:**
1. Execute an `expand` job that adds a new passer's history to the ingested bars
2. Wait for the job to complete successfully
3. Call `GET /api/data?as_of=None`
4. Compare the returned coverage counts against a fresh `_compute_coverage_uncached()` call

**Expected outcome:** The `expand` job's finalize hook persists a fresh `coverage_snapshot` row, byte-identical to a direct fresh compute

**Pass criteria:** Coverage counts are byte-identical to the independent fresh compute; `computed_at` timestamp is updated

---

### TC-4 — Stale coverage_snapshot rows pruned on dataset_version change

**Type:** api
**Preconditions:** Backend running; multiple `coverage_snapshot` rows exist under a now-superseded `dataset_version` (for different `asof_key`s); a new ingest job detects the dataset version has changed

**Steps:**
1. Query the DB to find all `coverage_snapshot` rows with the old `dataset_version`
2. Trigger a new ingest job (fetch, expand, backfill, or rebuild) that changes `_membership_dataset_version`
3. Wait for the finalize hook to complete
4. Query the DB again to verify rows with the old `dataset_version` are deleted

**Expected outcome:** All `coverage_snapshot` rows whose `dataset_version` differs from the current value are deleted in one bounded SQL DELETE statement (not a per-row Python scan), leaving only current-stamp rows

**Pass criteria:** Old-version rows are deleted; deletion is via one SQL DELETE (verify no loop in logs/trace); only current-stamp rows remain

---

### TC-5 — Cold boot returns honest all-zero sentinel without whole-table compute

**Type:** api
**Preconditions:** Backend just booted with zero ingest performed this session; committed DB with no bars ingested

**Steps:**
1. Call `GET /api/data?as_of=None` (the default path)
2. Verify HTTP 200 response
3. Check that `coverage` block shows all-zero values (universe: 0, symbols: 0, trading-days: 0, snapshot-dates: 0)
4. Instrument the `daily_prices` table query and verify zero queries beyond the committed-pool file read

**Expected outcome:** The default path returns HTTP 200 with the honest "not yet computed" sentinel without triggering a whole-table scan

**Pass criteria:** HTTP 200; all coverage counts == 0; no `daily_prices` table queries incurred (iter-2 TC-6/TC-9 remain unregressed)

---

### TC-6 — Fetch-triggered coverage refresh is byte-identical to fresh compute

**Type:** api
**Preconditions:** Backend running; a `fetch` or `expand` job has completed, triggering a coverage refresh; the job's finalize hook has persisted the new `coverage_snapshot` row

**Steps:**
1. Retrieve the persisted `coverage_snapshot` row's `payload_json` from the DB
2. Call `_compute_coverage_uncached()` independently for the same resolved as-of date
3. Compare the two `payload_json` objects field-by-field

**Expected outcome:** Every field in the persisted row matches the independent fresh compute exactly

**Pass criteria:** Field-by-field comparison shows byte-identical `payload_json`; no field mismatch or rounding error

---

### TC-7 — Widened finalize trigger makes zero external network calls

**Type:** api
**Preconditions:** Backend running with network/socket instrumentation enabled; a `fetch` or `expand` job that changes the bars manifest

**Steps:**
1. Start network/socket monitoring for the backend process
2. Execute the `fetch`/`expand` job
3. During the finalize step, monitor for any outbound TCP/UDP/socket activity
4. Wait for the job to complete

**Expected outcome:** The coverage refresh during the finalize step incurs zero external network/socket calls (AG-9 compliance)

**Pass criteria:** Zero external calls logged/detected; no network traffic to external systems during finalize hook

---

### TC-8 — Health polling during heavy job stays responsive

**Type:** api
**Preconditions:** Backend running via `scripts/start-backend.sh` (enforcing 6144 MB `ulimit -v` and `MALLOC_ARENA_MAX=2`); a real heavy ingest job queued (full `rebuild` or large multi-day `backfill` e.g., 2025-06-01 → 2026-07-17)

**Steps:**
1. Start polling `GET /api/health` at ≤250ms intervals
2. Dispatch the heavy job
3. Continue polling throughout the job's full duration (may take hours)
4. Record every poll's HTTP status code and response time
5. When the job completes, finalize the health poll log

**Expected outcome:** Every health poll returns HTTP 200 within 1 second; no timeouts or non-200 responses during the job

**Pass criteria:** All health polls: HTTP 200; all response times < 1 second; zero failures or timeouts

---

### TC-9 — Memory ceiling (VmPeak/VmSize) stays under 6144 MB ulimit during heavy job

**Type:** api
**Preconditions:** Backend running via `scripts/start-backend.sh` with 6144 MB `ulimit -v` cap; a real heavy ingest job (same as TC-8)

**Steps:**
1. Record the backend process ID
2. Start sampling `/proc/<pid>/status` for `VmPeak` and `VmSize` at ≤250ms intervals (alongside TC-8's health polls)
3. Dispatch the heavy job
4. Continue sampling throughout the job's duration
5. Record peak `VmPeak` and `VmSize` values observed
6. Calculate margin: 6144 MB - peak value
7. Append results to `reports/perf-budgets.md` (next lettered item after Item K)

**Expected outcome:** Peak `VmPeak` and `VmSize` stay under the 6144 MB `ulimit -v` cap with measurable margin

**Pass criteria:** Peak VmPeak/VmSize < 6144 MB; margin ≥ 10% (or other threshold defined in perf-budgets.md); results recorded in perf-budgets.md with date and job details

---

### TC-10 — J-01/J-03/J-04 regression tests pass unedited

**Type:** api
**Preconditions:** Existing test suites for J-01 (breakdown/chunking), J-03 (no per-run cap), J-04 (boot/readiness/logfile) are present and previously passing

**Steps:**
1. Run the full J-01 test suite (breakdown and chunking assertions)
2. Run the full J-03 test suite (no per-run range cap, chunked execution)
3. Run the full J-04 test suite (non-blocking boot, visible status, crash handling)
4. Record pass/fail status for each

**Expected outcome:** Every previously-passing assertion in the J-01/J-03/J-04 test suites still passes without modification

**Pass criteria:** All tests pass; zero regressions; no test code changes required

---

### TC-11 — Fetch + reload shows real coverage, not all-zero sentinel

**Type:** browser
**Preconditions:** Frontend running; `/data` page accessible; a committed DB with bars ingested; the B1 fix deployed

**Steps:**
1. Navigate to `/data` page (Coverage section visible)
2. Note the current coverage counts (Universe, Symbols, Trading-days, Snapshot-dates)
3. Open the Job Dispatch form on the same page
4. Execute a `fetch` job that lands at least one new bar
5. Wait for the job to complete (status shows "ok" or "partial")
6. Reload the `/data` page (or wait for auto-refresh if implemented)
7. Check the coverage panel again

**Expected outcome:** After the fetch job completes and the page reloads, the coverage panel shows real non-zero counts reflecting the fetched data, not the all-zero sentinel

**Pass criteria:** Coverage counts are non-zero and match the freshly-ingested bars; the literal B1 regression (false all-zero after fetch) is fixed

---

### TC-12 — Dev handoff documents B1/B2 fix and measured numbers

**Type:** artifact
**Preconditions:** Iteration complete; TC-8/TC-9 measurements recorded

**Steps:**
1. Read `docs/handoffs/goal-ops-hardening-iter-3-dev.md`
2. Verify it includes a concrete before/after description of the B1 fix (fetch/expand coverage refresh)
3. Verify it includes a concrete before/after description of the B2 fix (stale-row prune)
4. Verify it includes the TC-8 health poll results (all 200 within 1s)
5. Verify it includes the TC-9 peak VmPeak/VmSize and margin under 6144 MB

**Expected outcome:** The dev handoff is present and documents all required context

**Pass criteria:** File exists at `docs/handoffs/goal-ops-hardening-iter-3-dev.md`; B1 before/after is described; B2 before/after is described; TC-8/TC-9 numbers are recorded with date and margin

---

## Summary

Total test cases: 12
API/integration tests: 9 (TC-1, TC-2, TC-3, TC-4, TC-5, TC-6, TC-7, TC-8, TC-9)
Browser tests: 1 (TC-11)
Artifact checks: 2 (TC-10 is a regression suite verification; TC-12 is a handoff artifact check)

**Key coverage:**
- **B1 fix (fetch/expand refresh):** TC-1, TC-2, TC-3, TC-11
- **B2 fix (stale-row prune):** TC-4
- **Correctness (byte-identity):** TC-6
- **Cold-boot regression:** TC-5
- **J-05 step-4 live measurement:** TC-8, TC-9
- **Anti-goal compliance (AG-9 no network):** TC-7
- **Required-still-passing regression:** TC-10
- **Handoff documentation:** TC-12
