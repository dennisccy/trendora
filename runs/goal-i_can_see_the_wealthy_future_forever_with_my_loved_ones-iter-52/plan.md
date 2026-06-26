# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-52 Execution Plan

Target journey: **J-109 only** (full depth). First iteration of the new J-109..J-112 cluster
queued by the `docs/goal.md` extension (commit ab7de8c). NOT a GOAL_ACHIEVED candidate
(J-110/J-111/J-112 remain unbuilt) — its flushed full suite is non-load-bearing this iter.

## What to Build

- All-horizon Factor Lab on the EXISTING `/research/factor-lab` route. Drop the single-horizon
  `<select>`; show every `config.walk_forward.horizons` horizon (1/5/10/20/60d) at once as
  **paired (forward-return, max-drawdown) columns** on BOTH the all-factors table and each
  factor's expandable decile sort.
- All-factors table cell per `(factor, horizon)` = that factor's **top-decile (D10)** cohort
  mean realized forward return + that cohort's mean `forward_returns.max_drawdown` (J-86),
  consistent with the existing top-decile risk-adjusted column.
- Expanded decile sort cell per `(factor, horizon, decile)` = that **decile's** mean realized
  return + mean max-drawdown, with per-decile `n` chip + factor range.
- Every figure read VERBATIM via the SAME `compute_factor_lab` / `_deciles` / `_rank_ic` /
  `_risk_adjusted` builders over stored `forward_returns` — each horizon column **byte-identical**
  to today's single-horizon `compute_factor_lab(factor, horizon)` for the same `(factor,horizon,decile)`.
  Decile membership per horizon = the EXISTING per-horizon factor sort (independent per horizon
  because the qualifying observation set differs per horizon). No decile boundary, return, or
  max-drawdown recomputed.
- Serve the all-horizons + paired-MDD shape from the SAME `GET /api/research/factor-lab` (`all=true`
  path), from its derived-once `EventStudyCache` + `_dataset_version` aggregate, with the cache
  **key extended via a folded schema token** so any pre-iter-52 cached row (old shape) is a MISS and
  is recomputed once WITH the paired-MDD columns. Reuse the existing `event_study_cache` table — NO
  new `table=True` model (the `test_db.py` expected-tables guard stays UNCHANGED).
- Keep the heavy read path bounded (J-105): one shared `yield_per`/column-projected streamed
  observation pass reading `realized_return` AND `max_drawdown` for ALL horizons in one sweep
  (pattern already exists in `_event_study_members_by_horizon`); ScannerResult ordered `(run_id, id)`.
  No unbounded `select(...).all()` over `ForwardReturn` or `ScannerResult`.
- Rank-IC + downside risk-adjusted figures REMAIN, now computed at the FIXED
  `config.walk_forward.default_horizon` (=20) and **relabelled with that horizon** — no longer a
  user selector. Horizon set sourced from config (no hardcoded `[1,5,10,20,60]` literal).
- Research Samples drill-down: every per-horizon `N=` chip drills into the exact
  `(factor, horizon, decile)` cohort without a 4xx, total == published n (J-51/J-65), in both
  As-of and All-history; NA where the return is NA; low-sample deciles show NA + n.

## Agents Required

- developer: yes
  - **Backend:** extend `_all_factor_observations` (and/or an all-horizons sibling) to carry
    `max_drawdown` per observation across all horizons in one streamed pass; add `mean_max_drawdown`
    to `_deciles`; rebuild `compute_factor_lab_all` into the all-horizons paired-MDD shape; fold a
    schema token into the `factor_lab_all_cached` cache key; relabel rank-IC/risk-adjusted at
    `default_horizon`; confirm `samples._factor_samples` serves every `(factor, horizon, decile)`.
  - **Frontend:** remove the horizon `<select>` from `FactorLabPage`/`HorizonSelector`; render the
    paired-column all-factors table + all-horizon expandable decile sort; extend `fetchFactorLabAll`
    + `FactorLabAllResponse` to the new shape; per-horizon NA-last sort (J-48 view transform);
    color-grade MDD via the existing `lib/mdd-color.ts` tokens; per-horizon `N=` chip → samples.
- reviewer / qa / browser-qa: yes (standard goal-mode pipeline; browser-QA is in-iteration).

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- `_factor_observations` + `_all_factor_observations` carry
  `max_drawdown`; `_deciles` adds `mean_max_drawdown`; `compute_factor_lab_all` → all-horizons paired
  shape; `factor_lab_all_cached` cache key gets folded schema token; `compute_factor_lab` deciles gain
  additive `mean_max_drawdown` (keeps the byte-identity reference + samples consistent).
- `apps/backend/app/api/research.py` -- `/research/factor-lab` `all=true` serves the new shape;
  rank-IC / risk-adjusted relabelled with `default_horizon` (no behavior change to validation/422/503).
- `apps/backend/app/engine/samples.py` -- confirm/extend `_factor_samples` `(factor, horizon, decile)`
  cohort drills count-coherently for every rendered chip across all horizons (As-of + All-history).
- `apps/frontend/lib/api.ts` -- `fetchFactorLabAll` + `FactorLabAllResponse` extended to the
  all-horizons + paired-MDD shape (per-factor per-horizon top-decile pair; per-decile per-horizon pair).
- `apps/frontend/app/research/_labs.tsx` -- `FactorLabPage` (drop horizon state/selector),
  `FactorsTable` / `FactorRows` / `DecileTable` (paired all-horizon columns + per-decile `n` + range),
  `FactorSortHeader` / sort keys (per-horizon NA-last); reuse `mdd-color` for MDD color grade.
- `apps/frontend/app/research/factor-lab/page.tsx` -- expected UNCHANGED (thin wrapper); verify only.
- `apps/backend/tests/test_factor_lab_all.py` -- new byte-identity (all-horizons vs single-horizon),
  cache schema-token MISS-then-populate against an already-populated old-schema row, paired-MDD shape.
- `apps/backend/tests/test_research_streaming.py` -- bounded/streamed cold-path serves the full live
  `forward_returns` without MemoryError (uncached cold probe).
- Touch as needed: `apps/backend/tests/test_research.py`, `test_api_research.py` (shape/relabel),
  any factor-lab frontend test (NA-last per-horizon sort).

## UI Evolution (Frontend Present: yes)

- New user-facing capability: compare every catalog factor's **top-decile forward-return edge AND
  its paired downside (max-drawdown) at all five horizons in one table**, then expand any factor to
  the full D1…D10 decile return/drawdown grid — without ever picking a horizon.
- New information displayed: five paired max-drawdown columns beside the five forward-return columns
  on both the all-factors table (top-decile cohort) and the per-factor decile sort (per-decile), at
  all `config.walk_forward.horizons` horizons.
- New user actions: sort any new per-horizon forward-return / max-drawdown column (NA-last); expand a
  factor row to its all-horizon decile sort; click a decile's per-horizon `N=` chip to drill into the
  exact `(factor, horizon, decile)` cohort. The horizon `<select>` is removed.
- UI surface changes: `/research/factor-lab` only — paired MDD columns at all horizons on the
  all-factors table; all-horizon paired columns on the expandable decile sort; horizon selector gone;
  Rank-IC / risk-adjusted figures relabelled with the fixed `default_horizon`.
- Navigation changes: none. Lands on the EXISTING Research home → `/research/factor-lab` route. No new
  page, no nav-skeleton change, no `blueprint.reapproval-requested` (IA unchanged; J-109 registered as
  an additive amendment to the existing "Factor-Lab analytics" Data Contract row).

## Visual Requirements (Frontend Present: yes)

- Component patterns: reuse the existing Factor Lab table primitives (`FactorsTable`, `DecileTable`,
  `FactorSortHeader`, `HorizonSelector`'s former slot now removed); existing `Select` only where still
  needed elsewhere on the page; per-decile `N=` chips as today.
- Layout: the established `/research/factor-lab` lab page layout under the Research hub; wider
  multi-column grid to fit five forward-return + five paired max-drawdown columns (allow horizontal
  scroll / compact cells rather than dropping columns).
- Key visual effects: color-grade the forward-return cells with the existing return tokens and the
  max-drawdown cells via `lib/mdd-color.ts` (design tokens only — no hardcoded hex); keep sort affordance
  + expand chevron affordances; preserve survivorship-bias / descriptive-evidence labels.
- States to handle: loading (no "Loading…"/skeleton frame must persist in evidence); empty / zero-N
  (honest NA + n, never a fabricated bucket); a horizon with insufficient post-D bars → NA forward-return
  AND NA max-drawdown; backend-unavailable surfaced honestly (no fabricated rows).

## Key Test Scenarios

- Browser (J-109, on a quiet warmed single-fetch backend; md5sum the evidence dir first; Playwright
  fallback pre-planned per the iter-39/40/42 CDP-empties-dir lesson):
  1. all-factors table renders the 11 catalog factors with five forward-return AND five paired
     max-drawdown columns at all horizons (no Loading/Backend-unavailable/skeleton frame).
  2. expand a factor → its D1…D10 decile sort shows the same all-horizon paired columns + per-decile `n`.
  3. sort a per-horizon column → byte-DISTINCT before/after frames (md5sum the pair; NA sinks last).
     NOTE: the all-factors table defaults DESCENDING — a "no reorder" FAIL on the first descending click
     is a test-plan expectation artifact, not a regression (confirm the J-48 comparator path first).
  4. a decile `N=` chip → `/research/samples` opens the exact `(factor, horizon, decile)` cohort,
     Total observations == chip n.
  5. toggle As-of vs All-history → N values change globally via the single top-bar date (0 native
     `input[type=date]` — J-18). Resolve all controls by `aria-label`, not visible text.
- Unit/integration: deep-equality byte-identity of each `(factor, horizon, decile)` all-horizons figure
  vs the single-horizon `compute_factor_lab` output (as-of, all-history, zero-N); extended EventStudyCache
  key yields MISS-then-populate against an ALREADY-POPULATED old-schema cache row (not a fresh compute);
  bounded/streamed read path serves the full live dataset with NO MemoryError (cold uncached probe);
  `test_no_magic_numbers` + `test_db.py::test_create_all_produces_expected_tables` (expected-tables guard
  UNCHANGED — no new table); samples count-coherence for the new `(factor, horizon, decile)` cohort.
- Error cases: horizon with insufficient post-D bars → NA return AND NA MDD (never fabricated);
  low-sample decile → NA + n; out-of-vocabulary samples cohort → honest 4xx (no fabricated row);
  cold uncached factor-lab fetch must NOT OOM on the ~3M-row live `forward_returns`.
- Required-still-passing journeys remain green: J-25, J-26, J-29, J-107, J-104, J-105, J-86, J-51,
  J-65, and the CRITICAL trio J-06 (single source) / J-18 (exactly one date control) / J-07 (Risk-Off → 0).
- Full pytest suite launched nohup-async via the pump (flush `0 failed, EXIT 0` owed before any future
  GOAL_ACHIEVED candidacy; NON-load-bearing this iter — do NOT block the evaluator on the in-flight suite;
  do NOT run it concurrently with the heavy-lab browser-QA probes).

## Scope Guards (no creep)

- OUT OF SCOPE: J-110 (`/research/regime-lab`), J-111 (`/research/phase-severity-lab`),
  J-112 (`/research/regime-phase-factor`) — deferred to iter-53/54/55 (one heavy lab per iter).
- No change to the canonical factor decile / rank-IC / risk-adjusted math; the `by_regime` slice stays
  a derived-once canonical value (already unrendered in this view since J-107).
- No new `table=True` model, no new endpoint, no new served field on `/api/stocks|themes|sectors|data`,
  no second date state, no re-trigger of the J-85 `kind:rebuild`.
- No order/execution path (research-only). The As-of toggle stays a MODE — exactly one date selector.
