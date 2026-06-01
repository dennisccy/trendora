# Phase goal-i_can_see_the_wealthy_future_forever-iter-2 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

This iteration adds a read-only **"Return attribution"** section (J-19) to two existing pages:
`/system-health` (aggregate, rides the page's existing Horizon selector) and `/backtest` (per-date,
with a new client-side "Horizon" view selector). The section renders four panels:
**Top contributors & detractors**, **Distribution & hit-rate**, **Forward return by sector**, and
**Forward return by rank band**. No new routes or navigation were added; the change is additive.

These UI tests do NOT duplicate the API/artifact tests in
`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-test-plan.md` (TC-01–TC-08, TC-15, TC-16).
They cover only what an operator can see and click in the browser.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — System Health page loads with the new attribution section (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/system-health`

**Preconditions:**
- Frontend running at http://localhost:3835, backend at http://localhost:8000
- At least one walk-forward snapshot with elapsed forward windows exists (so evidence renders, not the
  "No forward-tested evidence yet" empty state)

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Wait for the page to fully load (the "Forward-tested evidence" content replaces the skeleton)
3. Scroll to the bottom of the page, past the "Control-group comparison — selection vs sector beta" card

**Expected Result:**
- Page renders without a blank screen or "Backend unavailable" error card
- A section heading "Return attribution" is visible, located BELOW the
  "Control-group comparison — selection vs sector beta" panel
- Four panel headings are visible under it: "Top contributors & detractors",
  "Distribution & hit-rate", "Forward return by sector", "Forward return by rank band"
- No console errors

---

### UT-02 — System Health attribution shows real per-stock / distribution / group figures (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → `ReturnAttributionSection`

**Preconditions:**
- A horizon with samples is selected (the default 20d, or pick one with data)

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Scroll to the "Return attribution" section
3. In the "Top contributors & detractors" panel, read the two columns labelled "Contributors" and
   "Detractors"
4. In the "Distribution & hit-rate" panel, read the five rows
5. In the "Forward return by sector" and "Forward return by rank band" panels, read the rows

**Expected Result:**
- "Top contributors & detractors" shows two columns ("Contributors", "Detractors"); each lists one or
  more tickers, and each ticker row shows a sector label below the ticker symbol and a colored mean
  return with a sample size in the form `(n=…)`
- "Distribution & hit-rate" shows exactly five rows: "Mean", "Median", "% positive (hit rate)",
  "Dispersion (σ)", "Sample size"
- "Mean" and "Median" values are color-graded (green for positive, red for negative);
  "% positive (hit rate)" and "Dispersion (σ)" are neutral (no green/red, no +/- sign) and shown as a
  percentage
- "Forward return by sector" shows one row per sector with a mean return and `n`
- "Forward return by rank band" lists every configured band (e.g. "1–10", "11–50", "51+"), each with a
  mean return and `n`

---

### UT-03 — Distribution Mean equals the page header "Mean stock fwd return" (happy path / consistency)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → `DistributionPanel`

**Preconditions:**
- A horizon with samples is selected; the page header strip shows a "Mean stock fwd return: …%"
  value with `(n=…)`

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. In the summary strip near the top, note the value after "Mean stock fwd return:" and its `(n=…)`
3. Scroll to the "Return attribution" → "Distribution & hit-rate" panel
4. Compare the "Mean" row value (and "Sample size") to the header value

**Expected Result:**
- The "Distribution & hit-rate" → "Mean" value equals the header "Mean stock fwd return" value (same
  number, same sign/color)
- The "Sample size" value equals the header `(n=…)` value
- No second, divergent mean is shown for the same horizon

---

### UT-04 — Horizon change re-renders the System Health attribution (happy path / regression of shared control)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → `HorizonSelector` (existing) drives the attribution section

**Preconditions:**
- Page loaded; the "Horizon" segmented selector (1d / 5d / 10d / 20d / 60d buttons) is visible in the
  top-right next to the "System Health" heading

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Note the current "Distribution & hit-rate" → "Mean" value and the active horizon button (highlighted)
3. Click a different horizon button (e.g. "5d") in the top-right Horizon selector
4. Wait for the page to refresh its figures
5. Re-read the "Return attribution" panels

**Expected Result:**
- The clicked button ("5d") becomes the highlighted/active one
- The "Return attribution" panels (per-stock, distribution, by-sector, by-rank-band) update to the new
  horizon's figures along with the rest of the page (the "Mean stock fwd return" header also updates)
- The intro copy in the section reads "Open the 5-day forward return:" matching the selected horizon
- No console errors, no blank section

---

### UT-05 — Backtest page loads with the attribution section and Horizon view selector (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend + backend running
- The global as-of switcher (top bar) is set to a historical date with ≥60 post-snapshot trading bars
  (so at least one horizon has an observed window)

**Steps:**
1. Use the top-bar "View as-of date" dropdown to select a historical date (any date other than
   "Latest")
2. Navigate to `http://localhost:3835/backtest` (use the "Backtest" sidebar link, not a hard reload)
3. Wait for the "Forward-test scorecard" table to render
4. Scroll below the "Forward-test scorecard" table

**Expected Result:**
- A "Return attribution" section heading is visible BELOW the "Forward-test scorecard" card
- A "Horizon" label with a segmented button group (buttons "1d", "5d", "10d", "20d", "60d") appears in
  the section header, right-aligned
- The four panels render: "Top contributors & detractors", "Distribution & hit-rate",
  "Forward return by sector", "Forward return by rank band"
- No "Backend unavailable" error card

---

### UT-06 — Backtest Horizon view selector switches the displayed slice (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` → `HorizonViewSelector`

**Preconditions:**
- On `/backtest` at a historical date where multiple horizons have observed windows (per UT-05)

**Steps:**
1. On `http://localhost:3835/backtest`, scroll to the "Return attribution" section
2. Note which Horizon button is highlighted by default and read the "Distribution & hit-rate" → "Mean"
   value
3. Click a different Horizon button (e.g. "10d")
4. Re-read the four panels and the section intro copy

**Expected Result:**
- The default highlighted Horizon button is the first horizon with an observed window (a panel showing
  real numbers, not all-NA), per the default-selection behavior
- After clicking "10d", the "10d" button becomes highlighted (active), and the four panels update to
  the 10d slice values
- The section intro copy updates to "Open the 10-day forward return:"
- The "Forward-test scorecard" table ABOVE the section does NOT change
- The "Viewing as-of {date}" badge near the top of the page does NOT change

---

### UT-07 — Backtest Horizon selector triggers NO refetch and NO date change (regression guard, J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest` → `HorizonViewSelector` (date-state regression guard)

**Preconditions:**
- On `/backtest` at a historical date with multiple observed horizons

**Steps:**
1. On `http://localhost:3835/backtest`, open browser DevTools → Network tab; clear the request log
2. Note the date shown in the "Viewing as-of {date}" badge near the top of the page
3. Scroll to the "Return attribution" section and click through several Horizon buttons (e.g. 1d → 5d
   → 60d)
4. Watch the Network tab during the clicks
5. Re-check the "Viewing as-of {date}" badge and the top-bar as-of dropdown value

**Expected Result:**
- No new `/api/backtest` (or any `/api/...`) request fires when switching Horizon buttons — the Network
  log stays empty of new data requests during the clicks
- The "Viewing as-of {date}" badge value is unchanged before and after
- The top-bar "View as-of date" dropdown selection is unchanged
- Only the attribution panels' numbers change

---

### UT-08 — Honest NA on a too-recent date (validation / honesty)

**Type:** validation
**Priority:** P2
**Surface:** `/backtest` → `ReturnAttributionSection` NA handling

**Preconditions:**
- A recent as-of date exists where one or more horizons have no elapsed forward window

**Steps:**
1. Use the top-bar "View as-of date" dropdown to select the most recent historical date (or "Latest"),
   one where short windows may not have elapsed
2. Navigate to `http://localhost:3835/backtest`
3. Scroll to the "Return attribution" section
4. Click a horizon button that has no elapsed window (e.g. "60d" on a recent date)

**Expected Result:**
- For a horizon with no data: "Distribution & hit-rate" rows show an em dash "—" for Mean/Median/hit
  rate/dispersion and "Sample size" shows n=0; "Top contributors & detractors" shows the copy
  "No ticker had a measurable forward return at this horizon."
- Empty sector / rank-band panels show "No sector had a measurable forward return at this horizon." /
  "No rank band had a measurable forward return at this horizon." (or empty bands render an em-dash NA
  row)
- Figures with a sample size below the page's `min_sample` carry the "⚠" low-sample marker
- NO fabricated "0%" or "0.00%" is shown in place of missing data

---

### UT-09 — Empty rank bands still listed; per-stock empty side renders copy (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/system-health` and `/backtest` → `GroupPanel` / `PerStockPanel`

**Preconditions:**
- A horizon/date where at least one configured rank band has no observations

**Steps:**
1. Navigate to `http://localhost:3835/system-health` (or `/backtest`)
2. Scroll to "Forward return by rank band"
3. Inspect each configured band row (e.g. "1–10", "11–50", "51+")
4. In "Top contributors & detractors", check whether either the Contributors or Detractors column is
   empty

**Expected Result:**
- Every configured rank band appears as a row even when it has no data; an empty band shows an em dash
  "—" for its mean return (NA), not a fabricated 0
- If a per-stock column (Contributors or Detractors) has no rows, it shows a single "—" placeholder
  rather than disappearing
- The set of band labels matches the configured bands (no missing or invented band)

---

### UT-10 — Regression: existing System Health panels unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/system-health` (J-09 / J-10)

**Preconditions:**
- Frontend + backend running, evidence present

**Steps:**
1. Navigate to `http://localhost:3835/system-health`
2. Confirm the pre-existing panels still render above the new section: "Forward return by score
   bucket", "Excess vs benchmarks", "Forward return by setup type", "Forward return by market regime",
   "Forward return: VCP vs non-VCP", and "Control-group comparison — selection vs sector beta"
3. Confirm each shows mean returns with `n` values and no layout breakage

**Expected Result:**
- All six pre-existing panels render with values and `n`, unchanged in position and content by the
  additive attribution section
- No panel was removed or visually broken; the new "Return attribution" section sits at the bottom only

---

### UT-11 — Regression: Backtest single global date control intact (regression, J-13 / J-14 / J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3835/backtest` via the "Backtest" sidebar link
2. Confirm the ONLY date control on the page area is the top-bar "View as-of date" dropdown — there is
   no second date picker inside the page body
3. Change the as-of date using the top-bar dropdown (pick a different historical date)
4. Confirm the "Forward-test scorecard" and the "Viewing as-of {date}" badge update to the new date
5. Confirm the "Return attribution" section's "Horizon" buttons are NOT a date control (they only say
   "1d/5d/10d/20d/60d", not dates)

**Expected Result:**
- Exactly one date selector governs the page (the global top-bar switcher); the in-section "Horizon"
  buttons select a view, not a date
- Changing the global as-of date updates the scorecard, the "Viewing as-of {date}" badge, and the
  attribution figures together
- No independent/page-local date state exists

---

### UT-12 — Feature is discoverable from existing navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** sidebar navigation → `/system-health`, `/backtest`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. In the left sidebar, click "System Health"
3. Scroll to the bottom of the page
4. In the left sidebar, click "Backtest"
5. Scroll below the "Forward-test scorecard"

**Expected Result:**
- Both "System Health" and "Backtest" links exist in the left sidebar (no new nav item was needed)
- On each page, the "Return attribution" section is reachable by scrolling — within one click from the
  sidebar plus a scroll
- The section heading "Return attribution" and its one-line explanatory copy ("Open the N-day forward
  return: which tickers drove or dragged it…") make the purpose clear without developer knowledge

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | System Health loads with attribution section | smoke | P1 | `/system-health` |
| UT-02 | Attribution shows real figures | happy-path | P1 | `/system-health` |
| UT-03 | Distribution Mean equals header mean | happy-path | P1 | `/system-health` |
| UT-04 | Horizon change re-renders attribution | happy-path | P1 | `/system-health` |
| UT-05 | Backtest loads with section + view selector | smoke | P1 | `/backtest` |
| UT-06 | Horizon view selector switches slice | happy-path | P1 | `/backtest` |
| UT-07 | Selector triggers no refetch / no date change | regression | P1 | `/backtest` |
| UT-08 | Honest NA on too-recent date | validation | P2 | `/backtest` |
| UT-09 | Empty bands listed; per-stock empty copy | validation | P2 | both |
| UT-10 | Existing System Health panels unchanged | regression | P1 | `/system-health` |
| UT-11 | Backtest single global date control intact | regression | P1 | `/backtest` |
| UT-12 | Discoverable from sidebar | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.**
</content>
</invoke>
