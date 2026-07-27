# Iteration State — ops-hardening

**After iteration:** 28 · **Date:** 2026-07-27 · **Verdict:** CONTINUE

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) — 8 total, all re-verified at iter-28

## Active blockers

- **dev — the ONE open anti-goal finding (AG-8, minor); the only thing between this session and
  GOAL_ACHIEVED.** `research.py:207-217` builds an unbounded `ret_by_run_symbol` dict over the whole
  `forward_returns` table (3.96M rows); MemoryError on `GET /api/evidence` at iter-27, also breaks ingest
  finalize (`data_manager.py:3361`); code unchanged since. Bound it AND serve an honest degraded response.
- **dev, non-blocking** — `UT-04` (coverage "not yet computed") needs a fresh-install DB fixture or a
  written waiver; the fixed `J-06.json` has never run through the deterministic replay lane (TC-9).
- **owner, non-blocking** — first-touch historical `/backtest` measured 206 s / 273 s (was 738-1442 s at
  iter-27); still no written budget. Card B-1107 (dispatch cap) stays optional.

## Last 2 verdicts

- iter 28: CONTINUE — iter-27's quota-killed browser lane was re-run in full; J-05/J-07/J-08 unknown ->
  passing, J-06 partial -> passing; only the carried AG-8 finding keeps GOAL_ACHIEVED off.
- iter 27: CONTINUE — both iter-26 findings fixed and verified, but the browser lane was quota-killed
  before testing its 3 target journeys; one new minor AG-8 finding opened.

## Do not redo

- **Drift-report self-poisoning FIXED** — `config.yaml:1152` + `config.py:2286` now point at this session's
  own `state/drift-report.json`. **J-06 golden FIXED** — step 1 asserts `"Market Regime"`; never assert a
  readiness/preflight string in a golden script.
- **iter-27 AG-8 (concurrent `/backtest` 500) + AG-3 (all-zero coverage) CLOSED, browser-verified** — 4
  overlapping requests on 2018-03-15 wrote exactly ONE `scanner_runs` row (1873); stale panel shows real
  figures under "Coverage as of a prior scan (version r1872-…)".
- **Byte-frozen** — `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split, the demo JSON, the OWNER BUDGET
  AMENDMENT. Audit B2 (`_backfill` rollback residual) needs its own iteration.
- **Never** re-trigger a live memory-pressure background-compute failure; never run the full pytest suite or
  two concurrent pytests here (`test_readiness.py -k drift` is NOT fixture-free — 1h37m). Consumed race
  dates: 2011-03-10, 2015-09-09, 2018-02-15, 2018-03-15, 2025-05-15, 2026-05-02..29.
