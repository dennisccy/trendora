# goal-ops-hardening-iter-13 Functional Test Plan

**Phase:** goal-ops-hardening-iter-13  
**Date:** 2026-07-23  
**Frontend Present:** yes

## Phase Goal

Bring `GET /api/indexes?full=true` — the default hot key read by Dashboard (`/`) and Data Manager (`/data`) on mount — within its committed ≤1.5s budget by warming this unparameterized key at ingest time (`IndexSeriesCache` table + `index_series_cached` wrapper + finalize-hook warm step), so J-06 (the session's last non-passing Must-have journey) can be scored on a genuinely in-budget measurement instead of the confirmed 2138.7–2257.7ms over-budget baseline.

---

## Test Cases

### TC-01 — Hot-key browser latency on Data Manager (`/data`)

**Type:** browser  
**Preconditions:**
- `IndexSeriesCache` table exists and is populated with a warmed row for the default hot key (`range_key=cfg.index_chart.default_range`, `full=True`)
- No concurrent ingest job is running (confirmed via `logs/backend.log`)
- Host is verifiably idle: `logs/hwmon/hwmon.csv` shows load1 <2.0 at or immediately before each test load

**Steps:**
1. Open Chrome DevTools Network tab with cache disabled (DevTools → Settings → Network → Disable cache)
2. Fresh-navigate to `http://localhost:3255/data` (new tab, not reused)
3. Record the Resource Timing duration for `GET /api/indexes?full=true` from the Network tab (DOMContentLoaded mark)
4. Close the tab completely
5. Repeat steps 1–4 two more times (three independent fresh navigations total)
6. Cross-check `logs/hwmon/hwmon.csv` at each measurement's exact timestamp to confirm load1 <2.0

**Expected outcome:** All three measurements show `GET /api/indexes?full=true` completes in ≤1500ms

**Pass criteria:**
- Resource Timing duration for each of the three `/data` loads is ≤1500ms
- `logs/hwmon/hwmon.csv` load1 <2.0 at each of the three measurement timestamps
- No measurement is >= 1501ms (no margin; must be strictly within budget)

---

### TC-02 — Hot-key browser latency on Dashboard (`/`)

**Type:** browser  
**Preconditions:**
- Same as TC-01: `IndexSeriesCache` warmed for default hot key, no concurrent ingest, host idle

**Steps:**
1. Open Chrome DevTools Network tab with cache disabled
2. Fresh-navigate to `http://localhost:3255/` (new tab, not reused)
3. Record Resource Timing duration for `GET /api/indexes?full=true` from Network tab
4. Cross-check `logs/hwmon/hwmon.csv` at this measurement's exact timestamp

**Expected outcome:** Dashboard's hot-key read also completes in ≤1500ms

**Pass criteria:**
- Resource Timing duration for `/` load is ≤1500ms
- `logs/hwmon/hwmon.csv` load1 <2.0 at the measurement timestamp

---

### TC-03 — Cached response byte-identity

**Type:** api  
**Preconditions:**
- `IndexSeriesCache` has warmed the default hot key
- No ingest job is running between requests

**Steps:**
1. Call `GET /api/indexes?full=true` (no `range` param, default assumed; `full=True`)
2. Store the full JSON response (including `series`, `asof_date`, `range`, `ranges`)
3. Wait 1 second
4. Call `GET /api/indexes?full=true` again with identical parameters
5. Compare all fields from both responses
6. In Python/test code, directly call `compute_index_series(session, as_of=None, range_key=cfg.index_chart.default_range, full=True)` on the same DB state
7. Compare the cached API response to the direct uncached call's output

**Expected outcome:** All three artifacts are byte-identical (JSON-equal)

**Pass criteria:**
```bash
curl -s "http://localhost:8255/api/indexes?full=true" | jq > /tmp/tc03_call1.json
curl -s "http://localhost:8255/api/indexes?full=true" | jq > /tmp/tc03_call2.json
diff /tmp/tc03_call1.json /tmp/tc03_call2.json
# Exit code 0 (no diff)
# Direct uncached call also matches exactly
```

---

### TC-04 — Cache invalidation on new bar ingest

**Type:** api  
**Preconditions:**
- `IndexSeriesCache` is warmed with current data (e.g., 9 symbols under `index_chart.symbols`)
- A backfill/fetch job touching one configured index symbol is ready to run (e.g., fetch SPY's latest day)

**Steps:**
1. Note the current maximum date in the cached `series` (e.g., 2026-07-22)
2. Run a bounded backfill/fetch job that lands a new bar for a configured index symbol (e.g., `python scripts/backfill.py --symbol SPY --end-date 2026-07-23`)
3. Wait for the job to complete and the finalize hook to execute
4. Call `GET /api/indexes?full=true` (the hot key, now cache-invalidated)
5. Verify the new bar's date appears in the response's `series`

**Expected outcome:** The new bar's data point appears in the cached response after finalize-hook invalidation

**Pass criteria:**
- The returned `series` includes a point for the new bar's date (2026-07-23 in the example)
- The new point's value matches the freshly-ingested bar (no stale pre-ingest snapshot)

---

### TC-05 — `aggregates_refreshed` enumeration integrity

**Type:** api  
**Preconditions:**
- Test database is clean (no prior ingest runs with `index_series` in `aggregates_refreshed`)
- Backend is running

**Steps:**
1. Run an ingest job (backfill/fetch/rebuild) that successfully warms the index-series cache
2. Query the resulting `data_provider_runs` row: `SELECT aggregates_refreshed FROM data_provider_runs ORDER BY id DESC LIMIT 1;`
3. Parse the JSON list and check for presence of `"index_series"`
4. Run another ingest that does NOT warm the index-series cache (e.g., due to error or early abort)
5. Query the next `data_provider_runs` row and check for ABSENCE of `"index_series"`

**Expected outcome:** `"index_series"` is present in `aggregates_refreshed` only when the warm step actually persisted a row; never fabricated

**Pass criteria:**
```bash
# After successful warm run:
SELECT aggregates_refreshed FROM data_provider_runs ORDER BY id DESC LIMIT 1;
# Contains JSON string ["...", "index_series", ...]

# After run where warm step raised/was skipped:
SELECT aggregates_refreshed FROM data_provider_runs ORDER BY id DESC LIMIT 1;
# Does NOT contain "index_series" (may be null or empty list, per existing convention)
```

---

### TC-06 — Non-hot-key requests bypass cache

**Type:** api  
**Preconditions:**
- `IndexSeriesCache` is populated for the default hot key
- Backend is running
- A known pre-iteration baseline response for a non-default range exists

**Steps:**
1. Call `GET /api/indexes?range=3M&full=true` (explicit non-default range)
2. Call `GET /api/indexes?full=true&as_of=2026-06-01` (explicit historical `as_of`)
3. For each call, verify the response is computed via the uncached path (not served from cache)
4. Compare to a pre-iteration baseline to confirm byte-identity

**Expected outcome:** Parameterized requests bypass `IndexSeriesCache` entirely and return byte-identical output to pre-iteration behavior

**Pass criteria:**
```bash
# Explicit range bypasses cache:
curl -s "http://localhost:8255/api/indexes?range=3M&full=true" | jq .series > /tmp/tc06_3m.json
# Should compute fresh, not cache-serve
# Compare to pre-iteration baseline: diff should be zero (or only `asof_date` field newer)

# Explicit as_of bypasses cache:
curl -s "http://localhost:8255/api/indexes?full=true&as_of=2026-06-01" | jq .series > /tmp/tc06_asof.json
# Should compute fresh, not cache-serve
```

---

### TC-07 — MemoryError isolation in warm step

**Type:** api  
**Preconditions:**
- Test can artificially raise `MemoryError` in the index-series warm step (via mock or code injection)
- Backend is running

**Steps:**
1. Inject a mock/patch that raises `MemoryError` in `app.engine.indexes.index_series_cached` during the warm step
2. Run an ingest job (backfill/fetch/rebuild)
3. Verify the job completes without flipping to `failed` status
4. Check `logs/backend.log` for the `MemoryError` exception message and `_release_process_memory()` call
5. Query the resulting `data_provider_runs` row and verify `aggregates_refreshed` does NOT contain `"index_series"`

**Expected outcome:** `MemoryError` is caught and isolated; the ingest job's terminal status (`ok`/`partial`) is unaffected; memory is released; `"index_series"` is omitted from `aggregates_refreshed`

**Pass criteria:**
- Ingest job exits with status `ok` or `partial` (not `failed`)
- `logs/backend.log` contains exception message for the `MemoryError`
- `logs/backend.log` contains `_release_process_memory()` call for the index-series warm step
- `data_provider_runs.aggregates_refreshed` does NOT include `"index_series"`

---

### TC-08 — Required journeys still passing

**Type:** api  
**Preconditions:**
- J-01, J-03, J-04, J-05 have been previously verified as `passing` in earlier iterations
- All necessary seed data and models are initialized

**Steps:**
1. Run deterministic golden replay for J-01 (per `docs/goal.md`)
2. Run deterministic golden replay for J-03
3. Run deterministic golden replay for J-04
4. Run deterministic golden replay for J-05
5. Compare results to prior iteration's passing verdicts
6. Record any LLM fallback invocations (per goal-mode contract)

**Expected outcome:** All four journeys re-verify as `passing`; no regression to `failing`

**Pass criteria:**
- Each of J-01, J-03, J-04, J-05 reaches `passing` verdict (via deterministic replay + LLM fallback if needed)
- Evidence is cited in iteration handoff
- No journey transitions from `passing` → `failing`

---

### TC-09 — In-budget pages spot-check (no regression)

**Type:** artifact  
**Preconditions:**
- `reports/perf-budgets.md` from iter-11/iter-12 lists 10 pages/endpoints already confirmed in-budget
- Browser is ready to perform fresh-navigation loads

**Steps:**
1. Select one or two high-impact pages from the 10 in-budget set (e.g., `/` Dashboard, `/evidence`)
2. Fresh-navigate to each page in Chrome with DevTools Network cache disabled
3. Record Time to Interactive (TTI) or the critical path endpoint's Resource Timing
4. Compare to the budget listed in `reports/perf-budgets.md`

**Expected outcome:** Spot-check pages remain within committed budget; no regression

**Pass criteria:**
- Each spot-checked page's TTI/critical-path endpoint is ≤ its committed budget (per `reports/perf-budgets.md`)
- No page exceeded budget by ≥50ms

---

### TC-10 — Targeted backend tests pass (host-guard confined)

**Type:** api  
**Preconditions:**
- Backend source code is built and database schema is initialized
- Host-guard environment variables are set: `TMPDIR=/home/dennis-chan/.cache/iad/iad.goal-ops-hard-3c35d720.791787`, `OMP_NUM_THREADS=4`, `OPENBLAS_NUM_THREADS=4`, etc.

**Steps:**
1. Set environment: `export TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-3c35d720.791787" OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`
2. Run targeted test subset under host-guard CPU affinity:
   ```bash
   taskset -c 0-3,8-11 pytest apps/backend/tests/test_indexes.py -v
   taskset -c 0-3,8-11 pytest apps/backend/tests/test_api_indexes.py -v
   taskset -c 0-3,8-11 pytest apps/backend/tests/test_data_manager.py -v -k "test_finalize_hook_index_series" --tb=short
   ```
3. Capture pass/fail counts and any exceptions
4. Compare to pre-iteration baseline

**Expected outcome:** All targeted tests pass, with zero new failures beyond the pre-existing documented `tests/test_db.py::test_create_all_produces_expected_tables` failure

**Pass criteria:**
```bash
# Example output (values vary by test file size):
# test_indexes.py: 5 passed
# test_api_indexes.py: 3 passed
# test_data_manager.py::test_finalize_hook_index_series*: 2 passed
# Total: 10 passed, 0 failed
# Exit code 0
```

---

### TC-11 — Dev handoff exists and is complete

**Type:** artifact  
**Preconditions:**
- Iteration development is complete

**Steps:**
1. Check for file existence: `docs/handoffs/goal-ops-hardening-iter-13-dev.md`
2. Open the file and verify:
   - Lists all changed backend files (models.py, indexes.py, api/indexes.py, data_manager.py, tests/*)
   - States whether the three `/data` control readings (TC-01) landed ≤1.5s or not
   - States whether the `/` spot-check (TC-02) landed ≤1.5s or not
   - Does NOT round marginal over-budget readings into "close enough"
3. Cross-reference against the actual source-code diff to confirm completeness

**Expected outcome:** Dev handoff is present, lists all changed files, and explicitly states whether the control readings held budget

**Pass criteria:**
- File path exists: `/home/dennis-chan/Git/trendora/docs/handoffs/goal-ops-hardening-iter-13-dev.md`
- File contains sections: "Changed Files", "Control Readings" (or similar), "Status" (PASS or PARTIAL depending on measurements)
- No vague language like "appears to be in budget" or "approximately"; statements are clear (e.g., "2045ms > 1500ms budget: FAIL" or "1389ms ≤ 1500ms budget: PASS")

---

### TC-12 — `forward_testing.py` byte-unchanged (AG-8 integrity)

**Type:** artifact  
**Preconditions:**
- Iteration is complete and all changes are committed

**Steps:**
1. Get the pre-iteration hash of `apps/backend/app/engine/forward_testing.py` (from prior iteration or from git)
2. Compute current SHA-256 of the file
3. Compare byte-for-byte (no whitespace changes allowed, no code changes)

**Expected outcome:** File is unchanged from pre-iteration state

**Pass criteria:**
```bash
# SHA-256 of current file matches pre-iteration file exactly:
sha256sum apps/backend/app/engine/forward_testing.py
# Output matches pre-iteration baseline
# Git diff shows 0 lines changed in this file
```

---

## Summary

**Total test cases:** 12  
**Browser tests:** 2 (TC-01, TC-02)  
**API tests:** 6 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-10)  
**Artifact/unit tests:** 4 (TC-08, TC-09, TC-11, TC-12)

**Critical pass criterion:** TC-01 and TC-02 must BOTH land ≤1500ms. If either exceeds this budget, J-06 remains `partial` and the iteration goal is not met (per iter-12's own lesson: score the number, not the fact that code was written).

**Required handoff:** Dev handoff at `docs/handoffs/goal-ops-hardening-iter-13-dev.md` must state plainly whether the measurements passed or failed; no rounding into "close enough."
