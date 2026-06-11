# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-43 — deep-linkable `?asof` (fix)
- `components/asof-provider.tsx`: the `AsOfUrlSync` serialize effect now depends on the live URL key
  `searchKey = searchParams.toString()`. The previous stale-closure read made the strip win on a
  deep-link load; now the restored `asOf=D` re-serializes `?asof=D` after it commits, so the historical
  date survives **reload, fresh tab, and leaderboard→detail click-through**. The provider remains the
  ONE owner of `?asof` (no page-local date state). An invalid/unknown `?asof` still degrades to latest.

### J-44 — Dashboard "Major indexes & regime" card (`/`, default ON)
- `components/major-indexes-card.tsx` + `components/index-regime-chart.tsx`:
  - Normalized-% lines for the **config-listed** index ETFs (SPY/QQQ/IWM/RSP; DIA omitted honestly —
    no seed bars), one shared % scale, with a legend (names from config). Lines are the **server**
    `series` — no client-side return math.
  - Soft **regime background bands** from `GET /api/regime-history` (stored label+score), drawn as an
    honest **step function between snapshot dates**, colored by the three risk families via the shared
    `lib/regime` mapping. Hover tooltip shows the `yyyy-MM-dd` date (via `lib/dates`), each index's %,
    and the exact stored regime label + score.
  - **Range-preset switcher** (`<Select>`, options from the API/config) re-normalizes to the new range
    start.
  - **Enable toggle** default ON, persisted client-side (`lib/use-persisted-toggle`), fully hides the
    card when off (leaving a "Show Major indexes & regime" affordance).
  - With a historical global as-of, no bar and no band renders after D (both fetched at the same as-of).
  - Loading (skeleton), empty (illustration + honest message), and error (styled alert) states.

### J-45 — Regime bands behind the stock-detail price chart (`/stocks/[ticker]`)
- `components/price-chart.tsx` + `components/regime-band-primitive.ts` + the StockChartPanel in
  `app/stocks/[ticker]/page.tsx`:
  - The SAME stored regime values via the SAME endpoint + `lib/regime` mapping → identical label and
    color for the same date as the dashboard card.
  - A **Regime** toggle in the chart controls (default ON, persisted client-side).
  - Bands render only for dates `<= the resolved as-of`; the **J-20 forward/after-as-of region keeps its
    muted display-only treatment with NO regime bands**. The as-of marker, MA overlays, volume, the three
    scores, setup status, and VCP/pattern flags are unchanged.

### Shared
- `lib/regime.ts`: the ONE label→risk-family/color module used by BOTH chart surfaces (no duplicated
  mapping). Colors are DESIGN-SYSTEM palette tokens only (`--pos`/`--warn`/`--neg`).
- `components/regime-band-primitive.ts`: one Lightweight-Charts primitive shared by both charts.

## Design-system conformance
- All colors are `--pos`/`--warn`/`--neg`/`--accent`/`--text*` tokens (no arbitrary hex); numbers use the
  `.num` tabular class; cards use the shared `Card`/`Select` components; toggles have hover/focus/active
  states; the new chart matches the dark analytical workstation style of the existing price chart.

## Gate
- `cd apps/frontend && npx tsc --noEmit` → clean (0 errors). ESLint is not installed in `apps/frontend`;
  `tsc --noEmit` is the configured frontend gate (do not run `npm run lint`).

## Notes for Browser QA
- The as-of `<select>` is React-controlled — use the native-setter + bubbled change event in eval, then
  assert live DOM (project memory).
- URL legs of J-43 must be asserted via a **post-hydration `window.location.href`** read, not HTTP smoke.
- Canvas hover is not automatable — accept the tooltip leg on code inspection of the single tooltip hook
  in `index-regime-chart.tsx` (reads served stored label/score + `formatIsoDate`); confirm the bands are
  visible in a screenshot.
- Toggle persistence: flip → reload → still flipped (localStorage keys `trendora.dashboard.indexCard` and
  `trendora.detail.regimeBands`); a fresh browser defaults to ON for both.
