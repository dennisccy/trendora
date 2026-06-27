# Iteration 55 Functional Test Plan — Regime × Phase × Factor Lab

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55
**Date:** 2026-06-27
**Frontend Present:** yes

## Phase Goal

Ship the new **Research → Regime × Phase × Factor** lab at `/research/regime-phase-factor` — a ranked, filterable, paginated table that shows how stocks' realized forward returns and paired max-drawdowns differ across the (regime-score decile × severity-score decile × factor decile) combinations at every configured horizon for a selected factor, completing the last unbuilt buildable Must-have (J-112).

## Test Cases

### TC-01 — Hub Tile Visibility and Navigation

**Type:** browser
**Preconditions:** Frontend running at `http://localhost:3000`; Research hub page (`/research`) loads; database contains populated scanner runs with forward-return data.

**Steps:**
1. Navigate to `/research` hub page
2. Locate the "Regime × Phase × Factor" tile in the LABS section (look for a grid/boxes icon)
3. Verify the tile displays a distinct one-line description
4. Click the tile

**Expected outcome:** User navigates to `/research/regime-phase-factor` page; page loads without error.
**Pass criteria:** URL changes to `/research/regime-phase-factor`; page renders (no 404 or "Backend unavailable" skeleton).

---

### TC-02 — Page Shell and Controls Load

**Type:** browser
**Preconditions:** Frontend running; user navigates to `/research/regime-phase-factor`.

**Steps:**
1. Wait for page to load (check for non-skeleton content)
2. Verify a factor selector (`<select>` or custom selector component) is present
3. Verify an "As-of vs All-history" toggle is present
4. Verify a ranked combination table is rendered with at least one row
5. Verify pagination controls (prev/next) appear at the bottom

**Expected outcome:** Page layout matches the research-lab shell (shared controls bar above full-width scrollable table with pagination footer).
**Pass criteria:** Factor selector, As-of toggle, table with ≥1 row, and pagination controls all render (no errors in browser console; no "Backend unavailable").

---

### TC-03 — Factor Selector Populates from Config

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded.

**Steps:**
1. Click the factor selector dropdown
2. Verify a list of factors appears (at least 3 entries from the config-backed factor catalog)
3. Verify a default factor is pre-selected
4. Select a different factor from the dropdown

**Expected outcome:** Dropdown lists all configured factors; selecting a new factor sends an API request with `factor=<selected_factor>` and re-renders the table.
**Pass criteria:** Dropdown populates with ≥3 factors; selecting a factor changes the table rows (byte-distinct from before the switch); `factor` query param in network request matches the selected factor.

---

### TC-04 — Table Structure — Columns and Decile Display

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded with data.

**Steps:**
1. Examine the table headers
2. Verify the first columns show regime-score decile, severity-score decile, and factor decile (labeled clearly)
3. Verify the next columns are grouped by horizon (1d, 5d, 10d, 20d, 60d) and each horizon shows mean realized forward return + paired mean max-drawdown
4. Verify a final "n" (sample count) column exists
5. Scroll right to verify all columns are accessible

**Expected outcome:** Table displays `(regime-decile, severity-decile, factor-decile)` dimensions, paired return/drawdown columns per horizon, and n.
**Pass criteria:** All expected columns render; no missing horizons; column order is consistent; horizontally-scrollable layout works.

---

### TC-05 — Table Sort — NA-Last Both Directions

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded with mixed NA and numeric values.

**Steps:**
1. Locate a column header with both numeric values and NA entries (e.g., forward-return at 60d)
2. Record the md5 hash of the table content before sort
3. Click the column header (resolve by `aria-label` not visible text)
4. Verify rows reorder
5. Record the md5 hash after sort
6. Verify NA rows (or rows with n=0 / value=null) appear at the bottom, not mixed with numbers
7. Click the column header again (reverse sort)
8. Verify NA rows still sink last (not first)

**Expected outcome:** Clicking a column header sorts ascending or descending; NA values always appear last in both directions; byte-distinct frame before and after sort (md5 differs).
**Pass criteria:** md5 hash before ≠ md5 hash after sort; NA rows consistently sort last; reverse sort also respects NA-last; `aria-label` selector successfully identifies header.

---

### TC-06 — Regime Decile Filter

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded; table shows rows with mixed regime-score deciles.

**Steps:**
1. Locate the "Regime Decile" filter control
2. Verify it defaults to "All"
3. Select a single regime decile (e.g., decile 5)
4. Verify the table re-renders showing only rows with that regime decile
5. Verify other deciles disappear from the visible rows
6. Select "All" to restore all rows

**Expected outcome:** Filtering by regime decile narrows the displayed rows (client-side view transform; no API refetch); reverting to "All" restores all rows.
**Pass criteria:** Selecting a decile removes rows with other deciles from view; "All" option restores full row set; no network request to API (pure client-side filter).

---

### TC-07 — Severity Decile Filter

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded.

**Steps:**
1. Locate the "Severity Decile" filter control
2. Verify it defaults to "All"
3. Select a single severity decile (e.g., decile 3)
4. Verify the table narrows to that decile only
5. Reset to "All"

**Expected outcome:** Filtering by severity decile works as a pure client-side view transform.
**Pass criteria:** Selecting a severity decile filters rows correctly; "All" restores full set; no API refetch.

---

### TC-08 — Factor Decile Filter

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded.

**Steps:**
1. Locate the "Factor Decile" filter control
2. Verify it defaults to "All"
3. Select a single factor decile (e.g., decile 8)
4. Verify the table narrows to that decile only
5. Reset to "All"

**Expected outcome:** Filtering by factor decile works as a pure client-side view transform.
**Pass criteria:** Selecting a factor decile filters rows correctly; "All" restores full set; no API refetch.

---

### TC-09 — Pagination at 30 Rows/Page

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded; table has ≥31 rows.

**Steps:**
1. Count the visible rows on the current page
2. Verify the count is exactly 30 (or fewer if fewer than 30 total exist)
3. Verify "Page 1" indicator (or similar) is displayed
4. Click the "Next" pagination button
5. Verify the page advances; row count is 30 or the remaining rows if <30
6. Verify the visible rows are DIFFERENT from page 1 (confirm it's not the same rows re-filtered)
7. Click "Previous" to return to page 1
8. Verify the same rows from step 1 reappear

**Expected outcome:** Pagination shows 30 rows per page; next/previous buttons navigate between pages (pure client-side view transform; no API refetch).
**Pass criteria:** Page displays exactly 30 rows; next/previous buttons work; navigating back to page 1 restores the original rows.

---

### TC-10 — As-of Filter Reduces Sample Counts

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded at latest (default); table shows n values.

**Steps:**
1. Record the n (sample count) values for 2–3 rows on the current page
2. Click the "As-of vs All-history" toggle to switch to a historical date (e.g., 2024-06-01, mid-history, NOT the warm-up head)
3. Verify the API request includes `as_of=2024-06-01` (sent via `withAsOf` helper; param spelling is `as_of=`, NOT `asof=`)
4. Wait for the table to re-render
5. Verify the n values for the same rows have DECREASED (historical cutoff filters out newer observations)
6. Toggle back to "All-history" (latest)
7. Verify the n values return to their original counts

**Expected outcome:** Toggling As-of filters the observation set by date; sample counts shrink; toggling back restores original counts. No second date control appears on the page (single global as-of only).
**Pass criteria:** As-of toggle filters rows by date; n values decrease when switching to historical date; network request shows `as_of=` param (correct spelling); toggling back restores counts; no extra date input on page.

---

### TC-11 — No Native Date Input (J-18 Constraint)

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded.

**Steps:**
1. Use browser DevTools or page inspection to search for any `<input type="date">` elements
2. Verify zero native date inputs are found on the page

**Expected outcome:** The page does NOT use native HTML date inputs; As-of control is a toggle or dropdown, not a text input.
**Pass criteria:** `document.querySelectorAll('input[type="date"]').length === 0`; As-of control is a toggle or dropdown.

---

### TC-12 — No Episodes/Pooled Toggle (Pinned Pooled)

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded.

**Steps:**
1. Search the page for any "Episodes" / "Pooled" toggle control
2. Verify NO such toggle is visible

**Expected outcome:** The page does not expose an Episodes/Pooled view selector (pinned to Pooled internally per iter-53 lesson).
**Pass criteria:** No Episodes/Pooled toggle found on the page; API requests include `view=pooled` in the fetch.

---

### TC-13 — N Chip Opens Samples Cohort in New Tab

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded; a row with a non-zero n value is visible.

**Steps:**
1. Locate an N chip (sample count) in a table row
2. Record the triple `(regime-decile, severity-decile, factor-decile, horizon)` for that row and the n value
3. Right-click or inspect the N chip to verify it's a link (or use middle-click to open in new tab)
4. Click the N chip (open in new tab via middle-click or Ctrl+click)
5. Wait for the new tab to load
6. Navigate to the new tab
7. Verify the URL is `/research/samples?...` with `regime_decile=X&severity_decile=Y&factor_decile=Z&horizon=H` and `?asof=` if historical
8. Verify the "Total observations" count on the Samples page equals the n value from step 2
9. Verify `view=pooled` is in the query string

**Expected outcome:** N chip links to `/research/samples` for the exact triple+horizon cohort; Samples page count-coherence is verified; `?asof` is carried forward if historical.
**Pass criteria:** N chip is clickable; new tab shows `/research/samples` with correct `regime_decile`, `severity_decile`, `factor_decile`, `horizon` params; "Total observations" == n from chip; `view=pooled` present in query string.

---

### TC-14 — Survivorship-Bias Label Present

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded.

**Steps:**
1. Search the page for text containing "survivorship" or "bias" or "descriptive evidence"
2. Verify a label or footnote is present explaining that the data represents descriptive evidence with survivorship bias (current-membership universe)

**Expected outcome:** A clear label warns users about survivorship bias in the forward-test data.
**Pass criteria:** Text containing "survivorship" AND "bias" (or equivalent "descriptive evidence") found on page; label is visible above or below the table.

---

### TC-15 — Table Displays NA + n for Low-Sample Combinations

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded with data that includes combinations below `config.walk_forward.min_sample`.

**Steps:**
1. Locate rows with n < config min-sample (e.g., n < 5 if min-sample is 5)
2. Verify the return/drawdown cells for those rows show "NA" (or similar placeholder)
3. Verify the n value is still displayed (not dropped)
4. Verify the row is NOT omitted from the table

**Expected outcome:** Low-sample combinations display NA in aggregate columns but are honest (never dropped silently or fabricated).
**Pass criteria:** Rows with n < min-sample show "NA" in return/drawdown columns; n value is visible; row is not missing from the table.

---

### TC-16 — API Endpoint Status and Response Shape

**Type:** api
**Preconditions:** Backend running at `http://localhost:8255`; database contains populated runner data with forward returns.

**Steps:**
1. Run the following curl command (with a valid factor and optional as_of date):
   ```bash
   curl -s "http://localhost:8255/api/research/regime-phase-factor?factor=close_price&view=pooled" | python3 -m json.tool | head -50
   ```
2. Verify HTTP status is 200 (or check with `-w "%{http_code}"`)
3. Verify the response is valid JSON
4. Inspect the payload structure to confirm it contains:
   - `rows` (array of combination objects)
   - Each row has keys: `regime_decile`, `severity_decile`, `factor_decile`, and per-horizon keys like `h1d_mean_return`, `h1d_mean_mdd`, `h1d_n`, etc.
   - `page_size` (integer, e.g. 30)
5. Verify no rows are omitted (no silent drops); all emitted combinations are present

**Expected outcome:** Endpoint returns 200 with valid JSON; response structure matches expected schema (no missing horizons or fields).
**Pass criteria:** HTTP 200; JSON valid; `rows` array present; each row has regime_decile, severity_decile, factor_decile; all horizons represented; no fabricated rows.

---

### TC-17 — API Respects factor Param

**Type:** api
**Preconditions:** Backend running; database contains forward-return data for at least 2 distinct factors.

**Steps:**
1. Fetch `/api/research/regime-phase-factor?factor=factor_A&view=pooled`
2. Record the set of regime/severity/factor-decile combinations returned
3. Fetch `/api/research/regime-phase-factor?factor=factor_B&view=pooled` (different factor)
4. Record the set of combinations returned
5. Verify the two result sets are DIFFERENT (rows differ because factor_A ≠ factor_B)

**Expected outcome:** The `factor` query parameter controls which factor is analyzed; changing it produces different rows.
**Pass criteria:** Fetching with two different factors returns visibly different result sets; rows are not identical.

---

### TC-18 — API Respects as_of Filter (Sample Count Decreases)

**Type:** api
**Preconditions:** Backend running; database contains historical forward-return data spanning multiple dates.

**Steps:**
1. Fetch `/api/research/regime-phase-factor?factor=close_price&view=pooled` (no as_of; latest)
2. Extract the total "n" count summed across all rows
3. Fetch `/api/research/regime-phase-factor?factor=close_price&view=pooled&as_of=2024-06-01` (historical date, mid-history)
4. Extract the total "n" count from this result
5. Verify the historical total "n" is LESS than the latest total "n" (historical cutoff filters out newer observations)

**Expected outcome:** The `as_of` parameter filters observations; historical dates yield lower sample counts than latest.
**Pass criteria:** Total n at historical as_of < total n at latest; response is 200 (not 4xx); samples are honestly reduced, not fabricated.

---

### TC-19 — API Supports Pooled View (Verified)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Fetch `/api/research/regime-phase-factor?factor=close_price&view=pooled`
2. Verify HTTP 200
3. Fetch `/api/research/regime-phase-factor?factor=close_price&view=episodes` (test that both views are served/unit-proven per spec)
4. Verify HTTP 200 for Episodes too (even though frontend pins Pooled)
5. Compare the two responses to confirm Episodes and Pooled yield different sample structures (Episodes collapse to first-appearance, Pooled uses all observations)

**Expected outcome:** Both `view=pooled` and `view=episodes` are supported by the API (unit-proven per spec, though frontend pins Pooled).
**Pass criteria:** Both `view=pooled` and `view=episodes` return 200; responses differ (Episodes has fewer or re-grouped rows); payload structure is consistent for both.

---

### TC-20 — API Rejects Unknown Factor (Honest Empty or 4xx)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Fetch `/api/research/regime-phase-factor?factor=nonexistent_factor&view=pooled`
2. Check the HTTP status and response body

**Expected outcome:** API either returns 200 with an empty `rows` array, or returns a 4xx status code with a clear error message (not a fabricated result).
**Pass criteria:** HTTP status is 200 (empty rows) OR 4xx (invalid factor); never 500; never a fabricated result; response body is JSON.

---

### TC-21 — API Rejects Out-of-Range Decile (4xx)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Fetch `/api/research/regime-phase-factor?factor=close_price&view=pooled&regime_decile=99` (invalid decile 99)
2. Verify HTTP status is 4xx (e.g., 400 or 422)

**Expected outcome:** Out-of-range decile parameters are rejected with a 4xx error.
**Pass criteria:** HTTP status is 4xx (not 200 or 5xx); error message in response body.

---

### TC-22 — Required-Still-Passing: J-06 Single-Source Regime

**Type:** browser
**Preconditions:** Frontend running; `/research/regime-phase-factor` page loaded and rendering table with regime values.

**Steps:**
1. Open the Stocks page `/stocks` in another tab
2. Locate a stock's regime label in the Stocks leaderboard
3. Verify the regime label matches the regime-score decile (or regime name) shown in the Regime × Phase × Factor table for the same run
4. Verify no duplicate or alternative regime derivation is shown

**Expected outcome:** The regime value displayed in the Regime × Phase × Factor lab is identical to the regime shown in the Stocks page (single source: `ScannerRun.regime_score` read verbatim).
**Pass criteria:** Regime values are byte-identical across pages; no second regime computation appears anywhere.

---

### TC-23 — Required-Still-Passing: J-18 Zero Native Date Inputs (Recheck)

**Type:** browser
**Preconditions:** Frontend running; all research pages loaded (hub, regime-phase-factor, factor lab, regime lab, phase-severity lab, etc.).

**Steps:**
1. Open `/research` hub
2. Open `/research/regime-phase-factor`
3. Open `/research/factor-lab`
4. Open `/research/regime-lab`
5. Open `/research/phase-severity-lab`
6. On each page, search for native date inputs (`<input type="date">`)
7. Verify zero native date inputs across all pages

**Expected outcome:** No native `<input type="date">` elements exist on any research page; all date controls are toggles or dropdowns.
**Pass criteria:** `document.querySelectorAll('input[type="date"]').length === 0` on every research page.

---

### TC-24 — Required-Still-Passing: J-07 Risk-Off Actionable Gate

**Type:** browser
**Preconditions:** Frontend running; backend with a Risk-Off regime in the current snapshot.

**Steps:**
1. Navigate to `/stocks` leaderboard in a Risk-Off regime day
2. Verify the "Actionable" status badges are ZERO (or show 0 count)
3. Verify only "Watchlist-only" labels appear (no Actionable/Breakout/Pullback candidates)
4. Verify the Regime × Phase × Factor lab STILL RENDERS the table (the lab is not gated by regime; it's a research tool showing historical realized returns)

**Expected outcome:** Risk-Off regime blocks Actionable status but does NOT block research labs (which are read-only retrospective studies).
**Pass criteria:** `/stocks` shows zero Actionable in Risk-Off; `/research/regime-phase-factor` still renders table; risk-off state does NOT break the lab.

---

### TC-25 — Required-Still-Passing: J-110 Regime Lab Still Renders

**Type:** browser
**Preconditions:** Frontend running; navigate to `/research/regime-lab`.

**Steps:**
1. Verify the Regime Lab page loads without error
2. Verify the regime-score table renders with real figures (not stale or corrupted)
3. Verify the regime label and numeric score match the latest scan regime

**Expected outcome:** The Regime Lab (J-110) is not broken by the new Regime × Phase × Factor lab; both sibling labs are byte-identical to before.
**Pass criteria:** Regime Lab page loads; table renders with coherent data; no regression in figures or layout.

---

### TC-26 — Required-Still-Passing: J-111 Phase & Severity Lab Still Renders

**Type:** browser
**Preconditions:** Frontend running; navigate to `/research/phase-severity-lab`.

**Steps:**
1. Verify the Phase & Severity Lab page loads without error
2. Verify the phase/severity table renders with real figures
3. Verify the severity values match the served `market_phase` timeline values (same source the Regime × Phase × Factor lab joins on)

**Expected outcome:** The Phase & Severity Lab (J-111) is not broken; both labs read severity from the same canonical source.
**Pass criteria:** Phase & Severity Lab loads and renders; severity values are coherent and match the Regime × Phase × Factor lab's severity-decile groupings.

---

### TC-27 — Required-Still-Passing: J-80 Stocks Header Regime

**Type:** browser
**Preconditions:** Frontend running; navigate to `/stocks` leaderboard.

**Steps:**
1. Locate the regime label/score in the page header (e.g., "Regime: Accumulation 72")
2. Verify the regime value matches the value read in the Regime × Phase × Factor lab (same `ScannerRun.regime_score` source)

**Expected outcome:** The Stocks header regime is the same canonical value read in the new lab (no second regime derivation).
**Pass criteria:** Regime value in Stocks header == regime-score in Regime × Phase × Factor table (byte-identical).

---

### TC-28 — Required-Still-Passing: J-87 Dashboard Market-Phase Panel

**Type:** browser
**Preconditions:** Frontend running; navigate to Dashboard (`/`).

**Steps:**
1. Locate the Market-Phase panel on the dashboard
2. Verify the displayed severity level (0–100) matches the severity values used in the Regime × Phase × Factor lab (same `market_phase` timeline source)
3. Check the panel heading/label to confirm it's sourcing from the canonical `market_phase` series

**Expected outcome:** The Dashboard Market-Phase panel and the Regime × Phase × Factor lab read severity from the same `market_phase` canonical timeline (joined by snapshot date).
**Pass criteria:** Severity values are byte-identical; both pages read from `market_phase._timeline_series`/`timeline_full` without recomputation.

---

## Summary

Total test cases: 28
- API tests: 7 (TC-16 through TC-21)
- Browser tests: 21 (TC-01 through TC-15, TC-22 through TC-28)
- Artifact checks: 0

**Key coverage areas:**
- Page shell and navigation (TC-01 to TC-02)
- Factor selector and dynamic re-fetching (TC-03)
- Table structure and column layout (TC-04)
- Sorting with NA-last behavior (TC-05)
- Filtering by regime/severity/factor deciles (TC-06 to TC-08)
- Pagination at 30 rows/page (TC-09)
- As-of filtering with sample count reduction (TC-10)
- UI constraints: no native date input (TC-11), no Episodes toggle (TC-12)
- Drill-down count coherence to Research Samples (TC-13)
- Survivorship-bias labeling (TC-14)
- NA handling for low-sample combinations (TC-15)
- API response structure and shape (TC-16)
- Factor parameter respect (TC-17)
- As-of filter effectiveness (TC-18)
- Pooled and Episodes views supported (TC-19)
- Error handling for invalid factor/decile (TC-20 to TC-21)
- Required-still-passing regression checks for J-06, J-18, J-07, J-110, J-111, J-80, J-87 (TC-22 to TC-28)

All tests are specific, reproducible, and grounded in the phase spec and anti-goals (Single source of truth, No recompute in read path, Honest limitations, One date selector).
