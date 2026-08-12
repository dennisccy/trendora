# Regression Replay — goal-ops-hardening-iter-70

**Phase:** goal-ops-hardening-iter-70
**Date:** 2026-08-12
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 0/7 journeys passed (0 skipped, 7 blocked — backend unreachable)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |
| UT-J-03 | J-03 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |
| UT-J-04 | J-04 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |
| UT-J-05 | J-05 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |
| UT-J-06 | J-06 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |
| UT-J-08 | J-08 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |
| UT-J-09 | J-09 | regression | P1 | backend answers GET http://localhost:8255/api/health with HTTP 200 before replay | backend unreachable: GET http://localhost:8255/api/health did not answer 200 | BLOCKED | none |

## Blocked Tests

_Not a journey failure — the backend was unreachable before this journey (or any other in this run) was ever replayed. Distinct from FAIL: FAIL means the journey's own assertions did not hold; BLOCKED means they were never checked._

### UT-J-01 — J-01

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

### UT-J-03 — J-03

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

### UT-J-04 — J-04

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

### UT-J-05 — J-05

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

### UT-J-06 — J-06

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

### UT-J-08 — J-08

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

### UT-J-09 — J-09

**Verdict:** BLOCKED
**Reason:** backend unreachable: GET http://localhost:8255/api/health did not answer 200

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-12
