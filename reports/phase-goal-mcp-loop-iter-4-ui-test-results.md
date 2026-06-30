# Phase goal-mcp-loop-iter-4 — UI Test Results

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/11 tests passed (11 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Evidence page loads without errors | smoke | P1 | Page renders with heading and two claim rows | Frontend not running | SKIP | none |
| UT-02 | Dashboard loads without errors | smoke | P1 | Dashboard renders with Market Regime card | Frontend not running | SKIP | none |
| UT-03 | Breakout-watch row displays "Regime: Risk-on" badge | happy-path | P1 | "Regime: Risk-on" badge visible in second row | Frontend not running | SKIP | none |
| UT-04 | Breakout-watch row shows correct title and subtitle | happy-path | P1 | Title "Breakout-watch setup" and subtitle visible | Frontend not running | SKIP | none |
| UT-05 | Breakout-watch linkback reads "Research event-study lab" and navigates to /research/event-study | happy-path | P1 | Linkback text correct and navigates to /research/event-study | Frontend not running | SKIP | none |
| UT-06 | Dashboard Market Regime card contains the Evidence affordance link | happy-path | P1 | "See evidence proven in this regime →" link visible | Frontend not running | SKIP | none |
| UT-07 | Dashboard affordance link navigates to the Evidence page | happy-path | P1 | Click navigates to /evidence with both claim rows | Frontend not running | SKIP | none |
| UT-08 | Breakout-watch row displays holdout edge, control comparison, and registration date | happy-path | P1 | "+6.12%", "vs SPY", "2026-06-30" visible | Frontend not running | SKIP | none |
| UT-09 | Leadership score row has no regime badge and linkback is unchanged | regression | P1 | No "Regime:" badge on first row; linkback "Backs: Stocks leaderboard →" | Frontend not running | SKIP | none |
| UT-10 | Dashboard regime score and label unchanged after affordance addition | regression | P1 | Regime label "Risk-on", score "76.05" unchanged | Frontend not running | SKIP | none |
| UT-11 | Regime-conditioned evidence is discoverable from Dashboard in one click | ux | P2 | Full journey in 1 click, self-explanatory affordance | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Evidence page loads without errors
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-02 — Dashboard loads without errors
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-03 — Breakout-watch row displays "Regime: Risk-on" badge
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-04 — Breakout-watch row shows correct title and subtitle
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-05 — Breakout-watch linkback reads "Research event-study lab" and navigates to /research/event-study
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-06 — Dashboard Market Regime card contains the Evidence affordance link
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-07 — Dashboard affordance link navigates to the Evidence page
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-08 — Breakout-watch row displays holdout edge, control comparison, and registration date
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-09 — Leadership score row has no regime badge and linkback is unchanged
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-10 — Dashboard regime score and label unchanged after affordance addition
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

### UT-11 — Regime-conditioned evidence is discoverable from Dashboard in one click
**Verdict:** SKIPPED
**Reason:** frontend not running — http://localhost:3255 was unreachable at test execution time

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-30
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-4-evidence/`
