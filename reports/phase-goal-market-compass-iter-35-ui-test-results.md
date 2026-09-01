# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-35-evidence/J-08-verify.png |
| UT-J-12 | Every frozen selection disposition is true — the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression/correctness | P1 | At the frontier as-of (`2026-08-12`, latest manifest v8), the Next-session focus section's candidate count, the summary's focus-count sentence, and `GET /api/compass`'s `selection.candidates` length all agree; the manifest strip's audit table shows zero `comparison_cohort` rows with `leadership_score >= 80.0` labelled `below_selection_floor` (all such rows show `excluded_by_cap`); a candidate that misses an advisory qualifier (entry or risk) renders a caution citing the threshold and actual value, never a false "clears" reason | Verified via Chrome MCP against `http://localhost:3255/`: summary sentence reads "10 names worth monitoring next session."; `GET /api/compass` (port 8255, same backend) returns `selection.candidates` length 10 and `disposition_tally: {below_selection_floor: 502, excluded_by_cap: 27}` (502+27+10=539, matches goal file's predicted partition); HPE (leadership 92.71) renders as a candidate with checklist row `entry_min_score` tagged `gating: false`/verdict `Miss` and caution text "ENTRY_QUALITY_QUALIFIER: Entry Quality score 21.5 is below the 70.0 qualifier (Weak entry) -- advisory only; Leadership alone determines candidacy."; CRL renders as a candidate despite failing BOTH entry and risk qualifiers; opened the "Audit table — comparison cohort (529) + near-threshold shadow (25)" details element and, via DOM query over all 529 rendered rows, confirmed 0 rows have `leadership >= 80.0` AND disposition text containing "below"; DXCM (leadership 85.0) shows disposition "excluded by cap"; belowFloorCount 502 / excludedByCapCount 27 exactly match the API tally | PASS | `reports/qa/goal-market-compass-iter-35-evidence/UT-J-12-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01

