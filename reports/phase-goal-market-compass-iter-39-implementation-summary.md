# Phase goal-market-compass-iter-39 — Implementation Summary

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** developer

---

## Features Implemented

- **Today page no longer crashes on historical dates**: the `/` page (the "Today" market
  compass) previously showed a full-page "Something went wrong" error on 21 of 23 historical
  dates you could view via the date switcher. It now loads normally on all of them. This was a
  bug introduced in the previous iteration (iter-38), not a new feature — this iteration is a
  repair.
- **Honest "unavailable" message on older sessions**: on the dates that predate last iteration's
  "why-not" detail feature, the "Not priority" section on the Today page now shows an honest
  message — "held-back counts unavailable for this manifest version" — instead of crashing. On
  the one date that already has the newer detail (the current frontier date, 2026-08-12), nothing
  changed: it still shows the full breakdown ("20 shown of 52 held back — 27 cap-excluded, 25
  below-floor near-miss").

---

## Changed Behavior

- **Today page (`/`) on historical dates**: Previously, visiting `/?asof=<date>` for 21 of 23
  historical dates crashed the whole page to a generic error screen. Now it renders completely,
  with the one changed detail being the "Not priority" summary text on the dates that predate the
  detail feature (described above). No other behavior changed.

---

## Backend-Only Items

None. This iteration made no backend changes — the underlying data and computation were already
correct; only the frontend's handling of that data was fixed.

---

## Incomplete Items

None from this iteration's scope. Everything the phase spec asked for was implemented: the
type-contract fix, the guarded render, a new automated test covering both the old-manifest and
new-manifest cases, and restoring four automated test scripts that had been improperly edited in
the prior iteration.

Full click-through verification of all 21 dates and the seven affected features (What-changed,
Summary, Manifest history, Market page, Incident-date rendering, Leadership rotation, and the
why-not detail itself) is the next pipeline stage's job (browser-based QA), not this stage's —
that stage runs after this one and will produce its own report.

---

## Config and Environment Changes

None. No new environment variables, no config file changes, no database migrations.

---

## Known Limitations

- This developer-stage check confirmed the fix works correctly on 3 representative dates using a
  real browser (the oldest crashing date, one mid-range date, and the newest/frontier date), plus
  confirmed all 21 previously-crashing dates now return a successful response from the server.
  The full automated browser walkthrough of every affected page and feature happens in the next
  pipeline stage.
- One pre-existing, already-known housekeeping item (a build-output folder that should be
  excluded from version control but currently isn't) was not addressed — it was called out in
  the phase instructions as explicitly out of scope for this repair.
