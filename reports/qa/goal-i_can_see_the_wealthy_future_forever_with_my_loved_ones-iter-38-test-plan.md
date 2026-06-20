# Goal Iteration 38 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38  
**Date:** 2026-06-20  
**Frontend Present:** yes

## Phase Goal

Add a `?full=true` serialization to `GET /api/market-phase` serving the complete causal phase/severity/P(bear) timeline; render a two-pane synchronized cross-view chart on the Dashboard showing the same index lines under both the regime lens (top) and phase/severity lens (bottom); and restructure the Dashboard to show a compact at-a-glance regime + phase/severity summary at first paint with supporting breadth/sectors/candidates/themes cards moved into a collapsed "More detail" section.

## Test Cases

### TC-01 — Full-history market-phase serialization is byte-identical to engine

**Type:** api  
**Preconditions:** Backend running; database seeded with historical snapshots and index bars.

**Steps:**
1. Start backend on port 8000: `python -m uvicorn apps.backend.app.main:app --port 8000`
2. Fetch `GET /api/market-phase?full=false` (default card payload)
3. Fetch `GET /api/market-phase?full=true` (full timeline)
4. In Python, load the same as-of date through `compute_market_phase()` and extract `timeline_full`
5. Compare the full-history array from the API response with the engine's `timeline_full` byte-for-byte

**Expected outcome:** The API's `timeline_full` field matches the engine's computed `timeline_full` exactly (same `date`, `phase`, `p_bear`, `severity` for each point).

**Pass criteria:** `md5(api_response['timeline_full']) == md5(engine_timeline_full)` and the count of timeline points matches.

---

### TC-02 — Full=false default is byte-identical to legacy card payload

**Type:** api  
**Preconditions:** Backend running; a successful baseline fetch of `GET /api/market-phase` from iter-37 committed.

**Steps:**
1. Start backend on port 8000
2. Fetch `GET /api/market-phase` (no query param; defaults to `full=false`)
3. Compare response body to the iter-37 baseline payload (excluding `timeline_full` field if present in v2 response structure)

**Expected outcome:** The bounded `timeline` tail, `total_timeline_dates`, episodes, recovery-turn, and retrospective fields are identical to iter-37.

**Pass criteria:** `GET /api/market-phase?full=false` produces a byte-identical card payload to the pre-iter-38 endpoint (the disclosed tail is unchanged; any new `timeline_full` field is absent in the default response).

---

### TC-03 — Full timeline is strictly causal (no-lookahead) per point

**Type:** api  
**Preconditions:** Backend running; database with multi-year snapshots and index bars.

**Steps:**
1. Start backend on port 8000
2. Fetch `GET /api/market-phase?full=true` with a known as-of date D (e.g., 2023-06-30)
3. Extract the full `timeline_full` array
4. For each point P in the timeline dated ≤ D, remove all bars/snapshots dated > D from the engine and re-compute `compute_market_phase` for the same date
5. Assert that the phase, severity, and p_bear for point P remain unchanged

**Expected outcome:** A point's values depend only on bars ≤ the point's date; removing future bars never changes an earlier point.

**Pass criteria:** Tail-invariance test passes: for all points dated ≤ D, re-computing with only bars ≤ D yields identical phase/severity/p_bear.

---

### TC-04 — Full timeline contains no smoothed/true-bear value

**Type:** api  
**Preconditions:** Backend running; `market_phase.py` contains both causal and retrospective paths.

**Steps:**
1. Start backend on port 8000
2. Fetch `GET /api/market-phase?full=true`
3. Extract the full `timeline_full` array
4. In Python, inspect the response schema: assert that `timeline_full` points contain only `date`, `phase`, `p_bear`, `severity` (the causal fields)
5. Grep the backend diff: confirm NO code path from `retrospective_cached` into `timeline_full` assembly

**Expected outcome:** The full timeline contains only causal-computed values; no smoothed/true-bear retrospective value leaks into the served series.

**Pass criteria:** (a) Response schema contains only 4 fields per timeline point: `date`, `phase`, `p_bear`, `severity`. (b) Grep diff shows no import or call to `retrospective_cached` in the `timeline_full` code path.

---

### TC-05 — Phase-band primitive renders config-driven phase colors, no hardcoded hex

**Type:** artifact  
**Preconditions:** Phase-band-primitive.ts created; design tokens defined in globals.css.

**Steps:**
1. Read `apps/frontend/components/phase-band-primitive.ts`
2. Grep for hardcoded hex colors (e.g., `#[0-9a-fA-F]{6}`) or magic phase strings
3. Confirm all phase→color mappings read from design tokens or a config-driven lookup
4. Verify NA/empty phase → no band (no fallback band fabricated)

**Expected outcome:** All phase colors come from design tokens or config; no hardcoded hex literals in the primitive.

**Pass criteria:** Grep finds 0 matches for hardcoded hex in phase-band-primitive.ts; all phase mappings reference `getPhaseColor()` or a token lookup; NA-phase case returns null/undefined (no band).

---

### TC-06 — Two-pane chart renders both panes with shared time scale

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8000; Dashboard loaded.

**Steps:**
1. Start backend on port 8000
2. Start frontend on port 3000: `npm run dev` in `apps/frontend`
3. Navigate to `http://localhost:3000/` (Dashboard)
4. Wait for the page to load and settle
5. Scroll down to view the chart area below the Major Indexes card
6. Take a screenshot of the full two-pane chart (scroll into viewport if below the fold)
7. Verify pane 0 (top) shows the existing index lines + regime bands + as-of marker
8. Verify pane 1 (bottom) shows the SAME index lines + phase-colored bands + a severity line + a filtered P(bear) line

**Expected outcome:** Both panes render; pane 0 unchanged (index lines + regime bands + as-of marker); pane 1 displays phase bands, severity, and P(bear) line over the same index lines.

**Pass criteria:** Screenshot shows (a) two distinct chart panes stacked vertically; (b) pane 0 with regime bands visible; (c) pane 1 with phase-colored bands + severity line + P(bear) line all rendered; (d) both panes share the same x-axis scale (dates align across panes).

---

### TC-07 — Synchronized zoom: dragging one pane zooms both

**Type:** browser  
**Preconditions:** Frontend and backend running; Dashboard loaded with two-pane chart visible.

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Take a screenshot of the full chart (before zoom) – record the visible date range (e.g., "2024-01-01 to 2026-06-20")
3. Click and drag in pane 0 (top pane) to select/zoom a narrower window (e.g., "2025-06-01 to 2026-01-01")
4. Release the drag
5. Wait 500ms for chart to settle
6. Take a screenshot of both panes after the zoom
7. Visually inspect pane 1: verify the date range displayed matches pane 0's new window

**Expected outcome:** Both panes zoom to the same date window; the visible range on pane 1 matches pane 0 after the drag.

**Pass criteria:** Before/after screenshots show (a) pane 0 date range changed by drag; (b) pane 1 date range ALSO changed to match pane 0 (x-axis labels align); (c) the two frame md5sums differ (proving a zoom occurred, not a stale/cached frame).

---

### TC-08 — Bottom pane carries as-of marker, post-as-of data display-only

**Type:** browser  
**Preconditions:** Frontend and backend running; an as-of date set to a historical date (not today).

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Click the as-of date selector (the global date picker)
3. Select a historical date (e.g., 2025-12-31)
4. Release and wait for the chart to refresh
5. Scroll the two-pane chart into full viewport
6. Take a screenshot of pane 1 (bottom pane)
7. Locate the vertical as-of marker line (should be at the selected date)
8. Verify that bars/bands dated after 2025-12-31 are rendered behind/below the marker (display-only, not feeding scores)

**Expected outcome:** The as-of marker appears on pane 1 at the selected historical date; any data beyond the marker is visible but visually de-emphasized (e.g., lower alpha, behind a line).

**Pass criteria:** Screenshot shows (a) vertical as-of marker at the selected date; (b) data after the marker is rendered but visually distinct (lower opacity, behind marker, or clearly labelled display-only); (c) phase bands and P(bear) line after the marker do not change the severity score displayed in the compact summary (indicating they feed no as-of value).

---

### TC-09 — Early as-of with no causal history renders honest-empty bottom pane

**Type:** browser  
**Preconditions:** Frontend and backend running; ability to set as-of to a very early date (before phase history exists).

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Click the as-of date selector
3. Select a date before phase history exists in the data (e.g., 2021-02-01, if phase history starts 2021-10)
4. Release and wait for chart to refresh
5. Take a screenshot of pane 1
6. Verify pane 1 has no phase bands, no severity line, no P(bear) line (honest empty)

**Expected outcome:** Pane 1 renders without content (no bands, no lines); pane 0 may still show index data if it exists for that date.

**Pass criteria:** Screenshot shows pane 1 as an empty chart frame (no colored bands, no lines) when as-of is before causal phase history.

---

### TC-10 — J-98 first paint: compact summary + chart only, "More detail" collapsed

**Type:** browser  
**Preconditions:** Frontend and backend running; Dashboard loaded for the first time (no local state).

**Steps:**
1. Start frontend and backend fresh
2. Navigate to `http://localhost:3000/` (Dashboard)
3. Wait for page to fully load and render
4. Take a screenshot of the entire viewport from top to bottom without scrolling
5. Inspect the page structure:
   - Verify a compact "Market Regime" figure is visible at the top (label + 0–100 score)
   - Verify a compact "Market Phase & Severity" figure is visible at the top (label + 0–100 severity + P(bear))
   - Verify the two-pane chart is visible below the summary
   - Verify breadth metrics, Top Sectors, Candidate Counts, Top Themes cards are NOT visible in the first paint (collapsed)

**Expected outcome:** First paint shows only the compact at-a-glance summary and the cross-view chart; supporting detail cards are hidden (in a collapsed "More detail" section).

**Pass criteria:** Screenshot shows (a) two compact summary figures at top; (b) no breadth/sectors/candidates/themes cards visible without scrolling; (c) a "More detail" disclosure control is present (e.g., "Show more" button or collapsed section).

---

### TC-11 — Compact summary figures display named component breakdown (no bare numbers)

**Type:** browser  
**Preconditions:** Frontend and backend running; Dashboard loaded.

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Hover over or click on the "Market Regime" figure (label + 0–100 score)
3. Verify a component breakdown tooltip or popover appears showing named components (e.g., "Regime: Bullish, Score: 75 = 0.5×Momentum(65) + 0.3×Breadth(90) + 0.2×VIX(40)")
4. Close the popover
5. Repeat for the "Market Phase & Severity" figure
6. Verify its breakdown includes phase label, severity score, and component contributors

**Expected outcome:** Each figure exposes its named component breakdown; no score appears as a bare number.

**Pass criteria:** (a) Hovering or clicking the summary figures reveals a popover/tooltip with named components. (b) Both figures include their respective component breakdowns. (c) No bare score is left without an explanation.

---

### TC-12 — "More detail" section expands/collapses; breadth/sectors/candidates/themes present

**Type:** browser  
**Preconditions:** Frontend and backend running; Dashboard loaded with "More detail" collapsed.

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Scroll down to find the "More detail" disclosure control (below the chart)
3. Click the expand button
4. Wait 300ms for animation to settle
5. Take a screenshot
6. Visually verify the previously-collapsed breadth metrics card is visible
7. Verify Top Sectors card is visible
8. Verify Candidate Counts card is visible
9. Verify Top Themes card is visible
10. Click collapse to fold the section again
11. Take a screenshot
12. Verify the cards are no longer visible (section is collapsed)

**Expected outcome:** The "More detail" section toggles open/closed; when open, all supporting cards (breadth, sectors, candidates, themes) are present and functional.

**Pass criteria:** (a) Expand button toggles the section open. (b) When open, all four card types are visible. (c) Collapse button hides them again. (d) Data in the cards (if any) matches the already-served values.

---

### TC-13 — Compact summary figures equal server values; J-06 single-source check

**Type:** browser + api  
**Preconditions:** Frontend and backend running; a known as-of date set.

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Set the as-of date to a specific date (e.g., 2025-12-31)
3. Take a screenshot of the "Market Regime" and "Market Phase & Severity" figures
4. Fetch `GET /api/dashboard?as_of=2025-12-31` from the backend
5. Fetch `GET /api/market-phase?as_of=2025-12-31&full=false` from the backend
6. Verify the regime label and score in the first API response match the displayed regime figure
7. Verify the phase label, severity score, and P(bear) in the second API response match the displayed phase/severity figure

**Expected outcome:** The UI figures display the exact values served by the API endpoints; no client-side recomputation.

**Pass criteria:** (a) Regime figure label == `api/dashboard.regime_label`. (b) Regime score == `api/dashboard.regime_score`. (c) Phase figure label == `api/market-phase.phase`. (d) Severity == `api/market-phase.severity`. (e) P(bear) == `api/market-phase.p_bear_filtered`.

---

### TC-14 — Risk-Off regime → zero Actionable in cards, J-07 gate untouched

**Type:** browser + api  
**Preconditions:** Frontend and backend running; database seeded with a Risk-Off date.

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Set the as-of date to a known Risk-Off date (e.g., 2022-10-15 during the bear market)
3. Take a screenshot of the "Market Regime" figure (should show "Risk-Off")
4. Scroll to the Candidate Counts card in the "More detail" section (expand if needed)
5. Verify the card shows "Actionable: 0"
6. Fetch `GET /api/dashboard?as_of=2022-10-15`
7. Verify the response shows `regime_label: "Risk-Off"` and `actionable_count: 0`

**Expected outcome:** When the regime is Risk-Off, the Actionable count is zero; the Risk-Off→Actionable gate is not bypassed.

**Pass criteria:** (a) Regime figure displays "Risk-Off". (b) Candidate Counts card shows "Actionable: 0" or zero indicator. (c) API confirms `actionable_count: 0`.

---

### TC-15 — Chart pane 0 unchanged: index lines + regime bands + as-of marker (J-49 compliance)

**Type:** browser  
**Preconditions:** Frontend and backend running; baseline screenshot from iter-37 pane 0 (top chart).

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Scroll to the chart area
3. Take a screenshot of pane 0 (top pane) on the same as-of date as the iter-37 baseline
4. Compare visually to the iter-37 baseline screenshot:
   - Index lines should be identical (same colors, same % values at same dates)
   - Regime bands should be identical (same phase colors, same date spans)
   - As-of marker should be identical (same vertical line position, same styling)

**Expected outcome:** Pane 0 is byte-identical to iter-37's chart.

**Pass criteria:** Pane 0 screenshot md5 == iter-37 baseline md5 (or visual diff shows 0 pixel changes in the index/regime renderings).

---

### TC-16 — Full pytest suite passes; tsc --noEmit exits 0

**Type:** artifact  
**Preconditions:** Dev changes committed; backend and frontend built.

**Steps:**
1. Run the full backend test suite: `cd apps/backend && python -m pytest --tb=short -v 2>&1 | tail -20`
2. Capture the final line (should be "X passed, Y failed, Z skipped in Ls")
3. Confirm exit code is 0 (no failures)
4. Run TypeScript type-check: `cd apps/frontend && npx tsc --noEmit`
5. Confirm exit code is 0 (no type errors)

**Expected outcome:** Full suite green; zero type errors.

**Pass criteria:** (a) Pytest final line shows `0 failed`. (b) Pytest exit code is 0. (c) tsc exit code is 0.

---

### TC-17 — No magic numbers in engine CALC_FILES; test_no_magic_numbers green

**Type:** artifact  
**Preconditions:** Dev diff available; backend test suite runs.

**Steps:**
1. Run the magic-numbers test: `cd apps/backend && python -m pytest tests/test_no_magic_numbers.py -v`
2. Capture output

**Expected outcome:** The test passes (no new magic numbers in engine calc files).

**Pass criteria:** Test status is PASSED; exit code is 0.

---

### TC-18 — No second date state: grep diff for new date useState, window/document keydown, global as-of write

**Type:** artifact  
**Preconditions:** Dev diff available; frontend changes visible.

**Steps:**
1. Generate the diff: `git diff HEAD~1 apps/frontend -- . 2>/dev/null | head -500`
2. Grep for `useState.*date` (new date state): `grep -c "useState.*date" <diff>`
3. Grep for `window\.addEventListener\|document\.addEventListener` with `keydown` or `keyup`: `grep -E "addEventListener.*key(down|up)" <diff>`
4. Grep for writes to global as-of (e.g., `setAsOf\(` called from chart/zoom logic): `grep -B5 -A5 "pane.*zoom\|handleZoom" <diff> | grep setAsOf`
5. Grep for native `input[type=date]`: `grep -i "input.*type.*date" <diff>`

**Expected outcome:** No new date state, no chart-driven writes to global as-of, 0 native date inputs added.

**Pass criteria:** All grep counts are 0 (no matches).

---

### TC-19 — J-43/J-13 smoke: as-of switch drives both panes

**Type:** browser  
**Preconditions:** Frontend and backend running; Dashboard loaded.

**Steps:**
1. Load Dashboard at `http://localhost:3000/`
2. Note the visible date range on both panes (e.g., "2024-01-01 to 2026-06-20")
3. Click the global as-of date picker
4. Select a new historical date (e.g., 2023-06-30)
5. Release and wait for both charts to refresh
6. Take a screenshot
7. Verify pane 0 is updated (new regime bands, new as-of marker position)
8. Verify pane 1 is updated (new phase bands, new severity/P(bear) values, new as-of marker position)
9. Verify both panes show the same date range

**Expected outcome:** Both panes refresh to the new as-of date; they remain synchronized.

**Pass criteria:** (a) As-of marker moves to the new date on both panes. (b) Pane 0 regime bands updated. (c) Pane 1 phase bands, severity, and P(bear) updated. (d) Both panes display the same visible date range.

---

### TC-20 — No new endpoints, no new snapshot column, no rebuild required

**Type:** artifact  
**Preconditions:** Dev diff available; backend code reviewed.

**Steps:**
1. Grep the backend diff for new route/endpoint definitions: `grep -E "@router\.|@app\." <diff> | grep -v "market_phase.*full"`
2. Grep the snapshot model for new columns: `grep -E "class.*Snapshot|Column\(" <diff> | head -20`
3. Grep for `kind:"rebuild"` or `snapshot_rebuild` in tests: `grep -i rebuild <diff>`
4. Verify the `market_phase_cached` path is still used (not a new cache): `grep -E "market_phase_cached|dataset_version" <diff>`

**Expected outcome:** No new endpoints (only the `full` query param added to existing `/api/market-phase`); no new snapshot columns; no rebuild triggered; existing cache reused.

**Pass criteria:** (a) Grep finds 0 new route definitions. (b) Grep finds 0 new snapshot columns. (c) Grep finds 0 `kind:"rebuild"` mentions. (d) `market_phase_cached` path unchanged (or confirmed to be reused in the code).

---

## Summary

**Total test cases:** 20  
**API tests:** 5 (TC-01, TC-02, TC-03, TC-04, TC-13)  
**Browser tests:** 10 (TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-14, TC-19, combined with TC-13's screenshot)  
**Artifact checks:** 5 (TC-05, TC-16, TC-17, TC-18, TC-20)

**Key assertion:** The iteration delivers J-97 (two-pane synchronized cross-view chart) and J-98 (Dashboard at-a-glance restructure) with no recomputation, no new endpoints, no second date state, and the full pytest suite green.
