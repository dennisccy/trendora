# goal-i_can_see_the_wealthy_future_forever-iter-13 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built (UI)

- **Factor dropdown grouped by family (`/research` Factor Lab).** The single Factor selector on the
  Research — Factor Lab page now groups its options under native `<optgroup>` headings keyed off each
  factor's `family` (e.g. **Score**, **Momentum**, **Trend**, **Volatility**). With iter-13's three new
  volatility factors added to the config-driven catalog, the **Volatility** group now lists all four
  measures together — **ATR % (volatility level)**, **Historical volatility (HV)**, **Volatility
  contraction (VCP-style)**, and **Downside volatility (semivol)** — so J-30 step 1 ("select the
  volatility family and view each measure") is obvious at a glance.
- This is **purely presentational**: the groups are derived from `data.factors` in the payload (no
  hard-coded factor or family list in the frontend), option **values are unchanged**, and selecting any
  option fetches and renders its existing decile table (raw mean + downside-risk-adjusted), rank-IC, and
  by-regime split through the unchanged `FactorLab` component. No recompute, no new value, no new state.

## Files Changed

- `apps/frontend/app/research/page.tsx` — `FactorSelector` now renders `<optgroup>` groups via two new
  pure helpers (`groupByFamily`, `familyLabel`); first-appearance family order is preserved from the
  config-driven payload. Nothing else on the page changed.

## What Did NOT Change

- No new page, route, API call, nav entry, or date control (J-18 preserved — the Factor Lab still has no
  as-of state).
- `lib/api.ts` unchanged — `FactorLabFactor.family` was already typed.
- The decile table, rank-IC card, RegimeEffectivenessTable, caveat banner, NA treatment, loading/error
  states, and the combination-cohort section are untouched — the new factors render through them verbatim.
- No `/stocks` leaderboard or `/stocks/[ticker]` change — the new volatility values are stored for the
  read-only lab only and are NOT surfaced on the leaderboard or the stock-detail score breakdowns.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **PASS** — compiled successfully and typechecked all routes; `/research` builds (7.63 kB).

## Known Issues

None. The grouping is presentational and config-driven; the `data-testid="factor-select"` hook is
retained, so option-by-value selection (used by browser QA) is unaffected by the grouping.
