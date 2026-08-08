# Phase goal-ops-hardening-iter-52 — UI Surface Map

**Phase:** goal-ops-hardening-iter-52
**Date:** 2026-08-07
**Written by:** ui-impact-analyst

---

## Scope note

`Frontend Present: no` in `plan.md` is correct at the file-diff level — zero `apps/frontend/` files changed
(verified directly: `git diff --stat -- apps/frontend/` is empty). Every row below is therefore an
*existing, unmodified* frontend surface whose underlying **reliability** was targeted by a backend-only
scheduling change — not a surface whose code changed. Unlike iter-51 (whose equivalent fix worked, confirmed
live), this iteration's own live measurement (`reports/perf-budgets.md` Item U / Addendum 12) found the
targeted improvement was **not achieved** — the "Why Changed" and "What to Test" columns reflect that honest
status rather than assuming success. See
`reports/phase-goal-ops-hardening-iter-52-user-visible-changes.md` for the full narrative.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| All pages (global header) | `HealthBadge` readiness pill (`data-testid="readiness-badge"`, `components/health-badge.tsx`, file unchanged) | Changed behavior — targeted, **not achieved** | This iteration added scheduling yield points to the backend's heaviest per-item loops so the badge's underlying `GET /api/health` poll would stop occasionally getting no response at all during a heavy job's longest phase. The badge's own rendering/trigger logic is unchanged; only the backend's failure frequency was targeted. | Start a fetch/backfill job on `http://localhost:3255/data` (see the `/data` row below for exact steps) and continuously watch the pill in the top-right of the header. Note every time it flips from green "Ready" (`data-state="ready"`) to red "Backend unavailable" (`data-state="unavailable"`) and roughly how long each flip lasts. **Do not expect zero occurrences** — the developer's own solo drill measured 22 occurrences in one run (worse than the 9 measured before this fix); this test's purpose is to record what actually happens on your run, not to assert a pass/fail against zero. |
| All pages (below header) | `PreflightBanner` (`data-testid="preflight-banner"`, `components/preflight-banner.tsx`, file unchanged) | Changed behavior — targeted, **not achieved** | Reads the exact same shared readiness poll as `HealthBadge` (no second fetch). On any single failed poll, `preflight` becomes `null` and this banner renders a loud, full-width "NO-GO — do not rely on today's board / Backend is unavailable — the preflight check could not run." This is the same underlying condition as the row above, surfaced through a second, more attention-grabbing element. | During the same job-watching session as the row above, note every time this full-width banner turns red with `data-verdict="NO-GO"` and the exact reason text "Backend is unavailable — the preflight check could not run." Record occurrences; do not expect zero. |
| `/data` | "Job progress" card / job status badge (`data-testid="job-status"`, `app/data/page.tsx`, file unchanged) | Changed behavior (timing) — targeted improvement not confirmed; new overage disclosed | The new yield points add a small measured overhead to one phase (+20.4% on `factor_lab_all_warm`); more significantly, this iteration's own live drill measured the finalize-tail total at 1,670.95s+ (partial — one background step still hadn't finished when the drill's own 30-minute ceiling closed), 470.95s (39.2%) over the product's existing ~1,200s (20-minute) budget on that run's date. | Start a backfill job on `http://localhost:3255/data` (fill "Start date" / "End date" with a range the page's own coverage display shows as not yet backfilled, leave "Job kind" = "Backfill snapshots", click "Start") and time how long the status badge (`data-testid="job-status"`) stays in a running state before reaching a terminal status (e.g. "ok"). Record the elapsed time; a run resembling this iteration's own measured date may exceed 20 minutes and possibly not finish within 30. |
| `/data` | "Refreshed: …" summary line (`data-testid="aggregates-refreshed"`, `app/data/page.tsx`, file unchanged) | Unaffected — regression check (TC-4) | This iteration is scheduling-only; every warmed category's presence/absence and every underlying value is required to be byte-identical to a pre-fix reference (proven by the existing pinned-oracle unit-test suite, 388 passed / 0 failed). Included to confirm nothing about this line's *content* moved, only job *timing* (see row above). | Once a job from the row above reaches a terminal status, read the "Refreshed:" line for that job on the "Job progress" card (or the matching row in the "Run History" table below it) and confirm it lists the same set of categories (e.g. "coverage", "research hot keys", "factor lab all" if that phase completed) that the same kind of job listed before this iteration — no category should appear or disappear because of this iteration's change alone. |
| `/research/factor-lab` | `FactorsTable` (`app/research/_labs.tsx`, file unchanged) | Unaffected — regression check (TC-4) | `compute_factor_lab_all`'s per-(factor,horizon) loop gained yield points but no value/ordering change; this row confirms the page still renders correctly and its numbers are unaffected. | Navigate to `http://localhost:3255/research/factor-lab` after a completed job and confirm the sortable factor table renders with real rows (not all "NA") and that clicking a column header still re-sorts client-side with no error — behavior must be identical to before this iteration. |
| `/research/factor-combination` | Combination results table (`app/research/_labs.tsx`, file unchanged) | Unaffected — regression check | Not touched this iteration; included because it shares the `research.py` module that received yield points in unrelated functions (`_combination_observations`, `_factor_decile_observations`). | Navigate to `http://localhost:3255/research/factor-combination`, click "Add condition" twice to configure two factor conditions, and confirm the returned single/strict/composite member counts match what the same inputs produced before this iteration (or `test_research_streaming.py`'s pinned-oracle fixture if no prior live baseline is available). |
| `/`, `/data`, `/research` | Sidebar navigation (`components/sidebar.tsx`, file unchanged) | Unaffected — discoverability/regression check | Entry points are unchanged; included to confirm the global badge/banner (rows 1–2) render consistently across distinct pages, not only on `/data`. | Click through "Dashboard" (`/`), "Data Manager" (`/data`), and "Research" (`/research`) in the left sidebar; confirm the readiness pill and (when in a non-GO state) the preflight banner appear identically in the header/sub-header area on all three pages. |

<!-- Change Type legend used above: Changed behavior (targeted, not achieved) | Unaffected (regression check). No New page/component/form/nav rows exist this iteration — zero frontend files changed. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — `time.sleep(0)` yield points added at 3 per-item loop sites
  (coverage per-date, market-phase per-date, forward-aggregates per-horizon) alongside existing
  `prog.tick()` heartbeat calls. Scheduling only, no UI surface of its own.
- `apps/backend/app/engine/research.py` — yield points added at 5 per-item/per-chunk sites across
  `compute_factor_lab_all`, `_combination_observations`, `_factor_decile_observations` (both passes),
  `_all_factor_observations_by_horizon`. Scheduling only, no UI surface of its own.
- `apps/backend/app/engine/forward_testing.py` — yield point added inside `compute_forward_aggregates`'s
  per-run-id-chunk loop; new `import time`. Scheduling only, no UI surface of its own.
- `apps/backend/tests/test_data_manager.py`, `test_research_streaming.py`, `test_forward_testing_
  aggregates_streaming.py` — new unit tests proving the yield points fire at the designed granularity.
  Test-only, no UI impact.
- `apps/backend/tests/test_start_backend_script.py` — new `spawned_backend_throwaway_db_fault_injected`
  fixture + `test_ingest_finalize_factor_lab_all_fault_is_honestly_omitted_health_stays_live` (TC-6,
  opt-in, heavy). A developer/QA verification tool, not a user-facing capability.
- `reports/perf-budgets.md` — new `## Item U` / `### Addendum 12` (append-only). An internal engineering
  report, not part of the product UI.

---

## Summary

- **Frontend surfaces changed (code):** 0 — zero `apps/frontend/` files touched this iteration.
- **Frontend surfaces with targeted-but-unconfirmed/negative behavior change:** 3 — the global readiness
  badge's and preflight banner's "unavailable" flip frequency (measured worse: 22 vs. 9), and `/data`'s job
  duration (measured over its existing budget on this run's date).
- **Frontend surfaces confirmed unaffected (regression checks only):** 4 — `/data`'s "Refreshed:" line
  content, `/research/factor-lab`, `/research/factor-combination`, sidebar navigation.
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 6 (3 product-code files + 3 test files/fixtures) + 1 report addendum.
