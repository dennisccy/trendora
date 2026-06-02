# goal-i_can_see_the_wealthy_future_forever-iter-12 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

J-26 — **Factor Lab multi-factor combination cohorts.** A new read-only aggregation + serving endpoint +
frontend section that lets the user combine **2–3 factor conditions** (each a catalog factor at its
top/bottom quantile) and read the **combined-AND cohort** beside the **unconditional baseline** and **each
single-factor cohort** — mean / median forward return, hit-rate, downside-risk-adjusted, and n. Strictly
additive over the proven read-only `/research` Factor-Lab seam (J-25 decile/IC, J-27 regime split).

- **`compute_factor_combination(session, conditions, horizon, config)`** in `app/engine/research.py` — the
  SINGLE canonical multi-factor combination read. Reuses the read-only seam verbatim: builds a multi-factor
  observation pool (`_combination_observations`) by SELECT-joining stored `ForwardReturn.realized_return`
  to the stored factor value on `ScannerResult` via the existing `_extract_factor_value`; keeps an obs only
  when a realized return exists **and every referenced factor is non-null** (a NULL excludes it — never
  fabricated). Per-condition membership uses a deterministic **nearest-rank** quantile cutoff over the
  shared pool's values (`top` → value ≥ cutoff(1−fraction); `bottom` → value ≤ cutoff(fraction); boundary
  ties included). Cohorts: `baseline` = whole pool; one `single` per condition; `combined` = exact
  set-intersection (AND). Per-cohort stats reuse the downside-only `_risk_adjusted` (never total vol); an
  empty/low-sample cohort shows NA + n. **SELECT-only — calls no scoring/return/pattern/regime math.**
- **`GET /api/research/factor-combination`** in `app/api/research.py` — serves
  `compute_factor_combination(...)` verbatim. Params: `condition` (repeatable `"<factor>:<side>:<quantile>"`)
  + optional `horizon`. Empty `condition` → `config…combination.default_conditions`. Validates count ∈
  [min,max], factor ∈ catalog, side ∈ {top,bottom}, quantile ∈ config quantiles, horizon ∈
  `walk_forward.horizons` → **422**; **503** when no price data. **No as-of/date param (J-18).**
- **`config.yaml`** — new `research.factor_lab.combination` block (`min_conditions: 2`, `max_conditions: 3`,
  a `quantiles` list [quintile/quartile/tertile/half], and the 2-condition `default_conditions`). No
  existing tunable touched. Low-sample threshold reused from `walk_forward.min_sample`.
- **`app/config.py`** — typed + boot-validated the block: new `QuantileOption`, `DefaultCondition`,
  `CombinationCfg` sub-models; added required `combination: CombinationCfg` to `FactorLabCfg`. Validates
  `1 ≤ min ≤ max`, `fraction ∈ (0,1)`, unique quantile keys, `min ≤ len(default_conditions) ≤ max`,
  default quantile keys resolvable (on `CombinationCfg`), and default factor keys resolvable (on
  `FactorLabCfg`, which can see both `factors` and `combination`). Invalid block → `ConfigError` at boot.
- **Frontend** — `lib/api.ts` types + `fetchFactorCombination`; `app/research/page.tsx` new "Multi-factor
  combination cohort" section. See the frontend handoff for detail.

## Files Changed

- `apps/backend/app/engine/research.py` — add `_combination_observations`, `_quantile_cutoff`,
  `_cohort_stats`, `_condition_payload`, `compute_factor_combination`; import `ceil` + `median`.
- `apps/backend/app/api/research.py` — add the `GET /research/factor-combination` route + `_CONDITION_SIDES`.
- `config.yaml` — add `research.factor_lab.combination`.
- `apps/backend/app/config.py` — add `QuantileOption`/`DefaultCondition`/`CombinationCfg`; add
  `combination` to `FactorLabCfg` + the default-factor cross-check.
- `apps/frontend/lib/api.ts` — add combination types + `fetchFactorCombination`.
- `apps/frontend/app/research/page.tsx` — add the combination section (`CombinationLab` + sub-components).
- `apps/backend/tests/test_research.py` — add J-26 engine tests + combination config boot-validation tests.
- `apps/backend/tests/test_api_research.py` — add J-26 endpoint tests (default payload, J-18 no-date,
  re-point, 422/503).
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py` —
  add the now-required `combination` sub-block to their minimal `factor_lab` config fixtures.
- `docs/handoffs/…-iter-12-dev.md`, `…-iter-12-frontend.md`,
  `reports/phase-…-iter-12-implementation-summary.md` — this handoff + the frontend handoff + summary.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (run once; project memory: ~14 min)
Result: **411 passed, 4 skipped in 1078.10s (~18 min)** — GREEN, no failures. The 4 skips are the
offline-skipped `@integration` external-network tests (e.g. the Stooq live fetch). This is iter-11's
384 passed + 27 new iter-12 tests (15 in `test_research.py` + 12 in `test_api_research.py`) = 411.

Targeted results during development (all green):
- `tests/test_research.py` — **42 passed** (incl. all new J-26 engine + combination-config tests).
- `tests/test_api_research.py` — **18 passed** (7 factor-lab + 11 new factor-combination, incl. 422/503/J-18).
- `tests/test_config.py` + `tests/test_config_engine.py` — **64 passed**.
- `tests/test_no_magic_numbers.py` — **2 passed** (research.py still introduces no literal in calc code).

Frontend: `cd apps/frontend && npm run build` → **Compiled successfully**, types valid, 14 routes generated.

## Anti-goal compliance (verified in source)

- **Read-only / no recompute:** `compute_factor_combination` + `_combination_observations` issue only
  SELECTs against `ForwardReturn` + `ScannerResult` and call no `run_scan`/`score_stocks`/`backfill*`/
  `forward_return`/`detect_*`/`score_regime`. A patch-to-raise keystone test asserts this.
- **Downside-only risk:** the risk-adjusted column reuses `_risk_adjusted` (`mean / downside_deviation`,
  MAR=0) verbatim — never total volatility; NA when no downside / n < 2.
- **No magic numbers:** condition limits, quantile fractions, and defaults all come from config; the cutoff
  method uses only structural integers (`test_no_magic_numbers` scans research.py and passes).
- **No fabricated data:** a factor-NULL observation is excluded from the pool; low-sample/empty cohorts show
  NA + n, never a fabricated 0.
- **One date control (J-18):** the endpoint takes no as-of param; the frontend section adds only
  `conditions` state and reuses the page's shared horizon.
- **Coherence:** the new value is registered in the session blueprint Data Contract (decomposer rows 78,
  108, 170) with ONE computing module (`app.engine.research:compute_factor_combination`) + ONE serving
  endpoint (`GET /api/research/factor-combination`); no existing contract value recomputed or re-homed.

## Known Issues

- The combined cohort is the strict AND-intersection, so it can become thin quickly (3 conditions or
  opposing extremes) → shown honestly as **NA + n**, never padded. This is by design (the NA fixture).
- The nearest-rank cutoff includes boundary ties, so a Top/Bottom cohort may be marginally larger than the
  nominal fraction on a small pool — documented, honest empirical-cutoff behavior.
- **return/MAE / MAE-MFE excursion** is intentionally out of scope (needs the J-29 post-snapshot excursion
  path); the risk-adjusted column is the established downside-deviation measure and the UI states this.
- **Live service startup verified.** A stale pre-iter-12 `uvicorn` was running on port 8835 (started by an
  earlier pipeline stage; no `--reload`, so it 404'd on the new route). I restarted trendora's backend
  **by port** (`fuser -k 8835/tcp` then `scripts/start-backend.sh`; never a broad pkill — multi-project
  machine) — it booted in ~2s and served `GET /api/research/factor-combination` **HTTP 200** against the
  committed seed: default conditions resolved from config (rs_spy_3m top quintile, atr_pct bottom tertile),
  **pool_n=1217**, baseline n=1217, singles n=244 / n=406, **combined-AND n=49** (< each single — interaction
  visible; the combined cohort beat both singles and the baseline on mean/hit-rate/risk-adjusted), J-18
  no-date field, and 422 on unknown factor / too-few conditions / bad horizon. The frontend `/research`
  served HTTP 200 (next dev hot-reloaded the new section). **I then stopped the backend I started (port
  8835 left free)** so the browser-QA stage starts its own fresh instance from disk — honoring the
  "kill servers you start" rule and avoiding a port conflict. The pre-existing frontend dev server (not
  started by me) was left running. The change is additive and does not touch startup/lifespan/CORS.

## Suggested Next Phase

Per the iter-11 evaluator's autonomous runway: **J-30 (volatility factor family)** is the smallest next
extension — it adds level/contraction/downside volatility factors to the same config-driven catalog and
rides the J-25 decile/IC + J-27 regime split with no new seam. J-29 (event study; introduces the
post-snapshot MAE/MFE excursion path and return/MAE) is the larger lift after J-30, and J-31 (synthesis)
needs J-29 + J-27. **Do not autonomously retry J-22/J-23/J-24** — they remain externally Yahoo-429
data-walled and auto-heal only on operator confirmation of a reachable egress.
