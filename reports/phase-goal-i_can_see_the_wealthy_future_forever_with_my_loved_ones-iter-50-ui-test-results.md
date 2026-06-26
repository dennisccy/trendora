# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50
**Date:** 2026-06-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 15/18 tests passed (2 skipped, 1 failed)

P1 failures: 1 (UT-03). All other P1 tests pass. All smoke and regression tests pass.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab page loads with all-factors table visible | smoke | P1 | Page renders with 3+ row table, Factor Lab heading, no dropdown | 11-row table loaded, heading "Research — Factor Lab", no dropdown | PASS | `UT-01-02-table-loaded.png` |
| UT-02 | All-factors table shows one row per catalog factor with all required columns | happy-path | P1 | 3+ rows, Factor/Family/Rank-IC/N/Risk-adjusted columns, no single-factor text | 11 rows, all 5 column headers present, no single-factor body text | PASS | `UT-01-02-table-loaded.png` |
| UT-03 | Clicking column header sorts table ascending | happy-path | P1 | Rows reorder with highest Rank-IC (+0.03) at top after first click | Rows reordered to ASCENDING (lowest -0.02 at top, highest +0.03 at bottom) | FAIL | `UT-03-after-first-click-ascending.png` |
| UT-04 | Second click on column header reverses sort, NA rows stay at bottom | happy-path | P1 | Row at position 1 moves to bottom; row at bottom moves to position 1 | Second click reversed to descending; lowest (-0.02) moved to bottom, highest (+0.03) moved to top | PASS | `UT-04-after-second-click-descending.png` |
| UT-05 | Clicking factor row expands decile panel (D1–D10) | happy-path | P1 | Full-width panel with D1–D10 decile rows, mean return, risk-adjusted, N | Panel expanded below row with D1–D10 rows showing fwd return, n=, risk-adjusted | PASS | `UT-05-decile-expanded.png` |
| UT-06 | Clicking expanded factor row collapses decile panel | happy-path | P1 | Panel disappears; row returns to compact height | D1–D10 panel gone; "Decile sort" text absent from page | PASS | `UT-06-decile-collapsed.png` |
| UT-07 | Decile N= chip opens Research Samples in new tab with matching count | happy-path | P1 | New tab opens with matching total count; URL has kind=factor, slice=decile, decile=1 | Research Samples tab opened; "Total observations: 11761" matched N=11761 chip; URL had kind=factor&factor=high_proximity&slice=decile&decile=1 | PASS | `UT-07-samples-page.png` |
| UT-08 | Factor selector dropdown is absent | regression | P1 | No select/combobox element for single-factor selection | 0 select elements, 0 combobox elements found | PASS | `UT-08-no-selects.png` |
| UT-09 | Single-factor body and RankIC card are absent | regression | P1 | No standalone RankIC card; no single-factor decile table at page level | No "Select a factor" text; no RankIC card visible; no single-factor decile table at page level | PASS | `UT-13-18-caveats-subtitle.png` |
| UT-10 | Per-regime effectiveness table is absent | regression | P1 | No Regime/Bull/Bear/by_regime text on page | No regime-related text found anywhere on page | PASS | `UT-13-18-caveats-subtitle.png` |
| UT-11 | Horizon selector updates all rows simultaneously | regression | P1 | Rank-IC and N values change in all rows after horizon change | At 20d: N=117614, Risk-adj=+0.45; at 60d: N=112868, Risk-adj=+0.82; all rows updated simultaneously | PASS | `UT-11-60d-horizon.png` |
| UT-12 | As-of mode toggle changes N values globally | regression | P1 | N values decrease when As-of date mode with historical date is used | All-history N=122964; As-of-date 2023-06-01 N=40674 (66% reduction); single global date switcher (top-bar) | PASS | `UT-12-asof-reduced-n.png` |
| UT-13 | ResearchCaveat warnings still visible | regression | P2 | At least one research caveat warning visible without extra interaction | "Survivorship bias · universe-relative · descriptive" header + full caveat text visible | PASS | `UT-13-18-caveats-subtitle.png` |
| UT-14 | Loading skeleton / WarmingState shows before data arrives | error | P2 | Skeleton or spinner shown before data arrives; no blank screen | During horizon changes, interactive button count dropped from 15 to 5 (loading state), confirming skeleton/spinner was shown; no screenshot captured of this transient state | SKIP | none |
| UT-15 | Zero-N and low-sample rows show NA and sort to bottom | validation | P2 | At least one N=0 or low-sample row shows NA in Rank-IC column | Precondition not met: all 11 factors have N > 100,000 in All-history mode; no zero-N or low-sample rows exist in current dataset | SKIP | none |
| UT-16 | ResearchError panel shows on backend failure | error | P2 | Error panel shown; no fabricated data; message indicates unavailability | At test start (backend not running): page showed "Backend unavailable — The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values." | PASS | `UT-01-initial.png` |
| UT-17 | Factor Lab reachable from Research navigation in 2 clicks | ux | P2 | Factor Lab reached in ≤2 clicks; clearly labeled; navigates to /research/factor-lab | Click 1: "Research" nav link → /research; Click 2: "Factor Lab" card → /research/factor-lab with all-factors table loaded | PASS | `UT-17-factor-lab-navigation.png` |
| UT-18 | Page subtitle reflects multi-factor scope | ux | P3 | Subtitle reads "Which factors actually sort future returns" | Subtitle reads "Which factors actually sort future returns? Every catalog factor's rank-IC + a downside risk-adjusted figure at the chosen horizon…" | PASS | `UT-13-18-caveats-subtitle.png` |

---

## Passed Tests

### UT-01 — Factor Lab page loads with all-factors table visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-01-02-table-loaded.png`
- Navigated to http://localhost:3255/research/factor-lab; page rendered with heading "Research — Factor Lab"
- 11 factor rows visible in table; columns: FACTOR, FAMILY, RANK-IC, N, RISK-ADJUSTED (DOWNSIDE)
- No dropdown or select element for single-factor selection found (0 selects, 0 comboboxes)
- "Factors: 11 | Horizon: 20d" indicator confirmed table populated

---

### UT-02 — All-factors table shows one row per catalog factor with all required columns
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-01-02-table-loaded.png`
- 11 rows total (factors: Proximity to 52-week high, Risk score, Moving-average stack, Relative strength vs SPY, Leadership score, Up/down volume, Downside volatility, Historical volatility, Volatility contraction, ATR %, Entry Quality score)
- All 5 column headers confirmed: Factor, Family, Rank-IC, N, Risk-adjusted (downside)
- Each row shows non-empty factor label, family label, numeric Rank-IC, N > 0, numeric risk-adjusted value
- No "Select a factor to view…" or single-factor body text visible

---

### UT-04 — Second click on column header reverses sort, NA rows stay at bottom
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-04-after-second-click-descending.png`
- After 1st click (ascending): Entry Quality score (-0.02) at row 1; Proximity to 52-week high (+0.03) at row 11
- After 2nd click (descending): Proximity to 52-week high (+0.03) at row 1; Entry Quality score (-0.02) at row 11
- Sort reversed correctly on second click
- No NA rows exist in current dataset (all factors have N > 0)

---

### UT-05 — Clicking factor row expands decile panel (D1–D10)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-05-decile-expanded.png`
- Clicked "Proximity to 52-week high" row; full-width decile panel appeared below it
- Panel showed 10 decile rows: D1 (n=11761, mean fwd return +2.59%, risk-adj +0.22) through D10 (n=11762, mean fwd return +2.74%, risk-adj +0.45)
- All other factor rows remained visible above and below the expanded panel
- Interactive element count increased from 15 buttons/10 links to 18 buttons/30 links (confirming panel rendered)

---

### UT-06 — Clicking expanded factor row collapses decile panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-06-decile-collapsed.png`
- Clicked the expanded "Proximity to 52-week high" row a second time
- "D1", "Decile sort" text absent from page after click
- Interactive count returned to 15 buttons/10 links (confirming panel removed)
- Table appearance identical to pre-expansion state

---

### UT-07 — Decile N= chip opens Research Samples in new tab with matching count
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-07-samples-page.png`
- D1 chip showed "n=11761" with href: `/research/samples?kind=factor&horizon=20&factor=high_proximity&slice=decile&decile=1&asof=2026-05-28`
- Opened that URL in new tab; Research Samples page loaded
- Page showed: "Cohort: Factor Lab — Proximity to 52-week high", "Slice: Decile D1 of 10", "Total observations: 11761"
- Count matched exactly (11761 = 11761); URL contained all required params: kind=factor, slice=decile, decile=1

---

### UT-08 — Factor selector dropdown is absent
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-08-no-selects.png`
- `document.querySelectorAll('select').length` = 0
- `document.querySelectorAll('[role="combobox"]').length` = 0
- Scanned all buttons: none labeled "Factor", "Select factor", "Choose a factor" or similar single-factor selection

---

### UT-09 — Single-factor body and RankIC card are absent
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-13-18-caveats-subtitle.png`
- No "Select a factor" or "Choose a factor" text found on page
- No standalone RankIC card visible at page body level
- Decile table only appears inside expanded row panels (not at page level)

---

### UT-10 — Per-regime effectiveness table is absent
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-13-18-caveats-subtitle.png`
- Searched page text for: "Regime", "Bull", "Bear", "by_regime" — none found
- Scrolled through full page; no market-regime table or regime-labelled rows visible

---

### UT-11 — Horizon selector updates all rows simultaneously
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-11-60d-horizon.png`
- At 20d horizon: Proximity to 52-week high row showed N=117614, Risk-adj=+0.45
- Clicked "60d" horizon button; table reloaded
- At 60d horizon: same row showed N=112868, Risk-adj=+0.82 — both values changed
- All 11 rows updated simultaneously; URL remained `/research/factor-lab` (no page reload)

---

### UT-12 — As-of mode toggle changes N values globally
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-12-asof-reduced-n.png`
- "All history" mode at 20d: Entry Quality score N=122964
- Clicked "As of date" toggle (in ANALYSIS MODE control bar); page showed "Point-in-time: pooling only snapshots dated ≤ DATE"
- With global as-of date set to 2023-06-01: same factor showed N=40674 (66% decrease)
- Single global date switcher in top bar (not a separate date input in controls); no two independent date selectors
- Table structure unchanged; all 11 rows updated together

---

### UT-13 — ResearchCaveat warnings still visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-13-18-caveats-subtitle.png`
- "Survivorship bias · universe-relative · descriptive" header visible without any interaction
- Full caveat: "Walk-forward evidence is measured on the current-membership universe and therefore carries survivorship bias: names that were later delisted or dropped from the universe are absent, so realized forward returns may be overstated."
- Second caveat: "Descriptive evidence, not a predictive model: these are realized forward returns sorted by a stored factor…"
- Both caveats visible directly on page, not behind any collapsed section

---

### UT-16 — ResearchError panel shows on backend failure
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-01-initial.png`
- At test start, backend was not running; navigated to http://localhost:3255/research/factor-lab
- Page showed: "Backend unavailable — The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- Controls bar (horizon selector, analysis mode) remained visible
- No fabricated factor rows with placeholder values were shown

---

### UT-17 — Factor Lab reachable from Research navigation in 2 clicks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-17-factor-lab-navigation.png`
- Start: http://localhost:3255 (Dashboard)
- Click 1: "Research" sidebar nav link → navigated to http://localhost:3255/research
- On /research page: "Factor Lab" card link found with href=/research/factor-lab
- Click 2: "Factor Lab" card → navigated to http://localhost:3255/research/factor-lab, heading "Research — Factor Lab", 11-row table loaded

---

### UT-18 — Page subtitle reflects multi-factor scope
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-13-18-caveats-subtitle.png`
- Subtitle text: "Which factors actually sort future returns? Every catalog factor's rank-IC + a downside risk-adjusted figure at the chosen horizon — sortable, and expandable in place to its full decile sort."
- Starts with "Which factors actually sort future returns?" — matches expected phrasing
- Does NOT reference a single factor or say "Select a factor to begin"

---

## Failed Tests

### UT-03 — Clicking column header sorts the table by that column ascending
**Verdict:** FAIL
**Failure:** After clicking the "Rank-IC" column header once, the table sorted in ASCENDING order (lowest Rank-IC -0.02 at position 1, highest Rank-IC +0.03 at position 11). The test expected the HIGHEST Rank-IC value (+0.03) to be at the top of the list after the first click (descending order).
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/UT-03-after-first-click-ascending.png`

**Steps taken:**
1. Navigated to http://localhost:3255/research/factor-lab; table loaded with default order: Proximity to 52-week high (+0.03) at row 1, descending by Rank-IC
2. Clicked "Rank-IC" column header button via `document.querySelectorAll('button').find(b => b.textContent.trim() === 'Rank-IC')?.click()`
3. Waited for table to reorder; read new row order

**Expected:** After first click, rows sorted descending — highest Rank-IC (+0.03) at position 1, "NA" rows at bottom

**Actual:** After first click, rows sorted ascending — lowest Rank-IC (-0.02) at position 1, highest Rank-IC (+0.03) at position 11.
- Row 1: "Entry Quality score — Score — -0.02"
- Row 11: "Proximity to 52-week high — Trend — +0.03"

**Note:** UT-04's precondition ("sorted by Rank-IC ascending from UT-03") matches this actual ascending behavior, indicating an internal inconsistency in the test plan's expected result for UT-03. The sort toggle mechanism itself works correctly (ascending → descending on second click). The discrepancy is likely that the default table display is already sorted descending by Rank-IC, so the first click toggles to ascending rather than to descending. This may reflect a test expectation error rather than a product defect.

---

## Skipped Tests

### UT-14 — Loading skeleton / WarmingState shows before data arrives
**Verdict:** SKIPPED
**Reason:** Backend cache was already warm by the time tests ran. The loading skeleton was not directly captured in a screenshot. Circumstantial evidence (button count dropping from 15 to 5 during horizon changes, then returning to 15 when data arrived) strongly suggests a loading skeleton/spinner is shown during data fetching. Could not isolate a cold-start scenario with a screenshot.

---

### UT-15 — Zero-N and low-sample factor rows display "NA" in value columns
**Verdict:** SKIPPED
**Reason:** Precondition not met. All 11 catalog factors have N > 100,000 in All-history mode (minimum observed: N=117,614 for Proximity to 52-week high at 20d). No zero-N or low-sample rows exist in the current dataset. The "NA" rendering path could not be exercised.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (health at /api/health)
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-26
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50-evidence/`
