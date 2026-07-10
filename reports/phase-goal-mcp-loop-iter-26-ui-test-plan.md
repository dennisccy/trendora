# Phase goal-mcp-loop-iter-26 — UI Test Plan

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-10
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255

---

## Context for the tester

This iteration shipped **zero frontend source changes**. Every route, label, and layout below is
expected to look and behave EXACTLY as it did before this iteration. The only thing that should be
different is **speed**: Backfill/Fetch data jobs on `/data` finish faster (developer-measured 78–91%
faster on the same host), and the `/data` job-progress panel's `done/total` counters must still tick
up honestly, one poll at a time — never snap straight to "done" and never mark partial data as
complete. Every score/bucket/pattern shown on `/stocks`, a ticker detail page, and `/evidence` must be
byte-identical to what it showed before this iteration (the backend byte-identity harness proves this
at the code level in `apps/backend/tests/test_scoring_window.py`; the tests below are the
browser-observable confirmation of that same guarantee).

**Do NOT duplicate** the API/artifact-level tests already covered in
`reports/qa/goal-mcp-loop-iter-26-test-plan.md` (TC-01 through TC-27) — those exercise
`score_stocks`, `close_on`/`bars_after`, and the byte-identity harness directly. The test cases below
are what a human sees in a browser.

**Operational precondition for every test below:** both services must be running in **prod mode**
(`start-backend.sh` / `start-frontend.sh` — never `dev.sh --reload`), and `apps/frontend/.next` must
have been freshly rebuilt (`rm -rf apps/frontend/.next` before starting the frontend), per the phase's
own operational-hygiene notes. A 30-year dataset must already be loaded (this is the standing state of
the dev environment).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend is running at http://localhost:3255, backend is running and reachable (both prod mode)
- At least one snapshot/run exists (standing 30-year dataset)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the page to fully load (the loading skeleton disappears)

**Expected Result:**
- The heading "Data Manager" is visible at the top of the page
- The "Dataset coverage" panel renders with non-empty numeric values for "Price history", "Symbols", "Trading days", and "Snapshot dates"
- The "Storage footprint" panel renders below it with non-empty values for "Database file", "Price bars", "Scanner rows", and "Forward returns"
- No "Backend unavailable" red error card is shown
- No blank page, no browser console errors

---

### UT-02 — Backfill job progress ticks honestly, never jumps to "done" early (happy-path, J-16 target)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- On `/data`, the "Dataset coverage" panel's "Backfill gaps" metric is checked first:
  - If it shows a count **greater than 0**, a real Backfill job is available over the pre-filled Start/End range.
  - If it shows **0** (no gaps), use the "Rebuild snapshots for current universe" button instead (Step 2b below) — it forces a real multi-date job regardless of gap count.
- No other job is currently running (the "Start a fetch / backfill job" panel's "Start" button is NOT disabled/showing "Job running…")

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. **If Backfill gaps > 0:** in the "Start a fetch / backfill job" panel, leave "Job kind" at its default value "Backfill snapshots" (the "Start date" and "End date" fields are pre-filled automatically from the first detected gap), then click the "Start" button.
   **2b. If Backfill gaps = 0:** scroll to the "Rebuild snapshots for current universe" panel, click the "Rebuild snapshots for current universe" button, then in the confirmation dialog titled "Confirm snapshot rebuild" click the "Rebuild snapshots" button.
3. Immediately after starting, observe the "Job progress" panel (right column): a status badge appears reading "running" (teal, with a spinning loader icon)
4. Watch the "Snapshots backfilled" row's counter (format `{done}/{total} dates`) for at least 10 seconds without refreshing the page
5. Confirm the counter's `done` value increases at least twice during that window (e.g. `3/40 dates` → `9/40 dates` → `17/40 dates`), each increase paired with the horizontal progress bar above it visibly growing
6. Wait for the job to finish (badge changes away from "running")

**Expected Result:**
- The `done` count in "Snapshots backfilled" never jumps directly from a low number (or 0) to the full `total` in a single poll tick — it climbs incrementally across multiple observed ticks
- The status badge never reads a completed state (e.g. "ok") while the counter still reads less than `total`
- Once finished, the badge reads "ok" (green) and the counter reads `{total}/{total} dates`, matching each other exactly — no state where the badge says done but the counter disagrees
- The "Snapshots created" / "forward returns inserted" line below the progress bar shows non-zero counts (unless the job was a genuine no-op, in which case both read 0 and the badge still correctly reads a completed, non-"running" state)

---

### UT-03 — Stage timings panel shows the measured speedup (happy-path / visible regression-budget proof)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- A Backfill (or Fetch + backfill) job has just completed (continue directly from UT-02, or start a fresh one covering ≥5 dates)

**Steps:**
1. On `/data`, in the "Job progress" panel, locate the "Stage timings" block (it appears below the progress bars once at least one stage has run)
2. Read the "Backfill" sub-section's "Elapsed", "Dates", and "Concurrency" rows
3. Look for a line reading "`{N.N}× faster than the per-date sum`" directly under the Backfill stats (only appears when the backend reports a speedup factor)

**Expected Result:**
- "Elapsed" shows a plausible small duration (seconds, not many minutes, for a handful of dates) consistent with the developer's measured 78–91% improvement
- The "`{N.N}× faster than the per-date sum`" line is present and shows a factor greater than 1.0× — this is the backend's own computed speedup ratio, not a frontend estimate
- No "Fetch" sub-section timing is shown unless a fetch stage actually ran (an absent stage renders nothing — no fabricated zero row)

---

### UT-04 — Cold-start `/data` load survives without crash or OOM (regression, iter-24 lesson)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Operator has terminal access to stop/start the backend process (`start-backend.sh`, prod mode)
- No browser tab has yet requested anything from the backend since the fresh start

**Steps:**
1. Stop the backend service completely
2. Start the backend fresh (cold start) using `start-backend.sh`
3. As the very FIRST request against the freshly-started backend, load `http://localhost:3255/data` in the browser (do not hit `/api/health` or any other route first)
4. Wait for the page to finish loading
5. Repeat steps 1–4 a second time (stop → cold start → `/data` as first request again)

**Expected Result:**
- Both times, `/data` renders fully: the "Dataset coverage" and "Storage footprint" panels show real numbers, not an error card
- No "Backend unavailable" error card appears
- No HTTP 500 response, no blank/crashed page
- The backend process does not exit or restart unexpectedly during either load (no OOM kill) — confirm the backend terminal/log shows no crash trace

---

### UT-05 — Storage footprint card values are consistent and well-formed (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` has loaded successfully (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Locate the "Storage footprint" panel (below "Dataset coverage")
3. Read all four values: "Database file" (a byte-size string like "1.2 GB"), "Price bars" (an integer with thousands separators), "Scanner rows" (an integer), "Forward returns" (an integer)
4. Refresh the page (F5) and re-read the same four values

**Expected Result:**
- All four values are non-empty, non-"—" (no NA placeholder) given the standing 30-year dataset
- "Database file" renders as a human-readable size (e.g. "1.24 GB", not a raw byte count)
- "Price bars", "Scanner rows", and "Forward returns" render as comma-formatted integers
- Values are identical before and after the refresh (assuming no job ran in between) — no flicker to a different number

---

### UT-06 — Per-date availability heatmap and legend are unchanged (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` has loaded successfully; the availability heatmap has data (standing 30-year dataset)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the "Per-date availability" panel
3. Confirm the legend area shows two labeled groups: "Price data — cell fill" (with six swatches labeled "none", "<25%", "25–50%", "50–75%", "75–<100%", "full") and "Scored snapshot — indicator" (with the text "a scored snapshot exists for that day")
4. Hover over any filled calendar cell
5. Confirm the hover readout (top-right of the legend area) shows text in the form "`{date} · {N}/{M} symbols · snapshot yes`" or "`... · snapshot no`"

**Expected Result:**
- Both legend groups render with all six density labels present, in that exact order
- The hover readout updates to show the exact figures for the hovered day (not a stale or blank value)
- No cell renders a color outside the expected blue density scale; no snapshot ring appears on a cell where the hover readout says "snapshot no"

---

### UT-07 — Job start form still validates malformed dates (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` has loaded; no job is currently running

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Start a fetch / backfill job" panel, click into the "Start date" field and clear it, then type `2026-13-40` (an invalid calendar date)
3. Observe the field and the "Start" button without submitting yet

**Expected Result:**
- A red inline error reading "Enter a valid date as YYYY-MM-DD" appears directly below the "Start date" field
- The "Start date" field's border turns red (invalid state)
- The "Start" button becomes disabled (grayed out, not clickable) while the invalid date is present
- No job starts and no network request is sent

---

### UT-08 — Starting a job while one is already running is blocked with a clear message (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- A Backfill or Fetch job is currently in the "running" state on `/data` (start one per UT-02 step 2/2b if needed)

**Steps:**
1. While the "Job progress" panel's badge still reads "running", look at the "Start a fetch / backfill job" panel's submit button
2. Attempt to click it

**Expected Result:**
- The button's label reads "Job running…" (not "Start") and it is visibly disabled (grayed out) while a job is in flight
- Clicking it produces no effect — no second job starts, no error dialog, no console crash
- Once the running job finishes, the button label reverts to "Start" and becomes clickable again

---

### UT-09 — `/stocks` leaderboard loads and scores match pre-iteration values (smoke + regression, byte-identity gated)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend and backend running; the scanner has scored data for the current as-of date
- Ideally, a pre-iteration screenshot or noted score/bucket values for at least 3 tickers is available for comparison (if none exists, this test instead confirms internal consistency: the same ticker's score matches between `/stocks` and its detail page in UT-11)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to load; confirm the heading "Stocks" and subtitle "Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason" are visible
3. Pick 3–5 tickers spanning both long-history names (e.g. large, well-known symbols) and any recently-added/short-history symbols visible in the list
4. For each, record the exact "Leadership", "Entry Quality", and "Risk" score numbers and letter-bucket badges shown in their row

**Expected Result:**
- The leaderboard table renders with rows, no error card, no blank table
- Each of the 3–5 recorded tickers shows a numeric score (0–100) and a bucket badge (A–E) for all three of Leadership, Entry Quality, and Risk — no missing/blank score cell
- If a pre-iteration baseline is available: every recorded value is IDENTICAL to the pre-iteration capture (exact number and exact bucket letter, not just "a number is present")
- Short-history symbols show either a full score (if they clear minimum-history) or an honest NA/exclusion — never a fabricated or zeroed score

---

### UT-10 — Evidence badges on `/stocks` still read "Not yet proven" for every score (regression, J-01 / J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded successfully (UT-09)
- The evidence ledger is known to be all-FAIL this iteration (no certified claims — per phase spec, both ledgers stay byte-identical all-FAIL)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. For the same 3–5 tickers picked in UT-09, locate the small evidence badge shown alongside each score
3. Hover over one badge and read its tooltip text

**Expected Result:**
- Every visible score's evidence badge reads exactly "Not yet proven" (muted/gray styling, shield icon) — no badge reads "Proven" and no score is shown without any badge
- The tooltip on hover reads "Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."
- No badge is a clickable link (a "Proven" badge would link to `/evidence`; none should here)

---

### UT-11 — `/stocks/[ticker]` detail page scores match the leaderboard row exactly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- `/stocks` is loaded and at least one ticker's Leadership/Entry Quality/Risk values were recorded (UT-09)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click on one of the tickers recorded in UT-09 (clicking the row or ticker link)
3. Confirm the page navigates to `http://localhost:3255/stocks/{TICKER}`
4. Confirm the page heading shows the ticker symbol, with subtitle "Stock detail — the three explainable scores (identical to the leaderboard; single source of truth)"
5. Read the Leadership, Entry Quality, and Risk score numbers and buckets shown on this detail page

**Expected Result:**
- The three score values and bucket letters on the detail page are IDENTICAL, digit-for-digit, to the values recorded for the same ticker on the `/stocks` leaderboard in UT-09
- No 404 or "Unknown ticker" warning card appears
- The "Back to leaderboard" link is present and, when clicked, returns to `/stocks`

---

### UT-12 — Dashboard Market Regime card renders unchanged (regression, J-04)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running; regime data exists for the current as-of date

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Confirm the heading "Dashboard" with subtitle "The daily snapshot at a glance" is visible
3. Locate the "Market Regime" card
4. Read the regime label badge and the large numeric score below it
5. Click "Why this regime — component breakdown" to expand the disclosure

**Expected Result:**
- The "Market Regime" card renders with a colored badge (e.g. "Risk-on", "Risk-off", or similar label) and a numeric score formatted to two decimal places
- No 500 error, no blank card, no "market regime unavailable" red error message
- The component breakdown expands and shows named components without error
- The "Market Phase & Severity" card beside it also renders with a phase label and severity figure, no error state

---

### UT-13 — `/evidence` ledger renders unchanged (all-FAIL / no-certified-claims state) (regression, J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- Frontend and backend running; both evidence ledgers remain all-FAIL this iteration (no new certified claims — confirmed out of scope for this phase)

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Confirm the heading "Evidence" and subtitle mentioning "Proven" ONLY when a referee-certified claim backs it, and "Not yet proven" otherwise, is visible
3. Scroll through the ledger / evidence sections on the page

**Expected Result:**
- No section shows a "Proven" / certified claim entry — the page is consistent with an all-FAIL ledger
- Where evidence for a given window is genuinely absent, an honest empty-state message is shown (e.g. "No forward-tested evidence for this window yet") rather than a blank section or a fabricated number
- No 500 error or crash

---

### UT-14 — Deep-history chart on ticker detail still renders full range (regression, J-10)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks/[ticker]`

**Preconditions:**
- A ticker with long price history is open (from UT-11, or navigate directly to a known long-history symbol, e.g. `http://localhost:3255/stocks/SPY` if SPY is in the universe/symbol set)

**Steps:**
1. On the ticker detail page, scroll to the price chart panel
2. Locate the chart range control near the chart (toggles between a default window and full history)
3. Switch the range control to show full history
4. Observe the chart render and the "chart-window-caption" text near it

**Expected Result:**
- The chart renders a continuous price line/candles covering the full stored history (spanning back years, not truncated to a recent window)
- No blank chart, no "Chart unavailable" error message
- The window caption text updates to reflect the full-history range selected
- Chart load does not take noticeably longer than before this iteration (no new lag introduced by the backend change)

---

### UT-15 — `/data` universe and membership-timeline counts render unchanged (regression, J-12)

**Type:** regression
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded successfully (UT-01)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Dataset coverage" panel, read the "Universe (as of date)" and "Candidate universe" figures
3. Scroll to the "Dynamic-universe membership timeline" panel and read its step-chart's rightmost (most recent) value and the honest labels ("Survivorship:", "Warm-up:", "Universe-relative:")
4. Scroll to the "Universe resolution" (per-date diagnostic) panel and read the "Admitted" count plus the excluded-by-reason counts

**Expected Result:**
- "Universe (as of date)" and "Candidate universe" show non-empty positive integers (not "—", not "loading")
- The membership timeline's step chart renders with a visible line and shows real dates on both ends (not an empty-state "No snapshots yet" message)
- The three honest labels (Survivorship / Warm-up / Universe-relative) render non-empty descriptive text, carried verbatim from the backend
- "Admitted" plus the four excluded-by-reason counts sum to the "candidate-pool" denominator stated in the panel's own footer text — no arithmetic mismatch

---

### UT-16 — Data Manager remains discoverable within 2 clicks; panel labels unchanged (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Preconditions:**
- Frontend running; user starts from the Dashboard

**Steps:**
1. Navigate to `http://localhost:3255/`
2. Look at the left sidebar navigation
3. Click "Data Manager" in the sidebar

**Expected Result:**
- "Data Manager" is visible in the sidebar (with a database icon) alongside "Dashboard", "Stocks", "Themes", "Sectors", "Scanner Runs", "Backtest", "Research", "Evidence", "Watchlist", and "Methodology" — the same set of nine other items as before this iteration (no new/removed/renamed nav entry)
- Clicking it navigates to `http://localhost:3255/data` in exactly one click from the Dashboard
- The panel titles on the resulting page read exactly: "Dataset coverage", "Storage footprint", "Rebuild snapshots for current universe", "Universe resolution …", "Dynamic-universe membership timeline", "Per-date availability", and "Start a fetch / backfill job" / "Job progress" — identical wording to the pre-iteration UI (no new panel added, no panel removed, no relabeling)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads without errors | smoke | P1 | `/data` |
| UT-02 | Backfill progress ticks honestly (J-16 target) | happy-path | P1 | `/data` |
| UT-03 | Stage timings show measured speedup | happy-path | P1 | `/data` |
| UT-04 | Cold-start `/data` survives, no OOM | regression | P1 | `/data` |
| UT-05 | Storage footprint values well-formed | regression | P2 | `/data` |
| UT-06 | Availability heatmap + legend unchanged | regression | P2 | `/data` |
| UT-07 | Job form rejects malformed dates | validation | P2 | `/data` |
| UT-08 | Second job start blocked while running | error | P2 | `/data` |
| UT-09 | Leaderboard scores byte-identical (sample) | regression | P1 | `/stocks` |
| UT-10 | Evidence badges still "Not yet proven" | regression | P1 | `/stocks` |
| UT-11 | Ticker detail scores match leaderboard | regression | P1 | `/stocks/[ticker]` |
| UT-12 | Dashboard regime card unchanged | regression | P1 | `/` |
| UT-13 | Evidence ledger all-FAIL unchanged | regression | P1 | `/evidence` |
| UT-14 | Deep-history chart still full-range | regression | P2 | `/stocks/[ticker]` |
| UT-15 | Universe/membership counts unchanged | regression | P2 | `/data` |
| UT-16 | Data Manager discoverable, labels unchanged | ux | P3 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02 and UT-03 are the direct
browser-observable proof of J-16 (fast + honest job progress); UT-09 through UT-13 are the
browser-observable proof that the byte-identity guarantee (the phase's primary correctness gate) holds
for every user-visible score and evidence status.
