# goal-i_can_see_the_wealthy_future-iter-10 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Agent:** developer
**Status:** complete

> Re-execution of the iter-9 J-14 plan, which silently produced zero product code. This iteration
> ACTUALLY implements J-14: real `apps/` changes are present in git + filesystem (see Files Changed).

## What Was Built

### Backend — per-date forward-test scorecard engine + endpoint (J-14)

- **`_insert_run_forward_returns(session, run, symbols, horizons, max_h, existing) -> int`** — factored the
  per-run forward-return INSERT loop out of `_backfill` into ONE shared helper, so there is exactly one
  forward-return formula (entry = `close_on(D)`, exit = h-th `bars_after(D)` bar via `forward_return`).
  `_backfill` now calls it. **Pure refactor — the iter-6 `test_forward_testing.py` suite stays byte-green.**
- **`backfill_run_forward_returns(session, run, config=None) -> dict`** — create-once, INSERT-only
  population of ONE run's realized forward returns into the existing append-only `forward_returns` table
  (idempotent: a 2nd call inserts 0 rows; never UPDATEs a `scanner_runs`/`scanner_results`/`*_scores` row).
- **`compute_run_scorecard(session, run, config=None) -> dict`** — the SINGLE canonical per-date scorecard.
  READS the stored `forward_returns` for the run joined to the stored `scanner_results` (bucket/setup/
  sector/rank **verbatim**); recomputes nothing. Per horizon (1/5/10/20/60): top-ranked cohort mean + `n`
  (cohort = rank ≤ `walk_forward.control_group.top_n`), excess vs SPY/QQQ/sector (each + `n`), and the 5
  control-group cohorts. No data for a horizon/cohort → `mean_return: null` / `n: 0` (honest NA). Reuses the
  iter-6 `_control_groups` so the cohort + control math has one implementation. Carries `min_sample`,
  `horizons`, and the `SURVIVORSHIP_BIAS_LABEL` verbatim.
- **`GET /api/backtest?as_of=YYYY-MM-DD`** (new router `app/api/backtest.py`, registered in `main.py`) —
  resolves the date via the iter-8 `snapshot_serving.resolved_run` (latest when omitted; create-once for a
  new date; invalid → explicit 4xx/503 via `_STATUS_BY_KIND`), calls `backfill_run_forward_returns`, returns
  the scorecard payload plus `is_latest`. Serves the **scorecard only** — regime/sector/theme/stock values
  stay single-sourced on their existing endpoints.

### Frontend — Backtest workspace (see the frontend handoff for detail)

- New `/backtest` page (own date picker + as-of scan summary + forward-test scorecard), new **Backtest**
  sidebar entry, `fetchBacktest` + types in `lib/api.ts`, and a shared `components/forward-return.tsx`
  formatting module reused by System Health.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` — added `_insert_run_forward_returns` (factored from
  `_backfill`), `backfill_run_forward_returns`, `_scorecard_excess`, `compute_run_scorecard`; `_backfill`
  now calls the shared helper.
- `apps/backend/app/api/backtest.py` — **new**: `GET /api/backtest` (mirrors `system_health.py`; resolves
  via `snapshot_serving.resolved_run`).
- `apps/backend/main.py` — import + register the `backtest` router under `/api`.
- `apps/backend/tests/test_backtest_scorecard.py` — **new**: 10 engine tests (shape/metadata, full-horizon
  exact values, partial/NA, all-NA, group-by-stored-rank, cross-check vs `compute_forward_aggregates`,
  keystone no-recompute, backfill no-lookahead/insert-only/create-once/honest-NA).
- `apps/backend/tests/test_api_backtest.py` — **new**: 7 API tests (default=latest all-NA, historical
  full-window numeric, keystone patch-to-raise, create-once + no snapshot mutation, invalid as-of 4xx,
  503 no-data, scorecard-only payload).
- `apps/frontend/app/backtest/page.tsx` — **new**: the workspace.
- `apps/frontend/components/forward-return.tsx` — **new**: shared `fmtPct`/`returnClass`/`SampleSize`/
  `Return` helpers.
- `apps/frontend/app/system-health/page.tsx` — import the shared helpers (local copies removed; no
  behaviour change).
- `apps/frontend/components/sidebar.tsx` — add the `/backtest` "Backtest" nav entry (`FlaskConical`).
- `apps/frontend/lib/api.ts` — add `fetchBacktest` + `ScorecardExcess`/`BacktestScorecardHorizonRow`/
  `BacktestScorecard`/`BacktestResponse`.

## Anti-goal compliance (verified in source + unit-proven)

- **No lookahead**: scorecard returns come only from `forward_returns` (date > D), entry = `close_on(D)`
  (date ≤ D) — proven by `test_backfill_run_is_no_lookahead_and_insert_only`.
- **Snapshots immutable**: `backfill_run_forward_returns` is INSERT-only into the append-only
  `forward_returns`; `models.py` unchanged, no new table; no UPDATE of any snapshot row — proven by the
  create-once tests.
- **Single source / no recompute in read path**: `compute_run_scorecard` reads stored rows + reuses the one
  `_control_groups` math; the keystone tests patch `forward_return` AND `score_*` to raise and the scorecard
  still serves. The page's scan summary reuses the existing canonical endpoints with `?as_of=`.
- **Honest forward-test / no fabricated data**: NA → `null`/`n=0`, never a 0%; invalid date → explicit
  4xx/503; survivorship-bias label carried verbatim and shown.
- **No magic numbers**: horizons / `min_sample` / `top_n` / seed all from `config.walk_forward`;
  `test_no_magic_numbers` (which scans `forward_testing.py`) stays green.
- **No order/execution path; no secrets**: none introduced.

## Tests Run

Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **213 passed, 0 failed** (885.60s — the full suite pays several walk-forward lifespan boots). This
includes the iter-6 `test_forward_testing.py` suite (byte-green after the INSERT-loop refactor),
`test_no_magic_numbers.py` (still green — `forward_testing.py` is scanned), `test_api_system_health.py` +
`test_api_engine.py` (no regression from the shared-helper/refactor), and the new
`test_backtest_scorecard.py` (10) + `test_api_backtest.py` (7).

Command (frontend): `cd apps/frontend && npm run build`
Result: ✓ Compiled successfully; types valid; all 11 routes generated (incl. `/backtest`, 6.13 kB).

Live smoke test (backend on :8835 against the committed seed, then stopped by port):
- `GET /api/health` → 200 ok; `GET /api/runs` → 11 runs (oldest 2022-10-07, latest 2026-05-28).
- `GET /api/backtest` (latest) → 200, `is_latest=true`, all-NA scorecard (`mean_return: null`, `n: 0`).
- `GET /api/backtest?as_of=2022-10-07` (full window) → 200, `is_latest=false`, NUMERIC per-horizon cohort
  returns (cohort `n=20` = `top_n`), excess vs SPY numeric, random-same-sector control `n=31`.
- `GET /api/backtest?as_of=2999-01-01` → 400; `?as_of=1900-01-01` → 400; `?as_of=not-a-date` → 422.

## Known Issues

- The frozen seed legitimately yields NA for longer horizons on recent dates (honest, not a bug).
- Two date controls visible on `/backtest` (the page's own picker by design + the global top-bar switcher,
  which does not drive this page).
- Dedicated browser-QA has historically SKIPPed on a CORS/port flap (runner-owner issue, non-gating per the
  spec); J-14 is otherwise proven by the unit/API suite + a clean production build + the backend live
  smoke test of `/api/backtest` recorded under Tests Run.

## Suggested Next Phase

J-16 (VCP detection — config-backed detector + filter + badge) next, then J-12 (config-backed glossary /
`/methodology`, including the VCP catalog entry) to close the round — a clean J-14 leaves 14/16 Must-haves
passing.
