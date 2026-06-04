# goal-i_can_see_the_wealthy_future_forever-iter-18 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

J-26 re-scope: the Factor-Lab **Combined** cohort is now a **non-empty composite percentile-rank blend**
(replacing the perpetually-0/NA strict AND-intersection), the strict AND is demoted to a clearly-labelled
secondary cohort, and the user can combine **up to all 11 catalog factors**.

- **`compute_factor_combination` (engine)** — the headline `combined` cohort is replaced by a `composite`
  cohort: over the SAME read-only `_combination_observations` pool, each condition's stored factor value is
  percentile-ranked (REUSE `_average_ranks` → `/n`), oriented by the user's `top`/`bottom` side
  (`top` = fraction as-is; `bottom` = `1 − fraction`), config-weighted-averaged across conditions, and the
  top config-quantile of the blend (REUSE `_quantile_cutoff`) is the cohort. The exact AND-intersection is
  retained as a secondary `strict_overlap` cohort. Both reuse `_cohort_stats` → the downside-only
  `_risk_adjusted`. The payload echoes `composite_quantile` + `weighting`. **The composite is a
  deterministic ranking/GROUPING of stored values (the same read-only class as the J-25 decile sort) — it
  recomputes no factor and no return and is NOT a fitted/ML model.**
- **Two new pure helpers** — `_percentile_rank_fractions` (rank → fraction in (0,1]) and `_composite_scores`
  (the oriented, config-weighted blend). No DB, no recomputation; only `_average_ranks` + arithmetic.
- **Config (`config.yaml`)** — `research.factor_lab.combination`: `max_conditions` **3 → 11**; new required
  `composite` sub-block (`quantile: quintile`, `weighting: { scheme: equal, default_weight: 1.0 }`).
- **Config typing (`config.py`)** — new `CompositeWeightingCfg` + `CompositeCfg`, wired onto `CombinationCfg`
  with boot validation: `composite.quantile` must be a real `quantiles` key; `weighting.default_weight > 0`;
  `scheme` is `Literal["equal"]`. An invalid block raises `ConfigError` at boot.
- **API (`api/research.py`)** — `factor_combination` signature unchanged; the raised `max_conditions`
  auto-lets the existing count-validation accept up to all catalog factors. No `as_of`/date param (J-18).
- **Frontend (`lib/api.ts` + `research/page.tsx`)** — `FactorCombinationResponse` carries `composite` +
  `strict_overlap` (+ `composite_quantile`/`weighting`) replacing `combined`; the table renders Baseline →
  singles → **Combined (composite)** (emphasized) → **Strict overlap (AND)** (secondary, muted); the section
  hint describes the rank-blend; the add/remove cap is payload-driven (no hard-coded UI cap).

## Files Changed

- `config.yaml` — `combination.max_conditions: 3 → 11`; added the required `composite` sub-block.
- `apps/backend/app/config.py` — added `CompositeWeightingCfg` + `CompositeCfg`; wired onto `CombinationCfg`
  + boot cross-check (`composite.quantile` ∈ quantiles; `default_weight > 0`).
- `apps/backend/app/engine/research.py` — `compute_factor_combination`: composite cohort + strict_overlap
  demotion + payload reshape (`combined` → `composite` + `strict_overlap` + echoed metadata); new
  `_percentile_rank_fractions` / `_composite_scores` pure helpers; updated section/docstrings.
- `apps/backend/app/api/research.py` — module docstring updated (composite + strict-overlap); no signature
  change.
- `apps/backend/tests/test_research.py` — composite orientation + config-driven-size tests; opposing-extremes
  test now asserts strict_overlap NA **and** composite populated; cohort-algebra/thin/horizon/labels tests
  updated to `composite`/`strict_overlap`; composite boot-validation tests; too-many-conditions raised to 12.
- `apps/backend/tests/test_api_research.py` — default payload asserts the composite clears min_sample;
  "scales to all factors" + "empty strict-overlap while composite populated" tests; too-many raised to 12.
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py` — added
  the required `composite` key to all 4 inline config dicts (`config-fixtures-need-new-required-keys`).
- `apps/frontend/lib/api.ts` — `FactorCombinationResponse` reshape + `CompositeWeighting` type.
- `apps/frontend/app/research/page.tsx` — `CombinationTable` row order/emphasis + `CombinationLab` hint.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (run ONCE per `backend-test-suite-runtime`)
Result: **461 passed, 4 skipped in 1168.75s (~19.5 min)**. The 4 skips are pre-existing offline/network
integration tests (the `integration` marker — no network), unrelated to this change.
Sub-suites also confirmed green individually during development:
- `tests/test_research.py` — 62 passed (composite orientation, non-empty bar-raise, config-driven size,
  cohort algebra, downside-only risk-adjusted, boot validation)
- `tests/test_api_research.py` — 27 passed (composite clears min_sample, scales to all factors, empty
  strict-overlap while composite populated, 422 error cases up to the raised cap)
- `tests/test_no_magic_numbers.py` — passed (no decile/quantile/weight/cap literal in `research.py`)

Frontend: `cd apps/frontend && npm run build` — compiled + typechecked clean (all 13 routes; `/research`
9.75 kB).

## Source-Verified Seams (per spec note: verify in source, not the QA table)

- **Read-only:** `compute_factor_combination` + the new helpers call no `run_scan`/`score_stocks`/`backfill*`/
  `forward_return`/`detect_*`/`score_regime` (SELECT + pure grouping/ranking only). The read-only keystone
  test (patch-to-raise) covers the composite path.
- **Composite non-empty invariant:** on the real seed the default 2-condition composite cohort is n≈244
  (≥ min_sample 30); the all-11-factors composite is n≈243; the opposing-extremes composite is the whole
  pool while strict_overlap = 0/NA.
- **J-18 (no date state):** no `as_of`/date param on any `/research` endpoint and no date `useState` added to
  `research/page.tsx` (only the shared `horizon`).
- **No DB regen:** the diff does NOT touch `scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/
  `forward_testing.py` math or the snapshot/serving path — J-06/J-07 byte-identical.

## Known Issues

- None. The composite is descriptive (a ranking of stored values), not predictive — surfaced in source
  comments, the payload's descriptive caveat, and the UI hint so the reviewer/auditor do not mistake the
  rank-blend for a recomputation or a fitted model.
