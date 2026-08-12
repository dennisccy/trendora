# Iteration State — ops-hardening

**After iteration:** 72 · **Date:** 2026-08-12 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) · 0 failing — 8 total

## Active blockers

- **J-07 step 3 — peak memory never measured under the new pool (dev).** `pool_size`+`max_overflow` went
  30 → 68 while `pragmas.cache_size: -262144` gives EACH pooled sqlite connection a 256 MB page cache under an
  unchanged 8192 MB `ulimit -v`: retained worst case 2.5 → 6 GB vs a warm last measured at 3.69 GB (iter-38).
  Measure at real concurrency, record the margin in `reports/perf-budgets.md`, lower `cache_size`/`pool_size`
  if thin. Only thing between J-07 and `passing`.
- **No trustworthy replay baseline (dev).** 6 of 8 goldens FAILed at 22:22-22:24 UTC because the QA frontend
  served unstyled pages stuck at "Checking backend…" (`…-evidence/J-07-verify.png`), all six overturned by
  live re-verification; `runs/…/journey-scripts/J-01.json` also lost two undisclosed assertions.
- **Owner-owned, 24th round:** the 2 s health ceiling (long vs short jobs); B-1107; `browser-qa-phase.sh` fix; a cost sanction (12th over-budget round).

## Last 2 verdicts

- iter 72: CONTINUE — availability fixed and re-derived by the evaluator (1,315/1,315 polls answered, max
  1.652 s, inside a 598 s `factor_lab_all_warm` matching iter-71's 607 s); J-05 back to `passing`, J-07
  `failing` → `partial` on the unmeasured memory demand behind the pool resize.
- iter 71: ESCALATE — a lean round measured a real 165 s outage (58/900 non-answers, one 500) rooted in
  DB-pool exhaustion plus iter-71's own blocking readiness fallback, on the forbidden `dev.sh` stack.

## Do not redo

- **DB pool sizing + boot invariant — DONE.** 24+44=68 ≥ `limit_concurrency` 64, drift guarded at
  `config.py:2778`; only lower if the memory measurement above demands it.
- **Readiness serve-stale + post-lock recheck — DONE.** `readiness.py:643-649` serves the cached entry with
  uncapped `stale_for_s` without touching `_TICK_LOCK`; never reinstate a blocking synchronous fallback.
- **`scripts/dev.sh` launcher parity — DONE.** Backend subshell carries the three uvicorn flags and appends to
  `logs/backend.log`; frontend subshell byte-unchanged.
- **Rendering `stale_for_s` is NOT done and needs its own FULL-depth round** (audit B4 / iter-72/f).
- **Walkthroughs ride along, never a goal** (J-05 14 rounds unrecorded; J-07's `[NEW]` steps) — and the demo
  recorder itself is broken: 5 of 8 steps failed their own fills/clicks.
- **iter-33/g the Regime Lab — deferred 39 times; do not schedule without owner direction.**
