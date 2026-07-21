# Phase goal-ops-hardening-iter-7 — UI Surface Map

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/evidence` | Evidence Ledger main data panel — per-claim `expectations` ("expected drawdown") sub-panels | Changed behavior (latency only, no display change) | The ingest finalize hook (`_refresh_ingest_aggregates`, `app.engine.data_manager`) now warms each ledger claim's `drawdown_expectations` cache slot at ingest time, calling the SAME `forward_testing.compute_drawdown_expectations_cached` function `GET /api/evidence` already calls lazily — the FIRST view after any ingest no longer pays a per-claim cold-compute (previously ~73s on the grown live dataset) | Trigger a real backfill/rebuild ingest job (e.g. a date range not previously snapshotted, via `POST /api/data/jobs` or the Data Manager job form) against a running prod-mode backend (`scripts/start-backend.sh`), wait for the job to complete, then load `/evidence` for the first time in that backend process; confirm the page's claim rows and "expected drawdown" panels populate within the committed ≤3s warm budget (Item I in `reports/perf-budgets.md`), and that the displayed numbers match a subsequent page reload exactly (no missing or placeholder values) |
| `/data` (Data Manager) | `BackfillBreakdown` component's "Refreshed:" line (`data-testid="aggregates-refreshed"`) inside `JobProgressPanel` — the LIVE job view shown while a job is running/just finished this browser session | Changed behavior (new list value, existing generic renderer) | `GET /api/data/jobs/{job_id}`'s `aggregates_refreshed` array can now include `"drawdown_expectations"` when the job's evidence ledger has ≥1 resolvable claim; the frontend's existing generic `.map(a => a.replace(/_/g," ")).join(", ")` renderer picks this up automatically with no frontend code change | Start a backfill/rebuild job on `/data` (job form: pick a date range not previously snapshotted, click "Start") against a project state whose evidence ledger has at least one resolvable claim; watch the live "Job progress" panel through completion and confirm the "Refreshed:" text line includes the phrase "drawdown expectations" among the comma-separated categories once the job finishes |
| `/data` (Data Manager) | `BackfillBreakdown` inside `LastRunSummary` — the persisted-run fallback "Job progress" card shown when no job has started this browser session | Changed behavior (new list value, existing generic renderer) | Same underlying `aggregates_refreshed` field, read from the persisted `DataRun` row instead of the live `DataJob` | After the backfill above completes, reload `/data` in a fresh browser tab/session (so no job has started this session and the page falls back to the persisted-run view); confirm the "Job progress" card's "Refreshed:" line still shows "drawdown expectations" for that run |
| `/data` (Data Manager) | `BackfillBreakdown` inside the Run History table row (last populated column, one row per past run) | Changed behavior (new list value, existing generic renderer) | Same underlying `aggregates_refreshed` field, rendered per row in the Run History table | Scroll to the Run History table on `/data`, locate the row for the backfill run above, and confirm its cell's "Refreshed:" text includes "drawdown expectations" alongside the pre-existing categories (latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys) |

<!-- Change Type is "Changed behavior" throughout — no new page, panel, form, table, modal, or nav entry was
     added or removed; the Evidence page's render contract is byte-identical, and the Data Manager rows use
     an already-shipped generic list renderer that requires no frontend code change to pick up the new value. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — `_refresh_ingest_aggregates`'s new warm step itself (ledger
  resolution, per-claim `compute_drawdown_expectations_cached` call, `prog.tick()` heartbeat, try/except
  isolation) — the computation logic is backend-internal; its only UI-visible effect is the two rows above
  (the `/evidence` latency fix and the `aggregates_refreshed` list value), both already captured.
- `apps/backend/tests/test_data_manager.py` — new/extended unit tests (TC-1, TC-3, TC-4, TC-5 and variants)
  — test-only, no UI surface affected.
- `reports/perf-budgets.md` — new dated "J-06 closeout" measurement section (live proof the mechanism
  fires, first-view timing, 11-page reconfirmation) — an engineering measurement log, not rendered by any
  UI element.
- `runs/goal-session-ops-hardening/state/blueprint.md` — checked for drift only, not edited (the decomposer
  had already added `"drawdown_expectations"` to the Data Contract's enumerated list before this iteration
  started; the shipped code matches it exactly) — no UI surface affected.
- No file under `apps/frontend/**` appears in this iteration's diff — every frontend surface listed above
  is affected purely through the pre-existing generic `aggregates_refreshed` renderer and the unchanged
  `/api/evidence` payload shape, not through any new or edited frontend code.

---

## Summary

- **Frontend surfaces changed:** 4 rows (`/evidence` main panel latency; `/data` live Job progress panel,
  persisted-run fallback card, and Run History table row — the latter three all driven by the same
  `BackfillBreakdown` component and the same underlying `aggregates_refreshed` field)
- **New pages/routes:** 0
- **Modified components:** 0 (`apps/frontend/**` untouched this iteration — all four rows are existing
  components picking up a backend-reported value or a faster backend response, with zero frontend diff)
- **Navigation changes:** no
- **Backend-only changes:** 4 (`data_manager.py`'s warm-loop logic itself, `test_data_manager.py`,
  `reports/perf-budgets.md`, `blueprint.md` drift check)
