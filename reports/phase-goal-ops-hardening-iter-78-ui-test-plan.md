# Phase goal-ops-hardening-iter-78 — UI Test Plan

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- This iteration ships no new page, form, or navigation element — every surface below is the
     existing global readiness badge / preflight banner, present on every route. -->

---

### UT-01 — Home page loads with readiness badge visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (global header, all routes)

**Preconditions:**
- Backend running and reachable at its configured port (health endpoint answering 200)
- Frontend running at http://localhost:3255

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to fully load (network idle)

**Expected Result:**
- Page renders without a blank screen or error boundary
- A badge with the text "Ready" (green dot, `data-testid="readiness-badge"`, `data-state="ready"`) is visible in the top-right of the header
- No console errors

---

### UT-02 — Readiness badge staleness annotation ticks live every second (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** global header (`HealthBadge`, `data-testid="readiness-staleness"`)

**Preconditions:**
- Backend has been running long enough to reach steady-state `Ready` (so the poll has backed off to the 30-second idle cadence) — i.e. at least one poll has landed and `stale_for_s` is genuinely `> 0`

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Confirm the "Ready" pill (`data-testid="readiness-badge"`) is showing
3. Read the text of the element with `data-testid="readiness-staleness"` (format: "as of Ns ago" or "as of <1s ago") and record the integer N
4. Wait 10 seconds without clicking, navigating, or refreshing
5. Read the same element's text again and record the new integer N'

**Expected Result:**
- The text is present in step 3 (not blank) — recorded value N
- In step 5, N' is approximately N + 10 (allow ±1s for measurement jitter) — the number visibly increased while no new backend poll necessarily landed
- The annotation never resets to "as of <1s ago" or disappears during the 10-second wait (that would indicate an unexpected extra poll or a broken tick)

---

### UT-03 — Preflight banner staleness annotation ticks live every second (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** global banner strip under the header (`PreflightBanner`, `data-testid="preflight-staleness"`)

**Preconditions:**
- Preflight verdict is `GO` (banner reads "GO — today's board is current.") — the annotation renders as `(as of Ns ago)` immediately after that text; if the current verdict is `DEGRADED` or `NO-GO`, the same `data-testid="preflight-staleness"` element still appears next to the bold warning line and the same tick assertion applies

**Steps:**
1. Navigate to `http://localhost:3255/` (or any route — the banner is mounted once in the shared layout)
2. Locate the element with `data-testid="preflight-staleness"` inside the banner strip directly under the header
3. Record its displayed integer N (from the "(as of Ns ago)" text)
4. Wait 10 seconds without clicking, navigating, or refreshing
5. Read the same element's text again and record N'

**Expected Result:**
- N' is approximately N + 10 (±1s), matching the readiness badge's tick from UT-02
- The banner's verdict text itself (e.g. "GO — today's board is current.") is unchanged by the tick — only the parenthetical number moves

---

### UT-04 — Fresh/synchronous compute never starts ticking (validation)

**Type:** validation
**Priority:** P2
**Surface:** global header + banner (`readiness-staleness` / `preflight-staleness`)

**Preconditions:**
- A moment where the backend's `GET /api/health` response has `stale_for_s === 0` (a fresh/synchronous compute just landed — most reliably observed right after the backend itself just finished warming up, or by inspecting the raw JSON response of `GET http://localhost:8255/api/health` in a separate tab/curl to confirm `"stale_for_s": 0` before checking the UI)

**Steps:**
1. Confirm via `curl http://localhost:8255/api/health` (or the frontend's next poll) that the current payload's `stale_for_s` field is `0`
2. Navigate to (or stay on) `http://localhost:3255/`
3. Wait 10 seconds without interacting

**Expected Result:**
- Neither `data-testid="readiness-staleness"` nor `data-testid="preflight-staleness"` renders any text at any point during the 10-second wait — a `0` base must never start ticking upward into a fabricated "as of 1s ago", "as of 2s ago", etc.
- The "Ready" pill and the "GO" banner text themselves still render normally

---

### UT-05 — Backend unreachable shows no fabricated staleness (error)

**Type:** error
**Priority:** P2
**Surface:** global header + banner (`readiness-staleness` / `preflight-staleness`, plus the pill/banner themselves)

**Preconditions:**
- Frontend is running and was previously connected to a healthy backend

**Steps:**
1. Navigate to `http://localhost:3255/` and confirm the "Ready" pill and a staleness annotation are showing normally
2. Stop the backend process (find and kill the process bound to its configured port, e.g. `ss -tlnp | grep :8255` then stop that PID, or use the project's own stop mechanism if one is running)
3. Wait for the frontend's next poll to fail (up to the active poll interval, a few seconds) and then wait an additional 10 seconds
4. Observe the badge and banner

**Expected Result:**
- The readiness pill switches to `data-testid="readiness-badge"` `data-state="unavailable"` reading "Backend unavailable"
- The preflight banner switches to `data-verdict="NO-GO"` reading "NO-GO — do not rely on today's board." with the reason "Backend is unavailable — the preflight check could not run."
- Neither `readiness-staleness` nor `preflight-staleness` renders any text at any point after the poll fails, including during the extra 10-second wait — a failed poll must never show a ticking or frozen "as of Ns ago" number
- Restart the backend afterward and confirm the pill returns to "Ready" and the annotation resumes ticking (cleanup / sanity close of the test)

---

### UT-06 — Existing background-compute indicator on /data is untouched (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` (`BackgroundComputeRow`, `data-testid="background-compute-active-row"`) and global header (`data-testid="background-compute-indicator"`)

**Preconditions:**
- A background compute can be put in flight by requesting a historical as-of date whose evidence needs on-demand dispatch (e.g. navigate to a `/backtest?asof=<a date not recently viewed>` URL known to trigger dispatch, per this session's established J-09 pattern)

**Steps:**
1. Navigate to `http://localhost:3255/backtest?asof=<a historical date that triggers on-demand dispatch>`
2. While the compute is in flight, navigate to `http://localhost:3255/data`
3. Look for a list item with `data-testid="background-compute-active-row"`
4. Also check the global header on this same page for `data-testid="background-compute-indicator"`

**Expected Result:**
- The `background-compute-active-row` item is present, showing "as-of <date>" (`data-testid="background-compute-asof"`), an "elapsed" duration, and "horizons N/M" — unchanged formatting from before this iteration (this iteration touched no code in `apps/frontend/app/data/page.tsx`)
- The header's `background-compute-indicator` badge reads "background compute running (N)" alongside the "Ready" pill — unchanged from before this iteration
- This confirms the readiness-provider tick change did not break the unrelated `backgroundCompute` field it shares a context with

---

### UT-07 — Header does not overflow with the badge, staleness text, and compute chip together (regression)

**Type:** regression
**Priority:** P2
**Surface:** global header (`apps/frontend/app/layout.tsx`)

**Preconditions:**
- Browser viewport set to 1280x800 (the width iter-77 specifically fixed a header-overflow bug for)
- A background compute is in flight (see UT-06) so all three elements — "Ready" pill, staleness text, and compute chip — are present simultaneously

**Steps:**
1. Set the browser viewport to 1280x800
2. Navigate to `http://localhost:3255/` while a background compute from UT-06 is still active
3. Observe the header row containing the as-of switcher, "Ready" pill, staleness text, and compute chip

**Expected Result:**
- All elements remain visible — either on one line or wrapped to a second line within the header (which grows via `min-h-14`) — the "Ready" pill is never pushed off-screen or clipped
- The staleness text does not overlap or get cut off by the compute chip

---

### UT-08 — Staleness annotation is visible and legible next to the Ready pill on first load (ux)

**Type:** ux
**Priority:** P3
**Surface:** global header (`HealthBadge`)

**Steps:**
1. Navigate to `http://localhost:3255/` as a first-time visitor (no prior state)
2. Look at the top-right of the header immediately after the page finishes loading

**Expected Result:**
- The "Ready" pill is clearly visible
- Immediately to its right (or wrapped to the same row group), small gray text reading "as of <1s ago" or "as of Ns ago" is legible without needing to hover, click, or open dev tools — the annotation is plain, unstyled inline text per the project's existing "quiet proven/not-proven chip" convention, not hidden behind an icon or tooltip

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home page loads with readiness badge | smoke | P1 | `/` |
| UT-02 | Readiness badge staleness ticks live | happy-path | P1 | global header |
| UT-03 | Preflight banner staleness ticks live | happy-path | P1 | global banner |
| UT-04 | Fresh compute (`stale_for_s===0`) never ticks | validation | P2 | global header + banner |
| UT-05 | Backend unreachable shows no fabricated staleness | error | P2 | global header + banner |
| UT-06 | Existing background-compute indicator untouched | regression | P1 | `/data` + global header |
| UT-07 | Header does not overflow at 1280x800 | regression | P2 | global header |
| UT-08 | Staleness annotation is discoverable/legible | ux | P3 | global header |

**P1 tests must all pass for browser QA verdict to be PASS.**
