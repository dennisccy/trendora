# Phase goal-i_can_see_the_wealthy_future-iter-8 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Date:** 2026-05-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running -->

**Overall:** 0/15 tests passed (15 skipped)

---

## Precondition Check

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Frontend reachable | `curl http://localhost:3835` | HTTP `000` (connection failed) | **DOWN** |
| Backend reachable | `curl http://localhost:8835/health` | HTTP `404` | reachable, but irrelevant — frontend down |

The frontend at `http://localhost:3835` is not running (connection refused / no listener).
Per the browser-qa-agent precondition rules ("If not running and no auto-start capability:
write all tests as SKIPPED with reason 'frontend not running'") and the dispatch instruction
("Frontend is NOT available. Mark all tests as SKIPPED ... Do NOT attempt to run browser tests."),
no browser automation was attempted. All 15 user-visible test cases are recorded as SKIPPED.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads with as-of switcher in top bar | smoke | P1 | Dashboard + as-of switcher (`aria-label="View as-of date"`) and "Latest" badge visible | Not executed — frontend not running | SKIP | none |
| UT-02 | As-of switcher offers Latest plus stored run dates | smoke | P1 | First option "Latest · {latest}", older run dates below, no duplicate/blank entries | Not executed — frontend not running | SKIP | none |
| UT-03 | Select a past date time-travels the Dashboard | happy-path | P1 | "Data as-of {D_OLD}" badge; panels re-point to historical values | Not executed — frontend not running | SKIP | none |
| UT-04 | Historical indicator badge appears and clears | happy-path | P1 | Amber "Viewing as-of {D_OLD} (historical)" appears, then clears back to "Latest" | Not executed — frontend not running | SKIP | none |
| UT-05 | Selected date carries across in-app navigation | happy-path | P1 | "as of {D_OLD}" persists across `/stocks`, `/themes`, `/sectors` | Not executed — frontend not running | SKIP | none |
| UT-06 | Stocks leaderboard reflects the selected date | happy-path | P1 | "as of {D_OLD}" badge; ranked rows re-point to historical snapshot | Not executed — frontend not running | SKIP | none |
| UT-07 | Leaderboard filters still work after re-point | regression | P1 | Sector filter narrows/restores rows; as-of badge unaffected by filtering | Not executed — frontend not running | SKIP | none |
| UT-08 | Stock detail matches leaderboard scores at latest and historical | regression | P1 | List↔detail score coherence holds at latest and at D_OLD | Not executed — frontend not running | SKIP | none |
| UT-09 | Stock price chart shows no future bars in a historical view | happy-path | P1 | Caption "{n} bars · as of {D_OLD}"; no bar after D_OLD; MA ends at/before D_OLD | Not executed — frontend not running | SKIP | none |
| UT-10 | Themes page reflects the selected date | happy-path | P1 | "as of {D_OLD}" badge; theme rows re-point to historical snapshot | Not executed — frontend not running | SKIP | none |
| UT-11 | Sectors page reflects the selected date | happy-path | P1 | "as of {D_OLD}" badge; sector rows re-point to historical snapshot | Not executed — frontend not running | SKIP | none |
| UT-12 | Reset to Latest restores the current view everywhere | happy-path | P1 | "as of {latest}" + quiet "Latest" indicator restored on all pages | Not executed — frontend not running | SKIP | none |
| UT-13 | Hard refresh returns to Latest | ux | P3 | After F5, badge returns to "as of {latest}" (date held in client state only) | Not executed — frontend not running | SKIP | none |
| UT-14 | As-of-aware page surfaces a clear error on backend failure | error | P2 | "Backend unavailable" card; no blank screen / no fabricated data | Not executed — frontend not running | SKIP | none |
| UT-15 | Switcher discoverability and labelling | ux | P2 | Date drop-down visible on every page; label "View as-of date"; amber "(historical)" state | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — frontend not running.

---

## Failed Tests

None — no tests were executed (no FAIL recorded; see Skipped Tests).

---

## Skipped Tests

All 15 tests were skipped for the same reason: **frontend not running** (the frontend at
`http://localhost:3835` returned HTTP `000` / connection failed during the precondition check).

### UT-01 — Dashboard loads with as-of switcher in top bar
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — As-of switcher offers Latest plus stored run dates
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — Select a past date time-travels the Dashboard
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Historical indicator badge appears and clears
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Selected date carries across in-app navigation
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Stocks leaderboard reflects the selected date
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Leaderboard filters still work after re-point
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — Stock detail matches leaderboard scores at latest and historical
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Stock price chart shows no future bars in a historical view
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Themes page reflects the selected date
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — Sectors page reflects the selected date
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Reset to Latest restores the current view everywhere
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — Hard refresh returns to Latest
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — As-of-aware page surfaces a clear error on backend failure
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — Switcher discoverability and labelling
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3835 (not running — HTTP 000 / connection failed)
- **Backend URL:** http://localhost:8835 (reachable; `/health` returned HTTP 404 — not exercised)
- **Browser:** Chrome via MCP (not used — no frontend to drive)
- **Test Date:** 2026-05-31
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-8-evidence/` (no screenshots — no tests executed)
