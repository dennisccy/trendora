# Iteration 18 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-26 landed exactly as the operator re-scope (commit `d723133`) requires: the Factor-Lab **Combined**
cohort is now a **non-empty composite percentile-rank blend** (config-weighted, top config-quantile)
that scales to all **11** catalog factors, with the perpetually-0/NA strict AND-intersection demoted to a
clearly-labelled secondary `strict_overlap` cohort (honest NA + n when empty). I verified every critical
seam in SOURCE (read-only, composite-non-empty, J-18 no-date-state, no DB regen, no magic numbers), not the
QA table. **J-26: partial → passing** (28/32 journeys passing). Not GOAL_ACHIEVED — **J-32** (Research
as-of toggle) is a buildable, unbuilt must-have (iter-19 target), so the loop continues.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-26** Factor Lab — multi-factor composite combination cohort | **partial** | **passing** | source: `research.py` `_composite_scores`/`compute_factor_combination` (top config-quantile rank-blend); unit: `test_api_research.py:157-163` (composite n>0, ≥min_sample, low_sample False, mean≠None) + `:221` (strict NA AND composite populated on opposing-extremes); browser UT-02/UT-08 (`UT-08-composite-populated-strict-NA.png`) |
| J-25 Factor Lab decile/rank-IC | passing | passing (re-verified) | browser UT-11 (`UT-11-factorlab-decile-rankic.png`) — decile D1–D10 + Rank-IC re-point on factor/horizon change; TC-16 |
| J-27 regime-conditioned effectiveness | passing | passing (re-verified) | browser TC-16 (`TC-16-j25-j27-j30-repoint.png`) — by-regime rank-IC table renders |
| J-30 volatility factor family | passing | passing (re-verified) | browser TC-16 — volatility-family present with data |
| J-18 One date control (no duplicate) — **principal anti-goal risk** | passing | passing (re-verified) | source: `api/research.py` 0 `as_of`; `CombinationLab` takes only `horizon`; `test_factor_combination_no_date_control_present`; browser UT-13/TC-15 — byte-identical, 0 `?as_of=` reqs, exactly 1 date `<select>` (in `<header>`, not `<main>`) |
| J-06 Score consistency | passing | passing (structural) | `git diff HEAD` of scoring/scanner/buckets/snapshot_serving = EMPTY → byte-identical, no DB regen |
| J-07 Risk-Off gates Actionable | passing | passing (structural) | scoring/scanner/regime untouched (git-verified) → gate byte-identical, no DB regen |
| J-29 Setup & Pattern event-study lab | passing | passing (re-verified) | browser UT-12 — event-study table re-points (Actionable n=2 → VCP n=27), honest NA + leaderboard link |
| J-31 synthesis travel | passing | passing (carried) | `/research`+`/stocks`+`/stocks/[ticker]` serving paths untouched (additive diff) |
| J-01–J-05, J-08–J-17, J-19–J-21, J-28 | passing | passing (carried) | additive read-only `/research` diff (12 files, scoring/snapshot path empty) → no regression possible |
| J-22 expanded universe (~500) | failing | failing (NON-HALTING) | data-walled (Yahoo-429); re-scoped goal records honestly blocked NA; not re-probed (spec forbids) |
| J-23 intraday multi-timeframe bars | failing | failing (NON-HALTING) | unbuilt + data-walled; honestly blocked NA |
| J-24 chart timeframe selector | failing | failing (NON-HALTING) | unbuilt (depends on J-23); honestly blocked NA |
| **J-32** Research as-of toggle | failing | failing (out of scope) | confirmed still unbuilt: `api/research.py` has ZERO `as_of` (grep clean). **iter-19 target (full)** |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Research lab read-only, not predictive | OK | Forbidden-call grep (`run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime`) hits ONLY docstrings in `research.py`; imports only `SURVIVORSHIP_BIAS_LABEL`/`_distribution`/`_mean_or_none` (constants + pure stats). Composite reads `obs["values"][key]` (stored factor values) + `pool[i]["return"]` (stored returns) via SELECT-only `_combination_observations`. A deterministic rank-blend (reuses `_average_ranks` + `_quantile_cutoff`) — same read-only class as the J-25 decile sort; NOT a fitted/ML model. Read-only keystone test (patch-to-raise) covers the composite path. |
| Risk-adjusted honest (downside-only) | OK | Composite/strict reuse `_cohort_stats` → unchanged `_risk_adjusted = mean / _downside_deviation` (sqrt(mean(min(r,0)²)), MAR=0); NA when no downside / n<2 — never total vol. |
| No magic numbers | OK | `config.yaml` `composite` block (`quantile: quintile`, `weighting {scheme: equal, default_weight: 1.0}`), `max_conditions 3→11`; weights normalized in-engine from `default_weight` (no `1/k` literal); `CompositeCfg`/`CompositeWeightingCfg` boot-validate; `test_no_magic_numbers` passes. |
| No fabricated data | OK | Empty/low-sample cohort → NA + n (live UT-08: `strict_overlap` n=0 ⚠ NA/NA/NA/NA; composite populated), never a fabricated 0. |
| Exactly one date selector (**principal risk**) | OK (resolved, re-confirmed) | No `as_of` param on `/research`; no date `useState` added (`CombinationLab` takes only `horizon`); browser exactly 1 date `<select>`, 0 `?as_of=` requests. |
| Single source of truth | OK | Same module `compute_factor_combination`, same endpoint `GET /api/research/factor-combination`; old `combined` key cleanly removed across engine/`api.ts`/`page.tsx` (no back-compat alias, no dead code). |
| No DB regen / snapshot immutable | OK | `git diff HEAD` of scoring/scanner/regime/patterns/buckets/forward_testing/snapshot_serving = EMPTY. |
| Coherence | COHERENCE-PASS | No veto. Textbook refinement of an existing Data-Contract value (same module/endpoint/page, read-only). |

## Next-Step Recommendation

**iter-19 → J-32 (full depth) — the last buildable journey.** Add an **All-history ⟷ As-of-date MODE** to
the three `/research` lab endpoints (`compute_factor_lab` / `compute_factor_combination` /
`compute_event_study`), reusing iter-17's `asof_date ≤ D` membership-filter seam (the
`compute_forward_aggregates(..., as_of=D)` pattern — a `ScannerRun.asof_date <= as_of` join on the
SELECT-only observation builders; `as_of=None` ⇒ byte-identical all-history). **It MUST be a MODE reading
the single global as-of control — NO second date state** (J-18 is again the principal anti-goal risk: the
toggle is a mode, not a date picker). Full depth justified: critical read-only research path on three lab
functions + the J-18 anti-goal surface + real unit tests (as-of filter correctness, no >D leak, no second
date state, low-sample NA at early dates) + coherence/closure. No nav change (lives on the approved
`/research` home) → no blueprint re-approval. After J-32 lands and nothing regresses → **GOAL_ACHIEVED is
reachable** on the buildable set: J-22/J-23/J-24 are honestly blocked (NA) and **non-halting per the
re-scoped goal** — do NOT autonomously re-probe them.

## Halt Justification (if halting)

N/A — not halting. CONTINUE: progress made (J-26 partial → passing) and a concrete, tractable next step
exists (J-32 — compute-only over the seed, not data-walled). No coherence veto (COHERENCE-PASS); no
prior-passing journey regressed; no critical anti-goal violated.
