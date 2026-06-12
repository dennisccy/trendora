# Goal Iteration 8 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8  
**Date:** 2026-06-12  
**Frontend Present:** yes

## Phase Goal

The Data Manager's multi-date snapshot backfill completes at least ~2× faster than the sequential per-date sum with byte-identical snapshots/forward-returns, and every fetch+backfill job's status payload and `/data` job card surface honest per-stage timings (fetch vs backfill: elapsed, items processed, concurrency used).

---

## Test Cases

### TC-01 — Parallel backfill produces byte-identical output to sequential path

**Type:** api  
**Preconditions:**
- Backend running on :8835
- `config.yaml` has `data_manager.import_chunking.backfill_workers` configured (default 4)
- Test data seed present (prices, symbols)

**Steps:**
1. Run a backfill job over a fixed multi-date range with `backfill_workers=4` via `/api/data/jobs/backfill` or equivalent internal runner
2. Capture all snapshot rows and forward-return rows from `scanner_runs` and forward-return tables for that range
3. Run the same backfill over the same range with `backfill_workers=1` (sequential)
4. Capture all snapshot rows and forward-return rows for that range
5. Compare: row counts, scores, buckets, setup fields, return values — all identical

**Expected outcome:** Parallel (workers=4) and sequential (workers=1) produce byte-identical snapshots and forward-returns

**Pass criteria:** All captured rows match exactly (same score, bucket, setup, return values; same row counts); no UNIQUE constraint crashes; both complete without errors

---

### TC-02 — Multi-date backfill wall-clock ≥~2× faster than per-date sum

**Type:** browser  
**Preconditions:**
- Backend running on :8835, frontend on :3835
- `/data` page accessible
- Test seed range covers at least 5+ dates with uncovered symbol/date combos
- `backfill_workers=4` configured

**Steps:**
1. Navigate to `/data` page
2. Click "Start Job" or equivalent; select a backfill-only job over 5+ dates (e.g. a date range with no fetch required)
3. Watch the job progress UI; record the **final job-status payload** via `GET /api/data/jobs/{job_id}` after completion
4. Extract `stages.backfill.elapsed_ms` (wall-clock) and `stages.backfill.per_date_sum_ms` (sum of per-date durations)
5. Calculate speedup ratio: `per_date_sum_ms / elapsed_ms`
6. Verify speedup ≥ ~2.0

**Expected outcome:** Job completes; backfill stage wall-clock is materially faster than the sum of per-date durations

**Pass criteria:** `per_date_sum_ms / elapsed_ms >= 2.0` as evidenced by the final job status payload; timings are present and non-zero

---

### TC-03 — Job status payload includes honest per-stage timings

**Type:** api  
**Preconditions:**
- Backend running, a completed or in-flight job present in the system
- Job executed at least one stage (fetch or backfill)

**Steps:**
1. Call `GET /api/data/jobs/{job_id}` for a completed job
2. Inspect the response body for a `stages` object
3. For each executed stage (fetch or backfill if present), verify:
   - `elapsed_ms` field exists and is a positive number
   - `items_processed` field exists and matches expected count (symbols for fetch, dates for backfill)
   - `concurrency_used` field exists and equals the config value (e.g. `fetch_workers` or `backfill_workers`)
   - For backfill stage: `per_date_sum_ms` field exists and is >= `elapsed_ms`
4. For a stage never executed, verify it is absent or marked NA

**Expected outcome:** Job status includes a well-formed `stages` object with all required timing fields for each executed stage

**Pass criteria:** All timing fields present and sensible (elapsed > 0, items == count, concurrency == config, per_date_sum >= elapsed for backfill); absent fields for unexecuted stages; no fabricated/zero values

---

### TC-04 — Job card renders stage-timings block with config-backed labels

**Type:** browser  
**Preconditions:**
- Frontend running on :3835
- A completed fetch+backfill job present
- Backend config includes glossary entries under `config.methodology` for the new stat labels

**Steps:**
1. Navigate to `/data` page
2. Locate the job card for the completed job
3. Verify the job card displays a stage-timings block with:
   - Fetch stage row: "Elapsed", "Symbols fetched", "Concurrency"
   - Backfill stage row: "Elapsed", "Dates backfilled", "Concurrency", and a derived row showing per-date sum vs wall-clock
4. Hover over or click the info icon next to a stat label (e.g. "Concurrency")
5. Verify a tooltip appears with text from the `config.methodology` glossary

**Expected outcome:** Job card displays a well-formatted stage-timings block with human-readable labels and tooltips backed by config

**Pass criteria:** All stat labels render; tooltips appear on hover/click and contain glossary text; layout matches the dense analytical style of existing job-card rows; no broken links or missing values

---

### TC-05 — Job detail page renders stage-timings block with same content

**Type:** browser  
**Preconditions:**
- Frontend running, a completed job present
- Job detail page accessible

**Steps:**
1. Navigate to `/data` page and click on a completed job card to open the job detail
2. Scroll to find the stage-timings section (same content as job card, but expanded)
3. Verify all stage timings display with full precision (elapsed in milliseconds, item counts, concurrency)
4. Verify the backfill speedup evidence is clear: per-date sum vs wall-clock side-by-side

**Expected outcome:** Job detail page displays stage-timings block with complete timing data and speedup evidence

**Pass criteria:** All timing fields render accurately; data matches the payload from `GET /api/data/jobs/{id}`; speedup ratio is derivable and sensible

---

### TC-06 — Idempotent re-run: same range produces no duplicates

**Type:** browser + artifact  
**Preconditions:**
- Backend running, a completed backfill job over a known date range
- Database accessible at `apps/backend/data/trendora.db`

**Steps:**
1. Record the final snapshot/forward-return row counts for the covered date range from `scanner_runs` and forward-return tables
2. Re-run the same backfill job over the same date range via `/data` start
3. Allow the job to complete
4. Query the database again; count rows for that range
5. Compare: new row count == old row count; no duplicate rows created
6. Verify job status shows "already present" or similar honest outcome, no error

**Expected outcome:** Re-running the same range is idempotent; database row counts unchanged; no crash

**Pass criteria:** No UNIQUE constraint crash; no duplicate rows inserted; row counts identical before and after second run; job completes with honest status

---

### TC-07 — Concurrency safety: concurrent same-date creation → one snapshot

**Type:** api  
**Preconditions:**
- Backend running
- Test harness can trigger concurrent backfill workers

**Steps:**
1. Trigger multiple backfill workers to attempt creation of a snapshot for the same date concurrently
2. Verify no UNIQUE constraint crash occurs
3. Query database: exactly one snapshot row exists for that date
4. Verify the snapshot is complete and correctly computed (no partial/corrupted state)

**Expected outcome:** Concurrent creation for the same date results in one snapshot, no crash, no data corruption

**Pass criteria:** No UNIQUE constraint exception; exactly one row per date; snapshot values correct and consistent

---

### TC-08 — Config validation: backfill_workers boot check

**Type:** api  
**Preconditions:**
- Backend not yet started
- Test can modify `config.yaml` or inject config

**Steps:**
1. Set `backfill_workers` to an invalid value (e.g. 0, -1, or a non-integer)
2. Attempt to start the backend
3. Verify boot fails with an explicit error message mentioning the field and validation rule (>= 1)

**Expected outcome:** Backend boot fails with a clear validation error

**Pass criteria:** Error message explicitly names the field and the constraint (must be >= 1); boot does not proceed

---

### TC-09 — Resumable job with partial timings after provider failure (alpha_vantage demo)

**Type:** browser + api  
**Preconditions:**
- Backend running
- Config set to use `alpha_vantage` with session key `demo` (triggers rate-limit/resumable)
- Frontend running on :3835

**Steps:**
1. Start a fetch+backfill job from `/data` with source `alpha_vantage` and session key `demo`
2. Allow the fetch stage to hit the throttle and enter a resumable state (expect ~3–16 min)
3. Verify the job shows `status = "resumable"` on `/data` job card
4. Verify the job-status payload includes `stages.fetch` with partial timings:
   - `elapsed_ms` > 0 (time spent before hitting rate limit)
   - `items_processed` > 0 (symbols fetched before limit)
   - `concurrency_used` == config value
5. Verify no backfill stage timings are present (stage never ran)
6. Call `GET /api/data/jobs/{id}` and verify the response does not contain API keys or tokens in `errors[]`

**Expected outcome:** Job enters resumable state with honest partial timings; no key leakage

**Pass criteria:** Job status is `resumable`; fetch timings present and sensible; no `?token=` or `?apikey=` in error strings; backfill timings absent as expected

---

### TC-10 — Job error strings do not leak provider keys

**Type:** api  
**Preconditions:**
- A job that encountered a provider error (rate limit, connection failure, etc.)
- Job status available via `GET /api/data/jobs/{id}`

**Steps:**
1. Call `GET /api/data/jobs/{id}` for a failed/resumable job
2. Inspect the `errors[]` array in the response
3. Grep each error string for patterns: `?token=`, `?apikey=`, `?key=`
4. Verify no such patterns are present (no full URL with embedded secrets)

**Expected outcome:** Error messages do not contain full URLs with embedded API keys

**Pass criteria:** No `?token=` or `?apikey=` patterns found in `errors[]`; error messages are sanitized and user-safe

---

### TC-11 — Required journeys still pass: J-17 (as-of dates + Backtest growth)

**Type:** browser  
**Preconditions:**
- Frontend running on :3835
- Backtest data available (from prior iterations)

**Steps:**
1. Navigate to Backtest page
2. Verify the date selector works and as-of dates appear
3. Run a backtest; verify "n" (number of snapshots/results) grows as expected
4. Verify the Backtest journey is operational

**Expected outcome:** As-of date control works; Backtest n-count grows with data

**Pass criteria:** Date selector functional; Backtest runs; n > 0 and grows with more data; no regressions

---

### TC-12 — Required journeys still pass: J-34 (amber resumable + Resume button)

**Type:** browser  
**Preconditions:**
- A resumable job available from prior QA setup
- `/data` page accessible

**Steps:**
1. Navigate to `/data` page
2. Locate a job with `status = "resumable"`
3. Verify the job card shows an amber-tinted or visually distinct resumable indicator
4. Click the "Resume" button
5. Verify the job resumes and progresses without duplicating fetch or backfill work

**Expected outcome:** Resumable jobs are clearly indicated; Resume button works; no duplicates on resume

**Pass criteria:** Resumable status visually distinct; Resume button present and functional; job completes without errors; database shows no duplicate rows

---

### TC-13 — Required journeys still pass: J-36 (coverage stats)

**Type:** browser + api  
**Preconditions:**
- Data present for multiple symbols/dates
- Backend running

**Steps:**
1. Call `GET /api/data` to fetch job summaries and coverage stats
2. Verify coverage metrics are reported (e.g. symbols covered, date range, %)
3. Navigate to `/data` page
4. Verify coverage is displayed on the page

**Expected outcome:** Coverage stats are available and accurate

**Pass criteria:** Coverage endpoint and UI both report sensible values; no missing data

---

### TC-14 — Required journeys still pass: J-37/J-38 (pull-missing + unfinished-imports)

**Type:** browser + artifact  
**Preconditions:**
- Backend running with existing seed data
- `/data` page accessible

**Steps:**
1. Trigger a "pull missing" operation (or ensure an unfinished import exists)
2. Verify the `/data` page shows the unfinished import in a distinct section
3. Call `GET /api/data/jobs` and verify the job appears with appropriate status
4. Verify Resume and Retry buttons are available

**Expected outcome:** Unfinished imports are tracked and UI allows resumption/retry

**Pass criteria:** Unfinished-imports section present on `/data` page; Resume/Retry buttons functional; database audit trail intact

---

### TC-15 — Required journeys still pass: J-39 (preview endpoint only, no live remove)

**Type:** browser  
**Preconditions:**
- Backend running with NVDA bars in the database
- Frontend running

**Steps:**
1. Navigate to `/data` page
2. Locate the NVDA symbol entry
3. Attempt to remove NVDA via the preview endpoint only (verify UI routes to preview, not live destructive endpoint)
4. Verify the preview shows what would be removed without actually deleting
5. Do NOT call the destructive live `POST /api/data/remove` endpoint

**Expected outcome:** Preview endpoint works; no destructive operations on live data

**Pass criteria:** Preview endpoint returns expected result; no rows deleted from the database

---

### TC-16 — Required journeys still pass: J-40 (cold-start readiness badge)

**Type:** browser  
**Preconditions:**
- Frontend running
- Backend starting fresh or with minimal warm-up

**Steps:**
1. Restart the backend (kill by port :8835)
2. Immediately navigate to `/data` page
3. Verify a readiness indicator (e.g. "Warming up…" badge) appears while the backend is initializing
4. Wait for the badge to change to "Ready" or similar
5. Verify the page becomes fully functional

**Expected outcome:** Readiness badge is honest during warm-up and resolves correctly

**Pass criteria:** Badge present during startup; transitions to "Ready" state; page becomes functional after warm-up

---

### TC-17 — Required journeys still pass: J-41 (create-once idempotency under concurrent backfill)

**Type:** api  
**Preconditions:**
- Backend running
- Parallel backfill workers active

**Steps:**
1. Trigger a backfill job with workers > 1
2. Verify that concurrent workers do not crash on UNIQUE constraint when creating snapshots
3. Query the database; verify each date has exactly one snapshot
4. Re-run the same range; verify no new snapshots are created
5. Verify the job status honestly reports "already present" or similar

**Expected outcome:** Idempotent create-once semantics hold under parallelism

**Pass criteria:** No UNIQUE crashes; one snapshot per date; re-run is idempotent; honest status reported

---

### TC-18 — Required journeys still pass: J-44 toggle off→reload→still-off persistence

**Type:** browser  
**Preconditions:**
- Frontend running on :3835
- Historical toggle accessible

**Steps:**
1. Navigate to the page with the historical toggle (e.g. `/backtest`)
2. Toggle the historical mode OFF
3. Reload the page (Ctrl+R or F5)
4. Verify the toggle is still OFF after reload
5. Verify the page displays present-day data (not historical)

**Expected outcome:** Toggle state persists across page reload

**Pass criteria:** Toggle state is OFF before and after reload; data displayed matches expected mode

---

### TC-19 — Required journeys still pass: J-46 (fetch-pool semantics unchanged)

**Type:** api  
**Preconditions:**
- Backend running
- A fetch job configured

**Steps:**
1. Start a fetch job from `/data` (e.g. expand universe or fetch new symbols)
2. Verify the job progresses and completes
3. Query `data_provider_runs` table; verify fetch job recorded honestly
4. Verify fetched rows appear in the bars/snapshot tables

**Expected outcome:** Fetch stage works; pooling semantics unchanged; data committed correctly

**Pass criteria:** Job completes; database rows inserted correctly; no regressions in fetch logic

---

### TC-20 — Frontend TypeScript compile clean

**Type:** artifact  
**Preconditions:**
- Frontend source at `apps/frontend/`
- TypeScript compiler available

**Steps:**
1. Navigate to `apps/frontend/`
2. Run `npx tsc --noEmit`
3. Verify no errors or warnings

**Expected outcome:** TypeScript compiles without errors

**Pass criteria:** `tsc` exit code 0; no output on stderr

---

## Summary

**Total test cases:** 20  
**Browser tests:** 12 (TC-01, TC-04, TC-05, TC-06, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-18, TC-19)  
**API tests:** 6 (TC-03, TC-07, TC-08, TC-09, TC-10, TC-20 artifact)  
**Artifact checks:** 2 (TC-06, TC-20)

**Key validation points:**
- Parallel backfill produces byte-identical output to sequential path (correctness)
- Backfill wall-clock ≥~2× faster than per-date sum (performance)
- Honest per-stage timings rendered on job card and detail (UX)
- Idempotency under parallelism (safety)
- Required journeys remain green (regression testing)
- No key leakage in error strings (security)
