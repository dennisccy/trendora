# Phase goal-market-compass-iter-39 — User-Visible Changes

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

<!-- This is a repair, not a new-capability iteration. Everything below is RESTORED capability. -->

- Users can now open the Today page (`/`) on any of the 21 previously-crashing historical `as_of`
  dates (e.g. `http://localhost:3255/?asof=2026-08-11`, `.../?asof=1996-01-02`,
  `.../?asof=2020-03-20`, and 18 others — full list below) and see the full page — market-state
  band, summary, What changed, Leadership rotation, Next-session focus, manifest strip — instead
  of a full-page "Something went wrong on this page" error card.
- Users can now expand the "Not priority" disclosure in the Next-session focus card on those same
  historical dates and read an honest explanation (`Not priority (20 shown — held-back counts
  unavailable for this manifest version)`) instead of the page crashing before it ever rendered.
- Users can now reach `/market`, `/stocks`, or any other page via the sidebar after landing on
  one of the 21 dates above — previously the crash meant only the sidebar/header chrome (outside
  the crashed page body) stayed usable.

---

## What Changed in the Visible UI

- The Next-session focus card's "Not priority" disclosure summary text on the Today page (`/`)
  now has two variants depending on which stored session the viewed date maps to:
  - **Pre-iter-38 manifest** (any of the 21 previously-crashing dates, e.g. `/?asof=2026-08-11`):
    reads `Not priority (20 shown — held-back counts unavailable for this manifest version)`.
  - **Post-iter-38 manifest** (currently only the frontier date, `/?asof=2026-08-12`): reads the
    same fully-counted string as before this fix —
    `Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)` — byte-
    identical, no visible change on this one date.
- Inside the expanded "Not priority" list, entries for pre-iter-38 dates no longer show the
  "— ranked #N of the above-floor names, cap 20" lead-in sentence (that field is honestly absent
  for those manifests); entries on the frontier date (`/?asof=2026-08-12`) still show it unchanged.

---

## What Old Behavior Changed

- **Today page (`/`) on historical dates**: previously, visiting `/?asof=<date>` for 21 of 23
  historical dates crashed the whole page body to the generic `error.tsx` card ("Something went
  wrong on this page" / "Try again" button), leaving only the sidebar/header usable. Now the page
  renders completely on every one of those 21 dates. This was a bug introduced in iter-38, not a
  behavior users had ever seen working before iter-38 shipped — this iteration is a repair back to
  the pre-iter-38-equivalent working state (plus the honest degraded-text addition above).
- **"Not priority" disclosure summary on old dates**: there was no prior "old" rendered text to
  compare against on these 21 dates, because the page crashed before the disclosure ever rendered.
  The only true behavior change visible to a user who compares "before iter-38" vs. "after this
  fix" is the new honest degraded-count wording above (in place of the fully-counted wording that
  iter-38 briefly required but which these older rows never had data for).
- **Frontier date (`/?asof=2026-08-12`)**: unchanged — same fully-counted "Not priority" text,
  same expandable cap-rank/cap lead-in sentences on individual entries.

---

## Not Visible Yet

None — this iteration is a frontend-only fix with no backend change and no new backend capability
awaiting UI wiring. J-15 (stock-level "Suppressed moves" undercount) remains unbuilt and queued,
but that is pre-existing, out-of-scope backlog, not a new backend capability introduced this
iteration.

---

## Reference: the 21 previously-crashing dates now fixed

1996-01-02, 1996-02-01, 2001-04-17, 2005-04-01, 2018-11-20, 2019-03-01, 2020-01-02, 2020-03-20,
2022-06-15, 2025-04-15, 2026-01-02, 2026-03-30, 2026-03-31, 2026-04-01, 2026-07-01, 2026-07-23,
2026-08-01, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11.
