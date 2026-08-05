# Phase goal-ops-hardening-iter-49 — UI Surface Map

**Phase:** goal-ops-hardening-iter-49
**Date:** 2026-08-05
**Written by:** ui-impact-analyst

---

## Diff Classification

Zero files under `apps/frontend/` changed this iteration. All three product files touched
(`apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/forward_testing.py`,
`apps/backend/app/engine/research.py`) classify as **backend-api / backend-internal** by
`diff-to-ui-impact.md`'s rules — but all three serve response fields or feed cache tables the frontend
already renders unchanged, so their behavior change reaches the UI indirectly ("indirect — frontend
consumes this API, surface affected").

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/engine/data_manager.py` | backend-api | indirect | Per-horizon/per-claim sub-phase timing (log-only, no UI) plus the `phases`-precompute change inside the `drawdown_expectations_warm` loop back the SAME `GET /api/data` job/run fields (`status`, `aggregates_refreshed`, `message`) the `/data` Job progress panel and `/scanner-runs` already render — the fields didn't change shape, but a historical-gap backfill's ENTIRE finalize tail (not just one step) now resolves them to a terminal value reliably within budget. |
| `apps/backend/app/engine/forward_testing.py` | backend-api | indirect (invisible) | `_ExactMeanAcc.add_ratio`/`_accumulate_group_ratio` (ratio-based accumulator siblings), the single-flight lock's new fall-through log line, and the additive `phases` parameter on `compute_drawdown_expectations`/`compute_drawdown_expectations_cached` back the SAME `GET /api/backtest` and `GET /api/evidence` reads — member values are proven byte-identical (TC-3), so the only user-observable effect is a faster/more-reliable ingest warm step, not a display difference. |
| `apps/backend/app/engine/research.py` | backend-api | indirect (invisible) | New `_extract_factor_value_from_row` + `_factor_value_column` column-project `_factor_decile_observations`'s two `ScannerResult` reads instead of loading full ORM rows — feeds the SAME `/evidence`/`/research/factor-lab` drawdown-expectations panels via `samples.py`; byte-identical output (TC-3), so no visible number change, only lower server cost. |
| `apps/backend/tests/*.py` (4 files: `test_data_manager.py`, `test_research_streaming.py`, `test_start_backend_script.py`, plus the pre-existing `test_forward_testing_aggregates_streaming.py`/`test_ingest_finalize_fault_injection.py` re-run for proof) | backend-internal | none | Test-only. |
| `reports/perf-budgets.md` | config/docs | none | Internal engineering record, not rendered in-product. |
| `runs/goal-session-ops-hardening/state/blueprint.md` | docs | none | Session architecture/decision log, not rendered in-product. |
| `reports/qa/goal-ops-hardening-iter-49-evidence/*.csv` | docs/evidence | none | Raw VmPeak/health-poll sample data backing the perf-budgets report — not shown in-product. |
| `runs/goal-ops-hardening-iter-49/status.json` | config/pipeline-state | none | Pipeline bookkeeping, not rendered in-product. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Job progress panel — status badge (`JobProgressPanel`, `data-testid="job-status"`) | Changed behavior | A historical-gap backfill's TWO remaining finalize-tail phases (`forward_aggregates_warm`, `drawdown_expectations_warm`) no longer scale unbounded with DB/data volume; the whole job now reaches a terminal status within ~17-17.5 minutes (proven 3/3 live), not just the one step iter-48 already fixed. | Start a Backfill snapshots job for start date `2012-01-05` / end date `2012-01-05` on `/data`, then watch the element with `data-testid="job-status"` — confirm it stops showing the spinner (`animate-spin` `Loader2` icon) and settles to `ok` (or `no new snapshots` if that date was already snapshotted by a prior run) within about 20 minutes, comfortably before the 1,200s budget expires. |
| `/data` | "Refreshed: …" line (`BackfillBreakdown`, `data-testid="aggregates-refreshed"`) | Regression check (iter-48's own fix, confirming it still holds under this iteration's diff) | Populates promptly once the membership-timeline refresh step (iter-48's fix area, untouched this iteration) finishes. | After starting the same backfill, confirm the element with `data-testid="aggregates-refreshed"` renders text starting with `Refreshed:` and mentioning `membership timeline` within about 30 seconds — before the two phases this iteration bounds even begin. |
| `/data` | Readiness badge (`HealthBadge`, `data-testid="readiness-badge"`) | Regression check / newly-relevant risk (verifies TC-4) | The backend must stay responsive (`GET /api/health` returns 200) throughout the whole finalize tail. A newly-disclosed, NOT-fixed gap: 2 of 3 automated live runs logged one ~10s health timeout early in the run (before this iteration's own two phases start). | While the backfill from the row above is still `running`, repeatedly check the readiness badge in the page header over the FULL run duration — confirm it shows `data-state="ready"` ("Ready", green) almost the entire time; a very brief (~10s) flip to `data-state="unavailable"` roughly 40-45 seconds after the job accepts is a known, disclosed, out-of-scope gap (not a new regression) as long as it self-recovers — a badge that STAYS on "unavailable" past that brief window, or flips at any OTHER point in the run, is a genuine new problem. |
| `/scanner-runs` | Run history table row (`RunTableRow`, "As of" column link) | Changed behavior | A historical-gap date's run now reliably becomes a real, clickable row because the ENTIRE backfill job (not just its first step) actually reaches a terminal status within budget. | After the `/data` job above settles, navigate to `/scanner-runs` and confirm a row with "As of" text `2012-01-05` appears in the table, with a clickable date link. |
| `/scanner-runs/[runId]` | Run detail heading + leaderboard table | Changed behavior | Opens the stored snapshot for the historical date reliably within the promised window instead of the job possibly still finishing 20+ minutes late. | Click the `2012-01-05` link from the row above — confirm the page shows text containing "as of 2012-01-05" and the leaderboard table below it renders at least one stock row (not a loading skeleton or 404/"not found" state). |
| `/backtest` | Forward-aggregate results table | Changed behavior (invisible — server-side speed only) | `forward_aggregates_ingest_cached`'s hot loop now computes each observation's ratio once and reuses it across all 7 accumulators instead of recomputing it 7 times; output proven byte-identical (TC-3) for every configured horizon (1, 5, 10, 20, 60). | Navigate to `/backtest`, select any horizon that already has cached data (e.g. 20-day), and confirm the aggregate stats table renders real numeric values (hit rate, mean return, etc.) — not an error card or empty state. |
| `/evidence` | Drawdown-expectations panel (`data-testid="evidence-expectations-panel"` / `"evidence-expectations-table"`) | Changed behavior (invisible — server-side speed only) | `compute_drawdown_expectations_cached`'s per-claim loop now reads `research.py`'s column-projected `_factor_decile_observations` (instead of full-entity ORM rows) and memoizes `phase_context_by_date` once per invocation (instead of once per claim); member rows proven byte-identical (TC-3). | Navigate to `/evidence`, open a claim card with a `data-testid="evidence-claim-regime"` badge, and confirm its `evidence-expectations-table` renders populated `evidence-expectations-phase-row` rows with real percentage figures — not the `data-testid="evidence-expectations-unavailable"` fallback state. |
| `/research/factor-lab` | Drawdown-expectations panel (same components as `/evidence`, via `_labs.tsx`) | Changed behavior (invisible — server-side speed only) | Same `research.py`/`forward_testing.py` code path as the `/evidence` row above. | Navigate to `/research/factor-lab`, confirm the page loads without an error card and at least one factor's drawdown-expectations table renders populated rows. |

<!-- Change Type key used above: Changed behavior (existing UI element now behaves differently because an
     unchanged-shape backend response resolves faster / more reliably); Regression check (unaffected or
     already-fixed-elsewhere code, verified to confirm nothing else broke). No New page | New component |
     New form | New table | New modal | Added navigation rows apply — this iteration added none of those. -->

---

## Backend-Only Changes (No UI Impact)

- `data_manager.py`'s new per-horizon/per-claim wall-clock instrumentation/logging (`logger.info("J-05
  finalize-tail sub-phase timing: ...")`) — server logs only, never surfaced in any page or component (the
  `/data` page's "Stage timings" block only ever shows fetch/backfill stages, not the finalize tail).
- `forward_testing.py`'s single-flight lock fall-through log line — a diagnostic log line for future
  contention investigation, never rendered.
- `forward_testing.py`'s `_ExactMeanAcc.add_ratio`/`_GroupAcc.add_ratio`/`_accumulate_group_ratio` — pure
  internal computation-path change with proven byte-identical output; reaches the UI only indirectly
  through the `/backtest` row above, and is invisible there.
- `research.py`'s `_extract_factor_value_from_row`/`_factor_value_column` — internal resolver functions;
  effect only reaches the UI indirectly through the `/evidence`/`/research/factor-lab` rows above, and is
  invisible there (byte-identical output).
- New/extended backend tests (`test_data_manager.py`, `test_research_streaming.py`,
  `test_start_backend_script.py`, plus re-runs of `test_forward_testing_aggregates_streaming.py` /
  `test_ingest_finalize_fault_injection.py`) — test-only, no UI surface.
- `reports/perf-budgets.md` Item R Addendum 4 — internal engineering record, not shown in-product.
- `runs/goal-session-ops-hardening/state/blueprint.md`'s iter-49 changelog paragraph and Data Contract row
  note — architecture/decision log, not rendered in-product.
- `reports/qa/goal-ops-hardening-iter-49-evidence/*.csv` — raw diagnostic sample data, not shown in-product.
- `runs/goal-ops-hardening-iter-49/status.json` — pipeline bookkeeping.

---

## Summary

- **Frontend surfaces changed:** 0 frontend files modified this iteration.
- **Existing UI surfaces with changed BEHAVIOR (no code change on the frontend side):** 5 observable
  (`/data` Job progress panel status badge, `/data` readiness badge, `/scanner-runs` run history table,
  `/scanner-runs/[runId]` run detail page) plus 3 invisible/perf-only confirmations (`/backtest`,
  `/evidence`, `/research/factor-lab` drawdown/aggregate panels — same numbers, faster server-side
  computation).
- **New pages/routes:** 0
- **Modified components:** 0 (behavior differs only because the backend now resolves the same
  already-rendered fields differently, and more reliably within budget)
- **Navigation changes:** no
- **Backend-only changes:** 8 (per-horizon/per-claim logging, lock fall-through logging, the ratio-based
  accumulator internals, the column-projected read internals, 3 test-file groups, the perf-budgets report,
  the blueprint changelog note, the evidence CSVs, the pipeline status file)
