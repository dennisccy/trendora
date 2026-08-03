# Iteration State — ops-hardening

**After iteration:** 44 · **Date:** 2026-08-03 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 2 failing (J-05 J-07) — 8 total

## Active blockers

- **dev — the app goes fully offline when a heavy job freezes, and cannot stop itself.** 20m51s
  unreachable, `SIGTERM` ignored past its own 120 s window, `SIGKILL` needed. The shutdown deadline
  wired this round (`start-backend.sh`) is enforced BY the frozen event loop, so it can never fire.
  Needs a watchdog OUTSIDE the process (launcher backgrounds uvicorn, owns its own force-stop).
- **dev — the freeze is now NAMED (first time in 7 rounds).** Ingesting ONE day rebuilds the whole
  membership history (~2,860 dates × ~591 symbols): `resolve_with_reasons` ← `_excluded_counts_by_date`
  ← `_membership_timeline` ← `_refresh_ingest_aggregates`, forced by `membership_timeline_cache`'s
  all-or-nothing invalidation (two live stack dumps agree).
- **dev — memory-pressure safety test is flaky** (1 fail then 2 pass back-to-back); a THIRD escape
  remains, inside the error-logging path (reviewer CRITICAL). **dev — health latency still misses**
  (16/240 polls over 2 s, max 2.354 s), hugely improved from 63.6%. **No owner blockers.**

## Last 2 verdicts

- iter 44: ESCALATE — J-07 failed a 3rd consecutive round and J-05 failed its own defining case on a
  never-saved day; review returned FAIL with a CRITICAL. The freeze is finally diagnosed.
- iter 43: ESCALATE — J-07 failed a 2nd consecutive round (total outage + health latency); only the
  audit lane caught the load-bearing defect, and a lean round has no auditor.

## Do not redo

- **`ServerOpsCfg` launcher wiring is DONE and live-verified** (`--limit-concurrency` /
  `--timeout-keep-alive` / `--timeout-graceful-shutdown` on `/proc/<pid>/cmdline`). Correct, and it
  CANNOT close the outage — do not re-wire it; build the out-of-process watchdog instead.
- **The stall is diagnosed — do NOT re-run diagnostics or guess again.** Fix the membership-timeline
  invalidation. No sixth `_BarCache.prefill` / `bars_asof` bound attempt.
- **Retry-503 parity (`api/data.py`) and failed-job message honesty (`_run_job`, incl. the textless
  `MemoryError` fallback + regression test) are DONE.**
- **Cap 6144 → 8192 is the owner's value — NEVER re-tune caps; `tsconfig.json` clean; TC-13 done.**
- **Capture-only, never a round's goal:** J-07's `[NEW]` walkthrough, J-05's frames. iter-33/g deferred 10×.
