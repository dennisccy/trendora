# Phase goal-i_can_see_the_wealthy_future_forever-iter-22 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-05
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

All affected surfaces are on the existing **`/data` (Data Manager)** page — no new route or nav
entry was added. The new capabilities are: a **chunk X/N** progress badge, an **amber
"rate-limited — resumable"** job state with a **Resume** button + session-only key field, a
post-restart **"Resumable imports"** panel, a backfill-only **source-label fold**, and **API-key
redaction** in surfaced provider errors.

> **Environment note (not a defect):** the external providers reachable from this host are
> rate-limited (Yahoo 429) or key-gated (Stooq). A *successfully completed* multi-chunk live fetch
> cannot be demonstrated offline. The chunk badge, amber resumable state, Resume affordance, key
> field, and post-restart panel are all reachable via a real Yahoo 429 (or an injected scripted-429
> provider). Tests that depend on a live provider 429 are marked **[provider-dependent]**; if the
> provider returns `ok` instead, record SKIPPED (environment), not FAIL.

These UI tests do **not** duplicate the API/curl/pytest checks in the functional test plan
(`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-22-test-plan.md`, TC-01…TC-09, TC-16…18).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Data Manager page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running at http://localhost:3835, backend running on :8000
- Backend reachable (health badge cleared; `GET /_next/static/chunks/main-app.js` → 200 — i.e. a
  live `next dev`, not a clobbered `.next`; see MEMORY `browser-qa-dead-shell-next-cache`)

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (skeleton shimmer disappears)

**Expected Result:**
- The heading **"Data Manager"** is visible with its subtitle about growing the dataset on demand
- A **"Dataset coverage"** card shows metrics (Price history, Universe, Symbols, Trading days,
  Snapshot dates, Backfill gaps)
- A **"Start a fetch / backfill job"** form card and a **"Job progress"** card are visible side by side
- No **"Backend unavailable"** red error card, no blank screen, no console errors

---

### UT-02 — Backfill job runs end-to-end with no source label in header (happy path / regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm` + `JobProgressPanel`

**Preconditions:**
- `/data` loaded; "Dataset coverage" shows **Backfill gaps > 0** (Start/End date inputs prefill from
  the first gap). If gaps = 0, this test is N/A for this environment — record SKIPPED.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. In the "Start a fetch / backfill job" card, leave the prefilled **Start date** / **End date**
3. In the **"Job kind"** dropdown, confirm **"Backfill snapshots"** is selected
4. Click the **"Start"** button
5. Watch the "Job progress" card on the right

**Expected Result:**
- The Start button shows a spinner then reads **"Job running…"** while the job runs
- The "Job progress" card status badge progresses to **`ok`** (green) on completion
- The **"Snapshots backfilled"** row shows `N/N dates` with a full progress bar; "N snapshots ·
  M forward returns inserted" appears
- **No "Import source" line** appears in the Job progress card header hint (the header reads
  `backfill job · <start> → <end>` with **no `<source> ·` segment** — Finding #2 fold)
- The completed backfill appears as a new row in the **"Run history"** table at the bottom

---

### UT-03 — Source picker + session key field reveal for a needs-key fetch (happy path / UX)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — `JobForm`

**Preconditions:**
- `/data` loaded; the source catalog contains at least one **needs-key** source whose key is **not**
  in the environment (shown as "needs key" in the picker). If every source is "available", skip the
  key-field assertion (step 5) and record it SKIPPED (environment).

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. In the **"Job kind"** dropdown, select **"Fetch EOD prices"**
3. Confirm an **"Import source"** dropdown now appears (it is hidden for backfill-only jobs)
4. In the **"Import source"** dropdown, select a source whose option text ends in **"· needs key"**
5. Observe the area below the form row

**Expected Result:**
- After step 2, the **"Import source"** dropdown becomes visible and a **source-availability** line
  (`data-testid="source-availability"`) shows the source label, an amber **"needs key"**, and the reason
- After step 4 (needs-key, no env key), a masked field labeled **"Session API key for &lt;source
  label&gt;"** appears with a key icon; the input is **`type="password"`** with helper text
  "Held in memory for this run only — never written to disk, the database, the run log, or a cookie,
  and never echoed back."
- Selecting an **"· available"** source instead hides the key field (no paste needed)

---

### UT-04 — Chunk X/N progress badge renders and advances on a chunked fetch (happy path) [provider-dependent]

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — chunk badge (`data-testid="chunk-progress"`)

**Preconditions:**
- `/data` loaded; a fetch import spanning multiple chunks (multi-symbol and/or multi-date-window so
  `chunk_total > 1`). Requires a reachable provider OR an injected scripted provider.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Select **"Job kind" → "Fetch EOD prices"**, pick an available source, set a multi-day date range
3. Click **"Start"**
4. Watch the "Job progress" card status area while the job runs

**Expected Result:**
- A second badge **"chunk X/N"** (`data-testid="chunk-progress"`) renders beside the status badge,
  in monospace/tabular figures, only when the job is chunked (`chunk_total > 0`)
- The **X advances** (e.g. `chunk 1/4` → `chunk 2/4` …) as chunks complete; N stays fixed
- The "Symbols fetched" progress bar and "new price bars" count continue to update alongside it
- The chunk badge is **absent** for a single-chunk job (e.g. a tiny one-symbol/one-day fetch)

---

### UT-05 — Rate-limit pause shows amber "rate-limited — resumable" state, not red failed (error / happy path) [provider-dependent]

**Type:** error
**Priority:** P1
**Surface:** `/data` — status badge + amber callout (`data-testid="resumable-state"`)

**Preconditions:**
- A fetch driven to a provider **429** (real Yahoo 429, or an injected scripted-429 provider) that
  exhausts the configured retries.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Start a fetch against a provider that rate-limits (429)
3. Watch the "Job progress" card transition: running → (retries) → paused

**Expected Result:**
- The status badge reads **"rate-limited — resumable"** in **amber** (`--warn`) — it is **NOT** the
  red `failed`/`partial` state
- An **amber callout** (`data-testid="resumable-state"`, amber border) appears stating
  **"Rate-limited — paused at chunk X/N. Progress is saved; resume to continue from the next
  un-fetched chunk (no data is re-fetched or duplicated)."**
- The callout shows symbol counts: **"&lt;n&gt; done · &lt;m&gt; remaining"** (and "&lt;k&gt; failed"
  only if k > 0)
- A **"Resume"** button (`data-testid="resume-button"`, amber) is present inside the callout

---

### UT-06 — Resume button on the live job card re-pulls the import (happy path) [provider-dependent]

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Resume button (`data-testid="resume-button"`) on the job card

**Preconditions:**
- UT-05 reached: the live "Job progress" card is showing the amber resumable state with a Resume
  button. If the source is needs-key with no env key, have a dummy key string ready.

**Steps:**
1. With the amber resumable job card showing, if a **"Session API key to resume &lt;import_id&gt;"**
   field is present, type a dummy key (e.g. `RESUMEKEY999`) into it
2. Click the **"Resume"** button inside the amber callout
3. Observe the Resume button and the job card

**Expected Result:**
- The Resume button shows a spinner while the POST is in flight
- The "Job progress" card re-enters a **running**/progress state for the same import (polling
  resumes); the chunk badge shows progress at or after the prior pause point (it does **not** reset
  to `chunk 0/N` and does **not** re-fetch already-saved chunks)
- If a key field was present, it is **cleared** immediately after clicking Resume (empty input)
- No red crash/error appears in place of the resume action

---

### UT-07 — Resumable imports panel survives a backend restart (happy path / regression) [provider-dependent]

**Type:** happy-path
**Priority:** P1
**Surface:** `/data` — Resumable imports panel (`data-testid="resumable-imports"`)

**Preconditions:**
- At least one import is in the **resumable** state (a durable `ImportCheckpoint` exists). Backend
  has been **restarted by port** (MEMORY `dev-server-cleanup-by-port`) so the in-memory job is gone
  but the checkpoint persists.

**Steps:**
1. Confirm a resumable import exists (UT-05), then restart the backend by its port
2. Navigate to (or hard-reload) `http://localhost:3835/data`
3. Scroll to below the "Job progress" card

**Expected Result:**
- A **"Resumable imports"** card (`data-testid="resumable-imports"`) is visible with hint text about
  "paused mid-run — progress is saved to the database and survives a backend restart"
- Each row shows: an amber **"chunk X/N"** badge, the **source label**, the **date range**
  (`start → end`), and a counts line **"&lt;n&gt; done · &lt;m&gt; remaining · &lt;b&gt; bars so far"**
  (plus "&lt;k&gt; failed" if k > 0)
- Each row has its own **"Resume"** button (`data-testid="resume-button"`)

---

### UT-08 — Resumable imports panel is hidden when nothing is paused (UX / regression)

**Type:** ux
**Priority:** P2
**Surface:** `/data` — `ResumableImportsPanel`

**Preconditions:**
- No import is in the resumable state (fresh state, or all paused imports have been resumed to
  completion).

**Steps:**
1. Navigate to `http://localhost:3835/data` with no paused imports present
2. Scroll through the whole page between the "Job progress" card and the "Run history" table

**Expected Result:**
- **No "Resumable imports" card** appears anywhere on the page (the panel renders nothing for an
  empty list — no empty/placeholder clutter)
- The "Run history" table still renders below where the panel would be

---

### UT-09 — Resume from the post-restart panel picks the import up as a live job (happy path) [provider-dependent]

**Type:** happy-path
**Priority:** P2
**Surface:** `/data` — Resume button on a `ResumableImportsPanel` row

**Preconditions:**
- UT-07 reached: the "Resumable imports" panel lists at least one paused import after a restart.

**Steps:**
1. On a "Resumable imports" row, if a **"Session API key to resume &lt;import_id&gt;"** masked field
   is shown, type a dummy key
2. Click the **"Resume"** button on that row
3. Observe the "Job progress" card (above) and the panel row

**Expected Result:**
- The import is pulled into the **"Job progress"** card as a live (running/progressing) job
- On completion, the import **drops off** the "Resumable imports" panel (the list reloads from
  `GET /api/data`); if it was the last row, the whole panel disappears
- The key field (if present) is cleared right after submit

---

### UT-10 — Resume rejects an invalid/expired import gracefully (error)

**Type:** error
**Priority:** P2
**Surface:** `/data` — `ResumeControl`

**Preconditions:**
- A resumable Resume button is present, but the underlying import is no longer resumable (e.g. it
  already completed in another tab, or the backend returns 404/409 for it). This can be observed if
  a Resume is clicked twice in quick succession, or after the import finished elsewhere.

**Steps:**
1. With a Resume button visible, click **"Resume"**
2. If the backend rejects it (404 unknown / 409 not-resumable / 400 missing key), observe the control

**Expected Result:**
- An inline **red error message** (`role="alert"`) appears next to the Resume button (e.g. "Could
  not resume the import." or the backend's message)
- The page does **not** crash or go blank; the rest of `/data` remains interactive
- For a **needs-key** source resumed with an **empty** key, the backend 400 surfaces as the inline
  error (the key field is required for that source)

---

### UT-11 — Surfaced provider error contains no API key or query string (error / security)

**Type:** error
**Priority:** P1
**Surface:** `/data` — job-card error list + Run history "Summary" column

**Preconditions:**
- A fetch on a **key-gated** source with a **pasted sentinel key** (e.g. `SENupKEY123`) is driven to
  a failure/429 so the error text is surfaced on the job card and recorded in run history.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Select **"Fetch EOD prices"**, pick a needs-key source, paste sentinel key `SENupKEY123` into the
   **"Session API key"** field, set a date range, click **"Start"**
3. Wait for the explicit error/resumable/failed job-card state
4. Read the job-card error list (the "N error(s) (no data fabricated)" box)
5. Read the matching row's **"Summary"** column in the "Run history" table

**Expected Result:**
- The job-card error list and the run-history Summary show an explicit provider error message
- The displayed text contains **neither** the sentinel key `SENupKEY123` **nor** any
  `?token=`/`?apikey=` query string (the URL query is stripped before display — security fix gating
  J-33; MEMORY `httpx-error-leaks-url-query-key`)
- No fabricated price/bar count appears for the failed symbols

---

### UT-12 — Exactly one date `<select>` app-wide; import dates stay job-parameter inputs (regression — J-18)

**Type:** regression
**Priority:** P1
**Surface:** `/data` (+ spot-check `/stocks`, `/backtest`, `/research`)

**Preconditions:**
- Frontend up; global header as-of switcher present.

**Steps:**
1. Navigate to `http://localhost:3835/data`; inspect the JobForm and any chunk/Resume controls
2. Spot-check `http://localhost:3835/stocks`, `/backtest`, `/research` for the global as-of switcher

**Expected Result:**
- The Job form's **Start date** / **End date** inputs are `type="date"` **job-parameter** inputs —
  they do **not** change the global as-of viewing date
- The new chunk badge, amber callout, Resume control, and Resumable-imports panel introduce **no new
  date `<select>`**
- Exactly **one** date `<select>` exists app-wide: the global header as-of switcher (MEMORY
  `j18-asof-on-stocks-fetch-is-correct`)

---

### UT-13 — Coverage panel + Run history still render after this phase (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data` — `CoveragePanel`, `RunHistoryPanel`

**Preconditions:**
- `/data` loaded with at least one prior run in history (or the empty-state if none).

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Inspect the "Dataset coverage" card and the "Run history" table

**Expected Result:**
- "Dataset coverage" shows all six metrics; "Backfill gaps" is amber when > 0, green when 0, with the
  gap-range line
- "Run history" shows prior runs with Started / Kind / Range / Status / Symbols ok-failed / Snapshots
  / Summary columns — OR the **"No fetch / backfill runs yet"** empty state if there are none
- Neither panel regressed (no missing columns, no console errors) after the iter-22 changes

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Data Manager page loads | smoke | P1 | `/data` |
| UT-02 | Backfill runs; no source label in header | happy-path | P1 | `/data` |
| UT-03 | Source picker + session key reveal | happy-path | P1 | `/data` |
| UT-04 | Chunk X/N badge advances | happy-path | P1 | `/data` |
| UT-05 | Amber rate-limited resumable state | error | P1 | `/data` |
| UT-06 | Resume on live job card | happy-path | P1 | `/data` |
| UT-07 | Resumable-imports panel survives restart | happy-path | P1 | `/data` |
| UT-08 | Panel hidden when nothing paused | ux | P2 | `/data` |
| UT-09 | Resume from panel row | happy-path | P2 | `/data` |
| UT-10 | Resume rejection handled inline | error | P2 | `/data` |
| UT-11 | Provider error has no key/query string | error | P1 | `/data` |
| UT-12 | One date select app-wide (J-18) | regression | P1 | `/data`,`/stocks`,`/backtest`,`/research` |
| UT-13 | Coverage + Run history still render | regression | P2 | `/data` |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-11, UT-12) must all pass for the
browser QA verdict to be PASS.** Tests marked **[provider-dependent]** (UT-04…UT-07, UT-09, UT-11)
may be recorded SKIPPED (environment) — not FAIL — if no real or injected provider 429 is drivable;
in that case prove the machinery via the functional/API plan (TC-05/TC-06/TC-10…TC-13).
