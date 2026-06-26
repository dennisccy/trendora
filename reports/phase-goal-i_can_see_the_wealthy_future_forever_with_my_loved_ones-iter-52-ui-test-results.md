# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/18 tests passed (18 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab loads without blank screen or errors | smoke | P1 | Page heading visible, all-factors table rendered, no error banner | Frontend not running — test not executed | SKIP | none |
| UT-02 | Horizon dropdown is absent from the page | smoke | P1 | No dropdown/select/horizon-picker present anywhere on page | Frontend not running — test not executed | SKIP | none |
| UT-03 | All ten paired Fwd/MDD horizon columns in table header | smoke | P1 | 10 paired columns (Fwd 1d/MDD 1d through Fwd 60d/MDD 60d) visible in header | Frontend not running — test not executed | SKIP | none |
| UT-04 | Rank-IC column shows fixed "(20d)" label | smoke | P1 | Rank-IC column header reads "Rank-IC (20d)", static text | Frontend not running — test not executed | SKIP | none |
| UT-05 | Risk-adjusted column shows fixed "(20d)" label | smoke | P1 | Header includes "(20d)", matches Rank-IC column, static text | Frontend not running — test not executed | SKIP | none |
| UT-06 | Top-decile Fwd 20d cell shows non-empty percentage value | happy-path | P1 | Non-blank percentage with colour coding and N= chip | Frontend not running — test not executed | SKIP | none |
| UT-07 | Top-decile MDD 20d cell shows red-shaded negative percentage | happy-path | P1 | Negative percentage, red shading, not blank | Frontend not running — test not executed | SKIP | none |
| UT-08 | "Fwd 1d" sort: factors reorder descending, NA rows last | happy-path | P1 | Highest Fwd 1d in row 1, NA rows at bottom, sort indicator shown, instant sort | Frontend not running — test not executed | SKIP | none |
| UT-09 | Second click on "Fwd 1d": sort reverses, NA still last | happy-path | P1 | Most negative value in row 1, NA rows still at bottom, indicator flips | Frontend not running — test not executed | SKIP | none |
| UT-10 | Expand factor chevron: D1–D10 decile grid with all-horizon paired columns | happy-path | P1 | Sub-table with 10 decile rows and all 10 paired columns visible | Frontend not running — test not executed | SKIP | none |
| UT-11 | N= chip in D5 "Fwd 5d" cell opens Samples page with matching count | happy-path | P1 | New tab opens to /research/samples with matching observation count | Frontend not running — test not executed | SKIP | none |
| UT-12 | Backend-unavailable shows error banner, not blank screen | error | P2 | Error message visible, app shell present, no blank screen | Frontend not running — test not executed | SKIP | none |
| UT-13 | D1 MDD 20d cell shaded deeper red than D10 | ux | P2 | D1 has more intense red background than D10 | Frontend not running — test not executed | SKIP | none |
| UT-14 | "Factor range" column appears once in expanded decile grid | ux | P2 | Exactly one "Factor range" column in decile sub-grid with values in each row | Frontend not running — test not executed | SKIP | none |
| UT-15 | Hover on "Fwd 5d" cell shows tooltip with that horizon's factor range | ux | P2 | Tooltip appears with horizon-specific factor value range | Frontend not running — test not executed | SKIP | none |
| UT-16 | As-of toggle updates N= chips globally; no second date picker | regression | P1 | N= chips change after toggling date; no second date control in page body | Frontend not running — test not executed | SKIP | none |
| UT-17 | All catalog factors still appear in table after changes | regression | P1 | At least 11 factor rows visible, all named, all with data | Frontend not running — test not executed | SKIP | none |
| UT-18 | Factor Lab navigation link reachable from main app menu | ux | P2 | "Factor Lab" link visible in nav, clicking navigates to /research/factor-lab | Frontend not running — test not executed | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

All 18 tests were skipped because the frontend was not running at http://localhost:3255 at the time of this QA run.

### UT-01 — Factor Lab loads without blank screen or errors
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — Horizon dropdown is absent from the page
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — All ten paired Fwd/MDD horizon columns in table header
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Rank-IC column shows fixed "(20d)" label
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Risk-adjusted column shows fixed "(20d)" label
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Top-decile Fwd 20d cell shows non-empty percentage value
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Top-decile MDD 20d cell shows red-shaded negative percentage
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — "Fwd 1d" sort: factors reorder descending, NA rows last
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Second click on "Fwd 1d": sort reverses, NA still last
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Expand factor chevron: D1–D10 decile grid with all-horizon paired columns
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — N= chip in D5 "Fwd 5d" cell opens Samples page with matching count
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Backend-unavailable shows error banner, not blank screen
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — D1 MDD 20d cell shaded deeper red than D10
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — "Factor range" column appears once in expanded decile grid
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — Hover on "Fwd 5d" cell shows tooltip with that horizon's factor range
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-16 — As-of toggle updates N= chips globally; no second date picker
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-17 — All catalog factors still appear in table after changes
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-18 — Factor Lab navigation link reachable from main app menu
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-27
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52-evidence/`
