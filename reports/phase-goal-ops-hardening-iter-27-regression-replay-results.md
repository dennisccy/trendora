# Regression Replay — goal-ops-hardening-iter-27

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 4/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-27-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-27-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-27-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "DEGRADED" did not appear | FAIL | reports/qa/goal-ops-hardening-iter-27-evidence/J-06-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-27-evidence/J-09-verify.png |

## Failed Tests

### UT-J-06 — Pages load only what they need

**Verdict:** FAIL
**Failure:** step 01 expected "DEGRADED" did not appear
**Evidence:** `reports/qa/goal-ops-hardening-iter-27-evidence/J-06-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-26
