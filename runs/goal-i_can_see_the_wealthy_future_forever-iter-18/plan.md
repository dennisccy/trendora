# goal-i_can_see_the_wealthy_future_forever-iter-18 Execution Plan

**Goal alignment:** Delivers **J-26** (must-have journey, `docs/goal.md`) at its re-scoped bar — the
Factor-Lab multi-factor **Combined** cohort becomes a **non-empty composite percentile-rank blend** of the
selected factors (config-weighted, top config-quantile), scaling to **all catalog factors**, with the old
strict AND-intersection demoted to a clearly-labelled secondary **Strict overlap (AND)** column. Matches Key
Capability 27, the "multi-factor composite cohorts — a rank-blend across any number of factors" canonical
value, and the anti-goal that *blesses* this transparent rank-blend as descriptive grouping (NOT a fitted/ML
model). **No drift / no scope creep** — this refines an EXISTING Data-Contract value (same module
`compute_factor_combination`, same endpoint `GET /api/research/factor-combination`); no new endpoint, page,
route, nav entry, or date state.

**Already in place (verify, do NOT recreate):** the strict-AND implementation (`research.py:477-510`), the
`combination` config block, `CombinationCfg`, and the frontend `CombinationLab`/`CombinationTable` all exist
and work. The blueprint reapproval marker is **consumed/absent** — `run-goal.sh` does NOT pause; do not
author a `blueprint.reapproval-requested`. The blueprint's J-26 Data-Contract row is edited additively
(composite replaces strict-AND headline + secondary strict-overlap) — no new contract value.

## What to Build

- **Composite rank-blend cohort (the headline fix)** in `app.engine.research:compute_factor_combination`.
  Over the SAME read-only `_combination_observations` pool (each obs already carries every referenced
  factor's stored value, read verbatim — no recompute), for **each condition** (catalog factor + `top`/
  `bottom` side):
  1. Percentile rank of that condition's factor value within the pool — **REUSE `_average_ranks`**, divide
     by `n` → fraction in (0, 1].
  2. **Orient by side:** `top` → rank-fraction as-is; `bottom` → `1 − rank-fraction`. (User `side` orients
     the blend, exactly like the single-condition cohorts; catalog `direction`/`family` stay descriptive
     metadata and never flip the sort.)
  3. **Composite score** per obs = **config-weighted mean** of the oriented ranks across conditions (default
     **equal-weight** = each condition `1/k`, weights normalized to sum to 1 — the scheme + default weight
     come from config; the only in-code arithmetic is normalization, not a `1/k` threshold literal).
  4. **Composite cohort** = top **config-quantile** of the pool by composite score — **REUSE
     `_quantile_cutoff`** on the sorted composite scores: members = obs with `composite ≥ cutoff(1 −
     composite_fraction)`, boundary ties included. For a sensible selection this is **non-empty
     (≈ `composite_fraction · pool_n`) and clears `walk_forward.min_sample` (30)**.
  - Note a CONDITION (factor+side) — not a distinct factor — contributes a rank; a factor used in two
    conditions (the opposing-extremes fixture) contributes two oriented ranks.
- **Keep strict-AND as a secondary cohort.** Retain the existing `combined_members &= members`
  AND-intersection as a separate `strict_overlap` cohort (label "Strict overlap (AND)") — **NA + n when
  empty**, never a fabricated 0.
- **Payload reshape (clean rename, no back-compat alias).** Keep `baseline` + `singles[]` unchanged. The old
  `combined` key is **removed**; the headline becomes `composite` (label "Combined (composite rank-blend)")
  and the new `strict_overlap` rides the same payload. Both reuse `_cohort_stats` → downside-only
  `_risk_adjusted` (NA when no downside / n<2 — never total vol). **Echo** the resolved composite quantile
  (`{key,label,fraction}`) + weighting scheme so the UI labels the blend honestly. Update ALL references to
  the old `combined` key (engine, API, tests, frontend) — no dead code.
- **Scale to all factors.** Algorithm accepts up to all catalog factors with no code cap; the only cap is
  `comb.max_conditions` (config).
- **Config (`config.yaml` → `research.factor_lab.combination`):** add a `composite` sub-block —
  `quantile` (a real `quantiles` key, e.g. `quintile`) + `weighting` (scheme `equal` + a `default_weight`
  `> 0`). **Raise `max_conditions: 3 → 11`** (= the 11 catalog factors), config-driven. Keep `quantiles`,
  `default_conditions`, `min_conditions` as-is.
- **Config typing (`apps/backend/app/config.py`):** add a typed `CompositeCfg` on `CombinationCfg`; validate
  at boot (loud `ConfigError`): `composite.quantile` MUST be a real `quantiles` key; weighting scheme valid +
  default weight `> 0`. Keep the existing `1 ≤ min ≤ max`, unique-quantile-key, and default-condition
  cross-checks. **`config-fixtures-need-new-required-keys`:** if `composite` is required, add it to ALL
  inline test config dicts building a `CombinationCfg`/`FactorLabCfg` (not just the obvious one).
- **API (`apps/backend/app/api/research.py:factor_combination`):** signature UNCHANGED (`condition`
  repeatable + `horizon`); composite + strict_overlap ride the same payload. Raising `max_conditions`
  auto-lets the existing count-validation accept up to all catalog factors. **Add NO `as_of` param** (J-32 is
  iter-19; J-18 — zero date state).
- **Frontend (`research/page.tsx` + `lib/api.ts`):** render `composite` as the primary emphasized "Combined"
  row and `strict_overlap` as a secondary labelled row (NA + n via `CohortCell`/`SampleSize`); row order
  Baseline → singles → **Combined (composite)** → **Strict overlap (AND)**. Update the section hint text
  (composite rank-blend, non-empty, top config-quantile, config-weighted equal; strict-overlap = optional
  secondary). Confirm the payload-driven add/remove cap now allows up to all catalog factors (no hard-coded
  UI cap). Update `FactorCombinationResponse` to carry `composite` + `strict_overlap` (replacing `combined`)
  + the echoed composite-quantile/weighting metadata. Re-format only — never compute a cohort client-side.
  **Add NO date/as-of state.**

## Agents Required

- developer: **yes** — backend (composite blend + strict_overlap demotion + payload rename + `CompositeCfg`
  + config + tests) and frontend (composite/strict-overlap rows + hint + type update).
- backend-data: **yes**
- frontend-ux: **yes**

Frontend Present: yes

## Files to Create/Modify

**Backend**
- `apps/backend/app/engine/research.py` — `compute_factor_combination`: add the composite rank-blend cohort
  (reusing `_average_ranks` + `_quantile_cutoff` + `_cohort_stats`/`_risk_adjusted`), demote strict-AND to
  `strict_overlap`, reshape payload (`combined` → `composite` + `strict_overlap` + echoed quantile/weighting).
  Add a source comment: the composite is a deterministic rank-blend of STORED values (like the J-25 decile
  sort) — recomputes no factor/return, NOT a fitted/ML model.
- `config.yaml` — `research.factor_lab.combination`: add `composite` sub-block; `max_conditions: 3 → 11`.
- `apps/backend/app/config.py` — add `CompositeCfg`; wire onto `CombinationCfg` + boot validation.
- `apps/backend/app/api/research.py` — `factor_combination`: no signature change; verify it passes the new
  payload through; update any `combined` doc/var reference.
- `apps/backend/tests/test_research.py` & `tests/test_api_research.py` — update every `combined` reference to
  `composite`/`strict_overlap`; add/extend the tests in Key Test Scenarios.

**Frontend**
- `apps/frontend/lib/api.ts` — `FactorCombinationResponse`: `composite` + `strict_overlap` (drop `combined`)
  + composite-quantile/weighting echo fields.
- `apps/frontend/app/research/page.tsx` — `CombinationTable` (row order + secondary strict-overlap row +
  emphasis) and `CombinationLab` (hint text); confirm add/remove cap is payload-driven.

## UI Evolution

- **New user-facing capability:** on `/research` → Factor Lab → "Multi-factor combination cohort", combine
  **2 up to all 11 catalog factors** and read a **Combined (composite rank-blend)** cohort that is actually
  populated (mean/median/hit-rate/downside-risk-adjusted/n) beside Baseline, each single, and a secondary
  **Strict overlap (AND)** column — so "does combining beat either alone?" is answerable instead of NA.
- **New information displayed:** a populated **Combined (composite)** row (non-empty for a sensible
  selection); a secondary **Strict overlap (AND)** row (honest NA + n when empty); the composite quantile +
  equal-weight labelling shown for transparency; survivorship-bias + descriptive-not-predictive labels persist.
- **New user actions:** add/remove combination conditions up to all catalog factors (existing add/remove
  control; cap raised via config). No new control type; **no date control**.
- **UI surface changes:** the existing "Multi-factor combination cohort" section on `/research`. No new page,
  route, or nav entry.
- **Navigation changes:** none.

## Visual Requirements

- **Component patterns:** reuse the existing `Card` + `PanelTitle` section, the combination `<table>`
  (`data-testid="combination-table"`), and `CohortCell`/`SampleSize` for NA + n. No new component types.
- **Layout:** unchanged Factor-Lab page layout; the combination table keeps Cohort / n / Mean / Median /
  Hit-rate / Risk-adjusted (downside) columns; rows Baseline → singles → **Combined (composite)** (emphasized
  `bg-surface-2`, semibold) → **Strict overlap (AND)** (secondary, muted).
- **Key visual effects:** dense dark analytical table; monospace tabular-nums for all figures; green/red
  return grading via palette tokens only; the composite row emphasized over the secondary strict-overlap row.
- **States to handle:** loading (existing `CombinationSkeleton`/dim), backend-unavailable (existing error
  card — no fabricated cohorts), empty pool (`pool_n === 0` EmptyState), and per-cell NA + n for any
  low-sample/empty cohort (composite populated while strict-overlap shows NA in the same view).

## Key Test Scenarios

**Browser (J-26 on `/research`, exclusive Chrome — serialize, de-dup evidence by sha256):**
- Default load → Combination Lab: **Combined (composite)** row populated (n ≥ 30; numeric
  mean/median/hit-rate/risk-adjusted via DOM), distinct from Baseline; **Strict overlap (AND)** row renders.
- Add conditions up to (near) all catalog factors → composite stays non-empty (DOM-assert n > 0).
- Drive an **empty-strict-overlap** selection (opposing-extremes / many-factor) → **composite populated AND
  strict-overlap = NA + n** in the same shot (membership-driven NA per the iter-11 lesson, never horizon).
- **J-18 re-verify:** toggle the global as-of in-app (not hard reload) → lab byte-identical (distinct sha256
  before/after + network spy showing **zero `/api/research/*?as_of=` requests**); exactly one date `<select>`
  on the page (none added on `/research`). Per `react-controlled-select-needs-native-setter`, drive selects
  via native-setter + bubbling change event and assert live DOM.
- Spot-check J-25 / J-27 / J-30 still render and re-point above the Combination Lab.

**Unit/integration (backend `tests/test_research.py` + `tests/test_api_research.py`, run pytest ONCE):**
- **Composite non-empty + clears `min_sample`** for the default conditions (`composite.stats.n ≥ min_sample`
  and `> 0`) — the headline fix.
- **Scales to all factors:** a selection up to `max_conditions` (≈ all 11) returns a non-empty composite.
- **Orientation correctness:** on a monotone fixture, `top`-side composite selects high-factor names and
  `bottom`-side selects low-factor names.
- **Strict overlap retained + honest NA:** extend `test_combination_opposing_extremes_empty_cohort_is_na_not_zero`
  → `strict_overlap` n=0/NA **AND** `composite` non-empty on the exact fixture that used to be 0/NA.
- **Read-only keystone:** extend `test_combination_is_read_only_no_scoring_or_return_or_pattern_call`
  (patch-to-raise) so the composite path triggers no
  `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime`.
- **Downside-only risk-adjusted:** composite/strict `risk_adjusted` = `mean / downside_deviation` (NA when no
  downside / n<2) — never total vol.
- **Cohort algebra:** `composite ⊆ baseline`; `strict_overlap ⊆ each single`; `baseline.n == pool_n`.
- **No magic numbers:** `test_no_magic_numbers` still passes (no decile/quantile/weight/cap literal in
  `research.py`).
- **Config validation (boot `ConfigError`):** `composite.quantile` not a real `quantiles` key → raises;
  invalid weighting → raises; existing min/max, unique-quantile, default-condition cross-checks still raise.
- **Config-driven cohort size:** changing `composite.quantile` re-points the composite `n` (proves the
  fraction is config-sourced, not hard-coded).
- **Error cases:** unknown factor/side/quantile + out-of-range condition count → `422` (now exercised up to
  the raised cap); invalid horizon → `422`; no-price-data → `503`.

**Regression / anti-goal guards (no DB regen):**
- Frontend `npm run build` typechecks. Full backend pytest green.
- Git-verify the diff does NOT touch `scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/
  `forward_testing.py` math or the snapshot/serving path — **J-06/J-07 byte-identical, no DB re-bootstrap**.
- Verify in source (not the QA table — `status.json` lands at the phase-namespace path and an `-audit.md` is
  often absent): the read-only seam, the composite-non-empty invariant, and zero `as_of`/date state on
  `/research`.

## Assumptions (documented, not blocking)

- **Config `composite` shape:** `quantile: quintile` + `weighting: equal` + `default_weight: 1.0` (>0);
  equal-weight = each condition's normalized weight `default_weight / Σ`. Developer may refine the exact key
  names provided (a) every tunable is config-sourced and (b) boot validation rejects a bad `quantile`/scheme.
- **`max_conditions: 11`** = the current catalog factor count; if the catalog grows, this stays config-driven.
- **Out of scope (excluded per spec):** J-32 / any `as_of`/date state on `/research` (iter-19); J-22/J-23/J-24
  (Yahoo-429 data-walled, non-halting — do not re-probe); request-level custom per-condition weights
  (config equal-weight default is the must); boolean pattern-flag conditions; return/MAE in the combination.

## Handoff

- Dev handoff: `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-18-dev.md` (note the composite is
  a deterministic rank-blend of stored values — NOT a recomputation or a fitted/ML model — so the
  reviewer/auditor/coherence-auditor do not mistake it).
