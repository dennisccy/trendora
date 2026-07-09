# Phase goal-mcp-loop-iter-25 — UI Test Plan

**Phase:** goal-mcp-loop-iter-25
**Date:** 2026-07-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3255
**Backend URL:** http://localhost:8255

---

## Context

This iteration shipped **zero new UI**. It exists to prove — live, in a browser, not just by code inspection — that a previously-committed one-line fix (`mmap_size_bytes: 0`) actually stops the backend from crashing the very first time `/data` is opened right after a restart. Every page in the product is byte-identical to the prior iteration. Because of that, this test plan is unusually regression-heavy: most of it is re-confirming that things which were never touched still work, rather than testing something new.

**Priority note:** the skill's default priority table marks most "regression" tests P3 (low risk). That default is overridden here for UT-02, UT-03, UT-05, UT-06, and UT-08–UT-14: the phase's own Definition of Done names each of these as a required, freshly-live-replayed gate this iteration (not a low-risk nice-to-check), so they are marked **P1**. A failure on any of them blocks the phase.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/data` loads normally on an already-warm backend (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/data`

**Preconditions:**
- Both backend (`:8255`) and frontend (`:3255`) are already running in prod mode and have been reachable for at least a minute (this is the ordinary warm case — the cold-restart scenario is tested separately in UT-02/UT-03)

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Wait for the loading skeleton to disappear

**Expected Result:**
- The "Data Manager" heading is visible at the top, with subtitle text beginning "Grow the dataset on demand — view coverage and gaps..."
- The "Dataset coverage" panel, "Storage footprint" panel, and "Per-date availability" heatmap are all visible with populated values
- No blank page and no red-bordered "Backend unavailable" card appears
- No errors in the browser console

---

### UT-02 — Cold-restart `/data` load does not crash the backend — run 1 (regression, THE CRUX)

**Type:** regression
**Priority:** P1 — named "the crux" verbatim in the phase spec; this is the entire reason iter-25 exists
**Surface:** `/data`

**Preconditions:**
- `apps/frontend/.next` has been freshly rebuilt (deleted and rebuilt) before this test so no stale build masks real behavior
- Both services are running in **prod mode** (`scripts/start-backend.sh` / `scripts/start-frontend.sh` — never `dev.sh`)
- The tester (or the browser-qa-agent) has terminal/process access to stop and restart the backend process — this specific test is unavoidably more than pure clicking, because the fix being verified only manifests at the moment of a cold restart

**Steps:**
1. Fully stop the backend process (kill the `uvicorn` process serving `:8255`) and confirm `http://localhost:8255/api/health` no longer responds
2. Cold-start the backend fresh via `scripts/start-backend.sh`
3. Immediately open a **new** browser tab and navigate to `http://localhost:3255/data` as the very first request against this freshly-started backend — do not open any other page or tab first
4. Time how long the page takes to finish loading
5. Once `/data` has finished loading, open a second tab and navigate to `http://localhost:3255/stocks`

**Expected Result:**
- Step 3–4: `/data` finishes loading within roughly 10 seconds. The "Dataset coverage" panel, "Storage footprint" panel (`data-testid="storage-capacity-panel"` — "Database file", "Price bars", "Scanner rows", "Forward returns" all populated), and "Per-date availability" heatmap all render with real numbers
- No blank white page, no browser connection-refused/"can't reach this page" error, no red "Backend unavailable" card
- Step 5: `/stocks` also loads successfully — this proves the whole backend **process** survived, not just that one lucky request slipped through (an `/api/health` check alone is not sufficient proof — it is a different code path per the carried-forward session lesson)

---

### UT-03 — Cold-restart `/data` load does not crash the backend — run 2, confirms the fix is not a fluke (regression, THE CRUX repeat)

**Type:** regression
**Priority:** P1
**Surface:** `/data`

**Preconditions:** Same as UT-02; run immediately after UT-02 completes, on the same freshly-rebuilt frontend.

**Steps:**
1. Repeat UT-02's steps 1–5 exactly, a second time (stop the backend completely, cold-start it, load `/data` as the first request, then confirm `/stocks` also loads)

**Expected Result:**
- Identical outcome to UT-02: `/data` loads within ~10 seconds with real data, the backend process stays alive, and `/stocks` also loads afterward
- No degradation between the two runs — the fix holds consistently, not as a one-time fluke (the phase spec requires "at least twice")

---

### UT-04 — Storage footprint card shows correct values after a cold start (happy-path)

**Type:** happy-path
**Priority:** P1 — named "Storage card (P1)" verbatim in the phase spec's Testing Requirements
**Surface:** `/data`

**Preconditions:** `/data` has just finished loading from a cold start (continue directly from UT-02 or UT-03 — do not restart again).

**Steps:**
1. On the loaded `/data` page, locate the "Storage footprint" panel (it has a database icon beside its heading, directly below "Dataset coverage")
2. Read the four values shown: "Database file", "Price bars", "Scanner rows", "Forward returns"

**Expected Result:**
- All four values are populated — none show "—" or a blank space
- "Database file" reads approximately **1.22 GB** (≈1,307,414,528 bytes)
- "Price bars" reads approximately **3,293,160**; "Scanner rows" reads approximately **165,755**; "Forward returns" reads approximately **821,054**
- Exact match is not required if new data has since been fetched/backfilled — the pass criterion is real, non-fabricated numbers in this range, never a placeholder or zero on a database that clearly has data

---

### UT-05 — Dataset coverage panel (including the backfill-gap diagnostic) renders real content after cold start (regression)

**Type:** regression
**Priority:** P1 — part of the DoD's required flip-to-PASS sequence for the missing-data/coverage diagnostic
**Surface:** `/data`

**Preconditions:** `/data` has just finished loading from a cold start.

**Steps:**
1. On the loaded `/data` page, locate the "Dataset coverage" panel (above the Storage footprint panel)
2. Read the "Price history", "Universe (as of date)", "Candidate universe", "Symbols", "Trading days", "Snapshot dates", and "Backfill gaps" tiles

**Expected Result:**
- Every tile shows a real value (a date range or a number) — none show a stuck loading spinner, a blank tile, or a generic error in place of a number
- The "Backfill gaps" tile shows a number (0 or more) with its definition sentence visible underneath: "A backfill gap is a trading day that HAS bars but NO scanner snapshot — the actionable backfill targets."
- If the gap count is greater than 0, the paragraph below the tiles also shows a "Gap range:" date span

---

### UT-06 — Contained "Backend unavailable" error card when the backend is stopped and left down (error, anti-goal #8)

**Type:** error
**Priority:** P1 — anti-goal #8 explicitly requires "never a blank application-error page"; this is the negative-path half of the same flip-to-PASS sequence as UT-02/03
**Surface:** `/data`

**Preconditions:** Backend is stopped and, unlike UT-02/UT-03, is intentionally **not** restarted for this test.

**Steps:**
1. Confirm the backend is stopped (`http://localhost:8255/api/health` does not respond)
2. In the browser, navigate to `http://localhost:3255/data`
3. Wait a few seconds for the page to settle

**Expected Result:**
- Exactly ONE contained error card renders with a red/warning border, reading (bold) "Backend unavailable" followed by "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- The rest of the page shell (heading, layout, navigation) still renders around the card — this is NOT a blank white screen and NOT the browser's own generic network-error page
- No more than one error card is stacked or duplicated
- No uncaught JavaScript exception appears in the browser console

---

### UT-07 — Data Manager is reachable and its states read clearly to a non-technical user (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation → `/data`

**Preconditions:** Backend and frontend both running normally (warm state, as in UT-01).

**Steps:**
1. Navigate to `http://localhost:3255` (the Dashboard/home page)
2. Look at the main navigation for an entry reaching the Data Manager page
3. Click that navigation entry

**Expected Result:**
- The navigation entry pointing at `/data` is visible without scrolling or opening a submenu — reachable within one click from the home page
- Clicking it navigates to `http://localhost:3255/data`, and the "Data Manager" heading is visible
- Every metric tile on the page carries its own plain-language definition sentence directly beneath its number (e.g., "Backfill gaps" is explained inline as a day with bars but no scanner snapshot) — a first-time, non-technical reader is not left guessing what a figure means

---

## Required-Still-Passing Journeys — Fresh Regression Replay

<!-- These journeys' pages were not modified this iteration, but iter-24's crash aborted their replay,
     so the phase spec requires each to be freshly LIVE-replayed (not carried over) this iteration. -->

### UT-08 — `/stocks` leaderboard loads with full membership count and sector-sort works (J-01, smoke)

**Type:** regression
**Priority:** P1 — explicit required-still-passing DoD item
**Surface:** `/stocks`
**Journey:** J-01

**Preconditions:** Backend running (can be the same instance left up after UT-02/03); at least one full scan snapshot exists.

**Steps:**
1. Navigate to `http://localhost:3255/stocks`
2. Wait for the leaderboard table to finish loading
3. Locate the membership-count indicator near the table header (expect "541/541" or equivalent "X of Y" phrasing)
4. Click the "Sector" column header to sort by sector

**Expected Result:**
- The leaderboard renders without error, showing a membership count of 541/541 (the two numbers must match each other — no partial or truncated list)
- Clicking the Sector header sorts the table by sector without a page crash, blank table, or JavaScript console error

---

### UT-09 — Unproven signals stay labeled "Not yet proven," never shown as confident (J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`, `/evidence`
**Journey:** J-03

**Preconditions:** Backend running; leaderboard loaded.

**Steps:**
1. On `http://localhost:3255/stocks`, locate any row's score/edge badge
2. Confirm the badge reads "Not yet proven" rather than an unqualified confident-looking number
3. Navigate to `http://localhost:3255/evidence`
4. Scan the ledger rows

**Expected Result:**
- Every score on `/stocks` lacking a certified out-of-sample pass is labeled "Not yet proven" — no score is presented as a proven edge without backing
- `/evidence` shows no row claiming a proven/certified status without an actual passing verdict attached

---

### UT-10 — Dashboard regime panel links through to the evidence ledger (J-04)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Dashboard), `/evidence`
**Journey:** J-04

**Preconditions:** Backend running.

**Steps:**
1. Navigate to `http://localhost:3255` (Dashboard)
2. Locate the market-regime panel
3. Click the link/button on that panel pointing to the evidence ledger

**Expected Result:**
- The Dashboard's regime panel renders a regime label without error
- Clicking the evidence link navigates to `http://localhost:3255/evidence`, and the ledger table is visible (not a 404 or blank page)

---

### UT-11 — Evidence ledgers show an honest all-FAIL state with no stale edge (J-05 / J-11)

**Type:** regression
**Priority:** P1
**Surface:** `/evidence`
**Journey:** J-05, J-11

**Preconditions:** Backend running; per goal.md, no claim has yet passed the referee, so an all-FAIL ledger is the currently-expected honest state.

**Steps:**
1. Navigate to `http://localhost:3255/evidence`
2. Read every row's out-of-sample verdict column
3. Look across the whole page for any badge or indicator suggesting a currently-active "edge" without a passing verdict attached

**Expected Result:**
- All ledger rows show a FAIL (or explicit "not yet proven"/pending) verdict — none show an unqualified PASS/proven claim
- No stale or leftover "edge" indicator appears anywhere on the page from a previous run — the ledger is honestly clear of any proven claim

---

### UT-12 — Full/Recent history toggle on a stock detail page still works (J-10)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks/{ticker}`
**Journey:** J-10

**Preconditions:** Backend running; a long-tenured ticker (e.g. AAPL) exists in the universe.

**Steps:**
1. Navigate to `http://localhost:3255/stocks/AAPL`
2. Locate the price chart and the "Full" / "Recent" history toggle near it
3. Click "Full"
4. Click "Recent"

**Expected Result:**
- Clicking "Full" expands the chart to show deep history (dates well before 2015 visible on the x-axis) without a crash or blank chart
- Clicking "Recent" collapses back to the shorter recent window without error
- No console error during either toggle

---

### UT-13 — `/data`'s symbol count matches `/stocks`'s leaderboard count (J-12)

**Type:** regression
**Priority:** P1
**Surface:** `/data`, `/stocks`
**Journey:** J-12

**Preconditions:** Backend running; both pages read from the same backend instance.

**Steps:**
1. Navigate to `http://localhost:3255/data` and read the "Universe (as of date)" value in the "Dataset coverage" panel
2. Navigate to `http://localhost:3255/stocks` and read the leaderboard's membership count

**Expected Result:**
- The number on `/data`'s "Universe (as of date)" tile equals the number on `/stocks`'s leaderboard count (541, or the current committed count) — the two pages agree with no discrepancy

---

### UT-14 — Index/macro benchmark series still disclose their data vendor (J-14)

**Type:** regression
**Priority:** P1
**Surface:** `/data` (Index & Macro vendor panel)
**Journey:** J-14

**Preconditions:** Backend running.

**Steps:**
1. Navigate to `http://localhost:3255/data`
2. Scroll to the index/benchmark/macro vendor-disclosure panel (it sits below the "Per-date availability" heatmap and the missing-data section; it reads the same index/macro payload the Dashboard's index chart uses)
3. Locate the SPX and VIX series entries in that panel

**Expected Result:**
- Each series discloses its data vendor in its label or tooltip (e.g., an "(Stooq)"/"(Yahoo)"-style vendor attribution) — no unlabeled "mystery" series
- Any macro proxy series (e.g. TNX, DXY, VXN) is labeled as a proxy/macro series, never presented as if it were a primary market index

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/data` loads on a warm backend | smoke | P1 | `/data` |
| UT-02 | Cold-restart `/data` survives — run 1 (crux) | regression | P1 | `/data` |
| UT-03 | Cold-restart `/data` survives — run 2 (crux) | regression | P1 | `/data` |
| UT-04 | Storage footprint card values correct | happy-path | P1 | `/data` |
| UT-05 | Coverage/backfill-gap diagnostic renders | regression | P1 | `/data` |
| UT-06 | Single contained "Backend unavailable" card | error | P1 | `/data` |
| UT-07 | Data Manager discoverable, states clear | ux | P2 | nav → `/data` |
| UT-08 | `/stocks` leaderboard + sector-sort (J-01) | regression | P1 | `/stocks` |
| UT-09 | "Not yet proven" labeling intact (J-03) | regression | P1 | `/stocks`, `/evidence` |
| UT-10 | Dashboard regime → evidence link (J-04) | regression | P1 | `/`, `/evidence` |
| UT-11 | Evidence ledgers all-FAIL, no stale edge (J-05/J-11) | regression | P1 | `/evidence` |
| UT-12 | Full/Recent history toggle (J-10) | regression | P1 | `/stocks/{ticker}` |
| UT-13 | `/data` count == `/stocks` count (J-12) | regression | P1 | `/data`, `/stocks` |
| UT-14 | Index/macro vendor disclosure (J-14) | regression | P1 | `/data` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Not applicable this iteration:** no dedicated Validation-type test case is included. Per the skill's own rule ("one test per form that was added or changed"), zero forms were added or changed this iteration — the Data Manager job form is untouched and out of scope.
