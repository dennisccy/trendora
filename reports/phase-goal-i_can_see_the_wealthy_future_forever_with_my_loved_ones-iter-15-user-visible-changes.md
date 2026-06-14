# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Date:** 2026-06-14
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now start a multi-month or full-history backfill (or fetch-then-backfill) job from the Data Manager at `/data` and expect it to run to completion — it no longer crashes partway with an internal database error on long date ranges.
- Users can now remove imported data by specifying only a date range (From and To) in the Remove Data panel at `/data`. Both dates are required; there is no longer a symbols text box to fill in or misuse.
- Users can now see a compact counts-only confirmation before executing a removal: how many bars will be removed, how many symbols are affected, how many protected seed bars are kept, how many snapshots cascade away, and the date range — all in one screen view without scrolling.
- Users can now click the "Remove" (Confirm) button in the removal confirmation dialog without scrolling, regardless of how large the date range is.

---

## What Changed in the Visible UI

- The "Remove imported data" panel on `/data` no longer has a "Symbols" text input field. The panel now consists of only two date fields (From and To) and the "Preview removal" button.
- Both the From and To date fields on the Remove panel are now required. The "Preview removal" button stays disabled until both fields contain a valid date in `yyyy-MM-dd` format.
- The confirmation modal for data removal no longer shows the long enumerated list of removable symbols or the per-symbol committed-seed breakdown. It now shows only count summaries (removable bar count, affected symbol count, protected-seed bar count, cascade snapshot/forward-return counts) alongside the restated date range.
- The confirmation modal body is now scrollable within a capped height (`max-h-[55vh]`), and the footer row containing the "Cancel" and "Remove" buttons sits outside the scrollable area — making the "Remove" button persistently visible without scrolling.

---

## What Old Behavior Changed

- **Remove Data panel — Symbols input**: Previously the panel had a free-text "Symbols" box (optional) and both date fields were optional. Now the symbols box is gone entirely and both date fields are mandatory before the button activates.
- **Remove Data panel — Button enable condition**: Previously the "Preview removal" button could become active with only one date or no dates filled in (symbols only). Now both dates must be valid ISO dates before the button is enabled; a partially filled form keeps the button disabled.
- **Remove Data confirmation modal — symbol lists**: Previously the modal listed every affected symbol individually and every protected-seed symbol by name, which could push the Confirm button off the bottom of the screen for a large range. Now the modal shows only counts, and the Confirm button is always visible without scrolling.
- **Backfill job behavior on multi-month ranges**: Previously a multi-month or full-history backfill job could die partway with a database crash, leaving incomplete work with no honest status. Now the job runs to completion; a single failed day is isolated with its own error while all other days complete; re-running the same range fills only what is missing without creating duplicates.

---

## Not Visible Yet

- The backend API still returns the full `removable_symbols`, `not_removable_by_symbol`, and `cascade.snapshot_dates` arrays in its response — these fields are no longer rendered in the UI but remain available in the API contract for future use.
- J-70 (availability heatmap readability improvements) and J-71 (as-of calendar keyboard stepping) are backend/frontend capabilities deferred to iteration 16. No UI change from these journeys is present in this iteration.
