# Iteration 12 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-26 (Factor Lab multi-factor combination cohorts) landed as a textbook-clean additive slice and is **newly passing** — verified at the API, in browser, and in source. The user can now compose 2–3 factor conditions (each a catalog factor at its top/bottom quantile) and read the Combined-(AND) cohort beside the unconditional baseline and each single-factor cohort (mean / median / hit-rate / downside-risk-adjusted / n), with honest NA on a thin combined cohort. **25/31 must-have journeys now pass, 6 fail** (J-22/J-23/J-24 externally Yahoo-429 data-walled; J-29/J-30/J-31 unbuilt compute-only `/research` labs). Not GOAL_ACHIEVED (6 journeys failing); not REGRESSION (nothing prior-passing regressed, no critical anti-goal); not STALLED (clear progress + identifiable next work). COHERENCE-PASS gives no veto.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-26** (target) | failing | **passing** | UT-02-default-combination.png + UT-10-thin-cohort-NA.png (evaluator viewed both) + source verification of all 5 critical seams |
| J-18 (req, principal risk) | passing | passing (re-verified) | UT-15-asof-historical-byte-identical.png — as-of toggle leaves all 4 `/research` tables byte-identical, zero as_of requests; new route/section have no date state (source) |
| J-25 (req) | passing | passing (re-verified) | UT-14-factorlab-repoint.png — decile + rank-IC re-point on factor change (rank-IC +0.00→−0.04) |
| J-27 (req) | passing | passing (re-verified) | UT-14-factorlab-repoint.png — regime table 7 cols intact below decile |
| J-09, J-19, J-15, J-16, J-28, J-01, J-12 (req) | passing | passing (carried green) | additive `/research`-only diff; forward_testing/scoring/scanner/patterns/regime/snapshot_serving untouched — no regression possible |
| J-02–J-08, J-10, J-11, J-13, J-14, J-17, J-20, J-21 | passing | passing (carried green) | additive diff; respective paths untouched |
| J-22, J-23, J-24 | failing | failing (out of scope) | externally Yahoo-429 data-walled — do NOT autonomously retry |
| J-29, J-30, J-31 | failing | failing (out of scope) | unbuilt compute-only `/research` labs — now-unblockable |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Research lab is read-only, honest & not predictive | OK | `compute_factor_combination` + `_combination_observations` are SELECT-only on `ForwardReturn`+`ScannerResult` (research.py:326/330); forbidden-call grep (`run_scan`/`score_stocks`/`backfill`/`forward_return`/`detect_*`/`score_regime`) hits docstrings only (lines 12/15/405); no scoring/scanner/regime/patterns engine imported; patch-to-raise keystone passes |
| Risk-adjusted honest, no up/down conflation | OK | `_cohort_stats` reuses downside-only `_risk_adjusted = mean/downside_deviation` (MAR=0), `None` for n<2 / all-non-negative; `_downside_deviation` untouched; raw mean shown alongside; UI states return/MAE arrives with J-29 |
| No recompute in the read path | OK | endpoint returns `compute_factor_combination(...)` verbatim; frontend re-formats payload only |
| No magic numbers | OK | min/max_conditions, quantiles, default_conditions, min_sample, horizons all from config; `test_no_magic_numbers` passes (scans research.py) |
| No fabricated data | OK | factor-NULL obs excluded (research.py:342-343); empty/low-sample cohort stats all `None`/NA + honest n (research.py:372-374); UT-10 shows Combined n=0 → NA, no fabricated 0 |
| Exactly one date selector (J-18) | OK (resolved, holding) | new route has no as_of param (api/research.py:67-76); CombinationLab adds only `conditions` state (page.tsx:503), effect keyed `[conditions, horizon]` (page.tsx:520); UT-15 confirms zero as_of requests on global as-of toggle |
| Single source of truth / coherence | OK | new value computed once + served by one endpoint; no existing contract value recomputed/re-homed (COHERENCE-PASS) |

No anti-goal violation introduced. The single historical minor one ("Exactly one date selector") stays **RESOLVED** (since iter-1) and was re-confirmed holding.

## Next-Step Recommendation

**full depth, target J-30 (volatility as a return driver — the factor family).** Smallest next extension of the now-triply-proven read-only Factor-Lab seam (J-25 decile/IC + J-27 regime split + J-26 combination): extend the `config.research.factor_lab` volatility family beyond `atr_pct` (HV/20-day historical vol, VCP-style contraction, downside/semivol), each decile/IC-tested raw + downside-risk-adjusted and regime-conditioned via the existing J-27 by-regime helper, cross-validating the contraction measure against the VCP evidence.

- **Decomposer must determine up front** whether the volatility factor *values* (HV, contraction, semivol) are **already stored** on `ScannerResult`/`record_json` (then J-30 is purely additive read-only catalog entries via `parse_factor_source`, exactly like J-25/J-27/J-26 — keep it on the `/research` seam, no nav re-approval) **or** must be **added to `scoring.py`** (then it touches the critical scoring path + requires a DB regen and a re-verification of the J-07 Risk-Off→Actionable=0 gate after regen). Full depth is justified either way (real unit tests + coherence/ux-regression/closure on the critical read-only research surface — the same justification J-25/J-26/J-27 carried).
- Autonomous runway after J-30: **J-29** (event study — larger lift; needs the post-snapshot daily high/low MAE/MFE excursion path extracted first; this is where return/MAE lands) → **J-31** (synthesis; needs J-29 + J-27).
- **Strategic:** GOAL_ACHIEVED is NOT autonomously reachable while J-22/J-23/J-24 stay externally Yahoo-429 data-walled — once the labs (J-29/J-30/J-31) are done, expect either operator confirmation of a reachable no-key egress (J-22 auto-heals via its committed finish runbook) or a (correct) STALLED on the data-walled remainder. **Do NOT autonomously retry J-22/J-23/J-24.**

## Halt Justification (if halting)

N/A — not halting. CONTINUE: J-26 newly passing (progress), 6 journeys remain failing but tractable (3 unbuilt compute-only labs are clear next work; 3 are externally data-walled and correctly out of scope). No critical anti-goal violation, COHERENCE-PASS, no regression.
