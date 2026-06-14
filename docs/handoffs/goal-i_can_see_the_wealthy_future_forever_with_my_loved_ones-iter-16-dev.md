# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-16
**Date:** 2026-06-14
**Agent:** developer
**Status:** complete

## What Was Built

Pure frontend-only polish completing the appended J-68..J-71 scope. Two isolated presentational components, no backend / schema / engine / config change. `GET /api/data/availability` and the global as-of resolution are read verbatim.

### J-70 — Availability heatmap readability + layout (`availability-heatmap.tsx`)
- **Legible day numbers on every density bucket 0–5.** Replaced the hardcoded `bucket >= 4 ? "text-bg" : "text-text-muted"` (which rendered dark-on-dark `text-text-muted` `#8b98a9` on the dark/low-opacity-accent buckets 0–3) with a per-bucket `BUCKET_TEXT_CLASS` map: `text-text` (near-white) on the faint buckets 0–3, `text-bg` (dark) on the bright teal buckets 4–5. Added `font-medium` for extra legibility. **Design tokens only — no hardcoded hex** (coherence invariant 10).
- **Descending month order.** `bands` now `toMonthBands(...).slice().reverse()` so the newest month renders first (top→bottom). Each month's internal day order stays ascending (`toMonthBands` unchanged), so a calendar still reads left→right, top→bottom within a month.
- **Two-up-per-row responsive layout.** The month-bands container changed from `space-y-5` (single vertical stack) to `grid grid-cols-1 gap-x-5 gap-y-5 md:grid-cols-2` — two month bands side-by-side on a normal viewport, collapsing to one column on narrow screens. `max-h-[28rem] overflow-auto` scroll behavior preserved.
- **Everything else preserved:** same density buckets (`densityBucket`/`BUCKET_CLASS` untouched), same `GET /api/data/availability` payload, hover readout, snapshot ring, legend, click/shift-click prefill into the job form (J-18: never touches the global as-of), and all the attributes browser-QA relies on — `data-testid="availability-cell"`, `data-bucket`, `data-date`, `data-symbols`, `data-total`, `data-snapshot`, `data-testid="availability-month"` (`data-month`).

### J-71 — Keyboard as-of stepping (`asof-calendar.tsx`)
- Extended the dialog's **existing `onKeyDown`** (which already handled `Escape`) to handle **ArrowLeft** (older snapshot) and **ArrowRight** (newer snapshot) via a new `stepAsOf(dir)` helper.
- Stepping moves **one available snapshot date at a time** within the existing `sortedAsc` ordering — never an arbitrary ±1 calendar day onto a non-snapshot day. Current index derived from `asOf` (or the newest index when at Latest / unknown).
- Each step calls the **existing `onSelect(...)`** (wired by the switcher straight to `setAsOf`) so it drives the **single global as-of state** and stays in sync with `?asof` (J-43). Landing on the newest available date passes `null` (the existing "Latest" semantics, matching the day buttons' `isLatest ? null : cell.iso`).
- **Popover stays open** on a keyboard step (no `onClose()`); only Escape / a click outside / Enter-on-a-day still close it.
- **Bounded:** at the oldest date ArrowLeft is a no-op; at the newest ArrowRight rests at Latest (the `nextIdx < 0 || nextIdx > lastIdx` guard returns early — no out-of-bounds index).
- The **viewed-month cursor follows the selection:** after a step, `setView(...)` slides the local month-navigation cursor to the landing date's month so the selected day is visible. `view` remains the ONLY local state — NOT an as-of value.
- `e.preventDefault()` on the handled Arrow keys so they don't scroll the popover/page.
- **No global `window`/`document` keydown listener** — handling lives on the dialog's `onKeyDown` (the dialog receives focus on open via `data-autofocus` on the "Latest" button; Arrow keys bubble from any inner focused element to the dialog handler).
- **No new date state:** `asof-provider.tsx`, `asof-switcher.tsx`, and the `?asof` serialization are untouched. The provider remains the sole owner of the as-of value (J-18 critical invariant).

## Files Changed
- `apps/frontend/components/availability-heatmap.tsx` -- J-70: per-bucket day-number text token (`BUCKET_TEXT_CLASS`), descending month bands (reverse), two-up responsive grid (`grid-cols-1 md:grid-cols-2`).
- `apps/frontend/components/asof-calendar.tsx` -- J-71: ArrowLeft/ArrowRight as-of scrubbing on the existing `onKeyDown` via new `stepAsOf`, bounded, popover stays open, view cursor follows, `preventDefault`.
- `docs/handoffs/...-iter-16-dev.md` -- this handoff.
- `docs/handoffs/...-iter-16-frontend.md` -- frontend-focused handoff (same scope).

## Tests Run
Command: `cd apps/frontend && npx tsc --noEmit`  (NOT `npm run lint` — ESLint is not installed; iter-1 lesson)
Result: PASS — EXIT=0, no type errors.

No backend tests required (frontend-only, no backend code path changed; `GET /api/data/availability` and the as-of resolution are read verbatim). No frontend component test harness exists for these two components, so the browser-QA journeys (J-70, J-71) below are the required visible-change evidence per the framework's UI-visibility rules.

## Pre-handoff Verification
- **Typecheck:** `npx tsc --noEmit` clean (EXIT=0).
- **Scope:** `git diff --stat` shows ONLY the two in-scope components changed (`asof-calendar.tsx`, `availability-heatmap.tsx`).
- **Invariant grep (manual review of the diff):** no hardcoded hex (only design tokens: `text-text`, `text-bg`, `bg-accent/*`, `md:grid-cols-2`); no `window.`/`document.addEventListener` keydown listener added; no new `useState`/date state in `asof-calendar.tsx` (only the pre-existing `view` month cursor); `asof-provider.tsx` / `asof-switcher.tsx` untouched.
- **Did NOT start the dev stack:** the rendered-behavior checks (contrast legibility, descending months, two-up layout, live keyboard scrubbing) are exactly what the browser-qa-agent stage verifies with live evidence next. Avoided a `next build` / dev start so as not to clobber the `.next` dev cache (the documented dead-shell gotcha) or leave server processes running. A pure className/JSX change passing `tsc --noEmit` compiles correctly.

## Known Issues
- None. Both changes are presentational re-renders of already-passing surfaces (J-61 heatmap, J-62 calendar) on the committed seed; no data dependency, no provider needed for QA.
- Evidence hygiene reminder for browser-QA (recurring iters 3/7/10/13/15): both J-70 (zoomed contrast) and J-71 (live scrubbing) are surfaces that previously degraded to blank/byte-identical close-ups — `md5sum` the evidence dir first and re-capture any blank/duplicate as a full-viewport screenshot. Durable evidence = full-viewport captures + DOM-text/attribute extraction (`data-bucket`, `asof-indicator`, `asof-cal-month`, the URL `?asof`).
- After J-70 and J-71 pass, the appended J-68..J-71 scope is complete; 0 buildable Must-have journeys remain failing/unknown except the data-walled J-22/J-23/J-24 (honest NA, non-vetoing). The next evaluation is expected to be GOAL_ACHIEVED.
