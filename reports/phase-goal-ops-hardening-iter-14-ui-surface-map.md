# Phase goal-ops-hardening-iter-14 — UI Surface Map

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## Context: no frontend files changed, but three existing surfaces are behaviorally affected

Zero files under `apps/frontend/` appear in this iteration's diff (confirmed via `git status`/`git
diff --stat`). The only product/test files touched are `apps/backend/app/engine/forward_testing.py`
(modified — the two-read rewrite), `apps/backend/tests/test_forward_testing_aggregates_streaming.py`
and `apps/backend/tests/test_forward_testing_concurrency.py` (both new test files), and
`reports/perf-budgets.md` (modified — a non-UI reporting artifact; `blueprint.md` itself documents
this file as "not a UI page"). The rewritten function, `compute_forward_aggregates`, is the sole
computing module behind `GET /api/backtest` (unchanged, byte-identical file) and the ingest finalize
hook's forward-aggregate warm step (`_refresh_ingest_aggregates` in
`apps/backend/app/engine/data_manager.py`, also byte-unchanged this iteration) — both already
consumed by existing frontend code. Because this iteration's entire purpose is fixing an
availability/resilience defect (a frozen badge / a ~12-minute full-backend wedge, reproduced twice
this session), the rows below capture the resulting behavior change on those existing surfaces, per
this dispatch's operator note not to suppress this report on account of `Frontend Present: no`. Every
row is annotated with the backend mechanism that drives it.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| (global — all pages) | `HealthBadge` top-bar readiness pill, `data-testid="readiness-badge"` (`apps/frontend/components/health-badge.tsx`, rendered globally from `apps/frontend/app/layout.tsx`) | Changed behavior (availability/resilience only — no visual, label, or polling-logic change) | The badge's `loading`/`error` states were reachable for the ~12-minute duration of iter-13's concurrent-load wedge (root cause: `compute_forward_aggregates`'s unbounded `ForwardReturn`/`ScannerResult` `.all()` reads inside the SAME ingest finalize warm this rewrite targets). The rewrite removes that unbounded read. | Trigger a real backfill/rebuild job on `/data` that lands new price bars for the benchmark/index symbols (mirroring J-01/J-03/J-05's own replay scripts — the same method browser-qa is instructed to use), so the finalize hook runs the rewritten forward-aggregate warm for all 5 horizons. While the job is in flight, repeatedly read the badge's `data-state` attribute (or screenshot every few seconds) and confirm it is never `data-state="loading"` for more than one polling interval and never `data-state="error"` at any point during the job. |
| `/backtest` | Per-horizon evidence panel — the `by_horizon` scorecard table, return-attribution leadership lists, and `BacktestSkeleton` loading state (`apps/frontend/app/backtest/page.tsx`) | Changed behavior (availability/resilience only — `GET /api/backtest`'s response content is proven byte-identical, TC-1/TC-2; only its reliability under memory pressure changes) | On a cache-miss, this page's fetch resolves through the SAME rewritten `compute_forward_aggregates` path. Previously a cache-miss under heavy load could hang on `BacktestSkeleton` for minutes or resolve to the "Backend unavailable" error card (`apps/frontend/app/backtest/page.tsx:138-149`). | Force a cache-miss (e.g., trigger a backfill that changes the latest scanner run's forward-return data, invalidating `ForwardAggregateCache` for that as-of) and, while that ingest job is still finalizing in the background, navigate to `/backtest`. Confirm the page moves from the pulsing `BacktestSkeleton` cards to the full evidence panel (the by-horizon table showing all 5 horizons' rows, plus the return-attribution lists) within a reasonable load time, and never shows the red "Backend unavailable" card during this load. |
| `/data` | Live "Job progress" panel — `BackfillBreakdown`'s "Refreshed: ..." line, `data-testid="aggregates-refreshed"` (`apps/frontend/app/data/page.tsx:2775`) | Changed behavior (reliability of an existing, already-legal list value — `"forward_aggregates"` was already a possible entry before this iteration; nothing new was added to the enum) | `_refresh_ingest_aggregates` (byte-unchanged) only appends `"forward_aggregates"` to this array if at least one of the 5 horizons' warm calls succeeds before any raises `MemoryError`; the rewrite removes the memory pressure that could make the very first horizon fail immediately, so the entry should be dropped less often at this data scale. | Start a backfill/fetch job on `/data` for a date range that lands a new price bar affecting the latest scanner run's forward-return computation. While the job is live (or just after it finishes), read the Job progress panel's "Refreshed: ..." line and confirm it includes "forward aggregates" among the comma-separated items. |
| `/data` | Persisted "Last run summary" card — same `BackfillBreakdown` component, fallback view when no job has started this browser session (`apps/frontend/app/data/page.tsx:2619`) | Changed behavior (same underlying value, different render site — fresh-reload path) | Same mechanism as the row above; this is the reduced, `DataRun`-based view rendered on a fresh page load with no live job this session. | After the job from the row above completes, open `/data` in a brand-new tab (so no job has started this browser session) and confirm the persisted "Last run summary" card's "Refreshed: ..." line still includes "forward aggregates" for that completed run. |
| `/data` | Run History table — per-row breakdown cell, same `BackfillBreakdown` component (`apps/frontend/app/data/page.tsx:3527`) | Changed behavior (same underlying value, different render site — historical table) | Same mechanism; this is the multi-run history table further down the page. | Scroll to the Run History table on `/data`, locate the row for the job used above, and confirm its breakdown cell includes "forward aggregates" among its comma-separated "Refreshed:" items. |

<!-- Change Type key used above: Changed behavior -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/forward_testing.py` — the actual rewrite (`compute_forward_aggregates`'s
  two whole-partition `ForwardReturn`/`ScannerResult` reads replaced with column-projected,
  `yield_per`-streamed access bounded by `cfg.research.read_batch_size`; +84/-36 lines). Byte-identical
  output proven (TC-1/TC-2); the `ScannerRun` read (`run_rows`) is explicitly untouched. No UI surface
  change of its own — its only user-visible traces are the five rows above, which flow through
  `GET /api/backtest` and `_refresh_ingest_aggregates`, both unchanged call sites.
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` (new) — 32-test byte-identity
  suite (TC-1/TC-2). No UI impact.
- `apps/backend/tests/test_forward_testing_concurrency.py` (new) — the real `ulimit -v` induction test
  (TC-3) and the 4-caller concurrency test (TC-4). No UI impact.
- `reports/perf-budgets.md` — gained two new dated sections (a transcription of iter-13's
  already-confirmed J-06 page-load readings, and the TC-5/TC-6/TC-7 full-deep-basis measurement
  results). This is the project's performance-budget ledger, explicitly documented in `blueprint.md`
  as "not a UI page" — no in-product surface renders this file. No UI impact.
- `docs/handoffs/goal-ops-hardening-iter-14-dev.md` (new) — pipeline process document. No UI impact.
- `apps/backend/app/api/backtest.py`, `apps/backend/app/mcp/tools.py` — confirmed byte-unchanged
  (absent from `git status`); both call sites of `compute_forward_aggregates` are unaffected by the
  rewrite. Listed for completeness since they are the two paths the surface-map rows above depend on,
  but neither has a line of diff this iteration.
- `runs/goal-ops-hardening-iter-14/` (status.json, tc5-vm-samples.csv, tc5-health.csv,
  review-packet.md, sorted_times_local.txt) — pipeline run-state and raw measurement artifacts. No UI
  impact.

---

## Summary

- **Frontend surfaces changed:** 0 (no `apps/frontend/` file appears in the diff)
- **UI surfaces with behavior impact via backend change:** 3 pages/elements ((global) `HealthBadge`,
  `/backtest`, `/data`), 5 surface-map rows total
- **New pages/routes:** 0
- **Modified components:** 0 (no component source edited — every effect above is a runtime/data-driven
  consequence of already-existing rendering code)
- **Navigation changes:** no
- **Backend-only changes:** 7 (1 product source file, 2 test files, 1 reporting artifact, 1 process
  doc, 2 confirmed-unchanged call-site files, plus the run-state directory)
