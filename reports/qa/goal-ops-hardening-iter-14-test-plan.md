# goal-ops-hardening-iter-14 Functional Test Plan

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Frontend Present:** no

## Phase Goal

Rewrite the unbounded ORM reads in `compute_forward_aggregates` to use column-projected, chunked/streamed access bounded by `cfg.research.read_batch_size`, ensuring the backend stays available and responsive while computing forward-return aggregates for all configured horizons, even under concurrent load and memory pressure.

## Test Cases

### TC-01 — Byte-identity test for horizon=20 with as_of=None

**Type:** artifact
**Preconditions:** 
- Small fixture DB exists (mirroring `aggregates_engine` convention)
- Pre-rewrite reference payload for horizon=20, as_of=None is stored
- Rewritten `compute_forward_aggregates` is in place

**Steps:**
1. Run the rewritten `compute_forward_aggregates(horizon=20, as_of=None)` against the fixture
2. Compare the returned dict to the stored reference payload
3. Verify every key matches: `overall`, `by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `by_pullback_to_rising_dma`, `by_flat_base_breakout`, `excess`, `control_group`, `attribution`

**Expected outcome:** Rewritten output is byte-identical to reference across all 10 keys.
**Pass criteria:** Returned dict `==` reference dict with no value discrepancies on any key.

---

### TC-02 — Byte-identity test across all horizons and as_of variants

**Type:** artifact
**Preconditions:**
- Small fixture DB exists with reference payloads pre-computed
- Reference payloads stored for all 5 configured horizons [1, 5, 10, 20, 60]
- Both `as_of=None` and a historical `as_of` (excluding newest snapshot) variants computed

**Steps:**
1. For each horizon in [1, 5, 10, 20, 60]:
   - Call rewritten `compute_forward_aggregates(horizon=h, as_of=None)`
   - Call rewritten `compute_forward_aggregates(horizon=h, as_of=historical_date)`
   - Compare each result to the pre-stored reference payload
2. Verify all 10 payload comparisons succeed

**Expected outcome:** All 10 rewritten outputs (5 horizons × 2 as_of variants) are byte-identical to their reference counterparts.
**Pass criteria:** 10/10 payload comparisons return true for full-dict equality.

---

### TC-03 — Real tightened-memory-cap induction test (no monkeypatch)

**Type:** api
**Preconditions:**
- Fixture DB exists (file-backed SQLite, not `:memory:`)
- Sized with enough `ForwardReturn`/`ScannerResult` rows to expose memory pressure in unbounded path
- A throwaway subprocess mechanism is available (e.g., `subprocess.run` with resource limits)

**Steps:**
1. Spawn a subprocess with `ulimit -v` set below what the old unbounded path needs but above what the new bounded path needs
2. Inside the subprocess, invoke `compute_forward_aggregates()` or `forward_aggregates_cached()` against the fixture
3. Catch the raised exception (expected: `MemoryError` or logged isolated failure)
4. In the SAME subprocess, execute a subsequent DB read (e.g., fetch an existing `ForwardAggregateCache` row)
5. Verify the second read succeeds without hanging

**Expected outcome:** First call raises `MemoryError` (or logged isolated failure); second read in same process succeeds immediately.
**Pass criteria:** Subprocess completes without timeout; second read returns a result within 5 seconds; no wedge/hang detected.

---

### TC-04 — Concurrent-caller regression test (N≥4 threads/processes)

**Type:** api
**Preconditions:**
- Fixture DB exists (file-backed SQLite, shared across callers)
- N≥4 concurrent callers can be spawned (ThreadPoolExecutor or multiprocessing)
- Shared timeout budget (e.g., 30 seconds)

**Steps:**
1. Spawn N≥4 concurrent threads/processes, each with its own DB session
2. Each caller invokes `compute_forward_aggregates()` or `forward_aggregates_cached()` against the shared fixture
3. Issue all N calls simultaneously
4. Collect results/exceptions from all N callers within the bounded timeout (30 s)

**Expected outcome:** All N callers return (either success or a clean isolated failure) within timeout; none blocked or hanging.
**Pass criteria:** All N calls complete (success or graceful failure) within 30 seconds; zero callers left blocked; timeout never reached.

---

### TC-05 — Operator-authorized full-deep-basis health & memory measurement pass

**Type:** api
**Preconditions:**
- Backend service is DOWN as of dispatch
- Operator has launched backend via `scripts/start-backend.sh` with host-guard confinement active:
  - `taskset -c 0-3,8-11`
  - `OMP_NUM_THREADS=4`, `OPENBLAS_NUM_THREADS=4`, `MKL_NUM_THREADS=4`, `NUMEXPR_NUM_THREADS=4`
  - `HOST_GUARD_CPU_LIST="0-3,8-11"`, `HOST_GUARD_REQUIRE_MARKERS=1`
- 1 Hz hwmon sampler running; thermal watchdog armed (Tctl ≥95°C sustained 10s, DIMM ≥85°C, NVMe ≥75°C abort)
- Process start timestamp and PID recorded

**Steps:**
1. In the SAME long-lived backend process, sequentially warm all 5 configured horizons (via finalize hook or direct call)
2. After each horizon, call `GET /api/backtest` once per horizon (5 calls total)
3. Poll `GET /api/health` at 1 Hz throughout the entire pass (start of warm → end of final backtest call)
4. Sample `/proc/<pid>/status` `VmPeak` at 1 Hz throughout
5. Record the process-start timestamp and the first `GET /api/health` HTTP 200 timestamp

**Expected outcome:** 
- Every `GET /api/health` poll returns HTTP 200 within its committed budget (any outlier <100 ms beyond baseline)
- Process `VmPeak` stays below 6,291,456 KB (6144 MB) with stated margin
- All 5 horizons warm without restart needed
- All 5 `GET /api/backtest` calls return HTTP 200

**Pass criteria:** 
- HTTP 200 on every health poll throughout the pass
- `VmPeak` documented and ≤6,291,456 KB
- Boot-to-first-200 elapsed time ≤5 seconds (recorded separately in TC-07)

---

### TC-06 — Induced memory-pressure abort isolation during heavy pass

**Type:** api
**Preconditions:**
- Same setup as TC-05 (full-deep-basis backend running)
- Same long-lived process has warmed at least one horizon successfully
- Memory-pressure induction mechanism available (tightened cap in nested subprocess, or test hook)

**Steps:**
1. During the warm of one middle horizon (e.g., horizon=10), induce a memory-pressure condition
2. Observe the induced warm step abort (expected: logged, isolated to that step)
3. In the SAME long-lived process, immediately poll `GET /api/health`
4. Attempt to serve a previously-cached `GET /api/backtest` horizon (from an earlier warm before the pressure)
5. Verify no process restart was required

**Expected outcome:** 
- Pressure-induced warm aborts with a logged, isolated failure
- Same process continues to answer `GET /api/health` with HTTP 200
- Previously-cached horizons still serve via `GET /api/backtest` HTTP 200
- No restart needed to recover

**Pass criteria:** 
- Health poll returns HTTP 200 post-abort
- Cached backtest request returns HTTP 200 with stored data
- Zero hangs or wedges observed; process remains live

---

### TC-07 — Live boot-to-first-200 timing from TC-05 pass

**Type:** artifact
**Preconditions:**
- TC-05 measurement pass has completed
- Process-start timestamp and first `GET /api/health` HTTP 200 timestamp recorded by operator

**Steps:**
1. Calculate elapsed seconds from process start to first HTTP 200
2. Compare to the committed ≤5 second budget
3. Record in `reports/perf-budgets.md` with measurement timestamp

**Expected outcome:** Boot-to-first-200 timing ≤5 seconds, recorded with margin and date.
**Pass criteria:** Elapsed time value exists, is ≤5 seconds, and is documented in perf-budgets.md with margin stated.

---

### TC-08 — Transcription of iter-13's J-06 passing readings into perf-budgets.md

**Type:** artifact
**Preconditions:**
- `reports/perf-budgets.md` exists
- Iter-13's already-verified J-06 readings are known: 218.7 ms, 218.7 ms, 219.2 ms on `/data`; 70.5 ms on `/`

**Steps:**
1. Add a new dated section to `reports/perf-budgets.md` (e.g., "Iteration 14 — Perf Baseline (J-06 Transcribed)")
2. Transcribe the three `/data` readings: 218.7 ms, 218.7 ms, 219.2 ms
3. Transcribe the `/` reading: 70.5 ms
4. Label each against the ≤1500 ms budget (all should show PASS)

**Expected outcome:** New dated section appears with transcribed readings and PASS labels.
**Pass criteria:** `reports/perf-budgets.md` contains the four values (3× `/data`, 1× `/`) with correct labels and budget comparison.

---

### TC-09 — Browser readiness badge stability during regression replay

**Type:** browser
**Preconditions:**
- Browser-qa-agent will run regression replay of J-01, J-03, J-05
- These journeys drive real backfills through the rewritten `_refresh_ingest_aggregates` finalize hook
- `/backtest` page is accessible

**Steps:**
1. Browser-qa-agent runs deterministic golden-script replay for J-01, J-03, J-05
2. During each journey's backfill execution, monitor the global readiness badge for frozen/blank frames
3. Load `/backtest` page once during the replay
4. Inspect screenshots/DOM for the frozen "Checking backend…" state or blank cards
5. Record the readiness badge state at each major checkpoint

**Expected outcome:** 
- Readiness badge never renders frozen "Checking backend…" state during any backfill
- Readiness badge never renders blank at any step
- `/backtest` renders its per-horizon evidence panel without frozen or blank frame

**Pass criteria:** Zero screenshots showing frozen/blank badge; `/backtest` renders complete evidence panel; no "Checking backend…" state captured.

---

### TC-10 — Required-still-passing journeys regression (J-01, J-03, J-04, J-05)

**Type:** browser
**Preconditions:**
- J-01, J-03, J-04, J-05 are currently passing
- Golden-script replay or LLM fallback available
- Deterministic replay harness is ready

**Steps:**
1. Run deterministic golden-script replay for J-01, J-03, J-04, J-05 against this iteration's build
2. For any journey without a golden, use LLM browser-qa fallback
3. Compare outcomes to baseline (should remain PASS)

**Expected outcome:** All four journeys re-verify PASS (either via golden replay or LLM fallback).
**Pass criteria:** J-01 PASS, J-03 PASS, J-04 PASS, J-05 PASS; zero regressions.

---

### TC-11 — Coherence audit: no second producer for forward-aggregate data contract

**Type:** artifact
**Preconditions:**
- No frontend file touched (Frontend Present: no)
- No new endpoint or table added
- `coherence.md` or equivalent audit artifact exists

**Steps:**
1. Inspect `coherence.md` or data-contract audit for the forward-aggregate row
2. Verify that `app.engine.forward_testing.compute_forward_aggregates` is listed as the sole computing module
3. Verify that `GET /api/backtest` is listed as the sole serving endpoint
4. Confirm the MCP `query_backtest` tool call site is unchanged
5. Check that zero second producer is recorded

**Expected outcome:** `compute_forward_aggregates` and `GET /api/backtest` remain the sole producer and endpoint; no second path or alternative aggregation.
**Pass criteria:** Audit confirms zero second producer; single module/endpoint chain unchanged.

---

## Summary

**Total test cases:** 11
**API tests:** 5 (TC-03, TC-04, TC-05, TC-06, TC-07)
**Browser tests:** 2 (TC-09, TC-10)
**Artifact checks:** 4 (TC-01, TC-02, TC-08, TC-11)

---

## Implementation Notes

- TC-01/TC-02 use small fixture DBs (file-backed SQLite, not `:memory:`) mirroring the existing `aggregates_engine` convention
- TC-03/TC-04 require file-backed fixtures to enable subprocess/multi-threaded sharing
- TC-05/TC-06 are operator-supervised, host-guard-confined passes — developer records operator-provided output verbatim in `reports/perf-budgets.md`
- All backend tests run with `taskset -c 0-3,8-11` and BLAS/OMP/numexpr threads=4; no full pytest suite
- Test-first contract from phase spec strictly adhered to; every test case maps to a numbered Definition-of-Done item
