# Phase goal-ops-hardening-iter-13 — UI Test Plan

**Phase:** goal-ops-hardening-iter-13
**Date:** 2026-07-23
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope note

This iteration touches zero files under `apps/frontend/`. The only user-visible effect is (1) a
latency improvement on an existing on-mount API call shared by two existing pages, and (2) one new
possible word ("index series") inside an existing generic "Refreshed: ..." summary line on `/data`.
No new page, button, form, or navigation target exists. Test cases below are drawn from
`reports/phase-goal-ops-hardening-iter-13-ui-surface-map.md`'s 5 affected rows, plus regression
checks on the two most closely related surfaces that were explicitly NOT changed this iteration
(the `/` "Major indexes & regime" card's range-preset selector, and every other page's boot time).

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Dashboard (`/`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3255`, backend at `http://localhost:8255`
- No login is required (no auth in this product)
- Backend has completed at least one ingest run so `IndexSeriesCache` has a warmed row for the
  default hot key (operator confirms via `logs/backend.log` — look for a completed
  `_refresh_ingest_aggregates` run with no error)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (network idle)

**Expected Result:**
- Page renders — no blank screen, no Next.js error overlay, no "Application error" text
- The "Major indexes & regime" card heading is visible
- Below it, the second synced chart card (no separate heading required, but two chart panes
  stacked vertically) is visible
- Browser DevTools Console shows no red error entries
- Neither card is stuck showing only its loading skeleton (a pulsing gray placeholder) — both
  resolve to either data or an explicit error/empty message within a few seconds

---

### UT-02 — Data Manager (`/data`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load (network idle)

**Expected Result:**
- Page renders — no blank screen, no Next.js error overlay
- A card titled "Index & benchmark data provenance" is visible (this is the panel with
  `data-testid="index-vendor-panel"`)
- A card titled "Start a fetch / backfill job" is visible further down the page
- Browser DevTools Console shows no red error entries
- The "Index & benchmark data provenance" card does not remain stuck on its loading skeleton
  (`data-testid="index-vendor-loading"`) — it resolves to a populated table within a few seconds

---

### UT-03 — `GET /api/indexes?full=true` lands within budget on three fresh `/data` loads (happy path / performance)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `IndexSeriesCache` has a warmed row for the default hot key (`range_key="all"`, `full=true`) —
  operator confirms via `logs/backend.log` showing a completed ingest finalize run
- No concurrent ingest job is running at test time — confirm via `logs/backend.log` (no
  "starting" / "finalize" entries in the last few minutes) and via `/data`'s own "Job progress"
  panel showing no job in the "running" state
- Host is verifiably idle: `logs/hwmon/hwmon.csv`'s most recent row shows `load1 < 2.0`
- This test requires exactly this iteration's canonical acceptance measurement (per goal.md J-06);
  it is the single most important check in this whole plan

**Steps:**
1. Open a NEW Chrome browser tab (do not reuse an already-open `/data` tab)
2. Open DevTools → Network tab → check "Disable cache"
3. In the address bar, type `http://localhost:3255/data` and press Enter (a fresh navigation, not
   a page refresh of an existing tab)
4. In the Network tab, locate the request row for `indexes?full=true` (filter by typing "indexes"
   in the Network tab's filter box if needed)
5. Read that row's "Time" column value (the total Resource Timing duration for the request)
6. Record the value, then note the exact wall-clock time of this reading
7. Close the tab completely (not just navigate away)
8. Repeat steps 1–7 two more times, for three independent fresh-navigation readings total
9. For each of the three recorded wall-clock times, check `logs/hwmon/hwmon.csv` for the row at or
   immediately preceding that timestamp and read its `load1` value

**Expected Result:**
- All three recorded "Time" values for `GET /api/indexes?full=true` are **≤ 1500ms**
- All three corresponding `logs/hwmon/hwmon.csv` `load1` readings are **< 2.0**
- The "Index & benchmark data provenance" table on the page shows the same set of rows/values
  across all three loads (no missing symbols, no "—" appearing where a value was present before)

**What "broken" looks like:** any one of the three readings shows ≥1500ms in the Network tab's
Time column, or `load1 ≥ 2.0` at that timestamp (which invalidates that specific reading and it
must be retaken on a verifiably idle host, not discarded silently).

---

### UT-04 — `GET /api/indexes?full=true` lands within budget on a fresh Dashboard (`/`) load (happy path / performance spot-check)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Same host-idle and no-concurrent-ingest preconditions as UT-03

**Steps:**
1. Open a NEW Chrome browser tab
2. Open DevTools → Network tab → check "Disable cache"
3. Navigate to `http://localhost:3255/` (fresh navigation)
4. In the Network tab, locate the request row for `indexes?full=true`
5. Read that row's "Time" column value
6. Note the exact wall-clock time of this reading and cross-check `logs/hwmon/hwmon.csv`'s
   `load1` value at/before that timestamp

**Expected Result:**
- The recorded "Time" value for `GET /api/indexes?full=true` is **≤ 1500ms**
- `logs/hwmon/hwmon.csv` `load1` < 2.0 at that timestamp
- The "Major indexes & regime" card and the synced two-pane chart below it both render index lines
  (not stuck on skeleton, not an error state)

**What "broken" looks like:** the Network tab's Time value for this request is ≥1500ms, or the
request never appears (indicates the card's request never fired — check DevTools Console for a
thrown error first).

---

### UT-05 — Index vendor panel content is unchanged after the cache fix (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loads successfully (UT-02 passing)
- A pre-iteration screenshot or row listing of the "Index & benchmark data provenance" table is
  available for comparison (if not available, this test instead confirms internal consistency:
  every configured symbol either shows a vendor + first-bar date or an honest "—")

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the "Index & benchmark data provenance" card to finish loading
3. Read every row of its table: the Symbol/Name column, the Vendor column, and the first-bar-date
   column
4. Confirm the row count matches the 10 configured `index_chart.symbols` entries (SPY, QQQ, IWM,
   RSP, DIA, ^SPX, ^NDX, ^DJI, ^VIX, ^TNX) — a symbol with no stored bars (e.g. DIA, if not yet
   fetched) is allowed to be honestly omitted, never fabricated
5. Confirm no row shows a blank/undefined vendor cell — each shows either a named vendor (Stooq /
   Yahoo / FRED-macro proxy) or an explicit "—"

**Expected Result:**
- Table content, vendor labels, and first-bar dates match what a pre-iteration reading would show
  (byte-identical data per the dev handoff's own direct-vs-cached comparison) — this test confirms
  the speed fix introduced no data corruption or truncation
- No console error, no "Vendor disclosure unavailable" warning box appears

---

### UT-06 — Dashboard cross-view chart content is unchanged after the cache fix (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- `/` loads successfully (UT-01 passing)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the "Major indexes & regime" card to finish loading
3. Read the "as of [date]" text shown next to the card title
4. Hover over the chart's rightmost data point for any one plotted index line and read its
   tooltip value
5. Scroll down to the second, synced two-pane chart card below it and confirm it also renders
   index lines with the same as-of date context

**Expected Result:**
- The "as of [date]" text shows today's (or the most recent trading day's) date, not a stale or
  blank date
- The chart displays index lines for the configured symbols with no "N/A" or empty legend entries
  where data previously existed
- Both the top card and the lower synced two-pane card show consistent index data (same lines
  present in both)

---

### UT-07 — Non-default range preset still works on Dashboard (regression — confirms non-hot-key path unaffected)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- `/` loads successfully with the "Major indexes & regime" card visible
- The card's default range is "All" (the newly-cached hot key)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the "Major indexes & regime" card to finish its initial load (chart lines visible,
   range selector showing "All")
3. Click the "Range preset" dropdown (labeled via `aria-label="Range preset"`, showing "All" by
   default) in the card's top-right corner
4. Select "3M" from the dropdown
5. Wait for the chart to re-render

**Expected Result:**
- The chart re-renders with a visibly shorter time window (approximately the last 3 months of
  data instead of full history) — the x-axis range visibly shrinks
- No error message appears; the card does not fall back to its error or empty state
- The "as of [date]" label next to the card title still shows a valid date
- This confirms the explicit non-default `range=3M` request still uses the unchanged, uncached
  code path exactly as before this iteration (per TC-6 in the functional test plan) — from the
  operator's perspective, simply: switching ranges still works correctly and instantly reflects a
  different (shorter) window of data.

---

### UT-08 — "Refreshed: ..." line includes "index series" after an ingest run that lands a new index-symbol bar (happy path — new information displayed)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` is loaded in a fresh tab (no job started yet this browser session)
- Operator has identified (or can trigger) a bounded fetch/backfill run that lands a new price bar
  for one of the configured `index_chart.symbols` (e.g. SPY) — a small, bounded job only, never a
  full-universe rebuild (per AG-10)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" card, type a valid start date (e.g. `2026-07-20`) into
   the "Start date" field
3. Type a valid end date one or more calendar days later (e.g. `2026-07-22`) into the "End date"
   field
4. From the "Job kind" dropdown, select "Fetch EOD prices" (or "Fetch + backfill" if a snapshot is
   also desired)
5. Click the "Start" button (shows a spinning icon and reads "Job running…" once clicked)
6. Wait for the "Job progress" panel above the form to show the job's status change from
   "running" to a terminal status (e.g. a green "ok" badge)
7. Read the "Refreshed: ..." line under the job's breakdown counts (`data-testid=
   "aggregates-refreshed"`)

**Expected Result:**
- The "Job progress" panel's "Refreshed: ..." line appears and its comma-separated list includes
  the item "index series" (rendered from the backend's `"index_series"` value with underscores
  converted to spaces) — but ONLY if the fetched date range actually landed a new bar for one of
  the 10 configured index-chart symbols
- If the job did not touch any configured index-chart symbol's bars (e.g. it only fetched a
  non-index symbol), the "Refreshed: ..." line still appears but does NOT include "index series" —
  this is the honest, gated behavior; do not treat its absence as a bug in that case

**What "broken" looks like:** "index series" appears in the "Refreshed: ..." line even when the
job's date range did NOT introduce any new bar for a configured index symbol (a fabricated/always-
on value), or the job's terminal status becomes "failed" as a side effect of this new warm step.

---

### UT-09 — "Refreshed: ..." line honestly omits "index series" for an unrelated run, per Run History row (regression / honesty check)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- At least two runs exist in the Run History table: one that touched a configured index-chart
  symbol's bars (from UT-08) and at least one earlier run that did not

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll down to the "Run history" table (bottom of the page)
3. Locate the row corresponding to the job started in UT-08 (match by its "Started" timestamp)
4. Read that row's "Snapshots" column breakdown text (includes the "Refreshed: ..." sub-line)
5. Locate a different, earlier row whose date range does not overlap any configured index-chart
   symbol's missing bars (e.g. a run that only touched non-index symbols, or one dated before this
   iteration's fix was deployed)
6. Read that row's "Refreshed: ..." sub-line, if present

**Expected Result:**
- The UT-08 run's row includes "index series" in its "Refreshed: ..." text
- The unrelated earlier row's "Refreshed: ..." text (if shown at all) does NOT include "index
  series" — confirming the honest, per-run gating holds at the table level, not just for the
  newest run

---

### UT-10 — "Refreshed: ..." wording remains clear and readable with the new item (UX)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- A run whose "Refreshed: ..." line includes "index series" is visible (from UT-08), ideally
  alongside several other refreshed items (e.g. "latest snapshot, coverage, membership timeline,
  market phase, research hot keys, index series")

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Job progress" panel (or the Run History row) showing the fullest "Refreshed: ..."
   list available
3. Read the full line without any developer context

**Expected Result:**
- The line reads as a plain, comma-separated, lower-case, space-separated phrase list (e.g.
  "Refreshed: latest snapshot, coverage, membership timeline, market phase, research hot keys,
  index series") — "index series" reads as an ordinary plain-English item indistinguishable in
  styling from any other item in the list (same font size/color, no new badge, icon, or emphasis)
- No raw underscore (`index_series`) or camelCase artifact is visible anywhere in the rendered text
- The item is understandable to a non-developer as referring to "the index chart data," even
  without documentation

---

### UT-11 — Backend-error state on the vendor panel remains unchanged (error handling regression)

**Type:** error
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- Operator can simulate a backend-unavailable condition (e.g. this check is performed opportunistically
  if the backend is briefly restarting for this iteration's own deployment, per the pump note; do NOT
  stop the backend solely to run this test — observe naturally if a restart window occurs)

**Steps:**
1. While the backend is not reachable (e.g. immediately after an operator-initiated restart, before
   it re-accepts connections), navigate to `http://localhost:3255/data`
2. Observe the "Index & benchmark data provenance" card's state

**Expected Result:**
- The card shows the warning box "Vendor disclosure unavailable" with the message "Could not load
  the index series from the API. Nothing is fabricated — confirm the backend is running and
  reload." — exactly this pre-existing wording, unchanged by this iteration
- No blank page, no unhandled crash/white screen
- Once the backend is reachable again, reloading the page recovers to the normal populated table
  (confirms this iteration did not regress the pre-existing error boundary)

**Note:** if no natural backend-down window occurs during this test pass, mark this test
"not exercised this run" rather than fabricating a result — do not force a backend restart solely
to test this (services in this session are restarted only by the operator, per this iteration's
pump note).

---

### UT-12 — Other in-budget pages show no regression (spot-check)

**Type:** regression
**Priority:** P2
**Surface:** multiple (spot-check only, per goal.md's explicit "do not re-run the full sweep")

**Preconditions:**
- `reports/perf-budgets.md` lists 10 other pages/endpoints already confirmed in-budget as of
  iter-11/iter-12, unrelated to this iteration's change
- Host is verifiably idle (same as UT-03)

**Steps:**
1. Open DevTools → Network tab → check "Disable cache"
2. Fresh-navigate to `http://localhost:3255/evidence`
3. Read the page's overall load completion time (DOMContentLoaded or the slowest tracked request,
   per `reports/perf-budgets.md`'s own methodology for this page)
4. Compare against the budget value recorded for `/evidence` in `reports/perf-budgets.md`

**Expected Result:**
- `/evidence`'s measured time remains within its committed budget in `reports/perf-budgets.md` (no
  new regression introduced by this iteration's backend changes, which did not touch this page's
  own endpoints)
- Page renders normally with no console errors

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads without errors | smoke | P1 | `/` |
| UT-02 | Data Manager loads without errors | smoke | P1 | `/data` |
| UT-03 | Hot-key latency ≤1.5s, 3 fresh `/data` loads | happy-path | P1 | `/data` |
| UT-04 | Hot-key latency ≤1.5s, `/` spot-check | happy-path | P1 | `/` |
| UT-05 | Vendor panel content unchanged | regression | P1 | `/data` |
| UT-06 | Dashboard chart content unchanged | regression | P2 | `/` |
| UT-07 | Non-default range preset still works | regression | P1 | `/` |
| UT-08 | "index series" appears in Refreshed line | happy-path | P2 | `/data` |
| UT-09 | "index series" honestly omitted elsewhere | regression | P2 | `/data` |
| UT-10 | Refreshed line reads clearly | ux | P3 | `/data` |
| UT-11 | Vendor-panel error state unchanged | error | P3 | `/data` |
| UT-12 | `/evidence` spot-check, no regression | regression | P2 | `/evidence` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-03 and UT-04 are the canonical
J-06 acceptance measurements for this iteration — per goal.md's own lesson (iter-12), score on the
actual number, never round a marginal miss into "close enough." If any of UT-01, UT-02, UT-03,
UT-04, UT-05, or UT-07 fails, the overall verdict must be FAIL/PARTIAL regardless of how the other
tests read.
