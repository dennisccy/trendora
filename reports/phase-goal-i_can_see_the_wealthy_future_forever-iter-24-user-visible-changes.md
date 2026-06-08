# Phase goal-i_can_see_the_wealthy_future_forever-iter-24 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-24
**Date:** 2026-06-08
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now read a plain-language definition for every coverage figure (Price history, Universe, Symbols, Trading days, Snapshot dates, Backfill gaps) directly on the `/data` (Data Manager) page — each number is shown next to a one-sentence explanation so no bare metric appears without context.
- Users can now see a "Universe vs symbols" distinction in prose at the bottom of the Dataset coverage panel, clarifying that the universe is the config-screened, scored set of names while symbols includes every ticker with bars (including ETFs and ^VIX).
- Users can now inspect a per-symbol / per-universe-member coverage table on `/data`, showing for every stored ticker and every universe member: whether it is in the scored universe, whether it has any price data, its date range, its bar count, and a "thin" or "missing" flag — nothing is faked; a member with no data shows NA.
- Users can now filter the per-symbol coverage table by typing a symbol name in the search field, sort it by symbol or bar count (ascending or descending), and toggle "Universe members only" to confirm every scored name either has data or is flagged missing/thin.
- Users can now open the "Remove imported data" panel on `/data`, specify a removal scope (by one or more symbols and/or a date range), and click "Preview removal" to see exactly what would be deleted — user-added bar count and range, committed-seed bars that are protected and kept, and the cascade of dependent snapshots and forward returns — before any data is touched.
- Users can now confirm a seed-safe removal from the confirm-preview modal: clicking "Remove N bars" deletes only the user-added bars in scope, cascade-removes only the dependent snapshots and forward returns, and immediately refreshes the coverage table and the global as-of date switcher to reflect the smaller dataset.
- Users can now see an explicit refusal (with the reason "committed seed") when a removal scope covers only bars from the committed seed — the destructive confirm button is disabled, nothing is deleted, and the reason is shown in amber in the modal.

---

## What Changed in the Visible UI

- The "Dataset coverage" panel on `/data` now shows each aggregate figure inside a bordered card alongside a one-line plain-language definition, replacing the previous bare-number display.
- A "Universe vs symbols" prose line and a backfill-gap description were added at the bottom of the Dataset coverage panel.
- A scrollable "Per-symbol coverage" table was added inside the Dataset coverage card, with columns: Symbol, In universe, Has data, Date range, Bars, Flag. Thin and missing rows are visually distinguished with an amber/muted treatment.
- Two controls were added above the per-symbol table: a symbol search input and a "Universe members only" toggle button. Clicking a column header (Symbol or Bars) sorts the table; clicking again reverses the order.
- A new "Remove imported data" panel was added to `/data` below the existing Resumable imports panel and above the Run history table. It contains a symbols text field, a "From date" date input, a "To date" date input, and a "Preview removal" button styled with a destructive (red-border) treatment.
- A full-screen overlay confirm-preview modal appears when "Preview removal" is clicked, enumerating: removable user-added bars (count, range, symbols list), not-removable committed-seed bars (per symbol, with the "committed seed" reason), and the cascade of dependent snapshots (dates listed) and forward return rows — before anything is deleted. A Cancel button and a destructive "Remove N bars" button are in the modal footer.
- After a successful removal, a green success notice appears in the Remove imported data panel confirming how many bars, snapshots, and forward returns were deleted.

---

## What Old Behavior Changed

- Coverage figures on `/data`: previously each aggregate (universe count, symbol count, etc.) was displayed as a bare number under a label. Now each figure is accompanied by a one-line plain-language definition directly below it, and the universe and symbols counts are explicitly distinguished in a prose summary.
- The `GET /api/data` response: the `coverage` object now additionally carries a `per_symbol` list (one entry per stored symbol and per universe member). Pages that only read the pre-existing fields are unaffected; the Data Manager page now renders this list as the per-symbol table.

---

## Not Visible Yet

- J-37 (missing-data diagnostic and one-click pull-missing) is not built. The per-symbol table will show a "missing" flag for universe members with no bars, but there is no "pull missing" action button yet — that is deferred to iter-25.
- J-38 (unified Unfinished-imports with Retry/Remove actions) is not built. The existing Resumable imports panel (J-34) is unchanged; the generalized Retry/Remove generalization is deferred to iter-25.
- The destructive removal endpoint (`POST /api/data/remove`) was not exercised in the browser against the live host (which holds real user-added NVDA bars with no database restore path). Its correctness on the live host relies on the read-only preview path and is proven by automated fixture tests.
