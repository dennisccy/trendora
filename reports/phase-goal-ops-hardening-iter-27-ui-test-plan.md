# Phase goal-ops-hardening-iter-27 — UI Test Plan

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (`NEXT_PUBLIC_API_URL`; the frontend calls it directly — there is no Next.js `/api` rewrite/proxy)

---

## Screenshot-capture constraint (read before executing any test below)

On this host, a **scrolled-viewport** screenshot returns a solid blank frame — it is a known capture-tool
defect on this box, not a product defect. Any test step below whose expected result lives below the fold
(anything on `/backtest` past the top badge, and the lower panels on `/data`) says so explicitly and
requires:

1. A **full-page** screenshot (or an **element-scoped** capture of the specific panel/section under test) —
   never a viewport screenshot after scrolling.
2. A **DOM-text cross-check** alongside the screenshot — read the element's visible text via the
   accessibility tree / `innerText` / `data-testid` lookup, not the screenshot alone.
3. When a test takes more than one screenshot, **md5-compare the PNG files**. Two supposedly-different
   captures with an identical hash mean the tool returned a blank/frozen frame, not real content — re-capture
   using full-page/element-scoped mode before recording a result.

Any browser-QA run that produces byte-identical screenshots across steps without this cross-check should be
treated as inconclusive, not as a pass.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/data` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend running at `http://localhost:8255`, frontend running at `http://localhost:3255`
- No login required (no auth in this product)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the loading skeleton to disappear (page finishes its first fetch)

**Expected Result:**
- Page renders without a blank screen and without the red "Backend unavailable" error card
- The page heading "Data Manager" is visible at the top
- The panel titled "Dataset coverage" is visible directly below the heading (top of page, no scroll needed)
- No browser console errors

---

### UT-02 — `/data` coverage panel honestly discloses the "stale" state (happy path — this iteration's core capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- The backend must be in the "stale" coverage state: a `CoverageSnapshot` row exists under an OLDER
  `dataset_version` than the current one. The most reliable way to force this state (mirrors the
  developer's own live verification): complete UT-06 first (its two concurrent `/backtest` requests for a
  never-scanned historical date create a new `ScannerRun`, which bumps the global dataset-version stamp
  without running an ingest finalize — exactly the "stale" trigger). Then return here.
- Do NOT run any data ingest/rebuild job between finishing UT-06 and starting this test — that would
  refresh the snapshot to "current" and skip the state this test is checking.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading
3. Look at the "Dataset coverage" panel (the first panel below the page heading — no scroll needed)
4. Read the muted single-line notice directly below the "Dataset coverage" title, above the metric grid
5. Read the "Price history" metric value in the grid
6. Read the "Universe (as of date)" metric value in the grid (element `data-testid="universe-count"`)

**Expected Result:**
- A muted (gray, not red/amber) text line reads exactly: `Coverage as of a prior scan (version
  <dataset_version>) — refreshes on the next data job`, where `<dataset_version>` is a real, non-empty
  version string (element `data-testid="coverage-stale-notice"`)
- "Price history" shows a real date range in `yyyy-MM-dd → yyyy-MM-dd` form (e.g. `1996-01-02 →
  2026-07-22`) — NOT `— → —`
- "Universe (as of date)" shows a non-zero integer — NOT `0`
- All of the above is visible without scrolling past the second panel on the page

---

### UT-03 — `/data` coverage panel's "current" state shows no stale label (regression guard)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- The last `CoverageSnapshot` matches the CURRENT `dataset_version` — the common, everyday case (true on
  a freshly-started backend before any historical `/backtest` request runs, or immediately after any Data
  Manager job's finalize step). If UT-02 was just run, first click the "Rebuild snapshots for current
  universe" button on `/data`, then click "Rebuild snapshots" in the confirmation dialog that appears, and
  wait for the job card to show a completed status before starting this test — that refreshes the snapshot
  back to "current."

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to finish loading
3. Look directly below the "Dataset coverage" title
4. Read the "Price history" and "Universe (as of date)" metric values

**Expected Result:**
- NO "Coverage as of a prior scan…" notice line appears anywhere in the panel
- "Price history" and "Universe (as of date)" show real, non-zero figures
- The panel's layout and figures otherwise look exactly as they did before this iteration — no visual
  regression from the new stale-fallback code path

---

### UT-04 — `/data` coverage panel's "not yet computed" state is unchanged (regression guard, byte-identical)

**Type:** regression
**Priority:** P3 (only reachable on a genuinely fresh-install database — this session's seeded dev database
cannot exhibit it; documented for completeness / a separate empty-DB environment, not this running instance)
**Surface:** `/data`

**Preconditions:**
- A database with zero `CoverageSnapshot` rows under any `dataset_version` (a fresh install that has never
  run an ingest job) — a separate environment from this session's seeded dev database.

**Steps:**
1. Point the frontend at a fresh-install backend instance that has never had a data job run
2. Navigate to `http://localhost:3255/data`
3. Look at the "Dataset coverage" panel

**Expected Result:**
- "Price history" reads `— → —`
- "Universe (as of date)" reads `0`
- No stale notice line appears
- This rendering is byte-identical to the pre-iteration-27 empty state (no new text, no new element)

---

### UT-05 — `/backtest` loads without errors at the latest (default) view (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Backend and frontend running; no `?asof` query param (default = latest view)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the loading skeleton to disappear
3. Take a FULL-PAGE screenshot (not a viewport/scrolled screenshot — see the capture-constraint note above)
   and separately confirm via DOM text extraction that both the "As-of scan summary" and "Forward-test
   scorecard" headings are present in the rendered document (they are far enough down the page that a
   viewport-only view will not show them without scrolling)

**Expected Result:**
- Page renders without a blank screen and without the "Backend unavailable" error card
- Heading "Backtest" is visible at the top
- A badge reading "Latest" is visible near the top (element `data-testid="asof-indicator"`) — NOT a
  "historical" badge
- The full-page capture / DOM check confirms both the "As-of scan summary" heading and the "Forward-test
  scorecard" heading are present somewhere on the page
- No browser console errors

---

### UT-06 — Two concurrent `/backtest` requests for the same never-scanned historical date both succeed (error test — the AG-8 fix)

**Type:** error
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Backend running at `http://localhost:8255`; `logs/backend.log` available to read
- Identify a currently never-scanned historical trading date:
  `curl -s http://localhost:8255/api/runs | grep -o '"asof_date":"[0-9-]*"' | sort -u` — pick any weekday
  date between `1996-01-02` and `2026-07-22` (the seed's covered range) that does NOT appear in that
  output. **Do not reuse `2011-03-10`** — the developer's own live verification for this iteration already
  consumed it (it is no longer never-scanned).
- Before writing any temp files for this test, export the pipeline's isolated temp dir:
  `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-be18659f.820599" TMP="$TMPDIR" TEMP="$TMPDIR"`

**Steps:**
1. Note the current line count of the backend log: `wc -l logs/backend.log`
2. Fire two concurrent requests at the SAME chosen date directly against the BACKEND (not the frontend —
   there is no proxy): `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8255/api/backtest?as_of=<DATE>" & curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8255/api/backtest?as_of=<DATE>" & wait`
3. Record both printed HTTP status codes
4. Run `tail -n +<line-count-from-step-1> logs/backend.log | grep -c "Exception in ASGI application"`
5. Only now, navigate the browser to `http://localhost:3255/backtest?asof=<DATE>` (navigating to this URL
   BEFORE the date has a run would silently degrade to the latest view instead — the race must be fired
   against the backend directly first, per the frontend's own `?asof` validation behavior)
6. Wait for the page to finish loading
7. Take a FULL-PAGE screenshot (never a viewport-only/scrolled capture on this host — see the constraint
   note above) AND independently confirm via DOM text extraction that the "Forward-test scorecard" and
   "As-of scan summary" headings are present
8. If more than one screenshot is taken during this test, md5-checksum each PNG and confirm they are not
   identical to each other or to UT-05's screenshot (an identical hash means a blank/frozen capture — re-run
   the capture in full-page/element-scoped mode)

**Expected Result:**
- Both curl calls in step 2 print `200`
- Step 4's grep count is exactly `0`
- The browser page shows the badge "Viewing as-of `<DATE>` (historical)" (element
  `data-testid="backtest-asof"`) — never a blank page or a Next.js error overlay
- The full-page capture AND the DOM check both show: the "As-of scan summary" heading, a "Market Regime"
  card with a numeric score, and the "Forward-test scorecard" table with column headers "Horizon / Cohort /
  vs SPY / vs QQQ / vs Sector / Random peers / SPY / QQQ / Sector ETF"
- No "Backend unavailable" card, no blank white page, no frozen/partial render

---

### UT-07 — An already-scanned historical `/backtest` view still renders correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Any date already present in `GET http://localhost:8255/api/runs`'s output — the date used in UT-06
  qualifies immediately after that test completes

**Steps:**
1. Navigate to `http://localhost:3255/backtest?asof=<an-already-scanned-date>`
2. Wait for the page to finish loading

**Expected Result:**
- The "Viewing as-of `<date>` (historical)" badge is visible (element `data-testid="backtest-asof"`)
- The Forward-test scorecard table and As-of scan summary render with real figures (not all-zero/blank),
  consistent with what UT-06 already established for this same date
- No "Backend unavailable" card, no blank content

---

### UT-08 — Stale coverage notice reads as calm/factual, never an alarm (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:** Same stale-state precondition as UT-02 (complete UT-06 first, do not run a rebuild job in
between)

**Steps:**
1. With the backend in the stale-coverage state, navigate to `http://localhost:3255/data`
2. Compare the text/background color of the "Coverage as of a prior scan…" notice against: (a) the red
   "Backend unavailable" error-card style (visible by temporarily stopping the backend, or from prior
   familiarity with the product), and (b) the amber "Backfill gaps" warning-tone figure elsewhere in the
   same panel
3. Note how many clicks it took to reach this notice starting from `http://localhost:3255/` (Dashboard)

**Expected Result:**
- The stale notice uses the SAME muted gray/neutral caption tone as the panel's other descriptive text
  (`text-text-muted`) — it uses neither the red error tone nor the amber warning tone
- A first-time reader would understand from this one line alone that the figures are a real prior reading,
  not a broken or empty page — no follow-up click is needed to understand it
- The notice is reached in exactly 1 click from Dashboard (click "Data Manager" in the left sidebar) and 0
  further clicks/scrolling once on `/data` — it sits directly under the "Dataset coverage" title, above the
  metric grid

---

### UT-09 — Required-still-passing journeys smoke sweep (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard), `/backtest`, `/data`, `/stocks`

**Preconditions:** Frontend/backend running, default latest as-of (no `?asof` param)

**Steps:**
1. Navigate to `http://localhost:3255/` — confirm the Dashboard heading and a numeric Market Regime score
   render with no error card
2. Click "Backtest" in the left sidebar — confirm the page (per UT-05) still loads with the "Latest" badge
3. Click "Data Manager" in the left sidebar — confirm the page (per UT-01/UT-03) still loads
4. Click "Stocks" in the left sidebar — confirm the ranked stock list renders with no error card

**Expected Result:**
- All four pages load without a "Backend unavailable" card or blank screen
- No sidebar link is missing, renamed, or reordered from before this iteration ("Dashboard", "Stocks",
  "Themes", "Sectors", "Scanner Runs", "Backtest", "Research", "Evidence", "Watchlist", "Methodology", "Data
  Manager")
- This is a manual smoke-level substitute only — the authoritative pass/fail for J-01/J-03/J-04/J-06/J-09
  is the automated golden-replay suite in TC-09, not this manual click-through

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | Coverage panel discloses "stale" state honestly | happy-path | P1 | `/data` |
| UT-03 | Coverage panel "current" state unchanged | regression | P1 | `/data` |
| UT-04 | Coverage panel "not yet computed" state unchanged | regression | P3 | `/data` |
| UT-05 | `/backtest` loads without errors (latest view) | smoke | P1 | `/backtest` |
| UT-06 | Concurrent `/backtest` race no longer 500s | error | P1 | `/backtest` |
| UT-07 | Already-scanned historical `/backtest` view still works | regression | P1 | `/backtest` |
| UT-08 | Stale notice reads calm, not alarming, discoverable | ux | P2 | `/data` |
| UT-09 | Required-still-passing journeys smoke sweep | regression | P1 | `/`, `/backtest`, `/data`, `/stocks` |

**P1 tests must all pass for browser QA verdict to be PASS.** (UT-01, UT-02, UT-03, UT-05, UT-06, UT-07,
UT-09)
