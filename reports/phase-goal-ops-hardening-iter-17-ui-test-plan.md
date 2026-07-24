# Phase goal-ops-hardening-iter-17 — UI Test Plan

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** ui-test-designer
**Frontend URL (main pair):** http://localhost:3255 (backend http://localhost:8255)
**Frontend URL (THROWAWAY pair — see Scope note):** http://127.0.0.1:13255 (backend http://localhost:18255)

---

## Scope & Environment Notes

Read this before executing any test case below.

- **Two service pairs are live this session, not one.** The MAIN pair (`:3255`/`:8255`) is the regular,
  populated working app — most tests run here. A SEPARATE, DISPOSABLE THROWAWAY pair (`:13255`/`:18255`)
  is also live, deliberately pointed at a never-ingested copy of `trendora.db`, solely so the
  `not_yet_computed` empty state can finally be seen in a real browser (it never has been, since iter-16).
  Every test case below names which pair it targets. **Do not confuse the two** — actions on one have no
  effect on the other, and the throwaway pair's boot was already done for you; do not start, stop, or
  restart either pair.
- **The new iter-17 cross-`asof_key` fallback cannot be exercised live this session, on either pair.** It
  only fires when the LATEST trading day advances past a date that has no complete forward-aggregate
  version yet, and this project's price basis ends at the latest snapshotted date (2026-07-22) with no
  future day to backfill into (no live external data calls are ever made — AG-9). Do not design or run a
  test that pretends otherwise. That logic is fully covered by backend unit tests only — 15/15 passing per
  `reports/qa/goal-ops-hardening-iter-17-qa.md` (Step 2), including
  `test_evidence_crosses_asof_key_boundary_when_newer_key_has_zero_rows` and its 2 siblings.
- **A separate, reachable browser gap does exist and is closed by UT-03 below**: the iter-17 CORRECTED
  `RefreshingEvidenceBanner` copy (plus its new `evidence_asof` label) has never been captured live — the
  only screenshot on file (`TC-07-backtest-page.png`/`TC-07-evidence-section.png`, both saved during the
  prior QA pass) shows the plain `ready` state, not `refreshing`. UT-03 reaches `refreshing` via the
  PRE-EXISTING (iter-16) same-`asof_key` stale-version mechanism, not the new cross-boundary one — see that
  test's own "IMPORTANT" note for why this distinction matters and must not be blurred in reporting.
- **`/data` is very tall (~17,800px).** A full-page screenshot there can come back blank. Prefer a
  scoped/element screenshot or a DOM text assertion over a full-page capture whenever a step touches `/data`.
- This iteration's functional (API/unit) test plan (`reports/qa/goal-ops-hardening-iter-17-test-plan.md`)
  already covers `curl`-level JSON assertions for `evidence_asof`, the MCP tool, and TC-11's health poll —
  none of that is repeated here; every test case below is a real browser action with a visible outcome.
- No form was added or changed this iteration (the `/data` job form is reused unmodified, purely as a
  trigger in UT-03) — there is deliberately no dedicated **validation**-type test case. The one
  error-shaped concern this iteration's spec calls out ("a request with no complete version anywhere must
  still answer HTTP 200 with the honest empty state, never a 500") is covered live by UT-02, not by a
  separate **error**-type case.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Main `/backtest` page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest` (MAIN pair)

**Preconditions:**
- Main backend (`http://localhost:8255`) and frontend (`http://localhost:3255`) are already running —
  do not start/stop them.
- No login exists in this app.

**Steps:**
1. Navigate to `http://localhost:3255/backtest`.
2. Wait for the page to finish loading (any brief loading skeleton disappears).
3. Open the browser console.

**Expected Result:**
- The page renders — no blank screen, and no red "Backend unavailable" card.
- The heading "Backtest" (an `<h1>`) is visible near the top.
- A badge reading "Viewing as-of `<date>` (latest)" is visible directly below the heading (with a small
  clock icon).
- A "Survivorship bias" card is visible below that badge.
- Scrolling down, both the "Forward-test scorecard" heading and the "Leadership cohorts" heading are
  visible, each above a populated table (not blank).
- No uncaught JavaScript error appears in the browser console.

---

### UT-02 — `not_yet_computed` empty state renders correctly (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/backtest` (**THROWAWAY pair — port 13255/18255, NOT the main app**)

**Preconditions:**
- The disposable throwaway backend (`:18255`) and frontend (`:13255`) are already running, pointed at a
  never-ingested copy of `trendora.db` (schema created, zero rows). This pair was booted for you
  specifically for this check — do not start, stop, or restart it.
- This is a completely separate instance from `http://localhost:3255`/`:8255`. Nothing done here touches
  the main working database.

**Steps:**
1. Navigate to `http://127.0.0.1:13255/backtest`.
2. Wait for the page to finish loading.
3. Scroll to the bottom of the page.
4. Refresh the page (F5) and scroll to the bottom again.

**Expected Result:**
- The page renders — no blank screen, and no red "Backend unavailable" card (a genuinely empty database
  is a designed, honest state here, never an application error).
- Near the top, the "As-of scan summary" area shows "Scan summary unavailable for this date" — expected on
  an empty DB, not the focus of this test.
- At the bottom, a dashed-bordered card is visible with a flask-shaped icon, the title "Backtest evidence
  not yet computed", and directly beneath it the description: *"No forward-tested evidence exists yet for
  this date. Backfilling or fetching data that covers it will compute this evidence — no numbers are
  fabricated in the meantime."*
- The phrase **"run an ingest"** does NOT appear anywhere in that description (removed this iteration,
  audit F2).
- The description reads as ONE clean sentence pair, not a repeated opening clause (audit F3 — the
  pre-iter-17 copy duplicated "Backtest evidence not yet computed" across the title and the body's own
  first words).
- After the step-4 refresh, the identical card/title/description reappear — no crash, no different
  content, no new console error.
- Capture a screenshot of the card (element-scoped, not necessarily full-page) and save it as
  `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png` — this closes the
  still-open TC-09 live-capture gap recorded in `reports/qa/goal-ops-hardening-iter-17-qa.md`'s
  "Deferred/Documented Limitations".

---

### UT-03 — Live capture: corrected "Refreshing" banner + `evidence_asof` label (happy-path)

**Type:** happy-path
**Priority:** P1 *(time-boxed — a documented non-capture is an acceptable outcome; see the last bullet
below and the Scope note above)*
**Surface:** `/data` then `/backtest` (MAIN pair)

**Preconditions:**
- Main backend/frontend already running at `:8255`/`:3255`.
- **IMPORTANT — what this test does and does NOT prove:** this test re-triggers ANY new ingest to bump
  the shared version stamp, which momentarily makes the CURRENT latest date's OWN forward-aggregate rows
  stale while its still-complete PRIOR version keeps being served (`evidence_asof` equal to that SAME
  date) — the pre-existing, iter-16-established mechanism. It does **not** exercise the NEW iter-17
  cross-`asof_key` fallback (which would show an OLDER date's `evidence_asof`) — that scenario is
  unreachable this session (see Scope note). Do not report this test as proof of the cross-boundary fix;
  it proves only that the corrected banner text and the new `evidence_asof` label render correctly when
  `refreshing` occurs at all.

**Steps:**
1. Navigate to `http://localhost:3255/data`.
2. Look at the "Start a fetch / backfill job" panel. Check whether the "Start date" and "End date" fields
   already show non-blank `yyyy-mm-dd` values (this page auto-fills them from the dataset's own real
   backfill gaps on load — you do not need to know or type a date yourself).
   - If BOTH fields are blank, there are no backfill gaps left in the working dataset. **Stop here** — do
     not type in dates yourself or invent a range. Skip to "If the window can't be reached" below and
     document that this test could not be attempted this session (no gap available).
3. Confirm the "Job kind" dropdown reads "Backfill snapshots" (its default). Leave it unchanged.
4. Do **not** click the "Rebuild snapshots for current universe" button elsewhere on this page — that is
   a much larger, unrelated, full-history operation and is not needed here.
5. Click the "Start" button (to the right of the Job kind dropdown).
6. Confirm the button's own label changes to "Job running…" with a spinning icon, and that — under the
   separate "Job progress" panel heading on the same page — a badge reading "running" (its own spinning
   icon) appears.
7. Open a SECOND browser tab to `http://localhost:3255/backtest` (no query parameters — the default
   latest view) and scroll to the bottom evidence section.
8. Reload this second tab every 30-60 seconds — leave the first `/data` tab alone; do not resubmit the
   form — for up to about 8 minutes, or until the `/data` tab's job-status badge leaves "running".
9. The moment the evidence section is preceded by an amber/warn-bordered card with a spinning icon and the
   text "Refreshing — showing the last complete evidence", capture a screenshot of that card immediately.

**Expected Result:**
- The captured card's body text reads: *"The dataset has changed since this evidence was generated, and
  the newer version is not complete yet. The forward-tested evidence below is the last complete version —
  evidence as of `<a real calendar date>`, generated `<a real timestamp>` — no partial or fabricated
  figures are shown in the meantime. Reload this page after the next ingest finishes to pick up the new
  version."*
- A real calendar date (e.g. "2026-07-22") — never an em dash, never blank — appears immediately before
  the word "generated".
- The evidence numbers below the banner are still fully populated — the banner sits ABOVE a populated
  section, never replacing it.
- Save the screenshot as
  `reports/qa/goal-ops-hardening-iter-17-evidence/TC-07-refreshing-banner-with-asof.png` — the exact
  filename the functional test plan already reserved for this still-open capture.
- **If the window can't be reached:** if roughly 8 minutes pass and the banner never appears, do not
  fabricate a capture. Document plainly which happened — "no backfill gap was available" or "the job
  completed without the state ever being observed mid-flight" — and note the attempt. This mirrors the
  phase spec's own accepted fallback pattern for TC-9's live-capture attempt: an honestly-reported miss is
  a legitimate outcome, a fabricated screenshot is not.

---

### UT-04 — Evidence section stays populated in the normal "ready" state (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest` (MAIN pair)

**Preconditions:**
- Main backend/frontend already running at `:8255`/`:3255`.
- Run this BEFORE submitting UT-03's backfill job for a clean "ready" baseline, or note the timing if
  UT-03's job happens to already be mid-flight (see Expected Result).

**Steps:**
1. Navigate to `http://localhost:3255/backtest`.
2. Scroll to the very bottom of the page, past the "Leadership cohorts" section.

**Expected Result:**
- The bottom of the page shows a populated evidence section (real per-horizon numbers) — NOT the
  "Backtest evidence not yet computed" empty-state card.
- Typically no banner appears above it at all (the plain `ready` case) — this is a PASS. If instead an
  amber "Refreshing — showing the last complete evidence" banner appears above still-populated numbers
  (e.g. because UT-03's backfill job happens to be mid-warm at this exact moment), that is ALSO a PASS —
  only an empty "not yet computed" card here is a FAIL, since the main app's latest date has real,
  previously-computed evidence and must never present as though it has none (the load-bearing B1 fix this
  iteration ships).

---

### UT-05 — Scorecard and leadership sections unaffected by this iteration's backend change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/backtest` (MAIN pair)

**Preconditions:**
- Main backend/frontend already running at `:8255`/`:3255`.

**Steps:**
1. Navigate to `http://localhost:3255/backtest`.
2. Locate the "Forward-test scorecard" table (below the "As-of scan summary" cards).
3. Locate the "Leadership cohorts" heading further down, with its "Top Sectors", "Top Themes", and
   "Ranked cohort" panels.

**Expected Result:**
- The "Forward-test scorecard" table shows one row per configured horizon (e.g. 1d/5d/10d/20d/60d), each
  with numeric or "—" cohort/excess-return values — not entirely blank, not an error card.
- "Top Sectors" and "Top Themes" each list ranked tickers with a score badge and a return figure (or the
  "No ranked … for this date" placeholder only if genuinely empty for this as-of).
- "Ranked cohort" shows a table of stocks with rank, ticker, setup, leadership badge, and forward-return
  columns populated.
- None of this iteration's backend changes (the new `evidence_asof` field, the widened fallback search)
  altered any figure in these three sections — they are driven by separate endpoints/fields
  (`scorecard`/`leadership_returns` on the same `/api/backtest` response, plus `/api/sectors`,
  `/api/themes`, `/api/stocks`) untouched this iteration.

---

### UT-06 — Empty-state copy reads factually and does not presume the user hasn't already acted (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/backtest` (**THROWAWAY pair — port 13255, NOT the main app**)

**Preconditions:**
- Same throwaway pair as UT-02, already running.

**Steps:**
1. Navigate to `http://127.0.0.1:13255/backtest`.
2. Scroll to the bottom and read the full "Backtest evidence not yet computed" card's description text.

**Expected Result:**
- The sentence states what is true right now ("No forward-tested evidence exists yet for this date") and
  what would resolve it ("Backfilling or fetching data that covers it will compute this evidence") without
  commanding the reader as though they haven't already tried — the old, removed "run an ingest" phrasing
  read that way even to a user who had already started one (audit F2).
- The sentence explicitly disclaims fabrication ("no numbers are fabricated in the meantime"), matching
  this project's calm, factual, never-hype tone (goal.md's Design Direction).
- The description reads as one clean statement, not a duplicated opening clause repeating the card's own
  title (audit F3).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/backtest` loads without errors | smoke | P1 | `/backtest` (main) |
| UT-02 | `not_yet_computed` empty state renders correctly | smoke | P1 | `/backtest` (throwaway :13255) |
| UT-03 | Live capture — corrected banner + `evidence_asof` | happy-path | P1 (time-boxed) | `/data` → `/backtest` (main) |
| UT-04 | Evidence section populated in normal "ready" state | regression | P1 | `/backtest` (main) |
| UT-05 | Scorecard/leadership sections unaffected | regression | P1 | `/backtest` (main) |
| UT-06 | Empty-state copy reads factually, non-presumptuously | ux | P2 | `/backtest` (throwaway :13255) |

**P1 tests must all pass for browser QA verdict to be PASS** — with the explicit exception that UT-03's
live capture may be documented as honestly missed (not fabricated) rather than forced, per its own
Expected Result clause; that documented outcome does not by itself fail the overall verdict, since the
underlying correctness is separately proven by 15/15 green backend unit tests.

**Coverage of phase requirements:**
- New disclosure field visible in the browser (`evidence_asof`, corrected copy): UT-03
- `not_yet_computed` reserved-for-true-fresh-install shape, live in a browser for the first time: UT-02
- Honest-empty-state-never-a-500/error-page concern: UT-02 (live HTTP 200 + graceful card, no crash)
- No regression to the pre-existing populated `/backtest` surfaces from this iteration's backend change:
  UT-04, UT-05
- Copy tone/clarity (audits F2/F3): UT-02, UT-06
- Deliberately NOT covered here (out of UI-test-designer scope / already covered elsewhere): the new
  cross-`asof_key` fallback logic itself (backend unit tests TC-1/TC-4/TC-5, already green), `evidence_asof`
  API/MCP parity (functional test plan TC-02), the disposable-DB BOOT action and the AG-10-class deep-basis
  latency re-measurement (both operator-only, TC-09's boot and TC-10 in the functional test plan), and the
  non-disruptive health poll (functional test plan TC-11).
