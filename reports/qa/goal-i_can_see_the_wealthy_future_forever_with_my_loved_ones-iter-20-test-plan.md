# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Frontend Present:** yes

## Phase Goal

Deliver three backend research cluster must-haves: event-study performance (J-72) via cached derived aggregates with byte-identical figures and a single batched read per `(subject, view, as_of)`; per-stock forward returns (J-75) read verbatim from stored data and displayed on leaderboard + detail; and a new ranked Regime × Setup × Pattern research study (J-77) grouping the enriched observation set with count-coherence guarantees and drill-down samples.

## Test Cases

### TC-01 — Event-study output byte-identical in both views and all windows

**Type:** api (backend unit/integration)
**Preconditions:** Backend seeded with committed test data; `apps/backend/tests/test_research.py` fixture(s) covering `compute_event_study`.
**Steps:**
1. Call `compute_event_study(subject, view='episodes', as_of=None)` and `compute_event_study(subject, view='episodes', as_of=<historical date>)`.
2. Call `compute_event_study(subject, view='pooled', as_of=None)` and `compute_event_study(subject, view='pooled', as_of=<historical date>)`.
3. Compare the full result payloads (all figures, structure) against pre-iter-20 baseline captures.
**Expected outcome:** All four calls produce payloads with byte-identical figures and structure to the prior implementation.
**Pass criteria:** `as_of=None` episodes, `as_of=<date>` episodes, `as_of=None` pooled, and `as_of=<date>` pooled all match committed assertion values; no horizon-by-horizon re-scan visible in the code (single batched read assertion in test).

---

### TC-02 — Event-study single-batched-read assertion (no per-horizon scan)

**Type:** api (backend integration)
**Preconditions:** A test with query-logging or mock-count instrumentation.
**Steps:**
1. Enable SQL logging or mock the `ForwardReturn` query.
2. Call `compute_event_study(subject, ...)` for a subject with multiple configured horizons.
3. Count the number of `ForwardReturn` scans / queries issued.
**Expected outcome:** Exactly ONE batched read of the subject's observation pool, regardless of the number of horizons.
**Pass criteria:** `len(forward_return_queries) == 1`; the query fetches the entire pool once; a run-position index is computed in-memory for all horizons.

---

### TC-03 — Event-study cache refreshes after dataset change

**Type:** api (backend integration)
**Preconditions:** Event-study cache table exists (standalone `create_all`-managed table); `compute_event_study` calls the cache read/write/invalidate logic.
**Steps:**
1. Call `compute_event_study(subject, ...)` and confirm the cache is written.
2. Fetch and record the cached `dataset_version` key.
3. Simulate a dataset change: add a new snapshot via `ScannerRun.insert()` or remove one.
4. Call `compute_event_study(subject, ...)` again.
5. Confirm the new cache entry has a different `dataset_version` and the figures reflect the dataset change.
**Expected outcome:** Cache is invalidated and recomputed on dataset change; old cached entry is not served; figures update to reflect new data.
**Pass criteria:** `dataset_version` changes after insert/remove; new call returns fresh figures; no stale cache returned.

---

### TC-04 — Event-study endpoint serves cached aggregate (never recomputes)

**Type:** api (REST)
**Preconditions:** Backend on `http://localhost:8000`; seeded data; cache populated.
**Steps:**
1. Call `GET /api/research/event-study?subject=<ticker>&view=episodes&horizon=1&as_of=<date>` twice in quick succession.
2. Verify the endpoint returns the same cached payload both times.
3. Optionally mock the `compute_event_study` function and confirm it is NOT called on the second request (cache hit).
**Expected outcome:** Both calls return identical payloads; the second call serves the cached value without recomputing.
**Pass criteria:** Payload shape and figures identical across calls; optional instrumentation shows no `compute_event_study` call on cache hit.

---

### TC-05 — J-75: Forward returns read verbatim from stored `forward_returns` table

**Type:** api (backend integration)
**Preconditions:** Seeded `forward_returns` rows for test symbols across multiple horizons; `/api/stocks` and `/api/stocks/{ticker}` endpoints.
**Steps:**
1. For a symbol (e.g., "AAPL") with stored forward returns for horizons [1, 5, 10, 20, 60], query `forward_returns` directly: `SELECT * FROM forward_returns WHERE run_id=<test_run>, symbol='AAPL', horizon IN (1,5,10,20,60)`.
2. Call `GET /api/stocks?as_of=<test_date>` and find the "AAPL" row.
3. Extract the five forward-return columns from the response.
4. Compare the five values against the direct `forward_returns` query.
**Expected outcome:** All five horizon values are identical and match the stored row values exactly.
**Pass criteria:** `leaderboard_row[forward_1d] == forward_returns[horizon=1].return`, and similarly for [5, 10, 20, 60]; values are read VERBATIM, never recomputed.

---

### TC-06 — J-75: Leaderboard and Stock Detail forward returns identical

**Type:** api (REST + browser)
**Preconditions:** Backend seeded; frontend running; a historical `as_of` date with complete forward returns.
**Steps:**
1. Call `GET /api/stocks?as_of=2026-05-28` and extract the "AAPL" row's five forward returns.
2. Call `GET /api/stocks/AAPL?as_of=2026-05-28` (Stock Detail) and extract the five forward returns.
3. Compare the two sets of values.
**Expected outcome:** Leaderboard and Stock Detail forward returns are identical for the same ticker/date/horizon.
**Pass criteria:** All five horizon values match exactly between the two endpoints (J-06 coherence — same stored row, single source of truth).

---

### TC-07 — J-75: Near-latest horizons render NA (never fabricated)

**Type:** api (REST)
**Preconditions:** Test fixture with latest snapshot date known (e.g., 2026-06-12); no forward-return rows exist for the latest run (by design — not enough subsequent bars).
**Steps:**
1. Call `GET /api/stocks?as_of=2026-06-12` (latest).
2. For a symbol, inspect all five forward-return columns.
**Expected outcome:** All five forward returns are `null` / `"NA"` (honest representation — no future bars available to compute return).
**Pass criteria:** All five horizon cells are null or "NA", never a fabricated number; the cell renders an honest missing-data marker in the UI.

---

### TC-08 — J-75: Horizons are config-driven (no hardcoded [1,5,10,20,60])

**Type:** artifact (code review)
**Preconditions:** `apps/backend/app/engine/snapshot_serving.py` and test code available.
**Steps:**
1. Grep `snapshot_serving.py` for hardcoded horizon list [1, 5, 10, 20, 60] or equivalents.
2. Confirm all horizon values are read from `config.walk_forward.horizons`.
3. Verify tests parameterize over the config horizons, not a fixed list.
**Expected outcome:** No hardcoded horizon list in serving code; `config.walk_forward.horizons` is the single source.
**Pass criteria:** Grep returns zero hardcoded `[1,5,10,20,60]` literals in serving code; all calls to forward returns are keyed by `config.walk_forward.horizons`.

---

### TC-09 — J-75: Forward returns are sortable (view-transform contract, J-48)

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; `/stocks` page rendered with forward-return columns visible.
**Steps:**
1. Navigate to `/stocks?asof=2026-05-28`.
2. Click the "1d Return" column header (first forward-return column).
3. Observe the table re-order by that column (ascending).
4. Click again to reverse (descending).
5. Confirm the rank column (e.g., Rank #1, #2, …) stays in the original stored order (not re-ranked).
**Expected outcome:** Forward-return columns are sortable; sort re-orders the leaderboard rows but does not refetch or recompute any value.
**Pass criteria:** Column header is clickable and sortable; no network request on sort; leaderboard rows re-order client-side per the J-48 view-transform contract; rank column unchanged.

---

### TC-10 — J-77: Regime × Setup × Pattern study byte-identical enrichment (existing figures untouched)

**Type:** api (backend integration)
**Preconditions:** `compute_event_study` and `compute_regime_setup_pattern_study` both callable; test fixtures covering both.
**Steps:**
1. Call `compute_event_study(...)` for a subject and capture the full payload (all figures, cells, n counts).
2. Call `compute_regime_setup_pattern_study(...)` for the same subject.
3. Re-call `compute_event_study(...)` again and compare to the pre-iter-20 baseline.
**Expected outcome:** The existing event-study figures (Factor Lab, Combination Lab, event study mean/median/hit-rate) are **byte-identical** before and after the enrichment is added.
**Pass criteria:** `as_of=None` and `as_of=<date>` event-study payloads match the pre-iter-20 committed assertion; enrichment is additive and does not mutate existing figures.

---

### TC-11 — J-77: Regime × Setup × Pattern study groups the enriched observation set correctly

**Type:** api (backend integration)
**Preconditions:** Seeded data with known regime/setup/pattern distributions; test fixture with a small fixed observation set.
**Steps:**
1. Manually construct a (regime, setup, pattern) combination (e.g., regime="Bull", setup="Oversold", pattern="Flag").
2. Fetch all enriched observations matching that combination from the live data.
3. Call `compute_regime_setup_pattern_study(...)` and extract the row for that combination.
4. Confirm the row's `n`, `mean`, `median`, `%positive`, `expectancy` match the manual grouping.
**Expected outcome:** The study correctly groups observations by (regime, setup, pattern) and computes correct statistics for each group.
**Pass criteria:** For a known combination, the row's `n` == manual count; `mean` computed over the matched observations is correct (within floating-point tolerance).

---

### TC-12 — J-77: Count-coherence — drill-down total equals published n (same-instant)

**Type:** api (backend integration + browser)
**Preconditions:** A (regime, setup, pattern) combination with known `n` > 0; `/research/samples` endpoint callable with the new cohort selector.
**Steps:**
1. Call `GET /api/research/regime-setup-pattern?subject=<ticker>&horizon=5&view=episodes&as_of=<date>` and extract a row with `n > min_sample`.
2. Record the row's published `n`.
3. Immediately call `GET /api/research/samples?subject=<ticker>&regime=<regime>&setup=<setup>&pattern=<pattern>&horizon=5&view=episodes&as_of=<date>` (the drill-down cohort selector).
4. Sum the `total` field from the response.
5. Compare the sum against the published `n`.
**Expected outcome:** The drill-down `total` equals the published row `n` exactly (same-instant, no drift).
**Pass criteria:** `drill_down_total == published_n` to the integer; both use the same observation set and membership filter; no intervening data changes.

---

### TC-13 — J-77: Low-sample combinations show NA + n (never fabricated)

**Type:** api (backend)
**Preconditions:** A (regime, setup, pattern) combination with `n < config.walk_forward.min_sample`.
**Steps:**
1. Call `compute_regime_setup_pattern_study(...)` or `GET /api/research/regime-setup-pattern?...`.
2. Inspect the row for that combination.
**Expected outcome:** The row shows `n`, but all statistic columns (mean, median, %positive, expectancy, risk-adjusted) are `null` / `"NA"`.
**Pass criteria:** Low-sample rows have visible `n` (e.g., "n=3") but all numeric figures are `null` / `"NA"`; no fabricated value; survivorship-bias label present.

---

### TC-14 — J-77: Endpoint `GET /api/research/regime-setup-pattern` returns 4xx on invalid inputs

**Type:** api (REST)
**Preconditions:** Backend on `http://localhost:8000`.
**Steps:**
1. `curl "/api/research/regime-setup-pattern?subject=UNKNOWN&..."` → expect `404` or `400` (no such subject).
2. `curl "/api/research/regime-setup-pattern?subject=AAPL&horizon=999&..."` → expect `400` (no such horizon in config).
3. `curl "/api/research/regime-setup-pattern?subject=AAPL&view=invalid&..."` → expect `400` (invalid view).
**Expected outcome:** Explicit 4xx errors for invalid inputs; never a silent empty `200` with `[]`.
**Pass criteria:** Status code is 400 or 404 (not 500); error message is descriptive.

---

### TC-15 — J-77: Regime/Setup/Pattern vocabularies are config-backed (no hardcoded lists)

**Type:** artifact (code review)
**Preconditions:** `apps/backend/app/engine/research.py`, `samples.py`, and tests.
**Steps:**
1. Grep for hardcoded regime, setup, or pattern literal lists (e.g., `["Bull", "Neutral", "Bear"]` or `["Oversold", "Neutral", ...]`).
2. Confirm all vocabulary values derive from `config.research` or are read from the `ScannerRun` / `ScannerResult` stored enumerations.
3. Verify no hardcoded list exists in serving or computing code.
**Expected outcome:** No hardcoded regime/setup/pattern lists in code; vocabularies are config-driven or read from canonical stored enums.
**Pass criteria:** Grep returns zero hardcoded lists; all values are sourced from `config.research` or the DB.

---

### TC-16 — J-77: Regime × Setup × Pattern study honors Episodes/Pooled toggle (J-63)

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; `/research` page with the new study section; Episodes/Pooled toggle visible.
**Steps:**
1. Navigate to `/research?asof=2026-05-28`.
2. Scroll to the new Regime × Setup × Pattern study section.
3. Select "Episodes" mode; record a row's statistics (e.g., regime="Bull", n=5, mean=0.015).
4. Toggle to "Pooled"; record the same row's statistics.
5. Confirm the figures differ (pooled may have a larger `n` and different stats due to multiple episodes per symbol).
**Expected outcome:** The study respects the Episodes/Pooled toggle; figures update correctly when the toggle changes.
**Pass criteria:** Toggle changes the study table figures; row counts and statistics reflect the selected mode.

---

### TC-17 — J-77: Regime × Setup × Pattern study honors As-of / All-history toggle (J-32)

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; `/research` page; As-of / All-history toggle visible.
**Steps:**
1. Navigate to `/research` at a historical date (e.g., `?asof=2026-05-28`).
2. Confirm the As-of / All-history toggle is set to "As-of" (default for the global control).
3. In the study table, record a row's `n`.
4. Toggle the global As-of switch to "All-history".
5. Confirm the study table updates; the same row's `n` likely increases (more snapshots included).
**Expected outcome:** The study respects the global As-of / All-history mode; figures filter correctly.
**Pass criteria:** Toggle changes the study table; row counts reflect the selected mode (as-of scoped ≤ larger all-history count).

---

### TC-18 — J-77: N= chip drills down to /research/samples in new tab

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; `/research` with study table visible.
**Steps:**
1. Navigate to `/research?asof=2026-05-28`.
2. In the Regime × Setup × Pattern study table, locate a row with `n > 0`.
3. Click the `N=X` chip (where X is the count).
4. Confirm a new browser tab opens and loads `/research/samples?regime=<regime>&setup=<setup>&pattern=<pattern>&horizon=<horizon>&asof=2026-05-28`.
5. Confirm the samples table shows the exact observations for that combination.
**Expected outcome:** Clicking the `N=` chip opens the drill-down in a new tab with the correct cohort selector params and `?asof` stamping.
**Pass criteria:** New tab opens with correct URL params; samples table loads the drill-down data; the total count matches the published `n`.

---

### TC-19 — J-72: Research labs load independently with per-section loading states

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; `/research` page.
**Steps:**
1. Navigate to `/research`.
2. Observe the page as it loads: each section (Factor Lab, Combination Lab, Setup & Pattern Lab, new Regime × Setup × Pattern study) should show its own skeleton/spinner.
3. Confirm that a slow Factor Lab query does NOT block the Combination Lab or event-study sections from becoming interactive.
**Expected outcome:** Each section loads independently with its own loading state; the page reaches interactive without a full-page blocking spinner.
**Pass criteria:** Skeleton loaders appear per-section (not page-wide); sections become interactive asynchronously (not all at once).

---

### TC-20 — Required-still-passing smoke: J-29 (Factor Lab figures untouched)

**Type:** api (backend integration)
**Preconditions:** Test fixture for J-29; baseline captures of Factor Lab output.
**Steps:**
1. Call `compute_factor_lab(...)` and compare the full payload against the pre-iter-20 baseline.
**Expected outcome:** Byte-identical figures and structure.
**Pass criteria:** All Factor Lab cells, n, mean, etc. match committed assertion.

---

### TC-21 — Required-still-passing smoke: J-63 (Event study Episodes/Pooled unchanged)

**Type:** api (backend integration)
**Preconditions:** Fixture with episode-collapse test.
**Steps:**
1. Call `compute_event_study(subject, view='episodes', ...)` and `compute_event_study(subject, view='pooled', ...)`.
2. Confirm the episode collapse is a pure in-memory grouping of the SAME stored rows (no recompute, no new query).
**Expected outcome:** Both views are byte-identical to pre-iter-20 baselines.
**Pass criteria:** Assertion passes; the collapse is unchanged.

---

### TC-22 — Required-still-passing smoke: J-05/J-06 (Leaderboard/Detail score coherence)

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; a historical date with complete data.
**Steps:**
1. Navigate to `/stocks?asof=2026-05-28` and find the top-ranked stock's score.
2. Click on that stock to open the Stock Detail page.
3. Confirm the score shown in the detail page matches the leaderboard score.
**Expected outcome:** Scores are identical (same source, single source of truth).
**Pass criteria:** Detail score == leaderboard score for the same ticker/date.

---

### TC-23 — Required-still-passing smoke: J-21 (Backtest reads the same stored forward_returns)

**Type:** browser
**Preconditions:** Frontend on `http://localhost:3000`; Backtest page accessible.
**Steps:**
1. Navigate to `/backtest?asof=2026-05-28` with a test symbol and strategy.
2. Confirm the forward returns shown in the backtest results match the `/stocks` leaderboard values for the same symbol/horizon/date.
**Expected outcome:** Backtest forward returns match leaderboard (same stored `forward_returns` table).
**Pass criteria:** Values are identical (no recompute, single source of truth).

---

### TC-24 — Required-still-passing smoke: J-51/J-64/J-65 (Samples count-coherence)

**Type:** api + browser
**Preconditions:** `/research/samples` endpoint and page.
**Steps:**
1. Call `GET /api/research/factor-lab?subject=<ticker>&as_of=2026-05-28` and record a decile's published `n`.
2. Click the `N=` chip on the Factor Lab to drill down to `/research/samples`.
3. Confirm the samples table `total` matches the published `n`.
**Expected outcome:** Count-coherence holds (published n == drill-down total).
**Pass criteria:** `total == published_n` (same-instant, no drift).

---

## Summary

**Total test cases:** 24
- **API tests:** 14 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-20, TC-21)
- **Browser tests:** 8 (TC-09, TC-16, TC-17, TC-18, TC-19, TC-22, TC-23, TC-24)
- **Artifact tests:** 2 (TC-08, TC-15)

All test cases are specific, reproducible, and grounded in the phase spec requirements. Tests cover the three target journeys (J-72, J-75, J-77), critical anti-goals (no lookahead, single source of truth, no recompute in read path, byte-identity, count-coherence), and required-still-passing journeys smoke tests.
