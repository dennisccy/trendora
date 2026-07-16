# Goal Iteration 41 — Functional Test Plan

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Frontend Present:** yes

## Phase Goal

On each certified claim's detail card on `/evidence`, the user sees a **phase-conditional expectations panel** displaying historical distributions (median/p90) of max-drawdown depth, underwater duration, time-to-recover, and longest losing streak — split by causal market phase at entry — so dry spells read as known historical fact rather than surprise.

## Test Cases

### TC-01 — Expectations panel renders on a certified claim row

**Type:** browser
**Preconditions:** The `/evidence` page loads with at least one certified claim card visible

**Steps:**
1. Navigate to `/evidence` in the browser
2. Wait for the page and all claim cards to fully load
3. Locate the first certified claim card
4. Scroll within the card to reveal content below the fold
5. Capture a full-page screenshot including the expectations panel

**Expected outcome:** The expectations panel is visible below the claim-row's primary fields (verdict/control/registration), displaying a table structure with phase rows and measure columns

**Pass criteria:** The panel is rendered and contains text with "historically" language (no promise/forecast phrasing); the screenshot shows the actual panel content (not a blank or header-only frame); md5 of the screenshot differs from blank/boilerplate control images

---

### TC-02 — Per-phase distributions render with correct structure (all four measures)

**Type:** browser
**Preconditions:** A certified claim on `/evidence` is fully loaded with expectations panel visible

**Steps:**
1. Open `/evidence` and locate a certified claim card
2. Scroll the expectations panel into view
3. Inspect the panel's table structure for all market phases present in the data
4. Verify each phase row displays columns for: max-drawdown depth, underwater duration, time-to-recover, longest losing streak
5. Capture an element-clip screenshot of the expectations table

**Expected outcome:** Each phase row shows four measure columns, each displaying either a distribution (median/p90 + n) or "insufficient (n=…)" text for below-floor phases

**Pass criteria:** All four measure columns are present for each phase; distribution cells contain numeric values formatted with `.toFixed()` (e.g., "12.5%"); insufficient cells read exactly "insufficient (n=X)" with a count

---

### TC-03 — Below-floor phases render "insufficient (n=…)" text, not blank cells

**Type:** browser
**Preconditions:** The expectations panel is visible on a claim card; at least one phase has below-floor sample count

**Steps:**
1. Locate a phase row in the expectations table
2. Examine a cell for a phase expected to have below-floor sample count (n < 30)
3. Capture the cell content
4. Verify the text pattern

**Expected outcome:** The cell displays "insufficient (n=X)" where X is the actual sample count for that phase

**Pass criteria:** No blank cells; text matches the pattern "insufficient \(n=\d+\)"; numeric n value is non-negative

---

### TC-04 — Historical wording and survivorship caveat are present (no forecast language)

**Type:** browser
**Preconditions:** The expectations panel is rendered on a certified claim

**Steps:**
1. Open `/evidence` to view a claim card with expectations panel
2. Read the panel's title and descriptive text
3. Search for any of these disallowed phrases: "expect to", "you will", "forecast", "predict", "likely to", "target", "buy", "sell", "trim", "reduce"
4. Verify the survivorship-bias caveat is displayed

**Expected outcome:** Panel text uses only historical language ("historically saw", "median max-DD", "time underwater"); survivorship caveat is visible and readable

**Pass criteria:** Zero matches for disallowed forecast/advice verbs; caveat text is present and contains "Stooq" and "delisted"; text contains only descriptive past-tense phrasing

---

### TC-05 — Underwater_days and time_to_recover_days helpers compute correctly (unit)

**Type:** api
**Preconditions:** Backend is running; test fixtures are available

**Steps:**
1. Run the backend test suite focusing on `test_forward_testing.py`
2. Verify tests for `underwater_days()` and `time_to_recover_days()` helpers pass
3. Capture test output showing fixture-exact assertions

**Expected outcome:** Both helpers pass fixture tests with constructed series of known underwater spans and recovery points; NA cases correctly return None/NA for horizons with no recovery or insufficient post-bars

**Pass criteria:** Test names matching `test_underwater_days*` and `test_time_to_recover_days*` all pass; test count and fixtures cover: known underwater spans (n ≥ 1 runs), recovery points within horizon, NA on < horizon post-bars, NA gate matching `max_drawdown` semantics

---

### TC-06 — Underwater_days helper correctly gates on horizon length (no fabricated zeros)

**Type:** api
**Preconditions:** Backend test fixtures for underwater_days

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "underwater_days" -v`
2. Verify fixture test for insufficient post-bars returns None, not 0
3. Check test assertions for exact NA semantics

**Expected outcome:** Helper returns None when post_bars < horizon; never returns fabricated 0; NA gate matches `max_drawdown` gate exactly

**Pass criteria:** Test assertion explicitly checks `is None` (not `== 0`); test name includes "insufficient" or "horizon" case; test passes

---

### TC-07 — Time_to_recover_days helper correctly gates on recovery point (never fabricates horizon-sentinel)

**Type:** api
**Preconditions:** Backend test fixtures for time_to_recover_days

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "time_to_recover_days" -v`
2. Verify fixture test where close never returns to entry level within horizon → returns None
3. Check fixture covering recovery within horizon → returns exact bar count
4. Verify NA gate matches `max_drawdown`

**Expected outcome:** Helper returns None (not horizon or sentinel value) when recovery never occurs in-window; returns exact bar count when recovery point exists

**Pass criteria:** Test fixture has two cases: (1) no recovery → None, (2) recovery at bar N → N; both pass; NA gate assertion matches `max_drawdown` semantics

---

### TC-08 — Max_drawdown helper is reused, not reforked

**Type:** api
**Preconditions:** Backend tests for forward_return aggregation

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "forward_return" -v`
2. Grep the implementation of `_insert_run_forward_returns` for call count of `max_drawdown`
3. Verify only ONE call to `max_drawdown` per row (at the original location)
4. Confirm new code does not re-derive or copy `max_drawdown` logic

**Expected outcome:** No second implementation of `max_drawdown` exists; the original helper is called once per forward-return row

**Pass criteria:** Grep finds exactly one `max_drawdown(...)` call per row in `_insert_run_forward_returns` insertion loop; test output shows no duplicate DD-depth computations; byte-identity test passes (existing expectation tests unchanged)

---

### TC-09 — Compute_drawdown_expectations aggregation produces exact per-phase median/p90/n

**Type:** api
**Preconditions:** Backend test fixtures for `compute_drawdown_expectations`

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "compute_drawdown_expectations" -v`
2. Verify fixture test with constructed cohort and known per-phase observations
3. Check test assertions for exact median/p90 calculations
4. Verify n count matches fixture setup

**Expected outcome:** Aggregation computes exact median and p90 percentiles per phase; n matches observation count; no rounding errors

**Pass criteria:** Test fixture constructs known values (e.g., cohort with 3 observations in Correction phase, 5 in Bull), computes aggregation, asserts median/p90 exact match; all test names matching `compute_drawdown_expectations*` pass

---

### TC-10 — Below-floor phase emits "insufficient" marker, not partial distribution

**Type:** api
**Preconditions:** Backend test for `compute_drawdown_expectations` with below-floor phase

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "insufficient" -v`
2. Verify fixture test with a phase having n < walk_forward.min_sample (30)
3. Check aggregation output structure for that phase

**Expected outcome:** Phase with n < 30 emits a marker object with `"insufficient": True` and `n` value, not a partial median/p90 dict

**Pass criteria:** Test assertion checks phase-insufficient marker structure; output JSON contains "insufficient" key (not "median"/"p90" for that phase); n value is present and correct

---

### TC-11 — Loss-streak computed at walk-forward cadence (no daily double-count)

**Type:** api
**Preconditions:** Backend test for loss-streak calculation in `compute_drawdown_expectations`

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "loss_streak" -v`
2. Verify fixture test with overlapping horizons (daily bars)
3. Check that longest-streak is counted at cadence iteration (e.g., weekly or monthly), not daily
4. Verify documentation mentions walk-forward cadence explicitly

**Expected outcome:** Loss-streak computed from walk-forward-cadence observations (asof_date list order), not daily bar overlaps; fixture proves no double-counting

**Pass criteria:** Test fixture iterates walk-forward asof_dates in order; fixture shows two consecutive negative returns → streak = 2; test passes; docstring mentions "walk-forward cadence" not "daily"

---

### TC-12 — Loss-streak below floor renders "insufficient (n=…)"

**Type:** api
**Preconditions:** Backend test for loss-streak floor (walk_forward.streak_min_n)

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "streak_min_n" -v`
2. Verify fixture test with a phase having n_losses < walk_forward.streak_min_n
3. Check aggregation output for that phase-measure cell

**Expected outcome:** Loss-streak cell renders "insufficient (n=X)" when phase-specific loss-count below floor; the `n` refers to loss-streak count, not the measure's distribution count

**Pass criteria:** Test fixture constructs cohort with phase where n_losses < streak_min_n; aggregation returns "insufficient" marker for that cell; test passes

---

### TC-13 — Causal phase-at-entry label is correct (no lookahead)

**Type:** api
**Preconditions:** Backend test for phase context by date in `compute_drawdown_expectations`

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -k "phase_context" -v`
2. Verify fixture test where observation has asof_date = entry date
3. Check that phase_context_by_date is called with (session, asof_date) for entry date
4. Verify test confirms a future bar does NOT change the phase label

**Expected outcome:** Phase label is looked up AS-OF the entry date; a bar from a later date does not retroactively change the stored phase label or any forward-return value

**Pass criteria:** Test fixture has two dates D and D+N; phase at D is looked up; adding a bar at D+N does not change the stored value at D; test assertion passes for both the lookup and the no-change case

---

### TC-14 — Existing forward_testing/scoring tests remain unedited and green (no regression)

**Type:** api
**Preconditions:** Backend test suite for forward_testing and scoring engines

**Steps:**
1. Run `pytest apps/backend/tests/test_forward_testing.py -v` (full suite, not just iter-41 tests)
2. Run `pytest apps/backend/tests/test_scoring.py -v`
3. Capture full output with pass/fail counts
4. Verify zero test edits in the output log

**Expected outcome:** All pre-existing tests pass without modification; new iter-41 tests are added but no existing test is edited; scores and regime stay byte-identical

**Pass criteria:** Full test output shows all `test_forward_testing.py` tests pass (existing + new); `test_scoring.py` tests pass; git diff shows test additions only, no edits to existing test lines; test counts match expected baseline + new tests

---

### TC-15 — GET /api/evidence additive expectations field (session-provided path)

**Type:** api
**Preconditions:** Backend is running; /api/evidence endpoint is accessible

**Steps:**
1. Call `curl -s http://localhost:8000/api/evidence | jq '.'`
2. Inspect response structure for first claim
3. Verify expectations field is present and is an object (not null)
4. Check structure contains keys: phases, and per-phase median/p90/n

**Expected outcome:** Response includes an `expectations` field on each claim; field is an object with per-phase data; field is only present when session is provided (real endpoint, not test-fixture path)

**Pass criteria:** Response HTTP 200; `expectations` key is present; if data exists, value is a JSON object with phase keys and distribution values

---

### TC-16 — GET /api/evidence expectations field is absent when session is None (backward compatibility)

**Type:** api
**Preconditions:** Backend test calling `build_evidence_payload(ledger_path)` WITHOUT session/config params

**Steps:**
1. Run `pytest apps/backend/tests/test_evidence.py -k "build_evidence_payload" -v`
2. Verify fixture test that calls `build_evidence_payload(str(ledger))` with ONE positional arg (no session)
3. Check response structure does not include expectations
4. Verify test_canonical_ledger_frozen_golden passes unedited

**Expected outcome:** When session is None, `expectations` is absent or empty per claim; response is still 200; no 500 error

**Pass criteria:** Test calls `build_evidence_payload(str(ledger))` with no keyword args; response has no `expectations` key or has empty value; test passes; test file shows no git edits (only new test additions)

---

### TC-17 — Empty/missing ledger renders empty expectations gracefully (no 500)

**Type:** api
**Preconditions:** Backend with empty or missing evidence ledger

**Steps:**
1. Start backend with missing ledger file
2. Call `curl -s http://localhost:8000/api/evidence`
3. Check response status and structure

**Expected outcome:** Response is HTTP 200; claims array is empty or ledger is absent; expectations is empty or absent; no 500 error

**Pass criteria:** HTTP status 200; no error stack in response; expectations field is absent or empty list; app does not crash

---

### TC-18 — Cohort resolving to zero observations renders empty expectations (no 500)

**Type:** api
**Preconditions:** Backend with ledger but a claim's cohort has no matching observations

**Steps:**
1. Create test fixture with claim that has no matching observations (bad factor/decile combination)
2. Call `compute_drawdown_expectations(session, claim, cfg)` on that claim
3. Check return value

**Expected outcome:** Returns empty dict or null expectations; never raises error or returns 500-status

**Pass criteria:** Function returns gracefully (empty dict or None); test passes; no exception raised

---

### TC-19 — Null underwater_days/time_to_recover_days do not crash the UI (guarded NA render)

**Type:** browser
**Preconditions:** Frontend is running; expectations panel is visible; a measure contains null value

**Steps:**
1. Start frontend with mocked API response containing null values for underwater_days
2. Render the expectations panel
3. Verify the page does not crash
4. Inspect the rendered cell for that measure

**Expected outcome:** Panel renders without error; null values are displayed as "—" or "NA" (guarded render), not an undefined crash

**Pass criteria:** Page does not throw React error boundary; cell with null value displays a valid placeholder; browser console shows no unhandled exceptions

---

### TC-20 — New config keys are present and validated (underwater_horizons, streak_min_n)

**Type:** artifact
**Preconditions:** config.py and config.yaml are updated

**Steps:**
1. Read `apps/backend/app/config.py` line 719-749 (WalkForwardCfg class)
2. Verify `underwater_horizons: list[int]` field exists
3. Verify `streak_min_n: int` field exists
4. Read `config.yaml` walk_forward block
5. Verify both keys are set with positive values

**Expected outcome:** Both config keys are defined in WalkForwardCfg; both are present in config.yaml with positive-integer values; validation in `_validate` enforces positive values

**Pass criteria:** `underwater_horizons` and `streak_min_n` appear in WalkForwardCfg definition; config.yaml has both keys; validation test passes; negative values are rejected

---

### TC-21 — ForwardReturn model has two new nullable columns (underwater_days, time_to_recover_days)

**Type:** artifact
**Preconditions:** models.py is updated

**Steps:**
1. Read `apps/backend/app/models.py` near line 327-393 (ForwardReturn model)
2. Locate `underwater_days` field
3. Locate `time_to_recover_days` field
4. Verify both are `Optional[int]`
5. Verify both have docstrings matching max_drawdown pattern

**Expected outcome:** Both columns exist on ForwardReturn; both are typed `Optional[int]` (nullable); both have descriptive docstrings

**Pass criteria:** Column definitions appear in model; types are correct; docstrings are present and reference the no-lookahead gate

---

### TC-22 — _ADDITIVE_COLUMNS registry includes new columns (db.py)

**Type:** artifact
**Preconditions:** db.py is updated with ALTER tuples

**Steps:**
1. Read `apps/backend/app/db.py` lines 108-124
2. Locate the tuple entries for new columns
3. Verify structure matches existing max_drawdown entry (table, column, ALTER statement)
4. Verify both new columns are registered

**Expected outcome:** Two new tuples in `_ADDITIVE_COLUMNS`: one for underwater_days, one for time_to_recover_days; each tuple has (table_name, column_name, ALTER_statement)

**Pass criteria:** Both tuples present; table names are "forward_returns"; column names match model; ALTER statements use INTEGER type and nullable syntax

---

### TC-23 — Full test suite passes after adding walk_forward config keys to 9 test files

**Type:** api
**Preconditions:** All 9 test files have been updated with new walk_forward keys

**Steps:**
1. Run full backend test suite: `pytest apps/backend/tests/ -v`
2. Capture output with pass/fail counts
3. Verify all 9 affected files pass (test_forward_testing.py, test_warmup.py, test_config.py, test_indexes.py, test_sectors.py, test_themes.py, test_iter20_research_cluster.py, test_research.py, test_config_engine.py)

**Expected outcome:** All tests pass; no failures due to missing config keys

**Pass criteria:** Test exit code 0; all 9 files show passing tests; no "missing key" or "unexpected keyword" errors in output

---

### TC-24 — /evidence page latency does not regress vs J-15 budget (measured)

**Type:** browser
**Preconditions:** Backend with populated evidence ledger; frontend running; performance measurement tooling available

**Steps:**
1. Start backend and frontend services
2. Open DevTools Network tab on `/evidence`
3. Navigate to `/evidence` and wait for full page load
4. Measure time to first contentful paint (FCP) and time to interactive (TTI)
5. Record timings in reports/perf-budgets.md

**Expected outcome:** FCP ≤ J-15 budget threshold; TTI ≤ budget threshold; no regression from previous iteration

**Pass criteria:** Measured latency is within recorded budget (check reports/perf-budgets.md for baseline); fresh measurement is recorded this iteration

---

### TC-25 — Memory backfill stays under 6144 MB cap (VSZ+RSS, two runs)

**Type:** api
**Preconditions:** Fresh database with full-universe backfill required

**Steps:**
1. Delete `apps/backend/data/trendora.db` and related files (-shm, -wal)
2. Start backend with `MALLOC_ARENA_MAX=2` and `ulimit -v 6291456`
3. Monitor `/proc/<pid>/status` for VmPeak and VmRSS during backfill
4. Record peak VSZ and RSS values for first run
5. Repeat steps 1-4 for second run
6. Document both measurements in reports/perf-budgets.md

**Expected outcome:** Peak VSZ + RSS combined stays under 6144 MB for both runs; no OOM killer invocation; backfill completes successfully

**Pass criteria:** Measured VSZ+RSS < 6144 MB on both runs; backfill completes with exit code 0; measurements are recorded in reports/perf-budgets.md with timestamps

---

### TC-26 — Required-still-passing journeys still pass (live browser-qa verification)

**Type:** browser
**Preconditions:** Frontend running; all previous journeys' UIs are intact

**Steps:**
1. Open `/evidence` and verify 7 claim rows render with verdict/control/registration (J-05)
2. Verify each score has a "Proven" or "Not yet proven" badge (J-01)
3. Verify the no-stale-edge invariant on the 0-PASS ledger (J-11)
4. Verify claim rows are labeled with regime (J-04)
5. Verify score drill functionality works on one score (J-02)
6. Open `/stocks/{ticker}` and verify deep history chart renders (J-10)
7. Open `/data` and verify it renders without error (J-13)
8. Verify the "GO" preflight strip appears on all score surfaces (J-20)

**Expected outcome:** All required-still-passing journeys render without UI regressions

**Pass criteria:** All 8 journeys (J-01, J-02, J-04, J-05, J-10, J-11, J-13, J-20) pass visual inspection; no new errors; rendered content matches baseline expectations

---

## Summary

**Total test cases:** 26
- **API tests:** 15 (TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-23, TC-25)
- **Browser tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-19, TC-24, TC-26)
- **Artifact checks:** 3 (TC-20, TC-21, TC-22)

**Key validation paths:**
1. **Expectations panel rendering:** TC-01, TC-02, TC-03, TC-04 verify the UI surface
2. **Aggregation correctness:** TC-09, TC-10, TC-11, TC-12 verify compute_drawdown_expectations logic
3. **Helper correctness:** TC-05, TC-06, TC-07 verify underwater_days and time_to_recover_days
4. **No regression:** TC-08, TC-13, TC-14 verify max_drawdown reuse and existing tests pass
5. **Backend API:** TC-15, TC-16, TC-17, TC-18 verify /api/evidence endpoint
6. **Configuration:** TC-20, TC-21, TC-22, TC-23 verify model and config updates
7. **Anti-goal compliance:** TC-04 (wording), TC-13 (no-lookahead), TC-25 (memory)
