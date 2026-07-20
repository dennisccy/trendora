# Phase goal-ops-hardening-iter-4 — UI Test Plan

**Phase:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context

This iteration's ONLY visible-surface frontend edit is a fourth branch added to `HealthBadge`
(`apps/frontend/components/health-badge.tsx`) plus a type widening in `apps/frontend/lib/api.ts` (no
render surface of its own). Every other panel referenced below (`JobForm`, `JobProgressPanel`,
`CoveragePanel`, `PreflightBanner`) is **unchanged code**, tested here only because the backend edits
(`readiness.py`, `data_manager.py`) feed them and must not have broken them.

**Not testable via any click path this iteration** (noted so testers do not go looking for them):
- The precise TC-2/TC-3 reproduction ("a NON-benchmark symbol's bar lands after the last run" vs.
  "the BENCHMARK's own bar lands after the last run") cannot be produced by clicking the "Start a
  fetch / backfill job" form alone — it has no per-symbol picker; "Fetch EOD prices" always targets
  "the full committed symbol pool" (its own on-page help text), so SPY and every other symbol move
  together. UT-03, UT-04, UT-05, and UT-08 below each name the exact database-level setup required
  (mirroring the backend's own pytest fixtures) as an explicit precondition, consistent with how
  `reports/phase-goal-ops-hardening-iter-3-ui-test-plan.md`'s UT-04/UT-08 already handled this same
  class of problem, and with `reports/perf-budgets.md`'s own "use an isolated throwaway copy of the DB,
  never the shared committed file" practice, which this plan reuses for the same reason.
- A full "before/after" measurement of the 16-minute rebuild's memory ceiling (TC-9 in
  `reports/perf-budgets.md`) is already on file and is not repeated here — UT-07 below only checks the
  **user-visible** heartbeat honesty during that same job, not the memory measurement itself.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Dashboard loads with the header badge and preflight banner visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (global header, mounted once in `app/layout.tsx` — visible on every page)

**Preconditions:**
- Frontend running at http://localhost:3255
- Backend running and reachable (e.g., started via `scripts/start-backend.sh`)
- No login required (single-user local application)

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page to finish loading
3. Look at the header bar's right-hand side
4. Look directly below the header bar

**Expected Result:**
- The "Dashboard" heading and subtitle "The daily snapshot at a glance" are visible — no blank
  screen, no crash, no error boundary
- The readiness badge (`data-testid="readiness-badge"`) is visible in the header, showing exactly
  one of: "Checking backend…", "Ready", "Initializing… history N/M", "Snapshot pending — …", or
  "Backend unavailable" — never blank
- The preflight banner (`data-testid="preflight-banner"`) is visible directly below the header,
  showing either the quiet green one-line strip "GO — today's board is current." or a louder
  amber/red banner starting "DEGRADED —" or "NO-GO —"
- No console errors

---

### UT-02 — Baseline: badge and banner are unaffected when a servable snapshot already exists (regression — TC-1)

**Type:** regression
**Priority:** P1
**Surface:** global header

**Preconditions:**
- Backend running against the normal committed dev database — no special setup

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Read the exact text of the readiness badge
3. Reload the page (F5) and read the badge text again
4. Read the preflight banner directly below the header

**Expected Result:**
- The badge reads "Ready" or "Initializing… history N/M" — NOT "Snapshot pending — …" and NOT
  "Backend unavailable"
- The badge text in step 3 is identical to step 2 (stable across a reload)
- The preflight banner shows the quiet green strip, `data-verdict="GO"`, text "GO — today's board is
  current."

---

### UT-03 — Full recovery loop: "Snapshot pending" appears, then clears after running a backfill (happy path — B3 fix, TC-3/TC-4/TC-5)

**Type:** happy-path
**Priority:** P1
**Surface:** global header + `/data`

**Preconditions:**
- **This exact condition cannot be produced by ordinary clicking.** A developer/QA engineer must
  first prepare it on an **isolated copy** of the database (never the shared committed dev database):
  1. From the header's as-of control (next to the readiness badge), note the current latest snapshot
     date (the date shown when it is not flagged "historical"). Call this date D.
  2. Insert one new `DailyPrice` row for symbol `SPY` dated D+1 (one calendar day later; if that lands
     on a weekend/holiday, use the next real trading day) into the copy's database — with **no** new
     `ScannerRun` row for that later date. (Mirrors `benchmark_ahead_engine` in
     `apps/backend/tests/test_readiness.py`.)
  3. Point a `scripts/start-backend.sh` instance at that copy (a separate port, e.g. 8256) and point a
     frontend instance at it.
- If this has already been prepared for you, skip straight to Step 1.

**Steps:**
1. Navigate to the Dashboard of the instance pointed at the prepared copy
2. Read the readiness badge's full text closely
3. Look at the small dot next to the badge text — note whether it pulses/animates or stays solid
4. Click "Data Manager" in the left sidebar
5. In the "Start a fetch / backfill job" panel, set "Job kind" to "Backfill snapshots"; ensure the
   "End date" field covers D+1 (the date used in the precondition)
6. Click the "Start" button
7. Wait for the "Job progress" panel's status badge to settle on "ok"
8. Navigate back to `/` (or reload) and read the readiness badge again

**Expected Result:**
- After step 2: `data-state="awaiting_snapshot"`; visible text begins "Snapshot pending" and includes
  the sentence "New data has landed for the benchmark (SPY) through `<D+1 date>`, but no snapshot has
  been produced for that date yet. Run a backfill or rebuild on Data Manager to produce it." — the
  text never says "Backend unavailable"
- After step 3: the dot is a steady accent color with NO pulse animation — visually distinct from
  both the red "unavailable" dot and the pulsing amber "Initializing…" dot
- After step 7: the job completes with status "ok" and creates at least one new snapshot dated D+1
- After step 8: the badge no longer reads "Snapshot pending" — it now reads "Ready" or
  "Initializing… history N/M" (either is acceptable), and `data-state` is no longer
  `awaiting_snapshot`
- Throughout, the preflight banner stays on its quiet green "GO — today's board is current." strip —
  it is never forced to DEGRADED/NO-GO by the Snapshot-pending condition alone

---

### UT-04 — An ordinary fetch/backfill job never flips the badge to "Backend unavailable" (regression — the actual B3 bug, TC-2)

**Type:** regression
**Priority:** P1
**Surface:** global header + `/data`

**Preconditions:**
- Backend running and reachable; badge currently reads "Ready" or "Initializing…" (confirm via UT-02
  first)

**Steps:**
1. Navigate to `http://localhost:3255/`, note the exact readiness badge text
2. Click "Data Manager" in the left sidebar
3. In the "Start a fetch / backfill job" panel, leave the pre-filled "Start date"/"End date" fields as
   they are, set "Job kind" to "Fetch EOD prices", and click "Start"
4. Wait for the "Job progress" panel's status badge to settle on a terminal value ("ok", "partial", or
   a "Zero-work outcome" note)
5. Read the readiness badge text again

**Expected Result:**
- After step 5, the readiness badge text is IDENTICAL to what was noted in step 1 — it must NOT
  change to "Backend unavailable" or to "Snapshot pending", regardless of whether the fetch landed
  any new bars
- This holds even if the fetch landed genuinely new price bars for one or more symbols
- Note: because "Fetch EOD prices" always targets the full committed symbol pool (no per-symbol
  picker exists in this form), this test demonstrates the general regression; the precise "one
  non-benchmark symbol only" reproduction from the functional test plan (TC-2) is a database-level
  check (see Context above), not reachable through this form alone

---

### UT-05 — A database that was never scanned still shows the true "Backend unavailable" state (regression guard — TC-6)

**Type:** regression
**Priority:** P1
**Surface:** global header

**Preconditions:**
- A developer/QA engineer has pointed a `scripts/start-backend.sh` instance at an **isolated**
  database copy containing at least one `DailyPrice` row but ZERO `ScannerRun` rows ever persisted
  (mirrors `unscanned_engine` in `apps/backend/tests/test_readiness.py`) — never the shared committed
  dev database

**Steps:**
1. Navigate to the Dashboard of the instance pointed at that database
2. Read the readiness badge
3. Read the preflight banner directly below the header

**Expected Result:**
- The badge shows `data-state="unavailable"`, red/danger styling, and the exact text "Backend
  unavailable" — NOT "Snapshot pending", even though real price data exists in this database
- The preflight banner shows the loud red banner: bold text "NO-GO — do not rely on today's board."
  with the bullet reason "No servable snapshot: the database is unreachable or no run is persisted
  for the latest data date."

---

### UT-06 — Backend fully unreachable shows an honest error, never a crash (error)

**Type:** error
**Priority:** P2
**Surface:** global header + `/data`

**Preconditions:**
- Tester has access to stop the backend process (`scripts/start-backend.sh`'s process), or otherwise
  make the API unreachable from the frontend

**Steps:**
1. With the frontend already loaded and showing a normal badge, stop the backend process
2. Wait roughly 10–15 seconds for the next readiness poll, or reload the page
3. Read the readiness badge
4. Read the preflight banner
5. Navigate to (or reload) `http://localhost:3255/data`

**Expected Result:**
- No blank white screen, raw stack trace, or generic browser network-error page appears anywhere
- The readiness badge shows `data-state="unavailable"`, text "Backend unavailable"
- The preflight banner shows the loud red banner: "NO-GO — do not rely on today's board." with the
  bullet "Backend is unavailable — the preflight check could not run."
- On `/data`, a card with a warning-triangle icon shows the bold text "Backend unavailable" and,
  below it, "Dataset coverage could not load from the API. No figures are shown rather than
  fabricated values. Confirm the backend is running and retry." — no coverage numbers are shown at
  all

---

### UT-07 — Job progress heartbeat keeps advancing through the entire aggregate-refresh finalize phase of a full rebuild (happy path — F1 fix, TC-7)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend running via `scripts/start-backend.sh`
- **This test runs much longer than the others** — a full rebuild of the current committed dev
  database measured at ~16 minutes total (`reports/perf-budgets.md`, Item L: 965.25 s, of which
  ~728.6 s is the finalize phase this fix targets). Budget accordingly, or point the backend at an
  isolated throwaway copy first (recommended — matches that same report's own practice, so the shared
  instance is not tied up for the full duration)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Rebuild snapshots for current universe" panel, click the "Rebuild snapshots for current
   universe" button
3. In the "Confirm snapshot rebuild" dialog that appears, click the "Rebuild snapshots" button
4. Watch the "Job progress" panel continuously: the status badge, the current-activity line, and the
   heartbeat text (e.g. "updated 3s ago")
5. Keep watching specifically for the stretch AFTER the visible per-date progress reaches its total
   (the main scan/backfill stage has finished) but the status badge is still "running" — this is the
   finalize/aggregate-refresh tail F1 fixed
6. Wait for the job to reach a terminal status

**Expected Result:**
- Throughout the ENTIRE job, including the finalize tail in step 5, the heartbeat text keeps
  resetting to a low value ("updated just now" / "updated Ns ago") roughly once per second — it never
  sits frozen on a growing number for more than about 20 seconds while status is still "running"
- The "· possibly stalled" suffix never appears next to the heartbeat while the job remains healthy
  and running
- The current-activity line keeps changing to name real ongoing work throughout, including during
  the finalize tail
- The job eventually reaches status "ok"
- The header's readiness badge remains stable throughout (never flips to "Backend unavailable")

---

### UT-08 — Fresh, never-ingested database shows an honest all-zero coverage panel on first load (regression — closes the previously-SKIPPED check, TC-8)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Requires a genuinely fresh, never-ingested **copy** of the database — an environment-setup
  precondition, not achievable by clicking alone on a normal shared instance
- Backend started via `scripts/start-backend.sh` against that fresh copy, with zero ingest performed
  yet this session

**Steps:**
1. As the very first request this session, navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading
3. Read every tile in the "Dataset coverage" panel

**Expected Result:**
- The page returns promptly — no infinite spinner, no error boundary, no crash, no long delay
- Every "Dataset coverage" figure honestly reads "0" (Universe (as of date), Candidate universe,
  Symbols, Trading days, Snapshot dates, Backfill gaps) or "—" (Price history's start/end dates) —
  never blank, never a fabricated non-zero placeholder
- This all-zero/dash state appears immediately on the very first paint, not after a delay
- **This check must actually be executed and observed this iteration** — it was SKIPPED in the prior
  iteration's QA pass; an argument of "no code changed here" alone does not satisfy this test

---

### UT-09 — Multi-day backfill still renders its breakdown line and keeps the badge "Ready" throughout (regression — required-still-passing J-01/J-03/J-04, TC-9)

**Type:** regression
**Priority:** P1
**Surface:** global header + `/data`

**Preconditions:**
- Frontend and backend running; the committed database has a range of trading days with existing
  backfill gaps (the default seeded state normally does)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Note the current "Snapshot dates" and "Backfill gaps" values in the "Dataset coverage" panel
3. In the "Start a fetch / backfill job" panel, set "Job kind" to "Backfill snapshots", leave the
   pre-filled multi-day date range as-is, and click "Start"
4. While the job runs, glance at the header's readiness badge every 10–15 seconds
5. Wait for the "Job progress" panel's status badge to settle on "ok"

**Expected Result:**
- The "Job progress" panel shows a breakdown line of the form "N calendar days · N already
  snapshotted · N non-trading" with real numbers substituted (never blank or "undefined")
- If the range requires chunking, a "chunk X/Y" badge is shown and its numbers advance as the run
  progresses
- Throughout the run, the header badge keeps reading whatever it read at the start ("Ready" or
  "Initializing…") — it never flips or freezes
- After completion, "Snapshot dates" increases and "Backfill gaps" decreases in the "Dataset
  coverage" panel, matching the gaps just filled

---

### UT-10 — "Snapshot pending" text is self-explanatory without developer knowledge (ux)

**Type:** ux
**Priority:** P3
**Surface:** global header

**Preconditions:**
- Same database precondition as UT-03 (badge showing `data-state="awaiting_snapshot"`) — run this
  check BEFORE performing UT-03's recovery steps (5–8), while the condition is still present

**Steps:**
1. With the badge showing "Snapshot pending — …", read the full detail sentence with no prior
   knowledge of this iteration's fix
2. Note whether the sentence names a specific symbol, a specific date, and a specific next action
3. Compare the badge's color/dot treatment against "Ready" (green), "Initializing…" (pulsing amber),
   and "Backend unavailable" (red)
4. Note whether "Data Manager" (the page the recovery text points to) is reachable within a single
   click from anywhere in the app

**Expected Result:**
- The sentence is understandable with no backend/code knowledge: it names the benchmark symbol
  (SPY), a specific date, states "no snapshot has been produced for that date yet", and says exactly
  what to do ("Run a backfill or rebuild on Data Manager to produce it.")
- The color/dot treatment is visually distinct from all three other states — it is not red, and the
  dot does not pulse the way "Initializing…" does
- "Data Manager" is one click away via the sidebar at all times — the recovery instruction points
  somewhere the user can actually reach immediately

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Dashboard loads with badge + banner | smoke | P1 | `/` |
| UT-02 | Baseline badge/banner unaffected | regression | P1 | header |
| UT-03 | Full "Snapshot pending" → recovery loop | happy-path | P1 | header + `/data` |
| UT-04 | Ordinary fetch never flips badge | regression | P1 | header + `/data` |
| UT-05 | Never-scanned DB still shows true unavailable | regression | P1 | header |
| UT-06 | Backend fully down shows honest error | error | P2 | header + `/data` |
| UT-07 | Heartbeat survives full rebuild's finalize tail | happy-path | P1 | `/data` |
| UT-08 | Fresh DB cold-boot honest all-zero coverage | regression | P1 | `/data` |
| UT-09 | Multi-day backfill regression (J-01/J-03/J-04) | regression | P1 | header + `/data` |
| UT-10 | "Snapshot pending" text is self-explanatory | ux | P3 | header |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note:** No validation-type test case is included — the "Start a fetch / backfill job" form was not
added or changed this iteration (per the manual-UI-test-plan-generator skill's own rule: one
validation test per form that was added or changed). Its existing validation behavior is exercised
incidentally by UT-03/UT-04/UT-07/UT-09 without regressing.
