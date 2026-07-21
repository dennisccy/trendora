# Iteration State — ops-hardening

**After iteration:** 8 · **Date:** 2026-07-22 · **Verdict:** CONTINUE

## Journeys

0 passing · 1 regressed (J-05) · 3 unknown (J-01 J-03 J-04 — lanes never ran) · 1 partial (J-06) — 5 total

## Active blockers

- **iter-8 verified NOTHING (dev).** browser-qa skipped on `Frontend Present: no`
  (`...-iter-8-ui-test-results.md` = "SKIPPED"; `status.json browser_checks_run: false`; no evidence dir,
  no raw `.llm.md`). J-01/J-03 replay + J-04 LLM never ran — hence three `unknown`. Closure =
  CLOSURE-FAIL; audit V1/V2 concur.
- **J-05 unproven (dev).** Fix is real (`data_manager.py:3049/3143/3186/3245` + audit B1 `:3067-3068`,
  10 injected-MemoryError tests, live 468/468 health polls, 43.6% VmPeak margin) but never
  browser-verified; steps 1-3 have no evidence. Audit V1: do not flip J-05 on this handoff alone.
- **AG-8 unresolved (critical, dev).** perf-budgets.md admits the clean run "never hit enough memory
  pressure to trigger the new branch at all", under host-guard CPU/thread caps absent in iter-7 — gain
  not attributable to the diff.
- **AG-10 gap (minor, dev).** `start-backend.sh` applies only `ulimit -v` + `MALLOC_ARENA_MAX`;
  `dev.sh` applies none — no `taskset`/BLAS-OMP caps from `host-guard.env`. goal.md schedules it next.
- Budget: `max_iterations: 9` — iteration 9 is the LAST; make it a pure verification/compliance closeout.

## Last 2 verdicts

- iter 8: CONTINUE — real, audited backend fix but zero journey verification ran; nothing moved
  passing->failing and every unblock path is agent-owned, so neither REGRESSION nor STALLED.
- iter 7: REGRESSION — J-05 passing->failing (7+ min `/api/health` hang + worker `MemoryError` at the
  6144 MB cap during back-to-back heavy ingest); acknowledged, iter-8 dispatched to recover.

## Do not redo

- Four-loop `MemoryError` early-abort + `aggregates_refreshed` honesty gating
  (`apps/backend/app/engine/data_manager.py:3049, 3143, 3186, 3245`) — done, unit-proven.
- Audit B1/T1/T2/T3 repairs (post-bar-cache release; TC-17 assertions restored; byte-offset logfile
  slice; heavy test opt-in via `TRENDORA_RUN_HEAVY_INGEST_TEST=1`) — verified.
- iter-7's `/evidence` `drawdown_expectations` warm — genuinely fixed (22.4 ms), byte-identical.
- `readiness.py`/`main.py` boot/`warmup.py`, `max_range_days`/`snapshot_cadence`/range-cap — settled.
- Raising `server.memory_cap_mb` as a workaround — considered and rejected (assumptions.md, iter-8).
