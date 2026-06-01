# Phase goal-i_can_see_the_wealthy_future_forever-iter-3 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3 (J-17 — Data Manager)
**Date:** 2026-06-01
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `DataManagerPage` (whole route) | New page | J-17 adds an on-demand dataset-growth screen | Navigate to `/data`; confirm the page renders with header "Data Manager" and four panels (coverage, job form, job progress, run history) — not a 404 or blank page |
| `/data` | `CoveragePanel` (Dataset coverage) | New component | Show descriptive dataset metadata | Confirm the five metrics render real values: Price history `YYYY-MM-DD → YYYY-MM-DD`, a non-zero Symbols count (~158), Trading days, Snapshot dates, and a Backfill gaps count; when gaps > 0 the count is amber and a "Gap range" line shows first → last gap date |
| `/data` | `JobForm` → Start date / End date `<input type="date">` | New form | Pick the date/range to fetch/backfill (job parameters only) | Confirm Start and End date inputs are pre-filled from gap dates on first load; change the End date and confirm only the form value changes — the global as-of switcher value in the header does NOT change (J-18 guard) |
| `/data` | `JobForm` → Job kind `Select` | New form control | Choose Backfill / Fetch / Fetch+backfill | Open the Job kind dropdown; confirm the three options "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill" are present and selectable |
| `/data` | `JobForm` → **Start** button | New action | Trigger the async fetch/backfill job | With kind = "Backfill snapshots" and a valid gap range, click **Start**; confirm the button shows a spinner + "Job running…" and the Job progress panel begins updating |
| `/data` | `JobProgressPanel` (Job progress) | New component | Watch live progress + final summary | After starting a backfill job, confirm the "Snapshots backfilled" progress bar advances (A/B dates rising), the snapshot/forward-return counts increase, and the status badge ends at "ok" (or "partial"/"failed") with a final message |
| `/data` | `JobProgressPanel` → error list | New component (error state) | Surface honest provider failures | Start a "Fetch EOD prices" job (provider unavailable in this env); confirm the panel ends in a "failed"/"partial" badge and shows an error block listing per-symbol failures with the text "(no data fabricated)" |
| `/data` | `RunHistoryPanel` (Run history table) | New table | Log of recent fetch/backfill runs | After a job completes, confirm a new row appears at the top with the correct Started time, Kind badge, Range, Status badge, Symbols ok/failed, Snapshots count, and Summary message |
| `/data` | `RunHistoryPanel` empty state | New component (empty state) | Handle the no-runs case | On a fresh DB with no runs, confirm the "No fetch / backfill runs yet" empty-state card shows instead of an empty table |
| `/data` | Loading skeleton / "Backend unavailable" card | New states | Honest loading + error handling | Load `/data` with the backend stopped; confirm the red "Backend unavailable" card appears (no fabricated figures) rather than zeros or a crash |
| (global) | `Sidebar` `NAV` → "Data Manager" link | Added navigation | New top-level page needs an entry point | Confirm a "Data Manager" item with a database icon appears as the last sidebar entry on every page and clicking it routes to `/data` and marks itself active |
| (global) | `asof-provider.tsx` global as-of switcher | Changed behavior | New backfilled dates must be selectable without reload | After a backfill job completes on `/data`, open the global as-of switcher; confirm previously-absent backfilled dates are now listed **without a hard page reload**, and the current selection is unchanged |
| `/system-health` | sample-size (n) display | Changed behavior (downstream) | Backfill grows forward-test evidence | Record System Health n before a backfill; after backfilling new dates, revisit `/system-health` and confirm n is higher than before |
| `/stocks`, `/` | as-of-driven content | Changed behavior (downstream) | Newly backfilled dates resolve across the dashboard | After backfilling, select a newly created date in the global switcher and confirm `/stocks` and `/` render a valid per-date scorecard/leaderboard for it (no error, no empty state) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — `compute_coverage` + `run_data_job` orchestration and in-memory job registry; surfaced only through the `/api/data*` endpoints (which the `/data` page consumes), no direct UI of its own.
- `apps/backend/app/data_providers/stooq_provider.py` + `make_provider` factory (`data_providers/__init__.py`) — live EOD provider; reached only via the fetch job path, no dedicated UI surface.
- `apps/backend/app/api/data.py` — new router (`GET /api/data`, `POST /api/data/jobs`, `GET /api/data/jobs/{job_id}`); consumed by the `/data` page via the `lib/api.ts` client, so its effects are visible but the endpoints themselves are not a UI surface.
- `apps/backend/main.py` — router include only (lifespan/boot unchanged) — no UI surface.
- `config.yaml` + `apps/backend/app/config.py` (`DataManagerCfg`, `data_manager` block) — config tunables (live_provider, max_range_days, gap_preview, run_history_limit); no UI surface.
- `apps/backend/tests/*` (test_data_manager, test_api_data, test_stooq_provider, conftest, and config/sectors/themes fixture updates) — tests only, no UI.

---

## Summary

- **Frontend surfaces changed:** 14 (one new route with multiple panels/states, one nav change, plus downstream behavior on the global switcher, `/system-health`, `/stocks`, `/`)
- **New pages/routes:** 1 (`/data`)
- **Modified components:** 2 (`Sidebar` nav entry, `asof-provider` additive `refresh()`) + `lib/api.ts` client additions
- **Navigation changes:** yes (one additive sidebar entry, "Data Manager" → `/data`)
- **Backend-only changes:** 6 file groups (engine, provider+factory, API router, main.py include, config, tests)
