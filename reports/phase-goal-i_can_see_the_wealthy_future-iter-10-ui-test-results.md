# Phase goal-i_can_see_the_wealthy_future-iter-10 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running -->

**Overall:** 0/15 tests passed (15 skipped)

> The browser-qa-phase harness reported the frontend as **NOT available** at
> `http://localhost:3835`. Per the browser-qa-agent precondition check
> ("If not running and no auto-start capability: write all tests as SKIPPED
> with reason 'frontend not running'"), all 15 UI test cases are marked
> **SKIPPED** and no browser automation was attempted. SKIPPED is distinct
> from FAIL — nothing was found broken; the UI simply could not be exercised
> because its service was down. The iteration-10 `/backtest` workspace,
> sidebar nav entry, and System Health refactor therefore remain
> **unverified by browser QA** and must be re-tested once the frontend is up.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Backtest page loads without errors | smoke | P1 | `/backtest` renders heading, as-of picker, survivorship card, scorecard table; no error overlay | Not executed — frontend not running | SKIP | none |
| UT-02 | Backtest is discoverable from the sidebar | ux | P1 | "Backtest" nav item (flask icon) between Scanner Runs and System Health; click routes to `/backtest` | Not executed — frontend not running | SKIP | none |
| UT-03 | As-of scan summary renders (full-window historical date) | happy-path | P1 | Regime card, candidate counts, top sectors/themes, ranked cohort all render for an old date | Not executed — frontend not running | SKIP | none |
| UT-04 | Forward-test scorecard shows numeric returns (full-window date) | happy-path | P1 | 5 horizon rows (1/5/10/20/60d) with numeric Cohort/excess/control returns + `n=` | Not executed — frontend not running | SKIP | none |
| UT-05 | Page-local date picker time-travels independently of global switcher | happy-path | P1 | Selecting historical D updates as-of badge + scan summary + scorecard, driven by page picker | Not executed — frontend not running | SKIP | none |
| UT-06 | As-of badge reflects historical vs latest | ux | P2 | Badge toggles "(latest)" clock vs amber "(historical)" history icon on selection | Not executed — frontend not running | SKIP | none |
| UT-07 | Recent/latest date shows honest NA, never fabricated numbers | validation | P1 | Un-elapsed horizons show "—" with `n=0`; empty-state copy when all NA; no fabricated % | Not executed — frontend not running | SKIP | none |
| UT-08 | Low-sample figures flagged with ⚠ warn token | validation | P2 | Cells with `n < min_sample` show amber ⚠; caption states threshold; tooltip on hover | Not executed — frontend not running | SKIP | none |
| UT-09 | Survivorship-bias banner is visible and honest | ux | P2 | Warn-styled "Survivorship bias" card with limitation text near top of page | Not executed — frontend not running | SKIP | none |
| UT-10 | Backend-unavailable degrades safely, no fabricated figures | error | P2 | With backend down, "Backend unavailable" card shows; no scorecard/fabricated numbers; no blank crash | Not executed — frontend not running | SKIP | none |
| UT-11 | Scan summary degrades when only dashboard endpoint fails | error | P3 | Scorecard still renders; scan-summary shows targeted "… unavailable" cards | Not executed — frontend not running | SKIP | none |
| UT-12 | Scan-summary values match canonical pages for the same date | regression | P2 | Regime/score, Actionable count, #1 sector on `/backtest` match `/` and `/sectors` for date D | Not executed — frontend not running | SKIP | none |
| UT-13 | System Health return figures render identically after shared-helper refactor | regression | P1 | `/system-health` forward-return %, colors, `n=`, ⚠ flags unchanged vs pre-refactor | Not executed — frontend not running | SKIP | none |
| UT-14 | Global top-bar as-of switcher did not regress | regression | P1 | Global switcher still time-travels `/` and `/stocks`; does not alter `/backtest` picker | Not executed — frontend not running | SKIP | none |
| UT-15 | Scorecard table horizontally scrollable on narrow viewports | ux | P3 | All 9 columns reachable via horizontal scroll within table container at ~1024px | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None. No test was executed (frontend not running).

---

## Failed Tests

None. No test was executed, so there are no failures. (A SKIPPED verdict is
not a FAIL — nothing was found broken; the test environment was simply
unavailable.)

---

## Skipped Tests

All 15 test cases were skipped for the same reason: **frontend not running**
(service unavailable at `http://localhost:3835`; the browser-qa-phase harness
reported the frontend as NOT available and there was no auto-start capability
in this run). No Chrome MCP automation was attempted.

### UT-01 — Backtest page loads without errors
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — Backtest is discoverable from the sidebar
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — As-of scan summary renders for a full-window historical date
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Forward-test scorecard shows numeric returns for a full-window date
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Page-local date picker time-travels independently of the global switcher
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — As-of badge reflects historical vs latest
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Recent/latest date shows honest NA, never fabricated numbers
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — Low-sample figures are flagged with the ⚠ warn token
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Survivorship-bias banner is visible and honest
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Backend-unavailable degrades safely, no fabricated figures
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — Scan summary degrades when only dashboard endpoint fails
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — Scan-summary values match canonical pages for the same date
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — System Health return figures render identically after the shared-helper refactor
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — Global top-bar as-of switcher did not regress
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — Scorecard table is horizontally scrollable on narrow viewports
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3835 — **NOT available** (reported down by `browser-qa-phase.sh`; frontend log: `/tmp/browser-qa-frontend-8835.log`)
- **Backend URL:** http://localhost:8835 (managed by the harness; health: `/health`; log: `/tmp/browser-qa-backend-8835.log`) — not exercised via the browser since the frontend was down
- **Browser:** Chrome via MCP — not launched (precondition not met)
- **Test Date:** 2026-05-31
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-10-evidence/` (no screenshots captured — no live UI states to capture)

---

## Recommendation

Re-run browser QA once the frontend is confirmed up at
`http://localhost:3835` (inspect `/tmp/browser-qa-frontend-8835.log` for the
startup-failure cause). When the service is healthy, execute UT-01..UT-15 and
replace this SKIPPED report with PASS/FAIL results plus focused evidence
screenshots (per the test plan: distinct, md5-checked captures of the
scorecard panel for a full-window date and a separate partial/NA date).

**Note for the evaluator (per the iteration-10 spec, NOTES → "Chronic runner-script debt"):**
the dedicated browser-qa has SKIPPED on the HTTP-000/CORS/frontend-down flap
for several consecutive iterations — this is a known runner-owner issue, not a
product defect. If browser-qa SKIPs again, the spec directs the evaluator to
reconcile J-14 from the on-disk QA evidence PNGs (if any), the unit/API
proofs, and direct source reads, rather than treating this SKIP as a J-14
failure.
