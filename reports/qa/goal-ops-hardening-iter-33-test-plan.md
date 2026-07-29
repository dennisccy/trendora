# Goal Iteration 33 Functional Test Plan

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Frontend Present:** yes

## Phase Goal

Fix `scripts/start-frontend.sh` to genuinely serve production mode (currently executes `npx next dev`), then run and record the real-browser 11-page time-to-interactive sweep that bug has blocked for the session, closing J-06.

## Test Cases

### TC-01 — Frontend launcher rebuilds when `.next` is stale or missing

**Type:** api
**Preconditions:** 
- `apps/frontend/.next` either missing or older than `apps/frontend/` sources / `package.json` / lockfile
- `NEXT_DIST_DIR` points to a scratch directory (test isolation)
- Backend running and healthy

**Steps:**
1. Invoke `scripts/start-frontend.sh` with stale/missing `.next` build
2. Capture script output and exit code
3. Use `ps aux` to identify the process listening on `FRONTEND_PORT`
4. Verify process is `next start` by reading its `/proc/<pid>/cmdline`
5. Confirm the script completes with exit code 0

**Expected outcome:** 
- Script runs `next build` before `next start`
- No error output from build
- Process bound to `FRONTEND_PORT` is genuinely `next start` (not `next dev`)

**Pass criteria:** 
- `next build` completes cleanly with exit code 0
- `/proc/<pid>/cmdline` contains `next start` (not `next dev`)
- Port is correctly configured to `FRONTEND_PORT`

---

### TC-02 — Frontend launcher skips rebuild when `.next` is current

**Type:** api
**Preconditions:**
- `apps/frontend/.next` exists and is newer than all sources / `package.json` / lockfile
- `NEXT_DIST_DIR` points to a scratch directory
- Backend running and healthy

**Steps:**
1. Record mtime of `.next/BUILD_ID` before invoking script
2. Invoke `scripts/start-frontend.sh`
3. Record elapsed time for process to become responsive on `FRONTEND_PORT`
4. Verify mtime of `.next/BUILD_ID` has NOT changed
5. Capture process identity via `/proc/<pid>/cmdline`

**Expected outcome:**
- Script detects current build and skips `next build` step
- Process starts rapidly (significantly faster than TC-01's build step)
- No rebuild occurs (BUILD_ID mtime unchanged)

**Pass criteria:**
- `.next/BUILD_ID` mtime is identical before and after script run
- Process startup completes in <5 seconds (no build overhead)
- Process is `next start` (not `next dev`)

---

### TC-03 — Frontend launcher fails cleanly on broken source

**Type:** api
**Preconditions:**
- `apps/frontend` has a deliberately introduced TypeScript/build error
- `NEXT_DIST_DIR` points to a scratch directory
- No pre-existing `next dev` or `next start` process running on `FRONTEND_PORT`

**Steps:**
1. Introduce a syntax/type error in an `apps/frontend` source file (e.g., invalid TypeScript)
2. Invoke `scripts/start-frontend.sh` and capture output + exit code
3. Wait 10 seconds and check for any process listening on `FRONTEND_PORT`
4. Use `ps aux` to verify no `next dev` or stale `next start` remains
5. Restore the broken file to its original state (cleanup)

**Expected outcome:**
- Script exits with non-zero exit code
- Build error is printed to stdout/stderr (authentic `next build` error, not a fallback message)
- No `next dev` or stale `.next` process is left running

**Pass criteria:**
- Exit code is non-zero
- Error output contains the actual build error (not a generic message)
- `ps aux | grep next` shows zero processes bound to `FRONTEND_PORT`

---

### TC-04 — Real-browser TTI and on-load latency sweep of 11 pages

**Type:** browser
**Preconditions:**
- Backend is warm and healthy (committed-seed DB, boot to first 200 completed)
- `scripts/start-frontend.sh` has completed with prod-mode `next start` running
- Chrome DevTools Protocol available for automation

**Steps:**
1. Record current time as "process start"
2. Navigate to each page in sequence: `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/<lab-id>`
3. For each page:
   - Measure time-to-interactive (LCP or TTI metric from DevTools timeline)
   - Record all on-load network requests and their latencies
   - Capture a screenshot for evidence
4. After all 11 pages complete, record a fresh `GET /api/health` request latency (cold)
5. Record the total elapsed time from frontend process start to first 200 HTTP response (≤5s reading)

**Expected outcome:**
- All 11 pages load and render without console errors
- Time-to-interactive for each page is recorded
- On-load API latencies are captured for each page's endpoint calls
- Fresh boot-to-health latency is ≤5 seconds
- All measurements are within or slightly above committed budgets (WARNs recorded honestly)

**Pass criteria:**
- Every page loads and renders (no application error boundaries)
- TTI measurements exist for all 11 pages
- On-load latencies exist for each page's API calls
- Boot-to-health ≤5s measurement is recorded
- Page load times are documented in `reports/perf-budgets.md` (appended as "## Iteration 33" section)

---

### TC-05 — Measurements over budget are recorded as honest WARNs

**Type:** artifact
**Preconditions:**
- TC-04 has completed and measurements are being recorded
- At least one page's measurement exceeds its committed budget (or this is verified as not occurring)

**Steps:**
1. Review the measurements recorded in TC-04
2. For any measurement exceeding its budget, verify it is recorded as a WARN row in `reports/perf-budgets.md`
3. Verify the WARN row includes a one-line stated cause (e.g., "dev-mode artifact being cleaned up" or similar)
4. Verify the row is NOT omitted from the table

**Expected outcome:**
- Any over-budget reading appears in the table with an explicit WARN label
- No measurements are silently dropped or omitted
- Each WARN has a concise stated cause

**Pass criteria:**
- WARN rows appear in `reports/perf-budgets.md` with stated causes
- No over-budget rows are missing from the output
- WARN text is honest and specific (not generic)

---

### TC-06 — Dev handoff contains code-level on-load audit

**Type:** artifact
**Preconditions:**
- Dev handoff file exists at `docs/handoffs/goal-ops-hardening-iter-33-dev.md`

**Steps:**
1. Open the dev handoff file
2. Locate the "on-load endpoints audit" section
3. For each of the 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab):
   - Verify the on-load endpoint(s) are listed
   - Verify the persisted table/cache each endpoint reads is named
4. Verify the audit explicitly states: "none performs an unbounded `daily_prices` scan or recomputes an already-ingest-warmed aggregate"

**Expected outcome:**
- Every on-load endpoint for the 11 pages is listed in the audit
- The persisted storage/cache for each endpoint is clearly identified
- An explicit statement confirms no unbounded scans or recomputes

**Pass criteria:**
- Audit table or list is present with all 11 pages covered
- Each endpoint names its data source (e.g., "scanner_runs table", "coverage_cache")
- Explicit statement about no unbounded scans is present and clear

---

### TC-07 — No error-level console entries on loaded pages

**Type:** browser
**Preconditions:**
- TC-04 has loaded all 11 pages in a real browser with DevTools console access

**Steps:**
1. For each of the 11 pages from TC-04:
   - Open browser DevTools console
   - Record all error-level (`console.error`) entries after page load completes
   - Capture a screenshot of the console if any errors are present

**Expected outcome:**
- Zero error-level console entries on any page (the Next.js dev-overlay pill is gone)
- Console contains only normal info/warning/debug entries, no errors

**Pass criteria:**
- No `console.error()` calls appear in DevTools console for any of the 11 pages
- Next.js dev-mode error-overlay UI is not visible on any page

---

### TC-08 — Golden scripts J-01, J-03, J-04, J-05, J-08, J-09 remain passing

**Type:** browser
**Preconditions:**
- `scripts/start-frontend.sh` serving prod-mode frontend
- Backend warm on committed-seed DB
- Golden journey-scripts available in `runs/goal-session-ops-hardening/journey-scripts/`

**Steps:**
1. For each of the 6 required-still-passing journeys (J-01, J-03, J-04, J-05, J-08, J-09):
   - Replay the golden script JSON against the prod-mode frontend + warm backend
   - Capture pass/fail result and any assertion diffs
   - If a failure occurs purely from dev-vs-prod markup (dev-overlay pill, CSS class name), document it for review
2. Aggregate results into a summary (6/6 pass expected)

**Expected outcome:**
- All 6 golden scripts replay and pass
- No assertion failures from behavior changes (only markup diffs are acceptable and should be documented)
- Passing baselines maintained from `last_passing_iter=32`

**Pass criteria:**
- 6/6 golden scripts report PASS status
- Any markup-only diffs are documented in the dev handoff with the specific diff shown
- No behavior-change failures (which would be treated as findings for the evaluator)

---

### TC-09 — HOST-GUARD blocks in `scripts/dev.sh` and `scripts/start-backend.sh` are unchanged

**Type:** artifact
**Preconditions:**
- Git repository state includes both the baseline and current iteration

**Steps:**
1. Run: `git diff HEAD~1..HEAD -- scripts/dev.sh`
2. Verify no lines within any `HOST-GUARD`-marked block have changed
3. Run: `git diff HEAD~1..HEAD -- scripts/start-backend.sh`
4. Verify no lines within any `HOST-GUARD`-marked block have changed
5. Run: `git diff HEAD~1..HEAD -- project-extensions/host-guard/host-guard.env`
6. Verify `HOST_GUARD_MARKER_FILES` still lists exactly `scripts/dev.sh scripts/start-backend.sh`

**Expected outcome:**
- All HOST-GUARD blocks are byte-identical to the previous iteration
- No capacity caps, ulimit settings, or resource constraints have changed
- Only `scripts/start-frontend.sh` has been modified (not wrapped in HOST-GUARD)

**Pass criteria:**
- `git diff` shows zero changes to HOST-GUARD sections in `scripts/dev.sh`
- `git diff` shows zero changes to HOST-GUARD sections in `scripts/start-backend.sh`
- `HOST_GUARD_MARKER_FILES` in `host-guard.env` is unchanged

---

### TC-10 — `merge_ui_test_results.py` preserves TC-prefixed FAIL rows

**Type:** api
**Preconditions:**
- Test invocation via the module's own `_self_test()` function

**Steps:**
1. Create two mock QA result files:
   - File A: contains a `TC-01` row with FAIL verdict and a headline FAIL
   - File B: contains only success rows or no rows
2. Run `merge_ui_test_results.py` to merge File A and File B
3. Verify the merged output includes the `TC-01` row with FAIL verdict
4. Verify the merged output's headline shows FAIL (not downgraded to PASS)

**Expected outcome:**
- TC-prefixed row IDs are matched by the updated `_ROW_RE` regex
- A FAIL headline from either input file survives into the merged output
- No silent downgrade of FAIL to PASS due to regex mismatch

**Pass criteria:**
- `_ROW_RE` regex accepts both `UT-` and `TC-` prefixes
- `TC-01` row appears in merged output with its original FAIL verdict
- Merged output headline is FAIL (proving the TC- row was parsed and its verdict counted)
- A new test case in `_self_test()` proves this with RED-before/GREEN-after

---

### TC-11 — `scripts/measure-perf.sh` header comment reflects prod-mode guarantee

**Type:** artifact
**Preconditions:**
- File `scripts/measure-perf.sh` (symlink to `incredible_auto_dev/scripts/measure-perf.sh`)

**Steps:**
1. Open `scripts/measure-perf.sh` and read lines ~11-14 (the header comment block)
2. Search for the phrase "no reliable way to detect [next dev]" or similar unresolved caveat
3. Verify the comment no longer presents detection of dev mode as an unresolved limitation
4. Verify the comment states that `start-frontend.sh` now guarantees prod mode

**Expected outcome:**
- The old caveat about undetectable dev mode is removed or reworded
- The comment reflects confidence that prod mode is guaranteed
- No change to the actual timing/measurement code

**Pass criteria:**
- Caveat about "no reliable way to detect" is not present in the header
- Comment text affirms prod-mode guarantee from the launcher
- Only the documentation changed; measurement logic is unchanged

---

## Summary

**Total test cases:** 11

| Category | Count |
|----------|-------|
| API tests (launcher behavior, merge logic) | 3 |
| Browser tests (real-browser TTI, golden scripts, console) | 3 |
| Artifact tests (dev handoff, git diffs, measurement file, documentation) | 5 |

**Pass criteria:**
- All 11 test cases pass
- TC-01/TC-02/TC-03 prove the launcher genuinely uses `next build` + `next start`
- TC-04/TC-05/TC-06 prove the real-browser TTI sweep is measured and recorded
- TC-07 proves the dev-overlay pill is gone
- TC-08 proves all 6 required golden scripts still pass on prod-mode frontend
- TC-09 proves HOST-GUARD blocks are untouched
- TC-10 proves the merge tooling handles TC- prefixes
- TC-11 proves the measurement script's documentation reflects the fix

**Key evidence artifacts:**
- `reports/perf-budgets.md` — new "## Iteration 33" section with 11-page measurements
- `docs/handoffs/goal-ops-hardening-iter-33-dev.md` — dev handoff with code-level on-load audit
- `incredible_auto_dev/scripts/start-frontend.sh` — rewritten launcher (next build if stale, then next start)
- `apps/backend/tests/test_start_frontend_script.py` — new smoke tests for TC-01/TC-02/TC-03
