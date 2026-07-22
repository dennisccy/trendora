# goal-ops-hardening-iter-9 Functional Test Plan

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Frontend Present:** yes

## Phase Goal

Verify J-05's four-step acceptance genuinely holds after iter-8's MemoryError-hardening fix via live browser testing under host-guard-capped launch conditions; clear the J-01/J-03/J-04 evidence gap with regression replay and LLM acceptance; close the AG-10 launcher gap so all heavy-compute paths run under declared host caps.

## Test Cases

### TC-01 — Backfill job reaches terminal status and populates aggregates

**Type:** browser
**Preconditions:** 
- Build with AG-10 launcher fix active
- Host-guard caps enabled
- `/data` page accessible
- No prior ingest for 2026-05-15

**Steps:**
1. Navigate to `/data` page
2. Submit a backfill job for one unsnapshotted historical trading day (e.g., 2026-05-15)
3. Wait for job to reach terminal status
4. Inspect `GET /api/data` response for the job's persisted run record

**Expected outcome:** Job completes with status "ok" and includes a non-empty `aggregates_refreshed` array in the persisted record

**Pass criteria:** `status == "ok"` AND `aggregates_refreshed.length > 0`

---

### TC-02 — Scanner leaderboard renders from cache without computing placeholder

**Type:** browser
**Preconditions:** 
- TC-01 backfill job completed
- `/scanner-runs` page accessible
- Market data for 2026-05-15 cached

**Steps:**
1. Navigate to `/scanner-runs`
2. Open the run record for the date from TC-01 (2026-05-15)
3. Observe the leaderboard table rendering
4. Verify no "computing…" placeholder appears

**Expected outcome:** Leaderboard table renders with rows matching the stored `scanner_results` snapshot, served from cache

**Pass criteria:** Table renders immediately with all stored rows visible AND no "computing…" state visible

---

### TC-03 — Market phase served from cache without live-recompute delay

**Type:** api
**Preconditions:** 
- TC-01 backfill job completed for 2026-05-15
- Market phase data cached for that date

**Steps:**
1. Call `GET /api/market-phase?as_of=2026-05-15` (exact endpoint name to confirm)
2. Measure response latency
3. Verify response comes from `market_phase_cache` table

**Expected outcome:** Response is served from persisted cache with minimal latency, not recomputed live

**Pass criteria:** Response status 200 AND response body contains cached market phase for the date AND latency < 100ms

---

### TC-04 — Cold load of `/data` page respects performance budget after restart

**Type:** browser
**Preconditions:** 
- Backend process restarted after TC-01 ingest
- Performance budget defined in `reports/perf-budgets.md`
- Browser cache cleared

**Steps:**
1. Stop and restart backend service
2. Navigate to `/data` page with cold cache
3. Measure time to render coverage panel
4. Verify no full `daily_prices` table prefill occurs

**Expected outcome:** Coverage panel renders within committed budget; backend performs no full `daily_prices` table prefill for this request

**Pass criteria:** Coverage panel visible within budget time AND backend logs show no full table prefill operation

---

### TC-05 — Heavy-ingest test: back-to-back jobs reach ok status under memory cap

**Type:** api
**Preconditions:** 
- `TRENDORA_RUN_HEAVY_INGEST_TEST=1` environment variable set
- AG-10 launcher fix active
- Host-guard caps applied (CPU affinity, thread caps, memory limit)
- Host in idle state (no concurrent test suite)

**Steps:**
1. Run: `apps/backend/.venv/bin/pytest apps/backend/tests/test_start_backend_script.py::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap -v`
2. Monitor for both jobs (full-universe rebuild and heavy backfill) to complete
3. Capture `VmPeak`/`VmSize` values during run
4. Verify all `GET /api/health` polls return 200 with no timeouts

**Expected outcome:** 
- Full-universe rebuild reaches status "ok" (not "partial")
- Heavy backfill reaches status "ok" (not "partial")
- Peak `VmPeak`/`VmSize` stay under `server.memory_cap_mb`'s KB ceiling
- Every health poll returns HTTP 200

**Pass criteria:** 
- Both jobs: `status == "ok"` (reject "partial")
- `VmPeak <= server.memory_cap_mb * 1024` KiB
- `VmSize <= server.memory_cap_mb * 1024` KiB
- 100% of health polls return HTTP 200

---

### TC-06 — Heavy-ingest jobs report complete aggregates_refreshed lists

**Type:** api
**Preconditions:** 
- TC-05 heavy-ingest test executed and both jobs completed
- Job records persisted in database

**Steps:**
1. After TC-05 completes, query each job's persisted record
2. Extract `aggregates_refreshed` list for the rebuild job
3. Extract `aggregates_refreshed` list for the backfill job
4. Verify each list contains all expected categories for its job kind

**Expected outcome:** Each job's `aggregates_refreshed` list is complete, proving no per-item loop silently early-aborted on `MemoryError`

**Pass criteria:** 
- Rebuild job: `aggregates_refreshed` contains all rebuild-expected categories
- Backfill job: `aggregates_refreshed` contains all backfill-expected categories
- No category is missing or marked as partial

---

### TC-07 — start-backend.sh applies host-guard CPU and thread caps

**Type:** api
**Preconditions:** 
- `project-extensions/host-guard/host-guard.env` present with `HOST_GUARD_ENABLED=1`
- `HOST_GUARD_CPU_LIST` and `HOST_GUARD_BLAS_THREADS` defined
- Backend not running

**Steps:**
1. Launch backend via `scripts/start-backend.sh`
2. Capture the backend process PID
3. Read `/proc/<pid>/status` and extract `Cpus_allowed_list`
4. Read `/proc/<pid>/environ` and verify `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`
5. Stop backend

**Expected outcome:** Process's CPU affinity matches `HOST_GUARD_CPU_LIST`; all BLAS/OMP thread variables equal `HOST_GUARD_BLAS_THREADS`

**Pass criteria:** 
- `Cpus_allowed_list` == `$HOST_GUARD_CPU_LIST`
- `OMP_NUM_THREADS` == `$HOST_GUARD_BLAS_THREADS`
- `OPENBLAS_NUM_THREADS` == `$HOST_GUARD_BLAS_THREADS`
- `MKL_NUM_THREADS` == `$HOST_GUARD_BLAS_THREADS`
- `NUMEXPR_NUM_THREADS` == `$HOST_GUARD_BLAS_THREADS`

---

### TC-08 — dev.sh backend subshell applies caps; frontend subshell does not

**Type:** api
**Preconditions:** 
- `project-extensions/host-guard/host-guard.env` present with `HOST_GUARD_ENABLED=1`
- Both frontend and backend services not running

**Steps:**
1. Launch via `scripts/dev.sh`
2. Capture PIDs of both backend (uvicorn) and frontend (next dev) processes
3. For backend PID: verify `/proc/<pid>/status` `Cpus_allowed_list` matches `HOST_GUARD_CPU_LIST`
4. For backend PID: verify effective `ulimit -v` equals `server.memory_cap_mb * 1024` KiB
5. For backend PID: verify `MALLOC_ARENA_MAX` is exported to expected value
6. For frontend PID: verify no CPU affinity, thread caps, or memory limits are applied
7. Stop both services

**Expected outcome:** 
- Backend process constrained by host-guard caps (CPU, BLAS threads, memory ulimit, malloc arena)
- Frontend process runs without any such constraints
- Existing config-derived `ulimit -v` and `MALLOC_ARENA_MAX` logic preserved

**Pass criteria:** 
- Backend: `Cpus_allowed_list` == `$HOST_GUARD_CPU_LIST`
- Backend: `ulimit -v` == `server.memory_cap_mb * 1024` KiB
- Backend: `MALLOC_ARENA_MAX` environment variable set correctly
- Frontend: no CPU affinity, thread caps, or memory constraints visible in `/proc/<pid>/status`

---

### TC-09 — Launch scripts work cleanly when host-guard.env absent or disabled

**Type:** api
**Preconditions:** 
- `project-extensions/host-guard/host-guard.env` absent OR `HOST_GUARD_ENABLED=0`
- Backend/frontend not running

**Steps:**
1. Attempt to launch backend via `scripts/start-backend.sh`; verify successful startup
2. Stop backend
3. Attempt to launch via `scripts/dev.sh`; verify both services start successfully
4. Verify no caps are applied (check `/proc/<pid>/status`, environment)
5. Stop both services

**Expected outcome:** Both scripts start cleanly with no errors; host-guard remains fully optional

**Pass criteria:** 
- `scripts/start-backend.sh` exits with 0
- `scripts/dev.sh` exits with 0
- Backend runs with no CPU affinity or thread caps enforced
- No environment errors or missing-file warnings in logs

---

### TC-10 — J-01 golden replay passes and outcome recorded

**Type:** api
**Preconditions:** 
- J-01's stored golden replay script exists
- Current build deployed and healthy
- Replay fixture data available

**Steps:**
1. Locate J-01's golden replay script in `docs/journey-evidence/` or replay artifact directory
2. Execute the replay script against the current build
3. Verify all steps pass (or adjudicate any stale-data proxies explicitly per iter-5 precedent)
4. Document outcome

**Expected outcome:** All replay steps pass; outcome recorded in `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`

**Pass criteria:** Replay script passes OR outcome explicitly adjudicated with reasoning AND recorded artifact exists

---

### TC-11 — J-03 golden replay passes and outcome recorded

**Type:** api
**Preconditions:** 
- J-03's stored golden replay script exists
- Current build deployed and healthy
- Replay fixture data available

**Steps:**
1. Locate J-03's golden replay script
2. Execute the replay script against the current build
3. Verify all steps pass
4. Document outcome

**Expected outcome:** All replay steps pass; outcome recorded in `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`

**Pass criteria:** Replay script passes AND recorded artifact exists

---

### TC-12 — J-04 six-step LLM acceptance passes and outcome recorded

**Type:** browser
**Preconditions:** 
- Current build deployed and healthy
- Browser-qa-agent has access to live backend and frontend

**Steps:**
1. Browser-qa-agent runs J-04's 6-step LLM acceptance against live build:
   - Step 1: Boot-to-health timing within spec
   - Step 2: Pre-ready phase detail rendered correctly
   - Step 3: Crash presentation (if applicable) shown correctly
   - Step 4: Interrupted-job detection works
   - Step 5: (Additional acceptance step per spec)
   - Step 6: (Additional acceptance step per spec)
2. Document each step's pass/fail
3. Record outcome

**Expected outcome:** All 6 steps pass; outcome recorded in `reports/phase-goal-ops-hardening-iter-9-regression-replay-results.md`

**Pass criteria:** All 6 steps pass AND recorded artifact exists

---

### TC-13 — Libc handle memoization call-count test (if B2 capacity allows)

**Type:** api
**Preconditions:** 
- B2 (libc memoization feature) implemented in `app.engine.data_manager`
- `test_data_manager.py` includes monkeypatched call-count test

**Steps:**
1. Unit test monkeypatches `ctypes.util.find_library` and `ctypes.CDLL` with a call counter
2. Invoke `_release_process_memory()` multiple times within one process lifetime (e.g., 5+ calls)
3. Verify libc-resolution path executes at most once across all invocations
4. Verify every call still performs `gc.collect()` and `malloc_trim` with unchanged effect

**Expected outcome:** Libc resolution cached after first call; subsequent calls reuse cached handle; all side effects preserved

**Pass criteria:** 
- `find_library` call count == 1
- `CDLL` constructor call count == 1
- `gc.collect()` called on every `_release_process_memory()` invocation
- `malloc_trim` called on every `_release_process_memory()` invocation

---

### TC-14 — RAW ui-test-results.llm.md verdict lines scored correctly

**Type:** artifact
**Preconditions:** 
- Browser-qa-agent completed J-05, J-01, J-03, J-04 verification
- `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md` exists

**Steps:**
1. Locate and read the RAW `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md` file
2. Extract per-journey verdict lines (not merged summary, not `status.json`)
3. Verify verdict lines are used for final scoring, not averaged or overridden by higher-level summaries

**Expected outcome:** Each journey (J-01, J-03, J-04, J-05) has an explicit verdict line in the raw artifact; scoring uses those lines, not `status.json` or merged table

**Pass criteria:** Raw artifact contains explicit verdict lines for all four journeys AND scoring workflow references the raw artifact, not merged summary

---

## Summary

**Total test cases:** 14

**Test case breakdown:**
- **Browser tests:** 3 (TC-01, TC-02, TC-12, TC-14 — browser/artifact interaction or manual browser verification)
- **API tests:** 10 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-13 — backend, launch scripts, replay, unit tests)
- **Artifact checks:** 1 (TC-14 — raw LLM markdown verification)

**Coverage:**
- J-05 acceptance (4 of 4 steps covered: TC-01, TC-02, TC-03, TC-05)
- J-01/J-03/J-04 re-verification (TC-10, TC-11, TC-12)
- AG-10 launcher gap closure (TC-07, TC-08, TC-09)
- Heavy-ingest regression hardening (TC-05, TC-06)
- Libc memoization optimization (TC-13, if B2 capacity allows)
- Scoring integrity (TC-14)
