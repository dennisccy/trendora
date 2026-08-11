# Iteration State — ops-hardening

**After iteration:** 64 · **Date:** 2026-08-11 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) · 0 failing — 8 total; all 8 replayed with fresh byte-distinct frames this round.

## Active blockers

- **J-07's last gap (dev-actionable):** `factor_lab_all_warm` holds 568 s of the job and 58 of 59 health-poll breaches (>2.0 s), plus the session's first unanswered poll. Make it yield, then re-run the drill (`runs/goal-ops-hardening-iter-64/evidence-drill/poll_health.py`, `reports/perf-budgets.md` Addendum 30). Output must stay byte-identical.
- **OWNER-gated (16th round):** keep the ≤2 s health promise for 17-20 min jobs, or apply it to short jobs only. J-07 cannot fully close without this sentence.
- **OWNER-gated:** `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix (build-system file).
- **OWNER-gated:** cost sanction for the replay lane's real ~17 min ingest every round — the dominant term in a 4th consecutive over-budget iteration (5,950 s vs 3,600 s, first at lean depth).
- **Open, unexplained (dev):** `/scanner-runs` rendered its contained error boundary once during J-05's replay — `reports/qa/goal-ops-hardening-iter-64-evidence/J-05-verify.png` (ledger iter-64/a). Did not reproduce; needs a written root cause.
- **Unverified until iter-65 (dev):** `CHAIN_BACKEND_READY_WAIT_S` 60→90 landed in `lib/common.sh:1434` and `lib/replay-lane.sh:341` but could not self-verify; confirm from iter-65's own engine log.

## Last 2 verdicts

- iter 64: CONTINUE — the J-05 golden now picks its own unused date at run time (re-proved live after the round), the 4-round-overdue memory-pressure drill passed, and the health-latency jump was attributed as REAL and reproducible; J-07 still `partial`.
- iter 63: CONTINUE — round missed its own goal (53 of 983 polls over 2.0 s), every lane said so; no journey moved.

## Do not redo

- **Do NOT hand-rotate J-05's date.** `resolve_sentinel_date()` (`demo_runner.py:237-275`) selects it at run time; verified live returning 2005-06-28 with 2,193 eligible days left. Only widen the window if it raises.
- **Do NOT re-run the fault-injection drill to "check it works"** — executed iter-64, 1 passed in 764.23 s on its own spawned backend; shared-log MemoryError count unchanged (7,127 before/after).
- **Do NOT re-measure whether the 1→53 latency jump is host noise** — settled: it reproduces (59/930 vs 53/983, within 11 %), 58 of 59 inside `factor_lab_all_warm`. Next step is a FIX, not another measurement.
- **Do NOT re-edit the `test_missing_data_diagnostic_cooperative_yield_byte_identical` docstring** — corrected iter-64 (TC-8), assertions byte-unchanged.
- **Do NOT touch product app code for its own sake:** iter-64's product diff was one docstring; `apps/backend/app/*` and `apps/frontend/*` are unchanged and no journey asks for a new surface.
- Evidence capture (J-05 walkthrough, unrecorded 6 rounds) rides along as a passenger task — never an iteration's own goal.
