# Phase goal-i_can_see_the_wealthy_future-iter-2 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running — all tests skipped -->

**Overall:** 0/19 tests passed (19 skipped)

**Reason:** Frontend not running. The frontend at `http://localhost:3835` is unreachable (HTTP `000` / connection refused). Per the browser-qa-agent precondition check and the dispatch instruction ("Frontend available: no"), all browser test cases are marked SKIPPED. No browser automation was attempted.

---

## Precondition Check

| Service | Endpoint | Result | Status |
|---------|----------|--------|--------|
| Frontend | `http://localhost:3835` | `000` (connection refused / unreachable) | DOWN |
| Backend | `http://localhost:8835/health` | `404` | not validated (frontend is the blocking precondition) |

Because the frontend is not serving, no page can be loaded and no UI test case can be executed. Chrome MCP was not invoked.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/sectors` loads | smoke | P1 | Sectors heading + ranked table render, no errors | Not executed — frontend unreachable | SKIP | none |
| UT-02 | `/` Dashboard loads | smoke | P1 | Dashboard heading + regime/breadth/Top Sectors cards render | Not executed — frontend unreachable | SKIP | none |
| UT-03 | Ranked leaderboard descending | happy-path | P1 | ≥10 rows, `#` counts up, scores non-increasing | Not executed — frontend unreachable | SKIP | none |
| UT-04 | Top row RS / dist / trend | happy-path | P1 | RS%, dist% and trend label all non-blank on row #1 | Not executed — frontend unreachable | SKIP | none |
| UT-05 | A–E colour-graded score badge | happy-path | P1 | Letter badge + 2-decimal raw number, colour-graded | Not executed — frontend unreachable | SKIP | none |
| UT-06 | Expand row → component breakdown (+keyboard) | happy-path | P1 | Click/Enter toggles breakdown grid below row | Not executed — frontend unreachable | SKIP | none |
| UT-07 | SPY excluded; benchmark badge | ux | P2 | No SPY row; "RS benchmark: SPY (excluded)" badge | Not executed — frontend unreachable | SKIP | none |
| UT-08 | "as of" date badge | ux | P2 | Badge "as of 2026-05-28" (real YYYY-MM-DD) | Not executed — frontend unreachable | SKIP | none |
| UT-09 | Regime label + numeric score | happy-path | P1 | One of six labels + 0–100 score (≈74.32) | Not executed — frontend unreachable | SKIP | none |
| UT-10 | Regime component breakdown | happy-path | P1 | Named regime components with numeric contributions | Not executed — frontend unreachable | SKIP | none |
| UT-11 | 3× universe-relative breadth cards | happy-path | P1 | 50-DMA / 200-DMA / Net new highs cards, universe-relative caption | Not executed — frontend unreachable | SKIP | none |
| UT-12 | Data as-of badge | ux | P2 | Badge "Data as-of 2026-05-28" with clock icon | Not executed — frontend unreachable | SKIP | none |
| UT-13 | Top Sectors = `/sectors` (single source) | happy-path | P1 | Top Sectors row #1 identical to `/sectors` row #1 | Not executed — frontend unreachable | SKIP | none |
| UT-14 | Pending placeholders (no fake zeros) | ux | P2 | Candidate Counts / Top Themes show — and "pending" badge | Not executed — frontend unreachable | SKIP | none |
| UT-15 | `/sectors` backend-unavailable state | error | P2 | Red "Backend unavailable" card, no fabricated rows | Not executed — frontend unreachable | SKIP | none |
| UT-16 | `/` backend-unavailable state | error | P2 | Red "Backend unavailable" card, no fabricated numbers | Not executed — frontend unreachable | SKIP | none |
| UT-17 | Top Sectors degrades independently | error | P3 | Regime renders; Top Sectors card alone shows error | Not executed — frontend unreachable | SKIP | none |
| UT-18 | Sidebar discoverability | ux | P2 | Sidebar Dashboard/Sectors links navigate + highlight active | Not executed — frontend unreachable | SKIP | none |
| UT-19 | Other routes not regressed | regression | P3 | `/stocks`, `/themes` still render empty states | Not executed — frontend unreachable | SKIP | none |

---

## Passed Tests

None — no tests were executed.

---

## Failed Tests

None — no tests were executed. (No FAIL verdicts: per agent rules, a not-running frontend is recorded as SKIPPED, never FAIL.)

---

## Skipped Tests

All 19 test cases were skipped for the same reason: **frontend not running** (`http://localhost:3835` returned HTTP `000` — connection refused). No browser automation (Chrome MCP) was attempted.

### UT-01 — `/sectors` page loads without errors (smoke)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — `/` Dashboard page loads without errors (smoke)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — `/sectors` shows a ranked leaderboard ordered by score (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Top row exposes RS-vs-SPY, distance-from-high, and a trend label (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Sector Score cell shows a colour-graded A–E badge + raw number (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Clicking a row expands its component breakdown; keyboard works too (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — SPY appears only as the excluded benchmark, never as a ranked row (ux)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — `/sectors` shows an honest "as of" date badge (ux)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Dashboard Market Regime panel shows a valid label + numeric score (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Regime score carries a named component breakdown (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — Three universe-relative breadth metric cards are shown (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Dashboard shows a "Data as-of" badge (ux)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — Top Sectors card matches `/sectors` (single source of truth) (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — Candidate Counts & Top Themes show honest "pending" placeholders (ux)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — `/sectors` shows "Backend unavailable" when the API is down (error)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-16 — `/` Dashboard shows "Backend unavailable" when the API is down (error)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-17 — Top Sectors degrades independently of the regime panel (error)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-18 — New analytical pages are reachable from the sidebar (ux / discoverability)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-19 — Unrelated sidebar routes still render their empty states (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3835 — **DOWN** (HTTP `000`, connection refused)
- **Backend URL:** http://localhost:8835 (`/health` → `404`; not validated since frontend is the blocking precondition)
- **Browser:** Chrome via MCP — **not invoked** (precondition failed)
- **Test Date:** 2026-05-29
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-2-evidence/` (empty — no screenshots captured because no tests executed)

---

## Note for downstream agents

These 19 browser tests are **untested**, not validated. The SKIPPED verdict reflects an environmental blocker (frontend not running), **not** a defect in the implementation. The functional/API + unit coverage referenced in `reports/qa/...-test-plan.md` (TC-01…TC-14) is independent of these browser tests and should be consulted for backend-side confidence. To obtain browser evidence, re-run `./scripts/automation/browser-qa-phase.sh goal-i_can_see_the_wealthy_future-iter-2` with the frontend successfully started on port 3835.
