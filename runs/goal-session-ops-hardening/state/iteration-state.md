# Iteration State — ops-hardening

**After iteration:** 30 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys
6 passing (J-01 J-03 J-04 J-05 J-08 J-09) · 2 partial (J-06 J-07) · 0 failing · 0 unknown — 8 total

## Active blockers
- **dev, FIRST — `/research/factor-lab` still runs out of memory** (`research.py:583`, the RETURNED `pools[h]`, ~771K x 5 horizons,
  docstring "NOT bounded here (deliberate)"). Live TC-05 FAIL this iteration; deferred twice. Bound the return list AND add the
  single-flight guard `factor_lab_all_cached` lacks (audit B5).
- **dev, SECOND — `stock_obs` (`forward_testing.py:988`) still unbounded**, the literal frame of the old crash; needs deliberate
  re-pinning of `_attribution_slices`'s frozen `(stock_obs, cfg)` signature. Also record the warm's VmPeak + margin in
  `perf-budgets.md` (J-07 step 3, never done).
- **capture only, passenger tasks, never an iteration goal:** `J-06.json` through the deterministic replay lane (no PASS row since
  iter-28); browser-QA's real-browser 11-page TTI sweep.
- **framework, outside the loop — the merged results file laundered a P1 FAIL into "PASS 6/6"** (`merge_ui_test_results.py`
  `_ROW_RE` matches only `UT-`; browser-qa emitted `TC-`); fix before any achievement run. Still deferred: `warmup.py:194`,
  `prices.py:141`, audit B2, UT-04's fixture.
- **owner** — `GET /api/health` 0.127787s vs its <=0.1s budget (0.094-2.431s under compute); until it is amended, J-06 step 2 and
  J-07 step 2 can never both read true. No agent fix exists.

## Last 2 verdicts
- iter 30: CONTINUE — the targeted warm memory fix works live (zero MemoryError over the full basis, 273/273 health 200) and J-06's
  budgets edit landed, but only 2 of 3 named containers were bound and Factor Lab still crashes, so both targets stay partial.
- iter 29: CONTINUE — the Evidence-page fix closed the oldest AG-8 finding, but three new live MemoryErrors appeared and both
  target journeys fell short of their own goal.md steps.

## Do not redo
- **`compute_forward_aggregates` run-chunking — DONE, proven** (`walk_forward.forward_agg_run_chunk: 100`, 19 chunks at h=20, 38
  byte-identity assertions, -16.4% peak); never fold into a ROWS knob, only `stock_obs` remains. **`_factor_observations`
  accumulator — DONE**; the OPEN part is the returned `pools[h]`.
- **`reports/perf-budgets.md` iter-30 section — DONE** (boot 1.354s, 11 pages, 15 endpoints, honest `/api/health` WARN); the
  missing half is real-browser TTI only. **Byte-frozen:** `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split, the demo JSON, the OWNER BUDGET AMENDMENT.
- **Never** re-trigger live memory pressure; never run the full suite or two concurrent pytests (`test_readiness.py -k drift` is
  NOT fixture-free — 1h37m). Consumed dates: 2005-04-05..11, 2011-03-10, 2015-09-09, 2018-02-15, 2018-03-15, 2022-04-12,
  2026-05-02..29. Audit B2 needs its own iteration.
