# Phase goal-ops-hardening-iter-13 — UI Surface Map

**Phase:** goal-ops-hardening-iter-13
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## Context: no frontend files changed, but two existing surfaces are behaviorally affected

Zero files under `apps/frontend/` appear in this iteration's diff (confirmed via `git status`/`git diff
--stat`). All seven changed product/test files are backend-only (`apps/backend/app/models.py`,
`apps/backend/app/engine/indexes.py`, `apps/backend/app/api/indexes.py`,
`apps/backend/app/engine/data_manager.py`, plus three test files). However, two existing frontend
components already call the changed endpoint unparameterized on mount, and one existing frontend component
already renders a data field generically — so backend-only changes flow through to visible behavior on two
pages without any frontend code being touched. Every row below is annotated with which backend file drives
it.

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Dashboard) | `PhaseCrossViewCard` — its `GET /api/indexes?full=true` call on mount (`apps/frontend/components/phase-cross-view-card.tsx:66`) | Changed behavior (latency only, no content change) | `apps/backend/app/api/indexes.py` now routes this exact hot key (no `range`, no `as_of`, `full=True`) through the new `index_series_cached` wrapper (`apps/backend/app/engine/indexes.py`), which serves an ingest-warmed `IndexSeriesCache` row instead of recomputing from full price history each request. | Open Chrome DevTools Network tab (cache disabled), do one fresh navigation (not a reload of an already-open tab) to `/`, and read the Resource-Timing duration of the `GET /api/indexes?full=true` request. Confirm it is ≤1500ms. Separately, confirm the phase/regime chart's plotted index lines and the displayed as-of date are unchanged from a pre-iteration reading (values must be byte-identical, only faster). |
| `/data` (Data Manager) | `IndexVendorPanel` — its `GET /api/indexes?full=true` call on mount (`apps/frontend/components/index-vendor-panel.tsx:43`) | Changed behavior (latency only, no content change) | Same hot-key cache routing as above; this is the second, independent consumer of the identical unparameterized request. | Perform three independent fresh navigations to `/data` (close and reopen the tab or use three separate incognito windows — not three reloads of one tab — with cache disabled each time). For each navigation, read the Resource-Timing duration of `GET /api/indexes?full=true` and confirm all three are ≤1500ms. Confirm the index-vendor panel's listed rows/values are unchanged from a pre-iteration reading. |
| `/data` (Data Manager) | Live "Job progress" panel — `BackfillBreakdown` component's "Refreshed: ..." line, `data-testid="aggregates-refreshed"` (`apps/frontend/app/data/page.tsx:2576-2580`, rendered from the in-progress/just-finished `DataJob` at line 2775) | New information displayed (conditional — new legal value in an existing generic list) | `apps/backend/app/engine/data_manager.py`'s new warm block inside `_refresh_ingest_aggregates` appends `"index_series"` to the `aggregates_refreshed` array ONLY when it actually persisted a cache row that run; the frontend already renders this array generically with no code change. | Start a bounded backfill or fetch job on `/data` (via the existing job form) for a date range that lands a new price bar for one configured index-chart symbol the DB doesn't already have a bar for on that date (e.g. SPY on a date one day after its current latest stored bar). While the job is live/just after it completes, read the "Job progress" panel's "Refreshed: ..." line and confirm it includes "index series" among the comma-separated items. |
| `/data` (Data Manager) | Persisted "Last run summary" card — same `BackfillBreakdown` component, fallback view when no job has started this browser session (`apps/frontend/app/data/page.tsx:2619`) | New information displayed (conditional — same field, different render site) | Same backend change as above; this is the reduced, `DataRun`-based view the panel falls back to on a fresh page load with no live job this session. | After the job from the row above completes, reload `/data` in a brand-new tab (so no job has started this session) and confirm the "Job progress" panel now shows the persisted Last Run Summary card whose "Refreshed: ..." line still includes "index series" for that completed run. |
| `/data` (Data Manager) | Run History table — per-row breakdown cell, same `BackfillBreakdown` component (`apps/frontend/app/data/page.tsx:3527`) | New information displayed (conditional — same field, table-row render site) | Same backend change as above; this is the historical multi-run table further down the page. | Scroll to the Run History table on `/data`, locate the row for the job used above, and confirm its breakdown cell includes "index series" among the comma-separated "Refreshed:" items. Then locate an earlier or unrelated run's row (one whose job did not touch a configured index-chart symbol's bars) and confirm that row's cell does NOT include "index series" — the honest-omission behavior must hold per-row, not just for the newest run. |

<!-- Change Type key used above: Changed behavior | New information displayed -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — new `IndexSeriesCache` table (columns `range_key`, `full`,
  `dataset_version`, `payload_json`, `created_at`) — pure storage; no endpoint, page, or setting exposes
  this table or its rows directly. No UI surface affected.
- `apps/backend/app/engine/indexes.py` — new `index_series_dataset_version` helper (narrow, index-scoped
  freshness stamp) and `index_series_cached_with_status` / `index_series_cached` wrapper functions —
  internal caching/derivation logic only reachable through the `GET /api/indexes` route change already
  captured in the surface map above. No independent UI surface of its own.
- `apps/backend/app/engine/data_manager.py` — the new warm step's internal mechanics: its `MemoryError`-
  specific isolation (stop immediately, call `_release_process_memory()`, never flip the job's own terminal
  status) and the two docstring/comment updates naming the new `aggregates_refreshed` enum member. The
  *only* user-visible trace of this file's change is the honest presence/absence of `"index_series"` in the
  "Refreshed: ..." line, already captured as three rows above — the error-isolation mechanics themselves
  have no separate UI surface (a `MemoryError` here is designed to be invisible to the job's own displayed
  status, exactly like the other five existing warm loops in this function).
- `apps/backend/tests/test_indexes.py`, `apps/backend/tests/test_api_indexes.py`,
  `apps/backend/tests/test_data_manager.py` — new/extended test coverage only. No UI impact.
- `reports/perf-budgets.md`, `docs/handoffs/goal-ops-hardening-iter-13-dev.md`,
  `reports/phase-goal-ops-hardening-iter-13-implementation-summary.md`,
  `runs/goal-ops-hardening-iter-13/status.json` — project/process artifacts (reports, handoffs, pipeline
  state). Not part of the product; no UI impact.
- `apps/backend/app/engine/forward_testing.py` — confirmed byte-unchanged this iteration (TC-12); not part
  of this iteration's diff at all, listed only because the dev handoff calls out that a pre-existing,
  separately-tracked `MemoryError` in this file was incidentally reproduced (not caused or worsened) during
  the developer's own live verification. No UI impact from this iteration.

---

## Summary

- **Frontend surfaces changed:** 0 (no `apps/frontend/` file appears in the diff)
- **UI surfaces with behavior impact via backend change:** 2 pages (`/`, `/data`), 5 surface-map rows total
- **New pages/routes:** 0
- **Modified components:** 0 (no component source edited — all effects are runtime/data-driven through
  already-existing generic rendering code)
- **Navigation changes:** no
- **Backend-only changes:** 9 (2 product source files' internal mechanics not already captured above, 3
  test files, 4 report/handoff/state artifacts)
