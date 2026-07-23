# Phase goal-ops-hardening-iter-16 — UI Test Plan

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255 (for Network-tab inspection only; do not call directly as a substitute for a browser check)

---

## Scope note

This iteration is `Frontend Present: yes`, but the change is narrowly confined to ONE existing page's ONE
existing section: the "Forward-tested evidence" panel at the bottom of `/backtest`, which now branches
three ways on a new `evidence_status` field (`ready` / `refreshing` / `not_yet_computed`). No new page,
route, nav entry, form, or user control was added — this is a read-only status disclosure only (per the
UI surface map and user-visible-changes report). Test cases below are scoped to that one surface plus the
minimum adjacent interaction (`/data`'s existing backfill form) needed to reproduce the `refreshing` state
live; they do not duplicate the functional/API test plan's TC-01…TC-18 (`reports/qa/goal-ops-hardening-iter-16-test-plan.md`), which already covers call-count-zero proofs, byte-identity, and completeness/cutover
correctness at the API layer.

**No Validation-type test case is included.** This phase adds no new form, field, or user-input control
(confirmed in the UI surface map: "New user actions: none") — the skill's own rule ("one test per form that
was added or changed") yields zero validation tests for zero changed forms. This is a deliberate omission,
not a gap.

## Shared precondition (applies to every `/backtest` test case below)

- The top-bar readiness badge (`data-testid="readiness-badge"`, near the page header on every page) must
  read the green **"Ready"** pill — not "Checking backend…", "Initializing… history n/m", "Snapshot
  pending", or "Backend unavailable". While the badge reads "Initializing…", `/backtest` shows a DIFFERENT
  pre-existing warn-toned card ("Warming up — historical evidence still loading") in place of the ENTIRE
  results area (scorecard, evidence section, everything) — none of the three `evidence_status` states
  below are reachable until this clears. This condition is unrelated to this iteration's change and is not
  itself under test here.
- Per this session's pump note: backend is up at `http://localhost:8255`, frontend at
  `http://localhost:3255`. Neither needs to be started for the tests below — do not attempt to start or
  stop either service; if either is down, treat it as a blocked precondition and report it, per this
  session's operational constraint (agents cannot start/stop services this dispatch).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/backtest` loads with the evidence section in its normal `ready` state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Shared precondition above (readiness badge reads "Ready").
- The forward-aggregate cache is warmed for the current latest date at a single, complete `dataset_version`
  (the default/steady state — per the phase spec's own DB evidence, the current latest `asof_key` already
  has all 5 horizons at one `dataset_version`, so this is the expected out-of-the-box condition; no setup
  action is required to reach it).

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Wait for the loading skeleton (three pulsing gray cards) to disappear
3. Confirm the badge near the top reads "Viewing as-of `<today's resolved date>` (latest)" (`data-testid="backtest-asof"`)
4. Scroll to the very bottom of the page, past the "Leadership cohorts" section

**Expected Result:**
- Page renders without a blank screen and without the red "Backend unavailable" card
- The heading "Backtest" is visible near the top of the page
- A section headed "Forward-tested evidence (expanding window ≤ `<date>`)" (`data-testid="evidence-aggregate"`) is visible at the very bottom, containing populated sub-panels titled "Forward return by score bucket", "Excess vs benchmarks", "Forward return by setup type", "Forward return by market regime", and "Control-group comparison — selection vs sector beta"
- NO warn-toned card reading "Refreshing — showing the last complete evidence" appears anywhere on the page
- NO card reading "Backtest evidence not yet computed" appears anywhere on the page
- No console errors in the browser DevTools console mentioning `evidence_status`, `evidence_by_horizon`, or `evidence_generated_at`

---

### UT-02 — Operator can see the "refreshing" disclosure during a live single-day backfill (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest` (state triggered via `/data`)

**Preconditions:**
- Shared precondition above.
- `/backtest` currently shows the `ready` state (confirm via UT-01 first).
- Identify one calendar date NOT yet snapshotted: on `/data`, the coverage/availability panel shows gap
  dates; pick any single one of them.
- **Timing note (from this iteration's own operator-supervised measurement):** the full backfill job runs
  ~380 seconds (~6.3 minutes) end-to-end, and the `refreshing` window is only reachable while it is in
  flight. Budget at least 7 minutes for this test, not 5.
- **Screenshot caveat:** `/data` renders roughly 17,800px tall on this project; full-page screenshots of it
  have been observed to come back blank. If using an automated browser tool, confirm the job's state via a
  DOM/element query on `data-testid="job-status"` rather than a full-page screenshot.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" card, type the chosen not-yet-snapshotted date into the "Start date" field (`data-testid="job-start-date"`) AND the same date into the "End date" field (`data-testid="job-end-date"`) — this makes it a single-day job
3. Leave "Job kind" on its default value "Backfill snapshots"
4. Click the "Start" button
5. Confirm the "Job progress" card's status badge (`data-testid="job-status"`) now reads "running" with a spinning icon
6. Every ~30 seconds, reload `http://localhost:3255/backtest` and check the bottom of the page, until either the refreshing banner appears or 7 minutes have elapsed

**Expected Result:**
- Within the polling window, a warn/amber-bordered card (`data-testid="evidence-refreshing"`) appears directly ABOVE the "Forward-tested evidence" heading, containing a spinning icon and the exact text "Refreshing — showing the last complete evidence"
- Directly below that heading, a sentence containing a formatted generation timestamp (format `yyyy-MM-dd HH:mm:ss`, e.g. "2026-07-23 14:44:52") is visible, and it matches the timestamp state from BEFORE the backfill started (i.e., the page is honestly labeled as serving the last complete PRIOR version, not something newer or partial)
- The "Forward-tested evidence" section directly below the banner remains fully populated with real numbers — it is NOT blank and NOT replaced by a loading skeleton
- The rest of the page (As-of scan summary, Forward-test scorecard, Return Attribution, Leadership cohorts) is unaffected and still shows normal figures throughout

---

### UT-03 — "Not yet computed" empty state when no evidence has ever been computed (happy path — operator-optional, non-destructive verification only)

**Type:** happy-path
**Priority:** P2 (see rationale below — not independently blocking for this iteration's UI verdict)
**Surface:** `/backtest`

**Preconditions:**
- **Do NOT run this test against the current shared/live database.** Every `asof_key` currently stored has
  already-computed forward-aggregate evidence; there is no non-destructive way to reach
  `evidence_status == "not_yet_computed"` on it. Do not delete `ForwardAggregateCache` rows or any other
  data to force this state — that would be a destructive test action and is out of scope for this plan.
- This test requires a SEPARATE, throwaway/freshly-seeded backend + database (e.g., a fresh
  `apps/backend/data/trendora.db` built from the seed script, pointed to by its own backend process on a
  different port) where the current latest date has never had a forward-aggregate finalize warm complete.
  Standing up that throwaway instance is itself a service action outside this test plan's scope — request
  it from the operator if this test is to be run live.
- **If no throwaway database is available, SKIP this test.** Its response-shape contract
  (`evidence_status == "not_yet_computed"`, `evidence_by_horizon == {}`, `evidence_generated_at == null`,
  HTTP 200) is already proven by 10/10 passing unit tests in
  `apps/backend/tests/test_forward_testing_serving_split.py` per the dev handoff. Record this row as
  "covered by API/unit tests only — not live-browser-verified" rather than fabricating a pass or fail.

**Steps (only if a throwaway backend/database is available):**
1. Point the browser at the `/backtest` page served by the throwaway backend (a different origin/port than the live `http://localhost:3255`)
2. Wait for the loading skeleton to disappear
3. Scroll to the bottom of the page, to where "Forward-tested evidence" would normally appear

**Expected Result:**
- In place of the evidence section, a dashed-border card is visible containing a flask icon, the title "Backtest evidence not yet computed", and the description "Backtest evidence not yet computed — run an ingest to populate the forward-tested evidence for this date. No numbers are fabricated in the meantime."
- No horizon numbers, tables, or charts appear anywhere in that section
- Scrolling up, the "As-of scan summary", "Forward-test scorecard", "Return Attribution", and "Leadership cohorts" sections above it still render their normal content, unaffected by the empty evidence state

---

### UT-04 — Cutover: refreshing banner disappears once the backfill's finalize warm completes (regression / continuation of UT-02)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest` (state triggered via `/data`)

**Preconditions:**
- UT-02 has been run and the refreshing banner was observed.
- The `/data` job started in UT-02 is still tracked (do not navigate away from the browser tab/session in a
  way that loses the job reference — reloading `/data` itself is fine, as job status is read from the
  backend, not local component state alone, via `data-testid="job-status"`).

**Steps:**
1. On `http://localhost:3255/data`, keep reloading the page every ~30 seconds until the "Job progress" card's status badge (`data-testid="job-status"`) reads "ok" (not "running")
2. On the same job card, confirm a line reading "Refreshed: forward aggregates" (`data-testid="aggregates-refreshed"`) is present (it may list additional refreshed aggregates alongside it, comma-separated)
3. Navigate to `http://localhost:3255/backtest` (or reload it)
4. Scroll to the bottom of the page

**Expected Result:**
- The warn-toned "Refreshing — showing the last complete evidence" card from UT-02 (`data-testid="evidence-refreshing"`) is GONE
- The "Forward-tested evidence" section still shows fully populated numbers (not blank, not a skeleton)
- No "Backtest evidence not yet computed" empty state appears
- This confirms the page auto-updates to the new version once the background warm finishes, with no manual refresh-and-recompute action required by the user beyond a normal page reload

---

### UT-05 — Ready-state evidence section renders all of its original sub-panels unchanged (regression, structural)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Shared precondition above; `/backtest` in its normal `ready` state (no active backfill in progress).

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Scroll to the "Forward-tested evidence (expanding window ≤ `<date>`)" section at the bottom
3. Confirm the summary line (`data-testid="evidence-summary"`) is visible directly under the section heading
4. Scroll through the full section, noting every sub-panel title present

**Expected Result:**
- The summary line shows "Snapshots contributing (≤ `<date>`): `<n>`", "As-of range: `<date>` → `<date>`", "Mean stock fwd return (`<h>`d): `<value>` (n=`<n>`)", and "Mean max drawdown (`<h>`d): `<value>`"
- All of the following sub-panel titles are present, in this order: "Forward return by score bucket", "Excess vs benchmarks", "Forward return by setup type", "Forward return by market regime", "Forward return: VCP vs non-VCP", "Forward return: Pullback-to-rising-DMA vs not", "Control-group comparison — selection vs sector beta"
- None of these panels are missing, reordered, or replaced by any new UI element — the refactor into a 3-way branch introduced no visible change to this steady-state path

---

### UT-06 — Rest of `/backtest` page is unaffected while the evidence section is in a non-`ready` state (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- Either UT-02 (mid-backfill, `refreshing`) or UT-03 (`not_yet_computed`, throwaway DB only) is in progress/reachable.

**Steps:**
1. While `/backtest` is showing either the refreshing banner or the not-yet-computed empty state, scroll to the TOP of the page
2. Confirm the "Survivorship bias" card is present and reads its usual caveat text
3. Scroll down through "As-of scan summary" (Market Regime card, Candidate Counts card), then "Forward-test scorecard", then "Return Attribution", then "Leadership cohorts" (Top Sectors, Top Themes, Ranked cohort table)

**Expected Result:**
- Every one of these sections renders its normal populated content (regime score, candidate counts, scorecard rows, attribution numbers, leadership lists) exactly as it does in the `ready` state
- None of these sections shows a loading skeleton, an error card, or any trace of the evidence section's refreshing/not-yet-computed treatment leaking upward — the new disclosure is confined entirely to the bottom evidence section

---

### UT-07 — Historical as-of viewing is unaffected by this iteration's change (regression, TC-13 browser confirmation)

**Type:** regression
**Priority:** P2
**Surface:** `/backtest` (via the as-of switcher)

**Preconditions:**
- Shared precondition above; `/backtest` in its normal `ready` (latest) state.
- At least one historical (non-latest) date is selectable in the as-of switcher.

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Click the as-of switcher button near the top of the page (`data-testid="asof-trigger"`, initially reading "Latest")
3. In the calendar that opens (`data-testid="asof-calendar"`), click any enabled day cell (`data-testid="asof-cal-day"`) for a date other than the current latest date
4. Wait for the page to reload with the new date
5. Scroll to the bottom of the page

**Expected Result:**
- The badge near the top now reads "Viewing as-of `<chosen date>` (historical)"
- The "Forward-tested evidence (expanding window ≤ `<chosen date>`)" heading reflects the chosen historical date
- On the FIRST view of this historical date, the evidence section may take a few seconds longer to appear than the latest-date view did (a one-time compute) — but it still resolves to a normal, fully populated evidence section (or the pre-existing, unrelated "No forward-tested evidence for this window yet" message if the chosen date is early enough that no forward window has elapsed yet — this is a distinct, older empty state, not this iteration's `not_yet_computed` disclosure)
- Reloading the SAME historical date again immediately afterward is fast (served from cache, no repeated delay)
- No "Refreshing — showing the last complete evidence" banner appears for a historical date (this iteration's `evidence_status` disclosure is exercised on the latest view only, per the phase's own documented scope note)

---

### UT-08 — Backend-unavailable error card still shown when the API fails (error)

**Type:** error
**Priority:** P2 (see operational note below)
**Surface:** `/backtest`

**Preconditions:**
- The backend must be unreachable to `/backtest`'s fetch. **Stopping the backend is a service action —
  per this session's operational constraint, only the operator may do this; an automated agent must not
  stop the service to run this test.** If the backend cannot be safely made unreachable this pass, mark
  this row "not independently re-verified this iteration" and note that the underlying error-rendering
  code path (`state.kind === "error"` in `page.tsx`) was NOT touched by this iteration's diff (confirmed
  against the UI surface map — this iteration's change is confined to the bottom evidence-section branch
  inside `BacktestResults`, not the page-level fetch/error handling above it) — this is a low-risk,
  pre-existing path, not new code.

**Steps (operator-performed, or skip per the note above):**
1. With the backend intentionally unreachable, navigate to `http://localhost:3255/backtest`
2. Wait a few seconds for the fetch to fail

**Expected Result:**
- A card with a warning-triangle icon and the text "Backend unavailable" is visible
- Below it, the text "The backtest scorecard could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." is visible
- Nothing else renders on the page — no partial evidence numbers, no refreshing banner, no empty-state card

---

### UT-09 — Refreshing banner reads as calm and factual, not alarming, and never blocks the page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- Same as UT-02 — `/backtest` showing the refreshing banner during a live backfill.

**Steps:**
1. With the refreshing banner visible (`data-testid="evidence-refreshing"`), read its full text without any developer/API knowledge
2. Note its color treatment (border/icon color) relative to the page's other status banners ("Survivorship bias" card above it)
3. Confirm you can still scroll, interact with the Horizon selector buttons ("1d"/"5d"/"10d"/"20d"/"60d"), and read the evidence numbers while the banner is showing

**Expected Result:**
- The banner's full text ("Refreshing — showing the last complete evidence" + the explanatory sentence about a newer dataset version being warmed, with the generation timestamp) is understandable on its own, with no jargon requiring backend knowledge (no mention of `dataset_version`, cache keys, or internal function names)
- Its amber/warn border-and-icon treatment visually matches the page's OTHER existing status banners (Survivorship bias, the historical Warming-up state) rather than introducing a jarring new color or a red/danger treatment — it reads as informational, not as an error
- The rest of the page remains fully interactive: the Horizon selector still switches views, and all evidence numbers remain readable — the banner never disables or dims anything below it

---

### UT-10 — Data contract: `evidence_status` and `evidence_generated_at` are present in the actual API response (ux / data-contract confirmation)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest` (Network tab)

**Preconditions:**
- Shared precondition above.
- Browser DevTools available (Network tab).

**Steps:**
1. Open the browser DevTools Network tab
2. Navigate to `http://localhost:3255/backtest` (or reload it)
3. Find the `GET /api/backtest` request in the Network tab and open its Response/Preview body
4. Locate the `evidence_status` and `evidence_generated_at` keys in the JSON body, alongside the pre-existing `evidence_by_horizon` key

**Expected Result:**
- `evidence_status` is present and is one of the exact strings `"ready"`, `"refreshing"`, or `"not_yet_computed"` — matching whichever visual state the page is currently rendering (cross-check against what's on-screen: if the page shows the refreshing banner, this field reads `"refreshing"`; if it shows the empty state, `"not_yet_computed"`; otherwise `"ready"`)
- `evidence_generated_at` is present and is either an ISO-8601 datetime string, or `null` — and it is `null` ONLY when `evidence_status` is `"not_yet_computed"`
- `evidence_by_horizon` is present and is an empty object `{}` ONLY when `evidence_status` is `"not_yet_computed"`; otherwise it is populated with one entry per configured horizon (1/5/10/20/60)
- This confirms the on-screen disclosure is driven by real backend data, not a frontend-only guess or a hardcoded UI state

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/backtest` loads, ready-state evidence renders | smoke | P1 | `/backtest` |
| UT-02 | Refreshing banner appears during a live backfill | happy-path | P1 | `/backtest` (+ `/data`) |
| UT-03 | Not-yet-computed empty state (throwaway DB only) | happy-path | P2 | `/backtest` |
| UT-04 | Cutover back to ready after the warm completes | regression | P1 | `/backtest` (+ `/data`) |
| UT-05 | Ready-state sub-panels unchanged | regression | P1 | `/backtest` |
| UT-06 | Rest of page unaffected during non-ready states | regression | P2 | `/backtest` |
| UT-07 | Historical as-of viewing unaffected | regression | P2 | `/backtest` |
| UT-08 | Backend-unavailable error card intact | error | P2 | `/backtest` |
| UT-09 | Refreshing banner tone/discoverability | ux | P2 | `/backtest` |
| UT-10 | Data-contract fields visible in Network tab | ux | P2 | `/backtest` |

**No validation-type test case** — this phase adds no new form/field (see "Scope note" above).

**P1 tests must all pass for browser QA verdict to be PASS.** UT-01, UT-02, UT-04, and UT-05 are P1 because
together they prove the complete J-08 loop live in a browser: the steady state is intact (UT-01/UT-05), the
new disclosure appears correctly during a real ingest (UT-02), and it correctly reverts once the ingest
finishes (UT-04). UT-03 is P2 despite being a "core new capability" test because the pump note for this
dispatch explicitly directs against designing a destructive test to reach it on the current live database;
it is already proven at the unit/API layer and is operator-optional here.
