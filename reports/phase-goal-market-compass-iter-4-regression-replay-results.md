# Regression Replay — goal-market-compass-iter-4

**Phase:** goal-market-compass-iter-4
**Date:** 2026-08-20
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 3/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "Consumer Discretionary" did not appear | FAIL | reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-4-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-4-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-4-evidence/J-04-verify.png |

## Failed Tests

### UT-J-01 — Sector attribution is honest and near-complete on new runs

**Verdict:** FAIL
**Failure:** step 03 expected "Consumer Discretionary" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-4-evidence/J-01-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-20

---

_Reconciliation (2026-08-20): the replay FAIL row(s) above no longer stand in the authoritative merged file (phase-goal-market-compass-iter-4-ui-test-results.md), which is what the goal-evaluator and the achievement gate read. Per journey: **J-01 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive)._
