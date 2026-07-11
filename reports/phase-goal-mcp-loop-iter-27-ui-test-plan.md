# Phase goal-mcp-loop-iter-27 — UI Test Plan

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-11
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context for the tester

No frontend source file changed this iteration — every route, label, and layout below is expected to look
and behave EXACTLY as it did before this iteration. What changed is backend memory hygiene, in two passes:

1. **Read-side windowing** — `regime.py`'s three `bars_asof` call sites now read a bounded trailing window
   (`bars_asof_window`/`close_on`) instead of materializing a whole multi-decade price history per
   (symbol, date). Audited and found **insufficient alone**: a live SECOND consecutive full-universe
   rebuild still crashed the backend (audit finding B1).
2. **Allocator/process hygiene** — `MALLOC_ARENA_MAX=2` (capped in `start-backend.sh`) plus a
   `gc.collect()` + `malloc_trim(0)` cleanup run after every backfill/rebuild stage
   (`data_manager._release_process_memory()`). This targets memory that accumulates ACROSS jobs in the
   same long-lived server process — exactly what pass 1 did not touch.

**This browser-driven test is the authoritative check, not a formality.** Per the dev handoff, the
isolated offline memory-measurement harness used during development peaks only ~3.0–3.8 GB and cannot
reproduce the live ~6 GB shape (the live process carries additional uvicorn/threadpool baseline overhead
the isolated script does not). **UT-02 below — driving the real job against the real live backend, TWICE
in a row — is the only test in this pipeline capable of confirming or refuting the fix**, and is this
plan's centerpiece.

**Do NOT duplicate** the API/artifact-level tests already covered in
`reports/qa/goal-mcp-loop-iter-27-test-plan.md` (memory-footprint sampling via `ulimit -v` +
`/proc/self/status`, byte-identity pytest gates). The test cases below are what a human sees in a browser.

**Operational preconditions for every test below:**
- Both services running in **prod mode** (`incredible_auto_dev/scripts/start-backend.sh` for the backend —
  never `dev.sh`, which is intentionally left uncapped/unhardened this iteration).
- **Backend cold start takes ≈130 seconds**; `GET /api/data` is a heavy endpoint (~10–30s per response,
  heavier still on a cold process). Any step below that involves a restart or an `/api/data`/`/data` load
  must allow at least that long — a shorter timeout producing a "failed to load" reading is a harness
  issue, not a product defect.
- A large, full-history, full-universe (322-date × ~541-member) price database must already be loaded (the
  standing dev-environment state) — this is what makes UT-02 the real crashing shape, not a toy dataset.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Cold-start-first: `/data` survives as the very first request after a backend restart (smoke, J-13 cold-path)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- The backend process is fully stopped (no process listening on its port).
- The operator can restart it (`bash incredible_auto_dev/scripts/start-backend.sh`) and can confirm the
  port is listening (e.g. `ss -tln`) WITHOUT making an HTTP request first — an `/api/health` warm-up call
  exercises a different code path than a cold `/data` load and would give a false "cold path OK" reading
  (iter-24 lesson).

**Steps:**
1. Start the backend fresh. Wait for the listening port to appear (up to 180 seconds) — do not make any
   HTTP request yet.
2. As the very FIRST request to the backend, navigate to `http://localhost:3255/data`.
3. Wait up to 30 seconds for the page to finish loading.
4. Observe the page.
5. Stop the backend again, wait 5 seconds, and repeat steps 1–4 a second time (repeatability check — the
   iter-24/25 mandated ×2 sequence).

**Expected Result:**
- On both cold starts, the "Data Manager" heading and its subtitle ("Grow the dataset on demand — view
  coverage and gaps, then fetch real EOD history and/or backfill immutable snapshots by date or
  range...") render — NOT a blank white page, NOT a browser network-error page.
- The "Dataset coverage" panel shows a non-blank "Universe (as of date)" value, and the "Storage
  footprint" panel shows non-blank "Database file", "Price bars", "Scanner rows", and "Forward returns"
  values.
- The "Rebuild snapshots for current universe" panel and its button are visible and enabled — no
  "Backend unavailable" error card in their place.
- No JavaScript console error mentioning "MemoryError", "500", or "Failed to fetch" appears.
- Both cold-start attempts behave identically — no flakiness between the first and second cold start.

---

### UT-02 — CENTERPIECE: Full-universe rebuild survives TWICE in a row, same session, no restart (happy-path, J-16 target)

**Type:** happy-path
**Priority:** P1 — this is the single most important test in this plan; a FAIL here is a phase-blocking
regression (unresolved critical anti-goal #8)
**Surface:** `/data`

**Preconditions:**
- Backend running (warm, or freshly cold-started per UT-01) and reachable at
  `http://localhost:3255/data`.
- No job is currently running — the "Rebuild snapshots for current universe" button is enabled and the
  "Start a fetch / backfill job" panel's submit button reads "Start", not "Job running…".
- Budget significant time: two full 322-date × ~541-member rebuilds back to back can take many minutes
  to tens of minutes each. Do not close the tab or stop the backend at any point during this test.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Click the "Rebuild snapshots for current universe" button (in the panel of the same name).
3. In the modal titled "Confirm snapshot rebuild", read the restated behavior ("This clears the entire
   snapshot set and recomputes a snapshot + forward returns for EVERY covered trading day...").
4. Click the "Rebuild snapshots" button in the modal's bottom-right (NOT "Cancel").
5. In the "Job progress" panel, confirm the status badge reads "running" (with a spinning loader icon)
   and the "Snapshots backfilled" row shows a counter formatted `{done}/{total} dates`.
6. Watch the counter every 1–2 minutes for the full run. At each check, confirm it has strictly increased,
   the progress bar above it has visibly grown, and the page is still responsive (scrolling/hovering
   works).
7. Pay particular attention to the LAST ~25% of dates (closest to the present day, deepest trailing
   history per date) — this is the stretch where the crash this iteration exists to fix actually occurred.
8. Wait for run 1 to finish: the status badge changes away from "running" to "ok", and the counter reads
   exactly `{total}/{total} dates`.
9. Confirm the page is still fully interactive (nav sidebar clickable, no error card visible anywhere).
10. **Immediately**, in the SAME browser session with the backend NOT restarted, click "Rebuild snapshots
    for current universe" again and repeat steps 3–8 for a SECOND run.
11. After run 2 also reaches "ok", open a new tab and load `http://localhost:3255/api/health` — confirm it
    responds — then load `http://localhost:3255/stocks` — confirm the leaderboard renders with populated
    rows.

**Expected Result:**
- **Run 1**: reaches `running` → `ok` with the counter climbing incrementally across many checkpoints,
  never jumping straight to the total in one poll and never regressing. The backend stays reachable the
  entire time — no connection error, no "Backend unavailable" card replacing the Job progress panel.
- **Run 2 (back-to-back, no restart)**: reaches `running` → `ok` identically. **This is the exact
  scenario that previously crashed the backend outright** — a first run barely survived while memory freed
  by it was not returned to the OS, so the second run pinned the process at the `ulimit -v` ceiling and
  crashed with `MemoryError`. A crash on run 2 specifically (page going blank, "Backend unavailable" card
  appearing mid-run, or the status badge/heartbeat freezing for more than ~2 minutes while still "running")
  is a FAIL of this test and of the phase's core objective, even if run 1 succeeded cleanly.
- After both runs, `/api/health` responds and `/stocks` renders its leaderboard — proving the whole
  backend PROCESS survived two consecutive heavy jobs, not just that each job's own request happened to
  succeed.

**If this test FAILS:** record at what `done/total` value (and on which of the two runs) the crash
occurred — this distinguishes an incomplete pass-1 fix (crashes late in run 1) from an incomplete pass-2
fix (run 1 clean, run 2 crashes) — both are critical anti-goal #8 violations regardless of which.

---

### UT-03 — Job progress reports honest, monotonically-advancing progress (validation, never "done early")

**Type:** validation
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- A rebuild job is in progress (start one per UT-02 steps 1–4, or observe one already running from UT-02).

**Steps:**
1. While the status badge reads "running", note the "Snapshots backfilled" counter and the job's current
   activity/heartbeat text at time T0.
2. Wait 30 seconds. Note the same values again at T1.
3. Repeat this observation 3 more times over the next 2 minutes.
4. Watch for the status badge changing to "ok" — confirm this happens only once the counter has climbed
   through the entire 322-date run, not within the first few seconds of confirming.

**Expected Result:**
- The counter and progress bar advance monotonically — never backward, never stuck unchanged for more
  than ~2 minutes while the badge still reads "running".
- The status badge never shows "ok" (or any completed state) while the counter still reads less than the
  total — no premature "done".
- The job's live-activity/heartbeat indicator keeps refreshing (not a frozen timestamp) for the duration
  of the observation.

---

### UT-04 — Rebuild confirm modal can be cancelled without starting a job (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Backend running; no job currently running (rebuild button enabled).

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Click "Rebuild snapshots for current universe".
3. Confirm the "Confirm snapshot rebuild" modal appears.
4. Click the "Cancel" button (to the left of "Rebuild snapshots" in the modal footer).

**Expected Result:**
- The modal closes immediately.
- The "Job progress" panel does not show a new running job — it remains in its pre-click state.
- The "Rebuild snapshots for current universe" button is enabled again, confirming no job was silently
  started.

---

### UT-05 — Rebuild and Start buttons are disabled while a job is already running (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- A job is currently running (start one per UT-02 steps 1–4).

**Steps:**
1. While the "Job progress" panel's badge reads "running", look at the "Rebuild snapshots for current
   universe" button and attempt to click it.
2. Look at the "Start a fetch / backfill job" panel's submit button.

**Expected Result:**
- The rebuild button appears visually disabled (faint text, not-allowed cursor); clicking it does not
  open the confirm modal. The text "A job is already running — wait for it to finish before rebuilding."
  is visible directly below it.
- The "Start a fetch / backfill job" submit button's label reads "Job running…" and is disabled; clicking
  it has no effect (no second job starts).
- Once the running job finishes, both controls become enabled again (rebuild button clickable, submit
  button reverts to "Start").

---

### UT-06 — Dashboard Market Regime card shows a live, correct value (regression, byte-identity re-check)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend running and reachable.

**Steps:**
1. Navigate to `http://localhost:3255/`.
2. Locate the card titled "Market Regime" (left card of the two-card AT-A-GLANCE row).
3. Note the colored regime label badge next to the title and the score beneath it, formatted
   `NN.NN / 100`.
4. Click "Why this regime — component breakdown" to expand the disclosure.
5. Read each named component's value inside.

**Expected Result:**
- The regime label badge shows a real, non-empty value — not "—", "undefined", or blank.
- The score renders as a two-decimal number followed by "/ 100" — not "NaN", not blank.
- This card's underlying computation (`regime.score_regime`) was rewritten this iteration to read a
  bounded window instead of full history — a unit test asserts byte-identical output, but this step
  confirms live rendering is unaffected: expanding the disclosure shows a non-empty, fully-populated list
  of named components, no blank/undefined rows.
- A link "See evidence proven in this regime →" is visible below the breakdown and, when clicked,
  navigates to `http://localhost:3255/evidence` — the regime-scoped evidence discoverability path (J-04).
- The adjacent "Market Phase & Severity" card also renders normally with no error state.

---

### UT-07 — Stocks leaderboard: every row shows an evidence badge (regression, J-01)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Backend running with at least one populated snapshot/leaderboard date.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`.
2. Wait for the heading "Stocks" and subtitle "Stock Leaderboard — ranked by Leadership, with independent
   Entry Quality and Risk (danger) scores, a setup status and a reason" to render.
3. Examine the first 5 rows of the leaderboard table and locate each row's evidence-status badge next to
   its score.

**Expected Result:**
- The leaderboard renders with at least 3 populated rows — not an empty state, not a "Backend
  unavailable" error card.
- Every one of the first 5 rows shows a badge reading exactly "Not yet proven" (the current honest state
  of the evidence ledger — the plan confirms both evidence ledgers remain byte-identical all-FAIL this
  iteration, so no row should show "Proven" today). No row is missing a badge.

---

### UT-08 — Unproven score is clearly marked, never shown as a confident number (regression, J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` leaderboard populated (per UT-07).

**Steps:**
1. Navigate to `http://localhost:3255/stocks`.
2. Pick any row's evidence badge (expect "Not yet proven" per UT-07).
3. Hover it and read its tooltip; note whether it is a clickable link.

**Expected Result:**
- The badge is styled in a muted/faint color token, visually distinct from the accent-colored, shield-check
  "Proven" style — never styled to look like a confident/positive result.
- The badge is NOT a clickable link when unproven (no navigable `href`) — the UI does not imply backing
  evidence exists to click through to.
- The tooltip reads to the effect of "Not yet proven — no certified out-of-sample evidence backs this
  signal yet". The raw score number beside the badge remains fully visible (the badge rides alongside the
  score, never replacing it).

---

### UT-09 — Evidence ledger page renders the honest empty state (regression, J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Backend running and reachable.

**Steps:**
1. Click "Evidence" in the left sidebar (shield-check icon, between "Research" and "Watchlist").
2. Wait for the page to load and read the heading and body content.

**Expected Result:**
- URL becomes `http://localhost:3255/evidence`. Heading "Evidence" is visible with subtitle text
  beginning "The certified-claims ledger — the single source of proven-ness...".
- Because both evidence ledgers remain byte-identical all-FAIL this iteration (no new evidence work was
  in scope), the page shows the empty-state card headed "No certified claims yet", with body text
  containing "every signal currently reads Not yet proven" — NOT a "Backend unavailable" card, NOT a
  blank page.
- The empty-state card lists the five fields a certified claim will show: "Hypothesis", "Out-of-sample
  verdict", "Control comparison (vs SPY)", "Registration date", "Forward-walk score-to-date".
- A "Stocks leaderboard" link is visible in the empty-state body and navigates to `/stocks` when clicked.

---

### UT-10 — Stock detail page: full-history toggle shows deep history without fabrication (regression, J-10)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:**
- Backend running; AAPL has deep historical price data seeded.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`.
2. Wait for the detail heading and subtitle "Stock detail — the three explainable scores (identical to
   the leaderboard; single source of truth)" to render.
3. Locate the chart's range toggle and click the option labeled "Full history".
4. Observe the price chart.

**Expected Result:**
- The chart re-renders to span AAPL's real historical range (extending back toward its actual IPO era),
  not truncated to a recent window.
- The chart line shows no discontinuous vertical jump or gap suggesting fabricated/missing data.
- The three score cards ("Leadership", "Entry Quality", risk) remain populated with numeric values,
  unaffected by the chart toggle.

---

### UT-11 — Dynamic-universe membership timeline shows honest entries/exits, no fabrication (regression, J-12)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend running; `/data` loaded successfully with membership data.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Scroll to the panel titled "Dynamic-universe membership timeline".
3. Read the step-function chart of universe size across snapshot dates and the plain-language labels
   describing which names entered/exited on which date.

**Expected Result:**
- The chart renders a step function (not a flat or broken line) showing the scored universe size changing
  over the snapshot date range.
- The panel's labels honestly attribute entries/exits to specific dates (e.g. a mid-history IPO name
  entering only from its real listing date onward) — carried verbatim from the backend, not silently
  smoothed or fabricated.
- No console error; the panel is not replaced by a "Backend unavailable" card.

---

### UT-12 — Core pages meet their performance budgets (regression, J-15)

**Type:** regression
**Priority:** P2 — important but does not block a PASS verdict by itself; `reports/perf-budgets.md` is the
source of truth this test cross-checks, not this plan
**Surface:** `/stocks`, `/stocks/AAPL`, `/data`, `/evidence`

**Preconditions:**
- Warm backend (already up for a while, not a cold start), started via `start-backend.sh`.

**Steps:**
1. Load `http://localhost:3255/stocks` once (uncounted warm-up), then reload and time from navigation to
   the leaderboard fully replacing any loading skeleton.
2. Repeat for `http://localhost:3255/stocks/AAPL`.
3. Repeat for `http://localhost:3255/data`.
4. Repeat for `http://localhost:3255/evidence`.

**Expected Result:**
- Each page becomes interactive within the committed warm budget in `reports/perf-budgets.md` (the
  memory-hardening change — bounded windowing + allocator cap + GC/trim — should not have slowed
  anything, but must be re-measured, not assumed).
- No page hangs on a loading skeleton indefinitely past its budget without an honest "still loading"
  indicator.

---

### UT-13 — Backend-down degrades to ONE contained "Backend unavailable" card, not a blank crash (error, anti-goal #8 boundary)

**Type:** error
**Priority:** P1
**Surface:** `/stocks`, `/evidence`

**Preconditions:**
- Frontend running and was previously showing data with a healthy backend.
- Operator can stop the backend cleanly.

**Steps:**
1. With `http://localhost:3255/stocks` already loaded and showing data, stop the backend process.
2. Wait 5 seconds for in-flight connections to fully close.
3. Refresh `/stocks` (F5).
4. Observe the result.
5. Navigate to `http://localhost:3255/evidence` (backend still stopped).
6. Observe the result.
7. Confirm the left sidebar (Dashboard, Stocks, ..., Data Manager) remains visible and clickable in both
   step 4 and step 6.

**Expected Result:**
- On `/stocks` (step 4): exactly ONE contained red-bordered card reading "Backend unavailable" with body
  "The Stock Leaderboard could not load from the API. No rankings are shown rather than fabricated values.
  Confirm the backend is running and retry." — not a blank page, not a browser crash/stack-trace page.
- On `/evidence` (step 6): exactly ONE contained card reading "Backend unavailable" with body "The
  certified-claims ledger could not load from the API. Nothing is fabricated — every signal continues to
  read "Not yet proven." Confirm the backend is running and reload." — same contained pattern.
- In both cases the left sidebar remains fully visible and every nav link stays clickable (the error is
  contained to the page content area, not a full-page takeover).
- No fabricated data (stale numbers, placeholder rows) is shown anywhere while the backend is down.

---

### UT-14 — Backend recovery: page recovers after the backend restarts (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Continuing from UT-13 with the backend still stopped and the "Backend unavailable" card showing on
  `/stocks`.

**Steps:**
1. Restart the backend (`bash incredible_auto_dev/scripts/start-backend.sh`). Wait up to 180 seconds.
2. Without manually refreshing, wait up to 30 seconds and observe whether `/stocks` recovers on its own,
   or manually refresh (F5) if the page has no auto-poll.

**Expected Result:**
- Once the backend is healthy again, `/stocks` shows the populated leaderboard again — either
  automatically or after a single manual refresh, matching the page's actual retry behavior.
- No leftover stale error card persists alongside the recovered data.

---

### UT-15 — Data Manager remains discoverable within 2 clicks; panel labels unchanged (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Preconditions:**
- Frontend running; start from the Dashboard.

**Steps:**
1. Navigate to `http://localhost:3255/`.
2. Look at the left sidebar navigation.
3. Click "Data Manager" (database icon, last item in the sidebar list).

**Expected Result:**
- "Data Manager" is visible in the sidebar alongside the same other nav entries as before this iteration
  (Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Evidence, Watchlist, Methodology,
  Data Manager) — no new/removed/renamed entry, since this iteration added no navigation.
- Clicking it navigates to `http://localhost:3255/data` in exactly one click from the Dashboard.
- The panel titles on the resulting page ("Dataset coverage", "Storage footprint", "Rebuild snapshots for
  current universe", "Dynamic-universe membership timeline", "Start a fetch / backfill job", "Job
  progress") read identically to the pre-iteration UI — no panel added, removed, or relabeled.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cold-start-first `/data` survives, ×2 (J-13 cold-path) | smoke | P1 | `/data` |
| UT-02 | Full-universe rebuild survives TWICE in a row (CENTERPIECE, J-16) | happy-path | P1 | `/data` |
| UT-03 | Job progress honest, monotonic, never "done early" | validation | P1 | `/data` |
| UT-04 | Rebuild confirm modal can be cancelled | validation | P2 | `/data` |
| UT-05 | Rebuild/Start buttons disabled while a job runs | validation | P2 | `/data` |
| UT-06 | Dashboard Market Regime card correct + evidence link (J-04) | regression | P1 | `/` |
| UT-07 | Leaderboard rows show evidence badges (J-01) | regression | P1 | `/stocks` |
| UT-08 | Unproven score clearly marked (J-03) | regression | P1 | `/stocks` |
| UT-09 | Evidence ledger honest empty state (J-05) | regression | P1 | `/evidence` |
| UT-10 | Full-history toggle shows deep history (J-10) | regression | P1 | `/stocks/AAPL` |
| UT-11 | Membership timeline honest entries/exits (J-12) | regression | P1 | `/data` |
| UT-12 | Core pages meet perf budgets (J-15) | regression | P2 | `/stocks`, `/stocks/AAPL`, `/data`, `/evidence` |
| UT-13 | Backend-down: one contained card (anti-goal #8) | error | P1 | `/stocks`, `/evidence` |
| UT-14 | Backend recovery after restart | regression | P2 | `/stocks` |
| UT-15 | Data Manager discoverable, labels unchanged | ux | P3 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02 is the centerpiece — a FAIL there
(backend crash on either the first or, critically, the SECOND consecutive rebuild) is a hard FAIL of the
phase regardless of any other test's result, since it is the exact regression this iteration exists to
fix. UT-01 is the mandatory iter-24/25 cold-start-first boundary check. UT-06 through UT-12 are the
browser-observable proof that all 8 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-12,
J-13, J-15) are live PASS, closing the iter-26 skipped-behind-the-outage gap.

**Not covered here (see functional test plan `reports/qa/goal-mcp-loop-iter-27-test-plan.md`):** memory
sampling (`VmPeak`/`VmSize`/`VmRSS` under `ulimit -v`) and pytest byte-identity harnesses
(`test_scoring_window.py`, `test_forward_testing.py`, `test_bar_cache.py`) — those are non-UI
verifications and are intentionally not duplicated in this UI test plan.
