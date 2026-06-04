# goal-i_can_see_the_wealthy_future_forever-iter-18 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

On `/research` → Factor Lab, replace the perpetually-0/NA strict-AND **Combined** cohort with a **non-empty composite percentile-rank blend** (config-weighted, top config-quantile of the stored factor-value ranks), scaling to all catalog factors, while demoting the strict AND-intersection to a clearly-labelled secondary **Strict overlap (AND)** column — all read-only, downside-only risk-adjusted, no magic numbers, and with **zero added date state**.

## Test Cases

### TC-01 — Composite cohort non-empty & clears min_sample (default conditions)

**Type:** api
**Preconditions:** Backend running on :8000; DB seeded; `walk_forward.min_sample = 30`.

**Steps:**
1. `curl -s "http://localhost:8000/api/research/factor-combination?horizon=21"` (default conditions, no explicit condition params).
2. Inspect JSON for the `composite` cohort.

**Expected outcome:** Payload returns `baseline`, `singles[]`, `composite`, and `strict_overlap`. The `composite.stats.n` is populated and ≥ 30, with numeric `mean`, `median`, `hit_rate`, `risk_adjusted`.
**Pass criteria:** HTTP 200; `composite.stats.n >= 30` and `> 0`; `composite` numeric fields are non-null; `composite` distinct from `baseline` (different n or mean). No `combined` key present (clean rename).

---

### TC-02 — Composite scales to all catalog factors

**Type:** api
**Preconditions:** Backend running; `comb.max_conditions = 11` (= catalog factor count).

**Steps:**
1. Build a request with conditions for up to all 11 catalog factors (repeatable `condition` params at the raised cap).
2. `curl` the endpoint with these conditions + `horizon=21`.

**Expected outcome:** Endpoint accepts the up-to-cap condition count and returns a non-empty composite cohort.
**Pass criteria:** HTTP 200; `composite.stats.n > 0`; no condition-count 422 at or below `max_conditions=11`.

---

### TC-03 — Empty strict-overlap while composite populated (the headline bar-raise)

**Type:** api
**Preconditions:** Backend running. Use an opposing-extremes / membership-driven selection (per iter-11 lesson — NOT horizon length) that empties the AND-intersection.

**Steps:**
1. `curl` the endpoint with conditions chosen so the strict AND-intersection is empty (e.g. opposing top/bottom sides of the same factor, or many factors).
2. Inspect `composite` and `strict_overlap` in the same response.

**Expected outcome:** `strict_overlap` reports n=0 / NA (no fabricated 0), while `composite` is populated and non-empty.
**Pass criteria:** `strict_overlap.stats.n == 0` and its stat values are NA/null (not 0.0); `composite.stats.n > 0` in the SAME payload.

---

### TC-04 — Orientation correctness (top vs bottom side)

**Type:** api
**Preconditions:** Backend running. Monotone factor fixture available (covered in unit tests; spot-checkable via API on a single factor).

**Steps:**
1. Request a single-condition composite on a factor with `side=top`; note composite members.
2. Request the same factor with `side=bottom`; note composite members.

**Expected outcome:** `top` side composite selects the high-factor-value names; `bottom` selects the low-factor-value names (oriented by user side, not catalog direction/family).
**Pass criteria:** The two member sets are oriented oppositely (top-side cohort mean factor value > bottom-side cohort mean factor value).

---

### TC-05 — Downside-only risk-adjusted (never total vol)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl` the endpoint (default conditions).
2. Verify `risk_adjusted` for `composite` and `strict_overlap` cohorts equals mean / downside-deviation; NA when no downside or n<2.

**Expected outcome:** `risk_adjusted` uses downside deviation only; NA on no-downside / n<2 cohorts.
**Pass criteria:** For a populated cohort, `risk_adjusted ≈ mean / downside_deviation` (NOT mean / total_stdev); for a cohort with no downside or n<2, `risk_adjusted` is NA/null.

---

### TC-06 — Echoed composite metadata (quantile + weighting) for honest UI labelling

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl` the endpoint.
2. Inspect payload for echoed composite quantile (key/label/fraction) and weighting scheme.

**Expected outcome:** Payload echoes the resolved composite quantile and weighting (equal-weight default) so the UI can label the blend transparently.
**Pass criteria:** Payload contains composite quantile metadata (e.g. `{key,label,fraction}`) and a weighting scheme field with a non-null value.

---

### TC-07 — Error cases: unknown factor/side/quantile, count overflow, bad horizon, no data

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl` with an unknown factor → expect 422.
2. `curl` with an invalid `side` → expect 422.
3. `curl` with condition count > `max_conditions` (>11) → expect 422.
4. `curl` with an invalid `horizon` → expect 422.
5. (If reproducible) no-price-data scenario → expect 503.

**Expected outcome:** Each malformed request returns the documented status; no fabricated/200 fallback.
**Pass criteria:** 422 for unknown factor/side, over-cap count, and invalid horizon; 503 on no-price-data; no 500s.

---

### TC-08 — Config validation raises ConfigError at boot

**Type:** artifact
**Preconditions:** Test suite / a temporary config with a bad `composite` block.

**Steps:**
1. Set `composite.quantile` to a value that is NOT a real `quantiles` key → boot config.
2. Set an invalid weighting scheme / non-positive default weight → boot config.
3. Confirm existing `1 ≤ min_conditions ≤ max_conditions`, unique-quantile-key, default-conditions cross-checks still raise.

**Expected outcome:** Each invalid config raises a loud `ConfigError` at boot — no silent default.
**Pass criteria:** `pytest` config-validation cases for bad `composite.quantile`, bad weighting, and existing cross-checks all raise `ConfigError`.

---

### TC-09 — Config-driven cohort size (no hard-coded fraction/cap)

**Type:** artifact
**Preconditions:** Backend test harness.

**Steps:**
1. Change `composite.quantile` in config (e.g. quintile → decile).
2. Recompute the composite cohort.

**Expected outcome:** The composite cohort `n` re-points with the config quantile — proving the fraction/cap is config-sourced.
**Pass criteria:** Different `composite.quantile` yields a different composite `n`; `test_no_magic_numbers` still passes (no decile/quantile/weight/cap literal in `research.py`).

---

### TC-10 — Read-only keystone (no recompute / no scoring path)

**Type:** artifact
**Preconditions:** Backend test harness with patch-to-raise on side-effecting functions.

**Steps:**
1. Run the extended `test_combination_is_read_only_no_scoring_or_return_or_pattern_call` covering the composite path.
2. Git-verify the diff does NOT touch `scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/`forward_testing.py` math or the snapshot/serving path.

**Expected outcome:** The composite path calls no `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime`; only SELECT-only `_combination_observations`. No DB regen.
**Pass criteria:** Patch-to-raise test passes (no side-effecting call); diff is clean of scoring/snapshot math files (J-06/J-07 byte-identical).

---

### TC-11 — Cohort algebra invariants

**Type:** artifact
**Preconditions:** Backend test harness.

**Steps:**
1. Run cohort-algebra assertions: `composite ⊆ baseline`; `strict_overlap ⊆ each single`; `baseline.n == pool_n`.

**Expected outcome:** Membership relationships hold.
**Pass criteria:** All three subset/equality assertions pass.

---

### TC-12 — Browser: Combination Lab default render (composite populated + strict-overlap row)

**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000. Chrome MCP (exclusive — serialize vs other Chrome users). Evidence under `reports/qa/<phase>-evidence/`, de-dup by sha256.

**Steps:**
1. Navigate to `http://localhost:3000/research`.
2. Locate the "Multi-factor combination cohort" section (`data-testid="combination-table"`).
3. Read the **Combined (composite)** row and **Strict overlap (AND)** row via DOM.

**Expected outcome:** Row order Baseline → singles → **Combined (composite)** (emphasized) → **Strict overlap (AND)** (secondary, muted). Composite row shows numeric n ≥ 30, mean, median, hit-rate, risk-adjusted; distinct from Baseline.
**Pass criteria:** Composite row DOM values are numeric and n ≥ 30 distinct from Baseline; strict-overlap row renders; survivorship-bias + descriptive-not-predictive labels present. Screenshot saved.

---

### TC-13 — Browser: add conditions up to (near) all catalog factors → composite stays non-empty

**Type:** browser
**Preconditions:** As TC-12; condition add/remove control present.

**Steps:**
1. On the Combination Lab, click "Add condition" repeatedly up to the payload-driven cap (toward all 11 catalog factors).
2. Verify the add control disables only at `data.max_conditions` (no hard-coded UI cap).
3. Read the composite row n.

**Expected outcome:** UI allows adding up to all catalog factors; composite cohort remains non-empty.
**Pass criteria:** Add control enabled up to 11 conditions, disabled at the cap; composite row n > 0 (DOM-asserted). Screenshot saved.

---

### TC-14 — Browser: empty-strict-overlap selection (composite populated AND strict-overlap NA in same shot)

**Type:** browser
**Preconditions:** As TC-12. Use a membership-driven empty-overlap selection (opposing-extremes / many-factor) per iter-11 lesson — never horizon length.

**Steps:**
1. Configure conditions so the strict AND-intersection is empty.
2. Read both the composite row and strict-overlap row in the same view.

**Expected outcome:** Composite row populated (n > 0); strict-overlap row shows NA + n (no fabricated 0) in the same shot.
**Pass criteria:** Single screenshot + DOM assertion: composite n > 0 AND strict-overlap = NA with its n displayed. Screenshot saved (distinct sha256).

---

### TC-15 — Browser: J-18 re-verify — global as-of leaves lab byte-identical, zero as_of requests, one date select

**Type:** browser
**Preconditions:** As TC-12. Network spy enabled. Use native-setter + bubbling change event for the global as-of select (per `react-controlled-select-needs-native-setter`); in-app toggle, NOT hard reload (iter-1 lesson).

**Steps:**
1. Capture the Combination Lab region (sha256 of screenshot / DOM).
2. Toggle the global as-of control in-app.
3. Re-capture the Combination Lab region (sha256).
4. Inspect network log for any `/api/research/*?as_of=` requests.
5. Count date `<select>` elements on `/research`.

**Expected outcome:** Lab is byte-identical across the toggle; no `as_of` request hits any `/api/research/*`; exactly one date selector on the page (none added on `/research`).
**Pass criteria:** Before/after sha256 of the lab region match (byte-identical); zero `/api/research/*?as_of=` network requests; exactly one date `<select>` on the page.

---

### TC-16 — Browser: spot-check J-25 / J-27 / J-30 still render and re-point

**Type:** browser
**Preconditions:** As TC-12.

**Steps:**
1. On `/research` above the Combination Lab, change the factor selection → verify J-25 decile/rank-IC re-points.
2. Verify J-27 by-regime split renders.
3. Verify J-30 volatility family renders.

**Expected outcome:** All three required-still-passing journeys render and re-point on factor change.
**Pass criteria:** Decile/rank-IC values change on factor change; regime split and volatility family sections present with data. Screenshot saved.

---

### TC-17 — Frontend type/build + full backend pytest (no regressions)

**Type:** artifact
**Preconditions:** Repo clean; run backend pytest ONCE (per backend-test-suite-runtime ~14 min — no concurrent invocations).

**Steps:**
1. `cd apps/frontend && npm run build` — typecheck `FactorCombinationResponse` (`composite` + `strict_overlap`, no `combined`).
2. Run full backend pytest once.

**Expected outcome:** Frontend build typechecks; full backend suite green.
**Pass criteria:** `npm run build` exits 0; pytest reports 0 failures.

---

### TC-18 — Dev handoff artifact exists

**Type:** artifact
**Preconditions:** Implementation complete.

**Steps:**
1. Check `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-18-dev.md` exists and notes the composite is a deterministic rank-blend of stored values (NOT a recomputation or fitted/ML model).

**Expected outcome:** Handoff present with the rank-blend clarification.
**Pass criteria:** File exists and contains the descriptive-not-predictive / no-recompute note.

---

## Summary

Total test cases: 18
- API tests: 7 (TC-01 … TC-07)
- Browser tests: 5 (TC-12 … TC-16)
- Artifact checks: 6 (TC-08, TC-09, TC-10, TC-11, TC-17, TC-18)

Coverage maps to DEFINITION OF DONE: composite non-empty/clears min_sample (TC-01), scales to all factors (TC-02/TC-13), headline empty-strict-overlap bar-raise (TC-03/TC-14), J-18 zero date state (TC-15), required-still-passing journeys (TC-16), anti-goal guards — read-only/downside-only/no-magic-numbers/no-fabrication (TC-05, TC-09, TC-10), config validation (TC-08), no regressions (TC-17), and handoff (TC-18).
