# Iteration 23 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-81 (themes/sectors forward-return columns) and J-82 (RSP table NA-last sort + filters + emitted-combination drill-down + Pooled default) both landed correctly and newly pass: browser QA is a clean 23/23, the 12 targeted backend tests in `test_iter23_leaderboard_returns.py` prove the J-06 single-source byte-identity of the new forward returns to Backtest's `_leadership_returns`, and coherence is COHERENCE-PASS. **But the standing GOAL_ACHIEVED gate — a GREEN full backend suite — is NOT met:** the flushed authoritative full-suite result is `2 failed, 844 passed, 4 skipped, EXIT_CODE=1`. The two failures are STALE `served == engine_output` byte-equality guards (`test_api_engine.py::test_api_themes_equals_engine_output`, `::test_api_sectors_equals_engine_output`) that the dev did not update for J-81's legitimate additive `forward_returns` field — not a coherence break, but a red suite that blocks GOAL_ACHIEVED.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-81 (Themes/Sectors forward-return columns) | unknown (TARGET) | passing | UT-01/02/04/05/06/07/15/17/18/20/21/22; `test_iter23_leaderboard_returns.py` 8 J-81 tests (incl. themes/sectors==Backtest byte-equal, equal-weight basket, NA-at-latest) |
| J-82 (RSP table fixes) | unknown (TARGET) | passing | UT-03/08/09/10/11/12/13/14/16/19/23; `test_iter23_leaderboard_returns.py` 4 J-82 tests (every-emitted-combination coherence Episodes+Pooled+As-of, pattern=none drill-down, genuinely-invalid 4xx) |
| J-03 (Theme Leaderboard) | passing | passing | UT-17 original theme columns intact + populated |
| J-04 (Sector Leaderboard) | already_passing | passing | UT-18 original sector columns intact, 31 rows |
| J-06 (score consistency) | passing | passing | UT-21 /themes 5d == /backtest 5d (Megacap +2.96%); themes/sectors==Backtest byte-equal tests PASS |
| J-09 (Backtest evidence) | passing | passing (unchanged) | UT-21 Backtest Top Themes/Sectors cross-check |
| J-21 (Backtest horizon-linked returns) | passing | passing | UT-21 cross-check; carried |
| J-29 (event study) | passing | passing | UT-19 Event Study stays Episodes-default (byte-identical) |
| J-32 (Research as-of toggle) | passing | passing | RSP As-of count-coherence test PASS (`test_rsp_samples_count_coherent_as_of_scoped`) |
| J-48 (column sorting) | passing | passing | UT-06/07/11/12/20 view-transform sort, default-order reset on nav |
| J-51 (sample-count drill-down) | passing | passing | UT-13/14 total==n for named + none patterns |
| J-63 (Episodes/Pooled) | passing | passing | UT-19 Event Study Episodes default unaffected by RSP Pooled default |
| J-75 (per-stock forward returns) | passing | passing | shared `forward-return` helper reused; mirror discipline followed |
| J-77 (Regime×Setup×Pattern study) | passing | passing | UT-09/10/13/14/16; samples reconciled to emitted set |

All non-scope Must-haves (J-01,02,05,07,08,10–20,22–80) carry forward unchanged. J-22/J-23/J-24 remain honestly blocked-NA (data-walled, non-vetoing).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Single source of truth (critical) | OK | J-81 `forward_returns` read VERBATIM via the SAME `_leadership_returns` builder Backtest uses; byte-equal to Backtest proven (`test_{themes,sectors}_forward_returns_match_backtest_leadership` PASS). NOT a second/divergent score. |
| No recompute in read path (critical) | OK | One `forward_returns` SELECT per run; `_leadership_returns_by_horizon` projects once; J-82c samples reuse the SAME observation builder + `_rsp_combination_members` predicate the study groups by. Coherence Step 1 PASS. |
| No lookahead (critical) | OK | Forward returns read from stored append-only rows (only bars > D); no scoring change. |
| Snapshots immutable (critical) | OK | No `scanner_run`/result row mutated; J-81 is a read surface; J-82 is read-only view/serve. |
| No fabricated data (critical) | OK | NA (not 0%) at/near latest verified UT-15 (naIn60d=11, zeroIn60d=0); industry ETFs without bars → NA (UT-05); empty-after-filter honest message (UT-16). |
| No magic numbers | OK | Horizons read from `config.walk_forward.horizons`; vocabularies config-backed. No new float literals (the iter-20 `_rsp_rank_key` violation stays resolved). |
| Honest limitations surfaced | OK | Survivorship-bias disclaimer present on samples drill-down (UT-14). |

No NEW anti-goal violation. The two full-suite failures are NOT an anti-goal violation — they are stale over-strict tests (see below), confirmed by COHERENCE-PASS and the passing J-06 byte-identity tests.

## Next-Step Recommendation

**Run a small full-depth consolidation iteration that turns the full backend suite GREEN, then declare GOAL_ACHIEVED.** Exactly one defect blocks completion:

`apps/backend/tests/test_api_engine.py::test_api_themes_equals_engine_output` and `::test_api_sectors_equals_engine_output` assert the served `/api/themes` and `/api/sectors` payloads are byte-for-byte equal to the raw engine output (`score_themes`/`score_sectors`). J-81 additively attached a `forward_returns` key to each served row — a value the engine score functions never compute (forward returns come from the separate walk-forward engine, read verbatim from the append-only `forward_returns` table, byte-identical to Backtest). The guards are now over-strict and must be reconciled to the legitimate additive surface, mirroring iter-20→iter-21's J-77 magic-numbers fix and the dev's own (correct) update of `test_iter20_research_cluster.py` this iteration.

Fix (developer's choice, must keep the single-source intent intact):
- Compare `served` to `expected` modulo the additive `forward_returns` key (strip/pop `forward_returns` from each served row before the byte-equality assert, and separately assert the field exists with the configured horizons), OR
- Build `expected` from the served-payload helper path the endpoint actually uses so the comparison reflects the real serve shape.

Then re-run the FULL backend pytest suite to `EXIT_CODE=0` (handed to the pump, nohup-async, never blocking the evaluator dispatch — lessons: backend-test-suite-runtime, goal-pump-never-block-evaluator-on-suite). No browser re-QA is needed for a test-only change beyond a smoke that `/themes` + `/sectors` still serve. After the suite is GREEN with zero regressions, every buildable Must-have is passing and J-22/J-23/J-24 stay honestly blocked-NA — GOAL_ACHIEVED is then appropriate.

## Halt Justification

Not halting. CONTINUE: J-81 + J-82 are functionally complete, correct, and coherent, but the binding GOAL_ACHIEVED gate (a GREEN full backend suite — the DoD's own requirement and the standing iter-19/21/22 rule) is unmet (`EXIT_CODE=1`, 2 stale-test failures). This is the identical pattern to iter-20→iter-21: a correct additive feature trips a pre-existing blanket guard, held one consolidation iter from done. Not a REGRESSION — the two failing tests are over-strict guards made stale by a legitimate, coherence-approved, byte-identity-proven additive surface, not a passing-then-broken behaviour.
