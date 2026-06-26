# Goal Iteration 49 — Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49
**Date:** 2026-06-26
**Frontend Present:** yes

## Phase Goal

Add a sortable "Proximity to 52w high" column to the Stocks leaderboard (displaying the already-served Leadership `high_proximity` component value) and fix the readiness badge so it honestly reflects backend status instead of being stuck on "Backend unavailable".

---

## Test Cases

### TC-01 — Stocks leaderboard displays "Proximity to 52w high" column after Risk column

**Type:** browser
**Preconditions:**
- Backend is running and serving `/api/stocks` with Leadership score components including `high_proximity`
- Frontend is loaded at `http://localhost:3000/stocks`

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Verify the table renders with column headers
3. Locate the "Risk" column header
4. Confirm a new "Proximity to 52w high" column header exists immediately after Risk

**Expected outcome:** The new column header is visible and positioned directly after the Risk column
**Pass criteria:** Header text reads "Proximity to 52w high" and is the N+1 column after Risk's column index

---

### TC-02 — Proximity column displays the same value as the Leadership breakdown

**Type:** browser
**Preconditions:**
- TC-01 passes
- Frontend is loaded at `/stocks` leaderboard
- At least one stock row is visible

**Steps:**
1. Select the first visible stock row
2. Record the "Proximity to 52w high" value shown in the leaderboard row
3. Click the stock ticker to open the detail page
4. Locate the Leadership score breakdown section
5. Find the "Proximity to 52w high" component value in the breakdown

**Expected outcome:** The value shown in the leaderboard matches exactly what the Leadership breakdown shows
**Pass criteria:** Both values are byte-identical (same number, same formatting, including NA if applicable)

---

### TC-03 — Proximity column is client-side sortable, NA-last

**Type:** browser
**Preconditions:**
- TC-01 passes
- Frontend is at `/stocks` leaderboard
- Multiple stock rows with mixed null and numeric proximity values are visible

**Steps:**
1. Take a screenshot of the current leaderboard order (Frame A)
2. Click the "Proximity to 52w high" column header to sort ascending
3. Wait for the table to re-order
4. Take a second screenshot (Frame B)
5. Verify rows with null `high_proximity` appear at the end (last position)
6. Click the column header again to sort descending
7. Take a third screenshot (Frame C)
8. Verify the sort direction reversed

**Expected outcome:** Clicking the header reorders the leaderboard rows by proximity value, with NA values consistently sorting last; two byte-distinct frames capture the reordering
**Pass criteria:** Frame A and Frame B are byte-distinct; NA rows are in the last position in both frames; Frame C shows reversed order

---

### TC-04 — Proximity column displays NA-honest (muted NA) when value is null

**Type:** browser
**Preconditions:**
- TC-01 passes
- Frontend is at `/stocks` leaderboard
- At least one stock has a null `high_proximity` component

**Steps:**
1. Locate a row where the proximity value is null
2. Inspect the cell rendering in that column

**Expected outcome:** The cell displays "NA" in a muted color (not fabricated data, not numeric placeholder)
**Pass criteria:** Cell text is exactly "NA" and uses muted text styling (CSS color class or attribute matching other NA cells in the table)

---

### TC-05 — Proximity column header carries config-backed glossary tooltip

**Type:** browser
**Preconditions:**
- TC-01 passes
- Frontend is at `/stocks` leaderboard

**Steps:**
1. Hover over the "Proximity to 52w high" column header
2. Wait for a tooltip to appear
3. Record the tooltip text

**Expected outcome:** A tooltip appears with the glossary definition of the term
**Pass criteria:** Tooltip text contains the plain-language explanation of proximity-to-52w-high (e.g., from the config-backed methodology catalog); NOT a default or missing-term message

---

### TC-06 — Column header has accessible aria-label for sort

**Type:** artifact
**Preconditions:**
- Frontend code is compiled

**Steps:**
1. Open `apps/frontend/app/stocks/page.tsx`
2. Locate the "Proximity to 52w high" SortHeader
3. Inspect the aria-label attribute on the header element

**Expected outcome:** The aria-label is present and descriptive
**Pass criteria:** aria-label value is "Sort by Proximity to 52w high" or similar (contains "Sort" + the column name)

---

### TC-07 — Readiness badge reaches Ready state when backend is genuinely serving

**Type:** browser
**Preconditions:**
- Backend is freshly restarted, warmed, and serving requests
- Frontend is loaded at `http://localhost:3000`

**Steps:**
1. Open DevTools and wait for the page to hydrate
2. Observe the readiness badge in the top-right app shell
3. Allow 2–3 seconds for the `/api/health` call to complete
4. Record the badge state

**Expected outcome:** The badge displays "Ready" or "Initializing… n/m" (during warm-up), not "Backend unavailable"
**Pass criteria:** Badge state is "Ready" (or "Initializing…" with progress) within 3 seconds of page load

---

### TC-08 — Readiness badge exercises the diagnosed failing scenario (LAN-IP origin)

**Type:** browser
**Preconditions:**
- Backend is running and serving
- Frontend can be accessed at the LAN-IP origin printed by `./scripts/dev.sh` (e.g., `http://192.168.x.x:3000`)
- The root cause of the host/CORS mismatch has been diagnosed and documented

**Steps:**
1. Open a browser and navigate to the frontend at the LAN-IP origin (not localhost)
2. Allow page to hydrate fully
3. Wait 2–3 seconds for the readiness health check
4. Observe the badge state

**Expected outcome:** The badge reaches "Ready" or "Initializing… n/m", NOT "Backend unavailable"
**Pass criteria:** Badge is honest (Ready or Initializing) instead of stuck on "Backend unavailable"; this proves the CORS/host fix works for the non-localhost origin

---

### TC-09 — Readiness badge shows Unavailable when backend is genuinely down

**Type:** browser
**Preconditions:**
- Backend is stopped/not serving
- Frontend is loaded at `http://localhost:3000`

**Steps:**
1. Start the frontend without starting the backend (or stop the backend after the frontend has loaded)
2. Wait 3–4 seconds for the `/api/health` request to timeout
3. Observe the badge state

**Expected outcome:** The badge displays "Unavailable" (honest, not faked Ready)
**Pass criteria:** Badge shows "Unavailable" and never shows "Ready" when the backend is genuinely unreachable

---

### TC-10 — API_BASE host-aware resolution: localhost config + non-localhost page host

**Type:** api
**Preconditions:**
- `resolveApiBase(...)` function is exported from `apps/frontend/lib/api-base.ts`
- Unit test file `apps/frontend/lib/api-base.test.ts` exists

**Steps:**
1. Run the unit test: `cd apps/frontend && npm test -- --testPathPattern=api-base`
2. Verify the test case for "localhost config + non-localhost page host → page-host + port" passes
3. Assert the resolved URL equals `http://<page-hostname>:<NEXT_PUBLIC_API_PORT>`

**Expected outcome:** The function resolves a localhost-configured base + a non-localhost page host to the page's hostname + the configured port
**Pass criteria:** Test assertion passes; resolved URL matches expected pattern exactly

---

### TC-11 — API_BASE host-aware resolution: explicit non-localhost URL used verbatim

**Type:** api
**Preconditions:**
- `resolveApiBase(...)` function is exported from `apps/frontend/lib/api-base.ts`
- Unit test file `apps/frontend/lib/api-base.test.ts` exists

**Steps:**
1. Run the unit test: `cd apps/frontend && npm test -- --testPathPattern=api-base`
2. Verify the test case for "explicit non-localhost `NEXT_PUBLIC_API_URL` → verbatim" passes
3. Assert the resolved URL equals the explicitly configured URL

**Expected outcome:** When a non-localhost `NEXT_PUBLIC_API_URL` is provided, it is returned verbatim (not overridden)
**Pass criteria:** Test assertion passes; resolved URL equals the configured value exactly

---

### TC-12 — Backend CORS allows LAN-IP frontend origin (if CORS was changed)

**Type:** api
**Preconditions:**
- Backend is running
- The root cause diagnosis indicates CORS was the blocker
- A backend CORS test exists in `apps/backend/tests/test_*.py`

**Steps:**
1. Run the backend test suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k cors`
2. Verify the test asserting the LAN-IP origin is allowed passes
3. Verify `readiness.py` readiness states are unchanged by the CORS change

**Expected outcome:** A request from the LAN-IP frontend origin is accepted (HTTP 200/success, not 403), and readiness logic is unaffected
**Pass criteria:** CORS test passes; `readiness.py` states remain consistent

---

### TC-13 — Required-still-passing smoke: J-01 Dashboard hydrates

**Type:** browser
**Preconditions:**
- Backend is running and serving
- Frontend is loaded at `http://localhost:3000/`

**Steps:**
1. Navigate to the Dashboard (home page)
2. Wait for the page to fully hydrate
3. Verify key dashboard elements render (market regime, sector scores, or other expected content)

**Expected outcome:** Dashboard loads, hydrates, and displays content without errors
**Pass criteria:** Page is interactive within ~1.5s; no console errors related to API_BASE or data fetching

---

### TC-14 — Required-still-passing smoke: J-06 Stock detail equals leaderboard

**Type:** browser
**Preconditions:**
- Backend is running
- Frontend is at `/stocks` leaderboard with visible stock rows
- TC-13 passes

**Steps:**
1. Record a stock's Leadership score from the leaderboard row
2. Click the stock ticker to open the detail page
3. Locate the Leadership score on the detail page
4. Compare the value

**Expected outcome:** The Leadership score displayed on the detail page matches the leaderboard value
**Pass criteria:** Scores are byte-identical; no data fetch or computation errors

---

### TC-15 — Required-still-passing smoke: J-07 Risk-Off regime → zero Actionable stocks (CRITICAL)

**Type:** browser
**Preconditions:**
- Backend is running with a Risk-Off regime snapshot
- Frontend is loaded at `/stocks` leaderboard

**Steps:**
1. Verify the regime indicator shows "Risk-Off"
2. Count the stocks labeled "Actionable" on the leaderboard
3. Record the count

**Expected outcome:** Zero stocks are labeled "Actionable" (watchlist-only labels only)
**Pass criteria:** Actionable count is exactly 0; this is a hard anti-goal constraint (J-07)

---

### TC-16 — Required-still-passing smoke: J-18 Zero native input[type=date] fields (CRITICAL)

**Type:** artifact
**Preconditions:**
- Frontend source code is available

**Steps:**
1. Search the frontend codebase: `grep -r 'input.*type="date"' apps/frontend/`
2. Record any matches

**Expected outcome:** No native `<input type="date">` elements exist
**Pass criteria:** grep returns zero matches (or only matches in comments/strings, not in JSX)

---

### TC-17 — Required-still-passing smoke: J-40 Data loads on every page after API_BASE change

**Type:** browser
**Preconditions:**
- Backend is running
- Frontend is loaded

**Steps:**
1. Navigate to each major page: Dashboard, Stocks, Sectors, Themes, Stock Detail, Research
2. For each page, verify data loads (no "Backend unavailable", no empty error states)
3. Open DevTools Network tab and confirm successful API calls to endpoints like `/api/stocks`, `/api/sectors`, etc.

**Expected outcome:** All pages load data successfully; no API fetch failures
**Pass criteria:** Every page shows content; Network tab shows 2xx status codes for data endpoints; no console 403/CORS errors

---

### TC-18 — Required-still-passing smoke: J-48 Column sort reorders the table

**Type:** browser
**Preconditions:**
- Frontend is at `/stocks` leaderboard
- Multiple sort-enabled columns are visible (e.g., Risk, Leadership Score, Proximity, etc.)

**Steps:**
1. Take a screenshot of the current table order (Frame A)
2. Click an existing sort-enabled column header (e.g., "Leadership Score")
3. Wait for the table to re-order
4. Take a second screenshot (Frame B)

**Expected outcome:** The table rows reorder based on the clicked column
**Pass criteria:** Frame A and Frame B are byte-distinct; the row order changed according to the sort direction

---

### TC-19 — Required-still-passing smoke: J-75/J-80 Forward-return columns visible

**Type:** browser
**Preconditions:**
- Frontend is at `/stocks` leaderboard
- Backend is serving forward-return data for the current snapshot

**Steps:**
1. Verify the leaderboard renders columns like "1D Return", "5D Return", "10D Return", "20D Return", "60D Return" (or similar naming)
2. Verify a regime/theme indicator strip is visible (header or top section)

**Expected outcome:** Forward-return columns and regime/theme strip are visible and populated
**Pass criteria:** At least one forward-return column header is visible; regime/theme strip renders without errors

---

### TC-20 — Required-still-passing smoke: J-104 Research lab loads after API_BASE change

**Type:** browser
**Preconditions:**
- Frontend is at `/research` or a research lab view
- Backend is serving cached aggregates and research data

**Steps:**
1. Navigate to the Research section
2. Wait for the page to fully load
3. Verify factor lab tables or research analysis loads

**Expected outcome:** Research page loads successfully without "Backend unavailable" errors
**Pass criteria:** Page renders content within ~2s; API calls to research endpoints succeed (2xx status); no CORS/fetch errors in console

---

### TC-21 — Dev handoff documents the diagnosed J-108 root cause

**Type:** artifact
**Preconditions:**
- Dev work is complete
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49-dev.md` exists

**Steps:**
1. Open the dev handoff file
2. Locate the section documenting the J-108 root cause
3. Verify it describes the diagnosed issue and the fix applied

**Expected outcome:** The handoff clearly states the root cause (e.g., "CORS mismatch: dev.sh advertises LAN-IP origin but CORS_ORIGINS only listed localhost") and the fix (e.g., "widened CORS_ORIGINS to include private-LAN range")
**Pass criteria:** Root cause is explicitly named; fix rationale is explained; not vague or omitted

---

## Summary

**Total test cases:** 21
- **Browser tests:** 13 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-08, TC-09, TC-13, TC-14, TC-15, TC-17, TC-18, TC-19, TC-20)
- **API tests:** 3 (TC-10, TC-11, TC-12)
- **Artifact checks:** 5 (TC-06, TC-16, TC-21)

**Coverage summary:**
- **J-106 (Proximity column):** TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-18
- **J-108 (Readiness badge fix):** TC-07, TC-08, TC-09, TC-10, TC-11, TC-12
- **Required-still-passing smoke:** TC-13, TC-14, TC-15, TC-16, TC-17, TC-19, TC-20
- **Handoff documentation:** TC-21
