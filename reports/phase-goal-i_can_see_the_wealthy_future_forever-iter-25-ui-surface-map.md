# Phase goal-i_can_see_the_wealthy_future_forever-iter-25 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `MissingDataDiagnosticPanel` (new) | New component | J-37: surface read-only missing-data diagnostic (3 categories) from `coverage.diagnostic` | Load `/data`, confirm the "Missing-data diagnostic" panel appears below the Coverage panel; when `affected_count === 0` confirm the panel shows a "No missing data" empty-state and no Pull buttons are present |
| `/data` | `DiagnosticCategory` — "No history" section | New component | J-37: list universe members with zero stored bars, exact shortfall, and a Pull button | On a dataset with a no-history member, confirm a row appears under "No history" showing the symbol and "0 / N bars", and a "Pull the missing data" button is rendered on that row |
| `/data` | `DiagnosticCategory` — "Thin history" section | New component | J-37: list universe members with bars below `min_history_bars`, exact shortfall, no Pull button | On a dataset with a thin member, confirm the row appears under "Thin history" showing bars-have/bars-needed, and confirm NO "Pull the missing data" button is rendered on that row (transparency only) |
| `/data` | `DiagnosticCategory` — "Intra-series gaps" section | New component | J-37: list members with trading days missing inside their own range, exact gap | On a dataset with a gap member, confirm a row shows the symbol, missing-day count, and gap range (e.g. "3 missing 2025-01-15 → 2025-02-03"), and a "Pull the missing data" button is rendered |
| `/data` | "Pull all missing" button (`pull-all-button`) | New element | J-37: dispatch gap-exact pull jobs for every pullable diagnostic row | Click "Pull all missing"; confirm a job is dispatched and surfaces in the live job card; confirm the request body scopes only diagnosed symbols/dates, not the full universe |
| `/data` | Per-row "Pull the missing data" button (`pull-row-button`) | New element | J-37: dispatch a gap-exact pull job for one diagnostic row | Click the "Pull the missing data" button on a single no-history or gap row; confirm the job card appears with running status and shows only the affected symbol, not the whole universe |
| `/data` | Job card — pull completion update | Changed behavior | J-37: on pull completion, coverage reloads and the diagnostic row clears | After a pull job completes, confirm the diagnostic row for that symbol disappears (or the shortfall decreases) and the per-symbol coverage table shows updated bar counts |
| `/data` | `UnfinishedImportsPanel` (replaces `ResumableImportsPanel`) | Changed component | J-38: unified list of all unfinished imports (resumable + partial + failed) | Load `/data` when at least one unfinished import exists; confirm the panel shows rows for all three states (resumable amber, partial amber, failed red), each with a plain-language state string under `data-testid="unfinished-state"` |
| `/data` | `UnfinishedImportsPanel` — hidden when empty | Changed behavior | J-38: panel is hidden when no unfinished imports exist | Load `/data` when all imports are complete; confirm the `unfinished-imports` panel is not rendered in the DOM (previously the panel may have shown a blank card) |
| `/data` | `UnfinishedImportsPanel` — status badge | New element | J-38: amber for paused/partial, red for failed, teal for running | In the unfinished-imports panel, confirm a resumable/partial row shows an amber badge and a failed row shows a red badge |
| `/data` | `RetryControl` — "Retry remaining" button (`retry-button`) | New element | J-38: re-dispatch only outstanding/failed work for a partial or failed run | Click "Retry remaining" on a partial-run row; confirm a new job is dispatched, the job card shows running status, and the retry scope is not the full universe |
| `/data` | `DismissControl` — "Remove" / "Dismiss" button (`dismiss-button`) | New element | J-38: drop the actionable job-control record from the unfinished list | Click "Dismiss" on a partial/failed run row; confirm the row disappears from the Unfinished-imports panel and the Run-history audit table below still contains that run's entry |
| `/data` | `ResumeControl` — session-key re-prompt for needs-key Retry/Resume | Changed behavior | J-38: Retry/Resume against a needs-key provider re-prompts for the session-only API key | For a paused import from a needs-key source, click Resume; confirm a key input field appears before the job is re-dispatched, and after submission the field is cleared |
| `/data` | `lib/api.ts` — `MissingDataDiagnostic` types on `DataCoverage` | Frontend-direct (type) | J-37: typed `coverage.diagnostic` field consumed by `MissingDataDiagnosticPanel` | Confirm TypeScript build is clean (`npx tsc --noEmit`); confirm the panel reads `diagnostic.no_history`, `diagnostic.thin`, and `diagnostic.intra_series_gaps` from the API response without casting |
| `/data` | `lib/api.ts` — `UnfinishedImport` type on `DataOverviewResponse` | Frontend-direct (type) | J-38: typed `unfinished_imports` field consumed by `UnfinishedImportsPanel` | Confirm TypeScript build is clean; confirm each row in the panel reads `imp.state`, `imp.record_type`, `imp.actions`, and progress counts from the typed API response |
| `/data` | `lib/api.ts` — `pullMissingData` client | Frontend-direct (API client) | J-37: sends gap-exact symbols + date range to `POST /api/data/jobs` | After clicking "Pull the missing data", confirm the outbound POST body contains only the diagnosed symbols and the diagnosed start/end dates — not the whole universe or the full window |
| `/data` | `lib/api.ts` — `retryDataJob` client | Frontend-direct (API client) | J-38: sends `POST /api/data/jobs/{id}/retry` | After clicking "Retry remaining", confirm the outbound POST is to the `/retry` endpoint (not `/resume`) and the job response carries a new `job_id` |
| `/data` | `lib/api.ts` — `dismissUnfinishedImport` client | Frontend-direct (API client) | J-38: sends `POST /api/data/jobs/{id}/dismiss?record_type=run|checkpoint` | After clicking "Dismiss" on a run row, confirm the outbound POST includes `record_type=run`; after clicking "Remove" on a checkpoint row, confirm `record_type=checkpoint` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — `_missing_data_diagnostic` helper, `unfinished_imports` union, `retry_run`, `dismiss_import` — all are consumed by the API and wired into the `/data` UI; classified full-stack, not backend-only.
- `apps/backend/app/models.py` — `DataProviderRun.dismissed` column added — this is a mutable job-control flag read by `unfinished_imports` and exposed through the dismiss endpoint; visible indirectly through the Unfinished-imports panel (dismissed runs leave the list but remain in Run history).
- `apps/backend/app/db.py` — `_ensure_additive_columns` startup backfill — applies the `dismissed` column to an existing DB without regen; no UI surface change.
- `apps/backend/tests/test_data_manager.py`, `apps/backend/tests/test_api_data.py`, `apps/backend/tests/test_db.py` — backend tests; no UI surface impact.

---

## Summary

- **Frontend surfaces changed:** 2 (the `/data` page gains 2 new additive panels)
- **New pages/routes:** 0
- **Modified components:** 1 (`UnfinishedImportsPanel` replaces `ResumableImportsPanel`)
- **New components:** 4 (`MissingDataDiagnosticPanel`, `DiagnosticCategory`, `RetryControl`, `DismissControl`)
- **Navigation changes:** no (all changes are additive on the existing `/data` page; no sidebar, route, or nav-skeleton change)
- **Backend-only changes:** 1 (DB startup backfill `_ensure_additive_columns`; the model/engine/API changes are full-stack)
