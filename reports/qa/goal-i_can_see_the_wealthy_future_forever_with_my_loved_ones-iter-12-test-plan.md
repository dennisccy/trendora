# Goal Iteration 12 — Jobs Pipeline Reliability Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Date:** 2026-06-13
**Frontend Present:** yes

## Phase Goal

Make the Data Manager's import jobs reliably resumable from the backfill stage with zero provider re-fetches, recorded in Run history from job start with fine-grained honest progress counters, and transactionally sound under concurrent multi-date backfill so a single bad date is isolated instead of aborting the entire stage.

## Test Cases

### TC-01 — Stage-aware checkpoint persists fetch completion

**Type:** api
**Preconditions:** A fresh job is dispatched and completes the fetch stage.

**Steps:**
1. Send `POST /api/data/jobs` with a multi-symbol, multi-date backfill request (e.g. 3 symbols over 2 months).
2. Poll `GET /api/data/jobs/{job_id}` until the fetch stage completes (or manually force a fault at the end of fetch).
3. Query `ImportCheckpoint` table directly for the created checkpoint row.
4. Verify the `fetch_done` (or equivalent stage-completion field) is set to `true`.

**Expected outcome:** The checkpoint row records fetch completion via a stage-completion field.
**Pass criteria:** `fetch_done == true` in the row when fetch stage completes; other stage flags (`screen_done`, `backfill_done`) are `false`.

---

### TC-02 — Resume from backfill stage performs zero provider calls

**Type:** api
**Preconditions:** A checkpoint exists with `fetch_done == true` (from TC-01 or previous job). An injected counting provider is active.

**Steps:**
1. Create a counting provider fixture that tallies each `fetch_eod()` call.
2. Call `resume_job(job_id)` on the existing checkpoint.
3. Assert the counting provider's call count remains `0` throughout the backfill stage.
4. Verify the backfill stage completes without hitting the live provider.

**Expected outcome:** Resume skips the fetch stage entirely and jumps to backfill with no provider calls.
**Pass criteria:** Counting provider call count == 0 after resume; job transitions to backfill stage immediately; no exceptions from provider code.

---

### TC-03 — Checkpoint survives simulated process restart

**Type:** api
**Preconditions:** A checkpoint with `fetch_done == true` exists in the database (persisted to disk).

**Steps:**
1. Load and inspect the checkpoint row from the database (simulate restart by closing and reopening the DB connection).
2. Call `resume_job(job_id)` using the reloaded checkpoint.
3. Verify the fetch stage is skipped again (zero provider calls via counting provider).

**Expected outcome:** The checkpoint is durable across process boundaries; resume route is stable.
**Pass criteria:** Checkpoint row reloads with the same stage flags; resume still skips fetch; no duplicate rows created.

---

### TC-04 — Covered-range fetch planner skips fully covered (symbol, window)

**Type:** api
**Preconditions:** A prior job has completed fetch for symbols ["AAPL", "MSFT"] over [2024-01-01, 2024-03-31]. Coverage is stored in the DB.

**Steps:**
1. Dispatch a new job with the same symbols and overlapping date range (same window or within it).
2. Inject a counting provider; run the fetch stage.
3. Assert counting provider calls == 0 for the covered (symbol, window) pairs.
4. Verify the job transitions to backfill stage without fetching.

**Expected outcome:** The fetch planner consults stored coverage and skips fully covered ranges.
**Pass criteria:** Counting provider calls == 0; fetch stage completes in < 2 seconds (no HTTP latency); job proceeds directly to backfill.

---

### TC-05 — Partially covered window still fetches

**Type:** api
**Preconditions:** Coverage exists for ["AAPL"] over [2024-01-01, 2024-03-31] but NOT for [2024-04-01, 2024-06-30].

**Steps:**
1. Dispatch a new job requesting ["AAPL"] over [2024-03-15, 2024-06-30] (partially covered).
2. Inject a counting provider.
3. Run the fetch stage.
4. Assert counting provider calls > 0 (the provider is hit for the uncovered portion).

**Expected outcome:** Partial coverage forces a fetch; the per-(symbol, date) idempotency prevents duplicate rows.
**Pass criteria:** Counting provider calls > 0; new bars inserted into `eod_bars` for dates > 2024-03-31; no duplicate rows (no UNIQUE constraint violation).

---

### TC-06 — Job creates DataProviderRun row at start with running status

**Type:** api
**Preconditions:** No job is currently running. The job registry is empty.

**Steps:**
1. Send `POST /api/data/jobs` to start a new import job.
2. Immediately query `DataProviderRun` table.
3. Find the row matching the job ID and verify status == "running".
4. Verify the row has kind, date_range, and source fields populated.
5. Assert the session key is NOT present in any field of the row.

**Expected outcome:** A `running` row is created at job start, carrying metadata but no secrets.
**Pass criteria:** Status == "running"; kind/range/source populated; no API key in the row; `finished_at` is NULL.

---

### TC-07 — Job transitions to exactly one terminal status

**Type:** api
**Preconditions:** A job has completed or failed. Its `DataProviderRun` row exists.

**Steps:**
1. Inspect the `DataProviderRun` row for the completed job.
2. Verify the row has been updated exactly once to a terminal status (`ok`, `partial`, `failed`, or `resumable`).
3. Verify `finished_at` is set to a non-null timestamp.
4. Query the table again and confirm the row is not mutated further.

**Expected outcome:** Exactly one terminal transition; the row is stable post-completion.
**Pass criteria:** Status in (`ok`, `partial`, `failed`, `resumable`); only one row per job; `finished_at` non-null; no duplicate rows; no further mutations.

---

### TC-08 — Boot sweep marks orphaned running rows as interrupted

**Type:** api
**Preconditions:** A `DataProviderRun` row with status == "running" exists in the database. The associated job process is dead (simulated by not starting the job).

**Steps:**
1. Manually insert a `DataProviderRun` row with status == "running" and a timestamp from > 1 second ago.
2. Start the backend (lifespan) without any active job for that ID.
3. Immediately query `DataProviderRun` for that row.
4. Verify the status has been changed to "interrupted" during the boot sweep.

**Expected outcome:** Orphaned `running` rows are marked `interrupted` during startup.
**Pass criteria:** Status == "interrupted" after boot; the sweep is idempotent (no error if run again); no process PID is required in the row.

---

### TC-09 — Per-symbol completion counter is distinct and monotone

**Type:** api
**Preconditions:** A multi-symbol fetch job is in progress or completed. The fetcher uses a thread-safe completion counter.

**Steps:**
1. Dispatch a fetch job over ["AAPL", "MSFT", "GOOG"] with 2 date windows (e.g., 2 months each).
2. Poll `JobProgress.to_dict()` during the fetch stage.
3. Verify `symbols_ok` increments once per symbol (not per window).
4. Verify `symbols_ok` never exceeds `symbols_total` (== 3).

**Expected outcome:** The symbols counter counts distinct symbols and never exceeds the total.
**Pass criteria:** `symbols_ok` reaches exactly 3 when all symbols are fetched; intermediate polls show `0 <= symbols_ok <= 3`; no value > 3 observed.

---

### TC-10 — Multi-window plan counters never exceed totals (318/159 regression)

**Type:** api
**Preconditions:** A plan spans 2+ date windows over the full symbol set (e.g., 10 symbols × 3 months split into monthly windows = 6 chunks).

**Steps:**
1. Dispatch a multi-symbol, multi-window backfill plan (e.g., 6 symbols over 3 months, split into monthly windows).
2. Track the job's `JobProgress.to_dict()` during execution.
3. Verify `symbols_ok` counts distinct symbols (0 to 6, not 0 to 18 with repeated windows).
4. Verify no counter field exceeds its total.

**Expected outcome:** Counters are correct for multi-window plans.
**Pass criteria:** `symbols_ok` peaks at 6 (distinct symbols), never 18; `bars_ok <= bars_total`; `days_ok <= days_total`.

---

### TC-11 — Current-activity and heartbeat present in job payload

**Type:** api
**Preconditions:** A job is running.

**Steps:**
1. Poll `GET /api/data/jobs/{job_id}` during a running fetch or backfill stage.
2. Inspect the response payload.
3. Verify `current_activity` field is present (e.g., "fetching AAPL (2/5)" or "scanning 2024-06-01 (12/22)").
4. Verify `last_progress_at` (heartbeat timestamp) is present and updates regularly.

**Expected outcome:** The payload carries live progress metadata.
**Pass criteria:** `current_activity` is a non-empty string; `last_progress_at` is a recent timestamp (< 10 seconds old during active work).

---

### TC-12 — Backend speedup figure in backfill stage payload

**Type:** api
**Preconditions:** A backfill stage has completed.

**Steps:**
1. Poll `GET /api/data/jobs/{job_id}` after backfill completes.
2. Inspect the `stages` array, specifically the backfill stage entry.
3. Verify the `speedupFactor` field is present and is a number (or null if timings are missing/zero).
4. Verify the value is computed as `per_date_seconds_sum / elapsed_seconds` (or honest-NA).

**Expected outcome:** The frontend receives the speedup figure from the backend.
**Pass criteria:** Backfill stage has `speedupFactor` field; value is a positive number or null (never NaN or Infinity).

---

### TC-13 — Single-date failure is isolated in parallel backfill

**Type:** api
**Preconditions:** A multi-date (~91-date) parallel backfill is ready. A fault-injecting provider is active.

**Steps:**
1. Dispatch a `both` or `backfill` job over a large date range (3 months).
2. Inject a provider fault that fails on one specific date (e.g., 2024-02-15).
3. Run the backfill stage in parallel (default concurrency).
4. Verify the job completes with status == "partial".
5. Inspect the `DataProviderRun` row; verify per-date failure detail is recorded for the bad date.
6. Verify remaining dates completed successfully.

**Expected outcome:** A single date's failure does not abort the stage; the job ends `partial` with honest per-date error recording.
**Pass criteria:** Job status == "partial"; one date marked failed; remaining ~90 dates marked ok; no whole-stage abort; no fabricated snapshot for the failed date.

---

### TC-14 — Multi-date parallel backfill completes with no committed-session error

**Type:** api
**Preconditions:** A ~91-date parallel backfill is ready (e.g., a full 3-month range). The backend uses concurrent workers with proper session isolation.

**Steps:**
1. Dispatch a `backfill` job over 3 months (>= 60 trading days).
2. Run with default concurrency (workers per CPU or configured limit).
3. Verify the job completes without an "invalid ('committed')" SQLite error.
4. Check the `scanner_runs` and `scanner_results` tables for consistency.

**Expected outcome:** Parallel backfill completes reliably without transaction/session errors.
**Pass criteria:** Job status in (`ok`, `partial`, `failed`) — not an unhandled exception; no "committed" error in logs; output byte-identical to sequential engine (re-asserted via existing test suite).

---

### TC-15 — Parallel-vs-sequential byte-identical equality re-asserted

**Type:** api
**Preconditions:** The full pytest test suite is run, including `test_data_manager_backfill_parallel.py`.

**Steps:**
1. Run the suite: `python -m pytest tests/test_data_manager_backfill_parallel.py -v`.
2. Verify all parallel-vs-sequential equality tests pass.
3. Inspect any captured byte-identity assertions for `scanner_runs`, `scanner_results`, and score outputs.

**Expected outcome:** Parallel backfill produces output byte-identical to the sequential engine.
**Pass criteria:** All tests in `test_data_manager_backfill_parallel.py` pass; no byte-equality regressions.

---

### TC-16 — Browser: Unfinished-imports shows failed-at-backfill-resumable state

**Type:** browser
**Preconditions:** The frontend is running. A job has failed at the backfill stage (can be injected/seeded or replayed from a prior job state).

**Steps:**
1. Navigate to `/data`.
2. Locate the Unfinished-imports section.
3. Find a job marked as failed after the fetch stage.
4. Verify the plain-language state reads "failed at backfill — resumable from the backfill stage" (or similar).

**Expected outcome:** The user understands which stage failed and what action is available.
**Pass criteria:** State text is displayed; Resume button is present and enabled; Job ID and date range are visible.

---

### TC-17 — Browser: Resume button triggers zero-provider-call backfill

**Type:** browser
**Preconditions:** An unfinished job is displayed (failed at backfill). An injected counting provider logs calls.

**Steps:**
1. On `/data`, locate the Unfinished-imports failed job.
2. Click Resume.
3. Verify the job card updates to show backfill stage in progress.
4. Monitor the counting provider logs; assert zero fetch calls.
5. Wait for backfill to complete.

**Expected outcome:** Resume skips fetch and proceeds directly to backfill.
**Pass criteria:** Job transitions to backfill; no fetch-related HTTP calls observed; job completes with status ok/partial.

---

### TC-18 — Browser: Run history shows running row at job start

**Type:** browser
**Preconditions:** The frontend is running. A fresh job is about to be dispatched.

**Steps:**
1. Navigate to `/data`.
2. Scroll to the Run history section.
3. Start a new job (submit the form).
4. Immediately (within 1 second) refresh or poll the Run history.
5. Verify a row with status == "running" appears for the new job.

**Expected outcome:** The job is visible in Run history immediately after dispatch.
**Pass criteria:** Row appears with status "running"; job ID, kind, and date range are displayed; no delay > 2 seconds before visibility.

---

### TC-19 — Browser: Run history shows interrupted row after backend restart

**Type:** browser
**Preconditions:** A job is running (status "running" in Run history). The backend can be restarted.

**Steps:**
1. Navigate to `/data` and confirm a "running" job is visible in Run history.
2. Restart the backend (or simulate a hard stop).
3. Refresh the `/data` page.
4. Verify the job's row now shows status == "interrupted".

**Expected outcome:** The boot sweep marks the orphaned job as interrupted.
**Pass criteria:** Status changes from "running" to "interrupted"; timestamp reflects the restart; the row is permanent (not deleted).

---

### TC-20 — Browser: Live job card shows per-symbol bar, current-activity, heartbeat

**Type:** browser
**Preconditions:** The frontend is running. A job is actively running (fetch or backfill stage).

**Steps:**
1. Navigate to `/data`.
2. Watch the live job card during an active job.
3. Verify the progress bar is per-symbol (e.g., "Symbols: 2/5") and updates as symbols complete.
4. Verify a current-activity line is visible (e.g., "Fetching AAPL (3/10)" or "Scanning 2024-06-01 (12/22)").
5. Verify an "Updated X seconds ago" or "Last update: now" heartbeat is visible and updates regularly.

**Expected outcome:** The user sees real-time, granular progress without mystery/stalling.
**Pass criteria:** Bar increments; activity line changes; heartbeat refreshes at least once per 5 seconds; no counter exceeds its total.

---

### TC-21 — Browser: Backfill stage shows live timings and backend speedup

**Type:** browser
**Preconditions:** A backfill stage is in progress.

**Steps:**
1. Navigate to `/data` and watch the live job card.
2. Inspect the backfill stage entry (in the stages list / card).
3. Verify elapsed time and per-date timing are displayed and update live.
4. Verify speedup factor is displayed (e.g., "2.1x") and is NOT a client-side division.

**Expected outcome:** Timings render live; speedup comes from the backend.
**Pass criteria:** Elapsed time increments; per-date seconds visible; speedup displays a reasonable number (e.g., 1.0 to 5.0x, not 0 or NaN); code check: `apps/frontend/app/data/page.tsx` has no `speedupFactor()` division.

---

### TC-22 — Browser: Partial job shows per-date failure detail

**Type:** browser
**Preconditions:** A job has completed with status "partial" (one or more dates failed during backfill).

**Steps:**
1. Navigate to `/data` and locate the completed partial job in Run history.
2. Click the job to expand or view detail.
3. Verify a "Failed dates" or "Per-date errors" section is visible.
4. Inspect one or more rows showing the failed date and the error message.

**Expected outcome:** The user can diagnose which dates failed and why.
**Pass criteria:** At least one failed date is listed; error message is non-empty and informative; other dates are marked ok or skipped.

---

### TC-23 — Browser: No counter exceeds its total

**Type:** browser
**Preconditions:** A multi-window job is running or has completed (e.g., 6 symbols × 3 months = 18 chunks).

**Steps:**
1. Navigate to `/data` and watch the live job card or view a completed job detail.
2. Inspect all counter fields (symbols, bars, days, chunks, etc.).
3. Verify no displayed number exceeds its total (e.g., "Symbols: 6/6", not "9/6").

**Expected outcome:** All counters are credible.
**Pass criteria:** For every visible counter, `value <= total`; refresh multiple times and verify the invariant holds.

---

## Summary

**Total test cases:** 23
**API tests:** 15 (TC-01 through TC-15)
**Browser tests:** 8 (TC-16 through TC-23)
**Artifact checks:** 0

All test cases map directly to the iteration's four target journeys:
- **J-59:** TC-01, TC-02, TC-03, TC-04, TC-05 (stage-aware checkpoint + covered-range planner)
- **J-60:** TC-06, TC-07, TC-08 (job lifecycle record + boot sweep)
- **J-66:** TC-09, TC-10, TC-11, TC-12, TC-20, TC-21, TC-23 (fine-grained progress, current-activity, heartbeat, speedup)
- **J-67:** TC-13, TC-14, TC-15 (per-date failure isolation, parallel transaction soundness, byte-identity)

Browser tests (TC-16 through TC-23) corroborate the backend implementation on the `/data` UI surfaces (Unfinished-imports, Run history, live job card).
