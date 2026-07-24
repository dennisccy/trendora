# Iteration State — ops-hardening

**After iteration:** 19 · **Date:** 2026-07-24 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-05 golden-replayed this iter; J-04 CARRIED, last_verified iter-15, disruptive replay OWED) · 3 partial (J-06 J-07 J-08) — 7 total. The forward_returns request-path blocker that held the three partial since iter-11 is now FIXED; two NEW/residual gaps below keep them partial.

## Active blockers

- **`ensure_loop_ms` cold-first-view stall on `/backtest` (J-06/J-08), owner=dev:** the FIRST view of a historical as-of sits 9.6-54s on an empty NO-affordance skeleton, then renders real values (audit F1; UT-04-historical-wait-check.png). A SEPARATE subsystem from iter-19's fix (`backfill_forward_returns_ms` stayed 12-80ms, write_taken=False on those reqs). FIX (agent-tractable): add an honest progress affordance + take the cold ensure_loop scan off the request path (the compute-at-ingest/serve-from-storage pattern already applied to the forward path).
- **TC-7 concurrent-INGEST overlay UNMEASURED (J-06/J-07), owner=human:** the ≤1.5s budget is proven only under pure reads; the actual historical breach condition (concurrent ingest, 11/68 @ 12.655s) needs owner go-ahead for the AG-10-blocked ingest trigger. Mechanism strongly predicts it holds — but verify live, don't extrapolate.
- **Fresh live DISRUPTIVE J-04 kill/restart replay, owner=human:** owed since iter-15 (same ingest-trigger gate); hard GOAL_ACHIEVED precondition. TC-8 non-disruptive sanity is not a substitute.

## Last 2 verdicts

- iter 19: CONTINUE — un-elapsed-horizon short-circuit FIXED the create-once forward_returns storm (TC-6 877→13.9ms, 63×, 0/4793 breaches, evaluator-recomputed CSV; byte-identity AG-3 proven), but ensure_loop_ms cold path + unmeasured TC-7 keep J-06/J-07/J-08 partial.
- iter 18: CONTINUE — diagnose-first: pinned the breach to backfill_forward_returns_ms SQLite-writer contention (82.2%); no fix by spec.

## Do not redo

- The forward_returns request-path latency fix — DONE (un-elapsed-horizon short-circuit in `backfill_run_forward_returns`; attempts 1-2 skip-commit + column-projection were INERT — do NOT retry them).
- `compute_forward_aggregates` body / compute-vs-serve split / resolver cross-`asof_key` fallback — untouched, byte-unchanged; do NOT reopen (iter-14/16/17). Keep ONE producer/ONE resolver (coherence contract).
- J-08 step-4 zero-aggregate-compute + step-5 empty state — PROVEN (TC-1..TC-5); residual is the ensure_loop cold path, not aggregate serving.
- Out of bounds: `main.py`, `health.py`, `readiness.py`, `warmup.py`, `scripts/*`. Heavy passes via `scripts/start-backend.sh` only (taskset 0-3,8-11, BLAS/OMP=4, AG-10); no full pytest; `loaded_engine` ~80min cite-don't-run.
- Carried non-blocking: B3 autoflush IntegrityError hazard in `_insert_run_forward_returns` (own iter, risky on iter-13 cluster); `test_db.py::test_create_all_produces_expected_tables` pre-existing failure — carried, not new.
