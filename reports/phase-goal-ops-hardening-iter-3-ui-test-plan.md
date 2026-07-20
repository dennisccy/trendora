# Phase goal-ops-hardening-iter-3 — UI Test Plan

**Phase:** goal-ops-hardening-iter-3
**Date:** 2026-07-20
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context

This iteration is a backend-only correctness fix (audit findings B1/B2): a "Fetch EOD prices"
(or "Fetch + backfill") job that lands new data now also refreshes the same "Dataset coverage"
panel on `/data` that previously only refreshed after a "Backfill snapshots" job or a
"Rebuild snapshots for current universe" run. **Zero frontend files changed** — every test below
exercises the existing, unmodified `/data` page; what changed is only whether the numbers it shows
are fresh. The target journey (J-05) and its literal regression (audit finding B1) are UT-02 below.
Required-still-passing journeys J-01/J-03/J-04 are covered as regression checks (UT-04, UT-05, UT-06).

**Not testable via any click path this iteration** (noted so testers do not go looking for them):
- The "expand" job kind half of the B1/B2 fix — no button, form, or control anywhere in the app
  submits an `expand` job (API-only; verified only by the backend's unit tests).
- The stale `coverage_snapshot` row cleanup (B2) — a purely internal database cleanup with no
  on-screen indicator; verifiable only by inspecting the database directly.
- The live health/memory measurement (J-05 step 4) — recorded in `reports/perf-budgets.md`, not
  shown anywhere in the running app. UT-06 below is the closest user-visible proxy (the app staying
  responsive during a heavy job), not the measurement itself.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/data` loads with the Dataset coverage panel visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable (e.g., started via `scripts/start-backend.sh`)
- No login required (single-user local application)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the loading skeleton to disappear

**Expected Result:**
- The "Data Manager" heading is visible, with the subtitle beginning "Grow the dataset on demand…"
- The "Dataset coverage" panel is visible with all seven stat tiles showing a value (not blank): "Price history", "Universe (as of date)", "Candidate universe", "Symbols", "Trading days", "Snapshot dates", "Backfill gaps"
- The "Start a fetch / backfill job" panel and the "Job progress" panel are both visible
- No "Backend unavailable" error card appears
- No blank screen, no crashed page

---

### UT-02 — Fetch job that lands a new bar refreshes coverage in place, and the fix survives a reload (happy-path — target journey J-05 / audit fix B1)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend reachable
- On first load, the "Start date" and "End date" fields in the job form are already pre-filled automatically from the database's own backfill-gap list — no manual date entry is required to start

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Dataset coverage" panel, write down the current values of "Universe (as of date)" (`data-testid="universe-count"`), "Symbols", "Trading days", and "Snapshot dates"
3. In the "Start a fetch / backfill job" panel, set the "Job kind" dropdown to "Fetch EOD prices" — leave the pre-filled "Start date" and "End date" fields as they are
4. If an "Import source" dropdown appears (it only shows for a fetch), leave it at its default selection
5. Click the "Start" button
6. Watch the "Job progress" panel's status badge until it stops spinning and settles on a final value ("ok" or "partial") — do not reload or navigate away yet
7. Without reloading, look at the "Dataset coverage" panel again
8. Now hard-reload the page (press F5) and look at the "Dataset coverage" panel one more time

**Expected Result:**
- After step 6: the status badge reads "ok" (or "partial"), the spinner stops, and a "Symbols fetched" count is shown in the Job progress panel
- After step 7 (same tab, no manual reload): the "Dataset coverage" panel updates itself automatically — at least one of "Symbols", "Trading days", or "Snapshot dates" is now a higher number than what was written down in step 2. (If the pre-filled range happens to land zero new bars on the first try, extend the "End date" a few days further forward and repeat steps 5–7 once more — the pre-filled range is drawn from existing gaps and may occasionally need widening.)
- After step 8 (hard reload): the SAME updated, non-stale numbers from step 7 are shown — this is the proof the fix wrote to storage, not just to the page's in-memory state
- At no point do the coverage numbers fall back to a false all-zero — before this iteration's fix (audit finding B1), a plain fetch could leave "Universe"/"Symbols"/"Trading days"/"Snapshot dates" frozen at stale or all-zero values despite a fully-ingested database; that must NOT happen here

---

### UT-03 — Re-running an already-up-to-date fetch is a fast, silent no-op (regression — zero-work cost-neutrality)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend and backend running; this test is self-contained (it runs its own fetch twice, it does not require UT-02 to have run first)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Set "Job kind" to "Fetch EOD prices", leave the pre-filled Start/End dates as-is, and click "Start"
3. Wait for the status badge to settle on "ok" (or "partial"), then note the "Dataset coverage" panel's numbers and roughly how long the job took (a few seconds at most for the committed offline fixture)
4. Immediately submit the exact same job again: same "Job kind" ("Fetch EOD prices"), same Start date, same End date — click "Start" a second time
5. Wait for the status badge to settle again

**Expected Result:**
- The second run completes in about the same short time as the first — no added delay, no long hang, no spinner stuck noticeably longer
- The "Dataset coverage" panel's numbers after the second run are IDENTICAL to what they were after the first run in step 3 — no flicker, no value change, no re-timestamp
- No error appears; the job still shows a normal terminal status ("ok"), just with nothing new to report

---

### UT-04 — Fresh/never-ingested database shows an honest all-zero coverage on first load (regression — cold-boot, CRITICAL)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Requires a test/QA environment where the backend can be restarted against a genuinely fresh, never-ingested copy of the database (this is an environment-setup precondition, not achievable by clicking alone in a normal shared instance)
- Backend started via `scripts/start-backend.sh` against that fresh database, with zero ingest performed yet this session

**Steps:**
1. As the very first request this session, navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading

**Expected Result:**
- The page returns promptly — no infinite spinner, no error boundary, no crash, no long delay while something computes in the background
- The "Dataset coverage" panel renders with every figure honestly at "0" (Universe, Candidate universe, Symbols, Trading days, Snapshot dates, Backfill gaps) — not blank, not a fabricated non-zero placeholder
- This all-zero state appears immediately on the very first paint, not after a delay

---

### UT-05 — Multi-day "Backfill snapshots" job still renders its breakdown line and updates coverage correctly (regression — shared B2 delete path, required-still-passing J-01/J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend and backend running; the committed database has a range of trading days with existing backfill gaps (the default seeded state normally does)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Note the current "Snapshot dates" and "Backfill gaps" values in the "Dataset coverage" panel
3. In the "Start a fetch / backfill job" panel, set "Job kind" to "Backfill snapshots"
4. Leave the pre-filled multi-day date range as-is (it is drawn from the actual current gap list), and click "Start"
5. Wait for the status badge to settle on "ok"

**Expected Result:**
- The "Job progress" panel shows a breakdown line of the form "N calendar days · N already snapshotted · N non-trading" with real numbers substituted (never blank or "undefined")
- If the range is large enough to require chunking, a "chunk X/Y" badge is shown and its numbers advance as the run progresses (it does not freeze)
- After completion, "Snapshot dates" in the "Dataset coverage" panel increases and "Backfill gaps" decreases, matching the number of gaps just filled
- No coverage figure is missing, corrupted, or stuck at its pre-run value after this completes

---

### UT-06 — Backend stays "Ready" and the job progress panel keeps ticking during a large job (regression/live — required-still-passing J-04, J-05 step-4 user-visible proxy)

**Type:** regression
**Priority:** P1
**Surface:** global header + `/data`

**Preconditions:**
- Backend running via `scripts/start-backend.sh`
- A large job is available to run: either the "Rebuild snapshots for current universe" action, or a "Backfill snapshots"/"Fetch EOD prices" job across a wide multi-month date range

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Look at the readiness badge in the page header (present on every page) and confirm it currently reads "Ready"
3. Start a large job — either click "Rebuild snapshots for current universe" and confirm the action, or submit a "Backfill snapshots" job with a wide multi-month date range
4. While the job runs, glance at the header's readiness badge every 10–15 seconds for the job's duration
5. At the same time, watch the "Job progress" panel's "updated Ns ago" heartbeat text and current-activity line

**Expected Result:**
- Throughout the entire job, the header badge keeps reading "Ready" — it never flips to "Backend unavailable" and never gets stuck on "Checking backend…"
- The heartbeat text keeps advancing (e.g., "updated 2s ago" → "updated 9s ago" → resets) and the current-activity line keeps changing to reflect ongoing work — it never freezes for an extended period or shows "· possibly stalled"
- When the job finishes, the status badge reads "ok", and the rest of the app (other pages, navigation) remains fully responsive throughout — no slowdown to a crawl, no crash

---

### UT-07 — Job form rejects a malformed date before it can be submitted (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- On `/data`, the "Start a fetch / backfill job" panel is visible

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Click into the "Start date" field and replace its contents with `2026-13-40` (an invalid calendar date)
3. Look directly below the "Start date" field
4. Attempt to click the "Start" button

**Expected Result:**
- A red inline message "Enter a valid date as yyyy-MM-dd" appears directly below the "Start date" field, with a small warning-triangle icon
- The "Start date" field's border turns red
- The "Start" button is greyed out (disabled) and cannot be clicked while the invalid value remains in either date field
- No job is started; the "Job progress" panel is unaffected

---

### UT-08 — Backend-unavailable state shows an honest error, not a blank page (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Tester has access to stop the backend process (`scripts/start-backend.sh`'s process), or otherwise make the API unreachable from the frontend

**Steps:**
1. Stop the backend process (or make the API otherwise unreachable)
2. Navigate to `http://localhost:3255/data` (or reload it if already open)
3. Wait for the loading skeleton to resolve

**Expected Result:**
- The page does NOT show a blank white screen, a raw stack trace, or a generic browser network-error page
- A card with a warning-triangle icon and the bold text "Backend unavailable" appears
- Directly below it, the text "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." is visible
- No coverage numbers are shown at all (never a fabricated "0" presented as if it were real data)

---

### UT-09 — "Refreshed: …" status line stays absent for a fetch run but present for a backfill run (regression — `aggregates_refreshed` contract, explicitly unchanged this iteration)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Frontend and backend running; this test is self-contained (runs one fetch and one backfill job itself)

**Steps:**
1. On `/data`, set "Job kind" to "Fetch EOD prices", leave the pre-filled dates, and click "Start"
2. Once it completes, inspect that run's card in the "Job progress" panel, then scroll down to the "Run history" table and find that run's row
3. Now set "Job kind" to "Backfill snapshots", leave the pre-filled dates (or pick a range with existing gaps), and click "Start"
4. Once it completes, inspect its "Job progress" card and its "Run history" row

**Expected Result:**
- Step 2 (fetch run): the card and its Run history row show only a plain summary (a "Symbols fetched" count and the job's message) — NO line beginning with "Refreshed:" appears anywhere on that run's card or row, even though the coverage numbers themselves did update (per UT-02)
- Step 4 (backfill run): the card and its Run history row DO show a line reading "Refreshed: coverage, …" (naming coverage plus whatever other aggregates were refreshed) — confirming the two job kinds still behave differently on this specific status line, exactly as before this iteration

---

### UT-10 — "Job kind" selection is clearly labeled and the form adapts sensibly (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Preconditions:**
- On `/data`, the "Start a fetch / backfill job" panel is visible

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Open the "Job kind" dropdown and read its options
3. Select "Fetch EOD prices"
4. Select "Backfill snapshots"
5. Select "Fetch + backfill"

**Expected Result:**
- The dropdown lists exactly three plainly worded options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill" — no raw internal codes (e.g. "backfill"/"fetch"/"both") are shown to the user
- Selecting "Fetch EOD prices" or "Fetch + backfill" reveals an "Import source" dropdown; selecting "Backfill snapshots" alone hides it — the form visibly adapts to the chosen kind so an operator does not need backend knowledge to know when a data source matters
- No layout breakage, overlap, or leftover fields occur when switching between the three options

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads with coverage panel visible | smoke | P1 | `/data` |
| UT-02 | Fetch lands new bar → coverage refreshes + persists after reload | happy-path | P1 | `/data` |
| UT-03 | Repeat fetch is a fast, silent no-op | regression | P1 | `/data` |
| UT-04 | Fresh DB boot shows honest all-zero coverage | regression | P1 | `/data` |
| UT-05 | Multi-day backfill still renders breakdown + updates coverage | regression | P1 | `/data` |
| UT-06 | Backend stays "Ready", job panel keeps ticking during heavy job | regression | P1 | header + `/data` |
| UT-07 | Malformed date blocks submit with inline error | validation | P2 | `/data` |
| UT-08 | Backend-unavailable shows honest error card | error | P2 | `/data` |
| UT-09 | "Refreshed:" line absent for fetch, present for backfill | regression | P2 | `/data` |
| UT-10 | "Job kind" dropdown is clear and form adapts | ux | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note:** No test case exists for the "expand" job kind or the stale-row (B2) database cleanup — neither has any UI control or on-screen representation this iteration (see "Context" above). No test case exists for the TC-8/TC-9 live health/memory measurement itself (a number recorded in `reports/perf-budgets.md`, not shown in the app) — UT-06 is its user-visible proxy (the app staying responsive), not a substitute for reading that report.
