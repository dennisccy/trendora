# Phase goal-market-compass-iter-1 — UI Test Plan

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Ground-truth facts used below

Captured live against the running instance while writing this plan — reuse these exact values, or
substitute today's current equivalents if time has passed and figures have moved on:

- Latest stored as-of: **2026-08-14**. Two most recent trading days (the required backfill precondition
  range): **2026-08-13** and **2026-08-14**.
- Current (pre-fallback) `/stocks` sector coverage: **424 / 541 resolved stocks (78.4%) show
  "Unassigned"** — confirmed both via the UI's `visible-count` badge and a direct `GET /api/stocks` count.
- `DELL` — curated (`config.stock_sectors`), sector **"Technology"**, unaffected by this iteration.
- `GRMN` — currently `null`/"Unassigned"; its `universe_pool.csv` sector is **"Consumer Discretionary"**,
  so it is expected to resolve to that value once a fresh backfill runs under this iteration's code.
- A live, read-only preview of removing 2026-08-13→2026-08-14 (`POST /api/data/remove/preview`) returned
  `refused: false` with `removable_bar_count: 1174`, `removable_symbol_count: 587`,
  `cascade.snapshot_count: 18`, `cascade.forward_return_count: 30439` — i.e. this range is safely
  removable user-added data today, not protected committed seed. **Exact counts will differ by the time
  you run this** — that is expected; the pass bar is "non-zero, not refused", not these specific numbers.
- `GET /api/methodology` **today omits the `universe_selection` key entirely** (pre-existing,
  out-of-scope gate — see UT-02/UT-07/UT-10).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no "test the form" / "verify it works". -->

---

### UT-01 — Stocks leaderboard loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3255; backend running at http://localhost:8255 (`GET
  http://localhost:8255/api/health` returns `"status":"ok"`).
- No login required — this app has no auth.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the page to finish loading (the loading skeleton disappears)

**Expected Result:**
- The heading "Stocks" is visible, with subtitle text starting "Stock Leaderboard — ranked by
  Leadership..."
- A `data-testid="visible-count"` badge is visible in the filter bar reading `<N> / <N>` (e.g. `541 /
  541`) with no filters applied
- The leaderboard table renders with a "Sector" column header among others
- No "Backend unavailable" error card appears
- No JavaScript console errors

---

### UT-02 — Methodology page core content loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/methodology`

**Preconditions:**
- Frontend/backend running as in UT-01.

**Steps:**
1. Navigate to `http://localhost:3255/methodology`
2. Wait for the page to finish loading

**Expected Result:**
- The heading "Methodology" is visible, with subtitle text starting "What every setup status and detected
  price pattern mean..."
- At least one methodology entry card renders below the heading (each carries a "Setup" or "Pattern"
  badge)
- A Glossary section renders near the bottom of the page
- No "Backend unavailable" error card appears
- No JavaScript console errors
- **Note:** the "Universe Selection" card (`data-testid="universe-selection"`) is NOT expected to appear
  in this environment today. Its absence is a known, pre-existing, out-of-scope condition (see UT-10) and
  must NOT be treated as a failure of this smoke test.

---

### UT-03 — Precondition: seed-safe Remove + Backfill of the last two trading days (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend/backend running. Confirm the two most recent dates in the coverage panel's "Snapshot dates"
  list — use `2026-08-13` / `2026-08-14` if unchanged from when this plan was written, otherwise use
  today's two most recent dates.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Remove imported data" panel, type `2026-08-13` into the "From date (required)" field and
   `2026-08-14` into the "To date (required)" field
3. Click the "Preview removal" button
4. In the "Confirm data removal" modal that opens, read the "Will be removed (user-added)" box's bar count
   and affected-symbol count, and confirm no amber "refused" banner is shown
5. Click the "Remove `<N>` bars" button (N = the bar count shown in step 4)
6. In the "Start a fetch / backfill job" panel, type `2026-08-13` into "Start date" and `2026-08-14` into
   "End date"; leave "Job kind" on its default value, "Backfill snapshots"
7. Click the "Start" button
8. Wait for the live job card's status badge (`data-testid="job-status"`) to stop reading "running"

**Expected Result:**
- After step 4: the "Will be removed (user-added)" box shows a bar count > 0 and a symbol count > 0; no
  "refused" banner appears (this specific range is user-added data, not the protected committed seed)
- After step 5: a green confirmation line appears reading "Removed `<N>` user-added bars; cascade-removed
  `<M>` snapshots and `<K>` forward returns..." with N matching step 4's count
- After step 8: the job status badge reads **"ok"** (not "failed" / "failed at backfill"), and the text
  directly below it reads "`<N>` snapshots · `<N>` forward returns inserted" with both numbers greater
  than 0
- The app has not entered an error state (no "Backend unavailable" card anywhere)

---

### UT-04 — Sector coverage improves to ≤5% Unassigned at the new latest as-of (happy path — TC-1)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- UT-03 completed (a fresh backfill has run over the last two trading days).

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Look at the top-bar as-of control (upper right, `aria-label="View as-of date"`); if it shows "Viewing
   as-of ... (historical)" rather than "Latest", click it and select the newest available date
3. Open the "Sector" filter dropdown (`aria-label="Filter by sector"`) and select `Unassigned`
4. Read the `data-testid="visible-count"` badge, e.g. `18 / 541` — the first number is the Unassigned
   count, the second is the total
5. Open `http://localhost:8255/api/stocks` in a new browser tab and count how many entries in the `rows`
   array have `"sector": null` (or use `curl http://localhost:8255/api/stocks` and grep/count)

**Expected Result:**
- The Unassigned count from step 4, divided by the total from the same badge, is **at most 5%** (today's
  pre-fallback baseline was 424/541 = 78.4%)
- The count from step 5 (direct API count of `"sector": null`) **equals** the count from step 4 — the UI
  and the API must agree (this project's own evidence-quality lesson: never trust a screenshot alone)
- Clearing the Sector filter back to "All sectors" and searching `GRMN` shows its Sector cell now reading
  a real sector (`Consumer Discretionary`) instead of "Unassigned"

---

### UT-05 — Cross-surface sector consistency for a curated and a pool-fallback ticker (happy path — TC-2)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`, `/stocks/{ticker}`

**Preconditions:**
- UT-03 completed.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Type `DELL` into the "Search ticker or name…" box (`data-testid="stocks-search"`) and note the Sector
   cell value for the DELL row
3. Clear the search box, type `GRMN`, and note the Sector cell value for the GRMN row
4. Click the `DELL` ticker link (it opens `/stocks/DELL` in a new tab) and note the small sector text next
   to the setup-status badge
5. Click the `GRMN` ticker link (opens `/stocks/GRMN`) and note the same
6. Open `http://localhost:8255/api/stocks/DELL` and `http://localhost:8255/api/stocks/GRMN` (or filter the
   `rows` array of `http://localhost:8255/api/stocks` by ticker) and note each response's `"sector"` field

**Expected Result:**
- `DELL` reads **"Technology"** in all three places (leaderboard cell, detail header, API response) —
  unchanged from before this iteration
- `GRMN` reads **"Consumer Discretionary"** in all three places — changed from `null`/"Unassigned" before
  the backfill to the pool-CSV fallback value after it
- All three surfaces agree with each other for each ticker; no drift between leaderboard, detail page, and
  API

---

### UT-06 — Remove panel requires both valid dates before enabling Preview (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data` — the pre-existing "Remove imported data" panel, exercised here because it is this
iteration's own required test precondition (UT-03), not because this iteration changed its validation
logic.

**Preconditions:**
- Frontend running.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. In the "Remove imported data" panel, leave "From date (required)" empty and type `2026-08-14` into "To
   date (required)" only
3. Observe the "Preview removal" button (`data-testid="remove-preview-button"`)
4. Now type an invalid value, `2026-13-40`, into "From date (required)"
5. Observe the "Preview removal" button again

**Expected Result:**
- At step 3, the "Preview removal" button is disabled (greyed out, not clickable) — only one of the two
  required dates is filled
- At step 5, the button remains disabled — `2026-13-40` is not a valid calendar date
- In neither case does a "Confirm data removal" modal open, and no network request is sent

---

### UT-07 — Methodology page degrades gracefully with today's gated payload (error / resilience)

**Type:** error
**Priority:** P2
**Surface:** `/methodology`

**Preconditions:**
- Frontend/backend running. `GET http://localhost:8255/api/methodology` currently omits
  `universe_selection` in this environment (confirmed live while writing this plan).

**Steps:**
1. Open the browser's developer console (F12) and clear it
2. Navigate to `http://localhost:3255/methodology`
3. Watch the console while the page loads and for a few seconds after

**Expected Result:**
- No red console errors appear — specifically nothing referencing `sector_basis`, `universe_selection`, or
  "Cannot read properties of undefined"
- The page renders its normal content (entries + glossary) with no visible gap, blank section, or broken
  layout where the Universe Selection card would sit — its absence is seamless, not a broken placeholder
- This confirms the new conditional render (`state.data.universe_selection ? <UniverseSelectionCard
  .../> : null`) fails safe when the field is missing, rather than crashing

---

### UT-08 — Existing leaderboard behavior is unchanged: curated sectors, scores, filters (regression — TC-4 spot-check)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Run after UT-03. (For the strongest evidence, also spot-check DELL's scores once before UT-03 and once
  after, and compare — they must be identical; the backend's own byte-identity unit test already proves
  this at the data layer, so this is a lighter UI-level spot-check of the same guarantee.)

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Search for `DELL`; note its Leadership, Entry Quality, and Risk score badges (bucket color + numeric
   value) and its Setup status badge text
3. Clear the search, open the "Setup" filter dropdown, and select any one non-"All" status; confirm the
   leaderboard narrows to only rows carrying that status
4. Clear the Setup filter, click the "Sector" column header to sort by sector

**Expected Result:**
- DELL's Leadership / Entry Quality / Risk score values and Setup status are unchanged from before this
  iteration's backfill
- The Setup filter still narrows the leaderboard correctly — unrelated existing feature, unaffected by
  this iteration
- Sorting by Sector still works; a `data-testid="sort-indicator"` arrow appears next to the "Sector"
  header and rows reorder alphabetically by sector label, now with far fewer rows collapsed into a single
  "Unassigned" cluster at one end

---

### UT-09 — Sector filter is discoverable without any new navigation (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/stocks` filter bar, sidebar navigation

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3255` (Dashboard)
2. Click "Stocks" in the left sidebar
3. Look at the filter bar directly under the "Stocks" page heading

**Expected Result:**
- "Stocks" is visible in the sidebar and reaches `/stocks` in exactly one click — unchanged navigation,
  this iteration adds no nav entries
- The "Sector" label and its dropdown are visible in the filter bar without scrolling on a standard
  desktop viewport, next to the search box
- No tooltip or explanation is needed to understand what the Sector filter narrows — pre-existing, unchanged
  UI, now backed by materially more complete data

---

### UT-10 — Universe Selection "Stock sector labels" disclosure content (informational — environment-gated, non-blocking)

**Type:** happy-path (content check)
**Priority:** P3 — informational only; must NOT gate this iteration's overall PASS verdict
**Surface:** `/methodology`

**Preconditions:**
- None achievable in this environment today — see Expected Result.

**Steps:**
1. Navigate to `http://localhost:3255/methodology`
2. Look for a card titled "Universe Selection" (`data-testid="universe-selection"`) carrying a "Screen"
   badge

**Expected Result — today, in this environment:**
- The card is **absent**. This is expected and correct, not a bug in this iteration. It is gated by a
  pre-existing, unrelated condition: `GET http://localhost:8255/api/methodology` does not include a
  `universe_selection` object because the committed offline screen record
  `apps/backend/data/seed/universe.json` has never been built here. No in-app control builds this file.

**Expected Result — once `data/seed/universe.json` exists** (a separate, manual, out-of-scope job; not
something this iteration or its browser QA can fix):
- The "Universe Selection" card appears, and within it a subsection titled "Stock sector labels" with a
  "Data basis" badge (`data-testid="universe-sector-basis"`) shows this exact text: "Each stock's sector
  label is resolved from two sources, in order: the curated `config.stock_sectors` mapping (Trendora's
  original universe) first, then — for any name the curated map does not cover — a fallback to the sector
  recorded in the committed candidate pool (universe_pool.csv). A name present in neither source serves no
  sector ('Unassigned') — never a fabricated value. Both sources describe the CURRENT sector only: there
  is no point-in-time sector history, so a stock's sector label at a historical as-of date reflects
  today's mapping, not necessarily what its sector was on that date (tracked open as backlog item B-114)."
- This exact text is already verified correct by passing backend tests
  (`test_universe_selection_sector_basis_present_and_matches_config`,
  `test_sector_basis_is_config_only_no_hard_coded_copy`,
  `test_universe_selection_sector_basis_served_and_names_both_sources`) — this UI step would only be
  confirmation, not the source of truth.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Stocks leaderboard loads | smoke | P1 | `/stocks` |
| UT-02 | Methodology core content loads | smoke | P1 | `/methodology` |
| UT-03 | Remove + Backfill precondition | happy-path | P1 | `/data` |
| UT-04 | Unassigned share ≤5% (TC-1) | happy-path | P1 | `/stocks` |
| UT-05 | Cross-surface consistency (TC-2) | happy-path | P1 | `/stocks`, `/stocks/{ticker}` |
| UT-06 | Remove panel required-field guard | validation | P2 | `/data` |
| UT-07 | Methodology graceful degradation | error | P2 | `/methodology` |
| UT-08 | Curated sectors + scores unchanged (TC-4) | regression | P1 | `/stocks` |
| UT-09 | Sector filter discoverability | ux | P3 | `/stocks`, nav |
| UT-10 | Sector-basis disclosure content (TC-5) | happy-path (informational) | P3 — non-blocking | `/methodology` |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-08) must all pass for browser QA verdict to be PASS.**
UT-10 is deliberately excluded from the pass bar — it documents a pre-existing, out-of-scope environment
gate (missing `data/seed/universe.json`), not a defect in this iteration's implementation. See the "Not
Visible Yet" section of `reports/phase-goal-market-compass-iter-1-user-visible-changes.md` for the full
explanation.
