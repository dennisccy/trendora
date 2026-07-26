# Phase goal-ops-hardening-iter-24 — UI Surface Map

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| All pages (root layout, `app/layout.tsx`) | `HealthBadge` → new inline `Badge` `data-testid="background-compute-indicator"` | Updated layout (conditional child element) | Discloses live in-flight background historical-evidence compute count next to the existing readiness pill | Trigger a real background-compute window (load `/backtest` for a historical as-of not yet ready for the current dataset version, or use the test-only force-dispatch hook if timing can't be controlled), then on any page confirm a badge reading "background compute running (1)" appears next to the readiness pill within one poll interval, and confirm it disappears (element no longer in DOM) within one poll interval after the dispatch completes |
| `/data` | `BackgroundComputePanel` (`data-testid="background-compute-panel"`) | New component/panel | New disclosure surface for background-compute detail (as-of, elapsed, horizon progress, last outcome) | With no background compute ever triggered since backend boot, load `/data` and confirm the panel shows the exact idle text "No background compute running. Last outcome: none yet." (`data-testid="background-compute-idle"`) |
| `/data` | `BackgroundComputeRow` (`data-testid="background-compute-active-row"`, child elements `background-compute-asof`, `background-compute-elapsed`, `background-compute-horizons`) | New component (list item) | Renders one row per active in-flight window with live progress | During a real background-compute window, load `/data` and confirm one `background-compute-active-row` appears showing "as-of <date>", an elapsed time > 0 that increases on re-poll, and "horizons X/Y" where X increases over successive polls (never decreases, never exceeds Y) |
| `/data` | `LastOutcomeSummary` (`data-testid="background-compute-last-outcome"`) | New component | Shows the most recently completed/failed outcome (duration, failure reason) | After a background-compute window completes successfully, reload `/data` and confirm the "Last outcome" section shows an "ok"-styled "Completed" badge, the as-of date, and a non-zero duration; separately, force a failed dispatch (test-injected fault) and confirm the badge instead reads "Failed" (danger-styled) with a visible non-empty reason string |
| `/data` | `BackgroundComputePanel` — process-lifetime disclosure line | New static copy | Prevents users from mistaking a post-restart empty history for "nothing ever ran" | Restart the backend, then load `/data` and confirm the panel shows the empty idle state alongside the fixed sentence "Since the last backend restart — this history is process-lifetime only, never persisted." (always visible, in every state) |

<!-- No existing route, page, or navigation element was removed, relabeled, or restructured — every row above is additive. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/forward_testing.py` — `_HIST_DISPATCH_INFLIGHT` changed from a `set` to a `dict` (adds `started_at`/`horizons_done`/`horizons_total` bookkeeping), new bounded `_HIST_RECENT_OUTCOMES` ring, new `get_background_compute_status()` accessor — internal data structure and computation; fully surfaced via the `GET /api/health` field consumed by the two rows above, so it has no *separate* UI surface of its own.
- `apps/backend/app/config.py` — new `StartupCfg.background_compute_history_size` field (validated `>= 1`, default `5`) — an internal config value read at backend startup, not an in-app setting; no UI control exists or is expected for it.
- `config.yaml` — `startup.background_compute_history_size: 5` — deployment configuration, not a UI surface.
- `apps/backend/app/engine/readiness.py` — `compute_readiness` composes `background_compute` into its return dict — internal composition logic; its output reaches the UI only through the `GET /api/health` field already covered above.
- `apps/backend/app/api/health.py` — serves `background_compute` as a new top-level field on `GET /api/health` (backend-api change) — this is the data contract the two frontend rows above consume; the endpoint itself has no UI of its own beyond that consumption.
- `apps/backend/tests/test_forward_testing_concurrency.py`, `test_readiness.py`, `test_health.py`, `test_config.py` — test-only changes, no UI impact.
- `reports/perf-budgets.md` — documentation/report update (re-measured `GET /api/health` steady-state latency) — no UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 (global `HealthBadge`, `/data` page)
- **New pages/routes:** 0
- **Modified components:** 2 (`health-badge.tsx` gains a conditional child; `app/data/page.tsx` gains the new `BackgroundComputePanel`/`BackgroundComputeRow`/`LastOutcomeSummary` components) — plus 2 plumbing-only files with no independent visual surface (`lib/api.ts` types, `readiness-provider.tsx` context field)
- **Navigation changes:** no
- **Backend-only changes:** 6 (forward_testing.py, config.py, config.yaml, readiness.py, health.py, test files) — all fully surfaced through the `GET /api/health` → `HealthBadge`/`BackgroundComputePanel` path listed above; none are stranded without UI access.
