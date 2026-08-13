# Iteration State — ops-hardening

**After iteration:** 74 · **Date:** 2026-08-13 · **Verdict:** CONTINUE

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) — 8 total. J-07 newly passing (first since iter-34);
J-08 + J-09 carried on durability, NOT verified for 2 rounds (`last_verified_iter` = iter-72).

## Active blockers

- **QA frontend intermittently serves unstyled, asset-less pages** (iter-72/c, 3rd round) — dev-owned;
  frames at `reports/qa/goal-ops-hardening-iter-74-evidence/J-0{6,7,8,9}-verify.png`. It is why J-08/J-09
  have no evidence and why the replay lane is untrustworthy. Do NOT regenerate goldens as the fix.
- **131 unresolved (minor) ledger entries** (journey-history.json) — blocks GOAL_ACHIEVED on its own.
- Owner-owned, unanswered: 2 s health-ceiling policy for long jobs; B-1107 concurrent-heavy-compute cap;
  `scripts/automation/browser-qa-phase.sh` one-line fix permission; cost sanction (14th over-budget round).

## Last 2 verdicts

- iter 74: CONTINUE — J-07 step 3 CLOSED on a complete drill (peak VmPeak 4,724.0 MB / 8,192 MB cap =
  42.3% margin, 9/9 finalize phases, 1,795/1,795 health polls 200, max 1.987 s); J-08/J-09 unverified.
- iter 73: CONTINUE — the VmPeak measurement was not obtained; zero journeys moved.

## Do not redo

- **J-07 step 3 is DONE** — `reports/perf-budgets.md` Addendum 39 + `iter-74/phase-vmpeak-samples*.{csv,json}`.
  Margin 42.3% (>= the 20% floor), so `config.yaml` is correctly byte-unchanged. Do not re-measure and do
  not tune `pool_size`/`max_overflow`/`pragmas.cache_size`.
- **Do not run one uninterrupted full-`rebuild` drill on this host** — defeated 4x (iters 72-73);
  `rebuild` rescans the full 2005-2026 basis regardless of requested dates. Fire the finalize tail from a
  single-date `backfill` instead (iter-74's method).
- **Do not regenerate the J-05..J-09 goldens** to fix the replay FAILs — cause is the asset-less frontend,
  confirmed by opening every frame; `state/goldens-regen-pending` points at the wrong fix.
- **`docs/goal.md` Ground truth + Addendum 38 test count are corrected** (iter-73/e, /a closed). Journeys
  and anti-goals were NOT touched — all 8 `spec_hash` values re-verified identical.
- **Readiness serve-stale + post-lock recheck (iter-72) is DONE** — no code touch to
  `compute_readiness`/`compute_preflight`/`_tick_and_cache`. Rendering `stale_for_s` (iter-72/f) stays
  queued for its own **full**-depth round, after the harness repair.
- **iter-33/g (Regime Lab) deferred a 41st time** — do not schedule without owner direction.
