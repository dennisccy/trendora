# Goal Iteration 44 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Date:** 2026-06-22
**Frontend Present:** yes

## Phase Goal

On the Dashboard, the user sees exactly one market chart (no duplicate Major-indexes card), the phase pane bands span full history at any as-of, and a new severity-velocity line replaces the P(bear) line while the tooltip gains market-regime label + score.

## Test Cases

### TC-01 — Dashboard renders single market chart (J-101a)

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend serving `/api/market-phase` and `/api/regime-history`; database seeded with 2021-2026 history

**Steps:**
1. Navigate to Dashboard (`/`)
2. Wait for all cards to render
3. Inspect the page for card count and titles
4. Search for instances of "Major" or "Index" in visible card titles

**Expected outcome:** Exactly one market-related chart is visible; the standalone `<MajorIndexesCard />` is absent
**Pass criteria:** CSS query `article:has(h2:contains("Major Index"))` or similar standalone card returns ZERO results; exactly ONE market card (the `<PhaseCrossViewCard />`) renders

---

### TC-02 — Phase pane bands span full history at historical as-of (J-101b)

**Type:** browser
**Preconditions:** Frontend running; backend serving; database with 1369-day+ history (seed 2021-2026); phase pane visible on Dashboard

**Steps:**
1. Navigate to Dashboard
2. Open the as-of date picker
3. Select a historical date (e.g., 2022-06-01, ~2 years ago)
4. Wait for the cross-view chart to re-render
5. Observe the phase pane (bottom of the cross-view chart)
6. Capture screenshot of the full phase pane bands

**Expected outcome:** Phase pane bands span the FULL width of the chart from the earliest stored date through the latest; the selected as-of date renders as a vertical marker WITHIN the bands, not truncating them
**Pass criteria:** Phase band visualization width spans from chart start to chart end; marker is a vertical line at the selected date; no bands truncate or vanish at the marker

---

### TC-03 — Phase pane bands honest-empty at early as-of (J-101b edge case)

**Type:** browser
**Preconditions:** Frontend running; backend serving; database with 1369-day history; phase pane visible

**Steps:**
1. Navigate to Dashboard
2. Select an early as-of date where market-phase history has gaps or no computed phases (e.g., 2021-01-01)
3. Wait for the cross-view chart to re-render
4. Observe the phase pane (bottom half)
5. Capture screenshot of the phase pane

**Expected outcome:** Phase pane renders as an empty grid (no colored bands, no fabricated data); the chart area remains clean and undecorated where no historical phases exist
**Pass criteria:** No fake/synthetic colored bands appear in the phase pane at dates with no real phase data; the empty state is visually honest and distinct from a loaded state

---

### TC-04 — Phase pane plots zero-centered severity-velocity line (J-102 chart)

**Type:** browser
**Preconditions:** Frontend running; backend serving `/api/market-phase` with new `severity_velocity` field; phase pane visible

**Steps:**
1. Navigate to Dashboard
2. Wait for the cross-view chart to render
3. Inspect the phase pane (bottom half) for overlay lines
4. Observe line colors, alignment, and centering
5. Verify no line labeled "P(bear)" or similar probability metric is drawn
6. Capture screenshot showing the severity-velocity line

**Expected outcome:** A zero-centered line is drawn on the phase pane overlay scale (labeled or color-coded as severity-velocity); the line crosses the horizontal zero reference; no P(bear) line is plotted (though P(bear) value may exist in the tooltip)
**Pass criteria:** A ZERO-CENTERED line exists in the phase pane; a horizontal `0` reference line is visible; no overlaid line labeled or styled as "P(bear)" or "Probability" is drawn; the line oscillates around zero

---

### TC-05 — Cross-view tooltip shows regime label + score + severity-velocity (J-102 tooltip)

**Type:** browser
**Preconditions:** Frontend running; backend serving `/api/market-phase` and `/api/regime-history`; Dashboard loaded; cross-view chart rendered

**Steps:**
1. Navigate to Dashboard
2. Wait for the cross-view chart to render
3. Hover over a date/point in the phase pane (bottom half)
4. Wait for tooltip to appear (verify Chrome MCP `await_text` for tooltip content)
5. Observe tooltip rows
6. Capture screenshot of the tooltip
7. Verify the regime label (e.g., "Bull", "Bear", "Risk-Off") is present
8. Verify the regime score (a 0-100 numeric value) is present
9. Verify the severity-velocity value (numeric, possibly zero or NA) is present

**Expected outcome:** Tooltip displays at least: date, index %, phase, severity, P(bear), regime label, regime score (0-100), and severity-velocity
**Pass criteria:** Tooltip text includes keywords ["regime", "score", "velocity"] (case-insensitive); regex `/(Bull|Bear|Risk-Off|regime|Regime).*\d+.*velocity|severity.*velocity/i` matches the tooltip text; regime score value is numeric 0-100

---

### TC-06 — Tooltip retains existing rows (phase, severity, P(bear)) (J-102 backward compat)

**Type:** browser
**Preconditions:** Frontend running; Dashboard loaded; cross-view chart rendered; tooltip visible

**Steps:**
1. Navigate to Dashboard
2. Hover over a date in the phase pane (cross-view chart)
3. Wait for tooltip to appear
4. Verify the tooltip includes the following rows: date, index %, phase, severity, P(bear)
5. Capture screenshot

**Expected outcome:** All pre-J-102 tooltip rows are still present in the same order/style as before
**Pass criteria:** Tooltip text contains all five keywords: ["date", "index", "phase", "severity", "P(bear)" or "bear"]; P(bear) row value is numeric 0-100

---

### TC-07 — Unit test: severity-velocity deterministic slope (backend)

**Type:** api
**Preconditions:** Backend running; `apps/backend/tests/test_market_phase.py` contains test fixtures; database seeded with known severity series

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_market_phase.py -k "severity_velocity" -v`
2. Capture stdout/stderr
3. Verify test assertion: `severity_velocity` at date D = slope of severity over the prior `severity_velocity_window` snapshots (e.g., 5 snapshots)
4. Verify sign convention: positive slope = worsening (severity increasing)

**Expected outcome:** Test passes; `severity_velocity` computed deterministically as a linear fit or per-bar difference sum over the config-defined window
**Pass criteria:** Test exit code 0; assertion message explicitly checks slope calculation; test covers at least one known example (e.g., [100, 105, 110, 115, 120] severity → positive velocity)

---

### TC-08 — Unit test: severity-velocity NA at warm-up head (backend)

**Type:** api
**Preconditions:** Backend running; test fixtures; database with short history

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_market_phase.py -k "severity_velocity and warmup" -v`
2. Capture stdout/stderr
3. Verify the first `severity_velocity_window - 1` snapshots return NA for `severity_velocity`

**Expected outcome:** Test passes; the tail of the timeline where there is insufficient historical depth shows `severity_velocity = null` or `"NA"`
**Pass criteria:** Test exit code 0; assertion explicitly checks the first N-1 points have null/NA velocity; the Nth point onwards have numeric values

---

### TC-09 — Unit test: severity-velocity no-lookahead tail-invariance (backend)

**Type:** api
**Preconditions:** Backend running; test fixtures; full 1369-day history seeded

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_market_phase.py -k "severity_velocity and tail" -v`
2. Capture stdout/stderr
3. Verify: when the timeline is truncated at date D (removing all bars dated > D), the `severity_velocity` at any date ≤ D remains byte-identical

**Expected outcome:** Test passes; no future bar influences severity-velocity at dates ≤ D
**Pass criteria:** Test exit code 0; assertion compares the `severity_velocity` field in two scenarios (full timeline vs truncated) and finds no difference for dates ≤ D

---

### TC-10 — Unit test: cache-schema s1→s2 forces recompute (backend)

**Type:** artifact
**Preconditions:** Backend running; database with existing `MarketPhaseCache` rows; `apps/backend/tests/test_market_phase.py` contains a cache validation test

**Steps:**
1. Inspect `apps/backend/app/engine/market_phase.py` line ~797 for `SCHEMA_VERSION`
2. Verify the version is `"s2"` (not `"s1"`)
3. Run: `cd apps/backend && python -m pytest tests/test_market_phase.py -k "cache and schema" -v`
4. Capture stdout/stderr
5. Verify the test SEEDS a fake old-schema cache row (missing `severity_velocity`), then asserts the fetch recomputes and returns the new `severity_velocity` field

**Expected outcome:** Test passes; old-schema cache rows are invalidated and recomputed
**Pass criteria:** Test exit code 0; test file includes a comment explaining the s1→s2 bump; assertion checks that `computed_timeline['severity_velocity']` exists and matches the fresh recompute

---

### TC-11 — Unit test: byte-identity of canonical fields (backend)

**Type:** api
**Preconditions:** Backend running; test fixtures with pre-iter-44 baseline data

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_market_phase.py -k "additive and canonical" -v`
2. Capture stdout/stderr
3. Verify the test compares pre-change and post-change payloads for fields: `phase`, `severity`, `p_bear`, `episodes` (J-89), `retrospective_fence` (J-89), `recovery_signal` (J-90)

**Expected outcome:** Test passes; all canonical fields are byte-identical before and after adding `severity_velocity`
**Pass criteria:** Test exit code 0; assertion uses `==` or md5-sum equality on all pre-existing fields; no regressions in canonical values

---

### TC-12 — Config validation: non-positive severity_velocity_window fails boot (backend)

**Type:** api
**Preconditions:** Backend source code with config validation; `config/config.yaml` editable

**Steps:**
1. Edit `config/config.yaml` to set `market_phase.severity_velocity_window: 0` (or `-1`)
2. Run: `cd apps/backend && python -c "from app.config import load_config; load_config()" 2>&1`
3. Capture stderr
4. Restore `config.yaml` to the valid state (e.g., `5`)

**Expected outcome:** Boot fails loudly with a validation error message mentioning `severity_velocity_window` and the requirement that it be positive
**Pass criteria:** Exit code non-zero; error message contains "severity_velocity_window" and "positive" or "greater than 0"

---

### TC-13 — test_no_magic_numbers stays green (backend)

**Type:** api
**Preconditions:** Backend running; `apps/backend/tests/test_market_phase.py` contains the `test_no_magic_numbers` test

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/test_market_phase.py::test_no_magic_numbers -v`
2. Capture stdout/stderr

**Expected outcome:** Test passes; no literal numeric constant for the window size is found in the code
**Pass criteria:** Test exit code 0; output includes "PASSED" or "1 passed"

---

### TC-14 — All config fixtures include severity_velocity_window (backend artifact)

**Type:** artifact
**Preconditions:** Source code reviewed; `apps/backend/tests/` directory readable

**Steps:**
1. Run: `grep -r "MarketPhaseCfg\|market_phase.*{" apps/backend/tests/ --include="*.py" | head -20`
2. For each inline config dict found, verify it includes the key `severity_velocity_window` with a positive numeric value
3. Run: `grep -r "severity_velocity_window" apps/backend/tests/ apps/backend/scripts/ --include="*.py" | wc -l`
4. Verify at least one result exists

**Expected outcome:** Every inline test config dict that includes a `MarketPhaseCfg` or market_phase block includes the new `severity_velocity_window` key
**Pass criteria:** Grep for `severity_velocity_window` returns results in both `apps/backend/tests/` and potentially `apps/backend/scripts/` (e.g., `build_qa_fixture_db.py`); manual audit shows no `MarketPhaseCfg` without the key

---

### TC-15 — Backend tests pass full suite (gate)

**Type:** api
**Preconditions:** Backend code complete; all source files modified per spec; database seeded; backend running (or auto-started by harness)

**Steps:**
1. Run: `cd apps/backend && python -m pytest tests/ -v 2>&1 | tee test_output.log`
2. Capture the final summary line (e.g., "639 passed in 123s")
3. Check exit code

**Expected outcome:** All tests pass; exit code 0; the summary line shows "0 failed"
**Pass criteria:** Exit code 0; output includes "passed" and "0 failed"; no "FAILED" or "ERROR" lines in the output

---

### TC-16 — Required-still-passing: J-97 cross-view chart synced panes (browser)

**Type:** browser
**Preconditions:** Frontend running; Dashboard visible; cross-view chart rendered

**Steps:**
1. Navigate to Dashboard
2. Observe the cross-view chart (two stacked panes: regime on top, phase on bottom)
3. Verify both panes share the same X-axis (date alignment)
4. Hover over a date on the top pane (regime)
5. Verify the overlay/highlight appears on both panes at the same date
6. Zoom/pan the top pane and verify the bottom pane follows

**Expected outcome:** Both panes are synchronized; shared axis; zoom/pan affects both
**Pass criteria:** A hover or selection at date D highlights both panes; pan/zoom on one pane moves the other identically; no date misalignment between panes

---

### TC-17 — Required-still-passing: J-98 at-a-glance card unchanged (browser)

**Type:** browser
**Preconditions:** Frontend running; Dashboard visible; at-a-glance (compact) card rendered

**Steps:**
1. Navigate to Dashboard
2. Locate the "At a Glance" or similar compact market-phase card
3. Verify the card displays P(bear) value and chart
4. Verify the "Expand" button or similar control exists
5. Click to expand
6. Verify the expanded view still shows P(bear) and the same metrics as before

**Expected outcome:** At-a-glance card displays P(bear) unchanged; expand/collapse works; no P(bear) replacement or removal
**Pass criteria:** Card shows "P(bear)" or similar label; expand button toggles the view; expanded view is readable and unchanged from pre-iter-44

---

### TC-18 — Required-still-passing: Market-Phase card P(bear) unchanged (browser)

**Type:** browser
**Preconditions:** Frontend running; Dashboard visible; Market-Phase card rendered

**Steps:**
1. Navigate to Dashboard
2. Locate the "Market Phase" or similar card
3. Observe the displayed metrics and chart
4. Verify P(bear) is shown (either in a line, a value row, or a label)
5. Compare visually to ensure no removal or replacement since iter-43

**Expected outcome:** Market-Phase card displays P(bear) unchanged
**Pass criteria:** Card includes P(bear) in the same position/style as expected from a pre-change screenshot; no new "severity_velocity" line is drawn on this card (only on the cross-view phase pane)

---

### TC-19 — Required-still-passing: J-06 figures match served API (backend)

**Type:** api
**Preconditions:** Backend running; `/api/market-phase` endpoint live; frontend visible

**Steps:**
1. Fetch: `curl -s http://localhost:8835/api/market-phase | jq '.timeline[0] | keys' | sort`
2. Fetch the same data from the frontend (via Chrome MCP inspect the network tab or request the same endpoint)
3. Compare the keys in both responses
4. Verify all displayed figures on the Dashboard match the API payload exactly (no rounding, no computation)

**Expected outcome:** Dashboard displays figures served by `/api/market-phase` verbatim; no frontend recomputation or rounding
**Pass criteria:** Network inspection shows the frontend reads the exact numeric values from the API; no second computation is evident in the browser console

---

### TC-20 — Required-still-passing: J-18 zero native date inputs (browser)

**Type:** browser
**Preconditions:** Frontend running; Dashboard visible

**Steps:**
1. Navigate to Dashboard (`/`)
2. Open the browser developer console (F12 → Elements/Inspector)
3. Search for all `input[type="date"]` elements on the page
4. Verify the count is zero (no native HTML date picker inputs)
5. Verify the as-of selector (if visible) is a custom component, not a native input

**Expected outcome:** Dashboard `/` has no native HTML `input[type="date"]` elements; the as-of control is a custom dropdown or picker
**Pass criteria:** CSS query `input[type="date"]` returns 0 results; the as-of selector uses a custom UI component (e.g., a dropdown, a date library picker)

---

### TC-21 — Required-still-passing: J-07 Risk-Off gate zeros Actionable (API invariant)

**Type:** api
**Preconditions:** Backend running; `/api/data` endpoint live; a Risk-Off regime date exists in the database

**Steps:**
1. Identify a historical as-of date where the market regime is "Risk-Off" (check `/api/regime-history`)
2. Run: `curl -s "http://localhost:8835/api/data?as_of=<RISK_OFF_DATE>" | jq '.scanner_run.actionable_count'`
3. Verify the response

**Expected outcome:** When the regime is Risk-Off, the `actionable_count` is zero (no stocks are marked Actionable)
**Pass criteria:** Response body includes `"actionable_count": 0` when the as-of regime is Risk-Off

---

## Summary

Total test cases: 21
API tests: 8 (TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-15, TC-19, TC-21)
Browser tests: 10 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-16, TC-17, TC-18, TC-20)
Artifact checks: 3 (TC-14 config keys, TC-10 schema version, TC-15 backend suite)

**Note on test coverage:**
- **J-101a (single chart):** TC-01
- **J-101b (full-history bands, honest-empty edge case):** TC-02, TC-03
- **J-102 (severity-velocity line, enriched tooltip):** TC-04, TC-05, TC-06
- **Anti-goals (no-lookahead, magic-numbers, single-source, cache-schema):** TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14
- **Required-still-passing:** TC-16, TC-17, TC-18, TC-19, TC-20, TC-21
- **Gate (backend suite):** TC-15

All test cases are directly traceable to requirements in the phase spec and the TESTING REQUIREMENTS section of the execution plan.
