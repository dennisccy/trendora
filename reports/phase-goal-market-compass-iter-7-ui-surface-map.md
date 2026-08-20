# Phase goal-market-compass-iter-7 — UI Surface Map

**Phase:** goal-market-compass-iter-7
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

---

## Affected UI Surfaces

None. No route, page, component, form, modal, table, chart, or navigation element changed this
iteration — zero files under `apps/frontend/` were touched (confirmed via the dev handoff's "Files
Changed" list and its own `git status --short` scoping statement).

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| *(none — no UI surface changed this iteration)* | — | — | — | — |

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/j10_recovery.py` — `RECOVERY_SOURCE` constant swapped `"stooq"` →
  `"yahoo"`; new fail-closed adjustment-convention-check function (`check_adjustment_convention`,
  returns agree/mismatch/inconclusive) and causal-ordering orchestrator (`run_gated_recovery`) added —
  internal one-time data-recovery engine logic, invoked only by a standalone incident-recovery script,
  not by any route handler. No UI surface affected.
- `apps/backend/app/data_providers/yahoo_provider.py` — additive `get_adjusted_close` method (fetches
  Yahoo's split/dividend-adjusted close series via `indicators.adjclose`) used only by the
  convention-check gate above. `get_daily`'s existing contract and callers are unchanged. No API route
  exposes this method. No UI surface affected.
- `apps/backend/tests/test_j10_recovery.py` — 2 tests updated, 9 new fixture-scoped tests added for the
  above. Test file only. No UI surface affected.
- `runs/goal-session-market-compass/state/assumptions.md` — one new dated entry (the tolerance
  discipline judgment call). Process artifact, not application code. No UI surface affected.
- `docs/handoffs/goal-market-compass-iter-7-dev.md` — this iteration's dev handoff. Documentation, not
  application code. No UI surface affected.

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 3 code files (`j10_recovery.py`, `yahoo_provider.py`,
  `test_j10_recovery.py`) + 2 non-code artifacts (assumption-ledger entry, dev handoff)

## Pre-Existing Surface State, Unchanged By This Iteration (context only — no row above because
nothing about it changed)

`GET /api/compass` is an existing backend-api endpoint already consumed by the frontend (the "market
compass" UI journeys, J-01 et al.), but no route file was touched this iteration and this endpoint's
own code did not change. Its behavior is unchanged: it returned HTTP 400 for `as_of=2026-08-11` /
`as_of=2026-08-12` before this iteration and still does after, because the new convention-check gate
correctly stopped before writing the missing data (verified via a direct, read-only API call recorded
in the dev handoff's step 5(f) table — not a browser session; none was run, per this iteration's
lane-gate restriction against verifying UI journeys on the still-possibly-damaged dataset, and per this
report's explicit instruction not to plan or recommend browser verification against the current
dataset).
