# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-17
**Frontend Present:** yes

## Phase Goal

Deliver J-89 (market-phase history timeline with fenced retrospective view) and J-90 (causal recovery-turn signal + edge study) to provide users with a dated view of market phases, downtrend episodes, and recovery-turn forward-return edge studies.

## Test Cases

### TC-01 — Market-Phase Timeline Series Renders on Dashboard

**Type:** browser
**Preconditions:** Backend API `/api/market-phase` serves the timeline series (per-date phase + filtered P(bear)); frontend is running; user is on Dashboard (`/`).

**Steps:**
1. Navigate to Dashboard (`/`)
2. Scroll to the Market-Phase panel / major-indexes card (below the fold ~1060px)
3. Verify the timeline overlay is visible as a step-function band behind the as-of marker
4. Verify the step function displays per-snapshot-date phase and filtered P(bear) values

**Expected outcome:** Timeline rendered correctly showing the historical phase states.
**Pass criteria:** Step function is visible on the card; each step visually corresponds to a snapshot date in the dataset.

---

### TC-02 — Causal Downtrend Episodes Display with Trigger Date and Severity

**Type:** browser
**Preconditions:** Dashboard loaded; timeline visible; the 2022 bear episode is in the data (first-trigger date + severity-at-trigger + open/closed state).

**Steps:**
1. On the Dashboard Market-Phase card, locate the downtrend-episode list below the timeline
2. Verify that each episode shows: first-trigger date, severity-at-trigger, and open/closed status at the resolved as-of
3. Locate the 2022 bear episode (should be a single causal episode)
4. Confirm the 2022 episode triggers at a specific date (not multiple entries)

**Expected outcome:** Episodes are listed with all required fields visible and accurate.
**Pass criteria:** The 2022 bear appears as exactly ONE dated episode with severity and status shown; no duplicate episodes.

---

### TC-03 — Fenced Retrospective Sub-View Labeled Analysis-Only

**Type:** browser
**Preconditions:** Dashboard loaded; timeline visible; the fenced retrospective field/endpoint is served by the backend.

**Steps:**
1. On the Dashboard Market-Phase card, locate the "Retrospective (full-sample / analysis-only)" toggle/sub-view control
2. Toggle the retrospective sub-view ON
3. Verify the label explicitly states "analysis-only" or similar disclaimer
4. Verify the smoothed P(bear) series and peak-to-trough true-bear dating are displayed separately from the causal timeline
5. Toggle the retrospective sub-view OFF
6. Confirm the causal timeline reappears without the smoothed data

**Expected outcome:** Retrospective sub-view is clearly fenced with visible analysis-only labeling.
**Pass criteria:** The sub-view displays when toggled on; the label is visible and contains "analysis-only" or equivalent; toggling off hides it cleanly.

---

### TC-04 — Clamping at Resolved As-Of (Historical Date)

**Type:** browser
**Preconditions:** A historical as-of date is available in the dataset (e.g., 2022-12-31); backend resolves the as-of correctly.

**Steps:**
1. Navigate to Dashboard with `?asof=2022-12-31` (historical date)
2. Scroll to the Market-Phase card and view the timeline
3. Verify that the causal timeline renders only dates ≤ 2022-12-31
4. Verify the retrospective sub-view, when toggled on, is the ONLY future-aware surface (shows full history)
5. Confirm the as-of marker on the chart is positioned at 2022-12-31

**Expected outcome:** Causal timeline clamps to as-of date; retrospective is the only forward-looking view.
**Pass criteria:** No dates > as-of appear on the causal timeline; retrospective shows full history when toggled on; as-of marker aligns with the clamped date.

---

### TC-05 — Early As-Of Yields Empty Timeline

**Type:** browser
**Preconditions:** An early historical as-of date exists (e.g., 2021-01-05, before substantial market history).

**Steps:**
1. Navigate to Dashboard with `?asof=2021-01-05`
2. Scroll to the Market-Phase card
3. Verify the timeline is empty or shows minimal history
4. Verify an empty/honest state message is displayed (not a fabricated timeline)

**Expected outcome:** Empty or minimal timeline for early as-of date.
**Pass criteria:** Timeline is empty or truthfully minimal; no fabricated episodes or probabilities appear.

---

### TC-06 — Recovery-Turn Signal Displays on Market-Phase Panel

**Type:** browser
**Preconditions:** Backend serves the causal recovery-turn signal (`is_recovery_turn` + `reason`) on `GET /api/market-phase`; an as-of date exists where a recovery turn is detected.

**Steps:**
1. Navigate to Dashboard at an as-of date where a recovery/turn is present
2. Scroll to the Market-Phase panel
3. Locate the recovery-turn signal line (should show boolean + triggering reason)
4. Verify the reason is descriptive (e.g., "phase left Bear/Correction" or "P(bear) crossed below threshold")

**Expected outcome:** Recovery-turn signal is visible with an explainable reason.
**Pass criteria:** Signal is displayed as a badge/line with a readable reason; it is NOT a bare flag or icon without explanation.

---

### TC-07 — Recovery-Turn Edge Lab Renders on Research Page

**Type:** browser
**Preconditions:** Frontend is running; backend serves `GET /api/research/recovery-turn-edge`; user navigates to `/research`.

**Steps:**
1. Navigate to `/research`
2. Locate the "Recovery-Turn Edge" lab section (should be appended to existing lab stack)
3. Verify the section displays a table with columns: horizon, mean, median, %-positive, expectancy, downside-risk-adjusted, aggregate max-drawdown
4. Verify the section has the label "Note: Forward returns contain survivorship bias"

**Expected outcome:** Recovery-Turn Edge lab section is visible with all required columns and the survivorship-bias label.
**Pass criteria:** Lab section is present; all return metrics are rendered; survivorship-bias label is visible.

---

### TC-08 — Recovery-Turn Edge Lab Horizon Toggle Switches Views

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible; backend serves multiple horizons (from config).

**Steps:**
1. In the Recovery-Turn Edge lab, locate the horizon selector (dropdown or toggle)
2. Select different horizons (e.g., 1d, 5d, 10d, 20d, 60d)
3. Verify the table updates with the selected horizon's data
4. Confirm the values change appropriately per horizon

**Expected outcome:** Horizon toggle switches the displayed data.
**Pass criteria:** Horizon selector is functional; table values re-point consistently when horizon is changed.

---

### TC-09 — Recovery-Turn Edge Lab Episodes ⇄ Pooled Toggle

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible; backend computes both Episodes and Pooled views.

**Steps:**
1. In the Recovery-Turn Edge lab, locate the Episodes ⇄ Pooled toggle
2. Switch between Episodes and Pooled modes
3. Verify the table updates (Episodes mode shows per-episode rows; Pooled mode shows aggregated rows)
4. Confirm the `n` (sample count) is displayed for each row

**Expected outcome:** View toggle switches between Episodes and Pooled modes.
**Pass criteria:** Toggle is functional; table rows change between per-episode and aggregated; sample counts are visible in both modes.

---

### TC-10 — Recovery-Turn Edge Lab As-Of ⇄ All-History Toggle

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible; backend serves both As-of and All-history filtered views.

**Steps:**
1. Navigate to Dashboard with a historical as-of date (e.g., `?asof=2023-06-30`)
2. Go to `/research` and find the Recovery-Turn Edge lab
3. Locate the As-of ⇄ All-history toggle
4. Switch between modes
5. Verify the table updates (As-of mode filters recovery turns ≤ as-of date; All-history mode includes all)

**Expected outcome:** As-of toggle switches between filtered and full views.
**Pass criteria:** Toggle is functional; row counts or dates change when switching; filtering is correct per mode.

---

### TC-11 — Recovery-Turn Edge Table Columns are Sortable

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible; table has multiple rows.

**Steps:**
1. In the Recovery-Turn Edge table, click on column headers (mean, median, %-positive, etc.)
2. Verify the table sorts by the clicked column (ascending/descending on repeated clicks)
3. Test at least two columns (e.g., mean return, sample count)

**Expected outcome:** Columns are client-side sortable.
**Pass criteria:** Clicking headers sorts the table; sort direction toggles on repeated clicks.

---

### TC-12 — N= Chip Opens Count-Coherent Samples Drill-Down

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible; table has rows with `N=` chips; backend samples endpoint is available.

**Steps:**
1. In the Recovery-Turn Edge table, locate an `N=` chip (e.g., "N=42")
2. Click the chip
3. Verify a new tab opens with the `/research/samples` page
4. On the samples page, verify the drill-down displays the cohort matching the original `n` value
5. Verify the `total` count on the samples page EQUALS the published `n` in the lab table (verify for at least one row in Episodes mode and one in Pooled mode)

**Expected outcome:** `N=` chip opens samples drill-down in a new tab with count-coherent data.
**Pass criteria:** New tab opens; samples total matches the lab's `n` value; drill-down shows recovery-turn cohort.

---

### TC-13 — Count-Coherence: Episodes Mode N= Total

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible in Episodes mode; multiple episodes are available.

**Steps:**
1. In the Recovery-Turn Edge lab (Episodes mode), note the `n` value for at least one row
2. Click its `N=` chip to open the samples drill-down
3. On the `/research/samples` page, verify the `total` count shown
4. Confirm `total == published n` from step 1

**Expected outcome:** Samples drill-down total matches the lab's `n`.
**Pass criteria:** `total` field on samples page equals the `n` value in the lab.

---

### TC-14 — Count-Coherence: Pooled Mode N= Total

**Type:** browser
**Preconditions:** Recovery-Turn Edge lab is visible in Pooled mode.

**Steps:**
1. Switch the Recovery-Turn Edge lab to Pooled mode
2. Note the `n` value for the Pooled aggregated row
3. Click the `N=` chip to open the samples drill-down
4. Verify the samples page `total` equals the Pooled `n`

**Expected outcome:** Samples drill-down total matches the Pooled `n`.
**Pass criteria:** `total` field equals the Pooled `n` value.

---

### TC-15 — Low-Sample Edge Cohorts Show NA + n

**Type:** browser
**Preconditions:** A horizon/view/as-of combination exists with fewer samples than the config minimum.

**Steps:**
1. In the Recovery-Turn Edge lab, look for a row where the return metrics show "NA" or similar
2. Verify the row's `n` value is visible (showing actual sample count even if below minimum)
3. Verify no fabricated return value appears (no 0% or interpolated value)

**Expected outcome:** Low-sample cohorts display NA + sample count.
**Pass criteria:** Metrics are NA; sample count `n` is shown; no fabricated returns.

---

### TC-16 — Invalid As-Of Parameter Returns 4xx/503

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Call `curl -s "http://localhost:8000/api/market-phase?as_of=invalid-date" | jq`
2. Verify the response status code is 4xx or 503
3. Call `curl -s "http://localhost:8000/api/market-phase?as_of=1900-01-01" | jq` (out-of-range date)
4. Verify the response status code is 400 or 422

**Expected outcome:** Invalid as_of returns error status.
**Pass criteria:** Status code is 4xx or 503; no fabricated date or default substitution occurs.

---

### TC-17 — Invalid View/Horizon on Recovery-Turn Edge Returns 4xx

**Type:** api
**Preconditions:** Backend is running; `/api/research/recovery-turn-edge` endpoint is available.

**Steps:**
1. Call `curl -s "http://localhost:8000/api/research/recovery-turn-edge?view=invalid" | jq`
2. Verify the response status code is 4xx
3. Call `curl -s "http://localhost:8000/api/research/recovery-turn-edge?horizon=999d" | jq`
4. Verify the response status code is 4xx

**Expected outcome:** Invalid view/horizon parameters return error status.
**Pass criteria:** Status code is 4xx; clear error message is provided.

---

### TC-18 — Timeline Series Byte-Identity vs _filtered_bear_path

**Type:** artifact
**Preconditions:** Backend tests pass; test file `apps/backend/tests/test_market_phase.py` exists.

**Steps:**
1. Inspect `test_market_phase.py` for a test named `test_timeline_filtered_byte_identity` or similar
2. Verify the test asserts that the timeline series per-date filtered P(bear) equals `_filtered_bear_path` at each date
3. Run the test: `pytest apps/backend/tests/test_market_phase.py::test_timeline_filtered_byte_identity -v`

**Expected outcome:** Timeline filtered P(bear) is byte-identical to _filtered_bear_path.
**Pass criteria:** Test passes; no byte difference between the two sources.

---

### TC-19 — No-Lookahead Tail-Invariance for Timeline/Episodes/Signal

**Type:** artifact
**Preconditions:** Backend tests pass; test file `apps/backend/tests/test_market_phase.py` exists.

**Steps:**
1. Inspect `test_market_phase.py` for a test named `test_no_lookahead_tail_invariance` or similar
2. Verify the test removes bars/runs dated > D and asserts that timeline / episode / signal values at dates ≤ D remain unchanged
3. Run the test: `pytest apps/backend/tests/test_market_phase.py::test_no_lookahead_tail_invariance -v`

**Expected outcome:** Removing future data does not change past values.
**Pass criteria:** Test passes; values at dates ≤ D are bit-identical after tail removal.

---

### TC-20 — FENCE: Smoothed Probability Not Read by As-Of Path

**Type:** artifact
**Preconditions:** Backend tests pass; test file `apps/backend/tests/test_market_phase.py` exists.

**Steps:**
1. Inspect `test_market_phase.py` for a test named `test_smoothed_not_in_asof_path` or similar
2. Verify the test asserts that `compute_market_phase` (and the episode/signal derivations) do NOT read the retrospective smoothed P(bear)
3. Run the test: `pytest apps/backend/tests/test_market_phase.py::test_smoothed_not_in_asof_path -v`

**Expected outcome:** Smoothed data is not consumed by live computations.
**Pass criteria:** Test passes; code inspection confirms no data-flow from retrospective field to as-of values.

---

### TC-21 — Config Validation: New Market-Phase Keys

**Type:** artifact
**Preconditions:** Backend is running; `apps/backend/config.yaml` includes the new market_phase keys.

**Steps:**
1. Verify `config.yaml` contains keys: `downtrend_pbear_threshold`, `recovery_signal_pbear_exit`, recovery trailing-MA window, Bry-Boschan min-phase-length, Bry-Boschan drawdown-amplitude
2. Inspect `apps/backend/app/config.py` for the `MarketPhaseCfg` class
3. Verify the new keys are typed and validated (e.g., positive floats, in-range)
4. Test with a malformed value (e.g., negative `downtrend_pbear_threshold`) by temporarily modifying `config.yaml`
5. Run the backend: `uvicorn apps/backend/app/main.py:app --reload` and check for a validation error at startup

**Expected outcome:** Config keys are validated and malformed values are rejected.
**Pass criteria:** Valid config loads successfully; invalid config raises a validation error at startup.

---

### TC-22 — Config Keys in All Test Fixtures

**Type:** artifact
**Preconditions:** Backend tests pass; test files in `apps/backend/tests/` exist.

**Steps:**
1. Run `grep -r "downtrend_pbear_threshold" apps/backend/tests/` to find all inline config dicts
2. Verify that EVERY inline `config` dict in test files includes the new `market_phase` keys
3. Specifically check: `test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py`
4. Run a sample test from each module: `pytest apps/backend/tests/test_config.py -v`

**Expected outcome:** All test config dicts include the new keys.
**Pass criteria:** No test fails due to missing config keys; grep finds the keys in all expected test files.

---

### TC-23 — No Magic Numbers in Market-Phase Module

**Type:** artifact
**Preconditions:** Backend tests pass; `test_no_magic_numbers.py` exists.

**Steps:**
1. Run the full magic-numbers guard: `pytest apps/backend/tests/test_no_magic_numbers.py -v`
2. Verify that `market_phase.py` is in the `CALC_FILES` list
3. Verify that Bry-Boschan cutoffs and recovery thresholds are sourced from config, not literals

**Expected outcome:** No magic numbers appear in calculated modules.
**Pass criteria:** Test passes; all thresholds are config-sourced.

---

### TC-24 — No New Database Table Created

**Type:** artifact
**Preconditions:** Backend tests pass; `test_db.py` exists.

**Steps:**
1. Run `pytest apps/backend/tests/test_db.py::test_create_all_produces_expected_tables -v`
2. Verify the test passes (no unexpected new tables)

**Expected outcome:** No new table is required; existing caches are reused.
**Pass criteria:** Test passes; the expected-tables set is unchanged.

---

### TC-25 — Byte-Equality Guards Updated for Additive Fields

**Type:** artifact
**Preconditions:** Backend tests pass; `test_api_engine.py` exists.

**Steps:**
1. Inspect `test_api_engine.py` for byte-equality guards on `GET /api/market-phase`
2. Verify that any guard comparing the full response has been updated to strip the additive timeline/episode/recovery-turn fields
3. Verify that the canonical phase/severity/filtered-p_bear equality is preserved in a separate sub-assertion
4. Run the test: `pytest apps/backend/tests/test_api_engine.py -v`

**Expected outcome:** Byte-equality guards are reconciled for additive fields.
**Pass criteria:** Test passes; canonical values match; additive fields are asserted separately.

---

### TC-26 — No New Date useState in Frontend (J-18 Compliance)

**Type:** browser
**Preconditions:** Frontend source code is available; new Dashboard timeline component is present.

**Steps:**
1. Inspect `apps/frontend/components/market-phase-card.tsx` for `useState` declarations
2. Verify that NO new date-related `useState` is introduced (e.g., no `useState("as_of")` or date-picker state)
3. Verify the component reads the resolved as-of ONLY via `useAsOf()` hook
4. Grep the source for `window.addEventListener`, `document.addEventListener`, and `keydown` listeners
5. Verify NO new listeners are added for date/as-of control

**Expected outcome:** Exactly one date selector (the global as-of) is used.
**Pass criteria:** No new date useState; no new event listeners; component uses only `useAsOf()` for the as-of date.

---

### TC-27 — Frontend TypeScript Compilation

**Type:** artifact
**Preconditions:** Frontend source code is complete; TypeScript is configured.

**Steps:**
1. Run `cd apps/frontend && npx tsc --noEmit`
2. Verify no TypeScript errors are reported

**Expected outcome:** Frontend compiles without type errors.
**Pass criteria:** Command exits with status 0; no errors printed.

---

### TC-28 — J-87/J-88 Panel Values Unchanged

**Type:** browser
**Preconditions:** Dashboard is loaded; J-87/J-88 phase/severity/filtered-P(bear) values are displayed.

**Steps:**
1. Navigate to Dashboard
2. On the Market-Phase panel, note the current phase, severity, and filtered P(bear) values
3. Compare these to a snapshot from a previous test run or a known reference
4. Verify they match exactly (no recomputation)

**Expected outcome:** Panel values are unchanged from J-87/J-88.
**Pass criteria:** Phase, severity, and P(bear) match the expected values; no drift.

---

### TC-29 — Risk-Off Gate Still Zero Actionable (J-07)

**Type:** browser
**Preconditions:** Dashboard is loaded with an as-of where the market phase is Risk-Off.

**Steps:**
1. Navigate to Dashboard with `?asof=<risk-off-date>`
2. Verify the Actionable-stocks count is zero
3. Verify watchlist-only mode is displayed

**Expected outcome:** Risk-Off gate is unchanged; zero actionable stocks.
**Pass criteria:** Actionable count is 0; watchlist-only is indicated.

---

### TC-30 — Recovery-Turn Edge Study Samples Kind Wired

**Type:** api
**Preconditions:** Backend is running; `/api/research/samples` endpoint supports the new `kind=recovery-turn`.

**Steps:**
1. Call `curl -s "http://localhost:8000/api/research/samples?kind=recovery-turn" | jq .data`
2. Verify a successful response (200) with sample records
3. Verify each record includes the recovery-turn cohort indicator

**Expected outcome:** Samples endpoint accepts the new `kind=recovery-turn`.
**Pass criteria:** Status 200; response contains recovery-turn samples with complete fields.

---

## Summary

**Total test cases:** 30
**API tests:** 3 (TC-16, TC-17, TC-30)
**Browser tests:** 17 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-26, TC-28, TC-29)
**Artifact checks:** 10 (TC-18, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-25, TC-27, TC-30)
