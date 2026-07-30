# Regression Replay — goal-ops-hardening-iter-38

**Phase:** goal-ops-hardening-iter-38
**Date:** 2026-07-30
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 1/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 15000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-38-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-38-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "provider: seed" did not appear | FAIL | reports/qa/goal-ops-hardening-iter-38-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-38-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-38-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | step 01 expected "Forward-tested evidence" did not appear | FAIL | reports/qa/goal-ops-hardening-iter-38-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform click: Locator.click: Timeout 10000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-38-evidence/J-09-verify.png |

## Failed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 15000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/J-01-verify.png`

### UT-J-03 — No per-run range cap

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/J-03-verify.png`

### UT-J-04 — Non-blocking boot with visible status

**Verdict:** FAIL
**Failure:** step 01 expected "provider: seed" did not appear
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/J-04-verify.png`

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/J-05-verify.png`

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request

**Verdict:** FAIL
**Failure:** step 01 expected "Forward-tested evidence" did not appear
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/J-08-verify.png`

### UT-J-09 — Disclose in-flight background-compute activity (badge + /data panel)

**Verdict:** FAIL
**Failure:** step 02 could not perform click: Locator.click: Timeout 10000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/J-09-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-30

---

_Reconciliation (2026-07-30): the replay FAIL row(s) for J-01 J-03 J-08 J-09 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-ops-hardening-iter-38-ui-test-results.md; the FAIL row(s) above are superseded._
