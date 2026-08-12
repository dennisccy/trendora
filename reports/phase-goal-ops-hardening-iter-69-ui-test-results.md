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
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-07-07, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-69-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down (steps 1-2, per TESTING REQUIREMENTS scope) | regression/resilience | P1 | While a forward-aggregate warm runs across all 5 configured horizons in the live backend process, every 1 Hz `GET /api/health` poll answers HTTP 200 (no frozen/unresponsive window), and `GET /api/backtest` continues serving stored evidence throughout — no crash, no block. | A genuine forward-aggregate warm was live-observed in progress on the inherited backend (`asof_key=2026-07-31`, `dataset_version=r2972-f6583415`, all 5 configured horizons `[1,5,10,20,60]`, progressing 0/5→1/5→3/5 across the session). 120 polls of `GET http://localhost:8255/api/health` at 1 Hz: **120/120 HTTP 200**, zero non-answers, max elapsed 4.93s (6/120 over the 2.0s relaxed background-compute ceiling — reported as measured, not smoothed). `/` showed "Ready" + "background compute running (1)" (honest disclosure, not frozen). `/backtest` loaded fully mid-warm: the per-horizon "Forward-test scorecard" correctly rendered its own honest "No elapsed forward window for this date yet" empty state (every horizon row "— n=0 ⚠", latest as-of has no elapsed post-snapshot bars — this is correct behavior, not a bug), while the separate "Forward-tested evidence (expanding window)" section below it was fully populated from storage (2,911 snapshots, n=1,257,974). `TRENDORA_HEALTH_WATCHDOG` could **not** be armed for this lane — see Known Constraint below. | PASS | `reports/qa/goal-ops-hardening-iter-69-evidence/UT-J-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-12

