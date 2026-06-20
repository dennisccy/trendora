# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Date:** 2026-06-20
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Dashboard `/` only — no new page, no new route, no nav change.

1. **J-98 at-a-glance summary (first paint).** Two compact cards at the top:
   - **Market Regime** — stored label badge + 0–100 score; named component breakdown reachable in an inline
     `<details>` ("Why this regime — component breakdown"). Re-displays `/api/dashboard` verbatim.
   - **Market Phase & Severity** — stored phase badge (posture-coloured) + 0–100 severity (coloured by the
     shared phase posture) + a filtered P(bear) chip; named severity-component breakdown reachable in an
     inline `<details>`. Re-displays `/api/market-phase` verbatim (the SAME value the detail card shows —
     single source).

2. **J-44/J-49 Major-indexes card** (unchanged) followed by the **J-97 cross-view card**
   ("Regime × phase cross-view"): ONE `lightweight-charts` chart, TWO stacked panes, ONE shared time axis.
   - Top pane: normalized-% index lines + stored-regime background bands + the as-of marker (the existing
     lens, unchanged).
   - Bottom pane: the SAME index lines under PHASE-coloured bands, plus a 0–100 severity line and the
     filtered P(bear) line, all from the SAME served `/api/market-phase?full=true` series; the bottom pane
     carries the SAME as-of marker.
   - **Synchronized zoom**: zoom / scroll / drag EITHER pane re-ranges BOTH (the shared time scale) — a view
     transform, not a date control. Hover tooltip surfaces the date, each index %, and the served
     phase / severity / P(bear) for that date.

3. **J-98 collapsed "More detail" section** below the chart (defaults collapsed; persisted): the breadth
   metrics, Candidate Counts, Top Sectors, Top Themes, and the full Market Phase & Severity detail card —
   relocated, not removed. Expand/collapse via the section header.

## States Handled

- **Loading**: chart skeleton (`h-[28rem]` pulse) + summary skeletons.
- **Honest-empty**: an early as-of with no causal history → the bottom pane renders no phase bands / lines
  (the primitive draws nothing for NA/empty phase); the card shows an explicit empty message. The phase
  glance card shows "Not enough history … reported NA, never fabricated."
- **Error**: backend-unavailable styled alerts (cross-view card + phase glance card + dashboard) — nothing
  fabricated.
- **Collapsed / expanded** "More detail" (persisted) and a persisted hide toggle on the cross-view card.

## Design-System Conformance

- Reused `Card`/`CardHeader`/`CardContent`/`CardTitle`, `Badge`, `ComponentBreakdown`, `TermInfo`,
  `ScoreBadge`, the `lightweight-charts` chart, the `AsOfMarkerPrimitive`, and the band-primitive pattern.
- Phase band colours + severity/P(bear) line colours come from the DESIGN SYSTEM tokens
  (`--pos`/`--warn`/`--neg`/`--accent`) via the shared `lib/phase` mapping — NO hardcoded hex outside the
  palette token mirror, NO arbitrary effect. Phase legend swatches use the same posture colours.
- Interactive elements (toggles, disclosures, section header) have hover / focus-visible / active states.
- Responsive: summary row is `md:grid-cols-2`; "More detail" inner grids are `sm:grid-cols-3` /
  `lg:grid-cols-3`; the chart is `autoSize` + full-width.

## J-18 (one date selector) — self-verified on the diff

- No new date `useState`; no `window`/`document` keydown listener (only `getComputedStyle` for tokens);
  no `setAsOf` write from the chart/card (both only READ `useAsOf()`); 0 native `input[type=date]`.

## Verification

- `npx tsc --noEmit` → EXIT 0 (clean).
- Live browser QA pending (browser-qa-agent): two-pane render + synchronized zoom (two byte-distinct
  frames, bottom pane scrolled into the full viewport) + the at-a-glance summary + collapsed/expand "More
  detail". Do not accept on source/API evidence alone.
