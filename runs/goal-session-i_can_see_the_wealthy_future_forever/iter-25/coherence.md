**Verdict:** COHERENCE-PASS

## Iteration: goal-i_can_see_the_wealthy_future_forever-iter-25 (index 25)

### Step 1 — Data Contract check

#### J-37 — Missing-data diagnostic + pull-missing constructor

- **Registered canonical source:** `app.engine.data_manager` (EXTENDED single coverage producer), blueprint Data Contract row added this iteration at line 218.
- **Canonical endpoint:** `GET /api/data` extended `coverage` payload; pull dispatch via `POST /api/data/jobs`.
- **What the iteration built:**
  - `_missing_data_diagnostic` function at `apps/backend/app/engine/data_manager.py:156` — a private helper called exclusively from `compute_coverage` at line 306. No parallel implementation found elsewhere.
  - `compute_coverage` remains the single public coverage function (`apps/backend/app/engine/data_manager.py:266`); the diagnostic is returned as `coverage.diagnostic` alongside the J-36 per-symbol table.
  - `GET /api/data` serves it via `data_manager.compute_coverage(session, cfg)` at `apps/backend/app/api/data.py:94` — the single canonical endpoint.
  - Pull-missing dispatches via `POST /api/data/jobs` with a `symbols` parameter (`api/data.py:119-130`) routed to `start_data_job(..., symbols=symbols)` — the EXISTING J-34 chunked engine; no second fetch path.
  - Frontend (`apps/frontend/app/data/page.tsx`) reads `coverage.diagnostic` verbatim from the API response and re-formats only; it does not compute any shortfall value. `pullMissingData` in `apps/frontend/lib/api.ts` calls `startDataJob("fetch", ...)` — the existing job-start path.
- **Verdict: no violation.** The diagnostic is computed once by the registered canonical module and served by the registered canonical endpoint. The pull reuses the J-34 engine; no second coverage/universe computation exists.

#### J-38 — Unified Unfinished-imports + Resume/Retry/Remove

- **Registered canonical source:** `app.engine.data_manager` (EXTENDED), blueprint Data Contract row added this iteration at line 220.
- **Canonical endpoints:** `GET /api/data` extended `unfinished_imports` payload; `POST /api/data/jobs/{id}/retry`; `POST /api/data/jobs/{id}/dismiss`; `POST /api/data/jobs/{import_id}/resume` (existing J-34).
- **What the iteration built:**
  - `unfinished_imports` function at `apps/backend/app/engine/data_manager.py:1762` — reads `import_checkpoints` + `DataProviderRun` rows; no value is recomputed.
  - Served on `GET /api/data` at `apps/backend/app/api/data.py:101` alongside the existing `resumable_imports` (kept for backward compatibility; the frontend renders only `unfinished_imports` at `page.tsx:292` — no duplicate panel rendered).
  - `retry_run` at `apps/backend/app/engine/data_manager.py:1798` calls `start_data_job` — the existing J-34 engine; no second fetch path.
  - `dismiss_import` at `apps/backend/app/engine/data_manager.py:1834` soft-dismisses (`DataProviderRun.dismissed = True`) or deletes a checkpoint; does not delete any `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` row.
  - New `dismissed: bool` column on `DataProviderRun` at `apps/backend/app/models.py:114` (mutable job-control flag); `test_db.py` updated in the same change with `test_data_provider_run_has_dismissed_column` at line 56 and `test_additive_migration_backfills_dismissed_on_existing_db` at line 64 — the iter-22 lesson applied.
- **Verdict: no violation.** The unfinished-imports list reads the same canonical job-control rows; Retry dispatches through the same J-34 engine; Dismiss mutates only job-control state; no snapshot/forward-return is touched; no duplicate computation.

#### Existing registered values — cross-check for new rival implementations

Grep of the diff for any new function whose name or logic matches registered canonical values (scores, buckets, returns, coverage, universe): none found. Changes are confined to `data_manager.py` (extended), `api/data.py` (extended), `models.py` (new column), `db.py` (additive migration), `page.tsx` (additive panels), `api.ts` (new client functions), and tests. No scoring/scanner/forward-testing/research/snapshot path was touched.

J-18 (exactly one date selector): `apps/frontend/app/data/page.tsx` uses `useAsOf()` at line 16/79 and holds no independent `date` state — `start`/`end` state at lines 81-82 are job parameter form inputs, not a global date control. No violation.

### Step 2 — Information Architecture check

No new pages, routes, or sidebar entries were introduced. All changes are additive panels on the existing `/data` page:

- `MissingDataDiagnosticPanel` (J-37) and `UnfinishedImportsPanel` (J-38) are new components on `/data`.
- `/data` (Data Manager) is reachable in 1 click via `apps/frontend/components/sidebar.tsx:39`: `{ href: "/data", label: "Data Manager" }` — within the 2 click rule.
- No parallel shell introduced. No duplicate home for any entity.
- `blueprint.reapproval-requested` is not written (correct — no nav-skeleton change).

### Step 3 — Advisory observations

WARN (advisory only): The `resumable_imports` array is still present on the `GET /api/data` response alongside `unfinished_imports` (`apps/backend/app/api/data.py:95` and `101`), described as "kept for backward compatibility". The frontend renders only `unfinished_imports` (`page.tsx:292`); the old `ResumableImportsPanel` is replaced. No data is displayed twice currently. If a future API consumer reads both fields it could surface the same resumable checkpoints twice — a future iteration may deprecate `resumable_imports` from the response to avoid confusion. No objective violation.

### Summary

| Rule | Status |
|------|--------|
| J-37 diagnostic computed by registered canonical module | PASS |
| J-37 pull dispatched through canonical J-34 engine (no second fetch path) | PASS |
| J-38 unfinished list reads canonical job-control rows (no recompute) | PASS |
| J-38 Retry dispatched through canonical J-34 engine | PASS |
| J-38 Dismiss mutates job-control only (no snapshot/forward-return deleted) | PASS |
| No duplicate computation of any existing registered value | PASS |
| Both J-37 and J-38 registered in blueprint Data Contract | PASS |
| No new page/route/nav entry | PASS |
| /data reachable 1 click from sidebar | PASS |
| No parallel shell | PASS |
| J-18 preserved (no second date state on /data) | PASS |
| test_db.py updated for dismissed column in same change | PASS |

