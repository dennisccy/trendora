# goal-i_can_see_the_wealthy_future-iter-2 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Frontend Present:** yes

## Phase Goal

Compute the first real **canonical values** — a 0–100 Market Regime (one of six labels) and ranked Sector/industry leadership scores — once in `apps/backend/app/engine/` and serve them read-only so `/sectors` ranks every sector/industry ETF (RS-vs-SPY, dist-from-52w-high, trend label) and `/` shows regime + universe-relative breadth + data-as-of + Top Sectors, deterministic against the frozen seed with **no client-side recomputation** (flips J-04 green; partially advances J-01).

## Test Cases

### TC-01 — `/api/sectors` returns ranked ETF leaderboard
**Type:** api
**Preconditions:** Backend running on its port; frozen seed loaded in `daily_prices`.
**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8000/api/sectors`
**Expected outcome:** HTTP 200; JSON list of rows, each with `ticker, kind, name, score, bucket, rs_vs_spy, dist_from_52w_high_pct, trend_label, components, rank`; rows sorted by `score` descending.
**Pass criteria:** status 200; `score` values are non-increasing across the list; every row has all listed fields; `components` is a non-empty array of `{name, contribution}`.

### TC-02 — SPY excluded as a ranked leader
**Type:** api
**Preconditions:** Backend running; `/api/sectors` reachable.
**Steps:**
1. `curl -s http://localhost:8000/api/sectors | python3 -c "import sys,json; d=json.load(sys.stdin); print([r['ticker'] for r in d if r['ticker']=='SPY'])"`
**Expected outcome:** SPY appears in no ranked row (it is `kind="index"`, the RS benchmark).
**Pass criteria:** the printed list is empty `[]`; no row has `ticker == "SPY"`.

### TC-03 — `/api/dashboard` returns regime + breadth + honest pending fields
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s -w "\n%{http_code}" http://localhost:8000/api/dashboard`
**Expected outcome:** HTTP 200; JSON `{regime:{score,label,components}, breadth:{above_50dma_pct,above_200dma_pct,label}, asof_date, candidate_counts, top_themes}`.
**Pass criteria:** status 200; `regime.score` ∈ [0,100]; `regime.label` is one of the six configured labels; `regime.components` non-empty; `breadth.label == "universe-relative"`; `breadth.above_50dma_pct` and `above_200dma_pct` ∈ [0,100]; `asof_date` present; **`candidate_counts` is null AND `top_themes` is null** (not 0, not fabricated).

### TC-04 — Single source of truth: served values equal engine outputs (no drift)
**Type:** api
**Preconditions:** Backend running; `pytest` available.
**Steps:**
1. Run `test_api_engine.py` (TestClient): compare `/api/sectors` body to `score_sectors(asof=max date)` and `/api/dashboard` regime to `score_regime(asof=max date)`.
2. Cross-check: Dashboard Top Sectors values match the top N rows of `/api/sectors`.
**Expected outcome:** API responses are identical to direct engine output; Top Sectors equal the sliced `/api/sectors` top N.
**Pass criteria:** `test_api_engine` passes; no value differs between endpoint and engine; regime served only by `/api/dashboard`, sectors only by `/api/sectors`.

### TC-05 — `bars_asof` no-lookahead boundary
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run `apps/backend/tests/test_prices_asof.py`.
**Expected outcome:** `bars_asof(session, symbol, d)` includes the bar with date == d and excludes every bar with date > d; rows returned ascending by date.
**Pass criteria:** test asserts a date==d bar present and a date>d bar absent, and passes.

### TC-06 — Indicator functions return exact hand-computed values
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run `apps/backend/tests/test_indicators.py`.
**Expected outcome:** `sma`, `rs_vs`, `atr_pct`, `dist_from_high`, `ma_stack`, `vol_trend` match exact expected values on small fixtures; periods sourced from `config.indicators`.
**Pass criteria:** all indicator assertions pass with exact (not "something returned") expected values.

### TC-07 — `to_bucket` correct letter at each config edge
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run `apps/backend/tests/test_buckets.py`.
**Expected outcome:** `to_bucket(score)` returns the correct A/B/C/D letter at each `config.buckets` edge and E below the D edge.
**Pass criteria:** boundary assertions (A/B/C/D edges + E-below-D) all pass; `to_bucket` is the only place A–E is derived.

### TC-08 — Regime score range, label set, and boundary mapping
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run `apps/backend/tests/test_regime.py`.
**Expected outcome:** `score_regime` returns `score ∈ [0,100]`, `label` ∈ the six configured labels, correct label **at `label_edges` boundaries**, `breadth ∈ [0,100]`, components present.
**Pass criteria:** all asserts pass including the label-edge boundary mapping.

### TC-09 — Sector scoring: ranked, complete rows, SPY excluded, deterministic
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run `apps/backend/tests/test_sectors.py`.
**Expected outcome:** list ranked descending by score; each row has RS-vs-SPY, dist-from-52w-high, trend label, components; SPY excluded; repeated calls with the same `asof` yield identical output.
**Pass criteria:** ranking, row-field, SPY-exclusion, and determinism asserts all pass.

### TC-10 — No magic numbers in calculation code
**Type:** artifact
**Preconditions:** repo checked out.
**Steps:**
1. Grep `apps/backend/app/engine/{indicators,regime,sectors,buckets}.py` for numeric period/weight/cutoff/bucket-edge literals.
**Expected outcome:** no such literal in calc code — every period/weight/cutoff/edge comes from `config.yaml`.
**Pass criteria:** grep finds no hard-coded scoring literal; `config.yaml` contains `indicators:`, `sectors:` (weights + trend cutoffs), and `regime.label_edges`.

### TC-11 — Config validation raises explicit ConfigError
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run `apps/backend/tests/test_config_engine.py` (missing/invalid `indicators`, `sectors.weights`, `regime.label_edges` not covering 0–100).
**Expected outcome:** each invalid config raises an explicit `ConfigError`, never a silent default.
**Pass criteria:** all error-path asserts pass; `ConfigError` raised for each malformed section.

### TC-12 — Short-history symbol reports NA, never fabricated
**Type:** api (unit)
**Preconditions:** `pytest` available; a symbol with `< config.indicators.min_history_bars` bars (e.g. WGMI/BKCH/GEV).
**Steps:**
1. Run the short-history case in `test_indicators.py` / `test_sectors.py`.
**Expected outcome:** long MAs/RS report NA for short-history symbols; no crash; no invented value.
**Pass criteria:** NA (not a number) returned for unavailable long-window metrics; no exception.

### TC-13 — Regression: existing backend tests still pass
**Type:** api (unit)
**Preconditions:** `pytest` available.
**Steps:**
1. Run the full backend pytest suite.
**Expected outcome:** the existing 25 backend tests plus the new engine/api tests pass.
**Pass criteria:** 0 failures; the prior 25 tests remain green.

### TC-14 — Frontend build compiles + typechecks
**Type:** artifact
**Preconditions:** frontend deps installed.
**Steps:**
1. Run `npm run build` in `apps/frontend`.
**Expected outcome:** build succeeds; TypeScript typechecks (new `fetchSectors`/`fetchDashboard` interfaces compile).
**Pass criteria:** build exits 0; no type errors.

### TC-15 — J-04 browser: `/sectors` ranked leaderboard
**Type:** browser
**Preconditions:** **both** backend and frontend running and stable.
**Steps:**
1. Chrome MCP navigate to `http://localhost:3000/sectors`.
2. Read the table rows; capture screenshot to `reports/qa/<phase>-evidence/TC-15-sectors.png`.
3. Expand the top row to reveal its component breakdown.
**Expected outcome:** dense ranked table; multiple rows ordered by Sector Score (non-increasing); A–E bucket + raw 0–100 (colour-graded), RS-vs-SPY, dist-from-52w-high %, trend label per row; top row shows numeric RS-vs-SPY + dist % + trend label; SPY absent as a leader; row expands to component breakdown.
**Pass criteria:** ≥2 rows non-increasing by score; top row has numeric RS-vs-SPY, numeric dist-from-52w-high %, a trend label; no SPY leader row; component breakdown visible on expand; screenshot saved on disk.

### TC-16 — J-01 browser (partial): `/` dashboard regime + breadth + data-as-of + Top Sectors
**Type:** browser
**Preconditions:** both servers running and stable.
**Steps:**
1. Chrome MCP navigate to `http://localhost:3000/`.
2. Read the regime panel, breadth figure, data-as-of indicator, Top Sectors list, and the candidate-counts / Top-Themes areas; capture screenshot to `reports/qa/<phase>-evidence/TC-16-dashboard.png`.
**Expected outcome:** Market Regime panel shows one of six labels + numeric 0–100 score + component breakdown; breadth % labelled "universe-relative"; "Data as-of <date>" renders; Top Sectors list shows ≥3 sectors each with a score (sourced from `/api/sectors`); candidate counts + Top Themes show an explicit **pending** placeholder (no zeros/fabricated numbers).
**Pass criteria:** regime label ∈ six + numeric score; breadth % with "universe-relative" label; a data-as-of date; ≥3 Top Sectors with scores matching `/api/sectors`; candidate counts & Top Themes display "pending" placeholder text, not numbers; screenshot saved. *(J-01 remains `failing`/partial — this is expected, not a regression.)*

### TC-17 — Backend-unavailable state (no fabricated data)
**Type:** browser
**Preconditions:** frontend running; backend stopped/unreachable.
**Steps:**
1. Stop the backend; Chrome MCP navigate to `/sectors` and `/`.
2. Capture screenshots to the evidence dir.
**Expected outcome:** both pages render an explicit "Backend unavailable" state — no fabricated rows, scores, or regime values.
**Pass criteria:** visible "Backend unavailable" (or equivalent explicit error) state on both pages; no numeric scores/rows shown; no crash.

## Summary

Total test cases: 17
- API tests (incl. unit/integration via pytest/curl/TestClient): 11 (TC-01–TC-09, TC-11, TC-13)
- Browser tests: 3 (TC-15, TC-16, TC-17)
- Artifact checks: 3 (TC-10, TC-12*, TC-14)

\* TC-12 is executed via pytest but verifies the "no fabricated value / NA" data contract; counted under API.

**Mapping to DoD:** J-04 → TC-01/02/15; J-01 partial → TC-03/16; single-source-of-truth → TC-04; no-lookahead → TC-05; no-magic-numbers → TC-10; explainable → TC-01/03/15/16; honest limitations → TC-03/16; no-fabrication → TC-12/17; config validation → TC-11; regression → TC-13/14.
