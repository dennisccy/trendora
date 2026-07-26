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
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-25-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-25-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-25-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-25-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-25-evidence/J-06-verify.png |
| UT-J-07 | Heavy aggregates never take the service down (goal.md journey) | regression/smoke | P1 | `GET /api/health` answers 200 throughout a real forward-aggregate background-compute window covering every configured horizon, in one long-lived process; no frozen/unresponsive window; peak-memory + induced-fault steps are backend-internal (already covered) | Two real, independently-dispatched background-compute windows (2026-07-14, then 2026-07-13; both `horizons_total=5`, all 5 configured horizons) ran back-to-back in the SAME long-lived backend process (PID 1662743) without any crash or restart between them. Polled `GET /api/health` once per second for 12 consecutive seconds during the second window: **12/12 polls returned HTTP 200** (latencies 0.126s–1.719s — elevated vs. the settled ≤0.1s steady-state budget, the same pre-existing owner-accepted BCW elevation documented in `reports/perf-budgets.md`, not a new regression). Window completed cleanly (`outcome:"completed"`, `duration_ms:74689`); readiness stayed `"ready"` throughout — never wedged, never restarted. Step-3/step-4 (peak VmPeak, induced memory-pressure fault injection) are backend-internal test-hook scenarios outside browser-QA's reach and are binding "do not redo" this iteration (TC-13/TC-14, owner-authorized, dated 2026-07-25, already PASSED) | PASS | `reports/qa/goal-ops-hardening-iter-25-evidence/UT-J-07-health-poll.log`; cross-checked against direct `GET /api/health` reads quoted in this report |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-25-evidence/J-08-verify.png |
| UT-J-09 | The backend discloses its own background-compute activity (goal.md journey, all 6 steps + F1/T1-adjacent TC-3/TC-4 browser checks per iter-25 TESTING REQUIREMENTS) | regression/new-capability | P1 | Steady-state `Ready`; a triggered historical `/backtest` view dispatches compute to a background thread without blocking; the SAME poll discloses it (badge detail + `/data` panel) while in flight; idle/last-outcome after completion; scope is honestly process-lifetime; poll-failure state is never misrepresented as idle | All six goal.md steps verified live (detail below) plus the new poll-failure "unknown" copy branch (TC-3) and the unchanged genuine-idle copy (TC-4), both introduced/preserved by this iteration's frontend change | PASS | `reports/qa/goal-ops-hardening-iter-25-evidence/UT-J-09-01-steady-ready.png`, `UT-J-09-03-badge-inflight.html`, `UT-J-09-04-data-panel-inflight.html`, `UT-J-09-05-data-panel-idle-lastoutcome.html`, `UT-J-09-06-idle-none-yet-post-restart.html`, `UT-J-09-07-poll-failure-unknown.html`, `UT-J-09-07-poll-failure-viewport.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-26

