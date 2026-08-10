# Phase goal-ops-hardening-iter-55 — UI Surface Map

**Phase:** goal-ops-hardening-iter-55
**Date:** 2026-08-10
**Written by:** ui-impact-analyst

---

## Scope note

`Frontend Present: no` in `plan.md` is correct at the file-diff level — zero `apps/frontend/` files changed
(verified: `git diff --stat -- apps/frontend/` and `git status --porcelain -- apps/frontend/` are both
empty). Every row below is therefore an *existing, unmodified* frontend surface whose underlying
**completeness-accounting correctness** (row 1) or **reliability** (rows 2-3) was targeted, or which must
be re-confirmed unaffected by the profiled scheduling change (rows 4-8). This iteration's own measurement
(`reports/perf-budgets.md` Addendum 19) found the reliability target **NOT met** (regressed: 11 non-answers
vs. the iter-54 baseline of 6) while the correctness fix is proven only by unit test, not yet observed
live — the "Why Changed" and "What to Test" columns reflect that honest, mixed status. See
`reports/phase-goal-ops-hardening-iter-55-user-visible-changes.md` for the full narrative.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | "Refreshed: …" summary line (`data-testid="aggregates-refreshed"`, `app/data/page.tsx:2594`, file unchanged) | Changed behavior — correctness fix, **unit-tested only, not yet observed live** | `_refresh_ingest_aggregates`'s `forward_aggregates_warmed` gate now requires ALL configured horizons (`[1,5,10,20,60]`) to complete before "forward aggregates" is added to this list — previously any single horizon succeeding was enough, so a `MemoryError`-aborted warm still claimed a full refresh. | Complete a full backfill/rebuild job on `http://localhost:3255/data` (fill "Start date"/"End date" with `data-testid="job-start-date"`/`"job-end-date"`, leave "Job kind" = "Backfill snapshots", click "Start") and, once `data-testid="job-status"` reaches a terminal state, read the "Refreshed: …" line and confirm it lists "forward aggregates" among the categories (happy path — matches pre-fix behavior exactly, no regression). The FAULT path (omission on a genuine mid-horizon memory error) cannot be reliably triggered on demand in the running app — it is proven by `test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings` in `apps/backend/tests/test_data_manager.py`, not by browser interaction. |
| All pages (global header) | `HealthBadge` readiness pill (`data-testid="readiness-badge"`, `components/health-badge.tsx`, file unchanged) | Changed behavior — targeted, **NOT achieved, regressed** | This iteration profiled and added intra-chunk yields to `compute_forward_aggregates`'s per-horizon call chain to close the last connection-level `/api/health` non-answers inside `forward_aggregates_warm`. The live drill instead measured 11 non-answers (up from 6 at the iter-54 baseline), 9 of 11 still inside this exact phase — root-caused to cross-request GIL contention with a concurrent heavy research compute, not this iteration's own code. | Start a backfill/rebuild job on `http://localhost:3255/data` and continuously watch the pill in the top-right of the header while the job is in flight, especially during its later stages (this iteration's evidence points to the horizon=10 sub-phase, roughly the second half of a forward-aggregate warm). Record every flip to `data-state="unavailable"`/text "Backend unavailable"; do not grade a brief flip that recovers as a hard bug, but DO grade the observed frequency against this iteration's own baseline (11 non-answers/1,839 polls, worse than iter-54's 6/1,822) — this iteration explicitly did not close the gap. |
| All pages (below header) | `PreflightBanner` (`data-testid="preflight-banner"`, `components/preflight-banner.tsx`, file unchanged) | Changed behavior — targeted, **NOT achieved, regressed** | Reads the exact same shared readiness poll as `HealthBadge` (no second fetch); same underlying condition as the row above. | During the same job-watching session as the row above, note every time this full-width banner turns red with `data-verdict="NO-GO"` and text "Backend is unavailable — the preflight check could not run." Same recording rule as the badge row above — this iteration's own drill shows the risk is not lower than before. |
| `/data` | "Start a fetch / backfill job" panel — `JobForm` ("Start date"/"End date" fields, "Job kind" select, "Start" button, `app/data/page.tsx:2290-2358`, file unchanged) | Unaffected — entry point for the two rows above | Not touched this iteration; the only entry point that can trigger `forward_aggregates_warm`, needed to verify the rows above. | Navigate to `http://localhost:3255/data`, confirm the "Start date" and "End date" fields (`data-testid="job-start-date"`/`"job-end-date"`) accept a `yyyy-MM-dd` value, "Job kind" defaults to "Backfill snapshots", and the "Start" button (with a play icon) is enabled once both dates are valid. |
| `/data` | "Job progress" card — job status badge (`data-testid="job-status"`, `app/data/page.tsx:2693`) | Unaffected — regression check (byte-identity, TC-7) | This iteration's `compute_forward_aggregates` scheduling fix must not change any computed or disclosed value, only when it yields the GIL — proven byte-identical for every horizon (1/5/10/20/60), with/without `as_of`, against a pinned pre-fix reference oracle. | Once the job from the row above reaches a terminal status, confirm `data-testid="job-status"` shows a real terminal label (e.g. "ok", not stuck on "running…" or a spinner) and that the snapshot/trading-days counts below it are real numbers, not "—"/NaN. |
| `/` (Dashboard) | Sidebar navigation + global badge/banner rendering across pages (`components/sidebar.tsx`, file unchanged) | Unaffected — regression/discoverability check | Included to confirm the readiness pill (row 2) and banner (row 3) render consistently on every page, not only `/data`. | Click through "Dashboard" (`/`), "Data Manager" (`/data`), and "Backtest" (`/backtest`) in the left sidebar; confirm the readiness pill (and, when not in a quiet "GO" state, the preflight banner) appear identically in the header/sub-header area on all three pages. |
| `/backtest` | Forward-test scorecard + evidence section (`data-testid="evidence-aggregate"`, `"evidence-summary"`, `app/backtest/page.tsx`, file unchanged) | Unaffected — regression check (J-08, required-still-passing; byte-identity) | Not touched this iteration; `compute_forward_aggregates` is the SAME canonical producer served here via `GET /api/backtest` — must return byte-identical output to before this iteration's scheduling change. | Navigate to `http://localhost:3255/backtest`, confirm the forward-test scorecard renders with real (non-placeholder) rows, and scroll to the evidence section to confirm "Snapshots contributing" shows a real numeric count, not a cold-recompute spinner or "—". |
| `/data` | "Background compute" panel (`data-testid="background-compute-panel"`, `app/data/page.tsx:3608`, file unchanged) | Unaffected — regression check (J-09, required-still-passing) | Not touched this iteration; included because J-09 is a required-still-passing journey this iteration's browser-qa lane replayed. | After viewing a historical as-of on `/backtest` (click "Previous available date" a few times), navigate to `/data` and confirm this panel shows either an active in-flight entry or an updated "Last outcome" summary, with the footer text "Since the last backend restart — this history is process-lifetime only, never persisted." still present. |

<!-- Change Type legend used above: Changed behavior (correctness fix, unit-tested only) | Changed behavior (targeted, not achieved) | Unaffected (regression check). No New page/component/form/nav rows exist this iteration — zero frontend files changed. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — `_refresh_ingest_aggregates`'s `forward_aggregates_warmed`
  gate (lines ~4230-4302) now tracks `_forward_horizons_completed` vs. `_forward_horizons_total` instead of
  an any-horizon-succeeded bool. Correctness-only; surfaces through the `/data` "Refreshed: …" row above but
  has no UI code of its own.
- `apps/backend/app/engine/forward_testing.py` — new `_FORWARD_AGG_ROW_YIELD_CHUNK = 5,000` intra-chunk
  `time.sleep(0)` yields inside `_forward_agg_slice_map` and `compute_forward_aggregates`'s per-observation
  loop. Scheduling-only, byte-identity proven; no UI surface of its own.
- `apps/backend/tests/test_data_manager.py` — inverted test
  (`test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly`) plus new
  `test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings`. Test-only, no UI
  impact.
- `apps/backend/tests/test_forward_testing_aggregates_streaming.py` — new
  `test_compute_forward_aggregates_byte_identical_with_row_yield_firing_every_row`. Test-only, no UI impact.
- `runs/goal-session-ops-hardening/journey-scripts/J-04.json` — new step 2 (`wait_for` the ready selector,
  20,000ms budget) inserted before the existing `data-state="ready"` assertion. Golden-script tooling fix,
  not a product file; no UI impact (the product behavior it verifies is unchanged).
- `reports/perf-budgets.md` — new `## Addendum 19` (append-only). An internal engineering report, not part
  of the product UI.
- `runs/goal-session-ops-hardening/state/blueprint.md` — additive changelog paragraph + row retags
  ("Job history…", "Backfill run-summary contract" rows to "BUILT, pending evaluator confirmation"). Not a
  UI surface, an internal Information-Architecture ledger.

---

## Summary

- **Frontend surfaces changed (code):** 0 — zero `apps/frontend/` files touched this iteration.
- **Frontend surfaces with a correctness fix, unit-verified but not yet observed live:** 1 — `/data`'s
  "Refreshed: …" line's omission of "forward aggregates" on a mid-horizon memory-error abort.
- **Frontend surfaces with a targeted-but-NOT-achieved reliability change:** 2 — the global readiness
  badge's and preflight banner's non-answer frequency during `forward_aggregates_warm` (measured worse:
  11/1,839 vs. the iter-54 baseline of 6/1,822).
- **Frontend surfaces confirmed unaffected (regression checks only):** 5 — `/data`'s job-status badge
  (byte-identity), the job-start form, sidebar navigation, `/backtest`'s evidence section, `/data`'s
  Background compute panel.
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 5 product/test files + 1 golden script + 1 report addendum + 1 blueprint update.
