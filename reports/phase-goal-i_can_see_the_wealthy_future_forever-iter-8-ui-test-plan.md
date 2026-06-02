# Phase goal-i_can_see_the_wealthy_future_forever-iter-8 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-8
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Status & Scope

This iteration **STALLED with zero file changes** — no source, config, or seed file was edited and
`data/seed/universe.json` was never produced (the offline Yahoo OHLCV/market-cap fetch was blocked by
HTTP 429). Therefore **no UI surface was added, modified, or removed**.

This is **not** a pure backend-only phase, so a bare N/A stub would be misleading. The correct UI
verification for this iteration is a set of **negative verifications** plus **regression checks**:

1. **Negative verification** — confirm the iter-7 "honest gate" is *still correctly suppressing* the
   not-yet-real Universe-Selection surfaces. The pass criterion is **absence**: no fabricated card, no
   empty/placeholder, no fake expanded universe count. This proves nothing was faked to force a green
   journey.
2. **Regression** — confirm the existing product (dashboard, leaderboard, methodology glossary, data
   coverage) renders exactly as at the end of iter-7 over the unchanged 122-name universe.

There are **no happy-path or validation tests** this iteration because no new capability reached the UI.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/methodology` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/methodology`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and reachable (the methodology page fetches `GET /api/methodology`)

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen, error overlay, or "Failed to load" message
- The methodology page heading is visible (e.g., "Methodology")
- The existing setup/pattern methodology glossary content renders fully
- No uncaught console errors

---

### UT-02 — Universe-Selection card is ABSENT on `/methodology` (negative verification)

**Type:** regression
**Priority:** P1
**Surface:** `/methodology` — Universe-Selection card

**Preconditions:**
- `data/seed/universe.json` does NOT exist (iteration STALLED — it was never produced)
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Wait for the page to fully load
3. Scan the full page (scroll top to bottom) for any "Universe Selection" card, section heading, or
   membership-rule/threshold block (e.g., text containing "Universe Selection", "resolved size",
   "membership rule", or the three config thresholds)

**Expected Result:**
- There is **NO** "Universe Selection" card or section anywhere on the page
- There is **NO** empty placeholder, skeleton, "coming soon", or zero-value threshold block where the
  card would be (the honest gate suppresses the whole card, not a hollow shell)
- The rest of the methodology glossary still renders normally
- **Broken looks like:** a visible "Universe Selection" card showing fabricated/empty thresholds, a
  blank card frame, a "resolved size ≈ 500" line, or a runtime error — any of these means the gate
  leaked or fake data appeared

---

### UT-03 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running (the data page fetches `GET /api/data`)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The existing data-coverage grid/section is visible
- No uncaught console errors

---

### UT-04 — No expanded Universe coverage metric on `/data` (negative verification)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — Universe coverage metric

**Preconditions:**
- `data/seed/universe.json` does NOT exist (STALLED)
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load
3. Locate any "Universe" coverage metric. Read the displayed count value.

**Expected Result:**
- Either the expanded "Universe" metric is **absent**, OR if a universe count is shown it reflects the
  **unchanged 122-name universe** (NOT ~400–500)
- There is **NO** fabricated expanded count (no "~500", "426", "500 names", etc.)
- The existing coverage grid renders unchanged from iter-7
- **Broken looks like:** a Universe metric displaying ~400–500 names, or a count sourced from a
  non-existent `universe.json` — either means fake data surfaced

---

### UT-05 — Dashboard `/` renders ranked rows over the 122-name universe (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (dashboard)

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running with the existing iter-7 seeded data

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load
3. Inspect the ranked rows / scored symbols section

**Expected Result:**
- The dashboard loads with no error page
- Ranked rows / scores render exactly as in iter-7 (still reflecting the 122-name universe)
- No new empty states, no broken counts, no missing sections
- **Broken looks like:** a blank dashboard, a stack trace, or row counts implying a 400–500 universe

---

### UT-06 — Leaderboard `/leaderboard` renders unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/leaderboard`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running with the existing iter-7 seeded data

**Steps:**
1. Navigate to `http://localhost:3835/leaderboard`
2. Wait for the page to fully load
3. Count/inspect the ranked rows

**Expected Result:**
- The leaderboard loads with no error
- Ranked rows render as in iter-7 over the 122-name universe (NOT ~400–500 rows)
- Sorting/columns behave as before; no regression from this no-op dispatch

---

### UT-07 — Navigation exposes no orphaned Universe link (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / header

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Inspect the primary navigation (header/sidebar links)

**Expected Result:**
- Navigation shows the existing iter-7 links (e.g., Dashboard, Leaderboard, Methodology, Data) and
  behaves as before
- There is **NO** new "Universe" / "Universe Selection" nav entry that leads to an empty or fabricated
  screen (the gate keeps the feature fully suppressed, including discoverability)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/methodology` loads | smoke | P1 | `/methodology` |
| UT-02 | Universe-Selection card absent (gate closed) | regression | P1 | `/methodology` |
| UT-03 | `/data` loads | smoke | P1 | `/data` |
| UT-04 | No expanded Universe metric (gate closed) | regression | P1 | `/data` |
| UT-05 | Dashboard renders over 122-name universe | regression | P1 | `/` |
| UT-06 | Leaderboard renders unchanged | regression | P1 | `/leaderboard` |
| UT-07 | No orphaned Universe nav link | ux | P3 | navigation |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note on interpretation:** For UT-02, UT-04, and UT-07 the *desired* outcome is **absence** of the
Universe-Selection surfaces. A "PASS" means the honest gate is still suppressing unbuilt features and
no fabricated data leaked. A "FAIL" means a fake/empty universe surface appeared — which would be worse
than the STALL itself.
