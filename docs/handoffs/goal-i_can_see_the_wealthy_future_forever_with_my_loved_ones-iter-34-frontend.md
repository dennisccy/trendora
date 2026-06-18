# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-34
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The single OPTIONAL frontend-only render fold-in that closes the iter-33 coherence Part-C WARN. The
backend `methodology._universe_selection` already returns three per-date fields on `GET /api/methodology`;
the frontend interface previously dropped them. This iteration surfaces them — re-format only, no new
value/computation/endpoint/date-state.

- **`/methodology` → Universe Selection card** now has a new **"Per-date membership rule"** sub-block,
  rendered below the existing "Screen thresholds" list and separated by a `border-t border-border` divider:
  - An "As-of" `Badge` (`variant="default"`) next to the uppercase section label, matching the section's
    existing chip pattern.
  - The `per_date_rule` prose (`text-sm text-text-muted`) — the J-93 per-as-of-date screen rule
    (candidate pool screened from bars ≤ D only on price + ADV + N trailing bars; market-cap dropped per-date).
  - A footnote line (`text-xs text-text-faint`) showing the **candidate-pool denominator**
    (`candidate_pool_size`, e.g. 122 names) and the **minimum-history bar count**
    (`per_date_min_history_bars`, e.g. 200 trailing bars), both with the `num` typographic token.

## Files Changed

- `apps/frontend/lib/api.ts` -- widened the `UniverseSelection` interface (added `candidate_pool_size`,
  `per_date_rule`, `per_date_min_history_bars`) + updated doc comment.
- `apps/frontend/app/methodology/page.tsx` -- added the "Per-date membership rule" block to
  `UniverseSelectionCard`.

## Design-System Conformance

- Used ONLY existing tokens: `text-text-muted`, `text-text-faint`, `text-text`, `border-border`, `num`,
  and the existing `Badge` component (`variant="default"`). No raw HTML where a component exists, no
  arbitrary color/spacing/typography values.
- Matched the existing methodology section styling (mirrors the "Screen thresholds" block layout and the
  card's existing flex header pattern). No new effects invented.
- The block is purely additive presentation — no business logic, no backend state validation in the
  frontend; values read verbatim from the existing API payload.

## States Handled

- **Loading / error / suppressed:** unchanged — the whole `UniverseSelectionCard` only renders when
  `state.kind === "ok"` AND `universe_selection` is present (the backend suppresses the section until the
  committed screen record exists). The new block sits inside that existing guard, so no new empty/error
  state is needed — when the section is absent, nothing renders (honest, not faked).

## Test / Verification

- `cd apps/frontend && npx tsc --noEmit` → **EXIT 0**.
- Backend payload confirmed in-process to serve all three fields (`candidate_pool_size=122`,
  `per_date_min_history_bars=200`, 444-char `per_date_rule`), so the rendered values are real.
- `data-testid` hooks for browser-QA: `universe-per-date-rule`, `universe-candidate-pool-size`,
  `universe-per-date-min-history-bars`.

## For Browser-QA

On `/methodology`, scroll to the Universe Selection card and confirm the "Per-date membership rule" block
renders with the prose + the candidate-pool denominator + the min-history bar count (real numbers, not
blank). This resolves the iter-33 coherence Part-C WARN. No new nav entry, no new page, no new date control
(J-18 invariant preserved — single global as-of selector unchanged).
