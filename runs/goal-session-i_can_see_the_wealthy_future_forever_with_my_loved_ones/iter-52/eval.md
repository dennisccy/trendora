# Iteration 52 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-109 (Factor Lab all-horizon paired forward-return + max-drawdown columns) is genuinely newly passing on live, evaluator-VIEWED evidence — the full-mode QA agent captured fully-hydrated frames of the all-factors table, the expanded all-horizon decile grid, and a byte-distinct view-transform sort. The change is anti-goal-clean (max-drawdown read VERBATIM from the stored J-86 column, no new endpoint/table, config-sourced horizons, bounded streamed read), COHERENCE-PASS, review PASS, QA PASS (994 passed/0 failed). This is NOT a GOAL_ACHIEVED candidate: J-110/J-111/J-112 — three new buildable, non-data-dependent Must-haves added in commit ab7de8c — remain unbuilt with no positive evidence, so the every-buildable-Must-have gate is unmet → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-109 (target) | unknown (new) | **passing** | reports/qa/goal-…-iter-52-evidence/TC-01-initial-load.png, TC-07-expanded-decile.png, TC-09-before/after-sort.png |
| J-110 (new) | — | unknown (queued, not built) | none |
| J-111 (new) | — | unknown (queued, not built) | none |
| J-112 (new) | — | unknown (queued, not built) | none |
| J-107 | passing | passing (re-verified live TC-17) | TC-01-initial-load.png |
| J-06 (CRITICAL) | passing | passing (TC-18 single-source) | TC-01-initial-load.png |
| J-18 (CRITICAL) | passing | passing (TC-10: 0 native date inputs) | TC-01-initial-load.png |
| J-07 (CRITICAL) | passing | passing (994-passed suite; no gate change) | — |
| J-25 | passing | passing (suite + byte-identity) | — |
| J-26 | passing | passing (suite + diff confinement) | — |
| J-29 | passing | passing (suite + diff confinement) | — |
| J-104 | passing | passing (cold compute 47.2s/517MB, no OOM) | — |
| J-105 | passing | passing (bounded yield_per (run_id,id) stream) | — |
| J-86 | passing | passing (max_drawdown read verbatim, store path untouched) | — |
| J-51 | passing | passing (TC-08 N= chip exact params + TC-14) | TC-08-decile-table-scroll.png |
| J-65 | passing | passing (suite count-coherence + TC-14) | — |
| J-22/J-23/J-24 | unknown | unknown (data-walled, NON-VETOING) | none |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth | OK | max_drawdown read VERBATIM from stored forward_returns.max_drawdown (J-86) via _mean_or_none; same compute_factor_lab/_deciles builders; 14 byte-identity tests; coherence Part A confirms no new computing module |
| No recompute in read path | OK | Served from derived-once EventStudyCache + _dataset_version; schema token allh-mdd-v1 folded into the key (old-schema rows MISS-then-prune, unit-tested against a real populated old row) |
| No lookahead | OK | as_of cutoff logic unchanged; forward returns/max_drawdown read from stored bars dated > D; no scoring/FR-compute change |
| No magic numbers | OK | Horizons from config.walk_forward.horizons; default_horizon=20 from config; test_no_magic_numbers green (TC-16) |
| Honest forward-test for partial windows | OK | test_paired_max_drawdown_is_populated_and_honest_na + test_zero_n_factor_is_honest_na_not_fabricated green; low-sample deciles show NA + n |
| No fabricated data | OK | Honest NA, no synthesized figures |
| Honest limitations surfaced | OK | Survivorship-bias descriptive banner present in TC-01/TC-07/TC-09 frames |
| No order/execution path | OK | No brokerage/order code in the diff (research read-surface only) |
| Exactly one date selector | OK | TC-10: 0 native input[type=date]; only the global as-of selector; As-of toggle is a mode |

Prior anti-goal record: the lone ever-recorded violation (iter-20 minor magic-number) stays resolved since iter-21. No new violation this iter (diff inspected: no new table=True, no new endpoint, no unbounded select(...).all() over ForwardReturn/ScannerResult).

## Next-Step Recommendation

iter-53 FULL — build **J-110** (Research — Regime Lab at the new `/research/regime-lab`): a derived-once cached cross-sectional study of the stored forward_returns (realized return + J-86 max-drawdown) grouped by the stored regime label and regime-score deciles, per config horizon, mirroring the Factor Lab. Required heeds: it is a new heavy cross-sectional lab on the OOM-sensitive read path → keep the J-105 streamed/column-projected observation builder (no unbounded `.all()`, ScannerResult ordered `(run_id, id)`); fold a schema token into a new EventStudyCache cohort kind (iter-38/39/44 cache-schema lesson); reuse the existing event_study_cache table or register any genuinely-new table in test_db.py's expected-tables guard (iter-12/20 trap); add a samples cohort kind with N= count-coherence (J-51/J-65); it adds a new tile + lazy sub-route under the existing /research hub — a NAV-SKELETON add, so the decomposer MUST file blueprint.reapproval-requested. Required-still-passing: J-109 (this iter), J-25/J-26/J-29/J-107/J-104/J-105/J-86/J-51/J-65, J-06/J-18/J-07 (CRITICAL). Then iter-54=J-111, iter-55=J-112. Only after J-109..J-112 all pass with a flushed-GREEN full suite (`0 failed, EXIT 0`, nohup-async; never block the evaluator) + COHERENCE-PASS + zero regression is the next evaluation a sound GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108). Evidence-hygiene for iter-53 QA: ensure BOTH the frontend and backend stay up for the dedicated browser-qa-agent step (this iter that step SKIPPED because servers were torn down before it ran — only the QA agent's earlier live run captured evidence); PLAN the Playwright fallback up front; md5sum the dir first; run heavy-lab probes single-fetch-at-a-time on a quiet warmed backend.

## Halt Justification

Not halting — verdict is CONTINUE. Progress was made (J-109 newly passing), zero regressions, COHERENCE-PASS, and three tractable unbuilt buildable Must-haves (J-110/J-111/J-112) remain.
