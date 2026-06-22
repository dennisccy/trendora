# Goal Iteration 47 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Frontend Present:** yes

## Phase Goal

Refactor the Research labs' heavy data-read path to stream column-projected `forward_returns` rows instead of materializing the entire table as ORM objects, restoring J-25/J-26/J-29 (heavy lab renders) and J-104 (lab reliability) to passing on the full 3.3 GB live dataset without MemoryError, with every served figure byte-identical.

## Test Cases

### TC-01 — Event-Study Lab renders REAL per-horizon figures on full live dataset

**Type:** browser
**Preconditions:** Backend is freshly restarted, warmed (one full `/api/health` ready cycle), and no concurrent heavy requests are in flight. Frontend is running at http://localhost:3000.

**Steps:**
1. Navigate to http://localhost:3000/research/event-study
2. Wait for the page to finish loading (loading skeleton disappears, event-study matrix renders with visible cells)
3. Verify the event-study matrix displays per-horizon rows (1d, 5d, 10d, 20d, 60d) with per-column mean-return, win-rate, and N values populated as real numbers (not "Loading…" or "Backend unavailable" or skeleton frames)
4. Click a `N=` chip (e.g., N=142 on the 5d mean-return cell) to drill into `/research/samples`
5. Verify the samples page loads with count-coherent rows matching the reported N

**Expected outcome:** Event-study matrix renders REAL figures per horizon. `N=` drill-down navigates to a count-coherent `/research/samples` page.
**Pass criteria:** HTTP 200 response on `/research/event-study`; matrix cells display real numeric values (not skeletons or error states); `N=` drill-down count matches the reported N on the event-study matrix.

---

### TC-02 — Factor Lab decile rankings and rank-IC per factor render REAL figures

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Navigate to http://localhost:3000/research (Factor Lab)
2. Wait for the page to finish loading
3. Verify the decile-table renders with real numeric rank-IC values per factor (not "Loading…", "Backend unavailable", or skeletons)
4. Verify each factor shows a sort-order column with real per-decile IC values
5. Click a `N=` chip (e.g., on the top-decile cohort) to drill into `/research/samples`
6. Verify the samples page loads with count-coherent rows

**Expected outcome:** Factor Lab decile table renders REAL rank-IC figures per factor and per decile. `N=` drill-down is count-coherent.
**Pass criteria:** HTTP 200 on `/research`; decile table displays real numeric rank-IC and decile values; `N=` drill-down returns count-coherent samples matching the reported N.

---

### TC-03 — Factor Lab multi-factor composite cohort renders REAL figures

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Navigate to http://localhost:3000/research (Factor Lab page)
2. Wait for loading to complete
3. Scroll to or locate the multi-factor composite section
4. Verify the composite cohort displays real mean-return and win-rate values (not "Loading…", "Backend unavailable", or skeletons)
5. Note the reported N for the composite cohort

**Expected outcome:** Multi-factor composite cohort section renders REAL mean-return, win-rate, and N values.
**Pass criteria:** HTTP 200 on `/research`; composite section displays real numeric values; no "Backend unavailable" error state.

---

### TC-04 — Regime×Setup×Pattern lab loads on full live dataset (required-still-passing smoke test)

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Navigate to http://localhost:3000/research/regime-setup-pattern
2. Wait for page loading
3. Verify the regime×setup×pattern matrix renders with real cell values

**Expected outcome:** Page serves HTTP 200; matrix displays REAL figures per regime/setup/pattern combination.
**Pass criteria:** HTTP 200 on `/research/regime-setup-pattern`; matrix cells are populated with real numeric values.

---

### TC-05 — Downtrend-Opportunity lab loads on full live dataset (required-still-passing smoke test)

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Navigate to http://localhost:3000/research/downtrend-opportunity
2. Wait for page loading
3. Verify the page renders with real downtrend opportunity figures

**Expected outcome:** Page serves HTTP 200; renders real recovery-turn opportunity analysis figures.
**Pass criteria:** HTTP 200 on `/research/downtrend-opportunity`; no "Backend unavailable" error; figures are populated and real.

---

### TC-06 — Recovery-Turn-Edge lab loads (J-90, required-still-passing smoke test)

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Navigate to http://localhost:3000/research/recovery-turn-edge
2. Wait for page loading
3. Verify the page renders with real figures

**Expected outcome:** Page serves HTTP 200; renders recovery-turn-edge analysis figures.
**Pass criteria:** HTTP 200 on `/research/recovery-turn-edge`; figures are real and populated.

---

### TC-07 — As-of date toggle switches between all-history and specific date views (J-32)

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running at the dashboard.

**Steps:**
1. Navigate to http://localhost:3000 (dashboard)
2. Verify the as-of date panel shows the current/latest as-of date
3. Click the as-of date to switch to a historical date (e.g., 30 days prior)
4. Verify the dashboard and all figures update to reflect the historical as-of date
5. Toggle back to "All history" (latest)
6. Verify figures revert to current data

**Expected outcome:** As-of date switcher correctly navigates between historical and latest views with coherent figure updates.
**Pass criteria:** Dashboard and all visible figures update when the as-of date changes; toggle between historical and latest completes without errors.

---

### TC-08 — N= sample counts are coherent across drill-downs (J-51, J-65, J-63)

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Navigate to any research lab page that shows `N=` chips and sample drill-downs (event-study, factor-lab)
2. Note the reported N value on a cell (e.g., "N=142")
3. Click the `N=` chip to navigate to `/research/samples`
4. Verify the samples page loads and shows exactly 142 rows (or the reported count)
5. Repeat for 2–3 different cohorts across different labs

**Expected outcome:** Sample count on the lab page matches the row count on the `/research/samples` drill-down.
**Pass criteria:** For each drill-down tested, the `N=` value on the lab page equals the number of rows displayed on the `/research/samples` page.

---

### TC-09 — Single-source NVDA detail score matches leaderboard (J-06, critical invariant)

**Type:** browser
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running. NVDA is in the dataset.

**Steps:**
1. Navigate to http://localhost:3000/research (leaderboard)
2. Locate NVDA in the leaderboard and note its Leadership, Entry Quality, and Risk scores
3. Click on NVDA to open its detail page
4. Verify the detail page shows IDENTICAL Leadership, Entry Quality, and Risk scores

**Expected outcome:** NVDA scores on the detail page match exactly the scores shown on the leaderboard.
**Pass criteria:** Leadership score, Entry Quality score, and Risk score are byte-identical between the leaderboard and detail page.

---

### TC-10 — No native HTML date inputs present (J-18, critical invariant)

**Type:** browser
**Preconditions:** Frontend is running.

**Steps:**
1. Navigate to http://localhost:3000/research
2. Open the browser DevTools console
3. Run the command: `document.querySelectorAll('input[type=date]').length`
4. Verify the result is 0

**Expected outcome:** No `input[type=date]` HTML elements are present on the page.
**Pass criteria:** Query returns 0.

---

### TC-11 — Risk-Off regime marks zero stocks Actionable (J-07, critical invariant)

**Type:** api
**Preconditions:** Backend is running. Database seed contains a Risk-Off regime snapshot. Get the as-of date for a Risk-Off snapshot via inspection or config.

**Steps:**
1. Run: `curl -s http://localhost:8000/api/stocks?as_of=<RISK_OFF_DATE> | jq '.leaderboard[] | select(.setup_status == "Actionable") | length'`
2. Verify the response count is 0

**Expected outcome:** When the regime is Risk-Off, no stocks have a setup_status of "Actionable".
**Pass criteria:** The query returns an empty array or count of 0 for Actionable stocks on a Risk-Off date.

---

### TC-12 — Backend serves /api/health with "ready" status after warm-up

**Type:** api
**Preconditions:** Backend is freshly restarted.

**Steps:**
1. Wait up to 2 minutes for the backend to complete warm-up
2. Run: `curl -s http://localhost:8000/api/health`
3. Verify the response is HTTP 200 and contains `"status": "ready"`

**Expected outcome:** `/api/health` returns ready status after the background warm-up completes.
**Pass criteria:** HTTP 200 response with `status` field = "ready".

---

### TC-13 — Event-study endpoint returns byte-identical figures across as_of=None and historical as_of (deep-equality unit test contract)

**Type:** artifact
**Preconditions:** Backend is running against the committed seed dataset.

**Steps:**
1. Unit test `test_research.py::test_event_study_members_by_horizon_deep_equality_all_history` or equivalent runs without error
2. Unit test `test_research.py::test_event_study_members_by_horizon_deep_equality_historical_as_of` or equivalent runs without error
3. Both tests assert the streamed/bounded builder output is byte-identical to the prior reference across `as_of=None` (all-history) and a historical `as_of` date (≤ D scoping)
4. Tests also verify ordering is preserved (member dicts sorted by `ScannerResult.id` ascending)

**Expected outcome:** Deep-equality assertions pass; byte-identity is proven.
**Pass criteria:** Both test cases pass with zero failures; byte-identity assertion succeeds for both as_of=None and historical as_of.

---

### TC-14 — Backfill forward returns builds identical idempotency set and inserts zero duplicates after streaming refactor

**Type:** artifact
**Preconditions:** Backend is running. Seed database is loaded.

**Steps:**
1. Unit test `test_forward_testing.py::test_backfill_forward_returns_idempotency_set_unchanged` or equivalent runs
2. Test asserts that `_backfill_all_runs` / `backfill_forward_returns` builds the SAME `(run_id, symbol, horizon)` idempotency set as the prior implementation after the streaming refactor
3. Test verifies INSERT-only contract: zero duplicate rows are inserted

**Expected outcome:** Idempotency set is unchanged; no duplicate rows are inserted.
**Pass criteria:** Test passes with zero assertion failures; idempotency set comparison passes; duplicate row count is 0.

---

### TC-15 — research.read_batch_size config key is validated >= 1 at boot

**Type:** artifact
**Preconditions:** Backend config.py is loaded.

**Steps:**
1. Unit test `test_config.py::test_research_cfg_read_batch_size_validated` or equivalent runs
2. Test verifies that `ResearchCfg` includes a `read_batch_size: int` field with a `model_validator(mode="after")` that raises `ValueError` if the value is < 1
3. Test sets `read_batch_size = 0` and asserts the validator raises

**Expected outcome:** Boot-time validation enforces `read_batch_size >= 1`.
**Pass criteria:** Validator raises `ValueError` when `read_batch_size < 1`; validation passes when `read_batch_size >= 1`.

---

### TC-16 — research.read_batch_size is config-sourced, no inline magic number in calculation code

**Type:** artifact
**Preconditions:** Code changes are in place. `test_no_magic_numbers` guard is run.

**Steps:**
1. Run: `pytest apps/backend/tests/test_config.py::test_no_magic_numbers -v`
2. Verify the test passes (no inline batch-size literals found in CALC_FILES)

**Expected outcome:** No inline `yield_per(N)` literals are present in calculation code; the batch size is always read from config.
**Pass criteria:** `test_no_magic_numbers` passes; grep for inline numeric yield_per batch sizes in research.py returns no results.

---

### TC-17 — No new table is created (test_db.py expected-tables assertion unchanged)

**Type:** artifact
**Preconditions:** Backend code changes are complete.

**Steps:**
1. Run: `pytest apps/backend/tests/test_db.py::test_create_all_produces_expected_tables -v`
2. Verify the test passes (expected table count is unchanged; no new `table=True` models added)

**Expected outcome:** The expected-tables assertion passes; no new table is registered.
**Pass criteria:** Test passes with zero assertion failures; table count matches the prior expected count.

---

### TC-18 — All inline test config fixtures include research.read_batch_size

**Type:** artifact
**Preconditions:** Code search has been completed across `apps/backend/tests/`.

**Steps:**
1. Run: `grep -r "ResearchCfg\|research:" apps/backend/tests/*.py | grep -v ".pyc"`
2. For each file that references `ResearchCfg` or has a `research:` block in an inline config dict, verify the `read_batch_size` key is present
3. Files to check: `test_research.py`, `test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py`

**Expected outcome:** Every inline `ResearchCfg` or `research:` config dict includes `read_batch_size: <int>`.
**Pass criteria:** All identified test files include `read_batch_size` in their config fixtures; no fixture is missing the key.

---

### TC-19 — Full backend test suite passes with zero failures

**Type:** artifact
**Preconditions:** All code changes are complete. Backend is running or can be tested offline.

**Steps:**
1. Run the full backend test suite (nohup-async via the pump, or via `pytest apps/backend/tests/ -v`)
2. Capture the final exit code and result summary
3. Verify: exit code = 0, failed count = 0

**Expected outcome:** Full backend suite reaches `0 failed, EXIT 0`.
**Pass criteria:** Test exit code is 0; no test failures are reported; coherence audit passes (if enabled).

---

### TC-20 — All five Research labs return HTTP 200 on the full live dataset

**Type:** api
**Preconditions:** Backend is freshly restarted and warmed. Frontend is running.

**Steps:**
1. Request: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/research/event-study`
2. Request: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/research/factor-combination`
3. Request: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/research/regime-setup-pattern`
4. Request: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/research/downtrend-opportunity`
5. Request: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/research/recovery-turn-edge`
6. Verify all responses return 200 (no 500, 503, or timeout)

**Expected outcome:** All five heavy research labs serve HTTP 200 on the full live 3.3 GB dataset without MemoryError or timeout.
**Pass criteria:** All five requests return HTTP 200.

---

## Summary

Total test cases: 20
- Browser tests: 11 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11)
- API tests: 2 (TC-12, TC-20)
- Artifact/unit tests: 7 (TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19)

**Key test focus:** J-105 regression fix validation — heavy labs must serve HTTP 200 on the full 3.3 GB live dataset with byte-identical figures, without MemoryError or "Backend unavailable" errors. Required-still-passing smoke tests ensure J-29/J-25/J-26 (lab renders), J-104 (reliability), J-77/J-91/J-90/J-63/J-51/J-65/J-72 (coherence), and critical invariants J-06/J-18/J-07 remain intact.
