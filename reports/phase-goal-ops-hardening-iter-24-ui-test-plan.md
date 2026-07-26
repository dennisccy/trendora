# Phase goal-ops-hardening-iter-24 — UI Test Plan

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context for the tester

This iteration is a **read-only disclosure** feature — no new buttons, forms, or navigation. It surfaces
the existing in-process "background compute" (a historical forward-aggregate calculation the backend
already runs when `/backtest` is asked for a historical date whose evidence isn't cached yet) in two
places:

1. A small badge next to the top-bar readiness pill (`data-testid="background-compute-indicator"`),
   visible on **every page**, reading "background compute running (N)".
2. A new **"Background compute"** panel on the **Data Manager page (`/data`)**.

### Two timing facts that shape every test below — read this before running anything

- **The badge/panel only refresh on the shared health poll.** Once the backend reports readiness as
  `"ready"` (the normal case), that poll backs off to a **30-second idle cadence**
  (`startup.health_poll_idle_interval_seconds` in `config.yaml`) — it does NOT poll every 1-2 seconds.
  A background-compute window commonly finishes in 10-60 seconds, so it is easy to trigger one and then
  "miss" it just by not waiting long enough, or to have it start and finish silently between two 30-second
  polls. **A full page reload (F5) forces an immediate fresh poll** (the poll timer restarts on mount) —
  use that instead of passively watching, and re-check a couple of times over ~30-60s rather than giving
  up after one look.
- **Triggering a real window requires picking a historical as-of date whose forward-aggregate evidence is
  NOT already cached for the current dataset version.** There is no fixed date guaranteed to work in every
  environment — step through a few different historical dates with the "Previous available date" (◀)
  button if the first one you try doesn't produce a badge (a date that was already visited earlier in this
  session, or already computed, will NOT re-trigger a window — that's correct behavior, not a bug).

### Screenshot/capture guidance (read before any browser-QA capture step)

The new `BackgroundComputePanel` is the **very last panel** on `/data`, appended after Coverage, Storage
Capacity, Drift Report, Rebuild, Universe Diagnostics, Membership Timeline, Backward History, Availability
Heatmap, Missing Data, Macro Feed, Index Vendor, Job Form/Job Progress, Unfinished Imports, Remove Data,
and Run History — a very long page. **It renders far below the fold.** A viewport-only screenshot taken at
the top of `/data` will NOT capture it and will look identical before/after the feature exists. For every
step below that references the "Background compute" panel:
- Scroll to the bottom of the page (or use an element-scoped capture targeting
  `[data-testid="background-compute-panel"]`) before taking any screenshot.
- When comparing "before" vs "after" frames (e.g. active row present vs. gone, elapsed time increasing),
  take a full-page or element-scoped capture each time and diff/md5-compare the actual pixels of that
  region — a viewport screenshot of the page header will produce two byte-identical, useless images.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Global header loads with readiness pill intact, no console errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (root layout — applies to every page)

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load
3. Inspect the sticky header in the top-right corner (right of the as-of calendar control)

**Expected Result:**
- Page renders — no blank screen, no error boundary text
- An element with `data-testid="readiness-badge"` is visible, showing one of: "Checking backend…",
  "Ready", "Initializing… history X/Y", "Snapshot pending", or "Backend unavailable"
- No `data-testid="background-compute-indicator"` element is present (no background compute has been
  triggered yet in this session)
- No console errors

---

### UT-02 — Triggering a historical backtest starts a real background-compute window, badge appears (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Backend is running; readiness pill shows "Ready"
- At least several historical snapshot dates exist in the as-of switcher

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Confirm the badge next to the calendar icon in the top-right header reads "Latest" (`data-testid="asof-indicator"`)
3. Click the "◀" button (`data-testid="asof-step-prev"`, `aria-label="Previous available date"`) once
4. Confirm the badge now reads "Viewing as-of `<date>` (historical)" in amber/warn styling
   (`data-testid="asof-indicator"`, `data-state` implied by the amber `History` icon)
5. Wait 3 seconds, then reload the page (press F5)
6. Look at the header row: check for a new badge reading "background compute running (1)"
   (`data-testid="background-compute-indicator"`) appearing immediately to the right of the readiness pill
7. If the badge is NOT present after step 6, click "◀" again to move to an older date, repeat steps 5-6
   (try up to 5 different historical dates before concluding the feature is broken — some dates will
   already be cached from earlier testing and will correctly NOT trigger a new window)

**Expected Result:**
- Within a few attempts, a historical date is found where `data-testid="background-compute-indicator"`
  appears, reading exactly "background compute running (1)"
- The existing readiness pill (`data-testid="readiness-badge"`) is still visible alongside it, unchanged —
  the new badge sits next to the pill, never replacing or hiding it
- The `/backtest` scorecard for that date still loads (or shows its own loading/skeleton state) within the
  existing response-time budget — the page does not hang or error while the background compute proceeds

---

### UT-03 — /data "Background compute" panel shows live active-window detail (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- A background-compute window is currently in flight (immediately continue from UT-02 step 6/7 — as soon
  as the badge appears, move to this test before the window completes)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll all the way to the bottom of the page (this panel is the LAST one on the page — see the capture
   guidance above; a top-of-page screenshot will NOT show it)
3. Locate the panel titled "Background compute" (`data-testid="background-compute-panel"`)
4. Within it, locate one row with `data-testid="background-compute-active-row"`
5. Read the three pieces of information on that row
6. Wait 5 seconds, reload the page (F5), scroll to the bottom again, and re-read the same row

**Expected Result:**
- Step 5: the row shows a badge "as-of `<date>`" (`data-testid="background-compute-asof"`, matching the
  date picked in UT-02), text "elapsed `<N>`s" or "elapsed `<N>`ms" (`data-testid="background-compute-elapsed"`)
  with a value greater than 0, and text "horizons `<X>`/`<Y>`" (`data-testid="background-compute-horizons"`)
  where X is less than Y
- Step 6 (after reload): the elapsed value has INCREASED from step 5's reading; the horizons "done" count
  (X) has stayed the same or INCREASED — it never decreases and never exceeds Y
- No fabricated finish-time or completion-percentage text appears anywhere on the row (only the real
  elapsed time and the real horizons-done/total counts)

---

### UT-04 — /data panel shows the honest idle message when nothing has ever run (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- No background compute has been triggered since the backend process currently running was started (use a
  freshly started backend, or run this check before UT-02/UT-03 in your session)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the bottom of the page
3. Locate the "Background compute" panel (`data-testid="background-compute-panel"`)

**Expected Result:**
- The panel shows the exact text "No background compute running. Last outcome: none yet."
  (`data-testid="background-compute-idle"`)
- No active-row list and no "Last outcome" section are rendered
- The panel does NOT appear blank or show a loading spinner indefinitely

---

### UT-05 — Last-outcome summary appears once the triggered window finishes (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- The background-compute window triggered in UT-02 has finished (the badge from UT-02 step 6 is no longer
  present on any page after a page reload)

**Steps:**
1. Navigate to `http://localhost:3255/data`, scroll to the bottom
2. Locate the "Background compute" panel and the "Last outcome" label inside it
3. Read the row below that label (`data-testid="background-compute-last-outcome"`)

**Expected Result:**
- No `data-testid="background-compute-active-row"` is present anymore (the active window ended)
- A badge reading "Completed" is visible, styled in the "ok"/success color (green-family) — note the raw
  DOM text is the lowercase word "completed"; it is visually capitalized to "Completed" by CSS
  (`className="capitalize"`), so a case-sensitive text check should look for "completed" while a visual
  screenshot will show "Completed"
- Text "as-of `<same date selected in UT-02>`" is visible
- A non-zero duration value is visible (e.g. "12.3s")
- No failure-reason text is shown (reason text only appears when the outcome failed — see UT-07 for the
  failed-state look, which requires a backend-side fault injection, not reproducible from the UI alone)

---

### UT-06 — Numeric fields never render fabricated or malformed values (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Either an active row (UT-03) or a last-outcome row (UT-05) is currently visible

**Steps:**
1. On `/data`, scrolled to the "Background compute" panel, inspect every numeric value shown: the elapsed
   time, the horizons X/Y pair, and the last-outcome duration

**Expected Result:**
- None of these values ever render as "NaN", "undefined", "Infinity", "null", or a negative number
- Elapsed time and duration are always shown with a unit suffix (e.g. "3.2s", "1m 5s", or "450ms") — never
  a bare unformatted number
- The horizons "done" count is never greater than the horizons "total" count

---

### UT-07 — Backend-unavailable state degrades the badge and panel honestly, no crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/` and `/data`

**Preconditions:**
- Tester has access to stop and restart the backend process

**Steps:**
1. Stop the backend process
2. Navigate to (or reload) `http://localhost:3255/`
3. Wait up to 5 seconds
4. Navigate to `http://localhost:3255/data` and scroll to the bottom
5. Restart the backend process
6. Reload `http://localhost:3255/` and then `http://localhost:3255/data`

**Expected Result:**
- Step 3: the readiness pill flips to `data-testid="readiness-badge"` with `data-state="unavailable"`,
  reading "Backend unavailable" in danger/red styling
- Step 3: no `data-testid="background-compute-indicator"` badge is shown (it should never claim an active
  compute window while the backend itself is unreachable)
- Step 4: `/data` does not show a blank page or an unhandled-exception screen — the "Background compute"
  panel either shows its last-known idle/active state or degrades to the idle copy; the page around it
  (other panels) still renders
- Step 6 (after restart): the readiness pill returns to "Ready" (or briefly "Initializing…"); the
  "Background compute" panel now shows "No background compute running. Last outcome: none yet." again —
  confirming the in-memory history does NOT survive a restart (this is documented behavior, not a bug —
  see UT-08)

---

### UT-08 — Process-lifetime disclosure sentence is always visible (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- None — this sentence must appear in every state of the panel (idle, active, or with a last outcome)

**Steps:**
1. Navigate to `http://localhost:3255/data`, scroll to the bottom
2. Read the last line of text inside the "Background compute" panel, in every state you can produce
   (idle from UT-04, active from UT-03, completed from UT-05)

**Expected Result:**
- The exact sentence "Since the last backend restart — this history is process-lifetime only, never
  persisted." is visible at the bottom of the panel in ALL of those states — a user who sees an empty
  panel after a restart cannot mistake it for "nothing ever ran"

---

### UT-09 — Pre-existing /data panels are unchanged and unremoved (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- `/data` loads successfully (backend reachable)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll through the full page top to bottom, noting each panel heading in order

**Expected Result:**
- All pre-existing panels are present and in their previous order: Coverage (top), Storage Capacity, Drift
  Report, Rebuild, Universe Diagnostics, Membership Timeline, Backward History, Availability Heatmap,
  Missing Data, Macro Feed, Index Vendor, the Job Form/Job Progress pair, Unfinished Imports, Remove Data,
  and Run History
- No existing field or label has been removed from any of those panels
- "Background compute" is the only new panel, and it is the LAST panel on the page, appearing immediately
  after "Run History" — no existing panel changed position

---

### UT-10 — Readiness pill states are unaffected by the new badge, in every state (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/` (root layout)

**Preconditions:**
- Ability to observe the backend across at least two readiness states (e.g. a fresh restart for
  "Initializing…", then steady-state "Ready")

**Steps:**
1. Observe the readiness pill immediately after a fresh backend start (before warm-up completes)
2. Observe it again once warm-up finishes
3. If a background-compute window is also active during either observation, note whether the new badge
   appears alongside

**Expected Result:**
- The readiness pill's text and color scheme for "Initializing… history X/Y" and "Ready" are unchanged
  from prior phases (same wording, same badge variant)
- The `background-compute-indicator` badge, when present, is always a SEPARATE sibling element next to the
  pill — it never overlaps, replaces, or hides the pill's text in any of the four readiness states
  (loading, ready, initializing, awaiting_snapshot) or the error state (unavailable)

---

### UT-11 — "Background compute" panel is discoverable within 2 clicks and its hint text is plain-language (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/` (Dashboard, the default landing page)
2. Click "Data Manager" in the left sidebar navigation (1 click)
3. Scroll to the bottom of the page and read the small gray hint line directly beneath the "Background
   compute" heading

**Expected Result:**
- The panel is reached in exactly 1 click from the Dashboard (well within the 2-click discoverability bar)
- The heading reads exactly "Background compute"
- The hint sentence beneath it explains, without backend jargon, that this is the automatic background
  calculation a historical Backtest request can start when that date's evidence isn't ready yet — a
  non-technical operator should be able to understand what triggers this panel's activity from the hint
  text alone

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Header/readiness pill loads cleanly | smoke | P1 | `/` |
| UT-02 | Historical backtest triggers a real background-compute window, badge appears | happy-path | P1 | `/backtest` |
| UT-03 | `/data` panel shows live active-window detail | happy-path | P1 | `/data` |
| UT-04 | `/data` panel shows honest idle message | smoke | P1 | `/data` |
| UT-05 | Last-outcome summary appears after completion | happy-path | P1 | `/data` |
| UT-06 | Numeric fields never fabricated/malformed | validation | P2 | `/data` |
| UT-07 | Backend-unavailable degrades badge/panel honestly | error | P2 | `/`, `/data` |
| UT-08 | Process-lifetime disclosure always visible | ux | P3 | `/data` |
| UT-09 | Pre-existing `/data` panels unchanged | regression | P3 | `/data` |
| UT-10 | Readiness pill states unaffected by new badge | regression | P3 | `/` |
| UT-11 | Panel discoverable in 1 click, hint text is plain-language | ux | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02/UT-03/UT-05 form one continuous
happy-path chain — run them in sequence within the same session, respecting the 30-second poll-cadence and
below-the-fold capture guidance at the top of this document.
