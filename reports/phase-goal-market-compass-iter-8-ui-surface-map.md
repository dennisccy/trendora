# Phase goal-market-compass-iter-8 — UI Surface Map

**Phase:** goal-market-compass-iter-8
**Date:** 2026-08-21
**Written by:** ui-impact-analyst

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

---

## Affected UI Surfaces

None. No route, page, component, form, modal, table, chart, or navigation element changed this
iteration — zero files under `apps/frontend/` were touched (confirmed via
`docs/handoffs/goal-market-compass-iter-8-dev.md`'s "Files Changed" list and its own
`git status --short` scoping statement: "No... frontend files. `git status --short` confirms the diff
is scoped to exactly the files above").

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| *(none — no UI surface changed this iteration)* | — | — | — | — |

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/j10_recovery.py` — replaced the single-tolerance, aggregate-verdict
  `check_adjustment_convention` with a per-symbol, two-part gate (path agreement +
  stable-multiplicative-bridge); added `_compute_symbol_verdict`, `SymbolConventionVerdict`,
  `ConventionCheckBatchResult`, `_BridgeApplyingProvider`, `convention_evidence_to_dict`; redesigned
  `run_gated_recovery`'s signature to remove threshold/sample/window override parameters (B5). All
  internal one-time data-recovery orchestration logic, invoked only by a standalone incident-recovery
  script — not by any route handler. No UI surface affected.
- `apps/backend/app/data_providers/yahoo_provider.py` — docstring-only change noting
  `get_adjusted_close`/`_parse_adjusted_close` are no longer used by the live J-10 gate (the gate now
  calibrates on `get_daily`'s raw close instead). No behavior change, no new method, no route exposes
  this client. No UI surface affected.
- `apps/backend/tests/test_j10_recovery.py` — restructured: 15 pre-existing tests unchanged, 12 old
  tests replaced with 22 new tests for the per-symbol redesign (37 total, all passing). Test file
  only. No UI surface affected.
- `apps/backend/tests/test_provider_clients.py` — 6 new synthetic-payload tests for
  `_parse_adjusted_close`'s failure branches (resolves T2). Test file only. No UI surface affected.
- `runs/goal-session-market-compass/state/assumptions.md` — 2 new dated entries (threshold-choice
  reasoning; declining to widen the comparison sample mid-task). Process artifact, not application
  code. No UI surface affected.
- `runs/goal-market-compass-iter-8/j10-convention-evidence.json` — new persisted per-pair evidence
  artifact from the real live run (20 symbols, 88 pairs). Internal orchestration record; not served
  by any endpoint, not displayed anywhere. No UI surface affected.
- `docs/handoffs/goal-market-compass-iter-8-dev.md` — this iteration's dev handoff. Documentation, not
  application code. No UI surface affected.
- `runs/goal-market-compass-iter-8/status.json` — process/orchestration state. No UI surface affected.

**Data change, not a file/code change (noted for completeness):** the live recovery run inserted 40
new rows into `daily_prices` (20 of 587 proven-missing symbols x 2 dates: 2026-08-11, 2026-08-12) and,
via an incidental backend-boot side effect (not an explicit call this iteration made), created three
new `ScannerRun` rows (2026-08-11, 2026-08-12, and an unrelated pre-existing cadence gap at
2026-05-12). `apps/backend/data/trendora.db` is gitignored and not part of this diff; it is reflected
here only because it is the substantive cause of the endpoint-behavior note below.

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 4 code files (`j10_recovery.py`, `yahoo_provider.py`,
  `test_j10_recovery.py`, `test_provider_clients.py`) + 4 non-code artifacts (assumptions-ledger
  entries, dev handoff, evidence JSON, status JSON)

## Pre-Existing Surface State, Changed As An Incidental Data Consequence (context only — no row above because no route file changed)

`GET /api/compass` is an existing backend-api endpoint already consumed by the frontend (the "market
compass" UI journeys, J-01 et al., per the precedent in
`reports/phase-goal-market-compass-iter-7-ui-surface-map.md`), but no route file was touched this
iteration and this endpoint's own code did not change. Its *observed response* for one date changed
as a side effect of newly-present data, not a code change:

- `GET /api/compass?as_of=2026-08-12` returned HTTP 400 before this iteration and now returns
  **HTTP 200**, per the dev handoff's step 5(f) direct, read-only API call against a transiently
  started backend (not a browser session). `?as_of=2026-08-11` similarly now returns 200.
- This reflects a genuinely partial repair — 20 of 587 proven-missing symbols restored, 567 not
  attempted this iteration — and the two dates' `ScannerRun` snapshots are documented, temporary,
  recovery-era derived state, not final. `docs/goal.md`'s J-10/J-11 responsibility boundary places
  the final repaired-state J-01/J-02/J-03 replay claim in a separate, not-yet-run **J-11 Stage G**,
  not this iteration.
- **No browser session was opened to confirm this**, and none should be: per `docs/goal.md`'s lane
  gate, verifying J-01–J-04 (or any UI journey) in a browser against the current, still-partially-
  repaired dataset is out of scope until J-11 Stage G passes. A replay lane that already ran against
  this damaged database is a recorded incident, quarantined at
  `reports/qa/goal-market-compass-iter-8-evidence/INVALID-forbidden-lane.md` — confirmed present,
  left untouched by this report. This report does not plan or recommend browser verification against
  the current dataset.
