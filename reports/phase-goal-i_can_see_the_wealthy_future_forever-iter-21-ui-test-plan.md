# Phase goal-i_can_see_the_wealthy_future_forever-iter-21 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21 (J-33 — Import source picker)
**Date:** 2026-06-05
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- These are user-visible browser tests only. API/artifact coverage lives in the functional test plan (TC-01..TC-14) and is not duplicated here. -->

> **Operator note (applies to every step that selects a value in the "Import source" or "Job kind" dropdown):**
> The Chrome MCP `select` action does NOT fire React's `onChange` on this frontend. To change a `<select>`, set the value with the native value setter and dispatch a bubbling `change` event, then assert against the **live DOM** (not an `await_text` snapshot). See MEMORY `react-controlled-select-needs-native-setter`. A human operator using a real mouse/keyboard is unaffected — this caveat is for automated runs.

---

### UT-01 — Data Manager page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend running (the page reads `GET /api/data`)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (the loading skeleton disappears)

**Expected Result:**
- The heading "Data Manager" is visible
- The "Dataset coverage" card is visible with metrics (Price history, Universe, Symbols, Trading days, Snapshot dates, Backfill gaps)
- The "Start a fetch / backfill job" card is visible
- The "Job progress" card is visible reading "No job has been started this session."
- No "Backend unavailable" red error card is shown
- No blank screen and no uncaught console errors

---

### UT-02 — Import source dropdown appears only for fetch-type jobs (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm` Import source `<select>` (`aria-label="Import source"`)

**Preconditions:**
- On `http://localhost:3835/data`, page loaded (UT-01 passed)
- Default "Job kind" value is "Backfill snapshots"

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. In the "Job kind" dropdown (`aria-label="Job kind"`), confirm the current value is "Backfill snapshots"
3. Observe that NO "Import source" dropdown is present in the form
4. Set the "Job kind" dropdown to "Fetch EOD prices" (value `fetch`) using the native-setter + bubbling-`change` pattern
5. Observe the form

**Expected Result:**
- While Job kind = "Backfill snapshots": there is NO element with `aria-label="Import source"` and NO `data-testid="source-availability"` line
- After Job kind = "Fetch EOD prices": a dropdown with `aria-label="Import source"` appears between "Job kind" and the "Start" button
- The "Import source" dropdown lists exactly these options, each suffixed " · available" or " · needs key": **Yahoo · available**, **Stooq · needs key**, **Tiingo · needs key**, **Finnhub · needs key**, **Alpha Vantage · needs key** (order and labels come from the config catalog; Yahoo is the default-selected first entry)

---

### UT-03 — Import source dropdown also appears for "Fetch + backfill" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm` Import source visibility toggle

**Preconditions:**
- On `http://localhost:3835/data`, page loaded

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Set the "Job kind" dropdown to "Fetch + backfill" (value `both`) using the native-setter + bubbling-`change` pattern

**Expected Result:**
- The "Import source" dropdown (`aria-label="Import source"`) is visible
- The `data-testid="source-availability"` line is visible below the form row

---

### UT-04 — Availability line reflects the selected source (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — availability line (`data-testid="source-availability"`)

**Preconditions:**
- On `http://localhost:3835/data`, Job kind set to "Fetch EOD prices"
- No `TIINGO_API_KEY` env var is set in the backend process (default in this environment)

**Steps:**
1. Navigate to `http://localhost:3835/data` and set Job kind to "Fetch EOD prices"
2. Ensure "Import source" is set to "Yahoo · available" (the default) and read the `data-testid="source-availability"` line
3. Set "Import source" to "Tiingo · needs key" using the native-setter + bubbling-`change` pattern
4. Read the `data-testid="source-availability"` line again

**Expected Result:**
- With Yahoo selected: the line begins "Yahoo: ", shows the word "available" in the positive (green) color, and ends with a reason (e.g. "no API key required")
- With Tiingo selected: the line begins "Tiingo: ", shows the words "needs key" in the warn (amber) color, and ends with a reason naming the env var, e.g. "set $TIINGO_API_KEY or paste a session key"
- The line text changes when the selected source changes (it is not a static string)

---

### UT-05 — Session API key field appears only for a needs-key source with no env key (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Session API key field (`type="password"`, `aria-label="Session API key"`)

**Preconditions:**
- On `http://localhost:3835/data`, Job kind set to "Fetch EOD prices"
- No env key set for Tiingo in the backend process

**Steps:**
1. Navigate to `http://localhost:3835/data` and set Job kind to "Fetch EOD prices"
2. Confirm "Import source" is "Yahoo · available" and observe the form
3. Set "Import source" to "Tiingo · needs key" using the native-setter + bubbling-`change` pattern
4. Observe the form
5. Set "Import source" back to "Yahoo · available"
6. Observe the form

**Expected Result:**
- With Yahoo (available) selected: NO field with `aria-label="Session API key"` is present
- With Tiingo (needs key, no env key) selected: a masked field with `type="password"` and `aria-label="Session API key"` appears, preceded by a key icon and the label text "Session API key for Tiingo"
- A caption below the field reads: "Held in memory for this run only — never written to disk, the database, the run log, or a cookie, and never echoed back."
- The field placeholder reads "or set $TIINGO_API_KEY"
- After switching back to Yahoo: the password field disappears again

---

### UT-06 — Session key field is masked and never pre-filled (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — Session API key field

**Preconditions:**
- On `http://localhost:3835/data`, Job kind = "Fetch EOD prices", Import source = "Tiingo · needs key" (key field visible)

**Steps:**
1. With the Session API key field visible, confirm its initial value is empty
2. Type `test-secret-123` into the "Session API key" field
3. Visually inspect the field

**Expected Result:**
- The field is initially empty (not pre-filled from any API response)
- After typing, the characters render as dots/masked (because `type="password"`), not as plain text `test-secret-123`
- No value appears that was sourced from the server (the server never returns a key)

---

### UT-07 — Needs-key source with blank key is rejected up front (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — `JobForm` start with needs-key source, no key

**Preconditions:**
- On `http://localhost:3835/data`, Job kind = "Fetch EOD prices"
- A valid Start date and End date are filled (the form pre-fills these from coverage gaps; if blank, type `2024-01-01` into "Job start date" and `2024-01-05` into "Job end date")
- No env key set for Tiingo

**Steps:**
1. Set "Import source" to "Tiingo · needs key" using the native-setter + bubbling-`change` pattern
2. Leave the "Session API key" field blank
3. Click the "Start" button

**Expected Result:**
- An inline error with `role="alert"` appears at the bottom of the form, prefixed by a warning triangle icon
- The error text explains a key is required for that source (it names the source/env var, e.g. mentions `TIINGO_API_KEY` or "requires a key")
- The "Job progress" card does NOT change to a running job (no new job starts)
- The typed/blank key is not echoed anywhere on screen

---

### UT-08 — Fetch against a walled provider surfaces an explicit error, fabricates nothing (error)

**Type:** error
**Priority:** P1
**Surface:** `/data` — `JobProgressPanel` after a failing fetch

**Preconditions:**
- On `http://localhost:3835/data`, Job kind = "Fetch EOD prices"
- Import source = "Yahoo · available" (Yahoo rate-limits this IP — fetches return an unavailable/error state; see MEMORY `data-provider-access-constraints`)
- Start date and End date are filled (e.g. `2024-01-01` → `2024-01-05`)

**Steps:**
1. Confirm Import source is "Yahoo · available"
2. Click the "Start" button
3. Wait for the "Job progress" card to leave the "running" state (poll completes)

**Expected Result:**
- The "Job progress" card header hint reads `fetch job · yahoo · 2024-01-01 → 2024-01-05` (the chosen source id `yahoo` is echoed in the header)
- The job status badge ends in "failed" or "partial" (red/amber), NOT "ok"
- An error box appears reading "N error(s) (no data fabricated)" followed by a list of error lines
- The "Symbols fetched" counter shows failures (e.g. `… (0 ok, N failed)`) and "0 new price bars" — no invented bars
- No API key string appears anywhere in the job card

---

### UT-09 — Job progress header echoes the chosen source id, never a key (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `JobProgressPanel` header hint

**Preconditions:**
- A fetch job has been started with Yahoo selected (continues from UT-08)

**Steps:**
1. After starting a fetch with Yahoo selected, read the "Job progress" card header hint line (the small text under "Job progress")

**Expected Result:**
- The header hint contains the source id `yahoo` between the kind and the date range, e.g. `fetch job · yahoo · 2024-01-01 → 2024-01-05`
- For a backfill-only job (no source), the header hint omits the source segment, e.g. `backfill job · <start> → <end>` (no provider id, no key)

---

### UT-10 — Backfill-only job hides source/key controls and still runs (regression — J-17)

**Type:** regression
**Priority:** P1
**Surface:** `/data` — `JobForm` with Job kind = "Backfill snapshots"

**Preconditions:**
- On `http://localhost:3835/data`, page loaded
- Coverage shows ≥1 backfill gap (the form pre-fills Start/End from the first gaps); if Start/End are blank, type `2024-01-01` and `2024-01-05`

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Confirm "Job kind" is "Backfill snapshots"
3. Confirm NO "Import source" dropdown and NO "Session API key" field are present
4. Click the "Start" button
5. Wait for the "Job progress" card to leave "running"

**Expected Result:**
- No Import source dropdown and no Session API key field are shown for the backfill kind
- The job starts; the "Job progress" card shows a "Snapshots backfilled" counter and progresses to a terminal status
- The header hint reads `backfill job · <start> → <end>` with NO source segment
- The deterministic/offline backfill path completes as in prior iterations (no new obstacle introduced by the source picker)

---

### UT-11 — Default source is preselected so an unchanged fetch behaves like J-17 (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `JobForm` default source

**Preconditions:**
- On `http://localhost:3835/data`, Job kind = "Fetch EOD prices"

**Steps:**
1. Navigate to `http://localhost:3835/data` and set Job kind to "Fetch EOD prices"
2. Without changing the "Import source" dropdown, read its selected value

**Expected Result:**
- The "Import source" dropdown is pre-selected to the first catalog entry, "Yahoo · available" (the config `default_source`), with no manual selection required
- Starting a fetch without touching the dropdown runs against `yahoo` (verified via the header hint in UT-09) — preserving the prior single-provider fetch behavior

---

### UT-12 — Page subtitle wording fix (regression / ux)

**Type:** regression
**Priority:** P3
**Surface:** `/data` — `DataManagerPage` subtitle

**Preconditions:**
- On `http://localhost:3835/data`, page loaded

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Read the grey subtitle directly under the "Data Manager" heading

**Expected Result:**
- The subtitle ends with "…new snapshot dates become selectable in the global as-of switcher and grow the **Backtest** evidence."
- The phrase "System Health evidence" does NOT appear anywhere in the subtitle

---

### UT-13 — Exactly one date `<select>` app-wide; J-18 not regressed (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/data` (app-wide) — date controls

**Preconditions:**
- On `http://localhost:3835/data`, Job kind = "Fetch EOD prices" (so the new source/key controls are present)

**Steps:**
1. Navigate to `http://localhost:3835/data` and set Job kind to "Fetch EOD prices"
2. Count every `<select>` element on the page that is a date/as-of viewing control
3. Inspect the "Job start date" and "Job end date" inputs
4. Inspect the "Import source" and "Job kind" controls

**Expected Result:**
- Exactly ONE date `<select>` exists app-wide: the global header as-of (viewing date) switcher
- "Job start date" and "Job end date" are `type="date"` `<input>` job-parameter fields — NOT viewing-date `<select>`s
- The "Import source" and "Job kind" `<select>`s are NOT date controls and add no date state
- No second viewing-date selector was introduced by the J-33 source/key controls

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager loads | smoke | P1 | `/data` |
| UT-02 | Import source shows for fetch only | happy-path | P1 | `/data` Import source select |
| UT-03 | Import source shows for "Fetch + backfill" | happy-path | P1 | `/data` visibility toggle |
| UT-04 | Availability line reflects source | happy-path | P1 | `/data` source-availability |
| UT-05 | Session key field appears for needs-key | happy-path | P1 | `/data` Session API key |
| UT-06 | Key masked, never pre-filled | validation | P2 | `/data` Session API key |
| UT-07 | Needs-key blank key rejected up front | validation | P2 | `/data` JobForm |
| UT-08 | Walled fetch → explicit error, no fabrication | error | P1 | `/data` JobProgressPanel |
| UT-09 | Header echoes source id, never key | ux | P2 | `/data` JobProgressPanel header |
| UT-10 | Backfill hides source/key, still runs | regression | P1 | `/data` JobForm backfill |
| UT-11 | Default source preselected (J-17) | regression | P2 | `/data` default source |
| UT-12 | Subtitle wording fix | regression | P3 | `/data` subtitle |
| UT-13 | Exactly one date select (J-18) | regression | P1 | `/data` app-wide |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-08, UT-10, UT-13) must all pass for the browser QA verdict to be PASS.**

> **Environment caveat:** A *successful* live fetch is not autonomously reachable here (Yahoo rate-limits this IP; the other live providers are key-gated). UT-08 therefore validates the honest error/unavailable path. If the entire `/data` page renders as a dead un-hydrated shell ("Checking backend…" / 404 on `_next/static/chunks/main-app.js`), record the browser tests as SKIPPED (not FAIL) — the dev server's `.next` was clobbered by a prod build (MEMORY `browser-qa-dead-shell-next-cache`).
