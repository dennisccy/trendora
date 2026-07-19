# Iteration State — ops-hardening

**After iteration:** 0 · **Date:** 2026-07-19 · **Verdict:** CONTINUE

## Journeys

0 passing · 1 partial (J-04) · 4 failing (J-01 J-03 J-05 J-06) — 5 total. All newly measured this baseline; none passing yet (honest starting line, no code changed).

## Active blockers

- Load-bearing dev work (not a human blocker): the cadence gate `_cadence_allowed_dates` in `apps/backend/app/engine/data_manager.py` `_do_backfill` (~:2496) filters explicit backfill requests, so J-01 & J-05 both compute `dates_total=0`. "Requested range always wins" must land before either can be exercised.

## Last 2 verdicts

- iter 0: CONTINUE — baseline verify-only; all 5 journeys fail as an honest measurement, no code changed, none regressed, no anti-goal introduced.
- iter -1: n/a — first evaluated iteration.

## Do not redo

- Baseline measurement is complete — do not re-run iter-0 verification; results are seeded in `journey-history.json`.
- J-04's boot speed (first 200 at 0.909s), phase-aware "Initializing… n/m" badge, distinct "Backend unavailable"/NO-GO crash presentation, and interrupted-job-after-restart already WORK live (mcp-loop iter-28/33) — build ONLY the persistent logfile + `ulimit`/`MALLOC_ARENA_MAX` enforcement in `scripts/start-backend.sh`, not the readiness state machine.
- The 25 mcp-loop journeys are archived (`docs/archive/goal-mcp-loop.md`), not tracked here — do not re-verify them.
- J-06: 8/11 page loads + the existing mcp-loop budgets in `reports/perf-budgets.md` already hold — only add the 2 new rows (boot time, cold `/api/data`) + the code-audit statement + fix the 3 heavy-aggregate pages (`/data` `/evidence` `/backtest`, same coverage-cache root cause as J-05).
- `docs/goal.md` is lint-final (commit 9c98cb3) — do not edit it.
