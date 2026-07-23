# Iteration 15 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The agent-tractable item iter-14 named — root-cause and fix `/backtest`'s 211.8 s
concurrent cache-miss (UT-04) — is genuinely DONE: a correctly-scoped, byte-identity-preserving
single-flight de-dup in `forward_aggregates_cached` (root cause measured, not guessed: 5 concurrent
same-key MISSes 9.91x → 1.04x on a 60k-row fixture; `compute_forward_aggregates` untouched). But the
one operator-supervised deep-basis pass proves the fix does NOT close the ≤1.5 s `/backtest` budget:
the live cold MISS is still **178.74 s (WARN, ~119x over)** plus an unflagged **5.37 s** second breach.
The residual is definitively characterized (audit B1/B2, dev, QA all concur) as ONE cold full-basis
`compute_forward_aggregates` pass — an inherent cost a wrapper-scoped fix cannot reduce; stacking was
only ~15.6% of the deep-basis finding. No journey regressed, no anti-goal is violated, coherence is
PASS — but every remaining path to closing J-06/J-07 is now a human-owned product-direction decision
(affordance / precompute-before-serve redesign / accept-and-amend the budget), exactly the escalation
the spec reserved for the owner. There is no further "fix the bug" agent work.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Golden replay UT-J-01 PASS (ui-test-results.md); spot-checked `J-01-verify.png` |
| J-03 | passing | passing | Golden replay UT-J-03 PASS; no J-03 code touched (diff = `forward_testing.py` + 1 test file) |
| J-04 | passing | passing (carried + steady-state sanity) | UT-J-04 PASS; opened `UT-J-04-carryforward-sanity.png` (`/data` Ready badge, coverage populated); J-04 code byte-unchanged this diff |
| J-05 | passing | passing | Golden replay UT-J-05 PASS; opened `J-05-verify.png` (immutable stored snapshot as-of 2025-05-15, Regime 70.76 Risk-on, served from storage) |
| J-06 | partial | partial | `reports/perf-budgets.md` TC-4 = 178.74 s WARN (~119x over ≤1.5 s) + 5.37 s spike; opened `UT-01-result.png` — `/backtest` renders fully & honestly (Ready, all 5 horizons "— n=0", "No numbers are fabricated"), so honest-status clause holds but the budget clause fails |
| J-07 | partial | partial | Same TC-4 pass; TC-6 health 498/500 HTTP 200 (2 isolated 4 s client-cutoffs, self-recovered, no wedge); VmPeak 4.00 GB = 36.3% margin, zero MemoryError |

No journey changed status. Passing-journey screenshots spot-checked (J-05, J-04) both corroborated their
recorded status; no contradiction, so no widened walk needed.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (unbacked proven-language) | OK | No proven-language added; `/backtest` shows honest NA ("No numbers are fabricated", `UT-01-result.png`) |
| AG-2 (return promises / orders) | OK | None; pure backend concurrency handling |
| AG-3 (displayed numbers correct) | OK | Byte-identity preserved — `compute_forward_aggregates` body untouched (diff hunks; audit §3; 32/32 streaming test); TC-1 all N callers byte-identical |
| AG-4 (overfit edges) | OK | N/A this iteration |
| AG-5 (determinism / no-lookahead) | OK | De-dup changes WHO computes, not WHAT; coherence COHERENCE-PASS |
| AG-6 (evidence claim w/o referee) | OK | No evidence-derived claims (pure ops work) |
| AG-7 (hardcoded credentials) | OK | `scan-report.md` CLEAN; no config/env files in diff |
| AG-8 (data-scale resilience / unbounded ORM / OOM / crash) | OK (resolved iter-14, stays resolved) | Fix adds no whole-table ORM load; streamed producer unchanged (audit §3). TC-4: VmPeak 36.3% margin, zero MemoryError, health 498/500, no wedge/crash. 178.74 s is latency, not exhaustion. WATCH: VmPeak grew +66.6% vs iter-14 (margin 61.8% → 36.3%) — under cap, not a violation |
| AG-9 (offline-deterministic ingest) | OK | No live network / paid data; scan-report CLEAN (no new deps) |
| AG-10 (host resource ceiling) | OK | One heavy pass operator-supervised via `scripts/start-backend.sh`, host-guard caps active (taskset 0-3,8-11, BLAS/OMP=4, sampler+watchdog); tests confined. Thermal peaked 84 °C < 95 °C trip (no trip). The 84 °C-vs-64 °C REPORTING gap is a measurement-integrity item, not a cap breach |

No anti-goal violated (critical or minor) this iteration.

## Next-Step Recommendation

Halt for an OWNER decision on the `/backtest` cold-MISS residual (see Halt Justification). Once the owner
picks a direction, resume at **full** depth (shared-infrastructure / cross-cutting change; whatever
direction is chosen — a frontend affordance or an architectural precompute redesign — warrants the full
audit/closure/ux-regression pipeline). No new feature work; the decomposer should carry the binding
"Do not redo" list (the single-flight fix, AG-8 resolution, byte-identity, `HOST_GUARD_REQUIRE_MARKERS`).

## Halt Justification (STALLED)

C.1 does not fire (no journey moved passing→failing; AG-8 resolved iter-14 and stays resolved — the fix
introduces no unbounded load, no crash, no OOM). C.3 (GOAL_ACHIEVED) is barred: J-06 and J-07 are
`partial`, not `passing`. So the tree reaches C.2, and it matches: **every unblock path for the current
blocker is a human-owned decision.**

The blocker is the ≤1.5 s `/backtest` budget breach under a concurrent ingest warm (178.74 s cold MISS +
a 5.37 s spike, `reports/perf-budgets.md` TC-4). The single agent-tractable item iter-14 identified is
complete and correct; its own live evidence proves the dominant residual is one cold full-basis compute a
wrapper-scoped fix cannot reduce (dev root-cause + audit B1/B2 reconciliation + QA #1). The spec's own
escalation flag anticipated exactly this ("if the latency is a hard architectural limit a targeted fix
cannot meaningfully reduce... name it plainly as a scoped finding for the evaluator/owner rather than
forcing an inadequate fix — 'accept this as a permanent constraint and add a `/backtest` affordance
instead' is an owner call"). The pump note, audit §5, and QA #3 all independently route this to the owner.

**Owner unblock options (pick one direction, then `--resume`; edit `docs/goal.md` where noted):**
1. **Add a `/backtest` elapsed-time/progress affordance** (the deferred iter-16 candidate) so the cold
   concurrent MISS shows honest progress — then read J-06/J-07's "honest status" clause as satisfied and
   the ≤1.5 s budget as governing warm loads only (which pass: `UT-01` 116.9/554.1 ms). Agent-implementable
   once chosen; may need a one-line goal.md wording note.
2. **Authorize a precompute-before-serve / incremental-aggregate redesign** so `GET /api/backtest` never
   eats a cold full-basis compute on the request path (aligns with the goal's own "compute at ingest, serve
   from storage, never recompute on a request path"). Larger architectural change — agent-implementable but
   a genuine direction call, not to be started silently.
3. **Accept the deep-basis cold-MISS as a disclosed constraint** — amend the committed `/backtest` budget
   in `reports/perf-budgets.md` (a conscious, logged budget change, never a silent loosening) and/or read
   J-06/J-07's serve-responsiveness clause as met by "stacking fixed + honest skeleton + warm-path fast".
   Under this reading the evaluator can score J-06/J-07 `passing` next iteration and the session reaches
   GOAL_ACHIEVED — but this is the owner's acceptance to grant, not the evaluator's to assume (goal Success
   Criteria commit to "page loads stay within committed never-regress budgets"; iter-12 precedent, human-
   ratified, kept J-06 partial rather than launder a budget breach into a green check).

Non-blocking items to weigh alongside (none closes J-06/J-07 on its own, all owner/operator-owned):
the undiagnosed 5.37 s spike (needs another AG-10 heavy pass to diagnose); the 84 °C-vs-64 °C thermal
reporting discrepancy (reconcile given host crash history); the four unguarded sibling caches
(`event_study_cached`, `market_phase_cached`, `compute_drawdown_expectations_cached`,
`index_series_cached_with_status` — out of scope, no live symptom, future decomposer should reuse this
iteration's single-flight idiom if it patches any). The `demo.sh --session-live` walkthrough now has
operator evidence (`runs/goal-ops-hardening-iter-14/operator-session-live-walkthrough.md`, exit 0, all 7
steps) and is no longer a distinct blocker. Carried unrelated: `test_db.py::test_create_all_produces_
expected_tables` (pre-existing, no schema change).
