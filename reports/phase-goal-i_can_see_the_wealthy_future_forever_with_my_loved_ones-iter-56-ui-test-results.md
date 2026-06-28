# UI Test Results (merged)

**Date:** 2026-06-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-48 | Stocks leaderboard column sorting | happy-path | P1 | Columns sort asc/desc; filter+sort compose; # restores default rank | Leadership sort toggled asc→desc; Ticker sort alphabetical; filter (Technology) applied while sort active — 57 rows in sorted order; # header restored default rank (1:MU, 2:ARM, 3:MRVL) | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-48-result.png` |
| UT-J-50 | As-of date survives every in-app navigation | happy-path | P1 | All in-app hrefs embed `?asof=D` when historical date selected; clean at Latest | Picked 2025-01-02; all sidebar + leaderboard row hrefs confirmed carrying `?asof=2025-01-02`; navigated to /themes and URL showed `?asof=2025-01-02`; back at Latest, all nav links were param-free | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-50-result.png` |
| UT-J-109 | Factor Lab — all-horizon columns, no horizon selector | happy-path | P1 | No horizon selector; all 5 Fwd then 5 MDD columns on both tables; n chips link to samples | No select elements on page; headers: Fwd 1d→5d→10d→20d→60d then MDD 1d→5d→10d→20d→60d on all-factors table; expanded decile sort shows same grouped column order (D1–D10 with n chips); n chip navigated correctly to /research/samples with correct cohort params | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-109-result.png` |
| UT-J-113 | Research hub lab order | smoke | P1 | Labs ordered: Factor Lab → Regime Lab → Market Phase & Severity Lab → Regime×Phase×Factor → Regime×Setup×Pattern → Severity-velocity×Regime → Multi-factor → Event Study → Recovery-Turn Edge → Downtrend Opportunity | Exact order confirmed via link enumeration from `data-testid="research-hub"` / main container; all 10 labs present and deep-linkable | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-113-result.png` |
| UT-J-114 | Research labs column grouping (all Fwd then all MDD) | happy-path | P1 | All four all-horizon lab tables show all forward-return columns first then all max-drawdown columns, never interleaved | Factor Lab: Fwd 1d–60d then MDD 1d–60d (both all-factors table and decile sort); Regime Lab: same order on by-label and regime-score decile tables; Market Phase & Severity Lab: same order on by-phase-label and severity-score decile tables; Regime×Phase×Factor: same order on combination table | PASS | `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-56-evidence/UT-J-114-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-06-29

