**Verdict:** COHERENCE-PASS

## Coherence Audit — Iteration 12 (J-59/J-60/J-66/J-67 jobs-pipeline cluster)

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration index: 12
Snapshot SHA: 2c19c2c4c2b354054de495a8d69c4da99cf6334a

---

## Part A — Data Contract (no violations)

### Speedup factor consolidation (clears iter-8 COHERENCE-WARN)

The prior iter-8 COHERENCE-WARN documented that `speedupFactor` was computed client-side in
`apps/frontend/app/data/page.tsx:97` (dividing `per_date_seconds_sum` by `elapsed_seconds`). This
iteration resolves it:

- The client-side `speedupFactor()` function is **deleted** from `apps/frontend/app/data/page.tsx`.
- A new backend function `_compute_speedup` at `apps/backend/app/engine/data_manager.py:91` is the
  single canonical derivation site. It is called from `JobProgress.record_stage()` and the computed
  value is carried in the stages payload as `speedup_factor`.
- The frontend reads `backfillStage?.speedup_factor ?? null` at `apps/frontend/app/data/page.tsx:1227`
  and only re-formats it (`.toFixed(1)` display) — no client-side division.

This is the consolidation the blueprint's "Import job control" Data Contract row explicitly mandated
under J-66. One derivation site, one serving path. WARN residual cleared.

### New job-pipeline metadata fields (J-59/J-60/J-66/J-67)

`current_activity`, `last_progress_at`, `completed_stages`, `date_failures`, `job_id` (correlation id),
`completed_stages_json` — these are genuinely new operational metadata on the already-registered
"Import job control" Data Contract row (`data_manager:*`, served by `GET /api/data` and
`POST /api/data/jobs*`). None is conceptually the same as any existing canonical score or computed
value. All are computed by `apps/backend/app/engine/data_manager.py` (the registered engine) and
served by the registered endpoints. No duplicate computation, no non-canonical source.

### `job_progress` config knobs (J-66)

`poll_interval_seconds`, `heartbeat_stale_seconds`, `per_symbol_ticks` are configuration knobs served
through the existing `GET /api/data` overview endpoint (`data_overview` in
`apps/backend/app/api/data.py`). They are operational/display parameters, not canonical data values.
No new endpoint, no new canonical value.

### `sweep_orphaned_runs` / `interrupted` status (J-60)

The boot sweep marks orphaned `running` `DataProviderRun` rows `interrupted`. This is a lifecycle
transition on the existing `data_provider_runs` table — the same mutable job-control table the "Import
job control" and "J-60 — Job lifecycle record" rows are registered against. No snapshot table is
touched. No fabricated value.

### Advisory note — `benchmark_pipeline.py`

`apps/backend/scripts/benchmark_pipeline.py:197` prints an independent speedup ratio (`a / b`)
for developer terminal output. This is the J-46 advisory benchmark script, not a product Data
Contract value and not a UI surface. It is not a violation — it reads the same two underlying timing
figures from the job payload and the backend now officially computes `speedup_factor` from the same
formula. Advisory only.

---

## Part B — Information Architecture (no violations)

### Surface changes

Only `apps/frontend/app/data/page.tsx` was modified. No new page, no new route, no new router entry.
The modified components (`JobProgressPanel`, `JobLiveActivity`, `StageTimings`, `UnfinishedImportsPanel`,
`RunHistoryPanel`) are all within the existing `/data` Data Manager page.

### Reachability

`/data` is a top-level sidebar link at `apps/frontend/components/sidebar.tsx:40`:
```
{ href: "/data", label: "Data Manager", icon: Database }
```
Reachable in 1 click from any page. No parallel shell introduced.

### Duplicate home check

No existing entity gained a second home. All new UI elements (live activity line, heartbeat, symbols
counter, speedup display, date-failure detail, `running`/`interrupted` Run History rows,
`failed_backfill` Unfinished-imports entry) are within the registered `/data` canonical home.

---

## Part C — Advisory observations

1. `benchmark_pipeline.py:197` independently computes a speedup ratio for terminal display. Not a
   product surface, not registered in the Data Contract, not served by any endpoint. Advisory only.
2. The `statusLabel` helper in `page.tsx` maps `failed_backfill` → `"failed at backfill"` for display.
   The raw token and the friendly label refer to the same concept — no coherence issue.

---

## Summary

No objective Part A or Part B violations found. The iter-8 COHERENCE-WARN residual (client-side
`speedupFactor` division) is resolved: derivation moved to `data_manager.py:91`, frontend reads the
backend-supplied value. All new operational metadata belongs to already-registered Data Contract rows
served by already-registered endpoints. No new routes, no duplicate homes, no parallel shell.
