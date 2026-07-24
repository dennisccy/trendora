# Iteration State — ops-hardening

**After iteration:** 20 · **Date:** 2026-07-24 · **Verdict:** STALLED

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 3 partial (J-06 J-07 J-08) — 7 total. iter-20 closed the last
agent-tractable latency blocker but NO journey crossed to passing — remaining path is owner-owned.

## Active blockers

- **OWNER-owned (the halt is for the owner — pick a direction, then `--resume` at full):**
  (1) authorize the AG-10-gated ingest for **TC-13** — prove `/backtest` ≤1.5 s under the
  concurrent-INGEST overlay (J-08's own step-1-2 scenario; only pure-read proof exists).
  (2) authorize the AG-10-gated ingest for **TC-14** — disruptive J-04 kill/restart replay (owed
  since iter-15; hard GOAL_ACHIEVED precondition; non-disruptive health check is NOT a substitute).
  (3) decide how ≤1.5 s / ≤0.1 s treat the **transient in-process contention** (3.0–6.3 s `/backtest`,
  1.60 s health during the bounded ~30 s background compute; `perf-budgets.md` "Iteration 20") —
  off-process/precompute are spec-rejected, so this is accept-and-log / amend / rescope, not agent work.
- Agent-tractable but closes NO journey alone: oldest-date (2005) ~1.3–1.9 s from `scorecard_ms +
  resolved_run_ms` (`apps/backend/app/api/backtest.py:162-177`, pre-existing, out of iter-20 scope).

## Last 2 verdicts

- iter 20: STALLED — historical ensure-loop moved off-thread (9.6–54 s → 0.082 s, live-verified) but
  NO journey crossed to passing; every remaining path to close J-06/J-07/J-08 is owner-owned (C.2).
- iter 19: CONTINUE — create-once INSERT storm fixed; the ensure_loop cold path was still agent-tractable.

## Do not redo

- Historical `/backtest` cold recompute is OFF the request thread — `ensure_historical_forward_
  aggregates_dispatched` (single-flight background daemon) in `forward_testing.py`, mirrored in
  `mcp/tools.py`. BOTH cold paths off-thread; J-08's literal "never a request-path recompute" met.
- `compute_forward_aggregates` + `resolved_forward_aggregate_evidence` byte-unchanged (ONE
  producer/resolver, coherence) — do NOT touch. Out of bounds: `main.py` `health.py` `readiness.py`
  `warmup.py` `scripts/*`. Frontend refreshing/empty-state copy corrected + live-verified — do not re-audit.
- REJECTED, no re-propose without owner sanction: precompute every historical date (unbounded); remove
  historical lazy create-once (time-machine regression); off-process/precompute contention fix.
- J-01/J-03/J-05 pass by golden replay; J-04 carried (owes disruptive TC-14). Heavy passes via
  `start-backend.sh` only (AG-10); `loaded_engine`/`test_data_manager.py` cite-don't-run (owed off-box).
