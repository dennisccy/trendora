# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Agent:** developer
**Status:** complete

## What Was Built

### J-86 — max-drawdown stored once, surfaced everywhere
- New nullable `max_drawdown` column on the append-only `forward_returns` table
  (`models.ForwardReturn`), registered in `db._ADDITIVE_COLUMNS` (`ALTER TABLE forward_returns ADD
  COLUMN max_drawdown FLOAT`) so an existing live DB gains it in place.
- New pure `forward_testing.max_drawdown(bars_after_list, entry_close, horizon)` helper — the true
  peak-to-trough decline `min_j( low_j / max(entry_close, high_1..high_j) − 1 )` over the FIRST
  `horizon` post-snapshot bars (running peak seeded at the as-of-D close). Always ≤ 0; shares the EXACT
  no-lookahead NA gate as `forward_return`/`forward_excursions` (non-None iff `realized_return` exists).
  Populated ONCE in the SAME `_insert_run_forward_returns` INSERT path beside `mae`/`mfe`.
- Served VERBATIM (no read-path recompute) on:
  - `GET /api/stocks` + `GET /api/stocks/{ticker}` — each `forward_returns` entry now carries
    `max_drawdown` (via `snapshot_serving._forward_returns_by_symbol` / `_forward_returns_for_row`).
  - `GET /api/themes` + `GET /api/sectors` — via the SAME `forward_testing._leadership_returns` builder
    Backtest uses (theme = equal-weight member-basket drawdown; sector = the ETF's own drawdown), so the
    leaderboard MDD is byte-identical to Backtest's for the same date+horizon (J-06).
- Aggregate mean-MDD beside each return stat:
  - Backtest (`compute_forward_aggregates`): `overall`, `by_bucket`, `by_setup`, `by_regime`, `by_vcp`,
    `by_pullback_to_rising_dma`, `by_flat_base_breakout`, `attribution.by_sector` / `by_rank_band` (via
    `_group_means`), each as `mean_max_drawdown` with the same NA discipline.
  - Research (`research._event_study_horizon_row` and `compute_regime_setup_pattern_study._rsp_stats`) —
    `mean_max_drawdown` beside the return/excursion stats.

### J-85 — confirm-gated regenerate-from-scratch rebuild + coverage diagnostic
- New `kind="rebuild"` job in the import-job runner (`data_manager`):
  - `clear_snapshot_set(session)` — whole-row deletes of `forward_returns` → `scanner_results` /
    `sector_scores` / `theme_scores` → `scanner_runs` (children before parents). It NEVER references or
    deletes `daily_prices` and asserts `bars_before == bars_after` (a hard seed-safety invariant).
  - `_run_job` rebuild branch: clear the snapshot set, widen the range to the FULL trading calendar, then
    drive the EXISTING `_do_backfill` create-once path (J-53 parallel + J-66 progress + J-41 guards). No
    new compute path, no in-place UPDATE.
  - Exposed via the EXISTING `POST /api/data/jobs` contract (new `kind`); `validate_job_request` exempts
    rebuild from the source/key + span-cap gates (it reads the committed seed over the full calendar).
    Recorded in the EXISTING run-history (J-60); progress through the EXISTING J-66 surface.
- `data_manager._coverage_diagnostic_absent` — the count of resolved-universe members
  (`config.universe.symbols`) ABSENT from the latest snapshot's scored set, served on the SAME
  `GET /api/data` `coverage` block as `absent_from_latest_snapshot` (0 absent → no banner).

### Frontend
- `components/forward-return.tsx`: new `fmtMdd` / `mddClass` / `MaxDrawdown` helpers (MDD grades on the
  negative/red scale; ≤ 0 or NA).
- `/stocks`, `/stocks/[ticker]`, `/themes`, `/sectors`: five PAIRED max-drawdown columns/values to the
  RIGHT of the forward-return columns — sortable (J-48 view transform, NA-last), colour-graded, NA where
  the return is NA.
- Backtest evidence panels (`components/evidence-panels.tsx`) + Research tables
  (`app/research/page.tsx`): aggregate mean-MDD cells beside the return stats.
- `/data`: a `RebuildPanel` — the J-85 coverage diagnostic banner (only when members are absent) + a
  confirm-gated "Rebuild snapshots for current universe" button (J-69 modal pattern: Card + fixed
  overlay, persistently-visible Confirm) that POSTs `kind="rebuild"` and surfaces progress through the
  EXISTING live job card (`setJob` + poll). Dates are not a parameter (the rebuild is full-calendar).

## Files Changed
- `apps/backend/app/models.py` — `ForwardReturn.max_drawdown` nullable column + docstring.
- `apps/backend/app/db.py` — registered `forward_returns.max_drawdown` in `_ADDITIVE_COLUMNS`.
- `apps/backend/app/engine/forward_testing.py` — `max_drawdown` helper; populate in
  `_insert_run_forward_returns`; `_leadership_returns` projects paired MDD; `_group_means` + `overall`
  + `by_vcp`/`by_*` carry `mean_max_drawdown`; scorecard passes the MDD map.
- `apps/backend/app/engine/snapshot_serving.py` — carry stored `max_drawdown` on stocks/detail/themes/
  sectors `forward_returns` payloads.
- `apps/backend/app/engine/research.py` — `max_drawdown` on event-study + RSP observations;
  `mean_max_drawdown` on `_event_study_horizon_row` and `_rsp_stats`.
- `apps/backend/app/engine/data_manager.py` — `rebuild` kind + `_REBUILD_KINDS`; `clear_snapshot_set`;
  `_coverage_diagnostic_absent` + `compute_coverage` wiring; `_run_job` rebuild branch; `_final_status`
  / `_final_summary` rebuild grading; `validate_job_request` rebuild exemption.
- `apps/backend/app/api/data.py` — `JobCreate.kind` adds `"rebuild"`.
- `apps/frontend/lib/api.ts` — `ForwardReturnEntry.max_drawdown`; `mean_max_drawdown` on group / event-
  study / RSP types; `LeadershipSectorReturn/ThemeReturn/CohortReturn.max_drawdown`;
  `DataCoverage.absent_from_latest_snapshot` + `AbsentFromLatestSnapshot`; `DataJobKind` adds `rebuild`.
- `apps/frontend/components/forward-return.tsx` — `fmtMdd` / `mddClass` / `MaxDrawdown`.
- `apps/frontend/app/stocks/page.tsx`, `apps/frontend/app/stocks/[ticker]/page.tsx`,
  `apps/frontend/app/themes/page.tsx`, `apps/frontend/app/sectors/page.tsx` — paired MDD columns.
- `apps/frontend/components/evidence-panels.tsx` — mean-MDD cells on Backtest.
- `apps/frontend/app/research/page.tsx` — mean-MDD cells on event-study + RSP tables.
- `apps/frontend/app/data/page.tsx` — `RebuildPanel` + `RebuildConfirmModal` + render wiring.
- `apps/backend/tests/test_forward_testing.py` — MDD-math unit tests + backfill-populates-MDD test.
- `apps/backend/tests/test_iter27_rebuild_mdd.py` — NEW: J-85 rebuild (clear-then-create-once, seed
  untouched, deterministic, clear_snapshot_set invariant) + coverage diagnostic + J-86 serving / J-06
  identity / aggregate tests.
- `apps/backend/tests/test_api_engine.py` — the three `*_equals_engine_output` byte-equality guards now
  also assert the additive `max_drawdown` paired sub-key (the canonical byte-equality still strips the
  whole `forward_returns` key, so they stay green).
- `apps/backend/tests/test_db.py` — `forward_returns.max_drawdown` additive-migration test + registry
  guard coverage (`NEW_COLUMNS_THIS_SESSION` + the generic registry loop).

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/<module> -q`
Targeted results (every module this iteration touched — all GREEN):
- `tests/test_db.py` → 9 passed (incl. the new `forward_returns.max_drawdown` additive-migration test +
  registry guard).
- `tests/test_api_engine.py` + `tests/test_iter23_leaderboard_returns.py` → 30 passed (the three
  `*_equals_engine_output` byte-equality guards stay green WITH the additive `max_drawdown` paired key;
  J-81/J-06 leaderboard-vs-Backtest identity holds).
- `tests/test_research.py` + `test_iter20_research_cluster.py` + `test_samples.py` +
  `test_api_research.py` + `test_api_backtest.py` + `test_backtest_scorecard.py` → 201 passed (incl. the
  J-63 pooled byte-identity guard, with `mean_max_drawdown` additive).
- `tests/test_data_manager.py` + `test_api_data.py` + `test_data_manager_backfill_parallel.py` +
  `test_data_manager_backfill_committed_session.py` → 134 passed (coverage + rebuild kind + the parallel
  backfill the rebuild reuses).
- `tests/test_no_magic_numbers.py` (+ MDD math) → 8 passed. NOTE: the MDD helper's only float literal
  (`0.0` seed) was REMOVED — it now takes `min(per-bar drawdowns)` (each `low/peak − 1` is intrinsically
  ≤ 0, the window is non-empty), so `forward_testing.py` carries NO float literal (the No-magic-numbers
  gate, the lone-ever-violation file).
- `tests/test_forward_testing.py` → 49 passed (the full module incl. the aggregation tests now carrying
  `mean_max_drawdown` and the backfill-populates-MDD test, EXIT 0).
- `tests/test_iter27_rebuild_mdd.py` → 13 passed standalone (the J-85 rebuild + coverage diagnostic +
  J-86 serving / J-06 identity / aggregate tests).
- `tsc --noEmit` (frontend) → EXIT 0.

TOTAL targeted: 444 backend tests passed, 0 failed, across EVERY module this iteration touched.

(One combined `test_forward_testing.py + test_iter27_rebuild_mdd.py` run hit the dev-turn 590s timeout —
that was the timeout, NOT a failure; both modules pass green when run separately as above.)

The FULL backend pytest suite (~862 tests, ~50-60 min) must be run nohup-async by the pump and gated on
the flushed `0 failed` line — it does NOT survive a dev-turn background run (iter-2/11 lesson). Every
module this iteration touched is green above.

## Known Issues
- The full backend suite was NOT completed inside this dev turn (per the standing iter-2/11 lesson — the
  ~50-60 min suite does not survive a dev-turn background run). Hand it to the pump nohup-async and gate
  the evaluator on the flushed `0 failed` line, never the in-flight stream.
- The J-86 byte-equality guards rely on the established pattern: the additive `max_drawdown` rides inside
  the already-stripped `forward_returns` key, so `test_api_{stocks,themes,sectors}_equals_engine_output`
  stay green; the guards were ALSO extended to assert the new paired sub-key + that MDD is ≤ 0 / NA.
- The J-85 rebuild over the FULL committed seed (~1356 trading days) is a multi-minute operation by
  design; the unit test exercises it on a reduced ~40-day calendar (file-backed DB — the rebuild's
  worker threads need shared tables, so a `:memory:` DB cannot be used for the rebuild path).
- A live `/data` rebuild was not driven end-to-end in this dev turn (it is browser-QA's job); the real
  orchestration is exercised by `test_iter27_rebuild_mdd.py::rebuilt` over the committed seed.
