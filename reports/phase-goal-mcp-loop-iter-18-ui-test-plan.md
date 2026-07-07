# Phase goal-mcp-loop-iter-18 — UI Test Plan

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-06
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

## Context for the tester

This iteration flipped the whole product onto a 30-year / 548-name price basis and reset the evidence
ledger to an honest all-FAIL state. The three target journeys are: **J-10** (deep, honestly-bounded price
history on Stock Detail), **J-11** (regenerated 7-row evidence ledger, zero "Proven" anywhere), **J-12**
(broadened point-in-time universe + a new staleness/recency exclusion gate). Four prior journeys
(J-01/J-03/J-04/J-05) must still pass on the regenerated data with **fresh pixels** — there is no
byte-identity carry from a prior run to lean on.

**A note on what "PASS" looks like this run:** every evidence badge in the product reading **"Not yet
proven"**, and every `/evidence` row reading **"FAIL"**, is the CORRECT and EXPECTED state — not a bug.
Do not treat an all-FAIL ledger as a failure of the test plan; the anti-goal sweep tests below (UT-18)
exist specifically to confirm nothing fabricates a "Proven" state instead.

**Known, persisted browser preference (read the code — this will bite you if skipped):** the Stock Detail
chart's Recent/Full-history choice is stored in `localStorage` under one shared key
(`trendora.detail.chartFullHistory`), not per-ticker. If a prior test left it on "Full history", the next
ticker you open will ALSO open in Full history. Where a test depends on the bounded default, its
Preconditions say to click "Recent" first.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Stock Detail page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255 and backend is up
- No login required (no auth in this product)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Wait for the page to fully load (the loading skeleton — three pulsing gray cards — should disappear)

**Expected Result:**
- The ticker "AAPL" appears as the page heading, with subtitle "Stock detail — the three explainable scores (identical to the leaderboard; single source of truth)"
- A setup-status badge (e.g. "Actionable", "Breakout-watch", "Extended", "Avoid", etc.) is visible near the top
- A "Price & moving averages" card is visible with a candlestick/line chart rendered inside it
- Three score cards titled "Leadership", "Entry Quality", and "Risk" are visible near the bottom, each showing a numeric score out of 100
- No blank page, no "Backend unavailable" message, no "Unknown ticker" message

---

### UT-02 — Stocks leaderboard loads at the broadened scale (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend is running at http://localhost:3255 and backend is up

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to fully load

**Expected Result:**
- Page heading reads "Stocks" with subtitle "Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason"
- A table renders with columns including `#`, `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Proximity to 52w high`, `Setup`, forward-return day columns, `Themes`, `Reason`
- Near the search box, a count reads "`N` / `N`" (visible-count / total-count) where `N` is several hundred — NOT capped near 122 (spot-check: this should be closer to the ~548-name pool, filtered by point-in-time membership)
- No blank page, no "Backend unavailable" message

---

### UT-03 — Data Manager page loads with the widened diagnostic grid (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255 and backend is up

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load
3. Scroll down to the panel titled "Universe resolution as of `<date>`" (or "Universe resolution (latest)")

**Expected Result:**
- Page heading reads "Data Manager"
- The "Universe resolution..." panel shows a row of **5** metric cards (not 4): "Admitted", "Below min history", "Stale series", "Below min price", "Below min liquidity" — in that order
- No blank page, no "Backend unavailable" message

---

### UT-04 — Evidence ledger page loads with exactly 7 rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255 and backend is up

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to fully load
3. Count the number of claim cards on the page

**Expected Result:**
- Page heading reads "Evidence" with subtitle mentioning "the single source of proven-ness"
- Exactly **7** claim cards are rendered (not the "No certified claims yet" empty state, and not more/fewer than 7)
- No blank page, no "Backend unavailable" message

---

### UT-05 — Chart range toggle switches AAPL between Recent and Full history (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- `/stocks/AAPL` loads successfully (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Scroll to the "Price & moving averages" card
3. Look at the card's header row: you should see a two-button control showing "Recent" and "Full history" side by side, immediately to the left of a second button reading "Regime on" (or "Regime off")
4. Confirm "Recent" is currently highlighted (light gray background); if "Full history" is highlighted instead, click "Recent" first and wait for the chart to reload
5. Note the chart's visible span (informally — roughly the last few years)
6. Click the "Full history" button
7. Immediately observe the chart area
8. Wait 1-2 seconds for the chart to finish loading

**Expected Result:**
- Step 7: briefly, the chart area shows a plain gray pulsing rectangle (the loading skeleton) — the OLD "Recent" chart must NOT remain visible during this fetch
- Step 8: the chart re-renders showing a visibly much longer time span (decades, not years) than the "Recent" view
- Clicking "Recent" again returns the chart to the shorter, bounded span within 1-2 seconds (same loading-skeleton behavior)
- No error message, no blank chart area, no console-visible crash

---

### UT-06 — AAPL chart caption discloses the real first-available date (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- `/stocks/AAPL` loads successfully

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Scroll to the "Price & moving averages" card header
3. With "Recent" selected, read the small caption text to the right of the Recent/Full-history and Regime buttons (format: "`N` bars · as of `DATE` · history since `DATE`")
4. Click "Full history"
5. Wait for the chart to reload, then re-read the same caption

**Expected Result:**
- Step 3 (Recent mode): the caption's "history since" date reads exactly **1996-01-02** — even though the chart itself only shows the last ~5 years, the caption discloses AAPL's true first-ever stored bar
- Step 5 (Full history mode): the caption still reads "history since **1996-01-02**", and now has an additional suffix: "**· older bars weekly-sampled**" appended after the date
- The bar count number in Full-history mode is visibly larger than in Recent mode

---

### UT-07 — NVDA chart discloses its real IPO date with weekly-sample disclosure (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- None beyond backend running

**Steps:**
1. Navigate to `http://localhost:3255/stocks/NVDA`
2. If the chart opens already in "Full history" (carried over from a prior test), click "Recent" first, wait for reload
3. Read the caption in Recent mode
4. Click "Full history" and wait for the chart to reload
5. Read the caption again
6. Visually inspect the candlestick/line series for any sudden, unexplained 10x-scale price cliff (a sign of a non-continuous or mis-adjusted split)

**Expected Result:**
- In both Recent and Full-history mode, the caption's "history since" date reads exactly **1999-01-22** (NVDA's real IPO date) — never an earlier, invented date
- In Full-history mode, the caption includes "· older bars weekly-sampled" (NVDA's real history is well beyond the 8-year downsample threshold)
- The price series moves smoothly with no unexplained vertical price cliff — split-adjustment continuity is visually intact

---

### UT-08 — Post-IPO ticker ARM honestly shows only its real short history (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- None beyond backend running

**Steps:**
1. Navigate to `http://localhost:3255/stocks/ARM`
2. If the chart opens already in "Full history", click "Recent" first, wait for reload
3. Read the caption in Recent mode
4. Click "Full history" and wait for the chart to reload
5. Read the caption again
6. Compare the leftmost (earliest) point of the rendered chart in both modes

**Expected Result:**
- In BOTH Recent and Full-history mode, the caption's "history since" date reads exactly **2023-09-14** (ARM's real IPO) — no earlier date
- Neither mode shows the "· older bars weekly-sampled" suffix (ARM's whole real history is under the 8-year downsample threshold)
- The chart's leftmost visible bar in Full-history mode does NOT extend before 2023-09-14 — no invented pre-IPO bars in either mode
- (Note: because ARM's IPO is more recent than the 5-year "Recent" window, the Recent and Full-history charts may look nearly identical — that similarity IS the correct, honest behavior, not a bug)

---

### UT-09 — Watchlist accepts a broadened-pool ticker and it survives a refresh (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Backend running; ABBV is not already on the watchlist (if it is, use any other broadened-pool ticker such as ABT, ACGL, or ACN and substitute below)

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. In the "Ticker" field (placeholder "e.g. ANET"), type `ABBV`
3. In the "Reason" field (placeholder "Why are you watching it?"), type `UI test — broadened pool`
4. Click the "Add" button (has a plus icon)
5. Wait for the table to refresh
6. Refresh the whole browser page (F5 / Cmd+R)

**Expected Result:**
- Step 5: no red error banner appears; a new row for **ABBV** appears in the watchlist table with live Leadership / Entry Quality / Risk badges, a Setup badge, and today's date in the "Added" column — NOT rejected as "unknown ticker"
- Step 6: after the refresh, the **ABBV** row is still present with the same reason text "UI test — broadened pool" — confirming the add was persisted server-side, not just an optimistic local update

---

### UT-10 — Broadened-pool stock detail page renders honestly (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- None beyond backend running

**Steps:**
1. Navigate to `http://localhost:3255/stocks/ABBV` (ABBV is a real S&P name carried in the broadened seed pool but is NOT one of the original ~122 curated tickers)
2. Observe the whole page

**Expected Result:**
- The page loads normally — same layout as UT-01 (setup badge, chart, three score cards)
- No "Unknown ticker" message, no "Backend unavailable" message, no blank sections
- The chart renders real price bars (not a flat line, not empty)
- The Sector text next to the setup badge is either a real sector name OR renders blank — it must NEVER show the literal text "None", "null", "undefined", or similar

---

### UT-11 — Global as-of switcher's oldest date reaches the disclosed floor (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** global top-bar control (visible on every page, tested from `/backtest`)

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. In the top bar, find the button showing "Latest" with a calendar icon (to the right of the ◀ / ▶ step buttons)
3. Click that button to open the calendar popover
4. Use the popover's left-pointing month-navigation chevron repeatedly (or the Year dropdown, if present) to go back to the earliest navigable month
5. Confirm the earliest clickable (non-grayed-out) day in the calendar

**Expected Result:**
- The calendar's month navigation stops advancing backward once it reaches **February 2005** — the earliest selectable day is **2005-02-25**, with no earlier day selectable
- Selecting that earliest date closes the popover, the top-bar button now reads "2026-07-06"-style formatted **2005-02-25**, and an amber "Viewing as-of 2005-02-25 (historical)" badge appears
- The Backtest page's own survivorship banner and scorecard still render (no crash) at that early date, though some evidence panels may honestly show sparse or NA figures this early in the warm-up window

---

### UT-12 — Universe staleness disclosure appears in both Coverage and Diagnostic panels (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loads successfully (UT-03 passed)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the top "Dataset coverage" panel, find the metric card labeled **"Universe (as of date)"** (NOT the "Admitted" card — that is a different, lower panel; see step 4)
3. Read its definition paragraph beneath the number
4. Scroll down to the separate "Universe resolution as of `<date>`" panel and read the hint sentence directly under that heading (above the 5 metric cards)

**Expected Result:**
- Step 3: the "Universe (as of date)" definition paragraph includes the phrase "**a fresh series (last bar within 10 days)**" alongside the existing history/price/liquidity language
- Step 4: the panel's hint sentence includes the phrase "**a FRESH series (last bar within 10 calendar days of the as-of)**" alongside history/price/liquidity criteria
- Both locations name the same **10-day** threshold — no mismatch between the two figures

---

### UT-13 — Methodology per-date rule cites the staleness/recency requirement (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/methodology`

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3255/methodology`
2. Find the card titled "Universe Selection" (has a "Screen" badge)
3. Scroll within that card to the sub-section labeled "Per-date membership rule" (has an "As-of" badge)
4. Read the paragraph of prose beneath that label

**Expected Result:**
- The per-date-rule paragraph mentions a data-recency or staleness requirement (e.g. references to a series being "fresh," "stale," or "recency") in addition to the pre-existing history/price/liquidity gates
- Directly below the paragraph, "Candidate pool: `N` names · Minimum history: `M` trailing bars" is shown, where `N` is a large number (hundreds, reflecting the ~548 pool) — not ~122

---

### UT-14 — Every score badge on the leaderboard reads "Not yet proven" (J-01 required regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loads with rows (UT-02 passed)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Pick any 3 visible rows
3. For each row, look directly beneath the Leadership score badge, the Entry Quality score badge, and the Risk score badge

**Expected Result:**
- Every one of the 3 badges beneath every one of the 3 chosen rows' scores reads exactly "**Not yet proven**" (muted gray badge with a shield icon)
- Zero badges anywhere on the visible rows read "Proven" (accent-colored badge)
- No score is missing its badge entirely

---

### UT-15 — Evidence ledger row 1 byte-matches the regenerated replay (J-03/J-11 required regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loads with 7 rows (UT-04 passed)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Find the row whose "Hypothesis" chips include `signal=leadership_score` (this should be the first row)
3. Read its verdict badge (top-left of the card)
4. Read its "Out-of-sample verdict" field value (includes a holdout-edge percentage)
5. Read its "Registration date" field

**Expected Result:**
- Verdict badge reads exactly "**FAIL**" (red/danger-colored badge) — never "PASS"
- The "Out-of-sample verdict" field shows a holdout edge of **-0.03%**
- The "Registration date" field reads exactly **2026-07-03**

---

### UT-16 — Breakout-watch row keeps its regime label with an honest FAIL verdict (J-04 required regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loads with 7 rows

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Find the row whose Hypothesis chips describe an event-study / Breakout-watch cohort
3. Look for a second, accent-colored badge next to the verdict badge (top of the card)
4. Read that badge's text
5. Read the row's verdict badge

**Expected Result:**
- A badge reading exactly "**Regime: Risk-on**" is present on this row (it must NOT have disappeared just because the verdict is now failing)
- The verdict badge on the same row reads "**FAIL**"
- The row's Registration date reads **2026-07-03**

---

### UT-17 — Evidence ledger is fully auditable end-to-end with working linkbacks (J-05 required regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` loads with 7 rows

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. For any 2 rows, confirm each shows all five fields: a Hypothesis (chips), "Out-of-sample verdict", "Control comparison (vs SPY)", "Registration date", "Forward-walk score-to-date"
3. Click the "Backs: `...` →" link in the top-right of one row's card
4. Use the browser back button (or re-navigate to `/evidence`)
5. Repeat step 3 for a second row with a different linkback label

**Expected Result:**
- All 5 fields render non-blank content (or an explicit "Pending — monitored as new data matures" / "—" placeholder — never a missing field) on both inspected rows
- Clicking "Backs: `...` →" navigates to the labeled surface (e.g. the Stocks leaderboard, a Research lab page) without a 404 or crash
- Both tested linkbacks work

---

### UT-18 — No retired evidence values or dates appear anywhere in the app (J-11 anti-goal, required regression)

**Type:** regression
**Priority:** P1
**Surface:** multi-page (`/stocks`, `/stocks/{ticker}`, `/evidence`, `/research/factor-lab`)

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3255/evidence`; visually scan all 7 rows' displayed percentages and dates
2. Navigate to `http://localhost:3255/stocks`; scan the visible score badges
3. Navigate to `http://localhost:3255/stocks/AAPL`; scan the three score cards
4. Navigate to `http://localhost:3255/research/factor-lab`; scan any cohort/decile badges

**Expected Result:**
- None of these retired figures appear anywhere on any of the 4 pages: **+21.34%, +8.91%, +6.36%, +6.12%, +4.69%, +3.33%**, p-value **0.0004998**, or register dates **2026-06-30** / **2026-07-01**
- No badge anywhere reads "Proven" — every evidence badge reads "Not yet proven", and every `/evidence` verdict reads "FAIL"

---

### UT-19 — Score badge is honestly non-interactive with no fabricated drill panel (J-02 partial — expected this iteration)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- `/stocks/AAPL` loads (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Scroll to the "Leadership" score card
3. Hover over the "Not yet proven" badge beneath the score for 1-2 seconds
4. Try clicking directly on the "Not yet proven" badge
5. Look for any collapsible "Why proven?" disclosure control anywhere on the score card

**Expected Result:**
- Step 3: a tooltip appears reading "Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)." — a plain hover tooltip, not a clickable element
- Step 4: clicking the badge does **NOT** navigate anywhere and does **NOT** open any panel (this is expected and correct this iteration — with zero "Proven" signals ledger-wide, there is nothing to drill into)
- Step 5: no "Why proven?" toggle button is present on this card (that control only appears for a PROVEN signal, and none exist this iteration)
- This is a PASS, not a bug: the honest absence of a drill affordance IS the correct behavior when nothing is proven

---

### UT-20 — Research Factor Lab shows the updated survivorship caveat and honest cohort badges (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research/factor-lab`

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3255/research`
2. Click the "Factor Lab" card
3. Find the amber-bordered banner near the top of the page (warning-triangle icon, bold heading "Survivorship bias · universe-relative · descriptive")
4. Read the paragraph beneath that heading
5. Scroll to the all-factors table and find any "Proven"/"Not yet proven"-style badge in a decile or cohort cell

**Expected Result:**
- Step 2: the page navigates to `http://localhost:3255/research/factor-lab`
- Step 4: the caveat paragraph mentions "**up to ~30 years of history (1996 to present**" — not the old shorter-window phrasing
- Step 5: any evidence-status badge found reads "Not yet proven" (muted); none read "Proven"

---

### UT-21 — Sector column sort and filter handle rows with no sector without crashing (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loads with rows, including at least one broadened-pool name with no assigned sector

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the "Sector" column header once
3. Click it again (to reverse sort direction)
4. Open the "Sector" filter dropdown (labeled "Sector", currently showing "All sectors")
5. Scroll through the dropdown's options list

**Expected Result:**
- No error page, blank screen, or crash occurs after either sort click
- Any row with no assigned sector shows an empty/blank Sector cell — never the literal text "None", "null", or "undefined"
- The Sector filter dropdown opens normally; it may contain one blank-looking option (for the unassigned-sector rows) but must not throw a visible error or freeze the page

---

### UT-22 — Backtest page's survivorship caveat discloses the ~30-year span (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Read the amber-bordered caveat banner directly beneath the "Viewing as-of..." badge

**Expected Result:**
- The banner text includes "**Walk-forward evidence now spans up to ~30 years of history (1996 to present**" (not a shorter-window phrase)
- The banner also mentions survivorship bias and "current index members" language
- The rest of the Backtest scorecard still renders beneath it (no crash)

---

### UT-23 — Watchlist rejects a genuinely unknown ticker (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- `/watchlist` loads successfully

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. In the "Ticker" field, type `ZZZZZ`
3. Leave the "Reason" field empty
4. Click the "Add" button

**Expected Result:**
- A red error line appears below the Add form reading exactly: "**unknown ticker: ZZZZZ**" (with a warning-triangle icon)
- No new row is added to the watchlist table
- The Ticker field's typed value is NOT cleared (so the user can see/correct their mistake)

---

### UT-24 — Watchlist "Add" button is disabled until a ticker is typed (validation)

**Type:** validation
**Priority:** P3
**Surface:** `/watchlist`

**Preconditions:**
- `/watchlist` loads successfully

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Without typing anything, observe the "Add" button
3. Type a single character in the "Ticker" field, then delete it

**Expected Result:**
- Step 2: the "Add" button appears visually dimmed/disabled (cannot be clicked to submit) while the Ticker field is empty
- Step 3: after deleting the character back to empty, the button returns to its disabled appearance

---

### UT-25 — Stock Detail shows an honest "Unknown ticker" state, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3255/stocks/ZZZZZ`
2. Observe the page

**Expected Result:**
- No blank white page and no unhandled crash
- A warning card appears with the heading "**Unknown ticker**"
- Body text reads: "**"ZZZZZ" is not in the scanned universe. Open a stock from the leaderboard.**" with "leaderboard" as a clickable link back to `/stocks`

---

### UT-26 — Watchlist rejects adding an already-saved ticker (error)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- At least one ticker (e.g. AAPL, or the ABBV row added in UT-09) is already on the watchlist

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Note a ticker already present in the table (e.g. `ABBV`)
3. Type that SAME ticker into the "Ticker" field
4. Click "Add"

**Expected Result:**
- A red error line appears reading: "**`<TICKER>` is already on the watchlist**" (e.g. "ABBV is already on the watchlist")
- No duplicate row is added — the table still shows only one row for that ticker

---

### UT-27 — Chart range toggle is discoverable without instructions (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/stocks/MSFT` as a first-time user would (no prior knowledge of the toggle)
2. Scroll to the "Price & moving averages" card
3. Without hovering for a tooltip, look at the header row

**Expected Result:**
- The "Recent" / "Full history" control is immediately visible in the same row as the card title, using plain-English labels (not jargon or an icon-only control) — a new user should be able to guess it changes the chart's date range without needing a tooltip
- It visually groups with the existing "Regime on" toggle as a pair of related display controls, not buried in a menu

---

### UT-28 — "Stale series" exclusion reason is understandable without developer knowledge (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- `/data` loads with the 5-card diagnostic grid (UT-03 passed)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the "Universe resolution..." panel's 5-card grid
3. Read the "Stale series" card's label and the one-line definition text beneath its number (no hovering/clicking needed — the definition is always visible under the number)

**Expected Result:**
- The card is labeled "Stale series" in plain English (not a code identifier like `stale_series`)
- The definition sentence beneath it is understandable without backend knowledge, e.g. explains that a name whose price feed stopped updating exits the scored universe, and names the exact day threshold
- A reader unfamiliar with the codebase can explain in their own words why a stock might be excluded for this reason after reading only this card

---

### UT-29 — Anti-goal sweep: no buy/sell/price-target language anywhere (regression / ux)

**Type:** regression
**Priority:** P1
**Surface:** multi-page (`/`, `/stocks`, `/stocks/{ticker}`, `/backtest`, `/watchlist`)

**Preconditions:**
- Backend running

**Steps:**
1. Visit `http://localhost:3255/`, `/stocks`, `/stocks/AAPL`, `/backtest`, and `/watchlist` in turn
2. On each page, scan all visible text for buy/sell/order/price-target/return-promise language

**Expected Result:**
- No page contains words or phrases like "Buy now", "Sell", "Place order", a specific future price target, or a guaranteed-return promise
- All language stays in the descriptive/decision-support register already used throughout (e.g. "Actionable" setup status, "Not yet proven" evidence, forward-tested returns framed as historical/descriptive, never predictive promises)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stock Detail loads | smoke | P1 | `/stocks/{ticker}` |
| UT-02 | Leaderboard loads at broadened scale | smoke | P1 | `/stocks` |
| UT-03 | Data Manager loads with 5-card grid | smoke | P1 | `/data` |
| UT-04 | Evidence ledger loads with 7 rows | smoke | P1 | `/evidence` |
| UT-05 | Chart range toggle Recent ↔ Full history | happy-path | P1 | `/stocks/{ticker}` |
| UT-06 | AAPL caption discloses 1996-01-02 | happy-path | P1 | `/stocks/{ticker}` |
| UT-07 | NVDA caption discloses 1999-01-22 | happy-path | P1 | `/stocks/{ticker}` |
| UT-08 | ARM honest short history, no fabrication | happy-path | P1 | `/stocks/{ticker}` |
| UT-09 | Watchlist accepts broadened ticker + persists | happy-path | P1 | `/watchlist` |
| UT-10 | Broadened-pool detail page renders honestly | happy-path | P1 | `/stocks/{ticker}` |
| UT-11 | As-of floor reaches 2005-02-25 | happy-path | P2 | global switcher / `/backtest` |
| UT-12 | Staleness disclosure in Coverage + Diagnostic panels | happy-path | P2 | `/data` |
| UT-13 | Methodology per-date rule cites staleness | happy-path | P2 | `/methodology` |
| UT-14 | Every score badge reads "Not yet proven" (J-01) | regression | P1 | `/stocks` |
| UT-15 | Evidence row 1 byte-matches replay (J-03/J-11) | regression | P1 | `/evidence` |
| UT-16 | Breakout-watch regime label + FAIL (J-04) | regression | P1 | `/evidence` |
| UT-17 | Evidence ledger auditable + linkbacks (J-05) | regression | P1 | `/evidence` |
| UT-18 | No retired values anywhere (J-11 anti-goal) | regression | P1 | multi-page |
| UT-19 | Badge honestly non-interactive (J-02 partial) | regression | P2 | `/stocks/{ticker}` |
| UT-20 | Factor Lab caveat + cohort badges | regression | P2 | `/research/factor-lab` |
| UT-21 | Sector sort/filter null-safety | regression | P2 | `/stocks` |
| UT-22 | Backtest caveat discloses ~30 years | regression | P2 | `/backtest` |
| UT-23 | Watchlist rejects unknown ticker | validation | P2 | `/watchlist` |
| UT-24 | Add button disabled until ticker typed | validation | P3 | `/watchlist` |
| UT-25 | Stock Detail honest 404 state | error | P2 | `/stocks/{ticker}` |
| UT-26 | Watchlist rejects duplicate ticker | error | P2 | `/watchlist` |
| UT-27 | Chart range toggle discoverable | ux | P2 | `/stocks/{ticker}` |
| UT-28 | "Stale series" reason understandable | ux | P3 | `/data` |
| UT-29 | Anti-goal sweep — no buy/sell language | regression | P1 | multi-page |

**P1 tests must all pass for browser QA verdict to be PASS.** Given this iteration's honest all-FAIL
ledger reset, "PASS" for UT-14/UT-15/UT-16/UT-17/UT-18/UT-29 means confirming the HONEST DARK state
renders correctly everywhere — not that any score reads "Proven".
