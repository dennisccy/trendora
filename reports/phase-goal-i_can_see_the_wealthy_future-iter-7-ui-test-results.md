# Phase goal-i_can_see_the_wealthy_future-iter-7 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running -->

**Overall:** 0/15 tests passed (15 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Page loads with empty state | smoke | P1 | Watchlist heading, Add panel, empty-state star card | Not executed — frontend not running | SKIP | none |
| UT-02 | Add a stock, see its row | happy-path | P1 | New ANET row with scores after Add | Not executed — frontend not running | SKIP | none |
| UT-03 | Scores match /stocks (single-source) | happy-path | P1 | Watchlist badges identical to /stocks for ANET | Not executed — frontend not running | SKIP | none |
| UT-04 | Honest 0.00% Since added | happy-path | P2 | Since-added cell shows +0.00% in muted text | Not executed — frontend not running | SKIP | none |
| UT-05 | Invalidation matches detail | regression | P2 | Invalidation text identical to /stocks/ANET | Not executed — frontend not running | SKIP | none |
| UT-06 | Ticker link → stock detail | happy-path | P1 | ANET link navigates to /stocks/ANET | Not executed — frontend not running | SKIP | none |
| UT-07 | Remove deletes the row | happy-path | P1 | Row removed, empty state returns, no full reload | Not executed — frontend not running | SKIP | none |
| UT-08 | Unknown ticker rejected | error | P2 | Inline alert, no ZZZZ row, fields not cleared | Not executed — frontend not running | SKIP | none |
| UT-09 | Duplicate ticker rejected | error | P2 | Inline alert, still exactly one ANET row | Not executed — frontend not running | SKIP | none |
| UT-10 | Add disabled when ticker empty | validation | P2 | Add button disabled while Ticker empty | Not executed — frontend not running | SKIP | none |
| UT-11 | Reason optional | validation | P3 | Add succeeds ticker-only, Reason shows em-dash | Not executed — frontend not running | SKIP | none |
| UT-12 | Backend-unavailable error card | error | P2 | Honest "Backend unavailable" card, no fabricated rows | Not executed — frontend not running | SKIP | none |
| UT-13 | Survives backend restart | regression | P1 | ANET row persists after backend restart (DB-backed) | Not executed — frontend not running | SKIP | none |
| UT-14 | Reachable from sidebar | ux | P3 | Sidebar "Watchlist" link opens working page | Not executed — frontend not running | SKIP | none |
| UT-15 | Prior journeys still render | regression | P1 | /, /stocks, /sectors all load without regression | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — no tests were executed.

---

## Failed Tests

None — no tests failed. No browser automation was attempted.

---

## Skipped Tests

All 15 test cases were skipped for the same reason: the frontend was reported as **not running** by the harness (Frontend available: no), and the agent instructions directed not to attempt browser tests. No browser session was launched, so no evidence screenshots were captured.

### UT-01 — Page loads with empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — Add a stock, see its row
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — Scores match /stocks (single-source)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Honest 0.00% Since added
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Invalidation matches detail
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Ticker link → stock detail
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Remove deletes the row
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — Unknown ticker rejected
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Duplicate ticker rejected
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Add disabled when ticker empty
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — Reason optional
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Backend-unavailable error card
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — Survives backend restart
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — Reachable from sidebar
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — Prior journeys still render
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Notes

- Reason for skip: **frontend not running** (Frontend available: no). Per the browser-qa-agent precondition rule, when the frontend is not running and there is no auto-start capability, all tests are written as SKIPPED with that reason rather than FAIL.
- This is an environment/availability condition, not a defect in the implementation under test. The watchlist persistence functionality (UT-01 … UT-15) was therefore not exercised through the browser in this run.
- Backend functional coverage for watchlist persistence is handled separately by the QA functional test plan (`reports/qa/goal-i_can_see_the_wealthy_future-iter-7-test-plan.md`) and the backend test suites (`apps/backend/tests/test_api_watchlist.py`, `apps/backend/tests/test_watchlist_persistence.py`).
- **Recommendation:** re-run browser QA once the frontend at http://localhost:3836 is reachable to obtain real UI verification and evidence screenshots, especially for the P1 cases (UT-01, UT-02, UT-03, UT-06, UT-07, UT-13, UT-15) that gate the PASS verdict.

---

## Environment

- **Frontend URL:** http://localhost:3836 (not available this run)
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP — not launched (frontend unavailable)
- **Test Date:** 2026-05-30
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-7-evidence/` (empty — no screenshots captured)
