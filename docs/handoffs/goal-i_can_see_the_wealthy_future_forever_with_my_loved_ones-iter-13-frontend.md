# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built (UI)

### J-61 — Per-date availability heatmap on `/data`
- New card `AvailabilityHeatmap` (`apps/frontend/components/availability-heatmap.tsx`), mounted on
  `apps/frontend/app/data/page.tsx` directly under the existing **Dataset coverage** panel.
- A month-banded trading-day calendar grid (weeks as rows, Monday-first). Each trading day is a single
  `<button>` cell colored by `symbols_with_bars / total_symbols` density — a 6-step sequential ramp from a
  muted surface (none/sparse) to a saturated accent (full). A SPARSE day (e.g. 158-of-159) is visibly
  fainter than a full day; a low/empty day is muted (honest, never omitted as covered).
- A positive-toned **ring** marks days that also have an immutable snapshot. A **legend** shows the ramp +
  the snapshot marker.
- **Hover or focus** a day → the exact figures appear in the header readout
  (`data-testid="availability-hover-readout"`): `yyyy-MM-dd`, `symbols_with_bars/total_symbols`, and
  `snapshot yes/no` — read verbatim from the cell (no recompute). Each cell also has a native `title` and
  an `aria-label` carrying the same figures.
- **Click a day** → prefills the Job form's Start + End to that day (start == end). **Shift-click** a
  second day → prefills the range [min, max]. These write ONLY `setStart`/`setEnd` (job parameters); the
  global as-of control is never touched. The current job-form Start/End is highlighted in the grid.
- States: loading spinner, error ("no cells shown rather than fabricated"), empty-DB (`EmptyState`), and a
  post-job/-removal re-read (the card re-fetches `GET /api/data/availability`).

### J-62 — As-of calendar popover (top-bar switcher)
- `apps/frontend/components/asof-switcher.tsx` rewritten: the flat `<Select>` dropdown → a popover trigger
  button (`data-testid="asof-trigger"`) showing the current view (`Latest` or the historical `yyyy-MM-dd`)
  + a chevron. Opening it renders `AsOfCalendar` (`apps/frontend/components/asof-calendar.tsx`, NEW).
- The calendar is a month grid: only the available snapshot `dates` (from `asof-provider`) are selectable
  `<button>` days (`data-testid="asof-cal-day"`); every other day is a disabled muted placeholder
  (`data-testid="asof-cal-day-disabled"`). Month-nav arrows (`asof-cal-prev`/`asof-cal-next`) clamp to the
  oldest/newest stored month — the oldest is always reachable. A **Latest** row (`asof-cal-latest`)
  returns to the latest view.
- Keyboard: focus moves into the popover on open; Tab cycles nav/Latest/days; Enter selects; Escape
  closes; outside-click closes. The historical badge (`asof-indicator`) is unchanged.

## Data Contract (frontend)
- `fetchDataAvailability()` → `AvailabilityResponse { total_symbols, trading_day_count, cells:
  AvailabilityCell[] }`, `AvailabilityCell { date, symbols_with_bars, total_symbols, snapshot_exists }`
  (`apps/frontend/lib/api.ts`). Throws on non-200 so the heatmap shows its error state (no fabricated cells).

## Invariants (UI)
- **No second date state.** `asof-provider.tsx` is byte-unchanged. The switcher (`open`) and calendar
  (`view` = viewed-month nav cursor) hold no as-of value; every selection calls the existing `setAsOf`.
  `?asof` (J-43) and href stamping (J-50) are untouched.
- **Heatmap click ≠ as-of.** Day/range click writes only `setStart`/`setEnd`.
- **No nested-interactive (iter-5).** Each heatmap/calendar day is one `<button>`; markers/labels are
  non-interactive spans inside it.
- All dates render `yyyy-MM-dd` through `lib/dates.formatIsoDate` (J-42).

## Verification
- `npx tsc --noEmit`: clean (exit 0).
- Backend route live-verified read-only against the real persistent DB (figures consistent with coverage).

## Key test selectors (for browser-QA)
- Heatmap: `availability-heatmap`, `availability-legend`, `availability-cell` (with
  `data-date`/`data-symbols`/`data-total`/`data-snapshot`/`data-bucket`/`data-selected`),
  `availability-hover-readout`, `availability-month`, `availability-loading`, `availability-error`.
- Job-form date inputs (assert prefill): `job-start-date`, `job-end-date`.
- As-of: `asof-trigger`, `asof-calendar`, `asof-cal-day`, `asof-cal-day-disabled`, `asof-cal-prev`,
  `asof-cal-next`, `asof-cal-month`, `asof-cal-latest`, `asof-indicator` (historical badge).

## Note for browser-QA
The pump's QA backend on :8835 (no `--reload`) must be restarted before it serves
`GET /api/data/availability` (it predates this change). A fresh `bash scripts/start-backend.sh` picks up
the route. The heatmap shows its error state (not fabricated cells) until the backend serves the route.
