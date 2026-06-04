# Phase goal-i_can_see_the_wealthy_future_forever-iter-18 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

This iteration changed exactly one page (`/research`) and one section within it
("Multi-factor combination cohort"). All test cases below target that section unless
stated otherwise. The single-factor Factor Lab, the Setup & Pattern Lab, and other
pages are only covered as regression checks.

Key elements and their selectors (for reference — testers can also locate by visible text):

| Element | Visible text / location | `data-testid` |
|---------|------------------------|---------------|
| Combination section | Panel titled "Multi-factor combination cohort" | `combination-section` |
| Comparison table | inside the section | `combination-table` |
| Baseline row | "Baseline (all names)" (label may vary) | `combination-row-baseline` |
| Combined composite row | "Combined (composite rank-blend)" — highlighted/bold | `combination-row-composite` |
| Strict overlap row | "Strict overlap (AND)" — muted | `combination-row-strict_overlap` |
| Add condition button | "Add condition" (+ icon) | `condition-add` |
| Remove condition button | "Remove" (× icon) per condition row | `condition-remove-<idx>` |
| Factor select (per row) | "Factor" labelled dropdown | `condition-factor-<idx>` |
| Side toggle (per row) | "Top" / "Bottom" segmented buttons | `condition-side-<idx>` |
| Quantile select (per row) | "Quantile" labelled dropdown | `condition-quantile-<idx>` |
| Horizon selector | "21d / 63d / …" segmented buttons (shared) | `horizon-select` |

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Research page loads with the combination section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend is running at http://localhost:3835
- Backend is running (so the Factor Lab payload resolves)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (skeletons disappear)
3. Scroll down to the panel titled "Multi-factor combination cohort"

**Expected Result:**
- The page heading "Research — Factor Lab" is visible at the top
- A panel titled "Multi-factor combination cohort" is visible
- Inside it, a comparison table (`combination-table`) with column headers **Cohort**, **n**, **Mean fwd return**, **Median**, **Hit-rate**, **Risk-adjusted (downside)** is rendered
- No "Backend unavailable" error card appears inside the section
- No blank screen and no browser console errors

---

### UT-02 — Combined (composite rank-blend) row is populated, not NA (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `combination-row-composite`

**Preconditions:**
- UT-01 passed (combination section rendered)
- Default condition selection is loaded (the section auto-loads server defaults)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Multi-factor combination cohort" table
3. Locate the row labelled "Combined (composite rank-blend)" (the highlighted/bold row, `combination-row-composite`)
4. Read its **n**, **Mean fwd return**, **Median**, **Hit-rate**, and **Risk-adjusted (downside)** cells

**Expected Result:**
- The composite row's **n** chip shows a number ≥ 30 (not 0)
- The **Mean fwd return**, **Median**, **Hit-rate**, and **Risk-adjusted (downside)** cells all show numeric values (e.g. "+1.23%", "0.54", "+0.31") — **none shows the literal text "NA"**
- The composite row's values are **not identical** to the "Baseline (all names)" row's values (the blend selects a sub-cohort, so figures differ)
- The composite row is visually emphasized (shaded background + bold label) relative to the single-factor rows

---

### UT-03 — Strict overlap (AND) row renders as a secondary row below the composite (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `combination-row-strict_overlap`

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Multi-factor combination cohort" table
3. Locate the row labelled "Strict overlap (AND)" (`combination-row-strict_overlap`)
4. Confirm its vertical position relative to the "Combined (composite rank-blend)" row
5. Read its **n** chip and its **Mean fwd return** / **Risk-adjusted (downside)** cells

**Expected Result:**
- A row labelled "Strict overlap (AND)" is present and appears **directly below** the "Combined (composite rank-blend)" row
- The strict-overlap row is styled as a muted/secondary row (label not bold, no highlight) — visually de-emphasized vs the composite row
- Its cells show **either** numeric values **or** the literal "NA" together with an **n** chip — they must never show a numeric figure with n = 0, and must never be blank

---

### UT-04 — Comparison table row order is correct (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `combination-table`

**Preconditions:**
- UT-01 passed
- Default selection has at least 2 single-factor conditions loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Multi-factor combination cohort" table
3. Read the **Cohort** column top-to-bottom and note the order of rows

**Expected Result:**
Rows appear in this exact top-to-bottom order:
1. **Baseline (all names)** (header-style row)
2. One row per **single-factor** condition (e.g. "Relative strength vs SPY (3m) · top Quintile (20%)")
3. **Combined (composite rank-blend)** — the emphasized/highlighted row
4. **Strict overlap (AND)** — the muted secondary row (last row)

- There is exactly **one** "Combined (composite rank-blend)" row and exactly **one** "Strict overlap (AND)" row
- There is **no** legacy single row simply labelled "Combined (AND)"

---

### UT-05 — Section hint describes the composite blend correctly (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research` — `combination-section` panel hint

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Multi-factor combination cohort" panel
3. Read the small grey hint text directly under the panel title

**Expected Result:**
The hint text contains all of:
- The phrase "Combined (composite rank-blend)"
- A composite quantile label (e.g. "Quintile (20%)", "Decile (10%)", or similar — a quantile name with a percentage)
- A weighting scheme word (e.g. "equal" — rendered as "…equal-weighted blend…")
- The explicit clarification that the blend is "a transparent ranking of stored values, NOT a fitted/ML model"
- A description of the "Strict overlap (AND)" row as the optional secondary exact intersection (with "NA + n when empty")

---

### UT-06 — Add condition allows up to all 11 catalog factors (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` — `condition-add`

**Preconditions:**
- UT-01 passed
- The catalog has 11 factors (config `max_conditions = 11`)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Multi-factor combination cohort" section
3. Note how many condition rows are present initially (each row has a Factor / Side / Quantile control and a "Remove" button)
4. Click the "Add condition" button repeatedly, once each time, until it can no longer be clicked
5. Count the total number of condition rows present
6. After each addition, glance at the "Combined (composite rank-blend)" row's **n**

**Expected Result:**
- "Add condition" can be clicked until there are **11** condition rows total
- At 11 condition rows, the "Add condition" button becomes **disabled** (greyed out / not clickable) — it does **not** disable at 3 rows
- As conditions are added (3, 4, … up to 11), the "Combined (composite rank-blend)" row continues to show an **n > 0** with numeric figures (it does not collapse to NA when more than 3 factors are selected)

---

### UT-07 — Remove condition works down to the minimum (regression / validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` — `condition-remove-<idx>`

**Preconditions:**
- UT-06 performed (multiple condition rows present), or default rows present

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the "Multi-factor combination cohort" section, add conditions until there are at least 4 rows (click "Add condition")
3. Click the "Remove" button on one condition row
4. Continue clicking "Remove" on rows until the "Remove" buttons become disabled
5. Count the remaining condition rows

**Expected Result:**
- Each "Remove" click removes exactly one condition row and the table re-fetches/updates
- The "Remove" buttons become **disabled** at the minimum number of conditions (2) — you cannot go below 2 conditions
- After each removal the comparison table still renders (Baseline → singles → composite → strict overlap), with no crash or blank section

---

### UT-08 — Empty strict-intersection keeps composite populated while strict overlap shows NA (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` — `combination-row-composite` + `combination-row-strict_overlap`

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the "Multi-factor combination cohort" section, set up a deliberately empty intersection. Easiest reliable method:
   - In condition row 1, set the **Factor** dropdown to any factor and set the **Side** toggle to "Top"
   - In condition row 2, set the **Factor** dropdown to the **same factor** and set the **Side** toggle to "Bottom"
   - (Top and Bottom of the same factor cannot both be true for any name → the strict AND intersection is empty)
3. Read the "Combined (composite rank-blend)" row's **n** and **Mean fwd return**
4. Read the "Strict overlap (AND)" row's **n** and cells

**Expected Result:**
- The "Combined (composite rank-blend)" row stays **populated** — **n > 0** and numeric Mean / Median / Hit-rate / Risk-adjusted values
- The "Strict overlap (AND)" row shows the literal "NA" in its value cells with an **n** chip showing **0** (an honest empty-intersection signal) — it must **not** show a fabricated 0.00% return as if it were a real cohort

---

### UT-09 — Backend error shows an honest message, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/research` — combination section error state

**Preconditions:**
- The frontend is running at http://localhost:3835
- The backend is **stopped** (or unreachable) — operator can stop the backend service, then reload

**Steps:**
1. Stop the backend service
2. Navigate to `http://localhost:3835/research`
3. Scroll to the "Multi-factor combination cohort" section

**Expected Result:**
- Inside the section, a "Backend unavailable" card appears with the text explaining "No figures are shown rather than fabricated values"
- No fabricated numbers and no all-zero table are shown
- The page does not white-screen or throw an uncaught error
- (Restart the backend and reload to return to a working state)

---

### UT-10 — Factor / Side / Quantile selection updates the cohorts (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research` — `condition-factor-0`, `condition-side-0`, `condition-quantile-0`

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the first condition row, note the current single-factor cohort label and its Mean fwd return in the table
3. Change the first condition's **Factor** dropdown to a different factor
4. Wait for the table to update (it briefly dims while re-fetching)
5. Observe the single-factor row label and the composite row figures

**Expected Result:**
- The single-factor cohort row's **label** changes to reflect the newly selected factor (e.g. "<new factor> · top Quintile (20%)")
- The "Combined (composite rank-blend)" row's figures recompute and stay numeric with n > 0
- No "NA" appears for the composite row purely as a result of changing one factor (unless the resulting pool genuinely has n < min_sample, in which case NA + n is acceptable and honest)

---

### UT-11 — Single-factor Factor Lab still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research` — Factor Lab (Decile sort + Rank-IC)

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. At the top, use the "Factor" dropdown to pick a factor
3. Use the "Horizon" segmented buttons to pick a horizon (e.g. click "63d")
4. Observe the "Decile sort — raw & downside risk-adjusted" table and the "Rank-IC" card

**Expected Result:**
- The Decile table renders 10 rows (D1…D10) with Factor range, Mean fwd return, and Risk-adjusted columns
- The Rank-IC card shows a numeric value (or honest "NA")
- Changing the Factor and Horizon updates both panels — confirming this iteration's combination-section changes did not break the existing Factor Lab

---

### UT-12 — Setup & Pattern Lab still works (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/research` — Setup & Pattern Lab event study

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the panel titled "Setup & Pattern Lab — event study"
3. Use the "Subject" dropdown to pick a setup or pattern
4. Observe the "Per-horizon distribution & exit-horizon curve" table

**Expected Result:**
- The event-study panel renders a per-horizon table with numeric figures (or honest NA + n)
- The "View the names expressing this on the leaderboard" link is present
- The panel is unaffected by the combination-section changes — confirms no shared-component regression

---

### UT-13 — No new date/as-of control on /research; global toggle does not alter Factor Lab (regression / anti-goal guard J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/research` — page-level date state

**Preconditions:**
- Backend running
- The app's global as-of date control exists in the shared header/nav (outside `/research`)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Confirm there is **no** date picker or as-of dropdown rendered *inside* the `/research` content (only the "Factor" dropdown, the "Horizon" buttons, the per-condition selects, and the "Subject" dropdown — none of these is a calendar/date control)
3. Read and remember the "Combined (composite rank-blend)" row's figures
4. Without reloading the page, change the **global** as-of control in the app header/nav to a different date
5. Return focus to the "Multi-factor combination cohort" table and compare its figures to step 3

**Expected Result:**
- There is **no** date/as-of input inside the `/research` page body
- Counting `<select>` elements: the only true HTML `<select>` controls on the page are the config-driven ones (Factor, per-condition Factor/Quantile, Subject) — there is **no** date `<select>` belonging to `/research` itself
- After toggling the global as-of date, the "Multi-factor combination cohort" figures are **unchanged / byte-identical** (the combination cohort is a cross-date aggregate and ignores the global as-of date — no `/api/research/*?as_of=` request fires)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research page + combination section loads | smoke | P1 | `/research` |
| UT-02 | Composite row populated (not NA) | happy-path | P1 | `combination-row-composite` |
| UT-03 | Strict overlap row renders as secondary | happy-path | P1 | `combination-row-strict_overlap` |
| UT-04 | Row order correct | happy-path | P1 | `combination-table` |
| UT-05 | Section hint describes composite blend | ux | P2 | `combination-section` |
| UT-06 | Add condition up to 11 factors | happy-path | P1 | `condition-add` |
| UT-07 | Remove condition down to minimum | validation | P2 | `condition-remove-*` |
| UT-08 | Empty intersection → composite populated, strict NA | validation | P2 | composite + strict rows |
| UT-09 | Backend error handled honestly | error | P2 | combination section |
| UT-10 | Factor/Side/Quantile change updates cohorts | happy-path | P2 | `condition-*-0` |
| UT-11 | Single-factor Factor Lab regression | regression | P1 | Factor Lab |
| UT-12 | Setup & Pattern Lab regression | regression | P2 | event study |
| UT-13 | No new date state; J-18 anti-goal guard | regression | P1 | page-level date state |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-06, UT-11, UT-13) must all pass for the browser QA verdict to be PASS.**
