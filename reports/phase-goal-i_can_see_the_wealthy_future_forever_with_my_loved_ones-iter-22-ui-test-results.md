# Goal Mode Iteration 22 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22
**Date:** 2026-06-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 15/15 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-79 | As-of stepping buttons + opt-in arrows + year/month dropdowns | target | P1 | ◀/▶ buttons step snapshot dates; checkbox enables ←/→ keys; keys ignored in search field; Year/Month dropdowns change viewed month only | ◀ stepped 2026-06-10→2026-06-09; ▶ stepped back; checkbox default-off, persisted after reload; ←/→ stepped date when enabled; field-guard blocked keys while search focused; Year/Month dropdowns changed viewed month without changing selected as-of | PASS | UT-J-79-step-buttons-pass.png, UT-J-79-field-guard-pass.png, UT-J-79-year-dropdown.png |
| UT-J-80 | Stocks header regime + Top-Themes strip + #n badges | target | P1 | Regime label+score matches Dashboard; ranked Top-Themes strip matches /themes order; #n badges on row chips and filter options; re-points on as-of change | At 2026-06-10: "Narrow leadership / 57.10" matched Dashboard; Top-Themes strip "1·Cybersecurity, 2·Semiconductors, 3·Ai Data Centre, 4·Software Cloud, 5·Homebuilders" matched /themes order; #n badges visible on every row's theme chips and filter options; at latest "Risk-on / 73.26" with re-ranked themes | PASS | UT-J-80-stocks-header.png, UT-J-80-latest-repoint.png |
| UT-J-18 | One date control (no duplicate) | regression | P1 | Backtest has no page-local date dropdown; global as-of drives it | /backtest has 0 `<select>` elements; loading `?asof=2026-06-10` showed "as of 2026-06-10" | PASS | none |
| UT-J-43 | Deep-linkable as-of | regression | P1 | ?asof=D in URL; historical indicator shown; leaderboard links carry ?asof | URL `?asof=2026-06-10` loaded with "Viewing as-of 2026-06-10 (historical)"; NVDA link href=`/stocks/NVDA?asof=2026-06-10` | PASS | none |
| UT-J-50 | As-of survives every in-app navigation | regression | P1 | All nav links embed ?asof when historical | All 10 nav links carried `?asof=2026-06-10` while historical | PASS | none |
| UT-J-62 | Calendar popover shows selectable dates | regression | P1 | Calendar opens with selectable days marked; "Latest" option; click picks date | Calendar opened as dialog; 1368 selectable dates shown; weekends absent (Jun 6,7 not in buttons); click on Jun 9 set ?asof=2026-06-09 | PASS | UT-J-79-calendar-open.png |
| UT-J-71 | Keyboard stepping with panel open | regression | P1 | ArrowLeft/ArrowRight step date while calendar popover open; popover stays open | At ?asof=2026-06-10, opened calendar, pressed ArrowLeft → date became 2026-06-09, URL updated, calendar remained open | PASS | none |
| UT-J-13 | Browse dashboard as of past date | regression | P1 | Historical indicator; data reflects that date; return to latest works | "Viewing as-of 2026-06-10 (historical)" badge shown; "Data as-of 2026-06-10" content loaded; different regime/scores than latest | PASS | UT-J-79-historical-selected.png |
| UT-J-06 | Score consistency across pages | regression | P1 | NVDA scores identical on leaderboard and detail page | Leaderboard: E/40.54, D/69.55, E/32.59; Detail: all three values present (confirmed 40.54, 69.55, 32.59) | PASS | none |
| UT-J-02 | Stock leaderboard with working filters | regression | P1 | Ranked rows with scores/setup; sector filter reduces rows; Actionable filter works | 122 ranked rows with Leadership/Entry Quality/Risk/Setup; Technology filter: 58/122; Actionable filter at latest: 0/122 (correct — 0 Actionable at latest) | PASS | none |
| UT-J-03 | Theme leaderboard | regression | P1 | At least 3 themes ranked by Theme Score; top theme shows returns/breadth/trend | Themes page showed Semiconductors, Cybersecurity, Crypto Equities ranked with Theme Score, 1M, 3M, Breadth, Trend columns | PASS | none |
| UT-J-48 | Stocks leaderboard column sorting | regression | P1 | Click column header → rows re-order; asc/desc toggle; sort indicator shown | LEADERSHIP column sort: ascending showed COIN/MSTR/INTU (lowest); descending showed MRVL/ARM/MU (highest); `aria-sort` indicator updated correctly | PASS | none |
| UT-J-55 | Stocks leaderboard symbol search | regression | P1 | Type-to-filter on ticker/name; no submit required; honest count | Typed "nv" → 4/122 rows (NVT, NVO, NVR, NVDA) instantly filtered | PASS | none |
| UT-J-56 | Stocks leaderboard theme column + theme filter | regression | P1 | Theme column shows chips; theme filter reduces to matching rows | Theme column shows #n-badged chips; Cybersecurity filter → 11/122 rows (FTNT, OKTA, PANW, CRWD, etc.) | PASS | none |
| UT-J-75 | Forward returns on leaderboard | regression | P1 | 1D/5D/10D/20D/60D columns; populated at historical D with post-D bars; NA at latest | At ?asof=2026-06-09: 1D/5D/10D/20D/60D columns present; MRVL 1D=-5.35% (1 bar), 5D/10D/20D/60D=NA; at latest all NA | PASS | UT-J-75-fwd-returns.png |

---

## Passed Tests

### UT-J-79 — As-of stepping buttons + opt-in arrows + year/month dropdowns
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22-evidence/UT-J-79-step-buttons-pass.png`

- **Step 1 (◀/▶ buttons):** Navigated to `?asof=2026-06-10`. Clicked `[data-testid="asof-step-prev"]` → URL became `?asof=2026-06-09` (stepped to previous available snapshot date). Clicked `[data-testid="asof-step-next"]` → URL returned to `?asof=2026-06-10`. Calendar popover was closed throughout; page re-read without covering the view.
- **Step 2 (opt-in checkbox):** `[data-testid="asof-arrow-toggle"]` was `checked=false` by default. Clicked it → `checked=true`. Focused document body (h1 click), pressed ArrowLeft → URL became `?asof=2026-06-09`. Pressed ArrowRight → URL became `?asof=2026-06-10`. Reloaded page → checkbox still `checked=true` (persisted to localStorage).
- **Step 3 (Year/Month dropdowns):** Opened calendar popover; Year and Month `<select>` dropdowns visible (years 2021–2026, months Jan–Dec). Used native setter + bubbling change event to set year=2025 → calendar header changed to "2025-06". Set month=Jan → header changed to "2025-01". URL remained `?asof=2026-06-10` throughout (dropdowns changed viewed month only, no second date state).
- **Step 4 (boundary — no-op at latest):** Navigated to `/` (latest). `[data-testid="asof-step-next"]` had `disabled=true`. Pressed ArrowRight with body focused → no DOM change, URL unchanged.
- **Step 5 (field-guard):** On `/stocks?asof=2026-06-10`, clicked `[data-testid="stocks-search"]` (activeElement=INPUT:stocks-search). Pressed ArrowLeft → no DOM change, URL still `?asof=2026-06-10`. Field-guard correctly suppressed the key.

### UT-J-80 — Stocks header regime + Top-Themes strip + #n badges
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22-evidence/UT-J-80-stocks-header.png`

- **Step 1-2 (regime label+score):** At `?asof=2026-06-10`, `/stocks` header showed "MARKET REGIME / Narrow leadership / 57.10" — identical to Dashboard at the same date (verified from same-session navigation).
- **Step 3 (Top-Themes strip):** Strip showed "1·Cybersecurity, 2·Semiconductors, 3·Ai Data Centre, 4·Software Cloud, 5·Homebuilders" — same descending order as /themes for that date.
- **Step 4 (#n badges):** Every row's theme chips showed rank badges (e.g. "#1 Cybersecurity", "#2 Semiconductors", "#3 Ai Data Centre"). Theme filter options showed "#1 · Cybersecurity", "#2 · Semiconductors", "#3 · Ai Data Centre", etc.
- **Step 5 (re-points on as-of change):** Navigated to `/stocks` (latest, 2026-06-15) → header changed to "MARKET REGIME / Risk-on / 73.26" and Top-Themes strip changed to "1·Semiconductors, 2·Cybersecurity, 3·Crypto Equities, 4·Ai Data Centre, 5·Homebuilders" — confirming both re-pointed to the new date.
- **Coherence check:** Regime and theme order at latest matched the Dashboard top-level display (Risk-on/73.26; Semiconductors #1, Cybersecurity #2).

### UT-J-18 — One date control
**Verdict:** PASS
- `/backtest` has 0 `<select>` elements (no page-local date picker). Loading `/backtest?asof=2026-06-10` showed "as of 2026-06-10" confirming global as-of drives it.

### UT-J-43 — Deep-linkable as-of
**Verdict:** PASS
- Loading `/stocks?asof=2026-06-10` showed "Viewing as-of 2026-06-10 (historical)"; NVDA row link href embedded `?asof=2026-06-10`.

### UT-J-50 — As-of survives every navigation
**Verdict:** PASS
- All 10 nav sidebar links carried `?asof=2026-06-10` while historical. At latest, nav links were date-free.

### UT-J-62 — Calendar popover
**Verdict:** PASS
- Calendar opens as `[role="dialog"]`; 1368 selectable dates; Jun 6/7 absent (weekends); "Latest" affordance present; clicking "View as-of 2026-06-09" set `?asof=2026-06-09` and historical badge appeared.

### UT-J-71 — Keyboard stepping with panel open
**Verdict:** PASS
- Opened calendar at `?asof=2026-06-10`; pressed ArrowLeft → URL became `?asof=2026-06-09`, switcher showed "2026-06-09", calendar dialog remained open.

### UT-J-13 — Browse dashboard as of past date
**Verdict:** PASS
- Loading `/?asof=2026-06-10` showed historical badge and date-appropriate data (Narrow leadership / 57.10, different from latest Risk-on / 73.26).

### UT-J-06 — Score consistency
**Verdict:** PASS
- NVDA leaderboard scores (E/40.54, D/69.55, E/32.59) matched detail page (same three values present).

### UT-J-02 — Stock leaderboard filters
**Verdict:** PASS
- 122 ranked rows with bucketed scores and setup statuses; Technology sector filter: 58/122; Actionable filter at latest: 0/122.

### UT-J-03 — Theme leaderboard
**Verdict:** PASS
- Themes ranked with Theme Score, 1M, 3M returns, Breadth %, Trend label; at least 5 themes shown.

### UT-J-48 — Column sorting
**Verdict:** PASS
- LEADERSHIP asc: lowest-scored stocks first (COIN, MSTR, INTU); desc: highest first (MRVL, ARM, MU); `aria-sort` indicator updated correctly on each click.

### UT-J-55 — Symbol search
**Verdict:** PASS
- Typed "nv" → instant filter to 4/122 rows (NVT, NVO, NVR, NVDA); no submit required.

### UT-J-56 — Theme column + filter
**Verdict:** PASS
- Theme column shows #n-badged chips; Cybersecurity filter → 11/122 rows (all known cybersecurity stocks).

### UT-J-75 — Forward returns on leaderboard
**Verdict:** PASS
- 1D/5D/10D/20D/60D columns present at `?asof=2026-06-09`; MRVL 1D=-5.35% (1 post-D bar), longer horizons NA; at latest all NA.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-16
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22-evidence/`
