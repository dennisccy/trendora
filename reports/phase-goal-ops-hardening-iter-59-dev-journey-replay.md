# Regression Replay — goal-ops-hardening-iter-59

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2010-11-15 must have 0 snapshot rows before this runs; re-verify and rotate if a prior lane consumed it), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-dev-evidence/J-05-verify.png |
| UT-J-07 | Heavy aggregates never take the service down — regression-hardening golden reading GET /api/health-backed attributes and persisted data_provider_runs fields, never a bare page-title/heading match | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-59-dev-evidence/J-07-verify.png |

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-11
