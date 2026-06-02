# goal-i_can_see_the_wealthy_future_forever-iter-12 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

On the Factor Lab (`/research`), the user can compose a 2–3 condition multi-factor (AND) cohort and read its forward-return stats (mean / median / hit-rate / downside-risk-adjusted / n) side-by-side against the unconditional baseline and each single-factor cohort — derived once, read-only, from already-stored forward returns + factor values, with honest NA on thin cohorts.

## Test Cases

### TC-01 — Combination endpoint returns default-conditions payload

**Type:** api
**Preconditions:** Backend running on :8000; price/forward-return seed data present.

**Steps:**
1. `curl -s -w "\n%{http_code}" "http://localhost:8000/api/research/factor-combination"`

**Expected outcome:** 200 with JSON containing `conditions` (resolved from config `default_conditions`, count ∈ [min,max]), `horizon`, `horizons`, `default_horizon`, `min_sample`, `min_conditions`, `max_conditions`, `factors` catalog, `quantiles` list, `survivorship_bias`, `descriptive_caveat`, `pool_n`, `baseline{label,stats}`, `singles[]`, `combined{label,stats}`.
**Pass criteria:** HTTP 200; `baseline.stats.n == pool_n`; each `singles[*].stats.n <= pool_n`; `combined.stats.n <= min(singles[*].stats.n)`; no `as_of` field anywhere.

### TC-02 — Explicit multi-condition query (AND intersection)

**Type:** api
**Preconditions:** Backend running; seed present; two valid catalog factor keys known (from TC-01 `factors`).

**Steps:**
1. `curl -s -w "\n%{http_code}" "http://localhost:8000/api/research/factor-combination?condition=<f1>:top:quintile&condition=<f2>:bottom:tertile"`

**Expected outcome:** 200; one `singles` entry per condition; `combined` = exact set-intersection (AND) of single memberships.
**Pass criteria:** HTTP 200; `len(singles) == 2`; `combined.stats.n <= each singles[*].stats.n <= pool_n`.

### TC-03 — Horizon parameter re-points cohorts

**Type:** api
**Preconditions:** Backend running; `horizons` known from TC-01.

**Steps:**
1. Call endpoint with `?horizon=<h>` for a valid `h ∈ walk_forward.horizons`.

**Expected outcome:** 200; `horizon` echoes `<h>`; stats reflect that horizon's stored returns.
**Pass criteria:** HTTP 200; response `horizon == <h>`.

### TC-04 — Invalid condition / count → 422

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Unknown factor: `?condition=NOTAFACTOR:top:quintile&condition=<f2>:bottom:tertile` → expect 422.
2. Bad side: `?condition=<f1>:sideways:quintile&condition=<f2>:bottom:tertile` → expect 422.
3. Bad quantile: `?condition=<f1>:top:decile99&condition=<f2>:bottom:tertile` → expect 422.
4. Too few (1) conditions: `?condition=<f1>:top:quintile` → expect 422.
5. Too many (4) conditions → expect 422.
6. `horizon` not in `walk_forward.horizons` (e.g. `9999`) → expect 422.

**Expected outcome:** Every malformed request rejected; no fabricated factor/side/quantile/horizon accepted.
**Pass criteria:** All six requests return HTTP 422.

### TC-05 — No price data → 503

**Type:** api
**Preconditions:** Test environment with no stored price data (mirrors `factor-lab` route / `system_health`).

**Steps:**
1. Call `/api/research/factor-combination` against an empty-data backend.

**Expected outcome:** Explicit unavailable state, not a fabricated cohort.
**Pass criteria:** HTTP 503 (or covered by `test_api_research.py` no-data case).

### TC-06 — Read-only keystone (no recompute)

**Type:** api
**Preconditions:** `apps/backend/tests/test_research.py` keystone test present.

**Steps:**
1. Run the keystone test that monkeypatches `run_scan` / `score_stocks` / `forward_return` / `detect_*` / `score_regime` to raise, then calls `compute_factor_combination`.

**Expected outcome:** `compute_factor_combination` completes (SELECT + pure-group only); none of the patched-to-raise functions are invoked.
**Pass criteria:** Test passes; no scoring/return/pattern/regime function called.

### TC-07 — Cohort algebra & stats correctness on fixture

**Type:** api
**Preconditions:** Controlled fixture in `test_research.py`.

**Steps:**
1. Run cohort-algebra + stats unit tests.

**Expected outcome:** `combined` membership == exact intersection of singles; `baseline.n == pool_n`; `single.n <= pool_n`; `combined.n <= min(single.n)`; mean/median/hit-rate exact; `risk_adjusted` == downside-only `_risk_adjusted`, and `None` for all-non-negative or `n<2` cohort.
**Pass criteria:** All assertions pass.

### TC-08 — Honest NA: thin & empty cohorts

**Type:** api
**Preconditions:** Fixture with opposing/near-orthogonal extremes producing a combined `n < min_sample`.

**Steps:**
1. Run the honest-NA unit test.

**Expected outcome:** Thin combined cohort ⇒ `low_sample: true`; empty cohort ⇒ stats `None` (NA), never a fabricated 0.
**Pass criteria:** Test passes; `low_sample` flagged; no stat equals a fabricated 0 for empty cohort.

### TC-09 — Pool honesty (NULL-factor exclusion)

**Type:** api
**Preconditions:** Fixture with an observation NULL in a referenced factor.

**Steps:**
1. Run pool-honesty unit test.

**Expected outcome:** Observation with any NULL referenced factor excluded; `pool_n` ≤ each single factor's `_factor_observations` n. Equality to `compute_forward_aggregates.overall.mean` is NOT asserted (AND pool is a subset).
**Pass criteria:** Test passes.

### TC-10 — No magic numbers & config typing/validation

**Type:** artifact
**Preconditions:** Source + config files present.

**Steps:**
1. Confirm `config.yaml` `research.factor_lab.combination` block has `min_conditions`, `max_conditions`, `quantiles[]` (`{key,label,fraction}`), `default_conditions[]`.
2. Confirm `apps/backend/app/config.py` types `CombinationCfg` and `FactorLabCfg._validate` enforces `1 <= min <= max`, `fraction ∈ (0,1)`, unique quantile keys, `default_conditions` reference real factor/quantile keys & valid side, count ∈ [min,max].
3. Run `test_no_magic_numbers` (scanning `research.py`).

**Expected outcome:** Tunables read from config; no new numeric literal in `research.py` calc code; invalid config raises `ConfigError` at boot.
**Pass criteria:** Config block + typing present; `test_no_magic_numbers` passes; invalid-config unit cases raise `ConfigError`.

### TC-11 — Full backend suite green (run once)

**Type:** api
**Preconditions:** Backend deps installed. Run pytest ONCE (~14 min; do not run two pytest invocations concurrently).

**Steps:**
1. Run the project-template backend test command, capturing output.

**Expected outcome:** All tests pass, including new J-26 tests; no regressions.
**Pass criteria:** Exit code 0; zero failures.

### TC-12 — J-26 default section renders

**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000, seed present. (Serialize Chrome with browser-qa-agent; de-dup shots by sha256.)

**Steps:**
1. Navigate to `http://localhost:3000/research`; scroll below the regime-effectiveness table.
2. Observe the "Multi-factor combination cohort" section.

**Expected outcome:** Section renders the default 2-condition cohort: a Baseline row, two single-condition rows, and a Combined (AND) row; columns Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside). Caveat banner (survivorship + descriptive) present plus the "return/MAE arrives with J-29" honest note.
**Pass criteria:** All four rows + six columns render with real values; screenshot saved under `reports/qa/<phase>-evidence/`.

### TC-13 — Change a condition re-points table (network + DOM)

**Type:** browser
**Preconditions:** TC-12 section visible; network panel observable.

**Steps:**
1. Capture before-shot + before-network.
2. Change a Factor / Side / Quantile control.
3. Capture after-shot + observe a fresh `GET /api/research/factor-combination?...` request.

**Expected outcome:** A new combination request fires; the table updates to match the API response.
**Pass criteria:** Distinct before/after screenshots (sha256-different) + observed network request; DOM values match API payload.

### TC-14 — Add a 3rd condition (nesting visible)

**Type:** browser
**Preconditions:** TC-12 section visible; default is 2 conditions.

**Steps:**
1. Click "+ Add condition"; set a valid 3rd condition.
2. Read the resulting table.

**Expected outcome:** Table grows to 3 single rows + Combined; "+ Add condition" disabled at `max_conditions`; per-row remove disabled at `min_conditions`.
**Pass criteria:** 3 single rows + Combined render; `Combined n ≤ each single n ≤ pool n`; add/remove disabled states correct.

### TC-15 — NA fixture: thin combined cohort shows NA + n

**Type:** browser
**Preconditions:** TC-12 section visible.

**Steps:**
1. Configure opposing/near-orthogonal extreme conditions that yield a thin combined cohort.
2. Inspect the Combined row cells.

**Expected outcome:** Combined cohort cells render **NA + the honest `n`** (low-sample/null treatment), never a fabricated number.
**Pass criteria:** Combined row shows NA chip(s) with the sample size `n`; screenshot saved.

### TC-16 — J-18 regression: as-of toggle leaves `/research` byte-identical

**Type:** browser
**Preconditions:** Combination section present; global as-of control reachable.

**Steps:**
1. Capture decile table, rank-IC, regime table, AND new combination table state at latest as-of.
2. Toggle the global as-of date to a historical date.
3. Observe network for `as_of`-param requests; re-capture the four tables.

**Expected outcome:** All four tables byte-identical before/after; ZERO `as_of`-param requests (combination section has no date state).
**Pass criteria:** Four tables unchanged; no request carries an `as_of` param.

### TC-17 — J-25 / J-27 regression: existing Factor Lab intact

**Type:** browser
**Preconditions:** `/research` loaded.

**Steps:**
1. Verify decile table + rank-IC still render; change a factor/horizon and confirm they re-point.
2. Verify regime-effectiveness table still renders.

**Expected outcome:** Decile/IC and regime sections unchanged and still interactive.
**Pass criteria:** Both sections render and re-point on factor/horizon change; no regression.

### TC-18 — Frontend typecheck / build

**Type:** artifact
**Preconditions:** Frontend deps installed.

**Steps:**
1. Run `npm run build` (or project-template frontend test command) in `apps/frontend`.

**Expected outcome:** Build/typecheck succeeds with the new `api.ts` types and page section.
**Pass criteria:** Exit code 0; no TypeScript errors.

### TC-19 — Dev handoff artifact present

**Type:** artifact
**Preconditions:** Iteration implemented.

**Steps:**
1. Confirm `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-12-dev.md` exists and documents the changes.

**Expected outcome:** Handoff file present and non-empty.
**Pass criteria:** File exists with content describing engine fn + route + config + frontend section + tests.

## Summary

Total test cases: 19
API tests: 10 (TC-01–TC-09, TC-11; TC-05 conditional on no-data env)
Browser tests: 6 (TC-12–TC-17)
Artifact checks: 3 (TC-10, TC-18, TC-19)
