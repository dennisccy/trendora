# goal-i_can_see_the_wealthy_future_forever-iter-12 Execution Plan

**Target journey:** J-26 — Factor Lab multi-factor combination cohorts.
**Depth:** full. **Type:** additive read-only extension of the proven `/research` Factor-Lab seam
(J-25 decile/IC iter-10, J-27 regime split iter-11). No nav change, no blueprint re-approval — the
blueprint was already updated additively by the decomposer (IA row 78, journey-home row 108,
Data-Contract row 170). New endpoint serves a NEW value, not a duplicate.

## What to Build

- **`compute_factor_combination(session, conditions, horizon, config) -> dict`** in
  `app/engine/research.py` — the SINGLE canonical multi-factor combination read (read-only):
  - `_combination_observations(session, factors, horizon)` mirroring `_factor_observations`: SELECT
    `ForwardReturn` at `horizon` ⋈ `ScannerResult`, read each referenced factor's stored value via the
    existing `_extract_factor_value` + `parse_factor_source` (VERBATIM). Keep an obs only when a realized
    return exists **AND every referenced factor is non-null** (any NULL excludes it — never fabricated).
    Each obs = `{run_id, ticker, return, values: {factor_key: float}}`.
  - Deterministic, tie-tolerant **empirical quantile cutoff** per condition over the shared pool's values
    for that factor (nearest-rank on sorted values). `side: top` ⇒ `value >= cutoff(1 − fraction)`;
    `side: bottom` ⇒ `value <= cutoff(fraction)`. Boundary ties **included** (documented in docstring;
    a fixed statistical rule, NOT a tunable → no magic number — only `fraction` is config).
  - Cohorts: `baseline` = whole pool; one `single` per condition; `combined` = **exact set-intersection
    (AND)** of all single memberships.
  - Per-cohort `CohortStats`: `mean_return` (`statistics.mean`), `median_return` (`statistics.median`),
    `hit_rate` (fraction `> 0`), `risk_adjusted` (**REUSE** the existing downside-only `_risk_adjusted` —
    never total vol), `n`, `low_sample` (`n < walk_forward.min_sample`). Empty cohort ⇒ stats `None` (NA).
  - Payload: resolved `conditions` (each `{factor:{key,label,family,direction,source}, side,
    quantile:{key,label,fraction}}`), `horizon`, `horizons`, `default_horizon`, `min_sample`,
    `min_conditions`, `max_conditions`, the config-driven `factors` catalog (reuse `factor_catalog`), the
    config-driven `quantiles` list, `survivorship_bias` (reuse `SURVIVORSHIP_BIAS_LABEL`),
    `descriptive_caveat` (reuse `RESEARCH_CAVEAT`), `pool_n`, `baseline {label, stats}`,
    `singles [{condition, stats}, …]`, `combined {label, stats}`. `ValueError` on unknown
    factor/side/quantile or out-of-range condition count.
  - **SELECT-only**; calls NO `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/
    `score_regime`. Recomputes no factor and no return.
- **`GET /api/research/factor-combination`** in `app/api/research.py` — serve
  `compute_factor_combination(...)` verbatim. Params: `condition` (repeatable
  `"<factor_key>:<side>:<quantile_key>"`), `horizon` (optional int). Empty `condition` →
  `config.research.factor_lab.combination.default_conditions`. Validate count ∈ [min,max], each
  `factor_key ∈ factor_catalog`, `side ∈ {top,bottom}`, `quantile_key ∈` config quantiles, `horizon ∈
  walk_forward.horizons` → **422**; **503** when no price data (mirror the `factor-lab` route). NO
  as-of/date param (J-18).
- **`config.yaml` → `research.factor_lab.combination`** block: `min_conditions: 2`, `max_conditions: 3`,
  `quantiles:` ordered `{key,label,fraction}` list (e.g. quintile 0.20 / quartile 0.25 / tertile 0.3333 /
  half 0.50), `default_conditions:` the canonical 2-condition default (e.g. `rs_spy_3m top quintile`,
  `atr_pct bottom tertile`). Low-sample threshold **reused** from `walk_forward.min_sample` (no new one).
- **`config.py`** — type + boot-validate: extend `FactorLabCfg` (`extra="allow"`) with a typed
  `combination: CombinationCfg` (+ `QuantileOption`/`DefaultCondition` sub-models). Validate
  `1 <= min_conditions <= max_conditions`; every `quantiles[*].fraction ∈ (0,1)`; quantile `key` unique;
  every `default_conditions[*]` references a real sibling `factors` key + a real `quantiles` key +
  `side ∈ {top,bottom}`; `min_conditions <= len(default_conditions) <= max_conditions`. Invalid block ⇒
  `ConfigError` at boot — never a silent default (mirror `FactorLabCfg._validate` /
  `_factor_lab_sources_resolve`; the factor-key cross-check sits in `FactorLabCfg._validate`, which can
  see both `factors` and `combination`).
- **Frontend `lib/api.ts`** — add `FactorCombinationCondition`, `QuantileOption`, `CohortStats`,
  `FactorCombinationResponse` types + `fetchFactorCombination(conditions, horizon, signal)` (repeated
  `condition=<factor>:<side>:<quantile>` query params; throws non-200 → explicit "Backend unavailable").
- **Frontend `app/research/page.tsx`** — additive "Multi-factor combination cohort" section BELOW the
  existing `RegimeEffectivenessTable`. (Details under UI Evolution / Visual Requirements.)

## Agents Required

- developer: **yes** — backend (engine + API + config + config typing) and frontend (api types + page
  section) plus unit/integration tests. Single full-depth iteration.
- backend-data: **yes**  ·  frontend-ux: **yes**

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/engine/research.py` — **modify.** Add `_combination_observations`, a quantile-cutoff
  helper, and `compute_factor_combination`. Reuse `_extract_factor_value`/`parse_factor_source`/
  `_risk_adjusted`/`_downside_deviation`/`factor_catalog`/`SURVIVORSHIP_BIAS_LABEL`/`RESEARCH_CAVEAT`.
- `apps/backend/app/api/research.py` — **modify.** Add the `GET /research/factor-combination` route +
  condition/horizon validation (422/503). Leave `factor-lab` untouched.
- `config.yaml` — **modify.** Add `research.factor_lab.combination` (min/max conditions, quantiles,
  default_conditions). No edit to any existing tunable.
- `apps/backend/app/config.py` — **modify.** Add `CombinationCfg` (+ sub-models); add `combination` to
  `FactorLabCfg`; extend `FactorLabCfg._validate`.
- `apps/frontend/lib/api.ts` — **modify.** New combination types + `fetchFactorCombination`.
- `apps/frontend/app/research/page.tsx` — **modify.** New combination section + condition-row controls.
- `apps/backend/tests/test_research.py` — **modify.** New J-26 unit/integration tests (see scenarios).
- `apps/backend/tests/test_api_research.py` — **modify.** New-endpoint API cases (422/503; J-18 no-date).
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-12-dev.md` — **create.** Dev handoff.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** compose a 2–3 condition multi-factor cohort on the Factor Lab and see
  whether **combining** factors beats the **baseline** and **each single factor** — mean, median,
  hit-rate, downside-risk-adjusted return, and `n`, with honest NA on thin combined cohorts.
- **New information displayed:** a "Multi-factor combination cohort" comparison table — Baseline vs each
  single-condition cohort vs the Combined (AND) cohort, each with n / mean / median / hit-rate /
  downside-risk-adjusted forward return at the selected horizon.
- **New user actions:** pick factor + side (Top/Bottom) + quantile per condition; **+ Add condition**
  (disabled at `max_conditions`); per-row **remove** (disabled at `min_conditions`); change the shared
  horizon — all re-point the combination table.
- **UI surface changes:** ONE additive section appended to the existing `/research` Factor Lab page.
- **Navigation changes:** none — no new page, route, or sidebar entry (J-18 / blueprint preserved).

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** reuse `Card` + `PanelTitle` for the section; `Select` for Factor and Quantile;
  the existing Top/Bottom toggle styled like `HorizonSelector`'s segmented control; a comparison
  `<table>` styled exactly like `DecileTable`/`RegimeEffectivenessTable`; reuse `SampleSize` for `n` and
  the `DecileValue`/`RegimeCell` NA treatment for null/low-sample cells (`fmtPct` for returns/hit-rate,
  `fmtRatio` for the risk-adjusted column).
- **Layout:** full-width section below the regime table; condition-row controls in a compact wrapped row;
  comparison table horizontally scrollable on mobile (existing `overflow-x-auto` pattern). Numbers
  monospace/tabular (`num`). Dark analytical workstation tokens only.
- **Key visual effects:** colour-graded returns via `returnClass`; warn-token NA chips; reuse the page
  `CaveatBanner` (survivorship + descriptive). Add a short honest note that **return/MAE is not yet
  available** (arrives with the event-study lab, J-29) so the single downside risk-adjusted column is not
  silently read as "all" risk measures.
- **States to handle:** loading skeleton; "Backend unavailable" error card (existing pattern); empty-pool
  state (`pool_n === 0`) renders an honest empty message; low-sample/empty cohort cells render **NA + n**,
  never a fabricated number. Config-driven option lists come **from the payload** — no hard-coded factor
  or quantile list in the frontend.

## Key Test Scenarios

- **Read-only keystone (critical):** extend the existing `test_factor_lab_is_read_only_...` discipline so
  monkeypatching `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime` to raise does NOT
  break `compute_factor_combination` (SELECT + pure-group only).
- **Cohort algebra:** on a controlled fixture, `combined` membership == exact set-intersection of single
  memberships; `baseline.n == pool_n`; each `single.n <= pool_n`; `combined.n <= min(single.n)`.
- **Stats correctness:** mean / median / hit-rate exact on a known fixture; `risk_adjusted` == downside-
  only `_risk_adjusted` of the membership, and `None` for an all-non-negative or `n<2` cohort.
- **Honest NA:** a deliberately thin combined cohort (two opposing/near-orthogonal extremes → `n <
  min_sample`) ⇒ `low_sample: true` and the UI renders NA + n; an empty cohort ⇒ stats `None`, never 0.
- **Pool honesty:** an observation NULL in any referenced factor is excluded → `pool_n` ≤ each single
  factor's `_factor_observations` n. **Do NOT** assert equality to
  `compute_forward_aggregates.overall.mean` (the AND pool is a strict subset — iter-2 lesson).
- **No magic numbers:** `min/max_conditions`, `quantiles`, `default_conditions` read from config;
  `test_no_magic_numbers` (scanning `research.py`) still passes (the cutoff method uses only structural
  math + config fractions, no new literal in calc code).
- **Error / config cases:** unknown factor/side/quantile or out-of-range count → `ValueError` (engine) /
  **422** (API); `horizon ∉ walk_forward.horizons` → 422; no price data → 503; invalid `combination`
  config (min>max, fraction ∉ (0,1), duplicate quantile key, default referencing an unknown
  factor/quantile, or count outside [min,max]) → **ConfigError at boot**.
- **Browser (browser-qa-agent, serialized with qa on shared Chrome; de-dup shots by sha256):**
  - **J-26:** `/research` renders the default 2-condition section (Baseline + 2 single + Combined rows,
    each n/mean/median/hit-rate/risk-adjusted). Change a condition → fresh
    `GET /api/research/factor-combination?...` fires + DOM matches API (distinct before/after shots +
    observed network). Add a 3rd condition → 3 single rows + Combined, with `Combined n ≤ each single n ≤
    pool`. Drive the NA fixture (opposing extremes) → capture the **NA + n** Combined cell.
  - **J-18 (principal regression risk):** with the new section present, toggle the global as-of date and
    assert the decile table, rank-IC, regime table **and the new combination table** are byte-identical
    with **zero** `as_of`-param requests (extend the iter-11 UT-08 check to the new table).
  - **J-25 / J-27 (regression):** decile table + rank-IC + regime table still render and re-point on
    factor/horizon change.
- **Suite:** full backend `pytest` runs **once** (~14 min, heavy walk-forward boot — do not run two
  pytest invocations concurrently); frontend `npm run build` typechecks.

## Notes / Scope Discipline

- **Diff must be additive.** No change to `scoring.py`/`forward_testing.py`/`scanner.py`/`patterns.py`/
  `regime.py`/`snapshot_serving.py`/the as-of provider/`backtest/page.tsx`/any existing endpoint or the
  `factor-lab` route. The single-factor decile/IC/regime value keeps its canonical home
  (`compute_factor_lab` / `GET /api/research/factor-lab`).
- **Deliberate, documented scope (not drift):** J-26's goal text mentions "return/vol, return/MAE", but
  the **anti-goals forbid total volatility** and **return/MAE needs the post-snapshot excursion path that
  is J-29's deliverable**. This iteration therefore ships the established **downside-deviation**
  risk-adjusted column (reusing `_risk_adjusted`) and the UI states return/MAE arrives with J-29 — the
  correct anti-goal-compliant reading. Boolean pattern-flag conditions (the "… AND VCP-flagged" example)
  are out of scope this iteration (acceptance is quantile-cohort-based); leave the condition model
  extensible.
- **Coherence:** the new value is registered in the Data Contract (blueprint row 170) with ONE computing
  module + ONE serving endpoint; no existing contract value is recomputed or served from a new path; no
  duplicate home. Expect COHERENCE-PASS.
- **Process expectation (evaluator):** per the iter-10/11 pattern this full-depth iter likely produces no
  `-audit.md` and writes `status.json` at the phase-namespace path
  `runs/goal-i_can_see_the_wealthy_future_forever-iter-12/status.json`. Verify the read-only /
  downside-only / no-magic-numbers seams **in source**; do not block on a missing audit/status artifact.
- **GOAL_ACHIEVED is not autonomously reachable** while J-22/J-23/J-24 stay externally Yahoo-429
  data-walled — **do NOT autonomously fetch, probe, or retry them.** Autonomous runway after J-26:
  J-30 → J-29 → J-31.
