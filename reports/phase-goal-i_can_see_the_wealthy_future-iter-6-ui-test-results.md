# Phase goal-i_can_see_the_wealthy_future-iter-6 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-6 — Walk-forward forward-testing engine + System Health evidence (J-09, J-10)
**Date:** 2026-05-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running -->

**Overall:** 0/15 tests passed (15 skipped)

---

## Precondition Check

| Check | Command | Result |
|-------|---------|--------|
| Frontend reachable | `curl http://localhost:3836` | `000` — **unreachable (connection refused)** |
| Backend reachable | `curl http://localhost:8835/health` | `404` |

The frontend at the configured URL (`http://localhost:3836`) is **not running**. Per the browser-qa-agent precondition rules and the explicit dispatch directive ("Frontend is NOT available… Do NOT attempt to run browser tests"), all test cases are marked SKIPPED. No browser automation was attempted; no screenshots were captured.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Page loads and is populated | smoke | P1 | System Health heading + 5 evidence panels render | Not executed — frontend not running | SKIP | none |
| UT-02 | Survivorship-bias banner visible | happy-path | P1 | Amber "Survivorship bias" banner under heading | Not executed — frontend not running | SKIP | none |
| UT-03 | By-bucket A–E table (mean + n) | happy-path | P1 | Rows A–E each with `+/-NN.NN%` and `n=NN` | Not executed — frontend not running | SKIP | none |
| UT-04 | Excess vs SPY / QQQ panels | happy-path | P1 | SPY + QQQ rows with stocks/benchmark/excess + `n` | Not executed — frontend not running | SKIP | none |
| UT-05 | By-setup / by-regime breakdowns | happy-path | P1 | Setup rows + both Risk-on/Risk-off regimes, mean + n | Not executed — frontend not running | SKIP | none |
| UT-06 | Control-group comparison (5 cohorts) | happy-path | P1 | 5 cohort rows, top-ranked highlighted, mean + n | Not executed — frontend not running | SKIP | none |
| UT-07 | Horizon selector changes figures | happy-path | P1 | Clicking 5d updates active state + figures + hint | Not executed — frontend not running | SKIP | none |
| UT-08 | Summary strip content | happy-path | P2 | Snapshot count, as-of range, overall mean, legend | Not executed — frontend not running | SKIP | none |
| UT-09 | Low-sample ⚠ flag | validation | P2 | `n < min` figures flagged with ⚠, not hidden | Not executed — frontend not running | SKIP | none |
| UT-10 | Pos/neg colour coding | ux | P3 | Green for +%, red for −%, grey for — | Not executed — frontend not running | SKIP | none |
| UT-11 | Backend-unavailable red alert | error | P2 | Red "Backend unavailable" alert, no fabricated 0% | Not executed — frontend not running | SKIP | none |
| UT-12 | Loading skeleton | smoke | P3 | 4 pulsing skeleton cards before data | Not executed — frontend not running | SKIP | none |
| UT-13 | Scanner Runs history regression | regression | P1 | `/scanner-runs` loads + shows added as-of snapshots | Not executed — frontend not running | SKIP | none |
| UT-14 | J-01–J-08 pages still load | regression | P1 | `/`, `/stocks`, `/sectors`, `/themes` all render | Not executed — frontend not running | SKIP | none |
| UT-15 | Discoverable from sidebar | ux | P2 | "System Health" sidebar link navigates correctly | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — no tests were executed.

---

## Failed Tests

None — no tests were executed.

---

## Skipped Tests

All 15 test cases were skipped for the same reason: **frontend not running** (the dev server at `http://localhost:3836` was unreachable — `curl` returned HTTP `000` / connection refused). No browser tests were attempted, per the dispatch directive.

### UT-01 — Page loads and is populated
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-02 — Survivorship-bias banner visible
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-03 — By-bucket A–E table (mean + n)
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-04 — Excess vs SPY / QQQ panels
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-05 — By-setup / by-regime breakdowns
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-06 — Control-group comparison (5 cohorts)
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-07 — Horizon selector changes figures
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-08 — Summary strip content
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-09 — Low-sample ⚠ flag
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-10 — Pos/neg colour coding
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-11 — Backend-unavailable red alert
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-12 — Loading skeleton
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-13 — Scanner Runs history regression
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-14 — J-01–J-08 pages still load
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

### UT-15 — Discoverable from sidebar
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3836 unreachable)

---

## Environment

- **Frontend URL:** http://localhost:3836 (unreachable — HTTP 000)
- **Backend URL:** http://localhost:8835 (/health returned 404)
- **Browser:** Chrome via MCP — not invoked (no frontend to test)
- **Test Date:** 2026-05-30
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-6-evidence/` (empty — no screenshots, all tests skipped)
