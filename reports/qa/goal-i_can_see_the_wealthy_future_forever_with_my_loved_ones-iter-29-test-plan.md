# Goal Iteration 29 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29
**Date:** 2026-06-17
**Frontend Present:** yes

## Phase Goal

Implement a read-only Market Phase & Severity panel on the Dashboard showing the market's discrete phase (Expansion / Pullback / Correction / Bear / Recovery), a 0–100 severity score with named component breakdown, and a deterministic 0–1 filtered P(bear), all derived strictly causally from stored snapshots and index bars dated ≤ the global as-of date.

## Test Cases

### TC-01 — Market Phase Panel Renders on Dashboard

**Type:** browser
**Preconditions:** Backend is running; frontend is running; at least one snapshot exists in the database for a recent trading date

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Verify the Dashboard page loads successfully
3. Scroll down to locate the "Market Phase & Severity" card
4. Verify the card displays beside the existing "Major Indexes & Regime" card

**Expected outcome:** The Market Phase & Severity panel is visible on the Dashboard with phase label, severity score, and P(bear) displayed
**Pass criteria:** The panel renders without JavaScript errors and is positioned after the Major Indexes card

---

### TC-02 — Market Phase Panel Shows Phase Label

**Type:** browser
**Preconditions:** Backend is running; frontend is running; database contains snapshots covering 2024 (risk-on era) and 2022 (bear market)

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Verify the Dashboard with default (latest) as-of date displays a phase label
3. Click on the as-of date picker to select a date in late 2024 (e.g., 2024-12-31)
4. Observe the phase label displayed
5. Select a date in the middle of 2022 (e.g., 2022-07-15, during the bear market)
6. Observe the phase label changes to "Bear"

**Expected outcome:** The phase label reflects the market regime for the selected as-of date; 2024 shows Expansion or Recovery; 2022 shows Bear
**Pass criteria:** Phase label changes correctly when the as-of date is modified; 2022 date displays "Bear" label

---

### TC-03 — Severity Score Renders with Component Breakdown

**Type:** browser
**Preconditions:** Backend is running; frontend is running; database contains historical snapshots

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Verify the Market Phase panel displays a 0–100 severity score
3. Observe the severity score has named components listed (e.g., "Drawdown Depth: X%", "Time Underwater: Y days", etc.)
4. Verify each component contributes a visible value to the total severity

**Expected outcome:** Severity score is displayed as a number 0–100 with each named component and its value visible (not a bare number)
**Pass criteria:** At least 5 named components are listed; each has a numeric value; the breakdown is legible and not truncated

---

### TC-04 — P(bear) Probability Displays with Observation Vector

**Type:** browser
**Preconditions:** Backend is running; frontend is running; database contains 2022 and 2024 snapshots

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Verify the Market Phase panel displays a P(bear) value (0–1 range, shown as percentage or decimal)
3. Observe the observation vector disclosed (e.g., "price_trend: down", "breadth: weak", etc.)
4. Change the as-of date to 2022-07-15
5. Observe P(bear) increases significantly (toward 1)
6. Change the as-of date to 2024-12-31
7. Observe P(bear) decreases significantly (toward 0)

**Expected outcome:** P(bear) value and its observation vector are displayed; 2022 shows high P(bear); 2024 shows low P(bear)
**Pass criteria:** P(bear) is a number between 0 and 1; observation vector is visible; probability reverses between 2022 and 2024

---

### TC-05 — Severity Score Consistent Across Page Reloads

**Type:** browser
**Preconditions:** Backend is running; frontend is running; database contains snapshots for 2022-07-15

**Steps:**
1. Navigate to `http://localhost:3000/?asof=2022-07-15`
2. Record the displayed severity score and phase label
3. Reload the page (Ctrl+R or F5)
4. Verify the severity score and phase label are identical to the pre-reload values

**Expected outcome:** The same as-of date produces byte-identical severity and phase on reload (coherence)
**Pass criteria:** Severity score value matches exactly before and after reload; phase label is identical

---

### TC-06 — Panel Reads Single Global As-Of, Not Local Date State

**Type:** browser
**Preconditions:** Frontend is running; database contains snapshots for multiple dates

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Use the global as-of date picker to change the date to 2022-06-30
3. Verify the Market Phase panel updates to reflect 2022-06-30
4. Scroll through the page; verify no independent date input or date state input exists on the Market Phase panel itself
5. Check the page URL to confirm `?asof=2022-06-30` is present

**Expected outcome:** The Market Phase panel responds to the global as-of date control; no new independent date selector exists on the panel
**Pass criteria:** URL contains `?asof=` when historical; Market Phase panel has no new date input; changing global as-of updates the panel

---

### TC-07 — Insufficient History Window Returns NA, Not Fabricated Data

**Type:** browser
**Preconditions:** Backend is running; frontend is running; database contains snapshots starting from 2021-01-04

**Steps:**
1. Navigate to `http://localhost:3000/`
2. Use the as-of date picker to select a very early date in 2021 (e.g., 2021-01-04)
3. Observe the Market Phase panel response (should show NA, "Insufficient history", or a similar explicit empty state)
4. Verify no fabricated phase/severity/probability is shown

**Expected outcome:** Early dates with insufficient historical bars explicitly show NA or a partial state, never a synthesized figure
**Pass criteria:** Panel displays an explicit "Insufficient history" message or empty state; no invented severity or phase is displayed

---

### TC-08 — Regime Label on Panel Matches Dashboard Regime Card

**Type:** browser
**Preconditions:** Backend is running; frontend is running; database contains snapshots for 2024-12-31

**Steps:**
1. Navigate to `http://localhost:3000/?asof=2024-12-31`
2. Record the regime label shown on the existing "Major Indexes & Regime" card
3. Scroll down to the Market Phase panel
4. Verify the regime information displayed in the Market Phase panel (if shown) is consistent with the regime card above

**Expected outcome:** Regime label/score on the Market Phase panel matches the existing Dashboard regime card (J-06 coherence)
**Pass criteria:** Both cards display the same regime label and score for the selected as-of date; no contradictions

---

### TC-09 — Major Indexes Card Remains Unchanged

**Type:** browser
**Preconditions:** Frontend is running; database contains snapshots for 2024-12-31

**Steps:**
1. Navigate to `http://localhost:3000/?asof=2024-12-31`
2. Verify the "Major Indexes & Regime" card displays all expected index charts
3. Verify the card layout, styling, and content are present and unaltered
4. Verify no new controls or changes were introduced to the existing card

**Expected outcome:** The Major Indexes & Regime card is unchanged from previous iterations (J-49 requirement)
**Pass criteria:** Index charts render correctly; no visual regressions; existing functionality unaffected

---

### TC-10 — API Endpoint Returns Correct Response Structure

**Type:** api
**Preconditions:** Backend is running on `http://localhost:8835`; database contains snapshots for 2024-12-31

**Steps:**
1. Run the following curl command:
   ```bash
   curl -s "http://localhost:8835/api/market-phase?as_of=2024-12-31" -H "Accept: application/json"
   ```
2. Capture the full HTTP response (status code and body)
3. Verify the response is valid JSON
4. Verify the response contains keys: `phase`, `severity`, `components`, `filtered_pbear`, `observation_vector`

**Expected outcome:** HTTP 200 with a JSON payload containing phase label, severity score, named components, and filtered P(bear)
**Pass criteria:** Status code is 200; response is valid JSON; all required keys are present; severity is 0–100; P(bear) is 0–1

---

### TC-11 — API Cache Invalidates on Dataset Version Change

**Type:** api
**Preconditions:** Backend is running; database is populated with initial snapshots

**Steps:**
1. Run curl to fetch `GET /api/market-phase?as_of=2024-12-31` and record the response
2. Trigger a dataset change (e.g., fetch new bars or add a snapshot via the Data Manager)
3. Run the same curl command again
4. Compare the two responses; they should be identical if the as-of date and data are unchanged, but the cache should have refreshed

**Expected outcome:** The endpoint caches results per `dataset_version`; after a dataset change the cache refreshes and serves fresh values
**Pass criteria:** The cache key includes `dataset_version`; responses are byte-identical before and after refresh if data is unchanged

---

### TC-12 — Invalid As-Of Date Degrades Like Existing Endpoints

**Type:** api
**Preconditions:** Backend is running on `http://localhost:8835`

**Steps:**
1. Run curl with an invalid as-of date (e.g., `?as_of=9999-12-31`):
   ```bash
   curl -s "http://localhost:8835/api/market-phase?as_of=9999-12-31"
   ```
2. Capture the HTTP response
3. Run curl with a malformed date (e.g., `?as_of=invalid`):
   ```bash
   curl -s "http://localhost:8835/api/market-phase?as_of=invalid"
   ```
4. Capture the HTTP response

**Expected outcome:** Invalid/unknown dates fall back to the latest date (graceful degradation, like other read endpoints); malformed dates return 400 or similar
**Pass criteria:** Unknown date uses latest; malformed date returns a client error (400–499); no 500 error; response is consistent with existing endpoint behavior

---

### TC-13 — Severity Weights Sum to ~1.0 (Config Validation)

**Type:** artifact
**Preconditions:** Backend code has been reviewed and config loaded successfully

**Steps:**
1. Read the config file (e.g., `apps/backend/config.yaml`)
2. Locate the `market_phase:` section
3. Extract the `weights:` subsection containing weights for: drawdown_depth, time_underwater, regime_score, breadth_below_200dma, vix_gate (if separate)
4. Sum all weight values
5. Verify the sum is approximately 1.0 (within 0.01)

**Expected outcome:** All severity component weights in the config sum to ~1.0
**Pass criteria:** Sum of weights is ≥0.99 and ≤1.01 (allowing for floating-point rounding)

---

### TC-14 — No Magic Numbers in Market Phase Module

**Type:** artifact
**Preconditions:** Backend code is available; development is complete

**Steps:**
1. Read the file `apps/backend/app/engine/market_phase.py`
2. Scan for numeric literals (e.g., `0.5`, `100`, `20`, `0.0`) used as thresholds or weights
3. Verify all thresholds and weights are referenced from the config (e.g., `config.market_phase.drawdown_threshold`)
4. Verify `apps/backend/tests/test_no_magic_numbers.py` includes `app/engine/market_phase.py` in the `CALC_FILES` list

**Expected outcome:** No threshold or weight literals appear in the market_phase.py code; all are config-driven
**Pass criteria:** Zero inline numeric thresholds found; all config references are in place; module is listed in test_no_magic_numbers.py

---

### TC-15 — No Second Date State in Frontend Panel

**Type:** artifact
**Preconditions:** Frontend code for Market Phase card is available

**Steps:**
1. Read the file `apps/frontend/components/market-phase-card.tsx`
2. Search for any `useState` hook related to date
3. Search for any `window.` or `document.` keyboard event listeners (e.g., keydown for date arrows)
4. Verify the component only reads from `useAsOf()` provider

**Expected outcome:** No new date state is introduced; the panel reads the single global as-of only
**Pass criteria:** Zero new date `useState` calls; zero date-related keydown listeners; only `useAsOf()` is called for date

---

### TC-16 — Regime Input Not Recomputed, Read Verbatim from ScannerRun

**Type:** artifact
**Preconditions:** Backend derivation code is available; database contains snapshots with regime scores

**Steps:**
1. Read the file `apps/backend/app/engine/market_phase.py`
2. Verify there are NO imports from `app.engine.regime`
3. Verify the function reads regime values (label, score) from the `ScannerRun` table via stored rows
4. Confirm regime is read, never recomputed via the regime derivation module

**Expected outcome:** Regime values are retrieved from persisted `ScannerRun` rows, not derived fresh
**Pass criteria:** Zero calls to regime computation functions; regime sourced from `ScannerRun` query results only

---

### TC-17 — Risk-Off Gate Unaffected — Zero Actionable in Risk-Off Date

**Type:** browser
**Preconditions:** Backend is running; database contains a Risk-Off snapshot (e.g., from 2022-03-15)

**Steps:**
1. Navigate to `http://localhost:3000/?asof=2022-03-15` (a known Risk-Off regime date)
2. Open the `/stocks` leaderboard
3. Count the number of stocks marked "Actionable" (filter by setup status if available)
4. Verify the count is zero

**Expected outcome:** A Risk-Off regime date shows zero stocks marked Actionable (the gate remains intact)
**Pass criteria:** No "Actionable" stocks appear on the leaderboard for a Risk-Off as-of date

---

### TC-18 — 2022 Bear Window Reproduces High Severity and High P(bear)

**Type:** api
**Preconditions:** Backend is running; database contains 2022 snapshots including the July 2022 bear market low

**Steps:**
1. Run curl to fetch the 2022-07-15 market phase:
   ```bash
   curl -s "http://localhost:8835/api/market-phase?as_of=2022-07-15"
   ```
2. Capture the response and verify the `phase` value
3. Verify the `severity` score is high (e.g., ≥70)
4. Verify the `filtered_pbear` value is high (e.g., ≥0.7)
5. Run curl for a 2024 date and verify severity and P(bear) are low

**Expected outcome:** The 2022 bear window shows phase=Bear, high severity (reproducing the −24.5% SPY peak-to-trough), and high P(bear); 2024 shows low severity and low P(bear)
**Pass criteria:** 2022-07-15 phase is "Bear"; severity ≥70; filtered_pbear ≥0.7; 2024 date shows inverse values

---

### TC-19 — Filtered P(bear) is Function of Observations ≤ D Only

**Type:** api
**Preconditions:** Backend is running; database contains continuous daily bars from 2024-01-01 to 2024-12-31

**Steps:**
1. Fetch market phase for 2024-06-30 and record the filtered_pbear value
2. Fetch market phase for 2024-06-30 again (no data change between calls)
3. Verify the filtered_pbear value is identical (determinism)
4. Manually verify via code review that the Hamilton filter implementation uses only observations dated ≤ D (no forward-looking data)

**Expected outcome:** Filtered P(bear) at D is deterministic and uses only data ≤ D
**Pass criteria:** Two identical requests return byte-identical filtered_pbear; code review confirms no forward data is used

---

### TC-20 — No New Snapshot Column, No Rebuild Triggered

**Type:** artifact
**Preconditions:** Backend code and database schema are available; dev phase is complete

**Steps:**
1. Inspect the `ScannerRun` model in `apps/backend/app/models.py`
2. Verify no new columns have been added to the `ScannerRun` table
3. Inspect the `ScannerResult` model and verify no new columns
4. Verify no new columns have been added to `forward_returns`
5. Verify the Market Phase endpoint does NOT trigger a `kind:"rebuild"` on the backend

**Expected outcome:** No new snapshot columns; no rebuild logic triggered by the market phase feature
**Pass criteria:** Zero new columns on any snapshot table; zero rebuild calls in the market_phase derivation code

---

## Summary

**Total test cases:** 20
**Browser tests:** 10
**API tests:** 6
**Artifact checks:** 4

**Coverage:**
- **Frontend:** Dashboard panel rendering, phase/severity/P(bear) display, as-of integration, single global date control
- **Backend:** API endpoint correctness, caching and dataset_version, invalid as-of handling, 2022 bear reproduction, filter determinism
- **Config & Code Quality:** No magic numbers, weights validation, regime non-recomputation, risk-off gate preservation
- **Anti-goal guardrails:** Strictly causal (≤D data), no lookahead, no snapshot rebuild, no second date state, no fabricated data
