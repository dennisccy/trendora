# Goal-ops-hardening-iter-19 Functional Test Plan

**Phase:** goal-ops-hardening-iter-19  
**Date:** 2026-07-24  
**Frontend Present:** no

## Phase Goal

Eliminate the SQLite write-lock bottleneck in `/backtest` and MCP `query_backtest` serving paths by guarding `backfill_run_forward_returns` so completed runs perform zero write-lock-acquiring operations on each request, proven by live re-measurement against the deep basis.

## Test Cases

### TC-1 — Fully-backfilled run via GET /api/backtest issues zero write statements

**Type:** api  
**Preconditions:**
- `ScannerRun` fixture with `forward_returns` already fully backfilled for every configured horizon and symbol
- Idempotency check confirms zero rows missing
- SQL statement tracking enabled via `before_cursor_execute` hook

**Steps:**
1. Call `GET /api/backtest` for the run's as-of date
2. Inspect SQL statement log captured by `before_cursor_execute`
3. Verify response HTTP 200

**Expected outcome:** Zero `INSERT`, `UPDATE`, or `DELETE` statements issued during the request; no write-lock acquisition.

**Pass criteria:** SQL log contains no write statements; HTTP 200 response; payload fields match pre-fix baseline.

---

### TC-2 — Fully-backfilled run via MCP query_backtest issues zero write statements and matches API response

**Type:** api  
**Preconditions:**
- Same fixture as TC-1 (fully-backfilled `ScannerRun`)
- SQL statement tracking enabled

**Steps:**
1. Call `app.mcp.tools.query_backtest(session, asof=<fixture_asof>)` directly
2. Inspect SQL statement log
3. Compare returned scorecard, `evidence_by_horizon`, `evidence_status`, `evidence_generated_at`, `evidence_asof` to `GET /api/backtest` response for same inputs

**Expected outcome:** Zero write statements issued; all evidence fields byte-identical to API response.

**Pass criteria:** SQL log contains no write statements; `evidence_status`, `evidence_generated_at`, `evidence_asof`, `evidence_by_horizon`, and scorecard fields byte-for-byte match API response.

---

### TC-3 — Never-backfilled run still inserts forward_returns synchronously and idempotently

**Type:** api  
**Preconditions:**
- `ScannerRun` fixture whose forward returns have never been backfilled (mirrors existing create-once test)
- SQL statement tracking enabled

**Steps:**
1. Call `GET /api/backtest` for the run's as-of
2. Verify `ForwardReturn` rows are inserted
3. Call `GET /api/backtest` again for the same as-of
4. Inspect second request's SQL statement log

**Expected outcome:**
- First request: `INSERT` statements executed; inserted row count = (configured symbols for run) × (configured horizons) minus any NA gaps
- Second request: zero write statements issued
- Both requests return HTTP 200 with identical payload

**Pass criteria:** First call inserts expected row count; second call issues no write statements; payloads identical.

---

### TC-4 — Concurrent requests for genuinely-missing forward_returns handle races safely

**Type:** api  
**Preconditions:**
- `ScannerRun` fixture with genuinely missing forward returns (new concurrency test fixture)
- Concurrency race monitoring enabled

**Steps:**
1. Spawn 5 concurrent `GET /api/backtest` requests for the SAME as-of and run
2. Wait for all 5 to complete
3. Query `forward_returns` table for the run and verify row uniqueness
4. Inspect exception logs for unhandled errors

**Expected outcome:**
- All 5 requests complete without unhandled exception
- `forward_returns` table contains no duplicate `(run_id, symbol, horizon)` key
- At least one of the 5 requests demonstrably exercises the `IntegrityError`-tolerant rollback path (proven by assertion, not merely reachable in theory)

**Pass criteria:** No unhandled exceptions; no duplicate keys; `IntegrityError` rollback path exercised and asserted.

---

### TC-5 — Served payload is byte-identical before and after the fix across all horizons and as_of variants

**Type:** api  
**Preconditions:**
- TC-1 fixture (fully-backfilled run)
- Both pre-fix and post-fix backend states available for comparison

**Steps:**
1. Capture `compute_run_scorecard` returned dict
2. Capture `evidence_status`, `evidence_generated_at`, `evidence_asof`, `evidence_by_horizon` fields
3. Repeat step 1–2 after the fix lands
4. Diff fields with and without explicit `as_of` query parameter for every configured horizon

**Expected outcome:** Every field is byte-for-byte identical across all variants.

**Pass criteria:** All evidence and scorecard fields match exactly; test passes for every horizon; test passes with and without `as_of` parameter.

---

### TC-6 — Operator pure-concurrency re-measurement: backfill_forward_returns_ms phase collapses

**Type:** api  
**Preconditions:**
- Deep-basis backend running, host-guard-confined via `scripts/start-backend.sh`
- Affinity mask `0-3,8-11`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=4`, `MALLOC_ARENA_MAX=2`
- Host cooled to baseline (previous measurement at 47 °C minimum)
- `hwmon` sampler running (1 Hz), thermal watchdog armed
- Per-request `backtest_timing` log enabled (iter-18 landed)

**Steps:**
1. Sustain 6 concurrent `GET /api/backtest` pollers for the same duration as iter-18's TC-9 (pure reads, no concurrent ingest)
2. Parse `backtest_timing` log entries and extract `backfill_forward_returns_ms` phase duration for each request
3. Calculate mean and max for the phase
4. Record results in a new dated section of `reports/perf-budgets.md`

**Expected outcome:**
- `backfill_forward_returns_ms` mean ≤ 350 ms (down from iter-18's 881 ms)
- `backfill_forward_returns_ms` max ≤ 400 ms (down from iter-18's 999 ms)
- Log format directly comparable to iter-18's TC-9

**Pass criteria:** Mean ≤ 350 ms AND max ≤ 400 ms; results recorded in dated `reports/perf-budgets.md` section.

---

### TC-7 — Operator ingest-overlay re-measurement: breach count and max latency recorded or block documented

**Type:** api  
**Preconditions:**
- Same setup as TC-6, plus a concurrent ingest job queued and ready
- **CONTINGENT on owner go-ahead for the ingest trigger** (blocked last session by AG-10 safety classifier, not assumed autonomous)

**Steps:**
1. If ingest trigger is authorized: spawn concurrent ingest job alongside TC-6's 6-poller workload
2. Parse `backtest_timing` log and extract total request count and count of requests exceeding 1.5s
3. Record max latency observed
4. If ingest trigger remains blocked: document the block plainly (e.g., "AG-10 safety classifier blocked ingest trigger authorization")

**Expected outcome:**
- If authorized: breach count and max latency recorded in a new dated `reports/perf-budgets.md` section, directly comparable to iter-16/17 baseline (11/68 @ max 12.655s)
- If blocked: block reason and attempt documented plainly (not silently omitted)

**Pass criteria:** Results or block reason recorded in `reports/perf-budgets.md`; entry format directly comparable to iter-18's TC-10 and iter-16/17 baseline.

---

### TC-8 — Health check and non-disruptive carry-forward passes

**Type:** api  
**Preconditions:**
- Backend running (no kill/restart — non-disruptive)

**Steps:**
1. Poll `GET /api/health`
2. Inspect response for `readiness: "ready"`
3. Grep `logs/backend.log` for new crash/restart banner since the last recorded one

**Expected outcome:**
- HTTP 200 response
- `readiness: "ready"` field present
- No new crash banner in logs

**Pass criteria:** HTTP 200, `readiness: "ready"`, no new crash banner.

---

### TC-9 — Required-still-passing regression: J-01/J-03/J-05 golden replay all PASS

**Type:** artifact  
**Preconditions:**
- Deterministic golden-replay scripts for J-01, J-03, J-05 available
- Regression baseline established

**Steps:**
1. Execute golden replay for J-01
2. Execute golden replay for J-03
3. Execute golden replay for J-05
4. Verify all three report PASS verdict (exit code 0)

**Expected outcome:** All three journeys pass deterministic golden replay with no new failures attributable to this iteration's diff.

**Pass criteria:** All three replay scripts exit 0; no new failures introduced by this change.

---

### TC-10 — Operator live single-request byte-identity corroboration

**Type:** api  
**Preconditions:**
- Same deep-basis backend as TC-6/TC-7
- Fix deployed and running

**Steps:**
1. Issue a single live `GET /api/backtest` request for a representative run
2. Capture `evidence_by_horizon`, `evidence_status`, scorecard fields
3. Repeat capture against baseline (pre-fix measurement if available, or expected values)
4. Diff the two captures for byte-identity
5. **Bonus (non-blocking):** if Chrome MCP (port 9224) has recovered, capture a live browser screenshot of `/backtest` page

**Expected outcome:**
- Live response fields byte-identical to baseline/expected values (corroborates TC-5 against real deep-basis process, not unit-test fixture only)
- **Bonus:** browser screenshot if MCP recovered (not required — port-9224 wedge is a carried infra issue)

**Pass criteria:** Fields byte-identical; if browser screenshot captured, it renders `/backtest` page without errors.

---

## Summary

**Total test cases:** 10  
**API tests:** 9 (TC-1, TC-2, TC-3, TC-4, TC-5, TC-6, TC-7, TC-8, TC-10)  
**Artifact checks:** 1 (TC-9)  

**Execution notes:**
- TC-1 through TC-5 are unit/integration tests in `test_forward_testing_serving_split.py` and `test_forward_testing_concurrency.py` — developer-executed during implementation
- TC-6 through TC-8 and TC-10 are operator-performed measurements requiring `scripts/start-backend.sh` launch and host-guard confinement (AG-10 class)
- TC-7 is **contingent** on owner authorization for ingest-trigger submission (blocked last session; attempt and outcome to be documented regardless)
- TC-9 is regression-check via deterministic golden replay (required-still-passing journeys J-01/J-03/J-05)
- Chrome MCP browser verification (TC-10 bonus) is explicitly non-blocking — port-9224 wedge is a carried infra issue confirmed unreachable at spec-writing time
