# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Date:** 2026-06-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|---------------------|-------------|-------------|--------------|
| `/` | `MarketPhaseCard` (new card in Dashboard grid) | New component | J-87: add market phase + severity panel to Dashboard | Load the Dashboard; confirm a card titled "Market Phase & Severity" appears below the "Major indexes & regime" card with a phase label badge (e.g., "Expansion") and a severity number (e.g., "28.75 / 100 severity") in the body |
| `/` | `MarketPhaseCard` — phase Badge in header | New component | J-87: phase label colored by stress posture | Check that the phase Badge in the card header is green for Expansion/Recovery, amber for Pullback, and red for Correction/Bear; use as-of navigation to reach a 2022 date and confirm the badge turns red with label "Bear" |
| `/` | `MarketPhaseCard` — severity headline + drawdown/off-trough metrics | New component | J-87: 0–100 severity score with cycle leg figures | On the Dashboard (latest date), confirm the body shows a numeric severity score, a "Drawdown" percentage, and an "Off trough" percentage; all three must be numeric, not "NA" |
| `/` | `MarketPhaseCard` — `SeverityBreakdown` three-column table | New component | J-87: explainable named component breakdown (never a bare number) | Confirm the breakdown table lists exactly five rows (Drawdown depth, Time underwater, Market regime (stored), Breadth below 200-DMA, VIX stress gate) each with a numeric Value and a numeric Contribution column |
| `/` | `MarketPhaseCard` — `PBearBadge` in header | New component | J-88: 0–1 deterministic P(bear) badge | With the latest date loaded, confirm the header shows a "P(bear) 0.00" badge (green); navigate the global as-of to 2022-10-07 and confirm the badge changes to red with a value near "P(bear) 1.00" |
| `/` | `MarketPhaseCard` — `ObservationVector` chips | New component | J-88: filter observation vector disclosed so P(bear) is never opaque | Confirm the bottom of the card shows a row of dated chips labeled "Filter observations · drives P(bear)"; hover a chip and verify its tooltip shows a stress value and a per-date P(bear) reading |
| `/` | `MarketPhaseCard` — loading skeleton state | New component | J-87/J-88: panel must show placeholder while backend computes | On a cold first load or a slow connection, confirm the card body shows an animated gray skeleton block (height ~176px) rather than blank space or a flash of fabricated data |
| `/` | `MarketPhaseCard` — NA/partial empty state | New component | J-87/J-88: insufficient-history dates must never show fabricated data | Set the global as-of to a very early date with few bars (e.g., before the seed window); confirm the card body shows "Not enough history to derive a market phase for this date" with a minimum-bar count, and no numeric severity or probability |
| `/` | `MarketPhaseCard` — error state | New component | J-87/J-88: backend-unreachable must show styled alert, not blank | With the backend stopped, reload the Dashboard; confirm the card body shows the amber warning box containing "Market phase unavailable" and the message "confirm the backend is running and reload" |
| `/` | `MarketPhaseCard` — as-of repoint (J-18 coherence) | New component | Panel must reuse the single global as-of, add no second date control | Confirm no additional date picker or date input appears inside the Market Phase card; change the global as-of via the existing Dashboard controls and verify the card body updates to the new date without a page reload |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — new `MarketPhaseCfg` + `RegimeSwitchingCfg` typed/validated models and constants; consumed by the backend engine only; no UI surface change beyond powering the new endpoint.
- `config.yaml` — new `market_phase:` + `regime_switching:` sections (weights, edges, thresholds, transition matrix, emission params); parameter tuning only; no UI surface change.
- `apps/backend/app/engine/market_phase.py` — new causal derivation engine (phase + severity + filtered P(bear)); server-side only; powers the endpoint but produces no direct UI change itself.
- `apps/backend/app/api/market_phase.py` — new `GET /api/market-phase?as_of=…` router; backend API; consumed by `MarketPhaseCard` (wired, not orphaned).
- `apps/backend/main.py` — router registration for `market_phase`; infrastructure change; no UI surface change.
- `apps/backend/app/models.py` — new `MarketPhaseCache` table; backend performance cache; no UI surface change.
- `apps/backend/tests/test_market_phase.py` — 27 new backend unit/integration tests; test-only; no UI surface change.
- `apps/backend/tests/test_no_magic_numbers.py` — added `market_phase.py` to `CALC_FILES`; test-only; no UI surface change.
- `apps/backend/tests/test_db.py` — registered `market_phase_cache` in expected-tables set; test-only; no UI surface change.
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py` — updated inline config fixtures to include the two new required sections; test-only; no UI surface change.

---

## Summary

- **Frontend surfaces changed:** 1 (Dashboard `/`)
- **New pages/routes:** 0
- **Modified components:** 1 (`app/page.tsx` — mounts the new card)
- **New components:** 1 (`components/market-phase-card.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 11
