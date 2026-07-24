# Iteration State — ops-hardening

**After iteration:** 17 · **Date:** 2026-07-24 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-05 replayed; **J-04 CARRIED — UT-J-04 SKIPPED, not re-verified live since iter-14**) · 3 partial (J-06 J-07 J-08) — 7 total

## Active blockers

- **/backtest ≤1.5s serving-budget (dev → operator → owner): the one thing between J-06/J-07/J-08 and passing.** 11/68 breaches, max 12.655s, all in the ingest window on a stored-row read — UNDIAGNOSED (thermal + single-txn ruled out; SQLite-writer vs GIL/threadpool indistinguishable, `logs/backend.log` has zero per-request timestamps). Next: **dev** adds per-request timing instrumentation → **operator** re-runs TC-10 (AG-10-class) → bounded fix, or **owner** amends the budget (logged, never silent). `reports/perf-budgets.md` iter-17 section.
- **Fresh live J-04 kill/restart replay (operator)** — required before any GOAL_ACHIEVED; iter-17 did only TC-11 steady-state sanity (health 200/ready, no crash banner). J-04 code surface byte-unchanged.
- Non-blocking cheap wins (dev): project metadata columns before reading payloads in the widened fallback query (audit B1); one endpoint-level test carrying an OLDER `evidence_asof` (audit T1).

## Last 2 verdicts

- iter 17: CONTINUE — B1 cross-asof_key fix + 2 first-ever live states (TC-09/TC-07) landed & verified; journeys held partial by latency that is undiagnosed (agent instrumentation), NOT a proven hard cost → not STALLED.
- iter 16: CONTINUE — J-08 precompute-before-serve redesign landed `partial` on 3 agent-owned gaps.

## Do not redo

- **B1 cross-asof_key fallback** (`forward_testing.py` resolver) — DONE + correct, 15 unit tests, AG-5 strictly-older SQL-verified, AG-3 byte-identical. Never add a compute branch to the read path; never revert cutover pruning to per-horizon deletion.
- **`compute_forward_aggregates` body** — byte-unchanged since iter-14 (AG-8 resolved). Not reopened. The new widened query is bounded by distinct-as-of count, not the deep basis — not an AG-8 violation.
- **`evidence_asof`** served identically by /api/backtest + MCP + its blueprint.md Data Contract row; F1 fix (`page.tsx:258-261` `asofDate={evidence_asof ?? asof_date}`) — keep.
- **Live not_yet_computed (TC-09) + refreshing banner w/ evidence_asof (TC-07)** — captured & verified; don't re-capture.
- **TC-8 live cross-boundary capture** — unproducible on this seed (max date 2026-07-22); evaluator accepted the unit + client-render floor. Do NOT chase it as a blocker (needs an owner data cycle).
- **Out of bounds:** `main.py`, `app/api/health.py`, `app/engine/readiness.py`, `warmup.py`, `scripts/*`. No full pytest; `loaded_engine` ~80min — cite, don't run. Heavy passes: `scripts/start-backend.sh` only, `taskset -c 0-3,8-11`, BLAS/OMP=4 (AG-10). Carried unrelated: `test_db.py::test_create_all_produces_expected_tables`.
