# Goal Iteration 14 — Event Study Episodes Default Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Frontend Present:** yes

## Phase Goal

The Setup & Pattern Lab (`/research`) defaults to a **first-trigger Episodes** view that collapses consecutive same-symbol signal-days of a subject into one observation, with a one-click **Episodes ⇄ Pooled** toggle whose Pooled figures are byte-identical to prior output. Both modes disclose n (observations), unique symbols, and episode count.

## Test Cases

### TC-01 — Event Study Loads in Episodes Mode by Default

**Type:** browser
**Preconditions:** Frontend is running; user is on `/research` page with at least one subject (e.g., Risk-off-watchlist) selected and a forward-return horizon available.

**Steps:**
1. Navigate to `/research` page
2. Observe the Setup & Pattern Lab section
3. Check the default state of the view mode

**Expected outcome:** The lab renders with Episodes mode active (visible as the selected/highlighted toggle state).
**Pass criteria:** The lab displays "Episodes" as the active/selected view mode in a segmented toggle control; Pooled is visible as an alternate option.

---

### TC-02 — Episodes ⇄ Pooled Toggle is Visible and Clickable

**Type:** browser
**Preconditions:** Frontend is running; `/research` page is loaded with EventStudyLab visible.

**Steps:**
1. Locate the Episodes⇄Pooled toggle control in the EventStudyLab
2. Verify it is styled as a segmented button group (not a `<select>`)
3. Attempt to click the Pooled option

**Expected outcome:** The toggle transitions from Episodes to Pooled when clicked; the lab re-renders with Pooled data.
**Pass criteria:** The toggle changes state visibly; no JavaScript errors in console; the toggle is not nested inside another interactive element (ESLint/dev-overlay warnings absent).

---

### TC-03 — Episodes Mode Disclosure Line Shows n, Unique Symbols, Episode Count

**Type:** browser
**Preconditions:** `/research` page is loaded with EventStudyLab in Episodes mode; a subject with multiple observations is selected.

**Steps:**
1. Observe the text/label area below or beside the event-study figures
2. Verify the presence of three disclosure metrics
3. Note the values for a subject with persisting symbols (e.g., Risk-off-watchlist)

**Expected outcome:** A disclosure line is visible listing:
- `n` = the count of observations in Episodes mode
- `unique_symbols` = the count of distinct tickers
- `episode_count` = the count of distinct first-trigger episodes
**Pass criteria:** All three values are displayed; numbers are formatted (ISO/number format); the disclosure line is rendered in muted/faint text styling consistent with the lab's design.

---

### TC-04 — Pooled Mode Disclosure Line Shows Same Structure

**Type:** browser
**Preconditions:** `/research` page is loaded; EventStudyLab has been toggled to Pooled mode.

**Steps:**
1. Toggle to Pooled mode
2. Observe the disclosure line
3. Verify the presence and values of n, unique_symbols, episode_count

**Expected outcome:** The disclosure line is present in Pooled mode; `n` equals the count of per-signal-day rows (should be ≥ the Episodes `n` for most subjects); `unique_symbols` and `episode_count` are identical to Episodes mode (since they derive from the same observation set).
**Pass criteria:** Disclosure line renders in both modes; `n` is mode-dependent; `unique_symbols` and `episode_count` values match between Episodes and Pooled.

---

### TC-05 — Pooled Mode Figures are Byte-Identical to Prior Output

**Type:** api
**Preconditions:** Backend is running; a subject and horizon are available.

**Steps:**
1. Capture the current pre-change output by running: `curl -s "http://localhost:8000/api/research/event-study?subject_key=<subject>&horizon=<horizon>" | jq .`
2. After the change, run the same query with `view=pooled` explicitly: `curl -s "http://localhost:8000/api/research/event-study?subject_key=<subject>&horizon=<horizon>&view=pooled" | jq .`
3. Compare the two JSON payloads (excluding the `view` and disclosure-value fields which are new)

**Expected outcome:** All existing figures (per-horizon distribution, hit-rate, expectancy, MAE/MFE, best-exit-horizon, risk-adjusted ratios, by-regime, by-sector) are byte-identical between the pre-change and `view=pooled` outputs.
**Pass criteria:** Diff of the two responses (minus new fields) shows zero differences in any numeric or categorical field.

---

### TC-06 — Episodes Mode Shows Fewer or Equal Observations Than Pooled

**Type:** api
**Preconditions:** Backend is running; a subject with persisting symbols (continuous occurrences) is selected.

**Steps:**
1. Fetch the event-study with default (Episodes) mode: `curl -s "http://localhost:8000/api/research/event-study?subject_key=Risk-off-watchlist&horizon=<horizon>" | jq .n`
2. Fetch the same with Pooled mode: `curl -s "http://localhost:8000/api/research/event-study?subject_key=Risk-off-watchlist&horizon=<horizon>&view=pooled" | jq .n`
3. Compare the two `n` values

**Expected outcome:** The Episodes `n` is less than or equal to the Pooled `n` (Episodes collapses consecutive runs).
**Pass criteria:** `episodes_n` ≤ `pooled_n`; for subjects with repeating symbols, `episodes_n` < `pooled_n`.

---

### TC-07 — Episode-Mode Samples Drill-Down Shows One Row per First-Trigger

**Type:** browser
**Preconditions:** `/research` page is loaded in Episodes mode; EventStudyLab is visible with at least one subject and an `N=` chip (indicating observations for a cohort).

**Steps:**
1. Click an `N=` chip in Episodes mode (e.g., the n value or a samples link labeled `N=<count>`)
2. Verify a new tab opens to `/research/samples`
3. Inspect the rows returned for a subject with continuous runs (e.g., multiple trigger dates for the same ticker)

**Expected outcome:** The samples drill-down lists observations, with one row per first-trigger date for each continuous run of the same ticker.
**Pass criteria:** For a continuous run of the same ticker across multiple stored snapshot dates, only one row appears (at the first trigger date); the row carries the stored return/MAE/MFE/regime/sector from that observation verbatim.

---

### TC-08 — Pooled-Mode Samples Drill-Down Shows All Signal Days

**Type:** browser
**Preconditions:** `/research` page is loaded; EventStudyLab is toggled to Pooled mode; an `N=` chip is visible.

**Steps:**
1. Toggle to Pooled mode
2. Click the same `N=` chip
3. Verify a new tab opens to `/research/samples` with `view=pooled` in the URL
4. Inspect the rows for the same subject

**Expected outcome:** The samples drill-down lists all per-signal-day observations; multiple rows appear for the same ticker if they were triggered on different stored run-dates.
**Pass criteria:** The row count in Pooled mode matches the `n` value from the Pooled disclosure; rows are NOT collapsed by consecutive date.

---

### TC-09 — N= Chip Count Matches Samples Drill-Down Total in Both Modes

**Type:** browser
**Preconditions:** `/research` page is loaded; EventStudyLab is visible with samples available.

**Steps:**
1. In Episodes mode, record the `N=<count>` value from a chip (or click the chip and count rows in `/research/samples`)
2. Toggle to Pooled mode and record the `N=` value for the same cohort
3. Open each in a new tab and verify the drill-down row count matches the clicked N

**Expected outcome:** In Episodes mode, the `N=` value equals the row count in the samples drill-down; in Pooled mode, the (larger) `N=` value equals the row count in that drill-down.
**Pass criteria:** `episodes_N === episodes_samples_row_count` AND `pooled_N === pooled_samples_row_count`; both assertions hold for the same subject/horizon/cohort.

---

### TC-10 — Samples View Parameter is Carried in N= Chip Href

**Type:** artifact
**Preconditions:** Frontend is built and running; `/research` page has been loaded.

**Steps:**
1. Open `/research` page in a browser and toggle to Episodes mode
2. Inspect the DOM for an `N=` chip element (using Chrome DevTools)
3. Read the `href` attribute of the chip's `<a>` or `<button>` element
4. Verify the URL contains `view=episodes` (or the default if omitted)
5. Repeat in Pooled mode

**Expected outcome:** The `N=` chip href includes the `view` parameter matching the current mode (e.g., `?view=episodes` or `?view=pooled`); when clicked, the new tab's URL reflects the mode.
**Pass criteria:** Episodes-mode chip href contains `view=episodes` (or no `view`, if omitted as default); Pooled-mode chip href contains `view=pooled`.

---

### TC-11 — /research/samples Page Reads and Respects View Parameter

**Type:** browser
**Preconditions:** `/research/samples` page is accessible; a `view` query parameter is present in the URL.

**Steps:**
1. Navigate to `/research/samples?subject_key=<subject>&horizon=<horizon>&view=episodes`
2. Note the rows displayed
3. Navigate to the same URL with `view=pooled`
4. Note the rows displayed

**Expected outcome:** With `view=episodes`, the page renders collapsed first-trigger episodes; with `view=pooled`, the page renders all per-signal-day observations; the total row count differs between modes.
**Pass criteria:** Samples page respects the `view` parameter; row counts and content match the selected mode.

---

### TC-12 — API Returns 422 for Invalid View Parameter

**Type:** api
**Preconditions:** Backend is running.

**Steps:**
1. Send: `curl -s "http://localhost:8000/api/research/event-study?subject_key=test&horizon=1&view=invalid" -w "\nStatus: %{http_code}\n"`
2. Send: `curl -s "http://localhost:8000/api/research/samples?subject_key=test&horizon=1&kind=event_study&view=invalid" -w "\nStatus: %{http_code}\n"`

**Expected outcome:** Both requests return HTTP 422 (Unprocessable Entity) with an error message indicating the invalid `view` value.
**Pass criteria:** Status code is 422; error response body includes a validation message naming the allowed values (`episodes`, `pooled`).

---

### TC-13 — Methodology Page Lists Episode and Pooled Glossary Entries

**Type:** browser
**Preconditions:** Frontend is running; user can navigate to `/methodology`.

**Steps:**
1. Navigate to `/methodology` page
2. Search or scroll for glossary entries containing "Episode" and "Pooled"
3. Verify both entries are present and readable

**Expected outcome:** The `/methodology` page displays two new glossary entries:
- **Episode** — defines first-trigger observation collapsing consecutive same-symbol occurrences
- **Pooled (per-signal-day)** — defines all per-signal-day observations
**Pass criteria:** Both entries appear on the page; text is sourced from the `config.yaml` `methodology.terms` catalog; no hard-coded duplication in the source code.

---

### TC-14 — Event Study Figures Recomputed from Mode-Specific Observation Set

**Type:** api
**Preconditions:** Backend is running; a test subject with enough observations to show different distribution/hit-rate is available.

**Steps:**
1. Fetch event-study with `view=episodes`: `curl -s "http://localhost:8000/api/research/event-study?subject_key=<subject>&horizon=<horizon>&view=episodes" | jq '.by_regime'`
2. Fetch with `view=pooled`: `curl -s "http://localhost:8000/api/research/event-study?subject_key=<subject>&horizon=<horizon>&view=pooled" | jq '.by_regime'`
3. Compare the by-regime figures (e.g., hit-rate, expectancy) between the two

**Expected outcome:** The `by_regime` figures (and similarly `by_sector`, distribution, hit-rate, MAE/MFE) are derived from the mode's observation set; if a regime has fewer episodes due to collapsing, its stats may differ from Pooled.
**Pass criteria:** Figures match the observation set (e.g., `by_regime.win_count + loss_count` ≤ `by_regime.win_count_pooled + loss_count_pooled` in most cases); pooled figures are byte-identical to pre-change output.

---

### TC-15 — Empty/Low-Sample Cohort Returns Honest NA and n (No Fabrication)

**Type:** api
**Preconditions:** Backend is running; a subject/horizon with zero forward-tested occurrences or very low sample count is available.

**Steps:**
1. Select a subject/horizon with no or very few observations
2. Fetch: `curl -s "http://localhost:8000/api/research/event-study?subject_key=<subject>&horizon=<horizon>&view=episodes" | jq '.mean_return, .n, .unique_symbols'`
3. Verify the response

**Expected outcome:** `mean_return` and other figures are `null` (NA); `n` is 0 or the actual low count; no fabricated row or synthetic observation is created.
**Pass criteria:** Response contains `null` for unavailable metrics; `n` matches the actual observation count; no synthetic row in the payload.

---

### TC-16 — View Orthogonality: Episodes Toggle Does Not Affect Global As-Of Date

**Type:** browser
**Preconditions:** `/research` page is loaded with a historical as-of date selected (if supported by the interface).

**Steps:**
1. Note the current as-of date from the global date selector / asof-provider
2. Toggle from Episodes to Pooled and back
3. Verify the as-of date remains unchanged

**Expected outcome:** Toggling the Episodes⇄Pooled control does not change the `?asof` URL parameter, the global as-of state, or the J-32 analysis-mode.
**Pass criteria:** The `?asof` query parameter (if present) is unchanged after toggling; the page date remains consistent.

---

### TC-17 — Count-Coherence: Samples Total Equals Event-Study n (Same-Instant)

**Type:** api
**Preconditions:** Backend is running with fresh/live database state.

**Steps:**
1. Fetch event-study: `curl -s "http://localhost:8000/api/research/event-study?subject_key=<subject>&horizon=<horizon>&view=episodes" | jq '.n'` → `episodes_n`
2. Fetch samples: `curl -s "http://localhost:8000/api/research/samples?subject_key=<subject>&horizon=<horizon>&kind=event_study&view=episodes" | jq 'length'` → `samples_count`
3. Assert `episodes_n === samples_count`
4. Repeat for `view=pooled`

**Expected outcome:** The row count returned by the samples endpoint equals the `n` value from the event-study endpoint for the same cohort and mode, assessed at the same instant.
**Pass criteria:** `event_study.n === samples_rowcount` for both Episodes and Pooled; assertion uses live aggregate, not a hardcoded fixture value.

---

### TC-18 — Regression: J-29 Event Study Lab Renders All Figures Unchanged

**Type:** browser
**Preconditions:** `/research` page is loaded; EventStudyLab is in Episodes mode.

**Steps:**
1. Observe the EventStudyLab figures: distribution, hit-rate, expectancy, MAE/MFE, best-exit-horizon, risk-adjusted ratios
2. Verify all are rendered and populated (not missing)
3. Toggle to Pooled and verify the same set of figures appear

**Expected outcome:** All figures are visible in both Episodes and Pooled modes; no figure is missing or hidden by the new toggle.
**Pass criteria:** Complete figure set (distribution chart, hit-rate %, expectancy $, MAE/MFE %, Sharpe, Sortino, etc.) is rendered in both modes.

---

### TC-19 — Regression: J-51/J-64/J-65 Samples Drill-Down Retains Sort/Filter and New-Tab Links

**Type:** browser
**Preconditions:** `/research/samples` page is accessible.

**Steps:**
1. Open `/research/samples` page (linked from an `N=` chip in Episodes mode)
2. Verify sort controls are present (if applicable per J-51)
3. Verify filter controls are present (if applicable per J-64/J-65)
4. Verify the drill-down content matches the clicked N

**Expected outcome:** Samples page retains all prior sort/filter/display functionality; new-tab link from `N=` chips in both modes works correctly.
**Pass criteria:** Sort/filter controls remain functional; row count matches the clicked N in both modes; no regressions in existing samples features.

---

### TC-20 — Regression: J-32 All/AsOf Analysis-Mode Unchanged

**Type:** browser
**Preconditions:** `/research` page is loaded.

**Steps:**
1. Locate the analysis-mode toggle (all-history vs. as-of, if present per J-32)
2. Toggle between modes
3. Verify EventStudyLab data updates accordingly
4. Toggle Episodes⇄Pooled while analysis-mode is active

**Expected outcome:** The J-32 analysis-mode toggle and the Episodes⇄Pooled toggle are independent; toggling one does not affect the other's state or behavior.
**Pass criteria:** Analysis-mode toggle continues to work as before; Episodes⇄Pooled is a separate, orthogonal control.

---

### TC-21 — Backend Read-Only Assertion: No INSERT/UPDATE in Episode Path

**Type:** artifact
**Preconditions:** Backend test suite is available.

**Steps:**
1. Run backend unit tests targeting the event-study and samples read-only paths: `pytest apps/backend/tests/test_research*.py -k "read_only or episode" -v`
2. Inspect test output for assertions on database operations

**Expected outcome:** Tests pass, confirming that `compute_event_study` and `_event_study_samples` issue ONLY SELECT queries (no INSERT/UPDATE/commit/run_scan/score_*/detect_*/forward_* calls) in the new Episode path.
**Pass criteria:** Test logs confirm SELECT-only operations; no database write operations are triggered.

---

### TC-22 — Episode-Collapse Determinism: Consecutive Runs Collapse to One

**Type:** artifact
**Preconditions:** Backend test suite is available.

**Steps:**
1. Run backend unit tests targeting episode-collapse logic: `pytest apps/backend/tests/test_research*.py -k "episode" -v`
2. Inspect test output for assertions on consecutive-date grouping

**Expected outcome:** Tests pass, confirming that consecutive stored snapshot dates for the same `(ticker, subject)` collapse into ONE first-trigger observation; rows carry stored return/MAE/MFE/regime/sector verbatim.
**Pass criteria:** Test logs confirm episode-collapse logic works correctly; first-trigger date is extracted; stored values are preserved (no recomputation).

---

### TC-23 — Episode-Collapse Determinism: Gaps in Stored Run-Date Sequence Split Episodes

**Type:** artifact
**Preconditions:** Backend test suite is available; a test subject with a gap in the stored run-date sequence.

**Steps:**
1. Run backend unit tests targeting gap-split logic: `pytest apps/backend/tests/test_research*.py -k "episode" -v`
2. Inspect test output for assertions on gap handling

**Expected outcome:** Tests pass, confirming that a break (gap) in the ordered `ScannerRun.asof_date` sequence (subject NOT triggered on an intervening stored run-date) yields SEPARATE episodes, not a merged observation.
**Pass criteria:** Test logs confirm gap-split logic; episodes are correctly separated by missing trigger dates in the run-date sequence.

---

### TC-24 — Disclosure Values: n is Mode-Dependent, unique_symbols and episode_count are Derivations

**Type:** artifact
**Preconditions:** Backend test suite is available.

**Steps:**
1. Run backend unit tests targeting disclosure-value computation: `pytest apps/backend/tests/test_research*.py -k "disclosure" -v`
2. Inspect test output for assertions on value correctness

**Expected outcome:** Tests pass, confirming:
- `n` differs between Episodes (collapsed) and Pooled (per-signal-day) modes
- `unique_symbols` is identical in both modes (distinct tickers in the observation set)
- `episode_count` is identical in both modes (first-trigger episodes regardless of rendered mode)
**Pass criteria:** Test logs confirm correct computation of all three disclosure values; mode-dependent and mode-independent assertions pass.

---

### TC-25 — Glossary Config: Methodology Terms Render Without Hard-Coded Duplication

**Type:** artifact
**Preconditions:** Backend is running; `/methodology` page is accessible.

**Steps:**
1. Inspect `config.yaml` for new `methodology.terms` entries under `forward_evidence` category
2. Check `apps/frontend/app/research/page.tsx` and other frontend sources for hard-coded term definitions
3. Verify the glossary terms on `/methodology` are sourced from the config

**Expected outcome:** The Episode and Pooled entries are in `config.yaml` `methodology.terms`; no duplicate term definitions exist in the frontend source code.
**Pass criteria:** Glossary terms are defined once in `config.yaml`; `/methodology` page renders them from the config without duplication.

---

## Summary

**Total test cases:** 25
- **API tests:** 6 (TC-05, TC-06, TC-12, TC-14, TC-17, and TC-24 artifact-based)
- **Browser tests:** 13 (TC-01, TC-02, TC-03, TC-04, TC-07, TC-08, TC-09, TC-11, TC-13, TC-16, TC-18, TC-19, TC-20)
- **Artifact/unit tests:** 6 (TC-10, TC-21, TC-22, TC-23, TC-24, TC-25)

All test cases map directly to the DEFINITION OF DONE and TESTING REQUIREMENTS sections of the phase spec. Byte-identity guard (TC-05), episode-collapse determinism (TC-22, TC-23), count-coherence both modes (TC-17), and regression sweep (TC-18 through TC-20) are included as required gates.
