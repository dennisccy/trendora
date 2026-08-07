# Phase goal-ops-hardening-iter-51 — UI Surface Map

**Phase:** goal-ops-hardening-iter-51
**Date:** 2026-08-07
**Written by:** ui-impact-analyst

---

## Scope note

`Frontend Present: no` in `plan.md` is correct at the file-diff level (zero `apps/frontend/` files
changed — verified via `git diff --stat`/`git status --short`). Every row below is therefore an
*existing, unmodified* frontend surface whose **behavior or content** changed because of a backend-only
code change, not a surface whose code changed. This is called out explicitly in each row's "Why Changed"
column. See `reports/phase-goal-ops-hardening-iter-51-user-visible-changes.md` for the full reasoning.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/factor-lab` | `FactorsTable` / `SlowComputeNotice` (`app/research/_labs.tsx`, file unchanged) | Changed behavior | New `factor_lab_all_warm` finalize-tail phase (`data_manager.py`) makes this page's data a cache HIT immediately after any ingest, instead of occasionally triggering a live multi-minute compute on the request path | Immediately after a `/data` job reaches status "ok" with a fresh dataset-version stamp, open `http://localhost:3255/research/factor-lab` and confirm the amber "Still computing — Xs elapsed" card (`data-testid="slow-compute-notice"`) does NOT appear and the sortable factor table (11 rows on this build) renders within ~3 seconds. Cross-check with `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" "http://localhost:8255/api/research/factor-lab?all=true"` — expect `200` and well under 1s (confirmed live on this build: 0.008–0.043s). |
| `/data` | "Refreshed: …" line (`data-testid="aggregates-refreshed"`, inside `BackfillBreakdown` in `app/data/page.tsx`, file unchanged) | Changed behavior (new value in an existing list) | `aggregates_refreshed`'s legal member set gained `"factor_lab_all"` (`data_manager.py`); the line already renders whatever this list contains | On `http://localhost:3255/data`, in the "Job progress" card (or its persisted-run fallback if no job started this session), read the paragraph with `data-testid="aggregates-refreshed"` and confirm the comma-separated list includes "factor lab all" for any run that warmed it. Confirmed live on this build: the most recent run (2011-03-16 backfill) lists `factor_lab_all`; the run immediately before this iteration's code shipped does not. |
| `/data` | "Job progress" card / live job duration (`app/data/page.tsx`, file unchanged) | Changed behavior (timing) | The new warm phase (~584s measured) now runs unconditionally inside every job's finalize tail, extending total job wall-clock (dev-measured ~12min → ~18min for the same job type) | Start a job on `/data` and watch its status badge (`data-testid="job-status"`) from submission to leaving "running" — confirm it takes noticeably longer than a pre-iter-51 run of the same kind/date-range (dev's own reference point: ~18 minutes vs. ~12 minutes before), while the live "updated Ns ago" heartbeat keeps ticking (so it reads as busy, not stalled). |
| `/research/factor-combination` | Combination results table (`app/research/_labs.tsx`, file unchanged) | Unaffected — regression check | `_combination_cohort_members`'s internal allocation strategy changed (`research.py:1530`); dev-proven byte-identical `single`/`strict`/`composite` outputs against a pinned reference — listed to confirm nothing visibly moved, not because a difference is expected | Open `http://localhost:3255/research/factor-combination`, click "Add condition" twice to configure two factor conditions, and confirm the returned single/strict/composite member counts and the samples drill-down match what the same inputs produced before this iteration (or the pinned-oracle fixture in `test_research_streaming.py` if no prior live baseline is available). |
| `/research` (hub) | "Factor Lab" tile (`data-testid="research-lab-link-factor-lab"`, `app/research/page.tsx`, file unchanged) | Unaffected — discoverability/regression check | Entry point is unchanged; included because this iteration's whole fix lives directly behind it | Open `http://localhost:3255/research`, confirm the "Factor Lab" tile is present and unchanged in wording/position, click it, and confirm it navigates to `/research/factor-lab` and loads (see row 1). |

<!-- Change Type legend used above: Changed behavior | Unaffected (regression check). No New page/component/form/nav rows exist this iteration — zero frontend files changed. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — new `factor_lab_all_warm` phase inside
  `_refresh_ingest_aggregates`'s finalize tail. This is the *mechanism* behind the first three surface
  rows above; it has no UI surface of its own (no endpoint shape change, no new field beyond the
  already-mapped `aggregates_refreshed` value).
- `apps/backend/app/engine/research.py` — `_combination_cohort_members`'s `strict_members` construction
  bounded to stop unconditionally allocating `set(range(pool_n))`. Pure internal allocation-strategy
  change; proven output-identical. Feeds the `/research/factor-combination` regression row above but has
  no UI surface of its own.
- `apps/backend/tests/test_data_manager.py`, `apps/backend/tests/test_research_streaming.py` — new/updated
  unit tests. Test-only, no UI impact.
- `reports/perf-budgets.md` — new dated addendum (Item T / Addendum 11) recording the new phase's measured
  cost and the reconciled finalize-tail total. An internal engineering report, not part of the product UI.

---

## Summary

- **Frontend surfaces changed (code):** 0 — zero `apps/frontend/` files touched this iteration.
- **Frontend surfaces with changed behavior/content (no code change):** 3 — `/research/factor-lab`'s load
  timing, `/data`'s "Refreshed: …" line content, `/data`'s job-duration timing.
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 2 product-code changes (the new warm phase, the cohort-members bound) + their
  tests + 1 report addendum.
