# Phase goal-mcp-loop-iter-40 — UI Test Plan

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL (for precondition checks only):** http://localhost:8255

---

## Context

J-24 / B-201 adds a read-only "Risk budget" card to the Stock Detail page (`/stocks/{ticker}`) and 5
matching sortable columns to the `/stocks` leaderboard — ATR%, downside volatility, an overnight-gap
profile (median/p95/worst + overnight variance share), the worst historical 20-day window, and
distance-to-invalidation %, each with a "pXX of universe" percentile chip. Three new glossary entries
document the new components on `/methodology`. Everything is additive and read-only; no new page, no
nav change, no new user action.

**Known environment fact (confirmed by the QA pass that already ran this iteration, and independently
re-derived below):** the current 590-symbol seed universe's shortest-history ticker (`Q`, IPO
2025-10-27) still has ~170 trading days of history by the "Latest" as-of date — far more than the
20-day window the new gap/worst-window components require. This means the "short-history renders NA"
state (UT-09) could **not** be reproduced against any real ticker during the last QA pass (their
candidate, ARM, has 701 bars). Treat UT-09's result accordingly — it is a legitimate DoD requirement to
test, but a "not reproducible with current seed data" outcome is a data-availability note, not a UI
defect. This does not affect any other test case below.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Stock Detail page loads with the Risk budget card present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:**
- Frontend is running at http://localhost:3255 and the backend is reachable (top bar shows a green
  "Ready" badge, not a loading/error state)
- The backend's snapshot database has been rebuilt under this iteration's code so `GET
  /api/stocks/AAPL` returns a non-null `risk_budget` object (confirmed true as of the last QA pass —
  if this is not true in your environment, the card will be silently absent; see UT-10's "Expected
  Result" for what that looks like and is not a bug in that case)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Wait for the loading skeleton (animated gray placeholder cards) to disappear
3. Confirm the page heading reads "AAPL"
4. Scroll down past the card containing the labels "THEMES" and "INVALIDATION"

**Expected Result:**
- A card titled "Risk budget" is visible directly below the Themes/Invalidation card and above the
  "VCP pattern" card
- The card's intro paragraph contains the exact phrase "Descriptive only; not a recommendation."
- No "Backend unavailable" error banner appears, and the page is not blank
- No browser console errors

---

### UT-02 — Risk budget card shows all six metrics with real values and percentile chips (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:** Same as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Inside the "Risk budget" card, locate the grid of 6 metric tiles
3. Read the label and value shown on each tile: "ATR %", "Downside volatility", "Worst 20-day
   window", "Distance to invalidation", "Overnight gap · p95", "Overnight share of 20d variance"
4. For each tile, check whether a smaller gray line below the value reads "pXX of universe"

**Expected Result:**
- All 6 tiles show a real numeric value ending in "%" — never blank, and never the text "NA" (at the
  last verified check: ATR % = "2.84%", Downside volatility = "1.15%", Worst 20-day window =
  "-67.03%", Distance to invalidation = "0.58%"; exact figures may drift slightly on a fresh snapshot
  rebuild, but every tile must show a real percentage)
- The "Overnight gap · p95" tile shows a line "p95 X.XX%" plus a smaller line underneath reading
  "median X.XX% · worst X.XX%"
- Every one of the 6 tiles shows a "pXX of universe" chip beneath its value (e.g. "p40 of universe") —
  a real value with no percentile chip would indicate a bug
- No tile shows the warn-colored (amber) text "NA — insufficient history"

---

### UT-03 — `/stocks` leaderboard shows the 5 new risk-budget columns with real values (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Same as UT-01
- The leaderboard has rows visible for the "Latest" as-of date (row-count indicator near the search
  box reads something like "590 / 590")

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the table to finish loading
3. Scroll the table horizontally to the right (the table has its own internal scrollbar) until you
   pass the "Proximity to 52w high" column
4. Read the next 5 column headers, left to right

**Expected Result:**
- The 5 headers appear in this exact order, between "Proximity to 52w high" and "Setup": "ATR%",
  "Downside vol", "Gap p95", "Worst 20d", "Dist. to invalidation"
- Every cell under these 5 headers shows either a right-aligned "%"-suffixed number or the muted gray
  text "NA" — never a blank cell
- The AAPL row shows a real (non-"NA") value in all 5 of these columns

---

### UT-04 — Leaderboard value matches the Stock Detail card value for the same stock (single source, happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` + `/stocks/AAPL`

**Preconditions:** Same as UT-03.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Type "AAPL" into the search box labeled "Search ticker or name…"
3. In the filtered AAPL row, record the exact number shown in the "ATR%" column cell and the "Worst
   20d" column cell
4. Click the "AAPL" link in the Ticker column (this opens `/stocks/AAPL` in a **new browser tab** —
   switch to it)
5. In the new tab, locate the "ATR %" tile and the "Worst 20-day window" tile inside the "Risk budget"
   card
6. Compare both numbers recorded in step 3 to the two tile values

**Expected Result:**
- The leaderboard's "ATR%" cell value is IDENTICAL (same digits, same decimal places, e.g. both read
  "2.84%") to the detail page's "ATR %" tile value
- The leaderboard's "Worst 20d" cell value is IDENTICAL to the detail page's "Worst 20-day window"
  tile value
- Neither comparison shows even a small rounding difference — both surfaces read the same stored
  number verbatim

---

### UT-05 — Risk-budget leaderboard columns are sortable; NA rows always sort last (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:** Same as UT-03.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the "Worst 20d" column header text once
3. Confirm an arrow icon appears next to "Worst 20d" and the row order changes
4. Scroll to the bottom of the table and check whether any visible rows show "NA" in the "Worst 20d"
   column
5. Click the "Worst 20d" column header text a second time
6. Confirm the arrow flips direction and the row order reverses

**Expected Result:**
- After step 3 (first click / ascending), rows are ordered by the "Worst 20d" numeric value; any row
  showing "NA" in that column is grouped at the very bottom of the table, never mixed into the middle
  or top
- After step 6 (second click / descending), the order of the real numeric values reverses, but any
  "NA" rows remain at the bottom — they do NOT jump to the top

---

### UT-06 — Leaderboard column header info icon shows the glossary definition (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:** Same as UT-03.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Locate the "Gap p95" column header
3. Click the small circular "i" info icon immediately to the right of the "Gap p95" header text (a
   separate icon from the sort-arrow)

**Expected Result:**
- A popup panel appears below the icon showing the bold term "overnight-gap profile", followed by a
  definition beginning "The distribution of overnight moves..."
- The panel includes a line starting with "WHERE:" mentioning "Stock Detail risk-budget card"
- The panel includes a threshold row reading "Gap window = 20 bars"
- Clicking anywhere outside the panel closes it

---

### UT-07 — `/methodology` Glossary shows the 3 new risk-budget terms, searchable (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/methodology`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable

**Steps:**
1. Navigate to `http://localhost:3255/methodology`
2. Scroll down to the "Glossary" section (a heading "Glossary" with a book icon)
3. Click into the search box labeled "Search terms and definitions…"
4. Type `overnight-gap`
5. Clear the box, then type `worst 20-day`
6. Clear the box, then type `distance-to-invalidation`

**Expected Result:**
- Step 4: exactly one result appears, under the category card titled "FACTOR LAB & STATISTICS" — term
  "overnight-gap profile" with a definition mentioning "median, p95 (a near-worst case), and worst
  gap" and a threshold line "Gap window = 20 bars"
- Step 5: exactly one result — term "worst 20-day window" with a threshold line "Window = 20 bars"
- Step 6: exactly one result — term "distance-to-invalidation %" with a definition mentioning "percent
  distance of the latest close above the invalidation level" and **no** threshold row underneath (this
  term has none configured)
- Every one of the 3 results shows a "WHERE:" line mentioning "Stock Detail risk-budget card"

---

### UT-08 — Methodology glossary counts stay additive-only (ux / low-risk regression)

**Type:** ux
**Priority:** P3
**Surface:** `/methodology`

**Preconditions:** Same as UT-07.

**Steps:**
1. Navigate to `http://localhost:3255/methodology`
2. Scroll to the "Glossary" heading
3. Read the small gray summary text to the right of the heading (format: "`<N>` terms across `<M>`
   categories — every word the UI uses, from this one config-backed catalog.")
4. Clear any search text, then count the category cards shown below (each is a bordered card with an
   uppercase title)

**Expected Result:**
- The summary text reads "... terms across 6 categories ..." — the category count is exactly 6 (no
  new category was created for the 3 new terms; they joined the pre-existing "Factor Lab &
  Statistics" category)
- The "FACTOR LAB & STATISTICS" category card's term list includes "overnight-gap profile", "worst
  20-day window", and "distance-to-invalidation %" alongside the pre-existing "ATR%" and "downside
  volatility (semivol)" terms
- Informational only, not a hard failure: if you have a pre-iter-40 baseline term count, confirm the
  total increased by exactly 3

---

### UT-09 — Short-history stock shows "NA — insufficient history" instead of a fabricated value (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks/{ticker}` — any name with materially less history than the rest of the universe

**Preconditions:**
- Same as UT-01
- **Known environment limitation** (see "Context" above): the QA pass that already ran this iteration
  could not find a ticker that actually triggers this state — every served ticker has well over the
  20-day minimum. This test is best-effort; a "could not reproduce" outcome is a data-availability
  note, not evidence of a defect.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Try the search box for names known to have listed more recently (e.g. type "Q" — the
   shortest-history symbol on record in this seed, ticker `Q`, first listed 2025-10-27) or sort by
   "Worst 20d" to surface extreme-history names
3. Open a few candidate tickers' detail pages at `/stocks/{ticker}` and inspect the "Risk budget" card

**Expected Result:**
- IF a short-history tile is found: it shows the warn-colored (amber) text "NA — insufficient
  history" instead of a numeric value, with NO "pXX of universe" chip beneath it. Hovering shows the
  tooltip "Insufficient history for this component (NA)". The value is never "0%" and never blank.
- IF no such tile is found on any inspected ticker after a reasonable search: record the result as
  "not reproducible in this environment" rather than a failure
- Secondary check, only if a genuine candidate is found: confirm "Overnight share of 20d variance" can
  independently show NA while "Overnight gap · p95" on the same card still shows real median/p95/worst
  values (these two are allowed to disagree with each other)

---

### UT-10 — A historical (pre-iter-40) as-of date shows no Risk budget card and NA leaderboard cells, without crashing (error handling)

**Type:** error
**Priority:** P2
**Surface:** `/stocks/AAPL` and `/stocks` at a historical as-of date

**Preconditions:**
- Same as UT-01
- Understand that only the "Latest" as-of date and 4 specific bootstrap dates were recomputed with
  the new risk-budget fields this iteration; every other stored as-of date was left untouched by
  design and should honestly lack the field

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. In the top bar, click the "◀" button (accessible label "Previous available date", positioned just
   left of the date-switcher button that reads "Latest") exactly once
3. Confirm the badge in the top bar changes from "Latest" to "Viewing as-of `<date>` (historical)"
4. With this historical date still active, look for the "Risk budget" card in its usual position
   (below the Themes/Invalidation card)
5. Click "Stocks" in the left sidebar to return to the leaderboard (the historical as-of date carries
   over)
6. Look at the "ATR%" through "Dist. to invalidation" columns for several rows

**Expected Result:**
- Step 4: the "Risk budget" card section is completely ABSENT — not an empty card, not a broken
  layout, simply not present. The rest of the page renders normally, no error banner, no blank screen
- Step 6: the 5 risk-budget columns show the muted gray "NA" text for every visible row at this
  historical date
- No red error banner, no browser console error, no crash
- If the Risk budget card unexpectedly DOES appear with real values at this historical date, this
  means the field was computed on demand for this date by the running code — treat this as a
  bonus-pass worth noting for the developer, not a failure of this test

---

### UT-11 — Risk budget card contains no proven/edge/position-advice language anywhere (content compliance)

**Type:** ux
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:** Same as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Read every word of text inside the "Risk budget" card — intro paragraph, all 6 tile labels, all 6
   tile values, all percentile chips
3. Use the browser's in-page search (Ctrl+F / Cmd+F) to search for: "proven", "buy", "sell", "trim",
   "reduce", "rebalance", "edge" — confirm none of these matches fall inside the Risk budget card
4. Look for any colored pill/badge inside the card resembling the "Not yet proven" / "Proven" badges
   used elsewhere on the same page (e.g. near the score cards further down)

**Expected Result:**
- None of the searched words appear anywhere inside the "Risk budget" card
- The only qualifying sentence in the card is "...distance from where the thesis is wrong.
  Descriptive only; not a recommendation."
- No badge/pill of any kind appears inside the "Risk budget" card — it contains plain tiles only

---

### UT-12 — Regression: Leadership/Entry Quality/Risk scores and evidence badges are unchanged (J-01/J-02/J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` + `/stocks/AAPL`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Find the AAPL row; record the 3 values shown under the "Leadership", "Entry Quality", and "Risk"
   columns (each is a letter-grade badge plus a decimal score, e.g. an "E" bucket badge and a number)
3. Confirm each of the 3 score cells has a small badge directly beneath it reading "Not yet proven"
4. Click the "AAPL" ticker link (opens `/stocks/AAPL` in a new tab — switch to it)
5. Scroll to the bottom of the detail page to the 3 score cards titled "Leadership", "Entry Quality",
   "Risk"
6. Compare the 3 scores and badges to what was recorded in steps 2-3

**Expected Result:**
- All 3 scores (bucket letter + numeric value) are IDENTICAL between the leaderboard row and the
  detail-page cards
- All 3 detail-page score cards show a "Not yet proven" badge (muted gray, shield icon), matching the
  leaderboard
- No score, badge, or bucket letter differs between the two views — the new Risk budget card sitting
  above these score cards has not altered them in any way

---

### UT-13 — Regression: Deep price chart still renders correctly below the new card (J-10)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks/AAPL`

**Preconditions:** Same as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Scroll down past the "Risk budget" card, past any pattern cards, past "Realized forward returns",
   to the card titled "Price & moving averages"
3. Confirm the price chart renders with visible candles/bars and moving-average lines
4. Click the "Full history" button in the chart's header controls (next to "Recent")
5. Click the regime toggle button in the chart's header (reads "Regime on" or "Regime off")

**Expected Result:**
- The "Price & moving averages" card shows a populated chart — not a blank area, not stuck on the
  animated loading placeholder — with a caption reading "`X` bars · as of 2026-07-01 · history since
  `<date>`"
- Clicking "Full history" increases the bar count shown in the caption and the chart redraws
- Clicking the regime toggle flips its own label between "Regime on" and "Regime off" and the colored
  background bands behind the price line appear/disappear accordingly
- The chart is fully visible and not overlapped, clipped, or pushed off-screen by the new Risk budget
  card above it

---

### UT-14 — Regression: Evidence status badges still render correctly on the score cards (J-05)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks/AAPL` + `/evidence`

**Preconditions:** Same as UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Scroll to the 3 score cards at the bottom of the page ("Leadership", "Entry Quality", "Risk")
3. Confirm each score card shows a badge reading "Not yet proven" directly below its score
4. Hover the mouse over the "Not yet proven" badge on the "Leadership" card
5. Navigate separately to `http://localhost:3255/evidence`

**Expected Result:**
- All 3 badges read "Not yet proven" (shield icon + muted gray text) — none read "Proven" (no
  certified evidence claim is registered this iteration, by design)
- Hovering shows tooltip text starting with "Not yet proven — no certified out-of-sample evidence..."
- The badge is a plain, non-clickable element while unproven (no underline-on-hover, no navigation on
  click)
- Step 5: the `/evidence` page loads normally with no error — this phase did not touch it

---

### UT-15 — Regression: Preflight banner still renders "GO" on both touched pages (J-20)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` + `/stocks/AAPL`

**Preconditions:**
- Frontend running at http://localhost:3255, backend healthy

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Look at the thin strip directly below the very top bar, above the "Stocks" page heading
3. Navigate to `http://localhost:3255/stocks/AAPL`
4. Look at the same thin strip below the top bar, above the "AAPL" page heading

**Expected Result:**
- On both pages, a thin green strip is visible reading "GO — today's board is current." with a small
  green dot icon
- The strip is not stuck on "Checking board status…" and does not read "NO-GO — do not rely on
  today's board." (if it does, that reflects a real backend/data health issue, not something this
  test plan can distinguish from a regression — flag it either way)
- The banner is not visually obstructed or pushed out of view by the new Risk budget card lower on
  the page

---

### UT-16 — Regression: Data Manager page unaffected (J-13)

**Type:** regression
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Confirm the page heading reads "Data Manager"

**Expected Result:**
- The page loads normally with heading "Data Manager" and a subtitle beginning "Grow the dataset on
  demand..."
- No error banner, no blank page
- No risk-budget-related content appears on this page — it was not touched by this phase

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stock Detail loads with Risk budget card present | smoke | P1 | `/stocks/AAPL` |
| UT-02 | Risk budget card: all 6 metrics + percentile chips | happy-path | P1 | `/stocks/AAPL` |
| UT-03 | Leaderboard: 5 new risk-budget columns with real values | happy-path | P1 | `/stocks` |
| UT-04 | Leaderboard value == detail card value (single source) | happy-path | P1 | `/stocks` + `/stocks/AAPL` |
| UT-05 | Risk-budget columns sortable, NA sorts last | ux | P2 | `/stocks` |
| UT-06 | Column header info icon shows glossary definition | ux | P2 | `/stocks` |
| UT-07 | Methodology glossary: 3 new terms, searchable | happy-path | P1 | `/methodology` |
| UT-08 | Methodology glossary counts stay additive-only | ux | P3 | `/methodology` |
| UT-09 | Short-history stock shows NA + reason | validation | P2 | `/stocks/{ticker}` |
| UT-10 | Historical as-of date: no card, NA columns, no crash | error | P2 | `/stocks` + `/stocks/AAPL` |
| UT-11 | No proven/edge/position-advice language on the card | ux | P1 | `/stocks/AAPL` |
| UT-12 | Regression: scores + evidence badges unchanged (J-01/02/03) | regression | P1 | `/stocks` + `/stocks/AAPL` |
| UT-13 | Regression: deep price chart still renders (J-10) | regression | P2 | `/stocks/AAPL` |
| UT-14 | Regression: evidence status badges still work (J-05) | regression | P2 | `/stocks/AAPL` + `/evidence` |
| UT-15 | Regression: preflight banner still shows GO (J-20) | regression | P1 | `/stocks` + `/stocks/AAPL` |
| UT-16 | Regression: Data Manager page unaffected (J-13) | regression | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-09 is a documented exception: a
"not reproducible with current seed data" outcome is acceptable and should not by itself fail the
verdict (see "Context" above).
