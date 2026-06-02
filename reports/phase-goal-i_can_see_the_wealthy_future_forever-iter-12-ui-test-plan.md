# Phase goal-i_can_see_the_wealthy_future_forever-iter-12 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- UT-XX prefix distinguishes these from the functional plan's TC-XX (API) tests. -->
<!-- Every step is independently executable. No API curl tests here — those live in the functional plan. -->

---

### UT-01 — `/research` page loads with the combination section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running at http://localhost:8000 with price/forward-return seed data present

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (loading skeletons disappear)
3. Scroll to the bottom of the page, below the "Factor effectiveness by market regime" table

**Expected Result:**
- The page heading "Research — Factor Lab" is visible at the top
- A Card titled "Multi-factor combination cohort" is visible at the bottom (the section is `data-testid="combination-section"`)
- The section shows condition control rows and a comparison table — no blank area, no error card, no permanent skeleton
- No uncaught errors in the browser console

---

### UT-02 — Default combination cohort renders Baseline + 2 singles + Combined (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `combination-table`

**Preconditions:**
- UT-01 passed; the "Multi-factor combination cohort" section is visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Multi-factor combination cohort" section
3. Read the comparison table (`data-testid="combination-table"`)

**Expected Result:**
- The table header row shows exactly six columns: "Cohort", "n", "Mean fwd return", "Median", "Hit-rate", "Risk-adjusted (downside)"
- Row 1 is the **Baseline (all names)** cohort (label-styled, e.g. "Baseline (all names)")
- Rows 2 and 3 are **single-condition** cohorts, each labelled like "<Factor label> · top <Quantile label>" (e.g. "Relative strength vs SPY (3m) · top Quintile (20%)")
- The final row is the **Combined (AND)** cohort, visually emphasised with a shaded background
- Each row's "n" column shows a sample-size chip with a number; the Mean/Median/Hit-rate/Risk-adjusted cells show either a signed value or "NA" (never a blank cell)
- Above the table there are two condition control rows; below the table the note "The risk-adjusted column is downside-deviation only … return/MAE and MAE/MFE excursion measures arrive with the event-study lab (J-29)." is visible

---

### UT-03 — Changing a condition factor re-points the table (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `condition-factor-0`

**Preconditions:**
- UT-02 passed; the combination table is visible with default conditions

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the "Multi-factor combination cohort" section
2. Note the current label and "Mean fwd return" value of the **first single-condition row** in the table
3. In the first condition control row, open the "Factor" dropdown (`data-testid="condition-factor-0"`, aria-label "Condition 1 factor") and select a different factor than the one currently shown
4. Wait ~1 second for the table to re-fetch (the table briefly dims, then refreshes)

**Expected Result:**
- The first single-condition row's label updates to reflect the newly chosen factor (e.g. "<New factor label> · top Quintile (20%)")
- The first single-condition row's n / Mean fwd return / Median / Hit-rate / Risk-adjusted values change to match the new factor
- The Combined (AND) row also re-computes (its values may change)
- No error card appears; the table remains populated

---

### UT-04 — Toggling a condition side from Top to Bottom updates the cohort (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research` → `condition-side-0`

**Preconditions:**
- UT-02 passed; the combination table is visible

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the combination section
2. In the first condition control row, locate the "Side" segmented toggle (`data-testid="condition-side-0"`) — the "Top" button is highlighted by default
3. Note the first single-condition row's label and n in the table
4. Click the "Bottom" button in that toggle
5. Wait ~1 second for the table to refresh

**Expected Result:**
- The "Bottom" button becomes highlighted (accent background); "Top" becomes unhighlighted
- The first single-condition row's label changes from "… · top <Quantile>" to "… · bottom <Quantile>"
- That row's n / Mean / Median / Hit-rate / Risk-adjusted values change (different cohort membership)
- The Combined (AND) row re-computes accordingly

---

### UT-05 — Changing the quantile grows or shrinks the cohort sample (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research` → `condition-quantile-0`

**Preconditions:**
- UT-02 passed; the combination table is visible

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the combination section
2. Note the first single-condition row's "n" value
3. In the first condition control row, open the "Quantile" dropdown (`data-testid="condition-quantile-0"`, aria-label "Condition 1 quantile") and select a wider quantile (e.g. change from "Quintile (20%)" to "Half (50%)")
4. Wait ~1 second for the table to refresh

**Expected Result:**
- The first single-condition row's label updates the quantile portion (e.g. "… · top Half (50%)")
- The first single-condition row's "n" **increases** when moving to a wider quantile (e.g. quintile → half), or **decreases** when moving to a narrower quantile (e.g. half → tertile)
- The Combined (AND) row's n remains ≤ each single row's n

---

### UT-06 — Add a 3rd condition extends the table to 3 singles (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `condition-add`

**Preconditions:**
- UT-02 passed; default is 2 condition rows; `max_conditions` is 3

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the combination section
2. Confirm there are exactly 2 condition control rows and the comparison table has 2 single-condition rows
3. Click the "Add condition" button (`data-testid="condition-add"`)
4. Wait ~1 second for the table to refresh

**Expected Result:**
- A 3rd condition control row appears (with its own Factor / Side / Quantile controls, `condition-factor-2`, `condition-side-2`, `condition-quantile-2`)
- The comparison table now shows 3 single-condition rows (between Baseline and Combined)
- The Combined (AND) row's n is ≤ the smallest single-row n, and each single-row n is ≤ the Baseline n
- The "Add condition" button is now **disabled** (greyed, not clickable) because 3 conditions = max

---

### UT-07 — Remove a condition reverts to 2 singles (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `condition-remove-<i>`

**Preconditions:**
- UT-06 performed: 3 condition rows are present

**Steps:**
1. With 3 condition rows present, click the "Remove" button on the 3rd condition row (`data-testid="condition-remove-2"`, aria-label "Remove condition 3")
2. Wait ~1 second for the table to refresh

**Expected Result:**
- The 3rd condition control row disappears; 2 condition rows remain
- The comparison table reverts to 2 single-condition rows + Baseline + Combined
- The "Add condition" button is enabled again
- Both remaining "Remove" buttons are now **disabled** (greyed) because 2 conditions = min

---

### UT-08 — Remove is disabled at the minimum of 2 conditions (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → `condition-remove-0`, `condition-remove-1`

**Preconditions:**
- Combination section visible with the default 2 conditions

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the combination section (2 condition rows present)
2. Inspect both "Remove" buttons (`condition-remove-0` and `condition-remove-1`)
3. Attempt to click "Remove" on the first condition row

**Expected Result:**
- Both "Remove" buttons appear greyed/dimmed (opacity ~50%, cursor "not-allowed")
- Clicking does nothing — both condition rows remain; the table still shows 2 single rows
- No 1-condition state can ever be reached from the UI

---

### UT-09 — Add is disabled at the maximum of 3 conditions (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → `condition-add`

**Preconditions:**
- 3 condition rows present (perform UT-06 first)

**Steps:**
1. With 3 condition rows present, inspect the "Add condition" button (`data-testid="condition-add"`)
2. Attempt to click it

**Expected Result:**
- The "Add condition" button appears greyed/dimmed (opacity ~50%, cursor "not-allowed")
- Clicking does nothing — no 4th condition row appears; the table still shows 3 single rows

---

### UT-10 — Thin combined cohort shows honest NA + n (error / honesty)

**Type:** error
**Priority:** P1
**Surface:** `/research` → Combined (AND) row cells in `combination-table`

**Preconditions:**
- Combination section visible

**Steps:**
1. Navigate to `http://localhost:3835/research` and scroll to the combination section
2. Set condition 1 to a factor at "Top" of a narrow quantile (e.g. "Tertile" or "Quartile") using `condition-factor-0` / `condition-side-0` / `condition-quantile-0`
3. Set condition 2 to the **same factor** (or a strongly correlated one) at the **opposing** side "Bottom" of the same narrow quantile using `condition-factor-1` / `condition-side-1` / `condition-quantile-1`
4. Wait ~1 second for the table to refresh and read the Combined (AND) row

**Expected Result:**
- The Combined (AND) row's "n" chip shows a small honest number (e.g. 0 or a value below the configured minimum)
- The Combined (AND) row's Mean / Median / Hit-rate / Risk-adjusted cells display "NA" (muted text) — **not** a fabricated number such as 0.00% or +0.00
- Hovering an NA cell shows a tooltip like "Low sample — n below the … minimum; NA, not a fabricated number" or "No observations"

---

### UT-11 — Empty pool shows the honest empty-state message (error / honesty)

**Type:** error
**Priority:** P2
**Surface:** `/research` → combination section empty state

**Preconditions:**
- Combination section visible; a horizon with no forward-tested observations is reachable (e.g. the longest horizon that exceeds available stored returns)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the top-right "Horizon" segmented control (`data-testid="horizon-select"`), click the longest available horizon button (e.g. the highest "Nd")
3. Scroll to the combination section and observe its body

**Expected Result:**
- If `pool_n` is 0 for that horizon, the combination section shows the empty-state message titled "No forward-tested observations for these conditions / horizon" with the explanation about picking a shorter horizon or different factors
- No comparison table with fabricated rows is shown
- (If the longest horizon still has data, this NA path may not trigger — note it as "not reproducible with current seed" rather than a failure)

---

### UT-12 — Backend unavailable shows an honest error card (error)

**Type:** error
**Priority:** P2
**Surface:** `/research` → combination section error card

**Preconditions:**
- Frontend running at http://localhost:3835; backend **stopped** (or reachable but returning 5xx)

**Steps:**
1. Stop the backend (or simulate it being down)
2. Navigate to `http://localhost:3835/research`
3. Scroll to the "Multi-factor combination cohort" section

**Expected Result:**
- Inside the combination section, a red-bordered card appears with the heading "Backend unavailable" and the text "The combination cohorts could not load from the API. No figures are shown rather than fabricated values — confirm the backend is running and adjust a condition to retry."
- No table with fabricated numbers is shown
- (Restart the backend afterward to restore other tests)

---

### UT-13 — Shared horizon selector re-points the combination table (regression / integration)

**Type:** regression
**Priority:** P1
**Surface:** `/research` → `horizon-select` + `combination-table`

**Preconditions:**
- `/research` loaded with data; at least two horizons available in the Horizon control

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Note the Combined (AND) row's "Mean fwd return" value in the combination table, and the Decile table's values
3. In the top-right "Horizon" control (`data-testid="horizon-select"`), click a different horizon button than the active one (e.g. switch from "20d" to a different "Nd")
4. Wait ~1 second for all tables to refresh

**Expected Result:**
- The Decile sort table, the Rank-IC card, the regime-effectiveness table, **and** the combination table all re-fetch for the new horizon
- The combination table's values update to reflect the new horizon (or show NA/empty honestly if that horizon lacks data)
- The two condition rows and their selections are preserved across the horizon change

---

### UT-14 — Existing Factor Lab (decile + rank-IC) still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research` → `factor-select`, Decile table, Rank-IC card

**Preconditions:**
- `/research` loaded with data

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Confirm the "Decile sort — raw & downside risk-adjusted" table renders with rows D1…D10 and columns Decile / Factor range / Mean fwd return / Risk-adjusted (downside)
3. Confirm the "Rank-IC" card renders a value (`data-testid="rank-ic-value"`)
4. In the top-right "Factor" dropdown (`data-testid="factor-select"`), select a different factor
5. Wait ~1 second

**Expected Result:**
- The decile table and rank-IC value re-point to the newly selected factor (values change)
- The "Factor effectiveness by market regime" table (`data-testid="regime-effectiveness-table"`) still renders with its 7 columns
- No regression: all three pre-existing sections remain functional after the new combination section was added

---

### UT-15 — Global as-of date toggle leaves `/research` byte-identical (regression / J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/research` + global as-of date control

**Preconditions:**
- `/research` loaded; the global as-of date control is reachable (in the app shell/header)

**Steps:**
1. Navigate to `http://localhost:3835/research` and let all tables load
2. Note the values in the decile table, rank-IC, regime table, and the combination table (Combined row n + Mean)
3. Change the global as-of date control to a historical date
4. Wait ~1 second and re-read all four tables

**Expected Result:**
- All four tables — decile, rank-IC, regime-effectiveness, and combination — are **byte-identical** before and after the as-of change
- The combination section adds no date state: toggling the as-of date triggers **zero** `as_of`-parameterised requests for `/api/research/factor-combination` (verify in the browser Network panel — no request carries an `as_of` query param)
- If any of the four tables change values on as-of toggle, that is a J-18 regression failure

---

### UT-16 — Combination section is discoverable on the Factor Lab (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research`

**Preconditions:**
- `/research` loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down the page as a new user would

**Expected Result:**
- The "Multi-factor combination cohort" Card section is reachable by scrolling below the regime-effectiveness table (no hidden tab, no extra navigation)
- The section's panel hint clearly explains the purpose: "Combine 2–3 factor conditions … does combining factors beat either alone?"
- Column headers and condition control labels (Factor / Side / Quantile) are self-explanatory
- The downside-deviation scope note and the J-29 honest-limitation note are visible under the table

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page + combination section load | smoke | P1 | `/research` |
| UT-02 | Default Baseline + 2 singles + Combined render | happy-path | P1 | `combination-table` |
| UT-03 | Change factor re-points table | happy-path | P1 | `condition-factor-0` |
| UT-04 | Toggle side updates cohort | happy-path | P2 | `condition-side-0` |
| UT-05 | Change quantile grows/shrinks n | happy-path | P2 | `condition-quantile-0` |
| UT-06 | Add 3rd condition | happy-path | P1 | `condition-add` |
| UT-07 | Remove condition reverts to 2 | happy-path | P1 | `condition-remove-2` |
| UT-08 | Remove disabled at min (2) | validation | P2 | `condition-remove-*` |
| UT-09 | Add disabled at max (3) | validation | P2 | `condition-add` |
| UT-10 | Thin combined cohort → NA + n | error | P1 | Combined row |
| UT-11 | Empty pool → honest empty state | error | P2 | combination section |
| UT-12 | Backend down → honest error card | error | P2 | combination section |
| UT-13 | Horizon re-points combination table | regression | P1 | `horizon-select` |
| UT-14 | Decile/Rank-IC/regime still work | regression | P1 | `factor-select` |
| UT-15 | As-of toggle byte-identical (J-18) | regression | P1 | global as-of |
| UT-16 | Section discoverable | ux | P3 | `/research` |

**P1 tests (UT-01, 02, 03, 06, 07, 10, 13, 14, 15) must all pass for the browser QA verdict to be PASS.**
