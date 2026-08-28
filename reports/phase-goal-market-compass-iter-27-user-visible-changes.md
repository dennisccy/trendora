# Phase goal-market-compass-iter-27 — User-Visible Changes

**Phase:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. No new user action, button, form, or page was added. This iteration is a route-ordering fix
inside an existing, already-consumed endpoint (`GET /api/compass`) — see "What Changed in the Visible
UI" below for the one narrow, already-scaffolded display state it makes reachable for the first time.

---

## What Changed in the Visible UI

- On the Today page (`/`, and `/?asof=<date>` for historical dates), the **Manifest card**'s **Basis**
  badge row (`compass-manifest-strip.tsx`'s `BasisLine`, `data-testid="compass-manifest-basis"`) can now
  display its red/"danger" **"Basis: unavailable"** state for a real historical request, for the first
  time. That badge and its exact label/color were already shipped and already unit-tested since iter-11
  (`apps/frontend/lib/basis-disclosure-label.ts`) — nothing about its appearance changed. What changed is
  purely a backend control-flow reorder in `GET /api/compass` (`apps/backend/app/api/compass.py`) that
  stops a previously-mandatory self-heal from running before the badge's underlying fact is read, so the
  live route can finally reach that pre-built badge state instead of masking it.
- No other visible element changed. The other three Basis states ("available"/green, "rebuilt"/amber,
  "unverifiable"/neutral) render exactly as before for exactly the same input conditions as before.

---

## What Old Behavior Changed

- **Today page → Manifest card → Basis badge, for a historical as-of date whose frozen manifest's
  underlying scan data was later removed** (e.g. during a data-repair/cleanup operation): previously, the
  page would silently trigger a full data rebuild behind the scenes before rendering anything, so the
  badge could only ever show "Basis: available" or "Basis: rebuilt" — the user had no way to see that the
  original underlying data was ever missing. Now, the page reports the honest "Basis: unavailable" state
  instead, and no silent rebuild happens — the user sees the true provenance gap rather than a
  quietly-patched-over one.
- Every other Today-page card (Compass Summary, What Changed, Focus) and every other route (`/stocks`,
  `/sectors`, `/themes`, dashboard, market-phase) is unaffected — their self-heal behavior is byte-identical
  to before this iteration.

---

## Not Visible Yet

- The new "Basis: unavailable" reachability is a real, live-route capability now, but no as-of date in the
  current live/canonical database currently satisfies its trigger condition (a frozen manifest whose
  backing scanner run has since been deleted) — the incident-window dates that would have satisfied it are
  the 7 dates that are deliberately kept manifest-less (never given a manifest at all, per the binding
  owner ruling), so they never reach the Manifest card in the first place. Deliberately deleting a live
  `ScannerRun` row to reproduce the state is out of scope and forbidden this iteration (project
  never-touch-the-canonical-DB-destructively rule). So an operator cannot currently click through to see
  the red "Basis: unavailable" badge live; it is proven only by the backend's automated fixture test
  (`apps/backend/tests/test_api_compass.py::test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`),
  not by a browser walkthrough. See the UI test plan for the exact command to run instead.
