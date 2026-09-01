# Regression Replay — goal-market-compass-iter-38

**Phase:** goal-market-compass-iter-38
**Date:** 2026-09-01
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 3/12 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-38-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "This is the earliest stored session — there is no prior session to compare against." did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date." did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "Strong leader (81.2)" did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "Basis: available" did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "MCD" did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | step 07 expected "Conditions are improving since the prior session (+4.7 regime-score points)." did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "retrospective" did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-38-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "Basis: rebuilt" did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-11-verify.png |
| UT-J-12 | Every frozen selection disposition is true -- the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-38-evidence/J-12-verify.png |
| UT-J-13 | Leadership rotation says which way, shows both directions, and stops repeating What-changed | regression | P1 | journey replays end-to-end; all expects hold | step 07 expected "This is the earliest stored session — there is no prior session to compare rotation against." did not appear | FAIL | reports/qa/goal-market-compass-iter-38-evidence/J-13-verify.png |

## Failed Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties

**Verdict:** FAIL
**Failure:** step 03 expected "This is the earliest stored session — there is no prior session to compare against." did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-02-verify.png`

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause

**Verdict:** FAIL
**Failure:** step 03 expected "This is a retrospective view, reconstructed under the CURRENT selection rule and config — not necessarily what would have rendered live on this date." did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-03-verify.png`

### UT-J-04 — Every next-session candidate explains why, why-not, and what would change it

**Verdict:** FAIL
**Failure:** step 01 expected "Strong leader (81.2)" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-04-verify.png`

### UT-J-05 — Each close freezes one provenance-stamped next-session manifest, exported byte-consistently

**Verdict:** FAIL
**Failure:** step 01 expected "Basis: available" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-05-verify.png`

### UT-J-06 — A frozen manifest never changes — later data, rebuilds, and regeneration are safe

**Verdict:** FAIL
**Failure:** step 01 expected "MCD" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-06-verify.png`

### UT-J-07 — The Today page answers the ten-second read from served values only

**Verdict:** FAIL
**Failure:** step 07 expected "Conditions are improving since the prior session (+4.7 regime-score points)." did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-07-verify.png`

### UT-J-08 — The market surface relocates intact and history never lies

**Verdict:** FAIL
**Failure:** step 03 expected "retrospective" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-08-verify.png`

### UT-J-11 — Incident-bounded clean regeneration of derived state (disposable-clone serving verification)

**Verdict:** FAIL
**Failure:** step 01 expected "Basis: rebuilt" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-11-verify.png`

### UT-J-13 — Leadership rotation says which way, shows both directions, and stops repeating What-changed

**Verdict:** FAIL
**Failure:** step 07 expected "This is the earliest stored session — there is no prior session to compare rotation against." did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-38-evidence/J-13-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-09-01

---

_Reconciliation (2026-09-01): the replay FAIL row(s) above no longer stand in the authoritative merged file (phase-goal-market-compass-iter-38-ui-test-results.md), which is what the goal-evaluator and the achievement gate read. Per journey: **J-04 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive); **J-05 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive); **J-06 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive); **J-07 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive)._
