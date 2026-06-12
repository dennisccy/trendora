# Goal Iter-5 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5
**Date:** 2026-06-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-48 | Leaderboard column sorting | happy-path | P1 | All column headers sortable, one indicator, `#` restores rank, values unchanged | All 7 columns sort with asc/desc toggle; exactly one aria-label indicator active; `#` restores stored rank (MRVL=1, A94.30 unchanged); filter+sort compose; empty-state on zero match | PASS | UT-J-48-restore-rank.png |
| UT-J-50 | As-of href embedding in every in-app link | happy-path | P1 | While historical D, every sidebar/leaderboard/research/watchlist href carries `?asof=D`; at latest hrefs are clean | All sidebar + leaderboard row + research/scanner-runs/sectors/themes/watchlist hrefs carry `?asof=2026-06-05`; fresh-tab direct URL restores historical indicator; switching to latest produces clean hrefs | PASS | UT-J-50-historical-hrefs.png |
| UT-J-54 | Leaderboard ticker opens in new tab | happy-path | P1 | Ticker links have `target="_blank"` + `rel="noopener noreferrer"`; href carries `?asof=D` historical, clean at latest; sidebar links stay same-window | Leaderboard tickers: target=`_blank`, rel=`noopener noreferrer`, href `/stocks/MRVL?asof=2026-06-05` at historical; clean `/stocks/MRVL` at latest; sidebar nav links have no target | PASS | UT-J-54-ticker-new-tab.png |
| UT-J-02 | Stock leaderboard with working filters (with sort active) | regression | P1 | Ranked rows with bucketed scores; sector filter narrows rows; setup filter narrows further; explicit empty-state when no match; composes with active sort | 122 rows with #, ticker, sector, Leadership A-E+score, EQ, Risk, Setup, Reason; Leadership sort active; Technology+Actionable filter returns explicit empty-state "No VCP-flagged…"; sort indicator preserved throughout | PASS | UT-J-02-sort-filter-compose.png |
| UT-J-05 | Stock detail with explainable scores (NVDA) | regression | P1 | Price chart, three scores with A-E bucket + numeric + component breakdowns, theme membership, setup, invalidation | NVDA detail shows Leadership, Entry Quality, Risk each with bucket+numeric; "Top driver: moving-average stack" component breakdown; theme chips (Ai Data Centre, Semiconductors, Megacap Leaders); setup + invalidation below 50-DMA at $205.76 | PASS | UT-J-05-nvda-detail.png |
| UT-J-06 | Score consistency across pages (NVDA leaderboard vs detail) | regression | P1 | NVDA Leadership, Entry Quality, Risk scores identical on leaderboard and detail page | Leaderboard: E43.14, E54.05, E35.80; Detail page contains 43.14, 54.05, 35.80 — all three values confirmed present and identical | PASS | UT-J-06-nvda-coherence.png |
| UT-J-13 | Browse dashboard as of a past date | regression | P1 | Selecting past date re-points all pages; historical indicator shown; returning to latest clears param | Selected 2026-06-05: URL `/?asof=2026-06-05`, "Viewing as-of 2026-06-05 (historical)" visible, all nav links carry param; switched to latest: URL clean, no historical text | PASS | UT-J-13-asof-switcher.png |
| UT-J-16 | VCP filter and glossary (with sort active) | regression | P1 | VCP filter shows flagged rows or explicit empty-state; VCP documented in /methodology | VCP-only filter returns explicit empty-state message; /methodology shows "VCP — Volatility Contraction Pattern" with plain-language definition; sort indicator preserved | PASS | UT-J-16-vcp-methodology.png |
| UT-J-18 | One date control — no duplicate on /backtest | regression | P1 | /backtest has no page-local date dropdown; global switcher drives it | Only 1 select element on /backtest (the global "View as-of date"); switching to 2026-06-05 changes URL to `backtest?asof=2026-06-05` | PASS | UT-J-18-backtest-one-date.png |
| UT-J-43 | As-of survives reload and invalid param degrades safely | regression | P1 | Reload preserves `?asof`; invalid `?asof` degrades to latest with no crash | Reload of `stocks?asof=2026-06-05` kept param; `?asof=9999-99-99` silently degraded to clean `/stocks` with latest data (122 rows, rank #1 MRVL), no crash, no error page | PASS | UT-J-43-invalid-asof-degrades.png |

---

## Passed Tests

### UT-J-48 — Leaderboard column sorting
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-48-restore-rank.png`

- Default order: MRVL=1, MU=2, DELL=3 — stored rank ascending; `#` header aria-label="Sort by #, ascending" with SVG indicator.
- Clicked Leadership: aria-label changed to "Sort by leadership, ascending"; rows reordered (COIN #122 first). Exactly one active indicator.
- Clicked Leadership again: "Sort by leadership, descending"; MRVL (highest leadership) moved to top.
- Sorted Ticker (AAPL first, alphabetical), Sector (Communication Services first), Entry Quality, Risk, Setup in turn — each produced one active indicator.
- Applied Technology sector + Actionable setup filters with setup-sort active: explicit empty-state "No stocks match these filters / No stock is currently 'Actionable' in Technology."
- Clicked `#`: MRVL returned to rank 1, Technology filter still applied; MRVL's scores post-restore: Leadership A94.30, Entry Quality E23.35, Risk E59.43 — identical to pre-sort initial state. No value changed.

---

### UT-J-50 — As-of href embedding
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-50-historical-hrefs.png`

- Selected 2026-06-05 via the as-of switcher (`select` action); URL became `stocks?asof=2026-06-05`.
- DOM inspection confirmed every in-app href carries `?asof=2026-06-05`: sidebar entries (`/?asof=2026-06-05`, `/stocks?asof=2026-06-05`, `/themes?asof=2026-06-05`, `/sectors?asof=2026-06-05`, `/scanner-runs?asof=2026-06-05`, `/backtest?asof=2026-06-05`, `/research?asof=2026-06-05`, `/watchlist?asof=2026-06-05`, `/methodology?asof=2026-06-05`, `/data?asof=2026-06-05`) and all leaderboard row links (`/stocks/MRVL?asof=2026-06-05`, etc.).
- Opened `http://localhost:3835/stocks/MRVL?asof=2026-06-05` directly in a new tab: `window.location.href` confirmed `stocks/MRVL?asof=2026-06-05`; historical indicator "Bars after the as-of date 2026-06-05 are display-only" visible; all sidebar links carried param.
- Switched to latest: URL became clean `/stocks`, all hrefs clean (no `?asof`), no historical indicator.

---

### UT-J-54 — Leaderboard ticker opens new tab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-54-newtab-detail.png`

- At historical date 2026-06-05: `tbody tr td a[href*="/stocks/"]` anchors: MRVL has `target="_blank"`, `rel="noopener noreferrer"`, `href="/stocks/MRVL?asof=2026-06-05"`.
- First 3 tickers (MRVL, ARM, MU) all have same attributes — confirmed via eval.
- At latest: same tickers have `target="_blank"`, `rel="noopener noreferrer"`, but `href="/stocks/MRVL"` (clean, no param).
- New tab opened with `stocks/MRVL?asof=2026-06-05`: landed on MRVL detail, URL confirmed, "as-of date 2026-06-05" visible in page text, all sidebar links carried `?asof=2026-06-05`.
- Sidebar nav links confirmed `target=null` — no new-tab for non-leaderboard-ticker links.
- Originating leaderboard tab was confirmed at `http://localhost:3835/stocks?asof=2026-06-05` before the new tab opened (tab list showed URL correctly).

---

### UT-J-02 — Stock leaderboard with working filters
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-02-sort-filter-compose.png`

- 122 rows, headers: `#`, `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Setup`, `Reason`.
- First row: `1 | MRVL | Technology | A94.30 | E23.35 | E59.43 | Extended | Strong leader…`
- Leadership sort active; Technology + Actionable filters applied: explicit empty-state returned ("No stock is currently 'Actionable' in Technology. No rows are fabricated…") — confirms filter composition with active sort, and correct empty-state behavior.

---

### UT-J-05 — Stock detail with explainable scores
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-05-nvda-detail.png`

- NVDA detail page: three score sections (Leadership, Entry Quality, Risk) present; A-E bucket + numeric present; component breakdown present ("Top driver: moving-average stack", "RS vs SPY", "Top driver" phrases in page text).
- Theme chips: Ai Data Centre, Semiconductors, Megacap Leaders.
- Invalidation note: "Invalid below the 50-DMA at $205.76".
- Setup status visible ("AvoidPullback" / setup text present).
- VCP section: "No VCP pattern detected."
- Pattern section: "Pulled back to a rising 50-day MA (up 13.0% over 40 bars)…" with pivot + invalidation for pullback_to_rising_dma pattern.

---

### UT-J-06 — Score consistency (NVDA leaderboard vs detail)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-06-nvda-coherence.png`

- Leaderboard NVDA row: Leadership E43.14, Entry Quality E54.05, Risk E35.80 (rank #74).
- Detail page `/stocks/NVDA`: confirmed all three values 43.14, 54.05, 35.80 present — one computed value per score, identical across both views.

---

### UT-J-13 — Browse as of a past date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-13-asof-switcher.png`

- Selected 2026-06-05 on `/`: URL became `/?asof=2026-06-05`, "Viewing as-of 2026-06-05 (historical)" indicator confirmed.
- Navigated to `stocks?asof=2026-06-05`: same historical indicator "Viewing as-of 2026-06-05 (historical)" visible.
- Switched to latest (navigate to clean `/stocks`): URL clean, no "historical" text, `asofInUrl=false`.

---

### UT-J-16 — VCP filter and glossary (with sort active)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-16-vcp-methodology.png`

- Leadership sort active on `/stocks`; VCP-only filter applied: explicit empty-state "No VCP-flagged name is currently shown. No rows are fabricated to fill the view — clear a filter to see more."
- `/methodology` page: VCP entry found — "VCP — Volatility Contraction Pattern / Pattern / A price-and-volume base of progressively shallower pullbacks with volume drying up into a pivot near the highs. A detected PATTERN that rides ALONGSIDE the…"
- VCP is documented as a pattern (not status), with plain-language description.

---

### UT-J-18 — One date control on /backtest
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-18-backtest-one-date.png`

- `/backtest` has exactly 1 select element: `aria-label="View as-of date"` (the global switcher). No page-local date dropdown.
- Switching global switcher to 2026-06-05: URL became `backtest?asof=2026-06-05`, confirming the single global control drives Backtest.

---

### UT-J-43 — As-of survives reload; invalid param degrades safely
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/UT-J-43-invalid-asof-degrades.png`

- Reload of `stocks?asof=2026-06-05`: URL remained `stocks?asof=2026-06-05` after `location.reload()`.
- Click-through already confirmed: `stocks?asof=2026-06-05` → `stocks/MRVL?asof=2026-06-05` (via href with param).
- Invalid param `?asof=9999-99-99`: URL silently became clean `/stocks`, no "historical" indicator, no crash, 122 rows with rank #1 — degraded to latest view.

---

## Failed Tests

*(none)*

---

## Skipped Tests

*(none)*

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-12
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-evidence/`
