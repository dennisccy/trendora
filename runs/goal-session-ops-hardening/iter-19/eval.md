# Iteration 19 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The iter-19 fix is real and I verified it independently: the un-elapsed-horizon short-circuit in
`backfill_run_forward_returns` collapses the request-path forward-returns phase from 877 ms to a personally
re-tallied **13.9 ms mean / 73 ms max under 6× concurrency** (TC-6 CSV: 4793 requests, 0 non-200, 0 breaches,
mean 112 ms, max 302 ms) with byte-identity preserved three ways — closing the create-once-INSERT contention
that held J-06/J-07/J-08 partial since iter-11. But it does **not** close those three journeys: (a) browser-QA
UT-04, which I opened, shows a **separate** cold-recompute subsystem (`ensure_loop_ms`) still stalls the FIRST
`/backtest` view of a historical as-of on an empty, no-affordance skeleton for 9.6–54 s — literally "a skeleton
waiting on a fresh compute" (J-08 step 2); and (b) TC-7, the concurrent-ingest overlay that is the *actual*
historical breach condition (11/68 @ 12.655 s), was never measured (AG-10 ingest-trigger blocked), so the
≤1.5 s budget is proven only under pure reads. Progress made, no regression, no anti-goal violated, coherence
PASS, and the next blocker is agent-tractable → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Golden replay UT-J-01 PASS (regression-replay 3/3); spot-checked `reports/qa/goal-ops-hardening-iter-19-evidence/J-01-verify.png` (/data coverage 1996→2026, universe 540) |
| J-03 | passing | passing | Golden replay UT-J-03 PASS; `reports/qa/goal-ops-hardening-iter-19-evidence/J-03-verify.png` |
| J-04 | passing | passing (CARRIED, last_verified LEFT at iter-15) | TC-8 non-disruptive sanity: `/api/health` 200/ready, no new crash banner (QA report Step 3.5). UT-J-04 SKIPPED (disruptive kill/restart is a blocked service action; no golden). Disruptive replay still owed since iter-15. |
| J-05 | passing | passing | Golden replay UT-J-05 PASS; spot-checked `reports/qa/goal-ops-hardening-iter-19-evidence/J-05-verify.png` (immutable 2025-05-15 snapshot, "never recomputed for today") |
| J-06 | partial | partial | TC-6 budget holds under pure reads only (perf-budgets.md iter-19 attempt-3; CSV re-tallied 0/4793 breaches). Held partial by F1 `ensure_loop_ms` cold-view stall + unmeasured TC-7. `UT-04-historical-wait-check.png` |
| J-07 | partial | partial | Core AG-8 availability/memory holds (resolved iter-14, `compute_forward_aggregates` byte-unchanged). Serve-responsiveness under the ingest window (TC-7) unmeasured — AG-10-blocked. |
| J-08 | partial | partial | Forward-AGGREGATE serving is request-path-compute-free (TC-1..TC-5, reviewer+QA+audit). But a cold recompute on a `/backtest` request remains on a different path: `UT-04-historical-wait-check.png` (empty skeleton) → `UT-04-historical-recheck.png` (real values), 9.6–54 s `ensure_loop_ms` (audit F1) |

Statuses set from this iteration's evidence: J-01/J-03/J-05 `passing` (last_verified→iter-19), J-06/J-07/J-08
`partial` (re-evaluated this iteration, last_verified→iter-19). J-04 carried `passing` (last_verified LEFT at
iter-15 — no fresh evidence; established iter-16/17/18 precedent). No journey moved passing→failing; no journey
newly failing; none regressed.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked proven/confident) | OK | Backend-only write-elimination; no proven-language; UT-01 shows honest NA ("No numbers are fabricated", all-"—" at latest) |
| AG-2 (decision-quality only) | OK | No return promises/orders; a latency fix |
| AG-3 (displayed numbers correct) | OK | Byte-identity proven by construction (strict upper bound) + full-column unit assertion + TC-2 (MCP==API) + TC-5 + all 4793 responses `ready` + UT-03 DOM byte-diff. The load-bearing property, proven thoroughly |
| AG-4 (no overfit edges) | OK | N/A — no evidence claims (goal loop mechanics: J-01..J-06 carry none) |
| AG-5 (no-lookahead) | OK | `observable_days` counts only `date > run.asof_date`; audit B2 confirms never a bar ≤ D |
| AG-6 (referee gate) | OK | N/A — no evidence-derived claims this iteration |
| AG-7 (no credentials) | OK | scan-report CLEAN; audit B2 confirms no keys/tokens |
| AG-8 (data-scale resilience, no unbounded ORM) | OK (strengthened) | Fix REDUCES work; `observable_days` is `LIMIT max_h` (≤60 rows) over `ix_daily_prices_date` covering index; bounded to one run's rows; audit B2 confirms not whole-table |
| AG-9 (offline-deterministic ingest) | OK | No ingest triggered; TC-7 blocked by AG-10 classifier and NOT worked around (fail-closed); scan CLEAN, no network/paid dep |
| AG-10 (host resource ceiling) | OK | TC-6 via `scripts/start-backend.sh`, /proc-verified caps (affinity 0-3,8-11, 6144 MB, MALLOC_ARENA_MAX=2, OMP=4), hwmon sampler live, watchdog armed, peak 89 °C < 95 abort; no `scripts/` file in the diff (coherence) |

No new anti-goal violation. All 10 historical records stay `resolved: true`. Coherence: **COHERENCE-PASS**
(control-flow change inside the one existing producer; `write_taken` is a log-only field never in the response;
no new function/route; `compute_forward_aggregates` untouched — grep zero hits).

## Next-Step Recommendation

**FULL depth, no new features.** The primary blocker's mechanism is genuinely resolved; two documented gaps
remain, and the first is agent-tractable:

1. **AGENT (the item between J-06/J-08 and passing): the `ensure_loop_ms` cold-first-view stall on `/backtest`
   (audit F1, ux-regression).** A first navigation to a not-yet-served historical as-of sits on empty skeletons
   for 9.6–54 s with **no loading affordance**, then renders real values. Two parts: (i) give it an honest
   progress/initializing affordance so it is never a blank/frozen skeleton (J-06/J-08 honest-status clause,
   `never a frozen or blank frame`); and (ii) take the cold historical `ensure_loop` scan off the request path
   (precompute/create-once with the same compute-at-ingest, serve-from-storage pattern iter-16–19 applied to the
   forward path) so a `/backtest` request never triggers a multi-second cold recompute (J-08 `never a cold
   recompute on request`). This is a frontend + serving-path change → UI chain warranted, hence full.
2. **OWNER-gated: TC-7 ingest-overlay re-measurement.** The ≤1.5 s budget is proven only under pure concurrent
   reads; the actual historical breach condition (concurrent ingest holding the writer lock, 11/68 @ 12.655 s)
   is unmeasured because the AG-10 ingest-trigger classifier blocks it. The fix's mechanism (1106→0 per-request
   fetches) strongly predicts the breach is gone, but this session's own lesson is "trust the live number over
   the extrapolation" — needed before J-06/J-07's budget-under-ingest clause is credited.
3. **OWNER-gated: the disruptive J-04 kill/restart replay** (owed since iter-15; same ingest-trigger gate). A
   hard precondition for any future GOAL_ACHIEVED — the non-disruptive TC-8 sanity is not a substitute.
4. **AGENT non-blocking, carried:** B3 — the pre-existing autoflush `IntegrityError`/`OperationalError` hazard
   inside `_insert_run_forward_returns` (per-symbol-loop autoflush outside the `IntegrityError`-tolerant
   wrapper; reachable under 2+ concurrent callers on a run with 2+ genuinely-missing symbols). Warm path never
   reaches it; risky to fix on the iter-13 REGRESSION cluster — its own iteration, own concurrency-test budget.
   Also: the boot `_backfill` un-elapsed-horizon fetches (`forward_testing.py:487`); and T2 — run the 4 skipped
   regression files (`test_forward_testing.py`, `test_warmup.py`, `test_data_manager.py`, `test_api_backtest.py`)
   off the host-constrained box before treating the DoD "all pre-existing tests pass" bullet as closed.

## Halt Justification (if halting)

N/A — CONTINUE. Not GOAL_ACHIEVED (J-06/J-07/J-08 partial). Not REGRESSION (no passing→failing; no anti-goal
violated; byte-identity preserved). Not STALLED (unlike iter-15, the current blocker has a concrete
agent-owned next step — the `ensure_loop_ms` cold-path fix + affordance — so not *every* unblock path is
human-owned; TC-7/J-04-disruptive are owner-gated but are not the sole residual). Not ESCALATE (already full
depth; review PASS, no fail-open; no journey failed twice).
