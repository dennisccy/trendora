# Phase goal-i_can_see_the_wealthy_future_forever-iter-15 — UI Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Date:** 2026-06-03
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3835

---

## Scope

This iteration is **frontend-only** and makes synthesis journey **J-31** navigable:
- `/research` Setup & Pattern Lab gains a cross-link **"View the names expressing this on the leaderboard →"**.
- `/stocks` Sector / Setup / Pattern filters are now carried in the URL query string — deep-linkable, shareable, and reflected back to the address bar as the dropdowns change.
- Robustness: a bad / unknown `pattern` param falls back to "all"; zero-match deep-links show the honest empty-state; exactly one date control remains (the global as-of switcher — no `as_of` filter param).

No backend, endpoint, value, or computation changed. These UI tests do **not** duplicate the API/artifact checks in the functional test plan (TC-07/TC-08/TC-09).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/research` loads with the cross-link present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/research`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend reachable (the Factor/Event-Study labs read live data)

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Wait for the page to fully load (the loading skeletons disappear)
3. Scroll down to the card titled **"Setup & Pattern Lab — event study"**

**Expected Result:**
- The page renders with the heading "Research — Factor Lab" at the top; no blank screen, no error card
- The "Setup & Pattern Lab — event study" card is visible with a **Subject** dropdown
- The accent link **"View the names expressing this on the leaderboard →"** is visible inside that card, with a grey caption beginning "completes the synthesis path — lab evidence →…"
- No console errors

---

### UT-02 — `/stocks` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running at http://localhost:3835
- Backend reachable

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Wait for the page to fully load (a brief skeleton may flash, then the table appears)

**Expected Result:**
- The page renders with the heading "Stocks"
- A blue **"as of YYYY-MM-DD"** badge is visible, followed by three dropdowns labelled **Sector**, **Setup**, **Pattern**, and a "N / M" count (e.g. "42 / 42")
- A ranked table with columns "# · Ticker · Sector · Leadership · Entry Quality · Risk · Setup · Reason" is shown
- The address bar stays `http://localhost:3835/stocks` (no query string added on a clean load)
- No console errors, in particular NO "useSearchParams() should be wrapped in a suspense boundary" error

---

### UT-03 — Pattern cross-link navigates to a pre-filtered leaderboard (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/stocks`

**Preconditions:**
- On `http://localhost:3835/research`, page loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the "Setup & Pattern Lab — event study" card, open the **Subject** dropdown and select the pattern **"Pullback to rising DMA"** (under the "Patterns" group)
3. Wait for the event-study tables to finish loading
4. Click the link **"View the names expressing this on the leaderboard →"**

**Expected Result:**
- The browser navigates (in-app, no full reload) to `http://localhost:3835/stocks?pattern=pullback_to_rising_dma__only`
- On `/stocks`, the **Pattern** dropdown shows **"Pullback to rising DMA only"** selected (not "All patterns")
- The "N / M" count shows a narrowed subset (N < M) — every visible row carries a "Pullback" badge in its Setup column
- No console errors

---

### UT-04 — Setup cross-link navigates to a pre-filtered leaderboard (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/research` → `/stocks`

**Preconditions:**
- On `http://localhost:3835/research`, page loaded

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the "Setup & Pattern Lab — event study" card, open the **Subject** dropdown and select a **setup** subject under the "Setups" group (e.g. **"Breakout-watch"**)
3. Wait for the event-study tables to finish loading
4. Click the link **"View the names expressing this on the leaderboard →"**

**Expected Result:**
- The browser navigates to `http://localhost:3835/stocks?setup=Breakout-watch` (the exact setup key, URL-encoded)
- On `/stocks`, the **Setup** dropdown shows the chosen setup (e.g. "Breakout-watch") selected, not "All setups"
- Every visible row's Setup column shows that setup status badge
- No console errors

---

### UT-05 — Direct deep-link opens the leaderboard pre-filtered by pattern (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running

**Steps:**
1. Paste `http://localhost:3835/stocks?pattern=pullback_to_rising_dma__only` directly into the address bar and load it
2. Wait for the table to render

**Expected Result:**
- The **Pattern** dropdown is pre-set to **"Pullback to rising DMA only"** on first paint (no manual selection needed)
- Only rows expressing that pattern are shown; the "N / M" count is narrowed (N < M)
- The Sector and Setup dropdowns remain "All sectors" / "All setups"
- No crash, no console error

---

### UT-06 — Direct deep-link opens the leaderboard pre-filtered by sector (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- Frontend running; the dataset contains at least one stock in the "Energy" sector (if Energy is empty, substitute any sector shown in the Sector dropdown)

**Steps:**
1. Paste `http://localhost:3835/stocks?sector=Energy` directly into the address bar and load it
2. Wait for the table to render

**Expected Result:**
- The **Sector** dropdown is pre-set to **"Energy"** on first paint
- Every visible row's Sector column reads "Energy"
- The "N / M" count reflects only Energy names (N ≤ M)
- No crash, no console error

---

### UT-07 — Changing a dropdown reflects the filter into the address bar (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- On `http://localhost:3835/stocks` with no query string

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Note the current vertical scroll position (stay at the top)
3. Open the **Pattern** dropdown and select **"Pullback to rising DMA only"**
4. Read the address bar

**Expected Result:**
- The address bar updates to `http://localhost:3835/stocks?pattern=pullback_to_rising_dma__only`
- The page does NOT scroll-jump (the viewport stays where it was)
- The table narrows to pullback-flagged rows and the "N / M" count drops accordingly
- Selecting the Pattern back to "All patterns" removes `pattern=…` from the address bar (URL returns to `http://localhost:3835/stocks`)

---

### UT-08 — Combined filters all reflect into the URL (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- On `http://localhost:3835/stocks`

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set **Sector** to any non-default value shown (e.g. "Technology")
3. Set **Setup** to any non-default value shown (e.g. "Actionable")
4. Read the address bar

**Expected Result:**
- The address bar contains both params, e.g. `http://localhost:3835/stocks?sector=Technology&setup=Actionable`
- Only `__all__` (default) selections are omitted; each non-default selection appears in the query string
- The table shows only rows matching BOTH filters

---

### UT-09 — Cross-link renders for a low-sample / NA subject (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. In the Setup & Pattern Lab, open the **Subject** dropdown and select a subject whose event study shows mostly "NA" cells / low pooled occurrences (try several subjects until one shows "NA" rows or the "No forward-tested occurrences for this subject" empty-state)
3. Observe the area directly under the Subject dropdown

**Expected Result:**
- The **"View the names expressing this on the leaderboard →"** link is STILL present even though the event-study sample is NA / low
- The caption next to it asserts **no name count** (it reads "…the names expressing this {setup|pattern} at the current as-of date → Stock Detail. The list reflects the live snapshot; no count is asserted here.")
- The link's destination still matches the subject's kind (`?pattern=<key>__only` for a pattern, `?setup=<key>` for a setup)

---

### UT-10 — Unknown pattern param falls back to "all" without crashing (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend running

**Steps:**
1. Paste `http://localhost:3835/stocks?pattern=garbage_value` directly into the address bar and load it
2. Wait for the table to render
3. Repeat with `http://localhost:3835/stocks?pattern=` (empty value)

**Expected Result:**
- The page renders normally with NO crash and NO error card
- The **Pattern** dropdown shows **"All patterns"** (the unknown/empty value is ignored, not applied)
- The full unfiltered list is shown ("N / M" with N = M)
- No console error

---

### UT-11 — Zero-match deep-link shows the honest empty-state (error / edge)

**Type:** error
**Priority:** P2
**Surface:** `/stocks`

**Preconditions:**
- Frontend running. Pick a valid filter combination that matches no rows at the current date — e.g. a rare pattern + a sector that has no such name. A reliable construction: deep-link a valid pattern AND a setup that contradicts it, e.g. `http://localhost:3835/stocks?pattern=flat_base_breakout__only&setup=Avoid` (adjust until the visible count is 0).

**Steps:**
1. Load the chosen zero-match deep-link in the address bar
2. Observe the content area below the filter row

**Expected Result:**
- The empty-state card **"No stocks match these filters"** is shown, with a one-line description naming the active filter and ending "…No rows are fabricated to fill the view — clear a filter to see more."
- NO table rows are rendered (no fabricated/placeholder rows)
- The dropdowns still reflect the deep-linked filters so the user can clear one
- No crash, no console error

---

### UT-12 — J-18: exactly one date control; as-of toggle keeps the filter and adds no `as_of` param (regression — PRINCIPAL RISK)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` ↔ top-bar as-of switcher

**Preconditions:**
- On a filtered deep-link, e.g. `http://localhost:3835/stocks?pattern=pullback_to_rising_dma__only`

**Steps:**
1. Load `http://localhost:3835/stocks?pattern=pullback_to_rising_dma__only`
2. Confirm there is exactly ONE date control on the page — the global as-of switcher in the top bar (there is no second date picker in the filter row)
3. Note the current URL and the "as of YYYY-MM-DD" badge value
4. Use the top-bar as-of switcher to change to a different date
5. Re-read the address bar and the "as of …" badge

**Expected Result:**
- The "as of …" badge updates to the newly chosen date (the page re-points by date)
- The `pattern=pullback_to_rising_dma__only` param **stays intact** in the address bar
- NO `as_of`, `date`, or similar date param is ever added to the URL
- The Pattern dropdown is still pre-set to "Pullback to rising DMA only" after the date change
- Only one date control exists on the page throughout

---

### UT-13 — J-31 travel ends correctly on Stock Detail (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks` → `/stocks/[ticker]`

**Preconditions:**
- Landed pre-filtered on `/stocks` via UT-03 (`?pattern=pullback_to_rising_dma__only`) with ≥1 visible row

**Steps:**
1. From the pre-filtered leaderboard, note the first visible row's Ticker and its three score badges (Leadership / Entry Quality / Risk)
2. Click that row's **Ticker** link
3. On the Stock Detail page, locate the three A–E score badges and the invalidation / setup info

**Expected Result:**
- The browser navigates to `http://localhost:3835/stocks/<TICKER>`
- The detail page shows the pattern/setup badge, the three A–E scores, and an invalidation level/note
- The three score buckets on detail match the buckets shown for that same row on the leaderboard (byte-consistent — J-06)
- No crash, no console error

---

### UT-14 — Existing `/stocks` dropdown filtering still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/stocks`

**Preconditions:**
- On `http://localhost:3835/stocks` (no query string)

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the **Setup** dropdown to a value present in the data (e.g. "Actionable")
3. Observe the table and the "N / M" count
4. Set the Setup dropdown back to "All setups"

**Expected Result:**
- Step 2 narrows the table to only "Actionable" rows and the "N / M" count drops (N < M)
- Step 4 restores the full list (N = M) and clears `setup` from the URL
- The score badges, sort order, and reason text are unchanged from before this iteration (filter is display-only, no recompute)

---

### UT-15 — Cross-link is discoverable from the lab card (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/research`

**Preconditions:**
- On `http://localhost:3835/research`

**Steps:**
1. Navigate to `http://localhost:3835/research`
2. Without prior knowledge, scroll to the Setup & Pattern Lab and look for a way to reach the matching names
3. Read the link label and its caption

**Expected Result:**
- The accent-coloured link **"View the names expressing this on the leaderboard →"** is clearly visible directly under the Subject selector (arrow affordance signals navigation)
- The caption explains the synthesis path in plain language ("lab evidence → the names expressing this … → Stock Detail"), so the purpose is self-evident within one read
- The link label changes meaning correctly with the subject kind (it always reads the same text but points to the right `?pattern=` / `?setup=` destination)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/research` loads with cross-link | smoke | P1 | `/research` |
| UT-02 | `/stocks` loads (Suspense OK) | smoke | P1 | `/stocks` |
| UT-03 | Pattern cross-link → pre-filtered board | happy-path | P1 | `/research`→`/stocks` |
| UT-04 | Setup cross-link → pre-filtered board | happy-path | P1 | `/research`→`/stocks` |
| UT-05 | Deep-link pre-filter by pattern | happy-path | P1 | `/stocks` |
| UT-06 | Deep-link pre-filter by sector | happy-path | P1 | `/stocks` |
| UT-07 | Dropdown change reflects to URL (no scroll-jump) | happy-path | P1 | `/stocks` |
| UT-08 | Combined filters reflect to URL | happy-path | P2 | `/stocks` |
| UT-09 | Cross-link renders for NA/low-sample subject | happy-path | P2 | `/research` |
| UT-10 | Unknown/empty pattern param → "all" | validation | P2 | `/stocks` |
| UT-11 | Zero-match deep-link → honest empty-state | error | P2 | `/stocks` |
| UT-12 | One date control; as-of keeps filter, no `as_of` param | regression | P1 | `/stocks`↔top-bar |
| UT-13 | Travel ends on Stock Detail, scores consistent | regression | P1 | `/stocks`→`/stocks/[ticker]` |
| UT-14 | Existing dropdown filtering still works | regression | P1 | `/stocks` |
| UT-15 | Cross-link discoverable & self-explaining | ux | P3 | `/research` |

**P1 tests (UT-01–07, UT-12, UT-13, UT-14) must all pass for browser QA verdict to be PASS.**
**Principal-risk test:** UT-12 (J-18 — exactly one date control, no `as_of` param).
**Defining test:** UT-03 + UT-13 together (full J-31 cross-page travel: lab → pre-filtered board → detail).
