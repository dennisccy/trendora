# Phase goal-ops-hardening-iter-47 — UI Test Plan

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Test Cases

<!-- Test IDs use UT-XX. All journey anchors (dates, counts) drift with every ingest — read the
     figures actually shown on screen at test time rather than assuming a fixed number. -->

---

### UT-01 — Evidence page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend is running at http://localhost:3255, backend at http://localhost:8255
- No login required

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the page to finish loading (the loading skeleton, a pulsing gray placeholder card, should
   disappear)

**Expected Result:**
- The heading "Evidence" is visible at the top of the page
- Either at least one `Card` with `data-testid="evidence-claim-row"` is visible, or (if zero certified
  claims exist) the `data-testid="evidence-empty"` card with the heading "No certified claims yet" is
  visible
- No "Backend unavailable" error card (`border-neg`, text "The certified-claims ledger could not load
  from the API") appears
- No browser console errors

---

### UT-02 — Idle Evidence page renders every claim's expectations table quickly with no "Refreshing" badge (happy path — baseline)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Backend has been idle for at least a minute (no backfill/rebuild job running — check the "Run history"
  table at the bottom of `http://localhost:3255/data` shows no row with a `job-status` badge reading
  "running")

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Time how long it takes from navigation to the claim cards being fully rendered (should feel instant —
   well under a couple of seconds, no visible multi-second stall)
3. For each visible claim card, look under the "Historical drawdown & dry-spell expectations (…-day hold)"
   heading

**Expected Result:**
- The page finishes rendering with no perceptible multi-second hang
- No claim card's expectations panel shows the amber "Refreshing" `Badge`
  (`data-testid="evidence-expectations-refreshing"`) — every panel is either a full table with real
  median/p90/n numbers, the "Unavailable — monitored and refreshed as new data arrives" note, or absent
  entirely (no panel section) for a claim with no expectations
- Table cells show real numbers (e.g. a percentage like "-4.20%" or "insufficient (n=…)"), never blank
  cells or a loading spinner

---

### UT-03 — Starting a genuinely new backfill causes the "Refreshing" badge to appear honestly (happy path — core new capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/evidence` + `/data`

**Preconditions:**
- UT-02 has already been run against this same claim set (so you know what "no badge" looks like for
  comparison)
- A prior generation of the expectations data already exists — i.e. the backend has been running for a
  while, not freshly restarted seconds ago

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Under the "Dataset coverage" panel, find the "Price history" row and read the SECOND (later) date shown
   in its value, formatted `<start date> → <end date>` (this is the latest date with any stored price bar
   — read the actual on-screen date, it changes with every ingest)
3. In the "Start date" field (`data-testid="job-start-date"`), type the calendar day immediately AFTER the
   date you read in step 2 (e.g. if the page showed "… → 2026-07-31", type `2026-08-01`)
4. In the "End date" field (`data-testid="job-end-date"`), type the SAME date you just typed in step 3
5. Click the "Start" button
6. Watch the `data-testid="job-status"` badge in the job progress panel — wait for it to stop reading
   "running" (a spinning loader icon disappears)
7. Within the next ~7-8 minutes, navigate to `http://localhost:3255/evidence` (reload if you were already
   on the page) and check each claim card's "Historical drawdown & dry-spell expectations" panel

**Expected Result:**
- After step 5, the job progress panel shows the new job as started (status badge no longer blank)
- After step 6, the job reaches a completed/non-"running" status without the page erroring
- Within the re-check window in step 7, AT LEAST ONE claim card shows the amber `Badge` reading
  "Refreshing" (`data-testid="evidence-expectations-refreshing"`) next to its "Historical drawdown &
  dry-spell expectations (…-day hold)" heading
- That same panel's table still shows real numbers (median/p90/n or "insufficient (n=…)"), never a blank
  table or a loading placeholder
- The descriptive paragraph under the heading includes the added sentence: "A newer version is computing
  in the background after a recent data update — the table below is the last complete version, not a
  partial or fabricated one."
- `GET /evidence`'s page load itself still feels fast (no multi-second/multi-minute hang), even while the
  badge is showing

---

### UT-04 — "Refreshing" badge clears once the background catch-up finishes (happy-path continuation)

**Type:** happy-path
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- UT-03 has just been run and produced at least one "Refreshing" badge

**Steps:**
1. Wait approximately 8-10 minutes after the backfill in UT-03 step 5 completed
2. Navigate to `http://localhost:3255/evidence` (or reload if already there)
3. Check the same claim card(s) that showed the "Refreshing" badge in UT-03

**Expected Result:**
- The "Refreshing" badge (`data-testid="evidence-expectations-refreshing"`) is no longer present on those
  claim cards
- The table's numbers may differ slightly from what UT-03 showed (a fresh generation), or may be identical
  if the underlying claim's data was not affected by the backfilled date — either is acceptable, both are
  "ready" (no badge), never a blank table

---

### UT-05 — Data Manager's backfill flow still works (regression — dependency of UT-03)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Confirm the "Data Manager" heading and the "Dataset coverage" panel are visible
3. Fill the "Start date" field (`data-testid="job-start-date"`) and "End date" field
   (`data-testid="job-end-date"`) with a short 1-2 day range using the "Price history" date read in UT-03
   step 2 as a reference (any range is acceptable for this smoke check — it does not need to be a NEW
   date)
4. Click the "Start" button

**Expected Result:**
- No client-side validation error appears (the form only blocks submission for a malformed non-`yyyy-MM-dd`
  date)
- The job progress panel updates with a new job (a `data-testid="job-status"` badge appears)
- The "Run history" table at the bottom of the page eventually includes a row for the new job

---

### UT-06 — Home page and Evidence page stay responsive while a backfill runs (regression — no-outage check)

**Type:** regression
**Priority:** P1
**Surface:** `/` and `/evidence`

**Preconditions:**
- A backfill job is currently running (e.g. immediately after UT-03 step 5 or UT-05 step 4, before the
  `job-status` badge leaves "running")

**Steps:**
1. While the job from a prior step is still "running", navigate to `http://localhost:3255/`
2. Confirm the page loads and shows the text "Ready" somewhere on the page (the readiness/health
   indicator)
3. Navigate to `http://localhost:3255/evidence`
4. Confirm the page loads within a few seconds (not frozen, not a blank white screen)

**Expected Result:**
- Both pages load successfully and quickly while the backfill is in flight
- No "Backend unavailable" error card appears on either page
- The Evidence page's claim cards render (with or without the "Refreshing" badge depending on timing) —
  never an indefinite spinner

---

### UT-07 — Existing "Unavailable" and absent expectations-panel states are unchanged (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/evidence`

**Preconditions:**
- None — this is an observational check across whatever claims currently exist

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Scroll through every visible claim card and note, for each one, which of the three possible states its
   "Historical drawdown & dry-spell expectations" section is in: a full table, the text "Unavailable —
   monitored and refreshed as new data arrives", or no expectations section at all

**Expected Result:**
- Any claim card currently showing "Unavailable — monitored and refreshed as new data arrives"
  (`data-testid="evidence-expectations-unavailable"`) renders that exact text with no badge and no table
  — unchanged from prior iterations
- Any claim card with no expectations section renders nothing extra in that area — unchanged
- Neither of these two states shows the "Refreshing" badge (that badge is exclusive to the full-table
  state)

---

### UT-08 — "Refreshing" badge is visually calm and does not break the claim card layout (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- At least one claim card is currently showing the "Refreshing" badge (run UT-03 first if none is showing)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate a claim card showing the "Refreshing" badge
3. Visually inspect the badge's placement relative to the "Historical drawdown & dry-spell expectations
   (…-day hold)" heading and the table below it

**Expected Result:**
- The badge sits inline next to the heading text, using the same amber/warn color treatment already used
  elsewhere on the page (e.g. the "INSUFFICIENT" verdict badge) — not a bright red alarm color, not a
  full-width banner
- The table, its columns, and the rest of the claim card (verdict badge, hypothesis chips, registration
  date, etc.) are laid out exactly as on a claim card with no badge — the badge does not push other
  elements out of place or cause any visible overlap/wrapping issue
- The added disclosure sentence reads as a natural continuation of the existing description paragraph, not
  as a jarring separate warning block

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Evidence page loads without errors | smoke | P1 | `/evidence` |
| UT-02 | Idle Evidence page fast, no Refreshing badge | happy-path | P1 | `/evidence` |
| UT-03 | New backfill triggers honest "Refreshing" badge | happy-path | P1 | `/evidence` + `/data` |
| UT-04 | "Refreshing" badge clears after catch-up | happy-path | P2 | `/evidence` |
| UT-05 | Data Manager backfill flow still works | regression | P1 | `/data` |
| UT-06 | Home + Evidence stay responsive during a backfill | regression | P1 | `/` + `/evidence` |
| UT-07 | "Unavailable"/absent panel states unchanged | regression | P3 | `/evidence` |
| UT-08 | "Refreshing" badge is calm and doesn't break layout | ux | P2 | `/evidence` |

**P1 tests must all pass for browser QA verdict to be PASS.**
