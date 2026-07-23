# Phase goal-ops-hardening-iter-14 — UI Test Plan

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Scope note

This iteration touches zero files under `apps/frontend/` (`Frontend Present: no`, confirmed by the
dev handoff's own `git status`). Its entire purpose is a backend availability/resilience fix — a
bounded, streamed rewrite of `compute_forward_aggregates` closing the defect that caused iter-7's and
iter-13's full-backend outages. There is no new page, button, form, or navigation target. Test cases
below are drawn from `reports/phase-goal-ops-hardening-iter-14-ui-surface-map.md`'s 3 affected
surfaces (5 rows: the global readiness badge, `/backtest`'s evidence panel, and `/data`'s three
"Refreshed: ..." render sites), plus the two Required-still-passing regression items named in the
phase spec's TESTING REQUIREMENTS (J-01/J-03/J-04/J-05, and the badge-never-freezes assertion during
their own backfills). These UI cases do not repeat the backend/API-level tests already covered in
`reports/qa/goal-ops-hardening-iter-14-test-plan.md` (TC-01 through TC-08, TC-11) — only the two
browser-facing rows there (TC-9, TC-10) are elaborated into human/agent-executable steps here.

**Types not used this iteration:** Validation. No form was added or changed (the "Start a fetch /
backfill job" form on `/data` is byte-unchanged) so there is nothing new to validate; its pre-existing
date-format validation is out of this iteration's scope to re-test.

**A design constraint carried from this dispatch's operator note, stated explicitly so it is not
mistaken for an oversight:** none of the tests below induce concurrent load or artificial memory
pressure against the live frontend-facing backend process. Concurrent-caller safety (N≥4 callers) is
already proven at the controlled, API-level layer (functional-plan TC-4, against a throwaway fixture
DB) — deliberately NOT repeated here against the live full-deep-basis process, because that exact
shape of load (concurrent backfills) is what produced this session's two hardware resets
(2026-07-20/21) and iter-13's 12-minute wedge. Every test below drives at most ONE real backfill job
at a time.

**Operational context relevant to every test below:** per `docs/handoffs/goal-ops-hardening-iter-14-dev.md`,
the backend (PID 3669411 at time of writing) was deliberately left running after this iteration's own
TC-5/TC-6/TC-7 measurement pass specifically so this browser lane would not need a cold restart —
confirm it is still up before starting rather than restarting it. If the frontend needs (re)starting,
use `bash scripts/start-frontend.sh` **only** — the combined `bash scripts/dev.sh` kills and restarts
**both** ports and would discard that already-running, already-warmed backend process.

---

## Shared setup: determining DATE_X (used by UT-03 onward)

Every test below that triggers a real backfill needs one single calendar date that currently has no
snapshot yet. Determine it once, reuse it for the whole pass:

1. Navigate to `http://localhost:3255/data`.
2. Scroll to the card titled "Rebuild snapshots for current universe" (`data-testid="rebuild-panel"`).
3. Read its status paragraph — either `data-testid="coverage-absent-banner"` (if some universe members
   are absent) or `data-testid="coverage-absent-none"` (if all are present). Both end with the phrase
   "...in the latest snapshot (YYYY-MM-DD)."
4. **DATE_X** = the calendar day immediately after that date. If that lands on a Saturday or Sunday,
   use the following Monday instead. (Example only, not a literal instruction: if the panel reads
   "...in the latest snapshot (2026-07-21)", DATE_X = `2026-07-22`.)

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Data Manager (`/data`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255` (see "Operational
  context" above — do not restart the backend to satisfy this precondition)
- No login required (no auth in this product)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load (network idle)

**Expected Result:**
- Page renders — no blank screen, no Next.js error overlay, no "Application error" text
- A card titled "Start a fetch / backfill job" is visible
- A card titled "Rebuild snapshots for current universe" is visible further down
- The top-bar readiness badge (`data-testid="readiness-badge"`) shows `data-state="ready"` (green dot,
  text "Ready") — if it instead shows `data-state="initializing"`, wait for it to settle to "ready"
  before treating this precondition as met (this iteration's fix targets load-triggered freezing, not
  the unrelated one-time startup warm-up)
- Browser DevTools Console shows no red error entries

---

### UT-02 — Backtest (`/backtest`) loads with its existing evidence panel, no error card (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Same as UT-01
- No backfill job is currently running (baseline, pre-warm read)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the page to fully load

**Expected Result:**
- Page renders — no blank screen, no Next.js error overlay
- In DevTools Console, `document.querySelector('[data-testid="evidence-aggregate"]') !== null`
  evaluates to `true` — the by-horizon evidence panel is present, not stuck on the loading skeleton
- The red "Backend unavailable" card (text starting "The backtest scorecard could not load from the
  API...") is NOT present
- The `data-testid="backtest-asof"` badge shows a real date (e.g. "Viewing as-of ... (latest)"), not
  blank
- Browser DevTools Console shows no red error entries

---

### UT-03 — Readiness badge stays honest (never frozen or unavailable) throughout a real backfill-triggered forward-aggregate warm (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** (global) `HealthBadge`, `data-testid="readiness-badge"` — present on every page

**Maps to:** functional test plan TC-9 (this is the standalone, single-trigger repro of TC-9's core
assertion)

**Preconditions:**
- UT-01 passing (badge already `data-state="ready"` before this test begins)
- DATE_X determined per "Shared setup" above

**Steps:**
1. On `http://localhost:3255/data`, in the "Start a fetch / backfill job" card, click into the "Start
   date" field (`data-testid="job-start-date"`) and type DATE_X (format `yyyy-MM-dd`)
2. Click into the "End date" field (`data-testid="job-end-date"`) and type DATE_X again (same single
   day — a one-day range)
3. In the "Job kind" dropdown (aria-label "Job kind"), select "Backfill snapshots"
4. Click the "Start" button (it reads "Job running…" with a spinning icon once clicked, confirming the
   job started)
5. Starting immediately and every 20 seconds thereafter, open DevTools Console and evaluate:
   `document.querySelector('[data-testid="readiness-badge"]').getAttribute('data-state')` — record
   each result with its wall-clock timestamp
6. At the same cadence, also evaluate:
   `document.querySelector('[data-testid="job-status"]').textContent` — keep polling both while this
   reads "running"
7. Stop once `job-status` shows any value other than "running." Continue for up to 8 minutes total
   before treating a still-"running" job as a stall worth flagging on its own.

**Expected Result:**
- Every recorded `data-state` reading throughout the job is `"ready"` — never `"loading"` and never
  `"unavailable"` at any single poll
- The visible badge (top bar) reads "Ready" with a green dot at every poll; it is never observed
  showing "Checking backend…" nor the red "Backend unavailable" pill
- The job's terminal `job-status` text reads `"ok"` (if it instead reads "no new snapshots", DATE_X had
  no real work to do — advance DATE_X by one calendar day and restart from Step 1)
- Total elapsed time from the "Start" click to the terminal status is recorded (expected in the
  ~4-6 minute range per this dispatch's own operator note for a single-date warm against the full
  basis)

**What "broken" looks like:** any single poll shows `data-state="loading"` held across two or more
consecutive 20-second polls, `data-state="unavailable"` at any poll, or the page/DevTools Console
itself becomes entirely unresponsive — this last one is the historical failure mode (a ~12-minute wedge
in iter-13).

---

### UT-04 — `/backtest` stays usable (renders the full evidence panel, never hangs or errors) during the same real warm (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest`

**Maps to:** functional test plan TC-9

**Preconditions:**
- The DATE_X job from UT-03 has been started (its Step 4) and is either still "running" or has just
  reached "ok" — this test can run during or immediately after that same job; it needs no separate
  trigger.
- Performed in a SECOND browser tab so the first tab keeps polling UT-03's readiness badge / job
  status uninterrupted.

**Steps:**
1. Open a new browser tab
2. Navigate to `http://localhost:3255/backtest`
3. In DevTools Console, evaluate:
   `document.querySelector('[data-testid="evidence-aggregate"]') !== null`
4. If it returns `false`, wait 15 seconds and re-evaluate, repeating for up to 2 minutes
5. Once it returns `true`, visually confirm the by-horizon scorecard table and the return-attribution
   leadership lists show populated numbers/labels (not blank cells)

**Expected Result:**
- The page resolves to the full evidence panel (`evidence-aggregate` present) within at most 2 minutes
  of the tab opening — it does not hang indefinitely on the pulsing gray skeleton (3 small cards + 1
  large card, class `animate-pulse`)
- The red "Backend unavailable" card never appears at any point during this check
- The `data-testid="backtest-asof"` badge shows a real (non-blank) date throughout

**What "broken" looks like:** the red "Backend unavailable" card appears at any point, or the skeleton
never resolves within the 2-minute window while UT-03's job is confirmed still "running" or already
"ok."

---

### UT-05 — Live "Job progress" panel's "Refreshed: ..." line includes "forward aggregates" once the backfill completes (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/data` — live Job progress panel

**Preconditions:**
- The DATE_X job from UT-03 has reached a terminal `job-status` of `"ok"` (not "no new snapshots")

**Steps:**
1. Return to the original tab (still on `http://localhost:3255/data` from UT-03), or reload
   `http://localhost:3255/data` in that same browser session (the "Job progress" panel keeps showing
   the last job started this session either way)
2. In DevTools Console, evaluate:
   `document.querySelector('[data-testid="aggregates-refreshed"]').textContent`
3. Also evaluate `document.querySelector('[data-testid="backfill-breakdown"]').textContent` to confirm
   the snapshot was genuinely new

**Expected Result:**
- The `aggregates-refreshed` text begins with "Refreshed: " and its comma-separated list includes the
  item "forward aggregates" (rendered from the backend's `forward_aggregates` value, underscores
  converted to spaces — no raw underscore or camelCase visible)
- The `backfill-breakdown` text reads "1 calendar day · 0 already snapshotted · 0 non-trading"
  (confirming DATE_X was a genuinely new, not-already-snapshotted trading day)

**What "broken" looks like:** the `aggregates-refreshed` element is not found (`null`) despite
`job-status` reading "ok", or its text omits "forward aggregates" even though `backfill-breakdown`
confirms a new snapshot was created (i.e., NOT "1 already snapshotted").

---

### UT-06 — Persisted "Last run summary" card (fresh tab, no job started this session) still shows "forward aggregates" for the same completed run (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — persisted summary card (fresh-reload path)

**Preconditions:**
- UT-05 has confirmed the DATE_X job's live view shows "forward aggregates"

**Steps:**
1. Open a brand-new browser tab (so no job has been started in this tab's session) — do not reuse any
   tab from UT-03/UT-04/UT-05
2. Navigate to `http://localhost:3255/data`
3. Locate the "Job progress" panel — since no job started in this new session, it renders the
   persisted-run (`LastRunSummary`) view instead of a live job card
4. In DevTools Console, evaluate `document.querySelector('[data-testid="last-run-status"]')?.textContent`
   and cross-check the panel's hint text (job kind · date range · "from a previous session") to confirm
   this is the DATE_X job, not some other run
5. Evaluate `document.querySelector('[data-testid="aggregates-refreshed"]')?.textContent`

**Expected Result:**
- The panel shows the persisted-run view for the DATE_X job (hint text ends "from a previous session",
  date range reads DATE_X → DATE_X)
- Its "Refreshed: ..." line includes "forward aggregates" — the same value UT-05 saw on the live view,
  now read from a different render site

**What "broken" looks like:** the persisted card shows a different run than the DATE_X job (re-verify
by date/timestamp if another run completed in the meantime), or it correctly identifies the DATE_X job
but its "Refreshed: ..." line omits "forward aggregates."

---

### UT-07 — Run History table row for the same job includes "forward aggregates" in its breakdown cell (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — Run history table

**Preconditions:**
- Same as UT-06

**Steps:**
1. On `http://localhost:3255/data` (either tab), scroll to the "Run history" table at the bottom of the
   page
2. Locate the row whose "Range" column shows DATE_X → DATE_X (or whose "Started" timestamp matches when
   UT-03's Step 4 was clicked)
3. In DevTools Console, scope the query to that row rather than the whole document (the table renders
   one `BackfillBreakdown` per row, each carrying the same `data-testid`), e.g. find the `<tr>` via its
   date-range cell text, then read its `[data-testid="aggregates-refreshed"]` descendant's `textContent`

**Expected Result:**
- That row's "Status" column (`data-testid="run-status"`) reads "ok"
- That row's "Symbols ok/failed" column reads "0 / 0" (a backfill-only job has no fetch stage)
- That row's Snapshots-column breakdown includes a "Refreshed: ..." sub-line, and it includes "forward
  aggregates"

**What "broken" looks like:** the row exists with Status "ok" and a nonzero new-snapshot count but has
no "Refreshed: ..." sub-line at all, or the sub-line is present but omits "forward aggregates."

---

### UT-08 — Required-still-passing journeys (J-01, J-03, J-04, J-05) remain green, with the readiness badge never freezing during each journey's own backfill step (regression)

**Type:** regression
**Priority:** P1
**Surface:** multiple (whichever pages J-01/J-03/J-04/J-05's own existing replay scripts drive)

**Maps to:** functional test plan TC-9 + TC-10

**Preconditions:**
- J-01, J-03, J-04, J-05 are currently `passing` per `docs/goal.md`
- This test does not redefine those four journeys' own steps (they belong to the existing
  deterministic golden-script / LLM-fallback regression-replay harness) — it adds one incremental
  badge-state assertion on top of whichever run that harness already performs this iteration

**Steps:**
1. Run the existing deterministic golden-script replay (or LLM fallback, for any journey without a
   golden) for J-01, J-03, J-04, and J-05 against this iteration's build, exactly as that harness
   already does
2. For J-01, J-03, and J-05 specifically (each triggers its own real backfill through the same
   rewritten warm path, per this phase's TESTING REQUIREMENTS), additionally capture
   `document.querySelector('[data-testid="readiness-badge"]').getAttribute('data-state')` at three
   checkpoints per journey: just as its backfill step begins, once mid-step, and once it completes
3. Record all four journeys' PASS/FAIL verdicts from their own harness output, plus the 3×3
   badge-state checkpoints from Step 2

**Expected Result:**
- All four journeys (J-01, J-03, J-04, J-05) re-verify PASS, unchanged from their prior baseline
- None of the 9 badge-state checkpoints captured during J-01/J-03/J-05's own backfill steps read
  `"loading"` or `"unavailable"`

**What "broken" looks like:** any of the four journeys flips from its prior PASS to FAIL/PARTIAL, or
any badge-state checkpoint captured during a J-01/J-03/J-05 backfill step reads `"loading"` or
`"unavailable"` — either is a regression this iteration must not introduce.

---

### UT-09 — The pre-fix failure states ("Backend unavailable" card, badge stuck on "Checking backend…") do not reoccur under this iteration's own load-bearing trigger (error)

**Type:** error
**Priority:** P1
**Surface:** (global) `HealthBadge`; `/backtest`

**Preconditions:**
- UT-03 and UT-04 both completed — this test performs no new trigger of its own; it is the explicit
  "the historical bug is gone" read of the evidence those two tests already captured

**Steps:**
1. Review the full `data-state` poll log recorded in UT-03 (every reading taken during the DATE_X
   backfill)
2. Count how many consecutive 20-second polling intervals (if any) showed `data-state="loading"`
3. Review whether UT-04 ever observed the red "Backend unavailable" card during its 2-minute
   resolution window

**Expected Result:**
- Zero polls in UT-03's log show `data-state="unavailable"`
- No poll shows `data-state="loading"` for more than one consecutive 20-second interval (a single
  transient tick immediately followed by "ready" is acceptable network jitter; two or more in a row
  reproduces the historical freeze)
- UT-04 never observed the "Backend unavailable" card

**What "broken" looks like:** any `data-state="unavailable"` reading, two or more consecutive
`data-state="loading"` readings, or the "Backend unavailable" card appearing on `/backtest` at any
point during the DATE_X backfill — each is exactly the iter-7/iter-13 failure mode this iteration
exists to close. Per this iteration's own escalation discipline
(`runs/goal-ops-hardening-iter-14/plan.md`: "report it plainly in the handoff — this is a second
consecutive failure of this exact code path"), any of these must be reported as-is, never rounded into
"probably fine."

---

### UT-10 — The live job's progress affordances stay clear and honest during the multi-minute warm, so an operator can tell it is alive, not stalled (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data` — Job progress panel

**Preconditions:**
- The DATE_X job from UT-03 is currently "running"

**Steps:**
1. While the job is running, read the "Job progress" panel's current-activity line (below the status
   badge), without any developer context
2. Note the "updated Ns ago" heartbeat text next to it
3. Watch both for at least two consecutive updates

**Expected Result:**
- The current-activity line names a real, changing detail (e.g. the date being scanned) rather than a
  static, unchanging placeholder for the whole run
- The "updated Ns ago" heartbeat periodically resets to a small value rather than climbing to a large,
  stale-looking number while the job still reads "running"
- A non-developer could look at this panel at any point mid-run and reasonably conclude "the job is
  still working," not "the job might be frozen"

**What "broken" looks like:** the activity line is blank or static for the whole run while `job-status`
still reads "running", or the heartbeat visibly goes stale well before the job's terminal state —
either would mean the UI is technically not frozen (per UT-03) but is misleadingly uninformative,
undermining this iteration's "honestly responsive" goal.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | `/backtest` loads with evidence panel | smoke | P1 | `/backtest` |
| UT-03 | Readiness badge never freezes during a real warm | happy-path | P1 | (global) badge |
| UT-04 | `/backtest` stays usable during the same warm | happy-path | P1 | `/backtest` |
| UT-05 | "forward aggregates" appears in live Refreshed line | happy-path | P2 | `/data` |
| UT-06 | Same value shows on persisted summary card | regression | P2 | `/data` |
| UT-07 | Same value shows in Run History row | regression | P2 | `/data` |
| UT-08 | J-01/J-03/J-04/J-05 remain green + badge never freezes | regression | P1 | multiple |
| UT-09 | Old failure states do not reoccur | error | P1 | (global) badge, `/backtest` |
| UT-10 | Job progress affordances stay clear mid-warm | ux | P3 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-03, UT-04, and UT-09 are this
iteration's canonical availability proof — the entire reason this REGRESSION-recovery iteration exists.
UT-08 protects the four Required-still-passing journeys. If any of UT-01, UT-02, UT-03, UT-04, UT-08, or
UT-09 fails, the overall verdict must be FAIL/PARTIAL regardless of how the other tests read — per this
iteration's own escalation discipline (`runs/goal-ops-hardening-iter-14/plan.md`: "report it plainly in
the handoff — this is a second consecutive failure of this exact code path"), do not soften the finding.
