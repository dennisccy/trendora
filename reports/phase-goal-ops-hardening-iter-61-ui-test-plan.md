# Phase goal-ops-hardening-iter-61 — UI Test Plan

**Phase:** goal-ops-hardening-iter-61
**Date:** 2026-08-11
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend and frontend are running (`scripts/dev.sh`, ports 8255/3255)
- No fault-injection env var is set (normal launch)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen
- The "Backend unavailable" error card does NOT appear
- The "Dataset coverage" panel is visible with stat tiles labeled "Snapshot dates" and
  "Backfill gaps", each showing a numeric value
- The "Start a fetch / backfill job" panel with a "Start" button is visible
- No errors appear in the browser console

---

### UT-02 — `/data` refreshes coverage counts on an ambient cadence, not just on this tab's own job (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` is open and loaded (UT-01 passed)
- Ability to trigger a data-changing event from a SECOND source (a second browser tab
  hitting `/backtest`, or a script calling `POST /api/data/jobs`) — this proves the fix is
  independent of "this tab's own job," which is the exact defect this iteration repairs

**Steps:**
1. Navigate to `http://localhost:3255/data` in Tab A and note the current "Snapshot dates"
   value shown in the "Dataset coverage" panel
2. Open browser DevTools → Network tab in Tab A, filter for `api/data`, and clear the log
3. Without touching Tab A, from a SECOND tab or a script, trigger any request-path event
   that changes `_membership_dataset_version` (e.g. load `http://localhost:3255/backtest`
   for a historical as-of date not previously scanned)
4. Return to Tab A and wait 35 seconds without clicking, typing, or reloading anything

**Expected Result:**
- Within the 35-second wait, the Network tab in Tab A shows a NEW `GET /api/data` request
  and a NEW `GET /api/data/availability` request that Tab A itself initiated, with no user
  action (no click, no reload) between steps 3 and 4
- The "Dataset coverage" panel's values update in place (no full-page reload, no flash of
  a loading spinner covering the whole panel)

---

### UT-03 — Ambient refresh fires on the configured cadence, not early or never (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `GET http://localhost:8255/api/health` reports `poll_idle_interval_seconds: 30.0` (the
  configured cadence; confirm with `curl http://localhost:8255/api/health` if in doubt)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Open browser DevTools → Network tab, filter for `api/data`, clear the log immediately
   after the page's own initial mount requests appear
3. Watch the Network tab continuously for 25 seconds without reloading

**Expected Result:**
- No new `GET /api/data` request appears in the first ~25 seconds after the initial mount
  fetch (the interval must not fire early / must not double-fire)
- Continuing to watch past the 30-second mark, exactly one new `GET /api/data` request
  (and one `GET /api/data/availability` request) appears between second 25 and second 35

---

### UT-04 — Job started from THIS tab still refreshes coverage immediately on completion (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` is open; the job form is idle (not currently "running")
- A short-duration job can be started (e.g. "Fetch EOD prices" for a small date range) —
  if only a long-running backfill is available, this test may be deferred to an automated
  pass rather than run manually within the 5-minute window

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, set "Start date" and "End date" to a small,
   valid range, leave "Job kind" as its default, and click the "Start" button
3. Wait for the button label to change from "Job running…" back to "Start" (job completed)

**Expected Result:**
- Immediately after the button reverts to "Start" (no additional wait needed), the
  "Dataset coverage" panel's values reflect the just-completed job — this is the
  PRE-EXISTING same-tab refresh path, which must still fire immediately and must not have
  been broken by the new ambient-refresh addition

---

### UT-05 — Top-bar readiness badge is unaffected by the new `pollIdleIntervalSeconds` field (regression)

**Type:** regression
**Priority:** P2
**Surface:** app shell (all pages) — readiness/health badge

**Preconditions:**
- Backend and frontend running normally

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Locate the readiness/health badge in the top bar

**Expected Result:**
- The badge shows "Ready" (or the app's normal ready state) exactly as it did before this
  iteration — no new label, no new color, no new tooltip text
- No console error referencing `pollIdleIntervalSeconds`, `readiness-provider`, or
  `ReadinessContext` appears

---

### UT-06 — Regime Lab shows the "Unavailable" indicator under an armed memory-pressure fault (error)

**Type:** error
**Priority:** P2
**Surface:** `/research/regime-lab`

**Preconditions:**
- **Requires a developer/operator action, not an end-user action:** the backend must be
  relaunched with the environment variable `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`
  set (e.g. `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab bash scripts/start-backend.sh`),
  then restored to a normal unarmed launch afterward
- A cohort with a nonzero real observation count exists for the chosen as-of date (e.g.
  `2010-11-05`, used during this iteration's own evidence capture)

**Steps:**
1. With the fault-injection env var armed, navigate to
   `http://localhost:3255/research/regime-lab?asof=2010-11-05`
2. Click the "As of date" toggle if not already selected (it should be selected by the URL
   param)
3. Locate a sample-size chip cell in the factor grid

**Expected Result:**
- The cell shows a small grey triangle warning icon followed by the word "Unavailable"
  (`data-testid="sample-link-unavailable"`), NOT a clickable blue `n=...` link
- Hovering the indicator shows the tooltip text "Temporarily unavailable — degraded under
  memory pressure"
- Clicking the indicator does nothing (it is a `<span>`, not a link — no navigation occurs)

---

### UT-07 — Regime Lab shows normal clickable sample-size links when the backend is NOT under fault injection (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/research/regime-lab`

**Preconditions:**
- Backend restarted WITHOUT `TRENDORA_FAULT_INJECT_MEMORY_ERROR` set (normal launch)
- Same as-of date used in UT-06 for direct comparison (e.g. `2010-11-05`)

**Steps:**
1. Navigate to `http://localhost:3255/research/regime-lab?asof=2010-11-05`
2. Locate the same sample-size chip cell checked in UT-06

**Expected Result:**
- The cell shows a normal clickable `n=...` chip (`data-testid="sample-link"`), with an
  underline on hover, and NO "Unavailable" text or triangle icon
- Clicking the chip opens `/research/samples` in a new browser tab

---

### UT-08 — Ambient refresh is silent — no loading flicker or error flash during background updates (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- `/data` is open and idle for at least one full 30-second cadence

**Steps:**
1. Navigate to `http://localhost:3255/data` and let it settle (initial load complete)
2. Watch the "Dataset coverage" panel continuously through at least one ambient refresh
   cycle (~35 seconds), without interacting with the page

**Expected Result:**
- The panel's numbers update in place with no visible full-panel loading spinner, no
  "Backend unavailable" flash, and no layout shift
- No new toast, banner, or modal appears announcing the refresh — the update is silent, as
  the plan specifies no new visible UI element was introduced

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | Ambient refresh picks up an externally-triggered change | happy-path | P1 | `/data` |
| UT-03 | Refresh cadence matches the configured 30s interval | validation | P2 | `/data` |
| UT-04 | Same-tab job completion still refreshes immediately | regression | P1 | `/data` |
| UT-05 | Readiness badge unaffected by new context field | regression | P2 | app shell |
| UT-06 | "Unavailable" indicator renders under armed fault | error | P2 | `/research/regime-lab` |
| UT-07 | Normal sample-link chips render without fault injection | regression | P1 | `/research/regime-lab` |
| UT-08 | Ambient refresh causes no visible flicker/error flash | ux | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**
