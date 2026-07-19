# Goal Ops-Hardening Iter-1 Functional Test Plan

**Phase:** goal-ops-hardening-iter-1  
**Date:** 2026-07-19  
**Frontend Present:** yes

## Phase Goal

An operator can request a backfill over any explicit date range — including spans over 370 days — and see every requested trading day actually targeted, chunked progress that is never rejected for size, and an honest, visually distinct explanation for zero-work outcomes that survives a page reload.

## Test Cases

### TC-01 — May-2026 backfill produces correct breakdown counts

**Type:** browser  
**Preconditions:**
- Backend running with committed seed (`snapshot_cadence.daily_start=2026-06-01`, no May-2026 snapshots exist)
- `/data` page accessible in browser
- No prior jobs started in this session

**Steps:**
1. Navigate to `/data`
2. Set job kind to `backfill`
3. Set start date to 2026-05-02, end date to 2026-05-29
4. Click "Start" button
5. Wait for job to complete (observe status changes from "running" to "ok")
6. Record the displayed summary values: `dates_total`, `snapshots_created`, `already_snapshotted`, `non_trading_days`, `calendar_days`

**Expected outcome:** Job completes with status "ok"; summary shows exactly `dates_total=19`, `snapshots_created=19`, `already_snapshotted=0`, `non_trading_days=9`, `calendar_days=28`

**Pass criteria:** All six summary fields match the expected values exactly; no 4xx/5xx API errors during job submission or polling

---

### TC-02 — Scanner runs created for backfill completion

**Type:** browser  
**Preconditions:** TC-01 has completed successfully

**Steps:**
1. From `/data`, navigate to `/scanner-runs`
2. Observe the runs list
3. Verify that runs exist for at least the dates: 2026-05-04, 2026-05-15, 2026-05-29
4. Click on one of these runs (e.g., 2026-05-04)
5. Verify the leaderboard loads with that as-of date's data

**Expected outcome:** At least three runs exist in the list with the expected dates; clicking a run renders a leaderboard with that as-of date

**Pass criteria:** All three expected dates appear in the runs list; leaderboard renders without 5xx errors

---

### TC-03 — Weekend-only backfill renders distinct zero-work state

**Type:** browser  
**Preconditions:**
- Backend running
- `/data` page accessible
- Current browser session has no prior jobs

**Steps:**
1. Navigate to `/data`
2. Set job kind to `backfill`
3. Set start date to 2026-05-02 (Friday), end date to 2026-05-03 (Saturday)
4. Click "Start"
5. Wait for job to complete
6. Observe the job status badge and summary display
7. Compare visual styling to a green "ok" badge — verify it is NOT the same green color

**Expected outcome:** Job completes with status "ok"; summary shows `dates_total=0`, `calendar_days=2`, `non_trading_days=2`; status badge is rendered in a visually distinct style (neutral/gray, not plain green)

**Pass criteria:** Summary fields are exact; badge is visually distinct from a plain green success badge (verified by color or label text, not a vague inspection)

---

### TC-04 — Identical re-run of completed backfill shows zero-work with all already-snapshotted

**Type:** browser  
**Preconditions:** TC-01 has completed; the May-2026 backfill snapshots still exist in the DB

**Steps:**
1. Navigate to `/data`
2. Set job kind to `backfill`
3. Set start date to 2026-05-02, end date to 2026-05-29 (same as TC-01)
4. Click "Start"
5. Wait for job to complete
6. Record the summary: `dates_total`, `snapshots_created`, `already_snapshotted`, `non_trading_days`, `calendar_days`
7. Observe the job status badge styling

**Expected outcome:** Job completes with status "ok"; summary shows `snapshots_created=0`, `already_snapshotted=19`, `non_trading_days=9`, `dates_total=19`, `calendar_days=28`; status badge is rendered in the same distinct zero-work style as TC-03

**Pass criteria:** Summary fields match exactly; badge styling matches the zero-work badge from TC-03

---

### TC-05 — Page reload preserves all run history and removes empty-session copy

**Type:** browser  
**Preconditions:** TC-01, TC-03, and TC-04 have all completed in the same browser session

**Steps:**
1. From `/data`, observe the Run history table; count and note all visible runs
2. Reload the page (F5 or refresh button)
3. After page loads, observe the Run history table again
4. Verify the exact same runs are still listed with the same status/counts
5. Check the Job progress panel for any text that says "No job has been started this session"
6. Verify that text does NOT appear on the page

**Expected outcome:** All three prior runs are still listed with matching status and counts; the literal text "No job has been started this session" does not appear anywhere

**Pass criteria:** Run history table is identical before and after reload; text search finds zero occurrences of "No job has been started this session"

---

### TC-06 — Fresh page load with history-but-no-session-job shows latest persisted run

**Type:** browser  
**Preconditions:**
- TC-01 and TC-04 have completed and snapshots exist in the DB
- Open a fresh incognito/private browser window (new session)
- Navigate to `/data`

**Steps:**
1. On page load, observe the Job progress panel (the top section showing current job status)
2. Check that it displays the latest persisted run's status, summary, and breakdown fields
3. Verify the run count, dates_total, and other fields are visible
4. Verify no panel displays "No job has been started this session"

**Expected outcome:** Job progress panel renders the most recent persisted run's data (not an empty "no job started" state); the run's status badge and breakdown are visible

**Pass criteria:** All summary fields from the latest persisted run are displayed; zero occurrences of the empty-session copy text

---

### TC-07 — Large (>370 day) backfill request is accepted without rejection

**Type:** browser  
**Preconditions:**
- Backend running
- `/data` page accessible

**Steps:**
1. Navigate to `/data`
2. Set job kind to `backfill`
3. Set start date to 2025-06-01, end date to 2026-07-17 (412 calendar days)
4. Click "Start"
5. Observe the API response and job creation; record the created job's `chunk_total` field

**Expected outcome:** API returns 200/201 (no 4xx rejection); job is created; `chunk_total` is populated and > 1

**Pass criteria:** No "date range too large" or "span_days > max" error message appears; `chunk_total` is an integer > 1

---

### TC-08 — Large backfill's progress advances with chunk tracking

**Type:** browser  
**Preconditions:** TC-07 has just been submitted; job is currently running

**Steps:**
1. From `/data`, observe the Job progress panel
2. Verify `chunk_index` and `chunk_total` are displayed
3. Poll the page every 2-3 seconds for 30 seconds
4. Record the progression of `chunk_index` (should advance from 0 to 1+)
5. Record the progression of `dates_done` (should advance above 0)
6. Check the `job.errors` field for any entries mentioning "range" or "cap"

**Expected outcome:** `chunk_index` advances to at least 1; `dates_done` advances above 0; no range/cap related errors appear

**Pass criteria:** `chunk_index >= 1`; `dates_done > 0`; `job.errors` contains no cap-related messages

---

### TC-09 — max_range_days is removed from config and test fixtures

**Type:** artifact  
**Preconditions:** None

**Steps:**
1. Read `apps/backend/app/config.py` and search for `max_range_days` field in `DataManagerCfg`
2. Read `config.yaml` and search for the `max_range_days` entry
3. Read `apps/backend/tests/test_data_manager.py` (lines ~491-518) and verify no cap-rejection tests exist
4. Read `apps/backend/tests/test_api_data.py` (lines ~294-310) and verify no cap-rejection tests exist
5. Read `apps/backend/tests/test_config.py` (lines ~23, ~477-485) and verify no `max_range_days` fixture key
6. Read `apps/backend/tests/test_themes.py`, `test_sectors.py`, `test_indexes.py` (named locations) and verify no `"max_range_days": 370` in fixture dicts

**Expected outcome:** `max_range_days` field is absent from `DataManagerCfg` class definition; `config.yaml` has no entry for it; none of the 6 named test files contain the old cap-rejection contract or stray fixture values

**Pass criteria:** Grep for `max_range_days` in all files returns zero matches in production code and config; test files contain zero occurrences

---

### TC-10 — Rebuild job remains cadence-filtered (unchanged behavior)

**Type:** api  
**Preconditions:**
- Backend running
- At least one `rebuild` job has been created via `POST /api/data/jobs` with kind="rebuild"

**Steps:**
1. Submit a `rebuild` job request: `curl -X POST http://localhost:8000/api/data/jobs -H "Content-Type: application/json" -d '{"kind":"rebuild","symbols":["SPY"]}'`
2. Poll `GET /api/data/jobs/{job_id}` until the job completes
3. Record the `dates_total` field from the final job summary
4. Verify that only dates matching `_cadence_allowed_dates` (i.e., dates matching `snapshot_cadence.daily_start` cadence, not all trading days in a range) are included in the target set

**Expected outcome:** Rebuild job executes with unchanged cadence-filtered target selection (no new dates beyond what `snapshot_cadence` permits); `dates_total` reflects the cadence filter, not an explicit range

**Pass criteria:** Rebuild targets are consistent with pre-iteration behavior (cadence-filtered only); no new dates outside the cadence appear in the executed snapshot set

---

### TC-11 — All-non-trading-day backfill completes without error_other penalty

**Type:** api  
**Preconditions:**
- Backend running
- Historical calendar data exists

**Steps:**
1. Submit a backfill request for a weekend-only range (or any all-non-trading-day span): `curl -X POST http://localhost:8000/api/data/jobs -H "Content-Type: application/json" -d '{"kind":"backfill","start":"2026-05-02","end":"2026-05-03"}'`
2. Poll the job until completion
3. Read the final summary from `GET /api/data/jobs/{job_id}`
4. Record `error_other`, `dates_total`, and `non_trading_days`
5. Check the persisted job record in the database for `date_failures` entries (should be none for a pure weekend)

**Expected outcome:** Job completes with `error_other=0`; `dates_total=0`; `non_trading_days=2` (for a 2-day weekend); no per-date failures are recorded

**Pass criteria:** `error_other=0`; `dates_total=0`; the persisted `message` JSON blob contains no `date_failures` entries for days that are genuinely non-trading

---

### TC-12 — Breakdown fields satisfy invariants

**Type:** api  
**Preconditions:**
- A completed backfill/rebuild job exists with all breakdown fields populated
- Job kind is backfill, both, or rebuild

**Steps:**
1. Poll `GET /api/data` to fetch the latest run summary
2. Read the fields: `calendar_days`, `non_trading_days`, `dates_total`, `snapshots_created`, `already_snapshotted`, `error_other`
3. Compute invariant 1: `non_trading_days + dates_total` and verify it equals `calendar_days`
4. Compute invariant 2: `snapshots_created + already_snapshotted + error_other` and verify it equals `dates_total`

**Expected outcome:** Both invariants hold exactly (no rounding, no approximation)

**Pass criteria:** Invariant 1 equals 0 (no difference); Invariant 2 equals 0 (no difference)

---

### TC-13 — Regression check: Fast boot and phase-aware badge still work

**Type:** browser  
**Preconditions:**
- Backend has been restarted during this test session
- `/data` page is accessible

**Steps:**
1. Navigate to `/data` immediately after backend startup
2. Observe the Job progress panel for a "phase-aware initializing" or similar badge (per J-04)
3. Measure page load time; it should be sub-second for the initial render
4. Verify the page renders without a blank white screen or unrecoverable error

**Expected outcome:** Page loads quickly (< 2 seconds); initializing badge appears if expected; page is fully interactive

**Pass criteria:** Initial render completes < 2 seconds; no 5xx page errors; initializing state is visually correct if present

---

### TC-14 — Regression check: Interrupted job state persists and resumes

**Type:** browser  
**Preconditions:**
- A backfill job has been started
- The backend is stopped before the job completes

**Steps:**
1. Start a backfill job on `/data`
2. Allow it to run for 5+ seconds
3. Stop the backend (e.g., `pkill -f uvicorn`)
4. Observe the job status on `/data` (should show "interrupted" or similar)
5. Restart the backend
6. Reload `/data` page
7. Verify the interrupted job is still listed and its status badge is distinct from "ok" and "failed"

**Expected outcome:** Interrupted job remains visible after restart; status badge is neutral/distinct and not confused with success or failure

**Pass criteria:** Interrupted state persists across restart; badge is visually distinct from both "ok" (green) and "failed" (red)

---

## Summary

**Total test cases:** 14

**Test case breakdown:**
- Browser tests: 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-13, TC-14)
- API tests: 4 (TC-09, TC-10, TC-11, TC-12)
- Artifact checks: 1 (TC-09)

**Key coverage areas:**
- Correct breakdown arithmetic for a normal backfill (TC-01, TC-02)
- Zero-work state distinct visual appearance (TC-03, TC-04)
- History persistence and reload correctness (TC-05, TC-06)
- Large backfill acceptance and chunking (TC-07, TC-08)
- Config/fixture removal validation (TC-09)
- Rebuild unchanged behavior (TC-10)
- Edge case: all-non-trading-day range (TC-11)
- Invariant verification (TC-12)
- Regression checks for J-04 sub-behaviors (TC-13, TC-14)
