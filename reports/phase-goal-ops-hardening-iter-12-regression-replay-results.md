# Regression Replay — goal-ops-hardening-iter-12

**Phase:** goal-ops-hardening-iter-12
**Date:** 2026-07-22
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 15000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-12-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-12-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-12-evidence/J-05-verify.png |

## Failed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 15000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-12-evidence/J-01-verify.png`

### UT-J-03 — No per-run range cap

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-12-evidence/J-03-verify.png`

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-12-evidence/J-05-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-22

---

_Reconciliation (2026-07-22): the replay FAIL row(s) for J-01 J-03 J-05 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-ops-hardening-iter-12-ui-test-results.md; the FAIL row(s) above are superseded._
