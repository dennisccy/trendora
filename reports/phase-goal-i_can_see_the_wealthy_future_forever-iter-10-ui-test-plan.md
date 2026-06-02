# Phase goal-i_can_see_the_wealthy_future_forever-iter-10 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835 (backend on http://localhost:8000)

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Research page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running at http://localhost:8000 with seed DB (`scanner_results` + `forward_returns`)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the loading skeleton to resolve (pulsing grey bars disappear)

**Expected Result:**
- Page renders without a blank screen or error overlay
- The heading "Research — Factor Lab" is visible at the top
- The subtitle starting "Does a factor actually sort future returns?" is visible
- A factor dropdown and a horizon button group are visible in the header
- A warning-coloured caveat banner, a decile table, and a Rank-IC card are all visible
- No browser console errors

---

### UT-02 — Default factor and horizon render the full Factor Lab (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Backend serving the catalog (8 factors) and the seed has ~1218 observations per factor

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Read the factor dropdown's currently selected value
3. Read the active (highlighted) horizon button
4. Read the decile table body
5. Read the Rank-IC card

**Expected Result:**
- The factor dropdown shows "Leadership score" selected by default
- The "20d" horizon button is highlighted (filled accent colour, `aria-pressed="true"`)
- The decile table has exactly 10 data rows labelled D1 through D10
- Each row shows a Factor range (e.g. `0.12 … 0.34`), a colour-graded "Mean fwd return" percentage, a "Risk-adjusted (downside)" ratio (signed, 2 decimals), and a sample-size `n` badge
- The Rank-IC card (`data-testid="rank-ic-value"`) shows one large signed number (e.g. `+0.08`) with an `n` badge and a sentence interpreting the sign
- The metadata line shows "Factor: Leadership score (score · higher better)", an "Observations:" count, and "Horizon: 20d"

---

### UT-03 — Factor dropdown options exactly match the server catalog (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `FactorSelector` (`data-testid="factor-select"`)

**Preconditions:**
- `/research` loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Click the factor dropdown (`data-testid="factor-select"`) to open it
3. Read every `<option>` label in order

**Expected Result:**
- The dropdown contains exactly these 8 options, in this order:
  1. Leadership score
  2. Entry Quality score
  3. Risk score (danger)
  4. Relative strength vs SPY (3m)
  5. Moving-average stack
  6. Proximity to 52-week high
  7. Up/down volume
  8. ATR % (volatility level)
- No "Loading…" placeholder option remains after the page resolves
- The option set equals the keys returned by `GET http://localhost:8000/api/research/factor-lab` (`factors[*].label`) — not a hardcoded list

---

### UT-04 — Selecting a different factor re-points the table and Rank-IC (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- `/research` loaded with default "Leadership score"

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Note the D10 "Mean fwd return" value and the Rank-IC number for "Leadership score"
3. In the factor dropdown, select "ATR % (volatility level)"
4. Wait for the table to refresh

**Expected Result:**
- The metadata line updates to "Factor: ATR % (volatility level) (volatility · lower better)"
- At least one decile "Mean fwd return" value changes versus the Leadership-score reading
- The Rank-IC number changes and its interpretation sentence now references "ATR % (volatility level)"
- A network request to `http://localhost:8000/api/research/factor-lab?factor=atr_pct...` is observed (values come from the server, not a client recompute)

---

### UT-05 — Selecting a different horizon re-points the table and Rank-IC (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `HorizonSelector` (`data-testid="horizon-select"`)

**Preconditions:**
- `/research` loaded; default horizon "20d" active

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Confirm one button exists per horizon: "1d", "5d", "10d", "20d", "60d"
3. Note the D1 "Mean fwd return" value at 20d
4. Click the "60d" button
5. Wait for the table to refresh

**Expected Result:**
- The "60d" button becomes highlighted (`aria-pressed="true"`) and "20d" is no longer highlighted
- The metadata line updates to "Horizon: 60d"
- At least one decile "Mean fwd return" value changes versus the 20d reading
- A network request including `horizon=60` is observed
- The Rank-IC value updates from server values

---

### UT-06 — Decile table columns and structure are correct (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research` — `DecileTable`

**Preconditions:**
- `/research` loaded with data

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Read the decile table column headers
3. Count the data rows

**Expected Result:**
- The panel title reads "Decile sort — raw & downside risk-adjusted"
- The four column headers read exactly: "Decile", "Factor range", "Mean fwd return", "Risk-adjusted (downside)"
- The "Risk-adjusted" header says "(downside)" — NOT "(total volatility)" or "(volatility)"
- Exactly 10 rows are present, labelled D1, D2, … D10 in order
- Positive mean returns render green, negative render red (colour-graded by sign)

---

### UT-07 — Rank-IC card shows value, sign, n, and interpretation (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research` — `RankICCard`

**Preconditions:**
- `/research` loaded with "Leadership score"

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Read the Rank-IC card panel title and value
3. Read the interpretation sentence below the value

**Expected Result:**
- The panel title reads "Rank-IC"
- `data-testid="rank-ic-value"` shows a signed number with 2 decimals (e.g. `+0.08`), coloured green if positive / red if negative
- An `n` badge appears beside the value
- The sentence reads either "A higher Leadership score is associated with a higher forward return in this universe (positive rank correlation)." (if positive) or the negative-correlation variant (if negative) — matching the displayed sign

---

### UT-08 — Caveat banner shows honesty labels verbatim (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research` — `CaveatBanner`

**Preconditions:**
- `/research` loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Read the warning-coloured banner near the top (below the header)

**Expected Result:**
- The banner heading reads exactly "Survivorship bias · universe-relative · descriptive" in warning colour with a shield-alert icon
- A survivorship-bias sentence is shown (e.g. mentions "survivorship bias" / "current-membership universe")
- A descriptive caveat sentence is shown (e.g. "Descriptive evidence, not a predictive model…")
- The banner text matches the server payload (`survivorship_bias` / `descriptive_caveat`), not a fabricated string

---

### UT-09 — Research is discoverable from the sidebar in ≤2 clicks (ux)

**Type:** ux
**Priority:** P1
**Surface:** navigation / sidebar (`components/sidebar.tsx`)

**Preconditions:**
- Frontend running; on any page (start from home)

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Look at the left sidebar between "System Health" and "Watchlist"
3. Click the "Research" item (microscope icon)

**Expected Result:**
- A "Research" link with a microscope icon is visible between "System Health" and "Watchlist"
- Clicking it changes the URL to `http://localhost:3835/research`
- The "Research — Factor Lab" heading loads (reached in 1 click from home)

---

### UT-10 — Low-sample / empty decile cells render explicit "NA" + n (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` — `DecileValue` (NA path)

**Preconditions:**
- `/research` loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Cycle the factor through all 8 options and the horizon through 1d/5d/10d/20d/60d, scanning for any cell that renders "NA"
3. If an "NA" cell is found, inspect it

**Expected Result:**
- Any decile cell with `n < min_sample` (the metadata line states the `n < ## ⚠` threshold) or zero observations shows the literal text "NA" plus its `n` badge — never blank, never a fabricated number
- NOTE: On the committed seed (~121 obs/decile) no cell is expected to render NA. If none appears, mark this test **Not-triggerable on seed** and confirm the backend unit test `test_low_sample_decile_is_flagged_with_its_n` covers it instead (do NOT fail the test for the absence of NA on this data)

---

### UT-11 — Backend-unavailable error state shows no fabricated figures (error)

**Type:** error
**Priority:** P2
**Surface:** `/research` — error Card

**Preconditions:**
- Frontend running; backend (`:8000`) STOPPED or unreachable

**Steps:**
1. Stop the backend (or block `:8000`)
2. Navigate to `http://localhost:3835/research`
3. Wait for the request to fail

**Expected Result:**
- A red-bordered card appears with the bold text "Backend unavailable"
- The body text explains "No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- NO decile table and NO Rank-IC number are shown (no fabricated values)
- The page does not crash to a blank screen

---

### UT-12 — Empty result (n_total === 0) shows the honest empty state (error)

**Type:** error
**Priority:** P3
**Surface:** `/research` — `EmptyState`

**Preconditions:**
- A factor/horizon combination where the server returns `n_total === 0` (may not be reproducible on the committed seed)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Select a factor/horizon combination that yields zero joined observations (if available on the test data)

**Expected Result:**
- An EmptyState with a microscope icon and the title "No forward-tested observations for this factor / horizon" appears
- The description explains no decile or rank-IC is fabricated to fill the gap
- NOTE: If not reproducible on the seed, mark **Not-triggerable on seed** — the path is unit-covered backend-side; do not fail

---

### UT-13 — /research exposes NO date / as-of selector (J-18 regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research` — page-level controls

**Preconditions:**
- `/research` loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scan the entire page (header and body) for any date picker, calendar, or "as-of" / date-selector control

**Expected Result:**
- There is NO date picker, calendar, or as-of control anywhere on `/research`
- The ONLY interactive controls are the factor dropdown (`data-testid="factor-select"`) and the horizon button group (`data-testid="horizon-select"`)

---

### UT-14 — Sidebar still has all prior items plus Research (regression)

**Type:** regression
**Priority:** P1
**Surface:** navigation / sidebar

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Count and read every sidebar item top-to-bottom

**Expected Result:**
- The sidebar now has 11 items (was 10); "Research" is the only addition
- "Research" sits between "System Health" and "Watchlist"
- All previously existing items and their relative order are unchanged

---

### UT-15 — System Health and dashboard still render (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/system-health`, `/`

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Confirm its existing by-bucket / excess / control-group evidence renders
3. Navigate to `http://localhost:3835/`
4. Confirm the dashboard content renders

**Expected Result:**
- `/system-health` renders its existing analytical content with no new errors
- `/` renders the dashboard with the full sidebar (including the new Research entry)
- No console errors introduced by this phase on either page

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research page loads | smoke | P1 | `/research` |
| UT-02 | Default factor/horizon renders lab | happy-path | P1 | `/research` |
| UT-03 | Factor options match server catalog | happy-path | P1 | `factor-select` |
| UT-04 | Factor change re-points table/IC | happy-path | P1 | `/research` |
| UT-05 | Horizon change re-points table/IC | happy-path | P1 | `horizon-select` |
| UT-06 | Decile table columns/structure | smoke | P1 | `DecileTable` |
| UT-07 | Rank-IC value/sign/n/interpretation | happy-path | P2 | `RankICCard` |
| UT-08 | Caveat banner honesty labels | ux | P2 | `CaveatBanner` |
| UT-09 | Research discoverable in sidebar | ux | P1 | sidebar |
| UT-10 | Low-sample cells render NA + n | validation | P2 | `DecileValue` |
| UT-11 | Backend-unavailable error state | error | P2 | error Card |
| UT-12 | Empty result honest empty state | error | P3 | `EmptyState` |
| UT-13 | No date/as-of selector (J-18) | regression | P1 | `/research` |
| UT-14 | Sidebar has all items + Research | regression | P1 | sidebar |
| UT-15 | System Health + dashboard render | regression | P1 | `/system-health`, `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Notes:**
- UT-10 and UT-12 are not triggerable on the committed seed (~121 obs/decile, all > min_sample); treat their absence as expected and defer to backend unit tests (`test_low_sample_decile_is_flagged_with_its_n`). Do NOT mark them FAIL for the data not triggering the path.
- Serialize Chrome access (one browser session at a time); de-dup screenshots by sha256.
</content>
</invoke>
