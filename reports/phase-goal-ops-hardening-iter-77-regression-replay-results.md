# Regression Replay — goal-ops-hardening-iter-77

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 3/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-77-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-77-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-08-11, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-77-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform expect: expect not satisfied | FAIL | reports/qa/goal-ops-hardening-iter-77-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform expect: expect not satisfied | FAIL | reports/qa/goal-ops-hardening-iter-77-evidence/J-08-verify.png |

## Failed Tests

### UT-J-06 — Pages load only what they need

**Verdict:** FAIL
**Failure:** step 02 could not perform expect: expect not satisfied
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/J-06-verify.png`

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request (payload-gated)

**Verdict:** FAIL
**Failure:** step 02 could not perform expect: expect not satisfied
**Evidence:** `reports/qa/goal-ops-hardening-iter-77-evidence/J-08-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-13

---

_Reconciliation (2026-08-13): the replay FAIL row(s) above no longer stand in the authoritative merged file (phase-goal-ops-hardening-iter-77-ui-test-results.md), which is what the goal-evaluator and the achievement gate read. Per journey: **J-06 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive); **J-08 -> PASS** (re-confirmed live by the LLM lane — the replay FAIL was a golden-script false positive)._
