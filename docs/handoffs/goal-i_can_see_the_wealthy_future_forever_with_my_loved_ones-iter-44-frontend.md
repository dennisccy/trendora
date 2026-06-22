# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Date:** 2026-06-22
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-101a — one market chart on the Dashboard
- Removed the standalone **Major indexes & regime** card (`<MajorIndexesCard />`) from `app/page.tsx`, plus its import. The two-pane synced **Regime × phase cross-view** card (`<PhaseCrossViewCard />`) is now the single market chart — its pane 0 already renders the same normalized-% index lines over the same stored-regime bands (same `/api/indexes?full=true` + `/api/regime-history?full=true` series). Nothing is lost; the Dashboard is de-cluttered to one chart.

### J-101b — phase bands span the full history at any as-of
- No new frontend logic was required: the cross-view card already fetched `timeline_full` via `GET /api/market-phase?full=true` (unfiltered by the global as-of) and drew the phase bands with `clip=null`. The backend now serves that full series across the FULL stored history independent of the as-of, so the bottom phase pane's bands span the full history (matching the top regime pane). The selected as-of renders only as the vertical marker; stored history past it is display-only.

### J-102 — severity-velocity line + enriched tooltip
- **Chart:** removed the plotted filtered-P(bear) line; drew a **zero-centered severity-velocity line** (color `--accent`) on the retired P(bear) overlay scale slot, with a dashed `0` reference line marking the worsening/easing boundary. NA (null) warm-up points are filtered out before plotting (no fabricated slope). The index % lines stay on their own scale, undistorted.
- **Tooltip (`CrossTooltipBox`):** added two things, read VERBATIM from already-fetched data:
  - the stored **market-regime label + 0–100 score** for the hovered date (from the `/api/regime-history` points — the SAME series the top pane's bands use);
  - the served **severity-velocity** value (formatted `+X.XX` / `-X.XX`, or `NA` at the warm-up head; positive = worsening).
  - The existing **date, index %, phase, severity, and P(bear)** rows are RETAINED (only the plotted P(bear) line was removed; its tooltip value stays).
- **Legend:** the "Filtered P(bear)" swatch is now "Severity velocity (0-centered; + = worsening)".
- **Type:** `MarketPhaseTimelinePoint` gained `severity_velocity: number | null`.

The frontend computes no velocity / regime / probability; it adds no second date state (J-18) and changes no canonical value or the as-of contract. The Market-Phase card and the J-98 at-a-glance summary keep showing P(bear) unchanged.

## Files Changed
- `apps/frontend/app/page.tsx` -- removed `<MajorIndexesCard />` + import (J-101a)
- `apps/frontend/lib/api.ts` -- added `severity_velocity: number | null` to `MarketPhaseTimelinePoint`
- `apps/frontend/components/phase-cross-view-chart.tsx` -- P(bear) line → zero-centered severity-velocity line + 0 reference; tooltip regime label/score + velocity rows; `regimeByDate` lookup; legend + docstring
- `apps/frontend/components/phase-cross-view-card.tsx` -- description paragraph updated

## Design System Adherence
- Reused the EXISTING `PhaseCrossViewCard` / cross-view chart + tooltip primitives — no new component-library elements.
- Colors are tokens only: severity-velocity line uses `var(--accent)` (the slot the P(bear) line used); the 0 reference uses `--text-faint`; tooltip rows reuse the existing `text-muted` / `text` typography and swatch style.
- Loading (existing skeleton), empty (honest-empty phase pane at an early as-of — backend serves `[]`), and NA-velocity (warm-up points dropped from the line, shown as `NA` in the tooltip) states are all handled honestly.
- Net layout: one fewer card on the Dashboard (the duplicate removed), single market chart; the grid is otherwise unchanged.

## Tests Run
Command: `cd apps/frontend && npx tsc --noEmit`
Result: **exit 0** (typecheck clean across the changed files).

## Known Issues
- ESLint was not run via `next lint` (the project has no committed ESLint config, so `next lint` prompts interactively). `tsc --noEmit` is clean.
- Live render evidence (the J-101 single-chart / full-history-bands / honest-empty frames and the J-102 velocity-line / enriched-tooltip frame) is captured by the browser-QA step — the Playwright fallback is pre-planned (md5sum the evidence dir first; the differential legs require byte-distinct frames), per the iter-38/39/40/43 lesson.
