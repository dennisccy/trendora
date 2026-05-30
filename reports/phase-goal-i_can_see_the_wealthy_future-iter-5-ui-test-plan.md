# Phase goal-i_can_see_the_wealthy_future-iter-5 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3836

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results. API-level checks (TC-01..TC-10) live in the functional test plan and are not duplicated here. -->

---

### UT-01 — `/scanner-runs` list page loads (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Frontend running at `http://localhost:3836`
- Backend running at `http://localhost:8000` with bootstrapped runs persisted

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs`
2. Wait for the page to fully load (the loading skeleton disappears)

**Expected Result:**
- The heading "Scanner Runs" is visible with the subtitle "History of immutable, dated scan snapshots — open one to see exactly what the scanner said on that date"
- A table renders with column headers "As of", "Regime", "Actionable", "Breakout-watch", "Pullback-watch", "Stocks"
- No red "Backend unavailable" card, no blank screen, no console errors

---

### UT-02 — Run list shows ≥2 dated rows newest-first (happy-path, J-08 entry)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Bootstrap has persisted the seed dates plus the latest date

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs`
2. Read the "As of" column top to bottom

**Expected Result:**
- At least 3 rows are present, including dates `2026-05-28`, `2025-04-04`, and `2022-10-07`
- The dates are ordered strictly newest-first (`2026-05-28` is the top row, `2022-10-07` near the bottom)
- Each "As of" cell is a clickable accent-coloured link

---

### UT-03 — Regime badges are colour-graded and labelled correctly (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs` — `RunTableRow` regime badge

**Preconditions:**
- Run list loaded (UT-02 passed)

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs`
2. Inspect the "Regime" cell of the `2026-05-28` row
3. Inspect the "Regime" cell of the `2025-04-04` and `2022-10-07` rows

**Expected Result:**
- The `2026-05-28` row shows a green "Risk-on" badge with a numeric score beside it (≈ `74.32`)
- The `2025-04-04` and `2022-10-07` rows each show a red "Risk-off" badge with a numeric score beside it (≈ `6.30` and `8.34` respectively)

---

### UT-04 — Risk-off rows read 0 Actionable; latest Risk-on row is non-zero (happy-path, J-07 at list level)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs` — Actionable column

**Preconditions:**
- Run list loaded

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs`
2. Read the "Actionable" column value for the `2025-04-04` row and the `2022-10-07` row
3. Read the "Actionable" column value for the `2026-05-28` row

**Expected Result:**
- The Actionable column reads exactly `0` for both Risk-off rows (`2025-04-04`, `2022-10-07`)
- The Actionable column reads a non-zero number for the `2026-05-28` Risk-on row

---

### UT-05 — Clicking an as-of date opens its immutable detail (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs` → `/scanner-runs/[runId]`

**Preconditions:**
- Run list loaded

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs`
2. Click the `2025-04-04` date link in the "As of" column

**Expected Result:**
- The URL changes to `http://localhost:3836/scanner-runs/<numeric-id>`
- A header strip with a lock icon reads "Immutable snapshot — as of 2025-04-04"
- The header sub-line shows "Stored exactly as scanned; never recomputed for today. Scanned … · provider … · benchmark …"

---

### UT-06 — Risk-off detail page: regime "Risk-off" and zero Actionable in stock table (happy-path, J-07)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs/[runId]` (a Risk-off run)

**Preconditions:**
- On a Risk-off run detail page (open `2025-04-04` via UT-05)

**Steps:**
1. From `http://localhost:3836/scanner-runs`, click the `2025-04-04` date link
2. Read the "Market Regime · as of 2025-04-04" card's badge and score
3. Read the "Candidate Counts" card's "Actionable" tile
4. Scroll the stored stock table and scan the entire "Setup" column top to bottom

**Expected Result:**
- The Market Regime card shows a red "Risk-off" badge and the score `6.30` over "/ 100"
- The Candidate Counts "Actionable" tile reads `0`; the "Risk-off-watchlist" tile shows a large count
- **No** row in the "Setup" column shows the badge "Actionable" — every setup is watchlist-only (e.g. "Risk-off-watchlist")

---

### UT-07 — Detail page renders regime breakdown + 3 breadth tiles (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/scanner-runs/[runId]` — regime panel, `ComponentBreakdown`, breadth `MetricCard` ×3

**Preconditions:**
- On any run detail page

**Steps:**
1. From `http://localhost:3836/scanner-runs`, click the `2026-05-28` date link
2. Inspect the "Market Regime" card body
3. Inspect the three metric cards in the right column

**Expected Result:**
- The Market Regime card shows a large numeric score, "/ 100", and a component breakdown (labelled component bars/rows)
- Three breadth tiles render titled "Breadth · above 50-DMA", "Breadth · above 200-DMA", and "Net new highs", each showing a `%` value (or `NA`) and a caption badge

---

### UT-08 — Stored rankings differ between an older run and the latest (happy-path, J-08)

**Type:** happy-path
**Priority:** P1
**Surface:** `/scanner-runs/[runId]` — stored stock table rankings

**Preconditions:**
- At least two dated runs reachable

**Steps:**
1. From `http://localhost:3836/scanner-runs`, click the `2022-10-07` date link
2. Note the top 3 tickers in the "Ticker" column (rows ranked 1–3, e.g. HUBB / REGN / AXON)
3. Click the "All runs" button
4. Click the `2026-05-28` date link
5. Note the top 3 tickers (e.g. MU / ARM / MRVL)

**Expected Result:**
- The top tickers and/or their per-stock scores differ between the `2022-10-07` run and the `2026-05-28` run
- This confirms each snapshot is a frozen as-of view, not a recomputation of today's data

---

### UT-09 — "All runs" back navigation works (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/scanner-runs/[runId]` — "All runs" back link

**Preconditions:**
- On any run detail page

**Steps:**
1. From `http://localhost:3836/scanner-runs`, click any date link to open a detail page
2. Click the "All runs" button (top-right, with a left-arrow icon)

**Expected Result:**
- The URL returns to `http://localhost:3836/scanner-runs`
- The run-list table is shown again

---

### UT-10 — Candidate counts include Risk-off-watchlist tile (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/scanner-runs/[runId]` — `CandidateCountsRow`

**Preconditions:**
- On a Risk-off run detail page

**Steps:**
1. From `http://localhost:3836/scanner-runs`, click the `2025-04-04` date link
2. Inspect the "Candidate Counts" card tiles

**Expected Result:**
- Four labelled tiles render: "Actionable", "Breakout-watch", "Pullback-watch", "Risk-off-watchlist"
- The footnote reads "Stored counts of the canonical per-stock setup statuses (zero Actionable in a Risk-off regime)."

---

### UT-11 — Stored stock scores reuse the leaderboard's ScoreBadge styling (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/scanner-runs/[runId]` stock table vs `/stocks`

**Preconditions:**
- Both detail page and live leaderboard reachable

**Steps:**
1. Open `http://localhost:3836/stocks` and note the Leadership/Entry Quality/Risk score-badge styling (A–E bucket + number)
2. Open `http://localhost:3836/scanner-runs/<a-run-id>` and inspect the Leadership/Entry Quality/Risk columns

**Expected Result:**
- The score badges in the stored run table render in the same A–E bucket + number style as the live leaderboard (Risk column rendered inverted, matching `/stocks`)

---

### UT-12 — Backend-unavailable list state (error)

**Type:** error
**Priority:** P2
**Surface:** `/scanner-runs`

**Preconditions:**
- Backend at `:8000` is stopped (or unreachable)

**Steps:**
1. Stop the backend (or simulate it being down)
2. Navigate to `http://localhost:3836/scanner-runs`

**Expected Result:**
- A red card appears reading "Backend unavailable" with the text "The scan-run history could not load from the API. No runs are shown rather than fabricated values. Confirm the backend is running and retry."
- No table rows and no fabricated/placeholder runs are shown

---

### UT-13 — Unknown run id shows honest 404 state (error)

**Type:** error
**Priority:** P2
**Surface:** `/scanner-runs/[runId]`

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs/999999`

**Expected Result:**
- A "Run not found" card appears reading "No scanner run exists with id 999999. It may never have been persisted — no run is fabricated to fill the gap."
- No regime panel, no stock table, no fabricated run is rendered

---

### UT-14 — Backend-unavailable detail state (error)

**Type:** error
**Priority:** P3
**Surface:** `/scanner-runs/[runId]`

**Preconditions:**
- Backend at `:8000` is stopped (network/500-class error, not a 404)

**Steps:**
1. Stop the backend
2. Navigate to `http://localhost:3836/scanner-runs/1`

**Expected Result:**
- A red "Backend unavailable" card appears reading "This run could not load from the API. Nothing is fabricated — confirm the backend is running and retry."
- No fabricated regime or stock data is shown

---

### UT-15 — J-01 Dashboard still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend + frontend running

**Steps:**
1. Navigate to `http://localhost:3836/`
2. Wait for the dashboard to load

**Expected Result:**
- The dashboard renders with the live market regime panel and real data (no blank screen, no error card)
- Behaviour is unchanged from before iter-5

---

### UT-16 — J-02 Stock leaderboard + filters still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Backend + frontend running

**Steps:**
1. Navigate to `http://localhost:3836/stocks`
2. Confirm the leaderboard table renders with score badges
3. Apply an available filter/sort control and confirm the table updates

**Expected Result:**
- The leaderboard renders real rows with Leadership/Entry Quality/Risk score badges and setup statuses
- Filtering/sorting behaves as before — no new errors introduced by iter-5

---

### UT-17 — J-03 Themes & J-04 Sectors still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/themes`, `/sectors`

**Preconditions:**
- Backend + frontend running

**Steps:**
1. Navigate to `http://localhost:3836/themes`; confirm the themes view renders real data
2. Navigate to `http://localhost:3836/sectors`; confirm the sectors view renders real data

**Expected Result:**
- Both pages render with real scored rows/cards and no error cards — unchanged from before iter-5

---

### UT-18 — J-05/J-06 Stock detail + list==detail consistency (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- Backend + frontend running

**Steps:**
1. Navigate to `http://localhost:3836/stocks` and note a ticker's six scores + bucket + setup (e.g. the top row)
2. Click into that ticker's detail page (`/stocks/[ticker]`)
3. Compare the detail page's scores/bucket/setup to what the leaderboard showed

**Expected Result:**
- The stock detail page loads with its price chart and score panels
- The same symbol's six scores, A–E buckets, and setup status are identical between the leaderboard and the detail page (single source of truth — no divergence)

---

### UT-19 — "Scanner Runs" is discoverable in the navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / sidebar

**Steps:**
1. Navigate to `http://localhost:3836/`
2. Look at the left navigation sidebar

**Expected Result:**
- A "Scanner Runs" navigation item is visible
- Clicking it navigates to `http://localhost:3836/scanner-runs` (Run Detail is reached from a row, not the top nav — by design)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | List page loads | smoke | P1 | `/scanner-runs` |
| UT-02 | ≥2 dated rows newest-first | happy-path | P1 | `/scanner-runs` |
| UT-03 | Regime badges colour-graded | happy-path | P1 | `/scanner-runs` |
| UT-04 | Risk-off rows read 0 Actionable | happy-path | P1 | `/scanner-runs` |
| UT-05 | Date link opens immutable detail | happy-path | P1 | `/scanner-runs/[runId]` |
| UT-06 | Risk-off detail: regime + zero Actionable (J-07) | happy-path | P1 | `/scanner-runs/[runId]` |
| UT-07 | Regime breakdown + 3 breadth tiles | happy-path | P2 | `/scanner-runs/[runId]` |
| UT-08 | Older vs latest rankings differ (J-08) | happy-path | P1 | `/scanner-runs/[runId]` |
| UT-09 | "All runs" back navigation | happy-path | P2 | `/scanner-runs/[runId]` |
| UT-10 | Risk-off-watchlist count tile | ux | P2 | `/scanner-runs/[runId]` |
| UT-11 | ScoreBadge styling matches leaderboard | ux | P3 | `/scanner-runs/[runId]` |
| UT-12 | Backend-unavailable list state | error | P2 | `/scanner-runs` |
| UT-13 | Unknown run id → 404 state | error | P2 | `/scanner-runs/[runId]` |
| UT-14 | Backend-unavailable detail state | error | P3 | `/scanner-runs/[runId]` |
| UT-15 | J-01 Dashboard regression | regression | P1 | `/` |
| UT-16 | J-02 Leaderboard + filters regression | regression | P1 | `/stocks` |
| UT-17 | J-03 Themes & J-04 Sectors regression | regression | P1 | `/themes`, `/sectors` |
| UT-18 | J-05/J-06 detail + consistency regression | regression | P1 | `/stocks/[ticker]` |
| UT-19 | "Scanner Runs" discoverable in nav | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.**
</content>
