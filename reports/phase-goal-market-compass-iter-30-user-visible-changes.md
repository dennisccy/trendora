# Phase goal-market-compass-iter-30 — User-Visible Changes

**Phase:** goal-market-compass-iter-30
**Date:** 2026-09-01
**Written by:** ui-impact-analyst

---

## Summary of what kind of iteration this was

This iteration shipped **zero frontend source-code changes** and **zero engine/API code changes**.
Per the dev handoff, the only files touched were one backend test file
(`apps/backend/tests/test_manifest_invariants.py`, adding one new unit test) and one regression-golden
script (`runs/goal-session-market-compass/journey-scripts/J-07.json`). The one production action this
iteration exercised is a single, already-shipped, already-proven API call —
`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` — which minted a new database row
(`next_session_manifests`, `as_of=2026-08-12`, version 7). Everything described below is the *effect*
of that one new row on what a user sees when they load the product with no special URL parameter; no
component, page, or route was edited.

---

## What Users Can Now Do

- Users can now open the product's default landing page — `http://localhost:3255/` with **no** `asof`
  query parameter, i.e. exactly what a first-time visitor sees — and read all three "Market state"
  direction badges as real words instead of the placeholder "NA":
  - Regime tile badge (`compass-state-band-regime-direction`) reads **"little changed"**
  - Market-phase tile badge (`compass-state-band-stress-direction`) reads **"little changed"**
  - Breadth row badge (`compass-state-band-breadth-direction`) reads **"little changed"**
- Users can now cross-check that badge wording against the Summary card's own sentence on the same
  default page load — the "direction" sentence (`compass-sentence-direction`) reads "Conditions are
  little changed since the prior session (-0.3 regime-score points)." — the same "little changed"
  wording as the Regime badge, sourced from the same underlying `state_band.regime` field. This closes
  the exact contradiction (one card stating a real comparison while the badge one line above/below read
  "NA") that both the iter-28 and iter-29 evaluators flagged as blocking J-07.
- This is the first time any of these three badges have shown a real word on the page a user actually
  lands on by default, without navigating or picking a historical date first.

---

## What Changed in the Visible UI

- **Nothing changed in markup, layout, components, or navigation.** The Today page (`/`), the "Market
  state" card (`CompassStateBandCard`), the Summary card, and every other section render the exact same
  JSX shipped in iter-28/iter-29 — confirmed via `git status --short apps/frontend/` showing no
  frontend files touched this iteration.
- What changed is **which data the default (no-`asof`) view now serves**: `next_session_manifests` for
  `as_of=2026-08-12` previously had 6 versions, all with `state_band_json` NULL (badges always rendered
  the "NA" fallback on the default landing view). It now has a 7th version whose `state_band_json` is
  populated, so loading `/` with no parameter is the first real-world exercise, on the frontier/default
  date specifically, of the "real word" rendering branch `compass-state-band-card.tsx` has had since
  iter-28.

---

## What Old Behavior Changed

- None for any *other* date. `/?asof=2026-08-03` (iter-29's date) and `/?asof=2025-04-15` (iter-26's
  date) are unaffected — the dev handoff's field-by-field re-derivation confirms all 6 pre-existing
  `as_of=2026-08-12` versions (1–6) and all other pre-existing rows remain byte-identical after the
  mint (AG-12 holds). Only the default landing view's badge wording changed, and it changed from a
  placeholder ("NA") to a real word — not from one real word to another.

---

## Not Visible Yet

- No new backend capability was added without UI wiring. The one new database row this iteration
  produced is already fully exposed through the pre-existing `GET /api/compass` endpoint and the
  pre-existing `compass-state-band-card.tsx` / `compass-summary-card.tsx` components — there is nothing
  "backend-only" to report.
- All three badges currently show the identical word ("little changed") because the two most recent
  trading sessions in this dataset happen to be a quiet pair (every band's delta falls below its
  respective config-thresholded flat-band). This is not a defect and not a rendering limitation — a
  more eventful close-pair would show different words per band, as already proven independently on
  `/?asof=2026-08-03` (iter-29), where the same badges read "improving".
