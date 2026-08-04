# UI Test Results (merged)

**Date:** 2026-08-04
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-45-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-45-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-45-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-45-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-45-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-45-evidence/J-09-verify.png |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | Backfill of a confirmed-absent historical date (`2019-02-25`) reaches terminal `ok` with a rendered leaderboard within a bounded window; badge stays `ready` throughout | Job (run 281) reached terminal status **`failed`** at t≈4m46s with message `"MemoryError (no message)"` — no snapshot, no scanner run ever created for `2019-02-25`. Backend then became fully unresponsive for 34+ minutes (still ongoing); the readiness badge never reached "Ready" again during that window, stuck on "Checking backend…" instead | FAIL | `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-05-fail.png` |
| UT-J-07 | Heavy aggregates never take the service down (target) | regression | P1 | `GET /api/health` stays HTTP 200 throughout a heavy warm; badge stays `ready`; `/backtest` never blank/frozen | Steps 1/3 partially confirmed pre-outage (badge "Ready", "Backfill gaps" = **2532**, a plausible nearby value to the script's stale `2533` anchor — consistent with the plan's disclosed drift). Step 2 (`/backtest` "n=8991") was not independently re-checked before the outage began. Steps 4-8 could not be executed as scripted because the backend was **already unreachable** for the entire remaining observation window: 60+ consecutive `/api/health` polls over ~34 minutes all returned no response (curl code `000`, 8-60s timeouts) — a 0% pass rate on the health-polling requirement, not the expected 100% | FAIL | `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-07-fail.png` |

## Failed Tests

### UT-J-05 — Aggregates precomputed at ingest, never on the fly (target)

**Verdict:** FAIL
**Failure:** Job (run 281) reached terminal status **`failed`** at t≈4m46s with message `"MemoryError (no message)"` — no snapshot, no scanner run ever created for `2019-02-25`. Backend then became fully unresponsive for 34+ minutes (still ongoing); the readiness badge never reached "Ready" again during that window, stuck on "Checking backend…" instead
**Evidence:** ``reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-05-fail.png``

### UT-J-07 — Heavy aggregates never take the service down (target)

**Verdict:** FAIL
**Failure:** Steps 1/3 partially confirmed pre-outage (badge "Ready", "Backfill gaps" = **2532**, a plausible nearby value to the script's stale `2533` anchor — consistent with the plan's disclosed drift). Step 2 (`/backtest` "n=8991") was not independently re-checked before the outage began. Steps 4-8 could not be executed as scripted because the backend was **already unreachable** for the entire remaining observation window: 60+ consecutive `/api/health` polls over ~34 minutes all returned no response (curl code `000`, 8-60s timeouts) — a 0% pass rate on the health-polling requirement, not the expected 100%
**Evidence:** ``reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-07-fail.png``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-04

