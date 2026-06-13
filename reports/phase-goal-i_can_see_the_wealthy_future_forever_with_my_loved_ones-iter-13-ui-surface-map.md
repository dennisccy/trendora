# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `AvailabilityHeatmap` card (`availability-heatmap.tsx`) | New component | J-61: new per-date availability heatmap showing data density per trading day | Navigate to `/data`; confirm a card containing a month-banded calendar grid appears below the Dataset Coverage panel; confirm cells are colored (darker = more coverage) and some cells have a ring marker (snapshot days) |
| `/data` | Heatmap legend (`availability-legend`) | New component | J-61: color ramp legend and snapshot marker key must be visible with the grid | On `/data`, locate the legend inside the heatmap card; confirm the legend labels at least the low/sparse and full/dense ends of the color ramp, and shows the snapshot ring marker key |
| `/data` | Heatmap hover readout (`availability-hover-readout`) | New component | J-61: exact figures on hover/focus (date, symbols/total, snapshot flag) | Hover or tab-focus a heatmap cell; confirm the header readout text updates to show a yyyy-MM-dd date, a "X/Y" symbols count, and a "snapshot: yes" or "snapshot: no" label |
| `/data` | Heatmap day click → job form prefill (`job-start-date`, `job-end-date`) | New behavior | J-61: clicking a day prefills the job form Start/End to that date | Click one heatmap day cell; confirm the Job form's Start date input and End date input both change to that cell's date; confirm the as-of switcher and `?asof` URL parameter are not changed |
| `/data` | Heatmap shift-click range prefill | New behavior | J-61: shift-click a second day to set a date range in the job form | Click one heatmap cell (first anchor), then shift-click a different cell; confirm Job form Start is set to the earlier date and End to the later date |
| `/data` | Heatmap post-job re-read | Changed behavior | J-61: heatmap must refresh after a job completes without a page reload | Trigger a short fetch or backfill job from the Job form; after the job status changes to complete, confirm the heatmap card re-renders (grid reloads) without a full page refresh |
| `/data` | Heatmap loading state (`availability-loading`) | New behavior | J-61: must show a loading placeholder while fetching availability data | Reload `/data` and observe the heatmap area briefly; confirm a loading spinner or skeleton is shown before the grid appears (may require slow network throttle to observe) |
| `/data` | Heatmap empty-DB state | New behavior | J-61: empty DB must render an honest empty state, not fabricated cells | On a freshly seeded or empty-DB environment, load `/data`; confirm the heatmap card renders an empty/zero state message rather than colored cells |
| Top bar (all pages) | `AsOfSwitcher` trigger button (`asof-trigger`) | Changed behavior | J-62: flat `<Select>` dropdown replaced by a calendar popover trigger button | On any page with the top bar, locate the as-of switcher; confirm it now renders as a button (showing "Latest" or a yyyy-MM-dd date) with a chevron icon, not a `<select>` element |
| Top bar (all pages) | `AsOfCalendar` popover (`asof-calendar`) | New component | J-62: calendar month-grid replaces the dropdown for selecting a historical snapshot date | Click the as-of trigger button; confirm a popover opens showing a month grid with labeled days; confirm available snapshot dates appear as clickable buttons (`asof-cal-day`) and other days appear as disabled muted placeholders (`asof-cal-day-disabled`) |
| Top bar (all pages) | As-of calendar month navigation (`asof-cal-prev`, `asof-cal-next`) | New component | J-62: navigate backwards/forwards through months to reach the oldest stored snapshot | In the as-of calendar popover, click the back-arrow (`asof-cal-prev`) repeatedly until the oldest stored month is displayed; confirm the back-arrow becomes disabled (cannot go further); confirm the forward-arrow (`asof-cal-next`) is enabled to navigate back toward latest |
| Top bar (all pages) | As-of calendar "Latest" affordance (`asof-cal-latest`) | New component | J-62: single-click returns to the current (latest) view from any historical month | Navigate the as-of calendar to an older month, then click the "Latest" button (`asof-cal-latest`); confirm the popover closes and the as-of switcher label returns to "Latest" |
| Top bar (all pages) | As-of calendar date selection driving existing `setAsOf` | Changed behavior | J-62: selecting a calendar date must produce the same outcome as the old dropdown (historical badge, `?asof` URL, href stamping) | In the as-of calendar popover, click a selectable snapshot date (`asof-cal-day`); confirm the popover closes, the trigger button updates to show the selected yyyy-MM-dd date, the historical badge (`asof-indicator`) appears, and `?asof=YYYY-MM-DD` is present in the URL |
| Top bar (all pages) | As-of calendar keyboard operation | New behavior | J-62: full keyboard operability required (open / navigate / select / dismiss) | With focus on the as-of trigger, press Enter to open the calendar; Tab to a selectable day button and press Enter to select; then reopen and press Escape to close without changing the date |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — new `compute_availability(session, cfg)` derivation function — UI impact via the frontend consuming the new endpoint; listed in table above as the backing data for the heatmap.
- `apps/backend/app/api/data.py` — new `GET /api/data/availability` read-only route — consumed by `fetchDataAvailability()` in the frontend; not a backend-only change (UI does consume it).
- `apps/backend/tests/test_data_manager.py` — 4 new fixture tests for the availability derivation — test files only, no UI impact.
- `apps/backend/tests/test_api_data.py` — 2 new endpoint tests for shape and empty-DB behavior — test files only, no UI impact.
- `apps/frontend/lib/api.ts` — `fetchDataAvailability()` function and `AvailabilityResponse`/`AvailabilityCell` types — client-side API layer consumed by `AvailabilityHeatmap`; supports the heatmap card listed in the table above.

---

## Summary

- **Frontend surfaces changed:** 14 (across `/data` and the top-bar as-of switcher present on all pages)
- **New pages/routes:** 0 (both J-61 and J-62 are additions to existing surfaces)
- **Modified components:** 2 (`asof-switcher.tsx` rewritten; `apps/frontend/app/data/page.tsx` extended)
- **New components:** 3 (`availability-heatmap.tsx`, `asof-calendar.tsx`, and the new `AvailabilityHeatmap` card mount in `page.tsx`)
- **Navigation changes:** no (no new top-level nav links added)
- **Backend-only changes:** 2 (test files only; the new endpoint and derivation are consumed by the frontend)
