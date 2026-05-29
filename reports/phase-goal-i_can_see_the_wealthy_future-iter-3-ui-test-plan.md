# Phase goal-i_can_see_the_wealthy_future-iter-3 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3836

---

> **Port note:** This task was dispatched with the frontend at **http://localhost:3836**. The functional test plan (`reports/qa/.../-test-plan.md`) and the iter-3 spec reference port **3835**. The managed `next dev` port has drifted between iterations and has caused two prior SKIP-vs-PASS flaps. **Before recording any verdict, confirm which port `next dev` is actually serving** (open the base URL; if 3836 is dead, try 3835) and use that port for every step below. All URLs are written for `3836` — substitute the live port if it differs.

> **Scope note:** This plan covers only the user-visible (browser) surfaces in the UI surface map. Pure API behaviour (envelope shape, 503/404 status codes, byte-identical list-vs-detail JSON) is already covered by the functional test plan (TC-01…TC-09, TC-18) and is **not** duplicated here. Where a UI test depends on a backend state (e.g. backend stopped), it is framed as an operator-observable outcome, not an API assertion.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Stock Leaderboard loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3836
- Backend up with seed data loaded (latest_data_date not null)

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Wait for the page to fully load

**Expected Result:**
- A dense dark ranked table renders (no blank screen, no error card)
- A column header row shows: `#`, `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Setup`, `Reason`
- An "as of {date}" badge is visible near the top
- A `visible / total` count is shown (e.g. `122 / 122`)
- No "Backend unavailable" red card is present

---

### UT-02 — Stock Leaderboard shows ranked rows with three scores + setup + reason (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Read the first data row (rank `#1`)
3. Read the next 4 rows

**Expected Result:**
- At least 2 data rows render (current seed: 122 rows)
- The first row shows rank `1`; ranks increase by 1 down the table
- Each row shows: a ticker, a sector name, three `ScoreBadge`s (each a letter A–E **and** a number) under Leadership / Entry Quality / Risk, a setup-status badge (one of: Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist), and a non-empty Reason text cell
- Rows are ordered by Leadership in non-increasing order (the #1 row's Leadership number ≥ the #2 row's)

---

### UT-03 — Sector filter narrows the leaderboard to one sector (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — Sector `<Select>`

**Preconditions:**
- `/stocks` loaded with the full table (note the total count, e.g. `122`)

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Note the current `visible / total` count (e.g. `122 / 122`)
3. Click the "Sector" dropdown
4. Select "Technology"

**Expected Result:**
- The table re-displays only rows whose Sector cell reads "Technology"
- The `visible / total` count's left number drops below the total (e.g. `12 / 122`); the total (right number) stays the same
- The score numbers on the remaining rows are unchanged from what they showed before filtering (client-side re-display, not a recompute)
- No page reload / no spinner that never resolves

---

### UT-04 — Setup filter to a populated status narrows rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — Setup `<Select>`

**Preconditions:**
- `/stocks` loaded with the full table

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Click the "Setup" dropdown
3. Select "Breakout-watch"

**Expected Result:**
- The table re-displays only rows whose Setup badge reads "Breakout-watch"
- The `visible / total` left number drops accordingly
- **If** "Breakout-watch" has zero rows on the current seed, the "No stocks match these filters" empty state appears instead (acceptable) — but a status with members must show only that status's rows

---

### UT-05 — Setup filter "Actionable" shows honest empty state on extended market (happy path / honest-empty)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — Setup `<Select>` + `EmptyState`

**Preconditions:**
- `/stocks` loaded; current seed market is "extended" (no Actionable candidates expected)

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Click the "Setup" dropdown
3. Select "Actionable"

**Expected Result:**
- Either: only rows with a setup badge of "Actionable" are shown, **or** (expected on the current seed) the explicit text "No stocks match these filters" is displayed
- **No fabricated rows** are shown — the table body is empty when no row matches; it does NOT silently fall back to showing all rows or a placeholder ticker

---

### UT-06 — Combined sector + setup filters compose; clearing restores full table (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks` — both `<Select>`s

**Preconditions:**
- `/stocks` loaded

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Select "Technology" in the "Sector" dropdown
3. Select "Extended" in the "Setup" dropdown
4. Note the `visible / total` count
5. Set the "Sector" dropdown back to its all/default option and the "Setup" dropdown back to its all/default option

**Expected Result:**
- After step 3, only rows that are BOTH Technology AND Extended show (the left count is ≤ the Technology-only count)
- After step 5, the `visible / total` left number returns to the full total (e.g. `122 / 122`) and all rows are shown again

---

### UT-07 — Ticker link navigates to the stock detail page (happy path / navigation)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — `StockTableRow` ticker `Link`

**Preconditions:**
- `/stocks` loaded with NVDA present in the table

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Click the "NVDA" ticker link in its row

**Expected Result:**
- The browser navigates to `http://localhost:3836/stocks/NVDA`
- The Stock Detail page for NVDA renders (three score cards visible — see UT-10)

---

### UT-08 — Risk badge is colour-inverted vs Leadership (ux / display)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks` — `Risk` `ScoreBadge` (invert option)

**Preconditions:**
- `/stocks` loaded

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Find a row whose Risk number is high (top of the A/B band, e.g. ≥ 70)
3. Inspect that row's Risk badge colour
4. Find a row whose Leadership number is high (≥ 70) and inspect its Leadership badge colour

**Expected Result:**
- A high **Risk** badge renders in a red / danger colour (high = dangerous)
- A high **Leadership** badge renders in a green / positive colour
- The two are visibly opposite — Risk colour direction is inverted relative to Leadership/Entry Quality (intentional, not a bug)

---

### UT-09 — Stock Leaderboard surfaces an explicit error when backend is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/stocks` — "Backend unavailable" `Card`

**Preconditions:**
- Frontend running; backend API **stopped** (or unreachable)

**Steps:**
1. Stop the backend API process
2. Navigate to `http://localhost:3836/stocks`
3. Wait for the page to settle

**Expected Result:**
- A red "Backend unavailable" card is shown
- **No** data rows and **no** fabricated/placeholder tickers appear
- The page does not crash to a blank screen or an unhandled Next.js error overlay

---

### UT-10 — Stock Detail renders three score cards with raw value, bucket, caption, components (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` — `ScoreCard` ×3

**Preconditions:**
- Backend up with seed data; NVDA in the universe

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Wait for the page to load
3. Read each of the three score cards

**Expected Result:**
- A header card shows NVDA's setup status + reason
- Three score cards render, labelled Leadership, Entry Quality, and Risk
- Each card shows: a large raw value in the form `NN.NN / 100`, an A–E `ScoreBadge`, a caption explaining the score's direction, and a component breakdown
- A "Back to leaderboard" link is present
- A note indicates the price chart / invalidation detail arrives in a later iteration (iter-4)

---

### UT-11 — Stock Detail scores match the leaderboard exactly (J-06 single source) (regression / critical)

**Type:** regression
**Priority:** P1 (CRITICAL — single-source anti-goal)
**Surface:** `/stocks` ↔ `/stocks/[ticker]`

**Preconditions:**
- Backend up with seed data

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Locate the NVDA row and write down its three numbers AND three A–E letters: Leadership `__ / _`, Entry Quality `__ / _`, Risk `__ / _`
3. Click the NVDA ticker link (or navigate to `http://localhost:3836/stocks/NVDA`)
4. Read the three numbers and three A–E letters on the detail page

**Expected Result:**
- All three raw numbers on the detail page equal the leaderboard's NVDA numbers (to the displayed precision)
- All three A–E buckets match exactly
- **Any** mismatch = FAIL (single-source violation — the score must be computed once and read identically)

---

### UT-12 — Stock Detail component breakdown shows ≥3 named components; NA component not fabricated (ux / explainability)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks/[ticker]` — `ComponentBreakdown`

**Preconditions:**
- `/stocks/NVDA` loaded

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Inspect / expand the component breakdown under one of the three score cards
3. Read the component rows

**Expected Result:**
- At least 3 named components appear, each with a human-readable label (e.g. "RS vs benchmark", "Sector RS", "Theme RS", "MA stack", "Distance from high") and a value
- Component keys render as human labels, NOT as raw keys like `rs_sector` / `ma_participation`
- If a `gap_climax` (earnings-gap) component is shown, it is marked unavailable / NA — **not** displayed as a fabricated number

---

### UT-13 — Unknown ticker shows a graceful "Unknown ticker" card, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/stocks/[ticker]` — "Unknown ticker" `Card`

**Preconditions:**
- Backend up with seed data

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NOTREAL`
2. Wait for the page to settle

**Expected Result:**
- A warn/info "Unknown ticker" card is shown
- A link back to the leaderboard is present
- The page does NOT crash to a blank screen or an unhandled error overlay; no fabricated score cards render

---

### UT-14 — "Back to leaderboard" link returns to /stocks (navigation)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks/[ticker]` — "Back to leaderboard" `Link`

**Preconditions:**
- `/stocks/NVDA` loaded

**Steps:**
1. Navigate to `http://localhost:3836/stocks/NVDA`
2. Click the "Back to leaderboard" link

**Expected Result:**
- The browser navigates to `http://localhost:3836/stocks`
- The full ranked leaderboard table renders again

---

### UT-15 — Theme Leaderboard loads and ranks ≥3 themes non-increasing (smoke + happy path)

**Type:** smoke
**Priority:** P1
**Surface:** `/themes`

**Preconditions:**
- Backend up with seed data

**Steps:**
1. Navigate to `http://localhost:3836/themes`
2. Wait for the page to load
3. Read the Theme Score column top to bottom

**Expected Result:**
- A ranked table renders with columns: `#`, `Theme`, `Theme Score`, `1m`, `3m`, `Breadth`, `Trend`, and an expand chevron
- At least 3 theme rows are shown (current seed: 11)
- Theme Score values are non-increasing down the table (row 1 ≥ row 2 ≥ …)
- A "breadth is universe-relative" badge and a "Price-confirmed, not news-driven" caption are visible
- No "Backend unavailable" card

---

### UT-16 — Top theme row shows numeric returns, breadth %, trend label (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/themes` — metrics columns

**Preconditions:**
- `/themes` loaded

**Steps:**
1. Navigate to `http://localhost:3836/themes`
2. Read the `#1` (top) theme row's `1m`, `3m`, `Breadth`, and `Trend` cells

**Expected Result:**
- The `1m` cell shows a numeric return (e.g. `+4.2%` or `-1.1%`), not blank
- The `3m` cell shows a numeric return
- The `Breadth` cell shows a percentage (e.g. `64%`) or an explicit `NA`
- The `Trend` cell shows a non-empty trend label

---

### UT-17 — Theme row expands to show member chips + component breakdown, then collapses (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/themes` — `ThemeRows` expandable row

**Preconditions:**
- `/themes` loaded

**Steps:**
1. Navigate to `http://localhost:3836/themes`
2. Click the top theme row (or its expand chevron)
3. Observe the expanded content
4. Click the same row / chevron again

**Expected Result:**
- After step 2, the row expands to reveal member-ticker chips and a `ComponentBreakdown` with named components (human labels, e.g. "Breadth", "MA participation", "Theme RS" — not raw keys)
- After step 4, the row collapses back to a single line

---

### UT-18 — Theme Leaderboard surfaces explicit error when backend is down (error)

**Type:** error
**Priority:** P2
**Surface:** `/themes` — "Backend unavailable" `Card`

**Preconditions:**
- Frontend running; backend API **stopped**

**Steps:**
1. Stop the backend API process
2. Navigate to `http://localhost:3836/themes`
3. Wait for the page to settle

**Expected Result:**
- A red "Backend unavailable" card is shown
- No theme rows and no fabricated data appear
- No blank screen / no unhandled error overlay

---

### UT-19 — Dashboard shows real Candidate Counts (J-01) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `CandidateCountsCard`

**Preconditions:**
- Backend up with seed data

**Steps:**
1. Navigate to `http://localhost:3836/`
2. Locate the "Candidate Counts" card

**Expected Result:**
- A "Candidate Counts" card renders with three rows: Actionable, Breakout-watch, Pullback-watch
- Each row shows a number (Actionable may legitimately be `0` on the current extended market)
- The card shows real numbers, NOT a "pending" placeholder

---

### UT-20 — Dashboard shows real Top Themes list with score badges (J-01) (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `Top Themes` `Card`

**Preconditions:**
- `/` loaded

**Steps:**
1. Navigate to `http://localhost:3836/`
2. Locate the "Top Themes" card

**Expected Result:**
- A "Top Themes" card lists at least 3 themes
- Each entry shows a rank, a theme name, a trend label, and a `ScoreBadge`
- The card shows real themes, NOT a "pending" placeholder
- The themes shown match the top entries of `/themes` (same names/order at the top)

---

### UT-21 — Dashboard regime / sectors / breadth / as-of still render after iter-3 changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Market Regime, Top Sectors, breadth, "Data as-of"

**Preconditions:**
- `/` loaded (dashboard now also fetches `/api/themes`)

**Steps:**
1. Navigate to `http://localhost:3836/`
2. Inspect the Market Regime card, the Top Sectors list, the breadth metrics, and the "Data as-of" badge

**Expected Result:**
- The Market Regime card shows a regime label + score (unchanged from iter-2)
- The Top Sectors list shows ≥3 sectors each with a score
- A breadth % renders, labelled universe-relative
- A "Data as-of" / last-scan timestamp renders
- None of these regressed or went blank after the new Candidate Counts / Top Themes cards were added

---

### UT-22 — Sector Leaderboard unaffected by labels.py extraction (J-04 regression)

**Type:** regression
**Priority:** P1 (J-04 must stay green)
**Surface:** `/sectors`

**Preconditions:**
- Backend up with seed data

**Steps:**
1. Navigate to `http://localhost:3836/sectors`
2. Read the ranked sector rows (scores, A–E buckets, labels)
3. Expand one sector's component breakdown

**Expected Result:**
- The Sector Leaderboard renders ranked sectors with scores, A–E buckets, and labels exactly as in iter-2 (the `labels.label_for` extraction must not change the output)
- Ordering is non-increasing by score; labels match the iter-2 appearance
- Component breakdown still expands and shows named components
- No layout or value regression

---

### UT-23 — New capability is discoverable from navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / nav skeleton

**Preconditions:**
- App loaded

**Steps:**
1. Navigate to `http://localhost:3836/`
2. Inspect the navigation (sidebar / top nav)
3. Click the "Stocks" nav item, then the "Themes" nav item

**Expected Result:**
- Nav items for "Dashboard", "Stocks", "Sectors", and "Themes" are visible (nav skeleton unchanged from prior iterations)
- Clicking "Stocks" navigates to `http://localhost:3836/stocks` (now a full leaderboard, not an empty stub)
- Clicking "Themes" navigates to `http://localhost:3836/themes` (now a full leaderboard, not an empty stub)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stock Leaderboard loads | smoke | P1 | `/stocks` |
| UT-02 | Ranked rows: 3 scores + setup + reason | happy-path | P1 | `/stocks` |
| UT-03 | Sector filter narrows rows | happy-path | P1 | `/stocks` |
| UT-04 | Setup filter (populated status) | happy-path | P1 | `/stocks` |
| UT-05 | Setup "Actionable" → honest empty state | happy-path | P1 | `/stocks` |
| UT-06 | Combined filters compose + clear restores | happy-path | P2 | `/stocks` |
| UT-07 | Ticker link → detail | happy-path | P1 | `/stocks` |
| UT-08 | Risk badge colour-inverted | ux | P2 | `/stocks` |
| UT-09 | Backend-down error card | error | P2 | `/stocks` |
| UT-10 | Detail: 3 score cards | happy-path | P1 | `/stocks/[ticker]` |
| UT-11 | Detail scores == leaderboard (J-06) | regression | P1* | `/stocks` ↔ detail |
| UT-12 | Detail components ≥3, NA not fabricated | ux | P2 | `/stocks/[ticker]` |
| UT-13 | Unknown ticker graceful card | error | P2 | `/stocks/[ticker]` |
| UT-14 | Back-to-leaderboard link | happy-path | P2 | `/stocks/[ticker]` |
| UT-15 | Themes load + ranked non-increasing | smoke | P1 | `/themes` |
| UT-16 | Top theme numeric metrics | happy-path | P1 | `/themes` |
| UT-17 | Theme row expand/collapse | happy-path | P1 | `/themes` |
| UT-18 | Themes backend-down error card | error | P2 | `/themes` |
| UT-19 | Dashboard real Candidate Counts | happy-path | P1 | `/` |
| UT-20 | Dashboard real Top Themes | happy-path | P1 | `/` |
| UT-21 | Dashboard regime/sectors/breadth regression | regression | P1 | `/` |
| UT-22 | Sector Leaderboard regression (J-04) | regression | P1 | `/sectors` |
| UT-23 | New surfaces discoverable from nav | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.**
**\* UT-11 is the critical single-source (J-06) check — any mismatch is a hard FAIL.**
</content>
