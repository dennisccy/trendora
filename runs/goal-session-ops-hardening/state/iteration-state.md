# Iteration State — ops-hardening

**After iteration:** 66 · **Date:** 2026-08-12 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) — 8 total

## Active blockers

- **J-07's ≤2.0 s health ceiling (dev).** Worst drill of the session: 70 of 1,024 polls over
  2.0 s (max 4.413 s), plus 6 of 150 in the second lane — both through the new canonical
  `scripts/qa/poll_health.py`. My alignment against `dev.log`'s phase lines puts **68 of the 70
  inside `factor_lab_all_warm`** (15.7 % of its 433 polls) and **0 in the 382 polls after it
  closed**. Raw: `runs/goal-ops-hardening-iter-66/evidence-drill/tc1-health-poll.csv`.
- **OWNER (18th round): the 2-second ceiling policy** — does it bind an 18-20 minute job, or
  short jobs only? J-07 cannot close either way until this is answered.
- **OWNER: cost sanction** for the replay lane's real ~18-minute ingest every round (sixth
  over-budget round, 8,641 s vs 3,600 s); **OWNER: sign-off** on the one-line ordering fix in
  `scripts/automation/browser-qa-phase.sh`.

## Last 2 verdicts

- iter 66: CONTINUE — profiling found nothing to bound (2nd null result running), but the
  unified stopwatch localized 97 % of the slow answers to one job phase; J-07 stays partial.
- iter 65: CONTINUE — empty product diff; four profiles of `factor_lab_all_warm` found no hold; J-07 held partial.

## Do not redo

- **Re-profiling `coverage_membership_timeline_refresh`** (2 passes, one at a 5x finer 0.05 s
  threshold, 0 stalls — `stall_summary_coverage.json`) and **re-running any compute chain in a
  STANDALONE script** to find the hold: two consecutive null results — watch the live process.
- **iter-64/d duplicate job-history row — FIXED**: `_reopen_interrupted_run_record`
  (`data_manager.py`) + 2 tests in `test_data_manager_jobs_pipeline.py`; reviewer re-ran them.
- **iter-64/c wrong sentinel window — FIXED**: `journey-scripts/J-05.json` states
  2005-03-01..2016-12-31, verified against `demo_runner.py:233-234`.
- **iter-65/a two disagreeing counters — CLOSED**: one checked-in `scripts/qa/poll_health.py`,
  both lanes used it, rates now agree (6.8 % vs 4.0 %).
- **NOTE, overrides iter-65's ban:** `factor_lab_all_warm` is RE-OPENED as a target — see the
  blocker above and `runs/goal-session-ops-hardening/state/assumptions.md` (iter-66 entry).
