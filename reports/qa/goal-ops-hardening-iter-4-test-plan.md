# goal-ops-hardening-iter-4 Functional Test Plan

**Phase:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Frontend Present:** yes

## Phase Goal

Fix two pre-existing trust-surface defects exposed by driving J-05 (aggregates precomputed at ingest) through the browser: B3 — an ordinary fetch that lands a bar past the last persisted snapshot no longer flips the app-wide readiness badge to the crash-identical "Backend unavailable" state; F1 — a heavy ingest job's live progress heartbeat stays honest through its aggregate-refresh finalize phase instead of freezing and showing a false "possibly stalled" message.

## Test Cases

### TC-01 — Baseline: ready/initializing state unchanged when servable run exists

**Type:** api
**Preconditions:** A `ScannerRun` is persisted for the benchmark symbol's (SPY) latest bar date (e.g., 2026-07-18); no data beyond that date exists; database is in a warm, initialized state.

**Steps:**
1. Call `GET /api/health` endpoint to retrieve the current readiness state.
2. Verify the response contains the `readiness` object with `state` and optional `detail` fields.

**Expected outcome:** The `readiness.state` is `"ready"` or `"initializing"` (same as behavior before this iteration); `readiness.detail` is `null`.
**Pass criteria:** `curl -s http://localhost:5000/api/health | jq '.readiness.state'` returns `"ready"` or `"initializing"` AND `jq '.readiness.detail'` is `null`.

---

### TC-02 — Non-benchmark symbol fetch does NOT affect global readiness

**Type:** api
**Preconditions:** A `ScannerRun` is persisted for date D (e.g., 2026-07-18); the benchmark symbol (SPY) has no bar dated after D; a non-benchmark symbol (e.g., AAPL) has one or more bars dated D+1 (2026-07-19) — simulating an ordinary fetch that landed a new bar for one symbol.

**Steps:**
1. Verify the initial `GET /api/health` response before the non-benchmark fetch.
2. Simulate an ingest job that fetches and persists a new `DailyPrice` row for a non-benchmark symbol dated D+1.
3. Call `GET /api/health` again to check readiness state after the fetch.

**Expected outcome:** The `readiness.state` remains unchanged from step 1 (still `"ready"` or `"initializing"`); `readiness.detail` is `null`. The non-benchmark symbol's new bar does NOT change the global readiness signal.
**Pass criteria:** State before == State after; state is NOT `"unavailable"` and NOT the new `"awaiting_snapshot"`.

---

### TC-03 — Benchmark symbol's latest bar advances past run; new state appears

**Type:** api
**Preconditions:** A `ScannerRun` is persisted for date D (e.g., 2026-07-18); the benchmark symbol (SPY) has its latest bar dated D; the benchmark's latest bar is then manually advanced to D+1 with NO `ScannerRun` yet created for D+1 (simulating the end of a fetch that landed new benchmark data).

**Steps:**
1. Verify initial `GET /api/health` returns `"ready"` or `"initializing"`.
2. Advance the benchmark symbol's latest bar to D+1 in the database (e.g., insert a `DailyPrice` row for SPY dated 2026-07-19).
3. Call `GET /api/health` and verify the response.

**Expected outcome:** `readiness.state` is the new literal `"awaiting_snapshot"` (not `"unavailable"`, not `"ready"`, not `"initializing"`); `readiness.detail` is a non-null string that names the condition (e.g., "Snapshot for 2026-07-19 pending") and points to a recovery action (e.g., "Run backfill or rebuild on Data Manager to catch up").
**Pass criteria:** `jq '.readiness.state'` == `"awaiting_snapshot"` AND `jq '.readiness.detail | length'` > 0 AND detail string contains date identifier and recovery hint.

---

### TC-04 — Health Badge renders the new awaiting_snapshot state

**Type:** browser
**Preconditions:** The app is running with TC-03's DB state (benchmark's latest bar at D+1, last run at D, state is `"awaiting_snapshot"`); user is on any page that displays the global health badge (e.g., Dashboard).

**Steps:**
1. Use Chrome MCP to navigate to the app's home/dashboard.
2. Locate the global health badge in the top bar.
3. Inspect the badge's data-testid and data-state attributes.
4. Capture a screenshot of the badge.
5. Verify the badge's visible text and styling.

**Expected outcome:** The badge element `[data-testid="readiness-badge"][data-state="awaiting_snapshot"]` is rendered; visible text is NOT "Backend unavailable"; badge uses a non-danger visual treatment (e.g., `Badge variant="accent"`); detail text is visible and names the condition + recovery pointer.
**Pass criteria:** Screenshot shows badge with distinct appearance (not red/danger); text clearly conveys "pending snapshot" or similar, NOT "Backend unavailable"; detail text visible.

---

### TC-05 — Preflight servability remains ok for awaiting_snapshot state

**Type:** api
**Preconditions:** TC-03's DB state (benchmark at D+1, run at D, `state == "awaiting_snapshot"`).

**Steps:**
1. Call the backend function `compute_preflight` (or retrieve `GET /api/health` and inspect the `preflight` object, if that endpoint is available).
2. Verify the servability component and overall verdict.

**Expected outcome:** The preflight's `servability.ok` is `true` (the new state does NOT trigger `NO-GO` or `DEGRADED`); the overall `preflight.verdict` is `GO`, not downgraded by the `awaiting_snapshot` state alone.
**Pass criteria:** `preflight.servability.ok == true` AND `preflight.verdict == "GO"`.

---

### TC-06 — Never-scanned DB still resolves to unavailable (regression guard)

**Type:** api
**Preconditions:** A fresh database with no `ScannerRun` rows persisted ever (the existing `unscanned_engine` fixture or equivalent state).

**Steps:**
1. Call `GET /api/health` on this never-scanned DB.
2. Verify the readiness state.

**Expected outcome:** `readiness.state` is `"unavailable"` (unchanged from previous behavior); the new `awaiting_snapshot` state is NOT used. This is a regression guard: true unavailability must never be masked by the new state.
**Pass criteria:** `jq '.readiness.state'` == `"unavailable"`.

---

### TC-07 — Job heartbeat advances through aggregate-refresh finalize phase

**Type:** api
**Preconditions:** Backend is running via `scripts/start-backend.sh`; a multi-date backfill or rebuild job is dispatched (e.g., backfill from 2026-07-10 to 2026-07-20); the job is actively running.

**Steps:**
1. Poll the job progress endpoint (e.g., `GET /api/jobs/<job_id>` or the data manager's job endpoint) every 2–5 seconds while the job runs.
2. Record the `JobProgress.last_progress_at` timestamp at multiple points, especially during and after the aggregate-refresh phase (the finalize phase that runs after the main per-date scan loop completes).
3. Verify that `last_progress_at` is advancing throughout the finalize phase, not frozen.
4. Check that the frontend's `/data` page shows the job's live status and does NOT display "· possibly stalled" during this phase while the job is healthy.

**Expected outcome:** `last_progress_at` advances at least once per date processed in the aggregate-refresh loop (not just during the main scan loop); the `/data` job card displays the job as active/progressing, not stalled, with a recent "updated Ns ago" message.
**Pass criteria:** Timestamps span the finalize phase duration (e.g., 2–5 tick calls recorded across dates); no "possibly stalled" text appears on `/data`; job completes successfully with no false stall warnings.

---

### TC-08 — Fresh DB cold-boot: coverage panel renders from persisted payload

**Type:** browser
**Preconditions:** A never-ingested DB copy is created (no `coverage_snapshot` rows, no prior `ScannerRun`); the backend is started fresh against this copy; the frontend connects to the backend.

**Steps:**
1. Ensure the backend boots cleanly against the fresh DB.
2. Navigate to the `/data` (Data Manager) page in the frontend.
3. Observe the coverage panel rendering.
4. Verify that the page loads within the committed performance budget and that no unbounded `daily_prices` table prefill occurs.
5. Inspect the backend logs or query plan to confirm indexed/bounded queries, not a full-table scan.

**Expected outcome:** The `/data` page renders the coverage panel from the persisted `coverage_snapshot` payload (empty/null if no snapshots exist); no full `daily_prices` table is streamed into RAM on page load; page load time is within budget (closes J-05's previously-SKIPPED UT-04 check).
**Pass criteria:** Page renders successfully without errors; backend logs show no "SELECT * FROM daily_prices" unbounded query; page load completes in <2 seconds (within typical budget).

---

### TC-09 — Required-still-passing journeys J-01, J-03, J-04 remain green

**Type:** browser
**Preconditions:** The iteration's code changes (`readiness.py`, `data_manager.py`, `health.py`, `api.ts`, `health-badge.tsx`) are deployed; the frontend and backend are running.

**Steps:**
1. Run the browser-qa deterministic replay for J-01 (Cadence Ingest — fetch/expand/rebuild full-stack acceptance).
2. Run the browser-qa deterministic replay for J-03 (Warm-boot coverage + logfile).
3. Run the browser-qa deterministic replay for J-04 (Global readiness badge + preflight banner).
4. Record all assertions/expectations from each journey's existing test suite.

**Expected outcome:** All 18+ pre-defined test steps from J-01, J-03, J-04 pass without modification; no regression in existing acceptance criteria; the global badge (J-04) still renders `"ready"`, `"initializing"`, `"unavailable"` states as expected (the new state is a 4th branch, not a replacement).
**Pass criteria:** Each of the three journeys passes its full scripted test suite with 100% assertion success; no new failures introduced.

---

### TC-10 — New benchmark-scoped query uses index, never whole-table scan

**Type:** api
**Preconditions:** The DB has the `(symbol, date)` index on `daily_prices` table (existing production index); a query plan inspection tool is available (e.g., SQLite's `EXPLAIN QUERY PLAN`).

**Steps:**
1. Identify the new query in `app/engine/readiness.py` that replaces `latest_data_date`'s whole-table max with a benchmark-symbol-only max.
2. Run `EXPLAIN QUERY PLAN` on this query, filtered to one symbol (SPY).
3. Inspect the query plan to confirm index usage.

**Expected outcome:** The query plan shows an index seek/range scan on the `(symbol, date)` index for a single symbol, not a full-table scan of `daily_prices`; row-read count is bounded by the number of rows for that one symbol (e.g., ~500 rows for SPY over all historical dates), not millions.
**Pass criteria:** Query plan output contains "SEARCH daily_prices USING INDEX" with symbol filter; row count estimate is <1000 (single symbol, bounded history).

---

## Summary

**Total test cases:** 10
**API tests:** 6 (TC-01, TC-02, TC-03, TC-05, TC-06, TC-10)
**Browser tests:** 3 (TC-04, TC-07, TC-08, TC-09)
**Integration/regression tests:** 1 (TC-09 — full regression on required-still-passing journeys)

**Mapping to DEFINITION OF DONE:**
- TC-01 → "Required-still-passing journeys J-01, J-03, J-04 remain green" (baseline regression guard)
- TC-02 → "B3 fixed" (non-benchmark fetch does not affect badge)
- TC-03, TC-04, TC-05 → "B3 fixed and evidenced live" (new state appears, badge renders, preflight unaffected)
- TC-06 → "Error cases: never-scanned DB still unavailable" (regression guard)
- TC-07 → "F1 fixed and evidenced live" (heartbeat advances through finalize phase)
- TC-08 → "J-05 step-3's previously-SKIPPED UT-04 check" (fresh DB cold-boot)
- TC-09 → "Required-still-passing journeys J-01, J-03, J-04 remain green" (full deterministic replay)
- TC-10 → "AG-8: new query is index-bounded, never whole-table scan" (no unbounded loads)
