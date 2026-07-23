# goal-ops-hardening-iter-12 Functional Test Plan

**Phase:** goal-ops-hardening-iter-12
**Date:** 2026-07-22
**Frontend Present:** yes

## Phase Goal

Close J-06's two remaining agent-owned evidence gaps (G1: sweep numbers missing from `reports/perf-budgets.md`; G2: `/api/indexes?full=true`'s over-budget reading has no valid like-for-like control) and correct iter-11's incomplete TC-4 audit, with no source code changes anticipated. The product surface remains unchanged; only measurement documentation and audit completeness change.

## Test Cases

### TC-01 — G1 Evidence Transcription: Iter-11 Sweep Captured and Recorded

**Type:** artifact
**Preconditions:**
- `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-perf-sweep-summary.txt` exists with 11-page TTI and endpoint-latency readings captured during 2026-07-22 ~21:38–21:49Z
- `reports/perf-budgets.md` exists with prior dated sections

**Steps:**
1. Read `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-perf-sweep-summary.txt` to identify all 11 pages' TTI readings and endpoint-latency values
2. Verify the two over-budget `/api/indexes?full=true` readings (2066.3ms, 2671.8ms) are present in the source file
3. Verify the `/api/health` 2948.8ms outlier is present in the source file
4. Open `reports/perf-budgets.md` and check for a new dated section transcribing the sweep
5. Verify the section includes all 11 pages' TTI figures
6. Verify the section includes all endpoint-latency readings, including both over-budget `/api/indexes` values and the `/api/health` outlier
7. Verify each over-budget reading is marked with a WARN indicator
8. Verify both the original measurement timestamp (2026-07-22 ~21:38–21:49Z) and the transcription date are stated

**Expected outcome:** `reports/perf-budgets.md` contains a complete, dated transcription of the iter-11 sweep with full disclosure of all readings, both budgets met and exceeded, and dual timestamps.

**Pass criteria:** The transcribed section is present, contains all 11 pages' TTI values, includes every endpoint-latency reading from the source file verbatim (no omitted or averaged values), marks both `/api/indexes?full=true` over-budget readings and the `/api/health` outlier as WARNs, and cites both the original 2026-07-22 window and today's transcription date.

---

### TC-02 — G2 Control Measurement: Three Fresh-Navigation `/api/indexes` Reads with Idle Confirmation

**Type:** browser
**Preconditions:**
- Backend running on port 8255 with frontend on port 3000 (or 3255 per operator note)
- `logs/backend.log` exists and is actively appending
- `logs/hwmon/hwmon.csv` exists with live load1 and MemAvailable readings
- No backfill/fetch/rebuild job is in-flight (confirmed via `/api/data/jobs` or log inspection)
- Host load is in the established idle range (load1 < 2.0, MemAvailable > 1.5GB — per iter-11 baselines)

**Steps:**
1. Open Chrome DevTools and disable browser cache
2. Navigate to `/data` (first fresh load, no cached tab reuse)
3. Wait for the `/api/indexes?full=true` network request to complete
4. Record the latency value and the exact timestamp from the browser network panel
5. Cross-check `logs/backend.log` at that timestamp to confirm no concurrent job was in-flight
6. Cross-check `logs/hwmon/hwmon.csv` at that exact timestamp to confirm load1 and MemAvailable are within idle range
7. Repeat steps 2–6 two more times (second and third independent navigations), each in a fresh new tab or after cache clear
8. Record all three latency readings and their corresponding idle-confirmation evidence in `reports/perf-budgets.md`
9. For each reading ≤1.5s, mark "holds: yes"; for any reading > 1.5s, mark "holds: no" with the exact overage amount

**Expected outcome:** `reports/perf-budgets.md` contains three recorded `/api/indexes?full=true` measurements, each with independent idle-window confirmation from both `logs/backend.log` and `logs/hwmon/hwmon.csv`, and each honestly marked against the ≤1.5s budget.

**Pass criteria:** All three readings are recorded with timestamps, all three have contemporaneous `logs/backend.log` and `logs/hwmon/hwmon.csv` evidence at those exact times confirming idle state (no concurrent job, load1 < 2.0, MemAvailable > 1.5GB), and each reading is marked "holds: yes" or an explicit WARN with numeric overage (not silently omitted or averaged).

---

### TC-03 — TC-4 Audit Correction: MISS/Compute Path Named

**Type:** artifact
**Preconditions:**
- `reports/perf-budgets.md` contains the existing TC-4 audit section from iter-11 (documenting cache-HIT paths only)
- Source code file `apps/backend/app/engine/forward_testing.py:826` exists

**Steps:**
1. Open `reports/perf-budgets.md` and locate the existing "J-06 re-sweep … TC-4 code audit" section from iter-11
2. Verify a new "AUDIT CORRECTION" blockquote addendum has been appended (using the same format as the iter-9 P1 blockquote already in the file)
3. Read the correction text to confirm it names `apps/backend/app/engine/forward_testing.py:826` and the exact query `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`
4. Verify the blockquote states this is the MISS/compute path inside `compute_forward_aggregates`, reached via `forward_aggregates_cached` on a cache miss
5. Verify the blockquote explicitly states that iter-11's "no genuine violation found" conclusion applied only to cache-HIT paths
6. Verify no code changes were made to `forward_testing.py` (the site is named, not fixed)

**Expected outcome:** An audit-correction blockquote is appended to the iter-11 TC-4 section, precisely naming the unbounded-load site and the audit's scope limitation, without any code modification to that site.

**Pass criteria:** The blockquote is present, cites the exact file path and line number, names the specific query, states the cache-HIT scope limitation of iter-11's prior audit, and `apps/backend/app/engine/forward_testing.py:826` remains unchanged.

---

### TC-04 — `data_provider_runs` Rows 120/121/122 Read and Handoff Statement

**Type:** artifact
**Preconditions:**
- SQLite database with `data_provider_runs` table is accessible (read-only)
- `logs/backend.log` contains entries around the time rows 120/121/122 were processed
- `docs/handoffs/goal-ops-hardening-iter-12-dev.md` will be created

**Steps:**
1. Read rows 120, 121, 122 directly from the `data_provider_runs` table
2. Record the `aggregates_refreshed` bitmap for each row (expect 4-of-7 on these zero-new-date runs)
3. Check whether these rows have zero new trading dates (verify `new_date_count` or similar field)
4. Read `logs/backend.log` at lines around 27185 and 27233 to locate the MemoryError abort entries
5. Check whether `forward_aggregates` is absent from rows 121/122 (expected outcome if MemoryError abort occurred)
6. In `docs/handoffs/goal-ops-hardening-iter-12-dev.md`, state explicitly whether the 4-of-7 `aggregates_refreshed` outcome is design-consistent (i.e., whether `latest_snapshot`/`market_phase` are legitimately skipped because no new trading date landed)
7. In the handoff, cite the MemoryError abort at the exact log lines and state whether `forward_aggregates`'s absence is solely attributable to that abort
8. In the handoff, confirm whether J-05's contract is intact or flag it for re-open if evidence contradicts the MemoryError-only explanation

**Expected outcome:** The handoff document explicitly records whether the 4-of-7 `aggregates_refreshed` outcome is design-correct and attributes `forward_aggregates`'s absence to the documented MemoryError abort, with J-05's contract integrity confirmed or flagged.

**Pass criteria:** The handoff contains an explicit statement of whether the 4-of-7 outcome is design-consistent (yes/no with reasoning), cites `logs/backend.log` lines 27185 and 27233, confirms that `forward_aggregates` is absent from rows 121/122, and either confirms J-05's contract is intact or flags it for re-open with specific evidence.

---

### TC-05 — J-01 Deterministic Replay PASS

**Type:** browser
**Preconditions:**
- J-01's stored golden replay script exists and is executable
- Backend and frontend are running
- No manual intervention in the replay pipeline is needed (or LLM fallback lane is available)

**Steps:**
1. Execute J-01's deterministic replay script against the current build
2. Allow the replay to run to completion without interruption
3. Inspect the regression-replay-results artifact for J-01's outcome

**Expected outcome:** J-01's replay records a PASS outcome in the regression-replay-results artifact.

**Pass criteria:** The replay exits with a PASS verdict and is recorded in the results artifact.

---

### TC-06 — J-03 Deterministic Replay PASS

**Type:** browser
**Preconditions:**
- J-03's stored golden replay script exists and is executable
- Backend and frontend are running
- No manual intervention in the replay pipeline is needed (or LLM fallback lane is available)

**Steps:**
1. Execute J-03's deterministic replay script against the current build
2. Allow the replay to run to completion without interruption
3. Inspect the regression-replay-results artifact for J-03's outcome

**Expected outcome:** J-03's replay records a PASS outcome in the regression-replay-results artifact.

**Pass criteria:** The replay exits with a PASS verdict and is recorded in the results artifact.

---

### TC-07 — J-04 LLM-Fallback Re-Verification PASS with Evidence

**Type:** browser
**Preconditions:**
- J-04's acceptance criteria are documented
- Backend and frontend are running
- Chrome/browser is available for manual/LLM-assisted verification

**Steps:**
1. Navigate to the UI surface(s) covered by J-04's acceptance steps
2. Interact with the UI according to the documented acceptance criteria
3. Verify each acceptance criterion via UI observation, log grep, or database row query
4. Record a screenshot or log excerpt as evidence for each criterion passed

**Expected outcome:** All of J-04's acceptance criteria are satisfied with cited evidence (screenshot, log line, or database row reference).

**Pass criteria:** J-04 records a PASS outcome with explicit evidence citations (e.g., "screenshot `TC-07-j04-verify.png`", "logs/backend.log line X shows ...", "DB query confirms Y").

---

### TC-08 — J-05 LLM-Fallback Re-Verification PASS with Evidence

**Type:** browser
**Preconditions:**
- J-05's acceptance criteria are documented
- Backend and frontend are running
- Chrome/browser is available for manual/LLM-assisted verification

**Steps:**
1. Navigate to the UI surface(s) covered by J-05's acceptance steps
2. Interact with the UI according to the documented acceptance criteria
3. Verify each acceptance criterion via UI observation, log grep, or database row query
4. Record a screenshot or log excerpt as evidence for each criterion passed

**Expected outcome:** All of J-05's acceptance criteria are satisfied with cited evidence (screenshot, log line, or database row reference).

**Pass criteria:** J-05 records a PASS outcome with explicit evidence citations (e.g., "screenshot `TC-08-j05-verify.png`", "logs/backend.log line X shows ...", "DB query confirms Y").

---

### TC-09 — Backend Test Subset Execution with Host-Guard Confinement

**Type:** api
**Preconditions:**
- `project-extensions/host-guard/host-guard.env` exists and defines `HOST_GUARD_CPU_LIST` and `HOST_GUARD_BLAS_THREADS`
- Test files `apps/backend/tests/test_data_manager_jobs_pipeline.py` and `apps/backend/tests/test_forward_testing.py` exist
- Backend dependencies are installed

**Steps:**
1. Source `project-extensions/host-guard/host-guard.env` to obtain `HOST_GUARD_CPU_LIST` and `HOST_GUARD_BLAS_THREADS` values
2. Export `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` to the value of `HOST_GUARD_BLAS_THREADS`
3. Run the targeted test subset under `taskset -c "$HOST_GUARD_CPU_LIST"` confinement:
   ```
   taskset -c "$HOST_GUARD_CPU_LIST" \
     OMP_NUM_THREADS="$HOST_GUARD_BLAS_THREADS" \
     OPENBLAS_NUM_THREADS="$HOST_GUARD_BLAS_THREADS" \
     MKL_NUM_THREADS="$HOST_GUARD_BLAS_THREADS" \
     NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS" \
     pytest apps/backend/tests/test_data_manager_jobs_pipeline.py apps/backend/tests/test_forward_testing.py -v
   ```
4. Exclude the heavy-ingest test lane: do not set `TRENDORA_RUN_HEAVY_INGEST_TEST=1`
5. Capture full pytest output (exit code, pass/fail counts, test names)
6. Verify exit code is 0 (all tests pass except pre-existing documented failures)
7. Confirm the only allowed pre-existing failure is `tests/test_db.py::test_create_all_produces_expected_tables`

**Expected outcome:** Targeted test subset completes with zero NEW failures beyond the pre-existing `tests/test_db.py::test_create_all_produces_expected_tables`.

**Pass criteria:** pytest exits with code 0 and the captured output shows all tests in the two targeted files pass (or only the pre-existing documented failure appears elsewhere), and the command was launched with all required host-guard environment variables and `taskset` CPU confinement.

---

### TC-10 — Dev Handoff Documentation Completeness

**Type:** artifact
**Preconditions:**
- All prior test cases have been executed
- `reports/perf-budgets.md` has been updated with G1 and G2 sections
- TC-4 audit correction blockquote has been appended
- `data_provider_runs` rows 120/121/122 have been read

**Steps:**
1. Open `docs/handoffs/goal-ops-hardening-iter-12-dev.md`
2. Verify the handoff exists and is non-empty
3. Verify it states explicitly whether any source file changed (expected: none)
4. Verify it cites the exact `reports/perf-budgets.md` section headers or line ranges supporting G1 closure
5. Verify it cites the exact `reports/perf-budgets.md` section headers or line ranges supporting G2 closure
6. Verify it contains the `data_provider_runs` 120/121/122 finding (design-consistency and MemoryError attribution)
7. Verify it lists the exact pytest command that was run (including host-guard wrap: `taskset`, env vars, test file paths)
8. Verify it records the pytest result (exit code, pass/fail/skip counts)
9. Verify it carries forward the open owner decisions unchanged: AG-8 MemoryError fix, `HOST_GUARD_REQUIRE_MARKERS`, `demo.sh --session-live` walkthrough

**Expected outcome:** `docs/handoffs/goal-ops-hardening-iter-12-dev.md` is complete, cites exact evidence sections, and records all required findings and decisions.

**Pass criteria:** The handoff exists, states no source file changed, cites specific `reports/perf-budgets.md` sections for G1/G2, includes the `data_provider_runs` statement, records the host-guard-wrapped pytest command and its result, and lists the three outstanding owner decisions without modification.

---

## Summary

**Total test cases:** 10

**Test case breakdown:**
- **API tests:** 1 (TC-09 backend test subset execution)
- **Browser tests:** 4 (TC-02 G2 three-load control measurement, TC-05 J-01 replay, TC-06 J-03 replay, TC-07 J-04 verification, TC-08 J-05 verification)
- **Artifact checks:** 5 (TC-01 G1 transcription, TC-03 TC-4 audit correction, TC-04 `data_provider_runs` read and handoff, TC-10 dev handoff completeness)

**Journey coverage:**
- **J-06 (target):** TC-01 (G1 evidence gap closure via transcription), TC-02 (G2 evidence gap closure via controlled re-measurement), TC-03 (TC-4 audit correction)
- **J-01, J-03 (required-still-passing, deterministic replay):** TC-05, TC-06
- **J-04, J-05 (required-still-passing, LLM fallback):** TC-07, TC-08

**Anti-goal alignment:**
- AG-3 (displayed numbers match engine computation): TC-02 verifies three fresh reads with exact timestamp evidence
- AG-8 (no source changes, measurement-only): TC-01/TC-02/TC-03 confirm evidence transcription and documentation only, no product code modification
- AG-10 (host-guard confinement): TC-09 requires pytest wrapped in taskset + env caps from host-guard.env
