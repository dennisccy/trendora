# Goal Iter-4 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4
**Date:** 2026-06-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 tests passed (0 skipped, 0 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| J-47 | Full glossary + inline term help | happy-path | P1 | Categorized ≥100-term glossary on /methodology, live search filters, tooltips on all 5 surfaces reading same catalog | Glossary section with 118 terms across 6 categories renders; live search filters live (62 matches for "IC"); all spot-check terms present; tooltips on /research, /backtest, /stocks, /, /data all match API definitions | PASS | J-47-methodology-initial.png, J-47-methodology-search-IC.png, J-47-research-rankIC-tooltip.png, J-47-backtest-excess-return-tooltip.png, J-47-stocks-leadership-tooltip.png, J-47-dashboard-breadth50dma-tooltip.png, J-47-data-universe-tooltip.png |
| J-01 | Daily dashboard at a glance | regression | P1 | Regime label, candidate counts, top sectors/themes, breadth, timestamp | Regime "Risk-on" present; Actionable/Breakout-watch/Pullback-watch counts shown; sectors, themes, breadth %, and ISO dates present | PASS | J-01-dashboard.png |
| J-02 | Stock leaderboard with working filters | regression | P1 | 3-score rows, sector filter, setup-status filter | 122 rows with Leadership/Entry Quality/Risk scores + setup status; 4 filter controls present (sector, setup, VCP, etc.) | PASS | J-02-stocks.png |
| J-09 | Backtest forward-tested evidence | regression | P1 | By-bucket forward return, excess vs SPY/QQQ, by-setup, by-regime, sample size n, no local date picker | All evidence elements present; no local date picker (single global switcher only — 1 select in nav) | PASS | J-09-backtest.png |
| J-12 | Methodology setup/pattern catalog intact | regression | P1 | All 6 setups + VCP + additional patterns with thresholds + examples; glossary still present; setups referenced in Setups & Patterns category | All 6 setups (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist), VCP, and additional patterns present with thresholds and examples; 118-term glossary present; SETUPS & PATTERNS category confirmed single-sourced | PASS | J-12-methodology.png |
| J-18 | One date control — no local picker on Backtest | regression | P1 | Backtest has no page-local date dropdown; single global switcher drives it | 0 local date pickers on /backtest; 1 select total (the global switcher in nav, options starting "Latest · 2026-06-10") | PASS | J-18-backtest-one-date-control.png |
| J-25 | Factor Lab — decile sort and rank-IC | regression | P1 | Decile table + rank-IC per factor, raw and risk-adjusted, with n | Decile sort, Rank-IC, risk-adjusted column, n=sample-size all present; factors (RS, Leadership, ATR, etc.) present | PASS | J-25-J-26-research-factorlab.png |
| J-26 | Factor Lab — multi-factor composite cohort | regression | P1 | Composite cohort combination, hit-rate, n visible | Composite / combination cohort section present with hit-rate and n | PASS | J-25-J-26-research-factorlab.png |
| J-29 | Setup & Pattern research lab — event study | regression | P1 | Pooled forward-return distribution, hit-rate, expectancy, MAE/MFE, by-regime, by-sector | All event-study elements verified via DOM: event study heading, expectancy, MAE, MFE, by-regime, by-sector sections all present on /research | PASS | J-29-research-pattern-lab.png |
| J-36 | Understand coverage — per-symbol table + universe-vs-symbols | regression | P1 | Coverage panel with universe-vs-symbols distinction, per-symbol table, thin/missing flag, in-universe column | All elements present: universe vs symbols distinction, coverage section, date range, bar count, thin/missing flags, in-universe column, per-symbol table; info-tooltips on universe/symbols/in-universe/date-range/bar-count/thin-missing verified | PASS | J-36-data-coverage.png |

---

## Passed Tests

### J-47 — Full glossary + inline term help (≥100 terms, categorized + searchable, tooltips on 5 surfaces)

**Verdict:** PASS

**API corroboration:** `GET http://localhost:8835/api/methodology` served 118 terms across 6 categories (scores_buckets: 17, setups_patterns: 9, regime_breadth: 16, universe_data: 21, forward_evidence: 28, factor_stats: 27). All 19 step-3 spot-check terms found in payload (breadth > 50-DMA, DMA/50-DMA/200-DMA, rank-IC, universe, decile, MAE, MFE, expectancy, hit-rate, dispersion, walk-forward, survivorship bias, horizon, excess return, composite, quantile, ATR%, pivot, invalidation).

**Step 1 — /methodology Glossary section:**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-methodology-initial.png` (172,492 bytes, md5: bfdc52d35c20b52b1796b7e2034a48d4)
- Page text confirmed: "118 terms across 6 categories — every word the UI uses, from this one config-backed catalog."
- All 6 category headings present: SCORES & BUCKETS, SETUPS & PATTERNS, REGIME & BREADTH, UNIVERSE & DATA, FORWARD-TESTING & EVIDENCE, FACTOR LAB & STATISTICS
- All 19 spot-check terms readable in DOM (verified via `extract text`)

**Step 2 — Live search for "IC":**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-methodology-search-IC.png` (172,527 bytes, md5: c41145e54e485f1f0a71944ea0cfdfaf)
- Fired React `onChange` directly via `__reactProps` fiber method — the only reliable approach on this frontend (per project memory lesson)
- DOM showed "62 matches for 'IC'" with filtered entries including rank-IC with its definition visible
- rank-IC entry text in filtered DOM: "The rank Information Coefficient — the rank correlation between a factor's value and the subsequent forward return across names…"

**Step 3 — spot-check terms readable (rank-IC confirmed):**
- rank-IC definition in filtered glossary DOM matches API payload exactly (character-for-character)

**Step 4a — /research tooltips (rank-IC and decile):**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-research-rankIC-tooltip.png` (59,830 bytes, md5: 51484ef3fe59609334eadb109eb679d8)
- Clicked `button[aria-label="Definition of rank-IC"]` — tooltip panel rendered in DOM
- Tooltip text: "rank-IC — The rank Information Coefficient — the rank correlation between a factor's value and the subsequent forward return across names. Positive and stable means the factor sorts future returns; near zero means it doesn't. Where: Research → Factor Lab."
- API definition: "The rank Information Coefficient — the rank correlation between a factor's value and the subsequent forward return across names. Positive and stable means the factor sorts future returns; near zero means it doesn't." — EXACT MATCH
- Clicked `button[aria-label="Definition of decile"]` — tooltip: "One of ten equal-sized buckets a factor's values are sorted into (D1 = lowest, D10 = highest). Comparing mean forward returns across deciles shows whether the factor sorts returns monotonically." — matches API exactly

**Step 4b — /backtest tooltips (hit-rate and excess return):**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-backtest-excess-return-tooltip.png` (80,515 bytes, md5: 8abf94244b839915064d0546bddfd723)
- Tooltip buttons found: Definition of horizon, forward return, excess return (×3), random same-sector control, contributors & detractors, median, hit-rate, dispersion, n (sample size), by-sector, by-rank-band
- hit-rate tooltip: "The percentage of occurrences with a POSITIVE forward return — how OFTEN an idea worked, independent of how much. A high mean with a low hit-rate signals a few outliers carried the result." — matches API exactly
- excess return tooltip: "A cohort's forward return MINUS a benchmark's (SPY, QQQ, or sector ETF) over the same window — what the selection added beyond simply being in the market. Excess return separates skill from market beta." — matches API exactly

**Step 4c — /stocks tooltip (Leadership Score):**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-stocks-leadership-tooltip.png` (294,283 bytes, md5: dc49382889b1b7a82486072045675b1b)
- Tooltip buttons: Definition of Leadership Score, Entry Quality Score, Risk Score, setup status, reason summary, Extended (per row), Actionable, Breakout-watch, Pullback to rising DMA pattern, Flat-base breakout pattern
- Leadership Score tooltip: "How strong a stock is right now — a 0–100 weighted blend of relative strength, moving-average trend stack, proximity to its 52-week high, and up/down volume. One of three deliberately independent scores; a high Leadership says nothing about whether the entry is good." — matches API exactly

**Step 4d — / (Dashboard) tooltip (breadth > 50-DMA):**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-dashboard-breadth50dma-tooltip.png` (205,502 bytes, md5: 5a7204dc72320f5479f8957fc1aeab79)
- Tooltip buttons: Definition of market regime, breadth > 50-DMA, breadth > 200-DMA, net new-high/low, setup status, Actionable, Breakout-watch, Pullback-watch
- breadth > 50-DMA tooltip: "The percentage of universe stocks trading above their own 50-day moving average — a short-horizon breadth gauge. Falling participation here is an early warning even while the index holds." — matches API exactly

**Step 4e — /data (Data Manager) tooltip (universe):**
- Evidence: `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-47-data-universe-tooltip.png` (215,024 bytes, md5: 76fcf544b94da5a072146ba3411b88b0)
- Tooltip buttons: Definition of universe, symbols, in-universe, date range, bar count, thin/missing
- universe tooltip: "The config-screened set of SCORED names — a transparent, reproducible liquidity/market-cap/price screen, NOT a hand-picked list. Distinct from 'symbols': the universe is what gets ranked; symbols is every ticker with bars (incl. ETFs and ^VIX)." — matches API exactly

---

### J-01 — Daily dashboard at a glance

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-01-dashboard.png` (175,927 bytes, md5: a05911a9a5fd7ae014da2dbb81499c65)
- Regime label "Risk-on" present (one of the six defined labels)
- Candidate counts for Actionable, Breakout-watch, Pullback-watch all present
- Top Sectors and Top Themes present with scores
- Breadth percentage and ISO date timestamps rendered

---

### J-02 — Stock Leaderboard with working filters

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-02-stocks.png` (267,442 bytes, md5: 034c9ccf4ca97bcb1f83bacf6b8adeae)
- 122 table rows rendered (matching universe size)
- Leadership, Entry Quality, Risk columns confirmed; setup status present
- 4 filter controls present (sector, setup, pattern, VCP)
- Reason summaries visible in table

---

### J-09 — Backtest forward-tested evidence (as-of-scoped, expanding window)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-09-backtest.png` (146,993 bytes, md5: 725aaf41bef26729c5a120ca62a33b30)
- Forward return by score bucket (A–E) table with 20-day horizon rendered
- Excess vs SPY and QQQ values present
- By-setup-type breakdown present (Actionable, Breakout-watch, etc.)
- By-regime breakdown (Risk-on and others) present
- Sample size n= values shown; no fabricated numbers (NA for insufficient samples)
- No page-local date picker (only global switcher in nav)

---

### J-12 — Understand what each setup/pattern means (glossary + inline)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-12-methodology.png` (172,492 bytes, md5: bfdc52d35c20b52b1796b7e2034a48d4)
- All 6 setup statuses listed with THRESHOLDS sections and examples: Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist
- VCP pattern listed with 6 config thresholds and worked example
- Additional patterns (Pullback to a rising DMA, Flat-base breakout) also present
- SETUPS & PATTERNS glossary category confirmed — setups appear as references in the glossary, not re-described (single-sourced)
- 118-term glossary section present alongside the catalog

---

### J-18 — One date control (no duplicate on Backtest)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-18-backtest-one-date-control.png` (146,993 bytes)
- 0 `input[type="date"]` elements on /backtest
- 1 total `<select>` element — the global nav switcher (options: "Latest · 2026-06-10", "2026-06-09", …)
- `hasGlobalSwitcherInHeader: true` — single control drives all date-scoped content

---

### J-25 — Factor Lab — decile sort and rank-IC per factor

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-25-J-26-research-factorlab.png` (195,724 bytes, md5: 11885e139c256a57d8e81616f8774d7c)
- Decile sort table (D1→D10) with mean forward return column present
- Rank-IC section present with numeric value and n count
- Risk-adjusted (downside) column present
- Factor selector with multiple factors (RS, Leadership, ATR, volatility family, etc.)

---

### J-26 — Factor Lab — multi-factor composite cohort

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-25-J-26-research-factorlab.png` (195,724 bytes, md5: 11885e139c256a57d8e81616f8774d7c)
- "Multi-factor combination cohort" section heading present
- Combined cohort shown with hit-rate and n values
- Composite percentile rank-blend described as "transparent ranking of stored values, NOT a fitted/ML model"

---

### J-29 — Setup & Pattern research lab — event study

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-29-research-pattern-lab.png` (195,724 bytes, md5: 11885e139c256a57d8e81616f8774d7c)
- "Setup & Pattern Lab — event study" heading present on /research
- Per-horizon distribution table with expectancy, MAE, MFE, risk-adjusted ratios confirmed in DOM
- "By market regime (20d)" section present
- "By sector (20d)" section present
- Low-sample cells show NA + n (confirmed in page text)

---

### J-36 — Understand coverage — per-symbol table + universe-vs-symbols clarity

**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/J-36-data-coverage.png` (189,346 bytes, md5: ac9953cc003e14001204ad0e1747e48f)
- "Universe vs symbols" distinction explicitly stated: "universe (122) is the set of config-screened, scored names; symbols (162) is every ticker with bars…"
- Coverage section with date range (2021-02-25 → 2026-03-11), bar count, universe and symbol counts
- Per-symbol table with in-universe, has-data, date range, bar count, thin/missing columns
- Info-tooltips on universe, symbols, in-universe, date range, bar count, thin/missing — all verified to match API definitions

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Evidence Integrity

All screenshots verified non-blank (no md5 `23fe5583…` — the known blank dark rectangle). md5 duplicates explained:
- `J-09-backtest.png` = `J-18-backtest-one-date-control.png`: same /backtest page in same state (both tests verified on one navigation)
- `J-12-methodology.png` = `J-47-methodology-initial.png`: same /methodology page at top scroll (valid — tested sequentially)
- `J-25-J-26-research-factorlab.png` = `J-29-research-pattern-lab.png`: same /research page at top scroll after scroll-back (J-29 DOM content verified independently via markdown capture before screenshot)

API corroboration for J-47: `GET http://localhost:8835/api/methodology` → 118 terms, all 19 spot-check terms present, all tooltip texts match API definitions exactly (character-for-character verified for rank-IC, decile, hit-rate, excess return, Leadership Score, breadth > 50-DMA, universe).

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (mcp__plugin_superpowers-chrome_chrome__use_browser)
- **Test Date:** 2026-06-11
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4-evidence/`
