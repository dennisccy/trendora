# UI Test Results (merged)

**Date:** 2026-08-13
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 5/8 journeys passed (2 skipped, 2 required-unverified)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-73-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-73-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-73-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | Live backfill of one unsnapshotted day creates a snapshot from stored aggregates only; the persisted run record lists which finalize-hook aggregates it refreshed; `GET /api/health` stays responsive throughout | Ran a real ~17m41s in-app backfill of 2005-07-12 end to end; job record + `/scanner-runs/2978` + `GET /api/data/jobs/<id>` all confirm storage-backed serving, all 9 aggregate categories refreshed, and a 1232-poll 1Hz health drill recorded 0 non-200s / 0 breaches throughout | PASS | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-05-result.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 nav-listed pages render their real heading/testid-gated on-load value within budget, on a warm prod-mode backend | All 16 golden steps re-verified live: readiness badge ready (7.5-12.9ms health calls), AAPL chart caption + 1.5ms cached bars call, availability-cell 34.1ms, `/api/runs` row + 320.9-378.6ms, remaining 7 pages render real headings/DOM, no drift from iter-71/72 baselines | PASS | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-06-result.png` |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks | SKIP | reports/qa/goal-ops-hardening-iter-73-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | All 4 numbered steps hold: (1) a full deep-basis forward-aggregate warm runs while `/api/backtest` keeps serving every horizon; (2) `GET /api/health` answers HTTP 200 on every 1 Hz poll throughout, no frozen window; (3) the process's peak VmPeak during the warm is measured and recorded under `server.memory_cap_mb` with its margin in `reports/perf-budgets.md`; (4) an induced memory-pressure abort during a warm is graceful — the SAME process keeps serving `/api/health` and cached reads, never wedged/restarted | Steps 1+2 (the browser/live-observable half): fresh evidence is clean — see body below (readiness badge `ready`, `/backtest` serving 2,917 stored snapshots with no "Refreshing" banner, 20/20 steady-state health polls just now, plus this iteration's own real warm activity — a 17m41s backfill and a 26-minute pressure-free rebuild arm — both recorded 0 non-200 health polls). Step 3 (the round's actual target): **not closed** — this iteration's developer pass ran the live pool-pressure drill 4 times; the 3 pressure-added attempts all collided with a separate, already-disclosed uvicorn admission-control 503 issue before completing, and the 1 pressure-free attempt that did run clean did not reach the warm's finalize tail before its own time bound, so no complete VmPeak-under-realistic-pool-pressure figure exists (`reports/perf-budgets.md` Addendum 38). Step 4: not exercised this round by any lane (code byte-unchanged — durability carry from earlier iterations, not independently re-verified here). | FAIL | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-07-result.png` |

## Missing Required Journeys

_Required-still-passing journeys named in the iteration spec that were NOT verified this iteration — either no lane (deterministic replay or LLM browser-qa) produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-40 lesson: this is exactly how required journeys shipped with zero evidence while every gate reported clean)._

- `UT-J-08` — only a SKIP row for J-08: named but never executed
- `UT-J-09` — only a SKIP row for J-09: named but never executed

## Failed Tests

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** FAIL
**Failure:** Steps 1+2 (the browser/live-observable half): fresh evidence is clean — see body below (readiness badge `ready`, `/backtest` serving 2,917 stored snapshots with no "Refreshing" banner, 20/20 steady-state health polls just now, plus this iteration's own real warm activity — a 17m41s backfill and a 26-minute pressure-free rebuild arm — both recorded 0 non-200 health polls). Step 3 (the round's actual target): **not closed** — this iteration's developer pass ran the live pool-pressure drill 4 times; the 3 pressure-added attempts all collided with a separate, already-disclosed uvicorn admission-control 503 issue before completing, and the 1 pressure-free attempt that did run clean did not reach the warm's finalize tail before its own time bound, so no complete VmPeak-under-realistic-pool-pressure figure exists (`reports/perf-budgets.md` Addendum 38). Step 4: not exercised this round by any lane (code byte-unchanged — durability carry from earlier iterations, not independently re-verified here).
**Evidence:** ``reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-07-result.png``

## Skipped Tests

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request (payload-gated)

**Verdict:** SKIPPED
**Reason:** voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks

### UT-J-09 — Disclose in-flight background-compute activity (badge + /data panel)

**Verdict:** SKIPPED
**Reason:** voided: suspected selector/environment drift — mass replay FAIL overturned by green canary re-checks

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-13

