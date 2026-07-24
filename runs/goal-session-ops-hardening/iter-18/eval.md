# Iteration 18 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This DIAGNOSE-FIRST lean iteration delivered its one key deliverable and it is strong: per-request
phase-broken-down timing instrumentation landed on `GET /api/backtest` + MCP `query_backtest`, and the
operator TC-9 re-measurement (966 concurrent requests, host-guard-confined via `start-backend.sh`)
DEFINITIVELY pinned the previously-undiagnosed `/backtest` latency mechanism — `backfill_run_forward_returns`,
the create-once forward_returns SQLite INSERT on the read path, is 82.2% of each slow request under
concurrency (881 ms vs ~175 ms single-threaded) while the pure-read resolver stays flat at 9.6 ms: SQLite
single-writer contention, NOT GIL/threadpool scheduling. But by design no journey crosses to passing — the
fix was explicitly deferred to the next iteration, so J-06/J-07/J-08 stay `partial` on the un-remediated
ingest-window budget breach. Two cheap wins (deferred-`payload_json` fallback, byte-identical per TC-6; new
endpoint-level cross-`asof_key` test) landed and were verified; 28/28 scoped tests green, review
PASS_WITH_NOTES, coherence COHERENCE-PASS, scan CLEAN. Progress made + a concrete agent-owned next step → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Golden replay UT-J-01 PASS; evaluator opened `reports/qa/goal-ops-hardening-iter-18-evidence/J-01-verify.png` (Data Manager coverage tiles populated) |
| J-03 | passing | passing | Golden replay UT-J-03 PASS; `reports/qa/goal-ops-hardening-iter-18-evidence/J-03-verify.png` |
| J-04 | passing | passing (CARRIED, last_verified LEFT at iter-15) | UT-J-04 SKIPPED (Chrome MCP infra wedge, no token); non-disruptive health 200/ready (perf-budgets TC-10 note); code surface byte-unchanged (not in 5-file diff). Fresh DISRUPTIVE replay still OWED |
| J-05 | passing | passing | Golden replay UT-J-05 PASS; evaluator opened `.../J-05-verify.png` (immutable 2025-05-15 stored snapshot, breadth 87.70%) |
| J-06 | partial | partial | TC-9 diagnosis in `reports/perf-budgets.md` iter-18 section + `runs/goal-ops-hardening-iter-18/tc9-backtest-poll.csv`; ingest-window breach un-remediated (fix deferred by spec) |
| J-07 | partial | partial | TC-9: 966/966 HTTP 200, health truthful, VmPeak capped, no wedge; shared budget blocker un-remediated |
| J-08 | partial | partial | TC-6 byte-identical served evidence (reviewer + coherence); held by the shared step-2 budget breach, not by any evidence-correctness gap |

No status changed this iteration; the deterministic replay lane (3/3 PASS) covered the required-still-passing
golden set (J-01/J-03/J-05), and 2 stable spot-checks (J-01, J-05 screenshots opened) corroborated recorded
status.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (proven-language) | OK | No evidence-claim language added; timing lines are internal ops data, never served (coherence: not a Data Contract value) |
| AG-2 (decision-quality only) | OK | No return promises/signals/orders introduced |
| AG-3 (displayed numbers correct) | OK | TC-6 byte-identical served evidence; reviewer + coherence + 28/28 tests confirm the returned dict is unchanged |
| AG-4 (no overfit edges) | OK | N/A — no proven claims this iteration |
| AG-5 (no-lookahead) | OK | Widened-fallback filter direction (`asof_key < asof_key`, strictly older) UNCHANGED; the deferred-payload refactor does not touch it (TC-6/coherence) |
| AG-6 (referee gate) | OK | N/A — no evidence-derived claims |
| AG-7 (no hard-coded creds) | OK | scan-report CLEAN; diff adds only `logging`/`time`/`datetime` imports + helpers, no config/env/secret files |
| AG-8 (resilience / no unbounded ORM) | OK | `compute_forward_aggregates` byte-unchanged; the deferred-payload query reads FEWER bytes (bounded by distinct-as-of count); coherence COHERENCE-PASS one producer; TC-9 VmPeak stayed capped, 966/966 HTTP 200 |
| AG-9 (offline-deterministic ingest) | OK | No external network / adapters / new deps (dev handoff + scan-report confirm) |
| AG-10 (host resource ceiling) | OK | TC-9 launched via `scripts/start-backend.sh`, /proc-verified caps (affinity 0-3,8-11, 6144 MB, MALLOC_ARENA_MAX=2, OMP=4), thermal peak 85 °C < 95 °C. No `scripts/` file in diff. TC-10 ingest trigger was BLOCKED by the AG-10 safety classifier and the operator did NOT work around it (fail-closed — respecting the guardrail, the opposite of a violation) |

scan-report CLEAN (secrets/deps/license). No new anti-goal violation this iteration; all 10 historical records
stay `resolved: true`.

## Next-Step Recommendation

FULL depth, no new features — apply the now-diagnosed latency fix (the one item between J-06/J-07/J-08 and
`passing`). AGENT (well-specified by TC-9): take the create-once `backfill_run_forward_returns` INSERT OFF the
per-request serving path — either precompute it at ingest (the J-05/J-08 compute-at-ingest principle already
applied to aggregates) OR guard it with a cheap read-only existence check so the single-writer lock is taken
zero times when forward_returns already exist; that should collapse the 881 ms phase to the ~10 ms read floor
and bring 6× concurrent `/backtest` under budget even during an ingest window. This touches the shared
serving/write path with real correctness surface (byte-identity, AG-8, AG-5, create-once idempotency, and the
exact under-concurrency behavior that produced iter-13's REGRESSION on this cluster) — recommend full so audit
+ closure re-verify it; and because success here plausibly closes the whole goal, it warrants the full
pipeline's rigor before the two-key confirm. NB: an advisory full recommendation was overridden into a lean
dispatch last iteration (iter-17→18), so weigh this deliberately.

OPERATOR / OWNER items that HARD-BLOCK GOAL_ACHIEVED regardless of the fix:
1. Fresh live DISRUPTIVE J-04 kill/restart replay (TC-10, owed since iter-15) — needs explicit owner go-ahead
   for the ingest trigger the session's AG-10 safety classifier currently blocks; the non-disruptive sanity
   check is not a substitute.
2. Chrome MCP browser infra is wedged (port 9224 never ready) — the deterministic replay lane worked (3/3),
   so this iteration was unaffected (backend-only), but the fix iteration WILL need a live `/backtest`
   browser verification; fix the MCP server before/during it or it becomes a real blocker.

## Halt Justification (if halting)

N/A — not halting. CONTINUE. Decision tree trace: C.1 no (no journey passing→failing; no unresolved critical
anti-goal — scan CLEAN, coherence PASS, TC-10 non-run is a fail-closed honest gap, not a violation); C.2 no
(the blocker's next step — apply the diagnosed fix — is agent-owned and well-specified, not human-owned, so
NOT STALLED); C.3 no (J-06/J-07/J-08 partial → GOAL_ACHIEVED off the table); C.4 no (no failing journey,
review PASS_WITH_NOTES so no fail-open, and the iteration cleanly succeeded rather than surfacing new
cross-cutting ambiguity) → C.5 CONTINUE.
