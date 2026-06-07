# goal-i_can_see_the_wealthy_future_forever-iter-22 Execution Plan

**Two coupled deliverables on `/data`, IN ORDER. Part 1 (fix) MUST land before Part 2 (J-34) is
wired — J-34 threads the same source/key and surfaces *richer* per-chunk errors, so it re-leaks
unless the redaction fix is in place first.** Confined to the provider package + `data_manager` +
`config` + `models` (one new empty table) + `/data`. **No scoring/snapshot/forward-side touch → no
scanner DB regen → the 29 carried journeys' stored values stay byte-identical.**

## What to Build

**Part 1 — Fix the import key-leak (gates J-33 → passing) — DO FIRST**
- Redact at the error source in `data_providers/_http.py`: build `ProviderUnavailableError` from a
  **redacted request URL** (`exc.request.url.copy_with(query=None, fragment=None)`) **+ HTTP status**,
  never `str(exc)` (which embeds `?token=`/`?apikey=`). Handle both `httpx.HTTPStatusError` (request
  + response → include `HTTP {status}`) and `httpx.RequestError` (request, no response → omit status).
  Route the unparseable-body branch through the same redaction-safe helper.
- Defense-in-depth in `data_manager.py`: scrub the **resolved key value** out of any error string
  before it enters `JobProgress.errors` (the worker already holds the resolved key local in
  `run_data_job`). Pass the key (or a redactor closure) down to the fetch. **Never log/persist the key
  — the redactor only removes it.**
- Real-httpx-error regression test that closes the iter-21 mocked-provider blind spot.

**Part 2 — J-34: chunked, rate-limit-resilient, resumable import**
- Config-driven chunking block (`config.yaml` + typed `ImportChunkingCfg`, boot-validated all-positive):
  `symbol_batch_size`, `date_window_days`, `max_retries`, `backoff_base_seconds`, `backoff_cap_seconds`,
  `inter_request_sleep_seconds`. **No chunk/backoff/sleep literal anywhere in `data_manager.py`/providers.**
- `RateLimitError(ProviderUnavailableError)` raised on HTTP 429 (still redacted) in `_http.py`; Alpha
  Vantage `Note`/`Information` throttle body → `RateLimitError` in its `_parse` (best-effort).
- Durable **mutable job-control** table `import_checkpoints` (`ImportCheckpoint`) — `import_id`
  (= the live `JobProgress.job_id`), source, kind, range, `symbol_plan_json`, `chunk_total`,
  `next_chunk_index` (advanced ONLY after a chunk fully completes), cumulative counters, `status`
  ∈ running|resumable|ok|failed, timestamps. **Never stores a key.** Created via `metadata.create_all`.
- Chunked fetch engine replacing the single-shot `_do_fetch` loop (J-17's small jobs = one chunk):
  deterministic plan = symbol-batches × date-windows; reuse the existing `_existing_dates`
  INSERT-new-only guard for per-`(symbol,date)` idempotency; update `JobProgress` (new
  `chunk_index`/`chunk_total`) AND persist the checkpoint **after each completed chunk**; **injectable
  sleep** between requests. On `RateLimitError`: retry the current chunk with exponential backoff up to
  `max_retries`, then stop gracefully → `status="resumable"` (distinct from `failed`); **fabricate
  nothing, do not raise, do not halt.** Non-429 `ProviderUnavailableError` per symbol → count failed +
  redacted error + continue (unchanged).
- Resume path: `resume_data_job(import_id, *, api_key=None)` loads the checkpoint, re-registers a fresh
  `JobProgress` (same `import_id`), runs from `next_chunk_index`, re-fetches nothing stored.
  `POST /api/data/jobs/{import_id}/resume` (re-accepts the session-only key for a needs-key source —
  never persisted); `resumable_imports` array on `GET /api/data` (newest first; **never a key**) so the
  affordance survives a backend restart. Unknown/`ok`/`failed` → explicit `404`/`409`; needs-key resumed
  with no key → explicit `400`.
- Frontend: chunk **x/N** in `JobProgressPanel`; a distinct amber **"rate-limited — resumable"** state
  (symbols done vs remaining) with a **Resume** button (re-prompts the `type="password"` session key,
  in-memory only, cleared after); a post-restart **resumable-imports** surface from `GET /api/data`,
  each with a Resume button. `lib/api.ts` gains the chunk fields + `"resumable"` status, a
  `ResumableImport` type + `resumable_imports`, and `resumeDataJob(import_id, opts?)`.
- Backfill unchanged (deterministic/idempotent — not chunked, no 429 handling).
- **Fold iter-21 nit Finding #2:** set `source` on the job ONLY for fetch kinds
  (`source = (source or default_source) if kind in _FETCH_KINDS else None`) so a backfill-only header
  shows no source segment.

## Agents Required
- developer: **yes** — backend (Part 1 redaction fix + Part 2 chunk/backoff/checkpoint/resume engine,
  config, models, API) **and** frontend (chunk x/N, resumable state, Resume, resumable-imports list).
- backend-data: **yes**
- frontend-ux: **yes**

## Frontend Present
yes

## Files to Create/Modify
- `config.yaml` — add `data_manager.import_chunking` (6 tunables).
- `apps/backend/app/config.py` — `ImportChunkingCfg` (Pydantic, boot-validated all-positive →
  `ConfigError`); wire onto `DataManagerCfg` (after L926).
- `apps/backend/app/data_providers/base.py` — `class RateLimitError(ProviderUnavailableError)`.
- `apps/backend/app/data_providers/_http.py` — **redaction helper** (strip query/fragment, add status);
  raise `RateLimitError` on 429; route both error branches through it. *(Part 1 + Part 2)*
- `apps/backend/app/data_providers/alpha_vantage_provider.py` — map throttle `Note`/`Information` body
  → `RateLimitError`.
- `apps/backend/app/models.py` — `class ImportCheckpoint(SQLModel, table=True)` (`import_checkpoints`).
- `apps/backend/app/engine/data_manager.py` — key-scrub before `_record_error` *(Part 1)*; chunked
  engine + checkpoint persistence + 429-backoff→resumable + `resume_data_job` + injectable sleep +
  `JobProgress` chunk fields + Finding #2 source fold *(Part 2)*.
- `apps/backend/app/api/data.py` — `POST /api/data/jobs/{import_id}/resume`; `resumable_imports` on
  `GET /api/data`; 404/409/400 handling.
- `apps/frontend/lib/api.ts` — chunk fields + `"resumable"` status; `ResumableImport` +
  `resumable_imports`; `resumeDataJob()`.
- `apps/frontend/app/data/page.tsx` — chunk x/N, amber resumable state + Resume (key re-prompt),
  resumable-imports panel.
- **Tests:** `tests/test_provider_clients.py` (real `httpx.MockTransport` 429 + non-JSON body, key/query
  absent, redacted URL; 429 → `RateLimitError`); `tests/test_data_manager.py` (**extend, do NOT delete**
  `test_pasted_api_key_never_persisted` with a real httpx error — key absent from `JobProgress.errors`,
  `GET /api/data/jobs/{id}`, the checkpoint, `DataProviderRun`, `caplog`; chunk-plan config-driven;
  backoff/retry honored with **patched sleep**; durable checkpoint + resume + idempotency via a **fresh
  DB session**; key-never-on-checkpoint); `tests/test_config.py` (`ImportChunkingCfg` boot `ConfigError`
  on non-positive — add to the new required keys in ALL inline config fixtures); `tests/test_api_data.py`
  (resume 404/409/400; `resumable_imports` carries no key).
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-22-dev.md` — handoff **with the REAL
  pytest summary line** (no `__PYTEST_RESULT__` placeholder — iter-21 nit).
- `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md` — **VERIFY only** (see
  Assumptions): the decomposer already wrote the additive iter-22 note (L94), the J-34 checkpoint
  Data-Contract row (L190), and the invariant-#3 clarification (L210). Confirm accurate; **do not
  duplicate**; **no reapproval marker.**

## UI Evolution
- **New user-facing capability:** a large import runs in visible **batches**; on a provider rate-limit
  it **pauses cleanly in a resumable state** (progress saved to the DB) instead of failing, and the user
  can **Resume** it — even after restarting the backend — continuing from the next un-fetched chunk with
  no duplicate fetch or row. A pasted session key is now **verifiably never shown back anywhere.**
- **New information displayed:** per-chunk progress (**chunk x/N**); a distinct **rate-limited —
  resumable** job state with symbols done vs remaining; a **resumable-imports** list surviving a restart.
- **New user actions:** **Resume** a rate-limited import (from the live job card and from the
  post-restart list), re-supplying a session-only key for a key-required source.
- **UI surface changes:** `/data` job card gains a chunk indicator + a Resume affordance + a
  resumable state; `/data` gains a resumable-imports surface.
- **Navigation changes:** none (additive under the existing `/data` home).

## Visual Requirements
- **Component patterns:** reuse the existing `/data` `JobProgressPanel` (shadcn **Card/Button/Select/
  Input**); render **chunk x/N** inline beside the existing symbols/snapshots progress; **Resume** as a
  Button; the resumable-imports surface as a small Card panel (or run-history-style rows) — keep the
  existing run-history panel.
- **Layout:** existing `/data` page — no new page; additive panel + job-card affordances.
- **Key visual effects:** **amber `--warn` (#fbbf24)** for the resumable/paused state — explicitly
  distinct from red `--neg` `failed`; dark-workstation tokens only; **monospace `tabular-nums`** for all
  chunk/symbol counts.
- **States to handle:** running (chunk advancing), resumable/paused (amber + Resume), failed (red,
  unchanged), ok (complete); loading on the Resume POST; key field **cleared after submit**; empty
  resumable-imports list hidden.

## Key Test Scenarios (must pass for the phase to be complete)
1. **Key redaction (the fix):** a **real** `httpx.HTTPStatusError`/429 with the key in the request URL
   (via `httpx.MockTransport` + a real `httpx.Client` injected into the provider) → the message contains
   **neither the key nor the query string**; the redacted URL has no query. End-to-end: the sentinel key
   is **absent** from `JobProgress.errors`, `GET /api/data/jobs/{id}`, the `import_checkpoints` row /
   `resumable_imports`, every `DataProviderRun` column, and `caplog`.
2. **Browser UT-08 re-run (J-33):** start a fetch against a needs-key source with a pasted dummy session
   key while the provider is walled → explicit error/unavailable state with **the pasted key string
   absent** from the job-card error list and run history; no fabricated bar. (The iter-21 FAIL passes.)
3. **Chunk plan config-driven:** `chunk_total` derives from `symbol_batch_size` × `date_window_days`
   (vary config → `chunk_total` changes); **boot `ConfigError`** on a non-positive `import_chunking` value.
4. **Backoff/retry honored:** injected `RateLimitError` for K attempts then success → the chunk retries
   with backoff up to `max_retries` (**patch `sleep`, record durations — do not wait**); exceeding
   `max_retries` → a **`resumable`** job (distinct from `failed`), **nothing fabricated**, loop does not
   raise.
5. **Durable checkpoint + resume + idempotency:** pause at chunk k; a **fresh DB session** sees
   `ImportCheckpoint.next_chunk_index == k`; `resume_data_job` continues from k; with `_existing_dates`,
   **no `(symbol, date)` fetched or inserted twice** (no duplicate `DailyPrice`; already-stored symbols
   skipped); `resumable_imports` lists the paused import; `ok`/unknown resume → `409`/`404`; needs-key
   resume with no key → `400`.
6. **Key never on the checkpoint:** a paused job that used a pasted key → key absent from every
   `ImportCheckpoint` column and from `resumable_imports`.
7. **Browser J-34:** an import shows **chunk x/N** advancing; the scripted-429 path drives a **retry**
   then an amber **resumable** state with symbols done vs remaining + a Resume button; **restart the
   backend by port** → reload `/data` → the import is still listed **resumable** (from `GET /api/data`)
   → **Resume** continues from the next chunk and progresses/completes with no duplicate rows.
8. **Required-still-passing:** J-17 (backfill runs end-to-end, snapshots created; a sub-batch fetch
   completes as one chunk), J-18 (**exactly one date `<select>` app-wide** — chunk/Resume controls add
   NO date state; import dates stay `type="date"` job parameters), J-15 (read path untouched).
9. **Suite hygiene:** full backend pytest green, **run ONCE** (~14 min — MEMORY `backend-test-suite-runtime`;
   never two concurrent invocations; **sleeps patched/config-zeroed** so 429-retry adds no wall-clock);
   frontend `tsc --noEmit` + an **isolated** build clean (build to a separate dir / before `next dev` —
   MEMORY `browser-qa-dead-shell-next-cache`; confirm `GET /_next/static/chunks/main-app.js` → 200 and
   the health badge clears before browser QA).

## Assumptions & Scope Flags
- **No blocking questions.** The spec is exhaustive, internally consistent, and aligned with the
  re-scoped `docs/goal.md` (J-33 fix + J-34); anti-goals reproduced verbatim. No drift detected.
- **Blueprint DoD already satisfied by the decomposer.** The additive iter-22 note (blueprint L94), the
  `Resumable import checkpoint` Data-Contract row (L190), and the invariant-#3 clarification (L210) are
  already in the working tree, and the `ProviderCatalogCfg → ProviderCatalogEntry` naming nit already
  reads `ProviderCatalogEntry` (L188). **Developer VERIFIES presence/accuracy; does not re-add or
  duplicate; writes no reapproval marker.**
- **Live fetch is data-walled & non-halting** (Yahoo 429 / Stooq key-gated — MEMORY
  `data-provider-access-constraints`). Prove the chunk/backoff/checkpoint/resume machinery **offline**
  with an **injected provider scripted to raise `RateLimitError`/429 after K symbols** (+ `MockTransport`
  for the redaction test). **Do NOT make any live network call** in tests or the pipeline; **do NOT**
  autonomously re-probe J-22/23/24. A successful live import is recorded honestly as NA/rate-limited.
- **Principal risk = the same anti-goal twice.** Verify the fix **in source**, not just via QA: grep the
  live `GET /api/data/jobs/{id}` response, the job card, the checkpoint row, and `resumable_imports` for
  the sentinel key (MEMORY `httpx-error-leaks-url-query-key`). Drive a **real** httpx error — the
  existing `_FakeResponse` hard-codes `http://x` and cannot reach the leak path.
- **Immutability preserved:** `import_checkpoints` is mutable job-control state (like `JobProgress`/
  `DataProviderRun`), **not** a scanner snapshot — invariant #3 binds only
  `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` (untouched). Resume reuses the existing
  INSERT-new-only `DailyPrice` guard → a committed bar is never overwritten.
- **Config-fixture fan-out:** the new required `import_chunking` key must be added to **all** inline
  test config dicts, not just the obvious ones (MEMORY `config-fixtures-need-new-required-keys`).
- **Opportunistic nits while in-file:** real pytest counts in the handoff (no placeholder); fold Finding
  #2 (backfill header source) into the engine change; revert any cosmetic `tsconfig.json` churn if
  present (verify via git diff).

## Out of Scope (excluded — flag if requested)
- **J-35** (Expand-universe / `expand` job kind / `universe_pool.csv` screen / market-cap fetch) —
  iter-23, on this foundation. Do **not** add an `expand` kind here.
- Rewriting provider auth to header-based (redaction is sufficient); chunking the offline backfill;
  any change to scoring/snapshot/forward/research/read-serving paths or the `/stocks`·`/backtest`·
  `/research` pages; persisting a pasted key anywhere; adding a second viewing-date control.
