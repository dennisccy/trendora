# Goal Mode — UI Test Results (Iter 51)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51
**Date:** 2026-06-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Daily dashboard at a glance | happy-path | P1 | Regime label + score; 3 candidate counts; ≥3 top sectors; ≥3 top themes; breadth %; last-scan date | Risk-on 76.05/100; Actionable=0, Breakout-watch=8, Pullback-watch=1; 5 sectors; 5 themes; 69.67% breadth; Data as-of 2026-06-25 | PASS | UT-J-01-expanded.png |
| UT-J-107 | Factor Lab — all-factors Rank-IC table with expandable decile sort | happy-path | P1 | All-factors table with family/Rank-IC/N/risk-adjusted; sortable NA-last; click-to-expand decile sort; N= chips link to samples in new tab | 11 factors listed; RANK-IC column sortable; first factor row expanded showing D1–D10 decile sort; N= chips have target="_blank" to /research/samples | PASS | UT-J-107-expanded.png |
| UT-J-26 | Factor Lab — multi-factor composite cohort | happy-path | P1 | Combined composite rank-blend cohort non-empty beside baseline + per-factor cohorts; mean/median/hit-rate/risk-adjusted shown; up to all factors | Baseline n=122964, RS 3m top n=24597, ATR% bottom n=40984, Combined n=24593, Strict overlap n=5578 all shown with stats | PASS | UT-J-26-result.png |
| UT-J-29 | Setup & Pattern research lab — event study | happy-path | P1 | Per-horizon distribution (mean/median/%positive/dispersion/expectancy/MAE/MFE/risk-adjusted); best exit-horizon; by-regime; by-sector; survivorship-bias label | "Actionable" subject shows 5 horizons (1d/5d/10d/20d/60d) with all columns; best exit=20d highlighted; by-regime and by-sector tables with NA for thin cells; Episodes/Pooled toggle present | PASS | UT-J-29-result.png |
| UT-J-51 | Every research sample count is a link to its exact samples | happy-path | P1 | N= chips are links opening samples in new tab; samples page total = published N; rows show ticker/date/value/return; deep-linkable; survivorship-bias label | N= chips have target="_blank" aria-label="See the 11761 observations in decile D1"; samples page total=11761 matches decile D1 N=11761; rows show COIN 2022-12-22 -87.66 +54.84% etc.; ticker links have target="_blank" in source | PASS | UT-J-51-samples-result.png |

---

## Passed Tests

### UT-J-01 — Daily dashboard at a glance
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-evidence/UT-J-01-expanded.png`
- Navigated to `/`. Dashboard loaded. Market Regime panel shows "Risk-on" with 76.05/100.
- Expanded "More detail" section via JS click on the button.
- Candidate counts visible: Actionable=0, Breakout-watch=8, Pullback-watch=1.
- Top Sectors: 5 listed — SOXX A 93.67, WGMI A 90.67, SMH A 90.00, XLK C 79.83, ROBO C 74.00.
- Top Themes: 5 listed — Semiconductors A 100.00, Ai Data Centre B 85.00, Cybersecurity C 78.00, Homebuilders D 67.00, Power Grid D 61.50.
- Breadth: ABOVE 50-DMA 69.67%, ABOVE 200-DMA 62.30%, NET NEW HIGHS 7.38%.
- Last-scan date shown as "Data as-of 2026-06-25".
- All acceptance criteria met.

---

### UT-J-107 — Factor Lab — all-factors Rank-IC table with expandable decile sort
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-evidence/UT-J-107-expanded.png`
- Navigated to `/research/factor-lab`. Page loaded as "Research — Factor Lab".
- All-factors table shows 11 factors with columns: FACTOR, FAMILY, RANK-IC, N, RISK-ADJUSTED (DOWNSIDE).
- Sorted by Rank-IC (desc): Proximity to 52w high +0.03, Risk score +0.02 … Entry Quality -0.02.
- Clicked first row (Proximity to 52-week high, aria-expanded=false); row expanded revealing decile sort D1–D10 with factor ranges, mean forward return, and risk-adjusted values.
- N= chips in decile rows confirmed `target="_blank" rel="noopener noreferrer"` with href `/research/samples?kind=factor&horizon=20&factor=high_proximity&slice=decile&decile=N`.
- Risk-adjusted uses downside deviation only (column label confirms "RISK-ADJUSTED (DOWNSIDE)").
- All acceptance criteria met.

---

### UT-J-26 — Factor Lab — multi-factor composite cohort
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-evidence/UT-J-26-result.png`
- Navigated to `/research/factor-combination`. Page shows "Research — Multi-factor combination".
- Selected 20d horizon. Cohort table appeared with:
  - Baseline (all names): n=122964, mean=+1.79%, median=+1.12%, hit-rate=+54.44%, risk-adj=+0.23
  - Relative strength vs SPY (3m) · top Quintile (20%): n=24597, mean=+2.41%
  - ATR % (volatility level) · bottom Tertile (33%): n=40984, mean=+1.48%
  - Combined (composite rank-blend): n=24593, mean=+1.78%, median=+1.51%, hit-rate=+58.19%, risk-adj=+0.37
  - Strict overlap (AND): n=5578, mean=+1.04%
- Combined cohort is non-empty (n=24593 >> min-sample 30).
- Factor dropdown shows all 11 catalog factors; "Add condition" button present.
- Text confirms "Combine 2–11 factor conditions" (config cap, not code).
- Survivorship bias label shown.
- All acceptance criteria met.

---

### UT-J-29 — Setup & Pattern research lab — event study across all snapshots
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-evidence/UT-J-29-result.png`
- Navigated to `/research/event-study`. Page shows "Research — Setup & Pattern event study".
- Subject selector: Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist, VCP, Pullback to a rising DMA, Flat-base breakout.
- Episodes/Pooled toggle present; Episodes is default.
- "Actionable" subject selected. Shows n=99 episodes, 33 unique symbols.
- Per-horizon table (1d/5d/10d/20d/60d) shows: MEAN, MEDIAN, % POSITIVE, DISPERSION, EXPECTANCY, MEAN MAE, MEAN MFE, MEAN MDD, RETURN/DOWNSIDE-DEV, RETURN/MAE.
- Best exit-horizon: 20d highlighted.
- By market regime: rows for all 6 regime labels (NA for thin cells, numeric for Defensive n=59 +1.90%).
- By sector: Technology, Financials, Energy, Health Care, Industrials, Consumer Discretionary, Consumer Staples, Utilities, Communication Services — NA for all below min-sample.
- Survivorship bias label shown.
- All acceptance criteria met.

---

### UT-J-51 — Every research sample count is a link to its exact samples
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-evidence/UT-J-51-samples-result.png`
- From Factor Lab decile expanded row, N= chips confirmed as `<a target="_blank" rel="noopener noreferrer" aria-label="See the 11761 observations in decile D1">`.
- Href: `/research/samples?kind=factor&horizon=20&factor=high_proximity&slice=decile&decile=1` — deep-linkable and parameterized.
- Navigated directly to that URL. Page: "Research Samples — observation drill-down".
- `await_text("Total observations: 11761")` succeeded — count equals the published N.
- Backend API confirmed `"total": 11761` in response.
- Each row: ticker (COIN), snapshot_date (2022-12-22), factor value (-87.66), forward_return (+54.84%).
- Samples-ticker-link in frontend source: `target="_blank" rel="noopener noreferrer"` at line 621–623 of `app/research/samples/page.tsx`.
- Survivorship bias label rendered on the page.
- All acceptance criteria met.

---

## Failed Tests

_(none)_

---

## Skipped Tests

_(none)_

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (Chrome DevTools Protocol)
- **Test Date:** 2026-06-26
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-51-evidence/`

## Notes

- The dashboard "More detail" section is collapsed by default; expansion required a JS-assisted click (the button is rendered as the last `<button>` in the DOM).
- The Research Samples page with 11761 rows is heavy — repeated screenshot captures timed out due to client-side table rendering. The `await_text` API confirmed the data loaded, and the count was verified directly via the backend API at `http://localhost:8255/api/research/samples`.
- All N= sample links carry `target="_blank"` (confirmed in HTML source of expanded Factor Lab row and in `apps/frontend/app/research/samples/page.tsx`).
