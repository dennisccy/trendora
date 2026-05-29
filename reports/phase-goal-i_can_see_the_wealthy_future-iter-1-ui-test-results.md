# Phase goal-i_can_see_the_wealthy_future-iter-1 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running. ALL tests skipped. -->

**Overall:** 0/15 tests passed (15 skipped)

---

## Precondition Check

Per the browser-qa-agent precondition protocol, service availability was checked before any test execution:

| Service | URL | Result | Status |
|---------|-----|--------|--------|
| Frontend | `http://localhost:3835/` | `000` (connection failed) | **NOT RUNNING** |
| Backend (health) | `http://localhost:8835/api/health` | `200` | running |
| Backend (alias) | `http://localhost:8835/health` | `404` | n/a (endpoint is `/api/health`) |

The **frontend is not running** (connection refused on port 3835). Without a frontend, no browser-driven UI test can be executed. The backend being reachable does not change this: every test case (UT-01 … UT-15) requires rendering the frontend at `http://localhost:3835`.

Per agent rules, all tests are recorded as **SKIPPED** with reason "frontend not running". No browser automation was attempted and no test results were fabricated.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads (shell + empty state) | smoke | P1 | Dashboard renders with sidebar, header, "No scan yet" empty state | Not executed — frontend not running | SKIP | none |
| UT-02 | All 7 sidebar destinations present | smoke | P1 | 7 labeled nav links in order + footer text | Not executed — frontend not running | SKIP | none |
| UT-03 | Sidebar navigation + active highlight | happy-path | P1 | Each link routes + highlights active item | Not executed — frontend not running | SKIP | none |
| UT-04 | Stocks empty state | smoke | P1 | "Stocks" heading + "No ranked stocks yet" card | Not executed — frontend not running | SKIP | none |
| UT-05 | Themes empty state | smoke | P1 | "Themes" heading + "No ranked themes yet" card | Not executed — frontend not running | SKIP | none |
| UT-06 | Sectors empty state | smoke | P1 | "Sectors" heading + "No ranked sectors yet" card | Not executed — frontend not running | SKIP | none |
| UT-07 | Scanner Runs empty state | smoke | P1 | "Scanner Runs" heading + "No scanner runs yet" card | Not executed — frontend not running | SKIP | none |
| UT-08 | System Health empty state | smoke | P1 | "System Health" heading + "No evidence yet" card | Not executed — frontend not running | SKIP | none |
| UT-09 | Watchlist empty state | smoke | P1 | "Watchlist" heading + "Your watchlist is empty" card | Not executed — frontend not running | SKIP | none |
| UT-10 | Stock detail stub resolves | smoke | P1 | `/stocks/NVDA` returns 200 with "NVDA" heading (not 404) | Not executed — frontend not running | SKIP | none |
| UT-11 | Run detail stub resolves | smoke | P1 | `/scanner-runs/1` returns 200 with "Run #1" heading (not 404) | Not executed — frontend not running | SKIP | none |
| UT-12 | Health badge connected (live values) | happy-path | P1 | "Backend OK", "provider: seed", "seed 2026-05-28", "158 symbols" | Not executed — frontend not running | SKIP | none |
| UT-13 | Health badge "Backend unavailable" | error | P1 | Red "Backend unavailable" badge, no fabricated healthy status | Not executed — frontend not running | SKIP | none |
| UT-14 | Dense-dark analytical theme applied | ux | P2 | Near-black bg, teal accents, sidebar+header layout | Not executed — frontend not running | SKIP | none |
| UT-15 | Header/badge persists across nav | regression | P2 | Header/badge persists, badge stays "Backend OK" across nav | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — all tests skipped (see precondition check).

---

## Failed Tests

None — all tests skipped (see precondition check). No test was marked FAIL, as a non-running frontend is a skip condition, not a functional failure.

---

## Skipped Tests

All 15 UI test cases were skipped for the same reason: **frontend not running** (connection refused at `http://localhost:3835`).

### UT-01 — Dashboard loads (shell + empty state)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — All 7 sidebar destinations present
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — Sidebar navigation + active highlight
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Stocks empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Themes empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Sectors empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Scanner Runs empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — System Health empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Watchlist empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Stock detail stub resolves
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — Run detail stub resolves
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Health badge connected (live values)
**Verdict:** SKIPPED
**Reason:** frontend not running (note: backend `/api/health` did return 200, but the badge is a frontend surface that could not be rendered)

### UT-13 — Health badge "Backend unavailable"
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — Dense-dark analytical theme applied
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — Header/badge persists across nav
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3835 (not running — connection refused, HTTP `000`)
- **Backend URL:** http://localhost:8835 (`/api/health` → HTTP `200`)
- **Browser:** Chrome via MCP — not invoked (no frontend to test)
- **Test Date:** 2026-05-29
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-1-evidence/` (empty — no states reached to screenshot)
