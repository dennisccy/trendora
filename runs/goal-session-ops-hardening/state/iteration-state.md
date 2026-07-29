# Iteration State — ops-hardening

**After iteration:** 29 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-03 J-04 J-05 J-08 J-09) · 2 partial (J-06 J-07) · 0 failing · 0 unknown — 8 total

## Active blockers

- **dev — `/research/factor-lab` returned HTTP 500 (MemoryError) on every visit, 4/4; audit FAIL +
  ux-regression FAIL.** A `research.py` fix (`_all_fr_slice_map`) landed AFTER the audit: undocumented,
  unreviewed, never opened in a browser since (one live 200 at `logs/backend.log:129876` is the only proof).
- **dev — three NEW live MemoryErrors, caught non-fatal, none in this diff:** `warmup.py:194` ->
  `forward_symbols_for_run` (readiness stuck "Initializing… 89/89" forever, `warmup.status: failed`);
  `forward_testing.py:965` in `compute_forward_aggregates` (byte-frozen — lift that freeze deliberately);
  `prices.py:141` whole-table `daily_prices` prefill in the ingest coverage refresh.
- **dev, small** — J-06 is partial for ONE missing edit: `reports/perf-budgets.md` not updated (step 2 / TC-8); TC-10 still needs `J-06.json` through the deterministic replay lane.
- **owner, non-blocking** — `data_provider_runs` 201 discloses "coverage refreshed" while the log shows that
  refresh raising MemoryError in the same window. `/backtest` latency has no budget; B-1107 optional.

## Last 2 verdicts

- iter 29: CONTINUE — the Evidence-page memory fix is proven real (7/7 claim cards render real figures, zero
  `research.py` MemoryError post-boot), closing the oldest AG-8 finding; but three NEW live MemoryErrors
  appeared and both target journeys fell short of their own goal.md steps.
- iter 28: CONTINUE — all 8 journeys re-verified passing; `research.py`'s unbounded `ret_by_run_symbol` stayed open and became iter-29's single blocking item.

## Do not redo

- **`_factor_observations` accumulator bound — DONE, proven** (`_runs_with_fr` / `_fr_slice_map`,
  `factor_join_run_chunk: 100`, 19 chunks / 55,195-entry peak at h=20). Never fold that knob back into
  `read_batch_size` — rows != runs is how it first shipped inert.
- **`build_evidence_payload` per-claim isolate-and-continue + `expectations_status` +
  `resolveDrawdownExpectationsPanelState` — DONE**, QA/audit-verified (UT-05/UT-06). Do not redesign.
- **Byte-frozen** — `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`,
  J-08's serving split, the demo JSON, the OWNER BUDGET AMENDMENT. Audit B2 needs its own iteration.
- **Never** re-trigger a live memory-pressure failure; never run the full suite or two concurrent pytests
  (`test_readiness.py -k drift` is NOT fixture-free — 1h37m). Consumed dates (not "fresh"): 2011-03-10,
  2015-09-09, 2018-02-15, 2018-03-15, 2022-04-12, 2026-05-02..29.
