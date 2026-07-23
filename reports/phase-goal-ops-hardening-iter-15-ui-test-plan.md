# Phase goal-ops-hardening-iter-15 — UI Test Plan

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope note

This iteration touches **zero** files under `apps/frontend/` (`Frontend Present: no`, confirmed by
`reports/phase-goal-ops-hardening-iter-15-user-visible-changes.md` and the ui-surface-map's own `git
status` read). The entire fix is a single-flight de-duplication guard added to
`forward_aggregates_cached`'s cache-miss path (`apps/backend/app/engine/forward_testing.py`) — the sole
change with any user-facing trace is `/backtest`'s response time when a request lands concurrently with
someone else's not-yet-finished computation for the SAME horizon/date. `compute_forward_aggregates`
itself, `GET /api/backtest`'s handler, and every page's rendering code are all byte-unchanged.

Per this dispatch's PUMP NOTE, this iteration's browser lane is deliberately **lean**: the load-bearing
case is the required-still-passing set (J-01, J-03, J-04, J-05), plus an optional `/backtest` smoke check
against the currently-**warm** cache. The following are explicitly excluded from this browser test plan,
with reasons — these are intentional omissions, not oversights:

| Excluded scenario | Why it is excluded here | Where it IS proven instead |
|---|---|---|
| Forcing a genuinely cold, first-ever `/backtest` cache-MISS | A real cold MISS takes on the order of minutes on the full deep basis (measured at 178.7s this iteration) — inducing one just to watch it in a browser wastes the exact multi-minute window this dispatch's PUMP NOTE says not to spend on it | `reports/qa/goal-ops-hardening-iter-15-test-plan.md` TC-04 (operator-supervised, ONE authorized AG-10-class pass); `reports/perf-budgets.md` |
| Concurrent-load or memory-pressure tests against the live process | This session's host has hard-reset twice (2026-07-20, 2026-07-21) under exactly this shape of concurrent load; the PUMP NOTE explicitly rules this out for the browser lane | Functional test plan TC-01/TC-02 (controlled, throwaway-fixture API tests) + TC-04 (the one live operator-supervised pass) |
| TC-8's in-flight-failure/no-deadlock proof | Requires injecting an artificial exception into a live in-flight computation — only reachable via a pytest monkeypatch, not from a browser without unsafe production manipulation | Functional test plan TC-08 |
| Re-spot-checking `/stocks`, `/sectors`, `/scanner-runs`, `/evidence` under the concurrent warm | These are the ui-surface-map's "Additional Pages Spot-Checked" row — none had a code change this iteration, and re-loading them under a live concurrent warm is the same excluded live-load condition above | ui-surface-map's own "Additional Pages Spot-Checked" table; functional test plan TC-05 (same authorized pass as TC-04) |

**Types not used this iteration, with rationale:**
- **Validation** — no form was added or changed; the `/data` backfill form is byte-unchanged.
- **Happy-path** — this iteration adds no new user-facing capability (confirmed by the phase spec: "New
  user-facing capability: None new"). The fix's OWN behavior change (de-dup on a concurrent cache-MISS)
  is only observable under the concurrent-MISS-during-a-live-warm condition excluded above; a
  browser-only "happy path" here would either be indistinguishable from the plain warm-cache smoke/
  regression checks below (which exercise the unchanged cache-HIT path, not the new de-dup code at all)
  or would require reproducing the excluded trigger. Neither is an honest "happy path" claim for this
  iteration's actual mechanism.
- **Error** — see the TC-8 exclusion above; the fix's own failure path is backend/pytest-only.

This plan also deliberately does **not** restate `reports/qa/goal-ops-hardening-iter-15-test-plan.md`'s
API-level tests (TC-01 through TC-06, TC-08) — only that plan's browser-facing item (TC-07, the four
required-still-passing journeys) is elaborated into human/agent-executable steps below.

**Do not restart the backend to satisfy any precondition below.** Per the PUMP NOTE, the backend's
forward-aggregate cache is currently warm; a restart would cold-evict it and turn an intended warm-cache
smoke check into the excluded cold-MISS scenario above. If the frontend needs (re)starting, use
`bash scripts/start-frontend.sh` only.

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — `/backtest` loads successfully against the warm cache (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255`
- Backend's forward-aggregate cache is currently warm (services were left up per this dispatch's PUMP
  NOTE) — do not restart either service to reach this precondition
- No login required (no auth in this product)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the page to fully load (network idle)
3. In DevTools Console, evaluate: `document.querySelector('[data-testid="evidence-aggregate"]') !== null`

**Expected Result:**
- Page renders — no blank screen, no Next.js error overlay, no "Application error" text
- The red "Backend unavailable" card (text starting "The backtest scorecard could not load from the
  API...") is NOT present anywhere on the page
- Step 3's evaluation returns `true` — the forward-tested evidence aggregate section at the bottom of the
  page is present, not stuck on the gray pulsing skeleton
- The `data-testid="backtest-asof"` badge shows real text starting "Viewing as-of" (not blank)
- The "Forward-test scorecard" table shows 5 horizon rows labeled `1d`, `5d`, `10d`, `20d`, `60d` (the
  page's own subtitle names this exact set: "...next 1/5/10/20/60 trading days..."), each row populated
  with figures or the honest "—" (NA) placeholder — never an entirely blank row
- Because the cache is warm, the whole page resolves within a few seconds — it does not sit on the gray
  pulsing skeleton (`BacktestSkeleton`, 3 small cards + 1 large card) for more than roughly 10 seconds
- Browser DevTools Console shows no red error entries

**What "broken" looks like:** the red "Backend unavailable" card appears, `evidence-aggregate` never
appears within a reasonable wait, or the page hangs on the skeleton for a suspiciously long time despite
the cache being warm (if so, do not silently wait it out — that would mean the cache was not actually
warm, or the fix regressed the warm/cache-HIT path itself; note it rather than assuming it will resolve).

---

### UT-02 — Two simultaneous tabs on the same warm `/backtest` date show identical numbers (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`

**Note:** this is an ordinary-usage multi-tab check on the **warm/cache-HIT** path (two humans casually
opening the same page at once) — it is explicitly NOT an attempt to reproduce this iteration's own
concurrent-cache-MISS de-dup mechanism (excluded above per the PUMP NOTE). Its purpose is to catch a
different, real regression class: a bug in the new lock/in-flight-dictionary code that corrupts or
staggers even the unrelated, previously-fine cache-HIT path.

**Preconditions:**
- UT-01 has passed (cache confirmed warm, page confirmed loading fast)
- Both tabs will use the SAME as-of date shown in UT-01's `backtest-asof` badge — call it DATE_W — since
  the global as-of switcher (not a per-tab control) determines which date a tab shows

**Steps:**
1. In your current tab, confirm you are still on `http://localhost:3255/backtest` showing DATE_W (do not
   change the as-of switcher)
2. Open a second, separate browser tab and navigate to `http://localhost:3255/backtest`
3. In the second tab's DevTools Console, evaluate:
   `document.querySelector('[data-testid="backtest-asof"]').textContent`
4. In the second tab's DevTools Console, evaluate:
   `Array.from(document.querySelectorAll("table tbody tr")).map(r => r.textContent)`
5. Return to the first tab and evaluate the identical expression from Step 4

**Expected Result:**
- Both tabs' `backtest-asof` text names the SAME date (DATE_W)
- Both tabs resolve to the full evidence panel within a few seconds — neither tab visibly hangs on the
  gray pulsing skeleton longer than the first tab did in UT-01, and neither shows the red "Backend
  unavailable" card
- The two tabs' captured row-text arrays from Steps 4/5 are character-for-character **identical** — same
  horizons, same figures, same order

**What "broken" looks like:** the two tabs show different figures for the same horizon/date, or one tab
takes dramatically longer than the other (suggesting the new code silently forced a redundant recompute
or a lock stall on what should be a plain cache-HIT read).

---

### UT-03 — J-01: Backfill honors the requested range and explains zero-work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs`
**Maps to:** functional test plan TC-07 (J-01 slice); the automated replay's own `UT-J-01`

**Preconditions:**
- J-01 is currently `passing` per `docs/goal.md` — the required-still-passing set named in this phase's
  TESTING REQUIREMENTS
- This iteration's diff touches none of J-01's own surfaces or backend code paths — this test exists
  purely to confirm no incidental regression, not to re-derive J-01 from scratch

**Steps:**
1. This journey has an existing deterministic golden script, run automatically by the browser-qa harness
   (`scripts/automation/lib/replay-lane.sh` / `demo_runner.py`) and recorded as `UT-J-01` in
   `reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md`. Confirm that report shows
   `UT-J-01 ... PASS`. If the report is missing this row or shows anything other than PASS, perform the
   manual/LLM-fallback walkthrough below (Steps 2-8).
2. Navigate to `http://localhost:3255/data`. In the "Start a fetch / backfill job" card, type
   `2026-05-02` into the "Start date" field and `2026-05-29` into the "End date" field.
3. From the "Job kind" dropdown, select "Backfill snapshots". Click the "Start" button (it switches to
   "Job running…" with a spinning icon).
4. Watch the "Job progress" panel's status badge (`data-testid="job-status"`) until it shows a terminal
   value (not "running").
5. Read the job's breakdown (`data-testid="backfill-breakdown"`). Because this exact May range has almost
   certainly already been backfilled in an earlier iteration of this session, expect the zero-work
   outcome: 0 new snapshots, with 19 already-snapshotted + 9 non-trading, partitioning all 28 calendar
   days (the same "re-run" case `docs/goal.md` itself defines as passing). If this genuinely is the first
   time this range has run, expect `dates_total` = 19 with 19 new snapshots created instead.
6. Navigate to `http://localhost:3255/scanner-runs` and confirm runs exist for in-range May dates (e.g.
   `2026-05-04`, `2026-05-15`, `2026-05-29`); click into one and confirm its leaderboard renders
   populated, non-blank values.
7. Reload `http://localhost:3255/data` and scroll to the "Run history" table; confirm a row for the
   `2026-05-02 → 2026-05-29` range is still listed with the same Status/breakdown as Step 5 — never
   absent, never reverted to "no job started this session."
8. Confirm the outcome from Step 5 (zero-work or productive) renders in a visually distinct explanatory
   presentation, not the same unqualified green success badge either way.

**Expected Result:**
- `reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md` records `UT-J-01 ... PASS`
  (primary evidence), or the manual walkthrough above completes with the outcomes in Steps 5-8
- Every calendar day in the requested range is accounted for in the breakdown (trading + non-trading =
  28; created + already-snapshotted + error-other = trading-day count)
- The run persists across reload in both `/scanner-runs` and `/data`'s Run history table

**What "broken" looks like:** the replay report shows FAIL for `UT-J-01`, the breakdown's day-counts do
not sum to the full range, or the run vanishes from history after a reload.

---

### UT-04 — J-03: No per-run range cap (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`
**Maps to:** functional test plan TC-07 (J-03 slice); the automated replay's own `UT-J-03`

**Preconditions:**
- J-03 is currently `passing`
- Same environment as UT-03

**Steps:**
1. Confirm `reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md` shows `UT-J-03 ...
   PASS` (existing deterministic golden script). If missing or not PASS, perform the manual walkthrough
   below.
2. Navigate to `http://localhost:3255/data`. In the "Start a fetch / backfill job" card, type
   `2025-06-01` into the "Start date" field and `2026-07-17` into the "End date" field (a >370-calendar-
   day span).
3. From the "Job kind" dropdown, select "Backfill snapshots". Click the "Start" button.
4. Confirm the request is accepted immediately — no "date range too large" (or similarly worded)
   rejection message appears anywhere on the page or as a toast.
5. Watch the "Job progress" panel for at least one minute; confirm its status badge shows "running" and
   its current-activity/progress detail visibly advances (e.g., the date or chunk being processed
   changes) rather than sitting static or reverting to an error state.

**Expected Result:**
- No range-too-large rejection appears at any point
- The job begins executing in visible chunks with live, advancing progress (full completion is not
  required for this check — J-03's own acceptance only requires "at least the first chunk completes...
  without any cap-related failure")

**What "broken" looks like:** any "range too large"/cap-rejection message appears, or the job immediately
fails/errors upon starting a >370-day range.

---

### UT-05 — J-04: Non-blocking boot with visible status (regression — includes OPERATOR-PERFORMED steps)

**Type:** regression
**Priority:** P1
**Surface:** (global) `HealthBadge` / `PreflightBanner`, `/data`
**Maps to:** functional test plan TC-07 (J-04 slice)

**Preconditions:**
- J-04 is currently `passing`
- **Carrying forward is the preferred path this iteration.** This iteration's diff touches none of J-04's
  own code (`app.engine.readiness`, `app/api/health.py`, the boot sequence) — per this dispatch's PUMP
  NOTE, `runs/goal-ops-hardening-iter-14/operator-session-live-walkthrough.md`-adjacent evidence
  (iter-14's own already-closed live pass of this exact journey) is an acceptable substitute for a fresh
  kill/restart this iteration. Only perform Steps 2-8 below if the operator/evaluator specifically wants
  iteration-15-dated evidence.
- **If performed, Steps 2, 5, and 7 require killing and restarting the live backend process — this
  session's agents cannot do this themselves (subagent-resume is broken this session). These steps are
  OPERATOR-PERFORMED: the operator runs them on request and reports console output, PIDs, and exact
  timestamps verbatim; never fabricate or estimate a number in their place.**

**Steps:**
1. Check `reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md` for a `UT-J-04` row.
   Per iter-14's own precedent, J-04's live-crash portion has historically been excluded from the
   fully-automated deterministic replay (that report listed only `UT-J-01`/`UT-J-03`/`UT-J-05`). If
   `UT-J-04` is absent here too, either accept iter-14's already-closed live evidence per the note above,
   or perform Steps 2-8 below (OPERATOR-PERFORMED where marked).
2. **(OPERATOR-PERFORMED)** Restart the backend via `scripts/start-backend.sh` (never `dev.sh`).
   Immediately begin polling `GET http://localhost:8255/api/health`; record the wall-clock timestamp of
   the first HTTP 200.
3. Confirm the first HTTP 200 arrived within 5 seconds of process start (the committed boot budget).
4. With the frontend open to any page, observe the top-bar `data-testid="readiness-badge"`: confirm it
   shows `data-state="initializing"` (text "Initializing… history {done}/{total}") at least once before
   settling to `data-state="ready"` ("Ready", green dot) — never jumping straight from blank to "Ready"
   with no visible initializing step.
5. **(OPERATOR-PERFORMED)** Kill the backend process (simulating a crash, not a graceful shutdown).
   Record the exact timestamp and PID killed.
6. Within the next poll cycle, confirm the readiness badge flips to `data-state="unavailable"` ("Backend
   unavailable", red dot) and `data-testid="preflight-banner"` shows `data-verdict="NO-GO"` with reason
   text "Backend is unavailable — the preflight check could not run." — visibly distinct from both the
   "Ready" and "Initializing…" presentations.
7. **(OPERATOR-PERFORMED)** Restart the backend again via `scripts/start-backend.sh`. Once ready,
   navigate to `http://localhost:3255/data` and check the "Run history" table for any job that was
   mid-flight (status "running") at the moment of the Step 5 kill.
8. Confirm the backend logfile (`logs/backend.log`) contains boot-sequence entries for both the Step 2
   and Step 7 starts, and that the log segment ending at the Step 5 kill stops abruptly with no
   clean-shutdown entry.

**Expected Result:**
- Steps 2-4: first HTTP 200 ≤5s from process start; the badge visibly passes through "Initializing…"
  before "Ready"
- Steps 5-6: the badge and the preflight banner both flip to their honest unreachable/NO-GO presentation
  immediately upon the kill — never a frozen "Ready" state and never a blank/crashed page
- Step 7: any job mid-flight at the kill shows an "interrupted" status (a muted/neutral badge, distinct
  from both "ok" and "failed"), not a still-"running" row with no living process behind it
- Step 8: the log shows entries for both starts and an abrupt (non-clean) end at the kill point

**What "broken" looks like:** the badge stays "Ready" or blank after the kill (masking a real outage), the
preflight banner does not show NO-GO, a phantom "running" job row survives the restart with no way to
tell it is dead, or boot-to-first-200 exceeds 5 seconds on the warm DB.

---

### UT-06 — J-05: Aggregates are precomputed at ingest, never on the fly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/scanner-runs`, Market Regime card (home `/` and `/backtest`'s As-of scan summary)
**Maps to:** functional test plan TC-07 (J-05 slice); the automated replay's own `UT-J-05`

**Preconditions:**
- J-05 is currently `passing`
- Same environment as UT-03

**Steps:**
1. Confirm `reports/phase-goal-ops-hardening-iter-15-regression-replay-results.md` shows `UT-J-05 ...
   PASS` (existing deterministic golden script). If missing or not PASS, perform the manual walkthrough
   below.
2. On `http://localhost:3255/data`, scroll to the "Rebuild snapshots for current universe" card and read
   its status text ending "...in the latest snapshot (YYYY-MM-DD)". Use the next calendar trading day
   after that date as your target (call it DATE_Y). In the "Start a fetch / backfill job" card, type
   DATE_Y into both "Start date" and "End date", select "Backfill snapshots", and click "Start".
3. Once the job reaches a terminal status, navigate to `http://localhost:3255/scanner-runs` and confirm
   DATE_Y's leaderboard renders immediately (no separate "computing" wait) with stored, populated values.
4. Navigate to `http://localhost:3255` (or `/backtest`, viewing DATE_Y) and confirm the "Market Regime"
   card shows a populated score/label, not a loading or error state.
5. While the Step 2 job (or any heavier ingest job) runs, confirm `data-testid="readiness-badge"` stays at
   `data-state="ready"` throughout — never "unavailable."

**Expected Result:**
- The replay report shows `UT-J-05 ... PASS`, or the manual walkthrough completes with every page in
  Steps 3-4 rendering DATE_Y's data immediately from storage — no visible "computing" delay distinct from
  any other already-cached date's ordinary load time
- The readiness badge never drops to "unavailable" while the ingest job runs

**What "broken" looks like:** `/scanner-runs` or the Market Regime card shows a multi-second-plus
"computing" delay specifically for the newly-ingested date (versus older, already-cached dates loading
instantly), or the readiness badge drops to "unavailable" while the ingest job runs.

---

### UT-07 — Nothing new to discover: the product looks and navigates exactly as before (ux)

**Type:** ux
**Priority:** P3
**Surface:** global navigation, `/backtest`

**Preconditions:**
- Frontend running at `http://localhost:3255`

**Steps:**
1. Navigate to `http://localhost:3255` and look at the full navigation sidebar/header.
2. Compare the visible list of nav entries against the previous iteration's own record of the same list
   (`reports/phase-goal-ops-hardening-iter-14-what-to-click.md`, or your own familiarity with the app):
   `/`, `/stocks`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`,
   `/watchlist`, one `/research` lab, `/methodology`.
3. Navigate to `http://localhost:3255/backtest` and visually compare the page's section order against
   iter-14's own documented structure: "As-of scan summary" → "Forward-test scorecard" → Return
   Attribution → "Leadership cohorts" → the forward-tested evidence aggregate section at the bottom.

**Expected Result:**
- No new nav entry, page, button, or label appears anywhere that wasn't present before this iteration
- `/backtest`'s section order and headings match iter-14's documented structure exactly — confirming the
  fix's entire footprint is invisible, exactly as this iteration's own user-visible-changes report claims
  ("What Changed in the Visible UI: None")

**What "broken" looks like:** any new nav item, page, card, badge, or label appears. Since this phase
spec explicitly commits to zero UI surface changes, any visible addition is itself an unplanned scope
signal worth flagging to the evaluator, not just a test failure.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/backtest` loads against the warm cache | smoke | P1 | `/backtest` |
| UT-02 | Multi-tab warm-cache consistency | regression | P2 | `/backtest` |
| UT-03 | J-01 backfill range + zero-work honesty | regression | P1 | `/data`, `/scanner-runs` |
| UT-04 | J-03 no per-run range cap | regression | P1 | `/data` |
| UT-05 | J-04 non-blocking boot + crash/restart | regression | P1 | (global) badge/banner, `/data` |
| UT-06 | J-05 aggregates precomputed at ingest | regression | P1 | `/data`, `/scanner-runs` |
| UT-07 | No new UI surface introduced | ux | P3 | global nav, `/backtest` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-01 is this iteration's own minimal
availability proof (the fix's warm-cache path still works). UT-03/UT-04/UT-05/UT-06 protect the four
Required-still-passing journeys named in this phase's TESTING REQUIREMENTS — none of them may regress
from passing to failing. UT-02 and UT-07 are supplementary sanity nets this iteration's designer added
(not independently required by the phase spec) and are scoped P2/P3 accordingly.
