# goal-mcp-loop-iter-40 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-24 / B-201's per-stock risk-budget card and leaderboard columns are correctly implemented, single-sourced, and honest. I independently re-derived the served values (gap p95/median/worst/variance-share, worst-20d, ATR%-reuse, distance-to-invalidation reframe) from the stored bars in the QA-rebuilt `trendora.db` and they **byte-match the served `record_json` to full float precision** — stronger evidence than the deferred pytest lane would have provided. Two documented gaps remain, both GAP-level (neither produces a wrong result): the 6 new `test_scoring.py` risk-budget tests were never pytest-certified (30-year fixture cost), and the "short-history renders NA" DoD item is architecturally unreachable through the resolved universe (so it was never genuinely demonstrated). The phase goal is achieved.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): "short-history NA" path is unreachable through the resolved universe**
`indicators.min_history_bars = 200` and the point-in-time resolver (`universe_resolver.resolve_members`) only admits names with ≥ 200 trailing bars ≤ D. All risk-budget windows are far smaller: `gap_window`=20 (needs 21 bars), `worst_window_days`=20 (needs 21), `semivol_window`=63 (downside-vol needs 64), invalidation `ma_period`=50 (needs 50). I scanned **all 541 rows of the latest served run (id=1, asof 2026-07-01)**: zero rows have any NA risk-budget leaf, and the minimum bar count among resolved members is **346**. Therefore no resolved member can ever render the card's "NA — insufficient history" state, and a name with < 200 bars is not resolved at all (its whole card returns `null` via `RiskBudgetCard`'s `if (!rb) return null`, not per-component NA). DoD item #2 ("a short-history name … renders NA + the reason … browser-verified") is not satisfiable with the current universe/config; QA's TC-02 "passed" only by observing that ARM in fact has ample history (i.e. it demonstrated the opposite of the intended case). The NA logic itself is correct and unit-tested at the function level (`test_overnight_gap_profile_na_when_too_short`, `test_worst_20d_window_na_when_too_short`, `test_invalidation_na_is_honest_never_fabricated_unit`) and defensively rendered — so this is a spec/reality mismatch and an unverified end-to-end path, not a behavioral defect. Not fixed (fixing would mean changing the universe floor or the spec — out of scope; would be scope creep).

**B2 — OBSERVATION (observation): `downside_vol` is served in two different units across surfaces**
`scoring.py:433` stores `risk_budget.downside_vol.value = downside_vol * 100` (a percent, e.g. NVDA `1.6054`), while the top-level `row["downside_vol"]` (the iter-13 Factor-Lab field, `scoring.py:458`) stores the raw fraction (`~0.016`). Same single underlying computation (the `downside_vol` local — no second call), scaled to percent only for card display to sit alongside ATR%/gap percents. A user cross-referencing the Factor Lab and the risk card sees numbers 100× apart for "downside volatility." Honest in both places and on different surfaces; noted only as a potential minor confusion. No change (unit scaling of one computed value is not a single-source violation).

**B3 — OBSERVATION (observation): distance-to-invalidation can render negative and is displayed verbatim**
For NVDA the served `distance_to_invalidation_pct` is **−5.87%** (price 197.58 is below its 50-DMA invalidation level 209.90 — the long thesis is already technically invalid). The value is mathematically correct (`(price − level)/level·100`, verified) and its percentile (0.824) correctly flags high danger via the `negate=True` orientation. A user could read the bare "−5.87%" without realizing it means "already below the level"; an "already breached" affordance would be clearer. Polish only — the datum is honest and correctly oriented.

### Frontend Findings

**F1 — (verified, no defect): single-source, no client recompute**
Both `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) rehydrate from the lossless `record_json` (`snapshot_serving.py:176` and `:238`). The detail card (`RiskBudgetCard`, `[ticker]/page.tsx:324`) and the five leaderboard columns (`RISK_BUDGET_COLUMNS`, `stocks/page.tsx:80`) both read `row.risk_budget?.<field>` verbatim through the single shared formatter `fmtRiskValue` (`lib/risk-budget.ts`). A grep for any risk math in `apps/frontend` (`open − prior close`, percentile math, `Math.sqrt`, `/ prior`) returns **only comments/labels** — zero client-side computation, so B-201's dominant "UI-recompute" failure mode is genuinely avoided. Leaderboard-value == detail-card-value holds by construction.

**F2 — (verified, no defect): honest, descriptive, no advice**
The card header disclaims "Descriptive only; not a recommendation." No proven-language, evidence badge, or position advice (buy/sell/trim/reduce/rebalance/target) appears anywhere in the risk-budget region (the only "proven/advice" string is a self-documenting comment asserting their absence). NA renders warn-coloured "NA — insufficient history," never a fabricated 0. Satisfies anti-goals #1/#2.

### Test Findings

**T1 — GAP (gap): the 6 new `test_scoring.py` risk-budget tests were never executed through pytest**
Confirmed by the dev handoff, the reviewer, and QA: the `loaded_engine` real-30-year-seed fixture takes 30+ min to build (the memory-noted "30y test suite slow, not the product"), so `test_risk_budget_*` (fields+percentiles, gap-p95 byte-match, worst-20d byte-match, atr/downside-vol reuse call-count, no-score-leakage) ran only inside a standalone script, not pytest. **Mitigation applied this audit:** I independently byte-matched every property those tests assert against the *stored/served* `record_json` (see §3), which exercises the real serve path end-to-end — stronger than the pytest assertions. So the behaviour is verified even though the pytest lane is uncertified. I did **not** run the slow pytest myself: the memory explicitly warns a full/concurrent pytest fork-locks this box, and the dev's own attempt ran 31+ min without completing fixture setup. Recommend a final `pytest tests/test_scoring.py -k risk_budget -v` on the next lean pass for formal certification.

**T2 — (verified, no defect): the pure-function fixture tests are exact and correct**
`test_indicators.py`'s 8 new tests ran green in the fast lane (162 passed). I hand-recomputed both fixtures: `overnight_gap_profile` (window=4) → median 3.5, p95 4.85, worst 5.0, variance-share 25.0 (the fixture sets each overnight leg = 0.5× the total return so the 0.25 share is exact, not approximate) — all match; `worst_20d_window` (window=3) → `(70/95 − 1)·100` = −26.32% (the most negative of the three trailing windows) — matches. NA/validation/mismatched-length/zero-variance paths are all covered with exact asserts.

**T3 — OBSERVATION (observation): browser-qa lane was SKIPPED (Chrome-MCP outage)**
The only browser evidence for J-24 is one qa-validation screenshot of the liquid card (`TC-01-risk-budget-card-liquid.png`). No interactive browser evidence exists for the leaderboard columns, the single-source spot-check, or the required-still-passing regression journeys (J-01/02/03/05/10/12/13/20). The regression risk is low (the diff is 395 insertions / 5 deletions, purely additive — it touches no existing score/serve/chart/evidence code path), and the reviewer's independent `test_scoring_window.py` run (4/4, real seed) proves `score_stocks` is byte-identical, but the UI-journey evidence floor (per judgment-rubric §5) is thinner than a normal full iteration.

---

## 3. Domain Assessment

The core domain logic is correct and the risk-budget bundle is genuinely single-sourced.

- **Correctness (independently verified against the served artifact).** Against the QA-rebuilt DB (copied read-only to scratchpad to avoid mutating it), for NVDA at the latest run I recomputed the risk components from the stored `daily_prices` bars and compared to the served `record_json`:

  | leaf | served | independent recompute | match |
  |------|--------|-----------------------|-------|
  | gap p95 | 2.508282505666966 | 2.508282505666966 | ✓ exact |
  | gap median | 0.8161070164469665 | 0.8161070164469665 | ✓ exact |
  | gap worst | 3.1056793673616188 | 3.1056793673616188 | ✓ exact |
  | overnight_variance_share | 28.339785564240767 | 28.339785564240767 | ✓ exact |
  | worst_20d_window | −57.94646591384358 | −57.94646591384358 | ✓ exact (full-history) |
  | atr_pct reuse | round(value,4) == risk.components.atr_pct.raw | — | ✓ |
  | distance_to_invalidation reframe | −5.868116266549786 | (price−level)/level·100 | ✓ exact |

- **No-lookahead / determinism.** Both new reads are date ≤ asof: the gap profile reads the `bars_asof_window(…, max_lookback_bars)` slice and consumes only its trailing `gap_window+1` bars; `worst_20d_window` reads `closes(bars_asof(…, asof))` (the logged full-history interpretation, `assumptions.md` iter-40). The reviewer ran `test_scoring_window.py` (4/4, 533 s) confirming `score_stocks` is byte-identical under the windowing harness — i.e. determinism and the "scores unchanged" invariant hold.

- **No score leakage (structural + behavioral).** `risk_budget` is stored additively and appears in no `cfg.scores.*.weights`; `test_risk_budget_values_ride_the_row_but_enter_no_score` forces both new indicators to 999 and asserts every score/bucket/setup/rank unchanged. The served scores (NVDA 34.24 / 52.54 / 34.64) are present and sane. The whole diff deletes only 5 lines, none in the existing score path — corroborating byte-identity.

- **Percentile orientation is correct.** `_apply_risk_budget_percentile` ranks cross-sectionally over the same as-of scan's members, negating `worst_20d_window` and `distance_to_invalidation_pct` so a HIGHER percentile always means MORE risk. I verified the negation handles the below-the-level case (NVDA's −5.87% distance → high p82 danger) correctly, and confirmed percentiles are genuinely cross-sectional (multiple distinct values across rows), not a fabricated constant.

- **Anti-goal #8 (OOM) respected.** All reads are per-symbol (`bars_asof`/`bars_asof_window`) or slices of the resident `bar_cache`; no whole-table ORM load. The bounded cadence rebuilt 90 runs (all carrying `risk_budget`) into a 561 MB DB with no OOM — not the forbidden full-universe 30-year daily backfill. Config folds both new windows into the `max_lookback_bars` guard (validated positive; fast-lane config tests green).

- **Methodology.** Three new `factor_stats` glossary terms — "overnight-gap profile," "worst 20-day window," "distance-to-invalidation %" — each carry a formula definition and (for the two windowed ones) a `thresholds` ref to the new config keys, served by the pure config-driven `build_catalog`.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT findings. All findings are GAP- or OBSERVATION-level; fixing them (changing the universe floor, re-scoping DoD #2, running the 30-year pytest lane, or relabelling display units) would be scope creep or risks fork-locking the box. Documented as known limitations instead.

---

## 5. Recommended Next Step

**Proceed to iter-41 (J-25).** The phase goal is achieved: a correct, honest, single-sourced risk-budget card + leaderboard columns whose served values I independently byte-verified. Carry these two documented gaps forward:

1. On the next lean/replay pass, run `pytest tests/test_scoring.py -k risk_budget -v` to completion to formally certify the 6 integration tests (their behaviour is already independently confirmed), and fold in the deterministic-replay lane for the required-still-passing set (the recurring iter-33/36/38/39/40 replay-lane gap noted in the spec's NOTES).
2. Record in the journey history that the "short-history renders NA" acceptance path for J-24 is architecturally unreachable while `indicators.min_history_bars = 200` exceeds every risk-budget window — it is unit-tested at the function level but cannot be browser-demonstrated, so it should not be reported as a browser-verified pass.
