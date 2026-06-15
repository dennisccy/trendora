# Goal iter-21 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-21
**Date:** 2026-06-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 0/0 tests passed (17 skipped)

---

## Reason for SKIPPED Verdict

The iter-21 spec explicitly excludes browser QA. From the spec:

> **Browser: none required (no served-payload / UI change). Do NOT spend a Chrome MCP session re-smoking unchanged surfaces.**

> **Browser re-QA of J-72/J-75/J-77 served behavior (no served-payload change)** is explicitly listed under **OUT OF SCOPE**.

This iteration is a lean backend-only consolidation with two surgical test-file fixes:
1. `tests/test_db.py` — add `event_study_cache` to the expected-tables set.
2. `tests/test_no_magic_numbers.py` — remove two `0.0` float literals from `_rsp_rank_key` in `research.py`.

No served payload changed. No UI surface changed. The target journeys (J-72, J-75, J-77) and required-still-passing journeys are confirmed via the backend test suite (guard tests + iter-20 research cluster), not via browser automation. The frontend was confirmed reachable (`http://localhost:3835` returned HTTP 200), but browser tests are explicitly excluded from this iteration's scope per the iter spec.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-72 | Research page loads fast — event study cached | target | P1 | Fast independent section loads; byte-identical figures | Not run — browser QA excluded by iter spec (no served-payload change) | SKIP | none |
| UT-J-75 | Forward returns on stock leaderboard and stock detail | target | P1 | Five fwd-return columns on /stocks and matching detail | Not run — browser QA excluded by iter spec (no served-payload change) | SKIP | none |
| UT-J-77 | Research — regime x setup x pattern ranked study | target | P1 | Ranked sortable RSP table; N= chips; Episodes/Pooled/As-of consistent | Not run — browser QA excluded by iter spec (no served-payload change) | SKIP | none |
| UT-J-05 | Stock Detail with explainable scores | regression | P2 | Score breakdowns visible on stock detail page | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-06 | Score consistency across pages | regression | P2 | Same scores on leaderboard and detail | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-18 | One date control (no duplicate) | regression | P2 | Single global as-of switcher only | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-21 | Backtest — leadership cohorts with horizon-linked returns | regression | P2 | Return columns on backtest page | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-25 | Factor Lab — decile sort and rank-IC per factor | regression | P2 | Decile/rank-IC table on /research | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-26 | Factor Lab — multi-factor composite cohort | regression | P2 | Composite cohort table on /research | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-29 | Setup & Pattern research lab — event study | regression | P2 | Event study results on /research | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-32 | Research point-in-time toggle | regression | P2 | As-of vs All-history toggle on /research | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-48 | Stocks leaderboard column sorting | regression | P2 | Sortable columns on /stocks | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-50 | As-of date survives in-app navigation including new tabs | regression | P2 | ?asof param preserved across navigation | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-51 | Every research sample count links to its exact samples | regression | P2 | N= chips link to /research/samples | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-63 | Event study overlap-honest — first-trigger episodes default | regression | P2 | Episodes mode default; Pooled toggle present | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-64 | Research samples table sortable and filterable | regression | P2 | Client-side sort/filter on samples table | Not run — browser QA excluded by iter spec | SKIP | none |
| UT-J-65 | N= chips open samples drill-down in a new tab | regression | P2 | N= chips open /research/samples in new tab | Not run — browser QA excluded by iter spec | SKIP | none |

---

## Skipped Tests

### UT-J-72 — Research page loads fast (event study cached)
**Verdict:** SKIPPED
**Reason:** Iter spec explicitly excludes browser QA: "Browser: none required (no served-payload / UI change). Do NOT spend a Chrome MCP session re-smoking unchanged surfaces." The J-72 cache table addition is a backend test-fixture fix only; byte-identity is verified by `tests/test_iter20_research_cluster.py`, not browser automation.

### UT-J-75 — Forward returns on stock leaderboard and stock detail
**Verdict:** SKIPPED
**Reason:** Iter spec explicitly excludes browser QA. No served payload changed in iter-21. J-75 forward-return columns built in iter-20 remain unchanged; byte-identity confirmed by the backend research cluster tests.

### UT-J-77 — Research — regime x setup x pattern ranked study
**Verdict:** SKIPPED
**Reason:** Iter spec explicitly excludes browser QA: "Browser re-QA of J-72/J-75/J-77 served behavior (no served-payload change)" listed under OUT OF SCOPE. The `_rsp_rank_key` fix is a no-functional-change sort-key refactor; the spec states "A single post-fix re-assertion of J-77 byte-identity via the existing iter-20 cluster test is sufficient."

### UT-J-05 through UT-J-65 (required-still-passing journeys)
**Verdict:** SKIPPED
**Reason:** Iter spec explicitly excludes browser QA for this lean consolidation iteration. No served payload or UI surface changed. Required-still-passing journeys are confirmed via the full backend pytest suite (no served-payload change means no regression path through the UI).

---

## Environment

- **Frontend URL:** http://localhost:3835 (confirmed reachable — HTTP 200)
- **Browser:** Chrome via MCP (not invoked — excluded by iter spec)
- **Test Date:** 2026-06-15
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-21-evidence/` (empty — no tests run)
