# Regression Replay — goal-market-compass-iter-6

**Phase:** goal-market-compass-iter-6
**Date:** 2026-08-20
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 2/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-6-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "vs 2026-08-11 (1 day ago)" did not appear | FAIL | reports/qa/goal-market-compass-iter-6-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "Market regime is Risk-on (73.2/100); market phase is Expansion with calm conditions (severity 25.8/100)." did not appear | FAIL | reports/qa/goal-market-compass-iter-6-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-6-evidence/J-04-verify.png |

## Failed Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties

**Verdict:** FAIL
**Failure:** step 01 expected "vs 2026-08-11 (1 day ago)" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-6-evidence/J-02-verify.png`

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause

**Verdict:** FAIL
**Failure:** step 01 expected "Market regime is Risk-on (73.2/100); market phase is Expansion with calm conditions (severity 25.8/100)." did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-6-evidence/J-03-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-20

---

_Reconciliation (2026-08-20): the replay FAIL row(s) above no longer stand in the authoritative merged file (phase-goal-market-compass-iter-6-ui-test-results.md), which is what the goal-evaluator and the achievement gate read. Per journey: **J-02 -> SKIP** (NOT re-verified — the replay FAIL is superseded, not disproven); **J-03 -> SKIP** (NOT re-verified — the replay FAIL is superseded, not disproven)._
