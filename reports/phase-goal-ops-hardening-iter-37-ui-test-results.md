# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-37-evidence/J-09-verify.png |
| UT-J-07a | Heavy aggregates never take the service down — global readiness badge + /backtest | smoke | P1 | Global readiness badge reads "Ready" on the Dashboard; `/backtest` (served by `compute_forward_aggregates`, byte-frozen this iteration but downstream of the shared-cache-touched finalize path) renders the "Forward-tested evidence" section with real, non-NA figures and zero console errors | Navigated to `http://localhost:3255/` — readiness badge showed "Ready" (green), `provider: seed`, `seed 2026-07-22`, `591 symbols`, consistent with a fresh `GET /api/health` read (`readiness: "ready"`, `background_compute.active: []`). Navigated to `http://localhost:3255/backtest` — "Forward-tested evidence (expanding window ≤ 2026-07-22)" section rendered every group fully: score-bucket table (Bucket A `+10.70% n=8878` … Bucket E `+4.14% n=483802`), excess vs SPY/QQQ, setup/regime/VCP/pullback/flat-base breakdowns, and the control-group comparison (Top-ranked cohort `+6.77% n=36336` vs Random same-sector peers `+6.28% n=22191`) — none blank, none an error string. No partial render, no Next.js error overlay | PASS | `reports/qa/goal-ops-hardening-iter-37-evidence/UT-J-07a-backtest-readiness.png` |
| UT-J-07b | Heavy aggregates never take the service down — /data Coverage payload & Backfill run-summary contract | smoke | P1 | `/data` (the home for the Coverage payload and Backfill run-summary contract this iteration's shared-cache fix directly touches — `_do_backfill` / `_persist_per_date_coverage_snapshots`) renders Dataset coverage metrics and the Job progress / Run history run-summary rows with real, non-error values | Navigated to `http://localhost:3255/data` — "Dataset coverage" panel rendered real figures (Price history `1996-01-02 → 2026-07-22`, Universe 540, Symbols 591, Trading days 5383, Snapshot dates 1880, Backfill gaps 3508), per-symbol coverage table populated (591 rows). Extracted full page text: "Job progress" showed a real completed run-summary (`backfill job · 2025-06-01 → 2026-07-17`, `412 calendar days · 283 already snapshotted · 129 non-trading`, `Refreshed: coverage, membership timeline, forward aggregates, research hot keys, drawdown expectations`) — exactly the run-summary contract fields (`dates_total`/exclusion breakdown/`aggregates_refreshed`) this iteration's fix must leave unchanged (TC-9); "Run history" table listed multiple prior runs including two from earlier today, each with the same well-formed `Refreshed:` category list. No blank/NA-where-data-expected, no error banner | PASS | `reports/qa/goal-ops-hardening-iter-37-evidence/UT-J-07b-data-runsummary.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

