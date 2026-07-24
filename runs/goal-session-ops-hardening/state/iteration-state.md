# Iteration State — ops-hardening

**After iteration:** 18 · **Date:** 2026-07-24 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 3 partial (J-06 J-07 J-08) — 7 total. J-04 passing is CARRIED
(last_verified iter-15; disruptive replay OWED). J-06/J-07/J-08 share ONE blocker (below).

## Active blockers

- `/backtest` ≤1.5s budget breach in the ingest window (J-06/J-07/J-08) — now DIAGNOSED, owner=dev: the
  create-once `backfill_run_forward_returns` SQLite INSERT on the serving path (`apps/backend/app/api/
  backtest.py` ~L81 / `mcp/tools.py`) serializes on the single-writer lock = 82.2% of each slow request
  (TC-9, perf-budgets.md iter-18). FIX (agent-tractable, next iter): move it to ingest OR guard with a cheap
  read-only existence check → collapses 881ms to the ~10ms read floor. NOT yet applied (diagnose-only by spec).
- Fresh live DISRUPTIVE J-04 kill/restart replay (TC-10, owed since iter-15) — owner=human: needs go-ahead
  for the ingest trigger the AG-10 safety classifier blocks. Hard GOAL_ACHIEVED precondition.
- Chrome MCP browser infra wedged (port 9224) — owner=human: harmless this backend-only iter (replay lane
  worked 3/3), but the fix iter needs a live `/backtest` browser check.

## Last 2 verdicts

- iter 18: CONTINUE — diagnose-first lean iter PINNED the latency mechanism (TC-9, 966 reqs); no fix by
  design, so J-06/J-07/J-08 stay partial; next step (apply the fix) is agent-owned. scan CLEAN, coherence PASS.
- iter 17: CONTINUE — B1 cross-asof_key fallback closed in code; budget breach narrowed not pinned.

## Do not redo

- AG-8 resolved since iter-14: `compute_forward_aggregates` bounded/streamed, byte-unchanged — do NOT reopen.
- Instrumentation + deferred-`payload_json` cheap win + TC-7 endpoint test are BUILT (iter-18, 28/28 green,
  TC-6 byte-identical) — the fix iter consumes the timing data, doesn't re-add it.
- TC-8 live cross-boundary capture unproducible on this seed (max dates == 2026-07-22) — settled, not a target.
- Do NOT add a compute branch to the read path; keep one producer / one resolver (coherence contract).
- Out of bounds: `main.py`, `health.py`, `readiness.py`, `warmup.py`, `scripts/*`. Heavy passes via
  `scripts/start-backend.sh` only (taskset 0-3,8-11, BLAS/OMP=4, AG-10); no full pytest, `loaded_engine` ~80min cite-don't-run.
- `test_db.py::test_create_all_produces_expected_tables` failure is pre-existing/unrelated — carried, not new.
