# Iteration State — ops-hardening

**After iteration:** 26 · **Date:** 2026-07-26 · **Verdict:** ESCALATE

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) · 0 failing · 0 unknown — 8 total; all re-verified this iteration (replay 7/7 + LLM lane J-09).

## Active blockers

- **dev** — an unhandled `sqlite3.IntegrityError` escapes as HTTP 500 from `GET /api/backtest` when two
  concurrent requests hit the same never-scanned historical as-of: `apps/backend/app/api/backtest.py:171`
  -> `apps/backend/app/engine/forward_testing.py:1667` -> `:390` (`logs/backend.log:81004`). The fix needs
  the freeze on `backfill_run_forward_returns` lifted on purpose. No capture exists of what the user sees
  when it happens, so AG-8's "degrades gracefully" half is unverified.
- **dev** — `/data` shows an empty dataset (PRICE HISTORY "— → —", UNIVERSE 0) for a populated DB after a
  time-machine visit creates a run outside ingest: `apps/backend/app/engine/data_manager.py:908`; evidence
  `reports/qa/goal-ops-hardening-iter-26-evidence/UT-J-09-01-data-page-top-badge.png`.

## Last 2 verdicts

- iter 26: ESCALATE — both iter-25 confirm gaps closed and all 8 journeys re-verified, but the lane's own
  run exposed a server 500 plus a wrong-looking Data Manager screen; cross-cutting, so next round is full.
- iter 25: GOAL_ACHIEVED — J-09's walkthrough manifest + audit F1 closed; the second-key CONFIRM then
  REJECTED it on the ≤0.1 s budget evidence and the untested failure branch (both now closed by iter-26).

## Do not redo

- The `≤ 0.1 s` steady-state `/api/health` re-measurement — DONE and binding: `reports/perf-budgets.md`
  "Iteration 26 — J-09 confirm-gap 1" (all 4 statistics hold; supersedes iter-24). Append-only; never edit
  prior sections, the OWNER BUDGET AMENDMENT, Revision 1, TC-13 or TC-14.
- J-09 failure-branch coverage — DONE: `test_health_background_compute_serves_failed_outcome_verbatim`
  (`apps/backend/tests/test_health.py`) + `apps/frontend/lib/background-compute-last-outcome.{ts,test.ts}`
  (evaluator re-ran it: 2 passed). Never trigger a live memory-pressure failure to re-prove it.
- `reports/goal-session-ops-hardening-demo.json` J-09 steps n=13-16 — written and verified (iter-25).
- Byte-frozen unless the planner lifts it ON PURPOSE for the blocker above: `app.engine.forward_testing`,
  `compute_readiness`, `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, J-08's serving split.
- Never launch a second concurrent pytest (the 30-year `loaded_engine` fixture costs 1h+ and starved the
  backend in iter-25). QA must trigger background compute on a date that ALREADY has a snapshot — never a
  never-scanned one: that is what caused both blockers above.
