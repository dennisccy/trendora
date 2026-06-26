# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 12/13 tests passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Proximity column renders after Risk column | smoke | P1 | "Proximity to 52w high" column visible immediately right of "Risk" with percentage values | Column header "PROXIMITY TO 52W HIGH" appears directly after "RISK"; all 120 rows show percentage values (e.g., -0.53%, 0.00%); badge shows "Ready"; no backend error | PASS | UT-01-result.png |
| UT-02 | Proximity value matches Leadership breakdown | happy-path | P1 | MU detail page shows same percentage as leaderboard (-0.53%) | /stocks/MU Leadership breakdown shows "Proximity to 52w high: -0.53%" exactly matching the leaderboard value | PASS | UT-02-result.png |
| UT-03 | Clicking header sorts table and shows arrow | happy-path | P1 | Table reorders; sort arrow appears on Proximity header only | First 3 rows changed from MU/ARM/MRVL to MSTR/HUBS/COIN; lucide-arrow-up (data-testid="sort-indicator") appeared on Proximity header; only 1 sort indicator total | PASS | UT-03-result.png |
| UT-04 | Second click reverses sort direction | happy-path | P1 | First row ticker changes; arrow flips direction | First row changed from MSTR to ARM; aria-label changed to "descending"; arrow changed from lucide-arrow-up to lucide-arrow-down | PASS | UT-04-result.png |
| UT-05 | NA cells are muted and sort last in both directions | validation | P2 | At least one row shows "NA" in Proximity column; NA sorts last | Precondition not met: 0 of 120 rows show "NA" in the Proximity to 52w high column; all stocks have valid percentage values | SKIP | none |
| UT-06 | Info icon tooltip shows glossary definition | ux | P2 | Tooltip appears with proximity definition, not empty/undefined | Clicking info button opened popover: "52-week high proximity — How close price is to its one-year high — leaders tend to trade near their highs. A leadership component, NOT a buy signal by itself. Where: Leadership components. High window=252" | PASS | UT-06-result.png |
| UT-07 | Detail page shows raw distance, not percentile | regression | P1 | Value shown as percentage (e.g., -0.53%), NOT "pctl 73" | /stocks/MU Leadership breakdown row shows "-0.53%" under DETAIL, not "pctl XX" | PASS | UT-02-result.png |
| UT-08 | Badge reaches Ready at LAN-IP address | happy-path | P1 | Badge shows "Ready" or "Initializing…" at http://192.168.1.68:3255 | Badge shows "Ready" when navigating to http://192.168.1.68:3255/stocks (backend started with CORS_ORIGIN_REGEX allowing private LAN origins) | PASS | UT-08-result.png |
| UT-09 | Badge shows Unavailable when backend is stopped | error | P1 | Badge shows "Backend unavailable" with backend down | Badge (data-testid="readiness-badge") shows "Backend unavailable" immediately after backend is stopped; no "Ready" flash | PASS | UT-09-result.png |
| UT-10 | Dashboard loads data at localhost | regression | P1 | Dashboard shows regime/sector/theme data; no backend error | Badge shows "Initializing… history 9/9"; Market Regime "Risk-on 76.05/100" with component breakdown visible; hasError=false | PASS | UT-10-result.png |
| UT-11 | Leaderboard retains all existing columns at localhost | regression | P1 | All pre-existing columns present plus new Proximity column; 120 rows | Headers: #, Ticker, Sector, Leadership, Entry Quality, Risk, Proximity to 52w high, Setup, 1d, 5d, 10d, 20d, 60d, 1d MDD, 5d MDD, 10d MDD, 20d MDD, 60d MDD, Themes, Reason; 120 rows; no backend error | PASS | none |
| UT-12 | Research lab loads after API_BASE change | regression | P2 | Research page renders at least one content section; no backend error | Research page shows "Factor Lab — Does a factor actually sort future returns? Decile means +"; badge "Ready"; no backend error | PASS | none |
| UT-13 | Pre-existing column sort still reorders the table | regression | P1 | Leadership sort reorders table; only Leadership shows sort arrow; Proximity shows no arrow | First row changed from MU to COIN after clicking Leadership; only "Leadership" has sort indicator; Proximity to 52w high column does NOT have sort arrow | PASS | UT-13-result.png |

---

## Passed Tests

### UT-01 — Proximity column renders after Risk column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-01-result.png`
- Navigated to http://localhost:3255/stocks; table loaded with 120 rows
- Column order confirmed via DOM eval: `[#, Ticker, Sector, Leadership, Entry Quality, Risk, Proximity to 52w high, Setup, ...]`
- "Proximity to 52w high" is at index 6, immediately after "Risk" at index 5
- Sample values: MU=-0.53%, ARM=0.00%, MRVL=-1.65%
- Badge shows "Ready"; no "Backend unavailable" error

---

### UT-02 — Proximity value matches Leadership breakdown
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-02-result.png`
- Navigated to http://localhost:3255/stocks/MU
- Leadership component breakdown row "Proximity to 52w high" shows DETAIL=-0.53%, CONTRIBUTION=8.82
- Value -0.53% is byte-identical to the leaderboard value for MU

---

### UT-03 — Clicking header sorts table and shows arrow
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-03-result.png`
- Before click: top 3 tickers = ["MU","ARM","MRVL"] (sorted by Leadership descending)
- Clicked button with aria-label "Sort by Proximity to 52w high, ascending"
- After click: top 3 tickers = ["MSTR","HUBS","COIN"] (most negative proximity first)
- `[data-testid="sort-indicator"]` count=1, only on "Proximity to 52w high" header

---

### UT-04 — Second click reverses sort direction
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-04-result.png`
- Before second click: first row = MSTR; sort button aria-label = "Sort by Proximity to 52w high, ascending"; SVG class = lucide-arrow-up
- After second click: first row = ARM (0.00%, at/nearest 52w high); aria-label = "Sort by Proximity to 52w high, descending"; SVG class = lucide-arrow-down

---

### UT-06 — Info icon tooltip shows glossary definition
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-06-result.png`
- Clicked info button with aria-label "Definition of 52-week high proximity"
- Popover appeared with text: "52-week high proximity — How close price is to its one-year high — leaders tend to trade near their highs. A leadership component, NOT a buy signal by itself. Where: Leadership components. High window=252"
- Not empty, not "undefined", not "term not found"

---

### UT-07 — Detail page shows raw distance, not percentile
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-02-result.png`
- Leadership breakdown for MU shows "Proximity to 52w high" DETAIL="-0.53%"
- Other components show percentile format "pctl XX" (e.g., "RS vs SPY · 1m: pctl 100")
- The Proximity row uniquely shows a raw percentage, not a percentile rank

---

### UT-08 — Badge reaches Ready at LAN-IP address
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-08-result.png`
- Navigated to http://192.168.1.68:3255/stocks (LAN-IP URL)
- Backend started with CORS_ORIGINS including the LAN-IP origin and CORS_ORIGIN_REGEX matching private LAN subnets
- `[data-testid="readiness-badge"]` shows "Ready"; 120 stock rows loaded; no "Backend unavailable" error

---

### UT-09 — Badge shows Unavailable when backend is stopped
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-09-result.png`
- Killed all processes on port 8255; curl returned HTTP 000 (connection refused)
- Navigated to http://localhost:3255/; `[data-testid="readiness-badge"]` shows "Backend unavailable"
- Data sections show empty state; badge never flipped to "Ready"

---

### UT-10 — Dashboard loads data at localhost
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-10-result.png`
- Navigated to http://localhost:3255/; badge shows "Initializing… history 9/9"
- Market Regime section visible: "Risk-on 76.05 / 100" with full component breakdown
- No backend error; no CORS errors; data populated

---

### UT-11 — Leaderboard retains all existing columns at localhost
**Verdict:** PASS
**Evidence:** none (column list extracted via DOM eval)
- All 20 column headers present: #, Ticker, Sector, Leadership, Entry Quality, Risk, Proximity to 52w high, Setup, 1d, 5d, 10d, 20d, 60d, 1d MDD, 5d MDD, 10d MDD, 20d MDD, 60d MDD, Themes, Reason
- 120 rows populated; no backend error

---

### UT-12 — Research lab loads after API_BASE change
**Verdict:** PASS
**Evidence:** none
- Navigated to http://localhost:3255/research
- Page shows "Research — Factor Lab — Does a factor actually sort future returns? Decile means +"
- Badge shows "Ready"; no "Backend unavailable" error

---

### UT-13 — Pre-existing column sort still reorders the table
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/UT-13-result.png`
- Before click: first row = MU (default Leadership descending)
- Clicked Leadership column button; after click: first row = COIN (Leadership ascending, lowest first)
- `[data-testid="sort-indicator"]` on "Leadership" only; "Proximity to 52w high" has no sort arrow

---

## Skipped Tests

### UT-05 — NA cells are muted and sort last in both directions
**Verdict:** SKIPPED
**Reason:** Prerequisite data missing — 0 of 120 rows in the dataset show "NA" in the "Proximity to 52w high" column. All 120 stocks have valid percentage values (range: 0.00% to -81.28%). The muted-NA visual and NA-sort-last behavior cannot be observed without a stock lacking 52-week price history in the seed data.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **LAN-IP URL:** http://192.168.1.68:3255
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-26
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-evidence/`
- **Backend:** Started manually with CORS_ORIGINS + CORS_ORIGIN_REGEX covering localhost and private LAN (192.168.x.x)
