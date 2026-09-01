# Phase goal-market-compass-iter-30 — UI Test Plan

**Phase:** goal-market-compass-iter-30
**Date:** 2026-09-01
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Default Today page (`/`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running at http://localhost:8255 and its `/api/health` endpoint returns healthy
- No login required (no auth in this product)

**Steps:**
1. Navigate to `http://localhost:3255/` (no query string)
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The "Market state" card heading is visible
- The "Summary" card heading is visible
- No console errors

---

### UT-02 — Default landing view shows real direction words, not "NA" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- UT-01 passed
- The one-time backend mint for this iteration (`POST /api/compass/regenerate?as_of=2026-08-12&confirm=true`)
  has already been issued (per the dev handoff — this is a data precondition, not a step to repeat)

**Steps:**
1. Navigate to `http://localhost:3255/` (no `asof` query parameter)
2. Locate the "Market state" card
3. Read the badge inside the "Regime" tile, immediately to the right of the regime score
4. Read the badge inside the "Market phase" tile, immediately to the right of the severity score
5. Read the badge in the "Breadth" row below the two tiles

**Expected Result:**
- The Regime tile's badge (`data-testid="compass-state-band-regime-direction"`) reads exactly
  "little changed" — never "NA"
- The Market-phase tile's badge (`data-testid="compass-state-band-stress-direction"`) reads exactly
  "little changed" — never "NA"
- The Breadth row's badge (`data-testid="compass-state-band-breadth-direction"`) reads exactly
  "little changed" — never "NA"

---

### UT-03 — Default view's Summary card is consistent with the Regime badge (happy path / consistency)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- UT-02 passed

**Steps:**
1. On the same `http://localhost:3255/` page load (no `asof` param), scroll to the "Summary" card
2. Read the sentence with `data-testid="compass-sentence-direction"`

**Expected Result:**
- The sentence reads exactly "Conditions are little changed since the prior session (-0.3 regime-score points)."
- The word "little changed" in this sentence matches the word shown in the Regime tile's badge from
  UT-02 step 3 — no card on this screen states a real comparison while another reads "NA" for the same
  comparison

---

### UT-04 — Prior historical date (`/?asof=2026-08-03`) is unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/?asof=2026-08-03`

**Preconditions:**
- Backend/frontend running (as in UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-03`
2. Read the three direction badges in the "Market state" card (Regime, Market phase, Breadth)

**Expected Result:**
- Regime badge (`compass-state-band-regime-direction`) reads exactly "improving"
- Market-phase badge (`compass-state-band-stress-direction`) reads exactly "improving"
- Breadth badge (`compass-state-band-breadth-direction`) reads exactly "little changed"
- These values are unchanged from iter-29 — proves this iteration's mint on `2026-08-12` did not
  disturb the `2026-08-03` row

---

### UT-05 — Prior proven date (`/?asof=2025-04-15`) still loads (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/?asof=2025-04-15`

**Preconditions:**
- Backend/frontend running (as in UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2025-04-15`
2. Wait for the page to load

**Expected Result:**
- Page renders without a blank screen or error message
- The "Market state" and "Summary" cards are both visible
- No console errors (this row is a pre-iter-28 vintage row and is not expected to show real
  direction words — this test only confirms the page itself, and the underlying row, are unaffected)

---

### UT-06 — "Full market context" link still navigates correctly from the default view (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` → `/market`

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3255/`
2. In the "Market state" card header, click the "Full market context (regime × phase, sectors, themes)"
   link (`data-testid="compass-state-band-market-link"`)

**Expected Result:**
- Browser navigates to `http://localhost:3255/market`
- The text "severity-velocity line" is visible somewhere on the resulting page
- No error page or blank screen appears

---

### UT-07 — Regenerate action still requires `confirm=true` (error / negative control)

**Type:** error
**Priority:** P2
**Surface:** backend API (`POST /api/compass/regenerate`), verified via a direct HTTP call, not a UI form

**Preconditions:**
- Backend running at http://localhost:8255

**Steps:**
1. Issue `curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8255/api/compass/regenerate?as_of=2026-08-12"`
   (deliberately omitting `confirm=true`)
2. Immediately re-check the row count: `sqlite3 "file:apps/backend/data/trendora.db?mode=ro" "SELECT COUNT(*) FROM next_session_manifests WHERE as_of='2026-08-12'"`

**Expected Result:**
- HTTP response status is `400`
- Row count for `as_of='2026-08-12'` is unchanged (still 7, matching the post-mint state) — no new
  row was created by this call
- **CAUTION:** this test issues a real write-gated request against the canonical backend. It must NOT
  be run with `confirm=true` — doing so would mint an 8th, out-of-scope version and violate this
  iteration's declared safe set (`{"2026-08-12"}` via exactly one mint, already consumed by the dev
  lane). Only the no-`confirm` negative-control form above is safe to re-run.

---

### UT-08 — Direction badges are discoverable without scrolling past the fold (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Steps:**
1. Navigate to `http://localhost:3255/` in a standard desktop browser window
2. Without scrolling, observe the top of the page

**Expected Result:**
- The "Market state" card (containing all three direction badges) is the first or second card visible
  at the top of the page, above the "Summary" card — a user reading top-to-bottom sees the badges
  before or alongside the Summary card's own direction sentence, so the two can be compared "at a
  glance" as J-07 requires

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Default page loads | smoke | P1 | `/` |
| UT-02 | Default view shows real direction words | happy-path | P1 | `/` |
| UT-03 | Summary card consistent with Regime badge | happy-path | P1 | `/` |
| UT-04 | `2026-08-03` unaffected | regression | P1 | `/?asof=2026-08-03` |
| UT-05 | `2025-04-15` still loads | regression | P2 | `/?asof=2025-04-15` |
| UT-06 | Market-context link still works | regression | P2 | `/` → `/market` |
| UT-07 | Regenerate without confirm still 400s | error | P2 | backend API |
| UT-08 | Badges discoverable above the fold | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
