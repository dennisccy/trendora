# Goal Mode Iter-10 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10
**Date:** 2026-06-13
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-64 | Samples table sort + ticker filter | happy-path | P1 | Click-sortable columns, ticker filter narrows rows with honest view count, cohort total unchanged, empty-state on no-match, filter+sort compose | Sort works (asc/desc toggle, 3rd click restores served order, exactly 1 indicator); filter narrows to AAPL 28 rows, "Showing 28 of 2376 observations", total stays 2376; no-match shows honest empty state; filter+sort compose (NVDA 19 rows with Leadership sort active) | PASS | UT-J-64-filter-sort-compose.png |
| UT-J-65 | N= chips open drill-down in new tab | happy-path | P1 | All N= chips have target=_blank + rel=noopener; hrefs carry cohort params + ?asof when historical; Back to Research stays same-window | 51/51 chips have target="_blank" + rel="noopener noreferrer"; hrefs at latest are date-free; with ?asof=2026-06-05 all 51 hrefs carry asof; Back to Research has no target=_blank | PASS | UT-J-65-research-historical-chips.png |
| UT-J-25 | Factor Lab renders with N= chips | regression | P1 | Factor Lab with decile rows and rank-IC render | Factor Lab heading, rank-IC, N= chips all present | PASS | UT-J-25-J-26-J-29-research.png |
| UT-J-26 | Combination cohort renders | regression | P1 | Multi-factor combination cohort with composite rank-blend renders | Combination, Combined, Composite all present on research page | PASS | UT-J-25-J-26-J-29-research.png |
| UT-J-29 | Setup & Pattern Lab renders | regression | P1 | Setup & Pattern Lab with MAE/MFE renders | Setup & Pattern Lab, Actionable, MAE, MFE all present | PASS | UT-J-25-J-26-J-29-research.png |
| UT-J-32 | Research as-of scope mode toggle | regression | P1 | As of date toggle changes scope to asof on N= chip hrefs | After toggling As of date, all 51 sample hrefs carry scope=asof | PASS | UT-J-32-asof-mode.png |
| UT-J-43 | Historical as-of URL serialization | regression | P1 | With ?asof=D selected, URL carries param, historical badge shows | URL carries ?asof=2026-06-05, "Viewing as-of 2026-06-05 (historical)" badge shown | PASS | UT-J-43-J-50-stocks-historical.png |
| UT-J-50 | In-app links embed ?asof while historical | regression | P1 | All nav links carry ?asof=D in their href when historical | All sidebar nav links carry ?asof=2026-06-05; 122 ticker links carry /stocks/[TICKER]?asof=2026-06-05 | PASS | UT-J-43-J-50-stocks-historical.png |
| UT-J-51 | Drill-down total equals published N | regression | P1 | Samples API total == published N on chip, same instant | API returns total=2376; research page D1 chip shows N=2376; count coherent (total==rows_count) | PASS | UT-J-51-J-52-samples-with-ticker-links.png |
| UT-J-52 | Row ticker opens dated stock detail in new tab | regression | P1 | Samples row tickers have target=_blank, rel=noopener, href carries row's snapshot date | 28/28 ticker links have target="_blank" + rel="noopener noreferrer"; hrefs are /stocks/AAPL?asof=2021-01-04 (row's own date, not page date) | PASS | UT-J-51-J-52-samples-with-ticker-links.png |

---

## Passed Tests

### UT-J-64 — Samples table sort + ticker filter (J-64)

**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-64-samples-loaded.png`
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-64-sort-forward-return-asc.png`
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-64-ticker-filter-aapl.png`
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-64-filter-empty-state.png`
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-64-filter-sort-compose.png`

**Cohort used:** Factor Lab — Leadership Score Decile D1 (2376 rows, multiple distinct tickers, spread of forward return values).

**Steps verified:**

1. **Samples page loads** — `/research/samples?kind=factor&horizon=20&factor=leadership_score&slice=decile&decile=1` renders with filter input (`data-testid="samples-ticker-filter"`), samples table (`data-testid="samples-table"`), cohort total (`data-testid="samples-total"` = 2376), Ticker / Snapshot date / Leadership Score / Forward return (20d) columns with sort buttons.

2. **Sort Forward return → asc** — Clicked `button[aria-label*="Sort by Forward return"]`; `data-testid="sort-indicator"` count = 1; `aria-sort="ascending"` on Forward return column (4th). Exactly one indicator visible.

3. **Sort Forward return → desc (toggle)** — Clicked again; `data-testid="sort-indicator"` count = 1; `aria-sort="descending"`. Direction toggled.

4. **Sort clears on 3rd click** — Clicked third time; `sort-indicator` count = 0; all `aria-sort="none"`. Served order restored.

5. **Sort Ticker** — 1 indicator, `aria-sort="ascending"` on first column.

6. **Sort Snapshot date** — 1 indicator, `aria-sort="ascending"` on second column.

7. **Sort qualifying-value column (Leadership Score)** — 1 indicator, `aria-sort="ascending"` on third column.

8. **Ticker filter narrows rows** — Typed "AAPL"; rows narrowed to 28 AAPL-only rows; `data-testid="samples-view-count"` rendered "Showing 28 of 2376 observations"; `data-testid="samples-total"` still reads 2376 (cohort total untouched).

9. **All-filtered-out honest empty state** — Typed "ZZZNOMATCH"; view count showed "Showing 0 of 2376 observations"; table hidden; EmptyState rendered "No observations match this filter — No ticker in this cohort matches 'AAPLZZZNOMATCH'. This is a view filter over the 2376 served observations — the cohort itself is unchanged." No fabricated rows.

10. **Filter + sort compose** — With Leadership sort active (1 indicator), typed "NVDA"; rows narrowed to 19 NVDA rows; sort indicator still active; view count showed "Showing 19 of 2376 observations"; total 2376 unchanged.

11. **Back to Research is same-window** — `href="/research"` with no `target="_blank"`.

12. **No nested interactive elements** — `SortHeader` implementation confirmed: sort `<button>` and `TermInfo` info trigger are siblings inside `<th>`, never nested. No dev-overlay error badges found.

---

### UT-J-65 — N= chips open drill-down in new tab (J-65)

**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-65-research-initial.png`
- `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-65-research-historical-chips.png`

**Steps verified:**

1. **All 51 N= chips on /research have target="_blank"** — `data-testid="sample-link"` anchors: 51/51 have `target="_blank"`, 51/51 have `rel="noopener noreferrer"`. Confirmed from live hydrated DOM (078-navigate.html).

2. **Hrefs at latest are date-free** — When at latest, all 51 hrefs carry only cohort params (e.g. `/research/samples?kind=factor&horizon=20&factor=leadership_score&slice=decile&decile=1`); no `?asof=` present (0/51).

3. **Hrefs with historical asof carry ?asof** — Navigated to `/research?asof=2026-06-05`; all 51 hrefs gained `&asof=2026-06-05` suffix. Example: `/research/samples?kind=factor&horizon=20&factor=leadership_score&slice=decile&decile=1&asof=2026-06-05`. Count: 51/51.

4. **Back to Research stays same-window** — `<a href="/research">Back to Research</a>` has no `target` attribute — confirmed same-window behavior.

5. **Href construction byte-unchanged (J-51/J-50)** — Two-step `buildSamplesHref(cohort, scope)` + `useAsOfHref` serialization confirmed in source (`sample-link.tsx` lines 44–45). Cohort params + scope + `?asof` all carry as before.

---

### UT-J-25 — Factor Lab renders with N= chips

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-25-J-26-J-29-research.png`
- Factor Lab heading present, decile table with N= chips renders, Rank-IC present.

---

### UT-J-26 — Combination cohort renders

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-25-J-26-J-29-research.png`
- Multi-factor combination cohort with composite rank-blend present; "Combined" and "Strict overlap" rows render.

---

### UT-J-29 — Setup & Pattern Lab renders

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-25-J-26-J-29-research.png`
- Setup & Pattern Lab section present; Actionable setup selectable; MAE/MFE columns render.

---

### UT-J-32 — Research as-of scope mode toggle

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-32-asof-mode.png`
- Clicked "As of date" button; all 51 sample link hrefs gained `scope=asof` parameter confirming the mode change propagates to chips. "All history" toggle also present. No second date state introduced.

---

### UT-J-43 — Historical as-of URL serialization

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-43-J-50-stocks-historical.png`
- Loaded `/stocks?asof=2026-06-05`; URL carries `?asof=2026-06-05`; historical badge "Viewing as-of 2026-06-05 (historical)" renders; the global as-of switcher reflects the date; single date control confirmed.

---

### UT-J-50 — In-app links embed ?asof while historical

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-43-J-50-stocks-historical.png`
- All sidebar nav links carry `?asof=2026-06-05` in their hrefs (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager). 122 ticker links carry `/stocks/[TICKER]?asof=2026-06-05`.

---

### UT-J-51 — Drill-down total equals published N (same-instant)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-51-J-52-samples-with-ticker-links.png`
- Research page D1 chip aria-label: "See the 2376 observations in decile D1". Backend API `GET /api/research/samples?kind=factor&horizon=20&factor=leadership_score&slice=decile&decile=1` returns `total=2376`, `len(rows)=2376`. Count coherent: `total == len(rows)` is True. Published N == API total in same session.

---

### UT-J-52 — Row ticker opens dated stock detail in new tab

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/UT-J-51-J-52-samples-with-ticker-links.png`
- 28/28 visible row ticker links (when filtered to AAPL) have `target="_blank"`, `rel="noopener noreferrer"`, and hrefs `/stocks/AAPL?asof=2021-01-04` (carrying the row's own snapshot date, not the page's global date). Confirmed via `data-testid="samples-ticker-link"`.

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
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-13
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-10-evidence/`

---

## Notes

**Browser context:** A second Next.js app (Tapeology, port 3650) was running in the same browser. The Chrome MCP tool defaulted to the Tapeology tab after `eval` actions. All Trendora tests were conducted via `tab_index=2` (the Trendora tab) and by reading the session-captured HTML files. The captured DOM at 078-navigate.html (full hydrated Trendora /research page) and the live DOM extracts from tab_index=2 confirm all J-64 and J-65 features.

**J-64 dormant-overflow lesson applied:** Decile D1 of Leadership Score was chosen as the test cohort. It has 2376 rows across many distinct tickers (AAPL, NVDA, ABNB, ADBE, confirmed in page text) and a spread of forward return values. All sort and filter legs were confirmed on a cohort with sufficient data.

**J-64 iter-7 N-drift lesson applied:** Count coherence (drill-down total == published N) was checked same-instant: API call during the same browser session returned total=2376 matching the chip's aria-label "See the 2376 observations in decile D1".

**J-65 new-tab contract verified:** 51/51 N= chips on /research carry `target="_blank"` + `rel="noopener noreferrer"` with cohort params + scope + ?asof serialized correctly in both latest (date-free) and historical (date-stamped) modes.
