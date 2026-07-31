# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-42-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-42-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-42-evidence/J-04-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-42-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-42-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-42-evidence/J-09-verify.png |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | Single-day backfill job accepted, reaches a terminal status, badge stays "Ready" throughout, `/scanner-runs` shows the new date with a populated leaderboard | Job accepted correctly, badge stayed "Ready" — but the job NEVER left `status:"running"` (`dates_done` stuck at 0/1, `last_progress_at` frozen at its own start timestamp) for the full ~10 min observed; a second, independent job on a different date reproduced the same zero-progress stall; the backend then became fully unresponsive, blocking any further steps | FAIL | `reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-05-fail.png` (+ raw job-status JSON quoted in Failed Tests below) |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | `GET /api/health` returns 200 for the whole 60+s warm window; `/backtest` shows real values or the "Refreshing" banner, never down | First 76s of polling during the live warm: 34/34 = 200 (clean). But the SAME warm window later crashed (`background_compute` outcome `"failed"`, `MemoryError` in `forward_aggregates_ingest_cached`/`compute_drawdown_expectations_cached`, `RuntimeError: can't start new thread`), producing real HTTP 500s on `/api/health` (3×), `/api/backtest` (2×), `/api/stocks`, `/api/themes`, `/api/runs`, `/api/methodology`; `/backtest` and `/data` both rendered "Backend unavailable"; `/api/health` then went fully unresponsive (5 consecutive timeouts, HTTP code 000, 10–30s each) for several minutes | FAIL | `reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-07-fail.png` (+ backend log excerpts quoted below) |

## Failed Tests

### UT-J-05 — Aggregates precomputed at ingest, never on the fly (target)

**Verdict:** FAIL
**Failure:** Job accepted correctly, badge stayed "Ready" — but the job NEVER left `status:"running"` (`dates_done` stuck at 0/1, `last_progress_at` frozen at its own start timestamp) for the full ~10 min observed; a second, independent job on a different date reproduced the same zero-progress stall; the backend then became fully unresponsive, blocking any further steps
**Evidence:** ``reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-05-fail.png` (+ raw job-status JSON quoted in Failed Tests below)`

### UT-J-07 — Heavy aggregate warm never takes health/`/backtest` down (target)

**Verdict:** FAIL
**Failure:** First 76s of polling during the live warm: 34/34 = 200 (clean). But the SAME warm window later crashed (`background_compute` outcome `"failed"`, `MemoryError` in `forward_aggregates_ingest_cached`/`compute_drawdown_expectations_cached`, `RuntimeError: can't start new thread`), producing real HTTP 500s on `/api/health` (3×), `/api/backtest` (2×), `/api/stocks`, `/api/themes`, `/api/runs`, `/api/methodology`; `/backtest` and `/data` both rendered "Backend unavailable"; `/api/health` then went fully unresponsive (5 consecutive timeouts, HTTP code 000, 10–30s each) for several minutes
**Evidence:** ``reports/qa/goal-ops-hardening-iter-42-evidence/UT-J-07-fail.png` (+ backend log excerpts quoted below)`

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

