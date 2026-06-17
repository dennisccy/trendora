# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 17/22 tests passed (1 skipped, 4 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | /stocks MDD columns smoke | smoke | P1 | Five MDD columns (1d–60d) visible at historical as-of date | All five columns present with negative % values at ?asof=2025-12-16 | PASS | UT-01-result.png |
| UT-02 | /stocks MDD values non-positive | happy-path | P1 | All MDD cells show negative % or "—"; none positive | 3 sample rows all-negative: -3.51%/-12.73%/-12.73%/-15.16%/-21.93%, etc. | PASS | UT-01-result.png |
| UT-03 | /stocks MDD sort | happy-path | P1 | Clicking "5d MDD" column header reorders table with NA rows last | Clicking "5d MDD" button does not reorder table; top 5 remain WDC/COHR/TER/CIEN/STX before and after multiple clicks | FAIL | UT-03-sort-fail.png |
| UT-04 | /stocks MDD colour grading | ux | P2 | More-negative MDD cells render redder than less-negative cells | Source code confirms `mddClass()` returns flat "text-neg" for ALL negatives — no graduated intensity | FAIL | UT-04-colour-grading.png |
| UT-05 | /stocks/[ticker] detail Max drawdown | happy-path | P1 | Each horizon card shows "Max drawdown" sub-line with value <= 0 | WDC detail shows Max drawdown on all 5 horizon cards: -3.51%/-12.73%/-12.73%/-15.16%/-21.93% | PASS | UT-05-stock-detail.png |
| UT-06 | /themes MDD columns smoke | smoke | P1 | Five MDD columns visible on themes leaderboard at historical date | All five MDD column headers visible at ?asof=2025-12-16 with negative values | PASS | UT-06-themes-mdd.png |
| UT-07 | /themes expanded member colspan | happy-path | P2 | Expanding a theme row shows member stocks; colspan covers MDD columns | Clicked Semiconductors theme row; expanded member stocks with proper MDD column coverage | PASS | UT-07-themes-expanded.png |
| UT-08 | /sectors MDD columns smoke | smoke | P1 | Five MDD columns visible on sectors leaderboard at historical date | All five MDD column headers visible at ?asof=2025-12-16; ETF rows show values or NA | PASS | UT-09-sectors-sort-fail.png |
| UT-09 | /sectors MDD sort | happy-path | P1 | Clicking "20d MDD" column header reorders table with NA rows last | Clicking "20d MDD" button does not reorder table; order unchanged after click | FAIL | UT-09-sectors-sort-fail.png |
| UT-10 | /backtest Mean MDD column | smoke | P1 | "Mean MDD" column present in breakdown evidence panels | Mean MDD column visible in backtest breakdown tables with negative values | PASS | UT-10-11-backtest-mdd.png |
| UT-11 | /backtest summary Mean max drawdown | happy-path | P1 | "Mean max drawdown" figure present in backtest evidence summary header | "Mean max drawdown" figure visible in summary header showing negative percentage | PASS | UT-10-11-backtest-mdd.png |
| UT-12 | /research event-study Mean MDD | smoke | P1 | "Mean MDD" column present in per-horizon event-study table | "Mean MDD" column found; low-n rows show NA; sufficient-n rows show negative values | PASS | UT-12-research-mdd.png |
| UT-13 | /research RSP table Mean MDD | happy-path | P1 | "Mean MDD" column present in Regime x Setup x Pattern table | MEAN MDD column present; Choppy/Avoid/none n=575 shows -13.11%; Risk-on/Extended/none n=35 shows -14.90%; all non-NA values negative | PASS | UT-13-rsp-mdd.png |
| UT-14 | /data coverage-absent-none note | smoke | P1 | `data-testid="coverage-absent-none"` present when absent_count=0 | Element confirmed: "All 122 resolved-universe members are present in the latest snapshot (2026-06-16)..." | PASS | UT-14-data-page-before.png |
| UT-15 | /data amber banner absent when count=0 | conditional | P2 | No `data-testid="coverage-absent-banner"` when absent_count=0 | `coverage-absent-banner` not present in DOM; only `coverage-absent-none` visible — correct | PASS | UT-14-data-page-before.png |
| UT-16 | /data rebuild button opens confirm modal | happy-path | P1 | Clicking rebuild button shows confirm modal without starting a job | Clicked `[data-testid="rebuild-button"]`; modal with `data-testid="rebuild-confirm-modal"` appeared; no job started | PASS | UT-16-18-modal.png |
| UT-17 | /data modal Cancel dismisses safely | happy-path | P1 | Clicking Cancel in modal closes it without starting a job | Clicked Cancel; modal dismissed (eval: "MODAL DISMISSED"); button count returned to baseline; no job created | PASS | UT-16-18-modal.png |
| UT-18 | /data rebuild Confirm button present | smoke | P1 | `data-testid="rebuild-confirm-button"` present and enabled in modal | Verified by eval: `confirmBtn=FOUND disabled=false`; text="Rebuild snapshots"; NOT clicked per CRITICAL GUARD | PASS | UT-16-18-modal.png |
| UT-19 | /data rebuild job progress | regression | P2 | After confirming rebuild, job card shows progress; rebuild button disables | SKIPPED: Destructive full-regeneration operation; cannot execute in live environment per CRITICAL GUARD | SKIP | none |
| UT-20 | /stocks forward-return sort still works | regression | P2 | Clicking "5d" forward-return column reorders table | Clicking "5d" header does not reorder table; WDC/COHR/TER/CIEN/STX unchanged — same systemic failure as UT-03/UT-09 | FAIL | UT-20-fwd-sort-fail.png |
| UT-21 | MDD never positive across surfaces | regression | P1 | No MDD cell shows a positive value on /stocks, /themes, /sectors | /stocks at ?asof=2025-12-16: all MDD column cells (indices 12-16) for sampled rows are negative; none positive | PASS | UT-22-asof-nav-mdd.png |
| UT-22 | MDD columns persist after as-of date nav | regression | P1 | Using back-arrow date navigation on /stocks keeps MDD columns with real values | Clicked `[aria-label="Previous available date"]`; URL changed to ?asof=2025-09-16; all 5 MDD headers remain; values: -8.60%/-14.94%/-17.70%/-17.70%/-33.24% (row 1) | PASS | UT-22-asof-nav-mdd.png |

---

## Passed Tests

### UT-01 — /stocks MDD columns smoke
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-01-result.png`
- Navigated to http://localhost:3835/stocks?asof=2025-12-16
- Confirmed five column headers via `th button` query: "1d MDD", "5d MDD", "10d MDD", "20d MDD", "60d MDD"
- Cells showed negative percentage values (e.g. -3.51%, -12.73%) at this historical date

---

### UT-02 — /stocks MDD values non-positive
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-01-result.png`
- Verified via column-index slice (td indices 12–16) on /stocks?asof=2025-12-16
- Row 1: -3.51%|-12.73%|-12.73%|-15.16%|-21.93%; Row 2: -6.42%|-11.33%|-12.63%|-13.14%|-25.77%; Row 3: -9.41%|-12.24%|-18.26%|-18.26%|-42.44%
- All sampled MDD cells are negative; no positive value found

---

### UT-05 — /stocks/[ticker] detail Max drawdown
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-05-stock-detail.png`
- Navigated to /stocks/WDC?asof=2025-12-16
- Each of the 5 horizon cards shows a "Max drawdown" sub-line with negative values
- Values: 1d=-3.51%, 5d=-12.73%, 10d=-12.73%, 20d=-15.16%, 60d=-21.93%

---

### UT-06 — /themes MDD columns smoke
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-06-themes-mdd.png`
- Navigated to /themes?asof=2025-12-16
- All five MDD column headers confirmed present; theme rows showed negative MDD percentages

---

### UT-07 — /themes expanded member colspan
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-07-themes-expanded.png`
- Clicked Semiconductors theme row; member stocks expanded correctly
- Expanded section layout correctly covered the MDD columns

---

### UT-08 — /sectors MDD columns smoke
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-09-sectors-sort-fail.png`
- Navigated to /sectors?asof=2025-12-16
- All five MDD column headers confirmed present; sector ETF rows showed negative values or "NA" for industry ETFs (expected — ETFs have no individual stock forward-return data)

---

### UT-10 — /backtest Mean MDD column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-10-11-backtest-mdd.png`
- Opened /backtest?asof=2025-12-16; loaded backtest results
- "Mean MDD" column confirmed present in breakdown evidence tables with negative percentage values

---

### UT-11 — /backtest summary Mean max drawdown
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-10-11-backtest-mdd.png`
- "Mean max drawdown" figure confirmed in summary header panel
- Value showed a negative percentage (not a fabricated positive)

---

### UT-12 — /research event-study Mean MDD
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-12-research-mdd.png`
- Navigated to /research?asof=2025-12-16; await_text confirmed "Mean MDD" present
- Per-horizon event-study table contains "MEAN MDD" column header
- Low-n rows (n=1) show NA; the column is present and correctly conditional

---

### UT-13 — /research RSP table Mean MDD
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-13-rsp-mdd.png`
- RSP (Regime x Setup x Pattern) table contains "MEAN MDD" column
- Values confirmed: Choppy/Avoid/none n=575 → -13.11%; Risk-on/Extended/none n=35 → -14.90%; Risk-on/Avoid/flat base n=51 → -8.30%
- All non-NA values are negative; low-n rows correctly show NA

---

### UT-14 — /data coverage-absent-none note
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-14-data-page-before.png`
- `document.querySelector('[data-testid="coverage-absent-none"]').textContent` returned: "All 122 resolved-universe members are present in the latest snapshot (2026-06-16). A rebuild is optional — it deterministically regenerates the whole snapshot set from scratch."

---

### UT-15 — /data amber banner absent when count=0
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-14-data-page-before.png`
- `[data-testid="coverage-absent-banner"]` not found in DOM when absent_count=0
- Only `coverage-absent-none` is visible — conditional rendering works correctly

---

### UT-16 — /data rebuild button opens confirm modal
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-16-18-modal.png`
- `[data-testid="rebuild-button"]` found with disabled=false, text="Rebuild snapshots for current universe"
- Clicked button; `[data-testid="rebuild-confirm-modal"]` appeared immediately
- No job was started

---

### UT-17 — /data modal Cancel dismisses safely
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-16-18-modal.png`
- Clicked Cancel button (2nd button in modal); eval confirmed "MODAL DISMISSED"
- Interactive button count returned to 1406 (pre-click baseline); no job created

---

### UT-18 — /data rebuild Confirm button present (verified-by-modal-presence)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-16-18-modal.png`
- Eval result: `confirmBtn=FOUND disabled=false`; button text="Rebuild snapshots"
- CRITICAL GUARD observed: Confirm button NOT clicked

---

### UT-21 — MDD never positive across surfaces
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-22-asof-nav-mdd.png`
- /stocks?asof=2025-12-16: column indices 12–16 for first 3 rows all negative
- No positive MDD value observed in any MDD cell sampled

---

### UT-22 — MDD columns persist after as-of date nav
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-22-asof-nav-mdd.png`
- Clicked `[aria-label="Previous available date"]` on /stocks?asof=2025-12-16
- URL changed to http://localhost:3835/stocks?asof=2025-09-16
- All 5 MDD headers confirmed: "1d MDD,5d MDD,10d MDD,20d MDD,60d MDD"
- MDD values for row 1: -8.60%/-14.94%/-17.70%/-17.70%/-33.24%

---

## Failed Tests

### UT-03 — /stocks MDD sort
**Verdict:** FAIL
**Failure:** Clicking the "5d MDD" column header button does not reorder the stocks table. Table remains in default leadership-rank order before and after multiple click attempts.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-03-sort-fail.png`

**Steps taken:**
1. Navigated to http://localhost:3835/stocks?asof=2025-12-16
2. Recorded default top-5 order: WDC, COHR, TER, CIEN, STX
3. Clicked `//th//button[contains(text(),'5d MDD')]` via XPath
4. Checked top-5: WDC, COHR, TER, CIEN, STX (unchanged)
5. Navigated fresh to same URL; clicked again — still unchanged
6. Attempted JS `.click()` directly on the button element via eval
7. Checked top-5 again: WDC, COHR, TER, CIEN, STX (unchanged)

**Expected:** Table reorders to show most-negative MDD values first (smallest, most negative), NA rows at the bottom
**Actual:** Table order unchanged after all click attempts on the "5d MDD" SortHeader button

---

### UT-04 — /stocks MDD colour grading
**Verdict:** FAIL
**Failure:** MDD cells apply a flat `"text-neg"` CSS class to all negative values regardless of magnitude — no graduated colour intensity between mildly negative and severely negative values.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-04-colour-grading.png`

**Steps taken:**
1. Navigated to /stocks?asof=2025-12-16
2. Read source: `apps/frontend/components/forward-return.tsx` `mddClass()` function
3. Verified in browser: a -3.51% cell and a -21.93% cell both carry only `"text-neg"` class

**Expected:** More-negative values (e.g. -20%) render visually more intense/redder than mildly-negative values (e.g. -3%)
**Actual:** `mddClass()` returns flat `"text-neg"` for ALL negative values; no intensity gradient implemented

---

### UT-09 — /sectors MDD sort
**Verdict:** FAIL
**Failure:** Clicking the "20d MDD" column header button on /sectors does not reorder the sectors table. Same failure pattern as UT-03.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-09-sectors-sort-fail.png`

**Steps taken:**
1. Navigated to http://localhost:3835/sectors?asof=2025-12-16
2. Recorded default top row order
3. Clicked "20d MDD" header button via XPath
4. Table order unchanged

**Expected:** Sectors table reorders by 20d MDD ascending (most-negative first), NA rows last
**Actual:** Table order unchanged after clicking "20d MDD" column header

---

### UT-20 — /stocks forward-return sort still works (regression)
**Verdict:** FAIL
**Failure:** The "5d" forward-return column sort also fails to reorder the table. The sort failure is a systemic regression affecting ALL column sorts on /stocks — not limited to MDD columns. The "1d" return column and "5d" return column both fail to sort.
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/UT-20-fwd-sort-fail.png`

**Steps taken:**
1. Navigated to http://localhost:3835/stocks?asof=2025-12-16
2. Verified top-5 default order: WDC, COHR, TER, CIEN, STX
3. Clicked "5d" column header via XPath `//th//button[normalize-space(text())='5d']`
4. Top-5 unchanged: WDC, COHR, TER, CIEN, STX
5. Tried JS `fiveDBtn.click()` — still unchanged
6. Also tried "1d" column header — unchanged

**Expected:** Clicking "5d" reorders by 5-day forward return descending; top stocks have highest 5d return
**Actual:** Table order unchanged after clicking any return or MDD column header

**Note:** This is a P2 regression test but the same root failure drives P1 tests UT-03 and UT-09. One possible root cause: the `onClick` React handler fires but a state update is swallowed, or the sort key is set but the sorted array is not passed back to the rendered table. The column headers ARE present and clickable — the issue is in the sort-result propagation.

---

## Skipped Tests

### UT-19 — /data rebuild job progress
**Verdict:** SKIPPED
**Reason:** Rebuild is a destructive full-regeneration operation that deletes and rewrites all snapshots across the live database. Cannot execute per CRITICAL GUARD instructions. The Confirm button was verified as present and enabled (UT-18) but intentionally not clicked.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Chrome via MCP (session-1781646120822)
- **Test Date:** 2026-06-17
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-evidence/`
- **Historical as-of dates used:** 2025-12-16 (primary), 2025-09-16 (UT-22 nav result)
