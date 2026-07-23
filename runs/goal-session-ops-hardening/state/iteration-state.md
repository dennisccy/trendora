# Iteration State — ops-hardening

**After iteration:** 16 · **Date:** 2026-07-23 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-05 replayed; **J-04 CARRIED — UT-J-04 SKIPPED, not re-verified since iter-14**) · 3 partial (J-06 J-07 J-08) — 7 total

## Active blockers

- **B1 (dev) — the one thing between J-08 and passing.** `resolved_forward_aggregate_evidence` resolves all 3 states inside ONE `asof_key` (`apps/backend/app/engine/forward_testing.py:1209`) while the default view resolves to the latest run (`app/api/backtest.py:70`) — so the *common single-latest-date* ingest serves `not_yet_computed` (empty evidence) instead of the labeled last-good J-08 step 2 promises. **Evaluator RULED the fallback must cross as-of boundaries** (label the served as-of; reserve the empty state for fresh-install). Zero unit or live coverage today.
- **Browser evidence (dev):** `not_yet_computed` never rendered (UT-03 SKIPPED) — use a DISPOSABLE copy of `trendora.db`, never the working one. The corrected refreshing banner (`apps/frontend/app/backtest/page.tsx:270-276`) is un-screenshotted; the only artifact shows the false pre-fix copy.
- **Latency (dev):** 11/68 live polls breach the committed ≤1.5s `/backtest` budget (max 12.655s), all inside the ingest window on a *stored-row read* → writer/reader contention, not compute (`reports/perf-budgets.md:2827-2831`). Owner may instead amend the budget — logged, never silent.
- **Human/operator:** live J-04 kill/restart replay (required before any GOAL_ACHIEVED); one `loaded_engine` test (T1); a fresh `demo.sh --session-live` run (iter-14's predates J-08's `[NEW]` steps).
- Non-blocking: B3 `evidence_generated_at` serialized naive vs its "ISO 8601 UTC" contract; B2 sticky `refreshing` (no self-heal); B5 historical branch deserializes every payload twice.

## Last 2 verdicts

- iter 16: CONTINUE — J-08's architecture is real and verified (cold recompute gone: 178.74s → 12.655s worst read; 68/68 HTTP 200, exactly 2 generations, never mixed), but B1 + the budget breach + missing browser evidence keep J-08 `partial`, so J-06/J-07 stay `partial` too.
- iter 15: STALLED — single-flight fix correct but the 178.74s cold MISS was a hard cost; all unblock paths owner-owned. Owner answered with J-08 (redesign), **not** a budget amendment — ≤1.5s still binds as written.

## Do not redo

- **The compute-vs-serve split** — `forward_aggregates_ingest_cached` is the SOLE caller of `compute_forward_aggregates`; `resolved_forward_aggregate_evidence` has no compute branch. Extend, don't re-architect.
- **`compute_forward_aggregates` body** — byte-unchanged since iter-14 (AG-8 resolved). Not reopened.
- **Completeness-gated cutover pruning** (`forward_testing.py:1126-1155`) — closes the confirmed-live mixed-`dataset_version` bug; never revert to per-horizon deletion. iter-15's single-flight guard survives it (TC-17).
- **J-06's other clauses** (10 idle-host page budgets, ≤5s boot, on-load audit for non-`/backtest` pages) — settled iter-9/11/13.
- **Out of bounds:** `main.py`, `app/api/health.py`, `app/engine/readiness.py`, `warmup.py`, `scripts/*`, `scripts/automation/*`. No full pytest suite; `loaded_engine` ~80 min — cite, don't run. Heavy passes: `scripts/start-backend.sh` only, `taskset -c 0-3,8-11`, BLAS/OMP=4 (AG-10).
- Carried unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing).
