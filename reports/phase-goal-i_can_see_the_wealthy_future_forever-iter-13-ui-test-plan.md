# Phase goal-i_can_see_the_wealthy_future_forever-iter-13 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Factor Lab page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running and reachable (port 8835)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (skeleton placeholders replaced by real tables)

**Expected Result:**
- The heading "Research — Factor Lab" is visible
- The amber caveat card titled "Survivorship bias · universe-relative · descriptive" is visible
- A "Factor" dropdown and a "Horizon" toggle (e.g. `5d` / `60d` buttons) are visible in the top-right control row
- The "Decile sort — raw & downside risk-adjusted" table and the "Rank-IC" card both render with data
- No "Backend unavailable" red error card appears; no blank screen; no console errors

---

### UT-02 — Factor dropdown is grouped by family with a 4-entry Volatility group (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `FactorSelector` (`data-testid="factor-select"`)

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Click the "Factor" dropdown (the `<select>` under the "Factor" label, top-right)
2. Read the option groups (native `<optgroup>` sub-headings)
3. Locate the group labelled "Volatility"

**Expected Result:**
- The dropdown options are organized under capitalised family sub-headings (e.g. "Score", "Momentum", "Trend", "Volatility") — NOT a flat list
- The "Volatility" group lists exactly four entries, in order:
  - "ATR % (volatility level)"
  - "Historical volatility (HV)"
  - "Volatility contraction (VCP-style)"
  - "Downside volatility (semivol)"
- No volatility entry appears outside the "Volatility" group

---

### UT-03 — Selecting Historical volatility (HV) re-points the lab and shows correct header (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — factor change → decile table / rank-IC / regime split

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Open the "Factor" dropdown and select "Historical volatility (HV)" from the "Volatility" group
2. Wait for the tables to re-render
3. Read the factor header line above the decile table (the "Factor: … (family · direction)" line)
4. Read the "Rank-IC" card value (`data-testid="rank-ic-value"`)

**Expected Result:**
- The factor header line reads `Factor: Historical volatility (HV) (volatility · lower better)`
- The decile table re-populates for HV (the page does NOT stay on the previously selected factor)
- The Rank-IC card shows a numeric value with a `+`/`−` sign (approximately `+0.03`) and a sample-size `n` chip beside it — NOT "NA", NOT blank
- The Rank-IC explanatory sentence references "Historical volatility (HV)"

---

### UT-04 — Volatility contraction decile table shows raw + downside-risk-adjusted columns with n (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — Decile table

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Open the "Factor" dropdown and select "Volatility contraction (VCP-style)" from the "Volatility" group
2. Wait for the decile table to re-render
3. Inspect the "Decile sort — raw & downside risk-adjusted" table

**Expected Result:**
- The table has columns: "Decile", "Factor range", "Mean fwd return", "Risk-adjusted (downside)"
- Rows D1 through D10 are listed
- At least one populated decile shows a signed percentage in "Mean fwd return" and a signed ratio (e.g. `+0.12`) in "Risk-adjusted (downside)"
- Each decile row shows a small sample-size `n` chip beside its values
- The factor header line reads `Factor: Volatility contraction (VCP-style) (volatility · lower better)`

---

### UT-05 — Downside volatility risk-adjusted column shows honest NA + n, never a fabricated 0 (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` — Decile table risk-adjusted cell / Regime table

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Open the "Factor" dropdown and select "Downside volatility (semivol)" from the "Volatility" group
2. Scan the "Risk-adjusted (downside)" column in the decile table for a cell showing "NA"
3. If no decile NA is present, scroll to the "Factor effectiveness by market regime" table (`data-testid="regime-effectiveness-table"`) and find a low-sample regime row (e.g. a regime with `n` of 0 or below the minimum)

**Expected Result:**
- At least one cell (a decile's "Risk-adjusted (downside)" cell, or a low-sample regime row) displays the literal text "NA" in muted grey — NOT "0", NOT "0.00", NOT blank
- A sample-size `n` chip is shown beside / on the same row as the NA cell (honest n is preserved)
- Hovering the NA cell shows a tooltip such as "Low sample — n below the … minimum" or "No observations" (downside undefined: a healthy all-up decile is NOT penalised)

---

### UT-06 — By-regime split renders for a new factor with NA on empty regimes (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research` — `RegimeEffectivenessTable` (`data-testid="regime-effectiveness-table"`)

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Open the "Factor" dropdown and select "Volatility contraction (VCP-style)"
2. Scroll to the "Factor effectiveness by market regime" table
3. Read the per-regime rows and their columns (Regime, n, Rank-IC, Top-decile mean, Bottom-decile mean, Spread, Risk-adjusted spread)

**Expected Result:**
- One row per configured regime label is shown
- At least one populated regime row shows a numeric Rank-IC and numeric spread values
- At least one genuinely empty/low-sample regime (e.g. "Strong risk-on" or "Defensive" with n=0) shows "NA" cells plus its `n` chip — NOT a fabricated 0

---

### UT-07 — Caveat banner stays visible with a new volatility factor selected (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research` — `CaveatBanner`

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Open the "Factor" dropdown and select "Downside volatility (semivol)"
2. Look at the amber card near the top of the page

**Expected Result:**
- The caveat card titled "Survivorship bias · universe-relative · descriptive" remains visible
- Both caveat lines are present: the survivorship-bias text and the "Descriptive evidence, not a predictive model …" text

---

### UT-08 — As-of date toggle does NOT re-point the Factor Lab (regression / J-18 guard)

**Type:** regression
**Priority:** P1
**Surface:** `/research` — global as-of date control vs Factor Lab

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded
- A global as-of date control is available in the app shell/header

**Steps:**
1. Select "Historical volatility (HV)" in the "Factor" dropdown and note the decile table values and the Rank-IC value
2. Change the global as-of date control to a different date
3. Re-read the Factor-Lab decile table values and Rank-IC value

**Expected Result:**
- The Factor-Lab decile table and Rank-IC value are byte-identical before and after the as-of change (the lab is a cross-date aggregate — it does not move with as-of)
- (If observing the network tab) no request carrying an `as_of` query parameter fires from the Factor Lab on the toggle

---

### UT-09 — Switching factors re-renders cleanly with no stale data (regression / J-25 + J-27)

**Type:** regression
**Priority:** P2
**Surface:** `/research` — factor change

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Select "ATR % (volatility level)" and note the Rank-IC value
2. Select "Historical volatility (HV)" and note the Rank-IC value
3. Select "Downside volatility (semivol)" and note the Rank-IC value
4. Re-select "ATR % (volatility level)"

**Expected Result:**
- The decile table, Rank-IC card, and regime table re-render on every selection
- The Rank-IC value changes between distinct factors (no frozen/stale value carried over)
- Re-selecting "ATR % (volatility level)" returns to its original ATR% values

---

### UT-10 — Risk-Off run shows zero Actionable after DB regen (regression / J-07 critical)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` (seeded Risk-Off run)

**Preconditions:**
- DB regenerated this iteration
- A seeded Risk-Off run is available/selectable on `/stocks`

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Select / open the seeded Risk-Off run
3. Count the stocks marked "Actionable" (vs watchlist-only)

**Expected Result:**
- Zero stocks are marked "Actionable" under Risk-Off (the Risk-Off gate is intact after DB regen)

---

### UT-11 — NVDA scores byte-identical across leaderboard and detail after DB regen (regression / J-06 critical)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` and `/stocks/NVDA`

**Preconditions:**
- DB regenerated this iteration

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Locate the NVDA row; read its Leadership, Entry Quality, and Risk scores (number + A–E bucket)
3. Navigate to `http://localhost:3835/stocks/NVDA`
4. Read the same three scores (number + bucket) in the detail score breakdown

**Expected Result:**
- Leaderboard and detail values match exactly for all three scores:
  - Leadership 47.48 / bucket E
  - Entry Quality 66.24 / bucket D
  - Risk 33.79 / bucket E
- No discrepancy between the two views

---

### UT-12 — New volatility values are NOT shown on the stock detail breakdown (ux / scope guard)

**Type:** ux
**Priority:** P3
**Surface:** `/stocks/NVDA` — score breakdown

**Preconditions:**
- DB regenerated this iteration

**Steps:**
1. Navigate to `http://localhost:3835/stocks/NVDA`
2. Inspect the score breakdown / indicator panels

**Expected Result:**
- The new volatility measures `hv`, `vcp_contraction`, `downside_vol` are NOT displayed anywhere on the stock detail page (they are stored for Factor-Lab read-only consumption only and enter no weighted score)
- The three displayed scores match the leaderboard (consistent with UT-11)

---

### UT-13 — Volatility family is discoverable in the dropdown (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research` — `FactorSelector`

**Preconditions:**
- On `http://localhost:3835/research`, page fully loaded

**Steps:**
1. Open the "Factor" dropdown
2. Without prior knowledge, look for where the volatility measures live

**Expected Result:**
- The four volatility measures are visually collected under a single "Volatility" sub-heading, making the family obvious at a glance (the grouping aids discoverability vs the old flat list)
- Labels are self-describing: "ATR % (volatility level)", "Historical volatility (HV)", "Volatility contraction (VCP-style)", "Downside volatility (semivol)"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Factor Lab loads | smoke | P1 | `/research` |
| UT-02 | Dropdown grouped, 4 Volatility entries | happy-path | P1 | `/research` factor-select |
| UT-03 | HV re-points + header `volatility · lower better` | happy-path | P1 | `/research` |
| UT-04 | VCP decile raw + risk-adjusted + n | happy-path | P1 | `/research` decile table |
| UT-05 | Downside semivol honest NA + n | validation | P2 | `/research` decile/regime |
| UT-06 | By-regime split + empty-regime NA | happy-path | P2 | `/research` regime table |
| UT-07 | Caveat banner still visible | regression | P2 | `/research` |
| UT-08 | As-of toggle does not re-point lab | regression | P1 | `/research` |
| UT-09 | Factor switch re-renders, no stale data | regression | P2 | `/research` |
| UT-10 | Risk-Off Actionable=0 after regen | regression | P1 | `/stocks` |
| UT-11 | NVDA scores byte-identical across views | regression | P1 | `/stocks`, `/stocks/NVDA` |
| UT-12 | Volatility values not on detail breakdown | ux | P3 | `/stocks/NVDA` |
| UT-13 | Volatility family discoverable | ux | P3 | `/research` |

**P1 tests must all pass for browser QA verdict to be PASS.**
**Critical gates:** UT-10 (Risk-Off=0) and UT-11 (NVDA consistency) — any failure here is a hard blocker after the DB regen.
