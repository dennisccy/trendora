# Phase goal-i_can_see_the_wealthy_future-iter-2 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835
**Backend URL:** http://localhost:8000

---

## Notes for the tester

- Two routes carry all user-visible change this iteration: **`/sectors`** (ranked leaderboard) and **`/` (Dashboard)** (regime + breadth + Top Sectors). No new navigation links were added — both routes pre-existed as empty states in the sidebar.
- Expected reference values against the frozen seed (data-as-of **2026-05-28**): regime label ≈ **"Risk-on"**, regime score ≈ **74.32**. Use these as a sanity anchor, but the P1 pass criteria below are written to tolerate any valid value (one of the six labels, score 0–100), not the exact number.
- These tests do NOT duplicate the API/unit tests in `reports/qa/...-test-plan.md` (TC-01…TC-14). They cover only what is visible in the browser.
- "Stop the backend" steps require operator access to the backend process. If you cannot stop the backend, mark the error-state tests (UT-15, UT-16) as *blocked*, not *failed*.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/sectors` page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running and reachable at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the loading skeleton (8 grey pulsing bars) to be replaced by content

**Expected Result:**
- The heading "Sectors" is visible with the subtitle starting "Sector / industry Leaderboard — ranked by Sector Score"
- A table with column headers `#`, `Ticker`, `Kind`, `Sector Score`, `RS vs SPY`, `Dist. 52w high`, `Trend` is visible
- No blank screen, no red "Backend unavailable" card, no browser console errors

---

### UT-02 — `/` Dashboard page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running and reachable

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the loading skeleton to be replaced by content

**Expected Result:**
- The heading "Dashboard" with subtitle "The daily snapshot at a glance" is visible
- A card titled "Market Regime", three breadth metric cards, a "Top Sectors" card, and "Candidate Counts" + "Top Themes" cards are all visible
- No blank screen, no red "Backend unavailable" card, no browser console errors

---

### UT-03 — `/sectors` shows a ranked leaderboard ordered by score (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- Frontend and backend running; frozen seed loaded

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Wait for the table to render
3. Read the `#` column top-to-bottom and the `Sector Score` raw number (the small number next to each A–E badge) top-to-bottom

**Expected Result:**
- At least 10 ticker rows are present
- The `#` column counts up 1, 2, 3, … with no gaps
- The raw Sector Score number is **non-increasing** from the first row to the last row (each row's score ≤ the row above it)

---

### UT-04 — Top row exposes RS-vs-SPY, distance-from-high, and a trend label (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors`

**Preconditions:**
- `/sectors` loaded with rows visible (UT-03 passed)

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Read row `#1` (the top row) across all columns

**Expected Result:**
- The "RS vs SPY" cell shows a signed percentage like `+3.21%` or `-1.04%` (green if positive, red if negative; amber "NA" only if unavailable)
- The "Dist. 52w high" cell shows a percentage like `-4.50%`
- The "Trend" cell shows a non-empty text label (e.g. "Leading", "Improving", "Lagging", or "Weakening")
- None of these three cells is blank

---

### UT-05 — Sector Score cell shows a colour-graded A–E badge + raw number (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — `ScoreBadge`

**Preconditions:**
- `/sectors` loaded with rows visible

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Inspect the "Sector Score" column for the top row and several lower rows

**Expected Result:**
- Each Sector Score cell shows a letter badge (one of A, B, C, D, E) immediately followed by a two-decimal raw number (e.g. `A 82.40`)
- A/B badges are green, C badges are amber, D/E badges are red
- Higher-ranked (top) rows trend toward A/B (green); lower rows trend toward D/E (red)

---

### UT-06 — Clicking a row expands its component breakdown; keyboard works too (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/sectors` — expandable `SectorRows` + `ComponentBreakdown`

**Preconditions:**
- `/sectors` loaded with rows visible

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Click anywhere on row `#1`
3. Observe the area that appears directly below row `#1`
4. Click row `#1` again
5. Press `Tab` until row `#1` is focused (a focus ring/highlight appears on the row), then press `Enter`

**Expected Result:**
- After step 2: the chevron at the row's right end changes from `>` (right) to `v` (down), and an expanded panel appears below showing a one-line summary `TICKER — <name> · Sector Score <n> (bucket <X>)` plus a breakdown grid with column headers "Component", "Detail", "Contribution"
- The breakdown lists named rows such as "RS vs SPY · 1m", "RS vs SPY · 3m", "RS vs SPY · 6m", "MA stack", "Dist. from 52w high", "Volume trend" — each with a Detail (e.g. `pctl 85`) and a numeric Contribution
- After step 4: the panel collapses and the chevron returns to `>`
- After step 5: pressing Enter on the focused row toggles the same panel open (keyboard accessibility works)

---

### UT-07 — SPY appears only as the excluded benchmark, never as a ranked row (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/sectors` — benchmark badge + table rows

**Preconditions:**
- `/sectors` loaded with rows visible

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Scan the entire "Ticker" column for the value `SPY`
3. Read the badges in the header strip below the page subtitle

**Expected Result:**
- No table row has the ticker `SPY`
- The header strip shows a badge reading "RS benchmark: SPY (excluded)"
- The header strip also shows the instruction text "Click a row for its component breakdown."

---

### UT-08 — `/sectors` shows an honest "as of" date badge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/sectors` — as-of badge

**Preconditions:**
- `/sectors` loaded with rows visible

**Steps:**
1. Navigate to `http://localhost:3835/sectors`
2. Read the first badge in the header strip below the subtitle

**Expected Result:**
- A badge reading "as of 2026-05-28" is visible (the date must be a real `YYYY-MM-DD`, expected `2026-05-28`)

---

### UT-09 — Dashboard Market Regime panel shows a valid label + numeric score (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Market Regime panel

**Preconditions:**
- Dashboard loaded (UT-02 passed)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Read the large card titled "Market Regime" (top-left, spans two columns)

**Expected Result:**
- A coloured badge in the card header shows exactly one of: `Strong risk-on`, `Risk-on`, `Narrow leadership`, `Choppy`, `Risk-off`, `Defensive` (expected `Risk-on`)
- A large number with two decimals followed by "/ 100" is shown (expected ≈ `74.32`); the number is between 0.00 and 100.00
- Risk-on/Strong risk-on render green, Risk-off/Defensive render red, Narrow leadership/Choppy render amber

---

### UT-10 — Regime score carries a named component breakdown (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — regime `ComponentBreakdown`

**Preconditions:**
- Dashboard loaded

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Read the area below the regime score inside the "Market Regime" card

**Expected Result:**
- A breakdown grid with headers "Component", "Detail", "Contribution" is visible
- It lists named components such as "Index MA stack", "Breadth > 50-DMA", "Breadth > 200-DMA", "Net new highs", "VIX gate" — each with a numeric Contribution value
- The regime score is never shown as a bare unexplained number

---

### UT-11 — Three universe-relative breadth metric cards are shown (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `MetricCard` ×3

**Preconditions:**
- Dashboard loaded

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Read the three small cards stacked at the right of the regime row

**Expected Result:**
- Card 1 title "Breadth · above 50-DMA" with a `%` value (0.00–100.00)
- Card 2 title "Breadth · above 200-DMA" with a `%` value (0.00–100.00)
- Card 3 title "Net new highs" with a `%` value and a caption like `N hi / M lo`
- Each card shows an amber caption badge containing the text "universe-relative"

---

### UT-12 — Dashboard shows a "Data as-of" badge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — Data as-of badge

**Preconditions:**
- Dashboard loaded

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Read the badge at the top-right of the page, next to the "Dashboard" heading

**Expected Result:**
- A badge with a clock icon reading "Data as-of 2026-05-28" is visible (must be a real `YYYY-MM-DD`)

---

### UT-13 — Top Sectors card matches `/sectors` (single source of truth) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Top Sectors card vs `/sectors` table

**Preconditions:**
- Both backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3835/sectors`; note the ticker, A–E badge letter, and raw score of row `#1`
2. Navigate to `http://localhost:3835/`
3. Read the "Top Sectors" card (left card in the lower grid)

**Expected Result:**
- The Top Sectors card lists exactly 5 rows, each with a rank number, ticker, a trend label, and an A–E score badge with raw score
- The top entry's ticker, badge letter, and raw score are **identical** to row `#1` recorded on `/sectors` in step 1 (the dashboard sources the same data — no divergence)

---

### UT-14 — Candidate Counts & Top Themes show honest "pending" placeholders (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `PendingCard` ×2

**Preconditions:**
- Dashboard loaded

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Read the "Candidate Counts" card and the "Top Themes" card in the lower grid

**Expected Result:**
- "Candidate Counts" card shows an amber "pending" badge in its header and rows "Actionable", "Breakout-watch", "Pullback-watch" each with an em-dash (—) value — NOT `0`
- "Top Themes" card shows an amber "pending" badge and a row with an em-dash (—) — NOT `0`
- Both cards show the footnote "Arriving in a later iteration (per-stock & theme scoring)."

---

### UT-15 — `/sectors` shows "Backend unavailable" when the API is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/sectors` — error state

**Preconditions:**
- Frontend running; **backend stopped / unreachable** (operator access to stop the backend required)

**Steps:**
1. Stop the backend (or block port 8000)
2. Navigate to `http://localhost:3835/sectors`
3. Wait for loading to finish

**Expected Result:**
- A red-bordered card with a warning triangle and the bold text "Backend unavailable" appears
- The body text explains "No rankings are shown rather than fabricated values."
- **No table rows, no scores, and no fabricated tickers are shown**
- The page does not crash or go blank

---

### UT-16 — `/` Dashboard shows "Backend unavailable" when the API is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — error state

**Preconditions:**
- Frontend running; backend stopped / unreachable

**Steps:**
1. Stop the backend (or block port 8000)
2. Navigate to `http://localhost:3835/`
3. Wait for loading to finish

**Expected Result:**
- A red-bordered card with a warning triangle and the bold text "Backend unavailable" appears
- The body text explains "Nothing is fabricated — confirm the backend is running and reload."
- **No regime score, no regime label, no breadth numbers are shown**
- The page does not crash or go blank

---

### UT-17 — Top Sectors degrades independently of the regime panel (error)

**Type:** error
**Priority:** P3
**Surface:** `/` — Top Sectors degraded state

**Preconditions:**
- Backend running and serving `/api/dashboard` successfully, but `/api/sectors` failing (requires developer assistance to force only the sectors endpoint to error — e.g. temporarily break/route `/api/sectors`). If this cannot be staged, mark *blocked*.

**Steps:**
1. With `/api/dashboard` healthy but `/api/sectors` returning an error, navigate to `http://localhost:3835/`
2. Read the regime panel and the Top Sectors card

**Expected Result:**
- The Market Regime panel, breadth cards, and "Data as-of" badge still render normally (the dashboard fetch succeeded)
- The "Top Sectors" card alone shows the red text "Sector data unavailable — backend not reachable." — it does NOT take down the whole page

---

### UT-18 — New analytical pages are reachable from the sidebar (ux / discoverability)

**Type:** ux
**Priority:** P2
**Surface:** sidebar navigation

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3835/`
2. In the left sidebar, locate and click "Sectors"
3. Then in the left sidebar, click "Dashboard"

**Expected Result:**
- The sidebar shows a "Dashboard" link and a "Sectors" link (among others)
- Clicking "Sectors" navigates to `http://localhost:3835/sectors` and shows the ranked table; the "Sectors" link is highlighted as active
- Clicking "Dashboard" returns to `http://localhost:3835/` and shows the regime panel; the "Dashboard" link is highlighted as active

---

### UT-19 — Unrelated sidebar routes still render their empty states (regression)

**Type:** regression
**Priority:** P3
**Surface:** other sidebar routes (e.g. `/stocks`, `/themes`, `/watchlist`)

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Click "Stocks" in the sidebar
3. Click "Themes" in the sidebar

**Expected Result:**
- `/stocks` and `/themes` still load their pre-existing empty/placeholder states without errors (these were intentionally NOT changed this iteration)
- No crash, no "Backend unavailable" card bleeding into these routes, no blank screen — confirming the two changed routes did not regress the others

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/sectors` loads | smoke | P1 | `/sectors` |
| UT-02 | `/` Dashboard loads | smoke | P1 | `/` |
| UT-03 | Ranked leaderboard descending | happy-path | P1 | `/sectors` |
| UT-04 | Top row RS / dist / trend | happy-path | P1 | `/sectors` |
| UT-05 | A–E colour-graded score badge | happy-path | P1 | `/sectors` |
| UT-06 | Expand row → component breakdown (+keyboard) | happy-path | P1 | `/sectors` |
| UT-07 | SPY excluded; benchmark badge | ux | P2 | `/sectors` |
| UT-08 | "as of" date badge | ux | P2 | `/sectors` |
| UT-09 | Regime label + numeric score | happy-path | P1 | `/` |
| UT-10 | Regime component breakdown | happy-path | P1 | `/` |
| UT-11 | 3× universe-relative breadth cards | happy-path | P1 | `/` |
| UT-12 | Data as-of badge | ux | P2 | `/` |
| UT-13 | Top Sectors = `/sectors` (single source) | happy-path | P1 | `/` |
| UT-14 | Pending placeholders (no fake zeros) | ux | P2 | `/` |
| UT-15 | `/sectors` backend-unavailable state | error | P2 | `/sectors` |
| UT-16 | `/` backend-unavailable state | error | P2 | `/` |
| UT-17 | Top Sectors degrades independently | error | P3 | `/` |
| UT-18 | Sidebar discoverability | ux | P2 | nav |
| UT-19 | Other routes not regressed | regression | P3 | other routes |

**P1 tests (UT-01 through UT-06, UT-09 through UT-11, UT-13) must all pass for the browser QA verdict to be PASS.**
