# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-18
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `market-phase-card.tsx` — phase/P(bear) history timeline (SVG step-function) | New component | J-89: surface full history of market phase and bear-probability across snapshot dates | Scroll to the Market-Phase panel; confirm the SVG timeline renders with a phase-colored band, a bear-probability polyline, and a dashed as-of marker at the current date; confirm the swatch legend shows phase color names |
| `/` | `market-phase-card.tsx` — dated causal downtrend-episode list | New component | J-89: show when each downtrend causally began and whether it is still open at the selected date | On the live host (latest date) confirm the 2022 episode row shows a first-trigger date in early 2022, a severity value, and a "closed" badge; change as-of to 2022-10-07 and confirm the same episode shows "open" |
| `/` | `market-phase-card.tsx` — recovery-turn signal line | New component | J-90: show whether the resolved date is a causal recovery/turn signal with an explainable reason | On the latest date (Expansion, P(bear)≈0.003) confirm the callout reads "No recovery turn at this date" with the shield icon and muted colour; set as-of to 2023-02-02 and confirm the callout turns green with the up-arrow icon and shows the plain-language trigger reason |
| `/` | `market-phase-card.tsx` — fenced retrospective sub-view (Show/Hide toggle + dashed-border panel) | New component | J-89: provide hindsight full-sample smoothed P(bear) and true-bear dating, walled off from any causal path | Click the "Show" toggle on the retrospective panel; confirm the dashed-border panel appears, shows a smoothed P(bear) chart, and dates the 2022 bear (e.g. 2022-01-03 to 2022-10-12 with a drawdown figure); confirm the panel carries the "future-aware analysis only" disclosure text; click "Hide" and confirm the panel collapses |
| `/` | `market-phase-card.tsx` — loading skeleton on cold compute | Changed behavior | First computation of any date's timeline takes 30–55 s before caching | On a host with a freshly-cleared `MarketPhaseCache`, navigate to `/`; confirm a loading skeleton is displayed in the Market-Phase panel while the backend computes; confirm the timeline, episode list, and recovery-turn line appear once computation finishes |
| `/research` | `app/research/page.tsx` — RecoveryTurnEdgeLab section | New component | J-90: surface per-horizon forward-return edge of entering at recovery-turn dates | Scroll to the "Recovery-Turn Edge" section on `/research`; confirm it appears after the Regime×Setup×Pattern lab; confirm the disclosure line shows the number of signal dates (6 on the real host) and the best exit horizon; confirm each horizon row shows mean return, win rate, expectancy, mean MAE/MFE, aggregate max-drawdown, and a downside risk-adjusted figure |
| `/research` | `app/research/page.tsx` — Episodes/Pooled view toggle affecting RecoveryTurnEdgeLab | Changed behavior | J-90 lab shares the page-level Episodes/Pooled toggle (J-63) | Toggle from "Pooled" to "Episodes" and confirm the RecoveryTurnEdgeLab totals update (the by-signal-phase table n values change); toggle back and confirm values return to their prior state |
| `/research` | `app/research/page.tsx` — per-horizon edge table sortable column headers | New component | J-90: allow user to rank horizons by any metric | Click the "Mean return" column header in the horizon edge table; confirm rows reorder descending; click again and confirm ascending sort; confirm the sort indicator arrow toggles |
| `/research` | `app/research/page.tsx` — by-signal-phase conditioning table | New component | J-90: show edge breakdown by the market phase at each recovery-turn signal date | Confirm the by-signal-phase table shows at least two rows (e.g. "Pullback" and "Recovery"); click a column header to sort; confirm n values in this table sum to the total n in the horizon table for the same scope |
| `/research` | `app/research/page.tsx` — N= chips on RecoveryTurnEdgeLab rows | New component | J-90: provide count-coherent drill-down to the observations behind each edge figure | Click an "N=" chip in the horizon edge table on the "Episodes" view; confirm a new browser tab opens to `/research/samples` with the recovery-turn cohort; note the count shown on the samples page; confirm it matches the N value on the chip; repeat for the "Pooled" view and confirm the count also matches |
| `/research` | `app/research/page.tsx` — survivorship-bias label on RecoveryTurnEdgeLab | New component | J-90: honest disclosure about forward-return methodology | Confirm the survivorship-bias label appears below or within the RecoveryTurnEdgeLab section; confirm no order/execution affordance (buy/sell button) is present anywhere in this section |
| `/research/samples` | `app/research/samples/page.tsx` — recovery-turn cohort header | Changed behavior | J-90: describe the recovery-turn cohort when arriving from an N= chip on the RecoveryTurnEdgeLab | Open the samples drill-down via an N= chip from RecoveryTurnEdgeLab; confirm the cohort header reads "All recovery-turn dates" (or "Phase at signal: <label>" for a by-phase chip); confirm the qualifying columns show "Signal date", "Phase at signal", and "P(bear) at signal" for each row; confirm the total row count matches the N value on the originating chip |
| `/research/samples` | `lib/samples-link.ts` — recovery-turn cohort serialization | Changed behavior | J-90: serialize the recovery-turn cohort into the chip→drill-down link | Open drill-down in both "Episodes" and "Pooled" scope; confirm total in both cases equals the n published in the RecoveryTurnEdgeLab for those scopes; open a by-phase chip (e.g. N=482 for "Recovery") and confirm the total is 482 |
| `lib/api.ts` | `fetchMarketPhase(asof, signal, retrospective)` — updated signature + new response fields | Changed behavior | J-89/J-90: market-phase fetch now requests timeline, episodes, recovery-turn; optionally requests retrospective | Verify in browser DevTools Network tab that the Dashboard requests `GET /api/market-phase` without `?retrospective=true` on initial load; verify it sends `?retrospective=true` only after the user clicks the "Show" toggle on the retrospective sub-view |
| `lib/api.ts` | `fetchRecoveryTurnEdge` — new API client function + response types | New component | J-90: wire the Research page to the new `/api/research/recovery-turn-edge` endpoint | In browser DevTools Network tab confirm `GET /api/research/recovery-turn-edge` is called when the RecoveryTurnEdgeLab section first becomes visible; confirm the request changes when the Episodes/Pooled toggle or As-of/All-history mode changes |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/market_phase.py` — causal timeline series, episode dating, recovery-turn signal derivation, fenced retrospective backward-smoother and Bry-Boschan true-bear dater, `recovery_turn_dates` accessor, `retrospective_cached` — all wired to the Dashboard Market-Phase panel via `GET /api/market-phase`; no backend-only residue.
- `apps/backend/app/engine/research.py` — `compute_recovery_turn_edge` and `_recovery_turn_observation_set` — wired to the RecoveryTurnEdgeLab via `GET /api/research/recovery-turn-edge`; no backend-only residue.
- `apps/backend/app/engine/samples.py` — `KIND_RECOVERY_TURN` and `_recovery_turn_samples` — wired to the samples drill-down via `GET /api/research/samples`; no backend-only residue.
- `apps/backend/app/config.py` + `config.yaml` — five new `MarketPhaseCfg` keys (`downtrend_pbear_threshold`, `recovery_signal_pbear_exit`, `recovery_trailing_ma_days`, `bry_boschan_min_phase_days`, `bry_boschan_min_amplitude_pct`) — validated at startup; govern the behaviour of the above engine functions; no direct UI surface but affect computed values users see.
- `apps/backend/tests/test_market_phase.py`, `test_research.py`, `test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py`, `test_no_magic_numbers.py` — test-only files; no UI impact.

---

## Summary

- **Frontend surfaces changed:** 6 distinct components / elements across 3 routes
- **New pages/routes:** 0 (all changes on existing routes `/`, `/research`, `/research/samples`)
- **Modified components:** 5 (`market-phase-card.tsx`, `app/research/page.tsx`, `app/research/samples/page.tsx`, `lib/api.ts`, `lib/samples-link.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 0 (every new backend capability is wired to a visible UI surface); 5 test/config file groups changed with no UI surface impact
