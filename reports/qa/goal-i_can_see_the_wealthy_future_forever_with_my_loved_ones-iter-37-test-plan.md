# Goal Iteration 37 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Date:** 2026-06-19
**Frontend Present:** yes

## Phase Goal

Restore the load-once bar-cache invariant broken by iter-36, optimize `/api/data` read performance, and live-verify the `/data` page renders the membership-timeline and coverage-diagnostic surfaces reliably under single-user and concurrent-reader conditions.

## Test Cases

### TC-01 — Load-once invariant restored for zero-bar candidate-pool symbols

**Type:** api
**Preconditions:** 
- Backend test suite is available
- Database contains candidate-pool symbols with zero bars in `daily_prices`

**Steps:**
1. Run `pytest apps/backend/tests/test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once -xvs`

**Expected outcome:** Test passes with no failures; the assertion `load_count_per_symbol <= 1` holds for every symbol including zero-bar candidates.

**Pass criteria:** 
- Exit code 0
- `assert 3 == 1` no longer appears in output
- Each candidate-pool symbol is loaded at most once during the K-date parallel backfill

---

### TC-02 — Membership-timeline payload byte-identity preserved

**Type:** api
**Preconditions:**
- Backend is running with or without the bar-cache optimization
- The same database state before and after the fix

**Steps:**
1. Call `GET /api/data` with the current implementation
2. Extract the `membership_timeline` field from the response
3. Replay the same call with the pre-fix code
4. Compare the two `membership_timeline` JSON payloads byte-for-byte

**Expected outcome:** Both responses contain identical `membership_timeline` arrays with the same symbols, entry/exit dates, and three honesty labels (survivorship, warm-up, universe-relative).

**Pass criteria:**
- Membership timeline arrays are byte-identical
- Excluded-by-reason counts (below_history, below_price, below_ADV) unchanged
- Admitted symbol set unchanged
- No new symbols appear; no existing symbols disappear

---

### TC-03 — Score output byte-identity preserved

**Type:** api
**Preconditions:**
- Database contains complete bar history for test symbols
- A specific as-of date D is selected with populated snapshots

**Steps:**
1. Call `score_stocks(D)` with the fixed implementation
2. Serialize the response (rows, scores, buckets, setups, VCP) to JSON
3. Replay the same call with the pre-fix code path (no-cache)
4. Serialize and compare byte-for-byte

**Expected outcome:** Both implementations return identical `score_stocks(D)` output with no score changes, no bucket reassignments, no setup status changes.

**Pass criteria:**
- Score values per symbol unchanged (6 canonical scores)
- Bucket assignments (A–E) unchanged
- Setup status unchanged
- VCP (VCP score) unchanged
- Row count and admitted symbol membership unchanged

---

### TC-04 — No-bar candidate-pool symbol counts as zero trailing bars from cache

**Type:** api
**Preconditions:**
- A candidate-pool symbol with zero bars in `daily_prices` exists (e.g., a symbol in the universe but no price history)
- The prefilled bar cache is active

**Steps:**
1. Query the prefilled cache for trailing bar count for a zero-bar candidate symbol
2. Verify the count is sourced from the cache, not a lazy per-date load
3. Instrument the cache loader to count "number of times this symbol was loaded"
4. Run a K-date backfill (10+ dates) calling `trailing_count(sym, asof)` on each date
5. Assert the load count for the zero-bar symbol is exactly 1 (prefill only)

**Expected outcome:** The zero-bar symbol returns a trailing count of 0 from the cache on every call; the loader is invoked exactly once for prefill, never on subsequent dates.

**Pass criteria:**
- `trailing_count(zero_bar_symbol, any_asof)` returns 0
- Symbol loader call count == 1 (prefill only)
- No per-date re-loads occur

---

### TC-05 — GET /api/data sub-second response time (if coverage optimization lands)

**Type:** api
**Preconditions:**
- Backend is warm (first boot cycle complete, background warm-up done)
- No active concurrent requests
- The coverage-precompute cache is populated

**Steps:**
1. Measure time to call `GET /api/data` on a warm backend
2. Compare total latency (not including network/browser rendering)

**Expected outcome:** Response time is sub-second (< 1000 ms) for the full payload including membership-timeline and coverage diagnostic.

**Pass criteria:**
- Total request latency < 1000 ms
- Response includes `membership_timeline` (non-empty array)
- Response includes per-date `coverage_diagnostic` with admitted/excluded counts
- `db_ok: true` in response

---

### TC-06 — GET /api/data under concurrent reader does not exhaust pool

**Type:** api
**Preconditions:**
- Backend is running with a DB connection pool (size 5 + overflow 10)
- First `/api/data` request is in flight

**Steps:**
1. Start a `GET /api/data` request (do not wait for completion)
2. After 100 ms, start a second concurrent `GET /api/data` request
3. Wait for both to complete
4. Inspect the response bodies and HTTP status codes

**Expected outcome:** Both requests complete successfully; neither returns `db_ok: false` or a skeleton frame; no 503 Service Unavailable.

**Pass criteria:**
- First request: HTTP 200, `db_ok: true`, full `membership_timeline` payload
- Second request: HTTP 200, `db_ok: true`, full `membership_timeline` payload
- No connection pool exhaustion errors in logs

---

### TC-07 — /data page renders membership-timeline chart (live browser, J-96)

**Type:** browser
**Preconditions:**
- Frontend is running on localhost:3000
- Backend is running and warmed up
- `/api/data` endpoint responds within ~30 s

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Wait for page hydration (readiness: "ready", max 30 s)
3. Check DOM for the membership-timeline chart container
4. Scroll the chart panel into the viewport if below the fold
5. Verify the chart renders (canvas or SVG with visible bars/line)
6. Capture screenshot as `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37-evidence/TC-07-timeline-chart.png`

**Expected outcome:** The page hydrates; the membership-timeline chart is visible; the chart shows a rising step function from ~2021-10-18 with clear entry/exit transitions.

**Pass criteria:**
- Page navigates to `/data` without 404
- No "Checking backend…" skeleton frame persists
- Chart container is in the DOM
- Chart renders (pixels are present, not blank/white)
- Chart shows at least two distinct levels (rising step function)
- Screenshot dimensions match expected viewport (not truncated or tiny)

---

### TC-08 — /data page renders three honesty labels for membership-timeline (live browser, J-96)

**Type:** browser
**Preconditions:**
- `/data` page is fully hydrated (from TC-07)
- Membership-timeline panel is in viewport

**Steps:**
1. Inspect the membership-timeline chart area for legend/labels
2. Scroll the entire below-fold content panel into viewport
3. Verify the presence of three distinct honesty labels:
   - "Survivorship"
   - "Warm-up"
   - "Universe-relative"
4. Capture screenshot as `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37-evidence/TC-08-honesty-labels.png`

**Expected outcome:** All three labels are visible and properly positioned; they explain the membership-timeline caveats to the user.

**Pass criteria:**
- Text "Survivorship" appears in the DOM
- Text "Warm-up" appears in the DOM
- Text "Universe-relative" appears in the DOM
- Labels are styled and positioned (not hidden, not overflow-clipped)
- Screenshot shows all three labels in the panel viewport

---

### TC-09 — /data page renders per-date universe-resolution diagnostic (live browser, J-94)

**Type:** browser
**Preconditions:**
- `/data` page is fully hydrated
- Diagnostic panel is visible or scrollable to

**Steps:**
1. Locate the per-date universe-resolution diagnostic panel on `/data`
2. Verify the diagnostic displays admitted count + excluded-by-reason counts
3. Scroll through at least 5 different dates to verify the counts vary
4. Check for the three exclusion reasons:
   - `below_history` (insufficient bar history)
   - `below_price` (price filter applied)
   - `below_ADV` (average daily volume filter applied)
5. Capture screenshot as `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37-evidence/TC-09-diagnostic.png`

**Expected outcome:** The diagnostic panel shows per-date resolution counts; the excluded-by-reason breakdown is visible and changes as the date is explored.

**Pass criteria:**
- Diagnostic panel is rendered and not a skeleton
- At least one date shows non-zero excluded counts
- The three exclusion-reason labels (below_history, below_price, below_ADV) are present
- Admitted count + excluded counts reconcile (no missing data)
- Screenshot captures a non-empty diagnostic table or card view

---

### TC-10 — /stocks page still slides fast through membership tiers (live browser, J-93 re-smoke)

**Type:** browser
**Preconditions:**
- Frontend is running
- `/stocks` page loads and hydrates
- The as-of date is set to a historical date with membership transitions

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Wait for hydration
3. Set as-of date to a date with known membership tier transitions (e.g., ~2021-11-15)
4. Verify the stock count changes smoothly: 0 → 495 → 504 → 544
5. Measure time to render the full stock list (should be sub-second)

**Expected outcome:** The stock list updates quickly; the membership transition counts (0, 495, 504, 544) match the expected tier progression.

**Pass criteria:**
- Page navigates without error
- Stock count reflects the correct membership tier for the selected as-of date
- List renders in < 3 s
- No "Checking backend…" skeleton persists

---

### TC-11 — NVDA /stocks value matches Stock-Detail value (live browser, J-06 re-smoke)

**Type:** browser
**Preconditions:**
- `/stocks` page is rendered with NVDA in the list
- `/stocks/NVDA` (Stock-Detail) page is accessible

**Steps:**
1. Navigate to `/stocks` and locate NVDA in the list
2. Record the displayed score and bucket for NVDA (e.g., "Setup: VCP", "Bucket: A")
3. Click the NVDA row or navigate to `/stocks/NVDA`
4. Verify the Stock-Detail page shows the same score/bucket/setup values
5. Compare the two views

**Expected outcome:** Both `/stocks` and `/stocks/NVDA` show the same canonical score, bucket, and setup for NVDA.

**Pass criteria:**
- `/stocks` list value for NVDA == Stock-Detail page value for NVDA
- No discrepancy in score or bucket assignment
- Both views source from the same snapshot

---

### TC-12 — Risk-Off regime marks zero stocks as Actionable (live browser, J-07 re-smoke)

**Type:** browser
**Preconditions:**
- A historical date with Risk-Off regime is available (check scanner_runs for `regime='Risk-Off'`)
- Frontend is running

**Steps:**
1. Navigate to `/stocks` with as-of date set to a Risk-Off date
2. Check the "Actionable" filter state or badge count
3. Verify zero stocks are marked as Actionable
4. Verify all stocks in the list are marked as "Watchlist-only" or similar non-actionable status

**Expected outcome:** When regime is Risk-Off, the Actionable stock count is zero; all stocks are watchlist-only.

**Pass criteria:**
- Actionable stock count == 0 on Risk-Off dates
- No stock is marked as "Actionable" or in the buy/sell bins
- At least 100 stocks are present in the "Watchlist" tier
- Regime indicator shows "Risk-Off" for the selected date

---

### TC-13 — Exactly one date selector present (live browser, J-18 re-smoke)

**Type:** browser
**Preconditions:**
- Frontend is running
- Both `/data` and `/stocks` pages are accessible

**Steps:**
1. Navigate to `/stocks` page
2. Inspect the DOM for all `input[type=date]` elements
3. Count the total number of date input controls
4. Navigate to `/data` page
5. Repeat the count for date inputs
6. Check both pages for any hidden/aria-hidden date selectors

**Expected outcome:** Each page has exactly one visible date selector; no page-local date state duplicates exist.

**Pass criteria:**
- `/stocks` page: exactly 1 `input[type=date]`
- `/data` page: exactly 1 `input[type=date]` (or 0 if date is controller via other UI)
- No hidden/duplicate date pickers in the DOM
- All date-dependent content uses the single selected as-of date

---

### TC-14 — Dashboard market-phase and P(bear) unchanged (live browser, J-87/J-88 re-smoke)

**Type:** browser
**Preconditions:**
- Frontend is running
- Dashboard page is accessible

**Steps:**
1. Navigate to `/dashboard` or the home page where market-phase and P(bear) are displayed
2. Record the current market-phase and P(bear) values
3. Load the same page in a second window or tab (without refreshing)
4. Compare the values between the two views
5. Verify they match the expected canonical values from the backend

**Expected outcome:** Market-phase (e.g., "Expansion", "Bear Market") and P(bear) (e.g., 0.35) are displayed consistently and match the backend's computed values for the current as-of date.

**Pass criteria:**
- Market-phase label is present and correct
- P(bear) value is a number between 0 and 1
- Both values are consistent across page loads
- No transient skeleton or "loading…" state persists

---

### TC-15 — Fast snapshot reads for single-user fetch (live browser, J-15 re-smoke)

**Type:** browser
**Preconditions:**
- Backend is warm and fully initialized
- Frontend is running

**Steps:**
1. Measure the time to navigate from `/stocks` to `/stocks/NVDA` (Stock-Detail page)
2. Wait for full hydration
3. Measure the time to navigate back to `/stocks`
4. Measure the time to navigate to `/data` and wait for hydration
5. Record all latencies

**Expected outcome:** All page transitions complete quickly; Stock-Detail hydrates within 2–3 s; `/data` hydrates within 5–10 s (or sub-second if coverage optimization lands).

**Pass criteria:**
- `/stocks/NVDA` hydration: < 3 s
- `/stocks` page transitions: < 2 s (subsequent loads from cache)
- `/data` hydration: < 10 s (acceptable documented limit if optimization descoped)
- No 503 or timeout errors
- All pages render non-skeleton content

---

### TC-16 — Backend test suite: test_bar_cache.py passes

**Type:** artifact
**Preconditions:**
- Backend test suite is available
- pytest is installed

**Steps:**
1. Run `pytest apps/backend/tests/test_bar_cache.py -v`
2. Capture exit code and pass/fail summary

**Expected outcome:** All tests in test_bar_cache.py pass; the load-once invariant test (`test_kdate_backfill_loads_each_symbol_at_most_once`) shows assert value of 1 (not 3).

**Pass criteria:**
- Exit code == 0
- `test_kdate_backfill_loads_each_symbol_at_most_once` PASSED
- `test_cached_snapshot_equals_uncached_row_level` PASSED
- `test_cached_bars_asof_slices_le_d_identically` PASSED

---

### TC-17 — Backend test suite: membership-cache byte-identity tests pass

**Type:** artifact
**Preconditions:**
- Backend test suite is available
- Membership-timeline cache and data_manager modules are fully built

**Steps:**
1. Run `pytest apps/backend/tests/test_data_manager_membership_cache.py -v -k "byte_identity or warm_read"`
2. Capture pass/fail status

**Expected outcome:** Tests asserting byte-identity of `membership_timeline` before and after optimization pass; tests asserting warm reads do not recompute pass.

**Pass criteria:**
- Tests containing "byte_identity" or "warm_read" all pass
- No test shows `AssertionError` on payload comparison
- Exit code == 0

---

### TC-18 — Backend full pytest suite exits 0 (background async run)

**Type:** artifact
**Preconditions:**
- Backend is fully implemented with load-once fix applied
- Full test suite is launched asynchronously (nohup) by the pump
- Test suite has been running for 3–4 hours (typical duration)

**Steps:**
1. Wait for the nohup-launched pytest to complete (monitor `pytest --co -q | tail -1` for total test count)
2. Check the terminal output or log for the final summary line: `X passed, Y failed, Z warnings in NNs`
3. Record exit code (should be 0 for all-pass)

**Expected outcome:** Full pytest suite completes with zero failures; `exit 0` is returned.

**Pass criteria:**
- Final line shows `0 failed` (or omits "failed" entirely)
- Exit code == 0
- No `SIGTERM` or timeout (suite allowed to complete naturally)
- No regressions introduced in unrelated tests

---

## Summary

**Total test cases:** 18
- **API tests:** 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06)
- **Browser tests:** 9 (TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15)
- **Artifact checks:** 3 (TC-16, TC-17, TC-18)

**Critical path:** TC-01 (load-once restored) → TC-02/TC-03 (byte-identity preserved) → TC-05 (performance) → TC-07/TC-08/TC-09 (browser evidence for J-94 and J-96) → TC-18 (full suite green)

**Re-smoke journeys:** J-93 (TC-10), J-06 (TC-11), J-07 (TC-12), J-18 (TC-13), J-87/J-88 (TC-14), J-15 (TC-15)
