# Phase goal-mcp-loop-iter-19 — UI Test Plan

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8000 (referenced in preconditions; every page shows a "Backend unavailable" card if it isn't reachable)

---

## Scope note

This plan is grounded directly in the current frontend source (`apps/frontend/app/stocks/page.tsx`,
`lib/sector-label.ts`, `app/error.tsx`, `app/global-error.tsx`, `app/stocks/[ticker]/page.tsx`,
`app/scanner-runs/[runId]/page.tsx`, `app/data/page.tsx`, `app/evidence/page.tsx`,
`app/watchlist/page.tsx`, `app/backtest/page.tsx`), not paraphrased from the surface map alone, so button
text and expected copy below are exact quotes from the shipped components.

**Correction to the phase spec's wording:** the phase spec and plan describe J-12's target as "the
`/methodology` membership timeline." Direct source inspection shows the actual UI component
(`MembershipTimelinePanel`, titled "Dynamic-universe membership timeline") lives on **`/data`** (the Data
Manager page), inside `apps/frontend/app/data/page.tsx`. The `/methodology` page (`app/methodology/page.tsx`)
has no timeline — only the Universe Selection card, setup/pattern entries, and the Glossary. UT-14/UT-15
below test the real location (`/data`) so this test plan is directly executable without a wrong-page dead end.

Test IDs use UT-XX (distinct from the functional test plan's TC-XX IDs and from any stale UT-XX numbering
left over in a browser-qa-agent task list from a prior iteration's run — this plan's numbering is
self-contained to this file only).

---

### UT-01 — `/stocks` loads successfully on the default (~78% null-sector) state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3255, backend running at http://localhost:8000
- No login required
- Default seeded dataset (30-year/548-name pool) is loaded, unfiltered

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the table to render (skeleton placeholder disappears)

**Expected Result:**
- The heading "Stocks" and subtitle "Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason" are visible
- A table renders with column headers including "#", "Ticker", "Sector", "Leadership", "Entry Quality", "Risk", "Setup"
- No "Backend unavailable" card appears
- The left sidebar navigation is visible
- No browser console errors

---

### UT-02 — Sort `/stocks` leaderboard by Sector ascending — no crash (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- UT-01 passed (leaderboard loaded, default rank-ascending sort)

**Steps:**
1. On `http://localhost:3255/stocks`, click the word "Sector" in the column header row
2. Observe the table and the header row

**Expected Result:**
- The table re-sorts; a small up-arrow icon appears next to "Sector" in the header (ascending indicator)
- The page does NOT crash, does not go blank, and the left sidebar navigation remains visible and clickable
- This is the exact interaction that previously threw an uncaught `TypeError` and blanked the whole app (the iter-18 regression) — it must complete cleanly now

---

### UT-03 — Sort `/stocks` leaderboard by Sector descending — no crash (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- UT-02 just executed (Sector column is the active sort, ascending)

**Steps:**
1. Click the word "Sector" in the column header again
2. Observe the table and header row

**Expected Result:**
- The sort reverses; the arrow icon flips to point down (descending indicator)
- No crash; sidebar nav still visible
- Because ~78% of rows are "Unassigned" and "Unassigned" sorts alphabetically after "Technology" but before "Utilities," a large consecutive block of "Unassigned" rows should be visible near the top of the descending list (right after any "Utilities" names, if present) — this is a good quick visual sanity check that the sort is genuinely re-ordering and not silently no-op'ing

---

### UT-04 — Sector filter dropdown lists "Unassigned" in the correct alphabetical position (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded, default state

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Click the dropdown labeled "Sector" (positioned in the filter row above the table, between the ticker/name search box and the "Setup" dropdown; it currently reads "All sectors")
3. Read through the full list of options top to bottom

**Expected Result:**
- The first option reads "All sectors"
- The remaining options are sorted alphabetically
- "Unassigned" appears in its correct alphabetical position — immediately after "Technology" and immediately before "Utilities" (assuming both are present in the current dataset)
- "Unassigned" is never rendered as a blank option or the literal text "null"

---

### UT-05 — Filter `/stocks` leaderboard by "Unassigned" (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded, default state, no filters applied

**Steps:**
1. Navigate to `http://localhost:3255/stocks` and note the row-count indicator next to the filters (format "`{visible} / {total}`", e.g. "541 / 541")
2. Open the "Sector" dropdown and select "Unassigned"

**Expected Result:**
- The table narrows to show only rows whose Sector cell reads "Unassigned"
- The count indicator updates to a smaller visible count against the same total (e.g., approximately "422 / 541" — exact figures may drift slightly with the live dataset, but the visible count must be noticeably smaller than the total)
- No row showing a real sector name (e.g., "Technology") remains visible while this filter is active

---

### UT-06 — No leaderboard row ever shows a blank Sector cell (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded, "All sectors" (no filter) selected

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Scroll through the Sector column (third column, directly after "Ticker") for at least 30 rows spread across the top, middle, and bottom of the table

**Expected Result:**
- Every row's Sector cell shows either a real GICS sector name (e.g., "Technology", "Health Care") or the literal text "Unassigned"
- No row's Sector cell is ever empty, and none shows the literal text "null"

---

### UT-07 — Evidence status badges still present on every score after the sector fix (regression — J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- `/stocks` loaded, default state

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. For the first 10 visible rows, inspect the small text directly beneath each of the Leadership, Entry Quality, and Risk score badges

**Expected Result:**
- Every one of the three scores on every inspected row shows its own evidence-status text reading "Not yet proven" (consistent with the ledger's current all-FAIL/empty state)
- No score is missing its status text
- This confirms the iter-19 sector-null fix did not disturb the evidence-status badges (a separate, earlier iteration's feature)

---

### UT-08 — `/stocks/{ticker}` shows "Unassigned" for an unmapped company (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- `/stocks` loaded; a ticker with no mapped sector is needed (discover one via the Steps below)

**Steps:**
1. On `http://localhost:3255/stocks`, open the "Sector" dropdown and select "Unassigned"
2. Click the ticker link (blue text) of the first row in the filtered list — it opens in a new browser tab at `/stocks/{TICKER}`
3. On the new tab, look at the header card: after the setup-status badge (and any pattern badges like "VCP") but before the "as of {date}" badge

**Expected Result:**
- The small muted text in that position reads "Unassigned"
- No blank value or error appears in its place
- The rest of the page (scores, chart, patterns) renders normally

---

### UT-09 — `/stocks/{ticker}` unaffected for a mapped company — NVDA still "Technology" (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- None special

**Steps:**
1. Navigate to `http://localhost:3255/stocks/NVDA`
2. Look at the same header-card position (after the setup-status badge, before the "as of" badge)

**Expected Result:**
- The text reads "Technology" (NVDA's real mapped GICS sector) — unchanged by the iter-19 fix
- The rest of the page renders normally, with no error state

---

### UT-10 — `/stocks/{ticker}` Full-history chart still renders after the prefill rewrite (regression — J-10)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`

**Preconditions:**
- A long-history ticker is available (e.g., NVDA)

**Steps:**
1. Navigate to `http://localhost:3255/stocks/NVDA`
2. Scroll to the "Price & moving averages" card
3. In its header, click the "Full history" button (the right-hand option of the "Recent" / "Full history" toggle)
4. Read the caption text to the right of the toggle buttons (format: "`{n} bars · as of {date} · history since {date}`", possibly with "`· older bars weekly-sampled`" appended)

**Expected Result:**
- The chart re-renders with a wider date range extending back toward the "history since" date shown in the caption, with no error and no blank chart area
- The "history since" date reflects NVDA's real earliest available bar (a deep date, not artificially truncated to only a few recent years)
- Clicking back to "Recent" restores the shorter bounded window without error
- (This browser check confirms the chart *renders* correctly post-rewrite — the deeper "byte-identical values" guarantee is enforced by `test_bar_cache.py`'s snapshot tests, which are backend-only and not independently checkable from the browser; that is the QA/reviewer's job, not this UI check's)

---

### UT-11 — `/scanner-runs/{runId}` Sector column shows correct labels, no blanks (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/scanner-runs/{runId}`

**Preconditions:**
- At least one scanner run exists in the run history

**Steps:**
1. Navigate to `http://localhost:3255/scanner-runs`
2. Click into any listed run (opens `/scanner-runs/{runId}`)
3. Scroll to the constituent results table and inspect its "Sector" column (third column, directly after "Ticker")

**Expected Result:**
- Every row shows either a real sector name or "Unassigned" — never a blank cell
- The page's "Immutable snapshot — as of {date}" banner still renders correctly above the table

---

### UT-12 — Cold-started `/data` loads without hanging or crashing (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Ideally: the backend process was just started/restarted (a genuinely cold cache), for the strongest signal. If a restart isn't possible in this session, a warm reload still validates correctness, though the timing won't reflect the worst-case cold path — note in the result which case was actually tested.

**Steps:**
1. (If possible) restart the backend process, then immediately:
2. Navigate to `http://localhost:3255/data`
3. Time how long it takes for the "Dataset coverage" panel to show real numbers (not a loading skeleton)

**Expected Result:**
- The page finishes loading within about 20 seconds (well inside the 60-second budget recorded in `reports/perf-budgets.md`)
- No "Backend unavailable" error card appears
- The backend process does not crash or need a manual restart during the load

---

### UT-13 — `/data` coverage numbers match between cold load and warm reload (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/data`

**Preconditions:**
- `/data` loaded successfully at least once

**Steps:**
1. Navigate to `http://localhost:3255/data` and note the values shown in the "Dataset coverage" panel: "Price history," "Universe (as of date)," "Symbols," "Trading days," "Snapshot dates," "Backfill gaps"
2. Refresh the page (F5)
3. Compare all noted values against the freshly reloaded page

**Expected Result:**
- Every value is identical between the two loads — the prefill rewrite re-serves byte-identical figures, it never recomputes a different answer between a cold and a warm read

---

### UT-14 — `/data` "Stale series" reason tile is visible and readable (happy path — part of J-12)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded successfully

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll past the "Dataset coverage" and "Rebuild snapshots for current universe" panels to reach the panel titled "Universe resolution as of {date}" (or "Universe resolution (latest)")
3. Within that panel's row of metric tiles, locate the tile labeled "Stale series" (it sits between "Below min history" and "Below min price")
4. Ensure the tile is fully visible in the viewport — scroll it into frame or use a full-page/element-clip screenshot capture (do not trust a scrolled-viewport capture; per project lesson, that can return a blank frame)

**Expected Result:**
- The "Stale series" tile shows a numeric count and, beneath it, definition text beginning "Last bar more than [N] calendar days before the as-of — the series ended or halted..."
- The tile is not clipped by the viewport edge or hidden behind another element in the captured screenshot

---

### UT-15 — `/data` Dynamic-universe membership timeline shows correct entries/exits for a mid-history IPO name (happy path — J-12; see Scope note re: correct page)

**Type:** happy-path
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- `/data` loaded successfully
- **Note:** despite the phase spec calling this "the `/methodology` membership timeline," the actual panel is on `/data`, titled "Dynamic-universe membership timeline" — see the Scope note at the top of this file.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the panel titled "Dynamic-universe membership timeline" (below "Universe resolution as of ...")
3. In the "Year" dropdown within this panel, select a year in the 2015–2023 range (likely to contain at least one recent-IPO company entering the universe)
4. Scan the "Entries" column of the resulting table for a row showing a green "+N" value followed by one or more listed ticker symbols
5. Note that ticker and its "Snapshot date"
6. Change the "Year" filter to the year (or two) immediately before the noted entry date, and/or use the "Prev" pagination button to browse a few pages of earlier snapshot dates
7. Confirm the noted ticker does NOT appear in the "Entries" column of any of those earlier rows (a reasonable spot-check of the year or two before is sufficient — it need not be an exhaustive scan of the entire history)
8. Navigate to `http://localhost:3255/stocks` and type the noted ticker into the "Search ticker or name…" box at the top of the leaderboard

**Expected Result:**
- The membership timeline table renders without error, with working Year/Month filters and Prev/Next pagination
- The noted ticker appears in an "Entries" cell on its true accrual snapshot date, and does not appear in the Entries column for the sampled earlier dates
- The same ticker is found in the current `/stocks` leaderboard via the search box, confirming it is a present, live member of today's universe (absent-before / present-after its `min_history_bars` accrual)

---

### UT-16 — Forced client-side error renders the contained `error.tsx` card with nav preserved (error)

**Type:** error
**Priority:** P1
**Surface:** all routes (`app/error.tsx`)

**Preconditions:**
- Tester has browser DevTools access (F12) and is comfortable pasting a short JS snippet into the Console — this is a tester-level check, not a plain-operator step
- `/stocks` loads successfully

**Steps:**
1. Navigate to `http://localhost:3255/stocks` and wait for the leaderboard to render
2. Open DevTools (F12) and select the "Console" tab
3. Paste the following and press Enter:
   ```js
   window.__origSort = Array.prototype.sort;
   Array.prototype.sort = function () { throw new Error("UT-16 forced test error"); };
   ```
4. Click the "Ticker" column header once (this triggers a client-side re-sort, which calls the now-patched `Array.prototype.sort` during React's render phase)

**Expected Result:**
- The leaderboard table content is replaced by a card containing a warning-triangle icon and the bold text "Something went wrong on this page," followed by "An unexpected error stopped this page from rendering. No data is lost — use the sidebar to open another page, or try this one again." and a "Try again" button (with a circular-arrow icon)
- The left sidebar navigation and top header remain visible and clickable (e.g., clicking another sidebar link still works)
- The page does NOT go fully blank/white, and the sidebar is NOT wiped out — this is the exact iter-18 failure mode this iteration fixes

**What "broken" looks like:** if the entire browser tab goes blank/white with no sidebar and no styled card (a raw, unstyled error page), the crash-containment fix has regressed.

**Cleanup (required before other tests):** in the Console, run `Array.prototype.sort = window.__origSort;` or fully reload the tab (F5) to remove the monkeypatch — leaving it in place will break sorting on every other page for the rest of the session.

---

### UT-17 — "Try again" button on the error card attempts to recover the page (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** all routes (`app/error.tsx`)

**Preconditions:**
- UT-16 has just been executed and the error card is currently showing (monkeypatch still active)

**Steps:**
1. In the DevTools Console, restore the original sort function: `Array.prototype.sort = window.__origSort;`
2. Without reloading the page, click the "Try again" button inside the currently-displayed error card

**Expected Result:**
- The error card disappears and the Stocks leaderboard re-renders successfully (a working table, not another error)
- The recovered sort order need not match whatever was selected before the crash (a fresh remount is expected to fall back to the default rank order) — the key pass condition is that the app recovers to a working page via the button, without a further crash or a manual full reload

---

### UT-18 — Root-layout failure renders the `global-error.tsx` fallback with no nav (error — dev-assisted)

**Type:** error
**Priority:** P3
**Surface:** root application shell (`app/global-error.tsx`)

**Preconditions:**
- Requires direct file-system access to the frontend source and the ability to save a file + reload/hot-reload the dev server — this is a developer-assisted verification step, not a plain browser-only check, because `global-error.tsx` only activates when the root layout itself throws, which cannot be triggered through normal navigation or DevTools alone.

**Steps:**
1. Open `apps/frontend/app/layout.tsx` in an editor
2. Temporarily add a line that unconditionally throws near the top of the layout component's function body (before its `return`), e.g. `throw new Error("UT-18 forced root layout error");`
3. Save the file and reload any page in the browser, e.g. `http://localhost:3255/stocks`
4. Observe the result

**Expected Result:**
- The entire browser tab is replaced by a standalone page with NO sidebar navigation and NO header — just a centered card reading the bold text "Trendora hit an unexpected error," followed by "The application failed to render. No data is lost — reloading usually recovers; if it keeps happening, note what you were doing and report it," and a "Try again" button
- This confirms `global-error.tsx` is correctly wired as the nav-free last-resort fallback, distinct from the per-page `error.tsx` card (which keeps the sidebar)

**Cleanup (required):** remove the forced `throw` from `app/layout.tsx`, save again, and confirm `/stocks` loads normally afterward.

---

### UT-19 — New copy introduced this iteration contains no prohibited financial-advice language (UX — anti-goal #2)

**Type:** ux
**Priority:** P2
**Surface:** `/stocks` (Unassigned label) + `app/error.tsx` + `app/global-error.tsx`

**Preconditions:**
- None special (can be done by direct inspection once the copy is known; UT-16/UT-18 confirm the error copy live if desired)

**Steps:**
1. Re-read the confirmed `error.tsx` card text: "Something went wrong on this page" / "An unexpected error stopped this page from rendering. No data is lost — use the sidebar to open another page, or try this one again." / "Try again"
2. Re-read the confirmed `global-error.tsx` text: "Trendora hit an unexpected error" / "The application failed to render. No data is lost — reloading usually recovers; if it keeps happening, note what you were doing and report it." / "Try again"
3. On `/stocks`, read the "Unassigned" option/label text wherever it appears (filter dropdown, table cell, sector chip)
4. Check all of the above strings for any of: a price target or dollar figure implying future value, the words "buy"/"sell"/"should invest"/"guaranteed"/"will rise"/"will fall," or any promise of a return or outcome

**Expected Result:**
- None of the new copy contains a buy/sell recommendation, a price target, a return promise, or an alpha/edge claim
- "Unassigned" reads as a neutral classification label, not a performance claim
- The error-card copy is limited to describing the technical failure and recovery option ("No data is lost," "reloading usually recovers") — it makes no claim about the user's positions, returns, or market outlook

---

### UT-20 — `/evidence` renders claim rows/empty-state and regime labels correctly (regression — J-04/J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`

**Preconditions:**
- `/evidence` page accessible

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Confirm the heading "Evidence" and its subtitle (mentioning "the single source of proven-ness") are visible
3. Observe the page content: either (a) a card titled "No certified claims yet" with a bulleted list of exactly 5 fields — "Hypothesis," "Out-of-sample verdict," "Control comparison (vs SPY)," "Registration date," "Forward-walk score-to-date" — or (b) one or more claim rows, each showing a status badge plus a title
4. If any claim row is visible, check whether it carries a second badge reading "Regime: {label}" next to its status badge

**Expected Result:**
- The page renders without a "Backend unavailable" error
- Either the "No certified claims yet" empty state renders completely (all 5 field bullets visible), or every visible claim row shows a readable status badge and title
- Any regime-conditioned claim row shows a "Regime: {label}" badge where `{label}` is a recognizable regime name (e.g., "Strong risk-on," "Risk-on," "Defensive," "Risk-off," or a similar breadth-based label) — never blank, never "Regime: null" or "Regime: undefined"

---

### UT-21 — `/evidence` shows no "Proven"/PASS status anywhere — all-FAIL ledger state preserved (regression — J-11)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`, `/stocks`, `/stocks/{ticker}`

**Preconditions:**
- Same as UT-20

**Steps:**
1. On `http://localhost:3255/evidence`, inspect every visible status badge (or the empty-state's "Not yet proven" text)
2. Navigate to `http://localhost:3255/stocks` and inspect the evidence-status text beneath each of the Leadership/Entry Quality/Risk score badges for the first 10 visible rows
3. Navigate to `http://localhost:3255/stocks/NVDA` and inspect the evidence-status text beneath its three score cards

**Expected Result:**
- No badge or status text anywhere reads "PASS" or "Proven" — every score's evidence status reads "Not yet proven," and every `/evidence` claim row (if any exist) shows a status badge reading "FAIL" or "INSUFFICIENT," never "PASS"
- This confirms the certified-claims ledger remains honestly all-FAIL/empty after this iteration's basis and reliability changes — no stale "Proven" value has leaked through anywhere

---

### UT-22 — Watchlist: adding an unknown ticker shows a clear inline error, no row added (error — deferred iter-18 check)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3255/watchlist`
2. Note the current number of rows in the watchlist table (or confirm the "Your watchlist is empty" state if none exist)
3. In the "Ticker" field (placeholder "e.g. ANET"), type a ticker that does not exist in the universe, e.g. "ZZZZZ"
4. Click the "Add" button (the button with the plus icon)

**Expected Result:**
- A red inline message (with a warning-triangle icon) appears directly below the Add form, inside the same card, describing the failure (exact wording depends on the backend's response — it must not fail silently with no message)
- The watchlist table's row count is unchanged from step 2 — no new row for "ZZZZZ" is added

---

### UT-23 — Watchlist: adding a duplicate ticker shows a clear inline error, no second row added (error — deferred iter-18 check)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- At least one ticker is already saved in the watchlist. If the list is empty, add one first: type a real ticker (e.g. "AAPL") into the "Ticker" field and click "Add," and confirm it appears in the table before proceeding.

**Steps:**
1. Navigate to `http://localhost:3255/watchlist` and confirm at least one entry (e.g. "AAPL") is present in the table
2. In the "Ticker" field, type the SAME ticker already in the table
3. Click the "Add" button

**Expected Result:**
- A red inline error message appears below the form (same card, warning-triangle icon), indicating the ticker is already saved / a duplicate
- The table still shows exactly one row for that ticker afterward — never two

---

### UT-24 — Backtest: as-of date floor at 2005-02-25 is enforced, no crash on an out-of-range date (validation — deferred iter-18 check)

**Type:** validation
**Priority:** P2
**Surface:** `/backtest`

**Preconditions:**
- Frontend running; tester has access to the global as-of date switcher (in the site header/top bar, shared across every page — `/backtest` holds no date state of its own)

**Steps:**
1. Navigate to `http://localhost:3255/backtest`
2. Locate the global as-of date control in the site header
3. Attempt to set the as-of date earlier than 2005-02-25 (e.g., try 2000-01-01), either through the picker's own input restriction or, if it accepts free entry, via a direct URL such as `http://localhost:3255/backtest?asof=2000-01-01`
4. Observe the result

**Expected Result:**
- The app does not crash and does not show a blank page
- Either (a) the date picker itself prevents selecting/entering a date before 2005-02-25, or (b) if an out-of-range date is forced via URL, the app clamps to the nearest valid date or shows a clear "no data" / empty-state message for that date — it never fabricates a scorecard for a date with no underlying data
- The "Viewing as-of {date} (historical)" badge (clock/history icon) reflects whatever date was actually resolved, never a phantom date with invented figures

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/stocks` loads on default null-heavy state | smoke | P1 | `/stocks` |
| UT-02 | Sort Sector ascending, no crash | happy-path | P1 | `/stocks` |
| UT-03 | Sort Sector descending, no crash | happy-path | P1 | `/stocks` |
| UT-04 | Sector filter lists "Unassigned" alphabetically | ux | P2 | `/stocks` |
| UT-05 | Filter leaderboard by "Unassigned" | happy-path | P1 | `/stocks` |
| UT-06 | No blank Sector cells | validation | P2 | `/stocks` |
| UT-07 | Evidence badges present after sector fix | regression | P1 | `/stocks` |
| UT-08 | Unmapped company shows "Unassigned" chip | happy-path | P1 | `/stocks/{ticker}` |
| UT-09 | Mapped company (NVDA) unaffected | regression | P1 | `/stocks/{ticker}` |
| UT-10 | Full-history chart renders post-rewrite | regression | P1 | `/stocks/{ticker}` |
| UT-11 | Scanner run Sector column correct | happy-path | P2 | `/scanner-runs/{runId}` |
| UT-12 | Cold `/data` load, no hang/crash | smoke | P1 | `/data` |
| UT-13 | `/data` coverage numbers stable cold vs warm | validation | P2 | `/data` |
| UT-14 | "Stale series" tile visible and readable | happy-path | P1 | `/data` |
| UT-15 | Membership timeline entries/exits (mid-history IPO) | happy-path | P1 | `/data` |
| UT-16 | Forced client error → contained `error.tsx` card | error | P1 | all routes |
| UT-17 | "Try again" recovers the page | happy-path | P2 | all routes |
| UT-18 | Root-layout failure → `global-error.tsx` fallback | error | P3 | root shell |
| UT-19 | New copy has no anti-goal-#2 language | ux | P2 | `/stocks` + error boundaries |
| UT-20 | `/evidence` rows + regime label render | regression | P1 | `/evidence` |
| UT-21 | No "Proven"/PASS anywhere (all-FAIL preserved) | regression | P1 | `/evidence`, `/stocks`, `/stocks/{ticker}` |
| UT-22 | Watchlist unknown-ticker error, no row added | error | P2 | `/watchlist` |
| UT-23 | Watchlist duplicate-ticker error, no 2nd row | error | P2 | `/watchlist` |
| UT-24 | Backtest as-of floor at 2005-02-25 | validation | P2 | `/backtest` |

**P1 tests must all pass for browser QA verdict to be PASS.** P1 count: 14 (UT-01, 02, 03, 05, 07, 08, 09,
10, 12, 14, 15, 16, 20, 21) — these cover the two headline fixes (sector-sort crash, `/data` OOM), the
crash-containment card, and every required-still-passing regression journey (J-03/J-04/J-05/J-10/J-11).
