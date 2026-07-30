# Phase goal-ops-hardening-iter-37 — UI Test Plan

**Status:** N/A — Backend-only phase. No UI tests required.

## Basis for this determination

- `runs/goal-ops-hardening-iter-37/plan.md`: `Frontend Present: no`; `Agents Required: frontend-ux: no
  -- zero UI/page/component changes; every served payload (GET /api/data coverage, backfill
  run-summary, GET /api/backtest) is byte-identical before and after.`
- `docs/phases/goal-ops-hardening-iter-37.md`: `New user-facing capability: None`; `New information
  displayed: None`; `New user actions: None`; `UI surface changes: None -- backend-only`; `Product
  surface delta: No visible product surface changes`; `Data-contract additions: None.`
- `reports/phase-goal-ops-hardening-iter-37-user-visible-changes.md` confirms the dev handoff's
  Files Changed list is entirely backend/test/report artifacts (`apps/backend/app/engine/
  data_manager.py`, `apps/backend/tests/test_backfill_coverage_shared_cache.py`,
  `reports/perf-budgets.md`, evidence artifacts under `runs/`) — zero files under `apps/frontend/`.
- `reports/phase-goal-ops-hardening-iter-37-ui-surface-map.md` confirms no route, component, form,
  chart, table, or API contract changed, so there is no surface-map row to derive test cases from.
- This iteration's fix (sharing one `_BarCache` for the whole K-date backfill job instead of two
  separate whole-table loads) is an internal memory-loading mechanism inside
  `_do_backfill`/`_persist_per_date_coverage_snapshots`. The byte-identity reference-oracle test
  (TC-7) and unchanged `test_api_data.py`/`test_data_manager.py` regression suites confirm `GET
  /api/data` and `GET /api/backtest` responses are unchanged, so any existing frontend page
  consuming those endpoints (e.g. `/data`, `/backtest`) continues to render the same values it did
  before this iteration.

No UI test cases are generated. Functional verification of this iteration's work (shared-cache
fix, J-07 steps 1-4) is covered by the backend unit/integration test suite and the live-process
measurement work described in `docs/phases/goal-ops-hardening-iter-37.md`'s Testing Requirements
and Test-first contract (TC-1 through TC-10), not by browser-driven UI tests.
