# Phase goal-ops-hardening-iter-32 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

## Basis for this classification

`Frontend Present: no` (per `runs/goal-ops-hardening-iter-32/plan.md` and
`docs/phases/goal-ops-hardening-iter-32.md`). This iteration bounds `compute_forward_aggregates`'s
internal `stock_obs` accumulator for memory safety; `/backtest` and all other pages continue serving the
same byte-identical data with no new capability, label, or click path to verify. Operator verification
for this iteration is the live full-deep-basis warm + `GET /api/health` poll + `reports/perf-budgets.md`
entry described in the phase spec's TESTING REQUIREMENTS (TC-4/TC-5), which is a live-process/API-level
check, not a browser UI check.
