# Iteration State — ops-hardening

**After iteration:** 21 · **Date:** 2026-07-25 · **Verdict:** STALLED

## Journeys

**5 passing (J-01 J-03 J-04 J-05 J-08)** · 2 partial (J-06 J-07) — 7 total. J-08 CROSSED (TC-13 closed its
one blocker + a live small-single-day ready→refreshing→ready); J-04 freshly re-verified by TC-14.

## Active blockers

- **ONE owner decision, the ONLY thing between here and GOAL_ACHIEVED.** J-06 + J-07 step 2 fail on latency
  alone during the bounded ~30 s HISTORICAL background-compute window: 3.0–6.3 s `/backtest`
  (budget ≤1.5 s), 4/16 `/api/health` samples over ≤0.1 s, max 1.60 s (`reports/perf-budgets.md`
  "Iteration 20", lines 3358 + 3368). Availability is NOT at issue — no wedge; readiness never drops.
  Owner picks: (1) accept-and-log a dated `perf-budgets.md` amendment for reads during a background-compute
  window → next evaluator scores J-06/J-07 passing; (2) sanction an off-process/precompute redesign
  (previously rejected as unbounded); (3) rescope ≤1.5 s/≤0.1 s to steady-state reads.
- **No agent-side fourth option** (verified, not inherited): `/api/health` already uses ~98.6% of its ≤0.1 s
  budget AT REST (`perf-budgets.md:553`) — no bounded pacing creates that headroom. Do NOT plan a mitigation
  iteration; the budget NUMBER must move, and that is owner-owned.

## Last 2 verdicts

- iter 21: STALLED — J-08 + J-04 closed on TC-13/TC-14; sole remaining blocker human-owned (C.2 before C.5).
- iter 20: STALLED — historical ensure-loop moved off-thread (9.6–54 s → 0.082 s) but no journey crossed.

## Do not redo

- **TC-13 + TC-14 DONE and PASS** (2026-07-25, owner-authorized, DB-corroborated) — never re-run. TC-13:
  0/4096 breaches, max 429 ms. TC-14: run 164 `interrupted`, `dates_done 1366/2904` survived `kill -9`.
- **J-08 is PASSING** — all 5 steps evidenced; do not re-open its serving split, resolver, or empty state.
  `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_
  aggregates_dispatched` byte-unchanged, ONE producer/resolver. Out of bounds: `main.py`, `health.py`,
  `readiness.py`, `warmup.py`, `scripts/*`; frontend evidence-state copy live-verified.
- Do NOT remove the `forward_aggregates_ingest_cached` imports (`backtest.py:75`, `mcp/tools.py:38`) — live
  `monkeypatch.setattr(raising=True)` targets for 4 tests; retarget those first.
- REJECTED, no re-propose without owner sanction: precompute every historical date (unbounded); remove
  historical lazy create-once (time-machine regression); off-process contention fix.
- `/backtest` banner is BELOW the fold — full-page capture. Heavy passes via `start-backend.sh` (AG-10).
