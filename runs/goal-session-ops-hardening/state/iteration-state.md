# Iteration State — ops-hardening

**After iteration:** 73 · **Date:** 2026-08-13 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) — 8 total. NOTE: J-08 and J-09 are
carried on evidence durability, NOT verified this round (their replay frames are broken shells).

## Active blockers

- **J-07 step 3 (dev):** no VmPeak measurement under the 68-connection pool — 3 pressure attempts
  (10/8/5 workers) hit the admission-control 503 cliff, the clean arm timed out (`reports/perf-budgets.md`
  Addendum 38). NEXT PATH: per-phase VmPeak deltas via `data_manager.py`'s existing phase timers — do NOT
  retry one uninterrupted end-to-end run on this shared host. Stop rule: if that fails too, ask the owner.
- **Replay lane broken (dev):** 5 of 8 goldens FAILed; frames are unstyled, asset-less "Checking backend…"
  pages (iter-72/c uncured). The recorded reason "selector drift" is WRONG and `state/goldens-regen-pending`
  queues the wrong remedy — fix the QA frontend, then re-verify J-09 first, J-08 second.
- **Ledger (dev):** 251 entries, 129 unresolved, 0 unresolved critical. New this round: iter-73/a..f.
- **Owner:** (a) 2 s health promise for long jobs or short only; (b) B-1107 concurrent-compute bound;
  (c) one quiet host hour, or accept 2,334.8 MB / 71.5% as the answer; (d) `browser-qa-phase.sh` fix
  permission; (e) cost — 13 consecutive over-budget rounds, this one 3.3x.

## Last 2 verdicts

- iter 73: CONTINUE — memory measurement not obtained (host contention, ~8.4 GB basis); no journey moved;
  nothing regressed; coherence PASS; product diff is one test file.
- iter 72: CONTINUE — availability fixed (1,315/1,315 polls) but the pool resize doubled the connection
  ceiling with no memory measurement, holding J-07 at partial.

## Do not redo

- `config.yaml` pool sizing (24+44=68) + the boot-time `pool_size + max_overflow >= limit_concurrency`
  invariant at `config.py:2778` — settled iter-72; never weaken or remove.
- The readiness serve-stale + post-lock-recheck mechanism (`readiness.py:643-649`) — DONE iter-72.
- Measuring VmPeak by one uninterrupted full-`rebuild` run on this host — defeated 4x in iter-73.
- Regenerating the J-05..J-09 goldens as the fix for the replay FAILs — wrong remedy; the cause is the
  asset-less QA frontend, proven by the frames themselves.
- Rendering `stale_for_s` at the glass (iter-72/f) — queued, needs its OWN full-depth round; not next.
- iter-33/g, the Regime Lab — deferred a 40th time; do not schedule without owner direction.
