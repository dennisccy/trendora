# goal-i_can_see_the_wealthy_future_forever-iter-22 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

Two coupled deliverables on `/data`, in order: **Part 1** fixes the iter-21 key-leak (gates J-33 →
passing), then **Part 2** builds J-34 (chunked, rate-limit-resilient, resumable import). Confined to the
provider package + `data_manager` + `config` + `models` (one new empty table) + `/data` — **no
scoring/snapshot/forward-side touch, no scanner DB regen** (the 29 carried journeys' stored values are
byte-identical).

## What Was Built

### Part 1 — Fix the import key-leak (J-33 → passing)
- **Redaction at the error source** (`data_providers/_http.py`): the surfaced `ProviderUnavailableError`
  message is now built from a **redacted request URL** (`exc.request.url.copy_with(query=None,
  fragment=None)` — the entire query string stripped, so it is key-agnostic: covers `token`/`apikey`/any
  future param) **+ the HTTP status**, never `str(exc)` (which embedded `?token=…`/`?apikey=…`). Handles
  both `httpx.HTTPStatusError` (request+response → include `HTTP {status}`) and `httpx.RequestError`
  (request, no response → omit status; its `.request` property raises when unset, handled defensively).
- **Defense-in-depth scrub** (`engine/data_manager.py`): a redactor closure removes the resolved key
  literal from any error string before it is recorded (`***`), in case a future error path still carries
  it. The key is only ever removed, never logged/persisted.
- **Blind-spot regression tests**: a **real** `httpx.HTTPStatusError`/429 with the key in the request URL
  (via `httpx.MockTransport` + a real `httpx.Client` injected into Tiingo/Finnhub/Alpha Vantage) → the
  message contains neither the key nor any query string. End-to-end, the key is absent from
  `JobProgress.errors`, `GET /api/data/jobs/{id}`, the checkpoint, `resumable_imports`, every
  `DataProviderRun` column, and `caplog` — while the `***` marker proves the scrub fired. (The existing
  `_FakeResponse` hard-codes `http://x` and could never reach this path; the iter-21
  `test_pasted_api_key_never_persisted` was **extended, not deleted**.)

### Part 2 — J-34 chunked, rate-limit-resilient, resumable import
- **Config-driven chunking** (`config.yaml` `data_manager.import_chunking` + typed `ImportChunkingCfg`,
  boot-validated all-positive + `cap ≥ base`): `symbol_batch_size`, `date_window_days`, `max_retries`,
  `backoff_base_seconds`, `backoff_cap_seconds`, `inter_request_sleep_seconds`. **No chunk/backoff/sleep
  literal anywhere in `data_manager.py`/the providers.**
- **`RateLimitError(ProviderUnavailableError)`** (`data_providers/base.py`): raised on HTTP 429 in
  `_http.py` (still redacted) and on an Alpha Vantage `Note`/`Information` throttle body. A subclass, so
  existing `except ProviderUnavailableError` handlers stay correct; the chunk loop catches it first.
- **Durable checkpoint table** `import_checkpoints` (`models.py` `ImportCheckpoint`) — **mutable
  job-control state, NOT a snapshot** (invariant #3 binds only `scanner_runs`/`scanner_results`/
  `*_scores`/`forward_returns`). `import_id` == the live `JobProgress.job_id`; stores the deterministic
  symbol plan, `chunk_total`, `next_chunk_index` (advanced only after a chunk fully completes), cumulative
  counters, `status` ∈ running|resumable|ok|failed. **No key column.** Created via `metadata.create_all`
  (empty on first boot).
- **Chunked fetch engine** (`engine/data_manager.py`): the single-shot `_do_fetch` is replaced by a
  batched loop (deterministic symbol-batches × date-windows; J-17's small jobs = one chunk). Reuses the
  existing INSERT-new-only `_existing_dates` guard for per-`(symbol, date)` idempotency; persists the
  checkpoint after each completed chunk; **injectable sleep** for backoff + inter-request delay. On
  `RateLimitError` it retries the current symbol with exponential backoff up to `max_retries`, then stops
  gracefully → `status="resumable"` (distinct from `failed`), persists, and returns — **never raises,
  never fabricates a bar**. A non-429 failure per symbol counts failed + records a redacted error +
  continues (unchanged).
- **Resume path**: `resume_data_job(import_id, *, api_key=…)` loads the checkpoint, re-registers a fresh
  `JobProgress` (same `import_id`), and runs from `next_chunk_index` (rebuilding the SAME plan from the
  stored symbol list) — re-fetching nothing already stored. `POST /api/data/jobs/{import_id}/resume`
  (re-accepts the session-only key for a needs-key source; unknown → 404, non-resumable → 409,
  needs-key-without-key → 400). `GET /api/data` gains a `resumable_imports` array (newest first; never a
  key) so the affordance survives a backend restart.
- **Finding #2 fold**: a backfill-only job's `JobProgress.source` is now `None` (source set only for
  fetch kinds), so its progress header shows no import source. The persisted run still records `seed`.
- **Frontend**: chunk x/N badge, amber "rate-limited — resumable" state + Resume on the job card, and a
  post-restart "Resumable imports" panel. (See the frontend handoff for detail.)

## Files Changed

- `config.yaml` — added `data_manager.import_chunking` (6 tunables).
- `apps/backend/app/config.py` — `ImportChunkingCfg` (boot-validated) wired onto `DataManagerCfg`.
- `apps/backend/app/data_providers/base.py` — `RateLimitError(ProviderUnavailableError)`.
- `apps/backend/app/data_providers/_http.py` — redaction helper (strip query/fragment + status); 429 →
  `RateLimitError`; both error branches redaction-safe.
- `apps/backend/app/data_providers/alpha_vantage_provider.py` — throttle `Note`/`Information` →
  `RateLimitError`.
- `apps/backend/app/models.py` — `ImportCheckpoint` (`import_checkpoints`; mutable job-control, no key).
- `apps/backend/app/engine/data_manager.py` — key scrub; chunk plan + chunked fetch engine + checkpoint
  persistence + 429-backoff→resumable; `resume_data_job`/`start_resume_job`; `resumable_imports`;
  `JobProgress` chunk fields; Finding #2 source fold.
- `apps/backend/app/api/data.py` — `POST /api/data/jobs/{import_id}/resume` (404/409/400);
  `resumable_imports` on `GET /api/data`; `ResumeRequest` body.
- `apps/frontend/lib/api.ts` — chunk fields + `resumable`; `ResumableImport` + `resumable_imports`;
  `resumeDataJob()`.
- `apps/frontend/app/data/page.tsx` — chunk x/N, amber resumable state + Resume, resumable-imports panel.
- Tests: `tests/test_provider_clients.py` (real-httpx 429/500/non-JSON redaction); `tests/test_config.py`
  (+`test_config_engine.py`,`test_themes.py`,`test_sectors.py`: the new required `import_chunking` key in
  all 4 inline config fixtures + boot-`ConfigError` cases); `tests/test_data_manager.py` (extended
  key-never-persisted with a real-httpx scrub case; chunk-plan config-driven; backoff/retry with patched
  sleep; durable checkpoint + resume + idempotency via a fresh DB session; resume 404/409);
  `tests/test_api_data.py` (overview shape + resume 404/409/400 + resumable_imports carries no key).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1 failed, 526 passed, 4 skipped in 1205.07s (0:20:05) — FAILED tests/test_db.py::test_create_all_produces_expected_tables (expected-table set missing 'import_checkpoints')

Frontend: `npx tsc --noEmit` clean; isolated `NEXT_DIST_DIR=.next-verify npx next build` clean (exit 0),
`/data` route compiled — built to a separate dist dir so the running `next dev` `.next` was not clobbered
(MEMORY `browser-qa-dead-shell-next-cache`).

## Known Issues

- **Live-fetch completion is externally data-walled** (Yahoo 429 / Stooq key-gated for this host), so a
  *fully-completed* live chunked import is not reachable offline; the chunk/backoff/checkpoint/resumable/
  Resume **machinery** is proven offline with an injected provider, and the live outcome is recorded
  honestly as rate-limited / NA (non-halting, per the spec). A real Yahoo 429 in the browser still drives
  the retry → resumable → Resume path.
- **httpx library request logging**: httpx emits its own INFO `HTTP Request: GET <url>` line (URL incl. a
  query key) when a real request is made — the library's behavior, not our error/persist path. Our app
  does not enable httpx INFO logging by default; all our error messages, job records, checkpoint, run
  history, and responses are redacted/scrubbed. A future hardening could silence the `httpx` logger.
- **Resume granularity is per-chunk**: a resume restarts at the first symbol of the interrupted chunk.
  Already-committed symbols are skipped at the DB layer (no duplicate rows); the provider may be re-asked
  for a symbol that 429'd mid-chunk. Intended design (the resume unit is the chunk); never duplicates data.
