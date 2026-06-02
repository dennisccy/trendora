# Phase goal-i_can_see_the_wealthy_future_forever-iter-11 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

This iteration adds one new panel to the existing Factor Lab page (`/research`): a
**"Factor effectiveness by market regime"** table (`data-testid="regime-effectiveness-table"`)
rendered below the existing decile table + rank-IC card. It is purely additive — no new route, no
new control, no navigation change. All re-point behaviour reuses the existing Factor and Horizon
selectors. These UI tests cover the new table, its NA cells, and the regression surfaces it touches.

Reference identifiers (from `apps/frontend/app/research/page.tsx`):
- Sidebar link: **"Research"** → `/research`
- Page heading: **"Research — Factor Lab"**
- Factor selector: dropdown with `data-testid="factor-select"` / aria-label "Factor"
- Horizon selector: button group `data-testid="horizon-select"`, buttons labelled `1d 5d 10d 20d 60d` (active button has `aria-pressed="true"`)
- Regime table: `data-testid="regime-effectiveness-table"`, panel title "Factor effectiveness by market regime"
- Regime table columns (in order): **Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top − bottom) · Risk-adjusted spread**
- Configured regime labels (6, in order): **Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off**
- Sample-size chip renders `n=<count>` (with ` ⚠` appended when `n < 30`)
- NA cell renders the muted literal text **"NA"**
- Global as-of switcher (top bar): aria-label "View as-of date", indicator badge `data-testid="asof-indicator"` ("Latest" / "Viewing as-of … (historical)")
- `min_sample = 30`

---

## Test Cases

---

### UT-01 — Research page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running at http://localhost:8000 (Factor Lab data available)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the loading skeleton to disappear and the page to fully render

**Expected Result:**
- Page renders without a blank screen or error card
- The heading **"Research — Factor Lab"** is visible at the top
- The amber caveat banner "Survivorship bias · universe-relative · descriptive" is visible
- The "Factor" dropdown and the Horizon button group (`1d 5d 10d 20d 60d`) are visible in the top-right
- No browser console errors

---

### UT-02 — Regime effectiveness table renders with all 6 regimes and 7 columns (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research` → `regime-effectiveness-table`

**Preconditions:**
- UT-01 passed (page loaded with data)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll down below the "Decile sort — raw & downside risk-adjusted" table and the "Rank-IC" card
3. Locate the panel titled **"Factor effectiveness by market regime"** (table `data-testid="regime-effectiveness-table"`)

**Expected Result:**
- A table titled "Factor effectiveness by market regime" is present below the decile/rank-IC grid
- The header row shows exactly these 7 columns left-to-right: **Regime, n, Rank-IC, Top-decile mean, Bottom-decile mean, Spread (top − bottom), Risk-adjusted spread**
- Exactly 6 body rows are present, with the Regime column reading top-to-bottom: **Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off** (in that order)
- Every row's `n` column shows a sample-size chip in the form `n=<number>` (a number, possibly `n=0`)

---

### UT-03 — A high-sample regime shows numeric rank-IC and spread (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `regime-effectiveness-table`

**Preconditions:**
- Page loaded at `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the Horizon button group, click the **"5d"** button (short horizon → more observations clear `min_sample`)
3. Wait for the tables to re-point
4. In the regime table, find a row whose `n` chip shows a count ≥ 30 with no ` ⚠` flag (e.g. **Risk-on**)

**Expected Result:**
- At least one regime row has an `n` chip ≥ 30 (rendered in the faint colour, no ` ⚠`)
- That same row's **Rank-IC** cell shows a signed numeric value (e.g. `+0.12` or `-0.08`), not the text "NA"
- That same row's **Top-decile mean** and **Bottom-decile mean** cells show signed percentages (e.g. `+1.34%`), not "NA"
- That same row's **Spread (top − bottom)** cell shows a signed percentage, not "NA"

---

### UT-04 — Low-sample regime renders honest "NA" with the true n (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → `RegimeCell` NA path

**Preconditions:**
- Page loaded at `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the Horizon button group, click the **"60d"** button (long horizon → fewer observations, more low-sample regimes)
3. Wait for the regime table to re-point
4. Find a regime row whose `n` chip shows a count below 30 (it will carry a ` ⚠` flag), e.g. **Strong risk-on** or **Defensive**

**Expected Result:**
- For that low-sample row, the **Rank-IC**, **Spread (top − bottom)**, and **Risk-adjusted spread** cells render the muted literal text **"NA"** — not blank, not `0`, not `—`
- The row's `n` column still shows the honest count (e.g. `n=7 ⚠`), including `n=0` if the regime has no observations
- Hovering an "NA" cell shows the tooltip "Low sample — n below the minimum; NA, not a fabricated number"

---

### UT-05 — Risk-adjusted spread shows NA while raw spread is numeric (validation / downside-only honesty)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → Risk-adjusted spread column

**Preconditions:**
- Page loaded at `/research`; a regime whose top decile has no downside exists for some (factor, horizon)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Step through the Factor dropdown options and the `1d`/`5d` horizons, scanning the regime table after each change
3. Look for any regime row where the **Spread (top − bottom)** cell shows a numeric percentage but the **Risk-adjusted spread** cell shows "NA"

**Expected Result:**
- It is possible to observe a row where raw **Spread** is numeric (e.g. `+2.10%`) while **Risk-adjusted spread** is "NA"
- The risk-adjusted value is never a total-volatility number masquerading as downside-adjusted — when there is no downside, the cell honestly reads "NA"
- (If no such row appears across the swept combinations, record this as "not reachable in current data" — not a failure, since it is data-dependent.)

---

### UT-06 — Regime table re-points when the Factor changes (happy path / changed behaviour)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → Factor selector → `regime-effectiveness-table`

**Preconditions:**
- Page loaded at `/research`; the Factor dropdown has ≥ 2 options

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Note the current Factor dropdown value and record the regime table's Rank-IC + Spread values for the **Risk-on** row (read the visible DOM text)
3. Open the **"Factor"** dropdown and select a different factor (e.g. switch from "Leadership score" to "Risk score")
4. Wait for the tables to re-point
5. (If watching the network tab) confirm a `GET /api/research/factor-lab?factor=<new>&horizon=…` request fires

**Expected Result:**
- A new `factor-lab` request is issued with the newly selected `factor` query param
- The regime table's Rank-IC and/or Spread values for at least one regime row change from the values recorded in step 2
- The decile table and rank-IC card above also update (they re-point together)
- No error card appears

---

### UT-07 — Regime table re-points and n chips update when the Horizon changes (happy path / changed behaviour)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → Horizon selector → `regime-effectiveness-table`

**Preconditions:**
- Page loaded at `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Click the **"5d"** Horizon button; record the `n` chips and Spread values across the 6 regime rows
3. Click the **"60d"** Horizon button
4. Wait for the regime table to re-point
5. (If watching the network tab) confirm a `GET /api/research/factor-lab?...&horizon=60` request fires

**Expected Result:**
- A new `factor-lab` request is issued with `horizon=60`
- The clicked Horizon button becomes active (`aria-pressed="true"`, accent background)
- The regime rows' `n` chips change (generally smaller counts at 60d → more ` ⚠` low-sample flags) and Spread/Rank-IC values update versus the 5d snapshot
- The new regime table values are consistent with the simultaneously updated decile table

---

### UT-08 — As-of switcher does NOT affect the Factor Lab (regression — J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/research` vs. global top-bar as-of switcher

**Preconditions:**
- Page loaded at `/research`; the as-of switcher (top bar, label "View as-of date") has ≥ 1 historical date option besides "Latest"

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Record the full Factor Lab state: the decile table, the Rank-IC value (`data-testid="rank-ic-value"`), and all 6 regime rows of the regime table (visible DOM text)
3. In the top bar, open the **"View as-of date"** dropdown and select a historical date (not "Latest")
4. Confirm the top-bar badge changes to "Viewing as-of … (historical)"
5. Re-read the decile table, Rank-IC value, and regime table

**Expected Result:**
- The decile table, Rank-IC card, AND the regime table are **identical** before and after the as-of change (same numbers, same NA cells, same `n` chips)
- (If watching the network tab) **zero** requests from `/research` carry an `as_of` query param
- J-18 preserved: `/research` is a cross-date aggregate and ignores the global as-of date

---

### UT-09 — Existing decile table + rank-IC card still render and re-point (regression — J-25)

**Type:** regression
**Priority:** P1
**Surface:** `/research` → decile table + rank-IC card

**Preconditions:**
- Page loaded at `/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Confirm the **"Decile sort — raw & downside risk-adjusted"** table renders with rows D1…D10 and columns Decile / Factor range / Mean fwd return / Risk-adjusted (downside)
3. Confirm the **"Rank-IC"** card renders with a large numeric value or "NA" (`data-testid="rank-ic-value"`)
4. Change the Factor dropdown to a different factor
5. Confirm the decile table values and the Rank-IC value both change

**Expected Result:**
- The decile table and rank-IC card are present and unchanged in structure (the new regime panel did not displace or break them)
- Both re-point on factor change alongside the new regime table
- No layout overlap, no console errors

---

### UT-10 — Empty state: no regime table fabricated when there are no observations (regression / error)

**Type:** error
**Priority:** P2
**Surface:** `/research` empty-state gate

**Preconditions:**
- A (factor, horizon) combination with `n_total === 0` is reachable (e.g. a horizon with no realized forward returns for the chosen factor). If none is reachable in current data, mark N/A.

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Select a Factor + Horizon combination known to have no forward-tested observations (try the longest horizon `60d` with each factor)
3. Observe the area below the caveat banner

**Expected Result:**
- The empty-state panel appears: heading **"No forward-tested observations for this factor / horizon"** with the Microscope icon
- The regime effectiveness table is **absent** (not rendered with fabricated rows)
- The decile table and rank-IC card are also absent (the whole Factor Lab is gated behind `n_total > 0`)
- No error card; no crash

---

### UT-11 — Backend-down error card; no fabricated regime numbers (error)

**Type:** error
**Priority:** P2
**Surface:** `/research` error card

**Preconditions:**
- Ability to stop the backend (or it is already unreachable on :8000)

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3835/research`
2. Wait for the loading skeleton to resolve

**Expected Result:**
- A red error card appears with **"Backend unavailable"** and the text "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values."
- Neither the decile table, the rank-IC card, NOR the regime effectiveness table renders any numbers
- No "NA" rows are fabricated; the page does not crash to a blank screen

---

### UT-12 — Regime table is discoverable and self-explaining (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research` → regime panel hint text

**Preconditions:**
- Page loaded at `/research` with data

**Steps:**
1. From `http://localhost:3835` (dashboard), click **"Research"** in the left sidebar
2. Confirm the page lands on `/research` with heading "Research — Factor Lab"
3. Scroll to the "Factor effectiveness by market regime" panel and read its sub-title hint

**Expected Result:**
- The Research page is reachable in one click from the sidebar
- The regime panel's hint text explains its purpose, e.g. "Does this factor still sort N-day forward returns WITHIN each market regime?" and states "regimes with n < 30 show NA + n, never a fabricated number"
- A new user can understand what the table shows without developer knowledge; the NA + n convention is documented in the hint

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research page loads | smoke | P1 | `/research` |
| UT-02 | Regime table renders (6 rows, 7 cols) | smoke | P1 | `regime-effectiveness-table` |
| UT-03 | High-sample regime numeric | happy-path | P1 | regime table |
| UT-04 | Low-sample regime NA + n | validation | P2 | RegimeCell NA |
| UT-05 | Risk-adjusted NA vs numeric spread | validation | P2 | risk-adjusted column |
| UT-06 | Re-point on factor change | happy-path | P1 | factor selector |
| UT-07 | Re-point on horizon change | happy-path | P1 | horizon selector |
| UT-08 | As-of switcher no effect (J-18) | regression | P1 | as-of vs lab |
| UT-09 | Decile + rank-IC still work (J-25) | regression | P1 | decile/rank-IC |
| UT-10 | Empty state, no fabricated table | error | P2 | empty-state gate |
| UT-11 | Backend-down error card | error | P2 | error card |
| UT-12 | Discoverable + self-explaining | ux | P3 | sidebar/hint |

**P1 tests (UT-01, UT-02, UT-03, UT-06, UT-07, UT-08, UT-09) must all pass for browser QA verdict to be PASS.**
