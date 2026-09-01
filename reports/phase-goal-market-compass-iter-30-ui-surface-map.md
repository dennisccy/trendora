# Phase goal-market-compass-iter-30 — UI Surface Map

**Phase:** goal-market-compass-iter-30
**Date:** 2026-09-01
**Written by:** ui-impact-analyst

---

## Note on this iteration's diff

The dev handoff and `git status --short apps/frontend/` (empty) confirm **zero frontend source files
changed** this iteration. The only backend files touched are
`apps/backend/tests/test_manifest_invariants.py` (new unit test, classified backend-internal /
test-only, no UI impact) and `runs/goal-session-market-compass/journey-scripts/J-07.json` (the
regression-golden script itself, classified config/test-fixture, no direct UI impact — it changes what
is *asserted*, not what is *rendered*). The only change of any production kind is one new row in
`next_session_manifests` (`as_of='2026-08-12'`, `version=7`, `id=28`), produced by calling the
pre-existing, unmodified `POST /api/compass/regenerate` endpoint. Every UI-surface row below is
therefore classified **"Changed behavior (data-only)"** — the component code is byte-identical to what
iter-28/iter-29 shipped; what changed is which real-world data now flows through it on the default
(no-`asof`) view specifically.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (no `asof` param — default landing view) | `CompassStateBandCard` — Regime tile direction badge (`data-testid="compass-state-band-regime-direction"`) | Changed behavior (data-only) | The new version-7 `state_band` row this iteration minted for `as_of=2026-08-12` (the frontier date the default view resolves to) has a non-null `regime` band, so the badge's `word ?? "NA"` fallback now fires with a real value on the default view for the first time | Navigate to `http://localhost:3255/` (no query string), find the "Market state" card's "Regime" tile, and confirm the badge to the right of the regime score reads exactly "little changed" (not "NA") |
| `/` (no `asof` param) | `CompassStateBandCard` — Phase/stress tile direction badge (`data-testid="compass-state-band-stress-direction"`) | Changed behavior (data-only) | Same new row's `stress` band is non-null | On the same page, in the "Market phase" tile, confirm the badge next to the severity score reads exactly "little changed" (not "NA") |
| `/` (no `asof` param) | `CompassStateBandCard` — Breadth row direction badge (`data-testid="compass-state-band-breadth-direction"`) | Changed behavior (data-only) | Same new row's `breadth` band is non-null | On the same page, in the "Breadth" row below the two tiles, confirm the badge reads exactly "little changed" (not "NA") |
| `/` (no `asof` param) | `CompassSummaryCard` — direction sentence (`data-testid="compass-sentence-direction"`) | Changed behavior (data-only, cross-card consistency) | Sourced from the SAME `direction_word`/`regime_score_delta` facts as the Regime tile's badge, on the SAME new row — this is the exact cross-card consistency check (TC-4) the iter-28/iter-29 evaluators flagged as failing on the default view | Below the "Summary" heading on the same default `/` load, confirm the sentence reads exactly "Conditions are little changed since the prior session (-0.3 regime-score points)." and that its direction word ("little changed") matches the Regime tile badge's word |
| `/?asof=2026-08-03` | `CompassStateBandCard` — all three direction badges | Regression check (no change) | Confirmed byte-identical after this iteration (iter-29's own mint, unaffected); still reads "improving"/"improving"/"little changed" per iter-29's report | Navigate to `http://localhost:3255/?asof=2026-08-03` and confirm the three badges still read "improving", "improving", "little changed" respectively — proves this iteration's mint on `2026-08-12` did not disturb iter-29's date |
| `/?asof=2025-04-15` | `CompassStateBandCard` — all three direction badges | Regression check (no change) | One of the pre-existing rows re-verified byte-identical this iteration | Navigate to `http://localhost:3255/?asof=2025-04-15` and confirm the page still loads with no error (badge wording for this pre-iter-28 date is not asserted by this iteration's scope, only that the row itself is unmutated) |
| `/` (no `asof` param) | `CompassStateBandCard` market link (`data-testid="compass-state-band-market-link"`) → `/market` page | No change (existing control, regression) | Verifies the surrounding card still navigates correctly after the data-only change | On the default `/` view, click the "Full market context (regime × phase, sectors, themes)" link and confirm the page navigates to `http://localhost:3255/market` and the text "severity-velocity line" is visible somewhere on the page |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_manifest_invariants.py::test_regenerate_on_frontier_yields_state_band_and_prospective_eligible_false` —
  new fixture-scoped unit test proving the regenerate-path + state_band combination; test-only, exercises
  no live route a user hits, no UI surface affected.
- `runs/goal-session-market-compass/journey-scripts/J-07.json` — regression-golden script update (adds
  steps 4–6 asserting the three direction-badge testids at `/`); this is test tooling, not a served page
  or component — no UI surface affected directly, though it now durably guards the surfaces listed above.

---

## Summary

- **Frontend surfaces changed:** 0 (no component/page code modified)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 2 (1 unit test, 1 regression-golden script — neither is a served UI surface)
- **Data-only behavior changes observable in the UI:** 1 (the state band now renders real words on the
  default `/` landing view instead of "NA", consistent with the Summary card's direction sentence)
