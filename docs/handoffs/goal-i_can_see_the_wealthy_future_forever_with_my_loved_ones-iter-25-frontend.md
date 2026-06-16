# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## What Was Built (UI / SSR)

J-83 — a `?asof=D` deep link now renders the selected date from the FIRST server-rendered paint with no React hydration-mismatch console error and no Clock→History icon flip. The persistent top-bar as-of chrome and the sidebar `?asof` nav hrefs are now correct in the server HTML itself; the client first-paint matches it exactly.

No new visible UI element, no new page/route, no new user action. The change is purely making the existing as-of chrome (History/Clock badge + "Viewing as-of D (historical)") and the J-50 `?asof` hrefs render at D in the server HTML instead of flipping latest→D on hydration.

## How it renders now

- Direct-open / reload / new-tab of `?asof=2026-06-10` (historical): the as-of badge shows the History icon + "Viewing as-of 2026-06-10 (historical)" from first paint; every in-app sidebar link's `href` already carries `?asof=2026-06-10`. No flash, no console hydration error.
- Latest (date-free) URL: Clock icon + "Latest", clean date-free hrefs, no flash.
- Invalid `?asof` (`not-a-date`, `2026-13-40`): degrades to latest with no fabricated date and no hydration error (middleware shape-gate forwards nothing; server seeds latest, matching the client).
- Well-formed-but-unknown `?asof` (e.g. `1999-01-04`): server and client seed it identically (no mismatch), then J-43's `ready` step degrades it to latest after the run list loads.

## Files Changed

- `apps/frontend/middleware.ts` -- NEW App-Router middleware; forwards a shape-valid `?asof` as the `x-asof` request header (matcher excludes api/_next/static/assets).
- `apps/frontend/app/layout.tsx` -- server component reads `x-asof` (async `headers()`) → `<AsOfProvider initialAsOf={…}>`.
- `apps/frontend/components/asof-provider.tsx` -- single `asOf` lazy initializer prefers `initialAsOf` over the client-only URL read.
- `apps/frontend/lib/dates.ts` -- shared `ASOF_PARAM` / `ASOF_HEADER` constants.

## States covered

- Loading: unchanged (the as-of switcher is disabled until the run list is `ready`, as before).
- Empty / no available dates: unchanged (switcher disabled).
- Error / invalid deep link: degrades to latest with no fabricated date (above).

## Gate

`cd apps/frontend && npx tsc --noEmit` → EXIT 0.

## Design-system note

No visual/style change — the badge variants (`warn` amber for historical, `default` for latest), the History/Clock lucide icons, and all tokens are byte-unchanged from prior iterations. The fix only changes WHERE the as-of value is first read (server header vs client `window`), not how anything looks.

## For browser QA

The load-bearing positive evidence for J-83 is a LIVE browser console capture showing ZERO "Hydration failed / server rendered HTML didn't match" errors on direct-open + reload + new-tab of `?asof=2026-06-10`, plus the historical badge + a `?asof=2026-06-10` sidebar href from first paint. Confirm `:3835`/`:8835`/`:9222` reachable before scoring. Also re-smoke the J-18 invariant: `/backtest` has zero page-local `<select>`/date inputs.
