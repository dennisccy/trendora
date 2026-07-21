# goal-ops-hardening-iter-7 Functional Test Plan

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Frontend Present:** yes

## Phase Goal

Close J-06's last residual gap: warm `/evidence`'s `drawdown_expectations` cache at ingest time, ensuring the page loads within budget on its first view after an ingest completes, not only on subsequent warm views.

---

## Test Cases

### TC-01 — Ingest warm step produces cache entries and updates aggregates list

**Type:** api
**Preconditions:** 
- Backend running with no prior ingest
- Ledger file contains at least one non-`FORWARD_WALK_TYPE` claim entry
- `_refresh_ingest_aggregates` hook is executed as part of a `backfill`/`both`/`rebuild` job

**Steps:**
1. Trigger a `backfill` or `both` ingest job via `POST /api/data/jobs` with a date range that will execute the finalize hook
2. Wait for the job to complete (poll `GET /api/data/jobs/{job_id}` until `status=completed`)
3. Query the database: `SELECT * FROM event_study_cache WHERE view_name='drawdown_expectations'`
4. Check the job's returned `aggregates_refreshed` list from the job-completed response

**Expected outcome:** 
- At least one `EventStudyCache` row exists with `view_name='drawdown_expectations'` per claim that was warmed
- The job's `aggregates_refreshed` list includes the string `"drawdown_expectations"`

**Pass criteria:** Both conditions are true: (a) ≥1 `EventStudyCache` row with `view_name='drawdown_expectations'` exists in DB before job marked completed, (b) `"drawdown_expectations"` appears in the job's returned `aggregates_refreshed` list

---

### TC-02 — `/evidence` loads within warm budget on first view after ingest

**Type:** browser
**Preconditions:**
- Backend running in prod mode (`scripts/start-backend.sh`)
- Frontend running in prod mode (`scripts/start-frontend.sh`)
- A fresh ingest job (`backfill`/`both`/`rebuild`) has just completed
- In-process cache has been cleared (e.g. new backend process or explicit cache flush)

**Steps:**
1. Trigger a real ingest job: POST `http://localhost:5000/api/data/jobs` with kind `backfill`, start/end dates spanning ≥1 trading day
2. Poll `http://localhost:5000/api/health` until job completes (status=`ready` + previous job_status != `running`)
3. Open a new browser tab; navigate to `http://localhost:3000/evidence`
4. Measure time-to-interactive (first paint + main content visible) from navigation start to final render
5. Record the measurement

**Expected outcome:** 
- Page loads and renders all claim rows and their expectations panels (if any) within 3 seconds (per `reports/perf-budgets.md` Item I warm budget for `/evidence`)
- No "loading" spinner persists beyond the timeout
- No blank page or error state

**Pass criteria:** Measured time ≤ 3.0 seconds for first view immediately after ingest (not a warm-cache re-measurement)

---

### TC-03 — Warmed cache payload is byte-identical to fresh computation

**Type:** api
**Preconditions:**
- Backend running
- Ingest-time warm has just completed (TC-01 confirms entries exist)
- A test claim exists in the evidence ledger

**Steps:**
1. Retrieve a claim ID from the warmed `EventStudyCache` rows: `SELECT subject FROM event_study_cache WHERE view_name='drawdown_expectations' LIMIT 1`
2. Extract the claim dict from the ledger entry (matching the subject hash)
3. Call `GET /api/evidence` and locate the claim's `expectations` panel in the response JSON
4. In the same backend process, call the internal `compute_drawdown_expectations(session, claim, cfg)` function (not cached) with the same claim
5. Compare the two payloads field-for-field

**Expected outcome:** 
- Both payloads are identical: same field names, same values, same structure
- No rounding errors or precision differences

**Pass criteria:** `json.dumps(warmed_payload, sort_keys=True) == json.dumps(fresh_payload, sort_keys=True)` (or equivalent byte-for-byte comparison)

---

### TC-04 — Unresolvable claims and exceptions are handled gracefully

**Type:** api
**Preconditions:**
- Backend running
- Ledger contains at least one claim that will fail to resolve (e.g. cohort has no matching securities) and optionally a claim whose warm call will raise an exception (via test monkeypatch)

**Steps:**
1. Trigger a `backfill` ingest job containing the unresolvable claim
2. Monitor the backend logs: confirm the warm loop logs a message for the unresolvable/erroring claim (e.g. `"Skipping claim ... : ..."`)
3. Check that the job completes successfully (does not abort)
4. Query the ledger and render `/api/evidence`: the unresolvable claim's row appears without an `expectations` panel
5. Verify no `EventStudyCache` row was created for that claim with `view_name='drawdown_expectations'`

**Expected outcome:** 
- Ingest job completes without raising an exception
- Backend logs show a non-fatal skip message for the unresolvable claim
- The claim renders on `/evidence` with no `expectations` panel (not a crash, not a fabricated panel)
- `"drawdown_expectations"` still appears in the job's `aggregates_refreshed` list (at least one other claim was warmed)

**Pass criteria:** (a) Job completes, (b) Log contains skip message, (c) `/evidence` renders without error, (d) No fabricated expectations value for the unresolvable claim

---

### TC-05 — Empty ledger results in honest zero-warm omission

**Type:** api
**Preconditions:**
- Backend running
- Ledger file is missing, empty, or contains only `FORWARD_WALK_TYPE` entries (all filtered out)

**Steps:**
1. Trigger a `backfill`/`both`/`rebuild` ingest job with an empty/no-claims ledger
2. Wait for job completion
3. Check the returned `aggregates_refreshed` list
4. Monitor backend logs: confirm zero warm calls were logged for drawdown_expectations

**Expected outcome:** 
- Job completes successfully
- `"drawdown_expectations"` does NOT appear in the `aggregates_refreshed` list
- No debug logs show warming attempts for this category

**Pass criteria:** `"drawdown_expectations"` is honest absent from `aggregates_refreshed` when zero claims were available to warm

---

### TC-06 — All 11 J-06 pages load within committed budgets (real browser, full set)

**Type:** browser
**Preconditions:**
- Backend running in prod mode (`scripts/start-backend.sh`)
- Frontend running in prod mode (`scripts/start-frontend.sh`)
- A warm backend (at least one full ingest cycle completed to populate aggregates)
- No artificial clock skew or network throttling

**Steps:**
1. Navigate to each of the following 11 pages in a real browser, recording time-to-interactive for each:
   - `/` (home/dashboard)
   - `/stocks` (stocks list)
   - `/stocks/AAPL` (individual stock detail)
   - `/sectors` (sectors view)
   - `/themes` (themes view)
   - `/data` (data jobs panel)
   - `/evidence` (evidence/claims panel)
   - `/scanner-runs` (historical scanner runs)
   - `/backtest` (backtest results)
   - `/watchlist` (watchlist)
   - `/research/<lab-id>` (one research lab, e.g. `/research/regime`)
2. For each page, measure time from navigation start to main content visible (first paint + critical API responses loaded)
3. Record all measurements and compare against `reports/perf-budgets.md` committed budgets
4. Re-measure any page that was previously marginal (near budget limit) up to 3 additional times to confirm stability

**Expected outcome:** 
- Every page loads and renders its primary content within its committed `reports/perf-budgets.md` budget
- No page shows "loading" spinner beyond timeout
- All API responses return successfully

**Pass criteria:** All 11 pages measure ≤ their committed budget in `reports/perf-budgets.md`, and new `/evidence` first-view measurement (taken post-ingest) is ≤ 3.0s

---

### TC-07 — Unit and integration tests pass with zero failures

**Type:** api
**Preconditions:**
- Code has been implemented
- Test environment is configured with the isolated TMPDIR

**Steps:**
1. Run the command: `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_forward_testing.py apps/backend/tests/test_api_backtest.py apps/backend/tests/test_mcp_window.py -v 2>&1`
2. Capture stdout and stderr
3. Count the pass/fail/error results

**Expected outcome:** 
- All tests complete without hanging or timing out
- Zero failures (F)
- Zero errors (E)

**Pass criteria:** Test command exit code = 0; pytest output shows "X passed" with no failures or errors

---

### TC-08 — Required-still-passing journeys remain green

**Type:** api
**Preconditions:**
- J-01 and J-03 golden replay scripts exist in `runs/goal-session-ops-hardening/`
- Backend running in prod mode
- Frontend running in prod mode

**Steps:**
1. Execute J-01's golden replay script: `python3 runs/goal-session-ops-hardening/replay-scripts/j-01-replay.py` (or equivalent path)
2. Check the exit code and any returned pass/fail summary
3. Execute J-03's golden replay script: `python3 runs/goal-session-ops-hardening/replay-scripts/j-03-replay.py`
4. Check the exit code and summary

**Expected outcome:** 
- Both replay scripts complete without errors
- Both return a "PASS" verdict (all steps succeeded)
- No step failures attributable to iter-7's code changes

**Pass criteria:** Both J-01 and J-03 replay scripts return exit code 0 and report PASS

---

## Summary

| Count | Type | Description |
|-------|------|-------------|
| 8 | Total test cases | — |
| 4 | API tests | TC-01, TC-03, TC-04, TC-05, TC-07 (unit); TC-02, TC-06 (integration via browser); TC-08 (replay) |
| 3 | Browser tests | TC-02 (first-view latency), TC-06 (all 11 pages), TC-08 (replay pass) |
| 1 | Unit/integration tests | TC-07 (pytest suite) |

**Test execution order:**
1. TC-01 (verify warm hook runs and creates cache entries)
2. TC-03 (verify warmed value matches fresh compute)
3. TC-04 (verify error handling)
4. TC-05 (verify empty-ledger edge case)
5. TC-07 (verify unit tests pass)
6. TC-02 (browser: first-view latency post-ingest)
7. TC-06 (browser: all 11 pages budget check)
8. TC-08 (replay: J-01, J-03 still pass)

All tests must pass for the iteration to close J-06 successfully.
