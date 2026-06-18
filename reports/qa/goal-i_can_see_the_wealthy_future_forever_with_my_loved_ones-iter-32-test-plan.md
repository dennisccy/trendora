# Iter-32 Functional Test Plan: Downtrend-Conditioned Opportunity Study + Optional FRED Macro Feed

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Frontend Present:** yes

## Phase Goal

Enable the user to condition the existing forward-return evidence on the causal downtrend state (phase / severity band / P(bear) band) through three side-by-side angles (held-up-best / weakness-evidence / recovery-turn) on `/research` (J-91), and optionally ingest a real, publication-lag-aligned FRED macro feed wired config-default-OFF into the severity/regime/study layer so price-only figures stay byte-identical until macro is enabled (J-92).

---

## Test Cases

### TC-01 — Downtrend Opportunity study endpoint returns three angles

**Type:** api
**Preconditions:** Backend is running with the committed seed data loaded; the `market_phase` and `event_study_observation_set` are computed and cached.

**Steps:**
1. Call `GET /api/research/downtrend-opportunity?horizon=5&view=episodes&as_of=all`
2. Verify the response status code is 200
3. Inspect the response JSON structure

**Expected outcome:** The endpoint returns a JSON object with three angle keys: `held_up_best`, `weakness_evidence`, and `recovery_turn_edge`, each containing an array of ranked row objects with per-horizon stats (n, mean, median, hit_rate, expectancy, downside_risk_adjusted, max_drawdown).

**Pass criteria:** Response status is 200; JSON contains all three angles; each angle's rows include the required stat fields; rows are ordered by downtrend strength (phase/severity-band/P(bear)-band).

---

### TC-02 — Downtrend Opportunity endpoint with invalid horizon returns 4xx

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Call `GET /api/research/downtrend-opportunity?horizon=999&view=episodes&as_of=all`
2. Verify the response status code

**Expected outcome:** The endpoint rejects the invalid horizon with a 4xx error.

**Pass criteria:** Response status is 4xx (e.g., 400 or 422); error message indicates invalid horizon.

---

### TC-03 — Downtrend Opportunity count-coherence: Episodes vs Pooled

**Type:** api
**Preconditions:** Backend is running; seed data is loaded.

**Steps:**
1. Call `GET /api/research/downtrend-opportunity?horizon=5&view=episodes&as_of=all`
2. Record the `n` value from the first row of `held_up_best` angle
3. Call `GET /api/research/downtrend-opportunity?horizon=5&view=pooled&as_of=all` (same phase/severity/P(bear) band)
4. Verify the drill-down total matches

**Expected outcome:** When drilling down via the `N=` chip into `/api/research/samples?kind=downtrend_opportunity&...`, the total sample count equals the published row `n` in BOTH Episodes and Pooled views.

**Pass criteria:** Drill-down sample count == published row n for the same phase/severity-band; no 4xx errors on valid drill-down combinations.

---

### TC-04 — Downtrend Opportunity As-of vs All-history filter

**Type:** api
**Preconditions:** Backend is running; an as-of date is selected (e.g., 2024-01-15).

**Steps:**
1. Call `GET /api/research/downtrend-opportunity?horizon=5&view=episodes&as_of=2024-01-15`
2. Call `GET /api/research/downtrend-opportunity?horizon=5&view=episodes&as_of=all`
3. Compare the two responses

**Expected outcome:** The as-of-scoped response filters observations to dates ≤ 2024-01-15 only; all-history includes observations from the entire seed window. The row structure and angle logic remain identical; only the observation set changes.

**Pass criteria:** As-of response contains only observations dated ≤ the selected date; all-history response includes full seed range; both return 200.

---

### TC-05 — Downtrend Opportunity with low sample cohort shows NA + count

**Type:** api
**Preconditions:** Backend is running; a conditioned cohort (phase/severity-band/P(bear)-band combination) has fewer than `config.walk_forward.min_sample` observations.

**Steps:**
1. Call `GET /api/research/downtrend-opportunity?horizon=5&view=episodes&as_of=all&phase=bull&severity=high&bear_prob=high`
2. Inspect rows where `n < min_sample`

**Expected outcome:** Low-sample rows display `NA` for the stat fields (mean, median, expectancy, risk-adjusted) and carry the integer `n` so the user knows the sample size.

**Pass criteria:** Low-sample rows have `n` present and all stat values are `null` or `NA`; the row still renders (no 4xx).

---

### TC-06 — Downtrend Opportunity samples drill-down for valid cohort returns 2xx

**Type:** api
**Preconditions:** Backend is running; a downtrend-opportunity row is published with a valid phase/severity-band/P(bear)-band/angle combination.

**Steps:**
1. Call `GET /api/research/samples?kind=downtrend_opportunity&phase=bear&severity=severe&bear_prob=high&angle=held_up_best&horizon=5`
2. Verify response status and structure

**Expected outcome:** The endpoint returns a 2xx response with the individual sample-level observations (stock, date, return, max_drawdown, etc.) for that conditioned cohort.

**Pass criteria:** Response status is 200; contains array of sample objects; total count matches published row n; no 4xx on valid combinations; 4xx on invalid combinations.

---

### TC-07 — Downtrend Opportunity byte-identity: existing studies unchanged

**Type:** api
**Preconditions:** Backend is running with the same seed data as the previous stable iteration.

**Steps:**
1. Fetch the JSON response from `/api/research/event-study` (J-29/J-63)
2. Fetch the JSON response from `/api/research/regime-setup-pattern` (J-77)
3. Fetch the JSON response from `/api/research/recovery-turn-edge` (J-90)
4. Compare to a pre-computed golden JSON (or compute the MD5 hash)

**Expected outcome:** The three existing study endpoints return byte-identical results to the prior iteration; the additive J-91 enrichment does not mutate the existing data.

**Pass criteria:** MD5 hash of each existing study response matches the golden baseline; JSON structure and values are unchanged.

---

### TC-08 — Macro provider is registered in make_provider

**Type:** artifact
**Preconditions:** Backend code is present.

**Steps:**
1. Read `apps/backend/app/data_providers/__init__.py`
2. Search for a FRED macro provider entry in the `make_provider` function

**Expected outcome:** A macro provider is registered and can be instantiated.

**Pass criteria:** The `make_provider` function includes a case for the macro provider (e.g., `provider_name == "fred"`); the provider is instantiable and accepts an env-var FRED key.

---

### TC-09 — MacroSeries table created by create_all

**Type:** artifact
**Preconditions:** Backend migrations are run.

**Steps:**
1. Read `apps/backend/app/models.py`
2. Check for a `MacroSeries` model class
3. Verify it is a SQLAlchemy table with columns: symbol, date, value, source, published_date

**Expected outcome:** The `MacroSeries` table is defined and will be created by the ORM's `create_all()`.

**Pass criteria:** `MacroSeries` model exists; has the five expected columns; is registered for create_all (not marked as abstract or excluded).

---

### TC-10 — MacroSeries table registered in test_db expected-tables guard

**Type:** artifact
**Preconditions:** Backend tests are present.

**Steps:**
1. Read `apps/backend/tests/test_db.py`
2. Search for the expected-tables guard (e.g., `EXPECTED_TABLES` or similar)
3. Verify `macro_series` is in a new `MACRO_TABLES` group (not in `_ADDITIVE_COLUMNS`)

**Expected outcome:** The test confirms that the `macro_series` table is created and expected.

**Pass criteria:** `test_db.py` includes `macro_series` in a separate `MACRO_TABLES` group; the table is verified to exist after migrations.

---

### TC-11 — Macro config blocks are typed and validated

**Type:** artifact
**Preconditions:** Backend code is present.

**Steps:**
1. Read `apps/backend/app/config.py`
2. Search for a macro config block (e.g., `MacroConfig` class)

**Expected outcome:** A typed Pydantic (or dataclass) model defines the macro config with provider list, env-var name, per-series id, publication-lag, and default-off enable flags.

**Pass criteria:** The macro config block is present; all fields are typed; validation is enforced (e.g., Pydantic validators for publication-lag ≥ 0).

---

### TC-12 — Macro seed is committed for offline testing

**Type:** artifact
**Preconditions:** Backend code is present.

**Steps:**
1. Check `config.yaml` for macro series definitions
2. Check the seed data directory (e.g., `seed_data/`) for macro seed files or check `seed_loader.py` for inline macro seed

**Expected outcome:** A small macro seed is committed for the seed window (mirroring the `^VIX` seed) so offline tests are reproducible.

**Pass criteria:** At least one macro series (e.g., `^TNX`) is seeded for the entire seed window; the seed is committed and deterministic.

---

### TC-13 — FRED key read from environment only, never persisted

**Type:** artifact
**Preconditions:** Backend code is present.

**Steps:**
1. Search `apps/backend/app/data_providers/fred_provider.py` for key handling
2. Grep for any hardcoded key or persisted key in config/DB

**Expected outcome:** The FRED key is read from an environment variable (e.g., `FRED_API_KEY`) only; never written to the config file, database, or log.

**Pass criteria:** `fred_provider.py` reads the key via `os.getenv("FRED_API_KEY")` or similar; no key is committed or persisted; grep for "fred" + "key" returns no hardcoded values.

---

### TC-14 — Macro-disabled byte-identity: J-87 severity score

**Type:** api
**Preconditions:** Backend is running; macro is disabled in config (default).

**Steps:**
1. Fetch the severity score for a stock from the Dashboard (J-87) with macro disabled
2. Disable the macro input in the config, reboot, and refetch
3. Compare the two responses

**Expected outcome:** The severity score is identical whether macro is enabled or disabled, proving that macro is optional and default-off.

**Pass criteria:** JSON response MD5 hash is identical; every stock's severity score matches.

---

### TC-15 — Macro-disabled byte-identity: J-88 regime-switching observation vector

**Type:** api
**Preconditions:** Backend is running; macro is disabled in config (default).

**Steps:**
1. Fetch the regime-switching observation vector from the engine (J-88) with macro disabled
2. Compare to the vector with macro disabled again (cold boot)

**Expected outcome:** The regime emissions and observation vector are byte-identical with macro disabled.

**Pass criteria:** Engine output matches; no regime-label change; no P(bear) score change.

---

### TC-16 — Macro publication-lag alignment: published_date <= D

**Type:** artifact
**Preconditions:** Backend code is present.

**Steps:**
1. Read the macro provider code (`fred_provider.py`)
2. Check the market_phase code for macro value selection logic

**Expected outcome:** When selecting a macro value for a snapshot date D, the code checks `published_date ≤ D`, never using the current/reference-date value (which would be lookahead).

**Pass criteria:** The macro value selector includes a filter `where published_date <= snapshot_date`; no use of `current_date` or `reference_date` in the macro conditioning path.

---

### TC-17 — Walled macro provider returns honest NA, never fabricates

**Type:** api
**Preconditions:** Backend is running; the FRED API key is missing or invalid (simulated walled provider).

**Steps:**
1. Unset the FRED_API_KEY environment variable
2. Call `/api/data/jobs` or the data-manager endpoint
3. Inspect the macro provider state in the response

**Expected outcome:** The macro provider returns a `ProviderUnavailableError` or similar; the macro data is marked blocked/unavailable (NA), never fabricated.

**Pass criteria:** Response includes an honest error message for the macro provider; no fabricated macro values are returned; the system does not halt or veto GOAL_ACHIEVED.

---

### TC-18 — Downtrend Opportunity panel renders on /research

**Type:** browser
**Preconditions:** Frontend is running at localhost:3000; backend is ready.

**Steps:**
1. Navigate to `http://localhost:3000/research`
2. Scroll down to find the Downtrend Opportunity panel (below RecoveryTurnEdgeLab)
3. Verify the panel is visible and contains three side-by-side tables

**Expected outcome:** The panel is displayed with three ranked tables (held-up-best, weakness-evidence, recovery-turn-edge).

**Pass criteria:** All three angle tables are visible; headers are readable; no console errors.

---

### TC-19 — Downtrend Opportunity conditioning controls function

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible on `/research`.

**Steps:**
1. Locate the phase dropdown in the Downtrend Opportunity panel
2. Click and select a different phase (e.g., "bull" → "bear")
3. Verify the tables update with new data
4. Repeat for severity-band and P(bear)-band dropdowns

**Expected outcome:** Changing any conditioning control re-queries the backend and updates all three tables with filtered results.

**Pass criteria:** Each dropdown is functional; table rows update when a condition changes; no console errors; as-of date does not change.

---

### TC-20 — Downtrend Opportunity horizon and view toggles work

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible on `/research`.

**Steps:**
1. Locate the horizon toggle (e.g., 5-day, 10-day)
2. Click to change horizons
3. Verify table values (mean, median, expectancy) update
4. Click Episodes⇄Pooled toggle
5. Verify table rows update with pooled aggregates

**Expected outcome:** Each toggle re-queries and updates the table; the data reflects the selected horizon and view.

**Pass criteria:** Toggles are functional; table data changes appropriately; stats remain consistent.

---

### TC-21 — Downtrend Opportunity As-of⇄All-history toggle

**Type:** browser
**Preconditions:** Frontend is running; a historical as-of date is selected in the global as-of switcher.

**Steps:**
1. Verify the global as-of date is set to a past date (e.g., 2024-01-15)
2. Locate the As-of⇄All-history toggle in the Downtrend Opportunity panel
3. Click to switch from As-of to All-history
4. Observe the table rows

**Expected outcome:** The as-of-scoped view shows observations ≤ 2024-01-15; all-history shows the full range. The toggle filters the same observation set without changing the panel date.

**Pass criteria:** Toggle works; observation counts differ appropriately; no date-state is created in the panel.

---

### TC-22 — Downtrend Opportunity N= chip opens samples in new tab

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible; a row has N > 0.

**Steps:**
1. Locate the `N=` chip in the first row of the held-up-best angle
2. Right-click and open in a new tab (or use Ctrl+click)
3. In the new tab, verify the URL is `/research/samples?kind=downtrend_opportunity&...`
4. Verify the sample count matches the published n

**Expected outcome:** The `N=` chip opens a samples drill-down page in a new tab; the URL includes the correct query parameters; the sample count on the new page equals the published row n.

**Pass criteria:** Link is present and functional; URL is correct; samples load in new tab; count is coherent.

---

### TC-23 — Downtrend Opportunity low-sample shows NA + n

**Type:** browser
**Preconditions:** Frontend is running; a conditioned cohort (phase/severity/P(bear)) has fewer than min_sample observations.

**Steps:**
1. Use conditioning controls to filter to a sparse cohort
2. Verify a row appears with `NA` for mean, median, expectancy, risk-adjusted stats
3. Verify the row still displays `n` (sample count)

**Expected outcome:** Low-sample rows show `NA` + count; the row is rendered (not hidden or error).

**Pass criteria:** NA values are displayed; n is visible; row is sortable and interactive.

---

### TC-24 — Downtrend Opportunity weakness angle labelled EVIDENCE ONLY

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible.

**Steps:**
1. Locate the weakness-evidence table
2. Verify a label "EVIDENCE ONLY" or similar is present
3. Verify no order/execution affordance (buttons, links) are present

**Expected outcome:** The weakness angle is clearly marked as evidence-only; no order or short-deployment affordance is available.

**Pass criteria:** EVIDENCE-ONLY label is visible; no order/execution UI elements are present.

---

### TC-25 — Downtrend Opportunity survivorship-bias label present

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible.

**Steps:**
1. Locate the survivorship-bias caveat banner or label in the panel
2. Verify the message explains that results are scoped to current-membership universe

**Expected outcome:** A caveat banner appears below or near the panel stating the survivorship limitation.

**Pass criteria:** Label is visible and readable; message is accurate.

---

### TC-26 — Downtrend Opportunity client-side column sort works

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible.

**Steps:**
1. Click the "mean" column header
2. Verify rows re-order (ascending or descending)
3. Click again to reverse order
4. Verify NA rows sort to the end (per J-82 NA-last contract)

**Expected outcome:** Clicking column headers sorts the table; NA values remain at the end.

**Pass criteria:** Sort is functional; NA-last ordering is correct; no console errors.

---

### TC-27 — Publication-lag limitation label visible for macro-conditioned figures

**Type:** browser
**Preconditions:** Frontend is running; macro is enabled in config.

**Steps:**
1. Navigate to a page or panel where macro-conditioned figures are displayed
2. Verify a publication-lag limitation label is visible (e.g., "Values reflect FRED publication lag")
3. Check the Dashboard or Research panels for macro-influenced scores

**Expected outcome:** A label explains the publication-lag limitation wherever macro inputs are used.

**Pass criteria:** Label is visible; message is clear; label is present on all affected surfaces.

---

### TC-28 — Macro provider visible in Data Manager provider catalog

**Type:** browser
**Preconditions:** Frontend is running; navigate to `/data` (Data Manager).

**Steps:**
1. Open the Data Manager page
2. Locate the provider catalog or import interface
3. Verify the macro provider (FRED) is listed alongside existing providers (Yahoo, Tiingo, etc.)

**Expected outcome:** The macro provider appears in the catalog with an honest state (blocked/unavailable if no key, or ready if the key is set).

**Pass criteria:** Macro provider is listed; import path is available (if key is set) or shows blocked state.

---

### TC-29 — Default figures byte-identical with macro disabled

**Type:** browser
**Preconditions:** Frontend is running; macro is disabled in config (default state).

**Steps:**
1. Take a screenshot of the Dashboard and /research page with macro disabled
2. Verify the rendered values visually match the prior iteration
3. Inspect network traffic to confirm the same endpoint responses

**Expected outcome:** The page appearance and data are identical to the prior iteration; macro is not impacting default renders.

**Pass criteria:** Visual diff is zero; endpoint responses match golden baseline.

---

### TC-30 — J-18 CRITICAL: exactly one date selector, no page-local date state

**Type:** browser
**Preconditions:** Frontend is running; Downtrend Opportunity panel is visible on `/research`.

**Steps:**
1. Use Chrome DevTools to search for `useState` in the React component tree for date state
2. Search for any window/document keydown listeners in the Downtrend Opportunity code
3. Verify only the global as-of switcher controls the date

**Expected outcome:** No page-local date `useState` or keydown listener is present in the J-91 or J-92 code; the global as-of controls all date-scoped views.

**Pass criteria:** Code review confirms zero date state in the new panel; all date control flows through the global as-of switcher.

---

### TC-31 — J-87/J-88 Dashboard Market-Phase unchanged

**Type:** browser
**Preconditions:** Frontend is running; navigate to the Dashboard.

**Steps:**
1. Verify the Market-Phase panel is present with regime label and severity score
2. Compare to the prior iteration's screenshot
3. Verify the date shown matches the global as-of, not any new local date

**Expected outcome:** The Dashboard Market-Phase panel is unchanged; regime and severity are consistent with the prior iteration.

**Pass criteria:** Visual and data match; no regression.

---

### TC-32 — J-06 single source: stock score identical across pages

**Type:** browser
**Preconditions:** Frontend is running; select a stock symbol and navigate to the stock detail page.

**Steps:**
1. Note the Leadership score on the Stocks leaderboard
2. Navigate to the stock detail page
3. Verify the Leadership score is identical

**Expected outcome:** The same score reads identically on both pages.

**Pass criteria:** Score is byte-identical; no recomputation in the UI.

---

### TC-33 — J-07 Risk-Off gate: zero stocks Actionable in Risk-Off regime

**Type:** api
**Preconditions:** Backend is running; a Risk-Off regime is seeded.

**Steps:**
1. Call `/api/stocks` or `/api/data/latest` with an as-of date in the Risk-Off regime
2. Verify the `actionable` or `scan_status` field for all stocks

**Expected outcome:** All stocks are marked watchlist-only (not Actionable) when the regime is Risk-Off.

**Pass criteria:** No Actionable stocks are returned in a Risk-Off regime.

---

### TC-34 — J-29/J-63 event-study byte-identity

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Fetch `/api/research/event-study` for a given horizon and view
2. Compare the JSON MD5 to the prior iteration's golden baseline

**Expected outcome:** The event-study endpoint returns byte-identical results.

**Pass criteria:** MD5 hash matches; no stat fields added or changed.

---

### TC-35 — J-77 regime-setup-pattern byte-identity

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Fetch `/api/research/regime-setup-pattern` for a given horizon
2. Compare the JSON MD5 to the prior iteration's golden baseline

**Expected outcome:** The regime-setup-pattern endpoint returns byte-identical results.

**Pass criteria:** MD5 hash matches; no stat fields added or changed.

---

### TC-36 — J-90 recovery-turn-edge reused in Downtrend Opportunity angle (c)

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Fetch `/api/research/downtrend-opportunity` and extract the `recovery_turn_edge` angle
2. Fetch `/api/research/recovery-turn-edge` directly
3. Compare the two responses

**Expected outcome:** The recovery-turn-edge angle in the downtrend-opportunity response is identical to the standalone recovery-turn-edge endpoint.

**Pass criteria:** Both responses contain identical recovery-turn edge data; no recomputation.

---

### TC-37 — J-32 as-of date filtering respected

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Call `/api/research/downtrend-opportunity?as_of=2024-01-15`
2. Verify all observation dates are ≤ 2024-01-15

**Expected outcome:** Observations are filtered to the as-of date; forward returns are computed from data after the as-of date.

**Pass criteria:** All returned observations are dated ≤ the as-of date; no lookahead.

---

### TC-38 — J-51/J-65 samples count-coherence

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Publish a Downtrend Opportunity row with `n=42` for a given cohort (phase/severity/P(bear)/angle/horizon)
2. Call `GET /api/research/samples?kind=downtrend_opportunity&...` with matching parameters
3. Count the returned samples

**Expected outcome:** The sample count equals the published row n.

**Pass criteria:** Sample count == published n; no drift across multiple queries.

---

### TC-39 — J-82 every displayable cohort combination resolves 2xx

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Iterate through all phase/severity-band/P(bear)-band/angle combinations published in the study response
2. For each, call `GET /api/research/samples?kind=downtrend_opportunity&...`
3. Verify all return 2xx

**Expected outcome:** Every published row's drill-down resolves without a 4xx.

**Pass criteria:** All drill-downs return 2xx (200 or 206); no invalid-combination 4xx errors.

---

### TC-40 — Test suite full pass with macro and without

**Type:** artifact
**Preconditions:** Backend tests are ready to run.

**Steps:**
1. Run `pytest` with macro disabled (default config)
2. Verify all ~880 tests pass
3. Enable macro in config
4. Run `pytest` again
5. Verify all tests pass (with the same seed)

**Expected outcome:** Full test suite passes with and without macro enabled; byte-identity assertions pass.

**Pass criteria:** Exit code 0; no test failures reported; byte-identity assertions green with macro disabled.

---

## Summary

**Total test cases:** 40
- **API tests:** 20 (TC-01 to TC-17, TC-34 to TC-39)
- **Browser tests:** 14 (TC-18 to TC-30)
- **Artifact tests:** 6 (TC-08 to TC-12, TC-40)

**Key coverage areas:**
- Downtrend Opportunity study (three angles, conditioning, filtering, count-coherence)
- Macro provider integration (registration, table, config, env-only key, walled provider)
- Byte-identity of existing studies (J-29, J-77, J-90)
- Frontend UI surfaces (panel, controls, toggles, N= drill-down, labels)
- Critical anti-goals (exactly-one-date, no-lookahead, no-recompute, byte-identity-when-disabled)
- Full test suite gate (all ~880 tests pass)

