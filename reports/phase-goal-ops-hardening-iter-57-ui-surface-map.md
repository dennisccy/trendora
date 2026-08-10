# Phase goal-ops-hardening-iter-57 — UI Surface Map

**Phase:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `AvailabilityHeatmap` — new `data-testid="availability-stale-notice"` banner | Changed behavior | Backend (`availability_from_storage`) now serves the most recent persisted `AvailabilityCache` row with `stale: true` on a stamp mismatch instead of the not-yet-computed empty sentinel; the component renders an "updating" banner for that case | Start a Fetch or Backfill job from the job form (Job kind select + "Start" button), reload `/data` while it is running, and confirm a text element with `data-testid="availability-stale-notice"` reading "Data as of `<version>` — updating" appears above the calendar grid while `availability-cell` elements still render real (non-empty) data |
| `/data` | `AvailabilityHeatmap` — idle/matching-stamp state (unchanged) | Changed behavior (regression guard) | Same code path now has a new branch (stale-serving); the non-stale path must remain byte-identical to iter-56 | With no job running, load `/data` and confirm the availability calendar renders its normal colored day cells with NO `availability-stale-notice` element present anywhere in the card |
| `/data` | `AvailabilityHeatmap` — never-ingested empty state (unchanged) | Changed behavior (regression guard) | The empty sentinel (`stale: false`, `served_dataset_version: null`) is now reserved strictly for a DB with zero persisted `AvailabilityCache` rows; must still render the original empty state | Against a database that has never completed an ingest job, load `/data` and confirm the card shows the "No availability yet" empty state with the description "There are no stored trading days to chart. Fetch real EOD prices to populate the dataset…" and no stale-notice or grid cells (not reproducible on the shared dev DB, which already has data — verify via `test_data_manager.py`'s TC-2 unit test instead if a fresh DB is not available) |
| `/` and every page (sticky header) | `HealthBadge` (`data-testid="readiness-badge"`) | Changed behavior (performance) | `GET /api/health`'s per-request `COUNT(DISTINCT symbol)` full-index scan was replaced with an indexed loose-scan query, cutting steady-state latency from 0.16-0.241s to 0.010-0.014s; response shape/values unchanged | Open DevTools → Network tab, load `http://localhost:3255/`, find the `GET /api/health` request, and confirm its duration is well under 100ms; confirm the header badge still reads `data-state="ready"` with the text "Ready" |
| `/stocks/{ticker}` (e.g. `/stocks/AAPL`) | Price & moving averages chart (`data-testid="chart-window-caption"`) | Changed behavior (performance) | `sma_series` (used by `bars_through_latest`) was bounding an ever-growing full-history slice per iteration (O(n²)); now bounds it to the trailing window per period, byte-identical output, 0.178s→0.038s compute | Navigate to `http://localhost:3255/stocks/AAPL`, open DevTools → Network tab, reload, and confirm the `GET /api/stocks/AAPL/bars?through=latest` request completes in well under 1.5s (was measured at 6.2s previously); confirm the `chart-window-caption` text (e.g. "N bars · as of YYYY-MM-DD · history since YYYY-MM-DD") and the moving-average lines render normally |
| `/data` | Job history row → `BackfillBreakdown` (`data-testid="aggregates-refreshed"`, the "Refreshed: …" text) | Changed behavior (rare failure path only) | `availability_cached_with_status` / `index_series_cached_with_status` now report `persisted_this_call=False` (previously always `True`) when their commit is rolled back, so this note no longer over-claims a refresh that did not durably persist | Not reproducible via normal UI interaction (requires forcing a DB commit failure mid-job). Verify instead by running `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_indexes.py -k rollback -v` and confirming both the `data_manager` and `indexes` rollback tests assert `persisted_this_call is False` |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `app.mcp.tools.list_runs` (`apps/backend/app/mcp/tools.py`) — replaced a per-run `ScannerResult` COUNT
  loop with the same grouped `GROUP BY ScannerResult.run_id` query `app.api.runs.runs` already uses.
  Byte-identical `n_stocks` output, much faster on this dataset's current size. This tool is called only by
  MCP/AI-assistant integrations, never by the web frontend — no UI surface exists for it.
- `reports/perf-budgets.md` (new Addenda 21/22, append-only) — profiling detail, before/after measurements,
  and a corrected calendar-span note. Internal project documentation, not part of the product UI.
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` — the automated golden test script was
  rewritten to assert real per-endpoint latency budgets (paired navigation/assertion timeout gates) instead
  of only matching page headings. A test-infrastructure change, not a product UI change.
- `docs/test-infra-tickets.md` (new file) — a standing ticket (`TI-1`) documenting `test_api_runs.py`'s
  repeated non-completion. Developer-facing record only.

---

## Summary

- **Frontend surfaces changed:** 4 (`AvailabilityHeatmap` stale banner + 2 regression-guarded states,
  `HealthBadge` readiness poll, Stock Detail price/MA chart, `BackfillBreakdown` "Refreshed" note)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/components/availability-heatmap.tsx`,
  `apps/frontend/lib/api.ts` type extension) — the `HealthBadge` and Stock Detail chart surfaces are
  affected purely by faster backend responses; no frontend file was changed for those two
- **Navigation changes:** no
- **Backend-only changes:** 4 (MCP `list_runs`, `perf-budgets.md` addenda, `J-06.json` golden rewrite,
  `docs/test-infra-tickets.md`)
