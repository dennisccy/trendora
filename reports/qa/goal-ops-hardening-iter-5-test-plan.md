# goal-ops-hardening-iter-5 Functional Test Plan

**Phase:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Frontend Present:** yes

## Phase Goal

Measure and certify that all 11 nav-listed pages in Trendora load only the data they need, with time-to-interactive (TTI) and on-load API latencies committed to a single performance budgets artifact, plus a ≤5-second cold-boot floor; any page exceeding its budget displays an honest loading state instead of a blank or frozen frame.

## Test Cases

### TC-01 — Backend cold-boot to first health check

**Type:** api
**Preconditions:** Backend process stopped; warm committed-seed database exists at the configured path; no frontend required

**Steps:**
1. Record the current system time (high precision)
2. Start the backend via `scripts/start-backend.sh`
3. Poll `GET /api/health` at 100 ms intervals until HTTP 200 is received
4. Record the wall time from process start to first HTTP 200

**Expected outcome:** First HTTP 200 response from `/api/health` arrives within 5 seconds of process start

**Pass criteria:** Wall-clock measurement ≤ 5.0 seconds and response status is HTTP 200

---

### TC-02 — Dashboard page (/) TTI and on-load API latencies

**Type:** browser
**Preconditions:** Backend running in prod mode (`scripts/start-backend.sh`); frontend running in prod mode (`scripts/start-frontend.sh`); frontend is reachable at `http://localhost:3000`

**Steps:**
1. Open Chrome DevTools Network tab; clear all entries
2. Navigate to `http://localhost:3000/` (Dashboard)
3. Record the time from navigation start to Time-to-Interactive (when the page is fully interactive)
4. Identify each of the page's on-load API calls in the Network tab: `/api/dashboard`, `/api/market-phase`, `/api/sectors`, `/api/themes`, plus any `/api/indexes?full=true` and `/api/regime-history?full=true` calls
5. Record the latency (time from request start to response complete) for each endpoint individually

**Expected outcome:** Dashboard loads completely within its committed TTI budget and each on-load API endpoint's latency is within its individual budget

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/dashboard` ≤ 1.5s; `/api/market-phase` ≤ 1.5s; `/api/sectors` ≤ 1.5s; `/api/themes` ≤ 1.5s; each additional endpoint (indexes, regime-history) ≤ 1.5s

---

### TC-03 — Stocks page (/stocks) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode; both services already warmed from prior test

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/stocks`
3. Record TTI from navigation start
4. Identify the `GET /api/stocks` request; record its latency

**Expected outcome:** Page loads with TTI and API latency within existing committed budgets

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/stocks` latency ≤ 1.5 seconds

---

### TC-04 — Stock detail page (/stocks/AAPL) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/stocks/AAPL`
3. Record TTI from navigation start
4. Identify `GET /api/stocks/AAPL` in Network tab; record its latency

**Expected outcome:** Detail page loads with TTI and API latency within existing committed budgets

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/stocks/AAPL` latency ≤ 0.3 seconds

---

### TC-05 — Sectors page (/sectors) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/sectors`
3. Record TTI from navigation start
4. Identify `GET /api/sectors` request; record its latency

**Expected outcome:** Page loads with TTI and API latency within newly-committed budgets (being measured for the first time)

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/sectors` latency ≤ 1.5 seconds

---

### TC-06 — Themes page (/themes) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/themes`
3. Record TTI from navigation start
4. Identify `GET /api/themes` request; record its latency

**Expected outcome:** Page loads with TTI and API latency within newly-committed budgets

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/themes` latency ≤ 1.5 seconds

---

### TC-07 — Data Manager page (/data) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/data`
3. Record TTI from navigation start
4. Identify `GET /api/data` request; record its latency

**Expected outcome:** Page loads with TTI and API latency within existing committed budgets; cold `/api/data` budget ≤ 2.0s is re-asserted

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/data` latency ≤ 1.5 seconds (warm) or ≤ 2.0 seconds (cold); budget documented in `reports/perf-budgets.md`

---

### TC-08 — Evidence page (/evidence) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/evidence`
3. Record TTI from navigation start
4. Identify `GET /api/evidence` request; record its latency

**Expected outcome:** Page loads with TTI and API latency within existing committed budgets (warm cache-hit path, per prior iteration)

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/evidence` latency ≤ 3.0 seconds

---

### TC-09 — Scanner Runs page (/scanner-runs) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/scanner-runs`
3. Record TTI from navigation start
4. Identify all network requests related to `/api/runs` and its child queries; record the cumulative on-load latency (including the per-run `ScannerResult` count queries, which are N+1 candidates per the spec)

**Expected outcome:** Page loads with TTI and API latency within newly-committed budgets; the N+1 pattern (per-run count queries over ~180+ runs) is measured

**Pass criteria:** TTI ≤ 3.0 seconds; total on-load API latency ≤ 1.5 seconds; documented in `reports/perf-budgets.md`

---

### TC-10 — Backtest page (/backtest) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/backtest`
3. Record TTI from navigation start
4. Identify `GET /api/backtest` request; record its total latency (including all 5 configured horizons' `evidence_by_horizon` aggregation — 1, 5, 10, 20, 60 days — each calling `compute_forward_aggregates`)

**Expected outcome:** Page loads with TTI and API latency within newly-committed budgets; the high-risk candidate endpoint (5 horizon iterations over ~1.5-1.7M row `forward_returns` table) is measured with extra attention

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/backtest` latency ≤ [newly-committed budget, typically ≤ 1.5-2.0s]; documented in `reports/perf-budgets.md`

---

### TC-11 — Watchlist page (/watchlist) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode; at least one watchlist entry is saved in the database (seed data or created via UI)

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/watchlist`
3. Record TTI from navigation start
4. Identify `GET /api/watchlist` request, including its `xray` payload field; record the latency

**Expected outcome:** Page loads with TTI and API latency within newly-committed budgets

**Pass criteria:** TTI ≤ 3.0 seconds; `/api/watchlist` latency ≤ 1.5 seconds; documented in `reports/perf-budgets.md`

---

### TC-12 — Research Event-Study Lab (/research/event-study) TTI and latency

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode

**Steps:**
1. Clear DevTools Network tab
2. Navigate to `http://localhost:3000/research/event-study`
3. Record TTI from navigation start
4. Identify the on-load API request for the event-study lab (may be a single endpoint or multiple related calls); record cumulative latency

**Expected outcome:** Lab loads with TTI and API latency within newly-committed budgets

**Pass criteria:** TTI ≤ 3.0 seconds; on-load API latency ≤ 1.5 seconds; documented in `reports/perf-budgets.md`

---

### TC-13 — Code-level audit of all 11 pages' backing endpoints

**Type:** artifact
**Preconditions:** Source code available; dev handoff document created; all 11 pages already measured (TC-01 through TC-12)

**Steps:**
1. Trace each of the 11 pages' backing endpoint(s) in the source code
2. For each endpoint, determine whether it:
   - Reads a persisted snapshot/cache (e.g., via a table row key lookup)
   - Performs an indexed-bounded query (e.g., windowed by date range or symbol)
   - Performs an unbounded `daily_prices` whole-table scan (violation)
   - Recomputes an already-persisted inventory aggregate (violation)
3. Explicitly re-trace the two named high-risk candidates:
   - `GET /api/backtest` → `compute_forward_aggregates` in `forward_testing.py:813-818` (5-horizon loop over `select(ForwardReturn).where(horizon==h)`)
   - `GET /api/runs` → per-run `ScannerResult` count query in `runs.py:33-36` (N+1 pattern)
4. Document findings in `docs/handoffs/goal-ops-hardening-iter-5-dev.md`

**Expected outcome:** Dev handoff names, per endpoint, whether it is persisted/cached/indexed-bounded, or identifies exactly which call site violates the unbounded-load / uncached-recompute rule and what fix was applied

**Pass criteria:** Handoff document exists at correct path; every endpoint is explicitly audited; any violation identified is noted with the exact code location and fix applied (if contingent fix was triggered); zero unnamed violations remain

---

### TC-14 — Loading state for over-budget pages

**Type:** browser
**Preconditions:** At least one page measured in TC-02 through TC-12 exceeds its committed budget (contingent); backend and frontend running in prod mode

**Steps:**
1. Clear browser cache and DevTools cache (hard reload)
2. Navigate to the identified over-budget page
3. Observe the page from navigation start until data arrival is complete
4. Verify that a visibly distinct loading/progress element is rendered while data loads

**Expected outcome:** Over-budget page displays a loading or progress indicator (skeleton, spinner, or warming state) — never a blank or frozen frame — until the API response completes and the page renders data

**Pass criteria:** Loading state is visually distinct and present; uses an existing pattern from the codebase (e.g., `XSkeleton` or `warming-state.tsx`); page becomes fully interactive only after data arrives

---

### TC-15 — All perf budgets in single artifact

**Type:** artifact
**Preconditions:** All measurements from TC-01 through TC-12 completed and recorded

**Steps:**
1. Search the repository for all performance budgets or measurement artifacts
2. Verify that `reports/perf-budgets.md` contains ONE new dated section with all new and re-measured numbers
3. Verify no second budgets artifact exists anywhere else in the repo (no separate `perf-*.md`, `measurements.md`, or similar files)

**Expected outcome:** All measurements live in a single file: `reports/perf-budgets.md`

**Pass criteria:** One dated section added to `reports/perf-budgets.md`; no other perf/measurement artifacts created; file is readable and all numbers are recorded with dates and page names

---

### TC-16 — Regression replay of J-01, J-03, J-04, J-05

**Type:** browser
**Preconditions:** Backend and frontend running in prod mode; all four prior journeys' test data/seed state available; deterministic golden scripts available

**Steps:**
1. Execute the deterministic golden browser script for J-01 (backfill honors requested range, explains zero-work)
2. Execute the deterministic golden browser script for J-03 (no per-run range cap)
3. Execute the deterministic golden browser script for J-04 (non-blocking boot with visible status)
4. Execute the deterministic golden browser script for J-05 (aggregates precomputed at ingest)
5. For any script that fails, apply LLM fallback (re-run with adaptive steps)
6. Record pass/fail for each journey with any observed deviations

**Expected outcome:** All four prior journeys continue to pass; zero regressions introduced by this iteration's changes

**Pass criteria:** All four journeys pass with zero regression attributable to iter-5's changes; if LLM fallback is needed, it still resolves to a passing state

---

### TC-17 — Contingent: Cached value byte-identity

**Type:** artifact
**Preconditions:** A contingent cache fix was applied (e.g., a new warm cache for `compute_forward_aggregates`); unit tests exist for the new cache

**Steps:**
1. Locate the new/modified unit test file (e.g., `test_forward_testing.py` or `test_data_manager.py`)
2. Run the test that asserts byte-identity between the cached value and the canonical live computation for the same as-of date
3. Verify the test passes

**Expected outcome:** Cached value is byte-identical to the canonical computation; no numeric or structural differences

**Pass criteria:** Unit test `test_*_byte_identity` or similar passes with no failures; the assertion compares the cached serialized value to the live computation result for the same as-of

---

### TC-18 — Contingent: Cache miss returns honest sentinel; refresh on ingest

**Type:** artifact
**Preconditions:** A contingent cache fix was applied; unit tests for cache semantics exist

**Steps:**
1. Run the unit test that queries a newly-added ingest-time cache for a not-yet-warmed key
2. Verify the test asserts the existing "not yet computed" or NA sentinel is returned (never fabricated values, never HTTP 500)
3. Run the unit test that verifies cache refresh/invalidation on every ingest kind that changes the underlying data (fetch, backfill, rebuild)
4. Verify the test exercises BOTH fetch-then-view AND backfill-then-view paths (iter-2 B1 lesson: fingerprint-only invalidation must not serve a false all-zero sentinel on a fully-populated DB)

**Expected outcome:** Cache miss returns honest sentinel; cache is refreshed on every relevant ingest kind

**Pass criteria:** Both unit tests pass; no fabricated sentinel values; cache stays consistent across fetch and backfill paths

---

### TC-19 — Unit and integration test suite passes

**Type:** artifact
**Preconditions:** All code changes (contingent or zero-diff) completed; backend test suite executable

**Steps:**
1. Run the relevant backend test suite: `pytest tests/test_bar_cache.py tests/test_scoring_window.py tests/test_forward_testing.py tests/test_data_manager.py tests/test_health.py tests/test_api_engine.py` (if no contingent fix) or extended suite if a fix was applied
2. Capture the full test output (pass/fail count, any failures listed)
3. Compare against the pre-iteration baseline count

**Expected outcome:** All tests pass; zero new failures introduced by this iteration

**Pass criteria:** Test suite exit code is 0 (success); no new test failures vs. baseline; all pre-existing tests continue to pass

---

### TC-20 — Dev handoff complete and comprehensive

**Type:** artifact
**Preconditions:** All changes completed; measurements recorded; code audit finished

**Steps:**
1. Open `docs/handoffs/goal-ops-hardening-iter-5-dev.md`
2. Verify it contains:
   - TC-13 code audit findings (per-endpoint persisted/cached/indexed-bounded analysis)
   - Pointer to the exact `reports/perf-budgets.md` section added by this iteration (with date/section number)
   - Explicit statement of whether a contingent fix was applied (and why, if not)
3. Verify the handoff is readable and complete

**Expected outcome:** Dev handoff document exists and is comprehensive

**Pass criteria:** Handoff file exists at correct path; contains TC-13 audit, perf-budgets.md pointer, and contingent-fix statement; no ambiguities or incomplete sections

---

## Summary

**Total test cases:** 20
- **API tests:** 1 (TC-01: backend cold-boot)
- **Browser tests:** 11 (TC-02 through TC-12: individual page TTI and latency measurements)
- **Artifact checks:** 8 (TC-13: code audit; TC-15: single budgets file; TC-16: regression replay; TC-17-TC-18: contingent cache semantics; TC-19: test suite; TC-20: dev handoff)

**Contingent test cases:** TC-14 (loading state — only if a page exceeds budget), TC-17 (cache byte-identity — only if a fix lands), TC-18 (cache sentinel — only if a fix lands)

All measurements recorded in: `reports/perf-budgets.md`
Dev handoff location: `docs/handoffs/goal-ops-hardening-iter-5-dev.md`
