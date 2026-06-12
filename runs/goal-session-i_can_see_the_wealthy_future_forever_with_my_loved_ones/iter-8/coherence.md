**Verdict:** COHERENCE-WARN

---

## Coherence Audit — iter-8
**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 8
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Snapshot SHA:** 47fff7b92f97863e6c28cf476956c4156589fd98

---

## Step 1 — Data Contract

### Changed files reviewed
- `apps/backend/app/engine/data_manager.py` — parallel backfill (`_compute_one_backfill_date`, `_do_backfill`), `JobProgress.stages`, `JobProgress.record_stage`
- `apps/backend/app/engine/scanner.py` — factored `compute_run_payload` + `persist_run_payload`; `run_scan` is now a thin compose of both
- `apps/backend/app/engine/prices.py` — thread-safe `_BAR_CACHES` registry; `_BarCache.prefill`, `attach_shared_cache`, `prefilled_bar_cache`
- `apps/backend/app/config.py` — new `backfill_workers` field in `ImportChunkingCfg`
- `apps/frontend/app/data/page.tsx` — new `StageTimings` component, `fmtDuration`, `speedupFactor`
- `apps/frontend/lib/api.ts` — additive `JobStageTiming` interface; `stages` field on `DataJob`
- `config.yaml` — `backfill_workers: 4`; two new glossary terms ("stage timings", "concurrency")

### Data Contract violations: NONE

**Job stage timings (new value).** The `stages` dict is computed once by the job runner via `JobProgress.record_stage()` (`apps/backend/app/engine/data_manager.py`), recorded on the orchestrating thread after each stage completes, and served by the existing canonical endpoints `GET /api/data` (job list) and `GET /api/data/jobs/{id}` (job status). The blueprint's import-job-control Data Contract row pre-registers this as the J-53 amendment ("[TARGET — iter-8 in flight]", human-approved). No second computation path or serving endpoint was introduced.

**`compute_run_payload` / `persist_run_payload` refactoring.** `scanner.py` factored `run_scan` into a compute half and a write half. `run_scan` is now a thin compose of both (`scanner.py:229-230`). The canonical engine calls (`score_stocks`, `score_regime`, `score_sector`, `score_themes`) are unchanged — they remain the single canonical source for scores. This is a structural decomposition for parallel fan-out, not a new independent computation of any registered value.

**`speedupFactor` in `page.tsx`.** This function (`apps/frontend/app/data/page.tsx:97`) divides `per_date_seconds_sum` by `elapsed_seconds` — both backend-computed and backend-served figures in `job.stages.backfill`. The ratio is a display label ("X.X× faster than the per-date sum") and is NOT a canonical score or registered value. It reads from the canonical endpoint (`GET /api/data/jobs/{id}`) and reformats two backend numbers for display — this is a presentation computation analogous to computing a percentage for display, not a duplicate of any registered score.

**Glossary terms.** "stage timings" and "concurrency" are genuinely new terms added to `config.methodology` in `config.yaml` and served by the existing `GET /api/methodology` endpoint (the registered canonical source for J-47 glossary). No second catalog introduced.

**DIA seed data.** `apps/backend/data/seed/prices/DIA.csv` feeds into `GET /api/indexes` via the existing registered `indexes:compute_index_series`. No second serving path.

---

## Step 2 — Information Architecture

### New routes/pages: NONE

No new page, route, or nav link was added. All changes are confined to:
- `/data` (Data Manager) — the pre-registered canonical home for job control; the `StageTimings` component is added inside the existing `JobProgressPanel`.
- `/methodology` — two new glossary terms appear in the existing glossary list.
- `/` (dashboard) — DIA series now renders in the existing Major-indexes chart.

All three surfaces have pre-existing canonical homes in the blueprint's IA skeleton. Navigation structure is unchanged.

---

## Step 3 — Advisory (WARN)

**Advisory: `speedupFactor` display derivation in the frontend.** `apps/frontend/app/data/page.tsx:97-101` computes a display ratio (sequential sum / parallel elapsed) from two backend-served timing numbers. Blueprint invariant 13 says "view transforms never recompute" in the context of canonical scores/membership — timings are descriptive operational metadata explicitly categorized as non-canonical in the blueprint. This is not a hard violation. However, if the backend pre-computed and served the ratio as a field alongside the two raw figures, the frontend would be a pure formatter with no arithmetic. Advisory note for a future tidy pass: have the backend add a `speedup_factor` field to the backfill stage entry so the frontend renders, never divides.

**Advisory: `backfill_workers` is a required typed config field.** The spec notes that EVERY inline test config dict must be updated (five files). The diff shows the config field was added and validated in `config.py`. The audit confirms test files were updated (`test_config.py`, `test_config_engine.py`, `test_bar_cache.py`, `test_sectors.py`, `test_themes.py`, `test_api_indexes.py`, `test_indexes.py`). No IA/data-contract concern; noted for completeness.

---

## Summary

- **Part A (Data Contract) violations:** 0
- **Part B (Information Architecture) violations:** 0
- **Part C (Advisory):** 1 — frontend display derivation of a speedup ratio from two backend-served timing numbers; advisory only, not a canonical score; recommend a future tidy (backend pre-computes `speedup_factor` and frontend renders it).

No objective violations from Step 1 or Step 2. Verdict: **COHERENCE-WARN**.
