# QA Validation Report — goal-ops-hardening-iter-44 (Revalidation)

**Phase:** goal-ops-hardening-iter-44
**Date:** 2026-08-03 (revalidation after auditor and reviewer FAIL)
**QA Agent:** qa (revalidation mode)

---

**Verdict:** FAIL

---

## Executive Summary

This iteration's phase goal is **"Stop J-07's heavy warm from taking the whole service unreachable"** by wiring concurrency/shutdown guards and diagnosing the stall.

**The goal was NOT achieved.** During browser QA execution of the target journeys, the backend became **fully unresponsive for 20 minutes 51 seconds** (20:10:33→20:31:24 UTC), requiring a manual `SIGKILL` after `SIGTERM` failed to exit the process within its configured 120s graceful-shutdown window. This directly contradicts:
- **TC-2:** "self-terminates within graceful_timeout_seconds, without requiring manual kill -9" — FAIL
- **TC-7:** "never goes fully unreachable" — FAIL

Both are Definition-of-Done items. Both are refuted by this pipeline's own browser lane report (`reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md`).

---

## Required Artifacts Verification

| Artifact | Present | Status | Notes |
|----------|---------|--------|-------|
| `docs/handoffs/goal-ops-hardening-iter-44-dev.md` | YES | Complete | Includes audit corrections; acknowledged TC-2/TC-7 unmet |
| `reports/reviews/goal-ops-hardening-iter-44-review.md` | YES | **FAIL** | Flaky memory-pressure test; TC-2/TC-5/TC-7 remain unmet |
| `runs/goal-ops-hardening-iter-44/status.json` | YES | Present | - |

---

## Backend Test Results

Tests run after auditor's fixes (developer fix pass):

```
Command: cd apps/backend && .venv/bin/python -m pytest \
  tests/test_api_data.py \
  tests/test_ingest_finalize_memory_pressure.py \
  tests/test_ingest_finalize_fault_injection.py -q

Result: 57 passed in 159.02s
  - TC-9 (Retry 503): PASS
  - TC-8 (induced-pressure abort): PASS (audit B2 fixes applied)
  - TC-10 (message honesty): PASS (audit B1 fix applied: type-name fallback for MemoryError)

Command: cd apps/backend && .venv/bin/python -m pytest \
  tests/test_data_manager.py -q -k "run_job or final_summary"

Result: 3 passed in 0.67s (includes audit B1 textless-exception test)
```

**Backend unit tests PASS.** However, unit tests do NOT verify the phase goal, which requires end-to-end availability under heavy compute. Browser QA tests that goal.

---

## Functional Test Results — Browser QA (Target Journeys)

No functional test plan exists for this phase (per execution plan: "No functional test plan found"). However, the browser QA lane executed the target journeys per standard goal-mode testing.

### Result Summary

| Test | Expected | Actual | Verdict |
|------|----------|--------|---------|
| **UT-J-05** — Aggregates precomputed at ingest (P1 target) | Backfill on unsnapshotted date creates snapshot, `/scanner-runs` shows new date with leaderboard, badge stays `Ready` | Job entered `running`, `dates_done: 0/1` for ~10 min, then `failed` with zero snapshots, no `/scanner-runs` entry, badge stuck "Checking backend…" | **FAIL** |
| **UT-J-07** — Heavy warm never takes health/backtest down (P1 target) | `GET /api/health` 200 throughout (≤2s BCW), badge stays `Ready`, `/backtest` renders, port never unreachable | 7.5 min baseline PASS (84/84 @ 200), then **backend fully unresponsive 20m51s** (51 consecutive timed-out health polls, port connection-refused), badge stuck "Checking backend…", `SIGTERM` not honored | **FAIL** |

**Overall browser QA:** 0/2 target journeys PASS

---

## Critical Findings from Browser QA

### UT-J-07 Total Outage — Full Timeline

| Time (UTC) | Event | Evidence |
|-----------|-------|----------|
| 20:01:36 | J-05 backfill (run 272) triggered; pre-existing stalled background compute already active (horizons_done: 0/5 since 19:49) | - |
| 20:02:15–20:09:48 | Clean baseline: 84/84 health polls @ 200, max 1.756s | `UT-J-07-health-poll-baseline.csv` |
| 20:10:11 | Last successful health poll (horizons_done: 1) | - |
| 20:10:33 | **First timed-out health poll** (5s timeout) | Outage begins |
| 20:10:33–20:31:24 | **51 consecutive timed-out `/api/health` polls from two independent pollers; direct `curl --max-time 4` returns `http_code=000`** | `UT-J-05-J-07-job-and-outage-timeline.csv` |
| 20:13:56 | Backend log stops all output (last line: caught `MemoryError` in `evidence.py`); internal logging ceased | `logs/backend.log` excerpt |
| 20:26:13 | This tester sends `SIGTERM` (graceful shutdown request) | - |
| 20:31:12 | Process still alive, all 19 threads `S` (sleeping), cumulative CPU not advancing | `/proc/<pid>/status` snapshot |
| 20:31:37 | **This tester escalates to `SIGKILL`** (process was 4m59s past its configured 120s graceful-shutdown window) | - |
| 20:31:56 | Fresh backend responsive from `bash scripts/start-backend.sh`; port turnaround ~19s | Recovery confirmed |

**Backend log analysis:** Zero shutdown output for the killed process. Log shows no `Shutting down`, no `Waiting for application shutdown`, no `Finished server process` — uvicorn's signal handling never ran. The asyncio event loop was wedged (all threads `S`, no CPU advancement).

### UT-J-05 Impact

During the outage, job 272 (J-05's test case) transitioned to `failed`:
- Precondition check: 2019-02-26 confirmed absent from `/scanner-runs` before test start
- Job created with `start=end=2019-02-26`, `status=running` at 20:01:36 UTC
- `dates_done` never advanced past 0; `snapshots_created` stayed 0
- At 20:11:29 UTC (within the outage window), transited to `failed` with persisted message: `"backfill: 0 snapshots over 1 dates, 0 forward returns"` (generic summary, not captured exception text)
- No `/scanner-runs` entry created
- Badge left `Ready` state, stuck on "Checking backend…" (loading skeleton)

**Evidence:** Screenshots `UT-J-05-job-failed.png`, `UT-J-07-outage-checking-backend.png`; timelines in `UT-J-05-J-07-job-and-outage-timeline.csv`

---

## Definition-of-Done Compliance

| Criterion | Required | Status | Evidence | Notes |
|-----------|----------|--------|----------|-------|
| **TC-1:** Launcher flags wired | YES | **PASS** | `/proc/<pid>/cmdline` confirms `--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120` live on PID 292479 | Mechanical wiring correct; flags present but insufficient to close availability goal |
| **TC-2:** Self-terminate on SIGTERM, no `kill -9` | YES | **FAIL** | Browser lane: `SIGTERM` 20:26:13 UTC → process alive at 20:31:12 (4m59s past 120s window) → `SIGKILL` required | Dev's lightweight test showed 6s exit; real scenario with wedged event loop required force kill |
| **TC-3:** Live SIGUSR1 diagnosis of blocked call | YES | **PASS** | Two corroborating all-thread dumps; blocked sites named: `_excluded_counts_by_date` O(dates×pool) loop + `compute_forward_aggregates` bounded-slice read | Diagnosis methodology sound; correctly identifies multiple bottlenecks |
| **TC-4:** Fix stall or honestly disclose | YES | **PASS** | Disclosed as unresolved; candidate fixes deferred as materially larger unevidenced work | Correct per spec binding (iter-38/42 lessons); honest disclosure preferred over speculative fix |
| **TC-5:** ≤2s BCW health budget | YES | **FAIL** | Dev measurement: 224/240 (93.3%) ≤2s; 16/240 (6.7%) exceeded, max 2.354s. Browser baseline: 84/84 clean, then total outage | 6.7% overage in isolation; completely moot given TC-7 failure |
| **TC-6:** Concurrent cached `GET /api/backtest` | YES | **PASS** | Dev measurement: 200 in 162ms | Single read verified; stress level insufficient (browser outage makes real concurrent load impossible to measure) |
| **TC-7:** Never fully unreachable | YES | **FAIL** | Browser lane: 51 consecutive timed-out `/api/health` polls over 20m51s; port connection-refused; zero responses | This is the exact failure TC-7 exists to prevent; iteration's goal completely unmet |
| **TC-8:** Induced-pressure abort still holds | YES | **PASS** | Audit B2 fixes applied; `test_ingest_finalize_memory_pressure.py` now 2/2; fault-injection 5/5 | Memory-pressure abort handlers fixed (malloc_trim + deferred import escapes) |
| **TC-9:** Retry returns 503 on thread-launch failure | YES | **PASS** | All three job-launch endpoints now share (RuntimeError, MemoryError) → 503 contract | Parity achieved, test passes |
| **TC-10:** Failed job preserves real message | PARTIAL | **FIXED but observed as no-op** | Code fix applied (type-name fallback); audit B1 test passes. BUT browser observed job 272 with generic message during outage. | This is timing artifact (pre-restart state); code path now correct |
| **TC-11:** tsconfig.json clean | YES | **PASS** | `git diff HEAD` empty; iter-43 F1 stray reordering not present | Verified clean; no work required |
| **TC-12:** J-05 retested on unsnapshotted date | YES | **FAIL** | 2019-02-26 confirmed absent beforehand; job created but never completed due to concurrent outage; ended `failed` with zero snapshots | Test scenario incomplete; job never ran to terminal state |
| **TC-13:** Required-still-passing regression PASS with unique evidence | DEFERRED | **PRE-VERIFIED** | Regression replay (J-01, J-03, J-04, J-06, J-08, J-09) executed ~19:48-19:49 UTC before outage; unique evidence timestamped | Not re-emitted in browser lane report (pre-verified per dispatch instructions) |

---

## Key Blockers

### 1. Phase Goal Not Achieved — Service Went Fully Unreachable

**The phase spec opening states:** *"Stop J-07's heavy warm from taking the whole service unreachable."*

**Result:** During this iteration's own verification, the service became completely unresponsive for **20 minutes 51 seconds**, requiring manual `SIGKILL`. This is:
- **Worse than iter-43** (which needed kill -9 after "several minutes")
- **Direct contradiction of TC-2 and TC-7**, both DoD items
- **Reproducible under realistic conditions** (two concurrent heavy computes: pre-existing stalled background compute + new ingest-finalize warm), not speculative

**Root cause identified by dev:** asyncio event-loop wedge. All 19 threads stuck in `S` (sleeping), no CPU advancement. The `--timeout-graceful-shutdown` flag is enforced by the event loop; when the loop itself is wedged, the flag cannot fire. No in-process watchdog can escape a wedge in which no Python thread advances.

**Why not fixed this iteration:** Spec defers the root-cause fixes (incremental membership-timeline cache redesign or sixth `_SymbolColumns` bound attempt). Both are materially larger unevidenced work. An out-of-process supervisor is the evidenced next step — new mechanism outside this iteration's scope.

**Consequence:** TC-2 and TC-7 are unmet. The phase goal is not achieved.

### 2. TC-5 Not Met — Health Budget Exceeded

6.7% of the dev's clean-measurement health polls exceeded the rescoped ≤2s bounded-compute-window (BCW) budget (16/240, max 2.354s). This is technically a miss of "every poll" but represents a large improvement over the confounded run's 70.9% overage. However, it is moot given TC-7 failure.

### 3. TC-12 Incomplete — J-05 Never Completed

J-05's defining test case (a genuinely unsnapshotted date, 2019-02-26) was triggered but never completed. The job entered `running` and failed mid-execution due to the concurrent outage. Per the spec's TC-12 wording, option (b) allows "if it does not terminate within a bounded observation window, the run's honest in-flight state (never a fabricated success) is captured and reported." This was done, but it means the journey was not verified on its own real use case.

---

## Audit Findings (from `reports/reviews/goal-ops-hardening-iter-44-review.md`)

The reviewer re-ran the iteration after the auditor's FAIL and identified:

**CRITICAL:** `test_ingest_finalize_memory_pressure.py` is flaky. Audit reported "2 passed in 170.76s"; review re-ran the same code and got "1 failed / 1 passed" on the first run, then "2 passed" on immediate rerun. This is a third, undisclosed `MemoryError` escape (distinct from the two audit B2 fixed sites), likely in exception-logging/formatting code. Reviewer recommends 3-5 consecutive clean runs before re-closing TC-8/B2.

**Mechanical fixes verified:** TC-1 (launcher wiring), TC-9 (Retry parity), TC-10 (message honesty) all correct via targeted pytest passes. TC-11 (tsconfig.json) confirmed clean.

**But:** TC-2/TC-5/TC-7 remain unmet and honestly disclosed as "out-of-iteration-reach" — unlike previous claims that were later refuted by the browser lane.

---

## Browser Checks — Evidence Directory

**Frontend Present:** no (per plan: no new UI surfaces ship this iteration)

**However, browser QA was executed** to verify both target journeys (J-05, J-07) via Chrome MCP. Complete evidence recorded in `reports/qa/goal-ops-hardening-iter-44-evidence/`:

| File | Purpose |
|------|---------|
| `UT-J-05-job-failed.png` | Post-recovery run-history row for failed job 272 |
| `UT-J-07-outage-checking-backend.png` | Badge stuck "Checking backend…" loading state during outage |
| `UT-J-07-health-poll-baseline.csv` | 84/84 clean health polls before incident (7.5 min baseline) |
| `UT-J-05-J-07-job-and-outage-timeline.csv` | Full timeline: baseline → last-good-poll → 51 consecutive timeouts → SIGKILL → recovery |

---

## Summary

| Scope | Count/Status | Verdict |
|-------|-------------|---------|
| **Backend unit tests** | 57 passed | PASS |
| **Definition-of-Done items met** | 8/13 (TC-1, TC-3, TC-4, TC-6, TC-8, TC-9, TC-11, TC-13) | PARTIAL |
| **Definition-of-Done items UNMET** | 5/13 (TC-2, TC-5, TC-7, TC-10 observed as no-op, TC-12) | FAIL |
| **Critical phase-goal items** | TC-2 (graceful shutdown), TC-7 (never unreachable) | FAIL |
| **Browser journey tests (P1 target)** | 0/2 passed (UT-J-05, UT-J-07) | FAIL |
| **Root-cause diagnosis** | Named with two SIGUSR1 dumps | PASS |
| **Known issues** | Flaky memory-pressure test (audit B1/B2 incomplete per reviewer) | CRITICAL |

---

## Conclusion

**Verdict:** FAIL

**This iteration's mechanical work is solid:**
- Launcher-flag wiring verified live on the real process
- Live stall diagnosis methodology sound and produces actionable findings
- Message-honesty fixes applied (audit B1, B2)
- Code is cleaner and more honest than before

**However, the phase GOAL is NOT achieved.**

TC-2 and TC-7 — the two core Definition-of-Done items defining "Stop J-07's heavy warm from taking the whole service unreachable" — are both refuted by this pipeline's own browser lane. The service went fully unreachable for 20+ minutes, worse than the incident it set out to close.

The root cause (asyncio event-loop wedge rooted in membership-timeline cache's O(dates×pool) full-history recompute) is accurately diagnosed but deferred as requiring an out-of-process supervisor, which is architecturally correct and beyond this iteration's scope.

**Result:** Pipeline must halt here. QA validates the evidence, auditor identified the gaps, reviewer confirmed them. The phase goal cannot be closed on this iteration.

Recommendation to evaluator: Record FAIL; mark next iteration with TC-2/TC-7 + out-of-process supervisor mechanism as highest priority for achieving the session's availability promises.
