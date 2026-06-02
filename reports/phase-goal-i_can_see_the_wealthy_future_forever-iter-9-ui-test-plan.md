# Phase goal-i_can_see_the_wealthy_future_forever-iter-9 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

This iteration grows the detected-pattern vocabulary from one (VCP) to three by adding **Pullback to rising DMA** and **Flat-base breakout** across four routes: `/stocks`, `/stocks/[ticker]`, `/system-health`, and `/methodology`. No new routes or navigation. These UI tests cover the 10 affected surfaces in the surface map; they do NOT duplicate the backend/API functional tests (TC-01…TC-12) in the QA test plan — they verify only what is visible in the browser.

Navigation context: the left sidebar carries "Stocks" (`/stocks`), "System Health" (`/system-health`), and "Methodology" (`/methodology`). Stock detail is reached by clicking a ticker on the leaderboard.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Stock Leaderboard loads with the new Pattern filter (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3835, backend running on :8000
- Backend DB regenerated so rows carry the new pattern flags

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load (skeleton rows disappear)

**Expected Result:**
- The heading "Stocks" is visible
- A filter bar shows three dropdowns labelled "Sector", "Setup", and "Pattern" (left to right)
- The "Pattern" dropdown is present and shows "All patterns" as its default selected value
- A ranked table with columns `#`, `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Setup`, `Reason` renders with at least one row
- No "Backend unavailable" error card, no blank screen, no console errors

---

### UT-02 — Pattern dropdown offers all three patterns with only/not options (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — "Pattern" `<Select>`

**Preconditions:**
- At UT-01 state (leaderboard loaded with rows)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Open the "Pattern" dropdown
3. Read its option list

**Expected Result:**
- The dropdown contains "All patterns", plus three option groups labelled "VCP", "Pullback to rising DMA", and "Flat-base breakout"
- The "VCP" group contains "VCP only" and "Not VCP"
- The "Pullback to rising DMA" group contains "Pullback to rising DMA only" and "Not Pullback to rising DMA"
- The "Flat-base breakout" group contains "Flat-base breakout only" and "Not Flat-base breakout"

---

### UT-03 — Filtering by "Pullback to rising DMA only" narrows to flagged rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — "Pattern" `<Select>`

**Preconditions:**
- Leaderboard loaded; at least one row is flagged for Pullback (if none flagged, see Expected Result empty-state branch)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Note the count to the right of the filters, shown as `<visible> / <total>` (e.g. `50 / 50`)
3. In the "Pattern" dropdown, select "Pullback to rising DMA only"

**Expected Result:**
- The visible count drops to ≤ the total (the left number in `<visible> / <total>` decreases or stays equal, never increases)
- Every remaining row shows a teal "Pullback" badge in the Setup column
- No row WITHOUT a "Pullback" badge remains
- If zero rows are flagged: an empty-state card appears reading "No stocks match these filters" with a description beginning "No Pullback to rising DMA-flagged name…" and NO table rows are shown (no fabricated rows)

---

### UT-04 — Filtering by "Not Flat-base breakout" removes flat-base rows (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks` — "Pattern" `<Select>`

**Preconditions:**
- Leaderboard loaded

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. In the "Pattern" dropdown, select "Flat-base breakout only"; note which tickers show a "Flat base" badge
3. In the "Pattern" dropdown, select "Not Flat-base breakout"

**Expected Result:**
- After step 3, none of the tickers identified in step 2 (the flat-base-flagged ones) appear in the list
- No remaining row shows a "Flat base" badge
- The visible count reflects total-minus-flagged

---

### UT-05 — Pullback / Flat base badges render with reason tooltip on flagged rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks` — per-pattern badges

**Preconditions:**
- At least one row flagged for Pullback or Flat base (use "Pullback to rising DMA only" or "Flat-base breakout only" filter to find one)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Select "Pullback to rising DMA only" in the "Pattern" dropdown
3. On the first row, locate the teal "Pullback" badge in the Setup column
4. Hover the mouse over the "Pullback" badge and hold for ~1 second

**Expected Result:**
- A teal "Pullback" badge is visible in the Setup column (cursor changes to a help cursor on hover)
- A browser tooltip appears containing the server-built reason text, and (when present) a "Pivot $<number>." fragment and an invalidation note
- The tooltip text is plain prose (not "undefined", not an empty string, not a JSON blob)

---

### UT-06 — Pattern glossary info tooltip shows the definition (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks` — `InfoTooltip` beside a pattern badge

**Preconditions:**
- A flagged Pullback or Flat base row visible; backend `/methodology` catalog reachable

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Select "Flat-base breakout only" in the "Pattern" dropdown
3. On a flagged row, locate the small info icon immediately to the right of the "Flat base" badge
4. Hover (or click) the info icon

**Expected Result:**
- An info icon (ⓘ-style) appears next to the "Flat base" badge
- Hovering/clicking reveals a tooltip with the pattern's glossary definition (the same plain-language "meaning" text shown on `/methodology`)
- The tooltip's accessible label is "Definition of the Flat-base breakout pattern"

---

### UT-07 — Pattern-aware empty state names the active filter (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks` — empty state

**Preconditions:**
- Leaderboard loaded with rows

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. In the "Setup" dropdown select a status, and in the "Pattern" dropdown select a pattern combination known to match zero rows (e.g. select "Pullback to rising DMA only" together with a Sector that has no pullback-flagged names)

**Expected Result:**
- The table is replaced by an empty-state card titled "No stocks match these filters"
- The description names the active pattern filter, e.g. begins "No Pullback to rising DMA-flagged name is currently …" and ends with "No rows are fabricated to fill the view — clear a filter to see more."
- No table rows are displayed

---

### UT-08 — Stock detail header shows a badge per flagged pattern (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` — header `PatternBadge`(s)

**Preconditions:**
- A ticker flagged for a new pattern is known (from UT-03/04). Example placeholder: `<TICKER>`.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Select "Pullback to rising DMA only" to find a flagged ticker; click that ticker's link in the Ticker column
3. On the detail page, look at the header card (top card, beside the setup-status badge)

**Expected Result:**
- The page heading is the ticker symbol
- The header card shows the setup-status badge AND a teal "Pullback" badge beside it
- Hovering the "Pullback" badge shows the same server reason + pivot + invalidation tooltip as on the leaderboard
- The sector text and an "as of <date>" badge are also present in the header

---

### UT-09 — Stock detail renders a dedicated pattern card with pivot and invalidation (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/[ticker]` — `PatternCard`

**Preconditions:**
- A flat-base-flagged ticker open at `/stocks/<TICKER>`

**Steps:**
1. From `/stocks`, select "Flat-base breakout only", click a flagged ticker
2. Scroll down past the header and the Themes/Invalidation card
3. Locate the card titled "Flat-base breakout"

**Expected Result:**
- A card titled "Flat-base breakout" with a teal "Flat base" badge in its header is present
- The card shows the server reason text, a "Pivot (breakout level)" value formatted as `$<number>` (or "—" if null), and an "Invalidation" note in amber/warn text
- The "VCP — Volatility Contraction Pattern" card (or its "No VCP pattern detected." state) is still present above/around it — unchanged

---

### UT-10 — System Health renders both new forward-return panels with n / NA (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` — two new `BreakdownPanel`s

**Preconditions:**
- Frontend running; backend DB regenerated with forward-test aggregates

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Wait for panels to load (skeleton disappears)
3. Scroll to the breakdown panel grid and locate the panel titled "Forward return: Pullback-to-rising-DMA vs not"
4. Locate the panel titled "Forward return: Flat-base breakout vs not"

**Expected Result:**
- Both panels are present, positioned after the existing "Forward return: VCP vs non-VCP" panel
- Each panel shows two rows (a flagged cohort and a not-flagged cohort) each with a mean forward-return value and a sample size `n`
- Any cohort with `n` below the minimum sample shows "NA" (or the low-sample ⚠ marker) rather than a fabricated number — values are never invented
- If a panel has no measurable cohort it shows its honest empty text (e.g. "No pullback-to-rising-DMA cohort had a measurable forward return at this horizon.")

---

### UT-11 — Methodology auto-renders the two new pattern glossary cards (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/methodology` — two new `EntryCard`s

**Preconditions:**
- Frontend running; backend catalog has both `kind:"pattern"` entries

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Wait for the cards to load
3. Scroll to find a card titled "Pullback to rising DMA" and a card titled "Flat-base breakout"

**Expected Result:**
- A card titled "Pullback to rising DMA" and a card titled "Flat-base breakout" each render
- Each card carries a teal "Pattern" chip in its header
- Each card shows a plain-language meaning paragraph, a "Thresholds" list with live config values, and an "Example:" line
- The threshold numbers are concrete values (not "undefined" / blank)

---

### UT-12 — Methodology subtitle is generic, not VCP-specific (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/methodology` — page subtitle

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Read the subtitle text directly under the "Methodology" heading

**Expected Result:**
- The subtitle reads generically about "every setup status and detected price pattern" — it must NOT say "the VCP pattern" specifically
- Exact expected substring: "What every setup status and detected price pattern mean"

---

### UT-13 — Regression: VCP filter, badge, and glossary still work unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/methodology`, `/system-health` — VCP surfaces

**Preconditions:**
- Frontend running; VCP-flagged rows exist

**Steps:**
1. Navigate to `http://localhost:3835/stocks`; in the "Pattern" dropdown select "VCP only"
2. Confirm only VCP-flagged rows remain, each with a "VCP" badge; hover a "VCP" badge to confirm its tooltip
3. Select "Not VCP"; confirm VCP-flagged rows disappear
4. Navigate to `http://localhost:3835/methodology`; confirm the "VCP" pattern card is still present with its meaning/thresholds/example
5. Navigate to `http://localhost:3835/system-health`; confirm the "Forward return: VCP vs non-VCP" panel still renders

**Expected Result:**
- "VCP only" / "Not VCP" filter identically to before (only VCP-flagged shown / hidden respectively)
- The "VCP" badge and its reason+pivot+invalidation tooltip are unchanged
- The VCP methodology card and the VCP system-health panel render unchanged
- No regression: VCP behaves exactly as in prior iterations

---

### UT-14 — Regression: Sector + Setup filters still work alongside the new Pattern filter (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` — Sector / Setup `<Select>`s

**Preconditions:**
- Leaderboard loaded with multiple sectors and setup statuses

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. In the "Sector" dropdown select any specific sector (not "All sectors")
3. Confirm only rows of that sector remain
4. In the "Setup" dropdown select any specific status (not "All setups")
5. Confirm rows now match BOTH the chosen sector and setup
6. Reset both back to "All sectors" / "All setups"

**Expected Result:**
- Sector filter narrows to the chosen sector only
- Setup filter further narrows; Sector + Setup + Pattern filters compose (AND) without interfering
- Resetting both restores the full row count (`<total> / <total>`)
- The `<visible> / <total>` counter updates correctly at each step

---

### UT-15 — Methodology glossary lists 6 setups + 3 patterns (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/methodology` — full card list

**Preconditions:**
- Frontend running; catalog complete

**Steps:**
1. Navigate to `http://localhost:3835/methodology`
2. Count cards bearing a "Setup" chip and cards bearing a "Pattern" chip

**Expected Result:**
- Exactly 6 cards carry a "Setup" chip
- Exactly 3 cards carry a "Pattern" chip (VCP, Pullback to rising DMA, Flat-base breakout)
- No duplicate or missing pattern card

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Leaderboard loads with Pattern filter | smoke | P1 | `/stocks` |
| UT-02 | Pattern dropdown offers 3 patterns ×2 modes | happy-path | P1 | `/stocks` |
| UT-03 | "Pullback only" narrows to flagged rows | happy-path | P1 | `/stocks` |
| UT-04 | "Not Flat-base" removes flat-base rows | happy-path | P2 | `/stocks` |
| UT-05 | Pullback/Flat base badge + reason tooltip | happy-path | P1 | `/stocks` |
| UT-06 | Pattern glossary info tooltip | happy-path | P2 | `/stocks` |
| UT-07 | Pattern-aware empty state | validation | P2 | `/stocks` |
| UT-08 | Detail header pattern badge(s) | happy-path | P1 | `/stocks/[ticker]` |
| UT-09 | Detail pattern card (pivot + invalidation) | happy-path | P1 | `/stocks/[ticker]` |
| UT-10 | System Health two new panels + n/NA | happy-path | P1 | `/system-health` |
| UT-11 | Methodology two new pattern cards | happy-path | P1 | `/methodology` |
| UT-12 | Methodology subtitle is generic | ux | P3 | `/methodology` |
| UT-13 | VCP filter/badge/glossary/panel regression | regression | P1 | multi |
| UT-14 | Sector + Setup filters still compose | regression | P1 | `/stocks` |
| UT-15 | Glossary lists 6 setups + 3 patterns | regression | P2 | `/methodology` |

**P1 tests (UT-01, 02, 03, 05, 08, 09, 10, 11, 13, 14) must all pass for browser QA verdict to be PASS.**
