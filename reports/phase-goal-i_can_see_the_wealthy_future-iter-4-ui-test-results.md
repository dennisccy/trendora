# Phase goal-i_can_see_the_wealthy_future-iter-4 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future-iter-4
**Date:** 2026-05-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: Frontend not running -->

**Overall:** 0/13 tests passed (13 skipped)

**Reason for SKIPPED:** The frontend at `http://localhost:3836` is not running. A precondition
check (`curl -s -o /dev/null -w "%{http_code}" http://localhost:3836`) returned `000` (no
response / connection refused). With no frontend to drive, no browser-based UI tests can be
executed. Per the browser-qa-agent precondition rule, all test cases are recorded as SKIPPED
rather than FAIL — a non-running service is not a product defect.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Stock Detail loads | smoke | P1 | Page renders heading "NVDA", subtitle, back link, and four cards with no error/blank | Not executed — frontend not running | SKIP | none |
| UT-02 | Candle chart + MA + volume | happy-path | P1 | PriceChart paints candles, 4 MA lines, volume histogram, and legend | Not executed — frontend not running | SKIP | none |
| UT-03 | Theme chips → /themes | happy-path | P1 | Accent theme chips render and clicking one navigates to `/themes` | Not executed — frontend not running | SKIP | none |
| UT-04 | Concrete invalidation note | happy-path | P1 | Note reads "Invalid below the 50-DMA at $<level>" in muted text with a real value | Not executed — frontend not running | SKIP | none |
| UT-05 | Invalidation NA state | validation | P2 | Note reads "Invalidation level NA — insufficient history" in amber; no fabricated value | Not executed — frontend not running | SKIP | none |
| UT-06 | Empty-theme state | validation | P2 | "Not a member of any tracked theme." in muted grey; no empty chips | Not executed — frontend not running | SKIP | none |
| UT-07 | Backend-down error card | error | P2 | Red "Backend unavailable" card; no fabricated prices/invalidation; no blank screen | Not executed — frontend not running | SKIP | none |
| UT-08 | Chart-only error, scores intact | error | P2 | Amber "Chart unavailable" box inside chart card; score cards still render | Not executed — frontend not running | SKIP | none |
| UT-09 | Empty price-history state | error | P3 | "No price history is available for <TICKER>." in muted text; no blank canvas | Not executed — frontend not running | SKIP | none |
| UT-10 | Scores match leaderboard (J-06) | regression | P1 | Three score cards match leaderboard bucket letters and 0–100 values exactly | Not executed — frontend not running | SKIP | none |
| UT-11 | Unknown-ticker state | regression | P1 | Amber "Unknown ticker" card; leaderboard link navigates to `/stocks` | Not executed — frontend not running | SKIP | none |
| UT-12 | Loading skeleton | ux | P3 | Pulsing grey placeholder cards appear before content, then replaced | Not executed — frontend not running | SKIP | none |
| UT-13 | Discoverable from leaderboard | ux | P3 | Leader row is clickable and reaches full detail view in one click | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — all tests skipped (frontend not running).

---

## Failed Tests

None — all tests skipped (frontend not running). No FAIL is recorded because a non-running
frontend is an environment condition, not a product defect.

---

## Skipped Tests

### UT-01 — Stock Detail page loads without errors (smoke)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-02 — User can study the price candle chart with MA overlays and volume (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-03 — Theme chips render and navigate to the Themes page (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-04 — Concrete invalidation level renders verbatim (happy path)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-05 — Invalidation NA state on short history (validation / no-fabrication)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-06 — Empty-theme honest state (validation)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-07 — Chart error state when backend is down (error)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-08 — Chart-only error state, scores intact (error)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-09 — Empty price-history state (error / honest)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-10 — Three explainable scores still render and match the leaderboard (regression, J-06 guard)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-11 — Unknown-ticker state still works (regression)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-12 — Loading skeleton appears before content (ux)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

### UT-13 — Feature is discoverable from the leaderboard (ux)
**Verdict:** SKIPPED
**Reason:** frontend not running (`http://localhost:3836` returned HTTP `000` / no response)

---

## Environment

- **Frontend URL:** http://localhost:3836 — **NOT running** (precondition check returned HTTP `000`)
- **Backend URL:** http://localhost:8835 (`/health` returned HTTP `404` during the check; not exercised — no frontend to drive)
- **Browser:** Chrome via MCP — not used (no frontend to test against)
- **Test Date:** 2026-05-30
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future-iter-4-evidence/` (empty — no browser tests executed)

---

## Notes

- This run was dispatched with the frontend explicitly marked unavailable; the precondition
  `curl` check independently confirmed it (HTTP `000`).
- No source files were modified and no browser automation was attempted, per the
  browser-qa-agent rules.
- The six P1 gating tests (UT-01, UT-02, UT-03, UT-04, UT-10, UT-11) could not be exercised.
  Because they are SKIPPED rather than FAILED, this report does not assert a PASS; the verdict
  is SKIPPED so downstream gates can decide whether to re-run with a live frontend.
