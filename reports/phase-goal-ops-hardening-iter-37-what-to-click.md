# Phase goal-ops-hardening-iter-37 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

## Basis for this determination

- `Frontend Present: no` per both `docs/phases/goal-ops-hardening-iter-37.md` and
  `runs/goal-ops-hardening-iter-37/plan.md`.
- Zero files under `apps/frontend/` were touched this iteration; every served payload (`GET
  /api/data` coverage overview, backfill run-summary, `GET /api/backtest`) is byte-identical
  before/after the fix.
- No new page, nav entry, component, form, or Data Contract value was introduced. The
  user-visible delta, per the spec, is confidence (lower peak memory during heavy backfills, a
  measured/recorded availability guarantee) — not a rendered UI change.

There is nothing for an operator to click this iteration. Verification of this iteration's work
(the shared-cache fix and J-07's steps 1-4) is done via backend test suites and live-process
measurement (VmPeak recording in `reports/perf-budgets.md`, health-poll during warm, induced
memory-pressure drill), not via browser interaction. See
`docs/phases/goal-ops-hardening-iter-37.md`'s Test-first contract (TC-1..TC-10) for that
verification's exact steps.
