# goal-i_can_see_the_wealthy_future_forever-iter-3 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3
**Date:** 2026-06-01
**Agent:** developer
**Status:** complete
**Target journey:** J-17 — Grow the dataset by date / date range (Data Manager, full depth)

## What Was Built

**Backend**
- **Data Manager engine** `app/engine/data_manager.py` (new, ORCHESTRATION ONLY — no scoring/return math):
  - `compute_coverage(session, cfg)` — read-only descriptive metadata: price-history date range, distinct
    symbol count, the stored snapshot/as-of date set, and **gaps** (trading days with bars but no
    snapshot) with a config-bounded preview.
  - `run_data_job(...)` / `start_data_job(...)` — runs a single fetch and/or backfill job over a date or
    `[start, end]` range, with an **in-memory job registry** for live progress and a one-shot final
    summary persisted to the append-only `DataProviderRun`. Backfill calls the **existing**
    `scanner.run_scan` (create-once, bars ≤ D) then `forward_testing.backfill_run_forward_returns`
    (INSERT-only, bars > D). Fetch pulls real EOD via the config-selected live provider and persists only
    NEW `(symbol, date)` rows; a per-symbol provider failure is counted and surfaced with **zero
    fabricated bars**. `validate_job_request` rejects an unknown kind / inverted range / over-long range.
- **Live provider** `app/data_providers/stooq_provider.py` (new) — `StooqProvider(PriceProvider)` fetching
  real EOD bars from Stooq via `httpx`; on any network/HTTP/parse/unknown-symbol failure it
  RAISES `ProviderUnavailableError` and returns zero bars (mirrors `SeedProvider`; never fabricates).
  Plus a name→provider **factory** `app/data_providers/make_provider` (`seed`→SeedProvider,
  `stooq`→StooqProvider, lazy import).
- **API** `app/api/data.py` (new router, included in `main.py`):
  - `GET /api/data` → coverage + recent fetch/backfill run history.
  - `POST /api/data/jobs` → validate + start the async job, return `{ job_id }` immediately
    (422 malformed date / unknown kind via the typed model; 400 inverted / over-long range; 503 no data).
  - `GET /api/data/jobs/{job_id}` → live status/progress → final summary (404 unknown id).
- **Config** — new typed `DataManagerCfg` (`config.py`) + a `data_manager` block in `config.yaml`
  (`live_provider`, `max_range_days`, `gap_preview`, `run_history_limit`) — every job limit comes from
  config (no magic numbers). The boot/runtime `provider` stays `seed`; the live provider is resolved by
  the fetch path only.

**Frontend** (see also `...-iter-3-frontend.md`)
- New `/data` page (coverage panel, job form, live-progress polling, run-history table, honest
  loading/empty/error states); additive `refresh()` on the global as-of provider (called on job
  completion so new dates are selectable without a reload); a `Data Manager` sidebar entry; and typed
  `fetchDataCoverage` / `startDataJob` / `fetchDataJob` API client.

## Files Changed

- `config.yaml` — new `data_manager` block (live_provider/max_range_days/gap_preview/run_history_limit).
- `apps/backend/app/config.py` — new `DataManagerCfg`; added `data_manager` to `Config`.
- `apps/backend/app/engine/data_manager.py` — **new** (coverage + job orchestration + in-memory registry + run history).
- `apps/backend/app/data_providers/stooq_provider.py` — **new** live provider (real-data-only; raises, never fabricates).
- `apps/backend/app/data_providers/__init__.py` — added `make_provider` factory + `DEFAULT_SEED_DIR`.
- `apps/backend/app/api/data.py` — **new** router (3 endpoints; async job start).
- `apps/backend/main.py` — included `data.router` under `/api` (lifespan UNCHANGED).
- `apps/backend/tests/conftest.py` — registered the `integration` pytest marker.
- `apps/backend/tests/test_data_manager.py` — **new** (coverage; backfill-grows-n; lookahead-free+reuse; create-once/immutable; config-driven; fetch forced-failure).
- `apps/backend/tests/test_api_data.py` — **new** (job lifecycle; 4xx/503/404 validation; isolated engine so the shared DB is not polluted).
- `apps/backend/tests/test_stooq_provider.py` — **new** (forced-failure no-fabrication units + one `@pytest.mark.integration` real fetch).
- `apps/backend/tests/test_config.py`, `tests/test_config_engine.py` — added `data_manager` to the valid-config fixtures + new validation tests.
- `apps/backend/tests/test_sectors.py`, `tests/test_themes.py` — added `data_manager` to the inline synthetic-config fixtures (now-required section).
- `apps/frontend/app/data/page.tsx` — **new** Data Manager page.
- `apps/frontend/components/asof-provider.tsx` — additive `refresh()`.
- `apps/frontend/components/sidebar.tsx` — `Data Manager → /data` nav entry.
- `apps/frontend/lib/api.ts` — Data Manager types + 3 client functions.

## Tests Run

- **Backend, full suite:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
  Result: **294 passed, 1 skipped, 0 failed** (295 collected; runtime ~15 min). The 1 skip is the
  live-Stooq integration test (offline / apikey-gated — see External Integration). The first full run
  surfaced 2 failures in `test_sectors.py` / `test_themes.py` whose inline synthetic configs predated the
  new required `data_manager` section; both were fixed (added `data_manager` to those fixtures) and
  re-verified green (8/8). A confirming full re-run completed: **294 passed, 1 skipped, 0 failed**.
- **Backend, new/changed modules** (`test_data_manager`, `test_api_data`, `test_stooq_provider`,
  `test_config`, `test_config_engine`, `test_no_magic_numbers`, `test_db`):
  **84 passed, 1 skipped** (the skip is the live-Stooq integration test — see External Integration below).
- **Frontend:** `cd apps/frontend && npm run build` → ✓ compiled, types valid, 13 routes incl. `/data`.

Key proofs (named tests in `test_data_manager.py`): backfill **grows `n`** and adds the expected
`ScannerRun` rows; a backfilled snapshot **equals the canonical `score_stocks(D)` verbatim** and its
forward returns use only bars > D (**lookahead-free + reuse**, no second math path); re-running the same
range creates **0 new snapshots** and mutates no `created_at` (**create-once / immutable**);
`DataProviderRun` is **append-only** (one row per job); the max-range guard reads **config**; a forced
provider failure writes **0 bars / 0 snapshots** and a `failed` run.

## External Integration Testing (per core.md)

- The live Stooq fetch was **exercised against the real endpoint** by the
  `@pytest.mark.integration` test. **Result: the live fetch did NOT succeed** — Stooq now gates its free
  daily-CSV endpoint behind an API key and returns an "apikey required" HTML page instead of CSV. The
  `StooqProvider` correctly treats that non-CSV body as `ProviderUnavailableError` (real-data-only; it
  fabricated nothing), so the integration test **skips honestly** rather than silently passing.
- This is documented as a Known Issue (below), not papered over. It does **not** block J-17: the
  acceptance flow uses the offline **backfill** path. The forced-failure (no-fabrication) contract is
  proven both by an offline stub unit test AND by the real endpoint's apikey gate.

## Coherence Notes (for reviewer / coherence-auditor / J-18 re-verify)

- **No second scan/return path.** `run_data_job` ORCHESTRATES `scanner.run_scan` +
  `forward_testing.backfill_run_forward_returns` (and the `get_run_for_date` create-once guard). No
  scoring/forward-return math exists in `data_manager.py`. Coverage is descriptive only.
- **`/data` date inputs are JOB PARAMETERS, not a viewing as-of control.** They are NOT bound to
  `useAsOf`/the global switcher and create no second viewing-date state — J-18 / "exactly one date
  selector" holds. (This is the deliberate, expected presence of date inputs on a non-as-of page.)
- **`refresh()` is additive + non-disruptive.** It only re-fetches the available run dates; it never
  changes the user's `asOf`, and an older-date backfill leaves `latest` unchanged.
- **Default boot unchanged.** `main.py` lifespan still bootstraps the quarterly seed snapshots only; the
  live provider is never reached on boot. `provider: seed` is untouched.

## Known Issues

- **Live Stooq fetch unavailable in this environment** — Stooq's free CSV endpoint now requires an API
  key; the provider surfaces this as an explicit failure with zero fabricated data (correct behavior),
  and the live integration test skips. Restoring live fetch needs a Stooq API key (env-only) or another
  free EOD provider behind the same `PriceProvider` interface — a small, isolated change. The offline
  backfill path (J-17's acceptance flow) is fully functional.
- **One active job at a time** (SQLite single-writer; concurrent jobs are out of scope). Live progress is
  in-memory and resets on backend restart; every run's final summary persists in the run-history table.

## Suggested Next Phase

Per the spec's plan: a single **closure / re-verify** pass that converts the five iter-0 partials
(J-02 filter interaction, J-06 cross-page numeric compare, J-11 add+restart, J-15 warm-load timing,
J-16 VCP filter→badge→detail→glossary) via their full acceptance flows → GOAL_ACHIEVED if nothing
regressed. J-17 (this iter) plus J-18/J-19 should remain green throughout.
