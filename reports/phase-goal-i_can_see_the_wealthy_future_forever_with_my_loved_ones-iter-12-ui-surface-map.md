# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/data` | `JobProgressPanel` — current-activity line (`JobLiveActivity`) | New component | J-66: server now supplies a real-time "now working on…" message during fetch and backfill | Start a job, then observe that a text line appears below the progress bar naming the current symbol or date being processed (e.g. "scanning 2021-03-11 (12/22)") |
| `/data` | `JobProgressPanel` — "updated Ns ago" heartbeat | New behavior | J-66: server now emits a `last_progress_at` timestamp; frontend ticks a 1s clock and renders elapsed time | While a job is running, verify the heartbeat line reads "updated Xs ago" and increments each second; wait 20+ seconds with no progress and confirm text turns amber and reads "possibly stalled" |
| `/data` | `JobProgressPanel` — symbols counter | Changed behavior | J-66: fixed the "318/159" bug — counter now counts distinct symbols and is clamped at its total | Start a multi-window fetch job and confirm the symbols counter (e.g. "12 / 159 symbols") never shows a value where the left number exceeds the right number |
| `/data` | `StageTimings` — speedup factor display | Changed behavior | J-66: the "× faster" speedup is now read from `stages.backfill.speedup_factor` (server-computed); the client-side division function was deleted | After a parallel backfill completes, verify the Stage Timings section shows a speedup figure (e.g. "3.2× faster") without any JavaScript error in the browser console |
| `/data` | `UnfinishedImportsPanel` — `failed_backfill` entry | New behavior | J-59: a job that completed fetch but failed during backfill now creates a durable `failed_backfill` checkpoint; the panel renders it with amber badge + stage-aware copy + Resume button | In the Unfinished Imports section, find a `failed_backfill` entry and confirm its status badge reads "failed at backfill" (amber), the description mentions "Resumable from the backfill stage (the fetch is skipped)", and clicking the Resume button starts a new running job visible in the live job card |
| `/data` | `RunHistoryPanel` — `running` status row | New behavior | J-60: a job creates its Run History record immediately on start, not only at completion | Start a new backfill job and immediately view the Run History table; confirm a row with "running" status (and an inline spinner) appears for that job before it finishes |
| `/data` | `RunHistoryPanel` — `interrupted` status row | New behavior | J-60: the boot sweep marks any `running` record found at startup as `interrupted` | After a backend restart with a previously-started job: confirm the Run History table shows that job's row with status "interrupted" (neutral/muted styling, not red) |
| `/data` | `RunHistoryPanel` — `partial` job failure detail | New behavior | J-67: per-date failure isolation surfaces failed-date details on a partial job | Find a `partial` job in Run History, expand or inspect it, and confirm a block lists the specific dates that failed (with their error messages) and states the remaining dates completed |
| `/data` | `JobProgressPanel` — poll interval (config-driven) | Changed behavior | J-66: `pollIntervalMs` now reads from `data.job_progress.poll_interval_seconds` (served by the API overview), not a hardcoded 1000ms literal | With a running job, confirm the live job card refreshes at approximately the configured interval (visible in the backend `config.yaml` `data_manager.job_progress.poll_interval_seconds` value) |

---

## File Classification

| File | Category | UI Impact | Explanation |
|---|---|---|---|
| `apps/frontend/app/data/page.tsx` | frontend-direct | direct | Adds `JobLiveActivity`, `heartbeatAgo`, `useNow`, config-driven poll, heartbeat stale indicator, symbols clamp, `statusVariant`/`statusLabel` extensions, per-date failure block, Run History spinner |
| `apps/frontend/lib/api.ts` | frontend-direct | direct | New TypeScript types (`JobStageTiming.speedup_factor`, `JobDateFailure`, `DataJob.current_activity`/`last_progress_at`/`completed_stages`/`date_failures`, `DataRun` status contract, `JobProgressConfig`, `DataOverviewResponse.job_progress`) — consumed by `page.tsx` |
| `apps/backend/app/engine/data_manager.py` | full-stack | indirect | Core engine change: stage-aware checkpoints, covered-range planner, lifecycle records, per-date failure isolation — all surfaced via the existing `/api/data` and `/api/data/jobs/{id}` endpoints the frontend already polls |
| `apps/backend/app/api/data.py` | backend-api | indirect | Overview exposes new `job_progress` config block; resume endpoint accepts `failed_backfill`; job-status payloads include new fields (`current_activity`, `last_progress_at`, `completed_stages`, `date_failures`) — consumed by existing frontend API calls |
| `apps/backend/app/models.py` | backend-internal | none (schema change, UI reads via API) | `ImportCheckpoint.completed_stages_json` and `DataProviderRun.job_id` are new columns; their values are exposed through the API layer and displayed in the UI, but the model file itself has no direct UI coupling |
| `apps/backend/main.py` | backend-internal | none (enables `interrupted` status) | Boot sweep marks orphaned `running` records `interrupted`; the result is visible in Run History via the API |
| `config.yaml` | config | indirect | New `data_manager.job_progress` block controls live-card poll interval and heartbeat stale threshold; the frontend reads these via the overview API, so changes here affect the live card's polling cadence without a frontend deploy |
| `apps/backend/app/config.py` | config | indirect | New `JobProgressCfg` typed config wired into `DataManagerCfg`; enforces positive values at boot — no direct UI surface |
| `apps/backend/tests/**` | backend-internal | none | Test files only; no UI impact |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — schema additions (`ImportCheckpoint.completed_stages_json`, `DataProviderRun.job_id`) — changes are surfaced through the API, not directly; the model file has no UI coupling.
- `apps/backend/app/config.py` — new `JobProgressCfg` typed config class — enforces config validity at boot; no direct UI surface.
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` (new) — 14 backend tests for J-59/J-60/J-66; no UI surface.
- `apps/backend/tests/test_data_manager_backfill_parallel.py` — updated J-67 isolation tests; no UI surface.
- `apps/backend/tests/test_config.py`, `test_api_data.py`, `test_sectors.py`, `test_indexes.py`, `test_themes.py`, `test_config_engine.py` — test-only updates for new config key requirements; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (the `/data` Data Manager page)
- **New pages/routes:** 0
- **Modified components:** 5 (live job card `JobProgressPanel` with `JobLiveActivity` + heartbeat + symbols clamp + config-driven poll; `UnfinishedImportsPanel` for `failed_backfill`; `RunHistoryPanel` for `running`/`interrupted`/partial-detail; `StageTimings` for server-side speedup; `statusVariant`/`statusLabel` for new status tokens)
- **Navigation changes:** no
- **Backend-only changes:** 6 (models, config class, main.py boot sweep, 4 test files)
