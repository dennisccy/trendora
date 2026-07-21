# Phase goal-ops-hardening-iter-7 — UI Test Plan

**Phase:** goal-ops-hardening-iter-7
**Date:** 2026-07-21
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255 (prod-mode frontend; pair with prod-mode backend at
http://localhost:8255 — start both via `scripts/start-backend.sh` / `scripts/start-frontend.sh`, NOT
`dev.sh`, so timing measurements are meaningful)

---

## Context

This iteration ships **zero frontend file changes**. The fix (`_refresh_ingest_aggregates` in
`app.engine.data_manager`) moves WHEN one background computation (`drawdown_expectations`, the
`/evidence` page's "expected drawdown" panels) runs — from "the first time someone opens `/evidence`
after an ingest" to "the moment the ingest job's own finalize step completes." Two existing, unmodified
frontend surfaces are affected purely through data they already know how to render:

1. `/evidence` — same payload shape, same values, only faster on the FIRST view after an ingest.
2. `/data` (Data Manager) — the existing generic `aggregates_refreshed` list renderer (used in the live
   Job progress panel, the persisted-run fallback card, and the Run History table) can now show one more
   phrase, "drawdown expectations," picked up automatically with no frontend code change.

Every test case below verifies these two surfaces plus their surrounding pre-existing (untouched)
elements — there is no new page, button, form, or nav entry to test.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Evidence page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Backend running in prod mode (`scripts/start-backend.sh`) at `http://localhost:8255`
- Frontend running in prod mode (`scripts/start-frontend.sh`) at `http://localhost:3255`
- No fresh ingest job is required for this test — existing seed/dev data is sufficient

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Wait for the loading skeleton to disappear (up to 5 seconds)

**Expected Result:**
- The page heading "Evidence" and its subtitle ("The certified-claims ledger — the single source of
  proven-ness...") are visible
- Either the claim list (`data-testid="evidence-claim-list"`, one Card per certified claim) is visible,
  OR — if zero certified claims exist — the empty-state Card (`data-testid="evidence-empty"`) with heading
  "No certified claims yet" is visible
- The red error Card with the text "Backend unavailable" is NOT shown
- No error appears in the browser console

---

### UT-02 — First `/evidence` view after a fresh ingest job loads fast with expectations panels intact (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` → `/evidence`

This is the core test for this iteration's fix: confirming the ingest-time warm actually makes the FIRST
`/evidence` view fast, and that the Data Manager's "Refreshed:" text picks up the new category.

**Preconditions:**
- Backend + frontend running in prod mode as in UT-01
- At least one certified claim exists in the evidence ledger (already true on the seed/dev dataset)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, type `2015-06-18` into the "Start date" field
3. Type `2015-06-18` into the "End date" field
4. Leave the "Job kind" dropdown at its default value "Backfill snapshots"
5. Click the "Start" button
6. Watch the Job progress panel's status badge until it stops showing the spinning icon and "Job
   running…" text (job has completed) — this can take from a few seconds up to roughly a minute
7. Once complete, read the small gray text line below the job's breakdown counts that begins "Refreshed:"
   (`data-testid="aggregates-refreshed"`)
8. Immediately open a new browser tab and navigate to `http://localhost:3255/evidence`
9. Note the time between navigation and the claim rows (`data-testid="evidence-claim-list"`) with their
   "Historical drawdown & dry-spell expectations" sub-panels (`data-testid="evidence-expectations-panel"`)
   fully rendering

**Expected Result:**
- The "Refreshed:" line from step 7 includes the phrase "drawdown expectations" among its
  comma-separated items (alongside pre-existing items such as "latest snapshot," "coverage," etc.)
- The `/evidence` tab from step 8-9 fully renders its claim rows and expectations tables within
  approximately 3 seconds of navigation — no extended spinner, no blank panel where a table should be
- Reloading `/evidence` again (F5) shows identical panel content — confirms the fast first view did not
  produce a different or truncated result than a subsequent warm view

---

### UT-03 — Persisted-run fallback view also shows "drawdown expectations" (regression / new-value pass-through)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

Confirms the SAME `aggregates_refreshed` value renders correctly through the Data Manager's second
rendering path — the persisted-run card shown when no job has started in the current browser session.

**Preconditions:**
- The backfill job from UT-02 has completed
- A fresh browser session/tab with no job started this session (use a new private/incognito window, or a
  different browser profile)

**Steps:**
1. Open a new private/incognito browser window
2. Navigate to `http://localhost:3255/data`
3. Locate the "Job progress" card (the panel titled "Job progress" — this is the persisted-run fallback,
   since no job was started in this fresh session)
4. Read its "Refreshed:" line (`data-testid="aggregates-refreshed"`)

**Expected Result:**
- The "Job progress" card is visible and shows the most recent run's status badge and message
- Its "Refreshed:" line includes "drawdown expectations" in its comma-separated list, matching what was
  shown live in UT-02

---

### UT-04 — Run History table row shows "drawdown expectations" for the qualifying run (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

Confirms the SAME field renders correctly through the Data Manager's third rendering path — the Run
History table, one row per past run.

**Preconditions:**
- The backfill job from UT-02 has completed and appears in Run History

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll down to the table titled "Run history"
3. In the "Range" column, locate the row showing "2015-06-18 → 2015-06-18" (the date used in UT-02)
4. Read the small gray text beneath the number in that row's "Snapshots" column

**Expected Result:**
- The row for the UT-02 job is present in the table
- The text beneath its Snapshots count begins "Refreshed:" and includes "drawdown expectations" in its
  comma-separated list
- Every other category that run also refreshed (e.g. "latest snapshot," "coverage," "membership
  timeline," "market phase," "forward aggregates," "research hot keys") is still present in that same
  list — nothing pre-existing was removed or reordered by this change

---

### UT-05 — A claim with no resolvable expectations renders cleanly, never a crash or fabricated panel (error / resilience)

**Type:** error
**Priority:** P2
**Surface:** `/evidence`

**Preconditions:**
- Backend + frontend running
- This test is exploratory: whether any currently-certified claim has an unresolvable cohort (and
  therefore no expectations panel) depends on the live dataset's contents at test time. If every claim
  currently has a populated panel, mark this test "not exercised this run" rather than forcing a failure.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Visually scan every claim row (`data-testid="evidence-claim-row"`) in the list
3. For any row that does NOT contain a "Historical drawdown & dry-spell expectations" section
   (`data-testid="evidence-expectations-panel"` absent for that row), check that the row's other fields
   still render fully: verdict badge, Hypothesis, Out-of-sample verdict, Control comparison (vs SPY),
   Registration date, Forward-walk score-to-date

**Expected Result:**
- No claim row shows a broken/blank box, a red error boundary, or any placeholder text where the
  expectations panel would be — a claim without one simply omits that section entirely
- Every other field on that same row renders normally with real or explicit "—" values (never blank)
- No error appears in the browser console for any row

---

### UT-06 — Existing claim-row fields are byte-identical before and after this iteration's timing change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

Directly verifies the anti-goal-3 concern this iteration's spec calls out: the fix must change WHEN a
value is computed, never WHAT value is shown.

**Preconditions:**
- At least one certified claim exists

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. On the first claim row shown, read and note the exact text of: the verdict badge (e.g. "PASS"),
   "Hypothesis," "Out-of-sample verdict," "Control comparison (vs SPY)," "Registration date," and
   "Forward-walk score-to-date"
3. Refresh the page (press F5)
4. Re-read the same fields on the same row (matched by its position/title)

**Expected Result:**
- All six values noted in step 2 are identical to the values read in step 4 — the refresh does not change
  any figure
- If an "Historical drawdown & dry-spell expectations" table was visible in step 2, its numeric contents
  (Max-DD depth, Underwater, Time to recover, Longest losing streak per phase row) are identical after the
  refresh in step 4

---

### UT-07 — Expectations panel content is clear and self-explanatory (UX)

**Type:** ux
**Priority:** P3
**Surface:** `/evidence`

**Preconditions:**
- At least one claim with a populated expectations panel exists (confirm via UT-01/UT-02 first)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Locate a claim row containing a "Historical drawdown & dry-spell expectations" section
   (`data-testid="evidence-expectations-panel"`)
3. Read the section's heading and the sentence directly beneath it
4. Read the table's column headers

**Expected Result:**
- The heading reads "Historical drawdown & dry-spell expectations (N-day hold)" with a real integer
  substituted for N (e.g. "20-day hold")
- The sentence beneath it reads "What following this cohort's methodology has historically felt like, by
  market phase at entry — descriptive history only, never a forecast or a promise."
- The table's column headers read exactly: "Phase," "Max-DD depth," "Underwater," "Time to recover,"
  "Longest losing streak"
- A method-note line (`data-testid="evidence-expectations-method-note"`) and a survivorship-bias
  disclosure line (`data-testid="evidence-expectations-survivorship"`) are both visible below the table,
  each containing real (non-empty) explanatory text

---

### UT-08 — Data Manager job form still renders and functions (smoke of the untouched form)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Backend + frontend running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Confirm the panel titled "Start a fetch / backfill job" is visible
3. Confirm it contains a "Start date" field, an "End date" field, a "Job kind" dropdown (default option
   "Backfill snapshots"), and a "Start" button
4. Open the "Job kind" dropdown and confirm it also offers "Fetch EOD prices" and "Fetch + backfill"

**Expected Result:**
- All four elements from step 3 are present and visible
- The dropdown from step 4 shows exactly three options: "Backfill snapshots," "Fetch EOD prices," "Fetch
  + backfill"
- No error appears in the browser console

---

### UT-09 — Job form blocks starting a job with an incomplete date range (validation of the pre-existing guard)

**Type:** validation
**Priority:** P3
**Surface:** `/data`

This form was not touched this iteration; this test confirms the pre-existing validation guard that UT-02
relies on is still intact.

**Preconditions:**
- Backend + frontend running
- Page freshly loaded (no dates typed yet)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Leave the "Start date" field empty
3. Type `2020-01-01` into the "End date" field
4. Observe the "Start" button's appearance and try clicking it

**Expected Result:**
- The "Start" button appears visually dimmed/disabled (reduced opacity, not-allowed cursor) and clicking
  it does nothing
- No new row appears in the "Run history" table
- The Job progress panel does not change state

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Evidence page loads without errors | smoke | P1 | `/evidence` |
| UT-02 | First `/evidence` view after ingest is fast, Refreshed line updates | happy-path | P1 | `/data` → `/evidence` |
| UT-03 | Persisted-run fallback card shows new Refreshed value | regression | P2 | `/data` |
| UT-04 | Run History row shows new Refreshed value | regression | P2 | `/data` |
| UT-05 | Unresolvable claim renders cleanly, no crash | error | P2 | `/evidence` |
| UT-06 | Claim-row values byte-identical across refresh | regression | P1 | `/evidence` |
| UT-07 | Expectations panel is clear and self-explanatory | ux | P3 | `/evidence` |
| UT-08 | Data Manager job form still renders and functions | smoke | P1 | `/data` |
| UT-09 | Job form still blocks incomplete date range | validation | P3 | `/data` |

**P1 tests (UT-01, UT-02, UT-06, UT-08) must all pass for browser QA verdict to be PASS.**
