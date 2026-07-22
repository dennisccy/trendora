# UI Test Results (merged)

**Date:** 2026-07-22
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-11-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-11-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-11-evidence/J-05-verify.png |
| UT-J-06 | J-06: Pages load only what they need (11-page real-browser TTI + on-load latency sweep) | performance/regression (target) | P1 | Every named page's TTI within the committed <=3s budget; every on-load API call within its committed budget (or an honest WARN); no frozen/blank page | All 11 pages measured via real Chrome (not curl): loadEventEnd 259.7ms-1099.4ms (worst case /sectors 1099.4ms), all well inside <=3s. All committed endpoint budgets held on a clean re-check. Two transient anomalies caught on a first pass (one endpoint over-budget, one /api/health outlier) both traced to a real, disclosed ~5-min window of elevated ambient host load (uptime 1.97 -> 0.63) and cleared on re-check — see methodology notes. Zero pages showed a blank/frozen/crashed state. | PASS | `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-*.png` (11 files), `UT-J-06-perf-sweep-summary.txt` |
| UT-J-04 | J-04: Non-blocking boot with visible status (6-step journey) | regression (required-still-passing) | P1 | All 6 acceptance steps hold: <=5s boot budget; pre-ready badge shows boot phase; crash shows explicit unreachable presentation; logfile shows boot events + abrupt end after a kill; a job mid-flight at a kill shows "interrupted" with real non-zero progress, never a phantom "running" row | Steps 1-2: this iteration's own fresh TC-3 boot measurement, 1.364s (holds <=5s). Steps 3-4: carried forward from iter-9's controlled-fetch-override simulation (badge/banner code confirmed zero-diff, on this iteration's own BINDING do-not-touch list). Step 5: live `grep` this turn confirms `logs/backend.log` has boot entries AND pid 2080333 (iter-10's real kill -9 target) has zero "Finished server process" line anywhere in the file, contrasted against pid 2100030 which DOES have one. Step 6: live navigation to `/data` this turn shows run 119 (job `bad4f8e9...`) and run 114 STILL rendering `interrupted` with real non-zero snapshots (117 and 59 respectively) and non-null breakdowns, surviving this iteration's own fresh restart cycle on top of iter-10's already-verified survival. | PASS | `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-04-step5-logfile-abrupt-truncation.txt`, `UT-J-04-step6-run-history-dom-live.txt`, `reports/qa/goal-ops-hardening-iter-10-evidence/UT-11-result.png`, `UT-12-result.png` (steps 3-4, carried forward) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-22

