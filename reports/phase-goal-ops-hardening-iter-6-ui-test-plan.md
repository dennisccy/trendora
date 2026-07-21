# Phase goal-ops-hardening-iter-6 — UI Test Plan

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-21
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context for the tester

This iteration is a **request-timing fix only** — no new page, button, form, label, or displayed value was
added or changed. Two below-the-fold widgets (`PhaseCrossViewCard` on `/` and the availability heatmap on
`/data`) now deliberately wait a short moment (250ms / 2500ms) after their page mounts before firing their
network request, so Chrome/backend contention clears before the request goes out. Visually the pages are
**identical** before and after this fix — what changed is only how fast the real data replaces the loading
skeleton/spinner, and (per the dev handoff) it is genuinely faster under real-browser conditions than before.

Two of the 11 J-06 pages (`/evidence` and `/research/event-study`) were found this iteration to be
**severely** over their load budget (up to ~9 minutes and ~92 seconds cold respectively) for reasons
**unrelated to this iteration's diff** — a pre-existing backend scaling regression discovered, not caused
or fixed, by this iteration's re-measurement pass. Test cases UT-13/UT-14 below document this so a tester
does not mistakenly file it as a new regression against this iteration.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Dashboard loads without errors, cross-view card present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh` (not `dev.sh`)
- Frontend running in prod mode via `scripts/start-frontend.sh` (not `dev.sh`), serving at
  `http://localhost:3255`
- Both services warm (readiness already settled to `ready`)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (up to 3 seconds)
3. Scroll down past the "Market Phase & Severity" card to the bottom of the page

**Expected Result:**
- Page renders without a blank screen or an "Application error" page
- The heading "Regime × phase cross-view" is visible on a card below the fold
- No browser console errors
- The card is NOT stuck showing only the grey `animate-pulse` skeleton block — within a couple of seconds
  it settles to either the rendered chart, an empty-state message ("No index history is available for this
  date."), or the error card ("Cross-view unavailable") — never an indefinite skeleton

---

### UT-02 — Dashboard cross-view chart loads within budget across 3 real-browser reloads (happy path / performance)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Same as UT-01
- Chrome DevTools available (Network tab)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Open Chrome DevTools → Network tab, filter the request list by typing `indexes?full=true`
3. Reload the page (F5) and note the "Time" column value for the `GET /api/indexes?full=true` request
4. Repeat step 3 two more times (3 reloads total), recording each measurement
5. Confirm the "Regime × phase cross-view" chart itself (not just the skeleton) is visible on-screen within
   ~1.5 seconds of each reload completing

**Expected Result:**
- All 3 reload measurements for `GET /api/indexes?full=true` are ≤ 1500ms (the dev handoff's own measured
  range is 821–872ms, well inside budget)
- The `animate-pulse` grey skeleton block is visible immediately on each reload (never a blank gap) and is
  replaced by the actual chart shortly after — the operator should never see a frozen or empty panel
- The chart's "as of `<date>`" label in the card header shows a real date, not blank

---

### UT-03 — Dashboard cross-view card shows an honest error state when the backend is unreachable (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running and reachable at `http://localhost:3255`
- Backend is STOPPED (kill the `scripts/start-backend.sh` process) before step 1

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3255/`
2. Scroll to the "Regime × phase cross-view" card
3. Wait up to 5 seconds

**Expected Result:**
- The card shows the amber-bordered error state with the heading "Cross-view unavailable" and the message
  "The index or market-phase series could not load from the API. Nothing is fabricated — confirm the
  backend is running and reload."
- The card is never blank and never stuck on the loading skeleton indefinitely
- (Restart the backend via `scripts/start-backend.sh` after this test before continuing to the next test case)

---

### UT-04 — Dashboard cross-view card survives a rapid as-of toggle mid-fetch without a blank/frozen frame (regression — abort handling)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend running in prod mode, warm
- At least 2 selectable historical dates exist (the top-bar "Previous available date" button is enabled)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Scroll to the "Regime × phase cross-view" card so it is visible
3. Immediately (within ~1 second of the page starting to load, before the card has finished loading) click
   the "◀" button in the top bar (`aria-label="Previous available date"`) twice in quick succession
4. Watch the "Regime × phase cross-view" card continuously through this transition
5. Wait for the card to settle (up to 3 seconds after the last click)

**Expected Result:**
- At every moment during the transition, the card shows one of: the `animate-pulse` grey skeleton, the
  rendered chart, or an empty/error message — it is NEVER a blank white/empty panel and never visibly
  "frozen" showing stale data from before the date change
- The amber "Viewing as-of `<date>` (historical)" badge in the top bar updates to reflect the two steps back
- After settling, the card's "as of `<date>`" label matches the newly selected historical date, and the
  chart reflects that date (not the original date's data)

---

### UT-05 — Existing Dashboard cards still render correctly, unaffected by the fetch-timing change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend and frontend running in prod mode, warm

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (3 seconds)
3. Observe the cards ABOVE the "Regime × phase cross-view" card: the market snapshot/summary card, the
   "Market Phase & Severity" card, and any sector/theme summary cards on the page

**Expected Result:**
- Every card above the cross-view card renders its data normally (numeric values, phase label, severity
  reading) with no loading spinner stuck indefinitely and no error card
- None of these cards show a blank or delayed-blank state as a side effect of the cross-view card's added
  250ms deferral — they are unrelated code paths and must be unaffected

---

### UT-06 — Regime × phase cross-view chart is discoverable, and its Hide/Show toggle works (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Backend and frontend running in prod mode, warm

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Scroll down to find the "Regime × phase cross-view" card (no more than one scroll gesture from the
   Market Phase card)
3. Click the "Hide" button in the top-right of the card
4. Observe the card collapses to a small dashed-border button reading "Show regime × phase cross-view"
5. Click that button again

**Expected Result:**
- Step 2: The card is found without needing to search — its heading "Regime × phase cross-view" with a
  layers icon is clearly labeled
- Step 3–4: Clicking "Hide" replaces the full card with the small "Show regime × phase cross-view" button —
  no fetch is triggered while hidden
- Step 5: Clicking "Show regime × phase cross-view" again re-mounts the card, shows the loading skeleton
  briefly, then the chart reloads and displays normally (confirms the deferred-fetch effect re-arms cleanly
  on re-enable, not just on first page mount)

---

### UT-07 — Data Manager loads without errors, availability heatmap present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend and frontend running in prod mode, warm

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load (up to 3 seconds)
3. Scroll to the "Dataset coverage" panel and continue scrolling until the calendar-grid heatmap panel is
   visible (it sits below the "Rebuild snapshots for current universe" panel and above "Missing data")

**Expected Result:**
- Page renders without a blank screen or an "Application error" page
- The "Data Manager" heading is visible at the top
- The availability heatmap panel is present; while its data is still loading it shows a spinning icon and
  the text "Loading availability…" — never a blank gap in its place
- No browser console errors

---

### UT-08 — Data Manager availability heatmap loads within budget across 3 real-browser reloads (happy path / performance)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Same as UT-07
- Chrome DevTools available (Network tab)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Open Chrome DevTools → Network tab, filter the request list by typing `data/availability`
3. Reload the page (F5) and note the "Time" column value for the `GET /api/data/availability` request
4. Repeat step 3 two more times (3 reloads total), recording each measurement
5. Confirm the heatmap grid of colored day-cells (not just the spinner) is visible on-screen within
   ~2.5–3 seconds of each reload

**Expected Result:**
- All 3 reload measurements for `GET /api/data/availability` are ≤ 1500ms (the dev handoff's own measured
  range is 1000–1052ms, inside budget)
- The `Loader2` spinning icon plus "Loading availability…" text is visible for roughly the first 2.5
  seconds of each reload (the intentional deferral window) — this is expected and NOT a bug; the heatmap
  never shows a blank panel during this wait
- After the wait, the heatmap grid renders with colored day-cells and a legend at the bottom

---

### UT-09 — Availability heatmap shows an honest error state when the backend is unreachable (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend running and reachable at `http://localhost:3255`
- Backend is STOPPED before step 1

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3255/data`
2. Scroll to the availability heatmap panel
3. Wait at least 3 seconds (past the 2.5s deferral window, so the fetch has had a chance to fire and fail)

**Expected Result:**
- The rest of the page shows the "Backend unavailable" error card ("Dataset coverage could not load from
  the API...") since the overview fetch also fails
- The heatmap area, once its own deferred fetch fails, shows the text "Availability could not load from the
  API. No cells are shown rather than fabricated values." — never a blank grid and never fabricated cells
- (Restart the backend via `scripts/start-backend.sh` after this test before continuing)

---

### UT-10 — Weekend-only backfill produces a "no new snapshots" persisted run-history entry (regression — mirrors the fixed J-01 golden script)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend and frontend running in prod mode, warm
- No job is currently running on `/data` (the "Start" button is enabled, not showing "Job running…")

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, type `2026-05-02` into the "Start date" field
3. Type `2026-05-03` into the "End date" field (leave "Job kind" at its default, "Backfill snapshots")
4. Click the "Start" button
5. Wait for the live job card to show a terminal status (no longer "running"); this run should report
   "2 non-trading" days somewhere in its summary text
6. Reload the page (`http://localhost:3255/data`)
7. Scroll to the "Run history" table at the bottom of the page

**Expected Result:**
- Step 5: the job completes without error; text "2 non-trading" appears (confirming both dates in the range
  were non-trading days, so zero snapshots were created)
- Step 7: the top row of the "Run history" table (this run, most recent) shows the date range
  `2026-05-02 → 2026-05-03`, kind "backfill", and a status badge reading **"no new snapshots"** (a neutral
  grey badge, NOT the same green "ok" badge a productive run gets)
- This is exactly the persisted entry the rewritten `J-01.json` golden script step 6 now asserts against
  (previously it asserted a stale, unrelated `/scanner-runs` date) — reloading `/data` and finding "no new
  snapshots" in this run's own history row is the manual equivalent of that automated check

---

### UT-11 — Job start form still blocks submission with an invalid or empty date (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Backend and frontend running in prod mode, warm
- No job is currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, clear the "Start date" field and type `2026-13-40` (an
   invalid calendar date)
3. Observe the field and the "Start" button
4. Clear the "Start date" field entirely (leave it blank) and leave "End date" blank too

**Expected Result:**
- Step 3: a red inline error message "Enter a valid date as yyyy-MM-dd" appears directly below the "Start
  date" field, and the "Start" button is disabled (greyed out, not clickable)
- Step 4: with both fields empty, the "Start" button remains disabled (no error text needed for an
  untouched empty field, but the button stays non-submittable)
- This confirms the pre-existing form validation this iteration's fetch-timing change did not touch is
  still intact

---

### UT-12 — Availability heatmap legend and labels remain clear and discoverable (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Backend and frontend running in prod mode, warm
- Availability heatmap has finished loading (wait ~3 seconds after page load)

**Steps:**
1. Navigate to `http://localhost:3255/data` and wait for the heatmap to finish loading
2. Look at the bottom of the heatmap panel for a legend
3. Hover over (or click) any colored day-cell in the grid

**Expected Result:**
- A legend with labeled swatches ("none", "<25%", "25–50%", "50–75%", "75–<100%", "full") is visible below
  the calendar grid, explaining what the cell colors mean
- Hovering/clicking a cell shows a tooltip or readout with the exact date, symbols-with-bars count, and
  whether a snapshot exists for that day — a new user can understand what the heatmap represents without
  needing developer documentation

---

### UT-13 — Evidence Ledger (`/evidence`) known pre-existing slow-load issue (regression / known-issue — NOT caused by this iteration)

**Type:** regression
**Priority:** P3
**Surface:** `/evidence`

**Preconditions:**
- Backend and frontend running in prod mode
- Backend has a cold cache for this endpoint (freshly restarted, or this is the first `/evidence` visit
  since the last backfill/rebuild)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Time how long the main data panel takes to populate

**Expected Result:**
- **This page is currently expected to take several minutes to load on a cold cache** (555.97s / ~9.3
  minutes measured this iteration via direct backend call, versus ~9.3–9.6s recorded as of iter-5) — this
  is a pre-existing backend scaling regression, discovered while re-measuring for this iteration but caused
  by neither this iteration's code nor its diff (no file under `apps/frontend/app/evidence/` or any backend
  module was touched this iteration)
- Do NOT file this as a new bug caused by this iteration's Dashboard/Data Manager fetch-timing fix — it is
  a known, already-flagged issue awaiting a dedicated follow-up iteration
- The page must still eventually load correctly (not crash, not show a garbled error) once the wait
  completes — only the wait time is out of budget, not the correctness of the result

---

### UT-14 — Research Event-Study lab (`/research/event-study`) known pre-existing slow-load issue (regression / known-issue — NOT caused by this iteration)

**Type:** regression
**Priority:** P3
**Surface:** `/research/event-study`

**Preconditions:**
- Backend and frontend running in prod mode
- Backend has a cold cache for this endpoint

**Steps:**
1. Navigate to `http://localhost:3255/research/event-study` (the "Episodes" overlap view loads by default)
2. Time how long the results panel takes to populate
3. Once loaded, reload the page again (warm/cached path this time) and time it again

**Expected Result:**
- Step 2 (cold): expect roughly 92 seconds to first render (versus ~0.003–0.005s recorded as of iter-5) —
  same root cause as UT-13, unrelated to this iteration's diff
- Step 3 (warm): expect roughly 1.46 seconds — still regressed from the prior near-instant warm reads, but
  far better than the cold path
- Do NOT file this as a new bug caused by this iteration's fix — it is a known, already-flagged issue

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads, cross-view card present | smoke | P1 | `/` |
| UT-02 | Cross-view chart within budget, 3 reloads | happy-path | P1 | `/` |
| UT-03 | Cross-view honest error state, backend down | error | P2 | `/` |
| UT-04 | Cross-view survives rapid as-of toggle | regression | P1 | `/` |
| UT-05 | Other Dashboard cards unaffected | regression | P1 | `/` |
| UT-06 | Cross-view discoverable, Hide/Show toggle | ux | P2 | `/` |
| UT-07 | Data Manager loads, heatmap present | smoke | P1 | `/data` |
| UT-08 | Heatmap within budget, 3 reloads | happy-path | P1 | `/data` |
| UT-09 | Heatmap honest error state, backend down | error | P2 | `/data` |
| UT-10 | Weekend backfill → "no new snapshots" history entry | regression | P1 | `/data` |
| UT-11 | Job form blocks invalid/empty dates | validation | P2 | `/data` |
| UT-12 | Heatmap legend/tooltip discoverable | ux | P2 | `/data` |
| UT-13 | `/evidence` known pre-existing slow load | regression | P3 | `/evidence` |
| UT-14 | `/research/event-study` known pre-existing slow load | regression | P3 | `/research/event-study` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-13/UT-14 are P3/informational — they are
expected to currently FAIL the ≤1.5s budget and must not be scored against this iteration's fix.
