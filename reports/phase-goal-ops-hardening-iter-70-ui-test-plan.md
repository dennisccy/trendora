# Phase goal-ops-hardening-iter-70 — UI Test Plan

**Phase:** goal-ops-hardening-iter-70
**Date:** 2026-08-12
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Scope note (backend-only iteration)

`Frontend Present: no` for this iteration (see
`reports/phase-goal-ops-hardening-iter-70-user-visible-changes.md` and
`reports/phase-goal-ops-hardening-iter-70-ui-surface-map.md` — both N/A, zero UI surface rows). This
iteration's own change is a request-path-to-cache redesign for `GET /api/health`: a bounded-interval
background-refresh thread now computes `compute_readiness`/`compute_preflight` on a tick instead of on
every request, closing the session's health-poll breach rate measured during a heavy background warm. The
response body/shape is byte-identical (same field names, types, values) to before, so no route,
component, form, chart, modal, or table in `apps/frontend/*` changed — **no NEW-surface smoke/happy-path/
validation/error/UX test cases are generated** (nothing to derive them from).

The phase spec names both a `Target journeys:` line (`J-07`) and a `Required-still-passing journeys:` line
(`J-01, J-03, J-04, J-05, J-06, J-08, J-09`). Per the ui-test-designer's binding backend-only handling
rule, every journey named on **either** line gets exactly one regression test case below, ID
`UT-<journey-id>`, `Type: regression`, `Priority: P1` — translated from that journey's own Steps/
Acceptance text in `docs/goal.md`'s "Must-have user journeys" section into exact URL / exact
selector-or-text / exact expected format. This closes the exact gap iter-40/41 identified: promoting a
journey to a `Target journeys:` line must never silently drop its verification, and a
required-still-passing journey must never ship with zero test coverage.

Selectors, button text, and exact expected strings below are cross-checked against the currently-shipped,
currently-passing deterministic replay goldens
(`runs/goal-session-ops-hardening/journey-scripts/J-*.json`) and their own trailing `_notes` (most
recently live-verified iter-62 for J-01/J-04, iter-64/iter-66 for J-05's date-resolution mechanism, and
unmodified since original authorship for J-03/J-06/J-07/J-08/J-09) so every step is grounded in what the
live app actually renders, not invented. Frontend testids referenced below
(`job-start-date`/`job-end-date`/`last-run-status`/`aggregates-refreshed`/`stage-timings`/
`zero-work-note`/`backfill-breakdown`/`background-compute-panel`/`readiness-badge`/`preflight-banner`/
`evidence-aggregate`/`evidence-summary`/`chart-window-caption`/`availability-cell`/`job-status`) were
confirmed present in `apps/frontend/components/` and `apps/frontend/app/` source by direct grep
immediately before writing this plan.

---

## Test Cases

<!-- Test IDs use UT-<journey-id> per the backend-only-phase regression convention (not the sequential
     UT-01/UT-02 scheme, which only applies to NEW-surface cases derived from a UI surface map row). -->

---

### UT-J-01 — Backfill honors the requested range and explains zero-work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs/748`

**Preconditions:**
- Backend (prod mode, `scripts/start-backend.sh`) and frontend running at `http://localhost:3255`
- This dataset's May 2026 trading days (2026-05-04 … 2026-05-29) already carry snapshots from many prior
  verification passes — both backfills below are EXPECTED to report a zero-work ("already snapshotted")
  outcome; that is the currently-passing behavior under test, not a new expectation. This iteration
  touches only `app.engine.readiness`/`app/api/health.py`/`main.py`/the `_refresh_ingest_aggregates`
  finalize hook's own trigger call — none of J-01's backfill/job-submission code path.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Expect the heading "Data Manager" to be visible
3. Type "2026-05-02" into the "Start date" field (`data-testid="job-start-date"`)
4. Type "2026-05-29" into the "End date" field (`data-testid="job-end-date"`)
5. Click the "Start" button
6. Wait for the job to finish (progress panel stops updating; allow at least 15 seconds)
7. Expect the text "19/19 dates" to appear
8. Expect the per-stage timings panel (`data-testid="stage-timings"`) to be visible
9. Expect the text "28 calendar days · 19 already snapshotted · 9 non-trading" to appear
10. Expect the zero-work explanatory note (`data-testid="zero-work-note"`) to appear, styled distinctly
    (neutral border/background) — NOT the same green success badge a productive run would show
11. Type "2026-05-02" into the "Start date" field, "2026-05-03" into the "End date" field, click "Start"
12. Expect the text "0/0 dates" to appear
13. Expect the text "2 calendar days · 0 already snapshotted · 2 non-trading" to appear
14. Reload `http://localhost:3255/data` (fresh navigation) and expect the text "Run history" to appear
15. Confirm both runs from steps 5 and 11 are still listed in the Run history panel with the same
    zero-work explanations — never "no job started this session"
16. Navigate to `http://localhost:3255/scanner-runs/748` and expect the text "as of 2026-05-29" to appear

**Expected Result:**
- Both backfill submissions are accepted — no "date range too large" or generic rejection appears
- Job counts match exactly: "19/19 dates" / "28 calendar days · 19 already snapshotted · 9 non-trading"
  (first run); "0/0 dates" / "2 calendar days · 0 already snapshotted · 2 non-trading" (weekend-only run)
- Both zero-work outcomes render with the neutral zero-work-note styling, never the productive-run
  success treatment
- The persisted Run history panel still lists both runs after a fresh page reload
- `/scanner-runs/748` shows "as of 2026-05-29" with a populated leaderboard (stored values, not blank)

---

### UT-J-03 — No per-run range cap (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend/frontend running at `http://localhost:3255`; `config.yaml`'s `import_chunking` values unchanged
  by this iteration

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Expect the heading "Data Manager" to be visible
3. Type "2025-06-01" into the "Start date" field (`data-testid="job-start-date"`)
4. Type "2026-07-17" into the "End date" field (`data-testid="job-end-date"`) — a 412-calendar-day span,
   well over the old (removed) 370-day cap
5. Click the "Start" button
6. Expect NO "date range too large" (or any similar rejection) message to appear
7. Expect the text "283/283 dates" to appear
8. Expect the per-stage timings panel (`data-testid="stage-timings"`) to be visible, confirming the job
   executed in visible chunks rather than one opaque jump
9. Expect the text "412 calendar days · 283 already snapshotted · 129 non-trading" to appear

**Expected Result:**
- No rejection of any kind appears for the >370-day span
- The job runs to completion with progress visibly advancing in chunks
- Final counts read exactly "283/283 dates" and "412 calendar days · 283 already snapshotted · 129
  non-trading"

---

### UT-J-04 — Non-blocking boot with visible status (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/data`

**Preconditions:**
- Backend started via `scripts/start-backend.sh` (prod mode); frontend at `http://localhost:3255`
- This iteration adds a NEW daemon thread (the readiness-refresh background tick) to the SAME `lifespan`
  boot sequence that already starts `app.engine.warmup.start_warmup` in `apps/backend/main.py` — this is
  the closest regression check to that specific change, since a badly-behaved new thread could in
  principle slow or block boot

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Expect the readiness badge element (`data-testid="readiness-badge"`) to be present
3. Wait up to 20 seconds for the readiness badge's `data-state` attribute to read `"ready"`
4. Expect the readiness badge to show `data-state="ready"` — read the badge's own attribute, not a page
   heading/title
5. Expect the preflight banner element (`data-testid="preflight-banner"`) to be visible on the same page
6. Navigate to `http://localhost:3255/data`
7. Expect the `last-run-status` element (`data-testid="last-run-status"`) to render a real, non-blank
   status (e.g. "no new snapshots" or "ok") sourced from a persisted `data_provider_runs` record

**Expected Result:**
- The readiness badge reaches `data-state="ready"` within 20 seconds of page load on a warm backend —
  same budget as before this iteration's new background thread was added to boot
- The preflight banner is mounted and shows a real verdict text (e.g. "GO — today's board is current."),
  never a blank or missing element
- `/data`'s `last-run-status` shows a genuine persisted value — never blank, "undefined", or fabricated

---

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs`

**Preconditions:**
- Backend/frontend running at `http://localhost:3255`
- Since iter-64, this journey's deterministic replay golden no longer hand-picks a target date; it
  resolves the earliest still-unsnapshotted trading day inside a 2005-03-01..2016-12-31 window
  automatically at replay time. For a MANUAL operator run, pick the target date the same way: navigate to
  `http://localhost:3255/scanner-runs` first and choose any historical trading day inside 2005–2016 that
  does NOT already appear in the list (call it `<TARGET_DATE>` below) — this guarantees the backfill
  creates a genuinely NEW snapshot rather than reporting a zero-work re-run
- **This is a REAL live ingest job.** Prior measured runs of this exact one-day backfill have taken
  between 11 and 25 minutes end-to-end (five measurements on record, trending upward as the dataset
  grows) — this is not a 5-minute check; budget up to 40 minutes before treating it as stalled

**Steps:**
1. Navigate to `http://localhost:3255/data`; expect the heading "Data Manager" to be visible
2. Type `<TARGET_DATE>` into the "Start date" field (`data-testid="job-start-date"`)
3. Type `<TARGET_DATE>` into the "End date" field (`data-testid="job-end-date"`)
4. Click the "Start" button
5. Wait ~15 seconds; expect the `job-status` element (`data-testid="job-status"`) to show the job has
   actually started running — not stuck on "accepted"
6. Wait for the backfill to run to completion (allow up to 40 minutes before treating it as stalled)
7. Expect the text "1/1 dates" to appear
8. Expect the per-stage timings panel (`data-testid="stage-timings"`) to be visible
9. Expect the `backfill-breakdown` element (`data-testid="backfill-breakdown"`) to read exactly
   "1 calendar day · 0 already snapshotted · 0 non-trading"
10. Expect the text "1 snapshots" to appear
11. Expect the `aggregates-refreshed` element (`data-testid="aggregates-refreshed"`) to list the
    finalize-hook aggregates this run refreshed
12. Navigate to `http://localhost:3255/scanner-runs`; expect the text `<TARGET_DATE>` to appear in the
    list
13. Click the `<TARGET_DATE>` row; expect the text "Immutable snapshot — as of `<TARGET_DATE>`" to appear
14. Expect the text "ENTRY QUALITY" to appear (the stored leaderboard's own column header — confirms the
    leaderboard rendered from storage, never the "No stored stock rows" empty state)

**Expected Result:**
- The backfill is accepted and actually starts executing — never accepted-then-never-run
- On completion, counts read exactly "1/1 dates", "1 calendar day · 0 already snapshotted · 0
  non-trading", and "1 snapshots"
- The persisted run record lists which aggregates its finalize hooks refreshed. Note: this iteration adds
  an immediate cache-refresh trigger at the end of this same finalize hook — so the readiness badge/
  preflight banner state should reflect this job's completion (e.g. `awaiting_snapshot` → `ready` style
  transitions, if applicable) within about one `readiness.refresh_interval_seconds` tick, not up to a
  full periodic-tick delay
- `/scanner-runs` lists `<TARGET_DATE>` and its detail page renders a populated leaderboard from storage —
  never a blank/empty state

---

### UT-J-06 — Pages load only what they need (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`,
`/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`

**Preconditions:**
- Backend running warm in prod mode (`scripts/start-backend.sh` — not `dev.sh`); frontend at
  `http://localhost:3255`; no active background job at test start

**Steps:**
1. Navigate to `http://localhost:3255/`; expect the text "Dashboard" to appear within 2.5 seconds
2. Expect the readiness badge to show `data-state="ready"` within 2 more seconds (≤4.5 s total from
   navigation start) — this iteration's `GET /api/health` now serves this from a background-refreshed
   cache rather than computing synchronously, so this budget should hold at least as well as before
3. Navigate to `http://localhost:3255/stocks`; expect the text "Stocks" to appear
4. Navigate to `http://localhost:3255/stocks/AAPL`; expect the text "AAPL" to appear within 2.5 seconds
5. Expect the chart-window caption element (`[data-testid="chart-window-caption"]`) to appear within 2
   more seconds (≤4.5 s total)
6. Navigate to `http://localhost:3255/sectors`; expect the text "Sectors" to appear
7. Navigate to `http://localhost:3255/themes`; expect the text "Themes" to appear
8. Navigate to `http://localhost:3255/data`; expect the text "Data Manager" to appear within 2.5 seconds
9. Wait 2.5 seconds (lets the page's own `AVAILABILITY_FETCH_STAGGER_MS` delay elapse)
10. Expect an availability-cell element (`[data-testid="availability-cell"]`) to appear within 2 more
    seconds
11. Navigate to `http://localhost:3255/evidence`; expect the text "Evidence" to appear
12. Navigate to `http://localhost:3255/scanner-runs`; expect the text "Scanner Runs" to appear within
    2.5 seconds
13. Expect at least one table row (`table tbody tr`) to appear within 2 more seconds (≤4.5 s total)
14. Navigate to `http://localhost:3255/backtest`; expect the text "Backtest" to appear
15. Navigate to `http://localhost:3255/watchlist`; expect the text "Watchlist" to appear
16. Navigate to `http://localhost:3255/research/regime-lab`; expect the text
    "Research — Regime Lab" to appear

**Expected Result:**
- Every page above renders its real heading/content — no blank screen, no error boundary, no
  frozen/skeleton-forever frame
- The four budget-gated endpoints (health/readiness, AAPL bars, `/data` availability, `/api/runs` via the
  scanner-runs table) each render their real value within the stated windows, proving the underlying API
  calls are fast — not merely that the page shell rendered
- No page takes more than a few seconds to become interactive

---

### UT-J-07 — Heavy aggregates never take the service down (regression — this iteration's TARGET journey)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/backtest`, `/data`

**Preconditions:**
- Backend/frontend running at `http://localhost:3255`
- Ideally checked shortly after a real ingest job so the background readiness-refresh thread (this
  iteration's own new mechanism) has ticked at least once and the panels reflect fresh state

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Expect the readiness badge element (`data-testid="readiness-badge"`) to show `data-state="ready"` and
   the text "Ready"
3. Navigate to `http://localhost:3255/backtest`
4. Expect the text "Forward-test scorecard" to appear — page renders promptly, no frozen/spinner-forever
   frame
5. Navigate to `http://localhost:3255/data`
6. Expect the background-compute panel (`data-testid="background-compute-panel"`) to render a real,
   non-fabricated state — either "No background compute running" with a last-outcome summary, or an
   in-flight window showing elapsed time and horizons done/total
7. Expect the `last-run-status` element (`data-testid="last-run-status"`) to render a genuine persisted
   status (e.g. "no new snapshots" or "ok"), never a live/fabricated value
8. Expect the `aggregates-refreshed` element (`data-testid="aggregates-refreshed"`) to list the
   categories the most recent finalize tail refreshed

**Expected Result:**
- All elements above render real, non-blank values sourced from `GET /api/health` — the exact endpoint
  this iteration changed to serve from a background-refreshed cache instead of computing
  `compute_readiness`/`compute_preflight` synchronously on the request thread. From the browser's
  perspective the response is byte-identical (same field names/types/values) to before this iteration, so
  this idle-state check should look and behave exactly as it did pre-change
- No page freeze, forever-spinner, or 5xx/blank error appears at any point during the check
- **Scope note:** this iteration's fix specifically targets `GET /api/health`'s response latency DURING a
  heavy `factor_lab_all_warm` forward-aggregate warm — a condition this idle-state browser check does not
  reproduce. The definitive quantitative proof (a 1 Hz `GET /api/health` poll for the full duration of a
  real full-deep-basis forward-aggregate warm, showing zero polls over the 2.0 s ceiling and zero
  non-answers within the poller's 5.0 s client timeout, phase-grouped by ingest window per
  `logs/backend.log`) is TC-3's dev drill (`scripts/qa/poll_health.py`) plus the browser-qa lane's own
  independent live-warm drill, recorded in `reports/perf-budgets.md` — not reproducible through this
  5-minute manual check. This case is the fast, deterministic regression proof that the browser-visible
  surfaces stay wired to real, non-frozen data after the caching change.

---

### UT-J-08 — Backtest evidence serves from storage only — never a cold recompute on request (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Backend/frontend running at `http://localhost:3255`; the forward-aggregate store has completed at
  least one warm

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Expect the text "Backtest" to appear
3. Expect the `evidence-aggregate` element (`data-testid="evidence-aggregate"`) to be visible
4. Expect the `evidence-summary` element (`data-testid="evidence-summary"`) to be visible
5. Expect the text "Snapshots contributing" to appear

**Expected Result:**
- The Backtest page loads and immediately shows the stored evidence aggregate/summary panels — no
  forever-spinner, no blank frame, no visible request-triggered recompute delay
- The text "Snapshots contributing" appears, confirming evidence is served from the stored aggregate, not
  computed live on this request

---

### UT-J-09 — The backend discloses its own background-compute activity (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`, `/data`

**Preconditions:**
- Backend/frontend running at `http://localhost:3255`

**Steps:**
1. Navigate to `http://localhost:3255/backtest`; expect the text "Time-machine" to appear
2. Click the "Previous available date" button
3. Expect the text "(historical)" to appear — the page returns immediately even while a background
   compute may be dispatched
4. Navigate to `http://localhost:3255/data`
5. Expect the `background-compute-panel` element (`data-testid="background-compute-panel"`) to be visible
6. Expect the text "process-lifetime only, never persisted" to appear inside that panel

**Expected Result:**
- Clicking "Previous available date" on `/backtest` returns immediately — no blocking/frozen UI — even
  when it triggers a background-compute window
- The `/data` background-compute panel is visible and honestly discloses its own scope with the text
  "process-lifetime only, never persisted"
- No fabricated progress percentages or estimated finish times appear anywhere in the panel

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-J-01 | Backfill honors requested range, explains zero-work | regression | P1 | `/data`, `/scanner-runs/748` |
| UT-J-03 | No per-run range cap (>370 days accepted) | regression | P1 | `/data` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | `/`, `/data` |
| UT-J-05 | Aggregates precomputed at ingest, never on the fly | regression | P1 | `/data`, `/scanner-runs` |
| UT-J-06 | Pages load only what they need (budget sweep) | regression | P1 | 11 routes |
| UT-J-07 | Heavy aggregates never take the service down (target) | regression | P1 | `/`, `/backtest`, `/data` |
| UT-J-08 | Backtest evidence serves from storage only | regression | P1 | `/backtest` |
| UT-J-09 | Backend discloses its own background-compute activity | regression | P1 | `/backtest`, `/data` |

**All P1 tests must pass for browser QA verdict to be PASS.** No NEW-surface (smoke/happy-path/validation/
error/ux) test cases were generated — this iteration touched zero UI surfaces (`Frontend Present: no`).
