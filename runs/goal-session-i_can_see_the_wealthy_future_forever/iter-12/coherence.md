**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-12 (J-26: Factor Lab multi-factor combination cohorts)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 12
- **Snapshot SHA audited:** `b19687744a8241f4fc6f0efb439df31b3b97e4be` (+ uncommitted working tree)
- **Auditor:** coherence-auditor
- **Result:** no objective Data-Contract or Information-Architecture violations. A textbook-clean additive iteration; no advisory issues worth raising.

## Scope of changes audited

`git diff` against the snapshot touched only the files the spec promised — additive, no edits to any existing contract value's computing module or read path:

| File | Nature |
|---|---|
| `apps/backend/app/engine/research.py` (+197) | NEW read-only `compute_factor_combination` + helpers (`_combination_observations`, `_quantile_cutoff`, `_cohort_stats`, `_condition_payload`); `compute_factor_lab` + all existing helpers unchanged (only `ceil`/`median` added to imports) |
| `apps/backend/app/api/research.py` (+88) | NEW `GET /api/research/factor-combination` route; existing `factor-lab` route untouched |
| `config.yaml` (+22) | additive `research.factor_lab.combination` block (min/max conditions, quantile vocabulary, default_conditions) |
| `apps/backend/app/config.py` (+97) | typed `CombinationCfg` + boot validation of the new block |
| `apps/frontend/app/research/page.tsx` (+390) | additive `CombinationLab` section + sub-components on the existing Factor Lab page |
| `apps/frontend/lib/api.ts` (+90) | new types + `fetchFactorCombination` (canonical-endpoint fetch) |
| `apps/backend/tests/*` (+532) | new `test_research.py`/`test_api_research.py`/`test_config*` cases + shared synthetic-config fixtures gaining the now-required `combination` sub-block (test_sectors/test_themes/test_config_engine) — no surface |
| `runs/goal-session-.../state/blueprint.md` (+9) | additive registration of the J-26 value + iter-12 nav note |
| telemetry/trace | automation artifacts (non-source) |

No change to `forward_testing.py`, `scoring.py`, `scanner.py`, `patterns.py`, `regime.py`, `snapshot_serving.py`, the as-of provider, `backtest/page.tsx`, or any existing endpoint — matching the spec's OUT OF SCOPE list and confirming a pure additive slice.

## Part A — Data Contract check (the "numbers don't match" gate) → PASS

The iteration registers ONE new value — **Factor-Lab multi-factor combination cohorts** — in the blueprint Data Contract (canonical module `app.engine.research:compute_factor_combination`, canonical endpoint `GET /api/research/factor-combination`). Checked against the objective FAIL rules:

1. **No duplicate computation of an existing value.** `compute_factor_combination` (`research.py:396`) and its pool builder `_combination_observations` (`research.py:317`) are **SELECT-only**: they read stored `ForwardReturn` rows and the `ScannerResult` factor values via the existing `_extract_factor_value` + `parse_factor_source`, read **verbatim**. Membership is pure set arithmetic (`_quantile_cutoff` nearest-rank + AND-intersection); stats reuse the existing downside-only `_risk_adjusted` (`research.py:78`). It recomputes **no factor and no return**.
   - **Read-only keystone verified in source:** `research.py`'s entire external import surface is `from app.config import Config, get_config, parse_factor_source`, `from app.engine.forward_testing import SURVIVORSHIP_BIAS_LABEL` (a label constant, not a compute fn), and `from app.models import ForwardReturn, ScannerResult, ScannerRun` (`research.py:39–41`). It imports **no** scoring/scanner/regime/patterns engine. The strings `run_scan`/`score_stocks`/`backfill`/`forward_return`/`detect_*`/`score_regime` appear in the file **only inside docstrings asserting they are not called** (lines 15, 405) — there are zero call sites.

2. **Not a duplicate/synonym of the single-factor value.** The single-factor decile/rank-IC/regime value keeps its canonical home (`compute_factor_lab` / `GET /api/research/factor-lab`) — that function and its helpers are byte-unchanged this iteration. The combination cohort is a genuinely **distinct** value: it requires a *list* of factors + per-factor quantile conditions (inputs the single-factor endpoint cannot express) and produces a combined-AND cohort vs baseline vs singles. This is the same "distinct read-only slice of the same stored returns" pattern already blessed for the J-19 attribution slices and the J-27 regime split. Not a re-derivation of any existing score/return/bucket.

3. **Canonical serving path, no recompute in the view.** The API route (`api/research.py:66`) validates inputs and returns `compute_factor_combination(...)` **verbatim** — it computes nothing itself. It is the single path that produces this value; `grep` finds no other endpoint computing combination cohorts.

4. **No non-canonical client source / no client recompute.** The frontend's `fetchFactorCombination` (`api.ts`) hits `/api/research/factor-combination` (the registered canonical endpoint). `CombinationTable`/`CohortCell` (`page.tsx`) **re-format the payload only** — every figure (`mean_return`, `median_return`, `hit_rate`, `risk_adjusted`, `n`, `low_sample`) is read from the response and rendered through the existing `fmtPct`/`fmtRatio`/`returnClass`/`SampleSize` display helpers (allowed re-format). The frontend chooses *which* conditions to send; it never computes a cohort statistic.

5. **No unregistered value.** The value is registered in the blueprint Data Contract by this iteration's additive edit (one canonical module + one serving endpoint), so no A5 "unregistered value" WARN applies.

6. **Read-only / downside-only honesty preserved (invariant #9).** `risk_adjusted` reuses `_risk_adjusted` (downside deviation, MAR=0 — never total volatility); empty/low-sample cohorts yield `None`/`low_sample=true` and render muted "NA" via `CohortCell`, never a fabricated 0. Config-driven: `min_conditions`/`max_conditions`/`quantiles`/`default_conditions` come from `config.research.factor_lab.combination`; the low-sample threshold is reused from `walk_forward.min_sample` (no new literal in calc code).

## Part B — Information Architecture check → PASS

1. **No new route / page / nav entry.** The change is a single additive section — `<CombinationLab horizon={horizon} />` rendered inside the existing `ResearchPage` component (`page.tsx:106`) on the already-approved `/research` page. The blueprint's iter-12 nav-skeleton note reads "**NO skeleton change**" and **no `blueprint.reapproval-requested` marker is written** — confirmed absent under `state/` — consistent with the diff (additive section, new endpoint serving a new value, not a new nav home).

2. **Reachability.** `/research` is an existing top-level sidebar entry (≤2 clicks, approved iter-10); the new section is reached by scrolling that page, below the regime-effectiveness table. No discoverability regression.

3. **No duplicate home.** No second page for any entity — the section extends the canonical Factor Lab home.

4. **No parallel shell.** It uses the established page shell (`Card`, `PanelTitle`, the existing `Select`/table/cell styling). No new layout or nav.

5. **One date selector preserved (J-18, invariant #5).** `CombinationLab` takes the page's shared `horizon` as a prop and adds **only** `conditions` state — no as-of/date control anywhere in the new code. `/research` remains a cross-date aggregate with no date selector. The new `factor-combination` route exposes no `as_of`/date param.

## Part C — Advisory (non-blocking)

- **Label & format consistency: good.** Cohort rows are server-labelled ("Baseline (all names)", "Combined (AND)", and single-condition labels built from payload `factor.label` + `quantile.label`); the Factor and Quantile dropdown vocabularies come from `data.factors` / `data.quantiles` (config-driven — no hard-coded frontend list, honoring the iter-9 config-driven-vocabulary lesson). Returns use `fmtPct`, the risk-adjusted ratio uses `fmtRatio`, matching the existing decile/regime tables; the column is explicitly labelled "Risk-adjusted (downside)" with an honest note that return/MAE arrives with J-29.
- **Test-fixture coupling is benign.** The `test_sectors.py`/`test_themes.py`/`test_config_engine.py` changes only add the now-required `combination` sub-block to their shared synthetic `Config` fixtures so boot validation passes — no contract value is recomputed in a test path.

## Conclusion

A clean additive iteration. The new combination-cohort value is derived once by the canonical `compute_factor_combination` (SELECT-only, reusing the verbatim-read factor values, the stored returns, and the existing downside-only `_risk_adjusted`), served by the single canonical `GET /api/research/factor-combination`, and re-formatted (never recomputed) by the frontend. No existing contract value is recomputed or served from a new path; the single-factor `compute_factor_lab` value is untouched. No new route/nav/home and no new date state are introduced (J-18 holds), and the blueprint Data Contract + IA homes were proactively extended to register the value. No objective violation under Step 1 or Step 2.

**Verdict: COHERENCE-PASS**
