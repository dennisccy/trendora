# Phase goal-ops-hardening-iter-77 — UI Test Plan

**Phase:** goal-ops-hardening-iter-77
**Date:** 2026-08-13
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Background for the operator

The readiness/background-compute state is served by `GET /api/health` and re-read by every page's top
bar every ~2s (or every ~30s once "Ready" and idle). In this build, the backend's readiness cache ticks
every 0.5s, so `stale_for_s` is virtually always slightly greater than zero during normal use — expect
the new annotation text to read **"as of 0s ago"** most of the time (it rounds to the nearest whole
second), not a large number. A background-compute window (needed for UT-05/UT-06) is most reliably
triggered by navigating to `/backtest` and stepping to a previous historical as-of date with the
"Previous available date" arrow — this dispatches forward-aggregate computation for that date if it
isn't already cached for the current dataset version.

---

## Test Cases

---

### UT-01 — Global top bar and preflight banner load without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (global top bar + preflight banner, present on every page)

**Preconditions:**
- Backend running at http://localhost:8255 (or configured backend URL)
- Frontend running at http://localhost:3255
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (the badge should leave its "Checking backend…" loading state)

**Expected Result:**
- The top-bar badge (`[data-testid="readiness-badge"]`) shows "Ready" (green pill), not "Checking
  backend…" or "Backend unavailable"
- The preflight strip directly under the top bar (`[data-testid="preflight-banner"]`) reads "GO —
  today's board is current." followed by staleness text in parentheses
- No blank page, no unhandled error screen, no browser console errors

---

### UT-02 — Readiness badge shows a live staleness annotation (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (global top bar — `HealthBadge`)

**Preconditions:**
- Backend and frontend both running and reachable (per UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Locate the "Ready" pill in the top-right of the header
3. Look immediately to the right of the pill for a small gray text element with
   `data-testid="readiness-staleness"`

**Expected Result:**
- A short text annotation reading `as of Ns ago` (e.g. "as of 0s ago") is visible immediately next to
  the "Ready" pill
- The displayed number is small (typically 0, occasionally 1) under normal light load — this is
  expected, not a bug, given the backend's fast internal refresh cadence
- The SAME text also appears on the preflight strip directly below, in parentheses, e.g.
  "GO — today's board is current.  (as of 0s ago)" (`[data-testid="preflight-staleness"]` inside
  `[data-testid="preflight-banner"]`)

---

### UT-03 — No annotation renders for a value of exactly zero or on a failed poll (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` (global top bar + preflight banner)

**Preconditions:**
- Backend and frontend both running (per UT-01)
- Browser DevTools available (to open the Network tab / simulate offline)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Open browser DevTools → Network tab → set throttling to "Offline" (or otherwise block requests to
   the backend's `/api/health` endpoint)
3. Wait ~5 seconds for the next poll to fail (badge poll cadence is ~2s while active)

**Expected Result:**
- The badge pill changes to "Backend unavailable" (red) or reverts to "Checking backend…" — never stays
  on a stale "Ready" with a frozen staleness number
- `[data-testid="readiness-staleness"]` is NOT present anywhere in the DOM once the poll has failed —
  no leftover or fabricated "as of Ns ago" text is shown
- `[data-testid="preflight-staleness"]` is likewise absent; the preflight strip instead shows the
  NO-GO state ("NO-GO — do not rely on today's board." with the reason "Backend is unavailable — the
  preflight check could not run.")
- Restore the network connection afterward and confirm the badge recovers to "Ready" with the
  annotation reappearing within ~2-30 seconds

---

### UT-04 — `/data` shows the honest fallback when the coverage endpoint fails (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Backend restarted with the environment variable
  `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` set (this is a pre-existing, already-shipped
  fault-injection hook at `apps/backend/app/api/data.py:119` — this iteration only captured fresh evidence
  for it, it did not add it)

**Steps:**
1. With the fault-injection env var set, restart the backend and navigate to
   `http://localhost:3255/data`
2. Wait for the page to finish loading

**Expected Result:**
- A red-bordered card reading "Backend unavailable" is visible
- Below it, the exact text "Dataset coverage could not load from the API. No figures are shown rather
  than fabricated values. Confirm the backend is running and retry." is visible
- No coverage numbers, gap counts, or symbol tables render — the page fails honestly rather than
  showing fabricated or zeroed-out figures
- Restart the backend afterward with the fault-injection variable unset

---

### UT-05 — "Ready" pill stays visible alongside the background-compute chip at 1280×800 (regression, iter-76/e)

**Type:** regression
**Priority:** P1
**Surface:** `/` and `/data` (global top bar)

**Preconditions:**
- Browser window (or DevTools device toolbar) resized to exactly 1280×800
- A background-compute window is in flight (see steps 1-3 below to trigger one)

**Steps:**
1. Resize the browser window to 1280×800 (DevTools → Toggle device toolbar → set custom size 1280×800)
2. Navigate to `http://localhost:3255/backtest`
3. Click the left arrow button labeled "Previous available date" (`[data-testid="asof-step-prev"]`,
   next to the "Latest" as-of selector in the top bar) 2-3 times to land on different historical dates,
   until the top bar shows a `[data-testid="background-compute-indicator"]` chip reading
   "background compute running (N)" (if the first date doesn't trigger one, try clicking a couple more
   times — the exact date needed to trigger a fresh compute varies by what's already cached)
4. Once the chip is visible, observe the full top bar

**Expected Result:**
- The readiness pill (`[data-testid="readiness-badge"]`, showing "Ready") AND the
  `[data-testid="background-compute-indicator"]` chip ("background compute running (N)") are BOTH
  visible on-screen simultaneously — neither is clipped or pushed outside the visible header
- If the combined badge content doesn't fit on one line, the row wraps onto a second line (the header
  grows slightly taller) rather than any element disappearing off the right edge
- This confirms the iter-76/e regression (the pill silently disappearing at this exact viewport size) is
  fixed

---

### UT-06 — `/backtest` scorecard rows carry stable test selectors, table unchanged visually (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/backtest`

**Preconditions:**
- Backend/frontend running; a populated as-of date is loaded (e.g. the default "Latest" view, or any
  historical date with at least the 1d row populated)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the "Forward-test scorecard" table to render
3. Open browser DevTools → Console and run:
   `document.querySelectorAll('[data-testid^="scorecard-row-"]').length`

**Expected Result:**
- The console command returns `5` (one row per configured horizon: 1d, 5d, 10d, 20d, 60d)
- Individually, `document.querySelector('[data-testid="scorecard-row-1d"]')` returns a non-null
  `<tr>` element whose text content starts with "1d"
- The visible table itself (Horizon / Cohort / vs SPY / vs QQQ / vs Sector / Random peers / SPY / QQQ /
  Sector ETF columns) looks exactly as before — no visual difference from this test-hook addition

---

### UT-07 — Staleness annotation is discoverable and reads clearly to a new user (UX)

**Type:** ux
**Priority:** P3
**Surface:** global top bar + preflight banner

**Steps:**
1. Navigate to `http://localhost:3255/` as if seeing the app for the first time
2. Look at the top-right corner of the page without any prior explanation

**Expected Result:**
- The small text next to the "Ready" pill (e.g. "as of 0s ago") is plainly readable at normal zoom and
  visually distinct from the pill itself (muted gray, not colored/alarming)
- Its meaning ("how old is this status reading") is inferable from the phrase "as of Ns ago" without
  needing a tooltip or documentation
- The parenthesized version on the "GO — today's board is current." strip reads naturally as part of
  the same sentence, not as a disconnected fragment

---

### UT-08 — Existing preflight DEGRADED/NO-GO banner still names its reasons correctly (regression)

**Type:** regression
**Priority:** P2
**Surface:** global preflight banner (all pages)

**Preconditions:**
- A condition that produces a DEGRADED or NO-GO preflight verdict is active (e.g. stop the backend to
  force NO-GO, per UT-03's steps, or use whatever existing condition this project's QA harness uses to
  induce DEGRADED)

**Steps:**
1. Induce a NO-GO condition (simplest: stop the backend process entirely, then load
   `http://localhost:3255/`)
2. Observe the full-width banner across the top of the page

**Expected Result:**
- The banner reads "NO-GO — do not rely on today's board." (exact phrase preserved, per prior journeys'
  acceptance criteria) followed by the reason "Backend is unavailable — the preflight check could not
  run." in a bulleted list below
- No staleness annotation appears next to the NO-GO heading (a failed poll must never show a stale or
  fabricated staleness number — see UT-03)
- Restore the backend afterward and confirm the banner returns to "GO"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Top bar / preflight banner load cleanly | smoke | P1 | `/` |
| UT-02 | Staleness annotation appears on badge + banner | happy-path | P1 | `/` |
| UT-03 | No annotation on zero-stale / failed poll | validation | P2 | `/` |
| UT-04 | `/data` honest fallback on fault injection | error | P2 | `/data` |
| UT-05 | Ready pill visible alongside compute chip at 1280×800 | regression | P1 | `/`, `/data` |
| UT-06 | Scorecard rows carry `data-testid`, table unchanged | regression | P3 | `/backtest` |
| UT-07 | Staleness text is discoverable/clear | ux | P3 | global |
| UT-08 | NO-GO banner still names reasons, no stale annotation | regression | P2 | global |

**P1 tests must all pass for browser QA verdict to be PASS.**
