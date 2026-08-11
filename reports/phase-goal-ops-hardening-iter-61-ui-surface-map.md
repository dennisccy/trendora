# Phase goal-ops-hardening-iter-61 — UI Surface Map

**Phase:** goal-ops-hardening-iter-61
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `CoveragePanel` — "Snapshot dates" / "Backfill gaps" `DefinedMetric` stat tiles | Changed behavior | Fixes the evaluator-reported staleness defect: the panel previously only refreshed on this tab's own job completion; it now also refreshes on an ambient ~30s cadence regardless of what triggered the ingest | Leave `/data` open, start (or have someone else start) a backfill job from a different browser tab or script, wait up to ~35 seconds without touching the original tab, and verify the "Snapshot dates" and "Backfill gaps" values update to the new counts without a manual page reload |
| `/data` (page-level) | New `useEffect`/`setInterval` in `DataManagerPage` (no new visible element — background polling loop) | Changed behavior | Closes the staleness gap by unconditionally re-calling `loadOverview()`, `loadAvailability()`, and the as-of run-list `refresh()` on the shared idle cadence | Open the browser DevTools Network tab on `/data`, clear the log, wait 30–35 seconds without interacting with the page, and verify a new `GET /api/data` request and a new `GET /api/data/availability` request both fire automatically (no click/reload triggered them) |
| App shell (every page) | `ReadinessProvider` / `useReadiness()` context — new additive `pollIdleIntervalSeconds` field | Internal data addition (no new visible element) | Backing plumbing that supplies `/data`'s ambient-refresh cadence from the already-polled `GET /api/health` response; purely additive, every existing reader (health badge, preflight banner, warming state, backtest page, research labs) is unaffected | Navigate to any page (e.g. `/`) and confirm the top-bar "Ready" badge still shows "Ready" and behaves exactly as before — no new banner, no new loading state, no flicker introduced |
| `/research/regime-lab` | `SampleLink` "Unavailable" indicator (`data-testid="sample-link-unavailable"`, AlertTriangle icon + "Unavailable" text) | No code change this iteration — evidence-capture only (component shipped unmodified in iter-60) | This iteration produced the first *opened and inspected* screenshot proving the already-shipped indicator renders correctly when the backend is deliberately degraded, closing an evidence gap the iter-60 evaluator flagged | Relaunch the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` set, navigate to `http://localhost:3255/research/regime-lab?asof=2010-11-05` in "As of date" mode, and verify sample-size chips render as a grey "Unavailable" label with a small triangle warning icon instead of a clickable `n=...` link; restart the backend without the flag afterward and confirm the same chips render as normal clickable `n=...` links |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_data_manager.py` — new regression test
  `test_data_overview_serves_freshest_ingested_coverage_after_unrelated_dataset_version_bump`
  pinning that `GET /api/data`'s underlying function already served fresh coverage after an
  unrelated `ScannerRun` creation — test-only; the investigation concluded the production
  backend code needed no change (the defect was on the frontend) — no UI surface affected.
- `reports/perf-budgets.md` — append-only "Addendum 28": the reconciled J-07 step-2
  health-poll measurement (raw poll log line-count reconciliation) — internal ops
  documentation, not reachable from any UI route — no UI surface affected.
- `runs/goal-ops-hardening-iter-61/evidence-drill/` — raw evidence artifacts (health-poll
  CSV, reconciliation notes, TC-4 screenshots and DOM-query JSON, a sanity screenshot) —
  internal QA/evidence storage, not a UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 (`/data`'s `DataManagerPage` ambient-refresh effect;
  `ReadinessProvider`'s additive `pollIdleIntervalSeconds` field), plus 1 evidence-only
  surface confirmed with no code change (`/research/regime-lab`'s pre-existing
  "Unavailable" indicator)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/app/data/page.tsx`,
  `apps/frontend/components/readiness-provider.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (`test_data_manager.py`, `perf-budgets.md`,
  `evidence-drill/` artifacts)
