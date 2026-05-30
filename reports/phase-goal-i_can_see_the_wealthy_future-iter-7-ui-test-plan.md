# Phase goal-i_can_see_the_wealthy_future-iter-7 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-7
**Date:** 2026-05-30
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3836

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Surface under test: the /watchlist route (J-11) — the product's first user-write surface. -->

---

### UT-01 — Watchlist page loads with empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- Frontend running at http://localhost:3836; backend running.
- Watchlist DB is empty (no `ANET` or any entry saved).

**Steps:**
1. Navigate to `http://localhost:3836/watchlist`
2. Wait for the page to fully load (loading skeleton clears).

**Expected Result:**
- The heading "Watchlist" is visible with its subtitle describing a research save-list.
- An Add panel card is visible containing a "Ticker" field, a "Reason" field, and an "Add" button.
- Below the Add panel, the empty state shows the star icon with the title "Your watchlist is empty" and description text mentioning date added, reason, Leadership / Entry / Risk, setup, price-since-added and invalidation.
- NO entries table is rendered. NO "Backend unavailable" card. No console errors.

---

### UT-02 — User can add a stock and see its row (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- On `http://localhost:3836/watchlist`, watchlist empty, backend running.
- `ANET` is a valid universe ticker.

**Steps:**
1. Navigate to `http://localhost:3836/watchlist`
2. Type `ANET` into the "Ticker" field (placeholder "e.g. ANET").
3. Type `ANET — strong leader, watching pullback` into the "Reason" field (placeholder "Why are you watching it?").
4. Click the "Add" button.
5. Wait for the list to refresh.

**Expected Result:**
- The "Ticker" and "Reason" fields both clear back to empty.
- A "as of <date>" badge and a "1 saved" count appear above a new entries table.
- A table row appears whose Ticker cell reads `ANET` (rendered as an accent-colored link), Added cell shows a date (YYYY-MM-DD), Reason cell shows the typed reason text, Leadership / Entry Quality / Risk cells each show a ScoreBadge (A–E letter + 0–100 number), Setup cell shows a status badge, Since added cell shows a signed percentage, and Invalidation cell shows a note.
- NO red inline error appears.

---

### UT-03 — Single-source: watchlist scores match the /stocks leaderboard (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist` vs `/stocks`

**Preconditions:**
- `ANET` is present on the watchlist (UT-02 done).

**Steps:**
1. Navigate to `http://localhost:3836/stocks`.
2. Locate the `ANET` row; note its Leadership, Entry Quality, and Risk badge values (letter bucket + number).
3. Navigate to `http://localhost:3836/watchlist`.
4. Locate the `ANET` row; compare its Leadership, Entry Quality, and Risk badge values against step 2.

**Expected Result:**
- The Leadership, Entry Quality, and Risk badge bucket-letters and numbers on `/watchlist` are identical to those on `/stocks` for `ANET`.
- The Risk badge color reads as danger (red) for a high-danger value (Risk uses inverted coloring).

---

### UT-04 — "Since added" shows an honest 0.00% on the frozen seed (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- `ANET` just added against the frozen seed (UT-02), no prior entry_close history.

**Steps:**
1. Navigate to `http://localhost:3836/watchlist`.
2. Read the "Since added" cell of the `ANET` row.

**Expected Result:**
- The cell reads `+0.00%` or `0.00%`, rendered in muted (neutral) text — NOT green, NOT red.
- The cell does NOT read `NaN`, blank, or any fabricated non-zero figure.

---

### UT-05 — Invalidation cell matches the stock detail verbatim (regression / single-source)

**Type:** regression
**Priority:** P2
**Surface:** `/watchlist` vs `/stocks/ANET`

**Preconditions:**
- `ANET` present on the watchlist.

**Steps:**
1. Navigate to `http://localhost:3836/watchlist`; read the `ANET` row's Invalidation cell text (hover to see the full tooltip if truncated).
2. Navigate to `http://localhost:3836/stocks/ANET`; read the invalidation note on the detail page.
3. Compare the two strings.

**Expected Result:**
- The Invalidation text on the watchlist row is identical to the invalidation note on `/stocks/ANET` (e.g., the same "Invalid below the 50-DMA at $X" string).

---

### UT-06 — Ticker link navigates to stock detail (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist` → `/stocks/[ticker]`

**Preconditions:**
- `ANET` present on the watchlist.

**Steps:**
1. Navigate to `http://localhost:3836/watchlist`.
2. Click the `ANET` ticker link in the first table column.

**Expected Result:**
- The browser navigates to `http://localhost:3836/stocks/ANET`.
- The ANET stock detail page loads (heading shows ANET).

---

### UT-07 — Remove deletes the row without a page reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- `ANET` is the only entry on the watchlist.

**Steps:**
1. Navigate to `http://localhost:3836/watchlist`.
2. Click the Remove button (trash icon, far-right column, aria-label "Remove ANET from the watchlist") on the `ANET` row.
3. Wait for the list to refresh.

**Expected Result:**
- The `ANET` row disappears from the table.
- Because it was the only entry, the table and the "as of" / "N saved" badges are replaced by the empty state ("Your watchlist is empty").
- The page did NOT do a full browser reload (no flash/URL change).

---

### UT-08 — Unknown ticker is rejected with an inline error (error)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- On `http://localhost:3836/watchlist`; `ZZZZ` is not in the universe.

**Steps:**
1. Type `ZZZZ` into the "Ticker" field.
2. Type `not real` into the "Reason" field.
3. Click the "Add" button.

**Expected Result:**
- A red inline error message (with a warning triangle icon, `role="alert"`) appears under the Add panel carrying the backend's explicit message (e.g., not a known ticker).
- NO `ZZZZ` row is added to the table.
- The Ticker/Reason fields are NOT cleared (the add failed).

---

### UT-09 — Duplicate ticker is rejected, no duplicate row (error)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- `ANET` is already on the watchlist (add it first if needed).

**Steps:**
1. On `http://localhost:3836/watchlist`, type `ANET` into the "Ticker" field.
2. Type `second attempt` into the "Reason" field.
3. Click the "Add" button.

**Expected Result:**
- A red inline error appears (e.g., "already on the watchlist").
- The table still shows exactly ONE `ANET` row; the count badge still reads "1 saved" (no duplicate created).

---

### UT-10 — Add button is disabled when Ticker is empty (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- On `http://localhost:3836/watchlist`, both fields empty.

**Steps:**
1. Leave the "Ticker" field empty.
2. Type any text (e.g., `just a reason`) into the "Reason" field.
3. Observe the "Add" button.
4. Attempt to click the "Add" button.

**Expected Result:**
- The "Add" button is visibly disabled (reduced opacity, not-allowed cursor) while the Ticker field is empty.
- Clicking it does nothing — no row is added and no error appears.

---

### UT-11 — Reason is optional: add succeeds with ticker only (validation)

**Type:** validation
**Priority:** P3
**Surface:** `/watchlist`

**Preconditions:**
- On `http://localhost:3836/watchlist`; `ANET` not yet present.

**Steps:**
1. Type `ANET` into the "Ticker" field.
2. Leave the "Reason" field empty.
3. Click the "Add" button.

**Expected Result:**
- The `ANET` row is added successfully (Add is enabled once Ticker is non-empty).
- The Reason cell of the new row shows a muted em-dash `—` placeholder instead of crashing or showing "undefined".

---

### UT-12 — Backend-unavailable shows an honest error card, no fabricated rows (error)

**Type:** error
**Priority:** P2
**Surface:** `/watchlist`

**Preconditions:**
- The backend (`:8835`) is stopped / unreachable.

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3836/watchlist`.
2. Wait for the loading skeleton to clear.

**Expected Result:**
- A red "Backend unavailable" card appears with the message that the watchlist could not load from the API and that no entries are shown rather than fabricated values.
- NO entries table and NO fabricated rows are shown.
- NO empty-state star card is shown (this is the error state, not the zero-entry state).

---

### UT-13 — Entry survives a backend restart (regression / persistence crux)

**Type:** regression
**Priority:** P1
**Surface:** `/watchlist`

**Preconditions:**
- `ANET` present on the watchlist (added via UT-02).
- Operator can restart the backend service.

**Steps:**
1. Confirm the `ANET` row is visible at `http://localhost:3836/watchlist`.
2. Restart the backend: stop the uvicorn process on `:8835`, then start it again via `bash scripts/start-backend.sh`; wait until `http://localhost:8835/api/health` returns ok.
3. Reload `http://localhost:3836/watchlist` (F5).

**Expected Result:**
- The `ANET` row is still present after the restart, with the same Added date and Reason as before.
- This confirms the watchlist is DB-backed, not held in memory.

---

### UT-14 — Watchlist is reachable from the sidebar (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / sidebar

**Preconditions:**
- On any page, e.g. `http://localhost:3836` (dashboard).

**Steps:**
1. Navigate to `http://localhost:3836`.
2. Look at the left navigation sidebar.
3. Click the "Watchlist" link.

**Expected Result:**
- A "Watchlist" link is visible in the sidebar.
- Clicking it navigates to `http://localhost:3836/watchlist` and renders the working Watchlist page (Add panel + heading), not a "coming soon" stub.

---

### UT-15 — Prior journeys still render (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`, `/stocks`, `/sectors`

**Preconditions:**
- Both services running.

**Steps:**
1. Navigate to `http://localhost:3836` — dashboard loads with regime info.
2. Navigate to `http://localhost:3836/stocks` — leaderboard table renders with ScoreBadge values.
3. Navigate to `http://localhost:3836/sectors` — sector leaderboard renders.

**Expected Result:**
- All three prior pages load without errors and show their data as before this phase — no regression from the additive watchlist work.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads with empty state | smoke | P1 | `/watchlist` |
| UT-02 | Add a stock, see its row | happy-path | P1 | `/watchlist` |
| UT-03 | Scores match /stocks (single-source) | happy-path | P1 | `/watchlist` vs `/stocks` |
| UT-04 | Honest 0.00% Since added | happy-path | P2 | `/watchlist` |
| UT-05 | Invalidation matches detail | regression | P2 | `/watchlist` vs `/stocks/ANET` |
| UT-06 | Ticker link → stock detail | happy-path | P1 | `/watchlist` → `/stocks/[ticker]` |
| UT-07 | Remove deletes the row | happy-path | P1 | `/watchlist` |
| UT-08 | Unknown ticker rejected | error | P2 | `/watchlist` |
| UT-09 | Duplicate ticker rejected | error | P2 | `/watchlist` |
| UT-10 | Add disabled when ticker empty | validation | P2 | `/watchlist` |
| UT-11 | Reason optional | validation | P3 | `/watchlist` |
| UT-12 | Backend-unavailable error card | error | P2 | `/watchlist` |
| UT-13 | Survives backend restart | regression | P1 | `/watchlist` |
| UT-14 | Reachable from sidebar | ux | P3 | navigation |
| UT-15 | Prior journeys still render | regression | P1 | `/`, `/stocks`, `/sectors` |

**P1 tests must all pass for browser QA verdict to be PASS.**
