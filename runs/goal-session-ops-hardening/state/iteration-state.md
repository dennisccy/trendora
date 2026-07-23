# Iteration State — ops-hardening

**After iteration:** 15 · **Date:** 2026-07-23 · **Verdict:** STALLED

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 2 partial (J-06 J-07) — 6 total

## Active blockers

- **`/backtest` cold-MISS over budget — OWNER direction decision (halts the session).** Under a concurrent
  ingest warm, the cold cache-MISS is **178.74s** (+ a distinct 5.37s spike) vs the committed ≤1.5s budget
  (`reports/perf-budgets.md` TC-4). The agent-tractable single-flight fix is DONE and correct; the residual
  is ONE cold full-basis `compute_forward_aggregates` pass a wrapper cannot reduce (stacking was only ~15.6%).
  Owner picks: (1) `/backtest` progress affordance + read budget as warm-only; (2) precompute-before-serve
  redesign; or (3) accept/amend the budget (a logged change, never silent) → then evaluator scores J-06/J-07
  passing → GOAL_ACHIEVED. Non-blocking: 5.37s spike undiagnosed; 84°C-vs-64°C thermal report gap; 4 unguarded
  sibling caches; VmPeak +66.6% vs iter-14 (36.3% margin, WATCH).

## Last 2 verdicts

- iter 15: STALLED — single-flight de-dup fix correct but the cold-MISS residual is a hard one-compute cost; all unblock paths owner-owned.
- iter 14: CONTINUE — AG-8 REGRESSION recovered (bounded/streamed rewrite); UT-04 concurrent latency named as the tractable follow-up (now done).

## Do not redo

- Single-flight de-dup in `forward_aggregates_cached` — DONE, tested (TC-1/2/8, `forward_testing.py`); do not re-root-cause the stacking pathology.
- AG-8 unbounded ORM load — RESOLVED iter-14, holds; `compute_forward_aggregates` stays byte-identical (never touch its body/signature/columns).
- `HOST_GUARD_REQUIRE_MARKERS` resolved iter-14 (e5624010); `demo.sh --session-live` walkthrough has operator evidence (iter-14 walkthrough file, exit 0).
- Do NOT touch `main.py` / `app/api/health.py` / `app.engine.readiness` / `warmup.py` or `scripts/automation/*` (binding).
- 10 idle-host J-06 page budgets + ≤5s boot — settled iter-9/11; not a re-measure target.
- Carried unrelated: `test_db.py::test_create_all_produces_expected_tables` (pre-existing, no schema change).
