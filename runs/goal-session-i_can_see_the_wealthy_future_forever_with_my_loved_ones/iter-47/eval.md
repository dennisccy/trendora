# Iteration 47 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-47 (the `--acknowledge-regression` fix of the iter-46 heavy-lab MemoryError) streamed/column-projected the seven unbounded `select(ForwardReturn)…all()` reads and reordered the two event-study builders. On primary live evidence this RESTORES J-29 (event-study) and J-26 (factor-combination) to passing and keeps J-77/J-91/J-103 passing — real progress, zero newly-broken prior-passing journeys. But the fix is INCOMPLETE: J-25 (Factor Lab) still HTTP-500s with a `MemoryError` because the ScannerResult side of `_factor_observations` (research.py:216) was left as an unstreamed `.all()` over ~609K rows, and factor-lab is uncached so it recomputes every request. J-25 remains a failing buildable Must-have that goal.md (J-105) makes non-data-dependent and non-haltable → not GOAL_ACHIEVED; tractable next step identified → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-29 (Setup & Pattern event study) | regressed | passing | reports/qa/.../iter-47-evidence/UT-01-result.png |
| J-26 (Factor Lab — multi-factor composite) | regressed | passing | reports/qa/.../iter-47-evidence/UT-07-result.png |
| J-25 (Factor Lab — decile / rank-IC) | regressed | regressed (still failing — HTTP 500 MemoryError, research.py:216) | reports/qa/.../iter-47-evidence/UT-04-fail.png |
| J-104 (research-labs reliability) | partial | partial (5/7 labs reliable; factor-lab still OOMs) | reports/qa/.../iter-47-evidence/UT-04-fail.png |
| J-77 (Regime × Setup × Pattern) | passing | passing | reports/qa/.../iter-47-evidence/UT-08-result.png |
| J-91 (Downtrend Opportunity) | passing | passing | reports/qa/.../iter-47-evidence/UT-10-result.png |
| J-103 (Severity-velocity × Regime) | passing | passing (carried; dev live-probe HTTP 200; UT-17 as-of) | reports/qa/.../iter-47-evidence/UT-17-asof-panel.png |
| J-51 / J-63 / J-65 (samples N= coherence) | passing | passing (event-study N=455→455 live; factor-lab chip blocked by J-25) | reports/qa/.../iter-47-evidence/UT-03-result.png |
| J-06 (single source) | passing | passing (NVDA leaderboard==detail 40.37/52.85/39.17) | UT-16 (page text) |
| J-13 (browse as-of) | passing | passing (?asof=2026-05-15 historical, 73.26/28.09) | reports/qa/.../iter-47-evidence/UT-17-asof-panel.png |
| J-18 (one date control, CRITICAL) | passing | passing (single calendar + step arrows; no second date state) | reports/qa/.../iter-47-evidence/UT-17-asof-panel.png |
| J-72 / J-32 (research point-in-time / cache contract) | passing | passing (carried; streamed builder byte-identity tested green) | dev byte-identity tests |
| J-90 (recovery-turn edge) | passing | passing (carried; served HTTP 200) | reports/qa/.../iter-47-evidence/UT-10-result.png |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | Pure read-path streaming refactor; no scoring/forward-return formula touched. |
| Snapshots immutable | OK | No snapshot/rebuild path touched (no `kind:rebuild`). |
| Single source of truth | OK | Column-projection reads stored values verbatim; coherence PASS confirms no recompute / no new endpoint. |
| No magic numbers | OK | `yield_per` batch sourced from new config `research.read_batch_size` (boot-validated ≥1); review confirms no inline batch literal in CALC_FILES. |
| No fabricated data | OK | The failing Factor Lab shows an explicit "Backend unavailable — No figures are shown rather than fabricated values" banner (UT-04-fail.png). Honest failure, not fabrication. |
| No order/execution path | OK | Not touched. |
| No secrets in source | OK | Not touched. |
| Risk-Off gates Actionable | OK | Snapshot-served fast path unaffected by the heavy-lab path; J-07 invariant intact. |

No anti-goal violation. The MemoryError is a resource/code defect (an honest HTTP 500), not an anti-goal breach.

## Next-Step Recommendation

iter-48 FULL — finish J-105 by streaming/column-projecting the ScannerResult reads in the UNPRUNED observation builders, **factor-lab (J-25) first**:
- `_factor_observations` (research.py:216) — replace `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` with a column-projected `yield_per`-streamed read (project only the ticker + per-factor value columns the decile/rank-IC study reads), keeping every figure byte-identical. This is the genuine OOM site (live backend log: `MemoryError` at research.py:216, ~609K ScannerResult rows; factor-lab is UNCACHED so it recomputes every request).
- `_combination_observations` (research.py:421) — the same unstreamed `select(ScannerResult)…all()` is a latent cold-miss OOM, currently masked only by the J-104 EventStudyCache hit; stream it too so a cold miss never reintroduces the failure.
- (Audit) confirm the other restored builders' ScannerResult reads are bounded/streamed or cache-served; `_recovery_turn_observation_set` (research.py:1770) is run-id-bounded to signal dates and uses `.order_by`, not the unbounded `.all()` — already bounded.

Required-still-passing for iter-48: J-29/J-26/J-77/J-91/J-103 (must STAY passing — re-render on a quiet, warmed, single-fetch-at-a-time backend), J-51/J-63/J-65 (factor-lab N= drill-down now testable once J-25 serves), J-06/J-18 (CRITICAL)/J-07 (CRITICAL), J-72/J-32 (byte-identity of the streamed builders). Suite-gate: pump nohup-async; gate the eventual GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight suite. Evidence-hygiene: PLAN the Playwright fallback up front; md5sum the dir FIRST; NEVER run the full backend suite concurrently with the heavy-lab probes (its RAM pressure exacerbated the factor-lab OOM this iter); fetch one heavy lab at a time; for the factor-lab cold compute over ~598K rows allow ~50-60s before the first cache hit. After J-25 flips to passing with byte-identical figures + a flushed-GREEN suite + COHERENCE-PASS + zero regression, the next evaluation is a sound GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).
