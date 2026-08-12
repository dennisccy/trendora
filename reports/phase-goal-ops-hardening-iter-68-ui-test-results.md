# UI Test Results (merged)

**Date:** 2026-08-12
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-07-06, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-68-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | Backend stays responsive (`GET /api/health` → HTTP 200, no frozen window) throughout a live forward-aggregate warm across every configured horizon; `/backtest` keeps serving from storage; UI readiness/background-compute surfaces stay honest | A real, ambient full 5-horizon `factor_lab_all_warm`-family background-compute job (asof 2026-07-31, dataset r2970-f6580475) was caught in flight and observed via `scripts/qa/poll_health.py`, 240 polls at 1Hz, 07:38:22.469Z–07:42:44.335Z: **240/240 HTTP 200, 0 non-answers**; 9/240 (3.75%) exceeded the relaxed 2.0s ceiling (max 4.19s), reported honestly, never a non-200/timeout. Job completed mid-drill (`outcome:"completed"`, duration_ms 482671). `/backtest` rendered the full forward-test scorecard/leadership cohorts mid-warm (horizons 1/5, 2/5); `/data`'s live panel text matched this agent's own concurrent `GET /api/health` polls exactly, both mid-warm and post-completion | PASS | `reports/qa/goal-ops-hardening-iter-68-evidence/UT-J-07-result.png`, `reports/qa/goal-ops-hardening-iter-68-evidence/j07-health-poll.csv` (+ `.meta.json`) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-12

