# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15  
**Date:** 2026-06-14  
**Frontend Present:** yes

## Phase Goal

Fix the Data Manager's multi-month backfill crash (`'committed'`-session error in transaction orchestration), and make data removal a deliberate, range-scoped, accident-proof flow (both dates mandatory, counts-only confirm, persistently visible button).

## Test Cases

### TC-01 — Multi-month backfill completes without committed-session crash

**Type:** api  
**Preconditions:** Backend is running; test DB is seeded with bars for a range (e.g., 3+ months of OHLCV data).

**Steps:**
1. Call `POST /api/data/jobs` with `action: "backfill"`, `start: "2025-01-01"`, `end: "2025-03-31"`, `backfill_workers: 2` (parallel)
2. Poll `GET /api/data/jobs/{job_id}` every 5 seconds until terminal state
3. Inspect the final `data_provider_runs` and `scanner_runs` tables for the date range

**Expected outcome:** Job completes with terminal state `ok` or `partial` (if a date forced-failed); the job row records no `'committed'`-state error in its `errors[]` field.

**Pass criteria:** `job.status` is `"ok"` or `"partial"`; `errors[]` does not contain `"'committed'"` or `"invalid state"` substring; `scanner_runs` shows a row for each date in the range.

---

### TC-02 — Per-date failure isolation (forced single-date failure)

**Type:** api  
**Preconditions:** Backend is running; a mechanism exists to force a provider failure on one specific date (mock or environment override).

**Steps:**
1. Call `POST /api/data/jobs` with `action: "backfill"`, `start: "2025-01-15"`, `end: "2025-01-20"`, forcing a provider error on `2025-01-17`
2. Poll `GET /api/data/jobs/{job_id}` until terminal state
3. Query `scanner_runs` where `date` is in the range
4. Inspect the job's progress/error log

**Expected outcome:** Job completes with terminal state `partial`; the `2025-01-17` date row in `scanner_runs` has `status: "failed"` with an error message; other dates (e.g., `2025-01-15`, `2025-01-16`, `2025-01-18`, `2025-01-20`) have `status: "ok"`.

**Pass criteria:** `job.status == "partial"`; exactly one `scanner_run` row has `status == "failed"` (the forced-failure date); at least 4 other dates have `status == "ok"` (isolation confirmed).

---

### TC-03 — Create-once idempotency (re-run same range creates no new snapshots)

**Type:** api  
**Preconditions:** TC-01 has completed successfully (multi-month range is persisted); backend is running.

**Steps:**
1. Record the count of `scanner_runs` rows for the date range `2025-01-01` to `2025-03-31` from TC-01
2. Call `POST /api/data/jobs` with the same `action: "backfill"`, `start: "2025-01-01"`, `end: "2025-03-31"`
3. Poll `GET /api/data/jobs/{job_id}` until terminal state
4. Verify the new job's progress logs report "0 new snapshots" or "already exists"

**Expected outcome:** Second job completes with terminal `ok`; no new rows inserted into `scanner_runs` for dates already covered; the job does not raise a UNIQUE constraint error.

**Pass criteria:** `job.status == "ok"`; the `scanner_runs` count for the range is identical before and after the re-run; no UNIQUE constraint error in the job's error log; progress shows "0 new snapshots created" or equivalent.

---

### TC-04 — Byte-identical outputs: parallel == sequential

**Type:** api  
**Preconditions:** Backend is running; test data available for a multi-month range (e.g., `2025-01-01` to `2025-02-28`).

**Steps:**
1. Call `POST /api/data/jobs` with `action: "backfill"`, `start: "2025-01-01"`, `end: "2025-02-28"`, `backfill_workers: 1` (sequential)
2. Wait for job to complete; record the `scanner_runs` rows and their checksums (score 0–100 values, setup status, leadership/entry/risk buckets)
3. Call `POST /api/data/jobs` with the same range but `backfill_workers: 4` (parallel)
4. Wait for job to complete; compare `scanner_runs` rows to the sequential run

**Expected outcome:** Parallel and sequential outputs are byte-identical for all snapshots in the range (same regime score, same top-ranked stocks, same A–E buckets).

**Pass criteria:** `MD5(sorted(scanner_runs rows for range)) == MD5(sequential run) AND MD5(...) == MD5(parallel run)`; all Leadership/Entry/Risk scores and buckets match exactly.

---

### TC-05 — POST /api/data/remove rejects single-ended date scope

**Type:** api  
**Preconditions:** Backend is running; `/data` removal endpoint is available.

**Steps:**
1. Call `POST /api/data/remove` with `{ "start": "2025-01-15" }` (missing `end`)
2. Verify the HTTP response status and `detail` field
3. Call `POST /api/data/remove` with `{ "end": "2025-01-20" }` (missing `start`)

**Expected outcome:** Both calls return HTTP 4xx (400 or 422); each includes a `detail` field that explicitly says a date range requires both `start` and `end`.

**Pass criteria:** HTTP status is 400 or 422; `response.json()["detail"]` contains substring "both" or "start and end" or similar; the error is not a generic validation message.

---

### TC-06 — POST /api/data/remove rejects empty scope

**Type:** api  
**Preconditions:** Backend is running.

**Steps:**
1. Call `POST /api/data/remove` with `{ }` (empty dict or no date fields)
2. Call `POST /api/data/remove` with `{ "start": null, "end": null }`

**Expected outcome:** Both calls return HTTP 4xx; the `detail` field explicitly mentions that a removal scope is required.

**Pass criteria:** HTTP status is 4xx; `detail` contains "required" or "scope" or similar.

---

### TC-07 — POST /api/data/remove accepts valid range-only (no symbols field)

**Type:** api  
**Preconditions:** Backend is running; user-added bars exist in the range `2025-02-01` to `2025-02-15` (bars beyond the committed seed).

**Steps:**
1. Call `POST /api/data/remove/preview` with `{ "start": "2025-02-01", "end": "2025-02-15" }` (no `symbols` field)
2. Inspect the response `removable_bar_count`, `removable_symbol_count`, `cascade_snapshot_count`

**Expected outcome:** The preview returns HTTP 200; the impact counts are non-zero integers matching the real computation.

**Pass criteria:** HTTP status is 200; `removable_bar_count > 0`; `removable_symbol_count > 0`; `cascade_snapshot_count >= 0` (exact counts match a manual verification of affected snapshots).

---

### TC-08 — POST /api/data/remove committed-seed protection unchanged

**Type:** api  
**Preconditions:** Backend is running; committed-seed bars exist for `AAPL` in the range `2024-01-01` to `2024-12-31`.

**Steps:**
1. Call `POST /api/data/remove/preview` with `{ "start": "2024-01-01", "end": "2024-12-31" }` (committed-seed date range)
2. Inspect the response `reason` field (should indicate the range contains only committed seed)

**Expected outcome:** The preview returns HTTP 200 with a `refused: true` or `reason` field that explains the range is entirely seed and cannot be removed.

**Pass criteria:** `preview.refused == true` or `reason` contains "committed seed" or "cannot remove"; no bars are marked removable; the flow preserves J-39 seed-safe semantics.

---

### TC-09 — Remove panel has NO symbols input

**Type:** browser  
**Preconditions:** Frontend is running on `localhost:3000`; user is on `/data` page.

**Steps:**
1. Open `/data` in Chrome
2. Locate the Remove panel (the panel labeled "Remove imported data" or similar)
3. Inspect the input fields visible in the panel
4. Take a screenshot of the entire Remove panel

**Expected outcome:** The Remove panel displays exactly two ISO date inputs (`From` and `To`); no text input or dropdown for "symbols" is present.

**Pass criteria:** Screenshot shows two date input fields only; no "symbols", "symbol list", or "pick symbols" field is visible; panel is compact and label-clear.

---

### TC-10 — Remove panel: button disabled with one date, enabled with both

**Type:** browser  
**Preconditions:** Frontend is running; user is on `/data` page.

**Steps:**
1. Open `/data`; locate the Remove panel
2. Verify the Preview/Remove button state (disabled or enabled initially)
3. Enter only a `From` date (e.g., `2025-02-01`); screenshot the button
4. Enter the `To` date (e.g., `2025-02-15`); screenshot the button
5. Clear the `To` date; verify the button is disabled again

**Expected outcome:** Button is disabled with zero or one date filled; button becomes enabled only when both `From` and `To` are non-empty, valid ISO dates (`yyyy-MM-dd`); clearing either date disables the button.

**Pass criteria:** Captured screenshots show button in disabled state with one date and enabled state with both; button state changes immediately on input without a form submission.

---

### TC-11 — Confirm modal renders counts only, Confirm button visible without scrolling

**Type:** browser  
**Preconditions:** Frontend is running; user is on `/data` with the Remove panel; a small safe user-added range exists (e.g., `2025-02-01` to `2025-02-05`).

**Steps:**
1. In the Remove panel, enter `From: 2025-02-01` and `To: 2025-02-05`
2. Click the Preview button
3. Wait for the confirm modal to appear
4. Inspect the modal body; take a screenshot of the entire modal
5. Scroll within the modal (if possible); verify the Confirm button is always visible at the bottom

**Expected outcome:** The modal displays a compact header (`"Remove data from 2025-02-01 to 2025-02-05"` or similar), a body with four counts (removable bar count, affected-symbol count, cascade snapshot count, restated date range), and a Confirm button in the footer. The Confirm button does NOT require scrolling to reach.

**Pass criteria:** Modal screenshot shows counts only (no `removable_symbols` list, no `not_removable_by_symbol` enumeration); Confirm button is visible in the footer area without requiring the user to scroll the modal content; the body text is clear and concise.

---

### TC-12 — After Confirm, coverage + heatmap refresh

**Type:** browser  
**Preconditions:** Frontend is running; user is on `/data`; the availability heatmap and coverage table are visible; a small test range has been prepared (e.g., user-added bars for `2025-02-01` to `2025-02-05`).

**Steps:**
1. Record the heatmap state and coverage counts before removal
2. In the Remove panel, enter `From: 2025-02-01`, `To: 2025-02-05`
3. Click Preview; review and click Confirm in the modal
4. Wait for the removal to complete (observe job-card completion)
5. Verify that the heatmap symbols-with-bars counts and snapshot markers have updated
6. Verify that the coverage table (if visible) reflects the removal

**Expected outcome:** After Confirm, the job completes with `ok` status; the heatmap's per-date bar counts decrease for the removed range; any affected snapshot dates are no longer marked with a snapshot indicator (or are updated).

**Pass criteria:** Heatmap counts decrease for dates `2025-02-01` to `2025-02-05`; at least one date's snapshot marker disappears (cascade); coverage table (if shown) updates to reflect the lower bar count post-removal.

---

### TC-13 — Backend immutability + no-lookahead suites still pass (J-41, J-53, J-67)

**Type:** artifact  
**Preconditions:** Backend test suite is available and can run in isolation.

**Steps:**
1. Run the backend pytest suite, focusing on the modules: `test_create_once_idempotency`, `test_parallel_vs_sequential_equality`, `test_immutability`, `test_no_lookahead`
2. Capture the test output (pass/fail count)

**Expected outcome:** All immutability, no-lookahead, create-once, and parallel-vs-sequential tests pass (green).

**Pass criteria:** pytest exit code is 0; all four test suites (or their equivalents for J-41, J-53, J-67) report 100% pass rate.

---

### TC-14 — Heatmap endpoint (J-61) still reads and refreshes after removal

**Type:** api  
**Preconditions:** Backend is running.

**Steps:**
1. Call `GET /api/data/availability` before a removal
2. Record the per-date symbols-with-bars counts
3. Perform a removal via `POST /api/data/remove` for a range
4. Call `GET /api/data/availability` again
5. Compare the counts

**Expected outcome:** The endpoint returns the same structure before and after; the counts for removed-range dates decrease post-removal.

**Pass criteria:** `GET /api/data/availability` returns HTTP 200 both times; the counts for the removal range are lower after the job completes; the structure (date, count, snapshot_exists) is consistent.

---

## Summary

Total test cases: 14  
API tests: 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-14)  
Browser tests: 4 (TC-09, TC-10, TC-11, TC-12)  
Artifact checks: 1 (TC-13)
