# goal-i_can_see_the_wealthy_future_forever-iter-25 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

This iteration describes the CODE actually changed (not the goal vision). All four targets are additive
on the existing `/data` Data Manager surface — no new page/route/nav, no scoring/scanner/snapshot change.

### J-37 — Missing-data diagnostic (backend)
- New `data_manager._missing_data_diagnostic(session, cfg)` — a read-only producer that reuses the SAME
  stored bars + `config.universe.symbols` + `indicators.min_history_bars` + the benchmark (SPY) trading
  calendar (`_trading_days`) the J-36 table / walk-forward already use. It emits three honest categories,
  each row carrying the symbol + the EXACT shortfall:
  - `no_history` — a universe member with 0 bars (`bars_have=0`, `bars_needed=threshold`, pull span = the
    calendar window).
  - `thin` — `0 < bar_count < indicators.min_history_bars` (`bars_have`/`bars_needed`; not pullable alone).
  - `intra_series_gap` — trading days (benchmark calendar) missing INSIDE the member's own first→last
    range (`missing_day_count`, `[first_gap, last_gap]`, a bounded `missing_preview`, and the gap pull span).
- Wired into the EXISTING `compute_coverage` payload as `coverage.diagnostic` (alongside `per_symbol`).
  No parallel module; no score/return/bucket/setup recomputed; thresholds + calendar from config.

### J-37 — Pull-missing job constructor (backend + API)
- `_run_job` / `run_data_job` / `start_data_job` gained an optional `symbols` override. A fetch with
  `symbols=[...]` restricts the chunk plan to EXACTLY the diagnosed-gap symbols — dispatched through the
  EXISTING J-34 chunked/checkpointed/resumable engine (`_chunk_plan` → `_run_chunked_fetch`), NO second
  fetch path. Per-`(symbol,date)` idempotency comes from the existing INSERT-new-only `_existing_dates`
  guard, so a re-pull duplicates nothing and overwrites no committed bar; on provider failure it surfaces
  an explicit failed/resumable state and fabricates no bar.
- `POST /api/data/jobs` (`JobCreate`) gained an optional `symbols` field; the handler normalizes
  empty/whitespace away and threads it to `start_data_job`. The response echoes the resolved `symbols`.

### J-38 — Unified Unfinished-imports view + Resume/Retry/Remove (backend + API)
- New `data_manager.unfinished_imports(session, cfg)` — a read-only union of resumable `ImportCheckpoint`
  rows + partial/failed `DataProviderRun` rows (excluding soft-dismissed ones and the plain seed-load
  non-job row). Each row carries a `record_type` (`checkpoint`|`run`), a stable `id`, a plain-language
  `state` string, `actions`, and progress/counts. Served on the EXISTING `GET /api/data` payload as
  `unfinished_imports` (the older `resumable_imports` field is kept for backward compatibility).
- New `retry_run(run_id, ...)` — re-dispatches a partial/failed run's SAME kind + `[start,end]` window
  through `start_data_job` (idempotent → re-fetches only what's missing); returns a NEW job id; the
  original audit run is never mutated.
- New `dismiss_import(session, record_type, record_id, ...)` — Remove/Dismiss drops ONLY the job-control
  record: a resumable `ImportCheckpoint` is DELETED; a partial/failed `DataProviderRun` gets a SOFT-dismiss
  flag (`dismissed=True`) so it leaves the actionable list but STAYS in the append-only Run-history audit.
  No immutable `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` row is touched.
- New endpoints `POST /api/data/jobs/{run_id}/retry` (404 unknown / 409 not-retryable / 400 needs-key) and
  `POST /api/data/jobs/{record_id}/dismiss?record_type=run|checkpoint` (404 unknown). Resume reuses the
  EXISTING `POST /api/data/jobs/{import_id}/resume`.

### Schema + migration (J-38)
- `DataProviderRun` gained a mutable `dismissed: bool = False` column (a job-control column on an
  already-mutable table — NOT a new table, NOT a snapshot column).
- Because this project has no Alembic, `app/db.py:create_db_and_tables` now runs an additive, idempotent
  `_ensure_additive_columns` backfill: it `ALTER TABLE … ADD COLUMN dismissed BOOLEAN NOT NULL DEFAULT 0`
  on an EXISTING `data_provider_runs` table that predates the column. A fresh DB already has the column
  (from the model). This preserves the "no DB regen" guarantee — the existing live DB gains the column in
  place (verified live; existing rows default to not-dismissed).

### Frontend (`/data`)
- `MissingDataDiagnosticPanel` — additive panel rendering the three categories (no-history / thin /
  intra-series gap), each row stating symbol + exact shortfall, with a per-row "Pull the missing data"
  button (pullable rows only) and a "Pull all missing" button. Empty diagnostic → a clean empty-state (no
  spurious pull). Pulls dispatch the gap-exact fetch and surface in the existing live job card.
- `UnfinishedImportsPanel` — REPLACES `ResumableImportsPanel`. Lists resumable + partial + failed, each
  with the server-built plain-language `state`, counts, and chunk progress. `ResumeControl` (checkpoint),
  new `RetryControl` (run; re-prompts the session-only key for a needs-key source), new `DismissControl`
  (Remove on checkpoints, Dismiss on runs).
- `lib/api.ts` — new `MissingDataDiagnostic` (+ category) types on `DataCoverage`; `UnfinishedImport` type
  on `DataOverviewResponse`; new clients `pullMissingData`, `retryDataJob`, `dismissUnfinishedImport`, and
  a `symbols` option on `startDataJob`.

### Re-capture only (NO code change)
- J-39 (seed-safe Remove-data confirm-preview) and J-35 (injected-provider expand) are unchanged — only
  their browser flows are to be re-captured by the QA/browser gate on a clean hydrated build.

## Files Changed
- `apps/backend/app/models.py` — add `DataProviderRun.dismissed` mutable job-control column (J-38).
- `apps/backend/app/db.py` — add idempotent additive-column backfill (`_ensure_additive_columns`) so an
  existing DB gains `dismissed` without regen (no Alembic).
- `apps/backend/app/engine/data_manager.py` — `_missing_data_diagnostic` + wire into `compute_coverage`
  (J-37); `symbols` override on the chunked fetch worker (J-37 pull); `unfinished_imports` union +
  `retry_run` + `dismiss_import` + `get_provider_run` + plain-language state strings (J-38).
- `apps/backend/app/api/data.py` — `symbols` on `JobCreate` + `start_job` (J-37 pull); `unfinished_imports`
  on `GET /api/data`; `POST …/retry` and `POST …/dismiss` endpoints (J-38).
- `apps/backend/tests/test_data_manager.py` — J-37 diagnostic (3 categories exact, threshold-from-config,
  empty, no-recompute, surfaced-on-coverage), pull constructor (gap-exact, idempotent, provider-failure),
  J-38 union + state strings + retry-outstanding-only + dismiss-preserves-audit + 404s.
- `apps/backend/tests/test_api_data.py` — pull/retry/dismiss endpoint shapes + 404/409/400 cases +
  `unfinished_imports` in overview + the CRITICAL key-leak regression through the pull job-status surface.
- `apps/backend/tests/test_db.py` — `dismissed` column assertion + the additive-migration test (an
  existing pre-column DB gains it in place; idempotent).
- `apps/frontend/lib/api.ts` — diagnostic + unfinished-import types and the pull/retry/dismiss clients.
- `apps/frontend/app/data/page.tsx` — the two additive panels (diagnostic with Pull; unified
  Unfinished-imports with Resume/Retry/Remove) + the pull/retry/dismiss handlers.

## Tests Run
Command (scoped during dev; full suite deferred to the QA gate per MEMORY `backend-test-suite-runtime`):
`cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_api_data.py tests/test_db.py -v`
Result: 102 passed (the three scoped files). Frontend `npx tsc --noEmit`: clean (no type errors).

Live verification on the actual host DB (`apps/backend/data/trendora.db`, backend booted on a temp port):
- `GET /api/data` returns `coverage.diagnostic` (threshold 200, affected_count 0 — every universe member
  has ≥200 bars and no gaps on this host, the honest healthy state) and `unfinished_imports` (12 rows: 1
  resumable checkpoint + 11 partial/failed runs), each with a correct plain-language state.
- No key leak anywhere in the payload (`token=`/`apikey=`/`"api_key"` all absent).
- `POST …/20/dismiss?record_type=run` → run 20 left the Unfinished list (12→11) but STAYS in Run history
  (audit-preservation boundary holds live).
- Retry/dismiss unknown id → 404; pull dispatch echoes the normalized gap-exact `symbols` (whitespace
  stripped) — not the whole universe.

## Known Issues
- The migration applied `data_provider_runs.dismissed` to the live host DB during the live smoke test (an
  additive, non-destructive `ADD COLUMN DEFAULT 0`); existing rows default to not-dismissed. The dismiss
  smoke test also soft-dismissed run id 20 on the live DB (it remains in Run history — reversible by
  clearing the flag). Neither affects any immutable snapshot/forward-return/audit row.
- The J-35 live market-cap expansion stays externally data-walled (universe.json absent → universe_count
  122) — recorded honestly NA / non-halting per goal.md; the offline injected-provider expand is unchanged
  and is the defining flow to re-capture.
- A real successful live pull/retry over a walled provider (Yahoo-429 / needs-key) is data-gated and
  non-halting — its absence does not block the iteration; the offline injected-provider pull is proven in
  unit tests and the error/rate-limited surface is verified with a real httpx error.
