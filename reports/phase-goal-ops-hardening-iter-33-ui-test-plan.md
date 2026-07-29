# Phase goal-ops-hardening-iter-33 — UI Test Plan

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (started via `scripts/start-frontend.sh`, NOT `scripts/dev.sh`)

---

## Context

This iteration fixed `scripts/start-frontend.sh` so it genuinely serves a Next.js **production**
build (`next build` + `next start`) instead of silently running `next dev` while claiming to be
"prod mode." Per the UI surface map, **no page/component source changed** — the same 11 pages the
goal's J-06 journey already tracks are affected only by their **serving mode**: production builds
never ship the Next.js dev-mode error-overlay pill, and (per AG-3) the served data must be
byte-identical to before the fix.

Because there is no new capability, this plan is weighted toward smoke coverage of all 11 affected
pages (each testable independently), plus regression checks on data-bearing pages (AG-3), one
happy-path cross-page workflow, one UX discoverability check (nav is unchanged this iteration, so
this doubles as a nav-regression check), and one dedicated console/dev-overlay check — the direct
user-visible signature of the fix. There is no validation-type case: no form was added or changed
this iteration.

**IMPORTANT — precondition for every test below:** the frontend under test must have been started
via `scripts/start-frontend.sh` (the launcher this iteration fixed), not `scripts/dev.sh`. If the
instance at http://localhost:3255 was started with `scripts/dev.sh` instead, these tests are
checking the wrong thing — the dev-overlay-pill assertions in particular will not be meaningful.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Dashboard loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3255 via `scripts/start-frontend.sh` (prod mode)
- Backend is running and healthy on its configured port

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or an application-error page
- The heading "Dashboard" is visible, with the subtitle "The daily snapshot at a glance"
- No Next.js dev-mode error-overlay pill appears anywhere on the page (bottom corner or full-screen)
- Browser DevTools console shows zero error-level (`console.error`) entries

---

### UT-02 — Stocks leaderboard loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Stocks" is visible, with subtitle beginning "Stock Leaderboard — ranked by
  Leadership..."
- The leaderboard table renders with populated ranked rows, OR — if no rows exist for the current
  as-of date — the honest empty state "No ranked stocks at this date" is shown (never a blank table
  with no message)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-03 — Stock detail page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:**
- AAPL exists in the current ranked/scored universe (seed data)
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Wait for the page to fully load

**Expected Result:**
- The heading "AAPL" is visible, with subtitle "Stock detail — the three explainable scores..."
- Three score cards titled "Leadership", "Entry Quality", and "Risk" are all visible with either a
  numeric score or an honest NA state (never blank)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-04 — Sectors leaderboard loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/sectors`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Sectors" is visible, with subtitle beginning "Sector / industry Leaderboard —
  ranked by Sector Score..."
- The table header row includes the column "Sector Score", and rows are populated (or the honest
  "No ranked sectors" empty state is shown)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-05 — Themes leaderboard loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/themes`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Themes" is visible, with subtitle beginning "Theme Leaderboard — ranked by a
  price-confirmed Theme Score..."
- The table renders populated rows with columns including "Theme", "1m", "3m", "Breadth" (or the
  honest "No ranked themes" empty state)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-06 — Data Manager loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load
3. Scroll down until the "Run history" panel is visible

**Expected Result:**
- The heading "Data Manager" is visible, with subtitle beginning "Grow the dataset on demand..."
- The "Run history" panel renders (populated with past jobs, or an honest empty state if none exist)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-07 — Evidence ledger loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Evidence" is visible, with subtitle mentioning "the certified-claims ledger"
- The ledger list/table renders with entries, or the honest empty state "No certified claims yet"
  is shown (never a blank page)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-08 — Scanner Runs loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Scanner Runs" is visible, with subtitle "History of immutable, dated scan
  snapshots..."
- The runs list renders populated rows, or the honest "No scanner runs yet" empty state
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-09 — Backtest loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Backtest" is visible, with subtitle beginning "Time-machine to a past scan date..."
- The "As-of scan summary" section renders, and the "Forward-test scorecard" section renders with
  figures (or the honest "Backtest evidence not yet computed" / "No elapsed forward window for
  this date yet" states)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-10 — Watchlist loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Watchlist" is visible, with subtitle beginning "Your saved stocks..."
- The watchlist table renders (populated with saved tickers, or the honest "Your watchlist is
  empty" state)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-11 — Regime Lab loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Research — Regime Lab" is visible, with subtitle beginning "How have stocks'
  realized forward returns and downside risk differed across the market regime?"
- The decile/regime-label table renders with data (or an honest "no observations" state)
- No dev-mode error-overlay pill; zero error-level console entries

---

### UT-12 — User can browse from Dashboard to a stock's detail page (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `/stocks` → `/stocks/AAPL`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy
- AAPL exists in the current ranked universe

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Click "Stocks" in the left sidebar navigation
3. Type "AAPL" into the search field at the top of the leaderboard (placeholder text "Search
   ticker or name…", `aria-label` "Search by ticker or company name")
4. Click the "AAPL" row in the filtered leaderboard table

**Expected Result:**
- After step 2: browser is at `http://localhost:3255/stocks`, heading "Stocks" is visible
- After step 3: the table filters down to show only the AAPL row (or rows matching "AAPL")
- After step 4: browser navigates to `http://localhost:3255/stocks/AAPL`; heading "AAPL" is
  visible; the three score cards ("Leadership", "Entry Quality", "Risk") render
- This entire cross-page flow completes with no dev-mode error-overlay pill appearing at any step

---

### UT-13 — Sectors leaderboard still shows correct, populated evidence (regression / AG-3)

**Type:** regression
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy
- At least one prior screenshot or known-good reading of `/sectors` exists from before this
  iteration (e.g., the dev handoff's pre-fix baseline), if available for comparison

**Steps:**
1. Navigate to `http://localhost:3255/sectors`
2. Read the "Sector Score" value and "RS vs SPY" value for the top-ranked row (rank "1")
3. Read at least one forward-return column value (e.g., the "1" or "5" trading-day column) for
   that same row
4. If a pre-fix baseline reading is available, compare the values read in steps 2-3 against it

**Expected Result:**
- Every value read is a real number (or an explicit "NA"/"—" placeholder with its documented
  tooltip, e.g. "No realized forward return at this horizon yet (NA)") — never blank, `undefined`,
  `NaN`, or a raw error string
- If a pre-fix baseline is available, the values are byte-identical to it — the launcher's
  build-mode change must not alter any served figure (this is the AG-3 anti-goal this iteration is
  bound by: "displayed numbers are correct... not merely that the page renders")

---

### UT-14 — Watchlist and Concentration X-ray still render for existing saved tickers (regression / AG-3)

**Type:** regression
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- At least 2-3 tickers were previously saved to the watchlist (seed data or a prior session's
  saved list) — if the watchlist is empty, this test instead verifies the empty-state path (see
  Expected Result below)

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Confirm each saved ticker's row shows its Leadership / Entry / Risk figures, setup status, and
   reason text
3. Scroll to the "Concentration X-ray" section (if present)
4. Confirm the "Sector concentration", "Theme concentration", and "Shared setup" breakdowns render

**Expected Result:**
- If 2 or more names are saved: the "Concentration X-ray" heading is visible, with all three
  breakdown panels ("Sector concentration", "Theme concentration", "Shared setup") populated
- If fewer than the minimum required names are saved: the honest "Not enough names yet for an
  X-ray" message is shown instead of a blank/broken panel — either outcome is acceptable, but a
  blank panel with no message is a FAIL
- Each row's Leadership/Entry/Risk figures are real numbers or honest NA states, never blank

---

### UT-15 — Regime Lab is discoverable within 2 clicks from the Dashboard (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / `/research`

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh`; backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/` (Dashboard)
2. Click "Research" in the left sidebar navigation
3. On the Research index page, locate and click the card titled "Regime Lab"

**Expected Result:**
- After step 2: browser is at `http://localhost:3255/research`; heading "Research" is visible; a
  card titled "Regime Lab" with description text mentioning "market regimes" is visible among the
  lab cards
- After step 3: browser navigates to `http://localhost:3255/research/regime-lab`; heading
  "Research — Regime Lab" is visible
- Total clicks from Dashboard to Regime Lab: 2 (sidebar "Research" link, then the "Regime Lab"
  card) — confirms this iteration's launcher fix did not disturb the existing navigation path

---

### UT-16 — Zero error-level console entries and no dev-overlay pill on any of the 11 pages (error)

**Type:** error
**Priority:** P1
**Surface:** all 11 J-06 step-1 pages

**Preconditions:**
- Frontend running via `scripts/start-frontend.sh` (prod mode); backend healthy
- Browser DevTools console panel open and cleared before each page navigation

**Steps:**
1. Open DevTools (F12) and select the Console tab; clear the console
2. Navigate to each of the following URLs in turn, waiting for full load before moving to the
   next, and check the console after each:
   - `http://localhost:3255/`
   - `http://localhost:3255/stocks`
   - `http://localhost:3255/stocks/AAPL`
   - `http://localhost:3255/sectors`
   - `http://localhost:3255/themes`
   - `http://localhost:3255/data`
   - `http://localhost:3255/evidence`
   - `http://localhost:3255/scanner-runs`
   - `http://localhost:3255/backtest`
   - `http://localhost:3255/watchlist`
   - `http://localhost:3255/research/regime-lab`
3. On each page, visually check for the Next.js dev-mode error-overlay pill (a small colored
   button/badge in the bottom-left or bottom-right corner, or a full-screen overlay with a stack
   trace, that appears ONLY under `next dev`)

**Expected Result:**
- Zero red/error-level (`console.error`) entries appear in the DevTools console on any of the 11
  pages after load completes
- No Next.js dev-mode overlay pill or full-screen error overlay appears on any page — this is the
  direct, user-visible signature of the fix (production builds never ship this overlay); its
  presence on any page means the frontend is still being served by `next dev`, not `next start`,
  and the fix has not taken effect for that instance

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard smoke | smoke | P1 | `/` |
| UT-02 | Stocks leaderboard smoke | smoke | P1 | `/stocks` |
| UT-03 | Stock detail smoke | smoke | P1 | `/stocks/AAPL` |
| UT-04 | Sectors leaderboard smoke | smoke | P1 | `/sectors` |
| UT-05 | Themes leaderboard smoke | smoke | P1 | `/themes` |
| UT-06 | Data Manager smoke | smoke | P1 | `/data` |
| UT-07 | Evidence ledger smoke | smoke | P1 | `/evidence` |
| UT-08 | Scanner Runs smoke | smoke | P1 | `/scanner-runs` |
| UT-09 | Backtest smoke | smoke | P1 | `/backtest` |
| UT-10 | Watchlist smoke | smoke | P1 | `/watchlist` |
| UT-11 | Regime Lab smoke | smoke | P1 | `/research/regime-lab` |
| UT-12 | Dashboard → Stocks → Stock detail browse flow | happy-path | P1 | `/`, `/stocks`, `/stocks/AAPL` |
| UT-13 | Sectors evidence unchanged by launcher fix (AG-3) | regression | P1 | `/sectors` |
| UT-14 | Watchlist + X-ray still render (AG-3) | regression | P1 | `/watchlist` |
| UT-15 | Regime Lab discoverable in 2 clicks | ux | P3 | nav / `/research` |
| UT-16 | No console errors / no dev-overlay pill across all 11 pages | error | P1 | all 11 pages |

**P1 tests must all pass for browser QA verdict to be PASS.** Given this iteration's entire scope
is a serving-mode defect fix with an explicit AG-3 ("displayed numbers are correct") and DoD
("zero error-level console entries... no dev-overlay pill") requirement, nearly every case here is
P1 — there is no new capability whose failure would be merely cosmetic. Only UT-15 (nav
discoverability, unchanged this iteration) is P3.

**No validation-type test case is included**: no form was added or changed by this iteration (per
the UI surface map and plan's "UI Evolution: New user actions: none").
