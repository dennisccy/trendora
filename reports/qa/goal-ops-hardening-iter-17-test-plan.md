# goal-ops-hardening-iter-17 Functional Test Plan

**Phase:** goal-ops-hardening-iter-17  
**Date:** 2026-07-24  
**Frontend Present:** yes

## Phase Goal

`/backtest`'s evidence section stays populated with honest, labeled last-good evidence through the single most common ingest shape (latest trading day advancing while its forward-aggregate warm is still in flight), instead of showing an empty "not yet computed" state, and the stored-row-read latency spikes during ingest windows are root-caused and any bounded mitigation is applied.

## Test Cases

### TC-01 — Older `asof_key` fallback with zero-row newer key

**Type:** api  
**Preconditions:** A `ForwardAggregateCache` fixture exists with a COMPLETE forward-aggregate version at an older `asof_key` (e.g., `2025-01-10`) and the newer `asof_key` (e.g., `2025-01-13`) has ZERO forward-aggregate rows of any version.

**Steps:**
1. Call `resolved_forward_aggregate_evidence()` with `as_of=2025-01-13`
2. Inspect the returned dict for status, as-of, and horizon data

**Expected outcome:** The function returns `evidence_status="refreshing"`, `evidence_asof="2025-01-10"`, and `evidence_by_horizon` equals the older version's stored rows for every configured horizon.

**Pass criteria:** Exact match: `status == "refreshing"`, `evidence_asof == "2025-01-10"`, `horizon_data == older_complete_rows`, never `not_yet_computed`.

---

### TC-02 — `evidence_asof` served identically by API and MCP

**Type:** api  
**Preconditions:** The same fixture as TC-01 is loaded.

**Steps:**
1. Call `GET /api/backtest` with `as_of=2025-01-13`
2. Call MCP `query_backtest` tool with the same `as_of=2025-01-13`
3. Compare the `evidence_asof` field in both responses

**Expected outcome:** Both endpoints return identical `evidence_asof: "2025-01-10"` alongside the existing `evidence_status`, `evidence_generated_at`, and `evidence_by_horizon` fields.

**Pass criteria:** Both API and MCP responses include `evidence_asof` with the identical value and type (string or null, never mismatched).

---

### TC-03 — Fresh-install shape (no complete version anywhere)

**Type:** api  
**Preconditions:** A store exists where NO `asof_key` has ever had a complete `dataset_version` (the existing `test_evidence_not_yet_computed_before_any_warm` fixture, unchanged).

**Steps:**
1. Call `resolved_forward_aggregate_evidence()`
2. Inspect the returned dict

**Expected outcome:** Returns `evidence_status="not_yet_computed"`, `evidence_asof=None`, `evidence_by_horizon={}` — identical to today's behavior.

**Pass criteria:** Exact regression guard: `status == "not_yet_computed"`, `evidence_asof is None`, `horizons == {}`.

---

### TC-04 — Multi-older-key tie-break (more recent wins)

**Type:** api  
**Preconditions:** Two older `asof_key`s each with a complete version exist (e.g., `2025-01-08` and `2025-01-10`) and the requested `asof_key` (`2025-01-13`) has zero complete rows.

**Steps:**
1. Call `resolved_forward_aggregate_evidence()` with `as_of=2025-01-13`
2. Inspect which older as-of is served

**Expected outcome:** The served `evidence_asof` is `"2025-01-10"` (the MORE RECENT of the two candidates), never `"2025-01-08"` and never a response mixing rows from both.

**Pass criteria:** `evidence_asof == "2025-01-10"` and `horizon_data` matches only that version's rows, never blended.

---

### TC-05 — No-lookahead verification (AG-5)

**Type:** api  
**Preconditions:** The fallback search is configured to cross older `asof_key`s.

**Steps:**
1. Execute the completeness query with `as_of=2025-01-13` set as the boundary
2. Use `before_cursor_execute` SQL-inspection hook (same technique as existing TC-18) to capture all executed SQL
3. Verify no row selection occurs after the boundary

**Expected outcome:** No SQL query reads or serves any row whose `asof_key` date is AFTER the requested `as_of` boundary.

**Pass criteria:** The captured SQL execution log shows zero reads past the `as_of` boundary; the `before_cursor_execute` hook confirms the WHERE clause filters correctly.

---

### TC-06 — Historical (is_latest=False) regression guard

**Type:** api  
**Preconditions:** A historical fixture (mirrors the existing `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior`) is in place.

**Steps:**
1. Call `resolved_forward_aggregate_evidence()` once with `is_latest=False`
2. Call the same function again with identical parameters

**Expected outcome:** The function computes once on the first call and returns the cached result on the second call.

**Pass criteria:** Execution trace shows exactly one compute branch entry and one cache hit on the second call; unchanged by this iteration's fallback search.

---

### TC-07 — `RefreshingEvidenceBanner` displays `evidence_asof`

**Type:** browser  
**Preconditions:** The `/backtest` page is loaded with a response where `evidence_status="refreshing"` and `evidence_asof` is earlier than the page's own resolved `asof_date` (e.g., `evidence_asof="2025-01-10"` but `asof_date="2025-01-13"`).

**Steps:**
1. Use Chrome MCP to navigate to the `/backtest` page
2. Locate the `RefreshingEvidenceBanner` component
3. Inspect the displayed text and capture a screenshot

**Expected outcome:** The banner visibly displays the `evidence_asof` date text (e.g., "Evidence as of 2025-01-10") alongside the existing generation timestamp, not only the timestamp.

**Pass criteria:** Text explicitly mentions the as-of date; screenshot saved to `reports/qa/goal-ops-hardening-iter-17-evidence/TC-07-refreshing-banner-with-asof.png`.

---

### TC-08 — As-of-advancing `refreshing` case with small backfill (agent/QA-performed)

**Type:** browser  
**Preconditions:** The currently-running backend (`:8255`) and frontend (`:3255`) are active; no service restart is performed.

**Steps:**
1. Through the existing `/data` job form, submit a small single-day backfill for a date that ADVANCES the latest stored run (not a historical gap date)
2. Wait for the job to reach the "warm running" state (forward-aggregate incomplete)
3. While the warm is still in flight, load `/backtest` in the browser
4. Measure response time and inspect the rendered page
5. Capture a screenshot of the evidence section

**Expected outcome:** The page renders within the committed ≤1.5s served-from-storage budget, showing `refreshing` labeled with the PRIOR `asof_key`'s date (e.g., "Refreshing from 2025-01-10"), never `not_yet_computed`, and the page is responsive (not frozen).

**Pass criteria:** Latency ≤1.5s; screenshot shows `RefreshingEvidenceBanner` with the older as-of date and populated evidence rows; HTTP 200 response.

---

### TC-09 — `not_yet_computed` state on disposable DB (OPERATOR-performed)

**Type:** browser  
**Preconditions:** **This step is OPERATOR-performed.** An alternate backend instance is launched via `scripts/start-backend.sh` under a `TRENDORA_CONFIG` override pointed at a disposable copy of `trendora.db` (schema created, zero ingest ever run) on an unused port. The working `trendora.db`'s row counts are recorded before boot.

**Steps:**
1. Boot the throwaway backend instance on the alternate port
2. Verify the frontend (or a direct HTTP client) can reach it
3. Load `/backtest` against that instance
4. Capture a screenshot of the rendered page
5. Stop the throwaway instance (OPERATOR performs stop)
6. Verify the working `trendora.db`'s row counts are unchanged

**Expected outcome:** The page renders the `not_yet_computed` `EmptyState` within budget (≤1.5s), and the working database is never opened by the throwaway instance.

**Pass criteria:** Screenshot saved to `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png`; HTTP 200 response with `evidence_status="not_yet_computed"`; working DB row counts identical before and after.

**Fallback (if impractical this session):** A backend-only JSON capture showing `evidence_status="not_yet_computed"` (HTTP 200) plus confirmation that the frontend's `EmptyState` call site is unconditionally reached for that status — documented in the QA report.

---

### TC-10 — Deep-basis latency re-measurement (OPERATOR-performed, AG-10-class)

**Type:** api  
**Preconditions:** **This step is OPERATOR-performed.** The same AG-10-class ingest-window concurrent-poll protocol iter-16's TC-16 used is executed: cooled host, sampler live, watchdog armed, `taskset -c 0-3,8-11`, BLAS/OMP=4.

**Steps:**
1. Prepare the environment per iter-16's protocol (host cooling, sampler, watchdog, CPU affinity)
2. Execute 68 concurrent polls to `/backtest` across a single-day backfill ingest window
3. Record response times and categorize breaches (>1.5s)
4. Calculate max latency and breach count
5. Write findings to a new dated section of `reports/perf-budgets.md`

**Expected outcome:** A measurement directly comparable to iter-16's baseline (11/68 breaches, max 12.655s). The root-cause investigation documents the finding (contention cost, write-pattern mitigation, or other), and any applied bounded mitigation is recorded.

**Pass criteria:** `reports/perf-budgets.md` contains a dated section (e.g., "2026-07-24 — Iter 17") with breach count, max latency, and root-cause summary; measurement methodology matches iter-16 exactly.

---

### TC-11 — Non-disruptive J-04 sanity check

**Type:** api  
**Preconditions:** The backend is already running; no kill/restart is performed.

**Steps:**
1. Poll `GET /api/health` once
2. Inspect the response for `readiness` field
3. Check `logs/backend.log` for any new crash or restart banner since the last recorded one

**Expected outcome:** HTTP 200 response with `readiness: "ready"`, and no new crash/restart banner appears in the log.

**Pass criteria:** HTTP 200; `readiness` field equals `"ready"`; no new error/crash lines in the log tail.

---

## Summary

**Total test cases:** 11  
**API tests:** 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-11)  
**Browser tests:** 4 (TC-07, TC-08, TC-09, TC-10)  
**Artifact checks:** 1 (TC-10 perf-budgets.md update)

**Test execution split:**
- **Agent/QA-performable (no service start/stop):** TC-01–07, TC-08, TC-11 — run against already-running services (`:8255`/`:3255`)
- **OPERATOR-performed (service start or AG-10-class heavy pass):** TC-09 (throwaway backend boot), TC-10 (deep-basis re-measurement with host guards)

**Coverage of phase requirements:**
- Cross-`asof_key` fallback correctness and no-lookahead: TC-01, TC-04, TC-05
- Fresh-install guard and regression guards: TC-03, TC-06
- API/MCP consistency: TC-02
- Frontend banner label display: TC-07
- Live evidence captures: TC-08 (advancing as-of), TC-09 (not-yet-computed)
- Latency root-cause and re-measurement: TC-10
- J-04 carry-forward check: TC-11
