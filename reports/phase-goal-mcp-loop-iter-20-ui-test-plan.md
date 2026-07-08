# Phase goal-mcp-loop-iter-20 — UI Test Plan

**Phase:** goal-mcp-loop-iter-20
**Date:** 2026-07-08
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (deterministic per-repo default computed by `scripts/start-backend.sh`'s `sha1sum`-based offset for this exact repo path — verified by re-running that formula, not assumed; every page shows a "Backend unavailable" card if it isn't reachable at this address. If `CHAIN_BACKEND_PORT` was set explicitly for this run, use that value instead.)

---

## Scope note

This plan is grounded directly in the current frontend source — `apps/frontend/app/data/page.tsx`,
`apps/frontend/components/availability-heatmap.tsx`, `apps/frontend/app/globals.css`, and
`apps/frontend/components/sidebar.tsx` — not paraphrased from the surface map alone, so option text,
button labels, copy, hex colors, and DOM structure below are exact quotes/values from the shipped code
(re-verified by direct `grep`/`Read` on 2026-07-08, after dev+review+ui-impact-analyst completed). Two
things worth flagging:

- **No dangling Expand code remains.** A direct search for `isExpandKind`, `isFetchKind`'s old Expand
  disjunct, `sourceIneligibleForExpand`, `ExpandScreenResult`, `isExpand`, and `value="expand"` in
  `page.tsx` returns zero matches — confirmed clean before writing this plan.
- **The job form's Start/End dates auto-prefill.** On page load, `start`/`end` begin empty but are
  populated ONCE from the dataset's real backfill-gap preview (`data.coverage.gaps_preview`) as soon as
  the coverage panel loads — so by the time a tester reaches the job-start form, the dates are usually
  already filled with a valid range and the "Start" button is enabled without typing anything. The default
  job kind on load is "Backfill snapshots" (not Fetch), so the Import Source field is hidden until a
  tester explicitly switches the Job kind dropdown.

Test IDs use UT-XX (distinct from the functional test plan's TC-XX IDs in
`reports/qa/goal-mcp-loop-iter-20-test-plan.md`, which this plan intentionally does not duplicate — that
plan's TC-01/TC-02 are API-level checks not repeated here as clicks).

---

## Test Cases

<!-- Each test has exact steps and specific expected results. No vague steps. -->

---

### UT-01 — `/data` loads without errors, required panels visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at `http://localhost:3255`, backend running at `http://localhost:8255`
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading (any loading spinners disappear)

**Expected Result:**
- The left sidebar is visible with "Data Manager" shown as the highlighted/active nav item
- A panel with the heading "Start a fetch / backfill job" is visible
- Further down the page, a card titled "Per-date availability" is visible
- No "Backend unavailable" card appears anywhere on the page
- The page is not blank and shows no unhandled error message
- No browser console errors

---

### UT-02 — Job-kind picker has exactly 3 options, no "Expand universe" (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-01 passed

**Steps:**
1. On `http://localhost:3255/data`, find the panel titled "Start a fetch / backfill job"
2. Click the dropdown labeled "Job kind"
3. Read every option from top to bottom

**Expected Result:**
- Exactly three options are listed, in this exact order: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill"
- No option reads "Expand universe" and no option text contains the word "Expand"
- The dropdown defaults to "Backfill snapshots" when the page first loads

---

### UT-03 — Starting "Fetch EOD prices" now covers the full ~588-symbol committed pool (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- UT-02 passed
- The Start/End date fields show a prefilled date range (see Scope note above); if they appear empty, type a short recent range in `yyyy-MM-dd` format into both the "Start date" and "End date" fields
- At least one entry in the "Import source" dropdown is available for selection (see step 2)

**Steps:**
1. In the "Job kind" dropdown, select "Fetch EOD prices"
2. An "Import source" dropdown appears next to it, already showing a selected value (it auto-selects the first source) — confirm the selected option's label ends in "· available" (if it instead ends in "· needs key", open the dropdown and pick a different option that ends in "· available")
3. Click the "Start" button (green Play icon, reads "Start")
4. Watch the "Job progress" panel that appears below the form and find the row labeled "Symbols fetched"

**Expected Result:**
- The "Start" button is not disabled and clicking it produces no error alert
- The "Symbols fetched" row shows a count in the form "`{done}/{total} ({ok} ok, {failed} failed)`" where `{total}` is approximately 588 and is at minimum 548 — NOT the old ~162 figure
- A progress bar directly beneath the counter is visible and advances as the job runs
- The job's button label changes to "Job running…" while active, and the job eventually reaches `{total}/{total}` (every symbol attempted) without the page crashing or showing a client-side error

---

### UT-04 — Starting "Backfill snapshots" still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; some trading days with stored price bars but no snapshot exist (true by default on a freshly-fetched or partially-backfilled dataset)

**Steps:**
1. In the "Job kind" dropdown, select "Backfill snapshots" (the default)
2. Confirm the "Import source" dropdown is NOT shown (Backfill needs no source)
3. Click the "Start" button

**Expected Result:**
- No error alert appears below the form
- The "Job progress" panel shows a row labeled "Snapshots backfilled" (not "Symbols fetched")
- The job runs (or shows a completed state) with no client-side error and no blank page

---

### UT-05 — Starting "Fetch + backfill" still works; no "Universe screen" block appears (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; an "· available" import source exists

**Steps:**
1. In the "Job kind" dropdown, select "Fetch + backfill"
2. Confirm an "Import source" dropdown appears and an "· available" option is selected
3. Click "Start"
4. While the job runs, scroll through the entire job-progress card from top to bottom

**Expected Result:**
- Both a "Symbols fetched" row and (once the fetch stage finishes) a "Snapshots backfilled" row appear on the same progress card
- At no point does a "Universe screen" section, an "N passed" / "N omitted" badge pair, or a list of omitted candidates appear anywhere on the card — this block only ever existed for the now-removed Expand job kind
- The job completes (or shows live progress) with no client-side error

---

### UT-06 — Import-source options are never disabled and carry no market-cap suffix (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded

**Steps:**
1. Select "Fetch EOD prices" in the "Job kind" dropdown
2. Open the "Import source" dropdown
3. Read every option's full label text top to bottom
4. Select each option in turn, including any option whose label ends in "· needs key"

**Expected Result:**
- Every option's label ends in exactly "· available" or "· needs key" — no other suffix text
- No option is greyed out or unselectable — every listed option can be chosen
- No option's label contains the words "market cap", "cannot supply", or "expand"

---

### UT-07 — No market-cap-ineligibility alert renders under any job-kind/source combination (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; more than one import source is registered (check the "Import source" dropdown's option count)

**Steps:**
1. Select "Fetch EOD prices" as the job kind
2. Cycle through every option in the "Import source" dropdown one at a time
3. After each selection, look at the area directly below the source dropdown for any amber/warning-colored alert box
4. Repeat the same cycle with "Fetch + backfill" selected as the job kind

**Expected Result:**
- No amber alert box reading anything like "cannot supply market cap" ever appears, for any job-kind/source combination tried
- The only text below the source dropdown is a small grey line reading "`{source label}: available`" or "`{source label}: needs key`" followed by "` · {reason}`" — never a warning-styled alert box

---

### UT-08 — Job-form heading and explainer paragraph read the post-removal copy (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded

**Steps:**
1. Read the heading directly above the date/job-kind fields in the job-start panel
2. Read the small grey paragraph below the "Job kind"/"Import source" fields (above where an error message would appear)

**Expected Result:**
- The heading reads exactly "Start a fetch / backfill job" — not "Start a fetch / backfill / expand job"
- The paragraph reads (in full): "Backfill creates immutable snapshots (and their forward returns) for trading days that have bars but no snapshot — offline and deterministic. Fetch pulls real EOD prices via the selected import source, covering the full committed symbol pool. A provider failure is surfaced explicitly and fabricates nothing."
- The paragraph contains no occurrence of the word "Expand"

---

### UT-09 — Market-cap figures are presented as static, not on-demand-refreshable (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; the "Dataset coverage" panel (near the top of the page) has finished loading

**Steps:**
1. In the "Dataset coverage" panel, locate the metric tile labeled "Candidate universe"
2. Read the definition text shown beneath its value (or revealed via its info icon, if collapsed)

**Expected Result:**
- The definition text reads: "The static screened candidate universe (market-cap/ADV/price pool) the per-date resolver screens. Not date-scoped — the date-resolved subset is shown above."
- The word "static" appears in the definition; no text anywhere on `/data` claims market-cap figures can be refreshed, updated on demand, or kept fresh via any button or control

---

### UT-10 — Availability legend renders two separately labeled groups (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; the "Per-date availability" card has at least one month of data

**Steps:**
1. Scroll down to the "Per-date availability" card
2. Look at the legend area directly above the calendar grid (below the header text, above the month labels)

**Expected Result:**
- Two clearly separate, stacked rows are visible (not merged into one row):
  - Top row: small uppercase label "PRICE DATA — CELL FILL" followed by 6 small color swatches labeled, left to right, "none", "<25%", "25–50%", "50–75%", "75–<100%", "full"
  - Bottom row: small uppercase label "SCORED SNAPSHOT — INDICATOR" followed by one ringed swatch and the text "a scored snapshot exists for that day"
- Each row has its own heading text — the two meanings are never combined into a single label

---

### UT-11 — Density ramp's top ("full") bucket is blue, not amber; all six buckets are visually distinct (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; browser DevTools available; at least one fully-covered day cell exists on the calendar (a recent trading day on a well-fetched dataset typically qualifies)

**Steps:**
1. In the legend's "PRICE DATA — CELL FILL" row, right-click the rightmost swatch (labeled "full") and choose "Inspect"
2. In DevTools, read its computed `background-color`
3. Visually scan all 6 swatches left to right

**Expected Result:**
- The "full" swatch's computed background color is `rgb(166, 200, 242)` (`#a6c8f2`, a bright blue) — it is NOT `rgb(240, 180, 41)` (`#f0b429`, the old amber)
- All 6 swatches belong to one consistent hue family (blue), getting progressively brighter from left (darkest, `#39516f`) to right (brightest, `#a6c8f2`) — no swatch appears green, cyan, or teal
- Each of the 6 swatches is visibly distinguishable from its immediate neighbor — no two adjacent swatches look like the same shade

---

### UT-12 — Snapshot ring color is violet, not green (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; browser DevTools available; at least one calendar cell has a visible ring (a thin outline distinct from its fill color) — if none is visible, run a Backfill job first (UT-04) and reload

**Steps:**
1. On the calendar grid, find a cell with a ring around it
2. Right-click that cell and choose "Inspect," then read its computed ring/outline color (the `box-shadow` or `ring` color in the Styles/Computed panel), or compare it directly against the legend's "SCORED SNAPSHOT — INDICATOR" swatch

**Expected Result:**
- The ring color is violet, `rgb(167, 139, 250)` (`#a78bfa`) — it is NOT green (`rgb(52, 211, 153)` / `#34d399`)
- The violet ring is visually distinct against every one of the 6 blue fill shades it can appear on — it never blends into the cell's own fill color

---

### UT-13 — Hovered-day readout shows "snapshot yes" in violet for a snapshotted day (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; at least one snapshotted (ringed) day and one non-ringed day both exist on the visible calendar

**Steps:**
1. Above the calendar grid, locate the readout line (it defaults to the grey text "Hover or focus a day for exact figures")
2. Move the mouse over a calendar cell that has a ring
3. Read the readout line
4. Move the mouse to a calendar cell with no ring
5. Read the readout line again

**Expected Result:**
- While hovering the ringed cell, the readout reads "`{date} · {N}/{total} symbols · snapshot yes`" with the words "snapshot yes" rendered in violet text
- While hovering the non-ringed cell, the readout instead reads "`{date} · {N}/{total} symbols · snapshot no`" with "snapshot no" in muted grey text
- Moving the mouse away from any cell restores "Hover or focus a day for exact figures"

---

### UT-14 — Hover distinguishes a "bars-but-no-snapshot" day from a "has-snapshot" day (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded; the calendar contains at least one highly-filled cell WITHOUT a ring (a Backfill gap) and at least one cell WITH a ring. If every visible cell already has a ring (a fully backfilled dataset), first run a Fetch job (UT-03) — its most recently fetched days will not yet have a snapshot, creating the needed gap — then reload the page.

**Steps:**
1. On the calendar grid, find a cell that is highly or fully filled (bright blue) but has NO ring around it
2. Hover that cell with the mouse and wait about a second for the browser's native tooltip to appear; read its text
3. Move to a different cell that DOES have a ring and hover it the same way
4. Read that tooltip's text

**Expected Result:**
- The no-ring cell's tooltip reads: "`{date} · {N}/{total} symbols have price data (Fetch) · no snapshot yet — Backfill gap`"
- The ringed cell's tooltip reads: "`{date} · {N}/{total} symbols have price data (Fetch) · scored snapshot exists (Backfill)`"
- The two tooltips' final clause is visibly and textually different, and both explicitly name "Fetch" and "Backfill"

---

### UT-15 — Header blurb and caption name the Fetch→fills / Backfill→scores workflow (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded

**Steps:**
1. Read the paragraph directly beneath the "Per-date availability" heading
2. Scroll to the bottom of the calendar card and read the caption text below the grid

**Expected Result:**
- The header paragraph states: "Two separate signals per trading day: the cell fill is how many symbols have price data (filled by Fetch), and the ring is whether a scored snapshot exists (produced by Backfill). A day can have one without the other — that is exactly a Backfill gap."
- The caption states that cell fill is "filled by Fetch" and the ring is "produced by Backfill"
- Both texts explicitly use the words "Fetch" and "Backfill," each tied to its own signal

---

### UT-16 — Availability card degrades honestly if the API call fails (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Tester has browser DevTools access; either the backend process can be temporarily stopped, or DevTools' Network "block request URL" feature can be used — this is a tester-level check, not a plain-operator step

**Steps:**
1. Navigate to `http://localhost:3255/data` with the backend reachable, then open DevTools → Network tab
2. Block the `GET /api/data/availability` request (right-click it in the Network list → "Block request URL," or add a matching block-list pattern), or stop the backend process entirely
3. Refresh the page (F5)
4. Scroll to where the "Per-date availability" card is

**Expected Result:**
- The card shows the text "Availability could not load from the API. No cells are shown rather than fabricated values." — no fabricated or stale calendar cells are drawn
- The rest of the page (job-start form, sidebar navigation) still renders and remains usable — the failure is contained to this one card, never a blank page
- No uncaught JavaScript error dialog appears
- **Cleanup:** remove the DevTools block (or restart the backend) and refresh before continuing to other tests

---

### UT-17 — Required-still-passing J-01: `/stocks` leaderboard loads and Sector sort completes without crashing (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- None special

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to render
3. Click the word "Sector" in the column header row
4. Click "Sector" again

**Expected Result:**
- The table renders rows with columns including "Ticker", "Sector", "Leadership", "Entry Quality", "Risk"
- Both sector-sort clicks re-order the table visibly (an arrow indicator appears/flips next to "Sector")
- The page never goes blank and the left sidebar navigation remains visible and clickable throughout
- No browser console error appears

---

### UT-18 — Required-still-passing J-03: evidence status badges still read "Not yet proven" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded

**Steps:**
1. On `http://localhost:3255/stocks`, inspect the small text beneath the Leadership, Entry Quality, and Risk score badges for the first 5 visible rows

**Expected Result:**
- Every score on every inspected row shows the text "Not yet proven" directly beneath it
- No score is missing its status text, and none reads "Proven" or "PASS"

---

### UT-19 — Required-still-passing J-05: `/evidence` ledger page renders (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- None special

**Steps:**
1. Click "Evidence" in the left sidebar navigation
2. Wait for the page to load

**Expected Result:**
- The page loads at `http://localhost:3255/evidence` with the heading "Evidence" visible
- Either a "No certified claims yet" empty-state card renders, or a list of claim rows renders, each with a readable status badge and title
- No "Backend unavailable" card and no blank page

---

### UT-20 — Required-still-passing J-10: `/stocks/{ticker}` deep-history chart still renders (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- None special

**Steps:**
1. Navigate to `http://localhost:3255/stocks/NVDA` (or another long-tenured ticker)
2. Scroll to the "Price & moving averages" card
3. Click the "Full history" button (the right-hand option of the "Recent" / "Full history" toggle)

**Expected Result:**
- The chart re-renders with a wider date range extending back many years (well before 2020), with no blank chart area and no error
- The caption text next to the toggle buttons updates its "history since" date to reflect the extended range
- Clicking back to "Recent" restores the shorter window without error

---

### UT-21 — Required-still-passing J-12: universe size is consistent between `/methodology` and `/stocks` (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/methodology`, `/stocks`

**Preconditions:**
- None special

**Steps:**
1. Navigate to `http://localhost:3255/methodology` and note the universe/symbol count shown in the Universe Selection section
2. Navigate to `http://localhost:3255/stocks` and note the leaderboard's total row count (the "`{visible} / {total}`" indicator with no filters applied)

**Expected Result:**
- The universe count referenced on `/methodology` is consistent with the total shown on `/stocks` — the same underlying point-in-time universe is described on both pages, with no mismatch

---

### UT-22 — "Data Manager" is discoverable in 1 click from the Dashboard (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Preconditions:**
- None special

**Steps:**
1. Navigate to `http://localhost:3255/` (Dashboard)
2. Look at the left sidebar navigation (it lists Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology, Data Manager)
3. Click "Data Manager" (the last item, with a database icon)

**Expected Result:**
- "Data Manager" is visible in the sidebar without needing to scroll, on a normal desktop viewport
- Clicking it navigates directly to `http://localhost:3255/data` in a single click
- The "Data Manager" item becomes visually highlighted as the active nav entry once on `/data`

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads, required panels visible | smoke | P1 | `/data` |
| UT-02 | Job-kind picker: exactly 3 options, no Expand | smoke | P1 | `/data` |
| UT-03 | Fetch EOD prices now covers ~588-symbol pool | happy-path | P1 | `/data` |
| UT-04 | Backfill snapshots still starts and runs | regression | P1 | `/data` |
| UT-05 | Fetch + backfill still starts, no Universe-screen block | regression | P1 | `/data` |
| UT-06 | Import-source options never disabled, no cap suffix | validation | P2 | `/data` |
| UT-07 | No market-cap-ineligibility alert, any combination | validation | P2 | `/data` |
| UT-08 | Panel title + explainer paragraph read post-removal copy | ux | P2 | `/data` |
| UT-09 | Market-cap figures presented as static, not refreshable | ux | P3 | `/data` |
| UT-10 | Availability legend renders two labeled groups | happy-path | P1 | `/data` |
| UT-11 | Density top bucket is blue not amber; 6 steps distinct | happy-path | P1 | `/data` |
| UT-12 | Snapshot ring is violet not green | happy-path | P1 | `/data` |
| UT-13 | Hover readout shows "snapshot yes" in violet | happy-path | P2 | `/data` |
| UT-14 | Hover distinguishes Backfill-gap day from snapshotted day | happy-path | P1 | `/data` |
| UT-15 | Header blurb + caption name Fetch/Backfill workflow | ux | P2 | `/data` |
| UT-16 | Availability card degrades honestly on API failure | error | P2 | `/data` |
| UT-17 | J-01: `/stocks` Sector sort, no crash | regression | P1 | `/stocks` |
| UT-18 | J-03: "Not yet proven" badges intact | regression | P1 | `/stocks` |
| UT-19 | J-05: `/evidence` ledger renders | regression | P1 | `/evidence` |
| UT-20 | J-10: deep-history chart still renders | regression | P1 | `/stocks/{ticker}` |
| UT-21 | J-12: universe count consistent across pages | regression | P1 | `/methodology`, `/stocks` |
| UT-22 | "Data Manager" discoverable in 1 click from Dashboard | ux | P3 | nav / sidebar |

**P1 tests must all pass for browser QA verdict to be PASS.** P1 count: 14 (UT-01, 02, 03, 04, 05, 10, 11,
12, 14, 17, 18, 19, 20, 21) — these cover the two headline J-13 changes (Fetch-scope widening, unambiguous
legend/color/tooltip encoding) plus every required-still-passing regression journey (J-01/J-03/J-05/J-10/J-12)
and the two highest-risk dead-code-removal regressions (Backfill/Fetch+backfill still starting cleanly).
