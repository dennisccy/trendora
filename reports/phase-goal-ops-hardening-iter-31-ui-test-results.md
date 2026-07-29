# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-09-verify.png |
| UT-FL-01 | Factor Lab all-factors view loads without MemoryError | smoke | P1 | `/research/factor-lab` returns HTTP 200; decile table + rank-IC render real numeric values for every catalog factor at every configured horizon; zero console errors; zero MemoryError in backend log | Page loaded via real browser navigation; extracted page text shows all 11 catalog factors each with real rank-IC, N=771129 (or the factor's own real N), risk-adjusted, and FWD/MDD values populated for all 5 horizons (1d/5d/10d/20d/60d); console capture showed only a React-DevTools info line, zero errors; backend log shows 0 MemoryError since this run's boot banner (line 132546) | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/TC-1-factor-lab-all-factors.png |
| UT-J-06 | Pages load only what they need (Factor Lab, this iteration's affected page) | regression | P1 | The one `/research` lab page in J-06's golden loads correctly (page-load smoke, per spec's Factor-Lab-spot-check mapping for this iteration); the previously-crashing Factor Lab page also loads | Golden script `J-06.json` replayed end-to-end via deterministic replay lane (demo_runner.py --mode verify), all 11 steps' expects held; supplemented by this agent's own live navigation to `/research/factor-lab` (the page this iteration's fix targets), which rendered correctly per UT-FL-01 | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-06-verify.png (ride-along replay) + reports/qa/goal-ops-hardening-iter-31-evidence/TC-1-factor-lab-all-factors.png (live navigation) |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Per spec's mapping, this iteration's J-07 browser coverage is the Factor-Lab spot-check (AG-8 crash-avoidance) plus the golden's existing smoke check | Golden script `J-07.json` replayed end-to-end via deterministic replay lane, both steps' expects held (`/evidence` shows "-7.48%", `/data` shows "drawdown expectations"); backend stayed responsive throughout (health checks above) | PASS | reports/qa/goal-ops-hardening-iter-31-evidence/J-07-verify.png |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

