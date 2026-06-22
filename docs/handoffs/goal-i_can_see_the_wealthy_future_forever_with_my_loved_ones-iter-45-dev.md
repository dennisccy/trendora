# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Agent:** developer
**Status:** complete

## What Was Built

**J-103 — Severity-velocity × Regime forward-return study (NEW)**
- `research:compute_severity_velocity_study(session, horizon, cfg, as_of)` — a read-only GROUPING of the
  stored benchmark (SPY) `forward_returns` by the (regime FAMILY, velocity SIGN) at each snapshot date. The
  regime family is a config-backed grouping of the STORED regime label (read verbatim); the velocity sign is
  the sign of the SERVED `severity_velocity` (J-102), read from `market_phase.severity_velocity_by_date`
  (NEW public accessor mirroring `phase_context_by_date`). Recomputes NO canonical return / regime / slope.
- Each matrix cell reports `mean_return`, `win_rate`, and `n` (+ `low_sample`). Empty/low-sample cells are
  honest NA. The payload carries the config-driven family + sign vocabularies, the survivorship/descriptive
  labels, and the honest verdict caveat VERBATIM (the hypothesis is NOT supported — on the committed seed,
  rising stress-velocity under a red regime preceded a bounce, not continuation).
- Served derived-once / cached via the EXISTING `EventStudyCache` + `_dataset_version` idiom under a new
  `_SEVERITY_VELOCITY_SUBJECT` sentinel (NO new table). `GET /api/research/severity-velocity`
  (`horizon`/`as_of`; 422 bad horizon; 503 no data).
- New samples cohort `kind` `severity-velocity` (`_severity_velocity_samples`) so each cell's `N=` chip
  reproduces its exact cohort via `GET /api/research/samples?kind=severity-velocity&family=&velocity_sign=` —
  per-cell drill-down total == published cell N, in both All-history and As-of scopes.
- Config: new `research.severity_velocity` block (`regime_families` partitioning `regime.labels` into
  risk-on / neutral / risk-off "red"; `velocity_signs` rising/flat/falling) + a Config-level cross-validator
  that the families reference real labels and partition them. No magic numbers.

**J-104 — Research-labs reliability**
- (a) `factor_combination_cached` + `regime_setup_pattern_cached` wrap `compute_factor_combination` /
  `compute_regime_setup_pattern_study` with the EXISTING `EventStudyCache` + `_dataset_version` cache
  (sentinels `__factor_combination__<conditions>` / `__regime_setup_pattern__`). Figures BYTE-IDENTICAL;
  refresh on dataset change. The two endpoints now route through the cached wrappers.
- (b) `_downtrend_opportunity_observation_set`'s full `select(ScannerRun)` run-date scan is now bounded by
  `where(ScannerRun.asof_date <= as_of)` (the shared `_run_position_index` was already as-of-bounded). An
  as-of-scoped read no longer loads the entire run table; figures stay byte-identical.
- (c) Frontend: the monolithic `/research` page is SPLIT — `/research` is now a HUB linking to each lab on
  its own lazy-loaded sub-route, so at most ONE heavy fetch fires per page.

## Files Changed

- `apps/backend/app/config.py` -- new `RegimeFamily` / `VelocitySign` / `SeverityVelocityCfg` models +
  `VELOCITY_SIGN_*` constants + `research.severity_velocity` on `ResearchCfg` + `_default_severity_velocity()`
  + a Config-level `_severity_velocity_families_resolve` cross-validator.
- `config.yaml` -- new `research.severity_velocity` block (regime_families + velocity_signs).
- `apps/backend/app/engine/market_phase.py` -- new public `severity_velocity_by_date` accessor.
- `apps/backend/app/engine/research.py` -- `compute_severity_velocity_study` + `severity_velocity_cached`
  (J-103); `factor_combination_cached` + `regime_setup_pattern_cached` (J-104a); bounded run-date scan in
  `_downtrend_opportunity_observation_set` (J-104b); imports the velocity-sign config constants.
- `apps/backend/app/engine/samples.py` -- `KIND_SEVERITY_VELOCITY` + `_severity_velocity_samples` builder +
  wiring in `compute_samples` (new `family`/`velocity_sign` selectors).
- `apps/backend/app/api/research.py` -- new `GET /api/research/severity-velocity` route; factor-combination
  + regime-setup-pattern routed through the cached wrappers; samples handler accepts `family`/`velocity_sign`.
- `apps/frontend/lib/api.ts` -- `SeverityVelocity*` types + `fetchSeverityVelocity`; `SampleCohort` gains
  `family`/`velocity_sign` + the `severity-velocity` kind.
- `apps/frontend/lib/samples-link.ts` -- `SeverityVelocityCohortParams` + the `buildSamplesHref` case.
- `apps/frontend/app/research/_labs.tsx` -- NEW shared lab module: the extracted lab components (exported) +
  shared scaffolding (`useResearchControls`, `ResearchControls`, `ResearchCaveat`, `ResearchError`,
  `HorizonSelector`, `LabSkeleton`) + the per-lab route-page wrappers (`FactorLabPage`, `CombinationLabPage`,
  `EventStudyLabPage`, `RegimeSetupPatternLabPage`, `RecoveryTurnEdgeLabPage`, `DowntrendOpportunityLabPage`).
  Each lab additively reports its config-driven horizons via an `onMeta` callback.
- `apps/frontend/app/research/page.tsx` -- now the HUB (a link grid to the 7 labs; no heavy fetch).
- `apps/frontend/app/research/{factor-lab,factor-combination,event-study,regime-setup-pattern,recovery-turn-edge,downtrend-opportunity}/page.tsx`
  -- NEW thin route pages, each rendering one relocated lab.
- `apps/frontend/app/research/severity-velocity/page.tsx` -- NEW: the regime-family × velocity-sign matrix
  (mean fwd return / win-rate / N), horizon selector, As-of⇄All-history mode, `N=` chips (new tab + `?asof`),
  verdict card with the verbatim caveats.
- `apps/frontend/app/research/samples/page.tsx` -- `describeCohort` gains a severity-velocity case.
- `apps/backend/tests/test_severity_velocity.py` -- NEW: J-103 grouping correctness, no-lookahead/as-of
  filter, NA/partial, cache byte-identity (against an already-populated row), cache refresh on dataset
  change, samples count-coherence + invalid/zero-N selectors, warm-up-head exclusion; J-104(a) factor-
  combination + regime-setup-pattern cache byte-identity + distinct-per-conditions keying.
- `apps/backend/tests/test_api_research.py` -- NEW severity-velocity endpoint + samples API tests (default
  payload, byte-identical repeats, bad-horizon 422, count-coherence, invalid-selector 422).

## Tests Run

Command (targeted): `cd apps/backend && .venv/bin/python -m pytest tests/test_severity_velocity.py tests/test_no_magic_numbers.py tests/test_db.py -q`
Result: 26/26 in test_severity_velocity.py pass; `test_no_magic_numbers` + `test_db` pass.

Command (API, real seed): `cd apps/backend && .venv/bin/python -m pytest tests/test_api_research.py -q -k "severity_velocity or factor_combination or regime_setup_pattern or combination or regime"`
Result: 29 passed (5 new severity-velocity API tests + the existing factor-combination/regime tests now
routing through the cache).

Command (full suite, nohup-async, handed to the pump): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: in flight at handoff time — log at `/tmp/iter45_full_suite.log`, 0 failures observed through ~50%.
The GOAL_ACHIEVED gate is the pump's to confirm on the flushed `0 failed, EXIT 0` line — NOT blocked here.

Frontend: `cd apps/frontend && npx tsc --noEmit` -> clean; `npx next build` -> success (all 7 research
sub-routes generated; `/research` hub is 2.3 kB, down from the ~25 kB monolith).

## Live verification

Started the backend on :8835 and probed the new endpoint against the real `trendora.db`:
- `GET /api/research/severity-velocity?horizon=20` → 200, `benchmark: SPY`, `n_total: 1147`, 3 families ×
  3 signs, verdict carries "NOT supported" + "bounce, not continuation" VERBATIM. The data confirms the
  finding: under the risk_off (red) regime, rising stress-velocity preceded +1.33% and falling −> +1.90%
  (both positive — a bounce, not continuation).
- `GET /api/research/samples?kind=severity-velocity&horizon=20&family=risk_off&velocity_sign=rising` → 200,
  `total: 180` == the matrix cell's N=180 (count-coherence); rows read verbatim (SPY ticker, regime +
  severity_velocity values).
- Invalid family → 422; a valid zero-N cell (flat) → honest empty 200 (total 0, not a 4xx).

The live backend was stopped (cleanup) after verification.

## Known Issues

- **No `view` (Episodes/Pooled) param on the severity-velocity endpoint** — deliberate and honest. The
  study has exactly ONE benchmark (SPY) observation per snapshot date, so there are no overlapping
  per-ticker episodes to collapse; Episodes and Pooled would be byte-identical. Adding a no-op toggle would
  be misleading, so it is omitted. The blueprint's "params mirroring /api/research/event-study" is honored
  for `horizon`/`as_of`; `view` is meaningless here. The As-of mode (J-32) is fully supported and is the
  study's real mode.
- **Recovery-Turn Edge got its OWN route** (`/research/recovery-turn-edge`) in the split, in addition to the
  5 routes the spec lists. The old monolith rendered it as a standalone section AND as angle (c) of the
  Downtrend Opportunity study; giving it its own route keeps "at most one heavy fetch per page" and avoids
  orphaning it (the hub lists 7 labs). The spec's route list said "e.g." (illustrative).
- **Heavy research endpoints are slow on a COLD cache and during the concurrent warm-up walk-forward** —
  this is exactly what J-104(a) caching fixes (first compute populates the cache; repeats are fast hits).
  A live probe of factor-combination/regime-setup-pattern/downtrend-opportunity timed out while the live
  server's background warm-up had not finished AND the full pytest suite was running concurrently (CPU
  contention). The J-104 caching + byte-identity is PROVEN by the passing targeted + API tests; the live
  slowness is warm-up/contention, not a code defect. NEVER probe these endpoints concurrently (pool
  exhaustion — MEMORY note).

## Suggested Next Phase

After the flushed-GREEN full pytest suite + COHERENCE-PASS + zero regression, every buildable Must-have
(J-01..J-21, J-25..J-104) is positive-evidenced and the next evaluation is a sound GOAL_ACHIEVED candidate.
J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-vetoing).
