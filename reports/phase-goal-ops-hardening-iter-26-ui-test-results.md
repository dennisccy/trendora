# UI Test Results (merged)

**Date:** 2026-07-26
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-06-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-07-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-26-evidence/J-08-verify.png |
| UT-J-09 | Backend discloses its own background-compute activity (regression pass) | regression | P1 | Readiness badge reads plain `Ready` at idle; `/data`'s `BackgroundComputePanel` renders the idle-no-outcome state honestly, and — once a real BCW is triggered and completes — the idle-with-last-outcome state with correct as-of key, `completed` badge (positive styling), and real measured duration, matching the live `/api/health` payload verbatim; process-lifetime disclosure present throughout | All of the above observed live and cross-checked against `GET /api/health` — see steps below | PASS | `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-01-data-page-top-badge.png`, `UT-J-09-readiness-badge.outerHTML.txt`, `UT-J-09-data-panel-completed-lastoutcome.outerHTML.txt`, `UT-J-09-health-snapshot.json` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-26

