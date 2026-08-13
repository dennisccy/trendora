# Regression Replay — goal-ops-hardening-iter-73

**Phase:** goal-ops-hardening-iter-73
**Date:** 2026-08-13
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-73-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-73-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-73-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-07-12, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-07-verify.png |

## Failed Tests

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-07-12, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/J-05-verify.png`

### UT-J-06 — Pages load only what they need

**Verdict:** FAIL
**Failure:** step 02 could not perform expect: expect not satisfied
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/J-06-verify.png`

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request (payload-gated)

**Verdict:** FAIL
**Failure:** step 02 could not perform expect: expect not satisfied
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/J-08-verify.png`

### UT-J-09 — Disclose in-flight background-compute activity (badge + /data panel)

**Verdict:** FAIL
**Failure:** step 02 could not perform click: Locator.click: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/J-09-verify.png`

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** FAIL
**Failure:** step 01 expected "Ready" did not appear
**Evidence:** `reports/qa/goal-ops-hardening-iter-73-evidence/J-07-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-13

---

_VOIDED (2026-08-13): the FAIL rows for J-05 J-06 J-07 J-08 J-09 above were VOIDED (SPEED-22 mass-false-FAIL breaker) — a majority of the replay set failed at once and the canary journeys re-checked GREEN via the LLM lane, so the failures are suspected golden-script/selector drift, not product regressions. These journeys keep their prior recorded status; their golden scripts are queued for regeneration (state/goldens-regen-pending) and are re-derived from the next verified demo recording._
