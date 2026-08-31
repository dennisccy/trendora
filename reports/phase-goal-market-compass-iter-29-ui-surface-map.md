# Phase goal-market-compass-iter-29 — UI Surface Map

**Phase:** goal-market-compass-iter-29
**Date:** 2026-08-31
**Written by:** ui-impact-analyst

---

## Note on this iteration's diff

`git status` / the dev handoff confirm **zero source files changed** this iteration (backend or
frontend). The only change of any kind is one new row in `next_session_manifests`
(`id=27`, `as_of='2026-08-03'`), produced by calling the pre-existing, unmodified
`GET /api/compass?as_of=2026-08-03` endpoint. Every row below is therefore classified
**"Changed behavior (data-only)"** — the component code is byte-identical to what iter-28 shipped;
what changed is which real-world input now flows through it.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/?asof=2026-08-03` | `CompassStateBandCard` — Regime tile direction badge (`data-testid="compass-state-band-regime-direction"`) | Changed behavior (data-only) | The new `state_band` row this iteration minted has a non-null `regime` band, so the badge's `word ?? "NA"` fallback fires with a real value for the first time on this date | Navigate to `http://localhost:3255/?asof=2026-08-03`, find the "Market state" card's "Regime" tile, and confirm the badge to the right of the regime score reads exactly "improving" (not "NA") |
| `/?asof=2026-08-03` | `CompassStateBandCard` — Phase/stress tile direction badge (`data-testid="compass-state-band-stress-direction"`) | Changed behavior (data-only) | Same new row's `stress` band is non-null | On the same page, in the "Market phase" tile, confirm the badge next to the severity score reads exactly "improving" (not "NA") |
| `/?asof=2026-08-03` | `CompassStateBandCard` — Breadth row direction badge (`data-testid="compass-state-band-breadth-direction"`) | Changed behavior (data-only) | Same new row's `breadth` band is non-null | On the same page, in the "Breadth" row below the two tiles, confirm the badge reads exactly "little changed" (not "NA") |
| `/?asof=2026-08-03` | `CompassSummaryCard` — direction sentence (`data-testid="compass-sentence-direction"`) | Changed behavior (data-only, cross-card consistency) | Sourced from the SAME `_direction_word` computation as the Regime tile's badge, on the SAME new row — this is the exact cross-card consistency check (TC-4) the iter-28 evaluator flagged as failing | Below the "Summary" heading, confirm the sentence reads exactly "Conditions are improving since the prior session (+4.7 regime-score points)." and that its direction word ("improving") matches the Regime tile badge's word |
| `/?asof=2026-08-12` (Latest) or `/?asof=2025-04-15` | `CompassStateBandCard` — all three direction badges | Regression check (no change) | These are two of the 26 pre-existing rows, confirmed byte-identical after this iteration; their `state_band_json` remains null | Navigate to `http://localhost:3255/?asof=2026-08-12` (or omit the param entirely for Latest), and confirm all three direction badges (regime, stress, breadth) still read "NA" — proves the fix is scoped to `2026-08-03` and did not regress the pre-existing "NA" fallback state |
| Top bar (any page) | `AsOfSwitcher` calendar trigger (`data-testid="asof-trigger"`) → popover (`data-testid="asof-calendar"`) → day cell (`data-testid="asof-cal-day"`, `aria-label="View as-of 2026-08-03"`) | No change (existing control) | Confirms the date is reachable by clicking, not only by hand-typing the URL — the underlying `GET /api/runs` list already includes `2026-08-03` (a stored `ScannerRun` existed before this iteration) | Click the as-of trigger button in the top bar, confirm August 2026 is the default month shown, click the day cell for "3", and confirm the URL updates to `?asof=2026-08-03` and the top-bar badge reads "Viewing as-of 2026-08-03 (historical)" |

---

## Backend-Only Changes (No UI Impact)

- None. The one database change this iteration produced (`next_session_manifests` row `id=27`) is
  immediately and fully exposed through the pre-existing `GET /api/compass` endpoint and the
  pre-existing `compass-state-band-card.tsx` / `compass-summary-card.tsx` components — there is no
  backend capability introduced this iteration that lacks a UI path.

---

## Summary

- **Frontend surfaces changed:** 0 (no component/page code modified)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 0
- **Data-only behavior changes observable in the UI:** 1 (the state band now renders real words on
  `/?asof=2026-08-03` instead of "NA", consistent with the Summary card's direction sentence)
