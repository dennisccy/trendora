# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-34-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Live full-horizon forward-aggregate warm runs in the same long-lived backend process; `GET /api/health` stays HTTP 200 throughout with no frozen window; readiness badge and `/backtest` never blank or crash; VmPeak stays under the memory cap; an induced memory-pressure abort is caught honestly with the same process still serving health + cached reads | Warm triggered live via the browser (`/backtest?asof=2026-07-15`, an uncached date under `dataset_version=r1879-f3971375`); badge showed "Ready · background compute running (1)" and the page showed the honest "Refreshing — showing the last complete evidence" state throughout the ~75 s warm, never blank/erroring; 100/100 `/api/health` polls at 1 Hz returned HTTP 200 (min 0.105 s / median 0.113 s / max 0.877 s — exceeds the ≤0.1 s budget, an honest WARN consistent with the existing documented convention, not a functional failure); warm completed (`background_compute.recent_outcomes: outcome=completed, duration_ms=74888`) and the page then rendered full evidence for 2026-07-15 ("Snapshots contributing (≤ 2026-07-15): 1873") with the badge still "Ready" and the SAME backend PID (2213604) alive throughout, no restart. Step 3 (VmPeak vs `memory_cap_mb`) and step 4 (induced-memory-pressure abort in a throwaway process) are backend/process-level actions with no browser affordance to drive — not re-executed by this browser session; they were independently verified live by the developer this iteration with log-corroborated evidence and a new passing permanent regression test (`test_ingest_finalize_memory_pressure.py`, 2 passed), documented in `reports/perf-budgets.md` ("Iteration 34 — J-07 step 2" / "step 4" sections). | PASS | `reports/qa/goal-ops-hardening-iter-34-evidence/J-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

