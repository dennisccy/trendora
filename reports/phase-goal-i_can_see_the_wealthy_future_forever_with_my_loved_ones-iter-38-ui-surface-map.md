# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Date:** 2026-06-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Dashboard page layout (`app/page.tsx`) | Updated layout | J-98 restructure: compact summary first, then cross-view chart, then collapsed "More detail" | Load the Dashboard; confirm the compact "Market Regime" and "Market Phase & Severity" figures appear before any chart at first paint, and that breadth metrics / Top Sectors / Top Themes are NOT visible until "More detail" is clicked |
| `/` | Market Regime compact figure (new, `page.tsx`) | New component | J-98 at-a-glance summary — display stored regime label + score at first paint | Verify the Market Regime card shows a non-empty label (e.g. "Risk-On") and a numeric 0–100 score; click the "Why this regime — component breakdown" disclosure and confirm the named driver rows appear |
| `/` | Market Phase & Severity compact figure (new, `page.tsx`) | New component | J-98 at-a-glance summary — display stored phase + severity + P(bear) at first paint | Verify the Market Phase & Severity card shows a phase badge (e.g. "Contraction"), a numeric 0–100 severity, and a bear-probability chip; click the component breakdown disclosure and confirm the named severity-component rows expand |
| `/` | Phase & Severity compact figure — honest-empty state | New component state | J-97/J-98 no-fabricated-data rule | Set the as-of calendar to a date with no causal market-phase history; verify the phase glance card shows "Not enough history … reported NA, never fabricated" and displays no score |
| `/` | Cross-view card (`phase-cross-view-card.tsx`) | New component | J-97 — host card for the two-pane synced chart below the Major-indexes card | Scroll down below the Major-indexes card; confirm a card titled "Regime × phase cross-view" is present and renders (not a skeleton) |
| `/` | Cross-view chart top pane (`phase-cross-view-chart.tsx`, pane 0) | New component | J-97 — top pane replicates the existing regime-band index view as the upper half of the synced chart | Confirm pane 0 shows coloured regime-band fills behind the normalized-% index lines, identical in appearance to the standalone Major-indexes regime chart above it |
| `/` | Cross-view chart bottom pane (`phase-cross-view-chart.tsx`, pane 1) | New component | J-97 — new phase lens: phase-coloured bands + severity line + P(bear) line + as-of marker | Scroll the bottom pane into the full viewport; confirm phase-coloured background bands are visible, a 0–100 severity line and a P(bear) line are drawn, and the as-of vertical marker is present on the bottom pane |
| `/` | Cross-view chart synchronized zoom | New behavior | J-97 — both panes share one time scale; scrolling one re-ranges the other | Scroll or drag to zoom into a subset of dates on the TOP pane; confirm the BOTTOM pane's date window changes to match (save a screenshot before and after — the two frames must show different date ranges on both panes) |
| `/` | Cross-view chart — hover tooltip | New behavior | J-97 — tooltip should surface date, each index %, phase, severity, P(bear) for the hovered date | Hover over a date on the bottom pane; confirm the tooltip shows the date, the index % values, the phase label, the numeric severity, and the P(bear) value |
| `/` | Cross-view chart — as-of marker on bottom pane | New behavior | J-97 — the as-of vertical marker must appear on both panes | Confirm the vertical as-of marker line is visible on the bottom pane at the same date position as on the top pane |
| `/` | Cross-view chart — honest-empty bottom pane | New component state | J-97 no-fabricated-data rule | Set as-of to an early date with no causal market-phase history; confirm the bottom pane shows no phase bands and no severity/P(bear) lines (empty pane, no fabricated data) |
| `/` | Cross-view card — loading skeleton | New component state | J-97 loading state | Hard-refresh the Dashboard while backend is responding; confirm a `h-[28rem]` pulsing skeleton renders in place of the chart before data arrives |
| `/` | Cross-view card — hide toggle (persisted) | New behavior | J-97 card has a persisted hide toggle | Click the hide toggle on the cross-view card; reload the page; confirm the chart remains hidden and the toggle state was preserved |
| `/` | "More detail" collapsible section | New component | J-98 — breadth metrics, Candidate Counts, Top Sectors, Top Themes, and Market Phase detail moved here | Load the Dashboard and confirm these sections are NOT visible by default; click the "More detail" header and confirm all five sections (breadth, candidate counts, top sectors, top themes, market phase detail) expand |
| `/` | "More detail" — persisted expand/collapse | Changed behavior | J-98 — expand/collapse state is persisted | Expand "More detail", reload the page, and confirm it remains expanded; collapse it, reload, and confirm it remains collapsed |
| `/` | `market-phase-card.tsx` — phase timeline SVG colours | Changed behavior | Phase colour mapping unified to shared `lib/phase.ts` (deleted private duplicate) | Open "More detail" and expand the Market Phase & Severity detail card; confirm the phase-timeline SVG bands still show posture-appropriate colours (positive / warning / negative tones) matching the phase labels — no blank or wrong-coloured bands |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/market_phase.py` — `compute_market_phase` now includes `timeline_full` in the cached payload; new `market_phase_full_cached` and `market_phase_default_payload` strip helper. These are implementation details of the existing cache path; the user-visible effect is entirely mediated by the API endpoint and the frontend chart.
- `apps/backend/tests/test_market_phase.py` — 6 new backend tests (byte-identical default, full-series verbatim, no smoothed/true-bear, tail-invariance, honest-empty). No UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 page (Dashboard `/`)
- **New pages/routes:** 0
- **Modified components:** 5 existing changed (`page.tsx`, `market-phase-card.tsx`, `lib/api.ts`); 5 new components/files added (`phase-cross-view-card.tsx`, `phase-cross-view-chart.tsx`, `phase-band-primitive.ts`, `lib/phase.ts`, `lib/api.ts` extended)
- **Navigation changes:** no
- **Backend-only changes:** 2 (engine caching helper, tests)
