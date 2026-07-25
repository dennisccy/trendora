# Iteration State — ops-hardening

**After iteration:** 23 · **Date:** 2026-07-25 · **Verdict:** GOAL_ACHIEVED

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08) · 0 partial · 0 failing · 0 unknown — 7 total.
All 7 re-verified at iter-23 (replay 4/4 + LLM lane 3/3); all 7 `spec_hash`es match current `docs/goal.md`.

## Active blockers

- **None.** The owner budget decision behind the iter-20/21 halts is settled and committed. Both
  agent-tractable iter-22 CONFIRM-reject findings are closed; the third was fixed by the operator
  (`reports/perf-budgets.md:3714`).
- Non-blocking: trim demo step n=9's "7.1191 s"/"0.2530 s" to 3 decimals
  (`reports/goal-session-ops-hardening-demo.json:105`, reviewer MINOR — exact vs the raw `bcw-measure.csv`,
  only the rendering differs). Owner-optional: backlog card **B-1107** (global cap on concurrent background
  computes) — re-opens the goal only under a literal AG-8 reading (`state/assumptions.md` iter-22).

## Last 2 verdicts

- iter 23: GOAL_ACHIEVED — the session demo manifest `--session-live` reads now carries 5 `[NEW]`/verified
  J-06/J-07/J-08 steps (was zero); `J-06.json`'s undisclosed timeout reverted 18000→8000 on a DB+log basis
  the evaluator re-derived; zero `apps/` diff, scan CLEAN, coherence PASS.
- iter 22: GOAL_ACHIEVED (first key) — REJECTED by the second-key CONFIRM on the three findings iter-23 closed.

## Do not redo

- **The budget amendment is settled owner policy** (`reports/perf-budgets.md` § "OWNER BUDGET AMENDMENT" +
  "Revision 1"): never edit, re-litigate, or "fix" the transient BCW contention in code.
- **TC-13 (concurrent-ingest overlay) and TC-14 (disruptive J-04 kill/restart)** are DONE and PASS, dated
  2026-07-25 (`runs/goal-ops-hardening-iter-21/` + `perf-budgets.md`); never re-run.
- **`J-06.json`'s `default_timeout_ms` = 8000 is investigated and cited** — no BCW overlap exists
  (no `forward_aggregate_cache` row 07:32:56–09:27:55 UTC; `logs/backend.log:77525/77533` = 30–45 ms).
- **Demo steps n=1–7 stay byte-unchanged**; `highlights` is at its 8-step cap — new steps must be `full_tour`.
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split/empty state — byte-unchanged; do
  not reopen. The cutover-pruning contract (`forward_testing.py:1135-1156`) is load-bearing evidence.
- Retarget `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches BEFORE removing the
  imports at `backtest.py:75` / `mcp/tools.py:38`; `/backtest` captures stay full-page/element-scoped.
