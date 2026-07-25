# Iteration State — ops-hardening

**After iteration:** 22 · **Date:** 2026-07-25 · **Verdict:** GOAL_ACHIEVED

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08) · 0 partial · 0 failing · 0 unknown — 7 total.
J-06 + J-07 crossed this iteration; all 7 verified in iter-22 (replay 3/3 + LLM lane 4/4).

## Active blockers

- **None blocking.** Owner-owned optional: promote backlog card **B-1107** (global cap on concurrent
  historical background computes) — `docs/improvement-backlog.md` Track 11. At N=5 concurrent BCWs the
  process reached its `ulimit -v` cap and one compute raised a contained `MemoryError`
  (`logs/backend.log:76796-76808`); service stayed 32/32 HTTP 200 / `readiness: ready`. Scored a residual
  risk, not an AG-8 violation (`state/assumptions.md` iter-22 records the reading that would re-open it).
- Documentation debt (non-blocking, lean-sized): 3 corrections owed in `reports/perf-budgets.md` — see
  `runs/goal-session-ops-hardening/iter-22/eval.md` § Next-Step item 1.

## Last 2 verdicts

- iter 22: GOAL_ACHIEVED — owner's BCW budget amendment (+ same-day 90 s revision) in
  `reports/perf-budgets.md` closed J-06/J-07's only blocker; two independent live BCWs inside the amended
  ceilings, VmPeak margin 58.2 %, all numbers re-derived by the evaluator from the raw CSV + DB.
- iter 21: STALLED — J-08/J-04 closed, but J-06/J-07's budget breach was a human-owned decision.

## Do not redo

- **The budget amendment is settled owner policy** (`reports/perf-budgets.md` § "OWNER BUDGET AMENDMENT" +
  "Revision 1"): never edit, re-litigate, or "fix" the transient BCW contention in code.
- **TC-13 (concurrent-ingest overlay) and TC-14 (disruptive J-04 kill/restart)** are DONE and PASS, dated
  2026-07-25 — evidence in `runs/goal-ops-hardening-iter-21/` + `perf-budgets.md`; never re-run.
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split/empty state — byte-unchanged and
  verified; do not reopen.
- Retarget `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches BEFORE anyone removes the
  imports at `backtest.py:75` / `mcp/tools.py:38` — they are load-bearing `raising=True` targets.
- `/backtest` evidence-state captures must be full-page or element-scoped (banner renders below the fold);
  iter-22's three J-08 captures already satisfy this.
