# Goal Iteration 25 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25
**Date:** 2026-06-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-83 | As-of deep link — no hydration mismatch (server-aware seeding) | happy-path | P1 | Deep link at ?asof=D renders at D from first paint; no hydration error; History icon from first paint; sidebar hrefs carry ?asof; invalid degrades to latest | No hydration error in shadow DOM; badge "Viewing as-of 2026-06-10 (historical)" with lucide-history icon; all 10 sidebar links carry ?asof=2026-06-10; reload and new-tab both clean; invalid ?asof=not-a-date and well-formed ?asof=2020-01-01 both degrade to latest URL with no error | PASS | UT-J-83-final.png |
| UT-J-73 | No as-of date flash — first data fetch at D | regression | P1 | Page renders data at D immediately; no latest→D flash | "Data as-of 2026-06-10" on dashboard when arriving at ?asof=2026-06-10; History icon present from first paint; no hydration error | PASS | UT-J-73-pass.png |
| UT-J-18 | One date control — no page-local date picker on /backtest | regression | P1 | /backtest has 0 page-local selects or date inputs; global switcher drives date | 0 page-local date selects, 0 date inputs on /backtest?asof=2026-06-10; global asof-trigger button present; badge "Viewing as-of 2026-06-10 (historical)" | PASS | UT-J-18-pass.png |
| UT-J-43 | ?asof serialize + invalid→latest degrade | regression | P1 | ?asof=yyyy-MM-dd in URL while historical; invalid degrades to latest | /stocks?asof=2026-06-10 shows correct badge; URL carries param; invalid ?asof=not-a-date strips to / with no badge; well-formed unknown ?asof=2020-01-01 strips to / | PASS | UT-J-43-pass.png |
| UT-J-50 | ?asof in every in-app href including new-tab links | regression | P1 | All nav links and stock-detail hrefs embed ?asof while historical | On /stocks?asof=2026-06-10: all 10 nav links carry ?asof=2026-06-10; 0 nav links missing param; 122 stock-detail row links carry ?asof; 0 missing it | PASS | UT-J-50-pass.png |
| UT-J-13 | Browse dashboard as of a past date | regression | P1 | Select past date from calendar; badge + data reflect that date; switch back to latest | Selected 2026-06-10 via calendar popover; URL became ?asof=2026-06-10; badge "Viewing as-of 2026-06-10 (historical)"; "Data as-of 2026-06-10" confirmed; regime "Narrow leadership" shown | PASS | UT-J-13-pass.png |
| UT-J-42 | Every user-facing date reads yyyy-MM-dd | regression | P1 | No locale-formatted dates; all dates in ISO yyyy-MM-dd | Dashboard at ?asof=2026-06-10: all dates match yyyy-MM-dd (2026-06-10, 2026-06-16); zero locale-formatted dates detected | PASS | UT-J-42-pass.png |
| UT-J-62 | As-of switcher is a calendar showing selectable dates | regression | P1 | Calendar popover with selectable snapshot dates, disabled non-snapshot days, Latest shortcut, year/month dropdowns | Calendar opened: 12 selectable snapshot dates (2026-06-01 through 2026-06-16); year/month dropdown found; "View as-of 2026-06-16 (latest)" present; Escape closes cleanly | PASS | UT-J-62-calendar.png |
| UT-J-79 | ◀▶ buttons + opt-in arrow stepping | regression | P1 | ◀ steps to prev snapshot; ▶ steps to next; URL updates; arrow-key checkbox present | ◀ stepped 2026-06-10 → 2026-06-09, URL updated; ▶ stepped 2026-06-10 → 2026-06-11, URL updated to ?asof=2026-06-11; checkbox for "← → steps date" present | PASS | UT-J-79-stepping.png |
| UT-J-80 | /stocks shows regime label + theme ranking | regression | P1 | Regime label + score from stored run; Top-Themes strip with #n rank badges | /stocks?asof=2026-06-10: regime "Narrow leadership" shown; Top-Themes strip: #1 Cybersecurity, #2 Semiconductors, #3 Ai Data Centre, #4 Software Cloud, #5 Homebuilders | PASS | UT-J-80-pass.png |
| UT-J-20 | Price chart shows full path through latest date with as-of marker | regression | P1 | Chart extends to latest seed date; as-of marker; post-D region labelled display-only | NVDA detail at ?asof=2026-06-10: chart canvas present (7 canvases); "Full path through 2026-06-16"; "Bars after the as-of date 2026-06-10 are display-only"; "Forward — after as-of 2026-06-10 (display only)" label present | PASS | UT-J-20-stock-detail.png |
| UT-J-45 | Market-regime bands behind stock-detail price chart | regression | P1 | Regime band overlays on stock-detail chart clamped at as-of date | NVDA detail: regime band legends "Risk-on regime", "Neutral regime", "Risk-off regime" present; "Regime on" indicator shown; 7 chart canvases (price + overlays); clamped at 2026-06-10 | PASS | UT-J-45-regime-bands.png |

---

## Passed Tests

### UT-J-83 — As-of deep link renders with no React hydration mismatch (server-aware seeding)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-83-final.png`

Key verifications:
- Navigated directly to `http://localhost:3835/?asof=2026-06-10` — nextjs-portal shadow root contained only 3 STYLE elements (no error dialogs); "Hydration failed", "server rendered HTML", "did not match" all absent from shadow
- As-of badge "Viewing as-of 2026-06-10 (historical)" visible from first paint with `lucide-history` (History icon, not Clock)
- All 10 sidebar nav links carry `?asof=2026-06-10` from server-rendered HTML
- Reload: same clean result — no hydration error, History icon, badge at D, 10 asof links
- New tab: same clean result — no hydration error, badge at D, 10 asof links
- Latest URL (`http://localhost:3835/`): no hydration error, Clock icon, "Latest" label, 0 sidebar links with ?asof
- Invalid `?asof=not-a-date`: degraded to `/` URL, no "Viewing as-of", no wrong date shown, no hydration error
- Well-formed unknown `?asof=2020-01-01`: degraded to `/` URL, no wrong date, no hydration error
- Client-side navigation: ◀ button stepped date to 2026-06-09 with URL update; calendar opened correctly with year/month dropdowns; client nav unchanged

---

### UT-J-73 — No as-of date flash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-73-pass.png`
- "Data as-of 2026-06-10" rendered on dashboard for `?asof=2026-06-10` deep link — first data fetch is already at D, not at latest
- History icon present from first paint; no hydration error

---

### UT-J-18 — One date control
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-18-pass.png`
- `/backtest?asof=2026-06-10`: 0 page-local `<select>` elements, 0 `<input type="date">` elements
- Global `[data-testid="asof-trigger"]` button present; badge "Viewing as-of 2026-06-10 (historical)"

---

### UT-J-43 — ?asof serialize + invalid degrade
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-43-pass.png`
- `/stocks?asof=2026-06-10`: URL carries param, badge correct
- Invalid `?asof=not-a-date`: URL stripped to `http://localhost:3835/`, showing latest view
- Well-formed unknown `?asof=2020-01-01`: same degradation

---

### UT-J-50 — ?asof in every in-app href
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-50-pass.png`
- All 10 nav links: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager — all carry `?asof=2026-06-10`
- 122 stock-detail row links on leaderboard all carry `?asof=2026-06-10`; 0 missing the param

---

### UT-J-13 — Browse dashboard as of a past date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-13-pass.png`
- Opened calendar on `/` (latest); calendar showed 12 selectable snapshot dates
- Clicked "View as-of 2026-06-10"; URL became `?asof=2026-06-10`
- Badge "Viewing as-of 2026-06-10 (historical)", "Data as-of 2026-06-10", regime "Narrow leadership" confirmed

---

### UT-J-42 — yyyy-MM-dd date format
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-42-pass.png`
- All visible dates: 2026-06-10, 2026-06-16 — ISO yyyy-MM-dd format
- Zero locale-formatted dates (no mm/dd/yyyy, no "Month dd, yyyy")

---

### UT-J-62 — Calendar popover shows selectable dates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-62-calendar.png`
- Calendar opened with 12 "View as-of" date buttons (2026-06-01 through 2026-06-16)
- "View as-of 2026-06-16 (latest)" present as the latest affordance
- Year/month `<select>` dropdown found
- Escape closes cleanly

---

### UT-J-79 — ◀▶ stepping + opt-in arrows
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-79-stepping.png`
- "Previous available date" and "Next available date" buttons present
- ◀ stepped 2026-06-10 → 2026-06-09; URL updated to `?asof=2026-06-09`; badge confirmed
- ▶ stepped 2026-06-10 → 2026-06-11; URL updated to `?asof=2026-06-11`; badge confirmed
- Arrow-key opt-in checkbox present in top bar

---

### UT-J-80 — /stocks shows regime + theme ranking
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-80-pass.png`
- Regime label "Narrow leadership" shown on /stocks for 2026-06-10
- Top-Themes strip with rank badges: #1 Cybersecurity, #2 Semiconductors, #3 Ai Data Centre, #4 Software Cloud, #5 Homebuilders

---

### UT-J-20 — Price chart full path through latest with as-of marker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-20-stock-detail.png`
- NVDA detail at `?asof=2026-06-10`: 7 chart canvases rendered
- "Full path through 2026-06-16" — chart extends past as-of date to latest seed date
- "Bars after the as-of date 2026-06-10 are display-only — they don't affect the scores, setup, or VCP flag"
- "Forward — after as-of 2026-06-10 (display only)" label visible

---

### UT-J-45 — Regime bands on stock-detail chart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/UT-J-45-regime-bands.png`
- Regime band legends: "Risk-on regime", "Neutral regime", "Risk-off regime" present
- "Regime on" indicator shown; 7 chart canvases (price + MA + regime overlays)
- Bands clamped at as-of date 2026-06-10

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (DevTools at :9222)
- **Test Date:** 2026-06-17
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-25-evidence/`
- **Test date used:** 2026-06-10 (historical snapshot with post-date bars available)
