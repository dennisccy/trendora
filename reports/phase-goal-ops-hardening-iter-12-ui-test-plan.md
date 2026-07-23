# Phase goal-ops-hardening-iter-12 — UI Test Plan

**Phase:** goal-ops-hardening-iter-12
**Date:** 2026-07-22
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Read this before running anything

This iteration shipped **zero frontend/backend source changes** (`reports/phase-goal-ops-hardening-iter-12-ui-surface-map.md`
confirms `git diff --stat -- apps/backend apps/frontend` is empty). `Frontend Present: yes` was set
deliberately so this browser-qa lane still runs against the **already-shipped, unchanged** surfaces, for two
reasons only:

1. **G2** needs three independent, cache-disabled, fresh-navigation real-Chrome loads of `/data` timing
   `GET /api/indexes?full=true`, each cross-checked against `logs/backend.log` and `logs/hwmon/hwmon.csv` for
   a genuinely idle window — this is the missing like-for-like control for J-06's over-budget reading.
2. **J-01, J-03, J-04, J-05** are "required-still-passing" this iteration — they must be re-verified green,
   not assumed.

No test case below expects to find a NEW button, panel, or message. Every "Expected Result" describes
**pre-existing** behavior that must still hold.

**Operational notes for whoever executes this plan:**

- **Agents cannot start, stop, or restart services this session** (permission classifier blocks it).
  Backend (`:8255`) and frontend (`:3255`) are already running with host-guard caps live — no service
  action is needed for the vast majority of steps. The few steps that need a backend restart/crash
  (J-04, marked **[OPERATOR-PERFORMED ACTION]** below) must be requested of the human operator; do not
  attempt to trigger them yourself.
- **`/data` is unusually tall (~17,800px).** A Chrome-MCP full-page `screenshot` on this route reliably
  returns a blank capture. Do NOT rely on a screenshot to confirm anything on `/data` — use a DOM query /
  JS assertion against the specific element (by its `data-testid`) taken at the same instant instead. This
  is called out explicitly in every `/data` step below.
- A known, already-flagged **critical issue (AG-8)** exists: `compute_forward_aggregates`'s unbounded
  `ScannerResult` load can `MemoryError` on a cache miss (a backfill landing a genuinely new trading date),
  which has previously cascaded into an HTTP 500 on `GET /api/data`. This is a carried-forward OWNER
  decision, out of scope for this iteration's fix — UT-15 below exists only to confirm the degrade stays
  honest (a contained error message), not to re-litigate or attempt to fix it. Do not treat UT-15 firing as
  a new regression.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` loads without errors, all panels present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8255 (already up — no
  service action needed)
- No login required (this application has no auth)
- At least one prior fetch/backfill run exists in history (true on this environment already)

**Steps:**
1. Open a fresh Chrome tab
2. Navigate to `http://localhost:3255/data`
3. Wait for the page's initial loading skeleton to disappear (the skeleton is a set of pulsing gray bars;
   once real content replaces it, loading is complete)

**Expected Result:**
- The page renders the "Data Manager" heading with subtitle "Grow the dataset on demand — view coverage
  and gaps, then fetch real EOD history and/or backfill immutable snapshots by date or range..."
- The job submission form is visible with a "Start date" field, an "End date" field, and a "Job kind"
  dropdown (options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill")
- The "Index & benchmark data provenance" panel (`data-testid="index-vendor-panel"`) is present somewhere
  on the page (query the DOM for this test-id — do not rely on a screenshot, per the page-height caveat
  above)
- No "Backend unavailable" error card is shown anywhere on the page
- No blank white page and no browser console errors

---

### UT-02 — G2 control reading #1: fresh-navigation `/api/indexes?full=true` timing with idle confirmation (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- No backfill/fetch/rebuild job is currently in-flight — confirm by tailing `logs/backend.log` for the
  last 2 minutes and checking there is no unterminated job-start line (every prior job-start line already
  has a matching completion/failure line)
- `logs/hwmon/hwmon.csv` is actively appending (its last row's timestamp is within the last 60 seconds)
- Chrome DevTools open, Network panel visible, "Disable cache" checkbox checked

**Steps:**
1. Record the current UTC timestamp (`date -u +"%Y-%m-%dT%H:%M:%SZ"`)
2. Open a brand-new Chrome tab (do not reuse any tab from a prior reading)
3. Navigate to `http://localhost:3255/data`
4. In the Network panel, locate the request whose path is `/api/indexes?full=true`; wait for it to reach
   status 200 and record its "Time" column value (total duration, in ms)
5. Grep `logs/backend.log` for the one-minute window covering this request's timestamp; confirm no
   "backfill", "fetch", or "rebuild" job-start line appears in that window
6. Open `logs/hwmon/hwmon.csv` and find the row whose timestamp is closest to the reading in step 4;
   record its `load1` and `MemAvailable` values
7. Using a DOM query (not a screenshot — page-height caveat), confirm the "Index & benchmark data
   provenance" panel (`data-testid="index-vendor-panel"`) has transitioned out of its loading state
   (`data-testid="index-vendor-loading"` is gone) and now shows a populated table

**Expected Result:**
- The `GET /api/indexes?full=true` request completes with HTTP 200 and a recorded duration
- `logs/backend.log` shows no concurrent ingest job in-flight during that same window
- `logs/hwmon/hwmon.csv`'s nearest row shows `load1` and `MemAvailable` within the already-established idle
  baseline (`load1 < 2.0`, `MemAvailable` comfortably above zero — no near-OOM reading)
- The "Index & benchmark data provenance" panel shows real rows (ticker, vendor, first-bar date), not
  stuck on its loading skeleton and not showing "Vendor disclosure unavailable"

---

### UT-03 — G2 control reading #2: independent second fresh-navigation reading (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:** Same as UT-02. This must be a SEPARATE fresh tab from UT-02's — never a reload of the
same tab.

**Steps:**
1. Repeat UT-02's steps 1–7 exactly, in a new fresh Chrome tab distinct from the one used in UT-02

**Expected Result:** Same as UT-02 — an independent HTTP 200 reading with its own idle-window confirmation
from `logs/backend.log` and `logs/hwmon/hwmon.csv`, and the provenance panel populated.

---

### UT-04 — G2 control reading #3: independent third fresh-navigation reading (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:** Same as UT-02. This must be a THIRD, separate fresh tab — never a reload of UT-02's or
UT-03's tab.

**Steps:**
1. Repeat UT-02's steps 1–7 exactly, in a third fresh Chrome tab distinct from the ones used in UT-02 and
   UT-03
2. After all three readings (UT-02, UT-03, UT-04) are collected, mark each one "holds: yes" if its duration
   is ≤ 1.5s, or "holds: no — over by <exact ms>" if it exceeds 1.5s

**Expected Result:** Same as UT-02 — an independent HTTP 200 reading with its own idle-window confirmation.
All three readings (UT-02/03/04 combined) are honestly marked against the ≤1.5s budget — none silently
omitted or averaged into a single favorable number.

---

### UT-05 — Backfill form rejects a malformed date (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` is loaded, job submission form visible, no job currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2026-13-40` into the "Start date" field (`data-testid="job-start-date"`)
3. Observe the field immediately below it

**Expected Result:**
- A red inline error appears directly below the "Start date" field reading exactly "Enter a valid date as
  yyyy-MM-dd" (`data-testid="job-start-date-error"`)
- The "Start date" input's border turns red (invalid state)
- The "Start" submit button remains disabled/does not submit while the field is in this state
- No job is created and no network request to `POST /api/data/jobs` is sent

---

### UT-06 — Backfill spanning more than 370 days is accepted, no range-cap rejection (regression — J-01/J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` is loaded, no job currently running (Job progress panel shows no "running" badge)
- No in-flight job per `logs/backend.log` (same check as UT-02 precondition)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Type `2025-06-01` into the "Start date" field
3. Type `2026-07-17` into the "End date" field (a span of more than 370 calendar days)
4. Leave "Job kind" on its default "Backfill snapshots"
5. Click the "Start" button
6. Wait 2 seconds, then query the DOM for any error text on the form (`role="alert"` element inside the
   job form) — do not rely on a screenshot

**Expected Result:**
- No "date range too large" or any range-cap rejection error appears anywhere on the form
- The "Start" button switches to its running state (shows a spinner icon and the text "Job running…")
- The Job progress panel (`PanelTitle` "Job progress") replaces its empty-state copy with a live status
  badge (`data-testid="job-status"`)

---

### UT-07 — Job progress panel shows live progress while the backfill runs (regression — J-01/J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:** UT-06 has just been submitted and the job is running (or was submitted moments ago).

**Steps:**
1. On the same `/data` tab from UT-06, without navigating away, observe the "Job progress" panel
2. Query the DOM for `data-testid="job-status"` (or `data-testid="chunk-progress"` if the job is chunked)
   and note its text every few seconds — do not rely on a screenshot (page-height caveat)
3. Wait for the job to reach a terminal state (its badge stops showing a spinner)

**Expected Result:**
- While running, the status badge shows a spinning loader icon plus a live status message
- If the job is chunked, a "chunk N/M" badge (`data-testid="chunk-progress"`) is visible and N increases
  over successive checks
- Once terminal, the badge shows one of: "ok", "partial", "failed", or (for a zero-new-snapshot day range)
  a distinctly-labeled zero-work outcome — never a bare, unexplained green success badge if zero snapshots
  were created
- A line reading "`<N>` snapshots · `<M>` trading days in range" is visible under the badge, with `<N>` and
  `<M>` both numeric (not blank, not "—" unless genuinely unknown)

---

### UT-08 — Job history row persists with the same outcome after a page reload (regression — J-01)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:** UT-06/UT-07's job has reached a terminal state (ok/partial/failed/zero-work).

**Steps:**
1. Note the terminal status badge text and the "`<N>` snapshots · `<M>` trading days" line from UT-07
2. Press F5 (or Cmd+R) to fully reload `http://localhost:3255/data`
3. Wait for the page to finish loading
4. Query the DOM for the "Run history" table (`PanelTitle` "Run history") and locate the row whose
   "Started" timestamp matches this job's start time

**Expected Result:**
- The "Run history" table still lists this run, with the same "Status" badge (`data-testid="run-status"`)
  as before the reload
- The "Symbols ok/failed" and "Snapshots" columns show the same counts as before the reload
- If the run created zero new snapshots on an already-covered range, the breakdown text
  (`data-testid="backfill-breakdown"`) still shows the exclusion reasons (e.g., "N already snapshotted",
  "N non-trading") rather than a blank cell

---

### UT-09 — Scanner Runs list renders a backfilled date immediately, no delay (regression — J-01/J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/scanner-runs`

**Preconditions:**
- At least one previously-backfilled trading date exists in the database (true after UT-06, or already
  true from prior iterations)

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Wait for the loading skeleton (a stack of pulsing gray bars) to disappear
3. Locate the row for a previously-backfilled date in the table (columns: "As of", "Regime", "Actionable",
   "Breakout-watch", "Pullback-watch", "Stocks")

**Expected Result:**
- The row for that date is fully populated the instant the skeleton clears — a real regime badge and
  numeric counts, not a spinner or "—" placeholder inside the row itself
- No error card reading "Backend unavailable" is shown
- Clicking the date link navigates to `http://localhost:3255/scanner-runs/<runId>`

---

### UT-10 — Scanner Run detail leaderboard matches the stored snapshot (regression — J-01/J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/scanner-runs/[runId]`

**Preconditions:** UT-09's run detail page is reachable.

**Steps:**
1. From `/scanner-runs`, click a previously-backfilled date's row
2. On the resulting `/scanner-runs/<runId>` page, wait for the page heading "Scanner Run" (subtitle "The
   exact, immutable as-of view the scanner produced on this date") to render
3. Query the DOM for the leaderboard table (columns: "#", "Ticker", "Sector", "Leadership", "Entry
   Quality", "Risk", "Setup", "Reason") and record the first 3 rows' Ticker + Setup values
4. Cross-check those same 3 rows against the `scanner_results` database record for that `run_id` (read-only
   query)

**Expected Result:**
- The rendered Ticker + Setup values for all 3 sampled rows match the stored `scanner_results` record
  exactly — no recomputed/different value
- The "Candidate Counts" card above the table shows the same counts as the stored `candidate_counts` field

---

### UT-11 — Market Phase & Severity card renders without a compute-on-read stall (regression — J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/` (home / Dashboard)

**Preconditions:** At least one trading date has a `market_phase_cache` entry (true on this environment).

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Wait for the page heading "Dashboard" (subtitle "The daily snapshot at a glance") to render
3. Observe the "Market Phase & Severity" card (has an Activity icon next to its title)
4. Time how long the card's loading skeleton (a single pulsing gray block) is visible before real content
   (a phase badge such as "Risk-on"/"Defensive"/etc., plus an "as of `<date>`" label) appears

**Expected Result:**
- The card transitions from its loading skeleton to populated content within roughly 1–2 seconds (a served
  cache read, not a multi-second live recompute)
- The card never shows "Market phase unavailable" during normal operation
- The phase badge and "as of `<date>`" text are both present once loaded

---

### UT-12 — Health badge shows boot-phase detail with progress n/m during a restart (regression — J-04)

**Type:** regression
**Priority:** P1
**Surface:** top bar (all pages)

**Preconditions:** **[OPERATOR-PERFORMED ACTION REQUIRED]** — agents in this pipeline cannot start, stop,
or restart the backend. This test case requires the human operator to restart the backend process; the
tester only observes the UI during and after that restart. Do not attempt to trigger the restart yourself.

**Steps:**
1. Have any page open in Chrome with the top-bar health badge visible (`data-testid="readiness-badge"`)
2. **[OPERATOR-PERFORMED ACTION]** Operator restarts the backend process and records the exact restart
   timestamp
3. Immediately after the restart begins, in the same browser tab, poll `GET http://localhost:8255/api/health`
   at ≤250ms intervals from the operator's recorded restart timestamp
4. In the same time window, query the DOM for `data-testid="readiness-badge"` and its `data-state`
   attribute at each poll interval

**Expected Result:**
- During the pre-ready window, the badge shows `data-state="initializing"` with the text "Initializing…
  history `<n>`/`<m>`" — the same `n`/`m` progress numbers the raw `/api/health` payload reports at that
  instant (not a bare "Backend unavailable" during this window)
- Once ready, the badge switches to `data-state="ready"` with the text "Ready"
- At no point during a normal restart does the badge show `data-state="unavailable"` ("Backend unavailable")
  while the process is merely warming up

---

### UT-13 — Preflight banner shows an explicit NO-GO state distinct from initializing (regression — J-04)

**Type:** regression
**Priority:** P1
**Surface:** global banner (all pages)

**Preconditions:** **[OPERATOR-PERFORMED ACTION REQUIRED]** — same constraint as UT-12. This requires the
operator to simulate a backend crash/unreachable state (e.g., kill the backend process) while the tester
observes the frontend.

**Steps:**
1. Have any page open with the global preflight banner visible (`data-testid="preflight-banner"`)
2. **[OPERATOR-PERFORMED ACTION]** Operator stops/crashes the backend process
3. Within one health-poll interval, query the DOM for `data-testid="preflight-banner"` and its
   `data-verdict` attribute

**Expected Result:**
- The banner switches to `data-verdict="NO-GO"`, a loud full-width banner with the exact text "NO-GO — do
  not rely on today's board." and the reason "Backend is unavailable — the preflight check could not run."
- This NO-GO presentation is visibly distinct from the earlier initializing-badge state (different color —
  danger red vs. the neutral "Checking board status…" strip) — never a blank page or an unstyled crash
- **[OPERATOR-PERFORMED ACTION]** Operator restarts the backend so subsequent test cases can run; confirm
  the banner returns to `data-verdict="GO"` ("GO — today's board is current.") once ready

---

### UT-14 — Unfinished imports panel shows "Interrupted", not "running", for a job killed mid-flight (regression — J-04)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:** **[OPERATOR-PERFORMED ACTION REQUIRED]** — requires the operator to start a job and
then crash the backend mid-flight, as part of the same crash exercise as UT-12/UT-13. Do not attempt this
without the operator's involvement.

**Steps:**
1. Submit a fetch or backfill job on `/data` (any small date range) so a job is actively running
2. **[OPERATOR-PERFORMED ACTION]** While the job is still running (chunk/status badge showing "running"),
   operator crashes and then restarts the backend
3. After the backend is back up, reload `http://localhost:3255/data`
4. Query the DOM for the "Unfinished imports" panel (`data-testid="unfinished-imports"`) and/or the "Run
   history" table row for the job that was mid-flight at crash time

**Expected Result:**
- The row for the job that was running at crash time now shows an explicit "Interrupted" badge
  (`data-testid="run-status"` or the unfinished-imports row's status badge), never still labeled "running"
  with a spinner and no living process behind it
- The row shows its last persisted progress (symbols/snapshots counted before the crash), not a blank or
  zeroed-out row

---

### UT-15 — Known-issue watch: a cache-miss `MemoryError` degrades honestly, never a blank crash (error / AG-8 awareness)

**Type:** error
**Priority:** P2 — informational; a recurrence here is a PRE-EXISTING, already-flagged critical issue
(AG-8), not a new regression to fail this iteration over. Fixing it is explicitly out of scope this
iteration.

**Surface:** `/data`

**Preconditions:**
- Understand before running: this test only OBSERVES behavior if the AG-8 cache-miss path is triggered
  (e.g., a backfill lands a genuinely new trading date not previously ingested). Do NOT deliberately try to
  force this path outside of a backfill that is already part of this iteration's required testing (UT-06) —
  this iteration explicitly excludes any new heavy-ingest/full-universe backfill (AG-10; two host hard-resets
  already occurred this week under heavy ingest bursts)

**Steps:**
1. If, during UT-06's normal backfill replay, the backend logs a `MemoryError` in `logs/backend.log` (grep
   for "MemoryError" in the window around the job's completion time) and/or a subsequent `GET /api/data`
   request returns HTTP 500
2. Reload `http://localhost:3255/data` and observe the coverage section

**Expected Result:**
- If the MemoryError/500 occurs, the coverage section shows the existing contained error card — heading
  "Backend unavailable", body "Dataset coverage could not load from the API. No figures are shown rather
  than fabricated values. Confirm the backend is running and retry." — NEVER a blank white page or an
  unstyled JavaScript stack trace
- If the MemoryError/500 does NOT occur during this iteration's testing, this test case is recorded as
  "not triggered" — that is an acceptable, non-blocking outcome; do not force it

---

### UT-16 — The `/api/indexes`-driving panel is discoverable within 2 clicks of home (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / `/data`

**Steps:**
1. Navigate to `http://localhost:3255/` (home)
2. Click "Data Manager" (or the equivalent nav label) in the top navigation
3. On the resulting `/data` page, scroll/query the DOM for the "Index & benchmark data provenance" panel

**Expected Result:**
- The panel is reached in exactly 2 clicks from home (nav click → land on `/data`, panel is already present
  on the page, no further click needed)
- Its section heading reads exactly "Index & benchmark data provenance" with the hint text "Every
  index/benchmark/macro line on the major-indexes chart, with its honest data vendor and real first-bar
  date — the same GET /api/indexes payload the Dashboard chart reads, never a recompute." — a clear,
  non-jargon label for what this panel is showing

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | G2 reading #1 (fresh nav + idle check) | happy-path | P1 | `/data` |
| UT-03 | G2 reading #2 (fresh nav + idle check) | happy-path | P1 | `/data` |
| UT-04 | G2 reading #3 (fresh nav + idle check) | happy-path | P1 | `/data` |
| UT-05 | Malformed date rejected | validation | P2 | `/data` |
| UT-06 | >370-day backfill accepted | regression | P1 | `/data` |
| UT-07 | Live job progress counters | regression | P1 | `/data` |
| UT-08 | Job history persists after reload | regression | P1 | `/data` |
| UT-09 | Scanner Runs list renders immediately | regression | P1 | `/scanner-runs` |
| UT-10 | Run detail leaderboard matches stored data | regression | P1 | `/scanner-runs/[runId]` |
| UT-11 | Market Phase card, no compute stall | regression | P1 | `/` |
| UT-12 | Health badge boot-phase n/m detail | regression | P1 | top bar |
| UT-13 | Preflight banner NO-GO state | regression | P1 | global banner |
| UT-14 | Unfinished imports "Interrupted" state | regression | P1 | `/data` |
| UT-15 | AG-8 graceful-degrade watch | error | P2 (informational) | `/data` |
| UT-16 | Provenance panel discoverable in 2 clicks | ux | P3 | nav / `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-12/UT-13/UT-14 additionally require an
**[OPERATOR-PERFORMED ACTION]** (backend restart/crash) — if the operator does not perform this action
during the test window, mark these three "SKIPPED — operator action not available this session" rather
than failing them; per this project's rules, a skip must carry this documented reason, never a silent
"could not run."

**UT-15 is informational only** — its outcome (triggered or not) does not gate this iteration's PASS
verdict; the AG-8 fix itself is an explicit, out-of-scope OWNER decision.
