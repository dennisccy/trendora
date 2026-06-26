# UI Test Results (merged)

**Date:** 2026-06-26
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Daily dashboard at a glance | happy-path | P1 | Regime label + score; 3 candidate counts; ≥3 top sectors; ≥3 top themes; breadth %; last-scan date | Risk-on 76.05/100; Actionable=0, Breakout-watch=8, Pullback-watch=1; 5 sectors; 5 themes; 69.67% breadth; Data as-of 2026-06-25 | PASS | UT-J-01-expanded.png |
| UT-J-107 | Factor Lab — all-factors Rank-IC table with expandable decile sort | happy-path | P1 | All-factors table with family/Rank-IC/N/risk-adjusted; sortable NA-last; click-to-expand decile sort; N= chips link to samples in new tab | 11 factors listed; RANK-IC column sortable; first factor row expanded showing D1–D10 decile sort; N= chips have target="_blank" to /research/samples | PASS | UT-J-107-expanded.png |
| UT-J-26 | Factor Lab — multi-factor composite cohort | happy-path | P1 | Combined composite rank-blend cohort non-empty beside baseline + per-factor cohorts; mean/median/hit-rate/risk-adjusted shown; up to all factors | Baseline n=122964, RS 3m top n=24597, ATR% bottom n=40984, Combined n=24593, Strict overlap n=5578 all shown with stats | PASS | UT-J-26-result.png |
| UT-J-29 | Setup & Pattern research lab — event study | happy-path | P1 | Per-horizon distribution (mean/median/%positive/dispersion/expectancy/MAE/MFE/risk-adjusted); best exit-horizon; by-regime; by-sector; survivorship-bias label | "Actionable" subject shows 5 horizons (1d/5d/10d/20d/60d) with all columns; best exit=20d highlighted; by-regime and by-sector tables with NA for thin cells; Episodes/Pooled toggle present | PASS | UT-J-29-result.png |
| UT-J-51 | Every research sample count is a link to its exact samples | happy-path | P1 | N= chips are links opening samples in new tab; samples page total = published N; rows show ticker/date/value/return; deep-linkable; survivorship-bias label | N= chips have target="_blank" aria-label="See the 11761 observations in decile D1"; samples page total=11761 matches decile D1 N=11761; rows show COIN 2022-12-22 -87.66 +54.84% etc.; ticker links have target="_blank" in source | PASS | UT-J-51-samples-result.png |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-06-26

