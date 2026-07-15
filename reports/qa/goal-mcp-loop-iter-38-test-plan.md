# Goal Iteration 38 Functional Test Plan

**Phase:** goal-mcp-loop-iter-38
**Journey:** J-23 (watchlist concentration X-ray)
**Date:** 2026-07-15
**Frontend Present:** yes

## Phase Goal

Add a descriptive **concentration X-ray** section to the `/watchlist` page that discloses correlation structure, effective independent bets count, sector/theme concentration, and cluster groupings — computed engine-side, served additively via `GET /api/watchlist`, and re-read verbatim by the UI (zero browser-side recompute).

## Test Cases

### TC-01 — ENB/Correlation Helper: Two Correlated + One Independent Series

**Type:** api
**Preconditions:** Backend is running; the new `app.engine.concentration` module is deployed.

**Steps:**
1. Create a synthetic fixture: two series that are perfectly correlated (r=1.0), one series independent (r≈0 to both).
2. Call `effective_number_of_bets(correlation_matrix)` with the 3×3 matrix from the fixture.
3. Verify the result against the expected formula: `(Σλ)²/Σλ²` where λ are eigenvalues.

**Expected outcome:** ENB ≈ 2.0 (the two correlated names count as one independent bet; the third independent name is the second bet).
**Pass criteria:** ENB computed value is within 0.01 of 2.0; clusters group the two correlated names together and isolate the independent one.

---

### TC-02 — Pairwise Correlation Spot-Check

**Type:** api
**Preconditions:** Backend is running; watchlist contains at least 2 names with overlapping price history.

**Steps:**
1. Call `build_xray_payload(session, cfg, tickers=['AAPL', 'MSFT'], asof=<seed_date>)` for two highly-correlated tech names.
2. Extract the pairwise correlation matrix element for AAPL-MSFT.
3. Independently compute Pearson correlation over the same `corr_window_days` window using an offline script (e.g., pandas).
4. Compare the two values.

**Expected outcome:** The two correlation values match to at least 4 decimal places.
**Pass criteria:** |engine_corr - offline_corr| < 0.0001.

---

### TC-03 — Undefined / Zero-Variance Pair Renders NA

**Type:** api
**Preconditions:** Backend is running; watchlist contains at least one name with zero-variance returns.

**Steps:**
1. Create or select a name with identical close prices over the window (zero variance).
2. Call `build_xray_payload()` with a pair involving this name.
3. Inspect the correlation matrix for that pair.

**Expected outcome:** The matrix cell is `None` / `null`, not a fabricated 0 or NaN.
**Pass criteria:** `xray.correlation_matrix[i][j] === null` for the zero-variance pair.

---

### TC-04 — Short-Overlap Member Renders NA in Matrix

**Type:** api
**Preconditions:** Backend running; watchlist contains a name with limited price history overlapping the correlation window.

**Steps:**
1. Add a name with < `min_overlap_days` bars overlapping the correlation window (e.g., a recent IPO with only 30 bars when `min_overlap_days=60`).
2. Call `build_xray_payload()`.
3. Inspect the correlation matrix for rows/columns corresponding to this name.

**Expected outcome:** All correlation values for this name are `null` (honest NA, not fabricated values).
**Pass criteria:** `xray.correlation_matrix[short_name_idx]` contains all null values.

---

### TC-05 — Empty or Single-Name Watchlist Returns HTTP 200 with Honest Empty State

**Type:** api
**Preconditions:** Backend running; watchlist is empty (0 names) or contains only 1 name.

**Steps:**
1. Call `GET /api/watchlist` with an empty watchlist.
2. Verify the HTTP status and the `xray` field structure.
3. Repeat with a single-name watchlist.

**Expected outcome:** HTTP 200; `xray` field is present but renders an honest empty/insufficient state (no crash, no 500).
**Pass criteria:** Status is 200; response is valid JSON; `xray` field exists; no server error in logs.

---

### TC-06 — GET /api/Watchlist: Additive Field, Existing Shape Unchanged

**Type:** api
**Preconditions:** Backend running; existing watchlist API tests pass before iteration.

**Steps:**
1. Fetch `GET /api/watchlist` with a populated watchlist.
2. Verify the response includes `asof_date` and `entries[]` fields unchanged.
3. Verify a new `xray` field is present and additive.
4. Run existing watchlist API tests.

**Expected outcome:** Existing `entries[]` and `asof_date` shape is byte-identical pre/post change; no regression.
**Pass criteria:** Existing watchlist tests pass; new `xray` field is present; `entries[]` count and structure unchanged.

---

### TC-07 — Null Sector Bucketed as "Unassigned" in Concentration

**Type:** api
**Preconditions:** Backend running; watchlist contains at least one name with `sector=null`.

**Steps:**
1. Call `build_xray_payload()` for a watchlist including a null-sector name.
2. Inspect the sector concentration bars in the `xray.sector_concentration`.
3. Verify an "Unassigned" bucket appears.

**Expected outcome:** The null-sector name contributes to an "Unassigned" sector group, not dropped or crashed.
**Pass criteria:** `xray.sector_concentration` includes a "Unassigned" entry; count is correct.

---

### TC-08 — Correlation-Threshold Clusters Deterministic

**Type:** api
**Preconditions:** Backend running; watchlist with known correlation structure.

**Steps:**
1. Call `build_xray_payload(asof=<seed_date>)` twice with identical inputs.
2. Verify the cluster groupings are identical.

**Expected outcome:** Deterministic clustering — same seed/as-of always produces the same cluster assignments.
**Pass criteria:** Both calls produce byte-identical `xray.clusters` arrays.

---

### TC-09 — One Canonical ENB Implementation Only

**Type:** artifact
**Preconditions:** Full codebase available.

**Steps:**
1. Run: `grep -r "effective_number_of_bets\|ENB" apps/backend --include="*.py" | grep -v test | grep -v __pycache__`
2. Verify exactly one implementation of `effective_number_of_bets` exists.

**Expected outcome:** Only `app.engine.concentration.effective_number_of_bets()` found; no duplicate implementations.
**Pass criteria:** `grep` output shows one match in production code.

---

### TC-10 — No Proven-Language or Advice-Language in Payload or UI

**Type:** artifact
**Preconditions:** Full codebase available; frontend compiled.

**Steps:**
1. Search backend for "Proven", "trim", "add", "reduce", "rebalance" in the X-ray composer and payload.
2. Search frontend for the same language in the X-ray section template.

**Expected outcome:** None of these words appear in X-ray code paths.
**Pass criteria:** `grep` returns no matches in relevant files; rendered section shows only descriptive language.

---

### TC-11 — Browser: X-Ray Renders on Watchlist with Multiple Correlated Names

**Type:** browser
**Preconditions:** Frontend running; backend running; user authenticated; watchlist populated with several correlated and unrelated names.

**Steps:**
1. Navigate to `/watchlist`.
2. Scroll to the X-ray section.
3. Verify the pairwise correlation matrix heatmap is rendered with cells colored appropriately.
4. Verify cluster badges are shown.
5. Verify sector/theme concentration bars are rendered.
6. Verify the "effective independent bets ≈ N.N (over the last W trading days)" headline is visible.

**Expected outcome:** All X-ray components are rendered and readable on the page.
**Pass criteria:** Matrix, clusters, concentration bars, and ENB headline all visible; no console errors; no missing data cells.

---

### TC-12 — Browser: Spot-Checked Pair Correlation Matches Offline Computation

**Type:** browser
**Preconditions:** Frontend running; `/watchlist` X-ray rendered; watchlist contains two known correlated names (e.g., AAPL, MSFT).

**Steps:**
1. Read the correlation value from the rendered matrix for AAPL-MSFT.
2. Independently compute Pearson correlation offline for the same window.
3. Compare.

**Expected outcome:** The rendered value matches the offline computation.
**Pass criteria:** |rendered_corr - offline_corr| < 0.0001.

---

### TC-13 — Browser: Short-History Name Renders NA in Matrix

**Type:** browser
**Preconditions:** Frontend running; `/watchlist` X-ray rendered; watchlist includes a short-history name (recent IPO with < min_overlap_days history).

**Steps:**
1. Locate the short-history name's row/column in the rendered correlation matrix.
2. Verify the cells are marked as "NA" or "--" visually (not a color-coded number).

**Expected outcome:** Short-history name's correlation cells are visibly marked NA, not a fabricated correlation color.
**Pass criteria:** Visual inspection shows honest NA marking (e.g., crossed hatch, muted gray, explicit "NA" text); no false-positive color.

---

### TC-14 — Browser: No Browser-Side Recompute

**Type:** browser
**Preconditions:** Frontend running; network inspection tools available; `/watchlist` X-ray rendered.

**Steps:**
1. Open browser DevTools Network tab.
2. Check whether the page makes a second request to `/api/watchlist` or any compute endpoint.
3. Inspect the page's JavaScript for any correlation/ENB calculation logic.

**Expected outcome:** Only one `GET /api/watchlist` call; no secondary compute calls; no client-side ENB/correlation formula in the JS.
**Pass criteria:** Single network request; no redundant API calls; code inspection shows X-ray section consumes `xray` payload verbatim.

---

### TC-15 — Browser: Existing Watchlist Controls Still Work

**Type:** browser
**Preconditions:** Frontend running; `/watchlist` page with existing add/remove/reason controls.

**Steps:**
1. Add a name to the watchlist via the existing UI control.
2. Remove a name via the existing control.
3. Edit a name's reason via the existing control.
4. Verify the watchlist re-fetches and X-ray updates accordingly.

**Expected outcome:** Existing controls are unaffected; X-ray updates when watchlist changes.
**Pass criteria:** Add/remove/reason controls respond; no error messages; X-ray re-computes on list change.

---

### TC-16 — Config: Default xray.corr_window_days Set

**Type:** artifact
**Preconditions:** `config.yaml` and `app/config.py` available.

**Steps:**
1. Check `config.yaml` for a `watchlist.xray.corr_window_days` key with a default value.
2. Check `app/config.py` for `WatchlistXrayCfg` with a typed `corr_window_days` field and default factory.

**Expected outcome:** Configuration is typed, has sensible defaults (~126 days), and does not require user editing.
**Pass criteria:** `WatchlistCfg` and `WatchlistXrayCfg` classes exist; default values are set; `Config` includes `watchlist` as a default-populated field.

---

### TC-17 — J-23 Required-Still-Passing: J-01, J-02, J-03, J-05, J-10, J-13, J-20 Green

**Type:** browser
**Preconditions:** Full system running; all existing journeys set up.

**Steps:**
1. Execute the golden-script deterministic replay or run lean verify pass for each required journey: J-01 (evidence badges on scores), J-02 (drill-into evidence), J-03 (unproven/noise marked), J-05 (evidence ledger audit), J-10 (deep price history honest), J-13 (data manager 548-symbol universe), J-20 (daily preflight verdict).
2. Record pass/fail for each.

**Expected outcome:** All seven journeys remain passing (regression-free).
**Pass criteria:** J-01/J-02/J-03/J-05/J-10/J-13/J-20 all PASS in this iteration's replay run.

---

### TC-18 — Ledger Byte-Identity: No Evidence Claim Registered

**Type:** artifact
**Preconditions:** Phase complete; `certified-claims.jsonl` and `staging-ledger.jsonl` available.

**Steps:**
1. Verify `certified-claims.jsonl` is byte-identical pre/post iteration (no new rows).
2. Verify `staging-ledger.jsonl` is byte-identical pre/post iteration.
3. Verify no `## Evidence Claim` heading appears in any iteration artifact.
4. Verify the canonical Bonferroni divisor remains 8.

**Expected outcome:** Both ledgers unchanged; no Evidence Claim submitted; divisor stays 8.
**Pass criteria:** `diff certified-claims.jsonl` returns no changes; `diff staging-ledger.jsonl` returns no changes; grep finds no `## Evidence Claim` in phase artifacts.

---

## Summary

**Total test cases:** 18
- **API tests:** 9 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09)
- **Browser tests:** 6 (TC-11, TC-12, TC-13, TC-14, TC-15, TC-17)
- **Artifact checks:** 3 (TC-10, TC-16, TC-18)

---

## Key Test Scenarios Mapped to Definition of Done

| DoD Item | Test Case(s) |
|----------|-------------|
| X-ray renders correlation, clusters, concentration, ENB | TC-11 |
| Spot-checked correlation matches offline computation | TC-02, TC-12 |
| Short-overlap name renders NA | TC-04, TC-13 |
| GET /api/watchlist additive, existing shape unchanged | TC-06 |
| ENB one canonical implementation | TC-09 |
| No proven-language, no advice-language | TC-10 |
| Null sector handled as "Unassigned" | TC-07 |
| Determinism (same seed = same X-ray) | TC-08 |
| J-01..J-20 required journeys pass | TC-17 |
| No Evidence Claim registered, ledger byte-identical | TC-18 |
| Existing watchlist controls unchanged | TC-15 |
| Config typed, defaults populated | TC-16 |
| Empty/1-name watchlist 200, no crash | TC-05 |
