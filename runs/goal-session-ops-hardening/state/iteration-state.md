# Iteration State — ops-hardening

**After iteration:** 9 · **Date:** 2026-07-22 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-03 J-05) · 2 partial (J-04 — step 6 only; J-06 — out of scope since iter-7) — 5 total

## Active blockers

- **J-04 step 6 — needs ONE browser-lane kill/restart cycle (dev).** Defect FIXED intra-iteration
  (`_checkpoint_run_record`, `data_manager.py:3668-3708`), proven at API level by the operator
  (`runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`: run 114 = 59 snapshots, 64/84
  dates vs. all-zero pre-fix run 113). Missing: the RENDERED `/data` panel post-fix; then supersede the
  AUDITOR ADDENDUM in `...-iter-9-regression-replay-results.md`.
- **Closure = CLOSURE-FAIL (dev).** The J-04 DoD gap above, plus `reports/qa/goal-ops-hardening-iter-9-qa.md`
  is stale — written 09:30, before the browser lane (12:34) and the heavy run (15:18-15:36); still calls
  that run "DEFERRED" and concludes "ready to move forward".
- **Owner decisions (human).** Deferred on-load `/api/backtest` MemoryError (J-06/AG-8 — recorded
  unresolved critical, hard-blocks GOAL_ACHIEVED); unproduced J-05/J-06 `demo.sh --session-live`
  walkthroughs; `HOST_GUARD_REQUIRE_MARKERS` 0→1; budget (`session.json max_iterations: 9`).
- Watch: VmPeak margin narrowed 43.6%→24.7% — the audit PROVED that is real demand growth, not a sampling artifact (`perf-budgets.md` iter-9).

## Last 2 verdicts

- iter 9: CONTINUE — J-05 recovered and proven live (439/439 health polls 200, VmPeak 24.7% under cap,
  launcher-applied caps); J-01/J-03 out of `unknown`; AG-10 + iter-7 AG-8 resolved; J-04 one step short.
- iter 8: CONTINUE — real audited MemoryError fix, but the browser lane was skipped so it verified nothing.

## Do not redo

- **AG-10 launcher caps — DONE.** HOST-GUARD blocks in `start-backend.sh` + `dev.sh` BACKEND SUBSHELL
  ONLY (never the frontend); values from `host-guard.env`; live-verified on `/proc`.
- **Heavy-ingest measurement — DONE; do NOT re-run** (1092.93s, owner-authorized). CSVs under
  `runs/goal-ops-hardening-iter-9/` + `perf-budgets.md` iter-9 section are the record.
- **Four-loop `MemoryError` early-abort, B2 libc memoization, T3/T4 test hardening — settled/verified.**
- **J-01/J-03/J-05 verified passing on this build**; golden `J-01.json`/`J-03.json` left unchanged (their
  replay FAILs were pre-`.next`-rebuild false positives).
- **Do NOT touch** `health.py`, `readiness.py`, `main.py` boot, `warmup.py`, `max_range_days`/
  `snapshot_cadence`, the `/evidence` drawdown warm, or `server.memory_cap_mb` — all settled.
