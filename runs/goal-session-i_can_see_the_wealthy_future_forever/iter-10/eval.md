# Iteration 10 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-25 landed cleanly: the **Research** sidebar home (`/research`) now hosts its first lab — the **Factor Lab** — a read-only decile sort (D1…D10 raw mean forward return + a downside-risk-adjusted column + n per decile) plus a Spearman **rank-IC**, all config-driven and derived once from the already-stored forward returns + factor values. This establishes the new nav home and the read-only lab-analytics seam every later lab (J-26/J-27/J-29/J-30/J-31) reuses. Every critical anti-goal seam was verified directly in source (read-only SELECT-only; downside-only risk; config-driven catalog; J-18 no date state); COHERENCE-PASS; diff purely additive so the required-still-passing set cannot have regressed. 8 journeys remain failing (J-22/23/24 data-walled; J-26/27/29/30/31 now-unblocked unbuilt labs) → not GOAL_ACHIEVED, clear progress + tractable next work → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-25** (target) | failing | **passing** | `…iter-10-evidence/UT-02-default-factorlab.png` + `UT-05-atr-60d.png` (viewed directly: decile table + rank-IC render, re-point +0.00→+0.16 on factor+horizon change); source: `research.py:154-181` SELECT-only; patch-to-raise keystone + consistency-invariant tests |
| J-09 (req) | passing | passing (re-verified) | `…iter-10-evidence/UT-15-system-health.png` — by-bucket/excess/control-group still render; shares the stored forward-return pool read-only |
| J-01 (req) | passing | passing (re-verified) | `…iter-10-evidence/UT-14-sidebar-dashboard.png` / `UT-15` — dashboard + full 11-item sidebar incl. Research |
| J-18 (req) | passing | passing (re-verified) | `…iter-10-evidence/UT-13-asof-ignored.png` — /research adds no date state (source: useState={factor,horizon,state}); changing global as-of leaves data byte-identical, zero `as_of` requests |
| J-12 (req) | passing | passing (carried) | methodology config catalog untouched by the additive diff (only existing-file edit is the additive sidebar NavItem) |
| J-15 (req) | passing | passing (carried) | no new per-request recompute — lab endpoint is SELECT-only; snapshot-served read path unchanged in the diff |
| J-19 (req) | passing | passing (carried) | `_attribution_slices` (forward_testing.py) untouched; the lab is a separate registered Data-Contract value |
| J-02–J-08, J-10, J-11, J-13, J-14, J-16, J-17, J-20, J-21, J-28 | passing | passing (carried) | additive /research diff → no scoring/snapshot/existing-endpoint change → no regression possible |
| J-22, J-23, J-24 | failing | failing (carried, out of scope) | externally Yahoo-429 data-walled — do NOT autonomously retry |
| J-26, J-27, J-29, J-30, J-31 | failing | failing (carried, **now unblocked**) | unbuilt `/research` labs; the home + read-only seam now exist (iter-10); compute-only, no new nav re-approval |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Research lab is read-only, honest & not predictive | OK | `research.py` issues only `select(ForwardReturn)`/`select(ScannerResult)`; reads `realized_return` + factor value verbatim; no `run_scan`/`score_stocks`/`forward_return`/`detect_*` (patch-to-raise keystone). Survivorship + descriptive caveat banner shown (UT-08). |
| Risk-adjusted must not conflate up/down volatility | OK | `_downside_deviation = sqrt(mean(min(r,0)**2))` (MAR=0); NA when dd==0 / n<2 — never total stdev. Dedicated helper, no `forward_testing` stdev reuse. |
| No recompute in the read path | OK | Single canonical endpoint `GET /api/research/factor-lab` returns `compute_factor_lab` verbatim; frontend re-formats only. Consistency invariant: pooled lab mean == `compute_forward_aggregates.overall.mean_return`. |
| Single source of truth | OK | New value (decile/IC aggregation) registered in blueprint Data-Contract (`blueprint.md:162`); factor values keep their `scoring`→`scanner_results` home, returns keep `forward_testing`→`forward_returns`. |
| No magic numbers | OK | `deciles:10` + 8-factor catalog in `config.research.factor_lab`; `test_no_magic_numbers` scans `research.py` + enforces the `deciles:10` sentinel; `ConfigError` boot validators (deciles≤1 / dup key / unresolvable source). |
| Honest limitations surfaced | OK | survivorship-bias + universe-relative + descriptive labels render verbatim from payload; low-sample deciles carry `low_sample` flag + n (NA path unit-tested; not seed-observable, honest). |
| No fabricated data | OK | factor-NULL observations excluded; empty/low-sample → honest n + NA, never a fabricated bucket; all-NA factor → n=0 empty table. |
| Exactly one date selector (J-18) | OK | /research has no `useAsOf`/date state (grep NONE); provably ignores global as-of (UT-13). The historical minor violation stays RESOLVED. |
| No order/execution path | OK | grep for broker/order/execute/capital = NONE in the new engine/api/page. |
| No lookahead | OK | N/A to this read-only aggregation; reads stored returns/factors, computes no as-of score. |

## Next-Step Recommendation

**full** depth. Target the next compute-only `/research` lab on the seam just established:

- **Primary — J-27 (regime-conditioned factor effectiveness):** the smallest direct extension of J-25 — add a `regime` field to each observation from the stored `scanner_runs.regime_label`, then split the existing decile table / rank-IC / top-minus-bottom-decile spread by regime, with honest per-regime n/NA. Reuses `compute_factor_lab`'s read-only observation builder + the `/research` page shell. No nav re-approval (additive section under the approved home); not data-walled.
- **Alternative — J-26 (multi-factor combination cohorts):** intersect two/three factors' top/bottom quantile membership; report the cohort's raw + risk-adjusted return, hit-rate, n vs the unconditional baseline and single-factor cohorts.
- **Defer J-29 (event study):** needs the post-snapshot daily high/low excursion path (MAE/MFE) extracted first — a larger lift. Then **J-30** (extend the volatility family already seeded by `atr_pct` with HV / contraction / downside-semivol + regime split) and **J-31** (synthesis: lab evidence → leaderboard filter → detail).
- Keep verifying the read-only seam in source on each new lab (no recompute) and de-dup evidence by sha256 — this remains a verify-by-source session (no `-audit.md` handoff was produced again this iter).
- Do **NOT** autonomously retry J-22/J-23/J-24 — the Yahoo-429 wall persists; J-22 auto-heals via its committed runbook only on operator confirmation of a reachable no-key egress.

## Halt Justification (if halting)

Not halting — CONTINUE. Progress was made (J-25 newly passing) and tractable failing journeys remain with a clear, non-data-walled, no-approval-needed next target (the remaining `/research` labs over the now-established read-only seam). Not GOAL_ACHIEVED (8 journeys still failing). Not REGRESSION (nothing prior-passing regressed; no critical anti-goal violated; COHERENCE-PASS). Not STALLED (clear journey progress + identifiable productive next work).
