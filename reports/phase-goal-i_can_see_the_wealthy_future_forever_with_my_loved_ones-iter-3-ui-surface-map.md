# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-3 — UI Surface Map

**Phase:** J-46 — Parallel bounded-worker fetch, per-chunk transactional writes, load-bars-once backfill cache, committed advisory benchmark
**Frontend Present:** no (spec metadata); plan.md overrides to yes only to force browser regression — no frontend file was changed
**Classification:** Backend-only; no UI surface was added, removed, or redesigned. Existing surfaces require behavioral regression verification only.

---

## Changed file classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `config.yaml` | config | none | Adds `fetch_workers: 4` to `data_manager.import_chunking`; not displayed in the web app |
| `apps/backend/app/config.py` | backend-internal | none | New typed field `fetch_workers` + boot validation; not surfaced via any API response |
| `apps/backend/app/engine/prices.py` | backend-internal | none | `_BarCache`, `_BAR_CACHES`, `bar_cache()` context manager — internal optimization seam; no API surface change |
| `apps/backend/app/engine/data_manager.py` | backend-internal | behavioral regression | Parallel fetch rewires the same `/api/data/jobs` import flow; live progress counts and resumable semantics must be regression-verified |
| `apps/backend/app/engine/warmup.py` | backend-internal | none | Bar-cache activation inside warm-up cadence; no API or response change |
| `apps/backend/app/engine/scanner.py` | backend-internal | none | Bar-cache activation inside bootstrap cadence; no API or response change |
| `apps/backend/scripts/benchmark_pipeline.py` | backend-internal | none | Offline CLI benchmark; never imported by the API; no browser-accessible surface |
| `apps/backend/tests/test_data_manager_parallel.py` | backend-internal | none | Test file only |
| `apps/backend/tests/test_bar_cache.py` | backend-internal | none | Test file only |
| `apps/backend/tests/test_config.py` | backend-internal | none | Test file only |
| `apps/backend/tests/test_config_engine.py` | backend-internal | none | Test file only |
| `apps/backend/tests/test_sectors.py` | backend-internal | none | Test file only |
| `apps/backend/tests/test_themes.py` | backend-internal | none | Test file only |
| `apps/backend/tests/test_indexes.py` | backend-internal | none | Test file only |

---

## UI surface map — regression verification only

No UI surface was added, removed, or redesigned. The following table covers the existing surfaces whose runtime behavior must be regression-verified after the parallel-engine rewrite.

| Route/Page | Component/Element | Change Type | Why Changed | What to Test |
|-----------|------------------|------------|-------------|--------------|
| `/data` | Live progress counter (symbol count / total symbols) | Behavioral regression | Data manager now fetches symbols in parallel; counts must still be updated only after bars are committed, never exceed total | Start a multi-symbol import with source=alpha_vantage key=demo, watch the "X / Y symbols" counter during active fetching — confirm the count shown never exceeds the declared total while the job runs |
| `/data` | Job card status — amber "rate-limited — resumable" state | Behavioral regression | Parallel rewrite changed how a mid-chunk 429 is handled (chunk-atomic discard + resumable checkpoint); the amber state must still appear on rate-limit | On a rate-limited job (source=alpha_vantage key=demo, ~3 min to throttle), confirm the job card transitions to the amber "rate-limited — resumable" label and does not show "failed" |
| `/data` | Resume button on amber job card | Behavioral regression | Resume must continue from the last committed checkpoint with no duplicate fetch of already-committed bars; idempotency unchanged under the parallel rewrite | After a job reaches the amber resumable state, click Resume and confirm (a) the job card transitions back to running, (b) the final job summary shows no duplicate `(symbol, date)` coverage increase beyond what was committed before the pause |
| `/data` | Backfill-only job card — progress and ok summary | Behavioral regression | The bar-cache optimization now loads each symbol's bars once per backfill job; the backfill output must be byte-identical to before (no score drift, no truncated coverage) | Submit a small-range backfill-only job (seed date range, offline deterministic), confirm it progresses to an "ok" summary with the same coverage count as before this iteration |
| `/stocks` | Stock scores and A-E bucket display for NVDA | Behavioral regression | Bar-cache now sits beneath the scan engine; canonical score outputs must be identical to pre-iteration values | Open `/stocks`, locate the NVDA row, read the three scores and bucket label — confirm they are identical to the values shown before this iteration (spot-check, not a full regression sweep) |
| `/stocks/NVDA` | Detail page scores and bucket for NVDA | Behavioral regression | Same bar-cache path affects the detail page's engine call | Open `/stocks/NVDA`, confirm the three scores and A-E bucket are identical to the values shown on `/stocks` for the same symbol on the same as-of date |

---

## Surfaces confirmed unchanged (no regression testing required)

| Route/Page | Reason not affected |
|-----------|---------------------|
| `/` (dashboard) | No engine call change; scores are read from existing snapshots |
| `/methodology` | Static/informational page; no data fetch |
| `/settings` | No config-display surface for `fetch_workers`; not wired to UI |
| All other `/stocks/*` detail pages | Regression spot-check limited to NVDA per J-06 plan; the bar-cache is a loading optimization that cannot change the output of `bars_asof` for any symbol |
