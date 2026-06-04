# Phase goal-i_can_see_the_wealthy_future_forever-iter-17 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Context

This iteration relocates the **forward-tested evidence aggregate** (forward return by bucket / excess /
setup / regime / VCP / pattern + control group) off the now-deleted **System Health** page and onto the
bottom of the **Backtest** page (`/backtest`), where it is **as-of-scoped** (driven by the single global
top-bar date switcher) and **horizon-switchable** (driven by the existing Backtest "Horizon" selector, no
refetch). The "System Health" sidebar link and `/system-health` route were removed.

Exact UI anchors used below (verified against source):
- Global date switcher: top-bar `<select>` labelled `View as-of date` with first option **"Latest · &lt;date&gt;"**
  then descending historical dates. Indicator badge `data-testid="asof-indicator"` reads "Latest" or
  "Viewing as-of &lt;D&gt; (historical)".
- New evidence section: `data-testid="evidence-aggregate"`, heading **"Forward-tested evidence (expanding
  window ≤ &lt;date&gt;)"**.
- Summary line: `data-testid="evidence-summary"` ("Snapshots contributing (≤ D):", "As-of range:",
  "Mean stock fwd return (Nd):", "(n=…)").
- Horizon selector: button group labelled "Horizon" with buttons "1d / 5d / 10d / 20d / 60d"
  (`aria-pressed` toggles); rendered in the Return Attribution header.
- Sidebar: 10 items — Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist,
  Methodology, Data Manager. **No "System Health".**

API-level checks (route 404, `evidence_by_horizon` payload, no-leak, NA semantics) are already covered by
the functional test plan (TC-01…TC-11) and are NOT duplicated here.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Backtest page loads with the new evidence section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend running at http://localhost:3835, backend reachable
- At least one scanner run exists (seed loaded) so the global switcher has dates

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Wait for the page to finish loading (the skeleton pulse cards disappear)
3. Scroll to the very bottom of the page

**Expected Result:**
- Page renders without a blank screen or an "Backend unavailable" error card
- The heading "Backtest" is visible near the top
- A section with `data-testid="evidence-aggregate"` headed **"Forward-tested evidence (expanding window ≤ &lt;some date&gt;)"** is visible at the bottom
- No uncaught console errors

---

### UT-02 — Evidence summary line and seven panels render (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → `EvidenceAggregateSection`

**Preconditions:**
- A scan date with measurable forward returns exists (the default load picks an observed horizon)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Scroll to the "Forward-tested evidence (expanding window ≤ …)" section
3. Read the summary line (`data-testid="evidence-summary"`)
4. Inspect each panel below the summary line

**Expected Result:**
- The summary line shows all of: "Snapshots contributing (≤ &lt;date&gt;): &lt;number&gt;", "As-of range: &lt;date&gt; → &lt;date&gt;", "Mean stock fwd return (&lt;N&gt;d): &lt;pct&gt; (n=&lt;number&gt;)", and the legend "Figures with n &lt; &lt;min&gt; ⚠ are low-sample."
- Panel **"Forward return by score bucket"** shows rows A, B, C, D, E, each with a Mean fwd return value or "—"
- Panel **"Excess vs benchmarks"** shows two rows "Excess vs SPY (SPY)" and "Excess vs QQQ (QQQ)" with Stocks / Benchmark / Excess columns
- Panels **"Forward return by setup type"**, **"by market regime"**, **"VCP vs non-VCP"**, **"Pullback-to-rising-DMA vs not"**, **"Flat-base breakout vs not"** each render either rows with a return + n, or their italic empty label
- A **"Control-group comparison — selection vs sector beta"** table renders at the bottom of the section
- No cell shows a literal `null`, `NaN`, or `undefined`

---

### UT-03 — Evidence re-scopes to an earlier as-of date, sample n shrinks (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` + global date switcher

**Preconditions:**
- At least two run dates exist in the switcher (one "Latest", one earlier historical date)

**Steps:**
1. Navigate to `http://localhost:3835/backtest` and let it load on **Latest**
2. Scroll to the evidence summary line; note the "Snapshots contributing (≤ &lt;date&gt;): &lt;N_latest&gt;" number and the "Mean stock fwd return (…) (n=&lt;n_latest&gt;)" value
3. At the top bar, open the "View as-of date" dropdown and select an **earlier historical date** (not the Latest option)
4. Wait for the page to reload data (skeleton flashes, then results return)
5. Scroll back to the evidence summary line and re-read the "Snapshots contributing" count and the "(n=…)" value

**Expected Result:**
- The top-bar indicator changes to the amber badge "Viewing as-of &lt;D&gt; (historical)"
- The evidence heading now reads "Forward-tested evidence (expanding window ≤ &lt;the earlier D&gt;)"
- The "Snapshots contributing (≤ D)" count is **less than or equal to** N_latest (strictly less when the date is earlier than latest)
- The overall "(n=…)" sample size is **less than or equal to** n_latest
- The displayed numbers differ from the Latest view — the evidence is genuinely re-scoped, not static

---

### UT-04 — Returning to Latest reproduces the full all-history numbers (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` + global date switcher

**Preconditions:**
- Continue from UT-03 (currently on an earlier historical date) OR start fresh and note Latest values first

**Steps:**
1. With an earlier historical date selected on `/backtest`, open the "View as-of date" dropdown
2. Select the first option **"Latest · &lt;date&gt;"**
3. Wait for the data to reload
4. Re-read the evidence summary "Snapshots contributing" count and "(n=…)"

**Expected Result:**
- The top-bar indicator returns to the quiet "Latest" badge
- The "Snapshots contributing" count and "(n=…)" return to the original N_latest / n_latest values seen before selecting an earlier date
- The evidence heading reads "Forward-tested evidence (expanding window ≤ &lt;latest date&gt;)"

---

### UT-05 — Horizon selector updates every evidence panel without a refetch (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → Horizon selector + `EvidenceAggregateSection`

**Preconditions:**
- A date with measurable returns at more than one horizon is selected (default Latest is fine)
- Browser DevTools open on the **Network** tab, filtered to "backtest"

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Open DevTools → Network tab; type "backtest" in the filter; clear the request log
3. Scroll to the "Horizon" button group (in the Return Attribution header). Note the currently pressed button (e.g. "10d")
4. Read the evidence summary "Mean stock fwd return (10d): …" and the values in the "Forward return by score bucket" panel
5. Click a **different** horizon button (e.g. "20d")
6. Re-read the evidence summary label and the bucket panel values
7. Check the Network tab request log

**Expected Result:**
- After clicking "20d", the evidence summary label changes to "Mean stock fwd return (20d): …"
- The numbers in the bucket panel (and the other evidence panels + control-group table) change to the 20d figures
- The control-group panel hint text updates to read "At 20 days: …"
- **No new request to `/api/backtest` appears** in the Network log — the horizon switch is purely client-side over the already-fetched payload

---

### UT-06 — Low-sample ⚠ flag and honest NA "—" render correctly (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/backtest` → evidence panels

**Preconditions:**
- An as-of/horizon combination that produces at least one low-sample or empty cell (an earlier historical date and/or a long horizon like 60d typically yields these)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Select an earlier historical date from the "View as-of date" dropdown
3. Click the "60d" horizon button
4. Scroll through the evidence panels (bucket, excess, setup, regime, VCP, pattern, control group)

**Expected Result:**
- Cells with no data show a literal em dash **"—"**, never `0`, `0.0%`, `null`, or `NaN`
- Cells whose sample size is below the stated minimum show the sample with the amber **"⚠"** warning marker (matching the legend "Figures with n &lt; &lt;min&gt; ⚠ are low-sample.")
- Breakdown panels with zero rows show their italic empty label (e.g. "No setup had a measurable forward return at this horizon.") rather than an empty table or a blank gap

---

### UT-07 — Empty-state shows for a window with no measurable evidence (error / empty state)

**Type:** error
**Priority:** P2
**Surface:** `/backtest` → `EvidenceAggregateSection` empty state

**Preconditions:**
- The earliest available as-of date has no snapshot with enough post-snapshot data at the selected horizon

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Open the "View as-of date" dropdown and select the **earliest (bottom-most) date** in the list
3. If needed, click the longest horizon button ("60d") to force a window with no elapsed forward return
4. Scroll to the "Forward-tested evidence (expanding window ≤ …)" section

**Expected Result:**
- Instead of empty panels or zeros, a single empty-state card appears with the title **"No forward-tested evidence for this window yet"** and an explanatory description mentioning moving the as-of date later
- The seven panels and the control-group table are NOT rendered in this state (the empty state replaces them)
- No fabricated numbers are shown

---

### UT-08 — Control-group top-ranked cohort row is highlighted (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/backtest` → `ControlGroupPanel`

**Preconditions:**
- A date with measurable control-group data is selected (Latest is fine)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Scroll to "Control-group comparison — selection vs sector beta"
3. Inspect the cohort rows

**Expected Result:**
- Rows are present for the top-ranked cohort, random same-sector peers, and the benchmarks (SPY / QQQ / sector ETF), each labelled and showing a numeric return or honest "—"
- The **top-ranked cohort row is visually highlighted** (bolder label text + a distinct row background `bg-surface-2`) versus the other rows
- The panel hint reads "At &lt;N&gt; days: does the top-ranked cohort beat random same-sector peers and the benchmarks …"

---

### UT-09 — System Health is gone from the sidebar; sidebar lists 10 items (regression / nav)

**Type:** regression
**Priority:** P1
**Surface:** Sidebar (all pages)

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Read the left sidebar navigation items top to bottom

**Expected Result:**
- The sidebar lists exactly **10** items in order: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager
- There is **no "System Health"** entry anywhere in the sidebar

---

### UT-10 — `/system-health` route returns 404 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/system-health` (removed route)

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate directly to `http://localhost:3835/system-health` by typing the URL into the address bar
2. Wait for the page to load

**Expected Result:**
- Next.js default 404 ("This page could not be found" / 404) is shown
- The forward-test evidence is NOT rendered here — it lives only on `/backtest`

---

### UT-11 — Single date control invariant: no page-local date dropdown, URL date-free (regression / J-18 guard)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest` (J-18 anti-goal guard)

**Preconditions:**
- Frontend running

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Visually scan the entire page, including the evidence section, for any second date `<select>` / date picker (other than the single top-bar "View as-of date" switcher)
3. Select an earlier date from the top-bar switcher and observe the browser address bar
4. Click a different horizon button and observe the address bar again

**Expected Result:**
- There is exactly **one** date control in view — the global top-bar "View as-of date" switcher. No date dropdown appears inside the evidence section
- The page URL stays `http://localhost:3835/backtest` with **no** `?as_of=` or date query parameter after changing the date
- Changing the horizon does not add any query parameter to the URL

---

### UT-12 — Existing Backtest surfaces unchanged and correctly ordered (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest` → scorecard / Return Attribution / leadership lists

**Preconditions:**
- A date with an elapsed forward window is selected (Latest)

**Steps:**
1. Navigate to `http://localhost:3835/backtest`
2. Scroll the page top to bottom, noting the order of the major sections
3. Count the occurrences of a "Return attribution" heading

**Expected Result:**
- Sections appear in this top-to-bottom order: As-of scan summary → **Forward-test scorecard** → **Return attribution** (with the Horizon selector in its header) → **Leadership cohorts** (Top Sectors / Top Themes / Ranked cohort) → **Forward-tested evidence (expanding window ≤ …)**
- Exactly **one** "Return attribution" heading exists (the new evidence section is separately titled, not a duplicate)
- The new evidence section is the **last** section, below the leadership lists
- The "Forward-test scorecard" table, Return Attribution, and leadership lists still render their values as before

---

### UT-13 — Backend-unavailable shows honest error, not fabricated evidence (error)

**Type:** error
**Priority:** P2
**Surface:** `/backtest` (error state)

**Preconditions:**
- Ability to stop the backend OR observe a transient backend outage

**Steps:**
1. Stop the backend API (or block `/api/backtest`)
2. Navigate to `http://localhost:3835/backtest`
3. Observe the page

**Expected Result:**
- A red "Backend unavailable" card appears stating the scorecard could not load and that no figures are shown rather than fabricated values
- The evidence section is NOT rendered with zeros or stale numbers
- (Restart the backend and reload to confirm the page recovers)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Backtest loads with evidence section | smoke | P1 | `/backtest` |
| UT-02 | Summary line + seven panels render | happy-path | P1 | `/backtest` |
| UT-03 | Evidence re-scopes earlier, n shrinks | happy-path | P1 | `/backtest` + switcher |
| UT-04 | Latest reproduces all-history numbers | happy-path | P1 | `/backtest` + switcher |
| UT-05 | Horizon updates panels, no refetch | happy-path | P1 | `/backtest` Horizon |
| UT-06 | Low-sample ⚠ + honest NA "—" | validation | P2 | `/backtest` panels |
| UT-07 | Empty-state for no-evidence window | error | P2 | `/backtest` empty state |
| UT-08 | Control-group top row highlighted | ux | P3 | `/backtest` control group |
| UT-09 | System Health gone, sidebar = 10 | regression | P1 | Sidebar |
| UT-10 | `/system-health` 404 | regression | P1 | `/system-health` |
| UT-11 | Single date control, URL date-free | regression | P1 | `/backtest` (J-18) |
| UT-12 | Existing surfaces unchanged + ordered | regression | P1 | `/backtest` |
| UT-13 | Backend-unavailable honest error | error | P2 | `/backtest` |

**P1 tests (UT-01–UT-05, UT-09–UT-12) must all pass for browser QA verdict to be PASS.**
