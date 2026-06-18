# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## What Was Built (UI)

All on EXISTING Information-Architecture homes — NO new top-level nav, NO new page, NO new date control.

### Dashboard (`/`) — the Market-Phase panel (`components/market-phase-card.tsx`)

- **J-89 phase + filtered-P(bear) history timeline** — a compact SVG step-function: a phase-colored band
  (one fill per phase posture: Expansion/Recovery green, Pullback amber, Correction/Bear red) behind the
  filtered-P(bear) polyline, over the disclosed most-recent snapshot dates, with a dashed as-of marker at
  the resolved date (the J-49 marker treatment). A swatch legend names the phase colours. Read from the
  SAME single served series — the timeline and the panel headline read ONE derivation.
- **J-89 dated causal downtrend-episode list** — one row per episode: `first-trigger → last` date, the
  severity-at-trigger + peak P(bear), and an open/closed badge. Honest empty when none triggered ≤ D.
- **J-90 recovery-turn signal line** — an explainable coloured callout: "Recovery / turn signalled" (green,
  ↑ icon) or "No recovery turn at this date" (muted, shield icon), with the config-defined triggering reason
  in words below — never a bare flag.
- **J-89 FENCED retrospective sub-view** — a dashed-border "Retrospective (full-sample / analysis-only)"
  panel with a Show/Hide toggle (off by default). When shown it fetches `?retrospective=true` and renders
  the SMOOTHED P(bear) tail + the peak-to-trough true-bear dating, with an explicit "future-aware analysis
  only … never feeds any score, signal, episode, or study" disclosure — visibly fenced from the causal path.
- J-18 by construction: the panel reads the single global as-of via `useAsOf()` only; it adds NO new date
  `useState` and NO window/document keydown listener. The retrospective toggle is a MODE, not a date.

### Research (`/research`) — the Recovery-Turn Edge lab (`app/research/page.tsx`)

- A NEW `RecoveryTurnEdgeLab` section (appended after the Regime×Setup×Pattern lab): an Episodes⇄Pooled view
  toggle, a disclosure line (resolved view + n + unique symbols + recovery-turn signal-date count + best
  exit-horizon), the per-horizon edge table (distribution + expectancy + mean MAE/MFE + aggregate
  max-drawdown + BOTH downside-only risk-adjusted ratios — reusing the event-study cell renderer), and a
  client-side-sortable by-signal-phase conditioning table. The survivorship-bias + descriptive caveats show.
  Every `N=` is a chip opening the count-coherent samples drill-down in a NEW tab (J-65). NO order/execution
  affordance (forward-return evidence only).
- Reuses the page's shared horizon selector + analysis-mode toggle (no second date/horizon state). The
  As-of⇄All-history scoping is the page-level mode (J-32); the Episodes⇄Pooled toggle is the overlap mode
  (J-63).

### Samples drill-down (`/research/samples`)

- The cohort header now describes the `recovery-turn` cohort (view + "All recovery-turn dates" or
  "Phase at signal: <label>"). Rows render through the generic ticker/date/values/return path with the
  causal signal-date context (Signal date, Phase at signal, P(bear) at signal) as the qualifying values.

## Files Changed

- `apps/frontend/components/market-phase-card.tsx` -- timeline overlay + episode list + recovery-turn line + fenced retrospective sub-view.
- `apps/frontend/app/research/page.tsx` -- the `RecoveryTurnEdgeLab` + its tables.
- `apps/frontend/app/research/samples/page.tsx` -- the recovery-turn cohort header.
- `apps/frontend/lib/api.ts` -- new response/component types + `fetchRecoveryTurnEdge`; `fetchMarketPhase(asof, signal, retrospective)`.
- `apps/frontend/lib/samples-link.ts` -- the `recovery-turn` cohort serialization for the chip→drill-down link.

## Tests Run

Frontend gate: `cd apps/frontend && npx tsc --noEmit` → exit 0 (clean typecheck; ESLint is not installed —
iter-1 lesson). Backend endpoints feeding these surfaces verified live on :8835 (see the dev handoff).

## Visual / States Handled

- Timeline: loading skeleton (cold compute), honest empty timeline on early/insufficient history.
- Episodes: honest empty list when none triggered.
- Recovery-turn line: rendered in BOTH the available and the NA (insufficient-history) panel states.
- Recovery-Turn Edge lab: warming/loading skeleton, backend-unavailable error card, honest empty-cohort
  state (no recovery turns / no forward-tested returns), NA + n for low-sample cohorts.
- All interactive elements (view toggle, sortable headers, retrospective toggle, N= chips) carry hover/
  focus/active states + aria-labels (sortable headers resolved by `aria-label`, not visible text — iter-27/28).

## Known Limitations

- The Dashboard Market-Phase panel sits below the fold (~1060px) — scroll the timeline + the retrospective
  sub-view into view for the QA capture (iter-3/7/18 evidence-hygiene note).
- On a host with pre-iter-30 `MarketPhaseCache` rows the timeline/episodes/recovery-turn may be absent on
  the FIRST read until the cache refreshes (clear `MarketPhaseCache` once, or any dataset change refreshes
  it) — see the dev handoff. No correctness impact.
