# Iteration State — ops-hardening

**After iteration:** 45 · **Date:** 2026-08-04 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 2 failing (J-05 J-07) — 8 total. Nothing changed status
this round; J-07 failing 4 rounds (last passed iter-34), J-05 2 rounds (last iter-39).

## Active blockers

- **dev — memory exhaustion is reachable from ORDINARY PAGE BROWSING, not just an ingest; this is
  the next round's ONE job.** 16 of 24 wedge-window `MemoryError`s entered via `evidence.py:168` →
  unbounded RETAINED accumulators at `research.py:777` / `forward_testing.py:2343`. Drove a ~42-min
  outage (`logs/backend.log` :172574 → :172965, zero access lines). Blocks BOTH targets. iter-45/ap.
- **dev — a fatal job logs nothing.** Run 281 died `"MemoryError (no message)"` with no log line;
  `_run_job`'s outer handler makes no logging call and `data_manager.py:3451` is unguarded.
- **dev — no out-of-process watchdog** (an in-process deadline provably cannot help: AnyIO
  worker-thread CREATION failed). **TC-11 re-opened:** `J-03-verify.png` == `J-04-verify.png`;
  `demo_runner.py` fixed at source, those files predate it. **No owner blockers.**

## Last 2 verdicts

- iter 45: ESCALATE — the membership fix is correct but NEVER ran live (`grep` → 0 matches) and
  neither target moved; review FAIL (CRITICAL), audit FAIL (2 CRITICAL gaps).
- iter 44: ESCALATE — J-07 failed a 3rd consecutive round, J-05 failed its own defining case; the
  live stack dump first named the membership-timeline storm.

## Do not redo

- **The append-forward fast path is BUILT, audit-guarded, byte-identity tested. Keep it; it needs one
  live drill, never a rewrite. Do NOT chase the membership-timeline storm again** — named for 2
  rounds, now fixed, NOT the binding constraint. No sixth `_BarCache.prefill` attempt.
- **No append-forward live drill can be planned:** `gap_last = 2019-02-25` vs latest snapshot
  `2026-07-31` (= the seed horizon); AG-9 forbids making one. Closing J-05 needs the gap-fill fast.
- **The third `MemoryError`-in-logging escape is CLOSED** (`_log_isolation_failure`, 19 sites,
  deterministic fallback tests; iter-44/am resolved). Only `data_manager.py:5058`/`:5091` remain.
- **AG-10 verified intact** (`start-backend.sh:56/:60/:76-101`, `config.yaml:1363` = 8192) — never
  re-tune caps. `J-07.json` step 3 = 2532 ok, `n=8991` unverified. **Capture-only, never a round's
  goal:** J-07's `[NEW]` walkthrough, J-05's frames. iter-33/g deferred 11×.
