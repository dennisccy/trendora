# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `StageTimings` block inside `JobProgressPanel` | New component | J-53: expose per-stage elapsed time, items processed, and concurrency to operator | Start a backfill-only job over an uncovered date range; wait for it to finish; verify the "Stage timings" section appears on the job card showing a Backfill sub-block with non-zero Elapsed, Dates count, and Concurrency value |
| `/data` | Backfill sub-block — `X.X× faster` speed-up line | New component element | J-53: make the parallel speed-up evidence visible on the job card itself | On a completed multi-date backfill job card, verify the Backfill sub-block shows a "per-date sum" value and a "X.X× faster than the per-date sum" label with a numeric ratio greater than 1 |
| `/data` | Fetch sub-block in `StageTimings` | New component element | J-53: show fetch stage timing (elapsed, symbols, concurrency) | Start a fetch+backfill job (e.g., alpha_vantage + demo key); after the fetch stage completes, verify the job card shows a Fetch sub-block with an Elapsed duration and a Symbols count matching the number of symbols fetched |
| `/data` | TermInfo tooltip on "Stage timings" label | New tooltip | J-47/J-53: new stat label must carry a help tooltip backed by the shared glossary | Hover the info icon next to the "Stage timings" section header on a job card; verify a tooltip appears with the glossary definition text (not empty, not the raw term key) |
| `/data` | TermInfo tooltip on "Concurrency" stat label | New tooltip | J-47/J-53: new stat label must carry a help tooltip backed by the shared glossary | Hover the info icon next to the "Concurrency" label inside a stage sub-block; verify a tooltip appears with the glossary definition text |
| `/data` | `StageTimings` — absent stage (honest NA) | Component behavior | J-53: a stage that never ran must not render | Start a backfill-only job (no fetch); verify the job card shows only the Backfill sub-block and no Fetch sub-block appears |
| `/` (dashboard) | Major-indexes & regime chart — DIA line | Updated data | J-44: DIA daily bars now committed in seed, so `/api/indexes` includes DIA | Load the dashboard; verify the Major-indexes chart legend shows exactly five entries including "Dow 30 (DIA)" and that the DIA line is drawn across the chart |
| `/methodology` | Glossary term list | New entries | J-53: two new config-backed glossary terms ("stage timings", "concurrency") added | Navigate to `/methodology` and verify both "stage timings" and "concurrency" appear as glossary entries with non-empty definition text |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/scanner.py` — split `run_scan` into `compute_run_payload` + `persist_run_payload`; `run_scan` is a thin compose of both; identical external behavior — no API surface or response shape change.
- `apps/backend/app/engine/prices.py` — lock-guarded `_BAR_CACHES` registry for thread-safety under parallel workers; no API surface change, no visible output change.
- `apps/backend/app/engine/data_manager.py` — parallel fan-out in `_do_backfill`; the stored snapshots and forward returns are byte-identical to the sequential path; the only externally visible change is the new `stages` field in the job payload (surfaced in the `/data` job card above).
- `apps/backend/scripts/benchmark_pipeline.py` — advisory benchmark script (Stage D parallel-vs-sequential report); never imported by the app, never a CI gate, not visible to end users.
- `apps/backend/tests/test_data_manager_backfill_parallel.py` and sibling test files — test infrastructure only; no user-visible impact.
- `apps/backend/app/config.py` — new `backfill_workers` required typed field with `>= 1` boot validation; controls parallelism but has no operator-facing UI — operators must edit `config.yaml` directly.

---

## Summary

- **Frontend surfaces changed:** 6 (StageTimings block, fetch sub-block, backfill sub-block with speed-up line, two TermInfo tooltips, dashboard DIA chart line, methodology glossary entries)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/app/data/page.tsx` — new `StageTimings` component wired into `JobProgressPanel`; `apps/frontend/lib/api.ts` — additive type additions)
- **Navigation changes:** no
- **Backend-only changes:** 6 (scanner split, bar-cache lock, data_manager parallelism internals, benchmark script, test files, config.py typed field)
