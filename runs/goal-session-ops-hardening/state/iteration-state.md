# Iteration State — ops-hardening

**After iteration:** 10 · **Date:** 2026-07-22 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 1 partial (J-06) · 0 failing — 5 total. J-06 is the LAST non-passing Must-have.

## Active blockers

- **J-06 measurement (dev).** 11-page real-browser TTI/on-load sweep + `bash scripts/measure-perf.sh --boot`
  not re-run since iter-6/7 → record in `reports/perf-budgets.md`. The `--boot` run also clears J-04's carried
  WARN (≤5 s budget last measured 2026-07-20, before iter-9 put host-guard into `scripts/start-backend.sh`).
- **`[NEW]` `demo.sh ops-hardening --session-live` walkthroughs for J-05 + J-06 (dev).** Still unproduced;
  J-06's own Acceptance names one. Open since iter-4.
- **AG-8 critical, UNRESOLVED (human scope call).** On-load `GET /api/backtest` → `forward_aggregates_cached`
  MemoryError; hard-blocks GOAL_ACHIEVED. Also human: `HOST_GUARD_REQUIRE_MARKERS` 0→1.
- **AG-10 minor, new (dev).** Agent-run pytest executes unconfined (dev handoff iter-10:74-87; hwmon peak
  91 °C vs the 95 °C watchdog, no trip) — wrap it in the host-guard `taskset`/BLAS env, or amend AG-10.
- **Bookkeeping.** iter-10 `status.json` stuck at `dev_complete`/`browser_checks_run: false` despite a passing
  browser lane; QA/audit/closure not run since iter-9; backend pid 2100030 exited — restart services first.

## Last 2 verdicts

- iter 10: CONTINUE — J-04 partial→passing: run 119 killed mid-flight at 158/504 dates renders `interrupted`
  + `Snapshots: 117` with a non-null breakdown, corroborated by the evaluator against sqlite + `backend.log`.
- iter 9: CONTINUE — J-05 regressed→passing, J-01/J-03 out of `unknown`; J-04 held one step short pending
  exactly the rendered-surface observation iter-10 has now made.

## Do not redo

- **J-04 step 6 — CLOSED.** `_checkpoint_run_record` (`data_manager.py:3677-3712`, iter-9 `5e073cf1`) is
  live-verified end-to-end; do not plan another crash cycle for it.
- **Heavy-ingest test — settled, do NOT re-run** (iter-9: 1092.93 s, 439/439 health-200, VmPeak 24.7 % under cap).
- **Host-guard launcher caps — DONE** in `start-backend.sh` + `dev.sh` backend subshell only; boot banner
  re-verified iter-10 (`cpu_list=0-3,8-11 blas_threads=4`). Never weaken or strip.
- **`/evidence` drawdown warm (iter-7) + `/api/indexes` / `/api/data/availability` fetch-stagger (iter-6)** —
  verified in budget; do not revisit. **Do NOT touch** `health.py`, `readiness.py`, `main.py` boot, `warmup.py`,
  `max_range_days`/`snapshot_cadence`, `server.memory_cap_mb` — all settled.
- **Process:** never hand-edit past iterations' artifacts (iter-7); never patch `scripts/automation/*` (iter-9).
