# Phase goal-i_can_see_the_wealthy_future-iter-5 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running -->

**Overall:** 0/19 tests passed (19 skipped)

**Reason:** Frontend not running. A precondition check against the configured frontend URL `http://localhost:3836/scanner-runs` returned HTTP status `000` (connection could not be established), confirming the frontend dev server is not up. Per browser-qa-agent precondition rules, all browser test cases are recorded as SKIPPED rather than attempted. No browser automation was run.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | List page loads | smoke | P1 | `/scanner-runs` heading + table headers render, no error card | Not executed — frontend not running | SKIP | none |
| UT-02 | ≥2 dated rows newest-first | happy-path | P1 | ≥3 dated rows (2026-05-28, 2025-04-04, 2022-10-07) newest-first, clickable links | Not executed — frontend not running | SKIP | none |
| UT-03 | Regime badges colour-graded | happy-path | P1 | Green Risk-on (≈74.32) on 2026-05-28; red Risk-off on 2025-04-04 (≈6.30) & 2022-10-07 (≈8.34) | Not executed — frontend not running | SKIP | none |
| UT-04 | Risk-off rows read 0 Actionable | happy-path | P1 | Actionable = 0 for both Risk-off rows; non-zero for 2026-05-28 | Not executed — frontend not running | SKIP | none |
| UT-05 | Date link opens immutable detail | happy-path | P1 | URL → `/scanner-runs/<id>`; "Immutable snapshot — as of 2025-04-04" header | Not executed — frontend not running | SKIP | none |
| UT-06 | Risk-off detail: regime + zero Actionable (J-07) | happy-path | P1 | Red Risk-off badge, score 6.30; Actionable tile = 0; no Actionable setup in table | Not executed — frontend not running | SKIP | none |
| UT-07 | Regime breakdown + 3 breadth tiles | happy-path | P2 | Score + "/ 100" + component breakdown; 3 breadth tiles with % or NA | Not executed — frontend not running | SKIP | none |
| UT-08 | Older vs latest rankings differ (J-08) | happy-path | P1 | Top tickers/scores differ between 2022-10-07 and 2026-05-28 runs | Not executed — frontend not running | SKIP | none |
| UT-09 | "All runs" back navigation | happy-path | P2 | URL returns to `/scanner-runs`; run-list table shown | Not executed — frontend not running | SKIP | none |
| UT-10 | Risk-off-watchlist count tile | ux | P2 | Four tiles incl. "Risk-off-watchlist"; correct footnote | Not executed — frontend not running | SKIP | none |
| UT-11 | ScoreBadge styling matches leaderboard | ux | P3 | Stored run scores use same A–E bucket + number style as `/stocks` | Not executed — frontend not running | SKIP | none |
| UT-12 | Backend-unavailable list state | error | P2 | Red "Backend unavailable" card; no fabricated rows | Not executed — frontend not running | SKIP | none |
| UT-13 | Unknown run id → 404 state | error | P2 | "Run not found" card for id 999999; no fabricated run | Not executed — frontend not running | SKIP | none |
| UT-14 | Backend-unavailable detail state | error | P3 | Red "Backend unavailable" detail card; nothing fabricated | Not executed — frontend not running | SKIP | none |
| UT-15 | J-01 Dashboard regression | regression | P1 | Dashboard renders live regime panel + real data, unchanged | Not executed — frontend not running | SKIP | none |
| UT-16 | J-02 Leaderboard + filters regression | regression | P1 | Leaderboard renders with score badges; filtering/sorting works | Not executed — frontend not running | SKIP | none |
| UT-17 | J-03 Themes & J-04 Sectors regression | regression | P1 | Themes & Sectors render real data, no error cards | Not executed — frontend not running | SKIP | none |
| UT-18 | J-05/J-06 detail + consistency regression | regression | P1 | Stock detail loads; scores/bucket/setup identical to leaderboard | Not executed — frontend not running | SKIP | none |
| UT-19 | "Scanner Runs" discoverable in nav | ux | P2 | "Scanner Runs" nav item visible; navigates to `/scanner-runs` | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — all tests were skipped because the frontend is not running.

---

## Failed Tests

None — no test was executed, so none can be marked FAIL. (Per browser-qa-agent rules, an unavailable frontend is recorded as SKIPPED, never FAIL.)

---

## Skipped Tests

All 19 test cases (UT-01 through UT-19) were skipped for the same reason.

### UT-01 — List page loads
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — ≥2 dated rows newest-first
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — Regime badges colour-graded
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Risk-off rows read 0 Actionable
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Date link opens immutable detail
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Risk-off detail: regime + zero Actionable (J-07)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Regime breakdown + 3 breadth tiles
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — Older vs latest rankings differ (J-08)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — "All runs" back navigation
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Risk-off-watchlist count tile
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — ScoreBadge styling matches leaderboard
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Backend-unavailable list state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — Unknown run id → 404 state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — Backend-unavailable detail state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — J-01 Dashboard regression
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-16 — J-02 Leaderboard + filters regression
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-17 — J-03 Themes & J-04 Sectors regression
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-18 — J-05/J-06 detail + consistency regression
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-19 — "Scanner Runs" discoverable in nav
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3836 (precondition check returned HTTP `000` — connection refused, not running)
- **Browser:** Chrome via MCP (not invoked — precondition not met)
- **Test Date:** 2026-05-30
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-5-evidence/` (no screenshots — no tests executed)

---

## Notes

- This is a SKIPPED run, not a failure. The frontend dev server at `http://localhost:3836` was not reachable at QA time, so no user-visible behaviour could be exercised through the browser.
- The 19 test cases above remain valid and should be executed once the frontend is running. P1 cases (UT-01–UT-06, UT-08, UT-15–UT-18) must all pass for a PASS verdict; until then the browser-QA dimension of this iteration is unverified.
- API-level behaviour (TC-01..TC-10) is covered separately by the functional QA test plan and is not duplicated here.
