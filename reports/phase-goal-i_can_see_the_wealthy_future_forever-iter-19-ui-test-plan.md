# Phase goal-i_can_see_the_wealthy_future_forever-iter-19 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Research page loads with the new analysis-mode toggle (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running and reachable (health badge cleared; not a dead un-hydrated shell)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (the loading skeletons resolve into tables)

**Expected Result:**
- The heading "Research — Factor Lab" is visible
- A segmented control labelled "Analysis mode" (`data-testid="analysis-mode-toggle"`) with two buttons "All history" and "As of date" is visible at the top, in the same row as the Factor and Horizon selectors
- The "All history" button is the active/highlighted segment (filled accent background) and has `aria-pressed="true"`; the "As of date" button is inactive (`aria-pressed="false"`)
- The mode-context line (`data-testid="analysis-mode-context"`) below the toggle reads "Pooling every snapshot — all history (the default cross-date aggregate)."
- The Decile table, Rank-IC card, Multi-factor combination cohort section, and Setup & Pattern Lab all render with numbers/NA cells — no blank screen, no "Backend unavailable" card
- No console errors

---

### UT-02 — Default All-history mode shows the full-sample figures (smoke / baseline capture)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research` in default "All history" mode

**Steps:**
1. Locate the "Observations:" meta line above the Decile table and read its value
2. Locate the Rank-IC card (`data-testid="rank-ic-value"`) and read its value and its n chip
3. Locate the Multi-factor combination cohort table (`data-testid="combination-table"`) and read the Combined (composite) row's n (`data-testid="combination-row-composite"`)
4. Locate the Setup & Pattern Lab per-horizon table (`data-testid="event-study-horizon-table"`) and read the "Pooled occurrences (Nd):" meta value

**Expected Result:**
- Each lab shows a non-zero observation/n count (the full cross-date sample)
- Record these baseline n values — UT-05 / UT-06 compare against them after scoping to an earlier date

---

### UT-03 — Toggle to "As of date" updates the active segment and context line (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research` in default "All history" mode
- The global top-bar as-of date switcher (the single `<select>` in the page `<header>`) is at its latest/default date

**Steps:**
1. Click the "As of date" button (`data-testid="analysis-mode-asof"`) in the Analysis-mode toggle
2. Observe the toggle and the mode-context line directly below it

**Expected Result:**
- The "As of date" button becomes the active segment (filled accent background) and gets `aria-pressed="true"`; "All history" becomes inactive (`aria-pressed="false"`)
- Because the global as-of date is still at the latest date, the context line (`data-testid="analysis-mode-context"`) reads: "As of the latest date — equals all history. Pick an earlier date in the top-bar as-of switcher to restrict the window."
- The figures are unchanged from All-history mode (As-of @ latest date == all history)

---

### UT-04 — Context line names the resolved cutoff at an earlier global date (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research` in "As of date" mode (from UT-03)

**Steps:**
1. Set the global top-bar as-of `<select>` (in `<header>`) to one of the **earliest** dates (an option near the bottom of the descending list). This is a React-controlled select — drive it with the native value setter + a bubbling `change` event (per MEMORY `react-controlled-select-needs-native-setter`); a plain `.value =` will not fire React's onChange
2. Read the mode-context line (`data-testid="analysis-mode-context"`)

**Expected Result:**
- The context line now reads "Point-in-time: pooling only snapshots dated ≤ <selected date> (a walk-forward view — smaller n, honest NA at early dates), driven by the single global as-of switcher." where `<selected date>` exactly matches the date chosen in the global switcher
- The accent-coloured "only snapshots dated ≤ <date>" phrase is present

---

### UT-05 — As-of @ early date re-points every lab with reduced n (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` (Factor Lab, Combination cohort, Event study)

**Preconditions:**
- Baseline n values recorded in UT-02
- On `http://localhost:3835/research` in "As of date" mode with the global as-of `<select>` set to an early date (from UT-04)

**Steps:**
1. Read the Factor Lab "Observations:" meta value
2. Read the Rank-IC card n chip
3. Read the Combination cohort Combined-row (`data-testid="combination-row-composite"`) n
4. Read the Event-study "Pooled occurrences (Nd):" meta value

**Expected Result:**
- Each lab's n is **strictly smaller** than the All-history baseline recorded in UT-02
- Low-sample cells (n below the per-lab minimum) display "NA" (muted), never a fabricated number, and still show their honest n chip
- The "Survivorship bias · universe-relative · descriptive" caveat banner is still visible

---

### UT-06 — Returning to All history restores the full sample (happy path / regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research` in "As of date" mode at an early date with reduced n (from UT-05)

**Steps:**
1. Click the "All history" button (`data-testid="analysis-mode-all"`)
2. Read the Factor Lab "Observations:", the Rank-IC n, the Combination Combined-row n, and the Event-study "Pooled occurrences" again

**Expected Result:**
- The "All history" button becomes active (`aria-pressed="true"`)
- The context line reverts to "Pooling every snapshot — all history (the default cross-date aggregate)."
- Each lab's n returns to the larger full-sample value recorded in UT-02 (figures re-point back to the full sample)

---

### UT-07 — In All-history mode, moving the global date does NOT change the figures (regression — J-15)

**Type:** regression
**Priority:** P1
**Surface:** `/research` + global as-of `<select>`

**Preconditions:**
- On `http://localhost:3835/research` in default "All history" mode
- Baseline n values recorded in UT-02

**Steps:**
1. Confirm the Analysis-mode toggle shows "All history" active
2. Set the global top-bar as-of `<select>` to an early date (native-setter + bubbling change event)
3. Read the Factor Lab "Observations:", Rank-IC n, Combination Combined-row n, and Event-study "Pooled occurrences" values

**Expected Result:**
- The mode-context line still reads "Pooling every snapshot — all history (the default cross-date aggregate)." (unchanged)
- Every lab's n is **identical** to the UT-02 baseline — the Research figures do NOT change and there is no research refetch in All-history mode (the labs ignore the global date unless As-of mode is active)

---

### UT-08 — Exactly one date control on the page, in the header (regression — J-18 anti-goal)

**Type:** regression
**Priority:** P1
**Surface:** `/research` (page structure)

**Preconditions:**
- On `http://localhost:3835/research`

**Steps:**
1. Visually scan the whole page for date pickers / date `<select>` controls
2. Confirm the only date control is the global as-of switcher in the top `<header>` bar
3. Confirm the Analysis-mode toggle, the Horizon segmented control, the Factor select, the Subject select, and the combination Condition rows contain **no** date input

**Expected Result:**
- There is exactly **one** date `<select>` on the page and it lives in the `<header>`, not in `<main>` / the page body
- The Analysis-mode toggle is a two-button mode switch ("All history" / "As of date"), not a date picker
- No second date input, calendar, or date `<select>` exists anywhere on `/research`

---

### UT-09 — Backend-unavailable error is surfaced, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend stopped or unreachable (or simulate by blocking the `/research/*` API calls)

**Steps:**
1. Navigate to `http://localhost:3835/research` (or trigger a refetch by toggling mode) with the backend down

**Expected Result:**
- The Factor Lab area shows the "Backend unavailable" card with text "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- The Combination and Event-study sections show their own "Backend unavailable" messages
- No blank white screen, no unhandled exception / React error overlay; no fabricated numbers are shown in place of missing data

---

### UT-10 — Stale "no as-of control" copy is gone (regression / content)

**Type:** regression
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research`

**Steps:**
1. Read the Setup & Pattern Lab subject-row helper text and the page descriptive copy
2. Search the visible page text for any sentence asserting that the page has "no as-of / date control"

**Expected Result:**
- The helper text under the event-study subject selector reads "Re-uses the page's shared horizon selector and the page-level analysis-mode toggle above — no date control of its own (the single global as-of drives any point-in-time scoping, J-18)." — i.e. it points at the global control, not a denial that any date control exists
- No on-page copy claims the page lacks an as-of/date control

---

### UT-11 — Required prior journeys still render in default mode (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research`, `/synthesis`

**Preconditions:**
- On `http://localhost:3835/research` in default "All history" mode

**Steps:**
1. Confirm the Factor-Lab decile table (`data-testid` table within the Decile card), the Rank-IC card, and the regime-effectiveness table (`data-testid="regime-effectiveness-table"`) render full-sample figures
2. Confirm the Multi-factor combination cohort table renders the Baseline, single-factor, Combined (composite), and Strict overlap (AND) rows
3. Confirm the Setup & Pattern Lab renders the per-horizon table, by-regime, and by-sector panels
4. Click "View the names expressing this on the leaderboard" (`data-testid="subject-leaderboard-link"`)

**Expected Result:**
- All three labs render their familiar full-sample figures unchanged from before iter-19 (default mode is identical to prior behaviour)
- The leaderboard cross-link navigates to `/stocks?...` filtered to the subject (J-31 travel intact)

---

### UT-12 — Mode toggle is keyboard-operable and clearly labelled (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research`

**Steps:**
1. Confirm the toggle group has the visible "Analysis mode" label above it
2. Tab to the "As of date" button and press Enter/Space (or click it)
3. Confirm the active segment is visually distinct (filled accent background vs muted)

**Expected Result:**
- The "Analysis mode" caption is visible above the two-button group
- Keyboard focus shows a visible focus ring; activating the button switches modes
- The active segment is unambiguously highlighted, and the context line explains in plain language what the mode pools — a new user can tell which mode is active and what it does without reading code

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research page loads with mode toggle | smoke | P1 | `/research` |
| UT-02 | Default All-history full-sample baseline | smoke | P1 | `/research` |
| UT-03 | Toggle to As-of updates segment + context | happy-path | P1 | `/research` |
| UT-04 | Context line names resolved cutoff | happy-path | P1 | `/research` |
| UT-05 | As-of @ early date re-points labs, n drops | happy-path | P1 | `/research` |
| UT-06 | All history restores full sample | happy-path | P1 | `/research` |
| UT-07 | All-history ignores global date (J-15) | regression | P1 | `/research` |
| UT-08 | Exactly one date control, in header (J-18) | regression | P1 | `/research` |
| UT-09 | Backend-unavailable surfaced, no crash | error | P2 | `/research` |
| UT-10 | Stale "no date control" copy removed | regression | P2 | `/research` |
| UT-11 | Prior journeys + synthesis travel intact | regression | P1 | `/research`, `/synthesis` |
| UT-12 | Toggle discoverable + keyboard-operable | ux | P3 | `/research` |

**P1 tests must all pass for browser QA verdict to be PASS.**
**Critical anti-goal gates:** UT-07 (J-15 — All-history does not refetch on global date) and UT-08 (J-18 — exactly one date control).
