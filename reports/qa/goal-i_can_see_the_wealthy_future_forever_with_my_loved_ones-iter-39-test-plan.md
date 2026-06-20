# Iteration 39 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39
**Date:** 2026-06-20
**Frontend Present:** yes

## Phase Goal

Fix the `MarketPhaseCache` schema-versioning defect so `GET /api/market-phase?full=true` at the live current as-of serves `timeline_full` (a cache HIT, not only at fresh-compute dates), enabling the Dashboard's two-pane cross-view bottom pane to render phase-colored bands, 0–100 severity line, and filtered P(bear) line. Verify J-97 (synced cross-view) and J-98 (at-a-glance restructure) on live browser evidence.

## Test Cases

### TC-01 — Cache-HIT serves timeline_full field after schema-version fix

**Type:** api
**Preconditions:**
- Backend is running at `http://localhost:8835`
- A cache row exists for the live current as-of date (2026-06-16) from before the schema-version fix
- The cache row is keyed to the old stamp without schema-version component
- The backend code now includes the `SCHEMA_VERSION` constant folded into the cache key

**Steps:**
1. Make request: `curl -s http://localhost:8835/api/market-phase?asof=2026-06-16&full=true | jq '.timeline_full'`
2. Verify response includes the `timeline_full` key
3. Store the response JSON as `live_full_response.json`
4. Compute fresh cache miss by requesting a non-existent date: `curl -s http://localhost:8835/api/market-phase?asof=2025-12-31&full=true | jq '.timeline_full' > fresh_compute.json`
5. Compare byte-by-byte: `jq '.timeline_full' live_full_response.json > live_timeline.json` and `diff live_timeline.json fresh_compute.json`

**Expected outcome:**
- `timeline_full` key is present in the live current-as-of response (the cache HIT case that failed in iter-38)
- `timeline_full` is byte-identical between the cache HIT (live as-of) and a fresh compute (different date)

**Pass criteria:**
- HTTP 200 response from both requests
- `timeline_full` key exists in both responses
- `diff live_timeline.json fresh_compute.json` produces no output (byte-identical)
- The `timeline_full` value is a non-empty array of objects with keys `index`, `phase`, `severity`, `prob_bear`

---

### TC-02 — Card payload (?full=false) remains byte-identical after cache-key fix

**Type:** api
**Preconditions:**
- Backend is running at `http://localhost:8835`
- A pre-fix baseline card payload was captured (or will be captured fresh before running the fix)

**Steps:**
1. Make request: `curl -s http://localhost:8835/api/market-phase?asof=2026-06-16&full=false | jq -S '.' > card_post_fix.json`
2. Verify the response does NOT include `timeline_full` key
3. Compare against pre-fix baseline (or fresh compute): `curl -s http://localhost:8835/api/market-phase?asof=2025-12-31&full=false | jq -S '.' > card_fresh.json`
4. Byte-compare: `diff card_post_fix.json card_fresh.json`

**Expected outcome:**
- Card payload (`?full=false`) at cache HIT and fresh compute are byte-identical
- No `timeline_full` key appears in the card payload
- All existing keys (phase, severity, prob_bear, etc.) remain unchanged

**Pass criteria:**
- HTTP 200 from both requests
- `diff card_post_fix.json card_fresh.json` produces no output
- The `timeline_full` key does NOT appear in the card payload

---

### TC-03 — Retrospective payload stays byte-identical after schema-version fix

**Type:** api
**Preconditions:**
- Backend is running at `http://localhost:8835`
- The retrospective cache path (`market_phase.py:1103-1146`) includes the same `SCHEMA_VERSION` token in its cache key

**Steps:**
1. Make request: `curl -s 'http://localhost:8835/api/market-phase?asof=2026-06-16&full=false&fence=retrospective' | jq -S '.' > retro_post_fix.json`
2. Capture fresh-compute baseline: `curl -s 'http://localhost:8835/api/market-phase?asof=2025-12-31&full=false&fence=retrospective' | jq -S '.' > retro_fresh.json`
3. Byte-compare: `diff retro_post_fix.json retro_fresh.json`

**Expected outcome:**
- Retrospective payload (smoothed/true-bear fence) is byte-identical pre/post fix
- Fence logic and values (recovered, continuing, etc.) are unchanged

**Pass criteria:**
- HTTP 200 from both requests
- `diff retro_post_fix.json retro_fresh.json` produces no output
- The retrospective fence keys and values match exactly

---

### TC-04 — J-97 bottom pane renders at live current as-of with phase bands and severity line

**Type:** browser
**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is running at `http://localhost:3835`
- The cache-key fix is deployed
- Current date is 2026-06-16 (or the live as-of date in the system)
- Chrome MCP is connected at `http://localhost:9222`

**Steps:**
1. Navigate to `http://localhost:3835/`
2. Wait for the Dashboard to fully load (check for Major-indexes card visible)
3. Scroll down to reveal the two-pane cross-view chart (below the fold)
4. Observe the bottom pane of the chart
5. Take a screenshot of the fully rendered bottom pane: `screenshot bottom-pane-populated.png`
6. Verify visual elements: phase-colored bands, 0–100 severity line, filtered P(bear) line, as-of marker

**Expected outcome:**
- Bottom pane is NOT empty (the iter-38 failure case)
- Phase-colored bands are visible (colored by the config phase mapping from `lib/phase.ts`)
- 0–100 severity vertical axis is rendered
- A line chart showing the filtered P(bear) is visible above the severity line
- The as-of marker (vertical line) is visible on the chart at 2026-06-16

**Pass criteria:**
- Screenshot shows non-empty bottom pane with all four elements (bands, severity axis, P(bear) line, as-of marker)
- No skeleton loading state or "Checking backend" message in the pane
- Chart pixels are distinct from iter-38's empty-pane screenshot

---

### TC-05 — J-97 synced zoom produces two byte-distinct before/after frames

**Type:** browser
**Preconditions:**
- Bottom pane is fully rendered (from TC-04)
- Frontend is at `http://localhost:3835/`

**Steps:**
1. Take a baseline screenshot of the full two-pane chart showing both panes with full visible range: `screenshot zoom-before.png`
2. On the chart, zoom in on a specific time window (drag to select a range or use pinch-zoom, depending on chart library)
3. Take a second screenshot after the zoom is applied: `screenshot zoom-after.png`
4. Verify both panes updated their visible range synchronously
5. Compare file sizes and MD5 hashes: `md5sum zoom-before.png zoom-after.png`

**Expected outcome:**
- Both screenshots render non-empty chart panes
- Zoom action is visible (time range on x-axis differs between before/after)
- Top pane (regime) and bottom pane (phase/severity) both zoom to the same time window (synchronized)

**Pass criteria:**
- `md5sum zoom-before.png zoom-after.png` produces two distinct hashes (byte-distinct frames)
- File sizes are non-zero and non-trivial (not skeleton or blank frame)
- The visible time range on the x-axis differs between the two screenshots
- Both panes rendered the same time-axis range after zoom

---

### TC-06 — J-97 early as-of with no causal phase history shows honest-empty bottom pane

**Type:** browser
**Preconditions:**
- Frontend is at `http://localhost:3835/`
- An as-of date with insufficient historical data exists (e.g., very early date with no regime/phase history)

**Steps:**
1. Click the as-of date picker on the Dashboard
2. Select an early date (e.g., 2025-01-15, before sufficient backfill)
3. Wait for the page to load and render the new as-of
4. Scroll down to the two-pane chart
5. Observe the bottom pane state: should be empty (no bands, no severity line, no P(bear) line) or show minimal data
6. Take a screenshot: `screenshot early-asof-empty.png`

**Expected outcome:**
- Bottom pane is empty or shows zero data points (honest-empty state)
- No fabricated phase bands, severity scores, or probability values are rendered
- Top pane still renders the regime bands (if available) or is also empty

**Pass criteria:**
- Screenshot shows an empty bottom pane (no colored bands, no lines)
- HTTP response for `?asof=<early-date>&full=true` contains `timeline_full: []` (empty array)
- No error message or fallback placeholder is shown (honest empty, not error)

---

### TC-07 — J-98 at-a-glance compact Market Regime figure renders with breakdown

**Type:** browser
**Preconditions:**
- Frontend is at `http://localhost:3835/`
- Current as-of is 2026-06-16 (live date with data)
- Dashboard has fully loaded

**Steps:**
1. Locate the compact "Market Regime" figure at the top of the Dashboard (below the header, above Major-indexes)
2. Observe the displayed label (e.g., "Bull", "Bear", "Risk-Off") and a numeric score (e.g., "0.65")
3. Click the `<details>` disclosure triangle next to the figure to expand component breakdown
4. Verify a breakdown list appears showing named components (e.g., "Momentum: +0.2", "Valuation: +0.15", etc.)
5. Take a screenshot: `screenshot at-a-glance-regime-expanded.png`

**Expected outcome:**
- Compact figure shows regime label and score (not a bare number)
- A clickable disclosure/summary element is available to expand
- Expanded breakdown shows multiple named components with individual scores
- No bare numeric value without explanation is visible

**Pass criteria:**
- Screenshot shows the regime figure with label and score
- Disclosure state can be toggled (expand/collapse)
- At least 2 named components appear in the breakdown (e.g., momentum, valuation, etc.)
- No error or missing data in the breakdown

---

### TC-08 — J-98 at-a-glance Market Phase & Severity figure renders with breakdown

**Type:** browser
**Preconditions:**
- Frontend is at `http://localhost:3835/`
- Current as-of is 2026-06-16 (live date with data)
- Dashboard has fully loaded

**Steps:**
1. Locate the compact "Market Phase & Severity" figure below the Regime figure
2. Observe the displayed label (e.g., "Recovery", "Distribution") and a numeric severity (e.g., "45")
3. Verify a phase-colored band or icon is rendered alongside the figure
4. Click the `<details>` disclosure to expand the component breakdown
5. Verify a breakdown list shows named components (e.g., "Price Momentum: +15", "Volume Accumulation: -5", etc.)
6. Take a screenshot: `screenshot at-a-glance-phase-expanded.png`

**Expected outcome:**
- Compact figure shows phase label, severity score (0–100), and a colored phase band
- Disclosure element is present and toggleable
- Expanded breakdown shows multiple named components
- No bare severity number without explanation

**Pass criteria:**
- Screenshot shows phase label, severity score, and color-coded band
- Disclosure can be toggled (expand/collapse)
- At least 2 named components appear in breakdown
- Severity score is in range 0–100

---

### TC-09 — J-98 More-detail expand button reveals full details section

**Type:** browser
**Preconditions:**
- Frontend is at `http://localhost:3835/`
- Current as-of is 2026-06-16
- Dashboard has fully loaded

**Steps:**
1. Scroll down past the at-a-glance compact figures
2. Locate a collapsed "More detail" section (or `<details>` element with label "More detail" or similar)
3. Click the expand/summary element to open the More-detail section
4. Verify the expanded section shows: breadth figure, Candidate Counts, Top Sectors, Top Themes, and the full MarketPhaseCard
5. Take a screenshot: `screenshot more-detail-expanded.png`

**Expected outcome:**
- More-detail section is initially collapsed
- Clicking expands the section to reveal multiple sub-figures and the full MarketPhaseCard
- All sub-sections render without errors
- The MarketPhaseCard at the bottom shows the same data as the two-pane chart

**Pass criteria:**
- Screenshot shows expanded More-detail section with at least 4 visible sub-elements
- No missing data or error messages in the expanded content
- The full MarketPhaseCard is visible at the bottom of the More-detail section

---

### TC-10 — J-98 as-of change updates both at-a-glance and More-detail figures

**Type:** browser
**Preconditions:**
- Frontend is at `http://localhost:3835/`
- Dashboard is fully loaded with current as-of (2026-06-16)
- Both at-a-glance and More-detail sections are expanded

**Steps:**
1. Take a baseline screenshot of the at-a-glance regime and phase figures: `screenshot before-asof-change.png`
2. Click the as-of date picker/calendar
3. Select a different date (e.g., 2026-06-10)
4. Wait for the page to re-render with the new as-of data
5. Take a second screenshot of the same at-a-glance figures: `screenshot after-asof-change.png`
6. Compare the two images for visual differences in the regime label/score and phase label/severity

**Expected outcome:**
- Regime label/score changes in the at-a-glance figure when as-of changes
- Phase label and severity score change in the at-a-glance figure when as-of changes
- The More-detail section figures (breadth, Candidate Counts, Top Sectors, Top Themes) also update
- The two-pane chart updates to show data for the new as-of

**Pass criteria:**
- `md5sum before-asof-change.png after-asof-change.png` produces distinct hashes
- At least one of the regime label, phase label, or severity score is visually different in the two screenshots
- All dependent figures (chart, More-detail) update when as-of changes
- No error or stale data is shown for the new as-of

---

### TC-11 — J-18 critical check: zero native input[type=date] on Dashboard

**Type:** browser
**Preconditions:**
- Frontend is at `http://localhost:3835/`

**Steps:**
1. Open browser DevTools (Chrome MCP: use `evaluate` action)
2. Run: `document.querySelectorAll('input[type="date"]').length`
3. Record the count
4. Run: `grep -r "input.*type.*date" apps/frontend/app/page.tsx apps/frontend/components/phase-cross-view-*.tsx`

**Expected outcome:**
- Query returns 0 (no native `input[type=date]` elements on the page)
- Grep search finds no `type="date"` or `type="date"` in the relevant component files

**Pass criteria:**
- `querySelectorAll('input[type="date"]').length === 0`
- No native date input elements are present in the DOM
- The as-of selector is a custom component, not a native HTML date input

---

### TC-12 — J-07 critical check: Risk-Off regime shows 0 Actionable stocks

**Type:** browser
**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is at `http://localhost:3835/`
- A date with Risk-Off regime is available in the data (e.g., a historical crisis date or a configured test scenario)

**Steps:**
1. Navigate to the `/stocks` page or a stocks-listing view
2. Use the as-of picker to select a Risk-Off date (verify the Dashboard shows "Risk-Off" label first)
3. Observe the Actionable count in the stocks table or filter
4. Verify the Actionable count is exactly 0
5. Verify Candidate Counts appear in the Dashboard's More-detail section

**Expected outcome:**
- When regime is Risk-Off, zero stocks are marked Actionable
- Other candidate counts (e.g., Candidate, Watch, Screen) may be > 0
- The Actionable count is explicitly shown as 0, not missing or omitted

**Pass criteria:**
- Actionable count in the UI is 0 when regime is Risk-Off
- HTTP request to `/api/...` shows `actionable: 0` in the response
- No backend error or missing data when Risk-Off regime is active

---

### TC-13 — J-06 critical check: at-a-glance figures match served API values

**Type:** api + browser
**Preconditions:**
- Backend is running at `http://localhost:8835`
- Frontend is at `http://localhost:3835/`
- Current as-of is 2026-06-16

**Steps:**
1. Fetch the API response: `curl -s 'http://localhost:8835/api/market-phase?asof=2026-06-16&full=false' > api_response.json`
2. Extract: `jq '.regime_label, .regime_score, .phase_label, .severity_score' api_response.json`
3. On the Frontend, capture the at-a-glance figures visually (screenshot)
4. Manually compare the displayed regime label and score with API values
5. Manually compare the displayed phase label and severity with API values

**Expected outcome:**
- The at-a-glance regime label (top figure) matches the API `regime_label` value
- The regime score (top figure) matches the API `regime_score` value
- The phase label (bottom figure) matches the API `phase_label` value
- The severity score (bottom figure) matches the API `severity_score` value
- No client-side recomputation; values are read from the API response

**Pass criteria:**
- Regime label in UI == API `regime_label`
- Regime score in UI == API `regime_score`
- Phase label in UI == API `phase_label`
- Severity score in UI == API `severity_score`

---

## Summary

**Total test cases:** 13
- **API tests:** 3 (TC-01, TC-02, TC-03)
- **Browser tests:** 10 (TC-04 through TC-13)

**Coverage:**
- Cache-correctness fix (schema-version key): TC-01, TC-02, TC-03
- J-97 bottom pane rendering: TC-04, TC-05, TC-06
- J-98 at-a-glance restructure: TC-07, TC-08, TC-09, TC-10
- Required-still-passing critical checks: TC-11 (J-18), TC-12 (J-07), TC-13 (J-06)
