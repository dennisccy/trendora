# Goal Iteration 30 Functional Test Plan

**Phase:** goal-ops-hardening-iter-30
**Date:** 2026-07-29
**Frontend Present:** no

## Phase Goal

Bound `compute_forward_aggregates`'s three unbounded in-RAM accumulators (AG-8 finding) and close J-06's performance budget documentation and replay verification gaps. The fix removes a live memory-exhaustion failure mode in the ingest-time forward-aggregate warm without changing the API or user-visible behavior.

## Test Cases

### TC-01 — Ingest warm completes with zero MemoryError in compute_forward_aggregates

**Type:** api
**Preconditions:**
- Backend service running against the live database
- `logs/backend.log` is clean and ready to capture output
- No concurrent ingest jobs running; verifiable via `logs/hwmon/hwmon.csv` idle check

**Steps:**
1. Start the backend service with `scripts/start-backend.sh`
2. Trigger the ingest-time forward-aggregate warm for all 5 configured horizons in a single long-lived process
3. Monitor `logs/backend.log` for the entire warm completion
4. Simultaneously poll `GET /api/health` at 1 Hz throughout the warm

**Expected outcome:**
- The warm-up process completes without raising `MemoryError`
- No error lines containing `MemoryError` with `compute_forward_aggregates`, `stock_obs`, or `ret_by_run_symbol` in the frame appear in `logs/backend.log`
- All 5 horizons finish processing
- The corresponding `data_provider_runs` row lists `forward_aggregates` in `aggregates_refreshed` with no partial/failed status

**Pass criteria:**
- `logs/backend.log` contains zero `MemoryError` lines with `forward_testing.py` frame targeting `compute_forward_aggregates` during the warm window
- Grep result: `grep -c "MemoryError.*forward_testing.py.*compute_forward_aggregates\|stock_obs\|ret_by_run_symbol" logs/backend.log` returns 0
- Boot banner line number is cited in the QA report (process quality requirement per TC-9)

---

### TC-02 — Byte-identical output across all 5 horizons (with and without as_of)

**Type:** api
**Preconditions:**
- Fixture database with known, small pool is available
- Pre-chunk reference implementation code is at a prior git commit (or tagged)
- All 5 configured horizons are defined in `config.yaml`

**Steps:**
1. Run the pre-chunk `compute_forward_aggregates` implementation for all 5 horizons with `as_of=None`
2. Capture all output slices: `by_bucket`, `by_setup`, `by_regime`, `by_sector`, `by_rank_band`, `control_group`, `attribution`, VCP/pullback/breakout groupings, `excess` (vs SPY, vs QQQ)
3. Run the post-chunk implementation for the same 5 horizons with `as_of=None`
4. Capture the identical set of output slices
5. Repeat steps 1–4 with a representative `as_of` date (e.g., 2026-05-29)
6. Deep-equal comparison on all returned payloads

**Expected outcome:**
- Every returned slice is byte-identical between pre-chunk and post-chunk implementations
- No differences in grouped means, control cohort composition, attribution slices, or excess calculations
- Decimal precision is preserved exactly (no rounding or float-precision drift)

**Pass criteria:**
- Fixture test assertion passes with 100% payload equality across all 5 horizons × 2 `as_of` conditions (10 comparisons total)
- Test name: `test_compute_forward_aggregates_chunked_byte_identical` or equivalent
- No assertion errors; test completes in deterministic fashion

---

### TC-03 — Shipped config value produces multiple chunks on live basis

**Type:** api
**Preconditions:**
- Shipped `config.yaml` is loaded via `load_config()`
- Live database with real forward_returns/scanner_results tables is present
- The new run-chunk width config knob is defined in `WalkForwardCfg` with its own dedicated key (RUN-count unit)

**Steps:**
1. Resolve the shipped config value via `load_config()`
2. Query the live database for distinct run count across a representative horizon (e.g., the most frequently-used one)
3. Calculate expected chunk count: `ceil(distinct_run_count / chunk_width)`
4. Run the chunking loop for that horizon with the shipped chunk-width value
5. Count actual chunks produced

**Expected outcome:**
- Actual chunk count > 1 (i.e., the bound is actually exercised, not just defined)
- The new config knob is named distinctly (not `research.read_batch_size` or `research.factor_join_run_chunk`)
- The config knob unit is RUN-count, not ROW-count

**Pass criteria:**
- Assertion: `chunks_produced > 1`
- Test name: `test_shipped_forward_aggregate_chunk_width_binds_on_live_basis` or equivalent
- Config key inspection: verify new key exists in `WalkForwardCfg` and in `config.yaml` with a live measurement noted in a comment

---

### TC-04 — Health endpoint responds 200 throughout warm under budget

**Type:** api
**Preconditions:**
- Backend running the ingest warm (same as TC-01)
- Existing committed latency budget for `/api/health` is known

**Steps:**
1. During the ingest-time warm (as in TC-01), poll `GET /api/health` at 1 Hz
2. Capture response status code and response time for each poll
3. Collect all responses until the warm completes
4. Verify 100% of responses are HTTP 200
5. Verify no response time exceeds the committed budget

**Expected outcome:**
- Every poll over the multi-hour warm returns HTTP 200
- No frozen or unresponsive window occurs
- All response times fall within the existing committed budget

**Pass criteria:**
- Count of 200 responses / total polls == 1.0 (100%)
- Max response time <= committed budget value
- Health endpoint never times out or fails during the warm window

---

### TC-05 — Factor Lab page renders with real numeric values (regression spot-check)

**Type:** browser
**Preconditions:**
- Backend service running against live database
- Host is verifiably idle (no concurrent ingest jobs, checked via `logs/hwmon/hwmon.csv`)
- Real Chrome browser available for automation

**Steps:**
1. Open the Factor Lab page at `/research/factor-lab` in a real browser
2. Wait for page load to complete (check for network quiet)
3. Inspect the decile table for populated numeric values
4. Inspect rank-IC figures for populated numeric values
5. Check browser console for errors
6. Verify HTTP response status

**Expected outcome:**
- Page HTTP 200
- Decile table renders with real numeric (not blank/NA/error) values
- Rank-IC figures display numeric values
- Browser console shows zero errors related to the rendering
- No blank table cells or "undefined" placeholders

**Pass criteria:**
- HTTP 200 on page load
- Decile table row count > 0 and all cells populated with numeric values (not empty/NA)
- Rank-IC figure data points present and numeric
- Console error count == 0 (or errors are pre-existing, unrelated to this iteration)
- Screenshot saved to `reports/qa/goal-ops-hardening-iter-30-evidence/TC-05-factor-lab.png`

---

### TC-06 — Performance budgets updated with this iteration's measurements

**Type:** artifact
**Preconditions:**
- Developer has completed a fresh 11-page real-browser TTI/on-load-latency sweep
- Developer has measured boot-to-health latency (≤5s budget)
- `reports/perf-budgets.md` exists with prior dated sections showing the format

**Steps:**
1. Developer appends a new dated section to `reports/perf-budgets.md` with this iteration's curl-based 11-page sweep
2. Each reading is scored PASS or WARN against its committed budget
3. Boot-to-health measurement is included and scored
4. Run `git diff reports/perf-budgets.md` to verify the file is modified

**Expected outcome:**
- `reports/perf-budgets.md` is modified by this iteration (git diff is non-empty)
- New dated section is present with this iteration's measurements
- Every reading is explicitly PASS or WARN (no unscored values)
- Budget comparisons are correct (measured value vs committed limit)

**Pass criteria:**
- `git diff reports/perf-budgets.md` output is non-empty
- New section header includes a date matching the iteration date (2026-07-29 or close)
- All readings are marked PASS or WARN
- File is parseable and follows the established convention in the document

---

### TC-07 — J-06.json deterministic replay passes with zero failures

**Type:** artifact
**Preconditions:**
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` exists and is committed
- The deterministic replay lane and demo-runner are available
- `verify` mode is enabled in the replay runner

**Steps:**
1. Run the deterministic replay lane for `J-06.json` via the demo-runner's verify mode
2. Capture the merged results output (typically a CSV or JSON with per-journey rows)
3. Inspect the J-06 row for verdict and failure count

**Expected outcome:**
- J-06 row in the merged results shows a PASS verdict
- Failure count for J-06 is zero
- No reconciliation overturns or data-integrity issues
- Replay completes without crashing

**Pass criteria:**
- J-06 row verdict == PASS
- J-06 row failure count == 0
- Merge file is non-empty and parseable
- No reconciliation overturns present

---

### TC-08 — Required-still-passing journeys remain green

**Type:** artifact
**Preconditions:**
- Required journeys: J-01, J-03, J-04, J-05, J-08, J-09
- Golden or LLM-fallback replay is available for each
- Deterministic replay infrastructure is functioning

**Steps:**
1. Run deterministic golden replay for each of the 6 required journeys
2. For any journey without a golden, run the LLM fallback replay
3. Collect all results into a merged results table

**Expected outcome:**
- All 6 journeys show PASS verdict in the merged results
- Zero FAIL rows across all 6 journeys
- Zero reconciliation overturns
- All measured assertions pass (if applicable to each journey)

**Pass criteria:**
- Pass count == 6
- Fail count == 0
- Overturn count == 0
- Replay summary shows "PASS" for the set

---

### TC-09 — MemoryError claims cite exact log line numbers

**Type:** artifact (process quality verification)
**Preconditions:**
- QA report for this iteration is written
- Any "zero MemoryError" claim appears in the report

**Steps:**
1. Inspect the QA report for any statement like "zero MemoryError" or "no memory exhaustion"
2. For each such claim, verify the report cites the exact `logs/backend.log` line number of the boot banner or process window it counted from
3. Example format: "zero MemoryError lines (counted from line 4521, boot banner 'Starting backend service')"

**Expected outcome:**
- Every MemoryError claim includes a specific `logs/backend.log` line number or line range
- The line number is verifiable (running `sed -n '<line>p' logs/backend.log` retrieves a recognizable boot banner or timestamp)
- No unqualified claims like "zero MemoryError" without a cited window

**Pass criteria:**
- Report inspection reveals all MemoryError claims include line numbers or ranges
- Each line number is within the documented backend log window (e.g., boot time ± ingest duration)
- No unqualified claims without context

---

## Unit Test Assertions (API-level, not browser tests)

### UT-01 — Chunk boundary doesn't double-count runs

Given a run whose observations span a chunk boundary, verify its contribution to grouped means is counted exactly once. This is an error-case unit test in `test_forward_testing.py` or equivalent.

### UT-02 — Empty chunk doesn't crash merge

Given a scenario where a chunk has zero qualifying observations, verify the merge step handles it gracefully without raising an exception or producing NaN/infinity values in the output.

---

## Summary

**Total test cases:** 9 (TC-01 through TC-09)

**By type:**
- API tests: 4 (TC-01, TC-02, TC-03, TC-04)
- Browser tests: 1 (TC-05)
- Artifact checks: 4 (TC-06, TC-07, TC-08, TC-09)

**By scope:**
- Live backend behavior: TC-01, TC-04, TC-05
- Fixture-backed correctness: TC-02, TC-03
- Deterministic replay: TC-07, TC-08
- Process/artifact quality: TC-06, TC-09

**Critical path:**
- TC-01 (zero MemoryError) and TC-02 (byte-identity) are blocking — if either fails, J-07 cannot pass.
- TC-06 and TC-07 close J-06's mechanical gaps.
- TC-08 ensures no regression on the 6 already-passing journeys.
