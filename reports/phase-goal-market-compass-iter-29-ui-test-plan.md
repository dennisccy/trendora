# Phase goal-market-compass-iter-29 — UI Test Plan

**Phase:** goal-market-compass-iter-29
**Date:** 2026-08-31
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## BINDING CONSTRAINT — read before running any test below

This iteration names an exact, pre-approved `as_of` allow-list (goal.md TC-6 / AG-12): every browser
action in this document, and any future extension of it, must stay inside

```
{ no param (Latest), "2026-08-12", "2025-04-15", "2026-08-03" }
```

`GET /api/compass?as_of=<any other date>` mints a **new, permanent** database row the first time it is
requested. **Do not navigate to, type, or otherwise trigger any `?asof=` value outside this set** —
doing so is a process violation of this iteration's spec, not a harmless exploratory click. Every test
case below only ever uses dates from this set.

---

## Test Cases

---

### UT-01 — Today page loads at the newly-frozen date (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/?asof=2026-08-03`

**Preconditions:**
- Backend running at http://localhost:8255 and frontend at http://localhost:3255 (start via
  `bash scripts/start-backend.sh` / `bash scripts/start-frontend.sh` if not already running)
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-03`
2. Wait for the page to fully load (skeleton cards disappear)

**Expected Result:**
- Page renders the heading "Today" with subtitle "The ten-second read after the close"
- A badge near the top right reads "Data as-of 2026-08-03"
- No "Backend unavailable" error card appears
- No console errors
- The "Market state" card (`data-testid="compass-state-band-card"`) is visible

---

### UT-02 — All three direction badges render real words, not "NA" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/?asof=2026-08-03` — `CompassStateBandCard`

**Preconditions:**
- UT-01 passed (page loaded successfully at `?asof=2026-08-03`)

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-03`
2. In the "Market state" card, locate the "Regime" tile (left column) and read the small pill badge
   next to the large regime score
3. Locate the "Market phase" tile (right column) and read the small pill badge next to the severity
   score
4. Locate the "Breadth ·" row below the two tiles and read the pill badge on its right edge

**Expected Result:**
- Regime tile badge (`data-testid="compass-state-band-regime-direction"`) reads exactly **"improving"**
- Market phase tile badge (`data-testid="compass-state-band-stress-direction"`) reads exactly
  **"improving"**
- Breadth row badge (`data-testid="compass-state-band-breadth-direction"`) reads exactly
  **"little changed"**
- None of the three badges reads "NA"

---

### UT-03 — Regime badge agrees with the Summary card's direction sentence (happy path / consistency)

**Type:** happy-path
**Priority:** P1
**Surface:** `/?asof=2026-08-03` — `CompassStateBandCard` + `CompassSummaryCard`

**Preconditions:**
- UT-02 passed

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-03`
2. Note the word shown in the Regime tile's direction badge (from UT-02)
3. Scroll down to the "Summary" card and read the first sentence
   (`data-testid="compass-sentence-direction"`)

**Expected Result:**
- The Summary card's first sentence reads exactly:
  **"Conditions are improving since the prior session (+4.7 regime-score points)."**
- The word "improving" in that sentence matches the Regime tile badge's word from step 2 — no card on
  the page states a real comparison ("improving") while another states "NA" for the same comparison
  (this is the exact inconsistency the iter-28 evaluator flagged; it must not recur)

---

### UT-04 — Latest date's state band still shows "NA" (regression — AG-12/TC-5)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Latest, no `asof` param) — `CompassStateBandCard`

**Preconditions:**
- None (default landing state)

**Steps:**
1. Navigate to `http://localhost:3255/` (no query string)
2. Wait for the page to load
3. Read the three direction badges in the "Market state" card (same three locations as UT-02)

**Expected Result:**
- The top-right badge reads "Data as-of 2026-08-12" (the current stored frontier)
- All three direction badges (`compass-state-band-regime-direction`,
  `compass-state-band-stress-direction`, `compass-state-band-breadth-direction`) read exactly **"NA"**
- This proves the real-word fix from UT-02/UT-03 is scoped to `2026-08-03` only and did not alter any
  pre-existing row

---

### UT-05 — A second pre-existing safe date also still shows "NA" (regression — AG-12/TC-5)

**Type:** regression
**Priority:** P2
**Surface:** `/?asof=2025-04-15` — `CompassStateBandCard`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2025-04-15`
2. Wait for the page to load
3. Read the three direction badges in the "Market state" card

**Expected Result:**
- Top-right badge reads "Data as-of 2025-04-15"
- All three direction badges read exactly "NA" (unchanged from before this iteration)

---

### UT-06 — The frozen date is reachable by clicking, not only by typing a URL (ux)

**Type:** ux
**Priority:** P2
**Surface:** top-bar `AsOfSwitcher` / `/`

**Steps:**
1. Navigate to `http://localhost:3255/` (Latest)
2. Click the top-bar date control (`data-testid="asof-trigger"`, showing a clock icon and "Latest")
3. In the calendar popover that opens (`data-testid="asof-calendar"`), confirm it is already showing
   "August 2026" (`data-testid="asof-cal-month"`) — no month navigation needed
4. Click the day cell for "3" (`data-testid="asof-cal-day"`, `aria-label="View as-of 2026-08-03"`)

**Expected Result:**
- The day cell for "3" is NOT greyed out / disabled (`data-testid="asof-cal-day-disabled"` does not
  apply to it) — it is a clickable, available snapshot date
- After clicking, the URL becomes `http://localhost:3255/?asof=2026-08-03`
- The top-bar badge changes from the plain "Latest" pill to an amber pill reading
  "Viewing as-of 2026-08-03 (historical)" (`data-testid="asof-indicator"`)
- The three direction badges update to "improving" / "improving" / "little changed" (same as UT-02)

---

### UT-07 — The real words survive a page refresh (regression / persistence)

**Type:** regression
**Priority:** P2
**Surface:** `/?asof=2026-08-03`

**Steps:**
1. Navigate to `http://localhost:3255/?asof=2026-08-03`
2. Confirm the three direction badges read "improving" / "improving" / "little changed" (per UT-02)
3. Refresh the page (press F5 or Cmd+R) — do NOT navigate away first

**Expected Result:**
- After reload, the URL is still `http://localhost:3255/?asof=2026-08-03`
- All three direction badges show the exact same words as before the refresh
- This confirms the data is a permanently stored database row, not a one-time or cached render

---

## Not applicable this iteration

**Validation tests:** N/A. No form was added or changed this iteration — the sole change is a
read-only page rendering a newly-populated data row; there is no user input surface to validate.

**Error tests:** N/A. No new error path was introduced. The pre-existing "Backend unavailable" /
"Market-phase data unavailable" states are unmodified since iter-28 and reproducing them would require
stopping the backend or requesting an `as_of` value outside the binding safe set above — out of scope
for this iteration's test plan.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Today page loads at 2026-08-03 | smoke | P1 | `/?asof=2026-08-03` |
| UT-02 | Three badges show real words | happy-path | P1 | `/?asof=2026-08-03` |
| UT-03 | Regime badge matches Summary sentence | happy-path | P1 | `/?asof=2026-08-03` |
| UT-04 | Latest still shows "NA" | regression | P1 | `/` |
| UT-05 | 2025-04-15 still shows "NA" | regression | P2 | `/?asof=2025-04-15` |
| UT-06 | Date reachable via calendar click | ux | P2 | top-bar |
| UT-07 | Real words survive refresh | regression | P2 | `/?asof=2026-08-03` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-04 is elevated to P1 (beyond the
skill's default "regression = P3") because it is this iteration's binding AG-12 proof, not an
incidental check.
