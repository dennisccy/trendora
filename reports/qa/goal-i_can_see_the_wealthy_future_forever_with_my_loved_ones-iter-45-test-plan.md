# Iteration 45 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45  
**Date:** 2026-06-22  
**Frontend Present:** yes

## Phase Goal

Deliver the last two buildable Must-haves: (J-103) a new Severity-velocity × Regime forward-return study at `/research/severity-velocity` with a regime × velocity-sign matrix, horizon selector, and an honest verdict; and (J-104) a research-labs reliability pass that caches two remaining studies, bounds the downtrend scan, and splits the monolithic `/research` page into lazy-loaded sub-routes behind a hub.

## Test Cases

### TC-01 — J-103 Severity-Velocity Study Matrix Renders

**Type:** browser  
**Preconditions:** Frontend running at localhost:3000; backend at localhost:8000 with committed 2021-2026 seed loaded; no filter applied on initial load.

**Steps:**
1. Navigate to `/research/severity-velocity`
2. Wait for the matrix to load (no "Checking backend…" skeleton if data is early/empty; if honest-empty, verify NA card rendered)
3. Verify the regime-family × velocity-sign matrix renders with cells containing mean forward return, win-rate, and N values for each horizon (5/10/20/60 days)
4. Verify the horizon selector is present and can be changed

**Expected outcome:** The matrix displays with at least one non-NA cell; the verdict text is visible below the matrix.

**Pass criteria:** The regime × velocity-sign matrix renders with numeric mean forward return, win-rate, and N values per horizon; at least one cell is populated and clickable (N chip resolvable by `aria-label`).

---

### TC-02 — J-103 Verdict Text Contains Honest Caveats

**Type:** browser  
**Preconditions:** Frontend running; `/research/severity-velocity` loaded with a populated matrix.

**Steps:**
1. Scroll down to view the verdict text below the matrix
2. Verify the verdict includes the phrase "rising stress-velocity under a red regime preceded a bounce, not continuation"
3. Verify the verdict includes the terms "survivorship", "bull-dominated", and "underpowered-for-crashes"

**Expected outcome:** The verdict text states that the hypothesis is NOT supported and includes all three caveats verbatim.

**Pass criteria:** All three caveats ("survivorship", "bull-dominated", "underpowered-for-crashes") appear in the rendered verdict text.

---

### TC-03 — J-103 N= Chip Opens Cohort in New Tab

**Type:** browser  
**Preconditions:** Frontend running; `/research/severity-velocity` loaded with populated matrix; at least one N chip present with non-zero value.

**Steps:**
1. Identify an N chip (e.g., "N=45") by resolving its `aria-label` attribute, not visible text
2. Click the N chip
3. Verify a new browser tab opens to `/research/samples` with appropriate query params (cohort type and as-of filter)
4. In the new tab, verify the total count matches the published N value from the matrix cell

**Expected outcome:** A new tab opens with the reproducing cohort; the total sample count equals the published N.

**Pass criteria:** New tab contains samples endpoint; the count displayed matches the N value from the clicked chip.

---

### TC-04 — J-103 Episodes/Pooled Mode Toggle Works

**Type:** browser  
**Preconditions:** Frontend running; `/research/severity-velocity` loaded.

**Steps:**
1. Locate the Episodes/Pooled toggle
2. Toggle between Episodes and Pooled modes
3. Verify the matrix updates to show the appropriate aggregation level

**Expected outcome:** The matrix visibly updates when toggling modes; the data remains consistent with the selected mode.

**Pass criteria:** Toggling Episodes/Pooled changes the displayed values; no errors or 4xx responses.

---

### TC-05 — J-103 As-of/All-History Mode Toggle Works

**Type:** browser  
**Preconditions:** Frontend running; `/research/severity-velocity` loaded.

**Steps:**
1. Locate the As-of/All-history toggle
2. Toggle between As-of and All-history modes
3. Verify the matrix updates and the as-of date is reflected in the URL if applicable

**Expected outcome:** The matrix updates when toggling; no new date state is created (as-of is a mode, not a separate date).

**Pass criteria:** Toggling As-of/All-history changes the displayed values; the URL reflects the global as-of date, not a second date state.

---

### TC-06 — J-103 Invalid Horizon Parameter Returns 422

**Type:** api  
**Preconditions:** Backend running at localhost:8000.

**Steps:**
1. Send `curl -s "http://localhost:8000/api/research/severity-velocity?horizon=999&view=episodes&as_of=2025-12-31" -H "Accept: application/json"`
2. Capture the response status code and body

**Expected outcome:** Status code 422 (Unprocessable Entity) with an error message describing the invalid horizon.

**Pass criteria:** Response status is 422; error body contains a validation error message.

---

### TC-07 — J-103 Empty Cohort Renders Honest NA State

**Type:** browser  
**Preconditions:** Frontend running; backend configured to produce an empty cohort (e.g., a velocity/regime combination with insufficient samples).

**Steps:**
1. Navigate to `/research/severity-velocity`
2. Locate a cell with N=0 or insufficient samples
3. Verify the cell is rendered as an NA card, not a fabricated row

**Expected outcome:** The NA cell is visibly marked as NA or empty; no fabricated data is displayed.

**Pass criteria:** Zero-N cells render as honest NA, not with fabricated numbers.

---

### TC-08 — J-104 Research Hub Navigation

**Type:** browser  
**Preconditions:** Frontend running at localhost:3000.

**Steps:**
1. Navigate to `/research`
2. Verify the page displays as a hub with links to each lab: factor-combination, event-study, regime-setup-pattern, downtrend-opportunity, and severity-velocity
3. Verify each link is reachable (no 404)

**Expected outcome:** The `/research` hub displays all five lab links; all links resolve to their respective sub-routes.

**Pass criteria:** `/research` hub is navigable; all five lab sub-routes are listed and clickable.

---

### TC-09 — J-104 Single Lab Fetch (No Concurrent Loads)

**Type:** browser  
**Preconditions:** Frontend running; browser DevTools Network tab or traffic monitoring enabled.

**Steps:**
1. Navigate to `/research` hub
2. Click on one lab link (e.g., event-study)
3. Monitor network traffic while the page loads
4. Verify only ONE heavy fetch request fires for the selected lab
5. Verify the other labs' heavy endpoints are NOT called on this route

**Expected outcome:** Only the selected lab's data is fetched; other labs remain unloaded.

**Pass criteria:** Exactly one heavy research endpoint is called per route; no concurrent probes to all four labs.

---

### TC-10 — J-104 Relocated Lab Figures Byte-Identical

**Type:** api  
**Preconditions:** Backend running; pre-split and post-split lab endpoints both available (for comparison).

**Steps:**
1. Send `curl -s "http://localhost:8000/api/research/factor-combination?view=episodes&as_of=2025-12-31"`
2. Capture the full JSON response body
3. Compare with a previous baseline (or verify the structure contains the same fields and numeric values)

**Expected outcome:** The factor-combination endpoint returns the same figures after relocation as before.

**Pass criteria:** Response JSON is byte-identical to a previous capture (or manually verified to contain the same data structure and values).

---

### TC-11 — J-104 Samples Drill-Down Count Coherence

**Type:** browser  
**Preconditions:** Frontend running; `/research/factor-combination` or `/research/event-study` or another relocated lab loaded.

**Steps:**
1. Locate an N chip in the relocated lab
2. Click it to open `/research/samples` in a new tab
3. Verify the total count displayed matches the N value from the lab matrix cell
4. Verify this holds in both Episodes+Pooled and All-history+As-of modes

**Expected outcome:** Sample totals match the N values shown in the lab matrices across both modes.

**Pass criteria:** Every N chip's drill-down total == published cell N in Episodes+Pooled AND All-history+As-of.

---

### TC-12 — J-103 Study Cache Byte-Identity (Fresh vs Hit)

**Type:** api  
**Preconditions:** Backend running; cache table `event_study_cache` populated from a previous request.

**Steps:**
1. Query `/api/research/severity-velocity?view=episodes&horizon=5&as_of=2025-12-31` and capture the response (cache hit)
2. Verify the response structure contains regime-family × velocity-sign cells with mean forward return, win-rate, N
3. Compare this response to a fresh compute (or verify consistency on a second request)

**Expected outcome:** Cached and fresh-compute responses are byte-identical.

**Pass criteria:** Cache hit returns exact same JSON bytes as a direct compute; figures do not vary between requests.

---

### TC-13 — J-103 No Lookahead in Forward Returns

**Type:** api  
**Preconditions:** Backend running; a specific as-of date selected (e.g., 2025-06-15).

**Steps:**
1. Query `/api/research/severity-velocity?view=episodes&horizon=5&as_of=2025-06-15`
2. Inspect the returned matrix cells for forward returns
3. Verify that forward returns use only bars dated AFTER 2025-06-15 (no lookahead)

**Expected outcome:** Forward return calculations strictly use future bars (> as_of), not past bars.

**Pass criteria:** Forward return samples are computed from bars with dates strictly > the as_of date (no-lookahead tail-invariance verified).

---

### TC-14 — J-101/J-102 Dashboard Cross-View Unchanged

**Type:** browser  
**Preconditions:** Frontend running; dashboard loaded with multiple chart views.

**Steps:**
1. Navigate to the dashboard (`/`)
2. Verify the cross-view chart syncing still works (scrolling one chart updates others)
3. Verify the severity-velocity line and tooltip on the dashboard are unchanged from the previous iteration

**Expected outcome:** Dashboard charts sync correctly; severity-velocity metric is unchanged.

**Pass criteria:** Cross-view synchronization functions; severity-velocity data/visualization unchanged.

---

### TC-15 — J-18 Zero Native Date Inputs (Critical)

**Type:** browser  
**Preconditions:** Frontend running; all pages navigable.

**Steps:**
1. Navigate through the entire application (dashboard, research hub, all research labs, samples)
2. Use browser DevTools Inspector to search for `input[type=date]` elements
3. Verify no native date input elements exist anywhere in the DOM

**Expected outcome:** Zero instances of `<input type="date">` in the DOM across all pages.

**Pass criteria:** No `input[type=date]` elements found; all date selectors use custom UI controls.

---

### TC-16 — J-07 Risk-Off Actionable Gate (Critical)

**Type:** browser  
**Preconditions:** Frontend running; dashboard loaded; a red/Risk-Off regime is active.

**Steps:**
1. Navigate to the dashboard and verify if a Risk-Off regime is shown
2. Navigate to any actionable/alert section
3. Verify that when Risk-Off is active, the Actionable count is 0 (if the gate is engaged)

**Expected outcome:** Under Risk-Off regime, no actionable signals appear.

**Pass criteria:** Actionable count is 0 when Risk-Off regime is active; the gate functions correctly.

---

### TC-17 — J-65/J-51 Count Coherence on Relocated Lab

**Type:** browser  
**Preconditions:** Frontend running; a relocated lab (e.g., regime-setup-pattern) loaded.

**Steps:**
1. Locate an N chip with a known value (e.g., "N=128")
2. Click it to open `/research/samples` in a new tab
3. Verify the sample count displayed equals the N value
4. Toggle between Episodes+Pooled and All-history+As-of modes
5. Verify the count remains coherent across mode changes

**Expected outcome:** Sample totals match N values across all mode combinations.

**Pass criteria:** Every cell's N value is reproduced accurately in `/research/samples` across Episodes+Pooled AND All-history+As-of modes.

---

### TC-18 — J-103 Samples Cohort Kind No 4xx

**Type:** api  
**Preconditions:** Backend running; a severity-velocity cohort is selected.

**Steps:**
1. Query `/api/research/samples?cohort_kind=severity_velocity&view=episodes&as_of=2025-12-31` (or the actual parameter name used)
2. Verify the response status is 200
3. Verify the response contains a list of samples with consistent structure

**Expected outcome:** A 200 response with valid sample data; no 4xx errors.

**Pass criteria:** Status 200; response contains well-formed sample records; no errors for any displayable cell.

---

### TC-19 — J-104(a) Factor-Combination Cache Byte-Identity

**Type:** api  
**Preconditions:** Backend running; cache populated from previous request.

**Steps:**
1. Query `/api/research/factor-combination?view=episodes&as_of=2025-12-31` (cache hit)
2. Capture the response
3. Verify the response structure and figures match a previous baseline or fresh compute

**Expected outcome:** Cached factor-combination endpoint returns figures byte-identical to a direct compute.

**Pass criteria:** Cache hit response is byte-identical to baseline; refresh on dataset change verified.

---

### TC-20 — J-104(a) Regime-Setup-Pattern Cache Byte-Identity

**Type:** api  
**Preconditions:** Backend running; cache populated.

**Steps:**
1. Query `/api/research/regime-setup-pattern?view=episodes&as_of=2025-12-31` (cache hit)
2. Capture the response
3. Compare to a previous baseline or fresh compute

**Expected outcome:** Cached regime-setup-pattern endpoint returns figures byte-identical to a direct compute.

**Pass criteria:** Cache hit response is byte-identical to baseline; refresh on dataset change verified.

---

### TC-21 — J-104(b) Downtrend Scan As-of Bounded

**Type:** api  
**Preconditions:** Backend running; a specific as-of date applied (e.g., 2025-06-30).

**Steps:**
1. Query `/api/research/downtrend-opportunity?view=episodes&as_of=2025-06-30`
2. Verify the response includes only scanner runs with `asof_date <= 2025-06-30`
3. Verify the query completes in reasonable time (no full-table scan overhead)

**Expected outcome:** Downtrend results are bounded by as-of; no runs from after the as-of date are included.

**Pass criteria:** All runs in the result have `asof_date <= as_of`; query performance is consistent (no runaway scan).

---

### TC-22 — Test No Magic Numbers

**Type:** artifact  
**Preconditions:** Backend codebase available; test suite runnable.

**Steps:**
1. Run `pytest apps/backend/tests/test_engine.py::test_no_magic_numbers -v`
2. Capture the output

**Expected outcome:** The test passes with no magic literals found in engine CALC_FILES.

**Pass criteria:** `test_no_magic_numbers` passes; EXIT 0.

---

### TC-23 — Test DB Expected Tables

**Type:** artifact  
**Preconditions:** Backend codebase available; test suite runnable.

**Steps:**
1. Run `pytest apps/backend/tests/test_db.py::test_create_all_produces_expected_tables -v`
2. Capture the output

**Expected outcome:** The test passes; no unexpected new tables are created.

**Pass criteria:** `test_create_all_produces_expected_tables` passes; EXIT 0; any new table is registered in `RESEARCH_CACHE_TABLES`.

---

### TC-24 — Research Endpoint Byte-Equality Guards Updated

**Type:** artifact  
**Preconditions:** Backend test files scanned for `set(payload) ==` or `served == ...` guards.

**Steps:**
1. Search `apps/backend/tests/` for byte-equality guards: `grep -r "set(payload) ==" apps/backend/tests/`
2. Identify all guards touching research endpoints (factor-combination, event-study, regime-setup-pattern, downtrend-opportunity)
3. Verify each guard has been updated to match the latest payload shape (if the endpoint was touched)

**Expected outcome:** All byte-equality guards on touched research endpoints are updated and passing.

**Pass criteria:** No stale byte-equality guards remain; all guards pass when tests run.

---

### TC-25 — Backend Unit/Integration Tests Pass

**Type:** artifact  
**Preconditions:** Backend code complete; test suite runnable; pytest installed.

**Steps:**
1. Run `pytest apps/backend/tests/test_research*.py apps/backend/tests/test_samples*.py -v`
2. Capture exit code and output

**Expected outcome:** All tests pass; 0 failures.

**Pass criteria:** Full pytest suite for research and samples modules exits with code 0; no failures.

---

### TC-26 — Full Backend Pytest Suite Passes

**Type:** artifact  
**Preconditions:** All backend changes complete; full test suite runnable.

**Steps:**
1. Run `pytest apps/backend/tests/ -v 2>&1 | tee test-output.log`
2. Capture the final line: `X passed, Y failed, Z skipped`

**Expected outcome:** The suite flushes `0 failed, EXIT 0`.

**Pass criteria:** Full pytest suite reports `0 failed` with exit code 0.

---

## Summary

Total test cases: 26  
API tests: 10 (TC-06, TC-10, TC-12, TC-13, TC-18, TC-19, TC-20, TC-21, TC-22, TC-23)  
Browser tests: 12 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-08, TC-09, TC-14, TC-15, TC-16, TC-17)  
Artifact checks: 4 (TC-24, TC-25, TC-26, TC-11 hybrid)

**Key coverage:**
- J-103 severity-velocity study: matrix rendering, verdict + caveats, N chip drill-downs, mode toggles, error handling, cache byte-identity, no lookahead
- J-104 research hub: navigation, single fetch per route, byte-identical figures after relocation, count coherence across modes
- Required-still-passing: dashboard sync, zero native date inputs (J-18 critical), Risk-Off gate (J-07 critical)
- Backend guardrails: no magic numbers, expected tables, byte-equality guards updated, full suite green
