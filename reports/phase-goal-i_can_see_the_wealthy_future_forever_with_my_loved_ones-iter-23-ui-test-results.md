# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23
**Date:** 2026-06-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 23/23 tests passed (0 skipped, 0 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Themes leaderboard loads with five forward-return column headers | smoke | P1 | Five column headers (1d/5d/10d/20d/60d) visible, no error | All five headers present (1D, 5D, 10D, 20D, 60D), all NA at latest date, no error | PASS | UT-01-result.png |
| UT-02 | Sectors leaderboard loads with five forward-return column headers | smoke | P1 | Five column headers (1d/5d/10d/20d/60d) visible, no error | All five headers present, 31 sector rows, no error | PASS | UT-02-result.png |
| UT-03 | Research page loads with RSP filter dropdowns visible | smoke | P1 | Three filter dropdowns (Regime/Setup/Pattern) visible, default "All" | Three selects found with "All regimes"/"All setups"/"All patterns" defaults; RSP table loaded | PASS | UT-03-result.png |
| UT-04 | Themes forward-return columns display numeric values at historical as-of | happy-path | P1 | Numeric % values in 1d–60d cols at 2025-01-15; green/red colour grading | All 11 themes show numeric values (e.g. Megacap +2.96%, Nuclear +14.18%); child elements: green rgb(52,211,153) for positive, red rgb(248,113,113) for negative | PASS | UT-04-result.png |
| UT-05 | Sectors forward-return columns display numeric values at historical as-of | happy-path | P1 | Numeric % values in 1d–60d cols at 2025-01-15; NA for ETFs without bars | Sector ETFs (XLF, XLE, XLC etc.) show numeric values; industry ETFs without bars show NA in muted grey rgb(139,152,169); colour grading confirmed | PASS | UT-05-result.png |
| UT-06 | Themes leaderboard can be sorted by the 5d forward-return column | happy-path | P1 | First click: rows sort desc then asc; NA at bottom; no page reload | 5d sort button found; first click: descending (+15.25%→-2.52%); second click: ascending (-2.52%→+15.25%); no network spinner; all theme names intact | PASS | UT-06-sorted-asc.png |
| UT-07 | Sectors leaderboard can be sorted by the 20d forward-return column | happy-path | P1 | First click: desc with NA at bottom; second click: asc with NA at bottom | 20d button clicked; first click: descending (+7.80%→-3.09%), NA rows (20 of 31) at bottom; second click: ascending (-3.09%→+7.80%), NA rows still at bottom; numericAfterNaCount=0 | PASS | UT-07-sorted-asc-na-bottom.png |
| UT-08 | Research RSP section defaults to Pooled view on page load | happy-path | P1 | RSP Episodes/Pooled toggle shows Pooled active; Event Study shows Episodes | aria-pressed: RSP Pooled=true, RSP Episodes=false; Event Study Episodes=true, Event Study Pooled=false — confirmed on fresh load | PASS | UT-08-rsp-pooled-default.png |
| UT-09 | Research RSP Regime filter narrows the table to matching rows | happy-path | P1 | Table redraw showing only rows for selected regime; no page reload | Set Regime="Risk-on" via native-setter+bubbling change; links dropped 157→76; all 18 visible RSP rows confirmed regime="Risk-on" | PASS | none |
| UT-10 | Research RSP Regime + Pattern filters compose correctly | happy-path | P1 | AND logic: only rows matching both Regime AND Pattern shown | Regime=Risk-on + Pattern=vcp: 4 rows (down from 18 regime-only); all showing Risk-on+vcp; reset both to "All" restored 162 links | PASS | none |
| UT-11 | Research RSP numeric sort pushes NA rows to bottom (ascending) | happy-path | P1 | Numeric rows first (smallest→largest); NA rows below all numeric | Sorted by Mean ascending: -2.28%→+8.71% in rows 0-64; firstNaIdx=65; numericAfterNaCount=0; 99 total rows | PASS | UT-11-12-rsp-sort-na-bottom.png |
| UT-12 | Research RSP numeric sort keeps NA rows at the bottom (descending) | happy-path | P1 | Numeric rows first (largest→smallest); NA rows still at bottom | Sorted by Mean descending: +8.71%→-2.28% in rows 0-64; firstNaIdx=65; numericAfterNaCount=0; last 3 rows all NA | PASS | UT-11-12-rsp-sort-na-bottom.png |
| UT-13 | Research RSP N= chip for standard pattern row opens samples without error | happy-path | P1 | New tab opens /research/samples with correct N count, no error | Navigated to samples for Narrow leadership/Extended/flat_base_breakout N=33; page heading "Research Samples — observation drill-down"; table with 33 rows; no error | PASS | UT-13-samples-named-pattern.png |
| UT-14 | Research RSP N= chip for "none" pattern row opens samples without error | happy-path | P1 | New tab for pattern=none opens /research/samples with matching N, no error | Navigated to samples for Defensive/Extended/pattern=none N=484; table with 484 rows; slice shows "— (no pattern)"; no error | PASS | UT-14-samples-none-pattern.png |
| UT-15 | Forward-return cells show "NA" not "0%" at the latest as-of date | validation | P2 | All 60d (and 20d/10d) cells show "NA" in muted text, not "0%" or blank | All 11 themes at 2026-06-15 show NA in all 5 fwd-return cols; zeroIn60d=0; naIn60d=11; no blank cells | PASS | none |
| UT-16 | Research RSP empty-after-filter state shows an informative message | validation | P2 | Clear non-broken empty state message when no rows match filters | Applied Risk-off+Actionable setup: RSP table absent from DOM; page text shows "No combinations match these filters — No (regime, setup, pattern) combination matches the current filter selection. Reset a filter to 'All' to widen the view" | PASS | UT-16-rsp-empty-state.png |
| UT-17 | Themes existing columns still work after forward-return additions | regression | P1 | Original columns (#, Theme, Theme Score, 1m, 3m, Breadth, Trend) present and populated; row click works | All original columns populated (existingColsPopulated=true); headers: #/Theme/Theme Score/1m/3m/Breadth/1d/5d/10d/20d/60d/Trend; row onclick works (role=button, cursor=pointer) | PASS | none |
| UT-18 | Sectors existing columns still work after forward-return additions | regression | P1 | Original sector columns (#, Ticker, Kind, Sector Score, RS vs SPY, Dist, Trend) present; 31 rows | Headers: #/Ticker/Kind/Sector Score/RS vs SPY/Dist. 52w high/1d/5d/10d/20d/60d/Trend; rowCount=31; existingColsOk=true | PASS | none |
| UT-19 | Research Event Study / Cluster sections still default to Episodes | regression | P1 | Event Study toggle shows Episodes active; not affected by RSP Pooled default | On fresh /research load: Event Study Episodes=aria-pressed:true, Event Study Pooled=aria-pressed:false; RSP Pooled=true unaffected | PASS | none |
| UT-20 | Themes/Sectors forward-return sort resets to default order after navigation | regression | P2 | After sort + navigate away + return, rows back in default served order | Sorted themes by 5d (ascending: Homebuilders first); navigated to /sectors then back to /themes; row order returned to default score-ranked (Megacap Leaders first); sort state did NOT persist | PASS | none |
| UT-21 | Themes forward-return value matches Backtest value for same date + horizon | regression | P1 | /themes 5d value for Megacap Leaders = /backtest 5d value for Megacap Leaders | /themes at 2025-01-15: Megacap Leaders 5d=+2.96%; /backtest at 2025-01-15 (horizon switched to 5d): Megacap Leaders FWD 5D=+2.96% — exact match | PASS | none |
| UT-22 | New forward-return columns are discoverable without instructions | ux | P2 | Labels readable without scroll; pointer cursor; sort affordance visible | All 5 buttons (1d/5d/10d/20d/60d): cursor=pointer; aria-label="Sort by Xd"; class includes hover transitions; table width 1646px < viewport 1920px (no horizontal scroll) | PASS | UT-22-themes-columns-discoverable.png |
| UT-23 | RSP filter dropdowns are discoverable in the section controls row | ux | P2 | Three dropdowns co-located with Pooled toggle; labelled; default "All" visible | Regime/Setup/Pattern selects visible (offsetParent!=null); all at top≈3014px (same row as Pooled toggle at top≈3015px); grandparent text shows "REGIME"/"SETUP"/"PATTERN" labels; defaults "All regimes"/"All setups"/"All patterns" | PASS | UT-23-rsp-filters-discoverable.png |

---

## Passed Tests

### UT-01 — Themes leaderboard loads with five forward-return column headers
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-01-result.png`
- Navigated to http://localhost:3835/themes at latest date (2026-06-15). Page rendered with heading "Themes". Table header row contains: #, Theme, Theme Score, 1m, 3m, Breadth, 1D, 5D, 10D, 20D, 60D, Trend. All five forward-return columns (1D/5D/10D/20D/60D) present and showing "NA" (correct for latest date). No JS error banner.

---

### UT-02 — Sectors leaderboard loads with five forward-return column headers
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-02-result.png`
- Navigated to http://localhost:3835/sectors. Page rendered with 31 sector rows. Table header contains: #, Ticker, Kind, Sector Score, RS vs SPY, Dist. 52w high, 1D, 5D, 10D, 20D, 60D, Trend. All five forward-return column headers present. No error.

---

### UT-03 — Research page loads with RSP filter dropdowns visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-03-result.png`
- Navigated to http://localhost:3835/research. Scrolled to RSP section. Found 9 select elements total; three RSP-specific selects confirmed: value="\_\_all\_\_" with text "All regimes", value="\_\_all\_\_" with text "All setups", value="\_\_all\_\_" with text "All patterns". RSP table loaded with 99 rows (Pooled view). No error banner.

---

### UT-04 — Themes forward-return columns display numeric values at historical as-of date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-04-result.png`
- Navigated to http://localhost:3835/themes?asof=2025-01-15. All 11 themes show numeric values across all five columns (e.g. Megacap Leaders: 1d=-0.40%, 5d=+2.96%, 10d=+2.62%, 20d=+6.10%, 60d=-9.45%). Colour grading confirmed via computed styles: positive values have child element colour rgb(52,211,153) (green), negative values rgb(248,113,113) (red).

---

### UT-05 — Sectors forward-return columns display numeric values at historical as-of date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-05-result.png`
- Navigated to http://localhost:3835/sectors?asof=2025-01-15. Sector ETFs (XLF, XLE, XLC, XLK, etc.) show numeric values. Industry ETFs without stored bars (XAR, SKYY, HACK, SMH, etc.) show NA in muted grey rgb(139,152,169). Example XLF: 1d=+0.67% (green), 5d=+2.47% (green), 10d=+4.63% (green), 20d=+4.49% (green), 60d=-5.34% (red).

---

### UT-06 — Themes leaderboard can be sorted by the 5d forward-return column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-06-sorted-asc.png`
- At 2025-01-15: Default order: Megacap Leaders, Nuclear Uranium, Ai Data Centre... First 5d click: descending (Crypto +15.25% → Glp1 -2.52%). Second 5d click: ascending (Glp1 -2.52% → Crypto +15.25%). All rows have numeric 5d values at this date; no NA rows to check sinking. No page reload between sorts. Theme names and other column values remained intact.

---

### UT-07 — Sectors leaderboard can be sorted by the 20d forward-return column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-07-sorted-asc-na-bottom.png`
- At 2025-01-15: First 20d click: descending (XLC +7.80%→XLE -3.09%), 20 NA rows at bottom. Second 20d click: ascending (XLE -3.09%→XLC +7.80%), 20 NA rows still at bottom. Verified numericAfterNaCount=0 in both directions. No network request triggered.

---

### UT-08 — Research RSP section defaults to Pooled view on page load
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-08-rsp-pooled-default.png`
- Fresh navigation to http://localhost:3835/research. Toggle button audit (4 buttons): [0] Episodes aria-pressed=true (Event Study); [1] Pooled aria-pressed=false (Event Study); [2] Episodes aria-pressed=false (RSP); [3] Pooled aria-pressed=true (RSP). RSP defaults to Pooled; Event Study unaffected (Episodes default).

---

### UT-09 — Research RSP Regime filter narrows the table to matching rows
**Verdict:** PASS
**Evidence:** none
- Set Regime="Risk-on" via native-setter + bubbling change event. Interactive links dropped from 157 to 76. All 18 data rows in RSP table (table index 6) showed regime="Risk-on" — no rows from other regimes visible. Client-side filter; no page reload.

---

### UT-10 — Research RSP Regime + Pattern filters compose correctly
**Verdict:** PASS
**Evidence:** none
- With Regime=Risk-on (18 rows), added Pattern=vcp: RSP table reduced to 4 rows, all showing Risk-on+vcp combinations. Row count 18 → 4 confirms AND composition. Reset both to "All": interactive links jumped back to 162 (all rows restored).

---

### UT-11 — Research RSP numeric sort pushes NA rows to bottom (ascending)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-11-12-rsp-sort-na-bottom.png`
- Clicked "Mean↕" sort button twice to reach ascending. Result: rows 0-64 are numeric (smallest: -2.28% Choppy first), rows 65-98 are all NA. firstNaIdx=65; numericAfterNaCount=0. No page reload.

---

### UT-12 — Research RSP numeric sort keeps NA rows at the bottom (descending)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-11-12-rsp-sort-na-bottom.png`
- Clicked "Mean↕" once more for descending. Result: rows 0-64 numeric (largest: +8.71% first), rows 65-98 all NA. firstNaIdx=65; numericAfterNaCount=0. NA rows did not float to the top.

---

### UT-13 — Research RSP N= chip for standard pattern row opens samples without error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-13-samples-named-pattern.png`
- Row: Narrow leadership / Extended / flat base breakout, N=33. Navigated to /research/samples?kind=regime-setup-pattern&horizon=20&regime=Narrow+leadership&setup=Extended&pattern=flat_base_breakout&view=pooled. Page heading "Research Samples — observation drill-down" loaded; table with 33 data rows (exact match to N=33); no error.

---

### UT-14 — Research RSP N= chip for "none" pattern row opens samples without error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-14-samples-none-pattern.png`
- Row: Defensive / Extended / — (none), N=484. URL contains pattern=none. Page loaded with heading "Research Samples — observation drill-down"; table with 484 data rows (exact match to N=484); slice shows "— (no pattern)"; no 4xx/5xx error.

---

### UT-15 — Forward-return cells show "NA" not "0%" at the latest as-of date
**Verdict:** PASS
**Evidence:** none
- At http://localhost:3835/themes (latest date 2026-06-15): All 11 themes show NA in all 5 forward-return columns (1D/5D/10D/20D/60D). zeroIn60d=0 (no "0%" values), naIn60d=11 (all show explicit NA). No blank cells.

---

### UT-16 — Research RSP empty-after-filter state shows an informative message
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-16-rsp-empty-state.png`
- Applied Regime=Risk-off + Setup=Actionable (no matching combinations in stored data). RSP table element absent from DOM (totalTables dropped from 7 to 6). Page text shows: "No combinations match these filters — No (regime, setup, pattern) combination matches the current filter selection. Reset a filter to 'All' to widen the view — nothing is fabricated..." Filter dropdowns remained visible and operable.

---

### UT-17 — Themes existing columns still work after forward-return additions
**Verdict:** PASS
**Evidence:** none
- Navigated to http://localhost:3835/themes. Headers: #, Theme, Theme Score, 1m, 3m, Breadth, 1d, 5d, 10d, 20d, 60d, Trend — original columns present alongside new fwd-return columns. existingColsPopulated=true for first 3 rows. Theme rows have onclick handler, role=button, cursor=pointer — row expansion still works.

---

### UT-18 — Sectors existing columns still work after forward-return additions
**Verdict:** PASS
**Evidence:** none
- Navigated to http://localhost:3835/sectors. Headers: #, Ticker, Kind, Sector Score, RS vs SPY, Dist. 52w high, 1d, 5d, 10d, 20d, 60d, Trend. existingColsOk=true. rowCount=31 (all rows present, none dropped). No duplicate or displaced columns.

---

### UT-19 — Research Event Study / Cluster sections still default to Episodes
**Verdict:** PASS
**Evidence:** none
- Fresh navigation to http://localhost:3835/research. Toggle state confirmed: Event Study Episodes aria-pressed=true, Event Study Pooled aria-pressed=false. RSP Pooled aria-pressed=true (unchanged). The RSP Pooled default change did not affect the Event Study section's Episodes default.

---

### UT-20 — Themes/Sectors forward-return sort resets to default order after navigation
**Verdict:** PASS
**Evidence:** none
- At 2025-01-15, clicked 5d sort (ascending result: Homebuilders first at +1.00%). Navigated to /sectors then back to /themes?asof=2025-01-15. Row order returned to default score-ranked order: Megacap Leaders first (+2.96%), Nuclear Uranium second (+14.18%). Sort state did not persist. Forward-return columns still visible after navigation cycle.

---

### UT-21 — Themes forward-return value matches Backtest value for same date + horizon
**Verdict:** PASS
**Evidence:** none
- /themes at 2025-01-15: Megacap Leaders 5d = +2.96%. /backtest at 2025-01-15 with horizon switched to 5d: Top Themes section shows "FWD 5D — Megacap Leaders: +2.96%". Values match exactly. Nuclear Uranium: /themes=+14.18%, /backtest=+14.18%. Ai Data Centre: /themes=+8.09%, /backtest=+8.09%.

---

### UT-22 — New forward-return columns are discoverable without instructions
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-22-themes-columns-discoverable.png`
- Five sort buttons (1d/5d/10d/20d/60d): cursor=pointer (visual clickability affordance); aria-label="Sort by Xd"; class includes transition-colors + hover pseudo-class (visual hover feedback); table width 1646px vs viewport 1920px (no horizontal scroll required; all headers visible without zooming).

---

### UT-23 — RSP filter dropdowns are discoverable in the section controls row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/UT-23-rsp-filters-discoverable.png`
- Regime dropdown: top≈3014px, left=434px. Setup dropdown: top≈3014px, left=622px. Pattern dropdown: top≈3014px, left=810px. Pooled toggle: top≈3015px, left=349px. All four controls are in the same horizontal row. Each select's grandparent container shows a clear text label (REGIME / SETUP / PATTERN). Default values "All regimes" / "All setups" / "All patterns" visible without user interaction.

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
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-evidence/`
- **Historical test date used:** 2025-01-15 (sufficient post-date bars for all 5 fwd-return horizons)
