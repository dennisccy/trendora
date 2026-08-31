# Phase goal-market-compass-iter-29 — User-Visible Changes

**Phase:** goal-market-compass-iter-29
**Date:** 2026-08-31
**Written by:** ui-impact-analyst

---

## Summary of what kind of iteration this was

This iteration shipped **zero lines of new or changed source code**. Every UI component and backend
producer for the "state band" feature (the three direction badges on the Today page) was already
built, tested, and sitting uncommitted in the working tree from iter-28. iter-28's gap was purely
observational: the badges always rendered "NA" because every date anyone could look at had a stored
snapshot from before the feature existed. This iteration's entire contribution was one authorized,
already-supported API call — `GET /api/compass?as_of=2026-08-03` — against a date that had never been
looked at before, which froze a new database row containing real (non-null) data for that date. No
component, route, or endpoint was touched. Everything below describes the *effect* of that one new
row on what a user sees, not a code change.

---

## What Users Can Now Do

- Users can now view the Today page for the specific date **2026-08-03** (via `http://localhost:3255/?asof=2026-08-03`,
  reachable either by typing that URL directly or by opening the as-of calendar in the top bar,
  clicking the "View as-of date" button, and selecting the day cell labeled "3" in August 2026) and see
  all three "Market state" direction badges render **real words instead of "NA"** for the first time on
  any live-servable date:
  - Regime tile badge (`compass-state-band-regime-direction`) reads **"improving"**
  - Market-phase tile badge (`compass-state-band-stress-direction`) reads **"improving"**
  - Breadth row badge (`compass-state-band-breadth-direction`) reads **"little changed"**
- Users can now read a Summary-card sentence ("Conditions are improving since the prior session
  (+4.7 regime-score points).") on that same date that is provably consistent with the Regime tile's
  direction badge — closing the exact "one card says a real comparison while another reads NA"
  inconsistency the iter-28 evaluator flagged as J-07's remaining gap.

This is the first time the state-band feature (shipped, but invisible, since iter-28) is observable
with real content anywhere in the live product.

---

## What Changed in the Visible UI

- **Nothing changed in markup, layout, components, or navigation.** The Today page (`/`), the "Market
  state" card, the Summary card, and every other section render the exact same JSX iter-28 shipped.
- What changed is **which data one specific URL now returns**: `/?asof=2026-08-03` previously had no
  stored snapshot at all (the date had a scored scanner run but no `next_session_manifests` row); it
  now has one (`id=27`, `version=1`), so visiting that URL is the first real-world exercise of the
  already-built "real word" rendering branch in `compass-state-band-card.tsx` — previously only
  exercised in unit tests.

---

## What Old Behavior Changed

- None. Visiting any of the other already-servable dates — no-param **Latest** (currently
  `2026-08-12`), **`2025-04-15`**, or any other stored date — still renders the "NA" badges exactly as
  before this iteration. The dev lane re-verified byte-identity on all 26 pre-existing
  `next_session_manifests` rows after its own actions (full-lane re-verification after replay and
  browser-qa also finish is still pending per the dev handoff's "Known Issues").

---

## Not Visible Yet

- Every manifest-less historical date **other than `2026-08-03`** (and the two other declared-safe
  dates `2026-08-12` and `2025-04-15`, which were already covered by iter-28's manifests) still shows
  "NA" badges — this iteration explicitly did not backfill or broadly mint new snapshots; a broad
  backfill was out of scope by design.
- No new backend capability was added without UI wiring — the single new database row is already fully
  exposed through the existing `GET /api/compass` endpoint and the existing frontend component, so
  there is nothing "backend-only" to report for this iteration.
