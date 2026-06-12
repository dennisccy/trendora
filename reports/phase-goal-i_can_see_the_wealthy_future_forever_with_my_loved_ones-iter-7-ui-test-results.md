# Goal Iter 7 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7
**Date:** 2026-06-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-51 | Every research sample count is a link to its exact samples | happy-path | P1 | All three labs have N= links to /research/samples; samples page shows total=N, survivorship label, TermInfo column headers, deep-link safe, N=0 honest empty state | 51 unique /research/samples hrefs across Factor Lab (decile/regime/total/rank-IC), Combination Lab (baseline/single/composite/strict_overlap), Event Study (pooled/regime/sector); D1 page shows Total observations: 2083 == n on chip; column headers have TermInfo info-button siblings; Risk-off N=0 shows "This cohort has zero observations — an honest empty set, not a fabricated row"; reload of same URL returns same cohort; as-of mode links carry scope=asof&asof=D | PASS | UT-J-51-initial.png, UT-J-51-samples-page.png, UT-J-51-empty-state.png, UT-J-51-samples-d10.png |
| UT-J-52 | From a sample row to the dated stock detail | happy-path | P1 | Row ticker opens /stocks/[ticker]?asof=<row snapshot date> in new tab with target=_blank + rel=noopener; originating tab untouched | Ticker links have target="_blank" rel="noopener noreferrer" data-testid="samples-ticker-link" href="/stocks/AAPL?asof=2021-01-04"; new tab at /stocks/AAPL?asof=2021-01-04 shows "Viewing as-of 2021-01-04 (historical)"; all nav links carry ?asof=2021-01-04; originating samples tab (tab index 1) unchanged at research/samples URL | PASS | UT-J-52-stock-detail-new-tab.png |
| UT-J-25 | Factor Lab — decile sort and rank-IC | regression | P1 | Decile table with mean forward return, risk-adjusted column, rank-IC, all with n links | Research page shows Factor Lab with D1-D10 decile table (+7.66% to +9.32%), risk-adjusted column, Rank-IC +0.04, n=20832 total; all decile rows carry n= links to /research/samples?kind=factor&... | PASS | UT-J-25-factor-lab.png |
| UT-J-26 | Factor Lab — multi-factor composite cohort | regression | P1 | Combination cohort shows Baseline/Combined/Strict overlap with n links | Combination Lab shows Baseline n=16687 (+3.79%), Combined composite n=3338 (+2.44%), Strict overlap n=606 (+0.59%); all rows have /research/samples?kind=combination&... links | PASS | UT-J-26-combination-lab.png |
| UT-J-29 | Setup & Pattern research lab — event study | regression | P1 | Event study with per-horizon distribution, MAE/MFE, by-regime, by-sector; all with n links | Event Study shows Actionable pooled: n=70 (1d), n=66 (5d), n=64 (10d), n=54 (20d), n=45 (60d) with mean/median/hit-rate/dispersion/expectancy/MAE/MFE/risk-adjusted columns; regime and sector slices shown; all n values are /research/samples?kind=event-study&... links | PASS | UT-J-25-factor-lab.png |
| UT-J-32 | Research point-in-time toggle (as-of vs all-history) | regression | P1 | All history / As of date toggle; in as-of mode scope=asof carried in links; point-in-time label shown | Both "All history" and "As of date" buttons present; clicking "As of date" changes chip links to carry scope=asof (confirmed: 24 scope=asof links appear when mode active with ?asof=2024-01-03 date); "As of date" mode shows "Point-in-time: pooling only snapshots dated ≤ 2024-01-03"; API confirmed as_of scoping reduces D1 to 115 obs at 2021-01-04 vs 2083 all-history | PASS | UT-J-32-asof-mode.png |
| UT-J-47 | Every term on every page is explained (glossary + tooltips) | regression | P1 | /methodology Glossary with categorized searchable entries; dense page headers have info-tooltip buttons reading same catalog | /methodology shows Glossary section with rank-IC, MAE, MFE, expectancy, hit-rate, dispersion, universe, walk-forward, survivorship, horizon, composite entries; Research page table headers have aria-label="Definition of rank-IC", "Definition of MAE", "Definition of MFE", "Definition of expectancy" etc; samples page column headers have TermInfo sibling buttons (not nested) | PASS | UT-J-25-factor-lab.png |
| UT-J-50 | The as-of date survives EVERY in-app navigation (href embedding) | regression | P1 | While historical D, every in-app link's href carries ?asof=D; at latest hrefs are clean | At ?asof=2025-01-09, after await_text("Viewing as-of 2025-01-09"), live DOM attr check: nav Research link href="/research?asof=2025-01-09"; leaderboard first ticker href="/stocks/NET?asof=2025-01-09"; note: pre-hydration SSR HTML shows bare hrefs — only live DOM attr() confirmed correct values | PASS | UT-J-50-historical-hrefs.png |
| UT-J-54 | Leaderboard ticker opens the stock detail in a new tab | regression | P1 | Ticker links target=_blank + rel=noopener; href carries ?asof=D at historical, clean at latest | Live DOM attr: table tbody tr:first-child a target="_blank", rel="noopener noreferrer", href="/stocks/NET?asof=2025-01-09" at historical; theme/sector sidebar links stay same-window | PASS | UT-J-54-ticker-new-tab.png |

---

## Passed Tests

### UT-J-51 — Every research sample count is a link to its exact samples
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-51-samples-page.png`, `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-51-empty-state.png`

- `/research` has 51 unique /research/samples hrefs across all three labs (Factor Lab decile/regime/total, Combination Lab all cohort types, Event Study pooled/regime/sector).
- Navigated to `/research/samples?kind=factor&horizon=20&factor=leadership_score&slice=decile&decile=1`: page heading "Research Samples — observation drill-down", cohort description "Factor Lab — Leadership score / Slice: Decile D1 of 10 / Horizon: 20d / Scope: All history", **Total observations: 2083** — matches chip n=2083 on the research page (count coherence).
- Survivorship-bias label visible: "Walk-forward evidence is measured on the current-membership universe and therefore carries survivorship bias".
- Table columns: TICKER, SNAPSHOT DATE (with TermInfo sibling ⓘ), LEADERSHIP SCORE (with TermInfo ⓘ), FORWARD RETURN (20D) (with TermInfo ⓘ). Info buttons are siblings of text, never nested (iter-5 lesson respected).
- Row data confirmed: AAPL 2021-01-04 0.00 +4.31%, ABNB 2021-01-04 0.00 +28.76% etc. — stored values, not recomputed.
- Deep-link safety confirmed: same URL reloads same cohort (2094 links in DOM = 2083 rows + nav).
- N=0 honest empty state: navigated to Risk-off regime event study slice (n=0 on research page) → "This cohort has zero observations — an honest empty set, not a fabricated row. The published N for this slice is also 0."
- As-of mode: with `?asof=2024-01-03` active and "As of date" mode toggled, chip links carry `scope=asof&asof=2024-01-03` (24 such links found); API confirmed scoping works (as_of=2021-01-04 → 115 obs, all-history → 2083).
- No dev overlay error badge on samples page.
- API count-coherence spot-checks: D10 total=2084 (matches chip), combination/composite total=3338, strict_overlap total=606, event-study Actionable 20d total=54 — all match published N values.

---

### UT-J-52 — From a sample row to the dated stock detail
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-52-stock-detail-new-tab.png`

- Ticker links in the samples table have `target="_blank"` and `rel="noopener noreferrer"` confirmed from HTML: `<a target="_blank" rel="noopener noreferrer" data-testid="samples-ticker-link" href="/stocks/AAPL?asof=2021-01-04">`.
- The href carries **that row's snapshot date** as `?asof=2021-01-04` (not the research page's global date).
- Opened `/stocks/AAPL?asof=2021-01-04` in new tab: "Viewing as-of 2021-01-04 (historical)" indicator shown; all nav links carry `?asof=2021-01-04`; page shows AAPL's stored 2021-01-04 snapshot ("Leadership is too weak for a setup — avoid").
- The originating samples tab (index 1) remained at `research/samples?kind=factor&...` URL — untouched.
- The new-tab opens independently with the row's date through the single global control (J-43 semantics preserved).

---

### UT-J-25 — Factor Lab — decile sort and rank-IC
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-25-factor-lab.png`

- Factor Lab renders D1-D10 decile table for Leadership score at 20d horizon with mean forward returns (+7.66% to +9.32%), risk-adjusted (downside) column, and Rank-IC +0.04 n=20832.
- All decile n values are hyperlinks to /research/samples — confirmed 20 unique factor-slice links.
- Survivorship-bias label present; NA threshold for low-n deciles documented.
- No regression from pre-iter-7 behavior.

---

### UT-J-26 — Factor Lab — multi-factor composite cohort
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-26-combination-lab.png`

- Combination Lab shows: Baseline (all names) n=16687 +3.79%, RS SPY 3m top Quintile n=3338 +9.03%, ATR% bottom Tertile n=5562 +1.18%, Combined (composite rank-blend) n=3338 +2.44%, Strict overlap (AND) n=606 +0.59%.
- All cohort rows carry /research/samples?kind=combination&... links.
- API confirmed composite total=3338, strict_overlap total=606 — matching displayed N.

---

### UT-J-29 — Setup & Pattern research lab — event study
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-25-factor-lab.png`

- Event Study shows per-horizon distribution for Actionable setup: 1d/5d/10d/20d/60d with mean, median, % positive, dispersion, expectancy, mean MAE, mean MFE, return/downside-dev, return/MAE.
- By-regime and by-sector slices shown; low-sample cells show NA + n honestly.
- All n values are links to /research/samples?kind=event-study&... links with slice=pooled/regime/sector params.
- API confirmed event-study Actionable 20d total=54 matches chip.

---

### UT-J-32 — Research point-in-time toggle (as-of vs all-history)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-32-asof-mode.png`

- Both "All history" and "As of date" buttons present on /research.
- In "As of date" mode with `?asof=2024-01-03`, chip links carry `scope=asof&asof=2024-01-03`; page shows "Point-in-time: pooling only snapshots dated ≤ 2024-01-03 (a walk-forward view)".
- API confirmed scoping: `as_of=2021-01-04` returns 115 observations vs 2083 all-history for D1.
- No second date state introduced — the global as-of switcher is the only date control (J-18 preserved).

---

### UT-J-47 — Every term on every page is explained
**Verdict:** PASS
**Evidence:** (confirmed via DOM inspection, not a separate screenshot)

- /methodology Glossary section contains categorized entries covering rank-IC, MAE, MFE, expectancy, hit-rate, dispersion, universe, walk-forward, survivorship, horizon, composite, forward return, decile, and many more.
- Research page table headers carry `aria-label="Definition of rank-IC"`, `"Definition of MAE"`, `"Definition of MFE"`, `"Definition of expectancy"`, `"Definition of hit-rate"`, `"Definition of dispersion"`, `"Definition of composite"`, `"Definition of horizon"` etc. — reading the same catalog.
- Samples page column headers carry TermInfo sibling buttons (not nested inside anchor or other interactive elements) — confirmed in HTML: `<span class="inline-flex items-center gap-1">Snapshot date<span class="relative inline-flex"><button ...>`.

---

### UT-J-50 — The as-of date survives EVERY in-app navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-50-historical-hrefs.png`

- At `stocks?asof=2025-01-09`, after React hydration confirmed via `await_text("Viewing as-of 2025-01-09")`:
  - `nav a[href*="research"]` attr href = `/research?asof=2025-01-09`
  - `table tbody tr:first-child a` attr href = `/stocks/NET?asof=2025-01-09`
- Note: pre-hydration SSR HTML shows bare hrefs (no `?asof`) — the `useAsOfHref` client hook sets them post-hydration. Live DOM `attr()` checks after `await_text` confirmed correct values.
- At latest date, hrefs are clean (no `?asof` param).

---

### UT-J-54 — Leaderboard ticker opens the stock detail in a new tab
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/UT-J-54-ticker-new-tab.png`

- Live DOM checks at `stocks?asof=2025-01-09` post-hydration:
  - `target` = `_blank`
  - `rel` = `noopener noreferrer`
  - `href` = `/stocks/NET?asof=2025-01-09`
- Theme/sector sidebar links remain same-window (no `target`).
- The new-tab behavior applies only to leaderboard tickers (and J-52 samples-row tickers), not to other nav links.

---

## Failed Tests

(none)

---

## Skipped Tests

(none)

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-12
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7-evidence/`
