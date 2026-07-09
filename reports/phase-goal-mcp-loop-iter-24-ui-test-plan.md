# Phase goal-mcp-loop-iter-24 — UI Test Plan

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL (for troubleshooting only):** http://localhost:8255

---

## Scope note

This iteration is goal.md's fast-platform **mechanical backend pass** (items B/C/D/G/H), a measurement
harness (item K), and **one** new UI surface: a read-only "Storage footprint" card on `/data`. Every
optimized backend path is byte-identity-gated — no displayed number is supposed to change anywhere in the
product. Accordingly this plan is weighted toward:
1. The one genuinely new capability (the Storage footprint card) — smoke / happy-path / ux.
2. Byte-identity regression checks on the five existing surfaces the backend changes feed
   (`/stocks/{ticker}`, `/watchlist`, the global readiness badge, the `/backtest`/`/research` warming
   card, and `/data`'s own Missing-data diagnostic + Dataset coverage panels) — these are marked **P1**
   even though they are "regression" type, because a value drifting here would trip the session's
   critical anti-goal on byte-identical displayed numbers, not just a cosmetic regression.
3. The J-15 page-speed budgets from the DEFINITION OF DONE.

This plan does **not** duplicate the backend/API-level tests already in
`reports/qa/goal-mcp-loop-iter-24-test-plan.md` (TC-01 pragmas, TC-02 index plans, TC-04 readiness query
count, TC-06/07 `compute_capacity` internals, TC-08 `measure-perf.sh`, TC-11 golden-snapshot byte-diff).
Every test case below is something a human can only observe in a rendered browser page.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` page loads with the new Storage footprint card (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Frontend running in prod mode at http://localhost:3255; backend running in prod mode at
  http://localhost:8255 and reachable (`GET /api/health` returns 200)
- The backend has the project's normal (non-empty) dataset loaded — not a fresh/empty database

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the loading skeleton to be replaced by real content (a few seconds)

**Expected Result:**
- The page heading "Data Manager" is visible near the top
- A card titled "Dataset coverage" renders with its metric grid populated
- Directly below it, a new card titled "Storage footprint" renders (small database icon next to the
  title) showing four labeled values: "Database file", "Price bars", "Scanner rows", "Forward returns"
- No red "Backend unavailable" error card is shown
- No blank white page, no broken/unstyled layout, no browser console errors

---

### UT-02 — Storage footprint values match the `GET /api/data` capacity payload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Same as UT-01
- Browser DevTools available (Network tab)

**Steps:**
1. Navigate to `http://localhost:3255/data` with DevTools open on the Network tab
2. Reload the page and find the `GET /api/data` request in the Network list; open its Response/Preview
   and locate the `capacity` object, noting its four fields: `db_file_bytes`, `daily_prices_rows`,
   `scanner_results_rows`, `forward_returns_rows`
3. On the rendered page, scroll to the "Storage footprint" card
4. Compare each of the card's four displayed values against the four fields noted in step 2

**Expected Result:**
- "Database file" displays a human-readable size derived from `capacity.db_file_bytes` (e.g. a
  `db_file_bytes` of `1310720000` displays as something like "1.22 GB" — never the raw byte integer, and
  never "0 B" unless `db_file_bytes` is actually `0`)
- "Price bars" displays `capacity.daily_prices_rows` formatted with thousands separators (e.g.
  `3293160` → "3,293,160")
- "Scanner rows" displays `capacity.scanner_results_rows` the same way
- "Forward returns" displays `capacity.forward_returns_rows` the same way
- None of the four values reads "undefined", "NaN", or blank

---

### UT-03 — Job-start form still rejects a malformed date (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Same as UT-01
- No data job is currently running on `/data` (the "Start" button is not already disabled by a running
  job — if one is running, wait for it to finish first)

**Steps:**
1. Navigate to `http://localhost:3255/data` and scroll to the "Start a fetch / backfill job" card
2. Click into the "Start date" field and type `2024-13-40` (an invalid calendar date)
3. Click into the "End date" field (moving focus away from "Start date")

**Expected Result:**
- A red inline message "Enter a valid date as yyyy-MM-dd" appears directly below the "Start date" field
- The "Start" button remains disabled (grayed out, not clickable)
- No job starts

**Steps (continued):**
4. Clear "Start date" and type a valid date, e.g. `2024-06-01`; clear "End date" and type `2024-06-05`

**Expected Result (continued):**
- The inline error under "Start date" disappears
- The "Start" button becomes enabled (assuming no job is already running)

---

### UT-04 — Storage footprint shows an honest zero state on a cold/empty database (validation — boundary state)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- A **separate** backend instance pointed at a brand-new, empty SQLite file — e.g. start the backend with
  `database.url` (or the `DATABASE_URL` equivalent) overridden to a fresh path such as
  `sqlite:///tmp/empty-iter24-check.db`, before any import has run against it.
- Do **not** point the shared/live dataset's config at an empty file to run this check — this test needs
  an isolated, throwaway database.
- Frontend pointed at that empty-DB backend for this check only.

**Steps:**
1. Navigate to `http://localhost:3255/data` against the empty-DB backend
2. Wait for the page to finish loading

**Expected Result:**
- The "Storage footprint" card still renders — no crash, no "Backend unavailable" error card
- "Database file" shows "0 B"
- "Price bars", "Scanner rows", and "Forward returns" each show "0"
- The rest of the page (e.g. "Dataset coverage") also shows its own honest empty state rather than an
  error

**If an isolated empty-DB instance is not available to the tester:** do not mark this PASS from
inference. Mark it **Not Executed** and rely on the backend unit test for `compute_capacity`'s empty-DB
case (`reports/qa/goal-mcp-loop-iter-24-test-plan.md` TC-06) as the authoritative check instead.

---

### UT-05 — `/data` shows one clean error card when the backend is unreachable (error)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Ability to stop the backend process or block port 8255 temporarily

**Steps:**
1. Stop the backend (or otherwise make `http://localhost:8255` unreachable)
2. Navigate to `http://localhost:3255/data`

**Expected Result:**
- Exactly ONE red-bordered card appears with the heading "Backend unavailable" and the text "Dataset
  coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the
  backend is running and retry."
- The new Storage footprint card does **not** render a second, separate error state — the page shows one
  error card total, not one per panel
- No blank/frozen page, no unhandled browser console exception

**Steps (continued):**
3. Restart the backend and reload the page

**Expected Result (continued):**
- The error card disappears and the page renders normally, including the Storage footprint card

---

### UT-06 — Missing-data diagnostic renders unchanged rows after the cold-path fix (regression — item H)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Ability to restart the backend process
- Backend has the normal (non-empty) dataset loaded

**Steps:**
1. Before restarting anything, navigate to `http://localhost:3255/data` and note exactly what the
   "Missing-data diagnostic" card shows today: either the empty state "No missing data", or the specific
   rows under "No history" / "Thin history" / "Intra-series gaps" (symbol + shortfall figures)
2. Restart the backend fresh (prod mode)
3. Immediately navigate to `http://localhost:3255/data` — this is the first request after boot, exercising
   the cold path item H changed
4. Compare the "Missing-data diagnostic" card's contents against what was noted in step 1

**Expected Result:**
- The exact same rows (same symbols, same category, same shortfall numbers such as "N / M bars" or "N
  missing (date → date)") or the exact same "No missing data" empty state appear both before and after
  the restart — nothing added, removed, re-labeled, or re-ordered
- The card populates without an unusually long stall (informal observation; the precise before/after
  timing belongs in `reports/perf-budgets.md`, not this check)

---

### UT-07 — Dataset coverage numbers stay stable across a reload (regression — items B/C/G/H)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3255/data` and note the exact values shown for "Universe (as of date)",
   "Candidate universe", "Symbols", "Trading days", "Snapshot dates", and "Backfill gaps"
2. Refresh the page (F5)
3. Note the same six values again

**Expected Result:**
- All six values are identical between step 1 and step 3 — no drift introduced by the pragma/index/N+1
  changes underneath this page
- If `reports/perf-budgets.md` records a "before" figure for any of these fields from prior to this
  iteration, the value observed here also matches it exactly

---

### UT-08 — `/stocks/AAPL` matches its `/stocks` leaderboard row exactly (regression — item D)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/AAPL`

**Preconditions:**
- AAPL is present in the scored universe at the current as-of date

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Type `AAPL` into the "Search ticker or company name" field (placeholder "Search ticker or name…")
3. Note the AAPL row's values in the "Leadership", "Entry Quality", "Risk", and "Setup" columns, plus its
   Sector text and any Theme badges shown
4. Click the "AAPL" ticker link in that row (or navigate directly to `http://localhost:3255/stocks/AAPL`)
5. On the detail page, note: the setup-status badge at the top, the three score cards' values under
   "Leadership" / "Entry Quality" / "Risk", and the sector text next to the setup badge

**Expected Result:**
- Every value noted in step 5 matches the corresponding value noted in step 3 exactly — no drift caused by
  the ticker-filtered fetch (item D) that now serves this page
- The page heading shows "AAPL"; the page loads without an "Unknown ticker" or "Backend unavailable" card

---

### UT-09 — Full-history toggle on the stock detail chart still works (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- On `http://localhost:3255/stocks/AAPL` (or any valid ticker) with the "Price & moving averages" card
  visible

**Steps:**
1. Confirm the "Recent" button is the highlighted/pressed option in the chart's range control (top-right
   of the "Price & moving averages" card) by default
2. Click the "Full history" button next to it

**Expected Result:**
- "Full history" becomes the visually pressed option (replacing "Recent")
- The chart redraws with a longer date range (older candles appear); the caption above the chart (e.g.
  "N bars · as of … · history since …") updates to a larger bar count and an earlier "history since" date
- No error message, no blank chart area, no frozen page

**Steps (continued):**
3. Click "Recent" again

**Expected Result (continued):**
- The chart reverts to the bounded recent window; the caption's bar count drops back down and "history
  since" moves to a more recent date

---

### UT-10 — Watchlist add + values match the leaderboard (regression — item D)

**Type:** regression
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- MSFT is present in the scored universe at the current as-of date
- MSFT is not already on the watchlist (if it is, remove it first via the row's remove control, or
  substitute a different ticker not currently saved)

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Type `MSFT` into the "Ticker to add" field
3. Type `Regression check` into the "Reason for watching" field
4. Click the "Add" button
5. Once the table refreshes, note the new MSFT row's "Leadership", "Entry Quality", "Risk", and "Setup"
   column values
6. Navigate to `http://localhost:3255/stocks`, type `MSFT` into the search field, and note the same four
   values on the leaderboard row

**Expected Result:**
- The new MSFT row appears on `/watchlist` with "Added" showing today's date and "Reason" showing
  "Regression check"
- All four values ("Leadership", "Entry Quality", "Risk", "Setup") noted in step 5 match exactly the
  values noted in step 6 — confirms the ticker-filtered watchlist fetch (item D) serves the same values as
  the full leaderboard path

---

### UT-11 — Global readiness badge shows a valid state on every page (regression — item G)

**Type:** regression
**Priority:** P2
**Surface:** global (every page, top-right of the header)

**Preconditions:**
- Frontend and backend both running

**Steps:**
1. Load `http://localhost:3255/` (or any page) and look at the top-right of the header bar, just left of
   nothing (it is the rightmost element, next to the as-of date control)
2. Observe the small pill-shaped badge

**Expected Result:**
- The badge shows exactly one of: a green "Ready" badge, an amber "Initializing… history N/M" badge (two
  whole numbers separated by a slash), or a red "Backend unavailable" badge
- It is never blank, never shows "undefined/undefined", and never remains stuck on "Checking backend…"
  for more than a few seconds after the page loads

**Steps (continued):**
3. Open DevTools → Network tab and watch the recurring `GET /api/health` calls over ~10 seconds

**Expected Result (continued):**
- Each `/api/health` call completes quickly (comfortably under a second on a warm backend; the committed
  server-side budget is ≤ 0.1 s per `reports/perf-budgets.md` — occasional network/dev-tools overhead on
  top of that is expected, but a call consistently taking multiple seconds is a regression)
- The badge's text updates in step with each successful call (e.g. the "history N/M" figure advances while
  initializing)

---

### UT-12 — Warming-up card matches the top-bar badge's progress (regression — item G; conditional)

**Type:** regression
**Priority:** P3
**Surface:** `/backtest`, `/research/*`

**Preconditions:**
- This check is only observable in the window right after a fresh backend restart, while historical
  warm-up is still in progress. If the backend has been up for a while, readiness will already read
  "Ready" and this state cannot be triggered live — in that case, mark this test **Not Executed** rather
  than guessing a result.

**Steps:**
1. Immediately after starting the backend fresh (prod mode), before warm-up finishes, note the top-right
   badge's "Initializing… history N/M" figure
2. Within the same few seconds, navigate to `http://localhost:3255/backtest`

**Expected Result:**
- A card with the heading "Warming up — historical evidence still loading (N/M)" appears, showing the same
  N/M figure noted in step 1 (allow the figure to have advanced slightly if another poll landed in
  between)
- The page does not show a blank result, a crash, or a partial result presented as complete

**Steps (continued):**
3. Wait for the top-bar badge to flip to "Ready", then reload `/backtest`

**Expected Result (continued):**
- The "Warming up…" card disappears and the page shows its normal populated content automatically — no
  extra click needed beyond the reload

---

### UT-13 — Storage footprint card is discoverable within one click + a short scroll (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation → `/data`

**Steps:**
1. Starting from `http://localhost:3255/` (Dashboard), look at the left sidebar
2. Click "Data Manager" in the sidebar (database icon, near the bottom of the nav list)
3. From the top of the resulting page, scroll down just past the first card

**Expected Result:**
- The URL becomes `http://localhost:3255/data`
- The "Storage footprint" card is visible immediately after the first ("Dataset coverage") card — no
  second navigation, tab, or expand/collapse action is needed to find it
- Its four labels ("Database file", "Price bars", "Scanner rows", "Forward returns") are legible without
  hovering over or clicking anything
- Total actions from the Dashboard to seeing the card: one click + one scroll

---

### UT-14 — Each Storage footprint value has a plain-language definition (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/data`

**Steps:**
1. On `http://localhost:3255/data`, look directly underneath each of the four Storage footprint values

**Expected Result:**
- Underneath "Database file": "The on-disk size of the SQLite database file."
- Underneath "Price bars": "Rows in daily_prices — one per (symbol, date) stored bar."
- Underneath "Scanner rows": "Rows in scanner_results — one per (snapshot run, stock) scored result."
- Underneath "Forward returns": "Rows in forward_returns — one per (snapshot run, symbol, horizon)
  realized return."
- No value on this card is shown as a bare, unexplained number — consistent with every other metric on
  the "Dataset coverage" card above it

---

### UT-15 — Core pages meet their time-to-interactive budgets (regression / J-15 target)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/stocks/AAPL`, `/data`, `/evidence`

**Preconditions:**
- Both services running in prod mode; `apps/frontend/.next` was cleared and the frontend rebuilt before
  this check (per the phase's operational hygiene note) so this is not measuring a stale/dev bundle
- This is a **warm** check — load each page once first (uncounted) so the second load is the one timed

**Steps:**
1. With DevTools Network tab open (cache enabled, not disabled), navigate to `http://localhost:3255/stocks`
   a second time; note the time from navigation to the full leaderboard table replacing the loading
   skeleton
2. Repeat for `http://localhost:3255/stocks/AAPL`
3. Repeat for `http://localhost:3255/data` (including the new Storage footprint card populating)
4. Repeat for `http://localhost:3255/evidence`

**Expected Result:**
- Each of the four pages finishes loading and becomes interactive within about 3 seconds on the warm
  reload
- None of the four pages ever shows a blank white screen, a frozen/unresponsive frame, or a Next.js
  "Application error" page — if a page is genuinely slow, it shows its own loading skeleton or an honest
  "Initializing…" / "Warming up…" state instead of freezing
- Record the observed times and compare against the committed budgets in `reports/perf-budgets.md` (pages
  ≤ 3 s warm)

---

### UT-16 — Cold `/data` completes without a hang or a blank frame after a backend restart (error / smoke boundary)

**Type:** error
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- Ability to stop and start the backend process (`scripts/start-backend.sh`)
- Backend has the normal (non-empty, deep-basis) dataset loaded

**Steps:**
1. Stop the backend
2. Start the backend fresh in prod mode; the moment it reports it is listening, immediately navigate to
   `http://localhost:3255/data` — this is the cold path (first request after boot, nothing cached)
3. Watch the page while it loads, without refreshing

**Expected Result:**
- Within 60 seconds, the page fully renders: "Dataset coverage", the new "Storage footprint" card, and
  "Missing-data diagnostic" all show real (non-error) values
- The backend process does not crash or restart during this window (no out-of-memory kill)
- The page never shows a blank white screen for the whole window — it shows its own loading skeleton
  until data arrives, then the real content all at once

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads with the new Storage footprint card | smoke | P1 | `/data` |
| UT-02 | Storage footprint values match the API capacity payload | happy-path | P1 | `/data` |
| UT-03 | Job-start form still rejects a malformed date | validation | P2 | `/data` |
| UT-04 | Storage footprint honest zero state on empty DB | validation | P2 | `/data` |
| UT-05 | `/data` shows one clean error card when backend is down | error | P2 | `/data` |
| UT-06 | Missing-data diagnostic rows unchanged after cold-path fix | regression | P1 | `/data` |
| UT-07 | Dataset coverage numbers stable across reload | regression | P1 | `/data` |
| UT-08 | `/stocks/AAPL` matches its leaderboard row exactly | regression | P1 | `/stocks/AAPL` |
| UT-09 | Full-history chart toggle still works | regression | P2 | `/stocks/{ticker}` |
| UT-10 | Watchlist add + values match the leaderboard | regression | P1 | `/watchlist` |
| UT-11 | Readiness badge shows a valid state everywhere | regression | P2 | global |
| UT-12 | Warming-up card matches the badge's progress (conditional) | regression | P3 | `/backtest`, `/research/*` |
| UT-13 | Storage footprint discoverable in 1 click + a scroll | ux | P2 | nav → `/data` |
| UT-14 | Every Storage footprint value has a plain definition | ux | P3 | `/data` |
| UT-15 | Core pages meet time-to-interactive budgets | regression | P1 | `/stocks`, `/stocks/AAPL`, `/data`, `/evidence` |
| UT-16 | Cold `/data` completes without hanging | error | P2 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.** Per this phase's anti-goal on
byte-identical displayed numbers, UT-06/07/08/10/15 are held to P1 even though "regression" is normally a
P3-default category in the test-design skill — a value drift on any of them is a critical-severity finding,
not a cosmetic one.
