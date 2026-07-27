# Phase goal-ops-hardening-iter-27 — UI Surface Map

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `CoveragePanel` (`apps/frontend/app/data/page.tsx`) + `DataCoverage` type (`apps/frontend/lib/api.ts`) | Changed behavior (new state added) | Fixes AG-3: the panel used to silently render the same all-zero "not yet computed" display for two different backend conditions (a real prior snapshot under an older internal `dataset_version` vs. a genuinely never-scanned database). It now discloses the "stale" case honestly with real figures. | Get the backend into the "stale" coverage state (per the dev handoff: fire a `/backtest` request for a never-scanned historical date, e.g. `2011-03-10`, which bumps the internal dataset version without a fresh ingest), then load `/data` and confirm: (1) the price-history and universe-count figures show real, non-zero values (not "— → —" / "Universe: 0"), and (2) the notice "Coverage as of a prior scan (version {stale_dataset_version}) — refreshes on the next data job" appears directly below the panel title, in the panel's normal muted text tone (not a warning/red color). |
| `/data` | `CoveragePanel` — `current` state (regression guard) | Changed behavior (unchanged path verified) | Must confirm the common, everyday path — coverage freshly computed after a normal ingest — still renders with NO stale label, since the new fallback logic is only supposed to trigger when the exact-match lookup misses. | Run a normal data ingest/finalize (or use a database where the last scan matches the current dataset version), load `/data`, and confirm the coverage panel shows its normal figures with the "Coverage as of a prior scan..." notice absent entirely. |
| `/data` | `CoveragePanel` — `not_yet_computed` state (regression guard) | No change (verify byte-identical) | Confirm the genuinely-never-scanned (fresh install) case still shows the original all-zero empty state, unaffected by the new stale-fallback branch. | Load `/data` against a database with zero `CoverageSnapshot` rows for any dataset version, and confirm the panel still shows "— → —" / "Universe: 0" with no stale notice and no other visual change from before this iteration. |
| `/backtest` | Backtest evidence page (Scorecard / As-Of Scan Summary — no component renamed or added) | Changed behavior (reliability fix, no new visible element) | Fixes AG-8: a mid-loop SQLAlchemy autoflush collision when two concurrent requests race the same never-scanned historical date's forward-returns write could raise an unhandled `IntegrityError`, surfacing as an HTTP 500 to one of the two requests instead of the normal evidence page. | Fire two concurrent requests (e.g., two `GET /api/backtest?as_of=<date>` calls, or two browser tabs navigating simultaneously) for the SAME never-scanned historical date. Confirm BOTH return HTTP 200 and BOTH render the normal Backtest evidence content (Scorecard / As-Of Scan Summary) in a full-page capture — never a blank or frozen frame — and confirm `logs/backend.log` shows zero "Exception in ASGI application" lines for that request window. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_forward_testing_concurrency.py` — new tests proving the mid-loop autoflush
  collision is tolerated (TC-3) and an unrelated `IntegrityError` still propagates (TC-4) — test-only, no UI
  surface affected.
- `apps/backend/tests/test_data_manager.py` — new stale-fallback test (TC-5) plus regression-guard
  assertion updates on 3 existing tests to account for the new additive `coverage_status` fields — test-only,
  no UI surface affected.
- `apps/backend/tests/test_api_data.py` — one existing test's equality assertion updated for the new
  additive fields (TC-8 regression guard) — test-only, no UI surface affected.
- `reports/perf-budgets.md` — corrected a mislabeled one-hour-off boot timestamp in the Iteration 26
  section (TC-10) — an internal ops/evidence report, not part of the shipped product; no UI surface
  affected.

<!-- Note: apps/backend/app/engine/forward_testing.py and apps/backend/app/engine/data_manager.py are the
     engine-layer implementations behind the /backtest and /data rows above, respectively — they are listed
     there (not here) because they have direct, traced UI consequences this iteration. -->

---

## Summary

- **Frontend surfaces changed:** 2 (`/data` coverage panel, `/backtest` evidence page reliability)
- **New pages/routes:** 0
- **Modified components:** 1 (`CoveragePanel`, plus its supporting `DataCoverage` type in `lib/api.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 4
