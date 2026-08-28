# Phase goal-market-compass-iter-27 — UI Test Plan

**Phase:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Scope note

This iteration touched only three backend files (`apps/backend/app/api/compass.py`,
`apps/backend/app/engine/compass.py`, `apps/backend/tests/test_api_compass.py`) and zero frontend files.
The response shape of `GET /api/compass` did not change; only which `basis.status` value is reachable for
a given input changed. The already-shipped Manifest card on the Today page (`/`) renders that field
verbatim, so the tests below are almost entirely **regression** tests confirming the reorder did not
disturb the two states already reachable in the live database, plus one test case documenting — honestly,
not by fabricating a browser step — that the actual new state cannot be reproduced live this iteration.

---

## Test Cases

---

### UT-01 — Today page loads with the Manifest card visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255 (verify with `curl http://localhost:8255/api/health`)
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (the compass cards populate after their client-side fetch resolves)

**Expected Result:**
- Page renders without a blank screen or a React error boundary
- A card with the heading "Manifest" is visible below the Compass Summary / What Changed / Focus cards
- No browser console errors

---

### UT-02 — Manifest card shows "Basis: available" for an intact historical manifest (regression, P1)

**Type:** regression
**Priority:** P1
**Surface:** `/?asof=2025-04-15`

**Preconditions:**
- Same as UT-01
- This as-of date's manifest (version 2, mode `retrospective`) and its backing scanner run are both
  intact in the live canonical database (verified via `GET /api/compass?as_of=2025-04-15` returning
  `basis.status: "available"` at the time this plan was written)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2025-04-15`
2. Wait for the Manifest card to populate
3. Locate the badge row directly below the hash-chip row inside the Manifest card
   (`data-testid="compass-manifest-basis"`)

**Expected Result:**
- The badge reads exactly "Basis: available", rendered in the green/positive badge style (not gray,
  amber, or red)
- No gray detail text appears next to the badge (the API's `basis.detail` is `null` for this date)
- The badge row above it shows "version 2" and "retrospective"
- This proves the new fast path the reorder introduced is inert on the common, already-working case — the
  branch most at risk of regressing from this change

---

### UT-03 — Manifest card shows "Basis: rebuilt" with its detail text for the frontier manifest (regression, P1)

**Type:** regression
**Priority:** P1
**Surface:** `/?asof=2026-08-12`

**Preconditions:**
- Same as UT-01
- This as-of date's manifest (version 6, mode `at_ingest`) has a backing scanner run whose recorded
  `created_at` differs from what the manifest captured, so it already reports `"rebuilt"` (verified via
  `GET /api/compass?as_of=2026-08-12` at the time this plan was written)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-12`
2. Wait for the Manifest card to populate
3. Locate the `data-testid="compass-manifest-basis"` badge row

**Expected Result:**
- The badge reads exactly "Basis: rebuilt", rendered in the amber/warn badge style
- The gray detail text "the source scanner run was recreated after this manifest was frozen" appears
  immediately to the right of the badge
- The badge row above it shows "version 6" and "at ingest"

---

### UT-04 — "Basis: unavailable" state — not reproducible live this iteration (documented gap, P1)

**Type:** happy-path (this IS the iteration's core fix — but it cannot be exercised through the browser
in this environment; see explanation)
**Priority:** P1
**Surface:** `/` (would be a historical `?asof=` date, if one existed with the right precondition)

**Why this cannot be a browser step:**
The red "Basis: unavailable" badge only renders when a frozen manifest's backing `ScannerRun` row has been
deleted from the database. No as-of date in the current live/canonical database is in that state — the 7
dates that would qualify are deliberately kept manifest-less altogether (per the binding owner ruling), so
they never reach the Manifest card at all — and this iteration is explicitly not authorized to delete a
live `ScannerRun` row to manufacture the condition (project rule: never destructively alter the canonical
database; the spec's OUT OF SCOPE list routes this drill to the isolated fixture suite only). Writing a
browser step here would require fabricating a precondition that cannot honestly be created.

**Steps (automated substitute — run this instead):**
1. `cd apps/backend`
2. `.venv/bin/python -m pytest tests/test_api_compass.py -v -k unavailable`

**Expected Result:**
- `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run` PASSES
- Its assertions include `basis["status"] == "unavailable"`, `basis["detail"]` containing "no longer
  stored", the manifest's `manifest_hash`/`version`/`content_hash` byte-identical to before the run was
  removed, and the removed run staying absent (`healed is None`) — i.e. the fix is proven at the route
  function level even though it cannot be proven by clicking through the live UI this iteration

---

### UT-05 — "Regenerate manifest" control is unaffected by the reorder (regression, P2)

**Type:** regression
**Priority:** P2
**Surface:** `/?asof=2025-04-15`

**Preconditions:**
- Same as UT-02

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2025-04-15`
2. Wait for the Manifest card to populate
3. Click the outlined amber "Regenerate manifest" button below the Versions list
   (`data-testid="compass-manifest-regenerate-button"`)
4. In the modal that opens, click the "Cancel" button in the modal's footer (do **not** click the second
   "Regenerate manifest" button inside the modal — confirming it mints a real new manifest version against
   the live database, which is outside this iteration's verification scope)

**Expected Result:**
- After step 3: a modal titled "Confirm manifest regenerate" opens
  (`data-testid="compass-manifest-regenerate-confirm-modal"`), containing the text "This mints a NEW
  manifest version for 2025-04-15 from the current selection rule and config."
- After step 4: the modal closes; the Manifest card's badges (including "Basis: available" from UT-02)
  are unchanged; no new "v3" entry appears under a "Versions" list
- Confirms `POST /api/compass/regenerate`'s route (explicitly untouched this iteration) still behaves as
  before

---

### UT-06 — An unknown/future `?asof` value still degrades safely to "Latest" (regression, P2)

**Type:** error
**Priority:** P2
**Surface:** `/?asof=2099-01-01`

**Preconditions:**
- Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2099-01-01`
2. Wait for the page to finish loading

**Expected Result:**
- The page does NOT show a blank screen or crash
- The `?asof=2099-01-01` query parameter is stripped from the URL bar shortly after load (pre-existing
  `asof-provider.tsx` degrade-to-latest behavior, unrelated to and unaffected by this iteration's change)
- The Manifest card shows the current "Latest" frontier manifest's data, not an error state
- Confirms `resolved_date`'s unchanged 4xx mapping for unresolvable dates does not surface as a broken page

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Today page loads with Manifest card | smoke | P1 | `/` |
| UT-02 | "Basis: available" regression (intact manifest+run) | regression | P1 | `/?asof=2025-04-15` |
| UT-03 | "Basis: rebuilt" regression (frontier manifest) | regression | P1 | `/?asof=2026-08-12` |
| UT-04 | "Basis: unavailable" — not live-reproducible, automated substitute | happy-path | P1 | pytest (not browser) |
| UT-05 | "Regenerate manifest" control unaffected | regression | P2 | `/?asof=2025-04-15` |
| UT-06 | Unknown/future `?asof` degrades safely | error | P2 | `/?asof=2099-01-01` |

**P1 tests must all pass for browser QA verdict to be PASS.** Note UT-04's P1 evidence is a pytest run, not
a browser interaction — its "PASS" criterion is the automated test result, not a screenshot.
