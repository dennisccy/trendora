# Phase goal-i_can_see_the_wealthy_future_forever-iter-22 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

All affected surfaces are on the existing `/data` page. No new route or nav entry.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Chunk badge (`data-testid="chunk-progress"`) on the job card | New component | J-34: show chunked import progress | Start a fetch import; while it runs, confirm a `chunk X/N` badge renders beside the status badge and the X advances as chunks complete |
| `/data` | Job status badge — `resumable` state (`JobProgressPanel`) | Changed behavior | J-34: distinguish a rate-limit pause from a failure | Drive a fetch to a provider 429 (e.g. Yahoo); confirm the status badge reads *"rate-limited — resumable"* in **amber** (not red `failed`) |
| `/data` | Amber resumable callout (`data-testid="resumable-state"`) on the job card | New component | J-34: surface the pause point + resume affordance | On a rate-limited job, confirm the amber callout shows `chunk X/N` plus symbols done vs remaining, and contains a Resume button |
| `/data` | Resume button (`data-testid="resume-button"`) on the job card | New form/action | J-34: let the user continue a paused import | Click **Resume** on a resumable job; confirm the job is re-pulled into the job card and polling resumes from the next un-fetched chunk (no duplicate fetch) |
| `/data` | Session-only API key field inside `ResumeControl` | New form | J-34/J-33: re-supply a key-gated source's key safely | Pause a needs-key source with no env key; confirm Resume reveals a `type="password"` field labeled *"Session API key for …"*, and that after clicking Resume the field is cleared |
| `/data` | Resumable imports panel (`data-testid="resumable-imports"`) | New component | J-34: surface paused imports that survived a backend restart | Pause an import, restart the backend, reload `/data`; confirm a *"Resumable imports"* card lists the import with source, date range, `chunk X/N`, symbols done/remaining/failed, bars-so-far, and a Resume button. Confirm the panel is **absent** when nothing is paused |
| `/data` | Resume button on each resumable-imports row (`data-testid="resume-button"`) | New action | J-34: resume from the post-restart panel | Click **Resume** on a resumable-imports row; confirm the import is picked back up as a live job card and the row drops off the panel |
| `/data` | Job progress header source label (`JobProgressPanel`) | Changed behavior | Finding #2: a backfill-only job has no fetch source | Run a backfill/seed job; confirm the progress header shows **no** import-source line (source appears only for fetch-kind jobs) |
| `/data` | Provider error text (job card / job-status / run history) | Changed behavior | J-33: redact leaked API key from error messages | Trigger a failed/429 fetch on a key-gated source with a pasted key; confirm the displayed error contains **neither** the key **nor** any `?token=`/`?apikey=` query string |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/data_providers/_http.py` — redacts the request URL (strips query/fragment) + status in
  `ProviderUnavailableError`; raises `RateLimitError` on HTTP 429. Drives the redacted error text shown in
  the UI but is itself not a surface.
- `apps/backend/app/data_providers/base.py` — new `RateLimitError(ProviderUnavailableError)` subclass — no
  direct UI surface.
- `apps/backend/app/data_providers/alpha_vantage_provider.py` — maps a throttle `Note`/`Information` body to
  `RateLimitError` — no direct UI surface.
- `apps/backend/app/models.py` — new `import_checkpoints` table (`ImportCheckpoint`) — mutable job-control
  state, no key column; powers resume but has no own surface.
- `apps/backend/app/engine/data_manager.py` — chunked fetch engine, key scrub, checkpoint persistence,
  backoff→resumable, `resume_data_job` — backend logic; user-visible only via the `/data` surfaces above.
- `apps/backend/app/api/data.py` — `POST /api/data/jobs/{import_id}/resume` (404/409/400) and
  `resumable_imports` on `GET /api/data` — consumed by the Resume controls and resumable-imports panel
  above (not separately navigable).
- `apps/backend/app/config.py` + `config.yaml` — `ImportChunkingCfg` / `data_manager.import_chunking`
  tunables (batch size, date window, retries, backoff, sleep) — config, no UI.
- `apps/frontend/lib/api.ts` — types + `resumeDataJob()` client wiring — supports the surfaces above; not a
  surface itself.
- `apps/backend/tests/*` — test changes — no UI impact.

---

## Summary

- **Frontend surfaces changed:** 9 (all on `/data`)
- **New pages/routes:** 0
- **Modified components:** `JobProgressPanel` (chunk badge, resumable callout, source-label fold); new
  `ResumeControl` and `ResumableImportsPanel`
- **Navigation changes:** no
- **Backend-only changes:** 9 files (provider redaction/rate-limit, checkpoint model, chunked engine, resume
  API, config, api client, tests)
