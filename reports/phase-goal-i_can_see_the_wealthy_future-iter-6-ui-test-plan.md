# Phase goal-i_can_see_the_wealthy_future-iter-6 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-6 — Walk-forward forward-testing engine + System Health evidence (J-09, J-10)
**Date:** 2026-05-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3836

---

## Notes for the tester

- All new functionality lives on a single page: **`/system-health`**. It is reachable from the left sidebar via the **"System Health"** link (already existed; now populated).
- On a fresh/restarted backend the first boot runs a one-time walk-forward backfill (~223 s). If the page shows the "Backend unavailable" red alert or the skeleton for a long time right after a restart, wait for the backfill to finish, then reload.
- Every numeric figure on the page is rendered as a percentage like `+1.23%` / `-0.84%`, with a sample-size token `n=NN` (or `n=NN ⚠` when low-sample) to its right. Use these as your anchors.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — System Health page loads and is populated (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/system-health`

**Preconditions:**
- Frontend running at http://localhost:3836
- Backend running and the walk-forward backfill has completed

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Wait for the page to fully load (skeleton, if shown, disappears)

**Expected Result:**
- The heading "System Health" is visible with the subtitle starting "Forward-tested evidence — did higher-ranked buckets…"
- The page is NOT the old empty-placeholder state and NOT a blank screen
- At least these panels are visible: "Forward return by score bucket", "Excess vs benchmarks", "Forward return by setup type", "Forward return by market regime", and "Control-group comparison — selection vs sector beta"
- No console errors

---

### UT-02 — Survivorship-bias banner is visible (happy path / honesty)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health`

**Preconditions:**
- `/system-health` is loaded with data (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Look near the top of the page, directly under the heading row

**Expected Result:**
- A prominent warn-toned (amber/yellow-bordered) banner appears with the bold label "Survivorship bias"
- The banner shows a sentence of explanatory text about current-membership universe / results possibly being overstated
- The banner is shown even before the data finishes loading (it has a default sentence)

---

### UT-03 — Forward-return by score bucket table shows A–E rows with mean + n (happy path, J-09)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → "Forward return by score bucket" panel

**Preconditions:**
- `/system-health` is loaded with data

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Locate the panel titled "Forward return by score bucket"
3. Read each row in the "Bucket" / "Mean fwd return" table

**Expected Result:**
- Rows for buckets A, B, C, D, and E are present, each with a colour-graded bucket badge
- Each row shows a numeric "Mean fwd return" formatted like `+1.23%` / `-0.45%` / `—`
- Each row shows a sample-size token `n=NN` to the right of the return
- No row shows a raw number without a percent sign or without an `n`

---

### UT-04 — Excess vs SPY and vs QQQ panels show cohort, benchmark, excess and n (happy path, J-09)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → "Excess vs benchmarks" panel

**Preconditions:**
- `/system-health` is loaded with data

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Locate the panel titled "Excess vs benchmarks"
3. Read the "Excess vs SPY" row and the "Excess vs QQQ" row

**Expected Result:**
- The panel has columns: "Excess", "Stocks", "Benchmark", "Excess"
- An "Excess vs SPY" row shows a numeric Stocks value, a numeric Benchmark value, and a numeric Excess value with an `n=NN` token; the row label includes the benchmark ticker in parentheses (e.g. "(SPY)")
- An "Excess vs QQQ" row shows the same four pieces of data with its own `n=NN`

---

### UT-05 — By-setup and by-regime breakdowns show mean + n; both regimes present (happy path, J-09)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → "Forward return by setup type" and "Forward return by market regime" panels

**Preconditions:**
- `/system-health` is loaded with data

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Locate the panel titled "Forward return by setup type" and read its rows
3. Locate the panel titled "Forward return by market regime" and read its rows

**Expected Result:**
- "Forward return by setup type": each setup row shows a label, a numeric mean return (`+/-NN.NN%` or `—`), and an `n=NN` token
- "Forward return by market regime": BOTH a "Risk-on" row and a "Risk-off" row appear, each with a numeric mean return and an `n=NN` token
- If a panel genuinely has no data it shows an explicit sentence (e.g. "No regime had a measurable forward return at this horizon"), never a fabricated 0%

---

### UT-06 — Control-group comparison panel shows all five cohorts with n (happy path, J-10)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → "Control-group comparison — selection vs sector beta" panel

**Preconditions:**
- `/system-health` is loaded with data

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Locate the panel titled "Control-group comparison — selection vs sector beta"
3. Read each cohort row in the "Cohort" / "Mean fwd return" table

**Expected Result:**
- Rows are present for: the top-ranked cohort, a random same-sector cohort, SPY, QQQ, and the sector ETF — each with a clear label
- The top-ranked cohort row is visually highlighted (bolder text / shaded background)
- Each row shows a numeric mean forward return and an `n=NN` token
- The panel hint mentions the selected horizon (e.g. "At 20 days: …")

---

### UT-07 — Horizon selector changes the figures (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/system-health` → Horizon segmented selector (top-right)

**Preconditions:**
- `/system-health` is loaded with data; default horizon button "20d" is active

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Note the "Mean fwd return" value in the first bucket row (e.g. bucket A) and the control-group top-ranked value
3. In the "Horizon" button group (top-right, labelled "Horizon" with buttons 1d / 5d / 10d / 20d / 60d), click the "5d" button
4. Wait for the page to update

**Expected Result:**
- The "5d" button becomes the active/highlighted button and the "20d" button is no longer active (`aria-pressed="true"` moves to "5d")
- The control-group panel hint updates to read "At 5 days: …"
- At least one figure on the page (bucket mean, excess, or control-group value) changes compared with the 20d view
- The page does NOT show the red "Backend unavailable" alert during a normal horizon change

---

### UT-08 — Summary strip shows snapshot count, as-of range, overall mean and legend (ux/happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/system-health` → summary strip (directly above the panel grid)

**Preconditions:**
- `/system-health` is loaded with data

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Read the single-line summary strip located between the survivorship banner and the panel grid

**Expected Result:**
- It shows "Snapshots contributing:" followed by a numeric count
- It shows "As-of range:" followed by a date → date range (e.g. `2024-06-30 → 2026-03-31`)
- It shows "Mean stock fwd return:" followed by a percent value and `(n=NN)`
- It shows the legend "Figures with n < <min> ⚠ are low-sample."

---

### UT-09 — Low-sample figures are flagged with ⚠ rather than hidden (validation, anti-goal)

**Type:** validation
**Priority:** P2
**Surface:** `/system-health` → any panel containing a low-sample figure

**Preconditions:**
- `/system-health` is loaded with data
- At least one figure has `n` below the minimum sample (read the min from the summary-strip legend)

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Read the legend in the summary strip to learn the minimum sample threshold (the number in "n < <min> ⚠")
3. Scan the bucket, breakdown, and control-group rows for any `n=NN` value below that threshold

**Expected Result:**
- Any figure whose `n` is below the threshold shows the `⚠` marker immediately after the `n=NN` (rendered in the warn/amber colour)
- Hovering that token shows a tooltip about it being low-sample / indicative only
- Such rows are still displayed (the figure is NOT removed or zeroed)

---

### UT-10 — Positive/negative returns use distinct colours (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/system-health` → any return figures

**Preconditions:**
- `/system-health` is loaded with data containing at least one positive and one negative figure

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Visually compare a `+NN.NN%` figure with a `-NN.NN%` figure (e.g. between bucket rows or excess values)

**Expected Result:**
- Positive returns (`+…%`) render in the positive/green palette
- Negative returns (`-…%`) render in the negative/red palette
- `—` (no data) figures render muted/grey, not green or red

---

### UT-11 — Backend-unavailable state shows a red alert, not fabricated zeros (error)

**Type:** error
**Priority:** P2
**Surface:** `/system-health` → error state

**Preconditions:**
- Backend is stopped or not yet ready (e.g. during the first-boot backfill window)

**Steps:**
1. With the backend stopped/unready, navigate to `http://localhost:3836/system-health`
2. Wait for the fetch to fail

**Expected Result:**
- A styled red-bordered alert appears with the bold heading "Backend unavailable" and explanatory text ("No figures are shown rather than fabricated values…")
- NO bucket/excess/control numbers and NO `0%` figures are shown
- The survivorship banner and the page heading remain visible (page does not white-screen)

---

### UT-12 — Loading skeleton appears before data (smoke)

**Type:** smoke
**Priority:** P3
**Surface:** `/system-health` → loading state

**Preconditions:**
- Backend running and responsive (so the page eventually loads)

**Steps:**
1. Navigate to `http://localhost:3836/system-health`
2. Immediately observe the area below the survivorship banner during the first moment after load (hard-reload with Ctrl/Cmd+Shift+R if needed)

**Expected Result:**
- A grid of pulsing/animated skeleton cards (4 cards) is briefly visible while data is fetched
- The skeleton is replaced by the real panels once data arrives (or by the red alert if the backend is down)

---

### UT-13 — Scanner Runs history still works and shows the added as-of snapshots (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- Backend running; walk-forward backfill has completed (it adds 8 cadence as-of snapshots → 11 runs total)

**Steps:**
1. Navigate to `http://localhost:3836/scanner-runs` (or click "Scanner Runs" in the left sidebar)
2. Read the list of scanner runs

**Expected Result:**
- The Scanner Runs page loads normally (no error/blank)
- The list now includes additional dated walk-forward as-of run rows on top of the pre-existing bootstrap runs (more rows than before this phase)
- Pre-existing run rows are still present and readable (immutable history — intended behavior, NOT a regression)

---

### UT-14 — Core J-01–J-08 pages still load (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/sectors`, `/themes`

**Preconditions:**
- Backend running

**Steps:**
1. Navigate to `http://localhost:3836/` and confirm the Dashboard renders
2. Navigate to `http://localhost:3836/stocks` and confirm the Stocks list renders
3. Navigate to `http://localhost:3836/sectors` and confirm the Sectors view renders
4. Navigate to `http://localhost:3836/themes` and confirm the Themes view renders

**Expected Result:**
- Each page loads with its data and no error/blank screen
- No new errors introduced by the iter-6 changes (these journeys were required to stay green)

---

### UT-15 — System Health is discoverable from the sidebar (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / sidebar

**Steps:**
1. Navigate to `http://localhost:3836/` (Dashboard)
2. Look at the left navigation sidebar

**Expected Result:**
- A sidebar link labelled "System Health" (with an activity icon) is visible
- Clicking it navigates to `http://localhost:3836/system-health` and the link is shown as active

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads and is populated | smoke | P1 | `/system-health` |
| UT-02 | Survivorship-bias banner visible | happy-path | P1 | `/system-health` |
| UT-03 | By-bucket A–E table (mean + n) | happy-path | P1 | `/system-health` |
| UT-04 | Excess vs SPY / QQQ panels | happy-path | P1 | `/system-health` |
| UT-05 | By-setup / by-regime breakdowns | happy-path | P1 | `/system-health` |
| UT-06 | Control-group comparison (5 cohorts) | happy-path | P1 | `/system-health` |
| UT-07 | Horizon selector changes figures | happy-path | P1 | `/system-health` |
| UT-08 | Summary strip content | happy-path | P2 | `/system-health` |
| UT-09 | Low-sample ⚠ flag | validation | P2 | `/system-health` |
| UT-10 | Pos/neg colour coding | ux | P3 | `/system-health` |
| UT-11 | Backend-unavailable red alert | error | P2 | `/system-health` |
| UT-12 | Loading skeleton | smoke | P3 | `/system-health` |
| UT-13 | Scanner Runs history regression | regression | P1 | `/scanner-runs` |
| UT-14 | J-01–J-08 pages still load | regression | P1 | `/`, `/stocks`, `/sectors`, `/themes` |
| UT-15 | Discoverable from sidebar | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.**
