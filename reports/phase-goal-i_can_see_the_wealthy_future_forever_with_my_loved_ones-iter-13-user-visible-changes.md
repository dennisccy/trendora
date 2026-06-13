# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, on the `/data` (Data Manager) page, a trading-day calendar heatmap that shows how many symbols have price data for each date, and whether a portfolio snapshot was computed — giving an at-a-glance picture of data coverage density across the full history.
- Users can now hover or focus any day cell in the availability heatmap to read the exact figures: the date (yyyy-MM-dd), number of symbols with bars vs total symbols, and whether a snapshot exists for that day.
- Users can now click a day in the availability heatmap to instantly prefill the Job form's Start and End date inputs with that date, shortening the workflow to trigger a new fetch or backfill for that specific day.
- Users can now shift-click a second day in the availability heatmap to prefill the Job form with a date range (the clicked days become the Start and End, in order), enabling quick range selection for multi-day backfill jobs.
- Users can now open the as-of date switcher (in the top bar) as a calendar popover instead of a plain dropdown list. The popover shows a month grid where snapshot dates are highlighted as selectable buttons and all other days are visibly muted and non-clickable.
- Users can now navigate backwards (and forwards) month by month in the as-of calendar popover to reach the oldest stored snapshot month, making it easy to select any historical date without scrolling through a long dropdown.
- Users can now click "Latest" inside the as-of calendar popover to return to the current (latest) view from any historical month without manually scrolling to the end of the list.
- Users can now operate the as-of calendar popover entirely by keyboard: Tab cycles through navigation arrows, the "Latest" button, and day buttons; Enter selects a date; Escape closes the popover.

---

## What Changed in the Visible UI

- The `/data` (Data Manager) page now shows a new "Availability Heatmap" card directly below the existing Dataset Coverage panel. The card contains a month-banded trading-day grid with color-coded cells (6-step density ramp from muted/sparse to saturated/full) and a ring marker on snapshot days, plus a legend explaining the color scale and snapshot marker.
- The heatmap card on `/data` shows a live header readout (above the grid) that updates on hover or focus to show the exact date, symbols-with-bars/total, and snapshot yes/no for the focused cell.
- The heatmap card on `/data` highlights the currently selected job-form Start/End date cells in the grid, giving visual feedback that a day was prefilled.
- The availability heatmap on `/data` automatically re-fetches and re-renders after any fetch, backfill, or removal job completes, reflecting the updated data coverage without a page reload.
- The as-of date switcher in the top navigation bar now renders as a button labeled with the current view ("Latest" or the selected yyyy-MM-dd date) with a chevron, replacing the previous flat dropdown list (`<Select>`).
- Opening the as-of switcher now displays a calendar month-grid popover instead of a dropdown list. Selectable snapshot dates appear as distinct, clickable buttons; all other days appear as disabled, muted placeholders.
- Month navigation arrows in the as-of popover clamp to the oldest and newest stored months — the oldest is always reachable, and the arrow to the next month is disabled when already at the newest month.

---

## What Old Behavior Changed

- As-of date selector: previously a flat `<Select>` dropdown listing all snapshot dates as `<option>` elements. Now a calendar popover triggered by a button, showing a month grid. The new popover shows the same selectable dates but in a spatial calendar layout with disabled days in between. Selecting a date or pressing "Latest" still drives the same global as-of state — the `?asof` URL parameter, historical badge, and page-wide date filtering are all unchanged in behavior.
- The `/data` page previously showed the Dataset Coverage panel as the primary data-density visual. The availability heatmap card is now inserted directly below it, making the page longer and adding a new scrollable section.

---

## Not Visible Yet

- None. All capabilities delivered in this iteration (J-61 availability heatmap and J-62 as-of calendar popover) are fully wired into the UI. The backend `GET /api/data/availability` endpoint is consumed by the new heatmap component.
