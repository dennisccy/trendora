# goal-i_can_see_the_wealthy_future_forever-iter-14 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Add the read-only **Setup & Pattern Lab** event study to `/research`: store lookahead-free, append-only MAE/MFE excursions on `forward_returns`, then pool every cross-snapshot occurrence of a chosen setup/pattern to report per-horizon distribution + expectancy + MAE/MFE + downside-risk-adjusted ratios + best exit-horizon + by-regime/by-sector slices — all from stored, survivorship-labelled values, with no read-path recompute and no new date control.

## Test Cases

### TC-01 — MAE/MFE no-lookahead property
**Type:** api (unit — `test_forward_testing.py`)
**Preconditions:** `forward_excursions(bars_after_list, entry_close, horizon)` helper exists.
**Steps:**
1. Compute `forward_excursions` over a known `entry_close` + post-bars list (date > D) at horizon h.
2. Re-compute after removing every bar after the h-th post-bar.
3. Assert MAE = `min(low_i)/entry_close − 1` and MFE = `max(high_i)/entry_close − 1` over the first `horizon` bars only.
**Expected outcome:** Result is identical before/after removing later bars; uses only `post_bars[:horizon]`.
**Pass criteria:** Both computations return byte-equal dict; values match the closed-form over the first h bars. No future bar (date > the h-th) influences the result.

### TC-02 — MAE/MFE NA gate
**Type:** api (unit — `test_forward_testing.py`)
**Preconditions:** helper + `_insert_run_forward_returns` extended.
**Steps:**
1. Call `forward_excursions` with `entry_close` missing/zero → assert `None`.
2. Call with fewer than `horizon` post-bars → assert `None`.
3. Confirm no `ForwardReturn` row is INSERTed for that `(symbol, horizon)` (same gate as `realized_return`).
**Expected outcome:** None returned and no row written when entry_close invalid or `< horizon` post-bars.
**Pass criteria:** Returns `None` in all under-data cases; no fabricated/truncated excursion row; gate matches `forward_return()`.

### TC-03 — Excursion immutability / idempotency on INSERT path
**Type:** api (unit — `test_forward_testing.py`)
**Preconditions:** DB with seeded runs.
**Steps:**
1. Run `backfill_forward_returns` / `backfill_run_forward_returns`; assert fresh rows carry populated `mae`/`mfe`.
2. Run the same backfill a 2nd time (warm).
**Expected outcome:** 2nd run inserts 0 rows and UPDATEs no `scanner_runs`/`scanner_results`/`*_scores`/existing `forward_returns` row.
**Pass criteria:** Insert count == 0 on warm run; no UPDATE issued; `(run_id, symbol, horizon)` skip-set unchanged; append-only preserved.

### TC-04 — MFE ≥ realized-at-h ≥ MAE band relationship
**Type:** api (unit — `test_forward_testing.py`)
**Preconditions:** seeded rows with realized_return + mae + mfe.
**Steps:**
1. For rows where all three are non-NA, assert `mfe ≥ realized_return ≥ mae` (the realized close lies within the [low-min, high-max] band).
**Expected outcome:** Band relationship holds for every assertable row.
**Pass criteria:** No row violates `mfe ≥ realized_return ≥ mae`.

### TC-05 — Event-study read-only keystone (patch-to-raise)
**Type:** api (unit — `test_research.py`)
**Preconditions:** `compute_event_study` exists; DB seeded.
**Steps:**
1. Monkeypatch `run_scan`, `score_stocks`, `forward_return`, `forward_excursions`, `detect_*`, `score_regime`, `backfill*` to raise.
2. Call `compute_event_study(session, subject_key, horizon)`.
**Expected outcome:** Returns a full payload without invoking any patched scoring/regime/return/excursion math (SELECT-only over ForwardReturn ⋈ ScannerResult ⋈ ScannerRun).
**Pass criteria:** No patched function raised; payload returned. Proves no read-path recompute.

### TC-06 — Consistency invariant (pooled mean == compute_forward_aggregates cohort mean)
**Type:** api (unit — `test_research.py`)
**Preconditions:** seeded DB.
**Steps:**
1. For a SETUP subject at horizon h, assert event-study pooled `mean_return` == `compute_forward_aggregates(h).by_setup[setup].mean_return`.
2. For the VCP PATTERN subject, assert pooled `mean_return` == the `by_vcp` flagged-cohort mean.
**Expected outcome:** Same stored-observation set → identical means.
**Pass criteria:** Means equal within float tolerance. (Bound to `compute_forward_aggregates`, NOT the per-date scorecard top cohort — iter-2 lesson.)

### TC-07 — Downside-only risk-adjusted + honest NA
**Type:** api (unit — `test_research.py`)
**Preconditions:** seeded DB incl. an all-non-negative (downside-undefined) cohort.
**Steps:**
1. Assert `return_per_downside_dev` (= `_risk_adjusted`) and `return_per_mae` (= mean/mean(|mae|)) are present beside raw mean.
2. Assert both are `None`/NA when no downside, `mean(|mae|)==0`, or n<2 — never total volatility.
3. For an empty regime/sector → NA + `n=0`; for a low-count subject → `low_sample=True`.
**Expected outcome:** Risk uses downside-deviation / |MAE| only; low-sample/empty cells honest NA + n.
**Pass criteria:** No total-vol metric; NA exactly in the defined edge cases; raw shown beside risk-adjusted.

### TC-08 — Unknown subject → ValueError; regime n-sum invariant
**Type:** api (unit — `test_research.py`)
**Preconditions:** seeded DB.
**Steps:**
1. Call `compute_event_study` with an unknown subject key → assert `ValueError`.
2. For the selected horizon, assert every `config.regime.labels` label emits a row (n=0 → NA) and `Σ per-regime n == selected-horizon pooled n`.
**Expected outcome:** ValueError on unknown subject; regime slice complete and conserving.
**Pass criteria:** ValueError raised; every configured regime label present; per-regime n sums to pooled n.

### TC-09 — Endpoint default / 422 / 503 / payload shape
**Type:** api (integration — `test_api_research.py`)
**Preconditions:** backend app importable; test DB.
**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/research/event-study"` → default subject + horizon (200).
2. `...?subject=__bogus__` → 422; `...?horizon=99999` → 422.
3. With no price data (`latest_data_date is None`) → 503.
4. Inspect 200 body: `subjects` catalog present, per-horizon rows, by-regime + by-sector slices, `survivorship_bias` + `descriptive_caveat` caveats, NO `as_of`/date param accepted.
**Expected outcome:** 200 default; 422 unknown subject/horizon; 503 no data; payload matches contract; mirrors factor-lab/factor-combination handlers.
**Pass criteria:** Status codes exactly 200/422/422/503; all listed payload keys present; endpoint takes no date param.

### TC-10 — No magic numbers scan extended
**Type:** artifact (unit — `test_no_magic_numbers.py`)
**Preconditions:** test scans `research.py` + `forward_testing.py`.
**Steps:**
1. Run the no-magic-numbers test over the event-study + excursion additions.
**Expected outcome:** No literal threshold introduced; subjects/min_sample/horizons sourced from config or the fixed `ALL_STATUSES`/`config.patterns` vocabulary; only structural `>0` win/loss boundary + rank/index 1's allowed.
**Pass criteria:** Test passes; no new disallowed literal.

### TC-11 — Full backend suite green after DB regen
**Type:** api (suite gate)
**Preconditions:** `apps/backend/data/trendora.db` deleted and regenerated from committed seed; any fixture updates landed.
**Steps:**
1. Run the full backend pytest ONCE (~14–20 min; do not run two pytest invocations concurrently).
**Expected outcome:** Entire suite passes including new excursion/event-study tests; regenerated snapshots byte-identical (scoring path untouched).
**Pass criteria:** pytest exit code 0; 0 failures/errors.

### TC-12 — Frontend build typechecks
**Type:** artifact
**Preconditions:** `apps/frontend` deps installed.
**Steps:**
1. Run `npm run build` in `apps/frontend`.
**Expected outcome:** Build + typecheck succeed with the new `EventStudyLab`, `fetchEventStudy`, and `EventStudyResponse` type.
**Pass criteria:** Build exits 0; no type errors.

### TC-13 — J-29: SETUP subject renders the full event study
**Type:** browser
**Preconditions:** backend + frontend running; DB regenerated.
**Steps:**
1. Navigate to `http://localhost:3000/research`; scroll to the Setup & Pattern Lab (below Factor Lab + Combination Lab).
2. Select a SETUP subject (e.g. Actionable or Breakout-watch) from the subject selector.
3. Inspect the per-horizon table.
**Expected outcome:** Per-horizon distribution (mean/median/%positive/dispersion) + expectancy + mean-MAE/mean-MFE + both downside-risk-adjusted columns (return/downside-dev AND return/MAE) + `n` render; best-exit-horizon row highlighted; survivorship caveat visible.
**Pass criteria:** All listed columns + n present for each horizon; best-exit-horizon highlighted; `CaveatBanner` (survivorship + descriptive) visible. Screenshot saved to `reports/qa/<phase>-evidence/TC-13-setup-event-study.png`.

### TC-14 — J-29: PATTERN subject + by-regime/by-sector NA + re-point
**Type:** browser
**Preconditions:** TC-13 environment.
**Steps:**
1. Select a PATTERN subject (e.g. VCP) via the grouped (`Setups` vs `Patterns`) selector.
2. Inspect the by-regime panel and by-sector panel for the selected horizon.
3. Compare rendered values + sha256 of the table region against the SETUP subject capture.
**Expected outcome:** Same per-horizon metrics render for VCP; by-regime + by-sector panels render with ≥1 honest NA + n cell; changing subject re-points to distinct values.
**Pass criteria:** By-regime + by-sector panels present with ≥1 NA + n cell; subject change yields distinct values + distinct sha256 vs TC-13. Screenshot `TC-14-pattern-event-study.png`.

### TC-15 — J-18 re-verify: as-of toggle leaves event study byte-identical
**Type:** browser
**Preconditions:** event study rendered; Chrome access serialized (one tool vacates before the other captures).
**Steps:**
1. Capture the event-study tables and record outbound network requests.
2. Toggle the global as-of control latest → historical.
3. Re-capture tables; record network.
**Expected outcome:** Event-study tables byte-identical across the toggle; zero requests carry an `as_of` param (the lab is a cross-date aggregate with no date state).
**Pass criteria:** DISTINCT shots compare byte-identical (sha256 equal across toggle) AND a DOM/network assertion confirms 0 `as_of`-param requests from the event-study fetch. Evidence de-duped by sha256.

### TC-16 — J-07 re-verify after regen: Risk-Off gates Actionable=0
**Type:** browser
**Preconditions:** DB regenerated; both seeded Risk-Off runs available.
**Steps:**
1. Navigate to the scanner/leaderboard for each seeded Risk-Off run.
2. Count stocks marked "Actionable".
**Expected outcome:** Zero stocks Actionable (watchlist-only) under Risk-Off after regen.
**Pass criteria:** Actionable count == 0 for both Risk-Off runs. Screenshot `TC-16-riskoff-actionable-zero.png`.

### TC-17 — J-06 re-verify after regen: NVDA list↔detail byte-identical
**Type:** browser
**Preconditions:** DB regenerated.
**Steps:**
1. Read NVDA's six canonical scores + bucket + setup on the leaderboard.
2. Open NVDA detail; read the same values.
**Expected outcome:** Values byte-identical between leaderboard and detail (single source of truth; no recompute).
**Pass criteria:** Every compared score/bucket/setup matches exactly. Screenshot `TC-17-nvda-list-detail.png`.

### TC-18 — Required labs/pages still green (J-09/J-14/J-16/J-25–J-27/J-30)
**Type:** browser
**Preconditions:** app running post-regen.
**Steps:**
1. Load System Health (J-09 by-bucket/setup/regime/VCP aggregates).
2. Load Backtest per-date scorecard (J-14).
3. Re-render Factor Lab + Combination Lab sections on `/research` and re-point a factor (J-25/J-26/J-27/J-30); confirm VCP/pattern surfaces (J-16/J-28).
**Expected outcome:** All listed surfaces render unchanged by the additive columns/section.
**Pass criteria:** Each surface renders without error and matches prior behavior; Factor/Combination labs re-point correctly. Screenshot `TC-18-regression-surfaces.png`.

## Summary

Total test cases: 18
- API tests: 11 (TC-01–TC-09, TC-11) + artifact-flavored counted below
- Browser tests: 6 (TC-13–TC-18)
- Artifact checks: 2 (TC-10, TC-12)

By type — API/unit/integration: 10 (TC-01–TC-09, TC-11); Browser: 6 (TC-13–TC-18); Artifact: 2 (TC-10, TC-12).
