# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52
**Date:** 2026-06-26
**Agent:** developer
**Status:** complete

## What Was Built

J-109 — the Factor Lab (`/research/factor-lab`) now shows **every configured horizon at once** as
paired **(forward-return, max-drawdown)** columns, on both the all-factors table and each factor's
expandable decile grid. The single-horizon `<select>` is gone; rank-IC + downside risk-adjusted are
fixed at `config.walk_forward.default_horizon`. Every figure is byte-identical to the existing
single-horizon `compute_factor_lab(factor, horizon)` output — no number recomputed.

- **Backend — paired max-drawdown in the factor pool.** `_factor_observations` now column-projects and
  carries `forward_returns.max_drawdown` (J-86) per observation; `_deciles` gained an additive
  `mean_max_drawdown` (mean over members with a stored drawdown — the `_group_mdd` NA convention, None
  when none). This flows into BOTH `compute_factor_lab` (single-horizon, the byte-identity reference +
  the samples drill-down) and the new all-horizons view, so the paired column is identical between them.
- **Backend — all-horizons builder + view.** New `_all_factor_observations_by_horizon` builds the shared
  per-observation pools for EVERY config horizon in ONE streamed, column-projected sweep (reads
  `realized_return` + `max_drawdown` for `horizon IN horizons`, streams `ScannerResult` ordered
  `(run_id, id)`, no unbounded `.all()`). `compute_factor_lab_all` rebuilt: per factor it emits the
  rank-IC + top-decile risk-adjusted + n_total at the default horizon, plus a `by_horizon` block with that
  factor's full decile table (paired return + max-drawdown) at every horizon. Dropped the now-meaningless
  `horizon` parameter (the view is horizon-independent).
- **Backend — cache schema token.** `factor_lab_all_cached` folds `_ALL_FACTORS_SCHEMA_TOKEN`
  (`"allh-mdd-v1"`) into the EventStudyCache `dataset_version` slot, so every pre-iter-52 (old single-
  horizon shape) cached row is a guaranteed MISS and is pruned on the next write — never served field-less.
  Reuses the EXISTING `event_study_cache` table (NO new `table=True` model; `test_db.py` guard unchanged).
- **Backend — API.** `GET /api/research/factor-lab?all=true` serves the new shape via the new cache
  signature; horizon validation (422) and 503-no-data behaviour unchanged. The single-factor view
  (`?factor=&horizon=`) is unchanged except its deciles additively gain `mean_max_drawdown`.
- **Backend — samples.** `GET /api/research/samples?kind=factor&slice=decile` already accepts any
  `(factor, horizon, decile)`; confirmed (live + unit) count-coherent at every horizon — no code change
  needed there.
- **Frontend.** `FactorLabPage` drops the horizon selector and fetches `?all=true` (no horizon). The
  all-factors table renders 5 forward-return + 5 paired max-drawdown columns (top-decile cohort per
  horizon), each sortable NA-last (new per-horizon `fwd:`/`mdd:` sort keys); rank-IC / risk-adjusted
  labelled with the default horizon. Expanding a factor reveals the all-horizon decile grid (per-decile
  return + paired max-drawdown at every horizon) with a per-`(factor, horizon, decile)` `N=` drill-down
  chip on each return cell. Max-drawdown cells colour-grade via the existing `lib/mdd-color` tokens.

## Files Changed

- `apps/backend/app/engine/research.py` -- `_factor_observations` carries `max_drawdown`; `_deciles` adds
  `mean_max_drawdown`; new `_all_factor_observations_by_horizon` (one-sweep all-horizons bounded read);
  `compute_factor_lab_all` rebuilt to the all-horizons paired shape (drops `horizon` arg);
  `factor_lab_all_cached` folds `_ALL_FACTORS_SCHEMA_TOKEN` into the cache key (drops `horizon` arg).
- `apps/backend/app/api/research.py` -- `?all=true` calls the new `factor_lab_all_cached(session, cfg, as_of=)`.
- `apps/frontend/lib/api.ts` -- `FactorDecileRow.mean_max_drawdown`; new `FactorHorizonDeciles`;
  `FactorTableRow.by_horizon` (replaces `deciles`); `FactorLabAllResponse` drops `horizon`;
  `fetchFactorLabAll(asof?, signal?)` drops the horizon param.
- `apps/frontend/app/research/_labs.tsx` -- `FactorLabPage` (no selector), `FactorsTable` (paired all-horizon
  columns + per-horizon sort keys), `FactorRows` + new `TopDecileCell`, `DecileTable` rebuilt as the
  all-horizon paired decile grid with `DecileReturnCell` (+ `N=` chip) / `DecileMddCell` (mdd-color).
- `apps/backend/tests/test_factor_lab_all.py` -- rewritten for all-horizons byte-identity, paired-MDD shape,
  cache schema-token MISS-then-prune against a real old-schema row, samples count-coherence across horizons.
- `apps/backend/tests/test_research_streaming.py` -- `_factor_observations_reference` carries `max_drawdown`;
  added cold-path / byte-identity / chunk-independence tests for `_all_factor_observations_by_horizon` and
  `compute_factor_lab_all`.
- `apps/backend/tests/test_api_research.py` -- `factor_lab_all` API tests updated to the new shape (per-horizon
  byte-identity vs the single-factor view, `by_horizon`, no single `horizon`, `mean_max_drawdown` present).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (run per-file during dev)

Result (changed/affected files, all green):
- `test_factor_lab_all.py` — 14 passed
- `test_research_streaming.py` — 35 passed
- `test_api_research.py` — 70 passed
- `test_research.py` + `test_samples.py` + `test_no_magic_numbers.py` + `test_db.py` + `test_iter20_research_cluster.py` — 135 passed
- Frontend: `node_modules/.bin/tsc --noEmit` — EXIT 0 (typecheck clean)

Full suite: launched async (non-load-bearing this iter) ->
`reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52-fullsuite.log`
(the flushed `0 failed, EXIT 0` is owed before a future GOAL_ACHIEVED candidacy, per the iter-50 lesson).

## Live integration (real backend + DB, 701,218 forward_returns / 125,019 scanner_results / 1,357 runs)

- Cold uncached `compute_factor_lab_all` over the LIVE DB: **47.2s, peak RSS 517MB — NO MemoryError**
  (the iter-46/47/48 OOM-sensitive path stays bounded). All 5 horizons computed in one sweep.
- `GET /api/research/factor-lab?all=true` served `http=200` (cold ~47s, cached hit ~18ms, 117KB);
  shape verified: no single `horizon`, `horizons=[1,5,10,20,60]`, `default_horizon=20`, 11 factors, each
  entry `{key,label,family,direction,n_total,rank_ic,risk_adjusted,by_horizon}`, each decile carrying
  `mean_max_drawdown` (e.g. leadership_score D10@20d return +0.031 / MDD -0.146 / n 12,297).
- Samples count-coherence over HTTP for `(leadership_score, h, D10)` at h=1/5/60: all `http=200`,
  `total == published n` (12,480 / 12,442 / 11,822). No 4xx.
- `scripts/start-backend.sh` (port 8255) and `scripts/start-frontend.sh` (port 3255) both start cleanly;
  `/research/factor-lab` compiles and serves `http=200`. Both servers stopped after verification.

## Known Issues

- The frontend node unit-test runner (`node lib/*.test.ts`) errors `ERR_UNKNOWN_FILE_EXTENSION` on this
  box's Node 22.22.1 (TS type-stripping not enabled by default) — an environment quirk unrelated to this
  change; correctness of the TS changes is gated by `tsc --noEmit` (EXIT 0). No new frontend unit test was
  added (no pre-existing factor-lab component test harness; the per-horizon sort + paired columns are
  covered by the backend byte-identity tests + live HTTP checks + in-iteration browser-QA).
- `next lint` is not configured in this project (prompts interactively) — not a gate; not run.
- The all-factors table is intentionally WIDE (5 forward-return + 5 max-drawdown columns + the default-
  horizon rank-IC/N/risk-adjusted). The table Card uses `overflow-x-auto` (horizontal scroll) rather than
  dropping columns, per the plan's layout requirement.
- The decile grid shows the factor range at the **default horizon** as a visible column; each horizon's
  own per-decile range (membership differs per horizon) is on that cell's hover title (kept honest without
  exploding the column count).
