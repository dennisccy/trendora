# goal-i_can_see_the_wealthy_future_forever-iter-11 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built (UI)

One additive panel on the existing **Research — Factor Lab** page (`/research`): **"Factor effectiveness
by market regime"** (J-27). It renders below the existing decile table + rank-IC card and re-points with
the existing factor + horizon selectors. No new page, no new route, no nav change, **no date control**.

The panel answers: *does this factor still sort forward returns WITHIN each market regime?* — so a factor
that looks good on the pooled decile table can be seen to be regime-dependent.

- **One row per configured regime label** (the six: Strong risk-on, Risk-on, Narrow leadership, Choppy,
  Defensive, Risk-off). The rows are **server-driven from `data.by_regime`** (itself from
  `config.regime.labels`) — NOT a hard-coded frontend regime list (iter-9 config-driven-vocabulary
  lesson).
- **Columns:** Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top − bottom) ·
  Risk-adjusted spread.
- **Honest NA treatment:** a low-sample regime (`n < min_sample`) or a null value renders **"NA"** (muted)
  with the honest `n` carried once per row by the existing `SampleSize` chip in the dedicated `n` column.
  Never blank, never a fabricated number. `risk_adjusted_spread` is NA whenever a decile leg has no
  downside (downside-only honesty — never total volatility).
- **Re-formats the payload only** — it computes no return/factor/regime client-side (the backend is the
  single source of truth).

## Files Changed

- `apps/frontend/lib/api.ts` — added the `RegimeEffectivenessRow` interface and the
  `by_regime: RegimeEffectivenessRow[]` field on `FactorLabResponse`.
- `apps/frontend/app/research/page.tsx` — added the `RegimeCell` cell renderer and the
  `RegimeEffectivenessTable` panel; imported the `RegimeEffectivenessRow` type; rendered the panel inside
  `FactorLab` below the `lg:grid-cols-3` decile/rank-IC grid.

## Design System Conformance

- Wrapped in the existing `Card` + `PanelTitle` idiom; dense numeric `<table>` matching `DecileTable`.
- Numbers use `num` (tabular-nums, monospace); `fmtPct` for the raw mean/spread columns, `fmtRatio` for
  the rank-IC and risk-adjusted spread; `returnClass` colour-grades by sign using palette tokens only
  (`--pos`/`--neg`/muted) — no arbitrary hex, spacing, or font sizes.
- Responsive: the table is wrapped in `overflow-x-auto` (scrolls horizontally < ~640px).
- States: the panel renders only when `data` is present (inside `FactorLab`), so the existing
  `n_total === 0` empty state, loading skeleton, and error card already gate it. No new loading/error
  path was needed.
- Stable selector for QA: the table carries `data-testid="regime-effectiveness-table"`.

## Tests Run (frontend)

Command: `cd apps/frontend && npm run build`
Result: **compiled successfully, types valid, all 14 routes generated.** `/research` = 5.79 kB First Load
(grown by the new panel). No type errors against the new `RegimeEffectivenessRow` / `by_regime` types.

## Known Issues

- **None.** The panel is purely additive and reuses established display helpers. UI workflow verification
  (renders one row per regime; numeric IC+spread for a populated regime; NA+n for a sparse/empty regime;
  re-points on factor change; byte-identical and zero `as_of` requests on the global as-of toggle — J-18)
  is left to the browser-qa-agent per the full-depth pipeline.

## What To Verify (operator, 60 seconds)

1. Open `/research`. Below the decile table + rank-IC card, find **"Factor effectiveness by market
   regime"** with one row per regime label.
2. With a short horizon (5d), confirm at least one regime (e.g. Risk-on) shows a numeric Rank-IC and
   Spread with its `n`; confirm a sparse/empty regime (e.g. Strong risk-on / Defensive) shows **NA** with
   its `n`.
3. Change the **Factor** dropdown → the regime-table numbers change (re-points). Change the **Horizon** →
   they change again.
4. Toggle the global top-bar **as-of** switcher → the whole Factor Lab (including this table) is
   unchanged (the page has no date control — J-18).
