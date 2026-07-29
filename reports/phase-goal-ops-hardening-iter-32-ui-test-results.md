# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-32-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-32-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-32-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-32-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-32-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-32-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | smoke | P1 | `/backtest` (the page served by the restructured `compute_forward_aggregates`) renders real by-group/control-group figures with zero console errors and zero backend crash; the dev/QA's independently-recorded live full-deep-basis warm shows zero `MemoryError` and a `VmPeak` margin recorded in `reports/perf-budgets.md` | Live Chrome MCP navigation to `/backtest` rendered the full page including the "Forward-tested evidence" section's `by_bucket`/`by_setup`/`by_regime`/`by_vcp`/`excess`/`control_group` tables with real, non-NA numbers (e.g. Bucket A `+10.68% n=8869`, Excess vs SPY `+0.60% n=749441`, Top-ranked cohort `+6.77% n=36316` vs Random same-sector peers `+6.27% n=22178`) — exactly the outputs the iteration's restructured accumulators produce; browser console showed zero errors (only the standard React-DevTools info line); 6/6 fresh `GET /api/health` polls at 1 Hz returned HTTP 200 during this check. Independently re-derived (read-only, no new compute triggered): `tail -n +133277 logs/backend.log \| grep -c MemoryError` = 0 from this session's own boot banner forward; `reports/perf-budgets.md`'s "Iteration 32" section exists with the recorded live-warm measurement (VmPeak 2,691,600 kB flat across both trials, margin 3,515.5 MB / 57.2% headroom under the 6144 MB cap, 77/77 health polls HTTP 200 across two independent trial dates) | PASS | `reports/qa/goal-ops-hardening-iter-32-evidence/J-07-backtest-forward-aggregates.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

