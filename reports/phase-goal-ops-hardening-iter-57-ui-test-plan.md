# Phase goal-ops-hardening-iter-57 — UI Test Plan

**Phase:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
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
- Frontend is running at http://localhost:3255
- Backend is running and reachable

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error boundary
- The heading "Data Manager" is visible
- The "Per-date availability" card (`data-testid="availability-heatmap"`) is present
- No console errors

---

### UT-02 — `/stocks/AAPL` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Frontend is running at http://localhost:3255
- Backend is running and reachable
- AAPL has price history in the database (present in the committed seed)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error boundary
- "AAPL" is visible in the page
- The "Price & moving averages" card is present with a `data-testid="chart-window-caption"` element showing text
- No console errors

---

### UT-03 — Availability heatmap shows the "updating" banner during an active ingest job (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running and reachable
- Host is otherwise idle (per AG-10, do not run this alongside a heavy test suite or another ingest job)
- `/data` has previously completed at least one ingest, so an `AvailabilityCache` row already exists

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the job form near the bottom of the page, set the "Job kind" dropdown to "Fetch EOD prices"
3. Set the "Job start date" and "Job end date" fields (`data-testid="job-start-date"` / `data-testid="job-end-date"`) to the smallest reasonable range (a single trading day already covered by the committed seed) to minimize job duration and host load
4. Click the "Start" button (the accent button with the Play icon, next to the job kind selector)
5. Within a few seconds of the job starting (before its finalize-tail warm has re-run), reload `http://localhost:3255/data`

**Expected Result:**
- A text element with `data-testid="availability-stale-notice"` reading "Data as of `<some-prior-version>` — updating" appears directly above the calendar grid
- The calendar grid still shows real, non-empty colored day cells (`data-testid="availability-cell"`) — the "No availability yet" empty state does NOT appear
- If the job completes before the reload catches the mid-flight window (job too fast), retry with a wider date range or the "Backfill snapshots" job kind, which takes longer

---

### UT-04 — Idle/matching-stamp availability heatmap renders unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- No ingest job is currently running
- `/data` has previously completed at least one ingest

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Confirm no job is shown as "Job running…" in the job form

**Expected Result:**
- The "Per-date availability" card shows its normal colored calendar grid with `data-testid="availability-cell"` elements
- NO element with `data-testid="availability-stale-notice"` is present anywhere in the card
- The legend, hover readout, and month bands render exactly as before this iteration

---

### UT-05 — Availability heatmap error state is unaffected (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- A way to simulate the `GET /api/data/availability` call failing (e.g., stop the backend momentarily, or use browser DevTools to block the request `**/api/data/availability**`)

**Steps:**
1. In DevTools → Network, add a request-blocking rule for `**/api/data/availability**`
2. Navigate to `http://localhost:3255/data` (or reload if already there)

**Expected Result:**
- The card shows the element `data-testid="availability-error"` with the text "Availability could not load from the API. No cells are shown rather than fabricated values."
- NO stale-notice banner, NO calendar cells, and NO "No availability yet" empty state appear at the same time
- Remove the blocking rule afterward to restore normal behavior

---

### UT-06 — Global readiness badge answers within budget on every page (regression / performance)

**Type:** regression
**Priority:** P1
**Surface:** header (all pages)

**Preconditions:**
- Backend is idle (no ingest job running)

**Steps:**
1. Open DevTools → Network tab and clear it
2. Navigate to `http://localhost:3255/`
3. Find the `GET /api/health` request in the Network tab

**Expected Result:**
- The request's duration is well under 100ms (previously measured 160-241ms)
- The header badge (`data-testid="readiness-badge"`) shows `data-state="ready"` and the text "Ready"
- Repeat on 2-3 other pages (e.g. `/stocks`, `/scanner-runs`) — every `GET /api/health` reading stays under 100ms at rest

---

### UT-07 — Stock Detail price chart loads within budget with correct data (regression / performance)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- Backend is idle (no ingest job running)
- AAPL has price history

**Steps:**
1. Open DevTools → Network tab and clear it
2. Navigate to `http://localhost:3255/stocks/AAPL`
3. Find the `GET /api/stocks/AAPL/bars?through=latest` request in the Network tab

**Expected Result:**
- The request's duration is well under 1.5s (previously measured up to 6.2s)
- The `chart-window-caption` element shows real text (e.g. "N bars · as of YYYY-MM-DD · history since YYYY-MM-DD")
- The price chart renders its moving-average lines (SMA-20/50/150/200 per the configured `indicators.ma_periods`) without gaps or errors

---

### UT-08 — Stale banner is discoverable and calmly styled, not alarming (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Same as UT-03 (an ingest job in-flight, mid-way between its first committed bar and finalize)

**Steps:**
1. Follow UT-03's steps 1-5 to get the stale banner on screen
2. Visually compare the banner to the existing "Coverage as of a prior scan" notice further down the same page (in the "Dataset coverage" card, `data-testid="coverage-stale-notice"`)

**Expected Result:**
- Both notices use the same visual treatment: a thin bordered row with a muted background and small muted-gray text — no red/amber/alarm coloring, no icon suggesting an error
- The banner text is legible and factual ("Data as of `<version>` — updating"), positioned directly above the calendar grid, not overlapping or hiding any cells
- A first-time user could reasonably infer "the data shown is current-ish, a refresh is in progress" without needing developer context

---

### UT-09 — Job history "Refreshed" note still shows normally after a successful job (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` (job history rows)

**Preconditions:**
- At least one previously-completed Backfill or "Fetch + backfill" job exists in the job history

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the job history / run list section
3. Locate a completed Backfill (or Fetch + backfill) job row that has aggregate data

**Expected Result:**
- The row shows a `data-testid="aggregates-refreshed"` text reading "Refreshed: `<aggregate names>`" (e.g. "Refreshed: availability heatmap") exactly as before this iteration
- This confirms the `persisted_this_call` rollback honesty fix did not change the normal successful-save case, only the (untestable-via-UI) rollback case

---

### UT-10 — Rollback honesty fix verified via unit test (regression, backend-only)

**Type:** regression
**Priority:** P3
**Surface:** backend (`data_manager.py` / `indexes.py`) — not browser-drivable

**Preconditions:**
- Backend repo checked out at this iteration's commit

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_indexes.py -k rollback -v`

**Expected Result:**
- Both the `data_manager` and `indexes` rollback tests pass and assert `persisted_this_call is False` after a forced commit failure
- No UI action can independently trigger or observe this path — recorded here so the phase-closure gate has an explicit verification method for DoD item "TC-10"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads | smoke | P1 | `/data` |
| UT-02 | `/stocks/AAPL` loads | smoke | P1 | `/stocks/{ticker}` |
| UT-03 | Stale "updating" banner appears during a job | happy-path | P1 | `/data` |
| UT-04 | Idle heatmap unchanged (no banner) | regression | P1 | `/data` |
| UT-05 | Availability error state unaffected | error | P2 | `/data` |
| UT-06 | Readiness badge answers within budget | regression | P1 | header (all pages) |
| UT-07 | Stock chart answers within budget | regression | P1 | `/stocks/{ticker}` |
| UT-08 | Banner discoverable, calm styling | ux | P2 | `/data` |
| UT-09 | "Refreshed" note unaffected on success | regression | P2 | `/data` |
| UT-10 | Rollback honesty fix (unit test) | regression | P3 | backend |

**P1 tests must all pass for browser QA verdict to be PASS.**
