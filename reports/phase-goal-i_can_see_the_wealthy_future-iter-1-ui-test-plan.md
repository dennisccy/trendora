# Phase goal-i_can_see_the_wealthy_future-iter-1 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope note

This is the foundation iteration: a navigable **app shell** with a persistent sidebar, a live backend-connectivity health badge, 7 section pages (all intentional styled empty states), and 2 detail-route stubs. There is **no scoring, scan, or stock data** yet — every page shows an empty-state card describing what will appear later. There are **no forms** this iteration, so no form-validation test cases apply; the closest "validation" surface is the health badge's contractual values. API/pytest coverage lives in the functional test plan (TC-01…TC-19) and is not duplicated here.

These UI tests are executed against a running frontend at `http://localhost:3835` with the backend reachable (except UT-13, which deliberately stops the backend).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Dashboard loads with sidebar, header, and empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error overlay
- A persistent left sidebar is visible with the brand label "Trendora" at the top
- The heading "Dashboard" is visible with subtitle "The daily snapshot at a glance"
- An empty-state card is visible with title "No scan yet" and body text beginning "Market regime, top sectors and themes…"
- The header shows the text "Research-only · decision support · no orders" on the left and a health badge on the right
- No console errors

---

### UT-02 — All 7 sidebar destinations are present and labeled (smoke / ux)

**Type:** smoke
**Priority:** P1
**Surface:** `Sidebar` (all routes)

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Inspect the left sidebar navigation links

**Expected Result:**
- Exactly these 7 links are visible, in this order: "Dashboard", "Stocks", "Themes", "Sectors", "Scanner Runs", "System Health", "Watchlist"
- The footer text "Offline seed spine · v0.1" is visible at the bottom of the sidebar
- No "Stock Detail" or "Run Detail" link appears in the sidebar (these are intentionally excluded)

---

### UT-03 — Clicking each sidebar link navigates and highlights the active item (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `Sidebar` (all routes)

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Click the "Stocks" link in the sidebar
3. Click the "Themes" link in the sidebar
4. Click the "Sectors" link in the sidebar
5. Click the "Scanner Runs" link in the sidebar
6. Click the "System Health" link in the sidebar
7. Click the "Watchlist" link in the sidebar
8. Click the "Dashboard" link in the sidebar

**Expected Result:**
- After each click the browser URL changes to, respectively: `/stocks`, `/themes`, `/sectors`, `/scanner-runs`, `/system-health`, `/watchlist`, then `/`
- After each click the just-clicked link shows the active style: a filled/surface background, bolder text, and a small teal accent dot at the right edge of the row
- Only one link is highlighted at a time
- The main content heading updates to match the clicked section each time (e.g. clicking "Stocks" shows heading "Stocks")

---

### UT-04 — Stocks page renders heading + empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/stocks`

**Expected Result:**
- Heading "Stocks" visible with subtitle "Stock Leaderboard — ranked, filterable"
- Empty-state card visible with title "No ranked stocks yet" and body text beginning "The leaderboard will list each stock's Leadership, Entry Quality and Risk scores…"
- The "Stocks" sidebar link is highlighted as active

---

### UT-05 — Themes page renders heading + empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/themes`

**Expected Result:**
- Heading "Themes" visible with subtitle "Theme Leaderboard — ranked by Theme Score"
- Empty-state card visible with title "No ranked themes yet" and body text beginning "Themes will be ranked by a price-confirmed Theme Score…"
- The "Themes" sidebar link is highlighted as active

---

### UT-06 — Sectors page renders heading + empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/sectors`

**Expected Result:**
- Heading "Sectors" visible with subtitle "Sector / industry Leaderboard — ranked by Sector Score"
- Empty-state card visible with title "No ranked sectors yet" and body text beginning "Sector and industry ETFs will be ranked by Sector Score…"
- The "Sectors" sidebar link is highlighted as active

---

### UT-07 — Scanner Runs page renders heading + empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/scanner-runs`

**Expected Result:**
- Heading "Scanner Runs" visible with subtitle "History of immutable scan snapshots"
- Empty-state card visible with title "No scanner runs yet" and body text beginning "Each daily scan is saved as an immutable, dated snapshot…"
- The "Scanner Runs" sidebar link is highlighted as active

---

### UT-08 — System Health page renders heading + empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/system-health`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/system-health`

**Expected Result:**
- Heading "System Health" visible with subtitle "Forward-tested evidence — does the ranking work?"
- Empty-state card visible with title "No evidence yet" and body text beginning "Walk-forward forward returns by score bucket…"
- The "System Health" sidebar link is highlighted as active

---

### UT-09 — Watchlist page renders heading + empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/watchlist`

**Expected Result:**
- Heading "Watchlist" visible with subtitle "Your saved stocks — persisted across restarts"
- Empty-state card visible with title "Your watchlist is empty" and body text beginning "Saved stocks will show date added, your reason…"
- The "Watchlist" sidebar link is highlighted as active

---

### UT-10 — Stock detail stub resolves (not a 404) (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate directly to `http://localhost:3835/stocks/NVDA`

**Expected Result:**
- Page returns successfully (HTTP 200), NOT a Next.js 404 "This page could not be found"
- Heading "NVDA" (ticker upper-cased) visible with subtitle "Stock detail"
- Empty-state card visible with title "Detail not available yet" and body beginning "A price + moving-average chart…"
- The persistent sidebar is still visible (this route is reachable directly but is not in the nav, so no sidebar link is highlighted)

---

### UT-11 — Scanner run detail stub resolves (not a 404) (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/scanner-runs/[runId]`

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate directly to `http://localhost:3835/scanner-runs/1`

**Expected Result:**
- Page returns successfully (HTTP 200), NOT a Next.js 404
- Heading "Run #1" visible with subtitle "Immutable as-of snapshot"
- Empty-state card visible with title "Run detail not available yet" and body beginning "This will show the exact, immutable as-of view…"
- The persistent sidebar is still visible

---

### UT-12 — Health badge shows connected state with live contract values (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `HealthBadge` (header, all routes)

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running and reachable; `GET /api/health` returns 200

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Observe the badge area in the top-right of the header immediately on load
3. Wait up to ~2 seconds for the health request to resolve

**Expected Result:**
- On first paint the badge briefly shows "Checking backend…" with a pulsing dot (loading state)
- After the request resolves the header shows four badges:
  - A green badge reading "Backend OK"
  - A badge reading "provider: seed"
  - A badge reading "seed 2026-05-28" (the latest seed date from the live response)
  - A badge reading "158 symbols" (the universe symbol count from the live response)
- The badge does NOT show "Backend unavailable"

---

### UT-13 — Health badge shows explicit "Backend unavailable" when backend is down (error)

**Type:** error
**Priority:** P1
**Surface:** `HealthBadge` — error path (header)

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend STOPPED (or `/api/health` made unreachable / pointed at a dead port)

**Steps:**
1. Stop the backend service (or block `GET /api/health`)
2. Navigate to `http://localhost:3835/` (or reload an already-open page)
3. Wait up to ~2 seconds for the health request to fail

**Expected Result:**
- The header badge turns red and reads "Backend unavailable"
- The badge does NOT show "Backend OK", a provider value, a seed date, or a symbol count — no fabricated healthy status appears
- The page itself still renders (sidebar + empty-state card remain visible); only the badge reflects the outage

---

### UT-14 — Dense-dark analytical theme is applied (ux)

**Type:** ux
**Priority:** P2
**Surface:** `app/globals.css` (all routes)

**Preconditions:**
- Frontend running at http://localhost:3835

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Observe the overall page palette and layout

**Expected Result:**
- The page background is near-black (dense dark theme, approx `#0a0e14`) — not a white/light default theme
- Accent elements (the brand dot next to "Trendora", the active-link accent dot) are teal (approx `#4fd1c5`)
- Layout is a fixed left sidebar plus a main content area with a top header bar (not a single full-width column)

---

### UT-15 — Health badge re-checks and stays consistent across navigation (regression / ux)

**Type:** regression
**Priority:** P2
**Surface:** `HealthBadge` (header persistence)

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running and reachable

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Confirm the badge reads "Backend OK"
3. Click the "Stocks" link, then the "Watchlist" link in the sidebar

**Expected Result:**
- The header (with the health badge) remains persistently visible across all navigations — it does not disappear or re-flash a full-page loading screen between sections
- The badge continues to read "Backend OK" with "provider: seed", "seed 2026-05-28", and "158 symbols" on each page
- The active sidebar highlight follows the current section on each click

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads (shell + empty state) | smoke | P1 | `/` |
| UT-02 | All 7 sidebar destinations present | smoke | P1 | sidebar |
| UT-03 | Sidebar navigation + active highlight | happy-path | P1 | sidebar / all routes |
| UT-04 | Stocks empty state | smoke | P1 | `/stocks` |
| UT-05 | Themes empty state | smoke | P1 | `/themes` |
| UT-06 | Sectors empty state | smoke | P1 | `/sectors` |
| UT-07 | Scanner Runs empty state | smoke | P1 | `/scanner-runs` |
| UT-08 | System Health empty state | smoke | P1 | `/system-health` |
| UT-09 | Watchlist empty state | smoke | P1 | `/watchlist` |
| UT-10 | Stock detail stub resolves | smoke | P1 | `/stocks/[ticker]` |
| UT-11 | Run detail stub resolves | smoke | P1 | `/scanner-runs/[runId]` |
| UT-12 | Health badge connected (live values) | happy-path | P1 | header badge |
| UT-13 | Health badge "Backend unavailable" | error | P1 | header badge |
| UT-14 | Dense-dark analytical theme applied | ux | P2 | globals.css |
| UT-15 | Header/badge persists across nav | regression | P2 | header badge |

**P1 tests (UT-01 … UT-13) must all pass for browser QA verdict to be PASS.**

**Regression note:** This is the first iteration that produces any UI; there is no prior UI behavior to regress. UT-15 instead verifies the persistent-shell/header behavior holds across navigation. All 11 target journeys (J-01…J-11) remain `failing` by design — these UI tests verify only that the shell renders, navigates, and reports backend connectivity.
