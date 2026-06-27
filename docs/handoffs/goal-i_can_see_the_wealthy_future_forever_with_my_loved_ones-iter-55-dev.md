# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Agent:** developer
**Status:** complete

## What Was Built
J-112 — the **Regime × Phase × Factor 3-way decile study** (`/research/regime-phase-factor`), the LAST
unbuilt buildable Must-have. A read-only re-surfacing of already-stored canonical values (recomputes nothing):

- **Engine** (`research.py`): `compute_regime_phase_factor_study(session, *, factor, view, as_of, config)` +
  its cache wrapper `regime_phase_factor_cached`. For a SELECTED factor it pools the same cross-sectional
  forward-return observations the sibling labs use, tagging each with (a) the run's stored
  `ScannerRun.regime_score` (J-80, verbatim, via `_regime_meta_by_run`), (b) the snapshot date's SERVED 0-100
  severity from the `market_phase` causal timeline (J-87/J-111, verbatim, via `_phase_severity_meta_by_run`,
  joined by snapshot date), and (c) the SELECTED factor's stored value (Factor-Lab `_extract_factor_value`,
  verbatim). Each dimension is bucketed into deciles via the EXISTING `_deciles`/`_decile_member_slice` edges
  (`_assign_triple_deciles`) and grouped by the `(regime-decile, severity-decile, factor-decile)` triple;
  per `config.walk_forward.horizons` horizon it reports mean realized forward return + paired mean
  max-drawdown + n, NA below `config.walk_forward.min_sample`.
  - Bounded read (`_regime_phase_factor_members_by_horizon`): ONE FR scan (column-projected + `yield_per`),
    ScannerResult streamed in `(run_id, id)` order (full ORM row — a component factor reads `record_json`),
    no unbounded `.all()`. One heavy read serves all horizons; the single-horizon
    `_regime_phase_factor_observation_set` is byte-identical to its all-horizons slice (the samples keystone).
  - Cache: REUSES `event_study_cache` (no new `table=True` model — `test_db.py` guard UNCHANGED). The key
    folds a schema token + the market-phase `SCHEMA_VERSION`/dataset stamp (severity source) + the SELECTED
    factor (subject = `__regime_phase_factor__:<factor>`, no cross-factor bleed).
- **API** (`api/research.py`): `GET /api/research/regime-phase-factor` (`factor` + `view` Episodes/Pooled +
  `as_of` FILTER-only; no `horizon` selector — all-horizons paired shape). 422 on unknown factor/view, 503
  no data. Samples endpoint widened with `regime_decile`/`severity_decile`/`factor_decile` params for the new
  kind.
- **Samples** (`samples.py`): `KIND_REGIME_PHASE_FACTOR` + `_regime_phase_factor_samples` reproducing the
  exact triple cohort from the SAME shared observation builder + `_assign_triple_deciles` (count-coherent;
  every emitted/in-range combination resolves, malformed → 4xx).
- **Config** (`config.py` + `config.yaml`): `research.regime_phase_factor_page_size` (default 30), served in
  the payload so the 30-rows/page constant is config-sourced (no inline literal in the CALC_FILEs).
- **Frontend**: new lazy sub-route page + `RegimePhaseFactorPage` (factor selector, three "All"-default
  decile filters, NA-last column sort resolvable by `aria-label`, client-side pagination at the config page
  size, As-of mode toggle, `N=` chips pinned `view=pooled`), a Research-hub tile (`Boxes` icon), the samples
  `describeCohort` branch, `fetchRegimePhaseFactor` + types, and the `RegimePhaseFactorCohortParams`
  samples-link branch. Pinned to the pooled view (no Episodes/Pooled toggle) per the iter-53 lesson.

## Files Changed
- `apps/backend/app/engine/research.py` -- J-112 engine: builders, `_assign_triple_deciles`, study + cache.
- `apps/backend/app/engine/samples.py` -- `KIND_REGIME_PHASE_FACTOR` + `_regime_phase_factor_samples` + wiring.
- `apps/backend/app/api/research.py` -- new endpoint + samples decile params.
- `apps/backend/app/config.py` -- `regime_phase_factor_page_size` field + validation.
- `config.yaml` -- `research.regime_phase_factor_page_size: 30`.
- `apps/backend/tests/test_regime_phase_factor.py` (new) -- 38 tests (byte-identity ≥2 factors/both views/both
  scopes, provenance, bounded-read guard, cache schema-token + mp-stamp + per-factor invalidation on a real
  populated old-schema row, samples count-coherence, invalid-selector).
- `apps/backend/tests/test_api_research.py` -- 7 new endpoint/shape/factor-switch/as-of/HTTP-coherence/4xx tests.
- `apps/backend/tests/test_samples.py` -- triple-cohort count-coherence test.
- `apps/frontend/app/research/_labs.tsx` -- `RegimePhaseFactorPage` + helpers.
- `apps/frontend/app/research/regime-phase-factor/page.tsx` (new) -- the lazy sub-route.
- `apps/frontend/app/research/page.tsx` -- hub tile.
- `apps/frontend/app/research/samples/page.tsx` -- `describeCohort` branch.
- `apps/frontend/lib/api.ts` -- types + `fetchRegimePhaseFactor` + `SampleCohort` extension.
- `apps/frontend/lib/samples-link.ts` -- `RegimePhaseFactorCohortParams` + `buildSamplesHref` branch.

## Tests Run
- Backend (full suite, nohup-async): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
  Result: **1210 passed, 4 skipped, 0 failed** (35:00). Flushed line in
  `reports/qa/goal-...-iter-55-test.log`. Includes the new `test_regime_phase_factor.py` (38), the 7 new
  `test_api_research.py` cases, and the new `test_samples.py` triple-cohort case. `test_no_magic_numbers` and
  `test_db.py` expected-tables guard both green (no new table; no inline literal). The 4 skips are the known
  data-walled/conditional cases (unchanged this iter).
- Frontend type-check: `cd apps/frontend && npx tsc --noEmit` → EXIT 0 (no type errors). `next lint` is not
  configured in this repo (interactive setup prompt) — `tsc` is the type gate.

## Live Verification (cold, freshly-restarted warmed backend :8255 / frontend :3255 via scripts/dev.sh)
One heavy fetch at a time (suite NOT running concurrently):
- `GET /api/research/regime-phase-factor` (cold, default) → HTTP 200 in 7.08s, 160 rows, 776 populated cells —
  no OOM on the cold-miss compute.
- `?view=pooled` (cold) → 200 in 7.7s, 468 rows, total@20 = 122,964 observations.
- `?view=pooled&factor=entry_quality_score` → 200, rows DIFFER from leadership_score (factor selector drives
  the study).
- `?view=pooled&as_of=2024-06-01` → 200, `asof_date` echoed, total@20 = 67,727 (< 122,964 — the As-of FILTER
  shrinks n).
- Samples drill-down (pooled, highest-n combination regime D10 × severity D1 × factor D6) → `total` = 1215 ==
  published n 1215 (live count-coherence); rows carry regime_score + severity + factor value + forward return.
- Invalid selectors (out-of-range decile; unknown factor) → 422.
- Frontend routes: `/research/regime-phase-factor` → 200 (title rendered, 0 native `input[type=date]`),
  `/research` hub contains the `regime-phase-factor` tile, samples route → 200.

Both servers were left UP (backend :8255 with `--reload`, frontend :3255) for the dedicated browser-qa-agent
step, per the plan's live-render-evidence lesson (iter-52 skipped on a torn-down frontend).

## Known Issues
- None. The 3-way grid is intentionally sparse (many low-sample combinations) — handled by the config
  min-sample "NA + n" discipline + the 30-rows/page pagination, as designed. The lab is pinned to the pooled
  view (the whole-cross-section episode collapse degenerates); the backend still serves + unit-proves both
  views for the samples structural twin.
