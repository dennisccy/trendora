# goal-iter-22 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### Top bar — as-of stepping (J-79)
- **◀ / ▶ stepper buttons** beside the as-of control (always visible). Step the global as-of one available snapshot date with the **popover closed** (the view is never covered). Bounded: ◀ disabled at the oldest date; ▶ disabled at the newest (which is "Latest"). Hover/focus/active states + disabled (opacity-40, not-allowed) styled with palette tokens.
- **"← → steps date" checkbox** (persisted, default-off). When on, ← / → step the as-of globally (panel closed). Field-guarded — does nothing while typing in a field; the caret moves instead.
- Both drive the **single global as-of state** (the asof-provider's `setAsOf`) — same control, one resolved date everywhere; `?asof` stays in sync (J-43/J-50). No second / page-local date state.

### As-of calendar popover — Year + Month quick-jump (J-79)
- Two dropdowns above the day grid: **Year** (spans stored history) and **Month** (Jan–Dec). Selecting one moves the **viewed month only** (clamped to the navigable stored range) — a presentation aid, not a date selection. The selectable-day / disabled-day / "Latest" / Escape / click-to-commit affordances are unchanged (J-62), as is the panel-open ←/→ scrub (J-71).

### Stocks page header — regime + theme ranking (J-80)
- A header **Card band** showing:
  - **Market regime** — the as-of date's label (colour-coded Badge) + 0–100 score, identical to the Dashboard for that date (re-display of `/api/dashboard`, never recomputed). Empty state when absent.
  - **Top themes** — a ranked strip (top 5, descending Theme Score: `#1 · Name`, `#2 · Name`, …), each chip a link to `/themes` carrying `?asof` while historical. Empty state ("No ranked themes for this date") — never a fabricated theme.
- **`#n` rank badges** on each leaderboard row's theme chips and on the theme-filter `<option>` labels (from the same `/api/themes` ranking). No served rank → no badge.
- Changing the global as-of re-points the regime, the strip, and the chip badges together (keyed to `[asOf]`).

## Files Changed (UI)

- `apps/frontend/components/asof-switcher.tsx` — ◀/▶ buttons, persisted ← → checkbox, field-guarded global key handler.
- `apps/frontend/components/asof-calendar.tsx` — Year + Month dropdowns; shared-step refactor.
- `apps/frontend/components/asof-provider.tsx` — `useAsOfStep()` hook.
- `apps/frontend/app/stocks/page.tsx` — `RegimeThemeHeader`, ranked Top-Themes strip, `#n` chip/filter badges, `/api/dashboard` + `/api/themes` fetches.
- `apps/frontend/app/page.tsx` — shared `regimeVariant` import (no visual change).
- `apps/frontend/lib/asof-step.ts`, `apps/frontend/lib/asof-step.test.ts`, `apps/frontend/lib/regime-variant.ts` — new shared modules.
- `apps/frontend/tsconfig.json` — exclude `**/*.test.ts` from the build.

## Design System Conformance

- All new controls use existing palette tokens (`border`, `border-strong`, `surface-2`, `text`, `text-muted`, `text-faint`, `accent`) and the `Badge` / `Card` components (no raw-HTML soup where a component exists; the native `<select>`/`<input type=checkbox>` are styled to match the existing calendar dropdowns and filter controls — the project deliberately uses styled native form controls, see `components/ui/select.tsx`).
- Hover / focus-visible / active / disabled states on every new interactive element.
- Empty states styled consistently (muted text) and honest (no fabricated regime/theme).
- Regime colour is the SAME mapping the Dashboard uses (one shared `regimeVariant`).

## Tests Run (UI)

- `node lib/asof-step.test.ts` → 13 checks passed.
- `npx tsc --noEmit` → exit 0.
- `next dev -p 3835`: `/`, `/stocks`, `/themes` all HTTP 200, compiled, no errors; killed by port.

## Known Issues (UI)

- No component-render test harness in this frontend; React behaviour is verified by the pure-logic unit tests + browser QA. See the dev handoff for the full test-ID list and the controlled-`<select>` native-setter note.
