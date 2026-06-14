# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-15
**Date:** 2026-06-14
**Agent:** developer
**Status:** complete

## What Was Built (UI changes — J-69, `/data`)

- **Remove-imported-data panel — symbols input removed; range now mandatory.** The free-text "Symbols"
  input is gone entirely. The panel is now two ISO date fields (From / To) + the "Preview removal" button.
  BOTH dates are required: the button is disabled until both are non-empty AND valid `yyyy-MM-dd`. The
  helper copy and panel hint were updated to describe a range-only, both-dates-required flow.
  - State change: `IsoDateInput`'s required-but-empty → invalid behavior gates the button; the panel's
    `startValid`/`endValid` now initialize to `false` (a fresh empty form is invalid until both filled).
  - `buildScope()` now returns `{ start, end }` only — it never sends a `symbols` field.

- **Confirm-data-removal modal — counts-only, Confirm always visible.** The modal body now shows COUNTS
  ONLY: removable (user-added) bar count + the affected-symbol count foregrounded side-by-side, the
  restated date range, a summary protected-seed bar count ("N bars kept"), and the cascade snapshot /
  forward-return counts. The long enumerated `removable_symbols` list and the per-symbol committed-seed
  breakdown list (which previously could push the Confirm button off-screen for a large range) are removed.
  The body scrolls within a capped `max-h-[55vh]` with `overflow-y-auto`; the footer action row (Cancel /
  Remove) stays OUTSIDE that scroll region (the existing `border-t` footer), so the Confirm button is
  persistently visible regardless of range size.

- **Post-Confirm refresh — unchanged.** After Confirm, `onRemoved()` still calls `refresh()` +
  `loadAvailability()`, so coverage and the per-date availability heatmap reflect the removal.

## Files Changed

- `apps/frontend/app/data/page.tsx` — `RemoveDataPanel` (dropped symbols input + state, both dates
  mandatory, `buildScope` → `{start, end}`); `RemoveConfirmModal` (counts-only body, removed long lists,
  capped scrollable body with the footer Confirm outside the scroll region).

## Design System Conformance

- Reused existing primitives only: `Card`, `PanelTitle`, `IsoDateInput`, the existing in-page modal
  (fixed `backdrop-blur` overlay + `Card` with a `border-t` footer action row). No new primitives.
- Existing tokens/effects preserved: `border-neg` danger styling on the panel button and the destructive
  Remove button, the `backdrop-blur-sm` overlay, the in-flight spinner (`Loader2 animate-spin`), monospace
  `num` numerics. No new colors, spacing, or effects introduced.
- Interactive states preserved: hover / focus-visible / active / disabled on the Preview and Confirm
  buttons; the button-disabled state until both dates are valid; loading (spinner), error (styled alert),
  refused (warn banner + reason), and done (success banner) states all handled.

## New / Notable data-testids (for browser QA)

- `remove-data` — the panel container.
- `remove-start-date` / `remove-end-date` — the two ISO date inputs (no symbols input exists anymore).
- `remove-preview-button` — disabled until both dates are valid ISO.
- `remove-confirm-modal` — the modal; `remove-confirm-button` — the persistently-visible Confirm.
- `remove-bar-count` / `remove-symbol-count` / `remove-range` — the counts-only removable block.
- `remove-cascade-counts` — the cascade snapshot/forward-return counts.
- `remove-refused` — the wholly-seed refusal banner (Confirm disabled).
- `remove-done` — the post-Confirm success banner.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — clean (exit 0).

## Known Limitations

- Browser-QA must use the PREVIEW endpoint or a SAFE small user-added range — NEVER the destructive
  endpoint on committed-seed symbols. Per project memory NVDA carries unrestorable user-added bars; do NOT
  remove a real symbol's bars in QA.
- The TS `RemovePreview` type still carries `removable_symbols` / `not_removable_by_symbol` /
  `cascade.snapshot_dates` (the API contract is unchanged); the J-69 modal simply no longer renders the
  long lists. Intentional — no contract churn.
