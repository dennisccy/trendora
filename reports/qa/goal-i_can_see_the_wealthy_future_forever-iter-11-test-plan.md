# goal-i_can_see_the_wealthy_future_forever-iter-11 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

On the Factor Lab (`/research`), show a chosen factor's effectiveness **split by market regime** — per configured regime label: `n`, rank-IC, top-decile mean, bottom-decile mean, the raw top-minus-bottom-decile spread, and the **downside-risk-adjusted** spread — served read-only from already-stored evidence, with honest **NA + n** for low-sample regimes (J-27), while J-25/J-18/J-09/J-19/J-15 stay green.

Base URLs: backend `http://localhost:8000`, frontend `http://localhost:3000`. Valid factors: `leadership_score`, `entry_quality_score`, `risk_score`, `rs_spy_3m`, `ma_stack`, `high_proximity`, `up_down_vol`, `atr_pct`. Valid horizons: `1, 5, 10, 20, 60`. Regime labels (config order): `Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off`. `min_sample = 30`, `deciles = 10`.

## Test Cases

### TC-01 — `by_regime` slice present and shaped correctly in payload
**Type:** api
**Preconditions:** Backend running; price/snapshot data loaded.
**Steps:**
1. `curl -s "http://localhost:8000/api/research/factor-lab?factor=leadership_score&horizon=5" | python3 -m json.tool`
2. Inspect the `by_regime` array.
**Expected outcome:** Response `200`; payload contains existing keys plus `by_regime`, an array. Each row has `regime` (string), `n` (int), `low_sample` (bool), `rank_ic` (object with `value`), `top_decile_mean`, `bottom_decile_mean`, `spread`, `risk_adjusted_spread` (number or null).
**Pass criteria:** `by_regime` exists; every row has all 8 fields with correct types; no row omits a field.

### TC-02 — One row per configured regime label, in config order
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s "http://localhost:8000/api/research/factor-lab?factor=leadership_score&horizon=5" | python3 -c "import sys,json; print([r['regime'] for r in json.load(sys.stdin)['by_regime']])"`
**Expected outcome:** Exactly 6 rows, regimes equal `["Strong risk-on","Risk-on","Narrow leadership","Choppy","Defensive","Risk-off"]` in that order.
**Pass criteria:** Row regimes match `config.regime.labels` exactly in order; a regime with no observations is present as an honest `n=0` row (not omitted, not fabricated).

### TC-03 — Σ per-regime n == n_total (consistency invariant)
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s "http://localhost:8000/api/research/factor-lab?factor=leadership_score&horizon=5" > /tmp/fl.json`
2. `python3 -c "import json; d=json.load(open('/tmp/fl.json')); print(sum(r['n'] for r in d['by_regime']), d.get('n_total'))"`
**Expected outcome:** Sum of per-regime `n` equals `n_total`.
**Pass criteria:** `Σ by_regime[*].n == n_total` exactly (every observation carries exactly one configured regime label).

### TC-04 — Low-sample regime renders honest NA, not a fabricated number
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s "http://localhost:8000/api/research/factor-lab?factor=leadership_score&horizon=60" > /tmp/fl60.json`
2. Inspect rows where `n < 30` (`low_sample` true).
**Expected outcome:** Any row with `n < 30` has `low_sample=true` and `spread=null` AND `risk_adjusted_spread=null`. A regime with `n<2`/zero rank variance has `rank_ic.value=null`.
**Pass criteria:** Low-sample rows carry honest `n`, `low_sample=true`, and `spread`/`risk_adjusted_spread` are `null` — never 0 or an invented value.

### TC-05 — Risk-adjusted spread is downside-only (NA when no downside)
**Type:** artifact (unit test) + api
**Preconditions:** Backend test suite available.
**Steps:**
1. Run the J-27 downside-only unit test in `apps/backend/tests/test_research.py` (regime with all-non-negative top decile).
2. Cross-check payload: find any regime row where `spread` is numeric but `risk_adjusted_spread` is null.
**Expected outcome:** Unit test asserts `risk_adjusted_spread is None` while raw `spread` is numeric for an all-non-negative top decile.
**Pass criteria:** Test passes; `risk_adjusted_spread` uses downside deviation only — never a total-volatility number; numeric `spread` can coexist with null `risk_adjusted_spread`.

### TC-06 — Read-only keystone: regime read verbatim, never recomputed
**Type:** artifact (unit test)
**Preconditions:** Backend test suite.
**Steps:**
1. Run the extended patch-to-raise keystone test that monkeypatches `app.engine.regime.score_regime` (plus `run_scan`/`score_stocks`/`forward_return`/`detect_*`) to raise.
2. Assert `compute_factor_lab(...)["by_regime"]` is still fully populated.
**Expected outcome:** `by_regime` is fully populated despite all compute functions raising.
**Pass criteria:** Test passes — proves the regime is read from stored `scanner_runs.regime_label` (SELECT-only), no scoring/return/factor/regime recompute in the read path.

### TC-07 — Exact regime spread + rank-IC on hand fixture
**Type:** artifact (unit test)
**Preconditions:** Backend test suite.
**Steps:**
1. Run the J-27 hand-fixture test: a monotone factor within one regime and an inverse within another.
**Expected outcome:** Monotone regime → known positive `spread` (top-decile mean − bottom-decile mean) and `rank_ic.value ≈ 1.0`; inverse regime → negative spread and negative rank-IC.
**Pass criteria:** Asserted exact spread + `rank_ic.value` match; observations sorted ascending by factor before deciles (top/bottom not scrambled).

### TC-08 — No magic numbers / no new config key in research.py
**Type:** artifact (unit test)
**Preconditions:** Backend test suite.
**Steps:**
1. Run `apps/backend/tests/test_no_magic_numbers.py`.
**Expected outcome:** `research.py` passes the scan — regime labels from `cfg.regime.labels`, threshold from `cfg.walk_forward.min_sample`, decile count from `cfg.research.factor_lab.deciles`; no new config key, no numeric literal added.
**Pass criteria:** Test passes; no new literal flagged in `research.py`.

### TC-09 — Error paths unchanged (unknown factor/horizon, no data)
**Type:** api
**Preconditions:** Backend running.
**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/api/research/factor-lab?factor=bogus&horizon=5"`
2. `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/api/research/factor-lab?factor=leadership_score&horizon=999"`
**Expected outcome:** Both return `422`.
**Pass criteria:** Unknown factor → 422; unknown horizon → 422 (no fabricated row, behavior unchanged).

### TC-10 — Full backend test suite green (no regression)
**Type:** artifact (unit test)
**Preconditions:** Backend deps installed. NOTE: full pytest ~14 min; run a single invocation only.
**Steps:**
1. Run the backend test command from `.claude/project-template.md` (pytest), capturing output.
**Expected outcome:** All tests pass, including pre-existing decile math, rank-IC, downside-only, NA honesty, pooled-mean == `compute_forward_aggregates.overall.mean_return` invariant, and config/boot validation.
**Pass criteria:** Exit code 0; zero failures/errors; new J-27 tests included in the pass count.

### TC-11 — Frontend builds / typechecks with new types
**Type:** artifact (build)
**Preconditions:** Frontend deps installed.
**Steps:**
1. `cd apps/frontend && npm run build`
**Expected outcome:** Build succeeds; `/research` route typechecks with the new `RegimeEffectivenessRow` interface and `by_regime` on `FactorLabResponse`.
**Pass criteria:** Build exits 0; no TypeScript errors.

### TC-12 — Regime-effectiveness table renders on /research (J-27)
**Type:** browser
**Preconditions:** Frontend `:3000` + backend `:8000` running. Serialize Chrome with browser-qa-agent; evidence under `reports/qa/<phase>-evidence/`.
**Steps:**
1. Chrome MCP navigate to `http://localhost:3000/research`.
2. Locate the "Factor effectiveness by market regime" table below the decile table + rank-IC card.
3. Screenshot `reports/qa/<phase>-evidence/TC-12-regime-table.png`.
**Expected outcome:** Table renders with columns Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top−bottom) · Risk-adjusted spread, one row per configured regime label (6 rows), each with an `n` chip.
**Pass criteria:** All 6 regime rows visible with their `n` chips; column headers as specified; DOM text confirms (not just an image).

### TC-13 — Short horizon shows a numeric regime row; long horizon shows NA+n
**Type:** browser
**Preconditions:** As TC-12.
**Steps:**
1. On `/research` set horizon = 5d (or 1d). Confirm at least one regime row clears `min_sample` with a numeric rank-IC + spread; screenshot.
2. Set horizon = 60d (and/or pick a sparse regime). Confirm at least one regime row shows **NA + n** for spread/risk-adjusted spread.
3. Capture distinct sha256 screenshots for each state.
**Expected outcome:** Short horizon → ≥1 regime with numeric rank-IC + spread; long horizon → ≥1 regime rendering NA + `SampleSize` chip (honest low-sample, not 0).
**Pass criteria:** A numeric regime cell observed at short horizon AND an NA+n cell observed at long/sparse horizon; the two screenshots have distinct sha256.

### TC-14 — Regime table re-points on factor change (J-27)
**Type:** browser
**Preconditions:** As TC-12.
**Steps:**
1. On `/research` at fixed horizon, note regime-table values (DOM text) and capture network `GET /api/research/factor-lab?factor=…&horizon=…`.
2. Change the factor selector to a different factor.
3. Observe a new `GET .../factor-lab?factor=<new>&horizon=…` request and changed regime-table DOM text; capture distinct before/after screenshots (sha256).
**Expected outcome:** Selecting a new factor fires a new fetch and the regime table values change.
**Pass criteria:** New network request observed with the new factor param AND regime-table DOM text differs; before/after screenshots have distinct sha256 (not a single reused pair).

### TC-15 — J-18 regression: as-of switcher does NOT affect /research
**Type:** browser
**Preconditions:** As TC-12.
**Steps:**
1. On `/research`, record the Factor Lab (decile table, rank-IC, regime table) DOM/screenshot and watch network.
2. Change the global top-bar as-of switcher.
3. Re-record DOM/screenshot and inspect all `/api/research/factor-lab` requests.
**Expected outcome:** The Factor Lab (incl. the new regime table) is byte-identical after the as-of change; **zero** requests carry an `as_of` param.
**Pass criteria:** Regime table + decile table + rank-IC unchanged (identical sha256); no `as_of`-param request issued from `/research`.

### TC-16 — J-25 regression: decile table + rank-IC still render and re-point
**Type:** browser
**Preconditions:** As TC-12.
**Steps:**
1. On `/research`, confirm the existing decile table and rank-IC card still render.
2. Change factor/horizon and confirm both re-point alongside the new regime table.
**Expected outcome:** Decile table + rank-IC card render and update on factor/horizon change.
**Pass criteria:** Both pre-existing panels present and re-point correctly; no visual/functional regression.

### TC-17 — Empty-state: no regime table fabricated when n_total == 0
**Type:** browser (or api)
**Preconditions:** A (factor, horizon) combination with `n_total == 0`, if reachable; otherwise inspect the empty-state gate.
**Steps:**
1. Reach a `/research` state where `n_total === 0` (e.g. a horizon with no realized forward returns).
2. Observe the page.
**Expected outcome:** The empty-state path renders; the regime table is absent (not fabricated). Existing error card behavior unchanged.
**Pass criteria:** When `n_total == 0`, no regime rows are fabricated; the existing empty-state/error gate shows.

### TC-18 — Dev handoff artifact present
**Type:** artifact
**Preconditions:** Dev phase complete.
**Steps:**
1. Check `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-11-dev.md` exists.
**Expected outcome:** Handoff present with What Was Built / Files Changed / Tests Run (exact counts) / Known Issues / Suggested Next Phase; states explicitly whether `status.json`/auditor handoff was produced (check phase-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-11/status.json`).
**Pass criteria:** File exists and contains the required sections with exact test counts.

## Summary

Total test cases: 18
- API tests: 5 (TC-01, TC-02, TC-03, TC-04, TC-09)
- Browser tests: 6 (TC-12, TC-13, TC-14, TC-15, TC-16, TC-17)
- Artifact / unit / build checks: 7 (TC-05, TC-06, TC-07, TC-08, TC-10, TC-11, TC-18)

(TC-05 spans a unit assertion + a payload cross-check; TC-17 is browser-or-api depending on reachability.)
