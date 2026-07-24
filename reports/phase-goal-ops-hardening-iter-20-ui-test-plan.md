# Phase goal-ops-hardening-iter-20 — UI Test Plan

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL (curl fallback only — never used in the primary browser steps below):** http://localhost:8255

---

## Scope

This iteration touches exactly ONE page — `/backtest` — and, on that page, exactly two pre-existing
components' copy (`RefreshingEvidenceBanner`, the `not_yet_computed` `EmptyState`) plus the page's own
response-time behavior for a first-ever view of a historical as-of date. No new page, panel, button, field,
or nav entry exists this iteration. Test cases below are derived from all 4 rows of
`reports/phase-goal-ops-hardening-iter-20-ui-surface-map.md`. MCP `query_backtest` and all backend-only
changes (dispatch mechanism, pytest updates) are covered by `reports/qa/goal-ops-hardening-iter-20-test-plan.md`
(TC-01…TC-16) and are NOT duplicated here.

## Setup Notes — read before testing

- **Frontend URL param is `asof` (no underscore).** Example: `http://localhost:3255/backtest?asof=2026-07-09`.
  This is DIFFERENT from the backend API's own param name `as_of` (used only in curl/API calls, e.g.
  `http://localhost:8255/api/backtest?as_of=2026-07-09`). Typing the backend's `as_of=` spelling into the
  browser's address bar will NOT deep-link a historical date — the frontend will silently show the Latest
  view instead, because `asof-provider.tsx` only recognizes its own `asof` param.
- **No login required.** This is a local, single-operator tool with no authentication.
- **Do not trigger a backfill/ingest.** Nothing below does; every step is a page navigation or a read-only
  `GET /api/backtest` fetch, which this session's own anti-goal review (AG-10) has classified as a safe read.
- **Two dates are already "warm" as of this iteration's own measurement and must NOT be used to demonstrate
  the "never-viewed / cold" scenario:** `2026-07-09` and `2026-07-08` (both computed live during this
  iteration's `reports/perf-budgets.md` "Iteration 20" pass — they will now load instantly with `ready`
  evidence and no interim banner, which defeats the point of a cold-path test). They ARE useful as a quick
  "already-warm date loads clean" sanity check if you want one.
- **Confirm the boot-time warm-up has finished before testing anything below**: the header's readiness badge
  (top-right of every page, `data-testid="readiness-badge"`) must read **"Ready"**, not "Initializing…". While
  "Initializing…" is showing, the ENTIRE evidence section is replaced by a page-wide "Warming up" placeholder
  (a separate, pre-existing capability unrelated to this iteration) and the tests below cannot observe the
  right state.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results. -->

---

### UT-01 — `/backtest` loads in the Latest (default) view without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- Frontend running at http://localhost:3255; backend reachable (confirmed in Step 3 below)
- Fresh tab — no historical as-of date currently selected

**Steps:**
1. Open a new browser tab and navigate to `http://localhost:3255`
2. In the left sidebar, click the "Backtest" link (flask-shaped icon)
3. Wait for the page to finish loading

**Expected Result:**
- URL is now `http://localhost:3255/backtest`
- The heading "Backtest" is visible, with subtitle text starting "Time-machine to a past scan date and read
  its forward-test scorecard..."
- The top-right header shows a badge reading **"Ready"** (`data-testid="readiness-badge"`) — NOT
  "Initializing…", "Snapshot pending", or "Backend unavailable"
- The top-right as-of control (`data-testid="asof-trigger"`) reads **"Latest"**
- A badge near the top of the page content reads "Viewing as-of `<today's latest date>` (latest)"
  (`data-testid="backtest-asof"`)
- The "Forward-test scorecard" table and "Leadership cohorts" section render with populated data — not a
  blank page, not a stuck pulsing skeleton
- No "Backend unavailable" red error card appears anywhere on the page
- No red errors in the browser console

---

### UT-02 — First-ever view of a never-viewed historical date responds promptly with an honest interim state (happy-path)

**Type:** happy-path
**Priority:** P1 — this is the core new capability this iteration ships
**Surface:** `/backtest`

**Preconditions:**
- UT-01 passed
- Header readiness badge reads "Ready"
- You will pick a historical date via the calendar in Step 2 that you have not personally visited yet this
  session — do NOT use `2026-07-09` or `2026-07-08` (see Setup Notes — already warm)

**Steps:**
1. On `http://localhost:3255/backtest`, click the "Latest" button in the top-right header
   (`data-testid="asof-trigger"`) — a calendar popover opens (`data-testid="asof-calendar"`)
2. Click the year dropdown (`data-testid="asof-cal-year"`) and select the **earliest (smallest) year** in
   the list
3. Look at the day grid. Selectable days are colored/bordered buttons (`data-testid="asof-cal-day"`);
   non-selectable days are faint gray, non-clickable numbers (`data-testid="asof-cal-day-disabled"`). If the
   shown month has zero colored days, click "▶" (Next month, `data-testid="asof-cal-next"`) or change the
   month dropdown (`data-testid="asof-cal-month-select"`) repeatedly until a month shows at least one colored
   day
4. Start timing, then click that colored day
5. Watch the page immediately after the click

**Expected Result:**
- The calendar closes and the page finishes updating in well under 2 seconds — it must NOT sit blank or
  frozen waiting for anything
- The as-of badge (`data-testid="backtest-asof"`) now reads "Viewing as-of `<the date you clicked>`
  (historical)" — **write this date down, UT-03/UT-05/UT-07/UT-10 reuse it**
- Near the bottom of the page (below "Leadership cohorts"), ONE of these two honest interim states is
  visible — both are a PASS:
  - **Either** a warn-colored (amber) card headed **"Refreshing — showing the last complete evidence"**
    (`data-testid="evidence-refreshing"`, spinning loader icon) whose body includes "This date's own
    evidence is being computed in the background (started by viewing this page) and is not complete yet."
  - **Or** a dashed-border empty-state card headed **"Backtest evidence not yet computed"** (flask icon)
    whose description includes "Viewing this page has started computing it in the background — reload
    shortly to see it."
- **FAIL condition:** the page stays blank/unresponsive for several seconds (the old behavior took 9.6–54 s)
  before anything appears, or a fully populated "Forward-tested evidence" section with real numbers appears
  in under 2 seconds with an `is_latest`-style ingest excuse in a refreshing banner that shouldn't be there
- **If the page instead shows fully populated evidence immediately with NO refreshing banner and no empty
  state:** this date was already warmed by an earlier run of this test — pick a different colored day and
  repeat from Step 4

---

### UT-03 — Revisiting the same historical date after the background compute finishes shows real, ready evidence (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/backtest`

**Preconditions:**
- UT-02 just completed; you know the exact historical date (D) it selected
- Per this iteration's own operator measurement (`reports/perf-budgets.md`, "Iteration 20"), the background
  compute finishes roughly 30 seconds after UT-02's Step 4 click

**Steps:**
1. Wait until at least 30 seconds have passed since UT-02's Step 4 click
2. Reload the page (press F5) — the URL should still show the same date D (or reselect D via the calendar
   exactly as in UT-02 Steps 1–4 if the URL was not preserved)
3. Look at the bottom of the page

**Expected Result:**
- The "Refreshing" banner and the "Backtest evidence not yet computed" empty state are BOTH gone
- A section headed **"Forward-tested evidence (expanding window ≤ D)"** is visible
  (`data-testid="evidence-aggregate"`)
- Directly below that heading, a line reads **"Snapshots contributing (≤ D): `<a number greater than 0>`"**
  (`data-testid="evidence-summary"`)
- The as-of badge still reads "Viewing as-of D (historical)"
- **If the empty/refreshing state is still showing:** wait another 30 seconds and reload once more before
  treating this as a FAIL — compute duration can vary with host load (peak 79 °C was recorded during this
  iteration's own measurement)

---

### UT-04 — The default Latest `/backtest` view is completely unaffected by this iteration (regression)

**Type:** regression
**Priority:** P1 (elevated above the usual regression default — this directly re-confirms the phase spec's
own binding guarantee: "The LATEST view/branch — unaffected... does not reach the new dispatch path")
**Surface:** `/backtest`

**Preconditions:**
- UT-02/UT-03 performed (page currently showing a historical date)

**Steps:**
1. Click the as-of control in the top-right header (`data-testid="asof-trigger"`) to reopen the calendar
2. Click the **"Latest · `<date>`"** button at the bottom of the popover (`data-testid="asof-cal-latest"`)
3. Observe the page

**Expected Result:**
- The page returns to the Latest view immediately — no delay, no refreshing banner, no empty state (this
  code path never reaches the new historical dispatch mechanism at all, before or after this iteration)
- The as-of badge reads "Viewing as-of `<today's latest date>` (latest)", not "(historical)"
- If the latest date's own evidence happens to be `ready` (the normal steady state), the "Forward-tested
  evidence" section shows real data directly with no "Refreshing" banner
- The URL no longer carries an `?asof=` query parameter

---

### UT-05 — `RefreshingEvidenceBanner`'s historical-view copy names the true cause (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest` (evidence section)

**Preconditions:**
- A historical date is showing the "Refreshing — showing the last complete evidence" banner. Reuse UT-02's
  date if it landed in the refreshing branch; otherwise repeat UT-02 Steps 1–4 with a fresh date until the
  refreshing banner (not the empty state) appears

**Steps:**
1. With the banner visible (`data-testid="evidence-refreshing"`), read its full body text top to bottom
2. Check the text against every bullet below

**Expected Result** — ALL of the following must hold:
- It does **NOT** say "The dataset has changed since this evidence was generated" (that sentence is reserved
  for the Latest-view cause — it would be FALSE here, since no ingest is necessarily involved)
- It **DOES** say "This date's own evidence is being computed in the background (started by viewing this
  page) and is not complete yet."
- It names which older evidence is being shown meanwhile, e.g. "evidence as of `<date>`, generated
  `<timestamp>`"
- It does **NOT** say "Reload this page after the next ingest finishes" (also reserved for the Latest cause)
- It **DOES** say "Reload this page shortly to pick up this date's own evidence once the background compute
  finishes."
- Visual tone stays calm/amber (warn-colored border, spinning loader icon) — not red/alarming

---

### UT-06 — `EmptyState`'s historical-view copy acknowledges viewing the page as the trigger (ux, best-effort)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest` (evidence section)

**Preconditions:**
- This is only observable when a historical date resolves to the true "not yet computed" state — i.e. no
  fallback evidence exists at or before it anywhere in the store. This is a narrower condition than UT-02's
  "refreshing" case; on a long-running instance most dates already have SOME older fallback, so this may not
  be reachable every run. Try the OLDEST selectable date first (fewest older dates to fall back to)

**Steps:**
1. Using the calendar, set the year dropdown (`data-testid="asof-cal-year"`) to the earliest year, then
   click the earliest selectable (colored) day in that year
2. Look at the bottom of the page

**Expected Result:**
- **If** the empty-state card titled "Backtest evidence not yet computed" appears (flask icon, dashed
  border), its description must:
  - **NOT** read only "Backfilling or fetching data that covers it will compute this evidence" (that
    phrasing alone is reserved for the Latest cause and is incomplete/misleading for a historical view)
  - **DO** say "Viewing this page has started computing it in the background — reload shortly to see it."
  - Still include "No numbers are fabricated in the meantime" (shared, unchanged wording)
- **If instead** the page shows the "Refreshing" banner or fully populated evidence (because even the oldest
  date has some older fallback, or was already warmed by a prior test run): record "not reachable this run"
  — this is NOT a product FAIL, just a data condition this instance doesn't currently expose. UT-05 already
  exercises the sibling `is_latest`-branch copy logic that this same code path shares.

---

### UT-07 — Backend readiness badge never drops during the background-compute window (regression, DoD-critical)

**Type:** regression
**Priority:** P1 (elevated — this is J-07's explicit "no-wedge" promise and a phase Definition-of-Done item,
mirrors backend TC-5)
**Surface:** header (every page), observed from `/backtest`

**Preconditions:**
- A background compute is in flight — perform this immediately after UT-02's Step 4 click, inside the ~30 s
  window before UT-03's reload

**Steps:**
1. Immediately after UT-02's click, look at the readiness badge in the top-right header
   (`data-testid="readiness-badge"`)
2. Watch it for the next 20–30 seconds (glance every ~5 seconds without navigating away)
3. Once during this window, click "Dashboard" in the sidebar, then click "Backtest" again

**Expected Result:**
- The badge reads **"Ready"** (green dot, `data-state="ready"`) continuously throughout
- It never flips to "Backend unavailable" (red, `data-state="unavailable"`) and never freezes
- The Dashboard/Backtest round-trip in Step 3 completes — a brief 1–2 s extra delay is acceptable (see
  UT-10's documented residual) but nothing hangs indefinitely or errors

---

### UT-08 — The rest of the `/backtest` page is unaffected during a historical first-view (regression, low risk)

**Type:** regression
**Priority:** P3
**Surface:** `/backtest`

**Preconditions:**
- A historical date is selected (reuse UT-02's date)

**Steps:**
1. While the Refreshing banner or empty state is showing (right after UT-02), scroll from the top of the
   page to the bottom
2. Check each section in turn: Survivorship bias banner → "As-of scan summary" (Market Regime + Candidate
   Counts) → "Forward-test scorecard" table → "Return Attribution" (with its Horizon selector buttons) →
   "Leadership cohorts" (Top Sectors / Top Themes / Ranked cohort)

**Expected Result:**
- Every section listed renders populated data for the selected historical date — none of them are blank or
  show an error card, and none of them depend on the `evidence_status` dispatch this iteration changed
- Only the evidence section at the very bottom (below Leadership cohorts) shows the interim
  Refreshing/EmptyState — everything above it is fully populated exactly as before this iteration

---

### UT-09 — An unknown/malformed `asof` URL value degrades gracefully to the Latest view (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- None beyond the frontend running

**Steps:**
1. Type directly into the browser's address bar and press Enter: `http://localhost:3255/backtest?asof=not-a-real-date`
2. Observe the page once it settles

**Expected Result:**
- The page does NOT crash and shows no raw error/stack trace
- The address bar settles on `http://localhost:3255/backtest` with the invalid `?asof=` parameter stripped
- The as-of badge reads "Viewing as-of `<today's latest date>` (latest)" — the malformed value silently
  degrades to Latest, exactly as before this iteration (this iteration did not touch this pre-existing
  validation path; this test confirms it still holds)

---

### UT-10 — A concurrent second-tab request during the background-compute window is slower but never hangs (regression, documented residual)

**Type:** regression
**Priority:** P3
**Surface:** `/backtest`

**Preconditions:**
- A background compute is in flight (within ~30 s of UT-02's Step 4 click)

**Steps:**
1. Immediately after UT-02's click, open a SECOND browser tab
2. In the new tab, navigate to `http://localhost:3255/backtest` (Latest view is fine)
3. Time how long this second tab takes to finish loading

**Expected Result:**
- The second tab's page DOES finish loading — never spins forever, never shows "Backend unavailable"
- Up to ~6 seconds is ACCEPTABLE here (slower than the normal sub-second response) — this is a documented,
  accepted residual of running the compute in-process (`reports/perf-budgets.md`, "Iteration 20": 3.0–6.3 s
  observed under this exact condition). This is NOT a failure.
- Only an outright hang (>15 s with no response) or a crash/error page is a FAIL

---

### UT-11 — Backtest + the as-of time-machine control are reachable within 2 clicks (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar / header

**Steps:**
1. Navigate to `http://localhost:3255` (the Dashboard / home page)
2. Look at the left sidebar

**Expected Result:**
- A "Backtest" link (flask-shaped icon) is visible in the sidebar — 1 click reaches `/backtest`
- Once on `/backtest`, the as-of control (reading "Latest", calendar icon) is visible in the top-right
  header, in the same position/label as on every other page — a 2nd click opens the date picker
- No new or renamed sidebar entry was introduced this iteration (confirms "Navigation changes: no" from the
  UI surface map)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Latest view loads without errors | smoke | P1 | `/backtest` |
| UT-02 | Never-viewed historical date responds fast + honest interim | happy-path | P1 | `/backtest` |
| UT-03 | Revisit after compute finishes → real ready evidence | happy-path | P1 | `/backtest` |
| UT-04 | Latest view completely unaffected | regression | P1 | `/backtest` |
| UT-05 | RefreshingEvidenceBanner historical copy is true | ux | P2 | `/backtest` |
| UT-06 | EmptyState historical copy is true (best-effort) | ux | P2 | `/backtest` |
| UT-07 | Readiness badge never drops during compute | regression | P1 | header |
| UT-08 | Rest of page unaffected during historical first-view | regression | P3 | `/backtest` |
| UT-09 | Malformed `asof` degrades to Latest | validation | P2 | `/backtest` |
| UT-10 | Concurrent second tab slower but never hangs | regression | P3 | `/backtest` |
| UT-11 | Backtest + as-of control reachable in 2 clicks | ux | P3 | nav/header |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-03, UT-04, UT-07.

**Not covered here (see `reports/qa/goal-ops-hardening-iter-20-test-plan.md` instead):** dispatch-once
guarantee under concurrency (TC-3), byte-identity of served evidence (TC-4), MCP `query_backtest` parity
(TC-6), dispatch-owner-failure recovery (TC-7 — not reproducible through the UI without injecting a backend
fault), the updated pytest contracts (TC-10/TC-11/TC-16), and the two owner-gated scenarios (TC-13 ingest
overlay, TC-14 disruptive kill/restart).
