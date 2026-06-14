# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Date:** 2026-06-14
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `RemoveDataPanel` — symbols text input | Removed element | J-69: removal is now range-only; a free-text symbols box was an accident vector | Navigate to `/data`, scroll to "Remove imported data" panel, confirm no symbols text input is present at all |
| `/data` | `RemoveDataPanel` — From and To date fields | Changed behavior | J-69: both dates are now mandatory; previously both were optional | Fill in only the "From" date and confirm the "Preview removal" button remains disabled; fill in both dates with valid ISO values and confirm the button becomes enabled |
| `/data` | `RemoveDataPanel` — Preview removal button | Changed behavior | J-69: button is now disabled until both From and To are valid `yyyy-MM-dd` strings | Enter an invalid date string (e.g. `2024-13-01`) in either field and confirm the button stays disabled; enter valid dates in both fields and confirm the button activates |
| `/data` | `RemoveConfirmModal` — modal body | Changed behavior | J-69: replaced long per-symbol enumeration lists with counts-only summary to keep Confirm always visible | Open the confirmation modal after filling in a date range and confirm the modal body shows only numeric counts (bar count, symbol count, seed count, cascade counts) with no list of individual symbol names |
| `/data` | `RemoveConfirmModal` — Confirm (Remove) button | Changed behavior | J-69: footer sits outside the scrollable body region so the button is always reachable | Open the confirmation modal and confirm the "Remove" button is visible without scrolling, even when the counts summary body is long |
| `/data` | `RemoveConfirmModal` — scrollable body | New component | J-69: body capped at `max-h-[55vh]` with `overflow-y-auto` to contain content without pushing footer off screen | Open the confirmation modal and, if the body content is taller than 55vh, confirm a scrollbar appears inside the body while the footer remains stationary outside it |
| `/data` | Backfill job card (existing job status display) | Changed behavior | J-68: multi-month backfill jobs now run to completion instead of crashing; a single bad day appears as `failed` with its error while the job reaches `partial` or `complete` rather than an unrecoverable crash state | Start a backfill job spanning multiple months from the Data Manager and confirm the job card eventually shows a completed or partial status (not an error/crash), with any individual failed day reported in the job errors without the whole job dying |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` (J-68 transaction boundary) — per-date write sessions replace the shared orchestrating session in `_do_backfill`; new `_cleanup_orphan_run` helper cleans up half-written snapshot rows on per-date failure. Internal transaction management; no new data displayed or new action exposed.
- `apps/backend/app/api/data.py` (J-69 `require_range=True`) — enforces that `POST /api/data/remove` and `/preview` reject a single-ended or empty date scope with a 400. The frontend already prevents this via the button-disabled state, so the 400 is a backend safety net invisible to a user following the normal flow.
- `apps/backend/tests/test_data_manager_backfill_committed_session.py` — new regression test file for J-68. No UI surface affected.
- `apps/backend/tests/test_api_data_remove_range.py` — new endpoint test file for J-69. No UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 6
- **New pages/routes:** 0
- **Modified components:** 2 (`RemoveDataPanel`, `RemoveConfirmModal` within `apps/frontend/app/data/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 4
