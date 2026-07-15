# goal-mcp-loop-iter-40 Functional Test Plan

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Frontend Present:** yes

## Phase Goal

Add a per-stock risk-budget card and leaderboard columns displaying ATR%, downside volatility, overnight-gap profile (median/p95/worst), worst 20-day historical window, and distance-to-invalidation %, each with universe-percentile context — sourced once from the stored snapshot, honestly NA for short history, no Evidence Claim (descriptive statistics only).

## Test Cases

### TC-01 — Stock detail page: Risk-budget card renders with full values for liquid name

**Type:** browser
**Preconditions:** 
- Backend has computed new risk-budget fields and regenerated bootstrap + latest snapshots with real values
- `/api/stocks/{ticker}` returns the new fields (not null) for a liquid stock (e.g., AAPL)

**Steps:**
1. Navigate to `/stocks/AAPL` (or equivalent liquid name)
2. Locate the Risk-budget card (positioned near the existing ThemeAndInvalidationCard)
3. Verify the card displays all five components: ATR%, downside volatility, overnight-gap median/p95/worst, worst 20-day window, distance-to-invalidation %
4. For each component, confirm a universe-percentile label is shown (e.g., "p87 of universe")
5. Verify all displayed values are non-null numeric values or percentiles, not NA

**Expected outcome:** The card renders with complete risk metrics and percentile context for all five components.

**Pass criteria:** All five component values + percentile labels are visibly rendered, none are null or blank, and the card layout matches the existing Card/CardHeader/CardContent structure.

---

### TC-02 — Stock detail page: Short-history stock renders NA + reason for each component

**Type:** browser
**Preconditions:**
- A short-history stock (e.g., ARM or recent IPO) exists in the database
- `/api/stocks/{ticker}` returns null or indicates insufficient history for the new fields

**Steps:**
1. Navigate to `/stocks/{short-history-ticker}` (e.g., `/stocks/ARM`)
2. Locate the Risk-budget card
3. For each component that lacks sufficient history, verify it displays "NA" + an explanatory reason (never a fabricated 0 or blank)
4. Verify the styling mirrors the existing `naInvalidation` warn-colored treatment (text-warn)

**Expected outcome:** All short-history components display honestly as NA with clear reason, no fabricated values.

**Pass criteria:** Every component lacking sufficient bars ≤ as-of displays "NA" + reason (e.g., "insufficient history"), styled consistently with existing NA patterns, no zero or blank cells.

---

### TC-03 — Stock detail page: Null invalidation level → distance-to-invalidation renders NA, no crash

**Type:** browser
**Preconditions:**
- A stock in the database has a null invalidation level (no thesis-invalidation defined)
- `/api/stocks/{ticker}` returns null for `invalidation.level` or the stock record

**Steps:**
1. Navigate to the detail page for a stock with null invalidation level
2. Locate the Risk-budget card
3. Verify the distance-to-invalidation component displays "NA" (never a divide-by-zero error or blank error page)
4. Confirm the page remains fully rendered and usable

**Expected outcome:** Absence of invalidation level is handled gracefully; distance-to-invalidation shows NA, no application crash.

**Pass criteria:** No error page, no console error, distance-to-invalidation renders NA safely.

---

### TC-04 — Leaderboard: Risk-budget columns re-read the SAME stored fields as detail card

**Type:** browser
**Preconditions:**
- Backend has computed risk-budget fields
- `/api/stocks` leaderboard endpoint returns the new fields on each row
- A spot-check stock has the same values on both detail card and leaderboard

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Locate the risk-budget columns (ATR%, downside volatility, overnight-gap, worst-20d, distance-to-invalidation %)
3. Identify a liquid stock row (e.g., AAPL)
4. Record the values shown in the leaderboard columns for that stock
5. Click the stock name to navigate to `/stocks/AAPL`
6. Read the same values from the Risk-budget card
7. Verify the leaderboard value equals the detail-card value exactly

**Expected outcome:** Leaderboard columns and detail card display identical values, confirming single-source serving.

**Pass criteria:** The spot-checked value (e.g., overnight-gap p95) is byte-identical on the leaderboard and detail page; no client recomputation occurred.

---

### TC-05 — Leaderboard columns: Sortability and NA-last ordering

**Type:** browser
**Preconditions:**
- Leaderboard is loaded with risk-budget columns
- Some stocks in the leaderboard have NA values (short history or missing data)

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Click the column header for one risk-budget component (e.g., "Overnight Gap p95")
3. Verify the leaderboard sorts by that column in ascending order
4. Observe that rows with NA values sort to the last position
5. Click the column header again to reverse sort (descending)
6. Verify NA rows still sort last (not first)

**Expected outcome:** Risk-budget columns are sortable; NA values consistently sort to the last position regardless of sort direction.

**Pass criteria:** Column sort works as expected, NA rows appear last in both ascending and descending sorts, following the existing fwd_/mdd_ pattern.

---

### TC-06 — Methodology endpoint: New risk-budget component entries are documented and complete

**Type:** api
**Preconditions:**
- Backend has added new entries to `config.methodology` glossary
- `build_catalog` has been invoked (via server start or test)

**Steps:**
1. Fetch `GET /api/methodology`
2. Parse the response JSON
3. Verify all six new entries exist (or are present as glossary terms):
   - overnight-gap-median
   - overnight-gap-p95
   - overnight-gap-worst
   - overnight-variance-share (share of 20-day return variance from overnight gaps)
   - worst-20d-window
   - distance-to-invalidation-%
4. For each entry, verify it has: `formula` (text description), `window` (time window or config reference), and `thresholds` (if applicable)
5. Verify no duplicate entries exist for these components

**Expected outcome:** `/api/methodology` contains complete glossary entries for all new risk-budget components.

**Pass criteria:** All six entries are present, each has a formula + window description, and `test_api_methodology.py` glossary spot-check passes for the new terms.

---

### TC-07 — Methodology endpoint: Catalog structure unchanged (only glossary extended)

**Type:** api
**Preconditions:**
- Backend methodology catalog has been served
- Test `test_methodology_endpoint_returns_catalog` asserts `kinds == {"setup","pattern"}`

**Steps:**
1. Fetch `GET /api/methodology`
2. Extract all entries with a `kind` field
3. Collect unique values of `kind`
4. Verify the set equals exactly `{"setup","pattern"}` (no new kinds added)
5. Count the total catalog entries (non-glossary, with a `kind` field)
6. Verify the count matches or exceeds the prior count (additive, no removals)

**Expected outcome:** The core catalog structure (setup + pattern kinds) is unchanged; glossary entries have been added but do not affect the kinds set.

**Pass criteria:** `kinds == {"setup","pattern"}` still holds; catalog entries are additive; all prior entries remain present.

---

### TC-08 — Unit test: Overnight-gap-profile function returns exact values for fixture data

**Type:** api
**Preconditions:**
- `test_indicators.py` has been written with a fixture test for `overnight_gap_profile`
- Fixture bars have known open/prior-close values

**Steps:**
1. Run `pytest apps/backend/tests/test_indicators.py::test_overnight_gap_profile_exact_values -v`
2. Verify the test passes
3. Inspect the test assertions to confirm:
   - median overnight-gap % is exact-valued
   - p95 overnight-gap % is exact-valued
   - worst (maximum) overnight-gap % is exact-valued
   - overnight variance share is exact-valued
4. Verify the insufficient-history path (bars < window size) returns `None`

**Expected outcome:** The pure function computes exact median/p95/worst gaps and variance share for fixture data; short history returns None.

**Pass criteria:** Test passes with assertions on exact numeric values (not ranges); insufficient-history path verified.

---

### TC-09 — Unit test: Worst-20d-window function returns exact values and handles short history

**Type:** api
**Preconditions:**
- `test_indicators.py` has a fixture test for `worst_20d_window`
- Fixture bars span at least 20 trading days with known close/open values

**Steps:**
1. Run `pytest apps/backend/tests/test_indicators.py::test_worst_20d_window_exact_values -v`
2. Verify the test passes
3. Inspect the test to confirm:
   - The most negative trailing 20-day return is computed exactly
   - The value matches an independent offline recomputation
   - Short-history path (bars < 20) returns `None`
4. Verify no lookahead occurred (only bars ≤ as-of used)

**Expected outcome:** The pure function computes the exact worst-20d window; short history returns None; no lookahead.

**Pass criteria:** Test passes; exact worst-20d value verified against independent calculation; insufficient-history returns None.

---

### TC-10 — Unit test: Stored row carries new risk-budget fields + percentiles, no weighted-score leakage

**Type:** api
**Preconditions:**
- `test_scoring.py` has an additive test for the stored row shape
- A snapshot scan has been run and rows collected

**Steps:**
1. Run `pytest apps/backend/tests/test_scoring.py::test_stored_row_has_risk_budget_fields -v`
2. Verify the test passes and confirms:
   - Each row dict carries new fields: `atr_pct`, `downside_vol`, `overnight_gap_median`, `overnight_gap_p95`, `overnight_gap_worst`, `overnight_var_share`, `worst_20d_window`, `distance_to_invalidation_pct`
   - Each field has a corresponding `_percentile` field (e.g., `overnight_gap_median_percentile`)
   - All percentile values fall in the range [0, 100]
3. Run `pytest apps/backend/tests/test_scoring.py::test_leadership_entry_quality_risk_unchanged -v`
4. Verify the three scores (Leadership / Entry Quality / Risk) are byte-identical with and without the new components present

**Expected outcome:** New fields are additive; percentiles are computed; core scores unchanged.

**Pass criteria:** All new fields + percentiles present on every row; Leadership/Entry Quality/Risk are byte-identical; test_scoring_window.py integration test passes (if run).

---

### TC-11 — Unit test: Byte-match spot check — overnight-gap value equals offline recomputation

**Type:** api
**Preconditions:**
- `test_scoring.py` has a spot-check test with a known stock and as-of date
- Fixture bars for that stock are available

**Steps:**
1. Run `pytest apps/backend/tests/test_scoring.py::test_overnight_gap_p95_byte_match_spot_check -v`
2. Verify the test passes and confirms:
   - The engine's computed overnight-gap p95 for a known stock/as-of equals the independent Python recomputation
   - The value is byte-identical (not a range match)
3. Confirm the test uses only bars ≤ as-of and applies the configured `gap_window`

**Expected outcome:** The engine's gap computation is correct and matches independent validation.

**Pass criteria:** Test passes; spot-check value is byte-identical to offline recomputation; no lookahead in the calculation.

---

### TC-12 — Regression: J-01, J-02, J-03 still show evidence badges and byte-identical scores on `/stocks` and detail

**Type:** browser
**Preconditions:**
- Required-still-passing journeys J-01, J-02, J-03 have passing browser tests
- `/stocks` leaderboard and `/stocks/{ticker}` detail pages are unmodified in structure

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Verify each row's score area displays an evidence badge ("Proven" or "Not yet proven")
3. Record one row's three score values (Leadership / Entry Quality / Risk)
4. Click that stock to open its detail page
5. Verify the same three scores are displayed with the same values and badges
6. Repeat for two additional stocks
7. Verify all badges render correctly and badges are consistent between views

**Expected outcome:** Evidence badges remain present and byte-identical across leaderboard and detail views; scores unchanged.

**Pass criteria:** All rows show evidence badges; J-01/J-02/J-03 acceptance criteria still met; no score regressions.

---

### TC-13 — Regression: J-05 (Evidence ledger) renders without obstruction on touched pages

**Type:** browser
**Preconditions:**
- J-05 (Evidence ledger) passing test exists
- The new risk-budget card is now present on `/stocks/{ticker}`

**Steps:**
1. Navigate to `/stocks/{ticker}` (any liquid stock)
2. Scroll the page to verify the new Risk-budget card is rendered below existing cards
3. Verify the Evidence badge(s) on score elements are still present and clickable
4. Click an evidence badge to verify it navigates to or expands the evidence drill-down correctly
5. Verify no visual overlap or obstruction between the new card and evidence UI

**Expected outcome:** New card is additive; evidence ledger navigation is unaffected.

**Pass criteria:** J-05 acceptance criteria met; no overlap or broken links; evidence UI fully functional.

---

### TC-14 — Regression: J-10 (Deep price chart) still renders on `/stocks/{ticker}` detail page

**Type:** browser
**Preconditions:**
- J-10 passing test exists
- `/stocks/{ticker}` page renders with the new risk-budget card

**Steps:**
1. Navigate to `/stocks/AAPL` (or any stock used in J-10)
2. Locate the deep price chart section (should be present on the detail page)
3. Verify the chart renders with all lines/overlays intact
4. Verify the chart is not obscured by the new Risk-budget card
5. Interact with the chart (scroll, hover) to verify responsiveness

**Expected outcome:** Deep price chart renders without regression or overlap.

**Pass criteria:** J-10 chart is fully visible and interactive; no layout shift or obstruction from new card.

---

### TC-15 — Regression: J-12 (Methodology) and `/methodology` documentation unchanged for prior components

**Type:** browser
**Preconditions:**
- J-12 passing test exists
- `/api/methodology` endpoint still serves prior entries

**Steps:**
1. Navigate to `/methodology` (or similar methodology surface)
2. Verify all prior methodology entries are still documented (e.g., ATR%, HV, Leadership, Entry Quality)
3. Verify the new risk-budget entries are also present
4. Click on a prior entry (e.g., "ATR%") and verify its documentation is unchanged
5. Verify the page layout and navigation are unaffected

**Expected outcome:** Prior methodology documentation intact; new entries additive.

**Pass criteria:** J-12 acceptance criteria still met; no prior entries removed or altered; new entries visible.

---

### TC-16 — Regression: J-13 (`/data` endpoint) and snapshot payload shape updated additively

**Type:** api
**Preconditions:**
- `test_snapshot_payload_shape.py` has been updated for the new fields
- `GET /api/stocks` and `GET /api/stocks/{ticker}` serve the updated payloads

**Steps:**
1. Run `pytest apps/backend/tests/test_snapshot_payload_shape.py -v`
2. Verify the test passes and confirms:
   - The StockRow payload includes the new nullable risk-budget fields
   - The payload schema is additive (no prior fields removed)
   - All new fields are properly typed (e.g., `float | None`)
3. Fetch `GET /api/stocks/AAPL` and verify the response includes the new fields

**Expected outcome:** Snapshot payload shape is extended additively; prior structure intact.

**Pass criteria:** Payload test passes; J-13 acceptance criteria met; new fields present and properly typed in the response.

---

### TC-17 — Regression: J-20 (Preflight banner) renders correctly on touched pages

**Type:** browser
**Preconditions:**
- J-20 passing test exists
- Preflight banner logic is unchanged

**Steps:**
1. Navigate to `/stocks` leaderboard
2. Verify the preflight banner (market status/regime) renders at the top
3. Navigate to `/stocks/{ticker}` detail page
4. Verify the preflight banner still renders at the top of the detail page
5. Verify banner content is correct (current regime, data freshness, etc.)

**Expected outcome:** Preflight banner renders without regression on both leaderboard and detail pages.

**Pass criteria:** J-20 acceptance criteria still met; banner visible and correct on all touched surfaces.

---

### TC-18 — Snapshot regeneration: Served snapshots carry real (non-null) new-field values after DB rebuild

**Type:** api
**Preconditions:**
- The database has been rebuilt from seed with the new code
- Bootstrap and latest snapshot runs have been regenerated (bounded, not full-universe backfill)

**Steps:**
1. Fetch `GET /api/stocks/AAPL?asof=<bootstrap-date>`
2. Verify the response includes the new fields (atr_pct, downside_vol, overnight_gap_median, etc.)
3. Verify all new fields are non-null for the liquid stock
4. Fetch `GET /api/stocks/AAPL?asof=<latest-date>`
5. Verify the latest snapshot also carries real values for the new fields
6. Verify that historical snapshots (if queried) have NA for the new fields (not backfilled)

**Expected outcome:** Bootstrap and latest snapshots carry real new-field values; historical rows stay NA.

**Pass criteria:** Served bootstrap + latest snapshots have non-null new values; historical rows honestly NA; no OOM or full-universe backfill occurred.

---

### TC-19 — Config: New settings present and validated in IndicatorsCfg

**Type:** api
**Preconditions:**
- `config.py` has been updated with `gap_window` and `worst_window_days` fields
- `config.yaml` has been set with values for these fields

**Steps:**
1. Run `pytest apps/backend/tests/test_config.py -v -k "indicators"` 
2. Verify the test passes and confirms:
   - `IndicatorsCfg` has `gap_window` and `worst_window_days` fields
   - Both are typed as integers and required (not optional)
   - Validation ensures both are positive (> 0)
   - `max_lookback_bars` computation includes both windows (e.g., `max(gap_window, worst_window_days, hv_window, ...)`)
3. Verify `config.yaml` has values set for both fields (e.g., `worst_window_days: 20`)

**Expected outcome:** Config fields are properly validated and folded into max_lookback_bars logic.

**Pass criteria:** Config test passes; fields are positivity-validated; max_lookback_bars includes both windows.

---

## Summary

**Total test cases:** 19
- **Browser tests:** 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-12, TC-13, TC-14, TC-15, TC-17)
- **API tests:** 8 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-16, TC-18, TC-19)
- **Artifact checks:** 0 (all tests are executable)

**Coverage areas:**
- **Risk-budget card and leaderboard columns:** TC-01, TC-02, TC-03, TC-04, TC-05, TC-18
- **Methodology and documentation:** TC-06, TC-07, TC-12, TC-15
- **Unit/integration tests:** TC-08, TC-09, TC-10, TC-11, TC-19
- **Regression (required-still-passing):** TC-12, TC-13, TC-14, TC-15, TC-16, TC-17
- **Configuration and data shape:** TC-16, TC-18, TC-19

All test cases derive directly from the phase spec's DEFINITION OF DONE and TESTING REQUIREMENTS sections. Tests are specific, reproducible, and verify that the risk-budget card displays correctly with proper source data, handles short history gracefully, maintains single-source serving on the leaderboard, and introduces no regressions to required-still-passing journeys.
