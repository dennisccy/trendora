# Phase goal-ops-hardening-iter-50 — UI Surface Map

**Phase:** goal-ops-hardening-iter-50
**Date:** 2026-08-05
**Written by:** ui-impact-analyst

---

## Diff Classification

Zero files under `apps/frontend/` changed this iteration. All three product files touched
(`apps/backend/app/engine/research.py`, `apps/backend/app/engine/data_manager.py`,
`apps/backend/app/engine/warmup.py`) classify as **backend-api / backend-internal** by
`diff-to-ui-impact.md`'s rules — but two of the three serve response fields the frontend already renders
unchanged (so their reliability change reaches the UI indirectly), while `warmup.py`'s change is pure
internal control-flow with no served field of its own.

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/research.py` | backend-api | indirect | `_FactorLabAllObs` (a `__slots__` memory-lean stand-in) + the bounded, isolated per-`(factor,horizon)` obs-build/sort inside `compute_factor_lab_all`, plus `factor_lab_all_cached`'s new outer `MemoryError` catch, back the SAME `GET /api/research/factor-lab?all=true` response the `/research/factor-lab` all-factors table already renders. The response SHAPE gained two fields (`by_horizon[].status`, `factors_status`) that the frontend does not read — confirmed absent from `FactorHorizonDeciles`/`FactorLabAllResponse` in `apps/frontend/lib/api.ts` — so the visible effect is "the page no longer crashes the backend," not a new displayed value. |
| `apps/backend/app/engine/data_manager.py` | backend-api | indirect (mostly invisible) | New `_DRAWDOWN_WARM_LOCK`/`_try_acquire_drawdown_warm`/`_release_drawdown_warm`/`_drawdown_expectations_ledger_needs_recompute`, plus the guard + conditional `phase_context_by_date` skip wired into `_refresh_ingest_aggregates`'s `drawdown_expectations_warm` phase, back the SAME `GET /api/data` job/run fields (`status`, `aggregates_refreshed`, `message`) the `/data` Job progress panel and `/scanner-runs` already render. Ordinary runs are unaffected; a rare guard-deferral can omit `"drawdown_expectations"` from one job's `aggregates_refreshed` list (see the `/data` row below). |
| `apps/backend/app/engine/warmup.py` | backend-internal | none (control-flow only) | `_warm_drawdown_expectations` now acquires/releases the SAME shared guard before/after its own heavy per-claim loop. This function runs on the boot/re-warm path, never inside an HTTP request — it serves no field of its own and has no direct UI reader. Its ONLY UI-reachable effect is the same rare `aggregates_refreshed`-omission case described above, attributed to the `data_manager.py` row. |
| `apps/backend/tests/*.py` (3 files: `test_data_manager.py`, `test_research_streaming.py`, `test_start_backend_script.py`) | backend-internal | none | Test-only. |
| `reports/perf-budgets.md` | config/docs | none | Internal engineering record (Addendum 7), not rendered in-product. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/factor-lab` | All-factors table, per-cell NA rendering (`FactorsTable`/`DecileTable`, `apps/frontend/app/research/_labs.tsx`) | Changed behavior (reliability) | `compute_factor_lab_all`'s confirmed iter-49 crash frame (`research.py:1051`'s `sorted(obs, ...)`) is now bounded (`_FactorLabAllObs`) and isolated (a per-`(factor,horizon)` `MemoryError` degrades that ONE entry, never the whole backend). | Navigate to `http://localhost:3255/research/factor-lab`, confirm the page loads without an error card and the all-factors table renders populated rows with real rank-IC/decile figures for every catalog factor — not a crash, not a blank screen, not a "Backend unavailable" state. |
| `/research/factor-lab` | Whole-page empty state (`EmptyState`, "No forward-tested factors", `apps/frontend/app/research/_labs.tsx` ~line 676) | Latent UX gap surfaced by this iteration's own outer catch (not a new component, not this iteration's fix target) | `factor_lab_all_cached`'s new OUTER `MemoryError` catch degrades the WHOLE response to `factors_table: []` / `factors_status: "unavailable"` when pressure hits outside the per-entry loop — the frontend has no field to distinguish this from a genuinely empty store, so it reuses the pre-existing empty state whose wording claims "no stored snapshot has a factor value," which is misleading when the true cause is a transient memory-pressure degrade. | Restart the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all` set in its environment (a test-only switch, `scripts/start-backend.sh`), reload `/research/factor-lab`, and confirm it shows the "No forward-tested factors" empty state instead of crashing — then restart WITHOUT that env var and confirm the SAME page shows real populated data, proving the empty state is being reused for a degrade, not sourced from genuinely missing data. |
| `/data` | Job progress panel — "Refreshed: …" line (`data-testid="aggregates-refreshed"`) | Changed behavior (rare edge case) | The new shared warm-in-progress guard (`data_manager._try_acquire_drawdown_warm`) can make an ingest's own `drawdown_expectations_warm` phase defer entirely if it starts while the boot re-warm (`warmup._warm_drawdown_expectations`) is already mid-flight in this process. | Hard to force on demand (requires the ingest and a fresh backend restart's boot re-warm to collide within the same narrow window) — if reproduced (e.g. start an ingest job within seconds of a backend restart), confirm the "Refreshed: …" line for THAT run does not mention "drawdown expectations," and a LATER, non-colliding ingest's line does include it. |
| `/data`, `/scanner-runs` | Job status badge (`data-testid="job-status"`) + Run history table row | Changed behavior (reliability) — J-05's own defining case | The crash source that has been interrupting an in-app backfill of one unsnapshotted historical day for several rounds is closed. | Start a "Backfill snapshots" job on `/data` for target date `2012-01-04` (the current `journey-scripts/J-05.json` golden date — re-verify live it still has 0 rows on `/scanner-runs` before starting; substitute another date if it was consumed by an intervening run) and confirm the job reaches a real terminal status (`ok`, `no new snapshots`, `partial`, `failed at backfill`, or `failed` — anything but stuck on "running"), then confirm `/scanner-runs` lists a clickable `2012-01-04` row whose detail page renders a populated leaderboard. |
| `/data` (readiness badge, global via `layout.tsx`) | Readiness badge (`data-testid="readiness-badge"`) | Regression check (this iteration's core resilience claim) | The whole point of this iteration is that `GET /api/health` keeps answering 200 throughout a concurrent ingest + Factor Lab view — the exact scenario that crashed the backend for 12m45s last round. | While a data job is `running` on `/data`, open `/research/factor-lab` in a second tab and confirm the readiness badge stays `data-state="ready"` in BOTH tabs throughout, and `/research/factor-lab` itself finishes loading rather than hanging or erroring. |
| `/evidence` | Drawdown-expectations panel (`data-testid="evidence-expectations-table"` / `"evidence-expectations-unavailable"`) | Regression check | Same `data_manager.py`/`forward_testing.py` call chain (via the shared warm) feeds this panel's cached values; the numbers themselves are untouched by this iteration (only the warm's interlocking and the `phase_context_by_date` gating changed). | Navigate to `http://localhost:3255/evidence`, open a claim card with a `data-testid="evidence-claim-regime"` badge, and confirm its `evidence-expectations-table` renders populated rows with real percentage figures — not the `evidence-expectations-unavailable` fallback. |
| `/backtest` | Forward-test scorecard (`BacktestResults`, "As-of scan summary" / "Leadership cohorts" headings) | Regression check | `data_manager.py`'s ingest finalize-hook changes could in principle affect when `forward_aggregates` gets (re)warmed; the scorecard itself reads only stored, byte-identical values. | Navigate to `http://localhost:3255/backtest`, confirm the page loads without an error card, and the forward-test scorecard below the horizon selector shows real numeric hit-rate/mean-return figures for the default horizon — not an empty state or all-NA row. |
| `/data` | Background-compute panel (`data-testid="background-compute-panel"` / `"background-compute-idle"` / `"background-compute-active-row"`) | Regression check (required-still-passing J-09) | Not touched by this iteration's diff, but shares the SAME `GET /api/health` payload and the SAME process as the changes above — must not regress just because the warm guard/crash fix landed nearby. | Navigate to `http://localhost:3255/data`, scroll to the background-compute panel, and confirm it renders either `data-testid="background-compute-idle"` ("No background compute running…") or, if a window happens to be active, `data-testid="background-compute-active-row"` with a real as-of + elapsed time — never a blank panel or a JS error. |

<!-- Change Type key used above: Changed behavior (existing UI element now behaves more reliably under
     concurrent background load because a previously-crashing code path is bounded/isolated, or a rare
     interlock-driven omission is now possible); Latent UX gap (an existing component is reused for a new
     cause, producing a misleading message — a finding, not this iteration's own regression); Regression
     check (unaffected or indirectly-touched code, verified to confirm nothing else broke). No New page |
     New component | New form | New table | New modal | Added navigation rows apply — this iteration
     added none of those. -->

---

## Backend-Only Changes (No UI Impact)

- `research.py`'s `_FactorLabAllObs` (`__slots__` memory-lean observation stand-in) — pure internal memory
  optimization; proven byte-identical output (TC-3); no UI surface.
- `data_manager.py`'s `_DRAWDOWN_WARM_LOCK` / `_DRAWDOWN_WARM_IN_PROGRESS` / `_try_acquire_drawdown_warm` /
  `_release_drawdown_warm` — internal control-flow guard; its ONLY UI-reachable effect is the rare
  `aggregates_refreshed`-omission case already captured in the `/data` row above; the guard's own deferral
  log line itself is server-log-only.
- `data_manager.py`'s `_drawdown_expectations_ledger_needs_recompute` helper — an internal read-only
  cache-HIT check that gates whether `phase_context_by_date` runs; the resulting speed difference
  (~23.6–23.9s saved on a genuine no-op ingest) is invisible in the UI, same as iter-49's own speed-only
  fixes to this same subsystem.
- `data_manager.py`'s `"factor_lab_all"` addition to `_FAULT_INJECT_SITES`, and both new `MemoryError`
  catches' `logger.exception`/`logger.warning` lines in `research.py` — test/ops-only, never rendered.
- New/extended backend tests (`test_data_manager.py`, `test_research_streaming.py`,
  `test_start_backend_script.py`) — test-only, no UI surface.
- `reports/perf-budgets.md` Addendum 7 — internal engineering record, not shown in-product.

---

## Summary

- **Frontend surfaces changed:** 0 frontend files modified this iteration.
- **Existing UI surfaces with changed BEHAVIOR (no frontend code change):** 4 (`/research/factor-lab`'s
  all-factors table reliability + its reused empty-state UX gap, `/data`'s "Refreshed: …" line rare edge
  case, `/data` + `/scanner-runs`'s J-05 backfill reliability) plus 3 regression-only confirmations
  (`/evidence`, `/backtest`, `/data`'s background-compute panel and readiness badge).
- **New pages/routes:** 0
- **Modified components:** 0 (behavior differs only because the backend now resolves the same
  already-rendered fields more reliably, and — in one rare edge case — reports one field's refresh
  honestly as deferred rather than attempting it under memory contention)
- **Navigation changes:** no
- **Backend-only changes:** 5 (the `__slots__` memory bound, the warm-in-progress guard internals, the
  needs-recompute helper, the fault-injection site addition + logging, the 3 test-file groups, the
  perf-budgets addendum)
