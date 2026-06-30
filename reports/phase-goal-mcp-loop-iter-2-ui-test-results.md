# Phase goal-mcp-loop-iter-2 — UI Test Results

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/18 tests passed (18 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stock detail page loads without errors | smoke | P1 | Page renders at /stocks/{ticker} with score cards | Frontend not running | SKIP | none |
| UT-02 | "Why proven?" toggle is present on Leadership score card | smoke | P1 | "Why proven?" button visible on Leadership card | Frontend not running | SKIP | none |
| UT-03 | Stocks leaderboard loads with "Proven" badge in Leadership column | smoke | P1 | Leadership column shows "Proven" badge in accent green | Frontend not running | SKIP | none |
| UT-04 | Evidence page loads with leadership_score claim row | smoke | P1 | Evidence page shows leadership_score claim row | Frontend not running | SKIP | none |
| UT-05 | Expand "Why proven?" panel shows OOS test result | happy-path | P1 | Proof panel shows PASS chip, +6.36%, p≈0.0005, n=12297 | Frontend not running | SKIP | none |
| UT-06 | Proof panel shows SPY benchmark control comparison | happy-path | P1 | "vs SPY" row showing +6.36% visible in panel | Frontend not running | SKIP | none |
| UT-07 | Proof panel shows certified claim id and registration date | happy-path | P1 | "leadership_score · registered 2026-06-30" and link visible | Frontend not running | SKIP | none |
| UT-08 | "View backing evidence row →" link navigates to evidence anchor | happy-path | P1 | URL becomes /evidence#signal-leadership_score | Frontend not running | SKIP | none |
| UT-09 | Evidence claim row shows all five required fields | happy-path | P1 | Hypothesis, OOS verdict, SPY control, date, forward-walk all populated | Frontend not running | SKIP | none |
| UT-10 | "Backs: Stocks leaderboard →" link navigates to /stocks | happy-path | P1 | Browser navigates to /stocks with leaderboard visible | Frontend not running | SKIP | none |
| UT-11 | Full round-trip: leaderboard → detail → proof panel → evidence → leaderboard | happy-path | P1 | All navigation steps complete, final URL is /stocks | Frontend not running | SKIP | none |
| UT-12 | Stocks leaderboard "Proven" badge links to /evidence#signal-leadership_score | regression | P1 | Clicking "Proven" badge navigates to evidence anchor | Frontend not running | SKIP | none |
| UT-13 | Entry Quality score card has no "Why proven?" toggle | regression | P1 | No "Why proven?" button on Entry Quality card | Frontend not running | SKIP | none |
| UT-14 | Risk score card has no "Why proven?" toggle | regression | P1 | No "Why proven?" button on Risk card | Frontend not running | SKIP | none |
| UT-15 | Entry Quality and Risk leaderboard badges read "Not yet proven" | regression | P1 | Both badges show "Not yet proven" in muted styling | Frontend not running | SKIP | none |
| UT-16 | "Why proven?" panel collapses on second click | ux | P2 | Panel hides after second toggle click | Frontend not running | SKIP | none |
| UT-17 | "Why proven?" feature discoverable within 2 clicks from leaderboard | ux | P2 | Proof panel reached in exactly 2 clicks | Frontend not running | SKIP | none |
| UT-18 | "Proven" badge visually distinct from "Not yet proven" badges | ux | P2 | Accent green vs muted/gray contrast is immediately apparent | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Stock detail page loads without errors
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-02 — "Why proven?" toggle is present on Leadership score card
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-03 — Stocks leaderboard loads with "Proven" badge in Leadership column
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-04 — Evidence page loads with leadership_score claim row
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-05 — Expand "Why proven?" panel shows OOS test result
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-06 — Proof panel shows SPY benchmark control comparison
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-07 — Proof panel shows certified claim id and registration date
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-08 — "View backing evidence row →" link navigates to evidence anchor
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-09 — Evidence claim row shows all five required fields
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-10 — "Backs: Stocks leaderboard →" link navigates to /stocks
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-11 — Full round-trip: leaderboard → detail → proof panel → evidence → leaderboard
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-12 — Stocks leaderboard "Proven" badge links to /evidence#signal-leadership_score
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-13 — Entry Quality score card has no "Why proven?" toggle
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-14 — Risk score card has no "Why proven?" toggle
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-15 — Entry Quality and Risk leaderboard badges read "Not yet proven"
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-16 — "Why proven?" panel collapses on second click
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-17 — "Why proven?" feature discoverable within 2 clicks from leaderboard
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

### UT-18 — "Proven" badge visually distinct from "Not yet proven" badges
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3255

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-30
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-2-evidence/`
