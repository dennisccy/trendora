# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

### J-53 — parallel multi-date backfill + per-stage job timings (the target journey)
- **Parallel multi-date snapshot backfill** (`apps/backend/app/engine/data_manager.py::_do_backfill`):
  the per-date COMPUTE (the expensive scoring engines) is now fanned out to a bounded pool of
  `backfill_workers` threads. Each worker opens its OWN read-only `Session` (a separate SQLite
  connection — concurrent readers are safe) and a per-session `bar_cache`, computes the canonical
  snapshot payload (regime/sectors/themes/stocks) for one date, and returns it as plain data. The
  ORCHESTRATING thread owns EVERY DB write: it persists each payload in **date order** via the new
  create-once `scanner.persist_run_payload`, then INSERTs forward returns — serially, transactionally.
  With `backfill_workers == 1` this is the byte-identical sequential baseline.
- **Scanner split** (`apps/backend/app/engine/scanner.py`): `run_scan` is split into
  `compute_run_payload` (pure compute, no writes) + `persist_run_payload` (write-only, owns the
  create-once / idempotent / concurrency-safe IntegrityError guards). `run_scan` is now a thin compose
  of the two — identical behavior and output. This is what lets workers compute off-session and the
  orchestrator write on-session.
- **New config knob** `data_manager.import_chunking.backfill_workers` (committed default 4, boot-validated
  `>= 1`, no magic numbers) in `config.yaml` + `apps/backend/app/config.py` (mirrors `fetch_workers`).
- **Per-stage timings** on `JobProgress` (`stages` dict + `record_stage()`): for each EXECUTED stage —
  `fetch` {elapsed_seconds, items_processed=symbols, concurrency=fetch_workers} and `backfill`
  {elapsed_seconds, items_processed=dates, concurrency, per_date_seconds_sum}. The backfill
  `per_date_seconds_sum` (the sum of each date's compute time) is the sequential baseline the parallel
  wall-clock beats, so the job's OWN payload evidences the ≥~2× speedup. A stage that never ran is
  ABSENT from `stages` (never a fabricated zero). Served by the existing `GET /api/data/jobs/{id}`
  (the job card's poll source) and persisted into the `DataProviderRun` audit detail JSON.
- **Bar-cache thread-safety** (`apps/backend/app/engine/prices.py`): the `_BAR_CACHES` registry dict is
  now lock-guarded for insert/lookup/pop so concurrent backfill workers (each on its own session ⇒ a
  distinct key) never race the shared dict. A given session's `_BarCache` is still only ever touched by
  its own single owning thread.
- **Benchmark extension** (`apps/backend/scripts/benchmark_pipeline.py`): a new **Stage D — MULTI-DATE
  BACKFILL job** times the real `run_data_job` backfill serial (`backfill_workers=1`) vs the config pool
  over the same K dates, reporting the job's own `per_date_seconds_sum` so the speedup is visible.
  Advisory only — no CI wall-clock gate.

### Frontend (J-53)
- **Stage-timings block** on the `/data` job card (`apps/frontend/app/data/page.tsx::StageTimings`):
  fetch vs backfill — elapsed (human-readable), items (symbols / dates), concurrency (`N×`); the backfill
  block also shows the per-date sum and a `X.X× faster than the per-date sum` line. Pure re-formatting of
  `job.stages` — no derived figure beyond display formatting. A stage that never ran simply does not
  render (NA honesty). Dates use the shared `lib/dates.ts` formatter; durations via a new `fmtDuration`.
- **New stat labels carry J-47 `TermInfo` tooltips** ("Stage timings", "Concurrency") reading two NEW
  config-backed glossary entries under `config.methodology.terms` (`stage timings`, `concurrency`). The
  catalog mechanism is unchanged; tooltip triggers are SIBLINGS of the label text, never nested.
- **api.ts**: additive `JobStageTiming` type + `stages?: Record<string, JobStageTiming>` on `DataJob`.

### One-shot best-effort data fetch (J-22/J-23/J-24 + DIA — single attempt, dispositioned independently)
- **DIA (J-44 legend leg): SUCCEEDED — committed.** A single one-shot fetch via the Yahoo EOD provider
  pulled **1356 real DIA bars** over the full seed range (2021-01-04 → 2026-05-28, matching SPY) and
  committed them to `apps/backend/data/seed/prices/DIA.csv`. `all_seed_symbols` now also includes the
  `index_chart.symbols` legend set (`apps/backend/app/seed_loader.py`) so the committed DIA.csv loads
  into `daily_prices` on a fresh seed (verified: 159 symbols ok / 0 failed; DIA renders in the J-44
  index-chart legend as "Dow 30 (DIA)" with 1356 points).
- **J-22 expanded universe: BLOCKED — honest NA.** The Yahoo EOD *chart* endpoint works, but the
  market-cap reference endpoint the expand screen requires returns **HTTP 401** (`/v7/finance/quote`
  walled). The config screen needs a real market cap; with no cap feed reachable it can produce no
  passers without fabricating. Zero bars/caps fabricated. (Auto-unblocks via J-35 once an operator
  points the Data Manager at a cap-capable reachable provider — no code change.)
- **J-23/J-24 intraday seed: BLOCKED — honest NA.** There is no buildable fetch path: the provider
  abstraction has no intraday method (Yahoo provider is `interval: 1d` only) and the timeframe-aware
  store/pipeline is not built — and building it is explicitly OUT OF SCOPE this iteration. No intraday
  bars attempted/fabricated.

## Files Changed
- `apps/backend/app/engine/data_manager.py` — parallel `_do_backfill` (compute fan-out, serialized writes), `_compute_one_backfill_date` worker, `JobProgress.stages` + `record_stage()` + `to_dict`, fetch/backfill stage-timing recording in `_run_job`, stage timings into `_persist_run` audit detail
- `apps/backend/app/engine/scanner.py` — split `run_scan` into `compute_run_payload` + `persist_run_payload`; `run_scan` recomposes them
- `apps/backend/app/engine/prices.py` — lock-guarded `_BAR_CACHES` registry (thread-safe under parallel workers)
- `apps/backend/app/config.py` — `backfill_workers` typed required field + `>= 1` boot validation
- `apps/backend/app/seed_loader.py` — `all_seed_symbols` includes the `index_chart.symbols` legend set (loads committed DIA.csv)
- `apps/backend/scripts/benchmark_pipeline.py` — Stage D parallel-vs-sequential multi-date backfill report
- `config.yaml` — `backfill_workers: 4` knob; new `methodology` glossary entries `stage timings` + `concurrency`
- `apps/backend/data/seed/prices/DIA.csv` — NEW committed DIA seed (1356 real bars, one-shot fetch)
- `apps/frontend/app/data/page.tsx` — `StageTimings` block on the job card; `fmtDuration` / `speedupFactor` helpers
- `apps/frontend/lib/api.ts` — `JobStageTiming` type + `DataJob.stages`
- `apps/backend/tests/test_data_manager_backfill_parallel.py` — NEW: equality, idempotency, timings, worker-exception, progress-honesty
- `apps/backend/tests/test_config.py` — `backfill_workers` fixture + 4 new validation tests
- `apps/backend/tests/test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py` — `backfill_workers` added to the inline import_chunking config dict

## Benchmark (advisory — never a CI gate)
`scripts/benchmark_pipeline.py --dates 6 --fetch-symbols 12` (offline, on the committed seed):
- **Stage D — MULTI-DATE BACKFILL job (the J-53 win):** serial (backfill_workers=1) **73.86 s** →
  parallel pool (backfill_workers=4) **6.39 s** → **11.56× speedup** over 6 dates. The serial run's own
  `per_date_seconds_sum` is **59.63 s** (the sequential baseline the parallel wall-clock beats). This is
  well above the ≥~2× target and is evidenced by the job's OWN stage timings.
- Stage A — symbol FETCH: serial 0.40 s → pool 0.13 s (3.16× — J-46, unchanged).

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (run in targeted batches; full suite handed to the pump)
Result (targeted modules, all green):
- `test_data_manager_backfill_parallel.py` — 9 passed (byte-identical parallel-vs-sequential equality over a 4-date range; idempotent re-run; honest stage timings; worker-exception → explicit failed + no partial snapshot)
- `test_bar_cache.py + test_data_manager_backfill_parallel.py` — 17 passed (the load-once-per-job invariant proven under the PARALLEL build via the shared pre-filled cache)
- `test_config.py + test_indexes.py + test_sectors.py + test_themes.py + test_config_engine.py` — 108 passed (incl. the new backfill_workers boot-validation tests)
- `test_warmup.py + test_data_manager_parallel.py` — 18 passed (warm-up determinism + J-46 parallel fetch contracts intact under the scanner split)
- `test_data_manager.py + test_forward_testing.py + test_scanner.py` — 121 passed (the run_scan split + shared-cache refactor produce identical output)
- `test_api_data.py + test_api_indexes.py + test_api_methodology.py` — 66 passed (the `stages` payload serves; DIA now renders in the index chart; the 2 new glossary terms serve — 111 total, ≥100 J-47)
- Frontend gate: `cd apps/frontend && npx tsc --noEmit` — clean (exit 0)

The FULL backend suite (~45–65 min) is handed to the pump per the runtime lesson (a dev-turn background run does not survive the turn; never two trendora pytest runs concurrently).

**FULL SUITE RESULT (run by the pump to completion in a single invocation):** **724 passed, 4 skipped, 0 failed** in 3394.92s (0:56:34); PYTEST_EXIT=0. Log: `/tmp/trendora-iter8-fullsuite.log` (START 2026-06-12T18:27:26Z → END 2026-06-12T19:24:02Z). +14 tests vs iter-7's 710 (new `test_data_manager_backfill_parallel.py` + `test_bar_cache.py` + `backfill_workers` config-validation tests). The parallel-vs-sequential **byte-identical equality** tests pass — the J-53 concurrency rewire (compute on worker threads, all writes serialized on the orchestrating thread, shared pre-filled bar cache) introduced no snapshot/forward-return regression; the DIA-present index tests are green. (An unrelated `tapeology` pytest shared CPU late in the run — separate project/DB, no interference.)

## Known Issues
- **J-22 / J-23 / J-24 are honest blocked-NA** (see dispositions above) — NON-VETOING per goal.md's
  "Data-dependent journeys (non-halting)" section. They must not halt the loop, drive STALLED, or veto
  GOAL_ACHIEVED. No fabricated data was introduced for any of them.
- **The ≥~2× speedup is advisory** — evidenced by the job's own timings (`elapsed_seconds` vs
  `per_date_seconds_sum`) and the benchmark Stage D, NOT asserted by a CI wall-clock test (flaky). The
  equality test (parallel output == sequential output) is the hard guard; the speedup is observable but
  not gated.
- **Backend restart required for browser QA** so the new `stages` payload field serves (kill by port
  8835/3835 only, never broad pkill — this is a multi-project machine).
- For browser QA: a **backfill-only job over an uncovered seed range** deterministically exercises the
  backfill stage + timings regardless of provider reachability; DIA is now committed so the J-44 legend
  shows 5 lines. The DIA seed change means a fresh DB now loads 159 symbols (was 158).
- **Live-DB DIA load (done):** the live host's `trendora.db` existed before this run (so `load_seed` —
  gated on emptiness — would not reload prices), so I loaded the committed DIA bars into the live DB via
  the SeedProvider (real committed data, idempotent INSERT-new-only). Verified live: `GET /api/indexes`
  now returns the 5-line legend including DIA. A fresh DB gets DIA automatically via the seed path.
- **Service-startup smoke (done):** started the backend on :8835, confirmed `GET /api/health` 200,
  `GET /api/indexes` shows DIA, and a live 3-date backfill job returned honest stage timings
  (`backfill: items_processed=3, concurrency=3, per_date_seconds_sum=1.30`). Stopped cleanly by port
  (no stray uvicorn; :8835 and :3835 free).
