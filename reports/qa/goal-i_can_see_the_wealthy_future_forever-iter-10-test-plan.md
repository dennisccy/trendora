# goal-i_can_see_the_wealthy_future_forever-iter-10 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Stand up the **Research** sidebar home (`/research`) with its first lab — the **Factor Lab** — so a user picks a factor + a forward horizon and reads a read-only **decile table (D1…D10)** of mean forward return plus a downside-risk-adjusted column (each with `n`) and the factor's **rank-IC**, all derived once from already-stored per-observation forward returns ⋈ stored factor values (no recompute), with honest NA on low samples and a survivorship-bias label.

## Test Cases

### TC-01 — Factor Lab endpoint returns full payload (default factor/horizon)

**Type:** api
**Preconditions:** Backend running on :8000; seed DB has `scanner_results` + `forward_returns`.

**Steps:**
1. `curl -s -w "\n%{http_code}" "http://localhost:8000/api/research/factor-lab"`

**Expected outcome:** `200`; JSON has `factor`, `horizon` (= `walk_forward.default_horizon`), `factors` (array ≥5), `horizons`, `default_horizon`, `min_sample`, `survivorship_bias` (string), `n_total`, `deciles` (array), `rank_ic: {value, n}`. `deciles[*]` each have `decile, factor_min, factor_max, mean_return, risk_adjusted, n`.
**Pass criteria:** Status 200 and every listed field present with correct types; `factor` equals first catalog factor key; `horizon` equals config default.

---

### TC-02 — Factor and horizon query params re-point the table

**Type:** api
**Preconditions:** Backend running; ≥2 catalog factors and ≥2 horizons configured.

**Steps:**
1. `curl -s "http://localhost:8000/api/research/factor-lab?factor=<2nd catalog key>&horizon=<2nd horizon>"`

**Expected outcome:** `200`; `factor` and `horizon` echo the requested values; deciles/rank_ic reflect that factor/horizon.
**Pass criteria:** Status 200; `factor` and `horizon` in response equal the requested params (no fabricated fallback to defaults).

---

### TC-03 — Unknown factor → 422

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/research/factor-lab?factor=__nope__"`

**Expected outcome:** `422` (no fabricated factor).
**Pass criteria:** HTTP status == 422.

---

### TC-04 — Horizon not in walk_forward.horizons → 422

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/research/factor-lab?horizon=99999"`

**Expected outcome:** `422`.
**Pass criteria:** HTTP status == 422.

---

### TC-05 — No price data → 503 (mirror system_health)

**Type:** api
**Preconditions:** Code path verified against an empty-price-data condition (test DB or unit test); mirrors `system_health.py`.

**Steps:**
1. In the backend test suite, invoke the endpoint with no price data present and assert the response.

**Expected outcome:** `503`; no fabricated decile/IC payload.
**Pass criteria:** Status 503 when no price data exists at all.

---

### TC-06 — Read-only keystone (patch-to-raise)

**Type:** artifact
**Preconditions:** `apps/backend/tests/test_research.py` exists.

**Steps:**
1. Inspect the test that monkeypatches `run_scan` / `score_stocks` / `forward_return` / `detect_vcp` (+ new detectors) to raise, then calls `compute_factor_lab`.
2. Confirm test passes in the suite run (see TC-15).
3. Grep `apps/backend/app/engine/research.py`: confirm it calls none of `run_scan`, `score_stocks`, `backfill`, `forward_return`, `detect_`, and issues only SELECTs against `ForwardReturn` + `ScannerResult`.

**Expected outcome:** `compute_factor_lab` returns a full payload with the scoring/return/detect functions patched to raise; source contains no scoring/return/bucket math calls or writes.
**Pass criteria:** Keystone test passes AND source grep confirms SELECT-only (no forbidden call). Both required.

---

### TC-07 — Decile math is exact and monotone

**Type:** artifact
**Preconditions:** Synthetic stored dataset test in `test_research.py`.

**Steps:**
1. Inspect/confirm a test with known factor values + returns asserting exact decile membership, `mean_return`, and `n` per decile.
2. Confirm a monotone factor yields monotone decile means.

**Expected outcome:** Asserted decile membership/means/n match hand-computed values; monotone input → monotone decile means.
**Pass criteria:** Test passes with exact-value assertions (not approximate/ranges only).

---

### TC-08 — Rank-IC exact (Spearman)

**Type:** artifact
**Preconditions:** Test in `test_research.py`.

**Steps:**
1. Confirm assertions: perfectly monotone pairs → `value == 1.0`; perfectly inverse → `-1.0`; a known mixed set → its known value; `n < 2` or zero rank-variance → `value is None`.

**Expected outcome:** All four rank-IC cases assert exact values / None.
**Pass criteria:** Test passes all four assertions.

---

### TC-09 — Risk-adjusted is downside-only

**Type:** artifact
**Preconditions:** Test in `test_research.py`; helper `_downside_deviation` exists.

**Steps:**
1. Confirm a symmetric up/down cohort computes `risk_adjusted` from the downside leg only (`downside_deviation = sqrt(mean(min(r,0)**2))`).
2. Confirm an all-non-negative cohort → `downside_deviation == 0` → `risk_adjusted is None` (NOT a large total-vol number).
3. Grep source: `_downside_deviation` does NOT reuse `forward_testing`'s total-`stdev` helper.

**Expected outcome:** Downside-only math; `None` on zero downside or `n < 2`; no total-stdev reuse.
**Pass criteria:** Test passes AND source confirms a dedicated downside helper (anti-goal: must not conflate up/down volatility).

---

### TC-10 — NA honesty (no fabricated rows)

**Type:** artifact
**Preconditions:** Test in `test_research.py`.

**Steps:**
1. Confirm factor-NULL observations are EXCLUDED (never bucketed).
2. Confirm a decile with `n < min_sample` reports its `n` + low-sample flag.
3. Confirm a too-few-post-bars horizon → honest NA rows; an all-NA factor → empty/NA table with `n_total == 0` (no fabricated rows).

**Expected outcome:** Low-sample/NA surfaced explicitly with `n`; never blank, never fabricated.
**Pass criteria:** Test passes all NA-honesty assertions.

---

### TC-11 — Consistency invariant (read-only slice)

**Type:** artifact
**Preconditions:** Test in `test_research.py`.

**Steps:**
1. Confirm: for a never-NULL typed-column factor (e.g. `leadership_score`), the pooled mean of all factor-lab observations at horizon `h` equals `compute_forward_aggregates(session, h).overall["mean_return"]`.

**Expected outcome:** Pooled lab mean == aggregates overall mean (same stored observation set).
**Pass criteria:** Invariant test passes — proving the lab reads the same pool, not a second computation.

---

### TC-12 — Config-driven catalog + no magic numbers

**Type:** artifact
**Preconditions:** `config.yaml` `research.factor_lab` block; `ResearchCfg`/`FactorLabCfg` in `config.py`; `test_research.py` + `test_no_magic_numbers.py`.

**Steps:**
1. Confirm `config.yaml` has `research.factor_lab: {deciles: 10, factors: [≥5 rows]}` including a volatility-family factor (`atr_pct`); each row `{key, label, family, direction, source}`.
2. Confirm a test adds a `factors` row and it appears in catalog + endpoint with NO code change.
3. Confirm `deciles` integer is registered in `test_no_magic_numbers.py`.

**Expected outcome:** Decile count + factor catalog come from config; adding a factor needs no code change.
**Pass criteria:** Config block present with ≥5 factors incl. `atr_pct`; config-driven test passes.

---

### TC-13 — Bad config raises ConfigError at boot

**Type:** artifact
**Preconditions:** Validation tests in `test_config.py`.

**Steps:**
1. Confirm tests: `deciles <= 1` → `ConfigError`; duplicate factor `key` → `ConfigError`; unresolvable factor `source` (bad typed column or `<block>.components.<name>.raw` with unknown name) → `ConfigError`.

**Expected outcome:** Each bad config raises `ConfigError` loudly at load — never a silent default.
**Pass criteria:** All three validation tests pass.

---

### TC-14 — Required `research` config block added to all Config fixtures

**Type:** artifact
**Preconditions:** `research` is a required `Config` field.

**Steps:**
1. Grep test fixtures building a full Config dict (`test_config.py` MINIMAL_VALID, `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, others) and confirm each adds the `research` block.

**Expected outcome:** No fixture omits the now-required `research` block.
**Pass criteria:** Full suite has no Config-construction failures attributable to a missing `research` block (see TC-15).

---

### TC-15 — Full backend test suite green

**Type:** artifact
**Preconditions:** Backend deps installed. (Full pytest ~14 min; do not run two pytest invocations concurrently.)

**Steps:**
1. Run the project test command (per `.claude/project-template.md`), capturing stdout+stderr to `reports/qa/<phase>-test.log`.

**Expected outcome:** All tests pass, including new `test_research.py` + `test_api_research.py`; no regressions.
**Pass criteria:** Exit code 0; 0 failures / 0 errors. Record exact pass/fail counts.

---

### TC-16 — Frontend build typechecks

**Type:** artifact
**Preconditions:** `apps/frontend` deps installed.

**Steps:**
1. `cd apps/frontend && npm run build`

**Expected outcome:** Build succeeds; `/research` route typechecks along with all existing routes.
**Pass criteria:** Build exits 0 with no type errors.

---

### TC-17 — Research is discoverable from the sidebar (≤2 clicks)

**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000.

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. Locate the sidebar **Research** NavItem; click it.
3. Assert URL is `/research` and the Factor Lab heading renders.
4. Screenshot → `reports/qa/<phase>-evidence/TC-17-research-nav.png`.

**Expected outcome:** Sidebar shows **Research**; one click loads `/research` Factor Lab.
**Pass criteria:** Sidebar entry present; ≤2 clicks reach `/research`; Factor Lab content visible. Assert live DOM/URL before capture.

---

### TC-18 — Factor Lab renders decile table + rank-IC; dropdown is config-driven

**Type:** browser
**Preconditions:** `/research` loaded; backend serving the catalog.

**Steps:**
1. On `/research`, confirm a D1…D10 decile table with columns: mean forward return (raw), risk-adjusted (downside), and `n` per decile.
2. Confirm a rank-IC readout: numeric value with sign + `n`.
3. Open the factor dropdown; DOM-assert its options match the server `factors` catalog (fetch `/api/research/factor-lab` and compare keys/labels) — NOT a hardcoded list.
4. Screenshot → `reports/qa/<phase>-evidence/TC-18-factor-lab.png`.

**Expected outcome:** Decile table + rank-IC render for the default factor/horizon; dropdown options equal the server catalog.
**Pass criteria:** Table (10 rows or honest NA rows), risk-adjusted column, and rank-IC all visible; dropdown option set == server `factors` keys/labels.

---

### TC-19 — Changing factor and horizon re-points table + IC (server values)

**Type:** browser
**Preconditions:** `/research` loaded; ≥2 factors + ≥2 horizons.

**Steps:**
1. Capture the current decile values + rank-IC (DOM read).
2. Select a different factor; assert ≥1 value/label changes and network call hits `/api/research/factor-lab?factor=...`.
3. Select a different horizon; assert ≥1 value/label changes and network call includes `horizon=...`.
4. Screenshots (distinct before/after) → `reports/qa/<phase>-evidence/TC-19-*.png`.

**Expected outcome:** Table + rank-IC update from server values on factor/horizon change; no client-side recompute.
**Pass criteria:** ≥1 DOM value/label changes per control AND a matching network request observed; before/after grounded on distinct shots + DOM assertion (not one pair).

---

### TC-20 — Low-sample decile shows NA + n; honesty labels present

**Type:** browser
**Preconditions:** `/research` loaded; a horizon (e.g. 60) yields a low-sample decile.

**Steps:**
1. Select a horizon expected to produce a low-sample/NA decile.
2. Assert that decile cell renders explicit **"NA" + `n`** (never blank, never a fabricated number).
3. Assert the survivorship-bias, "universe-relative", and "descriptive, not predictive" labels are visible (survivorship label verbatim from payload).
4. Screenshot → `reports/qa/<phase>-evidence/TC-20-na-honesty.png`.

**Expected outcome:** Low-sample cell = NA + n; all honesty labels present.
**Pass criteria:** NA + n rendered for the low-sample cell; all three labels visible.

---

### TC-21 — J-18 regression: `/research` has NO date selector

**Type:** browser
**Preconditions:** `/research` loaded.

**Steps:**
1. Inspect the `/research` DOM for any as-of/date selector control.
2. Confirm ONLY factor + horizon selectors exist.
3. Screenshot → `reports/qa/<phase>-evidence/TC-21-no-date-control.png`.

**Expected outcome:** No date/as-of control on `/research`; only factor + horizon selectors.
**Pass criteria:** Zero date-selector elements found; exactly the factor + horizon controls present (single-date-selector anti-goal preserved).

---

### TC-22 — Regression: J-09 System Health + J-01 dashboard/sidebar still render

**Type:** browser
**Preconditions:** Frontend + backend running.

**Steps:**
1. Navigate to `/system-health`; confirm its by-bucket / excess / control-group evidence still renders.
2. Navigate to `/`; confirm the dashboard + the full sidebar (incl. new **Research** item) render.
3. Screenshots → `reports/qa/<phase>-evidence/TC-22-*.png`.

**Expected outcome:** System Health unchanged; dashboard + full sidebar render with the new Research entry.
**Pass criteria:** Both pages render their existing content without regression; sidebar shows all prior items plus Research.

---

## Summary

Total test cases: 22
- API tests: 4 (TC-01, TC-02, TC-03, TC-04)
- Browser tests: 6 (TC-17, TC-18, TC-19, TC-20, TC-21, TC-22)
- Artifact checks: 12 (TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16)

**Notes for QA execution:**
- Serialize Chrome access with the browser-qa-agent (one vacates before the other captures); save evidence under `reports/qa/<phase>-evidence/` and de-dup screenshots by sha256 (iter-6 lesson).
- Verify-by-source: confirm the read-only seam directly in `app/engine/research.py` (SELECT-only; no scoring/return/factor call). Full-depth iters here have sometimes produced no `status.json`/auditor handoff — do not block on or fabricate those artifacts.
- Full backend pytest is ~14 min; do not run two pytest invocations concurrently.
