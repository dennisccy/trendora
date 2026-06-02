# Iteration 14 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-29 (the **Setup & Pattern Lab — event study**) landed cleanly on the approved `/research` home, along with the stored, lookahead-free, append-only **MAE/MFE excursion path** it depends on. This was the predicted iter-13 target and the last large autonomous lift before the J-31 synthesis. I verified every critical seam **in source and live** (not from the handoff): the read-only consistency invariant holds **exact to 1e-12** for a setup and both patterns, MAE/MFE are computed once on the forward-side INSERT with `forward_return`'s exact no-lookahead NA gate, and both criticals (J-06 byte-identical, J-07 Risk-Off→Actionable=0) re-verified green after the DB regen. **27/31 journeys passing, 4 failing** (J-22/J-23/J-24 externally Yahoo-429 data-walled; J-31 unbuilt — the next target). Not GOAL_ACHIEVED (4 failing); not REGRESSION (nothing prior-passing regressed, COHERENCE-PASS); not STALLED (clear progress + identifiable next work).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-29** (target) | failing | **passing** | UT-02-03-breakout-watch / UT-05-pullback-pattern / UT-06-vcp-lowsample-NA; evaluator live consistency-invariant + read-only + J-18 cross-checks |
| J-06 (critical, post-regen) | passing | passing (re-verified live) | TC-17; live `/api/stocks` NVDA == `/api/stocks/NVDA` byte-identical (47.48/E·66.24/D·33.79/E·Avoid·rank65) |
| J-07 (critical, post-regen) | passing | passing (re-verified live) | TC-16; live `/api/runs` both Risk-off runs (score 6.3, 8.34) → Actionable=0 |
| J-09 | passing | passing (re-verified live) | TC-18; live `/api/system-health` all panels present (by_bucket/setup/regime/vcp/control_group/attribution) |
| J-14 | passing | passing (re-verified) | TC-18 Backtest scorecard renders post-regen |
| J-16 | passing | passing (re-verified live) | UT-06; ES vcp pooled mean == by_vcp[VCP] exact (0.03184…, n=27) |
| J-18 (principal risk) | passing | passing (re-verified source+live) | UT-13; endpoint has no `as_of` param, `?as_of` → sha-identical, zero ES requests on toggle |
| J-25 / J-26 / J-30 | passing | passing (re-verified) | UT-14 Factor + Combination + volatility-family labs re-point; DOM order Factor→Combination→Event-Study |
| J-27 / J-28 | passing | passing (carried + live) | `_regime_effectiveness` untouched; by_pullback live, ES pullback mean == by_pullback exact (−0.00270, n=163) |
| J-01–J-05, J-08, J-10–J-13, J-15, J-17, J-19–J-21 | passing | passing (carried) | additive forward-side+research diff; their paths untouched |
| J-22 / J-23 / J-24 | failing | failing (out of scope) | externally Yahoo-429 data-walled — do NOT autonomously retry |
| J-31 | failing | failing (out of scope) | UNBUILT — the explicit next target (iter-15) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | `forward_excursions` slices `bars_after_list[:horizon]` (date > D), unchanged when later bars removed; same NA gate as `forward_return` |
| Snapshots immutable / append-only | OK | mae/mfe are new `Optional[float]` columns on the separate `forward_returns` table, INSERTed once via `_insert_run_forward_returns`; no `scanner_runs`/`scanner_results`/`*_scores` UPDATE |
| Single source of truth / No recompute in read path | OK | `_event_study_members` is SELECT-only (ForwardReturn/ScannerResult/ScannerRun), reads stored values verbatim; consistency invariant exact to 1e-12 (ES mean == `compute_forward_aggregates` cohort mean) — recomputes nothing |
| Research lab read-only & not predictive | OK | forbidden-call grep hits only docstrings; patch-to-raise keystone passes; descriptive caveat shown |
| Risk-adjusted must not conflate up/down vol | OK | `return_per_downside_dev` (mean/downside-dev, MAR=0) + `return_per_mae`; no total-vol "Sharpe"; NA when no downside / mean\|MAE\|==0 / n<2 |
| Honest forward-test for partial windows | OK | default Actionable n=2 + vcp n=27 → low_sample/NA; 3 empty regimes → NA + n=0; best_exit None on all-low-sample |
| No fabricated data | OK | low-sample/empty cohorts render NA + honest n in every table + the error state; MAE/MFE NA (no row) when < horizon post-bars |
| No magic numbers | OK | `subject_catalog` from `ALL_STATUSES` + `config.patterns` keys + methodology labels; min_sample/horizons from `walk_forward`; `test_no_magic_numbers` green |
| Risk-Off gates Actionable (critical) | OK | re-verified live after regen: both Risk-off runs Actionable=0 |
| Exactly one date selector | OK (RESOLVED holds) | new section adds no date state; endpoint no `as_of`; `?as_of` sha-identical |
| No order/execution path | OK | none added; diff is research/forward-test only |
| No secrets in source | OK | none added |

COHERENCE: **COHERENCE-PASS** (no Step-1 data-contract or Step-2 information-architecture violation; both new values registered in the blueprint, computed once, read verbatim). No GOAL_ACHIEVED veto, but GOAL_ACHIEVED is independently blocked by the 4 failing journeys.

## Next-Step Recommendation

**Full** depth, target **J-31 (synthesis — the last buildable journey).** The cross-page travel: lab evidence (Factor Lab J-25/26/27/30 + the new event study J-29, all now built) → `/stocks` leaderboard filter → Stock Detail, reading only canonical stored values, with weak/low-sample shown as NA. It is compute-only over the existing seed, lives on already-approved surfaces (no nav re-approval), and is not data-walled.

- **Scope caveat (iter-15 decomposer must heed):** J-31 step 4 ("open one on Stock Detail **across timeframes**") intersects the **data-walled, unbuilt J-24** (timeframe selector). Scope J-31's acceptance to the **canonical daily timeframe** (which works) and treat the intraday timeframes as honestly coverage-limited — the acceptance centers on the lab→filter→detail travel reading canonical values, not on the intraday selector. Do not let the J-24 data wall block J-31.
- **Keep verifying the read-only seam in source** on the synthesis surface (it should add no new computation — only navigation/cross-linking + filters reading stored values); de-dup browser evidence by sha256.
- **Do NOT autonomously retry J-22/J-23/J-24** — the Yahoo-429 wall persists; J-22 auto-heals via its committed finish runbook only on operator confirmation of a reachable no-key egress.

## Halt Justification (if halting)

Not halting — verdict is CONTINUE. (For forward planning: after J-31 lands, **GOAL_ACHIEVED is NOT autonomously reachable** while J-22/J-23/J-24 stay externally Yahoo-429 data-walled. Expect either operator egress confirmation, or a correct **STALLED** on the data-walled remainder once J-31 is green — at which point the user would edit `docs/goal.md` scope or confirm a reachable feed.)
