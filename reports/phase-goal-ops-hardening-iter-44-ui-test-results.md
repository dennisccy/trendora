# UI Test Results (merged)

**Date:** 2026-08-03
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-44-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-44-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-44-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-44-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-44-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-44-evidence/J-09-verify.png |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | A backfill on a confirmed-unsnapshotted date (2019-02-26) creates a snapshot quickly (fast scan stage), badge stays Ready throughout, `/scanner-runs` shows the new date with a leaderboard | Job entered `running`, `dates_done` stayed `0/1` for the entire ~10 min it was live, then the job record shows `status: failed`, `snapshots_created: 0`, message unchanged generic text ("backfill: 0 snapshots over 1 dates, 0 forward returns"); no `/scanner-runs` row for 2019-02-26 was ever created; badge went from Ready to stuck on "Checking backend…" during the concurrent outage | FAIL | `reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-05-job-failed.png`, `UT-J-07-outage-checking-backend.png`, `UT-J-05-J-07-job-and-outage-timeline.csv` |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | Steps 1-3 anchors render; `GET /api/health` returns 200 throughout the warm (rescoped ≤2s budget); badge stays `ready`; `/backtest` renders promptly (normal or "Refreshing" banner), never blank/frozen | Steps 1-3 anchors rendered (with the caveat that the two golden numeric anchors "n=8878"/"3508" have drifted with dataset growth — see Notes). During the warm: 84/84 clean baseline polls were 200 (max 1.756s) BEFORE the incident, then the backend went **fully unresponsive for 21m26s** — `GET /api/health` timed out on 51 consecutive independent polls (5s timeout each) plus this tester's own direct `curl` calls (one hung >120s); badge stuck on "Checking backend…"/loading; the process required a manual `SIGKILL` after `SIGTERM` failed to exit it within its configured 120s graceful window | FAIL | `reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-07-outage-checking-backend.png`, `UT-J-05-job-failed.png`, `UT-J-07-health-poll-baseline.csv`, `UT-J-05-J-07-job-and-outage-timeline.csv` |

## Failed Tests

### UT-J-05 — Aggregates precomputed at ingest, never on the fly (target)

**Verdict:** FAIL
**Failure:** Job entered `running`, `dates_done` stayed `0/1` for the entire ~10 min it was live, then the job record shows `status: failed`, `snapshots_created: 0`, message unchanged generic text ("backfill: 0 snapshots over 1 dates, 0 forward returns"); no `/scanner-runs` row for 2019-02-26 was ever created; badge went from Ready to stuck on "Checking backend…" during the concurrent outage
**Evidence:** ``reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-05-job-failed.png`, `UT-J-07-outage-checking-backend.png`, `UT-J-05-J-07-job-and-outage-timeline.csv``

### UT-J-07 — Heavy aggregate warm never takes health/`/backtest` down (target)

**Verdict:** FAIL
**Failure:** Steps 1-3 anchors rendered (with the caveat that the two golden numeric anchors "n=8878"/"3508" have drifted with dataset growth — see Notes). During the warm: 84/84 clean baseline polls were 200 (max 1.756s) BEFORE the incident, then the backend went **fully unresponsive for 21m26s** — `GET /api/health` timed out on 51 consecutive independent polls (5s timeout each) plus this tester's own direct `curl` calls (one hung >120s); badge stuck on "Checking backend…"/loading; the process required a manual `SIGKILL` after `SIGTERM` failed to exit it within its configured 120s graceful window
**Evidence:** ``reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-07-outage-checking-backend.png`, `UT-J-05-job-failed.png`, `UT-J-07-health-poll-baseline.csv`, `UT-J-05-J-07-job-and-outage-timeline.csv``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-03

