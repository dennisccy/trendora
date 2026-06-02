# Phase goal-i_can_see_the_wealthy_future_forever-iter-14 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

This phase adds **one new section** to the existing `/research` page: the **"Setup & Pattern Lab — event study"** (rendered below the Factor Lab and the Multi-factor Combination Lab). No new page, route, nav entry, or date control was added. All UI tests below operate on `/research`.

Key facts for testers (from the user-visible-changes report):
- The **default** subject on first load is **Actionable**, a rare setup with only ~2 occurrences in this seed — it honestly renders **NA + n=2**, NOT a bug.
- To see fully populated numbers, select a data-rich subject: **Breakout-watch** (Setups) or **Pullback to a rising DMA** (Patterns).
- The section reuses the page's shared **Horizon** button group; it has **no** date control of its own.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Research page loads with the new event-study section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running (default; reachable from the frontend)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load
3. Scroll to the bottom of the page, below the "Research — Factor Lab" heading, below the Factor Lab table and below the Multi-factor Combination Lab section

**Expected Result:**
- The page renders without a blank screen or error page
- A panel titled "Setup & Pattern Lab — event study" is visible (DOM element `data-testid="event-study-section"`)
- Inside that panel a "Subject" dropdown, a "Per-horizon distribution & exit-horizon curve" table, a "By market regime" panel, and a "By sector" panel are visible
- No uncaught console errors

---

### UT-02 — Data-rich SETUP subject renders the full per-horizon table (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → event-study section

**Preconditions:**
- UT-01 passed; the event-study section is visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Setup & Pattern Lab — event study" section
3. In the "Subject" dropdown, select **"Breakout-watch"** (under the "Setups" group)
4. Read the "Per-horizon distribution & exit-horizon curve" table (`data-testid="event-study-horizon-table"`)

**Expected Result:**
- The table shows one row per forward horizon (e.g. 5d, 10d, 20d, 60d), each labelled "<N>d" in the Horizon column
- The columns are, in order: Horizon, n, Mean, Median, % Positive, Dispersion, Expectancy, Mean MAE, Mean MFE, Return / downside-dev, Return / MAE
- For Breakout-watch, the populated horizon rows show real numbers (percentages and ratios), NOT the literal text "NA"
- The "Subject:" meta line above the table reads "Breakout-watch (setup)" and shows a "Pooled occurrences (<H>d): <number>" count

---

### UT-03 — Best exit-horizon is highlighted exactly once (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → event-study horizon table

**Preconditions:**
- UT-02 done; **Breakout-watch** is selected

**Steps:**
1. With "Breakout-watch" selected, scan the "Per-horizon distribution & exit-horizon curve" table
2. Look in the Horizon column for a "best exit" badge
3. Read the "Best exit-horizon:" value in the meta line above the table

**Expected Result:**
- Exactly one horizon row carries a "best exit" badge (an accent-bordered pill reading "best exit") and that row has a slightly shaded background
- The badged row's horizon matches the "Best exit-horizon: <N>d" value in the meta line
- The badged row is NOT one of the NA / low-sample rows (it is a populated, non-NA row)

---

### UT-04 — Subject selector is config-driven with grouped Setups / Patterns (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → Subject selector (`data-testid="subject-select"`)

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the event-study section
3. Open the "Subject" dropdown and read all options and their group labels

**Expected Result:**
- The dropdown contains two option groups: "Setups" and "Patterns"
- The "Setups" group lists all six setups: Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist
- The "Patterns" group lists: VCP, Pullback to a rising DMA, Flat-base
- No "Loading…" placeholder remains once the page has loaded

---

### UT-05 — PATTERN subject re-points the study to distinct values (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → event-study section

**Preconditions:**
- UT-02 done (Breakout-watch values observed)

**Steps:**
1. In the "Subject" dropdown, select **"Pullback to a rising DMA"** (under the "Patterns" group)
2. Read the per-horizon table and the meta line

**Expected Result:**
- The "Subject:" meta line now reads "Pullback to a rising DMA (pattern)"
- The per-horizon table values change versus the Breakout-watch capture (distinct means / ns) — the study re-pointed to the new subject
- The By market regime and By sector panels also update for this subject

---

### UT-06 — Low-sample subject renders honest NA + n, not fabricated numbers (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → event-study horizon table

**Preconditions:**
- Event-study section visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the event-study section
3. In the "Subject" dropdown, select **"Actionable"** (the default low-sample setup) — or **"VCP"**
4. Read the per-horizon table rows

**Expected Result:**
- The low-sample horizon rows render the literal text "NA" in the Mean / Median / % Positive / Dispersion / Expectancy / Mean MAE / Mean MFE / ratio cells — never a fabricated percentage
- The "n" column still shows the honest sample size (e.g. n=2 for Actionable) with a low-sample warning chip
- The meta line notes "Rows with n < <min> ⚠ render NA."

---

### UT-07 — Zero-occurrence subject shows the honest empty state (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → event-study section empty state

**Preconditions:**
- Event-study section visible

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the event-study section
3. Cycle the "Subject" dropdown through each option until one has zero forward-tested occurrences across all horizons (try **"Risk-off-watchlist"**, **"Extended"**, or **"Avoid"**)

**Expected Result:**
- For a subject with zero occurrences at every horizon, the section shows an empty-state card titled "No forward-tested occurrences for this subject" with the description "No stored snapshot has this setup/pattern with a realized forward return yet..."
- No fabricated distribution table is rendered for that subject
- (If every selectable subject has at least one occurrence in this seed, mark this case "not reproducible with current data" — that is acceptable.)

---

### UT-08 — By-regime panel emits a row per configured regime with ≥1 NA cell (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → `data-testid="event-study-regime-table"`

**Preconditions:**
- A data-rich subject (Breakout-watch) selected

**Steps:**
1. With "Breakout-watch" selected, read the "By market regime (<H>d)" panel
2. Count the rows and inspect each cell

**Expected Result:**
- The panel title reads "By market regime (<H>d)" where `<H>` is the currently selected horizon
- Columns are: Regime, n, Mean, Hit-rate, Risk-adjusted (downside)
- One row appears per configured regime label
- At least one empty / low-sample regime row shows "NA" in Mean / Hit-rate / Risk-adjusted with n=0 (or a low n + warning chip) — no fabricated number for an empty regime

---

### UT-09 — By-sector panel shows only sectors with members (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/research` → `data-testid="event-study-sector-table"`

**Preconditions:**
- "Pullback to a rising DMA" (or "Breakout-watch") selected

**Steps:**
1. Read the "By sector (<H>d)" panel
2. Inspect the rows and cells

**Expected Result:**
- The panel title reads "By sector (<H>d)" matching the selected horizon
- Columns are: Sector, n, Mean, Risk-adjusted (downside)
- Only sectors that actually have occurrences appear (no padded empty sector rows)
- A low-sample sector (if present) shows "NA" with its n chip
- If no sector has an occurrence, the panel shows the note "No sector has an occurrence of this subject at this horizon." instead of an empty table

---

### UT-10 — Caveat banner renders inside the event-study section (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/research` → CaveatBanner inside event-study section

**Preconditions:**
- Event-study section visible with data loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Scroll to the "Setup & Pattern Lab — event study" section
3. Read the caveat text directly below the Subject selector row

**Expected Result:**
- A caveat banner is shown within the section carrying both a survivorship-bias caveat and a descriptive ("not predictive") caveat
- A note is visible: "Re-uses the page's shared horizon selector above. No date control — a cross-date aggregate over every stored snapshot (J-18)."

---

### UT-11 — Shared Horizon selector re-points the by-regime / by-sector panels (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → shared HorizonSelector (`data-testid="horizon-select"`)

**Preconditions:**
- "Breakout-watch" selected; note the current "By market regime (Xd)" and "By sector (Xd)" titles and values

**Steps:**
1. At the top-right of the page, in the "Horizon" button group, click a different horizon button (e.g. if "20d" is active, click "60d")
2. Re-read the event-study section

**Expected Result:**
- The "By market regime (<H>d)" and "By sector (<H>d)" panel titles update to the newly selected horizon
- The per-horizon table's "best exit" highlight and the meta line's "Pooled occurrences (<H>d)" update for the chosen horizon
- The event study uses the SAME horizon control as the Factor Lab — there is no second horizon/date control inside the section

---

### UT-12 — Backend-unavailable error state shows an honest message, not a blank table (error)

**Type:** error
**Priority:** P2
**Surface:** `/research` → event-study error block

**Preconditions:**
- Ability to stop the backend (or block the `/api/research/event-study` request)

**Steps:**
1. Stop the backend service
2. Navigate to `http://localhost:3835/research`
3. Scroll to the "Setup & Pattern Lab — event study" section

**Expected Result:**
- The section shows a red-bordered error block titled "Backend unavailable" with the text "The event study could not load from the API. No figures are shown rather than fabricated values..."
- No fabricated or blank distribution table is rendered
- (Restart the backend afterward and reload to restore normal state.)

---

### UT-13 — As-of toggle leaves the event study byte-identical (regression, J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/research` → event-study section under the global as-of switcher

**Preconditions:**
- App running; at least one historical run date exists in the as-of switcher
- "Breakout-watch" selected so the tables are populated

**Steps:**
1. Navigate to `http://localhost:3835/research`, select "Breakout-watch", and note the per-horizon / by-regime / by-sector values
2. In the top bar, open the "View as-of date" dropdown and select a historical date (any option other than "Latest")
3. Confirm the amber "Viewing as-of <date> (historical)" badge appears
4. Re-read the event-study tables

**Expected Result:**
- The event-study per-horizon, by-regime, and by-sector tables are unchanged (identical values) before and after toggling the as-of date
- The event study is a cross-date aggregate and does NOT time-travel with the as-of control
- (Network-level check, optional: no request to `/api/research/event-study` carries an `as_of` query param.)

---

### UT-14 — Factor Lab and Combination Lab still render after the new section (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research` → Factor Lab + Multi-factor Combination Lab

**Preconditions:**
- App running

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Confirm the "Research — Factor Lab" heading and its decile table render at the top
3. In the top-right "Factor" dropdown, select a different factor and confirm the Factor Lab table re-points
4. Scroll to the Multi-factor Combination Lab section and confirm it renders its cohort table

**Expected Result:**
- The Factor Lab table renders and re-points when the factor changes
- The Multi-factor Combination Lab section renders below it without error
- The new event-study section appears below both — page order: Factor Lab → Combination Lab → Setup & Pattern Lab
- No layout break or error introduced by the added third section

---

### UT-15 — Research feature is discoverable from the sidebar (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Steps:**
1. Navigate to `http://localhost:3835`
2. Look at the left sidebar navigation

**Expected Result:**
- A "Research" link (with a microscope icon) is visible in the sidebar
- Clicking it navigates to `http://localhost:3835/research`
- The event study lives within the already-discoverable Research page; no separate nav entry is expected for it (additive section, by design)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Research page loads with event-study section | smoke | P1 | `/research` |
| UT-02 | SETUP subject renders full per-horizon table | happy-path | P1 | `/research` |
| UT-03 | Best exit-horizon highlighted once | happy-path | P1 | `/research` |
| UT-04 | Subject selector grouped Setups/Patterns | happy-path | P1 | `/research` |
| UT-05 | PATTERN subject re-points to distinct values | happy-path | P1 | `/research` |
| UT-06 | Low-sample subject → NA + n | validation | P2 | `/research` |
| UT-07 | Zero-occurrence subject → empty state | validation | P2 | `/research` |
| UT-08 | By-regime panel: row per regime, ≥1 NA | validation | P2 | `/research` |
| UT-09 | By-sector panel: members-only | validation | P2 | `/research` |
| UT-10 | Caveat banner inside section | ux | P2 | `/research` |
| UT-11 | Shared Horizon re-points panels | happy-path | P1 | `/research` |
| UT-12 | Backend-unavailable error state | error | P2 | `/research` |
| UT-13 | As-of toggle leaves study byte-identical (J-18) | regression | P1 | `/research` |
| UT-14 | Factor + Combination labs still render | regression | P1 | `/research` |
| UT-15 | Research discoverable from sidebar | ux | P3 | nav |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-11, UT-13, UT-14) must all pass for browser QA verdict to be PASS.**
