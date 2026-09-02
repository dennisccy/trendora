# Regression Replay — goal-market-compass-iter-40

**Phase:** goal-market-compass-iter-40
**Date:** 2026-09-02
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 8/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform click: Locator.wait_for: Timeout 8000ms exceeded. | FAIL | reports/qa/goal-market-compass-iter-40-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-04-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-08-verify.png |
| UT-J-12 | Every frozen selection disposition is true -- the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-12-verify.png |
| UT-J-13 | Leadership rotation says which way, shows both directions, and stops repeating What-changed | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-13-verify.png |
| UT-J-14 | "Not priority" names its real reason — the why-not block stops claiming a qualifier pass it never checked, and the actually-near-miss names come back | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-40-evidence/J-14-verify.png |

## Failed Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties

**Verdict:** FAIL
**Failure:** step 02 could not perform click: Locator.wait_for: Timeout 8000ms exceeded.
**Evidence:** `reports/qa/goal-market-compass-iter-40-evidence/J-02-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-09-02

---

_Reconciliation (2026-09-02): the replay FAIL row(s) above no longer stand in the authoritative merged file (phase-goal-market-compass-iter-40-ui-test-results.md), which is what the goal-evaluator and the achievement gate read. Per journey: **J-02 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive)._
