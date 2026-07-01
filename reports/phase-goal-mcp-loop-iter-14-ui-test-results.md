# UI Test Results (merged)

**Date:** 2026-07-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | Multi-factor combination certified edge on Combination lab + Evidence | happy-path | P1 | "Proven" badge for rs_spy_3m×high_proximity, deep-link lands 6th /evidence row with all standard fields, byte-match edge +4.69%/p=0.0009995 | All verified: badge data-proven=true, anchor id resolved, element in viewport, all fields present, byte-match confirmed, no backend-unavailable pill, 0 combination badges on /stocks | PASS | `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-07-fullpage.png`, `reports/qa/goal-mcp-loop-iter-14-evidence/UT-J-08-12-evidence-fullpage.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-01

