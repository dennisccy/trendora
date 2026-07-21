# Iteration State — ops-hardening

**After iteration:** 7 · **Date:** 2026-07-21 · **Verdict:** REGRESSION

## Journeys

3 passing (J-01 J-03 J-04) · 1 regressed (J-05) · 1 partial (J-06) — 5 total. J-05 broke; J-06 target fixed but not a clean pass.

## Active blockers

- **REGRESSION HALT — human review required.** J-05 (`passing`→`failing`): `GET /api/health` hung 7+ min during a heavy ingest; backend hit its enforced `memory_cap_mb=6144` `ulimit -v`, worker-thread `MemoryError`, all 22 threads `futex_do_wait`, manual restart needed. Lives on the ingest finalize hot path (`app.engine.data_manager._refresh_ingest_aggregates`) this iter modified. Owner: human (capacity/architecture call) → then dev. Evidence: `reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md` UT-J-05 + `reports/qa/goal-ops-hardening-iter-7-evidence/J-05-backend-hung-checking.png`.
- AG-8 (critical, unresolved): memory exhaustion + ungraceful hang (frozen "Checking backend…" instead of honest "Backend unavailable"); also a live `/api/backtest`→`forward_aggregates_cached`→large `ScannerResult` MemoryError on an on-load path. Attribution to iter-7's diff contested (pre-existing `/api/backtest` OOMs predate the test).

## Last 2 verdicts

- iter 7: REGRESSION — J-05 verified passing→failing (7-min health hang + MemoryError during heavy ingest, manual restart); AG-8 concern. Merged "PASS" top-line is the priority-blind merge bug; RAW browser-qa = FAIL.
- iter 6: CONTINUE — J-04/J-05 unknown→passing, J-06 failing→partial (Dashboard/Data latency fixed); closure gate + /evidence cold-miss outstanding.

## Do not redo

- J-06 `/evidence` cold-miss fix: DONE & verified — ingest-time `drawdown_expectations` warm (`_refresh_ingest_aggregates`), first-view 22.4ms real-browser, byte-identical (UT-02/UT-06/audit). Residual is the availability/capacity failure it surfaced, NOT the warm's correctness.
- J-01/J-03/J-04 settled: replay/LLM PASS this iter — do not re-plan their surfaces.
- max_range_days removal, snapshot_cadence, readiness.py/main.py boot: settled (prior iters).
- Recovery iter (after fix + `--acknowledge-regression`), full depth: root-cause the heavy-ingest MemoryError, bound/defer the ingest-time warm if it raises peak RAM, make health fail-fast + auto-recover on MemoryError (no manual restart), then re-run J-05's heavy-ingest step live.
