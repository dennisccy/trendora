# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Date:** 2026-06-17
**Agent:** developer
**Status:** complete

## What Was Built

A new **Market Phase & Severity** panel on the Dashboard (`/`), directly below the existing
"Major indexes & regime" card. It surfaces, for the single global as-of date, where in the market cycle
the tape sits — a read-only descriptive context read, never a stock signal.

- **`components/market-phase-card.tsx`** (new) — a `Card` (matching the Dashboard card style) that:
  - reads the SINGLE global as-of from `useAsOf()` only (NO new date `useState`, NO `window`/`document`
    keydown listener) and fetches `GET /api/market-phase` for it;
  - renders, in the header row: the discrete **phase** label as a `Badge` colored by stress posture
    (Expansion/Recovery → green, Pullback → amber, Correction/Bear → red), and the **P(bear)** as a
    `Badge` colored by level;
  - renders, in the body: the **0–100 severity** headline + the cycle legs (drawdown % / off-trough %),
    the **named severity component breakdown** (drawdown depth, time-underwater, stored market regime,
    breadth-below-200-DMA, VIX stress gate — each with its [0,1] value + points contributed, an NA
    component honestly marked), and the **filter observation vector** (the most-recent stress readings ≤ D
    that drive P(bear), with the full count disclosed);
  - handles loading (animated skeleton), NA/partial (explicit honest empty treatment — "Not enough history
    to derive a market phase", never a fabricated phase/probability), and error (styled warn alert,
    "confirm the backend is running") states.
- **`app/page.tsx`** — mounts `<MarketPhaseCard />` beside `<MajorIndexesCard />`. No new page, route, or
  nav change.
- **`lib/api.ts`** — `fetchMarketPhase(asof, signal)` + the `MarketPhaseResponse` / `MarketPhaseComponent`
  / `MarketPhaseObservation` / `MarketPhaseVixLevel` types. The client only re-formats server values — it
  computes no phase / severity / probability.

## Files Changed

- `apps/frontend/components/market-phase-card.tsx` -- NEW. The Dashboard Market Phase & Severity panel.
- `apps/frontend/app/page.tsx` -- mount `<MarketPhaseCard />` after `<MajorIndexesCard />`.
- `apps/frontend/lib/api.ts` -- `fetchMarketPhase` + response/component/observation/vix types.

## Design System Compliance

- Uses `Card` / `CardHeader` / `CardTitle` / `CardContent` + `Badge` from the configured component
  library — no raw-HTML where a component exists.
- Colors use only palette tokens via Badge variants (`ok`/`warn`/`danger`) and `text-text*`/`bg-surface*`
  /`border-border*` utility tokens — no arbitrary hex/spacing/font values.
- The component-breakdown uses the SAME three-column treatment as the existing `ComponentBreakdown`
  (Component · Value · Contribution) so the explainable-score look matches the Dashboard regime/score
  cards.
- Dates render through the shared `lib/dates.ts` `formatIsoDate` (J-42) — no per-component date literal.
- Loading skeleton, NA/partial empty state (icon + message), and error alert are all styled; the happy
  path is not the only handled case.

## Coherence / Anti-goal Notes

- **Exactly one date selector (J-18):** the panel reads `useAsOf()` only; it holds no second date state
  and adds no keydown listener (grep-verifiable in the panel diff). It re-points with the single global
  as-of like every other date-scoped surface, and the `?asof` URL serialization is unchanged.
- **J-06 regime coherence:** the panel's market-regime severity input is the SAME stored regime score the
  Dashboard regime card and `/stocks` header read — it is read verbatim from the stored snapshot
  (backend), never recomputed client-side. The "Market regime (stored)" component value equals
  `(100 − stored regime_score)/100`.
- **No fabricated data:** an insufficient-history window renders the explicit NA/partial treatment, never
  a synthesized phase or probability.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — exit 0 (clean typecheck after all edits).
- Backend integration tests for the served payload shape + as-of repoint + error degradation are in
  `apps/backend/tests/test_market_phase.py` (all green).

## Known Issues / Limitations

- On the daily-history host the FIRST fetch of a given as-of can take ~10–12s (backend cold compute over
  ~1170 stored runs; cached sub-second thereafter). The loading skeleton covers this; no client change is
  needed.
- Browser-QA capture of the rendered panel (phase + severity + breakdown + P(bear); stepping the as-of
  into 2022 → Bear/high-severity/high-P(bear), 2024/2026 → Expansion/Recovery/low-P(bear)) is left to the
  browser-qa-agent stage per the pipeline (requires a live frontend + Chrome MCP).
